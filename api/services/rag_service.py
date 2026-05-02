import os
import json
import time
import re
import math
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from api.models.rag_models import (
    Document, DocumentStatus, DocumentType,
    Chunk, ChunkEmbedding,
    RAGQuery, RAGResult, RAGResponse
)
from api.services.storage import StorageService

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self, storage_path: str = "data/rag/documents"):
        self.storage = StorageService[Document](storage_path, Document)

    def save(self, doc: Document) -> Document:
        doc.updated_at = datetime.now()
        return self.storage.save(doc)

    def get(self, doc_id: str) -> Optional[Document]:
        return self.storage.get(doc_id)

    def list(self, organization_id: Optional[str] = None,
             doc_type: Optional[DocumentType] = None) -> List[Document]:
        docs = self.storage.list()
        if organization_id:
            docs = [d for d in docs if d.organization_id == organization_id]
        if doc_type:
            docs = [d for d in docs if d.doc_type == doc_type]
        return docs

    def delete(self, doc_id: str) -> bool:
        return self.storage.delete(doc_id)

    def update_status(self, doc_id: str, status: DocumentStatus) -> Optional[Document]:
        doc = self.get(doc_id)
        if doc:
            doc.status = status
            return self.save(doc)
        return None


class ChunkService:
    def __init__(self, storage_path: str = "data/rag/chunks"):
        self.storage = StorageService[Chunk](storage_path, Chunk)

    def save(self, chunk: Chunk) -> Chunk:
        return self.storage.save(chunk)

    def get(self, chunk_id: str) -> Optional[Chunk]:
        return self.storage.get(chunk_id)

    def list_by_document(self, document_id: str) -> List[Chunk]:
        chunks = self.storage.list()
        return [c for c in chunks if c.document_id == document_id]

    def delete_by_document(self, document_id: str) -> None:
        chunks = self.list_by_document(document_id)
        for chunk in chunks:
            self.storage.delete(chunk.id)

    def chunk_text(self, text: str, chunk_size: int = 500,
                   overlap: int = 50) -> List[str]:
        if not text or len(text) == 0:
            return []

        sentences = self._split_into_sentences(text)
        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence)
            if current_length + sentence_length > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                overlap_words = ' '.join(current_chunk).split()[-overlap:]
                current_chunk = overlap_words + [sentence]
                current_length = sum(len(w) for w in current_chunk) + len(current_chunk)
            else:
                current_chunk.append(sentence)
                current_length += sentence_length

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        sentence_endings = re.compile(r'[。！？；\n\.!?;]')
        parts = sentence_endings.split(text)
        return [p.strip() for p in parts if p.strip()]

    def estimate_tokens(self, text: str) -> int:
        return math.ceil(len(text) / 4)


class EmbeddingService:
    def __init__(self, storage_path: str = "data/rag/embeddings",
                 model: str = "text-embedding-ada-002"):
        self.storage = StorageService[ChunkEmbedding](storage_path, ChunkEmbedding)
        self.model = model
        self._embedding_cache: Dict[str, List[float]] = {}
        self._openai_client = None

    def _get_openai_client(self):
        if self._openai_client is None:
            import os
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OPENAI_API_KEY environment variable not set")
                return None
            self._openai_client = OpenAI(api_key=api_key)
        return self._openai_client

    def get_embedding(self, text: str, use_cache: bool = True) -> List[float]:
        cache_key = text[:100]
        if use_cache and cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]

        embedding = self._generate_embedding(text)

        if use_cache:
            self._embedding_cache[cache_key] = embedding

        return embedding

    def _generate_embedding(self, text: str) -> List[float]:
        client = self._get_openai_client()
        if client:
            try:
                response = client.embeddings.create(
                    model=self.model,
                    input=text
                )
                return response.data[0].embedding
            except Exception as e:
                logger.warning(f"OpenAI API failed: {e}, using fallback")
        return self._fallback_embedding(text)

    def _fallback_embedding(self, text: str) -> List[float]:
        words = text.lower().split()
        dim = 1536
        vector = [0.0] * dim
        for word in words:
            idx = hash(word) % dim
            vector[idx] += 1
        norm = math.sqrt(sum(v*v for v in vector))
        if norm > 0:
            vector = [v/norm for v in vector]
        return vector

    def save(self, chunk_id: str, embedding: List[float]) -> ChunkEmbedding:
        chunk_emb = ChunkEmbedding(
            chunk_id=chunk_id,
            embedding=embedding,
            model=self.model
        )
        return self.storage.save(chunk_emb)

    def get(self, chunk_id: str) -> Optional[ChunkEmbedding]:
        embeddings = self.storage.list()
        for emb in embeddings:
            if emb.chunk_id == chunk_id:
                return emb
        return None

    def delete_by_chunk(self, chunk_id: str) -> bool:
        embeddings = self.storage.list()
        for emb in embeddings:
            if emb.chunk_id == chunk_id:
                self.storage.delete(emb.id)
                return True
        return False


class VectorStore:
    def __init__(self):
        self.embeddings: Dict[str, Tuple[str, List[float]]] = {}
        self.chunks: Dict[str, Chunk] = {}

    def add(self, chunk_id: str, document_id: str, embedding: List[float], chunk: Chunk):
        self.embeddings[chunk_id] = (document_id, embedding)
        self.chunks[chunk_id] = chunk

    def search(self, query_embedding: List[float], top_k: int = 5,
               filter_document_ids: Optional[List[str]] = None) -> List[Tuple[str, float]]:
        scores = []
        for chunk_id, (doc_id, embedding) in self.embeddings.items():
            if filter_document_ids and doc_id not in filter_document_ids:
                continue

            score = self._cosine_similarity(query_embedding, embedding)
            scores.append((chunk_id, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        if len(a) != len(b):
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def clear(self):
        self.embeddings.clear()
        self.chunks.clear()


class RAGService:
    def __init__(self):
        self.doc_service = DocumentService()
        self.chunk_service = ChunkService()
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self._load_embeddings()

    def _load_embeddings(self):
        chunks = self.chunk_service.storage.list()
        for chunk in chunks:
            emb = self.embedding_service.get(chunk.id)
            if emb:
                self.vector_store.add(chunk.id, chunk.document_id, emb.embedding, chunk)

    def index_document(self, doc: Document, chunk_size: int = 500,
                       overlap: int = 50) -> List[Chunk]:
        doc.status = DocumentStatus.PROCESSING
        self.doc_service.save(doc)

        self.chunk_service.delete_by_document(doc.id)
        chunks_data = self.chunk_service.chunk_text(doc.content, chunk_size, overlap)

        chunks = []
        for idx, content in enumerate(chunks_data):
            chunk = Chunk(
                document_id=doc.id,
                content=content,
                chunk_index=idx,
                token_count=self.chunk_service.estimate_tokens(content),
                metadata={"title": doc.title, "doc_type": doc.doc_type.value}
            )
            saved_chunk = self.chunk_service.save(chunk)

            embedding = self.embedding_service.get_embedding(content)
            self.embedding_service.save(saved_chunk.id, embedding)
            self.vector_store.add(saved_chunk.id, doc.id, embedding, saved_chunk)

            chunks.append(saved_chunk)

        doc.status = DocumentStatus.COMPLETED
        self.doc_service.save(doc)

        return chunks

    def query(self, rag_query: RAGQuery) -> RAGResponse:
        start_time = time.time()

        query_embedding = self.embedding_service.get_embedding(rag_query.query)

        filter_doc_ids = None
        if rag_query.organization_id:
            docs = self.doc_service.list(organization_id=rag_query.organization_id,
                                         doc_type=rag_query.doc_types[0] if rag_query.doc_types else None)
            filter_doc_ids = [d.id for d in docs]

        results = self.vector_store.search(
            query_embedding,
            top_k=rag_query.top_k,
            filter_document_ids=filter_doc_ids
        )

        rag_results = []
        for chunk_id, score in results:
            chunk = self.vector_store.chunks.get(chunk_id)
            if chunk:
                doc = self.doc_service.get(chunk.document_id)
                rag_results.append(RAGResult(
                    chunk_id=chunk_id,
                    document_id=chunk.document_id,
                    content=chunk.content,
                    score=score,
                    metadata={
                        "title": doc.title if doc else "Unknown",
                        "doc_type": chunk.metadata.get("doc_type", "unknown"),
                        "chunk_index": chunk.chunk_index
                    }
                ))

        processing_time = (time.time() - start_time) * 1000

        return RAGResponse(
            query=rag_query.query,
            results=rag_results,
            total_chunks=len(self.vector_store.embeddings),
            processing_time_ms=processing_time
        )

    def index_knowledge_base(self, organization_id: str,
                             knowledge_items: List[Dict[str, Any]]) -> int:
        count = 0
        for item in knowledge_items:
            doc = Document(
                organization_id=organization_id,
                title=item.get("title", "Untitled"),
                content=item.get("content", ""),
                doc_type=DocumentType.KNOWLEDGE,
                metadata={"category": item.get("category"), "tags": item.get("tags", [])}
            )
            self.index_document(doc)
            count += 1
        return count

    def index_spec(self, spec_content: str) -> List[Chunk]:
        doc = Document(
            title="ClawFlow Specification",
            content=spec_content,
            doc_type=DocumentType.SPEC,
            metadata={"source": "SPEC.md"}
        )
        return self.index_document(doc)

    def get_stats(self) -> Dict[str, Any]:
        docs = self.doc_service.storage.list()
        chunks = self.chunk_service.storage.list()

        status_counts = {}
        for doc in docs:
            status_counts[doc.status.value] = status_counts.get(doc.status.value, 0) + 1

        return {
            "total_documents": len(docs),
            "total_chunks": len(chunks),
            "total_embeddings": len(self.vector_store.embeddings),
            "documents_by_status": status_counts
        }