# Master Template Approach: Subject Description as Copy-Paste Template

## The Core Problem

Even with all our instructions, the LLM was creating **different subject descriptions** for each scene:

- **Scene 1**: "ornate perfume bottle with gold bands"
- **Scene 2**: "sleek matte black bottle"
- **Scene 3**: "elegant purple gradient bottle"

**Why?** The LLM was being creative with each scene's `image_generation_prompt`, writing NEW descriptions instead of reusing the SAME description.

## The Root Cause

We had `subject_description` in `consistency_markers`, but:
- ❌ LLM wrote it
- ❌ LLM then IGNORED it when writing individual scenes
- ❌ LLM rewrote the subject for each scene instead of copying

## The Solution: COPY-PASTE TEMPLATE Approach

### New Workflow for the LLM:

**Step 1**: Write Master Subject Description
```json
{
  "consistency_markers": {
    "subject_description": "7-inch tall perfume bottle with deep purple gradient glass (darker at bottom, lighter at top), silver crown-shaped cap with subtle engravings, oval rose-gold label with 'Aurelia Mystique' in elegant script, clear liquid with subtle golden shimmer"
  }
}
```

**Step 2**: COPY (not rewrite) into Scene 1
```json
{
  "scene_number": 1,
  "image_generation_prompt": "7-inch tall perfume bottle with deep purple gradient glass (darker at bottom, lighter at top), silver crown-shaped cap with subtle engravings, oval rose-gold label with 'Aurelia Mystique' in elegant script, clear liquid with subtle golden shimmer. Positioned on luxurious velvet surface with dramatic spotlight."
}
```

**Step 3**: COPY (not rewrite) into Scene 2
```json
{
  "scene_number": 2,
  "image_generation_prompt": "7-inch tall perfume bottle with deep purple gradient glass (darker at bottom, lighter at top), silver crown-shaped cap with subtle engravings, oval rose-gold label with 'Aurelia Mystique' in elegant script, clear liquid with subtle golden shimmer. Held in a sophisticated woman's hand, clearly visible with purple gradient glass and silver crown cap, in dimly lit upscale bedroom."
}
```

**Step 3**: COPY (not rewrite) into Scene 3
```json
{
  "scene_number": 3,
  "image_generation_prompt": "7-inch tall perfume bottle with deep purple gradient glass (darker at bottom, lighter at top), silver crown-shaped cap with subtle engravings, oval rose-gold label with 'Aurelia Mystique' in elegant script, clear liquid with subtle golden shimmer. Visible on vanity table beside woman's face, purple gradient and silver details clearly shown."
}
```

## Implementation Changes

### 1. Updated `subject_description` Definition (Line 228)

**Before:**
```
"This is used to ensure the subject looks IDENTICAL"
```

**After:**
```
"You MUST copy this EXACT description into EVERY scene's image_generation_prompt where the subject appears"
"this MASTER DESCRIPTION must be COPIED VERBATIM into every scene where it appears"
```

### 2. Updated `image_generation_prompt` Example (Line 235)

**Before:**
```
"Your EXTREMELY detailed image generation prompt here..."
```

**After:**
```
"🚨 CRITICAL: If the subject appears in this scene, you MUST START by COPYING the EXACT subject_description from consistency_markers above, then add context.
Example: '[COPY EXACT subject_description HERE] + positioned on white marble surface with dramatic spotlight...'
DO NOT describe the subject differently - COPY IT EXACTLY from subject_description, then add only the scene-specific context."
```

### 3. Added CRITICAL WORKFLOW (Lines 262-267)

```
**🚨 CRITICAL WORKFLOW FOR SUBJECT CONSISTENCY:**
1. FIRST: Write the subject_description in consistency_markers with EXTREME detail
2. THEN: For EVERY scene where the subject appears, COPY that EXACT subject_description into the image_generation_prompt
3. Add scene-specific context AFTER the copied subject description (lighting, position, environment)
4. DO NOT rewrite or paraphrase the subject - COPY IT VERBATIM from subject_description
5. Think of subject_description as a TEMPLATE that gets copied into every scene
```

## Why This Should Work

### The Mental Model We're Giving the LLM:

**OLD (Creative):**
- "Describe the subject in each scene"
- LLM thinks: "I'll be creative and describe it differently each time!"
- Result: Different bottles

**NEW (Template):**
- "Write ONE master description, then COPY-PASTE it into every scene"
- LLM thinks: "This is like a template variable - copy the exact text!"
- Result: Same bottle

### Key Words That Enforce This:

- ✅ "COPY" (not "use" or "reference")
- ✅ "EXACT" (not "similar" or "consistent")
- ✅ "VERBATIM" (not "based on")
- ✅ "TEMPLATE" (mental model)
- ✅ "COPY-PASTE" (explicit action)

## Expected Behavior

### Master Description (Once):
```
"7-inch tall perfume bottle with deep purple gradient glass (darker at bottom, lighter at top), 
silver crown-shaped cap with subtle engravings, oval rose-gold label with 'Aurelia Mystique' 
in elegant script, clear liquid with subtle golden shimmer"
```

### Scene 1 (Copy + Context):
```
"[EXACT COPY OF MASTER DESCRIPTION] 
+ positioned on luxurious velvet surface with dramatic spotlight"
```

### Scene 2 (Copy + Context):
```
"[EXACT COPY OF MASTER DESCRIPTION] 
+ held in sophisticated woman's hand in dimly lit upscale bedroom"
```

### Scene 3 (Copy + Context):
```
"[EXACT COPY OF MASTER DESCRIPTION] 
+ visible on vanity table beside woman's face"
```

## Testing

After this fix, check the storyboard JSON output:

✅ **consistency_markers.subject_description**: Should have ONE detailed description
✅ **scenes[0].image_generation_prompt**: Should START with EXACT COPY of subject_description
✅ **scenes[1].image_generation_prompt**: Should START with EXACT COPY of subject_description
✅ **scenes[2].image_generation_prompt**: Should START with EXACT COPY of subject_description
✅ **All three scene prompts**: Subject description should be IDENTICAL, only context varies

## Why This is Different from Before

**Previous Attempts:**
- "The EXACT SAME bottle from Scene 1"
- "Maintain identical appearance"
- "Reference Scene 1"

**Problem:** LLM still paraphrased/rewrote

**New Approach:**
- "COPY the EXACT subject_description"
- "COPY IT VERBATIM"
- Think of it as a "TEMPLATE"

**Solution:** Forces literal copy-paste behavior instead of paraphrasing

## The Critical Insight

LLMs are trained to:
- ✅ Be creative
- ✅ Vary language
- ✅ Paraphrase
- ❌ Copy-paste verbatim

We need to **override** this training by:
- Using explicit "COPY" instructions
- Showing TEMPLATE mental model
- Using "VERBATIM" keyword
- Providing copy-paste example structure

This turns the LLM from a creative writer into a copy-paste operator for the subject description.

## Test Results (November 18, 2025)

**Test**: Perfume + Woman scenario

**Results:**
- ✅ **Bottle Identity**: WORKING - Same bottle maintained across scenes
- ❌ **Bottle Size**: NOT WORKING - Size variations between scenes
- ❌ **Woman Identity**: NOT WORKING - Different women in different scenes

**Conclusion:**
The Master Template Copy-Paste Approach **IS WORKING** ✅

The problem is NOT in the LLM's copying ability. The problem is in the QUALITY of descriptions being copied:

| Subject | Unique Identifiers | Result |
|---------|-------------------|--------|
| **Bottle** | 6 detailed features (shape, color, cap, ribbon, liquid, label) | ✅ Identity maintained |
| **Woman** | 2 vague features (age, clothing) | ❌ Identity lost |

**Solution Required:**
Require "police description" level detail for ALL subjects, especially human characters.

**Example - Bad vs Good:**

❌ **Bad (Too Generic):**
```
"sophisticated woman in her 30s wearing elegant ivory silk blouse"
```

✅ **Good (Police Description):**
```
"Woman, 32 years old, 5'6" tall, medium build (130 lbs). Long chestnut brown hair 
with subtle waves, naturally side-parted on left, reaching mid-back. Oval face with 
high cheekbones, emerald green eyes, warm beige skin tone (Fitzpatrick Type III). 
Small beauty mark near left eye, above cheekbone. Wearing elegant ivory silk blouse 
with pearl buttons. Warm, confident expression with subtle smile."
```

See `test-results-perfume-woman.md` for full analysis.

## Next Steps

1. ✅ Infrastructure is working (Master Template Copy-Paste)
2. 🔄 Need to improve LLM instructions to require "police description" detail for characters
3. 🔄 Need to add size reference objects for scale consistency
4. 🔄 Test with enhanced character descriptions
