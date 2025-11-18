# Story 9.3: Integrated Feedback Loop CLI

Status: drafted

## Story

As a **developer**,  
I want a unified CLI tool that orchestrates the complete feedback loop workflow,  
So that I can rapidly iterate through the entire pipeline: image prompt → image generation → video prompt → video generation.

## Acceptance Criteria

1. **Given** I have a starting prompt (text or image)  
   **When** I run `python feedback_loop.py start_prompt.txt --workflow full`  
   **Then** the CLI tool orchestrates the complete workflow:
   - **Stage 1: Image Prompt Feedback Loop** (Story 8.1):
     - Calls `enhance_image_prompt.py` (or service directly)
     - Enhances prompt using two-agent approach
     - Saves trace files
     - Outputs final enhanced image prompt
   - **Stage 2: Image Generation Feedback Loop** (Story 8.2):
     - Calls `generate_images.py` (or service directly) with enhanced image prompt
     - Generates multiple image variations (default: 8, configurable)
     - Scores images using PickScore, CLIP-Score, VQAScore, Aesthetic
     - Selects best image candidate
     - Saves images and scores
   - **Stage 3: Storyboard Creation** (Story 8.3, optional):
     - Calls `create_storyboard.py` (or service directly) with best image
     - Creates start/end frames for video clips (if multi-clip)
     - Saves storyboard with metadata
   - **Stage 4: Video Prompt Feedback Loop** (Story 9.1):
     - Calls `enhance_video_prompt.py` (or service directly) with storyboard (if available) or enhanced image prompt
     - Enhances video/motion prompt using two-agent approach + VideoDirectorGPT
     - Saves trace files
     - Outputs final enhanced video prompt (or storyboard_enhanced_motion_prompts.json if storyboard mode)
   - **Stage 5: Video Generation Feedback Loop** (Story 9.2):
     - Calls `generate_videos.py` (or service directly) with enhanced video prompt or storyboard
     - Generates multiple video attempts (default: 3, configurable)
     - Scores videos using VBench
     - Selects best video candidate
     - Saves videos and scores

2. **Given** the workflow completes
   **Then** the CLI:
   - Saves complete workflow trace to `output/feedback_loops/{timestamp}/`:
     - All intermediate outputs (prompts, images, videos)
     - All scores and metrics at each stage
     - Complete iteration history
     - `workflow_summary.json` with end-to-end metrics:
       - Total cost (sum of all stages)
       - Total time (sum of all stages)
       - Quality scores at each stage (image prompt score, image quality scores, video prompt scores, VBench scores)
       - Best outputs: best image path, best video path(s)
       - File paths for all intermediate outputs
   - Prints workflow summary to console:
     - Final outputs (best image, best video)
     - Quality scores at each stage
     - Cost breakdown per stage
     - File paths for manual review
     - Total workflow time

3. **Given** I want to run partial workflows
   **Then** the CLI supports:
   - `--workflow image-only`: Stops after image generation (Stages 1-2)
   - `--workflow video-only`: Starts from existing image (skips Stages 1-2, requires `--input-image PATH`)
   - `--workflow prompt-only`: Just prompt enhancement (Stage 1 only)
   - `--workflow full`: Complete workflow (Stages 1-5, default)

4. **Given** I want to control iterations
   **Then** the CLI supports:
   - `--max-iterations-image N` (default: 3, image prompt iterations)
   - `--max-iterations-video N` (default: 3, video prompt iterations)
   - `--num-image-variations N` (default: 8, image generation count)
   - `--num-video-attempts N` (default: 3, video generation count)
   - `--threshold-image F` (default: 85.0, image prompt score threshold)
   - `--threshold-video F` (default: 85.0, video prompt score threshold)

5. **Given** I want human-in-the-loop feedback
   **Then** the CLI:
   - Supports `--interactive` flag to enable human feedback
   - Pauses after image generation for manual review
   - Pauses after video generation for manual review
   - Accepts feedback via CLI prompts:
     - "Continue to next stage? (y/n)"
     - "Regenerate images with feedback? (y/n)"
     - "Regenerate videos with feedback? (y/n)"
   - Incorporates feedback into next iteration (if regenerating)
   - Saves feedback to workflow trace

6. **Given** the workflow provides transparency
   **Then** it:
   - Logs all prompts, scores, and outputs at each stage
   - Saves all files for manual review
   - Provides complete trace of decision-making process
   - Tracks cost at each stage (image prompt enhancement, image generation, video prompt enhancement, video generation)
   - Supports verbose logging: `--verbose` flag

7. **Given** I want to resume from interruption
   **Then** the CLI:
   - Supports `--resume PATH` to resume from checkpoint
   - Saves checkpoint after each stage completion
   - Checkpoint file contains: current stage, intermediate outputs, state
   - Resumes from last completed stage
   - Validates checkpoint file integrity before resuming

## Tasks / Subtasks

- [ ] Task 1: Create feedback loop orchestrator service (AC: #1, #2, #3, #4, #5, #6, #7)
  - [ ] Create `app/services/pipeline/feedback_loop_orchestrator.py` service
  - [ ] Implement workflow orchestration:
    - Stage 1: Image Prompt Enhancement
      - Call `enhance_image_prompt()` from `image_prompt_enhancement.py` (or invoke CLI tool)
      - Pass starting prompt
      - Receive enhanced image prompt and trace files
      - Track cost and time
    - Stage 2: Image Generation
      - Call `generate_images()` from `image_generation.py` (or invoke CLI tool)
      - Pass enhanced image prompt
      - Receive generated images and quality scores
      - Select best image candidate (highest overall quality score)
      - Track cost and time
    - Stage 3: Storyboard Creation (optional)
      - Call `create_storyboard()` from `storyboard_service.py` (or invoke CLI tool)
      - Pass best image and enhanced prompt
      - Receive storyboard with start/end frames
      - Track cost and time
    - Stage 4: Video Prompt Enhancement
      - Call `enhance_video_prompt()` from `video_prompt_enhancement.py` (or invoke CLI tool)
      - Pass storyboard (if available) or enhanced image prompt
      - Receive enhanced video prompt or storyboard_enhanced_motion_prompts.json
      - Track cost and time
    - Stage 5: Video Generation
      - Call `generate_videos()` from `video_generation_cli.py` (or invoke CLI tool)
      - Pass enhanced video prompt or storyboard
      - Receive generated videos and VBench scores
      - Select best video candidate (highest overall VBench score)
      - Track cost and time
  - [ ] Implement partial workflow support:
    - `--workflow image-only`: Execute Stages 1-2 only
    - `--workflow video-only`: Skip Stages 1-2, start from Stage 4 (requires `--input-image PATH`)
    - `--workflow prompt-only`: Execute Stage 1 only
    - `--workflow full`: Execute all stages (default)
  - [ ] Implement iteration control:
    - Pass `--max-iterations-image` to image prompt enhancement
    - Pass `--max-iterations-video` to video prompt enhancement
    - Pass `--num-image-variations` to image generation
    - Pass `--num-video-attempts` to video generation
    - Pass `--threshold-image` to image prompt enhancement
    - Pass `--threshold-video` to video prompt enhancement
  - [ ] Implement human-in-the-loop feedback:
    - Pause after Stage 2 (image generation) if `--interactive`
    - Pause after Stage 5 (video generation) if `--interactive`
    - Accept feedback via CLI prompts
    - Incorporate feedback into next iteration (if regenerating)
    - Save feedback to workflow trace
  - [ ] Implement checkpoint/resume functionality:
    - Save checkpoint after each stage completion
    - Checkpoint file: `workflow_checkpoint.json` with current stage, intermediate outputs, state
    - Resume from checkpoint: Load checkpoint file, validate integrity, resume from last completed stage
  - [ ] Implement workflow trace generation:
    - Collect all intermediate outputs (prompts, images, videos, scores)
    - Collect all scores and metrics at each stage
    - Collect complete iteration history
    - Generate `workflow_summary.json` with end-to-end metrics:
      - Total cost (sum of all stages)
      - Total time (sum of all stages)
      - Quality scores at each stage
      - Best outputs: best image path, best video path(s)
      - File paths for all intermediate outputs
  - [ ] Create `FeedbackLoopResult` class:
    - stages: List[Dict] with stage results (stage_name, outputs, scores, cost, time, trace_path)
    - best_image: Optional[str] (path to best image)
    - best_video: Optional[str] (path to best video, or List[str] for storyboard mode)
    - workflow_summary: Dict (end-to-end metrics)
    - checkpoint_path: Optional[str] (if checkpoint saved)
  - [ ] Unit tests: Workflow orchestration logic, partial workflow support, iteration control, checkpoint/resume, trace generation

- [ ] Task 2: Create CLI tool for feedback loop (AC: #1, #2, #3, #4, #5, #6, #7)
  - [ ] Create `backend/feedback_loop.py` CLI script
  - [ ] Implement argument parsing (argparse or click):
    - Input: starting prompt file path (required for full/image-only/prompt-only workflows)
    - `--workflow MODE` (default: full, options: full, image-only, video-only, prompt-only)
    - `--input-image PATH` (required if --workflow video-only, path to existing image)
    - `--max-iterations-image N` (default: 3, image prompt iterations)
    - `--max-iterations-video N` (default: 3, video prompt iterations)
    - `--num-image-variations N` (default: 8, image generation count)
    - `--num-video-attempts N` (default: 3, video generation count)
    - `--threshold-image F` (default: 85.0, image prompt score threshold)
    - `--threshold-video F` (default: 85.0, video prompt score threshold)
    - `--interactive` (optional flag, enable human-in-the-loop feedback)
    - `--resume PATH` (optional, path to checkpoint file to resume from)
    - `--output-dir DIR` (default: output/feedback_loops/)
    - `--verbose` flag
  - [ ] Implement input validation:
    - Validate prompt file exists (if required for workflow mode)
    - Validate input image exists (if --workflow video-only)
    - Validate checkpoint file exists and is valid (if --resume)
    - Validate mutually exclusive options (--workflow and --resume)
  - [ ] Implement workflow execution:
    - Call orchestrator service with appropriate parameters
    - Handle stage-by-stage execution
    - Handle human feedback pauses (if --interactive)
    - Handle checkpoint saving after each stage
  - [ ] Implement console output formatting:
    - Progress indicators for each stage
    - Stage completion summaries (scores, cost, time)
    - Final workflow summary:
      - Final outputs (best image, best video)
      - Quality scores at each stage
      - Cost breakdown per stage
      - File paths for manual review
      - Total workflow time
  - [ ] Implement checkpoint/resume:
    - Save checkpoint after each stage: `workflow_checkpoint.json`
    - Load checkpoint if --resume provided
    - Validate checkpoint integrity
    - Resume from last completed stage
  - [ ] Implement trace file saving:
    - Save all intermediate outputs to organized directory structure
    - Save `workflow_summary.json` with end-to-end metrics
    - Save `workflow_trace.json` with complete trace (all stages, outputs, scores, costs, timestamps)
  - [ ] Unit tests: Argument parsing, input validation, workflow execution, checkpoint/resume, trace file saving, console output formatting
  - [ ] Integration test: End-to-end full workflow, verify all stages execute, verify intermediate outputs saved, verify workflow_summary.json created
  - [ ] Integration test: Partial workflows (image-only, video-only, prompt-only), verify correct stages execute
  - [ ] Integration test: Interactive mode with feedback, verify pauses and feedback acceptance
  - [ ] Integration test: Checkpoint/resume, verify checkpoint saved, verify resume from checkpoint works

- [ ] Task 3: Documentation and testing (All ACs)
  - [ ] Update `backend/requirements.txt` with any new dependencies
  - [ ] Create README or usage documentation for CLI tool
  - [ ] Add integration tests to `backend/tests/test_feedback_loop_cli.py`
  - [ ] Verify error handling for API failures, invalid inputs, missing files, checkpoint corruption, workflow interruption
  - [ ] Performance test: Verify full workflow completes within <30 minutes (target)
  - [ ] Document workflow orchestration patterns and checkpoint/resume behavior

## Dev Notes

### Learnings from Previous Story

**From Story 9.2 (Status: ready-for-dev)**
- **Video Generation CLI Tool**: Story 9.2 creates `backend/generate_videos.py` CLI tool that generates videos with automatic VBench quality scoring. This tool can be invoked directly or its service (`video_generation_cli.py`) can be called programmatically.
- **Video Quality Scoring**: Story 9.2 integrates VBench quality scoring via `quality_control.py`. The `video_quality_scoring.py` wrapper calculates overall quality scores and ranks videos.
- **Storyboard Mode**: Story 9.2 supports storyboard mode, loading `storyboard_enhanced_motion_prompts.json` from Story 9.1 and generating videos per clip using start/end frames.
- **CLI Tool Pattern**: Follow the pattern from `backend/generate_images.py` for CLI structure, argument parsing, trace directory creation, console output formatting.
- **Output Directory Structure**: Use `backend/output/` directory structure with timestamp-based subdirectories. Follow pattern: `output/{tool_name}/{timestamp}/` for organizing outputs.
- **Trace File Pattern**: Save comprehensive trace files (JSON metadata) for transparency. Include all prompts, videos, VBench scores, costs, timestamps.

[Source: docs/sprint-artifacts/9-2-video-generation-feedback-loop-cli.md#Dev-Notes]

**From Story 9.1 (Status: done)**
- **Video Prompt Enhancement CLI Tool**: Story 9.1 creates `backend/enhance_video_prompt.py` CLI tool that enhances video prompts using two-agent feedback loops. This tool can be invoked directly or its service (`video_prompt_enhancement.py`) can be called programmatically.
- **Storyboard Processing Output**: Story 9.1 generates `storyboard_enhanced_motion_prompts.json` when processing storyboards. This JSON includes enhanced motion prompts per clip, start/end frame paths, unified narrative document reference, and scores/iteration history per clip.

[Source: docs/sprint-artifacts/9-1-video-prompt-feedback-loop-cli.md#Dev-Notes]

**From Story 8.2 (Status: done)**
- **Image Generation CLI Tool**: Story 8.2 creates `backend/generate_images.py` CLI tool that generates images with automatic quality scoring. This tool can be invoked directly or its service (`image_generation.py`) can be called programmatically.
- **Image Quality Scoring**: Story 8.2 integrates quality scoring via `image_quality_scoring.py`. Images are ranked by overall quality score and best candidate selected.

[Source: docs/sprint-artifacts/8-2-image-generation-feedback-loop-cli.md#Dev-Notes]

**From Story 8.1 (Status: done)**
- **Image Prompt Enhancement CLI Tool**: Story 8.1 creates `backend/enhance_image_prompt.py` CLI tool that enhances image prompts using two-agent feedback loops. This tool can be invoked directly or its service (`image_prompt_enhancement.py`) can be called programmatically.

[Source: docs/sprint-artifacts/8-1-image-prompt-feedback-loop-cli.md#Dev-Notes]

**From Story 8.3 (Status: done)**
- **Storyboard Creation CLI Tool**: Story 8.3 creates `backend/create_storyboard.py` CLI tool that creates storyboards with start/end frames. This tool can be invoked directly or its service (`storyboard_service.py`) can be called programmatically.

[Source: docs/sprint-artifacts/8-3-storyboard-creation-cli.md#Dev-Notes]

### Architecture Patterns and Constraints

- **Service Integration**: Prefer calling service functions directly (e.g., `enhance_image_prompt()`, `generate_images()`) rather than invoking CLI tools via subprocess. This provides better error handling, state management, and performance. CLI tools can still be used for standalone execution.

- **Workflow Orchestration Pattern**: Create orchestrator service `app/services/pipeline/feedback_loop_orchestrator.py` that:
  - Chains together service calls in sequence
  - Manages workflow state and intermediate outputs
  - Handles checkpoint/resume functionality
  - Supports human-in-the-loop feedback
  - Generates unified trace format
  - [Source: docs/sprint-artifacts/tech-spec-epic-9.md]

- **CLI Tool Pattern**: Follow the pattern established by `backend/generate_images.py`:
  - Standalone Python script in `backend/` directory
  - Uses `argparse` for argument parsing
  - Saves outputs to `backend/output/` directory structure
  - Prints formatted console output with progress and summaries
  - Supports verbose logging mode
  - Supports custom output directories
  - [Source: backend/generate_images.py]

- **Checkpoint/Resume Pattern**: Save checkpoint after each stage completion:
  - Checkpoint file: `workflow_checkpoint.json` with current stage, intermediate outputs, state
  - Resume from checkpoint: Load checkpoint file, validate integrity, resume from last completed stage
  - Handle workflow interruption gracefully
  - [Source: docs/sprint-artifacts/tech-spec-epic-9.md]

- **Configuration Management**: Use `app/core/config.py` for API keys:
  - Access OpenAI API key via `settings.OPENAI_API_KEY` (for prompt enhancement)
  - Access Replicate API token via `settings.REPLICATE_API_TOKEN` (for image/video generation)
  - Follow existing pattern for environment variable loading
  - [Source: backend/app/core/config.py]

- **Output Directory Structure**: Follow existing pattern:
  - `backend/output/feedback_loops/{timestamp}/` for workflow outputs
  - Timestamp format: `YYYYMMDD_HHMMSS` (e.g., `20250117_143022`)
  - Organized subdirectories: `stage_1_image_prompt/`, `stage_2_image_generation/`, `stage_3_storyboard/`, `stage_4_video_prompt/`, `stage_5_video_generation/`
  - Workflow summary: `workflow_summary.json`
  - Workflow trace: `workflow_trace.json`
  - Checkpoint: `workflow_checkpoint.json` (saved after each stage)
  - [Source: docs/sprint-artifacts/tech-spec-epic-9.md]

- **Cost Tracking**: Track cost at each stage:
  - Image prompt enhancement: OpenAI API costs
  - Image generation: Replicate API costs
  - Video prompt enhancement: OpenAI API costs
  - Video generation: Replicate API costs
  - Sum all costs for total workflow cost
  - Include cost breakdown in workflow summary

- **Performance Target**: Full workflow should complete within <30 minutes (target). Log timing information for each stage to identify bottlenecks.

### Project Structure Notes

- **New Service File**: `app/services/pipeline/feedback_loop_orchestrator.py`
  - Follows existing service structure in `app/services/pipeline/`
  - Uses async/await pattern for API calls (where applicable)
  - Imports from `app.core.config` for settings
  - Imports from all Epic 8 and Epic 9 service modules:
    - `app.services.pipeline.image_prompt_enhancement`
    - `app.services.pipeline.image_generation`
    - `app.services.pipeline.storyboard_service`
    - `app.services.pipeline.video_prompt_enhancement`
    - `app.services.pipeline.video_generation_cli`

- **New CLI Tool**: `backend/feedback_loop.py`
  - Standalone script (not part of FastAPI app)
  - Can be run independently: `python feedback_loop.py start_prompt.txt`
  - Uses relative imports to access services: `from app.services.pipeline.feedback_loop_orchestrator import ...`

- **Output Directory**: `backend/output/feedback_loops/`
  - Created automatically if doesn't exist
  - Subdirectories named with timestamps for each run
  - Follows existing `backend/output/` structure

### Testing Standards

- **Unit Tests**: Use pytest framework (matches existing backend test structure)
  - Test orchestrator service: Workflow orchestration logic, partial workflow support, iteration control, checkpoint/resume, trace generation
  - Test CLI argument parsing, input validation, workflow execution, checkpoint/resume, trace file saving
  - Target: >80% code coverage

- **Integration Tests**: End-to-end CLI execution
  - Run full workflow with sample prompt
  - Verify all stages execute in order
  - Verify intermediate outputs saved
  - Verify workflow_summary.json created with end-to-end metrics
  - Test partial workflows (image-only, video-only, prompt-only)
  - Test interactive mode with feedback
  - Test checkpoint/resume functionality
  - Use test API keys or mock responses

- **Performance Tests**: Measure latency
  - Target: <30 minutes for full workflow (target)
  - Log timing information for each stage (generation, scoring, etc.)

### References

- **Epic 9 Tech Spec**: [Source: docs/sprint-artifacts/tech-spec-epic-9.md]
  - Detailed design for feedback loop orchestrator service
  - Acceptance criteria and traceability mapping
  - Non-functional requirements (performance, security, reliability)
  - Workflow orchestration patterns

- **Epic 9 Story Definition**: [Source: docs/epics.md#Story-9.3]
  - Original story acceptance criteria
  - Prerequisites: Story 8.1, Story 8.2, Story 8.3, Story 9.1, Story 9.2
  - Technical notes on orchestrating all CLI tools

- **Existing CLI Tools**: [Source: backend/enhance_image_prompt.py, backend/generate_images.py, backend/create_storyboard.py, backend/enhance_video_prompt.py, backend/generate_videos.py]
  - CLI tool patterns to follow
  - Service integration patterns
  - Output directory structures
  - Trace file formats

- **Existing Services**: [Source: backend/app/services/pipeline/]
  - `image_prompt_enhancement.py` - Image prompt enhancement service
  - `image_generation.py` - Image generation service
  - `storyboard_service.py` - Storyboard creation service
  - `video_prompt_enhancement.py` - Video prompt enhancement service
  - `video_generation_cli.py` - Video generation service (from Story 9.2)

- **Architecture Document**: [Source: docs/architecture.md]
  - Project structure patterns
  - Service organization in `app/services/pipeline/`
  - Configuration management via `app/core/config.py`

## Change Log

- 2025-11-17: Story created with comprehensive acceptance criteria covering full workflow orchestration, partial workflows, iteration control, human-in-the-loop feedback, checkpoint/resume functionality, and complete workflow trace generation.

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

