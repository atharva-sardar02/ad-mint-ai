# Master Mode Agent Sequence Reference

**Last Updated:** November 21, 2025

This document provides a complete reference for the agent call sequence in Master Mode, explaining which agents are called, in what order, and what they produce.

---

## Complete Agent Flow

```
User Prompt + Reference Images
    ↓
┌─────────────────────────────────────────┐
│ PHASE 1: Story Generation               │
│ [Story Director ↔ Story Critic]         │
│ Loop: 1-3 iterations (default: 3)       │
└─────────────────────────────────────────┘
    ↓
Final Approved Story
    ↓
┌─────────────────────────────────────────┐
│ PHASE 2: Scene Generation               │
│ For Each Scene:                         │
│   [Scene Writer ↔ Scene Critic]         │
│   Loop: 1-3 iterations per scene        │
│                                         │
│ After All Scenes:                       │
│   [Scene Cohesor]                       │
│   Loop: 1-2 iterations                  │
└─────────────────────────────────────────┘
    ↓
Final Approved Scenes + Cohesion Analysis
    ↓
┌─────────────────────────────────────────┐
│ PHASE 3: Video Prompt Enhancement       │
│ [Scene Enhancer]                        │
│ [Scene Aligner]                         │
└─────────────────────────────────────────┘
    ↓
Enhanced Video Prompts (300-500 words each)
    ↓
┌─────────────────────────────────────────┐
│ PHASE 4: Video Generation & Stitching  │
│ [Video Generator] (Parallel, max 4)     │
│ [Video Stitcher]                        │
└─────────────────────────────────────────┘
    ↓
Final Stitched Video
```

---

## Phase-by-Phase Breakdown

### **Phase 1: Story Generation**

**Entry Point:** `/api/master-mode/generate-story` endpoint  
**Code:** `backend/app/services/master_mode/story_generator.py`

#### Agent Sequence:

1. **Story Director**
   - **Purpose:** Creates story drafts from user prompt
   - **Input:** User prompt + reference images (optional)
   - **Output:** Story draft text
   - **Model:** Claude with vision support (if reference images provided)

2. **Story Critic** 
   - **Purpose:** Reviews and scores story quality
   - **Input:** Story draft from Director
   - **Output:** 
     - Approval status (`approved`, `needs_revision`, `rejected`)
     - Overall score (0-100)
     - Detailed critique
     - Strengths list
     - Improvements needed
     - Priority fixes
   - **Approval Threshold:** Score ≥ 85

#### Iteration Logic:
```python
max_iterations = 3  # Configurable
for iteration in range(1, max_iterations + 1):
    story_draft = story_director.generate(prompt, previous_critique)
    critique = story_critic.evaluate(story_draft)
    
    if critique.approval_status == "approved":
        break  # Story approved!
    
    if iteration == max_iterations:
        # Use best available draft
        break
```

#### Output:
- Final approved story
- Conversation history (all Director ↔ Critic exchanges)
- Total iterations
- Final score

---

### **Phase 2: Scene Generation**

**Code:** `backend/app/services/master_mode/scene_generator.py`

#### Agent Sequence:

##### Step 1: Per-Scene Generation Loop

For each scene identified in the story:

3. **Scene Writer**
   - **Purpose:** Creates detailed scene descriptions
   - **Input:** 
     - Complete story (for context)
     - Scene number
     - Previous critique (if revision)
   - **Output:** Detailed scene content in Markdown format (150-250 words)
     - Scene description
     - Visual elements
     - Camera direction
     - Timing
     - Action/narrative

4. **Scene Critic**
   - **Purpose:** Evaluates individual scene quality
   - **Input:** Scene draft from Writer
   - **Output:**
     - Approval status
     - Overall score (0-100)
     - Critique
     - Strengths
     - Improvements needed
     - Priority fixes
   - **Approval Threshold:** Score ≥ 80

```python
max_iterations_per_scene = 3  # Configurable
for scene_number in range(1, total_scenes + 1):
    for iteration in range(1, max_iterations_per_scene + 1):
        scene_draft = scene_writer.write(story, scene_number, previous_critique)
        critique = scene_critic.evaluate(scene_draft)
        
        if critique.approval_status == "approved":
            break
```

##### Step 2: Cross-Scene Cohesion Analysis

After all scenes are written and approved:

5. **Scene Cohesor**
   - **Purpose:** Analyzes cohesion and consistency across all scenes
   - **Input:** All final scene drafts
   - **Output:**
     - Overall cohesion score (0-100)
     - Pairwise transition analysis (Scene 1→2, 2→3, etc.)
     - Transition scores for each pair
     - Global issues affecting multiple scenes
     - Scene-specific feedback
     - Consistency issues (character, environment, style)
     - Overall recommendations
   - **Approval Threshold:** Score ≥ 75

```python
max_cohesor_iterations = 2  # Configurable
for iteration in range(1, max_cohesor_iterations + 1):
    cohesion_analysis = scene_cohesor.analyze(all_scenes)
    
    if cohesion_analysis.overall_cohesion_score >= 75:
        break  # Cohesion approved!
    
    # Revise problematic scenes based on feedback
    revised_scenes = revise_scenes(cohesion_analysis.scene_specific_feedback)
```

#### Output:
- Final approved scenes (N scenes)
- Scene-by-scene conversation history
- Cohesion analysis with transition recommendations
- Total iterations across all scenes

---

### **Phase 3: Video Prompt Enhancement**

**Code:** `backend/app/services/master_mode/scene_to_video.py` + `scene_enhancer.py`

#### Agent Sequence:

6. **Scene Enhancer**
   - **Purpose:** Expands scenes into ultra-detailed Veo 3.1 prompts
   - **Input:** Scene content (150-250 words)
   - **Process:** Uses LLM to add:
     - Detailed cinematography specifications
     - Precise lighting descriptions
     - Camera movement details
     - Technical video parameters
     - Color grading notes
     - Composition details
   - **Output:** Enhanced prompt (300-500 words)
   - **Target:** Optimized for Google Veo 3.1 video generation

7. **Scene Aligner**
   - **Purpose:** Ensures visual consistency across enhanced scenes
   - **Input:** All enhanced prompts
   - **Process:** 
     - Analyzes visual elements across scenes
     - Identifies inconsistencies (character appearance, environment, lighting)
     - Aligns visual descriptions for smooth transitions
   - **Output:** Aligned enhanced prompts with consistent visual language

```python
# Enhancement process
enhanced_scenes = []
for scene in scenes:
    enhanced = scene_enhancer.enhance(
        scene_content=scene["content"],
        target_words=400,  # 300-500 range
        optimization="veo-3.1"
    )
    enhanced_scenes.append(enhanced)

# Alignment process
aligned_scenes = scene_aligner.align(enhanced_scenes)
```

#### Output:
- Enhanced video prompts (300-500 words each)
- Metadata (duration, camera movement, subject presence)
- Reference image assignments

---

### **Phase 4: Video Generation & Stitching**

**Code:** `backend/app/services/master_mode/video_generation.py` + `video_stitcher.py`

#### Agent Sequence:

8. **Video Generator**
   - **Purpose:** Generates videos using Google Veo 3.1
   - **Input:** Enhanced video prompts + parameters
   - **Process:**
     - Parallel generation (max 4 concurrent by default)
     - Uses semaphore for controlled parallelism
     - Supports two modes:
       - **R2V Mode:** Uses reference images (8s duration, 16:9)
       - **Start/End Frame Mode:** Uses generated keyframes
   - **Parameters:**
     - Prompt (300-500 words)
     - Negative prompt (quality controls)
     - Duration (4s, 6s, or 8s)
     - Aspect ratio (16:9 default)
     - Resolution (1080p)
     - Audio generation (enabled)
   - **Output:** Individual scene MP4 videos

```python
# Parallel video generation with controlled concurrency
max_parallel = 4
semaphore = asyncio.Semaphore(max_parallel)

async def generate_with_semaphore(scene_params, scene_num):
    async with semaphore:
        return await generate_scene_video(scene_params, output_dir, scene_num)

tasks = [generate_with_semaphore(params, params["scene_number"]) 
         for params in video_params_list]
video_paths = await asyncio.gather(*tasks)
```

9. **Video Stitcher**
   - **Purpose:** Combines scene videos into final stitched video
   - **Input:** 
     - List of scene video paths
     - Transition types from Scene Cohesor analysis
   - **Transition Types:**
     - `crossfade`: Smooth blend (score ≥ 85)
     - `cut`: Direct cut (score 70-84)
     - `fade`: Fade through black (score < 70)
   - **Process:**
     - Uses MoviePy for video editing
     - Applies transitions based on cohesion scores
     - Maintains audio continuity
   - **Output:** Final stitched MP4 video

```python
# Transition selection logic
def get_transition(transition_score):
    if transition_score >= 85:
        return "crossfade"
    elif transition_score >= 70:
        return "cut"
    else:
        return "fade"

transitions = [get_transition(pair["transition_score"]) 
               for pair in cohesion_analysis["pair_wise_analysis"]]
```

#### Output:
- Final stitched video (MP4)
- Individual scene videos
- Generation metadata (costs, durations, success rates)

---

## Agent Reference Table

| # | Agent | Module | Purpose | Input | Output | Max Iterations |
|---|-------|--------|---------|-------|--------|----------------|
| 1 | **Story Director** | `story_director.py` | Create story drafts | User prompt, reference images | Story text | 3 (loop) |
| 2 | **Story Critic** | `story_critic.py` | Evaluate story | Story draft | Critique + score | 3 (loop) |
| 3 | **Scene Writer** | `scene_writer.py` | Write scene descriptions | Story, scene number | Scene content (150-250 words) | 3 per scene |
| 4 | **Scene Critic** | `scene_critic.py` | Evaluate scene | Scene draft | Critique + score | 3 per scene |
| 5 | **Scene Cohesor** | `scene_cohesor.py` | Analyze cohesion | All scenes | Cohesion analysis + transitions | 2 |
| 6 | **Scene Enhancer** | `scene_enhancer.py` | Enhance for Veo 3.1 | Scene content | Enhanced prompt (300-500 words) | 1 |
| 7 | **Scene Aligner** | `scene_enhancer.py` | Ensure consistency | Enhanced prompts | Aligned prompts | 1 |
| 8 | **Video Generator** | `video_generation.py` | Generate videos | Enhanced prompts | MP4 videos | 1 (parallel) |
| 9 | **Video Stitcher** | `video_stitcher.py` | Stitch videos | Video files + transitions | Final video | 1 |

---

## Approval Thresholds

| Agent | Approval Threshold | Metric |
|-------|-------------------|--------|
| Story Critic | Score ≥ 85 | Overall story quality |
| Scene Critic | Score ≥ 80 | Individual scene quality |
| Scene Cohesor | Score ≥ 75 | Overall cohesion |

---

## Default Configuration

```python
# Story generation
MAX_STORY_ITERATIONS = 3

# Scene generation
MAX_ITERATIONS_PER_SCENE = 3
MAX_COHESOR_ITERATIONS = 2

# Video generation
MAX_PARALLEL_VIDEOS = 4
DEFAULT_DURATION = 6  # seconds
DEFAULT_RESOLUTION = "1080p"
DEFAULT_ASPECT_RATIO = "16:9"

# Enhancement
ENHANCE_PROMPTS = True  # Use Scene Enhancer
TARGET_PROMPT_LENGTH = 400  # words (range: 300-500)
```

---

## API Endpoint Parameters

**Endpoint:** `POST /api/master-mode/generate-story`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `prompt` | string | Yes | - | User prompt for the advertisement |
| `title` | string | No | None | Optional video title |
| `brand_name` | string | No | None | Optional brand name |
| `reference_images` | file[] | No | [] | Reference images (up to 3) |
| `max_iterations` | int | No | 3 | Maximum story iterations |
| `generate_scenes` | bool | No | true | Generate scenes after story |
| `generate_videos` | bool | No | false | Generate and stitch videos |

---

## Progress Tracking

Master Mode provides real-time progress updates via Server-Sent Events (SSE):

1. **init** (0%) - Starting generation
2. **upload** (5-10%) - Saving reference images
3. **story** (15-30%) - Story generation progress
4. **scenes** (35-55%) - Scene generation progress
5. **video_params** (60-65%) - Video prompt enhancement
6. **videos** (70-95%) - Video generation and stitching
7. **complete** (100%) - Generation complete

---

## Total Agent Count

**9 distinct agents** work together in the Master Mode pipeline:
- 2 Story agents (Director, Critic)
- 3 Scene agents (Writer, Critic, Cohesor)
- 2 Enhancement agents (Enhancer, Aligner)
- 2 Video agents (Generator, Stitcher)

---

## Example Execution Time

For a typical 30-second video (5 scenes × 6 seconds):

| Phase | Estimated Time |
|-------|----------------|
| Story Generation (3 iterations) | ~2-3 minutes |
| Scene Generation (5 scenes × 3 iterations) | ~5-7 minutes |
| Scene Cohesion (2 iterations) | ~1-2 minutes |
| Prompt Enhancement | ~30-60 seconds |
| Video Generation (5 scenes, parallel) | ~15-20 minutes |
| Video Stitching | ~30-60 seconds |
| **Total** | **~25-35 minutes** |

*Note: Video generation time depends on Veo 3.1 API response times*

---

## Related Documentation

- **API Routes:** `backend/app/api/routes/master_mode.py`
- **Progress Streaming:** `backend/app/api/routes/master_mode_progress.py`
- **Schemas:** `backend/app/services/master_mode/schemas.py`
- **Story Generation:** `backend/app/services/master_mode/story_generator.py`
- **Scene Generation:** `backend/app/services/master_mode/scene_generator.py`
- **Video Generation:** `backend/app/services/master_mode/video_generation.py`

---

## Key Design Decisions

1. **Iterative Refinement:** Each phase uses critic feedback to improve quality
2. **Parallel Processing:** Videos generate concurrently for speed (max 4)
3. **Vision Support:** Reference images enhance story and video generation
4. **Ultra-Detailed Prompts:** Scene Enhancer expands to 300-500 words for Veo 3.1
5. **Cohesion Analysis:** Scene Cohesor ensures smooth transitions
6. **Progressive Enhancement:** Each agent builds on previous outputs
7. **Quality Thresholds:** Approval scores ensure minimum quality standards

---

*This document reflects the Master Mode implementation as of November 21, 2025*

