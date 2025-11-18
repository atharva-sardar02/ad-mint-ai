# Test Results: Perfume + Woman Prompt

**Date**: November 18, 2025  
**Test Prompt**: Luxury perfume commercial featuring "Serenity Rose" with woman using the perfume

## Test Configuration

- **Target Duration**: 15 seconds
- **Expected Scenes**: 3-4 scenes
- **Primary Subject**: Teardrop-shaped perfume bottle (Serenity Rose)
- **Secondary Character**: Woman in her 30s

## Test Results Summary

| Aspect | Status | Details |
|--------|--------|---------|
| **Bottle Identity** | ✅ **PARTIAL SUCCESS** | Same bottle type maintained across scenes |
| **Bottle Size** | ❌ **FAILED** | Size variations between scenes |
| **Woman Identity** | ❌ **FAILED** | Different women in different scenes |
| **Visual Cohesion** | ⚠️ **PARTIAL** | Style consistent, but subjects inconsistent |

## Detailed Analysis

### 1. Bottle Identity: Partial Success ✅

**What Worked:**
- ✅ Bottle shape maintained (teardrop crystal glass)
- ✅ Bottle color consistent (crystal clear with blush pink liquid)
- ✅ Bottle features consistent (rose-gold cap, cream ribbon, label)
- ✅ Master Template Copy-Paste Approach IS WORKING

**What Failed:**
- ❌ Size inconsistency: Bottle appeared at different scales across scenes
- ❌ Proportions varied slightly between scenes

**Root Cause:**
- The LLM successfully copied the subject description across scenes ✅
- Image generation model (Nano Banana) is interpreting "6.5 inches tall" differently in each context ❌
- Problem: No absolute size reference in images, so model uses relative framing

### 2. Character Consistency: Complete Failure ❌

**What Failed:**
- ❌ Scene 2: Different woman than expected
- ❌ Scene 3: Another different woman
- ❌ Scene 4: Yet another different woman

**Root Cause:**
- The prompt described the woman generically: "sophisticated woman in her 30s wearing elegant ivory silk blouse"
- LLM likely DID copy this description across scenes
- But this description is TOO GENERIC for character identity:
  - ❌ No facial features specified
  - ❌ No hair color/style specified
  - ❌ No skin tone specified
  - ❌ No body type specified
  - ❌ Only clothing: "ivory silk blouse" (easy to replicate, but not unique)

**The Problem:**
Unlike the bottle (which has 6+ unique identifiers), the woman description had ZERO unique physical identifiers.

## Why This Happened

### Bottle (Partial Success):

**Unique Identifiers Provided:**
1. ✅ "teardrop-shaped crystal-clear glass body"
2. ✅ "rose-gold metallic spherical cap (like a dewdrop)"
3. ✅ "delicate cream-colored satin ribbon tied around neck"
4. ✅ "pale blush pink liquid with subtle pearl shimmer"
5. ✅ "minimalist white label with 'Serenity Rose' in gold cursive"
6. ✅ "6.5 inches tall" (but failed to enforce)

**Result:** Image model recognized the unique features and maintained them across scenes, BUT couldn't maintain absolute size without visual anchors.

### Woman (Complete Failure):

**Unique Identifiers Provided:**
1. ❌ "sophisticated woman in her 30s" (generic age/vibe)
2. ❌ "wearing elegant ivory silk blouse" (clothing only, not physical traits)

**Result:** Image model generated any woman fitting this vague description in each scene. No unique physical features to maintain identity.

## Lessons Learned

### ✅ What's Working:

1. **Master Template Copy-Paste Approach is effective**
   - LLM IS copying subject descriptions across scenes
   - Text prompts ARE maintaining consistency
   
2. **Detailed Product Descriptions Work**
   - Bottle identity maintained (shape, color, features)
   - Multiple unique identifiers help

### ❌ What's NOT Working:

1. **Size/Scale Consistency**
   - Problem: "6.5 inches tall" means nothing without reference
   - Image model cannot maintain absolute dimensions across scenes
   - Relative framing changes based on scene context

2. **Generic Character Descriptions Fail**
   - "Woman in her 30s" = thousands of possibilities
   - Need DETAILED physical characteristics:
     - Hair: color, length, style (e.g., "long chestnut brown hair with subtle waves, side-parted")
     - Face: features (e.g., "oval face with high cheekbones, green eyes, warm skin tone")
     - Body: type (e.g., "medium build, 5'6" tall")
     - Distinguishing features (e.g., "small mole near left eye")

3. **Sequential Image Generation for Characters**
   - Currently using sequential generation for reference, start, end images
   - BUT: Text override is stronger than visual reference for humans
   - Even passing previous image, if text says "woman in her 30s," model will generate ANY woman

## Critical Insights

### Image Generation Hierarchy:

```
Text Prompt (STRONGEST influence)
    ↓
Visual Reference Image
    ↓
Model's Training Data
```

**For Products (Bottles):**
- Detailed text + visual reference = ✅ Identity maintained
- But size/scale still varies without absolute anchors

**For Humans:**
- Generic text + visual reference = ❌ Identity lost
- Need EXTREMELY detailed text (like police description) + visual reference

### The "Police Description" Standard:

To maintain character identity, we need descriptions as detailed as a police witness statement:

**Bad (Generic):**
```
"sophisticated woman in her 30s wearing elegant ivory silk blouse"
```

**Good (Police Description):**
```
"Woman, approximately 32 years old, 5'6" tall, medium build (130 lbs). Long chestnut brown hair with subtle waves, naturally side-parted on left, reaching mid-back. Oval face with high cheekbones, emerald green eyes, warm beige skin tone (Fitzpatrick Type III). Small beauty mark near left eye, above cheekbone. Elegant ivory silk blouse with pearl buttons. Warm, confident expression with subtle smile."
```

## Required Fixes

### 1. Fix Character Consistency (HIGH PRIORITY)

**Solution A: Extremely Detailed Character Descriptions**

Update `storyboard_planner.py` to require "police description" level detail for human characters:

```python
🚨 **RULE #2: CHARACTER DESCRIPTIONS MUST BE FORENSICALLY DETAILED** 🚨

If this video features a human character, you MUST provide:
- Age: Specific (e.g., "approximately 32 years old")
- Height: Specific (e.g., "5'6" tall")
- Build: Specific (e.g., "medium build, approximately 130 lbs")
- Hair: Color, length, style, texture (e.g., "long chestnut brown hair with subtle waves, naturally side-parted on left, reaching mid-back")
- Face: Shape, features (e.g., "oval face with high cheekbones, emerald green eyes")
- Skin: Tone (e.g., "warm beige skin tone, Fitzpatrick Type III")
- Distinguishing features: Unique markers (e.g., "small beauty mark near left eye")
- Expression/demeanor: (e.g., "warm, confident expression with subtle smile")

❌ BAD: "sophisticated woman in her 30s"
✅ GOOD: "Woman, 32, 5'6", medium build, long chestnut brown hair (side-parted left), oval face, high cheekbones, emerald eyes, warm beige skin, small beauty mark near left eye"
```

**Solution B: Character Reference Images** (Future Enhancement)

Allow users to upload reference images for characters:
- User uploads image of desired actor/model
- System uses this as visual reference for all scenes
- Maintains character identity through visual consistency

### 2. Fix Size Consistency (MEDIUM PRIORITY)

**Solution A: Add Size Reference Objects**

Include size reference objects in scene descriptions:

```python
# For bottle
"6.5-inch tall perfume bottle on standard 12-inch square marble tile (for size reference)"

# For character
"Woman, 5'6" tall, standing next to standard 6-foot doorframe (for size reference)"
```

**Solution B: Relative Size Constraints**

Add explicit relative size instructions:

```python
"CRITICAL: Maintain consistent bottle-to-hand proportions across all scenes where both appear. The bottle should be approximately 60% the length of the hand."
```

**Solution C: Accept Size Variation as Limitation**

Document that slight size variations are acceptable if:
- Subject identity is maintained (shape, color, features)
- Variation is minimal (within 10-15%)
- Cinematic framing justifies it (close-ups vs. wide shots)

## Testing Recommendations

### Test Case 1: Product Only (Bottle)
**Goal:** Verify bottle identity and size consistency

**Prompt:**
```
Luxury perfume advertisement for "Lumière Noir". The perfume bottle is sleek and sophisticated: 8 inches tall with a frosted matte black glass body (cylindrical shape, 2.5 inches diameter), gold metallic crown-shaped cap (1.5 inches tall with ornate engravings), minimalist rectangular gold label with "Lumière Noir" embossed text (0.5 inches tall), deep amber liquid visible inside. Create a cinematic commercial showing the bottle in various elegant settings.
```

**Expected:**
- ✅ Same bottle in all scenes (shape, color, cap, label, liquid)
- ⚠️ Slight size variations acceptable (within 10%)

### Test Case 2: Human Character Only
**Goal:** Verify character identity consistency

**Prompt:**
```
Fashion commercial featuring a woman. Character description: Female model, 28 years old, 5'8" tall, slender athletic build (125 lbs). Platinum blonde hair cut in a sleek bob (chin-length, blunt-cut), naturally parted in center. Angular face with defined jawline, striking ice-blue eyes with subtle eyeliner, pale porcelain skin (Fitzpatrick Type I). Small diamond nose stud on right nostril. Wearing minimalist black turtleneck. Confident, intense expression with direct eye contact. Create a cinematic fashion video showing her in various elegant poses and settings.
```

**Expected:**
- ✅ Same woman in all scenes (hair, face, eyes, skin, nose stud)
- ✅ Same clothing (black turtleneck)
- ✅ Same expression/demeanor

### Test Case 3: Product + Character (Current Test)
**Goal:** Verify both product and character identity

**Retest with enhanced character description:**
```
[Keep same bottle description]

Character: Woman, approximately 32 years old, 5'6" tall, medium build (130 lbs). Long chestnut brown hair with subtle waves, naturally side-parted on left, reaching mid-back. Oval face with high cheekbones, emerald green eyes, warm beige skin tone (Fitzpatrick Type III). Small beauty mark near left eye, above cheekbone. Wearing elegant ivory silk blouse with pearl buttons. Warm, confident expression with subtle smile.
```

**Expected:**
- ✅ Same bottle in all scenes
- ✅ Same woman in all scenes (brown hair, green eyes, beauty mark)
- ✅ Same blouse

## Action Items

### Immediate (Do Now):

1. ✅ Document test results (this file)
2. 🔄 Update `storyboard_planner.py`:
   - Add Rule #2 for character descriptions
   - Add examples of good vs. bad character descriptions
   - Require "police description" level detail
3. 🔄 Update prompt engineering docs
4. 🔄 Test with enhanced character descriptions

### Short-term (Next Sprint):

1. Add size reference object instructions
2. Test size consistency improvements
3. Add UI guidance for character descriptions
4. Create character description template

### Long-term (Future Enhancement):

1. Character reference image upload
2. Multi-subject tracking system
3. Advanced consistency validation
4. Character consistency scoring

## Conclusion

**The Master Template Copy-Paste Approach IS WORKING** ✅

The problem is NOT in the LLM's ability to copy descriptions. The problem is in the QUALITY and SPECIFICITY of the descriptions being copied:

- ✅ **Bottle**: 6 unique identifiers → Identity maintained
- ❌ **Woman**: 2 vague descriptors → Identity lost

**Solution:** Require "police description" level detail for ALL subjects (products AND characters).

This is a **prompt engineering fix**, not a code fix. The infrastructure is working correctly.

