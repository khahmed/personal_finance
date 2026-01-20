"""
Output schemas for each agent type.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import date


class PortfolioDataOutput(BaseModel):
    """Output schema for Portfolio Data Agent."""
    
    portfolio_summary: Dict[str, Any] = Field(default_factory=dict)
    holdings: List[Dict[str, Any]] = Field(default_factory=list)
    allocation: Dict[str, Any] = Field(default_factory=dict)
    concentration_metrics: Dict[str, Any] = Field(default_factory=dict)
    diversification_metrics: Dict[str, Any] = Field(default_factory=dict)


class TaxRecommendation(BaseModel):
    """Individual tax recommendation."""
    priority: str
    action: str
    security: Optional[str] = None
    account: Optional[str] = None
    rationale: str
    tax_impact: float
    timing: str


class TaxLossHarvesting(BaseModel):
    """Tax loss harvesting opportunity."""
    security: str
    unrealized_loss: float
    tax_benefit: float
    superficial_loss_warning: bool = False


class TaxAdvisorOutput(BaseModel):
    """Output schema for Tax Advisor Agent."""
    
    tax_optimization_report: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[TaxRecommendation] = Field(default_factory=list)
    tax_loss_harvesting: List[TaxLossHarvesting] = Field(default_factory=list)
    withdrawal_strategy: Dict[str, Any] = Field(default_factory=dict)
    llm_insights: Optional[Dict[str, Any]] = Field(default=None, exclude_unset=True)  # Optional LLM enhancements


class EstateRecommendation(BaseModel):
    """Estate planning recommendation."""
    priority: str
    category: str
    action: str
    rationale: str
    estate_benefit: str
    implementation_steps: List[str] = Field(default_factory=list)


class ProductRecommendation(BaseModel):
    """Product recommendation for estate planning."""
    product_type: str
    allocation_percentage: float
    account_type: str
    rationale: str
    risk_level: str
    tax_treatment: str


class EstatePlannerOutput(BaseModel):
    """Output schema for Estate Planner Agent."""
    
    estate_planning_report: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[EstateRecommendation] = Field(default_factory=list)
    product_recommendations: List[ProductRecommendation] = Field(default_factory=list)
    account_structure_optimization: Dict[str, Any] = Field(default_factory=dict)
    llm_insights: Optional[Dict[str, Any]] = Field(default=None, exclude_unset=True)  # Optional LLM enhancements


class SecurityRecommendation(BaseModel):
    """Investment recommendation for a security."""
    security_name: str
    symbol: str
    current_allocation_pct: float
    recommendation: str  # Strong Buy, Buy, Hold, Reduce, Sell
    action: str
    target_allocation_pct: Optional[float] = None
    rationale: str
    risk_factors: List[str] = Field(default_factory=list)
    confidence_level: str
    timeframe: str


class RebalancingAction(BaseModel):
    """Rebalancing action recommendation."""
    security: str
    action: str  # Buy, Sell, Hold
    quantity: Optional[float] = None
    estimated_value: Optional[float] = None
    reason: str


class InvestmentAnalystOutput(BaseModel):
    """Output schema for Investment Analyst Agent."""
    
    investment_analysis_report: Dict[str, Any] = Field(default_factory=dict)
    security_recommendations: List[SecurityRecommendation] = Field(default_factory=list)
    sector_analysis: Dict[str, Any] = Field(default_factory=dict)
    rebalancing_plan: List[RebalancingAction] = Field(default_factory=list)
    market_context: Dict[str, Any] = Field(default_factory=dict)
    llm_insights: Optional[Dict[str, Any]] = Field(default=None, exclude_unset=True)  # Optional LLM enhancements

