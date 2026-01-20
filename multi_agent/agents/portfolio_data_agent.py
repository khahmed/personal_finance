"""
Portfolio Data Agent - Data Specialist and Context Provider.
"""

from typing import Dict, Any, Optional, List
from crewai import Agent, Task
from .base_agent import BaseAgent
from ..tools.database_tools import DatabaseTools
from ..schemas.agent_outputs import PortfolioDataOutput
import logging

logger = logging.getLogger(__name__)


class PortfolioDataAgent(BaseAgent):
    """Agent responsible for portfolio data retrieval and aggregation."""
    
    def __init__(self, model: str = "deepseek-chat", temperature: float = 0.1):
        """Initialize Portfolio Data Agent."""
        self.db_tools = DatabaseTools()
        
        super().__init__(
            name="PortfolioDataAgent",
            role="Data Specialist and Context Provider",
            goal="Retrieve, aggregate, and provide accurate portfolio data to other agents",
            backstory="""You are an expert data analyst specializing in financial portfolio data.
            You have deep knowledge of SQL and database systems. You ensure data accuracy and
            provide comprehensive portfolio context including holdings, allocation, and metrics.
            You always validate data before sharing it with other agents.""",
            tools=[],  # Tools are accessed directly via db_tools
            model=model,
            temperature=temperature,
            verbose=True
        )
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get comprehensive portfolio summary."""
        return self.db_tools.get_portfolio_summary()
    
    def get_holdings(self, institution: Optional[str] = None,
                    account_number: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get latest holdings."""
        return self.db_tools.get_latest_holdings(institution, account_number)
    
    def get_allocation(self, institution: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get portfolio allocation."""
        return self.db_tools.get_portfolio_allocation(institution)
    
    def get_value_trend(self, institution: Optional[str] = None,
                       start_date: Optional[str] = None,
                       end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get portfolio value over time."""
        from datetime import datetime
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        return self.db_tools.get_value_over_time(institution, start, end)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get portfolio metrics including concentration and diversification."""
        concentration = self.db_tools.get_concentration_risk()
        diversification = self.db_tools.get_diversification_score()
        
        return {
            "concentration_metrics": concentration,
            "diversification_metrics": diversification
        }
    
    def process_request(self, request: Dict[str, Any]) -> PortfolioDataOutput:
        """
        Process a data request and return structured output.
        
        Args:
            request: Request dictionary with action and filters
            
        Returns:
            PortfolioDataOutput with requested data
        """
        action = request.get("action", "get_all")
        filters = request.get("filters", {})
        
        institution = filters.get("institution")
        account_number = filters.get("account_number")
        
        try:
            # Get portfolio summary
            portfolio_summary = self.get_portfolio_summary()
            
            # Get holdings
            holdings = self.get_holdings(institution, account_number)
            
            # Get allocation
            allocation = self.get_allocation(institution)
            
            # Get metrics
            metrics = self.get_metrics()
            
            return PortfolioDataOutput(
                portfolio_summary=portfolio_summary,
                holdings=holdings,
                allocation={"by_category": allocation} if allocation else {},
                concentration_metrics=metrics.get("concentration_metrics", {}),
                diversification_metrics=metrics.get("diversification_metrics", {})
            )
        except Exception as e:
            logger.error(f"Error processing portfolio data request: {e}")
            return PortfolioDataOutput()

