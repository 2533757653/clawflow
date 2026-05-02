import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from api.models.memory import (
    MemoryEntry,
    MemoryType,
    MemoryCompressionRequest,
    MemoryCompressionResult,
    MemoryResetRequest,
    MemoryResetResult,
    MemoryStats,
    PromptEnhancementRequest,
    PromptEnhancementResponse,
    CompressionCallbackRequest
)
from api.services.memory_service import memory_service

logger = logging.getLogger(__name__)

router = APIRouter()


# ─── Static-path routes (must be before /{role_id} to avoid being captured) ───

@router.post("/compress", response_model=MemoryCompressionResult)
async def compress_memories(request: MemoryCompressionRequest):
    result = memory_service.compress_memories(
        request.role_id,
        request.max_entries,
        request.compression_prompt
    )
    ratio = result.original_count and result.compressed_count / result.original_count or 0
    logger.info(f"Compressed memories for role={request.role_id}: {result.original_count}→{result.compressed_count} ({ratio:.0%})")
    return result


@router.post("/reset", response_model=MemoryResetResult)
async def reset_memories(request: MemoryResetRequest):
    kept, cleared_count = memory_service.reset_memories(
        request.role_id,
        request.keep_types
    )
    logger.info(f"Reset memories for role={request.role_id}: cleared={cleared_count}, kept={len(kept)}")
    return MemoryResetResult(
        cleared_count=cleared_count,
        kept_count=len(kept),
        kept_entries=kept
    )


@router.post("/enhance-prompt", response_model=PromptEnhancementResponse)
async def enhance_prompt_with_memory(request: PromptEnhancementRequest):
    enhanced, memory_used = memory_service.enhance_prompt(
        request.role_id,
        request.base_prompt,
        request.max_memory_items
    )
    logger.debug(f"Enhanced prompt for role={request.role_id}: {len(memory_used)} memory items used")
    return PromptEnhancementResponse(
        enhanced_prompt=enhanced,
        memory_used=memory_used
    )


# ─── Parameterized routes ───

@router.get("/{role_id}", response_model=List[MemoryEntry])
async def get_role_memories(role_id: str):
    return memory_service.get_sorted_entries(role_id)


@router.post("/{role_id}", response_model=MemoryEntry)
async def add_memory(role_id: str, content: str, memory_type: MemoryType = MemoryType.CONVERSATION):
    entry = memory_service.add_entry(role_id, content, memory_type)
    logger.debug(f"Added memory for role={role_id}: id={entry.id}, type={memory_type}")
    return entry


@router.put("/{role_id}/{memory_id}", response_model=MemoryEntry)
async def update_memory(role_id: str, memory_id: str, content: str):
    entry = memory_service.update_entry(role_id, memory_id, content)
    if not entry:
        raise HTTPException(status_code=404, detail="Memory entry not found")
    return entry


@router.delete("/{role_id}/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(role_id: str, memory_id: str):
    success = memory_service.delete_entry(role_id, memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory entry not found")
    logger.info(f"Deleted memory: id={memory_id} from role={role_id}")


@router.post("/{role_id}/access/{memory_id}", response_model=MemoryEntry)
async def access_memory(role_id: str, memory_id: str):
    entry = memory_service.access_entry(role_id, memory_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Memory entry not found")
    return entry


@router.get("/{role_id}/stats", response_model=MemoryStats)
async def get_memory_stats(role_id: str):
    return memory_service.get_stats(role_id)


@router.post("/{role_id}/callback/compress")
async def handle_compression_callback(request: CompressionCallbackRequest):
    compressed_entry = memory_service.add_entry(
        request.role_id,
        request.compressed_content,
        MemoryType.COMPRESSED,
        parent_id=request.original_memory_ids[0] if request.original_memory_ids else None
    )
    return {
        "compressed_entry": compressed_entry,
        "original_count": len(request.original_memory_ids)
    }


@router.post("/{role_id}/sync")
async def sync_memory_to_openclaw(role_id: str, role_name: str = None):
    return memory_service.sync_to_openclaw(role_id, role_name)
