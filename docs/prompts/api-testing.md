# Prompt: API 测试覆盖

## 项目信息

- **项目名称**: ClawFlow - Agent 组织动态构建平台
- **项目路径**: `d:\clawflow`
- **后端**: `api/` (FastAPI + Python 3.11+)
- **测试框架**: pytest

## 项目架构

参见 `docs/prompts/workflow-execution-engine.md`

## 已有测试结构

### 已有测试文件
位置: `api/tests/`

```
api/tests/
├── __init__.py
├── conftest.py          # pytest fixtures
├── test_knowledge.py
├── test_openclaw_adapter.py
├── test_organizations.py
├── test_rag.py
├── test_roles.py
├── test_skills.py
└── test_tasks.py
```

### 现有 conftest.py
```python
# 位置: api/tests/conftest.py
# 已有基础的 pytest fixtures
```

## 任务要求

### 1. 增强 conftest.py

修改 `api/tests/conftest.py`:

```python
import pytest
import os
import shutil
import tempfile
from fastapi.testclient import TestClient
from typing import Generator

# 在测试开始前设置临时目录
TEST_DATA_DIR = tempfile.mkdtemp()

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """设置测试环境"""
    os.environ["TESTING"] = "true"
    yield
    # 清理
    if os.path.exists(TEST_DATA_DIR):
        shutil.rmtree(TEST_DATA_DIR)

@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """创建临时目录用于测试"""
    dir_path = tempfile.mkdtemp()
    yield dir_path
    shutil.rmtree(dir_path, ignore_errors=True)

@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """创建测试客户端"""
    from api.main import app
    with TestClient(app) as c:
        yield c

@pytest.fixture
def org_storage():
    """组织存储 fixture"""
    from api.services.storage import StorageService
    from api.models import Organization

    storage = StorageService("data/organizations", Organization)
    yield storage
    # 清理
    for item_id in storage._list_files():
        storage.delete(item_id)

@pytest.fixture
def role_storage():
    """角色存储 fixture"""
    from api.services.storage import StorageService
    from api.models import Role

    storage = StorageService("data/roles", Role)
    yield storage
    # 清理
    for item_id in storage._list_files():
        storage.delete(item_id)

@pytest.fixture
def sample_organization():
    """示例组织数据"""
    from api.models import Organization, OrganizationStatus
    return Organization(
        name="Test Organization",
        description="A test organization",
        status=OrganizationStatus.DRAFT,
        role_ids=[]
    )

@pytest.fixture
def sample_role():
    """示例角色数据"""
    from api.models import Role, PermissionLevel
    return Role(
        name="Test Role",
        description="A test role",
        responsibilities=["Test responsibility 1", "Test responsibility 2"],
        required_skills=["skill1"],
        permission_level=PermissionLevel.MEMBER,
        hierarchy_level=1
    )

@pytest.fixture
def sample_task():
    """示例任务数据"""
    from api.models import Task, Priority, ExecutionMode
    return Task(
        organization_id="test-org-id",
        name="Test Task",
        description="A test task",
        priority=Priority.MEDIUM,
        execution_mode=ExecutionMode.SEQUENTIAL
    )

@pytest.fixture
def sample_dataflow():
    """示例数据流数据"""
    from api.models import DataFlow, DataFlowNode, DataFlowEdge, NodeType
    return DataFlow(
        organization_id="test-org-id",
        name="Test DataFlow",
        description="A test dataflow",
        nodes=[
            DataFlowNode(id="node1", type=NodeType.INPUT, position={"x": 0, "y": 0}),
            DataFlowNode(id="node2", type=NodeType.ROLE, ref_id="role1", position={"x": 100, "y": 0}),
            DataFlowNode(id="node3", type=NodeType.OUTPUT, position={"x": 200, "y": 0})
        ],
        edges=[
            DataFlowEdge(id="edge1", source="node1", target="node2"),
            DataFlowEdge(id="edge2", source="node2", target="node3")
        ]
    )
```

### 2. Organizations 测试

创建/增强 `api/tests/test_organizations.py`:

```python
import pytest
from fastapi import status

class TestOrganizations:
    """组织 API 测试"""

    def test_list_organizations_empty(self, client):
        """测试获取空组织列表"""
        response = client.get("/api/v1/organizations")
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)

    def test_create_organization(self, client, sample_organization):
        """测试创建组织"""
        response = client.post(
            "/api/v1/organizations",
            json=sample_organization.model_dump(mode="json")
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == sample_organization.name
        assert data["id"] is not None

    def test_create_organization_duplicate_name(self, client, sample_organization):
        """测试创建重复名称的组织"""
        # 创建第一个
        client.post(
            "/api/v1/organizations",
            json=sample_organization.model_dump(mode="json")
        )
        # 尝试创建重复
        response = client.post(
            "/api/v1/organizations",
            json=sample_organization.model_dump(mode="json")
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_organization(self, client, sample_organization):
        """测试获取单个组织"""
        # 创建
        create_response = client.post(
            "/api/v1/organizations",
            json=sample_organization.model_dump(mode="json")
        )
        org_id = create_response.json()["id"]

        # 获取
        response = client.get(f"/api/v1/organizations/{org_id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == sample_organization.name

    def test_get_organization_not_found(self, client):
        """测试获取不存在的组织"""
        response = client.get("/api/v1/organizations/non-existent-id")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_organization(self, client, sample_organization):
        """测试更新组织"""
        # 创建
        create_response = client.post(
            "/api/v1/organizations",
            json=sample_organization.model_dump(mode="json")
        )
        org_id = create_response.json()["id"]

        # 更新
        update_data = sample_organization.model_dump(mode="json")
        update_data["name"] = "Updated Name"
        response = client.put(
            f"/api/v1/organizations/{org_id}",
            json=update_data
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "Updated Name"

    def test_delete_organization(self, client, sample_organization):
        """测试删除组织"""
        # 创建
        create_response = client.post(
            "/api/v1/organizations",
            json=sample_organization.model_dump(mode="json")
        )
        org_id = create_response.json()["id"]

        # 删除
        response = client.delete(f"/api/v1/organizations/{org_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # 验证删除
        get_response = client.get(f"/api/v1/organizations/{org_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_deploy_organization_empty_roles(self, client, sample_organization):
        """测试部署没有角色的组织"""
        # 创建没有角色的组织
        response = client.post(
            "/api/v1/organizations",
            json=sample_organization.model_dump(mode="json")
        )
        org_id = response.json()["id"]

        # 部署
        deploy_response = client.post(f"/api/v1/organizations/{org_id}/deploy")
        assert deploy_response.status_code == status.HTTP_400_BAD_REQUEST

    def test_deploy_organization_with_roles(self, client, sample_organization, sample_role):
        """测试部署有角色的组织"""
        # 创建角色
        role_response = client.post(
            "/api/v1/roles",
            json=sample_role.model_dump(mode="json")
        )
        role_id = role_response.json()["id"]

        # 创建组织并关联角色
        sample_organization.role_ids = [role_id]
        org_response = client.post(
            "/api/v1/organizations",
            json=sample_organization.model_dump(mode="json")
        )
        org_id = org_response.json()["id"]

        # 部署
        deploy_response = client.post(f"/api/v1/organizations/{org_id}/deploy")
        assert deploy_response.status_code == status.HTTP_200_OK
        assert deploy_response.json()["total_roles"] == 1

        # 验证状态更新
        org_get = client.get(f"/api/v1/organizations/{org_id}")
        assert org_get.json()["status"] == "deployed"

    def test_start_organization(self, client, sample_organization, sample_role):
        """测试开启组织"""
        # 创建并部署
        role_response = client.post("/api/v1/roles", json=sample_role.model_dump(mode="json"))
        role_id = role_response.json()["id"]

        sample_organization.role_ids = [role_id]
        sample_organization.input_role_id = role_id
        org_response = client.post(
            "/api/v1/organizations",
            json=sample_organization.model_dump(mode="json")
        )
        org_id = org_response.json()["id"]

        client.post(f"/api/v1/organizations/{org_id}/deploy")

        # 开启
        start_response = client.post(f"/api/v1/organizations/{org_id}/start")
        assert start_response.status_code == status.HTTP_200_OK

        # 验证状态
        org_get = client.get(f"/api/v1/organizations/{org_id}")
        assert org_get.json()["status"] == "running"

    def test_start_organization_not_deployed(self, client, sample_organization):
        """测试开启未部署的组织"""
        response = client.post(
            "/api/v1/organizations",
            json=sample_organization.model_dump(mode="json")
        )
        org_id = response.json()["id"]

        start_response = client.post(f"/api/v1/organizations/{org_id}/start")
        assert start_response.status_code == status.HTTP_400_BAD_REQUEST

    def test_stop_organization(self, client, sample_organization, sample_role):
        """测试停止组织"""
        # 创建、部署、开启
        role_response = client.post("/api/v1/roles", json=sample_role.model_dump(mode="json"))
        role_id = role_response.json()["id"]

        sample_organization.role_ids = [role_id]
        sample_organization.input_role_id = role_id
        org_response = client.post(
            "/api/v1/organizations",
            json=sample_organization.model_dump(mode="json")
        )
        org_id = org_response.json()["id"]

        client.post(f"/api/v1/organizations/{org_id}/deploy")
        client.post(f"/api/v1/organizations/{org_id}/start")

        # 停止
        stop_response = client.post(f"/api/v1/organizations/{org_id}/stop")
        assert stop_response.status_code == status.HTTP_200_OK

        # 验证状态
        org_get = client.get(f"/api/v1/organizations/{org_id}")
        assert org_get.json()["status"] == "stopped"
```

### 3. Roles 测试

创建/增强 `api/tests/test_roles.py`:

```python
import pytest
from fastapi import status

class TestRoles:
    """角色 API 测试"""

    def test_list_roles_empty(self, client):
        """测试获取空角色列表"""
        response = client.get("/api/v1/roles")
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)

    def test_create_role(self, client, sample_role):
        """测试创建角色"""
        response = client.post(
            "/api/v1/roles",
            json=sample_role.model_dump(mode="json")
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == sample_role.name
        assert data["id"] is not None

    def test_create_role_duplicate_name(self, client, sample_role):
        """测试创建重复名称的角色"""
        client.post("/api/v1/roles", json=sample_role.model_dump(mode="json"))
        response = client.post(
            "/api/v1/roles",
            json=sample_role.model_dump(mode="json")
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_role(self, client, sample_role):
        """测试获取单个角色"""
        create_response = client.post(
            "/api/v1/roles",
            json=sample_role.model_dump(mode="json")
        )
        role_id = create_response.json()["id"]

        response = client.get(f"/api/v1/roles/{role_id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == sample_role.name

    def test_update_role(self, client, sample_role):
        """测试更新角色"""
        create_response = client.post(
            "/api/v1/roles",
            json=sample_role.model_dump(mode="json")
        )
        role_id = create_response.json()["id"]

        update_data = sample_role.model_dump(mode="json")
        update_data["name"] = "Updated Role Name"
        response = client.put(
            f"/api/v1/roles/{role_id}",
            json=update_data
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "Updated Role Name"

    def test_delete_role(self, client, sample_role):
        """测试删除角色"""
        create_response = client.post(
            "/api/v1/roles",
            json=sample_role.model_dump(mode="json")
        )
        role_id = create_response.json()["id"]

        response = client.delete(f"/api/v1/roles/{role_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_role_hierarchy(self, client, sample_role):
        """测试角色层级"""
        # 创建角色
        create_response = client.post(
            "/api/v1/roles",
            json=sample_role.model_dump(mode="json")
        )
        role_id = create_response.json()["id"]

        # 获取层级
        response = client.get(f"/api/v1/roles/{role_id}/hierarchy")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == role_id
        assert data["name"] == sample_role.name
```

### 4. DataFlows 测试

创建 `api/tests/test_dataflows.py`:

```python
import pytest
from fastapi import status

class TestDataFlows:
    """数据流 API 测试"""

    @pytest.fixture
    def org_with_dataflow(self, client, sample_organization):
        """创建用于测试数据流的组织"""
        org_response = client.post(
            "/api/v1/organizations",
            json=sample_organization.model_dump(mode="json")
        )
        org_id = org_response.json()["id"]
        return org_id

    def test_create_dataflow(self, client, org_with_dataflow, sample_dataflow):
        """测试创建数据流"""
        sample_dataflow.organization_id = org_with_dataflow
        response = client.post(
            f"/api/v1/organizations/{org_with_dataflow}/dataflows",
            json=sample_dataflow.model_dump(mode="json")
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["name"] == sample_dataflow.name

    def test_list_dataflows(self, client, org_with_dataflow, sample_dataflow):
        """测试获取数据流列表"""
        sample_dataflow.organization_id = org_with_dataflow
        client.post(
            f"/api/v1/organizations/{org_with_dataflow}/dataflows",
            json=sample_dataflow.model_dump(mode="json")
        )

        response = client.get(f"/api/v1/organizations/{org_with_dataflow}/dataflows")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 1

    def test_get_dataflow(self, client, org_with_dataflow, sample_dataflow):
        """测试获取单个数据流"""
        sample_dataflow.organization_id = org_with_dataflow
        create_response = client.post(
            f"/api/v1/organizations/{org_with_dataflow}/dataflows",
            json=sample_dataflow.model_dump(mode="json")
        )
        dataflow_id = create_response.json()["id"]

        response = client.get(
            f"/api/v1/organizations/{org_with_dataflow}/dataflows/{dataflow_id}"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == dataflow_id

    def test_update_dataflow(self, client, org_with_dataflow, sample_dataflow):
        """测试更新数据流"""
        sample_dataflow.organization_id = org_with_dataflow
        create_response = client.post(
            f"/api/v1/organizations/{org_with_dataflow}/dataflows",
            json=sample_dataflow.model_dump(mode="json")
        )
        dataflow_id = create_response.json()["id"]

        update_data = sample_dataflow.model_dump(mode="json")
        update_data["name"] = "Updated DataFlow"
        response = client.put(
            f"/api/v1/organizations/{org_with_dataflow}/dataflows/{dataflow_id}",
            json=update_data
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "Updated DataFlow"

    def test_delete_dataflow(self, client, org_with_dataflow, sample_dataflow):
        """测试删除数据流"""
        sample_dataflow.organization_id = org_with_dataflow
        create_response = client.post(
            f"/api/v1/organizations/{org_with_dataflow}/dataflows",
            json=sample_dataflow.model_dump(mode="json")
        )
        dataflow_id = create_response.json()["id"]

        response = client.delete(
            f"/api/v1/organizations/{org_with_dataflow}/dataflows/{dataflow_id}"
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_add_node_to_dataflow(self, client, org_with_dataflow, sample_dataflow):
        """测试向数据流添加节点"""
        sample_dataflow.organization_id = org_with_dataflow
        create_response = client.post(
            f"/api/v1/organizations/{org_with_dataflow}/dataflows",
            json=sample_dataflow.model_dump(mode="json")
        )
        dataflow_id = create_response.json()["id"]

        from api.models import DataFlowNode, NodeType
        new_node = DataFlowNode(
            id="new-node",
            type=NodeType.TASK,
            position={"x": 300, "y": 100},
            label="New Task"
        )

        response = client.post(
            f"/api/v1/organizations/{org_with_dataflow}/dataflows/{dataflow_id}/nodes",
            json=new_node.model_dump(mode="json")
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["nodes"]) == 4  # 原有3个 + 1个新节点

    def test_remove_node_from_dataflow(self, client, org_with_dataflow, sample_dataflow):
        """测试从数据流移除节点"""
        sample_dataflow.organization_id = org_with_dataflow
        create_response = client.post(
            f"/api/v1/organizations/{org_with_dataflow}/dataflows",
            json=sample_dataflow.model_dump(mode="json")
        )
        dataflow_id = create_response.json()["id"]

        response = client.delete(
            f"/api/v1/organizations/{org_with_dataflow}/dataflows/{dataflow_id}/nodes/node1"
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # 验证节点被移除，同时移除关联的边
        get_response = client.get(
            f"/api/v1/organizations/{org_with_dataflow}/dataflows/{dataflow_id}"
        )
        dataflow = get_response.json()
        node_ids = [n["id"] for n in dataflow["nodes"]]
        edge_node_ids = set()
        for e in dataflow["edges"]:
            edge_node_ids.add(e["source"])
            edge_node_ids.add(e["target"])
        assert "node1" not in node_ids
        assert "node1" not in edge_node_ids
```

### 5. Tasks 测试

增强 `api/tests/test_tasks.py`:

```python
import pytest
from fastapi import status

class TestTasks:
    """任务 API 测试"""

    @pytest.fixture
    def org_for_tasks(self, client, sample_organization):
        """创建用于测试任务的组织"""
        org_response = client.post(
            "/api/v1/organizations",
            json=sample_organization.model_dump(mode="json")
        )
        return org_response.json()["id"]

    def test_create_task(self, client, org_for_tasks, sample_task):
        """测试创建任务"""
        sample_task.organization_id = org_for_tasks
        response = client.post(
            f"/api/v1/organizations/{org_for_tasks}/tasks",
            json=sample_task.model_dump(mode="json")
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["name"] == sample_task.name

    def test_list_tasks(self, client, org_for_tasks, sample_task):
        """测试获取任务列表"""
        sample_task.organization_id = org_for_tasks
        client.post(
            f"/api/v1/organizations/{org_for_tasks}/tasks",
            json=sample_task.model_dump(mode="json")
        )

        response = client.get(f"/api/v1/organizations/{org_for_tasks}/tasks")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 1

    def test_task_dependencies(self, client, org_for_tasks, sample_task):
        """测试任务依赖"""
        # 创建第一个任务
        sample_task.organization_id = org_for_tasks
        task1_response = client.post(
            f"/api/v1/organizations/{org_for_tasks}/tasks",
            json=sample_task.model_dump(mode="json")
        )
        task1_id = task1_response.json()["id"]

        # 创建依赖 task1 的第二个任务
        task2 = sample_task.model_dump(mode="json")
        task2["name"] = "Task 2"
        task2["dependencies"] = [task1_id]
        task2_response = client.post(
            f"/api/v1/organizations/{org_for_tasks}/tasks",
            json=task2
        )

        # 获取依赖链
        response = client.get(
            f"/api/v1/organizations/{org_for_tasks}/tasks/{task2_response.json()['id']}/dependencies"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == task2_response.json()["id"]
        assert len(data["dependencies"]) == 1
```

### 6. 运行测试

```bash
cd d:\clawflow\api

# 运行所有测试
pytest -v

# 运行带覆盖率
pytest -v --cov=. --cov-report=html --cov-report=term

# 运行特定文件
pytest -v tests/test_organizations.py

# 运行特定测试
pytest -v tests/test_organizations.py::TestOrganizations::test_create_organization

# 生成覆盖率报告
pytest --cov=. --cov-report=html
# 报告位置: htmlcov/index.html
```

## 文件结构

```
api/tests/
├── __init__.py
├── conftest.py          # 修改: 增强 fixtures
├── test_organizations.py # 修改: 增强组织测试
├── test_roles.py         # 修改: 增强角色测试
├── test_dataflows.py    # 新增: 数据流测试
├── test_tasks.py        # 修改: 增强任务测试
├── test_knowledge.py    # 已有
├── test_skills.py       # 已有
└── test_rag.py          # 已有
```

## 注意事项

1. **测试隔离**: 每个测试使用独立的组织/角色 ID
2. **Fixtures**: 使用 fixtures 进行 setup/teardown
3. **Mock 外部依赖**: OpenClaw 调用使用 mock
4. **并发测试**: 注意测试顺序依赖问题
5. **覆盖率**: 目标 80% 覆盖率

## 验收标准

- [ ] conftest.py 有完整的 fixtures
- [ ] Organizations API 80%+ 覆盖率
- [ ] Roles API 80%+ 覆盖率
- [ ] DataFlows API 80%+ 覆盖率
- [ ] Tasks API 80%+ 覆盖率
- [ ] 所有测试通过
- [ ] 可以生成覆盖率报告
