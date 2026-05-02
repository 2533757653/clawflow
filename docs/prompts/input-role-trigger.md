# Prompt: 输入角色触发机制

## 项目信息

- **项目名称**: ClawFlow - Agent 组织动态构建平台
- **项目路径**: `d:\clawflow`
- **后端**: `api/` (FastAPI + Python 3.11+)
- **前端**: `web/` (React 18 + TypeScript)

## 项目架构

参见 `docs/prompts/workflow-execution-engine.md`

## 已有实现

### Organization 端点 (已实现)
位置: `api/routers/organizations.py`

```python
@router.post("/{org_id}/start")
async def start_organization(org_id: str):
    # 当前实现仅更新状态为 running
    org.status = OrganizationStatus.RUNNING
```

### Memory Service (已实现)
位置: `api/routers/memory.py`

### OpenClawAdapter (已实现)
位置: `api/services/openclaw_adapter.py`

## 设计决策

根据 SPEC.md "设计决策记录" section 3:

### 用户输入入口 (input_role)

1. **Organization.input_role_id**: 指定接收外部输入的角色
2. **用户输入流程**:
   - 用户输入 prompt
   - 发送给 input_role_id 对应的角色
   - 该角色被触发后，根据数据流生成传递给下一个角色的 prompt
   - 形成完整的工作流链路

3. **Session 管理**: 需要追踪每个用户会话的执行上下文

## 任务要求

### 1. 增强 Start Organization 端点

修改 `api/routers/organizations.py`:

```python
class StartOrgRequest(BaseModel):
    initial_prompt: str
    dataflow_id: Optional[str] = None

@router.post("/{org_id}/start")
async def start_organization(org_id: str, request: StartOrgRequest):
    """
    启动组织:
    1. 验证组织状态为 deployed
    2. 验证 input_role_id 已设置
    3. 创建新 session
    4. 发送 initial_prompt 给 input_role
    5. 返回 session_id
    """
```

### 2. Session 数据模型

创建 `api/models/session.py`:

```python
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
    status: str  # pending, running, completed, failed
    input_data: Dict[str, Any] = {}
    output_data: Dict[str, Any] = {}
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class Session(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    input_role_id: str
    dataflow_id: Optional[str] = None
    status: SessionStatus = SessionStatus.RUNNING
    initial_prompt: str
    current_node_id: Optional[str] = None
    node_states: List[SessionNodeState] = []
    context: Dict[str, Any] = {}  # 跨节点传递的上下文
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

### 3. Session 存储服务

创建 `api/services/session_service.py`:

```python
class SessionService:
    def __init__(self, storage_path: str = "data/sessions"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)

    def _get_session_path(self, session_id: str) -> str:
        return os.path.join(self.storage_path, f"{session_id}.json")

    def create_session(self, org_id: str, input_role_id: str, initial_prompt: str, dataflow_id: str = None) -> Session:
        session = Session(
            organization_id=org_id,
            input_role_id=input_role_id,
            initial_prompt=initial_prompt,
            dataflow_id=dataflow_id
        )
        self._save_session(session)
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        ...

    def update_session(self, session: Session) -> Session:
        ...

    def list_sessions(self, org_id: str) -> List[Session]:
        ...

    def delete_session(self, session_id: str) -> bool:
        ...
```

### 4. Session 路由器

创建 `api/routers/sessions.py`:

```python
router = APIRouter()
session_service = SessionService()

class SendInputRequest(BaseModel):
    message: str
    node_id: Optional[str] = None  # 指定发送到哪个节点

class SessionResponse(BaseModel):
    session_id: str
    status: SessionStatus
    message: str  # Agent 的响应
    current_node_id: Optional[str]
    next_actions: List[str]  # 可用的下一步操作

@router.get("/{session_id}", response_model=Session)
async def get_session(session_id: str):
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.post("/{session_id}/input", response_model=SessionResponse)
async def send_input(session_id: str, request: SendInputRequest):
    """
    发送用户输入到 session:
    1. 获取 session
    2. 确定目标节点（默认是当前等待输入的节点）
    3. 构建发送给 Agent 的完整 prompt:
       - Agent 的 SOUL.md + IDENTITY.md
       - 当前上下文
       - 用户输入
    4. 执行 Agent（模拟或实际调用 OpenClaw）
    5. 更新 session 状态
    6. 根据数据流触发下一个节点
    7. 返回响应
    """

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_session(session_id: str):
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.status = SessionStatus.CANCELLED
    session_service.update_session(session)

@router.get("/organization/{org_id}", response_model=List[Session])
async def list_org_sessions(org_id: str):
    return session_service.list_sessions(org_id)
```

### 5. Agent 执行逻辑

```python
async def execute_agent(session: Session, node_id: str, user_input: str) -> dict:
    """
    执行 Agent 的逻辑:
    1. 获取节点对应的角色
    2. 构建 prompt:
       - 读取 SOUL.md 内容
       - 读取 IDENTITY.md 内容
       - 读取 memory/context.md
       - 注入相关知识 (rag_service)
       - 注入 session context
       - 添加用户输入
    3. 模拟 Agent 执行（当前版本）
       - 实际版本会调用 OpenClaw Agent
    4. 返回 Agent 输出
    """

def build_agent_prompt(role_id: str, context: dict, user_input: str) -> str:
    """构建发送给 Agent 的完整 prompt"""
    role = role_storage.get(role_id)

    prompt_parts = []

    # 添加 Identity
    if role.identity_template:
        prompt_parts.append(f"## Identity\n{role.identity_template}")
    else:
        prompt_parts.append(f"## Identity\n- Name: {role.name}\n- Role: {role.description}")

    # 添加 Soul
    if role.soul_template:
        prompt_parts.append(f"\n## Soul\n{role.soul_template}")

    # 添加 Context
    if role.context_memory:
        prompt_parts.append(f"\n## Context Memory\n{role.context_memory}")

    # 添加 Session Context
    if context:
        prompt_parts.append(f"\n## Current Context\n{format_context(context)}")

    # 添加用户输入
    prompt_parts.append(f"\n## User Input\n{user_input}")

    # 添加指令
    prompt_parts.append("\n\nPlease respond to the user's input based on your role and context.")

    return "\n".join(prompt_parts)
```

### 6. Session 状态流转

```
用户发起 start
    │
    ▼
┌─────────────────────────────────────┐
│ 创建 Session                         │
│ status: RUNNING                     │
│ current_node: input_role_id          │
└─────────────────────────────────────┘
    │
    ▼
用户发送消息
    │
    ▼
┌─────────────────────────────────────┐
│ execute_agent()                      │
│ - 构建 prompt                        │
│ - 注入 soul, identity, memory        │
│ - 注入 knowledge                     │
│ - 执行 Agent                        │
└─────────────────────────────────────┘
    │
    ├── 成功 ──► 更新 context
    │              │
    │              ▼
    │         根据数据流边
    │         确定下一个节点
    │              │
    │              ▼
    │         current_node = next_node
    │
    └── 失败 ──► status = FAILED
                    │
                    ▼
               返回错误信息
```

### 7. 数据流触发

```python
def get_next_nodes(dataflow: DataFlow, current_node_id: str, context: dict) -> List[str]:
    """
    获取下一个应该触发的节点:
    1. 获取所有以 current_node_id 为源节点的边
    2. 检查边的 condition（如果有）
    3. 返回满足条件的边指向的节点
    """
    next_nodes = []
    for edge in dataflow.edges:
        if edge.source == current_node_id:
            if edge.condition:
                # 评估条件
                if evaluate_condition(edge.condition, context):
                    next_nodes.append(edge.target)
            else:
                next_nodes.append(edge.target)
    return next_nodes
```

## 文件结构

```
api/
├── models/
│   └── session.py      # 新增: Session 模型
├── routers/
│   ├── sessions.py     # 新增: Session 端点
│   └── organizations.py # 修改: 增强 start 端点
├── services/
│   └── session_service.py  # 新增: Session 存储服务
└── main.py            # 修改: 注册新 router
```

## 前端集成

### 创建前端 API

`web/src/services/sessionApi.ts`:

```typescript
export interface SessionResponse {
  session_id: string;
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  message: string;
  current_node_id?: string;
  next_actions: string[];
}

export const sessionApi = {
  get: (sessionId: string) =>
    api.get<Session>(`/sessions/${sessionId}`),

  sendInput: (sessionId: string, message: string, nodeId?: string) =>
    api.post<SessionResponse>(`/sessions/${sessionId}/input`, { message, node_id: nodeId }),

  cancel: (sessionId: string) =>
    api.delete(`/sessions/${sessionId}`),

  listByOrg: (orgId: string) =>
    api.get<Session[]>(`/sessions/organization/${orgId}`),
};
```

### 创建 Session Console 页面

`web/src/pages/SessionConsole.tsx`:

```typescript
interface SessionConsoleProps {
  sessionId: string;
  onClose: () => void;
}

// 功能:
// - 显示当前 Session 状态
// - 显示消息历史
// - 输入框发送消息
// - 显示当前节点和数据流进度
// - 取消 Session 按钮
```

### 修改 Dashboard 添加启动按钮

在 Dashboard 中:
- 选择组织后，点击"开启"按钮
- 弹出输入 initial_prompt 的对话框
- 创建 Session
- 跳转到 SessionConsole 页面

## 注意事项

1. **Session 持久化**: Session 存储在 `data/sessions/{session_id}.json`
2. **多轮对话**: 支持用户多次发送消息
3. **上下文累积**: 每次输入后更新 context
4. **Agent 调用**: 当前版本模拟 Agent 响应，后续可集成 OpenClaw
5. **错误恢复**: Session 失败后可以重试或取消

## 验收标准

- [ ] POST /api/v1/organizations/{org_id}/start 接受 initial_prompt
- [ ] Session 被创建并持久化
- [ ] GET /api/v1/sessions/{session_id} 返回 Session 详情
- [ ] POST /api/v1/sessions/{session_id}/input 发送消息
- [ ] Agent prompt 包含 soul, identity, memory, knowledge
- [ ] 前端有 SessionConsole 页面
- [ ] 支持多轮对话
