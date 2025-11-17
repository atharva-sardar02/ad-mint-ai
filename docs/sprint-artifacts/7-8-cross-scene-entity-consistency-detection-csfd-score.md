# Story 7.8: Cross-Scene Entity Consistency Detection (CSFD Score)

Status: drafted

## Story

As a developer,
I want to implement CSFD (Cross-Scene Face Distance) scoring for character-driven ads,
so that the system can quantify and ensure character consistency across multiple scenes.

## Acceptance Criteria

1. **CSFD Score Calculation:**
   **Given** a video with a main character appearing in multiple scenes
   **When** the consistency detection service processes it
   **Then** it:
   - Extracts face embeddings from each scene featuring the character
   - Computes pairwise distances between face embeddings
   - Calculates CSFD score (lower = better consistency)
   - Identifies scenes with character appearance drift

2. **Character Consistency Assessment:**
   **Given** CSFD scores are computed for all character appearances
   **When** the system evaluates consistency
   **Then** it:
   - Determines if CSFD score is below acceptable threshold (<0.3 for excellent)
   - Flags scenes with high CSFD scores (character drift)
   - Provides recommendations for regeneration of inconsistent scenes
   - Tracks character consistency across all videos

3. **Integration:**
   **Given** CSFD scoring is implemented
   **When** a character-driven video generation completes
   **Then** the system:
   - Checks if CSFD detection is enabled in coherence settings (default: disabled, character ads only)
   - Automatically runs CSFD analysis if enabled and character consistency groups are present
   - Skips CSFD analysis if disabled
   - Stores CSFD scores in quality_metrics table (if enabled)
   - Triggers regeneration for scenes exceeding CSFD threshold (optional, if enabled)
   - Makes CSFD scores available for quality feedback loop

[Source: docs/epics.md#Story-7.8]

## Tasks / Subtasks

- [ ] Task 1: Research and Set Up Face Detection and Embedding Libraries (AC: 1)
  - [ ] Research face detection libraries (face_recognition, InsightFace, ArcFace)
  - [ ] Evaluate library availability, performance, and accuracy
  - [ ] Determine best approach for face embedding extraction (ArcFace, FaceNet, or similar)
  - [ ] Document face detection and embedding methodology
  - [ ] Set up face detection dependencies in requirements.txt
  - [ ] Create face detection test script to verify integration
  - [ ] Unit test: Face detection with sample video frames

- [ ] Task 2: Implement CSFD Score Calculation Service (AC: 1, 2)
  - [ ] Create `csfd_scoring.py` service in `backend/app/services/pipeline/`
  - [ ] Implement `extract_face_embeddings()` function that:
    - Accepts video clip path and scene number
    - Detects faces in video frames
    - Extracts face embeddings using chosen library (ArcFace/FaceNet)
    - Returns face embeddings for each detected face
  - [ ] Implement `calculate_csfd_score()` function that:
    - Accepts face embeddings from multiple scenes
    - Computes pairwise distances between embeddings
    - Calculates CSFD score (average or max distance)
    - Returns CSFD score and scene comparison details
  - [ ] Implement error handling (graceful degradation if face detection fails)
  - [ ] Add logging for CSFD scoring operations
  - [ ] Unit test: Face embedding extraction with sample video
  - [ ] Unit test: CSFD score calculation with known embeddings
  - [ ] Unit test: CSFD score calculation edge cases (no faces, single face, multiple faces)

- [ ] Task 3: Integrate CSFD Scoring into Quality Control Pipeline (AC: 1, 3)
  - [ ] Update `quality_control.py` to include CSFD scoring functionality
  - [ ] Add `evaluate_csfd()` function that:
    - Checks if CSFD detection is enabled in coherence settings
    - Checks if character consistency groups are present in scene plan
    - Extracts face embeddings from all character scenes
    - Calculates CSFD scores for all character appearances
    - Returns CSFD scores and consistency assessment
  - [ ] Integrate CSFD evaluation into quality control workflow
  - [ ] Store CSFD scores in QualityMetric model (add `csfd_score` field if not present)
  - [ ] Update quality control to run CSFD analysis after video generation completes (if enabled)
  - [ ] Ensure CSFD analysis doesn't block pipeline (async where possible)
  - [ ] Integration test: CSFD scoring integrated into quality control pipeline
  - [ ] Integration test: CSFD analysis runs only when enabled and character groups present

- [ ] Task 4: Implement CSFD Threshold Configuration and Assessment (AC: 2)
  - [ ] Create CSFD threshold configuration in `backend/app/core/config.py`
  - [ ] Define default CSFD threshold (recommended: <0.3 for excellent, <0.5 for good)
  - [ ] Make threshold configurable via environment variables
  - [ ] Implement `assess_character_consistency()` function in csfd_scoring.py that:
    - Accepts CSFD scores and threshold
    - Determines if scores are below acceptable threshold
    - Flags scenes with high CSFD scores (character drift)
    - Generates recommendations for regeneration of inconsistent scenes
  - [ ] Add consistency tracking to QualityMetric model
  - [ ] Unit test: CSFD threshold checking logic
  - [ ] Unit test: Character consistency assessment with various score combinations

- [ ] Task 5: Add CSFD Score Storage to Quality Metrics (AC: 3)
  - [ ] Verify QualityMetric model has `csfd_score` field (add if missing)
  - [ ] Update QualityMetric schema in `backend/app/schemas/generation.py` to include CSFD score
  - [ ] Update quality control service to store CSFD scores in database
  - [ ] Ensure CSFD scores are linked to correct scenes and generations
  - [ ] Unit test: CSFD score storage in QualityMetric model
  - [ ] Integration test: CSFD scores persisted correctly in database

- [ ] Task 6: Implement Optional Regeneration Trigger for High CSFD Scores (AC: 2, 3)
  - [ ] Add `csfd_regeneration_enabled` flag to coherence settings (optional feature)
  - [ ] Implement regeneration trigger logic in quality_control.py:
    - Check if CSFD regeneration is enabled
    - Check if CSFD score exceeds threshold
    - Trigger regeneration for scenes with high CSFD scores
    - Track regeneration attempts for CSFD-triggered regenerations
  - [ ] Update regeneration logic to handle CSFD-triggered regenerations
  - [ ] Log CSFD-triggered regeneration attempts
  - [ ] Integration test: Regeneration triggered for high CSFD scores (if enabled)
  - [ ] Integration test: CSFD regeneration respects retry limits

- [ ] Task 7: Update Coherence Settings Integration (AC: 3)
  - [ ] Verify `csfd_detection` setting exists in coherence settings schema
  - [ ] Ensure CSFD detection service respects enabled/disabled setting
  - [ ] Update coherence settings validation to handle CSFD dependencies (requires enhanced planning)
  - [ ] Add logging when CSFD detection is disabled (informational only)
  - [ ] Verify CSFD detection default is disabled (character ads only)
  - [ ] Unit test: CSFD detection respects coherence settings flag

- [ ] Task 8: Create CSFD Score API Endpoint (AC: 3)
  - [ ] Update `GET /api/generations/{id}/quality` endpoint to include CSFD scores
  - [ ] Add CSFD score data to quality metrics response:
    - CSFD score per scene (if character-driven)
    - Character consistency assessment summary
    - Scenes flagged for high CSFD scores
    - Recommendations for regeneration (if applicable)
  - [ ] Ensure authorization check (user can only access their own CSFD scores)
  - [ ] Integration test: Quality metrics endpoint returns CSFD scores
  - [ ] Integration test: Authorization prevents access to other users' CSFD scores

- [ ] Task 9: Add CSFD Score Display (Optional UI Enhancement) (AC: 3)
  - [ ] Update `VideoDetail.tsx` to display CSFD scores if available (character-driven ads)
  - [ ] Show CSFD score per scene with character appearances
  - [ ] Display character consistency assessment (excellent/good/poor)
  - [ ] Add visual indicators for scenes with high CSFD scores (character drift warnings)
  - [ ] Make CSFD metrics section optional/collapsible
  - [ ] Unit test: CSFD score display component
  - [ ] E2E test: User can view CSFD scores on video detail page (if character-driven)

- [ ] Task 10: Performance Optimization and Documentation (AC: 1, 2, 3)
  - [ ] Measure CSFD calculation time per scene
  - [ ] Optimize face detection and embedding extraction (batch processing, caching)
  - [ ] Implement async CSFD analysis where possible (don't block pipeline)
  - [ ] Add performance logging for CSFD operations
  - [ ] Monitor CSFD calculation overhead (target: <15 seconds per character scene)
  - [ ] Document CSFD scoring methodology and thresholds
  - [ ] Document face detection library choice and rationale
  - [ ] Performance test: CSFD calculation doesn't significantly slow pipeline
  - [ ] Performance test: Async CSFD analysis works correctly

## Dev Notes

### Architecture Patterns and Constraints

- **Service Layer Pattern:** Create new `csfd_scoring.py` service following existing service structure from `quality_control.py` and `video_generation.py`. CSFD scoring should integrate with the quality control pipeline.
- **Database Schema:** CSFD scores stored in existing `quality_metrics` table (add `csfd_score` field if not present). CSFD analysis is optional - generation continues even if CSFD analysis fails.
- **API Design:** CSFD scores included in existing `/api/generations/{id}/quality` endpoint. Follows RESTful patterns established in Epic 3 and Story 7.6.
- **Pipeline Integration:** CSFD analysis runs after video generation completes (if enabled). Should not block pipeline - use async processing where possible. Regeneration triggers new clip generation with updated parameters.
- **Error Handling:** If face detection fails, log error but continue generation without CSFD analysis. Graceful degradation ensures pipeline reliability.
- **Coherence Settings Integration:** CSFD detection respects `csfd_detection` flag from coherence settings. Default: disabled (character ads only). Requires enhanced planning (Story 7.3) to identify character consistency groups.

[Source: docs/architecture.md#Project-Structure]
[Source: docs/architecture.md#Implementation-Patterns]
[Source: docs/sprint-artifacts/tech-spec-epic-7.md#Services-and-Modules]

### Project Structure Notes

**New Files to Create:**
- `backend/app/services/pipeline/csfd_scoring.py` - CSFD scoring service with face detection and embedding extraction
- `backend/tests/test_csfd_scoring.py` - Unit tests for CSFD scoring service
- `backend/tests/test_face_detection.py` - Face detection integration test script

**Files to Modify:**
- `backend/app/services/pipeline/quality_control.py` - Integrate CSFD scoring into quality control pipeline
- `backend/app/db/models/quality_metric.py` - Add `csfd_score` field to QualityMetric model (if not present)
- `backend/app/schemas/generation.py` - Add CSFD score to quality metrics schemas
- `backend/app/api/routes/generations.py` - Update quality metrics endpoint to include CSFD scores
- `backend/app/core/config.py` - Add CSFD threshold configuration
- `backend/app/services/coherence_settings.py` - Verify `csfd_detection` setting exists and is properly handled
- `backend/requirements.txt` - Add face detection dependencies (face_recognition, insightface, or similar)
- `frontend/src/routes/VideoDetail.tsx` - Add CSFD score display (optional)

**Component Location:**
- CSFD scoring service follows existing pipeline service patterns in `backend/app/services/pipeline/`
- CSFD scoring integrates with existing quality control service
- CSFD score display (if implemented) follows existing video detail page patterns

[Source: docs/architecture.md#Project-Structure]
[Source: docs/sprint-artifacts/tech-spec-epic-7.md#Data-Models-and-Contracts]

### Testing Standards

- **Unit Tests:** Test CSFD scoring service functions, face detection, embedding extraction, and threshold checking in isolation. Use pytest for backend.
- **Integration Tests:** Test full CSFD analysis flow from video generation to CSFD scoring to database storage. Test CSFD integration with quality control pipeline.
- **E2E Tests:** Test user flow from character-driven generation with CSFD enabled to viewing CSFD scores (if UI implemented).
- **Backend Tests:** Use pytest for all backend service and API endpoint tests. Test face detection, CSFD calculation, threshold checking, and regeneration logic.
- **Performance Tests:** Measure CSFD calculation overhead and ensure it doesn't significantly slow pipeline.

[Source: docs/architecture.md#Testing]
[Source: docs/sprint-artifacts/tech-spec-epic-7.md#Test-Strategy-Summary]

### Learnings from Previous Story

**From Story 7-6 (VBench Integration for Automated Quality Control):**
- **Quality Control Service Pattern:** CSFD scoring should integrate with existing `quality_control.py` service, similar to how VBench evaluation is integrated. Follow the same service structure and error handling patterns.
- **Database Model Pattern:** CSFD scores should be stored in existing `QualityMetric` model (add `csfd_score` field). Follow the same database patterns from Story 7.6 - use UUID primary keys, proper foreign keys, and migration scripts if needed.
- **API Endpoint Pattern:** CSFD scores should be included in existing `/api/generations/{id}/quality` endpoint, following the same RESTful patterns established in Story 7.6.
- **Pipeline Integration:** CSFD analysis should run after video generation completes (if enabled), similar to VBench evaluation. Should not block pipeline - use async processing where possible.
- **Error Handling:** If CSFD analysis fails, generation should continue (graceful degradation) - similar to VBench error handling.
- **Coherence Settings Integration:** CSFD detection already has `csfd_detection` flag in coherence settings - verify integration with `coherence_settings.py` service. Default is disabled (character ads only).
- **Testing Approach:** Use comprehensive integration tests similar to VBench tests - test full flow from API to database.

**Key Reusable Components:**
- `QualityMetric` model from `backend/app/db/models/quality_metric.py` - extend with `csfd_score` field
- `quality_control.py` service from `backend/app/services/pipeline/quality_control.py` - integrate CSFD scoring
- Coherence settings service from `backend/app/services/coherence_settings.py` - read `csfd_detection` flag
- Quality metrics API endpoint from `backend/app/api/routes/generations.py` - extend to include CSFD scores
- Database session patterns from existing services - follow same transaction patterns for CSFD score storage

[Source: docs/sprint-artifacts/7-6-vbench-integration-for-automated-quality-control.md#Dev-Agent-Record]
[Source: backend/app/services/pipeline/quality_control.py]
[Source: backend/app/services/coherence_settings.py]

### References

- [Source: docs/epics.md#Story-7.8] - Story acceptance criteria and technical notes
- [Source: docs/sprint-artifacts/tech-spec-epic-7.md#Services-and-Modules] - CSFD scoring service design patterns
- [Source: docs/sprint-artifacts/tech-spec-epic-7.md#Data-Models-and-Contracts] - QualityMetric database model specification (CSFD score field)
- [Source: docs/sprint-artifacts/tech-spec-epic-7.md#Workflows-and-Sequencing] - CSFD analysis workflow in generation pipeline
- [Source: docs/Multi_Scene_Video_Ad_Generation_Research_Report.md#CSFD-Score] - CSFD scoring methodology and implementation details
- [Source: docs/PRD.md#20.2-Phase-3-Features] - Character consistency requirements context
- [Source: docs/architecture.md#Project-Structure] - Backend and frontend structure patterns
- [Source: docs/architecture.md#Implementation-Patterns] - Naming conventions and error handling patterns
- [Source: backend/app/services/pipeline/quality_control.py] - Existing quality control service for integration reference
- [Source: backend/app/services/coherence_settings.py] - Coherence settings service for CSFD flag integration

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

## Change Log

- 2025-11-16: Story created (drafted)

