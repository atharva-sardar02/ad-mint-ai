# Appearance Sanitizer Implementation

## Date: 2025-11-22

## Problem Statement

Even though we provide the same reference images to all video generations, Veo 3.1 produces inconsistent character appearances across scenes because:

**Text prompts were "fighting" with reference images** - When prompts contain physical descriptions (face, hair, race, body), Veo 3.1 tries to blend:
1. What it sees in the reference image
2. What the text describes  
3. Its own interpretation

Result: Each generation is slightly different because the model is confused about which source to trust.

## Solution

Created a comprehensive **Appearance Sanitizer** that removes ALL physical appearance descriptions from video generation prompts BEFORE sending to Veo 3.1.

This makes **reference images the SOLE source of truth** for character appearance.

## Implementation

### New File: `backend/app/services/master_mode/appearance_sanitizer.py`

**Features:**
- Removes 100+ appearance-related terms (face, hair, race, body, etc.)
- Uses regex patterns to catch complex descriptions
- Preserves reference phrases like "the exact same person from Reference Image 1"
- Cleans up text formatting after removal
- Detailed logging of what was removed

**What Gets Removed:**
- ✅ Face features: eyes, nose, lips, jawline, complexion, skin tone
- ✅ Hair: color, style, length, texture
- ✅ Race/ethnicity: caucasian, asian, african, hispanic, etc.
- ✅ Body: muscular, athletic, slim, tall, short, build
- ✅ Age descriptors: "32-year-old", "in his early 30s"
- ✅ Specific measurements: height, weight

**What Gets Kept:**
- ✅ Reference phrases: "the exact same person from Reference Image 1"
- ✅ Actions: "picks up", "walks toward", "gestures"
- ✅ Emotions: "confident", "determined", "joyful"
- ✅ Wardrobe: "wearing a gray sweater", "elegant dress"
- ✅ Environment: "modern living room", "marble countertop"
- ✅ Technical specs: lighting, camera angles, cinematography

### Integration

**Modified: `backend/app/services/master_mode/scene_to_video.py`**

Added as **Step 3** after scene enhancement and alignment:

```python
# Step 3: Sanitize appearance descriptions from prompts (NEW)
logger.info("[Scene→Video] Step 3: Sanitizing appearance descriptions from prompts")
video_params_list = sanitize_all_video_params(video_params_list)
logger.info("[Scene→Video] ✅ Prompts sanitized - reference images are now sole source of appearance")
```

This runs automatically for every Master Mode generation.

## Example

### BEFORE Sanitization:
```
A 32-year-old man with short brown hair, blue eyes, and a strong jawline 
stands in a modern living room. He has an athletic build, standing 
approximately 6 feet tall, wearing a charcoal gray sweater. His face 
shows determination as he looks toward the window.
```

### AFTER Sanitization:
```
A man stands in a modern living room, wearing a charcoal gray sweater. 
He shows determination as he looks toward the window.
```

**Result:**
- ❌ Removed: age, hair color, eye color, jawline, athletic build, height
- ✅ Kept: setting, wardrobe, emotion, action

Veo 3.1 now relies ONLY on the reference image for appearance!

## Testing

Run the test script to see before/after examples:

```bash
cd D:\gauntlet-ai\ad-mint-ai\backend
python -m app.services.master_mode.test_appearance_sanitizer
```

## Expected Results

### Before This Fix:
- Scene 1: Man looks like reference image
- Scene 2: Man's face slightly different (model blending text + image)
- Scene 3: Man's face noticeably different (more text influence)

### After This Fix:
- Scene 1: Man looks like reference image
- Scene 2: Man SHOULD look like reference image (no text interference)
- Scene 3: Man SHOULD look like reference image (no text interference)

**Note:** This doesn't guarantee 100% consistency (Veo 3.1 still has model limitations), but it removes the #1 cause of inconsistency (text prompt interference).

## Logging

You'll see detailed logs during generation:

```
[Appearance Sanitizer] Sanitizing 3 video prompts
[Appearance Sanitizer] Scene 1: 450 -> 320 chars (28.9% removed)
[Appearance Sanitizer] Scene 2: 480 -> 340 chars (29.2% removed)
[Appearance Sanitizer] Scene 3: 420 -> 350 chars (16.7% removed)
[Appearance Sanitizer] ✅ All prompts sanitized - reference images are now sole source of appearance
```

## Files Changed

1. ✅ **Created**: `backend/app/services/master_mode/appearance_sanitizer.py` (new module)
2. ✅ **Modified**: `backend/app/services/master_mode/scene_to_video.py` (integrated sanitizer)
3. ✅ **Created**: `backend/app/services/master_mode/test_appearance_sanitizer.py` (test/demo)

## Next Steps

1. **Restart backend** to apply changes:
   ```bash
   cd D:\gauntlet-ai\ad-mint-ai\backend
   python -m uvicorn app.main:app --reload
   ```

2. **Generate a new Master Mode video** and check consistency

3. **Check logs** to see what was removed from prompts

## Benefits

✅ **Reference images are now the sole source of appearance**
✅ **No more text/image "fighting"**
✅ **Should significantly improve character consistency across scenes**
✅ **Automatic - no user action required**
✅ **Preserves all non-appearance details** (story, emotion, cinematography)

## Limitations

This fixes Text Prompt Interference (Issue #1), but doesn't address:
- Veo 3.1's inherent consistency limitations (model issue)
- Multiple reference image confusion (model issue)
- Random seed variation (model issue)

For those issues, consider the other options discussed (face swap, different model, etc.).

---

**Status**: ✅ IMPLEMENTED AND INTEGRATED

**Ready to test!** 🚀

