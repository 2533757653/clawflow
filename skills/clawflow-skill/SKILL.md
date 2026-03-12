---
name: clawflow
description: "ClawFlow 工作流编排引擎入口：将用户请求转发到独立 ClawFlow 服务，并返回结果"
metadata:
  {
    "openclaw":
      {
        "emoji": "🐙",
        "requires": { "bins": ["curl"] },
        "install": [],
      },
  }
---

# ClawFlow Skill

ClawFlow 是运行在 OpenClaw 之上的多智能体工作流编排引擎。

## 架构

```
OpenClaw 会话 → clawflow-skill → ClawFlow 独立服务 → Agent 网络
```

## 配置

在 `~/.openclaw/config.json` 中添加：

```json
{
  "clawflow": {
    "service_url": "http://localhost:8765",
    "timeout_seconds": 60
  }
}
```

## 使用方式

### 1. 启动 ClawFlow 服务

```bash
cd /path/to/clawflow
python -m clawflow.server --port 8765
```

### 2. 在 OpenClaw 中调用

```bash
# 运行工作流
clawflow run "创建一个数据分析功能"

# 查看状态
clawflow status

# 列出 Agent
clawflow agents
```

### 3. 通过 API 调用

```bash
# 运行工作流
curl -X POST http://localhost:8765/run \
  -H "Content-Type: application/json" \
  -d '{"input": "创建一个数据分析功能"}'

# 查看状态
curl http://localhost:8765/status

# 健康检查
curl http://localhost:8765/health
```

## 消息格式

### 请求

```json
{
  "input": "用户输入",
  "workflow": "optional_workflow_name",
  "options": {
    "parallel": true,
    "timeout": 300
  }
}
```

### 响应

```json
{
  "status": "success|processing|error",
  "workflow_id": "uuid",
  "result": {...},
  "message": "描述信息"
}
```

## 内部 Agent

ClawFlow 内置以下 Agent：

| Agent | 类型 | 职责 |
|-------|------|------|
| `meta_agent` | Meta | 创建和管理其他 Agent |
| `worker_builder` | Builder | 根据模板生成 Worker |
| `router` | Router | 入口路由，过滤需求 |
| `planner` | Planner | 任务规划与拆解 |
| `reviewer` | Reviewer | 方案审核 |
| `orchestrator` | Orchestrator | 任务调度与结果汇总 |
| `data_worker` | Worker | 数据处理 |
| `code_worker` | Worker | 代码实现 |
| `doc_worker` | Worker | 文档生成 |
| `review_worker` | Worker | 质量审查 |

## 自举机制

ClawFlow 启动时自动执行自举流程：

1. 创建 `meta_agent`（元 Agent）
2. 创建 `worker_builder`（Worker 生成器）
3. `worker_builder` 创建各类 Worker Agent
4. 创建工作流核心 Agent（Router, Planner, Orchestrator）

## 扩展

### 创建自定义 Agent

```bash
curl -X POST http://localhost:8765/agents/create \
  -H "Content-Type: application/json" \
  -d '{
    "id": "my_custom_agent",
    "type": "Worker",
    "capabilities": ["exec", "web_search"],
    "description": "我的自定义 Agent"
  }'
```

### 定义工作流

在 `workflows/` 目录下创建 YAML 文件：

```yaml
name: my-workflow
entry: router
steps:
  - from: router
    condition: valid_requirement
    to: planner
  - from: planner
    condition: plan_created
    to: orchestrator
```

## 注意事项

- ClawFlow 服务必须独立运行（不与 OpenClaw 同进程）
- 消息总线默认使用内存队列，生产环境建议用 Redis
- Agent 之间通过消息异步通信，避免阻塞
