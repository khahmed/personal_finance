"""
Financial Advisory Flow - Main entry point for financial advisory workflows.
"""

from typing import Dict, Any, Optional
from ..flows.workflow_orchestrator import WorkflowOrchestrator
import logging

logger = logging.getLogger(__name__)


class FinancialAdvisoryFlow:
    """Main flow controller for financial advisory workflows."""
    
    def __init__(self):
        """Initialize the flow."""
        self.orchestrator = WorkflowOrchestrator()
    
    def process_query(self, query: str, user_context: Optional[Dict[str, Any]] = None,
                     workflow_type: str = "sequential") -> Dict[str, Any]:
        """
        Process a user query through the multi-agent system.
        
        Args:
            query: User's natural language query
            user_context: User context (tax bracket, province, age, etc.)
            workflow_type: "sequential" or "parallel"
            
        Returns:
            Comprehensive analysis results
        """
        try:
            logger.info(f"Processing query: {query}")
            logger.info(f"Workflow type: {workflow_type}")
            
            if workflow_type == "parallel":
                return self.orchestrator.execute_parallel_workflow(query, user_context)
            else:
                return self.orchestrator.execute_sequential_workflow(query, user_context)
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "error": str(e),
                "status": "error",
                "query": query
            }
    
    def get_comprehensive_review(self, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get a comprehensive financial review.
        
        Args:
            user_context: User context information
            
        Returns:
            Comprehensive financial review
        """
        query = "Provide a comprehensive financial review including tax optimization, "
        query += "estate planning, and investment analysis"
        
        return self.process_query(query, user_context, workflow_type="sequential")

