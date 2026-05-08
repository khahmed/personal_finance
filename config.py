"""
Configuration file for portfolio management system.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database configuration
# Supports both PostgreSQL and SQLite backends.
#   DB_TYPE=postgres (default) uses psycopg2 with host/database/user/password/port
#   DB_TYPE=sqlite uses the built-in sqlite3 module and DB_NAME (or SQLITE_DB_PATH)
DB_TYPE = os.getenv("DB_TYPE", "postgres").lower()

DB_CONFIG = {
    "type": DB_TYPE,  # "postgres" or "sqlite"
}

if DB_TYPE == "sqlite":
    # For SQLite, the "database" field is the file path.
    # Defaults to a local file in the project root.
    DB_CONFIG["database"] = os.getenv("SQLITE_DB_PATH", os.getenv("DB_NAME", "portfolio.db"))
else:
    # PostgreSQL (default)
    DB_CONFIG.update(
        {
            "host": os.getenv("DB_HOST", "localhost"),
            "database": os.getenv("DB_NAME", "portfolio_db"),
            "user": os.getenv("DB_USER", "bankapp"),
            "password": os.getenv("DB_PASSWORD", "XXXXXX"),
            "port": int(os.getenv("DB_PORT", 5432)),
        }
    )

# Paths
STATEMENTS_DIR = os.getenv("STATEMENTS_DIR", "statements")
REPORTS_DIR = os.getenv("REPORTS_DIR", "reports")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
