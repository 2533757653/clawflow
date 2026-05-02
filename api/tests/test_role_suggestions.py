import pytest
import uuid
from fastapi.testclient import TestClient


class TestRoleSuggestionsAPI:
    def test_suggest_responsibilities(self, test_client):
        response = test_client.post(
            "/api/v1/roles/suggest-responsibilities",
            json={
                "name": "Frontend Engineer",
                "description": "Builds user interfaces",
                "division": "Engineering",
                "hierarchy_level": 2
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "responsibilities" in data
        assert "confidence" in data
        assert isinstance(data["responsibilities"], list)
        assert 0 <= data["confidence"] <= 1

    def test_suggest_responsibilities_minimal(self, test_client):
        response = test_client.post(
            "/api/v1/roles/suggest-responsibilities",
            json={"name": "Tester"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["responsibilities"]) > 0

    def test_generate_soul(self, test_client):
        response = test_client.post(
            "/api/v1/roles/generate-soul",
            json={
                "name": "Backend Engineer",
                "description": "Builds APIs",
                "division": "Engineering",
                "responsibilities": ["Write APIs", "Optimize performance"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "soul_template" in data
        assert len(data["soul_template"]) > 0
        assert "Backend Engineer" in data["soul_template"]

    def test_generate_soul_minimal(self, test_client):
        response = test_client.post(
            "/api/v1/roles/generate-soul",
            json={
                "name": "Writer",
                "responsibilities": ["Write content"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["soul_template"]) > 0

    def test_suggest_division(self, test_client):
        response = test_client.post(
            "/api/v1/roles/suggest-division",
            json={
                "name": "Marketing Manager",
                "description": "Leads marketing campaigns"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "suggested_division" in data
        assert "alternatives" in data
        assert isinstance(data["alternatives"], list)

    def test_suggest_division_unknown(self, test_client):
        response = test_client.post(
            "/api/v1/roles/suggest-division",
            json={
                "name": "Widget Specialist",
                "description": "Does widget things"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "suggested_division" in data
        assert "alternatives" in data

    def test_apply_suggestions_role_not_found(self, test_client):
        response = test_client.post(
            "/api/v1/roles/apply-suggestions",
            json={
                "role_id": "nonexistent-id",
                "responsibilities": ["New responsibility"]
            }
        )
        assert response.status_code == 404

    def test_apply_suggestions_success(self, test_client):
        role_response = test_client.post(
            "/api/v1/roles",
            json={"name": f"Apply Test Role {uuid.uuid4()}"}
        )
        role_id = role_response.json()["id"]

        response = test_client.post(
            "/api/v1/roles/apply-suggestions",
            json={
                "role_id": role_id,
                "responsibilities": ["Applied responsibility 1", "Applied responsibility 2"],
                "soul_template": "# Applied SOUL\n\nThis is applied."
            }
        )
        assert response.status_code == 200

        get_response = test_client.get(f"/api/v1/roles/{role_id}")
        role = get_response.json()
        assert "Applied responsibility 1" in role["responsibilities"]
        assert role["soul_template"] == "# Applied SOUL\n\nThis is applied."