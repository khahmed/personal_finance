"""
Message schemas for agent-to-agent communication.
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Types of messages between agents."""
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    ERROR = "error"


class MessagePriority(str, Enum):
    """Message priority levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AgentMessage(BaseModel):
    """Standardized message format for agent communication."""
    
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    from_agent: str
    to_agent: str
    message_type: MessageType
    priority: MessagePriority = MessagePriority.MEDIUM
    payload: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True

