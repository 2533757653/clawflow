"""
ClawFlow 独立服务

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


class AgentFactory:
    """
    Agent 工厂
    
    负责创建各种类型的 Agent
    未来可扩展：从配置文件加载、动态代码生成
    """
    
    def __init__(self, message_bus: InMemoryMessageBus):
        self.message_bus = message_bus
        self.agents: Dict[str, Agent] = {}
    
    def create_agent(
        self,
        agent_id: str,
        agent_type: str,
        capabilities: list,
        description: str = "",
    ) -> Agent:
        """创建 Agent 实例"""
        from .agents import Router, Planner, Reviewer, Orchestrator, Worker, Monitor
        
        type_map = {
            "Router": Router,
            "Planner": Planner,
            "Reviewer": Reviewer,
            "Orchestrator": Orchestrator,
            "Worker": Worker,
            "Monitor": Monitor,
            "Meta": MetaAgent,
            "Builder": WorkerBuilderAgent,
        }
        
        agent_class = type_map.get(agent_type, Worker)
        
        # 特殊处理 MetaAgent 和 WorkerBuilderAgent
        if agent_type == "Meta":
            agent = agent_class(self.message_bus, self.create_agent)
        elif agent_type == "Builder":
            agent = agent_class(self.message_bus, self.create_agent)
        else:
            agent = agent_class(
                agent_id=agent_id,
                definition={"type": agent_type, "capabilities": capabilities},
                engine=None,  # 独立服务模式下不需要 engine
            )
            # 适配到新的消息总线模式
            agent.message_bus = self.message_bus
        
        self.agents[agent_id] = agent
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """获取 Agent 实例"""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> list:
        """列出所有 Agent"""
        return list(self.agents.keys())


class ClawFlowService:
    """
    ClawFlow 核心服务
    
    管理自举流程、消息总线、Agent 生命周期
    """
    
    def __init__(self, storage_path: str = ".clawflow"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.message_bus = get_message_bus(str(self.storage_path / "messages"))
        self.agent_factory = AgentFactory(self.message_bus)
        self.running = False
        
        # 核心 Agent
        self.meta_agent: Optional[MetaAgent] = None
        self.worker_builder: Optional[WorkerBuilderAgent] = None
    
    def bootstrap(self) -> None:
        """
        自举流程
        
        1. 创建 MetaAgent
        2. 创建 WorkerBuilderAgent
        3. 使用 WorkerBuilder 创建各类 Worker
        4. 创建核心工作流 Agent（Router, Planner, Orchestrator）
        """
        print("🐙 ClawFlow 自举启动...")
        
        # 步骤 1: 创建 MetaAgent
        print("  [1/4] 创建 MetaAgent...")
        self.meta_agent = MetaAgent(self.message_bus, self.agent_factory.create_agent)
        self.agent_factory.agents["meta_agent"] = self.meta_agent
        
        # 步骤 2: 创建 WorkerBuilderAgent
        print("  [2/4] 创建 WorkerBuilderAgent...")
        self.worker_builder = WorkerBuilderAgent(self.message_bus, self.agent_factory.create_agent)
        self.agent_factory.agents["worker_builder"] = self.worker_builder
        
        # 步骤 3: 创建 Worker Agents
        print("  [3/4] 创建 Worker Agents...")
        for worker_type in ["data", "code", "doc", "review"]:
            response = self.worker_builder.request("meta_agent", {
                "id": f"{worker_type}_worker",
                "type": "Worker",
                "capabilities": [],
                "description": f"{worker_type} Worker",
            }, timeout=5.0)
            
            if response:
                print(f"    ✓ {worker_type}_worker 创建成功")
            else:
                print(f"    ✗ {worker_type}_worker 创建失败")
        
        # 步骤 4: 创建核心工作流 Agent
        print("  [4/4] 创建工作流 Agents...")
        core_agents = [
            ("router", "Router", "入口路由器"),
            ("planner", "Planner", "任务规划器"),
            ("reviewer", "Reviewer", "方案审核器"),
            ("orchestrator", "Orchestrator", "任务调度器"),
        ]
        
        for agent_id, agent_type, desc in core_agents:
            agent = self.agent_factory.create_agent(
                agent_id=agent_id,
                agent_type=agent_type,
                capabilities=[],
                description=desc,
            )
            print(f"    ✓ {agent_id} 创建成功")
        
        print("✅ ClawFlow 自举完成！")
        print(f"   已创建 {len(self.agent_factory.agents)} 个 Agent")
    
    def start_agent_threads(self) -> None:
        """在独立线程中启动所有 Agent"""
        for agent_id, agent in self.agent_factory.agents.items():
            thread = threading.Thread(target=agent.start, daemon=True)
            thread.start()
            print(f"  → {agent_id} 线程启动")
    
    def process_workflow(self, user_input: str) -> Dict[str, Any]:
        """
        处理用户工作流请求
        
        简化版：直接调用 Router → Planner → Orchestrator
        """
        # 发送请求到 Router
        request_msg = Message(
            id=str(uuid.uuid4()),
            type="task",
            from_agent="external_user",
            to_agent="router",
            payload={"user_input": user_input},
        )
        
        self.message_bus.send("router", request_msg)
        
        # 等待 Orchestrator 返回结果（简化处理）
        time.sleep(2)  # 实际应该用更复杂的等待逻辑
        
        return {
            "status": "processing",
            "message": "工作流已启动",
            "input": user_input,
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
        """处理 GET 请求"""
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
        """处理 POST 请求"""
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
            # 动态创建 Agent
            agent_id = data.get("id")
            agent_type = data.get("type")
            
            if not agent_id or not agent_type:
                self._send_error(400, "Missing 'id' or 'type'")
                return
            
            agent = self.service.agent_factory.create_agent(
                agent_id=agent_id,
                agent_type=agent_type,
                capabilities=data.get("capabilities", []),
                description=data.get("description", ""),
            )
            
            self._send_json({
                "status": "success",
                "agent_id": agent_id,
            })
        
        else:
            self._send_error(404, "Not Found")
    
    def _send_json(self, data: dict, status: int = 200):
        """发送 JSON 响应"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def _send_error(self, status: int, message: str):
        """发送错误响应"""
        self._send_json({"error": message}, status)
    
    def log_message(self, format, *args):
        """自定义日志格式"""
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
