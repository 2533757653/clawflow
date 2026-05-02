from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel
import os
import re
import logging

logger = logging.getLogger(__name__)
import shutil
import subprocess
from datetime import datetime

from api.models import Role

router = APIRouter()

AGENCY_REPO_PATH = "data/agency-agents"
AGENCY_GITHUB_URL = "https://github.com/msitarzewski/agency-agents.git"


class AgencyImportRequest(BaseModel):
    divisions: Optional[List[str]] = None
    agent_names: Optional[List[str]] = None


class AgencyImportResponse(BaseModel):
    imported_count: int
    skipped_count: int
    roles: List[Role]
    errors: List[str]


def parse_frontmatter(content: str) -> tuple[dict, str]:
    frontmatter = {}
    body = content

    fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
    if fm_match:
        fm_text = fm_match.group(1)
        body = fm_match.group(2)

        for line in fm_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                if key and value:
                    frontmatter[key.lower()] = value

    return frontmatter, body


def extract_agency_content(markdown_content: str) -> dict:
    frontmatter, body = parse_frontmatter(markdown_content)

    responsibilities = []

    core_mission_match = re.search(r'## Core Mission\s*\n(.*?)(?=\n##|\Z)', body, re.DOTALL | re.IGNORECASE)
    if core_mission_match:
        mission_text = core_mission_match.group(1).strip()
        responsibilities.append(mission_text[:200])

    critical_rules = []
    rules_match = re.findall(r'(?:^|\n)#{1,3}\s*(?:Critical Rules?|When to Use|Technical Deliverables|Workflow Process)[s]?\s*\n(.*?)(?=\n##|\Z)', body, re.DOTALL | re.IGNORECASE)
    for rule in rules_match[:3]:
        cleaned = rule.strip()[:300]
        if cleaned:
            critical_rules.append(cleaned)

    return {
        'name': frontmatter.get('name', 'Unknown Agent'),
        'specialty': frontmatter.get('specialty', ''),
        'division': frontmatter.get('division', 'General'),
        'description': frontmatter.get('description', ''),
        'responsibilities': responsibilities + critical_rules,
        'body': body
    }


def clone_agency_repo() -> bool:
    if os.path.exists(AGENCY_REPO_PATH):
        return True

    try:
        subprocess.run(
            ['git', 'clone', '--depth', '1', AGENCY_GITHUB_URL, AGENCY_REPO_PATH],
            capture_output=True,
            check=True,
            timeout=120
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def scan_agency_agents() -> List[str]:
    agents_dir = os.path.join(AGENCY_REPO_PATH)
    if not os.path.exists(agents_dir):
        return []

    divisions = []
    for item in os.listdir(agents_dir):
        item_path = os.path.join(agents_dir, item)
        if os.path.isdir(item_path) and not item.startswith('.'):
            divisions.append(item)

    return sorted(divisions)


def get_agents_from_division(division: str) -> List[dict]:
    division_path = os.path.join(AGENCY_REPO_PATH, division)
    if not os.path.exists(division_path):
        return []

    agents = []
    for filename in os.listdir(division_path):
        if filename.endswith('.md') and not filename.startswith('README'):
            filepath = os.path.join(division_path, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            parsed = extract_agency_content(content)
            parsed['file_path'] = filepath
            parsed['division'] = division
            agents.append(parsed)

    return agents


def build_soul_template(agent_data: dict) -> str:
    name = agent_data.get('name', 'Unknown')
    specialty = agent_data.get('specialty', '')
    division = agent_data.get('division', 'General')
    description = agent_data.get('description', '')
    body = agent_data.get('body', '')

    core_mission_match = re.search(r'## Core Mission\s*\n(.*?)(?=\n##|\Z)', body, re.DOTALL | re.IGNORECASE)
    core_mission = core_mission_match.group(1).strip() if core_mission_match else ''

    critical_rules_match = re.search(r'## Critical Rules\s*\n(.*?)(?=\n##|\Z)', body, re.DOTALL | re.IGNORECASE)
    critical_rules = critical_rules_match.group(1).strip() if critical_rules_match else ''

    workflow_match = re.search(r'## Workflow Process\s*\n(.*?)(?=\n##|\Z)', body, re.DOTALL | re.IGNORECASE)
    workflow = workflow_match.group(1).strip() if workflow_match else ''

    soul = f"""# SOUL.md - {name}

## Identity

{name} from {division} division.

{specialty}

## Core Mission

{core_mission}

## Critical Rules

{critical_rules}

## Workflow

{workflow}

## Description

{description}
"""
    return soul.strip()


def build_identity_template(agent_data: dict) -> str:
    name = agent_data.get('name', 'Unknown')
    specialty = agent_data.get('specialty', '')
    division = agent_data.get('division', 'General')

    return f"""# IDENTITY.md - {name}

**Division:** {division}
**Specialty:** {specialty}

## Who Am I

{name} - {specialty}

## Voice & Tone

Professional, specialized, deliverable-focused.
""".strip()


@router.post("/import", response_model=AgencyImportResponse)
async def import_from_agency(request: AgencyImportRequest = None):
    if not clone_agency_repo():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clone agency-agents repository. Please ensure git is installed."
        )

    available_divisions = scan_agency_agents()
    if not available_divisions:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No agent divisions found in repository."
        )

    target_divisions = request.divisions if request and request.divisions else available_divisions
    target_names = request.agent_names if request and request.agent_names else None

    all_agents = []
    for division in target_divisions:
        if division in available_divisions:
            all_agents.extend(get_agents_from_division(division))

    if target_names:
        all_agents = [a for a in all_agents if a['name'] in target_names]

    from api.services import StorageService
    role_storage = StorageService[Role]("data/roles", Role)
    existing_roles = role_storage.list()
    existing_names = {r.name for r in existing_roles}

    imported_roles = []
    skipped = 0
    errors = []

    for agent in all_agents:
        try:
            if agent['name'] in existing_names:
                skipped += 1
                continue

            soul = build_soul_template(agent)
            identity = build_identity_template(agent)

            role = Role(
                name=agent['name'],
                description=agent.get('description', '')[:500],
                responsibilities=agent.get('responsibilities', [])[:5],
                division=agent.get('division', 'General'),
                soul_template=soul,
                identity_template=identity,
                source="agency-agents"
            )

            saved_role = role_storage.save(role)
            imported_roles.append(saved_role)
            existing_names.add(role.name)

        except Exception as e:
            errors.append(f"Failed to import {agent.get('name', 'unknown')}: {str(e)}")

    return AgencyImportResponse(
        imported_count=len(imported_roles),
        skipped_count=skipped,
        roles=imported_roles,
        errors=errors
    )


@router.get("/divisions", response_model=List[str])
async def get_agency_divisions():
    if not clone_agency_repo():
        return []

    return scan_agency_agents()


@router.get("/divisions/{division}/agents")
async def get_division_agents(division: str):
    if not clone_agency_repo():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clone agency-agents repository."
        )

    available = scan_agency_agents()
    if division not in available:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Division '{division}' not found. Available: {available}"
        )

    agents = get_agents_from_division(division)
    return [
        {
            "name": a['name'],
            "specialty": a.get('specialty', ''),
            "description": a.get('description', ''),
            "division": a.get('division', division)
        }
        for a in agents
    ]


@router.get("/status")
async def get_agency_status():
    is_cloned = os.path.exists(AGENCY_REPO_PATH)
    is_updated = False

    if is_cloned:
        try:
            result = subprocess.run(
                ['git', '-C', AGENCY_REPO_PATH, 'rev-parse', 'HEAD'],
                capture_output=True,
                text=True,
                timeout=10
            )
            is_updated = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as e:
            logger.warning(f"Failed to check agency repo status: {e}")
            is_updated = False

    divisions = scan_agency_agents() if is_cloned else []

    return {
        "is_cloned": is_cloned,
        "is_updated": is_updated,
        "repo_path": AGENCY_REPO_PATH,
        "divisions_count": len(divisions),
        "divisions": divisions
    }


@router.post("/sync")
async def sync_agency_repo():
    if os.path.exists(AGENCY_REPO_PATH):
        try:
            subprocess.run(
                ['git', '-C', AGENCY_REPO_PATH, 'pull', 'origin', 'main'],
                capture_output=True,
                check=True,
                timeout=60
            )
            return {"message": "Repository synced successfully"}
        except subprocess.CalledProcessError as e:
            return {"error": f"Sync failed: {e.stderr}"}

    if clone_agency_repo():
        return {"message": "Repository cloned successfully"}

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to sync or clone repository"
    )
