import os
import shutil
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from api.models import Role
from api.services.storage import StorageService

logger = logging.getLogger(__name__)


class AgentSyncService:
    def __init__(self, agents_path: str = "agents"):
        self.agents_path = agents_path
        self.role_storage = StorageService[Role]("data/roles", Role)

    def sync_role(self, role: Role, force: bool = False) -> Dict[str, Any]:
        agent_name = role.name.lower().replace(" ", "_")
        agent_path = os.path.join(self.agents_path, agent_name)

        if not os.path.exists(agent_path):
            return {
                "status": "skipped",
                "reason": "Agent not deployed",
                "agent_path": agent_path
            }

        try:
            self._update_agent_files(role, agent_path)
            return {
                "status": "synced",
                "agent_path": agent_path,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "agent_path": agent_path
            }

    def sync_all(self, role_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        if role_ids:
            roles = [self.role_storage.get(rid) for rid in role_ids]
            roles = [r for r in roles if r]
        else:
            roles = self.role_storage.list()

        results = []
        for role in roles:
            result = self.sync_role(role)
            result["role_id"] = role.id
            result["role_name"] = role.name
            results.append(result)

        return results

    def _update_agent_files(self, role: Role, agent_path: str):
        files_to_update = {
            "SOUL.md": role.soul_template or self._default_soul(role),
            "IDENTITY.md": role.identity_template or self._default_identity(role),
            "AGENTS.md": self._generate_agents_md(role),
        }

        for filename, content in files_to_update.items():
            filepath = os.path.join(agent_path, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

        if role.context_memory:
            memory_path = os.path.join(agent_path, "memory", "context.md")
            os.makedirs(os.path.dirname(memory_path), exist_ok=True)
            with open(memory_path, 'w', encoding='utf-8') as f:
                f.write(role.context_memory)

    def _default_soul(self, role: Role) -> str:
        responsibilities = "\n".join([f"- {r}" for r in role.responsibilities])
        return f"""# SOUL.md - {role.name}

_You're not a chatbot. You're becoming someone._

## Core Truths

**Be genuinely helpful, not performatively helpful.**

## Responsibilities

{responsibilities}

## Boundaries

- Private things stay private. Period.
- When in doubt, ask before acting externally.
"""

    def _default_identity(self, role: Role) -> str:
        return f"""# IDENTITY.md - Who Am I?

- **Name:** {role.name}
- **Role:** {role.description or 'AI Agent'}
- **Vibe:** Professional, helpful, and efficient
"""

    def _generate_agents_md(self, role: Role) -> str:
        responsibilities = "\n".join([f"- {r}" for r in role.responsibilities]) if role.responsibilities else "No responsibilities defined."
        return f"""# AGENTS.md - {role.name}'s Workspace

## Role: {role.name}

{role.description or 'No description provided.'}

## Core Responsibilities

{responsibilities}

## Skills

Skills provide your tools. When you need one, check the `skills/` directory.

## Red Lines

- Don't exfiltrate private data. Ever.
- Don't run destructive commands without asking.
- When in doubt, ask.
"""

    def migrate_agent_directory(self, old_name: str, new_name: str) -> bool:
        old_path = os.path.join(self.agents_path, old_name.lower().replace(" ", "_"))
        new_path = os.path.join(self.agents_path, new_name.lower().replace(" ", "_"))

        if not os.path.exists(old_path):
            return False

        if os.path.exists(new_path):
            return False

        shutil.move(old_path, new_path)
        return True