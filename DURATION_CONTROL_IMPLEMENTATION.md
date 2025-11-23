# Master Mode Duration Control Implementation

## Overview
Implemented automatic detection of video duration from user prompts. The system now extracts duration mentions from the user's prompt, calculates the required number of scenes, and passes it to the Story Director agent to guide the video length.

## Critical Fix: Scene Count Calculation

### The Problem
- Veo 3.1 max scene duration: **8 seconds**
- Default 3-act structure: **3 scenes**
- Maximum video length: **3 × 8 = 24 seconds**
- User requests 60 seconds → impossible with only 3 scenes!

### The Solution
**Dynamic scene count calculation:**
```python
required_scenes = ceil(target_duration / 8)
```

**Examples:**
- 15 seconds → ceil(15/8) = **2 scenes** → use 3 (minimum for structure)
- 30 seconds → ceil(30/8) = **4 scenes**
- 45 seconds → ceil(45/8) = **6 scenes**
- 60 seconds → ceil(60/8) = **8 scenes**

## Changes Made

### 1. Duration Extraction Function (`backend/app/api/routes/master_mode.py`)

Added `extract_target_duration_from_prompt()` function that:
- Detects duration patterns like "30 seconds", "15-second video", "20s ad"
- Validates duration is within reasonable range (12-60 seconds)
- Returns `None` if no duration found or outside valid range

**Supported patterns:**
- "make a 30 second video"
- "15-second ad"
- "create a 20s advertisement"
- "video of 25 seconds"

### 2. API Endpoint Update (`backend/app/api/routes/master_mode.py`)

Modified `/api/master-mode/generate-story` endpoint to:
- Extract duration from user prompt using the new function
- Log whether duration was found or using default
- Pass `target_duration` parameter through the call chain

### 3. Streaming Wrapper Update (`backend/app/services/master_mode/streaming_wrapper.py`)

Updated `generate_story_iterative_with_streaming()` to:
- Accept `target_duration` parameter
- Pass it to the underlying story generation function

### 4. Story Generator Update (`backend/app/services/master_mode/story_generator.py`)

Updated `generate_story_iterative()` to:
- Accept `target_duration` parameter
- Log the target duration in the startup message
- Pass it to `generate_story_draft()`

### 5. Story Director Update (`backend/app/services/master_mode/story_director.py`)

Modified Story Director to:
- Accept `target_duration` parameter in `generate_story_draft()`
- **Calculate required number of scenes:** `ceil(target_duration / 8)`
- Format the system prompt with dynamic duration AND scene count guidance
- Changed prompt from hardcoded "3-5 scenes" to dynamic `{scenes_guidance}`
- Display either user-specified duration/scenes or default "12-20 seconds / 3-5 scenes"
- Updated narrative arc instructions to handle both short (3-scene) and long (4+ scene) videos

**System prompt now shows:**
- If 15s specified: "15 seconds (as specified by user)" with "3 scenes (to achieve 15s: 3 × ~5s per scene)"
- If 30s specified: "30 seconds (as specified by user)" with "4 scenes (to achieve 30s: 4 × ~7s per scene)"
- If 60s specified: "60 seconds (as specified by user)" with "8 scenes (to achieve 60s: 8 × ~7s per scene)"
- If no duration: "12-20 seconds" with "3-5 scenes, suggest 3 for simplicity"

**Narrative Arc Updates:**
- **For 3-scene videos (12-24s):** Uses classic 3-act structure (kept as-is for quality)
  - Scene 1: Establishment/Entry
  - Scene 2: Product Usage (authentic interaction)
  - Scene 3: Result + Product Showcase

- **For 4+ scene videos (25-60s):** Expands with DYNAMIC middle scenes (not repetitive!)
  - Act 1 (Scene 1): Establishment - same as 3-scene
  - Act 2 (Scenes 2 to N-1): **DYNAMIC STORY PROGRESSION** - each scene shows different moment/context:
    - Scene 2: Initial product usage (authentic action)
    - Scenes 3+: Journey through time showing:
      - Different emotional beats
      - Product benefits in different contexts
      - Transformation over time
      - Social interactions
      - Various use cases
      - Build-up of benefits
  - Act 3 (Final scene): Results + Product Showcase - same as 3-scene

**Key Quality Principles:**
- NO repetitive "multiple angles of same action" - boring!
- Each scene shows something NEW and MEANINGFUL
- Maintains emotional progression and narrative momentum
- Rich, dynamic storytelling with variety

## How It Works

### User Flow

1. **User submits prompt with duration:**
   ```
   "Create a 60 second ad for my perfume with the exact people in the images set in washington dc national mall"
   ```

2. **System extracts duration:**
   ```python
   target_duration = extract_target_duration_from_prompt(prompt)  # Returns 60
   ```

3. **System calculates required scenes:**
   ```python
   import math
   min_scenes_required = math.ceil(60 / 8)  # = 8 scenes
   required_scenes = max(3, 8)  # = 8 scenes
   ```

4. **Story Director receives guidance:**
   ```
   Recommended video duration: 60 seconds (as specified by user)
   Scene Breakdown: **CRITICAL: You MUST create EXACTLY 8 scenes** (to achieve 60s target: 8 × ~7s per scene)
   ```

5. **Story Director creates 8 dynamic scenes:**
   - **Scene 1:** Character enters National Mall, morning light (Act 1 - Establishment)
   - **Scene 2:** Opens perfume, sprays on wrist - authentic usage (Act 2 begins)
   - **Scene 3:** Walks confidently through Mall, scent trailing
   - **Scene 4:** Pauses at monument, feeling empowered
   - **Scene 5:** Subtle interaction with passerby noticing fragrance
   - **Scene 6:** Golden hour light, scent still present
   - **Scene 7:** Reflective moment, satisfaction with the experience
   - **Scene 8:** Elegant product + brand showcase (Act 3 - Resolution)
   
   Each scene: 6-8 seconds
   Total duration: ~56-64 seconds (close to 60s target)

### Scene Count Examples

| Target Duration | Min Scenes | Actual Scenes | Story Structure | Example |
|----------------|------------|---------------|-----------------|---------|
| 15 seconds | ceil(15/8) = 2 | 3 | Classic 3-act | Setup → Usage → Showcase |
| 20 seconds | ceil(20/8) = 3 | 3 | Classic 3-act | Setup → Usage → Showcase |
| 30 seconds | ceil(30/8) = 4 | 4 | Expanded | Setup → Usage → Benefit → Showcase |
| 45 seconds | ceil(45/8) = 6 | 6 | Dynamic journey | Setup → Usage → 3 varied moments → Showcase |
| 60 seconds | ceil(60/8) = 8 | 8 | Full transformation | Setup → Usage → 5 dynamic moments → Showcase |

### Backward Compatibility

If user doesn't mention duration:
- System uses default "12-20 seconds" guidance
- Story Director decides based on its standard logic
- Existing behavior is preserved

## Constraints

- **Valid range:** 12-60 seconds (enforced by extraction function)
- **Individual scenes:** 3-7 seconds (decided by Story Director)
- **Veo 3.1 constraint:** Each scene rendered as 4, 6, or 8 seconds
- **Total duration:** Sum of all scene durations (may not exactly match target)

## Example Prompts

✅ **Will extract duration:**
- "Create a 30 second video for my brand"
- "Make a 15-second advertisement"
- "Generate 45s commercial"
- "I need a 20 second ad"

❌ **Won't extract (uses default):**
- "Create a video for my brand" (no duration mentioned)
- "Make a 5 second video" (below minimum 12s)
- "Generate 90 second commercial" (above maximum 60s)

## Benefits

1. **User-friendly:** Natural language duration specification
2. **Flexible:** Story Director still has creative control within calculated scene count
3. **Backward compatible:** Works with or without duration
4. **Validated:** Rejects unrealistic durations
5. **Logged:** Clear visibility of detected vs default durations
6. **Scalable:** Automatically calculates required scenes for any duration (12-60s)
7. **Quality-preserving:** 
   - Short videos (3 scenes) maintain proven 3-act structure
   - Long videos (4+ scenes) use dynamic storytelling to avoid repetition
8. **Non-repetitive:** Each scene in longer videos shows meaningful progression, not just different camera angles

## Technical Notes

- No database schema changes required
- No frontend changes needed (works with existing form)
- All changes in backend Python code
- No breaking changes to API interface
- Linter passes with no errors

## Future Enhancements

Potential improvements:
- Add optional explicit `target_duration` form field in frontend
- Show detected duration in UI for user confirmation
- Add duration slider/selector in Master Mode interface
- Support duration ranges (e.g., "15-20 seconds")

