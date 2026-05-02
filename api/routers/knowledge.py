import logging
from fastapi import APIRouter, HTTPException, status
from typing import List
from pydantic import BaseModel
from api.models import Knowledge
from api.services import StorageService

logger = logging.getLogger(__name__)

router = APIRouter()


class PromptInjectionRequest(BaseModel):
    base_prompt: str
    include_knowledge: bool = True
    max_knowledge_items: int = 5


class PromptInjectionResponse(BaseModel):
    enhanced_prompt: str
    knowledge_used: List[dict]


def get_knowledge_storage(org_id: str) -> StorageService[Knowledge]:
    return StorageService[Knowledge](f"data/organizations/{org_id}/knowledge", Knowledge)


def build_prompt_with_knowledge(base_prompt: str, knowledge_items: List[Knowledge], max_items: int = 5) -> tuple[str, List[dict]]:
    if not knowledge_items:
        return base_prompt, []

    selected = knowledge_items[:max_items]
    knowledge_context = "\n\n## 相关知识库内容\n"

    used_knowledge = []
    for i, kb in enumerate(selected, 1):
        knowledge_context += f"\n### {i}. {kb.title}\n"
        if kb.category:
            knowledge_context += f"分类: {kb.category}\n"
        knowledge_context += f"{kb.content}\n"
        used_knowledge.append({
            "id": kb.id,
            "title": kb.title,
            "category": kb.category,
            "preview": kb.content[:100] + "..." if len(kb.content) > 100 else kb.content
        })

    if base_prompt:
        enhanced = f"{base_prompt}\n{knowledge_context}"
    else:
        enhanced = f"请根据以下知识回答问题：\n{knowledge_context}"

    return enhanced, used_knowledge


@router.get("/{org_id}/knowledge", response_model=List[Knowledge])
async def list_knowledge(org_id: str):
    storage = get_knowledge_storage(org_id)
    return storage.list()


@router.post("/{org_id}/knowledge", response_model=Knowledge, status_code=status.HTTP_201_CREATED)
async def create_knowledge(org_id: str, knowledge: Knowledge):
    knowledge.organization_id = org_id
    storage = get_knowledge_storage(org_id)
    saved = storage.save(knowledge)
    logger.info(f"Created knowledge: {knowledge.title} (id={saved.id}) in org={org_id}")
    return saved


@router.get("/{org_id}/knowledge/{knowledge_id}", response_model=Knowledge)
async def get_knowledge(org_id: str, knowledge_id: str):
    storage = get_knowledge_storage(org_id)
    knowledge = storage.get(knowledge_id)
    if not knowledge:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    return knowledge


@router.put("/{org_id}/knowledge/{knowledge_id}", response_model=Knowledge)
async def update_knowledge(org_id: str, knowledge_id: str, knowledge: Knowledge):
    storage = get_knowledge_storage(org_id)
    existing = storage.get(knowledge_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    knowledge.id = knowledge_id
    knowledge.organization_id = org_id
    knowledge.version = existing.version + 1
    saved = storage.save(knowledge)
    logger.info(f"Updated knowledge: {knowledge.title} (id={knowledge_id}, v{saved.version})")
    return saved


@router.delete("/{org_id}/knowledge/{knowledge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge(org_id: str, knowledge_id: str):
    storage = get_knowledge_storage(org_id)
    if not storage.delete(knowledge_id):
        raise HTTPException(status_code=404, detail="Knowledge not found")
    logger.info(f"Deleted knowledge: id={knowledge_id} from org={org_id}")


@router.get("/{org_id}/knowledge/search")
async def search_knowledge(org_id: str, q: str):
    storage = get_knowledge_storage(org_id)
    all_knowledge = storage.list()
    query = q.lower()
    results = [
        kb for kb in all_knowledge
        if query in kb.title.lower() or query in kb.content.lower() or
           (kb.category and query in kb.category.lower()) or
           any(query in tag.lower() for tag in kb.tags)
    ]
    logger.info(f"Knowledge search in org={org_id}: q={q!r}, results={len(results)}")
    return results


@router.post("/{org_id}/knowledge/inject", response_model=PromptInjectionResponse)
async def inject_knowledge(
    org_id: str,
    request: PromptInjectionRequest
):
    storage = get_knowledge_storage(org_id)
    all_knowledge = storage.list()

    if not all_knowledge:
        return PromptInjectionResponse(
            enhanced_prompt=request.base_prompt,
            knowledge_used=[]
        )

    if request.include_knowledge:
        enhanced_prompt, used_knowledge = build_prompt_with_knowledge(
            request.base_prompt,
            all_knowledge,
            request.max_knowledge_items
        )
    else:
        enhanced_prompt = request.base_prompt
        used_knowledge = []

    logger.info(f"Knowledge injected in org={org_id}: {len(used_knowledge)} items used")
    return PromptInjectionResponse(
        enhanced_prompt=enhanced_prompt,
        knowledge_used=used_knowledge
    )


@router.post("/{org_id}/knowledge/inject/{knowledge_id}", response_model=PromptInjectionResponse)
async def inject_single_knowledge(
    org_id: str,
    knowledge_id: str,
    base_prompt: str
):
    storage = get_knowledge_storage(org_id)
    knowledge = storage.get(knowledge_id)

    if not knowledge:
        raise HTTPException(status_code=404, detail="Knowledge not found")

    enhanced_prompt, used_knowledge = build_prompt_with_knowledge(
        base_prompt,
        [knowledge],
        1
    )

    return PromptInjectionResponse(
        enhanced_prompt=enhanced_prompt,
        knowledge_used=used_knowledge
    )
