# API Reference

## Storyboard Planner

### `plan_storyboard()`

**Location**: `backend/app/services/pipeline/storyboard_planner.py`

**Signature**:
```python
async def plan_storyboard(
    user_prompt: str,
    reference_image_path: Optional[str] = None,
    max_retries: int = 3,
) -> dict
```

**Parameters**:
- `user_prompt` (str): User's original prompt
- `reference_image_path` (Optional[str]): Path to user-provided reference image
- `max_retries` (int): Maximum retry attempts (default: 3)

**Returns**:
- `dict`: Storyboard plan with detailed prompts, markers, and scene descriptions

**Example**:
```python
storyboard_plan = await plan_storyboard(
    user_prompt="Create an ad for a fitness app",
    reference_image_path="/path/to/reference.jpg"
)

# Access detailed prompts
for scene in storyboard_plan["scenes"]:
    print(scene["detailed_prompt"])
    
# Access markers
markers = storyboard_plan["consistency_markers"]
```

## Image Generation

### `generate_image()`

**Location**: `backend/app/services/pipeline/image_generation.py`

**Signature**:
```python
async def generate_image(
    prompt: str,
    output_dir: str,
    generation_id: str,
    scene_number: Optional[int] = None,
    consistency_markers: Optional[dict] = None,
    reference_image_path: Optional[str] = None,
    cancellation_check: Optional[callable] = None,
) -> str
```

**Parameters**:
- `prompt` (str): Detailed prompt from storyboard
- `output_dir` (str): Directory to save image
- `generation_id` (str): Generation ID for logging
- `scene_number` (Optional[int]): Scene number for filename
- `consistency_markers` (Optional[dict]): Consistency markers to enhance prompt
- `reference_image_path` (Optional[str]): Previous image for visual consistency
- `cancellation_check` (Optional[callable]): Function to check cancellation

**Returns**:
- `str`: Path to generated image file

**Example**:
```python
image_path = await generate_image(
    prompt="A young professional jogging through a sunlit park...",
    output_dir="output/images",
    generation_id="gen-123",
    scene_number=1,
    consistency_markers={
        "style": "dynamic modern",
        "color_palette": "vibrant primary colors",
        ...
    },
    reference_image_path=None  # First image has no reference
)
```

### `generate_images_with_sequential_references()`

**Location**: `backend/app/services/pipeline/image_generation_batch.py`

**Signature**:
```python
async def generate_images_with_sequential_references(
    prompts: List[str],
    output_dir: str,
    generation_id: str,
    consistency_markers: Optional[dict] = None,
    cancellation_check: Optional[callable] = None,
) -> List[str]
```

**Parameters**:
- `prompts` (List[str]): List of detailed prompts (one per scene)
- `output_dir` (str): Directory to save images
- `generation_id` (str): Generation ID for logging
- `consistency_markers` (Optional[dict]): Shared consistency markers
- `cancellation_check` (Optional[callable]): Function to check cancellation

**Returns**:
- `List[str]`: List of paths to generated images (in order)

**Example**:
```python
image_paths = await generate_images_with_sequential_references(
    prompts=[
        "A young professional jogging through a sunlit park...",
        "The same person checking their phone while jogging...",
        "The same person at a modern gym...",
        "The same person celebrating their achievement..."
    ],
    output_dir="output/images",
    generation_id="gen-123",
    consistency_markers=markers
)
# Returns: ["scene_1.png", "scene_2.png", "scene_3.png", "scene_4.png"]
```

## Video Generation

### `generate_video_clip()`

**Location**: `backend/app/services/pipeline/video_generation.py`

**Signature**:
```python
async def generate_video_clip(
    scene: Scene,
    output_dir: str,
    generation_id: str,
    scene_number: int,
    cancellation_check: Optional[callable] = None,
    seed: Optional[int] = None,
    preferred_model: Optional[str] = None,
    reference_image_path: Optional[str] = None,
    consistency_markers: Optional[dict] = None,
) -> tuple[str, str]
```

**Parameters**:
- `scene` (Scene): Scene object with detailed prompt and reference image path
- `output_dir` (str): Directory to save video
- `generation_id` (str): Generation ID for logging
- `scene_number` (int): Scene number
- `cancellation_check` (Optional[callable]): Function to check cancellation
- `seed` (Optional[int]): Seed for visual consistency
- `preferred_model` (Optional[str]): Preferred video model
- `reference_image_path` (Optional[str]): Generated reference image path
- `consistency_markers` (Optional[dict]): Consistency markers

**Returns**:
- `tuple[str, str]`: (clip_path, model_used)

**Example**:
```python
clip_path, model_used = await generate_video_clip(
    scene=scene,  # Contains detailed_prompt and reference_image_path
    output_dir="output/videos",
    generation_id="gen-123",
    scene_number=1,
    reference_image_path="output/images/scene_1.png",
    consistency_markers=markers
)
```

## Helper Functions

### `_enhance_prompt_with_markers()`

**Location**: `backend/app/services/pipeline/video_generation.py`

**Signature**:
```python
def _enhance_prompt_with_markers(
    base_prompt: str,
    consistency_markers: Optional[dict] = None,
) -> str
```

**Purpose**: Enhances prompt by appending consistency markers

**Example**:
```python
enhanced = _enhance_prompt_with_markers(
    "A person jogging in a park",
    {"style": "cinematic", "color_palette": "warm tones"}
)
# Returns: "A person jogging in a park. Style: cinematic, Color palette: warm tones"
```

### `_build_prompt_with_markers()`

**Location**: `backend/app/services/pipeline/image_generation.py`

**Signature**:
```python
def _build_prompt_with_markers(
    base_prompt: str,
    consistency_markers: Optional[dict] = None,
) -> str
```

**Purpose**: Same as above, for image generation

## Main Pipeline Entry Point

### `process_generation()`

**Location**: `backend/app/api/routes/generations.py`

**Signature**:
```python
async def process_generation(
    generation_id: str,
    prompt: str,
    preferred_model: Optional[str] = None,
    num_clips: Optional[int] = None,
    use_llm: bool = True,
    image_path: Optional[str] = None,
):
```

**Workflow**:
1. Plans storyboard (if `use_llm=True`)
2. Generates reference images sequentially
3. Creates scene plan from storyboard
4. Generates videos in parallel
5. Assembles final video

**Called by**: 
- `POST /api/generate` endpoint
- `POST /api/generate-with-image` endpoint

