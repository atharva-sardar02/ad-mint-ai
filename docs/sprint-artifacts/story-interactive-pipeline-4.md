# User Story 1.4: Advanced Image Editing

**Epic:** Interactive Video Generation Pipeline
**Story ID:** interactive-pipeline-4
**Status:** Draft
**Points:** 3
**Priority:** Medium

---

## User Story

**As a** content creator using the web application
**I want** to select specific regions in images and replace them with new content using AI inpainting
**So that** I can fix specific issues (wrong character, incorrect product, bad background) without regenerating the entire image, saving time and maintaining visual consistency

---

## Acceptance Criteria

**AC #1: Image Editor Access**
- GIVEN an image is displayed in ImageReview (from Story 3)
- WHEN the user clicks the "Edit" button on an image
- THEN an image editor modal/panel opens
- AND displays the image at editable size (max 2048x2048)
- AND shows editing tools (brush, eraser, clear)

**AC #2: Mask Creation with Brush Tool**
- GIVEN the image editor is open
- WHEN the user selects the brush tool
- THEN they can click and drag to draw a mask over regions to replace
- AND the masked region is highlighted (semi-transparent red/blue overlay)
- AND brush size is adjustable (slider: 10-100px)

**AC #3: Mask Editing**
- GIVEN a mask has been drawn
- WHEN the user selects the eraser tool
- THEN they can remove parts of the mask by clicking/dragging
- WHEN the user clicks "Clear Mask"
- THEN the entire mask is removed and they can start over

**AC #4: Replacement Prompt Input**
- GIVEN a mask has been created
- WHEN the user enters a text prompt describing the replacement
- EXAMPLES: "red sports car", "sunset beach background", "smiling woman in blue dress"
- THEN the prompt is validated (not empty, reasonable length)
- AND a negative prompt can optionally be provided
- EXAMPLES: "blurry, low quality, distorted"

**AC #5: Inpainting Execution**
- GIVEN a mask and replacement prompt exist
- WHEN the user clicks "Generate"
- THEN the backend sends image + mask + prompt to SDXL-inpaint model
- AND shows loading indicator "Generating replacement..."
- AND displays estimated time (if available)

**AC #6: Edited Image Display**
- GIVEN the inpainting is complete
- WHEN the result is received
- THEN the edited image is displayed side-by-side with the original
- AND shows a before/after comparison slider
- AND the user can choose "Use Edited" or "Keep Original"

**AC #7: Integration with Pipeline**
- GIVEN the user selects "Use Edited"
- WHEN they close the editor
- THEN the edited image replaces the original in ImageReview gallery
- AND the edited image is used in subsequent pipeline stages
- AND the original is preserved for rollback if needed

**AC #8: Multiple Edits**
- GIVEN an edited image exists
- WHEN the user clicks "Edit" again on the same image
- THEN they can make further edits to the edited version
- AND the edit history is tracked (original → edit1 → edit2)
- AND the user can revert to any previous version

---

## Tasks/Subtasks

**Backend: Inpainting Service (AC: #5)**
- [ ] Create `app/services/pipeline/inpainting_service.py` module
- [ ] Implement `InpaintingService` class
- [ ] Add `inpaint(image_path, mask, prompt, negative_prompt)` method
- [ ] Integrate Replicate SDXL-inpaint model
- [ ] Process mask (convert numpy array to PIL Image)
- [ ] Upload image and mask to Replicate API
- [ ] Download and save result image
- [ ] Return path to edited image

**Backend: API Routes (AC: #5, #7)**
- [ ] Update `interactive_generation.py` with inpainting endpoint
- [ ] Implement `POST /api/v1/interactive/{session_id}/inpaint`
- [ ] Accept: image_id, mask_data (base64 or binary), prompt, negative_prompt
- [ ] Call inpainting_service
- [ ] Update session state with edited image
- [ ] Return edited image URL

**Backend: Image Version Management (AC: #7, #8)**
- [ ] Add image version tracking to session state
- [ ] Store edit history: {original_url, edit1_url, edit2_url, ...}
- [ ] Support rollback to previous version
- [ ] Mark current active version

**Frontend: Image Editor Component (AC: #1, #2, #3, #4)**
- [ ] Create `src/components/generation/ImageEditor.tsx` component
- [ ] Implement modal/panel layout (full-screen or large modal)
- [ ] Integrate react-konva for canvas drawing
- [ ] Add brush tool with adjustable size
- [ ] Add eraser tool
- [ ] Add "Clear Mask" button
- [ ] Implement mask overlay (semi-transparent color)
- [ ] Add prompt input field
- [ ] Add negative prompt input field (optional, collapsed by default)

**Frontend: Canvas Drawing Logic (AC: #2, #3)**
- [ ] Implement Konva.Stage and Konva.Layer setup
- [ ] Load image onto canvas
- [ ] Track mouse events (mousedown, mousemove, mouseup) for drawing
- [ ] Render brush strokes as shapes on mask layer
- [ ] Convert mask layer to binary mask (0/1 numpy-like array or ImageData)
- [ ] Implement eraser (remove shapes under eraser)
- [ ] Implement clear (remove all shapes)

**Frontend: Brush Size Control (AC: #2)**
- [ ] Add slider for brush size (range: 10-100px)
- [ ] Update cursor size to match brush size
- [ ] Show brush size value (e.g., "50px")

**Frontend: Inpainting Execution (AC: #5, #6)**
- [ ] Convert canvas mask to base64 or binary data
- [ ] Call API: `inpaintImage(sessionId, imageId, maskData, prompt, negativePrompt)`
- [ ] Show loading state during inpainting
- [ ] Handle API response (edited image URL)
- [ ] Display edited image in editor

**Frontend: Before/After Comparison (AC: #6)**
- [ ] Implement side-by-side view (original | edited)
- [ ] Add comparison slider (drag to reveal before/after)
- [ ] Use react-compare-image or custom implementation
- [ ] Add "Use Edited" and "Keep Original" buttons

**Frontend: Integration with ImageReview (AC: #7, #8)**
- [ ] Update ImageReview.tsx to support "Edit" button per image
- [ ] Open ImageEditor modal on edit button click
- [ ] Pass image data to ImageEditor
- [ ] Update gallery with edited image when "Use Edited" is clicked
- [ ] Track edit history in pipelineStore
- [ ] Show "Edited" badge on modified images

**Frontend: API Client (AC: #5)**
- [ ] Update `interactive-api.ts` with inpainting method
- [ ] Implement `inpaintImage(sessionId, imageId, maskData, prompt, negativePrompt)`
- [ ] Handle large payload (mask data may be significant)

**Frontend: Error Handling (AC: #5)**
- [ ] Handle inpainting failures (model error, timeout)
- [ ] Display user-friendly error messages
- [ ] Allow retry with different prompt or mask

**Testing: Backend (AC: #5, #7, #8)**
- [ ] Create `tests/services/test_inpainting_service.py`
- [ ] Test mask processing (numpy to PIL Image conversion)
- [ ] Test Replicate API integration (mock API calls)
- [ ] Test image download and save
- [ ] Create `tests/api/test_inpainting.py`
- [ ] Test inpainting endpoint with valid/invalid inputs
- [ ] Test image version management

**Testing: Frontend (AC: #1-8)**
- [ ] Create `src/components/generation/__tests__/ImageEditor.test.tsx`
- [ ] Test brush drawing (mock canvas interactions)
- [ ] Test eraser functionality
- [ ] Test clear mask
- [ ] Test prompt validation
- [ ] Mock API call and test loading state
- [ ] Test before/after display
- [ ] Update `ImageReview.test.tsx` with edit button test

**Integration Testing (AC: #1-8)**
- [ ] Test full flow: open editor → draw mask → enter prompt → generate → use edited
- [ ] Test edited image persists in pipeline
- [ ] Test multiple edits on same image
- [ ] Test rollback to original

---

## Technical Summary

This story adds professional-grade image editing capabilities using AI inpainting. Users can select specific regions (mask) and replace them with AI-generated content based on text prompts, similar to Photoshop Generative Fill or Midjourney's Vary Region.

**Key Technology:**
- **SDXL-inpaint:** State-of-the-art inpainting model from Stability AI
- **react-konva:** React bindings for Konva.js (HTML5 canvas library)
- **Canvas API:** For mask drawing and image manipulation

**Architecture:**

**Backend:**
- **InpaintingService:** Handles AI inpainting workflow
  1. Receives image, mask (binary array), prompt
  2. Converts mask to PIL Image format
  3. Calls Replicate SDXL-inpaint API
  4. Downloads result, saves to storage
  5. Returns edited image URL

**Frontend:**
- **ImageEditor:** Full-featured image editor component
  - Canvas-based drawing with react-konva
  - Brush and eraser tools
  - Mask overlay visualization
  - Prompt input for replacement
  - Before/after comparison
  - Integration with ImageReview gallery

**Data Flow:**
```
User clicks "Edit" on image in ImageReview
  ↓
ImageEditor modal opens with image loaded on canvas
  ↓
User draws mask with brush tool
  ↓
User enters prompt: "red sports car"
  ↓
User clicks "Generate"
  ↓
Frontend converts canvas mask to binary data
  ↓
POST /api/v1/interactive/{id}/inpaint
  {imageId, maskData, prompt, negativePrompt}
  ↓
Backend: InpaintingService.inpaint()
  ↓
Call Replicate SDXL-inpaint API
  ↓
Download edited image
  ↓
Save to storage, return URL
  ↓
Frontend displays before/after comparison
  ↓
User clicks "Use Edited"
  ↓
ImageReview gallery updates with edited image
  ↓
Edited image used in subsequent stages (storyboard/video)
```

**Mask Format:**
- Frontend: Canvas with semi-transparent overlay
- Data format: Binary mask as base64 string or Blob
  - 1 (white) = selected region to replace
  - 0 (black) = preserve original

**Example Use Cases:**
1. **Character replacement:** Mask character, prompt "smiling woman in blue dress"
2. **Background change:** Mask background, prompt "sunset beach scene"
3. **Product swap:** Mask product, prompt "red iPhone 15 Pro"
4. **Object removal:** Mask object, prompt "empty space" or use negative prompt

---

## Project Structure Notes

**files_to_modify:**
```
# Backend
backend/app/services/pipeline/inpainting_service.py         # CREATE
backend/app/api/routes/interactive_generation.py            # MODIFY - Add inpaint endpoint

# Frontend
frontend/src/components/generation/ImageEditor.tsx          # CREATE
frontend/src/components/generation/ImageReview.tsx          # MODIFY - Add edit button
frontend/src/services/interactive-api.ts                    # MODIFY - Add inpaint method
frontend/src/stores/pipelineStore.ts                        # MODIFY - Add edit tracking
```

**test_locations:**
```
# Backend
backend/tests/services/test_inpainting_service.py           # CREATE
backend/tests/api/test_inpainting.py                        # CREATE

# Frontend
frontend/src/components/generation/__tests__/ImageEditor.test.tsx           # CREATE
frontend/src/components/generation/__tests__/ImageReview.test.tsx           # MODIFY
```

**story_points:** 3

**dependencies:**
- Story 3 (Interactive Image/Storyboard Feedback) - **REQUIRED** (provides ImageReview UI)
- Replicate SDXL-inpaint model access
- react-konva library for canvas
- Image storage (S3/local) for edited images

**estimated_effort:** 2-3 days

---

## Key Code References

**Existing Code to Reference:**

1. **`backend/app/services/pipeline/image_generation.py`** (Full file)
   - Replicate API integration pattern
   - Image upload/download logic
   - Use similar pattern for SDXL-inpaint

2. **`backend/app/services/pipeline/quality_control.py`** (If available)
   - Image processing utilities
   - PIL/numpy conversion patterns

**New Libraries to Install:**

**Backend:**
```python
# requirements.txt
# Already have:
# pillow>=10.0.0
# numpy>=1.24.0,<2.0
# replicate>=0.25.0

# No new dependencies needed
```

**Frontend:**
```json
// package.json
{
  "dependencies": {
    "react-konva": "^18.2.0",  // Canvas library
    "konva": "^9.2.0"          // Konva.js core
    // Optional:
    "react-compare-image": "^3.4.0"  // Before/after slider
  }
}
```

**New Patterns to Establish:**

1. **Mask Conversion (Frontend → Backend):**
```typescript
// Frontend: Canvas to binary mask
function canvasToBinaryMask(stage: Konva.Stage): string {
  // Get mask layer ImageData
  const maskLayer = stage.findOne('.maskLayer');
  const imageData = maskLayer.toCanvas().getContext('2d')!.getImageData(...);

  // Convert to binary (0/1)
  const binaryData = new Uint8Array(imageData.width * imageData.height);
  for (let i = 0; i < binaryData.length; i++) {
    binaryData[i] = imageData.data[i * 4] > 128 ? 1 : 0;  // Threshold
  }

  // Convert to base64 for transfer
  return btoa(String.fromCharCode(...binaryData));
}
```

2. **Inpainting Service Pattern:**
```python
# Backend
async def inpaint(
    image_path: str,
    mask_base64: str,
    prompt: str,
    negative_prompt: str = "blurry, low quality"
) -> str:
    # 1. Load image
    image = Image.open(image_path)

    # 2. Decode and convert mask
    mask_data = base64.b64decode(mask_base64)
    mask = Image.frombytes('L', (image.width, image.height), mask_data)

    # 3. Call Replicate SDXL-inpaint
    output = await replicate.run(
        "stability-ai/sdxl-inpaint",
        input={
            "image": image,
            "mask": mask,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "num_inference_steps": 50
        }
    )

    # 4. Download and save result
    edited_path = await download_image(output[0])

    return edited_path
```

---

## Context References

**Primary Reference:**
- Technical Specification: `docs/tech-spec.md`
  - See "Implementation Guide" → "Story 4: Advanced Image Editing"
  - See "Technical Details" → section 4 for inpainting workflow

**Related Documentation:**
- PRD: `docs/PRD.md` (Section 8.7.3: Iteration Workspace & Human-in-the-Loop Refinement)

**External References:**
- Replicate SDXL-inpaint: https://replicate.com/stability-ai/sdxl-inpaint
- react-konva docs: https://konvajs.org/docs/react/
- Konva drawing tutorial: https://konvajs.org/docs/react/Free_Drawing.html

---

## Dev Agent Record

**Agent Model Used:**
- TBD

**Debug Log References:**
- TBD

**Completion Notes:**
- TBD

**Files Modified:**
- TBD

**Test Results:**
- TBD

---

## Review Notes

**Code Review:**
- TBD

**QA Notes:**
- TBD

**Deployment Notes:**
- TBD
