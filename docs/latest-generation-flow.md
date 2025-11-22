# Latest Video Generation Flow

## Complete Workflow

### Overview

This document describes the current video generation flow with Kling 2.5 Turbo Pro as the default model, emphasizing unique start/end frames for each scene while maintaining visual consistency.

## Step-by-Step Flow

### STEP 1: Storyboard Planning (LLM GPT-4o)

**Input:**
- User prompt (e.g., "Create an ad for Nike shoes")
- Optional reference image (user-provided)
- Number of scenes (default: 3)

**Process:**
- LLM analyzes the prompt and reference image (if provided)
- Generates detailed storyboard with:
  - **Consistency Markers**: style, color_palette, lighting, composition, mood (shared across all scenes)
  - **For each scene**:
    - `detailed_prompt`: Main video generation prompt (40-80 words)
    - `image_generation_prompt`: Detailed image generation prompt (80-150 words) - for reference images
    - `start_image_prompt`: **UNIQUE** first frame description (different moment/pose for each scene)
    - `end_image_prompt`: **UNIQUE** last frame description (different moment/pose for each scene)
    - `image_continuity_notes`: How this scene relates to previous scenes
    - `visual_consistency_guidelines`: Per-scene consistency instructions
    - `scene_transition_notes`: How scene transitions from previous

**Output:**
- Storyboard plan with all prompts and markers
- **CRITICAL**: Each scene's `start_image_prompt` and `end_image_prompt` are DIFFERENT (unique moments)

---

### STEP 2: Image Generation (Nano Banana - Sequential)

**Reference Images (for style consistency):**
1. **Scene 1 Reference Image**:
   - Prompt: `image_generation_prompt` + consistency markers
   - Reference: User's initial image (if provided) OR none
   - Output: `scene_1_ref.png`

2. **Scene 2 Reference Image**:
   - Prompt: `image_generation_prompt` + consistency markers + continuity notes
   - Reference: `scene_1_ref.png` (sequential chain)
   - Output: `scene_2_ref.png`

3. **Scene 3 Reference Image**:
   - Prompt: `image_generation_prompt` + consistency markers + continuity notes
   - Reference: `scene_2_ref.png` (sequential chain)
   - Output: `scene_3_ref.png`

**Start Images (for first frame control - UNIQUE moments but VISUALLY COHESIVE):**
1. **Scene 1 Start Image**:
   - Prompt: `start_image_prompt` + consistency markers + **explicit visual consistency instructions**
   - Reference: `scene_1_ref.png` (ensures same subject/style/colors/lighting)
   - Output: `scene_1_start.png` (UNIQUE moment/pose, but visually cohesive with reference)

2. **Scene 2 Start Image**:
   - Prompt: `start_image_prompt` + consistency markers + **explicit visual consistency instructions**
   - Reference: `scene_2_ref.png` (ensures same subject/style/colors/lighting)
   - Output: `scene_2_start.png` (DIFFERENT moment/pose from Scene 1, but visually cohesive)

3. **Scene 3 Start Image**:
   - Prompt: `start_image_prompt` + consistency markers + **explicit visual consistency instructions**
   - Reference: `scene_3_ref.png` (ensures same subject/style/colors/lighting)
   - Output: `scene_3_start.png` (DIFFERENT moment/pose from Scenes 1 & 2, but visually cohesive)

**End Images (for last frame control - UNIQUE moments but VISUALLY COHESIVE):**
1. **Scene 1 End Image**:
   - Prompt: `end_image_prompt` + consistency markers + **explicit visual consistency instructions**
   - Reference: `scene_1_ref.png` (ensures same subject/style/colors/lighting)
   - Output: `scene_1_end.png` (UNIQUE moment/pose, but visually cohesive with reference)

2. **Scene 2 End Image**:
   - Prompt: `end_image_prompt` + consistency markers + **explicit visual consistency instructions**
   - Reference: `scene_2_ref.png` (ensures same subject/style/colors/lighting)
   - Output: `scene_2_end.png` (DIFFERENT moment/pose from Scene 1, but visually cohesive)

3. **Scene 3 End Image**:
   - Prompt: `end_image_prompt` + consistency markers + **explicit visual consistency instructions**
   - Reference: `scene_3_ref.png` (ensures same subject/style/colors/lighting)
   - Output: `scene_3_end.png` (DIFFERENT moment/pose from Scenes 1 & 2, but visually cohesive)

**Key Points:**
- Reference images are generated sequentially (chain: Img1 → Img2 → Img3)
- Start/end images are generated individually, each using its scene's reference image as base
- Each scene has **UNIQUE** start and end frames (different moments/poses) BUT maintains **VISUAL COHESION**
- Visual cohesion is ensured via:
  - Using scene's reference image as base reference
  - Strong consistency markers (style, colors, lighting, composition, mood)
  - Explicit visual consistency instructions in prompts
  - Critical consistency instruction: "same subject appearance, same colors, same lighting, same style, same visual universe"
- Result: Different moments/poses, but looks like frames from the same movie/shot

---

### STEP 3: Video Generation (Kling 2.5 Turbo Pro - Parallel)

**For each scene, Kling 2.5 Turbo Pro receives:**

1. **Scene 1 Video**:
   - Prompt: `detailed_prompt` + consistency markers
   - **Start Image**: `scene_1_start.png` (controls first frame - UNIQUE)
   - **End Image**: `scene_1_end.png` (controls last frame - UNIQUE)
   - **Reference Image**: `scene_1_ref.png` (for style/character consistency only)
   - Output: `scene_1.mp4`

2. **Scene 2 Video**:
   - Prompt: `detailed_prompt` + consistency markers
   - **Start Image**: `scene_2_start.png` (controls first frame - DIFFERENT from Scene 1)
   - **End Image**: `scene_2_end.png` (controls last frame - DIFFERENT from Scene 1)
   - **Reference Image**: `scene_2_ref.png` (for style/character consistency only)
   - Output: `scene_2.mp4`

3. **Scene 3 Video**:
   - Prompt: `detailed_prompt` + consistency markers
   - **Start Image**: `scene_3_start.png` (controls first frame - DIFFERENT from Scenes 1 & 2)
   - **End Image**: `scene_3_end.png` (controls last frame - DIFFERENT from Scenes 1 & 2)
   - **Reference Image**: `scene_3_ref.png` (for style/character consistency only)
   - Output: `scene_3.mp4`

**Image Priority in Kling 2.5 Turbo Pro:**
1. **PRIMARY**: `start_image` - Controls the first frame (each scene has unique start)
2. **PRIMARY**: `end_image` - Controls the last frame (each scene has unique end)
3. **SECONDARY**: `image` (reference) - For style/character consistency (doesn't override frames)

**Key Points:**
- All videos generate in **parallel** (simultaneously)
- Each scene has **DIFFERENT** start and end frames (unique moments)
- All scenes share the same subject/style (via reference images and consistency markers)
- Reference image is for style consistency, NOT frame control

---

### STEP 4: Video Assembly

1. **Stitch Clips**: Combine all scene videos with transitions
2. **Add Text Overlays**: Optional text overlays per scene (with fallback)
3. **Add Audio Layer**: Background music and sound effects (with fallback)
4. **Add Brand Overlay**: Brand name at the end (with fallback)
5. **Final Video**: Complete cohesive video

---

## Visual Consistency Strategy

### What's Shared Across Scenes:
- ✅ **Subject/Character**: Same person/product (via reference images and consistency markers)
- ✅ **Style**: Same visual style (via consistency markers)
- ✅ **Color Palette**: Same colors (via consistency markers)
- ✅ **Lighting**: Same lighting approach (via consistency markers)
- ✅ **Composition**: Same composition style (via consistency markers)
- ✅ **Mood**: Same emotional tone (via consistency markers)

### What's Unique Per Scene (but Visually Cohesive):
- ✅ **Start Frame**: Each scene starts at a DIFFERENT moment/pose (but same subject/style/colors/lighting)
- ✅ **End Frame**: Each scene ends at a DIFFERENT moment/pose (but same subject/style/colors/lighting)
- ✅ **Action**: Each scene shows different action/narrative moment (but maintains visual consistency)
- ✅ **Camera Angle**: Each scene can have different framing (but same visual style)

**Visual Cohesion Strategy:**
- Each start/end image uses its scene's reference image as base reference
- Explicit instructions: "Maintain exact visual consistency with reference image - same subject appearance, same colors, same lighting, same style"
- Strong consistency markers applied to all images
- Result: Unique moments that look like they're from the same visual universe

---

## Example Flow

**User Prompt**: "Create an ad for Nike running shoes"

**Scene 1**:
- Start Image: Person standing still, putting on shoes
- End Image: Person starting to jog
- Reference Image: Person with Nike shoes (style reference)

**Scene 2**:
- Start Image: Person jogging at moderate pace (DIFFERENT from Scene 1 end)
- End Image: Person checking phone while jogging (DIFFERENT moment)
- Reference Image: Same person with Nike shoes (style reference)

**Scene 3**:
- Start Image: Person at gym, about to use equipment (DIFFERENT moment)
- End Image: Person celebrating achievement (DIFFERENT moment)
- Reference Image: Same person with Nike shoes (style reference)

**Result**: 3 videos that:
- Share the same subject (person) and style (Nike shoes, visual aesthetic)
- Each start at a DIFFERENT moment (not the same frame)
- Each end at a DIFFERENT moment (not the same frame)
- Flow together as a cohesive narrative

---

## Current Defaults

- **Default Model**: Kling 2.5 Turbo Pro
- **Default Number of Scenes**: 3
- **Default Brand Name**: User-provided (or extracted from prompt)

