"""
Server-Sent Events (SSE) for Master Mode real-time progress updates.
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import AsyncGenerator, Optional, List, Dict, Any
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/master-mode", tags=["master-mode"])

# Store progress updates in memory (keyed by generation_id)
progress_queues = {}

# Store conversation history in memory (keyed by generation_id)
conversation_histories = {}


def create_progress_queue(generation_id: str) -> asyncio.Queue:
    """Create (or return existing) progress queue for a generation."""
    queue = progress_queues.get(generation_id)
    if queue is None:
        queue = asyncio.Queue()
        progress_queues[generation_id] = queue
        # Also initialize conversation history storage
        conversation_histories[generation_id] = []
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
        interaction = {
            "type": "llm_interaction",
            "agent": agent,
            "interaction_type": interaction_type,  # "prompt" or "response"
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        await queue.put(interaction)
        
        # Also store in conversation history for later retrieval
        if generation_id in conversation_histories:
            conversation_histories[generation_id].append(interaction)
        
        logger.info(f"[LLM] {generation_id}: {agent} - {interaction_type}")


async def close_progress_queue(generation_id: str):
    """Close and cleanup progress queue."""
    queue = get_progress_queue(generation_id)
    if queue:
        await queue.put(None)  # Signal end of stream
        del progress_queues[generation_id]
        # Note: Keep conversation_histories[generation_id] until saved to DB


def get_conversation_history(generation_id: str) -> List[Dict[str, Any]]:
    """Get the stored conversation history for a generation."""
    return conversation_histories.get(generation_id, [])


def clear_conversation_history(generation_id: str):
    """Clear the stored conversation history after it's been saved to DB."""
    if generation_id in conversation_histories:
        del conversation_histories[generation_id]
        logger.info(f"[Progress] Cleared conversation history for {generation_id}")


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
    generation_id: str
    # No authentication required - generation_id acts as capability token
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


@router.get("/conversation/{generation_id}")
async def get_conversation(generation_id: str):
    """Get the stored conversation history for a generation (for later viewing)."""
    from sqlalchemy.orm import Session
    from fastapi import Depends
    from app.db.session import get_db
    from app.db.models.generation import Generation
    
    # Get conversation from database
    db = next(get_db())
    generation = db.query(Generation).filter(Generation.id == generation_id).first()
    
    if not generation:
        return {"error": "Generation not found", "conversation": []}
    
    if not generation.llm_conversation_history:
        return {"generation_id": generation_id, "conversation": []}
    
    return {
        "generation_id": generation_id,
        "conversation": generation.llm_conversation_history,
        "num_entries": len(generation.llm_conversation_history) if generation.llm_conversation_history else 0
    }

