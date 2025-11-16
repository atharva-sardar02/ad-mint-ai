# Seed Control Technical Guide

**Date:** 2025-11-14  
**Purpose:** Explain how seed control works and its applicability across different video generation models

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

**How to Check:**
1. Check model documentation on Replicate
2. Inspect model schema: `replicate.models.get(model_name).latest.version.openapi_schema`
3. Test with explicit seed parameter

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

## Implementation for Current Codebase

### **Step 1: Add Seed Generation**

In the video generation pipeline, generate a seed once per video:

```python
# In video_generation.py or pipeline orchestrator
import random

def generate_video_seed(generation_id: str) -> int:
    """Generate a deterministic seed for a video generation."""
    # Option 1: Random seed (different each time)
    return random.randint(0, 2**31 - 1)
    
    # Option 2: Deterministic from generation_id (reproducible)
    # import hashlib
    # seed_hash = int(hashlib.md5(generation_id.encode()).hexdigest()[:8], 16)
    # return seed_hash % (2**31)
```

### **Step 2: Pass Seed to Generation Function**

Modify `generate_video_clip` to accept and use seed:

```python
async def generate_video_clip(
    scene: Scene,
    output_dir: str,
    generation_id: str,
    scene_number: int,
    seed: Optional[int] = None,  # Add seed parameter
    cancellation_check: Optional[callable] = None
) -> tuple[str, str]:
    # ... existing code ...
    
    # Prepare input parameters
    input_params = {
        "prompt": scene.visual_prompt,
        "duration": scene.duration,
        "aspect_ratio": "9:16",
    }
    
    # Add seed if provided and model supports it
    if seed is not None:
        input_params["seed"] = seed
    
    # ... rest of code ...
```

### **Step 3: Use Same Seed for All Scenes**

In the pipeline orchestrator:

```python
# Generate seed once per video
video_seed = generate_video_seed(generation_id)

# Use same seed for all scenes
for scene_number, scene in enumerate(scenes, start=1):
    clip_path, model_name = await generate_video_clip(
        scene=scene,
        output_dir=output_dir,
        generation_id=generation_id,
        scene_number=scene_number,
        seed=video_seed,  # Same seed for all scenes
        cancellation_check=cancellation_check
    )
```

### **Step 4: Store Seed in Database**

Add seed to Generation model:

```python
# In generation.py model
class Generation(Base):
    # ... existing fields ...
    seed = Column(Integer, nullable=True)  # Store seed for reproducibility
```

### **Step 5: Handle Model-Specific Seed Parameters**

Create a helper function to get model-specific seed parameter:

```python
def get_model_seed_param(model_name: str, seed: int) -> dict:
    """Get seed parameter in format expected by model."""
    # Default: most models use "seed"
    param_name = "seed"
    
    # Model-specific overrides (add as discovered)
    model_seed_params = {
        "klingai/kling-video": "random_seed",  # Example if different
        # Add more as needed
    }
    
    param_name = model_seed_params.get(model_name, "seed")
    return {param_name: seed}
```

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

