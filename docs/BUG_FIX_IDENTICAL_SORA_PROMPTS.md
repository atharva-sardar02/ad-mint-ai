# Bug Fix: Identical Sora-2 Prompts Across All Scenes

## Problem

All scenes in a video generation were receiving **identical Sora-2 prompts**, causing all video clips to look the same despite being different scenes (Attention, Interest, Desire, Action).

## Root Cause

The bug occurred in the LLM enhancement pipeline:

1. **Expected Flow:**
   - LLM returns a blueprint with `scene_description` objects containing fragments (visual, action, camera, lighting, mood, product_usage)
   - `_convert_sora_blueprint_to_ad_spec()` extracts these fragments
   - Scene assembler converts fragments into unique Sora-2 prompts per scene

2. **Actual Flow (Bug):**
   - LLM was returning blueprints with `visual_prompt` instead of `scene_description`
   - `_convert_sora_blueprint_to_ad_spec()` tried to extract `scene_data.get("scene_description")` → got `None`
   - All fragments became empty strings `{}`
   - Scene assembler received empty fragments and fell back to `user_prompt` for ALL scenes
   - Result: All scenes got identical prompts

## Evidence

From the database query:
```json
{
  "scenes": [
    {
      "scene_number": 1,
      "visual_prompt": "...",  // ❌ Wrong format - should be scene_description
      // Missing: "scene_description": { "visual": "...", "action": "...", ... }
    }
  ]
}
```

All scenes had `visual_prompt` but **no `scene_description` objects**, so fragments were empty.

## Fix

### 1. Added Blueprint Validation (`llm_enhancement.py`)

Before converting the blueprint, we now validate that each scene has a `scene_description` object:

```python
# --- Validate scene_description structure (CRITICAL) ---
missing_scene_descriptions = []
for i, scene in enumerate(scenes, 1):
    if "scene_description" not in scene or not scene.get("scene_description"):
        missing_scene_descriptions.append(i)

if missing_scene_descriptions:
    if attempt < max_retries:
        error_msg = (
            f"\n\nERROR: Scenes {missing_scene_descriptions} are missing 'scene_description' objects. "
            "Each scene MUST have a 'scene_description' object with fields: "
            "visual, action, camera, lighting, mood, product_usage. "
            "Do NOT use 'visual_prompt' - use 'scene_description' instead."
        )
        current_prompt += error_msg
        continue
    raise ValueError(...)
```

This forces the LLM to retry with the correct format.

### 2. Added Fragment Validation Logging (`llm_enhancement.py`)

Before calling the scene assembler, we now log warnings when fragments are missing:

```python
# --- Validate fragments before assembly ---
fragment_count = sum(1 for v in fragment_input.values() if v and isinstance(v, str) and v.strip())
if fragment_count == 0:
    logger.error(
        f"[Scene Assembler] Scene {idx} has NO fragments! "
        f"scene_description={desc}, falling back to user_prompt. "
        "This will cause identical prompts across scenes."
    )
```

### 3. Enhanced Scene Assembler Error Handling (`scene_assembler.py`)

Added explicit checks and warnings when fragments are empty:

```python
# Check if fragments are actually empty (all values are empty strings)
non_empty_count = sum(1 for v in fragment.values() if v and isinstance(v, str) and v.strip())
if non_empty_count == 0:
    logger.error(
        f"[Scene Assembler] All fragments are empty! fragment={fragment}, "
        f"falling back to user_prompt. This will cause identical prompts across scenes."
    )
    return fallback_prompt
```

## Testing

To verify the fix:

1. **Check logs** for validation messages:
   - `[Stage 1 LLM] Blueprint validated: 4 scenes with scene_description objects`
   - `[Scene Assembler] Scene X has Y fragments: ...`

2. **Check for errors**:
   - `[Scene Assembler] Scene X has NO fragments!` → indicates the bug
   - `ERROR: Scenes [X] are missing 'scene_description' objects` → LLM retry triggered

3. **Verify prompts are different**:
   - Query the database and check that `scene_plan.scenes[].visual_prompt` values are unique
   - Check logs for `EXACT SORA-2 PROMPT FOR SCENE X` - they should differ

## Prevention

The fix ensures:
- ✅ LLM must return correct format or retry
- ✅ Empty fragments are detected and logged
- ✅ Fallback behavior is explicit and warned
- ✅ Debug logging shows fragment values

## Related Files

- `backend/app/services/pipeline/llm_enhancement.py` - Blueprint validation
- `backend/app/services/pipeline/scene_assembler.py` - Fragment validation
- `backend/app/services/pipeline/scene_planning.py` - Scene enrichment (not affected)

## Next Steps

1. Monitor logs for the validation messages
2. If LLM continues to return wrong format, consider:
   - Strengthening the system prompt
   - Adding example JSON in the prompt
   - Using structured outputs (if available)

