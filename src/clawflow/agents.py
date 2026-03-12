"""
Agent 基类与具体实现

每个 Agent 负责特定功能，通过 execute() 方法执行任务
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Agent(ABC):
    """Agent 基类"""
    agent_id: str
    definition: dict
    engine: Any  # WorkflowEngine
    
    @abstractmethod
    def execute(self, context: Any) -> Any:
        """执行 Agent 任务"""
        pass
    
    def get_tools(self) -> list[str]:
        """获取此 Agent 可用的工具列表"""
        return self.definition.get('tools', [])
    
    def get_rules(self) -> list[str]:
        """获取此 Agent 的执行规则"""
        return self.definition.get('rules', [])


class Router(Agent):
    """入口路由器：过滤用户输入，提炼核心需求"""
    
    def execute(self, context: Any) -> Any:
        user_input = context.user_input
        
        # 过滤无效内容
        if not user_input or len(str(user_input).strip()) < 2:
            return {"filtered_intent": None, "reason": "无效输入"}
        
        # 判断是否为核心需求（简化版，实际可用 LLM 判断）
        keywords = ['创建', '开发', '实现', '功能', '需求', '问题', '修复', '添加']
        is_valid = any(kw in str(user_input) for kw in keywords)
        
        if is_valid:
            return {"filtered_intent": user_input, "status": "valid"}
        else:
            return {"filtered_intent": None, "reason": "非核心需求，可能是闲聊"}


class Planner(Agent):
    """任务规划器：将需求拆解为可执行子任务"""
    
    def execute(self, context: Any) -> Any:
        requirement = context.get('filtered_intent') or context.user_input
        
        # 简化版规划逻辑（实际应调用 LLM）
        task_plan = {
            "tasks": [
                {"id": "1", "type": "data", "description": f"数据采集: {requirement}"},
                {"id": "2", "type": "code", "description": f"功能实现: {requirement}"},
                {"id": "3", "type": "doc", "description": f"文档生成: {requirement}"},
            ],
            "estimated_time": "2-3 小时",
            "dependencies": ["1 → 2 → 3"],
        }
        
        context.set('task_plan', task_plan)
        return {"status": "planned", "task_plan": task_plan}


class Reviewer(Agent):
    """方案审核器：评估可行性与风险"""
    
    def execute(self, context: Any) -> Any:
        task_plan = context.get('task_plan')
        
        # 简化版审核逻辑
        review_result = {
            "status": "accept",  # 或 "reject"
            "comments": "方案可行，风险可控",
            "suggestions": ["建议增加错误处理", "考虑添加单元测试"],
        }
        
        context.set('review_result', review_result)
        return review_result


class Orchestrator(Agent):
    """任务调度器：分发任务并汇总结果"""
    
    def execute(self, context: Any) -> Any:
        task_plan = context.get('task_plan')
        results = []
        
        # 模拟并行执行任务
        for task in task_plan.get('tasks', []):
            task_type = task.get('type')
            result = self._dispatch_task(task_type, task)
            results.append(result)
        
        execution_results = {
            "completed_tasks": len(results),
            "results": results,
            "status": "success",
        }
        
        context.execution_results = results
        return execution_results
    
    def _dispatch_task(self, task_type: str, task: dict) -> dict:
        """分发任务到对应 Worker"""
        # 简化版：直接返回模拟结果
        return {
            "task_id": task.get('id'),
            "type": task_type,
            "status": "completed",
            "output": f"{task_type} 任务完成",
        }


class Worker(Agent):
    """通用工作单元：数据/代码/文档/部署执行"""
    
    def execute(self, context: Any) -> Any:
        task_spec = context.get('current_task', {})
        
        # 根据任务类型执行不同逻辑
        task_type = task_spec.get('type', 'generic')
        
        return {
            "status": "completed",
            "task_type": task_type,
            "output": f"{task_type} 执行结果",
        }


class Monitor(Agent):
    """系统监控器：独立运行，采集状态指标"""
    
    def execute(self, context: Any) -> Any:
        # 采集系统指标
        metrics = {
            "timestamp": "2026-03-12T12:00:00Z",
            "active_agents": len(self.engine.agents),
            "tasks_completed": len(context.execution_results),
            "memory_usage": "45%",
            "cpu_usage": "12%",
        }
        
        return {"status": "monitoring", "metrics": metrics}
