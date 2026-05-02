from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid


class SessionStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SessionNodeState(BaseModel):
    node_id: str
    status: str
    input_data: Dict[str, Any] = {}
    output_data: Dict[str, Any] = {}
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class Session(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    input_role_id: str
    dataflow_id: Optional[str] = None
    status: SessionStatus = SessionStatus.RUNNING
    initial_prompt: str
    current_node_id: Optional[str] = None
    node_states: List[SessionNodeState] = []
    context: Dict[str, Any] = {}
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
