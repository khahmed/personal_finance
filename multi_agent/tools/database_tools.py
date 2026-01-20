"""
Database tools for Portfolio Data Agent.
"""

import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.db_manager import DatabaseManager
from config import DB_CONFIG
from analysis.portfolio_analyzer import PortfolioAnalyzer
import logging

logger = logging.getLogger(__name__)


class DatabaseTools:
    """Tools for querying the portfolio database."""
    
    def __init__(self):
        """Initialize database connection."""
        try:
            self.db_manager = DatabaseManager(DB_CONFIG)
            self.analyzer = PortfolioAnalyzer(self.db_manager)
            logger.info("Database tools initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database tools: {e}")
            self.db_manager = None
            self.analyzer = None
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive portfolio summary.
        
        Returns:
            Dictionary with portfolio summary statistics
        """
        if not self.analyzer:
            return {"error": "Database not initialized"}
        
        try:
            summary = self.analyzer.get_portfolio_summary()
            return summary
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return {"error": str(e)}
    
    def get_latest_holdings(self, institution: Optional[str] = None,
                           account_number: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get latest holdings, optionally filtered.
        
        Args:
            institution: Optional institution filter
            account_number: Optional account number filter
            
        Returns:
            List of holding dictionaries
        """
        if not self.db_manager:
            return []
        
        try:
            holdings = self.db_manager.get_latest_holdings(institution, account_number)
            # Convert to list of dicts
            return [dict(h) for h in holdings]
        except Exception as e:
            logger.error(f"Error getting holdings: {e}")
            return []
    
    def get_portfolio_allocation(self, institution: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get portfolio allocation by asset category.
        
        Args:
            institution: Optional institution filter
            
        Returns:
            List of allocation dictionaries
        """
        if not self.analyzer:
            return []
        
        try:
            df = self.analyzer.get_current_allocation(institution)
            if df.empty:
                return []
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Error getting allocation: {e}")
            return []
    
    def get_value_over_time(self, institution: Optional[str] = None,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get portfolio value trend over time.
        
        Args:
            institution: Optional institution filter
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            List of value trend dictionaries
        """
        if not self.analyzer:
            return []
        
        try:
            df = self.analyzer.get_value_over_time(institution, start_date, end_date)
            if df.empty:
                return []
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Error getting value trend: {e}")
            return []
    
    def get_concentration_risk(self) -> Dict[str, Any]:
        """
        Get concentration risk metrics.
        
        Returns:
            Dictionary with concentration metrics
        """
        if not self.analyzer:
            return {}
        
        try:
            return self.analyzer.get_concentration_risk()
        except Exception as e:
            logger.error(f"Error getting concentration risk: {e}")
            return {}
    
    def get_diversification_score(self) -> Dict[str, Any]:
        """
        Get diversification metrics.
        
        Returns:
            Dictionary with diversification scores
        """
        if not self.analyzer:
            return {}
        
        try:
            return self.analyzer.get_diversification_score()
        except Exception as e:
            logger.error(f"Error getting diversification score: {e}")
            return {}
    
    def get_holdings_by_account(self, institution: Optional[str] = None,
                               account_number: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get detailed holdings for specific account(s).
        
        Args:
            institution: Optional institution filter
            account_number: Optional account number filter
            
        Returns:
            List of holding dictionaries
        """
        if not self.analyzer:
            return []
        
        try:
            df = self.analyzer.get_holdings_by_account(institution, account_number)
            if df.empty:
                return []
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Error getting holdings by account: {e}")
            return []
    
    def execute_custom_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a custom SQL query (read-only).
        
        Args:
            query: SQL SELECT query
            params: Optional query parameters
            
        Returns:
            List of result dictionaries
        """
        if not self.db_manager:
            return []
        
        try:
            # Basic validation - only SELECT queries
            if not query.strip().upper().startswith('SELECT'):
                logger.warning("Non-SELECT query rejected")
                return []
            
            results = self.db_manager.execute_query(query, params, fetch=True)
            return [dict(r) for r in results]
        except Exception as e:
            logger.error(f"Error executing custom query: {e}")
            return []

