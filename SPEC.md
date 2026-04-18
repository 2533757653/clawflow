# ClawFlow - Agent 组织动态构建平台

## 项目概述

**ClawFlow** 是一个用于动态构建和管理 AI Agent 组织的平台。它解决了 OpenClaw AI Agent 之间无法协作、无法形成严密有效组织的缺点，提供可视化界面让用户构建完整的公司级 AI 代理系统。

### 核心价值

- **组织可视化**：通过动态界面构建 Agent 组织架构
- **角色抽象**：定义 Agent 角色及其职责分工
- **任务编排**：抽象和分配任务给不同 Agent
- **数据流通**：可视化编辑 Agent 间的数据流
- **知识共享**：构建公有知识库供所有 Agent 访问
- **技能管理**：从 ClawHub 查询和部署所需技能
- **动态部署**：在 OpenClaw 动态创建用户构建的 Agent 组织

---

## 技术架构

### 技术栈

- **后端**：Python 3.11+ / FastAPI
- **前端**：React 18 + TypeScript + Ant Design
- **数据存储**：SQLite (开发) / PostgreSQL (生产)
- **OpenClaw 集成**：文件系统适配器

### 目录结构

```
clawflow/
├── api/                      # FastAPI 后端
│   ├── main.py              # 应用入口
│   ├── routers/             # API 路由
│   │   ├── organizations.py # 组织管理
│   │   ├── agents.py        # Agent 管理
│   │   ├── roles.py         # 角色管理
│   │   ├── tasks.py         # 任务管理
│   │   ├── dataflows.py     # 数据流管理
│   │   ├── knowledge.py     # 知识库管理
│   │   └── skills.py        # 技能管理
│   ├── models/              # 数据模型
│   ├── services/            # 业务逻辑
│   └── adapters/            # OpenClaw 适配器
├── web/                      # React 前端
│   ├── src/
│   │   ├── components/      # UI 组件
│   │   ├── pages/           # 页面
│   │   ├── stores/          # 状态管理
│   │   └── services/        # API 服务
│   └── package.json
├── data/                     # 数据存储
│   ├── organizations/        # 组织配置
│   ├── knowledge/           # 知识库文件
│   └── skills/              # 已下载技能
└── openclaw_workspace/      # OpenClaw 工作区
```

---

## 功能模块

### 1. 组织管理 (Organization)

用户可以创建多个独立的 Agent 组织，每个组织是一个完整的 AI 公司系统。

**核心功能**：
- 创建/编辑/删除组织
- 组织基础信息配置（名称、描述、logo）
- 组织状态管理（草稿/部署/运行/停止）

### 2. 角色编辑 (Role Editor)

角色是 Agent 的抽象定义，描述 Agent 的职责、能力和行为规范。

**核心功能**：
- 创建/编辑/删除角色
- 定义角色属性：
  - 名称 (name)
  - 描述 (description)
  - 核心职责 (responsibilities)
  - 所需技能 (required_skills)
  - 汇报关系 (reports_to)
  - 权限级别 (permission_level)
- 角色继承（高层 Agent 可以由低层角色组合）
- 角色模板库

### 3. 任务编辑 (Task Editor)

任务是对抽象工作的定义，描述需要完成的工作及其输入输出。

**核心功能**：
- 创建/编辑/删除任务
- 定义任务属性：
  - 任务名称 (name)
  - 任务描述 (description)
  - 输入数据 (input_data)
  - 输出数据 (output_data)
  - 执行角色 (assigned_role)
  - 依赖任务 (dependencies)
  - 优先级 (priority)
- 任务模板库
- 任务编排（顺序/并行/条件）

### 4. 数据流编辑 (DataFlow Editor)

数据流定义了 Agent 之间数据传递的通道。

**核心功能**：
- 可视化数据流设计器
- 数据节点管理：
  - 角色节点 (Agent Role)
  - 任务节点 (Task)
  - 知识库节点 (Knowledge)
  - 外部输入节点 (External Input)
  - 输出节点 (Output)
- 数据连接线（带数据转换）
- 数据流状态监控

### 5. 公有知识库 (Knowledge Base)

公有知识库存储所有 Agent 可以共享访问的知识。

**核心功能**：
- 创建/编辑/删除知识条目
- 知识分类管理
- 知识搜索
- 知识版本控制
- 访问权限管理

### 6. 技能管理 (Skill Management)

技能是 Agent 执行特定任务的能力，从 ClawHub 查询和下载。

**核心功能**：
- ClawHub 技能搜索
- 技能预览（查看 SKILL.md）
- 技能安装/卸载
- 已安装技能列表
- 技能与角色关联

### 7. OpenClaw 部署

将构建好的组织部署到 OpenClaw。

**核心功能**：
- 生成 OpenClaw Agent 文件（SOUL.md, IDENTITY.md, AGENTS.md 等）
- 同步技能到 OpenClaw 工作区
- 部署状态监控
- 一键部署/回滚

---

## 数据模型

### Organization (组织)

```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "logo": "string (url)",
  "status": "draft|deployed|running|stopped",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Role (角色)

```json
{
  "id": "uuid",
  "organization_id": "uuid",
  "name": "string",
  "description": "string",
  "responsibilities": ["string"],
  "required_skills": ["skill_id"],
  "reports_to": "role_id | null",
  "permission_level": "admin|manager|member|readonly",
  "hierarchy_level": "number",
  "soul_template": "string",
  "identity_template": "string",
  "agents_config": {},
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Task (任务)

```json
{
  "id": "uuid",
  "organization_id": "uuid",
  "name": "string",
  "description": "string",
  "input_schema": {},
  "output_schema": {},
  "assigned_role_id": "uuid",
  "dependencies": ["task_id"],
  "priority": "high|medium|low",
  "execution_mode": "sequential|parallel|conditional",
  "conditions": {},
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### DataFlow (数据流)

```json
{
  "id": "uuid",
  "organization_id": "uuid",
  "name": "string",
  "description": "string",
  "nodes": [
    {
      "id": "uuid",
      "type": "role|task|knowledge|input|output",
      "ref_id": "uuid",
      "position": {"x": "number", "y": "number"}
    }
  ],
  "edges": [
    {
      "id": "uuid",
      "source": "node_id",
      "target": "node_id",
      "data_mapping": {},
      "condition": "string | null"
    }
  ],
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Knowledge (知识)

```json
{
  "id": "uuid",
  "organization_id": "uuid",
  "title": "string",
  "content": "string",
  "category": "string",
  "tags": ["string"],
  "version": "number",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Skill (技能)

```json
{
  "id": "uuid",
  "name": "string",
  "version": "string",
  "description": "string",
  "author": "string",
  "tags": ["string"],
  "installed": "boolean",
  "installed_at": "datetime | null",
  "local_path": "string | null"
}
```

---

## API 端点

### Organizations

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/organizations | 获取组织列表 |
| POST | /api/v1/organizations | 创建组织 |
| GET | /api/v1/organizations/{id} | 获取组织详情 |
| PUT | /api/v1/organizations/{id} | 更新组织 |
| DELETE | /api/v1/organizations/{id} | 删除组织 |
| POST | /api/v1/organizations/{id}/deploy | 部署组织 |

### Roles

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/organizations/{org_id}/roles | 获取角色列表 |
| POST | /api/v1/organizations/{org_id}/roles | 创建角色 |
| GET | /api/v1/organizations/{org_id}/roles/{id} | 获取角色详情 |
| PUT | /api/v1/organizations/{org_id}/roles/{id} | 更新角色 |
| DELETE | /api/v1/organizations/{org_id}/roles/{id} | 删除角色 |

### Tasks

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/organizations/{org_id}/tasks | 获取任务列表 |
| POST | /api/v1/organizations/{org_id}/tasks | 创建任务 |
| GET | /api/v1/organizations/{org_id}/tasks/{id} | 获取任务详情 |
| PUT | /api/v1/organizations/{org_id}/tasks/{id} | 更新任务 |
| DELETE | /api/v1/organizations/{org_id}/tasks/{id} | 删除任务 |

### DataFlows

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/organizations/{org_id}/dataflows | 获取数据流列表 |
| POST | /api/v1/organizations/{org_id}/dataflows | 创建数据流 |
| GET | /api/v1/organizations/{org_id}/dataflows/{id} | 获取数据流详情 |
| PUT | /api/v1/organizations/{org_id}/dataflows/{id} | 更新数据流 |
| DELETE | /api/v1/organizations/{org_id}/dataflows/{id} | 删除数据流 |

### Knowledge

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/organizations/{org_id}/knowledge | 获取知识列表 |
| POST | /api/v1/organizations/{org_id}/knowledge | 创建知识条目 |
| GET | /api/v1/organizations/{org_id}/knowledge/{id} | 获取知识详情 |
| PUT | /api/v1/organizations/{org_id}/knowledge/{id} | 更新知识 |
| DELETE | /api/v1/organizations/{org_id}/knowledge/{id} | 删除知识 |

### Skills

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/skills | 获取已安装技能列表 |
| GET | /api/v1/skills/search | 从 ClawHub 搜索技能 |
| GET | /api/v1/skills/{id}/preview | 预览技能详情 |
| POST | /api/v1/skills/{id}/install | 安装技能 |
| DELETE | /api/v1/skills/{id}/uninstall | 卸载技能 |

---

## 前端页面

### 1. 组织概览 (Dashboard)
- 组织列表和状态
- 快速创建新组织
- 组织健康度指标

### 2. 组织编辑器 (Organization Editor)
- 组织基本信息编辑
- 组织架构可视化树形图

### 3. 角色管理 (Role Management)
- 角色列表和搜索
- 角色编辑器（表单）
- 角色关系可视化

### 4. 任务管理 (Task Management)
- 任务列表（看板视图）
- 任务编辑器（表单）
- 任务依赖关系图

### 5. 数据流设计器 (DataFlow Designer)
- 可视化画布
- 拖拽式节点放置
- 连线编辑
- 缩放和平移

### 6. 知识库 (Knowledge Base)
- 知识列表
- 知识编辑器（富文本）
- 知识分类和标签

### 7. 技能中心 (Skill Center)
- ClawHub 搜索
- 已安装技能列表
- 技能详情预览

### 8. 部署中心 (Deployment Center)
- 部署状态监控
- 一键部署
- 部署历史

---

## OpenClaw 适配器

适配器负责将 ClawFlow 组织配置转换为 OpenClaw Agent 文件。

### 文件映射

| ClawFlow | OpenClaw |
|----------|----------|
| Role.name | Agent 目录名 |
| Role.soul_template | SOUL.md |
| Role.identity_template | IDENTITY.md |
| Role.agents_config | AGENTS.md |
| Task 定义 | HEARTBEAT.md |
| 技能引用 | skills/ 目录 |

### 生成流程

1. 为每个 Role 创建目录
2. 生成 SOUL.md (从模板)
3. 生成 IDENTITY.md (从模板)
4. 生成 AGENTS.md (包含组织信息)
5. 生成 BOOTSTRAP.md (首次运行引导)
6. 复制所需技能到 skills/ 目录

---

## 验收标准

### 核心功能
- [ ] 可以创建、编辑、删除组织
- [ ] 可以创建、编辑、删除角色，角色可设置汇报关系
- [ ] 可以创建、编辑、删除任务，任务可设置依赖关系
- [ ] 可以可视化编辑数据流（节点和连线）
- [ ] 可以管理公有知识库
- [ ] 可以从 ClawHub 搜索和安装技能
- [ ] 可以将组织部署到 OpenClaw

### 界面交互
- [ ] 数据流设计器支持拖拽添加节点
- [ ] 数据流设计器支持节点连线
- [ ] 角色关系以树形图展示
- [ ] 任务关系以看板展示

### 技术要求
- [ ] API 响应时间 < 200ms
- [ ] 前端无明显卡顿
- [ ] 配置文件持久化到磁盘
- [ ] 错误处理完善，用户提示清晰

---

## 术语表

| 术语 | 定义 |
|------|------|
| OpenClaw | 一个 AI Agent 框架，每个 Agent 由多个 Markdown 文件定义 |
| Agent | OpenClaw 中的 AI 代理实例 |
| Organization | ClawFlow 中的 Agent 组织 |
| Role | 角色的抽象定义，类似公司中的职位 |
| Task | 抽象任务的定义，描述工作内容 |
| DataFlow | 数据在 Agent 之间流动的通道 |
| Knowledge | 公有知识库中的条目 |
| Skill | Agent 的能力模块，可从 ClawHub 获取 |
| ClawHub | 技能市场，提供可共享的 Skill |
