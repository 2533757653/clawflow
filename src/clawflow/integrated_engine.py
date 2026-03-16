"""
集成工作流引擎

直接利用 OpenClaw 原生 Agent 和工具系统的引擎
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field

# 导入 OpenClaw 工具
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from openclaw_integration import OpenClawWorkflowExecutor


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


class IntegratedWorkflowEngine:
    """集成工作流引擎 - 使用 OpenClaw 原生能力"""
    
    def __init__(self, config_path: str = "../examples/claw.yaml"):
        self.config_path = Path(config_path)
        self.executor = OpenClawWorkflowExecutor()
        self.context = ExecutionContext()
    
    def execute_workflow(self, user_input: str) -> Dict[str, Any]:
        """
        执行完整工作流，利用 OpenClaw 原生 Agent
        """
        print(f"🚀 启动集成工作流: {user_input[:50]}...")
        
        # 直接使用 OpenClaw 集成执行器
        result = self.executor.execute_workflow(user_input)
        
        return result
    
    def run_router(self, user_input: str) -> Dict[str, Any]:
        """运行路由 Agent - 使用 OpenClaw 原生能力"""
        return self.executor.execute_router(user_input)
    
    def run_planner(self, requirement: str) -> Dict[str, Any]:
        """运行规划 Agent - 使用 OpenClaw 原生能力"""
        return self.executor.execute_planner(requirement)
    
    def run_reviewer(self, task_plan: Dict[str, Any]) -> Dict[str, Any]:
        """运行审核 Agent - 使用 OpenClaw 原生能力"""
        return self.executor.execute_reviewer(task_plan)
    
    def run_orchestrator(self, approved_tasks: Dict[str, Any]) -> Dict[str, Any]:
        """运行调度 Agent - 使用 OpenClaw 原生能力"""
        return self.executor.execute_orchestrator(approved_tasks)
    
    def run_worker(self, task_type: str, task: dict) -> Dict[str, Any]:
        """运行工作 Agent - 使用 OpenClaw 原生能力"""
        return self.executor._execute_task(task_type, task)


class AgentProxy:
    """
    Agent 代理 - 用于与 OpenClaw 原生 Agent 系统交互
    """
    
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.engine = IntegratedWorkflowEngine()
    
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