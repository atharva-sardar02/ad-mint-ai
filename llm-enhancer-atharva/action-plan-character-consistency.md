# Action Plan: Character Consistency Fix

**Status**: ✅ IMPLEMENTED - Ready for Testing  
**Priority**: HIGH  
**Complexity**: Medium  
**Implementation Time**: Completed (November 18, 2025)

## Problem Statement

Test results show:
- ✅ **Product consistency**: WORKING (bottle identity maintained across scenes)
- ❌ **Character consistency**: FAILING (different women in each scene)

**Root Cause**: Character descriptions are too generic. The LLM is copying descriptions correctly, but the descriptions themselves lack the unique physical details needed for image generation models to maintain identity.

## Solution Overview

Enhance the LLM system prompt in `storyboard_planner.py` to require "police description" level detail for human characters.

## Implementation Steps

### ✅ Step 1: Add Rule #2 for Character Descriptions - COMPLETED

**File**: `backend/app/services/pipeline/storyboard_planner.py`

**Location**: Added after Rule #1 (lines 55-107)

**Implementation**: Added comprehensive Rule #2 with:
- Forensic detail requirements (age, height, build, hair, face, eyes, skin, features, expression, clothing)
- Bad vs Good examples showing generic vs police-level descriptions
- Clear explanation of WHY this matters
- Explicit copy-paste instructions for character descriptions

### ✅ Step 2: Add Character Examples to Key Points - COMPLETED

**File**: `backend/app/services/pipeline/storyboard_planner.py`

**Location**: In "Key points" section (lines 327-333)

**Implementation**: Added CHARACTER CONSISTENCY CRITICAL section with:
- Bad examples: "woman in her 30s" → Different people
- Good examples: Forensic descriptions → Same person
- Warning about guaranteed failure without detail

### ✅ Step 3: Update JSON Examples - COMPLETED

**File**: `backend/app/services/pipeline/storyboard_planner.py`

**Location**: JSON example structure and key sections

**Implementation**: Updated multiple sections:
- Line 281: Enhanced `subject_description` field with character example
- Line 137: Updated CRITICAL: SUBJECT IDENTITY section with "police description" reference
- Lines 265-272: Updated CRITICAL REMINDER with character-specific instructions

### Step 4: Validation/Warning (Optional Enhancement) - DEFERRED

**Status**: Not implemented in initial fix
**Reason**: Core fix (LLM prompt enhancement) should be sufficient
**Future**: Can add programmatic validation if needed

```python
🚨 **ABSOLUTE RULE #2: CHARACTER DESCRIPTIONS MUST BE FORENSICALLY DETAILED** 🚨

If this video features a human character (person, actor, model):
- YOU MUST PROVIDE EXTREMELY DETAILED PHYSICAL CHARACTERISTICS
- Think like a police witness providing a description for identification
- This is NOT negotiable, NOT optional, NOT flexible

REQUIRED DETAILS FOR EVERY HUMAN CHARACTER:
1. **Age**: Specific (e.g., "approximately 32 years old")
2. **Height**: Specific (e.g., "5'6" tall")
3. **Build**: Specific (e.g., "medium build, approximately 130 lbs")
4. **Hair**: 
   - Color: Specific (e.g., "chestnut brown")
   - Length: Specific (e.g., "mid-back length")
   - Style: Specific (e.g., "subtle waves, naturally side-parted on left")
   - Texture: Specific (e.g., "fine, silky texture")
5. **Face**:
   - Shape: Specific (e.g., "oval face")
   - Features: Specific (e.g., "high cheekbones, defined jawline")
   - Eyes: Color and shape (e.g., "emerald green eyes, almond-shaped")
6. **Skin**: 
   - Tone: Specific (e.g., "warm beige skin tone, Fitzpatrick Type III")
7. **Distinguishing Features**:
   - Unique markers (e.g., "small beauty mark near left eye, above cheekbone")
8. **Expression/Demeanor**:
   - (e.g., "warm, confident expression with subtle smile")
9. **Clothing**:
   - Detailed (e.g., "elegant ivory silk blouse with pearl buttons, collar style")

❌ **UNACCEPTABLE (Too Generic):**
"sophisticated woman in her 30s wearing elegant ivory silk blouse"

✅ **REQUIRED (Police Description Level):**
"Woman, approximately 32 years old, 5'6" tall, medium build (130 lbs). Long chestnut brown 
hair with subtle waves, naturally side-parted on left, reaching mid-back. Oval face with 
high cheekbones, emerald green eyes, warm beige skin tone (Fitzpatrick Type III). Small 
beauty mark near left eye, above cheekbone. Wearing elegant ivory silk blouse with pearl 
buttons. Warm, confident expression with subtle smile."

WHY THIS MATTERS:
- Image generation models need SPECIFIC physical details to maintain identity
- "Woman in her 30s" could be ANY of thousands of different people
- Each unique detail (hair color, eye color, beauty mark) helps lock in identity
- Without these details, you'll get a DIFFERENT person in each scene

THE RULE:
- Write this DETAILED character description ONCE in subject_description
- COPY it VERBATIM into every scene where the character appears
- Only add scene-specific context (position, action, lighting)
```

### Step 2: Add Character Examples to Key Points

**File**: `backend/app/services/pipeline/storyboard_planner.py`

**Location**: In "Key points" section (around line 250-270)

Add:

```python
**🚨 CHARACTER CONSISTENCY CRITICAL:**
For human characters, you MUST provide forensic-level detail:
- ❌ BAD: "athletic man in his 20s wearing black hoodie"
- ✅ GOOD: "Man, 27 years old, 6'1" tall, athletic build (180 lbs). Short dark brown hair 
  styled in textured crop, square face with strong jawline, dark brown eyes, medium tan 
  skin (Fitzpatrick Type IV). Slight scar above right eyebrow. Wearing black cotton hoodie 
  with white drawstrings. Confident, focused expression."

Without this level of detail, the character will change in every scene!
```

### Step 3: Update JSON Examples

**File**: `backend/app/services/pipeline/storyboard_planner.py`

**Location**: JSON example structure (around line 235)

Update the example to show detailed character description:

```python
{
  "consistency_markers": {
    "subject_description": "If there's a PRIMARY SUBJECT (product like a bottle, can, box OR character like a person, animal), describe it here in EXTREME detail with specific measurements, colors, materials, textures, proportions. For CHARACTERS: include age, height, build, hair (color/length/style), face (shape/features/eyes), skin tone, distinguishing features, expression, clothing details. You MUST copy this EXACT description into EVERY scene's image_generation_prompt where the subject appears. Example: 'Woman, 32, 5'6", medium build, long chestnut brown hair (side-parted left, mid-back length), oval face, high cheekbones, emerald green eyes, warm beige skin, small beauty mark near left eye. Ivory silk blouse with pearl buttons. Confident expression with subtle smile.'",
    "style_notes": "...",
    "lighting_palette": "...",
    "color_palette": "..."
  }
}
```

### Step 4: Add Validation/Warning (Optional Enhancement)

Add character description quality check:

```python
def validate_character_description(description: str) -> tuple[bool, list[str]]:
    """
    Validates that character descriptions meet minimum detail requirements.
    Returns (is_valid, missing_elements)
    """
    required_keywords = {
        'age': ['year', 'old', 'age'],
        'height': ['tall', 'height', 'feet', 'inches', "'"],
        'build': ['build', 'weight', 'lbs', 'kg'],
        'hair': ['hair'],
        'eyes': ['eye', 'eyes'],
        'skin': ['skin'],
    }
    
    missing = []
    description_lower = description.lower()
    
    for category, keywords in required_keywords.items():
        if not any(kw in description_lower for kw in keywords):
            missing.append(category)
    
    return (len(missing) == 0, missing)

# Usage in storyboard_planner (after LLM generates storyboard):
if storyboard.consistency_markers and storyboard.consistency_markers.subject_description:
    desc = storyboard.consistency_markers.subject_description
    # Check if description mentions human/person/character
    if any(word in desc.lower() for word in ['person', 'woman', 'man', 'character', 'model', 'actor']):
        is_valid, missing = validate_character_description(desc)
        if not is_valid:
            logger.warning(f"Character description may lack detail. Missing: {', '.join(missing)}")
            # Could optionally retry with additional prompt
```

## Testing Plan

### Test Case 1: Character Only

**Prompt:**
```
Fashion commercial featuring a woman. Character: Female model, 28 years old, 5'8" tall, 
slender athletic build (125 lbs). Platinum blonde hair cut in sleek bob (chin-length, 
blunt-cut), center-parted. Angular face with defined jawline, striking ice-blue eyes 
with subtle eyeliner, pale porcelain skin (Fitzpatrick Type I). Small diamond nose stud 
on right nostril. Wearing minimalist black turtleneck. Confident, intense expression 
with direct eye contact. Show her in various elegant poses and settings.
```

**Expected:**
- ✅ Same woman in all scenes (blonde bob, blue eyes, nose stud, pale skin)
- ✅ Same clothing (black turtleneck)
- ✅ Same expression/demeanor

### Test Case 2: Product + Character (Enhanced)

**Prompt:**
```
Luxury perfume commercial for "Serenity Rose". The perfume bottle: 6.5 inches tall, 
teardrop-shaped crystal-clear glass body, rose-gold metallic spherical cap (like dewdrop), 
delicate cream-colored satin ribbon tied around neck, pale blush pink liquid with subtle 
pearl shimmer, minimalist white label with "Serenity Rose" in gold cursive.

Character: Woman, 32 years old, 5'6" tall, medium build (130 lbs). Long chestnut brown 
hair with subtle waves, naturally side-parted on left, reaching mid-back. Oval face with 
high cheekbones, emerald green eyes, warm beige skin tone (Fitzpatrick Type III). Small 
beauty mark near left eye, above cheekbone. Wearing elegant ivory silk blouse with pearl 
buttons. Warm, confident expression with subtle smile.

Show scenes: bottle on vanity (Scene 1), woman discovering bottle (Scene 2), woman 
spraying perfume (Scene 3), woman experiencing fragrance (Scene 4).
```

**Expected:**
- ✅ Same bottle in all scenes (teardrop, rose-gold cap, cream ribbon)
- ✅ Same woman in all scenes (brown hair, green eyes, beauty mark)
- ✅ Both subjects maintain identity across all appearances

### Validation Checklist

After generation, check storyboard JSON:

```json
{
  "consistency_markers": {
    "subject_description": "[Should contain detailed character description with age, height, build, hair color/style, face shape, eye color, skin tone, distinguishing features, expression, clothing]"
  },
  "scenes": [
    {
      "scene_number": 1,
      "image_generation_prompt": "[Should START with EXACT COPY of detailed character description from consistency_markers]"
    },
    {
      "scene_number": 2,
      "image_generation_prompt": "[Should START with EXACT COPY of same detailed character description]"
    }
  ]
}
```

**Validation Steps:**
1. ✅ `subject_description` contains at least 8 specific details (age, height, hair, eyes, skin, etc.)
2. ✅ Each scene's `image_generation_prompt` starts with copied character description
3. ✅ Character description is IDENTICAL across all scenes (not paraphrased)
4. ✅ Only scene context varies (position, action, lighting)

## Success Criteria

**Before Fix:**
- ❌ Generic descriptions: "woman in her 30s"
- ❌ Different woman in each scene
- ❌ No unique physical identifiers

**After Fix:**
- ✅ Detailed descriptions: "Woman, 32, 5'6", chestnut brown hair, emerald eyes, beauty mark near left eye..."
- ✅ Same woman in all scenes
- ✅ Multiple unique identifiers maintained

## Implementation Time

- **Step 1**: Add Rule #2 → 15 minutes
- **Step 2**: Add examples → 10 minutes
- **Step 3**: Update JSON structure → 10 minutes
- **Step 4**: Validation (optional) → 30 minutes
- **Testing**: 30 minutes

**Total**: 1-2 hours (including testing)

## Rollout Plan

1. ✅ Document test results (DONE - test-results-perfume-woman.md)
2. ✅ Implement Rule #2 and examples in `storyboard_planner.py` (DONE - November 18, 2025)
3. 🔄 Test with character-only prompt (READY - see test-prompt-enhanced-character.md)
4. 🔄 Test with product + character prompt (READY - see test-prompt-enhanced-character.md)
5. 🔄 Validate results meet success criteria
6. ⏳ Document final results and update docs

## Risk Assessment

**Low Risk:**
- Only modifying LLM system prompt (no code changes to core logic)
- Infrastructure is already working (Master Template Copy-Paste verified)
- Changes are additive (not removing anything)
- Can easily revert if needed

**Expected Impact:**
- ✅ Significantly improved character consistency
- ✅ Better visual cohesion for multi-character scenarios
- ⚠️ Slightly longer LLM generation time (more text to process)
- ⚠️ User prompts may need to be more detailed (can be guided in UI)

## Future Enhancements

1. **Character Reference Images**
   - Allow users to upload reference image for characters
   - Use as visual seed for all scenes featuring that character

2. **Character Templates**
   - Pre-defined character archetypes with detailed descriptions
   - Users can select from templates and customize

3. **Multi-Character Support**
   - Track multiple characters independently
   - Maintain identity for Character A, Character B, etc.

4. **UI Guidance**
   - Add tooltip/help text explaining need for detailed character descriptions
   - Provide template/example for users to follow
   - Character description builder form

## References

- `test-results-perfume-woman.md` - Full test analysis
- `critical-fix-subject-identity-enforcement.md` - Infrastructure validation
- `master-template-approach.md` - Copy-paste mechanism validation
- `backend/app/services/pipeline/storyboard_planner.py` - File to modify

