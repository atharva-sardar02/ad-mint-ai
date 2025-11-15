# Story 3.3: Video Assembly and Export

Status: drafted

## Story

As a developer,
I want to stitch clips together, add audio, and export the final video,
so that the output is professional-quality and ready for download.

## Acceptance Criteria

1. **Video Stitching:**
   **Given** multiple video clips with text overlays
   **When** the video stitching service processes them
   **Then** it concatenates clips in sequence
   **And** applies crossfade transitions (0.5s) between clips
   **And** adds fade in at start (0.3s) and fade out at end (0.3s)
   **And** maintains consistent frame rate (24-30 fps)

2. **Audio Layer:**
   **Given** a stitched video and music style specification
   **When** the audio layer service processes it
   **Then** it selects background music from library based on style
   **And** trims music to video duration
   **And** adjusts music volume to 30%
   **And** adds sound effects at scene transitions
   **And** composites audio (music + SFX) and attaches to video

3. **Post-Processing and Export:**
   **Given** a video with audio
   **When** the post-processing service processes it
   **Then** it applies color grading based on brand style
   **And** exports final video as 1080p MP4 (H.264 codec)
   **And** generates thumbnail from first frame
   **And** saves video to permanent storage (`/output/videos/`)
   **And** updates database with video_url and thumbnail_url

4. **Final Video Quality:**
   **Given** a completed video generation
   **When** I examine the final video
   **Then** total duration matches sum of scene durations (accounting for transitions)
   **And** frame rate is consistent (24 fps default)
   **And** resolution is 1080p minimum
   **And** file size is reasonable (<50MB for 15s video)
   **And** video plays correctly in HTML5 video players

[Source: docs/epics.md#Story-3.3]
[Source: docs/sprint-artifacts/tech-spec-epic-3.md#AC-3.3.1]
[Source: docs/sprint-artifacts/tech-spec-epic-3.md#AC-3.3.2]
[Source: docs/sprint-artifacts/tech-spec-epic-3.md#AC-3.3.3]
[Source: docs/sprint-artifacts/tech-spec-epic-3.md#AC-3.3.4]

## Tasks / Subtasks

- [ ] Task 1: Create Video Stitching Service (AC: 1)
  - [ ] Create `backend/app/services/pipeline/stitching.py` module
  - [ ] Implement function to concatenate video clips using MoviePy
  - [ ] Apply crossfade transitions (0.5s) between clips using CompositeVideoClip
  - [ ] Add fade in effect at start (0.3s) using fadein method
  - [ ] Add fade out effect at end (0.3s) using fadeout method
  - [ ] Ensure consistent frame rate (24-30 fps) across all clips
  - [ ] Handle clip duration mismatches (trim or pad clips to match)
  - [ ] Export stitched video to temp storage
  - [ ] Test: Test video stitching with multiple clips and transitions

- [ ] Task 2: Create Audio Layer Service (AC: 2)
  - [ ] Create `backend/app/services/pipeline/audio.py` module
  - [ ] Create or verify music library structure (`/backend/assets/music/` directory)
  - [ ] Implement music selection logic based on style/mood from scene plan
  - [ ] Load music file from library (MP3 format)
  - [ ] Trim music to match video duration using MoviePy
  - [ ] Adjust music volume to 30% using volumex method
  - [ ] Implement sound effect selection for scene transitions
  - [ ] Load sound effects from library (`/backend/assets/sfx/` directory)
  - [ ] Composite audio tracks (music + SFX) using CompositeAudioClip
  - [ ] Attach composite audio to video using set_audio method
  - [ ] Test: Test audio layer with various music styles and sound effects

- [ ] Task 3: Create Post-Processing and Export Service (AC: 3)
  - [ ] Create `backend/app/services/pipeline/export.py` module
  - [ ] Implement color grading function using OpenCV or MoviePy filters
  - [ ] Apply color grading based on brand style keywords from scene plan
  - [ ] Export video as 1080p MP4 with H.264 codec using MoviePy write_videofile
  - [ ] Configure FFmpeg encoding settings (bitrate, quality, preset)
  - [ ] Generate thumbnail from first frame using MoviePy save_frame or Pillow
  - [ ] Save video to permanent storage (`/output/videos/` directory)
  - [ ] Save thumbnail to permanent storage (`/output/thumbnails/` directory)
  - [ ] Update Generation model with video_url and thumbnail_url
  - [ ] Test: Test export with various video qualities and thumbnail generation

- [ ] Task 4: Integrate Stitching, Audio, and Export into Pipeline (AC: 1, 2, 3)
  - [ ] Update `backend/app/api/routes/generations.py` generation endpoint
  - [ ] After text overlays (progress=80%), call video stitching service
  - [ ] Update progress to 85% after stitching
  - [ ] Call audio layer service after stitching
  - [ ] Update progress to 90% after audio layer
  - [ ] Call post-processing and export service
  - [ ] Update progress to 95% during export
  - [ ] Update Generation record with video_url, thumbnail_url, status=completed, progress=100%
  - [ ] Clean up temp clip files after successful export
  - [ ] Handle errors: update status to failed, store error_message
  - [ ] Check cancellation_requested flag before each stage
  - [ ] Test: Integration test for complete flow (clips → stitching → audio → export)

- [ ] Task 5: Update Generation Model Schema (AC: 3)
  - [ ] Update `backend/app/db/models/generation.py` Generation model
  - [ ] Add `video_url` string field to store final video path
  - [ ] Add `thumbnail_url` string field to store thumbnail path
  - [ ] Create database migration script for new fields
  - [ ] Update Pydantic schemas in `backend/app/schemas/generation.py` if needed
  - [ ] Test: Verify model updates and migration

- [ ] Task 6: Create Music and Sound Effects Library (AC: 2)
  - [ ] Create `/backend/assets/music/` directory structure
  - [ ] Organize music files by mood/style (e.g., energetic, calm, professional)
  - [ ] Create `/backend/assets/sfx/` directory for sound effects
  - [ ] Add royalty-free music files (MP3 format) to library
  - [ ] Add sound effect files (MP3/WAV format) for transitions
  - [ ] Document music library structure and selection logic
  - [ ] Test: Verify music library structure and file access

- [ ] Task 7: Testing (AC: 1, 2, 3, 4)
  - [ ] Unit test: Video stitching service with multiple clips and transitions
  - [ ] Unit test: Audio layer service with various music styles
  - [ ] Unit test: Post-processing service with color grading and export
  - [ ] Unit test: Thumbnail generation
  - [ ] Integration test: Complete flow (clips → stitching → audio → export)
  - [ ] Integration test: Error handling (file not found, encoding failures)
  - [ ] Integration test: Cancellation during stitching/audio/export
  - [ ] E2E test: User submits prompt → final video exported → video plays correctly

## Dev Notes

### Architecture Patterns and Constraints

- **Backend Framework:** FastAPI + Python 3.11 (from Epic 1)
- **Video Processing:** MoviePy library for video stitching, audio composition, and export
- **Audio Processing:** MoviePy for audio manipulation, Pydub for advanced audio processing if needed
- **Image Processing:** Pillow for thumbnail generation, OpenCV for color grading
- **Video Encoding:** FFmpeg (via MoviePy) for H.264 encoding and export
- **Storage:** Permanent video storage in `/output/videos/`, thumbnails in `/output/thumbnails/`
- **Error Handling:** Retry logic for encoding failures, clear error messages, cleanup temp files
- **Logging:** Structured logging at INFO level for each stage, WARNING for encoding issues, ERROR for failures
- **Cancellation:** Check `cancellation_requested` flag before each stage (stitching, audio, export)
- **Cost Tracking:** No additional API costs for this story (all local processing)

[Source: docs/architecture.md#Decision-Summary]
[Source: docs/architecture.md#Project-Structure]
[Source: docs/sprint-artifacts/tech-spec-epic-3.md#System-Architecture-Alignment]
[Source: docs/PRD.md#AI-Video-Generation-Pipeline]
[Source: docs/sprint-artifacts/tech-spec-epic-3.md#Dependencies-and-Integrations]

### Project Structure Notes

- **Backend Services:** `backend/app/services/pipeline/stitching.py` - Video stitching service
- **Backend Services:** `backend/app/services/pipeline/audio.py` - Audio layer service
- **Backend Services:** `backend/app/services/pipeline/export.py` - Post-processing and export service
- **Backend API:** `backend/app/api/routes/generations.py` - Update generation endpoint to call stitching, audio, and export
- **Backend Models:** `backend/app/db/models/generation.py` - Add video_url and thumbnail_url fields
- **Backend Schemas:** `backend/app/schemas/generation.py` - Update if needed for video_url and thumbnail_url
- **Assets:** `/backend/assets/music/` - Music library directory
- **Assets:** `/backend/assets/sfx/` - Sound effects library directory
- **Storage:** `/output/videos/` - Permanent video storage (create if not exists)
- **Storage:** `/output/thumbnails/` - Thumbnail storage (create if not exists)
- **Dependencies:** MoviePy already in requirements.txt, may need to add `opencv-python` and `pillow` if not present

[Source: docs/architecture.md#Project-Structure]
[Source: docs/sprint-artifacts/tech-spec-epic-3.md#Services-and-Modules]

### Learnings from Previous Story

**From Story 3-2-video-generation-and-text-overlays (Status: done)**

- **Pipeline Services Pattern:** Services are organized under `backend/app/services/pipeline/` as separate modules - follow same pattern for stitching.py, audio.py, and export.py
- **Generation Model:** Generation model has `temp_clip_paths` JSON field storing array of temp clip file paths - use this to load clips for stitching
- **API Endpoint Pattern:** Generation endpoint (`POST /api/generate`) already handles LLM enhancement, scene planning, and video generation - extend to call stitching, audio, and export after video generation completes
- **Progress Tracking:** Progress updates follow pattern: update `progress` percentage and `current_step` description at each stage - continue this pattern (80% for stitching, 90% for audio, 95% for export, 100% for complete)
- **Error Handling:** Follow same error handling patterns: update status to `failed`, store `error_message`, log errors with structured logging
- **Pydantic Schemas:** Use Pydantic schemas for request/response validation - may need to update schemas for video_url and thumbnail_url fields
- **MoviePy Usage:** MoviePy is already used for text overlays - reuse patterns for video stitching and audio composition
- **Temp File Management:** Temp clips stored in `/output/temp/` - clean up after successful export, handle cleanup on errors
- **Cancellation Support:** Cancellation checks occur before each pipeline stage - continue this pattern for stitching, audio, and export stages

**New Files Created (to reference):**
- `backend/app/services/pipeline/video_generation.py` - Video clip generation service (shows MoviePy usage patterns)
- `backend/app/services/pipeline/overlays.py` - Text overlay service (shows MoviePy composition patterns)
- `backend/app/api/routes/generations.py` - Generation API endpoints (shows endpoint pattern and progress tracking)

**Architectural Decisions:**
- Services are modular and separate - each pipeline stage has its own module
- JSON fields in Generation model store intermediate pipeline data (llm_specification, scene_plan, temp_clip_paths) - use same pattern for final video URLs
- Progress tracking updates database at each stage - continue this pattern for final stages
- Error handling uses structured logging and database status updates - follow same pattern
- MoviePy is used for all video processing (overlays, stitching, audio, export) - maintain consistency

**Technical Debt:**
- Video validation was completed in story 3-2 using ffprobe - reuse validation patterns if needed for final video
- Text animations simplified for MVP (slide_up and scale reduced to fade_in) - similar simplifications may be needed for color grading in MVP

**Testing Patterns:**
- Backend testing uses pytest with FastAPI TestClient
- Mock external APIs in tests (not needed for this story - all local processing)
- Integration tests verify complete flow
- Unit tests for each service module

[Source: docs/sprint-artifacts/3-2-video-generation-and-text-overlays.md#Dev-Agent-Record]
[Source: docs/sprint-artifacts/3-2-video-generation-and-text-overlays.md#File-List]

### References

- [Source: docs/epics.md#Story-3.3] - Story requirements and acceptance criteria
- [Source: docs/sprint-artifacts/tech-spec-epic-3.md#AC-3.3.1] - Video stitching acceptance criteria
- [Source: docs/sprint-artifacts/tech-spec-epic-3.md#AC-3.3.2] - Audio layer acceptance criteria
- [Source: docs/sprint-artifacts/tech-spec-epic-3.md#AC-3.3.3] - Post-processing and export acceptance criteria
- [Source: docs/sprint-artifacts/tech-spec-epic-3.md#AC-3.3.4] - Final video quality acceptance criteria
- [Source: docs/sprint-artifacts/tech-spec-epic-3.md#Services-and-Modules] - Service module responsibilities
- [Source: docs/sprint-artifacts/tech-spec-epic-3.md#APIs-and-Interfaces] - API specifications
- [Source: docs/sprint-artifacts/tech-spec-epic-3.md#Workflows-and-Sequencing] - Pipeline workflow details
- [Source: docs/sprint-artifacts/tech-spec-epic-3.md#Dependencies-and-Integrations] - MoviePy, OpenCV, Pillow dependencies
- [Source: docs/PRD.md#AI-Video-Generation-Pipeline] - Pipeline overview and final export details
- [Source: docs/PRD.md#Stage-5-Video-Stitching] - Video stitching process
- [Source: docs/PRD.md#Stage-6-Audio-Layer] - Audio layer process
- [Source: docs/PRD.md#Stage-7-Post-Processing-and-Export] - Post-processing and export process
- [Source: docs/architecture.md#Decision-Summary] - Architecture decisions for backend (FastAPI, SQLAlchemy, Pydantic)
- [Source: docs/architecture.md#Project-Structure] - Backend project structure and organization

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

## Change Log

- **2025-11-14**: Story created from epics.md and tech-spec-epic-3.md

