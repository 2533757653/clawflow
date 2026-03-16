"""
ClawFlow 集成服务器

利用 OpenClaw 原生 Agent 系统的重构版本
不再使用独立的消息总线和 Agent 线程，
而是直接调用 OpenClaw 的 sessions_spawn 和其他原生功能
"""

import json
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import uuid

from .enhanced_engine import EnhancedWorkflowEngine


class IntegratedClawFlowService:
    """集成版 ClawFlow 服务"""
    
    def __init__(self, storage_path: str = ".clawflow"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.running = False
        self.engine = EnhancedWorkflowEngine()
    
    def process_workflow(self, user_input: str) -> Dict[str, Any]:
        """处理用户工作流请求 - 使用增强版引擎，支持 Actor-Critic 模式"""
        return self.engine.execute_workflow(user_input)
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            "status": "running" if self.running else "stopped",
            "engine": "integrated_openclaw",
            "capabilities": [
                "router", "planner", "reviewer", "orchestrator",
                "data_worker", "code_worker", "doc_worker"
            ]
        }
    
    def start(self, host: str = "0.0.0.0", port: int = 8765) -> None:
        """启动 HTTP 服务"""
        self.running = True
        
        print(f"\n🌐 集成版 ClawFlow HTTP 服务启动：http://{host}:{port}")
        print("   利用 OpenClaw 原生 Agent 系统")
        print("   按 Ctrl+C 停止服务\n")
        
        # 启动 HTTP 服务器
        server = IntegratedClawFlowHTTPServer((host, port), self)
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 正在停止服务...")
            self.running = False
            server.shutdown()


class IntegratedClawFlowHTTPServer(HTTPServer):
    """集成版 ClawFlow HTTP 服务器"""
    
    def __init__(self, server_address, clawflow_service: IntegratedClawFlowService):
        super().__init__(server_address, IntegratedClawFlowRequestHandler)
        self.clawflow_service = clawflow_service


class IntegratedClawFlowRequestHandler(BaseHTTPRequestHandler):
    """集成版 HTTP 请求处理器"""
    
    @property
    def service(self) -> IntegratedClawFlowService:
        return self.server.clawflow_service
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == "/status":
            self._send_json(self.service.get_status())
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
            
            # 直接调用集成引擎 - 不再有锁竞争问题
            result = self.service.process_workflow(user_input)
            self._send_json(result)
        
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
    """启动集成版 ClawFlow 服务"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Integrated ClawFlow Service (Using OpenClaw Native Agents)")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind")
    parser.add_argument("--storage", default=".clawflow", help="Storage path")
    
    args = parser.parse_args()
    
    service = IntegratedClawFlowService(storage_path=args.storage)
    service.start(host=args.host, port=args.port)


if __name__ == "__main__":
    main()