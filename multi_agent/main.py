"""
Main entry point for the multi-agent financial advisory system.
"""

import sys
import os
import logging
from typing import Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_agent.flows.financial_advisory_flow import FinancialAdvisoryFlow

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main function to run the financial advisory system."""
    flow = FinancialAdvisoryFlow()
    
    # Example usage
    user_context = {
        "tax_bracket": "mid",
        "tax_rate": 0.30,
        "province": "ON",
        "age": 55,
        "risk_profile": "moderate"
    }
    
    # Get comprehensive review
    print("Running comprehensive financial review...")
    results = flow.get_comprehensive_review(user_context)
    
    if "error" in results:
        print(f"Error: {results['error']}")
        return
    
    print("\n" + "="*50)
    print("FINANCIAL ADVISORY REPORT")
    print("="*50)
    
    # Print summary
    if "portfolio_data" in results:
        portfolio = results["portfolio_data"]
        summary = portfolio.get("portfolio_summary", {})
        print(f"\nPortfolio Value: ${summary.get('total_value', 0):,.2f}")
        print(f"Number of Accounts: {summary.get('num_accounts', 0)}")
        print(f"Number of Securities: {summary.get('num_securities', 0)}")
    
    if "tax_analysis" in results:
        tax = results["tax_analysis"]
        report = tax.get("tax_optimization_report", {})
        summary = report.get("summary", {})
        print(f"\nTax Analysis:")
        print(f"  Unrealized Gains: ${summary.get('total_unrealized_gains', 0):,.2f}")
        print(f"  Unrealized Losses: ${summary.get('total_unrealized_losses', 0):,.2f}")
        print(f"  Estimated Tax Liability: ${summary.get('estimated_tax_liability', 0):,.2f}")
        print(f"  Potential Tax Savings: ${summary.get('potential_tax_savings', 0):,.2f}")
    
    if "estate_analysis" in results:
        estate = results["estate_analysis"]
        report = estate.get("estate_planning_report", {})
        summary = report.get("summary", {})
        print(f"\nEstate Planning:")
        print(f"  Total Estate Value: ${summary.get('total_estate_value', 0):,.2f}")
        print(f"  Estimated Probate Fees: ${summary.get('estimated_probate_fees', 0):,.2f}")
    
    if "investment_analysis" in results:
        investment = results["investment_analysis"]
        report = investment.get("investment_analysis_report", {})
        summary = report.get("summary", {})
        print(f"\nInvestment Analysis:")
        print(f"  Portfolio Health Score: {summary.get('portfolio_health_score', 0):.1f}/10")
        print(f"  Concentration Risk: {summary.get('concentration_risk_level', 'Unknown')}")
        print(f"  Rebalancing Urgency: {summary.get('rebalancing_urgency', 'Unknown')}")
        
        # Show LLM insights if available
        if investment.get('llm_insights'):
            llm_insights = investment['llm_insights']
            print(f"\n  LLM Insights ({llm_insights.get('llm_provider', 'Unknown')}):")
            if llm_insights.get('explanation'):
                print(f"    {llm_insights['explanation'][:200]}...")
    
    print("\n" + "="*50)
    print("Report generated successfully!")
    print("="*50)
    
    # Check if LLM was used
    llm_used = False
    for agent_key in ['tax_analysis', 'estate_analysis', 'investment_analysis']:
        if agent_key in results:
            agent_result = results[agent_key]
            if isinstance(agent_result, dict) and agent_result.get('llm_insights'):
                llm_used = True
                break
    
    if llm_used:
        print("\nNote: Analysis enhanced with LLM insights")
    else:
        print("\nNote: Using rule-based analysis (set DEEPSEEK_API_KEY or ANTHROPIC_API_KEY for LLM enhancement)")


if __name__ == "__main__":
    main()

