# Epic Technical Specification: Video Management

Date: 2025-11-14
Author: BMad
Epic ID: epic-4
Status: Draft

---

## Overview

Epic 4: Video Management enables users to view, play, download, search, and delete their generated videos through an intuitive gallery interface. This epic builds upon the video generation pipeline (Epic 3) by providing the essential user-facing features needed to manage and consume generated video content. The epic covers four stories: Video Gallery (4.1), Video Playback and Download (4.2), Video Deletion (4.3), and Video Search (4.4 - optional).

This epic directly addresses functional requirements FR-017 through FR-021 from the PRD, focusing on the post-generation user experience. Users need to be able to browse their video history, preview videos before downloading, download videos for use in marketing campaigns, and manage their video library by deleting unwanted content. The optional search feature enhances discoverability for users with large video collections.

## Objectives and Scope

**In-Scope:**
- Backend API endpoints for listing user's videos with pagination, filtering, and search
- Backend endpoint for streaming video files with range request support
- Backend endpoint for deleting videos (files and database records)
- Frontend gallery page with responsive grid layout displaying video thumbnails and metadata
- Frontend video detail page with HTML5 video player
- Frontend download functionality for completed videos
- Frontend deletion flow with confirmation dialog
- Frontend search and filter capabilities (optional story 4.4)
- User authorization checks ensuring users can only access their own videos
- Proper error handling and user feedback for all operations

**Out-of-Scope:**
- Video editing or regeneration from gallery (covered in Epic 3)
- Video sharing with other users (post-MVP feature)
- Video analytics or view tracking (post-MVP feature)
- Bulk operations (bulk delete, bulk download) - MVP supports single-item operations only
- Video metadata editing (prompt changes, title changes)
- Video organization features (folders, tags, collections)

## System Architecture Alignment

This epic aligns with the existing architecture by extending the FastAPI backend with new routes in `app/api/routes/generations.py` and creating corresponding frontend components in `frontend/src/routes/Gallery.tsx` and `frontend/src/routes/VideoDetail.tsx`. The implementation leverages:

- **Existing Components:**
  - `Generation` model (already includes all required fields: video_url, thumbnail_url, status, prompt, cost, dates)
  - `User` model (for ownership verification)
  - JWT authentication middleware (from Epic 2)
  - File storage structure (`/output/videos/` for video files, `/output/thumbnails/` for thumbnails)

- **New Components:**
  - `GET /api/generations` endpoint with query parameters for pagination, filtering, and search
  - `GET /api/video/{generation_id}` endpoint for video streaming with range request support
  - `DELETE /api/generations/{id}` endpoint for video deletion
  - Frontend `Gallery.tsx` component with grid layout, pagination, and filters
  - Frontend `VideoDetail.tsx` component with video player and download/delete actions

- **Constraints:**
  - Videos are stored on local disk (`/output/videos/`) with paths stored in database
  - Nginx serves video files directly (configured in deployment)
  - All endpoints require JWT authentication
  - User ownership must be verified on every request

## Detailed Design

### Services and Modules

| Module/Service | Responsibility | Inputs | Outputs | Owner |
|---------------|---------------|--------|---------|-------|
| `app/api/routes/generations.py` | Gallery listing endpoint | Query params (limit, offset, status, q), JWT user | Paginated list of Generation records | Backend |
| `app/api/routes/generations.py` | Video streaming endpoint | generation_id, JWT user, HTTP Range header | Video file stream with proper headers | Backend |
| `app/api/routes/generations.py` | Video deletion endpoint | generation_id, JWT user | Success/error response | Backend |
| `app/schemas/generation.py` | Pydantic schemas for request/response | Raw data | Validated Generation schemas | Backend |
| `app/db/models/generation.py` | Generation ORM model | Database queries | Generation objects | Backend (existing) |
| `frontend/src/routes/Gallery.tsx` | Gallery page component | User auth state | Rendered gallery grid with videos | Frontend |
| `frontend/src/routes/VideoDetail.tsx` | Video detail page component | generation_id from route | Rendered video player with metadata | Frontend |
| `frontend/src/components/ui/VideoCard.tsx` | Reusable video card component | Generation data | Rendered video thumbnail card | Frontend |
| `frontend/src/lib/apiClient.ts` | API client with interceptors | API requests | HTTP responses with error handling | Frontend (existing) |

### Data Models and Contracts

**Generation Model (Existing - No Changes Required):**
```python
class Generation(Base):
    id: str (UUID, primary key)
    user_id: str (UUID, foreign key to users.id, indexed)
    prompt: str (Text, required)
    status: str (pending|processing|completed|failed, indexed)
    video_url: str (nullable, path to video file)
    thumbnail_url: str (nullable, path to thumbnail image)
    duration: int (seconds)
    cost: float (nullable, USD)
    created_at: datetime (indexed)
    completed_at: datetime (nullable)
    # ... other fields from existing model
```

**Pydantic Response Schemas (New):**
```python
class GenerationListItem(BaseModel):
    id: str
    prompt: str
    status: str
    video_url: Optional[str]
    thumbnail_url: Optional[str]
    duration: int
    cost: Optional[float]
    created_at: datetime
    completed_at: Optional[datetime]

class GenerationListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    generations: List[GenerationListItem]
```

**Database Queries:**
- Gallery listing: `SELECT * FROM generations WHERE user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?`
- With status filter: Add `AND status = ?` clause
- With search: Add `AND prompt ILIKE ?` clause (PostgreSQL) or `AND prompt LIKE ?` (SQLite)
- Deletion: `DELETE FROM generations WHERE id = ? AND user_id = ?` (ownership check)

### APIs and Interfaces

**GET /api/generations**
- **Method:** GET
- **Auth:** Required (JWT Bearer token)
- **Query Parameters:**
  - `limit` (int, default: 20, max: 100): Number of results per page
  - `offset` (int, default: 0): Pagination offset
  - `status` (string, optional): Filter by status (completed, processing, failed, pending)
  - `q` (string, optional): Search term for prompt text (case-insensitive substring match)
  - `sort` (string, default: "created_at_desc"): Sort order
- **Response (200 OK):**
```json
{
  "total": 45,
  "limit": 20,
  "offset": 0,
  "generations": [
    {
      "id": "abc-123-def-456",
      "prompt": "Luxury watch ad...",
      "status": "completed",
      "video_url": "/output/videos/abc-123-def-456.mp4",
      "thumbnail_url": "/output/thumbnails/abc-123-def-456.jpg",
      "duration": 15,
      "cost": 1.87,
      "created_at": "2025-11-14T10:30:00Z",
      "completed_at": "2025-11-14T10:33:45Z"
    }
  ]
}
```
- **Errors:**
  - 401: Unauthorized (invalid/missing token)
  - 422: Validation error (invalid query parameters)

**GET /api/video/{generation_id}**
- **Method:** GET
- **Auth:** Required (JWT Bearer token)
- **Path Parameters:**
  - `generation_id` (string, UUID): Generation ID
- **Headers:**
  - `Range` (optional): HTTP range request header for video seeking (e.g., "bytes=0-1023")
- **Response (200 OK):**
  - Content-Type: `video/mp4`
  - Content-Disposition: `attachment; filename="ad_{generation_id}.mp4"`
  - Accept-Ranges: `bytes`
  - Content-Length: Video file size (if no Range header)
  - Content-Range: Byte range (if Range header present)
  - Binary video data
- **Errors:**
  - 401: Unauthorized
  - 404: Video not found or user doesn't own it
  - 400: Video not ready yet (status != "completed")
  - 416: Range not satisfiable (invalid Range header)

**DELETE /api/generations/{id}**
- **Method:** DELETE
- **Auth:** Required (JWT Bearer token)
- **Path Parameters:**
  - `id` (string, UUID): Generation ID
- **Response (200 OK):**
```json
{
  "message": "Video deleted successfully",
  "generation_id": "abc-123-def-456"
}
```
- **Errors:**
  - 401: Unauthorized
  - 404: Video not found
  - 403: Not authorized to delete this video (user doesn't own it)
  - 500: File deletion failed (file not found on disk is acceptable, log warning)

### Workflows and Sequencing

**Gallery Page Load Flow:**
1. User navigates to `/gallery` route
2. Frontend `Gallery.tsx` component mounts
3. Component calls `GET /api/generations?limit=20&offset=0` with JWT token
4. Backend verifies JWT, extracts user_id
5. Backend queries database: `SELECT * FROM generations WHERE user_id = ? ORDER BY created_at DESC LIMIT 20 OFFSET 0`
6. Backend returns paginated list
7. Frontend renders grid layout with video cards
8. Each card displays thumbnail, status badge, prompt preview, cost, date

**Video Playback Flow:**
1. User clicks video thumbnail in gallery
2. Frontend navigates to `/gallery/{generation_id}`
3. `VideoDetail.tsx` component mounts, calls `GET /api/generations?limit=1&offset=0` (or dedicated detail endpoint if added)
4. Backend returns single generation record
5. Frontend renders HTML5 `<video>` element with `src={video_url}`
6. Browser requests video file via Nginx (served from `/output/videos/`)
7. Video player displays with controls, metadata shown below player

**Video Download Flow:**
1. User clicks "Download" button on video detail page
2. Frontend creates anchor element: `<a href={video_url} download={`ad_${generation_id}.mp4`}>`
3. Frontend programmatically clicks anchor
4. Browser downloads file via Nginx (served from `/output/videos/`)
5. File saved with proper filename

**Video Deletion Flow:**
1. User clicks "Delete" button on video detail page
2. Frontend shows confirmation dialog: "Are you sure you want to delete this video? This action cannot be undone."
3. User confirms deletion
4. Frontend calls `DELETE /api/generations/{id}` with JWT token
5. Backend verifies JWT and ownership (user_id matches generation.user_id)
6. Backend deletes video file from disk: `os.remove(video_path)` (ignore FileNotFoundError)
7. Backend deletes thumbnail file: `os.remove(thumbnail_path)` (ignore FileNotFoundError)
8. Backend deletes database record: `db.delete(generation)`
9. Backend commits transaction
10. Backend returns success response
11. Frontend redirects to `/gallery` with success message

**Search/Filter Flow:**
1. User types in search bar (debounced 300ms)
2. Frontend calls `GET /api/generations?q={search_term}&status={filter_status}`
3. Backend applies search filter: `WHERE user_id = ? AND prompt ILIKE ? AND status = ?`
4. Backend returns filtered results
5. Frontend updates gallery display with filtered videos
6. If no results, frontend shows "No videos found" message

## Non-Functional Requirements

### Performance

**Gallery Load Performance:**
- Gallery page with 20 videos: <1 second to load (per PRD NFR-002)
- Database query with filters: <200ms
- Thumbnail image loading: Lazy load as user scrolls
- Pagination: Load next page on "Load More" click (not infinite scroll for MVP)

**Video Streaming Performance:**
- Video file serving: <2 seconds to first frame (per PRD NFR-002)
- Range request support: Required for video seeking (HTML5 video player requirement)
- Video file size: Typically 5-50MB per video (1080p, 15-60 seconds)
- Concurrent video streams: Support at least 10 concurrent users streaming videos

**Search Performance:**
- Search query response: <500ms for substring search on prompt field
- Database index: Ensure `prompt` field is searchable (full-text search not required for MVP, ILIKE/LIKE is sufficient)

### Security

**Authentication & Authorization:**
- All endpoints require valid JWT token (from Epic 2)
- User ownership verification: Every request must verify `generation.user_id == current_user.id`
- Video file access: Only video owner can access video files
- SQL injection prevention: Use SQLAlchemy ORM parameterized queries (no raw SQL)

**File Access Security:**
- Video file paths: Never expose absolute file system paths to frontend
- Path traversal prevention: Validate generation_id is valid UUID, verify ownership before file access
- File deletion: Only delete files owned by requesting user

**Input Validation:**
- Query parameters: Validate limit (1-100), offset (>=0), status (enum), q (string, max 500 chars)
- Generation ID: Must be valid UUID format
- Search term: Sanitize to prevent injection (SQLAlchemy handles this, but validate length)

### Reliability/Availability

**Error Handling:**
- Missing video files: If video file not found on disk but record exists, return 404 (file may have been manually deleted)
- Database errors: Return 500 with user-friendly message, log full error server-side
- Network errors: Frontend shows retry option for failed API calls
- Partial failures: If thumbnail deletion fails but video deletion succeeds, log warning but return success

**Data Consistency:**
- Deletion transaction: Delete database record and files atomically (if file deletion fails, rollback database deletion)
- Orphaned files: Acceptable for MVP (files may exist without database records if deletion partially fails)

**Availability:**
- Gallery endpoint: Must be available even if some video files are missing (show videos with "File not found" status)
- Video streaming: Graceful degradation if file missing (404 error)

### Observability

**Logging Requirements:**
- Gallery requests: Log user_id, query parameters, result count
- Video access: Log generation_id, user_id, file size served
- Deletions: Log generation_id, user_id, success/failure, file deletion status
- Search queries: Log search term, result count, execution time

**Metrics to Track:**
- Gallery page load time
- Video streaming start time (time to first byte)
- Deletion success rate
- Search query performance
- API error rates by endpoint

**Error Logging:**
- All 4xx and 5xx errors logged with full context
- File system errors (FileNotFoundError, PermissionError) logged with file path
- Database errors logged with query details (sanitized)

## Dependencies and Integrations

**Backend Dependencies:**
- FastAPI 0.104+ (existing)
- SQLAlchemy 2.0+ (existing)
- Pydantic (existing, for request/response validation)
- Python standard library: `os` (for file deletion), `pathlib` (for path handling)

**Frontend Dependencies:**
- React 18+ (existing)
- React Router 6+ (existing, for routing to `/gallery` and `/gallery/:id`)
- Axios 1.6+ (existing, for API calls)
- Zustand 4.4+ (existing, for auth state)

**External Services:**
- None (all operations are local (database queries, file system operations))
- Nginx (existing, serves video files from `/output/videos/` directory)

**Database:**
- PostgreSQL (production) or SQLite (development) - existing
- Indexes required: `user_id` (existing), `status` (existing), `created_at` (existing)
- No new indexes required for MVP (ILIKE search on prompt is acceptable without full-text index)

**File System:**
- Video files stored at: `/output/videos/{generation_id}.mp4` (or path from `video_path` field)
- Thumbnail files stored at: `/output/thumbnails/{generation_id}.jpg` (or path from `thumbnail_url` field)
- Nginx configured to serve `/output/` directory (existing from Epic 1)

## Acceptance Criteria (Authoritative)

**AC-4.1.1:** Backend returns paginated list of user's videos
- **Given** I am logged in
- **When** I request `GET /api/generations?limit=20&offset=0`
- **Then** I receive a response with `total`, `limit`, `offset`, and `generations` array
- **And** only my videos are returned (user_id matches JWT token)
- **And** results are sorted by `created_at DESC` (newest first)

**AC-4.1.2:** Frontend displays gallery in responsive grid
- **Given** I am on the gallery page
- **When** the page loads with video data
- **Then** I see a grid layout (1 column mobile, 2-3 tablet, 4+ desktop)
- **And** each video card shows thumbnail, status badge, prompt preview, cost, and date

**AC-4.1.3:** Gallery supports pagination
- **Given** I have more than 20 videos
- **When** I view the gallery
- **Then** I see a "Load More" button or pagination controls
- **And** clicking loads the next page of results

**AC-4.1.4:** Gallery supports status filtering
- **Given** I have videos with different statuses
- **When** I select a status filter (All, Completed, Processing, Failed)
- **Then** the gallery shows only videos matching that status
- **And** the filter persists when loading more pages

**AC-4.2.1:** Video playback serves file with range support
- **Given** I have a completed video
- **When** I request `GET /api/video/{generation_id}` with Range header
- **Then** the server responds with 206 Partial Content and the requested byte range
- **And** the video file is served with proper Content-Type headers

**AC-4.2.2:** Frontend displays video player
- **Given** I am on a video detail page
- **When** the page loads
- **Then** I see an HTML5 video player with controls
- **And** the video loads and plays correctly
- **And** the player supports different aspect ratios (9:16, 16:9, 1:1)

**AC-4.2.3:** Video download works correctly
- **Given** I am viewing a completed video
- **When** I click the download button
- **Then** the browser downloads the video file
- **And** the filename is `ad_{generation_id}.mp4`

**AC-4.3.1:** Video deletion removes files and database record
- **Given** I own a video
- **When** I request `DELETE /api/generations/{id}`
- **Then** the video file is deleted from disk
- **And** the thumbnail file is deleted from disk
- **And** the database record is deleted
- **And** I receive a success response

**AC-4.3.2:** Deletion requires confirmation
- **Given** I am viewing a video
- **When** I click the delete button
- **Then** a confirmation dialog appears
- **And** deletion only proceeds if I confirm
- **And** I am redirected to gallery after successful deletion

**AC-4.3.3:** Only video owner can delete
- **Given** I try to delete a video I don't own
- **When** I request `DELETE /api/generations/{id}`
- **Then** I receive a 403 Forbidden error
- **And** the video is not deleted

**AC-4.4.1:** Search filters videos by prompt text (Optional)
- **Given** I have multiple videos
- **When** I enter search text in the search bar
- **Then** the gallery shows only videos where prompt contains the search text (case-insensitive)
- **And** results update in real-time (debounced 300ms)

**AC-4.4.2:** Search works with status filter (Optional)
- **Given** I have videos with different statuses and prompts
- **When** I enter search text and select a status filter
- **Then** both filters are applied (AND logic)
- **And** only videos matching both criteria are shown

## Traceability Mapping

| AC ID | Spec Section | Component/API | Test Idea |
|-------|--------------|---------------|-----------|
| AC-4.1.1 | APIs: GET /api/generations | `app/api/routes/generations.py` | Test pagination, user filtering, sorting |
| AC-4.1.2 | Workflows: Gallery Page Load | `frontend/src/routes/Gallery.tsx` | Test responsive grid rendering, video card display |
| AC-4.1.3 | Workflows: Gallery Page Load | `frontend/src/routes/Gallery.tsx` | Test pagination button, load more functionality |
| AC-4.1.4 | APIs: GET /api/generations | `app/api/routes/generations.py`, `frontend/src/routes/Gallery.tsx` | Test status filter query param, frontend filter UI |
| AC-4.2.1 | APIs: GET /api/video/{generation_id} | `app/api/routes/generations.py` | Test range request handling, video file serving |
| AC-4.2.2 | Workflows: Video Playback Flow | `frontend/src/routes/VideoDetail.tsx` | Test video player rendering, aspect ratio handling |
| AC-4.2.3 | Workflows: Video Download Flow | `frontend/src/routes/VideoDetail.tsx` | Test download button, filename generation |
| AC-4.3.1 | APIs: DELETE /api/generations/{id} | `app/api/routes/generations.py` | Test file deletion, database deletion, transaction |
| AC-4.3.2 | Workflows: Video Deletion Flow | `frontend/src/routes/VideoDetail.tsx` | Test confirmation dialog, redirect after deletion |
| AC-4.3.3 | APIs: DELETE /api/generations/{id} | `app/api/routes/generations.py` | Test ownership verification, 403 error |
| AC-4.4.1 | APIs: GET /api/generations, Workflows: Search/Filter | `app/api/routes/generations.py`, `frontend/src/routes/Gallery.tsx` | Test search query param, debounced search input |
| AC-4.4.2 | APIs: GET /api/generations | `app/api/routes/generations.py` | Test combined search and status filter |

## Risks, Assumptions, Open Questions

**Risk: Large Video Files Impact Performance**
- **Description:** Serving large video files (50MB+) may slow down server or consume bandwidth
- **Likelihood:** Medium
- **Impact:** Medium
- **Mitigation:** Use Nginx to serve video files directly (not through FastAPI), implement range requests for efficient streaming, consider CDN for post-MVP

**Risk: Orphaned Files After Failed Deletions**
- **Description:** If database deletion succeeds but file deletion fails, files remain on disk
- **Likelihood:** Low
- **Impact:** Low (storage waste, but doesn't break functionality)
- **Mitigation:** Accept for MVP, implement cleanup job post-MVP, log warnings for manual cleanup

**Risk: Search Performance Degrades with Large Datasets**
- **Description:** ILIKE search on prompt field may be slow with thousands of videos per user
- **Likelihood:** Low (MVP scale: <1000 videos per user)
- **Impact:** Low for MVP
- **Mitigation:** Acceptable for MVP, implement full-text search index post-MVP if needed

**Assumption: Video Files Always Exist When Status is "completed"**
- **Description:** We assume that if `status == "completed"` and `video_url` is set, the file exists on disk
- **Validity:** May not be true if files are manually deleted or disk fails
- **Handling:** Return 404 if file not found, log error, show user-friendly message

**Assumption: Nginx is Configured to Serve /output/ Directory**
- **Description:** We assume Nginx is already configured to serve video files (from Epic 1)
- **Validity:** Should be verified in deployment
- **Handling:** Verify Nginx config includes `/output/` location block

**Question: Should We Implement Video Detail Endpoint?**
- **Current Approach:** Use `GET /api/generations?limit=1` to get single video
- **Alternative:** Create dedicated `GET /api/generations/{id}` endpoint
- **Decision:** Use existing endpoint for MVP, add dedicated endpoint if needed for performance

**Question: How to Handle Videos in "processing" Status in Gallery?**
- **Description:** Should processing videos show in gallery with different UI?
- **Decision:** Yes, show all videos with status badges, allow clicking to see progress

## Test Strategy Summary

**Unit Tests:**
- Backend: Test query building with filters, pagination logic, ownership verification
- Frontend: Test component rendering, API client calls, state management

**Integration Tests:**
- Backend: Test full API endpoints with database, file system operations
- Frontend: Test gallery page with mock API responses, video player functionality

**End-to-End Tests:**
- User flow: Login → Generate video → View in gallery → Play video → Download video → Delete video
- Search flow: Enter search term → Verify filtered results → Clear search → Verify all videos shown

**Performance Tests:**
- Gallery load time with 100+ videos
- Video streaming start time
- Search query performance with large datasets

**Security Tests:**
- Attempt to access another user's videos (should return 404 or empty list)
- Attempt to delete another user's video (should return 403)
- Verify JWT token required for all endpoints

**Error Handling Tests:**
- Missing video file (404 response)
- Invalid generation_id (404 response)
- Network errors (frontend retry logic)
- Database errors (500 response with user-friendly message)

