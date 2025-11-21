# Implementation Details

## File Structure

```
backend/app/services/pipeline/
├── storyboard_planner.py          # Detailed storyboard planning (NEW)
├── image_generation.py             # Single image generation with Nano Banana
├── image_generation_batch.py       # Sequential batch image generation (NEW)
├── video_generation.py             # Video generation (updated with markers)
└── prompt_generator.py             # Alternative prompt generation (legacy)

backend/app/api/routes/
└── generations.py                  # Main pipeline (updated workflow)

backend/app/schemas/
└── generation.py                  # Scene schema (updated with reference_image_path)
```

## Key Functions

### Storyboard Planning

```python
# backend/app/services/pipeline/storyboard_planner.py

async def plan_storyboard(
    user_prompt: str,
    reference_image_path: Optional[str] = None,
    max_retries: int = 3,
) -> dict:
    """
    Creates detailed storyboard plan with:
    - 4 detailed prompts (40-80 words each)
    - Consistency markers
    - Scene descriptions
    """
```

**Returns**:
```python
{
    "consistency_markers": {
        "style": "...",
        "color_palette": "...",
        "lighting": "...",
        "composition": "...",
        "mood": "..."
    },
    "scenes": [
        {
            "scene_number": 1,
            "aida_stage": "Attention",
            "detailed_prompt": "40-80 word detailed prompt...",
            "scene_description": {...},
            "duration_seconds": 4
        },
        ...
    ]
}
```

### Image Generation

```python
# backend/app/services/pipeline/image_generation.py

async def generate_image(
    prompt: str,
    output_dir: str,
    generation_id: str,
    scene_number: Optional[int] = None,
    consistency_markers: Optional[dict] = None,
    reference_image_path: Optional[str] = None,  # Previous image
    cancellation_check: Optional[callable] = None,
) -> str:
    """
    Generates single image with Nano Banana.
    Uses reference_image_path for visual consistency.
    """
```

### Batch Image Generation

```python
# backend/app/services/pipeline/image_generation_batch.py

async def generate_images_with_sequential_references(
    prompts: List[str],
    output_dir: str,
    generation_id: str,
    consistency_markers: Optional[dict] = None,
    cancellation_check: Optional[callable] = None,
) -> List[str]:
    """
    Generates multiple images sequentially.
    Each image uses the previous one as reference.
    """
```

### Video Generation

```python
# backend/app/services/pipeline/video_generation.py

async def generate_video_clip(
    scene: Scene,
    output_dir: str,
    generation_id: str,
    scene_number: int,
    cancellation_check: Optional[callable] = None,
    seed: Optional[int] = None,
    preferred_model: Optional[str] = None,
    reference_image_path: Optional[str] = None,  # Generated reference image
    reference_images: Optional[List[str]] = None,  # Array of 1-3 reference images (Veo 3.1 R2V mode)
    start_image_path: Optional[str] = None,  # Start frame (Veo 3.1, Kling 2.5 Turbo Pro)
    end_image_path: Optional[str] = None,  # End frame (Veo 3.1, Kling 2.5 Turbo Pro)
    resolution: Optional[str] = None,  # "720p" or "1080p" (Veo 3.1)
    generate_audio: Optional[bool] = None,  # Audio generation (Veo 3.1)
    negative_prompt: Optional[str] = None,  # Negative prompt (Veo 3.1)
    consistency_markers: Optional[dict] = None,   # Text markers
) -> tuple[str, str]:
    """
    Generates video clip using:
    - Detailed prompt from scene.visual_prompt
    - Consistency markers
    - Generated reference image(s) or start/end frames
    - Default model: Google Veo 3.1
    """
```

## Pipeline Flow (Code)

### Step 1: Storyboard Planning

```python
# In process_generation()

storyboard_plan = await plan_storyboard(
    user_prompt=prompt,
    reference_image_path=image_path,  # User-provided if available
)

# Extract markers and prompts
consistency_markers = storyboard_plan.get("consistency_markers", {})
scene_detailed_prompts = [
    scene.get("detailed_prompt", "") 
    for scene in storyboard_plan.get("scenes", [])
]

# Store in database
generation.coherence_settings["consistency_markers"] = consistency_markers
generation.coherence_settings["storyboard_plan"] = storyboard_plan
```

### Step 2: Image Generation

```python
# If user provided a reference image, use it directly as first scene reference
if user_initial_reference:
    # Copy user's image to first scene reference location
    first_scene_ref_path = image_dir / f"{generation_id}_scene_1.png"
    shutil.copy2(user_initial_reference, first_scene_ref_path)
    first_reference_image = str(first_scene_ref_path)
    
    # Generate remaining reference images (scenes 2+) using sequential chaining
    # Start the chain with the user's image
    if len(scene_detailed_prompts) > 1:
        remaining_prompts = scene_detailed_prompts[1:]
        remaining_reference_images = await generate_enhanced_reference_images_with_sequential_references(
            prompts=remaining_prompts,
            output_dir=str(image_dir),
            generation_id=generation_id,
            consistency_markers=consistency_markers,
            initial_reference_image=first_reference_image,  # Start with user's image
            ...
        )
        reference_image_paths = [first_reference_image] + remaining_reference_images
    else:
        reference_image_paths = [first_reference_image]
else:
    # No user image: Generate all images sequentially with enhanced mode
    reference_image_paths = await generate_enhanced_reference_images_with_sequential_references(
        prompts=scene_detailed_prompts,
        output_dir=str(image_dir),
        generation_id=generation_id,
        consistency_markers=consistency_markers,
        initial_reference_image=None,
        ...
    )

# Store reference image paths in storyboard plan
for idx, scene in enumerate(storyboard_plan.get("scenes", [])):
    if idx < len(reference_image_paths):
        scene["reference_image_path"] = reference_image_paths[idx]
```

### Step 3: Video Generation

```python
# Create Scene objects with detailed prompts and reference images
scenes = []
for scene_data in storyboard_plan.get("scenes", []):
    scenes.append(
        Scene(
            scene_number=scene_data.get("scene_number", 0),
            scene_type=scene_data.get("aida_stage", "Scene"),
            visual_prompt=scene_data.get("detailed_prompt", ""),  # Detailed prompt
            reference_image_path=scene_data.get("reference_image_path"),  # Generated image
            duration=int(scene_data.get("duration_seconds", 4)),
        )
    )

# Generate videos in parallel
for scene in scenes:
    await generate_video_clip(
        scene=scene,
        reference_image_path=scene.reference_image_path,  # Generated reference
        consistency_markers=consistency_markers,  # Shared markers
        ...
    )
```

## Data Structures

### Storyboard Plan

```python
{
    "consistency_markers": {
        "style": str,
        "color_palette": str,
        "lighting": str,
        "composition": str,
        "mood": str
    },
    "scenes": [
        {
            "scene_number": int,
            "aida_stage": str,
            "detailed_prompt": str,  # 40-80 words (base prompt)
            "start_image_prompt": str,  # First frame description (base prompt)
            "end_image_prompt": str,    # Last frame description (base prompt)
            "reference_image_prompt": str,  # Enhanced prompt with markers (for reference image)
            "start_image_enhanced_prompt": str,  # Enhanced prompt with markers (for start image)
            "end_image_enhanced_prompt": str,   # Enhanced prompt with markers (for end image)
            "scene_description": {
                "environment": str,
                "character_action": str,
                "camera_angle": str,
                "composition": str,
                "visual_elements": str
            },
            "duration_seconds": int,
            "reference_image_path": str,  # Relative path (normalized from absolute)
            "start_image_path": str,      # Relative path (normalized from absolute)
            "end_image_path": str,         # Relative path (normalized from absolute)
            "reference_image_url": str,   # Converted to URL for frontend
            "start_image_url": str,       # Converted to URL for frontend
            "end_image_url": str          # Converted to URL for frontend
        }
    ]
}
```

**Note**: Enhanced prompts are stored after image generation and include the base prompt plus consistency markers (e.g., "Detailed prompt. Style: cinematic, Color palette: cool blues, Lighting: soft natural light...").

### Scene Object

```python
class Scene(BaseModel):
    scene_number: int
    scene_type: str
    visual_prompt: str  # Detailed prompt from storyboard
    model_prompts: dict[str, str]  # Model-specific (optional)
    reference_image_path: Optional[str]  # Generated reference image (or user's image for scene 1)
    start_image_path: Optional[str]  # Generated start image (for Veo 3.1, Kling 2.5 Turbo Pro)
    end_image_path: Optional[str]  # Generated end image (for Veo 3.1, Kling 2.5 Turbo Pro)
    transition_to_next: Optional[str]  # LLM-selected transition type (e.g., "crossfade")
    text_overlay: Optional[TextOverlay]
    duration: int
    sound_design: Optional[str]
```

## Database Storage

- **Storyboard Plan**: `Generation.coherence_settings["storyboard_plan"]`
- **Consistency Markers**: `Generation.coherence_settings["consistency_markers"]`
- **Reference Images**: Stored in `output/temp/images/{generation_id}/`
- **Start Images**: Stored in `output/temp/images/{generation_id}/start/` (for Kling 2.5 Turbo Pro)
- **End Images**: Stored in `output/temp/images/{generation_id}/end/` (for Kling 2.5 Turbo Pro)
- **Reference Image Paths**: Stored in `Scene.reference_image_path`, `Scene.start_image_path`, `Scene.end_image_path` (in scene_plan)

## Frontend Components

### Storyboard Visualizer

**Location**: `frontend/src/components/storyboard/StoryboardVisualizer.tsx`

**Props**:
```typescript
interface StoryboardVisualizerProps {
  storyboardPlan: StoryboardPlan;
  prompt: string;
}
```

**Features**:
- Displays original prompt
- Shows consistency markers (style, color, lighting, composition, mood)
- Visual grid of images for each scene (reference, start, end)
- **Image Generation Prompts**: Shows the actual prompt used to generate each image (with consistency markers)
- Scene details (environment, action, camera angle, composition)
- AIDA stage labels
- Responsive design with Tailwind CSS

**Image Prompt Display**:
- Each image (reference, start, end) displays its generation prompt below the image
- Shows enhanced prompt (base prompt + consistency markers) if available
- Falls back to base prompt for backward compatibility
- Prompts displayed in gray boxes with "Image Prompt:" label

**Integration**:
- Automatically appears in Dashboard when `activeGeneration.storyboard_plan` exists
- Updates in real-time as storyboard is generated
- Image URLs are converted from paths to public URLs by backend
- Accessible via `/storyboard/:generationId` route
- "View Storyboard" button on VideoDetail page (when LLM enhancement was used)

**API Data Flow**:
```
Backend: coherence_settings["storyboard_plan"] 
  → Status endpoint converts paths to URLs
  → Status endpoint reconstructs from scene_plan if needed (fallback)
  → Frontend receives storyboard_plan with image_urls and enhanced prompts
  → StoryboardVisualizer displays images, prompts, and details
```

## Image Path Normalization

### Path Storage

Image paths are normalized to relative paths before storing in the storyboard plan:

```python
# backend/app/api/routes/generations.py

def normalize_path(path: str) -> str:
    """Convert absolute path to relative path for storage."""
    if not path:
        return path
    # If already relative, return as-is
    if not os.path.isabs(path):
        return path
    # Convert absolute path to relative
    # Paths like: D:\gauntlet-ai\ad-mint-ai\backend\output\temp\images\...
    # Become: output/temp/images/...
    backend_dir = Path(__file__).parent.parent.parent  # backend directory
    try:
        relative_path = os.path.relpath(path, backend_dir)
        # Normalize to forward slashes for URLs
        return relative_path.replace("\\", "/")
    except ValueError:
        # If path is on different drive (Windows), extract the relative part
        if "output" in path:
            idx = path.find("output")
            return path[idx:].replace("\\", "/")
        return path.replace("\\", "/")
```

**Benefits**:
- Paths work across different operating systems
- Can be converted to public URLs correctly
- Images load properly in frontend storyboard visualizer

## Storyboard Reconstruction Fallback

### Automatic Reconstruction

If `storyboard_plan` is missing from `coherence_settings`, the system attempts to reconstruct it from `scene_plan`:

```python
# In get_generation_status() endpoint

# Fallback: Try to reconstruct storyboard from scene_plan
if generation.scene_plan and isinstance(generation.scene_plan, dict):
    scenes = generation.scene_plan.get("scenes", [])
    if scenes and any(scene.get("reference_image_path") for scene in scenes):
        # Reconstruct storyboard structure
        reconstructed_scenes = []
        for scene in scenes:
            reconstructed_scene = {
                "scene_number": scene.get("scene_number", 0),
                "aida_stage": scene.get("scene_type", "Scene"),
                "detailed_prompt": scene.get("visual_prompt", ""),
                "reference_image_path": scene.get("reference_image_path"),
                "start_image_path": scene.get("start_image_path"),
                "end_image_path": scene.get("end_image_path"),
                "duration_seconds": scene.get("duration", 4),
            }
            reconstructed_scenes.append(reconstructed_scene)
        
        storyboard_plan = {
            "consistency_markers": consistency_markers or {},
            "scenes": reconstructed_scenes
        }
```

**Use Cases**:
- Videos generated before storyboard feature was fully implemented
- Videos where storyboard planning failed but images were generated
- Legacy generations that have images but no stored storyboard plan

**Limitations**:
- Enhanced prompts may not be available (only base prompts)
- Scene descriptions may be missing
- Start/end image prompts may not be available

## Error Handling

- Storyboard planning failures: Falls back to old LLM enhancement
- Image generation failures: Retries with exponential backoff
- Video generation failures: Tries fallback models
- Reference image missing: Continues without reference (uses markers only)

## Brand Overlay Implementation

### Brand Name Extraction

```python
# backend/app/services/pipeline/overlays.py

def extract_brand_name(prompt: str) -> Optional[str]:
    """
    Extracts brand name from user prompt.
    - Checks common brand names (Nike, Adidas, Apple, etc.)
    - Falls back to capitalized words in prompt
    - Returns None if no brand found
    """
```

### Brand Overlay Addition

```python
# backend/app/services/pipeline/overlays.py

def add_brand_overlay_to_final_video(
    video_path: str,
    brand_name: Optional[str],
    output_path: str,
    duration: float = 2.0
) -> str:
    """
    Adds brand overlay at the end of video:
    - Creates semi-transparent black background
    - Centers brand name (white text, 72px font, uppercase)
    - Applies fade-in animation
    - Appears for last 2 seconds
    """
```

**Visual Design**:
- Background: Semi-transparent black (70% opacity)
- Text: White, uppercase, 72px font
- Position: Center of screen
- Padding: 30% horizontal, 40% vertical
- Animation: Fade-in
- Duration: Last 2 seconds of video

### Integration in Pipeline

```python
# In process_generation() after audio layer

# Extract brand name from prompt
brand_name = extract_brand_name(prompt)

# Add brand overlay if found
if brand_name:
    try:
        video_with_brand = add_brand_overlay_to_final_video(
            video_path=video_with_audio,
            brand_name=brand_name,
            output_path=brand_overlay_output_path,
            duration=2.0
        )
        video_for_export = video_with_brand
    except Exception as e:
        # Fallback: continue without brand overlay
        logger.warning(f"Brand overlay failed: {e}")
        video_for_export = video_with_audio
```

## Error Handling

### Resilient Pipeline Stages

All optional enhancement stages now have error handling:

1. **Text Overlays** (70% progress):
   ```python
   try:
       overlay_paths = add_overlays_to_clips(...)
   except Exception as e:
       logger.warning(f"Text overlay failed: {e}")
       overlay_paths = clip_paths  # Fallback to raw clips
   ```

2. **Audio Layer** (90% progress):
   ```python
   try:
       video_with_audio = add_audio_layer(...)
   except Exception as e:
       logger.warning(f"Audio failed: {e}")
       video_with_audio = stitched_video_path  # Fallback to silent
   ```

3. **Brand Overlay** (92% progress):
   ```python
   try:
       video_with_brand = add_brand_overlay_to_final_video(...)
   except Exception as e:
       logger.warning(f"Brand overlay failed: {e}")
       video_for_export = video_with_audio  # Fallback without brand
   ```

**Benefits**:
- Generation completes even if optional enhancements fail
- Users get video output in all cases
- Failures logged for debugging
- No silent failures

## Progress Tracking

- 5%: Storyboard Planning
- 15%: Image Generation
- 20%: Scene Plan Creation
- 30-70%: Video Generation
- 70%: Text Overlays (with error handling)
- 80%: Video Stitching
- 90%: Audio Layer (with error handling)
- 92%: Brand Overlay (with error handling)
- 95-100%: Final Export and Post-processing

