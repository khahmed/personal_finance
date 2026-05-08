"""
Tax Advisor Agent - Tax Optimization Specialist.
"""

from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent
from ..tools.analysis_tools import AnalysisTools
from ..schemas.agent_outputs import TaxAdvisorOutput, TaxRecommendation, TaxLossHarvesting
import logging

logger = logging.getLogger(__name__)

# Baseline rules used when the DB has no active config for this agent.
_DEFAULT_RULES: Dict[str, Any] = {
    "inclusion_rate": 0.5,
    "default_tax_rate": 0.30,
    "min_loss_threshold": 100.0,
    "max_tlh_recommendations": 10,
    "max_priority_recommendations": 5,
}


class TaxAdvisorAgent(BaseAgent):
    """Agent responsible for tax optimization and planning."""

    def __init__(self, model: str = "deepseek-chat", temperature: float = 0.2):
        self.analysis_tools = AnalysisTools()

        super().__init__(
            name="TaxAdvisorAgent",
            role="Tax Optimization Specialist",
            goal="Analyze portfolio for tax-efficient strategies and minimize tax liability",
            backstory=(
                "You are a Canadian tax expert specializing in investment tax optimization. "
                "You have deep knowledge of RRSP, TFSA, LIRA, and non-registered account tax treatment. "
                "You understand capital gains taxation, tax-loss harvesting, and withdrawal strategies. "
                "You always consider the client's tax bracket and provincial tax rates in your recommendations."
            ),
            tools=[],
            model=model,
            temperature=temperature,
            verbose=True,
        )

        # Merge DB rules over defaults so callers never get a KeyError
        merged = {**_DEFAULT_RULES, **self.business_rules}
        self.business_rules = merged

    def _rule(self, key: str) -> Any:
        """Convenience accessor with fallback to _DEFAULT_RULES."""
        return self.business_rules.get(key, _DEFAULT_RULES.get(key))

    def analyze_portfolio(
        self,
        holdings: List[Dict[str, Any]],
        user_context: Dict[str, Any],
    ) -> TaxAdvisorOutput:
        """
        Analyze portfolio for tax optimization opportunities.

        Args:
            holdings: List of holding dictionaries
            user_context: User context including tax bracket, province, etc.

        Returns:
            TaxAdvisorOutput with recommendations
        """
        try:
            total_gains = 0.0
            total_losses = 0.0

            for holding in holdings:
                try:
                    book_value = float(holding.get("book_value") or 0)
                except (ValueError, TypeError):
                    book_value = 0.0
                try:
                    market_value = float(holding.get("market_value") or 0)
                except (ValueError, TypeError):
                    market_value = 0.0

                gain_loss = market_value - book_value
                if gain_loss > 0:
                    total_gains += gain_loss
                else:
                    total_losses += abs(gain_loss)

            # Tax rates – prefer user_context over business_rules over default
            tax_rate = float(
                user_context.get("tax_rate") or self._rule("default_tax_rate")
            )
            inclusion_rate = float(self._rule("inclusion_rate"))

            taxable_gains = total_gains * inclusion_rate
            estimated_tax = taxable_gains * tax_rate

            # Tax-loss harvesting
            min_loss = float(self._rule("min_loss_threshold"))
            loss_opportunities = self.analysis_tools.identify_tax_loss_harvesting(
                holdings, min_loss=min_loss, inclusion_rate=inclusion_rate, tax_rate=tax_rate
            )
            potential_savings = sum(opp["tax_benefit"] for opp in loss_opportunities)

            # Recommendations
            recommendations: List[TaxRecommendation] = []
            max_prio = int(self._rule("max_priority_recommendations"))
            for opp in loss_opportunities[:max_prio]:
                recommendations.append(
                    TaxRecommendation(
                        priority="High" if opp["tax_benefit"] > 500 else "Medium",
                        action=f"Sell {opp['security']} to realize tax loss",
                        security=opp["security"],
                        account=opp["account"],
                        rationale=(
                            f"Unrealized loss of ${opp['unrealized_loss']:,.2f} can provide "
                            f"${opp['tax_benefit']:,.2f} in tax savings"
                        ),
                        tax_impact=-opp["tax_benefit"],
                        timing="Before year-end",
                    )
                )

            withdrawal_strategy = self._recommend_withdrawal_strategy(holdings, user_context)

            max_tlh = int(self._rule("max_tlh_recommendations"))
            output_data = {
                "summary": {
                    "total_unrealized_gains":  float(total_gains),
                    "total_unrealized_losses": float(total_losses),
                    "estimated_tax_liability": float(estimated_tax),
                    "potential_tax_savings":   float(potential_savings),
                    "inclusion_rate_used":     inclusion_rate,
                    "tax_rate_used":           tax_rate,
                },
                "recommendations": [r.dict() for r in recommendations],
                "tax_loss_harvesting": [
                    {
                        "security":                 opp["security"],
                        "unrealized_loss":          opp["unrealized_loss"],
                        "tax_benefit":              opp["tax_benefit"],
                        "superficial_loss_warning": False,
                    }
                    for opp in loss_opportunities[:max_tlh]
                ],
                "withdrawal_strategy": withdrawal_strategy,
            }

            if self.use_llm_analysis():
                logger.info(f"{self.name}: Enhancing analysis with LLM")
                output_data = self.enhance_with_llm(output_data, "tax")

            return TaxAdvisorOutput(
                tax_optimization_report=output_data.get("summary", {}),
                recommendations=recommendations,
                tax_loss_harvesting=[
                    TaxLossHarvesting(**item)
                    for item in output_data.get("tax_loss_harvesting", [])
                ],
                withdrawal_strategy=output_data.get("withdrawal_strategy", {}),
                llm_insights=output_data.get("llm_insights"),
            )
        except Exception as e:
            logger.error(f"Error in tax analysis: {e}")
            return TaxAdvisorOutput()

    def _recommend_withdrawal_strategy(
        self,
        holdings: List[Dict[str, Any]],
        user_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        accounts: Dict[str, Dict] = {}
        for holding in holdings:
            account_type = holding.get("account_type", "Unknown")
            account_key = f"{holding.get('institution_name', '')}_{holding.get('account_number', '')}"
            if account_key not in accounts:
                accounts[account_key] = {
                    "account_number":   holding.get("account_number", ""),
                    "account_type":     account_type,
                    "institution_name": holding.get("institution_name", ""),
                    "balance":          0,
                }
            accounts[account_key]["balance"] += float(holding.get("market_value") or 0)

        account_list = list(accounts.values())
        recommendations = self.analysis_tools.recommend_withdrawal_order(account_list)

        return {
            "account_order": recommendations,
            "estimated_tax_by_account": {
                acc["account"]: self._estimate_account_tax(acc, user_context)
                for acc in recommendations
            },
        }

    def _estimate_account_tax(
        self, account: Dict[str, Any], user_context: Dict[str, Any]
    ) -> float:
        account_type = account.get("account_type", "")
        tax_rate = float(
            user_context.get("tax_rate") or self._rule("default_tax_rate")
        )
        if account_type == "TFSA":
            return 0.0
        elif account_type in ("RRSP", "RRIF", "LIRA"):
            return account.get("balance", 0) * tax_rate
        return 0.0
