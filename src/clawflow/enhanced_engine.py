"""
增强工作流引擎

支持 Actor-Critic 模式的集成工作流引擎
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field

# 导入内置的 Actor-Critic 引擎
from .actor_critic_engine import ActorCriticEngine


@dataclass
class ExecutionContext:
    """执行上下文，存储任务状态和中间结果"""
    current_agent: str = ""
    user_input: Any = None
    task_plan: Optional[dict] = None
    review_result: Optional[dict] = None
    execution_results: list = field(default_factory=list)
    variables: dict = field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.variables.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        self.variables[key] = value


class EnhancedWorkflowEngine:
    """增强工作流引擎 - 支持内置 Actor-Critic 模式"""
    
    def __init__(self, config_path: str = "../examples/claw.yaml"):
        self.config_path = Path(config_path)
        self.context = ExecutionContext()
        self.actor_critic_engine = ActorCriticEngine()
    
    def execute_workflow(self, user_input: str) -> Dict[str, Any]:
        """
        执行完整工作流，支持内置 Actor-Critic 模式
        """
        print(f"🚀 启动增强工作流: {user_input[:50]}...")
        
        # 检查是否是自更新请求
        if 'update' in user_input.lower() or '自更新' in user_input or 'self-update' in user_input:
            return self._execute_self_update_workflow(user_input)
        else:
            return self._execute_standard_workflow(user_input)
    
    def _execute_self_update_workflow(self, user_input: str) -> Dict[str, Any]:
        """
        执行自更新工作流（内置 Actor-Critic 模式）
        """
        print("🔄 检测到自更新请求，启用内置 Actor-Critic 模式")
        
        # 执行内置的自更新周期（最多3轮后暂停）
        actor_critic_result = self.actor_critic_engine.execute_self_update_cycle()
        
        # 构建结果
        result = {
            "status": "completed_with_pause",
            "input": user_input,
            "workflow_type": "self_update_actor_critic_builtin",
            "actor_critic_result": actor_critic_result,
            "summary": f"内置 Actor-Critic 自更新完成: {actor_critic_result['summary']}"
        }
        
        return result
    
    def _execute_standard_workflow(self, user_input: str) -> Dict[str, Any]:
        """
        执行标准工作流
        """
        from ..openclaw_integration import OpenClawWorkflowExecutor
        executor = OpenClawWorkflowExecutor()
        return executor.execute_workflow(user_input)
    
    def run_router(self, user_input: str) -> Dict[str, Any]:
        """运行路由 Agent"""
        from ..openclaw_integration import OpenClawWorkflowExecutor
        executor = OpenClawWorkflowExecutor()
        return executor.execute_router(user_input)
    
    def run_planner(self, requirement: str) -> Dict[str, Any]:
        """运行规划 Agent"""
        from ..openclaw_integration import OpenClawWorkflowExecutor
        executor = OpenClawWorkflowExecutor()
        return executor.execute_planner(requirement)
    
    def run_reviewer(self, task_plan: Dict[str, Any]) -> Dict[str, Any]:
        """运行审核 Agent"""
        from ..openclaw_integration import OpenClawWorkflowExecutor
        executor = OpenClawWorkflowExecutor()
        return executor.execute_reviewer(task_plan)
    
    def run_orchestrator(self, approved_tasks: Dict[str, Any]) -> Dict[str, Any]:
        """运行调度 Agent"""
        from ..openclaw_integration import OpenClawWorkflowExecutor
        executor = OpenClawWorkflowExecutor()
        return executor.execute_orchestrator(approved_tasks)
    
    def run_worker(self, task_type: str, task: dict) -> Dict[str, Any]:
        """运行工作 Agent"""
        from ..openclaw_integration import OpenClawWorkflowExecutor
        executor = OpenClawWorkflowExecutor()
        return executor._execute_task(task_type, task)


class AgentProxy:
    """
    Agent 代理 - 用于与 OpenClaw 原生 Agent 系统交互
    """
    
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.engine = EnhancedWorkflowEngine()
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Agent 任务"""
        if self.agent_type == "Router":
            return self.engine.run_router(input_data.get("user_input", ""))
        elif self.agent_type == "Planner":
            return self.engine.run_planner(input_data.get("requirement", ""))
        elif self.agent_type == "Reviewer":
            return self.engine.run_reviewer(input_data.get("task_plan", {}))
        elif self.agent_type == "Orchestrator":
            return self.engine.run_orchestrator(input_data.get("approved_tasks", {}))
        elif self.agent_type in ["DataWorker", "CodeWorker", "DocWorker"]:
            task_type = self.agent_type.replace("Worker", "").lower()
            return self.engine.run_worker(task_type, input_data.get("task", {}))
        else:
            return {"error": f"Unknown agent type: {self.agent_type}", "status": "error"}


def create_agent(agent_type: str) -> AgentProxy:
    """工厂函数：创建 Agent 代理"""
    return AgentProxy(agent_type)