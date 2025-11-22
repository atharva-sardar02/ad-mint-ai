# Video Prompt Enhancement CLI Tool

Standalone command-line tool for iteratively enhancing video prompts using two specialized LLM agents with VideoDirectorGPT enhancements.

## Overview

This tool uses a two-agent system to transform any basic video prompt into a professional, production-ready specification optimized for video generation models (Stable Video Diffusion, AnimateDiff, Sora, etc.):

- **Agent 1 (Video Director/Creative Director)**: Enhances prompts with camera framing, movement, action beats, timing cues, lighting, color palette, motion intensity, and temporal continuity hints
- **Agent 2 (Prompt Engineer)**: Critiques and scores prompts on 6 dimensions, providing actionable feedback

The agents iterate until a quality threshold is met or convergence is detected.

### Key Features

- **6-Dimension Scoring**: Completeness, Specificity, Professionalism, Cinematography, Temporal Coherence, Brand Alignment
- **Storyboard Mode**: Process all clips from a storyboard JSON with unified narrative context integration
- **Image-to-Video Mode**: Enhanced motion prompts for image-to-video generation
- **VideoDirectorGPT Planning**: Optional integration with scene planning (graceful fallback if unavailable)
- **Comprehensive Trace Files**: Full iteration history saved for transparency

## Installation

Ensure you have the required dependencies:

```bash
cd backend
pip install -r requirements.txt
```

Set your OpenAI API key:

```bash
export OPENAI_API_KEY="your-key-here"
# Or add to .env file
```

## Usage

### Single Prompt Mode

Enhance a single video prompt:

```bash
# Read from file
python enhance_video_prompt.py prompt.txt --video-mode

# Read from stdin
echo "A sleek smartphone on a minimalist desk" | python enhance_video_prompt.py - --video-mode

# Or pipe from file
cat my_prompt.txt | python enhance_video_prompt.py - --video-mode
```

### Storyboard Mode

Process all clips from a storyboard JSON (from Story 8.3/8.4):

```bash
python enhance_video_prompt.py --storyboard output/storyboards/20251117_203210/storyboard_metadata.json
```

**Storyboard Mode Features:**
- Loads unified narrative document for narrative context
- Validates start/end frame images for each clip
- Enhances motion prompts per clip with narrative coherence
- Preserves frame paths and narrative references for Story 9.2 video generation

### Image-to-Video Mode

Generate motion prompts for image-to-video generation:

```bash
python enhance_video_prompt.py prompt.txt --video-mode --image-to-video
```

This mode focuses on:
- Camera movement (pan, tilt, dolly, static, tracking)
- Motion intensity (subtle, moderate, dynamic)
- Frame rate considerations
- Negative prompts for unwanted motion

## Advanced Options

### Custom Output Directory

```bash
python enhance_video_prompt.py prompt.txt --output-dir ./my_traces
```

### Custom Iteration Settings

```bash
python enhance_video_prompt.py prompt.txt --max-iterations 5 --threshold 90
```

- `--max-iterations`: Maximum iteration rounds (1-5, default: 3)
- `--threshold`: Score threshold for early stopping (default: 85.0)

### Model Selection

```bash
python enhance_video_prompt.py prompt.txt --creative-model gpt-4-turbo --critique-model gpt-4-turbo
```

### Verbose Logging

```bash
python enhance_video_prompt.py prompt.txt --verbose
```

## Output Structure

### Single Prompt Mode

```
output/video_prompt_traces/20251117_143022/
├── 00_original_prompt.txt
├── 01_agent1_iteration_1.txt
├── 02_agent2_iteration_1.txt
├── 03_agent1_iteration_2.txt (if iterated)
├── 04_agent2_iteration_2.txt (if iterated)
├── 05_final_enhanced_prompt.txt
├── 06_videodirectorgpt_plan.json (if available)
├── motion_prompt.txt (if --image-to-video)
├── prompt_trace_summary.json
└── FINAL_PROMPT.txt
```

### Storyboard Mode

```
output/video_prompt_traces/20251117_143022/
├── clip_001/
│   ├── 00_original_motion.txt
│   ├── 01_agent1_iteration_1.txt
│   ├── 02_agent2_iteration_1.txt
│   └── ...
├── clip_002/
│   └── ...
├── clip_001_enhanced_motion_prompt.txt
├── clip_002_enhanced_motion_prompt.txt
└── storyboard_enhanced_motion_prompts.json
```

## Scoring Dimensions

The tool scores prompts on 6 dimensions (0-100 each):

1. **Completeness**: Does it have all necessary elements (subject, action, setting, style, motion)?
2. **Specificity**: Are visual and motion details clear and unambiguous?
3. **Professionalism**: Is it ad-quality language? Does it read like a one-sentence screenplay?
4. **Cinematography**: Does it include camera/composition details? Lighting cues?
5. **Temporal Coherence**: Does it describe smooth, plausible motion? (Video-specific)
6. **Brand Alignment**: Are brand elements preserved and enhanced?

**Overall Score**: Weighted average of all dimensions.

## Prompt Scoring Guide Compliance

Enhanced prompts follow Prompt Scoring Guide best practices:

- **Structure**: One-sentence screenplay style (subject → action → setting → style → mood → motion)
- **Film Terminology**: Uses professional cinematography language
- **Single Scene**: Limited to one scene or action per prompt
- **Visual Language**: Describes what the camera sees
- **Details**: Specifies camera framing, depth of field, action beats, lighting, palette, motion

## Integration with Story 9.2

When using storyboard mode, the output JSON (`storyboard_enhanced_motion_prompts.json`) includes:

- Enhanced motion prompts for each clip
- **Start/end frame paths** (preserved from storyboard, required for image-to-video generation)
- **Unified narrative document reference** (for context continuity)
- Scores and iteration history per clip

This output is ready for Story 9.2 video generation workflow.

## VideoDirectorGPT Planning

The tool optionally integrates with VideoDirectorGPT planning (Story 7.3 Phase 2):

- If available: Generates shot list with camera metadata, scene dependencies, narrative flow, consistency groupings
- If unavailable: Uses basic scene planning as fallback, or skips planning (tool still works)

The planning output is saved to `06_videodirectorgpt_plan.json` when available.

## Examples

### Example 1: Basic Video Prompt

```bash
# Input prompt
echo "A smartphone on a desk" > prompt.txt

# Enhance
python enhance_video_prompt.py prompt.txt --video-mode

# Output: Enhanced prompt with camera movement, lighting, motion details
```

### Example 2: Storyboard Processing

```bash
# Process storyboard with 3 clips
python enhance_video_prompt.py --storyboard output/storyboards/20251117_203210/storyboard_metadata.json

# Output: Enhanced motion prompts for all 3 clips, ready for video generation
```

### Example 3: Image-to-Video Motion Prompt

```bash
# Generate motion prompt for image-to-video
python enhance_video_prompt.py prompt.txt --video-mode --image-to-video

# Output: Enhanced prompt + motion_prompt.txt with camera movement and frame rate details
```

## Error Handling

The tool handles various error conditions gracefully:

- **Missing API Key**: Clear error message with setup instructions
- **Invalid Input File**: File not found error with helpful message
- **Invalid Storyboard JSON**: JSON parsing error with file path
- **Missing Unified Narrative**: Error if storyboard missing narrative document
- **Missing Frame Images**: Warning logged, processing continues
- **API Failures**: Error message with retry suggestion

## Performance

Target performance:
- **Single Prompt**: <60 seconds for 2-iteration enhancement
- **Storyboard Mode**: <60 seconds per clip (for 3 clips: <3 minutes total)

Timing information is logged for each major operation when using `--verbose`.

## Troubleshooting

### "OPENAI_API_KEY not configured"
Set your API key in environment variables or `.env` file.

### "Storyboard missing unified_narrative_path"
Ensure the storyboard was created with Story 8.4 (unified narrative generation).

### "Unified narrative document not found"
Check that the `unified_narrative_path` in storyboard JSON points to a valid file.

### "Start/end frame images not found"
Verify that frame images exist at the paths specified in the storyboard JSON.

## Related Tools

- `enhance_image_prompt.py`: Image prompt enhancement (Story 8.1)
- `create_storyboard.py`: Storyboard creation (Story 8.3)
- `generate_videos.py`: Video generation (Story 9.2, upcoming)

## References

- **Prompt Scoring Guide**: `docs/Prompt_Scoring_and_Optimization_Guide.md`
- **Epic 9 Tech Spec**: `docs/sprint-artifacts/tech-spec-epic-9.md`
- **Story 8.4**: Unified narrative generation
- **Story 9.2**: Video generation workflow



