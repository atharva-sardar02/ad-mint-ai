# Epic Technical Specification: CLI MVP - Video Generation Feedback Loops

Date: 2025-11-17
Author: BMad
Epic ID: 9
Status: Draft

---

## Overview

Epic 9 establishes CLI-based rapid iteration tools for video prompt enhancement and video generation with automatic VBench quality scoring. This epic enables developers to quickly test and refine video generation workflows before building UI components, following the CLI MVP strategy outlined in the PRD's Hero-Frame Iteration Plan (Section 23.0). The epic implements three CLI tools: (1) `enhance_video_prompt.py` for iterative video prompt enhancement using two-agent feedback loops with VideoDirectorGPT enhancements, (2) `generate_videos.py` for text-to-video and image-to-video generation with automatic VBench quality scoring, and (3) `feedback_loop.py` for orchestrating the complete end-to-end workflow from image prompt → image generation → video prompt → video generation. These tools build upon Epic 8's image generation feedback loops and integrate with existing VBench quality control infrastructure (Story 7.6) to ensure professional-quality video outputs. The CLI MVP approach allows rapid validation of video feedback loops, VBench scoring mechanisms, and complete workflow orchestration before committing to UI development.

## Objectives and Scope

**In-Scope:**
- CLI tool for iterative video prompt enhancement (`enhance_video_prompt.py`) with two-agent feedback loops (Video Director/Creative Director + Prompt Engineer) and VideoDirectorGPT-style enhancements
- CLI tool for video generation (`generate_videos.py`) supporting both text-to-video and image-to-video modes with automatic VBench quality scoring
- CLI tool for integrated feedback loop orchestration (`feedback_loop.py`) that chains image prompt enhancement → image generation → video prompt enhancement → video generation
- Integration with existing `prompt_enhancement.py` service pattern from Story 7.3 Phase 1, adapted for video-specific enhancement
- Integration with VBench quality control service (`quality_control.py`) from Story 7.6 for automatic video quality scoring
- Support for image-to-video generation using hero frames from Epic 8 (Story 8.2) and storyboards from Epic 8 (Story 8.3)
- Trace file generation and logging for transparency (all prompt versions, scores, iterations, metadata, VBench dimensions)
- Support for stdin input, custom output directories, and configuration flags (max-iterations, threshold, num-attempts, negative-prompt)
- Directory structure for organizing outputs (`output/video_prompt_traces/`, `output/video_generations/`, `output/feedback_loops/`)
- Human-in-the-loop feedback support: pause after generation for manual review, accept feedback via CLI, incorporate into next iteration
- Reuse of Prompt Scoring Guide guidelines for video prompt structure and enhancement best practices
- Storyboard processing mode: Load storyboard JSON, enhance motion prompts per clip using unified narrative context, save enhanced prompts

**Out-of-Scope:**
- UI components for video gallery, iteration workspace, or quality dashboard (deferred to future UI phase after CLI MVP validation)
- Integration with main web application API endpoints (CLI tools are standalone for developer use)
- Database persistence of CLI-generated videos (saved to disk only)
- User authentication or access control for CLI tools (local developer tools)
- Real-time progress updates or webhooks (CLI tools run synchronously)
- Multi-user collaboration features
- Production deployment of CLI tools (developer tools, not production services)

## System Architecture Alignment

This epic extends the existing architecture described in `docs/architecture.md` by adding CLI-based developer tools for video generation feedback loops that operate independently of the main FastAPI web application. The CLI tools follow the same service patterns established in the backend (`app/services/pipeline/`) but execute as standalone Python scripts. The `enhance_video_prompt.py` tool reuses the two-agent prompt enhancement pattern from `app/services/pipeline/prompt_enhancement.py` (Story 7.3 Phase 1) and adapts the image-specific pattern from `app/services/pipeline/image_prompt_enhancement.py` (Story 8.1), adapting it for video-specific enhancement with motion, temporal coherence, and cinematography focus. The `generate_videos.py` tool integrates with Replicate API for text-to-video and image-to-video generation (Kling, Wan, PixVerse, or similar models), following the same API integration patterns used in `app/services/pipeline/video_generation.py` for existing video models. The VBench quality scoring integration reuses `app/services/pipeline/quality_control.py` from Story 7.6, which already implements VBench evaluation for video quality metrics via the `evaluate_vbench()` function. The `feedback_loop.py` orchestrator chains together Epic 8's CLI tools (`enhance_image_prompt.py`, `generate_images.py`, `create_storyboard.py`) with Epic 9's video tools, creating a complete end-to-end workflow. All CLI tools save outputs to the `backend/output/` directory structure, consistent with the existing pipeline's output organization. The tools are designed to be runnable from the command line without requiring the FastAPI server to be running, enabling rapid iteration and testing workflows for developers. The video generation tools support both text-to-video (direct prompt-to-video) and image-to-video (hero frame + motion prompt) modes, enabling the hero-frame-first workflow outlined in the PRD's Hero-Frame Iteration Plan. Storyboard processing integrates with `app/services/pipeline/storyboard_service.py` (Story 8.3) and uses unified narrative documents from Story 8.4 to maintain narrative coherence across video clips.

## Detailed Design

### Services and Modules

**Backend Services:**

1. **`app/services/pipeline/video_prompt_enhancement.py`** (New)
   - **Purpose**: Video-specific prompt enhancement service adapting the two-agent pattern for motion, temporal coherence, and cinematography focus
   - **Responsibilities**:
     - Agent 1 (Video Director/Creative Director): Enhances prompts with camera framing/movement, action beats, timing cues, lighting, color palette, motion intensity, temporal continuity hints
     - Agent 2 (Prompt Engineer): Critiques and scores prompts on completeness, specificity, professionalism, cinematography, temporal coherence, brand alignment
     - Iterative refinement (max 3 rounds) until score threshold met or convergence detected
     - VideoDirectorGPT-style enhancements (if Story 7.3 Phase 2 available): Shot list with camera metadata, scene dependencies, narrative flow, consistency groupings
     - Scoring on 6 dimensions (0-100 each): Completeness, Specificity, Professionalism, Cinematography, Temporal Coherence, Brand Alignment
     - Image-to-video motion prompt enhancement: Camera movement, motion intensity, frame rate considerations, negative prompts
     - Storyboard processing: Load storyboard JSON, enhance motion prompts per clip using unified narrative context
   - **Inputs**: User prompt (string), max_iterations (int), score_threshold (float), trace_dir (Path), video_mode (bool), image_to_video (bool), storyboard_path (Optional[str])
   - **Outputs**: Enhanced prompt (string), iteration history (List[Dict]), final scores (Dict[str, float]), VideoDirectorGPT plan (Optional[Dict])
   - **Dependencies**: OpenAI API (GPT-4), `app/core/config.py` for settings, scene planning service (if VideoDirectorGPT available), storyboard_service (for storyboard mode)

2. **`app/services/pipeline/video_generation_cli.py`** (New)
   - **Purpose**: Video generation service for CLI tools supporting text-to-video and image-to-video modes
   - **Responsibilities**:
     - Generate multiple video attempts (default: 3) from enhanced prompt or hero frame + motion prompt
     - Support text-to-video mode: Direct prompt-to-video using Replicate API (Kling, Wan, PixVerse)
     - Support image-to-video mode: Hero frame image + motion prompt using Replicate API
     - Support storyboard mode: Generate videos from storyboard start/end frames
     - Download and save generated videos to organized directory structure
     - Track generation metadata (prompt, model, settings, timestamps, cost)
   - **Inputs**: Enhanced prompt (string) OR hero_frame_path (str) + motion_prompt (str), num_attempts (int), model (str), negative_prompt (Optional[str]), storyboard_path (Optional[str])
   - **Outputs**: List of video file paths, metadata JSON files
   - **Dependencies**: Replicate API, `app/core/config.py` for API keys, VBench quality control service

3. **`app/services/pipeline/video_quality_scoring.py`** (New - Wrapper/CLI Integration)
   - **Purpose**: CLI integration wrapper for VBench quality scoring service
   - **Responsibilities**:
     - Integrate with existing `quality_control.py` VBench evaluation (Story 7.6)
     - Score each generated video using VBench metrics (all 16 dimensions)
     - Calculate overall quality score (weighted combination of VBench dimensions)
     - Rank videos by overall quality score
     - Support batch scoring for multiple video attempts
   - **Inputs**: Video file path (str), prompt text (str)
   - **Outputs**: VBench scores dictionary with all dimensions and overall score
   - **Dependencies**: `app/services/pipeline/quality_control.py` (evaluate_vbench function)

4. **`app/services/pipeline/feedback_loop_orchestrator.py`** (New)
   - **Purpose**: Orchestrator service for complete end-to-end feedback loop workflow
   - **Responsibilities**:
     - Chain together Epic 8 tools (image prompt enhancement, image generation, storyboard creation) with Epic 9 tools (video prompt enhancement, video generation)
     - Support full workflow: image prompt → image generation → video prompt → video generation
     - Support partial workflows: image-only, video-only, prompt-only
     - Manage workflow state and checkpoints (resume from interruption)
     - Support human-in-the-loop feedback: Pause after each stage, accept feedback, incorporate into next iteration
     - Generate unified trace format for end-to-end workflow
   - **Inputs**: Starting prompt (string), workflow_mode (str: "full", "image-only", "video-only", "prompt-only"), iteration controls (Dict)
   - **Outputs**: Complete workflow trace with all intermediate outputs, scores, metrics
   - **Dependencies**: All Epic 8 and Epic 9 CLI service modules

**CLI Tools:**

1. **`backend/enhance_video_prompt.py`** (New)
   - **Purpose**: Standalone CLI tool for iterative video prompt enhancement
   - **Usage**: `python enhance_video_prompt.py prompt.txt [--video-mode] [--max-iterations 5] [--threshold 90] [--output-dir ./my_traces] [--storyboard storyboard.json]`
   - **Features**: stdin input support, custom output directories, iteration control, VideoDirectorGPT integration, image-to-video motion prompt mode, storyboard processing mode, verbose logging
   - **Outputs**: Trace files in `output/video_prompt_traces/{timestamp}/` with all prompt versions, scores, VideoDirectorGPT plan

2. **`backend/generate_videos.py`** (New)
   - **Purpose**: Standalone CLI tool for video generation with automatic VBench quality scoring
   - **Usage**: `python generate_videos.py enhanced_prompt.txt [--num-attempts 3] [--image-to-video --hero-frame path/to/image.png --motion-prompt "camera pans left"]`
   - **Features**: Text-to-video and image-to-video modes, automatic VBench scoring, ranked output, top video highlighting, cost tracking, storyboard mode support, negative prompts
   - **Outputs**: Videos and metadata in `output/video_generations/{timestamp}/`

3. **`backend/feedback_loop.py`** (New)
   - **Purpose**: Standalone CLI tool for orchestrating complete feedback loop workflow
   - **Usage**: `python feedback_loop.py start_prompt.txt [--workflow full] [--max-iterations-image 3] [--max-iterations-video 3] [--num-image-variations 8] [--num-video-attempts 3]`
   - **Features**: Full workflow orchestration, partial workflows (image-only, video-only, prompt-only), human-in-the-loop feedback, checkpoint/resume support, unified trace format
   - **Outputs**: Complete workflow trace in `output/feedback_loops/{timestamp}/` with all intermediate outputs, scores, metrics

### Data Models and Contracts

**Data Structures (Python Classes):**

1. **`VideoPromptEnhancementResult`** (in `video_prompt_enhancement.py`)
   ```python
   class VideoPromptEnhancementResult:
       original_prompt: str
       final_prompt: str
       iterations: List[Dict]  # Each dict: {iteration_num, agent1_output, agent2_output, scores}
       final_score: Dict[str, float]  # {completeness, specificity, professionalism, cinematography, temporal_coherence, brand_alignment, overall}
       total_iterations: int
       videodirectorgpt_plan: Optional[Dict]  # Shot list, scene dependencies, consistency groupings
       motion_prompt: Optional[str]  # For image-to-video mode
       storyboard_enhanced_prompts: Optional[Dict]  # For storyboard mode: {clip_id: enhanced_motion_prompt}
   ```

2. **`VideoGenerationResult`** (in `video_generation_cli.py`)
   ```python
   class VideoGenerationResult:
       videos: List[VideoMetadata]  # Sorted by quality score (best first)
       generation_trace: Dict  # Complete trace with prompts, videos, scores, costs, timestamps
       mode: str  # "text-to-video" or "image-to-video"
       hero_frame_path: Optional[str]  # If image-to-video mode
       storyboard_ref: Optional[str]  # If storyboard mode
   
   class VideoMetadata:
       file_path: str
       rank: int
       vbench_scores: Dict[str, float]  # All 16 VBench dimensions + overall
       generation_params: Dict  # {prompt, model, settings, seed, timestamp, cost}
   ```

3. **`FeedbackLoopResult`** (in `feedback_loop_orchestrator.py`)
   ```python
   class FeedbackLoopResult:
       workflow_mode: str  # "full", "image-only", "video-only", "prompt-only"
       stages: List[WorkflowStage]
       final_outputs: Dict  # {best_image, best_video, final_prompts}
       end_to_end_metrics: Dict  # {total_cost, total_time, quality_scores_at_each_stage}
       workflow_trace: Dict  # Complete trace with all intermediate outputs
   
   class WorkflowStage:
       stage_name: str  # "image_prompt", "image_generation", "video_prompt", "video_generation"
       inputs: Dict
       outputs: Dict
       scores: Dict
       feedback: Optional[str]  # Human feedback if provided
   ```

**File Structure Contracts:**

1. **Video Prompt Trace Directory** (`output/video_prompt_traces/{timestamp}/`):
   - `00_original_prompt.txt` - Original user input
   - `01_agent1_iteration_1.txt` - First Video Director enhancement
   - `02_agent2_iteration_1.txt` - First Prompt Engineer critique + score
   - `03_agent1_iteration_2.txt` - Second enhancement (if iterated)
   - `04_agent2_iteration_2.txt` - Second critique (if iterated)
   - `05_final_enhanced_prompt.txt` - Final enhanced prompt
   - `06_videodirectorgpt_plan.json` - VideoDirectorGPT planning output (if available)
   - `prompt_trace_summary.json` - Metadata: scores, iterations, timestamps
   - For storyboard mode: `storyboard_enhanced_motion_prompts.json` with all clips' enhanced prompts and scores

2. **Video Generation Directory** (`output/video_generations/{timestamp}/`):
   - `video_001.mp4`, `video_002.mp4`, etc. (numbered by quality rank)
   - `video_001_metadata.json`, `video_002_metadata.json` (VBench scores, prompt, model, settings)
   - `generation_trace.json` - Complete trace with all prompts, videos, VBench scores (all 16 dimensions), costs, timestamps, hero frame path (if image-to-video), storyboard references (if used)

3. **Feedback Loop Directory** (`output/feedback_loops/{timestamp}/`):
   - `stage_01_image_prompt/` - Image prompt enhancement outputs
   - `stage_02_image_generation/` - Image generation outputs
   - `stage_03_storyboard/` - Storyboard outputs (if applicable)
   - `stage_04_video_prompt/` - Video prompt enhancement outputs
   - `stage_05_video_generation/` - Video generation outputs
   - `workflow_summary.json` - End-to-end metrics, final outputs, quality scores at each stage, cost breakdown

### APIs and Interfaces

**External API Integrations:**

1. **Replicate API** (Text-to-Video and Image-to-Video Models)
   - **Endpoint**: Replicate Python SDK
   - **Models**: Kling, Wan, PixVerse, or other text-to-video/image-to-video models available on Replicate
   - **Text-to-Video Request**: `replicate.run(model="kling/kling-v1", input={"prompt": str, "duration": int, "aspect_ratio": str})`
   - **Image-to-Video Request**: `replicate.run(model="wan/research", input={"image": image_url, "motion_prompt": str, "negative_prompt": str})`
   - **Response**: Video URL (download required)
   - **Error Handling**: Retry logic with exponential backoff, fallback models if primary fails
   - **Cost Tracking**: Track cost per generation (varies by model and duration)

2. **OpenAI API** (LLM for Prompt Enhancement)
   - **Endpoint**: OpenAI Python SDK
   - **Models**: GPT-4-turbo (default for both agents)
   - **Request**: `openai.ChatCompletion.create(model="gpt-4-turbo", messages=[system_prompt, user_prompt])`
   - **Response**: Enhanced prompt text (Agent 1) or JSON scores/critique (Agent 2)
   - **Error Handling**: Retry logic for rate limits, timeout handling
   - **Cost Tracking**: Track token usage and cost per iteration

3. **VBench Quality Control** (Internal Service)
   - **Source**: `app/services/pipeline/quality_control.py` (Story 7.6)
   - **Function**: `evaluate_vbench(video_clip_path: str, prompt_text: str) -> Dict[str, float]`
   - **Input**: Video file path, prompt text
   - **Output**: VBench scores dictionary with all 16 dimensions:
     - Temporal Quality: subject_consistency, background_consistency, motion_smoothness, dynamic_degree
     - Frame-wise Quality: aesthetic_quality, imaging_quality, object_class_alignment
     - Text-Video Alignment: text_video_alignment
     - Overall Quality: overall_quality (weighted combination)
   - **Note**: Currently uses fallback metrics if VBench library unavailable, but structure ready for VBench integration

**CLI Interface Contracts:**

1. **`enhance_video_prompt.py`**
   ```bash
   enhance_video_prompt.py <input> [OPTIONS]
   
   Arguments:
     input              File path or "-" for stdin
   
   Options:
     --video-mode       Enable video-specific enhancement (default: True)
     --image-to-video   Enable image-to-video motion prompt mode
     --storyboard PATH  Path to storyboard JSON file (for storyboard processing mode)
     --max-iterations N Maximum iteration rounds (default: 3)
     --threshold F      Score threshold to stop at (default: 85.0)
     --output-dir DIR   Custom output directory (default: output/video_prompt_traces/)
     --creative-model M Model for Video Director agent (default: gpt-4-turbo)
     --critique-model M Model for Prompt Engineer agent (default: gpt-4-turbo)
     --verbose          Enable verbose logging
   ```

2. **`generate_videos.py`**
   ```bash
   generate_videos.py <prompt_file> [OPTIONS]
   
   Arguments:
     prompt_file         Path to enhanced prompt file (for text-to-video)
   
   Options:
     --num-attempts N    Number of video attempts (default: 3)
     --image-to-video    Enable image-to-video mode (requires --hero-frame)
     --hero-frame PATH   Path to hero frame image (for image-to-video)
     --motion-prompt S   Motion prompt for image-to-video (e.g., "camera pans left")
     --storyboard PATH   Path to storyboard JSON (for storyboard mode)
     --negative-prompt S Negative prompt (e.g., "jerky, flicker, inconsistent")
     --output-dir DIR    Custom output directory (default: output/video_generations/)
     --model M           Replicate model name (default: kling/kling-v1)
     --verbose           Enable verbose logging
   ```

3. **`feedback_loop.py`**
   ```bash
   feedback_loop.py <prompt_file> [OPTIONS]
   
   Arguments:
     prompt_file         Path to starting prompt file
   
   Options:
     --workflow MODE    Workflow mode: full, image-only, video-only, prompt-only (default: full)
     --max-iterations-image N  Image prompt iterations (default: 3)
     --max-iterations-video N  Video prompt iterations (default: 3)
     --num-image-variations N  Image generation count (default: 8)
     --num-video-attempts N    Video generation count (default: 3)
     --output-dir DIR    Custom output directory (default: output/feedback_loops/)
     --interactive       Enable human-in-the-loop feedback (pause after each stage)
     --resume PATH       Resume from checkpoint file
     --verbose           Enable verbose logging
   ```

### Workflows and Sequencing

**Workflow 1: Video Prompt Enhancement (Story 9.1)**

```
1. User provides basic video prompt (file or stdin) OR storyboard JSON
2. CLI tool loads prompt/storyboard and initializes trace directory
3. If storyboard mode:
   a. Load storyboard JSON and parse clip information
   b. Load unified narrative document (from storyboard metadata)
   c. For each clip: Extract motion_description, camera metadata, start/end frame paths
4. Quick initial assessment (rule-based scoring)
   - If score >= 75.0: Skip enhancement, return original
   - Else: Proceed to iterative enhancement
5. Iteration Loop (max 3 rounds):
   a. Agent 1 (Video Director) enhances prompt:
      - Adds camera framing and movement (wide aerial shot, steady tracking shot, low-angle view)
      - Adds action beats and timing cues
      - Adds lighting and color palette
      - Adds motion intensity and style
      - Adds temporal continuity hints
      - For storyboard mode: Integrates narrative context (emotional arc, visual progression, scene connections)
   b. Agent 2 (Prompt Engineer) critiques and scores:
      - Scores on 6 dimensions (0-100 each)
      - Provides specific feedback
      - Calculates overall weighted score
   c. Check convergence:
      - If overall score >= threshold: Exit loop
      - If no improvement: Exit loop
      - Else: Continue to next iteration
6. Optional: VideoDirectorGPT-style planning (if Story 7.3 Phase 2 available):
   - Generate shot list with camera metadata
   - Generate scene dependencies and narrative flow
   - Generate consistency groupings for entities
7. For image-to-video mode: Enhance motion prompt:
   - Camera movement (pan, tilt, dolly, static, tracking)
   - Motion intensity (subtle, moderate, dynamic)
   - Frame rate considerations
   - Negative prompts for unwanted motion
8. Save all prompt versions to trace files
9. Save metadata JSON with scores, iteration history, VideoDirectorGPT plan
10. Print results to console (scores, iteration count, final prompt)
```

**Workflow 2: Video Generation with VBench Scoring (Story 9.2)**

```
1. User provides enhanced video prompt OR hero frame + motion prompt OR storyboard
2. CLI tool loads inputs and initializes output directory
3. Determine generation mode:
   a. Text-to-video: Use enhanced prompt directly
   b. Image-to-video: Use hero frame + motion prompt
   c. Storyboard: Use start/end frames from storyboard
4. Generate multiple video attempts (default: 3):
   a. For each attempt:
      - Call Replicate API (text-to-video or image-to-video model)
      - Download generated video
      - Save video file (numbered: video_001.mp4, video_002.mp4, ...)
5. Automatic VBench quality scoring for each video:
   a. Call evaluate_vbench() from quality_control.py
   b. Compute all 16 VBench dimensions:
      - Temporal Quality: subject_consistency, background_consistency, motion_smoothness, dynamic_degree
      - Frame-wise Quality: aesthetic_quality, imaging_quality, object_class_alignment
      - Text-Video Alignment: text_video_alignment
   c. Calculate overall quality score (weighted combination)
6. Rank videos by overall quality score (best first)
7. Rename/sort videos by rank (video_001 = best, video_002 = second-best, ...)
8. Save metadata JSON for each video (VBench scores, prompt, model, settings)
9. Save generation trace JSON (all prompts, videos, VBench scores, costs, timestamps)
10. Print results to console:
    - Ranked list with VBench scores
    - Top video highlighted as "system-selected best"
    - VBench score breakdown per video (key dimensions)
    - File paths for manual viewing
    - Cost summary
11. Auto-select top-scoring video as "system-selected best"
12. Optional: Human feedback loop:
    - Pause for manual review
    - Accept feedback via CLI
    - Incorporate feedback into next iteration
```

**Workflow 3: Integrated Feedback Loop (Story 9.3)**

```
1. User provides starting prompt (text or image)
2. CLI tool loads prompt and initializes feedback loop directory
3. Determine workflow mode (full, image-only, video-only, prompt-only)
4. Stage 1: Image Prompt Feedback Loop (if workflow includes images):
   a. Call enhance_image_prompt.py (Epic 8, Story 8.1)
   b. Save outputs to stage_01_image_prompt/
   c. Get final enhanced image prompt
   d. If interactive: Pause for feedback
5. Stage 2: Image Generation Feedback Loop (if workflow includes images):
   a. Call generate_images.py (Epic 8, Story 8.2)
   b. Save outputs to stage_02_image_generation/
   c. Get best image candidate
   d. If interactive: Pause for feedback
6. Stage 3: Storyboard Creation (optional, if multi-clip):
   a. Call create_storyboard.py (Epic 8, Story 8.3)
   b. Save outputs to stage_03_storyboard/
   c. Get storyboard with start/end frames
7. Stage 4: Video Prompt Feedback Loop:
   a. Call enhance_video_prompt.py (Story 9.1)
   b. Save outputs to stage_04_video_prompt/
   c. Get final enhanced video prompt
   d. If interactive: Pause for feedback
8. Stage 5: Video Generation Feedback Loop:
   a. Call generate_videos.py (Story 9.2)
   b. Use best image from Stage 2 (if image-to-video mode)
   c. Use storyboard from Stage 3 (if storyboard mode)
   d. Save outputs to stage_05_video_generation/
   e. Get best video candidate
   f. If interactive: Pause for feedback
9. Generate workflow summary:
   a. Collect all intermediate outputs
   b. Collect all scores and metrics
   c. Calculate end-to-end metrics (total cost, total time, quality scores at each stage)
   d. Save workflow_summary.json
10. Print workflow summary to console:
    - Final outputs (best image, best video)
    - Quality scores at each stage
    - Cost breakdown
    - File paths for manual review
11. Save complete workflow trace with all stages
```

**Integration Points:**

- Story 9.1 → Story 9.2: Enhanced prompts from `enhance_video_prompt.py` used as input to `generate_videos.py`
- Epic 8 → Story 9.2: Hero frames from `generate_images.py` and storyboards from `create_storyboard.py` used for image-to-video generation
- Story 7.3 Phase 1: Reuses `prompt_enhancement.py` service pattern, adapting for video-specific enhancement
- Story 7.6: Reuses `quality_control.py` VBench evaluation for automatic video quality scoring
- Story 7.3 Phase 2: Integrates VideoDirectorGPT planning (if available) for shot list and scene dependencies
- Story 8.4: Uses unified narrative documents for storyboard processing to maintain narrative coherence
- Prompt Scoring Guide: All workflows follow guidelines for video prompt structure, film terminology, motion descriptions

## Non-Functional Requirements

### Performance

- **Video Prompt Enhancement Latency**: Video prompt enhancement should complete within 30-90 seconds for typical prompts (3 iterations max, includes VideoDirectorGPT planning if available). Target: <60 seconds for 2-iteration enhancement.
- **Video Generation Latency**: Text-to-video or image-to-video generation via Replicate API should complete within 30-120 seconds per video (varies by model and duration). For 3 attempts: target <10 minutes total.
- **VBench Quality Scoring Latency**: Automatic VBench quality scoring should complete within 20-60 seconds per video (depends on video length and VBench library availability). For 3 videos: target <5 minutes total.
- **Integrated Feedback Loop Latency**: Complete end-to-end workflow (image prompt → image generation → video prompt → video generation) should complete within 20-30 minutes total (including all scoring and optional storyboard creation).
- **Throughput**: CLI tools are single-user developer tools, not production services. No concurrent user requirements.
- **Resource Usage**: VBench evaluation may be CPU/GPU intensive. Videos should be processed sequentially to avoid memory issues. Consider batch processing optimizations if VBench library supports it.

### Security

- **API Key Management**: All API keys (OpenAI, Replicate) must be stored in environment variables or `.env` file, never hardcoded. Follow existing `app/core/config.py` pattern.
- **File System Access**: CLI tools only write to `backend/output/` directory structure. No access to system directories or user files outside project.
- **Input Validation**: All user inputs (prompts, file paths, image paths) must be validated to prevent path traversal attacks or injection vulnerabilities.
- **No Authentication Required**: CLI tools are developer tools run locally, no user authentication or access control needed.
- **Sensitive Data**: Generated videos and prompts may contain sensitive content. No automatic sharing or cloud uploads (local disk only).

### Reliability/Availability

- **Error Handling**: All CLI tools must handle API failures gracefully with clear error messages. Retry logic for transient failures (rate limits, network issues).
- **Fallback Models**: Video generation should support fallback models if primary model fails (similar to existing video generation service pattern).
- **Partial Failure Recovery**: If VBench scoring fails for some videos, tool should continue and report which videos couldn't be scored. If VBench library unavailable, use fallback metrics from quality_control.py.
- **Output Preservation**: All outputs (trace files, videos, metadata) must be saved even if tool encounters errors mid-execution.
- **Checkpoint/Resume**: Integrated feedback loop should support checkpoint/resume functionality if workflow is interrupted.
- **Availability**: CLI tools are developer tools, not production services. No uptime requirements. Tools should be reliable for local development use.

### Observability

- **Logging**: All CLI tools must support verbose logging mode (`--verbose` flag) with detailed progress information (API calls, VBench scoring steps, file operations).
- **Trace Files**: Complete transparency through trace files:
  - Video prompt enhancement: All prompt versions, scores, iteration history, VideoDirectorGPT plan
  - Video generation: All prompts, videos, VBench scores (all 16 dimensions), costs, timestamps
  - Integrated feedback loop: All stages, intermediate outputs, scores, metrics
- **Console Output**: Clear, formatted console output showing:
  - Progress indicators for long-running operations (video generation, VBench scoring)
  - Final results with VBench scores and rankings
  - File paths for manual viewing
  - Error messages with actionable guidance
- **Cost Tracking**: All API calls (OpenAI, Replicate) must be logged with cost estimates in trace files and console output.
- **Performance Metrics**: Log timing information for each major operation (enhancement, generation, VBench scoring) to identify bottlenecks.

## Dependencies and Integrations

**External Dependencies:**

1. **Python Packages** (add to `backend/requirements.txt`):
   - `openai>=1.0.0` - OpenAI API client for prompt enhancement
   - `replicate>=0.25.0` - Replicate API client for video generation (text-to-video and image-to-video models)
   - `click>=8.1.0` - CLI argument parsing (or argparse from stdlib)
   - `requests>=2.31.0` - HTTP requests for downloading videos
   - `opencv-python>=4.8.0` - Video processing for VBench evaluation (if fallback metrics used)

2. **External APIs**:
   - **OpenAI API**: GPT-4-turbo for prompt enhancement agents (requires API key)
   - **Replicate API**: Kling, Wan, PixVerse, or other text-to-video/image-to-video models (requires API token)

3. **VBench Library** (when available):
   - **VBench**: Video quality evaluation library (Vchitect/VBench on GitHub)
   - **Status**: Currently using fallback metrics from `quality_control.py`, but structure ready for VBench integration
   - **Note**: VBench library integration is pending (see `app/services/pipeline/quality_control.py`)

**Internal Dependencies:**

1. **Existing Services** (reuse patterns):
   - `app/services/pipeline/prompt_enhancement.py` - Two-agent pattern (Story 7.3 Phase 1)
   - `app/services/pipeline/image_prompt_enhancement.py` - Image prompt enhancement pattern (Story 8.1)
   - `app/services/pipeline/quality_control.py` - VBench evaluation (Story 7.6) - **CRITICAL**: Reuse existing VBench integration
   - `app/core/config.py` - Configuration management for API keys
   - `app/services/pipeline/scene_planning.py` - Scene planning for VideoDirectorGPT (if Story 7.3 Phase 2 available)

2. **Epic 8 Dependencies** (must be complete):
   - `app/services/pipeline/image_prompt_enhancement.py` - Image prompt enhancement (Story 8.1)
   - `app/services/pipeline/image_generation.py` - Image generation (Story 8.2)
   - `app/services/pipeline/storyboard_service.py` - Storyboard creation (Story 8.3)
   - `app/services/pipeline/storyboard_prompt_enhancement.py` - Storyboard prompt enhancement (Story 8.3)
   - `backend/enhance_image_prompt.py` - CLI tool (Story 8.1)
   - `backend/generate_images.py` - CLI tool (Story 8.2)
   - `backend/create_storyboard.py` - CLI tool (Story 8.3)

3. **Project Structure**:
   - `backend/output/` directory structure for organizing outputs
   - Existing logging infrastructure (`app/core/logging.py`)

**Version Constraints:**

- Python 3.11+ (matches existing backend requirements)
- All dependencies should be compatible with existing `requirements.txt` versions
- VBench library: Install from GitHub when available, use fallback metrics until then

## Acceptance Criteria (Authoritative)

**Story 9.1: Video Prompt Feedback Loop CLI**

1. **Given** a basic video prompt file or stdin input
   **When** I run `python enhance_video_prompt.py prompt.txt --video-mode`
   **Then** the CLI tool:
   - Uses Agent 1 (Video Director) to enhance prompt with camera framing/movement, action beats, timing cues, lighting, color palette, motion intensity, temporal continuity hints
   - Uses Agent 2 (Prompt Engineer) to critique and score on 6 dimensions (0-100 each): Completeness, Specificity, Professionalism, Cinematography, Temporal Coherence, Brand Alignment
   - Iterates between agents (max 3 rounds) until score threshold met or convergence detected
   - Applies VideoDirectorGPT-style enhancements (if Story 7.3 Phase 2 available): Shot list, scene dependencies, narrative flow, consistency groupings
   - Saves all prompt versions to `output/video_prompt_traces/{timestamp}/` with numbered files
   - Saves `prompt_trace_summary.json` with scores, iterations, timestamps, VideoDirectorGPT plan
   - Prints enhancement results to console with scores and iteration history
   - Supports stdin input: `echo "prompt" | python enhance_video_prompt.py -`
   - Supports custom output directories: `--output-dir ./my_traces`
   - Supports iteration control: `--max-iterations 5 --threshold 90`
   - For image-to-video mode: Enhances motion prompts with camera movement, motion intensity, frame rate considerations, negative prompts

2. **Given** prompt enhancement follows Prompt Scoring Guide guidelines
   **Then** enhanced prompts:
   - Structure like one-sentence screenplay (subject → action → setting → style → mood)
   - Use film terminology for clarity
   - Limit to one scene or action per prompt
   - Use visual language (describe what camera sees)
   - Specify camera framing, depth of field, action beats, lighting, palette

3. **Given** I have a storyboard JSON file from Story 8.3 (`storyboard_metadata.json`)
   **When** I run `python enhance_video_prompt.py --storyboard storyboard_metadata.json`
   **Then** the CLI tool:
   - Loads the storyboard JSON file and parses clip information
   - Loads the unified narrative document (from `unified_narrative_path` in storyboard metadata) to use as narrative context
   - For each clip in the storyboard:
     - Extracts the clip's `motion_description` as the base motion prompt
     - Extracts camera metadata: `camera_movement`, `shot_size`, `perspective`, `lens_type`
     - Uses start/end frame paths as context (for image-to-video generation)
     - Uses unified narrative document as context to ensure motion prompts maintain story coherence, follow emotional arc progression, apply consistent visual progression strategy, create smooth narrative transitions
     - Enhances the motion prompt using two-agent feedback loop (per clip) with narrative context integration
     - Iterates (max 3 rounds) until score threshold met or convergence detected
     - Generates negative prompts for unwanted motion
   - Saves enhanced motion prompts per clip with per-clip trace files
   - Saves `storyboard_enhanced_motion_prompts.json` with all clips' enhanced prompts and scores

**Story 9.2: Video Generation Feedback Loop CLI**

4. **Given** an enhanced video prompt OR hero frame + motion prompt OR storyboard
   **When** I run `python generate_videos.py enhanced_prompt.txt --num-attempts 3`
   **Then** the CLI tool:
   - Calls Replicate API (text-to-video or image-to-video model) to generate 3 video attempts
   - All videos follow the enhanced prompt and settings
   - Automatically scores each video using VBench (all 16 dimensions via quality_control.py)
   - Saves all videos to `output/video_generations/{timestamp}/` numbered by quality rank
   - Saves metadata JSON for each video with VBench scores, prompt, model, settings
   - Saves `generation_trace.json` with all prompts, videos, VBench scores (all 16 dimensions), costs, timestamps, hero frame path (if image-to-video), storyboard references (if used)
   - Prints ranked list to console with top video highlighted, VBench score breakdown, file paths, cost summary
   - Automatically selects top-scoring video as "system-selected best"
   - Supports custom output directory: `--output-dir ./my_videos`
   - Supports image-to-video mode: `--image-to-video --hero-frame path/to/image.png --motion-prompt "camera pans left"`
   - Supports storyboard mode: `--storyboard path/to/storyboard.json`
   - Supports negative prompts: `--negative-prompt "jerky, flicker, inconsistent"`
   - Supports human feedback: Pause for manual review, accept feedback via CLI, incorporate into next iteration

**Story 9.3: Integrated Feedback Loop CLI**

5. **Given** a starting prompt (text or image)
   **When** I run `python feedback_loop.py start_prompt.txt --workflow full`
   **Then** the CLI tool orchestrates complete workflow:
   - Stage 1: Image Prompt Feedback Loop (Story 8.1) - enhances prompt, saves trace files
   - Stage 2: Image Generation Feedback Loop (Story 8.2) - generates images, scores with PickScore/CLIP/VQAScore/Aesthetic, selects best
   - Stage 3: Storyboard Creation (Story 8.3, optional) - creates start/end frames for clips
   - Stage 4: Video Prompt Feedback Loop (Story 9.1) - enhances video/motion prompt, saves trace files
   - Stage 5: Video Generation Feedback Loop (Story 9.2) - generates videos, scores with VBench, selects best
   - Saves complete workflow trace to `output/feedback_loops/{timestamp}/` with all intermediate outputs, scores, metrics, `workflow_summary.json`
   - Prints workflow summary: final outputs (best image, best video), quality scores at each stage, cost breakdown, file paths
   - Supports partial workflows: `--workflow image-only`, `--workflow video-only`, `--workflow prompt-only`
   - Supports iteration control: `--max-iterations-image 3`, `--max-iterations-video 3`, `--num-image-variations 8`, `--num-video-attempts 3`
   - Supports human feedback: Pauses after each stage, accepts feedback via CLI, incorporates into next iteration
   - Supports checkpoint/resume: `--resume PATH` to resume from interruption

## Traceability Mapping

| AC # | Acceptance Criteria | Spec Section | Component/Service | Test Idea |
|------|---------------------|--------------|-------------------|-----------|
| 1 | Video prompt enhancement CLI with two-agent feedback loops + VideoDirectorGPT | Detailed Design → Services → `video_prompt_enhancement.py`, Workflows → Workflow 1 | `backend/enhance_video_prompt.py`, `app/services/pipeline/video_prompt_enhancement.py` | Unit test: Two-agent iteration loop, verify prompt enhancement adds camera/motion details, verify scoring on 6 dimensions, verify VideoDirectorGPT integration (if available) |
| 1 | Trace file generation and console output | Detailed Design → Data Models → File Structure, Workflows → Workflow 1 | `backend/enhance_video_prompt.py` | Integration test: Run CLI with sample prompt, verify trace files created with correct structure (including VideoDirectorGPT plan), verify console output format |
| 1 | CLI options (stdin, output-dir, max-iterations, threshold, image-to-video mode) | Detailed Design → APIs → CLI Interface → `enhance_video_prompt.py` | `backend/enhance_video_prompt.py` | Unit test: Test argparse/click options, test stdin input, test custom output directory, test image-to-video motion prompt mode |
| 2 | Prompt Scoring Guide compliance | Detailed Design → Services → `video_prompt_enhancement.py`, Objectives → In-Scope | `app/services/pipeline/video_prompt_enhancement.py` | Unit test: Verify enhanced prompts include camera/motion cues, follow screenplay structure, use film terminology |
| 3 | Storyboard processing mode with unified narrative context | Detailed Design → Services → `video_prompt_enhancement.py`, Workflows → Workflow 1 | `backend/enhance_video_prompt.py`, `app/services/pipeline/video_prompt_enhancement.py` | Integration test: Run CLI with storyboard JSON, verify unified narrative loaded, verify per-clip enhancement with narrative context, verify storyboard_enhanced_motion_prompts.json created |
| 4 | Video generation with automatic VBench scoring | Detailed Design → Services → `video_generation_cli.py`, `video_quality_scoring.py`, Workflows → Workflow 2 | `backend/generate_videos.py`, `app/services/pipeline/video_generation_cli.py`, `app/services/pipeline/video_quality_scoring.py` | Integration test: Generate 3 videos, verify all VBench dimensions computed (via quality_control.py), verify ranking by overall score |
| 4 | Replicate API integration (text-to-video and image-to-video) | Detailed Design → APIs → External API Integrations → Replicate API | `app/services/pipeline/video_generation_cli.py` | Integration test: Call Replicate API with test prompt (text-to-video), call with hero frame + motion prompt (image-to-video), verify video download, verify error handling and retry logic |
| 4 | Generation trace and metadata files | Detailed Design → Data Models → File Structure → Video Generation Directory | `backend/generate_videos.py` | Integration test: Verify `generation_trace.json` contains all prompts, videos, VBench scores (all 16 dimensions), costs, timestamps, hero frame path (if image-to-video), storyboard references (if used) |
| 4 | CLI options (num-attempts, image-to-video, storyboard, negative-prompt, output-dir) | Detailed Design → APIs → CLI Interface → `generate_videos.py` | `backend/generate_videos.py` | Unit test: Test all CLI options, verify image-to-video mode works with hero frame, verify storyboard mode integration, verify negative prompts passed to API |
| 5 | Integrated feedback loop orchestration | Detailed Design → Services → `feedback_loop_orchestrator.py`, Workflows → Workflow 3 | `backend/feedback_loop.py`, `app/services/pipeline/feedback_loop_orchestrator.py` | Integration test: Run full workflow, verify all stages execute in order, verify intermediate outputs saved, verify workflow_summary.json contains end-to-end metrics |
| 5 | Partial workflows and iteration control | Detailed Design → Services → `feedback_loop_orchestrator.py`, Workflows → Workflow 3 | `backend/feedback_loop.py` | Integration test: Test `--workflow image-only`, `--workflow video-only`, `--workflow prompt-only`, verify iteration controls work correctly |
| 5 | Human-in-the-loop feedback and checkpoint/resume | Detailed Design → Services → `feedback_loop_orchestrator.py`, Workflows → Workflow 3 | `backend/feedback_loop.py` | Integration test: Test interactive mode with feedback prompts, test checkpoint creation and resume functionality |
| All | Performance requirements (latency targets) | Non-Functional Requirements → Performance | All services | Performance test: Measure video prompt enhancement (<60s), video generation (<10min for 3 videos), VBench scoring (<5min for 3 videos), integrated workflow (<30min) |
| All | Error handling and retry logic | Non-Functional Requirements → Reliability/Availability | All services | Integration test: Simulate API failures, verify retry logic, verify graceful error messages, verify partial failure recovery, verify VBench fallback metrics if library unavailable |
| All | Logging and observability | Non-Functional Requirements → Observability | All CLI tools | Integration test: Run with `--verbose`, verify detailed logging, verify cost tracking in trace files, verify VBench score logging |

## Risks, Assumptions, Open Questions

**Risks:**

1. **Risk: VBench Library Availability**
   - **Description**: VBench library (Vchitect/VBench) may not be easily available or may require significant setup
   - **Impact**: Medium - Core functionality of Story 9.2 depends on VBench scoring, but fallback metrics exist in quality_control.py
   - **Mitigation**: 
     - Use existing fallback metrics from `quality_control.py` (Story 7.6) until VBench library available
     - Structure code to easily swap in VBench when library becomes available
     - Document VBench setup requirements clearly
     - Test with fallback metrics to ensure functionality works

2. **Risk: Replicate API Model Availability**
   - **Description**: Kling, Wan, PixVerse, or preferred text-to-video/image-to-video models may not be available on Replicate, or API may change
   - **Impact**: High - Blocks video generation functionality
   - **Mitigation**: 
     - Support multiple model options with fallback chain
     - Test with alternative models (other text-to-video or image-to-video models on Replicate)
     - Follow same pattern as existing video generation service (fallback models)
     - Monitor Replicate API changes and adapt as needed

3. **Risk: VBench Scoring Performance**
   - **Description**: Running VBench evaluation on 3 videos may be slow (>5 minutes target), especially if library unavailable and using fallback metrics
   - **Impact**: Medium - Affects developer experience and iteration speed
   - **Mitigation**: 
     - Use existing optimized fallback metrics from quality_control.py (frame sampling, efficient processing)
     - Consider GPU acceleration if available for VBench library
     - Make scoring optional with `--skip-scoring` flag for faster iteration
     - Process videos sequentially to avoid memory issues

4. **Risk: Cost Overruns**
   - **Description**: Generating 3 videos + prompt enhancement iterations + image generation (if full workflow) may exceed cost expectations
   - **Impact**: Low - Developer tools, not production, but still need cost awareness
   - **Mitigation**: 
     - Clear cost tracking in trace files and console output
     - Support `--num-attempts 1` to reduce default from 3
     - Document expected costs per operation
     - Warn users if costs exceed thresholds

5. **Risk: Epic 8 Dependencies**
   - **Description**: Story 9.3 (Integrated Feedback Loop) depends on all Epic 8 stories being complete
   - **Impact**: High - Blocks Story 9.3 if Epic 8 not complete
   - **Mitigation**: 
     - Story 9.1 and 9.2 can proceed independently (only depend on Story 8.1 pattern, not full Epic 8)
     - Story 9.3 can be implemented incrementally (support partial workflows even if Epic 8 not complete)
     - Document dependencies clearly

**Assumptions:**

1. **Assumption**: Story 7.3 Phase 1 (Two-Agent Prompt Enhancement) is complete and `prompt_enhancement.py` service pattern is available for reuse
   - **Validation**: Verify `app/services/pipeline/prompt_enhancement.py` exists and follows two-agent pattern
   - **If False**: May need to implement two-agent pattern from scratch for video-specific enhancement

2. **Assumption**: Story 7.6 (VBench Integration) is complete and `quality_control.py` provides `evaluate_vbench()` function
   - **Validation**: Verify `app/services/pipeline/quality_control.py` exists and provides VBench evaluation (with fallback metrics)
   - **If False**: May need to implement VBench evaluation from scratch

3. **Assumption**: Story 8.1 (Image Prompt Enhancement) is complete and pattern can be reused
   - **Validation**: Verify `app/services/pipeline/image_prompt_enhancement.py` exists
   - **If False**: Story 9.1 can still proceed but may need to implement image prompt enhancement pattern

4. **Assumption**: VideoDirectorGPT planning (Story 7.3 Phase 2) may not be complete, but basic scene planning is available
   - **Validation**: Check if `app/services/pipeline/scene_planning.py` supports VideoDirectorGPT or basic planning
   - **If False**: Video prompt enhancement will work without VideoDirectorGPT planning (optional feature)

5. **Assumption**: Replicate API supports text-to-video and image-to-video models with similar API patterns
   - **Validation**: Test Replicate API with Kling/Wan/PixVerse models, verify API patterns match existing video generation service
   - **If False**: Adapt API integration patterns as needed

6. **Assumption**: Story 8.3 and 8.4 are complete (storyboard service and unified narrative generation)
   - **Validation**: Verify `app/services/pipeline/storyboard_service.py` and unified narrative generation exist
   - **If False**: Storyboard processing mode in Story 9.1 will be blocked until Epic 8 complete

**Open Questions:**

1. **Question**: Should VBench scoring be optional or always-on?
   - **Decision Needed**: Default behavior for `generate_videos.py` - always score or require `--score` flag?
   - **Recommendation**: Always-on by default (core feature), but support `--skip-scoring` for faster iteration

2. **Question**: What weights should be used for overall VBench quality score calculation?
   - **Decision Needed**: Relative importance of temporal quality vs frame-wise quality vs text-video alignment
   - **Recommendation**: Use existing weights from quality_control.py, or: Temporal 40%, Frame-wise 35%, Text-Video Alignment 25% (adjust based on validation)

3. **Question**: Should integrated feedback loop support parallel execution of stages?
   - **Decision Needed**: Can image generation and video prompt enhancement run in parallel, or must be sequential?
   - **Recommendation**: Sequential by default (simpler, clearer dependencies), but consider parallel optimization for future

4. **Question**: How should checkpoint/resume work for integrated feedback loop?
   - **Decision Needed**: What state needs to be saved, how to resume, what happens to intermediate outputs?
   - **Recommendation**: Save workflow state JSON after each stage, include all intermediate outputs paths, resume from last completed stage

## Test Strategy Summary

**Test Levels:**

1. **Unit Tests** (pytest):
   - **`video_prompt_enhancement.py`**: Test two-agent iteration loop, prompt enhancement logic, scoring calculation (6 dimensions), convergence detection, VideoDirectorGPT integration (if available), image-to-video motion prompt enhancement, storyboard processing with unified narrative
   - **`video_generation_cli.py`**: Test Replicate API integration (mocked), video download, file organization, metadata generation, text-to-video and image-to-video modes, storyboard mode
   - **`video_quality_scoring.py`**: Test VBench integration wrapper, verify calls to quality_control.py evaluate_vbench(), test overall score calculation, test ranking logic
   - **`feedback_loop_orchestrator.py`**: Test workflow orchestration logic, stage sequencing, checkpoint/resume functionality, human feedback integration
   - **CLI tools**: Test argument parsing, stdin input handling, file I/O, error handling

2. **Integration Tests** (pytest):
   - **End-to-end video prompt enhancement**: Run `enhance_video_prompt.py` with sample prompt, verify trace files created (including VideoDirectorGPT plan if available), verify console output
   - **End-to-end video generation**: Run `generate_videos.py` with enhanced prompt (text-to-video), verify videos generated, verify VBench scoring (via quality_control.py), verify ranking
   - **End-to-end image-to-video generation**: Run `generate_videos.py` with hero frame + motion prompt, verify image-to-video mode works, verify VBench scoring
   - **End-to-end storyboard processing**: Run `enhance_video_prompt.py` with storyboard JSON, verify unified narrative loaded, verify per-clip enhancement, verify storyboard_enhanced_motion_prompts.json
   - **End-to-end integrated feedback loop**: Run `feedback_loop.py` with starting prompt, verify all stages execute, verify workflow_summary.json created, verify checkpoint/resume
   - **API integration**: Test Replicate API calls (with test API key or mocked), test OpenAI API calls (with test key or mocked)
   - **VBench integration**: Test VBench evaluation via quality_control.py with sample videos (may require longer test time, use fallback metrics if VBench library unavailable)

3. **Manual Testing** (Developer Workflows):
   - **CLI usability**: Test all CLI options, verify help text, verify error messages
   - **Output verification**: Manually inspect generated videos, trace files, metadata JSON, VBench scores
   - **Performance validation**: Measure actual latencies, verify they meet targets
   - **Cost validation**: Run full workflows, verify cost tracking accuracy
   - **Human feedback workflow**: Test interactive mode, verify feedback prompts, verify feedback incorporation

**Test Coverage Goals:**

- **Unit tests**: >80% code coverage for all service modules
- **Integration tests**: Cover all three CLI tools end-to-end with sample inputs
- **Critical paths**: 100% coverage for prompt enhancement iteration loop, VBench scoring integration, video ranking, workflow orchestration

**Test Frameworks:**

- **pytest**: Primary testing framework (matches existing backend test structure)
- **pytest-mock**: For mocking external APIs (OpenAI, Replicate)
- **pytest-asyncio**: For async service functions (if needed)
- **pytest-cov**: For code coverage reporting

**Test Data:**

- **Sample prompts**: Create test prompts covering various scenarios (simple, complex, with/without brand guidelines, motion prompts for image-to-video)
- **Sample videos**: Use pre-generated test videos for VBench scoring tests (avoid generating during tests to save time/cost)
- **Sample images**: Use pre-generated hero frame images for image-to-video tests
- **Sample storyboards**: Use pre-generated storyboard JSON files for storyboard processing tests
- **Mock API responses**: Create mock responses for OpenAI and Replicate APIs to avoid API costs during testing

**Edge Cases:**

- **Empty or invalid prompts**: Test error handling
- **API failures**: Test retry logic and graceful degradation
- **VBench library unavailable**: Test fallback metrics from quality_control.py
- **Large prompts**: Test with very long prompts (token limits)
- **Many attempts**: Test with `--num-attempts 10` to verify performance
- **Missing hero frames**: Test image-to-video mode error handling
- **Missing storyboard files**: Test storyboard mode error handling
- **Workflow interruption**: Test checkpoint/resume functionality
- **Concurrent runs**: Test multiple CLI tools running simultaneously (if applicable)

**Performance Benchmarks:**

- **Video prompt enhancement**: <60 seconds for 2-iteration enhancement (target)
- **Video generation**: <10 minutes for 3 videos (target)
- **VBench scoring**: <5 minutes for 3 videos (target)
- **Integrated feedback loop**: <30 minutes for complete workflow (target)

**Test Execution:**

- **Local development**: Run unit and integration tests before committing
- **CI/CD**: Add tests to existing test suite (if CI pipeline exists)
- **Manual validation**: Developer runs full CLI workflows with real APIs before marking story complete
