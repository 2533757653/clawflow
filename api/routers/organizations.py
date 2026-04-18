from fastapi import APIRouter, HTTPException, status
from typing import List
from api.models import Organization, OrganizationStatus
from api.services import StorageService, OrganizationService, OpenClawAdapter

router = APIRouter()

org_storage = StorageService[Organization]("data/organizations", Organization)
org_service = OrganizationService()
adapter = OpenClawAdapter()


@router.get("", response_model=List[Organization])
async def list_organizations():
    return org_storage.list()


@router.post("", response_model=Organization, status_code=status.HTTP_201_CREATED)
async def create_organization(org: Organization):
    existing = [o for o in org_storage.list() if o.name == org.name]
    if existing:
        raise HTTPException(status_code=400, detail="Organization with this name already exists")
    org.status = OrganizationStatus.DRAFT
    result = org_storage.save(org)
    org_service.create_organization_dirs(org.id)
    return result


@router.get("/{org_id}", response_model=Organization)
async def get_organization(org_id: str):
    org = org_storage.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.put("/{org_id}", response_model=Organization)
async def update_organization(org_id: str, org: Organization):
    existing = org_storage.get(org_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Organization not found")
    org.id = org_id
    return org_storage.save(org)


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(org_id: str):
    if not org_storage.delete(org_id):
        raise HTTPException(status_code=404, detail="Organization not found")
    org_service.delete_organization_dirs(org_id)
    adapter.undeploy_organization(org_id)


@router.post("/{org_id}/deploy")
async def deploy_organization(org_id: str):
    org = org_storage.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    from api.services import StorageService
    from api.models import Role, Knowledge

    role_storage = StorageService[Role](f"data/organizations/{org_id}/roles", Role)
    knowledge_storage = StorageService[Knowledge](f"data/organizations/{org_id}/knowledge", Knowledge)

    roles = role_storage.list()
    knowledge = knowledge_storage.list()

    deployed_agents = []
    for role in roles:
        adapter.deploy_role(org_id, role, knowledge)
        deployed_agents.append({
            "role_id": role.id,
            "role_name": role.name,
            "deployed_at": "now"
        })

    org.status = OrganizationStatus.DEPLOYED
    org_storage.save(org)

    return {
        "message": "Organization deployed successfully",
        "deployed_agents": deployed_agents,
        "total_roles": len(roles)
    }


@router.post("/{org_id}/undeploy")
async def undeploy_organization(org_id: str):
    org = org_storage.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    adapter.undeploy_organization(org_id)
    org.status = OrganizationStatus.DRAFT
    org_storage.save(org)

    return {"message": "Organization undeployed successfully"}
