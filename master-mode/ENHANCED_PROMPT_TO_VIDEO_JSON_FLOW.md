# Enhanced Prompt to Video Model - Complete JSON Flow

**Verification**: Scene Enhancer output → Veo 3.1 API

## Complete Data Flow

### Step 1: Scene Enhancer Output
```python
# scene_enhancer.py
enhanced_content = "Shot on Arri Alexa 65 with Zeiss Master Prime 50mm f/1.4 lens at eye-level 5'8\" height, a handsome man in his early 30s with short dark brown hair, precisely groomed stubble at 3-day growth, natural skin texture with visible pores and subtle shine on cheekbones, stands confidently in a contemporary minimalist loft space. Large floor-to-ceiling windows spanning 12 feet wide allow soft north-facing natural light at 5600K color temperature to flood the space from camera left at 45-degree angle, creating a 3:1 lighting ratio with gentle wrap-around fill from white interior walls reducing shadows to -2 stops below key..."
# [300-500 words total]

scene["enhanced_content"] = enhanced_content
```

### Step 2: Scene-to-Video Builds JSON Parameters
```python
# scene_to_video.py - lines 119-132
prompt_content = scene["enhanced_content"]  # ← Enhanced 300-500 word prompt

veo_params = {
    "scene_number": 1,
    "prompt": prompt_content,  # ← ENHANCED PROMPT HERE
    "negative_prompt": "blurry, low quality, distorted...",
    "duration": 8,
    "aspect_ratio": "16:9",
    "resolution": "1080p",
    "generate_audio": True,
    "reference_images": ["path/to/img1.jpg", "path/to/img2.jpg"],
    "seed": None,
    "metadata": {...}
}

# This veo_params dict is returned to the caller
return [veo_params]  # List of params for all scenes
```

### Step 3: Video Generation Extracts from JSON
```python
# video_generation.py - lines 43-70
prompt = scene_params["prompt"]  # ← Extract ENHANCED prompt from JSON
duration = scene_params["duration"]
resolution = scene_params.get("resolution", "1080p")
reference_images = scene_params.get("reference_images")
# ... other params

# Pass to video generation function
result = await generate_video_clip_with_model(
    prompt=prompt,  # ← ENHANCED prompt passed here
    duration=duration,
    resolution=resolution,
    reference_images=reference_images,
    # ... other params
)
```

### Step 4: Build Replicate API JSON
```python
# video_generation.py (pipeline) - lines 436, 553-558

# Enhance prompt with consistency markers
enhanced_prompt = _enhance_prompt_with_markers(prompt, consistency_markers)
# Note: This adds consistency markers, but the base prompt is already enhanced!

# For Veo 3.1 with reference images (R2V mode)
input_params = {
    "prompt": enhanced_prompt,  # ← 300-500 word enhanced prompt!
    "duration": 8,
    "aspect_ratio": "16:9",
    "reference_images": [file_handle1, file_handle2],
}

# This JSON is sent to Replicate API
output = await client.run(
    "google/veo-3.1",
    input=input_params  # ← Enhanced prompt in JSON sent to Veo 3.1!
)
```

### Step 5: Veo 3.1 API Receives JSON
```json
{
  "prompt": "Shot on Arri Alexa 65 with Zeiss Master Prime 50mm f/1.4 lens at eye-level 5'8\" height, a handsome man in his early 30s with short dark brown hair, precisely groomed stubble at 3-day growth, natural skin texture with visible pores and subtle shine on cheekbones, stands confidently in a contemporary minimalist loft space. Large floor-to-ceiling windows spanning 12 feet wide allow soft north-facing natural light at 5600K color temperature to flood the space from camera left at 45-degree angle, creating a 3:1 lighting ratio with gentle wrap-around fill from white interior walls reducing shadows to -2 stops below key. The man wears a charcoal gray merino wool sweater with natural fabric texture visible, slight wrinkle formations at the elbow creases showing authentic material physics, the weave catching micro-highlights from the window light. In his right hand, positioned precisely at mid-chest height 14 inches from his sternum, he holds an elegant perfume bottle - crystal glass with 95% light transmission showing amber-toned fragrance inside, the surface reflecting environment with mirror-accurate physics, subtle fingerprint marks on glass adding photorealistic authenticity. The camera executes a slow dolly-in movement at exactly 0.5 feet per second over the full 6-second duration, gliding from a medium shot showing 60% of the figure at f/1.4 shallow depth of field to a tighter medium-close composition at 75% frame fill, with the background concrete softly blurring into creamy bokeh with smooth circular aperture characteristics. Natural micro-movements include subtle weight shift from left to right foot at 2.3 seconds, barely perceptible chest rise from natural breathing creating authentic life, and a slow deliberate 3-degree head tilt toward camera occurring from 4.0 to 5.2 seconds with realistic neck muscle tension and natural joint articulation. The color palette maintains cinematic desaturation at -10% for skin tones preserving natural authenticity, while the perfume bottle amber liquid shows rich warm saturation at 115% drawing visual focus, all balanced within an analogous color harmony of warm amber highlights (3200K), cool slate blue shadows (6500K), and neutral gray midtones creating aspirational luxury mood with professional commercial photography aesthetic throughout.",
  "duration": 8,
  "aspect_ratio": "16:9",
  "reference_images": [<binary_file_1>, <binary_file_2>],
  "resolution": "1080p",
  "generate_audio": true
}
```

## Verification in Logs

Your logs will show:

```
[Scene Enhancer] Scene 1: Enhanced successfully! 245 chars → 1847 chars (412 words)
[Scene→Video] Scene 1: Using enhanced prompt (1847 chars)
[Video Gen] Scene 1: Duration=8s, Resolution=1080p, R2V=Yes
[Video Gen] Scene 1: Prompt length: 1847 characters (412 words)  ← NEW LOG!
[Video Gen] Scene 1: Using 2 reference images for ultra-realistic R2V mode
```

The "Prompt length: 1847 characters (412 words)" confirms the enhanced prompt is being used!

## JSON Structure at Each Stage

### Stage 1: scene_enhancer.py Output
```python
{
  "scene_number": 1,
  "content": "Original 150-250 word scene",
  "enhanced_content": "Enhanced 300-500 word scene"  # ← NEW!
}
```

### Stage 2: scene_to_video.py Output
```python
{
  "scene_number": 1,
  "prompt": "Enhanced 300-500 word scene",  # ← From enhanced_content
  "negative_prompt": "...",
  "duration": 8,
  "aspect_ratio": "16:9",
  "resolution": "1080p",
  "generate_audio": True,
  "reference_images": ["img1.jpg", "img2.jpg"],
  "metadata": {...}
}
```

### Stage 3: video_generation.py Passes to API
```python
{
  "prompt": "Enhanced 300-500 word scene",  # ← Same enhanced prompt
  "duration": 8,
  "aspect_ratio": "16:9",
  "reference_images": [<file_handle_1>, <file_handle_2>]
}
```

### Stage 4: Replicate/Veo 3.1 Receives
```json
{
  "prompt": "Enhanced 300-500 word scene",
  "duration": 8,
  "aspect_ratio": "16:9",
  "reference_images": [<binary_data_1>, <binary_data_2>]
}
```

## Summary

✅ **Enhanced prompt flows correctly through the entire pipeline:**

1. Scene Enhancer expands 150-250 words → 300-500 words
2. `scene_to_video.py` puts enhanced prompt in `veo_params["prompt"]`
3. `video_generation.py` extracts `scene_params["prompt"]`
4. Pipeline builds Replicate JSON with `input_params["prompt"]`
5. Veo 3.1 receives enhanced 300-500 word prompt in JSON

**The enhanced prompt IS part of the JSON sent to the video model!** ✨


