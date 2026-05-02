# ClawFlow - Agent 组织动态构建平台

## 项目概述

**ClawFlow** 是一个用于动态构建和管理 AI Agent 组织的平台。它解决了 OpenClaw AI Agent 之间无法协作、无法形成严密有效组织的缺点，提供可视化界面让用户构建完整的公司级 AI 代理系统。

### 核心价值

- **组织可视化**：通过动态界面构建 Agent 组织架构
- **角色抽象**：定义 Agent 角色及其职责分工
- **任务编排**：通过 prompt 将数据流转换为工作流
- **数据流通**：可视化编辑 Agent 间的数据流
- **知识共享**：构建组织级知识库，prompt 构建时注入
- **技能管理**：从 ClawHub 查询和部署所需技能，对单个角色安装
- **动态部署**：在 OpenClaw 动态创建独立的 Agent

---

## 技术架构

### 技术栈

- **后端**：Python 3.11+ / FastAPI
- **前端**：React 18 + TypeScript + Ant Design + ReactFlow
- **数据存储**：JSON 文件 (开发) / PostgreSQL (生产)
- **OpenClaw 集成**：文件系统适配器

### 目录结构

```
clawflow/
├── api/                      # FastAPI 后端
│   ├── main.py              # 应用入口
│   ├── routers/             # API 路由
│   │   ├── organizations.py # 组织管理
│   │   ├── roles.py         # 角色管理
│   │   ├── tasks.py         # 任务管理
│   │   ├── dataflows.py     # 数据流管理
│   │   ├── knowledge.py     # 知识库管理
│   │   └── skills.py        # 技能管理
│   ├── models/              # 数据模型
│   └── services/            # 业务逻辑
├── web/                      # React 前端
│   ├── src/
│   │   ├── components/      # UI 组件
│   │   ├── pages/           # 页面
│   │   ├── stores/          # 状态管理
│   │   └── services/        # API 服务
│   └── package.json
├── data/                     # ClawFlow 本地存储
│   ├── organizations/       # 组织配置
│   ├── knowledge/           # 知识库文件
│   └── skills/              # 已下载技能
└── agents/                   # OpenClaw Agents（部署后）
     ├── role-A/              # 一个角色 = 一个 OpenClaw Agent
     │   ├── SOUL.md
     │   ├── IDENTITY.md
     │   ├── agents/         # OpenClaw 内部子代理
     │   ├── skills/         # 角色 A 的技能
     │   └── memory/         # 角色 A 的记忆
     └── role-B/
         └── ...
```

---

## 核心概念

### 角色 = Agent

**重要**：在 ClawFlow 中，**每个角色是一个独立的 OpenClaw Agent**。

- 角色在**全局唯一**
- 每个角色拥有独立的 workspace（SOUL.md, IDENTITY.md, skills/, memory/）
- OpenClaw 中的 Agent 就是 ClawFlow 中的角色

### 组织是 ClawFlow 概念

- 组织是 ClawFlow 用来管理和组织多个角色的容器
- OpenClaw 不知道"组织"的存在，只知道一个个独立的 Agent
- 组织配置、数据流、任务、知识库都存储在 ClawFlow 本地

### 数据流 vs 任务

| 概念 | 作用 |
|------|------|
| **数据流** | 控制数据的方向（输入→角色A→角色B→输出） |
| **任务** | 基于数据流，在特定节点添加 prompt，将数据流转换为工作流 |

### 存储分离

| 内容 | 存储位置 |
|------|----------|
| Agent 定义（角色 + 技能） | **OpenClaw** (`agents/` 目录) |
| 数据流 | **本地** (`data/organizations/{org_id}/dataflows`) |
| 任务（含 prompt） | **本地** (`data/organizations/{org_id}/tasks`) |
| 知识库 | **本地** (`data/organizations/{org_id}/knowledge`) |
| 组织配置 | **本地** (`data/organizations`) |
| 上下文记忆 | **本地**（ClawFlow 控制压缩） |

---

## 设计决策记录

### 2026-04-18 核心设计讨论

#### 1. 组织与角色的关系

**设计决策**：
- **角色是全局资源**：角色存储在 `data/roles/` 目录，在全局唯一
- **组织通过 role_ids 引用角色**：Organization 模型包含 `role_ids: List[str]` 字段，存储组织包含的角色 ID 列表
- **角色无需知道所属组织**：角色自身不存储 organization_id，组织自己管理包含哪些角色
- **多组织复用**：同一角色可以被多个组织引用

**部署影响**：
- 部署组织时，只部署 `role_ids` 中包含的角色，而非全局所有角色

#### 2. 数据流 + 任务管理 = 工作流

**设计决策**：
- **数据流**：定义 Agent 之间数据传递的通道和控制方向（输入→角色A→角色B→输出）
- **任务**：基于数据流，在特定节点添加 prompt，将数据流转换为可执行的工作流
- **节点关联**：数据流节点通过 `ref_id` 关联具体的 Role/Task/Knowledge 实体
- **连线映射**：通过 `data_mapping` 配置节点间的数据传递关系

#### 3. 用户输入入口 (input_role)

**设计决策**：
- Organization 包含 `input_role_id` 字段，指定接收外部输入的角色
- 用户输入的 prompt 发送给 `input_role_id` 对应的角色
- 该角色被触发后，根据数据流生成传递给下一个角色的 prompt
- 形成完整的工作流链路

#### 4. 上下文记忆管理

**设计决策**：
- **记忆存储**：ClawFlow 本地管理，存储在 `data/memory/` 目录
- **压缩策略**：由用户主动触发（如 reset 指令），调用 OpenClaw 上的 Agent 完成压缩
- **同步机制**：记忆压缩后回调更新上下文，通过 Agent 的 memory/ 目录同步
- **具体流程**：用户调用 reset → Agent 压缩上下文 + 返回压缩后内容 → 回调更新上下文

#### 5. agency-agents 导入功能

**设计决策**：
- agency-agents（https://github.com/msitarzewski/agency-agents）包含 144+ 专业 AI Agent 模板
- 提供从 agency-agents 导入角色到 ClawFlow 的功能
- 导入的角色作为模板，可在 ClawFlow 中进一步编辑和定制
- 角色来源标记为 `source: "agency-agents"`

#### 6. RAG 与知识库

**设计决策**：
- RAG 模型预定义但暂不启用
- 知识库作为组织级的公用数据库使用
- 知识库内容在构建 prompt 时作为上下文注入
- 后续可扩展为完整的 RAG 向量检索功能

#### 7. 角色职责填充

**设计决策**：
- 用户创建角色后，职责（responsibilities）和 soul_template 需要填充
- 计划使用 HR Agent 来辅助编辑和生成角色职责
- 可在角色基本创建完成后，由 Agent 完成细节填充

---

## 功能模块

### 1. 组织管理 (Organization)

用户可以创建多个独立的 Agent 组织，每个组织可以包含多个角色（Agent）。

**核心功能**：
- 创建/编辑/删除组织
- 组织基础信息配置（名称、描述、logo）
- 组织状态管理：
  - **草稿 (draft)**：初始状态
  - **部署 (deployed)**：已部署到 OpenClaw
  - **开启 (running)**：正在运行，接收外部输入
  - **停止 (stopped)**：已停止

**组织开启**：将用户输入的初始 prompt 传递给组织中负责接收外部输入的角色。

### 2. 组织设置 (Organization Settings)

**核心功能**：
- 组织基本信息编辑
- **动态组件化页面**：通过拖拽组件、添加组件、删除组件的方式构建组织基本概括
- 可视化组织架构

### 3. 角色管理 (Role Editor)

角色是独立的 OpenClaw Agent，拥有唯一的身份和能力。

**核心功能**：
- 创建/编辑/删除角色
- 角色在**全局唯一**
- 定义角色属性：
  - 名称 (name)
  - 描述 (description)
  - 核心职责 (responsibilities)
  - 所需技能 (required_skills)
  - 汇报关系 (reports_to)
  - 权限级别 (permission_level)
  - 层级 (hierarchy_level)
- 角色模板库
- **上下文记忆**：通过不同的上下文记忆区分相同角色的不同实例

### 4. 任务编辑 (Task Editor)

任务是基于数据流的工作单元，通过 prompt 将数据流转换为工作流。

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
  - 执行模式 (execution_mode)
- **任务 prompt**：在任务节点添加 prompt，定义数据流如何转换为工作流
- 任务编排（顺序/并行/条件）

### 5. 数据流编辑 (DataFlow Editor)

数据流定义了 Agent 之间数据传递的通道。

**核心功能**：
- 可视化数据流设计器
- 数据节点管理：
  - 角色节点 (Role)
  - 任务节点 (Task)
  - 知识库节点 (Knowledge)
  - 外部输入节点 (External Input)
  - 输出节点 (Output)
- 数据连接线（带数据转换）
- 数据流状态监控

### 6. 知识库 (Knowledge Base)

知识库与组织绑定，不与角色绑定。构建 prompt 时将知识库内容作为上下文注入。

**核心功能**：
- 创建/编辑/删除知识条目
- 知识分类管理
- 知识搜索
- 知识版本控制
- **prompt 注入**：构建 prompt 时自动注入相关知识

### 7. 技能管理 (Skill Management)

技能是 Agent 执行特定任务的能力，从 ClawHub 查询和下载，安装在**单个角色**上。

**核心功能**：
- ClawHub 技能搜索
- 技能预览（查看 SKILL.md）
- 技能安装/卸载（对单个角色）
- 已安装技能列表
- 技能与角色关联

### 8. OpenClaw 部署

将角色部署为独立的 OpenClaw Agent。

**核心功能**：
- 为每个角色创建独立的 Agent 目录
- 生成 OpenClaw Agent 文件（SOUL.md, IDENTITY.md, agents/ 等）
- 同步技能到角色的 skills/ 目录
- 部署状态监控
- 一键部署/回滚

### 9. 上下文记忆管理 (Context Memory)

ClawFlow 本地管理角色的上下文记忆，主动控制记忆压缩。

**核心功能**：
- 记忆存储（本地）
- 记忆压缩策略
- 记忆检索
- 与 OpenClaw memory/ 目录同步

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
  "initial_prompt": "string | null",
  "input_role_id": "uuid | null",
  "role_ids": ["uuid"],
  "layout": [],
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**注意**：
- `role_ids` 存储此组织包含的角色 ID 列表，角色是全局资源
- `layout` 存储组织设置页面的可视化组件配置
```

### Role (角色)

```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "responsibilities": ["string"],
  "required_skills": ["skill_id"],
  "reports_to": "role_id | null",
  "permission_level": "admin|manager|member|readonly",
  "hierarchy_level": "number",
  "soul_template": "string",
  "identity_template": "string",
  "context_memory": "string | null",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**注意**：
- `organization_id` 不再存储在 Role 中，角色是全局唯一的
- `context_memory` 用于存储角色的上下文记忆

### Task (任务)

```json
{
  "id": "uuid",
  "organization_id": "uuid",
  "name": "string",
  "description": "string",
  "prompt": "string | null",
  "input_schema": {},
  "output_schema": {},
  "assigned_role_id": "uuid | null",
  "dependencies": ["task_id"],
  "priority": "high|medium|low",
  "execution_mode": "sequential|parallel|conditional",
  "conditions": {},
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**注意**：
- `prompt` 字段用于存储任务节点的 prompt，将数据流转换为工作流

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
      "ref_id": "uuid | null",
      "position": {"x": "number", "y": "number"},
      "label": "string | null"
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
  "installed_roles": ["role_id"],
  "local_path": "string | null"
}
```

**注意**：
- `installed_roles` 记录技能被安装到了哪些角色

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
| POST | /api/v1/organizations/{id}/deploy | 部署组织到 OpenClaw |
| POST | /api/v1/organizations/{id}/start | 开启组织（接收输入） |
| POST | /api/v1/organizations/{id}/stop | 停止组织 |

### Roles

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/roles | 获取所有角色（全局） |
| POST | /api/v1/roles | 创建角色 |
| GET | /api/v1/roles/{id} | 获取角色详情 |
| PUT | /api/v1/roles/{id} | 更新角色 |
| DELETE | /api/v1/roles/{id} | 删除角色 |
| GET | /api/v1/organizations/{org_id}/roles | 获取指定组织包含的角色列表 |

**说明**：角色是全局资源，存储在 `data/roles/` 目录。组织通过 `role_ids` 字段引用角色。

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
| POST | /api/v1/skills/{id}/install | 安装技能到角色 |
| DELETE | /api/v1/skills/{id}/uninstall | 卸载技能 |
| GET | /api/v1/roles/{role_id}/skills | 获取角色已安装技能 |
| POST | /api/v1/roles/{role_id}/skills/{skill_id}/install | 对角色安装技能 |

---

## 前端页面

### 1. 组织概览 (Dashboard)
- 组织列表和状态
- 快速创建新组织
- 组织状态操作（部署/开启/停止/删除）

### 2. 组织设置 (Organization Settings)
- 组织基本信息编辑
- **动态组件化页面**：拖拽添加组件、删除组件、配置组件

### 3. 角色管理 (Role Management)
- 全局角色列表
- 角色编辑器（表单）
- 角色上下文记忆配置
- 角色关系可视化

### 4. 任务管理 (Task Management)
- 任务列表
- 任务编辑器（表单 + prompt 编辑）
- 任务依赖关系图

### 5. 数据流设计器 (DataFlow Designer)
- 可视化画布（ReactFlow）
- 拖拽式节点放置
- 连线编辑
- 任务节点 prompt 配置
- 缩放和平移

### 6. 知识库 (Knowledge Base)
- 知识列表
- 知识编辑器（富文本）
- 知识分类和标签
- prompt 注入预览

### 7. 技能中心 (Skill Center)
- ClawHub 搜索
- 已安装技能列表
- 技能详情预览
- **按角色安装**：选择角色后安装技能

### 8. 上下文记忆 (Context Memory)
- 记忆列表
- 记忆压缩配置
- 记忆检索测试

---

## OpenClaw 适配器

适配器负责将 ClawFlow 角色配置转换为 OpenClaw Agent 文件。

### 文件映射

| ClawFlow | OpenClaw |
|----------|----------|
| Role.name | Agent 目录名 |
| Role.soul_template | SOUL.md |
| Role.identity_template | IDENTITY.md |
| Role.context_memory | memory/ 目录 |
| Skill | skills/ 目录 |

### 目录结构

```
agents/
└── {role_name}/              # 一个角色 = 一个 OpenClaw Agent
    ├── SOUL.md              # 角色灵魂
    ├── IDENTITY.md          # 角色身份
    ├── agents/              # OpenClaw 内部子代理
    ├── skills/              # 角色技能
    │   ├── skill-A/
    │   └── skill-B/
    └── memory/              # 上下文记忆（ClawFlow 管理）
```

### 生成流程

1. 为每个角色创建 Agent 目录
2. 生成 SOUL.md（从模板）
3. 生成 IDENTITY.md（从模板）
4. 复制已安装技能到 skills/ 目录
5. 同步 memory/ 内容

---

## 验收标准

### 核心功能
- [ ] 可以创建、编辑、删除组织
- [ ] 组织支持开启/停止操作
- [ ] 可以创建、编辑、删除角色（全局唯一）
- [ ] 角色可设置上下文记忆
- [ ] 可以创建、编辑、删除任务，任务可设置 prompt
- [ ] 可以可视化编辑数据流（节点和连线）
- [ ] 可以管理组织级知识库
- [ ] 知识库可注入到 prompt
- [ ] 可以从 ClawHub 搜索和安装技能
- [ ] 可以对单个角色安装技能
- [ ] 可以将角色部署到 OpenClaw
- [ ] 可以管理上下文记忆

### 界面交互
- [ ] 组织设置支持拖拽组件
- [ ] 数据流设计器支持拖拽添加节点
- [ ] 数据流设计器支持节点连线
- [ ] 角色关系以树形图展示
- [ ] 任务关系以看板展示

### 技术要求
- [ ] API 响应时间 < 200ms
- [ ] 前端无明显卡顿
- [ ] 配置文件持久化到磁盘
- [ ] 错误处理完善，用户提示清晰
- [ ] OpenClaw Agent 独立运行

---

## 术语表

| 术语 | 定义 |
|------|------|
| OpenClaw | 一个 AI Agent 框架，每个 Agent 由多个 Markdown 文件定义 |
| Agent | OpenClaw 中的 AI 代理实例，在 ClawFlow 中即角色 |
| Organization | ClawFlow 中的 Agent 组织，OpenClaw 不知道此概念 |
| Role | 角色的抽象定义，同时也是一个独立的 OpenClaw Agent |
| Task | 基于数据流的工作单元，通过 prompt 转换为工作流 |
| DataFlow | 数据在 Agent 之间流动的通道，控制方向 |
| Knowledge | 组织级知识库，构建 prompt 时注入 |
| Skill | Agent 的能力模块，可从 ClawHub 获取，安装在角色上 |
| ClawHub | 技能市场，提供可共享的 Skill |
| Context Memory | 角色的上下文记忆，ClawFlow 本地管理和压缩 |
