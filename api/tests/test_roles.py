import pytest
import uuid
from fastapi.testclient import TestClient


class TestRolesAPI:
    def test_list_roles_empty(self, test_client):
        response = test_client.get("/api/v1/roles")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_role(self, test_client):
        role_data = {
            "name": f"Test Role {uuid.uuid4()}",
            "description": "A test role",
            "responsibilities": ["Task 1", "Task 2"]
        }
        response = test_client.post("/api/v1/roles", json=role_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == role_data["name"]
        assert data["description"] == "A test role"
        assert "id" in data

    def test_create_role_duplicate_name(self, test_client):
        role_name = f"Duplicate Role {uuid.uuid4()}"
        role_data = {"name": role_name}
        test_client.post("/api/v1/roles", json=role_data)
        response = test_client.post("/api/v1/roles", json={"name": role_name})
        assert response.status_code == 400

    def test_get_role(self, test_client):
        role_data = {"name": f"Get Test Role {uuid.uuid4()}"}
        create_response = test_client.post("/api/v1/roles", json=role_data)
        role_id = create_response.json()["id"]

        response = test_client.get(f"/api/v1/roles/{role_id}")
        assert response.status_code == 200
        assert response.json()["name"] == role_data["name"]

    def test_get_nonexistent_role(self, test_client):
        response = test_client.get("/api/v1/roles/nonexistent-id")
        assert response.status_code == 404

    def test_update_role(self, test_client):
        role_data = {"name": f"Update Test Role {uuid.uuid4()}"}
        create_response = test_client.post("/api/v1/roles", json=role_data)
        role_id = create_response.json()["id"]

        update_data = {
            "name": role_data["name"],
            "description": "Updated description"
        }
        response = test_client.put(f"/api/v1/roles/{role_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["description"] == "Updated description"

    def test_delete_role(self, test_client):
        role_data = {"name": f"Delete Test Role {uuid.uuid4()}"}
        create_response = test_client.post("/api/v1/roles", json=role_data)
        role_id = create_response.json()["id"]

        response = test_client.delete(f"/api/v1/roles/{role_id}")
        assert response.status_code == 204

        get_response = test_client.get(f"/api/v1/roles/{role_id}")
        assert get_response.status_code == 404

    def test_role_hierarchy(self, test_client):
        parent_data = {"name": f"Parent Role {uuid.uuid4()}"}
        parent_response = test_client.post("/api/v1/roles", json=parent_data)
        parent_id = parent_response.json()["id"]

        child_data = {
            "name": f"Child Role {uuid.uuid4()}",
            "reports_to": parent_id
        }
        child_response = test_client.post("/api/v1/roles", json=child_data)
        child_id = child_response.json()["id"]

        hierarchy_response = test_client.get(f"/api/v1/roles/{parent_id}/hierarchy")
        assert hierarchy_response.status_code == 200
        hierarchy = hierarchy_response.json()
        assert hierarchy["id"] == parent_id
        assert hierarchy["name"] == parent_data["name"]