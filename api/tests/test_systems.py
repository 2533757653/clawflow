import pytest
import uuid
from fastapi.testclient import TestClient


class TestSystemsAPI:
    def test_list_systems_empty(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"System Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        response = test_client.get(f"/api/v1/organizations/{org_id}/systems")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_system(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"System Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        system_data = {
            "organization_id": org_id,
            "name": "Test System",
            "description": "A test system"
        }
        response = test_client.post(f"/api/v1/organizations/{org_id}/systems", json=system_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test System"
        assert data["organization_id"] == org_id
        assert data["state"] == "initialized"

    def test_get_system(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"System Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        system_data = {
            "organization_id": org_id,
            "name": "Get Test System"
        }
        create_response = test_client.post(f"/api/v1/organizations/{org_id}/systems", json=system_data)
        system_id = create_response.json()["id"]

        response = test_client.get(f"/api/v1/organizations/{org_id}/systems/{system_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Get Test System"

    def test_get_nonexistent_system(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"System Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        response = test_client.get(f"/api/v1/organizations/{org_id}/systems/nonexistent-id")
        assert response.status_code == 404

    def test_update_system(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"System Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        system_data = {
            "organization_id": org_id,
            "name": "Update Test System"
        }
        create_response = test_client.post(f"/api/v1/organizations/{org_id}/systems", json=system_data)
        system_id = create_response.json()["id"]

        update_data = {
            "organization_id": org_id,
            "name": "Updated System Name",
            "description": "Updated description"
        }
        response = test_client.put(f"/api/v1/organizations/{org_id}/systems/{system_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["name"] == "Updated System Name"

    def test_delete_system(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"System Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        system_data = {
            "organization_id": org_id,
            "name": "Delete Test System"
        }
        create_response = test_client.post(f"/api/v1/organizations/{org_id}/systems", json=system_data)
        system_id = create_response.json()["id"]

        response = test_client.delete(f"/api/v1/organizations/{org_id}/systems/{system_id}")
        assert response.status_code == 204

    def test_add_actor_to_system(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"System Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        system_data = {
            "organization_id": org_id,
            "name": "Actor Test System"
        }
        create_response = test_client.post(f"/api/v1/organizations/{org_id}/systems", json=system_data)
        system_id = create_response.json()["id"]

        actor_data = {
            "type": "role",
            "role_id": "test-role-id",
            "depth": 0
        }
        response = test_client.post(f"/api/v1/organizations/{org_id}/systems/{system_id}/actors", json=actor_data)
        assert response.status_code == 200
        assert len(response.json()["actors"]) == 1

    def test_start_system(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"System Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        system_data = {
            "organization_id": org_id,
            "name": "Start Test System"
        }
        create_response = test_client.post(f"/api/v1/organizations/{org_id}/systems", json=system_data)
        system_id = create_response.json()["id"]

        role_data = {
            "organization_id": org_id,
            "name": "Test Role for System"
        }
        role_response = test_client.post(f"/api/v1/organizations/{org_id}/roles", json=role_data)
        role_id = role_response.json()["id"]

        decider_data = {"type": "role", "role_id": role_id}
        test_client.post(f"/api/v1/organizations/{org_id}/systems/{system_id}/decider", json=decider_data)

        actor_data = {"type": "role", "role_id": role_id}
        test_client.post(f"/api/v1/organizations/{org_id}/systems/{system_id}/actors", json=actor_data)

        feedbacker_data = {"type": "role", "role_id": role_id}
        test_client.post(f"/api/v1/organizations/{org_id}/systems/{system_id}/feedbacker", json=feedbacker_data)

        response = test_client.post(f"/api/v1/organizations/{org_id}/systems/{system_id}/start")
        assert response.status_code == 200
        assert response.json()["state"] == "running"

    def test_stop_system(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"System Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        system_data = {
            "organization_id": org_id,
            "name": "Stop Test System"
        }
        create_response = test_client.post(f"/api/v1/organizations/{org_id}/systems", json=system_data)
        system_id = create_response.json()["id"]

        test_client.post(f"/api/v1/organizations/{org_id}/systems/{system_id}/start")
        response = test_client.post(f"/api/v1/organizations/{org_id}/systems/{system_id}/stop")
        assert response.status_code == 200
        assert response.json()["state"] == "stopped"

    def test_execute_loop_step(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"System Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        system_data = {
            "organization_id": org_id,
            "name": "Loop Test System"
        }
        create_response = test_client.post(f"/api/v1/organizations/{org_id}/systems", json=system_data)
        system_id = create_response.json()["id"]

        role_data = {
            "organization_id": org_id,
            "name": "Loop Test Role"
        }
        role_response = test_client.post(f"/api/v1/organizations/{org_id}/roles", json=role_data)
        role_id = role_response.json()["id"]

        decider_data = {"type": "role", "role_id": role_id}
        test_client.post(f"/api/v1/organizations/{org_id}/systems/{system_id}/decider", json=decider_data)

        actor_data = {"type": "role", "role_id": role_id}
        test_client.post(f"/api/v1/organizations/{org_id}/systems/{system_id}/actors", json=actor_data)

        feedbacker_data = {"type": "role", "role_id": role_id}
        test_client.post(f"/api/v1/organizations/{org_id}/systems/{system_id}/feedbacker", json=feedbacker_data)

        test_client.post(f"/api/v1/organizations/{org_id}/systems/{system_id}/start")

        response = test_client.post(f"/api/v1/organizations/{org_id}/systems/{system_id}/loop")
        assert response.status_code == 200
        data = response.json()
        assert data["system_id"] == system_id
        assert data["phase"] == "complete"

    def test_get_available_executors(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"System Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        role_data = {
            "organization_id": org_id,
            "name": "Executor Test Role"
        }
        test_client.post(f"/api/v1/organizations/{org_id}/roles", json=role_data)

        response = test_client.get(f"/api/v1/organizations/{org_id}/available-executors")
        assert response.status_code == 200
        data = response.json()
        assert "roles" in data
        assert "systems" in data
        assert len(data["roles"]) >= 1
