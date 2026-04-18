from fastapi import APIRouter, HTTPException, status
from typing import List
from api.models import Role, PermissionLevel
from api.services import StorageService

router = APIRouter()


def get_role_storage(org_id: str) -> StorageService[Role]:
    return StorageService[Role](f"data/organizations/{org_id}/roles", Role)


@router.get("/{org_id}/roles", response_model=List[Role])
async def list_roles(org_id: str):
    storage = get_role_storage(org_id)
    return storage.list()


@router.post("/{org_id}/roles", response_model=Role, status_code=status.HTTP_201_CREATED)
async def create_role(org_id: str, role: Role):
    role.organization_id = org_id
    role.permission_level = role.permission_level or PermissionLevel.MEMBER
    storage = get_role_storage(org_id)
    return storage.save(role)


@router.get("/{org_id}/roles/{role_id}", response_model=Role)
async def get_role(org_id: str, role_id: str):
    storage = get_role_storage(org_id)
    role = storage.get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.put("/{org_id}/roles/{role_id}", response_model=Role)
async def update_role(org_id: str, role_id: str, role: Role):
    storage = get_role_storage(org_id)
    existing = storage.get(role_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Role not found")
    role.id = role_id
    role.organization_id = org_id
    return storage.save(role)


@router.delete("/{org_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(org_id: str, role_id: str):
    storage = get_role_storage(org_id)
    if not storage.delete(role_id):
        raise HTTPException(status_code=404, detail="Role not found")


@router.get("/{org_id}/roles/{role_id}/hierarchy")
async def get_role_hierarchy(org_id: str, role_id: str):
    storage = get_role_storage(org_id)
    role = storage.get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    def build_hierarchy(r: Role, visited: set = None) -> dict:
        if visited is None:
            visited = set()
        if r.id in visited:
            return {"id": r.id, "name": r.name, "circular_reference": True}
        visited.add(r.id)

        children = [storage.get(rid) for rid in storage.list() if storage.get(rid).reports_to == r.id]
        children = [c for c in children if c]

        return {
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "hierarchy_level": r.hierarchy_level,
            "permission_level": r.permission_level,
            "children": [build_hierarchy(child, visited.copy()) for child in children]
        }

    return build_hierarchy(role)
