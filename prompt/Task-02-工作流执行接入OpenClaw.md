# Task-02: 工作流执行服务接入真实OpenClaw

## 项目背景

**项目**: ClawFlow - Agent组织动态构建平台
**当前问题**: `api/services/execution_service.py` 中的 `_simulate_agent_execution` 只是返回假数据，工作流执行是纯模拟
**修改目标**: 实现真实调用OpenClaw Agent执行工作流节点

## 输入输出要求

### 输入
- 工作流执行请求（已存在）
- 角色定义（从 `data/roles/` 读取）
- 任务定义（从 `data/organizations/{org_id}/tasks/` 读取）

### 输出
- 真实Agent执行结果
- 执行日志/状态
- 错误捕获和传播

## 约束条件

1. **OpenClaw集成方式**: 通过文件系统适配器（已存在的 `OpenClawAdapter` 模式）
2. **执行模式**: 支持同步和异步（考虑未来扩展）
3. **错误隔离**: 单个节点失败不影响其他节点执行
4. **日志记录**: 记录每个节点的输入输出
5. **超时控制**: 每个角色执行超时时间可配置（默认60秒）

## 技术实现要求

### 1. 理解现有架构

**关键文件**:
- `api/services/execution_service.py` - 执行引擎
- `api/services/openclaw_adapter.py` - OpenClaw适配器
- `api/models/__init__.py` - 数据模型

**现有执行流程**:
```
execute_workflow()
  → topological_sort()  # 拓扑排序确定执行顺序
  → 遍历节点执行
    → _execute_input_node()
    → _execute_role_node()     # 调用角色
    → _execute_task_node()     # 调用任务
    → _execute_knowledge_node()
    → _execute_output_node()
```

### 2. 设计OpenClaw执行接口

**新增文件**: `api/services/openclaw_executor.py`

```python
import os
import subprocess
import json
import time
from typing import Dict, Any, Optional

class OpenClawExecutor:
    """真实执行OpenClaw Agent"""

    def __init__(self, agents_base_path: str = "agents", timeout: int = 60):
        self.agents_base_path = agents_base_path
        self.timeout = timeout

    def execute_role(
        self,
        role_name: str,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行单个角色"""
        agent_path = os.path.join(
            self.agents_base_path,
            role_name.lower().replace(" ", "_")
        )

        if not os.path.exists(agent_path):
            raise FileNotFoundError(f"Agent not deployed: {agent_path}")

        # 构建执行上下文
        exec_input = {
            "task": input_data.get("task", "process request"),
            "context": context or {},
            "timestamp": time.time()
        }

        # 写入输入文件供Agent读取
        input_path = os.path.join(agent_path, "memory", "input.json")
        os.makedirs(os.path.dirname(input_path), exist_ok=True)
        with open(input_path, 'w', encoding='utf-8') as f:
            json.dump(exec_input, f, ensure_ascii=False)

        # 调用OpenClaw CLI执行
        try:
            result = self._call_openclaw(agent_path, input_data)
            return self._parse_output(agent_path, result)
        except subprocess.TimeoutExpired:
            return {"error": "Execution timeout", "role": role_name}
        except Exception as e:
            return {"error": str(e), "role": role_name}

    def _call_openclaw(self, agent_path: str, input_data: Dict[str, Any]) -> str:
        """调用OpenClaw CLI"""
        # 尝试多种OpenClaw调用方式
        cmd = self._build_openclaw_command(agent_path, input_data)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self.timeout,
            cwd=agent_path
        )

        if result.returncode != 0:
            raise RuntimeError(f"OpenClaw execution failed: {result.stderr}")

        return result.stdout

    def _build_openclaw_command(self, agent_path: str, input_data: Dict[str, Any]) -> list:
        """构建OpenClaw命令"""
        # 方式1: 直接调用Python（如果OpenClaw是Python包）
        return ["python", "-m", "openclaw", "--agent", agent_path, "--input", json.dumps(input_data)]
```

### 3. 重构ExecutionService

**修改文件**: `api/services/execution_service.py`

```python
from api.services.openclaw_executor import OpenClawExecutor

class ExecutionService:
    def __init__(self):
        self.storage = StorageService[Organization]("data/organizations", Organization)
        self.role_storage = StorageService[Role]("data/roles", Role)
        self.rag_service = RAGService()
        # 新增真实执行器
        self.executor = OpenClawExecutor()

    def _execute_role_node(self, ...):
        # ... 现有代码 ...

        # 替换模拟执行
        # 旧: simulated_output = self._simulate_agent_execution(...)
        # 新:
        try:
            result = self.executor.execute_role(
                role_name=role.name,
                input_data=input_mapping,
                context={"org_id": org.id, "tasks": role_tasks}
            )
            output = result
        except Exception as e:
            output = {"error": str(e), "role_name": role.name}

        return {
            "role_id": role.id,
            "role_name": role.name,
            "output": output,
            "tasks_executed": [t.id for t in role_tasks],
            "node_label": node.label
        }

    # 删除或注释掉 _simulate_agent_execution 方法
    # def _simulate_agent_execution(...):
    #     """已废弃 - 使用 OpenClawExecutor 替代"""
    #     pass
```

### 4. 部署检查

在执行前验证Agent已部署:
```python
def _execute_role_node(self, ...):
    if not node.ref_id:
        return {"error": "Role node has no ref_id"}

    role = self.role_storage.get(node.ref_id)
    if not role:
        return {"error": f"Role not found: {node.ref_id}"}

    # 新增: 检查Agent是否已部署
    agent_path = os.path.join("agents", role.name.lower().replace(" ", "_"))
    if not os.path.exists(agent_path):
        return {
            "error": f"Agent not deployed. Please deploy organization first.",
            "role_id": role.id,
            "role_name": role.name
        }
    # ... 继续执行
```

## 验收标准

1. ✅ 部署后的组织执行时真实调用OpenClaw Agent
2. ✅ Agent执行结果正确返回并显示在前端
3. ✅ 执行超时能正确处理（不挂起）
4. ✅ Agent未部署时给出明确错误提示
5. ✅ 单节点失败不影响其他节点
6. ✅ 节点执行时间被正确记录

## 依赖关系

- **前置依赖**: Task-01（RAG向量生成）
- **可并行**: Task-03（前端状态）、Task-04（Agent同步）

## 注意事项

1. 当前OpenClaw的实际调用方式需要根据实际部署环境调整
2. 如果OpenClaw CLI不存在，应返回明确错误而非崩溃
3. 建议添加 `OPENCLAW_ENABLED` 环境变量控制是否启用真实执行
4. 执行结果应包含足够调试信息
