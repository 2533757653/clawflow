import pytest
import uuid
from fastapi.testclient import TestClient


class TestTasksAPI:
    def test_list_tasks_empty(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"Task Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        response = test_client.get(f"/api/v1/organizations/{org_id}/tasks")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_task(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"Task Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        task_data = {
            "organization_id": org_id,
            "name": "Test Task",
            "description": "A test task",
            "priority": "high"
        }
        response = test_client.post(f"/api/v1/organizations/{org_id}/tasks", json=task_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Task"
        assert data["priority"] == "high"

    def test_get_task(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"Task Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        task_data = {
            "organization_id": org_id,
            "name": "Get Test Task"
        }
        create_response = test_client.post(f"/api/v1/organizations/{org_id}/tasks", json=task_data)
        task_id = create_response.json()["id"]

        response = test_client.get(f"/api/v1/organizations/{org_id}/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Get Test Task"

    def test_get_nonexistent_task(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"Task Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        response = test_client.get(f"/api/v1/organizations/{org_id}/tasks/nonexistent-id")
        assert response.status_code == 404

    def test_update_task(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"Task Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        task_data = {
            "organization_id": org_id,
            "name": "Update Test Task"
        }
        create_response = test_client.post(f"/api/v1/organizations/{org_id}/tasks", json=task_data)
        task_id = create_response.json()["id"]

        update_data = {
            "organization_id": org_id,
            "name": "Updated Task Name",
            "description": "Updated description"
        }
        response = test_client.put(f"/api/v1/organizations/{org_id}/tasks/{task_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Task Name"

    def test_delete_task(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"Task Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        task_data = {
            "organization_id": org_id,
            "name": "Delete Test Task"
        }
        create_response = test_client.post(f"/api/v1/organizations/{org_id}/tasks", json=task_data)
        task_id = create_response.json()["id"]

        response = test_client.delete(f"/api/v1/organizations/{org_id}/tasks/{task_id}")
        assert response.status_code == 204

    def test_get_task_dependencies(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"Task Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        task_data = {
            "organization_id": org_id,
            "name": "Dependency Test Task"
        }
        create_response = test_client.post(f"/api/v1/organizations/{org_id}/tasks", json=task_data)
        task_id = create_response.json()["id"]

        response = test_client.get(f"/api/v1/organizations/{org_id}/tasks/{task_id}/dependencies")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Dependency Test Task"
        assert "dependencies" in data
