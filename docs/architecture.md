# ClawFlow 架构文档

## 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         ClawFlow                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐         ┌──────────────────┐               │
│  │    Frontend      │         │     Backend      │               │
│  │   (React SPA)    │◄──────►│    (FastAPI)     │               │
│  │   Port 8000      │   HTTP  │    Port 8000     │               │
│  └──────────────────┘         └────────┬─────────┘               │
│                                        │                         │
│                          ┌─────────────┼─────────────┐           │
│                          ▼             ▼             ▼           │
│                   ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│                   │Storage    │ │OpenClaw  │ │ClawHub   │        │
│                   │(JSON/File)│ │Adapter   │ │Client    │        │
│                   └──────────┘ └──────────┘ └──────────┘        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 分层架构

### 1. 前端层 (Frontend Layer)

**技术选型**：
- React 18 (CDN)
- Ant Design 5 (CDN)
- Axios (HTTP 客户端)
- Babel Standalone (JSX 编译)

**职责**：
- 用户界面渲染
- 表单处理和验证
- 状态管理 (React useState/useEffect)
- 与后端 API 通信

**特点**：
- 单页应用 (SPA)
- 无需构建，CDN 直接加载
- 响应式设计

### 2. API 层 (API Layer)

**技术选型**：
- FastAPI
- Pydantic (数据验证)
- Uvicorn (ASGI 服务器)

**路由模块**：

| 路由模块 | 路径前缀 | 功能 |
|---------|----------|------|
| organizations | `/api/v1/organizations` | 组织 CRUD |
| roles | `/api/v1/roles` | 角色管理（全局） |
| tasks | `/api/v1/organizations/{org_id}/tasks` | 任务管理 |
| dataflows | `/api/v1/organizations/{org_id}/dataflows` | 数据流管理 |
| knowledge | `/api/v1/organizations/{org_id}/knowledge` | 知识库管理 |
| skills | `/api/v1/skills` | 技能管理 |

### 3. 服务层 (Service Layer)

#### StorageService
- 通用 JSON 文件存储
- 支持任何 Pydantic 模型
- 持久化到 `data/` 目录

#### OpenClawAdapter
- 将 ClawFlow 组织转换为 OpenClaw Agent
- 生成 SOUL.md, IDENTITY.md, AGENTS.md
- 管理 Agent 工作区

#### RAGService (可选扩展)
- 文档处理和分块
- 向量嵌入生成
- 相似度检索

### 4. 数据层 (Data Layer)

**存储位置**：`data/`

```
data/
├── organizations/           # 组织数据
│   └── {org_id}/
│       ├── roles/         # 角色 JSON
│       ├── tasks/         # 任务 JSON
│       ├── dataflows/     # 数据流 JSON
│       └── knowledge/     # 知识 JSON
├── skills/                # 已安装技能
│   └── registry.json      # 技能注册表
└── skills/                # ClawHub 缓存
```

### 5. 集成层 (Integration Layer)

#### OpenClaw 工作区
- 部署路径：`openclaw_workspace/{org_id}/{role_name}/`
- 每个角色一个目录
- 包含完整的 Agent 文件结构

#### ClawHub 客户端
- 技能搜索 API
- 技能元数据缓存
- 本地技能安装/卸载

## 核心组件

### Organization (组织)

```python
class Organization(BaseModel):
    id: str                          # UUID
    name: str                        # 组织名称
    description: Optional[str]       # 描述
    status: OrganizationStatus       # draft/deployed/running/stopped
    created_at: datetime
    updated_at: datetime
```

**状态流转**：
```
draft → deployed → running
                   ↘ stopped
```

### Role (角色)

```python
class Role(BaseModel):
    id: str
    organization_id: str
    name: str
    description: Optional[str]
    responsibilities: List[str]      # 职责列表
    required_skills: List[str]     # 所需技能
    reports_to: Optional[str]       # 汇报对象 (Role ID)
    hierarchy_level: int            # 1-4
    permission_level: PermissionLevel
    soul_template: Optional[str]    # 自定义 SOUL.md
    identity_template: Optional[str]
```

**层级结构**：
```
Level 4: 高层管理 (CEO, CTO, CFO)
    │
Level 3: 部门负责人 (VP, Director)
    │
Level 2: 小组负责人 (Manager, Lead)
    │
Level 1: 基础角色 (Individual Contributor)
```

### Task (任务)

```python
class Task(BaseModel):
    id: str
    organization_id: str
    name: str
    description: Optional[str]
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    assigned_role_id: Optional[str]
    dependencies: List[str]         # 依赖任务 ID
    priority: Priority             # high/medium/low
    execution_mode: ExecutionMode   # sequential/parallel/conditional
```

### DataFlow (数据流)

```python
class DataFlowNode(BaseModel):
    id: str
    type: NodeType                  # role/task/knowledge/input/output
    ref_id: Optional[str]           # 关联实体 ID
    position: Dict[str, float]     # x, y 坐标
    label: Optional[str]

class DataFlowEdge(BaseModel):
    id: str
    source: str                    # 源节点 ID
    target: str                    # 目标节点 ID
    data_mapping: Dict[str, Any]
    condition: Optional[str]

class DataFlow(BaseModel):
    id: str
    organization_id: str
    name: str
    nodes: List[DataFlowNode]
    edges: List[DataFlowEdge]
```

### Knowledge (知识)

```python
class Knowledge(BaseModel):
    id: str
    organization_id: str
    title: str
    content: str                   # 知识内容
    category: Optional[str]        # 分类
    tags: List[str]                # 标签
    version: int                   # 版本号
```

### Skill (技能)

```python
class Skill(BaseModel):
    id: str
    name: str
    version: str
    description: Optional[str]
    author: Optional[str]
    tags: List[str]
    installed: bool
    installed_at: Optional[datetime]
    local_path: Optional[str]      # 本地路径
```

## OpenClaw 文件映射

| ClawFlow | OpenClaw | 说明 |
|----------|----------|------|
| Organization | `openclaw_workspace/{org_id}/` | 组织根目录 |
| Role | `{role_name}/` | 角色目录 |
| Role.soul_template | `SOUL.md` | Agent 灵魂 |
| Role.identity_template | `IDENTITY.md` | Agent 身份 |
| Role.agents_config | `AGENTS.md` | Agent 配置 |
| Task 定义 | `HEARTBEAT.md` | 定时任务 |
| Skill | `skills/` | 技能目录 |

## 部署流程

```
用户点击部署
       │
       ▼
┌──────────────────┐
│ 部署确认          │
│ 验证组织完整性    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 创建工作区目录    │
│ openclaw_workspace/
│   └── {org_id}/  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 遍历所有角色      │
│ 对每个角色：      │
│ - 创建目录        │
│ - 生成 SOUL.md   │
│ - 生成 IDENTITY.md│
│ - 生成 AGENTS.md │
│ - 复制技能        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 更新组织状态      │
│ status = deployed │
└──────────────────┘
```

## 安全考虑

1. **CORS**：允许所有来源 (`allow_origins=["*"]`)
2. **数据隔离**：每个组织数据独立存储
3. **文件操作**：使用 shutil 而非危险命令
4. **输入验证**：Pydantic 模型自动验证

## 扩展点

1. **数据库**：可替换 StorageService 为 SQLAlchemy
2. **认证**：可添加 JWT 认证中间件
3. **向量检索**：集成向量数据库支持 RAG
4. **实时通信**：添加 WebSocket 支持
