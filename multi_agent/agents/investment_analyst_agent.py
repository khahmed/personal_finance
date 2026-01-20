"""
Investment Analyst Agent - Securities Research and Portfolio Optimization Specialist.
"""

from typing import Dict, Any, Optional, List
from .base_agent import BaseAgent
from ..schemas.agent_outputs import InvestmentAnalystOutput, SecurityRecommendation, RebalancingAction
import logging

logger = logging.getLogger(__name__)


class InvestmentAnalystAgent(BaseAgent):
    """Agent responsible for investment analysis and recommendations."""
    
    def __init__(self, model: str = "deepseek-chat", temperature: float = 0.3):
        """Initialize Investment Analyst Agent."""
        super().__init__(
            name="InvestmentAnalystAgent",
            role="Securities Research and Portfolio Optimization Specialist",
            goal="Analyze securities, identify opportunities, and provide buy/sell recommendations",
            backstory="""You are an investment analyst with expertise in security analysis and portfolio optimization.
            You analyze individual securities, assess portfolio concentration, and provide actionable recommendations.
            You consider risk-adjusted returns, diversification, and market conditions in your analysis.
            You always provide clear rationale for your recommendations with confidence levels.""",
            tools=[],
            model=model,
            temperature=temperature,
            verbose=True
        )
    
    def analyze_investments(self, holdings: List[Dict[str, Any]],
                           portfolio_summary: Dict[str, Any],
                           user_context: Dict[str, Any]) -> InvestmentAnalystOutput:
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
            # Calculate total portfolio value
            total_value = portfolio_summary.get('total_value', 0)
            if total_value == 0:
                total_value = sum(
                    float(h.get('market_value') or 0) if h.get('market_value') is not None else 0.0
                    for h in holdings
                )
            
            # Identify overweight/underweight positions
            security_recommendations = []
            overweight_positions = []
            underweight_positions = []
            
            # Analyze each holding
            for holding in holdings:
                # Handle None values safely
                market_value_raw = holding.get('market_value')
                try:
                    market_value = float(market_value_raw) if market_value_raw is not None else 0.0
                except (ValueError, TypeError):
                    market_value = 0.0
                
                allocation_pct = (market_value / total_value * 100) if total_value > 0 else 0
                
                # Simple rule: if position > 10% of portfolio, consider overweight
                if allocation_pct > 10:
                    overweight_positions.append({
                        'security': holding.get('security_name', ''),
                        'allocation': allocation_pct
                    })
                    security_recommendations.append(SecurityRecommendation(
                        security_name=holding.get('security_name') or 'Unknown',
                        symbol=holding.get('symbol') or '',  # Ensure it's a string, not None
                        current_allocation_pct=allocation_pct,
                        recommendation="Reduce",
                        action="Reduce position size",
                        target_allocation_pct=8.0,
                        rationale=f"Position represents {allocation_pct:.1f}% of portfolio, "
                                f"exceeding recommended 10% concentration limit",
                        risk_factors=["Concentration risk"],
                        confidence_level="High",
                        timeframe="3-6 months"
                    ))
                elif allocation_pct < 1 and market_value > 1000:
                    # Small positions that could be consolidated
                    underweight_positions.append({
                        'security': holding.get('security_name', ''),
                        'allocation': allocation_pct
                    })
            
            # Calculate portfolio health score
            health_score = self._calculate_health_score(holdings, portfolio_summary)
            
            # Generate rebalancing plan
            rebalancing_plan = self._generate_rebalancing_plan(
                holdings, overweight_positions, total_value
            )
            
            # Sector analysis
            sector_analysis = self._analyze_sectors(holdings)
            
            # Build output
            output_data = {
                "summary": {
                    "portfolio_health_score": health_score,
                    "overweight_positions": overweight_positions,
                    "underweight_positions": underweight_positions,
                    "concentration_risk_level": "High" if len(overweight_positions) > 3 else "Moderate",
                    "rebalancing_urgency": "High" if len(overweight_positions) > 2 else "Medium"
                },
                "security_recommendations": [r.dict() for r in security_recommendations],
                "sector_analysis": sector_analysis,
                "rebalancing_plan": [a.dict() for a in rebalancing_plan],
                "market_context": {
                    "market_conditions": "Normal",
                    "relevant_trends": [],
                    "risk_warnings": []
                }
            }
            
            # Enhance with LLM if available
            if self.use_llm_analysis():
                logger.info(f"{self.name}: Enhancing analysis with LLM")
                output_data = self.enhance_with_llm(output_data, "investment")
            
            return InvestmentAnalystOutput(
                investment_analysis_report=output_data.get("summary", {}),
                security_recommendations=security_recommendations,
                sector_analysis=output_data.get("sector_analysis", {}),
                rebalancing_plan=rebalancing_plan,
                market_context=output_data.get("market_context", {}),
                llm_insights=output_data.get("llm_insights")
            )
        except Exception as e:
            logger.error(f"Error in investment analysis: {e}")
            return InvestmentAnalystOutput()
    
    def _calculate_health_score(self, holdings: List[Dict[str, Any]],
                                portfolio_summary: Dict[str, Any]) -> float:
        """Calculate portfolio health score (0-10)."""
        score = 7.0  # Base score
        
        # Adjust based on diversification
        num_holdings = len(holdings)
        if num_holdings > 20:
            score += 1.0
        elif num_holdings < 5:
            score -= 1.0
        
        # Adjust based on concentration
        total_value = portfolio_summary.get('total_value', 0)
        if total_value > 0 and holdings:
            max_position = max(
                (float(h.get('market_value') or 0) / total_value * 100)
                if h.get('market_value') is not None else 0.0
                for h in holdings
            )
            if max_position > 20:
                score -= 1.5
            elif max_position < 10:
                score += 0.5
        
        return max(0.0, min(10.0, score))
    
    def _generate_rebalancing_plan(self, holdings: List[Dict[str, Any]],
                                   overweight_positions: List[Dict[str, Any]],
                                   total_value: float) -> List[RebalancingAction]:
        """Generate rebalancing plan."""
        plan = []
        
        for pos in overweight_positions[:5]:  # Top 5 overweight positions
            # Find the holding
            for holding in holdings:
                if holding.get('security_name') == pos['security']:
                    market_value_raw = holding.get('market_value')
                    try:
                        current_value = float(market_value_raw) if market_value_raw is not None else 0.0
                    except (ValueError, TypeError):
                        current_value = 0.0
                    
                    target_value = total_value * 0.08  # Target 8%
                    reduction = current_value - target_value
                    
                    if reduction > 0:
                        plan.append(RebalancingAction(
                            security=pos['security'],
                            action="Sell",
                            quantity=None,  # Would need to calculate from price
                            estimated_value=reduction,
                            reason=f"Reduce from {pos['allocation']:.1f}% to 8% target allocation"
                        ))
                    break
        
        return plan
    
    def _analyze_sectors(self, holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sector exposure."""
        # Simplified - would need sector classification
        return {
            "current_exposure": {},
            "benchmark_exposure": {},
            "recommendations": []
        }

