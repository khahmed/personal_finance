"""
Estate Planner Agent - Estate Planning Specialist.
"""

from typing import Dict, Any, Optional, List
from .base_agent import BaseAgent
from ..tools.analysis_tools import AnalysisTools
from ..schemas.agent_outputs import EstatePlannerOutput, EstateRecommendation, ProductRecommendation
import logging

logger = logging.getLogger(__name__)


class EstatePlannerAgent(BaseAgent):
    """Agent responsible for estate planning and product recommendations."""
    
    def __init__(self, model: str = "deepseek-chat", temperature: float = 0.3):
        """Initialize Estate Planner Agent."""
        self.analysis_tools = AnalysisTools()
        
        super().__init__(
            name="EstatePlannerAgent",
            role="Estate Planning Specialist",
            goal="Optimize estate structure, minimize probate fees, and recommend suitable products",
            backstory="""You are an estate planning expert specializing in Canadian estate law.
            You understand probate fees, beneficiary designations, and tax-efficient estate transfer.
            You recommend products and account structures that minimize estate costs and taxes.
            You consider the client's age, family situation, and legacy goals in your recommendations.""",
            tools=[],
            model=model,
            temperature=temperature,
            verbose=True
        )
    
    def analyze_estate(self, portfolio_summary: Dict[str, Any],
                      holdings: List[Dict[str, Any]],
                      user_context: Dict[str, Any]) -> EstatePlannerOutput:
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
            total_value = portfolio_summary.get('total_value', 0)
            province = user_context.get('province', 'ON')
            age = user_context.get('age', 65)
            
            # Calculate probate fees
            probate_fees = self.analysis_tools.calculate_probate_fees(total_value, province)
            
            # Analyze account structure
            accounts = self._analyze_account_structure(holdings)
            accounts_with_beneficiaries = sum(1 for acc in accounts if acc.get('has_beneficiary', False))
            
            # Generate recommendations
            recommendations = []
            
            # Beneficiary designation recommendations
            if accounts_with_beneficiaries < len(accounts):
                recommendations.append(EstateRecommendation(
                    priority="High",
                    category="Beneficiary Designation",
                    action="Designate beneficiaries on registered accounts",
                    rationale=f"Only {accounts_with_beneficiaries} of {len(accounts)} accounts have beneficiaries. "
                             f"Designating beneficiaries can avoid probate on registered accounts.",
                    estate_benefit=f"Potential probate savings: ${probate_fees * 0.3:,.2f}",
                    implementation_steps=[
                        "Review each registered account (RRSP, TFSA, LIRA)",
                        "Designate primary and contingent beneficiaries",
                        "Update beneficiary designations with institutions"
                    ]
                ))
            
            # Product recommendations based on allocation
            product_recommendations = self._generate_product_recommendations(
                portfolio_summary, user_context
            )
            
            # Account structure optimization
            current_structure = self._get_current_structure(holdings)
            recommended_structure = self._recommend_structure_optimization(
                current_structure, user_context
            )
            
            # Build output
            output_data = {
                "summary": {
                    "total_estate_value": float(total_value),
                    "estimated_probate_fees": float(probate_fees),
                    "estate_tax_estimate": 0.0,  # Canada doesn't have estate tax
                    "accounts_with_beneficiaries": accounts_with_beneficiaries,
                    "accounts_without_beneficiaries": len(accounts) - accounts_with_beneficiaries
                },
                "recommendations": [r.dict() for r in recommendations],
                "product_recommendations": [p.dict() for p in product_recommendations],
                "account_structure_optimization": {
                    "current_structure": current_structure,
                    "recommended_structure": recommended_structure,
                    "rebalancing_steps": []
                }
            }
            
            # Enhance with LLM if available
            if self.use_llm_analysis():
                logger.info(f"{self.name}: Enhancing analysis with LLM")
                output_data = self.enhance_with_llm(output_data, "estate")
            
            return EstatePlannerOutput(
                estate_planning_report=output_data.get("summary", {}),
                recommendations=recommendations,
                product_recommendations=product_recommendations,
                account_structure_optimization=output_data.get("account_structure_optimization", {}),
                llm_insights=output_data.get("llm_insights")
            )
        except Exception as e:
            logger.error(f"Error in estate analysis: {e}")
            return EstatePlannerOutput()
    
    def _analyze_account_structure(self, holdings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze account structure from holdings."""
        accounts = {}
        for holding in holdings:
            account_key = f"{holding.get('institution_name', '')}_{holding.get('account_number', '')}"
            if account_key not in accounts:
                accounts[account_key] = {
                    'account_number': holding.get('account_number', ''),
                    'account_type': holding.get('account_type', ''),
                    'institution_name': holding.get('institution_name', ''),
                    'has_beneficiary': False,  # Would need to check database
                    'value': 0
                }
            accounts[account_key]['value'] += float(holding.get('market_value', 0))
        return list(accounts.values())
    
    def _generate_product_recommendations(self, portfolio_summary: Dict[str, Any],
                                          user_context: Dict[str, Any]) -> List[ProductRecommendation]:
        """Generate product recommendations based on portfolio and user context."""
        recommendations = []
        
        # Get current allocation
        by_category = portfolio_summary.get('by_asset_category', {})
        
        # Recommend based on gaps
        if by_category.get('Equity', 0) < 50:
            recommendations.append(ProductRecommendation(
                product_type="Equity ETF",
                allocation_percentage=20.0,
                account_type="TFSA",
                rationale="Increase equity exposure for long-term growth",
                risk_level="Medium-High",
                tax_treatment="Tax-free growth in TFSA"
            ))
        
        if by_category.get('Fixed Income', 0) < 20:
            recommendations.append(ProductRecommendation(
                product_type="Bond ETF",
                allocation_percentage=15.0,
                account_type="RRSP",
                rationale="Add fixed income for diversification and income",
                risk_level="Low",
                tax_treatment="Tax-deferred growth in RRSP"
            ))
        
        return recommendations
    
    def _get_current_structure(self, holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get current account structure."""
        structure = {}
        for holding in holdings:
            account_type = holding.get('account_type', 'Unknown')
            if account_type not in structure:
                structure[account_type] = 0
            structure[account_type] += float(holding.get('market_value', 0))
        return structure
    
    def _recommend_structure_optimization(self, current_structure: Dict[str, Any],
                                         user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend optimized account structure."""
        # Simplified recommendation - maintain current structure but optimize
        return current_structure

