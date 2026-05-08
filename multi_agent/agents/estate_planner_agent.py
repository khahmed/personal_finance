"""
Estate Planner Agent - Estate Planning Specialist.
"""

from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent
from ..tools.analysis_tools import AnalysisTools
from ..schemas.agent_outputs import EstatePlannerOutput, EstateRecommendation, ProductRecommendation
import logging

logger = logging.getLogger(__name__)

_DEFAULT_RULES: Dict[str, Any] = {
    "equity_threshold_pct":        50,
    "fixed_income_threshold_pct":  20,
    "equity_etf_allocation_pct":   20.0,
    "bond_etf_allocation_pct":     15.0,
    "default_province":            "ON",
}


class EstatePlannerAgent(BaseAgent):
    """Agent responsible for estate planning and product recommendations."""

    def __init__(self, model: str = "deepseek-chat", temperature: float = 0.3):
        self.analysis_tools = AnalysisTools()

        super().__init__(
            name="EstatePlannerAgent",
            role="Estate Planning Specialist",
            goal="Optimize estate structure, minimize probate fees, and recommend suitable products",
            backstory=(
                "You are an estate planning expert specializing in Canadian estate law. "
                "You understand probate fees, beneficiary designations, and tax-efficient estate transfer. "
                "You recommend products and account structures that minimize estate costs and taxes. "
                "You consider the client's age, family situation, and legacy goals in your recommendations."
            ),
            tools=[],
            model=model,
            temperature=temperature,
            verbose=True,
        )

        self.business_rules = {**_DEFAULT_RULES, **self.business_rules}

    def _rule(self, key: str) -> Any:
        return self.business_rules.get(key, _DEFAULT_RULES.get(key))

    def analyze_estate(
        self,
        portfolio_summary: Dict[str, Any],
        holdings: List[Dict[str, Any]],
        user_context: Dict[str, Any],
    ) -> EstatePlannerOutput:
        """
        Analyze portfolio for estate planning opportunities.

        Args:
            portfolio_summary: Portfolio summary dictionary
            holdings: List of holding dictionaries
            user_context: User context including age, province, etc.

        Returns:
            EstatePlannerOutput with recommendations
        """
        try:
            total_value = portfolio_summary.get("total_value", 0)
            province = user_context.get("province") or self._rule("default_province")

            probate_fees = self.analysis_tools.calculate_probate_fees(total_value, province)

            accounts = self._analyze_account_structure(holdings)
            accounts_with_beneficiaries = sum(
                1 for acc in accounts if acc.get("has_beneficiary", False)
            )

            recommendations: List[EstateRecommendation] = []
            if accounts_with_beneficiaries < len(accounts):
                recommendations.append(
                    EstateRecommendation(
                        priority="High",
                        category="Beneficiary Designation",
                        action="Designate beneficiaries on registered accounts",
                        rationale=(
                            f"Only {accounts_with_beneficiaries} of {len(accounts)} accounts have "
                            "beneficiaries. Designating beneficiaries can avoid probate on registered accounts."
                        ),
                        estate_benefit=f"Potential probate savings: ${probate_fees * 0.3:,.2f}",
                        implementation_steps=[
                            "Review each registered account (RRSP, TFSA, LIRA)",
                            "Designate primary and contingent beneficiaries",
                            "Update beneficiary designations with institutions",
                        ],
                    )
                )

            product_recommendations = self._generate_product_recommendations(
                portfolio_summary, user_context
            )
            current_structure = self._get_current_structure(holdings)
            recommended_structure = self._recommend_structure_optimization(
                current_structure, user_context
            )

            output_data = {
                "summary": {
                    "total_estate_value":             float(total_value),
                    "estimated_probate_fees":         float(probate_fees),
                    "estate_tax_estimate":            0.0,
                    "accounts_with_beneficiaries":    accounts_with_beneficiaries,
                    "accounts_without_beneficiaries": len(accounts) - accounts_with_beneficiaries,
                },
                "recommendations": [r.dict() for r in recommendations],
                "product_recommendations": [p.dict() for p in product_recommendations],
                "account_structure_optimization": {
                    "current_structure":     current_structure,
                    "recommended_structure": recommended_structure,
                    "rebalancing_steps":     [],
                },
            }

            if self.use_llm_analysis():
                logger.info(f"{self.name}: Enhancing analysis with LLM")
                output_data = self.enhance_with_llm(output_data, "estate")

            return EstatePlannerOutput(
                estate_planning_report=output_data.get("summary", {}),
                recommendations=recommendations,
                product_recommendations=product_recommendations,
                account_structure_optimization=output_data.get("account_structure_optimization", {}),
                llm_insights=output_data.get("llm_insights"),
            )
        except Exception as e:
            logger.error(f"Error in estate analysis: {e}")
            return EstatePlannerOutput()

    def _analyze_account_structure(self, holdings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        accounts: Dict[str, Dict] = {}
        for holding in holdings:
            key = f"{holding.get('institution_name', '')}_{holding.get('account_number', '')}"
            if key not in accounts:
                accounts[key] = {
                    "account_number":   holding.get("account_number", ""),
                    "account_type":     holding.get("account_type", ""),
                    "institution_name": holding.get("institution_name", ""),
                    "has_beneficiary":  False,
                    "value":            0,
                }
            accounts[key]["value"] += float(holding.get("market_value") or 0)
        return list(accounts.values())

    def _generate_product_recommendations(
        self,
        portfolio_summary: Dict[str, Any],
        user_context: Dict[str, Any],
    ) -> List[ProductRecommendation]:
        recommendations: List[ProductRecommendation] = []
        by_category = portfolio_summary.get("by_asset_category", {})

        equity_threshold  = float(self._rule("equity_threshold_pct"))
        fi_threshold      = float(self._rule("fixed_income_threshold_pct"))
        equity_alloc      = float(self._rule("equity_etf_allocation_pct"))
        bond_alloc        = float(self._rule("bond_etf_allocation_pct"))

        if by_category.get("Equity", 0) < equity_threshold:
            recommendations.append(
                ProductRecommendation(
                    product_type="Equity ETF",
                    allocation_percentage=equity_alloc,
                    account_type="TFSA",
                    rationale="Increase equity exposure for long-term growth",
                    risk_level="Medium-High",
                    tax_treatment="Tax-free growth in TFSA",
                )
            )

        if by_category.get("Fixed Income", 0) < fi_threshold:
            recommendations.append(
                ProductRecommendation(
                    product_type="Bond ETF",
                    allocation_percentage=bond_alloc,
                    account_type="RRSP",
                    rationale="Add fixed income for diversification and income",
                    risk_level="Low",
                    tax_treatment="Tax-deferred growth in RRSP",
                )
            )

        return recommendations

    def _get_current_structure(self, holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
        structure: Dict[str, float] = {}
        for holding in holdings:
            account_type = holding.get("account_type", "Unknown")
            structure[account_type] = structure.get(account_type, 0) + float(
                holding.get("market_value") or 0
            )
        return structure

    def _recommend_structure_optimization(
        self,
        current_structure: Dict[str, Any],
        user_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        return current_structure
