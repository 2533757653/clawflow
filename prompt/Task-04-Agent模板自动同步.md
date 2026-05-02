# Task-04: Agent模板自动同步机制

## 项目背景

**项目**: ClawFlow - Agent组织动态构建平台
**当前问题**: 用户在ClawFlow中修改角色（改名、更新职责等），但 `agents/{role_name}/` 目录下的 SOUL.md/IDENTITY.md 不会自动更新
**修改目标**: 实现角色修改后自动同步到已部署的Agent目录

## 问题场景

```
# 1. 用户创建角色 "CEO"
# 2. 部署后生成 agents/ceo/SOUL.md

# 3. 用户把角色名改为 "Chief Executive Officer"
# 4. 但 agents/ceo/ 还是旧内容！
# 5. 更糟糕的是，如果部署新组织，会生成 agents/chief_executive_officer/
```

## 输入输出要求

### 输入
- 角色更新事件（通过API或内部触发）
- 当前角色定义（从 `data/roles/` 读取）

### 输出
- 更新后的 Agent 文件（SOUL.md, IDENTITY.md, AGENTS.md）
- 同步日志（可选）

## 约束条件

1. **幂等性**: 同步操作可重复执行，结果一致
2. **原子性**: 同步失败时回滚，不留半更新状态
3. **最小影响**: 只更新确实变更的内容
4. **向后兼容**: 不影响现有部署流程

## 技术实现要求

### 1. 新增Agent同步服务

**新增文件**: `api/services/agent_sync_service.py`

```python
import os
import shutil
from datetime import datetime
from typing import List, Optional, Dict, Any

from api.models import Role
from api.services.storage import StorageService

class AgentSyncService:
    """同步ClawFlow角色到OpenClaw Agent目录"""

    def __init__(self, agents_path: str = "agents"):
        self.agents_path = agents_path
        self.role_storage = StorageService[Role]("data/roles", Role)

    def sync_role(self, role: Role, force: bool = False) -> Dict[str, Any]:
        """
        同步单个角色到Agent目录

        Returns:
            Dict with 'synced', 'skipped', 'errors' keys
        """
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
        """同步所有或指定角色"""
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
        """更新Agent目录下的文件"""
        files_to_update = {
            "SOUL.md": role.soul_template or self._default_soul(role),
            "IDENTITY.md": role.identity_template or self._default_identity(role),
            "AGENTS.md": self._generate_agents_md(role),
        }

        for filename, content in files_to_update.items():
            filepath = os.path.join(agent_path, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

        # 更新上下文记忆
        if role.context_memory:
            memory_path = os.path.join(agent_path, "memory", "context.md")
            os.makedirs(os.path.dirname(memory_path), exist_ok=True)
            with open(memory_path, 'w', encoding='utf-8') as f:
                f.write(role.context_memory)

    def _default_soul(self, role: Role) -> str:
        """生成默认SOUL.md（参考OpenClawAdapter）"""
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
```

### 2. 修改Role Router

**修改文件**: `api/routers/roles.py`

```python
from api.services.agent_sync_service import AgentSyncService

router = APIRouter()
role_storage = StorageService[Role]("data/roles", Role)
agent_sync_service = AgentSyncService()  # 新增

@router.put("/{role_id}", response_model=Role)
async def update_role(role_id: str, role: Role):
    existing = role_storage.get(role_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Role not found")

    # 检查名称变更
    old_name = existing.name
    name_changed = role.name != old_name

    # 保存角色
    if role.name != existing.name:
        name_conflict = [r for r in role_storage.list() if r.name == role.name and r.id != role_id]
        if name_conflict:
            raise HTTPException(status_code=400, detail="Role with this name already exists")

    role.id = role_id
    saved_role = role_storage.save(role)

    # 新增: 同步到已部署的Agent
    sync_result = agent_sync_service.sync_role(saved_role)

    # 如果名称变更，需要处理旧目录
    if name_changed:
        old_agent_path = os.path.join("agents", old_name.lower().replace(" ", "_"))
        new_agent_path = os.path.join("agents", saved_role.name.lower().replace(" ", "_"))

        if os.path.exists(old_agent_path):
            if os.path.exists(new_agent_path):
                # 新目录已存在，只同步文件，不移动目录
                agent_sync_service.sync_role(saved_role, force=True)
            else:
                # 安全重命名目录
                try:
                    shutil.move(old_agent_path, new_agent_path)
                    # 更新目录内的引用
                    agent_sync_service.sync_role(saved_role, force=True)
                except Exception as e:
                    # 回滚角色名
                    saved_role.name = old_name
                    role_storage.save(saved_role)
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to rename agent directory: {str(e)}"
                    )

    return saved_role
```

### 3. 添加同步API端点（可选管理端点）

**修改文件**: `api/routers/roles.py`

```python
@router.post("/sync-all")
async def sync_all_roles(role_ids: Optional[List[str]] = None):
    """手动触发所有角色的同步"""
    results = agent_sync_service.sync_all(role_ids)
    synced = [r for r in results if r["status"] == "synced"]
    skipped = [r for r in results if r["status"] == "skipped"]
    errors = [r for r in results if r["status"] == "error"]

    return {
        "total": len(results),
        "synced": len(synced),
        "skipped": len(skipped),
        "errors": len(errors),
        "details": results
    }

@router.post("/{role_id}/sync")
async def sync_single_role(role_id: str):
    """手动触发单个角色同步"""
    role = role_storage.get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    result = agent_sync_service.sync_role(role)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])

    return result
```

### 4. 添加名称变更检测（可选）

如果需要支持角色名变更时自动迁移Agent目录：

```python
def migrate_agent_directory(old_name: str, new_name: str) -> bool:
    """迁移Agent目录到新名称"""
    old_path = os.path.join("agents", old_name.lower().replace(" ", "_"))
    new_path = os.path.join("agents", new_name.lower().replace(" ", "_"))

    if not os.path.exists(old_path):
        return False

    if os.path.exists(new_path):
        # 冲突：保留两个版本
        return False

    shutil.move(old_path, new_path)
    return True
```

## 验收标准

1. ✅ 更新角色后，已部署的Agent文件（SOUL.md等）同步更新
2. ✅ 角色重命名时，正确处理Agent目录迁移
3. ✅ 未部署的角色更新不报错（跳过）
4. ✅ 同步操作幂等（重复执行结果一致）
5. ✅ 提供手动触发同步的API端点
6. ✅ 同步失败时给出明确错误信息

## 依赖关系

- **前置依赖**: 无
- **可并行**: Task-01, Task-02, Task-03

## 注意事项

1. 名称变更涉及目录重命名，需要谨慎处理
2. 建议添加同步锁防止并发问题
3. 考虑添加版本控制，记录每次同步的变更
4. 如果有外部工具监听文件变化，需要通知重新加载
