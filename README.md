# ClawFlow

Agent 组织动态构建平台 - 可视化构建和管理 AI Agent 组织架构。

[English](README_en.md) | 简体中文

## 项目简介

ClawFlow 是一个用于动态构建和管理 AI Agent 组织的平台。它解决了 OpenClaw AI Agent 之间无法协作、无法形成严密有效组织的缺点，提供可视化界面让用户构建完整的公司级 AI 代理系统。

### 核心功能

- **组织可视化** - 通过动态界面构建 Agent 组织架构
- **角色抽象** - 定义 Agent 角色及其职责分工
- **任务编排** - 抽象和分配任务给不同 Agent
- **数据流通** - 可视化编辑 Agent 间的数据流
- **知识共享** - 构建公有知识库供所有 Agent 访问
- **技能管理** - 从 ClawHub 查询和部署所需技能
- **动态部署** - 在 OpenClaw 动态创建用户构建的 Agent 组织

## 技术栈

- **后端**: Python 3.11+ / FastAPI
- **前端**: React 18 + TypeScript + Ant Design
- **数据存储**: JSON 文件 (开发) / 可扩展至 PostgreSQL (生产)
- **OpenClaw 集成**: 文件系统适配器

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- npm 或 yarn

### 安装

```bash
# 克隆项目
git clone https://github.com/yourusername/clawflow.git
cd clawflow

# 安装后端依赖
cd api
pip install -r requirements.txt

# 安装前端依赖
cd ../web
npm install
```

### 运行

```bash
# 启动后端 (在 api 目录)
cd api
uvicorn main:app --reload --port 8000

# 启动前端 (在新终端, 在 web 目录)
cd web
npm run dev
```

访问 http://localhost:5173 查看应用。

## 项目结构

```
clawflow/
├── api/                    # FastAPI 后端
│   ├── main.py            # 应用入口
│   ├── routers/           # API 路由
│   │   ├── organizations.py
│   │   ├── roles.py
│   │   ├── tasks.py
│   │   ├── dataflows.py
│   │   ├── knowledge.py
│   │   ├── skills.py
│   │   ├── systems.py
│   │   ├── generator.py
│   │   └── rag.py
│   ├── models/            # 数据模型
│   ├── services/         # 业务逻辑
│   └── tests/             # 测试
├── web/                    # React 前端
│   ├── src/
│   │   ├── pages/        # 页面组件
│   │   ├── services/     # API 服务
│   │   ├── stores/       # 状态管理
│   │   └── types/        # TypeScript 类型
│   └── package.json
├── data/                   # 数据存储
│   ├── organizations/     # 组织配置
│   ├── rag/              # RAG 数据
│   └── skills/           # 已下载技能
└── docs/                   # 项目文档
```

## API 文档

启动后端服务后，访问 http://localhost:8000/docs 查看 Swagger API 文档。

### 主要 API 端点

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/organizations | 获取组织列表 |
| POST | /api/v1/organizations | 创建组织 |
| GET | /api/v1/organizations/{id} | 获取组织详情 |
| PUT | /api/v1/organizations/{id} | 更新组织 |
| DELETE | /api/v1/organizations/{id} | 删除组织 |
| GET | /api/v1/skills | 获取技能列表 |
| GET | /api/v1/skills/search | 搜索技能 |
| POST | /api/v1/generator/generate | 生成 Agent 配置 |

## 开发指南

### 运行测试

```bash
cd api
pytest
```

### 构建前端

```bash
cd web
npm run build
```

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License
