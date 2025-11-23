# Fix: Scene Count Mismatch - 60 Second Video Generating Only 32 Seconds

## Problem Identified

**User Request:** "Create a 60 second ad..."

**What Happened:**
1. ✅ Story Director correctly calculated: **8 scenes needed** (line 32, 59, 86 in logs)
   ```
   [Story Director] Target 60s requires 8 scenes (7.5 at 8s max)
   ```

2. ❌ Scene Generator failed to detect scenes: **Defaulted to 4 scenes** (line 116-117 in logs)
   ```
   WARNING | Could not extract scene count from story, defaulting to 4
   INFO | Detected 4 scenes in story
   ```

3. ❌ Result: **Only 32 seconds generated** instead of 60 seconds
   - 4 scenes × 8 seconds = 32 seconds

## Root Cause

**Disconnect in Information Flow:**

```
Story Director                     Scene Generator
     ↓                                   ↓
Calculates: 8 scenes          Tries to extract via regex
Writes story with 8 scenes    Regex fails: finds only 4
     ↓                                   ↓
Returns story                 Generates only 4 scenes
     ❌ (scene count lost)         ❌ (28 seconds short!)
```

The Scene Generator was using **fragile regex parsing** to extract scene count:
```python
scene_matches = re.findall(r'###\s*Scene\s+(\d+)', story, re.IGNORECASE)
```

If Story Director writes scenes in a slightly different format (e.g., `**Scene 1:**` instead of `### Scene 1:`), the regex fails and defaults to 4 scenes.

## Solution Implemented

**Pass Expected Scene Count Through the Pipeline:**

```
Story Director                     Scene Generator
     ↓                                   ↓
Calculates: 8 scenes           Receives: expected_scene_count=8
Writes story with 8 scenes     Uses passed value (reliable!)
     ↓                                   ↓
Returns StoryGenerationResult  Generates all 8 scenes
  .expected_scene_count = 8         ✅ (60 seconds achieved!)
```

### Files Modified

1. **`backend/app/services/master_mode/schemas.py`**
   - Added `expected_scene_count` field to `StoryGenerationResult`

2. **`backend/app/services/master_mode/story_generator.py`**
   - Calculate expected scene count from target duration
   - Store it in the result object
   - Log it for visibility

3. **`backend/app/services/master_mode/scene_generator.py`**
   - Accept `expected_scene_count` parameter
   - Use it instead of relying solely on regex
   - Log warning if extracted count differs from expected

4. **`backend/app/services/master_mode/streaming_wrapper.py`**
   - Pass `expected_scene_count` through wrapper function

5. **`backend/app/api/routes/master_mode.py`**
   - Pass `story_result.expected_scene_count` to scene generation

## How It Works Now

### Example: 60-Second Request

**Step 1: Story Director Calculates**
```python
target_duration = 60  # seconds
min_scenes_required = ceil(60 / 8)  # = 8 scenes
expected_scene_count = max(3, 8)  # = 8 scenes
```

**Step 2: Story Director Saves**
```python
result = StoryGenerationResult(
    final_story=story_draft,
    expected_scene_count=8  # ✅ Saved!
    # ... other fields
)
```

**Step 3: Scene Generator Uses**
```python
if expected_scene_count:
    total_scenes = expected_scene_count  # = 8 ✅
    logger.info(f"Using expected scene count: {total_scenes}")
else:
    total_scenes = _extract_scene_count_from_story(story)  # fallback
```

**Step 4: Generate All 8 Scenes**
```
Scene 1: 8 seconds
Scene 2: 8 seconds  
Scene 3: 8 seconds
Scene 4: 8 seconds
Scene 5: 8 seconds
Scene 6: 8 seconds
Scene 7: 8 seconds
Scene 8: 8 seconds
-------------------
Total: 64 seconds ✅ (close to 60s target)
```

## Benefits

1. **Reliable:** No longer depends on regex parsing
2. **Accurate:** Uses calculated value directly from Story Director
3. **Fallback:** Still attempts regex extraction if expected count not provided
4. **Logged:** Clear visibility when counts differ
5. **Backward Compatible:** Works with/without expected_scene_count

## Expected Log Output (Next Run)

```
[Story Director] Target 60s requires 8 scenes (7.5 at 8s max)
[Story Generator] Expected scene count for 60s: 8 scenes
[Story Generator] Expected scene count: 8
[Master Mode] Expected scene count: 8
[Streaming] Starting scene generation with streaming for {id}
[Scene Generator] Using expected scene count from Story Director: 8 scenes
=== Processing Scene 1/8 ===
=== Processing Scene 2/8 ===
...
=== Processing Scene 8/8 ===
[Scene Generator] Total scenes: 8
[Video Gen] Generated 8/8 videos successfully
[Stitcher] Starting stitch: 8 clips
```

## Testing

Test with these prompts:
- "Create a 60 second ad..." → Should generate 8 scenes ✅
- "Make a 45 second video..." → Should generate 6 scenes ✅
- "Generate a 30 second ad..." → Should generate 4 scenes ✅
- "Create an ad..." (no duration) → Should generate 3 scenes (default) ✅

All linting checks passed ✅

