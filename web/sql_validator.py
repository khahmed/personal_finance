"""
SQL validator to ensure queries are safe and only perform SELECT operations.
"""

import re
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class SQLValidator:
    """Validates SQL queries for safety."""

    # Dangerous SQL keywords that should not be allowed
    DANGEROUS_KEYWORDS = [
        'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE',
        'GRANT', 'REVOKE', 'EXEC', 'EXECUTE', 'CALL', 'MERGE', 'COPY'
    ]

    # Allowed SQL keywords (SELECT queries only)
    ALLOWED_KEYWORDS = [
        'SELECT', 'FROM', 'WHERE', 'JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN',
        'FULL JOIN', 'ON', 'GROUP BY', 'ORDER BY', 'HAVING', 'LIMIT', 'OFFSET',
        'UNION', 'UNION ALL', 'INTERSECT', 'EXCEPT', 'DISTINCT', 'AS', 'AND', 'OR',
        'IN', 'NOT IN', 'LIKE', 'ILIKE', 'BETWEEN', 'IS NULL', 'IS NOT NULL',
        'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END',
        'CAST', 'COALESCE', 'NULLIF', 'EXTRACT', 'DATE_TRUNC', 'INTERVAL',
        'CURRENT_DATE', 'CURRENT_TIMESTAMP', 'NOW'
    ]

    def validate(self, sql: str) -> Tuple[bool, str]:
        """
        Validate SQL query for safety.

        Args:
            sql: SQL query string

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not sql or not sql.strip():
            return False, "Empty SQL query"

        sql_upper = sql.upper().strip()

        # Must start with SELECT
        if not sql_upper.startswith('SELECT'):
            return False, "Only SELECT queries are allowed"

        # Check for dangerous keywords
        for keyword in self.DANGEROUS_KEYWORDS:
            # Use word boundaries to avoid false positives
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, sql_upper):
                return False, f"Dangerous keyword '{keyword}' is not allowed"

        # Check for SQL injection patterns
        injection_patterns = [
            r';\s*(DROP|DELETE|INSERT|UPDATE|ALTER|CREATE)',
            r'--',
            r'/\*',
            r'\*/',
            r'UNION\s+SELECT.*FROM.*information_schema',
            r'xp_cmdshell',
            r'sp_executesql'
        ]

        for pattern in injection_patterns:
            if re.search(pattern, sql_upper, re.IGNORECASE):
                return False, f"Potentially dangerous SQL pattern detected"

        # Check for multiple statements (semicolon followed by non-comment)
        statements = [s.strip() for s in sql.split(';') if s.strip()]
        if len(statements) > 1:
            # Allow semicolon only if it's the last character (trailing semicolon)
            if not (sql.strip().endswith(';') and len(statements) == 2 and not statements[1]):
                return False, "Multiple SQL statements are not allowed"

        # Basic syntax check - ensure balanced parentheses
        if sql.count('(') != sql.count(')'):
            return False, "Unbalanced parentheses in SQL query"

        return True, ""

    def sanitize(self, sql: str) -> str:
        """
        Sanitize SQL query by removing comments and normalizing whitespace.

        Args:
            sql: SQL query string

        Returns:
            Sanitized SQL query
        """
        # Remove comments
        sql = re.sub(r'--.*', '', sql)
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)

        # Normalize whitespace
        sql = ' '.join(sql.split())

        return sql.strip()

