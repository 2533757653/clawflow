# ClawFlow 项目开发流程指南

## 概述

本指南用于指导 ClawFlow 项目的代码审查、设计讨论和任务分解流程。通过系统化的方法，确保每个功能都能被准确理解、正确设计和高效实现。

---

## 流程总览

```
┌─────────────────────────────────────────────────────────────┐
│                    完整开发流程                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Phase 1: 全面代码审查                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 1.1 读取项目架构文档 (README, SPEC, architecture)    │   │
│  │ 1.2 读取核心模型定义                                  │   │
│  │ 1.3 读取关键服务和路由实现                             │   │
│  │ 1.4 读取前端核心代码                                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                         ↓                                  │
│  Phase 2: 问题识别与设计讨论                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 2.1 识别实现与 SPEC 的不一致                          │   │
│  │ 2.2 识别设计缺陷和矛盾                                 │   │
│  │ 2.3 识别缺失的功能模块                                 │   │
│  │ 2.4 向用户提问确认设计意图                             │   │
│  └─────────────────────────────────────────────────────┘   │
│                         ↓                                  │
│  Phase 3: 修复已有问题                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 3.1 修复 SPEC 与实现的不一致                          │   │
│  │ 3.2 修复明显的 bug                                    │   │
│  │ 3.3 更新文档记录设计决策                              │   │
│  └─────────────────────────────────────────────────────┘   │
│                         ↓                                  │
│  Phase 4: 生成任务 Prompts                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 4.1 为每个待实现功能生成详细 prompt                    │   │
│  │ 4.2 包含项目上下文、设计决策、代码模板                  │   │
│  │ 4.3 包含验收标准                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                         ↓                                  │
│  Phase 5: 分发执行                                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 5.1 并发分发 prompts 给多个 agents                    │   │
│  │ 5.2 收集执行结果                                      │   │
│  │ 5.3 处理冲突和依赖                                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: 全面代码审查

### 1.1 读取项目文档

必须读取以下文件以理解项目背景：

```
项目根目录/
├── README.md                    # 项目简介
├── SPEC.md                      # 功能规格说明（重要）
└── docs/
    └── architecture.md          # 系统架构
```

### 1.2 读取核心模型定义

位置：`api/models/__init__.py`

需要理解的核心模型：

| 模型 | 用途 | 关键字段 |
|------|------|---------|
| Organization | 组织 | name, status, role_ids, input_role_id |
| Role | 角色（全局资源） | name, responsibilities, soul_template |
| Task | 任务 | organization_id, assigned_role_id, prompt |
| DataFlow | 数据流 | nodes, edges |
| DataFlowNode | 数据流节点 | id, type, ref_id, position |
| DataFlowEdge | 数据流边 | source, target, data_mapping |

### 1.3 读取关键服务

| 服务 | 位置 | 用途 |
|------|------|------|
| StorageService | api/services/storage.py | JSON 文件存储 |
| OpenClawAdapter | api/services/openclaw_adapter.py | OpenClaw 部署 |
| RAGService | api/services/rag_service.py | 知识库检索 |

### 1.4 读取路由实现

按以下顺序阅读：

```
api/routers/
├── organizations.py    # 组织管理
├── roles.py            # 角色管理
├── tasks.py            # 任务管理
├── dataflows.py        # 数据流管理
├── knowledge.py        # 知识库
├── memory.py           # 记忆管理
└── rag.py              # RAG 查询
```

### 1.5 读取前端代码

```
web/src/
├── types/index.ts      # TypeScript 类型
├── stores/index.ts     # 状态管理
├── services/api.ts     # API 调用
└── pages/
    ├── Dashboard.tsx
    ├── OrganizationEditor.tsx
    ├── RoleEditor.tsx
    ├── DataFlowEditor.tsx
    └── ...
```

---

## Phase 2: 问题识别与设计讨论

### 2.1 需要识别的问题类型

#### 严重问题（必须修复）
- 实现与 SPEC 描述不一致
- 数据丢失（如保存时不完整）
- 安全漏洞
- 核心逻辑错误

#### 设计疑问（需要用户确认）
- 概念模糊（组织与角色的关系）
- 流程不清晰（数据流如何驱动工作流）
- 职责不清（某个功能由谁负责）

#### 代码质量问题（可选修复）
- 错误处理不完善
- 性能问题
- 代码重复

### 2.2 向用户提问的模板

```markdown
## 🔴 严重问题

### N. [问题标题]
**位置**: [file:line]

**问题描述**:
[具体问题]

**代码片段**:
```python
# 问题代码
```

**疑问**:
[向用户提问]
```

```markdown
## 🟡 设计疑问

### N. [疑问标题]
**背景**: [为什么有这个疑问]

**疑问**:
[具体问题]
```

### 2.3 用户回答后的处理

收集用户回答，更新对设计的理解：

| 概念 | 设计意图 |
|------|---------|
| 组织 | 横向容器，管理数据流、session、公用数据库、工作任务 |
| 角色 | 全局资源，被组织引用，自身不知道属于哪个组织 |
| 数据流 + 任务 | = 工作流 |
| input_role | 接收用户输入的入口角色 |

---

## Phase 3: 修复已有问题

### 3.1 修复优先级

1. **SPEC 与实现不一致** - 立即修复
2. **数据丢失 bug** - 立即修复
3. **明显错误** - 立即修复
4. **代码质量问题** - 可选

### 3.2 修复后必须更新文档

如果修改了设计决策，必须同步更新：
- `SPEC.md` - 功能规格
- `docs/architecture.md` - 架构文档
- `docs/prompts/README.md` - 如果是任务相关

### 3.3 设计决策记录格式

在 SPEC.md 中添加：

```markdown
## 设计决策记录

### YYYY-MM-DD 核心设计讨论

#### N. [决策标题]

**设计决策**：
- [具体决策]

**背景**：
- [为什么做这个决策]

**影响**：
- [对其他部分的影响]
```

---

## Phase 4: 生成任务 Prompts

### 4.1 Prompt 文件结构

每个 prompt 文件应包含：

```
# Prompt: [功能名称]

## 项目信息
- 项目名称
- 项目路径
- 技术栈

## 项目架构
[引用 workflow-execution-engine.md 的架构部分]

## 已有实现
[列出已实现的组件和位置]

## 设计决策
[从 SPEC.md 或用户回答中提取的设计决策]

## 任务要求
[详细的实现步骤]

## 文件结构
[需要创建/修改的文件列表]

## 前端集成
[如果涉及前端]

## 注意事项
[实现注意点]

## 验收标准
- [ ] 标准1
- [ ] 标准2
```

### 4.2 Prompt 存放位置

```
docs/prompts/
├── README.md                      # 索引
├── workflow-execution-engine.md   # 工作流执行引擎
├── input-role-trigger.md          # 输入角色触发
├── memory-compression.md          # 记忆压缩
├── rag-knowledge-base.md          # RAG 知识库
├── hr-agent-responsibilities.md   # HR Agent
├── dataflow-visualization.md      # 数据流可视化
└── api-testing.md                # API 测试
```

### 4.3 依赖关系分析

| Prompt | 依赖 | 可并发？ |
|--------|------|---------|
| workflow-execution-engine | 无 | ✅ |
| input-role-trigger | Session 模型 | ✅ |
| memory-compression | 现有 memory router | ⚠️ 改同一文件 |
| rag-knowledge-base | 现有 rag_service | ⚠️ 改同一文件 |
| hr-agent-responsibilities | 无 | ✅ |
| dataflow-visualization | 无 | ✅ |
| api-testing | 功能实现后 | ⏳ |

---

## Phase 5: 分发执行

### 5.1 Agent 分发模板

```markdown
# Prompt for [功能名称]

## Context
[简要描述]

## Project Location
- Project root: d:\clawflow
- Backend: api/
- Frontend: web/

## Design Reference
参见 `docs/prompts/[功能名].md`

## Task Description
[任务描述]

## Requirements
[具体要求]

## Files to Create/Modify
- Create: `path/to/file.py`
- Modify: `path/to/file.py`

## Important
- [注意事项]

## Acceptance Criteria
- [ ] 标准1
- [ ] 标准2
```

### 5.2 并发执行策略

可以安全并发的任务：
- workflow-execution-engine
- input-role-trigger
- hr-agent-responsibilities
- dataflow-visualization

需要注意文件冲突的：
- memory-compression 和 rag-knowledge-base（会改同一文件）
- 建议串行或分批

### 5.3 执行结果收集

Agents 返回的内容：
- 创建/修改的文件列表
- 验收标准完成情况
- 遇到的问题

---

## 常用命令参考

### Python 后端
```bash
cd d:\clawflow\api
pip install -r requirements.txt
python -m uvicorn api.main:app --reload
pytest -v
```

### React 前端
```bash
cd d:\clawflow\web
npm install
npm run dev
```

---

## 模板文件

### 代码审查报告模板

```markdown
## 代码审查报告

### 项目: ClawFlow
### 日期: YYYY-MM-DD
### 审查人: AI Assistant

---

## 🔴 严重问题

### 1. [问题标题]
**位置**: [file:line]

**问题**:
[描述]

**建议**:
[修复建议]

---

## 🟡 设计疑问

### 1. [疑问标题]
**背景**: [背景]

**疑问**: [问题]

---

## 🟢 代码质量问题

### 1. [问题标题]
**位置**: [file:line]

**问题**: [描述]
**建议**: [建议]
```

### 任务 Prompt 模板

```markdown
# Prompt: [功能名称]

## 项目信息
- 项目名称: ClawFlow - Agent 组织动态构建平台
- 项目路径: `d:\clawflow`
- 后端: `api/` (FastAPI + Python 3.11+)
- 前端: `web/` (React 18 + TypeScript)

## 项目架构
[复制架构图]

## 已有实现
[列出已实现的组件]

## 设计决策
[从用户回答或 SPEC 中提取]

## 任务要求
[详细步骤]

## 文件结构
```
api/
├── routers/
│   └── xxx.py      # 新增/修改
└── services/
    └── xxx.py      # 新增/修改
```

## 验收标准
- [ ] [标准1]
- [ ] [标准2]
```
