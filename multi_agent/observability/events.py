"""
Event and span types for observability.
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid


class SpanKind(str, Enum):
    """Type of span for categorization."""
    WORKFLOW = "workflow"
    AGENT = "agent"
    LLM_CALL = "llm_call"
    AGENT_MESSAGE = "agent_message"  # Data passed from one agent to another


@dataclass
class Span:
    """A single observability span (unit of work)."""
    span_id: str
    session_id: str
    parent_span_id: Optional[str]
    kind: SpanKind
    name: str
    start_time: str  # ISO format
    end_time: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "span_id": self.span_id,
            "session_id": self.session_id,
            "parent_span_id": self.parent_span_id,
            "kind": self.kind.value if isinstance(self.kind, SpanKind) else self.kind,
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "metadata": self.metadata,
            "error": self.error,
            "duration_ms": self.duration_ms(),
        }

    def duration_ms(self) -> Optional[float]:
        if not self.end_time:
            return None
        try:
            start = datetime.fromisoformat(self.start_time.replace("Z", "+00:00"))
            end = datetime.fromisoformat(self.end_time.replace("Z", "+00:00"))
            return (end - start).total_seconds() * 1000
        except Exception:
            return None

    def end(self, error: Optional[str] = None) -> None:
        self.end_time = datetime.utcnow().isoformat() + "Z"
        if error:
            self.error = error
