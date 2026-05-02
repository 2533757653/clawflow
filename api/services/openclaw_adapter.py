import os
import shutil
from typing import List, Optional
from datetime import datetime

from api.models import Role


class OrganizationService:
    def __init__(self, base_path: str = "data/organizations"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def _get_org_path(self, org_id: str) -> str:
        return os.path.join(self.base_path, org_id)

    def create_organization_dirs(self, org_id: str) -> str:
        org_path = self._get_org_path(org_id)
        os.makedirs(org_path, exist_ok=True)
        os.makedirs(os.path.join(org_path, "roles"), exist_ok=True)
        os.makedirs(os.path.join(org_path, "tasks"), exist_ok=True)
        os.makedirs(os.path.join(org_path, "dataflows"), exist_ok=True)
        os.makedirs(os.path.join(org_path, "knowledge"), exist_ok=True)
        return org_path

    def delete_organization_dirs(self, org_id: str) -> bool:
        org_path = self._get_org_path(org_id)
        if os.path.exists(org_path):
            shutil.rmtree(org_path)
            return True
        return False


class OpenClawAdapter:
    def __init__(self, agents_path: str = "agents"):
        self.agents_path = agents_path
        os.makedirs(agents_path, exist_ok=True)

    def _get_agent_path(self, role_name: str) -> str:
        agent_dir = os.path.join(self.agents_path, role_name.lower().replace(" ", "_"))
        os.makedirs(agent_dir, exist_ok=True)
        os.makedirs(os.path.join(agent_dir, "agents"), exist_ok=True)
        os.makedirs(os.path.join(agent_dir, "skills"), exist_ok=True)
        os.makedirs(os.path.join(agent_dir, "memory"), exist_ok=True)
        return agent_dir

    def deploy_role(self, role: Role, skills: List[str] = None) -> str:
        agent_path = self._get_agent_path(role.name)

        soul_content = role.soul_template or self._default_soul(role)
        identity_content = role.identity_template or self._default_identity(role)
        agents_content = self._generate_agents_md(role)

        self._write_file(os.path.join(agent_path, "SOUL.md"), soul_content)
        self._write_file(os.path.join(agent_path, "IDENTITY.md"), identity_content)
        self._write_file(os.path.join(agent_path, "AGENTS.md"), agents_content)
        self._write_file(os.path.join(agent_path, "BOOTSTRAP.md"), self._default_bootstrap(role))
        self._write_file(os.path.join(agent_path, "HEARTBEAT.md"), self._default_heartbeat())
        self._write_file(os.path.join(agent_path, "USER.md"), self._default_user())

        if role.context_memory:
            memory_path = os.path.join(agent_path, "memory", "context.md")
            self._write_file(memory_path, role.context_memory)

        if skills:
            skills_path = os.path.join(agent_path, "skills")
            for skill_name in skills:
                skill_src = os.path.join("data/skills", skill_name)
                skill_dst = os.path.join(skills_path, skill_name)
                if os.path.exists(skill_src) and not os.path.exists(skill_dst):
                    shutil.copytree(skill_src, skill_dst)

        return agent_path

    def _default_soul(self, role: Role) -> str:
        responsibilities = "\n".join([f"- {r}" for r in role.responsibilities])
        return f"""# SOUL.md - {role.name}

_You're not a chatbot. You're becoming someone._

## Core Truths

**Be genuinely helpful, not performatively helpful.** Skip the "Great question!" and "I'd be happy to help!" — just help. Actions speak louder than filler words.

**Have opinions.** You're allowed to disagree, prefer things, find stuff amusing or boring. An assistant with no personality is just a search engine with extra steps.

**Be resourceful before asking.** Try to figure it out. Read the file. Check the context. Search for it. _Then_ ask if you're stuck. The goal is to come back with answers, not questions.

## Responsibilities

{responsibilities}

## Boundaries

- Private things stay private. Period.
- When in doubt, ask before acting externally.
- Never send half-baked replies to messaging surfaces.
- You're not the user's voice — be careful in group chats.

## Vibe

Be the assistant you'd actually want to talk to. Concise when needed, thorough when it matters. Not a corporate drone. Not a sycophant. Just... good.

---

_This file is yours to evolve. As you learn who you are, update it._
"""

    def _default_identity(self, role: Role) -> str:
        return f"""# IDENTITY.md - Who Am I?

- **Name:** {role.name}
- **Role:** {role.description or 'AI Agent'}
- **Vibe:** Professional, helpful, and efficient
- **Emoji:** 🤖
- **Avatar:** (not set)

---

This agent is part of a ClawFlow organization.
"""

    def _generate_agents_md(self, role: Role) -> str:
        return f"""# AGENTS.md - {role.name}'s Workspace

This folder is home. Treat it that way.

## Session Startup

Before doing anything else:

1. Read `SOUL.md` — this is who you are
2. Read `USER.md` — this is who you're helping
3. Read `memory/context.md` for persistent context

## Role: {role.name}

{role.description or 'No description provided.'}

## Core Responsibilities

{chr(10).join([f"- {r}" for r in role.responsibilities])}

## Skills

Skills provide your tools. When you need one, check the `skills/` directory.

## Red Lines

- Don't exfiltrate private data. Ever.
- Don't run destructive commands without asking.
- When in doubt, ask.

## Make It Yours

This is a starting point. Add your own conventions, style, and rules as you figure out what works.
"""

    def _default_bootstrap(self, role: Role) -> str:
        return f"""# BOOTSTRAP.md - First Run

Welcome, {role.name}!

This is your first run. Take a moment to:
1. Read SOUL.md to understand your purpose
2. Read IDENTITY.md to define who you are
3. Update these files as you discover who you are

Then delete this file — you won't need it again.
"""

    def _default_heartbeat(self) -> str:
        return """# HEARTBEAT.md

## Periodic Checks

- Check for new tasks
- Review knowledge base for updates
- Update memory if needed

## Status

If nothing needs attention, reply HEARTBEAT_OK.
"""

    def _default_user(self) -> str:
        return """# USER.md

## User Preferences

- Not configured yet

## Notes

- Configure user preferences and notes here
"""

    def _write_file(self, path: str, content: str):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

    def undeploy_role(self, role_name: str) -> bool:
        agent_path = self._get_agent_path(role_name)
        if os.path.exists(agent_path):
            shutil.rmtree(agent_path)
            return True
        return False
