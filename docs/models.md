# ClawFlow 数据模型文档

## 模型总览

```
Organization
    │
    ├── Role (角色)
    │       └── hierarchy_level: 1-4
    │       └── reports_to: Role.id
    │
    ├── Task (任务)
    │       └── assigned_role_id: Role.id
    │       └── dependencies: [Task.id]
    │
    ├── DataFlow (数据流)
    │       ├── DataFlowNode (节点)
    │       └── DataFlowEdge (连线)
    │
    └── Knowledge (知识)

Skill (独立)
    └── RAG Models (扩展)
```

---

## Organization (组织)

**文件位置**：`data/organizations/{org_id}/organization.json`

```python
class OrganizationStatus(str, Enum):
    DRAFT = "draft"       # 草稿
    DEPLOYED = "deployed" # 已部署
    RUNNING = "running"   # 运行中
    STOPPED = "stopped"   # 已停止

class Organization(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    logo: Optional[str] = None
    status: OrganizationStatus = OrganizationStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

**字段说明**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | UUID | 自动 | 唯一标识 |
| name | string | 是 | 组织名称 |
| description | string | 否 | 组织描述 |
| logo | string | 否 | Logo URL |
| status | enum | 否 | 状态，默认 draft |
| created_at | datetime | 自动 | 创建时间 |
| updated_at | datetime | 自动 | 更新时间 |

---

## Role (角色)

**文件位置**：`data/organizations/{org_id}/roles/{role_id}.json`

```python
class PermissionLevel(str, Enum):
    ADMIN = "admin"       # 管理员
    MANAGER = "manager"   # 经理
    MEMBER = "member"     # 成员
    READONLY = "readonly" # 只读

class Role(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    name: str
    description: Optional[str] = None
    responsibilities: List[str] = []
    required_skills: List[str] = []
    reports_to: Optional[str] = None  # 父角色 ID
    permission_level: PermissionLevel = PermissionLevel.MEMBER
    hierarchy_level: int = 1  # 1-4
    soul_template: Optional[str] = None
    identity_template: Optional[str] = None
    agents_config: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

**字段说明**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | UUID | 自动 | 唯一标识 |
| organization_id | UUID | 是 | 所属组织 |
| name | string | 是 | 角色名称 |
| description | string | 否 | 角色描述 |
| responsibilities | array | 否 | 职责列表 |
| required_skills | array | 否 | 所需技能 |
| reports_to | UUID | 否 | 上级角色 ID |
| permission_level | enum | 否 | 权限级别 |
| hierarchy_level | int | 否 | 层级 (1-4) |
| soul_template | string | 否 | 自定义 SOUL.md |
| identity_template | string | 否 | 自定义 IDENTITY.md |
| agents_config | object | 否 | Agent 配置 |

**层级定义**：

| 层级 | 名称 | 说明 |
|------|------|------|
| 1 | 基础角色 | 执行具体任务 |
| 2 | 小组负责人 | 协调多个基础角色 |
| 3 | 部门负责人 | 管理多个小组 |
| 4 | 高层管理 | 制定策略和决策 |

---

## Task (任务)

**文件位置**：`data/organizations/{org_id}/tasks/{task_id}.json`

```python
class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ExecutionMode(str, Enum):
    SEQUENTIAL = "sequential"   # 顺序执行
    PARALLEL = "parallel"       # 并行执行
    CONDITIONAL = "conditional"  # 条件执行

class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    name: str
    description: Optional[str] = None
    input_schema: Dict[str, Any] = {}
    output_schema: Dict[str, Any] = {}
    assigned_role_id: Optional[str] = None
    dependencies: List[str] = []  # 依赖任务 ID 列表
    priority: Priority = Priority.MEDIUM
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    conditions: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

**字段说明**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | UUID | 自动 | 唯一标识 |
| organization_id | UUID | 是 | 所属组织 |
| name | string | 是 | 任务名称 |
| description | string | 否 | 任务描述 |
| input_schema | object | 否 | 输入数据模式 |
| output_schema | object | 否 | 输出数据模式 |
| assigned_role_id | UUID | 否 | 执行角色 |
| dependencies | array | 否 | 依赖任务 ID |
| priority | enum | 否 | 优先级 |
| execution_mode | enum | 否 | 执行模式 |
| conditions | object | 否 | 执行条件 |

**执行模式说明**：

| 模式 | 说明 |
|------|------|
| sequential | 按依赖顺序依次执行 |
| parallel | 所有依赖完成后并行执行 |
| conditional | 根据 conditions 决定执行路径 |

---

## DataFlow (数据流)

**文件位置**：`data/organizations/{org_id}/dataflows/{dataflow_id}.json`

### DataFlowNode (数据流节点)

```python
class NodeType(str, Enum):
    ROLE = "role"         # 角色节点
    TASK = "task"         # 任务节点
    KNOWLEDGE = "knowledge" # 知识节点
    INPUT = "input"        # 输入节点
    OUTPUT = "output"      # 输出节点

class DataFlowNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: NodeType
    ref_id: Optional[str] = None  # 关联实体 ID
    position: Dict[str, float] = {"x": 0, "y": 0}
    label: Optional[str] = None
```

### DataFlowEdge (数据流连线)

```python
class DataFlowEdge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str   # 源节点 ID
    target: str   # 目标节点 ID
    data_mapping: Dict[str, Any] = {}
    condition: Optional[str] = None
```

### DataFlow (完整数据流)

```python
class DataFlow(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    name: str
    description: Optional[str] = None
    nodes: List[DataFlowNode] = []
    edges: List[DataFlowEdge] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

**节点类型说明**：

| 类型 | 说明 | 示例 |
|------|------|------|
| role | 执行者角色 | "工程师" |
| task | 具体任务 | "代码审查" |
| knowledge | 知识库引用 | "API 文档" |
| input | 外部输入 | "用户请求" |
| output | 外部输出 | "回复邮件" |

---

## Knowledge (知识)

**文件位置**：`data/organizations/{org_id}/knowledge/{knowledge_id}.json`

```python
class Knowledge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    title: str
    content: str
    category: Optional[str] = None
    tags: List[str] = []
    version: int = 1
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

**字段说明**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | UUID | 自动 | 唯一标识 |
| organization_id | UUID | 是 | 所属组织 |
| title | string | 是 | 知识标题 |
| content | string | 是 | 知识内容 |
| category | string | 否 | 分类 |
| tags | array | 否 | 标签 |
| version | int | 自动 | 版本号 |

**分类示例**：
- 公司制度
- 产品文档
- 技术规范
- 运营流程
- 其他

---

## Skill (技能)

**文件位置**：`data/skills/registry.json`

```python
class Skill(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    version: str = "1.0.0"
    description: Optional[str] = None
    author: Optional[str] = None
    tags: List[str] = []
    installed: bool = False
    installed_at: Optional[datetime] = None
    local_path: Optional[str] = None
```

**字段说明**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | UUID | 自动 | 唯一标识 |
| name | string | 是 | 技能名称 |
| version | string | 否 | 版本号 |
| description | string | 否 | 描述 |
| author | string | 否 | 作者 |
| tags | array | 否 | 标签 |
| installed | bool | 自动 | 是否已安装 |
| installed_at | datetime | 否 | 安装时间 |
| local_path | string | 否 | 本地路径 |

---

## RAG Models (扩展)

### Document

```python
class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"

class DocumentType(str, Enum):
    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"

class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    title: str
    content: str
    doc_type: DocumentType = DocumentType.TEXT
    status: DocumentStatus = DocumentStatus.PENDING
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

### Chunk

```python
class Chunk(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    content: str
    index: int  # 在文档中的顺序
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.now)
```

### ChunkEmbedding

```python
class ChunkEmbedding(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chunk_id: str
    embedding: List[float]
    model: str = "default"
    created_at: datetime = Field(default_factory=datetime.now)
```

### RAGQuery & RAGResult

```python
class RAGQuery(BaseModel):
    query: str
    top_k: int = 5
    organization_id: str

class RAGResult(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: Dict[str, Any] = {}

class RAGResponse(BaseModel):
    query: str
    results: List[RAGResult]
    total: int
```

---

## 存储结构

```
data/
├── organizations/
│   └── {org_id}/
│       ├── organization.json      # 组织信息
│       ├── roles/
│       │   ├── {role_id}.json
│       │   └── ...
│       ├── tasks/
│       │   ├── {task_id}.json
│       │   └── ...
│       ├── dataflows/
│       │   ├── {dataflow_id}.json
│       │   └── ...
│       └── knowledge/
│           ├── {knowledge_id}.json
│           └── ...
├── skills/
│   ├── registry.json             # 技能注册表
│   └── {skill_name}/
│       └── SKILL.md
└── embeddings/                  # 向量存储 (扩展)
    └── {org_id}/
        └── ...
```
