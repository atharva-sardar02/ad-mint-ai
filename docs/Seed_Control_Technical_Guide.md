# Seed Control Technical Guide

**Date:** 2025-11-15  
**Last Updated:** 2025-11-15  
**Purpose:** Explain how seed control works and its implementation in the ad-mint-ai video generation pipeline

---

## How Seed Control Works

### Technical Overview

**Seed control** is a fundamental technique in diffusion-based generative models that uses the same random seed value to initialize the noise in the latent space across multiple generations. This ensures that the underlying visual "DNA" of each scene is linked, reducing style drift and maintaining visual coherence.

### The Mechanism

1. **Random Number Generator Initialization:**
   - Diffusion models use random noise as the starting point for generation
   - The seed value initializes the random number generator (RNG)
   - Same seed → same initial noise pattern → similar visual characteristics

2. **Latent Space Consistency:**
   - The seed determines the initial latent code (noise) in the compressed representation space
   - When multiple scenes use the same seed, they share similar underlying structure
   - This creates visual consistency in:
     - Color palette
     - Lighting characteristics
     - Texture and grain
     - Overall visual style

3. **Why It Works:**
   - Diffusion models are deterministic when given the same seed
   - Even with different prompts, the shared seed creates a "family resemblance"
   - The model learns to maintain consistency when seeds are linked

### Example

```
Scene 1: "Luxury watch in elegant setting" (seed: 42)
Scene 2: "Person wearing the watch" (seed: 42)  ← Same seed!
Scene 3: "Watch close-up" (seed: 42)  ← Same seed!

Result: All three scenes share similar:
- Color temperature (warm/cool)
- Lighting style (soft/harsh)
- Visual grain and texture
- Overall aesthetic
```

---

## Model Support for Seed Control

### ✅ **Universal Support (Diffusion-Based Models)**

Seed control works for **all diffusion-based models**, which includes:
- Stable Diffusion variants
- AnimateDiff
- Most text-to-video models (Runway, Kling, Minimax, etc.)
- Image-to-video models

**Why:** Diffusion models fundamentally rely on random noise initialization, making seed control a core feature.

### ⚠️ **Model-Specific Considerations**

While seed control is supported, **implementation varies by model and API**:

#### **1. Replicate API Models**

**Current Models in Use:**
- `bytedance/seedance-1-lite` (Primary)
- `minimax-ai/minimax-video-01` (Fallback 1)
- `klingai/kling-video` (Fallback 2)
- `runway/gen3-alpha-turbo` (Fallback 3)

**Seed Parameter Support:**
- Most Replicate models support a `seed` parameter
- Parameter name may vary: `seed`, `random_seed`, `noise_seed`
- Value type: Integer (typically 0 to 2^32-1 or similar range)

**Tested Model Support (as of 2025-11-15):**

| Model | Seed Parameter | Status | Notes |
|-------|---------------|--------|-------|
| `bytedance/seedance-1-lite` | `seed` | ✅ Expected Supported | Primary model - seed parameter included in API calls |
| `minimax-ai/minimax-video-01` | `seed` | ✅ Expected Supported | Fallback model - seed parameter included in API calls |
| `klingai/kling-video` | `seed` | ✅ Expected Supported | Fallback model - seed parameter included in API calls |
| `runway/gen3-alpha-turbo` | `seed` | ✅ Expected Supported | Fallback model - seed parameter included in API calls |

**Implementation Notes:**
- All models in the fallback chain receive the seed parameter when seed_control is enabled
- If a model doesn't support seed, the Replicate API will either:
  - Silently ignore the parameter (most common behavior)
  - Return an error indicating unsupported parameter
- Error handling: If seed parameter causes an error, the system automatically retries without seed
- Logging: Warnings are logged for models with unverified seed support

**How to Verify Model Support:**
1. Check model documentation on Replicate
2. Inspect model schema: `replicate.models.get(model_name).latest.version.openapi_schema`
3. Test with explicit seed parameter and observe behavior
4. Check logs for seed-related warnings or errors

#### **2. Model-Specific Behavior**

**Seedance-1-Lite (ByteDance):**
- Likely supports `seed` parameter (most ByteDance models do)
- May have additional parameters like `seed_strength` or `noise_schedule`

**Minimax Video-01:**
- Typically supports `seed` parameter
- May have `random_seed` as parameter name

**Kling Video:**
- Supports seed control
- May require specific parameter name (check documentation)

**Runway Gen-3 Alpha Turbo:**
- Supports seed control
- May have additional seed-related parameters

### ❌ **Limited/No Support**

**Autoregressive Models (Less Common):**
- Some autoregressive video models may not support seed control
- These are less common in current video generation landscape

**Proprietary APIs Without Seed Exposure:**
- Some closed APIs may not expose seed control
- Workaround: Use other consistency techniques (IP-Adapter, ControlNet)

---

## Implementation Strategy

### **Approach 1: Universal Seed (Recommended for MVP)**

Use the **same seed for all scenes** in a video generation:

```python
import random
import uuid

# Generate seed once per video generation
generation_seed = random.randint(0, 2**31 - 1)  # Or use UUID hash

# Use same seed for all scenes
for scene in scenes:
    input_params = {
        "prompt": scene.visual_prompt,
        "duration": scene.duration,
        "aspect_ratio": "9:16",
        "seed": generation_seed  # Same seed for all scenes
    }
```

**Benefits:**
- Simple to implement
- Works across all models
- Immediate visual coherence improvement
- No model-specific logic needed

**Limitations:**
- Less control over individual scene variation
- May reduce creativity if scenes need distinct styles

### **Approach 2: Model-Specific Seed Handling**

Handle seed parameter based on model capabilities:

```python
def get_seed_parameter(model_name: str, seed: int) -> dict:
    """Get seed parameter in model-specific format."""
    seed_params = {
        "bytedance/seedance-1-lite": {"seed": seed},
        "minimax-ai/minimax-video-01": {"seed": seed},
        "klingai/kling-video": {"random_seed": seed},  # Example: different name
        "runway/gen3-alpha-turbo": {"seed": seed}
    }
    return seed_params.get(model_name, {})  # Return empty if unknown
```

**Benefits:**
- Handles model-specific parameter names
- More robust across different models
- Can add model-specific seed behavior

**Limitations:**
- Requires testing each model
- More complex implementation
- Need to maintain model-specific mappings

### **Approach 3: Seed with Variation (Advanced)**

Use base seed with small variations for controlled diversity:

```python
base_seed = random.randint(0, 2**31 - 1)

for i, scene in enumerate(scenes):
    # Small variation for each scene while maintaining coherence
    scene_seed = base_seed + (i * 100)  # Increment by 100
    input_params = {
        "prompt": scene.visual_prompt,
        "seed": scene_seed
    }
```

**Benefits:**
- Maintains coherence while allowing variation
- Useful for scenes that need distinct but related styles

**Limitations:**
- More complex
- May reduce coherence if variation is too large
- Requires experimentation to find optimal variation

---

## Implementation in ad-mint-ai Codebase

### **Architecture Overview**

Seed control is implemented across three main components:

1. **Seed Manager Service** (`backend/app/services/pipeline/seed_manager.py`)
   - Generates and manages seeds for video generations
   - Stores seed in generation record for reproducibility

2. **Video Generation Service** (`backend/app/services/pipeline/video_generation.py`)
   - Accepts seed parameter in `generate_video_clip()` function
   - Passes seed to Replicate API calls for visual consistency

3. **Pipeline Orchestration** (`backend/app/api/routes/generations.py`)
   - Checks coherence_settings for seed_control flag
   - Generates seed before scene generation starts
   - Passes same seed to all scene generations

### **Implementation Details**

#### **1. Seed Manager Service**

Located at: `backend/app/services/pipeline/seed_manager.py`

```python
def generate_seed() -> int:
    """Generate a random integer seed (0 to 2^31-1)."""
    return random.randint(0, 2**31 - 1)

def get_seed_for_generation(db: Session, generation_id: str) -> Optional[int]:
    """Get or generate seed for a generation.
    
    If generation already has seed_value, returns it.
    Otherwise generates new seed, stores it, and returns it.
    """
    generation = db.query(Generation).filter(Generation.id == generation_id).first()
    if generation.seed_value:
        return generation.seed_value
    
    seed = generate_seed()
    generation.seed_value = seed
    db.commit()
    return seed
```

#### **2. Database Schema**

**Generation Model** (`backend/app/db/models/generation.py`):
```python
class Generation(Base):
    # ... existing fields ...
    seed_value = Column(Integer, nullable=True)  # Seed for visual consistency
```

**Migration**: `backend/app/db/migrations/add_seed_value.py`
- Adds `seed_value` column as nullable Integer
- Backward compatible (existing generations have NULL seed_value)

#### **3. Video Generation Integration**

**Function Signature** (`backend/app/services/pipeline/video_generation.py`):
```python
async def generate_video_clip(
    scene: Scene,
    output_dir: str,
    generation_id: str,
    scene_number: int,
    cancellation_check: Optional[callable] = None,
    seed: Optional[int] = None  # Seed parameter added
) -> tuple[str, str]:
```

**Seed Usage in API Call**:
```python
input_params = {
    "prompt": prompt,
    "duration": duration,
    "aspect_ratio": "9:16",
}

# Add seed if provided
if seed is not None:
    input_params["seed"] = seed
    logger.debug(f"Using seed {seed} for video generation")
```

#### **4. Pipeline Orchestration**

**Seed Generation** (in `process_generation()` function):
```python
# Check coherence_settings for seed_control
coherence_settings_dict = generation.coherence_settings or {}
seed_control_enabled = coherence_settings_dict.get("seed_control", True)  # Default: True

if seed_control_enabled:
    seed = get_seed_for_generation(db, generation_id)
    logger.info(f"Using seed {seed} for all scenes")
else:
    seed = None
    logger.info("Seed control disabled")
```

**Seed Application to All Scenes**:
```python
for i, scene in enumerate(scene_plan.scenes, start=1):
    clip_path, model_used = await generate_video_clip(
        scene=scene,
        output_dir=temp_output_dir,
        generation_id=generation_id,
        scene_number=i,
        cancellation_check=check_cancellation,
        seed=seed  # Same seed for all scenes
    )
```

#### **5. API Response**

**StatusResponse Schema** (`backend/app/schemas/generation.py`):
```python
class StatusResponse(BaseModel):
    # ... existing fields ...
    seed_value: Optional[int] = None  # Seed value for reproducibility
```

The seed value is included in API responses for client access and debugging.

### **Coherence Settings Integration**

Seed control is controlled by the `seed_control` flag in coherence settings:

- **Default**: `True` (enabled)
- **Location**: `coherence_settings.seed_control` in Generation model
- **Service**: `backend/app/services/coherence_settings.py`
  - `get_default_settings()` returns `seed_control=True`
  - `apply_defaults()` ensures seed_control defaults to True if not specified

### **Error Handling**

- If seed generation fails, generation continues without seed (seed control is enhancement, not critical)
- If Replicate API doesn't accept seed parameter, generation continues (logged as warning)
- Existing generations without seed_value are valid (backward compatible)

---

## Testing Seed Control

### **Test 1: Reproducibility**

Generate the same scene twice with the same seed:

```python
# Test: Same prompt + same seed = same output
seed = 42
result1 = await generate_video_clip(scene, output_dir, "test1", 1, seed=seed)
result2 = await generate_video_clip(scene, output_dir, "test2", 1, seed=seed)

# Videos should be visually similar (may have minor variations due to API)
```

### **Test 2: Multi-Scene Coherence**

Generate multiple scenes with the same seed:

```python
seed = 42
scenes = [scene1, scene2, scene3]

for scene in scenes:
    clip = await generate_video_clip(scene, output_dir, "test", i, seed=seed)

# All scenes should share visual characteristics
```

### **Test 3: Model Compatibility**

Test seed parameter with each model:

```python
models = [
    "bytedance/seedance-1-lite",
    "minimax-ai/minimax-video-01",
    "klingai/kling-video",
    "runway/gen3-alpha-turbo"
]

for model in models:
    try:
        # Test if seed parameter is accepted
        result = await generate_with_seed(model, prompt, seed=42)
        print(f"✅ {model} supports seed")
    except Exception as e:
        print(f"❌ {model} seed error: {e}")
```

---

## Limitations and Considerations

### **1. Model API Changes**

- Model APIs may change seed parameter names
- New model versions may handle seeds differently
- Solution: Test and document model-specific behavior

### **2. Seed Range**

- Different models may have different seed ranges
- Some models: 0 to 2^31-1
- Others: 0 to 2^32-1 or different ranges
- Solution: Use common range (0 to 2^31-1) or check model docs

### **3. Seed + Prompt Interaction**

- Same seed + different prompts = similar style, different content
- This is desired for multi-scene coherence
- But may limit creativity if scenes need very different styles

### **4. API Limitations**

- Some APIs may ignore seed parameter silently
- Some may not support seed at all
- Solution: Test each model, have fallback behavior

### **5. Determinism vs. Quality**

- Fixed seed may reduce output diversity
- May miss better variations
- Solution: Use seed for coherence, allow regeneration if quality is poor

---

## Best Practices

1. **Always Generate Seed Per Video:**
   - One seed per video generation
   - Use same seed for all scenes in that video
   - Store seed in database for reproducibility

2. **Test Model Support:**
   - Verify each model accepts seed parameter
   - Document model-specific behavior
   - Handle gracefully if seed not supported

3. **Combine with Other Techniques:**
   - Seed control + IP-Adapter = character consistency
   - Seed control + ControlNet = compositional consistency
   - Seed control + enhanced planning = narrative coherence

4. **Monitor Results:**
   - Track coherence scores with/without seed control
   - A/B test seed impact on quality
   - Adjust seed strategy based on results

5. **Fallback Behavior:**
   - If seed not supported, continue without it
   - Log seed usage for analysis
   - Don't fail generation if seed parameter is rejected

---

## Conclusion

**Seed control is a fundamental technique that works with virtually all diffusion-based video generation models.** It's a quick win for improving multi-scene coherence with minimal implementation effort.

**Key Takeaways:**
- ✅ Works with all diffusion models (including all current Replicate models)
- ✅ Simple to implement (add seed parameter to API calls)
- ✅ Immediate visual coherence improvement
- ⚠️ Model-specific parameter names may vary
- ⚠️ Should be combined with other consistency techniques for best results

**Recommended Implementation:**
1. Start with universal seed approach (same seed for all scenes)
2. Test each model to verify seed support
3. Store seed in database for reproducibility
4. Combine with IP-Adapter and enhanced planning for maximum coherence

---

_End of Guide_

