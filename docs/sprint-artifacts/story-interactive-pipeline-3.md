# User Story 1.3: Interactive Image/Storyboard Feedback

**Epic:** Interactive Video Generation Pipeline
**Story ID:** interactive-pipeline-3
**Status:** Draft
**Points:** 3
**Priority:** High

---

## User Story

**As a** content creator using the web application
**I want** to review and refine reference images and storyboard images through conversational feedback before proceeding to video generation
**So that** I can ensure visual quality meets my standards and avoid generating videos based on images I don't like

---

## Acceptance Criteria

**AC #1: Reference Image Review**
- GIVEN the user has approved the story
- WHEN reference images are generated (Stage 2 complete)
- THEN the frontend displays all reference images in a gallery layout
- AND shows the reusable chat interface from Story 2
- AND shows "Approve" and "Regenerate" buttons
- AND displays quality scores for each image (if available from quality_control.py)

**AC #2: Image-Specific Feedback**
- GIVEN the user is reviewing reference images
- WHEN they provide feedback like "make the background brighter" or "change the character's outfit to blue"
- THEN the conversation handler processes the image-specific feedback
- AND translates feedback into image generation parameters
- AND responds conversationally explaining the planned changes

**AC #3: Image Regeneration**
- GIVEN the user has provided image feedback
- WHEN they click "Regenerate"
- THEN the backend regenerates reference images with updated parameters
- AND shows loading indicator "Regenerating images..."
- AND the new images replace the old ones in the gallery
- AND quality scores are updated

**AC #4: Reference Image Approval**
- GIVEN the user is satisfied with reference images
- WHEN they click "Approve"
- THEN the session state updates to "approved_reference_image"
- AND the pipeline proceeds to Stage 3 (storyboard generation)
- AND the frontend shows "Reference images approved! Generating storyboard..."

**AC #5: Storyboard Review**
- GIVEN the user has approved reference images
- WHEN storyboard images are generated (Stage 3 complete)
- THEN the frontend displays all storyboard images in a gallery
- AND shows image index/sequence number (Clip 1, Clip 2, etc.)
- AND shows the chat interface for feedback
- AND shows "Approve" and "Edit" buttons per image

**AC #6: Storyboard-Specific Feedback**
- GIVEN the user is reviewing storyboard images
- WHEN they provide feedback for a specific clip like "Clip 2 needs more motion blur"
- THEN the conversation handler identifies which clip to modify
- AND processes the feedback
- AND regenerates only that specific clip's images (or all if feedback is general)

**AC #7: Batch Feedback Handling**
- GIVEN the user wants to provide feedback on multiple images
- WHEN they say "all images are too dark" or "Clips 1-3 need better lighting"
- THEN the conversation handler processes batch feedback
- AND identifies all affected images
- AND regenerates them with updated parameters

**AC #8: Storyboard Approval and Video Generation**
- GIVEN the user is satisfied with all storyboard images
- WHEN they click "Approve"
- THEN the session state updates to "approved_storyboard"
- AND the pipeline proceeds to Stage 4 (video generation)
- AND the frontend shows "Storyboard approved! Generating final video..."

---

## Tasks/Subtasks

**Backend: Extend Interactive Pipeline (AC: #1, #4, #5, #8)**
- [ ] Update `interactive_pipeline.py` to support `reference_image` stage
- [ ] Add `storyboard` stage support
- [ ] Implement pause points for both new stages
- [ ] Add stage-specific state management (store images, clip info)

**Backend: Image Feedback Processing (AC: #2, #3, #6, #7)**
- [ ] Extend `conversation_handler.py` with image feedback methods
- [ ] Implement `process_image_feedback(images, feedback, history)` method
- [ ] Add feedback translation logic (conversational → image parameters)
- [ ] Support clip-specific feedback parsing ("Clip 2", "third image", etc.)
- [ ] Support batch feedback ("all images", "Clips 1-3")
- [ ] Integrate with `image_generation.py` for regeneration

**Backend: API Routes (AC: #3, #6)**
- [ ] Update `interactive_generation.py` with image-specific endpoints (if needed)
- [ ] Support regenerate requests with image indices
- [ ] Return quality scores with images

**Backend: Quality Score Integration (AC: #1)**
- [ ] Integrate `quality_control.py` (from Epic 7) to score images
- [ ] Return scores (PickScore, CLIP-Score, Aesthetic) with images
- [ ] Store scores in session state

**Frontend: Image Review Component (AC: #1, #5)**
- [ ] Create `src/components/generation/ImageReview.tsx` component
- [ ] Implement gallery layout (2-3 columns, responsive)
- [ ] Display image with index/clip number
- [ ] Show quality scores as badges
- [ ] Add click-to-enlarge (modal/lightbox)
- [ ] Integrate ChatInterface from Story 2 (reuse)
- [ ] Add "Approve" button for batch approval
- [ ] Add "Edit" button per image (prepare for Story 4)

**Frontend: Update Pipeline Component (AC: #1, #4, #5, #8)**
- [ ] Update `InteractivePipeline.tsx` to render ImageReview for reference_image stage
- [ ] Add storyboard stage rendering (also uses ImageReview)
- [ ] Update stage progress indicator to highlight current stage
- [ ] Handle stage transitions from images → storyboard → video

**Frontend: Image Selection & Feedback (AC: #2, #6, #7)**
- [ ] Add image selection UI (click to select for targeted feedback)
- [ ] Show selected image indicator (border, checkmark)
- [ ] Support multi-select for batch feedback
- [ ] Update chat context with selected image info
- [ ] Send image indices with feedback message

**Frontend: API Updates (AC: #3, #6)**
- [ ] Update `interactive-api.ts` with image regeneration support
- [ ] Add `regenerateImages(sessionId, imageIndices, feedback)` method
- [ ] Handle batch regeneration requests

**Frontend: Loading States (AC: #3, #6)**
- [ ] Show spinner during image regeneration
- [ ] Display progress indicator if regenerating multiple images
- [ ] Preserve conversation history during regeneration

**Testing: Backend (AC: #1-8)**
- [ ] Update `test_interactive_pipeline.py` with reference_image and storyboard stages
- [ ] Test stage transitions: story → reference_image → storyboard
- [ ] Create `test_image_feedback.py` for image-specific feedback processing
- [ ] Test clip-specific feedback parsing
- [ ] Test batch feedback handling
- [ ] Mock image_generation.py and quality_control.py

**Testing: Frontend (AC: #1-8)**
- [ ] Create `src/components/generation/__tests__/ImageReview.test.tsx`
- [ ] Test gallery rendering
- [ ] Test image selection (single and multi-select)
- [ ] Test approve and regenerate buttons
- [ ] Update `InteractivePipeline.test.tsx` with new stages
- [ ] Test stage transitions

**Integration Testing (AC: #1-8)**
- [ ] Test full flow: story → reference images → feedback → regenerate → approve
- [ ] Test storyboard: images → feedback → regenerate → approve → video
- [ ] Test batch feedback on multiple clips
- [ ] Test quality score display

---

## Technical Summary

This story extends the interactive pattern from Story 2 (story feedback) to visual stages (reference images and storyboard). It reuses the chat infrastructure and adds image-specific feedback processing, gallery UI, and batch operations.

**Key Differences from Story 2:**
- **Multiple outputs:** Story has 1 output (text), images have N outputs (image files)
- **Batch feedback:** Users can select multiple images for feedback
- **Quality scores:** Images have numerical quality scores to display
- **Clip context:** Storyboard images have sequence/clip numbers

**Architecture:**

**Backend:**
- **InteractivePipelineOrchestrator:** Extended with reference_image and storyboard stages
- **ConversationHandler:** New `process_image_feedback()` method
  - Parses clip-specific references ("Clip 2", "third image")
  - Translates conversational feedback to image parameters:
    - "brighter" → increase brightness/exposure
    - "change outfit to blue" → update prompt with color
    - "more motion blur" → add motion effects to prompt
  - Supports batch operations ("all images", "Clips 1-3")

**Frontend:**
- **ImageReview:** Gallery component for both reference_image and storyboard stages
  - Grid layout with responsive columns
  - Click to enlarge (modal)
  - Quality scores displayed
  - Selection UI for targeted feedback
  - Reuses ChatInterface from Story 2

**Data Flow (Reference Images):**
```
User approves story
  ↓
Backend generates reference images (existing image_generation.py)
  ↓
Backend scores images (quality_control.py)
  ↓
Backend saves to session, sends WS notification
  ↓
Frontend displays images in ImageReview gallery
  ↓
User selects image, sends feedback: "make this darker"
  ↓
ConversationHandler processes, updates parameters
  ↓
Backend regenerates image with adjustments
  ↓
Frontend updates gallery with new image + scores
  ↓
User approves all images
  ↓
Pipeline proceeds to storyboard
```

**Data Flow (Storyboard):**
```
Reference images approved
  ↓
Backend generates storyboard (existing storyboard_generator.py)
  ↓
Storyboard has N clips, each with start/end frames
  ↓
Frontend displays clips in sequence
  ↓
User: "Clip 2 has wrong character"
  ↓
ConversationHandler identifies Clip 2, processes feedback
  ↓
Backend regenerates Clip 2 only
  ↓
Frontend updates Clip 2 images
  ↓
User approves storyboard
  ↓
Pipeline proceeds to video generation
```

---

## Project Structure Notes

**files_to_modify:**
```
# Backend (extend existing from Story 2)
backend/app/services/pipeline/interactive_pipeline.py        # MODIFY - Add stages
backend/app/services/pipeline/conversation_handler.py        # MODIFY - Add image methods

# Frontend (new components)
frontend/src/components/generation/ImageReview.tsx          # CREATE
frontend/src/components/generation/InteractivePipeline.tsx  # MODIFY - Add stages

# Frontend (updates)
frontend/src/services/interactive-api.ts                    # MODIFY - Add image methods
frontend/src/types/pipeline.ts                              # MODIFY - Add image types
```

**test_locations:**
```
# Backend
backend/tests/services/test_interactive_pipeline.py         # MODIFY - Add image stage tests
backend/tests/services/test_image_feedback.py               # CREATE

# Frontend
frontend/src/components/generation/__tests__/ImageReview.test.tsx           # CREATE
frontend/src/components/generation/__tests__/InteractivePipeline.test.tsx   # MODIFY
```

**story_points:** 3

**dependencies:**
- Story 2 (Interactive Story Generation) - **REQUIRED** (provides chat infrastructure)
- Existing `image_generation.py` service
- Existing `storyboard_generator.py` service
- Optional: `quality_control.py` for quality scores (Epic 7)

**estimated_effort:** 2-3 days

---

## Key Code References

**Existing Code to Reference:**

1. **`backend/app/services/pipeline/image_generation.py`** (Full file)
   - Replicate API integration for image generation
   - Use for regeneration with updated prompts/parameters

2. **`backend/app/services/pipeline/storyboard_generator.py`** (Full file)
   - Storyboard creation with start/end frames
   - Clip structure and organization

3. **`backend/app/services/pipeline/quality_control.py`** (If available from Epic 7)
   - Image quality scoring (PickScore, CLIP-Score, Aesthetic Predictor)
   - Use to score generated images

4. **`backend/app/services/pipeline/image_prompt_enhancement.py`** (Lines 1-300)
   - Image-specific prompt enhancement patterns
   - Adapt for feedback translation

**New Patterns to Establish:**

1. **Image Feedback Translation:**
```python
async def translate_image_feedback(feedback: str) -> Dict[str, Any]:
    """
    Translate conversational feedback to image parameters.

    Examples:
    "make it brighter" → {"brightness": +0.2, "exposure": +0.1}
    "change background to sunset" → {"prompt": "...sunset background..."}
    "more vibrant colors" → {"saturation": +0.3}
    """
```

2. **Clip-Specific Parsing:**
```python
def parse_clip_references(feedback: str) -> List[int]:
    """
    Extract clip numbers from feedback.

    Examples:
    "Clip 2 is too dark" → [2]
    "Clips 1-3 need better lighting" → [1, 2, 3]
    "all clips" → [1, 2, 3, ..., N]
    """
```

---

## Context References

**Primary Reference:**
- Technical Specification: `docs/tech-spec.md`
  - See "Implementation Guide" → "Story 3: Interactive Image/Storyboard Feedback"
  - See "Technical Approach" → section 2 for conversational refinement

**Related Documentation:**
- PRD: `docs/PRD.md` (Section 8.7: Hero-Frame & Iterative Refinement Workflow)
- Epic 8 Tech Spec: `docs/sprint-artifacts/tech-spec-epic-8.md` (image generation patterns)

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
