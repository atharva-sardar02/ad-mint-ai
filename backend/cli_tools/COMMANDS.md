# CLI Tools - Complete Command Reference

## Quick Start - Full Pipeline (YOLO!)

```bash
# Full automated pipeline - prompt to final video
python3 cli_tools/pipeline.py prompt.txt --yolo

# Full pipeline with custom settings
python3 cli_tools/pipeline.py prompt.txt --yolo --num-clips 5 --duration 30
```

---

## Pipeline Orchestrator Commands

The `pipeline.py` tool orchestrates the entire workflow from prompt to final video.

### Pipeline Stages

1. **ref-image** - Generate reference/hero image
2. **narrative** - Generate unified narrative document
3. **storyboard** - Create start/end frames for each clip
4. **motion-prompts** - Enhance motion prompts for video generation
5. **clips** - Generate video clips
6. **final-video** - Assemble final video

### Full Pipeline (YOLO Mode)

```bash
# Complete automation - no stops
python3 cli_tools/pipeline.py "A product showcase video" --yolo

# YOLO with custom settings
python3 cli_tools/pipeline.py product_brief.txt --yolo \
  --num-clips 5 \
  --duration 30 \
  --story-type transformation \
  --video-attempts 3
```

### Stop at Specific Stages

```bash
# Stop after reference image generation
python3 cli_tools/pipeline.py prompt.txt --stop-at ref-image

# Stop after storyboard creation (frames only, no videos)
python3 cli_tools/pipeline.py prompt.txt --stop-at storyboard

# Stop after clips (skip final video assembly)
python3 cli_tools/pipeline.py prompt.txt --stop-at clips
```

### Interactive Mode (Manual Approval at Each Stage)

```bash
# Pause at each stage for review/approval
python3 cli_tools/pipeline.py prompt.txt --interactive

# Interactive with custom settings
python3 cli_tools/pipeline.py prompt.txt --interactive \
  --num-clips 3 \
  --duration 20 \
  --aspect-ratio 9:16
```

### Resume from Checkpoint

```bash
# Resume from previous run (pipeline saves state automatically)
python3 cli_tools/pipeline.py --resume output/pipeline_runs/20250119_120000

# Resume and continue to completion
python3 cli_tools/pipeline.py --resume output/pipeline_runs/20250119_120000 --yolo
```

### Pipeline Options

```bash
# Content settings
--num-clips N              # Number of video clips/scenes (default: 3)
--duration N               # Total video duration in seconds (default: 15)
--clip-duration N          # Individual clip duration (default: 5)
--aspect-ratio RATIO       # 1:1, 4:3, 16:9, 9:16 (default: 16:9)
--story-type TYPE          # Narrative structure (default: sensory_experience)
                           # Options: transformation, reveal_discovery, journey_path,
                           #          problem_solution, sensory_experience,
                           #          symbolic_metaphor, micro_drama, montage

# Generation settings
--ref-image-variations N   # Reference image variations (default: 4)
--video-attempts N         # Video attempts per clip (default: 3)
--prompt-iterations N      # Prompt enhancement iterations (default: 2)

# Model settings
--image-model MODEL        # Image generation model
                           # default: black-forest-labs/flux-schnell
--video-model MODEL        # Video generation model
                           # default: kwaivgi/kling-v2.1
--seed N                   # Seed for reproducibility

# Other
--verbose                  # Enable verbose logging
```

---

## Individual Tool Commands

Use these for granular control or testing individual pipeline stages.

### 1. Image Prompt Enhancement

```bash
# Basic prompt enhancement
python3 cli_tools/enhance_image_prompt.py prompt.txt

# Custom settings
python3 cli_tools/enhance_image_prompt.py prompt.txt \
  --output-dir ./traces \
  --max-iterations 5 \
  --threshold 90 \
  --creative-model gpt-4-turbo \
  --verbose

# From stdin
echo "A beautiful sunset over mountains" | python3 cli_tools/enhance_image_prompt.py -
```

**Outputs:**
- Enhanced prompt text
- Iteration trace files
- Score breakdown (completeness, specificity, professionalism, cinematography, brand alignment)
- `FINAL_PROMPT.txt` - Use this for image generation

---

### 2. Image Generation

```bash
# Basic image generation
python3 cli_tools/generate_images.py enhanced_prompt.txt

# With prompt enhancement (recommended)
python3 cli_tools/generate_images.py prompt.txt \
  --enhance-mode prompt-only \
  --num-variations 8 \
  --aspect-ratio 16:9

# Custom model and settings
python3 cli_tools/generate_images.py enhanced_prompt.txt \
  --num-variations 6 \
  --model black-forest-labs/flux-dev \
  --seed 12345 \
  --output-dir ./my_images

# Advanced: Image feedback loop (slower, higher quality)
python3 cli_tools/generate_images.py prompt.txt \
  --enhance-mode image-feedback \
  --max-iterations 3 \
  --num-variations 4

# Advanced: Parallel exploration (test multiple prompt variations)
python3 cli_tools/generate_images.py prompt.txt \
  --enhance-mode parallel-exploration \
  --num-variations 8
```

**Model Options:**
- `black-forest-labs/flux-schnell` (fast, default)
- `black-forest-labs/flux-dev` (higher quality, slower)
- `stability-ai/sdxl-turbo` (fast, lower quality)
- `google/imagen-4-ultra` (highest quality, expensive)

**Outputs:**
- Ranked images (`image_001.png` = best, `image_002.png` = 2nd best, etc.)
- Quality scores (PickScore, CLIP-Score, Aesthetic, VQAScore)
- Metadata JSON for each image
- `best_candidate.png` symlink
- Generation trace with costs

---

### 3. Storyboard Creation

```bash
# Basic storyboard (3 clips)
python3 cli_tools/create_storyboard.py video_concept.txt

# With reference image for visual coherence
python3 cli_tools/create_storyboard.py video_concept.txt \
  --reference-image output/image_generations/20250119_120000/image_001.png \
  --num-clips 5

# Custom story type and duration
python3 cli_tools/create_storyboard.py video_concept.txt \
  --num-clips 5 \
  --total-duration 30 \
  --story-type transformation \
  --aspect-ratio 9:16

# All story types
python3 cli_tools/create_storyboard.py prompt.txt --story-type transformation   # Before/after transformation
python3 cli_tools/create_storyboard.py prompt.txt --story-type reveal_discovery # Gradual reveal
python3 cli_tools/create_storyboard.py prompt.txt --story-type journey_path     # Physical/metaphorical journey
python3 cli_tools/create_storyboard.py prompt.txt --story-type problem_solution # Problem → solution arc
python3 cli_tools/create_storyboard.py prompt.txt --story-type sensory_experience # Immersive sensory journey
python3 cli_tools/create_storyboard.py prompt.txt --story-type symbolic_metaphor # Abstract/symbolic narrative
python3 cli_tools/create_storyboard.py prompt.txt --story-type micro_drama      # Character-driven story
python3 cli_tools/create_storyboard.py prompt.txt --story-type montage          # Fast-paced montage
```

**Outputs:**
- Start and end frames for each clip (keyframes)
- `storyboard_metadata.json` - Use this for motion prompt enhancement
- Unified narrative document (if reference image provided)
- Motion descriptions and camera movements
- Shot compositions and perspectives

---

### 4. Video Prompt Enhancement

```bash
# Enhance single video prompt
python3 cli_tools/enhance_video_prompt.py prompt.txt --video-mode

# Enhance storyboard motion prompts (all clips)
python3 cli_tools/enhance_video_prompt.py \
  --storyboard output/storyboards/20250119_120000/storyboard_metadata.json

# Image-to-video mode
python3 cli_tools/enhance_video_prompt.py prompt.txt \
  --video-mode \
  --image-to-video

# Custom settings
python3 cli_tools/enhance_video_prompt.py \
  --storyboard storyboard_metadata.json \
  --max-iterations 4 \
  --threshold 90 \
  --creative-model gpt-4-turbo \
  --output-dir ./video_traces
```

**Outputs:**
- Enhanced video prompts with temporal coherence
- Motion descriptions (for image-to-video)
- VideoDirectorGPT plan (multi-scene planning)
- Score breakdown (completeness, specificity, professionalism, cinematography, temporal coherence, brand alignment)
- `storyboard_enhanced_motion_prompts.json` - Use this for video generation

---

### 5. Video Generation

```bash
# Text-to-video (single prompt)
python3 cli_tools/generate_videos.py enhanced_prompt.txt --num-attempts 3

# Image-to-video (hero frame + motion)
python3 cli_tools/generate_videos.py \
  --image-to-video \
  --hero-frame output/reference_images/image_001.png \
  --motion-prompt "slow zoom in, camera pans right"

# Storyboard mode (generates all clips)
python3 cli_tools/generate_videos.py \
  --storyboard output/video_prompt_traces/20250119_120000/storyboard_enhanced_motion_prompts.json \
  --num-attempts 3

# Custom model and settings
python3 cli_tools/generate_videos.py enhanced_prompt.txt \
  --num-attempts 5 \
  --model kwaivgi/kling-v2.1 \
  --duration 5 \
  --seed 12345 \
  --output-dir ./my_videos
```

**Model Options:**
- `kwaivgi/kling-v2.1` (recommended, default)
- `klingai/kling-2.5-turbo` (faster, lower quality)
- Other Replicate video models

**Outputs:**
- Ranked videos (`video_001.mp4` = best, `video_002.mp4` = 2nd best, etc.)
- VBench quality scores (temporal quality, subject consistency, motion smoothness, aesthetic quality, text-video alignment)
- Metadata JSON for each video
- Generation trace with costs
- Per-clip organization (in storyboard mode)

---

## Complete Workflow Examples

### Example 1: Quick Test (Stop at Reference Image)

```bash
# Test prompt enhancement and image generation only
python3 cli_tools/pipeline.py "A modern minimalist product showcase" \
  --stop-at ref-image \
  --ref-image-variations 6
```

**Output:** Reference image variations, best candidate selected

---

### Example 2: Storyboard Preview (Stop Before Video Generation)

```bash
# Generate storyboard frames without videos (faster, cheaper)
python3 cli_tools/pipeline.py product_brief.txt \
  --stop-at storyboard \
  --num-clips 5 \
  --story-type transformation
```

**Output:** Reference image + storyboard frames + narrative document

---

### Example 3: Full Pipeline with Custom Settings

```bash
# Complete pipeline with all custom settings
python3 cli_tools/pipeline.py marketing_brief.txt --yolo \
  --num-clips 5 \
  --duration 30 \
  --clip-duration 6 \
  --aspect-ratio 9:16 \
  --story-type reveal_discovery \
  --ref-image-variations 8 \
  --video-attempts 4 \
  --prompt-iterations 3 \
  --image-model black-forest-labs/flux-dev \
  --video-model kwaivgi/kling-v2.1 \
  --seed 42
```

**Output:** Complete video from prompt to final assembled MP4

---

### Example 4: Interactive Review Mode

```bash
# Review and approve each stage before continuing
python3 cli_tools/pipeline.py concept.txt --interactive \
  --num-clips 3 \
  --duration 15
```

**Flow:**
1. Generates reference image → pause for approval
2. Creates storyboard → pause for approval
3. Enhances motion prompts → pause for approval
4. Generates video clips → pause for approval
5. Assembles final video → complete

---

### Example 5: Resume from Previous Run

```bash
# Step 1: Start pipeline, stop at storyboard
python3 cli_tools/pipeline.py prompt.txt --stop-at storyboard

# Step 2: Review outputs, then resume to completion
python3 cli_tools/pipeline.py \
  --resume output/pipeline_runs/20250119_120000 \
  --yolo
```

**State saved automatically** - pipeline remembers all previous work

---

## Manual Multi-Stage Workflow (Advanced)

For complete manual control, run each tool individually:

```bash
# Stage 1: Enhance prompt
python3 cli_tools/enhance_image_prompt.py concept.txt \
  --output-dir ./stage1_prompt

# Stage 2: Generate reference image
python3 cli_tools/generate_images.py ./stage1_prompt/FINAL_PROMPT.txt \
  --num-variations 8 \
  --output-dir ./stage2_images

# Stage 3: Create storyboard with best reference image
python3 cli_tools/create_storyboard.py concept.txt \
  --reference-image ./stage2_images/image_001.png \
  --num-clips 5 \
  --output-dir ./stage3_storyboard

# Stage 4: Enhance motion prompts
python3 cli_tools/enhance_video_prompt.py \
  --storyboard ./stage3_storyboard/storyboard_metadata.json \
  --output-dir ./stage4_motion

# Stage 5: Generate video clips
python3 cli_tools/generate_videos.py \
  --storyboard ./stage4_motion/storyboard_enhanced_motion_prompts.json \
  --num-attempts 3 \
  --output-dir ./stage5_videos

# Stage 6: Assemble final video (manual ffmpeg)
cd ./stage5_videos

# Create concat list
for i in {1..5}; do
  echo "file 'clip_$(printf %03d $i)/clip_$(printf %03d $i)_video_001.mp4'" >> concat.txt
done

# Concatenate
ffmpeg -f concat -safe 0 -i concat.txt -c copy final_video.mp4
```

---

## Common Use Cases

### Marketing Video Creation

```bash
python3 cli_tools/pipeline.py marketing_brief.txt --yolo \
  --num-clips 5 \
  --story-type problem_solution \
  --aspect-ratio 9:16
```

### Product Demo Video

```bash
python3 cli_tools/pipeline.py product_description.txt --yolo \
  --num-clips 3 \
  --story-type reveal_discovery \
  --duration 20
```

### Social Media Content

```bash
python3 cli_tools/pipeline.py social_post.txt --yolo \
  --num-clips 3 \
  --clip-duration 5 \
  --aspect-ratio 9:16 \
  --story-type sensory_experience
```

### Brand Story Video

```bash
python3 cli_tools/pipeline.py brand_story.txt --yolo \
  --num-clips 7 \
  --duration 45 \
  --story-type transformation \
  --video-attempts 5
```

---

## Environment Setup

**Required Environment Variables** (in `.env` file):

```bash
REPLICATE_API_TOKEN=your_replicate_token
OPENAI_API_KEY=your_openai_key
```

**Optional:**

```bash
LOG_LEVEL=INFO  # or DEBUG for verbose output
```

---

## Cost Estimation

**Approximate costs per pipeline run:**

- **Reference Image Generation**: $0.02 - $0.10 (4-8 images)
- **Storyboard Creation**: $0.10 - $0.30 (3-5 clips × 2 frames)
- **Motion Prompt Enhancement**: $0.01 - $0.05 (LLM calls)
- **Video Clip Generation**: $0.30 - $1.50 (3-5 clips × 3 attempts)
- **Total per run**: $0.43 - $1.95

**Cost-saving tips:**
- Use `--ref-image-variations 4` instead of 8
- Use `--video-attempts 2` for testing
- Use `--stop-at storyboard` to preview before video generation
- Use `flux-schnell` for images (fastest, cheapest)

---

## Troubleshooting

### Import Errors

```bash
# Ensure you're in the backend directory
cd /path/to/ad-mint-ai/backend
python3 cli_tools/pipeline.py --help
```

### API Key Errors

```bash
# Verify .env file exists
cat .env | grep API

# Should show:
# REPLICATE_API_TOKEN=r8_...
# OPENAI_API_KEY=sk-...
```

### FFmpeg Not Found (Final Video Assembly)

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Verify installation
ffmpeg -version
```

### Pipeline State Recovery

```bash
# Find your pipeline run
ls -la output/pipeline_runs/

# Check state
cat output/pipeline_runs/20250119_120000/pipeline_state.json

# Resume from checkpoint
python3 cli_tools/pipeline.py --resume output/pipeline_runs/20250119_120000
```

---

## Tips and Best Practices

1. **Start Small**: Test with `--stop-at ref-image` first
2. **Use Interactive Mode**: Review outputs at each stage with `--interactive`
3. **Save Costs**: Use `--stop-at storyboard` to preview before expensive video generation
4. **Resume Capability**: Pipeline auto-saves state - safe to Ctrl+C and resume later
5. **Seed for Reproducibility**: Use `--seed 42` to get consistent results
6. **Aspect Ratio**: Match your target platform (9:16 for mobile, 16:9 for desktop)
7. **Story Type**: Choose narrative structure that fits your content

---

## Output Directory Structure

```
output/pipeline_runs/20250119_120000/
├── pipeline_state.json                    # State for resume capability
├── 01_image_prompt_traces/                # Prompt enhancement traces
│   ├── 00_original_prompt.txt
│   ├── 05_final_enhanced_prompt.txt
│   └── prompt_trace_summary.json
├── 02_reference_images/                   # Reference image variations
│   ├── image_001.png                      # Best (highest score)
│   ├── image_002.png
│   ├── ...
│   └── best_candidate.png                 # Symlink to best
├── 03_storyboard/                         # Storyboard frames
│   ├── storyboard_metadata.json
│   ├── unified_narrative.md
│   ├── clip_001_start.png
│   ├── clip_001_end.png
│   └── ...
├── 04_motion_prompt_traces/               # Enhanced motion prompts
│   ├── storyboard_enhanced_motion_prompts.json
│   ├── clip_001/
│   └── ...
├── 05_video_clips/                        # Generated video clips
│   ├── clip_001/
│   │   ├── clip_001_video_001.mp4        # Best (highest VBench score)
│   │   ├── clip_001_video_002.mp4
│   │   └── clip_001_video_003.mp4
│   └── ...
└── 06_final_video/                        # Final assembled video
    ├── concat_list.txt
    └── final_video.mp4
```

---

## Help Commands

```bash
# Pipeline orchestrator help
python3 cli_tools/pipeline.py --help

# Individual tool help
python3 cli_tools/enhance_image_prompt.py --help
python3 cli_tools/generate_images.py --help
python3 cli_tools/create_storyboard.py --help
python3 cli_tools/enhance_video_prompt.py --help
python3 cli_tools/generate_videos.py --help
```

---

**Happy creating! 🎬**
