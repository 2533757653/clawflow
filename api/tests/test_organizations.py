import pytest
import uuid
from fastapi.testclient import TestClient


class TestOrganizationsAPI:
    def test_health_check(self, test_client):
        response = test_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_list_organizations_empty(self, test_client):
        response = test_client.get("/api/v1/organizations")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_organization(self, test_client):
        unique_name = f"Test Organization {uuid.uuid4()}"
        org_data = {
            "name": unique_name,
            "description": "A test organization"
        }
        response = test_client.post("/api/v1/organizations", json=org_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == unique_name
        assert data["status"] == "draft"
        assert "id" in data

    def test_create_duplicate_organization(self, test_client):
        unique_name = f"Duplicate Org {uuid.uuid4()}"
        org_data = {"name": unique_name}
        test_client.post("/api/v1/organizations", json=org_data)
        response = test_client.post("/api/v1/organizations", json=org_data)
        assert response.status_code == 400

    def test_get_organization(self, test_client):
        unique_name = f"Get Test Org {uuid.uuid4()}"
        org_data = {"name": unique_name}
        create_response = test_client.post("/api/v1/organizations", json=org_data)
        org_id = create_response.json()["id"]

        response = test_client.get(f"/api/v1/organizations/{org_id}")
        assert response.status_code == 200
        assert response.json()["name"] == unique_name

    def test_get_nonexistent_organization(self, test_client):
        response = test_client.get("/api/v1/organizations/nonexistent-id")
        assert response.status_code == 404

    def test_update_organization(self, test_client):
        unique_name = f"Update Test Org {uuid.uuid4()}"
        org_data = {"name": unique_name}
        create_response = test_client.post("/api/v1/organizations", json=org_data)
        org_id = create_response.json()["id"]

        update_data = {"name": f"Updated {uuid.uuid4()}", "description": "Updated description"}
        response = test_client.put(f"/api/v1/organizations/{org_id}", json=update_data)
        assert response.status_code == 200

    def test_delete_organization(self, test_client):
        unique_name = f"Delete Test Org {uuid.uuid4()}"
        org_data = {"name": unique_name}
        create_response = test_client.post("/api/v1/organizations", json=org_data)
        org_id = create_response.json()["id"]

        response = test_client.delete(f"/api/v1/organizations/{org_id}")
        assert response.status_code == 204

        get_response = test_client.get(f"/api/v1/organizations/{org_id}")
        assert get_response.status_code == 404
