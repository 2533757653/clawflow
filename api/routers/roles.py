import logging
import os
import shutil
from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from api.models import Role, PermissionLevel
from api.services import StorageService
from api.services.agent_sync_service import AgentSyncService

logger = logging.getLogger(__name__)

router = APIRouter()

role_storage = StorageService[Role]("data/roles", Role)
agent_sync_service = AgentSyncService()


@router.get("", response_model=List[Role])
async def list_roles():
    return role_storage.list()


@router.post("", response_model=Role, status_code=status.HTTP_201_CREATED)
async def create_role(role: Role):
    existing = [r for r in role_storage.list() if r.name == role.name]
    if existing:
        logger.warning(f"Duplicate role name: {role.name}")
        raise HTTPException(status_code=400, detail="Role with this name already exists")
    role.permission_level = role.permission_level or PermissionLevel.MEMBER
    saved = role_storage.save(role)
    logger.info(f"Created role: {role.name} (id={saved.id})")
    return saved


@router.get("/{role_id}", response_model=Role)
async def get_role(role_id: str):
    role = role_storage.get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.put("/{role_id}", response_model=Role)
async def update_role(role_id: str, role: Role):
    existing = role_storage.get(role_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Role not found")

    old_name = existing.name
    name_changed = role.name != old_name

    if role.name != existing.name:
        name_conflict = [r for r in role_storage.list() if r.name == role.name and r.id != role_id]
        if name_conflict:
            raise HTTPException(status_code=400, detail="Role with this name already exists")

    role.id = role_id
    saved_role = role_storage.save(role)
    logger.info(f"Updated role: {saved_role.name} (id={role_id})")

    agent_sync_service.sync_role(saved_role)

    if name_changed:
        old_agent_path = os.path.join("agents", old_name.lower().replace(" ", "_"))
        new_agent_path = os.path.join("agents", saved_role.name.lower().replace(" ", "_"))

        if os.path.exists(old_agent_path):
            if os.path.exists(new_agent_path):
                agent_sync_service.sync_role(saved_role, force=True)
            else:
                try:
                    shutil.move(old_agent_path, new_agent_path)
                    agent_sync_service.sync_role(saved_role, force=True)
                    logger.info(f"Renamed agent directory: {old_name} -> {saved_role.name}")
                except Exception as e:
                    saved_role.name = old_name
                    role_storage.save(saved_role)
                    logger.error(f"Failed to rename agent directory: {e}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to rename agent directory: {str(e)}"
                    )

    return saved_role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(role_id: str):
    role = role_storage.get(role_id)
    if not role_storage.delete(role_id):
        raise HTTPException(status_code=404, detail="Role not found")
    logger.info(f"Deleted role: {role.name if role else role_id} (id={role_id})")


@router.get("/{role_id}/hierarchy")
async def get_role_hierarchy(role_id: str):
    role = role_storage.get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return build_hierarchy(role)


def build_hierarchy(r: Role, visited: set = None) -> dict:
    if visited is None:
        visited = set()
    if r.id in visited:
        return {"id": r.id, "name": r.name, "circular_reference": True}
    visited.add(r.id)

    children = [role_storage.get(rid) for rid in [r.id for r in role_storage.list()] if role_storage.get(rid).reports_to == r.id]
    children = [c for c in children if c]

    return {
        "id": r.id,
        "name": r.name,
        "description": r.description,
        "hierarchy_level": r.hierarchy_level,
        "permission_level": r.permission_level,
        "children": [build_hierarchy(child, visited.copy()) for child in children]
    }


@router.post("/sync-all")
async def sync_all_roles(role_ids: Optional[List[str]] = None):
    results = agent_sync_service.sync_all(role_ids)
    synced = [r for r in results if r["status"] == "synced"]
    skipped = [r for r in results if r["status"] == "skipped"]
    errors = [r for r in results if r["status"] == "error"]
    logger.info(f"Synced all roles: {len(synced)} synced, {len(skipped)} skipped, {len(errors)} errors")
    return {
        "total": len(results),
        "synced": len(synced),
        "skipped": len(skipped),
        "errors": len(errors),
        "details": results
    }


@router.post("/{role_id}/sync")
async def sync_single_role(role_id: str):
    role = role_storage.get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    result = agent_sync_service.sync_role(role)
    if result["status"] == "error":
        logger.error(f"Failed to sync role {role.name}: {result.get('error')}")
        raise HTTPException(status_code=500, detail=result.get("error"))
    logger.info(f"Synced role: {role.name}")
    return result
