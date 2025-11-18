# Sequential Image Generation Strategy

## Overview

All images (reference, start, and end) are generated **sequentially** to maintain visual cohesion across the entire video. This creates a visual chain where each image uses the previous one as a reference.

## Three Sequential Chains

### 1. Reference Image Chain
Reference images are generated **first** and form the foundation for the entire generation:

```
Ref Image 1 (no reference) 
    → Ref Image 2 (ref: Ref Img 1) 
    → Ref Image 3 (ref: Ref Img 2) 
    → Ref Image 4 (ref: Ref Img 3)
```

**Purpose**: Maintain visual consistency of the main subject, style, and environment across all scenes.

### 2. Start Image Chain
Start images are generated **second**, forming their own sequential chain:

```
Start Image 1 (ref: Ref Img 1) 
    → Start Image 2 (ref: Start Img 1) 
    → Start Image 3 (ref: Start Img 2) 
    → Start Image 4 (ref: Start Img 3)
```

**Purpose**: Create unique first frames for each video clip while maintaining visual cohesion.

**Key Points**:
- Start Image 1 begins with Scene 1's reference image as the base
- Each subsequent start image uses the **previous start image** as reference (NOT its own scene's reference)
- This creates a smooth visual progression across all start frames

### 3. End Image Chain
End images are generated **third**, forming their own sequential chain:

```
End Image 1 (ref: Ref Img 1) 
    → End Image 2 (ref: End Img 1) 
    → End Image 3 (ref: End Img 2) 
    → End Image 4 (ref: End Img 3)
```

**Purpose**: Create unique last frames for each video clip while maintaining visual cohesion.

**Key Points**:
- End Image 1 begins with Scene 1's reference image as the base
- Each subsequent end image uses the **previous end image** as reference (NOT its own scene's reference)
- This creates a smooth visual progression across all end frames

## Why This Matters

### ❌ **WRONG: One-at-a-time generation (old approach)**
```python
for scene in scenes:
    # Each scene generates in isolation
    start_image = generate([start_prompt], ref=scene.reference)  # ❌ No chain
    end_image = generate([end_prompt], ref=scene.reference)      # ❌ No chain
```

**Result**: Each scene's start/end images are isolated islands. No visual flow between scenes.

### ✅ **CORRECT: Sequential batch generation (current approach)**
```python
# Generate ALL start images as one sequential batch
all_start_images = generate(
    prompts=[start_prompt_1, start_prompt_2, start_prompt_3, start_prompt_4],
    initial_reference=reference_image_1
)
# Result: Start 1 → Start 2 → Start 3 → Start 4 (visual chain)

# Generate ALL end images as one sequential batch
all_end_images = generate(
    prompts=[end_prompt_1, end_prompt_2, end_prompt_3, end_prompt_4],
    initial_reference=reference_image_1
)
# Result: End 1 → End 2 → End 3 → End 4 (visual chain)
```

**Result**: Smooth visual flow across all scenes, maintaining cohesion while showing unique moments.

## Visual Consistency Mechanisms

Each image in the chain maintains consistency through:

1. **Sequential Visual Reference**: Using the previous image as a visual guide
2. **Consistency Markers**: Text-based markers (style, color palette, lighting, composition, mood) appended to all prompts
3. **Explicit Cohesion Instructions**: Prompts enhanced with "Maintain exact visual consistency with the reference image..."
4. **Subject Description**: Detailed description of the main subject to ensure it remains identical across scenes

## Implementation Details

### Code Structure
```python
# In generations.py (lines ~350-442)

# STEP 1: Generate reference images sequentially
reference_image_paths = await generate_images_with_sequential_references(
    prompts=scene_image_generation_prompts,
    initial_reference_image=user_provided_image,  # Optional
    ...
)

# STEP 2: Generate start images sequentially
start_image_paths = await generate_images_with_sequential_references(
    prompts=enhanced_start_prompts,  # All 4 prompts at once
    initial_reference_image=reference_image_paths[0],  # Start with Scene 1's ref
    ...
)

# STEP 3: Generate end images sequentially
end_image_paths = await generate_images_with_sequential_references(
    prompts=enhanced_end_prompts,  # All 4 prompts at once
    initial_reference_image=reference_image_paths[0],  # Start with Scene 1's ref
    ...
)
```

### Key Parameters
- `prompts`: List of ALL prompts for the chain (e.g., all 4 start prompts)
- `initial_reference_image`: The base image to start the chain (Scene 1's reference)
- `scene_offset`: Set to 0 for batch generation (filenames numbered correctly)

## Benefits

1. **Visual Cohesion**: All images flow naturally from one to another
2. **Unique Moments**: Each scene still has unique start/end frames
3. **Subject Identity**: The main subject remains identical when it appears
4. **Smooth Transitions**: Videos transition smoothly between scenes
5. **Professional Quality**: Looks like a single, well-planned production

## Example Flow

For a perfume ad with 4 scenes:

**Reference Chain**:
- Ref 1: Perfume bottle centered, white background
- Ref 2: Same bottle, slight rotation (using Ref 1 as reference)
- Ref 3: Same bottle, different angle (using Ref 2 as reference)
- Ref 4: Same bottle, close-up (using Ref 3 as reference)

**Start Chain**:
- Start 1: Bottle emerging from shadows (using Ref 1 as base)
- Start 2: Bottle with first light ray (using Start 1 as reference)
- Start 3: Bottle with more dramatic lighting (using Start 2 as reference)
- Start 4: Bottle with full illumination beginning (using Start 3 as reference)

**End Chain**:
- End 1: Bottle with vapor starting to dissipate (using Ref 1 as base)
- End 2: Bottle with vapor forming patterns (using End 1 as reference)
- End 3: Bottle with vapor reaching peak (using End 2 as reference)
- End 4: Bottle with final dramatic vapor moment (using End 3 as reference)

**Result**: 12 images (4 ref + 4 start + 4 end) that all maintain visual cohesion while showing progression and unique moments.

