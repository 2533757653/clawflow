import logging
import os
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel

from api.models import Skill

logger = logging.getLogger(__name__)

router = APIRouter()

CLAWHUB_URL = "https://clawhub.example.com/api/v1"

INSTALLED_SKILLS_PATH = "data/skills"


class InstallToRoleRequest(BaseModel):
    role_id: str


def get_installed_skills_storage_path() -> str:
    os.makedirs(INSTALLED_SKILLS_PATH, exist_ok=True)
    return os.path.join(INSTALLED_SKILLS_PATH, "registry.json")


def load_installed_skills() -> List[Skill]:
    registry_path = get_installed_skills_storage_path()
    if not os.path.exists(registry_path):
        return []
    with open(registry_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return [Skill(**item) for item in data]


def save_installed_skills(skills: List[Skill]):
    registry_path = get_installed_skills_storage_path()
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump([s.model_dump(mode='json') for s in skills], f, ensure_ascii=False, indent=2)


@router.get("", response_model=List[Skill])
async def list_installed_skills():
    return load_installed_skills()


@router.get("/search")
async def search_clawhub_skills(q: Optional[str] = None, tag: Optional[str] = None):
    mock_skills = [
        Skill(
            id="skill-hr-policy-cn",
            name="hr-policy-generator-cn",
            version="1.0.0",
            description="综合性 HR 政策设计工具，覆盖考勤、休假、加班、远程办公及合规要求",
            author="hr-policy",
            tags=["hr", "人力资源", "考勤", "休假", "加班", "合规"],
            installed=False
        ),
        Skill(
            id="skill-code-review",
            name="code-review-assistant",
            version="1.0.0",
            description="代码审查助手，提供代码质量分析、漏洞检测和优化建议",
            author="dev-tools",
            tags=["代码审查", "质量分析", "安全"],
            installed=False
        ),
        Skill(
            id="skill-data-analyst",
            name="data-analyst",
            version="1.0.0",
            description="数据分析助手，支持数据清洗、统计分析和可视化建议",
            author="data-team",
            tags=["数据分析", "统计", "可视化"],
            installed=False
        ),
        Skill(
            id="skill-customer-service",
            name="customer-service-bot",
            version="1.0.0",
            description="客服机器人，支持常见问题解答和工单处理",
            author="support-team",
            tags=["客服", "问答", "工单"],
            installed=False
        ),
        Skill(
            id="skill-content-writer",
            name="content-writer",
            version="1.0.0",
            description="内容写作助手，支持文章创作、编辑和校对",
            author="content-team",
            tags=["写作", "编辑", "内容创作"],
            installed=False
        ),
    ]

    results = mock_skills
    if q:
        q_lower = q.lower()
        results = [s for s in results if q_lower in s.name.lower() or q_lower in (s.description or "").lower()]
    if tag:
        results = [s for s in results if tag.lower() in [t.lower() for t in s.tags]]

    installed = load_installed_skills()
    installed_ids = {s.name for s in installed}

    for skill in results:
        if skill.name in installed_ids:
            skill.installed = True

    return results


@router.get("/{skill_id}/preview")
async def preview_skill(skill_id: str):
    skills = load_installed_skills()
    skill = next((s for s in skills if s.id == skill_id), None)

    if not skill:
        mock_skills = {
            "skill-hr-policy-cn": """---
name: hr-policy-generator-cn
version: 1.0.0
description: "综合性 HR 政策设计工具，覆盖考勤、休假、加班、远程办公及合规要求"
author: "hr-policy"
tags:
  - hr
  - 人力资源
invocable: true
---

# 人力资源政策生成器（中文版）

## 描述
综合性 HR 政策设计工具...

## 输入
| 名称 | 类型 | 必填 |
|------|------|------|
| company_size | text | 是 |

## 输出
生成的完整 HR 政策文档
"""
        }
        content = mock_skills.get(skill_id, "Skill preview not available")
    else:
        skill_path = os.path.join(INSTALLED_SKILLS_PATH, skill.name)
        skill_md_path = os.path.join(skill_path, "SKILL.md")
        if os.path.exists(skill_md_path):
            with open(skill_md_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = "Skill files not found"

    return {"skill_id": skill_id, "preview": content}


@router.post("/{skill_id}/install", response_model=Skill)
async def install_skill(skill_id: str, request: Optional[InstallToRoleRequest] = None):
    skills = load_installed_skills()
    skill = next((s for s in skills if s.id == skill_id), None)

    if not skill:
        skill = Skill(
            id=skill_id,
            name=skill_id.replace("skill-", ""),
            version="1.0.0",
            description="Installed from ClawHub",
            installed=True,
            installed_at=datetime.now()
        )
        skills.append(skill)
    else:
        skill.installed = True
        skill.installed_at = datetime.now()

    skill_path = os.path.join(INSTALLED_SKILLS_PATH, skill.name)
    os.makedirs(skill_path, exist_ok=True)

    skill_md_content = f"""---
name: {skill.name}
version: {skill.version}
description: "{skill.description}"
author: "{skill.author or 'unknown'}"
tags:
{chr(10).join([f'  - {t}' for t in skill.tags])}
invocable: true
---

# {skill.name}

{skill.description}
"""

    with open(os.path.join(skill_path, "SKILL.md"), 'w', encoding='utf-8') as f:
        f.write(skill_md_content)

    skill.local_path = skill_path

    if request and request.role_id:
        if request.role_id not in skill.installed_roles:
            skill.installed_roles.append(request.role_id)

    save_installed_skills(skills)
    logger.info(f"Installed skill: {skill.name} (id={skill_id})")
    return skill


@router.delete("/{skill_id}/uninstall", status_code=status.HTTP_204_NO_CONTENT)
async def uninstall_skill(skill_id: str):
    skills = load_installed_skills()
    skill = next((s for s in skills if s.id == skill_id), None)

    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    import shutil
    if skill.local_path and os.path.exists(skill.local_path):
        shutil.rmtree(skill.local_path)

    skills = [s for s in skills if s.id != skill_id]
    save_installed_skills(skills)
    logger.info(f"Uninstalled skill: {skill.name} (id={skill_id})")


@router.post("/{skill_id}/install/{role_id}", response_model=Skill)
async def install_skill_to_role(skill_id: str, role_id: str):
    skills = load_installed_skills()
    skill = next((s for s in skills if s.id == skill_id), None)

    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    if role_id not in skill.installed_roles:
        skill.installed_roles.append(role_id)
        save_installed_skills(skills)
        logger.info(f"Assigned skill {skill.name} to role={role_id}")

    return skill


@router.delete("/{skill_id}/uninstall/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def uninstall_skill_from_role(skill_id: str, role_id: str):
    skills = load_installed_skills()
    skill = next((s for s in skills if s.id == skill_id), None)

    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    if role_id in skill.installed_roles:
        skill.installed_roles.remove(role_id)
        save_installed_skills(skills)
        logger.info(f"Removed skill {skill.name} from role={role_id}")


@router.get("/role/{role_id}", response_model=List[Skill])
async def get_role_skills(role_id: str):
    skills = load_installed_skills()
    return [s for s in skills if role_id in s.installed_roles]
