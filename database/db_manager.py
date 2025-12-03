"""
Database manager for portfolio holdings data.
Handles all database operations including connections, inserts, and queries.
"""

import psycopg2
from psycopg2 import pool, extras
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and operations."""

    def __init__(self, db_config: Dict[str, str]):
        """
        Initialize database manager with configuration.

        Args:
            db_config: Dictionary with keys: host, database, user, password, port
        """
        self.db_config = db_config
        self.connection_pool = None
        self._init_connection_pool()

    def _init_connection_pool(self):
        """Initialize the database connection pool."""
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=self.db_config['host'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                port=self.db_config.get('port', 5432)
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Error creating connection pool: {e}")
            raise

    def get_connection(self):
        """Get a connection from the pool."""
        return self.connection_pool.getconn()

    def release_connection(self, conn):
        """Release a connection back to the pool."""
        self.connection_pool.putconn(conn)

    def close_all_connections(self):
        """Close all connections in the pool."""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("All database connections closed")

    def reset_data_tables(self, confirm: bool = False):
        """
        Reset all data tables (statements, holdings, cash_balances).
        This preserves the schema and reference tables (institutions, accounts, securities, asset_types).

        Args:
            confirm: Must be True to execute. Safety measure to prevent accidental deletion.
        """
        if not confirm:
            logger.warning("reset_data_tables called without confirmation. Set confirm=True to execute.")
            return False

        try:
            logger.info("Resetting data tables...")

            # Delete in order respecting foreign key constraints
            self.execute_query("DELETE FROM holdings")
            logger.info("  - Cleared holdings table")

            self.execute_query("DELETE FROM cash_balances")
            logger.info("  - Cleared cash_balances table")

            self.execute_query("DELETE FROM statements")
            logger.info("  - Cleared statements table")

            logger.info("Data tables reset successfully")
            return True

        except Exception as e:
            logger.error(f"Error resetting data tables: {e}")
            raise

    def reset_all_tables(self, confirm: bool = False):
        """
        Reset ALL tables including reference data (institutions, accounts, securities, asset_types).
        WARNING: This will delete everything and require complete re-import.

        Args:
            confirm: Must be True to execute. Safety measure to prevent accidental deletion.
        """
        if not confirm:
            logger.warning("reset_all_tables called without confirmation. Set confirm=True to execute.")
            return False

        try:
            logger.info("Resetting ALL tables...")

            # Delete in order respecting foreign key constraints
            self.execute_query("DELETE FROM holdings")
            logger.info("  - Cleared holdings table")

            self.execute_query("DELETE FROM cash_balances")
            logger.info("  - Cleared cash_balances table")

            self.execute_query("DELETE FROM statements")
            logger.info("  - Cleared statements table")

            self.execute_query("DELETE FROM securities")
            logger.info("  - Cleared securities table")

            self.execute_query("DELETE FROM asset_types")
            logger.info("  - Cleared asset_types table")

            self.execute_query("DELETE FROM accounts")
            logger.info("  - Cleared accounts table")

            self.execute_query("DELETE FROM institutions")
            logger.info("  - Cleared institutions table")

            logger.info("All tables reset successfully")
            return True

        except Exception as e:
            logger.error(f"Error resetting all tables: {e}")
            raise

    def execute_query(self, query: str, params: Tuple = None, fetch: bool = False):
        """
        Execute a SQL query.

        Args:
            query: SQL query string
            params: Query parameters
            fetch: Whether to fetch results

        Returns:
            Query results if fetch=True, None otherwise
        """
        conn = self.get_connection()
        cursor = None
        try:
            cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
            cursor.execute(query, params)
            conn.commit()

            if fetch:
                return cursor.fetchall()
            return None

        except Exception as e:
            conn.rollback()
            logger.error(f"Error executing query: {e}")
            logger.error(f"Query: {query}")
            raise
        finally:
            if cursor:
                cursor.close()
            self.release_connection(conn)

    def get_or_create_institution(self, institution_name: str) -> int:
        """Get or create institution and return its ID."""
        query = """
            INSERT INTO institutions (institution_name)
            VALUES (%s)
            ON CONFLICT (institution_name) DO UPDATE SET institution_name = EXCLUDED.institution_name
            RETURNING institution_id
        """
        result = self.execute_query(query, (institution_name,), fetch=True)
        return result[0]['institution_id']

    def get_or_create_account(self, institution_id: int, account_number: str,
                              account_type: str, account_name: str = None) -> int:
        """Get or create account and return its ID."""
        query = """
            INSERT INTO accounts (institution_id, account_number, account_type, account_name)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (institution_id, account_number)
            DO UPDATE SET account_type = EXCLUDED.account_type, account_name = EXCLUDED.account_name
            RETURNING account_id
        """
        result = self.execute_query(query, (institution_id, account_number, account_type, account_name), fetch=True)
        return result[0]['account_id']

    def get_or_create_asset_type(self, asset_type_name: str, asset_category: str) -> int:
        """Get or create asset type and return its ID."""
        query = """
            INSERT INTO asset_types (asset_type_name, asset_category)
            VALUES (%s, %s)
            ON CONFLICT (asset_type_name) DO UPDATE SET asset_category = EXCLUDED.asset_category
            RETURNING asset_type_id
        """
        result = self.execute_query(query, (asset_type_name, asset_category), fetch=True)
        return result[0]['asset_type_id']

    def get_or_create_security(self, symbol: Optional[str], security_name: str,
                               asset_type_id: int, description: str = None) -> int:
        """Get or create security and return its ID."""
        # First try to find by symbol and name
        if symbol:
            query_find = """
                SELECT security_id FROM securities
                WHERE symbol = %s AND security_name = %s
            """
            result = self.execute_query(query_find, (symbol, security_name), fetch=True)
            if result:
                return result[0]['security_id']

        # If not found, try by name only
        query_find_name = """
            SELECT security_id FROM securities
            WHERE security_name = %s
        """
        result = self.execute_query(query_find_name, (security_name,), fetch=True)
        if result:
            # Always update asset_type_id to reflect any classification changes
            query_update = """
                UPDATE securities
                SET symbol = %s, asset_type_id = %s, description = %s
                WHERE security_id = %s
            """
            self.execute_query(query_update, (symbol, asset_type_id, description, result[0]['security_id']))
            return result[0]['security_id']

        # Create new security
        query_insert = """
            INSERT INTO securities (symbol, security_name, asset_type_id, description)
            VALUES (%s, %s, %s, %s)
            RETURNING security_id
        """
        result = self.execute_query(query_insert, (symbol, security_name, asset_type_id, description), fetch=True)
        return result[0]['security_id']

    def create_statement(self, account_id: int, statement_date: datetime,
                        period_start: datetime = None, period_end: datetime = None,
                        total_value: float = None, file_path: str = None) -> int:
        """Create a statement record and return its ID."""
        query = """
            INSERT INTO statements (account_id, statement_date, statement_period_start,
                                   statement_period_end, total_value, file_path)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (account_id, statement_date)
            DO UPDATE SET
                statement_period_start = EXCLUDED.statement_period_start,
                statement_period_end = EXCLUDED.statement_period_end,
                total_value = EXCLUDED.total_value,
                file_path = EXCLUDED.file_path
            RETURNING statement_id
        """
        result = self.execute_query(
            query,
            (account_id, statement_date, period_start, period_end, total_value, file_path),
            fetch=True
        )
        return result[0]['statement_id']

    def create_holding(self, statement_id: int, account_id: int, security_id: int,
                      quantity: float, price: float, book_value: float = None,
                      market_value: float = None, holding_date: datetime = None,
                      currency: str = 'CAD'):
        """Create a holding record."""
        query = """
            INSERT INTO holdings (statement_id, account_id, security_id, quantity, price,
                                 book_value, market_value, holding_date, currency)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (statement_id, security_id)
            DO UPDATE SET
                quantity = EXCLUDED.quantity,
                price = EXCLUDED.price,
                book_value = EXCLUDED.book_value,
                market_value = EXCLUDED.market_value,
                holding_date = EXCLUDED.holding_date,
                currency = EXCLUDED.currency
        """
        self.execute_query(
            query,
            (statement_id, account_id, security_id, quantity, price, book_value,
             market_value, holding_date, currency)
        )

    def create_cash_balance(self, statement_id: int, account_id: int,
                           balance_date: datetime, cash_amount: float,
                           currency: str = 'CAD'):
        """Create a cash balance record."""
        query = """
            INSERT INTO cash_balances (statement_id, account_id, balance_date, cash_amount, currency)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """
        self.execute_query(query, (statement_id, account_id, balance_date, cash_amount, currency))

    def save_statement_data(self, statement_data: Dict):
        """
        Save complete statement data to database.

        Args:
            statement_data: Dictionary containing parsed statement data
        """
        try:
            # Get or create institution
            institution_id = self.get_or_create_institution(statement_data['institution'])

            # Get or create account
            account_id = self.get_or_create_account(
                institution_id,
                statement_data['account_number'],
                statement_data.get('account_type', 'Unknown'),
                statement_data.get('account_name')
            )

            # Create statement
            statement_id = self.create_statement(
                account_id,
                statement_data['statement_date'],
                statement_data.get('period_start'),
                statement_data.get('period_end'),
                statement_data.get('total_value'),
                statement_data.get('file_path')
            )

            # Save cash balance if present
            if statement_data.get('cash_balance') and statement_data.get('cash_balance') > 0:
                self.create_cash_balance(
                    statement_id,
                    account_id,
                    statement_data['statement_date'],
                    statement_data['cash_balance']
                )

            # Save holdings
            for holding in statement_data.get('holdings', []):
                # Get or create asset type
                asset_type_id = self.get_or_create_asset_type(
                    holding['asset_type'],
                    holding['asset_category']
                )

                # Get or create security
                security_id = self.get_or_create_security(
                    holding.get('symbol'),
                    holding['security_name'],
                    asset_type_id
                )

                # Create holding
                self.create_holding(
                    statement_id,
                    account_id,
                    security_id,
                    holding['quantity'],
                    holding['price'],
                    holding.get('book_value'),
                    holding.get('market_value'),
                    statement_data['statement_date'],
                    holding.get('currency', 'CAD')
                )

            logger.info(f"Successfully saved statement data for account {statement_data['account_number']}")

        except Exception as e:
            logger.error(f"Error saving statement data: {e}")
            raise

    def get_latest_holdings(self, institution: str = None, account_number: str = None) -> List[Dict]:
        """Get latest holdings, optionally filtered by institution and account."""
        query = "SELECT * FROM v_latest_holdings WHERE 1=1"
        params = []

        if institution:
            query += " AND institution_name = %s"
            params.append(institution)

        if account_number:
            query += " AND account_number = %s"
            params.append(account_number)

        query += " ORDER BY institution_name, account_number, market_value DESC"

        return self.execute_query(query, tuple(params) if params else None, fetch=True)

    def get_portfolio_allocation(self, as_of_date: datetime = None) -> List[Dict]:
        """Get portfolio allocation by asset category."""
        query = "SELECT * FROM v_portfolio_allocation"

        if as_of_date:
            query += " WHERE statement_date = %s"
            params = (as_of_date,)
        else:
            query += " WHERE statement_date = (SELECT MAX(statement_date) FROM statements)"
            params = None

        query += " ORDER BY institution_name, account_number, asset_category"

        return self.execute_query(query, params, fetch=True)

    def get_portfolio_value_trend(self, institution: str = None,
                                 start_date: datetime = None,
                                 end_date: datetime = None) -> List[Dict]:
        """Get portfolio value over time."""
        query = "SELECT * FROM v_portfolio_value_trend WHERE 1=1"
        params = []

        if institution:
            query += " AND institution_name = %s"
            params.append(institution)

        if start_date:
            query += " AND statement_date >= %s"
            params.append(start_date)

        if end_date:
            query += " AND statement_date <= %s"
            params.append(end_date)

        query += " ORDER BY statement_date, institution_name, account_number"

        return self.execute_query(query, tuple(params) if params else None, fetch=True)
