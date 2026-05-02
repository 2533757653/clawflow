# Task-01: RAG向量生成服务重构

## 项目背景

**项目**: ClawFlow - Agent组织动态构建平台
**当前问题**: `api/services/rag_service.py` 中的 `_generate_embedding` 方法使用伪随机算法，无法实现真实语义检索
**修改目标**: 接入OpenAI embedding API实现真实的向量生成

## 输入输出要求

### 输入
- 无新增输入参数
- 重构现有 `EmbeddingService._generate_embedding` 方法

### 输出
- 真实OpenAI text-embedding-ada-002 向量
- 向量维度: 1536
- 保持向后兼容的接口

## 约束条件

1. **必须使用OpenAI官方SDK** (`openai` pip包)
2. **API Key配置**: 从环境变量 `OPENAI_API_KEY` 读取，不硬编码
3. **错误处理**: API调用失败时返回降级方案（简单词频向量）而非直接崩溃
4. **性能**: 考虑添加本地缓存（TTL至少1小时）
5. **现有测试必须通过**: `api/tests/test_rag.py`

## 技术实现要求

### 1. 安装依赖
```bash
pip install openai
```

### 2. 重构EmbeddingService

**文件**: `api/services/rag_service.py`

```python
class EmbeddingService:
    def __init__(self, storage_path: str = "data/rag/embeddings",
                 model: str = "text-embedding-ada-002"):
        self.storage = StorageService[ChunkEmbedding](storage_path, ChunkEmbedding)
        self.model = model
        self._embedding_cache: Dict[str, List[float]] = {}
        # 新增: OpenAI客户端
        self._openai_client = None

    def _get_openai_client(self):
        """延迟初始化OpenAI客户端"""
        if self._openai_client is None:
            import os
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self._openai_client = OpenAI(api_key=api_key)
        return self._openai_client

    def _generate_embedding(self, text: str) -> List[float]:
        """调用OpenAI API生成真实嵌入向量"""
        try:
            client = self._get_openai_client()
            response = client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            # 降级方案: 使用简单词频向量
            logger.warning(f"OpenAI API failed: {e}, using fallback")
            return self._fallback_embedding(text)
```

### 3. 添加降级方案

当OpenAI API不可用时，使用基于词频的简单向量（供参考）:
```python
def _fallback_embedding(self, text: str) -> List[float]:
    """简单词频向量降级方案"""
    words = text.lower().split()
    dim = 1536
    vector = [0.0] * dim
    for word in words:
        idx = hash(word) % dim
        vector[idx] += 1
    # 归一化
    norm = math.sqrt(sum(v*v for v in vector))
    if norm > 0:
        vector = [v/norm for v in vector]
    return vector
```

### 4. 添加日志

在 `api/services/__init__.py` 或 `rag_service.py` 顶部添加:
```python
import logging
logger = logging.getLogger(__name__)
```

## 验收标准

1. ✅ 向量维度保持1536
2. ✅ 相同文本产生相同向量（与OpenAI一致）
3. ✅ 相似的文本产生相似的向量距离
4. ✅ API失败时优雅降级
5. ✅ 现有测试 `pytest api/tests/test_rag.py` 全部通过
6. ✅ 向量搜索结果相关性明显提升（可通过手动测试验证）

## 依赖关系

- 本任务为其他RAG相关任务的前置
- 无其他依赖

## 注意事项

1. 不要修改 `ChunkEmbedding` 模型结构
2. 缓存实现使用内存缓存即可，暂不需Redis
3. 确保环境变量文档更新（.env.example）
