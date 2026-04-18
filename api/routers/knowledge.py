from fastapi import APIRouter, HTTPException, status
from typing import List
from api.models import Knowledge
from api.services import StorageService

router = APIRouter()


def get_knowledge_storage(org_id: str) -> StorageService[Knowledge]:
    return StorageService[Knowledge](f"data/organizations/{org_id}/knowledge", Knowledge)


@router.get("/{org_id}/knowledge", response_model=List[Knowledge])
async def list_knowledge(org_id: str):
    storage = get_knowledge_storage(org_id)
    return storage.list()


@router.post("/{org_id}/knowledge", response_model=Knowledge, status_code=status.HTTP_201_CREATED)
async def create_knowledge(org_id: str, knowledge: Knowledge):
    knowledge.organization_id = org_id
    storage = get_knowledge_storage(org_id)
    return storage.save(knowledge)


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
    return storage.save(knowledge)


@router.delete("/{org_id}/knowledge/{knowledge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge(org_id: str, knowledge_id: str):
    storage = get_knowledge_storage(org_id)
    if not storage.delete(knowledge_id):
        raise HTTPException(status_code=404, detail="Knowledge not found")


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
    return results
