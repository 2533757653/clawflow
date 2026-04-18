import pytest
import uuid
from fastapi.testclient import TestClient


class TestDataFlowsAPI:
    def test_list_dataflows_empty(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"DataFlow Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        response = test_client.get(f"/api/v1/organizations/{org_id}/dataflows")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_dataflow(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"DataFlow Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        dataflow_data = {
            "organization_id": org_id,
            "name": "Test DataFlow",
            "description": "A test dataflow"
        }
        response = test_client.post(f"/api/v1/organizations/{org_id}/dataflows", json=dataflow_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test DataFlow"
        assert data["organization_id"] == org_id

    def test_get_dataflow(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"DataFlow Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        dataflow_data = {
            "organization_id": org_id,
            "name": "Get Test DataFlow"
        }
        create_response = test_client.post(f"/api/v1/organizations/{org_id}/dataflows", json=dataflow_data)
        dataflow_id = create_response.json()["id"]

        response = test_client.get(f"/api/v1/organizations/{org_id}/dataflows/{dataflow_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Get Test DataFlow"

    def test_get_nonexistent_dataflow(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"DataFlow Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        response = test_client.get(f"/api/v1/organizations/{org_id}/dataflows/nonexistent-id")
        assert response.status_code == 404

    def test_update_dataflow(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"DataFlow Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        dataflow_data = {
            "organization_id": org_id,
            "name": "Update Test DataFlow"
        }
        create_response = test_client.post(f"/api/v1/organizations/{org_id}/dataflows", json=dataflow_data)
        dataflow_id = create_response.json()["id"]

        update_data = {
            "organization_id": org_id,
            "name": "Updated DataFlow Name",
            "description": "Updated description"
        }
        response = test_client.put(f"/api/v1/organizations/{org_id}/dataflows/{dataflow_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["name"] == "Updated DataFlow Name"

    def test_delete_dataflow(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"DataFlow Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        dataflow_data = {
            "organization_id": org_id,
            "name": "Delete Test DataFlow"
        }
        create_response = test_client.post(f"/api/v1/organizations/{org_id}/dataflows", json=dataflow_data)
        dataflow_id = create_response.json()["id"]

        response = test_client.delete(f"/api/v1/organizations/{org_id}/dataflows/{dataflow_id}")
        assert response.status_code == 204

    def test_add_node_to_dataflow(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"DataFlow Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        dataflow_data = {
            "organization_id": org_id,
            "name": "Node Test DataFlow"
        }
        create_response = test_client.post(f"/api/v1/organizations/{org_id}/dataflows", json=dataflow_data)
        dataflow_id = create_response.json()["id"]

        node_data = {
            "type": "role",
            "ref_id": "test-ref-id",
            "position": {"x": 100, "y": 200},
            "label": "Test Node"
        }
        response = test_client.post(f"/api/v1/organizations/{org_id}/dataflows/{dataflow_id}/nodes", json=node_data)
        assert response.status_code == 200
        assert len(response.json()["nodes"]) == 1

    def test_add_edge_to_dataflow(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"DataFlow Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        dataflow_data = {
            "organization_id": org_id,
            "name": "Edge Test DataFlow"
        }
        create_response = test_client.post(f"/api/v1/organizations/{org_id}/dataflows", json=dataflow_data)
        dataflow_id = create_response.json()["id"]

        node_data = {
            "type": "role",
            "ref_id": "test-ref-id",
            "position": {"x": 100, "y": 200}
        }
        test_client.post(f"/api/v1/organizations/{org_id}/dataflows/{dataflow_id}/nodes", json=node_data)

        edge_data = {
            "source": node_data.get("id", "test-source"),
            "target": "test-target"
        }
        response = test_client.post(f"/api/v1/organizations/{org_id}/dataflows/{dataflow_id}/edges", json=edge_data)
        assert response.status_code == 200
