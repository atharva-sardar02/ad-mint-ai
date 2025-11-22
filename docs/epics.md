# ad-mint-ai - Epic Breakdown

**Author:** BMad
**Date:** 2025-11-22
**Project Level:** TBD
**Target Scale:** TBD

---

## Overview

This document provides the complete epic and story breakdown for ad-mint-ai, decomposing the requirements from the [PRD](./PRD.md) into implementable stories.

**Living Document Notice:** This is the initial version. It will be updated after UX Design and Architecture workflows add interaction and technical details to stories.

This brownfield consolidation project transforms 4 fragmented video ad generation pipelines into a single, unified system. The epic below delivers the complete pipeline merge combining Master Mode's visual consistency, Interactive Mode's user feedback, Original Pipeline's quality scoring, and CLI Tools' headless execution.

**Epic Count:** 1
**Story Count:** 5
**Focus:** Consolidate 4 pipelines → 1 unified codebase with all capabilities

---

## Functional Requirements Inventory

### Core Consolidation Requirements (Extracted from PRD)

The unified pipeline must consolidate 4 separate pipelines into a single system:

**From Master Mode Pipeline (Best Visual Consistency):**
- FR14-FR18: 3-reference-image system for visual consistency
- FR27: Cross-scene consistency (characters, products, colors, motion)
- FR36: Motion continuity across clips

**From Interactive Pipeline (User Feedback):**
- FR10: Iterative story feedback
- FR29-FR31: Scene description editing and regeneration
- FR57-FR63: ChatGPT-style conversational interface
- FR75-FR81: Robust state management and WebSocket handling

**From Original Pipeline (Quality Scoring):**
- FR40-FR44: VBench quality scoring (background, non-blocking)
- FR98-FR104: Quality metrics display and storage

**From CLI Tools (Dual Execution):**
- FR82-FR97: Full CLI execution with all capabilities
- FR55: Unified configuration system (UI + CLI)

**New Unified Capabilities:**
- FR19-FR25: Flexible brand asset integration (0-N products, optional logo, 0-N characters)
- FR34-FR35: **Parallel video clip generation** (all scenes generate simultaneously)
- FR45-FR50: Parallel variant generation for A/B testing
- FR51-FR56: Configuration-driven architecture (no hardcoded prompts)

**Critical Non-Functional Requirements:**
- NFR-P8: Parallel video generation (total time = longest clip, not sum)
- NFR-P9: Non-blocking background processing (VBench, stitching)
- NFR-M1: Configuration-driven architecture
- NFR-M2: Modular pipeline stages

---

## FR Coverage Map

**Epic 1 - Pipeline Consolidation:** Addresses FRs from all 4 legacy pipelines:
- Master Mode FRs: FR14-FR18 (3-ref system), FR27 (cross-scene consistency), FR36 (motion continuity)
- Interactive FRs: FR10 (story feedback), FR29-FR31 (scene editing), FR57-FR63 (chat UI), FR75-FR81 (state management)
- Original Pipeline FRs: FR40-FR44 (VBench background scoring), FR98-FR104 (quality metrics)
- CLI FRs: FR82-FR97 (CLI execution), FR55 (unified config)
- New Unified FRs: FR19-FR25 (brand assets), FR34-FR35 (parallel video), FR45-FR50 (A/B testing), FR51-FR56 (config-driven)
- Architecture NFRs: NFR-P8 (parallel generation), NFR-P9 (background tasks), NFR-M1 (config-driven), NFR-M2 (modular)

---

## Epic 1: Unified Pipeline Consolidation

**Goal:** Merge 4 fragmented pipelines (Master Mode, Interactive, Original, CLI) into a single, modular, configuration-driven system that combines Master Mode's 3-reference-image visual consistency with Interactive Mode's conversational feedback flow, while adding parallel video generation and background quality scoring.

**User Value:** Developers maintain ONE codebase instead of FOUR, deployment velocity increases 3-4x, and users get the "impossible combination" - Master Mode-level consistency WITH Interactive Mode's narrative control.

**FRs Covered:** FR10, FR14-FR18, FR19-FR25, FR27, FR29-FR31, FR34-FR35, FR36, FR40-FR44, FR45-FR50, FR51-FR56, FR57-FR63, FR75-FR81, FR82-FR97, FR98-FR104 + NFR-P8, NFR-P9, NFR-M1, NFR-M2

---

### Story 1.1: Unified Pipeline Orchestrator & Configuration System

As a **backend developer**,
I want **a single pipeline orchestrator that coordinates all stages (story, references, scenes, videos) using externalized YAML configurations**,
So that **we eliminate hardcoded Master Mode prompts and have one execution path for both UI and CLI**.

**Acceptance Criteria:**

**Given** a brownfield codebase with 4 separate pipeline implementations
**When** I implement the unified orchestrator
**Then** a single `backend/app/services/unified_pipeline/orchestrator.py` module coordinates all pipeline stages

**And** all LLM prompts are externalized to `backend/app/config/prompts/*.yaml` files (story_director.yaml, story_critic.yaml, scene_writer.yaml, scene_critic.yaml, scene_cohesor.yaml)

**And** pipeline stage configurations are in `backend/app/config/pipelines/default.yaml` with:
  - Stage enable/disable flags (story: true, reference_images: true, scenes: true, videos: true)
  - Max iterations per stage (story: 3, scenes: 2)
  - Timeout settings (story: 120s, scenes: 180s, videos: 600s)
  - Quality thresholds (vbench_enabled: true, threshold_good: 80, threshold_acceptable: 60)
  - Parallel generation settings (parallel: true, max_concurrent: 5)

**And** the orchestrator loads configuration via `config_loader.py` with Pydantic validation (PipelineConfig schema)

**And** the orchestrator supports both interactive mode (waits for user approval via WebSocket at story and scene stages) and automated mode (runs entire pipeline without user input)

**And** the unified endpoint `POST /api/v2/generate` accepts GenerationRequest schema with:
  - prompt (required)
  - framework (optional: AIDA, PAS, FAB, custom)
  - brand_assets (optional: product_images[], logo, character_images[])
  - config overrides (optional: quality_threshold, parallel_variants, enable_vbench)
  - interactive flag (true for UI, false for CLI automated)
  - session_id (optional for resuming)

**And** the orchestrator creates a database Generation record tracking:
  - status (pending → story → references → scenes → videos → completed/failed)
  - current_stage
  - All outputs (story_text, reference_images JSONB, scenes JSONB, video_clips JSONB, final_video_url)
  - config used (JSONB snapshot of pipeline configuration)
  - error_message (if failed)

**Prerequisites:** None (foundation story)

**Technical Notes:**
- Architecture Section: Unified Pipeline Orchestration (lines 78-86 in architecture.md)
- Architecture Section: Configuration Patterns (lines 1008-1073)
- Use existing database models: Generation (lines 1092-1121 in architecture.md)
- Replaces hardcoded Master Mode prompts with YAML templates using {variables}
- Supports variable substitution: {framework}, {product}, {audience}, {message}, {requirements}
- CLI will call same orchestrator via `backend/cli_tools/admint.py`

---

### Story 1.2: Master Mode 3-Reference-Image Consistency System

As a **backend developer**,
I want **the reference image stage to implement Master Mode's proven 3-reference-image approach with GPT-4 Vision analysis**,
So that **all videos achieve >85% visual similarity across clips (Master Mode quality standard)**.

**Acceptance Criteria:**

**Given** the orchestrator has approved a story from the previous stage
**When** the reference stage executes via `backend/app/services/unified_pipeline/reference_stage.py`
**Then** the system generates or uses 3 reference images following this logic:

**And** **if user provided brand assets** (product_images, logo, character_images in request.brand_assets):
  - Use first 3 brand images as reference images
  - Prioritize: product_images[0], character_images[0], logo (or any provided assets up to 3)
  - Store mapping: which brand assets became references

**And** **if no brand assets provided**:
  - Generate 3 reference images from approved story using Replicate Nano Banana Pro
  - Prompts derived from story: main character, key product, scene environment
  - Ensure diversity: 1 character-focused, 1 product-focused, 1 environment-focused

**And** **GPT-4 Vision analyzes each reference image** to extract:
  - Character appearance (age, gender, clothing, hair, facial features, body type)
  - Product features (color, shape, size, branding, key visual elements)
  - Color palette (dominant colors as hex codes, accent colors)
  - Visual style (photorealistic, illustrated, 3D render, sketch)
  - Environmental context (indoor/outdoor, lighting, setting)

**And** analysis results stored in `reference_images` JSONB array:
```json
[
  {
    "url": "s3://bucket/ref1.jpg",
    "type": "character",
    "analysis": {
      "character_description": "...",
      "colors": ["#FF5733", "#C70039"],
      "style": "photorealistic"
    }
  },
  // ... 2 more references
]
```

**And** reference image characteristics passed to scene stage as `consistency_context` string:
```
CHARACTER APPEARANCE: [detailed description from analysis]
PRODUCT FEATURES: [detailed description from analysis]
COLOR PALETTE: [hex codes from analysis]
VISUAL STYLE: [style from analysis]
```

**And** in interactive mode, system displays generated reference images in chat feed with message: "Using these 3 reference images for visual consistency across all scenes" (read-only, no user feedback in MVP)

**And** reference images uploaded to S3 with paths stored in database

**Prerequisites:** Story 1.1 (orchestrator creates pipeline session and approves story)

**Technical Notes:**
- Architecture Pattern: 3-Reference-Image Consistency System (lines 711-752 in architecture.md)
- FR14-FR18: Reference image requirements
- FR19-FR25: Brand asset integration
- Uses `backend/app/services/media/image_processor.py` for GPT-4 Vision analysis
- Vision analysis prompt: "Analyze this image and extract: character appearance, product features, color palette (hex codes), visual style, environmental context"
- In MVP, reference images are NOT interactive - user cannot provide feedback or regenerate (deferred to Phase 2)

---

### Story 1.3: Parallel Video Clip Generation with Real-Time Progress

As a **backend developer**,
I want **all scene video clips to generate in parallel using asyncio with per-clip progress updates via WebSocket**,
So that **total video generation time = longest clip (~1 min), not sum of all clips (~5 min), achieving 5x speed improvement**.

**Acceptance Criteria:**

**Given** the orchestrator has approved scenes from the previous stage
**When** the video stage executes via `backend/app/services/unified_pipeline/video_stage.py`
**Then** all scene video clips generate **simultaneously in parallel** using asyncio:

**And** implementation uses asyncio.gather() to execute concurrent Replicate API calls:
```python
async def generate_all_videos_parallel(scenes: List[Scene], ref_context: str) -> List[VideoResult]:
    semaphore = asyncio.Semaphore(5)  # Max 5 concurrent Replicate calls

    async def generate_with_limit(scene):
        async with semaphore:
            # Include reference image consistency context in prompt
            full_prompt = f"{ref_context}\n\nSCENE: {scene.description}"
            return await replicate_api.generate_video(full_prompt, model="veo-3")

    tasks = [generate_with_limit(scene) for scene in scenes]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]
```

**And** each video generation task sends WebSocket progress updates:
  - `video_progress` message type with payload: `{clip_id: 1, progress: 45, status: "rendering"}`
  - Progress polled from Replicate API every 2 seconds
  - Status values: "queued", "processing", "rendering", "complete", "failed"

**And** as each clip completes, send `video_complete` WebSocket message:
  - Payload: `{clip_id: 1, url: "s3://bucket/clip1.mp4", duration: 6.2}`
  - Upload completed video to S3 immediately
  - Store in database Generation.video_clips JSONB array

**And** frontend displays **ParallelProgress component** showing all clips simultaneously:
  - `frontend/src/components/pipeline/ParallelProgress.tsx`
  - Shows progress bar for each clip (Clip 1: 45%, Clip 2: 32%, Clip 3: 51%)
  - Updates in real-time as WebSocket messages arrive
  - Visual indicator when each clip completes (green checkmark)

**And** error handling for partial failures:
  - If one clip fails, continue generating others
  - Store error in database with clip_index
  - Allow user to retry failed clip individually
  - Log failure with full context (scene description, error message, Replicate API response)

**And** after ALL clips complete (success or partial failure), trigger background stitching task

**And** total video generation time measured from first API call to last clip complete < 90 seconds (target: ~60 seconds for 5 clips)

**Prerequisites:** Story 1.2 (reference images with consistency context available)

**Technical Notes:**
- Architecture Pattern: Parallel Video Clip Generation (lines 599-635 in architecture.md)
- Architecture ADR-004: Parallel Video Generation Architecture (lines 1636-1670)
- FR34-FR35: Parallel video generation requirements
- NFR-P8: Parallel video generation performance target
- Use Replicate Veo 3 model via `POST /v1/predictions` and `GET /v1/predictions/{id}` polling
- Semaphore limits concurrent Replicate API calls (max 5-10) to avoid rate limits
- Reference image consistency context injected into EVERY scene prompt
- WebSocket manager: `backend/app/services/session/websocket_manager.py`

---

### Story 1.4: Background VBench Quality Scoring with Non-Blocking UI

As a **backend developer**,
I want **VBench quality scoring to run in FastAPI BackgroundTasks after video generation completes, streaming results via WebSocket as they become available**,
So that **users can download videos, navigate, or start new generations while VBench scores calculate in background (~30 seconds per video)**.

**Acceptance Criteria:**

**Given** a video clip has finished generating and uploaded to S3
**When** the video stage triggers VBench scoring
**Then** scoring runs in **FastAPI BackgroundTasks** (separate thread pool, non-blocking):

**And** implementation in `backend/app/api/routes/unified_pipeline.py`:
```python
@router.post("/api/v2/generate")
async def generate_video(request: GenerationRequest, background_tasks: BackgroundTasks):
    # ... generate videos synchronously ...
    video_clips = await orchestrator.generate_videos(scenes, ref_context)

    # Start VBench scoring in background (returns immediately)
    for clip in video_clips:
        background_tasks.add_task(
            run_vbench_scoring,
            video_path=clip.s3_url,
            clip_id=clip.id,
            generation_id=request.generation_id,
            session_id=request.session_id,
            websocket_manager=ws_manager  # Stream results via WebSocket
        )

    # Return immediately without waiting for VBench
    return GenerationResponse(
        generation_id=request.generation_id,
        video_clips=video_clips,
        status="complete",
        message="VBench scoring in progress - scores will stream in shortly"
    )
```

**And** VBench scorer implementation in `backend/app/services/quality/vbench_scorer.py`:
  - Accepts video S3 URL, downloads to temp file
  - Runs VBench metrics: overall_score, composition_score, coherence_score, motion_score, visual_appeal_score
  - Scoring duration ~30 seconds per video clip
  - Stores results in `quality_metrics` table with clip_index (0-N for clips, NULL for overall video)

**And** as each VBench score completes, send `vbench_score` WebSocket message:
```json
{
  "type": "vbench_score",
  "payload": {
    "clip_id": 1,
    "overall_score": 82.5,
    "breakdown": {
      "composition": 85,
      "coherence": 80,
      "motion": 78,
      "visual_appeal": 87
    }
  }
}
```

**And** frontend updates quality display **asynchronously without blocking UI**:
  - `frontend/src/components/quality/QualityScore.tsx` listens for WebSocket updates
  - Initially shows "Scoring..." placeholder
  - Updates to actual score when available (color-coded: green >80, yellow 60-80, red <60)
  - User can navigate to other pages, scores continue streaming in background

**And** after final video stitched, trigger overall VBench scoring in background:
  - Score final stitched video (all clips combined)
  - Send `vbench_score` message with `clip_id: null` (indicates overall video)
  - Store in quality_metrics with clip_index = NULL

**And** background task error handling:
  - If VBench fails, log error but DO NOT crash main application
  - Set quality_score = NULL in database
  - Display "Scoring unavailable" in UI instead of score
  - User can manually retry VBench scoring later via API endpoint

**And** UI remains fully interactive during all background processing:
  - Users can download videos before scores available
  - Users can start new generations while previous VBench runs
  - Users can navigate away, scores persist and display when returning

**Prerequisites:** Story 1.3 (video clips generated and uploaded to S3)

**Technical Notes:**
- Architecture Pattern: Background VBench Scoring (lines 637-675 in architecture.md)
- Architecture ADR-001: FastAPI BackgroundTasks vs Celery (lines 1562-1583)
- FR40-FR44, FR98-FR104: Quality scoring requirements
- NFR-P9: Non-blocking background processing
- FastAPI BackgroundTasks run in separate thread pool (adequate for I/O-bound VBench)
- VBench library: assumed to be existing Python package with `vbench.score(video_path) -> dict` API
- WebSocket updates use existing WebSocket manager from Story 1.1
- Display-only in MVP (no auto-regeneration based on scores - user decides)

---

### Story 1.5: Interactive Conversational Interface with State Management

As a **frontend developer**,
I want **a ChatGPT-style conversational UI that displays pipeline stages in a scrollable feed with robust WebSocket state management**,
So that **users experience the unified pipeline through a familiar, intuitive interface with zero data loss on navigation**.

**Acceptance Criteria:**

**Given** the user accesses the unified pipeline UI
**When** they interact with the generation process
**Then** the interface behaves as a ChatGPT-style conversation:

**And** UI layout in `frontend/src/routes/UnifiedPipeline.tsx`:
  - Dark background (#1a1a1a)
  - Scrollable chat feed with grey message bubbles (#2a2a2a)
  - Text input at bottom with send button
  - Optional settings icon for advanced config (framework selection, quality thresholds)

**And** chat feed components in `frontend/src/components/chat/`:
  - `ChatFeed.tsx`: Scrollable message list, auto-scrolls to bottom on new messages
  - `MessageBubble.tsx`: User messages (right-aligned, blue) vs system messages (left-aligned, grey)
  - `PromptInput.tsx`: Text input with send button, disabled during processing
  - `QuickActions.tsx`: Optional approve/regenerate buttons for story and scene stages

**And** pipeline stage displays in chat feed:
  - Story generated → Display text with quality score badge
  - Reference images ready → Display 3 images in grid (read-only, with caption "Using these for visual consistency")
  - Scenes generated → Display editable scene list with inline edit buttons
  - Video progress → Display ParallelProgress component (multiple progress bars updating simultaneously)
  - Video complete → Display VideoPlayer component with playback controls
  - VBench score → Display QualityScore component (streams in asynchronously)

**And** WebSocket state management in `frontend/src/services/websocket.ts`:
  - Auto-connect on component mount with session_id
  - Heartbeat/ping-pong every 30 seconds to keep connection alive
  - Auto-reconnect with exponential backoff (1s, 2s, 4s, 8s, max 30s) on disconnect
  - Message queueing: if disconnected, queue messages and send on reconnect
  - Clean disconnect on component unmount

**And** Zustand store in `frontend/src/store/pipelineStore.ts` manages:
  - Current pipeline state (status: "idle" | "story" | "references" | "scenes" | "videos" | "complete")
  - Generation session data (session_id, generation_id, prompt, framework)
  - Pipeline outputs (story_text, reference_images[], scenes[], video_clips[], quality_scores{})
  - Conversation history (all messages for display in ChatFeed)
  - WebSocket connection status (connected, disconnected, reconnecting)

**And** state persistence to database via `backend/app/services/session/session_storage.py`:
  - Save to Redis cache on every major state change (non-blocking async)
  - Save to PostgreSQL on stage completion (story approved, scenes approved, videos complete)
  - State includes: current_stage, all outputs, conversation history, timestamp

**And** navigation safety:
  - User can navigate away from pipeline page without losing progress
  - On return, restore session from database if within 24 hours
  - Display "Resuming generation session..." indicator
  - Continue WebSocket connection from last known state

**And** error recovery:
  - If WebSocket connection lost, show "Reconnecting..." banner (yellow, top of screen)
  - Retry connection with exponential backoff
  - On successful reconnect, fetch latest pipeline state from backend
  - If reconnect fails after 5 attempts, show "Connection lost" modal with manual retry button

**And** interactive breakpoints (2 in MVP):
  - **Story stage:** System displays generated story, waits for user input ("looks good" / "make it more dramatic" / "regenerate")
  - **Scene stage:** System displays scenes, user can edit descriptions inline or approve all
  - Reference images: Auto-generated, displayed read-only (NO feedback in MVP)

**And** conversation intent parsing in `backend/app/services/pipeline/conversation_handler.py`:
  - Rule-based detection for simple cases: {"yes", "ok", "looks good", "approve", "continue"} → APPROVE
  - "regenerate", "try again", "redo" → REGENERATE
  - Feedback with >5 words → REFINE (pass feedback to LLM for incorporation)
  - Default to REFINE with feedback text

**Prerequisites:** Story 1.1 (orchestrator and WebSocket endpoint), Story 1.3 (parallel video generation for ParallelProgress), Story 1.4 (VBench for QualityScore)

**Technical Notes:**
- Architecture Section: Interactive Conversational Interface (FR57-FR81 mapping, lines 331-342)
- Architecture Pattern: Conversational Intent Parsing (lines 677-709)
- FR57-FR63: Chat interface requirements
- FR64-FR69: Progress feedback (non-blocking UI updates)
- FR70-FR74: Media display
- FR75-FR81: State management and navigation safety
- WebSocket message types: user_feedback, story_generated, reference_images_ready, scenes_generated, video_progress, video_complete, vbench_score, error, heartbeat
- Use existing WebSocket implementation: `backend/app/api/routes/websocket.py`
- Redis session storage: `backend/app/services/session/session_storage.py` (already exists)
- Zustand lightweight state management (already in use, see architecture.md line 472-474)

---

## FR Coverage Matrix

| FR | Requirement | Epic | Story | Implementation Component |
|----|-------------|------|-------|--------------------------|
| FR10 | Iterative story feedback | 1 | 1.1, 1.5 | Orchestrator interactive mode + conversational UI |
| FR14-FR18 | 3-reference-image system | 1 | 1.2 | reference_stage.py + GPT-4 Vision analysis |
| FR19-FR25 | Brand asset integration | 1 | 1.2 | Flexible brand asset handling in reference stage |
| FR27 | Cross-scene consistency | 1 | 1.2, 1.3 | Consistency context injected into video prompts |
| FR29-FR31 | Scene editing/regeneration | 1 | 1.5 | SceneList.tsx inline editing + orchestrator |
| FR34-FR35 | Parallel video generation | 1 | 1.3 | asyncio.gather() with ParallelProgress UI |
| FR36 | Motion continuity | 1 | 1.3 | Consistency context in video prompts |
| FR40-FR44 | VBench background scoring | 1 | 1.4 | FastAPI BackgroundTasks + WebSocket streaming |
| FR45-FR50 | A/B testing variants | 1 | 1.1 | Orchestrator parallel_variants config |
| FR51-FR56 | Configuration-driven | 1 | 1.1 | YAML configs + config_loader.py |
| FR57-FR63 | ChatGPT-style UI | 1 | 1.5 | ChatFeed, MessageBubble, PromptInput components |
| FR75-FR81 | State management | 1 | 1.5 | Zustand + Redis + PostgreSQL persistence |
| FR82-FR97 | CLI execution | 1 | 1.1 | CLI calls same orchestrator as UI |
| FR98-FR104 | Quality metrics | 1 | 1.4 | vbench_scorer.py + quality_metrics table |
| NFR-P8 | Parallel generation | 1 | 1.3 | asyncio concurrent Replicate API calls |
| NFR-P9 | Non-blocking background | 1 | 1.4 | BackgroundTasks for VBench |
| NFR-M1 | Config-driven architecture | 1 | 1.1 | Externalized YAML prompts and configs |
| NFR-M2 | Modular pipeline stages | 1 | 1.1 | Separate stage modules in unified_pipeline/ |

**Coverage:** 100% of consolidation-related FRs covered by Epic 1's 5 stories

---

## Summary

### Epic 1 - Unified Pipeline Consolidation (5 Stories)

**What it delivers:**
- Single orchestrator replacing 4 separate pipelines (Master Mode, Interactive, Original, CLI)
- Configuration-driven architecture with externalized LLM prompts and pipeline settings
- Master Mode's 3-reference-image visual consistency system (>85% similarity across clips)
- Parallel video clip generation (5x speed improvement: 5 clips in ~1 min vs ~5 min sequential)
- Background VBench quality scoring (non-blocking, streams results via WebSocket)
- ChatGPT-style conversational interface with robust state management and navigation safety

**Story sequence:**
1. **Foundation:** Unified orchestrator with YAML configs, database tracking, interactive/automated modes
2. **Visual Consistency:** 3-reference-image system with GPT-4 Vision analysis, brand asset integration
3. **Performance:** Parallel video generation using asyncio with real-time progress updates
4. **Quality:** Background VBench scoring in FastAPI BackgroundTasks, non-blocking UI
5. **User Experience:** ChatGPT-style UI with WebSocket state management, conversation intent parsing

**Technical highlights:**
- Brownfield consolidation preserves existing database schema and AWS infrastructure
- All 4 original pipelines can be deprecated after epic completion
- Development velocity increases 3-4x (1 codebase to maintain vs 4)
- Zero regression from current best (Master Mode quality + Interactive Mode control)

**Context incorporated:**
- ✅ PRD requirements (all consolidation-related FRs)
- ✅ Architecture technical decisions (FastAPI BackgroundTasks, asyncio parallel generation, configuration patterns)

**Next steps after Epic 1 completion:**
- Deprecate and remove 4 original pipeline codebases
- Run end-to-end integration tests (pytest for backend, vitest for frontend)
- Performance validation: <10 min total generation, >85% visual consistency, VBench scores >80
- Deploy to staging, user acceptance testing with 3-5 test users

---

_For implementation: Use the `create-story` workflow to generate individual story implementation plans from this epic breakdown._

_This document will be updated after UX Design and Architecture workflows to incorporate interaction details and technical decisions._
