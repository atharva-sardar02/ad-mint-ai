# Storyboard Creation CLI Tool

The `create_storyboard.py` CLI tool generates storyboards (start and end frames) for video clips, helping visualize the motion arc before generating video.

## Overview

This tool:
- Breaks video prompts into 3-5 individual clips using scene planning
- Generates start and end frame images for each clip
- Creates comprehensive metadata including camera movements, shot lists, and motion descriptions
- Optionally enhances prompts before planning (using Story 8.1 service)
- Saves all outputs to organized directories with timestamps

## Prerequisites

- Python 3.8+
- `REPLICATE_API_TOKEN` environment variable set (required for image generation)
- `OPENAI_API_KEY` environment variable set (optional, required for `--enhance-prompts`)

## Installation

No additional installation required beyond project dependencies. The tool uses services from:
- `app/services/pipeline/storyboard_service.py` - Core storyboard generation
- `app/services/pipeline/image_generation.py` - Image generation (Story 8.2)
- `app/services/pipeline/image_prompt_enhancement.py` - Prompt enhancement (Story 8.1, optional)
- `app/services/pipeline/scene_planning.py` - Scene planning

## Usage

### Basic Usage

```bash
# Create storyboard with 3 clips (default)
python create_storyboard.py clip_prompt.txt

# Create storyboard with 5 clips
python create_storyboard.py clip_prompt.txt --num-clips 5

# Read prompt from stdin
echo "A product showcase video" | python create_storyboard.py -
```

### Advanced Options

```bash
# With prompt enhancement (uses Story 8.1 service)
python create_storyboard.py clip_prompt.txt --enhance-prompts

# Custom output directory
python create_storyboard.py clip_prompt.txt --output-dir ./my_storyboard

# Custom aspect ratio
python create_storyboard.py clip_prompt.txt --aspect-ratio 9:16

# Verbose logging
python create_storyboard.py clip_prompt.txt --verbose
```

### Command-Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `prompt_file` | path | required | Input file path containing video clip prompt, or `-` for stdin |
| `--num-clips` | int | 3 | Number of clips to create (3-5) |
| `--enhance-prompts` | flag | false | Enhance prompts using Story 8.1 service before planning |
| `--output-dir` | path | auto | Output directory (default: `output/storyboards/{timestamp}/`) |
| `--aspect-ratio` | string | 16:9 | Aspect ratio for frames (1:1, 4:3, 16:9, 9:16) |
| `--verbose` | flag | false | Enable verbose logging |

## Output Structure

The tool creates a timestamped directory with the following structure:

```
output/storyboards/20250117_143022/
├── clip_001_start.png          # Start frame for clip 1
├── clip_001_end.png            # End frame for clip 1
├── clip_002_start.png          # Start frame for clip 2
├── clip_002_end.png            # End frame for clip 2
├── clip_003_start.png          # Start frame for clip 3
├── clip_003_end.png            # End frame for clip 3
├── storyboard_metadata.json   # Complete metadata (see below)
└── prompt_enhancement_trace/   # (if --enhance-prompts used)
    ├── 00_original_prompt.txt
    ├── 05_final_enhanced_prompt.txt
    └── prompt_trace_summary.json
```

## Metadata Structure

The `storyboard_metadata.json` file contains:

```json
{
  "prompt": "Original prompt text",
  "enhanced_prompt": "Enhanced prompt (if --enhance-prompts used)",
  "num_clips": 3,
  "aspect_ratio": "16:9",
  "framework": "AIDA",
  "total_duration": 15,
  "clips": [
    {
      "clip_number": 1,
      "description": "Clip description",
      "start_frame_prompt": "Start frame prompt",
      "end_frame_prompt": "End frame prompt",
      "motion_description": "Camera movement description",
      "camera_movement": "Push in from wide to medium",
      "shot_size": "Wide shot",
      "perspective": "Eye level, establishing",
      "lens_type": "24-35mm wide angle",
      "start_frame_path": "path/to/clip_001_start.png",
      "end_frame_path": "path/to/clip_001_end.png"
    }
  ],
  "shot_list": [
    {
      "clip_number": 1,
      "camera_movement": "Push in from wide to medium",
      "shot_size": "Wide shot",
      "perspective": "Eye level, establishing",
      "lens_type": "24-35mm wide angle"
    }
  ],
  "scene_dependencies": [
    {
      "clip_number": 1,
      "dependencies": []
    },
    {
      "clip_number": 2,
      "dependencies": [
        {
          "depends_on": 1,
          "type": "narrative_flow",
          "description": "Continues narrative from clip 1"
        }
      ]
    }
  ],
  "narrative_flow": "Attention → Interest → Desire → Action across 3 clips",
  "consistency_groupings": [
    {
      "group_id": 1,
      "clip_numbers": [1, 2, 3],
      "consistency_type": "visual_style",
      "description": "Clips with similar visual style and camera settings"
    }
  ],
  "failed_clips": null,
  "partial_success": false,
  "created_at": "2025-01-17T14:30:22"
}
```

## Planning Behavior

### Basic Scene Planning (Current)

The tool currently uses basic scene planning from `scene_planning.py` as a fallback, since VideoDirectorGPT planning (Story 7.3 Phase 2) is in backlog. The basic planning:

- Breaks prompts into 3-5 clips based on framework templates (PAS, BAB, AIDA)
- Generates basic camera metadata (movement, shot size, perspective, lens type)
- Creates simple motion descriptions
- Groups clips by visual style for consistency

### VideoDirectorGPT Planning (Future)

When Story 7.3 Phase 2 is implemented, the tool will automatically use VideoDirectorGPT-style planning, which will provide:

- More sophisticated shot list generation
- Enhanced camera metadata
- Better consistency groupings (character/product identity preservation)
- Improved scene dependencies and narrative flow

The current implementation is designed to be compatible with VideoDirectorGPT planning when it becomes available.

## Error Handling

The tool handles errors gracefully:

- **Partial Failures**: If some clips fail to generate, the tool continues processing remaining clips and reports partial success in metadata
- **API Failures**: Image generation failures are caught per clip, logged, and reported in `failed_clips` metadata
- **Missing Files**: Clear error messages if input file is missing
- **API Key Validation**: Checks for required API keys before starting

If all clips fail, the tool raises an error. If some clips succeed, metadata includes `partial_success: true` and `failed_clips` array.

## Performance

Expected performance for 3 clips with start/end frames:
- **Without enhancement**: ~5-10 minutes
- **With enhancement** (`--enhance-prompts`): ~8-15 minutes

Performance depends on:
- Replicate API response times
- Number of clips (3-5)
- Whether prompt enhancement is enabled
- Network conditions

The tool includes timeout protection (15 minutes) in integration tests.

## Troubleshooting

### "REPLICATE_API_TOKEN not configured"
- Set the `REPLICATE_API_TOKEN` environment variable in your `.env` file or shell
- Get your token from https://replicate.com/account/api-tokens

### "OPENAI_API_KEY not configured" (when using --enhance-prompts)
- Set the `OPENAI_API_KEY` environment variable
- The tool will skip enhancement if the key is missing (with a warning)

### Image generation failures
- Check your Replicate API token is valid and has credits
- Check network connectivity
- Review logs for specific error messages
- Partial failures are reported in metadata `failed_clips` field

### "Failed to generate any storyboard clips"
- All clips failed to generate
- Check API keys and network connectivity
- Review error messages in logs
- Try with a simpler prompt

## Examples

### Example 1: Basic Storyboard

```bash
# Create a simple storyboard
echo "A sleek smartphone on a minimalist background" > prompt.txt
python create_storyboard.py prompt.txt
```

### Example 2: Enhanced Prompt Storyboard

```bash
# Use prompt enhancement for better results
python create_storyboard.py prompt.txt --enhance-prompts --num-clips 4
```

### Example 3: Custom Output

```bash
# Save to custom directory
python create_storyboard.py prompt.txt --output-dir ./my_storyboards/project1
```

## Integration with Other Tools

This tool integrates with:

- **Story 8.1** (`enhance_image_prompt.py`): Optional prompt enhancement
- **Story 8.2** (`generate_images.py`): Image generation service
- **Story 7.3 Phase 2** (future): VideoDirectorGPT planning

## See Also

- `backend/enhance_image_prompt.py` - Image prompt enhancement CLI
- `backend/generate_images.py` - Image generation CLI
- `docs/sprint-artifacts/tech-spec-epic-8.md` - Technical specification
- `docs/sprint-artifacts/8-3-storyboard-creation-cli.md` - Story documentation

## Support

For issues or questions:
1. Check this README and troubleshooting section
2. Review story documentation: `docs/sprint-artifacts/8-3-storyboard-creation-cli.md`
3. Check logs with `--verbose` flag for detailed error messages



