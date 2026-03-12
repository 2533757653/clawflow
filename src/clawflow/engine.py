"""
核心编排引擎

WorkflowEngine 负责：
- 解析 YAML 配置
- 管理状态机流转
- 调度 Agent 执行
- 处理条件判断
"""

import yaml
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field

from .agents import Agent, Router, Planner, Reviewer, Orchestrator, Worker, Monitor
from .workflow import Workflow, Step


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


class WorkflowEngine:
    """工作流编排引擎"""
    
    AGENT_TYPES = {
        "Router": Router,
        "Planner": Planner,
        "Reviewer": Reviewer,
        "Orchestrator": Orchestrator,
        "Worker": Worker,
        "Monitor": Monitor,
    }
    
    def __init__(self, config_path: str | Path):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.agents = self._init_agents()
        self.workflow = self._init_workflow()
        self.context = ExecutionContext()
    
    def _load_config(self) -> dict:
        """加载 YAML 配置"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _init_agents(self) -> dict[str, Agent]:
        """初始化所有 Agent 实例"""
        agents = {}
        for agent_id, agent_def in self.config.get('agents', {}).items():
            agent_type = agent_def.get('type', 'Worker')
            agent_class = self.AGENT_TYPES.get(agent_type, Worker)
            agents[agent_id] = agent_class(
                agent_id=agent_id,
                definition=agent_def,
                engine=self,
            )
        return agents
    
    def _init_workflow(self) -> Workflow:
        """初始化工作流"""
        wf_def = self.config.get('workflow', {})
        return Workflow(
            entry=wf_def.get('entry', 'router'),
            steps=[Step(**s) for s in wf_def.get('steps', [])],
            background_services=wf_def.get('background_services', []),
        )
    
    def run(self, user_input: Any) -> Any:
        """执行工作流"""
        self.context.user_input = user_input
        current = self.workflow.entry
        
        max_iterations = 100  # 防止无限循环
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            if current not in self.agents:
                raise ValueError(f"Unknown agent: {current}")
            
            agent = self.agents[current]
            result = agent.execute(self.context)
            
            # 评估条件，决定下一步
            next_step = self.workflow.evaluate(current, result, self.context)
            
            if next_step is None or next_step == "END":
                return result
            
            current = next_step
        
        raise RuntimeError("Workflow exceeded maximum iterations")
    
    def get_agent(self, agent_id: str) -> Agent:
        """获取指定 Agent"""
        return self.agents.get(agent_id)
    
    def update_state(self, key: str, value: Any) -> None:
        """更新全局状态"""
        self.context.set(key, value)
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """获取全局状态"""
        return self.context.get(key, default)
