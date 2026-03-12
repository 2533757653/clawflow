"""
消息总线

ClawFlow 的核心：Agent 之间通过消息传递通信，而非直接调用
支持同步和异步两种模式
"""

import json
import uuid
import time
from pathlib import Path
from typing import Any, Optional, Dict, List
from dataclasses import dataclass, field, asdict
from datetime import datetime
import threading
from queue import Queue, Empty


@dataclass
class Message:
    """消息结构"""
    id: str
    type: str  # 消息类型：task, response, control, event
    from_agent: str
    to_agent: str
    payload: Dict[str, Any]
    reply_to: Optional[str] = None  # 回复目标
    correlation_id: Optional[str] = None  # 关联 ID（用于请求 - 响应配对）
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    priority: int = 0  # 优先级，越高越先处理
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Message':
        return cls(**data)


class InMemoryMessageBus:
    """
    内存版消息总线（MVP 阶段）
    
    生产环境可替换为 Redis/RabbitMQ
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path) if storage_path else None
        self._queues: Dict[str, Queue] = {}  # agent_id -> Queue
        self._subscribers: Dict[str, List[callable]] = {}  # topic -> callbacks
        self._lock = threading.Lock()
        
        # 持久化存储（可选）
        if self.storage_path:
            self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def create_queue(self, agent_id: str) -> None:
        """为 Agent 创建邮箱"""
        with self._lock:
            if agent_id not in self._queues:
                self._queues[agent_id] = Queue()
    
    def send(self, to_agent: str, message: Message) -> None:
        """发送消息到 Agent 邮箱"""
        with self._lock:
            if to_agent not in self._queues:
                self.create_queue(to_agent)
            
            self._queues[to_agent].put(message)
            
            # 持久化（可选）
            if self.storage_path:
                self._persist_message(message)
            
            # 通知订阅者
            topic = f"agent:{to_agent}:message"
            self._publish(topic, message)
    
    def receive(self, agent_id: str, timeout: float = 1.0) -> Optional[Message]:
        """从 Agent 邮箱接收消息"""
        with self._lock:
            if agent_id not in self._queues:
                self.create_queue(agent_id)
        
        try:
            return self._queues[agent_id].get(timeout=timeout)
        except Empty:
            return None
    
    def receive_all(self, agent_id: str) -> List[Message]:
        """接收所有可用消息（非阻塞）"""
        messages = []
        with self._lock:
            if agent_id not in self._queues:
                return messages
            queue = self._queues[agent_id]
            while not queue.empty():
                try:
                    messages.append(queue.get_nowait())
                except Empty:
                    break
        return messages
    
    def request(self, to_agent: str, payload: Dict, timeout: float = 30.0) -> Optional[Message]:
        """
        发送请求并等待响应（同步模式）
        
        自动设置 correlation_id 和 reply_to
        """
        correlation_id = str(uuid.uuid4())
        request_msg = Message(
            id=str(uuid.uuid4()),
            type="task",
            from_agent="coordinator",  # 发送者
            to_agent=to_agent,
            payload=payload,
            correlation_id=correlation_id,
            reply_to="coordinator",  # 回复到协调器
        )
        
        self.send(to_agent, request_msg)
        
        # 等待响应
        start_time = time.time()
        while time.time() - start_time < timeout:
            response = self.receive("coordinator", timeout=1.0)
            if response and response.correlation_id == correlation_id:
                return response
        
        return None
    
    def subscribe(self, topic: str, callback: callable) -> None:
        """订阅主题"""
        with self._lock:
            if topic not in self._subscribers:
                self._subscribers[topic] = []
            self._subscribers[topic].append(callback)
    
    def _publish(self, topic: str, message: Message) -> None:
        """发布消息到主题"""
        with self._lock:
            callbacks = self._subscribers.get(topic, [])
        
        for callback in callbacks:
            try:
                callback(message)
            except Exception as e:
                print(f"Callback error for topic {topic}: {e}")
    
    def _persist_message(self, message: Message) -> None:
        """持久化消息到磁盘"""
        if not self.storage_path:
            return
        
        date = message.timestamp[:10]  # YYYY-MM-DD
        log_file = self.storage_path / f"messages_{date}.jsonl"
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(message.to_dict()) + '\n')
    
    def get_stats(self) -> Dict:
        """获取消息总线统计信息"""
        with self._lock:
            queue_sizes = {
                agent_id: queue.qsize()
                for agent_id, queue in self._queues.items()
            }
        
        return {
            "total_queues": len(self._queues),
            "queue_sizes": queue_sizes,
            "total_subscribers": sum(len(v) for v in self._subscribers.values()),
        }


# 全局消息总线实例（单例）
_global_bus: Optional[InMemoryMessageBus] = None


def get_message_bus(storage_path: Optional[str] = None) -> InMemoryMessageBus:
    """获取全局消息总线实例"""
    global _global_bus
    if _global_bus is None:
        _global_bus = InMemoryMessageBus(storage_path)
    return _global_bus
