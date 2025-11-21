"""
WebSocket routes for interactive pipeline real-time communication.

Handles bi-directional communication between frontend and backend:
- User sends conversational feedback
- Backend processes via ConversationHandler
- Backend sends LLM responses and stage updates
- Heartbeat/ping-pong for connection health
"""

import asyncio
import copy
import json
import logging
from datetime import datetime
from typing import Dict, Set, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from app.schemas.interactive import (
    WSErrorMessage,
    WSFeedbackMessage,
    WSHeartbeatMessage,
    WSResponseMessage,
    WSStageCompleteMessage,
)
from app.services.pipeline.conversation_handler import get_conversation_handler
from app.services.pipeline.interactive_pipeline import get_orchestrator

logger = logging.getLogger(__name__)

router = APIRouter()

AUTO_REGENERATE_STAGES = {"story", "reference_image", "storyboard"}
ACK_MESSAGES = {
    "yes",
    "y",
    "ok",
    "okay",
    "looks good",
    "looks good!",
    "approved",
    "approve",
    "good",
    "great",
    "love it",
    "sounds good",
    "sure",
    "all good",
}


# ============================================================================
# WebSocket Connection Manager
# ============================================================================

class ConnectionManager:
    """
    Manages WebSocket connections for interactive pipeline sessions.

    Responsibilities:
    - Track active connections per session
    - Send messages to specific sessions
    - Handle connection lifecycle (connect, disconnect, cleanup)
    - Implement heartbeat for connection health
    """

    def __init__(self, heartbeat_interval: int = 30):
        """
        Initialize connection manager.

        Args:
            heartbeat_interval: Heartbeat interval in seconds
        """
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}
        logger.info(f"ConnectionManager initialized (heartbeat: {heartbeat_interval}s)")

    async def connect(self, websocket: WebSocket, session_id: str):
        """
        Accept new WebSocket connection.

        Args:
            websocket: WebSocket connection
            session_id: Pipeline session ID
        """
        await websocket.accept()

        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()

        self.active_connections[session_id].add(websocket)

        logger.info(f"✅ WebSocket connected: session={session_id}, total={len(self.active_connections[session_id])}")

        # Start heartbeat for this connection
        heartbeat_task = asyncio.create_task(self._heartbeat_loop(websocket, session_id))
        self.heartbeat_tasks[id(websocket)] = heartbeat_task

    def disconnect(self, websocket: WebSocket, session_id: str):
        """
        Remove WebSocket connection.

        Args:
            websocket: WebSocket connection
            session_id: Pipeline session ID
        """
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)

            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

        # Cancel heartbeat task
        task_id = id(websocket)
        if task_id in self.heartbeat_tasks:
            self.heartbeat_tasks[task_id].cancel()
            del self.heartbeat_tasks[task_id]

        logger.info(f"❌ WebSocket disconnected: session={session_id}")

    async def send_message(self, session_id: str, message: dict):
        """
        Send message to all connections for a session.

        Args:
            session_id: Pipeline session ID
            message: Message dict to send
        """
        if session_id not in self.active_connections:
            logger.warning(f"No active connections for session {session_id}")
            return

        message_json = json.dumps(message, default=str)
        dead_connections = set()

        for websocket in self.active_connections[session_id]:
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                dead_connections.add(websocket)

        # Cleanup dead connections
        for websocket in dead_connections:
            self.disconnect(websocket, session_id)

    async def broadcast(self, message: dict):
        """Broadcast message to all active connections."""
        for session_id in list(self.active_connections.keys()):
            await self.send_message(session_id, message)

    async def _heartbeat_loop(self, websocket: WebSocket, session_id: str):
        """
        Send periodic heartbeats to maintain connection.

        Args:
            websocket: WebSocket connection
            session_id: Session ID
        """
        try:
            while True:
                await asyncio.sleep(self.heartbeat_interval)

                heartbeat = WSHeartbeatMessage()
                # Use mode='json' to ensure datetime is serialized to ISO string
                await websocket.send_json(heartbeat.model_dump(mode='json'))

        except asyncio.CancelledError:
            pass  # Task cancelled on disconnect
        except Exception as e:
            logger.error(f"Heartbeat failed for session {session_id}: {e}")
            self.disconnect(websocket, session_id)


# Global connection manager
manager = ConnectionManager()


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@router.websocket("/ws/pipeline/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time pipeline communication.

    URL: /ws/pipeline/{session_id}

    Message Types (Client → Server):
    - feedback: User sends conversational feedback
    - ping: Connection health check

    Message Types (Server → Client):
    - llm_response: LLM's conversational response
    - stage_complete: Stage generation complete with data
    - error: Error occurred
    - heartbeat: Connection health ping

    Args:
        websocket: WebSocket connection
        session_id: Pipeline session ID
    """
    # Verify session exists
    orchestrator = get_orchestrator()
    session = await orchestrator.get_session(session_id)

    if not session:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Session not found")
        logger.warning(f"WebSocket rejected: session {session_id} not found")
        return

    # Connect
    await manager.connect(websocket, session_id)

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "current_stage": session.status,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Message loop
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type")
            logger.info(f"📨 WebSocket message received: type={message_type}, session={session_id}")

            if message_type == "feedback":
                await handle_feedback_message(websocket, session_id, message)

            elif message_type == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})

            else:
                logger.warning(f"Unknown message type: {message_type}")
                await websocket.send_json({
                    "type": "error",
                    "error_code": "UNKNOWN_MESSAGE_TYPE",
                    "message": f"Unknown message type: {message_type}",
                    "timestamp": datetime.utcnow().isoformat()
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected normally: session={session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await send_error(websocket, "WEBSOCKET_ERROR", str(e), session_id=session_id)
    finally:
        manager.disconnect(websocket, session_id)


# ============================================================================
# Message Handlers
# ============================================================================

async def handle_feedback_message(websocket: WebSocket, session_id: str, message: dict):
    """
    Handle user feedback message.

    Args:
        websocket: WebSocket connection
        session_id: Session ID
        message: Feedback message
    """
    try:
        # Parse message
        feedback_msg = WSFeedbackMessage(**message)

        # Get session and current output
        orchestrator = get_orchestrator()
        session = await orchestrator.get_session(session_id)

        if not session:
            await send_error(websocket, "SESSION_NOT_FOUND", "Session not found", session_id=session_id)
            return

        conv_history = session.conversation_history
        logger.info(
            "conversation_history snapshot: session=%s type=%s len=%s value=%r",
            session_id,
            type(conv_history).__name__,
            len(conv_history) if hasattr(conv_history, "__len__") else "n/a",
            conv_history,
        )

        # Add user message to conversation
        await orchestrator.add_message(session_id, feedback_msg.message, "user")

        # Process feedback via ConversationHandler
        handler = get_conversation_handler()

        current_output = session.outputs.get(session.status, {})

        if session.status == "story":
            result = await handler.process_story_feedback(
                story=current_output,
                feedback=feedback_msg.message,
                conversation_history=session.conversation_history
            )
        elif session.status == "reference_image":
            result = await handler.process_image_feedback(
                image_data=current_output,
                feedback=feedback_msg.message,
                conversation_history=session.conversation_history
            )
        elif session.status == "storyboard":
            result = await handler.process_storyboard_feedback(
                storyboard_data=current_output,
                feedback=feedback_msg.message,
                conversation_history=session.conversation_history
            )
        else:
            await send_error(
                websocket,
                "INVALID_STAGE",
                f"Cannot process feedback for stage: {session.status}",
                session_id=session_id,
            )
            return

        modifications = copy.deepcopy(result.get("modifications") or {})
        feedback_text = feedback_msg.message.strip()
        if feedback_text:
            modifications.setdefault("feedback_text", feedback_text)

        # Send LLM response to all active connections for this session
        response_msg = WSResponseMessage(
            message=result["response"],
            intent=result.get("modifications")
        )
        await manager.send_message(session_id, response_msg.model_dump(mode='json'))

        # Add assistant response to conversation
        await orchestrator.add_message(session_id, result["response"], "assistant")

        # Persist feedback metadata for this stage
        try:
            stage_feedback_key = f"{session.status}_last_feedback"
            session.stage_data[stage_feedback_key] = {
                "message": feedback_msg.message,
                "modifications": modifications,
                "timestamp": datetime.utcnow().isoformat(),
            }
            await orchestrator._save_session(session)
        except Exception as save_err:
            logger.warning(f"Failed to persist feedback metadata: {save_err}")

        # Auto-regenerate stage when meaningful feedback is provided
        if _should_auto_regenerate(feedback_msg.message, session.status):
            async def trigger_regen():
                try:
                    await orchestrator.regenerate_stage(
                        session_id,
                        session.status,
                        feedback=feedback_msg.message,
                        modifications=copy.deepcopy(modifications) if modifications else {"feedback_text": feedback_msg.message},
                    )
                except Exception as regen_err:
                    logger.error(f"Auto-regeneration failed for session {session_id}: {regen_err}")

            asyncio.create_task(trigger_regen())

        logger.info(f"✅ Feedback processed for session {session_id}")

    except Exception as e:
        logger.error(f"Failed to handle feedback: {e}")
        await send_error(websocket, "FEEDBACK_PROCESSING_FAILED", str(e), session_id=session_id)


async def send_error(
    websocket: WebSocket,
    error_code: str,
    message: str,
    recoverable: bool = True,
    session_id: Optional[str] = None,
):
    """
    Send error message via WebSocket.

    Args:
        websocket: WebSocket connection
        error_code: Error code
        message: Error message
        recoverable: Whether error is recoverable
    """
    error_msg = WSErrorMessage(
        error_code=error_code,
        message=message,
        recoverable=recoverable
    )
    try:
        await websocket.send_json(error_msg.model_dump(mode='json'))
    except Exception as e:
        logger.warning(
            f"Failed to send error message on direct socket: {e}. Session_id={session_id}"
        )
        if session_id:
            try:
                await manager.send_message(session_id, error_msg.model_dump(mode='json'))
            except Exception as broadcast_error:
                logger.error(f"Failed to broadcast error message: {broadcast_error}")


def _should_auto_regenerate(message: str, stage: str) -> bool:
    if stage not in AUTO_REGENERATE_STAGES:
        return False
    cleaned = message.strip().lower()
    if not cleaned:
        return False
    return cleaned not in ACK_MESSAGES


# ============================================================================
# Notification Helpers (called by orchestrator)
# ============================================================================

async def notify_stage_complete(session_id: str, stage: str, data: dict):
    """
    Notify frontend that a stage has completed.

    Args:
        session_id: Session ID
        stage: Completed stage name
        data: Stage output data
    """
    message = WSStageCompleteMessage(
        stage=stage,
        data=data
    )
    await manager.send_message(session_id, message.model_dump(mode='json'))
    logger.info(f"📢 Stage complete notification sent: session={session_id}, stage={stage}")


async def notify_error(session_id: str, error_code: str, message: str):
    """
    Notify frontend of an error.

    Args:
        session_id: Session ID
        error_code: Error code
        message: Error message
    """
    error_msg = WSErrorMessage(
        error_code=error_code,
        message=message,
        recoverable=True
    )
    await manager.send_message(session_id, error_msg.model_dump(mode='json'))
    logger.info(f"📢 Error notification sent: session={session_id}, code={error_code}")
