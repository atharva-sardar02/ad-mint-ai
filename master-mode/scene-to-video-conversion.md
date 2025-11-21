# Scene-to-Video Conversion for Master Mode

## Overview

Converts detailed scene descriptions into Veo 3.1 video generation parameters. **Uses the FULL detailed scene content (150-250 words) as the prompt** for maximum quality and accuracy. No LLM optimization or condensing - the complete scene description is passed directly to Veo 3.1.

## Architecture

```
Detailed Scenes (from Scene Generator)
            ↓
    [Metadata Extraction] (Parse duration, camera, subject)
            ↓
    Veo 3.1 Parameters (with FULL scene as prompt)
```

## Key Design Decision

**Full Scene Content as Prompt**: Unlike typical approaches that condense prompts, we use the **entire detailed scene description** (150-250 words) because:
- Veo 3.1 can handle long, detailed prompts
- Scene Writer already created production-ready descriptions
- More detail = more accurate video generation
- Preserves all cinematography, lighting, and visual specifications
- No information loss from optimization

## Implementation

### Core Service: `scene_to_video.py`

**Location**: `backend/app/services/master_mode/scene_to_video.py`

**Key Functions**:

1. **`extract_scene_metadata()`**
   - Parses scene content to extract metadata
   - Detects: duration, camera_movement, subject_present
   - Uses regex and keyword matching
   - No LLM calls needed

2. **`convert_scenes_to_video_prompts()`**
   - Processes all scenes (synchronous - no LLM needed)
   - Builds Veo 3.1-compatible parameters for each scene
   - Uses **full scene content** as prompt
   - Handles R2V mode (with reference images) vs Start/End Frame mode
   - Returns list of video generation parameter sets

### Metadata Extraction

**Duration Detection**:
```python
# Extracts from: "Scene 1: Attention (6 seconds)"
duration_match = re.search(r'\((\d+)\s*seconds?\)', content_lower)
# Maps to Veo 3.1 valid values: 4, 6, or 8 seconds
```

**Camera Movement Detection**:
- Searches for keywords: "push-in", "pull-out", "pan left", "pan right", "tilt up", "tilt down"
- Defaults to "static" if not found

**Subject Presence Detection**:
- Checks for: "subject does not appear", "no subject"
- Defaults to True if not explicitly stated

## Veo 3.1 Parameter Mapping

### Mode Selection

**R2V Mode (Reference-to-Video)**: When subject is present AND reference images provided
```python
{
    "prompt": "...",
    "reference_images": ["/path/to/img1.jpg", "/path/to/img2.jpg"],
    "duration": 8,  # Fixed for R2V mode
    "aspect_ratio": "16:9",  # Fixed for R2V mode
    "resolution": "1080p",
    "generate_audio": true,
    "negative_prompt": "...",
    "seed": null
}
```

**Start/End Frame Mode**: When subject not present OR no reference images
```python
{
    "prompt": "...",
    "image": null,  # Will be populated with start frame
    "last_frame": null,  # Will be populated with end frame
    "duration": 4/6/8,  # Variable based on scene
    "aspect_ratio": "16:9",
    "resolution": "1080p",
    "generate_audio": true,
    "negative_prompt": "...",
    "seed": null
}
```

### Field Mappings

| Scene Data | Veo 3.1 Parameter | Notes |
|-----------|-------------------|-------|
| Optimized prompt | `prompt` | 50-150 words |
| Negative elements | `negative_prompt` | What to avoid |
| Scene duration | `duration` | 4, 6, or 8 seconds |
| Subject presence + ref images | `reference_images` | R2V mode |
| Subject absence or no ref | `image` + `last_frame` | Start/End mode |
| - | `aspect_ratio` | "16:9" (default) |
| - | `resolution` | "1080p" (default) |
| - | `generate_audio` | true (default) |
| - | `seed` | null (random) |

## Parallel Processing

All scenes are converted simultaneously using `asyncio.gather()`:

```python
tasks = [
    convert_scene_to_video_prompt(scene, scene_num, story)
    for scene_num, scene in enumerate(scenes)
]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

**Benefits**:
- Fast processing (all scenes converted at once)
- Efficient API usage
- Handles failures gracefully (per-scene error handling)

## API Integration

### Endpoint: `/api/master-mode/generate-story`

**New Response Field**: `video_generation_params`

```json
{
  "success": true,
  "story": "...",
  "scenes": {...},
  "video_generation_params": [
    {
      "scene_number": 1,
      "prompt": "Optimized prompt for scene 1...",
      "negative_prompt": "blurry, low quality...",
      "duration": 6,
      "aspect_ratio": "16:9",
      "resolution": "1080p",
      "generate_audio": true,
      "reference_images": ["/path/img1.jpg", "/path/img2.jpg"],
      "seed": null,
      "metadata": {
        "camera_movement": "push-in",
        "key_visual_elements": ["..."],
        "subject_present": true
      }
    },
    // ... more scenes
  ]
}
```

## Example Conversion

### Input (Detailed Scene)
```
Scene 1: Attention (6 seconds)

Visual Description:
A 32-year-old woman with shoulder-length chestnut brown hair stands in a modern minimalist bathroom with white marble countertops and soft gray walls. She wears a white silk robe. The environment features chrome fixtures and a large frameless mirror. Soft morning light streams through frosted glass windows creating a serene, luxurious atmosphere. The camera starts at a medium shot, eye-level, 50mm lens f/1.8, with shallow depth of field focusing on her face. Camera slowly pushes in as she reaches toward the counter...

Action Description:
She stands still for a moment, then gracefully reaches for a frosted glass perfume bottle on the marble counter. Her movement is slow and deliberate, emphasizing elegance...

Cinematography:
Medium shot, 50mm f/1.8, eye-level, push-in camera movement...

Start Frame: Woman standing, looking at counter
End Frame: Hand reaching toward bottle
```

### Output (Veo 3.1 Parameters - FULL SCENE)
```json
{
  "scene_number": 1,
  "prompt": "Scene 1: Attention (6 seconds)\n\nVisual Description:\nA 32-year-old woman with shoulder-length chestnut brown hair stands in a modern minimalist bathroom with white marble countertops and soft gray walls. She wears a white silk robe. The environment features chrome fixtures and a large frameless mirror. Soft morning light streams through frosted glass windows creating a serene, luxurious atmosphere. The camera starts at a medium shot, eye-level, 50mm lens f/1.8, with shallow depth of field focusing on her face. Camera slowly pushes in as she reaches toward the counter...\n\n[FULL 150-250 WORD SCENE]",
  "negative_prompt": "blurry, low quality, distorted, deformed, disfigured, bad anatomy, extra limbs, missing limbs, floating limbs, text, watermarks, logos, signatures, low resolution, pixelated, grainy",
  "duration": 6,
  "aspect_ratio": "16:9",
  "resolution": "1080p",
  "generate_audio": true,
  "reference_images": ["/path/to/user_ref_1.jpg", "/path/to/user_ref_2.jpg"],
  "seed": null,
  "metadata": {
    "scene_number": 1,
    "camera_movement": "push-in",
    "subject_present": true,
    "original_scene_length": 1247
  }
}
```

**Note**: The `prompt` field contains the **entire scene description** - no optimization or condensing.

## Error Handling

### Conversion Failures
- If LLM fails to convert a scene, creates fallback prompt from first 500 characters
- Logs error but continues with other scenes
- Returns exception info in `asyncio.gather()` results

### Validation
- Validates required fields in LLM response
- Ensures duration is 4, 6, or 8 seconds
- Checks aspect_ratio and resolution are valid

### Trace Support
- Saves each scene's video params to trace directory
- Format: `scene_{N}_video_params.json`

## Integration Points

### Current: API Response
- Returns `video_generation_params` in response
- Frontend receives ready-to-use Veo 3.1 parameters

### Future: Video Generation Pipeline
- Pass `video_generation_params` directly to video generation service
- Use existing Veo 3.1 integration in `video_generation.py`
- Generate all videos in parallel
- Stitch using cohesion analysis transitions

## Benefits

1. **Maximum Detail**: Uses full 150-250 word scene descriptions
2. **No Information Loss**: All cinematography, lighting, and visual specs preserved
3. **Production Quality**: Scene Writer's detailed descriptions directly to Veo 3.1
4. **No LLM Overhead**: Simple regex/parsing instead of additional LLM calls
5. **Consistent with Intent**: Maintains Scene Writer's exact specifications
6. **Veo 3.1 Compatible**: Long prompts work well with Veo 3.1
7. **Flexible Modes**: Automatically chooses R2V or Start/End Frame mode
8. **Error Resilient**: Simple parsing with sensible defaults

## Next Steps

1. **Image Generation**: Generate start/end frames for non-R2V scenes
2. **Video Generation**: Pass params to Veo 3.1 via existing pipeline
3. **Parallel Video Gen**: Generate all scene videos simultaneously
4. **Stitching**: Combine videos using transition data from cohesion analysis
5. **Audio**: Add voiceover and music
6. **Final Export**: Complete advertisement video

## Files Modified

- ✅ `backend/app/services/master_mode/scene_to_video.py` (NEW)
- ✅ `backend/app/services/master_mode/__init__.py` (exports)
- ✅ `backend/app/api/routes/master_mode.py` (integration)

## Testing

To test:
1. Generate story and scenes via Master Mode
2. Check response for `video_generation_params` field
3. Verify each scene has optimized prompt + Veo 3.1 parameters
4. Check R2V mode is used when reference images provided
5. Verify parallel processing (all scenes converted simultaneously)

