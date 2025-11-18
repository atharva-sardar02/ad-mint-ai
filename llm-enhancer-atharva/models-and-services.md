# Models and Services

## LLM Services

### Storyboard Planner
- **Service**: `backend/app/services/pipeline/storyboard_planner.py`
- **Model**: GPT-4o (OpenAI)
- **Purpose**: Create detailed storyboard with rich prompts for each scene
- **Input**: User prompt + optional reference image
- **Output**: JSON with detailed prompts, consistency markers, scene descriptions
- **Key Features**:
  - Vision API support (if reference image provided)
  - Generates 40-80 word detailed prompts
  - Creates consistency markers
  - Follows AIDA framework

### Prompt Generator (Legacy/Alternative)
- **Service**: `backend/app/services/pipeline/prompt_generator.py`
- **Model**: GPT-4o (OpenAI)
- **Purpose**: Generate prompts with consistency markers (alternative to storyboard planner)
- **Functions**:
  - `generate_prompt_with_markers()` - Single prompt + markers
  - `generate_scene_prompts_with_markers()` - Multiple scene prompts with shared markers

## Image Generation

### Nano Banana
- **Service**: `backend/app/services/pipeline/image_generation.py`
- **Model**: `google/nano-banana` (Replicate)
- **Purpose**: Generate reference images for video generation
- **Key Features**:
  - Character and style consistency
  - Reference image support (for sequential consistency)
  - Aspect ratio: 9:16 (vertical for mobile ads)
  - Cost: ~$0.01 per image

**API Parameters**:
- `prompt`: Enhanced prompt with consistency markers
- `reference_image`: Previous image (for images 2-4)
- `aspect_ratio`: "9:16"
- `num_outputs`: 1

**Batch Generation**:
- **Service**: `backend/app/services/pipeline/image_generation_batch.py`
- **Function**: `generate_images_with_sequential_references()`
- **Purpose**: Generate multiple images sequentially, each using previous as reference
- **Kling 2.5 Turbo Pro Support**: 
  - Generates reference images (one per scene)
  - Generates start images (first frame per scene) in `output/temp/images/{generation_id}/start/`
  - Generates end images (last frame per scene) in `output/temp/images/{generation_id}/end/`
  - All images use sequential references for consistency

## Video Generation

### Supported Models (via Replicate)

#### Sora-2 (OpenAI)
- **Model**: `openai/sora-2`
- **Default**: Yes (recommended)
- **Features**:
  - State-of-the-art realism
  - Exceptional physics
  - Multi-shot continuity
  - Synchronized audio
- **Parameters**:
  - `prompt`: Enhanced detailed prompt
  - `duration`: 4 seconds (per scene)
  - `aspect_ratio`: "portrait"
  - `quality`: "high"
  - `input_reference`: Generated reference image
- **Cost**: ~$0.10 per second

#### Veo-3 (Google)
- **Model**: `google/veo-3`
- **Features**:
  - Top-tier cinematic quality
  - Stunning HD visuals
  - Native audio generation
  - Lip-synced dialogue
- **Parameters**:
  - `prompt`: Enhanced detailed prompt
  - `duration`: 4, 6, or 8 seconds (rounded)
  - `aspect_ratio`: "9:16"
- **Cost**: ~$0.12 per second

#### PixVerse V5
- **Model**: `pixverse/pixverse-v5`
- **Features**:
  - Balanced quality & cost
  - Good for faster generation
- **Parameters**:
  - `prompt`: Enhanced detailed prompt
  - `duration`: 4 seconds
  - `aspect_ratio`: "9:16"
  - `quality`: "1080p"
- **Cost**: ~$0.06 per second

#### Kling 2.5 Turbo Pro
- **Model**: `kwaivgi/kling-v2.5-turbo-pro` (Replicate)
- **Features**:
  - Fast cinematic generation
  - Excellent camera control
  - Physics-aware motion
  - **Supports reference, start, and end images simultaneously**
- **Parameters**:
  - `prompt`: Enhanced detailed prompt
  - `image`: Reference image (main scene representation)
  - `start_image`: First frame of video (optional)
  - `end_image`: Last frame of video (optional)
- **Cost**: ~$0.07 per second
- **Special Feature**: When using Kling 2.5 Turbo Pro, the system generates:
  - Reference images (one per scene)
  - Start images (first frame per scene)
  - End images (last frame per scene)
  - All three are passed to the model for precise video control

## Service Architecture

```
┌─────────────────────────────────────┐
│  Storyboard Planner (GPT-4o)        │
│  - Plans detailed storyboard        │
│  - Generates consistency markers    │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Image Generation (Nano Banana)     │
│  - Sequential generation            │
│  - Reference image chain            │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Video Generation (Sora-2/Veo-3/etc)  │
│  - Parallel generation               │
│  - Uses generated reference images   │
└─────────────────────────────────────┘
```

## API Keys Required

- **OpenAI API Key**: For GPT-4o (storyboard planning)
- **Replicate API Token**: For Nano Banana (images) and video models

## Cost Estimates

Per 16-second video (4 scenes):
- Storyboard Planning: ~$0.01-0.02 (GPT-4o)
- Image Generation: ~$0.04 (4 images × $0.01)
- Video Generation: ~$1.60-2.40 (16 seconds × $0.10-0.15)
- **Total**: ~$1.65-2.46 per video

