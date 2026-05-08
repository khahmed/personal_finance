"""
Main entry point for the multi-agent financial advisory system.

Usage
─────
# Standard run (evolution enabled by default)
python -m multi_agent.main

# Run without evolution (faster, no DB writes)
python -m multi_agent.main --no-evolution

# Pass explicit feedback that feeds the evolution loop
python -m multi_agent.main --feedback accepted

# Show config version history for all agents
python -m multi_agent.main --history

# Roll back a specific agent to an earlier version
python -m multi_agent.main --rollback TaxAdvisorAgent --version 1
"""

import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_agent.flows.financial_advisory_flow import FinancialAdvisoryFlow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _print_separator(title: str = "") -> None:
    if title:
        print(f"\n{'='*50}")
        print(title)
        print("="*50)
    else:
        print("="*50)


def _print_results(results: dict) -> None:
    _print_separator("FINANCIAL ADVISORY REPORT")

    if "portfolio_data" in results:
        summary = results["portfolio_data"].get("portfolio_summary", {})
        print(f"\nPortfolio Value:      ${summary.get('total_value', 0):,.2f}")
        print(f"Number of Accounts:   {summary.get('num_accounts', 0)}")
        print(f"Number of Securities: {summary.get('num_securities', 0)}")

    if "tax_analysis" in results:
        tax    = results["tax_analysis"]
        report = tax.get("tax_optimization_report", {})
        print(f"\nTax Analysis (config v{_agent_version(results, 'tax_advisor')}):")
        print(f"  Unrealized Gains:        ${report.get('total_unrealized_gains', 0):,.2f}")
        print(f"  Unrealized Losses:       ${report.get('total_unrealized_losses', 0):,.2f}")
        print(f"  Estimated Tax Liability: ${report.get('estimated_tax_liability', 0):,.2f}")
        print(f"  Potential Tax Savings:   ${report.get('potential_tax_savings', 0):,.2f}")
        if report.get("inclusion_rate_used") is not None:
            print(f"  Inclusion Rate Used:     {report['inclusion_rate_used']:.0%}")

    if "estate_analysis" in results:
        estate = results["estate_analysis"]
        report = estate.get("estate_planning_report", {})
        print(f"\nEstate Planning (config v{_agent_version(results, 'estate_planner')}):")
        print(f"  Total Estate Value:     ${report.get('total_estate_value', 0):,.2f}")
        print(f"  Estimated Probate Fees: ${report.get('estimated_probate_fees', 0):,.2f}")

    if "investment_analysis" in results:
        inv    = results["investment_analysis"]
        report = inv.get("investment_analysis_report", {})
        print(f"\nInvestment Analysis (config v{_agent_version(results, 'investment_analyst')}):")
        print(f"  Portfolio Health Score: {report.get('portfolio_health_score', 0):.1f}/10")
        print(f"  Concentration Risk:     {report.get('concentration_risk_level', 'Unknown')}")
        print(f"  Rebalancing Urgency:    {report.get('rebalancing_urgency', 'Unknown')}")

        if inv.get("llm_insights"):
            insights = inv["llm_insights"]
            print(f"\n  LLM Insights ({insights.get('llm_provider', 'Unknown')}):")
            explanation = insights.get("explanation", "")
            print(f"    {explanation[:200]}{'...' if len(explanation) > 200 else ''}")

    # ── Evolution summary ──────────────────────────────────────────────────
    evo = results.get("evolution", {})
    if evo:
        print("\nEvolution Step:")
        if evo.get("evolved"):
            for agent, detail in evo.get("updates", {}).items():
                print(
                    f"  ✓ {agent} evolved to v{detail.get('new_version')} "
                    f"(confidence={detail.get('confidence', 0):.2f})"
                )
            if evo.get("critique_summary"):
                print(f"  Summary: {evo['critique_summary']}")
        else:
            reason = evo.get("skipped_reason", "no changes warranted")
            print(f"  No evolution: {reason}")

    _print_separator()
    print("Report generated successfully!")
    _print_separator()

    llm_used = any(
        results.get(k, {}).get("llm_insights")
        for k in ("tax_analysis", "estate_analysis", "investment_analysis")
    )
    if llm_used:
        print("\nNote: Analysis enhanced with LLM insights")
    else:
        print(
            "\nNote: Using rule-based analysis "
            "(set DEEPSEEK_API_KEY or ANTHROPIC_API_KEY for LLM enhancement)"
        )


def _agent_version(results: dict, agent_key: str) -> str:
    """Extract the config version used by an agent from workflow_state."""
    state = results.get("workflow_state", {})
    outputs = state.get("agent_outputs", {})
    agent_out = outputs.get(agent_key, {})
    return str(agent_out.get("config_version", "?"))


def _show_history() -> None:
    """Print config version history for all evolvable agents."""
    try:
        from multi_agent.config.agent_config_store import AgentConfigStore
        store = AgentConfigStore.get_instance()
        agents = [
            "TaxAdvisorAgent", "EstatePlannerAgent",
            "InvestmentAnalystAgent", "MetaEvolutionAgent",
        ]
        for name in agents:
            versions = store.list_versions(name)
            print(f"\n{name}:")
            if not versions:
                print("  No versions in DB (using hardcoded defaults)")
            for v in versions:
                active = "← ACTIVE" if v.get("is_active") else ""
                print(
                    f"  v{v['version']}  {v.get('created_at', '')[:19]}  "
                    f"{(v.get('evolution_reason') or '')[:60]}  {active}"
                )
    except Exception as e:
        print(f"Could not read history: {e}")


def _rollback(agent_name: str, version: int) -> None:
    try:
        from multi_agent.agents.meta_evolution_agent import MetaEvolutionAgent
        meta = MetaEvolutionAgent()
        success = meta.rollback_agent(agent_name, version)
        if success:
            print(f"Rolled back {agent_name} to version {version}")
        else:
            print(f"Rollback failed for {agent_name} v{version}")
    except Exception as e:
        print(f"Rollback error: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-agent financial advisory system")
    parser.add_argument("--no-evolution", action="store_true",
                        help="Skip the MetaEvolutionAgent step")
    parser.add_argument("--feedback", choices=["accepted", "rejected", "modified"],
                        help="Explicit feedback for this run (logged for evolution)")
    parser.add_argument("--history", action="store_true",
                        help="Show config version history for all agents and exit")
    parser.add_argument("--rollback", metavar="AGENT_NAME",
                        help="Roll back AGENT_NAME to --version")
    parser.add_argument("--version", type=int,
                        help="Version number for --rollback")
    parser.add_argument("--parallel", action="store_true",
                        help="Use parallel workflow instead of sequential")
    args = parser.parse_args()

    if args.history:
        _show_history()
        return

    if args.rollback:
        if not args.version:
            print("--rollback requires --version")
            sys.exit(1)
        _rollback(args.rollback, args.version)
        return

    flow = FinancialAdvisoryFlow()

    user_context = {
        "tax_bracket": "mid",
        "tax_rate":    0.30,
        "province":    "ON",
        "age":         55,
        "risk_profile": "moderate",
    }

    enable_evolution = not args.no_evolution
    workflow_type    = "parallel" if args.parallel else "sequential"

    print(
        f"Running comprehensive financial review "
        f"(workflow={workflow_type}, evolution={enable_evolution})..."
    )

    results = flow.get_comprehensive_review(
        user_context=user_context,
        enable_evolution=enable_evolution,
        user_feedback=args.feedback,
    )

    if "error" in results:
        print(f"Error: {results['error']}")
        return

    _print_results(results)


if __name__ == "__main__":
    main()
