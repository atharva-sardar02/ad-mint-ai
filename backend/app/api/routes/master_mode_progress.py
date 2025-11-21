"""
Server-Sent Events (SSE) for Master Mode real-time progress updates.
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import AsyncGenerator, Optional
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.api.deps import get_current_user
from app.db.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/master-mode", tags=["master-mode"])

# Store progress updates in memory (keyed by generation_id)
progress_queues = {}


def create_progress_queue(generation_id: str) -> asyncio.Queue:
    """Create (or return existing) progress queue for a generation."""
    queue = progress_queues.get(generation_id)
    if queue is None:
        queue = asyncio.Queue()
        progress_queues[generation_id] = queue
    return queue


def get_progress_queue(generation_id: str) -> Optional[asyncio.Queue]:
    """Get existing progress queue."""
    return progress_queues.get(generation_id)


async def send_progress_update(
    generation_id: str,
    step: str,
    status: str,
    progress: int,
    message: str,
    data: Optional[dict] = None
):
    """Send a progress update to the SSE stream."""
    queue = get_progress_queue(generation_id)
    if queue:
        update = {
            "step": step,
            "status": status,
            "progress": progress,
            "message": message,
            "data": data or {}
        }
        await queue.put(update)
        logger.info(f"[Progress] {generation_id}: {step} - {message} ({progress}%)")


async def send_llm_interaction(
    generation_id: str,
    agent: str,
    interaction_type: str,
    content: str,
    metadata: Optional[dict] = None
):
    """Send an LLM interaction (prompt sent or response received) to the SSE stream."""
    queue = get_progress_queue(generation_id)
    if queue:
        update = {
            "type": "llm_interaction",
            "agent": agent,
            "interaction_type": interaction_type,  # "prompt" or "response"
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        await queue.put(update)
        logger.info(f"[LLM] {generation_id}: {agent} - {interaction_type}")


async def close_progress_queue(generation_id: str):
    """Close and cleanup progress queue."""
    queue = get_progress_queue(generation_id)
    if queue:
        await queue.put(None)  # Signal end of stream
        del progress_queues[generation_id]


async def progress_generator(generation_id: str) -> AsyncGenerator[str, None]:
    """Generate SSE events for progress updates."""
    queue = get_progress_queue(generation_id)
    if not queue:
        logger.info(f"[Progress] Queue not found for {generation_id}, creating placeholder")
        queue = create_progress_queue(generation_id)
    
    try:
        while True:
            update = await queue.get()
            
            if update is None:  # End of stream signal
                break
            
            # Format as SSE
            yield f"data: {json.dumps(update)}\n\n"
            
    except asyncio.CancelledError:
        logger.info(f"[Progress] Stream cancelled for {generation_id}")
    finally:
        logger.info(f"[Progress] Stream closed for {generation_id}")


@router.get("/progress/{generation_id}")
async def stream_progress(
    generation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Stream real-time progress updates via SSE."""
    logger.info(f"[Progress] Starting stream for {generation_id}")
    
    return StreamingResponse(
        progress_generator(generation_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

