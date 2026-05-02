import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from api.services.hr_agent_service import HRAgentService

logger = logging.getLogger(__name__)

router = APIRouter()
hr_service = HRAgentService()


class SuggestResponsibilitiesRequest(BaseModel):
    name: str
    description: Optional[str] = None
    division: Optional[str] = None
    hierarchy_level: int = 1


class SuggestResponsibilitiesResponse(BaseModel):
    responsibilities: List[str]
    confidence: float


class GenerateSoulRequest(BaseModel):
    name: str
    description: Optional[str] = None
    division: Optional[str] = None
    responsibilities: List[str]


class GenerateSoulResponse(BaseModel):
    soul_template: str


class SuggestDivisionRequest(BaseModel):
    name: str
    description: str


class SuggestDivisionResponse(BaseModel):
    suggested_division: Optional[str]
    alternatives: List[str]


class ApplySuggestionsRequest(BaseModel):
    role_id: str
    responsibilities: Optional[List[str]] = None
    soul_template: Optional[str] = None


@router.post("/suggest-responsibilities", response_model=SuggestResponsibilitiesResponse)
async def suggest_responsibilities(request: SuggestResponsibilitiesRequest):
    """
    建议角色职责:
    基于部门、层级和描述生成职责建议
    """
    responsibilities = hr_service.suggest_responsibilities(
        name=request.name,
        description=request.description,
        division=request.division,
        hierarchy_level=request.hierarchy_level
    )

    confidence = 0.5
    if request.division:
        confidence += 0.3
    if request.description:
        confidence += 0.2

    result = SuggestResponsibilitiesResponse(
        responsibilities=responsibilities,
        confidence=min(1.0, confidence)
    )
    logger.info(f"Suggested responsibilities for role={request.name!r}: {len(responsibilities)} items")
    return result


@router.post("/generate-soul", response_model=GenerateSoulResponse)
async def generate_soul(request: GenerateSoulRequest):
    """
    生成 SOUL.md 模板:
    基于角色信息生成 soul_template
    """
    soul_template = hr_service.generate_soul_template(
        name=request.name,
        description=request.description,
        division=request.division,
        responsibilities=request.responsibilities
    )

    logger.info(f"Generated soul template for role={request.name!r}")
    return GenerateSoulResponse(soul_template=soul_template)


@router.post("/suggest-division", response_model=SuggestDivisionResponse)
async def suggest_division(request: SuggestDivisionRequest):
    """
    建议部门:
    基于名称和描述推断适合的部门
    """
    suggested = hr_service.suggest_division(
        name=request.name,
        description=request.description
    )

    alternatives = ["Engineering", "Product", "Design", "Operations"]
    if suggested and suggested in alternatives:
        alternatives.remove(suggested)

    logger.info(f"Suggested division for role={request.name!r}: {suggested}")
    return SuggestDivisionResponse(
        suggested_division=suggested,
        alternatives=alternatives[:3]
    )


@router.post("/apply-suggestions")
async def apply_suggestions(request: ApplySuggestionsRequest):
    """
    应用建议到角色:
    将建议的 responsibilities 和 soul_template 应用到角色
    """
    from api.services import StorageService
    from api.models import Role

    role_storage = StorageService[Role]("data/roles", Role)
    role = role_storage.get(request.role_id)

    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    if request.responsibilities:
        role.responsibilities = request.responsibilities

    if request.soul_template:
        role.soul_template = request.soul_template

    role_storage.save(role)
    logger.info(f"Applied suggestions to role: id={role.id}")
    return {"message": "Suggestions applied successfully", "role_id": role.id}