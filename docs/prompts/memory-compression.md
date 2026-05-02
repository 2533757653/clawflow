# Prompt: 上下文记忆压缩系统

## 项目信息

- **项目名称**: ClawFlow - Agent 组织动态构建平台
- **项目路径**: `d:\clawflow`
- **后端**: `api/` (FastAPI + Python 3.11+)
- **前端**: `web/` (React 18 + TypeScript)

## 项目架构

参见 `docs/prompts/workflow-execution-engine.md`

## 已有实现

### Memory Router (部分实现)
位置: `api/routers/memory.py`

当前已实现:
- `GET /api/v1/memory/{role_id}` - 获取记忆列表
- `POST /api/v1/memory/{role_id}` - 添加记忆
- `POST /api/v1/memory/{role_id}/access/{memory_id}` - 访问记忆
- `POST /api/v1/memory/compress` - 压缩记忆
- `POST /api/v1/memory/enhance-prompt` - 增强 prompt
- `POST /api/v1/memory/{role_id}/sync` - 同步到 OpenClaw

当前 MemoryEntry 模型:
```python
class MemoryEntry(BaseModel):
    id: str
    role_id: str
    content: str
    created_at: str
    access_count: int = 0
    last_accessed: Optional[str] = None
    importance: float = 1.0
```

## 设计决策

根据 SPEC.md "设计决策记录" section 4:

### 上下文记忆管理

1. **记忆存储**: ClawFlow 本地管理，存储在 `data/memory/` 目录
2. **压缩策略**: 由用户主动触发（如 reset 指令），调用 OpenClaw 上的 Agent 完成压缩
3. **同步机制**: 记忆压缩后回调更新上下文，通过 Agent 的 memory/ 目录同步
4. **具体流程**: 用户调用 reset → Agent 压缩上下文 + 返回压缩后内容 → 回调更新上下文

## 任务要求

### 1. 增强 MemoryEntry 模型

修改 `api/models/memory.py` (或添加到 `api/models/__init__.py`):

```python
class MemoryType(str, Enum):
    CONVERSATION = "conversation"      # 对话记录
    FACT = "fact"                       # 事实信息
    PREFERENCE = "preference"            # 用户偏好
    CONTEXT = "context"                 # 上下文
    COMPRESSED = "compressed"           # 压缩后的记忆

class MemoryEntry(BaseModel):
    id: str
    role_id: str
    content: str
    memory_type: MemoryType = MemoryType.CONVERSATION
    created_at: str
    access_count: int = 0
    last_accessed: Optional[str] = None
    importance: float = 1.0
    tags: List[str] = []
    parent_id: Optional[str] = None  # 压缩后的记忆指向原始记忆
    is_compressed: bool = False
    metadata: Dict[str, Any] = {}  # 额外元数据
```

### 2. 增强 Memory Service

修改 `api/services/memory_service.py` (或增强 `api/routers/memory.py`):

```python
class MemoryService:
    """增强的记忆服务"""

    def get_memory_path(self, role_id: str) -> str:
        return os.path.join("data/memory", role_id, "entries")

    def load_entries(self, role_id: str) -> List[MemoryEntry]:
        """加载所有记忆条目"""
        ...

    def save_entries(self, role_id: str, entries: List[MemoryEntry]):
        """保存记忆条目"""
        ...

    def add_entry(
        self,
        role_id: str,
        content: str,
        memory_type: MemoryType = MemoryType.CONVERSATION,
        tags: List[str] = None
    ) -> MemoryEntry:
        """添加新记忆"""
        ...

    def calculate_importance(self, entry: MemoryEntry) -> float:
        """
        计算记忆重要性分数 (0-1)
        考虑因素:
        - 访问频率 (access_count)
        - 最近访问时间 (last_accessed)
        - 记忆类型权重 (fact > preference > conversation)
        - 用户标记的重要性
        """
        type_weights = {
            MemoryType.FACT: 1.0,
            MemoryType.PREFERENCE: 0.8,
            MemoryType.CONTEXT: 0.6,
            MemoryType.CONVERSATION: 0.4,
            MemoryType.COMPRESSED: 0.2
        }

        # 访问频率分数 (最高 0.3)
        access_score = min(0.3, entry.access_count / 20)

        # 时间衰减分数 (最高 0.3)
        recency_score = 0.3
        if entry.last_accessed:
            hours_since = (datetime.now() - datetime.fromisoformat(entry.last_accessed)).total_seconds() / 3600
            recency_score = max(0, 0.3 - (hours_since / 168) * 0.3)  # 7天衰减

        # 类型权重 (最高 0.3)
        type_score = type_weights.get(entry.memory_type, 0.4) * 0.3

        # 用户标记重要性 (最高 0.1)
        importance_score = (entry.importance / 5) * 0.1

        return access_score + recency_score + type_score + importance_score

    def compress_memories(
        self,
        role_id: str,
        max_entries: int = 10,
        compression_prompt: str = None
    ) -> MemoryCompressionResult:
        """
        压缩记忆:
        1. 加载所有记忆
        2. 按重要性排序
        3. 保留最重要的记忆
        4. 生成压缩摘要 (如果提供 prompt)
        5. 返回压缩结果
        """
        ...

    def search_memories(
        self,
        role_id: str,
        query: str,
        top_k: int = 5
    ) -> List[MemoryEntry]:
        """
        搜索记忆:
        1. 简单的关键词匹配
        2. 按相关性排序
        3. 返回 top_k 结果
        """
        ...
```

### 3. 增强压缩端点

修改 `api/routers/memory.py`:

```python
class MemoryCompressionRequest(BaseModel):
    role_id: str
    max_entries: int = 10
    compression_prompt: Optional[str] = None  # 用于生成摘要的 prompt

class MemoryCompressionResult(BaseModel):
    original_count: int
    compressed_count: int
    compressed_entries: List[MemoryEntry]
    removed_entries: List[str]
    summary: Optional[str]  # 生成的摘要

@router.post("/compress", response_model=MemoryCompressionResult)
async def compress_memories(request: MemoryCompressionRequest):
    """
    压缩记忆:
    - 保留最重要的 max_entries 条记忆
    - 如果提供 compression_prompt，生成摘要
    - 标记被压缩的记忆
    """
```

### 4. Reset 端点

```python
class MemoryResetRequest(BaseModel):
    role_id: str
    keep_types: List[MemoryType] = [MemoryType.FACT, MemoryType.PREFERENCE]  # 保留的记忆类型
    reason: Optional[str] = None

class MemoryResetResult(BaseModel):
    cleared_count: int
    kept_count: int
    kept_entries: List[MemoryEntry]

@router.post("/reset", response_model=MemoryResetResult)
async def reset_memories(request: MemoryResetRequest):
    """
    重置记忆:
    - 清除非关键记忆
    - 保留 FACT 和 PREFERENCE 类型
    - 返回清除结果
    """
```

### 5. 回调机制

```python
@router.post("/{role_id}/callback/compress")
async def handle_compression_callback(
    role_id: str,
    compressed_content: str,
    original_memory_ids: List[str]
):
    """
    处理 Agent 压缩后的回调:
    1. 创建新的 COMPRESSED 类型记忆
    2. 标记原始记忆为 is_compressed=True
    3. 更新 role 的 context_memory
    4. 同步到 OpenClaw
    """
    role = role_storage.get(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # 创建压缩记忆
    compressed_entry = MemoryEntry(
        role_id=role_id,
        content=compressed_content,
        memory_type=MemoryType.COMPRESSED,
        parent_id=original_memory_ids[0] if original_memory_ids else None,
        metadata={"original_count": len(original_memory_ids)}
    )

    # 更新角色 context_memory
    role.context_memory = compressed_content
    role_storage.save(role)

    # 同步到 OpenClaw
    memory_service.sync_to_openclaw(role_id)

    return compressed_entry
```

### 6. 同步到 OpenClaw

```python
@router.post("/{role_id}/sync")
async def sync_memories_to_openclaw(role_id: str):
    """
    同步记忆到 OpenClaw:
    1. 加载角色记忆
    2. 格式化为 context.md
    3. 写入 agents/{role_name}/memory/context.md
    """
    role = role_storage.get(role_id)
    agent_path = os.path.join("agents", role.name.lower().replace(" ", "_"))

    memory_dir = os.path.join(agent_path, "memory")
    os.makedirs(memory_dir, exist_ok=True)

    context_path = os.path.join(memory_dir, "context.md")
    entries = memory_service.load_entries(role_id)

    # 按重要性排序，只保留最重要的 20 条
    sorted_entries = sorted(entries, key=lambda e: memory_service.calculate_importance(e), reverse=True)[:20]

    content = "# 角色上下文记忆\n\n"
    content += f"最后更新: {datetime.now().isoformat()}\n"
    content += f"记忆总数: {len(entries)}\n\n"
    content += "---\n\n"

    for i, entry in enumerate(sorted_entries, 1):
        content += f"## [{entry.memory_type.value}] {entry.created_at}\n\n"
        content += f"{entry.content}\n\n"
        content += f"*重要性: {memory_service.calculate_importance(entry):.2f} | "
        content += f"访问: {entry.access_count}次*\n\n---\n\n"

    with open(context_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return {
        "memory_path": context_path,
        "entries_count": len(sorted_entries)
    }
```

### 7. 记忆统计端点

```python
class MemoryStats(BaseModel):
    total_entries: int
    by_type: Dict[str, int]
    average_importance: float
    most_accessed: List[MemoryEntry]
    oldest_entry: Optional[str]
    newest_entry: Optional[str]

@router.get("/{role_id}/stats", response_model=MemoryStats)
async def get_memory_stats(role_id: str):
    """获取记忆统计信息"""
```

## 文件结构

```
api/
├── models/
│   └── memory.py      # 新增: Memory 模型 (增强)
├── routers/
│   └── memory.py      # 修改: 增强端点
└── services/
    └── memory_service.py  # 新增: 记忆服务
```

## 前端集成

### 创建 MemoryManager 页面

`web/src/pages/MemoryManager.tsx`:

```typescript
interface MemoryManagerProps {
  roleId: string;
}

// 功能:
// - 显示记忆列表 (按重要性排序)
// - 显示记忆类型标签
// - 添加新记忆
// - 编辑记忆
// - 删除记忆
// - 手动触发压缩
// - 重置记忆
// - 查看统计
// - 同步到 OpenClaw
```

### 添加组件

`web/src/components/Memory/MemoryCard.tsx`:
- 显示单条记忆
- 显示重要性分数
- 显示访问次数
- 快捷操作按钮

`web/src/components/Memory/MemoryStats.tsx`:
- 统计图表
- 记忆分布饼图

`web/src/components/Memory/CompressionModal.tsx`:
- 压缩配置
- 预览压缩结果

## 注意事项

1. **重要性计算**: 考虑多种因素，保持分数合理
2. **压缩不可逆**: 压缩后的记忆标记为 is_compressed，但仍保留原始内容
3. **回调安全**: 验证回调来源，防止恶意注入
4. **同步频率**: 不要频繁同步，设置合理间隔
5. **存储限制**: 考虑设置最大记忆条数，防止无限增长

## 验收标准

- [ ] 记忆按重要性排序显示
- [ ] 可以添加/编辑/删除记忆
- [ ] 压缩端点正确工作
- [ ] 压缩后保留重要记忆
- [ ] Reset 端点保留关键类型记忆
- [ ] 回调更新 role.context_memory
- [ ] 同步到 OpenClaw 正确写入 context.md
- [ ] 前端有完整的 MemoryManager 页面
- [ ] 显示记忆统计信息
