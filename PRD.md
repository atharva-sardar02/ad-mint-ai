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

---

## 1. Executive Summary

### 1.1 Product Vision

AI Video Ad Generator is a web application that enables users to create professional-quality video advertisements from simple text prompts. The system leverages advanced AI models and proven advertising frameworks to automatically generate coherent, persuasive video content suitable for social media platforms like Instagram, TikTok, and YouTube.

### 1.2 Key Features

- **Simple Text-to-Video Generation**: Users input a product description, and the system generates a complete video ad
- **AI-Powered Creative Direction**: LLM automatically determines brand guidelines, colors, style, and music
- **Framework-Based Storytelling**: Implements proven advertising frameworks (PAS, BAB, AIDA)
- **Professional Video Composition**: Multi-scene videos with transitions, text overlays, and background music
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
- **Cost-Effective**: ~$0.80-2.00 per video vs. $500-5000 for traditional production
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
4. **Cost Efficiency**: Under $2 per video for system costs
5. **User Satisfaction**: 80%+ of videos require no regeneration

### 5.2 Success Metrics (KPIs)

**Technical Performance:**
- Video generation success rate: >90%
- Average generation time: <3 minutes
- Cost per video: <$2.00
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

---

## 8. Functional Requirements

### 8.1 User Authentication

**FR-001: User Registration**
- System shall allow users to create accounts with username and password
- Username must be unique (3-50 characters)
- Password must be hashed using bcrypt
- Optional email field for future password recovery

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
- System shall track cost per generation:
  - LLM API calls
  - Video generation per clip
  - Total cost stored in database
- System shall update user's total_cost field

### 8.3 Video Management

**FR-016: Video Gallery**
- System shall display all user's generated videos
- Grid layout with video thumbnails
- Display metadata: prompt, date, duration, status, cost
- Sort by creation date (newest first)
- Click thumbnail to view video detail

**FR-017: Video Playback**
- System shall serve video files from storage
- HTML5 video player with controls
- Autoplay on video detail page
- Support for different aspect ratios

**FR-018: Video Download**
- System shall allow users to download MP4 files
- File naming: `ad_{generation_id}.mp4`
- Download button on video detail page

**FR-019: Video Deletion**
- System shall allow users to delete their videos
- Confirmation dialog before deletion
- Remove video file from storage and database record
- Only video owner can delete

**FR-020: Video Search**
- System shall filter videos by prompt text (optional feature)
- System shall filter by status (completed, failed, processing)

### 8.4 User Profile

**FR-021: Profile Display**
- System shall show user statistics:
  - Total videos generated
  - Total cost spent
  - Account creation date
  - Last login timestamp
- Display username and email (if provided)

**FR-022: User Stats Update**
- System shall increment total_generations on video completion
- System shall add generation cost to total_cost
- System shall update last_login on each login

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

**NFR-003: Concurrent Users**
- Support 10 concurrent video generations
- Queue additional requests if limit exceeded
- Graceful degradation under high load

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

**NFR-013: Error Messages**
- User-friendly error messages (no technical jargon)
- Actionable suggestions (e.g., "Retry" button)
- Error logging for debugging

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

### 10.1 System Architecture Diagram

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

### 10.2 Technology Stack Details

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
- SQLite 3 (Development)
- PostgreSQL 14+ (Production - optional)

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

### 17.3 Scalability

**Concurrent Users:**
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

### 18.3 Pricing Strategy (Future)

**Free Tier:**
- 3 videos per month
- 15s videos only
- Watermarked output

**Pro Tier ($29/month):**
- 50 videos per month
- All durations (15s, 30s, 60s)
- No watermark
- Priority generation

**Business Tier ($99/month):**
- Unlimited videos
- API access
- Custom branding
- Dedicated support

---

## 19. Deployment Strategy

### 19.1 Deployment Architecture

**Single EC2 Instance Deployment:**
- All services on one server (frontend + backend)
- Nginx serves React build and proxies API
- FastAPI runs via systemd service
- Local file storage for videos

**Components:**
- Nginx: Port 80/443 (web server, reverse proxy)
- FastAPI: Port 8000 (API server)
- SQLite: Local database file
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
DATABASE_URL=sqlite:///./production.db
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

**Video Editing:**
- Regenerate specific scenes
- Edit text overlays
- Change music track
- Adjust scene durations
- Apply different color grading

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
- Character consistency across scenes

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

### 22.2 Acronyms

- **AI:** Artificial Intelligence
- **API:** Application Programming Interface
- **AWS:** Amazon Web Services
- **CDN:** Content Delivery Network
- **CTA:** Call-to-Action
- **EC2:** Elastic Compute Cloud (AWS virtual servers)
- **FPS:** Frames Per Second
- **HTTP/HTTPS:** HyperText Transfer Protocol (Secure)
- **JWT:** JSON Web Token
- **LLM:** Large Language Model
- **MP4:** MPEG-4 video format
- **MVP:** Minimum Viable Product
- **ORM:** Object-Relational Mapping
- **PRD:** Product Requirements Document
- **REST:** Representational State Transfer
- **S3:** Simple Storage Service (AWS)
- **SDK:** Software Development Kit
- **SQL:** Structured Query Language
- **SSL:** Secure Sockets Layer
- **UI/UX:** User Interface / User Experience
- **URL:** Uniform Resource Locator
- **UUID:** Universally Unique Identifier

### 22.3 References

**AI Video Generation Models:**
- Runway Gen-3: https://runwayml.com/
- Kling AI: https://klingai.com/
- Minimax Video-01: https://replicate.com/minimax/video-01
- Luma Dream Machine: https://lumalabs.ai/

**LLM Providers:**
- OpenAI GPT-4: https://platform.openai.com/
- Anthropic Claude: https://www.anthropic.com/

**Video Processing Libraries:**
- MoviePy: https://zulko.github.io/moviepy/
- OpenCV: https://opencv.org/
- FFmpeg: https://ffmpeg.org/

**Frontend Technologies:**
- React: https://react.dev/
- Vite: https://vitejs.dev/
- Tailwind CSS: https://tailwindcss.com/

**Backend Technologies:**
- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy: https://www.sqlalchemy.org/
- Uvicorn: https://www.uvicorn.org/

**Deployment:**
- AWS EC2: https://aws.amazon.com/ec2/
- Nginx: https://nginx.org/

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
- [ ] Video quality is professional (720p minimum)
- [ ] User can view, download, and delete videos
- [ ] Cost per video is <$2
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

## Document Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Nov 14, 2025 | Dev Team | Initial PRD creation |

---

## Approval & Sign-off

**Product Owner:** ___________________ Date: ___________

**Technical Lead:** ___________________ Date: ___________

**Stakeholder:** ___________________ Date: ___________

---

**END OF DOCUMENT**