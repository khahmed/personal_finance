"""
Standard disclaimers for financial advisory outputs.
"""

DISCLAIMER = """
IMPORTANT DISCLAIMER:
This analysis is provided for informational and educational purposes only.
It does not constitute professional financial, tax, legal, or investment advice.
Always consult with a qualified professional (CPA, CFP, attorney) before making
financial decisions. Past performance does not guarantee future results.
Investments involve risk, including possible loss of principal.
"""

TAX_DISCLAIMER = """
TAX ADVICE DISCLAIMER:
This tax analysis is for educational purposes only and should not be considered
personalized tax advice. Tax laws vary by province and change annually. Please
consult with a qualified CPA or tax professional for personalized tax planning.
"""

INVESTMENT_DISCLAIMER = """
INVESTMENT ADVICE DISCLAIMER:
This investment analysis is for informational purposes only and does not
constitute a recommendation to buy, sell, or hold any security. Past
performance does not guarantee future results. All investments carry risk.
Please consult with a registered investment advisor before making investment
decisions.
"""

ESTATE_DISCLAIMER = """
ESTATE PLANNING DISCLAIMER:
This estate planning analysis is for educational purposes only and should not
be considered legal or financial advice. Estate laws vary by province. Please
consult with a qualified estate planning attorney and financial advisor for
personalized estate planning advice.
"""


def add_disclaimer_to_output(output: dict, agent_type: str = "general") -> dict:
    """
    Add appropriate disclaimer to agent output.
    
    Args:
        output: Agent output dictionary
        agent_type: Type of agent (tax, investment, estate, general)
        
    Returns:
        Output dictionary with disclaimer added
    """
    disclaimers = {
        "tax": TAX_DISCLAIMER,
        "investment": INVESTMENT_DISCLAIMER,
        "estate": ESTATE_DISCLAIMER,
        "general": DISCLAIMER
    }
    
    disclaimer = disclaimers.get(agent_type, DISCLAIMER)
    
    if "disclaimer" not in output:
        output["disclaimer"] = disclaimer
    
    return output

