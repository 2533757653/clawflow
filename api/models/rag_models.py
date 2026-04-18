from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentType(str, Enum):
    KNOWLEDGE = "knowledge"
    SPEC = "spec"
    README = "readme"
    CODE = "code"
    API_DOC = "api_doc"
    OTHER = "other"


class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: Optional[str] = None
    title: str
    content: str
    doc_type: DocumentType = DocumentType.OTHER
    source: Optional[str] = None
    metadata: Dict[str, Any] = {}
    status: DocumentStatus = DocumentStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Chunk(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    content: str
    chunk_index: int
    token_count: int = 0
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ChunkEmbedding(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chunk_id: str
    embedding: List[float]
    model: str = "text-embedding-ada-002"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class RAGQuery(BaseModel):
    query: str
    top_k: int = 5
    organization_id: Optional[str] = None
    doc_types: Optional[List[DocumentType]] = None
    filters: Optional[Dict[str, Any]] = None


class RAGResult(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: Dict[str, Any] = {}


class RAGResponse(BaseModel):
    query: str
    results: List[RAGResult]
    total_chunks: int
    processing_time_ms: float


class SystemRoleType(str, Enum):
    DECIDER = "decider"
    ACTOR = "actor"
    FEEDBACKER = "feedbacker"


class ExecutorType(str, Enum):
    ROLE = "role"
    SYSTEM = "system"


class ExecutorUnit(BaseModel):
    type: ExecutorType
    role_id: Optional[str] = None
    system_id: Optional[str] = None
    depth: int = 0
    name: Optional[str] = None


class DeciderConfig(BaseModel):
    decision_type: str = "directive"
    scope: List[str] = []
    autonomy_level: str = "medium"


class ActorConfig(BaseModel):
    action_type: str = "execute"
    skills: List[str] = []
    reporting_mode: str = "effect"


class FeedbackerConfig(BaseModel):
    feedback_type: str = "observation"
    metrics: List[str] = []
    termination_condition: Optional[str] = None


class SystemNode(BaseModel):
    role_id: str
    role_type: SystemRoleType
    config: Dict[str, Any] = {}


class SystemEdge(BaseModel):
    source_id: str
    target_id: str
    edge_type: str
    data_mapping: Dict[str, Any] = {}


class AgentSystem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    name: str
    description: Optional[str] = None
    decider: Optional[ExecutorUnit] = None
    actors: List[ExecutorUnit] = []
    feedbacker: Optional[ExecutorUnit] = None
    nodes: List[SystemNode] = []
    edges: List[SystemEdge] = []
    state: str = "initialized"
    loop_count: int = 0
    max_loops: Optional[int] = None
    max_depth: int = 3
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class SystemLoopStep(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    system_id: str
    step_index: int
    phase: str
    depth: int = 0
    executor_type: Optional[str] = None
    executor_name: Optional[str] = None
    decider_output: Optional[Dict[str, Any]] = None
    actor_output: Optional[Dict[str, Any]] = None
    feedbacker_output: Optional[Dict[str, Any]] = None
    terminated: bool = False
    termination_reason: Optional[str] = None
    child_steps: List["SystemLoopStep"] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)