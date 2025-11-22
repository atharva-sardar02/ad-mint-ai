# API Contracts - Ad Mint AI Pipelines

**Generated:** 2025-11-22
**Purpose:** Document all 4 video generation pipelines and their API endpoints

---

## Overview

Ad Mint AI currently has **4 working video generation pipelines**, each with different strengths and trade-offs:

1. **Master Mode Pipeline** - Best consistency, 3 ref images, hardcoded
2. **Interactive Pipeline** - User feedback/iteration, lacks consistency
3. **Original Pipeline** - Has quality scoring, mostly deprecated
4. **CLI Tools** - Standalone command-line interface

---

## 1. Master Mode Pipeline

**Status:** ⭐ Best consistency (3 reference images approach)
**Location:** `backend/app/api/routes/master_mode.py`, `backend/app/services/master_mode/`
**Base Path:** `/api/master-mode`

### Key Features
- **3 Reference Images:** Upload up to 3 images for visual consistency across characters/products
- **Two-Agent Story System:** Story Director + Story Critic iteratively refine story
- **Three-Agent Scene System:** Scene Writer + Scene Critic + Scene Cohesor create detailed scenes
- **Progress Streaming:** Real-time progress updates via queue system
- **LLM Conversation History:** Full visibility into agent discussions
- **Vision-Enhanced AI:** Analyzes reference images to maintain consistency

### Endpoints

#### POST /api/master-mode/generate-story

Generate a complete video ad story (and optionally scenes + videos) using the master mode pipeline.

**Request:**
```typescript
{
  prompt: string;                    // User prompt for the advertisement
  title?: string;                    // Optional video title
  brand_name?: string;               // Optional brand name
  client_generation_id?: string;     // Client-provided generation ID
  reference_images: File[];          // Up to 3 reference images (multipart/form-data)
  max_iterations?: number;           // Max story iterations (default: 3)
  generate_scenes?: boolean;         // Whether to generate scenes (default: true)
  generate_videos?: boolean;         // Whether to generate videos (default: false)
}
```

**Response:**
```typescript
{
  success: boolean;
  generation_id: string;

  // Story Results
  story: string;                      // Final approved story
  approval_status: "approved" | "needs_revision";
  final_score: number;                // 0-100
  total_iterations: number;
  story_conversation_history: Array<{
    role: "director" | "critic";
    iteration: number;
    content: string;
    timestamp: string;
  }>;
  story_iterations: Array<{
    iteration: number;
    story_draft: string;
    critique: {
      approval_status: string;
      overall_score: number;
      critique: string;
      strengths: string[];
      improvements: string[];
      priority_fixes: string[];
    };
    timestamp: string;
  }>;

  // Scenes Results (if generate_scenes=true)
  scenes?: {
    total_scenes: number;
    cohesion_score: number;           // 0-100
    scenes: Array<{
      scene_number: number;
      content: string;
      iterations: number;
      approved: boolean;
      final_critique: { /* same structure as story critique */ };
    }>;
    cohesion_analysis: {
      overall_cohesion_score: number;
      pair_wise_analysis: Array<{
        from_scene: number;
        to_scene: number;
        transition_score: number;
        issues: string[];
        recommendations: string[];
      }>;
      global_issues: string[];
      scene_specific_feedback: Record<number, string>;
      consistency_issues: string[];
      overall_recommendations: string[];
    };
    conversation_history: any[];
    total_iterations: number;
  };

  // Video Generation Parameters (if generate_scenes=true)
  video_generation_params?: Array<{
    scene_number: number;
    prompt: string;
    // ... other generation params
  }>;

  // Final Video (if generate_videos=true)
  final_video_path?: string;         // URL to final stitched video
  video_generation_status?: "success" | "failed";
  scene_videos?: string[];            // URLs to individual scene videos
}
```

**Progress Updates:**
Real-time progress is streamed via the progress queue system (master_mode_progress.py):
- `init` - Initialization
- `upload` - Saving reference images
- `story` - Generating story with vision-enhanced AI
- `scenes` - Generating detailed scenes
- `video_params` - Preparing video generation parameters
- `videos` - Generating and stitching videos
- `complete` - Generation complete

### Agent System Architecture

```
Story Generation Flow:
┌─────────────────┐
│ Story Director  │───► Generates initial story draft
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Story Critic   │───► Evaluates story (score, strengths, improvements)
└────────┬────────┘
         │
         ▼ (iterates up to max_iterations)
┌─────────────────┐
│ Final Story     │───► Approved story (score >= threshold)
└─────────────────┘

Scene Generation Flow:
┌─────────────────┐
│  Scene Writer   │───► Generates detailed scene content for each scene
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Scene Critic   │───► Evaluates scene (visual detail, consistency)
└────────┬────────┘
         │
         ▼ (iterates per scene)
┌─────────────────┐
│  Scene Cohesor  │───► Analyzes transitions between all scenes
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Final Scenes    │───► Approved scenes with cohesion analysis
└─────────────────┘
```

### Database Model Used
- **Generation** model with special `framework="master_mode"`
- Stores: `llm_conversation_history`, `video_path`, `scene_plan`, etc.

---

## 2. Interactive Pipeline

**Status:** Has user feedback/iteration, lacks consistency (no ref images)
**Location:** `backend/app/api/routes/interactive_generation.py`, `backend/app/services/pipeline/interactive_pipeline.py`
**Base Path:** `/api/v1/interactive`
**Known Issues:** WebSocket errors when navigating away from `/interactive` URL

### Key Features
- **User Feedback Loops:** Iterative refinement at each stage
- **WebSocket Real-Time Updates:** Live progress streaming
- **Conversational Interface:** Chat-based feedback system
- **Stage-by-Stage Approval:** User approves or regenerates each stage
- **Image Inpainting:** Edit specific regions of generated images
- **Manual Reference Upload:** Optionally provide reference images

### Pipeline Stages

```
Flow: story → reference_image → storyboard → video → complete

1. Story Stage        - Generate narrative from prompt
2. Reference Image    - Generate or upload reference images (up to 3)
3. Storyboard        - Create visual storyboard frames
4. Video             - Generate final video
5. Complete          - Finished
```

### Endpoints

#### POST /api/v1/interactive/start

Start a new interactive pipeline session.

**Request:**
```typescript
{
  prompt: string;              // 10-5000 chars
  target_duration?: number;    // 9-60 seconds (default: 15)
  mode?: "interactive" | "auto"; // Default: interactive
  title?: string;              // Max 200 chars
}
```

**Response:**
```typescript
{
  session_id: string;
  user_id: string;
  status: "story" | "reference_image" | "storyboard" | "video" | "complete" | "error";
  current_stage: string;
  created_at: string;
  updated_at: string;
  outputs: Record<string, any>;
  conversation_history: Array<{
    role: "user" | "assistant";
    content: string;
    timestamp: string;
  }>;
}
```

#### GET /api/v1/interactive/{session_id}/status

Get lightweight session status (for polling).

**Response:**
```typescript
{
  session_id: string;
  status: string;
  current_stage: string;
  updated_at: string;
  has_output: boolean;
}
```

#### GET /api/v1/interactive/{session_id}

Get full session details including conversation history.

#### POST /api/v1/interactive/{session_id}/approve

Approve current stage and proceed to next.

**Request:**
```typescript
{
  stage: string;                  // Must match current session stage
  notes?: string;                 // Optional approval notes
  selected_indices?: number[];    // Optional - select specific outputs
}
```

**Response:**
```typescript
{
  session_id: string;
  approved_stage: string;
  next_stage: string;
  message: string;
}
```

#### POST /api/v1/interactive/{session_id}/regenerate

Regenerate current stage with feedback.

**Request:**
```typescript
{
  stage: string;
  feedback?: string;              // Feedback text
  modifications?: any;            // Structured modifications
}
```

**Response:**
```typescript
{
  session_id: string;
  stage: string;
  message: string;
  regenerated: boolean;
}
```

#### POST /api/v1/interactive/{session_id}/reference-images/upload

Upload manual reference images (during story stage).

**Request:** Multipart form-data with up to 3 JPG/PNG images (max 10MB each)

**Response:**
```typescript
{
  session_id: string;
  images: Array<{
    index: number;
    path: string;
    url: string;
    prompt: string;
    quality_score: number | null;
    source: "manual";
  }>;
  message: string;
}
```

#### POST /api/v1/interactive/{session_id}/inpaint

Inpaint/edit a specific region of an image.

**Request:**
```typescript
{
  image_id: number;              // Index of image to edit (0-based)
  mask_data: string;             // Base64-encoded mask
  prompt: string;                // Replacement content description
  negative_prompt?: string;      // What to avoid
}
```

**Response:**
```typescript
{
  session_id: string;
  edited_image_url: string;
  original_image_url: string;
  version: number;
  edit_history: string[];
  message: string;
}
```

### WebSocket Integration

Connect to `/ws/{session_id}` for real-time updates:

**Messages sent:**
- `stage_progress` - Progress within current stage
- `stage_complete` - Stage finished
- `stage_error` - Error occurred
- `conversation_update` - New conversation message

**Messages received:**
- User chat messages for feedback

---

## 3. Original Pipeline (Generations API)

**Status:** Mostly deprecated, keep quality scoring features
**Location:** `backend/app/api/routes/generations.py`, `backend/app/api/routes/generations_with_image.py`
**Base Path:** `/api/generations`

### Key Features (To Preserve)
- **Quality Metrics:** Image and video quality scoring
- **VBench Integration:** Automated quality control (planned)
- **Comparison Groups:** Parallel generation with A/B testing
- **Coherence Settings:** Seed control, latent reuse

### Endpoints (Selected)

#### POST /api/generations/generate

Create a new video generation (original pipeline).

**Request:**
```typescript
{
  prompt: string;
  framework?: "PAS" | "BAB" | "AIDA";
  duration?: number;              // 9-60 seconds
  aspect_ratio?: string;          // "9:16", "16:9", "1:1"
  title?: string;
  use_llm?: boolean;              // Enable LLM enhancement
  coherence_settings?: {
    use_seed_control?: boolean;
    use_latent_reuse?: boolean;
    use_ip_adapter?: boolean;
    seed_value?: number;
  };
}
```

#### POST /api/generations/generate/parallel

Create parallel generations for comparison.

**Request:**
```typescript
{
  base_prompt: string;
  variations: Array<{
    prompt?: string;              // If different prompt
    coherence_settings?: any;     // If testing settings
  }>;
  comparison_type: "settings" | "prompt";
}
```

#### GET /api/generations/{generation_id}/quality

Get quality metrics for a generation.

**Response:**
```typescript
{
  generation_id: string;
  metrics: {
    image_quality_score: number;  // 0-100
    video_quality_score: number;  // 0-100
    // ... other VBench metrics
  };
}
```

#### POST /api/generations/{generation_id}/cancel

Cancel an in-progress generation.

#### DELETE /api/generations/{generation_id}

Delete a generation and its associated files.

### Quality Metric Model

```python
class QualityMetric(Base):
    id: str
    generation_id: str (FK)
    scene_number: int | None
    metric_name: str              # "image_quality", "temporal_consistency", etc.
    metric_value: float
    model_name: str | None        # "vbench", "clip", etc.
    created_at: datetime
```

---

## 4. CLI Tools Pipeline

**Status:** Standalone command-line tools
**Location:** `backend/cli_tools/`
**Execution:** Direct Python scripts

### Available Tools

#### create_storyboard.py
Create a detailed storyboard from a prompt.

**Usage:**
```bash
python cli_tools/create_storyboard.py \
  --prompt "Your ad description" \
  --scenes 3 \
  --output storyboard.json
```

#### generate_images.py
Generate reference images from prompts.

**Usage:**
```bash
python cli_tools/generate_images.py \
  --prompt "Product shot of eco-friendly water bottle" \
  --count 3 \
  --model "flux-pro" \
  --output ./output/images/
```

#### generate_videos.py
Generate videos from prompts and reference images.

**Usage:**
```bash
python cli_tools/generate_videos.py \
  --prompts prompts.json \
  --reference-images ./ref/*.jpg \
  --model "kling-v1.5" \
  --output ./output/videos/
```

#### enhance_image_prompt.py
Enhance image generation prompts using LLM.

**Usage:**
```bash
python cli_tools/enhance_image_prompt.py \
  --input "simple prompt" \
  --output enhanced_prompt.txt
```

#### enhance_video_prompt.py
Enhance video generation prompts using LLM.

#### pipeline.py
Complete end-to-end pipeline orchestrator.

**Usage:**
```bash
python cli_tools/pipeline.py \
  --prompt "Your ad concept" \
  --reference-images ./refs/ \
  --output ./final_output/ \
  --full-pipeline  # story → images → videos → stitch
```

---

## Database Models Summary

### Generation Model

The primary model for all pipelines:

```python
class Generation:
    id: str (UUID)
    user_id: str (FK to User)
    title: str | None
    prompt: str
    duration: int = 15
    aspect_ratio: str = "9:16"
    status: str                       # "pending", "processing", "completed", "failed"
    progress: int                     # 0-100
    current_step: str | None
    video_path: str | None
    video_url: str | None
    thumbnail_url: str | None
    framework: str | None             # "PAS", "BAB", "AIDA", "master_mode"
    num_scenes: int | None
    generation_time_seconds: int | None
    cost: float | None
    error_message: str | None
    llm_specification: JSON | None    # LLM-generated spec
    scene_plan: JSON | None           # Scene breakdown
    llm_conversation_history: JSON | None  # Master mode agent conversations
    temp_clip_paths: JSON | None      # Array of scene video paths
    coherence_settings: JSON | None   # Seed, latent reuse settings
    seed_value: int | None
    cancellation_requested: bool = False
    model: str | None                 # "openai/sora-2", "kling-v1.5", etc.
    num_clips: int | None
    use_llm: bool = True
    generation_group_id: str | None (FK)  # For parallel comparisons
    parent_generation_id: str | None (FK) # For edited versions
    created_at: datetime
    completed_at: datetime | None
```

### GenerationGroup Model

For parallel generation comparisons:

```python
class GenerationGroup:
    id: str (UUID)
    user_id: str (FK)
    created_at: datetime
    comparison_type: "settings" | "prompt"

    # Relationships
    generations: List[Generation]
```

---

## Pipeline Comparison Matrix

| Feature | Master Mode | Interactive | Original | CLI Tools |
|---------|-------------|-------------|----------|-----------|
| **Consistency (3 ref images)** | ✅ Best | ❌ None | Partial | ✅ Supported |
| **User Feedback** | ❌ No | ✅ Full | ❌ No | ❌ No |
| **Interactivity** | ❌ Hardcoded | ✅ Iterative | ❌ One-shot | ❌ Scripted |
| **Quality Scores** | ❌ No | ❌ No | ✅ Yes | ❌ No |
| **Image Generation** | ❌ Must provide | ✅ Generates | ✅ Generates | ✅ Generates |
| **LLM Agent Chain** | ✅ Complex (5+ agents) | ✅ Basic | ✅ Basic | ✅ Available |
| **UI** | ✅ Stable | ⚠️ Buggy WebSocket | ✅ Stable | ❌ CLI only |
| **CLI Support** | ❌ No | ❌ No | ❌ No | ✅ Yes |
| **Video Stitching** | ✅ Automatic | ✅ Automatic | ✅ Automatic | ✅ Manual/Auto |
| **Progress Streaming** | ✅ Custom queue | ✅ WebSocket | ✅ Polling | ❌ No |

---

## Consolidation Goal: Unified Pipeline

### Target Features (From All Pipelines)

✅ **From Master Mode:**
- 3 reference image consistency approach
- Complex LLM agent chain (Director, Critic, Cohesor)
- Progress streaming system
- Vision-enhanced AI

✅ **From Interactive:**
- User feedback at each stage
- Conversational interface
- Stage-by-stage approval/regeneration
- Image inpainting
- Manual reference upload capability

✅ **From Original:**
- Quality score display (image + video metrics)
- Comparison groups for A/B testing
- Coherence settings (seed, latent reuse)

✅ **From CLI Tools:**
- Command-line execution option
- Standalone script capability
- Flexible orchestration

### Required Architecture Changes

1. **Unified API Gateway** - Single endpoint that routes to appropriate pipeline logic
2. **Flexible Reference System** - Support both provided and generated reference images
3. **WebSocket Stability** - Fix navigation bugs in interactive mode
4. **Consistent Agent System** - Standardize LLM agent communication
5. **Quality Integration** - Add quality scoring to master mode
6. **CLI + UI Support** - Dual execution mode (UI or command-line)
7. **Configuration-Driven** - Replace hardcoded logic with flexible config

---

## Authentication

All API endpoints (except health check) require JWT authentication:

**Header:**
```
Authorization: Bearer <jwt_token>
```

**Get Token:**
```http
POST /api/auth/login
{
  "username": "user",
  "password": "pass"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": "...", "username": "..." }
}
```

---

## Error Handling

### HTTP Status Codes

- **200 OK** - Success
- **201 Created** - Resource created (sessions)
- **202 Accepted** - Request accepted, processing asynchronously
- **400 Bad Request** - Invalid input
- **401 Unauthorized** - Missing/invalid auth token
- **403 Forbidden** - No access to resource
- **404 Not Found** - Resource doesn't exist
- **422 Unprocessable Entity** - Validation error
- **500 Internal Server Error** - Server error
- **503 Service Unavailable** - Health check failed

### Error Response Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": { /* optional additional info */ }
  }
}
```

---

## Rate Limiting

Currently not implemented globally. Individual endpoints may have limits:
- File uploads: Max 3 files, 10MB each
- Session polling: Recommended max 1 request/second

---

## Pagination

List endpoints support pagination:

**Query Parameters:**
- `limit` - Number of results (default: 20, max: 100)
- `offset` - Skip N results (default: 0)

**Response:**
```typescript
{
  items: T[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}
```
