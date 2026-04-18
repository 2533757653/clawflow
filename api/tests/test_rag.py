import pytest
from fastapi.testclient import TestClient


class TestRAGAPI:
    def test_list_documents_empty(self, test_client):
        response = test_client.get("/api/v1/rag/documents")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_document(self, test_client):
        doc_data = {
            "title": "Test Document",
            "content": "This is test content for the document"
        }
        response = test_client.post("/api/v1/rag/documents", json=doc_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Document"
        assert data["status"] == "pending"

    def test_get_document(self, test_client):
        doc_data = {
            "title": "Get Test Document",
            "content": "Content here"
        }
        create_response = test_client.post("/api/v1/rag/documents", json=doc_data)
        doc_id = create_response.json()["id"]

        response = test_client.get(f"/api/v1/rag/documents/{doc_id}")
        assert response.status_code == 200
        assert response.json()["title"] == "Get Test Document"

    def test_get_nonexistent_document(self, test_client):
        response = test_client.get("/api/v1/rag/documents/nonexistent-id")
        assert response.status_code == 404

    def test_delete_document(self, test_client):
        doc_data = {
            "title": "Delete Test Document",
            "content": "Content to delete"
        }
        create_response = test_client.post("/api/v1/rag/documents", json=doc_data)
        doc_id = create_response.json()["id"]

        response = test_client.delete(f"/api/v1/rag/documents/{doc_id}")
        assert response.status_code == 204

    def test_index_document(self, test_client):
        doc_data = {
            "title": "Index Test Document",
            "content": "Content to be indexed"
        }
        create_response = test_client.post("/api/v1/rag/documents", json=doc_data)
        doc_id = create_response.json()["id"]

        response = test_client.post(f"/api/v1/rag/documents/{doc_id}/index?chunk_size=100&overlap=20")
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == doc_id
        assert "chunks_created" in data

    def test_get_document_chunks(self, test_client):
        doc_data = {
            "title": "Chunks Test Document",
            "content": "This is a longer piece of content that should produce multiple chunks when indexed properly."
        }
        create_response = test_client.post("/api/v1/rag/documents", json=doc_data)
        doc_id = create_response.json()["id"]

        test_client.post(f"/api/v1/rag/documents/{doc_id}/index")

        response = test_client.get(f"/api/v1/rag/documents/{doc_id}/chunks")
        assert response.status_code == 200
        chunks = response.json()
        assert isinstance(chunks, list)

    def test_query_rag(self, test_client):
        doc_data = {
            "title": "Query Test Document",
            "content": "Machine learning is a subset of artificial intelligence"
        }
        create_response = test_client.post("/api/v1/rag/documents", json=doc_data)
        doc_id = create_response.json()["id"]

        test_client.post(f"/api/v1/rag/documents/{doc_id}/index")

        query_data = {
            "query": "What is machine learning?",
            "top_k": 5
        }
        response = test_client.post("/api/v1/rag/query", json=query_data)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total_chunks" in data
        assert "processing_time_ms" in data

    def test_simple_query(self, test_client):
        response = test_client.post("/api/v1/rag/query/simple?query=test&top_k=3")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    def test_get_rag_stats(self, test_client):
        response = test_client.get("/api/v1/rag/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_documents" in data
        assert "total_chunks" in data
        assert "total_embeddings" in data

    def test_reindex_all(self, test_client):
        response = test_client.post("/api/v1/rag/reindex-all")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "stats" in data
