"""
Schemas for agent communication and data structures.
"""

from .messages import AgentMessage, MessageType, MessagePriority
from .agent_outputs import (
    PortfolioDataOutput,
    TaxAdvisorOutput,
    EstatePlannerOutput,
    InvestmentAnalystOutput
)
from .workflow_state import WorkflowState

__all__ = [
    'AgentMessage',
    'MessageType',
    'MessagePriority',
    'PortfolioDataOutput',
    'TaxAdvisorOutput',
    'EstatePlannerOutput',
    'InvestmentAnalystOutput',
    'WorkflowState'
]

