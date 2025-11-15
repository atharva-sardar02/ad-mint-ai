# Epic Technical Specification: Video Generation Pipeline

Date: 2025-11-14
Author: BMad
Epic ID: 3
Status: Draft

---

## Overview

Epic 3 implements the complete AI-powered video generation pipeline that transforms a simple user text prompt into a professional-quality video advertisement. This epic encompasses the entire end-to-end workflow from prompt input through LLM enhancement, scene planning, video clip generation, text overlay addition, video stitching, audio layer integration, and final export. As outlined in the PRD (Section 11: AI Video Generation Pipeline), the system leverages OpenAI GPT-4 for intelligent prompt enhancement, Replicate API for video clip generation using state-of-the-art models (Runway Gen-3, Kling, Minimax), and MoviePy for video processing and composition. This epic is the core value proposition of the application, enabling users to create publication-ready video ads in minutes without any creative input beyond a simple text description. The pipeline implements proven advertising frameworks (PAS, BAB, AIDA) to ensure every generated video follows best practices for persuasive advertising narratives.

## Objectives and Scope

**In-Scope:**
- Dashboard component with prompt input form and client-side validation (10-500 characters)
- LLM enhancement service that sends user prompt to GPT-4/Claude and receives structured JSON with product description, brand guidelines, framework selection, and ad specifications
- Scene planning module that breaks video into 3-5 scenes based on selected framework (AIDA, PAS, BAB) with visual prompts, text overlays, and durations
- Video clip generation service using Replicate API to generate 3-7 second clips per scene
- Text overlay service using MoviePy to add styled text with brand colors, fonts, and animations
- Video stitching service that concatenates clips with crossfade transitions (0.5s) and fade in/out effects
- Audio layer service that adds background music (30% volume) and sound effects synchronized with video
- Post-processing service that applies color grading, exports final video (1080p MP4, H.264), and generates thumbnail
- Progress tracking that updates database with status and progress percentage at each pipeline stage
- Cost calculation service that tracks API costs per generation and updates user's total_cost field
- Best-effort cancellation functionality that allows users to request cancellation of in-progress generations
- Frontend progress UI that polls status endpoint every 2 seconds and displays real-time updates

**Out-of-Scope:**
- User-selectable video duration or aspect ratio (defaults to 15s and 9:16 for MVP)
- User-selectable framework (automatic selection only)
- Brand asset uploads (logos, custom fonts) (post-MVP)
- Scene regeneration or editing (post-MVP)
- Music generation (uses royalty-free library only)
- Voice-over generation (post-MVP)
- Multiple video variations (A/B testing) (post-MVP)
- True concurrent generation guarantees and request queuing (post-MVP)

## System Architecture Alignment

This epic implements the video generation pipeline orchestration described in the PRD (Section 11) and architecture document. The backend follows the synchronous orchestration pattern established in Epic 1, with a single orchestration function in `backend/app/services/pipeline/orchestrator.py` that coordinates all seven pipeline stages sequentially within a single FastAPI request handler. The architecture's decision to use synchronous processing for MVP aligns with the PRD's single-instance deployment model. The pipeline services are organized under `backend/app/services/pipeline/` as separate modules (llm_enhancement.py, scene_planning.py, video_generation.py, overlays.py, stitching.py, audio.py, export.py), following the architecture's modular service pattern. The frontend dashboard component (`frontend/src/routes/Dashboard.tsx`) implements the prompt input form and progress tracking UI, consistent with the architecture's React Router page-based structure. The Generation model from Epic 1 is used to track status, progress, and cost throughout the pipeline. The cost tracking service (`backend/app/services/cost_tracking.py`) updates the user's total_cost field atomically, ensuring data consistency as specified in the architecture document.

## Detailed Design

### Services and Modules

| Module/Service | Responsibility | Inputs | Outputs | Owner |
|----------------|----------------|--------|---------|-------|
| `backend/app/api/routes/generations.py` | Video generation endpoint (`POST /api/generate`), status endpoint (`GET /api/status/{id}`), cancel endpoint (`POST /api/generations/{id}/cancel`) | HTTP requests | HTTP responses with generation_id, status objects | Backend |
| `backend/app/services/pipeline/orchestrator.py` | Main pipeline orchestration function that coordinates all seven stages sequentially | User prompt, generation_id | Completed video file path | Backend |
| `backend/app/services/pipeline/llm_enhancement.py` | Sends prompt to GPT-4/Claude, validates response with Pydantic, returns structured JSON | User prompt (string) | AdSpecification JSON (product description, brand guidelines, framework, scenes) | Backend |
| `backend/app/services/pipeline/scene_planning.py` | Processes LLM output, selects framework-specific scene structure, generates enriched visual prompts | AdSpecification JSON | ScenePlan JSON (scenes array with visual prompts, text overlays, durations) | Backend |
| `backend/app/services/pipeline/video_generation.py` | Calls Replicate API for each scene, downloads clips to temp storage, tracks costs | ScenePlan JSON | List of video clip file paths | Backend |
| `backend/app/services/pipeline/overlays.py` | Adds text overlays to video clips using MoviePy with brand styling | Video clip path, text overlay specification | Video clip with text overlay | Backend |
| `backend/app/services/pipeline/stitching.py` | Concatenates clips with transitions, applies fade in/out | List of video clip paths | Single stitched video file | Backend |
| `backend/app/services/pipeline/audio.py` | Selects music from library, trims to video duration, adds sound effects | Stitched video path, music style | Video with audio track | Backend |
| `backend/app/services/pipeline/export.py` | Applies color grading, exports final video (1080p MP4), generates thumbnail | Video with audio | Final video file path, thumbnail path | Backend |
| `backend/app/services/cost_tracking.py` | Tracks API costs at each stage, calculates total cost, updates user.total_cost | Generation record, cost per stage | Updated user.total_cost | Backend |
| `backend/app/services/cancellation.py` | Handles cancellation requests, sets cancellation flag, updates generation status | Generation ID | Updated generation status | Backend |
| `frontend/src/routes/Dashboard.tsx` | Main dashboard page with prompt input form, progress display, cancel button | User input | Form submission, progress UI | Frontend |
| `frontend/src/components/ProgressBar.tsx` | Progress bar component that displays status and progress percentage | Progress data | Progress bar UI | Frontend |
| `frontend/src/lib/generationService.ts` | API service functions for generation (start, status, cancel) | Prompt, generation_id | API responses | Frontend |

### Data Models and Contracts

**Generation Model (from Epic 1, extended in Epic 3):**
```python
class Generation(Base):
    __tablename__ = "generations"
    
    # ... fields from Epic 1 ...
    
    # Epic 3 additions:
    llm_specification = Column(JSON, nullable=True)  # LLM output JSON
    scene_plan = Column(JSON, nullable=True)  # Scene breakdown JSON
    temp_clip_paths = Column(JSON, nullable=True)  # Array of temp file paths
    cancellation_requested = Column(Boolean, default=False)  # Cancellation flag
```

**Pydantic Request Schemas (`backend/app/schemas/generation.py`):**
```python
class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=10, max_length=500)

class StatusResponse(BaseModel):
    generation_id: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    current_step: Optional[str]
    video_url: Optional[str]
    cost: Optional[float]
    error: Optional[str]
```

**Pydantic LLM Response Schema:**
```python
class AdSpecification(BaseModel):
    product_description: str
    brand_guidelines: BrandGuidelines
    ad_specifications: AdSpec
    framework: str  # "PAS", "BAB", or "AIDA"
    scenes: List[Scene]

class BrandGuidelines(BaseModel):
    brand_name: str
    brand_colors: List[str]  # Hex colors
    visual_style_keywords: str
    mood: str

class Scene(BaseModel):
    scene_number: int
    scene_type: str  # Framework-specific type
    visual_prompt: str
    text_overlay: TextOverlay
    duration: int  # seconds
```

### APIs and Interfaces

**Backend API Endpoints:**

| Method | Path | Description | Request Body | Response | Status Codes |
|--------|------|-------------|--------------|----------|--------------|
| POST | `/api/generate` | Start video generation from prompt | `GenerateRequest` | `{"generation_id": "...", "status": "pending"}` | 202, 401, 422 |
| GET | `/api/status/{generation_id}` | Get generation progress and status | - | `StatusResponse` | 200, 401, 404 |
| POST | `/api/generations/{id}/cancel` | Request cancellation of in-progress generation | - | `StatusResponse` | 202, 401, 404 |

**Request/Response Examples:**

**Start Generation:**
```json
// Request
POST /api/generate
Headers: Authorization: Bearer {jwt_token}
{
  "prompt": "Create a luxury watch ad for Instagram"
}

// Response (202 Accepted)
{
  "generation_id": "abc-123-def-456",
  "status": "pending",
  "message": "Video generation started"
}
```

**Get Status:**
```json
// Request
GET /api/status/abc-123-def-456
Headers: Authorization: Bearer {jwt_token}

// Response (200 OK) - Processing
{
  "generation_id": "abc-123-def-456",
  "status": "processing",
  "progress": 45,
  "current_step": "Generating video clip 2 of 3",
  "video_url": null,
  "cost": null,
  "error": null
}

// Response (200 OK) - Completed
{
  "generation_id": "abc-123-def-456",
  "status": "completed",
  "progress": 100,
  "current_step": "Complete",
  "video_url": "/output/videos/abc-123-def-456.mp4",
  "cost": 1.87,
  "error": null
}
```

**Cancel Generation:**
```json
// Request
POST /api/generations/abc-123-def-456/cancel
Headers: Authorization: Bearer {jwt_token}

// Response (202 Accepted)
{
  "generation_id": "abc-123-def-456",
  "status": "failed",
  "progress": 45,
  "current_step": "Cancelled",
  "video_url": null,
  "cost": 0.0,
  "error": "Cancelled by user"
}
```

**Frontend API Service Interface:**
```typescript
// frontend/src/lib/generationService.ts
export const generationService = {
  startGeneration: async (prompt: string) => {
    return apiClient.post('/api/generate', { prompt });
  },
  
  getStatus: async (generationId: string) => {
    return apiClient.get(`/api/status/${generationId}`);
  },
  
  cancelGeneration: async (generationId: string) => {
    return apiClient.post(`/api/generations/${generationId}/cancel`);
  }
};
```

### Workflows and Sequencing

**Video Generation Pipeline Workflow:**
1. User submits prompt on dashboard (10-500 characters)
2. Frontend validates prompt length, sends POST `/api/generate`
3. Backend creates Generation record with `status=pending`, `progress=0`
4. Backend updates `status=processing`, `progress=10%`, `current_step="LLM Enhancement"`
5. LLM Enhancement: Send prompt to GPT-4, receive AdSpecification JSON, validate with Pydantic
6. Backend updates `progress=20%`, `current_step="Scene Planning"`
7. Scene Planning: Process AdSpecification, select framework, generate ScenePlan with 3-5 scenes
8. Backend updates `progress=30%`, `current_step="Generating video clip 1 of N"`
9. Video Generation: For each scene, call Replicate API, download clip to temp storage
10. Backend updates progress incrementally (30-70% based on scene count)
11. Backend updates `progress=70%`, `current_step="Adding text overlays"`
12. Text Overlays: For each clip, add text overlay using MoviePy with brand styling
13. Backend updates `progress=80%`, `current_step="Stitching video clips"`
14. Video Stitching: Concatenate clips with crossfade transitions, apply fade in/out
15. Backend updates `progress=90%`, `current_step="Adding audio layer"`
16. Audio Layer: Select music from library, trim to duration, add sound effects, composite audio
17. Backend updates `progress=95%`, `current_step="Post-processing and export"`
18. Post-Processing: Apply color grading, export final video (1080p MP4), generate thumbnail
19. Backend updates `status=completed`, `progress=100%`, `video_url`, `cost`, `completed_at`
20. Cost Tracking: Calculate total cost, update user.total_cost atomically
21. Frontend polls status endpoint every 2 seconds, displays progress updates
22. When status=completed, frontend displays video player and download button

**Cancellation Workflow:**
1. User clicks cancel button on dashboard
2. Frontend sends POST `/api/generations/{id}/cancel`
3. Backend sets `cancellation_requested=True` on Generation record
4. Backend checks cancellation flag at start of each pipeline stage
5. If flag is True, stop processing, update `status=failed`, `error="Cancelled by user"`
6. Clean up temp files, return cancellation response
7. Frontend updates UI to show cancelled state

## Non-Functional Requirements

### Performance

**NFR-3.1: Video Generation Speed**
- Target: 15-second video generates in <3 minutes (target: 2 minutes) (PRD Section 9.1, NFR-001)
- Measurement: Time from POST `/api/generate` to `status=completed`
- Pipeline Breakdown Targets:
  - LLM enhancement: 5-10 seconds
  - Scene planning: 2 seconds
  - Video generation (3 clips): 60-90 seconds
  - Text overlay: 5 seconds per clip
  - Stitching: 10 seconds
  - Audio layer: 5 seconds
  - Export: 15 seconds
- Implementation: Optimize API calls, use fastest viable models (Minimax for MVP), parallel clip generation if API allows
- Source: PRD Section 9.1 (Generation Speed)

**NFR-3.2: Status Endpoint Response Time**
- Target: `/api/status/{id}` responds in <200ms (PRD Section 9.1, NFR-002)
- Measurement: Average response time over 100 requests
- Implementation: Indexed database query on generation_id, minimal data returned
- Source: PRD Section 9.1 (API Response Time)

**NFR-3.3: Frontend Progress Polling**
- Target: Progress updates displayed within 2 seconds of backend state change
- Measurement: Time from backend progress update to frontend display
- Implementation: Frontend polls `/api/status/{id}` every 2 seconds, efficient React state updates
- Source: PRD Section 7.1 (User Stories - Progress Tracking)

**NFR-3.4: Video File Size**
- Target: 15-second video file size <50MB (PRD Section 11.8)
- Measurement: File size of exported MP4
- Implementation: Optimize FFmpeg encoding settings (H.264, appropriate bitrate), compression settings
- Source: PRD Section 11.8 (Final Export)

### Security

**NFR-3.5: API Key Protection**
- Requirement: Replicate and OpenAI API keys stored in backend `.env` only, never exposed to frontend (PRD Section 16.4, NFR-010)
- Implementation: Environment variables loaded in backend config, validated on startup
- Validation: Verify API keys not in frontend code, not in client-side JavaScript
- Source: PRD Section 16.4 (API Keys)

**NFR-3.6: User Authorization**
- Requirement: Users can only access their own generation status and videos (PRD Section 16.2, NFR-010)
- Implementation: JWT token verification in status endpoint, check `generation.user_id == current_user.id`
- Validation: Test unauthorized access attempts, verify 403 Forbidden response
- Source: PRD Section 16.2 (Authorization)

**NFR-3.7: Input Validation**
- Requirement: Prompt input validated and sanitized (10-500 characters, no scripts) (PRD Section 16.3, NFR-011)
- Implementation: Pydantic schema validation, HTML/script sanitization
- Validation: Test with XSS attempts, SQL injection attempts, verify sanitization
- Source: PRD Section 16.3 (Input Validation)

**NFR-3.8: Rate Limiting**
- Requirement: 10 video generations per user per hour (PRD Section 16.2, NFR-011)
- Implementation: Rate limiting middleware, track generation count per user per hour
- Validation: Test with 11 rapid requests, verify 429 Too Many Requests response
- Source: PRD Section 16.2 (API Rate Limiting)

### Reliability/Availability

**NFR-3.9: Video Generation Success Rate**
- Requirement: >90% success rate (PRD Section 9.2, NFR-004)
- Measurement: Percentage of generations that complete successfully (status=completed)
- Implementation: Automatic retry for transient failures (up to 3 attempts), fallback to alternative video models, clear error messages for permanent failures
- Source: PRD Section 9.2 (Success Rate)

**NFR-3.10: Error Handling and Recovery**
- Requirement: Transient API failures handled gracefully with retry logic (PRD Section 9.2, NFR-004)
- Implementation: Retry logic for Replicate API calls (exponential backoff, max 3 attempts), fallback to alternative models (Kling if Minimax fails)
- Validation: Test with simulated API failures, verify retry behavior and fallback
- Source: PRD Section 9.2 (Success Rate)

**NFR-3.11: Temp File Cleanup**
- Requirement: Temporary video files cleaned up after generation completes or fails (PRD Section 9.3, NFR-008)
- Implementation: Cleanup temp files in finally block, scheduled cleanup job for orphaned files (1 day retention)
- Validation: Verify temp files deleted after completion, verify cleanup job runs
- Source: PRD Section 9.3 (Storage Management)

**NFR-3.12: Database Transaction Integrity**
- Requirement: Generation status updates and cost tracking use database transactions (Architecture document)
- Implementation: SQLAlchemy session.commit() with rollback on error, atomic user.total_cost updates
- Validation: Test concurrent updates, verify no partial data
- Source: Architecture document (database patterns)

### Observability

**NFR-3.13: Pipeline Stage Logging**
- Requirement: All pipeline stages log with structured format (level, message, timestamp, generation_id) (PRD Section 9.6, NFR-017)
- Implementation: Python logging module, log at INFO level for stage transitions, WARNING for retries, ERROR for failures
- Log Format: `{"event": "pipeline_stage", "stage": "llm_enhancement", "generation_id": "...", "timestamp": "..."}`
- Source: PRD Section 9.6 (Logging)

**NFR-3.14: Cost Tracking Logging**
- Requirement: All API costs logged with generation_id and cost breakdown (PRD Section 9.6, NFR-017)
- Implementation: Log cost per stage (LLM cost, video generation cost), log total cost on completion
- Log Format: `{"event": "cost_tracked", "generation_id": "...", "llm_cost": 0.01, "video_cost": 0.75, "total_cost": 0.76}`
- Source: PRD Section 9.6 (Logging)

**NFR-3.15: Error Logging**
- Requirement: All generation failures logged with error details and stack traces (PRD Section 9.6, NFR-017)
- Implementation: Log at ERROR level with full exception details, include generation_id and stage
- Log Format: `{"event": "generation_failed", "generation_id": "...", "stage": "video_generation", "error": "...", "stack_trace": "..."}`
- Source: PRD Section 9.6 (Logging)

**NFR-3.16: Progress Tracking Visibility**
- Requirement: Progress updates visible to users in real-time (PRD Section 7.1)
- Implementation: Frontend polls status endpoint every 2 seconds, displays progress bar and current step
- Validation: Verify progress updates appear within 2 seconds of backend state change
- Source: PRD Section 7.1 (User Stories - Progress Tracking)

## Dependencies and Integrations

**Backend Dependencies (New for Epic 3):**
- `openai` 1.0+ (OpenAI API client for GPT-4 LLM enhancement)
- `replicate` 0.22+ (Replicate Python SDK for video generation API)
- `moviepy` 1.0.3+ (Video editing library for text overlays, stitching, audio, export)
- `opencv-python` 4.8+ (Image/video processing for color grading and effects)
- `pillow` 10.1+ (Image manipulation for thumbnail generation)
- `pydub` 0.25+ (Audio processing library)
- `ffmpeg-python` 0.2+ (FFmpeg wrapper for video encoding) OR system FFmpeg binary

**Backend Dependencies (From Epic 1-2, Used Here):**
- FastAPI 0.104+ (Web framework for API endpoints)
- SQLAlchemy 2.0+ (ORM for Generation model updates)
- Pydantic 2.0+ (Request/response validation, LLM response schemas)
- PyJWT 2.8+ (JWT authentication for protected endpoints)

**Frontend Dependencies (From Epic 1-2, Used Here):**
- React 18.2+ (Dashboard UI components)
- TypeScript 5.0+ (Type safety for API calls)
- Axios 1.6+ (HTTP client for API requests)
- React Router 6+ (Dashboard route)
- Zustand 4.4+ (State management for generation status)

**External Services:**
- **OpenAI API** (GPT-4 for LLM enhancement)
  - Endpoint: `https://api.openai.com/v1/chat/completions`
  - Authentication: API key from environment variable `OPENAI_API_KEY`
  - Cost: ~$0.01 per generation (PRD Section 18.1)
- **Replicate API** (Video generation models)
  - Endpoint: `https://api.replicate.com/v1/predictions`
  - Authentication: API token from environment variable `REPLICATE_API_TOKEN`
  - Models: Minimax Video-01 (primary), Runway Gen-3 Alpha Turbo, Kling 1.5 (fallback)
  - Cost: ~$0.05 per second of video (PRD Section 18.1)
- **Music Library** (Royalty-free background music)
  - Local storage: `/backend/assets/music/` directory
  - Format: MP3 files categorized by mood/style
  - No external API required (local files)

**System Dependencies (EC2):**
- FFmpeg (Video encoding/decoding, required by MoviePy)
- Python 3.11+ (Backend runtime)
- Node.js 18+ (Frontend build, already installed in Epic 1)

**Version Constraints:**
- OpenAI API: Use GPT-4 model (gpt-4 or gpt-4-turbo)
- Replicate API: Use latest stable model versions (check Replicate docs for current versions)
- MoviePy: Requires FFmpeg system binary, version 4.4+ recommended
- All Python dependencies should use exact versions or version ranges in `requirements.txt`

**Integration Points:**
- Epic 1: Uses Generation model and database schema, API infrastructure
- Epic 2: Uses JWT authentication for protected endpoints
- Epic 4: Provides video files and metadata for gallery display
- Epic 5: Provides cost data for user profile statistics

**API Rate Limits:**
- OpenAI API: Rate limits vary by tier (check OpenAI dashboard)
- Replicate API: Rate limits vary by account tier (check Replicate dashboard)
- Implementation: Handle 429 Too Many Requests with exponential backoff retry

## Acceptance Criteria (Authoritative)

**AC-3.1.1: Prompt Input Validation**
- **Given** I am on the dashboard
- **When** I enter a prompt and submit
- **Then** the system validates prompt length (10-500 characters)
- **And** invalid prompts show error message
- **And** valid prompts trigger video generation

**AC-3.1.2: LLM Enhancement**
- **Given** a user prompt
- **When** the LLM enhancement service processes it
- **Then** it sends prompt to GPT-4 API
- **And** receives structured JSON with product description, brand guidelines, framework selection, and ad specifications
- **And** validates response with Pydantic schema
- **And** returns AdSpecification object

**AC-3.1.3: Scene Planning**
- **Given** LLM-generated ad specification with framework
- **When** the scene planning module processes it
- **Then** it generates scene breakdown with 3-5 scenes
- **And** each scene has visual prompt, text overlay, and duration
- **And** scene structure matches selected framework (AIDA, PAS, or BAB)
- **And** total duration matches target (15s, 30s, or 60s)

**AC-3.2.1: Video Clip Generation**
- **Given** a scene with visual prompt and duration
- **When** the video generation service processes it
- **Then** it calls Replicate API with visual prompt
- **And** generates a video clip (3-7 seconds)
- **And** downloads clip to temp storage
- **And** tracks API cost per clip

**AC-3.2.2: Text Overlay Addition**
- **Given** a video clip and text overlay specification
- **When** the text overlay service processes it
- **Then** it adds styled text to the video clip
- **And** text uses brand colors and fonts
- **And** text positioning matches specification (top, center, or bottom)
- **And** text animation is applied (fade in, slide up)

**AC-3.2.3: Multiple Clip Generation**
- **Given** multiple scenes in scene plan
- **When** video generation processes all scenes
- **Then** clips are generated sequentially (or in parallel if API allows)
- **And** each clip matches scene duration specification
- **And** all clips use same aspect ratio (9:16 for MVP)

**AC-3.3.1: Video Stitching**
- **Given** multiple video clips with text overlays
- **When** the video stitching service processes them
- **Then** it concatenates clips in sequence
- **And** applies crossfade transitions (0.5s) between clips
- **And** adds fade in at start (0.3s) and fade out at end (0.3s)
- **And** maintains consistent frame rate (24-30 fps)

**AC-3.3.2: Audio Layer**
- **Given** a stitched video and music style specification
- **When** the audio layer service processes it
- **Then** it selects background music from library based on style
- **And** trims music to video duration
- **And** adjusts music volume to 30%
- **And** adds sound effects at scene transitions
- **And** composites audio (music + SFX) and attaches to video

**AC-3.3.3: Post-Processing and Export**
- **Given** a video with audio
- **When** the post-processing service processes it
- **Then** it applies color grading based on brand style
- **And** exports final video as 1080p MP4 (H.264 codec)
- **And** generates thumbnail from first frame
- **And** saves video to permanent storage (`/output/videos/`)
- **And** updates database with video_url and thumbnail_url

**AC-3.3.4: Final Video Quality**
- **Given** a completed video generation
- **When** I examine the final video
- **Then** total duration matches sum of scene durations (accounting for transitions)
- **And** frame rate is consistent (24 fps default)
- **And** resolution is 1080p minimum
- **And** file size is reasonable (<50MB for 15s video)
- **And** video plays correctly in HTML5 video players

**AC-3.4.1: Progress Tracking**
- **Given** I have started a video generation
- **When** I check the generation status
- **Then** I see current status (pending, processing, completed, failed)
- **And** progress percentage (0-100)
- **And** current step description
- **And** progress updates occur at: 10% (LLM), 20% (Scene Planning), 30-70% (Video Generation), 80% (Stitching), 90% (Audio), 100% (Complete)

**AC-3.4.2: Cost Calculation**
- **Given** a video generation completes
- **When** the cost calculation service processes it
- **Then** it calculates total cost (LLM + video generation API costs)
- **And** stores cost per generation in database
- **And** updates user's total_cost field atomically

**AC-3.4.3: Cancel Generation**
- **Given** I have a video generation in progress
- **When** I click the cancel button
- **Then** the system sets cancellation_requested flag
- **And** checks flag at start of each pipeline stage
- **And** stops processing if flag is True
- **And** updates status to failed with error="Cancelled by user"
- **And** cleans up temp files

**AC-3.4.4: Frontend Progress Display**
- **Given** I am on the dashboard with an active generation
- **When** the frontend polls status endpoint
- **Then** progress bar updates every 2 seconds
- **And** current step description is displayed
- **And** cancel button is available during processing
- **And** video player appears when status=completed

## Traceability Mapping

| AC ID | Spec Section | Component(s)/Module(s) | Test Idea |
|-------|--------------|------------------------|-----------|
| AC-3.1.1 | APIs and Interfaces | `frontend/src/routes/Dashboard.tsx` (prompt form) | Enter prompts of various lengths, verify validation |
| AC-3.1.2 | Services and Modules | `backend/app/services/pipeline/llm_enhancement.py` | Mock OpenAI API, verify JSON structure and validation |
| AC-3.1.3 | Services and Modules | `backend/app/services/pipeline/scene_planning.py` | Test with different frameworks, verify scene structure |
| AC-3.2.1 | Services and Modules | `backend/app/services/pipeline/video_generation.py` | Mock Replicate API, verify clip generation and download |
| AC-3.2.2 | Services and Modules | `backend/app/services/pipeline/overlays.py` | Test text overlay with various styles and positions |
| AC-3.2.3 | Workflows and Sequencing | `backend/app/services/pipeline/video_generation.py` | Test multiple scenes, verify sequential/parallel generation |
| AC-3.3.1 | Services and Modules | `backend/app/services/pipeline/stitching.py` | Test video concatenation with transitions |
| AC-3.3.2 | Services and Modules | `backend/app/services/pipeline/audio.py` | Test music selection, trimming, volume adjustment |
| AC-3.3.3 | Services and Modules | `backend/app/services/pipeline/export.py` | Test color grading, export settings, thumbnail generation |
| AC-3.3.4 | Non-Functional Requirements | `backend/app/services/pipeline/export.py` | Verify video properties (duration, resolution, file size) |
| AC-3.4.1 | Workflows and Sequencing | `backend/app/api/routes/generations.py` (status endpoint) | Test progress updates at each stage |
| AC-3.4.2 | Services and Modules | `backend/app/services/cost_tracking.py` | Test cost calculation and user.total_cost update |
| AC-3.4.3 | Services and Modules | `backend/app/services/cancellation.py` | Test cancellation flag and cleanup |
| AC-3.4.4 | Services and Modules | `frontend/src/routes/Dashboard.tsx`, `frontend/src/components/ProgressBar.tsx` | Test polling, progress display, cancel button |

## Risks, Assumptions, Open Questions

**Risk-3.1: Video Generation API Failures**
- **Risk:** Replicate API may fail or return low-quality videos, causing generation failures
- **Impact:** High (user frustration, poor experience)
- **Mitigation:** Implement retry logic (up to 3 attempts), fallback to alternative models (Kling if Minimax fails), clear error messages
- **Status:** Mitigated - retry and fallback logic specified

**Risk-3.2: High API Costs**
- **Risk:** Video generation costs may exceed $2 per video target, making product unprofitable
- **Impact:** High (budget overrun, unprofitable product)
- **Mitigation:** Use cheapest viable models (Minimax for MVP), monitor costs daily, implement strict rate limiting (10 videos/hour per user)
- **Status:** Mitigated - cost targets specified, rate limiting implemented

**Risk-3.3: Long Generation Times**
- **Risk:** Video generation may take >5 minutes, exceeding user expectations
- **Impact:** Medium (user dissatisfaction)
- **Mitigation:** Optimize API calls, use fastest models, parallel clip generation if API allows, set clear expectations in UI
- **Status:** Mitigated - performance targets specified (<3 minutes for 15s video)

**Risk-3.4: LLM Response Quality**
- **Risk:** GPT-4 may generate inconsistent or low-quality ad specifications
- **Impact:** Medium (poor video quality, user dissatisfaction)
- **Mitigation:** Refine system prompts, validate responses with Pydantic schemas, test extensively with diverse prompts
- **Status:** Open - requires testing and prompt engineering iteration

**Risk-3.5: MoviePy Performance**
- **Risk:** MoviePy video processing may be slow or memory-intensive for multiple clips
- **Impact:** Medium (slow generation, memory issues)
- **Mitigation:** Optimize MoviePy settings, use efficient encoding options, monitor memory usage, consider FFmpeg direct calls if needed
- **Status:** Open - requires performance testing

**Risk-3.6: Storage Capacity**
- **Risk:** Video files may fill up disk storage quickly
- **Impact:** Medium (failed saves, system downtime)
- **Mitigation:** Auto-delete temp files after completion, implement video retention policy (30 days), monitor disk usage
- **Status:** Mitigated - cleanup strategy specified

**Assumption-3.1: FFmpeg Availability**
- **Assumption:** FFmpeg is installed on EC2 instance and accessible to MoviePy
- **Validation:** Deployment script should verify FFmpeg installation, test MoviePy functionality
- **Status:** Documented - FFmpeg required system dependency

**Assumption-3.2: Music Library**
- **Assumption:** Royalty-free music library exists in `/backend/assets/music/` directory with files categorized by mood/style
- **Validation:** Music library must be created before Epic 3 implementation, test music selection logic
- **Status:** Open - music library creation required

**Assumption-3.3: API Key Availability**
- **Assumption:** OpenAI and Replicate API keys are available and have sufficient quota
- **Validation:** Verify API keys in environment variables, test API connectivity on startup
- **Status:** Documented - API keys required

**Question-3.1: Parallel Clip Generation**
- **Question:** Should we generate video clips in parallel or sequentially?
- **Decision:** Attempt parallel generation if Replicate API supports it, fallback to sequential if rate limits or API constraints prevent parallelization
- **Status:** Resolved - parallel preferred, sequential fallback

**Question-3.2: Framework Selection Accuracy**
- **Question:** How accurate is LLM framework selection? Should we allow manual override?
- **Decision:** For MVP, trust LLM selection. Manual override can be added post-MVP if needed.
- **Status:** Resolved - automatic selection for MVP

**Question-3.3: Cancellation Granularity**
- **Question:** How granular should cancellation be? Can we cancel mid-clip generation?
- **Decision:** Best-effort cancellation checks at start of each pipeline stage. Cannot cancel mid-API call, but will stop before next stage.
- **Status:** Resolved - best-effort cancellation at stage boundaries

## Test Strategy Summary

**Unit Tests (Backend):**
- Test LLM enhancement service with mocked OpenAI API responses
- Test scene planning with different frameworks (AIDA, PAS, BAB)
- Test video generation service with mocked Replicate API
- Test text overlay service with various styles and positions
- Test video stitching with multiple clips and transitions
- Test audio layer service with music selection and trimming
- Test export service with color grading and encoding settings
- Test cost tracking service with various cost scenarios
- Test cancellation service with cancellation flag logic
- Test Pydantic schema validation for LLM responses

**Unit Tests (Frontend):**
- Test Dashboard component prompt form validation
- Test ProgressBar component with various progress states
- Test generationService API calls (start, status, cancel)
- Test polling logic (2-second intervals)
- Test error handling and display

**Integration Tests:**
- Test complete pipeline flow (prompt → completed video)
- Test status endpoint updates throughout pipeline
- Test progress tracking at each stage
- Test cost calculation and user.total_cost update
- Test cancellation flow (request → stop → cleanup)
- Test error handling and retry logic
- Test fallback to alternative video models

**End-to-End Tests:**
- Test user submits prompt → video generates → video plays correctly
- Test progress updates appear in real-time
- Test cancellation works during generation
- Test error handling displays user-friendly messages

**Performance Tests:**
- Test generation time for 15-second video (<3 minutes target)
- Test status endpoint response time (<200ms target)
- Test progress polling overhead (2-second intervals)
- Test video file size (<50MB for 15s video)

**Manual Testing:**
- Test with diverse prompts (luxury products, tech products, lifestyle products)
- Test with different frameworks (verify LLM selects appropriate framework)
- Test video quality (visual coherence, audio sync, text readability)
- Test error scenarios (API failures, network issues, invalid prompts)
- Test cancellation at various stages
- Test concurrent generations (if multiple users)

**Test Coverage Goals:**
- Backend: 80%+ coverage for pipeline services
- Frontend: 70%+ coverage for dashboard and progress components
- Integration: All critical user flows covered
- Performance: All NFR targets validated

**Test Frameworks:**
- Backend: pytest with FastAPI TestClient, mocking for external APIs
- Frontend: Vitest with React Testing Library
- E2E: Manual testing for MVP (can add Playwright/Cypress post-MVP)

