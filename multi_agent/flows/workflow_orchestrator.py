"""
Workflow Orchestrator - Coordinates multi-agent workflows.
"""

from typing import Dict, Any, Optional, List
from ..agents.portfolio_data_agent import PortfolioDataAgent
from ..agents.tax_advisor_agent import TaxAdvisorAgent
from ..agents.estate_planner_agent import EstatePlannerAgent
from ..agents.investment_analyst_agent import InvestmentAnalystAgent
from ..schemas.workflow_state import WorkflowState, UserContext
import logging
import uuid

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """Orchestrates multi-agent workflows."""
    
    def __init__(self):
        """Initialize orchestrator with agents."""
        self.portfolio_agent = PortfolioDataAgent()
        self.tax_agent = TaxAdvisorAgent()
        self.estate_agent = EstatePlannerAgent()
        self.investment_agent = InvestmentAnalystAgent()
    
    def execute_sequential_workflow(self, query: str,
                                   user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute sequential analysis workflow.
        
        Args:
            query: User query
            user_context: User context information
            
        Returns:
            Comprehensive analysis results
        """
        try:
            # Create workflow state
            state = WorkflowState(
                session_id=str(uuid.uuid4()),
                user_context=UserContext(**user_context) if user_context else UserContext()
            )
            
            # Step 1: Get portfolio data
            logger.info("Step 1: Gathering portfolio data...")
            portfolio_request = {"action": "get_all", "filters": {}}
            portfolio_data = self.portfolio_agent.process_request(portfolio_request)
            state.data_cache["portfolio_data"] = portfolio_data.dict()
            
            # Step 2: Tax analysis
            logger.info("Step 2: Analyzing tax optimization...")
            tax_analysis = self.tax_agent.analyze_portfolio(
                portfolio_data.holdings,
                state.user_context.dict()
            )
            state.agent_outputs["tax_advisor"] = tax_analysis.dict()
            
            # Step 3: Estate planning
            logger.info("Step 3: Analyzing estate planning...")
            estate_analysis = self.estate_agent.analyze_estate(
                portfolio_data.portfolio_summary,
                portfolio_data.holdings,
                state.user_context.dict()
            )
            state.agent_outputs["estate_planner"] = estate_analysis.dict()
            
            # Step 4: Investment analysis
            logger.info("Step 4: Analyzing investments...")
            investment_analysis = self.investment_agent.analyze_investments(
                portfolio_data.holdings,
                portfolio_data.portfolio_summary,
                state.user_context.dict()
            )
            state.agent_outputs["investment_analyst"] = investment_analysis.dict()
            
            # Update state
            state.workflow_status = "completed"
            state.update()
            
            return {
                "session_id": state.session_id,
                "portfolio_data": portfolio_data.dict(),
                "tax_analysis": tax_analysis.dict(),
                "estate_analysis": estate_analysis.dict(),
                "investment_analysis": investment_analysis.dict(),
                "workflow_state": state.dict()
            }
        except Exception as e:
            logger.error(f"Error in sequential workflow: {e}")
            return {"error": str(e), "status": "error"}
    
    def execute_parallel_workflow(self, query: str,
                                  user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute parallel analysis workflow.
        
        Args:
            query: User query
            user_context: User context information
            
        Returns:
            Comprehensive analysis results
        """
        try:
            # Create workflow state
            state = WorkflowState(
                session_id=str(uuid.uuid4()),
                user_context=UserContext(**user_context) if user_context else UserContext()
            )
            
            # Step 1: Get portfolio data (required for all)
            logger.info("Gathering portfolio data...")
            portfolio_request = {"action": "get_all", "filters": {}}
            portfolio_data = self.portfolio_agent.process_request(portfolio_request)
            state.data_cache["portfolio_data"] = portfolio_data.dict()
            
            # Step 2: Parallel execution of analysis agents
            logger.info("Executing parallel analysis...")
            
            # In a real implementation, these would run in parallel threads/processes
            tax_analysis = self.tax_agent.analyze_portfolio(
                portfolio_data.holdings,
                state.user_context.dict()
            )
            
            estate_analysis = self.estate_agent.analyze_estate(
                portfolio_data.portfolio_summary,
                portfolio_data.holdings,
                state.user_context.dict()
            )
            
            investment_analysis = self.investment_agent.analyze_investments(
                portfolio_data.holdings,
                portfolio_data.portfolio_summary,
                state.user_context.dict()
            )
            
            # Aggregate results
            state.agent_outputs["tax_advisor"] = tax_analysis.dict()
            state.agent_outputs["estate_planner"] = estate_analysis.dict()
            state.agent_outputs["investment_analyst"] = investment_analysis.dict()
            
            state.workflow_status = "completed"
            state.update()
            
            return {
                "session_id": state.session_id,
                "portfolio_data": portfolio_data.dict(),
                "tax_analysis": tax_analysis.dict(),
                "estate_analysis": estate_analysis.dict(),
                "investment_analysis": investment_analysis.dict(),
                "workflow_state": state.dict()
            }
        except Exception as e:
            logger.error(f"Error in parallel workflow: {e}")
            return {"error": str(e), "status": "error"}

