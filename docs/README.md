# ClawFlow

**Agent 组织动态构建平台**

## 概述

ClawFlow 是一个用于动态构建和管理 AI Agent 组织的平台。它解决了 OpenClaw AI Agent 之间无法协作、无法形成严密有效组织的缺点，提供可视化界面让用户构建完整的公司级 AI 代理系统。

## 核心价值

- **组织可视化**：通过动态界面构建 Agent 组织架构
- **角色抽象**：定义 Agent 角色及其职责分工
- **任务编排**：抽象和分配任务给不同 Agent
- **数据流通**：可视化编辑 Agent 间的数据流
- **知识共享**：构建公有知识库供所有 Agent 访问
- **技能管理**：从 ClawHub 查询和部署所需技能
- **动态部署**：在 OpenClaw 动态创建用户构建的 Agent 组织

## 技术栈

- **后端**：Python 3.11+ / FastAPI
- **前端**：React 18 + Ant Design (CDN 内嵌)
- **数据存储**：JSON 文件 (开发) / PostgreSQL (生产可选)
- **OpenClaw 集成**：文件系统适配器

## 快速开始

### 启动服务

```bash
cd d:\clawflow
uvicorn api.main:app --reload --port 8000
```

### 访问应用

打开浏览器访问：http://localhost:8000

### 创建第一个组织

1. 点击「+ 创建组织」按钮
2. 输入组织名称和描述
3. 在「角色管理」中创建角色并设置汇报关系
4. 在「任务管理」中定义抽象任务
5. 在「数据流设计」中设计数据流向
6. 在「知识库」中添加共享知识
7. 在「技能中心」安装所需技能
8. 点击「部署到 OpenClaw」完成部署

## 功能模块

| 模块 | 说明 |
|------|------|
| 组织概览 | 查看和管理所有组织，显示统计信息 |
| 角色管理 | 创建/编辑角色，设置层级和汇报关系 |
| 任务管理 | 定义抽象任务，设置优先级和依赖关系 |
| 数据流设计 | 可视化设计 Agent 间的数据流向 |
| 公有知识库 | 构建供所有 Agent 共享的知识库 |
| 技能中心 | 从 ClawHub 搜索和安装技能 |
| 组织设置 | 配置组织信息和部署管理 |

## 项目结构

```
clawflow/
├── api/                      # FastAPI 后端
│   ├── main.py              # 应用入口
│   ├── models/              # Pydantic 数据模型
│   │   └── rag_models.py    # RAG 相关模型
│   ├── routers/             # API 路由
│   │   ├── organizations.py
│   │   ├── roles.py
│   │   ├── tasks.py
│   │   ├── dataflows.py
│   │   ├── knowledge.py
│   │   └── skills.py
│   └── services/            # 业务逻辑
│       ├── storage.py           # JSON 存储服务
│       ├── openclaw_adapter.py   # OpenClaw 部署适配器
│       └── rag_service.py        # RAG 服务
├── docs/                    # 项目文档
├── data/                    # 数据存储
│   ├── organizations/       # 组织配置
│   ├── knowledge/           # 知识库文件
│   └── skills/             # 已下载技能
└── openclaw_workspace/      # OpenClaw 工作区
```

## 设计理念

### 角色层级

ClawFlow 支持构建多层级 Agent 组织：

- **Level 1**: 基础角色 - 执行具体任务
- **Level 2**: 小组负责人 - 协调多个基础角色
- **Level 3**: 部门负责人 - 管理多个小组
- **Level 4**: 高层管理 - 制定策略和决策

### 任务编排

任务可以设置：
- 执行模式：顺序执行、并行执行、条件执行
- 依赖关系：前置任务完成后才能执行
- 角色分配：指定执行角色

### 数据流

数据流定义了 Agent 之间数据传递的通道：
- 角色节点：代表执行者
- 任务节点：代表具体工作
- 知识节点：代表数据源/汇
- 输入/输出节点：代表外部交互

## License

MIT
