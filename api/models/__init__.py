from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

from api.models.rag_models import (
    Document,
    DocumentStatus,
    DocumentType,
    Chunk,
    ChunkEmbedding,
    RAGQuery,
    RAGResult,
    RAGResponse,
    SystemRoleType,
    ExecutorType,
    ExecutorUnit,
    DeciderConfig,
    ActorConfig,
    FeedbackerConfig,
    SystemNode,
    SystemEdge,
    AgentSystem,
    SystemLoopStep
)

from api.models.memory import (
    MemoryType,
    MemoryEntry,
    MemoryCompressionRequest,
    MemoryCompressionResult,
    MemoryResetRequest,
    MemoryResetResult,
    MemoryStats,
    PromptEnhancementRequest,
    PromptEnhancementResponse,
    CompressionCallbackRequest
)


class OrganizationStatus(str, Enum):
    DRAFT = "draft"
    DEPLOYED = "deployed"
    RUNNING = "running"
    STOPPED = "stopped"


class PermissionLevel(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    READONLY = "readonly"


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ExecutionMode(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"


class NodeType(str, Enum):
    ROLE = "role"
    TASK = "task"
    KNOWLEDGE = "knowledge"
    INPUT = "input"
    OUTPUT = "output"


class BaseModelWithDates(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ComponentType(str, Enum):
    HEADER = "header"
    ROLE_LIST = "role_list"
    TASK_LIST = "task_list"
    KNOWLEDGE = "knowledge"
    DATA_FLOW = "data_flow"
    SKILL = "skill"
    PROMPT = "prompt"
    MEMORY = "memory"
    CUSTOM = "custom"


class OrgComponent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: ComponentType
    position: Dict[str, float] = {"x": 0, "y": 0}
    size: Dict[str, float] = {"width": 200, "height": 100}
    config: Dict[str, Any] = {}
    label: Optional[str] = None


class Organization(BaseModelWithDates):
    name: str
    description: Optional[str] = None
    logo: Optional[str] = None
    status: OrganizationStatus = OrganizationStatus.DRAFT
    initial_prompt: Optional[str] = None
    input_role_id: Optional[str] = None
    role_ids: List[str] = []
    layout: List[OrgComponent] = []


class Role(BaseModelWithDates):
    name: str
    description: Optional[str] = None
    responsibilities: List[str] = []
    required_skills: List[str] = []
    reports_to: Optional[str] = None
    permission_level: PermissionLevel = PermissionLevel.MEMBER
    hierarchy_level: int = 1
    soul_template: Optional[str] = None
    identity_template: Optional[str] = None
    context_memory: Optional[str] = None
    division: Optional[str] = None
    source: Optional[str] = "manual"


class Task(BaseModelWithDates):
    organization_id: str
    name: str
    description: Optional[str] = None
    prompt: Optional[str] = None
    input_schema: Dict[str, Any] = {}
    output_schema: Dict[str, Any] = {}
    assigned_role_id: Optional[str] = None
    dependencies: List[str] = []
    priority: Priority = Priority.MEDIUM
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    conditions: Dict[str, Any] = {}


class DataFlowNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: NodeType
    ref_id: Optional[str] = None
    position: Dict[str, float] = {"x": 0, "y": 0}
    label: Optional[str] = None


class DataFlowEdge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str
    target: str
    data_mapping: Dict[str, Any] = {}
    condition: Optional[str] = None


class DataFlow(BaseModelWithDates):
    organization_id: str
    name: str
    description: Optional[str] = None
    nodes: List[DataFlowNode] = []
    edges: List[DataFlowEdge] = []


class Knowledge(BaseModelWithDates):
    organization_id: str
    title: str
    content: str
    category: Optional[str] = None
    tags: List[str] = []
    version: int = 1


class Skill(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    version: str = "1.0.0"
    description: Optional[str] = None
    author: Optional[str] = None
    tags: List[str] = []
    installed: bool = False
    installed_at: Optional[datetime] = None
    installed_roles: List[str] = []
    local_path: Optional[str] = None


class DeployedAgent(BaseModel):
    role_id: str
    agent_name: str
    deployed_at: datetime = Field(default_factory=datetime.now)
    status: str = "running"
