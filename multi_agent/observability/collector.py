"""
In-memory collector for observability events.
Stores sessions and spans for retrieval by the web UI or external tools.
"""

import threading
from typing import Dict, Any, Optional, List
from datetime import datetime
from .events import Span, SpanKind


class ObservabilityCollector:
    """Singleton collector for spans and sessions."""

    _instance: Optional["ObservabilityCollector"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "ObservabilityCollector":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._spans: Dict[str, List[Span]] = {}  # session_id -> list of spans
        self._spans_by_id: Dict[str, Span] = {}  # span_id -> Span
        self._max_sessions = 100
        self._max_spans_per_session = 500
        self._lock = threading.Lock()

    def start_session(self, query: Optional[str] = None, workflow_type: str = "sequential") -> str:
        session_id = f"sess_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{id(self) % 100000}"
        with self._lock:
            self._sessions[session_id] = {
                "session_id": session_id,
                "query": query,
                "workflow_type": workflow_type,
                "start_time": datetime.utcnow().isoformat() + "Z",
                "end_time": None,
                "status": "running",
                "span_count": 0,
            }
            self._spans[session_id] = []
            self._trim_sessions()
        return session_id

    def end_session(self, session_id: str, status: str = "completed", error: Optional[str] = None) -> None:
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id]["end_time"] = datetime.utcnow().isoformat() + "Z"
                self._sessions[session_id]["status"] = status
                if error:
                    self._sessions[session_id]["error"] = error

    def add_span(self, span: Span) -> None:
        with self._lock:
            sid = span.session_id
            if sid not in self._spans:
                self._spans[sid] = []
            if len(self._spans[sid]) < self._max_spans_per_session:
                self._spans[sid].append(span)
                self._spans_by_id[span.span_id] = span  # allow end_span to find it
            if sid in self._sessions:
                self._sessions[sid]["span_count"] = len(self._spans[sid])

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            if session_id not in self._sessions:
                return None
            session = dict(self._sessions[session_id])
            spans = [s.to_dict() for s in self._spans.get(session_id, [])]
            spans.sort(key=lambda x: x["start_time"])
            session["spans"] = spans
            return session

    def list_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            sessions = list(self._sessions.values())
            sessions.sort(key=lambda x: x["start_time"], reverse=True)
            return sessions[:limit]

    def _trim_sessions(self) -> None:
        if len(self._sessions) <= self._max_sessions:
            return
        by_time = sorted(self._sessions.items(), key=lambda x: x[1]["start_time"])
        to_remove = len(by_time) - self._max_sessions
        for i in range(to_remove):
            sid = by_time[i][0]
            for span in self._spans.get(sid, []):
                self._spans_by_id.pop(span.span_id, None)
            del self._sessions[sid]
            del self._spans[sid]


def get_observer() -> ObservabilityCollector:
    return ObservabilityCollector()
