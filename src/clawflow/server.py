"""
ClawFlow 独立服务 - MVP 版本

启动消息总线、Agent 工厂、自举流程
提供 HTTP API 供 OpenClaw Skill 调用
"""

import json
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import uuid

from .message_bus import get_message_bus, InMemoryMessageBus, Message
from .agent_base import Agent, MetaAgent, WorkerBuilderAgent, AgentDefinition


class SimpleAgent(Agent):
    """
    简单 Agent 实现
    
    用于 MVP 测试
    """
    
    def __init__(self, agent_id: str, agent_type: str, message_bus: InMemoryMessageBus):
        super().__init__(
            agent_id=agent_id,
            agent_type=agent_type,
            message_bus=message_bus,
            capabilities=[],
            description=f"{agent_type} Agent",
        )
    
    def handle_message(self, message: Message) -> Optional[Message]:
        """处理消息"""
        print(f"[{self.agent_id}] 收到消息：{message.type} from {message.from_agent}")
        
        # 简单响应
        return Message(
            id=str(uuid.uuid4()),
            type="response",
            from_agent=self.agent_id,
            to_agent=message.from_agent,
            payload={
                "status": "received",
                "agent": self.agent_id,
                "original_type": message.type,
            },
            correlation_id=message.correlation_id,
        )


class AgentFactory:
    """Agent 工厂"""
    
    def __init__(self, message_bus: InMemoryMessageBus):
        self.message_bus = message_bus
        self.agents: Dict[str, Agent] = {}
    
    def create_agent(self, agent_id: str, agent_type: str) -> Agent:
        """创建 Agent 实例"""
        if agent_id == "meta_agent":
            agent = MetaAgent(self.message_bus, self.create_agent)
        elif agent_id == "worker_builder":
            agent = WorkerBuilderAgent(self.message_bus, self.create_agent)
        else:
            agent = SimpleAgent(agent_id, agent_type, self.message_bus)
        
        self.agents[agent_id] = agent
        print(f"  ✓ 创建 Agent: {agent_id} ({agent_type})")
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        return self.agents.get(agent_id)
    
    def list_agents(self) -> list:
        return list(self.agents.keys())


class ClawFlowService:
    """ClawFlow 核心服务"""
    
    def __init__(self, storage_path: str = ".clawflow"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.message_bus = get_message_bus(str(self.storage_path / "messages"))
        self.agent_factory = AgentFactory(self.message_bus)
        self.running = False
        
        self.meta_agent: Optional[MetaAgent] = None
        self.worker_builder: Optional[WorkerBuilderAgent] = None
    
    def bootstrap(self) -> None:
        """自举流程"""
        print("\n🐙 ClawFlow 自举启动...")
        
        # 步骤 1: 创建 MetaAgent
        print("  [1/4] 创建 MetaAgent...")
        self.meta_agent = self.agent_factory.create_agent("meta_agent", "Meta")
        
        # 步骤 2: 创建 WorkerBuilderAgent
        print("  [2/4] 创建 WorkerBuilderAgent...")
        self.worker_builder = self.agent_factory.create_agent("worker_builder", "Builder")
        
        # 步骤 3: 创建 Worker Agents
        print("  [3/4] 创建 Worker Agents...")
        for worker_type in ["data", "code", "doc", "review"]:
            self.agent_factory.create_agent(f"{worker_type}_worker", "Worker")
        
        # 步骤 4: 创建核心工作流 Agent
        print("  [4/4] 创建工作流 Agents...")
        for agent_id, agent_type in [
            ("router", "Router"),
            ("planner", "Planner"),
            ("reviewer", "Reviewer"),
            ("orchestrator", "Orchestrator"),
        ]:
            self.agent_factory.create_agent(agent_id, agent_type)
        
        print(f"\n✅ ClawFlow 自举完成！已创建 {len(self.agent_factory.agents)} 个 Agent\n")
    
    def start_agent_threads(self) -> None:
        """启动所有 Agent 线程"""
        for agent_id, agent in self.agent_factory.agents.items():
            thread = threading.Thread(target=agent.start, daemon=True)
            thread.start()
            print(f"  → {agent_id} 线程启动")
    
    def process_workflow(self, user_input: str) -> Dict[str, Any]:
        """处理用户工作流请求"""
        request_msg = Message(
            id=str(uuid.uuid4()),
            type="task",
            from_agent="external_user",
            to_agent="router",
            payload={"user_input": user_input},
            correlation_id=str(uuid.uuid4()),
        )
        
        self.message_bus.send("router", request_msg)
        
        # 等待响应（简化版 MVP）
        time.sleep(0.2)
        
        return {
            "status": "accepted",
            "message": "工作流已启动，Agents 正在处理",
            "input": user_input,
            "agents_active": len(self.agent_factory.agents),
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            "status": "running" if self.running else "stopped",
            "agents": self.agent_factory.list_agents(),
            "message_bus_stats": self.message_bus.get_stats(),
        }
    
    def start(self, host: str = "0.0.0.0", port: int = 8765) -> None:
        """启动 HTTP 服务"""
        self.running = True
        
        # 自举
        self.bootstrap()
        
        # 启动 Agent 线程
        print("启动 Agent 线程...")
        self.start_agent_threads()
        
        # 启动 HTTP 服务器
        server = ClawFlowHTTPServer((host, port), self)
        print(f"\n🌐 ClawFlow HTTP 服务启动：http://{host}:{port}")
        print("   按 Ctrl+C 停止服务\n")
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 正在停止服务...")
            self.running = False
            server.shutdown()


class ClawFlowHTTPServer(HTTPServer):
    """ClawFlow HTTP 服务器"""
    
    def __init__(self, server_address, clawflow_service: ClawFlowService):
        super().__init__(server_address, ClawFlowRequestHandler)
        self.clawflow_service = clawflow_service


class ClawFlowRequestHandler(BaseHTTPRequestHandler):
    """HTTP 请求处理器"""
    
    @property
    def service(self) -> ClawFlowService:
        return self.server.clawflow_service
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == "/status":
            self._send_json(self.service.get_status())
        elif path == "/agents":
            self._send_json({"agents": self.service.agent_factory.list_agents()})
        elif path == "/health":
            self._send_json({"status": "healthy"})
        else:
            self._send_error(404, "Not Found")
    
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON")
            return
        
        if path == "/run":
            user_input = data.get("input", "")
            if not user_input:
                self._send_error(400, "Missing 'input' field")
                return
            
            result = self.service.process_workflow(user_input)
            self._send_json(result)
        
        elif path == "/agents/create":
            agent_id = data.get("id")
            agent_type = data.get("type")
            
            if not agent_id or not agent_type:
                self._send_error(400, "Missing 'id' or 'type'")
                return
            
            self.service.agent_factory.create_agent(agent_id, agent_type)
            
            self._send_json({
                "status": "success",
                "agent_id": agent_id,
            })
        
        else:
            self._send_error(404, "Not Found")
    
    def _send_json(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def _send_error(self, status: int, message: str):
        self._send_json({"error": message}, status)
    
    def log_message(self, format, *args):
        print(f"[HTTP] {args[0]}")


def main():
    """启动 ClawFlow 服务"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ClawFlow Independent Service")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind")
    parser.add_argument("--storage", default=".clawflow", help="Storage path")
    
    args = parser.parse_args()
    
    service = ClawFlowService(storage_path=args.storage)
    service.start(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
