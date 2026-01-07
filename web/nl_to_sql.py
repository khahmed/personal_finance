"""
Natural language to SQL converter using LLM.
"""

import os
import json
import logging
from typing import Dict, Optional, List
import re

logger = logging.getLogger(__name__)


class NLToSQLConverter:
    """Converts natural language queries to SQL using LLM."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Initialize the converter.

        Args:
            api_key: API key for OpenAI/Anthropic/DeepSeek. If None, tries to get from env.
            model: Model to use (gpt-4, gpt-3.5-turbo, claude-3-opus, deepseek-chat, etc.)
        """
        # Priority: DeepSeek > OpenAI > Anthropic
        self.model = model
        
        # Check environment variables first (explicit preference)
        deepseek_key = os.getenv('DEEPSEEK_API_KEY')
        openai_key = os.getenv('OPENAI_API_KEY')
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        
        # If api_key is provided directly and no env vars are set, use it
        # (Note: DeepSeek and OpenAI both use 'sk-' prefix, so we default to OpenAI)
        if api_key and not (deepseek_key or openai_key or anthropic_key):
            # Default to OpenAI format if no env vars set
            openai_key = api_key
        
        # Determine which API to use (priority order: DeepSeek > OpenAI > Anthropic)
        self.use_deepseek = bool(deepseek_key)
        self.use_openai = bool(openai_key and not self.use_deepseek)
        self.use_anthropic = bool(anthropic_key and not self.use_deepseek and not self.use_openai)
        
        # Set the API key to use
        self.api_key = deepseek_key or openai_key or anthropic_key

    def _get_schema_info(self) -> str:
        """Get database schema information for the LLM."""
        return """
Database Schema:
- institutions (institution_id, institution_name, created_at)
- accounts (account_id, institution_id, account_number, account_type, account_name, created_at)
- statements (statement_id, account_id, statement_date, statement_period_start, statement_period_end, total_value, file_path, processed_at)
- asset_types (asset_type_id, asset_type_name, asset_category, created_at)
- securities (security_id, symbol, security_name, asset_type_id, description, created_at)
- holdings (holding_id, statement_id, account_id, security_id, quantity, price, book_value, market_value, holding_date, currency, created_at)
- cash_balances (cash_balance_id, statement_id, account_id, balance_date, cash_amount, currency, created_at)
- account_performance (performance_id, account_id, performance_date, return_1m, return_3m, return_6m, return_ytd, return_1y, return_3y, return_5y, return_inception, created_at)

Views:
- v_latest_holdings: Latest holdings by account with institution, security, and asset category info
- v_portfolio_allocation: Portfolio allocation by asset category
- v_portfolio_value_trend: Portfolio value over time

Common patterns:
- Use v_latest_holdings for current holdings
- Use v_portfolio_value_trend for time series analysis
- Use v_portfolio_allocation for allocation analysis
- Always use parameterized queries with %s for dates and strings
- Dates should be in 'YYYY-MM-DD' format
- Use SUM() for aggregations, COUNT() for counts
- Use GROUP BY for aggregations
- Use ORDER BY for sorting
"""

    def _get_example_queries(self) -> str:
        """Get example queries for few-shot learning."""
        return """
Example natural language to SQL conversions:

1. "Show me my current portfolio allocation by asset category"
   SQL: SELECT asset_category, SUM(market_value) as total_value FROM v_latest_holdings GROUP BY asset_category ORDER BY total_value DESC

2. "What are my top 10 holdings by value?"
   SQL: SELECT security_name, symbol, market_value, asset_category FROM v_latest_holdings ORDER BY market_value DESC LIMIT 10

3. "Show me portfolio value over the last 6 months"
   SQL: SELECT statement_date, SUM(total_account_value) as total_value FROM v_portfolio_value_trend WHERE statement_date >= CURRENT_DATE - INTERVAL '6 months' GROUP BY statement_date ORDER BY statement_date

4. "What is my total portfolio value?"
   SQL: SELECT SUM(market_value) as total_value FROM v_latest_holdings

5. "Show me holdings for Scotiabank accounts"
   SQL: SELECT * FROM v_latest_holdings WHERE institution_name = 'ScotiaBank' ORDER BY market_value DESC

6. "What is my allocation by institution?"
   SQL: SELECT institution_name, SUM(market_value) as total_value FROM v_latest_holdings GROUP BY institution_name ORDER BY total_value DESC

7. "Show me the performance of my RRSP accounts"
   SQL: SELECT * FROM v_latest_holdings WHERE account_type = 'RRSP' ORDER BY market_value DESC
"""

    def convert_to_sql(self, natural_language_query: str, context: Optional[Dict] = None) -> Dict[str, any]:
        """
        Convert natural language query to SQL.

        Args:
            natural_language_query: User's natural language query
            context: Optional context (e.g., current filters, date ranges)

        Returns:
            Dictionary with 'sql', 'params', 'explanation', and 'error' keys
        """
        try:
            schema_info = self._get_schema_info()
            examples = self._get_example_queries()

            prompt = f"""{schema_info}

{examples}

User Query: "{natural_language_query}"

Generate a PostgreSQL query that answers this question. Follow these rules:
1. Only generate SELECT queries (no INSERT, UPDATE, DELETE, DROP, etc.)
2. Use parameterized queries with %s for any user-provided values
3. Return ONLY the SQL query - nothing else, no explanations, no JSON arrays, no additional text
4. The output must be valid SQL that can be executed directly
5. Use views when appropriate (v_latest_holdings, v_portfolio_allocation, v_portfolio_value_trend)
6. Format dates as 'YYYY-MM-DD' strings
7. Use proper SQL syntax for PostgreSQL
8. Do NOT include parameter lists, JSON arrays, or any text after the SQL query

SQL Query:"""

            if self.use_deepseek:
                return self._call_deepseek(prompt, natural_language_query)
            elif self.use_openai:
                return self._call_openai(prompt, natural_language_query)
            elif self.use_anthropic:
                return self._call_anthropic(prompt, natural_language_query)
            else:
                # Fallback to simple rule-based conversion
                return self._rule_based_conversion(natural_language_query)

        except Exception as e:
            logger.error(f"Error converting to SQL: {e}")
            return {
                'sql': None,
                'params': [],
                'explanation': None,
                'error': str(e)
            }

    def _call_deepseek(self, prompt: str, query: str) -> Dict:
        """Call DeepSeek API for SQL generation."""
        try:
            import openai
            # DeepSeek uses OpenAI-compatible API with different base URL
            client = openai.OpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com/v1"
            )

            # DeepSeek models: deepseek-chat, deepseek-coder
            model_name = self.model if 'deepseek' in self.model.lower() else 'deepseek-chat'

            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a SQL expert. Generate only valid PostgreSQL SELECT queries. Return ONLY the SQL query - no markdown, no JSON arrays, no explanations, no additional text. The output must be executable SQL."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )

            sql_text = response.choices[0].message.content.strip()
            # Remove markdown code blocks if present
            sql_text = re.sub(r'```sql\n?', '', sql_text)
            sql_text = re.sub(r'```\n?', '', sql_text)
            sql_text = sql_text.strip()
            
            # Clean SQL to remove trailing JSON arrays and artifacts
            sql_text = self._clean_sql(sql_text)

            # Extract parameters if mentioned
            params = self._extract_params(query, sql_text)
            
            # Replace %s placeholders with actual values
            sql_text = self._replace_placeholders(sql_text, params)

            return {
                'sql': sql_text,
                'params': params,
                'explanation': f"Generated SQL query using DeepSeek for: {query}",
                'error': None
            }
        except ImportError:
            logger.warning("OpenAI library not installed. Install with: pip install openai")
            return self._rule_based_conversion(query)
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            return self._rule_based_conversion(query)

    def _call_openai(self, prompt: str, query: str) -> Dict:
        """Call OpenAI API for SQL generation."""
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)

            response = client.chat.completions.create(
                model=self.model if self.model.startswith('gpt') else 'gpt-4',
                messages=[
                    {"role": "system", "content": "You are a SQL expert. Generate only valid PostgreSQL SELECT queries. Return ONLY the SQL query - no markdown, no JSON arrays, no explanations, no additional text. The output must be executable SQL."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )

            sql_text = response.choices[0].message.content.strip()
            # Remove markdown code blocks if present
            sql_text = re.sub(r'```sql\n?', '', sql_text)
            sql_text = re.sub(r'```\n?', '', sql_text)
            sql_text = sql_text.strip()
            
            # Clean SQL to remove trailing JSON arrays and artifacts
            sql_text = self._clean_sql(sql_text)

            # Extract parameters if mentioned
            params = self._extract_params(query, sql_text)
            
            # Replace %s placeholders with actual values
            sql_text = self._replace_placeholders(sql_text, params)

            return {
                'sql': sql_text,
                'params': params,
                'explanation': f"Generated SQL query for: {query}",
                'error': None
            }
        except ImportError:
            logger.warning("OpenAI library not installed. Install with: pip install openai")
            return self._rule_based_conversion(query)
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return self._rule_based_conversion(query)

    def _call_anthropic(self, prompt: str, query: str) -> Dict:
        """Call Anthropic API for SQL generation."""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)

            response = client.messages.create(
                model=self.model if 'claude' in self.model.lower() else 'claude-3-opus-20240229',
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            sql_text = response.content[0].text.strip()
            # Remove markdown code blocks if present
            sql_text = re.sub(r'```sql\n?', '', sql_text)
            sql_text = re.sub(r'```\n?', '', sql_text)
            sql_text = sql_text.strip()
            
            # Clean SQL to remove trailing JSON arrays and artifacts
            sql_text = self._clean_sql(sql_text)

            params = self._extract_params(query, sql_text)
            
            # Replace %s placeholders with actual values
            sql_text = self._replace_placeholders(sql_text, params)

            return {
                'sql': sql_text,
                'params': params,
                'explanation': f"Generated SQL query for: {query}",
                'error': None
            }
        except ImportError:
            logger.warning("Anthropic library not installed. Install with: pip install anthropic")
            return self._rule_based_conversion(query)
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return self._rule_based_conversion(query)

    def _clean_sql(self, sql: str) -> str:
        """
        Clean SQL by removing trailing JSON arrays, explanations, and other artifacts.
        
        Args:
            sql: Raw SQL string that may contain artifacts
            
        Returns:
            Cleaned SQL string
        """
        if not sql:
            return sql
        
        # Split by lines to process more carefully
        lines = sql.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Stop processing if we encounter non-SQL content
            if line.startswith(('Note:', 'Parameters:', 'Explanation:', '//', '/*')):
                break
            
            # Remove trailing JSON arrays from the line
            # Pattern: space(s) followed by [ followed by content ] at end of line
            line = re.sub(r'\s+\[.*?\]\s*$', '', line)
            line = re.sub(r'\s*\[["\']?[^"\']*["\']?\]\s*$', '', line)
            
            # Remove trailing JSON objects
            line = re.sub(r'\s+\{.*?\}\s*$', '', line)
            
            # If line still has content, add it
            if line:
                cleaned_lines.append(line)
        
        # Join lines back together
        sql = ' '.join(cleaned_lines) if cleaned_lines else sql
        
        # Final pass: remove any remaining trailing JSON arrays/objects
        sql = re.sub(r'\s+\[.*?\]\s*$', '', sql)
        sql = re.sub(r'\s+\{.*?\}\s*$', '', sql)
        
        # Remove trailing whitespace
        sql = sql.strip()
        
        return sql

    def _extract_params(self, query: str, sql: str) -> List:
        """Extract parameters from natural language query for SQL."""
        params = []
        query_lower = query.lower()

        # Extract institution names - map to exact database values
        institution_map = {
            'scotiabank': 'ScotiaBank',
            'sunlife': 'SunLife',
            'olympia': 'Olympia',
            'cibc': 'CIBC'
        }
        for inst_key, inst_value in institution_map.items():
            if inst_key in query_lower:
                params.append(inst_value)

        # Extract account types
        account_types = ['rrsp', 'tfsa', 'lira', 'resp']
        for acc_type in account_types:
            if acc_type in query_lower:
                params.append(acc_type.upper())

        # Extract dates (simple patterns)
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{1,2})/(\d{1,2})/(\d{4})',
        ]
        for pattern in date_patterns:
            matches = re.findall(pattern, query)
            if matches:
                params.extend(matches)

        return params

    def _replace_placeholders(self, sql: str, params: List) -> str:
        """
        Replace %s placeholders in SQL with actual values.
        This is safer than parameterized queries when values are extracted from natural language.
        
        Args:
            sql: SQL query with %s placeholders
            params: List of parameter values
            
        Returns:
            SQL query with placeholders replaced
        """
        if not params or '%s' not in sql:
            return sql
        
        # Count placeholders
        placeholder_count = sql.count('%s')
        
        if len(params) < placeholder_count:
            logger.warning(f"Parameter count mismatch: {len(params)} params but {placeholder_count} placeholders. Not replacing.")
            return sql
        
        # Replace placeholders with properly escaped values
        # Only replace up to the number of placeholders
        result_sql = sql
        for i, param in enumerate(params):
            if i >= placeholder_count:
                break
            # Escape single quotes for SQL
            if isinstance(param, str):
                escaped_param = param.replace("'", "''")
                result_sql = result_sql.replace('%s', f"'{escaped_param}'", 1)
            else:
                result_sql = result_sql.replace('%s', str(param), 1)
        
        return result_sql

    def _rule_based_conversion(self, query: str) -> Dict:
        """Fallback rule-based SQL conversion."""
        query_lower = query.lower()
        sql = None
        params = []

        # Portfolio allocation
        if 'allocation' in query_lower or 'asset category' in query_lower:
            if 'institution' in query_lower:
                sql = "SELECT institution_name, asset_category, SUM(market_value) as total_value FROM v_latest_holdings GROUP BY institution_name, asset_category ORDER BY institution_name, total_value DESC"
            else:
                sql = "SELECT asset_category, SUM(market_value) as total_value FROM v_latest_holdings GROUP BY asset_category ORDER BY total_value DESC"

        # Top holdings
        elif 'top' in query_lower and ('holding' in query_lower or 'security' in query_lower):
            n = 10
            match = re.search(r'top\s+(\d+)', query_lower)
            if match:
                n = int(match.group(1))
            sql = f"SELECT security_name, symbol, market_value, asset_category FROM v_latest_holdings ORDER BY market_value DESC LIMIT {n}"

        # Total value
        elif 'total' in query_lower and ('value' in query_lower or 'portfolio' in query_lower):
            sql = "SELECT SUM(market_value) as total_value FROM v_latest_holdings"

        # Holdings by institution
        elif 'institution' in query_lower or 'bank' in query_lower:
            if 'scotiabank' in query_lower:
                sql = "SELECT * FROM v_latest_holdings WHERE institution_name = 'ScotiaBank' ORDER BY market_value DESC"
            elif 'sunlife' in query_lower:
                sql = "SELECT * FROM v_latest_holdings WHERE institution_name = 'SunLife' ORDER BY market_value DESC"
            else:
                sql = "SELECT institution_name, SUM(market_value) as total_value FROM v_latest_holdings GROUP BY institution_name ORDER BY total_value DESC"

        # Value over time
        elif 'over time' in query_lower or 'trend' in query_lower or 'history' in query_lower:
            sql = "SELECT statement_date, SUM(total_account_value) as total_value FROM v_portfolio_value_trend GROUP BY statement_date ORDER BY statement_date"

        # Default: latest holdings
        else:
            sql = "SELECT * FROM v_latest_holdings ORDER BY market_value DESC LIMIT 50"

        return {
            'sql': sql,
            'params': params,
            'explanation': f"Rule-based conversion for: {query}",
            'error': None
        }

