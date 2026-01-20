"""
Tax Advisor Agent - Tax Optimization Specialist.
"""

from typing import Dict, Any, Optional, List
from .base_agent import BaseAgent
from ..tools.analysis_tools import AnalysisTools
from ..schemas.agent_outputs import TaxAdvisorOutput, TaxRecommendation, TaxLossHarvesting
import logging

logger = logging.getLogger(__name__)


class TaxAdvisorAgent(BaseAgent):
    """Agent responsible for tax optimization and planning."""
    
    def __init__(self, model: str = "deepseek-chat", temperature: float = 0.2):
        """Initialize Tax Advisor Agent."""
        self.analysis_tools = AnalysisTools()
        
        super().__init__(
            name="TaxAdvisorAgent",
            role="Tax Optimization Specialist",
            goal="Analyze portfolio for tax-efficient strategies and minimize tax liability",
            backstory="""You are a Canadian tax expert specializing in investment tax optimization.
            You have deep knowledge of RRSP, TFSA, LIRA, and non-registered account tax treatment.
            You understand capital gains taxation, tax-loss harvesting, and withdrawal strategies.
            You always consider the client's tax bracket and provincial tax rates in your recommendations.""",
            tools=[],
            model=model,
            temperature=temperature,
            verbose=True
        )
    
    def analyze_portfolio(self, holdings: List[Dict[str, Any]],
                         user_context: Dict[str, Any]) -> TaxAdvisorOutput:
        """
        Analyze portfolio for tax optimization opportunities.
        
        Args:
            holdings: List of holding dictionaries
            user_context: User context including tax bracket, province, etc.
            
        Returns:
            TaxAdvisorOutput with recommendations
        """
        try:
            # Calculate unrealized gains/losses
            total_gains = 0.0
            total_losses = 0.0
            
            for holding in holdings:
                # Handle None values safely
                book_value_raw = holding.get('book_value') or holding.get('book_value', 0)
                market_value_raw = holding.get('market_value') or holding.get('market_value', 0)
                
                try:
                    book_value = float(book_value_raw) if book_value_raw is not None else 0.0
                except (ValueError, TypeError):
                    book_value = 0.0
                
                try:
                    market_value = float(market_value_raw) if market_value_raw is not None else 0.0
                except (ValueError, TypeError):
                    market_value = 0.0
                
                gain_loss = market_value - book_value
                
                if gain_loss > 0:
                    total_gains += gain_loss
                else:
                    total_losses += abs(gain_loss)
            
            # Get tax bracket (default to 30% if not provided)
            tax_rate = float(user_context.get('tax_rate', 0.30))
            province = user_context.get('province', 'ON')
            
            # Estimate tax liability
            taxable_gains = total_gains * 0.5  # 50% inclusion rate
            estimated_tax = taxable_gains * tax_rate
            
            # Identify tax loss harvesting opportunities
            loss_opportunities = self.analysis_tools.identify_tax_loss_harvesting(holdings)
            
            # Calculate potential tax savings
            potential_savings = sum(opp['tax_benefit'] for opp in loss_opportunities)
            
            # Generate recommendations
            recommendations = []
            
            # Tax loss harvesting recommendations
            for opp in loss_opportunities[:5]:  # Top 5 opportunities
                recommendations.append(TaxRecommendation(
                    priority="High" if opp['tax_benefit'] > 500 else "Medium",
                    action=f"Sell {opp['security']} to realize tax loss",
                    security=opp['security'],
                    account=opp['account'],
                    rationale=f"Unrealized loss of ${opp['unrealized_loss']:,.2f} can provide "
                             f"${opp['tax_benefit']:,.2f} in tax savings",
                    tax_impact=-opp['tax_benefit'],
                    timing="Before year-end"
                ))
            
            # Withdrawal strategy
            withdrawal_strategy = self._recommend_withdrawal_strategy(holdings, user_context)
            
            # Build output
            output_data = {
                "summary": {
                    "total_unrealized_gains": float(total_gains),
                    "total_unrealized_losses": float(total_losses),
                    "estimated_tax_liability": float(estimated_tax),
                    "potential_tax_savings": float(potential_savings)
                },
                "recommendations": [r.dict() for r in recommendations],
                "tax_loss_harvesting": [
                    {
                        "security": opp['security'],
                        "unrealized_loss": opp['unrealized_loss'],
                        "tax_benefit": opp['tax_benefit'],
                        "superficial_loss_warning": False
                    }
                    for opp in loss_opportunities[:10]
                ],
                "withdrawal_strategy": withdrawal_strategy
            }
            
            # Enhance with LLM if available
            if self.use_llm_analysis():
                logger.info(f"{self.name}: Enhancing analysis with LLM")
                output_data = self.enhance_with_llm(output_data, "tax")
            
            output = TaxAdvisorOutput(
                tax_optimization_report=output_data.get("summary", {}),
                recommendations=recommendations,
                tax_loss_harvesting=[
                    TaxLossHarvesting(**item) for item in output_data.get("tax_loss_harvesting", [])
                ],
                withdrawal_strategy=output_data.get("withdrawal_strategy", {}),
                llm_insights=output_data.get("llm_insights")
            )
            
            return output
        except Exception as e:
            logger.error(f"Error in tax analysis: {e}")
            return TaxAdvisorOutput()
    
    def _recommend_withdrawal_strategy(self, holdings: List[Dict[str, Any]],
                                      user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend optimal withdrawal order."""
        # Group holdings by account type
        accounts = {}
        for holding in holdings:
            account_type = holding.get('account_type', 'Unknown')
            account_key = f"{holding.get('institution_name', '')}_{holding.get('account_number', '')}"
            
            if account_key not in accounts:
                accounts[account_key] = {
                    'account_number': holding.get('account_number', ''),
                    'account_type': account_type,
                    'institution_name': holding.get('institution_name', ''),
                    'balance': 0
                }
            
            accounts[account_key]['balance'] += float(holding.get('market_value', 0))
        
        account_list = list(accounts.values())
        recommendations = self.analysis_tools.recommend_withdrawal_order(account_list)
        
        return {
            "account_order": recommendations,
            "estimated_tax_by_account": {
                acc['account']: self._estimate_account_tax(acc, user_context)
                for acc in recommendations
            }
        }
    
    def _estimate_account_tax(self, account: Dict[str, Any],
                              user_context: Dict[str, Any]) -> float:
        """Estimate tax for account withdrawal."""
        account_type = account.get('account_type', '')
        tax_rate = float(user_context.get('tax_rate', 0.30))
        
        if account_type == 'TFSA':
            return 0.0
        elif account_type in ['RRSP', 'RRIF', 'LIRA']:
            # Fully taxable as income
            return account.get('balance', 0) * tax_rate
        else:
            # Non-registered - would need to calculate capital gains
            return 0.0  # Simplified

