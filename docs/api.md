# ClawFlow API 文档

## 基础信息

- **基础路径**：`http://localhost:8000/api/v1`
- **内容类型**：`application/json`
- **认证**：暂无（开发中）

## 健康检查

### GET /health

检查服务状态。

**响应**：
```json
{
    "status": "healthy",
    "message": "ClawFlow API is running"
}
```

---

## 组织管理 (Organizations)

### 创建组织

**POST** `/organizations`

**请求体**：
```json
{
    "name": "My Company",
    "description": "A sample company"
}
```

**响应** (201)：
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "My Company",
    "description": "A sample company",
    "status": "draft",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
}
```

### 获取组织列表

**GET** `/organizations`

**响应** (200)：
```json
[
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "My Company",
        "status": "draft",
        ...
    }
]
```

### 获取组织详情

**GET** `/organizations/{org_id}`

**响应** (200)：
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "My Company",
    "description": "A sample company",
    "status": "draft",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
}
```

### 更新组织

**PUT** `/organizations/{org_id}`

**请求体**：
```json
{
    "name": "Updated Company",
    "description": "Updated description"
}
```

### 删除组织

**DELETE** `/organizations/{org_id}`

**响应** (204 No Content)

### 部署组织

**POST** `/organizations/{org_id}/deploy`

将组织部署到 OpenClaw 工作区。

**响应** (200)：
```json
{
    "message": "Organization deployed successfully",
    "deployed_agents": [
        {
            "role_id": "role-uuid",
            "role_name": "CEO",
            "deployed_at": "2024-01-01T00:00:00"
        }
    ],
    "total_roles": 5
}
```

### 取消部署

**POST** `/organizations/{org_id}/undeploy`

---

## 角色管理 (Roles)

### 创建角色

**POST** `/organizations/{org_id}/roles`

**请求体**：
```json
{
    "name": "Software Engineer",
    "description": "Writes code",
    "hierarchy_level": 1,
    "permission_level": "member",
    "responsibilities": ["Write code", "Review PRs"],
    "required_skills": ["python", "javascript"]
}
```

**字段说明**：
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 角色名称 |
| description | string | 否 | 角色描述 |
| hierarchy_level | int | 否 | 层级 (1-4)，默认 1 |
| permission_level | string | 否 | 权限级别 |
| reports_to | string | 否 | 汇报对象角色 ID |
| responsibilities | array | 否 | 职责列表 |
| required_skills | array | 否 | 所需技能列表 |

### 获取角色列表

**GET** `/organizations/{org_id}/roles`

### 获取角色详情

**GET** `/organizations/{org_id}/roles/{role_id}`

### 更新角色

**PUT** `/organizations/{org_id}/roles/{role_id}`

### 删除角色

**DELETE** `/organizations/{org_id}/roles/{role_id}`

### 获取角色层级

**GET** `/organizations/{org_id}/roles/{role_id}/hierarchy`

获取角色的完整层级树。

**响应**：
```json
{
    "id": "role-uuid",
    "name": "CEO",
    "description": "Chief Executive Officer",
    "hierarchy_level": 4,
    "permission_level": "admin",
    "children": [
        {
            "id": "cto-uuid",
            "name": "CTO",
            "hierarchy_level": 3,
            "children": [...]
        }
    ]
}
```

---

## 任务管理 (Tasks)

### 创建任务

**POST** `/organizations/{org_id}/tasks`

**请求体**：
```json
{
    "name": "Code Review",
    "description": "Review pull requests",
    "priority": "high",
    "execution_mode": "sequential",
    "assigned_role_id": "role-uuid",
    "dependencies": []
}
```

**字段说明**：
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 任务名称 |
| description | string | 否 | 任务描述 |
| priority | string | 否 | high/medium/low |
| execution_mode | string | 否 | sequential/parallel/conditional |
| assigned_role_id | string | 否 | 执行角色 ID |
| dependencies | array | 否 | 依赖任务 ID 列表 |

### 获取任务列表

**GET** `/organizations/{org_id}/tasks`

### 获取任务详情

**GET** `/organizations/{org_id}/tasks/{task_id}`

### 更新任务

**PUT** `/organizations/{org_id}/tasks/{task_id}`

### 删除任务

**DELETE** `/organizations/{org_id}/tasks/{task_id}`

### 获取任务依赖

**GET** `/organizations/{org_id}/tasks/{task_id}/dependencies`

获取任务及其依赖任务的完整链路。

---

## 数据流管理 (DataFlows)

### 创建数据流

**POST** `/organizations/{org_id}/dataflows`

**请求体**：
```json
{
    "name": "Order Processing",
    "description": "Handle order from placement to delivery"
}
```

### 获取数据流列表

**GET** `/organizations/{org_id}/dataflows`

### 获取数据流详情

**GET** `/organizations/{org_id}/dataflows/{dataflow_id}`

**响应**：
```json
{
    "id": "df-uuid",
    "organization_id": "org-uuid",
    "name": "Order Processing",
    "description": "Handle order from placement to delivery",
    "nodes": [
        {
            "id": "node-uuid",
            "type": "input",
            "position": {"x": 100, "y": 100},
            "label": "Order Received"
        },
        {
            "id": "node-uuid-2",
            "type": "role",
            "ref_id": "role-uuid",
            "position": {"x": 250, "y": 100},
            "label": "Order Processor"
        }
    ],
    "edges": [
        {
            "id": "edge-uuid",
            "source": "node-uuid",
            "target": "node-uuid-2",
            "data_mapping": {},
            "condition": null
        }
    ],
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
}
```

### 更新数据流

**PUT** `/organizations/{org_id}/dataflows/{dataflow_id}`

### 删除数据流

**DELETE** `/organizations/{org_id}/dataflows/{dataflow_id}`

---

## 知识库管理 (Knowledge)

### 创建知识条目

**POST** `/organizations/{org_id}/knowledge`

**请求体**：
```json
{
    "title": "Company Policy",
    "content": "This is the company policy document...",
    "category": "公司制度",
    "tags": ["policy", "hr", "规则"]
}
```

### 获取知识列表

**GET** `/organizations/{org_id}/knowledge`

### 获取知识详情

**GET** `/organizations/{org_id}/knowledge/{knowledge_id}`

### 更新知识

**PUT** `/organizations/{org_id}/knowledge/{knowledge_id}`

### 删除知识

**DELETE** `/organizations/{org_id}/knowledge/{knowledge_id}`

### 搜索知识

**GET** `/organizations/{org_id}/knowledge/search?q={query}`

---

## 技能管理 (Skills)

### 获取已安装技能

**GET** `/skills`

**响应**：
```json
[
    {
        "id": "skill-uuid",
        "name": "hr-policy-generator-cn",
        "version": "1.0.0",
        "description": "HR policy generator",
        "author": "hr-policy",
        "tags": ["hr", "人力资源"],
        "installed": true,
        "installed_at": "2024-01-01T00:00:00",
        "local_path": "data/skills/hr-policy-generator-cn"
    }
]
```

### 搜索 ClawHub 技能

**GET** `/skills/search?q={query}&tag={tag}`

**响应**：
```json
[
    {
        "id": "skill-hr-policy-cn",
        "name": "hr-policy-generator-cn",
        "version": "1.0.0",
        "description": "综合性 HR 政策设计工具",
        "author": "hr-policy",
        "tags": ["hr", "人力资源", "考勤"],
        "installed": false
    }
]
```

### 安装技能

**POST** `/skills/{skill_id}/install`

**响应**：
```json
{
    "id": "skill-hr-policy-cn",
    "name": "hr-policy-generator-cn",
    "version": "1.0.0",
    "installed": true,
    "installed_at": "2024-01-01T00:00:00",
    "local_path": "data/skills/hr-policy-generator-cn"
}
```

### 卸载技能

**DELETE** `/skills/{skill_id}/uninstall`

**响应** (204 No Content)

---

## 错误响应

所有 API 错误返回统一格式：

```json
{
    "detail": "Error message"
}
```

### 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 204 | 删除成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 状态枚举

### OrganizationStatus
- `draft` - 草稿
- `deployed` - 已部署
- `running` - 运行中
- `stopped` - 已停止

### PermissionLevel
- `admin` - 管理员
- `manager` - 经理
- `member` - 成员
- `readonly` - 只读

### Priority
- `high` - 高
- `medium` - 中
- `low` - 低

### ExecutionMode
- `sequential` - 顺序执行
- `parallel` - 并行执行
- `conditional` - 条件执行

### NodeType
- `role` - 角色节点
- `task` - 任务节点
- `knowledge` - 知识节点
- `input` - 输入节点
- `output` - 输出节点
