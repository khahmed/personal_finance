"""
Observability hooks for the multi-agent system.
Monitor LLM calls, agent invocations, and inter-agent interactions.
"""

from .events import SpanKind, Span
from .collector import get_observer
from .hooks import (
    start_session,
    end_session,
    start_span,
    end_span,
    record_llm_call,
    record_agent_input,
    record_agent_output,
    set_current_context,
    get_current_context,
)

__all__ = [
    "SpanKind",
    "Span",
    "get_observer",
    "start_session",
    "end_session",
    "start_span",
    "end_span",
    "record_llm_call",
    "record_agent_input",
    "record_agent_output",
    "set_current_context",
    "get_current_context",
]
