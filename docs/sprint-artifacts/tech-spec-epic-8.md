# Epic Technical Specification: CLI MVP - Image Generation Feedback Loops

Date: 2025-11-17
Author: BMad
Epic ID: 8
Status: Draft

---

## Overview

Epic 8 establishes CLI-based rapid iteration tools for image prompt enhancement and image generation with automatic quality scoring. This epic enables developers to quickly test and refine image generation workflows before building UI components, following the CLI MVP strategy outlined in the PRD's Hero-Frame Iteration Plan (Section 23.0). The epic implements three CLI tools: (1) `enhance_image_prompt.py` for iterative prompt enhancement using two-agent feedback loops, (2) `generate_images.py` for text-to-image generation with automatic quality scoring (PickScore, CLIP-Score, VQAScore, Aesthetic Predictor), and (3) `create_storyboard.py` for generating start/end frames for video clips. These tools build upon the existing prompt enhancement service pattern from Story 7.3 Phase 1 and integrate with the Prompt Scoring and Optimization Guide to ensure professional-quality outputs. The CLI MVP approach allows rapid validation of feedback loops, scoring mechanisms, and workflow transparency before committing to UI development.

## Objectives and Scope

**In-Scope:**
- CLI tool for iterative image prompt enhancement (`enhance_image_prompt.py`) with two-agent feedback loops (Cinematographer/Creative Director + Prompt Engineer)
- CLI tool for text-to-image generation (`generate_images.py`) with automatic quality scoring using PickScore, CLIP-Score, VQAScore, and LAION Aesthetic Predictor
- CLI tool for storyboard creation (`create_storyboard.py`) generating start/end frames for video clips using VideoDirectorGPT-style planning
- Integration with existing `prompt_enhancement.py` service pattern from Story 7.3 Phase 1
- Automatic quality scoring service (`image_quality_scoring.py`) implementing multiple benchmark metrics
- Trace file generation and logging for transparency (all prompt versions, scores, iterations, metadata)
- Support for stdin input, custom output directories, and configuration flags (max-iterations, threshold, aspect-ratio, seed)
- Directory structure for organizing outputs (`output/image_prompt_traces/`, `output/image_generations/`, `output/storyboards/`)
- Reuse of Prompt Scoring Guide guidelines for prompt structure and enhancement best practices

**Out-of-Scope:**
- UI components for hero-frame gallery, iteration workspace, or quality dashboard (deferred to future UI phase after CLI MVP validation)
- Integration with main web application API endpoints (CLI tools are standalone for developer use)
- Database persistence of CLI-generated images (saved to disk only)
- User authentication or access control for CLI tools (local developer tools)
- Real-time progress updates or webhooks (CLI tools run synchronously)
- Multi-user collaboration features
- Production deployment of CLI tools (developer tools, not production services)

## System Architecture Alignment

This epic extends the existing architecture described in `docs/architecture.md` by adding CLI-based developer tools that operate independently of the main FastAPI web application. The CLI tools follow the same service patterns established in the backend (`app/services/pipeline/`) but execute as standalone Python scripts. The `enhance_image_prompt.py` tool reuses the two-agent prompt enhancement pattern from `app/services/pipeline/prompt_enhancement.py` (Story 7.3 Phase 1), adapting it for image-specific enhancement with cinematography focus. The `generate_images.py` tool integrates with Replicate API for text-to-image generation (SDXL or similar models), following the same API integration patterns used in `app/services/pipeline/video_generation.py` for video models. The quality scoring service (`image_quality_scoring.py`) follows the structure of `app/services/pipeline/quality_control.py` (VBench integration) but implements image-specific metrics (PickScore, CLIP-Score, VQAScore, Aesthetic Predictor). All CLI tools save outputs to the `backend/output/` directory structure, consistent with the existing pipeline's output organization. The tools are designed to be runnable from the command line without requiring the FastAPI server to be running, enabling rapid iteration and testing workflows for developers.

## Detailed Design

### Services and Modules

**Backend Services:**

1. **`app/services/pipeline/image_prompt_enhancement.py`** (New)
   - **Purpose**: Image-specific prompt enhancement service adapting the two-agent pattern for cinematography focus
   - **Responsibilities**:
     - Agent 1 (Cinematographer/Creative Director): Enhances prompts with camera details (body, lens), lighting, composition, film stock references, mood, aspect ratio hints
     - Agent 2 (Prompt Engineer): Critiques and scores prompts on completeness, specificity, professionalism, cinematography, brand alignment
     - Iterative refinement (max 3 rounds) until score threshold met or convergence detected
     - Scoring on 5 dimensions (0-100 each): Completeness, Specificity, Professionalism, Cinematography, Brand Alignment
   - **Inputs**: User prompt (string), max_iterations (int), score_threshold (float), trace_dir (Path)
   - **Outputs**: Enhanced prompt (string), iteration history (List[Dict]), final scores (Dict[str, float])
   - **Dependencies**: OpenAI API (GPT-4), `app/core/config.py` for settings

2. **`app/services/pipeline/image_generation.py`** (New)
   - **Purpose**: Text-to-image generation service using Replicate API (SDXL or similar models)
   - **Responsibilities**:
     - Generate multiple image variations (4-8 default) from enhanced prompt
     - Support aspect ratio control, seed control for reproducibility
     - Download and save generated images to organized directory structure
     - Track generation metadata (prompt, model, seed, timestamps, cost)
   - **Inputs**: Enhanced prompt (string), num_variations (int), aspect_ratio (str), seed (Optional[int])
   - **Outputs**: List of image file paths, metadata JSON files
   - **Dependencies**: Replicate API, `app/core/config.py` for API keys

3. **`app/services/pipeline/image_quality_scoring.py`** (New)
   - **Purpose**: Automatic quality scoring service for generated images using multiple benchmark metrics
   - **Responsibilities**:
     - Compute PickScore (primary): Human preference prediction (0-100)
     - Compute CLIP-Score: Image-text alignment (0-100)
     - Compute VQAScore: Compositional semantic alignment (0-100)
     - Compute Aesthetic Predictor (LAION): Aesthetic quality (1-10 scale)
     - Calculate overall quality score (weighted combination)
     - Rank images by quality score
   - **Inputs**: Image file path (str), prompt text (str)
   - **Outputs**: Quality scores dictionary with all metrics and overall score
   - **Dependencies**: PickScore model (Stability AI), CLIP model (Hugging Face transformers), VQAScore (if available), LAION Aesthetic Predictor

4. **`app/services/pipeline/storyboard_service.py`** (New)
   - **Purpose**: Storyboard creation service generating start/end frames for video clips
   - **Responsibilities**:
     - Use VideoDirectorGPT-style planning (or basic scene planning) to break prompt into clips
     - For each clip, generate start frame and end frame using image generation service
     - Generate motion descriptions (camera movement, subject motion) between start/end
     - Store storyboard metadata (clip descriptions, prompts, motion arcs, shot list)
   - **Inputs**: Video clip prompt (string), num_clips (int), enhance_prompts (bool)
   - **Outputs**: Storyboard directory with start/end frame images and metadata JSON
   - **Dependencies**: `image_prompt_enhancement.py`, `image_generation.py`, scene planning service (if available)

**CLI Tools:**

1. **`backend/enhance_image_prompt.py`** (New)
   - **Purpose**: Standalone CLI tool for iterative image prompt enhancement
   - **Usage**: `python enhance_image_prompt.py prompt.txt [--max-iterations 5] [--threshold 90] [--output-dir ./my_traces]`
   - **Features**: stdin input support, custom output directories, iteration control, verbose logging
   - **Outputs**: Trace files in `output/image_prompt_traces/{timestamp}/` with all prompt versions and scores

2. **`backend/generate_images.py`** (New)
   - **Purpose**: Standalone CLI tool for text-to-image generation with automatic quality scoring
   - **Usage**: `python generate_images.py enhanced_prompt.txt [--num-variations 8] [--aspect-ratio 16:9] [--seed 12345]`
   - **Features**: Automatic quality scoring, ranked output, top 3 highlighting, cost tracking
   - **Outputs**: Images and metadata in `output/image_generations/{timestamp}/`

3. **`backend/create_storyboard.py`** (New)
   - **Purpose**: Standalone CLI tool for creating storyboards (start/end frames) for video clips
   - **Usage**: `python create_storyboard.py clip_prompt.txt [--num-clips 3] [--enhance-prompts] [--output-dir ./my_storyboard]`
   - **Features**: VideoDirectorGPT planning integration, optional prompt enhancement, motion descriptions
   - **Outputs**: Storyboard in `output/storyboards/{timestamp}/` with start/end frames and metadata

### Data Models and Contracts

**Data Structures (Python Classes):**

1. **`ImagePromptEnhancementResult`** (in `image_prompt_enhancement.py`)
   ```python
   class ImagePromptEnhancementResult:
       original_prompt: str
       final_prompt: str
       iterations: List[Dict]  # Each dict: {iteration_num, agent1_output, agent2_output, scores}
       final_score: Dict[str, float]  # {completeness, specificity, professionalism, cinematography, brand_alignment, overall}
       total_iterations: int
   ```

2. **`ImageGenerationResult`** (in `image_generation.py`)
   ```python
   class ImageGenerationResult:
       images: List[ImageMetadata]  # Sorted by quality score (best first)
       generation_trace: Dict  # Complete trace with prompts, scores, costs, timestamps
   
   class ImageMetadata:
       file_path: str
       rank: int
       quality_scores: Dict[str, float]  # {pickscore, clip_score, vqa_score, aesthetic, overall}
       generation_params: Dict  # {prompt, model, seed, aspect_ratio, timestamp}
   ```

3. **`StoryboardResult`** (in `storyboard_service.py`)
   ```python
   class StoryboardResult:
       clips: List[ClipStoryboard]
       metadata: Dict  # {original_prompt, planning_metadata, total_clips, created_at}
   
   class ClipStoryboard:
       clip_number: int
       start_frame_path: str
       end_frame_path: str
       motion_description: str
       camera_movement: str
       prompts: Dict  # {start_prompt, end_prompt, enhanced_prompts}
   ```

**File Structure Contracts:**

1. **Image Prompt Trace Directory** (`output/image_prompt_traces/{timestamp}/`):
   - `00_original_prompt.txt` - Original user input
   - `01_agent1_iteration_1.txt` - First Cinematographer enhancement
   - `02_agent2_iteration_1.txt` - First Prompt Engineer critique + score
   - `03_agent1_iteration_2.txt` - Second enhancement (if iterated)
   - `04_agent2_iteration_2.txt` - Second critique (if iterated)
   - `05_final_enhanced_prompt.txt` - Final enhanced prompt
   - `prompt_trace_summary.json` - Metadata: scores, iterations, timestamps

2. **Image Generation Directory** (`output/image_generations/{timestamp}/`):
   - `image_001.png`, `image_002.png`, etc. (numbered by quality rank)
   - `image_001_metadata.json`, `image_002_metadata.json` (scores, prompt, model, seed)
   - `generation_trace.json` - Complete trace with all prompts, images, scores, costs

3. **Storyboard Directory** (`output/storyboards/{timestamp}/`):
   - `clip_001_start.png`, `clip_001_end.png`
   - `clip_002_start.png`, `clip_002_end.png`
   - `storyboard_metadata.json` - Clip descriptions, prompts, motion descriptions, shot list

### APIs and Interfaces

**External API Integrations:**

1. **Replicate API** (Text-to-Image Models)
   - **Endpoint**: Replicate Python SDK
   - **Models**: SDXL (default), or other text-to-image models available on Replicate
   - **Request**: `replicate.run(model="stability-ai/sdxl", input={"prompt": str, "aspect_ratio": str, "seed": int})`
   - **Response**: Image URL (download required)
   - **Error Handling**: Retry logic with exponential backoff, fallback models if primary fails
   - **Cost Tracking**: Track cost per generation (varies by model)

2. **OpenAI API** (LLM for Prompt Enhancement)
   - **Endpoint**: OpenAI Python SDK
   - **Models**: GPT-4-turbo (default for both agents)
   - **Request**: `openai.ChatCompletion.create(model="gpt-4-turbo", messages=[system_prompt, user_prompt])`
   - **Response**: Enhanced prompt text (Agent 1) or JSON scores/critique (Agent 2)
   - **Error Handling**: Retry logic for rate limits, timeout handling
   - **Cost Tracking**: Track token usage and cost per iteration

3. **PickScore Model** (Quality Scoring)
   - **Source**: Stability AI open-source model
   - **Integration**: Hugging Face transformers or direct model loading
   - **Input**: Image file path, prompt text
   - **Output**: Score (0-100, higher = better human preference prediction)

4. **CLIP Model** (Image-Text Alignment)
   - **Source**: Hugging Face transformers (OpenAI CLIP)
   - **Integration**: `transformers` library
   - **Input**: Image file path, prompt text
   - **Output**: CLIP-Score (0-100, higher = better alignment)

5. **VQAScore** (Compositional Alignment)
   - **Source**: VQAScore model (if available)
   - **Integration**: Hugging Face or direct model loading
   - **Input**: Image file path, prompt text
   - **Output**: VQAScore (0-100, higher = better compositional alignment)

6. **LAION Aesthetic Predictor** (Aesthetic Quality)
   - **Source**: LAION dataset aesthetic predictor
   - **Integration**: Pre-trained model (linear model on CLIP embeddings)
   - **Input**: Image file path
   - **Output**: Aesthetic score (1-10 scale)

**CLI Interface Contracts:**

1. **`enhance_image_prompt.py`**
   ```bash
   enhance_image_prompt.py <input> [OPTIONS]
   
   Arguments:
     input              File path or "-" for stdin
   
   Options:
     --max-iterations N  Maximum iteration rounds (default: 3)
     --threshold F      Score threshold to stop at (default: 85.0)
     --output-dir DIR   Custom output directory (default: output/image_prompt_traces/)
     --creative-model M Model for Cinematographer agent (default: gpt-4-turbo)
     --critique-model M Model for Prompt Engineer agent (default: gpt-4-turbo)
     --verbose          Enable verbose logging
   ```

2. **`generate_images.py`**
   ```bash
   generate_images.py <prompt_file> [OPTIONS]
   
   Arguments:
     prompt_file         Path to enhanced prompt file
   
   Options:
     --num-variations N  Number of image variations (default: 8)
     --aspect-ratio R    Aspect ratio (default: 16:9, options: 1:1, 4:3, 16:9, 9:16)
     --seed N            Seed for reproducibility
     --output-dir DIR    Custom output directory (default: output/image_generations/)
     --model M           Replicate model name (default: stability-ai/sdxl)
     --verbose           Enable verbose logging
   ```

3. **`create_storyboard.py`**
   ```bash
   create_storyboard.py <prompt_file> [OPTIONS]
   
   Arguments:
     prompt_file         Path to video clip prompt file
   
   Options:
     --num-clips N       Number of clips to generate (default: 3)
     --enhance-prompts   Enable prompt enhancement before generation
     --output-dir DIR    Custom output directory (default: output/storyboards/)
     --verbose           Enable verbose logging
   ```

### Workflows and Sequencing

**Workflow 1: Image Prompt Enhancement (Story 8.1)**

```
1. User provides basic image prompt (file or stdin)
2. CLI tool loads prompt and initializes trace directory
3. Quick initial assessment (rule-based scoring)
   - If score >= 75.0: Skip enhancement, return original
   - Else: Proceed to iterative enhancement
4. Iteration Loop (max 3 rounds):
   a. Agent 1 (Cinematographer) enhances prompt:
      - Adds camera details (body, lens, angle)
      - Adds lighting direction and quality
      - Adds composition notes
      - Adds film stock/color science references
      - Adds mood and atmosphere descriptors
      - Adds aspect ratio and stylization hints
   b. Agent 2 (Prompt Engineer) critiques and scores:
      - Scores on 5 dimensions (0-100 each)
      - Provides specific feedback
      - Calculates overall weighted score
   c. Check convergence:
      - If overall score >= threshold: Exit loop
      - If no improvement: Exit loop
      - Else: Continue to next iteration
5. Save all prompt versions to trace files
6. Save metadata JSON with scores and iteration history
7. Print results to console (scores, iteration count, final prompt)
```

**Workflow 2: Image Generation with Quality Scoring (Story 8.2)**

```
1. User provides enhanced prompt file
2. CLI tool loads prompt and initializes output directory
3. Generate multiple image variations (4-8 default):
   a. For each variation:
      - Call Replicate API with prompt, aspect_ratio, seed
      - Download generated image
      - Save image file (numbered: image_001.png, image_002.png, ...)
4. Automatic quality scoring for each image:
   a. Compute PickScore (primary metric)
   b. Compute CLIP-Score (image-text alignment)
   c. Compute VQAScore (compositional alignment)
   d. Compute Aesthetic Predictor (LAION)
   e. Calculate overall quality score (weighted combination)
5. Rank images by overall quality score (best first)
6. Rename/sort images by rank (image_001 = best, image_002 = second-best, ...)
7. Save metadata JSON for each image (scores, prompt, model, seed)
8. Save generation trace JSON (all prompts, images, scores, costs, timestamps)
9. Print results to console:
   - Ranked list with scores
   - Top 3 images highlighted
   - Score breakdown per image
   - File paths for manual viewing
10. Auto-select top-scoring image as "best candidate"
```

**Workflow 3: Storyboard Creation (Story 8.3)**

```
1. User provides video clip prompt file
2. CLI tool loads prompt and initializes storyboard directory
3. Optional: Enhance prompt using Story 8.1 workflow (if --enhance-prompts flag)
4. VideoDirectorGPT-style planning (or basic scene planning):
   a. Break prompt into individual video clips (3-5 clips)
   b. For each clip, generate:
      - Shot list with camera metadata (movement, shot size, perspective, lens)
      - Scene dependencies and narrative flow
      - Consistency groupings (if applicable)
5. For each clip:
   a. Generate start frame prompt (derived from shot list)
   b. Generate end frame prompt (derived from shot list)
   c. Generate motion description (what happens between start/end)
   d. Generate start frame image (using Story 8.2 workflow)
   e. Generate end frame image (using Story 8.2 workflow)
   f. Save start/end frame images (clip_001_start.png, clip_001_end.png, ...)
6. Save storyboard metadata JSON:
   - Clip descriptions
   - Start/end frame prompts
   - Motion descriptions
   - Camera movements
   - Shot list metadata
7. Print storyboard summary to console:
   - List of clips with start/end frame descriptions
   - Motion arcs for each clip
   - File paths for manual viewing
```

**Integration Points:**

- Story 8.1 → Story 8.2: Enhanced prompts from `enhance_image_prompt.py` can be used as input to `generate_images.py`
- Story 8.1 + Story 8.2 → Story 8.3: Both tools are used within `create_storyboard.py` for generating start/end frames
- Story 7.3 Phase 1: Reuses `prompt_enhancement.py` service pattern, adapting for image-specific enhancement
- Prompt Scoring Guide: All workflows follow guidelines for prompt structure, camera cues, lighting cues

## Non-Functional Requirements

### Performance

- **Prompt Enhancement Latency**: Image prompt enhancement should complete within 30-60 seconds for typical prompts (3 iterations max). Target: <45 seconds for 2-iteration enhancement.
- **Image Generation Latency**: Text-to-image generation via Replicate API should complete within 10-30 seconds per image. For 8 variations: target <5 minutes total.
- **Quality Scoring Latency**: Automatic quality scoring (PickScore, CLIP-Score, VQAScore, Aesthetic) should complete within 5-15 seconds per image. For 8 images: target <2 minutes total.
- **Storyboard Generation Latency**: Storyboard creation (3 clips with start/end frames) should complete within 10-15 minutes total (including optional prompt enhancement).
- **Throughput**: CLI tools are single-user developer tools, not production services. No concurrent user requirements.
- **Resource Usage**: Quality scoring models (PickScore, CLIP) should be loaded once and reused across multiple images to minimize memory overhead.

### Security

- **API Key Management**: All API keys (OpenAI, Replicate) must be stored in environment variables or `.env` file, never hardcoded. Follow existing `app/core/config.py` pattern.
- **File System Access**: CLI tools only write to `backend/output/` directory structure. No access to system directories or user files outside project.
- **Input Validation**: All user inputs (prompts, file paths) must be validated to prevent path traversal attacks or injection vulnerabilities.
- **No Authentication Required**: CLI tools are developer tools run locally, no user authentication or access control needed.
- **Sensitive Data**: Generated images and prompts may contain sensitive content. No automatic sharing or cloud uploads (local disk only).

### Reliability/Availability

- **Error Handling**: All CLI tools must handle API failures gracefully with clear error messages. Retry logic for transient failures (rate limits, network issues).
- **Fallback Models**: Image generation should support fallback models if primary model fails (similar to video generation service pattern).
- **Partial Failure Recovery**: If quality scoring fails for some images, tool should continue and report which images couldn't be scored.
- **Output Preservation**: All outputs (trace files, images, metadata) must be saved even if tool encounters errors mid-execution.
- **Availability**: CLI tools are developer tools, not production services. No uptime requirements. Tools should be reliable for local development use.

### Observability

- **Logging**: All CLI tools must support verbose logging mode (`--verbose` flag) with detailed progress information (API calls, scoring steps, file operations).
- **Trace Files**: Complete transparency through trace files:
  - Prompt enhancement: All prompt versions, scores, iteration history
  - Image generation: All prompts, images, scores, costs, timestamps
  - Storyboard: All clips, prompts, motion descriptions, metadata
- **Console Output**: Clear, formatted console output showing:
  - Progress indicators for long-running operations
  - Final results with scores and rankings
  - File paths for manual viewing
  - Error messages with actionable guidance
- **Cost Tracking**: All API calls (OpenAI, Replicate) must be logged with cost estimates in trace files and console output.
- **Performance Metrics**: Log timing information for each major operation (enhancement, generation, scoring) to identify bottlenecks.

## Dependencies and Integrations

**External Dependencies:**

1. **Python Packages** (add to `backend/requirements.txt`):
   - `openai>=1.0.0` - OpenAI API client for prompt enhancement
   - `replicate>=0.25.0` - Replicate API client for image generation
   - `transformers>=4.30.0` - Hugging Face transformers for CLIP model
   - `torch>=2.0.0` - PyTorch for PickScore and CLIP models (if GPU available)
   - `pillow>=10.0.0` - Image processing for quality scoring
   - `numpy>=1.24.0` - Numerical operations for scoring calculations
   - `requests>=2.31.0` - HTTP requests for downloading images
   - `click>=8.1.0` - CLI argument parsing (or argparse from stdlib)

2. **External APIs**:
   - **OpenAI API**: GPT-4-turbo for prompt enhancement agents (requires API key)
   - **Replicate API**: SDXL or other text-to-image models (requires API token)
   - **Hugging Face**: Model downloads for PickScore, CLIP, VQAScore (if available)

3. **Model Files** (downloaded on first use):
   - **PickScore**: Stability AI open-source model (via Hugging Face)
   - **CLIP**: OpenAI CLIP model (via Hugging Face transformers)
   - **VQAScore**: VQAScore model (if available via Hugging Face)
   - **LAION Aesthetic Predictor**: Pre-trained model (linear model on CLIP embeddings)

**Internal Dependencies:**

1. **Existing Services** (reuse patterns):
   - `app/services/pipeline/prompt_enhancement.py` - Two-agent pattern (Story 7.3 Phase 1)
   - `app/core/config.py` - Configuration management for API keys
   - `app/services/pipeline/scene_planning.py` - Scene planning for storyboard (if VideoDirectorGPT available)

2. **Project Structure**:
   - `backend/output/` directory structure for organizing outputs
   - Existing logging infrastructure (`app/core/logging.py`)

**Version Constraints:**

- Python 3.11+ (matches existing backend requirements)
- All dependencies should be compatible with existing `requirements.txt` versions
- Model files: Download on-demand, cache locally to avoid repeated downloads

## Acceptance Criteria (Authoritative)

**Story 8.1: Image Prompt Feedback Loop CLI**

1. **Given** a basic image prompt file or stdin input
   **When** I run `python enhance_image_prompt.py prompt.txt`
   **Then** the CLI tool:
   - Uses Agent 1 (Cinematographer) to enhance prompt with camera details, lighting, composition, film stock, mood, aspect ratio
   - Uses Agent 2 (Prompt Engineer) to critique and score on 5 dimensions (0-100 each)
   - Iterates between agents (max 3 rounds) until score threshold met or convergence detected
   - Saves all prompt versions to `output/image_prompt_traces/{timestamp}/` with numbered files
   - Saves `prompt_trace_summary.json` with scores, iterations, timestamps
   - Prints enhancement results to console with scores and iteration history
   - Supports stdin input: `echo "prompt" | python enhance_image_prompt.py -`
   - Supports custom output directories: `--output-dir ./my_traces`
   - Supports iteration control: `--max-iterations 5 --threshold 90`

2. **Given** prompt enhancement follows Prompt Scoring Guide guidelines
   **Then** enhanced prompts:
   - Structure like scene descriptions (who/what → action → where/when → style)
   - Include camera cues: "wide aerial shot", "close-up portrait", "telephoto shot"
   - Include lighting cues: "soft golden morning light", "harsh neon glow", "dramatic side lighting"
   - Limit to one scene or idea per prompt
   - Use natural language, not keyword stuffing

**Story 8.2: Image Generation Feedback Loop CLI**

3. **Given** an enhanced image prompt file
   **When** I run `python generate_images.py enhanced_prompt.txt --num-variations 8`
   **Then** the CLI tool:
   - Calls Replicate API (SDXL) to generate 8 image variations
   - All images share the specified aspect ratio
   - All follow the enhanced prompt
   - Automatically scores each image using PickScore, CLIP-Score, VQAScore, Aesthetic Predictor
   - Saves all images to `output/image_generations/{timestamp}/` numbered by quality rank
   - Saves metadata JSON for each image with scores, prompt, model, seed
   - Saves `generation_trace.json` with all prompts, images, scores, costs, timestamps
   - Prints ranked list to console with top 3 highlighted, score breakdown, file paths
   - Automatically selects top-scoring image as "best candidate"
   - Supports custom output directory: `--output-dir ./my_images`
   - Supports aspect ratio control: `--aspect-ratio 16:9`
   - Supports seed control: `--seed 12345`

**Story 8.3: Storyboard Creation CLI**

4. **Given** a video clip prompt file
   **When** I run `python create_storyboard.py clip_prompt.txt --num-clips 3`
   **Then** the CLI tool:
   - Uses VideoDirectorGPT-style planning (or basic planning) to break prompt into 3 clips
   - For each clip, generates start frame and end frame using image generation service
   - Generates motion descriptions (camera movement, subject motion) between start/end
   - Saves storyboard to `output/storyboards/{timestamp}/` with start/end frame images
   - Saves `storyboard_metadata.json` with clip descriptions, prompts, motion descriptions, shot list
   - Prints storyboard summary to console with clip descriptions, motion arcs, file paths
   - Supports custom output directory: `--output-dir ./my_storyboard`
   - Supports optional prompt enhancement: `--enhance-prompts`

## Traceability Mapping

| AC # | Acceptance Criteria | Spec Section | Component/Service | Test Idea |
|------|---------------------|--------------|-------------------|-----------|
| 1 | Image prompt enhancement CLI with two-agent feedback loops | Detailed Design → Services → `image_prompt_enhancement.py`, Workflows → Workflow 1 | `backend/enhance_image_prompt.py`, `app/services/pipeline/image_prompt_enhancement.py` | Unit test: Two-agent iteration loop, verify prompt enhancement adds camera/lighting details, verify scoring on 5 dimensions |
| 1 | Trace file generation and console output | Detailed Design → Data Models → File Structure, Workflows → Workflow 1 | `backend/enhance_image_prompt.py` | Integration test: Run CLI with sample prompt, verify trace files created with correct structure, verify console output format |
| 1 | CLI options (stdin, output-dir, max-iterations, threshold) | Detailed Design → APIs → CLI Interface → `enhance_image_prompt.py` | `backend/enhance_image_prompt.py` | Unit test: Test argparse/click options, test stdin input, test custom output directory |
| 2 | Prompt Scoring Guide compliance | Detailed Design → Services → `image_prompt_enhancement.py`, Objectives → In-Scope | `app/services/pipeline/image_prompt_enhancement.py` | Unit test: Verify enhanced prompts include camera cues, lighting cues, follow scene description structure |
| 3 | Image generation with automatic quality scoring | Detailed Design → Services → `image_generation.py`, `image_quality_scoring.py`, Workflows → Workflow 2 | `backend/generate_images.py`, `app/services/pipeline/image_generation.py`, `app/services/pipeline/image_quality_scoring.py` | Integration test: Generate 8 images, verify all quality metrics computed (PickScore, CLIP, VQAScore, Aesthetic), verify ranking by overall score |
| 3 | Replicate API integration and image download | Detailed Design → APIs → External API Integrations → Replicate API | `app/services/pipeline/image_generation.py` | Integration test: Call Replicate API with test prompt, verify image download, verify error handling and retry logic |
| 3 | Generation trace and metadata files | Detailed Design → Data Models → File Structure → Image Generation Directory | `backend/generate_images.py` | Integration test: Verify `generation_trace.json` contains all prompts, images, scores, costs, timestamps |
| 3 | CLI options (num-variations, aspect-ratio, seed, output-dir) | Detailed Design → APIs → CLI Interface → `generate_images.py` | `backend/generate_images.py` | Unit test: Test all CLI options, verify aspect ratio passed to Replicate API, verify seed reproducibility |
| 4 | Storyboard creation with start/end frames | Detailed Design → Services → `storyboard_service.py`, Workflows → Workflow 3 | `backend/create_storyboard.py`, `app/services/pipeline/storyboard_service.py` | Integration test: Generate storyboard with 3 clips, verify start/end frames generated for each clip, verify motion descriptions |
| 4 | VideoDirectorGPT planning integration | Detailed Design → Services → `storyboard_service.py`, Dependencies → Internal Dependencies | `app/services/pipeline/storyboard_service.py` | Integration test: Verify planning breaks prompt into clips, generates shot list with camera metadata (if VideoDirectorGPT available) |
| 4 | Storyboard metadata and console output | Detailed Design → Data Models → File Structure → Storyboard Directory | `backend/create_storyboard.py` | Integration test: Verify `storyboard_metadata.json` contains clip descriptions, prompts, motion descriptions, shot list |
| All | Performance requirements (latency targets) | Non-Functional Requirements → Performance | All services | Performance test: Measure prompt enhancement (<45s), image generation (<5min for 8 images), quality scoring (<2min for 8 images) |
| All | Error handling and retry logic | Non-Functional Requirements → Reliability/Availability | All services | Integration test: Simulate API failures, verify retry logic, verify graceful error messages, verify partial failure recovery |
| All | Logging and observability | Non-Functional Requirements → Observability | All CLI tools | Integration test: Run with `--verbose`, verify detailed logging, verify cost tracking in trace files |

## Risks, Assumptions, Open Questions

**Risks:**

1. **Risk: Quality Scoring Model Availability**
   - **Description**: PickScore, VQAScore, or LAION Aesthetic Predictor models may not be easily available or may require significant setup
   - **Impact**: High - Core functionality of Story 8.2 depends on automatic quality scoring
   - **Mitigation**: 
     - Prioritize PickScore (Stability AI open-source, most important)
     - CLIP-Score as fallback (widely available via Hugging Face)
     - Graceful degradation: If some metrics unavailable, use available ones
     - Document model setup requirements clearly

2. **Risk: Replicate API Model Availability**
   - **Description**: SDXL or preferred text-to-image model may not be available on Replicate, or API may change
   - **Impact**: Medium - Blocks image generation functionality
   - **Mitigation**: 
     - Support multiple model options with fallback chain
     - Test with alternative models (Stable Diffusion, other SDXL variants)
     - Follow same pattern as video generation service (fallback models)

3. **Risk: Quality Scoring Performance**
   - **Description**: Running PickScore, CLIP, VQAScore, Aesthetic on 8 images may be slow (>2 minutes target)
   - **Impact**: Medium - Affects developer experience and iteration speed
   - **Mitigation**: 
     - Load models once and reuse across images
     - Consider GPU acceleration if available
     - Make scoring optional with `--skip-scoring` flag for faster iteration
     - Optimize batch processing if possible

4. **Risk: Cost Overruns**
   - **Description**: Generating 8 images + prompt enhancement iterations may exceed cost expectations
   - **Impact**: Low - Developer tools, not production, but still need cost awareness
   - **Mitigation**: 
     - Clear cost tracking in trace files and console output
     - Support `--num-variations 4` to reduce default from 8
     - Document expected costs per operation
     - Warn users if costs exceed thresholds

**Assumptions:**

1. **Assumption**: Story 7.3 Phase 1 (Two-Agent Prompt Enhancement) is complete and `prompt_enhancement.py` service pattern is available for reuse
   - **Validation**: Verify `app/services/pipeline/prompt_enhancement.py` exists and follows two-agent pattern
   - **If False**: May need to implement two-agent pattern from scratch for image-specific enhancement

2. **Assumption**: VideoDirectorGPT planning (Story 7.3 Phase 2) may not be complete, but basic scene planning is available
   - **Validation**: Check if `app/services/pipeline/scene_planning.py` supports VideoDirectorGPT or basic planning
   - **If False**: Storyboard creation will use basic scene planning (break into clips, generate start/end frames)

3. **Assumption**: Replicate API supports text-to-image models (SDXL) with similar API patterns as video models
   - **Validation**: Test Replicate API with SDXL model, verify API patterns match video generation service
   - **If False**: Adapt API integration patterns as needed

4. **Assumption**: Quality scoring models (PickScore, CLIP) can be loaded and run locally without external API calls
   - **Validation**: Test model loading and inference performance
   - **If False**: May need to use API-based scoring services (if available) or reduce scoring metrics

**Open Questions:**

1. **Question**: Should quality scoring be optional or always-on?
   - **Decision Needed**: Default behavior for `generate_images.py` - always score or require `--score` flag?
   - **Recommendation**: Always-on by default (core feature), but support `--skip-scoring` for faster iteration

2. **Question**: What weights should be used for overall quality score calculation?
   - **Decision Needed**: PickScore (primary) vs CLIP-Score vs VQAScore vs Aesthetic - relative importance
   - **Recommendation**: PickScore 50%, CLIP-Score 25%, VQAScore 15%, Aesthetic 10% (adjust based on validation)

3. **Question**: Should storyboard creation integrate with existing scene planning service or be standalone?
   - **Decision Needed**: Use `scene_planning.py` or implement planning logic in `storyboard_service.py`?
   - **Recommendation**: Reuse existing scene planning if VideoDirectorGPT available, otherwise implement basic planning in storyboard service

4. **Question**: How should CLI tools handle model file downloads (PickScore, CLIP) - automatic or manual?
   - **Decision Needed**: Download on first use vs require manual download vs provide setup script
   - **Recommendation**: Download on first use with clear progress indicators, cache locally, document manual setup option

## Test Strategy Summary

**Test Levels:**

1. **Unit Tests** (pytest):
   - **`image_prompt_enhancement.py`**: Test two-agent iteration loop, prompt enhancement logic, scoring calculation, convergence detection
   - **`image_generation.py`**: Test Replicate API integration (mocked), image download, file organization, metadata generation
   - **`image_quality_scoring.py`**: Test each scoring metric (PickScore, CLIP-Score, VQAScore, Aesthetic) with sample images, test overall score calculation, test ranking logic
   - **`storyboard_service.py`**: Test planning logic (clip breakdown), start/end frame prompt generation, motion description generation
   - **CLI tools**: Test argument parsing, stdin input handling, file I/O, error handling

2. **Integration Tests** (pytest):
   - **End-to-end prompt enhancement**: Run `enhance_image_prompt.py` with sample prompt, verify trace files created, verify console output
   - **End-to-end image generation**: Run `generate_images.py` with enhanced prompt, verify images generated, verify quality scoring, verify ranking
   - **End-to-end storyboard**: Run `create_storyboard.py` with clip prompt, verify start/end frames generated, verify metadata
   - **API integration**: Test Replicate API calls (with test API key or mocked), test OpenAI API calls (with test key or mocked)
   - **Model integration**: Test quality scoring models with sample images (may require GPU or longer test time)

3. **Manual Testing** (Developer Workflows):
   - **CLI usability**: Test all CLI options, verify help text, verify error messages
   - **Output verification**: Manually inspect generated images, trace files, metadata JSON
   - **Performance validation**: Measure actual latencies, verify they meet targets
   - **Cost validation**: Run full workflows, verify cost tracking accuracy

**Test Coverage Goals:**

- **Unit tests**: >80% code coverage for all service modules
- **Integration tests**: Cover all three CLI tools end-to-end with sample inputs
- **Critical paths**: 100% coverage for prompt enhancement iteration loop, quality scoring calculation, image ranking

**Test Frameworks:**

- **pytest**: Primary testing framework (matches existing backend test structure)
- **pytest-mock**: For mocking external APIs (OpenAI, Replicate)
- **pytest-asyncio**: For async service functions
- **pytest-cov**: For code coverage reporting

**Test Data:**

- **Sample prompts**: Create test prompts covering various scenarios (simple, complex, with/without brand guidelines)
- **Sample images**: Use pre-generated test images for quality scoring tests (avoid generating during tests)
- **Mock API responses**: Create mock responses for OpenAI and Replicate APIs to avoid API costs during testing

**Edge Cases:**

- **Empty or invalid prompts**: Test error handling
- **API failures**: Test retry logic and graceful degradation
- **Missing model files**: Test model download and error handling
- **Large prompts**: Test with very long prompts (token limits)
- **Many variations**: Test with `--num-variations 20` to verify performance
- **Concurrent runs**: Test multiple CLI tools running simultaneously (if applicable)

**Performance Benchmarks:**

- **Prompt enhancement**: <45 seconds for 2-iteration enhancement (target)
- **Image generation**: <5 minutes for 8 images (target)
- **Quality scoring**: <2 minutes for 8 images (target)
- **Storyboard creation**: <15 minutes for 3 clips with start/end frames (target)

**Test Execution:**

- **Local development**: Run unit and integration tests before committing
- **CI/CD**: Add tests to existing test suite (if CI pipeline exists)
- **Manual validation**: Developer runs full CLI workflows with real APIs before marking story complete

