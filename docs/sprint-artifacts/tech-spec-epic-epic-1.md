# Epic Technical Specification: Unified Pipeline Consolidation

Date: 2025-11-22
Author: BMad
Epic ID: epic-1
Status: Draft

---

## Overview

Epic 1 consolidates four fragmented video ad generation pipelines (Master Mode, Interactive, Original, CLI) into a single, unified, configuration-driven system. This brownfield consolidation eliminates 4x code duplication while combining the best capabilities from each pipeline: Master Mode's proven 3-reference-image visual consistency system (>85% cross-clip similarity), Interactive Mode's conversational feedback at critical creative decision points (story and scene narratives), Original Pipeline's VBench quality scoring with non-blocking background processing, and CLI Tools' headless execution capabilities.

The unified pipeline delivers the "impossible combination" - Master Mode-level character/product consistency WITH Interactive Mode's narrative control - solving the fundamental UX problem plaguing all AI video generators where users must choose between visual consistency OR creative control. By implementing parallel video clip generation (asyncio concurrent execution), background VBench scoring (FastAPI BackgroundTasks), and a ChatGPT-style conversational interface with robust WebSocket state management, the system achieves professional-quality output (<10 min total generation, >85% visual similarity, VBench scores >80) while maintaining development velocity through single-codebase architecture.

## Objectives and Scope

**In Scope:**

- **Pipeline Consolidation:** Merge 4 separate pipeline codebases (Master Mode, Interactive, Original, CLI) into single unified orchestrator (`backend/app/services/unified_pipeline/orchestrator.py`)
- **Configuration-Driven Architecture:** Externalize all LLM prompts to YAML configs (`backend/app/config/prompts/*.yaml`), pipeline stage configurations (`backend/app/config/pipelines/default.yaml`), no hardcoded workflows
- **Master Mode 3-Reference-Image System:** Implement proven visual consistency approach using 3 reference images with GPT-4 Vision analysis for character/product/color extraction, inject consistency context into all scene prompts
- **Parallel Video Generation:** Generate all scene video clips simultaneously using asyncio concurrent Replicate API calls, semaphore-limited to 5-10 concurrent requests, total time = longest clip (~1 min) not sum (~5 min)
- **Background VBench Scoring:** Run quality scoring in FastAPI BackgroundTasks after video generation completes, stream results via WebSocket as they become available, UI remains fully responsive during scoring
- **Interactive Conversational Interface:** ChatGPT-style UI (`frontend/src/routes/UnifiedPipeline.tsx`) with 2 interactive breakpoints (story narrative and scene descriptions), conversation intent parsing, WebSocket real-time updates, session persistence (Redis + PostgreSQL)
- **Dual Execution Modes:** Full capabilities via web UI (interactive conversational flow) AND CLI (`backend/cli_tools/admint.py` headless execution), identical pipeline orchestration, both support interactive and automated modes
- **Flexible Brand Asset Integration:** Support 0-N product images, optional logo, 0-N character images as reference image inputs, auto-generate missing references from story if not provided
- **Database Integration:** Preserve existing database schema (Generation, QualityMetric, BrandStyle, ProductImage models), add JSONB fields for pipeline state tracking, quality metrics storage

**Out of Scope (Deferred to Phase 2):**

- Interactive reference image refinement (user feedback on generated references, custom uploads, regeneration) - MVP displays references read-only
- Auto-regeneration based on quality thresholds - MVP displays VBench scores for transparency, user manually decides to regenerate
- Multi-aspect ratio support (16:9, 9:16, 1:1, 4:5) - MVP uses default aspect ratio from Veo 3 model
- Batch processing from CSV - MVP supports single prompt or parallel variants from same session
- Campaign-level management and variant tracking - MVP supports A/B testing but no persistent campaign grouping
- Mobile responsive UI - MVP targets desktop/laptop only (>= 1366px width)
- Advanced accessibility (WCAG 2.1 Level AA) - MVP targets Level A baseline compliance only

## System Architecture Alignment

**Alignment with Architecture.md:**

The unified pipeline directly implements architectural patterns defined in the system architecture document:

- **Modular Pipeline Orchestration (Architecture lines 78-86):** Four independent pipeline stages (story, references, scenes, videos) coordinated by single orchestrator, each stage implemented as separate service module with clear input/output contracts
- **Background Task Processing (Architecture ADR-001, lines 1562-1583):** FastAPI BackgroundTasks for VBench scoring and video stitching, separate thread pool execution, non-blocking HTTP responses, WebSocket streaming for result updates
- **Parallel Video Generation (Architecture ADR-004, lines 1636-1670):** asyncio.gather() concurrent execution for all scene clips, semaphore rate limiting, per-clip WebSocket progress updates, 5x speed improvement (5 min → 1 min)
- **3-Reference-Image Consistency System (Architecture lines 711-752):** Vision AI analysis extracts character/product/color characteristics, consistency context injected into every scene video prompt, supports brand asset integration (0-N products, optional logo, 0-N characters)
- **Configuration Patterns (Architecture ADR-005, lines 1672-1706):** All LLM prompts externalized to YAML templates with variable substitution, pipeline stage configs (enable/disable, timeouts, quality thresholds), Pydantic validation for config schemas
- **Conversational Intent Parsing (Architecture lines 677-709):** Rule-based detection for simple approvals ("looks good", "approve"), LLM-enhanced for complex feedback ("make scene 2 more dramatic"), infers APPROVE/REGENERATE/REFINE intent from natural language
- **Data Models (Architecture lines 1092-1121):** Reuses existing Generation table with JSONB fields (reference_images, scenes, video_clips, config), QualityMetric table with clip_index for per-clip and overall scores, preserves brownfield schema compatibility

**Component Alignment:**

| Architecture Component | Epic 1 Implementation | Location |
|------------------------|----------------------|----------|
| Unified Orchestrator | Main pipeline coordinator, stage execution, interactive/automated modes | `backend/app/services/unified_pipeline/orchestrator.py` |
| Multi-Agent LLM System | Story Director/Critic, Scene Writer/Critic/Cohesor reusable agents | `backend/app/services/agents/*.py` |
| Reference Stage | 3-ref image generation, GPT-4 Vision analysis, brand asset integration | `backend/app/services/unified_pipeline/reference_stage.py` |
| Video Stage | Parallel asyncio video generation, Replicate API concurrent calls | `backend/app/services/unified_pipeline/video_stage.py` |
| VBench Scorer | Background quality scoring, BackgroundTasks execution | `backend/app/services/quality/vbench_scorer.py` |
| WebSocket Manager | Real-time bidirectional communication, auto-reconnect, heartbeat | `backend/app/services/session/websocket_manager.py` |
| ChatGPT-Style UI | Conversational interface, scrollable feed, real-time updates | `frontend/src/routes/UnifiedPipeline.tsx` + `components/chat/*` |
| CLI Execution | Headless pipeline execution calling same orchestrator as UI | `backend/cli_tools/admint.py` |

**Constraints from Architecture:**

- **No Celery Dependency:** Use FastAPI BackgroundTasks for MVP (adequate for VBench/stitching), can migrate post-MVP if task persistence becomes critical (ADR-001)
- **FastAPI Native WebSocket:** Continue existing implementation (`backend/app/api/routes/websocket.py`), no Socket.io migration needed, frontend already has auto-reconnect (ADR-002)
- **PostgreSQL Production / SQLite Development:** Preserve existing database setup, no schema migration required beyond adding JSONB fields
- **Brownfield Compatibility:** Cannot change existing database models (Generation, QualityMetric, etc.), add fields only, maintain backward compatibility

## Detailed Design

### Services and Modules

**Core Pipeline Services:**

| Service Module | Responsibilities | Inputs | Outputs | Owner Story |
|----------------|------------------|--------|---------|-------------|
| **Orchestrator** (`backend/app/services/unified_pipeline/orchestrator.py`) | Main pipeline coordinator, stage execution sequencing, interactive/automated mode routing, session state management | GenerationRequest (prompt, framework, brand_assets, config, interactive flag, session_id) | GenerationResponse (generation_id, session_id, websocket_url, status) | Story 1.1 |
| **Story Stage** (`backend/app/services/unified_pipeline/story_stage.py`) | Story generation using Director+Critic agents, iterative refinement loop, framework-specific prompt loading | Prompt, framework, max_iterations config | Story text, quality score, awaiting_approval flag | Story 1.1, 1.5 |
| **Reference Stage** (`backend/app/services/unified_pipeline/reference_stage.py`) | 3-reference-image generation/selection, GPT-4 Vision analysis, brand asset integration, consistency context extraction | Approved story, brand_assets (product_images, logo, character_images) | 3 reference images (S3 URLs), vision analysis results (character/product/color descriptions), consistency context string | Story 1.2 |
| **Scene Stage** (`backend/app/services/unified_pipeline/scene_stage.py`) | Scene generation using Writer+Critic+Cohesor agents, cross-scene consistency validation, individual scene regeneration | Approved story, reference consistency context, max_iterations config | Scene descriptions array (id, description, duration), quality scores | Story 1.1, 1.5 |
| **Video Stage** (`backend/app/services/unified_pipeline/video_stage.py`) | Parallel video clip generation (asyncio concurrent), Replicate API orchestration, per-clip progress tracking, S3 upload coordination | Approved scenes, reference consistency context, parallel config (max_concurrent) | Video clips array (scene_id, S3 URL, duration, status), per-clip progress updates via WebSocket | Story 1.3 |
| **Config Loader** (`backend/app/services/unified_pipeline/config_loader.py`) | Load and validate pipeline configurations, prompt template resolution, Pydantic schema validation | Config name (default, custom), overrides from request | PipelineConfig (stage settings, timeouts, quality thresholds), PromptTemplates (system/user prompts with variables) | Story 1.1 |

**Multi-Agent LLM System (Reusable Across Stages):**

| Agent | Responsibilities | Inputs | Outputs | Used By |
|-------|------------------|--------|---------|---------|
| **Story Director** (`backend/app/services/agents/story_director.py`) | Generate advertising story from prompt using specified framework (AIDA/PAS/FAB), incorporate user feedback for refinement | Prompt, framework, feedback (optional), prompt template from config | Story text (narrative arc with scenes) | Story Stage |
| **Story Critic** (`backend/app/services/agents/story_critic.py`) | Evaluate story quality, check framework adherence, identify improvement opportunities | Story text, framework, evaluation criteria | Quality score (0-10), feedback for refinement, approval recommendation | Story Stage |
| **Scene Writer** (`backend/app/services/agents/scene_writer.py`) | Generate detailed scene descriptions from story narrative, incorporate reference image context for consistency | Story text, reference consistency context, scene count | Scene descriptions array (detailed visual/action descriptions) | Scene Stage |
| **Scene Critic** (`backend/app/services/agents/scene_critic.py`) | Evaluate individual scene quality, check consistency with story, identify issues | Scene description, story context, quality criteria | Scene quality score, feedback for improvement | Scene Stage |
| **Scene Cohesor** (`backend/app/services/agents/scene_cohesor.py`) | Ensure cross-scene consistency (characters, products, colors, motion), validate narrative flow, synchronize references | All scene descriptions, reference consistency context | Cohesion validation result, consistency adjustments | Scene Stage |

**Quality & Media Services:**

| Service | Responsibilities | Inputs | Outputs | Execution Mode |
|---------|------------------|--------|---------|----------------|
| **VBench Scorer** (`backend/app/services/quality/vbench_scorer.py`) | Calculate VBench quality metrics (overall, composition, coherence, motion, visual_appeal), per-clip and overall video scoring | Video S3 URL, clip_index (0-N or NULL for overall) | QualityMetric record (overall_score, breakdown), WebSocket update message | BackgroundTasks (Story 1.4) |
| **Video Stitcher** (`backend/app/services/media/video_stitcher.py`) | Stitch individual scene clips into final coherent video, add transitions | Video clips array (S3 URLs in scene order) | Final video S3 URL | BackgroundTasks |
| **Image Processor** (`backend/app/services/media/image_processor.py`) | GPT-4 Vision analysis for reference images, extract character/product/color characteristics | Reference image S3 URL | Vision analysis (character_description, product_features, color_palette hex codes, visual_style) | Synchronous (Story 1.2) |
| **S3 Uploader** (`backend/app/services/media/s3_uploader.py`) | Upload media to S3 with retry logic, generate pre-signed download URLs (24hr expiration) | Local file path, bucket name, content type | S3 URL, pre-signed download URL | Synchronous with retry |

**Session & Communication Services:**

| Service | Responsibilities | Inputs | Outputs | Used By |
|---------|------------------|--------|---------|---------|
| **WebSocket Manager** (`backend/app/services/session/websocket_manager.py`) | Manage WebSocket connections per session, broadcast messages to connected clients, heartbeat/ping-pong | session_id, message type/payload | WebSocket message delivery to frontend | All pipeline stages (Story 1.5) |
| **Session Storage** (`backend/app/services/session/session_storage.py`) | Persist session state to Redis (cache) and PostgreSQL (durable), enable session resumption after navigation | session_id, pipeline state snapshot | Stored session data, retrieval by session_id | Orchestrator (Story 1.5) |
| **Conversation Handler** (`backend/app/services/pipeline/conversation_handler.py`) | Parse user natural language feedback, infer intent (APPROVE/REGENERATE/REFINE), extract feedback text | User message string, current pipeline stage context | Intent enum, extracted feedback text | Story Stage, Scene Stage (Story 1.5) |

**Frontend Components:**

| Component | Responsibilities | Inputs (Props) | Outputs (Events) | Owner Story |
|-----------|------------------|----------------|------------------|-------------|
| **UnifiedPipeline** (`frontend/src/routes/UnifiedPipeline.tsx`) | Main pipeline page, ChatGPT-style layout, orchestrate chat feed and input components | None (route-level) | Navigation events | Story 1.5 |
| **ChatFeed** (`frontend/src/components/chat/ChatFeed.tsx`) | Scrollable message list, auto-scroll to bottom, display user/system messages | messages array from pipelineStore | None (display only) | Story 1.5 |
| **PromptInput** (`frontend/src/components/chat/PromptInput.tsx`) | Text input with send button, disabled during processing, submit on Enter key | disabled flag, onSubmit handler | User message submission | Story 1.5 |
| **ParallelProgress** (`frontend/src/components/pipeline/ParallelProgress.tsx`) | Display multiple progress bars for parallel video generation, update in real-time | clips array (id, progress %, status) | None (display only) | Story 1.3 |
| **QualityScore** (`frontend/src/components/quality/QualityScore.tsx`) | Color-coded quality score display, streams updates as VBench completes | score (float), breakdown (composition, coherence, motion, visual_appeal) | None (display only) | Story 1.4 |
| **ReferenceImages** (`frontend/src/components/pipeline/ReferenceImages.tsx`) | Display 3 reference images in grid, read-only in MVP with usage caption | images array (url, type, analysis) | None (display only) | Story 1.2 |
| **SceneList** (`frontend/src/components/pipeline/SceneList.tsx`) | Editable scene descriptions list, inline edit buttons, regenerate individual scenes | scenes array (id, description, duration) | onEdit(scene_id, new_description), onRegenerate(scene_id) | Story 1.5 |

### Data Models and Contracts

**Database Schema (Existing Models with JSONB Extensions):**

```sql
-- Generations Table (Main Pipeline Execution Record)
-- Existing table with new JSONB fields for unified pipeline
CREATE TABLE generations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),

    -- Input
    prompt TEXT NOT NULL,
    framework VARCHAR(50),  -- AIDA, PAS, FAB, custom
    brand_assets JSONB,     -- NEW: Uploaded brand images {product_images: [], logo: "", character_images: []}

    -- Pipeline State
    status VARCHAR(50) NOT NULL,  -- pending, story, references, scenes, videos, completed, failed
    current_stage VARCHAR(50),

    -- Outputs (JSONB for flexibility)
    story_text TEXT,
    story_quality_score FLOAT,
    reference_images JSONB,  -- NEW: [{url, type, analysis: {character_description, colors, style}}]
    scenes JSONB,            -- NEW: [{id, description, duration, quality_score}]
    video_clips JSONB,       -- NEW: [{scene_id, url, duration, status, progress}]
    final_video_url TEXT,
    overall_quality_score FLOAT,

    -- Metadata
    config JSONB,            -- NEW: Pipeline configuration snapshot used for this generation
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Indexes for query performance
CREATE INDEX idx_generations_user_id ON generations(user_id);
CREATE INDEX idx_generations_status ON generations(status);
CREATE INDEX idx_generations_created_at ON generations(created_at DESC);
```

**JSONB Field Schemas (Pydantic Models):**

```python
# backend/app/schemas/unified_pipeline.py

from pydantic import BaseModel
from typing import List, Optional

class BrandAssets(BaseModel):
    product_images: List[str] = []  # S3 URLs
    logo: Optional[str] = None      # S3 URL
    character_images: List[str] = [] # S3 URLs

class ReferenceImageAnalysis(BaseModel):
    character_description: Optional[str] = None
    product_features: Optional[str] = None
    colors: List[str] = []  # Hex color codes
    style: Optional[str] = None  # photorealistic, illustrated, 3D render, etc.

class ReferenceImage(BaseModel):
    url: str  # S3 URL
    type: str  # product, character, logo, environment
    analysis: ReferenceImageAnalysis

class Scene(BaseModel):
    id: int
    description: str
    duration: float  # seconds
    quality_score: Optional[float] = None

class VideoClip(BaseModel):
    scene_id: int
    url: Optional[str] = None  # S3 URL when complete
    duration: Optional[float] = None
    status: str  # queued, processing, rendering, complete, failed
    progress: int = 0  # 0-100 percentage

class PipelineConfig(BaseModel):
    pipeline_name: str = "default"
    story_max_iterations: int = 3
    scene_max_iterations: int = 2
    video_parallel: bool = True
    video_max_concurrent: int = 5
    vbench_enabled: bool = True
    vbench_threshold_good: float = 80.0
    vbench_threshold_acceptable: float = 60.0
```

**Quality Metrics Table (Existing, No Changes):**

```sql
CREATE TABLE quality_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    generation_id UUID NOT NULL REFERENCES generations(id),
    clip_index INT,  -- NULL for overall video score, 0-N for individual clips

    -- VBench Metrics
    overall_score FLOAT,
    composition_score FLOAT,
    coherence_score FLOAT,
    motion_score FLOAT,
    visual_appeal_score FLOAT,

    -- Metadata
    scored_at TIMESTAMP NOT NULL DEFAULT NOW(),
    scoring_duration_ms INT
);

CREATE INDEX idx_quality_metrics_generation_id ON quality_metrics(generation_id);
```

**Relationships:**
- Generation (1) → QualityMetrics (N): One overall + per-clip scores
- User (1) → Generations (N): User owns multiple generations
- Reference images, scenes, video clips stored as JSONB arrays within Generation record

### APIs and Interfaces

**Unified Pipeline Endpoint (Story 1.1):**

```
POST /api/v2/generate
Content-Type: application/json
Authorization: Bearer {jwt_token}

Request Body:
{
  "prompt": "Create a 30-second ad for eco-friendly water bottle",
  "framework": "AIDA",  // Optional: AIDA, PAS, FAB, custom
  "brand_assets": {
    "product_images": ["s3://bucket/product1.jpg"],
    "logo": "s3://bucket/logo.png",
    "character_images": []
  },
  "config": {
    "parallel_variants": 1,
    "quality_threshold": 0.8,
    "enable_vbench": true
  },
  "interactive": true,  // true = wait for user feedback, false = automated
  "session_id": "abc123"  // Optional: resume existing session
}

Response (202 Accepted):
{
  "data": {
    "generation_id": "gen_abc123",
    "session_id": "session_xyz789",
    "websocket_url": "wss://api.example.com/ws/session_xyz789",
    "status": "pending"
  },
  "status": "success",
  "message": "Generation started. Connect to WebSocket for real-time updates."
}

Error Responses:
400 Bad Request - Invalid input (missing prompt, invalid framework)
401 Unauthorized - Missing/invalid JWT token
429 Too Many Requests - Rate limit exceeded (10 generations/hour)
500 Internal Server Error - Unexpected server error
```

**WebSocket Interactive Communication (Story 1.5):**

```
WS /ws/{session_id}

Client → Server (User Feedback):
{
  "type": "user_feedback",
  "payload": {
    "message": "make the first scene more dramatic",
    "stage": "scenes",
    "scene_id": 1  // Optional for scene-specific feedback
  },
  "timestamp": "2025-11-22T10:30:00Z"
}

Server → Client (Message Types):

// Story generated
{
  "type": "story_generated",
  "payload": {
    "story_text": "...",
    "quality_score": 8.5,
    "awaiting_approval": true
  },
  "timestamp": "2025-11-22T10:30:05Z"
}

// Reference images ready (Story 1.2)
{
  "type": "reference_images_ready",
  "payload": {
    "images": [
      {"url": "s3://...", "type": "product", "analysis": {...}},
      {"url": "s3://...", "type": "character", "analysis": {...}},
      {"url": "s3://...", "type": "logo", "analysis": {...}}
    ]
  }
}

// Video clip progress (Story 1.3 - Parallel Generation)
{
  "type": "video_progress",
  "payload": {
    "clip_id": 1,
    "progress": 45,  // 0-100 percentage
    "status": "rendering"
  }
}

// VBench score available (Story 1.4 - Background Scoring)
{
  "type": "vbench_score",
  "payload": {
    "clip_id": 1,  // NULL for overall video
    "overall_score": 82.5,
    "breakdown": {
      "composition": 85,
      "coherence": 80,
      "motion": 78,
      "visual_appeal": 87
    }
  }
}

// Generation complete
{
  "type": "generation_complete",
  "payload": {
    "generation_id": "gen_abc123",
    "final_video_url": "s3://...",
    "overall_quality_score": 83.2
  }
}
```

**CLI Interface (Story 1.1 - Dual Execution):**

```bash
# Interactive mode with brand assets
admint generate \
  --prompt "Athletic shoe ad" \
  --product-images ./assets/shoe-*.jpg \
  --logo ./brand/logo.png \
  --framework AIDA \
  --interactive

# Automated mode (no user feedback)
admint generate \
  --prompt "Eco-friendly water bottle ad" \
  --auto \
  --output ./output/

# Output quality metrics as JSON
admint generate \
  --prompt "..." \
  --auto \
  --format json \
  > results.json
```

**Internal Service Interfaces:**

```python
# backend/app/services/unified_pipeline/orchestrator.py

class PipelineOrchestrator:
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Main pipeline execution entry point."""

    async def execute_stage(self, stage_name: str, inputs: dict) -> StageResult:
        """Execute individual pipeline stage."""

    async def wait_for_approval(self, session_id: str, stage: str) -> UserFeedback:
        """Wait for user feedback in interactive mode."""

# backend/app/services/unified_pipeline/video_stage.py

async def generate_all_videos_parallel(
    scenes: List[Scene],
    consistency_context: str,
    max_concurrent: int = 5
) -> List[VideoResult]:
    """Generate all scene videos in parallel using asyncio."""

# backend/app/services/quality/vbench_scorer.py

async def run_vbench_scoring(
    video_path: str,
    clip_id: Optional[int],
    generation_id: str,
    session_id: str,
    websocket_manager: WebSocketManager
) -> QualityMetric:
    """Calculate VBench quality metrics in background."""
```

### Workflows and Sequencing

**Main Pipeline Execution Flow (Orchestrator):**

```
1. User submits prompt via UI or CLI
   ↓
2. Orchestrator.generate() creates Generation record (status: pending)
   ↓
3. IF interactive mode:
     a. STORY STAGE: Director generates → Critic evaluates → WS send to user
     b. WAIT for user feedback (approve/regenerate/refine)
     c. IF refine: Director regenerates with feedback → loop to 3b
     d. IF approve: proceed to 4
   ELSE automated mode:
     a. Story generation without user interaction
   ↓
4. REFERENCE STAGE:
   a. IF brand_assets provided: Use first 3 as references
   b. ELSE: Generate 3 reference images from approved story (Replicate Nano Banana Pro)
   c. GPT-4 Vision analyzes each image → extract character/product/color
   d. Build consistency_context string from analysis
   e. WS send reference images to user (read-only display in MVP)
   ↓
5. IF interactive mode:
     a. SCENE STAGE: Writer generates → Critic evaluates → Cohesor validates consistency → WS send to user
     b. WAIT for user feedback (approve/edit scene N/regenerate all)
     c. IF edit scene N: Regenerate scene N only → loop to 5b
     d. IF approve: proceed to 6
   ELSE automated mode:
     a. Scene generation without user interaction
   ↓
6. VIDEO STAGE (Parallel Generation - Story 1.3):
   a. Create asyncio tasks for ALL scenes simultaneously
   b. Semaphore limits concurrent Replicate API calls (max 5-10)
   c. Each task:
      - Inject consistency_context into scene prompt
      - Call Replicate Veo 3 API → poll every 2 seconds
      - WS send per-clip progress updates (clip_id, progress %, status)
      - On complete: Upload to S3 → WS send video_complete event
   d. asyncio.gather() waits for all clips to complete
   e. Total time ≈ longest clip time (~1 min), not sum (~5 min)
   ↓
7. BACKGROUND TASKS (Non-blocking - Story 1.4):
   a. For each completed video clip:
      - BackgroundTasks.add_task(run_vbench_scoring, clip_path, clip_id)
      - VBench calculates quality metrics (~30 sec per clip)
      - WS send vbench_score event as each completes
   b. After all clips complete:
      - BackgroundTasks.add_task(stitch_videos, clip_urls)
      - Stitch final video → upload to S3
      - BackgroundTasks.add_task(run_vbench_scoring, final_video_path, clip_id=NULL)
      - WS send overall quality score when available
   ↓
8. Update Generation record (status: completed, final_video_url)
   ↓
9. WS send generation_complete event
   ↓
10. User can download video, view scores, navigate away (UI stays responsive)
```

**Parallel Video Generation Sequence (Story 1.3):**

```
Scene 1 ─┐
Scene 2 ─┤
Scene 3 ─┼─> asyncio.gather() ──> [Video 1, Video 2, Video 3, Video 4, Video 5]
Scene 4 ─┤                         (All complete in ~1 min = longest clip time)
Scene 5 ─┘

Timeline:
t=0s:     All 5 Replicate API calls initiated
t=2s:     Poll all 5 predictions for progress → WS updates
t=4s:     Poll again → WS updates (Clip 3: 25%, Clip 1: 18%, ...)
...
t=60s:    All clips complete → Upload to S3 → WS video_complete events
```

**Background VBench Scoring Sequence (Story 1.4):**

```
Video Generation Complete (HTTP 202 response sent to user)
   ↓
FastAPI BackgroundTasks (separate thread pool):
   ↓
┌─────────────────────────────────────────┐
│ Task 1: VBench Clip 1 (~30s)           │ ─┐
│ Task 2: VBench Clip 2 (~30s)           │  │ Run in parallel
│ Task 3: VBench Clip 3 (~30s)           │  │ (I/O bound, thread pool)
│ ...                                     │ ─┘
│ Each task:                              │
│   - Download video from S3              │
│   - Run VBench scoring                  │
│   - Save to quality_metrics table       │
│   - WS send vbench_score event          │
└─────────────────────────────────────────┘
   ↓
User sees scores stream in as they complete
UI remains fully interactive (can navigate, start new generation)
```

**Conversational Intent Parsing Flow (Story 1.5):**

```
User types message in chat input
   ↓
Frontend sends WS message (type: user_feedback, payload: {message, stage})
   ↓
Backend WebSocket route receives message
   ↓
ConversationHandler.parse_intent(message, stage)
   ↓
Rule-based detection:
   - IF message in {"yes", "looks good", "approve", "ok"} → Intent.APPROVE
   - IF "regenerate" or "try again" in message → Intent.REGENERATE
   - IF "edit scene N" pattern → Intent.EDIT with scene_id extraction
   ↓
ELSE (complex feedback):
   - LLM-enhanced analysis: "make scene 2 more dramatic"
   - Extract intent + feedback text
   ↓
Orchestrator routes based on intent:
   - APPROVE: Proceed to next stage
   - REGENERATE: Re-run current stage
   - REFINE: Pass feedback text to agent for incorporation
   ↓
WS send updated content to user
```

## Non-Functional Requirements

### Performance

**Critical Performance Targets (PRD NFR-P1 to NFR-P9):**

| Metric | Target | Measurement | PRD Reference | Epic 1 Implementation |
|--------|--------|-------------|---------------|----------------------|
| **Total Generation Time** | < 10 minutes (95th percentile) | Initial prompt → final stitched video including user feedback loops | NFR-P1 | Parallel video generation (Story 1.3) reduces 5 min → 1 min, background VBench (Story 1.4) removes blocking |
| **WebSocket Latency** | < 200ms | Message delivery from backend → frontend | NFR-P2 | FastAPI native WebSocket with minimal serialization overhead (Story 1.5) |
| **UI Responsiveness** | 60fps (16ms frame time) | State changes → DOM updates | NFR-P3 | Zustand lightweight state management, React 19 concurrent rendering (Story 1.5) |
| **Page Load Time** | < 3 seconds to interactive | Initial load on broadband (25 Mbps+) | NFR-P4 | Vite code splitting, lazy route loading (existing architecture) |
| **API Response Time** | < 500ms (P95) | Non-generation endpoints (auth, config, history) | NFR-P5 | Database indexes on user_id, status, created_at; connection pooling |
| **Parallel Video Generation** | Total time = longest clip (~1 min), not sum (~5 min) | 5 scene clips generated simultaneously | NFR-P8 | asyncio.gather() with semaphore limiting (max 5-10 concurrent), Story 1.3 |
| **Background Processing** | Non-blocking VBench scoring, UI fully responsive | User can navigate/download while scoring runs | NFR-P9 | FastAPI BackgroundTasks for VBench/stitching, WebSocket streaming results, Story 1.4 |

**Performance Budget Allocation (NFR-P1 breakdown):**
- Story generation: 1-2 minutes (OpenAI GPT-4 with Director+Critic iterations)
- Reference images: 1-2 minutes (Generate 3 images via Replicate + GPT-4 Vision analysis)
- Scene generation: 2-3 minutes (Writer+Critic+Cohesor for 5 scenes)
- **Video generation: 4-5 minutes → optimized to ~1 minute with parallel execution (5x improvement, Story 1.3)**
- VBench scoring: ~30 seconds per clip, **runs in background non-blocking (Story 1.4)**
- Video stitching: ~30 seconds, **runs in background after all clips complete**

**Memory Efficiency (NFR-P6):**
- Frontend: < 500MB per session (5-10 generations) - lazy loading media assets, cleanup on unmount
- Backend: < 1GB per concurrent generation session - stream video uploads to S3, no in-memory buffering

**Asset Loading Performance (NFR-P7):**
- Generated images render in viewport < 500ms (S3 pre-signed URLs with CDN headers)
- Video thumbnails prioritized over full video files (progressive loading)
- S3 pre-signed URL generation < 100ms (in-memory JWT signing)

### Security

**Authentication & Authorization (PRD NFR-S1):**
- **JWT Tokens:** 30-day expiration, bcrypt password hashing (12 rounds), refresh token support
- **API Tokens for CLI:** User-revocable tokens stored hashed in database, passed via `Authorization: Bearer {token}` header
- **Session Security:** HttpOnly cookies for web sessions, secure flag in production, SameSite=Strict
- **Password Reset:** Single-use tokens with 1-hour expiration, email verification required
- **Implementation:** `backend/app/core/security.py` (existing, no changes needed)

**API Key Protection (PRD NFR-S2):**
- **Environment Variables:** OPENAI_API_KEY, REPLICATE_API_TOKEN stored in .env (never committed to git)
- **Backend-Only AI Calls:** Frontend never receives API keys, all OpenAI/Replicate requests from backend services
- **Rate Limiting:** 10 generations/hour per user (configurable via `backend/app/config/pipelines/default.yaml`)
- **Cost Monitoring:** Track API usage per generation, log costs in quality_metrics table, alert on >$X/day spikes
- **Implementation:** All agents (`backend/app/services/agents/*.py`) load API keys from environment

**Input Validation (PRD NFR-S3):**
- **Pydantic Request Schemas:** All API requests validated via `backend/app/schemas/unified_pipeline.py` models
- **Prompt Length:** Max 5000 characters (validate in GenerationRequest schema)
- **File Upload:** Max 10MB per file, 50MB total per generation (validate in `backend/app/api/routes/assets.py`)
- **File Type Validation:** Allowed image types: jpg, png, webp (MIME type + magic number validation)
- **SQL Injection Prevention:** SQLAlchemy ORM with parameterized queries (no raw SQL)
- **XSS Prevention:** React auto-escapes JSX content, CSP headers in production

**Data Privacy (PRD NFR-S4):**
- **Private by Default:** User content not publicly accessible, no public gallery in MVP
- **S3 Pre-Signed URLs:** 24-hour expiration for downloads (`backend/app/services/media/s3_uploader.py`)
- **GDPR Compliance:** User can delete all generations via DELETE /api/generations (soft delete with deleted_at timestamp)
- **No Sensitive Logging:** Passwords, API keys excluded from logs (filter in `backend/app/core/logging.py`)

**Transport Security (PRD NFR-S5):**
- **HTTPS:** All production traffic over TLS 1.3, valid certificates (Let's Encrypt or AWS ACM)
- **WSS:** WebSocket Secure for all real-time communication (`wss://` protocol)
- **HSTS:** Strict-Transport-Security header enabled in Nginx config (`deployment/nginx.conf`)
- **CORS:** Allowed origins configured in `backend/app/main.py` (restrict to production domain)

**Rate Limiting (PRD NFR-S6):**
- **Generation Endpoints:** 10 generations/hour per user (enforced in `backend/app/api/routes/unified_pipeline.py`)
- **Authentication Endpoints:** 5 login attempts per 15 minutes per IP (prevent brute force)
- **Rate Limit Response:** 429 Too Many Requests with Retry-After header
- **Implementation:** slowapi middleware (existing) or Redis-based rate limiter

### Reliability/Availability

**Uptime & Availability (PRD NFR-I5):**
- **Target:** 99% uptime for MVP (allows ~7 hours downtime per month)
- **Health Checks:** GET /health endpoint returns API status, database connection, Redis connection, background task queue status
- **Monitoring:** CloudWatch alarms for API error rate > 5%, response time > 1s (P95), background task failures
- **Planned Maintenance:** Scheduled during low-usage periods (announced 24 hours in advance)

**Graceful Degradation (PRD NFR-I2):**
- **VBench Scoring Failure:** If VBench service unavailable, log warning and proceed without scores (set quality_score = NULL, display "Scoring unavailable" in UI)
- **WebSocket Disconnect:** Frontend auto-reconnects with exponential backoff (1s, 2s, 4s, 8s, max 30s), queues messages during disconnect
- **S3 Upload Failure:** Retry up to 3 times with exponential backoff, if still fails mark generation as failed with error message
- **OpenAI/Replicate API Errors:** Transient failures (5xx, timeouts) retry 3 times, permanent failures (4xx) fail immediately with user-friendly error
- **Implementation:** Error handling in all service modules with try-except fallbacks

**Error Recovery (PRD NFR-I3):**
- **Transient Failures:** Network timeouts, 5xx errors retry automatically (3 attempts, exponential backoff 1s → 2s → 4s)
- **Permanent Failures:** 4xx errors, invalid API keys fail immediately with actionable error message ("Invalid API key, check configuration")
- **Partial Video Generation Failure:** If 1 of 5 clips fails, continue generating others, allow user to retry failed clip individually
- **Session Recovery:** WebSocket reconnection restores session state from database/Redis, resume from last known pipeline stage
- **Database Backups:** Daily automated backups to S3 with 30-day retention, point-in-time recovery capability

**Data Integrity (PRD NFR-I1, NFR-I5):**
- **Session State Persistence:** Save to Redis (cache, 24hr TTL) and PostgreSQL (durable) after each stage completion (Story 1.5)
- **No Data Loss During Errors:** Auto-save pipeline state before background operations, commit Generation record updates in transactions
- **Database Constraints:** Foreign keys enforce referential integrity (Generation → User, QualityMetric → Generation)
- **Concurrency Control:** Optimistic locking for Generation updates (check updated_at timestamp, retry on conflict)

### Observability

**Logging (PRD NFR-I4, NFR-M6):**
- **Framework:** Python stdlib logging with structured JSON formatter (zero dependencies)
- **Log Levels:**
  - DEBUG: Detailed diagnostic info (development only) - agent prompts/responses, config loading
  - INFO: General informational messages (production default) - pipeline stage transitions, API requests, background task start/completion
  - WARNING: Unexpected but handled situations - API rate limit warnings, quality score below threshold
  - ERROR: Errors requiring attention - AI service failures, database errors, S3 upload failures
  - CRITICAL: System-critical failures - database unavailable, Redis connection lost
- **Structured Format:**
  ```json
  {
    "timestamp": "2025-11-22T10:30:00Z",
    "level": "INFO",
    "message": "Story generation complete",
    "session_id": "abc123",
    "user_id": "user456",
    "generation_id": "gen789",
    "duration_ms": 1250,
    "quality_score": 8.5,
    "framework": "AIDA"
  }
  ```
- **Implementation:** Configure in `backend/app/core/logging.py`, use logger.info(..., extra={context}) for structured fields

**Metrics & Monitoring (PRD NFR-I4):**
- **API Latency:** Track response time per endpoint (P50, P95, P99), alert if P95 > 500ms for non-generation endpoints
- **Generation Success Rate:** Track completed/failed generations ratio, alert if failure rate > 10%
- **AI Service Costs:** Log cost per generation (OpenAI tokens, Replicate API minutes), aggregate daily/monthly spend
- **Background Task Queue:** Monitor BackgroundTasks queue depth, task completion rate, alert if queue growing (>100 pending tasks)
- **Database Performance:** Track query execution time, slow query log for queries > 1 second
- **WebSocket Connections:** Track active connections, connection churn rate, message throughput

**Health Checks (PRD NFR-I4):**
```
GET /health

Response:
{
  "status": "healthy",
  "checks": {
    "database": "healthy",  // PostgreSQL connection test
    "redis": "healthy",     // Redis connection test
    "background_tasks": {
      "status": "healthy",
      "pending_count": 3,
      "processing_count": 2
    },
    "disk_space": "healthy"  // Temp file storage availability
  },
  "timestamp": "2025-11-22T10:30:00Z"
}
```

**Tracing (Deferred to Post-MVP):**
- Distributed tracing for multi-service requests (OpenTelemetry)
- Request ID propagation through all services
- Trace pipeline execution across all stages (story → references → scenes → videos)

**Error Tracking:**
- All exceptions logged with full stack traces (`logger.exception()`)
- Error context includes: user_id, generation_id, session_id, pipeline stage, input parameters
- Critical errors trigger alerts (email/Slack) for immediate investigation
- Error aggregation dashboard showing top errors by frequency

## Dependencies and Integrations

### External Service Dependencies

**AI/ML Services:**

| Service | Purpose | Version/Model | Authentication | Epic 1 Usage | Cost Impact |
|---------|---------|---------------|----------------|--------------|-------------|
| **OpenAI GPT-4** | Story generation (Director), scene generation (Writer), conversation intent parsing | GPT-4 Turbo (latest) | API Key (env: OPENAI_API_KEY) | Stories 1.1, 1.5 - all LLM agent calls | ~$0.03-0.05 per generation (story + scenes) |
| **OpenAI GPT-4 Vision** | Reference image analysis (character/product/color extraction) | GPT-4 Vision (latest) | API Key (env: OPENAI_API_KEY) | Story 1.2 - 3 image analyses per generation | ~$0.01 per generation (3 images) |
| **Replicate Nano Banana Pro** | Reference image generation when no brand assets provided | Latest via Replicate API | Token (env: REPLICATE_API_TOKEN) | Story 1.2 - generate 3 reference images if needed | ~$0.10 per generation (3 images) |
| **Replicate Veo 3** | Video clip generation from scene descriptions | Latest via Replicate API | Token (env: REPLICATE_API_TOKEN) | Story 1.3 - 5 video clips per generation (parallel) | ~$0.50-1.00 per generation (5 clips @ 6s each) |

**Infrastructure Services:**

| Service | Purpose | Configuration | Epic 1 Usage |
|---------|---------|---------------|--------------|
| **AWS S3** | Media storage (reference images, video clips, final videos) | Bucket: {project}-videos, {project}-images, IAM role or access keys | All stories - upload generated media, serve via pre-signed URLs (24hr expiration) |
| **AWS RDS PostgreSQL** | Production database (generations, quality_metrics, users) | PostgreSQL 14+, connection pooling | All stories - persist pipeline state, session data, quality scores |
| **Redis** | Session caching, WebSocket state persistence | Redis 5.0+, 24hr TTL for session data | Story 1.5 - WebSocket session state, conversation history cache |
| **AWS EC2** | Application hosting (FastAPI backend, Nginx reverse proxy) | Instance type based on load | All stories - run backend services, serve frontend static files |

### Backend Dependencies

**Core Framework (from requirements.txt):**

```python
# Web Framework & Server
fastapi>=0.104.0          # Async API framework, WebSocket support, OpenAPI docs
uvicorn[standard]>=0.24.0 # ASGI server for FastAPI
python-multipart>=0.0.20  # File upload support

# Database & ORM
sqlalchemy>=2.0.0         # ORM for PostgreSQL, async support
psycopg2-binary>=2.9.0    # PostgreSQL driver (sync)
asyncpg>=0.29.0           # PostgreSQL driver (async for SQLAlchemy 2.0)

# Data Validation & Config
pydantic>=2.0.0           # Request/response schemas, config validation
python-dotenv>=1.0.0      # Environment variable loading

# AI Services
openai>=1.0.0             # OpenAI GPT-4 API client
replicate>=0.25.0         # Replicate API client (Veo 3, Nano Banana Pro)

# Media Processing
moviepy>=1.0.3            # Video stitching, clip manipulation
opencv-python>=4.8.0      # Video processing, frame extraction
pillow>=10.0.0            # Image processing, format conversion

# Machine Learning (VBench dependencies)
transformers>=4.30.0      # Hugging Face transformers for VBench
torch>=2.0.0              # PyTorch for VBench scoring
numpy>=1.24.0,<2.0        # Numerical computing (VBench, video processing)

# Cloud Storage & Auth
boto3>=1.34.0             # AWS S3 SDK for media uploads
bcrypt>=4.0.0             # Password hashing
PyJWT>=2.8.0              # JWT token generation/validation

# Session & Caching
redis>=5.0.0              # Redis client for session storage

# HTTP & Testing
httpx>=0.24.0             # Async HTTP client for external APIs
requests>=2.31.0          # HTTP client (legacy, sync)
pytest>=7.4.0             # Testing framework
pytest-asyncio>=0.21.0    # Async test support
```

**Critical Dependency Notes:**
- **VBench library:** Currently commented out in requirements.txt - requires installation from GitHub (Vchitect/VBench) when available, Story 1.4 implementation
- **NumPy version constraint:** `<2.0` due to VBench compatibility (transformers/torch requirements)
- **PyTorch:** Large dependency (~1GB), required for VBench quality scoring only

### Frontend Dependencies

**Core Framework (from package.json):**

```json
{
  "dependencies": {
    "react": "^19.2.0",              // UI framework - latest version
    "react-dom": "^19.2.0",          // React DOM rendering
    "react-router-dom": "^7.9.6",    // Client-side routing
    "zustand": "^5.0.8",             // Lightweight state management
    "axios": "^1.13.2"               // HTTP client for API calls
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^5.1.0",     // Vite React plugin
    "vite": "^5.4.11",                    // Build tool, dev server
    "typescript": "~5.9.3",               // Type checking
    "tailwindcss": "^4.1.17",             // Utility-first CSS
    "@testing-library/react": "^16.1.0",  // React component testing
    "vitest": "^1.6.0",                   // Test runner (Vite integration)
    "eslint": "^9.39.1",                  // Code linting
    "prettier": "^3.6.2"                  // Code formatting
  }
}
```

**Key Version Notes:**
- **React 19:** Latest version with concurrent rendering features (Story 1.5 UI responsiveness)
- **Tailwind CSS 4.1.17:** Very new version (architecture decision: acceptable risk, monitor for stability issues)
- **Zustand 5.0:** Lightweight state management for pipeline session state (pipelineStore, authStore, uiStore)

### Integration Points Summary

**API Integrations (Story-Specific Usage):**

| Integration | Endpoint | Request Pattern | Response | Error Handling | Used By |
|-------------|----------|-----------------|----------|----------------|---------|
| **OpenAI Chat Completions** | POST /v1/chat/completions | {"model": "gpt-4-turbo", "messages": [...]} | {"choices": [{"message": {"content": "..."}}]} | Retry 3x on 5xx/timeout, fail fast on 4xx | Story 1.1 (Director, Critic), Story 1.5 (conversation parsing) |
| **OpenAI Vision** | POST /v1/chat/completions | {"model": "gpt-4-vision-preview", "messages": [{"content": [{"type": "image_url", ...}]}]} | Analysis text in response | Retry 3x on transient failures | Story 1.2 (reference image analysis) |
| **Replicate Predictions** | POST /v1/predictions | {"version": "{model-version}", "input": {...}} | {"id": "pred_123", "status": "starting"} | Retry 3x on 5xx, poll every 2s until complete | Story 1.2 (image gen), Story 1.3 (video gen) |
| **Replicate Poll** | GET /v1/predictions/{id} | None (GET request) | {"status": "succeeded", "output": "url"} | Continue polling until succeeded/failed, timeout after 10 min | Story 1.3 (video generation progress) |
| **AWS S3 Upload** | PUT to pre-signed URL | Binary file data | 200 OK | Retry 3x with exponential backoff | All stories (media upload) |

**Internal Component Integrations:**

| From Component | To Component | Data Flow | Protocol | Used By |
|----------------|--------------|-----------|----------|---------|
| Frontend (UnifiedPipeline.tsx) | Backend (WebSocket route) | User feedback messages | WebSocket (wss://) | Story 1.5 |
| Backend (Orchestrator) | Frontend (via WebSocket) | Pipeline stage updates, progress | WebSocket broadcast | All stories |
| Orchestrator | Story/Scene/Video Stages | Stage execution requests | Python async function calls | Story 1.1 |
| Video Stage | VBench Scorer | Video S3 URL for scoring | BackgroundTasks queue | Story 1.4 |
| All Stages | Session Storage | Pipeline state snapshots | Redis write (cache) + PostgreSQL write (durable) | Story 1.5 |

## Acceptance Criteria (Authoritative)

**Epic 1 consolidates 4 separate pipelines into 1 unified system. Acceptance criteria extracted from epic stories in epics.md:**

### AC-1: Pipeline Consolidation & Configuration (Story 1.1)

**Given** a brownfield codebase with 4 separate pipeline implementations (Master Mode, Interactive, Original, CLI)

**When** Epic 1 implementation is complete

**Then** the following must be true:

1. **Single Orchestrator Exists:** A single `backend/app/services/unified_pipeline/orchestrator.py` module coordinates all pipeline stages (story → references → scenes → videos)

2. **Externalized Prompts:** All LLM prompts are externalized to YAML files in `backend/app/config/prompts/` directory:
   - `story_director.yaml` - Story generation prompt template
   - `story_critic.yaml` - Story evaluation prompt
   - `scene_writer.yaml` - Scene description generation
   - `scene_critic.yaml` - Scene evaluation prompt
   - `scene_cohesor.yaml` - Cross-scene consistency validation

3. **Pipeline Stage Configuration:** Pipeline configurations exist in `backend/app/config/pipelines/default.yaml` with:
   - Stage enable/disable flags (story: true, reference_images: true, scenes: true, videos: true)
   - Max iterations per stage (story: 3, scenes: 2)
   - Timeout settings (story: 120s, scenes: 180s, videos: 600s)
   - Quality thresholds (vbench_enabled: true, threshold_good: 80, threshold_acceptable: 60)
   - Parallel generation settings (parallel: true, max_concurrent: 5)

4. **Pydantic Config Validation:** Orchestrator loads configuration via `config_loader.py` with Pydantic validation (PipelineConfig schema validates all settings before execution)

5. **Dual Execution Modes:** Orchestrator supports:
   - **Interactive mode:** Waits for user approval via WebSocket at story and scene stages
   - **Automated mode:** Runs entire pipeline without user input (CLI headless execution)

6. **Unified API Endpoint:** `POST /api/v2/generate` endpoint accepts GenerationRequest schema with all required fields (prompt, framework, brand_assets, config overrides, interactive flag, session_id)

7. **Database Tracking:** Orchestrator creates Generation database record tracking:
   - Status progression (pending → story → references → scenes → videos → completed/failed)
   - Current stage indicator
   - All outputs (story_text, reference_images JSONB, scenes JSONB, video_clips JSONB, final_video_url)
   - Config snapshot used (JSONB)
   - Error message if failed

8. **No Hardcoded Workflows:** Zero hardcoded prompts or pipeline logic in Python code - all configurable via YAML

### AC-2: 3-Reference-Image Visual Consistency (Story 1.2)

**Given** the orchestrator has approved a story from the previous stage

**When** the reference stage executes

**Then** the following must occur:

1. **3 Reference Images Generated/Selected:**
   - **IF user provided brand assets:** Use first 3 brand images (prioritize: product_images[0], character_images[0], logo)
   - **IF no brand assets:** Generate 3 reference images from story using Replicate Nano Banana Pro (1 character-focused, 1 product-focused, 1 environment-focused)

2. **GPT-4 Vision Analysis:** Each reference image analyzed to extract:
   - Character appearance (age, gender, clothing, hair, facial features, body type)
   - Product features (color, shape, size, branding, key visual elements)
   - Color palette (dominant colors as hex codes, accent colors)
   - Visual style (photorealistic, illustrated, 3D render, sketch)
   - Environmental context (indoor/outdoor, lighting, setting)

3. **JSONB Storage:** Analysis results stored in Generation.reference_images JSONB array:
   ```json
   [{"url": "s3://...", "type": "character", "analysis": {"character_description": "...", "colors": ["#FF5733"], "style": "photorealistic"}}, ...]
   ```

4. **Consistency Context String:** Reference characteristics passed to scene stage as `consistency_context`:
   ```
   CHARACTER APPEARANCE: [detailed description]
   PRODUCT FEATURES: [detailed description]
   COLOR PALETTE: [hex codes]
   VISUAL STYLE: [style]
   ```

5. **Interactive Display:** In interactive mode, system displays generated reference images in chat feed with message "Using these 3 reference images for visual consistency across all scenes" (read-only, no user feedback in MVP)

6. **S3 Upload:** Reference images uploaded to S3 with paths stored in database

### AC-3: Parallel Video Clip Generation (Story 1.3)

**Given** the orchestrator has approved scenes from the previous stage

**When** the video stage executes

**Then** the following must happen:

1. **Parallel Execution:** All scene video clips generate **simultaneously in parallel** using asyncio.gather() - NOT sequentially

2. **Semaphore Rate Limiting:** Implementation uses asyncio.Semaphore(5) to limit concurrent Replicate API calls (max 5-10 simultaneous requests)

3. **Consistency Context Injection:** Each video generation prompt includes reference image consistency context:
   ```python
   full_prompt = f"{consistency_context}\n\nSCENE: {scene.description}"
   ```

4. **WebSocket Progress Updates:** Each video generation task sends real-time progress:
   - Message type: `video_progress`
   - Payload: `{clip_id: 1, progress: 45, status: "rendering"}`
   - Polling frequency: Every 2 seconds from Replicate API
   - Status values: "queued", "processing", "rendering", "complete", "failed"

5. **Clip Completion Notifications:** As each clip completes, send `video_complete` WebSocket message:
   - Payload: `{clip_id: 1, url: "s3://bucket/clip1.mp4", duration: 6.2}`
   - Immediate S3 upload after generation
   - Store in Generation.video_clips JSONB array

6. **Frontend ParallelProgress Component:** UI displays `ParallelProgress.tsx` showing all clips simultaneously with individual progress bars updating in real-time

7. **Error Handling:** Partial failure support:
   - If one clip fails, continue generating others
   - Store error in database with clip_index
   - Allow user to retry failed clip individually
   - Log failure with full context

8. **Performance Target Met:** Total video generation time < 90 seconds for 5 clips (target: ~60 seconds = longest single clip time, NOT sum of all clips = ~300 seconds)

### AC-4: Background VBench Quality Scoring (Story 1.4)

**Given** a video clip has finished generating and uploaded to S3

**When** the video stage triggers VBench scoring

**Then** the following must be true:

1. **Background Execution:** VBench scoring runs in **FastAPI BackgroundTasks** (separate thread pool, non-blocking):
   ```python
   background_tasks.add_task(run_vbench_scoring, video_path, clip_id, generation_id, session_id, websocket_manager)
   ```

2. **Immediate HTTP Response:** API returns 202 Accepted immediately without waiting for VBench (message: "VBench scoring in progress - scores will stream in shortly")

3. **Per-Clip Scoring:** Each video clip scored independently in background (~30 seconds per clip)

4. **VBench Metrics Calculated:**
   - overall_score (0-100)
   - composition_score
   - coherence_score
   - motion_score
   - visual_appeal_score

5. **Database Persistence:** Scores stored in quality_metrics table with clip_index (0-N for clips, NULL for overall video)

6. **WebSocket Streaming:** As each VBench score completes, send `vbench_score` WebSocket message:
   ```json
   {"type": "vbench_score", "payload": {"clip_id": 1, "overall_score": 82.5, "breakdown": {...}}}
   ```

7. **Frontend Non-Blocking Updates:** `QualityScore.tsx` component updates asynchronously:
   - Initially shows "Scoring..." placeholder
   - Updates to actual score when available
   - Color-coded: green >80, yellow 60-80, red <60

8. **Overall Video Scoring:** After final video stitched, trigger overall VBench scoring in background (clip_id: null)

9. **UI Remains Interactive:** User can download videos, navigate to other pages, or start new generation while VBench runs in background

10. **Error Handling:** If VBench fails:
    - Log error but DO NOT crash main application
    - Set quality_score = NULL in database
    - Display "Scoring unavailable" in UI instead of score

### AC-5: Interactive Conversational Interface (Story 1.5)

**Given** the user accesses the unified pipeline UI

**When** they interact with the generation process

**Then** the interface must behave as follows:

1. **ChatGPT-Style Layout:** `UnifiedPipeline.tsx` displays:
   - Dark background (#1a1a1a)
   - Scrollable chat feed with grey message bubbles (#2a2a2a)
   - Text input at bottom with send button
   - Optional settings icon for advanced config

2. **Pipeline Stage Display:** Chat feed shows all stages:
   - Story generated → Text with quality score badge
   - Reference images ready → 3 images in grid (read-only, caption: "Using these for visual consistency")
   - Scenes generated → Editable scene list with inline edit buttons
   - Video progress → ParallelProgress component (multiple progress bars)
   - Video complete → VideoPlayer component with playback controls
   - VBench score → QualityScore component (streams in asynchronously)

3. **WebSocket State Management:** `frontend/src/services/websocket.ts` implements:
   - Auto-connect on component mount with session_id
   - Heartbeat/ping-pong every 30 seconds
   - Auto-reconnect with exponential backoff (1s, 2s, 4s, 8s, max 30s)
   - Message queueing: if disconnected, queue messages and send on reconnect
   - Clean disconnect on component unmount

4. **Zustand Store:** `pipelineStore.ts` manages:
   - Current pipeline state (status: "idle" | "story" | "references" | "scenes" | "videos" | "complete")
   - Generation session data (session_id, generation_id, prompt, framework)
   - Pipeline outputs (story_text, reference_images[], scenes[], video_clips[], quality_scores{})
   - Conversation history (all messages for ChatFeed display)
   - WebSocket connection status (connected, disconnected, reconnecting)

5. **State Persistence:** Session data saved to database:
   - Redis cache on every major state change (non-blocking async)
   - PostgreSQL on stage completion (durable storage)
   - State includes: current_stage, all outputs, conversation history, timestamp

6. **Navigation Safety:**
   - User can navigate away without losing progress
   - On return, restore session from database if within 24 hours
   - Display "Resuming generation session..." indicator
   - Continue WebSocket connection from last known state

7. **Error Recovery:**
   - WebSocket connection lost → show "Reconnecting..." banner (yellow, top of screen)
   - Retry with exponential backoff
   - On successful reconnect → fetch latest pipeline state from backend
   - If reconnect fails after 5 attempts → show "Connection lost" modal with manual retry button

8. **Interactive Breakpoints (2 in MVP):**
   - **Story stage:** Display generated story, wait for user input ("looks good" / "make it more dramatic" / "regenerate")
   - **Scene stage:** Display scenes, user can edit descriptions inline or approve all

9. **Conversation Intent Parsing:** `conversation_handler.py` detects:
   - Rule-based: {"yes", "ok", "looks good", "approve", "continue"} → APPROVE
   - "regenerate", "try again", "redo" → REGENERATE
   - Feedback with >5 words → REFINE (pass feedback to LLM for incorporation)

## Traceability Mapping

**Mapping acceptance criteria → spec sections → implementation components → test coverage:**

| AC | Requirement | Spec Section(s) | Component(s) | Test Coverage |
|----|-------------|-----------------|--------------|---------------|
| **AC-1.1** | Single orchestrator module | Detailed Design - Services & Modules | `backend/app/services/unified_pipeline/orchestrator.py` | `tests/test_services/test_orchestrator.py` - verify single entry point |
| **AC-1.2** | Externalized prompts to YAML | Detailed Design - Services & Modules, Configuration Patterns | `backend/app/config/prompts/*.yaml`, `config_loader.py` | `tests/test_services/test_config_loader.py` - validate prompt loading |
| **AC-1.3** | Pipeline stage configuration | Detailed Design - Data Models, APIs | `backend/app/config/pipelines/default.yaml` | `tests/test_services/test_config_loader.py` - validate config schema |
| **AC-1.4** | Pydantic config validation | Detailed Design - Data Models | `backend/app/schemas/unified_pipeline.py` - PipelineConfig | `tests/test_schemas/test_unified_pipeline.py` - schema validation tests |
| **AC-1.5** | Dual execution modes | Detailed Design - Workflows & Sequencing | `orchestrator.py` - interactive/automated routing | `tests/test_integration/test_pipeline_modes.py` - both modes |
| **AC-1.6** | Unified API endpoint | Detailed Design - APIs & Interfaces | `backend/app/api/routes/unified_pipeline.py` - POST /api/v2/generate | `tests/test_api/test_unified_pipeline.py` - endpoint tests |
| **AC-1.7** | Database tracking | Detailed Design - Data Models | `backend/app/db/models/generation.py` - Generation model | `tests/test_integration/test_pipeline_execution.py` - verify state transitions |
| **AC-1.8** | No hardcoded workflows | Configuration Patterns (Architecture) | All service modules load from config | Code review - grep for hardcoded prompts (should be zero) |
| **AC-2.1** | 3 reference images | Detailed Design - Services & Modules | `backend/app/services/unified_pipeline/reference_stage.py` | `tests/test_services/test_reference_stage.py` - verify 3 images generated |
| **AC-2.2** | GPT-4 Vision analysis | Detailed Design - Services & Modules | `backend/app/services/media/image_processor.py` | `tests/test_services/test_image_processor.py` - mock Vision API calls |
| **AC-2.3** | JSONB storage | Detailed Design - Data Models | Generation.reference_images JSONB field | `tests/test_db/test_generation_model.py` - JSONB serialization |
| **AC-2.4** | Consistency context string | Detailed Design - Workflows & Sequencing | `reference_stage.py` - build_consistency_context() | `tests/test_services/test_reference_stage.py` - verify context format |
| **AC-2.5** | Interactive display | Detailed Design - APIs & Interfaces | WebSocket message type: reference_images_ready | `tests/test_api/test_websocket.py` - verify WS message sent |
| **AC-2.6** | S3 upload | Dependencies & Integrations | `backend/app/services/media/s3_uploader.py` | `tests/test_services/test_s3_uploader.py` - mock boto3 |
| **AC-3.1** | Parallel execution | Detailed Design - Workflows & Sequencing, NFR Performance | `video_stage.py` - asyncio.gather() | `tests/test_services/test_video_stage.py` - verify concurrent execution |
| **AC-3.2** | Semaphore rate limiting | Detailed Design - Workflows & Sequencing | `video_stage.py` - asyncio.Semaphore(5) | `tests/test_services/test_video_stage.py` - verify max 5 concurrent |
| **AC-3.3** | Consistency context injection | Detailed Design - Workflows & Sequencing | `video_stage.py` - prompt building | `tests/test_services/test_video_stage.py` - verify context in prompts |
| **AC-3.4** | WebSocket progress updates | Detailed Design - APIs & Interfaces | WebSocket message type: video_progress | `tests/test_api/test_websocket.py` - verify progress messages |
| **AC-3.5** | Clip completion notifications | Detailed Design - APIs & Interfaces | WebSocket message type: video_complete | `tests/test_api/test_websocket.py` - verify completion messages |
| **AC-3.6** | ParallelProgress component | Detailed Design - Services & Modules (Frontend) | `frontend/src/components/pipeline/ParallelProgress.tsx` | `tests/components/test_ParallelProgress.test.tsx` - render multiple bars |
| **AC-3.7** | Error handling | NFR Reliability | `video_stage.py` - try-except per clip | `tests/test_services/test_video_stage.py` - test partial failure |
| **AC-3.8** | Performance target | NFR Performance | `video_stage.py` - parallel execution | `tests/test_integration/test_performance.py` - measure total time < 90s |
| **AC-4.1** | Background execution | Detailed Design - Workflows & Sequencing, NFR Performance | `unified_pipeline.py` - BackgroundTasks.add_task() | `tests/test_api/test_unified_pipeline.py` - verify non-blocking response |
| **AC-4.2** | Immediate HTTP response | NFR Performance | `unified_pipeline.py` - return 202 Accepted | `tests/test_api/test_unified_pipeline.py` - verify 202 status |
| **AC-4.3** | Per-clip scoring | Detailed Design - Services & Modules | `vbench_scorer.py` - run_vbench_scoring() | `tests/test_services/test_vbench_scorer.py` - mock VBench library |
| **AC-4.4** | VBench metrics | Detailed Design - Data Models | quality_metrics table - 5 score fields | `tests/test_db/test_quality_metric_model.py` - verify schema |
| **AC-4.5** | Database persistence | Detailed Design - Data Models | quality_metrics table with clip_index | `tests/test_services/test_vbench_scorer.py` - verify DB write |
| **AC-4.6** | WebSocket streaming | Detailed Design - APIs & Interfaces | WebSocket message type: vbench_score | `tests/test_api/test_websocket.py` - verify score messages |
| **AC-4.7** | Frontend updates | Detailed Design - Services & Modules (Frontend) | `QualityScore.tsx` - async state updates | `tests/components/test_QualityScore.test.tsx` - test score display |
| **AC-4.8** | Overall video scoring | Detailed Design - Workflows & Sequencing | `vbench_scorer.py` - clip_id=NULL for overall | `tests/test_services/test_vbench_scorer.py` - verify overall scoring |
| **AC-4.9** | UI remains interactive | NFR Performance | BackgroundTasks thread pool isolation | Manual testing - verify navigation during scoring |
| **AC-4.10** | Error handling | NFR Reliability | `vbench_scorer.py` - try-except with logging | `tests/test_services/test_vbench_scorer.py` - test VBench failure |
| **AC-5.1** | ChatGPT-style layout | Detailed Design - Services & Modules (Frontend) | `UnifiedPipeline.tsx`, `ChatFeed.tsx` | `tests/routes/test_UnifiedPipeline.test.tsx` - verify layout |
| **AC-5.2** | Pipeline stage display | Detailed Design - Services & Modules (Frontend) | Chat feed components (StoryDisplay, ReferenceImages, etc.) | Component tests for each display type |
| **AC-5.3** | WebSocket state mgmt | Detailed Design - Services & Modules (Frontend), NFR Reliability | `frontend/src/services/websocket.ts` | `tests/services/test_websocket.test.ts` - test reconnection |
| **AC-5.4** | Zustand store | Detailed Design - Services & Modules (Frontend) | `pipelineStore.ts` | `tests/store/test_pipelineStore.test.ts` - state transitions |
| **AC-5.5** | State persistence | NFR Reliability | `backend/app/services/session/session_storage.py` | `tests/test_services/test_session_storage.py` - Redis + PostgreSQL |
| **AC-5.6** | Navigation safety | NFR Reliability | Session restoration on return | `tests/test_integration/test_session_recovery.py` - full flow |
| **AC-5.7** | Error recovery | NFR Reliability | WebSocket auto-reconnect, state fetch | `tests/services/test_websocket.test.ts` - reconnection logic |
| **AC-5.8** | Interactive breakpoints | Detailed Design - Workflows & Sequencing | Orchestrator wait_for_approval() | `tests/test_integration/test_interactive_mode.py` - verify 2 breakpoints |
| **AC-5.9** | Intent parsing | Detailed Design - Services & Modules | `conversation_handler.py` - parse_intent() | `tests/test_services/test_conversation_handler.py` - various inputs |

**Test Coverage Summary:**
- **Unit Tests:** 45+ test files covering all service modules, data models, API endpoints
- **Integration Tests:** 10+ test files for end-to-end pipeline execution, WebSocket communication, session recovery
- **Frontend Tests:** 15+ component tests (vitest + @testing-library/react)
- **Performance Tests:** Verify parallel video generation < 90s, background VBench non-blocking
- **Manual Testing:** WebSocket auto-reconnect, navigation safety, UI responsiveness during background tasks

## Risks, Assumptions, Open Questions

### Risks

| Risk ID | Description | Impact | Probability | Mitigation Strategy | Owner Story |
|---------|-------------|--------|-------------|---------------------|-------------|
| **R1** | VBench library not yet available as pip package (commented in requirements.txt) | **HIGH** - Story 1.4 blocked until VBench installable | **MEDIUM** | Monitor Vchitect/VBench GitHub for release, implement placeholder scorer returning mock scores for testing, migrate to real VBench when available | Story 1.4 |
| **R2** | Replicate API rate limits may throttle parallel video generation (5-10 concurrent requests) | **MEDIUM** - Could slow video generation if rate limited | **LOW** | Semaphore already limits concurrency to 5-10, implement exponential backoff on 429 responses, monitor Replicate API quotas | Story 1.3 |
| **R3** | Background VBench scoring could accumulate if generation rate exceeds scoring rate (~30s per clip) | **MEDIUM** - BackgroundTasks queue could grow unbounded | **MEDIUM** | Monitor background task queue depth (health check endpoint), alert if >100 pending tasks, migrate to Celery if task persistence becomes critical post-MVP | Story 1.4 |
| **R4** | WebSocket connection stability over long generation sessions (10+ minutes) | **MEDIUM** - User may lose real-time updates | **LOW** | Implement heartbeat/ping-pong every 30 seconds, auto-reconnect with exponential backoff, fallback to polling if WebSocket unavailable | Story 1.5 |
| **R5** | Database schema migration risk - adding JSONB fields to existing Generation table | **LOW** - Migration could lock table during deployment | **LOW** | Test migration on staging database first, use online schema change tool (pg_repack) for zero-downtime if needed, schedule migration during low-usage period | Story 1.1 |
| **R6** | OpenAI/Replicate API cost overruns if usage exceeds projections | **HIGH** - Unexpected costs could impact budget | **MEDIUM** | Implement rate limiting (10 generations/hour per user), track costs per generation in database, set up CloudWatch billing alarms for >$X/day | All stories |
| **R7** | Parallel video generation may overwhelm Replicate API if too many users generate simultaneously | **MEDIUM** - 429 rate limit errors | **MEDIUM** | Implement global semaphore across all users (not just per-generation), queue requests if limit reached, display "High demand, estimated wait time: X minutes" to users | Story 1.3 |
| **R8** | React 19 + Tailwind CSS 4.1 are very new - potential ecosystem compatibility issues | **LOW** - May encounter bugs or incompatible plugins | **MEDIUM** | Monitor GitHub issues for both libraries, have rollback plan to React 18 + Tailwind 3.4 if critical bugs discovered, thorough testing before production deployment | Story 1.5 |

### Assumptions

| Assumption ID | Description | Validation Strategy | Impact if Invalid |
|---------------|-------------|---------------------|-------------------|
| **A1** | VBench scoring library will become available as pip package within Epic 1 timeframe | Monitor Vchitect/VBench GitHub weekly, reach out to maintainers | If unavailable: Implement alternative quality scoring (CLIP similarity, DOVER, or defer to post-MVP) |
| **A2** | Existing database schema can accommodate JSONB fields without breaking backward compatibility | Review existing Generation model usage, test migration on staging | If incompatible: Create new GenerationV2 table, migrate data gradually |
| **A3** | FastAPI BackgroundTasks adequate for VBench/stitching workload (no Celery needed for MVP) | Load test with 10+ concurrent generations, monitor task queue depth | If inadequate: Migrate to Celery with Redis broker post-MVP (ADR-001 migration path) |
| **A4** | Users will accept 2 interactive breakpoints (story and scenes) without demanding reference image feedback in MVP | User acceptance testing with 3-5 test users, collect feedback | If demanded: Add reference image interactive breakpoint in Phase 2 (already scoped out of MVP) |
| **A5** | Replicate Veo 3 model supports parallel requests with reasonable rate limits | Test concurrent API calls in development, monitor 429 responses | If rate limits too strict: Implement queue system, batch generations, or explore alternative video models |
| **A6** | S3 storage costs remain manageable with video retention policy (no expiration in MVP) | Calculate storage costs based on generation volume projections | If costs excessive: Implement video expiration policy (delete after 30 days), tier to Glacier for long-term storage |
| **A7** | PostgreSQL JSONB performance adequate for querying generation history with 100,000+ records | Create indexes on Generation.created_at, .user_id, .status, test query performance at scale | If slow: Add JSONB indexes (GIN indexes on reference_images, scenes, video_clips fields) |
| **A8** | WebSocket connections can sustain 10-minute generation sessions without disconnecting | Stress test WebSocket with long-running connections, implement heartbeat | If unreliable: Add polling fallback, increase heartbeat frequency, consider Socket.io with automatic fallback |

### Open Questions

| Question ID | Question | Decision Needed By | Stakeholder | Current Status |
|-------------|----------|-------------------|-------------|----------------|
| **Q1** | Should Epic 1 include CLI batch processing from CSV, or defer to Phase 2? | Before Story 1.1 implementation | Product Owner | **DECISION:** Defer to Phase 2 - CLI supports single prompts only in MVP (FR90 scoped out) |
| **Q2** | What quality score threshold should trigger automatic regeneration in future releases? | Post-MVP (not needed for Story 1.4) | Product Owner + Users | **DEFERRED:** MVP displays scores only, user manually decides to regenerate (no auto-regeneration) |
| **Q3** | Should reference images be deletable/replaceable in Phase 2, or just viewable? | Before UX Design for Phase 2 | UX Designer + Product Owner | **PENDING:** To be decided in Phase 2 planning |
| **Q4** | How should video stitching handle transitions between clips (hard cut, fade, dissolve)? | Before Story 1.1 implementation | Video Producer + Product Owner | **DECISION:** Hard cuts only in MVP - moviepy concatenate_videoclips() default behavior |
| **Q5** | Should conversation intent parsing use LLM for all inputs, or rule-based with LLM fallback? | Before Story 1.5 implementation | Technical Architect | **DECISION:** Rule-based for simple cases (faster, cheaper), LLM fallback for complex feedback (Architecture lines 677-709) |
| **Q6** | What happens if user navigates away during video generation - continue in background or pause? | Before Story 1.5 implementation | Product Owner + UX Designer | **DECISION:** Continue in background, restore progress when user returns (session persistence) |
| **Q7** | Should Epic 1 support multiple aspect ratios (16:9, 9:16, 1:1), or single aspect ratio? | Before Story 1.3 implementation | Product Owner | **DECISION:** Single aspect ratio (Veo 3 default) in MVP, defer multi-aspect to Phase 2 (FR extended video formats) |
| **Q8** | How to handle API cost allocation across users (free tier, usage limits, billing)? | Post-MVP (admin features) | Product Owner + Finance | **DEFERRED:** Rate limiting (10 gen/hour) sufficient for MVP, usage-based billing in future |

## Test Strategy Summary

### Testing Approach

**Epic 1 testing follows a pyramid strategy: extensive unit tests (70% coverage target) → integration tests for critical flows → manual testing for UX validation.**

### Test Levels

**1. Unit Tests (Backend - pytest):**

**Coverage Target:** >70% for service layer business logic

**Test Suites:**
- `tests/test_services/` - All service modules (orchestrator, stages, agents, quality, media, session)
- `tests/test_db/` - Database models, JSONB serialization, relationships
- `tests/test_schemas/` - Pydantic validation (GenerationRequest, PipelineConfig, etc.)
- `tests/test_api/` - API endpoint handlers (unified_pipeline.py, websocket.py)

**Key Test Cases:**
- Orchestrator stage sequencing (story → references → scenes → videos)
- Config loader YAML validation and Pydantic schema enforcement
- Reference stage: 3-image generation vs brand asset usage logic
- Video stage: asyncio.gather() concurrent execution, semaphore limiting
- VBench scorer: BackgroundTasks execution, WebSocket message sending
- Conversation handler: intent parsing (APPROVE/REGENERATE/REFINE detection)
- Session storage: Redis cache + PostgreSQL persistence

**Mocking Strategy:**
- Mock OpenAI API calls (httpx.AsyncClient)
- Mock Replicate API calls (replicate.predictions.create)
- Mock S3 uploads (boto3.client)
- Mock VBench library (when unavailable, placeholder implementation)
- Mock WebSocket manager for service tests

**2. Integration Tests (Backend - pytest):**

**Test Suites:**
- `tests/test_integration/test_pipeline_execution.py` - End-to-end pipeline (prompt → final video)
- `tests/test_integration/test_interactive_mode.py` - User feedback loops (story approval, scene editing)
- `tests/test_integration/test_session_recovery.py` - WebSocket disconnect → reconnect → state restoration
- `tests/test_integration/test_performance.py` - Parallel video generation timing, background VBench non-blocking

**Key Test Scenarios:**
- **Full Pipeline (Automated Mode):** Submit GenerationRequest → verify status transitions → check final_video_url populated
- **Interactive Mode (2 Breakpoints):** Submit prompt → receive story → send approval → receive scenes → send approval → receive videos
- **Parallel Video Generation:** 5 scenes → verify asyncio.gather() concurrency → total time < 90 seconds
- **Background VBench:** Video complete → verify 202 response → verify vbench_score WebSocket messages arrive asynchronously
- **Session Recovery:** Start generation → disconnect WebSocket → reconnect → verify state restored from database
- **Error Recovery:** Replicate API returns 500 → verify 3 retries → verify graceful failure with error message

**3. Frontend Tests (vitest + @testing-library/react):**

**Test Suites:**
- `tests/components/` - React component tests (ChatFeed, ParallelProgress, QualityScore, etc.)
- `tests/routes/` - Route component tests (UnifiedPipeline.tsx)
- `tests/services/` - WebSocket manager, API client
- `tests/store/` - Zustand store state transitions

**Key Test Cases:**
- **ChatFeed Component:** Render messages, auto-scroll to bottom, display user/system bubbles
- **ParallelProgress Component:** Render multiple progress bars, update progress on props change
- **QualityScore Component:** Display "Scoring...", update to actual score asynchronously, color coding
- **WebSocket Manager:** Auto-connect, heartbeat, auto-reconnect on disconnect, message queueing
- **Pipeline Store:** State transitions (idle → story → references → scenes → videos → complete)
- **UnifiedPipeline Route:** Integration test - render full page, submit prompt, display chat feed

**4. API Contract Tests:**

**Tool:** pytest with OpenAPI schema validation

**Test Strategy:**
- Validate all API requests/responses match OpenAPI spec (generated from FastAPI)
- Test error responses (400, 401, 429, 500) return correct error format
- Test WebSocket message types match documented schema

**5. Performance Tests:**

**Tool:** pytest-benchmark, locust (load testing)

**Test Cases:**
- **Parallel Video Generation Timing:** Measure total time for 5 clips, verify < 90 seconds
- **WebSocket Latency:** Measure message delivery time, verify < 200ms (P95)
- **API Response Time:** Non-generation endpoints < 500ms (P95)
- **Database Query Performance:** Generation history queries with 100,000 records < 500ms
- **Load Testing:** 50 concurrent users generating videos, measure success rate, response times

**6. Manual Testing (UAT):**

**Test Users:** 3-5 representative users (solo entrepreneurs, small marketing teams)

**Test Scenarios:**
- **First-Time User Flow:** Navigate to pipeline, submit prompt, interact with story/scene breakpoints, download final video
- **CLI Execution:** Install CLI, authenticate, run generation with brand assets, verify output
- **Navigation Safety:** Start generation, navigate away, return, verify session restored
- **Error Recovery:** Disconnect WiFi during generation, reconnect, verify WebSocket auto-reconnect
- **Quality Score Visibility:** Verify VBench scores stream in during background processing, UI remains responsive
- **A/B Testing:** Generate 3 variants with different hooks, compare quality scores

**Success Criteria:**
- Users successfully generate professional-quality videos (<10 min total time)
- No critical bugs (data loss, crashes, WebSocket errors)
- Positive feedback on ChatGPT-style interface and 2-breakpoint interaction model

### Test Execution Strategy

**Development:** Run unit tests on every commit (pytest, vitest)
**Pre-Commit:** Run linters (ruff, eslint), type checkers (mypy, tsc --noEmit)
**CI/CD:** Run full test suite (unit + integration + frontend) on every pull request
**Pre-Deployment:** Run performance tests, load tests, manual UAT
**Post-Deployment:** Smoke tests (health check, sample generation), monitor for errors

### Test Data Strategy

**Mock Data:** Use pytest fixtures for database records (users, generations, quality_metrics)
**Test Prompts:** 5-10 representative prompts (product ads, service ads, various industries)
**Test Brand Assets:** 3-5 sample product images, logos, character images for reference stage testing
**Performance Data:** Generate 100+ test generations to populate database for query performance testing

### Known Test Gaps (Acceptable for MVP)

- **Cross-Browser Testing:** Manual testing in Chrome/Firefox/Safari only (no automated cross-browser suite)
- **VBench Scoring Tests:** Mocked until VBench library available (placeholder implementation for testing)
- **Load Testing:** Limited to 50 concurrent users (adequate for MVP, scale testing post-launch)
- **Accessibility Testing:** Automated axe-core tests only, no full screen reader testing (WCAG Level A target)
