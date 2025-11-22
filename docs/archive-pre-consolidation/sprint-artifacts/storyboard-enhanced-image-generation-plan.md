# Plan: Enhanced Image Generation for Storyboard Phase

## Overview

Apply the enhanced image generation approach (from Story 9-4) to the storyboard phase, specifically for generating start and end frames. This will improve quality and consistency of storyboard frames by using prompt enhancement, multiple variations, quality scoring, and best-image selection.

**Scope**: Image generation ONLY - does not affect storyboard prompt generation, JSON creation, or narrative generation.

---

## Current State Analysis

### Current Storyboard Image Generation (`storyboard_service.py`)

**Location**: `backend/app/services/pipeline/storyboard_service.py` (lines 164-272, 340-448)

**Current Approach**:
- Generates **1 image per frame** (start/end) using `generate_images()` directly
- No prompt enhancement
- No quality scoring
- No variation generation or ranking
- Uses sequential chaining: reference image + previous frame
- Simple fallback on errors

**Key Code Pattern**:
```python
start_frame_results = await generate_images(
    prompt=start_frame_prompt,
    num_variations=1,  # Single image
    aspect_ratio=aspect_ratio,
    output_dir=output_dir,
    model_name=model_name,
    image_input=image_input_list
)
start_frame_result = start_frame_results[0]  # Use first (and only) result
```

### Enhanced Reference Image Generation (`image_generation_batch.py`)

**Location**: `backend/app/services/pipeline/image_generation_batch.py` (lines 231-545)

**Enhanced Approach**:
- **Prompt Enhancement**: Iterative two-agent enhancement (4 iterations, threshold 85.0)
- **Variation Generation**: Generates 4 variations per scene
- **Quality Scoring**: Scores all variations using PickScore, CLIP-Score, Aesthetic
- **Ranking & Selection**: Ranks by overall quality, selects best (rank 1)
- **Sequential Chaining**: Maintains visual consistency chain
- **Error Handling**: Graceful fallbacks at each step
- **Trace Files**: Saves enhancement traces (cleaned up after completion)

**Key Services Used**:
- `enhance_prompt_iterative()` from `app.services.pipeline.prompt_enhancement`
- `generate_images()` from `app.services.image_generation`
- `score_image()` from `app.services.pipeline.image_quality_scoring`
- `rank_images_by_quality()` from `app.services.pipeline.image_quality_scoring`

---

## Target State

### Enhanced Storyboard Frame Generation

**New Approach**:
- For each start/end frame:
  1. Enhance prompt using iterative two-agent enhancement (4 iterations)
  2. Generate 4 image variations using enhanced prompt
  3. Score all 4 variations (PickScore, CLIP-Score, Aesthetic)
  4. Rank variations by overall quality score
  5. Select best-ranked image (rank 1) as the frame
  6. Check quality threshold (≥30.0) and log warnings if below
  7. Maintain sequential chaining (reference image + previous frame)
  8. Save trace files (cleaned up after completion)

**Benefits**:
- Higher quality frames (best of 4 variations)
- More consistent frames (quality scoring ensures good results)
- Better prompts (iterative enhancement)
- Maintains existing sequential chaining pattern
- Graceful error handling with fallbacks

---

## Implementation Plan

### Phase 1: Create Enhanced Frame Generation Function

**File**: `backend/app/services/pipeline/image_generation_batch.py`

**Task**: Create new function `generate_enhanced_storyboard_frames_with_sequential_references()`

**Function Signature**:
```python
async def generate_enhanced_storyboard_frames_with_sequential_references(
    prompts: List[str],  # One prompt per frame (start_frame_prompt or end_frame_prompt)
    output_dir: str,
    generation_id: str,
    frame_type: str,  # "start" or "end"
    clip_number: int,
    reference_image_uri: Optional[str] = None,  # Reference image for visual consistency
    previous_frame_path: Optional[str] = None,  # Previous frame for sequential chaining
    aspect_ratio: str = "16:9",
    cancellation_check: Optional[callable] = None,
    quality_threshold: float = 30.0,
    num_variations: int = 4,
    max_enhancement_iterations: int = 4,
) -> str:
    """
    Generate enhanced storyboard frame (start or end) with prompt enhancement and quality scoring.
    
    Returns:
        str: Path to selected best frame image
    """
```

**Implementation Steps**:
1. Create trace directory: `output/storyboard_frame_traces/{generation_id}/clip_{clip_number:03d}_{frame_type}/`
2. Enhance prompt using `enhance_prompt_iterative()` (4 iterations, threshold 85.0)
3. Build enhanced prompt with consistency markers (if available)
4. Prepare image_input list:
   - First clip start: reference_image_uri only
   - Subsequent clip start: reference_image_uri + previous_frame_path
   - End frame: reference_image_uri + current_clip_start_frame_path
5. Generate 4 variations using `generate_images()` with enhanced prompt
6. Score all 4 variations using `score_image()`
7. Rank variations using `rank_images_by_quality()`
8. Select best-ranked image (rank 1)
9. Check quality threshold (≥30.0) and log warnings if below
10. Rename selected image to `clip_{clip_number:03d}_{frame_type}.png`
11. Clean up trace files immediately after completion
12. Return path to selected frame

**Error Handling**:
- If enhancement fails: Fall back to original prompt, generate single image
- If generation fails: Retry once, then fall back to single image
- If scoring fails: Use first generated image (no ranking)
- Never fail entire storyboard due to frame generation errors

---

### Phase 2: Integrate into Storyboard Service

**File**: `backend/app/services/pipeline/storyboard_service.py`

**Task**: Replace direct `generate_images()` calls with enhanced function

**Changes Required**:

1. **Import new function** (at top of file):
```python
from app.services.pipeline.image_generation_batch import (
    generate_enhanced_storyboard_frames_with_sequential_references
)
```

2. **Replace start frame generation** (lines 164-220):
   - Remove: Direct `generate_images()` call with `num_variations=1`
   - Add: Call to `generate_enhanced_storyboard_frames_with_sequential_references()`
   - Pass: `frame_type="start"`, `clip_number=i`, `reference_image_uri`, `previous_frame_path`

3. **Replace end frame generation** (lines 222-272):
   - Remove: Direct `generate_images()` call with `num_variations=1`
   - Add: Call to `generate_enhanced_storyboard_frames_with_sequential_references()`
   - Pass: `frame_type="end"`, `clip_number=i`, `reference_image_uri`, `start_frame_path` (as previous_frame_path)

4. **Update both code paths**:
   - Enhanced prompts path (lines 146-310)
   - Generic prompts path (lines 311-486)

**Key Considerations**:
- Maintain existing sequential chaining logic
- Keep frame naming convention: `clip_{i:03d}_start.png`, `clip_{i:03d}_end.png`
- Preserve error handling and failed_clips tracking
- Maintain aspect_ratio parameter usage
- Keep reference_image_uri preparation logic

---

### Phase 3: Update Function Signature and Parameters

**Task**: Ensure new function matches storyboard service needs

**Parameters to Handle**:
- `generation_id`: Use timestamp or storyboard output directory name
- `output_dir`: Storyboard output directory
- `frame_type`: "start" or "end"
- `clip_number`: Current clip number (1-based)
- `reference_image_uri`: Already prepared URI (from `prepare_image_for_replicate()`)
- `previous_frame_path`: Path to previous frame (for sequential chaining)
- `aspect_ratio`: From storyboard function parameter
- `cancellation_check`: Optional (not currently used in storyboard, but good to support)

**Return Value**:
- Single string path to selected frame (replaces current `start_frame_path` / `end_frame_path`)

---

### Phase 4: Trace File Management

**Task**: Implement trace file cleanup

**Trace Directory Structure**:
```
output/storyboard_frame_traces/
  {generation_id}/
    clip_001_start/
      - 00_original_prompt.txt
      - 01_agent1_iteration_1.txt
      - 02_agent2_iteration_1.txt
      - ...
      - final_enhanced_prompt.txt
      - prompt_trace_summary.json
      - generation_trace.json
    clip_001_end/
      - (same structure)
    clip_002_start/
      - (same structure)
    ...
```

**Cleanup Strategy**:
- Delete trace files immediately after frame generation completes
- Use `shutil.rmtree()` to remove entire trace directory after all frames generated
- Log cleanup actions for debugging

---

### Phase 5: Error Handling and Fallbacks

**Task**: Implement graceful error handling

**Error Scenarios**:

1. **Prompt Enhancement Fails**:
   - Log error with context
   - Fall back to original prompt
   - Generate single image (not 4 variations)
   - Continue with storyboard generation

2. **Image Generation Fails**:
   - Log error with context
   - Retry once with original prompt
   - If retry fails, skip frame and mark clip as failed
   - Continue with next clip

3. **Quality Scoring Fails**:
   - Log warning
   - Use first generated image (no ranking)
   - Continue with storyboard generation

4. **Ranking Fails**:
   - Log warning
   - Use first scored image
   - Continue with storyboard generation

**Implementation**:
- Wrap each step in try/except blocks
- Log errors with clip number, frame type, and error details
- Never raise exceptions that would stop entire storyboard generation
- Update `failed_clips` list appropriately

---

## Implementation Details

### Function Location

**New Function**: `backend/app/services/pipeline/image_generation_batch.py`

**Rationale**: 
- Keeps image generation logic together
- Reuses existing services (enhancement, scoring, ranking)
- Follows pattern from `generate_enhanced_reference_images_with_sequential_references()`

### Dependencies

**Required Services**:
- `app.services.pipeline.prompt_enhancement.enhance_prompt_iterative`
- `app.services.image_generation.generate_images`
- `app.services.pipeline.image_quality_scoring.score_image`
- `app.services.pipeline.image_quality_scoring.rank_images_by_quality`

**All services are already available** (used in Story 9-4 implementation).

### Configuration

**Default Values**:
- `num_variations`: 4 per frame (fixed)
- `max_enhancement_iterations`: 4 (fixed)
- `quality_threshold`: 30.0 (minimum score to proceed, with warning if below)
- `score_threshold`: 85.0 (for prompt enhancement)

**Performance Impact**:
- Enhancement: ~10-20s per frame (4 LLM iterations)
- Multiple variations: ~15-30s per frame (4 image generations)
- Scoring: ~8-20s per frame (4 images × 2-5s each)
- **Total overhead per frame**: ~33-70s
- **For 3 clips (6 frames)**: ~198-420s additional time (3-7 minutes)

**Note**: This is acceptable given the quality improvement. Storyboard generation is not time-critical.

---

## Testing Plan

### Unit Tests

**File**: `backend/tests/services/pipeline/test_image_generation_batch.py`

**Test Cases**:
1. Test prompt enhancement integration (4 iterations)
2. Test image generation with 4 variations
3. Test quality scoring and ranking of 4 variations
4. Test quality threshold check (≥30) with warning logging
5. Test sequential chaining behavior:
   - First clip start: reference image only
   - Subsequent clip start: reference + previous frame
   - End frame: reference + current start frame
6. Test trace file cleanup after generation completes
7. Test error handling:
   - Enhancement failure → fallback to original prompt
   - Generation failure → retry once, then fallback
   - Scoring failure → use first image
   - Ranking failure → use first scored image

### Integration Tests

**File**: `backend/tests/services/pipeline/test_storyboard_service.py`

**Test Cases**:
1. Test full storyboard generation with enhanced frames (3 clips)
2. Test sequential chaining across multiple clips
3. Test frame quality (compare enhanced vs. previous approach)
4. Test error handling does not fail entire storyboard
5. Test trace file cleanup after storyboard completes

### Manual Testing

**Scenarios**:
1. Generate storyboard with 3 clips, verify start/end frames are high quality
2. Generate storyboard with reference image, verify consistency
3. Generate storyboard without reference image, verify it still works
4. Verify trace files are created and cleaned up
5. Test error scenarios (simulate API failures)

---

## Migration Strategy

### Backward Compatibility

**No breaking changes**:
- Function signature of `create_storyboard()` remains the same
- Output format (JSON, file paths) remains the same
- Frame naming convention remains the same
- Only internal implementation changes

### Rollout Plan

1. **Phase 1**: Implement new function (no integration)
2. **Phase 2**: Add feature flag (optional enhanced generation)
3. **Phase 3**: Test with feature flag enabled
4. **Phase 4**: Enable by default (remove feature flag)
5. **Phase 5**: Remove old code path (if desired)

**Feature Flag** (optional):
```python
USE_ENHANCED_STORYBOARD_FRAMES = True  # Default: True
```

---

## Success Criteria

### Quality Metrics

1. **Frame Quality**: 
   - Average quality score ≥ 50 (vs. current unmeasured quality)
   - Quality score ≥ 30 for 95% of frames (with warnings for < 30)

2. **Consistency**:
   - Visual consistency maintained across frames (sequential chaining works)
   - Reference image properly used for first clip

3. **Reliability**:
   - Storyboard generation success rate ≥ 95% (same as current)
   - Error handling prevents complete failures

### Performance Metrics

1. **Generation Time**:
   - Acceptable overhead: 3-7 minutes for 3 clips (6 frames)
   - No timeout issues

2. **Resource Usage**:
   - API calls: ~4x more (4 variations vs. 1)
   - Storage: Temporary (trace files cleaned up)

---

## Risks and Mitigations

### Risk 1: Increased Generation Time

**Impact**: Medium
**Probability**: High
**Mitigation**: 
- Acceptable trade-off for quality improvement
- Storyboard generation is not time-critical
- Can add feature flag to disable if needed

### Risk 2: API Rate Limits

**Impact**: Medium
**Probability**: Medium
**Mitigation**:
- Implement retry logic with exponential backoff
- Add rate limit detection and handling
- Fallback to single image if rate limited

### Risk 3: Quality Scoring Failures

**Impact**: Low
**Probability**: Low
**Mitigation**:
- Graceful fallback to first image
- Log warnings for debugging
- Continue with storyboard generation

### Risk 4: Trace File Storage

**Impact**: Low
**Probability**: Low
**Mitigation**:
- Clean up immediately after generation
- Use temporary directory
- Monitor disk usage

---

## Open Questions

1. **Should we add a feature flag?**
   - Recommendation: No, enable by default (quality improvement is worth it)

2. **Should we keep old code path?**
   - Recommendation: Remove after testing (simplifies maintenance)

3. **Should we expose configuration?**
   - Recommendation: Use fixed defaults (4 variations, 4 iterations) for consistency

4. **Should we add progress tracking?**
   - Recommendation: Yes, update progress for enhancement, generation, scoring steps

---

## Next Steps

1. ✅ Review and approve plan
2. ⏳ Implement `generate_enhanced_storyboard_frames_with_sequential_references()`
3. ⏳ Integrate into `storyboard_service.py`
4. ⏳ Add unit tests
5. ⏳ Add integration tests
6. ⏳ Manual testing
7. ⏳ Deploy and monitor

---

## References

- **Story 9-4**: `docs/sprint-artifacts/9-4-enhanced-reference-image-generation.md`
- **Current Storyboard Service**: `backend/app/services/pipeline/storyboard_service.py`
- **Enhanced Reference Generation**: `backend/app/services/pipeline/image_generation_batch.py` (lines 231-545)
- **Prompt Enhancement**: `backend/app/services/pipeline/prompt_enhancement.py`
- **Quality Scoring**: `backend/app/services/pipeline/image_quality_scoring.py`


