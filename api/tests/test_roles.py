import pytest
import uuid
from fastapi.testclient import TestClient


class TestRolesAPI:
    def test_list_roles_empty(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"Role Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        response = test_client.get(f"/api/v1/organizations/{org_id}/roles")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_role(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"Role Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        role_data = {
            "organization_id": org_id,
            "name": "Test Role",
            "description": "A test role",
            "responsibilities": ["Task 1", "Task 2"]
        }
        response = test_client.post(f"/api/v1/organizations/{org_id}/roles", json=role_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Role"
        assert data["organization_id"] == org_id

    def test_get_role(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"Role Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        role_data = {
            "organization_id": org_id,
            "name": "Get Test Role"
        }
        create_response = test_client.post(f"/api/v1/organizations/{org_id}/roles", json=role_data)
        role_id = create_response.json()["id"]

        response = test_client.get(f"/api/v1/organizations/{org_id}/roles/{role_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Get Test Role"

    def test_get_nonexistent_role(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"Role Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        response = test_client.get(f"/api/v1/organizations/{org_id}/roles/nonexistent-id")
        assert response.status_code == 404

    def test_update_role(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"Role Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        role_data = {
            "organization_id": org_id,
            "name": "Update Test Role"
        }
        create_response = test_client.post(f"/api/v1/organizations/{org_id}/roles", json=role_data)
        role_id = create_response.json()["id"]

        update_data = {
            "organization_id": org_id,
            "name": "Updated Role Name",
            "description": "Updated description"
        }
        response = test_client.put(f"/api/v1/organizations/{org_id}/roles/{role_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Role Name"

    def test_delete_role(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"Role Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        role_data = {
            "organization_id": org_id,
            "name": "Delete Test Role"
        }
        create_response = test_client.post(f"/api/v1/organizations/{org_id}/roles", json=role_data)
        role_id = create_response.json()["id"]

        response = test_client.delete(f"/api/v1/organizations/{org_id}/roles/{role_id}")
        assert response.status_code == 204
