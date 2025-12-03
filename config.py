"""
Configuration file for portfolio management system.
"""

import os

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'portfolio_db'),
    'user': os.getenv('DB_USER', 'bankapp'),
    'password': os.getenv('DB_PASSWORD', 'XXXXXX'),
    'port': int(os.getenv('DB_PORT', 5432))
}

# Paths
STATEMENTS_DIR = os.getenv('STATEMENTS_DIR', 'statements')
REPORTS_DIR = os.getenv('REPORTS_DIR', 'reports')

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
