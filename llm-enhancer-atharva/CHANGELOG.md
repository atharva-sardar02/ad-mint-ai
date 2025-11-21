# Changelog - LLM Enhancer Workflow

## Latest Updates (2025-11-19)

### Google Veo 3.1 Integration
- **Changed**: Default video generation model updated to `google/veo-3.1`
- **Features**:
  - Reference-to-Video (R2V) mode with support for 1-3 reference images
  - Start/end frame control via `image` and `last_frame` parameters
  - Resolution control (720p or 1080p, default: 1080p)
  - Native audio generation (default: enabled)
  - Negative prompt support
  - Seed parameter for reproducibility
- **R2V Mode**:
  - When `reference_images` array provided (1-3 images), uses R2V mode
  - Requires 16:9 aspect ratio and 8-second duration
  - `last_frame` parameter is ignored in R2V mode
- **Start/End Frame Mode**:
  - When no `reference_images`, supports `image` (start) and `last_frame` (end)
  - Creates smooth interpolation between start and end frames
  - Supports 9:16 or 16:9 aspect ratio
  - Supports 4, 6, or 8-second duration
- **Implementation**: Updated in `backend/app/services/pipeline/video_generation.py`
- **Frontend**: Updated model definitions in `frontend/src/lib/models/videoModels.ts`

### User Reference Image Direct Usage
- **Changed**: User-provided reference images are now used **directly** as the first scene's reference image
- **Behavior**:
  - User's image is copied to first scene reference location (not regenerated)
  - All subsequent reference images are generated using sequential chaining starting from user's image
  - Ensures maximum consistency with user's provided image throughout all scenes
- **Implementation**: Updated in `backend/app/api/routes/generations.py` (lines ~320-450)
- **Benefits**:
  - User's exact image appears in storyboard (not a generated version)
  - All generated images maintain consistency with user's original
  - Better control over subject/product appearance

### Enhanced Image Generation Always Enabled
- **Changed**: Enhanced image generation is now **always enabled by default** (Story 9.4)
- **Removed**: `use_advanced_image_generation` toggle parameter
- **Default Settings**:
  - Quality threshold: 30.0
  - Number of variations: 4 per scene
  - Enhancement iterations: 4
- **Benefits**: All generations now use prompt enhancement and quality scoring for consistent high-quality results
- **Implementation**: Updated in `backend/app/api/routes/generations.py`

### Storyboard Image Display Improvements
- **Fixed**: Images no longer cropped from top/bottom
- **Changed**: Images now use `object-contain` instead of `object-cover` to show complete image
- **Added**: Click-to-view popup modal for full-size image viewing
- **Features**:
  - Images display with proper aspect ratio (no cropping)
  - Click any image to view in full-size modal
  - Modal supports closing via X button or clicking outside
  - Hover effects indicate images are clickable
- **Implementation**: Updated `frontend/src/components/storyboard/StoryboardVisualizer.tsx`

### LLM-Selected Transitions
- **Added**: Scene transitions are now selected by LLM and passed to video stitching
- **Features**:
  - LLM selects appropriate transition type for each scene boundary
  - Transitions stored in scene plan as `transition_to_next`
  - Default fallback: "crossfade" if not specified
- **Implementation**: Updated in `backend/app/api/routes/generations.py` and `backend/app/services/pipeline/stitching.py`

## Previous Updates (2025-11-17)

### Image Generation Prompts in Storyboard
- **Added**: Image generation prompts now displayed in storyboard visualizer
- **Features**:
  - Each image (reference, start, end) shows the actual prompt used for generation
  - Enhanced prompts include consistency markers (e.g., "Style: cinematic, Color palette: cool blues...")
  - Prompts stored in storyboard plan: `reference_image_prompt`, `start_image_enhanced_prompt`, `end_image_enhanced_prompt`
  - Fallback to base prompts for backward compatibility
- **Implementation**: 
  - Backend stores enhanced prompts when images are generated
  - Frontend displays prompts below each image in storyboard visualizer
  - Prompts show the complete text sent to image generation model (base prompt + consistency markers)

### Image Path Normalization
- **Fixed**: Image paths now normalized to relative paths before storage
- **Issue**: Absolute Windows paths (e.g., `D:\gauntlet-ai\...`) were stored, causing image loading failures
- **Solution**: Added `normalize_path()` function to convert absolute paths to relative paths (e.g., `output/temp/images/...`)
- **Benefit**: Images now load correctly in storyboard visualizer

### Brand Overlay Bug Fix
- **Fixed**: Changed `set_opacity()` to `with_opacity()` for MoviePy ColorClip
- **Issue**: `AttributeError: 'ColorClip' object has no attribute 'set_opacity'`
- **Solution**: Updated to use correct MoviePy API method
- **Location**: `backend/app/services/pipeline/overlays.py`

### Storyboard Reconstruction Fallback
- **Added**: Fallback to reconstruct storyboard from `scene_plan` if `storyboard_plan` missing
- **Features**:
  - Automatically reconstructs storyboard for older generations
  - Extracts image paths and prompts from `scene_plan`
  - Converts image paths to public URLs
  - Helps with videos generated before storyboard feature was fully implemented
- **Implementation**: Added in `get_generation_status()` endpoint

## Previous Updates (2025-01-XX)

### Brand Overlay Feature
- **Added**: Automatic brand name overlay at the end of videos
- **Features**:
  - Extracts brand name from user prompt (e.g., "Nike", "Apple", "Adidas")
  - Displays brand name in center of screen with semi-transparent black background
  - White text, 72px font, uppercase display
  - Fade-in animation
  - Appears for last 2 seconds of video
  - Graceful fallback if brand extraction fails
- **Implementation**: `extract_brand_name()` and `add_brand_overlay_to_final_video()` in `overlays.py`
- **Integration**: Added after audio layer, before final export (92% progress)

### Resilient Error Handling
- **Improved**: Text overlay, audio, and brand overlay stages now have error handling
- **Features**:
  - Text overlay failures: Falls back to raw clips without overlays
  - Audio layer failures: Falls back to silent video (stitched clips)
  - Brand overlay failures: Falls back to video without brand overlay
  - All failures logged as warnings, generation continues
- **Benefit**: Generation completes even if optional enhancements fail

### Storyboard Visualizer UI
- **Added**: Real-time storyboard visualizer component in frontend
- **Features**: 
  - Displays storyboard plan with images during generation
  - Shows consistency markers and scene details
  - Visual representation of all generated images (reference, start, end)
  - Integrated into Dashboard component
- **API**: Updated status endpoint to return storyboard plan with image URLs

### Kling 2.5 Turbo Pro Support
- **Added**: Full support for Kling 2.5 Turbo Pro (`kwaivgi/kling-v2.5-turbo-pro`)
- **Features**:
  - Generates start images (first frame) for each scene
  - Generates end images (last frame) for each scene
  - Passes reference, start, and end images to video model
  - Enhanced storyboard planning includes start/end image prompts
- **Model**: Updated to use correct Replicate model name

## Implementation Date: 2025-01-XX

## Changes Made

### New Workflow

**Before**: 
- User prompt → LLM JSON blueprint → Scene Assembler → Video generation
- Complex JSON structures
- No reference image generation

**After**:
- User prompt → Detailed Storyboard Planning → Image Generation → Video Generation
- Simple, detailed prompts
- Sequential reference image generation
- Visual consistency chain

### New Files Created

1. **`storyboard_planner.py`**
   - Plans detailed storyboard with GPT-4o
   - Generates 40-80 word detailed prompts
   - Creates consistency markers
   - Supports vision API for reference images

2. **`image_generation.py`**
   - Single image generation with Nano Banana
   - Supports reference images for consistency
   - Applies consistency markers to prompts

3. **`image_generation_batch.py`**
   - Sequential batch image generation
   - Each image uses previous as reference
   - Maintains visual consistency chain

### Modified Files

1. **`generations.py`** (Pipeline)
   - Added storyboard planning step
   - Added image generation step
   - Updated to use detailed prompts from storyboard
   - Updated to use generated reference images

2. **`video_generation.py`**
   - Added `consistency_markers` parameter
   - Added `_enhance_prompt_with_markers()` function
   - Updated to use detailed prompts and reference images

3. **`generation.py`** (Schema)
   - Added `reference_image_path` to Scene model
   - Added `model_prompts` to Scene model (for future use)

### Key Features

1. **Detailed Storyboard Planning**
   - LLM creates rich, detailed prompts (40-80 words)
   - Includes visual details, composition, camera angles
   - Generates consistency markers

2. **Sequential Image Generation**
   - Images generated one after another
   - Each uses previous image as reference
   - Maintains character/style consistency

3. **Parallel Video Generation**
   - All videos generated simultaneously
   - Uses detailed prompts from storyboard
   - Uses corresponding generated reference images

4. **Dual Consistency System**
   - Text-based markers (style, color, lighting, etc.)
   - Visual reference images (pixel-level consistency)

## Models Used

- **Storyboard Planning**: GPT-4o (OpenAI)
- **Image Generation**: Nano Banana / google/nano-banana (Replicate)
- **Video Generation**: Sora-2, Veo-3, PixVerse (Replicate)

## Benefits

1. **Better Quality**: Detailed prompts produce better results
2. **Visual Consistency**: Reference images ensure cohesion
3. **Simpler Workflow**: No complex JSON structures
4. **Flexible**: Can use different models for different scenes
5. **Maintainable**: Clear separation of concerns

## Migration Notes

- Old workflow still available as fallback
- Set `use_llm=True` to use new workflow
- Storyboard plan stored in `coherence_settings["storyboard_plan"]`
- Reference images stored in `output/temp/images/{generation_id}/`

