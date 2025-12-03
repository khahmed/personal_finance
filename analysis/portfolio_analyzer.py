"""
Portfolio analysis module for analyzing holdings and trends over time.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from database.db_manager import DatabaseManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PortfolioAnalyzer:
    """Analyzes portfolio holdings and performance over time."""

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the portfolio analyzer.

        Args:
            db_manager: DatabaseManager instance
        """
        self.db = db_manager

    def get_current_allocation(self, institution: str = None) -> pd.DataFrame:
        """
        Get current portfolio allocation by asset category.

        Args:
            institution: Optional institution filter

        Returns:
            DataFrame with allocation data
        """
        data = self.db.get_portfolio_allocation()
        df = pd.DataFrame(data)

        if df.empty:
            logger.warning("No allocation data found")
            return df

        if institution:
            df = df[df['institution_name'] == institution]

        # Calculate percentages
        if not df.empty:
            # Convert Decimal to float to avoid type mismatch
            df['total_value'] = df['total_value'].astype(float)
            total_by_account = df.groupby(['institution_name', 'account_number'])['total_value'].transform('sum')
            df['percentage'] = (df['total_value'] / total_by_account * 100).round(2)

        return df

    def get_portfolio_summary(self) -> Dict:
        """
        Get a summary of the entire portfolio.

        Returns:
            Dictionary with portfolio summary statistics
        """
        holdings = self.db.get_latest_holdings()
        df = pd.DataFrame(holdings)

        if df.empty:
            return {
                'total_value': 0,
                'num_accounts': 0,
                'num_securities': 0,
                'num_institutions': 0
            }

        summary = {
            'total_value': float(df['market_value'].sum()),
            'num_accounts': int(df[['institution_name', 'account_number']].drop_duplicates().shape[0]),
            'num_securities': int(df['security_name'].nunique()),
            'num_institutions': int(df['institution_name'].nunique()),
            'total_gain_loss': float((df['market_value'] - df['book_value']).sum()),
            'total_gain_loss_pct': float(((df['market_value'].sum() - df['book_value'].sum()) /
                                         df['book_value'].sum() * 100)) if df['book_value'].sum() > 0 else 0
        }

        # Breakdown by institution
        summary['by_institution'] = df.groupby('institution_name').agg({
            'market_value': 'sum',
            'security_name': 'nunique'
        }).to_dict()

        # Breakdown by asset category
        summary['by_asset_category'] = df.groupby('asset_category').agg({
            'market_value': 'sum'
        }).to_dict()

        return summary

    def get_holdings_by_account(self, institution: str = None,
                               account_number: str = None) -> pd.DataFrame:
        """
        Get detailed holdings for specific account(s).

        Args:
            institution: Optional institution filter
            account_number: Optional account number filter

        Returns:
            DataFrame with holdings data
        """
        holdings = self.db.get_latest_holdings(institution, account_number)
        df = pd.DataFrame(holdings)

        if not df.empty:
            # Convert Decimal to float to avoid type mismatch
            df['market_value'] = df['market_value'].astype(float)
            # Add some calculated columns
            df['weight'] = (df['market_value'] / df['market_value'].sum() * 100).round(2)

        return df

    def get_value_over_time(self, institution: str = None,
                           start_date: datetime = None,
                           end_date: datetime = None) -> pd.DataFrame:
        """
        Get portfolio value trend over time.

        Args:
            institution: Optional institution filter
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            DataFrame with value trend data
        """
        data = self.db.get_portfolio_value_trend(institution, start_date, end_date)
        df = pd.DataFrame(data)

        if not df.empty:
            df['statement_date'] = pd.to_datetime(df['statement_date'])
            df = df.sort_values('statement_date')

        return df

    def calculate_returns(self, institution: str = None,
                         account_number: str = None) -> pd.DataFrame:
        """
        Calculate returns for accounts over time.

        Args:
            institution: Optional institution filter
            account_number: Optional account number filter

        Returns:
            DataFrame with return calculations
        """
        df = self.get_value_over_time(institution)

        if df.empty:
            return df

        # Filter by account if specified
        if account_number:
            df = df[df['account_number'] == account_number]

        # Sort by date
        df = df.sort_values(['institution_name', 'account_number', 'statement_date'])

        # Convert Decimal to float to avoid type mismatch
        df['total_account_value'] = df['total_account_value'].astype(float)

        # Calculate returns
        df['prev_value'] = df.groupby(['institution_name', 'account_number'])['total_account_value'].shift(1)
        df['return_pct'] = ((df['total_account_value'] - df['prev_value']) / df['prev_value'] * 100).round(2)

        # Calculate cumulative returns
        df['cumulative_return'] = (
            (df['total_account_value'] /
             df.groupby(['institution_name', 'account_number'])['total_account_value'].transform('first') - 1) * 100
        ).round(2)

        return df

    def get_asset_allocation_trend(self, start_date: datetime = None,
                                   end_date: datetime = None) -> pd.DataFrame:
        """
        Get asset allocation changes over time.

        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            DataFrame with allocation trend data
        """
        # Get all statements within date range
        query = """
            SELECT
                s.statement_date,
                i.institution_name,
                a.account_number,
                at.asset_category,
                SUM(h.market_value) as total_value
            FROM holdings h
            JOIN statements s ON h.statement_id = s.statement_id
            JOIN accounts a ON h.account_id = a.account_id
            JOIN institutions i ON a.institution_id = i.institution_id
            JOIN securities sec ON h.security_id = sec.security_id
            JOIN asset_types at ON sec.asset_type_id = at.asset_type_id
            WHERE 1=1
        """
        params = []

        if start_date:
            query += " AND s.statement_date >= %s"
            params.append(start_date)

        if end_date:
            query += " AND s.statement_date <= %s"
            params.append(end_date)

        query += """
            GROUP BY s.statement_date, i.institution_name, a.account_number, at.asset_category
            ORDER BY s.statement_date, i.institution_name, a.account_number, at.asset_category
        """

        data = self.db.execute_query(query, tuple(params) if params else None, fetch=True)
        df = pd.DataFrame(data)

        if not df.empty:
            df['statement_date'] = pd.to_datetime(df['statement_date'])

            # Convert Decimal to float to avoid type mismatch
            df['total_value'] = df['total_value'].astype(float)

            # Calculate percentages by date
            total_by_date = df.groupby('statement_date')['total_value'].transform('sum')
            df['percentage'] = (df['total_value'] / total_by_date * 100).round(2)

        return df

    def get_top_holdings(self, n: int = 10) -> pd.DataFrame:
        """
        Get top N holdings by market value.

        Args:
            n: Number of top holdings to return

        Returns:
            DataFrame with top holdings
        """
        holdings = self.db.get_latest_holdings()
        df = pd.DataFrame(holdings)

        if df.empty:
            return df

        # Convert Decimal to float to avoid type mismatch
        df['market_value'] = df['market_value'].astype(float)

        # Sort by market value and get top N
        df = df.nlargest(n, 'market_value')

        # Calculate percentage of total portfolio
        total_value = df['market_value'].sum()
        df['portfolio_pct'] = (df['market_value'] / total_value * 100).round(2)

        return df[['security_name', 'symbol', 'asset_category', 'quantity',
                  'price', 'market_value', 'portfolio_pct', 'institution_name',
                  'account_number']]

    def get_concentration_risk(self) -> Dict:
        """
        Analyze concentration risk in the portfolio.

        Returns:
            Dictionary with concentration metrics
        """
        holdings = self.db.get_latest_holdings()
        df = pd.DataFrame(holdings)

        if df.empty:
            return {}

        # Convert Decimal to float to avoid type mismatch
        df['market_value'] = df['market_value'].astype(float)

        total_value = df['market_value'].sum()

        # Top 5 holdings concentration
        top5_value = df.nlargest(5, 'market_value')['market_value'].sum()
        top5_pct = (top5_value / total_value * 100).round(2)

        # Top 10 holdings concentration
        top10_value = df.nlargest(10, 'market_value')['market_value'].sum()
        top10_pct = (top10_value / total_value * 100).round(2)

        # Asset category concentration
        category_concentration = df.groupby('asset_category')['market_value'].sum()
        max_category = category_concentration.idxmax()
        max_category_pct = (category_concentration.max() / total_value * 100).round(2)

        # Institution concentration
        institution_concentration = df.groupby('institution_name')['market_value'].sum()
        max_institution = institution_concentration.idxmax()
        max_institution_pct = (institution_concentration.max() / total_value * 100).round(2)

        return {
            'top5_concentration': float(top5_pct),
            'top10_concentration': float(top10_pct),
            'max_category': max_category,
            'max_category_pct': float(max_category_pct),
            'max_institution': max_institution,
            'max_institution_pct': float(max_institution_pct),
            'num_holdings': len(df)
        }

    def get_diversification_score(self) -> Dict:
        """
        Calculate diversification metrics.

        Returns:
            Dictionary with diversification scores
        """
        holdings = self.db.get_latest_holdings()
        df = pd.DataFrame(holdings)

        if df.empty:
            return {}

        total_value = df['market_value'].sum()
        weights = df['market_value'] / total_value

        # Herfindahl-Hirschman Index (HHI)
        # Lower is more diversified, ranges from 1/N to 1
        hhi = (weights ** 2).sum()

        # Effective number of holdings
        # Higher is more diversified
        effective_n = 1 / hhi

        # Asset category diversification
        category_weights = df.groupby('asset_category')['market_value'].sum() / total_value
        category_hhi = (category_weights ** 2).sum()
        category_effective_n = 1 / category_hhi

        return {
            'hhi': float(hhi),
            'effective_number_holdings': float(effective_n),
            'actual_number_holdings': len(df),
            'category_hhi': float(category_hhi),
            'category_effective_n': float(category_effective_n),
            'num_categories': len(category_weights),
            'diversification_ratio': float(effective_n / len(df))
        }
