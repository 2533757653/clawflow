import os
import subprocess
import json
import time
import logging
import shutil
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class OpenClawExecutor:
    def __init__(self, agents_base_path: str = "agents", timeout: int = 60):
        self.agents_base_path = agents_base_path
        self.timeout = timeout

    def is_openclaw_available(self) -> bool:
        """Check if OpenClaw CLI is installed and accessible."""
        python_cmd = self._get_python_command()
        if not python_cmd:
            return False
        try:
            result = subprocess.run(
                [python_cmd, "-m", "openclaw", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False

    def _get_python_command(self) -> Optional[str]:
        """Get the best available Python command for this platform."""
        if os.name == "nt":
            for cmd in ["py", "python", "python.exe"]:
                if shutil.which(cmd):
                    return cmd
            return "py"
        return "python"

    def execute_role(
        self,
        role_name: str,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if not self.is_openclaw_available():
            return {
                "error": "OpenClaw is not installed. Run: pip install openclaw",
                "role": role_name,
                "hint": "Make sure openclaw is in your PATH or installed in the current environment."
            }

        agent_path = os.path.join(
            self.agents_base_path,
            role_name.lower().replace(" ", "_")
        )

        if not os.path.exists(agent_path):
            raise FileNotFoundError(f"Agent not deployed: {agent_path}")

        exec_input = {
            "task": input_data.get("task", "process request"),
            "context": context or {},
            "timestamp": time.time()
        }

        input_path = os.path.join(agent_path, "memory", "input.json")
        os.makedirs(os.path.dirname(input_path), exist_ok=True)
        with open(input_path, 'w', encoding='utf-8') as f:
            json.dump(exec_input, f, ensure_ascii=False)

        try:
            result = self._call_openclaw(agent_path, input_data)
            return self._parse_output(agent_path, result)
        except subprocess.TimeoutExpired:
            return {"error": "Execution timeout", "role": role_name}
        except Exception as e:
            logger.error(f"OpenClaw execution error: {e}")
            return {"error": str(e), "role": role_name}

    def _call_openclaw(self, agent_path: str, input_data: Dict[str, Any]) -> str:
        cmd = self._build_openclaw_command(agent_path, input_data)
        python_cmd = self._get_python_command()
        if python_cmd != "python":
            cmd = [python_cmd if c == "python" else c for c in cmd]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self.timeout
        )

        if result.returncode != 0:
            raise RuntimeError(f"OpenClaw execution failed (exit {result.returncode}): {result.stderr.strip()}")

        return result.stdout

    def _build_openclaw_command(self, agent_path: str, input_data: Dict[str, Any]) -> list:
        return ["python", "-m", "openclaw", "--agent", agent_path, "--input", json.dumps(input_data)]

    def _parse_output(self, agent_path: str, result: str) -> Dict[str, Any]:
        output_path = os.path.join(agent_path, "memory", "output.json")
        if os.path.exists(output_path):
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to parse output.json: {e}")

        if result:
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {"result": result}

        return {"result": "No output"}

    def is_agent_deployed(self, role_name: str) -> bool:
        agent_path = os.path.join(
            self.agents_base_path,
            role_name.lower().replace(" ", "_")
        )
        return os.path.exists(agent_path)
