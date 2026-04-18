import pytest
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="function")
def test_client():
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app)


@pytest.fixture(scope="function")
def test_org_id(test_client):
    response = test_client.post("/api/v1/organizations", json={"name": "Test Org"})
    if response.status_code == 201:
        return response.json()["id"]
    return None
