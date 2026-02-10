#!/usr/bin/env python3
"""
Synthetic Financial Data Generator

Generates realistic synthetic financial data for portfolio demonstration purposes.
Creates accounts, securities, holdings, and statements over a 2-year period.

Usage:
    python generate_synthetic_data.py [--reset] [--portfolio-value VALUE] [--months MONTHS]
"""

import argparse
import random
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Tuple
import logging

from database.db_manager import DatabaseManager
from config import DB_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# SYNTHETIC SECURITIES DATA
# ============================================================================

SECURITIES_POOL = {
    'ETF': [
        {'symbol': 'VGRO', 'name': 'Vanguard Growth ETF Portfolio', 'base_price': 35.50, 'volatility': 0.15},
        {'symbol': 'VFV', 'name': 'Vanguard S&P 500 Index ETF', 'base_price': 115.20, 'volatility': 0.18},
        {'symbol': 'VCN', 'name': 'Vanguard FTSE Canada All Cap Index ETF', 'base_price': 45.80, 'volatility': 0.16},
        {'symbol': 'XAW', 'name': 'iShares Core MSCI All Country World ex Canada', 'base_price': 38.90, 'volatility': 0.17},
        {'symbol': 'XIC', 'name': 'iShares Core S&P/TSX Capped Composite Index ETF', 'base_price': 32.40, 'volatility': 0.14},
        {'symbol': 'ZAG', 'name': 'BMO Aggregate Bond Index ETF', 'base_price': 15.60, 'volatility': 0.08},
        {'symbol': 'VDY', 'name': 'Vanguard FTSE Canadian High Dividend Yield Index ETF', 'base_price': 48.30, 'volatility': 0.12},
        {'symbol': 'XEF', 'name': 'iShares Core MSCI EAFE IMI Index ETF', 'base_price': 29.70, 'volatility': 0.16},
        {'symbol': 'VIU', 'name': 'Vanguard FTSE Developed All Cap ex North America Index ETF', 'base_price': 34.20, 'volatility': 0.17},
        {'symbol': 'ZRE', 'name': 'BMO Equal Weight REITs Index ETF', 'base_price': 18.90, 'volatility': 0.19},
    ],
    'Stock': [
        {'symbol': 'TD.TO', 'name': 'Toronto-Dominion Bank', 'base_price': 82.50, 'volatility': 0.20},
        {'symbol': 'RY.TO', 'name': 'Royal Bank of Canada', 'base_price': 135.40, 'volatility': 0.18},
        {'symbol': 'BMO.TO', 'name': 'Bank of Montreal', 'base_price': 128.90, 'volatility': 0.19},
        {'symbol': 'ENB.TO', 'name': 'Enbridge Inc.', 'base_price': 52.30, 'volatility': 0.22},
        {'symbol': 'CNR.TO', 'name': 'Canadian National Railway', 'base_price': 165.70, 'volatility': 0.17},
        {'symbol': 'SU.TO', 'name': 'Suncor Energy Inc.', 'base_price': 42.80, 'volatility': 0.28},
        {'symbol': 'BCE.TO', 'name': 'BCE Inc.', 'base_price': 58.90, 'volatility': 0.15},
        {'symbol': 'T.TO', 'name': 'TELUS Corporation', 'base_price': 26.40, 'volatility': 0.16},
        {'symbol': 'SHOP.TO', 'name': 'Shopify Inc.', 'base_price': 98.50, 'volatility': 0.35},
        {'symbol': 'AAPL', 'name': 'Apple Inc.', 'base_price': 178.20, 'volatility': 0.25},
        {'symbol': 'MSFT', 'name': 'Microsoft Corporation', 'base_price': 412.50, 'volatility': 0.23},
        {'symbol': 'GOOGL', 'name': 'Alphabet Inc.', 'base_price': 142.80, 'volatility': 0.24},
        {'symbol': 'AMZN', 'name': 'Amazon.com Inc.', 'base_price': 178.90, 'volatility': 0.26},
        {'symbol': 'JPM', 'name': 'JPMorgan Chase & Co.', 'base_price': 195.30, 'volatility': 0.21},
    ],
    'Mutual Fund': [
        {'symbol': None, 'name': 'RBC Canadian Equity Fund', 'base_price': 42.50, 'volatility': 0.16},
        {'symbol': None, 'name': 'TD Canadian Bond Fund', 'base_price': 11.80, 'volatility': 0.07},
        {'symbol': None, 'name': 'Fidelity Global Equity Fund', 'base_price': 28.90, 'volatility': 0.19},
        {'symbol': None, 'name': 'BMO Balanced Fund', 'base_price': 24.60, 'volatility': 0.12},
        {'symbol': None, 'name': 'Scotia Canadian Dividend Fund', 'base_price': 18.30, 'volatility': 0.14},
        {'symbol': None, 'name': 'Mackenzie US Equity Fund', 'base_price': 52.70, 'volatility': 0.20},
    ],
    'Bond': [
        {'symbol': 'CAN.GOVT.5Y', 'name': 'Government of Canada 5-Year Bond', 'base_price': 98.50, 'volatility': 0.04},
        {'symbol': 'CAN.GOVT.10Y', 'name': 'Government of Canada 10-Year Bond', 'base_price': 97.30, 'volatility': 0.06},
        {'symbol': 'ONT.PROV.5Y', 'name': 'Province of Ontario 5-Year Bond', 'base_price': 99.20, 'volatility': 0.05},
    ],
    'GIC': [
        {'symbol': None, 'name': 'TD 5-Year GIC 4.5%', 'base_price': 10000.00, 'volatility': 0.0},
        {'symbol': None, 'name': 'RBC 3-Year GIC 4.0%', 'base_price': 15000.00, 'volatility': 0.0},
        {'symbol': None, 'name': 'BMO 1-Year GIC 3.5%', 'base_price': 5000.00, 'volatility': 0.0},
    ],
}


# Asset type classifications
ASSET_TYPE_MAPPING = {
    'ETF': ('ETF', 'Equity'),
    'Stock': ('Stock', 'Equity'),
    'Mutual Fund': ('Mutual Fund - Equity', 'Equity'),
    'Bond': ('Bond', 'Fixed Income'),
    'GIC': ('GIC', 'Fixed Income'),
}


# ============================================================================
# ACCOUNT CONFIGURATIONS
# ============================================================================

ACCOUNT_CONFIGS = [
    {
        'institution': 'DemoBank',
        'account_number': 'RRSP-001234',
        'account_type': 'RRSP',
        'account_name': 'Personal RRSP',
        'target_value': 450000,  # $450k
        'allocation': {
            'ETF': 0.60,
            'Stock': 0.20,
            'Mutual Fund': 0.10,
            'Bond': 0.10,
        },
        'monthly_contribution': 500,  # Monthly deposits
    },
    {
        'institution': 'DemoBank',
        'account_number': 'TFSA-005678',
        'account_type': 'TFSA',
        'account_name': 'Tax-Free Savings',
        'target_value': 150000,  # $150k
        'allocation': {
            'ETF': 0.70,
            'Stock': 0.25,
            'Mutual Fund': 0.05,
        },
        'monthly_contribution': 300,
    },
    {
        'institution': 'DemoInvestCo',
        'account_number': 'RRSP-987654',
        'account_type': 'RRSP',
        'account_name': 'Spousal RRSP',
        'target_value': 380000,  # $380k
        'allocation': {
            'ETF': 0.50,
            'Stock': 0.15,
            'Mutual Fund': 0.20,
            'Bond': 0.15,
        },
        'monthly_contribution': 400,
    },
    {
        'institution': 'DemoInvestCo',
        'account_number': 'NON-REG-112233',
        'account_type': 'Non-Registered',
        'account_name': 'Investment Account',
        'target_value': 520000,  # $520k
        'allocation': {
            'Stock': 0.50,
            'ETF': 0.30,
            'Bond': 0.20,
        },
        'monthly_contribution': 1000,
    },
    {
        'institution': 'WealthAdvisors',
        'account_number': 'LIRA-445566',
        'account_type': 'LIRA',
        'account_name': 'Locked-In Retirement',
        'target_value': 280000,  # $280k
        'allocation': {
            'ETF': 0.40,
            'Mutual Fund': 0.35,
            'Bond': 0.15,
            'GIC': 0.10,
        },
        'monthly_contribution': 0,  # Locked-in, no contributions
    },
    {
        'institution': 'WealthAdvisors',
        'account_number': 'RESP-778899',
        'account_type': 'RESP',
        'account_name': 'Education Savings',
        'target_value': 120000,  # $120k
        'allocation': {
            'ETF': 0.55,
            'Mutual Fund': 0.30,
            'Bond': 0.15,
        },
        'monthly_contribution': 200,
    },
]


# ============================================================================
# DATA GENERATION FUNCTIONS
# ============================================================================

class SyntheticDataGenerator:
    """Generates synthetic financial portfolio data."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.start_date = datetime.now() - timedelta(days=730)  # 2 years ago
        self.random = random.Random(42)  # Seed for reproducibility

    def generate_price_for_date(self, security: Dict, base_date: datetime,
                                current_date: datetime) -> float:
        """
        Generate a price for a security on a given date using geometric Brownian motion.

        Args:
            security: Security dictionary with base_price and volatility
            base_date: Starting date
            current_date: Date to generate price for

        Returns:
            Price as float
        """
        days_elapsed = (current_date - base_date).days
        if days_elapsed <= 0:
            return security['base_price']

        # Geometric Brownian Motion: S(t) = S(0) * exp((μ - σ²/2)t + σW(t))
        # μ = drift (expected return), σ = volatility, W(t) = Wiener process
        base_price = security['base_price']
        volatility = security['volatility']
        drift = 0.08 / 365  # 8% annual return, daily

        # Generate random walk
        daily_returns = []
        for _ in range(days_elapsed):
            random_shock = self.random.gauss(0, 1)
            daily_return = drift + volatility * random_shock / (365 ** 0.5)
            daily_returns.append(daily_return)

        # Calculate cumulative return
        cumulative_return = sum(daily_returns)
        price = base_price * (1 + cumulative_return)

        # GICs don't change price
        if security.get('volatility', 0) == 0:
            price = base_price

        return round(max(price, 0.01), 4)  # Ensure positive price

    def select_securities_for_account(self, account_config: Dict) -> List[Tuple[str, Dict]]:
        """
        Select securities for an account based on allocation.

        Args:
            account_config: Account configuration dictionary

        Returns:
            List of tuples (asset_type, security)
        """
        selected = []
        allocation = account_config['allocation']

        for asset_type, weight in allocation.items():
            if weight > 0:
                # Determine how many securities of this type
                if asset_type == 'GIC':
                    num_securities = self.random.randint(1, 2)
                elif asset_type == 'Bond':
                    num_securities = self.random.randint(1, 3)
                elif asset_type == 'Mutual Fund':
                    num_securities = self.random.randint(2, 4)
                elif asset_type == 'ETF':
                    num_securities = self.random.randint(3, 6)
                else:  # Stock
                    num_securities = self.random.randint(4, 8)

                # Select random securities from pool
                pool = SECURITIES_POOL.get(asset_type, [])
                if pool:
                    selected_securities = self.random.sample(
                        pool,
                        min(num_securities, len(pool))
                    )
                    for sec in selected_securities:
                        selected.append((asset_type, sec))

        return selected

    def calculate_quantity(self, target_value: float, price: float,
                          allocation_weight: float, num_positions: int) -> float:
        """
        Calculate quantity of shares/units to purchase.

        Args:
            target_value: Total account target value
            price: Security price
            allocation_weight: Weight of this asset type (0-1)
            num_positions: Number of positions in this asset type

        Returns:
            Quantity as float
        """
        position_value = (target_value * allocation_weight) / num_positions
        quantity = position_value / price

        # Round based on security type
        if price > 1000:  # GICs
            quantity = round(quantity, 0)
        elif price > 100:
            quantity = round(quantity, 2)
        else:
            quantity = round(quantity, 3)

        return max(quantity, 0.001)

    def generate_account_data(self, account_config: Dict,
                             statement_date: datetime) -> Dict:
        """
        Generate holdings data for an account on a specific date.

        Args:
            account_config: Account configuration
            statement_date: Date of statement

        Returns:
            Dictionary with account and holdings data
        """
        # Select securities for this account
        securities = self.select_securities_for_account(account_config)

        # Calculate growth based on months elapsed
        months_elapsed = (statement_date - self.start_date).days / 30
        contributions = account_config['monthly_contribution'] * months_elapsed

        # Add some market growth (7-10% annually)
        annual_return = self.random.uniform(0.07, 0.10)
        market_growth = account_config['target_value'] * (annual_return / 12) * months_elapsed

        current_target = account_config['target_value'] + contributions + market_growth

        # Group securities by asset type for allocation
        securities_by_type = {}
        for asset_type, security in securities:
            if asset_type not in securities_by_type:
                securities_by_type[asset_type] = []
            securities_by_type[asset_type].append(security)

        # Generate holdings
        holdings = []
        total_market_value = 0

        for asset_type, securities_list in securities_by_type.items():
            allocation_weight = account_config['allocation'].get(asset_type, 0)
            num_positions = len(securities_list)

            for security in securities_list:
                # Generate price for this date
                price = self.generate_price_for_date(
                    security, self.start_date, statement_date
                )

                # Calculate quantity
                quantity = self.calculate_quantity(
                    current_target, price, allocation_weight, num_positions
                )

                market_value = price * quantity

                # Book value (purchased ~1-3 years ago at lower price)
                years_held = self.random.uniform(0.5, 3.0)
                book_price = price * (1 - annual_return * years_held)
                book_value = max(book_price * quantity, market_value * 0.7)

                asset_type_name, asset_category = ASSET_TYPE_MAPPING.get(
                    asset_type, ('Stock', 'Equity')
                )

                holdings.append({
                    'symbol': security.get('symbol'),
                    'security_name': security['name'],
                    'quantity': quantity,
                    'price': price,
                    'book_value': round(book_value, 2),
                    'market_value': round(market_value, 2),
                    'asset_type': asset_type_name,
                    'asset_category': asset_category,
                    'currency': 'CAD',
                })

                total_market_value += market_value

        # Add cash balance (1-5% of portfolio)
        cash_balance = total_market_value * self.random.uniform(0.01, 0.05)

        return {
            'institution': account_config['institution'],
            'account_number': account_config['account_number'],
            'account_type': account_config['account_type'],
            'account_name': account_config['account_name'],
            'statement_date': statement_date,
            'period_start': statement_date.replace(day=1),
            'period_end': statement_date,
            'total_value': round(total_market_value + cash_balance, 2),
            'cash_balance': round(cash_balance, 2),
            'holdings': holdings,
        }

    def generate_all_data(self, months: int = 24):
        """
        Generate synthetic data for all accounts over specified months.

        Args:
            months: Number of months to generate (default 24 = 2 years)
        """
        logger.info(f"Generating synthetic data for {len(ACCOUNT_CONFIGS)} accounts over {months} months")

        # Generate statements quarterly
        statement_dates = []
        current = self.start_date

        for i in range(0, months, 3):  # Quarterly statements
            statement_date = current + timedelta(days=i * 30)
            statement_dates.append(statement_date)

        logger.info(f"Creating {len(statement_dates)} quarterly statements per account")

        total_statements = 0
        total_holdings = 0

        # Generate data for each account
        for account_config in ACCOUNT_CONFIGS:
            logger.info(f"Generating data for {account_config['institution']} - {account_config['account_number']}")

            for statement_date in statement_dates:
                # Generate holdings for this statement
                statement_data = self.generate_account_data(account_config, statement_date)

                # Save to database
                try:
                    self.db.save_statement_data(statement_data)
                    total_statements += 1
                    total_holdings += len(statement_data['holdings'])

                    logger.info(
                        f"  Saved statement for {statement_date.strftime('%Y-%m-%d')}: "
                        f"{len(statement_data['holdings'])} holdings, "
                        f"${statement_data['total_value']:,.2f} total value"
                    )
                except Exception as e:
                    logger.error(f"Error saving statement: {e}")
                    raise

        logger.info("=" * 70)
        logger.info("Synthetic data generation complete!")
        logger.info(f"  Total accounts: {len(ACCOUNT_CONFIGS)}")
        logger.info(f"  Total statements: {total_statements}")
        logger.info(f"  Total holdings created: {total_holdings}")
        logger.info("=" * 70)

        # Print portfolio summary
        self.print_summary()

    def print_summary(self):
        """Print summary statistics of generated data."""
        try:
            # Get latest portfolio value
            query = """
                SELECT
                    i.institution_name,
                    COUNT(DISTINCT a.account_id) as num_accounts,
                    SUM(s.total_value) as total_value
                FROM statements s
                JOIN accounts a ON s.account_id = a.account_id
                JOIN institutions i ON a.institution_id = i.institution_id
                WHERE s.statement_date = (SELECT MAX(statement_date) FROM statements)
                GROUP BY i.institution_name
                ORDER BY total_value DESC
            """
            results = self.db.execute_query(query, fetch=True)

            logger.info("\nPortfolio Summary (Latest Statement):")
            logger.info("-" * 70)

            grand_total = 0
            for row in results:
                logger.info(
                    f"  {row['institution_name']:20} - "
                    f"{row['num_accounts']} account(s): "
                    f"${float(row['total_value']):>12,.2f}"
                )
                grand_total += float(row['total_value'])

            logger.info("-" * 70)
            logger.info(f"  {'TOTAL PORTFOLIO':20}              ${grand_total:>12,.2f}")
            logger.info("=" * 70)

        except Exception as e:
            logger.error(f"Error generating summary: {e}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Generate synthetic financial data for portfolio demonstration'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset database before generating data (WARNING: deletes all existing data)'
    )
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Skip confirmation prompts (auto-confirm)'
    )
    parser.add_argument(
        '--months',
        type=int,
        default=24,
        help='Number of months of historical data to generate (default: 24)'
    )

    args = parser.parse_args()

    # Initialize database manager
    try:
        db = DatabaseManager(DB_CONFIG)
        logger.info("Connected to database successfully")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)

    try:
        # Reset database if requested
        if args.reset:
            logger.warning("Resetting database - ALL DATA WILL BE DELETED")
            if not args.yes:
                response = input("Are you sure? Type 'yes' to confirm: ")
                if response.lower() != 'yes':
                    logger.info("Reset cancelled")
                    sys.exit(0)
            db.reset_all_tables(confirm=True)
            logger.info("Database reset complete")

        # Generate synthetic data
        generator = SyntheticDataGenerator(db)
        generator.generate_all_data(months=args.months)

    except KeyboardInterrupt:
        logger.info("\nGeneration cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during data generation: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close_all_connections()


if __name__ == '__main__':
    main()
