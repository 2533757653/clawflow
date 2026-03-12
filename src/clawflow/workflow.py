"""
工作流定义与条件评估

Workflow 管理 Agent 之间的流转逻辑
"""

from dataclasses import dataclass, field
from typing import Any, Optional, Callable


@dataclass
class Step:
    """工作流步骤"""
    from_: str  # 源 Agent
    to: str     # 目标 Agent
    condition: str  # 条件表达式
    description: str = ""
    
    def __post_init__(self):
        # 处理 from 关键字
        if hasattr(self, 'from_'):
            self.from_agent = self.from_
        else:
            self.from_agent = getattr(self, 'from', '')


@dataclass
class Workflow:
    """工作流定义"""
    entry: str
    steps: list[Step] = field(default_factory=list)
    background_services: list[dict] = field(default_factory=list)
    
    def evaluate(self, current_agent: str, result: Any, context: Any) -> Optional[str]:
        """
        评估条件，决定下一步
        
        Returns:
            下一个 Agent ID，或 None 表示结束
        """
        for step in self.steps:
            if step.from_agent != current_agent:
                continue
            
            # 评估条件
            if self._check_condition(step.condition, result, context):
                return step.to
        
        return None
    
    def _check_condition(self, condition: str, result: Any, context: Any) -> bool:
        """
        检查条件是否满足
        
        支持的条件表达式：
        - "valid_requirement" → result.get('status') == 'valid'
        - "plan_created" → result.get('status') == 'planned'
        - "approval_passed" → result.get('status') == 'accept'
        - "rejection_needed" → result.get('status') == 'reject'
        - "execution_complete" → result.get('status') == 'completed'
        - "all_tasks_completed" → True
        """
        condition_map = {
            "valid_requirement": lambda: result.get('status') == 'valid',
            "plan_created": lambda: result.get('status') == 'planned',
            "approval_passed": lambda: result.get('status') == 'accept',
            "rejection_needed": lambda: result.get('status') == 'reject',
            "execution_complete": lambda: result.get('status') in ['completed', 'success'],
            "all_tasks_completed": lambda: True,
            "dispatch_data_task": lambda: True,
            "dispatch_code_task": lambda: True,
            "dispatch_review_task": lambda: True,
            "dispatch_deploy_task": lambda: True,
            "dispatch_doc_task": lambda: True,
        }
        
        checker = condition_map.get(condition)
        if checker:
            try:
                return checker()
            except Exception:
                return False
        
        return False
    
    def get_next_steps(self, agent_id: str) -> list[Step]:
        """获取指定 Agent 的所有可能下一步"""
        return [s for s in self.steps if s.from_agent == agent_id]
