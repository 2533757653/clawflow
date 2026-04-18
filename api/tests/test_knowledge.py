import pytest
import uuid
from fastapi.testclient import TestClient


class TestKnowledgeAPI:
    def test_list_knowledge_empty(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"Knowledge Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        response = test_client.get(f"/api/v1/organizations/{org_id}/knowledge")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_knowledge(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"Knowledge Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        knowledge_data = {
            "organization_id": org_id,
            "title": "Test Knowledge",
            "content": "This is test knowledge content",
            "category": "testing"
        }
        response = test_client.post(f"/api/v1/organizations/{org_id}/knowledge", json=knowledge_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Knowledge"
        assert data["version"] == 1

    def test_get_knowledge(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"Knowledge Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        knowledge_data = {
            "organization_id": org_id,
            "title": "Get Test Knowledge",
            "content": "Content here"
        }
        create_response = test_client.post(f"/api/v1/organizations/{org_id}/knowledge", json=knowledge_data)
        knowledge_id = create_response.json()["id"]

        response = test_client.get(f"/api/v1/organizations/{org_id}/knowledge/{knowledge_id}")
        assert response.status_code == 200
        assert response.json()["title"] == "Get Test Knowledge"

    def test_get_nonexistent_knowledge(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"Knowledge Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        response = test_client.get(f"/api/v1/organizations/{org_id}/knowledge/nonexistent-id")
        assert response.status_code == 404

    def test_update_knowledge(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"Knowledge Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        knowledge_data = {
            "organization_id": org_id,
            "title": "Update Test Knowledge",
            "content": "Original content"
        }
        create_response = test_client.post(f"/api/v1/organizations/{org_id}/knowledge", json=knowledge_data)
        knowledge_id = create_response.json()["id"]

        update_data = {
            "organization_id": org_id,
            "title": "Updated Knowledge Title",
            "content": "Updated content"
        }
        response = test_client.put(f"/api/v1/organizations/{org_id}/knowledge/{knowledge_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Knowledge Title"
        assert data["version"] == 2

    def test_delete_knowledge(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"Knowledge Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        knowledge_data = {
            "organization_id": org_id,
            "title": "Delete Test Knowledge",
            "content": "Content to delete"
        }
        create_response = test_client.post(f"/api/v1/organizations/{org_id}/knowledge", json=knowledge_data)
        knowledge_id = create_response.json()["id"]

        response = test_client.delete(f"/api/v1/organizations/{org_id}/knowledge/{knowledge_id}")
        assert response.status_code == 204
