# Story 7.7: Enhanced Post-Processing with Brand Palette Preservation

Status: drafted

## Story

As a developer,
I want to enhance post-processing with brand-aware color grading and transition optimization,
so that final videos maintain brand identity while improving visual coherence.

## Acceptance Criteria

1. **Brand-Aware Color Grading:**
   **Given** a video with brand color guidelines
   **When** post-processing applies color grading
   **Then** it:
   - Preserves brand color palette from original generation
   - Applies color matching between clips while maintaining brand colors
   - Uses histogram matching to normalize colors across scenes
   - Applies LUTs (Look-Up Tables) for consistent color grading
   - Maintains brand visual identity throughout video

2. **Transition Optimization:**
   **Given** multiple clips are being stitched together
   **When** transitions are applied
   **Then** the system:
   - Optimizes crossfade durations based on scene analysis
   - Adjusts transition easing for smoother flow
   - Uses motion matching for seamless scene linking
   - Applies appropriate transition types (cut, crossfade, wipe, flash, zoom_blur, whip_pan, glitch) based on scene relationship and target audience

3. **Lighting and Style Normalization:**
   **Given** clips may have varying lighting and style
   **When** post-processing normalizes the video
   **Then** it:
   - Adjusts exposure to match across clips
   - Normalizes contrast and saturation
   - Applies texture matching for style consistency
   - Enhances sharpness uniformly
   - Maintains artistic intent while improving coherence

4. **Integration:**
   **Given** enhanced post-processing is implemented
   **When** a video generation completes stitching
   **Then** the system:
   - Checks if post-processing enhancement is enabled in coherence settings (default: enabled)
   - Applies brand-aware color grading before final export (if enabled)
   - Optimizes transitions based on scene analysis (if enabled)
   - Normalizes lighting and style (if enabled)
   - Skips enhancements if disabled (uses basic post-processing)
   - Maintains video quality (no degradation, 1080p minimum)
   - Completes processing efficiently

[Source: docs/epics.md#Story-7.7]
[Source: docs/sprint-artifacts/tech-spec-epic-7.md#Acceptance-Criteria]

## Tasks / Subtasks

- [ ] Task 1: Enhance Color Grading with Brand Palette Preservation (AC: 1)
  - [ ] Extend `_apply_color_grading()` in `export.py` to accept brand color palette
  - [ ] Implement histogram matching algorithm using OpenCV to normalize colors across clips while preserving brand colors
  - [ ] Create LUT (Look-Up Table) generation function for brand color palettes
  - [ ] Implement color matching between clips that maintains brand color identity
  - [ ] Extract brand colors from LLM enhancement output (brand_guidelines section)
  - [ ] Store brand color palette in generation record for post-processing reference
  - [ ] Unit test: Histogram matching preserves brand colors
  - [ ] Unit test: LUT generation creates correct color transformations
  - [ ] Unit test: Color matching maintains brand identity across clips

- [ ] Task 2: Implement Transition Optimization (AC: 2)
  - [ ] Extend `stitch_video_clips()` in `stitching.py` to analyze scene relationships
  - [ ] Implement scene analysis function that determines optimal transition type:
    - Cut for rapid scene changes and dramatic reveals
    - Crossfade for smooth narrative flow
    - Flash/zoom_blur/whip_pan/glitch for high-energy modern content
    - Wipe for location changes
  - [ ] Calculate optimal crossfade duration based on scene motion and content
  - [ ] Implement transition easing (ease-in, ease-out) for smoother flow
  - [ ] Add motion matching algorithm to link scenes with similar motion patterns
  - [ ] Integrate transition optimization with existing stitching service
  - [ ] Unit test: Transition type selection based on scene analysis
  - [ ] Unit test: Crossfade duration calculation
  - [ ] Integration test: Transition optimization integrated into stitching pipeline

- [ ] Task 3: Implement Lighting and Style Normalization (AC: 3)
  - [ ] Create `normalize_lighting_style()` function in `export.py` or new `enhanced_post_processing.py` service
  - [ ] Implement exposure matching across clips using histogram analysis
  - [ ] Implement contrast normalization using CLAHE (Contrast Limited Adaptive Histogram Equalization)
  - [ ] Implement saturation normalization to match across clips
  - [ ] Add texture matching algorithm for style consistency (using OpenCV texture analysis)
  - [ ] Implement uniform sharpness enhancement across all clips
  - [ ] Ensure normalization maintains artistic intent (preserve creative choices)
  - [ ] Unit test: Exposure matching across clips
  - [ ] Unit test: Contrast and saturation normalization
  - [ ] Unit test: Texture matching maintains style consistency

- [ ] Task 4: Create Enhanced Post-Processing Service (AC: 1, 2, 3, 4)
  - [ ] Create `enhanced_post_processing.py` service in `backend/app/services/pipeline/`
  - [ ] Implement `apply_enhanced_post_processing()` function that:
    - Accepts video clips, brand guidelines, coherence settings
    - Applies brand-aware color grading (if enabled)
    - Optimizes transitions (if enabled)
    - Normalizes lighting and style (if enabled)
    - Returns processed video ready for export
  - [ ] Integrate with existing `export.py` and `stitching.py` services
  - [ ] Add proper error handling and graceful degradation
  - [ ] Add logging for post-processing operations
  - [ ] Unit test: Enhanced post-processing service with all features enabled
  - [ ] Unit test: Enhanced post-processing service with features disabled
  - [ ] Integration test: Enhanced post-processing integrated into full pipeline

- [ ] Task 5: Integrate Enhanced Post-Processing into Pipeline (AC: 4)
  - [ ] Update `generations.py` route to check `post_processing_enhancement` flag in coherence settings
  - [ ] Call enhanced post-processing service after stitching and before final export
  - [ ] Pass brand color guidelines from LLM enhancement to post-processing
  - [ ] Ensure video quality maintained (1080p minimum, no degradation)
  - [ ] Update generation progress to reflect post-processing stage
  - [ ] Handle cancellation checks during post-processing
  - [ ] Integration test: Enhanced post-processing in full generation pipeline
  - [ ] Integration test: Post-processing respects coherence settings flag
  - [ ] Performance test: Post-processing overhead stays within acceptable limits

- [ ] Task 6: Update Database Schema for Brand Guidelines (AC: 1, 4)
  - [ ] Verify `generations` table has field to store brand color guidelines (check if exists in LLM enhancement output)
  - [ ] If missing, add `brand_guidelines` JSON field to store brand colors and style preferences
  - [ ] Create migration script if schema change needed: `backend/app/db/migrations/add_brand_guidelines.py`
  - [ ] Update Pydantic schemas in `backend/app/schemas/generation.py` to include brand guidelines
  - [ ] Unit test: Brand guidelines storage and retrieval
  - [ ] Integration test: Migration up and down (if migration created)

- [ ] Task 7: Add Dependencies for Enhanced Post-Processing (AC: 1, 3)
  - [ ] Add `scikit-image>=0.21.0` to `requirements.txt` for histogram matching and advanced image processing
  - [ ] Add `lutgen>=0.1.0` to `requirements.txt` for LUT generation (or implement custom LUT generation)
  - [ ] Verify OpenCV is already in requirements (should be present from Epic 3)
  - [ ] Update dependency documentation
  - [ ] Test dependency installation in clean environment

- [ ] Task 8: Performance Optimization and Quality Validation (AC: 4)
  - [ ] Measure post-processing time overhead
  - [ ] Optimize histogram matching and color grading algorithms for performance
  - [ ] Implement caching for LUT generation (reuse LUTs for same brand colors)
  - [ ] Validate video quality after post-processing (resolution, bitrate, visual quality)
  - [ ] Ensure no quality degradation (1080p minimum maintained)
  - [ ] Add performance logging for post-processing operations
  - [ ] Performance test: Post-processing completes within acceptable time (<45 seconds per video)
  - [ ] Quality test: Post-processed video maintains 1080p resolution and visual quality

## Dev Notes

### Architecture Patterns and Constraints

- **Service Layer Pattern:** Create new `enhanced_post_processing.py` service following existing service structure from `export.py` and `stitching.py`. Enhanced post-processing should extend existing services rather than replace them.
- **Pipeline Integration:** Enhanced post-processing runs after stitching (from `stitching.py`) and before final export (in `export.py`). Should integrate seamlessly with existing pipeline stages.
- **Coherence Settings Integration:** Enhanced post-processing respects `post_processing_enhancement` flag from coherence settings. Default: enabled (recommended).
- **Error Handling:** If enhanced post-processing fails, fall back to basic post-processing (existing `export.py` functionality). Graceful degradation ensures pipeline reliability.
- **Brand Guidelines:** Extract brand colors from LLM enhancement output (`AdSpecification.brand_guidelines`). Store in generation record for post-processing reference.

[Source: docs/architecture.md#Project-Structure]
[Source: docs/architecture.md#Implementation-Patterns]
[Source: docs/sprint-artifacts/tech-spec-epic-7.md#Services-and-Modules]

### Project Structure Notes

**New Files to Create:**
- `backend/app/services/pipeline/enhanced_post_processing.py` - Enhanced post-processing service with brand-aware color grading, transition optimization, and style normalization

**Files to Modify:**
- `backend/app/services/pipeline/export.py` - Integrate enhanced post-processing, extend `_apply_color_grading()` for brand palette preservation
- `backend/app/services/pipeline/stitching.py` - Add transition optimization functions
- `backend/app/api/routes/generations.py` - Integrate enhanced post-processing into generation pipeline
- `backend/app/db/models/generation.py` - Verify/add brand_guidelines field (may already exist from LLM enhancement)
- `backend/app/schemas/generation.py` - Add brand guidelines to schemas if needed
- `backend/app/core/config.py` - Add post-processing configuration (thresholds, quality settings)
- `backend/requirements.txt` - Add scikit-image and lutgen dependencies
- `backend/app/services/pipeline/llm_enhancement.py` - Verify brand_guidelines extraction from LLM output

**Component Location:**
- Enhanced post-processing service follows existing pipeline service patterns in `backend/app/services/pipeline/`
- Color grading functions extend existing `_apply_color_grading()` in `export.py`
- Transition optimization extends existing `stitch_video_clips()` in `stitching.py`

[Source: docs/architecture.md#Project-Structure]
[Source: docs/sprint-artifacts/tech-spec-epic-7.md#Data-Models-and-Contracts]

### Testing Standards

- **Unit Tests:** Test enhanced post-processing service functions, color grading algorithms, transition optimization, and style normalization in isolation. Use pytest for backend.
- **Integration Tests:** Test full enhanced post-processing flow from stitching to export. Test integration with coherence settings and pipeline.
- **E2E Tests:** Test user flow from generation with enhanced post-processing enabled to viewing final video with brand palette preserved.
- **Backend Tests:** Use pytest for all backend service and algorithm tests. Test histogram matching, LUT generation, transition optimization, and style normalization.
- **Performance Tests:** Measure post-processing overhead and ensure it doesn't significantly slow pipeline (target: <45 seconds per video).
- **Quality Tests:** Validate video quality after post-processing (resolution, visual quality, brand color preservation).

[Source: docs/architecture.md#Testing]
[Source: docs/sprint-artifacts/tech-spec-epic-7.md#Test-Strategy-Summary]

### Learnings from Previous Story

**From Story 7-6 (VBench Integration for Automated Quality Control):**
- **Service Structure:** Follow `quality_control.py` service structure for `enhanced_post_processing.py` - clean service interface, proper error handling, logging, graceful degradation
- **Coherence Settings Integration:** Enhanced post-processing has `post_processing_enhancement` flag in coherence settings - verify integration with `coherence_settings.py` service
- **Database Pattern:** Follow QualityMetric model pattern for storing brand guidelines - use JSON field for flexible brand color storage
- **Pipeline Integration:** Enhanced post-processing should integrate with existing pipeline similar to how quality control integrates - run after specific stage, respect coherence settings, update progress
- **Error Handling:** If enhanced post-processing fails, fall back to basic post-processing (similar to quality control graceful degradation)
- **Testing Approach:** Use comprehensive integration tests similar to quality control tests - test full flow from API to database

**From Story 7-2 (Parallel Generation and Comparison Tool):**
- **Service Integration:** Enhanced post-processing should integrate with existing export and stitching services, similar to how parallel generation extends the pipeline
- **API Patterns:** Follow RESTful endpoint patterns established in parallel generation for any new endpoints (if needed)

**From Story 7-1 (Seed Control and Latent Reuse for Visual Coherence):**
- **Service Structure:** Follow `seed_manager.py` service structure for clean service interface
- **Database Migration Pattern:** Follow migration pattern from Story 7.1 for adding new fields - use standalone Python script pattern consistent with project

**From Epic 3 (Video Generation Pipeline):**
- **Pipeline Integration:** Enhanced post-processing should integrate with existing `export.py` and `stitching.py` services - extend existing functions rather than replace
- **Progress Tracking:** Update generation progress to reflect enhanced post-processing stage
- **Cost Tracking:** Enhanced post-processing may incur additional processing time - ensure cost tracking accounts for this (if applicable)
- **Existing Color Grading:** Current `_apply_color_grading()` in `export.py` uses OpenCV for basic color grading - extend this function for brand palette preservation

**Key Reusable Components:**
- `export.py` service from `backend/app/services/pipeline/export.py` - extend `_apply_color_grading()` for brand palette preservation
- `stitching.py` service from `backend/app/services/pipeline/stitching.py` - extend `stitch_video_clips()` for transition optimization
- `Generation` model from `backend/app/db/models/generation.py` - verify/add brand_guidelines field
- Coherence settings service from `backend/app/services/coherence_settings.py` - read `post_processing_enhancement` flag
- Database session patterns from existing services - follow same transaction patterns for brand guidelines storage
- LLM enhancement output (`AdSpecification`) - extract brand_guidelines for post-processing

[Source: docs/sprint-artifacts/7-6-vbench-integration-for-automated-quality-control.md#Dev-Agent-Record]
[Source: docs/sprint-artifacts/7-2-parallel-generation-and-comparison-tool.md#Dev-Agent-Record]
[Source: backend/app/services/pipeline/export.py]
[Source: backend/app/services/pipeline/stitching.py]

### References

- [Source: docs/epics.md#Story-7.7] - Story acceptance criteria and technical notes
- [Source: docs/sprint-artifacts/tech-spec-epic-7.md#Services-and-Modules] - Enhanced post-processing service design patterns
- [Source: docs/sprint-artifacts/tech-spec-epic-7.md#Data-Models-and-Contracts] - Brand guidelines storage specification
- [Source: docs/sprint-artifacts/tech-spec-epic-7.md#Workflows-and-Sequencing] - Enhanced post-processing workflow in generation pipeline
- [Source: docs/sprint-artifacts/tech-spec-epic-7.md#Dependencies-and-Integrations] - Required dependencies (scikit-image, lutgen)
- [Source: docs/PRD.md#20.2-Phase-3-Features] - Quality optimization requirements context
- [Source: docs/architecture.md#Project-Structure] - Backend and frontend structure patterns
- [Source: docs/architecture.md#Implementation-Patterns] - Naming conventions and error handling patterns
- [Source: backend/app/services/pipeline/export.py] - Existing export service with color grading for extension reference
- [Source: backend/app/services/pipeline/stitching.py] - Existing stitching service for transition optimization extension
- [Source: backend/app/services/pipeline/llm_enhancement.py] - LLM enhancement service for brand_guidelines extraction

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

## Change Log

- 2025-01-27: Story created (drafted)

