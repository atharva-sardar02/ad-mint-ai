# User Story 1.2: Interactive Story Generation

**Epic:** Interactive Video Generation Pipeline
**Story ID:** interactive-pipeline-2
**Status:** Draft
**Points:** 3
**Priority:** High

---

## User Story

**As a** content creator using the web application
**I want** to review the AI-generated story and refine it through conversational feedback before proceeding to image generation
**So that** I can ensure the narrative matches my creative vision and avoid wasting API credits on images/videos based on a story I don't like

---

## Acceptance Criteria

**AC #1: Interactive Pipeline Initiated**
- GIVEN a user on the video generation page
- WHEN they select "Interactive Mode" and submit a prompt
- THEN the backend starts an interactive pipeline session
- AND creates a session ID with initial state
- AND the frontend displays a loading state "Generating your story..."

**AC #2: Story Displayed for Review**
- GIVEN the story has been generated (Stage 1 complete)
- WHEN the pipeline pauses at the story review stage
- THEN the frontend displays the full story text
- AND shows a chat interface for feedback
- AND shows "Approve" and "Regenerate" buttons
- AND WebSocket connection is established

**AC #3: Conversational Feedback Processed**
- GIVEN the user is reviewing the story
- WHEN they type a message like "make it more humorous and focus on product benefits"
- THEN the message is sent via WebSocket to the backend
- AND the LLM processes the feedback
- AND returns a conversational response explaining the planned changes
- AND the response appears in the chat interface

**AC #4: Story Regeneration**
- GIVEN the user has provided feedback
- WHEN they click "Regenerate" or type "regenerate the story"
- THEN the backend regenerates the story incorporating the feedback
- AND shows a loading indicator "Regenerating story..."
- AND the new story replaces the old one in the UI
- AND the conversation history is preserved

**AC #5: Story Approval and Stage Transition**
- GIVEN the user is satisfied with the story
- WHEN they click "Approve"
- THEN the session state is updated to "approved_story"
- AND the pipeline proceeds to Stage 2 (reference image generation)
- AND the frontend shows "Story approved! Generating reference images..."
- AND the story review UI transitions to the next stage UI

**AC #6: WebSocket Reconnection**
- GIVEN an active WebSocket connection
- WHEN the connection drops (network issue, server restart)
- THEN the frontend automatically attempts to reconnect
- AND shows "Reconnecting..." indicator
- WHEN reconnected
- THEN chat functionality resumes
- AND session state is restored

**AC #7: Session State Persistence**
- GIVEN a user has an active interactive pipeline session
- WHEN they refresh the browser or close/reopen the tab
- THEN the frontend restores the session using the session ID
- AND displays the current stage (story review)
- AND shows the current story and conversation history
- AND the user can continue where they left off

---

## Tasks/Subtasks

**Backend: Interactive Pipeline Orchestrator (AC: #1, #5)**
- [ ] Create `app/services/pipeline/interactive_pipeline.py` module
- [ ] Implement `InteractivePipelineOrchestrator` class
- [ ] Add `start_pipeline(user_id, prompt, target_duration)` method
- [ ] Add `run_stage_with_pause(stage_name, generation_fn, session_id)` method
- [ ] Implement session state save/load using Redis or PostgreSQL
- [ ] Add stage transition logic (story → reference_image → storyboard → video)

**Backend: WebSocket Communication (AC: #2, #3, #6)**
- [ ] Create `app/api/routes/websocket.py` module
- [ ] Implement WebSocket endpoint `/ws/pipeline/{session_id}`
- [ ] Add connection manager for multiple WebSocket connections
- [ ] Implement message routing (user message → conversation handler → response)
- [ ] Add heartbeat/ping-pong for connection health monitoring
- [ ] Implement auto-disconnect on timeout (5 min idle)

**Backend: Conversation Handler (AC: #3, #4)**
- [ ] Create `app/services/pipeline/conversation_handler.py` module
- [ ] Implement `ConversationHandler` class
- [ ] Add `process_story_feedback(story, feedback, history)` method
- [ ] Integrate with OpenAI GPT-4 for intent extraction
- [ ] Add `refine_story(original_story, modifications)` method
- [ ] Use existing `story_generator.py` for regeneration with updated parameters

**Backend: API Routes (AC: #1, #4, #5)**
- [ ] Create `app/api/routes/interactive_generation.py` module
- [ ] Implement `POST /api/v1/interactive/start` - Start pipeline
- [ ] Implement `GET /api/v1/interactive/{session_id}/status` - Get session status
- [ ] Implement `POST /api/v1/interactive/{session_id}/approve` - Approve current stage
- [ ] Implement `POST /api/v1/interactive/{session_id}/regenerate` - Regenerate with feedback

**Backend: Schemas (AC: #1, #3, #4)**
- [ ] Create `app/schemas/interactive_schemas.py` module
- [ ] Define `PipelineStartRequest` schema (prompt, target_duration, mode)
- [ ] Define `PipelineSessionResponse` schema (session_id, status, current_stage)
- [ ] Define `ChatMessage` schema (type, content, timestamp)
- [ ] Define `RegenerateRequest` schema (feedback, stage)

**Frontend: Pipeline Store (AC: #1, #5, #7)**
- [ ] Create `src/stores/pipelineStore.ts` (Zustand store)
- [ ] Add state: `sessionId`, `currentStage`, `stageData`, `conversationHistory`
- [ ] Add actions: `startPipeline()`, `updateStage()`, `sendFeedback()`, `approveStage()`
- [ ] Implement session restoration from localStorage/sessionStorage

**Frontend: WebSocket Service (AC: #2, #3, #6)**
- [ ] Create `src/services/websocket-service.ts` module
- [ ] Implement WebSocket connection management
- [ ] Add message handling (send/receive)
- [ ] Implement auto-reconnect with exponential backoff
- [ ] Add connection status tracking (connected, disconnected, reconnecting)

**Frontend: WebSocket Hook (AC: #3, #6)**
- [ ] Create `src/hooks/useWebSocket.ts` hook
- [ ] Return `{ connected, sendMessage, messages, connectionStatus }`
- [ ] Handle WebSocket lifecycle (connect, disconnect, cleanup)
- [ ] Integrate with websocket-service

**Frontend: Chat Interface Component (AC: #2, #3)**
- [ ] Create `src/components/generation/ChatInterface.tsx` component
- [ ] Display message list (user messages on right, LLM on left)
- [ ] Implement message input with send button
- [ ] Add loading indicator for LLM response
- [ ] Auto-scroll to latest message
- [ ] Show timestamp for each message

**Frontend: Story Review Component (AC: #2, #4, #5)**
- [ ] Create `src/components/generation/StoryReview.tsx` component
- [ ] Display generated story (narrative + script if applicable)
- [ ] Integrate ChatInterface for feedback
- [ ] Add "Approve" button (green, prominent)
- [ ] Add "Regenerate" button (secondary)
- [ ] Show loading state during regeneration
- [ ] Display conversation history

**Frontend: Interactive Pipeline Component (AC: #1, #5, #7)**
- [ ] Create `src/components/generation/InteractivePipeline.tsx` component
- [ ] Add stage progress indicator (Story → Images → Storyboard → Video)
- [ ] Render StoryReview when currentStage === 'story'
- [ ] Handle stage transitions (update UI when stage changes)
- [ ] Implement session restoration on mount
- [ ] Show loading states between stages

**Frontend: API Client (AC: #1, #4, #5)**
- [ ] Create `src/services/interactive-api.ts` module
- [ ] Implement `startPipeline(prompt, duration)` API call
- [ ] Implement `getSessionStatus(sessionId)` API call
- [ ] Implement `approveStage(sessionId, stage)` API call
- [ ] Implement `regenerate(sessionId, stage, feedback)` API call

**Testing: Backend (AC: #1-7)**
- [ ] Create `tests/services/test_interactive_pipeline.py`
- [ ] Test session creation and initialization
- [ ] Test stage transitions and state management
- [ ] Test session save/load from Redis
- [ ] Create `tests/services/test_conversation_handler.py`
- [ ] Test feedback processing and story refinement
- [ ] Mock OpenAI API calls
- [ ] Create `tests/api/test_websocket.py`
- [ ] Test WebSocket connection and message handling
- [ ] Test reconnection behavior

**Testing: Frontend (AC: #2-7)**
- [ ] Create `src/components/generation/__tests__/StoryReview.test.tsx`
- [ ] Test story display and approve/regenerate buttons
- [ ] Test chat message sending
- [ ] Create `src/components/generation/__tests__/ChatInterface.test.tsx`
- [ ] Test message rendering and input
- [ ] Create `src/components/generation/__tests__/InteractivePipeline.test.tsx`
- [ ] Test stage rendering and transitions
- [ ] Mock WebSocket and API calls

**Integration Testing (AC: #1-7)**
- [ ] Test full flow: start → story generated → feedback → regenerate → approve
- [ ] Test WebSocket reconnection during active session
- [ ] Test session restoration after page refresh
- [ ] Test error handling (API failures, WebSocket disconnect)

---

## Technical Summary

This story implements the core infrastructure for interactive pipeline: WebSocket communication, session state management, and conversational feedback for the story generation stage. It sets the foundation for Stories 3 and 4 to extend the interactive pattern to images and storyboard.

**Architecture:**

**Backend:**
- **InteractivePipelineOrchestrator:** Manages pipeline flow with pause points
  - Extends existing `multi_stage_orchestrator.py` pattern
  - Adds pause/resume functionality at each stage
  - Uses Redis for session state (fast in-memory storage)

- **WebSocket Layer:** Real-time bi-directional communication
  - FastAPI WebSocket endpoint
  - Connection manager for multiple users
  - Heartbeat for connection health

- **ConversationHandler:** Processes user feedback
  - Uses GPT-4 to understand conversational feedback
  - Extracts modifications (tone, focus, structure)
  - Calls `story_generator.py` with updated parameters

**Frontend:**
- **InteractivePipeline:** Main component orchestrating the flow
- **StoryReview:** Story-specific UI with approve/regenerate
- **ChatInterface:** Reusable chat component (used in Stories 3-4 too)
- **pipelineStore:** Zustand state management for pipeline
- **WebSocket hook:** Manages WebSocket connection lifecycle

**Data Flow:**
```
User submits prompt
  ↓
POST /api/v1/interactive/start (create session)
  ↓
Backend generates story (existing story_generator.py)
  ↓
Backend saves to session, sends WS notification
  ↓
Frontend displays story + chat in StoryReview
  ↓
User sends feedback via chat
  ↓
WS → ConversationHandler → GPT-4 processes
  ↓
LLM response via WS
  ↓
User clicks "Regenerate"
  ↓
Backend regenerates story with modifications
  ↓
Frontend updates story display
  ↓
User clicks "Approve"
  ↓
POST /api/v1/interactive/{id}/approve
  ↓
Backend transitions to next stage (reference_image)
  ↓
Frontend shows loading for images
```

---

## Project Structure Notes

**files_to_modify:**
```
# Backend
backend/app/services/pipeline/interactive_pipeline.py        # CREATE
backend/app/services/pipeline/conversation_handler.py        # CREATE
backend/app/api/routes/interactive_generation.py            # CREATE
backend/app/api/routes/websocket.py                         # CREATE
backend/app/schemas/interactive_schemas.py                  # CREATE

# Frontend
frontend/src/components/generation/InteractivePipeline.tsx  # CREATE
frontend/src/components/generation/StoryReview.tsx          # CREATE
frontend/src/components/generation/ChatInterface.tsx        # CREATE
frontend/src/hooks/useWebSocket.ts                          # CREATE
frontend/src/services/websocket-service.ts                  # CREATE
frontend/src/services/interactive-api.ts                    # CREATE
frontend/src/stores/pipelineStore.ts                        # CREATE
frontend/src/types/pipeline.ts                              # CREATE
```

**test_locations:**
```
# Backend
backend/tests/services/test_interactive_pipeline.py         # CREATE
backend/tests/services/test_conversation_handler.py         # CREATE
backend/tests/api/test_interactive_generation.py            # CREATE

# Frontend
frontend/src/components/generation/__tests__/InteractivePipeline.test.tsx   # CREATE
frontend/src/components/generation/__tests__/StoryReview.test.tsx           # CREATE
frontend/src/components/generation/__tests__/ChatInterface.test.tsx         # CREATE
```

**story_points:** 3

**dependencies:**
- Story 1 (CLI tools organization) - recommended to complete first for clean codebase
- Redis instance for session state (can use PostgreSQL as fallback)
- Existing `story_generator.py` service
- Existing `multi_stage_orchestrator.py` pattern

**estimated_effort:** 2-3 days

---

## Key Code References

**Existing Code to Reference:**

1. **`backend/app/services/pipeline/multi_stage_orchestrator.py`** (Lines 1-150)
   - Current 4-stage pipeline orchestration
   - Pattern for stage execution: `await select_template()` → `await generate_story()` → etc.
   - Use this as template for interactive orchestrator

2. **`backend/app/services/pipeline/story_generator.py`** (Full file)
   - Story generation logic with template-based approach
   - LLM prompt patterns for narrative creation
   - Reuse for regeneration with updated parameters

3. **`backend/app/services/pipeline/image_prompt_enhancement.py`** (Lines 1-300)
   - Two-agent feedback loop pattern (Cinematographer + Prompt Engineer)
   - Iterative refinement with scoring
   - Adapt this pattern for conversational feedback

4. **`backend/app/api/routes/videos.py`** (If exists)
   - Current video generation API patterns
   - Authentication and authorization patterns
   - Response schema patterns

**New Patterns to Establish:**

1. **Session State Schema:**
```python
class PipelineSession(BaseModel):
    session_id: str
    user_id: str
    status: Literal["story", "reference_image", "storyboard", "video", "complete"]
    current_stage: str
    outputs: Dict[str, Any]  # {stage_name: output_data}
    conversation_history: List[Dict]
    created_at: datetime
    updated_at: datetime
```

2. **WebSocket Message Protocol:**
```typescript
// Client → Server
{type: "feedback", stage: "story", message: string}

// Server → Client
{type: "llm_response", message: string}
{type: "stage_complete", stage: string, data: any}
```

---

## Context References

**Primary Reference:**
- Technical Specification: `docs/tech-spec.md`
  - See "Technical Approach" → sections 1-3 for detailed implementation
  - See "Implementation Guide" → "Story 2: Interactive Story Generation"

**Related Documentation:**
- PRD: `docs/PRD.md` (Section 8.7: Hero-Frame & Iterative Refinement Workflow)
- Architecture: `docs/architecture.md`
- Epic 8 Tech Spec: `docs/sprint-artifacts/tech-spec-epic-8.md` (feedback loop patterns)

---

## Dev Agent Record

**Agent Model Used:**
- TBD

**Debug Log References:**
- TBD

**Completion Notes:**
- TBD

**Files Modified:**
- TBD

**Test Results:**
- TBD

---

## Review Notes

**Code Review:**
- TBD

**QA Notes:**
- TBD

**Deployment Notes:**
- TBD
