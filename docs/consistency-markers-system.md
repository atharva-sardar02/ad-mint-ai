# Consistency Markers System

## Overview

The consistency markers system ensures that all images and videos generated for a single ad campaign share the same visual style, color palette, lighting, composition, and mood - creating a cohesive "universe" across all scenes.

## How It Works

### 1. **Marker Generation (Once Per Generation)**

At the start of each video generation, the system:

1. **Generates consistency markers** using OpenAI's `gpt-4o` model via `generate_scene_prompts_with_markers()`
2. **Extracts shared markers** that will be used across ALL scenes
3. **Stores markers** in the `Generation.coherence_settings` JSON field for persistence

```python
# Markers are generated once and shared across all scenes
consistency_markers = {
    "style": "cinematic modern minimalist",
    "color_palette": "warm earth tones with cool accents",
    "lighting": "soft natural window light",
    "composition": "rule of thirds with dynamic angles",
    "mood": "energetic optimistic professional"
}
```

### 2. **Dual Consistency Approach**

We use **TWO methods** to ensure maximum visual consistency:

#### A. **Text-Based Markers** (Applied to All)
- **All Image Generations** (Nano Banana)
  - Markers are appended to image prompts
  - Ensures all reference images share the same visual style

- **All Video Generations** (Sora-2, Veo-3, PixVerse, etc.)
  - Markers are appended to video prompts
  - Ensures all video clips share the same visual universe

#### B. **Visual Reference Images** (Sequential for Images)
- **Image Generation**: Sequential reference chain
  - Image 1: Generated with markers only
  - Image 2: Generated with markers + Image 1 as reference
  - Image 3: Generated with markers + Image 2 as reference
  - And so on...
  
  This creates a **visual chain** where each image builds on the previous one, ensuring:
  - Character consistency (same person/product across images)
  - Style consistency (visual style carries forward)
  - Color consistency (palette remains consistent)

**Why Both?**
- **Markers** provide high-level style guidance (text-based)
- **Reference Images** provide visual consistency (pixel-level)
- Together, they create maximum cohesion

### 3. **Prompt Enhancement**

Both image and video generation use the same enhancement function:

```python
def _enhance_prompt_with_markers(base_prompt, consistency_markers):
    # Example:
    # Base: "A person checking their watch in a modern office"
    # Enhanced: "A person checking their watch in a modern office. Style: cinematic modern minimalist, Color palette: warm earth tones with cool accents, Lighting: soft natural window light, Composition: rule of thirds with dynamic angles, Mood: energetic optimistic professional"
```

**Storage**: Enhanced prompts for images are stored in the storyboard plan:
- `reference_image_prompt`: Enhanced prompt for reference images
- `start_image_enhanced_prompt`: Enhanced prompt for start frame images
- `end_image_enhanced_prompt`: Enhanced prompt for end frame images

These enhanced prompts are displayed in the storyboard visualizer UI, showing users exactly what text was sent to the image generation model.

## Implementation Details

### Marker Storage

Markers are stored in the database:
- **Location**: `Generation.coherence_settings["consistency_markers"]`
- **Format**: JSON dictionary with 5 keys (style, color_palette, lighting, composition, mood)
- **Persistence**: Markers persist across generation retries and can be reused

### Marker Retrieval

If markers already exist (from a previous run), they are retrieved instead of regenerated:

```python
if generation.coherence_settings and "consistency_markers" in generation.coherence_settings:
    consistency_markers = generation.coherence_settings["consistency_markers"]
else:
    # Generate new markers
    consistency_markers = await generate_scene_prompts_with_markers(...)
```

### Marker Application Flow

```
User Prompt
    ↓
Generate Consistency Markers (ONCE)
    ↓
Store in Database
    ↓
    ├─→ Image Generation (Nano Banana) - SEQUENTIAL
    │   ├─→ Image 1: Markers only
    │   ├─→ Image 2: Markers + Image 1 as reference
    │   ├─→ Image 3: Markers + Image 2 as reference
    │   └─→ Image N: Markers + Image N-1 as reference
    │
    └─→ Video Generation (Sora-2, Veo-3, etc.)
        └─→ Apply Markers to Video Prompts
            (Videos can also use reference images if provided)
```

## Benefits

1. **Visual Cohesion**: All images and videos share the same style, colors, lighting, and mood
2. **Universe Consistency**: Scenes feel like they exist in the same world
3. **Brand Consistency**: Maintains visual identity across all generated content
4. **Single Source of Truth**: Markers generated once, applied everywhere

## Example

**User Prompt**: "Create an ad for a fitness app"

**Generated Markers**:
```json
{
  "style": "dynamic modern minimalist",
  "color_palette": "vibrant primary colors with energetic gradients",
  "lighting": "bright natural daylight with soft shadows",
  "composition": "dynamic angles with rule of thirds",
  "mood": "energetic motivated optimistic"
}
```

**Scene 1 Image Prompt** (Enhanced):
"A person jogging in a park. Style: dynamic modern minimalist, Color palette: vibrant primary colors with energetic gradients, Lighting: bright natural daylight with soft shadows, Composition: dynamic angles with rule of thirds, Mood: energetic motivated optimistic"

**Scene 1 Video Prompt** (Enhanced):
"A person checking their fitness progress on their phone while jogging. Style: dynamic modern minimalist, Color palette: vibrant primary colors with energetic gradients, Lighting: bright natural daylight with soft shadows, Composition: dynamic angles with rule of thirds, Mood: energetic motivated optimistic"

Both image and video will share the same visual universe!

**Note**: Enhanced prompts are stored in the storyboard plan after image generation and are displayed in the storyboard visualizer UI, showing users exactly what prompt was sent to the image generation model.

## Technical Files

- **Marker Generation**: `backend/app/services/pipeline/prompt_generator.py`
- **Image Enhancement**: `backend/app/services/pipeline/image_generation.py` → `_build_prompt_with_markers()`
- **Video Enhancement**: `backend/app/services/pipeline/video_generation.py` → `_enhance_prompt_with_markers()`
- **Pipeline Integration**: `backend/app/api/routes/generations.py` → `process_generation()`

