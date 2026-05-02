# Prompt: RAG 公用数据库

## 项目信息

- **项目名称**: ClawFlow - Agent 组织动态构建平台
- **项目路径**: `d:\clawflow`
- **后端**: `api/` (FastAPI + Python 3.11+)
- **前端**: `web/` (React 18 + TypeScript)

## 项目架构

参见 `docs/prompts/workflow-execution-engine.md`

## 已有实现

### RAG Router (已实现)
位置: `api/routers/rag.py`

已实现端点:
- `POST /api/v1/rag/query` - RAG 查询
- `POST /api/v1/rag/index/knowledge-base/{org_id}` - 索引知识库
- `GET /api/v1/rag/stats` - RAG 统计

### RAG Service (已实现)
位置: `api/services/rag_service.py`

已实现组件:
- `DocumentService` - 文档管理服务
- `ChunkService` - 文本分块服务，支持按句子边界分割、重叠窗口
- `EmbeddingService` - Embedding 生成服务，支持缓存
- `VectorStore` - 向量存储，支持余弦相似度搜索
- `RAGService` - 核心 RAG 服务，整合各组件

### Knowledge Router (已实现)
位置: `api/routers/knowledge.py`

已实现端点:
- `GET /api/v1/organizations/{org_id}/knowledge` - 列表
- `POST /api/v1/organizations/{org_id}/knowledge` - 创建
- `PUT /api/v1/organizations/{org_id}/knowledge/{knowledge_id}` - 更新
- `DELETE /api/v1/organizations/{org_id}/knowledge/{knowledge_id}` - 删除
- `GET /api/v1/organizations/{org_id}/knowledge/search` - 关键词搜索
- `POST /api/v1/organizations/{org_id}/knowledge/inject` - Prompt 注入
- `POST /api/v1/organizations/{org_id}/knowledge/inject/{knowledge_id}` - 单条知识注入

### RAG Models (已实现)
位置: `api/models/rag_models.py`

已实现模型:
- `Document` / `DocumentStatus` / `DocumentType` - 文档模型
- `Chunk` - 分块模型
- `ChunkEmbedding` - Embedding 存储模型
- `RAGQuery` / `RAGResult` / `RAGResponse` - RAG 查询/响应模型

### Knowledge Model (已实现)
位置: `api/models/__init__.py`

```python
class Knowledge(BaseModel):
    id: str
    organization_id: str
    title: str
    content: str
    category: Optional[str]
    tags: List[str]
    version: int = 1
```

## 设计决策

根据 SPEC.md "设计决策记录" section 6:

### RAG 与知识库

1. **RAG 模型预定义但暂不启用** - 当前使用简化的 embedding 实现
2. **知识库作为组织级的公用数据库使用**
3. **知识库内容在构建 prompt 时作为上下文注入**
4. **后续可扩展为完整的 RAG 向量检索功能**

### 当前实现状态

- **Embedding**: 使用简化的基于字符的 embedding 生成，维度 1536
- **分块策略**: 按句子边界分割 (，。！？；\n.!?;)，支持重叠窗口
- **相似度计算**: 余弦相似度
- **存储**: JSON 文件存储，通过 StorageService 管理

## 任务要求

以下任务已在 `api/services/rag_service.py` 中实现:

### 1. 知识库分块 (已实现)

`ChunkService.chunk_text()` 方法:

```python
def chunk_text(self, text: str, chunk_size: int = 500,
               overlap: int = 50) -> List[str]:
    sentences = self._split_into_sentences(text)
    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        sentence_length = len(sentence)
        if current_length + sentence_length > chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            overlap_words = ' '.join(current_chunk).split()[-overlap:]
            current_chunk = overlap_words + [sentence]
            current_length = sum(len(w) for w in current_chunk) + len(current_chunk)
        else:
            current_chunk.append(sentence)
            current_length += sentence_length

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks
```

### 2. Embedding 生成 (已实现)

`EmbeddingService` 类:

```python
class EmbeddingService:
    def __init__(self, storage_path: str = "data/rag/embeddings",
                 model: str = "text-embedding-ada-002"):
        self.storage = StorageService[ChunkEmbedding](storage_path, ChunkEmbedding)
        self.model = model
        self._embedding_cache: Dict[str, List[float]] = {}

    def get_embedding(self, text: str, use_cache: bool = True) -> List[float]:
        cache_key = text[:100]
        if use_cache and cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]
        embedding = self._generate_embedding(text)
        if use_cache:
            self._embedding_cache[cache_key] = embedding
        return embedding

    def _generate_embedding(self, text: str) -> List[float]:
        norm = sum((ord(c) % 100) / 100 for c in text[:min(len(text), 100)])
        dim = 1536
        embedding = []
        for i in range(dim):
            seed = (norm * 1000 + i * 7) % 100 / 100
            embedding.append(math.sin(seed * math.pi))
        magnitude = math.sqrt(sum(e ** 2 for e in embedding))
        embedding = [e / magnitude for e in embedding]
        return embedding
```

### 3. 相似度计算 (已实现)

`VectorStore._cosine_similarity()` 方法:

```python
def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)
```

### 4. RAG Service (已实现)

`RAGService` 类主要方法:

```python
class RAGService:
    def __init__(self):
        self.doc_service = DocumentService()
        self.chunk_service = ChunkService()
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self._load_embeddings()

    def index_document(self, doc: Document, chunk_size: int = 500,
                       overlap: int = 50) -> List[Chunk]:
        # 1. 分块
        # 2. 生成 embedding
        # 3. 存储到 vector store
        ...

    def query(self, rag_query: RAGQuery) -> RAGResponse:
        # 1. 生成 query embedding
        # 2. 搜索相似 chunks
        # 3. 返回结果
        ...

    def index_knowledge_base(self, organization_id: str,
                             knowledge_items: List[Dict[str, Any]]) -> int:
        # 批量索引知识库
        ...
```

### 5. 知识注入 API (已实现)

`api/routers/knowledge.py` 中的端点:

```python
class PromptInjectionRequest(BaseModel):
    base_prompt: str
    include_knowledge: bool = True
    max_knowledge_items: int = 5

class PromptInjectionResponse(BaseModel):
    enhanced_prompt: str
    knowledge_used: List[dict]

@router.post("/{org_id}/knowledge/inject")
async def inject_knowledge(
    org_id: str,
    request: PromptInjectionRequest
):
    # 1. 获取所有知识
    # 2. 选择 top-k 条知识
    # 3. 格式化知识上下文
    # 4. 追加到 base_prompt
    ...
```

### 6. 知识搜索 API (已实现)

`api/routers/knowledge.py` 中的端点:

```python
@router.get("/{org_id}/knowledge/search")
async def search_knowledge(org_id: str, q: str):
    # 关键词搜索: 匹配 title, content, category, tags
    storage = get_knowledge_storage(org_id)
    all_knowledge = storage.list()
    query = q.lower()
    results = [
        kb for kb in all_knowledge
        if query in kb.title.lower() or query in kb.content.lower() or
           (kb.category and query in kb.category.lower()) or
           any(query in tag.lower() for tag in kb.tags)
    ]
    return results
```

### 7. 索引知识库 (已实现)

`api/routers/rag.py` 中的端点:

```python
@router.post("/api/v1/rag/index/knowledge-base/{org_id}")
async def index_knowledge_base(org_id: str):
    # 1. 获取组织所有知识
    # 2. 转换为 Document
    # 3. 批量索引
    ...
```

## 文件结构

```
api/
├── services/
│   ├── rag_service.py       # 已实现: DocumentService, ChunkService,
│   │                        #         EmbeddingService, VectorStore, RAGService
│   └── storage.py           # 已存在: StorageService
├── routers/
│   ├── knowledge.py         # 已实现: CRUD + inject + search
│   └── rag.py               # 已实现: query + index + stats
└── models/
    ├── rag_models.py        # 已实现: Document, Chunk, ChunkEmbedding,
    │                         #         RAGQuery, RAGResult, RAGResponse
    └── __init__.py           # 已实现: Knowledge

web/src/
├── components/
│   └── Knowledge/
│       ├── SearchPanel.tsx       # 新增: 语义搜索面板
│       ├── InjectionPreview.tsx # 新增: Prompt 注入预览
│       └── IndexStatus.tsx      # 新增: 索引状态显示
├── pages/
│   └── KnowledgeBase.tsx        # 增强: 添加标签页
├── services/
│   └── api.ts                  # 增强: 添加 ragApi
└── stores/
    └── index.ts                 # 增强: 添加 RAG 状态和操作
```

## 前端集成

### 现有 KnowledgeBase 页面
位置: `web/src/pages/KnowledgeBase.tsx`

已实现功能:
- 知识列表展示 (Table)
- 添加/编辑/删除知识
- 关键词搜索
- 知识预览
- Prompt 注入预览 (通过 inject 端点)
- **新增**: 语义搜索标签页
- **新增**: 注入预览标签页
- **新增**: 索引状态标签页

### 已实现组件

`web/src/components/Knowledge/SearchPanel.tsx`:
- 搜索输入框
- 搜索结果列表 (语义搜索 + 关键词搜索 切换)
- 结果高亮

`web/src/components/Knowledge/InjectionPreview.tsx`:
- 原始 prompt 显示
- 注入后的 prompt 显示
- 使用的知识列表

`web/src/components/Knowledge/IndexStatus.tsx`:
- 索引状态指示
- Chunk 数量统计
- 重建索引按钮

## 注意事项

1. **Embedding 简化**: 当前使用基于字符的简化版 embedding，后续可升级到真正的向量模型 (OpenAI text-embedding-ada-002, Sentence-BERT 等)
2. **索引性能**: 大量知识时考虑异步索引
3. **存储管理**: 定期清理 orphaned chunks
4. **相似度阈值**: 设置最小相似度阈值，过滤低相关结果
5. **向量维度**: 当前为 1536，与 OpenAI ada-002 一致

## 验收标准

- [x] 知识可以分块存储 (ChunkService.chunk_text)
- [x] 生成文本 embedding (EmbeddingService.get_embedding)
- [x] 相似度搜索正确工作 (VectorStore.search + _cosine_similarity)
- [x] 知识注入 API 正确返回增强后的 prompt (/knowledge/inject)
- [x] 搜索 API 返回相关知识 (/knowledge/search - 关键词搜索)
- [x] RAG 语义搜索集成到前端 (SearchPanel 组件)
- [x] 注入预览功能集成到前端 (InjectionPreview 组件)
- [x] 索引状态显示集成到前端 (IndexStatus 组件)

## API 端点汇总

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/v1/organizations/{org_id}/knowledge` | 获取知识列表 |
| POST | `/api/v1/organizations/{org_id}/knowledge` | 创建知识 |
| GET | `/api/v1/organizations/{org_id}/knowledge/{id}` | 获取单条知识 |
| PUT | `/api/v1/organizations/{org_id}/knowledge/{id}` | 更新知识 |
| DELETE | `/api/v1/organizations/{org_id}/knowledge/{id}` | 删除知识 |
| GET | `/api/v1/organizations/{org_id}/knowledge/search?q=` | 关键词搜索 |
| POST | `/api/v1/organizations/{org_id}/knowledge/inject` | Prompt 注入 |
| POST | `/api/v1/rag/query` | RAG 语义查询 |
| POST | `/api/v1/rag/index/knowledge-base/{org_id}` | 索引知识库 |
| GET | `/api/v1/rag/stats` | RAG 统计信息 |
