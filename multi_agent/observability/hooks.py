"""
Observability hooks: call these from orchestrator, agents, and LLM tools.
"""

import uuid
import time
from typing import Dict, Any, Optional
from datetime import datetime

from .events import Span, SpanKind
from .collector import get_observer
from . import context as _ctx

def set_current_context(session_id: Optional[str], parent_span_id: Optional[str]) -> None:
    """Set current context so nested LLM calls attach to the right parent."""
    _ctx.set_current_context(session_id, parent_span_id)

def get_current_context() -> tuple:
    """Get (session_id, parent_span_id) for current context."""
    return _ctx.get_current_context()


def _new_span_id() -> str:
    return f"span_{uuid.uuid4().hex[:12]}"


def start_session(query: Optional[str] = None, workflow_type: str = "sequential") -> str:
    """Start a new observability session. Returns session_id."""
    observer = get_observer()
    session_id = observer.start_session(query=query, workflow_type=workflow_type)
    set_current_context(session_id, None)
    return session_id


def end_session(session_id: str, status: str = "completed", error: Optional[str] = None) -> None:
    """End an observability session."""
    get_observer().end_session(session_id, status=status, error=error)
    set_current_context(None, None)


def start_span(
    session_id: str,
    parent_span_id: Optional[str],
    kind: SpanKind,
    name: str,
    **metadata: Any,
) -> str:
    """Start a span. Returns span_id. Call end_span(span_id) when done."""
    span_id = _new_span_id()
    span = Span(
        span_id=span_id,
        session_id=session_id,
        parent_span_id=parent_span_id,
        kind=kind,
        name=name,
        start_time=datetime.utcnow().isoformat() + "Z",
        metadata=dict(metadata),
    )
    observer = get_observer()
    observer.add_span(span)
    observer._spans_by_id[span_id] = span
    return span_id


def end_span(span_id: str, error: Optional[str] = None, **metadata: Any) -> None:
    """End a span and optionally add metadata."""
    observer = get_observer()
    span = observer._spans_by_id.get(span_id)
    if span:
        span.end(error=error)
        if metadata:
            span.metadata.update(metadata)


def record_llm_call(
    provider: str,
    model: str,
    prompt_preview: str,
    response_preview: str,
    duration_ms: float,
    session_id: Optional[str] = None,
    parent_span_id: Optional[str] = None,
    error: Optional[str] = None,
    **extra: Any,
) -> str:
    """Record an LLM call as a span. Uses current context if session_id/parent not given."""
    sid, pid = get_current_context() if (session_id is None and parent_span_id is None) else (session_id, parent_span_id)
    if not sid:
        return ""
    span_id = start_span(
        sid,
        pid,
        SpanKind.LLM_CALL,
        f"llm:{provider}:{model}",
        provider=provider,
        model=model,
        prompt_preview=prompt_preview[:500] if prompt_preview else "",
        response_preview=response_preview[:500] if response_preview else "",
        duration_ms=duration_ms,
        **extra,
    )
    end_span(span_id, error=error)
    return span_id


def record_agent_input(
    session_id: str,
    parent_span_id: Optional[str],
    agent_name: str,
    input_summary: Dict[str, Any],
) -> str:
    """Record start of an agent invocation (input received). Returns span_id to pass to end_span."""
    return start_span(
        session_id,
        parent_span_id,
        SpanKind.AGENT_MESSAGE,
        f"input:{agent_name}",
        agent=agent_name,
        direction="in",
        **input_summary,
    )


def record_agent_output(
    session_id: str,
    parent_span_id: Optional[str],
    agent_name: str,
    output_summary: Dict[str, Any],
) -> str:
    """Record output from an agent (data passed to next step)."""
    span_id = start_span(
        session_id,
        parent_span_id,
        SpanKind.AGENT_MESSAGE,
        f"output:{agent_name}",
        agent=agent_name,
        direction="out",
        **output_summary,
    )
    end_span(span_id)
    return span_id
