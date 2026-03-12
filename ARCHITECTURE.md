# ClawFlow 架构文档

## 核心理念

**消息驱动 + 自举创建 + 独立服务**

ClawFlow 不是一个库，而是一个**运行在 OpenClaw 之上的多智能体操作系统**。

## 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户 (OpenClaw 会话)                       │
│                              ↓                                    │
│                    ┌──────────────────┐                          │
│                    │  clawflow-skill  │ ← OpenClaw Skill (入口)   │
│                    └────────┬─────────┘                          │
└─────────────────────────────┼────────────────────────────────────┘
                              │ HTTP/WebSocket
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    ClawFlow 独立服务                             │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Message Bus (消息总线)                  │  │
│  │  - 异步通信：Agent 之间不直接调用，通过消息传递            │  │
│  │  - 队列管理：每个 Agent 有独立邮箱 (inbox)                 │  │
│  │  - 持久化：消息可持久化到磁盘/Redis                        │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    自举创建流程                            │  │
│  │                                                            │  │
│  │   ┌─────────────┐                                         │  │
│  │   │ Meta-Agent  │ ← 第一个被创建的 Agent                   │  │
│  │   │ (创建者)    │    职责：创建和管理其他 Agent             │  │
│  │   └──────┬──────┘                                         │  │
│  │          │ create_agent()                                  │  │
│  │          ↓                                                 │  │
│  │   ┌─────────────┐                                         │  │
│  │   │ Worker-     │ ← Meta-Agent 创建                        │  │
│  │   │ Builder     │    职责：根据模板生成各类 Worker          │  │
│  │   └──────┬──────┘                                         │  │
│  │          │ build_worker()                                  │  │
│  │          ↓                                                 │  │
│  │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │  │
│  │   │ data_worker │  │ code_worker │  │ doc_worker  │  ...  │  │
│  │   └─────────────┘  └─────────────┘  └─────────────┘       │  │
│  │                                                            │  │
│  │   同时创建核心工作流 Agents:                                │  │
│  │   router → planner → reviewer → orchestrator               │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    HTTP API 服务                           │  │
│  │  - POST /run          运行工作流                           │  │
│  │  - GET  /status       查看服务状态                         │  │
│  │  - GET  /agents       列出所有 Agent                       │  │
│  │  - POST /agents/create  动态创建 Agent                     │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. Message Bus (消息总线)

**职责**：Agent 之间的通信基础设施

```python
# 发送消息
message_bus.send("agent:code_worker:inbox", Message(
    type="task",
    from_agent="orchestrator",
    to_agent="code_worker",
    payload={"task": "实现数据分析功能"},
))

# 接收消息
message = message_bus.receive("agent:code_worker:inbox", timeout=30)

# 请求 - 响应模式（同步）
response = message_bus.request("agent:planner:inbox", {
    "requirement": "创建量化策略"
}, timeout=60)
```

**实现选项**：
- MVP: 内存队列 (`queue.Queue`)
- 生产：Redis Pub/Sub 或 RabbitMQ

### 2. Meta-Agent (元 Agent)

**职责**：创建、管理、销毁其他 Agent

```python
# 创建新 Agent
meta_agent.send("meta_agent", {
    "type": "create_agent",
    "id": "my_agent",
    "agent_type": "Worker",
    "capabilities": ["exec", "web_search"],
})

# 列出所有 Agent
meta_agent.send("meta_agent", {"type": "list_agents"})

# 销毁 Agent
meta_agent.send("meta_agent", {
    "type": "destroy_agent",
    "agent_id": "my_agent",
})
```

### 3. Worker-Builder Agent

**职责**：根据预定义模板生成 Worker Agent

```python
# 构建 data_worker
worker_builder.send("worker_builder", {
    "type": "build_worker",
    "worker_type": "data",
})

# 内部流程：
# 1. 查找 data_worker 模板
# 2. 调用 meta_agent.create_agent()
# 3. 返回创建的 Agent ID
```

### 4. 工作流 Agents

| Agent | 职责 | 消息处理 |
|-------|------|----------|
| `router` | 入口路由，过滤需求 | 接收用户输入 → 判断是否有效 → 转发给 planner |
| `planner` | 任务规划与拆解 | 接收需求 → 拆解为子任务 → 发送给 reviewer |
| `reviewer` | 方案审核 | 接收计划 → 评估可行性 → 通过/打回 |
| `orchestrator` | 任务调度 | 接收通过的计划 → 分发到 Workers → 汇总结果 |

## 自举流程

```
启动 ClawFlow 服务
    ↓
[1] 创建 Meta-Agent
    - agent_id: "meta_agent"
    - 能力：create_agent, list_agents, destroy_agent
    ↓
[2] 创建 Worker-Builder Agent
    - agent_id: "worker_builder"
    - 能力：build_worker
    - 加载 Worker 模板
    ↓
[3] Worker-Builder 创建 Workers
    - data_worker (数据处理)
    - code_worker (代码实现)
    - doc_worker (文档生成)
    - review_worker (质量审查)
    ↓
[4] 创建工作流核心 Agents
    - router (入口)
    - planner (规划)
    - reviewer (审核)
    - orchestrator (调度)
    ↓
✅ 系统就绪，开始处理用户请求
```

## 消息格式

```python
@dataclass
class Message:
    id: str                    # 消息唯一 ID
    type: str                  # task | response | control | event
    from_agent: str            # 发送者 ID
    to_agent: str              # 接收者 ID
    payload: Dict[str, Any]    # 消息内容
    reply_to: Optional[str]    # 回复目标（可选）
    correlation_id: Optional[str]  # 关联 ID（请求 - 响应配对）
    timestamp: str             # 时间戳
    priority: int              # 优先级
```

## 与 OpenClaw 的集成

### clawflow-skill (OpenClaw 入口)

```markdown
# 安装
clawhub install clawflow

# 使用
clawflow run "创建一个数据分析功能"
```

### 内部实现

```python
# clawflow-skill/SKILL.md
def run_workflow(user_input):
    # 1. 转发到 ClawFlow 服务
    response = requests.post(
        "http://localhost:8765/run",
        json={"input": user_input}
    )
    
    # 2. 轮询结果（或 WebSocket 订阅）
    workflow_id = response.json()["workflow_id"]
    while True:
        status = requests.get(f"http://localhost:8765/workflow/{workflow_id}")
        if status.json()["status"] == "completed":
            return status.json()["result"]
        time.sleep(1)
```

## 扩展点

### 1. 自定义 Agent

```bash
curl -X POST http://localhost:8765/agents/create \
  -H "Content-Type: application/json" \
  -d '{
    "id": "quant_analyst",
    "type": "Worker",
    "capabilities": ["exec", "web_fetch"],
    "description": "量化分析 Agent"
  }'
```

### 2. 自定义工作流

在 `workflows/` 目录创建 YAML：

```yaml
name: quant-strategy
entry: router
steps:
  - from: router
    condition: valid_requirement
    to: planner
  - from: planner
    condition: plan_created
    to: reviewer
  - from: reviewer
    condition: approval_passed
    to: orchestrator
```

### 3. 替换消息总线

实现 `MessageBus` 接口：

```python
class RedisMessageBus(MessageBus):
    def __init__(self, redis_url):
        self.redis = redis.from_url(redis_url)
    
    def send(self, to_agent, message):
        self.redis.lpush(f"agent:{to_agent}:inbox", message.json())
    
    def receive(self, agent_id, timeout):
        result = self.redis.brpop(f"agent:{agent_id}:inbox", timeout)
        return Message.parse_raw(result[1]) if result else None
```

## 生产部署建议

| 组件 | MVP | 生产环境 |
|------|-----|----------|
| 消息总线 | 内存队列 | Redis/RabbitMQ |
| 状态存储 | 文件 (JSONL) | PostgreSQL |
| 服务发现 | 硬编码 URL | Consul/Etcd |
| 负载均衡 | 无 | Nginx/HAProxy |
| 监控 | 日志 | Prometheus + Grafana |
| 高可用 | 单实例 | Kubernetes 集群 |

## 安全考虑

1. **消息认证**：Agent 之间通信需要签名验证
2. **权限控制**：Meta-Agent 的创建/销毁操作需要授权
3. **资源限制**：每个 Agent 的 CPU/内存使用需要配额
4. **审计日志**：所有 Agent 操作需要记录日志

## 下一步

- [ ] 实现 Redis 消息总线
- [ ] 添加 WebSocket 支持（实时推送结果）
- [ ] 实现工作流编辑器（Web UI）
- [ ] 添加 Agent 热更新机制
- [ ] 实现分布式部署
