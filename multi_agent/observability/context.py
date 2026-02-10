"""
Context variables for current session/span so nested calls can attach spans
without passing IDs through every function.
"""

import contextvars
from typing import Optional, Tuple

# (session_id, parent_span_id)
_observability_context: contextvars.ContextVar[Optional[Tuple[str, Optional[str]]]] = contextvars.ContextVar(
    "observability_context", default=None
)


def set_current_context(session_id: Optional[str], parent_span_id: Optional[str]) -> None:
    _observability_context.set((session_id, parent_span_id) if session_id else None)


def get_current_context() -> Tuple[Optional[str], Optional[str]]:
    ctx = _observability_context.get()
    if ctx is None:
        return None, None
    return ctx
