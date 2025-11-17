# Product Requirements Document (PRD)
## AI Video Ad Generator

---

## Document Information

| Field | Value |
|-------|-------|
| **Project Name** | AI Video Ad Generator |
| **Version** | 1.0 |
| **Date** | November 14, 2025 |
| **Author** | Development Team |
| **Status** | Active Development |

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Problem Statement](#problem-statement)
3. [Solution Overview](#solution-overview)
4. [Target Audience](#target-audience)
5. [Product Goals & Success Metrics](#product-goals--success-metrics)
6. [User Personas](#user-personas)
7. [User Stories](#user-stories)
8. [Functional Requirements](#functional-requirements)
9. [Non-Functional Requirements](#non-functional-requirements)
10. [Technical Architecture](#technical-architecture)
11. [AI Video Generation Pipeline](#ai-video-generation-pipeline)
12. [Ad Narrative Frameworks](#ad-narrative-frameworks)
13. [User Interface Design](#user-interface-design)
14. [API Specifications](#api-specifications)
15. [Data Models](#data-models)
16. [Security & Privacy](#security--privacy)
17. [Performance Requirements](#performance-requirements)
18. [Cost Structure](#cost-structure)
19. [Deployment Strategy](#deployment-strategy)
20. [Future Enhancements](#future-enhancements)
21. [Risks & Mitigations](#risks--mitigations)
22. [Appendices](#appendices)
23. [Hero-Frame Iteration Plan & Timeline](#hero-frame-iteration-plan--timeline)

---

## 1. Executive Summary

### 1.1 Product Vision

AI Video Ad Generator is a web application that enables users to create professional-quality video advertisements from simple text prompts. The system leverages advanced AI models and proven advertising frameworks to automatically generate coherent, persuasive video content suitable for social media platforms like Instagram, TikTok, and YouTube.

### 1.2 Key Features

- **Simple Text-to-Video Generation**: Users input a product description, and the system generates a complete video ad
- **AI-Powered Creative Direction**: LLM automatically determines brand guidelines, colors, style, and music
- **Framework-Based Storytelling**: Implements proven advertising frameworks (PAS, BAB, AIDA)
- **Professional Video Composition**: Multi-scene videos with transitions, text overlays, and background music
- **Video Editing Tools**: Timeline-based editor with trim, split, and merge capabilities for fine-tuning generated videos
- **Intelligent Quality Optimization**: Automatic video coherence enhancement and LLM-powered prompt optimization for best results
- **User Management**: Authentication system with video history and profile management
- **Cost-Effective**: Target cost under $2 per video generated

### 1.3 Technology Stack

- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS
- **Backend**: Python 3.11 + FastAPI + SQLAlchemy
- **Video Generation**: Replicate API (Runway Gen-3, Kling, Minimax)
- **LLM Enhancement**: GPT-4 or Claude for prompt enhancement
- **Video Processing**: MoviePy + OpenCV + Pillow
- **Database**: SQLite (development) / PostgreSQL (production)
- **Deployment**: AWS EC2 + Nginx
- **Authentication**: JWT-based authentication

---

## 2. Problem Statement

### 2.1 Current Challenges

**For Small Businesses & Creators:**
- Creating video ads is expensive (requires videographers, editors, designers)
- Traditional production takes days or weeks
- Requires specialized skills in video editing and advertising
- Difficult to create multiple variations for A/B testing
- Stock footage and templates lack brand consistency

**For Marketing Teams:**
- Need to produce hundreds of ad variations at scale
- Lack resources for rapid iteration and testing
- Time-consuming creative review and revision cycles
- Inconsistent brand messaging across campaigns

### 2.2 Market Opportunity

- Global digital advertising spend: $600+ billion annually
- Video advertising growing 20%+ year-over-year
- Social media platforms prioritizing video content
- AI-generated content market expanding rapidly
- Demand for personalized, targeted ad creative

---

## 3. Solution Overview

### 3.1 Core Value Proposition

**"Create professional video ads in minutes, not days—just describe what you want."**

Our solution transforms a simple text prompt into a publication-ready video advertisement by:

1. **Intelligent Analysis**: LLM analyzes the product and determines optimal creative direction
2. **Framework Selection**: Automatically selects proven advertising framework (PAS, BAB, or AIDA)
3. **Scene Planning**: Breaks video into coherent scenes with narrative arc
4. **Video Generation**: Creates actual video clips using state-of-the-art AI models
5. **Professional Composition**: Adds text overlays, transitions, music, and color grading
6. **Instant Delivery**: Delivers final video in 2-3 minutes, ready for download

### 3.2 Competitive Advantages

- **Zero Creative Input Required**: Users don't need to specify colors, style, music, or framework
- **Framework-Based Storytelling**: Applies proven advertising psychology (not random scenes)
- **Video Clips, Not Static Images**: Real motion footage with cinematic quality
- **Cost-Effective**: Up to $200 per video vs. $500-5000 for traditional production (quality-focused pricing)
- **Fast Generation**: 2-3 minutes vs. days/weeks for manual creation
- **Consistent Quality**: Every output follows best practices for advertising

---

## 4. Target Audience

### 4.1 Primary Users

**Small Business Owners**
- Need: Affordable video ads for social media marketing
- Pain Point: Can't afford professional video production
- Budget: $0-500/month for marketing content
- Technical Skill: Low to moderate

**Digital Marketers**
- Need: Rapid creation of ad variations for testing
- Pain Point: Slow creative production bottlenecks campaigns
- Budget: $1000-10,000/month for creative assets
- Technical Skill: Moderate to high

**Content Creators / Influencers**
- Need: Professional-looking sponsored content
- Pain Point: Time-consuming editing process
- Budget: $100-1000/month
- Technical Skill: Moderate

### 4.2 Secondary Users

**Marketing Agencies**
- Need: Scalable ad production for multiple clients
- Use Case: Generate initial concepts for client review
- Budget: $5000+/month

**E-commerce Sellers**
- Need: Product showcase videos at scale
- Use Case: Create videos for hundreds of SKUs
- Budget: $500-2000/month

---

## 5. Product Goals & Success Metrics

### 5.1 Primary Goals

1. **Deliver High-Quality Video Ads**: Professional-grade output suitable for paid advertising
2. **Minimize User Effort**: Single text prompt input with zero configuration required
3. **Fast Generation**: Complete video in under 5 minutes
4. **Cost Efficiency**: Under $200 per video for system costs (quality is priority)
5. **User Satisfaction**: 80%+ of videos require no regeneration

### 5.2 Success Metrics (KPIs)

**Technical Performance:**
- Video generation success rate: >90%
- Average generation time: <3 minutes
- Cost per video: <$200.00 (quality-focused, cost is not a constraint)
- System uptime: >99%

**User Engagement:**
- Daily active users: 100+ (Month 1)
- Videos generated per user: 3+ per month
- User retention (30-day): >40%
- Video download rate: >80%

**Quality Metrics:**
- Video completion rate: >80% (users watch entire video)
- Regeneration rate: <20% (most videos accepted first try)
- User satisfaction score: 4+/5

---

## 6. User Personas

### Persona 1: Sarah - Small Business Owner

**Demographics:**
- Age: 34
- Location: Austin, Texas
- Business: Boutique skincare brand
- Revenue: $200K/year

**Goals:**
- Create Instagram Reels and TikTok ads
- Increase brand awareness
- Drive online sales

**Frustrations:**
- Can't afford $2000/video from agencies
- Doesn't have video editing skills
- Needs content weekly but lacks time

**How Our Product Helps:**
- Generates luxury skincare ads in minutes
- Automatically matches brand aesthetic
- Costs <$5 per ad instead of $2000

### Persona 2: Marcus - Performance Marketer

**Demographics:**
- Age: 28
- Location: San Francisco
- Role: Growth Marketing Manager at tech startup
- Team Size: 5 people

**Goals:**
- Test 20+ ad variations per week
- Optimize ad creative for conversions
- Reduce production costs

**Frustrations:**
- Creative team bottleneck (5-day turnaround)
- Hard to test different messaging quickly
- Budget constraints for creative production

**How Our Product Helps:**
- Generate variations instantly
- Test different frameworks (PAS vs. AIDA)
- A/B test at scale

---

## 7. User Stories

### 7.1 Core User Stories

**As a user, I want to...**

1. **Generate Video from Prompt**
   - Input: "Create a luxury watch ad"
   - Output: 15-second vertical video with brand colors, music, and CTA
   - Acceptance: Video generated in <3 minutes, professional quality

2. **View My Video History**
   - Action: Click "Gallery" to see all my videos
   - Output: Grid of video thumbnails with metadata
   - Acceptance: Videos load in <2 seconds, sorted by date

3. **Download Generated Video**
   - Action: Click "Download" button on completed video
   - Output: MP4 file downloaded to device
   - Acceptance: Video plays correctly on mobile and desktop

4. **Track Generation Progress**
   - Action: Submit video generation request
   - Output: Real-time progress bar with status updates
   - Acceptance: Progress updates every 2 seconds

5. **Create Account & Login**
   - Action: Register with username and password
   - Output: Authenticated session with JWT token
   - Acceptance: Can access protected pages after login

### 7.2 Advanced User Stories

6. **Regenerate Failed Videos**
   - Action: Click "Retry" on failed generation
   - Output: New generation attempt with same prompt
   - Acceptance: New video starts generating

7. **View Cost and Stats**
   - Action: Navigate to profile page
   - Output: Total videos generated, total cost spent
   - Acceptance: Accurate cost calculation displayed

8. **Delete Unwanted Videos**
   - Action: Click "Delete" with confirmation
   - Output: Video removed from gallery and storage
   - Acceptance: Video no longer accessible

### 7.3 Video Editing User Stories

9. **Edit Generated Video with Timeline**
   - Action: Open video in editor mode
   - Output: Timeline interface showing all video clips with visual representation
   - Acceptance: Timeline displays all clips, durations, and allows navigation

10. **Trim Video Clips**
   - Action: Select clip on timeline and adjust start/end points
   - Output: Clip trimmed to selected duration
   - Acceptance: Trimmed clip updates in timeline, preview shows changes

11. **Split Video Clips**
   - Action: Click split point on timeline within a clip
   - Output: Single clip divided into two separate clips
   - Acceptance: Two clips appear on timeline, can be edited independently

12. **Merge Video Clips**
   - Action: Select multiple adjacent clips and merge
   - Output: Multiple clips combined into single clip
   - Acceptance: Merged clip appears as one segment on timeline

### 7.4 Video Quality Optimization User Stories

13. **Optimize Video Coherence Between Clips**
   - Action: System automatically analyzes and improves visual consistency
   - Output: Enhanced transitions and visual flow between clips
   - Acceptance: Final video shows smooth, coherent visual narrative across all clips

14. **AI-Powered Prompt Optimization**
   - Action: User provides initial prompt, LLM analyzes and enhances it
   - Output: Optimized prompt that generates higher quality video
   - Acceptance: Enhanced prompt produces better visual results than original

---

## 8. Functional Requirements

### 8.1 User Authentication

**FR-001: User Registration**
- System shall allow users to create accounts with username and password
- Username must be unique (3-50 characters)
- Password must be hashed using bcrypt
- Optional email field (no password recovery flow in MVP)

**FR-002: User Login**
- System shall authenticate users via username/password
- System shall generate JWT token on successful login
- Token shall expire after 7 days
- Failed login attempts shall show clear error messages

**FR-003: Protected Routes**
- System shall restrict access to authenticated users only
- Unauthenticated users shall be redirected to login page
- JWT token shall be verified on every protected endpoint

**FR-004: User Logout**
- System shall clear JWT token from client storage
- User shall be redirected to login page after logout

### 8.2 Video Generation

**FR-005: Simple Prompt Input**
- System shall accept text prompt (10-500 characters)
- No additional user configuration required
- System shall validate prompt before processing

**FR-006: LLM Enhancement**
- System shall send prompt to LLM (GPT-4/Claude)
- LLM shall generate complete ad specification JSON including:
  - Product description
  - Brand guidelines (colors, style, mood)
  - Ad framework (PAS, BAB, or AIDA)
  - Scene breakdown with visual prompts
  - Music style selection
  - Call-to-action text
- System shall validate LLM output against schema

**FR-007: Framework Selection**
- System shall automatically select best advertising framework:
  - **PAS**: For problem-solving products
  - **BAB**: For aspirational/transformational products
  - **AIDA**: For general direct-response ads
- Framework determines scene structure and narrative arc

**FR-008: Scene Planning**
- System shall break video into 3-5 scenes based on framework
- Each scene shall have:
  - Duration (3-7 seconds)
  - Visual prompt for video generation
  - Text overlay content and positioning
  - Transition type
- Total duration shall match target (15s, 30s, or 60s)

**FR-009: Video Clip Generation**
- System shall generate video clips using Replicate API
- Support for multiple models: Runway Gen-3, Kling, Minimax
- Each clip generated from enriched visual prompt
- Aspect ratio: 9:16 (vertical), 16:9 (horizontal), or 1:1 (square)
- Duration: 3-7 seconds per clip

**FR-010: Text Overlay Addition**
- System shall add text overlays to video clips
- Text content based on scene type (brand name, features, CTA)
- Text styling based on brand colors and fonts
- Text animations: fade in, slide up, scale
- Text positioning: top, center, or bottom

**FR-011: Video Stitching**
- System shall concatenate all scene clips
- Apply smooth transitions between clips (crossfade)
- Add fade in at start and fade out at end
- Maintain consistent frame rate (24-30 fps)

**FR-012: Audio Layer**
- System shall select background music based on style keywords
- Music library categorized by mood (luxury, tech, eco, energetic)
- System shall add sound effects at scene transitions
- Audio volume: 30% for music, 50% for SFX
- Audio shall be synchronized with video duration

**FR-013: Post-Processing**
- System shall apply color grading based on brand style
- Optional: vignette effect, film grain, contrast adjustment
- Final video resolution: 1080p minimum
- Output format: MP4 (H.264 video, AAC audio)

**FR-014: Progress Tracking**
- System shall update database with current status and progress %
- Status values: pending, processing, completed, failed
- Progress steps:
  - 10%: LLM enhancement
  - 20%: Scene planning
  - 30-70%: Video generation (per scene)
  - 80%: Video stitching
  - 90%: Audio layer
  - 100%: Complete

**FR-015: Cost Calculation**
- System shall track total cost per generation
- System shall store the final per-generation cost in the database
- System shall update user's `total_cost` field on generation completion

**FR-016: Cancel Generation (Best-Effort)**
- System shall allow users to request cancellation of an in-progress generation from the UI
- System shall make a best-effort attempt to stop further processing for that generation
- If cancellation succeeds before completion, the generation status shall be updated to `failed` with an appropriate `error_message` (e.g., "Cancelled by user")
- If cancellation is requested too late (generation already completed), the existing completed video shall remain available and billable

### 8.3 Video Management

**FR-017: Video Gallery**
- System shall display all user's generated videos
- Grid layout with video thumbnails
- Display metadata: prompt, date, duration, status, cost
- Sort by creation date (newest first)
- Click thumbnail to view video detail

**FR-018: Video Playback**
- System shall serve video files from storage
- HTML5 video player with controls
- Autoplay on video detail page
- Support for different aspect ratios

**FR-019: Video Download**
- System shall allow users to download MP4 files
- File naming: `ad_{generation_id}.mp4`
- Download button on video detail page

**FR-020: Video Deletion**
- System shall allow users to delete their videos
- Confirmation dialog before deletion
- Remove video file from storage and database record
- Only video owner can delete

**FR-021: Video Search**
- System shall filter videos by prompt text (optional feature)
- System shall filter by status (completed, failed, processing)

### 8.4 Video Editing

**FR-024: Video Editor Access**
- System shall provide an editor interface accessible from completed video detail page and/or from any saved gallery item.
- Editor shall load the underlying project with all individual scene clips available for editing (not just a flattened final video file).
- Editor shall maintain original source media as backup for restoration and re-generation workflows.

**FR-025: Timeline Interface**
- System shall display a timeline showing all video clips in sequence
- Timeline shall show visual thumbnails for each clip
- Timeline shall display clip durations and allow scrubbing/playback
- Timeline shall support zoom in/out for precise editing
- Timeline shall show current playback position indicator

**FR-026: Clip Trimming**
- System shall allow users to select any clip on the timeline
- System shall provide trim handles (start and end points) for selected clip
- System shall allow users to adjust trim points by dragging or entering time values
- System shall provide real-time preview of trimmed clip
- System shall validate that trim points are within clip boundaries
- System shall update timeline immediately after trim operation

**FR-027: Clip Splitting**
- System shall allow users to place a split point at any position within a clip
- System shall divide the clip into two separate clips at the split point
- System shall maintain both resulting clips in the timeline sequence
- System shall preserve all metadata (text overlays, transitions) for both clips
- System shall allow independent editing of split clips

**FR-028: Clip Merging**
- System shall allow users to select multiple adjacent clips
- System shall merge selected clips into a single continuous clip
- System shall preserve video content and maintain frame rate consistency
- System shall apply appropriate transitions between merged segments
- System shall update timeline to show merged clip as single entity

**FR-029: Editor Save and Export**
- System shall allow users to save editing changes without exporting.
- System shall treat each manual save as a **versioned editor state** that can be reopened later from the gallery with full timeline and clip data intact.
- System shall create a new video version when exporting from any saved editor state, without overwriting previous exports.
- System shall preserve original generated media and prior versions for comparison.
- System shall track editing history for undo/redo functionality within a given editor session.
- System shall export edited video in the same format and quality as the underlying source clips.

**FR-036 (New): Clip-Level Regeneration and Gap Filling**
- System shall support **clip-level** AI regeneration rather than only regenerating entire final videos.
- Given a timeline where the user trims or deletes part of a clip, the system shall allow the user to request generation of a **new clip** to fill the resulting gap:
  - The new clip shall match the gap’s duration and aspect ratio.
  - The user may provide a local prompt (or reuse scene-level/hero-frame prompts) to describe the replacement content.
  - The system shall reuse applicable coherence settings (e.g., seed control, IP-Adapter) so the new clip fits visually with neighboring clips.
- System shall track regenerated clips as distinct assets linked to the editor state and generation history, not as a brand new standalone video.

### 8.5 Video Quality Optimization

**Epic 7 Implementation:** This section is implemented by Epic 7 (Multi-Scene Coherence & Quality Optimization), which provides state-of-the-art generation-time consistency techniques and automated quality control. See `docs/epics.md` for detailed story breakdown.

**Key Techniques:**
- **Seed Control & Latent Reuse:** Shared random seeds and latent state reuse across scenes for visual coherence
- **IP-Adapter:** Identity preservation for characters and products using reference images
- **LoRA Training:** Custom model fine-tuning for recurring brand characters/products
- **VideoDirectorGPT-Style Planning:** Enhanced LLM planning with consistency groupings and shot lists
- **VBench Quality Metrics:** Automated quality assessment with temporal, aesthetic, and prompt alignment scores
- **CSFD Character Consistency:** Cross-Scene Face Distance scoring for character-driven ads
- **ControlNet:** Compositional consistency via depth maps and layout control
- **Enhanced Post-Processing:** Brand-aware color grading and transition optimization

**FR-030: Video Coherence Analysis**
- System shall automatically analyze visual consistency across all clips in a video
- System shall detect visual inconsistencies (color, lighting, style, motion)
- System shall identify optimal transition points between clips
- System shall assess narrative flow and visual continuity
- **Implementation:** Epic 7, Stories 7.5 (VBench Integration), 7.7 (CSFD Detection), 7.6 (Post-Processing)

**FR-031: Coherence Enhancement**
- System shall automatically apply color grading adjustments to improve consistency
- System shall optimize transitions between clips for smoother visual flow
- System shall adjust lighting and contrast to create cohesive visual narrative
- System shall maintain brand guidelines while improving coherence
- System shall apply enhancements during video stitching phase
- **Implementation:** Epic 7, Stories 7.1 (Seed Control), 7.3 (IP-Adapter), 7.4 (LoRA), 7.6 (Post-Processing), 7.8 (ControlNet)

**FR-032: Prompt Optimization via LLM**
- System shall accept user's initial prompt as input
- System shall send prompt to LLM (GPT-4/Claude) for analysis and enhancement
- LLM shall analyze prompt for clarity, specificity, and visual generation potential
- LLM shall generate optimized prompt that:
  - Includes relevant visual style keywords
  - Specifies composition and framing details
  - Adds brand-appropriate descriptive elements
  - Enhances product feature descriptions
  - Improves scene-by-scene visual prompts
- System shall present optimized prompt to user with explanation of improvements
- System shall allow user to accept, modify, or reject optimized prompt
- **Implementation:** Epic 7, Stories 7.2 (Enhanced Planning), 7.9 (Feedback Loop)

**FR-033: Quality Feedback Loop**
- System shall track video quality metrics (coherence score, visual consistency)
- System shall learn from user preferences and regeneration patterns
- System shall improve prompt optimization based on successful video outcomes
- System shall refine coherence enhancement algorithms based on user feedback
- **Implementation:** Epic 7, Story 7.9 (Quality Feedback Loop)

### 8.6 User Profile

**FR-034: Profile Display**
- System shall show user statistics:
  - Total videos generated
  - Total cost spent
  - Account creation date
  - Last login timestamp
- Display username and email (if provided)

**FR-035: User Stats Update**
- System shall increment total_generations on video completion
- System shall add generation cost to total_cost
- System shall update last_login on each login

### 8.7 Hero-Frame & Iterative Refinement Workflow

The system shall support a professional, hero-frame-first workflow that mirrors how expert creators work in practice: starting from a single high-quality still frame, evolving into motion, and iterating with both automated and human-in-the-loop feedback.

**FR-036: Hero Frame Generation (Text → Photo)**
- System shall provide a dedicated hero-frame generation flow separate from full video generation.
- System shall accept a cinematography-focused text prompt (subject, lighting, mood, lens, composition, film stock, aspect ratio).
- System shall call a text-to-image model (e.g., Stable Diffusion / SDXL on Replicate) and generate **4–8 hero frame candidates** per request.
- System shall expose a gallery UI where the user can:
  - View all hero frame candidates in a grid
  - Zoom into a candidate
  - Mark one hero frame as the **primary hero frame** for downstream video generation
- System shall store generated hero frames with metadata (prompt, model, seed, aspect ratio) linked to the user and generation request.

**FR-037: Cinematographer-Level Prompt Enhancement for Images**
- System shall offer an optional LLM-powered “cinematographer enhancement” step for hero-frame prompts.
- System shall accept a basic user prompt and return an enriched prompt that includes:
  - Camera body and lens details
  - Lighting direction and quality
  - Composition notes (framing, depth, rule of thirds)
  - Film stock/color science references
  - Mood and atmosphere descriptors
  - Aspect ratio and stylization hints
- System shall display the enhanced prompt side-by-side with the original, with a clear explanation of what was improved.
- System shall allow the user to accept as-is, edit, or revert to the original prompt before generating hero frames.

**FR-038: Hero Frame Iteration & Selection**
- System shall allow the user to:
  - Regenerate hero frames with the same prompt (slot-machine style iteration)
  - Slightly mutate prompts (e.g., adjust lighting, composition, mood) and regenerate
  - Save multiple “favorite” hero frames for later experiments
- System shall clearly indicate which hero frame is currently selected as the canonical anchor for video generation.
- System shall track the iteration history for hero frame generation (prompt variants, model settings, seeds) for analytics and debugging.

**FR-039: Image-to-Video Generation (Photo → Video) from Hero Frame**
- System shall support an image-to-video flow that takes a selected hero frame as the primary visual input.
- System shall call one or more image-to-video models (e.g., Kling, Wan, PixVerse, or equivalent) via a backend service.
- System shall accept a **motion prompt** describing camera movement and temporal behavior, including:
  - Camera movement (dolly, push-in, handheld, static)
  - Frame rate and playback speed (slow motion vs. real-time)
  - Motion intensity and direction
- System shall support **negative prompts** to suppress undesirable artifacts (e.g., “fast movements”, “disfigurements”, “low quality”, “dust particles”, “distortions”).
- System shall generate at least one video attempt from the hero frame with the provided motion + negative prompts.

**FR-040: Automated Multi-Attempt Generation with VBench-Based Selection**
- System shall support an **automated 3-attempt mode** for image-to-video generation:
  - Given a hero frame and motion/negative prompts, the system **automatically generates 3 video attempts** without additional user input.
  - All 3 attempts shall be stored and linked to the same “generation group”.
- After generation completes, the system shall:
  - Run VBench (or equivalent) quality evaluation on each attempt.
  - Compute per-attempt scores (e.g., temporal consistency, aesthetics, prompt alignment) and an overall quality score.
  - Automatically select the **highest-scoring attempt** as the “system-selected best” and mark it explicitly in the UI.
- System shall expose an API and UI to retrieve:
  - All attempts for a given generation group
  - VBench metrics per attempt
  - Which attempt was auto-selected as best and why (score breakdown).

**FR-041: Iteration Workspace & Human-in-the-Loop Refinement**
- System shall provide a dedicated **Iteration Workspace** UI for refining video attempts that includes:
  - Side-by-side comparison of the 3 auto-generated attempts
  - Visual indication of the VBench score for each attempt
  - Ability to play videos in sync for direct comparison
- System shall allow users to:
  - Manually override the auto-selected best attempt (choose a different “winner”)
  - Trigger manual regenerations with updated motion and/or negative prompts
  - Edit the hero-frame or motion prompts using an inline editor.
- System shall offer LLM-powered **prompt improvement suggestions** based on:
  - VBench feedback (e.g., low temporal consistency → suggest stronger motion constraints)
  - User feedback (e.g., “too chaotic”, “not cinematic enough”)
- System shall log each manual regeneration as a new attempt in the generation group, preserving full history.

**FR-042: Iterative Refinement Workflow & Versioning**
- System shall treat each cycle of “prompt update → new attempts → evaluation → selection” as a **refinement iteration**.
- System shall maintain a **generation history timeline** that shows:
  - Iteration number
  - Chosen attempt for that iteration
  - Key prompt changes
  - VBench score trends over time
- System shall support version comparison:
  - Compare any two selected versions side-by-side (player + metrics)
  - Clearly label which version is the current “final” version.
- System shall maintain a `final_version` pointer for each ad that is used for export, download, and reporting.

**FR-043: Quality Dashboard & Benchmarks**
- System shall provide a **Quality Dashboard** that summarizes:
  - VBench score distribution across attempts and final videos
  - Average number of iterations per final video
  - Auto-selected vs. user-selected “best” agreement rate
- For each video, the dashboard shall visualize:
  - Per-attempt VBench scores (bar/line chart)
  - How quality changed across iterations (trend line)
  - Which iteration produced the final accepted version.
- System shall allow filtering and aggregation by:
  - Date range
  - Campaign or tag (future)
  - Model used (Kling/Wan/PixVerse/etc.)

**FR-044: Integration with Existing Pipeline & Epics**
- The hero-frame and iterative refinement workflow shall **build on** existing epics rather than replacing them:
  - Reuse the existing generation pipeline (LLM enhancement → scene planning → video generation → stitching → audio) when generating from hero frames.
  - Reuse Epic 7 capabilities (seed control, VBench, enhanced planning) to power automated quality scoring and consistency.
  - Reuse Epic 6 editing tools (timeline, trim/split/merge, editor export) as post-generation refinement options on top of the final selected version.
- No existing epics or PRD requirements shall be removed; this workflow is an additive, professional-mode layer on top of the current system.

---

## 9. Non-Functional Requirements

### 9.1 Performance

**NFR-001: Generation Speed**
- 15-second video: Generate in <3 minutes (target: 2 minutes)
- 30-second video: Generate in <6 minutes (target: 4 minutes)
- 60-second video: Generate in <12 minutes (target: 8 minutes)

**NFR-002: API Response Time**
- Login/Register: <500ms
- Video status check: <200ms
- Gallery load: <1 second for 20 videos

**NFR-003: Concurrent Users (Post-MVP)**
- Post-MVP goal: Support 10 concurrent video generations
- Post-MVP goal: Queue additional requests if limit exceeded
- Post-MVP goal: Graceful degradation under high load

### 9.2 Reliability

**NFR-004: Success Rate**
- Video generation success rate: >90%
- Automatic retry for transient failures (up to 3 attempts)
- Clear error messages for permanent failures

**NFR-005: System Uptime**
- Target: 99% uptime (excluding maintenance)
- Automated health checks every 5 minutes
- Alerting on service failures

**NFR-006: Data Persistence**
- All user data backed up daily
- Video files retained for 30 days minimum
- Database transactions for data integrity

### 9.3 Scalability

**NFR-007: User Growth**
- Support 1000+ registered users (Month 1)
- Support 10,000+ registered users (Month 6)
- Horizontal scaling capability via multiple EC2 instances

**NFR-008: Storage Management**
- Automatic cleanup of temp files after generation
- Video storage: 50GB initial capacity
- Expandable S3 storage for production

### 9.4 Security

**NFR-009: Authentication Security**
- Passwords hashed with bcrypt (cost factor: 12)
- JWT tokens signed with secret key
- Token expiration enforced (7 days)
- HTTPS for all API communication (production)

**NFR-010: Data Privacy**
- Users can only access their own videos
- API endpoints validate user authorization
- No sharing of user data with third parties

**NFR-011: Input Validation**
- Sanitize all user inputs to prevent injection attacks
- Rate limiting: 10 generations per user per hour
- File upload limits: 100MB for brand assets (future feature)

### 9.5 Usability

**NFR-012: User Interface**
- Clean, minimal design (Google-style)
- Mobile-responsive (works on phones, tablets, desktop)
- Intuitive navigation (max 3 clicks to any feature)

**NFR-013: Error Messages & Basic Error Handling**
- User-friendly error messages (no technical jargon)
- Actionable suggestions (e.g., "Retry" button)
- Error logging for debugging
- All API error responses shall use a simple JSON structure:

```json
{
  "error": {
    "code": "SIMPLE_ERROR_CODE",
    "message": "Human readable description of the error"
  }
}
```

**NFR-014: Accessibility**
- Keyboard navigation support
- Screen reader compatibility
- Sufficient color contrast ratios

### 9.6 Maintainability

**NFR-015: Code Quality**
- Type-safe code (TypeScript for frontend, type hints for Python)
- Modular architecture (services, components, utilities)
- Comprehensive error handling

**NFR-016: Documentation**
- README with setup instructions
- API documentation with examples
- Architecture diagram
- Deployment guide

**NFR-017: Logging**
- Structured logging at all critical points
- Log levels: DEBUG, INFO, WARNING, ERROR
- Log retention: 30 days

---

## 10. Technical Architecture

### 10.1 MVP vs Post-MVP Scope

To keep implementation focused, all capabilities in this PRD are categorized into two scopes:

1. **MVP Scope**
   - User registration, login, logout, and basic JWT-based authentication
   - Simple prompt-to-video generation pipeline (LLM enhancement → scene planning → video generation → stitching → audio → export)
   - Minimum video output quality of **1080p**
   - Basic progress tracking (status + progress %) for each generation
   - Video gallery with list, playback, download, and delete
   - Per-generation cost tracking and aggregate `total_cost` per user
   - Basic error handling with simple JSON error responses (see API section)
   - Best-effort **Cancel Generation** behavior from the UI for in-progress jobs
   - Single-instance deployment (one backend + one frontend on a single EC2)

2. **Post-MVP Scope**
   - True concurrent video generation guarantees and request queuing
   - Advanced analytics and engagement dashboards
   - Collaboration features (teams, comments, approvals)
   - Video editing tools (timeline interface, trim, split, merge clips)
   - Video coherence optimization (automatic visual consistency enhancement)
   - LLM-powered prompt optimization (enhance user prompts for better video quality)
   - Advanced video editing tools (scene regeneration, text edits, music changes)
   - Brand asset uploads, logos, and custom fonts
   - Subscription plans, billing, and payment integrations
   - Large-scale horizontal scaling and multi-instance deployments

Unless otherwise noted, requirements elsewhere in this document are **assumed MVP**. Items explicitly marked “Post-MVP” are not required for the MVP launch.

### 10.2 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         USERS                                │
│                    (Web Browsers)                            │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    AWS EC2 Instance                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Nginx Web Server                         │  │
│  │  - Serves React static files                         │  │
│  │  - Reverse proxy /api/* to FastAPI                   │  │
│  │  - Serves /output/* video files                      │  │
│  └─────────────────┬────────────────────────────────────┘  │
│                    │                                         │
│  ┌─────────────────▼────────────────────────────────────┐  │
│  │            FastAPI Backend (Uvicorn)                  │  │
│  │  - API endpoints                                      │  │
│  │  - JWT authentication                                 │  │
│  │  - Business logic orchestration                       │  │
│  └─────────────────┬────────────────────────────────────┘  │
│                    │                                         │
│  ┌─────────────────▼────────────────────────────────────┐  │
│  │         Video Generation Pipeline                     │  │
│  │  ┌──────────────────────────────────────────────┐    │  │
│  │  │ 1. LLM Enhancement (GPT-4)                   │    │  │
│  │  │    - Prompt → Structured JSON                │    │  │
│  │  └──────────────────┬───────────────────────────┘    │  │
│  │                     ▼                                 │  │
│  │  ┌──────────────────────────────────────────────┐    │  │
│  │  │ 2. Scene Planning                            │    │  │
│  │  │    - Framework selection                     │    │  │
│  │  │    - Scene breakdown                         │    │  │
│  │  └──────────────────┬───────────────────────────┘    │  │
│  │                     ▼                                 │  │
│  │  ┌──────────────────────────────────────────────┐    │  │
│  │  │ 3. Video Clip Generation (Replicate)        │    │  │
│  │  │    - Generate clips per scene                │    │  │
│  │  └──────────────────┬───────────────────────────┘    │  │
│  │                     ▼                                 │  │
│  │  ┌──────────────────────────────────────────────┐    │  │
│  │  │ 4. Video Processing (MoviePy)                │    │  │
│  │  │    - Text overlays                           │    │  │
│  │  │    - Transitions                             │    │  │
│  │  │    - Audio layer                             │    │  │
│  │  │    - Post-processing                         │    │  │
│  │  └──────────────────┬───────────────────────────┘    │  │
│  │                     ▼                                 │  │
│  │  ┌──────────────────────────────────────────────┐    │  │
│  │  │ 5. Final Export & Storage                    │    │  │
│  │  │    - Save to /output/videos/                 │    │  │
│  │  │    - Update database                         │    │  │
│  │  └──────────────────────────────────────────────┘    │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            SQLite Database (Local)                    │  │
│  │  - users table                                        │  │
│  │  - generations table                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         File Storage (Local Disk)                     │  │
│  │  /output/videos/       - Final videos                │  │
│  │  /output/temp/         - Processing files            │  │
│  │  /output/thumbnails/   - Video thumbnails            │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   External Services                          │
│  - Replicate API (Video generation)                         │
│  - OpenAI API (LLM enhancement)                             │
└─────────────────────────────────────────────────────────────┘
```

### 10.3 Technology Stack Details

**Frontend:**
- React 18.2+ (UI library)
- TypeScript 5.0+ (Type safety)
- Vite 5.0+ (Build tool, fast dev server)
- Tailwind CSS 3.3+ (Utility-first CSS)
- Zustand 4.4+ (State management)
- Axios 1.6+ (HTTP client)
- React Router 6+ (Routing)

**Backend:**
- Python 3.11+
- FastAPI 0.104+ (Web framework)
- Uvicorn (ASGI server)
- SQLAlchemy 2.0+ (ORM)
- Pydantic (Data validation)
- Passlib + Bcrypt (Password hashing)
- PyJWT (JWT tokens)
- Python-multipart (File uploads)

**Video Generation:**
- Replicate Python SDK 0.22+ (API client)
- MoviePy 1.0+ (Video editing)
- OpenCV 4.8+ (Image processing)
- Pillow 10.1+ (Image manipulation)
- FFmpeg (Video encoding)
- Pydub (Audio processing)

**AI Services:**
- OpenAI API (GPT-4 for LLM enhancement)
- Replicate Models:
  - Runway Gen-3 Alpha Turbo (video generation)
  - Kling 1.5 (alternative video model)
  - Minimax Video-01 (fast, cost-effective)

**Database:**
- SQLite 3 (Local Development)
- PostgreSQL 14+ via AWS RDS (Production - primary)

**Deployment:**
- AWS EC2 (t3.large or t3.xlarge)
- Nginx (Web server, reverse proxy)
- Systemd (Process management)
- Ubuntu 22.04 LTS

---

## 11. AI Video Generation Pipeline

### 11.1 Pipeline Overview

The video generation pipeline transforms a simple user prompt into a professional video ad through seven distinct stages:

```
Simple Prompt → LLM Enhancement → Scene Planning → Video Generation → 
Text Overlays → Video Stitching → Audio Layer → Final Export
```

### 11.2 Stage 1: LLM Enhancement

**Input:** User prompt (e.g., "Create a luxury watch ad")

**Process:**
1. Send prompt to GPT-4 with system instructions
2. LLM analyzes product type and target audience
3. LLM selects best advertising framework (PAS, BAB, or AIDA)
4. LLM generates complete specification JSON

**Output:** Structured JSON containing:
- Product description (expanded)
- Brand guidelines (colors, style keywords, mood)
- Ad specifications (duration, aspect ratio, CTA)
- Framework selection with rationale
- Music style selection

**Example Output:**
```json
{
  "product_description": "Premium luxury smartwatch for professionals...",
  "brand_guidelines": {
    "brand_name": "Chronos Elite",
    "brand_colors": ["#0A192F", "#D4AF37", "#FFFFFF"],
    "visual_style_keywords": "elegant, sophisticated, luxury, minimalist",
    "mood": "aspirational, confident, premium"
  },
  "ad_specifications": {
    "ad_duration_seconds": 15,
    "aspect_ratio": "9:16",
    "framework": "BAB",
    "call_to_action_text": "Elevate Your Time",
    "music_style": "elegant_orchestral_minimal"
  }
}
```

### 11.3 Stage 2: Scene Planning

**Input:** LLM-generated JSON specification

**Process:**
1. Select framework-specific scene structure
2. Break video into 3-5 scenes based on framework
3. Generate enriched visual prompts for each scene
4. Plan text overlays and positioning
5. Determine scene durations and transitions

**Framework-Specific Planning:**

**BAB (Before-After-Bridge):**
- Scene 1 (5s): Before - Current/ordinary state
- Scene 2 (5s): After - Aspirational/transformed state
- Scene 3 (5s): Bridge - Product as solution + CTA

**PAS (Problem-Agitate-Solve):**
- Scene 1 (4s): Problem - Show frustration
- Scene 2 (3s): Agitate - Intensify pain
- Scene 3 (4s): Solve - Introduce product
- Scene 4 (4s): Resolution - Happy result

**AIDA (Attention-Interest-Desire-Action):**
- Scene 1 (3s): Attention - Hook/surprise
- Scene 2 (4s): Interest - Explain product
- Scene 3 (5s): Desire - Show benefits
- Scene 4 (3s): Action - Clear CTA

**Output:** Scene-by-scene breakdown with:
- Visual prompts enriched with brand keywords
- Text overlay content and styling
- Duration and transition types

### 11.4 Stage 3: Video Clip Generation

**Input:** Visual prompts for each scene

**Process:**
1. For each scene, call Replicate API
2. Use model (Runway Gen-3, Kling, or Minimax)
3. Generate 3-7 second video clip
4. Download video file to temp storage
5. Validate video quality and duration

**API Call Example:**
```python
video_clip = replicate.run(
    "minimax/video-01",
    input={
        "prompt": "Luxury smartwatch on wrist in elegant setting...",
        "duration": 5,
        "aspect_ratio": "9:16",
        "motion_amount": "medium"
    }
)
```

**Output:** 3-5 video clip files (MP4 format)

### 11.5 Stage 4: Text Overlay Addition

**Input:** Video clips + text overlay specifications

**Process:**
1. Load video clip with MoviePy
2. Create text clip with brand fonts and colors
3. Position text (top, center, or bottom)
4. Add text animations (fade in, slide up)
5. Add text shadow for readability
6. Composite text onto video

**Output:** Video clips with text overlays

### 11.6 Stage 5: Video Stitching

**Input:** All scene clips with text overlays

**Process:**
1. Load all clips in sequence
2. Apply crossfade transitions between clips (0.5s)
3. Add fade in at start (0.3s)
4. Add fade out at end (0.3s)
5. Ensure consistent frame rate (24-30 fps)
6. Concatenate all clips

**Output:** Single combined video clip (no audio yet)

### 11.7 Stage 6: Audio Layer

**Input:** Combined video + music style specification

**Process:**
1. Select background music from library based on style
2. Trim music to video duration
3. Adjust music volume (30%)
4. Add sound effects at scene transitions
5. Composite audio (music + SFX)
6. Attach audio to video

**Output:** Video with synchronized audio

### 11.8 Stage 7: Final Export & Post-Processing

**Input:** Video with audio

**Process:**
1. Apply color grading (cinematic, luxury, vibrant)
2. Add optional effects (vignette, film grain)
3. Enhance sharpness and contrast
4. Export final video:
   - Codec: H.264 (libx264)
   - Resolution: 1080p
   - Frame rate: 24-30 fps
   - Audio: AAC
5. Generate thumbnail (first frame)
6. Upload to storage (/output/videos/)
7. Update database (video_url, status=completed)

**Output:** Final MP4 video file, ready for download

### 11.9 Content Planner JSON Specification (PAS, BAB, AIDA)

The `Content Planner` module shall output a structured JSON description of the ad, using one of three narrative frameworks: **PAS**, **BAB**, or **AIDA**. For MVP, implementing **AIDA** end-to-end is sufficient, with PAS and BAB as straightforward extensions.

At minimum, the JSON shall include a `scenes` array, where each scene contains:

- `scene_number`: Integer index in playback order
- `scene_type`: One of the framework-specific scene types
- `visual_prompt`: Natural language description for the video model
- `text_overlay`: Short on-screen text for that scene
- `duration`: Scene duration in seconds

**Example JSON template for PAS (Problem-Agitate-Solve):**

```json
{
  "scenes": [
    {
      "scene_number": 1,
      "scene_type": "Problem",
      "visual_prompt": "A person looking frustrated while trying to [perform a task related to the problem], shot in a dull, slightly desaturated color palette.",
      "text_overlay": "Tired of [the problem]?",
      "duration": 4
    },
    {
      "scene_number": 2,
      "scene_type": "Agitate",
      "visual_prompt": "Dynamic shot showing the negative consequence of the problem, like [a specific failure]. Use quick cuts and a slightly shaky camera effect.",
      "text_overlay": "It only gets worse.",
      "duration": 3
    },
    {
      "scene_number": 3,
      "scene_type": "Solve",
      "visual_prompt": "A magical, brightly lit reveal of [the product]. The product is shown in a heroic close-up, effortlessly fixing the problem from Scene 1.",
      "text_overlay": "There’s a better way.",
      "duration": 4
    },
    {
      "scene_number": 4,
      "scene_type": "Resolution",
      "visual_prompt": "The same person from Scene 1, now happy and successful, in a bright and vibrant environment. The product is displayed prominently.",
      "text_overlay": "[Your Brand Name]. Shop Now!",
      "duration": 4
    }
  ]
}
```

**Example JSON template for BAB (Before-After-Bridge):**

```json
{
  "scenes": [
    {
      "scene_number": 1,
      "scene_type": "Before",
      "visual_prompt": "A shot of a person in their current, average state, performing a task without the product. The scene is shot with flat, neutral lighting.",
      "text_overlay": "This is you now.",
      "duration": 5
    },
    {
      "scene_number": 2,
      "scene_type": "After",
      "visual_prompt": "A vibrant, exciting shot of the same person, now transformed and successful. The environment is beautiful and aspirational. Use slow-motion or epic camera angles.",
      "text_overlay": "Imagine this...",
      "duration": 5
    },
    {
      "scene_number": 3,
      "scene_type": "Bridge",
      "visual_prompt": "A clean, studio shot of [the product] against a simple background. Graphics animate to show its key feature. The final shot is the person from Scene 2 holding the product.",
      "text_overlay": "[Your Brand Name] is how. Get Started.",
      "duration": 5
    }
  ]
}
```

**Example JSON template for AIDA (Attention-Interest-Desire-Action):**

```json
{
  "scenes": [
    {
      "scene_number": 1,
      "scene_type": "Attention",
      "visual_prompt": "An unexpected and visually stunning opening shot, like [an unusual visual]. Fast cuts and high energy.",
      "text_overlay": "You’re doing [task] all wrong.",
      "duration": 3
    },
    {
      "scene_number": 2,
      "scene_type": "Interest",
      "visual_prompt": "A clean, clear introduction to [the product], showing what it is and the main problem it solves. Simple studio background.",
      "text_overlay": "Meet [Product Name].",
      "duration": 4
    },
    {
      "scene_number": 3,
      "scene_type": "Desire",
      "visual_prompt": "A montage of satisfying shots showing the product’s best benefits in action. Happy customers, glowing reviews, and benefit-driven text overlays.",
      "text_overlay": "Transform your [area of life].",
      "duration": 5
    },
    {
      "scene_number": 4,
      "scene_type": "Action",
      "visual_prompt": "A final, strong shot of the product with a clear offer. An animated arrow points to a button.",
      "text_overlay": "Limited Time Offer! Click to Buy!",
      "duration": 3
    }
  ]
}
```

For MVP, the system only needs to reliably support AIDA; PAS and BAB can be implemented as post-MVP enhancements while reusing the same schema.

---

## 12. Ad Narrative Frameworks

### 12.1 Framework Overview

The system implements three proven advertising frameworks that follow psychological principles to create persuasive narratives:

| Framework | Psychological Driver | Best Use Case | Scene Count |
|-----------|---------------------|---------------|-------------|
| PAS | Loss Aversion & Relief | Problem-solving products | 4 |
| BAB | Aspiration & Hope | Transformational products | 3 |
| AIDA | Curiosity & Urgency | Direct response ads | 4 |

### 12.2 PAS (Problem-Agitate-Solve)

**Structure:**
1. **Problem** (4s): Show relatable frustration
2. **Agitate** (3s): Intensify emotional stakes
3. **Solve** (4s): Introduce product as hero
4. **Resolution** (4s): Show happy result + CTA

**Example - Stain Remover:**
- Problem: Coffee spill on white shirt before meeting
- Agitate: Panic, no time to change, important client
- Solve: Product instantly removes stain
- Resolution: Confident presentation, smiling customer

**When to Use:** Products that solve clear pain points (cleaning, software bugs, pain relief)

### 12.3 BAB (Before-After-Bridge)

**Structure:**
1. **Before** (5s): Current state (mundane/uninspired)
2. **After** (5s): Aspirational state (transformed/elevated)
3. **Bridge** (5s): Product as the path + CTA

**Example - Fitness App:**
- Before: Person struggling with motivation, average fitness
- After: Energized, confident, achieving fitness goals
- Bridge: App logo, "Your personal AI trainer"

**When to Use:** Aspirational products (fitness, education, luxury goods, lifestyle)

### 12.4 AIDA (Attention-Interest-Desire-Action)

**Structure:**
1. **Attention** (3s): Hook - surprising/arresting visual
2. **Interest** (4s): Explain what product is
3. **Desire** (5s): Show benefits and social proof
4. **Action** (3s): Clear CTA with urgency

**Example - Smartwatch:**
- Attention: "You're tracking fitness wrong"
- Interest: "Meet the AI-powered smartwatch"
- Desire: "24/7 health insights, 7-day battery"
- Action: "Order now - 20% off today only"

**When to Use:** General-purpose direct response ads, e-commerce products

---

## 13. User Interface Design

### 13.1 Design Principles

**Simplicity First:**
- Google-style minimalism
- Single primary action per page
- Maximum 3 clicks to any feature
- No unnecessary form fields

**Visual Hierarchy:**
- Clear typographic scale
- Ample whitespace
- Focused attention on key actions
- Subtle animations for feedback

**Responsive Design:**
- Mobile-first approach
- Breakpoints: 640px (mobile), 1024px (tablet), 1280px (desktop)
- Touch-friendly button sizes (44px minimum)

### 13.2 Page Layouts

**Landing Page (Unauthenticated)**
```
┌─────────────────────────────────────────────────────┐
│  Ad Generator                      [Login] [Sign Up]│
│                                                      │
│              ┌────────────────────────────┐         │
│              │  Create AI-Powered Ads     │         │
│              │  in Seconds                │         │
│              │                            │         │
│              │    [Get Started →]         │         │
│              └────────────────────────────┘         │
└─────────────────────────────────────────────────────┘
```

**Dashboard (Main Page)**
```
┌─────────────────────────────────────────────────────┐
│  Ad Generator     Dashboard  Gallery    @username ▼ │
├─────────────────────────────────────────────────────┤
│                                                      │
│           Generate Your Video Ad                     │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │ Describe your ad...                            │ │
│  │ e.g., "Luxury watch ad with elegant gold..."  │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│              [Generate Video]                        │
│                                                      │
│  ──────────────────────────────────────────────────  │
│                                                      │
│  Your Recent Videos:                                 │
│  ┌──────┐ ┌──────┐ ┌──────┐                        │
│  │ 🎥   │ │ 🎥   │ │ 🎥   │                        │
│  │ 15s  │ │ 30s  │ │ 15s  │                        │
│  └──────┘ └──────┘ └──────┘                        │
└─────────────────────────────────────────────────────┘
```

**Generation in Progress**
```
┌─────────────────────────────────────────────────────┐
│              Generating Your Video...                │
│                                                      │
│  ████████████░░░░░░░░░░░░  60%                     │
│                                                      │
│  Current Step: Generating video clips               │
│  Estimated time: 1 minute remaining                 │
│                                                      │
│              [Cancel Generation]                     │
└─────────────────────────────────────────────────────┘
```

**Video Result**
```
┌─────────────────────────────────────────────────────┐
│  ✓ Video Generated Successfully!                    │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │                                             │    │
│  │           VIDEO PLAYER                      │    │
│  │           [▶ Play]                         │    │
│  │                                             │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
│  Duration: 15s | Cost: $0.87 | 2 min ago           │
│                                                      │
│  [Download] [Regenerate] [Share] [Delete]          │
└─────────────────────────────────────────────────────┘
```

**Gallery Page**
```
┌─────────────────────────────────────────────────────┐
│  Ad Generator     Dashboard  Gallery    @username ▼ │
├─────────────────────────────────────────────────────┤
│  Your Videos                    [Search...] [Filter]│
│                                                      │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐              │
│  │ 🎥   │ │ 🎥   │ │ 🎥   │ │ 🎥   │              │
│  │ 15s  │ │ 30s  │ │ 15s  │ │ 30s  │              │
│  │ ✓    │ │ ✓    │ │ ⏳   │ │ ✓    │              │
│  └──────┘ └──────┘ └──────┘ └──────┘              │
│                                                      │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐              │
│  │ ...  │ │ ...  │ │ ...  │ │ ...  │              │
│  └──────┘ └──────┘ └──────┘ └──────┘              │
└─────────────────────────────────────────────────────┘
```

**Profile Page**
```
┌─────────────────────────────────────────────────────┐
│  Profile                                             │
│                                                      │
│  @username                                           │
│  Member since: Nov 2025                              │
│                                                      │
│  ──────────────────────────────────────────────     │
│                                                      │
│  Statistics:                                         │
│  • Total Videos: 12                                 │
│  • Total Cost: $24.50                               │
│  • Success Rate: 92%                                │
│                                                      │
│  [Logout]                                           │
└─────────────────────────────────────────────────────┘
```

### 13.3 Color Palette

**Primary Colors:**
- Primary Blue: `#2563EB` (buttons, links)
- Success Green: `#10B981` (completed videos)
- Warning Yellow: `#F59E0B` (processing)
- Error Red: `#EF4444` (failed, delete)

**Neutral Colors:**
- Gray 900: `#111827` (text)
- Gray 600: `#4B5563` (secondary text)
- Gray 200: `#E5E7EB` (borders)
- White: `#FFFFFF` (backgrounds)

### 13.4 Typography

**Fonts:**
- Headings: System font stack (San Francisco, Segoe UI, Roboto)
- Body: System font stack
- Monospace: Courier New (for code, if needed)

**Scale:**
- H1: 2.25rem (36px) - Page titles
- H2: 1.875rem (30px) - Section headers
- Body: 1rem (16px) - Default text
- Small: 0.875rem (14px) - Captions

---

## 14. API Specifications

### 14.1 Authentication Endpoints

#### POST /api/auth/register
**Description:** Create new user account

**Request:**
```json
{
  "username": "john_doe",
  "password": "SecurePass123!",
  "email": "john@example.com"
}
```

**Response (201 Created):**
```json
{
  "message": "User created successfully",
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Errors:**
- 400: Username already exists
- 422: Validation error (password too short, etc.)

---

#### POST /api/auth/login
**Description:** Authenticate user and get JWT token

**Request:**
```json
{
  "username": "john_doe",
  "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "john_doe",
    "total_generations": 5,
    "total_cost": 12.45
  }
}
```

**Errors:**
- 401: Invalid credentials

---

#### GET /api/auth/me
**Description:** Get current user info

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "email": "john@example.com",
  "total_generations": 5,
  "total_cost": 12.45,
  "created_at": "2025-11-10T08:30:00Z",
  "last_login": "2025-11-14T10:15:00Z"
}
```

**Errors:**
- 401: Invalid or expired token

---

### 14.2 Video Generation Endpoints

#### POST /api/generate
**Description:** Start video generation from prompt

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Request:**
```json
{
  "prompt": "Create a luxury watch ad for Instagram"
}
```

**Response (202 Accepted):**
```json
{
  "generation_id": "abc-123-def-456",
  "status": "pending",
  "message": "Video generation started"
}
```

**Errors:**
- 401: Unauthorized
- 422: Invalid prompt (too short, etc.)
- 429: Rate limit exceeded

---

#### GET /api/status/{generation_id}
**Description:** Check generation progress

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response (200 OK):**
```json
{
  "generation_id": "abc-123-def-456",
  "status": "processing",
  "progress": 65,
  "current_step": "Generating video clip 2 of 3",
  "video_url": null,
  "cost": null,
  "error": null,
  "created_at": "2025-11-14T10:30:00Z"
}
```

**Status Values:**
- `pending`: Queued, not started
- `processing`: Currently generating
- `completed`: Successfully completed
- `failed`: Generation failed

**When Completed:**
```json
{
  "generation_id": "abc-123-def-456",
  "status": "completed",
  "progress": 100,
  "current_step": "Complete",
  "video_url": "/output/videos/abc-123-def-456.mp4",
  "cost": 1.87,
  "error": null,
  "created_at": "2025-11-14T10:30:00Z",
  "completed_at": "2025-11-14T10:33:45Z"
}
```

**Errors:**
- 401: Unauthorized
- 404: Generation not found
- 403: Not authorized to view this generation

---

#### POST /api/generations/{id}/cancel
**Description:** Request best-effort cancellation of an in-progress generation (MVP)

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response (202 Accepted):**
```json
{
  "generation_id": "abc-123-def-456",
  "status": "failed",
  "progress": 100,
  "current_step": "Cancelled",
  "video_url": null,
  "cost": 0.0,
  "error": "Cancelled by user"
}
```

**Notes:**
- If the generation has already completed by the time the cancellation request is processed, the backend may return the existing completed state instead of `failed`.
- Cancellation is best-effort only; some work may still complete and be billed if already in-flight.

**Errors:**
- 401: Unauthorized
- 404: Generation not found

---

#### GET /api/video/{generation_id}
**Description:** Get video file

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response (200 OK):**
- Content-Type: `video/mp4`
- Content-Disposition: `attachment; filename="ad_abc-123-def-456.mp4"`
- Binary video data

**Errors:**
- 401: Unauthorized
- 404: Video not found
- 400: Video not ready yet

---

### 14.3 Video Management Endpoints

#### GET /api/generations
**Description:** List all user's videos

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Query Parameters:**
- `limit`: Number of results (default: 20, max: 100)
- `offset`: Pagination offset (default: 0)
- `status`: Filter by status (optional)
- `sort`: Sort order (default: `created_at_desc`)
- `q`: Optional search term to filter by prompt text (case-insensitive substring match)

**Response (200 OK):**
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
      "aspect_ratio": "9:16",
      "cost": 1.87,
      "created_at": "2025-11-14T10:30:00Z",
      "completed_at": "2025-11-14T10:33:45Z"
    },
    // ... more videos
  ]
}
```

---

#### DELETE /api/generations/{id}
**Description:** Delete video

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response (200 OK):**
```json
{
  "message": "Video deleted successfully",
  "generation_id": "abc-123-def-456"
}
```

**Errors:**
- 401: Unauthorized
- 404: Video not found
- 403: Not authorized to delete this video

---

### 14.4 User Profile Endpoints

#### GET /api/user/profile
**Description:** Get user profile and statistics

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "email": "john@example.com",
  "total_generations": 45,
  "total_cost": 87.32,
  "created_at": "2025-11-10T08:30:00Z",
  "last_login": "2025-11-14T10:15:00Z"
}
```

---

## 15. Data Models

### 15.1 User Model

```python
class User(Base):
    __tablename__ = "users"
    
    # Primary Key
    id = Column(String(36), primary_key=True, default=uuid4)
    
    # Authentication
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    
    # Statistics
    total_generations = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    generations = relationship("Generation", back_populates="user")
```

**Fields:**
- `id`: Unique identifier (UUID)
- `username`: Login username (unique, indexed)
- `password_hash`: Bcrypt hashed password
- `email`: Optional email (for future features)
- `total_generations`: Count of videos created
- `total_cost`: Total spending in USD
- `created_at`: Account creation timestamp
- `last_login`: Last successful login timestamp

---

### 15.2 Generation Model

```python
class Generation(Base):
    __tablename__ = "generations"
    
    # Primary Key
    id = Column(String(36), primary_key=True, default=uuid4)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Input
    prompt = Column(Text, nullable=False)
    duration = Column(Integer, default=15)
    aspect_ratio = Column(String(10), default="9:16")
    
    # Status
    status = Column(String(20), default="pending", index=True)
    progress = Column(Integer, default=0)
    current_step = Column(String(100), nullable=True)
    
    # Output
    video_path = Column(String(500), nullable=True)
    video_url = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    
    # Metadata
    framework = Column(String(20), nullable=True)  # PAS, BAB, AIDA
    num_scenes = Column(Integer, nullable=True)
    generation_time_seconds = Column(Integer, nullable=True)
    
    # Cost
    cost = Column(Float, nullable=True)
    
    # Error
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="generations")
```

**Fields:**
- `id`: Unique identifier (UUID)
- `user_id`: Foreign key to users table
- `prompt`: User's input prompt
- `duration`: Video duration (15, 30, or 60 seconds)
- `aspect_ratio`: Video format (9:16, 16:9, 1:1)
- `status`: Generation state (pending, processing, completed, failed)
- `progress`: Percentage complete (0-100)
- `current_step`: Current pipeline stage description
- `video_path`: Server file path
- `video_url`: Public URL for frontend
- `thumbnail_url`: Video thumbnail URL
- `framework`: Ad framework used (PAS, BAB, AIDA)
- `num_scenes`: Number of scenes in video
- `generation_time_seconds`: Total generation time
- `cost`: Generation cost in USD
- `error_message`: Error details if failed
- `created_at`: Request timestamp
- `completed_at`: Completion timestamp

---

## 16. Security & Privacy

### 16.1 Authentication Security

**Password Storage:**
- Passwords hashed using bcrypt with cost factor 12
- Never store plain-text passwords
- Password requirements: minimum 8 characters

**JWT Tokens:**
- Signed with 256-bit secret key
- Expiration: 7 days
- Payload: user_id, username, issued_at, expiration
- Verified on every protected endpoint

**HTTPS (Production):**
- All API communication over HTTPS
- SSL certificate via Let's Encrypt (optional for MVP)

### 16.2 Authorization

**User Data Access:**
- Users can only access their own videos
- Video ownership checked on every request
- JWT user_id compared to generation.user_id

**API Rate Limiting:**
- 10 video generations per user per hour
- 100 API requests per user per minute
- Prevents abuse and controls costs

### 16.3 Input Validation

**Prompt Validation:**
- Minimum length: 10 characters
- Maximum length: 500 characters
- Sanitize HTML/scripts from input

**SQL Injection Prevention:**
- SQLAlchemy ORM parameterized queries
- Never construct raw SQL from user input

**File Upload Security (Future):**
- File type validation (images only)
- File size limit: 100MB
- Virus scanning (optional)

### 16.4 Data Privacy

**User Data:**
- No sharing of user data with third parties
- No analytics tracking without consent
- Videos deleted from storage after 30 days (optional)

**API Keys:**
- Replicate and OpenAI keys stored in backend .env only
- Never exposed to frontend
- Rotate keys regularly

### 16.5 Error Handling

**Error Disclosure:**
- User-friendly error messages (no stack traces)
- Internal errors logged server-side
- No exposure of system internals

---

## 17. Performance Requirements

### 17.1 Video Generation Performance

**Speed Targets:**
- 15s video: <3 minutes (target: 2 minutes)
- 30s video: <6 minutes (target: 4 minutes)
- 60s video: <12 minutes (target: 8 minutes)

**Pipeline Breakdown:**
- LLM enhancement: 5-10 seconds
- Scene planning: 2 seconds
- Video generation (3 clips): 60-90 seconds
- Text overlay: 5 seconds
- Stitching: 10 seconds
- Audio layer: 5 seconds
- Export: 15 seconds

**Optimization Strategies:**
- Parallel video clip generation
- GPU acceleration for video processing (optional)
- Cached music library (no generation needed)
- Optimized FFmpeg encoding settings

### 17.2 API Performance

**Response Times:**
- Authentication: <500ms
- Status check: <200ms
- Gallery load (20 videos): <1 second
- Video streaming: <2 seconds to first frame

**Database Query Optimization:**
- Indexes on user_id, status, created_at
- Pagination for large result sets
- Connection pooling

### 17.3 Scalability (Post-MVP)

**Concurrent Users (Post-MVP):**
- Support 10 concurrent video generations
- Queue additional requests
- Horizontal scaling via multiple EC2 instances

**Storage Management:**
- Video files: 50GB initial capacity
- Automatic cleanup of temp files after 1 day
- Optional: Move to S3 for unlimited storage

---

## 18. Cost Structure

### 18.1 Per-Video Cost Breakdown

**15-Second Video (3 scenes @ 5s each):**

| Component | Provider | Cost |
|-----------|----------|------|
| LLM Enhancement | OpenAI GPT-4 | $0.01 |
| Video Clips (3x 5s) | Replicate (Minimax) | $0.75 |
| Video Processing | Local (MoviePy) | $0.00 |
| Music | Library (royalty-free) | $0.00 |
| **Total** | | **$0.76** |

**30-Second Video (5 scenes @ 6s each):**

| Component | Provider | Cost |
|-----------|----------|------|
| LLM Enhancement | OpenAI GPT-4 | $0.01 |
| Video Clips (5x 6s) | Replicate (Minimax) | $1.50 |
| Video Processing | Local (MoviePy) | $0.00 |
| Music | Library (royalty-free) | $0.00 |
| **Total** | | **$1.51** |

**Cost per Second of Video:**
- Minimax Video-01: ~$0.05 per second
- Runway Gen-3 Turbo: ~$0.05 per second
- Kling 1.5: ~$0.03 per second

### 18.2 Monthly Operating Costs

**AWS EC2:**
- t3.large (8GB RAM, 2 vCPU): ~$60/month
- t3.xlarge (16GB RAM, 4 vCPU): ~$120/month
- EBS Storage (50GB): ~$5/month
- Data Transfer: ~$10-20/month

**API Costs (Example for 1000 videos/month):**
- OpenAI API: $10
- Replicate API: $760-1510
- **Total API**: ~$770-1520/month

**Total Monthly Cost:** ~$850-1665 for 1000 videos

**Cost per User (20 videos/month):** ~$17-33

---

## 19. Deployment Strategy

### 19.1 Deployment Architecture

**Single EC2 + RDS Deployment:**
- Application services on one EC2 instance (frontend + backend)
- Nginx serves React build and proxies API
- FastAPI runs via systemd service
- AWS RDS PostgreSQL instance for the primary relational database
- Local file storage for videos

**Components:**
- Nginx: Port 80/443 (web server, reverse proxy)
- FastAPI: Port 8000 (API server)
- PostgreSQL: Managed via AWS RDS (separate instance in same VPC)
- File Storage: /var/www/ad-generator/backend/output/

### 19.2 Deployment Process

**Initial Setup:**
1. Launch AWS EC2 instance (Ubuntu 22.04 LTS)
2. Install dependencies (Python, Node.js, FFmpeg, Nginx)
3. Clone repository from GitHub
4. Set up Python virtual environment
5. Install Python dependencies
6. Build React frontend (npm run build)
7. Configure Nginx
8. Create systemd service for FastAPI
9. Start services

**Continuous Deployment:**
1. Push code to GitHub
2. SSH into EC2 instance
3. Pull latest code
4. Rebuild frontend
5. Restart FastAPI service
6. Restart Nginx (if config changed)

**Deployment Script:**
```bash
#!/bin/bash
# deploy.sh

git pull origin main

# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart fastapi

# Frontend
cd ../frontend
npm install
npm run build
sudo rm -rf /var/www/html/ad-generator/*
sudo cp -r dist/* /var/www/html/ad-generator/

sudo systemctl restart nginx

echo "Deployment complete!"
```

### 19.3 Environment Configuration

**Backend (.env):**
```
DATABASE_URL=postgresql+psycopg2://ad_mint_ai_app:strongpassword@your-rds-endpoint.amazonaws.com:5432/ad_mint_ai
REPLICATE_API_TOKEN=r8_xxxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
JWT_SECRET_KEY=xxxxxxxxxxxxx
OUTPUT_DIR=/var/www/ad-generator/backend/output
```

**Frontend (.env):**
```
VITE_API_URL=http://your-ec2-ip
```

### 19.4 Monitoring & Logging

**Logging:**
- FastAPI logs: `/var/log/fastapi/app.log`
- Nginx access logs: `/var/log/nginx/access.log`
- Nginx error logs: `/var/log/nginx/error.log`

**Monitoring:**
- Manual health checks via `/api/health` endpoint
- Monitor disk space for video storage
- Track API costs via Replicate dashboard

**Backup:**
- Daily database backup to S3 (optional)
- Video retention: 30 days

---

## 20. Future Enhancements

### 20.1 Phase 2 Features

**Advanced Options:**
- User-selectable duration (15s, 30s, 60s)
- User-selectable aspect ratio (9:16, 16:9, 1:1)
- Style presets (Luxury, Minimal, Vibrant, Tech)
- Brand color picker (up to 3 colors)
- Framework selection (PAS, BAB, AIDA)

**Brand Guidelines:**
- Upload brand logo
- Save brand presets for reuse
- Custom fonts (upload TTF files)
- Brand voice/tone settings

**Advanced Video Editing:**
- Regenerate specific scenes
- Edit text overlays
- Change music track
- Apply different color grading
- Advanced timeline effects and filters

### 20.2 Phase 3 Features

**Collaboration:**
- Share videos with team members
- Comment on videos
- Approval workflows
- Team workspaces

**Analytics:**
- View count tracking
- Engagement metrics
- A/B testing results
- Cost per video analytics dashboard

**Integrations:**
- Direct upload to Instagram, TikTok, YouTube
- Export to Google Drive, Dropbox
- Webhook notifications
- Zapier integration

**AI Enhancements:**
- Voice-over generation (text-to-speech)
- Custom music generation per video
- Real video footage (not just AI-generated)
- Character consistency across scenes (implemented in Epic 7 via IP-Adapter, LoRA, and CSFD)
- Advanced prompt optimization with style transfer (implemented in Epic 7 via VideoDirectorGPT-style planning)
- Multi-model ensemble generation for quality improvement
- **Note:** Epic 7 (Multi-Scene Coherence & Quality Optimization) implements advanced coherence techniques including seed control, IP-Adapter, LoRA training, VBench quality metrics, CSFD character consistency, ControlNet compositional consistency, and enhanced post-processing. These features are available in MVP scope with user-controllable settings.

### 20.3 Enterprise Features

**API Access:**
- RESTful API for programmatic access
- Bulk video generation
- Webhook callbacks
- API rate limits per tier

**White Label:**
- Custom branding
- Remove "Powered by" attribution
- Custom domain

**Advanced Controls:**
- Video resolution selection (720p, 1080p, 4K)
- Frame rate options (24, 30, 60 fps)
- Codec selection
- Bitrate control

---

## 21. Risks & Mitigations

### 21.1 Technical Risks

**Risk: Video Generation Failures**
- **Likelihood:** Medium
- **Impact:** High (user frustration, poor experience)
- **Mitigation:**
  - Implement automatic retry logic (up to 3 attempts)
  - Fallback to alternative video models if primary fails
  - Clear error messages with actionable steps
  - "Retry" button for failed generations

**Risk: API Rate Limits**
- **Likelihood:** Medium
- **Impact:** High (blocked generations, poor UX)
- **Mitigation:**
  - Implement user-level rate limiting (10 videos/hour)
  - Queue system for concurrent requests
  - Monitor API usage and set alerts
  - Cache common generations (future)

**Risk: High API Costs**
- **Likelihood:** High
- **Impact:** High (unprofitable, budget overrun)
- **Mitigation:**
  - Use cheapest viable models (Minimax, not Runway)
  - Implement strict user rate limiting
  - Monitor costs daily via dashboard
  - Set monthly budget caps
  - Implement paid tiers before scaling

**Risk: Storage Capacity**
- **Likelihood:** Medium
- **Impact:** Medium (disk full, failed saves)
- **Mitigation:**
  - Auto-delete temp files after 1 day
  - Implement video retention policy (30 days)
  - Monitor disk usage and alert at 80%
  - Migrate to S3 for unlimited storage

### 21.2 Product Risks

**Risk: Poor Video Quality**
- **Likelihood:** Medium
- **Impact:** High (user dissatisfaction, churn)
- **Mitigation:**
  - Test extensively with diverse prompts
  - Implement quality scoring system
  - Allow regeneration at no cost if quality is poor
  - Continuously improve prompt engineering
  - Collect user feedback and iterate

**Risk: Framework Selection Errors**
- **Likelihood:** Low
- **Impact:** Medium (incorrect narrative structure)
- **Mitigation:**
  - Extensive testing of LLM framework selection
  - Manual override option (future feature)
  - A/B test framework effectiveness
  - Refine LLM system prompts based on data

**Risk: Inconsistent Visual Style**
- **Likelihood:** Medium
- **Impact:** Medium (unprofessional look)
- **Mitigation:**
  - Use consistent brand keywords across all scenes
  - Test style consistency across models
  - Implement post-processing color grading
  - Add style reference images (future)

### 21.3 Business Risks

**Risk: Competition**
- **Likelihood:** High
- **Impact:** Medium (market share loss)
- **Mitigation:**
  - Focus on framework-based storytelling (differentiation)
  - Emphasize zero-configuration UX
  - Build strong brand and community
  - Rapid iteration and feature development
  - Focus on quality over quantity

**Risk: AI Model Changes**
- **Likelihood:** Medium
- **Impact:** High (API breakage, quality degradation)
- **Mitigation:**
  - Support multiple video generation models
  - Version lock critical dependencies
  - Monitor model updates from providers
  - Test new model versions before switching
  - Maintain fallback options

**Risk: Low User Adoption**
- **Likelihood:** Medium
- **Impact:** High (failed product launch)
- **Mitigation:**
  - Extensive user testing before launch
  - Clear value proposition and demo videos
  - Free tier to lower entry barrier
  - Marketing via social media and product communities
  - Iterate based on user feedback

**Risk: Regulatory/Copyright Issues**
- **Likelihood:** Low
- **Impact:** High (legal liability)
- **Mitigation:**
  - Use only licensed music (royalty-free library)
  - Terms of Service: users own their videos
  - AI-generated content disclosure
  - Monitor copyright landscape
  - Consult legal counsel for commercial use

### 21.4 Operational Risks

**Risk: Server Downtime**
- **Likelihood:** Low
- **Impact:** High (lost revenue, user frustration)
- **Mitigation:**
  - Implement health checks and monitoring
  - Automated alerting (email, SMS)
  - Documented incident response plan
  - Regular backups
  - Failover strategy (multi-instance deployment)

**Risk: Data Loss**
- **Likelihood:** Low
- **Impact:** High (user trust loss)
- **Mitigation:**
  - Daily automated database backups to S3
  - Test backup restoration regularly
  - Video file replication (future)
  - Version control for code
  - Document disaster recovery procedures

---

## 22. Appendices

### 22.1 Glossary

**Terms:**

- **Ad Framework:** Proven narrative structure for advertising (PAS, BAB, AIDA)
- **Aspect Ratio:** Video dimensions (9:16 vertical, 16:9 horizontal, 1:1 square)
- **CTA (Call-to-Action):** Final message prompting user action ("Buy Now", "Learn More")
- **Crossfade:** Transition where one scene fades out as next fades in
- **Generation:** The process of creating a video from a prompt
- **JWT (JSON Web Token):** Secure token for user authentication
- **Ken Burns Effect:** Motion effect on static images (zoom, pan)
- **LLM (Large Language Model):** AI model for text generation (GPT-4, Claude)
- **MVP (Minimum Viable Product):** Basic version with core features
- **Scene:** Individual segment of video (3-7 seconds)
- **Text Overlay:** Text displayed on top of video
- **Video Stitching:** Combining multiple clips into one video

**Frameworks:**

- **PAS (Problem-Agitate-Solve):** Show problem → intensify pain → present solution
- **BAB (Before-After-Bridge):** Show current state → dream state → product as path
- **AIDA (Attention-Interest-Desire-Action):** Hook → explain → build desire → CTA

### 22.4 Ad Framework Resources

**Marketing Psychology:**
- "Influence: The Psychology of Persuasion" by Robert Cialdini
- "Made to Stick" by Chip Heath and Dan Heath
- "Contagious: Why Things Catch On" by Jonah Berger

**Advertising Best Practices:**
- AIDA Model: https://en.wikipedia.org/wiki/AIDA_(marketing)
- PAS Framework: https://copyblogger.com/problem-agitate-solve/
- Before-After-Bridge: https://www.copyhackers.com/

**Video Marketing:**
- Facebook Video Ads Best Practices
- TikTok Creative Center
- YouTube Ads Leaderboard

### 22.5 Technical Documentation

**API Documentation:**
- See `docs/API.md` for complete API reference
- Postman collection: `docs/postman_collection.json`

**Architecture:**
- See `docs/ARCHITECTURE.md` for detailed system design
- Pipeline flow diagram: `docs/pipeline_diagram.png`

**Deployment:**
- See `docs/DEPLOYMENT.md` for step-by-step deployment guide
- Nginx config: `deployment/nginx.conf`
- Systemd service: `deployment/fastapi.service`

### 22.6 Sample Prompts

**Good Prompts (Clear and Specific):**
- "Create a luxury watch ad for Instagram"
- "Make a 30-second eco-friendly water bottle ad"
- "Generate a tech startup ad with modern aesthetics"
- "Create an energetic fitness app ad for TikTok"
- "Make a minimalist skincare product ad"

**Poor Prompts (Too Vague):**
- "Make a video" (no product specified)
- "Ad" (no context)
- "Something cool" (no direction)

**Tips for Better Results:**
- Specify product category (watch, water bottle, app)
- Include style adjectives (luxury, minimalist, energetic)
- Mention platform if relevant (Instagram, TikTok)

### 22.7 Example LLM Output

**Input Prompt:** "Create a luxury watch ad"

**LLM Generated JSON:**
```json
{
  "analysis": {
    "product_type": "luxury_product",
    "target_audience": "affluent_professionals_25-45",
    "pain_point": "desire_for_status_and_quality",
    "best_framework": "BAB",
    "rationale": "Luxury watches are aspirational - BAB shows transformation"
  },
  "product_description": "A premium luxury smartwatch for discerning professionals who demand both elegance and cutting-edge technology. Features sapphire crystal display, 7-day battery, and advanced health tracking.",
  "brand_guidelines": {
    "brand_name": "Chronos Elite",
    "brand_colors": ["#0A192F", "#D4AF37", "#FFFFFF"],
    "visual_style_keywords": "elegant, sophisticated, luxury, minimalist, cinematic lighting, golden hour, professional photography",
    "mood": "aspirational, confident, premium, refined"
  },
  "ad_specifications": {
    "ad_duration_seconds": 15,
    "aspect_ratio": "9:16",
    "framework": "BAB",
    "call_to_action_text": "Elevate Your Time",
    "music_style": "elegant_orchestral_minimal",
    "pacing": "slow_cinematic"
  },
  "scenes": [
    {
      "scene_number": 1,
      "scene_type": "Before",
      "duration_seconds": 5,
      "narrative_purpose": "Show current reality",
      "visual_prompt": "Close-up of generic smartwatch on wrist in dull office setting, flat lighting, muted colors, 9:16 vertical, cinematic",
      "text_overlay": {
        "text": "Your Time",
        "position": "top_center",
        "font_style": "modern_serif",
        "color": "#FFFFFF",
        "animation": "fade_in"
      },
      "transition_out": "crossfade"
    },
    {
      "scene_number": 2,
      "scene_type": "After",
      "duration_seconds": 5,
      "narrative_purpose": "Show aspirational reality",
      "visual_prompt": "Stunning close-up of luxury smartwatch with golden accents in upscale lounge with golden hour lighting, 9:16 vertical, luxury photography",
      "text_overlay": {
        "text": "Elevated",
        "position": "center",
        "font_style": "elegant_serif",
        "color": "#D4AF37",
        "animation": "fade_in_scale"
      },
      "transition_out": "fade_through_white"
    },
    {
      "scene_number": 3,
      "scene_type": "Bridge",
      "duration_seconds": 5,
      "narrative_purpose": "Product hero shot with CTA",
      "visual_prompt": "Hero product shot of luxury smartwatch floating against dark minimalist background with dramatic golden lighting, 9:16 vertical, advertising quality",
      "text_overlay": {
        "text": "Chronos Elite\nElevate Your Time",
        "position": "bottom_center",
        "font_style": "luxury_serif",
        "color": "#D4AF37",
        "animation": "slide_up_fade_in"
      },
      "transition_out": "fade_out"
    }
  ],
  "audio_layer": {
    "background_music": {
      "style": "elegant_minimal_orchestral",
      "mood": "sophisticated, aspirational, premium",
      "tempo": "slow_70_bpm",
      "volume": 0.3
    },
    "sound_effects": [
      {
        "scene": 2,
        "type": "luxury_transition_whoosh",
        "timing": "0s"
      }
    ]
  }
}
```

### 22.8 Video Generation Models Comparison

| Model | Provider | Cost/Second | Quality | Speed | Best For |
|-------|----------|-------------|---------|-------|----------|
| Runway Gen-3 Alpha Turbo | Runway ML | $0.05 | High | Medium | High-quality output |
| Kling 1.5 | Kling AI | $0.03 | Good | Fast | Balanced quality/cost |
| Minimax Video-01 | Minimax | $0.05 | Good | Fast | Cost-effective MVP |
| Luma Dream Machine | Luma Labs | $0.04 | Good | Medium | Creative content |

**Recommended for MVP:** Minimax Video-01 (good quality, fast, predictable)

### 22.9 Project Timeline

**Week 1 (MVP - Core Functionality):**
- Day 1-2: Project setup, authentication (PR #1-4)
- Day 3-4: Video generation pipeline (PR #6-12)
- Day 5-6: Frontend UI (PR #14-16)
- Day 7: Testing and bug fixes (PR #26)

**Week 2 (Polish & Deployment):**
- Day 8-9: Error handling, responsive design (PR #18-20)
- Day 10-11: Documentation and deployment (PR #23-24)
- Day 12-13: Performance optimization (PR #25)
- Day 14: Final testing, demo video, submission (PR #27)

### 22.10 Success Criteria

**MVP Launch Criteria:**
- [ ] User can register and login
- [ ] User can generate video from simple prompt
- [ ] Video generation completes in <5 minutes
- [ ] Video quality is professional (1080p minimum)
- [ ] User can view, download, and delete videos
- [ ] Cost per video is <$200 (quality-focused)
- [ ] Success rate >80%
- [ ] Application deployed and accessible online
- [ ] Demo video recorded
- [ ] Documentation complete

**Post-Launch Success Metrics (Month 1):**
- [ ] 100+ registered users
- [ ] 500+ videos generated
- [ ] 80%+ video completion rate
- [ ] <20% regeneration rate
- [ ] 4+/5 user satisfaction score
- [ ] 99%+ system uptime
- [ ] <$2 average cost per video

### 22.11 Contact & Support

**Development Team:**
- GitHub Repository: [repository-url]
- Documentation: [docs-url]
- Issues/Bugs: [github-issues-url]

**For Questions:**
- Create GitHub issue with `question` label
- Check documentation first: `docs/` folder
- Review API documentation: `docs/API.md`

---

## 23. Hero-Frame Iteration Plan & Timeline

This section describes how the new hero-frame-first, iterative refinement workflow will be rolled out over time. It is designed as an additive “professional mode” that builds on top of the existing MVP pipeline and Epic 7 quality/coherence capabilities.

### 23.1 Phase Overview (Hero Frame → Video → Iteration)

The hero-frame workflow is organized into **five phases**:

1. **Phase 1: Hero Frame Generation (TEXT → PHOTO)**
   - Implement the hero-frame generation service using text-to-image models (Replicate / SDXL).
   - Build a hero-frame gallery UI that displays **4–8 variations** per prompt and supports hero-frame selection.
   - Integrate LLM-based cinematographer prompt enhancement (FR-037), exposed as an optional step before generation.
   - Persist hero frames and their metadata for reuse in downstream video generations and experiments.

2. **Phase 2: Image-to-Video Workflow (PHOTO → VIDEO)**
   - Implement image-to-video generation from a selected hero frame using models such as Kling, Wan, or PixVerse.
   - Extend the generation request schema to include motion prompts (camera movement, frame rate, motion intensity).
   - Add negative prompt support to suppress artifacts and stabilize motion.
   - Integrate with the existing video pipeline so that audio, stitching, and post-processing still apply.

3. **Phase 3: Automated Feedback (3 Auto-Attempts)**
   - Enable **automated 3-attempt generation** for each image-to-video request (FR-040).
   - Run VBench (or equivalent) on all attempts and compute per-attempt and overall quality scores.
   - Auto-select the top-scoring attempt as the “system-selected best”, while retaining all attempts for user review.
   - Persist attempt-level quality metrics for use in dashboards and future feedback loops.

4. **Phase 4: Human-in-the-Loop Refinement**
   - Deliver the **Iteration Workspace** UI (FR-041) with side-by-side comparison of video attempts.
   - Support manual prompt editing for both hero-frame and motion prompts.
   - Integrate LLM-powered prompt improvement suggestions driven by VBench feedback and user comments.
   - Allow manual override of the auto-selected best attempt; track overrides for quality analysis.

5. **Phase 5: Iterative Refinement Workflow & Quality Dashboard**
   - Implement generation history and versioning (FR-042), showing iterations and selected versions.
   - Provide a quality dashboard (FR-043) that visualizes VBench metrics, iteration counts, and selection patterns.
   - Add comparison views between versions and make the final version pointer explicit for export, analytics, and reporting.

### 23.2 Workflow Sequence (End-to-End)

The end-to-end hero-frame iterative workflow shall operate as:

1. User enters a high-level ad prompt.
2. System offers LLM-based cinematographer enhancement and generates 4–8 hero frames (TEXT → PHOTO).
3. User selects a hero frame as the anchor.
4. System generates 3 image-to-video attempts from that hero frame (PHOTO → VIDEO) using motion + negative prompts.
5. VBench evaluates all attempts; system auto-selects the best-scoring attempt and surfaces it in the UI.
6. User opens the Iteration Workspace, reviews all attempts (side-by-side, with metrics), and may:
   - Accept the auto-selected best
   - Choose a different attempt as best
   - Edit prompts and regenerate additional attempts
7. System tracks each iteration as a version; the user iterates until satisfied.
8. Final selected version flows into the existing editor (Epic 6), export, and gallery paths.

### 23.3 Implementation Timeline (Hero-Frame Workflow)

This timeline focuses specifically on delivering the hero-frame and iterative refinement capabilities, assuming the core MVP pipeline and most epics are already in place.

**Phase 1–2 (Weeks 1–4) – Foundation**
- Week 1:
  - Backend: Hero-frame generation API (text-to-image via Replicate).
  - Frontend: Hero-frame gallery UI and selection flow.
  - Data: Hero frame storage and linkage to users/generations.
- Week 2:
  - LLM cinematographer prompt enhancement service (FR-037) and UI.
  - Backend: Image-to-video service wrapper for Kling/Wan/PixVerse.
  - Schema updates for motion and negative prompts.
- Week 3–4:
  - Integration of hero-frame-first path into existing generation flow.
  - QA across a variety of prompts and aspect ratios.

**Phase 3–4 (Weeks 5–6) – Automation & Human-in-the-Loop**
- Week 5:
  - Automated 3-attempt mode and VBench evaluation integration (FR-040).
  - Auto-selection logic and persistence of attempt-level metrics.
- Week 6:
  - Iteration Workspace UI (FR-041) with side-by-side comparison and prompt editing.
  - LLM-based prompt improvement suggestions and override logging.

**Phase 5 (Weeks 7–8) – Iterative Refinement & Dashboard**
- Week 7:
  - Versioning and generation history (FR-042).
  - Final-version pointer and integration with gallery, editor, and export.
- Week 8:
  - Quality Dashboard (FR-043) with VBench visualization and iteration analytics.
  - Polishing UX for professional workflows; final validation and documentation.

### 23.4 Success Metrics (Hero-Frame Workflow)

In addition to existing product KPIs, success for this workflow is measured by:
- ≥70% agreement between auto-selected “best” attempt and user-selected final version.
- ≥50% of professional users adopting hero-frame mode for complex campaigns.
- Median iterations per final video ≤ 3 (user reaches satisfaction quickly).
- Observable upward trend in VBench scores across iterations within the same project.

### 23.5 Risks & Mitigations (Incremental)

**Risk: Excessive Computational Cost from Auto-Attempts**
- **Mitigations:**
  - Limit auto-attempts to 3 by default, configurable per workspace.
  - Gate hero-frame iterative mode behind a “pro” flag or environment toggle initially.
  - Track cost per attempt set and alert when thresholds are exceeded.

**Risk: User Overwhelm from Too Many Options**
- **Mitigations:**
  - Default to simple prompt-to-video flow; expose hero-frame mode as an advanced option.
  - Provide clear visual hierarchy: “Recommended best” vs. alternatives.
  - Offer opinionated defaults (e.g., motion prompt templates, recommended negative prompts).

**Risk: Misalignment Between VBench Scores and Human Judgement**
- **Mitigations:**
  - Track disagreements between auto-selected best and user-selected best over time.
  - Use disagreements as input to improve VBench thresholds and prompt suggestions.
  - Allow users to disable auto-selection and rely solely on human choice if desired.

### 23.6 API Endpoints (Hero-Frame Workflow)

The following endpoints extend the existing API to support the hero-frame workflow (high-level spec; detailed request/response schemas will follow the patterns in section 14):

- **POST `/api/hero-frames`**
  - Description: Generate 4–8 hero frame candidates from a text prompt.
  - Body: `{ "prompt": string, "enhance_with_llm": boolean }`
  - Response: List of hero frame objects with IDs, URLs, and metadata.

- **GET `/api/hero-frames/{id}`**
  - Description: Retrieve a specific hero frame and its metadata.

- **POST `/api/hero-frames/{id}/select`**
  - Description: Mark a hero frame as the primary anchor for a new generation.

- **POST `/api/image-to-video`**
  - Description: Start image-to-video generation from a selected hero frame.
  - Body includes: `hero_frame_id`, `motion_prompt`, `negative_prompt`, `auto_attempts` (default: 3).
  - Response: Returns a generation group ID and initial status.

- **GET `/api/generation-groups/{group_id}`**
  - Description: Retrieve all attempts for a generation group, including VBench scores and selection flags.

- **POST `/api/generation-groups/{group_id}/select`**
  - Description: Mark a specific attempt as the user-selected best and update the final version pointer.

### 23.7 Data Model Changes (High-Level)

The hero-frame workflow introduces new entities and relationships; exact schema will be refined in the technical spec, but at PRD level:

- **HeroFrame**
  - Fields (conceptual): `id`, `user_id`, `prompt`, `enhanced_prompt`, `image_path`, `thumbnail_path`, `model`, `seed`, `aspect_ratio`, `created_at`.
  - Relationships: Belongs to a user; may be linked to one or more generation groups.

- **GenerationGroup**
  - Fields: `id`, `user_id`, `hero_frame_id`, `comparison_type` (settings vs prompt), `created_at`.
  - Relationships: Has many `VideoAttempt` records; links a set of related generations.

- **VideoAttempt**
  - Fields: `id`, `group_id`, `generation_id`, `iteration_index`, `is_system_selected_best`, `is_user_selected_best`, `vbench_score_overall`, `status`, `created_at`.
  - Relationships: Belongs to a `GenerationGroup` and to a `Generation`.

- **QualityMetric / VBenchScore**
  - Fields: `id`, `attempt_id`, `metric_name`, `metric_value`, `created_at`.
  - Purpose: Store detailed per-dimension VBench metrics to power dashboards and feedback loops.

### 23.8 Component Breakdown (Hero-Frame Workflow)

At a high level, the hero-frame workflow adds the following components, building on existing architecture:

- **Backend Services**
  - `hero_frame_service`: Orchestrates text-to-image generation, stores hero frames and metadata.
  - `image_to_video_service`: Wraps Kling/Wan/PixVerse APIs, including motion and negative prompts.
  - `quality_evaluation_service`: Runs VBench on attempts and stores scores.
  - `iteration_service`: Manages generation groups, attempts, versioning, and final-version pointers.

- **Frontend Components**
  - `HeroFrameGenerator` (Dashboard extension): Prompt input, LLM enhancement, and hero-frame gallery.
  - `HeroFrameGallery`: Grid view with zoom and selection, tied to user history.
  - `IterationWorkspace`: Side-by-side comparison view with metrics, prompt editing, and regeneration controls.
  - `QualityDashboard`: Aggregated view of VBench metrics, iteration counts, and adoption statistics.

- **Integration Points**
  - Existing `/api/generate` flow remains unchanged for simple users.
  - Hero-frame flow plugs into the same `generations` and gallery mechanisms once a final version is selected.
  - Epic 6 editor can be launched from any final version produced by this workflow.

---

## Document Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Nov 14, 2025 | Dev Team | Initial PRD creation |
| 1.1 | Nov 14, 2025 | PM Agent | Added video editing user stories (timeline, trim, split, merge) and video quality optimization features (coherence enhancement, LLM prompt optimization) |
| 1.2 | Nov 17, 2025 | PM Agent | Added hero-frame-first iterative workflow (FR-036–FR-044) and Hero-Frame Iteration Plan & Timeline section for professional, image-driven iteration with automated VBench feedback and human-in-the-loop refinement |

---

## Approval & Sign-off

**Product Owner:** ___________________ Date: ___________

**Technical Lead:** ___________________ Date: ___________

**Stakeholder:** ___________________ Date: ___________

---

**END OF DOCUMENT**