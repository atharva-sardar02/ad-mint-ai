# Sequential Image Generation: Visual Reference Chain

## YES, We Provide Previously Generated Images as Visual References! ✅

## How It Works

### The Sequential Chain

```
Reference Images (for each scene):
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Scene 1 Reference      Scene 2 Reference      Scene 3 Reference│
│       Image                 Image                  Image        │
│         │                     │                      │          │
│         │   ┌─────────────┐   │   ┌──────────────┐  │          │
│         └──>│ PASS AS REF │───┴──>│  PASS AS REF │──┴─>...     │
│             │   IMAGE     │       │    IMAGE     │              │
│             └─────────────┘       └──────────────┘              │
│                                                                 │
│  Image 1 → Image 2 → Image 3 (Each uses previous as reference) │
└─────────────────────────────────────────────────────────────────┘
```

### Detailed Flow

**For Reference Images:**

**If user provides a reference image:**
```
Step 1: Use User's Reference Image (Scene 1)
  - Input: User-provided image (copied directly)
  - Visual Reference: NONE (user's original image)
  - Output: scene_1_reference.png (user's image)
  - Subject: User's image (woman, product, etc.)

Step 2: Generate Scene 2 Reference Image
  - Input: Text prompt (with character/product description)
  - Visual Reference: scene_1_reference.png ⬅️ USER'S IMAGE
  - Output: scene_2_reference.png
  - Subject: Consistent with user's image (model sees both text + user's image)
```

**If no user image provided:**
```
Step 1: Generate Scene 1 Reference Image
  - Input: Text prompt (with character description)
  - Visual Reference: NONE (first image)
  - Output: scene_1_reference.png
  - Subject: Woman with chestnut hair, emerald eyes, beauty mark

Step 2: Generate Scene 2 Reference Image
  - Input: Text prompt (with SAME character description)
  - Visual Reference: scene_1_reference.png ⬅️ PREVIOUS IMAGE
  - Output: scene_2_reference.png
  - Subject: SAME woman (model sees both text + previous image)

Step 3: Generate Scene 3 Reference Image
  - Input: Text prompt (with SAME character description)
  - Visual Reference: scene_2_reference.png ⬅️ PREVIOUS IMAGE
  - Output: scene_3_reference.png
  - Subject: SAME woman (model sees both text + previous image)

Step 4: Generate Scene 4 Reference Image
  - Input: Text prompt (with SAME character description)
  - Visual Reference: scene_3_reference.png ⬅️ PREVIOUS IMAGE
  - Output: scene_4_reference.png
  - Subject: SAME woman (model sees both text + previous image)
```

### Code Implementation

From `backend/app/services/pipeline/image_generation_batch.py`:

```python
async def generate_images_with_sequential_references(
    prompts: List[str],
    initial_reference_image: Optional[str] = None,
    ...
) -> List[str]:
    """
    Generate multiple images sequentially, using each previous image as reference.
    """
    image_paths = []
    previous_image_path = initial_reference_image  # Start with initial reference
    
    for idx, prompt in enumerate(prompts, start=1):
        # Use previous image as visual reference
        reference_to_use = previous_image_path
        
        # Generate new image with:
        # 1. Text prompt (with detailed subject description)
        # 2. Previous image as VISUAL REFERENCE ⬅️ THIS IS KEY
        image_path = await generate_image(
            prompt=enhanced_prompt,
            reference_image_path=reference_to_use,  # ⬅️ PREVIOUS IMAGE
            ...
        )
        
        image_paths.append(image_path)
        # Use this newly generated image as reference for NEXT iteration
        previous_image_path = image_path  # ⬅️ CHAIN CONTINUES
```

## Why This Matters

### Two Mechanisms Working Together

**1. Text Prompt (Detailed Description):**
```
"Woman, 32 years old, 5'6" tall, medium build, chestnut brown hair, emerald green eyes, 
small beauty mark near left eye..."
```

**2. Visual Reference (Previous Image):**
```
[Actual pixel data of the woman from Scene 1]
```

### Image Generation Model Receives BOTH:

```
┌────────────────────────────────────────────────┐
│  Image Generation Model (Nano Banana)          │
│                                                 │
│  Inputs:                                        │
│  1. Text: "Woman, 32, chestnut hair, emerald   │
│     eyes, beauty mark..."                       │
│                                                 │
│  2. Visual Reference: [Scene 1 image showing   │
│     the actual woman]                           │
│                                                 │
│  Output: New image that combines:              │
│  - Same woman (from visual reference)           │
│  - New context (from text: different pose,     │
│    lighting, action)                            │
└────────────────────────────────────────────────┘
```

## The Problem We Fixed

### Before Fix (Why Different Women Appeared):

**Text was TOO GENERIC:**
```
Text: "woman in her 30s wearing ivory blouse"
Visual Reference: [Image of specific woman]

Result: Model prioritized TEXT over visual reference
→ "woman in her 30s" could be ANYONE
→ Generated a different woman matching the generic text
```

**The text was OVERRIDING the visual reference!**

### After Fix (Why Same Woman Should Appear):

**Text is NOW DETAILED:**
```
Text: "Woman, 32, 5'6", chestnut hair, emerald eyes, beauty mark near left eye..."
Visual Reference: [Image of specific woman with chestnut hair, emerald eyes, beauty mark]

Result: Model sees BOTH text and visual reference AGREE
→ "chestnut hair, emerald eyes, beauty mark" = SPECIFIC person
→ Text reinforces what visual reference shows
→ Generates SAME woman with consistent features
```

**Now text REINFORCES the visual reference!**

## Visual Example

### Scene 1 → Scene 2 Chain:

```
┌─────────────────────────────────────┐
│  Scene 1 Reference Image            │
│  (First Generation - No Reference)  │
│                                     │
│  Input:                             │
│  - Text: "Woman, 32, chestnut hair, │
│    emerald eyes, beauty mark..."    │
│  - Visual Reference: NONE           │
│                                     │
│  Output:                            │
│  🧍‍♀️ Woman with chestnut hair,       │
│     emerald eyes, beauty mark       │
│                                     │
│  Saved as: scene_1_reference.png    │
└─────────────────────────────────────┘
              │
              │ PASS AS VISUAL REFERENCE
              ▼
┌─────────────────────────────────────┐
│  Scene 2 Reference Image            │
│  (Uses Scene 1 as Reference)        │
│                                     │
│  Input:                             │
│  - Text: "The EXACT SAME woman      │
│    from Scene 1 (32, chestnut hair, │
│    emerald eyes, beauty mark)..."   │
│  - Visual Reference:                │
│    scene_1_reference.png ⬅️         │
│    [Shows the woman]                │
│                                     │
│  Output:                            │
│  🧍‍♀️ SAME woman with chestnut hair, │
│     emerald eyes, beauty mark       │
│     (in different pose/context)     │
│                                     │
│  Saved as: scene_2_reference.png    │
└─────────────────────────────────────┘
              │
              │ PASS AS VISUAL REFERENCE
              ▼
           Scene 3...
```

## Complete Flow for Your Perfume + Woman Scenario

### Reference Images (Main Subject Images):

```
Scene 1: Bottle only
  └─> Generate: bottle on vanity
      Input: Detailed bottle text + NO reference
      Output: scene_1_reference.png (bottle)

Scene 2: Woman + Bottle
  └─> Generate: woman holding bottle
      Input: Detailed woman text + Detailed bottle text + scene_1_reference.png
      Output: scene_2_reference.png (woman + bottle)

Scene 3: Woman + Bottle
  └─> Generate: woman spraying bottle
      Input: SAME woman text + SAME bottle text + scene_2_reference.png ⬅️
      Output: scene_3_reference.png (SAME woman + SAME bottle)

Scene 4: Woman + Bottle
  └─> Generate: woman experiencing fragrance
      Input: SAME woman text + SAME bottle text + scene_3_reference.png ⬅️
      Output: scene_4_reference.png (SAME woman + SAME bottle)
```

### Start Images (First Frame of Video):

```
All 4 Start Images Generated in ONE Sequential Batch:

Start Image 1 (for Scene 1 video)
  └─> Input: Text + scene_1_reference.png as base
      Output: start_1.png

Start Image 2 (for Scene 2 video)
  └─> Input: Text + start_1.png as reference ⬅️
      Output: start_2.png

Start Image 3 (for Scene 3 video)
  └─> Input: Text + start_2.png as reference ⬅️
      Output: start_3.png

Start Image 4 (for Scene 4 video)
  └─> Input: Text + start_3.png as reference ⬅️
      Output: start_4.png
```

### End Images (Last Frame of Video):

```
All 4 End Images Generated in ONE Sequential Batch:

End Image 1 (for Scene 1 video)
  └─> Input: Text + scene_1_reference.png as base
      Output: end_1.png

End Image 2 (for Scene 2 video)
  └─> Input: Text + end_1.png as reference ⬅️
      Output: end_2.png

End Image 3 (for Scene 3 video)
  └─> Input: Text + end_2.png as reference ⬅️
      Output: end_3.png

End Image 4 (for Scene 4 video)
  └─> Input: Text + end_3.png as reference ⬅️
      Output: end_4.png
```

## Key Insight

**The sequential visual reference chain IS working correctly!**

The problem was NOT the chain itself. The problem was that:

1. **Generic text** ("woman in her 30s") was OVERRIDING the visual reference
2. Image model saw: vague text + specific visual → chose to follow vague text → new random woman

Now with the fix:

1. **Detailed text** ("Woman, 32, chestnut hair, emerald eyes, beauty mark") REINFORCES the visual reference
2. Image model sees: detailed text + specific visual → both AGREE → SAME woman

## Summary

**Q: Are we providing the first woman's image to generate the second woman's image?**

**A: YES! ✅**

- ✅ Scene 2 woman image receives Scene 1 woman image as visual reference
- ✅ Scene 3 woman image receives Scene 2 woman image as visual reference  
- ✅ Scene 4 woman image receives Scene 3 woman image as visual reference

**The chain is working. The fix we made ensures the TEXT matches the VISUAL so they work together instead of conflicting.**

Before: Text ❌ Visual Reference → Different women  
After: Text ✅ Visual Reference → Same woman

