# System Patterns

1. **Interactive Pipeline Orchestrator** (`backend/app/services/pipeline/interactive_pipeline.py`)
   - Owns session lifecycle, stage transitions, and persistence hooks.
   - Emits WebSocket notifications when stages complete; expects storage backend for resilience.

2. **Session Storage Strategy** (`session_storage.py`)
   - Prefers Redis, falls back to Postgres, otherwise uses an in-memory dict.
   - Current local dev defaults to in-memory because `DATABASE_URL` is SQLite and `REDIS_URL` is unset.

3. **Conversation Handler** (`conversation_handler.py`)
   - Uses OpenAI Async client to interpret feedback and extract structured modifications.
   - Relies on a well-formed `conversation_history` list when building prompts.

4. **WebSocket Endpoint** (`api/routes/websocket.py`)
   - Thin wrapper that validates sessions, relays messages to the handler, and streams results back.
   - Heartbeat loop keeps idle connections alive; reconnect logic lives on the frontend service layer.

5. **Frontend Store + WebSocket Service** (`frontend/src/stores/pipelineStore.ts`, `src/services/websocket-service.ts`)
   - Zustand store mirrors session state, last message, stage outputs, connection state, and chat history.
   - WebSocket hook wires events into the store, throttles reconnections, and pings for health.

### Notable Constraints
- Python backend is async; long-running generation tasks await internal helpers but may need background workers in production.
- OpenAI API key must be present; without it, story generation fails early.
- Heartbeat interval defaults to 30s (backend) / 25s (frontend ping) to guard stale connections.
