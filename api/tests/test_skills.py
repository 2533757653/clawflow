import pytest
from fastapi.testclient import TestClient


class TestSkillsAPI:
    def test_list_installed_skills(self, test_client):
        response = test_client.get("/api/v1/skills")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_search_skills(self, test_client):
        response = test_client.get("/api/v1/skills/search?q=code")
        assert response.status_code == 200
        results = response.json()
        assert isinstance(results, list)

    def test_search_skills_with_tag(self, test_client):
        response = test_client.get("/api/v1/skills/search?tag=hr")
        assert response.status_code == 200
        results = response.json()
        assert isinstance(results, list)

    def test_preview_skill(self, test_client):
        response = test_client.get("/api/v1/skills/skill-hr-policy-cn/preview")
        assert response.status_code == 200
        data = response.json()
        assert "preview" in data

    def test_install_skill(self, test_client):
        response = test_client.post("/api/v1/skills/skill-test/install")
        assert response.status_code == 200
        data = response.json()
        assert data["installed"] is True

    def test_uninstall_skill(self, test_client):
        install_response = test_client.post("/api/v1/skills/skill-test-uninstall/install")
        assert install_response.status_code == 200

        response = test_client.delete("/api/v1/skills/skill-test-uninstall/uninstall")
        assert response.status_code == 204
