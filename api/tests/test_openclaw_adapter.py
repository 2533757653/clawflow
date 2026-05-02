import pytest
import os
import tempfile
import shutil
from api.services.openclaw_adapter import OpenClawAdapter, OrganizationService
from api.models import Role, PermissionLevel


class TestOpenClawAdapter:
    @pytest.fixture
    def temp_workspace(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def adapter(self, temp_workspace):
        return OpenClawAdapter(agents_path=temp_workspace)

    @pytest.fixture
    def sample_role(self):
        return Role(
            id="test-role-id",
            name="Test Engineer",
            description="A test engineer role",
            responsibilities=[
                "Write tests",
                "Review code",
                "Fix bugs"
            ],
            required_skills=["python", "testing"],
            reports_to=None,
            permission_level=PermissionLevel.MEMBER,
            hierarchy_level=1
        )

    def test_adapter_initialization(self, temp_workspace):
        adapter = OpenClawAdapter(agents_path=temp_workspace)
        assert adapter.agents_path == temp_workspace
        assert os.path.exists(temp_workspace)

    def test_get_agent_path(self, adapter):
        path = adapter._get_agent_path("Test Agent")
        assert "test_agent" in path
        assert os.path.exists(os.path.join(path, "agents"))
        assert os.path.exists(os.path.join(path, "skills"))
        assert os.path.exists(os.path.join(path, "memory"))

    def test_deploy_role(self, adapter, sample_role):
        agent_path = adapter.deploy_role(sample_role)
        assert os.path.exists(agent_path)
        assert os.path.exists(os.path.join(agent_path, "SOUL.md"))
        assert os.path.exists(os.path.join(agent_path, "IDENTITY.md"))
        assert os.path.exists(os.path.join(agent_path, "AGENTS.md"))
        assert os.path.exists(os.path.join(agent_path, "BOOTSTRAP.md"))
        assert os.path.exists(os.path.join(agent_path, "HEARTBEAT.md"))
        assert os.path.exists(os.path.join(agent_path, "USER.md"))

    def test_deploy_role_custom_soul(self, adapter):
        role = Role(
            id="custom-soul-role",
            name="Custom Soul Role",
            soul_template="# Custom Soul\n\nThis is a custom soul template."
        )
        agent_path = adapter.deploy_role(role)
        soul_path = os.path.join(agent_path, "SOUL.md")
        with open(soul_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Custom Soul" in content

    def test_deploy_role_with_context_memory(self, adapter, sample_role):
        sample_role.context_memory = "This is the agent's context memory."
        agent_path = adapter.deploy_role(sample_role)
        memory_path = os.path.join(agent_path, "memory", "context.md")
        assert os.path.exists(memory_path)
        with open(memory_path, 'r', encoding='utf-8') as f:
            assert "context memory" in f.read()

    def test_undeploy_role(self, adapter, sample_role):
        agent_path = adapter.deploy_role(sample_role)
        assert os.path.exists(agent_path)

        result = adapter.undeploy_role(sample_role.name)
        assert result is True
        assert not os.path.exists(agent_path)

    def test_undeploy_nonexistent_role(self, adapter):
        # The adapter creates the directory on _get_agent_path, so undeploy returns True
        result = adapter.undeploy_role("nonexistent-role")
        assert result is True
        # Verify the directory was cleaned up
        assert not os.path.exists(os.path.join(adapter.agents_path, "nonexistent_role"))

    def test_user_md_no_tbd(self, adapter, sample_role):
        adapter.deploy_role(sample_role)
        user_md_path = os.path.join(adapter.agents_path, "test_engineer", "USER.md")
        with open(user_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert "- TBD" not in content
        assert "USER.md" in content


class TestOrganizationService:
    @pytest.fixture
    def temp_base_path(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def org_service(self, temp_base_path):
        return OrganizationService(base_path=temp_base_path)

    def test_create_organization_dirs(self, org_service):
        org_path = org_service.create_organization_dirs("test-org-123")
        assert os.path.exists(org_path)
        assert os.path.exists(os.path.join(org_path, "roles"))
        assert os.path.exists(os.path.join(org_path, "tasks"))
        assert os.path.exists(os.path.join(org_path, "dataflows"))
        assert os.path.exists(os.path.join(org_path, "knowledge"))

    def test_delete_organization_dirs(self, org_service):
        org_service.create_organization_dirs("test-org-delete")
        result = org_service.delete_organization_dirs("test-org-delete")
        assert result is True
        assert not os.path.exists(org_service._get_org_path("test-org-delete"))

    def test_delete_nonexistent_organization(self, org_service):
        result = org_service.delete_organization_dirs("nonexistent-org")
        assert result is False