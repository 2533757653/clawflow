"""
Agent 基类与元定义

每个 Agent 是一个独立的行为单元，通过消息总线通信
"""

import json
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field, asdict
from pathlib import Path

from .message_bus import Message, get_message_bus, InMemoryMessageBus


@dataclass
class AgentDefinition:
    """Agent 元定义"""
    id: str
    type: str  # Router, Planner, Worker, etc.
    capabilities: List[str] = field(default_factory=list)
    description: str = ""
    behavior_code: Optional[str] = None  # 可选：动态行为代码
    
    def to_dict(self) -> dict:
        return asdict(self)


class Agent(ABC):
    """
    Agent 基类
    
    每个 Agent 必须实现 handle_message() 方法
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        message_bus: InMemoryMessageBus,
        capabilities: Optional[List[str]] = None,
        description: str = "",
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.capabilities = capabilities or []
        self.description = description
        self.message_bus = message_bus
        self.state: Dict[str, Any] = {}
        self.running = False
        
        # 注册到消息总线
        self.message_bus.create_queue(self.agent_id)
    
    @abstractmethod
    def handle_message(self, message: Message) -> Optional[Message]:
        """
        处理接收到的消息
        
        Returns:
            可选的响应消息
        """
        pass
    
    def start(self) -> None:
        """启动 Agent 循环"""
        self.running = True
        while self.running:
            message = self.message_bus.receive(self.agent_id, timeout=1.0)
            if message:
                try:
                    response = self.handle_message(message)
                    if response:
                        self.message_bus.send(response.to_agent, response)
                except Exception as e:
                    error_response = Message(
                        id=str(uuid.uuid4()),
                        type="error",
                        from_agent=self.agent_id,
                        to_agent=message.from_agent,
                        payload={"error": str(e)},
                        correlation_id=message.correlation_id,
                    )
                    self.message_bus.send(message.from_agent, error_response)
    
    def stop(self) -> None:
        """停止 Agent 循环"""
        self.running = False
    
    def send(self, to_agent: str, payload: Dict, message_type: str = "task") -> Message:
        """发送消息到另一个 Agent"""
        message = Message(
            id=str(uuid.uuid4()),
            type=message_type,
            from_agent=self.agent_id,
            to_agent=to_agent,
            payload=payload,
        )
        self.message_bus.send(to_agent, message)
        return message
    
    def request(self, to_agent: str, payload: Dict, timeout: float = 30.0) -> Optional[Message]:
        """发送请求并等待响应"""
        return self.message_bus.request(to_agent, payload, timeout)
    
    def update_state(self, key: str, value: Any) -> None:
        """更新内部状态"""
        self.state[key] = value
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """获取内部状态"""
        return self.state.get(key, default)
    
    def get_definition(self) -> AgentDefinition:
        """获取 Agent 定义"""
        return AgentDefinition(
            id=self.agent_id,
            type=self.agent_type,
            capabilities=self.capabilities,
            description=self.description,
        )


class MetaAgent(Agent):
    """
    元 Agent：负责创建其他 Agent
    
    这是 ClawFlow 自举的关键
    """
    
    def __init__(self, message_bus: InMemoryMessageBus, agent_factory: Callable):
        super().__init__(
            agent_id="meta_agent",
            agent_type="Meta",
            message_bus=message_bus,
            capabilities=["create_agent", "list_agents", "destroy_agent"],
            description="创建和管理其他 Agent 的元 Agent",
        )
        self.agent_factory = agent_factory  # 工厂函数
        self.created_agents: List[str] = []
    
    def handle_message(self, message: Message) -> Optional[Message]:
        msg_type = message.type
        payload = message.payload
        
        if msg_type == "create_agent":
            return self._create_agent(payload, message.from_agent)
        elif msg_type == "list_agents":
            return self._list_agents(message.from_agent)
        elif msg_type == "destroy_agent":
            return self._destroy_agent(payload, message.from_agent)
        else:
            return None
    
    def _create_agent(self, payload: Dict, reply_to: str) -> Message:
        """创建新 Agent"""
        agent_id = payload.get("id")
        agent_type = payload.get("type")
        capabilities = payload.get("capabilities", [])
        description = payload.get("description", "")
        
        try:
            # 使用工厂函数创建 Agent
            agent = self.agent_factory(
                agent_id=agent_id,
                agent_type=agent_type,
                capabilities=capabilities,
                description=description,
            )
            
            self.created_agents.append(agent_id)
            
            return Message(
                id=str(uuid.uuid4()),
                type="response",
                from_agent=self.agent_id,
                to_agent=reply_to,
                payload={
                    "status": "success",
                    "agent_id": agent_id,
                    "message": f"Agent {agent_id} created",
                },
                correlation_id=message.correlation_id,
            )
        except Exception as e:
            return Message(
                id=str(uuid.uuid4()),
                type="error",
                from_agent=self.agent_id,
                to_agent=reply_to,
                payload={"error": str(e)},
                correlation_id=message.correlation_id,
            )
    
    def _list_agents(self, reply_to: str) -> Message:
        """列出所有已创建的 Agent"""
        return Message(
            id=str(uuid.uuid4()),
            type="response",
            from_agent=self.agent_id,
            to_agent=reply_to,
            payload={"agents": self.created_agents},
        )
    
    def _destroy_agent(self, payload: Dict, reply_to: str) -> Message:
        """销毁 Agent"""
        agent_id = payload.get("agent_id")
        
        if agent_id in self.created_agents:
            self.created_agents.remove(agent_id)
            # 这里应该调用 agent.stop() 并清理资源
            return Message(
                id=str(uuid.uuid4()),
                type="response",
                from_agent=self.agent_id,
                to_agent=reply_to,
                payload={"status": "success", "message": f"Agent {agent_id} destroyed"},
            )
        else:
            return Message(
                id=str(uuid.uuid4()),
                type="error",
                from_agent=self.agent_id,
                to_agent=reply_to,
                payload={"error": f"Agent {agent_id} not found"},
            )


class WorkerBuilderAgent(Agent):
    """
    Worker 生成器 Agent
    
    根据模板创建具体的 Worker Agent（data_worker, code_worker, etc.）
    """
    
    def __init__(self, message_bus: InMemoryMessageBus, agent_factory: Callable):
        super().__init__(
            agent_id="worker_builder",
            agent_type="Builder",
            message_bus=message_bus,
            capabilities=["build_worker"],
            description="根据模板生成各类 Worker Agent",
        )
        self.agent_factory = agent_factory
        self.worker_templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Dict]:
        """加载 Worker 模板"""
        return {
            "data_worker": {
                "type": "Worker",
                "capabilities": ["exec", "web_fetch", "read/write"],
                "description": "数据处理 Worker",
            },
            "code_worker": {
                "type": "Worker",
                "capabilities": ["exec", "read/write/edit", "web_search"],
                "description": "代码实现 Worker",
            },
            "doc_worker": {
                "type": "Worker",
                "capabilities": ["read/write/edit", "web_search"],
                "description": "文档生成 Worker",
            },
            "review_worker": {
                "type": "Worker",
                "capabilities": ["exec", "read", "web_search"],
                "description": "质量审查 Worker",
            },
        }
    
    def handle_message(self, message: Message) -> Optional[Message]:
        if message.type == "build_worker":
            return self._build_worker(message.payload, message.from_agent)
        return None
    
    def _build_worker(self, payload: Dict, reply_to: str) -> Message:
        """根据模板构建 Worker"""
        worker_type = payload.get("worker_type")  # data, code, doc, review
        template = self.worker_templates.get(f"{worker_type}_worker")
        
        if not template:
            return Message(
                id=str(uuid.uuid4()),
                type="error",
                from_agent=self.agent_id,
                to_agent=reply_to,
                payload={"error": f"Unknown worker type: {worker_type}"},
            )
        
        agent_id = f"{worker_type}_worker"
        
        # 请求 MetaAgent 创建
        response = self.request("meta_agent", {
            "id": agent_id,
            "type": template["type"],
            "capabilities": template["capabilities"],
            "description": template["description"],
        }, timeout=10.0)
        
        if response and response.payload.get("status") == "success":
            return Message(
                id=str(uuid.uuid4()),
                type="response",
                from_agent=self.agent_id,
                to_agent=reply_to,
                payload={
                    "status": "success",
                    "agent_id": agent_id,
                    "worker_type": worker_type,
                },
                correlation_id=message.correlation_id,
            )
        else:
            return Message(
                id=str(uuid.uuid4()),
                type="error",
                from_agent=self.agent_id,
                to_agent=reply_to,
                payload={"error": "Failed to create worker"},
                correlation_id=message.correlation_id,
            )
