import pytest
import uuid
from fastapi.testclient import TestClient


class TestExecutionAPI:
    def test_execute_workflow_not_found_org(self, test_client):
        response = test_client.post(
            f"/api/v1/organizations/{uuid.uuid4()}/execute",
            json={"input_data": {"query": "test"}}
        )
        # Returns 200 with status=failed when org not found
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "failed"
        assert "error" in data.get("final_output", {})

    def test_execute_workflow_found_org_no_dataflow(self, test_client):
        org_response = test_client.post(
            "/api/v1/organizations",
            json={"name": f"No DataFlow Org {uuid.uuid4()}"}
        )
        org_id = org_response.json()["id"]
        response = test_client.post(
            f"/api/v1/organizations/{org_id}/execute",
            json={"input_data": {"query": "test"}}
        )
        assert response.status_code in (200, 404)

    def test_validate_dataflow_not_found(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"Exec Test Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        response = test_client.get(f"/api/v1/organizations/{org_id}/dataflows/{uuid.uuid4()}/validate")
        assert response.status_code == 404

    def test_execution_status_endpoint(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"Exec Status Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]
        response = test_client.get(f"/api/v1/organizations/{org_id}/execution/{uuid.uuid4()}")
        assert response.status_code == 200
        data = response.json()
        assert "execution_id" in data
        assert "status" in data

    def test_validate_empty_dataflow(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"Validate Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]

        df_response = test_client.post(
            f"/api/v1/organizations/{org_id}/dataflows",
            json={"name": "Empty DataFlow", "organization_id": org_id}
        )
        assert df_response.status_code == 201, f"Create failed: {df_response.json()}"
        data = df_response.json()
        df_id = data.get("id")
        assert df_id, f"No id in response: {data}"

        response = test_client.get(f"/api/v1/organizations/{org_id}/dataflows/{df_id}/validate")
        assert response.status_code == 200
        val_data = response.json()
        assert val_data["valid"] is True
        assert val_data["node_count"] == 0
        assert val_data["edge_count"] == 0

    def test_validate_dataflow_with_cycle(self, test_client):
        org_response = test_client.post("/api/v1/organizations", json={"name": f"Cycle Org {uuid.uuid4()}"})
        org_id = org_response.json()["id"]

        node_a = {"id": "node-a", "type": "input", "position": {"x": 0, "y": 0}}
        node_b = {"id": "node-b", "type": "output", "position": {"x": 100, "y": 0}}
        edge_ab = {"id": "ab", "source": "node-a", "target": "node-b"}
        edge_ba = {"id": "ba", "source": "node-b", "target": "node-a"}

        df_response = test_client.post(
            f"/api/v1/organizations/{org_id}/dataflows",
            json={
                "name": "Cycle DataFlow",
                "organization_id": org_id,
                "nodes": [node_a, node_b],
                "edges": [edge_ab, edge_ba]
            }
        )
        assert df_response.status_code == 201, f"Create failed: {df_response.json()}"
        df_id = df_response.json().get("id")
        assert df_id

        response = test_client.get(f"/api/v1/organizations/{org_id}/dataflows/{df_id}/validate")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "circular" in data.get("error", "").lower()