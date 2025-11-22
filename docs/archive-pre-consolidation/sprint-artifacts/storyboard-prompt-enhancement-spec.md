# Storyboard Prompt Enhancement Service - Technical Specification

## Overview

A specialized prompt enhancement service for generating high-quality storyboard prompts that maintain visual coherence with the original generated image. Uses a two-agent iterative feedback loop (similar to image prompt enhancement) to create distinct, creative start/end frame prompts for each scene following the Sensory Journey framework.

## Purpose

**Problem:** Current storyboard generation (`_generate_frame_prompts()`) only appends generic modifiers ("Opening scene, establishing shot") to the same base prompt, resulting in lackluster creative distinction between start/end frames.

**Solution:** Create a dedicated storyboard prompt enhancement service that:
- Extracts visual elements from the best generated image (brand, bottle shape, colors, style)
- Uses Sensory Journey framework (hardcoded, 3 scenes configurable)
- Generates creatively distinct start/end prompts for each scene
- Maintains visual coherence across all storyboard frames
- Controls progressive product reveal (hidden → partial → full)

## Architecture

### Service Location
`backend/app/services/pipeline/storyboard_prompt_enhancement.py`

### Dependencies
- OpenAI API (GPT-4 Vision for image analysis, GPT-4 Turbo for agents)
- PIL/Pillow for image handling
- Existing: `image_prompt_enhancement.py` (as reference pattern)

## Data Flow

```
8-1: Enhanced prompt → enhanced_prompt.txt
8-2: Best image → image_001.png
8-3: Storyboard Prompt Enhancer
  ├─ Input: enhanced_prompt.txt + image_001.png + num_scenes (configurable, default 3)
  ├─ Step 1: Extract visual elements from image (GPT-4 Vision)
  ├─ Step 2: Iterative enhancement loop (Cinematic Creative ↔ Storyboard Engineer)
  └─ Output: 6 enhanced prompts (3 scenes × 2 frames = start/end for each)
8-4: Generate storyboard images using the 6 enhanced prompts
```

## Visual Element Extraction

### Image Analysis Component
Uses GPT-4 Vision API to extract:
- **Brand elements**: Brand name, logo style, brand colors (hex codes)
- **Product details**: Bottle shape, size, design elements, materials
- **Color palette**: Dominant colors, accent colors, color scheme
- **Style/aesthetic**: Abstract style indicators, mood, visual tone
- **Composition**: Framing, perspective, lighting style

### Prompt for Vision API
```
Analyze this perfume advertisement image and extract the following visual elements:

1. Brand Identity:
   - Brand name (if visible or inferable)
   - Brand colors (provide hex codes for dominant colors)
   - Logo style or brand markers

2. Product Details:
   - Bottle shape and design (cylindrical, rectangular, unique shape, etc.)
   - Bottle size and proportions
   - Materials/textures visible (glass, metal, matte, glossy)
   - Any distinctive design elements

3. Color Palette:
   - Dominant colors (with hex codes)
   - Accent colors
   - Overall color scheme (warm, cool, monochromatic, etc.)

4. Style & Aesthetic:
   - Visual style (abstract, minimalist, luxury, vibrant, etc.)
   - Mood and atmosphere
   - Composition style (centered, dynamic, etc.)
   - Lighting characteristics

5. Composition Elements:
   - Framing and perspective
   - Background style
   - Any recurring visual motifs

Return as structured JSON.
```

## Sensory Journey Framework (Hardcoded)

### Scene Structure
- **Scene 1: Discovery** - Product reveal, first impression
  - Product visibility: Hidden or partially obscured (mystery)
  - Emotional arc: Anticipation → Recognition
  - Visual progression: Abstract/mysterious → Product comes into focus

- **Scene 2: Transformation** - Application/experience, emotional connection
  - Product visibility: Partial reveal (more visible than Scene 1)
  - Emotional arc: Recognition → Connection
  - Visual progression: Product-focused → Experience/application

- **Scene 3: Desire** - Aspiration, lifestyle, call to action
  - Product visibility: Full reveal (product prominently featured)
  - Emotional arc: Connection → Aspiration
  - Visual progression: Experience → Lifestyle/elegance

### Progressive Reveal Logic
- Scene 1: Product hidden or very subtle (abstract shapes, shadows, reflections)
- Scene 2: Product partially visible (side angle, close-up details, application)
- Scene 3: Product fully visible (hero shot, lifestyle integration)

## Two-Agent System

### Agent 1: Cinematic Creative Director
**Role:** Creates visually distinct, creative start/end prompts for each scene

**System Prompt Focus:**
- Visual storytelling expertise
- Abstract ad style suggestion (let it emerge naturally, don't force it)
- Scene transition understanding
- Creative distinction between start/end frames
- Motion description generation (camera movement, visual transitions, what changes between frames)
- Sensory Journey framework knowledge
- Progressive reveal control
- Visual coherence maintenance (brand, colors, bottle shape)

**Output:** Enhanced prompts for start and end frames of each scene, plus motion description, all written as single flowing sentences (like image prompt enhancement)

**Key Responsibilities:**
- Generate distinct visual states for start vs end of each scene
- Generate motion descriptions that describe what happens between start and end frames
- Maintain brand/product consistency across scenes
- Control progressive product reveal
- Suggest abstract artistic style (let it emerge naturally, don't force it)
- Create compelling visual transitions

### Agent 2: Storyboard Prompt Engineer
**Role:** Critiques and scores storyboard prompts for quality and coherence

**Evaluation Criteria:**
1. **Completeness (0-100)**: Does it have all necessary elements (scene context, visual state, style, cinematography)?
2. **Creative Distinction (0-100)**: Are start/end frames visually distinct and creative? Do they show clear progression?
3. **Visual Coherence (0-100)**: Does it maintain brand colors, bottle shape, and style from original image?
4. **Framework Alignment (0-100)**: Does it align with Sensory Journey framework (Discovery → Transformation → Desire)?
5. **Progressive Reveal (0-100)**: Does product visibility progress correctly (hidden → partial → full)?
6. **Abstract Style (0-100)**: Does it suggest abstract ad style naturally? (Should emerge organically, not be forced)

**Output:** JSON with scores, critique, and improvement suggestions

## Service Interface

### Main Function
```python
async def enhance_storyboard_prompts(
    original_prompt: str,
    reference_image_path: str,
    num_scenes: int = 3,
    max_iterations: int = 3,
    score_threshold: float = 85.0,
    trace_dir: Optional[Path] = None
) -> StoryboardEnhancementResult
```

### Input Parameters
- `original_prompt`: Enhanced prompt from 8-1 (string)
- `reference_image_path`: Path to best image from 8-2 (string/Path)
- `num_scenes`: Number of scenes (default: 3, configurable via CLI parameter `--num-clips`)
- `max_iterations`: Max iteration rounds (default: 3)
- `score_threshold`: Stop if overall score >= this (default: 85.0)
- `trace_dir`: Optional directory to save trace files

### Return Type
```python
@dataclass
class StoryboardEnhancementResult:
    original_prompt: str
    reference_image_path: str
    extracted_visual_elements: Dict[str, Any]
    scene_prompts: List[ScenePromptSet]  # One per scene
    iterations: List[Dict]  # Iteration history
    final_scores: Dict[str, float]
    total_iterations: int

@dataclass
class ScenePromptSet:
    scene_number: int
    scene_type: str  # "Discovery", "Transformation", "Desire"
    start_frame_prompt: str
    end_frame_prompt: str
    motion_description: str
    product_visibility: str  # "hidden", "partial", "full"
```

## Enhancement Process

### Step 1: Extract Visual Elements
1. Load reference image
2. Call GPT-4 Vision API with image analysis prompt
3. Parse JSON response with visual elements
4. Validate and store extracted elements

### Step 2: Initialize Scene Structure
1. Create scene structure based on Sensory Journey framework
2. Assign scene types: Discovery, Transformation, Desire
3. Set product visibility levels per scene
4. Create initial prompt templates incorporating visual elements

### Step 3: Iterative Enhancement Loop
For each scene (1 to num_scenes):
1. **Agent 1 (Cinematic Creative)**: Generate start/end prompts AND motion description
   - Input: Scene context, visual elements, framework guidance, previous feedback
   - Output: Enhanced start_frame_prompt, end_frame_prompt, and motion_description
   - Motion description should describe: camera movement, visual transitions, what changes between frames
2. **Agent 2 (Storyboard Engineer)**: Critique and score
   - Input: Both prompts AND motion description for the scene
   - Output: Scores, critique, improvements (including motion description quality)
3. **Convergence Check**: 
   - If score >= threshold OR improvement < 2 points: Move to next scene
   - Else: Iterate with feedback
4. **Max Iterations**: Stop after max_iterations even if threshold not met

## Integration with Storyboard Service

### Modified Workflow in `storyboard_service.py`

**Current Flow:**
```python
scene_plan = create_basic_scene_plan_from_prompt(...)
for scene in scene_plan.scenes:
    start_prompt, end_prompt, motion = _generate_frame_prompts(...)  # Generic
    # Generate images
```

**New Flow:**
```python
# After 8-2 generates best image, get its path
best_image_path = get_best_image_from_8_2(...)

# NEW: Enhance storyboard prompts
storyboard_result = await enhance_storyboard_prompts(
    original_prompt=working_prompt,
    reference_image_path=best_image_path,
    num_scenes=num_clips,
    trace_dir=output_dir / "storyboard_enhancement_trace"
)

# Use enhanced prompts instead of generic ones
for scene_prompt_set in storyboard_result.scene_prompts:
    # Generate start frame image
    start_image = await generate_images(prompt=scene_prompt_set.start_frame_prompt, ...)
    # Generate end frame image
    end_image = await generate_images(prompt=scene_prompt_set.end_frame_prompt, ...)
```

## Trace Files (Optional)

If `trace_dir` provided, save:
- `00_reference_image.png` - Copy of reference image
- `01_extracted_visual_elements.json` - Extracted visual elements
- `02_scene_1_initial_prompts.txt` - Initial prompts for scene 1
- `03_scene_1_iteration_1_agent1.txt` - Agent 1 enhancement
- `04_scene_1_iteration_1_agent2.json` - Agent 2 critique
- `05_scene_1_final_prompts.txt` - Final prompts for scene 1
- ... (repeat for each scene)
- `storyboard_enhancement_summary.json` - Complete summary

## Example Output

### Extracted Visual Elements
```json
{
  "brand_identity": {
    "brand_name": "Luxe Parfum",
    "brand_colors": ["#2C1810", "#D4AF37", "#FFFFFF"],
    "logo_style": "Elegant serif typography"
  },
  "product_details": {
    "bottle_shape": "Rectangular with rounded edges, tall and slender",
    "materials": "Clear glass with gold accents",
    "distinctive_elements": "Gold cap, minimalist label"
  },
  "color_palette": {
    "dominant_colors": ["#2C1810", "#D4AF37"],
    "accent_colors": ["#FFFFFF"],
    "scheme": "Warm, luxurious, monochromatic with gold accents"
  },
  "style_aesthetic": {
    "visual_style": "Abstract, minimalist luxury",
    "mood": "Elegant, sophisticated, aspirational",
    "composition": "Centered, balanced, clean"
  }
}
```

### Scene Prompt Example (Scene 1: Discovery)
```python
ScenePromptSet(
    scene_number=1,
    scene_type="Discovery",
    start_frame_prompt="Abstract composition with soft golden light (#D4AF37) filtering through mysterious shadows, elegant minimalist aesthetic, rectangular shapes subtly suggesting a luxury product, warm monochromatic palette with deep brown (#2C1810) undertones, cinematic wide shot with shallow depth of field, anticipation building, Canon EOS R5 35mm lens, soft diffused lighting creating ethereal atmosphere",
    end_frame_prompt="The rectangular glass bottle with gold accents emerges from the abstract shadows, elegant minimalist luxury aesthetic, warm golden light (#D4AF37) highlighting the bottle's form, deep brown (#2C1810) background maintaining brand coherence, close-up portrait shot, Canon EOS R5 85mm f/1.2 lens, dramatic side lighting revealing product details, sophisticated and aspirational mood",
    motion_description="Camera slowly pushes in from abstract wide shot to product-focused close-up, golden light gradually reveals the bottle shape, shadows give way to clarity, anticipation transforms to recognition",
    product_visibility="partial"
)
```

## Error Handling

- **Image not found**: Raise FileNotFoundError with clear message
- **Vision API failure**: Raise RuntimeError - enhancement cannot proceed without visual elements
- **Enhancement failure for a scene**: Raise RuntimeError - fail fast, no fallback to generic prompts
- **Any enhancement error**: Raise RuntimeError with detailed error message - do not continue with generic fallbacks

## Configuration

### Environment Variables
- `OPENAI_API_KEY` (required, already exists)
- `STORYBOARD_ENHANCEMENT_MAX_ITERATIONS` (optional, default: 3)
- `STORYBOARD_ENHANCEMENT_SCORE_THRESHOLD` (optional, default: 85.0)

### Framework Hardcoding
- Sensory Journey framework is hardcoded in the service
- Scene types: ["Discovery", "Transformation", "Desire"] (for 3 scenes default)
- For configurable scene counts: Map scene numbers to framework positions (Scene 1 = Discovery, Scene 2 = Transformation, Scene 3+ = Desire variations)
- Can be extended later to support other frameworks

### CLI Integration
- `--num-clips N` parameter in `create_storyboard.py` CLI tool
- Default: 3 scenes
- Configurable: 3-5 scenes (validated in service)
- Passes `num_scenes` parameter to enhancement service

## Testing Considerations

1. **Unit Tests**: 
   - Visual element extraction parsing
   - Scene structure initialization
   - Prompt generation logic

2. **Integration Tests**:
   - Full enhancement flow with mock API calls
   - Error handling scenarios

3. **Manual Testing**:
   - Test with various perfume ad images
   - Verify visual coherence across scenes
   - Check progressive reveal logic

## Future Enhancements

- Support for other frameworks (Luxury Narrative, Problem-Solution)
- Configurable abstract style intensity
- Multi-image reference support
- Advanced motion description generation
- Scene transition optimization

