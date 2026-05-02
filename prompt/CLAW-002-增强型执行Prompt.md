# ClawFlow 增强型执行Prompt - 并发处理4个核心任务

## 📋 任务概述

本Prompt用于指导执行者Agent完成ClawFlow项目的4个核心重构任务。这些任务可以**并发处理**，但需遵循指定的依赖关系。

---

## 🎯 需要完成的4个任务

| 任务编号 | 任务名称 | 优先级 | 依赖关系 |
|----------|----------|--------|----------|
| Task-01 | RAG向量生成重构 | CRITICAL | 无，可最先完成 |
| Task-02 | 工作流执行接入OpenClaw | CRITICAL | Task-01（RAG依赖） |
| Task-03 | 前端状态管理重构 | HIGH | 无，可并发 |
| Task-04 | Agent模板自动同步 | HIGH | 无，可并发 |

---

## 📁 任务Prompt文件路径

完成该文档的命令：
```
prompt/Task-01-RAG向量生成重构.md
prompt/Task-02-工作流执行接入OpenClaw.md
prompt/Task-03-前端状态管理重构.md
prompt/Task-04-Agent模板自动同步.md
```

---

## 🔧 并发处理指南

### 并发策略

**可100%并发的任务**：
- Task-01（RAG向量生成）
- Task-03（前端状态管理）
- Task-04（Agent同步）

**有依赖关系的任务**：
- Task-02 需等待 Task-01 完成后才能开始（或可先实现框架，等Task-01完成后再接入真实embedding）

### 推荐执行顺序

```
方案A（保守）:
1. 先完成 Task-01, Task-03, Task-04（可并发）
2. Task-01 完成后执行 Task-02

方案B（激进）:
1. Task-01, Task-03, Task-04 并发执行
2. Task-02 与上述任务也可部分并发，但最终需接入真实embedding
```

---

## 📝 各任务详细说明

### Task-01: RAG向量生成重构 [CRITICAL]

**问题**: 当前 `_generate_embedding` 使用伪随机算法，无法实现真实语义检索

**核心修改**:
1. 接入OpenAI text-embedding-ada-002 API
2. 添加降级方案（当API不可用时）
3. 保持1536维度兼容

**关键文件**:
- `api/services/rag_service.py` - 修改 `EmbeddingService._generate_embedding`

**验收标准**:
- ✅ 相同文本产生相同向量
- ✅ 相似的文本产生相似的向量距离
- ✅ API失败时优雅降级
- ✅ `pytest api/tests/test_rag.py` 通过

---

### Task-02: 工作流执行接入OpenClaw [CRITICAL]

**问题**: `_simulate_agent_execution` 只是返回假数据

**核心修改**:
1. 新增 `OpenClawExecutor` 类
2. 重构 `_execute_role_node` 使用真实执行
3. 添加部署检查和错误处理

**关键文件**:
- 新增: `api/services/openclaw_executor.py`
- 修改: `api/services/execution_service.py`

**验收标准**:
- ✅ 部署后的组织执行时真实调用OpenClaw
- ✅ Agent未部署时给出明确错误
- ✅ 单节点失败不影响其他节点
- ✅ 执行超时正确处理

**注意**: 本任务依赖 Task-01 的RAG重构完成后再接入真实embedding

---

### Task-03: 前端状态管理重构 [HIGH]

**问题**: Zustand store与组件状态职责不清，切换组织时数据残留

**核心修改**:
1. 修复 `setCurrentOrganization` 清空关联数据
2. 添加竞态条件防护
3. 改进错误处理

**关键文件**:
- `web/src/stores/index.ts`

**验收标准**:
- ✅ 切换组织时旧数据立即清空
- ✅ 快速切换不出现竞态条件
- ✅ TypeScript无编译错误

---

### Task-04: Agent模板自动同步 [HIGH]

**问题**: 角色修改后，已部署的Agent文件不会自动更新

**核心修改**:
1. 新增 `AgentSyncService` 类
2. 在角色更新API中触发同步
3. 支持角色重命名时的目录迁移

**关键文件**:
- 新增: `api/services/agent_sync_service.py`
- 修改: `api/routers/roles.py`

**验收标准**:
- ✅ 更新角色后Agent文件同步更新
- ✅ 角色重命名时正确处理目录迁移
- ✅ 未部署的角色更新不报错
- ✅ 提供手动同步API

---

## 🔨 执行约束

### 通用约束

1. **保持向后兼容**: 不破坏现有API接口
2. **渐进式修改**: 每次修改后确保测试通过
3. **代码质量**: 遵循项目现有代码风格
4. **文档更新**: 如有需要更新相关文档

### 环境要求

- Python 3.11+
- Node.js 18+
- pytest
- OpenAI API Key（Task-01, Task-02需要）

### 测试要求

- 修改后运行 `pytest api/tests/` 确保测试通过
- 前端修改后运行 TypeScript 编译检查

---

## ✅ 验收检查清单

完成每个任务后检查：

- [ ] 代码遵循项目规范（PEP8/ESLint）
- [ ] 无新增编译错误
- [ ] 相关测试通过
- [ ] API接口保持兼容
- [ ] 错误处理完善

---

## 📞 遇到问题时

1. **先查看项目文档**: `docs/`, `SPEC.md`
2. **查看现有代码风格**: 在修改前先阅读同类型文件的代码风格
3. **不确定时**: 先实现最小可用版本，后续再优化

---

## 附加任务（可选）

在完成上述4个核心任务后，如果时间允许，可以处理以下问题（详见 `prompt/CLAW-001-项目批评与质疑报告.md`）：

- 存储层并发控制（切换到SQLite）
- CORS配置优化
- 数据流循环依赖检测修复
- 角色删除完整性检查
