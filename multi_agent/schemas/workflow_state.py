"""
Workflow state management schema.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class UserContext(BaseModel):
    """User context information."""
    user_id: Optional[str] = None
    risk_profile: Optional[str] = None
    tax_bracket: Optional[str] = None
    province: Optional[str] = None
    age: Optional[int] = None
    goals: List[str] = Field(default_factory=list)


class WorkflowState(BaseModel):
    """Shared workflow state across agents."""
    
    session_id: str
    user_context: UserContext = Field(default_factory=UserContext)
    data_cache: Dict[str, Any] = Field(default_factory=dict)
    agent_outputs: Dict[str, Any] = Field(default_factory=dict)
    workflow_status: str = "in_progress"  # in_progress, completed, error
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def update(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow().isoformat()

