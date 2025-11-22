# Epic Technical Specification: Video Editing

Date: 2025-11-15
Author: BMad
Epic ID: 6
Status: Draft

---

## Overview

Epic 6 implements a comprehensive video editing system that enables users to edit generated videos using a timeline-based editor with trim, split, and merge capabilities. This epic transforms the AI Video Ad Generator from a simple generation tool into a full-featured video editing platform, allowing users to fine-tune their generated content before final export. As outlined in the PRD (Section 8.4), the system provides an editor interface accessible from completed videos, a timeline interface showing all video clips, and three core editing operations: clip trimming, clip splitting, and clip merging. The epic also includes save and export functionality that preserves original videos while creating new edited versions. This epic builds upon Epic 3 (video generation pipeline with scene clips), Epic 4 (video gallery and playback), and requires the existing video storage and database infrastructure from Epic 1. The video editing capabilities enable users to refine their AI-generated content, remove unwanted portions, reorganize scenes, and create polished final videos suitable for professional advertising use.

## Objectives and Scope

**In-Scope:**
- **Navigation Access:**
  - "Editor" tab in navbar (between Gallery and Profile) for direct editor access
  - "Edit Video" button on video detail page for completed videos (navigates to editor with that video loaded)
- **Editor Interface:**
  - Editor page accessible at `/editor` (empty state) and `/editor/:generationId` (with specific video loaded)
  - Editor layout: video preview player, timeline at bottom, side panels for controls
  - Gallery integration panel: allows adding videos from user's gallery to editor timeline
  - Timeline interface displaying all scene clips with thumbnails, durations, and playhead
  - Timeline interaction: scrubbing, zoom in/out, clip selection, time markers
- **Editing Operations:**
  - Clip trimming: adjust start/end points with drag handles, real-time preview, validation
  - Clip splitting: divide clips at playhead position, preserve metadata for both resulting clips
  - Clip merging: combine adjacent clips into single continuous clip with transitions
- **Persistence & Export:**
  - Editor save functionality: persist editing state to database, allow resume editing
  - Editor export: create new video version with all edits applied, maintain original backup
  - Backend API endpoints for editor data loading, editing operations, save, and export
  - Editing session management: track active editing sessions in database
  - Original video preservation: maintain backup for restoration capability
  - Version management: display both original and edited versions

**Out-of-Scope:**
- Advanced video effects (color grading, filters, transitions beyond basic crossfade) (post-MVP)
- Audio editing (separate audio tracks, volume adjustment, music replacement) (post-MVP)
- Text overlay editing within editor (post-MVP)
- Clip reordering/drag-and-drop on timeline (post-MVP)
- Undo/redo functionality (mentioned in technical notes but not in acceptance criteria) (post-MVP)
- Multi-track editing (post-MVP)
- Keyframe animation (post-MVP)
- Real-time collaboration (post-MVP)
- Mobile editor interface (desktop-only for MVP)

## System Architecture Alignment

This epic extends the existing architecture with a new video editing module that integrates with the video generation pipeline (Epic 3) and video management system (Epic 4). The backend follows the established FastAPI pattern with new routes in `app/api/routes/editor.py` for editor-specific endpoints. The editor leverages MoviePy (already in tech stack) for video manipulation operations (trim, split, merge), consistent with the architecture's use of MoviePy for video processing in Epic 3. The frontend adds a new editor route/page component (`Editor.tsx`) that uses React Router's page-based routing, following the architecture's routing structure. The timeline interface requires canvas or SVG rendering for performance, which aligns with the architecture's emphasis on efficient UI components. The editing session data model extends the existing database schema with an `editing_sessions` table, following the SQLAlchemy ORM patterns established in Epic 1. The editor maintains separation of concerns: API routes handle HTTP, services handle business logic (trim/split/merge operations), and the database layer persists editing state. The export functionality reuses the video processing pipeline from Epic 3, ensuring consistency in video output format and quality (1080p MP4).

## Detailed Design

### Services and Modules

| Module/Service | Responsibility | Inputs | Outputs | Owner |
|----------------|----------------|--------|---------|-------|
| `backend/app/api/routes/editor.py` | Editor API routes: load editor data, trim, split, merge, save, export | HTTP requests with JWT token, generation_id, edit operations | Editor data responses, operation confirmations | Backend |
| `backend/app/services/editor/editor_service.py` | Editor business logic: load clips, validate edits, apply operations | Generation ID, edit operations (trim/split/merge) | Editor state, validation results | Backend |
| `backend/app/services/editor/trim_service.py` | Clip trimming operations using MoviePy | Clip path, start time, end time | Trimmed clip path | Backend |
| `backend/app/services/editor/split_service.py` | Clip splitting operations using MoviePy | Clip path, split time | Two clip paths | Backend |
| `backend/app/services/editor/merge_service.py` | Clip merging operations using MoviePy | List of clip paths | Merged clip path | Backend |
| `backend/app/services/editor/export_service.py` | Video export: apply all edits, create final video | Editing session data, original video path | Exported video path | Backend |
| `backend/app/db/models/editing_session.py` | Editing session ORM model | N/A | Database record | Backend |
| `frontend/src/routes/Editor.tsx` | Main editor page component | Route params (generation_id, optional) | Editor UI with layout | Frontend |
| `frontend/src/components/editor/Timeline.tsx` | Timeline visualization component | Clip data, editing state | Timeline UI with interactions | Frontend |
| `frontend/src/components/editor/VideoPlayer.tsx` | Video preview player component | Video URL, playback position | Video player UI | Frontend |
| `frontend/src/components/editor/TrimControls.tsx` | Trim handle UI components | Selected clip, trim state | Trim handles, time inputs | Frontend |
| `frontend/src/components/editor/GalleryPanel.tsx` | Gallery video selection panel | User's video gallery | Video selection UI for adding to timeline | Frontend |
| `frontend/src/components/layout/Navbar.tsx` | Navigation bar (updated) | N/A | Editor tab link | Frontend |
| `frontend/src/routes/VideoDetail.tsx` | Video detail page (updated) | Video ID | Edit Video button | Frontend |
| `frontend/src/lib/editorApi.ts` | Editor API client functions | Editor operations | API responses | Frontend |

### Data Models and Contracts

**EditingSession Model (New):**
```python
class EditingSession(Base):
    __tablename__ = "editing_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    generation_id = Column(String(36), ForeignKey("generations.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    original_video_path = Column(String(500), nullable=False)  # Backup of original
    editing_state = Column(JSON, nullable=False)  # Current editing operations
    # editing_state structure:
    # {
    #   "clips": [
    #     {
    #       "id": "clip-1",
    #       "original_path": "/path/to/clip.mp4",
    #       "start_time": 0.0,
    #       "end_time": 5.0,
    #       "trim_start": 0.5,  # Optional trim adjustments
    #       "trim_end": 4.5,
    #       "split_points": [],  # If split, contains split times
    #       "merged_with": []  # If merged, contains other clip IDs
    #     }
    #   ],
    #   "version": 1
    # }
    status = Column(String(20), default="active")  # active, saved, exported
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    exported_video_path = Column(String(500), nullable=True)  # Path to exported video
    
    # Relationships
    generation = relationship("Generation", backref="editing_sessions")
    user = relationship("User", backref="editing_sessions")
```

**Editor Data Response Schema:**
```python
class EditorDataResponse(BaseModel):
    generation_id: str
    original_video_url: str
    original_video_path: str
    clips: List[ClipInfo]
    total_duration: float
    aspect_ratio: str
    framework: Optional[str]

class ClipInfo(BaseModel):
    clip_id: str
    scene_number: int
    original_path: str
    clip_url: str
    duration: float
    start_time: float  # Start time in original video
    end_time: float
    thumbnail_url: Optional[str]
    text_overlay: Optional[dict]  # Text overlay metadata if exists
```

**Edit Operation Request Schemas:**
```python
class TrimClipRequest(BaseModel):
    clip_id: str
    trim_start: float  # New start time (seconds)
    trim_end: float  # New end time (seconds)

class SplitClipRequest(BaseModel):
    clip_id: str
    split_time: float  # Time position to split at (seconds)

class MergeClipsRequest(BaseModel):
    clip_ids: List[str]  # Must be adjacent clips
```

### APIs and Interfaces

**GET /api/editor/{generation_id}**
- **Description:** Load editor data for a video generation
- **Headers:** `Authorization: Bearer {jwt_token}`
- **Response (200 OK):**
```json
{
  "generation_id": "abc-123",
  "original_video_url": "/output/videos/abc-123.mp4",
  "original_video_path": "/var/www/backend/output/videos/abc-123.mp4",
  "clips": [
    {
      "clip_id": "clip-1",
      "scene_number": 1,
      "original_path": "/var/www/backend/output/temp/abc-123-scene-1.mp4",
      "clip_url": "/api/clips/abc-123/1",
      "duration": 5.0,
      "start_time": 0.0,
      "end_time": 5.0,
      "thumbnail_url": "/output/thumbnails/abc-123-scene-1.jpg",
      "text_overlay": {
        "text": "Your Time",
        "position": "top_center"
      }
    }
  ],
  "total_duration": 15.0,
  "aspect_ratio": "9:16",
  "framework": "AIDA"
}
```
- **Errors:** 401 (Unauthorized), 403 (Not owner), 404 (Generation not found)

**POST /api/editor/{generation_id}/trim**
- **Description:** Trim a clip by adjusting start/end points
- **Request Body:**
```json
{
  "clip_id": "clip-1",
  "trim_start": 0.5,
  "trim_end": 4.5
}
```
- **Response (200 OK):**
```json
{
  "message": "Clip trimmed successfully",
  "clip_id": "clip-1",
  "new_duration": 4.0,
  "updated_state": { /* editing_state JSON */ }
}
```

**POST /api/editor/{generation_id}/split**
- **Description:** Split a clip at specified time
- **Request Body:**
```json
{
  "clip_id": "clip-1",
  "split_time": 2.5
}
```
- **Response (200 OK):**
```json
{
  "message": "Clip split successfully",
  "original_clip_id": "clip-1",
  "new_clips": [
    {"clip_id": "clip-1a", "duration": 2.5},
    {"clip_id": "clip-1b", "duration": 2.5}
  ],
  "updated_state": { /* editing_state JSON */ }
}
```

**POST /api/editor/{generation_id}/merge**
- **Description:** Merge multiple adjacent clips
- **Request Body:**
```json
{
  "clip_ids": ["clip-1", "clip-2"]
}
```
- **Response (200 OK):**
```json
{
  "message": "Clips merged successfully",
  "merged_clip_id": "clip-1-2",
  "new_duration": 10.0,
  "updated_state": { /* editing_state JSON */ }
}
```

**POST /api/editor/{generation_id}/save**
- **Description:** Save current editing state
- **Response (200 OK):**
```json
{
  "message": "Editing session saved",
  "session_id": "session-xyz",
  "saved_at": "2025-11-15T10:30:00Z"
}
```

**POST /api/editor/{generation_id}/export**
- **Description:** Export edited video with all edits applied
- **Response (202 Accepted):**
```json
{
  "message": "Video export started",
  "export_id": "export-123",
  "status": "processing",
  "estimated_time_seconds": 30
}
```
- **Polling:** Use same status endpoint pattern as video generation (`GET /api/status/{export_id}`)

### Workflows and Sequencing

**Editor Access Workflows:**

**Workflow A: From Video Detail Page**
1. User clicks "Edit Video" button on video detail page (for completed videos only)
2. Frontend navigates to `/editor/{generation_id}` route
3. Frontend calls `GET /api/editor/{generation_id}` to load editor data
4. Backend verifies user ownership, loads generation record
5. Backend extracts scene clips from `temp_clip_paths` or reconstructs from `scene_plan`
6. Backend creates/loads editing session record
7. Backend returns editor data with all clip information
8. Frontend renders editor interface with timeline and video player, video pre-loaded

**Workflow B: From Navbar Tab**
1. User clicks "Editor" tab in navbar
2. Frontend navigates to `/editor` route (no generation_id)
3. Frontend renders editor interface in empty state (no video loaded)
4. User can browse gallery panel to add videos from their gallery
5. When user selects a video from gallery, frontend calls `GET /api/editor/{generation_id}` to load that video
6. Editor loads the selected video with all scene clips

**Timeline Rendering Workflow:**
1. Frontend receives clip data from editor API
2. Timeline component generates thumbnails (or requests from backend)
3. Timeline calculates clip positions based on durations
4. Timeline renders clips as visual blocks with thumbnails
5. User can click timeline to seek, drag playhead, zoom in/out
6. Timeline updates in real-time as edits are made

**Clip Trimming Workflow:**
1. User selects clip on timeline
2. Trim handles appear at clip start/end
3. User drags trim handle to adjust start/end time
4. Frontend validates trim points (within clip boundaries, minimum duration)
5. Frontend calls `POST /api/editor/{generation_id}/trim` with trim data
6. Backend validates request, updates editing session state
7. Backend returns updated state (trim not applied to video until export)
8. Frontend updates timeline to show trimmed clip duration
9. Preview player shows trimmed clip when playing

**Clip Splitting Workflow:**
1. User positions playhead within a clip
2. User clicks "Split" button or presses 'S' key
3. Frontend calls `POST /api/editor/{generation_id}/split` with clip_id and split_time
4. Backend validates split point (not at start/end, within clip duration)
5. Backend updates editing session: original clip replaced with two clips
6. Backend returns new clip structure
7. Frontend updates timeline to show two clips instead of one
8. Both clips can be edited independently

**Clip Merging Workflow:**
1. User selects multiple adjacent clips (Ctrl/Cmd + click)
2. User clicks "Merge" button
3. Frontend validates clips are adjacent
4. Frontend calls `POST /api/editor/{generation_id}/merge` with clip_ids
5. Backend validates adjacency, updates editing session
6. Backend returns merged clip structure
7. Frontend updates timeline to show single merged clip

**Export Workflow:**
1. User clicks "Export Video" button
2. Frontend calls `POST /api/editor/{generation_id}/export`
3. Backend creates export job, returns export_id
4. Backend processes export asynchronously:
   a. Load all clips from editing session state
   b. Apply trim operations to clips using MoviePy
   c. Handle split clips (already separated in state)
   d. Merge clips that were merged
   e. Concatenate all processed clips with transitions
   f. Apply audio layer (reuse from original or regenerate)
   g. Export final video to `/output/videos/edited-{generation_id}.mp4`
   h. Create new Generation record for edited version (or version field)
5. Frontend polls export status endpoint
6. When complete, frontend shows success, allows download of edited video

## Non-Functional Requirements

### Performance

**NFR-EDIT-001: Editor Load Time**
- Editor interface shall load within 2 seconds of clicking "Edit Video" button
- Editor data API response time: <500ms
- Timeline rendering with thumbnails: <1 second for videos with up to 5 clips

**NFR-EDIT-002: Timeline Performance**
- Timeline shall maintain 60fps during scrubbing and zoom operations
- Timeline updates shall be responsive (<100ms) when edits are applied
- Thumbnail generation: <200ms per clip (can be async/background)

**NFR-EDIT-003: Edit Operation Performance**
- Trim operation API response: <300ms (state update only, not video processing)
- Split operation API response: <300ms
- Merge operation API response: <300ms
- Export operation: <2 minutes for 15-second video with edits applied

**NFR-EDIT-004: Video Processing Performance**
- Clip trimming with MoviePy: <5 seconds per clip
- Clip splitting with MoviePy: <5 seconds per clip
- Clip merging with MoviePy: <10 seconds for 2 clips
- Final export processing: <90 seconds for 15-second video

### Security

**NFR-EDIT-005: Editor Access Control**
- Only video owner can access editor for their videos
- JWT token required for all editor endpoints
- User ownership verified on every editor operation
- Editing sessions are user-scoped (users cannot access others' sessions)

**NFR-EDIT-006: Data Protection**
- Original video files are preserved and not modified
- Editing state stored securely in database with user_id association
- Exported videos stored with same security as original videos
- No exposure of internal file paths to frontend

### Reliability/Availability

**NFR-EDIT-007: Editing Session Persistence**
- Editing sessions shall persist across browser refreshes
- Auto-save functionality: save editing state every 30 seconds (optional for MVP)
- Editing state recovery: users can resume editing from last saved state
- Original video backup: original video never modified, always restorable

**NFR-EDIT-008: Export Reliability**
- Export success rate: >95% (retry on transient failures)
- Export progress tracking: accurate progress updates every 5 seconds
- Export cancellation: best-effort cancellation support (similar to generation cancellation)
- Export failure recovery: clear error messages, ability to retry export

**NFR-EDIT-009: Data Integrity**
- Editing operations are atomic (all-or-nothing for complex operations)
- Database transactions ensure editing state consistency
- Export operations validate editing state before processing
- No data loss if export fails (editing state preserved)

### Observability

**NFR-EDIT-010: Editor Logging**
- Log all editor access attempts with user_id and generation_id
- Log all edit operations (trim, split, merge) with operation details
- Log export operations with timing and success/failure status
- Log errors with full context (user, generation, operation type)

**NFR-EDIT-011: Editor Metrics**
- Track editor usage: number of videos edited per user
- Track edit operation frequency: trim/split/merge counts
- Track export success rate and average export time
- Monitor editing session duration and abandonment rate

## Dependencies and Integrations

**Internal Dependencies:**
- Epic 1: Database infrastructure (SQLAlchemy, PostgreSQL), User model
- Epic 2: Authentication system (JWT tokens, protected routes)
- Epic 3: Video generation pipeline (scene clips, video storage, MoviePy integration)
- Epic 4: Video gallery and playback (video detail page, video URLs)

**External Dependencies:**
- MoviePy 1.0+ (already in tech stack): Required for video manipulation (trim, split, merge, concatenate)
- FFmpeg (already in tech stack): Required for video encoding/decoding in MoviePy operations
- React 18+ (frontend): Timeline rendering, component architecture
- Canvas API or SVG (frontend): Timeline visualization (performance requirement)

**New Dependencies:**
- No new external dependencies required (all tools already in tech stack)

**Integration Points:**
- Editor integrates with existing video storage (`/output/videos/`, `/output/temp/`)
- Editor uses existing authentication middleware (`get_current_user` dependency)
- Editor extends Generation model with editing_sessions relationship
- Editor reuses video processing utilities from Epic 3 (MoviePy helpers, file paths)

**Version Constraints:**
- MoviePy: Must support `subclip()`, `concatenate_videoclips()`, and video file I/O
- SQLAlchemy: Must support JSON column type for editing_state
- React: Must support canvas/SVG rendering and event handling for timeline

## Acceptance Criteria (Authoritative)

**AC-EDIT-001: Editor Access**
- Given a completed video on the video detail page
- When user clicks "Edit Video" button
- Then editor interface opens and loads video with all scene clips available
- And original video is preserved as backup
- And "Exit Editor" button returns to video detail page

**AC-EDIT-001B: Editor Access from Navbar**
- Given user is authenticated
- When user clicks "Editor" tab in navbar
- Then editor interface opens in empty state
- And gallery panel is visible showing user's videos
- And user can select videos from gallery to add to editor

**AC-EDIT-001C: Gallery Integration**
- Given user is in the editor
- When user browses gallery panel and selects a video
- Then that video is loaded into editor with all scene clips
- And video appears on timeline
- And user can add multiple videos from gallery to timeline

**AC-EDIT-002: Timeline Interface**
- Given user is in the video editor
- When editor loads
- Then timeline displays all video clips in sequence with thumbnails and durations
- And playhead shows current playback position
- And user can scrub timeline, zoom in/out, and select clips
- And timeline updates in real-time as edits are made

**AC-EDIT-003: Clip Trimming**
- Given user has selected a clip on timeline
- When user adjusts trim handles
- Then clip duration updates in real-time
- And preview shows trimmed clip content
- And system validates trim points (within boundaries, minimum 0.5s duration)
- And trim operation is saved to editing session

**AC-EDIT-004: Clip Splitting**
- Given user has positioned playhead within a clip
- When user clicks "Split" button
- Then clip is divided into two separate clips at split point
- And both clips appear on timeline
- And both clips can be edited independently
- And metadata (text overlays) is preserved for both clips

**AC-EDIT-005: Clip Merging**
- Given user has selected multiple adjacent clips
- When user clicks "Merge" button
- Then selected clips are combined into single continuous clip
- And merged clip appears as single entity on timeline
- And video content from all merged clips is preserved
- And transitions are applied between merged segments

**AC-EDIT-006: Editor Save**
- Given user has made edits to a video
- When user clicks "Save" or system auto-saves
- Then editing state is persisted to database
- And original video remains unchanged
- And user can return and continue editing later
- And "Saved" confirmation message is displayed

**AC-EDIT-007: Editor Export**
- Given user has edited a video and wants to export
- When user clicks "Export Video"
- Then system creates new video version with all edits applied
- And original video is maintained for comparison
- And exported video is in same format and quality as original (1080p MP4)
- And export progress is tracked and displayed
- And exported video is available for download when complete

## Traceability Mapping

| Acceptance Criteria | PRD Section | Epic Story | Component/API | Test Idea |
|---------------------|-------------|------------|---------------|-------------|
| AC-EDIT-001 | FR-024 | Story 6.1 | `GET /api/editor/{generation_id}`, `Editor.tsx`, `VideoDetail.tsx` | Test editor access from video detail page, verify clip loading |
| AC-EDIT-001B | FR-024 | Story 6.1 | `Navbar.tsx`, `Editor.tsx` | Test editor access from navbar, verify empty state |
| AC-EDIT-001C | FR-024 | Story 6.1 | `GalleryPanel.tsx`, `Editor.tsx` | Test gallery integration, verify video selection and loading |
| AC-EDIT-002 | FR-025 | Story 6.2 | `Timeline.tsx`, editor API | Test timeline rendering, scrubbing, zoom, clip selection |
| AC-EDIT-003 | FR-026 | Story 6.3 | `POST /api/editor/{generation_id}/trim`, `TrimControls.tsx` | Test trim handles, validation, preview updates |
| AC-EDIT-004 | FR-027 | Story 6.4 | `POST /api/editor/{generation_id}/split` | Test split operation, verify two clips created, metadata preserved |
| AC-EDIT-005 | FR-028 | Story 6.5 | `POST /api/editor/{generation_id}/merge` | Test merge operation, verify adjacency validation, content preservation |
| AC-EDIT-006 | FR-029 | Story 6.6 | `POST /api/editor/{generation_id}/save` | Test save functionality, session persistence, resume editing |
| AC-EDIT-007 | FR-029 | Story 6.6 | `POST /api/editor/{generation_id}/export`, export service | Test export workflow, progress tracking, video quality, original preservation |

**Component Traceability:**
- **Backend Routes:** `app/api/routes/editor.py` → AC-EDIT-001, AC-EDIT-003, AC-EDIT-004, AC-EDIT-005, AC-EDIT-006, AC-EDIT-007
- **Backend Services:** `app/services/editor/*.py` → AC-EDIT-003, AC-EDIT-004, AC-EDIT-005, AC-EDIT-007
- **Frontend Components:** `Editor.tsx`, `Timeline.tsx`, `VideoPlayer.tsx`, `TrimControls.tsx` → AC-EDIT-001, AC-EDIT-002, AC-EDIT-003
- **Data Models:** `EditingSession` model → AC-EDIT-001, AC-EDIT-006, AC-EDIT-007

## Risks, Assumptions, Open Questions

**Risks:**

**RISK-EDIT-001: Scene Clip Availability**
- **Risk:** Original scene clips may not be available if temp files were cleaned up
- **Impact:** High - Editor cannot function without individual scene clips
- **Mitigation:** 
  - Store scene clips in persistent location (not temp) when generation completes
  - Or reconstruct clips from final video using scene timing data (more complex)
  - Add validation on editor access to check clip availability
- **Status:** Open - Need to verify current clip storage strategy from Epic 3

**RISK-EDIT-002: Timeline Performance with Many Clips**
- **Risk:** Timeline may become slow with videos containing many clips (5+)
- **Impact:** Medium - Poor user experience
- **Mitigation:**
  - Use canvas/SVG for efficient rendering
  - Implement virtual scrolling for timeline
  - Lazy load thumbnails (only visible clips)
  - Optimize thumbnail generation (cache, lower resolution)
- **Status:** Assumed manageable for MVP (typically 3-5 clips)

**RISK-EDIT-003: Export Processing Time**
- **Risk:** Export may take too long, causing user frustration
- **Impact:** Medium - Users may abandon exports
- **Mitigation:**
  - Process export asynchronously (similar to video generation)
  - Show accurate progress updates
  - Allow export cancellation
  - Optimize MoviePy operations (use efficient codecs)
- **Status:** Acceptable for MVP (export is less frequent than generation)

**RISK-EDIT-004: Editing State Complexity**
- **Risk:** Editing state JSON may become complex and error-prone with many operations
- **Impact:** Medium - Data corruption, export failures
- **Mitigation:**
  - Use structured schema for editing_state
  - Validate editing state before export
  - Implement state versioning for migration support
  - Add comprehensive error handling
- **Status:** Manageable with careful design

**Assumptions:**

**ASSUMPTION-EDIT-001:** Scene clips are preserved after video generation completes (not deleted immediately)
**ASSUMPTION-EDIT-002:** MoviePy operations (trim, split, merge) are reliable and performant for clips up to 10 seconds
**ASSUMPTION-EDIT-003:** Users will primarily edit videos with 3-5 clips (typical scene count)
**ASSUMPTION-EDIT-004:** Desktop browser environment (mobile editor not required for MVP)
**ASSUMPTION-EDIT-005:** Original video files remain accessible throughout editing session

**Open Questions:**

**QUESTION-EDIT-001:** Should edited videos create new Generation records or use a versioning system?
- **Decision Needed:** New Generation record vs. version field on existing record
- **Recommendation:** New Generation record with `parent_generation_id` field for traceability

**QUESTION-EDIT-002:** How should we handle text overlays when clips are trimmed/split/merged?
- **Decision Needed:** Preserve overlays, remove them, or allow re-editing
- **Recommendation:** Preserve overlays for MVP, re-editing is post-MVP

**QUESTION-EDIT-003:** Should editing sessions have expiration (auto-cleanup)?
- **Decision Needed:** Session retention policy
- **Recommendation:** Keep sessions indefinitely for MVP, add cleanup later if needed

**QUESTION-EDIT-004:** Should we support editing videos that are still processing?
- **Decision Needed:** Editor access rules
- **Recommendation:** Only allow editing of completed videos (status="completed")

## Test Strategy Summary

**Unit Tests:**
- Editor service functions: trim, split, merge operations with MoviePy
- Editing state validation and serialization
- API request/response schemas (Pydantic models)
- Timeline component rendering and interaction logic
- Trim controls validation logic

**Integration Tests:**
- Editor API endpoints with authentication
- Editing session creation and persistence
- Editor data loading from generation records
- Export workflow end-to-end (edit → export → verify video)

**E2E Tests:**
- User flow: Access editor → Trim clip → Split clip → Merge clips → Export
- Editor save and resume functionality
- Original video preservation verification
- Export progress tracking and completion

**Performance Tests:**
- Timeline rendering performance with 5 clips
- Editor load time (<2 seconds)
- Export processing time (<2 minutes for 15s video)
- API response times for edit operations

**Security Tests:**
- Editor access control (only owner can edit)
- Editing session isolation (users cannot access others' sessions)
- JWT token validation on all endpoints

**Test Coverage Target:** >80% for editor-specific code (services, routes, components)

