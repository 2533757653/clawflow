# Task-03: 前端状态管理重构

## 项目背景

**项目**: ClawFlow - Agent组织动态构建平台
**当前问题**: `web/src/stores/index.ts` 中Zustand store与组件本地状态职责不清，存在双重数据源和状态残留问题
**修改目标**: 重构为清晰的数据获取层，解决状态残留和数据同步问题

## 当前问题分析

### 问题1: 状态残留
```typescript
// currentOrganizationId 变化时，旧的 tasks/dataflows/knowledge 不会被清空
setCurrentOrganization: (orgId) => {
  set({ currentOrganizationId: orgId });
  if (orgId) {
    get().loadTasks(orgId);
    get().loadDataflows(orgId);
    get().loadKnowledge(orgId);
  }
  // ❌ 问题：没有清空旧数据
},
```

### 问题2: 双重数据源
- Store中的数据 vs 组件本地useState
- 可能导致数据不一致

### 问题3: 缺乏错误处理
- API调用失败时不清理loading状态
- 没有重试机制

## 输入输出要求

### 输入
- 现有API服务（`web/src/services/api.ts`）
- 现有路由配置（`web/src/App.tsx`）

### 输出
- 重构后的 `web/src/stores/index.ts`
- 可选：新建 `web/src/hooks/useOrganization.ts` 自定义hook

## 约束条件

1. **保持向后兼容**: 现有组件调用方式不变
2. **TypeScript严格模式**: 无any类型
3. **状态一致性**: 组织切换时自动清空关联数据
4. **错误边界**: API失败时正确处理

## 技术实现要求

### 1. 重构Store结构

**修改文件**: `web/src/stores/index.ts`

```typescript
interface OrganizationState {
  // 数据
  organizations: Organization[];
  currentOrganizationId: string | null;
  roles: Role[];

  // 组织相关数据（随currentOrganizationId切换）
  tasks: Task[];
  dataflows: DataFlow[];
  knowledge: Knowledge[];

  // 全局数据
  skills: Skill[];
  clawhubSkills: Skill[];
  ragStats: RAGStats | null;
  semanticSearchResults: SearchResult[];

  // 加载状态
  loading: {
    organizations: boolean;
    roles: boolean;
    tasks: boolean;
    dataflows: boolean;
    knowledge: boolean;
    skills: boolean;
    rag: boolean;
  };
}

interface OrganizationActions {
  setCurrentOrganization: (orgId: string | null) => void;
  // ... 其他actions
}
```

### 2. 修复状态切换逻辑

```typescript
setCurrentOrganization: (orgId) => {
  // ✅ 先清空关联数据，防止显示旧数据闪烁
  set({
    currentOrganizationId: orgId,
    tasks: [],        // 清空旧数据
    dataflows: [],    // 清空旧数据
    knowledge: [],    // 清空旧数据
  });

  if (orgId) {
    get().loadTasks(orgId);
    get().loadDataflows(orgId);
    get().loadKnowledge(orgId);
  }
},
```

### 3. 添加数据加载hooks（可选）

**新增文件**: `web/src/hooks/useOrganization.ts`

```typescript
import { useEffect } from 'react';
import { useStore } from '../stores';

export function useOrganizationData(orgId: string | null) {
  const { tasks, dataflows, knowledge, loading, loadTasks, loadDataflows, loadKnowledge } = useStore();

  useEffect(() => {
    if (orgId) {
      loadTasks(orgId);
      loadDataflows(orgId);
      loadKnowledge(orgId);
    }
  }, [orgId, loadTasks, loadDataflows, loadKnowledge]);

  return {
    tasks,
    dataflows,
    knowledge,
    isLoading: loading.tasks || loading.dataflows || loading.knowledge,
  };
}
```

### 4. 改进错误处理

```typescript
loadTasks: async (orgId) => {
  set((state) => ({ ...state, loading: { ...state.loading, tasks: true } }));
  try {
    const data = await taskApi.list(orgId);
    set((state) => ({
      ...state,
      // ✅ 只在当前组织匹配时更新，防止请求延迟导致数据错乱
      ...(state.currentOrganizationId === orgId ? { tasks: data } : {}),
      loading: { ...state.loading, tasks: false }
    }));
  } catch (error) {
    set((state) => ({ ...state, loading: { ...state.loading, tasks: false } }));
    console.error('Failed to load tasks:', error);
    throw error; // 让调用者知道失败
  }
},
```

### 5. 防止竞态条件

```typescript
let currentRequestId = 0;

loadTasks: async (orgId) => {
  const requestId = ++currentRequestId;

  set((state) => ({ ...state, loading: { ...state.loading, tasks: true } }));
  try {
    const data = await taskApi.list(orgId);

    // ✅ 检查是否是最新的请求，防止旧请求覆盖新数据
    if (requestId !== currentRequestId) {
      return;
    }

    set((state) => ({
      ...state,
      ...(state.currentOrganizationId === orgId ? { tasks: data } : {}),
      loading: { ...state.loading, tasks: false }
    }));
  } catch (error) {
    if (requestId !== currentRequestId) {
      return;
    }
    set((state) => ({ ...state, loading: { ...state.loading, tasks: false } }));
    throw error;
  }
},
```

## 验收标准

1. ✅ 切换组织时，旧数据立即清空（无闪烁）
2. ✅ 同一组织的数据不会因为切换组织而混乱
3. ✅ 请求失败时loading状态正确重置
4. ✅ 快速切换组织时不会出现竞态条件
5. ✅ TypeScript无编译错误

## 依赖关系

- **前置依赖**: 无
- **可并行**: Task-01, Task-02, Task-04

## 注意事项

1. 改动涉及多个组件，先在本地测试通过再提交
2. 考虑添加immer简化不可变更新（可选）
3. 如果项目增大，可考虑RTK Query重构，但不是本次范围
