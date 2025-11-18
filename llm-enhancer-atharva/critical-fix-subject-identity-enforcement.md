# Critical Fix: Subject Identity Enforcement

## The Problem Discovered

The user tested with a perfume bottle prompt and the storyboard showed **3 completely different bottles**:
- Scene 1: Bottle with ridged/textured body, gold bands, ornate cap
- Scene 2: Smooth matte black bottle, different proportions, different cap
- Scene 3: Yet another completely different bottle design

**Root Cause**: The LLM's text descriptions were overriding the visual reference images. Even though we pass Scene 1's image as a reference to generate Scene 2's image, the **text prompt** describing a different bottle design is more influential than the reference image for image generation models.

## The Solution

Added **ABSOLUTE RULE #1** at the very top of the system prompt with maximum emphasis:

### 1. Top of System Prompt (Line 41-53)

```
🚨 **ABSOLUTE RULE #1: SUBJECT MUST BE PHYSICALLY IDENTICAL** 🚨
If this video features a product (bottle, can, box, etc.) or character (person, animal, etc.):
- THE PHYSICAL OBJECT MUST BE IDENTICAL IN EVERY SCENE WHERE IT APPEARS
- This is NOT negotiable, NOT flexible, NOT creative freedom
- Scene 1: Describe the subject in EXTREME detail
- Scenes 2, 3, 4+: COPY THE EXACT SAME PHYSICAL DESCRIPTION from Scene 1
- Start with: "The EXACT SAME [subject] from Scene 1" followed by IDENTICAL physical description
- Example for perfume bottle: [detailed 3-scene example]
- What CAN change: camera angle, lighting, positioning, environment, effects
- What CANNOT change: size, shape, color, material, texture, labels, caps, proportions, design
```

### 2. Critical Reminder Before JSON Output (Line 212-217)

```
🚨 **CRITICAL REMINDER BEFORE YOU START:** 🚨
- If there's a product/subject, it MUST be IDENTICAL in every scene
- Scene 1: Describe it in detail
- Scenes 2+: Use "The EXACT SAME [subject] from Scene 1" and REPEAT SAME physical characteristics
- DO NOT change bottle shape, color, cap, label, size, or any physical feature
- Only change: camera angle, lighting, position, environment, effects
```

## Why This Should Work

### 1. Position
- At the VERY TOP (before duration rules, before anything else)
- Makes it the #1 priority
- LLM sees this first

### 2. Tone
- "ABSOLUTE RULE #1" - non-negotiable
- "NOT negotiable, NOT flexible, NOT creative freedom" - removes ambiguity
- 🚨 emoji - visual emphasis

### 3. Clarity
- "COPY THE EXACT SAME PHYSICAL DESCRIPTION" - explicit instruction
- Concrete 3-scene example showing exact pattern
- Lists what CAN and CANNOT change

### 4. Redundancy
- Stated at top
- Repeated before JSON structure
- Also in detailed prompt sections
- Also in key points
- Multiple reinforcements throughout

## Expected Behavior After Fix

### Scene 1 (image_generation_prompt):
```
"8-inch tall perfume bottle with frosted matte black glass body, gold metallic cap 
(1-inch diameter), minimalist gold rectangular label with 'Lumière Noir' embossed text, 
deep amber liquid visible inside. Centered on white marble surface, soft overhead lighting."
```

### Scene 2 (image_generation_prompt):
```
"The EXACT SAME 8-inch tall perfume bottle from Scene 1 (identical frosted matte black 
glass body, same gold metallic cap with 1-inch diameter, same minimalist gold rectangular 
label with 'Lumière Noir' embossed, same deep amber liquid inside). Now positioned at 
edge of surface with dramatic side lighting from left."
```

### Scene 3 (image_generation_prompt):
```
"The EXACT SAME 8-inch tall perfume bottle from Scene 1 (maintaining identical frosted 
matte black glass, same gold cap, same gold label with 'Lumière Noir', same amber liquid). 
Now with delicate vapor wisps emerging, backlit with soft blue-tinted light."
```

## The Critical Difference

**Before Fix:**
- LLM had creative freedom with subject descriptions
- Each scene described a "perfume bottle" differently
- Text descriptions were too creative
- Result: Different bottles in each scene

**After Fix:**
- LLM must COPY physical descriptions from Scene 1
- "The EXACT SAME bottle from Scene 1" enforced
- Physical attributes must be IDENTICAL
- Result: Same bottle with different contexts

## Test Results (November 18, 2025)

**Test Prompt**: Perfume + Woman scenario ("Serenity Rose" with woman using the perfume)

### Results:

| Aspect | Status | Details |
|--------|--------|---------|
| **Bottle Identity** | ✅ **PARTIAL SUCCESS** | Same bottle type maintained |
| **Bottle Size** | ❌ **FAILED** | Size variations between scenes |
| **Woman Identity** | ❌ **FAILED** | Different women in different scenes |

### Analysis:

**✅ What's Working:**
- **Master Template Copy-Paste Approach IS WORKING**
- LLM successfully copies subject descriptions across scenes
- Bottle identity maintained (shape, color, features all consistent)

**❌ What's NOT Working:**
- **Size Consistency**: "6.5 inches tall" not enforced without visual anchors
- **Character Consistency**: Generic description "woman in her 30s" too vague

### Root Cause:

**Bottle (Partial Success):**
- ✅ Had 6 unique identifiers (shape, color, cap, ribbon, liquid, label)
- ✅ Image model recognized and maintained these features
- ❌ But couldn't maintain size without reference objects

**Woman (Complete Failure):**
- ❌ Only 2 vague descriptors: "woman in her 30s" + "ivory silk blouse"
- ❌ No hair color, facial features, skin tone, or unique identifiers
- ❌ Image model generated ANY woman matching vague description

### Key Insight:

The infrastructure is working correctly. The problem is **description quality**:

- ✅ **Detailed Product Description** (6 unique features) → Identity maintained
- ❌ **Generic Character Description** (2 vague features) → Identity lost

### Solution:

Require "police description" level detail for ALL subjects (products AND characters):

**Bad (Generic):**
```
"sophisticated woman in her 30s wearing elegant ivory silk blouse"
```

**Good (Police Description):**
```
"Woman, 32 years old, 5'6" tall, medium build. Long chestnut brown hair with subtle 
waves, side-parted on left, reaching mid-back. Oval face, high cheekbones, emerald 
green eyes, warm beige skin. Small beauty mark near left eye. Ivory silk blouse with 
pearl buttons. Warm, confident expression."
```

See: `test-results-perfume-woman.md` for full analysis and action items.

## Why This Is So Important

The sequential image generation relies on TWO mechanisms:
1. **Visual Reference**: Passing Scene 1's image to generate Scene 2
2. **Text Prompt**: Describing what to generate

If the text prompt says "generate a different bottle design," it will override the visual reference. That's why we MUST force the LLM to use nearly identical text descriptions for the physical subject while varying only the context.

This fix makes the text prompts **complement** the visual references instead of **contradicting** them.


