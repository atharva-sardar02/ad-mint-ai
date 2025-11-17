# Professional Workflow Implementation Plan
## Enabling Iterative AI Video Creation with Human-in-the-Loop

**Date:** 2025-01-XX  
**Status:** Planning  
**Goal:** Transform current product to support professional creator workflow: TEXT → PHOTO → VIDEO with automated feedback loops and iterative refinement

---

## Executive Summary

This plan outlines the implementation of a professional-grade video generation workflow that:
1. **Generates hero frames first** (TEXT → PHOTO) before video generation
2. **Supports image-to-video** workflow using polished hero frames
3. **Automates quality assessment** using VBench (3 auto-attempts)
4. **Enables human-in-the-loop refinement** after automated attempts
5. **Provides iterative refinement UI** for prompt tweaking and regeneration
6. **Integrates LLM feedback** for prompt improvement suggestions

---

## Current State vs. Target State

### Current State
- ✅ LLM enhancement for prompt improvement
- ✅ Scene planning with frameworks (PAS, BAB, AIDA)
- ✅ Video generation via Replicate (text-to-video)
- ✅ VBench quality control (implemented)
- ✅ Automatic regeneration (2 attempts)
- ❌ No image generation phase
- ❌ No image-to-video workflow
- ❌ Limited iterative refinement UI
- ❌ No prompt refinement feedback loops

### Target State
- ✅ TEXT → PHOTO: Hero frame generation with iteration
- ✅ PHOTO → VIDEO: Image-to-video with polished frames
- ✅ Automated feedback: 3 auto-generations with VBench evaluation
- ✅ Human-in-the-loop: Manual approval and refinement after auto-attempts
- ✅ Iterative refinement: Side-by-side comparison, prompt tweaking
- ✅ LLM-powered suggestions: Prompt improvements based on VBench scores

---

## Phase 1: Hero Frame Generation (TEXT → PHOTO)

### 1.1 Image Generation Service
**New Service:** `backend/app/services/pipeline/image_generation.py`

**Capabilities:**
- Generate 4-8 image variations per prompt using Replicate Stable Diffusion models
- Support for cinematic prompt enhancement (camera specs, lighting, composition)
- Store all generated images with metadata (prompt, seed, model used)
- Support image regeneration with prompt tweaks

**Replicate Models to Use:**
- `stability-ai/sdxl` - High quality, cinematic
- `black-forest-labs/flux-pro` - Latest quality leader
- `stability-ai/stable-diffusion-xl-base-1.0` - Reliable fallback

**Database Changes:**
- New table: `hero_frames` (id, generation_id, image_url, prompt, seed, model, vbench_score, created_at)
- Link to `generations` table

### 1.2 Image Generation UI
**New Component:** `frontend/src/components/generation/HeroFrameGallery.tsx`

**Features:**
- Grid view of generated images (4-8 variations)
- One-click regeneration with prompt tweaks
- Image selection interface (select "hero frame" for video generation)
- Side-by-side comparison view
- Image metadata display (prompt, model, seed)

### 1.3 Cinematographer-Level Prompt Enhancement
**Enhance:** `backend/app/services/pipeline/llm_enhancement.py`

**New Function:** `enhance_image_prompt_with_cinematography()`

**Capabilities:**
- Enhance prompts with camera specs (Alexa Mini, Leica M11, RED, Sony Venice)
- Add lens details (35mm, Helios 44, Cooke S4)
- Specify lighting direction (backlit, motivated lighting, hard rim light)
- Add composition details (rule of thirds, depth, framing)
- Include film stock/color science references (Cinestill 800T, etc.)

**LLM System Prompt:**
- Role: Professional cinematographer
- Task: Transform product description into cinematic image generation prompt
- Output: Detailed prompt with camera, lens, lighting, composition specifications

---

## Phase 2: Image-to-Video Workflow (PHOTO → VIDEO)

### 2.1 Image-to-Video Generation
**Enhance:** `backend/app/services/pipeline/video_generation.py`

**New Function:** `generate_video_from_image()`

**Capabilities:**
- Accept hero frame image as input
- Use image-to-video models on Replicate:
  - `klingai/kling-2.5-turbo` (primary - professional workflow uses Kling)
  - `alibaba/wan-2.5` (supports I2V, high quality)
  - `pixverse/pixverse-v5` (supports I2V, cinematic)
- Generate video with cinematographer-level motion prompts
- Support negative prompts for artifact reduction

**API Changes:**
- Add `hero_frame_id` parameter to video generation endpoint
- Add `negative_prompt` field to scene generation
- Add `camera_movement` field (push-in, dolly left, static, handheld)

### 2.2 Motion Prompt Enhancement
**Enhance:** `backend/app/services/pipeline/llm_enhancement.py`

**New Function:** `enhance_motion_prompt()`

**Capabilities:**
- Generate cinematographer-level motion descriptions
- Specify camera movement (push-in, dolly, tracking, static)
- Add frame rate specifications (120fps slow motion, etc.)
- Include environmental details (dust, confetti, particles)
- Enhance based on hero frame analysis

### 2.3 Negative Prompts Support
**Enhance:** Scene schema and video generation

**Capabilities:**
- Default negative prompts: "fast movements", "disfigurements", "low quality", "artifacts", "distortions"
- User-customizable negative prompts per scene
- Store in scene metadata

---

## Phase 3: Automated Feedback Loops (3 Auto-Attempts)

### 3.1 Multi-Attempt Generation with VBench
**Enhance:** `backend/app/services/pipeline/video_generation.py`

**New Function:** `generate_multiple_attempts_with_vbench()`

**Workflow:**
1. Generate 3 video attempts automatically (parallel or sequential)
2. Run VBench evaluation on each attempt
3. Rank attempts by overall VBench score
4. Auto-select highest-scoring attempt
5. Store all attempts with scores for user review

**Database Changes:**
- Enhance `quality_metrics` table to track multiple attempts per scene
- Add `attempt_number` field
- Add `is_selected` boolean field

### 3.2 VBench Integration Enhancement
**Enhance:** `backend/app/services/pipeline/quality_control.py`

**Capabilities:**
- Complete VBench library integration (currently using fallback)
- Evaluate all VBench dimensions:
  - Temporal quality (subject consistency, background consistency, motion smoothness)
  - Frame-wise quality (aesthetic, imaging quality, object alignment)
  - Text-video alignment (prompt adherence)
- Return detailed scores per dimension
- Generate quality report with recommendations

### 3.3 Auto-Selection Logic
**New Service:** `backend/app/services/pipeline/attempt_selection.py`

**Logic:**
- Compare VBench scores across 3 attempts
- Weighted scoring: temporal_quality (40%), aesthetic_quality (30%), text_video_alignment (30%)
- Select highest overall score
- Flag if all attempts below threshold (trigger human review)

---

## Phase 4: Human-in-the-Loop Refinement

### 4.1 Iteration Workspace UI
**New Component:** `frontend/src/components/generation/IterationWorkspace.tsx`

**Features:**
- Side-by-side comparison of all 3 auto-generated attempts
- VBench score display for each attempt
- Visual quality indicators (color-coded scores)
- One-click "Use This Version" selection
- "Regenerate This Scene" button with prompt editing

### 4.2 Manual Regeneration Interface
**Enhance:** `frontend/src/routes/VideoDetail.tsx`

**New Features:**
- Per-scene regeneration controls
- Prompt editing interface (pre-filled with original prompt)
- Option to use hero frame or regenerate new frame
- Negative prompt editor
- Camera movement selector
- "Generate New Attempt" button (unlimited manual attempts)

### 4.3 Prompt Refinement Suggestions
**New Service:** `backend/app/services/pipeline/prompt_refinement.py`

**Capabilities:**
- Analyze VBench scores to identify weak dimensions
- Use LLM to suggest prompt improvements:
  - Low subject consistency → Add character/product description
  - Low aesthetic quality → Enhance style keywords
  - Low text-video alignment → Clarify visual elements
- Present suggestions in UI for user approval
- Track prompt evolution over iterations

**LLM System Prompt:**
- Role: Video generation expert
- Task: Analyze VBench scores and suggest prompt improvements
- Input: Original prompt + VBench dimension scores
- Output: Specific prompt enhancement suggestions

---

## Phase 5: Iterative Refinement Workflow

### 5.1 Generation History Tracking
**Database Changes:**
- Enhance `generations` table with `parent_generation_id` (for iteration tracking)
- New table: `generation_iterations` (generation_id, iteration_number, parent_id, changes_made)
- Track prompt changes, settings changes, selected attempts

### 5.2 Comparison View
**New Component:** `frontend/src/components/generation/VersionComparison.tsx`

**Features:**
- Compare current iteration vs. previous iterations
- Show VBench score improvements over time
- Highlight what changed (prompt diff, settings diff)
- Side-by-side video playback

### 5.3 Quality Dashboard
**New Component:** `frontend/src/components/generation/QualityDashboard.tsx`

**Features:**
- Visualize VBench scores per scene (radar chart)
- Highlight low-scoring dimensions
- Suggest which scenes need regeneration
- Show improvement trends across iterations
- Overall video quality score

---

## API Endpoints

### New Endpoints

**Image Generation:**
- `POST /api/generations/{id}/hero-frames` - Generate hero frames
- `GET /api/generations/{id}/hero-frames` - List all hero frames
- `POST /api/generations/{id}/hero-frames/{frame_id}/regenerate` - Regenerate specific frame
- `POST /api/generations/{id}/hero-frames/{frame_id}/select` - Select hero frame for video

**Iterative Refinement:**
- `POST /api/generations/{id}/scenes/{scene_number}/regenerate` - Manual scene regeneration
- `GET /api/generations/{id}/attempts` - Get all attempts for a generation
- `POST /api/generations/{id}/attempts/{attempt_id}/select` - Select specific attempt
- `GET /api/generations/{id}/prompt-suggestions` - Get LLM prompt improvement suggestions

**Quality Assessment:**
- `GET /api/generations/{id}/quality-report` - Detailed VBench report
- `GET /api/generations/{id}/quality-trends` - Quality improvement over iterations

### Enhanced Endpoints

**Video Generation:**
- `POST /api/generations` - Add `hero_frame_id`, `negative_prompt`, `camera_movement` parameters
- `POST /api/generations/{id}/process` - Support image-to-video mode

---

## Database Schema Changes

### New Tables

```sql
-- Hero frames for TEXT → PHOTO phase
CREATE TABLE hero_frames (
    id UUID PRIMARY KEY,
    generation_id UUID REFERENCES generations(id),
    image_url TEXT NOT NULL,
    prompt TEXT NOT NULL,
    enhanced_prompt TEXT,
    seed INTEGER,
    model TEXT NOT NULL,
    vbench_score JSONB,
    is_selected BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Track generation iterations
CREATE TABLE generation_iterations (
    id UUID PRIMARY KEY,
    generation_id UUID REFERENCES generations(id),
    iteration_number INTEGER NOT NULL,
    parent_generation_id UUID REFERENCES generations(id),
    changes_made JSONB, -- {prompt_changes, settings_changes, selected_attempts}
    created_at TIMESTAMP DEFAULT NOW()
);

-- Track all video generation attempts (enhance existing)
ALTER TABLE quality_metrics ADD COLUMN attempt_number INTEGER DEFAULT 1;
ALTER TABLE quality_metrics ADD COLUMN is_selected BOOLEAN DEFAULT FALSE;
ALTER TABLE quality_metrics ADD COLUMN parent_attempt_id UUID REFERENCES quality_metrics(id);
```

### Enhanced Tables

```sql
-- Add image-to-video support to scenes
ALTER TABLE scenes ADD COLUMN hero_frame_id UUID REFERENCES hero_frames(id);
ALTER TABLE scenes ADD COLUMN negative_prompt TEXT;
ALTER TABLE scenes ADD COLUMN camera_movement TEXT;

-- Track iteration history
ALTER TABLE generations ADD COLUMN parent_generation_id UUID REFERENCES generations(id);
ALTER TABLE generations ADD COLUMN iteration_number INTEGER DEFAULT 1;
```

---

## Workflow Sequence

### Complete Professional Workflow

1. **User submits prompt** → LLM enhances with cinematography details
2. **Generate hero frames** → 4-8 image variations
3. **User selects hero frame** → Mark as selected
4. **Generate video from hero frame** → 3 auto-attempts with VBench
5. **Auto-select best attempt** → Based on VBench scores
6. **Human review** → User sees all 3 attempts with scores
7. **User can:**
   - Accept auto-selected attempt
   - Select different attempt
   - Regenerate scene with prompt tweaks
   - Request new hero frame
   - Get LLM prompt suggestions
8. **Iterate until satisfied** → Unlimited manual attempts
9. **Finalize video** → Stitch scenes, add audio, export

---

## Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
- Image generation service
- Hero frame gallery UI
- Database schema updates
- Basic image-to-video support

### Phase 2: Automation (Weeks 3-4)
- Multi-attempt generation (3 auto)
- VBench integration completion
- Auto-selection logic
- Quality metrics storage

### Phase 3: Human-in-the-Loop (Weeks 5-6)
- Iteration workspace UI
- Manual regeneration interface
- Prompt refinement service
- Comparison views

### Phase 4: Polish (Weeks 7-8)
- Quality dashboard
- Iteration history tracking
- LLM prompt suggestions UI
- Performance optimization

---

## Success Metrics

1. **Workflow Adoption:**
   - % of users using hero frame generation
   - Average iterations per video
   - Time to final video

2. **Quality Improvement:**
   - Average VBench scores (before vs. after iterations)
   - % of videos requiring manual refinement
   - User satisfaction with final output

3. **Automation Effectiveness:**
   - % of videos where auto-selected attempt is accepted
   - Average number of manual regenerations needed
   - VBench score improvement per iteration

---

## Risks & Mitigations

1. **Risk:** VBench library integration complexity
   - **Mitigation:** Start with fallback metrics, gradually enhance

2. **Risk:** Cost escalation with multiple attempts
   - **Mitigation:** User is aware, cost tracking visible, 3 auto-attempts capped

3. **Risk:** UI complexity overwhelming users
   - **Mitigation:** Progressive disclosure, clear workflow steps, tutorials

4. **Risk:** LLM prompt suggestions not helpful
   - **Mitigation:** User can ignore suggestions, track suggestion acceptance rate

---

## Future Enhancements (Post-MVP)

1. **Automated prompt optimization** based on VBench feedback
2. **Image polishing tools** (artifact removal, enhancement)
3. **Batch generation** (generate multiple videos with variations)
4. **Template library** (save successful prompt patterns)
5. **A/B testing framework** (compare prompt variations automatically)

---

## Dependencies

- Replicate API (image generation models)
- VBench library (complete integration)
- OpenAI/Claude API (prompt refinement)
- Frontend state management (iteration tracking)
- Database migrations (schema updates)

---

## Next Steps

1. **Review and approve this plan**
2. **Create detailed technical specifications** for Phase 1
3. **Set up development environment** for image generation testing
4. **Design UI mockups** for iteration workspace
5. **Begin Phase 1 implementation**

---

**Document Status:** High-Level Plan - Ready for Review

