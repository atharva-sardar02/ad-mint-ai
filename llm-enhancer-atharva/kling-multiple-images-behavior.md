# Kling Multiple Images Behavior & Fix

## The Issue
When providing `start_image`, `end_image`, AND `image` (reference) to Kling 2.5 Turbo Pro simultaneously, the model sometimes ignores the `end_image` constraint. This results in videos that start correctly but end on a random frame instead of the specified end image.

## The Fix (Applied Nov 18, 2025)
We modified `backend/app/services/pipeline/video_generation.py` to implement a priority system:

1. **If BOTH `start_image` and `end_image` are present:**
   - Send `start_image` ✅
   - Send `end_image` ✅
   - **SKIP** `reference_image` ❌
   - *Reasoning*: The start and end images already provide sufficient visual context (character, style, setting) for the model. Adding a third image confuses the model's frame control logic.

2. **If ONLY `start_image` is present:**
   - Send `start_image` ✅
   - Send `reference_image` ✅
   - *Reasoning*: We need the reference image to guide the style/character for the rest of the video since the end is open.

3. **If ONLY `end_image` is present:**
   - Send `end_image` ✅
   - Send `reference_image` ✅
   - *Reasoning*: We need the reference image to guide the start/middle of the video.

4. **If NEITHER start/end are present:**
   - Send `reference_image` ✅
   - *Reasoning*: This is the standard image-to-video generation mode.

## Verification
Logs will now show:
```
ℹ️ Skipping reference image for Kling because BOTH start and end images are provided (ensures end_image is respected)
```
or
```
ℹ️ Reference image available but skipped to prioritize start/end frame control: ...
```

This ensures precise control over both the first and last frames of the generated video clips.
