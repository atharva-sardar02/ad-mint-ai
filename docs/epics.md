# ad-mint-ai - Epic Breakdown

**Author:** BMad
**Date:** 2025-11-14 (Updated: 2025-11-14)
**Project Level:** Intermediate
**Target Scale:** MVP + Post-MVP Features

---

## Overview

This document provides the complete epic and story breakdown for ad-mint-ai, decomposing the requirements from the [PRD](./PRD.md) into implementable stories.

**Living Document Notice:** This is the initial version. It will be updated after UX Design and Architecture workflows add interaction and technical details to stories.

---

## Functional Requirements Inventory

- **FR-001:** User Registration - System shall allow users to create accounts with username and password ✅
- **FR-002:** User Login - System shall authenticate users via username/password and generate JWT token ✅
- **FR-003:** Protected Routes - System shall restrict access to authenticated users only ✅
- **FR-004:** User Logout - System shall clear JWT token from client storage ✅
- **FR-005:** Simple Prompt Input - System shall accept text prompt (10-500 characters) ✅
- **FR-006:** LLM Enhancement - System shall send prompt to LLM and generate complete ad specification JSON ✅
- **FR-007:** Framework Selection - System shall automatically select best advertising framework (PAS, BAB, or AIDA) ✅
- **FR-008:** Scene Planning - System shall break video into 3-5 scenes based on framework ✅
- **FR-009:** Video Clip Generation - System shall generate video clips using Replicate API ✅
- **FR-010:** Text Overlay Addition - System shall add text overlays to video clips ✅
- **FR-011:** Video Stitching - System shall concatenate all scene clips with transitions ✅
- **FR-012:** Audio Layer - System shall select and add background music and sound effects ✅
- **FR-013:** Post-Processing - System shall apply color grading and export final video (1080p minimum) ✅
- **FR-014:** Progress Tracking - System shall update database with current status and progress % ✅
- **FR-015:** Cost Calculation - System shall track total cost per generation ✅
- **FR-016:** Cancel Generation (Best-Effort) - System shall allow users to request cancellation of in-progress generation ✅
- **FR-017:** Video Gallery - System shall display all user's generated videos in grid layout ✅
- **FR-018:** Video Playback - System shall serve video files from storage with HTML5 player ✅
- **FR-019:** Video Download - System shall allow users to download MP4 files ✅
- **FR-020:** Video Deletion - System shall allow users to delete their videos with confirmation ✅
- **FR-021:** Video Search - System shall filter videos by prompt text and status (optional) ✅
- **FR-022:** Profile Display - System shall show user statistics (total videos, cost, dates) ✅
- **FR-023:** User Stats Update - System shall increment total_generations and update total_cost ✅
- **FR-024:** Video Editor Access - System shall provide an editor interface accessible from completed video detail page
- **FR-025:** Timeline Interface - System shall display a timeline showing all video clips in sequence
- **FR-026:** Clip Trimming - System shall allow users to trim clips by adjusting start/end points
- **FR-027:** Clip Splitting - System shall allow users to split clips at any position
- **FR-028:** Clip Merging - System shall allow users to merge multiple adjacent clips
- **FR-029:** Editor Save and Export - System shall allow users to save editing changes and export edited videos
- **FR-030:** Video Coherence Analysis - System shall automatically analyze visual consistency across all clips
- **FR-031:** Coherence Enhancement - System shall automatically apply color grading and transition optimizations
- **FR-032:** Prompt Optimization via LLM - System shall enhance user prompts using LLM for better video quality
- **FR-033:** Quality Feedback Loop - System shall track quality metrics and learn from user preferences
- **FR-034:** Profile Display - System shall show user statistics (total videos, cost, dates) ✅
- **FR-035:** User Stats Update - System shall increment total_generations and update total_cost ✅
 - **FR-036:** Hero Frame Generation (Text → Photo) - System shall provide a dedicated hero-frame generation flow, using text-to-image models to generate 4–8 hero frame candidates per request and persist them with metadata.
 - **FR-037:** Cinematographer-Level Prompt Enhancement for Images - System shall offer an optional LLM-powered “cinematographer enhancement” step for hero-frame prompts, returning enriched prompts with detailed cinematography guidance.
 - **FR-038:** Hero Frame Iteration & Selection - System shall allow users to regenerate, mutate, favorite, and clearly select a canonical hero frame as the anchor for downstream generations.
 - **FR-039:** Image-to-Video Generation (Photo → Video) from Hero Frame - System shall support image-to-video generation from a selected hero frame, including motion and negative prompts, and produce at least one video attempt.
 - **FR-040:** Automated Multi-Attempt Generation with VBench-Based Selection - System shall support a 3-attempt auto mode, evaluate attempts with VBench, and auto-select the top-scoring attempt within a generation group.
 - **FR-041:** Iteration Workspace & Human-in-the-Loop Refinement - System shall provide an Iteration Workspace UI for side-by-side comparison of attempts, manual overrides, prompt edits, and LLM-based improvement suggestions.
 - **FR-042:** Iterative Refinement Workflow & Versioning - System shall treat each cycle of “prompt update → attempts → evaluation → selection” as an iteration, maintain a generation history timeline, and track a final_version per ad.
 - **FR-043:** Quality Dashboard & Benchmarks - System shall provide a quality dashboard visualizing VBench scores, iterations, and acceptance trends with filtering and aggregation options.
 - **FR-044:** Integration with Existing Pipeline & Epics - The hero-frame workflow shall reuse the existing generation pipeline, Epic 7 coherence capabilities, and Epic 6 editor as an additive professional-mode layer on top of the current system.

---

## FR Coverage Map

- **Epic 1 (Foundation):** Stories 1.1-1.4 ✅ COMPLETED, Story 1.5 pending - Covers infrastructure needs for all FRs - project setup, database, deployment pipeline, production deployment
- **Epic 2 (User Authentication):** ✅ COMPLETED - FR-001, FR-002, FR-003, FR-004
- **Epic 3 (Video Generation Pipeline):** ✅ COMPLETED - FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-016
- **Epic 4 (Video Management):** ✅ COMPLETED - FR-017, FR-018, FR-019, FR-020, FR-021
- **Epic 5 (User Profile):** ✅ COMPLETED - FR-022, FR-023, FR-034, FR-035
- **Epic 6 (Video Editing):** FR-024, FR-025, FR-026, FR-027, FR-028, FR-029
- **Epic 7 (Video Quality Optimization):** FR-030, FR-031, FR-032, FR-033
 - **Epic 8 (Hero-Frame Generation):** FR-036, FR-037, FR-038
 - **Epic 9 (Hero-Frame Iteration & Image-to-Video Workflow):** FR-039, FR-040, FR-041, FR-042, FR-043, FR-044

---

## Epic 1: Foundation & Infrastructure

**Goal:** Establish the foundational infrastructure, project structure, database setup, and deployment pipeline that enables all subsequent development work.

**Status:** Stories 1.1-1.4 completed. Story 1.5 (Production Deployment) pending.

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

### Story 1.5: Production Deployment

As a developer,
I want a complete production deployment setup with CI/CD, monitoring, and security,
So that the application can be deployed reliably to production with proper safeguards.

**Acceptance Criteria:**

**Deployment Infrastructure:**
**Given** I have a production environment ready
**When** I deploy the application
**Then** the system:
- Configures SSL/TLS certificates (Let's Encrypt or AWS Certificate Manager)
- Sets up domain name and DNS configuration
- Configures production database (PostgreSQL) with backups
- Sets up file storage (S3 or equivalent) for video files
- Configures environment variables for production secrets
- Implements health check endpoints for monitoring

**CI/CD Pipeline:**
**Given** code is pushed to the repository
**When** CI/CD pipeline runs
**Then** it:
- Runs automated tests (unit, integration, e2e)
- Builds Docker images (if containerized) or prepares deployment artifacts
- Runs security scans and dependency checks
- Deploys to staging environment for validation
- Promotes to production after staging approval
- Sends deployment notifications

**Security & Hardening:**
**Given** the application is deployed
**When** security measures are in place
**Then** the system includes:
- Firewall rules (only necessary ports open)
- Rate limiting on API endpoints
- CORS properly configured for production domain
- Secure headers (HSTS, CSP, X-Frame-Options)
- Database connection encryption
- Secrets management (AWS Secrets Manager or equivalent)
- Regular security updates and patching

**Monitoring & Observability:**
**Given** the application is running in production
**When** monitoring is configured
**Then** the system tracks:
- Application health and uptime
- API response times and error rates
- Database performance metrics
- Server resource usage (CPU, memory, disk)
- Video generation success/failure rates
- Cost tracking per generation
- User activity and authentication events

**Backup & Recovery:**
**Given** production data exists
**When** backup procedures are in place
**Then** the system:
- Automatically backs up database daily (with retention policy)
- Backs up video files to secondary storage
- Tests restore procedures regularly
- Documents disaster recovery plan
- Maintains point-in-time recovery capability

**Rollback & Version Management:**
**Given** a deployment fails or issues are detected
**When** rollback is needed
**Then** the system:
- Maintains previous deployment artifacts
- Can quickly revert to previous version
- Preserves database migrations (forward/backward compatible)
- Logs all deployment events for audit trail

**Documentation:**
**Given** deployment is complete
**When** documentation is reviewed
**Then** it includes:
- Deployment runbook with step-by-step procedures
- Environment configuration guide
- Troubleshooting guide for common issues
- Incident response procedures
- Contact information for on-call support

**Prerequisites:** Story 1.4 (Deployment Pipeline Basics), Story 1.2 (Database Schema), Story 1.3 (API Infrastructure)

**Technical Notes:**
- Use GitHub Actions, GitLab CI, or AWS CodePipeline for CI/CD
- Consider Docker containerization for consistent deployments
- Set up AWS CloudWatch, Datadog, or similar for monitoring
- Use AWS RDS for managed PostgreSQL with automated backups
- Configure AWS S3 for video file storage with lifecycle policies
- Implement structured logging (JSON format) for better observability
- Set up alerting for critical errors and performance degradation
- Use infrastructure as code (Terraform, CloudFormation) for reproducibility
- Configure auto-scaling if needed for high traffic
- Set up CDN (CloudFront) for static assets and video delivery

---

## Epic 2: User Authentication ✅ COMPLETED

**Goal:** Enable users to create accounts, log in securely, and access protected features using JWT-based authentication.

**Status:** All stories completed. Epic delivered and in production.

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

## Epic 3: Video Generation Pipeline ✅ COMPLETED

**Goal:** Implement the complete AI-powered video generation pipeline from user prompt to final video output.

**Status:** All stories completed. Epic delivered and in production.

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

## Epic 4: Video Management ✅ COMPLETED

**Goal:** Enable users to view, play, download, search, and delete their generated videos through an intuitive gallery interface.

**Status:** All stories completed. Epic delivered and in production.

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

## Epic 5: User Profile ✅ COMPLETED

**Goal:** Display user statistics and account information so users can track their usage and costs.

**Status:** All stories completed. Epic delivered and in production.

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

## Epic 6: Video Editing

**Goal:** Enable users to edit generated videos using a timeline-based editor with trim, split, and merge capabilities for fine-tuning video content.

### Story 6.1: Video Editor Access and Setup

As a user,
I want to access a video editor from my completed video,
So that I can edit and refine my generated video.

**Acceptance Criteria:**

**Editor Access:**
**Given** I am viewing a completed video on the video detail page
**When** I click the "Edit Video" button
**Then** the system opens the video editor interface

**And** the editor:
- Loads the video with all individual scene clips available
- Maintains a backup of the original video for restoration
- Displays the video in a preview player
- Shows an "Exit Editor" button to return to video detail page

**Backend:**
**Given** a user requests to edit a video
**When** the system processes the request
**Then** it:
- Verifies user ownership of the video
- Loads all scene clips associated with the generation
- Returns video metadata including clip information, durations, and transitions
- Creates an editing session record in the database

**Prerequisites:** Story 4.2 (Video Playback), Story 3.3 (Video Assembly)

**Technical Notes:**
- Create editor route/page component, add "Edit Video" button to video detail page
- Create editor API endpoint that returns video and clip data
- Store original video path for restoration capability
- Create editing_session table to track active editing sessions

---

### Story 6.2: Timeline Interface

As a user,
I want to see a timeline with all my video clips,
So that I can visualize and navigate through the video structure.

**Acceptance Criteria:**

**Timeline Display:**
**Given** I am in the video editor
**When** the editor loads
**Then** I see a timeline showing:
- All video clips in sequence from left to right
- Visual thumbnails for each clip (first frame or keyframe)
- Clip durations displayed below each clip
- Current playback position indicator (playhead)
- Zoom controls for precise editing

**Timeline Interaction:**
**Given** I am viewing the timeline
**When** I interact with it
**Then** I can:
- Click anywhere on timeline to seek to that position
- Drag playhead to scrub through video
- Zoom in/out using controls or mouse wheel (Ctrl/Cmd + scroll)
- See time markers (seconds) along the timeline
- Select clips by clicking on them

**And** the timeline:
- Updates in real-time as I make edits
- Maintains smooth scrolling and performance
- Shows selected clip with highlight/border
- Displays total video duration

**Prerequisites:** Story 6.1

**Technical Notes:**
- Use canvas or SVG for timeline rendering, implement thumbnail generation for clips
- Create timeline component with zoom/pan functionality, implement playhead scrubbing
- Generate thumbnails on video load, cache thumbnails for performance
- Use requestAnimationFrame for smooth timeline updates

---

### Story 6.3: Clip Trimming

As a user,
I want to trim video clips by adjusting start and end points,
So that I can remove unwanted portions and fine-tune clip durations.

**Acceptance Criteria:**

**Trim Selection:**
**Given** I have selected a clip on the timeline
**When** I select the clip
**Then** trim handles appear at the start and end of the clip

**Trim Adjustment:**
**Given** I see trim handles on a selected clip
**When** I drag a trim handle
**Then**:
- The clip duration updates in real-time
- Preview shows the trimmed clip content
- Timeline updates immediately to reflect changes
- Time values update to show new start/end times

**Trim Validation:**
**Given** I am trimming a clip
**When** I adjust trim points
**Then** the system:
- Prevents trimming beyond clip boundaries
- Maintains minimum clip duration (0.5 seconds)
- Shows visual feedback for invalid trim positions
- Allows precise time entry via input fields (optional)

**Preview:**
**Given** I have trimmed a clip
**When** I preview the video
**Then** the trimmed clip plays with the new start/end points

**Prerequisites:** Story 6.2

**Technical Notes:**
- Implement trim handle UI components, add drag handlers for trim adjustment
- Use MoviePy to trim clips, validate trim points before applying
- Update timeline state on trim, provide real-time preview
- Store trim points in editing session, apply on export

---

### Story 6.4: Clip Splitting

As a user,
I want to split a clip at any point,
So that I can divide long clips into separate segments for independent editing.

**Acceptance Criteria:**

**Split Point Selection:**
**Given** I have a clip selected on the timeline
**When** I click a "Split" button or press a keyboard shortcut (S key)
**Then** a split indicator appears at the playhead position

**Split Execution:**
**Given** I have positioned the split indicator
**When** I confirm the split
**Then** the system:
- Divides the clip into two separate clips at the split point
- Maintains both clips in the timeline sequence
- Preserves all metadata (text overlays, transitions) for both clips
- Updates the timeline to show two clips instead of one

**Split Clip Editing:**
**Given** I have split a clip
**When** I select either resulting clip
**Then** I can edit them independently:
- Trim each clip separately
- Apply different effects or transitions
- Move clips independently (if reordering is supported)

**Prerequisites:** Story 6.2

**Technical Notes:**
- Implement split UI with split indicator, add split confirmation dialog
- Use MoviePy to split video at specified time, create two clip objects
- Preserve metadata for both clips, update timeline data structure
- Handle edge cases (split at start/end, very short clips)

---

### Story 6.5: Clip Merging

As a user,
I want to merge multiple adjacent clips,
So that I can combine related segments into a single continuous clip.

**Acceptance Criteria:**

**Clip Selection:**
**Given** I have multiple clips on the timeline
**When** I select multiple adjacent clips (Ctrl/Cmd + click or drag selection)
**Then** the selected clips are highlighted

**Merge Execution:**
**Given** I have selected multiple adjacent clips
**When** I click the "Merge" button
**Then** the system:
- Combines selected clips into a single continuous clip
- Preserves video content from all merged clips
- Maintains frame rate consistency across merged segments
- Applies appropriate transitions between merged segments
- Updates timeline to show merged clip as single entity

**Merge Validation:**
**Given** I attempt to merge clips
**When** the system processes the merge
**Then** it:
- Only allows merging of adjacent clips
- Validates that clips are in sequence
- Shows error message if non-adjacent clips are selected
- Maintains total video duration correctly

**Prerequisites:** Story 6.2

**Technical Notes:**
- Implement multi-clip selection UI, add merge button/action
- Use MoviePy concatenate_videoclips to merge, apply transitions between segments
- Validate clip adjacency, update timeline after merge
- Handle metadata preservation (text overlays may need adjustment)

---

### Story 6.6: Editor Save and Export

As a user,
I want to save my editing changes and export the edited video,
So that I can preserve my work and download the final result.

**Acceptance Criteria:**

**Save Editing Session:**
**Given** I have made edits to a video
**When** I click "Save" or the system auto-saves
**Then** the system:
- Saves editing state (trim points, splits, merges) to database
- Preserves original video unchanged
- Allows me to return and continue editing later
- Shows "Saved" confirmation message

**Export Edited Video:**
**Given** I have edited a video and want to export
**When** I click "Export Video"
**Then** the system:
- Creates a new video version with all edits applied
- Processes the video with all trim, split, and merge operations
- Maintains original video for comparison
- Exports edited video in same format and quality as original (1080p MP4)
- Updates database with new video version

**Export Progress:**
**Given** I have initiated video export
**When** the export is processing
**Then** I see:
- Progress indicator showing export status
- Estimated time remaining
- Ability to cancel export (if not too late)

**Version Management:**
**Given** I have exported an edited video
**When** I view the video
**Then** I can:
- See both original and edited versions
- Compare original vs edited
- Restore original if needed

**Prerequisites:** Story 6.3, Story 6.4, Story 6.5

**Technical Notes:**
- Create save/export API endpoints, implement editing session persistence
- Use MoviePy to apply all edits and export final video, maintain version history
- Store edited video as new generation record or version, implement progress tracking
- Add undo/redo functionality (store edit history in session)

---

## Epic 7: Multi-Scene Coherence & Quality Optimization

**Goal:** Implement state-of-the-art generation-time consistency techniques and automated quality control to ensure professional multi-scene video coherence—the core differentiator for professional ad generation. This epic incorporates bleeding-edge research techniques prioritizing prevention (generation-time consistency) over correction (post-processing).

**Scope:** 
- **MVP (Stories 7.0-7.4):** Core coherence techniques essential for professional quality
- **Growth (Stories 7.5-7.10):** Advanced quality control and optimization (nice-to-have)
- Story 7.0 (Settings UI) is primarily a developer tool for iteration and testing

### Story 7.0: Coherence Settings UI Panel [MVP - Dev Tool]

As a developer,
I want to see and control which coherence techniques are applied to video generation,
So that I can iterate on videos, test different settings, and optimize quality during development.

**Acceptance Criteria:**

**Coherence Settings Panel (Dev Tool):**
**Given** I am a developer testing video generation
**When** I view the generation form or dev dashboard
**Then** I see a coherence settings panel with checkboxes for:
- ☑ Seed Control (enabled by default, recommended)
- ☑ IP-Adapter for Character/Product Consistency (enabled by default if entities detected)
- ☐ LoRA Training (disabled by default, requires trained LoRA)
- ☑ Enhanced LLM Planning (enabled by default, recommended)
- ☑ VBench Quality Control (enabled by default, recommended)
- ☑ Post-Processing Enhancement (enabled by default, recommended)
- ☐ ControlNet for Compositional Consistency (disabled by default, advanced)
- ☐ CSFD Character Consistency Detection (disabled by default, character-driven ads only)

**Settings Display:**
**Given** I view the coherence settings panel
**When** I examine each option
**Then** I see:
- Checkbox/toggle for each technique
- Brief description of what each technique does
- Default state (enabled/disabled)
- Estimated impact on generation time (if applicable)
- Estimated impact on cost (if applicable)
- Tooltip with more details on hover/click

**Settings Persistence:**
**Given** I configure coherence settings
**When** I submit the video generation
**Then** the system:
- Sends selected settings to backend API
- Stores settings with generation record
- Applies only selected techniques during generation
- Remembers my preferences for next generation (optional)

**Settings Validation:**
**Given** I configure coherence settings
**When** I select/deselect options
**Then** the system:
- Shows dependencies (e.g., "IP-Adapter requires Enhanced Planning")
- Disables incompatible options
- Shows warnings for recommended combinations
- Validates settings before submission

**Prerequisites:** Story 3.1 (Prompt Processing)

**Technical Notes:**
- Create `CoherenceSettingsPanel` React component
- Add to Dashboard page, expandable/collapsible section
- Use checkboxes or toggles for each technique
- Store settings in component state, send to API with generation request
- Backend: Add `coherence_settings` JSON field to generation model
- Default settings: Enable recommended techniques, disable advanced/optional ones
- Show estimated cost impact for each technique (time is not a constraint, quality is priority)
- Add tooltips/help text explaining each technique

---

### Story 7.1: Seed Control and Latent Reuse for Visual Coherence [MVP]

As a developer,
I want to implement seed control and latent reuse across all scenes in a video,
So that the generated clips maintain consistent visual "DNA" and seamless transitions.

**Acceptance Criteria:**

**Seed Control:**
**Given** a video generation with multiple scenes is initiated
**When** the system generates video clips for each scene
**Then** it:
- Checks if seed control is enabled in coherence settings (default: enabled)
- Uses the same random seed for all scenes in the video (if enabled)
- Ensures the underlying latent structure is linked across scenes
- Maintains base level of visual similarity through shared seed
- Stores seed value with generation record for reproducibility
- Skips seed control if disabled by user

**Latent Reuse:**
**Given** scenes are being generated sequentially
**When** transitioning between scenes that should be continuous
**Then** the system:
- Initializes the latent noise for a new scene with the final latent state of the previous scene
- Creates seamless visual continuity between linked scenes
- Applies latent reuse only when scenes are marked as continuous in the scene plan
- Maintains temporal coherence for long continuous narratives

**Visual Coherence:**
**Given** seed control and latent reuse are implemented
**When** a multi-scene video is generated
**Then** the system:
- Maintains consistent visual style across all scenes
- Reduces style drift between clips
- Creates smoother transitions between scenes
- Improves overall multi-scene coherence score

**Prerequisites:** Story 3.1 (Prompt Processing), Story 3.2 (Video Generation)

**Technical Notes:**
- Implement seed management in video generation service, store seed per generation
- Use same seed parameter across all Replicate API calls for scenes in same video
- Implement latent reuse mechanism for continuous scenes (requires model support or post-processing)
- For Replicate API: Use seed parameter in API calls, ensure seed persistence across scene generation
- Store seed value in generation record for debugging and reproducibility
- Document seed control strategy in technical documentation

---

### Story 7.2: Parallel Generation and Comparison Tool [MVP]

As a user,
I want to generate multiple video variations in parallel by tweaking settings or prompts,
So that I can compare different outputs and select the best result for my needs.

**Acceptance Criteria:**

**Parallel Generation Interface:**
**Given** I am on the video generation dashboard
**When** I want to create multiple variations
**Then** I see an option to enable "Parallel Generation Mode" with:
- Toggle to enable/disable parallel generation
- Ability to specify number of variations (2-5 variations)
- Two comparison modes:
  - **Settings Comparison:** Same prompt, different coherence settings
  - **Prompt Comparison:** Same settings, different prompt variations

**Settings Comparison Mode:**
**Given** I have enabled parallel generation with settings comparison
**When** I configure the generation
**Then** I can:
- Enter a single prompt
- Create multiple setting profiles (e.g., "Profile A", "Profile B", "Profile C")
- Configure different coherence settings for each profile:
  - Different seed control settings
  - Different IP-Adapter configurations
  - Different enhanced planning options
  - Different post-processing settings
- See a preview of each profile's settings before submission
- Submit all variations to generate in parallel

**Prompt Comparison Mode:**
**Given** I have enabled parallel generation with prompt comparison
**When** I configure the generation
**Then** I can:
- Enter multiple prompt variations (2-5 prompts)
- Use the same coherence settings for all prompts
- See all prompts in a list/table format
- Edit individual prompts independently
- Submit all prompt variations to generate in parallel

**Parallel Generation Execution:**
**Given** I have submitted parallel generation requests
**When** the system processes them
**Then** it:
- Creates multiple generation records (one per variation)
- Links variations together as a "generation group" or "comparison set"
- Processes all variations in parallel (background tasks run concurrently)
- Tracks progress for each variation independently
- Updates status for each generation separately

**Comparison View:**
**Given** I have multiple video variations generated
**When** I view the comparison results
**Then** I see:
- Side-by-side or grid layout showing all variations
- Video thumbnails for each variation
- Metadata for each (prompt, settings used, cost, generation time)
- Ability to play each video independently
- Ability to select and download the preferred variation
- Ability to delete individual variations or the entire comparison set
- Visual indicators showing which settings/prompts differ between variations

**Comparison Navigation:**
**Given** I am viewing a comparison set
**When** I interact with it
**Then** I can:
- Navigate to individual video detail pages from the comparison view
- Return to comparison view from individual video pages
- Filter or sort variations by quality metrics (if available)
- See cost breakdown per variation and total cost for the comparison set

**Backend Support:**
**Given** parallel generation is requested
**When** the backend processes the request
**Then** it:
- Accepts array of generation requests in a single API call
- Creates generation_group record to link related generations
- Processes all generations concurrently (uses async/background tasks)
- Tracks group_id in generation records for querying related videos
- Supports querying all generations in a group via API

**Parallel Clip Creation (Single Video Variation):**
**Given** a single video variation is being generated with multiple scenes
**When** the system generates video clips for all scenes
**Then** it:
- Checks if parallel clip creation is enabled in coherence settings (default: enabled if API allows)
- If enabled, creates all clips for the video variation in parallel using concurrent API calls to Replicate
- If disabled, generates clips sequentially (one after another)
- Speeds up generation significantly when parallel mode is enabled (reduces total generation time from sum of clip times to max of clip times)
- Handles errors gracefully: if one clip fails, other clips continue processing
- Tracks progress for each clip independently
- Updates overall generation progress based on completed clips

**Parallel Clip Creation Settings:**
**Given** I am configuring a video generation
**When** I view coherence settings
**Then** I see:
- Toggle for "Parallel Clip Creation" (enabled by default if supported)
- Description: "Generate all clips for a video in parallel to speed up generation"
- Warning if disabled: "Clips will be generated sequentially, which may take longer"
- Estimated time savings when enabled (e.g., "~3x faster for 5-scene videos")

**Prerequisites:** Story 3.1 (Prompt Processing), Story 7.0 (Coherence Settings UI)

**Technical Notes:**
- **Frontend:**
  - Add "Parallel Generation" toggle to Dashboard component
  - Create `ParallelGenerationPanel` component with:
    - Mode selector (Settings Comparison vs Prompt Comparison)
    - Variation count selector (2-5)
    - Dynamic form for each variation (settings profiles or prompt inputs)
    - Preview/summary view before submission
  - Create `ComparisonView` component for displaying results:
    - Grid layout with video cards
    - Side-by-side video player
    - Metadata display
    - Selection and download functionality
  - Update Dashboard to handle parallel generation submission
  - Create comparison detail page route (`/comparison/{group_id}`)
- **Backend:**
  - Add `generation_groups` table:
    - `id` (UUID, primary key)
    - `user_id` (FK to users)
    - `created_at` (timestamp)
    - `comparison_type` (enum: 'settings', 'prompt')
  - Add `generation_group_id` field to `generations` table (FK, nullable)
  - Create `/api/generate/parallel` endpoint:
    - Accepts array of `GenerateRequest` objects
    - Creates generation_group record
    - Creates multiple generation records linked to group
    - Processes all in parallel using background tasks
    - Returns group_id and array of generation_ids
  - Create `/api/comparison/{group_id}` endpoint:
    - Returns all generations in a group with metadata
    - Includes comparison-specific metadata (which settings/prompts differ)
  - Update generation service to support parallel processing
  - Ensure proper error handling (if one variation fails, others continue)
- **Database:**
  - Migration to add `generation_groups` table
  - Migration to add `generation_group_id` to `generations` table
  - Index on `generation_group_id` for efficient queries
- **UI/UX:**
  - Make it clear this is a comparison/experimentation tool
  - Show estimated total cost before submission (sum of all variations)
  - Provide clear visual distinction between comparison mode and single generation
  - Allow users to save favorite setting profiles for reuse
- **Performance:**
  - Parallel processing should not overwhelm the system
  - Consider rate limiting for parallel requests
  - Monitor concurrent generation capacity
- **Parallel Clip Creation Implementation:**
  - Add `parallel_clip_creation` boolean field to `CoherenceSettings` schema (default: True)
  - Update `generate_all_clips()` function in `video_generation.py` to support parallel execution:
    - Use `asyncio.gather()` or `asyncio.create_task()` to run all clip generation calls concurrently
    - Maintain proper error handling: if one clip fails, others should continue
    - Update progress tracking to handle parallel clip completion
    - Ensure cancellation checks work correctly with parallel execution
  - Update `process_generation()` in `generations.py` to pass parallel_clip_creation setting to clip generation service
  - Add UI toggle in `CoherenceSettingsPanel` component for parallel clip creation
  - Document performance improvements and any rate limiting considerations
  - Test with various scene counts (3-5 scenes) to verify speedup

---

### Story 7.3: Two-Agent Prompt Enhancement + LLM-Guided Multi-Scene Planning (VideoDirectorGPT-style) [MVP]

As a developer,
I want a two-phase prompt enhancement and planning system that first iteratively refines user prompts using specialized agents, then applies VideoDirectorGPT-style planning with consistency groupings and entity descriptions,
So that any user prompt (regardless of quality) gets transformed into a professional, production-ready specification with explicit consistency markers and shot lists.

**Acceptance Criteria:**

**Phase 1: Two-Agent Prompt Enhancement**
**Given** a user prompt (of any quality) is submitted
**When** the prompt enhancement service processes it
**Then** it:
- Uses Agent 1 (Creative Director) to enhance the prompt with cinematography, brand elements, and professional advertising language
- Uses Agent 2 (Prompt Engineer) to critique and score the enhanced prompt
- Iterates between agents (max 3 rounds) until score threshold is met or convergence detected
- Scores prompts on multiple dimensions: completeness, specificity, professionalism, cinematography, brand alignment
- Stops early if score ≥ 85 or if improvement < 2 points between iterations
- Produces a professionally enhanced prompt ready for planning phase

**Phase 2: VideoDirectorGPT-Style Planning**
**Given** an enhanced prompt from Phase 1
**When** the VideoDirectorGPT planning module processes it
**Then** it includes:
- Explicit consistency groupings for entities (e.g., "Character A must look the same in Scene 1 and Scene 3")
- Entity descriptions with consistency requirements (product appearance, character identity, brand colors)
- Shot list with detailed metadata:
  - Shot number and scene number
  - Shot description (action and composition)
  - Duration/runtime
  - Camera movement (pan, tilt, dolly, static)
  - Shot size (wide, medium, close-up)
  - Perspective (POV, over-shoulder, bird's eye)
  - Lens type (35mm, 50mm, telephoto)
- Scene dependencies and narrative flow markers
- Consistency markers indicating which entities must remain consistent across scenes

**Consistency Groupings:**
**Given** the LLM has analyzed the enhanced prompt
**When** it generates the video plan
**Then** it:
- Identifies all entities that appear in multiple scenes (characters, products, brand elements)
- Creates consistency groups for each entity
- Specifies visual requirements for each entity (colors, style, appearance)
- Marks which scenes require entity consistency

**Shot List Generation:**
**Given** the scene plan includes shot list metadata
**When** video clips are generated
**Then** the system:
- Uses shot list metadata to enhance visual prompts
- Incorporates camera movement keywords in generation prompts
- Applies framing and composition details from shot list
- Maintains consistency based on shot list specifications

**Prompt Transparency & Debugging:**
**Given** prompt enhancement and planning are running
**When** a generation is processed
**Then** the system:
- Saves all prompt versions to versioned files in `output/prompt_traces/{generation_id}/`
- File structure:
  - `00_original_prompt.txt` - Original user input
  - `01_agent1_iteration_1.txt` - First Creative Director enhancement
  - `02_agent2_iteration_1.txt` - First Prompt Engineer critique + score
  - `03_agent1_iteration_2.txt` - Second Creative Director refinement (if iterated)
  - `04_agent2_iteration_2.txt` - Second Prompt Engineer critique (if iterated)
  - `05_final_enhanced_prompt.txt` - Final enhanced prompt after all iterations
  - `06_videodirectorgpt_plan.json` - Complete VideoDirectorGPT planning output
  - `07_final_scene_prompts.json` - Final prompts sent to video generation (per scene)
  - `prompt_trace_summary.json` - Metadata: scores, iterations, timestamps
- Provides standalone CLI tool: `python enhance_prompt.py <input_file>` for terminal-based prompt enhancement
- CLI supports: file input, stdin input, custom output directories, iteration control, model selection
- All files are human-readable and versioned for debugging and analysis
- CLI can be used independently of the main pipeline for testing and experimentation

**Integration:**
**Given** the two-phase enhancement system is implemented
**When** a video generation is initiated
**Then** the system:
- Checks if two-agent enhancement is enabled in coherence settings (default: enabled)
- Checks if VideoDirectorGPT planning is enabled in coherence settings (default: enabled)
- Runs Phase 1 (two-agent enhancement) if enabled, otherwise uses original prompt
- Runs Phase 2 (VideoDirectorGPT planning) on enhanced prompt
- Falls back to basic planning if both phases disabled
- Passes consistency markers to video generation service
- Uses entity descriptions for IP-Adapter (Story 7.4) and seed control (Story 7.1)
- Stores complete enhancement and planning output in generation record
- Saves all prompt versions to trace files for transparency

**Prerequisites:** Story 3.1 (Prompt Processing)

**Status:**
- ✅ **Phase 1 (Two-Agent Prompt Enhancement): COMPLETED**
  - `prompt_enhancement.py` service implemented with two-agent iterative refinement
  - Standalone CLI tool `enhance_prompt.py` created for terminal-based usage
  - Prompt scoring mechanism implemented (hybrid: rule-based + LLM-based)
  - File-based trace system saves all versions for transparency
- ⚠️ **Phase 2 (VideoDirectorGPT Planning): NOT YET IMPLEMENTED**
  - Needs enhancement to `scene_planning.py` with VideoDirectorGPT-style planning
  - Needs LLM prompt template updates for consistency groupings and shot lists
  - Needs schema expansion for consistency_groups, shot_list, entity_descriptions
- ⚠️ **Integration: NOT YET IMPLEMENTED**
  - Needs integration into main pipeline (`llm_enhancement.py`)
  - Needs UI integration for coherence settings
  - Needs database schema updates for storing enhanced planning output
- ⚠️ **Pipeline Cleanup & Fixes: REQUIRED**
  - Fix `num_clips` determinism: When user specifies num_clips, pass it to LLM so it creates exactly that many scenes (currently LLM creates 3-5, then code limits after)
  - Fix clip persistence: Save individual clips permanently to `output/clips/{generation_id}/` instead of only in temp directory
  - Update `temp_clip_paths` to point to permanent clip locations
  - Ensure clips remain accessible after final video generation (currently they may be in temp and could be cleaned up)
  - Verify editor's drag-and-drop reordering uses permanent clips, not cached/temp files

**Technical Notes:**
- **Phase 1 Implementation (✅ COMPLETED):**
  - ✅ Created `app/services/pipeline/prompt_enhancement.py` service with two-agent iterative refinement
  - ✅ Agent 1: Creative Director (GPT-4 Turbo) - enhances with cinematography, brand, style
  - ✅ Agent 2: Prompt Engineer (GPT-4 Turbo) - critiques and scores prompts
  - ✅ Implemented prompt scoring mechanism (hybrid: rule-based + LLM-based)
  - ✅ Max 3 iterations, early stopping on score threshold (85) or convergence (<2 point improvement)
  - ✅ Cost optimization: Only runs if initial prompt score < 75
  - ✅ Created standalone CLI tool: `enhance_prompt.py` for terminal-based usage
  - ✅ CLI supports: `python enhance_prompt.py <input_file> [options]` with file/stdin input
  - ✅ File structure: `output/prompt_traces/{timestamp}/` with numbered versions
  - ✅ Saves JSON metadata with scores, timestamps, iteration history
  - ✅ All trace files are human-readable for debugging and analysis
- **Phase 2 Implementation (⚠️ TODO):**
  - ⚠️ Enhance existing `scene_planning.py` with VideoDirectorGPT-style planning
  - ⚠️ Enhance LLM prompt template in `llm_enhancement.py` to include VideoDirectorGPT-style planning instructions
  - ⚠️ Expand `AdSpecification` schema to include:
    - `consistency_groups`: Array of entities with scene appearances
    - `shot_list`: Array of shots with camera metadata (camera movement, shot size, perspective, lens type)
    - `entity_descriptions`: Detailed descriptions of entities requiring consistency
  - ⚠️ Update scene planner to parse and utilize new planning structure
  - ⚠️ Integrate shot list metadata into visual prompt generation for video clips
- **Integration (⚠️ TODO):**
  - ⚠️ Update `llm_enhancement.py` to call `prompt_enhancement.py` service first (Phase 1)
  - ⚠️ Update `llm_enhancement.py` to use enhanced prompt for VideoDirectorGPT planning (Phase 2)
  - ⚠️ Update `scene_planning.py` to use enhanced prompt from Phase 1
  - ⚠️ Integrate shot list metadata into `video_generation.py` for visual prompts
  - ⚠️ Add coherence settings UI controls for enabling/disabling two-agent enhancement
  - ⚠️ Store complete enhancement and planning output in generation record
  - ⚠️ Save all prompt versions to trace files during pipeline execution
  - ⚠️ Update frontend to show prompt enhancement status and scores
- **Pipeline Cleanup & Fixes (⚠️ REQUIRED):**
  - ⚠️ **Fix num_clips determinism** in `generations.py`:
    - When `num_clips` is specified AND `use_llm=True`: Pass `num_clips` to LLM prompt so it creates exactly that many scenes (currently LLM creates 3-5, then code limits after)
    - When `num_clips` is specified AND `use_llm=False`: Use `num_clips` directly (already works)
    - When `num_clips` is NOT specified: Let LLM decide (3-5 scenes, current behavior)
    - Update `SYSTEM_PROMPT` in `llm_enhancement.py` to accept and respect `num_clips` parameter
  - ⚠️ **Fix clip persistence** in `generations.py` and `video_generation.py`:
    - Create permanent clip storage: `output/clips/{generation_id}/` directory
    - After each clip is generated, copy/move it from temp to permanent location: `output/clips/{generation_id}/clip_{scene_number}.mp4`
    - After overlays are added, save overlay clips to permanent location: `output/clips/{generation_id}/clip_{scene_number}_overlay.mp4`
    - Update `generation.temp_clip_paths` to store permanent paths (or add new `clip_paths` field for permanent storage)
    - Ensure clips remain accessible after final video generation completes
    - Update editor service to use permanent clip paths instead of temp paths
  - ⚠️ **Verify editor clip handling**:
    - Confirm editor's drag-and-drop reordering uses permanent clips, not cached/temp files
    - Ensure clips persist even if temp directory is cleaned up
    - Test that clips are accessible long after generation completes

---

### Story 7.4: IP-Adapter Integration for Character/Product Identity Preservation [MVP]

As a developer,
I want to implement IP-Adapter for identity preservation,
So that characters and products maintain consistent appearance across multiple scenes without requiring model training.

**Acceptance Criteria:**

**IP-Adapter Implementation:**
**Given** a video generation includes entities requiring consistency (characters, products)
**When** the system generates video clips
**Then** it:
- Uses IP-Adapter to condition generation on reference images
- Preserves facial features and identity for characters
- Maintains product appearance across scenes
- Applies identity preservation without requiring LoRA training

**Reference Image Management:**
**Given** entities require consistency
**When** the system processes the scene plan
**Then** it:
- Identifies entities that need reference images (from consistency groupings)
- Generates or retrieves reference images for each entity
- Stores reference images in asset manager
- Associates reference images with generation record

**Identity Preservation:**
**Given** reference images are available for entities
**When** video clips are generated
**Then** the system:
- Uses IP-Adapter to inject reference image embeddings into generation process
- Conditions each scene's generation on relevant entity reference images
- Maintains identity consistency across all scenes featuring the entity
- Handles multiple entities in the same scene

**Integration:**
**Given** IP-Adapter is implemented
**When** a video generation includes character or product consistency requirements
**Then** the system:
- Checks if IP-Adapter is enabled in coherence settings (default: enabled if entities detected)
- Automatically applies IP-Adapter when consistency groups are present and enabled
- Falls back to standard generation when disabled or no consistency requirements exist
- Logs IP-Adapter usage for cost and quality tracking
- Stores reference images and IP-Adapter metadata with generation

**Prerequisites:** Story 7.3 (Enhanced Scene Planning), Story 3.2 (Video Generation)

**Technical Notes:**
- Research and select IP-Adapter implementation (diffusers library, ComfyUI workflows, or custom)
- Implement reference image generation service (text-to-image for entities)
- Create asset manager for storing and retrieving reference images
- Integrate IP-Adapter with Replicate API or video generation service
- For Replicate: Use image input parameters if supported, or pre-process with IP-Adapter locally
- Handle IP-Adapter configuration (strength, conditioning) per entity
- Document IP-Adapter usage patterns and best practices

---

### Story 7.5: LoRA Training Pipeline for Recurring Character/Product Identity [MVP]

As a developer,
I want to implement LoRA training infrastructure and pipeline for recurring characters and products,
So that brand mascots, spokespersons, and flagship products maintain perfect visual consistency across unlimited future ads with a one-time training investment.

**Acceptance Criteria:**

**Infrastructure Setup:**
**Given** the system needs to support LoRA training
**When** infrastructure is provisioned
**Then** it:
- Sets up GPU infrastructure (local GPU, RunPod, Vast.ai, or AWS SageMaker)
- Configures training environment with required dependencies (PyTorch, diffusers, peft, accelerate)
- Establishes secure connection between training infrastructure and main application
- Implements job queue system for async training requests
- Sets up monitoring and logging for training jobs
- Configures storage for training datasets and trained models
- Implements cost tracking for GPU usage

**LoRA Training Pipeline:**
**Given** a user wants to train a LoRA for a recurring character or product
**When** the system processes the training request
**Then** it:
- Accepts training images (multiple angles, expressions, poses, lighting conditions)
- Validates training dataset (minimum images, quality requirements)
- Queues training job in async job system
- Trains LoRA model using the provided images on GPU infrastructure
- Monitors training progress and provides status updates
- Stores trained LoRA model as reusable asset
- Associates LoRA with user account or brand
- Sends notification when training completes

**Training Dataset Management:**
**Given** a user wants to train a character/product LoRA
**When** they upload training images
**Then** the system:
- Accepts images in multiple formats (JPG, PNG, WebP)
- Validates image quality and resolution (minimum 512x512 recommended)
- Requires minimum dataset size (10-20 images recommended, minimum 5)
- Supports dataset augmentation (optional, automatic cropping, resizing, normalization)
- Stores training dataset in secure storage (S3 or local filesystem)
- Provides dataset preview and validation feedback
- Allows users to add/remove images before training starts

**LoRA Model Training:**
**Given** a validated training dataset is available
**When** the LoRA training service processes it
**Then** it:
- Transfers dataset to GPU infrastructure securely
- Trains LoRA model using appropriate base model (Stable Diffusion XL or compatible)
- Configures training parameters (rank: 4-32, learning rate: 1e-4 to 5e-4, epochs: 10-20, batch size: 1-4)
- Monitors training progress and loss (logs every N steps)
- Validates trained LoRA quality (test generation with sample prompts)
- Stores trained LoRA model file (.safetensors format)
- Transfers trained model back to main application storage
- Cleans up temporary files on GPU infrastructure

**Example Training Workflow:**
**Given** a user wants to train a LoRA for their brand mascot
**When** they complete the training workflow
**Then** the system:
- Provides UI for uploading training images (drag-and-drop or file picker)
- Shows example training images (demonstrates angles, expressions, poses needed)
- Validates dataset and provides feedback (e.g., "Need 3 more images with different angles")
- Shows estimated training time and cost
- Starts training job and shows progress (0% → 100% with ETA)
- Sends email/notification when training completes
- Provides test generation interface to validate LoRA quality
- Allows user to retrain if quality is insufficient

**LoRA Usage in Generation:**
**Given** a trained LoRA model exists for an entity
**When** video clips are generated featuring that entity
**Then** the system:
- Loads appropriate LoRA model during generation
- Applies LoRA conditioning to ensure entity consistency
- Maintains perfect visual fidelity across all scenes
- Handles multiple LoRAs in same scene (character + product)
- Falls back to IP-Adapter if LoRA not available or disabled
- Caches LoRA models in memory for performance (if possible)

**LoRA Asset Management:**
**Given** LoRA models are being used
**When** the system manages LoRA assets
**Then** it:
- Stores LoRA models in asset library (S3 or local filesystem with backup)
- Associates LoRAs with specific entities (character names, product IDs)
- Allows users to manage their LoRA library (upload, delete, update, test)
- Tracks LoRA usage across generations (analytics)
- Provides LoRA versioning for updates (retrain and replace)
- Implements access control (users can only access their own LoRAs)
- Provides LoRA sharing capability (optional, for team workspaces)

**Infrastructure Requirements:**
**Given** LoRA training is production-ready
**When** the system is deployed
**Then** it:
- Has GPU infrastructure available (NVIDIA H100, A100, RTX 4090+, or cloud equivalent)
- Implements job queue system (Redis, RabbitMQ, or database-backed queue)
- Has sufficient storage for datasets and models (100GB+ recommended)
- Implements cost tracking and budget limits per user
- Has monitoring and alerting for training failures
- Implements retry logic for transient failures
- Has backup and disaster recovery for trained models

**Integration:**
**Given** LoRA training pipeline is implemented
**When** a video generation includes entities with trained LoRAs
**Then** the system:
- Checks if LoRA is enabled in coherence settings (default: disabled, user must enable)
- Automatically applies LoRA when available and enabled (preferred over IP-Adapter)
- Uses IP-Adapter as fallback if LoRA disabled or not trained
- Logs LoRA usage for quality tracking
- Stores LoRA metadata with generation record
- Shows LoRA usage in generation history

**Prerequisites:** Story 7.3 (Enhanced Scene Planning), Story 7.4 (IP-Adapter)

**Technical Notes:**
- **Infrastructure Options:**
  - **Local GPU:** Direct GPU access if available (fastest, most control)
  - **RunPod:** Cloud GPU service with API integration (recommended for MVP)
  - **Vast.ai:** Cost-effective GPU marketplace
  - **AWS SageMaker:** Enterprise-grade training infrastructure
  - **Hybrid:** Start with RunPod/Vast.ai, migrate to local if scale requires
- **Training Framework:** Use Kohya_ss or PEFT library (Hugging Face)
- **Base Models:** Support Stable Diffusion XL, AnimateDiff, SkyReels compatible models
- **Training Parameters:** 
  - Rank: 16-32 for characters, 8-16 for products (start with 16)
  - Learning rate: 1e-4 (adjust based on results)
  - Epochs: 15-20 (monitor loss, early stopping if overfitting)
  - Batch size: 1-2 (GPU memory dependent)
- **Storage:** Store .safetensors files in S3 or local filesystem with versioning
- **Integration:** Load LoRA weights during video generation inference
- **For Replicate API:** Evaluate LoRA support, may need self-hosted models or pre-processing
- **Cost Management:** Track GPU hours, implement user budget limits, show cost estimates
- **Example Training Dataset:** Provide sample images showing required variety (angles, expressions, poses)
- **Documentation:** Create user guide for preparing training datasets, best practices

---

### Story 7.6: VBench Integration for Automated Quality Control [MVP]

As a developer,
I want to integrate VBench metrics for automated quality assessment,
So that the system can automatically evaluate video quality and trigger regeneration for low-quality clips.

**Acceptance Criteria:**

**VBench Metrics Integration:**
**Given** a video clip has been generated
**When** the quality control service processes it
**Then** it evaluates:
- Temporal quality (subject consistency, background consistency, motion smoothness, dynamic degree)
- Frame-wise quality (aesthetic quality, imaging quality, object class alignment)
- Text-video alignment (prompt adherence)
- Multiple objects assessment (if applicable)

**Automated Quality Assessment:**
**Given** VBench metrics are computed for a clip
**When** the system processes the results
**Then** it:
- Generates quality scores for each dimension (0-100 scale)
- Computes overall quality score
- Compares scores against quality thresholds
- Identifies clips falling below acceptable quality

**Quality Threshold Triggers:**
**Given** a clip's quality scores are below thresholds
**When** the system evaluates the results
**Then** it:
- Automatically triggers regeneration for low-quality clips
- Logs quality issues for analysis
- Tracks regeneration attempts and success rates
- Updates generation progress to reflect regeneration

**Quality Dashboard:**
**Given** quality metrics are being tracked
**When** a video generation completes
**Then** the system:
- Checks if VBench quality control is enabled in coherence settings (default: enabled)
- Runs VBench evaluation only if enabled
- Stores all VBench scores in database
- Makes quality metrics available via API
- Displays quality scores in video detail page (optional)
- Uses metrics for quality feedback loop (Story 7.9)

**Prerequisites:** Story 3.2 (Video Generation)

**Technical Notes:**
- Research VBench implementation (GitHub: Vchitect/VBench)
- Integrate VBench evaluation service into video generation pipeline
- Implement quality threshold configuration (configurable per quality dimension)
- Create quality_metrics table to store VBench scores per clip
- Add quality assessment step after each clip generation
- Implement automatic regeneration logic with retry limits
- Document quality thresholds and regeneration policies

---

### Story 7.7: Enhanced Post-Processing with Brand Palette Preservation [MVP]

As a developer,
I want to enhance post-processing with brand-aware color grading and transition optimization,
So that final videos maintain brand identity while improving visual coherence.

**Acceptance Criteria:**

**Brand-Aware Color Grading:**
**Given** a video with brand color guidelines
**When** post-processing applies color grading
**Then** it:
- Preserves brand color palette from original generation
- Applies color matching between clips while maintaining brand colors
- Uses histogram matching to normalize colors across scenes
- Applies LUTs (Look-Up Tables) for consistent color grading
- Maintains brand visual identity throughout video

**Transition Optimization:**
**Given** multiple clips are being stitched together
**When** transitions are applied
**Then** the system:
- Optimizes crossfade durations based on scene analysis
- Adjusts transition easing for smoother flow
- Uses motion matching for seamless scene linking
- Applies appropriate transition types (hard cut, crossfade, dissolve) based on scene relationship

**Lighting and Style Normalization:**
**Given** clips may have varying lighting and style
**When** post-processing normalizes the video
**Then** it:
- Adjusts exposure to match across clips
- Normalizes contrast and saturation
- Applies texture matching for style consistency
- Enhances sharpness uniformly
- Maintains artistic intent while improving coherence

**Integration:**
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

**Prerequisites:** Story 3.3 (Video Assembly), Story 7.6 (VBench Integration)

**Technical Notes:**
- Enhance existing post-processing service with brand palette awareness
- Implement histogram matching algorithms using OpenCV
- Create LUT generation for brand color palettes
- Integrate transition optimization based on VBench motion smoothness scores
- Use MoviePy and OpenCV for color grading and normalization
- Store brand color guidelines in generation record for post-processing
- Document color grading strategies and brand preservation techniques

---

### Story 7.8: Cross-Scene Entity Consistency Detection (CSFD Score) [MVP]

As a developer,
I want to implement CSFD (Cross-Scene Face Distance) scoring for character-driven ads,
So that the system can quantify and ensure character consistency across multiple scenes.

**Acceptance Criteria:**

**CSFD Score Calculation:**
**Given** a video with a main character appearing in multiple scenes
**When** the consistency detection service processes it
**Then** it:
- Extracts face embeddings from each scene featuring the character
- Computes pairwise distances between face embeddings
- Calculates CSFD score (lower = better consistency)
- Identifies scenes with character appearance drift

**Character Consistency Assessment:**
**Given** CSFD scores are computed for all character appearances
**When** the system evaluates consistency
**Then** it:
- Determines if CSFD score is below acceptable threshold (<0.3 for excellent)
- Flags scenes with high CSFD scores (character drift)
- Provides recommendations for regeneration of inconsistent scenes
- Tracks character consistency across all videos

**Integration:**
**Given** CSFD scoring is implemented
**When** a character-driven video generation completes
**Then** the system:
- Checks if CSFD detection is enabled in coherence settings (default: disabled, character ads only)
- Automatically runs CSFD analysis if enabled and character consistency groups are present
- Skips CSFD analysis if disabled
- Stores CSFD scores in quality_metrics table (if enabled)
- Triggers regeneration for scenes exceeding CSFD threshold (optional, if enabled)
- Makes CSFD scores available for quality feedback loop

**Prerequisites:** Story 7.3 (Enhanced Scene Planning), Story 7.6 (VBench Integration)

**Technical Notes:**
- Implement face detection and embedding extraction (ArcFace, FaceNet, or similar)
- Use computer vision library (OpenCV, face_recognition) for face detection
- Implement embedding extraction and distance calculation
- Create CSFD scoring service integrated with quality control pipeline
- Store CSFD scores per scene in quality_metrics table
- Configure CSFD threshold (recommended: <0.3 for excellent, <0.5 for good)
- Document CSFD scoring methodology and thresholds

---

### Story 7.9: ControlNet Integration for Compositional Consistency [MVP]

As a developer,
I want to implement ControlNet for enforcing compositional and structural consistency,
So that scene layouts, character positions, and perspectives remain consistent across scenes.

**Acceptance Criteria:**

**ControlNet Implementation:**
**Given** a video generation includes scenes requiring compositional consistency
**When** the system generates video clips
**Then** it:
- Uses ControlNet with depth maps for perspective consistency
- Applies layout control for scene structure
- Enforces character pose consistency using OpenPose
- Maintains compositional consistency across related scenes

**Depth Map Control:**
**Given** scenes share similar environments or perspectives
**When** depth maps are generated and applied
**Then** the system:
- Generates depth maps for reference scenes
- Uses depth maps to condition subsequent scene generation
- Maintains consistent perspective and spatial relationships
- Ensures proper depth perception across scenes

**Layout Control:**
**Given** scenes require consistent layout (product placement, character position)
**When** layout control is applied
**Then** the system:
- Defines layout structure for key scenes
- Enforces layout consistency across scenes
- Maintains product placement and positioning
- Ensures visual composition matches storyboard

**Integration:**
**Given** ControlNet is implemented
**When** a video generation includes compositional consistency requirements
**Then** the system:
- Checks if ControlNet is enabled in coherence settings (default: disabled, advanced feature)
- Automatically applies ControlNet when enabled and layout/depth requirements are present
- Skips ControlNet if disabled
- Uses ControlNet in conjunction with IP-Adapter for full consistency (if both enabled)
- Logs ControlNet usage for analysis
- Stores ControlNet configuration with generation record

**Prerequisites:** Story 7.3 (Enhanced Scene Planning), Story 7.4 (IP-Adapter), Story 7.5 (LoRA)

**Technical Notes:**
- Research ControlNet implementation options (diffusers, ComfyUI, or custom)
- Implement depth map generation service (MiDaS or similar)
- Create layout control service for scene structure
- Integrate ControlNet with video generation pipeline
- For Replicate: Evaluate ControlNet support or pre-process locally
- Handle ControlNet configuration (strength, conditioning) per scene
- Document ControlNet usage patterns and best practices

---

### Story 7.10: Quality Feedback Loop with Research Metrics [MVP]

As a developer,
I want to implement a comprehensive quality feedback loop using VBench, CSFD, and coherence metrics,
So that the system continuously improves prompt optimization and consistency techniques based on successful outcomes.

**Acceptance Criteria:**

**Comprehensive Metrics Tracking:**
**Given** a video has been generated
**When** the quality feedback system processes it
**Then** it tracks:
- VBench scores (temporal quality, aesthetic quality, prompt alignment)
- CSFD scores (character consistency, if applicable)
- Coherence scores (color, lighting, style consistency)
- User acceptance metrics (download rate, regeneration rate)
- Generation success indicators

**Pattern Recognition:**
**Given** quality metrics are being tracked over multiple generations
**When** the system analyzes patterns
**Then** it:
- Identifies which prompt optimizations lead to better VBench scores
- Learns which consistency techniques (IP-Adapter, seed control, ControlNet) are most effective
- Correlates scene planning quality with final video quality
- Discovers optimal configurations for different ad types

**Continuous Improvement:**
**Given** the feedback loop has learned from outcomes
**When** new videos are generated
**Then** the system:
- Applies learned improvements to scene planning
- Adjusts consistency technique selection based on success rates
- Refines quality thresholds based on user acceptance patterns
- Improves overall video quality over time

**Analytics and Reporting:**
**Given** quality metrics are being tracked
**When** system administrators review analytics
**Then** they can:
- View quality trends over time
- Identify which techniques improve which metrics
- Adjust system parameters based on data
- Export quality reports for analysis

**Prerequisites:** Story 7.6 (VBench Integration), Story 7.8 (CSFD Score), Story 7.7 (Post-Processing)

**Technical Notes:**
- Enhance quality_metrics table to store all research-recommended metrics
- Implement analytics service for pattern recognition
- Create quality dashboard for administrators (optional)
- Use machine learning for pattern recognition (optional, can start with rule-based)
- Store anonymized quality data for learning
- Implement A/B testing framework for technique comparison
- Document quality improvement strategies and learned patterns

---

## Epic 8: CLI MVP - Image Generation Feedback Loops

**Goal:** Provide rapid-iteration CLI tools for image prompt enhancement and image generation with automatic quality scoring, enabling developers to quickly test and refine image generation workflows before building UI.

**Status:** Not started.

### Story 8.1: Image Prompt Feedback Loop CLI (FR-037)

As a **developer**,  
I want a CLI tool for iterative image prompt enhancement using two-agent feedback loops,  
So that I can rapidly refine prompts for image generation without UI overhead.

**Acceptance Criteria:**

**Given** I have a basic image prompt  
**When** I run `python enhance_image_prompt.py prompt.txt`  
**Then** the CLI tool:
- Uses Agent 1 (Cinematographer/Creative Director) to enhance the prompt with:
  - Camera body and lens details (e.g., "Canon EOS R5, 85mm f/1.2 lens")
  - Lighting direction and quality (e.g., "soft golden morning light", "dramatic side lighting")
  - Composition notes (framing, depth, rule of thirds)
  - Film stock/color science references
  - Mood and atmosphere descriptors
  - Aspect ratio and stylization hints
- Uses Agent 2 (Prompt Engineer) to critique and score the enhanced prompt
- Iterates between agents (max 3 rounds) until score threshold is met or convergence detected
- Scores prompts on multiple dimensions based on Prompt Scoring Guide:
  - Completeness (0-100): Does it have all necessary elements?
  - Specificity (0-100): Are visual details clear and unambiguous?
  - Professionalism (0-100): Is it ad-quality language?
  - Cinematography (0-100): Does it include camera/composition details?
  - Brand alignment (0-100): Are brand guidelines present and clear?
  - Overall score (weighted average)

**And** the CLI:
- Saves all prompt versions to `output/image_prompt_traces/{timestamp}/`:
  - `00_original_prompt.txt` - Original user input
  - `01_agent1_iteration_1.txt` - First Cinematographer enhancement
  - `02_agent2_iteration_1.txt` - First Prompt Engineer critique + score
  - `03_agent1_iteration_2.txt` - Second enhancement (if iterated)
  - `04_agent2_iteration_2.txt` - Second critique (if iterated)
  - `05_final_enhanced_prompt.txt` - Final enhanced prompt
  - `prompt_trace_summary.json` - Metadata: scores, iterations, timestamps
- Prints enhancement results to console with scores and iteration history
- Supports stdin input: `echo "prompt" | python enhance_image_prompt.py -`
- Supports custom output directories: `--output-dir ./my_traces`
- Supports iteration control: `--max-iterations 5 --threshold 90`
- Follows guidelines from Prompt Scoring Guide (structure like scene description, camera cues, lighting cues)

**And** prompt enhancement follows best practices from Prompt Scoring Guide:
- Structure prompts like scene descriptions (who/what → action → where/when → style)
- Use camera cues: "wide aerial shot", "close-up portrait", "telephoto shot", "macro photograph"
- Use lighting cues: "soft golden morning light", "harsh neon glow", "dramatic side lighting"
- Limit to one scene or idea per prompt
- Use natural language, not keyword stuffing

**Prerequisites:** Story 7.3 Phase 1 (Two-Agent Prompt Enhancement pattern).

**Technical Notes:**
- Reuse `prompt_enhancement.py` service pattern from Story 7.3
- Create `enhance_image_prompt.py` CLI tool similar to `enhance_prompt.py`
- Adapt agent prompts for image-specific enhancement (cinematography focus)
- Integrate Prompt Scoring Guide guidelines into agent system prompts
- Use same scoring mechanism (hybrid: rule-based + LLM-based)
- Save trace files for transparency and debugging

---

### Story 8.2: Image Generation Feedback Loop CLI (FR-036)

As a **developer**,  
I want a CLI tool for generating images with automatic quality scoring,  
So that I can rapidly iterate on image generation and select the best candidates.

**Acceptance Criteria:**

**Given** I have an enhanced image prompt (from Story 8.1)  
**When** I run `python generate_images.py enhanced_prompt.txt --num-variations 8`  
**Then** the CLI tool:
- Calls a text-to-image model (e.g., SDXL on Replicate) to generate multiple image variations (4-8 default)
- All images share the specified aspect ratio
- All follow the enhanced prompt

**And** after generation, the system automatically scores each image using multiple benchmarks:
- **PickScore** (primary): Human preference prediction (0-100, higher = better)
- **CLIP-Score**: Image-text alignment (0-100, higher = better)
- **VQAScore**: Compositional semantic alignment (0-100, higher = better)
- **Aesthetic Predictor** (LAION): Aesthetic quality (1-10 scale)
- **Overall Quality Score**: Weighted combination of all metrics

**And** the CLI:
- Saves all generated images to `output/image_generations/{timestamp}/`:
  - `image_001.png`, `image_002.png`, etc. (numbered by quality rank)
  - `image_001_metadata.json`, `image_002_metadata.json` (scores, prompt, model, seed)
- Saves generation trace to `output/image_generations/{timestamp}/generation_trace.json`:
  - All prompts used (original, enhanced)
  - All images generated with file paths
  - All quality scores per image
  - Model settings, seeds, timestamps
  - Cost tracking
- Prints results to console:
  - Ranked list of images by overall quality score
  - Top 3 images highlighted
  - Score breakdown per image (PickScore, CLIP-Score, VQAScore, Aesthetic)
  - File paths for manual viewing
- Supports custom output directory: `--output-dir ./my_images`
- Supports aspect ratio control: `--aspect-ratio 16:9`
- Supports seed control: `--seed 12345` (for reproducibility)

**And** the system:
- Automatically selects the top-scoring image as "best candidate"
- Provides comparison summary showing why top image scored highest
- Logs all API calls and costs for transparency

**Prerequisites:** Story 8.1 (Image Prompt Enhancement), Story 3.2 (Generation Infrastructure).

**Technical Notes:**
- Create `generate_images.py` CLI tool
- Integrate Replicate SDXL API (or other text-to-image model)
- Implement automatic scoring using:
  - PickScore model (Stability AI open-source)
  - CLIP-Score (Hugging Face transformers)
  - VQAScore (if available)
  - LAION Aesthetic Predictor
- Create `image_quality_scoring.py` service to compute all metrics
- Store images and metadata in organized directory structure
- Support manual file opening (images saved to disk, user opens manually)
- Log all operations for transparency

---

### Story 8.3: Storyboard Creation CLI (Start/End Frames for Video Clips)

As a **developer**,  
I want a CLI tool to create storyboards (start and end frames) for individual video clips,  
So that I can visualize the motion arc before generating video.

**Acceptance Criteria:**

**Given** I have a video clip prompt (or enhanced prompt from Story 8.1)  
**When** I run `python create_storyboard.py clip_prompt.txt --num-clips 3`  
**Then** the CLI tool:
- Uses VideoDirectorGPT-style planning to break the prompt into individual video clips
- For each clip, generates:
  - **Start frame**: The initial frame of the video clip
  - **End frame**: The final frame of the video clip
  - **Motion description**: What happens between start and end (camera movement, subject motion)
- Uses enhanced image generation (Story 8.2) to create start/end frames

**And** the CLI:
- Saves storyboard to `output/storyboards/{timestamp}/`:
  - `clip_001_start.png`, `clip_001_end.png`
  - `clip_002_start.png`, `clip_002_end.png`
  - `clip_003_start.png`, `clip_003_end.png`
  - `storyboard_metadata.json`:
    - Clip descriptions
    - Start/end frame prompts
    - Motion descriptions
    - Camera movements
    - Shot list metadata (from VideoDirectorGPT planning)
- Prints storyboard summary to console:
  - List of clips with start/end frame descriptions
  - Motion arcs for each clip
  - File paths for manual viewing
- Supports custom output directory: `--output-dir ./my_storyboard`
- Integrates with Story 8.1 for prompt enhancement (optional flag: `--enhance-prompts`)

**And** storyboard creation includes:
- VideoDirectorGPT-style planning with:
  - Shot list with camera metadata (camera movement, shot size, perspective, lens type)
  - Scene dependencies and narrative flow
  - Consistency groupings (if applicable)
- Start/end frame prompts derived from shot list
- Motion descriptions for image-to-video generation

**Prerequisites:** Story 8.1 (Image Prompt Enhancement), Story 8.2 (Image Generation), Story 7.3 Phase 2 (VideoDirectorGPT Planning - if available, otherwise basic planning).

**Technical Notes:**
- Create `create_storyboard.py` CLI tool
- Integrate VideoDirectorGPT planning (or basic scene planning if Phase 2 not complete)
- For each clip, generate two images (start + end) using Story 8.2
- Store storyboard as organized directory with metadata
- Support manual file opening for visual review
- Log all operations for transparency

---

### Story 8.4: Unified Narrative Generation for Storyboard Enhancement

As a **developer**,  
I want the storyboard enhancement service to generate a unified narrative document that describes the overall ad story,  
So that individual scene prompts are guided by a cohesive narrative and video generation can maintain story coherence across all scenes.

**Acceptance Criteria:**

1. **Given** I have a reference image and enhanced prompt (from Stories 8.1 and 8.2)  
   **When** the storyboard prompt enhancement service processes them  
   **Then** the service generates a unified narrative document BEFORE creating individual scene prompts that includes:
   - Overall Ad Story (2-3 paragraph narrative following Sensory Journey framework)
   - Emotional Arc (how emotions progress across scenes)
   - Scene Connections (how scenes transition narratively and visually)
   - Visual Progression (how visuals evolve across scenes)
   - Product Reveal Strategy (hidden → partial → full)
   - Brand Narrative (how brand identity is woven throughout)

2. **Given** the unified narrative document is generated  
   **When** individual scene prompts are created  
   **Then** the Cinematic Creative agent uses the narrative document as context to ensure:
   - Each scene contributes to the overall story
   - Narrative coherence between scenes
   - Emotional arc progression
   - Visual progression strategy
   - Product reveal strategy execution

3. **Given** the storyboard enhancement completes  
   **When** the service saves outputs  
   **Then** it saves the unified narrative document as:
   - `unified_narrative.md` (human-readable markdown)
   - `unified_narrative.json` (structured JSON for programmatic use)
   - Both saved to `output/storyboards/{timestamp}/storyboard_enhancement_trace/`

4. **Given** the unified narrative document exists  
   **When** Epic 9 video generation processes the storyboard  
   **Then** video generation can use the narrative document to:
   - Guide video prompt enhancement with narrative context
   - Ensure video clips maintain story coherence
   - Apply consistent emotional tone across scenes
   - Maintain visual progression throughout the video
   - Create smooth narrative transitions between clips

**Prerequisites:** Story 8.3 (Storyboard Creation CLI with prompt enhancement)

**Technical Notes:**
- Add narrative generation as Step 0 in `enhance_storyboard_prompts()` function
- Use two-agent iterative feedback loop (Creative Director + Editor) similar to scene prompt generation
- Agent 1 (Creative Director): Generates narrative document with full context (original prompt, visual elements, intent, framework)
- Agent 2 (Editor): Critiques and scores narrative on 6 dimensions (coherence, emotional arc, scene connections, visual progression, brand integration, framework alignment)
- Iterative loop: Max 3 rounds, threshold 85.0, convergence detection
- Generate both markdown and JSON formats from final narrative
- Update `StoryboardEnhancementResult` dataclass to include narrative paths, content, and iteration history
- Pass narrative document as context to Cinematic Creative agent during scene prompt generation
- Narrative document enables Epic 9 to maintain story coherence during video generation
- LLM API: OpenAI GPT-4 Turbo (same API as existing agents, but specialized system prompts for narrative)

---

## Epic 9: CLI MVP - Video Generation Feedback Loops

**Goal:** Provide rapid-iteration CLI tools for video prompt enhancement and video generation with automatic VBench quality scoring, enabling developers to quickly test and refine video generation workflows before building UI.

**Status:** Not started.

### Story 9.1: Video Prompt Feedback Loop CLI (FR-039)

As a **developer**,  
I want a CLI tool for iterative video prompt enhancement using two-agent feedback loops with VideoDirectorGPT enhancements,  
So that I can rapidly refine prompts for video generation without UI overhead.

**Acceptance Criteria:**

**Given** I have a basic video prompt (or motion prompt for image-to-video)  
**When** I run `python enhance_video_prompt.py prompt.txt --video-mode`  
**Then** the CLI tool:
- Uses Agent 1 (Video Director/Creative Director) to enhance the prompt with:
  - Camera framing and movement (e.g., "wide aerial shot", "steady tracking shot", "low-angle view")
  - Action beats and timing cues
  - Lighting and color palette
  - Motion intensity and style
  - Temporal continuity hints
- Uses Agent 2 (Prompt Engineer) to critique and score the enhanced prompt
- Iterates between agents (max 3 rounds) until score threshold is met or convergence detected
- Applies VideoDirectorGPT-style enhancements (if Story 7.3 Phase 2 available):
  - Shot list with camera metadata (camera movement, shot size, perspective, lens type)
  - Scene dependencies and narrative flow
  - Consistency groupings for entities
  - Entity descriptions with consistency requirements
- Scores prompts on multiple dimensions based on Prompt Scoring Guide:
  - Completeness (0-100): Does it have all necessary elements?
  - Specificity (0-100): Are visual and motion details clear?
  - Professionalism (0-100): Is it ad-quality language?
  - Cinematography (0-100): Does it include camera/motion details?
  - Temporal coherence (0-100): Does it describe smooth, plausible motion?
  - Brand alignment (0-100): Are brand guidelines present?
  - Overall score (weighted average)

**And** the CLI:
- Saves all prompt versions to `output/video_prompt_traces/{timestamp}/`:
  - `00_original_prompt.txt` - Original user input
  - `01_agent1_iteration_1.txt` - First Video Director enhancement
  - `02_agent2_iteration_1.txt` - First Prompt Engineer critique + score
  - `03_agent1_iteration_2.txt` - Second enhancement (if iterated)
  - `04_agent2_iteration_2.txt` - Second critique (if iterated)
  - `05_final_enhanced_prompt.txt` - Final enhanced prompt
  - `06_videodirectorgpt_plan.json` - VideoDirectorGPT planning output (if available)
  - `prompt_trace_summary.json` - Metadata: scores, iterations, timestamps
- Prints enhancement results to console with scores and iteration history
- Supports stdin input: `echo "prompt" | python enhance_video_prompt.py -`
- Supports custom output directories: `--output-dir ./my_traces`
- Supports iteration control: `--max-iterations 5 --threshold 90`
- Follows guidelines from Prompt Scoring Guide:
  - Structure like one-sentence screenplay (subject → action → setting → style → mood)
  - Use film terminology for clarity
  - Limit to one scene or action per prompt
  - Use visual language (describe what camera sees)
  - Specify camera framing, depth of field, action beats, lighting, palette

**And** for image-to-video prompts (motion prompts):
- Enhances motion descriptions with:
  - Camera movement (pan, tilt, dolly, static, tracking)
  - Motion intensity (subtle, moderate, dynamic)
  - Frame rate considerations
  - Negative prompts for unwanted motion (e.g., "jerky, flicker, inconsistent")

**And** for storyboard processing (building upon Epic 8.3/8.4):
- **Given** I have a storyboard JSON file from Story 8.3 (`storyboard_metadata.json`)
- **When** I run `python enhance_video_prompt.py --storyboard storyboard_metadata.json`
- **Then** the CLI tool:
  - Loads the storyboard JSON file and parses clip information
  - **Loads the unified narrative document** (from `unified_narrative_path` in storyboard metadata) to use as narrative context for maintaining story coherence across clips
  - For each clip in the storyboard:
    - Extracts the clip's `motion_description` as the base motion prompt
    - Extracts camera metadata: `camera_movement`, `shot_size`, `perspective`, `lens_type`
    - Uses start/end frame paths as context (for image-to-video generation)
    - **Uses unified narrative document as context** to ensure motion prompts:
      - Maintain story coherence with overall narrative
      - Follow the emotional arc progression from the narrative
      - Apply consistent visual progression strategy
      - Create smooth narrative transitions between clips
    - Enhances the motion prompt using **two-agent feedback loop** (per clip):
      - Agent 1 (Video Director): Enhances motion description with detailed camera movement specifications, motion intensity, frame rate considerations, temporal continuity hints, and **narrative context integration** (emotional arc, visual progression, scene connections from unified narrative)
      - Agent 2 (Prompt Engineer): Critiques and scores the enhanced motion prompt
      - Iterates (max 3 rounds) until score threshold met or convergence detected
    - Generates negative prompts for unwanted motion
  - Saves enhanced motion prompts per clip with per-clip trace files
  - Saves `storyboard_enhanced_motion_prompts.json` with all clips' enhanced prompts and scores

**Prerequisites:** Story 7.3 Phase 1 (Two-Agent Prompt Enhancement), Story 8.1 (Image Prompt Enhancement pattern), Story 8.3 (Storyboard Creation), Story 8.4 (Unified Narrative Generation).

**Technical Notes:**
- Create `enhance_video_prompt.py` CLI tool
- Reuse `prompt_enhancement.py` service pattern from Story 7.3
- Adapt agent prompts for video-specific enhancement (motion, temporal coherence focus)
- Integrate VideoDirectorGPT planning (if Story 7.3 Phase 2 available)
- Integrate Prompt Scoring Guide guidelines into agent system prompts
- Use same scoring mechanism (hybrid: rule-based + LLM-based) with video-specific dimensions
- Save trace files for transparency and debugging

---

### Story 9.2: Video Generation Feedback Loop CLI (FR-040)

As a **developer**,  
I want a CLI tool for generating videos with automatic VBench quality scoring,  
So that I can rapidly iterate on video generation and select the best candidates.

**Acceptance Criteria:**

**Given** I have:
- An enhanced video prompt (from Story 9.1), OR
- A hero frame image + motion prompt (from Epic 8), OR
- Storyboard start/end frames (from Story 8.3)

**When** I run `python generate_videos.py enhanced_prompt.txt --num-attempts 3`  
**Then** the CLI tool:
- For text-to-video: Calls a text-to-video model (e.g., Kling/Wan/PixVerse on Replicate)
- For image-to-video: Calls an image-to-video model with hero frame + motion prompt
- Generates multiple video attempts (default: 3, configurable)
- All videos follow the enhanced prompt and settings

**And** after generation, the system automatically scores each video using VBench:
- **Temporal Quality**:
  - Subject identity consistency (0-100)
  - Background consistency (0-100)
  - Motion smoothness (0-100)
  - Dynamic degree (0-100)
- **Frame-wise Quality**:
  - Aesthetic quality (0-100)
  - Imaging quality (0-100)
  - Object class alignment (0-100)
- **Text-Video Alignment**:
  - Prompt adherence (0-100)
- **Overall Quality Score**: Weighted combination of all VBench dimensions

**And** the CLI:
- Saves all generated videos to `output/video_generations/{timestamp}/`:
  - `video_001.mp4`, `video_002.mp4`, etc. (numbered by quality rank)
  - `video_001_metadata.json`, `video_002_metadata.json` (scores, prompt, model, settings)
- Saves generation trace to `output/video_generations/{timestamp}/generation_trace.json`:
  - All prompts used (original, enhanced, motion, negative)
  - All videos generated with file paths
  - All VBench scores per video (all 16 dimensions)
  - Model settings, seeds, timestamps, costs
  - Hero frame path (if image-to-video)
  - Storyboard references (if used)
- Prints results to console:
  - Ranked list of videos by overall quality score
  - Top video highlighted as "system-selected best"
  - VBench score breakdown per video (key dimensions)
  - File paths for manual viewing
  - Cost summary
- Supports custom output directory: `--output-dir ./my_videos`
- Supports image-to-video mode: `--image-to-video --hero-frame path/to/image.png --motion-prompt "camera pans left"`
- Supports storyboard mode: `--storyboard path/to/storyboard.json`
- Supports negative prompts: `--negative-prompt "jerky, flicker, inconsistent"`

**And** the system:
- Automatically selects the top-scoring video as "system-selected best"
- Provides comparison summary showing why top video scored highest
- Logs all API calls and costs for transparency
- Supports human feedback: After viewing videos manually, user can provide feedback via CLI for next iteration

**Prerequisites:** Story 9.1 (Video Prompt Enhancement), Story 7.6 (VBench Integration), Story 3.2 (Video Generation Infrastructure).

**Technical Notes:**
- Create `generate_videos.py` CLI tool
- Integrate Replicate image-to-video APIs (Kling, Wan, PixVerse) or text-to-video APIs
- Reuse VBench integration from Story 7.6 (`quality_control.py`)
- Store videos and metadata in organized directory structure
- Support manual file opening (videos saved to disk, user opens manually)
- Log all operations for transparency
- Support feedback loop: After human review, incorporate feedback into next iteration

---

### Story 9.3: Integrated Feedback Loop CLI (Complete Workflow)

As a **developer**,  
I want a unified CLI tool that orchestrates the complete feedback loop workflow,  
So that I can rapidly iterate through the entire pipeline: image prompt → image generation → video prompt → video generation.

**Acceptance Criteria:**

**Given** I have a starting prompt (text or image)  
**When** I run `python feedback_loop.py start_prompt.txt --workflow full`  
**Then** the CLI tool orchestrates the complete workflow:
1. **Image Prompt Feedback Loop** (Story 8.1):
   - Enhances prompt using two-agent approach
   - Saves trace files
   - Outputs final enhanced image prompt
2. **Image Generation Feedback Loop** (Story 8.2):
   - Generates multiple image variations
   - Scores images using PickScore, CLIP-Score, VQAScore, Aesthetic
   - Selects best image candidate
   - Saves images and scores
3. **Storyboard Creation** (Story 8.3, optional):
   - Creates start/end frames for video clips (if multi-clip)
   - Saves storyboard
4. **Video Prompt Feedback Loop** (Story 9.1):
   - Enhances video/motion prompt using two-agent approach + VideoDirectorGPT
   - Saves trace files
   - Outputs final enhanced video prompt
5. **Video Generation Feedback Loop** (Story 9.2):
   - Generates multiple video attempts
   - Scores videos using VBench
   - Selects best video candidate
   - Saves videos and scores

**And** the CLI:
- Saves complete workflow trace to `output/feedback_loops/{timestamp}/`:
  - All intermediate outputs (prompts, images, videos)
  - All scores and metrics
  - Complete iteration history
  - `workflow_summary.json` with end-to-end metrics
- Prints workflow summary to console:
  - Final outputs (best image, best video)
  - Quality scores at each stage
  - Cost breakdown
  - File paths for manual review
- Supports partial workflows:
  - `--workflow image-only` (stops after image generation)
  - `--workflow video-only` (starts from existing image)
  - `--workflow prompt-only` (just prompt enhancement)
- Supports iteration control:
  - `--max-iterations-image 3` (image prompt iterations)
  - `--max-iterations-video 3` (video prompt iterations)
  - `--num-image-variations 8` (image generation count)
  - `--num-video-attempts 3` (video generation count)
- Supports human feedback at each stage:
  - Pauses after image generation for manual review
  - Pauses after video generation for manual review
  - Accepts feedback via CLI prompts
  - Incorporates feedback into next iteration

**And** the workflow provides transparency:
- All prompts, scores, and outputs are logged
- All files are saved for manual review
- Complete trace of decision-making process
- Cost tracking at each stage

**Prerequisites:** Story 8.1, Story 8.2, Story 8.3, Story 9.1, Story 9.2.

**Technical Notes:**
- Create `feedback_loop.py` CLI tool that orchestrates all previous CLI tools
- Chain together: `enhance_image_prompt.py` → `generate_images.py` → `enhance_video_prompt.py` → `generate_videos.py`
- Support interactive mode for human feedback
- Create unified trace format for end-to-end workflow
- Support resume from checkpoints (if workflow interrupted)
- Log all operations for full transparency

---

### Story 9.4: Enhanced Reference Image Generation with Prompt Enhancement and Quality Scoring

As a **user**,  
I want reference images generated using enhanced prompts and quality scoring,  
So that I get higher quality, more consistent reference images for my video generation.

**Acceptance Criteria:**

1. **Given** I start a video generation with the enhanced reference image feature enabled
   **When** the system generates reference images for each scene
   **Then** the system:
   - Enhances each scene's image generation prompt using iterative two-agent enhancement:
     - Agent 1 (Creative Director): Enhances prompt with visual details, style, composition, lighting
     - Agent 2 (Prompt Engineer): Critiques and scores the enhanced prompt
     - Iterates up to 4 rounds until score threshold is met or convergence detected
     - Scores prompts on dimensions: Completeness, Specificity, Professionalism, Cinematography, Brand Alignment
   - Generates 4 image variations per scene using the enhanced prompt
   - Scores all 4 variations using quality metrics:
     - PickScore (human preference prediction, 0-100)
     - CLIP-Score (image-text alignment, 0-100)
     - Aesthetic Predictor (aesthetic quality, 0-100)
     - Overall Quality Score (weighted combination)
   - Ranks all variations by overall quality score
   - Selects the best-ranked image (rank 1) as the reference image for the scene
   - Checks if selected image's quality score is ≥ 30:
     - If score ≥ 30: Proceeds with selected image
     - If score < 30: Logs warning with score but proceeds with selected image
   - Uses selected reference image as input for next scene's generation (maintains sequential chaining)
   - Saves trace files to `output/reference_image_traces/{generation_id}/scene_{N}/`:
     - `00_original_prompt.txt` - Original scene prompt
     - `01_agent1_iteration_1.txt` - First Creative Director enhancement
     - `02_agent2_iteration_1.txt` - First Prompt Engineer critique + score
     - `03_agent1_iteration_2.txt` - Second enhancement (if iterated)
     - `04_agent2_iteration_2.txt` - Second critique (if iterated)
     - ... (up to 4 iterations)
     - `final_enhanced_prompt.txt` - Final enhanced prompt used for generation
     - `prompt_trace_summary.json` - Enhancement metadata: scores, iterations, timestamps
     - `generation_trace.json` - Image generation metadata: variations, scores, rankings, selected image
   - Cleans up trace files immediately after reference image generation completes (no retention)
   - Updates progress: "Enhancing prompts for reference images" → "Generating reference image variations" → "Scoring and ranking reference images"

2. **Given** the system maintains sequential chaining for visual consistency
   **Then** reference image generation:
   - First scene: Uses user's initial reference image (if provided) as base for first scene's generation
   - Subsequent scenes: Uses previous scene's best-ranked reference image as reference for next scene
   - Maintains consistency markers, continuity notes, and consistency guidelines from LLM planning
   - Ensures visual coherence across all scenes

3. **Given** I start a video generation
   **When** the system processes the generation request
   **Then** the enhanced reference image generation is enabled by default for all users:
   - No optional toggle required (feature is always on)
   - No backward compatibility mode (replaces previous approach entirely)
   - All new generations use enhanced prompt + quality scoring workflow

4. **Given** reference image generation completes
   **When** the system has selected the best reference images for all scenes
   **Then** the system:
   - Logs quality scores for each scene's selected reference image
   - Logs warnings for any scenes where quality score < 30
   - Continues with video generation pipeline using selected reference images
   - Cleans up all trace files immediately after completion

5. **Given** an error occurs during prompt enhancement or image generation
   **When** the system encounters the error
   **Then** the system:
   - Logs the error with context (scene number, step, error details)
   - Falls back gracefully: Uses original prompt (without enhancement) and generates single image
   - Continues pipeline with fallback image
   - Does not fail the entire generation due to enhancement errors

**Prerequisites:** Story 8.3 (Storyboard Creation CLI), Story 8.4 (Unified Narrative Generation), Epic 3 (Progress Tracking), existing prompt enhancement service, existing image generation service, existing quality scoring service.

**Technical Notes:**
- Replace `generate_images_with_sequential_references()` call in `process_generation()` (around line 339)
- Use `app.services.pipeline.prompt_enhancement.enhance_prompt_iterative()` for prompt enhancement
- Use `app.services.image_generation.generate_images()` for generating variations
- Use `app.services.pipeline.image_quality_scoring.score_image()` for quality scoring
- Use `app.services.pipeline.image_quality_scoring.rank_images_by_quality()` for ranking
- Configuration: 4 variations per scene, 4 enhancement iterations, quality threshold 30.0
- Trace cleanup: Immediate (delete trace files after generation completes)
- Update progress tracking to include enhancement and scoring steps
- Error handling: Fallback to original prompt if enhancement fails, retry once if generation fails, use first image if scoring fails
- Performance overhead: ~33-70s per scene (2-5 minutes for 4 scenes)

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
- **FR-024:** Video Editor Access → Epic 6, Story 6.1
- **FR-025:** Timeline Interface → Epic 6, Story 6.2
- **FR-026:** Clip Trimming → Epic 6, Story 6.3
- **FR-027:** Clip Splitting → Epic 6, Story 6.4
- **FR-028:** Clip Merging → Epic 6, Story 6.5
- **FR-029:** Editor Save and Export → Epic 6, Story 6.6
- **FR-030:** Video Coherence Analysis → Epic 7, Story 7.6 (VBench), Story 7.8 (CSFD), Story 7.7 (Post-Processing)
- **FR-031:** Coherence Enhancement → Epic 7, Story 7.1 (Seed Control), Story 7.4 (IP-Adapter), Story 7.5 (LoRA), Story 7.7 (Post-Processing), Story 7.9 (ControlNet)
- **FR-032:** Prompt Optimization via LLM → Epic 7, Story 7.3 (Enhanced Planning), Story 7.10 (Feedback Loop)
- **FR-033:** Quality Feedback Loop → Epic 7, Story 7.10
- **FR-034:** Profile Display → Epic 5, Story 5.1 (duplicate of FR-022)
- **FR-035:** User Stats Update → Epic 5, Story 5.2 (duplicate of FR-023)
 - **FR-036:** Hero Frame Generation (Text → Photo) → Epic 8, Story 8.2 (CLI MVP)
 - **FR-037:** Cinematographer-Level Prompt Enhancement for Images → Epic 8, Story 8.1 (CLI MVP)
 - **FR-038:** Hero Frame Iteration & Selection → Epic 8, Story 8.2 (CLI MVP with automatic scoring)
 - **FR-039:** Image-to-Video Generation (Photo → Video) from Hero Frame → Epic 9, Story 9.2 (CLI MVP)
 - **FR-040:** Automated Multi-Attempt Generation with VBench-Based Selection → Epic 9, Story 9.2 (CLI MVP)
 - **FR-041:** Iteration Workspace & Human-in-the-Loop Refinement → Epic 9, Story 9.3 (CLI MVP - integrated workflow)
 - **FR-042:** Iterative Refinement Workflow & Versioning → Epic 9, Story 9.3 (CLI MVP - complete feedback loop)
 - **FR-043:** Quality Dashboard & Benchmarks → Epic 9, Story 9.2 (CLI MVP - VBench scoring)
 - **FR-044:** Integration with Existing Pipeline & Epics → Epic 9, Story 9.3 (CLI MVP - workflow orchestration)

---

## Summary

This epic breakdown decomposes all 35 functional requirements from the PRD into 7 epics and 29 implementable stories. Each story is sized for focused development work, with detailed BDD-style acceptance criteria and technical implementation notes.

**Epic Sequencing:**
1. **Epic 1 (Foundation)** - Must be completed first, establishes infrastructure (5 stories: 1.1-1.4 ✅ COMPLETED, 1.5 pending)
2. **Epic 2 (User Authentication)** ✅ COMPLETED - Enables user access, required before video features (4 stories)
3. **Epic 3 (Video Generation Pipeline)** ✅ COMPLETED - Core product functionality (4 stories)
4. **Epic 4 (Video Management)** ✅ COMPLETED - Enables users to view and manage their videos (4 stories)
5. **Epic 5 (User Profile)** ✅ COMPLETED - Provides usage tracking and account information (2 stories)
6. **Epic 6 (Video Editing)** - Enables users to edit generated videos with timeline-based editor (6 stories)
7. **Epic 7 (Multi-Scene Coherence & Quality Optimization)** [MVP: Stories 7.0-7.4] - Implements state-of-the-art generation-time consistency techniques (seed control, IP-Adapter, LoRA training with infrastructure setup, VideoDirectorGPT-style planning) to ensure professional multi-scene coherence. MVP includes dev tool for testing coherence settings (Story 7.0), seed control (7.1), parallel generation comparison tool (7.2), enhanced LLM planning (7.3), IP-Adapter (7.4), and LoRA training pipeline (7.5). Growth phase (7.6-7.10) includes advanced quality control (VBench, CSFD, ControlNet) and feedback loops. Quality is priority; cost and generation time are not constraints.
8. **Epic 8 (CLI MVP - Image Generation Feedback Loops)** [Not Started] - Provides rapid-iteration CLI tools for image prompt enhancement and image generation with automatic quality scoring (PickScore, CLIP-Score, VQAScore, Aesthetic Predictor). Includes: image prompt feedback loop using two-agent approach (8.1), image generation with automatic scoring (8.2), and storyboard creation with start/end frames (8.3). Enables developers to quickly test and refine image generation workflows before building UI.
9. **Epic 9 (CLI MVP - Video Generation Feedback Loops)** [Not Started] - Provides rapid-iteration CLI tools for video prompt enhancement and video generation with automatic VBench quality scoring. Includes: video prompt feedback loop using two-agent approach + VideoDirectorGPT (9.1), video generation with VBench scoring (9.2), integrated complete workflow orchestrator (9.3), and enhanced reference image generation with prompt enhancement and quality scoring (9.4). Enables developers to rapidly iterate through entire pipeline: image prompt → image generation → video prompt → video generation.

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
