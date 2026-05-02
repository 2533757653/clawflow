from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MemoryType(str, Enum):
    CONVERSATION = "conversation"
    FACT = "fact"
    PREFERENCE = "preference"
    CONTEXT = "context"
    COMPRESSED = "compressed"


class MemoryEntry(BaseModel):
    id: str = Field(default_factory=lambda: f"mem-{datetime.now().timestamp()}")
    role_id: str
    content: str
    memory_type: MemoryType = MemoryType.CONVERSATION
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    access_count: int = 0
    last_accessed: Optional[str] = None
    importance: float = 1.0
    tags: List[str] = []
    parent_id: Optional[str] = None
    is_compressed: bool = False
    metadata: Dict[str, Any] = {}


class MemoryCompressionRequest(BaseModel):
    role_id: str
    max_entries: int = 10
    compression_prompt: Optional[str] = None


class MemoryCompressionResult(BaseModel):
    original_count: int
    compressed_count: int
    compressed_entries: List[MemoryEntry]
    removed_entries: List[str]
    summary: Optional[str] = None


class MemoryResetRequest(BaseModel):
    role_id: str
    keep_types: List[MemoryType] = [MemoryType.FACT, MemoryType.PREFERENCE]
    reason: Optional[str] = None


class MemoryResetResult(BaseModel):
    cleared_count: int
    kept_count: int
    kept_entries: List[MemoryEntry]


class MemoryStats(BaseModel):
    total_entries: int
    by_type: Dict[str, int]
    average_importance: float
    most_accessed: List[MemoryEntry]
    oldest_entry: Optional[str]
    newest_entry: Optional[str]


class PromptEnhancementRequest(BaseModel):
    role_id: str
    base_prompt: str
    max_memory_items: int = 3


class PromptEnhancementResponse(BaseModel):
    enhanced_prompt: str
    memory_used: List[dict]


class CompressionCallbackRequest(BaseModel):
    role_id: str
    compressed_content: str
    original_memory_ids: List[str]
