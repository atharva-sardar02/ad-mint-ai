# Master Mode Video Generation and Stitching

## Overview

Generates videos for each scene using Veo 3.1 and stitches them together into a final advertisement video. Uses the full detailed scene descriptions as prompts and a **custom Master Mode stitcher** (not the old pipeline stitcher).

## Architecture

```
Video Generation Params (from scene-to-video)
            ↓
    [Parallel Video Generation] (Veo 3.1)
            ↓
    Individual Scene Videos (scene_01.mp4, scene_02.mp4, ...)
            ↓
    [Extract Transitions] (from cohesion analysis)
            ↓
    [Master Mode Video Stitcher] (NEW - clean implementation)
            ↓
    Final Advertisement Video
```

## Implementation

### New Service: `video_stitcher.py`

**Location**: `backend/app/services/master_mode/video_stitcher.py`

**Purpose**: Clean, focused stitching implementation specifically for Master Mode.

**Key Features**:
- Context manager for automatic resource cleanup
- Only 3 transition types: `cut`, `crossfade`, `fade`
- Clear, maintainable code without complex effects
- Better logging with progress indicators
- High-quality output settings (5000k bitrate, 24fps)

**Class: `VideoStitcher`**

```python
class VideoStitcher:
    """Handles video stitching operations for Master Mode."""
    
    TRANSITION_DURATIONS = {
        "cut": 0.0,
        "crossfade": 0.5,
        "fade": 0.8,
    }
```

**Methods**:
- `__init__(target_fps=24)`: Initialize stitcher
- `__enter__` / `__exit__`: Context manager for cleanup
- `_load_clip()`: Load and normalize video clip
- `_apply_crossfade()`: Smooth blend between clips
- `_apply_fade()`: Fade to black, then fade in
- `_apply_transition()`: Apply any transition type
- `stitch_videos()`: Main stitching function

**Usage**:
```python
with VideoStitcher() as stitcher:
    final_path = stitcher.stitch_videos(
        video_paths=["scene_01.mp4", "scene_02.mp4"],
        output_path="final.mp4",
        transitions=["crossfade"]
    )
```

**Convenience Function**:
```python
def stitch_master_mode_videos(
    video_paths: List[str],
    output_path: str,
    transitions: Optional[List[str]] = None
) -> str:
    """Stitch Master Mode scene videos together."""
    with VideoStitcher() as stitcher:
        return stitcher.stitch_videos(video_paths, output_path, transitions)
```

### Service: `video_generation.py`

**Location**: `backend/app/services/master_mode/video_generation.py`

**Key Functions**:

#### 1. `generate_scene_video()`
- Generates video for a single scene
- Calls existing `generate_video_clip()` from pipeline
- Handles both R2V mode and Start/End frame mode
- Saves video to output directory as `scene_XX.mp4`

#### 2. `generate_all_scene_videos()`
- Generates all scene videos in parallel
- Uses `asyncio.Semaphore` for controlled parallelism (max 4 concurrent)
- Returns list of video paths (None for failed scenes)
- Handles per-scene failures gracefully

#### 3. `extract_transitions_from_cohesion()`
- Extracts transition types from cohesion analysis
- Maps transition scores to transition types:
  - Score ≥ 85: `crossfade` (smooth)
  - Score 70-84: `cut` (direct)
  - Score < 70: `fade` (gentler)

#### 4. `generate_and_stitch_videos()` (Main Orchestrator)
- Step 1: Generate all scene videos in parallel
- Step 2: Extract transitions from cohesion analysis
- Step 3: Stitch videos together using existing pipeline
- Returns final video path

## Video Generation Flow

### Step 1: Parallel Video Generation

```python
# Generate videos with controlled parallelism
semaphore = asyncio.Semaphore(4)  # Max 4 concurrent

tasks = [
    generate_scene_video(params, output_dir, scene_num)
    for params in video_params_list
]

video_paths = await asyncio.gather(*tasks)
```

**Parameters passed to Veo 3.1**:
```python
{
    "prompt": "[FULL 150-250 WORD SCENE]",
    "model": "google/veo-3.1",
    "duration": 6,
    "aspect_ratio": "16:9",
    "resolution": "1080p",
    "generate_audio": true,
    "reference_images": ["img1.jpg", "img2.jpg"],  # R2V mode
    "negative_prompt": "blurry, low quality...",
    "seed": null
}
```

### Step 2: Transition Extraction

From cohesion analysis:
```python
{
    "pair_wise_analysis": [
        {
            "from_scene": 1,
            "to_scene": 2,
            "transition_score": 88  # → "crossfade"
        },
        {
            "from_scene": 2,
            "to_scene": 3,
            "transition_score": 75  # → "cut"
        }
    ]
}
```

Maps to: `["crossfade", "cut", "crossfade"]`

### Step 3: Video Stitching

Uses **Master Mode custom stitcher** (clean implementation):
```python
final_video = stitch_master_mode_videos(
    video_paths=[
        "scene_01.mp4",
        "scene_02.mp4",
        "scene_03.mp4",
        "scene_04.mp4"
    ],
    output_path="final_video.mp4",
    transitions=["crossfade", "cut", "crossfade"]
)
```

**Stitching Steps**:
1. Load all video clips (normalize to 24fps)
2. Apply intro fade (0.3s) to first clip
3. Apply transitions between clips
4. Apply outro fade (0.3s) to last clip
5. Concatenate all clips
6. Write high-quality output (5000k bitrate)

## API Integration

### Updated Endpoint: `/api/master-mode/generate-story`

**New Parameter**: `generate_videos` (bool, default: False)

**Request**:
```bash
POST /api/master-mode/generate-story
Content-Type: multipart/form-data

prompt: "Luxury perfume ad"
reference_images: [file1, file2, file3]
generate_scenes: true
generate_videos: true  # NEW!
```

**Response** (when `generate_videos=true`):
```json
{
  "success": true,
  "story": "...",
  "scenes": {...},
  "video_generation_params": [...],
  "video_generation_status": "success",
  "final_video_path": "temp/master_mode/user-id/final_video_20251120_162530.mp4"
}
```

## File Structure

```
temp/master_mode/{user_id}/
├── reference_1_woman.jpg
├── reference_2_perfume.jpg
├── scene_videos/
│   ├── scene_01.mp4  (Scene 1 video)
│   ├── scene_02.mp4  (Scene 2 video)
│   ├── scene_03.mp4  (Scene 3 video)
│   └── scene_04.mp4  (Scene 4 video)
└── final_video_20251120_162530.mp4  (Stitched final video)
```

## Parallelism Control

**Why Limit to 4 Concurrent?**
- Veo 3.1 API rate limits
- Memory constraints
- Optimal balance of speed vs resources

```python
semaphore = asyncio.Semaphore(4)  # Max 4 concurrent videos
```

If generating 6 scenes:
- First batch: Scenes 1, 2, 3, 4 (parallel)
- Second batch: Scenes 5, 6 (parallel)

## Error Handling

### Scene Video Generation Failures
- Failed scenes return `None`
- Other scenes continue generating
- If some scenes fail, still stitch available videos
- If all scenes fail, return error

### Stitching Failures
- Logs error details
- Returns `None` as final video path
- Response includes `video_generation_status: "failed"`

## Integration with Existing Pipeline

### Reused Components:

1. **`generate_video_clip_with_model()`** from `video_generation.py`
   - Handles Veo 3.1 API calls
   - Supports R2V mode and Start/End frame mode
   - Returns tuple: `(video_path, cost)`

### New Master Mode Components:

2. **`VideoStitcher`** class in `video_stitcher.py` (NEW)
   - Custom stitcher specifically for Master Mode
   - Clean, focused implementation
   - Only 3 transition types (cut, crossfade, fade)
   - Context manager for resource cleanup
   - Better error handling and logging

### Why Not Reuse Old Stitcher?

The old pipeline stitcher (`app.services.pipeline.stitching`) has:
- Complex transitions (wipe, flash, zoom_blur, whip_pan, glitch)
- 500+ lines of code
- Tightly coupled to old pipeline logic
- Less maintainable for Master Mode needs

The new Master Mode stitcher:
- Simple, clean implementation (~300 lines)
- Only necessary transitions
- Easy to maintain and extend
- Purpose-built for Master Mode
- Better logging and error handling

## Performance

### Example: 4-Scene Ad

```
Story Generation:      ~75s  (1 iteration)
Scene Generation:      ~120s (4 scenes, 3 agents each)
Video Params:          ~1s   (metadata extraction)
Video Generation:      ~240s (4 videos @ ~60s each, parallel)
Stitching:             ~10s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total:                 ~446s (~7.5 minutes)
```

### Parallel vs Sequential

**Parallel** (current, 4 concurrent):
- 4 videos @ 60s each = ~60s total (limited by slowest)

**Sequential** (if we didn't parallelize):
- 4 videos @ 60s each = ~240s total

**Speedup**: 4x faster!

## Logging

Detailed logging at each step:
```
[Master Mode Video] Starting video generation and stitching
[Video Gen] Scene 1: Starting video generation
[Video Gen] Scene 2: Starting video generation
[Video Gen] Scene 3: Starting video generation
[Video Gen] Scene 4: Starting video generation
[Video Gen] Scene 1: Video generated with cost $0.45
[Video Gen] Scene 2: Video generated with cost $0.45
[Video Gen] Scene 3: Video generated with cost $0.45
[Video Gen] Scene 4: Video generated with cost $0.45
[Video Gen] Generated 4/4 videos successfully
[Video Gen] Extracted transitions: ['crossfade', 'cut', 'crossfade']
[Master Mode Video] Step 3: Stitching 4 videos
[Stitcher] Starting stitch: 4 clips with transitions: ['crossfade', 'cut', 'crossfade']
[Stitcher] Step 1/4: Loading video clips
[Stitcher] Loading clip 1/4: scene_01.mp4
[Stitcher] Loading clip 2/4: scene_02.mp4
[Stitcher] Loading clip 3/4: scene_03.mp4
[Stitcher] Loading clip 4/4: scene_04.mp4
[Stitcher] Step 2/4: Applying intro fade (0.3s)
[Stitcher] Step 3/4: Applying 3 transitions
[Stitcher] Step 4/4: Applying outro fade (0.3s)
[Stitcher] Concatenating clips
[Stitcher] Writing final video to: final_video.mp4
[Stitcher] ✅ Stitching complete! Duration: 12.3s, Size: 45.2MB
[Master Mode Video] Successfully created final video: final_video.mp4
[Master Mode Video] Total time: 310.5s
```

## Testing

### Test Without Video Generation (Fast)
```bash
POST /api/master-mode/generate-story
{
  "prompt": "...",
  "generate_scenes": true,
  "generate_videos": false  # Just get params
}
```

Returns `video_generation_params` but doesn't generate videos.

### Test With Video Generation (Full Pipeline)
```bash
POST /api/master-mode/generate-story
{
  "prompt": "...",
  "generate_scenes": true,
  "generate_videos": true  # Full pipeline
}
```

Generates and stitches videos, returns `final_video_path`.

## Next Steps

1. ✅ Video generation (DONE)
2. ✅ Video stitching (DONE)
3. 🔄 Audio overlay (voiceover + music) - optional enhancement
4. 🔄 Brand overlay (logo) - optional enhancement
5. 🔄 Database integration (save final video) - optional enhancement
6. 🔄 Frontend video player - optional enhancement

## Files Created/Modified

- ✅ `backend/app/services/master_mode/video_generation.py` (created)
- ✅ `backend/app/services/master_mode/video_stitcher.py` (NEW - created)
- ✅ `backend/app/services/master_mode/__init__.py` (updated exports)
- ✅ `backend/app/api/routes/master_mode.py` (added video generation)

## Dependencies

- Existing `video_generation.py` service (Veo 3.1 API calls only)
- **NEW**: Custom `video_stitcher.py` (Master Mode specific)
- `asyncio` for parallel processing
- `shutil` for file operations
- `moviepy` for video processing (crossfade, fade, concatenation)

## Transition Types

Master Mode supports 3 clean transition types:

1. **`cut`** (0.0s) - Hard cut, no transition
   - Use: Fast-paced scenes, dramatic changes
   - When: Low cohesion scores (< 70)

2. **`crossfade`** (0.5s) - Smooth blend
   - Use: Smooth scene transitions, visual continuity
   - When: High cohesion scores (≥ 85)

3. **`fade`** (0.8s) - Fade to black, then fade in
   - Use: Time passage, location changes
   - When: Medium cohesion scores (70-84)

These are automatically selected based on the Scene Cohesor's transition scores.

