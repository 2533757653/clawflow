import os
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from api.models.memory import (
    MemoryEntry,
    MemoryType,
    MemoryCompressionResult,
    MemoryStats
)
from api.services.ai_client import chat_completion, is_ai_available

logger = logging.getLogger(__name__)


class MemoryService:
    MEMORY_PATH = "data/memory"

    def get_memory_path(self, role_id: str) -> str:
        path = os.path.join(self.MEMORY_PATH, role_id)
        os.makedirs(path, exist_ok=True)
        return path

    def get_memory_registry_path(self) -> str:
        os.makedirs(self.MEMORY_PATH, exist_ok=True)
        return os.path.join(self.MEMORY_PATH, "registry.json")

    def load_entries(self, role_id: str) -> List[MemoryEntry]:
        registry_path = self.get_memory_registry_path()
        if not os.path.exists(registry_path):
            return []

        with open(registry_path, 'r', encoding='utf-8') as f:
            all_entries = json.load(f)

        return [MemoryEntry(**e) for e in all_entries if e.get('role_id') == role_id]

    def save_entries(self, role_id: str, entries: List[MemoryEntry]):
        registry_path = self.get_memory_registry_path()

        if os.path.exists(registry_path):
            with open(registry_path, 'r', encoding='utf-8') as f:
                all_entries = json.load(f)
        else:
            all_entries = []

        all_entries = [e for e in all_entries if e.get('role_id') != role_id]
        all_entries.extend([e.model_dump() for e in entries])

        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(all_entries, f, ensure_ascii=False, indent=2)

    def add_entry(
        self,
        role_id: str,
        content: str,
        memory_type: MemoryType = MemoryType.CONVERSATION,
        tags: List[str] = None,
        importance: float = 1.0
    ) -> MemoryEntry:
        entry = MemoryEntry(
            id=f"mem-{datetime.now().timestamp()}",
            role_id=role_id,
            content=content,
            memory_type=memory_type,
            tags=tags or [],
            importance=importance,
            created_at=datetime.now().isoformat()
        )

        entries = self.load_entries(role_id)
        entries.append(entry)
        self.save_entries(role_id, entries)

        return entry

    def update_entry(self, role_id: str, memory_id: str, content: str) -> Optional[MemoryEntry]:
        entries = self.load_entries(role_id)
        for entry in entries:
            if entry.id == memory_id:
                entry.content = content
                self.save_entries(role_id, entries)
                return entry
        return None

    def delete_entry(self, role_id: str, memory_id: str) -> bool:
        entries = self.load_entries(role_id)
        original_count = len(entries)
        entries = [e for e in entries if e.id != memory_id]

        if len(entries) == original_count:
            return False

        self.save_entries(role_id, entries)
        return True

    def access_entry(self, role_id: str, memory_id: str) -> Optional[MemoryEntry]:
        entries = self.load_entries(role_id)
        for entry in entries:
            if entry.id == memory_id:
                entry.access_count += 1
                entry.last_accessed = datetime.now().isoformat()
                self.save_entries(role_id, entries)
                return entry
        return None

    def calculate_importance(self, entry: MemoryEntry) -> float:
        type_weights = {
            MemoryType.FACT: 1.0,
            MemoryType.PREFERENCE: 0.8,
            MemoryType.CONTEXT: 0.6,
            MemoryType.CONVERSATION: 0.4,
            MemoryType.COMPRESSED: 0.2
        }

        access_score = min(0.3, entry.access_count / 20)

        recency_score = 0.3
        if entry.last_accessed:
            hours_since = (datetime.now() - datetime.fromisoformat(entry.last_accessed)).total_seconds() / 3600
            recency_score = max(0, 0.3 - (hours_since / 168) * 0.3)

        type_score = type_weights.get(entry.memory_type, 0.4) * 0.3

        importance_score = (entry.importance / 5) * 0.1

        return access_score + recency_score + type_score + importance_score

    def get_sorted_entries(self, role_id: str) -> List[MemoryEntry]:
        entries = self.load_entries(role_id)
        return sorted(entries, key=lambda e: self.calculate_importance(e), reverse=True)

    def compress_memories(
        self,
        role_id: str,
        max_entries: int = 10,
        compression_prompt: str = None
    ) -> MemoryCompressionResult:
        entries = self.load_entries(role_id)

        if len(entries) <= max_entries:
            return MemoryCompressionResult(
                original_count=len(entries),
                compressed_count=len(entries),
                compressed_entries=entries,
                removed_entries=[],
                summary=None
            )

        sorted_entries = sorted(entries, key=lambda e: self.calculate_importance(e), reverse=True)
        kept = sorted_entries[:max_entries]
        removed = sorted_entries[max_entries:]

        for entry in kept:
            entry.is_compressed = True

        self.save_entries(role_id, kept)

        summary = None
        if is_ai_available() and removed:
            summary = self._ai_summarize_removed_memories(removed, kept)
        elif compression_prompt:
            summary = f"Compressed {len(removed)} memories into {len(kept)} important entries."
        else:
            summary = f"Compressed {len(removed)} memories into {len(kept)} important entries."

        return MemoryCompressionResult(
            original_count=len(entries),
            compressed_count=len(kept),
            compressed_entries=kept,
            removed_entries=[e.id for e in removed],
            summary=summary
        )

    def _ai_summarize_removed_memories(
        self,
        removed: List[MemoryEntry],
        kept: List[MemoryEntry]
    ) -> str:
        """Use AI to generate a narrative summary of discarded memories."""
        memories_text = "\n".join([
            f"- [{e.memory_type.value}] {e.content}" for e in removed
        ])

        system_prompt = (
            "You are a memory consolidation assistant. "
            "Given a list of discarded memories, generate a concise 2-3 sentence summary "
            "that preserves the key information. "
            "Return ONLY the summary text, no JSON, no explanation."
        )
        user_prompt = (
            f"Discarded memories:\n{memories_text}\n\n"
            f"Write a brief summary (max 200 chars) that captures the essence of "
            f"the discarded memories."
        )

        result = chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model="doubao-seed-2-0-pro-260215",
            temperature=0.5,
            max_tokens=150,
        )

        if result:
            return f"Compressed summary: {result.strip()}"
        return f"Compressed {len(removed)} memories into {len(kept)} important entries."

    def reset_memories(
        self,
        role_id: str,
        keep_types: List[MemoryType] = None
    ) -> tuple[List[MemoryEntry], int]:
        if keep_types is None:
            keep_types = [MemoryType.FACT, MemoryType.PREFERENCE]

        entries = self.load_entries(role_id)
        kept = [e for e in entries if e.memory_type in keep_types]
        cleared_count = len(entries) - len(kept)

        self.save_entries(role_id, kept)

        return kept, cleared_count

    def search_memories(
        self,
        role_id: str,
        query: str,
        top_k: int = 5
    ) -> List[MemoryEntry]:
        entries = self.load_entries(role_id)
        query_lower = query.lower()

        matched = []
        for entry in entries:
            if query_lower in entry.content.lower():
                matched.append(entry)
            elif any(query_lower in tag.lower() for tag in entry.tags):
                matched.append(entry)

        matched.sort(key=lambda e: self.calculate_importance(e), reverse=True)
        return matched[:top_k]

    def get_stats(self, role_id: str) -> MemoryStats:
        entries = self.load_entries(role_id)

        if not entries:
            return MemoryStats(
                total_entries=0,
                by_type={},
                average_importance=0.0,
                most_accessed=[],
                oldest_entry=None,
                newest_entry=None
            )

        by_type: Dict[str, int] = {}
        for entry in entries:
            type_val = entry.memory_type.value
            by_type[type_val] = by_type.get(type_val, 0) + 1

        total_importance = sum(self.calculate_importance(e) for e in entries)
        avg_importance = total_importance / len(entries) if entries else 0.0

        sorted_by_access = sorted(entries, key=lambda e: e.access_count, reverse=True)
        most_accessed = sorted_by_access[:5]

        sorted_by_created = sorted(entries, key=lambda e: e.created_at)
        oldest = sorted_by_created[0].created_at if sorted_by_created else None
        newest = sorted_by_created[-1].created_at if sorted_by_created else None

        return MemoryStats(
            total_entries=len(entries),
            by_type=by_type,
            average_importance=round(avg_importance, 2),
            most_accessed=most_accessed,
            oldest_entry=oldest,
            newest_entry=newest
        )

    def sync_to_openclaw(self, role_id: str, role_name: str = None) -> Dict[str, Any]:
        entries = self.load_entries(role_id)

        agent_name = (role_name or role_id).lower().replace(" ", "_")
        memory_dir = os.path.join("agents", agent_name, "memory")
        os.makedirs(memory_dir, exist_ok=True)

        context_path = os.path.join(memory_dir, "context.md")

        sorted_entries = sorted(entries, key=lambda e: self.calculate_importance(e), reverse=True)[:20]

        content = "# 角色上下文记忆\n\n"
        content += f"最后更新: {datetime.now().isoformat()}\n"
        content += f"记忆总数: {len(entries)}\n\n"
        content += "---\n\n"

        for i, entry in enumerate(sorted_entries, 1):
            content += f"## [{entry.memory_type.value}] {entry.created_at}\n\n"
            content += f"{entry.content}\n\n"
            content += f"*重要性: {self.calculate_importance(entry):.2f} | "
            content += f"访问: {entry.access_count}次*\n\n---\n\n"

        with open(context_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return {
            "memory_path": context_path,
            "entries_count": len(sorted_entries)
        }

    def enhance_prompt(
        self,
        role_id: str,
        base_prompt: str,
        max_memory_items: int = 3
    ) -> tuple[str, List[Dict[str, Any]]]:
        entries = self.load_entries(role_id)

        if not entries:
            return base_prompt, []

        sorted_entries = sorted(entries, key=lambda e: self.calculate_importance(e), reverse=True)
        selected = sorted_entries[:max_memory_items]

        memory_context = "\n\n## 相关记忆\n"
        memory_used = []

        for i, entry in enumerate(selected, 1):
            memory_context += f"\n### 记忆 {i}\n{entry.content}\n"
            memory_used.append({
                "id": entry.id,
                "preview": entry.content[:50] + "..." if len(entry.content) > 50 else entry.content,
                "importance": round(self.calculate_importance(entry), 2)
            })

            entry.access_count += 1
            entry.last_accessed = datetime.now().isoformat()

        self.save_entries(role_id, entries)

        enhanced = f"{base_prompt}{memory_context}"
        return enhanced, memory_used


memory_service = MemoryService()
