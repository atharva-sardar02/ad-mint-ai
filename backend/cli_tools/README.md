# CLI Tools for Image & Video Generation

**⚠️ Important: These are development and testing utilities, not production code.**

This directory contains standalone CLI tools developed in Epic 8 (Image Generation MVP) and Epic 9 (Video Generation MVP). These tools provide command-line interfaces for testing and validating the image and video generation pipeline components outside of the main web application.

## Purpose

These CLI tools are designed for:
- **Development Testing**: Quickly test pipeline services without starting the full web application
- **Manual QA**: Generate test outputs for quality validation
- **Debugging**: Isolate and test individual pipeline stages
- **Experimentation**: Try different prompts, models, and parameters interactively

**These tools are NOT part of the production web application pipeline.** The main application uses the same underlying services (`app/services/pipeline/`) but orchestrates them through web API endpoints.

---

## Available Tools

### 1. `enhance_image_prompt.py` (Epic 8)

**Purpose**: Enhance image generation prompts using two-agent iterative refinement (Cinematographer + Prompt Engineer).

**Usage**:
```bash
# Basic usage - enhance a prompt from file
python cli_tools/enhance_image_prompt.py prompt.txt

# Custom output directory and iteration settings
python cli_tools/enhance_image_prompt.py prompt.txt \
  --output-dir ./my_traces \
  --max-iterations 5 \
  --threshold 90

# Read from stdin
echo "A cat in a city" | python cli_tools/enhance_image_prompt.py -
```

**Key Options**:
- `--output-dir`: Output directory for trace files (default: `output/image_prompt_traces/<timestamp>`)
- `--max-iterations`: Maximum refinement rounds (default: 3)
- `--threshold`: Score threshold for early stopping (default: 85.0)
- `--creative-model`: Model for Cinematographer agent (default: `gpt-4-turbo`)
- `--critique-model`: Model for Prompt Engineer agent (default: `gpt-4-turbo`)
- `--verbose`: Enable verbose logging

**Outputs**:
- Enhanced prompt text
- Iteration trace files showing refinement process
- Score breakdown (completeness, specificity, professionalism, cinematography, brand alignment)
- Summary JSON with full enhancement history

---

### 2. `generate_images.py` (Epic 8)

**Purpose**: Generate multiple image variations with automatic quality scoring and ranking.

**Usage**:
```bash
# Basic usage - generates 8 images with default settings
python cli_tools/generate_images.py enhanced_prompt.txt

# Custom number of variations and aspect ratio
python cli_tools/generate_images.py enhanced_prompt.txt \
  --num-variations 6 \
  --aspect-ratio 1:1

# With prompt enhancement and custom output directory
python cli_tools/generate_images.py prompt.txt \
  --enhance-mode image-feedback \
  --output-dir ./my_images \
  --seed 12345
```

**Key Options**:
- `--num-variations`: Number of image variations (1-20, default: 8)
- `--aspect-ratio`: Aspect ratio (1:1, 4:3, 3:4, 16:9, 9:16, default: 16:9)
- `--seed`: Seed value for reproducibility
- `--model`: Replicate model (default: `black-forest-labs/flux-schnell`)
- `--enhance-mode`: Enhancement mode (`prompt-only`, `image-feedback`, `parallel-exploration`, `none`, default: `prompt-only`)
- `--max-iterations`: Enhancement iterations (default: 2-3 depending on mode)
- `--no-negative-prompt`: Skip negative prompt generation
- `--verbose`: Enable verbose logging

**Outputs**:
- Ranked images (image_001.png = best quality, image_002.png = 2nd best, etc.)
- Quality scores (PickScore, CLIP-Score, Aesthetic, VQAScore)
- Metadata JSON for each image
- Best candidate symlink
- Generation trace with costs and parameters

---

### 3. `create_storyboard.py` (Epic 8)

**Purpose**: Create storyboards (start and end frames) for multi-clip video sequences.

**Usage**:
```bash
# Basic usage - creates 3 clips with start/end frames
python cli_tools/create_storyboard.py clip_prompt.txt

# Create 5 clips with reference image for visual coherence
python cli_tools/create_storyboard.py clip_prompt.txt \
  --num-clips 5 \
  --reference-image output/image_generations/20251117_164104/image_001.png

# Custom output directory and story type
python cli_tools/create_storyboard.py clip_prompt.txt \
  --output-dir ./my_storyboard \
  --total-duration 30 \
  --story-type transformation
```

**Key Options**:
- `--num-clips`: Number of scenes/clips (1-10, default: 3)
- `--aspect-ratio`: Frame aspect ratio (default: 16:9)
- `--reference-image`: Reference image for visual coherence and narrative generation
- `--total-duration`: Total video duration in seconds (15-60, default: 15)
- `--story-type`: Narrative structure (`transformation`, `reveal_discovery`, `journey_path`, `problem_solution`, `sensory_experience`, `symbolic_metaphor`, `micro_drama`, `montage`, default: `sensory_experience`)
- `--verbose`: Enable verbose logging

**Outputs**:
- Start/end frames for each clip (keyframes)
- Storyboard metadata JSON with clip descriptions
- Motion descriptions for each clip
- Camera movements and shot compositions
- Unified narrative document (if reference image provided)

---

### 4. `enhance_video_prompt.py` (Epic 9)

**Purpose**: Enhance video generation prompts with video-specific quality dimensions and motion descriptions.

**Usage**:
```bash
# Basic usage - enhance video prompt
python cli_tools/enhance_video_prompt.py prompt.txt --video-mode

# Image-to-video mode with motion prompts
python cli_tools/enhance_video_prompt.py prompt.txt \
  --video-mode \
  --image-to-video

# Storyboard mode - processes all clips from storyboard
python cli_tools/enhance_video_prompt.py \
  --storyboard output/storyboards/20250117_143022/storyboard_metadata.json
```

**Key Options**:
- `--video-mode`: Enable video-specific enhancement (default: True)
- `--image-to-video`: Enable image-to-video motion prompt mode
- `--storyboard`: Path to storyboard metadata JSON (processes all clips)
- `--output-dir`: Output directory for trace files
- `--max-iterations`: Maximum refinement rounds (1-5, default: 3)
- `--threshold`: Score threshold for early stopping (default: 85.0)
- `--creative-model`: Model for Video Director agent (default: `gpt-4-turbo`)
- `--critique-model`: Model for Prompt Engineer agent (default: `gpt-4-turbo`)
- `--verbose`: Enable verbose logging

**Outputs**:
- Enhanced video prompt with temporal coherence
- Motion descriptions (for image-to-video mode)
- VideoDirectorGPT plan (multi-scene planning)
- Score breakdown (completeness, specificity, professionalism, cinematography, temporal coherence, brand alignment)
- Per-clip traces (in storyboard mode)

---

### 5. `generate_videos.py` (Epic 9)

**Purpose**: Generate videos with automatic VBench quality scoring and ranking.

**Usage**:
```bash
# Text-to-video mode
python cli_tools/generate_videos.py enhanced_prompt.txt --num-attempts 3

# Image-to-video mode
python cli_tools/generate_videos.py \
  --image-to-video \
  --hero-frame hero.png \
  --motion-prompt "slow zoom in"

# Storyboard mode - generates all clips
python cli_tools/generate_videos.py \
  --storyboard output/video_prompt_traces/20251117_211447/storyboard_enhanced_motion_prompts.json
```

**Key Options**:
- `--num-attempts`: Number of video attempts per clip (default: 3)
- `--model`: Replicate model (default: `kwaivgi/kling-v2.1`)
- `--duration`: Video duration in seconds (3-7, default: 5)
- `--seed`: Seed value for reproducibility
- `--negative-prompt`: Negative prompt text
- `--hero-frame`: Hero frame image path (required for `--image-to-video`)
- `--motion-prompt`: Motion description (required for `--image-to-video`)
- `--storyboard`: Storyboard JSON path (for multi-clip generation)
- `--output-dir`: Output directory for videos
- `--interactive`: Enable human-in-the-loop feedback
- `--verbose`: Enable verbose logging

**Outputs**:
- Ranked videos (video_001.mp4 = best quality, video_002.mp4 = 2nd best, etc.)
- VBench quality scores (temporal quality, subject consistency, motion smoothness, aesthetic quality, text-video alignment)
- Metadata JSON for each video
- Generation trace with costs and parameters
- Per-clip organization (in storyboard mode)

---

## Pipeline Services Used

These CLI tools import and use the following core pipeline services:

**Image Pipeline** (`app/services/pipeline/`):
- `image_prompt_enhancement.py` - Two-agent prompt refinement
- `image_generation.py` - Image generation orchestration
- `image_quality_scoring.py` - PickScore, CLIP-Score, Aesthetic, VQAScore
- `storyboard_service.py` - Storyboard creation with unified narrative

**Video Pipeline** (`app/services/pipeline/`):
- `video_prompt_enhancement.py` - Video-specific prompt refinement
- `video_generation_cli.py` - Video generation orchestration
- `video_quality_scoring.py` - VBench quality scoring

**Core Services** (`app/core/`):
- `config.py` - Configuration and environment variables
- `logging.py` - Logging setup

---

## Environment Requirements

All CLI tools require the following environment variables set in `.env`:

```bash
# Required for image generation
REPLICATE_API_TOKEN=your_replicate_token

# Required for prompt enhancement
OPENAI_API_KEY=your_openai_key

# Optional - for custom configuration
LOG_LEVEL=INFO
```

---

## Common Workflows

### Image Generation Workflow
```bash
# Step 1: Enhance the prompt
python cli_tools/enhance_image_prompt.py original_prompt.txt \
  --output-dir ./traces

# Step 2: Generate images using enhanced prompt
python cli_tools/generate_images.py ./traces/FINAL_PROMPT.txt \
  --num-variations 8 \
  --output-dir ./images
```

### Video Generation Workflow
```bash
# Step 1: Create storyboard with reference image
python cli_tools/create_storyboard.py video_concept.txt \
  --num-clips 3 \
  --reference-image ./best_hero_image.png \
  --output-dir ./storyboard

# Step 2: Enhance motion prompts for each clip
python cli_tools/enhance_video_prompt.py \
  --storyboard ./storyboard/storyboard_metadata.json \
  --output-dir ./enhanced_storyboard

# Step 3: Generate videos for all clips
python cli_tools/generate_videos.py \
  --storyboard ./enhanced_storyboard/storyboard_enhanced_motion_prompts.json \
  --num-attempts 3
```

---

## Development Notes

**DO NOT** use these CLI tools in production deployments:
- These are **development utilities only**
- They are not optimized for production workloads
- They do not include production error handling
- They are not monitored or logged like production services
- They bypass the web application's authentication and authorization

**Use the web application API endpoints instead** for production image/video generation workflows.

---

## Testing

To verify CLI tools are working after installation:

```bash
# Test each tool with --help flag
python cli_tools/enhance_image_prompt.py --help
python cli_tools/generate_images.py --help
python cli_tools/create_storyboard.py --help
python cli_tools/enhance_video_prompt.py --help
python cli_tools/generate_videos.py --help
```

All tools should display usage information without errors.

---

## Troubleshooting

**Import Errors**:
- Ensure you're running commands from the `backend/` directory root
- CLI tools use `sys.path.insert(0, str(Path(__file__).parent.parent))` to add backend to path
- Verify `app/` directory structure is intact

**API Key Errors**:
- Check `.env` file exists in `backend/` directory
- Verify `REPLICATE_API_TOKEN` and `OPENAI_API_KEY` are set correctly
- Ensure no extra spaces or quotes around keys

**File Not Found Errors**:
- Use absolute paths or paths relative to `backend/` directory
- Check file permissions for input files and output directories

---

## Related Documentation

- **Epic 8 Tech Spec**: `docs/sprint-artifacts/tech-spec-epic-8.md` (CLI MVP - Image Generation)
- **Epic 9 Tech Spec**: `docs/sprint-artifacts/tech-spec-epic-9.md` (CLI MVP - Video Generation)
- **Interactive Pipeline Tech Spec**: `docs/tech-spec.md` (Integration with web application)
- **Architecture Documentation**: `docs/architecture.md` (System design and pipeline services)
