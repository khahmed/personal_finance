"""
MetaEvolutionAgent - Runtime agent that evaluates workflow outputs and evolves
agent configurations stored in the database.

Lifecycle
─────────
1. WorkflowOrchestrator calls evaluate_and_evolve() after every completed run.
2. The agent records each sub-agent's interaction in agent_interactions.
3. If the LLM is available and enough interactions have been logged, it calls
   the LLM to critique outputs and propose targeted updates.
4. Proposals that exceed the confidence threshold are written as new versioned
   configs in agent_configs (old version deactivated, new version activated).
5. The next workflow run automatically loads the evolved config for each agent.

Rollback: AgentConfigStore.rollback_to_version(agent_name, version) restores
any prior version at any time.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

_DEFAULT_RULES: Dict[str, Any] = {
    "min_interactions_before_evolution": 3,
    "min_confidence_to_evolve":          0.7,
    "max_versions_per_agent":            10,
    "evolution_cooldown_hours":          24,
}

# Agents that MetaEvolutionAgent is allowed to evolve
_EVOLVABLE_AGENTS = [
    "TaxAdvisorAgent",
    "EstatePlannerAgent",
    "InvestmentAnalystAgent",
]


class MetaEvolutionAgent(BaseAgent):
    """Evaluates agent outputs and evolves their configs based on LLM critique."""

    def __init__(self, model: str = "deepseek-chat", temperature: float = 0.2):
        super().__init__(
            name="MetaEvolutionAgent",
            role="Agent Evolution Specialist",
            goal=(
                "Monitor agent performance and evolve agent configurations "
                "based on interaction patterns"
            ),
            backstory=(
                "You are an AI meta-agent responsible for continuously improving other financial "
                "advisory agents. You evaluate the quality of agent outputs, identify patterns in "
                "user feedback, and propose targeted improvements to agent prompts and business rules. "
                "You are conservative: you only propose changes when there is clear evidence of "
                "improvement, and you always preserve version history for rollback."
            ),
            tools=[],
            model=model,
            temperature=temperature,
            verbose=True,
        )

        self.business_rules = {**_DEFAULT_RULES, **self.business_rules}

        # Lazy-loaded config store
        self._config_store = None

    def _rule(self, key: str) -> Any:
        return self.business_rules.get(key, _DEFAULT_RULES.get(key))

    @property
    def config_store(self):
        if self._config_store is None:
            try:
                from ..config.agent_config_store import AgentConfigStore
                self._config_store = AgentConfigStore.get_instance()
            except Exception as e:
                logger.warning(f"MetaEvolutionAgent: config store unavailable: {e}")
        return self._config_store

    # ── main entry point ─────────────────────────────────────────────────────

    def evaluate_and_evolve(
        self,
        workflow_results: Dict[str, Any],
        user_context: Dict[str, Any],
        user_feedback: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate completed workflow outputs and evolve agent configs if warranted.

        Args:
            workflow_results: Full results dict from WorkflowOrchestrator.
            user_context:     The user context used in the run.
            user_feedback:    Optional explicit feedback ('accepted'/'rejected'/'modified').
            session_id:       Session ID for interaction logging.

        Returns:
            Dict with keys: evolved (bool), updates (dict), critique_summary (str),
            skipped_reason (str if skipped).
        """
        # ── 1. Record interaction for every evolvable agent ──────────────────
        if self.config_store and session_id:
            for agent_name in _EVOLVABLE_AGENTS:
                output_summary = self._extract_output_summary(workflow_results, agent_name)
                current_config = self.config_store.get_config(agent_name) or {}
                self.config_store.record_interaction(
                    session_id=session_id,
                    agent_name=agent_name,
                    output_summary=output_summary,
                    user_feedback=user_feedback,
                    config_version=current_config.get("version", 1),
                )

        # ── 2. Require LLM ───────────────────────────────────────────────────
        if not self.use_llm_analysis():
            logger.debug("MetaEvolutionAgent: LLM unavailable, skipping evolution")
            return {"evolved": False, "skipped_reason": "LLM not available"}

        # ── 3. Check interaction threshold ───────────────────────────────────
        if self.config_store:
            min_interactions = int(self._rule("min_interactions_before_evolution"))
            for agent_name in _EVOLVABLE_AGENTS:
                count = self.config_store.get_interaction_count(agent_name)
                if count < min_interactions:
                    logger.debug(
                        f"MetaEvolutionAgent: {agent_name} has {count}/{min_interactions} "
                        "interactions, skipping evolution"
                    )
                    return {
                        "evolved": False,
                        "skipped_reason": (
                            f"Insufficient interactions for {agent_name} "
                            f"({count}/{min_interactions})"
                        ),
                    }

        # ── 4. Critique outputs via LLM ──────────────────────────────────────
        critique = self._critique_outputs(workflow_results, user_context)
        if not critique:
            return {"evolved": False, "skipped_reason": "LLM critique failed or returned no JSON"}

        # ── 5. Apply high-confidence proposals ──────────────────────────────
        min_confidence = float(self._rule("min_confidence_to_evolve"))
        evolution_results: Dict[str, Any] = {}

        for agent_name in _EVOLVABLE_AGENTS:
            agent_critique = critique.get(agent_name, {})
            confidence = float(agent_critique.get("confidence", 0.0))
            if confidence < min_confidence:
                logger.debug(
                    f"MetaEvolutionAgent: {agent_name} confidence {confidence:.2f} "
                    f"below threshold {min_confidence:.2f}, skipping"
                )
                continue

            proposed = agent_critique.get("proposed_updates", {})
            if not proposed:
                continue

            reason = agent_critique.get("reason", "LLM-driven evolution")
            if self.config_store:
                new_version = self.config_store.save_new_version(
                    agent_name=agent_name,
                    updates=proposed,
                    reason=f"[confidence={confidence:.2f}] {reason}",
                )
                if new_version:
                    evolution_results[agent_name] = {
                        "evolved":     True,
                        "new_version": new_version,
                        "confidence":  confidence,
                        "reason":      reason,
                    }
                    logger.info(
                        f"MetaEvolutionAgent: {agent_name} evolved to v{new_version} "
                        f"(confidence={confidence:.2f})"
                    )

        return {
            "evolved":          len(evolution_results) > 0,
            "updates":          evolution_results,
            "critique_summary": critique.get("overall_summary", ""),
        }

    # ── LLM critique ─────────────────────────────────────────────────────────

    def _critique_outputs(
        self,
        workflow_results: Dict[str, Any],
        user_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Ask the LLM to evaluate agent outputs and return structured proposals.
        Returns a dict keyed by agent name, or {} on failure.
        """
        context_for_llm = self._build_critique_context(workflow_results, user_context)

        system_prompt = (
            self.system_prompts.get("meta")
            or (
                "You are a meta-agent evaluating the quality of financial advisory outputs. "
                "Your goal is to identify specific, actionable improvements to agent prompts "
                "and business rules. Be precise, conservative, and evidence-based. "
                "Return ONLY valid JSON — no prose before or after."
            )
        )

        prompt = f"""Review the following agent outputs and user context.

{json.dumps(context_for_llm, indent=2, default=str)}

For each agent in TaxAdvisorAgent, EstatePlannerAgent, InvestmentAnalystAgent, assess:
1. Were recommendations specific to the user's context (age, province, risk profile)?
2. Are the business rule thresholds appropriate for this user?
3. Could role/goal/backstory text be improved?

Return ONLY valid JSON matching this exact structure (no markdown, no extra text):
{{
  "overall_summary": "One sentence overall assessment",
  "TaxAdvisorAgent": {{
    "quality_score": 0.0,
    "confidence": 0.0,
    "issues": [],
    "reason": "Why this update is needed",
    "proposed_updates": {{
      "backstory": null,
      "goal": null,
      "business_rules": {{}}
    }}
  }},
  "EstatePlannerAgent": {{
    "quality_score": 0.0,
    "confidence": 0.0,
    "issues": [],
    "reason": "",
    "proposed_updates": {{
      "backstory": null,
      "goal": null,
      "business_rules": {{}}
    }}
  }},
  "InvestmentAnalystAgent": {{
    "quality_score": 0.0,
    "confidence": 0.0,
    "issues": [],
    "reason": "",
    "proposed_updates": {{
      "backstory": null,
      "goal": null,
      "business_rules": {{}}
    }}
  }}
}}

Rules:
- confidence must be 0.0–1.0; only set > 0.7 when you have specific, concrete improvements.
- For backstory/goal: set to null if no change needed, otherwise provide the full new text.
- For business_rules: include ONLY keys you want to change and their new values.
- Do not invent thresholds; only adjust based on clear evidence from the outputs.
"""

        response = self.llm_tools.analyze_with_llm(
            prompt, system_prompt, temperature=0.3, max_tokens=3000
        )

        if not response:
            return {}

        return self._parse_json_response(response)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _build_critique_context(
        self,
        workflow_results: Dict[str, Any],
        user_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build a condensed context dict for the LLM (avoids sending all holdings)."""
        context: Dict[str, Any] = {
            "user_context": {
                "age":          user_context.get("age"),
                "province":     user_context.get("province"),
                "risk_profile": user_context.get("risk_profile"),
                "tax_rate":     user_context.get("tax_rate"),
                "tax_bracket":  user_context.get("tax_bracket"),
            },
            "agent_outputs": {},
        }

        tax = workflow_results.get("tax_analysis", {})
        if tax:
            report = tax.get("tax_optimization_report", {})
            context["agent_outputs"]["TaxAdvisorAgent"] = {
                "num_recommendations":  len(tax.get("recommendations", [])),
                "num_tlh_opportunities": len(tax.get("tax_loss_harvesting", [])),
                "estimated_tax_liability": report.get("estimated_tax_liability"),
                "potential_tax_savings":   report.get("potential_tax_savings"),
                "inclusion_rate_used":     report.get("inclusion_rate_used"),
                "tax_rate_used":           report.get("tax_rate_used"),
                "sample_recommendation":   (
                    tax.get("recommendations", [{}])[0]
                    if tax.get("recommendations") else {}
                ),
            }

        estate = workflow_results.get("estate_analysis", {})
        if estate:
            report = estate.get("estate_planning_report", {})
            context["agent_outputs"]["EstatePlannerAgent"] = {
                "num_recommendations":    len(estate.get("recommendations", [])),
                "num_product_recs":       len(estate.get("product_recommendations", [])),
                "estimated_probate_fees": report.get("estimated_probate_fees"),
                "total_estate_value":     report.get("total_estate_value"),
                "sample_recommendation":  (
                    estate.get("recommendations", [{}])[0]
                    if estate.get("recommendations") else {}
                ),
            }

        inv = workflow_results.get("investment_analysis", {})
        if inv:
            report = inv.get("investment_analysis_report", {})
            context["agent_outputs"]["InvestmentAnalystAgent"] = {
                "num_security_recs":      len(inv.get("security_recommendations", [])),
                "num_rebalancing_actions": len(inv.get("rebalancing_plan", [])),
                "health_score":           report.get("portfolio_health_score"),
                "concentration_risk":     report.get("concentration_risk_level"),
                "rebalancing_urgency":    report.get("rebalancing_urgency"),
                "sample_recommendation":  (
                    inv.get("security_recommendations", [{}])[0]
                    if inv.get("security_recommendations") else {}
                ),
            }

        return context

    def _extract_output_summary(
        self,
        workflow_results: Dict[str, Any],
        agent_name: str,
    ) -> Dict[str, Any]:
        """Extract a small summary dict for logging to agent_interactions."""
        key_map = {
            "TaxAdvisorAgent":       "tax_analysis",
            "EstatePlannerAgent":    "estate_analysis",
            "InvestmentAnalystAgent": "investment_analysis",
        }
        key = key_map.get(agent_name, "")
        agent_result = workflow_results.get(key, {})

        if agent_name == "TaxAdvisorAgent":
            report = agent_result.get("tax_optimization_report", {})
            return {
                "estimated_tax_liability": report.get("estimated_tax_liability", 0),
                "num_recommendations":     len(agent_result.get("recommendations", [])),
            }
        elif agent_name == "EstatePlannerAgent":
            report = agent_result.get("estate_planning_report", {})
            return {
                "estimated_probate_fees": report.get("estimated_probate_fees", 0),
                "num_recommendations":    len(agent_result.get("recommendations", [])),
            }
        elif agent_name == "InvestmentAnalystAgent":
            report = agent_result.get("investment_analysis_report", {})
            return {
                "health_score":        report.get("portfolio_health_score", 0),
                "num_recommendations": len(agent_result.get("security_recommendations", [])),
            }
        return {}

    @staticmethod
    def _parse_json_response(response: str) -> Dict[str, Any]:
        """Safely extract JSON from an LLM response string."""
        try:
            start = response.find("{")
            end   = response.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"MetaEvolutionAgent: could not parse LLM JSON: {e}")
        return {}

    # ── convenience methods ───────────────────────────────────────────────────

    def get_evolution_history(self, agent_name: str) -> List[Dict[str, Any]]:
        """Return all config versions for an agent."""
        if self.config_store:
            return self.config_store.list_versions(agent_name)
        return []

    def rollback_agent(self, agent_name: str, version: int) -> bool:
        """Roll an agent back to a specific config version."""
        if self.config_store:
            return self.config_store.rollback_to_version(agent_name, version)
        return False
