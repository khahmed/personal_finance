"""
Investment Analyst Agent - Securities Research and Portfolio Optimization Specialist.
"""

from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent
from ..schemas.agent_outputs import InvestmentAnalystOutput, SecurityRecommendation, RebalancingAction
import logging

logger = logging.getLogger(__name__)

_DEFAULT_RULES: Dict[str, Any] = {
    "overweight_threshold_pct":          10.0,
    "underweight_threshold_pct":         1.0,
    "underweight_min_value":             1000.0,
    "target_allocation_pct":             8.0,
    "health_score_base":                 7.0,
    "health_score_many_holdings_bonus":  1.0,
    "health_score_few_holdings_penalty": 1.0,
    "health_score_high_conc_penalty":    1.5,
    "health_score_low_conc_bonus":       0.5,
    "many_holdings_threshold":           20,
    "few_holdings_threshold":            5,
    "high_concentration_threshold":      20.0,
    "low_concentration_threshold":       10.0,
    "max_rebalancing_actions":           5,
    "high_risk_overweight_count":        3,
    "high_urgency_overweight_count":     2,
}


class InvestmentAnalystAgent(BaseAgent):
    """Agent responsible for investment analysis and recommendations."""

    def __init__(self, model: str = "deepseek-chat", temperature: float = 0.3):
        super().__init__(
            name="InvestmentAnalystAgent",
            role="Securities Research and Portfolio Optimization Specialist",
            goal="Analyze securities, identify opportunities, and provide buy/sell recommendations",
            backstory=(
                "You are an investment analyst with expertise in security analysis and portfolio optimization. "
                "You analyze individual securities, assess portfolio concentration, and provide actionable recommendations. "
                "You consider risk-adjusted returns, diversification, and market conditions in your analysis. "
                "You always provide clear rationale for your recommendations with confidence levels."
            ),
            tools=[],
            model=model,
            temperature=temperature,
            verbose=True,
        )

        self.business_rules = {**_DEFAULT_RULES, **self.business_rules}

    def _rule(self, key: str) -> Any:
        return self.business_rules.get(key, _DEFAULT_RULES.get(key))

    def analyze_investments(
        self,
        holdings: List[Dict[str, Any]],
        portfolio_summary: Dict[str, Any],
        user_context: Dict[str, Any],
    ) -> InvestmentAnalystOutput:
        """
        Analyze investments and provide recommendations.

        Args:
            holdings: List of holding dictionaries
            portfolio_summary: Portfolio summary
            user_context: User context including risk profile

        Returns:
            InvestmentAnalystOutput with recommendations
        """
        try:
            total_value = portfolio_summary.get("total_value", 0)
            if total_value == 0:
                total_value = sum(
                    float(h.get("market_value") or 0) for h in holdings
                )

            overweight_threshold  = float(self._rule("overweight_threshold_pct"))
            underweight_threshold = float(self._rule("underweight_threshold_pct"))
            underweight_min_value = float(self._rule("underweight_min_value"))
            target_allocation     = float(self._rule("target_allocation_pct"))

            security_recommendations: List[SecurityRecommendation] = []
            overweight_positions: List[Dict] = []
            underweight_positions: List[Dict] = []

            for holding in holdings:
                try:
                    market_value = float(holding.get("market_value") or 0)
                except (ValueError, TypeError):
                    market_value = 0.0

                allocation_pct = (market_value / total_value * 100) if total_value > 0 else 0

                if allocation_pct > overweight_threshold:
                    overweight_positions.append({
                        "security":   holding.get("security_name", ""),
                        "allocation": allocation_pct,
                    })
                    security_recommendations.append(
                        SecurityRecommendation(
                            security_name=holding.get("security_name") or "Unknown",
                            symbol=holding.get("symbol") or "",
                            current_allocation_pct=allocation_pct,
                            recommendation="Reduce",
                            action="Reduce position size",
                            target_allocation_pct=target_allocation,
                            rationale=(
                                f"Position represents {allocation_pct:.1f}% of portfolio, "
                                f"exceeding {overweight_threshold:.0f}% concentration limit"
                            ),
                            risk_factors=["Concentration risk"],
                            confidence_level="High",
                            timeframe="3-6 months",
                        )
                    )
                elif allocation_pct < underweight_threshold and market_value > underweight_min_value:
                    underweight_positions.append({
                        "security":   holding.get("security_name", ""),
                        "allocation": allocation_pct,
                    })

            health_score    = self._calculate_health_score(holdings, portfolio_summary)
            rebalancing_plan = self._generate_rebalancing_plan(
                holdings, overweight_positions, total_value
            )
            sector_analysis = self._analyze_sectors(holdings)

            high_risk_count    = int(self._rule("high_risk_overweight_count"))
            high_urgency_count = int(self._rule("high_urgency_overweight_count"))

            output_data = {
                "summary": {
                    "portfolio_health_score":  health_score,
                    "overweight_positions":    overweight_positions,
                    "underweight_positions":   underweight_positions,
                    "concentration_risk_level": (
                        "High" if len(overweight_positions) > high_risk_count else "Moderate"
                    ),
                    "rebalancing_urgency": (
                        "High" if len(overweight_positions) > high_urgency_count else "Medium"
                    ),
                },
                "security_recommendations": [r.dict() for r in security_recommendations],
                "sector_analysis":          sector_analysis,
                "rebalancing_plan":         [a.dict() for a in rebalancing_plan],
                "market_context": {
                    "market_conditions": "Normal",
                    "relevant_trends":   [],
                    "risk_warnings":     [],
                },
            }

            if self.use_llm_analysis():
                logger.info(f"{self.name}: Enhancing analysis with LLM")
                output_data = self.enhance_with_llm(output_data, "investment")

            return InvestmentAnalystOutput(
                investment_analysis_report=output_data.get("summary", {}),
                security_recommendations=security_recommendations,
                sector_analysis=output_data.get("sector_analysis", {}),
                rebalancing_plan=rebalancing_plan,
                market_context=output_data.get("market_context", {}),
                llm_insights=output_data.get("llm_insights"),
            )
        except Exception as e:
            logger.error(f"Error in investment analysis: {e}")
            return InvestmentAnalystOutput()

    def _calculate_health_score(
        self,
        holdings: List[Dict[str, Any]],
        portfolio_summary: Dict[str, Any],
    ) -> float:
        score = float(self._rule("health_score_base"))

        num_holdings = len(holdings)
        if num_holdings > int(self._rule("many_holdings_threshold")):
            score += float(self._rule("health_score_many_holdings_bonus"))
        elif num_holdings < int(self._rule("few_holdings_threshold")):
            score -= float(self._rule("health_score_few_holdings_penalty"))

        total_value = portfolio_summary.get("total_value", 0)
        if total_value > 0 and holdings:
            max_position = max(
                float(h.get("market_value") or 0) / total_value * 100
                for h in holdings
            )
            if max_position > float(self._rule("high_concentration_threshold")):
                score -= float(self._rule("health_score_high_conc_penalty"))
            elif max_position < float(self._rule("low_concentration_threshold")):
                score += float(self._rule("health_score_low_conc_bonus"))

        return max(0.0, min(10.0, score))

    def _generate_rebalancing_plan(
        self,
        holdings: List[Dict[str, Any]],
        overweight_positions: List[Dict[str, Any]],
        total_value: float,
    ) -> List[RebalancingAction]:
        plan: List[RebalancingAction] = []
        max_actions   = int(self._rule("max_rebalancing_actions"))
        target_pct    = float(self._rule("target_allocation_pct"))

        for pos in overweight_positions[:max_actions]:
            for holding in holdings:
                if holding.get("security_name") == pos["security"]:
                    try:
                        current_value = float(holding.get("market_value") or 0)
                    except (ValueError, TypeError):
                        current_value = 0.0

                    target_value = total_value * (target_pct / 100)
                    reduction    = current_value - target_value

                    if reduction > 0:
                        plan.append(
                            RebalancingAction(
                                security=pos["security"],
                                action="Sell",
                                quantity=None,
                                estimated_value=reduction,
                                reason=(
                                    f"Reduce from {pos['allocation']:.1f}% "
                                    f"to {target_pct:.0f}% target allocation"
                                ),
                            )
                        )
                    break

        return plan

    def _analyze_sectors(self, holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "current_exposure":   {},
            "benchmark_exposure": {},
            "recommendations":    [],
        }
