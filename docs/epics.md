# ad-mint-ai - Epic Breakdown

**Author:** BMad
**Date:** 2025-11-14
**Project Level:** Intermediate
**Target Scale:** MVP

---

## Overview

This document provides the complete epic and story breakdown for ad-mint-ai, decomposing the requirements from the [PRD](./PRD.md) into implementable stories.

**Living Document Notice:** This is the initial version. It will be updated after UX Design and Architecture workflows add interaction and technical details to stories.

---

## Functional Requirements Inventory

- **FR-001:** User Registration - System shall allow users to create accounts with username and password
- **FR-002:** User Login - System shall authenticate users via username/password and generate JWT token
- **FR-003:** Protected Routes - System shall restrict access to authenticated users only
- **FR-004:** User Logout - System shall clear JWT token from client storage
- **FR-005:** Simple Prompt Input - System shall accept text prompt (10-500 characters)
- **FR-006:** LLM Enhancement - System shall send prompt to LLM and generate complete ad specification JSON
- **FR-007:** Framework Selection - System shall automatically select best advertising framework (PAS, BAB, or AIDA)
- **FR-008:** Scene Planning - System shall break video into 3-5 scenes based on framework
- **FR-009:** Video Clip Generation - System shall generate video clips using Replicate API
- **FR-010:** Text Overlay Addition - System shall add text overlays to video clips
- **FR-011:** Video Stitching - System shall concatenate all scene clips with transitions
- **FR-012:** Audio Layer - System shall select and add background music and sound effects
- **FR-013:** Post-Processing - System shall apply color grading and export final video (1080p minimum)
- **FR-014:** Progress Tracking - System shall update database with current status and progress %
- **FR-015:** Cost Calculation - System shall track total cost per generation
- **FR-016:** Cancel Generation (Best-Effort) - System shall allow users to request cancellation of in-progress generation
- **FR-017:** Video Gallery - System shall display all user's generated videos in grid layout
- **FR-018:** Video Playback - System shall serve video files from storage with HTML5 player
- **FR-019:** Video Download - System shall allow users to download MP4 files
- **FR-020:** Video Deletion - System shall allow users to delete their videos with confirmation
- **FR-021:** Video Search - System shall filter videos by prompt text and status (optional)
- **FR-022:** Profile Display - System shall show user statistics (total videos, cost, dates)
- **FR-023:** User Stats Update - System shall increment total_generations and update total_cost

---

## FR Coverage Map

- **Epic 1 (Foundation):** Covers infrastructure needs for all FRs - project setup, database, deployment pipeline
- **Epic 2 (User Authentication):** FR-001, FR-002, FR-003, FR-004
- **Epic 3 (Video Generation Pipeline):** FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-016
- **Epic 4 (Video Management):** FR-017, FR-018, FR-019, FR-020, FR-021
- **Epic 5 (User Profile):** FR-022, FR-023

---

## Epic 1: Foundation & Infrastructure

**Goal:** Establish the foundational infrastructure, project structure, database setup, and deployment pipeline that enables all subsequent development work.

### Story 1.1: Project Setup and Repository Structure

As a developer,
I want a well-organized project structure with proper configuration files,
So that the codebase is maintainable and follows best practices.

**Acceptance Criteria:**

**Given** a new project repository
**When** I clone and examine the project structure
**Then** I see frontend directory with React + TypeScript + Vite, backend directory with Python + FastAPI, and proper configuration files

**And** the project includes:
- `package.json` with React 18+, TypeScript 5+, Vite 5+, Tailwind CSS 3.3+
- `requirements.txt` with Python 3.11+, FastAPI 0.104+, SQLAlchemy 2.0+
- TypeScript configuration with strict mode enabled
- ESLint and Prettier configuration for code quality
- Basic folder structure for components, services, utilities

**Prerequisites:** None (this is the first story)

**Technical Notes:** Initialize React app with Vite, set up Python virtual environment, configure Tailwind CSS, create basic folder structure

---

### Story 1.2: Database Schema and Models

As a developer,
I want database models for users and video generations,
So that I can store and retrieve user data and generation records.

**Acceptance Criteria:**

**Given** a database connection is configured
**When** I run database migrations
**Then** the following tables are created:
- `users` table with fields: id (UUID), username (unique, indexed), password_hash, email (optional), total_generations, total_cost, created_at, last_login
- `generations` table with fields: id (UUID), user_id (FK, indexed), prompt, duration, aspect_ratio, status (indexed), progress, current_step, video_path, video_url, thumbnail_url, framework, num_scenes, generation_time_seconds, cost, error_message, created_at (indexed), completed_at

**And** the models include:
- SQLAlchemy ORM models with proper relationships
- Indexes on frequently queried fields (user_id, status, created_at)
- Proper data types (String, Integer, Float, DateTime, Text)
- UUID primary keys generated automatically

**Prerequisites:** Story 1.1

**Technical Notes:** Use SQLAlchemy 2.0+, support SQLite for development and PostgreSQL for production, add proper foreign key constraints

---

### Story 1.3: API Infrastructure Setup

As a developer,
I want a complete API infrastructure with backend server and frontend client,
So that the frontend and backend can communicate securely.

**Acceptance Criteria:**

**Backend:**
**Given** the FastAPI server is running
**When** I make a GET request to `/api/health`
**Then** I receive a 200 OK response with health status

**And** CORS is configured to allow requests from frontend origin, support credentials, and allow common HTTP methods

**Frontend:**
**Given** the frontend application is running
**When** I examine the API client configuration
**Then** I see Axios instance with interceptors for JWT tokens and error handling

**And** the client includes:
- TypeScript types for API request/response models
- Centralized API endpoint constants
- Proper error types (NetworkError, AuthError, ValidationError)
- Request interceptor that adds JWT token to Authorization header
- Response interceptor that handles 401 errors (redirects to login)

**Prerequisites:** Story 1.1

**Technical Notes:** 
- Backend: Set up FastAPI with CORS middleware, create basic router structure, configure environment variables, set up structured logging
- Frontend: Set up Axios with interceptors, create API service modules, configure Zustand store for auth state, configure Vite environment variables

---

### Story 1.4: Deployment Pipeline Basics

As a developer,
I want basic deployment scripts and configuration,
So that I can deploy the application to AWS EC2.

**Acceptance Criteria:**

**Given** I have an AWS EC2 instance with Ubuntu 22.04
**When** I run the deployment script
**Then** the script:
- Installs system dependencies (Python 3.11, Node.js, FFmpeg, Nginx)
- Sets up Python virtual environment and installs dependencies
- Builds the React frontend (`npm run build`)
- Configures Nginx to serve static files and proxy API requests
- Creates systemd service for FastAPI backend
- Starts all services

**And** the deployment includes:
- Basic Nginx configuration file
- Systemd service file for FastAPI
- Deployment script (`deploy.sh`) with error handling
- Environment variable template (`.env.example`)

**Prerequisites:** Story 1.1, Story 1.2, Story 1.3

**Technical Notes:** Create deployment documentation, set up Nginx reverse proxy, configure systemd service with auto-restart, set up log rotation

---

## Epic 2: User Authentication

**Goal:** Enable users to create accounts, log in securely, and access protected features using JWT-based authentication.

### Story 2.1: Authentication Backend

As a user,
I want to register, log in, and have my requests authenticated,
So that I can securely access the video generation features.

**Acceptance Criteria:**

**Registration:**
**Given** I submit a registration form with valid username and password
**When** the system processes the request
**Then** a new user account is created with hashed password and unique username validation

**Login:**
**Given** I have a registered account
**When** I submit valid login credentials
**Then** the system generates a JWT token and returns it with user information

**Protected Routes:**
**Given** a protected API endpoint
**When** a request includes a valid JWT token
**Then** the middleware verifies the token and allows the request to proceed

**And** all endpoints return proper error messages for invalid credentials or expired tokens

**Prerequisites:** Story 1.2, Story 1.3

**Technical Notes:** 
- Use Pydantic for validation, bcrypt for password hashing
- Use PyJWT for token generation, verify password with Passlib
- Create FastAPI dependency for authentication, verify token signature and expiration
- Update last_login timestamp on successful login

---

### Story 2.2: Authentication Frontend

As a user,
I want registration and login forms,
So that I can create an account and authenticate through the web interface.

**Acceptance Criteria:**

**Registration:**
**Given** I am on the registration page
**When** I view and submit the registration form
**Then** I see real-time validation feedback and can successfully create an account

**Login:**
**Given** I am on the login page
**When** I submit valid credentials
**Then** I am authenticated and redirected to the dashboard

**And** both forms include:
- Client-side validation with proper error messages
- Loading states during API requests
- Success/error feedback
- Mobile-responsive design

**Prerequisites:** Story 1.3, Story 2.1

**Technical Notes:** Create React components with form handling, implement client-side validation, use Tailwind CSS, use Zustand for auth state, store token in localStorage

---

### Story 2.3: Protected Routes Frontend

As a user,
I want protected pages that require authentication,
So that only logged-in users can access video generation features.

**Acceptance Criteria:**

**Given** I am not logged in
**When** I try to access a protected route (e.g., `/dashboard`, `/gallery`)
**Then** I am redirected to `/login` page
**And** the original URL is saved for redirect after login

**Given** I am logged in
**When** I access a protected route
**Then** the page loads normally
**And** I can see my username in the navigation

**And** the application includes:
- Protected route wrapper component that checks authentication
- Navigation bar with logout button (when authenticated)
- Automatic token refresh handling (if implemented)
- Graceful handling of expired tokens (redirect to login)

**Prerequisites:** Story 2.2

**Technical Notes:** Create ProtectedRoute component, check auth state from Zustand store, use React Router's Navigate component for redirects

---

### Story 2.4: Logout Functionality

As a user,
I want to log out of my account,
So that my session is cleared and I return to the login page.

**Acceptance Criteria:**

**Given** I am logged in
**When** I click the logout button
**Then** the system:
- Clears JWT token from localStorage/sessionStorage
- Clears user state from Zustand store
- Redirects to login page
- Shows success message (optional: "You have been logged out")

**And** after logout:
- Protected routes redirect to login
- API requests no longer include Authorization header
- User must log in again to access protected features

**Prerequisites:** Story 2.2, Story 2.3

**Technical Notes:** Create logout function in auth service, update Zustand store to reset auth state, clear Axios default headers

---

## Epic 3: Video Generation Pipeline

**Goal:** Implement the complete AI-powered video generation pipeline from user prompt to final video output.

### Story 3.1: Prompt Processing and Planning

As a user,
I want to enter a text prompt and have it processed into a video plan,
So that the system can generate a video based on my description.

**Acceptance Criteria:**

**Prompt Input:**
**Given** I am on the dashboard
**When** I enter a valid prompt (10-500 characters) and submit
**Then** the system validates the input and starts video generation

**LLM Enhancement:**
**Given** a user prompt
**When** the LLM enhancement service processes it
**Then** it returns structured JSON with product description, brand guidelines, framework selection, and ad specifications

**Scene Planning:**
**Given** LLM-generated ad specification with framework
**When** the scene planning module processes it
**Then** it generates scene breakdown with visual prompts, text overlays, and durations

**Prerequisites:** Story 2.3

**Technical Notes:** 
- Create dashboard component with prompt input, implement client-side validation
- Create llm_service.py module, use OpenAI/Claude API, validate response with Pydantic
- Create scene_planner.py module, implement framework-specific scene templates (AIDA, PAS, BAB)

---

### Story 3.2: Video Generation and Text Overlays

As a developer,
I want to generate video clips and add text overlays,
So that each scene becomes a complete video clip with branding.

**Acceptance Criteria:**

**Video Clip Generation:**
**Given** a scene with visual prompt and duration
**When** the video generation service processes it
**Then** it generates a video clip using Replicate API and downloads it to temp storage

**Text Overlay Addition:**
**Given** a video clip and text overlay specification
**When** the text overlay service processes it
**Then** it adds styled text to the video clip with proper positioning and animation

**And** the system:
- Generates clips in parallel (if API allows) or sequentially
- Each clip is 3-7 seconds, matches scene duration specification
- All clips use same aspect ratio (9:16 for MVP)
- Text styling includes brand colors, fonts, and animations

**Prerequisites:** Story 3.1

**Technical Notes:** 
- Create video_generator.py module, use Replicate Python SDK, track costs
- Use MoviePy library for video processing, create text clips with styling
- Handle rate limits gracefully, support multiple models with fallback logic

---

### Story 3.3: Video Assembly and Export

As a developer,
I want to stitch clips together, add audio, and export the final video,
So that the output is professional-quality and ready for download.

**Acceptance Criteria:**

**Video Stitching:**
**Given** multiple video clips with text overlays
**When** the video stitching service processes them
**Then** it concatenates clips with crossfade transitions and exports a single video

**Audio Layer:**
**Given** a stitched video and music style specification
**When** the audio layer service processes it
**Then** it adds background music and sound effects synchronized with the video

**Post-Processing:**
**Given** a video with audio
**When** the post-processing service processes it
**Then** it applies color grading, exports final video (1080p MP4), and generates thumbnail

**And** the final video:
- Total duration matches sum of scene durations (accounting for transitions)
- Frame rate is consistent (24 fps default)
- Resolution is 1080p minimum
- File size is reasonable (<50MB for 15s video)
- Plays correctly in HTML5 video players

**Prerequisites:** Story 3.2

**Technical Notes:** 
- Use MoviePy's concatenate_videoclips, apply fade effects and transitions
- Use MoviePy's AudioFileClip, trim music to video duration, adjust volume levels
- Use OpenCV or MoviePy for color grading, use FFmpeg for encoding, generate thumbnail
- Move files to permanent storage, update database with video_url and status

---

### Story 3.4: Progress Tracking and Management

As a user,
I want to see real-time progress, track costs, and cancel if needed,
So that I know the status of my video generation and can manage it.

**Acceptance Criteria:**

**Progress Tracking:**
**Given** I have started a video generation
**When** I check the generation status
**Then** I see current status, progress percentage, and current step description

**Cost Calculation:**
**Given** a video generation completes
**When** the cost calculation service processes it
**Then** it calculates total cost and updates user's total_cost field

**Cancel Generation:**
**Given** I have a video generation in progress
**When** I click the cancel button
**Then** the system attempts to stop processing and updates status accordingly

**And** progress updates occur at: 10% (LLM), 20% (Scene Planning), 30-70% (Video Generation), 80% (Stitching), 90% (Audio), 100% (Complete)

**Prerequisites:** Story 1.3, Story 3.1, Story 3.3

**Technical Notes:** 
- Update generation record at each pipeline stage, create status endpoint, frontend polls every 2 seconds
- Track API costs at each stage, store cost per generation, update user.total_cost atomically
- Add cancellation flag to generation record, check flag at each pipeline stage

---

## Epic 4: Video Management

**Goal:** Enable users to view, play, download, search, and delete their generated videos through an intuitive gallery interface.

### Story 4.1: Video Gallery

As a user,
I want to see all my generated videos in a grid layout,
So that I can quickly browse and select videos.

**Acceptance Criteria:**

**Backend:**
**Given** I am logged in
**When** I request my video gallery
**Then** the system returns paginated list of my generations with metadata (id, prompt, status, video_url, thumbnail_url, duration, cost, dates)

**Frontend:**
**Given** I am on the gallery page
**When** the page loads
**Then** I see grid layout with video thumbnails, status indicators, and metadata

**And** the gallery includes:
- Responsive grid (1 column mobile, 2-3 tablet, 4+ desktop)
- Pagination or "Load More" button
- Search bar (filters by prompt text)
- Status filter dropdown (All, Completed, Processing, Failed)
- Empty state if no videos
- Click thumbnail to navigate to video detail page

**Prerequisites:** Story 1.2, Story 1.3, Story 2.3, Story 1.4

**Technical Notes:** 
- Backend: Create endpoint with pagination, filtering, and search support
- Frontend: Create gallery component with responsive grid, implement pagination and search

---

### Story 4.2: Video Playback and Download

As a user,
I want to play and download my generated videos,
So that I can preview and use them in my marketing campaigns.

**Acceptance Criteria:**

**Video Playback Backend:**
**Given** I have a completed video generation
**When** I request the video file
**Then** the system serves the video file with proper headers and range request support

**Video Playback Frontend:**
**Given** I am on a video detail page
**When** the page loads
**Then** I see HTML5 video player with controls and video metadata

**Video Download:**
**Given** I am viewing a completed video
**When** I click the download button
**Then** the browser downloads the video file with proper filename (`ad_{generation_id}.mp4`)

**And** the video player:
- Supports different aspect ratios (9:16 vertical, 16:9 horizontal, 1:1 square)
- Responsive sizing (fits container, maintains aspect ratio)
- Shows loading state while video loads
- Handles playback errors gracefully

**Prerequisites:** Story 1.3, Story 1.4, Story 3.3

**Technical Notes:** 
- Create video streaming endpoint, support range requests for video seeking
- Create video detail page component, use HTML5 video element
- Use HTML5 download attribute or JavaScript download trigger

---

### Story 4.3: Video Deletion

As a user,
I want to delete videos I no longer need,
So that I can manage my storage and keep my gallery organized.

**Acceptance Criteria:**

**Backend:**
**Given** I own a video generation
**When** I request deletion
**Then** the system deletes the video file, thumbnail, and database record

**Frontend:**
**Given** I am viewing a video
**When** I click the delete button
**Then** a confirmation dialog appears and deletion proceeds on confirmation

**And** deletion includes:
- Confirmation dialog: "Are you sure you want to delete this video? This action cannot be undone."
- Loading state on delete button
- Success: redirects to gallery with success message
- Error: displays error message
- Only video owner can delete

**Prerequisites:** Story 1.2, Story 1.3, Story 2.3, Story 1.4

**Technical Notes:** 
- Create delete endpoint, verify ownership, delete files and database record
- Create confirmation dialog component, handle delete API call with error handling

---

### Story 4.4: Video Search (Optional)

As a user,
I want to search my videos by prompt text,
So that I can quickly find specific videos.

**Acceptance Criteria:**

**Given** I have multiple videos in my gallery
**When** I enter search text in the search bar
**Then** the gallery filters videos:
- Shows only videos where prompt contains search text (case-insensitive)
- Updates results in real-time as I type (debounced, 300ms delay)
- Shows "No results" message if no matches
- Clears filter when search text is empty

**And** search works with:
- Partial matches (substring search)
- Case-insensitive matching
- Combined with status filter (search + status filter both apply)

**Prerequisites:** Story 4.1

**Technical Notes:** Add search input to gallery, implement debounced search, send search query to backend, update gallery display when search results change

---

## Epic 5: User Profile

**Goal:** Display user statistics and account information so users can track their usage and costs.

### Story 5.1: Profile Display

As a user,
I want to view my profile page with statistics,
So that I can see my account information and usage.

**Acceptance Criteria:**

**Backend:**
**Given** I am logged in
**When** I request my profile
**Then** the system returns user information and statistics (total_generations, total_cost, dates)

**Frontend:**
**Given** I am logged in
**When** I navigate to the profile page
**Then** I see:
- Username and email (if provided)
- Account creation date: "Member since: {month} {year}"
- Statistics section:
  - Total Videos Generated: {total_generations}
  - Total Cost Spent: ${total_cost} (formatted as currency)
  - Last Login: {last_login} (formatted as relative time, e.g., "2 hours ago")
- Logout button

**And** the profile page:
- Loads user data on mount (API call to `/api/user/profile`)
- Shows loading state while fetching
- Displays error message if fetch fails
- Responsive design (works on mobile, tablet, desktop)

**Prerequisites:** Story 1.2, Story 1.3, Story 2.3, Story 1.4

**Technical Notes:** 
- Create profile endpoint, return user data and statistics
- Create profile page component, format currency and dates, display statistics

---

### Story 5.2: User Stats Update

As a developer,
I want user statistics to update automatically,
So that users see accurate counts and costs.

**Acceptance Criteria:**

**Given** a video generation completes
**When** the generation service finishes
**Then** the system:
- Increments `user.total_generations` by 1
- Adds `generation.cost` to `user.total_cost`
- Updates `user.last_login` on each successful login

**And** updates are:
- Atomic (database transaction ensures consistency)
- Immediate (user sees updated stats on next profile view)
- Accurate (no race conditions, proper locking if needed)

**Prerequisites:** Story 2.1 (last_login), Story 3.4 (total_cost, total_generations)

**Technical Notes:** Update user record atomically after generation completes, update last_login in login endpoint

---

## FR Coverage Matrix

- **FR-001:** User Registration → Epic 2, Story 2.1
- **FR-002:** User Login → Epic 2, Story 2.1
- **FR-003:** Protected Routes → Epic 2, Story 2.1, Story 2.3
- **FR-004:** User Logout → Epic 2, Story 2.4
- **FR-005:** Simple Prompt Input → Epic 3, Story 3.1
- **FR-006:** LLM Enhancement → Epic 3, Story 3.1
- **FR-007:** Framework Selection → Epic 3, Story 3.1
- **FR-008:** Scene Planning → Epic 3, Story 3.1
- **FR-009:** Video Clip Generation → Epic 3, Story 3.2
- **FR-010:** Text Overlay Addition → Epic 3, Story 3.2
- **FR-011:** Video Stitching → Epic 3, Story 3.3
- **FR-012:** Audio Layer → Epic 3, Story 3.3
- **FR-013:** Post-Processing → Epic 3, Story 3.3
- **FR-014:** Progress Tracking → Epic 3, Story 3.4
- **FR-015:** Cost Calculation → Epic 3, Story 3.4
- **FR-016:** Cancel Generation → Epic 3, Story 3.4
- **FR-017:** Video Gallery → Epic 4, Story 4.1
- **FR-018:** Video Playback → Epic 4, Story 4.2
- **FR-019:** Video Download → Epic 4, Story 4.2
- **FR-020:** Video Deletion → Epic 4, Story 4.3
- **FR-021:** Video Search → Epic 4, Story 4.4 (optional)
- **FR-022:** Profile Display → Epic 5, Story 5.1
- **FR-023:** User Stats Update → Epic 5, Story 5.2

---

## Summary

This epic breakdown decomposes all 23 functional requirements from the PRD into 5 epics and 18 implementable stories. Each story is sized for focused development work, with detailed BDD-style acceptance criteria and technical implementation notes.

**Epic Sequencing:**
1. **Epic 1 (Foundation)** - Must be completed first, establishes infrastructure (4 stories)
2. **Epic 2 (User Authentication)** - Enables user access, required before video features (4 stories)
3. **Epic 3 (Video Generation Pipeline)** - Core product functionality (4 stories)
4. **Epic 4 (Video Management)** - Enables users to view and manage their videos (4 stories)
5. **Epic 5 (User Profile)** - Provides usage tracking and account information (2 stories)

**Next Steps in BMad Method:**
1. **UX Design** (if UI exists) - Run: `*create-ux-design` workflow
   → Will add interaction details to stories in epics.md
2. **Architecture** - Run: `*create-architecture` workflow
   → Will add technical details to stories in epics.md
3. **Phase 4 Implementation** - Stories ready for context assembly and development

**Important:** This is a living document that will be updated as you progress through the workflow chain. The epics.md file will evolve with UX and Architecture inputs before implementation begins.

---

_For implementation: Use the `*create-story` workflow to generate individual story implementation plans from this epic breakdown._

_This document will be updated after UX Design and Architecture workflows to incorporate interaction details and technical decisions._
