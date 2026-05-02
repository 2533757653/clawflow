import pytest
import uuid
from fastapi.testclient import TestClient
from api.models.memory import MemoryType


class TestMemoryAPI:
    def test_get_memories_empty(self, test_client):
        role_id = str(uuid.uuid4())
        response = test_client.get(f"/api/v1/memory/{role_id}")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_add_memory(self, test_client):
        role_id = str(uuid.uuid4())
        response = test_client.post(
            f"/api/v1/memory/{role_id}",
            params={"content": "Test memory content", "memory_type": "conversation"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Test memory content"
        assert data["memory_type"] == "conversation"
        assert "id" in data

    def test_update_memory(self, test_client):
        role_id = str(uuid.uuid4())
        add_response = test_client.post(
            f"/api/v1/memory/{role_id}",
            params={"content": "Original content", "memory_type": "conversation"}
        )
        memory_id = add_response.json()["id"]

        update_response = test_client.put(
            f"/api/v1/memory/{role_id}/{memory_id}",
            params={"content": "Updated content"}
        )
        assert update_response.status_code == 200
        assert update_response.json()["content"] == "Updated content"

    def test_update_nonexistent_memory(self, test_client):
        role_id = str(uuid.uuid4())
        response = test_client.put(
            f"/api/v1/memory/{role_id}/{uuid.uuid4()}",
            params={"content": "Updated content"}
        )
        assert response.status_code == 404

    def test_delete_memory(self, test_client):
        role_id = str(uuid.uuid4())
        add_response = test_client.post(
            f"/api/v1/memory/{role_id}",
            params={"content": "To be deleted", "memory_type": "conversation"}
        )
        memory_id = add_response.json()["id"]

        del_response = test_client.delete(f"/api/v1/memory/{role_id}/{memory_id}")
        assert del_response.status_code == 204

        get_response = test_client.get(f"/api/v1/memory/{role_id}")
        ids = [m["id"] for m in get_response.json()]
        assert memory_id not in ids

    def test_access_memory(self, test_client):
        role_id = str(uuid.uuid4())
        add_response = test_client.post(
            f"/api/v1/memory/{role_id}",
            params={"content": "Access this", "memory_type": "conversation"}
        )
        memory_id = add_response.json()["id"]

        access_response = test_client.post(f"/api/v1/memory/{role_id}/access/{memory_id}")
        assert access_response.status_code == 200
        data = access_response.json()
        assert data["access_count"] >= 1

    def test_compress_memories(self, test_client):
        role_id = str(uuid.uuid4())
        for i in range(5):
            test_client.post(
                f"/api/v1/memory/{role_id}",
                params={"content": f"Memory {i}", "memory_type": "conversation"}
            )

        compress_response = test_client.post(
            "/api/v1/memory/compress",
            json={"role_id": role_id, "max_entries": 2}
        )
        assert compress_response.status_code == 200
        data = compress_response.json()
        assert "compressed_entries" in data
        assert "removed_entries" in data
        assert len(data["compressed_entries"]) <= 2

    def test_reset_memories(self, test_client):
        role_id = str(uuid.uuid4())
        for i in range(3):
            test_client.post(
                f"/api/v1/memory/{role_id}",
                params={"content": f"Memory {i}", "memory_type": "conversation"}
            )

        reset_response = test_client.post(
            "/api/v1/memory/reset",
            json={"role_id": role_id, "keep_types": ["fact"]}
        )
        assert reset_response.status_code == 200
        data = reset_response.json()
        assert "cleared_count" in data
        assert "kept_count" in data

    def test_enhance_prompt(self, test_client):
        role_id = str(uuid.uuid4())
        test_client.post(
            f"/api/v1/memory/{role_id}",
            params={"content": "User likes Python", "memory_type": "conversation"}
        )

        enhance_response = test_client.post(
            "/api/v1/memory/enhance-prompt",
            json={"role_id": role_id, "base_prompt": "What language to use?", "max_memory_items": 5}
        )
        assert enhance_response.status_code == 200
        data = enhance_response.json()
        assert "enhanced_prompt" in data
        assert "memory_used" in data

    def test_memory_stats(self, test_client):
        role_id = str(uuid.uuid4())
        test_client.post(
            f"/api/v1/memory/{role_id}",
            params={"content": "Test stat", "memory_type": "conversation"}
        )

        stats_response = test_client.get(f"/api/v1/memory/{role_id}/stats")
        assert stats_response.status_code == 200
        data = stats_response.json()
        assert "total_entries" in data
        assert "by_type" in data

    def test_sync_memory(self, test_client):
        role_id = str(uuid.uuid4())
        sync_response = test_client.post(
            f"/api/v1/memory/{role_id}/sync",
            params={"role_name": "Test Agent"}
        )
        assert sync_response.status_code == 200
        data = sync_response.json()
        assert "memory_path" in data or "entries_count" in data