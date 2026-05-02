# Prompt: 工作流执行引擎

## 项目信息

- **项目名称**: ClawFlow - Agent 组织动态构建平台
- **项目路径**: `d:\clawflow`
- **后端**: `api/` (FastAPI + Python 3.11+)
- **前端**: `web/` (React 18 + TypeScript)
- **数据存储**: JSON 文件 (开发模式)

## 项目架构

```
clawflow/
├── api/
│   ├── main.py              # FastAPI 入口
│   ├── routers/             # API 路由
│   │   ├── organizations.py # 组织管理
│   │   ├── roles.py         # 角色管理 (全局)
│   │   ├── tasks.py         # 任务管理
│   │   ├── dataflows.py     # 数据流管理
│   │   ├── knowledge.py     # 知识库
│   │   ├── skills.py        # 技能管理
│   │   ├── memory.py        # 记忆管理
│   │   ├── rag.py           # RAG 查询
│   │   └── agency.py        # agency-agents 导入
│   ├── models/
│   │   ├── __init__.py      # 核心模型
│   │   └── rag_models.py    # RAG 模型
│   └── services/
│       ├── storage.py        # JSON 存储服务
│       ├── openclaw_adapter.py # OpenClaw 部署适配器
│       └── rag_service.py    # RAG 服务
├── web/
│   └── src/
│       ├── pages/           # React 页面组件
│       ├── stores/          # Zustand 状态管理
│       ├── services/api.ts  # 前端 API 调用
│       └── types/index.ts   # TypeScript 类型定义
└── agents/                  # OpenClaw Agent 目录
```

## 核心模型定义

### Organization (组织)
```python
class Organization(BaseModel):
    id: str
    name: str
    description: Optional[str]
    logo: Optional[str]
    status: OrganizationStatus  # draft, deployed, running, stopped
    initial_prompt: Optional[str]
    input_role_id: Optional[str]  # 接收外部输入的角色
    role_ids: List[str]  # 组织包含的角色列表
    layout: List[OrgComponent]
    created_at: datetime
    updated_at: datetime
```

### Role (角色)
```python
class Role(BaseModel):
    id: str
    name: str
    description: Optional[str]
    responsibilities: List[str]  # 职责列表
    required_skills: List[str]
    reports_to: Optional[str]  # 汇报对象
    permission_level: PermissionLevel  # admin, manager, member, readonly
    hierarchy_level: int  # 1-4
    soul_template: Optional[str]  # SOUL.md 模板
    identity_template: Optional[str]  # IDENTITY.md 模板
    context_memory: Optional[str]
    division: Optional[str]  # 部门
    source: Optional[str]  # manual 或 agency-agents
```

### Task (任务)
```python
class Task(BaseModel):
    id: str
    organization_id: str
    name: str
    description: Optional[str]
    prompt: Optional[str]  # 任务执行的 prompt
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    assigned_role_id: Optional[str]  # 负责的角色
    dependencies: List[str]  # 依赖的任务
    priority: Priority  # high, medium, low
    execution_mode: ExecutionMode  # sequential, parallel, conditional
    conditions: Dict[str, Any]
```

### DataFlow (数据流)
```python
class DataFlowNode(BaseModel):
    id: str
    type: NodeType  # role, task, knowledge, input, output
    ref_id: Optional[str]  # 关联的实体 ID
    position: Dict[str, float]  # x, y 坐标
    label: Optional[str]

class DataFlowEdge(BaseModel):
    id: str
    source: str  # 源节点 ID
    target: str  # 目标节点 ID
    data_mapping: Dict[str, Any]  # 数据映射
    condition: Optional[str]  # 条件

class DataFlow(BaseModel):
    id: str
    organization_id: str
    name: str
    description: Optional[str]
    nodes: List[DataFlowNode]
    edges: List[DataFlowEdge]
```

## 设计决策

根据 SPEC.md "设计决策记录"：

### 核心概念

1. **角色 = Agent**: 每个角色是独立的 OpenClaw Agent
2. **角色全局唯一**: 存储在 `data/roles/`，组织通过 `role_ids` 引用
3. **数据流 + 任务 = 工作流**:
   - 数据流: 定义 Agent 之间数据传递的通道
   - 任务: 基于数据流，添加 prompt，将数据流转换为工作流
4. **输入角色**: Organization.input_role_id 指定接收外部输入的角色

### 存储分离

| 内容 | 存储位置 |
|------|----------|
| Agent 定义 | OpenClaw (`agents/` 目录) |
| 数据流 | 本地 (`data/organizations/{org_id}/dataflows`) |
| 任务 | 本地 (`data/organizations/{org_id}/tasks`) |
| 知识库 | 本地 (`data/organizations/{org_id}/knowledge`) |
| 组织配置 | 本地 (`data/organizations`) |
| 上下文记忆 | 本地 (`data/memory/`) |

## 已有实现

### OpenClawAdapter (已实现)
位置: `api/services/openclaw_adapter.py`

```python
class OpenClawAdapter:
    def deploy_role(self, role: Role, skills: List[str]) -> str:
        # 创建 agents/{role_name}/
        # 生成 SOUL.md, IDENTITY.md, AGENTS.md, BOOTSTRAP.md, HEARTBEAT.md, USER.md
        # 复制技能到 skills/
```

### Memory Service (已实现)
位置: `api/routers/memory.py`

```python
# 已有的端点:
GET  /api/v1/memory/{role_id}                    # 获取记忆
POST /api/v1/memory/{role_id}                    # 添加记忆
POST /api/v1/memory/{role_id}/access/{memory_id} # 访问记忆
POST /api/v1/memory/compress                      # 压缩记忆
POST /api/v1/memory/enhance-prompt               # 增强 prompt
POST /api/v1/memory/{role_id}/sync               # 同步到 OpenClaw
```

### RAG Service (已实现)
位置: `api/routers/rag.py`

```python
# 已有的端点:
POST /api/v1/rag/query                    # RAG 查询
POST /api/v1/rag/index/knowledge-base/{org_id}  # 索引知识库
GET  /api/v1/rag/stats                    # RAG 统计
```

## 任务要求

### 1. 创建执行服务

创建 `api/services/execution_service.py`:

```python
class ExecutionService:
    def __init__(self):
        self.storage = StorageService()

    def execute_workflow(
        self,
        organization_id: str,
        input_data: dict,
        dataflow_id: Optional[str] = None,
        input_role_id: Optional[str] = None
    ) -> ExecutionResult:
        """
        执行工作流的逻辑:
        1. 加载组织和数据流
        2. 确定起始节点（input 节点或 input_role）
        3. 按拓扑顺序执行节点
        4. 对每个角色节点:
           - 加载角色定义
           - 加载分配的任务
           - 注入知识库上下文
           - 执行 prompt
        5. 根据边和数据映射传递数据
        6. 返回执行结果
        """
```

### 2. 创建执行路由器

创建 `api/routers/execution.py`:

```python
@router.post("/organizations/{org_id}/execute")
async def execute_workflow(
    org_id: str,
    request: ExecuteRequest
):
    """
    请求体:
    {
        "input_data": {"user_input": "..."},
        "dataflow_id": "可选",
        "input_role_id": "可选"
    }

    响应:
    {
        "execution_id": "uuid",
        "status": "completed|failed|partial",
        "node_results": [...],
        "final_output": {...}
    }
    """
```

### 3. 数据模型

```python
class ExecuteRequest(BaseModel):
    input_data: Dict[str, Any]
    dataflow_id: Optional[str] = None
    input_role_id: Optional[str] = None

class NodeResult(BaseModel):
    node_id: str
    role_id: Optional[str]
    output: Dict[str, Any]
    error: Optional[str]
    execution_time_ms: int

class ExecutionResult(BaseModel):
    execution_id: str
    status: str
    node_results: List[NodeResult]
    final_output: Dict[str, Any]
```

### 4. 执行逻辑细节

```
用户输入 (input_data)
    │
    ▼
┌─────────────────────┐
│  加载数据流          │
│  验证节点和边        │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│  找到起始节点        │
│  (input 节点或       │
│   input_role)       │
└─────────────────────┘
    │
    ▼
遍历节点 (按拓扑顺序):
    │
    ├─── 角色节点 ────
    │    ├── 加载角色 (role_storage.get(ref_id))
    │    ├── 加载任务 (tasks.filter(assigned_role_id == role_id))
    │    ├── 注入知识库 (rag_service.query)
    │    ├── 注入记忆 (memory_api.enhance_prompt)
    │    ├── 构建执行 prompt
    │    └── 模拟执行 (实际调用 OpenClaw 或 mock)
    │
    ├─── 任务节点 ────
    │    ├── 加载任务定义
    │    └── 执行任务 prompt
    │
    ├─── 知识节点 ────
    │    └── 返回知识内容
    │
    └─── 输出节点 ────
         └── 收集输出
    │
    ▼
根据边传递数据 (data_mapping)
    │
    ▼
返回 ExecutionResult
```

### 5. 拓扑排序实现

```python
def topological_sort(nodes: List[DataFlowNode], edges: List[DataFlowEdge]) -> List[str]:
    """返回节点 ID 的执行顺序"""
    # 构建邻接表和入度表
    # Kahn 算法或 DFS
    # 处理循环引用情况
```

### 6. 数据映射

边的 `data_mapping` 定义如何传递数据:

```json
{
  "source": "node_A",
  "target": "node_B",
  "data_mapping": {
    "user_query": "{{source.output.user_query}}",
    "summary": "{{source.output.summary}}"
  }
}
```

实现数据替换:
```python
def apply_data_mapping(mapping: dict, source_output: dict) -> dict:
    result = {}
    for target_key, source_expr in mapping.items():
        # 解析 {{source.output.xxx}} 格式
        # 从 source_output 提取值
        result[target_key] = extract_value(source_expr, source_output)
    return result
```

### 7. 知识库注入

```python
def inject_knowledge(rag_service: RAGService, org_id: str, context: dict) -> str:
    """基于当前上下文注入相关知识"""
    query = context.get("user_input", "")
    result = rag_service.query(RAGQuery(
        query=query,
        organization_id=org_id,
        top_k=3
    ))
    # 返回格式化的知识上下文
    return format_knowledge_context(result)
```

## 文件结构

```
api/
├── routers/
│   └── execution.py      # 新增: 执行端点
├── services/
│   └── execution_service.py  # 新增: 执行逻辑
└── main.py               # 修改: 注册 router
```

## 前端集成

### 创建前端 API

`web/src/services/executionApi.ts`:

```typescript
export const executionApi = {
  execute: (orgId: string, request: ExecuteRequest) =>
    api.post<ExecutionResult>(`/organizations/${orgId}/execute`, request),
};
```

### 创建执行结果页面

`web/src/pages/ExecutionResult.tsx`:

- 显示执行状态
- 节点执行结果列表
- 输出可视化
- 错误信息展示

## 注意事项

1. **错误处理**: 节点执行失败时，根据 execution_mode 决定是继续还是停止
2. **循环引用检测**: 拓扑排序时检测循环，返回错误
3. **模拟执行**: 当前版本可以模拟执行结果，后续可集成真正的 OpenClaw 调用
4. **日志记录**: 记录每个节点的执行时间和输入输出
5. **状态码**: 使用 FastAPI 标准状态码

## 验收标准

- [ ] POST /api/v1/organizations/{org_id}/execute 端点可调用
- [ ] 执行结果包含 node_results 和 final_output
- [ ] 按拓扑顺序执行节点
- [ ] 数据映射正确传递数据
- [ ] 知识库上下文被注入
- [ ] 前端可以发起执行并显示结果
