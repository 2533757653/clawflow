"""
ClawFlow OpenClaw 技能集成

将 ClawFlow 工作流作为 OpenClaw 技能运行
"""

import json
import subprocess
import requests
from typing import Dict, Any, Optional
from pathlib import Path


class ClawFlowSkill:
    """
    ClawFlow 技能类 - 与 OpenClaw 原生集成
    """
    
    def __init__(self, api_endpoint: str = "http://localhost:8765"):
        self.api_endpoint = api_endpoint
        self.session = requests.Session()
    
    def run_workflow(self, user_input: str) -> Dict[str, Any]:
        """
        通过 API 运行 ClawFlow 工作流
        """
        try:
            response = self.session.post(
                f"{self.api_endpoint}/run",
                json={"input": user_input},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "error": f"API 调用失败: {str(e)}"
            }
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取 ClawFlow 服务状态
        """
        try:
            response = self.session.get(f"{self.api_endpoint}/health")
            response.raise_for_status()
            return {"status": "healthy", "api": self.api_endpoint}
        except:
            return {"status": "unavailable", "api": self.api_endpoint}
    
    def execute_self_update(self) -> Dict[str, Any]:
        """
        执行自更新流程
        """
        print("🔄 开始执行 ClawFlow 自更新流程...")
        
        # 1. 检查当前版本
        try:
            result = subprocess.run(
                ["git", "status"], 
                cwd="/root/Agents/Profession/clawflow",
                capture_output=True, 
                text=True,
                timeout=10
            )
            print(f"📋 Git 状态: {result.stdout[:200]}...")
        except subprocess.TimeoutExpired:
            print("⏰ Git 状态检查超时")
        except Exception as e:
            print(f"❌ Git 状态检查失败: {e}")
        
        # 2. 执行更新
        try:
            result = subprocess.run(
                ["git", "pull", "origin", "main"], 
                cwd="/root/Agents/Profession/clawflow",
                capture_output=True, 
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                print("✅ 更新成功")
                update_result = {"status": "success", "details": result.stdout}
            else:
                print(f"❌ 更新失败: {result.stderr}")
                update_result = {"status": "failed", "error": result.stderr}
        except subprocess.TimeoutExpired:
            print("⏰ 更新操作超时")
            update_result = {"status": "timeout", "error": "更新操作超时"}
        except Exception as e:
            print(f"❌ 更新过程中出错: {e}")
            update_result = {"status": "error", "error": str(e)}
        
        # 3. 记录更新日志
        try:
            log_content = f"Self-update executed at {self._get_timestamp()}\nResult: {update_result}\n"
            with open("/root/Agents/Profession/clawflow/update_log.txt", "a", encoding="utf-8") as f:
                f.write(log_content)
            print("📝 更新日志已记录")
        except Exception as e:
            print(f"❌ 记录日志失败: {e}")
        
        return update_result
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# OpenClaw 技能接口
def skill_handler(command: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    OpenClaw 技能处理器
    """
    skill = ClawFlowSkill()
    
    if command == "status":
        return skill.get_status()
    elif command == "run":
        user_input = params.get("input", "")
        return skill.run_workflow(user_input)
    elif command == "self-update":
        return skill.execute_self_update()
    elif command == "health":
        return skill.get_status()
    else:
        return {"status": "error", "error": f"未知命令: {command}"}


if __name__ == "__main__":
    # 测试技能
    skill = ClawFlowSkill()
    
    print("Testing ClawFlow Skill Integration:")
    print("Status:", skill.get_status())
    
    result = skill.run_workflow("测试工作流")
    print("Workflow result:", json.dumps(result, indent=2, ensure_ascii=False)[:200] + "...")