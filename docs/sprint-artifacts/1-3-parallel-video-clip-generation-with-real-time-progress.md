# Story 1.3: Parallel Video Clip Generation with Real-Time Progress

Status: ready-for-dev

## Story

As a backend developer,
I want all scene video clips to generate in parallel using asyncio with per-clip progress updates via WebSocket,
so that total video generation time = longest clip (~1 min), not sum of all clips (~5 min), achieving 5x speed improvement.

## Acceptance Criteria

1. **Parallel Execution** - All scene video clips generate **simultaneously in parallel** using asyncio.gather() - NOT sequentially

2. **Semaphore Rate Limiting** - Implementation uses asyncio.Semaphore(5) to limit concurrent Replicate API calls (max 5-10 simultaneous requests)

3. **Consistency Context Injection** - Each video generation prompt includes reference image consistency context:
   ```python
   full_prompt = f"{consistency_context}\n\nSCENE: {scene.description}"
   ```

4. **WebSocket Progress Updates** - Each video generation task sends real-time progress:
   - Message type: `video_progress`
   - Payload: `{clip_id: 1, progress: 45, status: "rendering"}`
   - Polling frequency: Every 2 seconds from Replicate API
   - Status values: "queued", "processing", "rendering", "complete", "failed"

5. **Clip Completion Notifications** - As each clip completes, send `video_complete` WebSocket message:
   - Payload: `{clip_id: 1, url: "s3://bucket/clip1.mp4", duration: 6.2}`
   - Immediate S3 upload after generation
   - Store in Generation.video_clips JSONB array

6. **Frontend ParallelProgress Component** - UI displays `ParallelProgress.tsx` showing all clips simultaneously with individual progress bars updating in real-time

7. **Error Handling** - Partial failure support:
   - If one clip fails, continue generating others
   - Store error in database with clip_index
   - Allow user to retry failed clip individually
   - Log failure with full context

8. **Performance Target Met** - Total video generation time < 90 seconds for 5 clips (target: ~60 seconds = longest single clip time, NOT sum of all clips = ~300 seconds)

## Tasks / Subtasks

- [ ] Implement video stage module (AC: #1, #2, #3)
  - [ ] Create `backend/app/services/unified_pipeline/video_stage.py` with main `execute()` method
  - [ ] Implement asyncio.gather() for parallel Replicate API calls to all scenes
  - [ ] Add asyncio.Semaphore(5) rate limiting for concurrent requests
  - [ ] Inject consistency_context into each scene video prompt
  - [ ] Write unit tests for parallel generation logic

- [ ] Implement Replicate API integration (AC: #4)
  - [ ] Create async Replicate video generation method using Veo 3 model
  - [ ] Add polling loop (every 2 seconds) for Replicate prediction status
  - [ ] Extract progress percentage from Replicate API response
  - [ ] Map Replicate status to internal status values (queued, processing, rendering, complete, failed)
  - [ ] Write unit tests mocking Replicate API responses

- [ ] Implement WebSocket progress streaming (AC: #4, #5)
  - [ ] Send `video_progress` messages during polling loop for each clip
  - [ ] Send `video_complete` message when clip generation finishes
  - [ ] Use existing WebSocketManager from orchestrator
  - [ ] Write integration tests for WebSocket message delivery

- [ ] Implement S3 upload and database storage (AC: #5)
  - [ ] Download completed video from Replicate output URL
  - [ ] Upload to S3 using existing S3Storage service
  - [ ] Store video clip metadata in Generation.video_clips JSONB array
  - [ ] Write unit tests for S3 upload error handling

- [ ] Implement error handling (AC: #7)
  - [ ] Catch exceptions in asyncio tasks, continue other tasks
  - [ ] Store per-clip error messages in video_clips array
  - [ ] Log errors with full context (scene description, Replicate response)
  - [ ] Add retry method for individual failed clips
  - [ ] Write unit tests for partial failure scenarios

- [ ] Create frontend ParallelProgress component (AC: #6)
  - [ ] Implement `frontend/src/components/pipeline/ParallelProgress.tsx`
  - [ ] Display progress bar for each clip with percentage
  - [ ] Update progress bars on WebSocket messages
  - [ ] Show green checkmark on clip completion
  - [ ] Write component tests with @testing-library/react

- [ ] Integration with orchestrator (AC: #1, #8)
  - [ ] Add video stage execution in orchestrator after scene approval
  - [ ] Pass scenes and consistency_context to video stage
  - [ ] Measure total generation time (first API call → last clip complete)
  - [ ] Verify performance target: <90 seconds for 5 clips
  - [ ] Write integration tests for orchestrator → video stage flow

- [ ] Testing and validation (AC: All)
  - [ ] Test with 5 scenes (standard case)
  - [ ] Test with 1 scene (no parallelism, still works)
  - [ ] Test partial failure (1 clip fails, 4 succeed)
  - [ ] Test Replicate API rate limiting (semaphore blocks excess concurrent calls)
  - [ ] Verify WebSocket messages sent for all clips
  - [ ] Verify S3 uploads complete before video_complete message
  - [ ] Performance test: measure total time for 5 clips in parallel

## Dev Notes

### Architecture Patterns and Constraints

**From Architecture.md:**
- **Parallel Video Clip Generation Pattern** (lines 599-635): Generate all scene video clips in parallel using asyncio concurrent execution. Total time = longest clip (~1 min), not sum (~5 min). Replicate API rate limits handled with semaphore (max 5-10 concurrent). Frontend displays per-clip progress (better UX than waiting 5 minutes).
- **Modular Pipeline Orchestration** (lines 78-86): Video stage is independent service module with clear input/output contracts, coordinated by orchestrator
- **WebSocket Real-Time Updates** (ADR-002, lines 1586-1609): FastAPI native WebSocket for bidirectional communication, auto-reconnect on frontend, per-clip progress updates

**From Tech-Spec (Epic 1):**
- Video Stage Module (line 86): Responsibilities include parallel video clip generation (asyncio concurrent), Replicate API orchestration, per-clip progress tracking, S3 upload coordination
- Data Models (lines 196-206): VideoClip Pydantic schema with scene_id, url, duration, status, progress fields
- WebSocket Messages (lines 118-128): video_progress and video_complete message types with payload structure

**From ADR-004 (Parallel Video Generation Architecture, lines 1636-1670):**
- Use asyncio.gather() for concurrent execution
- Semaphore limits concurrent Replicate calls (max 5-10)
- Real-time progress updates for each clip via WebSocket
- 5x speed improvement: 5 clips in ~1 min vs ~5 min sequential
- Error handling: partial failures (retry failed clips individually)

**Testing Requirements:**
- Unit Tests: `tests/test_services/test_unified_pipeline/test_video_stage.py` - parallel generation, semaphore limiting, error handling
- Integration Tests: `tests/test_integration/test_pipeline_execution.py` - orchestrator → video stage flow, performance timing
- Frontend Tests: `tests/components/test_ParallelProgress.test.tsx` - progress bar rendering, WebSocket updates

### Project Structure Notes

**Component Locations** (from Tech-Spec):
- **Video Stage:** `backend/app/services/unified_pipeline/video_stage.py` (NEW)
- **WebSocket Manager:** `backend/app/services/session/websocket_manager.py` (EXISTING - reuse)
- **S3 Uploader:** `backend/app/services/storage/s3_storage.py` (EXISTING - reuse)
- **Database Models:** `backend/app/db/models/generation.py` (Generation.video_clips JSONB field already exists from Story 1.1)
- **Pydantic Schemas:** `backend/app/schemas/unified_pipeline.py` (VideoClip, VideoProgressMessage, VideoCompleteMessage already defined in Story 1.1)
- **Frontend Component:** `frontend/src/components/pipeline/ParallelProgress.tsx` (NEW)

**Expected File Structure:**
```
backend/
  app/
    services/
      unified_pipeline/
        video_stage.py  # NEW - main video stage module with parallel generation
      session/
        websocket_manager.py  # EXISTING - reuse for progress updates
      storage/
        s3_storage.py  # EXISTING - reuse for video uploads
frontend/
  src/
    components/
      pipeline/
        ParallelProgress.tsx  # NEW - parallel progress bars component
```

**Database Schema** (from Story 1.1, already migrated):
```python
# Generation model already has video_clips JSONB field
video_clips JSONB  # [{scene_id, url, duration, status, progress, error_message}]
```

### Learnings from Previous Story

**From Story 1-2-master-mode-3-reference-image-consistency-system (Status: ready-for-dev)**

- **New Files Created** (expected after Story 1.2 implementation):
  - `backend/app/services/unified_pipeline/reference_stage.py` - reference stage module generating consistency_context string
  - `backend/app/services/media/image_processor.py` - Vision API integration (modified/extended)
  - Reference stage sets pattern for video stage structure (execute() method, config loading, S3 upload)

- **Consistency Context Available**:
  - Story 1.2 generates consistency_context string from reference image analysis
  - Format: "CHARACTER APPEARANCE: ... PRODUCT FEATURES: ... COLOR PALETTE: ... VISUAL STYLE: ..."
  - Video stage MUST inject this context into ALL scene video prompts for >85% visual similarity

- **Architectural Decisions**:
  - Stage execution pattern established: `execute(inputs, config) -> outputs`
  - Synchronous execution for critical path stages (reference stage)
  - Video stage is DIFFERENT: parallel asyncio execution, not synchronous
  - Configuration-driven settings from `backend/app/config/pipelines/default.yaml`

- **S3 Upload Pattern**:
  - Reuse `S3Storage.upload_file()` from Story 1.2
  - Upload reference images to S3, same pattern applies to video clips
  - Pre-signed URLs for downloads (24hr expiration)

- **JSONB Storage Pattern**:
  - Story 1.2 stores reference_images as JSONB array in Generation table
  - Video stage stores video_clips as JSONB array using same pattern
  - Pydantic schemas (ReferenceImage, VideoClip) validate structure before storage

- **WebSocket Integration**:
  - Story 1.2 sends reference_images_ready WebSocket message
  - Video stage sends video_progress and video_complete messages
  - Reuse existing WebSocketManager from orchestrator

[Source: docs/sprint-artifacts/1-2-master-mode-3-reference-image-consistency-system.md#Dev-Notes]

### References

**Technical Specifications:**
- [Source: docs/sprint-artifacts/tech-spec-epic-epic-1.md#Video-Stage] - Video stage responsibilities and component structure (line 86)
- [Source: docs/sprint-artifacts/tech-spec-epic-epic-1.md#Data-Models-and-Contracts] - VideoClip schema (lines 196-206)
- [Source: docs/epics.md#Story-1.3] - Story 1.3 acceptance criteria (lines 206-271)

**Architecture Decisions:**
- [Source: docs/architecture.md#Parallel-Video-Clip-Generation-Pattern] - asyncio concurrent execution, semaphore limiting (lines 599-635)
- [Source: docs/architecture.md#ADR-004] - Parallel video generation architecture decision (lines 1636-1670)
- [Source: docs/architecture.md#Modular-Pipeline-Orchestration] - Independent stage modules with clear contracts (lines 78-86)

**Requirements Traceability:**
- [Source: docs/epics.md#FR34-FR35] - Parallel video generation requirements
- [Source: docs/epics.md#NFR-P8] - Parallel generation performance target

### Constraints and Technical Debt

**From Architecture.md:**
- **Replicate API Rate Limits:** Semaphore already limits concurrency to 5-10, implement exponential backoff on 429 responses, monitor Replicate API quotas
- **Partial Failure Handling:** If 1 of 5 clips fails, continue generating others, allow user to retry failed clip individually, do not fail entire generation
- **Performance Target:** Total video generation time < 90 seconds for 5 clips (target: ~60 seconds for 5 parallel clips), measure from first API call to last clip complete

**From Tech-Spec:**
- **Replicate Veo 3 Model:** Use Replicate Veo 3 for video generation, polling every 2 seconds until complete/failed, timeout after 10 minutes per clip
- **Consistency Context Required:** Reference images must be generated first (Story 1.2), video stage depends on consistency_context from reference stage

**From ADR-004:**
- **asyncio Concurrent Execution:** Use asyncio.gather() with semaphore, NOT threading or multiprocessing
- **Error Handling:** Use return_exceptions=True in gather() to catch individual clip failures without stopping other clips
- **WebSocket Per-Clip Updates:** Send progress/complete messages for EACH clip individually, frontend displays all simultaneously

**Existing Codebase to Leverage:**
- S3 Uploader: `backend/app/services/storage/s3_storage.py` (reuse for video clip uploads with retry logic)
- WebSocket Manager: `backend/app/services/session/websocket_manager.py` (reuse for progress streaming)
- Database models: `backend/app/db/models/generation.py` (Generation.video_clips JSONB field added in Story 1.1)
- Pydantic schemas: `backend/app/schemas/unified_pipeline.py` (VideoClip, VideoProgressMessage, VideoCompleteMessage defined in Story 1.1)

## Dev Agent Record

### Context Reference

- docs/sprint-artifacts/1-3-parallel-video-clip-generation-with-real-time-progress.context.xml

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
