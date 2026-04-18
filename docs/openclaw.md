# ClawFlow OpenClaw 集成文档

## 概述

ClawFlow 的核心功能之一是将用户在平台上构建的 Agent 组织部署到 OpenClaw 工作区。OpenClaw 是一个 AI Agent 框架，每个 Agent 由多个 Markdown 文件定义。

## OpenClaw Agent 结构

每个 OpenClaw Agent 包含以下文件：

| 文件 | 必填 | 说明 |
|------|------|------|
| SOUL.md | 是 | Agent 的灵魂/核心性格 |
| IDENTITY.md | 是 | Agent 的身份定义 |
| AGENTS.md | 是 | Agent 的工作区配置 |
| BOOTSTRAP.md | 否 | 首次运行引导 |
| HEARTBEAT.md | 否 | 定时任务配置 |
| USER.md | 否 | 用户信息 |
| skills/ | 否 | 技能目录 |

## 文件映射

### ClawFlow → OpenClaw

| ClawFlow 概念 | OpenClaw 文件 | 说明 |
|--------------|---------------|------|
| Organization | `openclaw_workspace/{org_id}/` | 组织根目录 |
| Role | `{role_name}/` | 角色 Agent 目录 |
| Role.soul_template | `SOUL.md` | Agent 灵魂模板 |
| Role.identity_template | `IDENTITY.md` | Agent 身份模板 |
| Role.agents_config | `AGENTS.md` | Agent 配置 |
| Task | `HEARTBEAT.md` | 定时任务 |
| Knowledge | `AGENTS.md` (内嵌) | 共享知识 |
| Skill | `skills/` 目录 | 技能目录 |

## 部署流程

### 1. 创建目录结构

```
openclaw_workspace/
└── {organization_id}/
    └── {role_name}/
        ├── SOUL.md
        ├── IDENTITY.md
        ├── AGENTS.md
        ├── BOOTSTRAP.md
        ├── HEARTBEAT.md
        ├── USER.md
        ├── skills/
        │   ├── skill1/
        │   │   └── SKILL.md
        │   └── skill2/
        │       └── SKILL.md
        └── memory/
            └── (记忆文件)
```

### 2. 生成 Agent 文件

#### SOUL.md 生成

```python
def generate_soul(role: Role) -> str:
    responsibilities = "\n".join([
        f"- {r}" for r in role.responsibilities
    ])
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
```

#### IDENTITY.md 生成

```python
def generate_identity(role: Role) -> str:
    return f"""# IDENTITY.md - Who Am I?

- **Name:** {role.name}
- **Role:** {role.description or 'AI Agent'}
- **Vibe:** Professional, helpful, and efficient
- **Emoji:** 🤖
- **Avatar:** (not set)

---

This agent is part of a ClawFlow organization.
"""
```

#### AGENTS.md 生成

```python
def generate_agents_md(role: Role, knowledge: List[Knowledge]) -> str:
    knowledge_section = ""
    if knowledge:
        kb_list = "\n".join([
            f"- {kb.title}: {kb.content[:50]}..."
            for kb in knowledge[:5]
        ])
        knowledge_section = f"\n## 📚 Knowledge Base\n\n{kb_list}\n"

    return f"""# AGENTS.md - {role.name}'s Workspace

This folder is home. Treat it that way.

## Session Startup

Before doing anything else:

1. Read `SOUL.md` — this is who you are
2. Read `USER.md` — this is who you're helping
3. Read `memory/YYYY-MM-DD.md` (today + yesterday) for recent context

## Role: {role.name}

{role.description or 'No description provided.'}

## Core Responsibilities

{chr(10).join([f"- {r}" for r in role.responsibilities])}
{knowledge_section}
## Tools

Skills provide your tools. When you need one, check its `SKILL.md`.

## Red Lines

- Don't exfiltrate private data. Ever.
- Don't run destructive commands without asking.
- When in doubt, ask.

## Make It Yours

This is a starting point. Add your own conventions, style, and rules as you figure out what works.
"""
```

## OpenClawAdapter 服务

### 核心方法

```python
class OpenClawAdapter:
    def __init__(self, openclaw_path: str = "openclaw_workspace"):
        self.openclaw_path = openclaw_path
        os.makedirs(openclaw_path, exist_ok=True)

    def deploy_role(self, org_id: str, role: Role,
                    knowledge_base: List[Knowledge] = None) -> str:
        """部署单个角色到 OpenClaw"""
        agent_path = self._get_agent_path(org_id, role.name)

        # 生成并写入文件
        self._write_file("SOUL.md", self._default_soul(role))
        self._write_file("IDENTITY.md", self._default_identity(role))
        self._write_file("AGENTS.md", self._generate_agents_md(role, knowledge_base))
        self._write_file("BOOTSTRAP.md", self._default_bootstrap(role))
        self._write_file("HEARTBEAT.md", self._default_heartbeat())
        self._write_file("USER.md", self._default_user())

        return agent_path

    def undeploy_role(self, org_id: str, role_name: str) -> bool:
        """移除已部署的角色"""
        ...

    def undeploy_organization(self, org_id: str) -> bool:
        """移除整个组织"""
        ...
```

### 部署组织

```python
@app.post("/organizations/{org_id}/deploy")
async def deploy_organization(org_id: str):
    org = get_organization(org_id)
    roles = get_roles(org_id)
    knowledge = get_knowledge(org_id)

    adapter = OpenClawAdapter()

    deployed_agents = []
    for role in roles:
        adapter.deploy_role(org_id, role, knowledge)
        deployed_agents.append({
            "role_id": role.id,
            "role_name": role.name,
            "deployed_at": datetime.now().isoformat()
        })

    update_organization_status(org_id, "deployed")

    return {
        "message": "Organization deployed successfully",
        "deployed_agents": deployed_agents,
        "total_roles": len(roles)
    }
```

## 层级 Agent 支持

ClawFlow 支持高层 Agent 参与组织构建。这意味着：

1. **CEO Agent** 可以由多个下层 Agent 组合而成
2. **Director Agent** 协调多个 Manager Agent
3. **Manager Agent** 管理多个基础 Agent

### 示例组织结构

```
CEO (Level 4)
├── CTO (Level 3)
│   ├── Frontend Lead (Level 2)
│   │   ├── Frontend Engineer 1 (Level 1)
│   │   └── Frontend Engineer 2 (Level 1)
│   └── Backend Lead (Level 2)
│       ├── Backend Engineer 1 (Level 1)
│       └── Backend Engineer 2 (Level 1)
└── CFO (Level 3)
    └── Finance Manager (Level 2)
        └── Accountant (Level 1)
```

### 跨层级协作

高层 Agent 可以：
1. 委派任务给下层 Agent
2. 汇总下层 Agent 的结果
3. 制定策略并分配执行

## 技能集成

### 技能安装

```python
@app.post("/skills/{skill_id}/install")
async def install_skill(skill_id: str):
    skill = get_skill(skill_id)

    # 下载或复制技能文件
    skill_path = os.path.join("data/skills", skill.name)
    os.makedirs(skill_path, exist_ok=True)

    # 生成 SKILL.md
    skill_md = f"""---
name: {skill.name}
version: {skill.version}
description: "{skill.description}"
---

# {skill.name}

{skill.description}
"""
    write_file(os.path.join(skill_path, "SKILL.md"), skill_md)

    return skill
```

### 技能链接

部署 Agent 时，将已安装的技能链接到 Agent 的 `skills/` 目录：

```python
def link_skills(agent_path: str, skill_names: List[str]):
    for skill_name in skill_names:
        source = os.path.join("data/skills", skill_name)
        target = os.path.join(agent_path, "skills", skill_name)

        if os.path.exists(source):
            os.symlink(source, target)  # Unix
            # 或 shutil.copytree(source, target)  # Windows
```

## 现有 OpenClaw Agent 复用

你的环境中已有三个 OpenClaw Agent：

```
d:\openclaw\
├── coder/
│   ├── SOUL.md
│   ├── AGENTS.md
│   └── ...
├── trader/
│   ├── SOUL.md
│   └── ...
└── writer/
    ├── SOUL.md
    └── ...
```

ClawFlow 可以：
1. **导入**现有 Agent 作为模板
2. **修改**现有 Agent 的配置
3. **扩展**现有 Agent 的能力

## 注意事项

1. **路径分隔符**：Windows 使用 `\`，Unix 使用 `/`
2. **文件编码**：始终使用 UTF-8
3. **目录清理**：删除时使用 `shutil.rmtree` 而非 `rm -rf`
4. **并发部署**：建议添加分布式锁（后续扩展）

## 扩展方向

1. **实时同步**：使用 WebSocket 实时同步 Agent 状态
2. **版本控制**：支持 Agent 配置版本管理
3. **回滚支持**：一键回滚到之前的部署版本
4. **监控集成**：集成 Prometheus 监控 Agent 运行状态
