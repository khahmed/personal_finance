"""
Base agent class with common functionality.
"""

from typing import Any, Dict, List, Optional, Union
from crewai import Agent
import logging

logger = logging.getLogger(__name__)

try:
    from crewai.tools import BaseTool
    ToolType = Union[BaseTool, Any]
except ImportError:
    ToolType = Any


class BaseAgent:
    """Base class for all agents with common functionality."""

    def __init__(
        self,
        name: str,
        role: str,
        goal: str,
        backstory: str,
        tools: Optional[List[ToolType]] = None,
        model: str = "deepseek-chat",
        temperature: float = 0.3,
        verbose: bool = True,
    ):
        # ── Load DB config (overrides constructor args when available) ────────
        db_config = self._try_load_db_config(name)

        self.name = name
        self.role        = db_config.get("role")        or role
        self.goal        = db_config.get("goal")        or goal
        self.backstory   = db_config.get("backstory")   or backstory
        self.model       = db_config.get("model")       or model
        self.temperature = (db_config["temperature"]
                            if db_config.get("temperature") is not None
                            else temperature)
        self.business_rules: Dict[str, Any] = db_config.get("business_rules") or {}
        self.system_prompts: Dict[str, Any] = db_config.get("system_prompts") or {}
        self.config_version: int            = db_config.get("version", 1)

        self.tools   = tools or []
        self.verbose = verbose

        # ── LLM tools ─────────────────────────────────────────────────────────
        self.llm_tools = None
        try:
            from ..tools.llm_tools import LLMTools
            self.llm_tools = LLMTools(model=self.model)
            if self.llm_tools.is_available():
                provider = "DeepSeek" if self.llm_tools.use_deepseek else "Anthropic"
                logger.info(f"{self.name} v{self.config_version}: LLM available ({provider})")
            else:
                logger.debug(f"{self.name}: LLM not available (no API key)")
        except ImportError as e:
            logger.debug(f"{self.name}: LLM tools not available: {e}")

        # ── CrewAI agent (optional – only when LLM is available) ─────────────
        self._crewai_agent = None
        if self.llm_tools and self.llm_tools.is_available():
            try:
                if self.llm_tools.use_anthropic:
                    from langchain_anthropic import ChatAnthropic
                    llm = ChatAnthropic(
                        model=self.llm_tools.model or "claude-3-opus-20240229",
                        temperature=self.temperature,
                    )
                elif self.llm_tools.use_deepseek:
                    from langchain_openai import ChatOpenAI
                    llm = ChatOpenAI(
                        model=self.llm_tools.model or "deepseek-chat",
                        temperature=self.temperature,
                        openai_api_key=self.llm_tools.api_key,
                        openai_api_base="https://api.deepseek.com/v1",
                    )
                else:
                    llm = None

                if llm:
                    self._crewai_agent = Agent(
                        role=self.role,
                        goal=self.goal,
                        backstory=self.backstory,
                        tools=self.tools,
                        verbose=verbose,
                        allow_delegation=False,
                        llm=llm,
                    )
                    logger.debug(f"{self.name}: CrewAI Agent created with LLM")
            except Exception as e:
                logger.debug(f"{self.name}: Could not create CrewAI Agent: {e}")

    # ── DB config loading ─────────────────────────────────────────────────────

    @staticmethod
    def _try_load_db_config(name: str) -> Dict[str, Any]:
        """Return active DB config for this agent, or {} if unavailable."""
        try:
            from ..config.agent_config_store import AgentConfigStore
            config = AgentConfigStore.get_instance().get_config(name)
            if config:
                logger.debug(f"{name}: loaded config v{config.get('version', '?')} from DB")
                return config
        except Exception as e:
            logger.debug(f"{name}: could not load DB config: {e}")
        return {}

    # ── task processing ───────────────────────────────────────────────────────

    def process(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generic task processing (subclasses implement domain-specific methods)."""
        try:
            if context:
                task_description = f"{task_description}\n\nContext: {context}"
            logger.info(f"{self.name} processing task: {task_description[:100]}...")
            return {"agent": self.name, "status": "completed", "output": {}}
        except Exception as e:
            logger.error(f"Error in {self.name}: {e}")
            return {"agent": self.name, "status": "error", "error": str(e)}

    def get_agent(self) -> Optional[Agent]:
        """Return the underlying CrewAI agent (if available)."""
        return self._crewai_agent

    def use_llm_analysis(self) -> bool:
        """Check if LLM analysis is available."""
        return self.llm_tools is not None and self.llm_tools.is_available()

    def enhance_with_llm(self, data: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
        """Enhance analysis results with LLM-generated insights."""
        if not self.use_llm_analysis():
            return data

        # Use DB system_prompts if available, otherwise LLMTools default
        system_prompt_override = self.system_prompts.get(analysis_type)

        try:
            llm_recommendations = self.llm_tools.generate_recommendations(
                data, analysis_type, system_prompt_override=system_prompt_override
            )
            explanation = self.llm_tools.explain_analysis(data, analysis_type)

            enhanced = data.copy()
            enhanced["llm_insights"] = {
                "explanation":    explanation,
                "recommendations": llm_recommendations,
                "llm_provider":   "DeepSeek" if self.llm_tools.use_deepseek else "Anthropic",
            }
            return enhanced
        except Exception as e:
            logger.error(f"Error enhancing with LLM: {e}")
            return data
