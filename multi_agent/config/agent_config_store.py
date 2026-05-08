"""
AgentConfigStore - DB-backed store for versioned agent configurations.

Agents call AgentConfigStore.get_instance().get_config(name) at init time to
load their role/goal/backstory/business_rules from the database, falling back
to hardcoded constructor defaults if the DB is unavailable or has no row yet.

MetaEvolutionAgent calls save_new_version() to append an evolved config and
record_interaction() to log run outcomes for future evolution decisions.
"""

import json
import logging
import os
import sys
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ── path bootstrap so we can import project-root modules ───────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


class AgentConfigStore:
    """Singleton store for versioned agent configurations."""

    _instance: Optional["AgentConfigStore"] = None

    @classmethod
    def get_instance(cls) -> "AgentConfigStore":
        if cls._instance is None:
            cls._instance = AgentConfigStore()
        return cls._instance

    def __init__(self) -> None:
        self._db: Any = None
        self._db_type: str = "postgres"
        self._cache: Dict[str, Dict] = {}
        self._tables_ensured: bool = False
        self._connect()

    # ── connection ──────────────────────────────────────────────────────────

    def _connect(self) -> None:
        try:
            from database.db_manager import DatabaseManager
            from config import DB_CONFIG
            self._db = DatabaseManager(DB_CONFIG)
            self._db_type = DB_CONFIG.get("type", "postgres").lower()
            logger.debug("AgentConfigStore: connected to database")
        except Exception as e:
            logger.warning(f"AgentConfigStore: DB unavailable, using hardcoded defaults ({e})")
            self._db = None

    # ── table bootstrap ─────────────────────────────────────────────────────

    def _ensure_tables(self) -> None:
        """Create evolution tables if they don't exist (idempotent)."""
        if self._tables_ensured or self._db is None:
            return

        if self._db_type == "postgres":
            configs_ddl = """
                CREATE TABLE IF NOT EXISTS agent_configs (
                    id              SERIAL PRIMARY KEY,
                    agent_name      VARCHAR(100) NOT NULL,
                    version         INTEGER NOT NULL DEFAULT 1,
                    is_active       BOOLEAN DEFAULT TRUE,
                    role            TEXT,
                    goal            TEXT,
                    backstory       TEXT,
                    system_prompts  TEXT DEFAULT '{}',
                    business_rules  TEXT DEFAULT '{}',
                    model           VARCHAR(100) DEFAULT 'deepseek-chat',
                    temperature     FLOAT DEFAULT 0.3,
                    evolution_reason TEXT,
                    parent_version  INTEGER,
                    created_at      TIMESTAMP DEFAULT NOW(),
                    UNIQUE(agent_name, version)
                )
            """
            interactions_ddl = """
                CREATE TABLE IF NOT EXISTS agent_interactions (
                    id              SERIAL PRIMARY KEY,
                    session_id      VARCHAR(100),
                    agent_name      VARCHAR(100),
                    config_version  INTEGER DEFAULT 1,
                    user_feedback   VARCHAR(20),
                    output_summary  TEXT DEFAULT '{}',
                    created_at      TIMESTAMP DEFAULT NOW()
                )
            """
        else:
            # SQLite
            configs_ddl = """
                CREATE TABLE IF NOT EXISTS agent_configs (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name      TEXT NOT NULL,
                    version         INTEGER NOT NULL DEFAULT 1,
                    is_active       INTEGER DEFAULT 1,
                    role            TEXT,
                    goal            TEXT,
                    backstory       TEXT,
                    system_prompts  TEXT DEFAULT '{}',
                    business_rules  TEXT DEFAULT '{}',
                    model           TEXT DEFAULT 'deepseek-chat',
                    temperature     REAL DEFAULT 0.3,
                    evolution_reason TEXT,
                    parent_version  INTEGER,
                    created_at      TEXT DEFAULT (datetime('now')),
                    UNIQUE(agent_name, version)
                )
            """
            interactions_ddl = """
                CREATE TABLE IF NOT EXISTS agent_interactions (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id      TEXT,
                    agent_name      TEXT,
                    config_version  INTEGER DEFAULT 1,
                    user_feedback   TEXT,
                    output_summary  TEXT DEFAULT '{}',
                    created_at      TEXT DEFAULT (datetime('now'))
                )
            """

        try:
            self._db.execute_query(configs_ddl)
            self._db.execute_query(interactions_ddl)
            self._db.execute_query(
                "CREATE INDEX IF NOT EXISTS idx_agent_configs_name_active "
                "ON agent_configs(agent_name, is_active)"
            )
            self._db.execute_query(
                "CREATE INDEX IF NOT EXISTS idx_agent_interactions_agent "
                "ON agent_interactions(agent_name, created_at)"
            )
            self._tables_ensured = True
            logger.debug("AgentConfigStore: tables ready")
        except Exception as e:
            logger.warning(f"AgentConfigStore: could not create tables: {e}")

    # ── public API ──────────────────────────────────────────────────────────

    def get_config(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Return the active configuration dict for agent_name, or None if not found.

        The returned dict contains: version, role, goal, backstory,
        system_prompts (dict), business_rules (dict), model, temperature.
        """
        if agent_name in self._cache:
            return self._cache[agent_name]

        if self._db is None:
            return None

        self._ensure_tables()

        try:
            rows = self._db.execute_query(
                "SELECT * FROM agent_configs WHERE agent_name = %s AND is_active = %s "
                "ORDER BY version DESC LIMIT 1",
                (agent_name, True if self._db_type == "postgres" else 1),
                fetch=True,
            )
            if not rows:
                return None

            row = dict(rows[0])
            config = {
                "version":        row.get("version", 1),
                "role":           row.get("role"),
                "goal":           row.get("goal"),
                "backstory":      row.get("backstory"),
                "system_prompts": self._parse_json(row.get("system_prompts", "{}")),
                "business_rules": self._parse_json(row.get("business_rules", "{}")),
                "model":          row.get("model", "deepseek-chat"),
                "temperature":    row.get("temperature", 0.3),
            }
            self._cache[agent_name] = config
            return config
        except Exception as e:
            logger.warning(f"AgentConfigStore: could not load config for {agent_name}: {e}")
            return None

    def save_new_version(
        self,
        agent_name: str,
        updates: Dict[str, Any],
        reason: str,
    ) -> Optional[int]:
        """
        Persist an evolved configuration as a new version.

        Deactivates the current active version, then inserts a new row with
        version = current_version + 1. Returns the new version number, or
        None if the save failed.

        `updates` may contain any subset of: role, goal, backstory,
        system_prompts (dict), business_rules (dict), model, temperature.
        """
        if self._db is None:
            return None

        self._ensure_tables()

        try:
            # Load current active config as the baseline
            current = self.get_config(agent_name) or {}
            current_version = current.get("version", 0)
            new_version = current_version + 1

            # Check max versions guard
            max_versions = 10
            if current_version >= max_versions:
                logger.info(
                    f"AgentConfigStore: {agent_name} has reached max versions ({max_versions}), "
                    "skipping evolution"
                )
                return None

            # Merge updates onto current
            merged = {
                "role":           updates.get("role")           or current.get("role"),
                "goal":           updates.get("goal")           or current.get("goal"),
                "backstory":      updates.get("backstory")      or current.get("backstory"),
                "model":          updates.get("model")          or current.get("model", "deepseek-chat"),
                "temperature":    updates.get("temperature")    if updates.get("temperature") is not None
                                  else current.get("temperature", 0.3),
                "system_prompts": {**current.get("system_prompts", {}),
                                   **updates.get("system_prompts", {})},
                "business_rules": {**current.get("business_rules", {}),
                                   **updates.get("business_rules", {})},
            }

            # Deactivate old version
            self._db.execute_query(
                "UPDATE agent_configs SET is_active = %s "
                "WHERE agent_name = %s AND is_active = %s",
                (False if self._db_type == "postgres" else 0,
                 agent_name,
                 True if self._db_type == "postgres" else 1),
            )

            # Insert new version
            self._db.execute_query(
                """INSERT INTO agent_configs
                   (agent_name, version, is_active, role, goal, backstory,
                    system_prompts, business_rules, model, temperature,
                    evolution_reason, parent_version)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    agent_name,
                    new_version,
                    True if self._db_type == "postgres" else 1,
                    merged["role"],
                    merged["goal"],
                    merged["backstory"],
                    json.dumps(merged["system_prompts"]),
                    json.dumps(merged["business_rules"]),
                    merged["model"],
                    merged["temperature"],
                    reason,
                    current_version,
                ),
            )

            # Invalidate cache so next get_config loads the new version
            self._cache.pop(agent_name, None)
            logger.info(f"AgentConfigStore: {agent_name} evolved to version {new_version}. Reason: {reason}")
            return new_version

        except Exception as e:
            logger.error(f"AgentConfigStore: failed to save new version for {agent_name}: {e}")
            return None

    def record_interaction(
        self,
        session_id: str,
        agent_name: str,
        output_summary: Dict[str, Any],
        user_feedback: Optional[str] = None,
        config_version: int = 1,
    ) -> None:
        """Log a run outcome for MetaEvolutionAgent to analyse later."""
        if self._db is None:
            return

        self._ensure_tables()

        try:
            self._db.execute_query(
                """INSERT INTO agent_interactions
                   (session_id, agent_name, config_version, user_feedback, output_summary)
                   VALUES (%s, %s, %s, %s, %s)""",
                (
                    session_id,
                    agent_name,
                    config_version,
                    user_feedback,
                    json.dumps(output_summary, default=str),
                ),
            )
        except Exception as e:
            logger.warning(f"AgentConfigStore: could not record interaction: {e}")

    def get_interaction_count(self, agent_name: str) -> int:
        """Return total number of logged interactions for an agent."""
        if self._db is None:
            return 0

        self._ensure_tables()

        try:
            rows = self._db.execute_query(
                "SELECT COUNT(*) as cnt FROM agent_interactions WHERE agent_name = %s",
                (agent_name,),
                fetch=True,
            )
            return int(rows[0]["cnt"]) if rows else 0
        except Exception:
            return 0

    def list_versions(self, agent_name: str) -> list:
        """Return all config versions for an agent (for audit/debugging)."""
        if self._db is None:
            return []

        self._ensure_tables()

        try:
            rows = self._db.execute_query(
                "SELECT version, is_active, evolution_reason, created_at "
                "FROM agent_configs WHERE agent_name = %s ORDER BY version",
                (agent_name,),
                fetch=True,
            )
            return [dict(r) for r in rows]
        except Exception:
            return []

    def rollback_to_version(self, agent_name: str, version: int) -> bool:
        """Reactivate a specific older version and deactivate the current one."""
        if self._db is None:
            return False

        self._ensure_tables()

        try:
            # Deactivate all
            self._db.execute_query(
                "UPDATE agent_configs SET is_active = %s WHERE agent_name = %s",
                (False if self._db_type == "postgres" else 0, agent_name),
            )
            # Activate the requested version
            self._db.execute_query(
                "UPDATE agent_configs SET is_active = %s "
                "WHERE agent_name = %s AND version = %s",
                (True if self._db_type == "postgres" else 1, agent_name, version),
            )
            self._cache.pop(agent_name, None)
            logger.info(f"AgentConfigStore: {agent_name} rolled back to version {version}")
            return True
        except Exception as e:
            logger.error(f"AgentConfigStore: rollback failed: {e}")
            return False

    # ── helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_json(value: Any) -> Dict:
        if isinstance(value, dict):
            return value
        if not value:
            return {}
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return {}
