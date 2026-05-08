"""
Financial Advisory Flow - Main entry point for financial advisory workflows.
"""

from typing import Any, Dict, Optional
from ..flows.workflow_orchestrator import WorkflowOrchestrator
import logging

logger = logging.getLogger(__name__)


class FinancialAdvisoryFlow:
    """Main flow controller for financial advisory workflows."""

    def __init__(self):
        self.orchestrator = WorkflowOrchestrator()

    def process_query(
        self,
        query: str,
        user_context: Optional[Dict[str, Any]] = None,
        workflow_type: str = "sequential",
        enable_evolution: bool = True,
        user_feedback: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a user query through the multi-agent system.

        Args:
            query:            User's natural language query.
            user_context:     User context (tax bracket, province, age, …).
            workflow_type:    "sequential" or "parallel".
            enable_evolution: Whether to run MetaEvolutionAgent post-workflow.
            user_feedback:    Optional explicit feedback ('accepted', 'rejected',
                              'modified') recorded for future evolution decisions.

        Returns:
            Comprehensive analysis results dict, including an 'evolution' key
            when enable_evolution is True.
        """
        try:
            logger.info(f"Processing query: {query}")
            logger.info(f"Workflow type: {workflow_type}, evolution: {enable_evolution}")

            if workflow_type == "parallel":
                return self.orchestrator.execute_parallel_workflow(
                    query, user_context,
                    enable_evolution=enable_evolution,
                    user_feedback=user_feedback,
                )
            else:
                return self.orchestrator.execute_sequential_workflow(
                    query, user_context,
                    enable_evolution=enable_evolution,
                    user_feedback=user_feedback,
                )
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {"error": str(e), "status": "error", "query": query}

    def get_comprehensive_review(
        self,
        user_context: Optional[Dict[str, Any]] = None,
        enable_evolution: bool = True,
        user_feedback: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get a comprehensive financial review.

        Args:
            user_context:     User context information.
            enable_evolution: Whether to run the evolution step.
            user_feedback:    Optional explicit feedback to log.

        Returns:
            Comprehensive financial review dict.
        """
        query = (
            "Provide a comprehensive financial review including tax optimization, "
            "estate planning, and investment analysis"
        )
        return self.process_query(
            query, user_context,
            workflow_type="sequential",
            enable_evolution=enable_evolution,
            user_feedback=user_feedback,
        )
