"""
Workflow Orchestrator - Coordinates multi-agent workflows.
"""

from typing import Any, Dict, Optional
from ..agents.portfolio_data_agent import PortfolioDataAgent
from ..agents.tax_advisor_agent import TaxAdvisorAgent
from ..agents.estate_planner_agent import EstatePlannerAgent
from ..agents.investment_analyst_agent import InvestmentAnalystAgent
from ..schemas.workflow_state import WorkflowState, UserContext
from ..observability.hooks import (
    start_session,
    end_session,
    start_span,
    end_span,
    set_current_context,
)
from ..observability.events import SpanKind
import logging
import uuid

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """Orchestrates multi-agent workflows."""

    def __init__(self):
        self.portfolio_agent  = PortfolioDataAgent()
        self.tax_agent        = TaxAdvisorAgent()
        self.estate_agent     = EstatePlannerAgent()
        self.investment_agent = InvestmentAnalystAgent()

    def execute_sequential_workflow(
        self,
        query: str,
        user_context: Optional[Dict[str, Any]] = None,
        enable_evolution: bool = True,
        user_feedback: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute sequential analysis workflow.

        Steps: portfolio data → tax → estate → investment → (optional) evolution.

        Args:
            query:            User query string.
            user_context:     User context (tax bracket, province, age, …).
            enable_evolution: Run MetaEvolutionAgent as a post-workflow step.
            user_feedback:    Optional explicit feedback to log ('accepted',
                              'rejected', or 'modified').

        Returns:
            Comprehensive analysis results dict.
        """
        obs_session_id: Optional[str] = None
        try:
            obs_session_id = start_session(query=query, workflow_type="sequential")
            workflow_span_id = start_span(
                obs_session_id, None, SpanKind.WORKFLOW, "workflow", query=query or ""
            )

            state = WorkflowState(
                session_id=str(uuid.uuid4()),
                user_context=UserContext(**user_context) if user_context else UserContext(),
            )

            # ── Step 1: Portfolio data ─────────────────────────────────────
            logger.info("Step 1: Gathering portfolio data...")
            step_span_id = start_span(
                obs_session_id, workflow_span_id, SpanKind.AGENT, "portfolio_data"
            )
            set_current_context(obs_session_id, step_span_id)
            try:
                portfolio_data = self.portfolio_agent.process_request(
                    {"action": "get_all", "filters": {}}
                )
                state.data_cache["portfolio_data"] = portfolio_data.dict()
            finally:
                end_span(step_span_id)
                set_current_context(obs_session_id, workflow_span_id)

            # ── Step 2: Tax analysis ───────────────────────────────────────
            logger.info("Step 2: Analyzing tax optimization...")
            step_span_id = start_span(
                obs_session_id, workflow_span_id, SpanKind.AGENT, "tax_advisor"
            )
            set_current_context(obs_session_id, step_span_id)
            try:
                tax_analysis = self.tax_agent.analyze_portfolio(
                    portfolio_data.holdings, state.user_context.dict()
                )
                state.agent_outputs["tax_advisor"] = tax_analysis.dict()
            finally:
                end_span(step_span_id)
                set_current_context(obs_session_id, workflow_span_id)

            # ── Step 3: Estate planning ────────────────────────────────────
            logger.info("Step 3: Analyzing estate planning...")
            step_span_id = start_span(
                obs_session_id, workflow_span_id, SpanKind.AGENT, "estate_planner"
            )
            set_current_context(obs_session_id, step_span_id)
            try:
                estate_analysis = self.estate_agent.analyze_estate(
                    portfolio_data.portfolio_summary,
                    portfolio_data.holdings,
                    state.user_context.dict(),
                )
                state.agent_outputs["estate_planner"] = estate_analysis.dict()
            finally:
                end_span(step_span_id)
                set_current_context(obs_session_id, workflow_span_id)

            # ── Step 4: Investment analysis ────────────────────────────────
            logger.info("Step 4: Analyzing investments...")
            step_span_id = start_span(
                obs_session_id, workflow_span_id, SpanKind.AGENT, "investment_analyst"
            )
            set_current_context(obs_session_id, step_span_id)
            try:
                investment_analysis = self.investment_agent.analyze_investments(
                    portfolio_data.holdings,
                    portfolio_data.portfolio_summary,
                    state.user_context.dict(),
                )
                state.agent_outputs["investment_analyst"] = investment_analysis.dict()
            finally:
                end_span(step_span_id)
                set_current_context(obs_session_id, workflow_span_id)

            state.workflow_status = "completed"
            state.update()

            results = {
                "session_id":              state.session_id,
                "observability_session_id": obs_session_id,
                "portfolio_data":          portfolio_data.dict(),
                "tax_analysis":            tax_analysis.dict(),
                "estate_analysis":         estate_analysis.dict(),
                "investment_analysis":     investment_analysis.dict(),
                "workflow_state":          state.dict(),
            }

            # ── Step 5: Meta-evolution (optional) ─────────────────────────
            if enable_evolution:
                results = self._run_evolution_step(
                    results=results,
                    user_context=state.user_context.dict(),
                    user_feedback=user_feedback,
                    session_id=state.session_id,
                    obs_session_id=obs_session_id,
                    parent_span_id=workflow_span_id,
                )

            end_span(workflow_span_id)
            end_session(obs_session_id, status="completed")
            return results

        except Exception as e:
            logger.error(f"Error in sequential workflow: {e}")
            if obs_session_id:
                end_session(obs_session_id, status="error", error=str(e))
            return {"error": str(e), "status": "error"}

    def execute_parallel_workflow(
        self,
        query: str,
        user_context: Optional[Dict[str, Any]] = None,
        enable_evolution: bool = True,
        user_feedback: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute parallel analysis workflow.

        Step 1 (portfolio data) is sequential; steps 2–4 run in pseudo-parallel
        (same thread, consecutive calls – reserved for async upgrade).

        Args:
            query:            User query string.
            user_context:     User context.
            enable_evolution: Run MetaEvolutionAgent post-workflow.
            user_feedback:    Optional explicit feedback to log.

        Returns:
            Comprehensive analysis results dict.
        """
        obs_session_id: Optional[str] = None
        try:
            obs_session_id = start_session(query=query, workflow_type="parallel")
            workflow_span_id = start_span(
                obs_session_id, None, SpanKind.WORKFLOW, "workflow", query=query or ""
            )

            state = WorkflowState(
                session_id=str(uuid.uuid4()),
                user_context=UserContext(**user_context) if user_context else UserContext(),
            )

            logger.info("Gathering portfolio data...")
            step_span_id = start_span(
                obs_session_id, workflow_span_id, SpanKind.AGENT, "portfolio_data"
            )
            set_current_context(obs_session_id, step_span_id)
            try:
                portfolio_data = self.portfolio_agent.process_request(
                    {"action": "get_all", "filters": {}}
                )
                state.data_cache["portfolio_data"] = portfolio_data.dict()
            finally:
                end_span(step_span_id)
                set_current_context(obs_session_id, workflow_span_id)

            logger.info("Executing parallel analysis...")
            span_ids = [
                start_span(obs_session_id, workflow_span_id, SpanKind.AGENT, name)
                for name in ("tax_advisor", "estate_planner", "investment_analyst")
            ]

            set_current_context(obs_session_id, span_ids[0])
            try:
                tax_analysis = self.tax_agent.analyze_portfolio(
                    portfolio_data.holdings, state.user_context.dict()
                )
            finally:
                end_span(span_ids[0])

            set_current_context(obs_session_id, span_ids[1])
            try:
                estate_analysis = self.estate_agent.analyze_estate(
                    portfolio_data.portfolio_summary,
                    portfolio_data.holdings,
                    state.user_context.dict(),
                )
            finally:
                end_span(span_ids[1])

            set_current_context(obs_session_id, span_ids[2])
            try:
                investment_analysis = self.investment_agent.analyze_investments(
                    portfolio_data.holdings,
                    portfolio_data.portfolio_summary,
                    state.user_context.dict(),
                )
            finally:
                end_span(span_ids[2])

            set_current_context(obs_session_id, workflow_span_id)
            state.agent_outputs["tax_advisor"]       = tax_analysis.dict()
            state.agent_outputs["estate_planner"]    = estate_analysis.dict()
            state.agent_outputs["investment_analyst"] = investment_analysis.dict()
            state.workflow_status = "completed"
            state.update()

            results = {
                "session_id":              state.session_id,
                "observability_session_id": obs_session_id,
                "portfolio_data":          portfolio_data.dict(),
                "tax_analysis":            tax_analysis.dict(),
                "estate_analysis":         estate_analysis.dict(),
                "investment_analysis":     investment_analysis.dict(),
                "workflow_state":          state.dict(),
            }

            if enable_evolution:
                results = self._run_evolution_step(
                    results=results,
                    user_context=state.user_context.dict(),
                    user_feedback=user_feedback,
                    session_id=state.session_id,
                    obs_session_id=obs_session_id,
                    parent_span_id=workflow_span_id,
                )

            end_span(workflow_span_id)
            end_session(obs_session_id, status="completed")
            return results

        except Exception as e:
            logger.error(f"Error in parallel workflow: {e}")
            if obs_session_id:
                end_session(obs_session_id, status="error", error=str(e))
            return {"error": str(e), "status": "error"}

    # ── private helpers ───────────────────────────────────────────────────────

    def _run_evolution_step(
        self,
        results: Dict[str, Any],
        user_context: Dict[str, Any],
        user_feedback: Optional[str],
        session_id: str,
        obs_session_id: str,
        parent_span_id: str,
    ) -> Dict[str, Any]:
        """Run MetaEvolutionAgent and attach its output to results."""
        evolution_span_id = start_span(
            obs_session_id, parent_span_id, SpanKind.AGENT, "meta_evolution"
        )
        set_current_context(obs_session_id, evolution_span_id)
        try:
            from ..agents.meta_evolution_agent import MetaEvolutionAgent
            meta_agent = MetaEvolutionAgent()
            evolution_result = meta_agent.evaluate_and_evolve(
                workflow_results=results,
                user_context=user_context,
                user_feedback=user_feedback,
                session_id=session_id,
            )
            results["evolution"] = evolution_result
            if evolution_result.get("evolved"):
                updated = list(evolution_result.get("updates", {}).keys())
                logger.info(f"Evolution complete. Updated agents: {updated}")
        except Exception as e:
            logger.warning(f"Evolution step failed (non-fatal): {e}")
            results["evolution"] = {"evolved": False, "skipped_reason": str(e)}
        finally:
            end_span(evolution_span_id)
            set_current_context(obs_session_id, parent_span_id)

        return results
