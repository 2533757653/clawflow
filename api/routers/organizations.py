import logging
from fastapi import APIRouter, HTTPException, status
from typing import List
from api.models import Organization, OrganizationStatus, Role
from api.services import StorageService, OrganizationService, OpenClawAdapter

logger = logging.getLogger(__name__)

router = APIRouter()

org_storage = StorageService[Organization]("data/organizations", Organization)
org_service = OrganizationService()
adapter = OpenClawAdapter()
role_storage = StorageService[Role]("data/roles", Role)


@router.get("", response_model=List[Organization])
async def list_organizations():
    return org_storage.list()


@router.post("", response_model=Organization, status_code=status.HTTP_201_CREATED)
async def create_organization(org: Organization):
    existing = [o for o in org_storage.list() if o.name == org.name]
    if existing:
        logger.warning(f"Duplicate organization name: {org.name}")
        raise HTTPException(status_code=400, detail="Organization with this name already exists")
    org.status = OrganizationStatus.DRAFT
    result = org_storage.save(org)
    org_service.create_organization_dirs(org.id)
    logger.info(f"Created organization: {org.name} (id={org.id})")
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
    saved = org_storage.save(org)
    logger.info(f"Updated organization: {saved.name} (id={org_id})")
    return saved


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(org_id: str):
    if not org_storage.delete(org_id):
        raise HTTPException(status_code=404, detail="Organization not found")
    org_service.delete_organization_dirs(org_id)
    logger.info(f"Deleted organization: {org_id}")


@router.post("/{org_id}/deploy")
async def deploy_organization(org_id: str):
    org = org_storage.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if not org.role_ids:
        raise HTTPException(status_code=400, detail="Organization has no roles to deploy")

    all_roles = role_storage.list()
    org_roles = [r for r in all_roles if r.id in org.role_ids]

    if not org_roles:
        raise HTTPException(status_code=400, detail="No valid roles found in organization")

    deployed_agents = []
    for role in org_roles:
        skills = role.required_skills or []
        adapter.deploy_role(role, skills)
        deployed_agents.append({
            "role_id": role.id,
            "role_name": role.name,
            "deployed_at": "now"
        })
        logger.debug(f"Deployed role: {role.name}")

    org.status = OrganizationStatus.DEPLOYED
    org_storage.save(org)
    logger.info(f"Organization deployed: {org.name} ({len(org_roles)} roles)")

    return {
        "message": "Organization deployed successfully",
        "deployed_agents": deployed_agents,
        "total_roles": len(org_roles)
    }


@router.post("/{org_id}/start")
async def start_organization(org_id: str):
    org = org_storage.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    if org.status != OrganizationStatus.DEPLOYED:
        raise HTTPException(status_code=400, detail="Organization must be deployed before starting")
    org.status = OrganizationStatus.RUNNING
    org_storage.save(org)
    logger.info(f"Organization started: {org.name}")
    return {"message": "Organization started successfully"}


@router.post("/{org_id}/stop")
async def stop_organization(org_id: str):
    org = org_storage.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    if org.status != OrganizationStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Organization must be running to stop")
    org.status = OrganizationStatus.STOPPED
    org_storage.save(org)
    logger.info(f"Organization stopped: {org.name}")
    return {"message": "Organization stopped successfully"}


@router.post("/{org_id}/rollback")
async def rollback_organization(org_id: str):
    """Undeploy all agents and set organization status back to draft."""
    org = org_storage.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    all_roles = role_storage.list()
    org_roles = [r for r in all_roles if r.id in org.role_ids]

    undeployed = []
    for role in org_roles:
        result = adapter.undeploy_role(role.name)
        undeployed.append({"role_name": role.name, "undeployed": result})

    org.status = OrganizationStatus.DRAFT
    org_storage.save(org)
    logger.info(f"Organization rolled back: {org.name} ({len(org_roles)} roles)")

    return {
        "message": "Organization rolled back successfully",
        "undeployed_agents": undeployed,
        "total_roles": len(org_roles)
    }
