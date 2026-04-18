from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from api.models.rag_models import (
    Document, DocumentStatus, DocumentType,
    Chunk, RAGQuery, RAGResponse, RAGResult
)
from api.services.rag_service import RAGService

router = APIRouter()
rag_service = RAGService()


@router.get("/documents", response_model=List[Document])
async def list_documents(
    organization_id: Optional[str] = None,
    doc_type: Optional[DocumentType] = None
):
    return rag_service.doc_service.list(organization_id, doc_type)


@router.post("/documents", response_model=Document, status_code=status.HTTP_201_CREATED)
async def create_document(doc: Document):
    doc.status = DocumentStatus.PENDING
    return rag_service.doc_service.save(doc)


@router.get("/documents/{doc_id}", response_model=Document)
async def get_document(doc_id: str):
    doc = rag_service.doc_service.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(doc_id: str):
    rag_service.chunk_service.delete_by_document(doc_id)
    if not rag_service.doc_service.delete(doc_id):
        raise HTTPException(status_code=404, detail="Document not found")


@router.post("/documents/{doc_id}/index")
async def index_document(doc_id: str, chunk_size: int = 500, overlap: int = 50):
    doc = rag_service.doc_service.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks = rag_service.index_document(doc, chunk_size, overlap)
    return {
        "message": "Document indexed successfully",
        "document_id": doc_id,
        "chunks_created": len(chunks)
    }


@router.get("/documents/{doc_id}/chunks", response_model=List[Chunk])
async def get_document_chunks(doc_id: str):
    return rag_service.chunk_service.list_by_document(doc_id)


@router.post("/query", response_model=RAGResponse)
async def query_rag(rag_query: RAGQuery):
    return rag_service.query(rag_query)


@router.post("/query/simple")
async def simple_query(query: str, top_k: int = 5, organization_id: Optional[str] = None):
    rag_query = RAGQuery(
        query=query,
        top_k=top_k,
        organization_id=organization_id
    )
    return rag_service.query(rag_query)


@router.post("/index/knowledge-base/{org_id}")
async def index_knowledge_base(org_id: str):
    from api.services.storage import StorageService
    from api.models import Knowledge

    knowledge_storage = StorageService[Knowledge](f"data/organizations/{org_id}/knowledge", Knowledge)
    knowledge_items = knowledge_storage.list()

    items = [
        {
            "title": kb.title,
            "content": kb.content,
            "category": kb.category,
            "tags": kb.tags
        }
        for kb in knowledge_items
    ]

    count = rag_service.index_knowledge_base(org_id, items)

    return {
        "message": "Knowledge base indexed successfully",
        "organization_id": org_id,
        "documents_created": count
    }


@router.post("/index/spec")
async def index_spec():
    try:
        with open("SPEC.md", "r", encoding="utf-8") as f:
            spec_content = f.read()

        chunks = rag_service.index_spec(spec_content)

        return {
            "message": "Specification indexed successfully",
            "chunks_created": len(chunks)
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="SPEC.md not found")


@router.get("/stats")
async def get_rag_stats():
    return rag_service.get_stats()


@router.post("/reindex-all")
async def reindex_all():
    rag_service.vector_store.clear()
    rag_service._load_embeddings()

    return {
        "message": "Vector store reloaded",
        "stats": rag_service.get_stats()
    }