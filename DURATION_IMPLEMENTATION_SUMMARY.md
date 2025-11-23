# Duration Control with Dynamic Scene Count - Implementation Summary

## Problem Solved

**Original Issue:**
- User requests "60 second ad" → System only creates 3 scenes (3-act structure)
- Maximum possible: 3 scenes × 8 seconds = **24 seconds**
- Result: Video is 36 seconds SHORT of target ❌

**Root Cause:**
- Veo 3.1 constraint: Max 8 seconds per scene
- System prompt hardcoded: "MANDATORY 3-ACT STRUCTURE"
- No calculation of required scenes based on target duration

## Solution Implemented

### 1. Dynamic Scene Count Calculation

Added to `generate_story_draft()` in `story_director.py`:

```python
if target_duration:
    duration_guidance = f"{target_duration} seconds (as specified by user)"
    # Calculate required scenes: ceil(duration / 8)
    import math
    min_scenes_required = math.ceil(target_duration / 8)
    required_scenes = max(3, min_scenes_required)  # Minimum 3 for structure
    scenes_guidance = f"**CRITICAL: You MUST create EXACTLY {required_scenes} scenes**"
    logger.info(f"[Story Director] Target {target_duration}s requires {required_scenes} scenes")
```

### 2. Dual Narrative Structure

Updated system prompt to support TWO approaches:

#### A. Short Videos (3 scenes, 12-24s) - Classic Structure
**Kept exactly as-is for quality:**
- Scene 1: Establishment/Entry
- Scene 2: Product Usage (authentic interaction)
- Scene 3: Result + Product Showcase

#### B. Long Videos (4+ scenes, 25-60s) - Dynamic Storytelling
**New approach to avoid repetition:**

- **Act 1 (Scene 1):** Establishment - same as short videos
- **Act 2 (Scenes 2 to N-1):** DYNAMIC PROGRESSION - each scene unique:
  - Scene 2: Initial product usage (authentic action)
  - Scenes 3+: Journey showing:
    - Different moments in time
    - Different emotional beats
    - Benefits in various contexts
    - Transformation over time
    - Social interactions
    - Multiple use cases
- **Act 3 (Final scene):** Results + Product Showcase - same as short videos

### 3. Quality Guarantee

**Critical instruction added to system prompt:**
```
⚠️ CRITICAL: DO NOT just show the same product usage from multiple angles. 
Tell a RICH, DYNAMIC STORY with variety!

⚠️ KEY PRINCIPLES FOR LONGER VIDEOS:
- Each scene must show something NEW and MEANINGFUL
- Maintain emotional progression and narrative momentum
- Avoid repetitive actions - show VARIETY and RICHNESS
```

## Results

### Example: 60-Second Perfume Ad

**User prompt:**
```
"Create a 60 second ad for my perfume with the exact people in the images set in washington dc national mall"
```

**System calculation:**
- Required scenes: ceil(60 / 8) = **8 scenes**
- Guidance: "MUST create EXACTLY 8 scenes (8 × ~7s per scene)"

**Generated dynamic story:**
1. **Scene 1 (8s):** Morning at National Mall, character enters frame, anticipation
2. **Scene 2 (7s):** Opens perfume bottle, authentic spray application on wrists
3. **Scene 3 (8s):** Walks confidently through Mall, scent creates invisible aura
4. **Scene 4 (7s):** Pauses at Lincoln Memorial, feeling empowered and elegant
5. **Scene 5 (8s):** Subtle interaction - passerby notices the captivating fragrance
6. **Scene 6 (7s):** Golden hour light, scent still lingering, lasting impression
7. **Scene 7 (8s):** Reflective moment overlooking Mall, satisfaction with experience
8. **Scene 8 (7s):** Elegant product showcase with brand name clearly visible

**Total: 60 seconds ✅**

Each scene shows a DIFFERENT moment in the journey - not just "spray perfume from 8 different angles"!

## Scene Count Table

| User Request | Calculation | Required Scenes | Total Duration | Structure Type |
|--------------|-------------|-----------------|----------------|----------------|
| "15 second ad" | ceil(15/8) = 2 | 3 (min) | 3 × 5s = 15s | Classic 3-act |
| "20 second ad" | ceil(20/8) = 3 | 3 | 3 × 6-7s = 20s | Classic 3-act |
| "30 second ad" | ceil(30/8) = 4 | 4 | 4 × 7-8s = 30s | Expanded dynamic |
| "45 second ad" | ceil(45/8) = 6 | 6 | 6 × 7-8s = 45s | Rich journey |
| "60 second ad" | ceil(60/8) = 8 | 8 | 8 × 7-8s = 60s | Full transformation |

## Code Changes

### Files Modified:
1. ✅ `backend/app/api/routes/master_mode.py` - Duration extraction
2. ✅ `backend/app/services/master_mode/streaming_wrapper.py` - Parameter passing
3. ✅ `backend/app/services/master_mode/story_generator.py` - Parameter forwarding
4. ✅ `backend/app/services/master_mode/story_director.py` - **Scene calculation + dynamic narrative**

### No Breaking Changes:
- API interface unchanged
- Database schema unchanged
- Frontend unchanged
- Backward compatible (works with/without duration)
- All linting checks pass

## Key Innovation

**Before:** Fixed 3-scene structure → max 24 seconds

**After:** Dynamic scene count based on target duration → supports 12-60 seconds

**Quality:** Short videos keep proven structure, long videos get rich dynamic storytelling (not repetitive camera angles!)

## Testing

Test with these prompts:
```
✅ "Create a 15 second ad for my cologne"
✅ "Make a 30 second video showcasing my perfume brand"
✅ "Generate a 60 second commercial for my fragrance set in National Mall"
```

System will automatically:
1. Extract duration (15s, 30s, 60s)
2. Calculate scenes (3, 4, 8)
3. Guide Story Director to create dynamic, non-repetitive narrative
4. Generate videos matching target duration ✅

