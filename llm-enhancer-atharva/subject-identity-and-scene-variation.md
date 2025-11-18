# Subject Identity & Scene Variation - The Critical Balance

## The Problem

When generating **ALL images** (reference, start, and end) for multiple scenes, we need to achieve **TWO CRITICAL REQUIREMENTS** simultaneously:

1. **IDENTICAL SUBJECT**: The main subject (product/person) must remain exactly the same across all scenes in ALL image types (reference, start, end)
2. **DIFFERENT MOMENTS/CONTEXTS**: Each scene must show unique actions/poses/positions/angles/lighting

## Image Types That Need Identical Subjects

### 1. Reference Images (Main Images for Each Scene)
- ✅ **IDENTICAL subject** across all scene reference images
- ✅ **UNIQUE context** (camera angle, lighting, positioning, environment)

### 2. Start Images (First Frame of Each Scene)
- ✅ **IDENTICAL subject** across all scene start images
- ✅ **UNIQUE action/pose** (different starting positions)

### 3. End Images (Last Frame of Each Scene)
- ✅ **IDENTICAL subject** across all scene end images
- ✅ **UNIQUE action/pose** (different ending positions)

## Why This Matters

### ❌ **Problem 1: Changing Subject**
```
Scene 1: Blue bottle, 6 inches, round cap
Scene 2: Green bottle, 8 inches, square cap  ❌ DIFFERENT SUBJECT!
Scene 3: Purple bottle, 5 inches, no cap     ❌ DIFFERENT SUBJECT!
```

**Result**: Looks like 3 different products. No cohesion. Viewers get confused.

### ❌ **Problem 2: Identical Moments**
```
Scene 1: Bottle centered, upright, soft lighting
Scene 2: Bottle centered, upright, soft lighting  ❌ SAME AS SCENE 1!
Scene 3: Bottle centered, upright, soft lighting  ❌ SAME AS SCENE 1!
```

**Result**: All scenes look the same. No progression. Boring video.

### ✅ **Correct: Identical Subject + Unique Moments**

**Reference Images:**
```
Scene 1 ref: Blue bottle (6 inches, round cap) - centered, upright, soft lighting
Scene 2 ref: SAME blue bottle (6 inches, round cap) - edge of surface, dramatic side lighting
Scene 3 ref: SAME blue bottle (6 inches, round cap) - with vapor, backlit
```

**Start Images:**
```
Scene 1 start: SAME blue bottle - centered position, no vapor
Scene 2 start: SAME blue bottle - tilted 30°, beginning to emit vapor
Scene 3 start: SAME blue bottle - rotating, vapor swirling
```

**End Images:**
```
Scene 1 end: SAME blue bottle - subtle vapor wisps starting
Scene 2 end: SAME blue bottle - vapor forming spiral patterns
Scene 3 end: SAME blue bottle - vapor cloud at peak expansion
```

**Result**: Cohesive visual identity across ALL image types + dynamic progression. Professional quality.

## The Solution: Enhanced LLM Instructions

### 1. Reference Image Requirements (image_generation_prompt)

**CRITICAL: Identical Subject Across All Reference Images**
```
CRITICAL REQUIREMENTS:
- IDENTICAL SUBJECT ACROSS ALL SCENES: When the subject appears in ANY scene, it must be the EXACT SAME subject
  - Scene 1: Establish characteristics in extreme detail
  - Scenes 2+: "The EXACT SAME [subject] from Scene 1" + reference identical characteristics
  - NEVER change the subject's design, color, size, shape, material, branding

- UNIQUE SCENE CONTEXT: While subject remains identical, each scene can have unique:
  - Camera angles (overhead, side view, close-up, wide shot)
  - Environmental context (different backgrounds, surfaces, settings)
  - Lighting approach (soft, dramatic, backlit, side-lit)
  - Subject positioning (centered, off-center, tilted, elevated)
  - Additional elements (vapor, light effects, supporting objects)
```

**Example:**
```
Scene 1: "An 8-inch tall perfume bottle with frosted matte glass body, silver metallic cap..."
Scene 2: "The EXACT SAME 8-inch frosted glass perfume bottle from Scene 1 (maintaining identical 
          silver metallic cap, same rose gold label...) now positioned at edge with dramatic 
          side lighting..."
Scene 3: "The EXACT SAME perfume bottle from Scene 1 (identical 8-inch height, same frosted glass 
          texture, same silver cap...) now captured with vapor wisps emerging..."
```

### 2. Start/End Frame Requirements

**For Start Images:**
```
CRITICAL REQUIREMENTS:
- DIFFERENT ACTION/MOMENT: Each scene's start frame must show a DIFFERENT action, pose, position, or moment
  - Scene 1 start: Subject at position A, doing action A
  - Scene 2 start: Subject at position B, doing action B
  - Scene 3 start: Subject at position C, doing action C

- IDENTICAL SUBJECT: When the subject IS present, it must be the EXACT SAME subject
  - For Scene 1: Establish characteristics (e.g., "frosted glass bottle, 8 inches, silver cap")
  - For Scenes 2+: Start with "The EXACT SAME [subject] from Scene 1"
  - NEVER change the subject's design, color, size, shape, material
```

### 2. Concrete Examples in Instructions

**Perfume Ad Example:**
```
Scene 1 start: "The frosted glass perfume bottle (8 inches, silver cap, rose gold liquid) 
                stands centered on a white marble surface, perfectly upright, 
                soft overhead lighting creating subtle shadows"

Scene 2 start: "The EXACT SAME frosted glass perfume bottle from Scene 1 
                (identical 8-inch height, same silver cap, same rose gold liquid) 
                now positioned at the edge of the marble surface, 
                camera angle from below looking up, dramatic side lighting"

Scene 3 start: "The EXACT SAME perfume bottle from Scene 1 
                (maintaining all identical physical characteristics) 
                now tilted at 45 degrees, vapor beginning to emerge from the cap, 
                backlit with blue-tinted light"
```

### 3. Clear JSON Structure

**In System Prompt:**
```json
{
  "start_image_prompt": "UNIQUE MOMENT for Scene 1: Describe the first frame showing a SPECIFIC action/pose/position (e.g., 'bottle centered, upright'). If subject present, describe its EXACT characteristics (size, color, material, etc.) in detail.",
  "end_image_prompt": "UNIQUE MOMENT for Scene 1: Describe the last frame showing a DIFFERENT SPECIFIC action/pose/position than the start (e.g., 'bottle with vapor beginning to rise'). If subject present, use SAME characteristics as start."
}
```

### 4. Explicit Key Points

**Added to system prompt:**
```
CRITICAL FOR START/END FRAMES:
- Each scene's start_image_prompt must describe a UNIQUE action/pose/position
  (Scene 1: centered upright, Scene 2: tilted with side lighting, Scene 3: rotating with vapor)
  
- Each scene's end_image_prompt must describe a UNIQUE action/pose/position
  (Scene 1: subtle vapor, Scene 2: swirling vapor, Scene 3: expanding vapor cloud)
  
- When the subject IS present, it must be the EXACT SAME subject with IDENTICAL physical characteristics
  (Scene 1: "8-inch frosted bottle, silver cap"; Scenes 2+: "The EXACT SAME 8-inch frosted bottle from Scene 1")
  
- DO NOT make start/end frames identical across scenes - vary the action, angle, lighting, 
  or progression while keeping the subject itself identical
```

## Implementation Details

### File: `storyboard_planner.py`

**Updated Sections:**
1. **Lines ~123-148**: Detailed `start_image_prompt` instructions with examples
2. **Lines ~149-174**: Detailed `end_image_prompt` instructions with examples
3. **Lines ~201-202**: JSON structure examples with inline guidance
4. **Lines ~232-236**: Critical key points section with explicit instructions

### Key Changes:
- ✅ Added **"DIFFERENT ACTION/MOMENT"** requirement with scene-by-scene examples
- ✅ Added **"IDENTICAL SUBJECT"** requirement with Scene 1 vs. Scenes 2+ distinction
- ✅ Provided **concrete perfume ad examples** showing exact phrasing
- ✅ Emphasized **"The EXACT SAME [subject] from Scene 1"** pattern for Scenes 2+
- ✅ Added explicit instruction to **NOT make frames identical** across scenes

## Expected LLM Behavior

### For Scene 1 (Establishing Subject)
```json
{
  "start_image_prompt": "A frosted glass perfume bottle, 8 inches tall with a silver metallic cap and rose gold liquid inside, stands perfectly centered on a white marble surface. The bottle is completely upright with soft overhead lighting creating delicate shadows. Clean minimalist composition with the bottle as the hero element.",
  "end_image_prompt": "The same frosted glass perfume bottle (8 inches, silver cap, rose gold liquid) with the first wisps of delicate vapor beginning to rise from the opened cap, creating an ethereal effect. The lighting remains soft and overhead, the marble surface pristine, the bottle still centered but now with vapor adding visual interest."
}
```

### For Scene 2+ (Maintaining Subject, Varying Moment)
```json
{
  "start_image_prompt": "The EXACT SAME frosted glass perfume bottle from Scene 1 (identical 8-inch height, same silver metallic cap, same rose gold liquid) now positioned at the edge of the marble surface, tilted at approximately 30 degrees. Camera angle shifts to a low perspective, looking up at the bottle, with dramatic side lighting from the left creating strong contrast and highlighting the frosted glass texture.",
  "end_image_prompt": "The EXACT SAME frosted glass perfume bottle from Scene 1 (maintaining all identical physical characteristics - 8 inches, silver cap, rose gold liquid) now with vapor forming intricate spiral patterns that swirl around the bottle in elegant curves. The side lighting from the left illuminates the vapor, making it glow softly against the darker background."
}
```

## Visual Consistency Mechanisms

The system maintains subject identity through:

1. **Explicit Subject Description** (Scene 1):
   - Detailed physical characteristics
   - Measurable attributes (height, color, material)
   - Reference-quality description

2. **Subject Reference Pattern** (Scenes 2+):
   - "The EXACT SAME [subject] from Scene 1"
   - Reiteration of key characteristics
   - Emphasis on "identical" and "maintaining all characteristics"

3. **Sequential Image Generation**:
   - All start images generated as one chain
   - Each start image uses previous start image as visual reference
   - Same for end images
   - Visual continuity reinforced by actual image references

4. **Consistency Markers**:
   - Text-based style markers appended to all prompts
   - Includes: style, color_palette, lighting, composition, mood, subject_description

## Testing & Validation

### Check for Subject Identity Across ALL Image Types:

**Reference Images:**
```
✅ Is the bottle/product the same shape across all scene reference images?
✅ Is it the same color across all scene reference images?
✅ Does it have the same key features (cap, label, size) across all scene reference images?
✅ Are the physical dimensions identical across all scene reference images?
```

**Start Images:**
```
✅ Is the bottle the same shape in all start images?
✅ Is the bottle the same color in all start images?
✅ Is the bottle the same size in all start images?
✅ Does the cap look identical in all start images?
```

**End Images:**
```
✅ Is the bottle the same shape in all end images?
✅ Is the bottle the same color in all end images?
✅ Is the bottle the same size in all end images?
✅ Does the cap look identical in all end images?
```

### Check for Scene Variation:

**Reference Images:**
```
✅ Is Scene 1 ref different from Scene 2 ref? (camera angle/lighting/positioning)
✅ Is Scene 2 ref different from Scene 3 ref? (context/environment/effects)
✅ Does each scene show unique visual context?
```

**Start Images:**
```
✅ Is Scene 1 start different from Scene 2 start? (pose/angle/action)
✅ Is Scene 2 start different from Scene 3 start? (pose/angle/action)
✅ Does each start frame show clear progression or variation?
✅ Are the starting moments unique enough to be visually interesting?
```

**End Images:**
```
✅ Is Scene 1 end different from Scene 2 end? (pose/angle/action/progression)
✅ Is Scene 2 end different from Scene 3 end? (pose/angle/action/progression)
✅ Does each end frame show clear progression?
✅ Are the ending moments unique enough to be visually interesting?
```

## Benefits

1. **Brand Consistency**: Product/character remains recognizable across all scenes
2. **Visual Interest**: Dynamic variety keeps viewers engaged
3. **Professional Quality**: Looks intentional and well-planned
4. **Narrative Flow**: Clear progression from scene to scene
5. **Cohesive Identity**: All clips feel like part of the same production

## Common Pitfalls to Avoid

❌ **Vague descriptions**: "A bottle" → ✅ "An 8-inch frosted glass bottle with silver cap"
❌ **No scene reference**: "The bottle tilted" → ✅ "The EXACT SAME bottle from Scene 1, now tilted"
❌ **Identical moments**: All scenes "bottle centered" → ✅ Each scene unique action/angle
❌ **Changing attributes**: Scene 1 "silver cap", Scene 2 "gold cap" → ✅ All scenes "silver cap"
❌ **Insufficient detail**: Scene 2+ don't reference Scene 1 → ✅ Explicit "from Scene 1" pattern

