# Subject Consistency Improvements

## Problem Identified
User reported that different clips showed different perfume bottles (or different versions of the main subject), breaking visual continuity. The subject (whether it's a perfume bottle, character, or product) was changing appearance between scenes.

## Key Insight
**The subject doesn't need to appear in EVERY scene, but when it DOES appear, it must be IDENTICAL.**

- Some scenes might be:
  - Establishing shots (environment without product)
  - Close-ups of secondary elements (flowers, textures)
  - Abstract/artistic moments
  - Transitional shots
- BUT: When the subject appears, it must look EXACTLY the same across all scenes

## Solutions Implemented

### 1. Enhanced LLM System Prompt (`storyboard_planner.py`)

Added **CRITICAL: SUBJECT IDENTITY CONSISTENCY** section that explicitly states:
- Subject doesn't need to appear in every scene (creative freedom)
- When subject DOES appear, it must be IDENTICAL
- Specific examples for different subject types (perfume bottle, character, product)
- Instructions to establish subject characteristics in Scene 1
- Instructions to reference "the same [subject] from Scene 1" in subsequent scenes
- Guidance to use `subject_presence: "none"` for scenes without the subject

### 2. New Consistency Marker: `subject_description`

Added a new field in `consistency_markers`:
```json
{
  "consistency_markers": {
    "style": "...",
    "color_palette": "...",
    "lighting": "...",
    "composition": "...",
    "mood": "...",
    "subject_description": "EXTREMELY detailed description of main subject..."
  }
}
```

**Example for perfume bottle:**
```
"subject_description": "8-inch tall perfume bottle with frosted matte glass body, 
silver metallic cap (1-inch diameter), thin rose gold metallic rectangular label 
with embossed text, rose gold liquid visible inside, subtle hexagonal facets on 
bottle sides, narrow neck transitioning to rounded shoulders"
```

This description is:
- Used across ALL scenes where the subject appears
- Extremely detailed (dimensions, colors, materials, textures, shapes, branding)
- Specific enough that an artist could recreate the exact same subject

### 3. Enhanced Image Generation Prompts (`image_generation_batch.py`)

Modified `_build_enhanced_image_prompt()` to:

**For Scene 1 (where subject first appears):**
```
| PRIMARY SUBJECT SPECIFICATION: [detailed subject description]
```

**For Scenes 2+ (where subject appears):**
```
| SUBJECT CONSISTENCY (if subject appears in this scene): [detailed subject description] 
- If the subject appears in this scene, it must be the EXACT SAME subject with 
IDENTICAL appearance as established in Scene 1
```

**For ALL scenes:**
```
| CRITICAL VISUAL CONSISTENCY: This image must maintain exact visual consistency 
with the reference image - ESPECIALLY THE SUBJECT MUST BE IDENTICAL (same exact 
design, same exact appearance, same exact proportions, same exact colors, same 
exact materials), same lighting direction, same style, same visual universe.
```

### 4. Updated Image Generation Prompt Instructions

Enhanced the LLM instructions for `image_generation_prompt`:
- **For Scene 1**: Establish detailed specs with exact measurements and characteristics
- **For Scenes 2+**: Start with "The EXACT SAME [subject type] from Scene 1"
- Explicitly state "maintaining identical appearance"
- Reference the exact specs from Scene 1

### 5. Updated Image Continuity Notes

Modified to conditionally emphasize subject:
- **IF SUBJECT APPEARS**: "The EXACT SAME [subject] from Scene X must appear with IDENTICAL appearance"
- **IF SUBJECT DOES NOT APPEAR**: Describe visual relationship without forcing subject

### 6. Conditional Subject Enforcement

The image generation prompt enhancement now:
- Includes subject description for Scene 1 (establishing)
- For Scenes 2+: Only emphasizes subject IF it appears in that scene
- Doesn't force the subject into scenes where `subject_presence: "none"`
- The LLM's base prompt naturally excludes subject mentions when appropriate

## How It Works in Practice

### Example: Perfume Commercial with 3 Scenes

**Scene 1: Product Introduction** (`subject_presence: "full"`)
- LLM establishes detailed subject description in `subject_description` field
- Image generation prompt includes: "PRIMARY SUBJECT SPECIFICATION: 8-inch tall perfume bottle..."
- Reference image generated with these exact specs

**Scene 2: Artistic Flower Close-up** (`subject_presence: "none"`)
- LLM base prompt focuses on flowers, petals, textures
- Subject description still included but as conditional: "if subject appears in this scene"
- Since base prompt doesn't mention subject, image generation focuses on flowers
- Visual style, colors, lighting remain consistent

**Scene 3: Product with Flowers** (`subject_presence: "full"`)
- LLM base prompt describes the SAME bottle from Scene 1 with flowers
- Image generation prompt includes: "SUBJECT CONSISTENCY: 8-inch tall perfume bottle... must be EXACT SAME subject with IDENTICAL appearance as established in Scene 1"
- Reference image from Scene 1 is used as visual reference
- Result: Same bottle as Scene 1, now composed with flowers

## Key Technical Changes

### Files Modified:
1. `backend/app/services/pipeline/storyboard_planner.py`
   - Enhanced system prompt with subject consistency instructions
   - Added `subject_description` to consistency markers JSON structure
   - Updated all prompt type instructions to emphasize subject identity

2. `backend/app/services/pipeline/image_generation_batch.py`
   - Modified `_build_enhanced_image_prompt()` to prioritize subject description
   - Added conditional logic for Scene 1 vs. subsequent scenes
   - Strengthened final consistency instruction to emphasize subject identity

## Expected Results

- **Better Subject Consistency**: Same perfume bottle (or character, or product) across all scenes where it appears
- **Creative Freedom**: Scenes can exclude the subject when narratively appropriate
- **Stronger Visual Cohesion**: Detailed subject specifications ensure identical appearance
- **Reference Chain Effectiveness**: Sequential image generation uses previous images with explicit subject consistency instructions

## Testing Recommendations

When testing, verify:
1. ✅ Subject appears identical in all scenes where it's present
2. ✅ Subject can be absent from some scenes (establishing shots, etc.)
3. ✅ Subject specifications are detailed and specific
4. ✅ Scenes without subject still maintain overall visual style
5. ✅ Reference images effectively maintain subject consistency

## Future Enhancements (Optional)

- **Subject Verification**: Add post-generation check to verify subject consistency across scenes
- **Subject Templates**: Pre-defined subject descriptions for common product types
- **Subject Comparison**: Automated comparison of subject appearance across scenes
- **Subject Locking**: Option to upload a "golden" subject image that all scenes must match

