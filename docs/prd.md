# ad-mint-ai - Product Requirements Document

**Author:** BMad
**Date:** 2025-11-22
**Version:** 1.0

---

## Executive Summary

Ad Mint AI is consolidating four separate video ad generation pipelines into a single, unified, best-in-class system that eliminates the false choice between visual consistency and user control. The unified pipeline combines Master Mode's industry-leading 3-reference-image consistency system with Interactive Mode's iterative feedback capabilities, Original Pipeline's quality scoring visibility, and CLI's headless execution—all in a flexible, configuration-driven architecture that works seamlessly via web UI or command line.

This is a brownfield consolidation project that transforms fragmented technical debt (4 separate codebases requiring 4x maintenance) into a cohesive competitive advantage: the only AI video ad platform where users get Master Mode-level character/product consistency while maintaining full creative control through feedback at every generation stage.

### What Makes This Special

**"Master Mode-level visual consistency combined with Interactive Mode's narrative control - the only AI video ad generator where users get professional visual coherence while iterating on story and scenes until they're perfect."**

Every existing AI video generator—including our own current pipelines—forces users into an impossible trade-off:

- **Choose Consistency:** Use Master Mode, get videos with characters/products that look the same across clips, but the story and scene narratives are fixed by AI. One shot - if you don't like the narrative arc, start completely over.

- **Choose Control:** Use Interactive Mode, refine the story and scenes iteratively, but get videos where characters morph between scenes and products change appearance—making the final output unusable for professional advertising.

The unified pipeline breaks this constraint by keeping Master Mode's sophisticated visual consistency system (3-reference-image approach with vision-enhanced AI for cross-clip coherence) while adding interactive control at the two most critical creative decision points: **story narrative** and **scene descriptions**. Users can iterate on what the ad says and shows while maintaining professional-grade visual consistency.

This isn't about feedback at every possible stage—it's about feedback at the stages that matter most for creative control, without sacrificing the technical sophistication that makes videos look professional.

---

## Project Classification

**Technical Type:** web_app
**Domain:** general (AI/ML SaaS)
**Complexity:** low regulatory requirements

This is a **brownfield enhancement project** consolidating four existing working pipelines:

1. **Master Mode Pipeline** - Best visual consistency (3-reference-image approach), complex multi-agent LLM system (5+ specialized agents), but completely hardcoded, inflexible, and lacks user interactivity. Cannot generate reference images—they must be provided.

2. **Interactive Pipeline** - Enables user feedback during story, reference image, and scene generation with conversational interface, but lacks cross-clip visual consistency mechanisms and has UI stability issues (WebSocket errors, state loss on navigation).

3. **Original Pipeline** - Has useful image/video quality scoring and parallel generation capabilities, but produces poor overall quality and is largely deprecated.

4. **CLI Tools** - Provides standalone command-line execution but is disconnected from web UI workflows.

**Consolidation Goal:** Single modular pipeline combining Master Mode's 3-reference-image consistency + Interactive Mode's user feedback + quality score displays + UI/CLI execution + image generation capability + flexible, configuration-driven architecture.

**Technical Context:**
- **Backend:** Python 3.11+, FastAPI 0.104+, SQLAlchemy 2.0+
- **Frontend:** React 19+, TypeScript 5.9+, Vite 5.4+, Tailwind CSS 3.4+, Zustand (state), React Router
- **Database:** PostgreSQL (production) / SQLite (development)
- **AI Services:** OpenAI GPT-4, Replicate (Nano Banana Pro for images, Veo 3 for videos)
- **Background Processing:** FastAPI BackgroundTasks for async operations (VBench scoring, video stitching)
- **WebSocket:** FastAPI native WebSocket for real-time bidirectional communication
- **Session Storage:** Redis for WebSocket session caching and state persistence
- **Testing:** pytest (backend), vitest (frontend)
- **Logging:** Python standard logging with structured format
- **Deployment:** AWS EC2 + RDS + S3 with Nginx reverse proxy

---

## Success Criteria

**The unified pipeline succeeds when users experience the "impossible combination" - Master Mode consistency with Interactive Mode control - and development velocity increases from eliminating 4-pipeline fragmentation.**

### User Experience Success

**1. The Consistency-Control Breakthrough**
- Users generate professional video ads with > 85% visual similarity for characters/products across all clips (Master Mode standard) WHILE providing iterative feedback at **story and scene narrative stages** (the two critical creative decision points)
- Zero forced trade-offs: users don't choose between visual consistency OR narrative control - they get both
- Confidence in final output: users trust that their brand assets will appear correctly and consistently, AND the story/scenes say exactly what they refined them to say

**2. Professional Quality with Iteration Speed**
- Complete generation cycle (initial prompt → final video) in < 10 minutes including user feedback loops
- Video quality scores > 80 on standardized benchmarks (VBench equivalent)
- Users can refine story/scenes without full regeneration - iteration adds seconds, not minutes
- Motion continuity without typical AI artifacts (no teleporting objects, no position resets between clips)

**3. Interface Flexibility Without Fragmentation**
- Power users execute full pipeline via CLI for automation/batch processing
- Mainstream users use ChatGPT-style web interface with zero learning curve
- Identical capabilities and output quality regardless of interface choice
- State persists across sessions - no WebSocket errors, no data loss on navigation

**4. Brand Asset Adaptability**
- Pipeline successfully generates professional ads whether user provides:
  - All brand assets (products, logo, character)
  - Some brand assets (generates missing ones maintaining style)
  - No brand assets (generates everything from prompt)
- Asset integration feels natural, not forced or inconsistent

### Development & Technical Success

**1. Consolidation Complete**
- Single codebase replaces all 4 pipelines (Master Mode, Interactive, Original, CLI)
- All original pipelines deprecated and removed
- Bug fixes and AI model updates deploy once, not 4 times
- Feature development velocity increases 3-4x without fragmentation overhead

**2. Code Quality & Maintainability**
- No hardcoded prompts or workflows - fully configuration-driven
- Modular pipeline stages (story → references → scenes → videos) independently testable
- Multi-agent orchestration (Director, Critic, Cohesor patterns) works in both interactive and automated modes
- Clear separation: API layer (routes) → Service layer (business logic) → Data layer (ORM)

**3. Zero Regression from Current Best**
- Output quality matches or exceeds current Master Mode (the quality benchmark)
- All critical features from all 4 pipelines available in unified version
- No performance degradation when adding interactivity to Master Mode approach

### Business Metrics

**Efficiency Gains:**
- Single pull request affects entire pipeline (vs. 4 separate updates)
- Testing complexity reduced: 1 workflow to validate (vs. 4 different workflows)
- Onboarding new developers: 1 codebase to learn (vs. navigating 4 systems)

**User Satisfaction Indicators:**
- 3-5 test users successfully generate professional-quality ads using unified pipeline
- Positive feedback on ChatGPT-style conversational interface
- Users prefer unified pipeline over choosing between fragmented options
- Users report "this is the first AI video tool where I don't have to compromise"

**Risk Mitigation:**
- No critical bugs in WebSocket/state management (current Interactive Mode issue)
- Brownfield migration complete without data loss (existing generations database intact)
- Fallback mechanisms if advanced features fail (graceful degradation)

---

## Product Scope

### MVP - Minimum Viable Product

**The unified pipeline MVP delivers the complete consistency-control breakthrough with single codebase consolidation:**

**Core Pipeline Integration:**
- Visual consistency system from Master Mode (3-reference-image input, vision-enhanced AI analysis, character/product/color/motion consistency tracking)
- Interactive feedback at 2 critical breakpoints from Interactive Mode (story review/refinement and scene narrative editing with conversational UI)
- Quality scoring from Original Pipeline (VBench for per-clip and overall video quality metrics - display only, no auto-regeneration loops in MVP)
- Dual execution from CLI Tools (full REST/WebSocket API for UI, complete CLI command set, headless backend execution)

**New Unified Capabilities:**
- Flexible brand input system (0-N product images, optional logo, 0-N character images, dynamic pipeline adaptation)
- Configuration-driven architecture (modular pipeline stages, configurable agent orchestration, no hardcoded prompts)
- Robust state management (reliable WebSocket with auto-reconnect, session persistence in database, navigation-safe state)
- Multi-agent LLM system (Director + Critic for story, Writer + Critic + Cohesor for scenes, vision analysis for references, works in interactive and automated modes)

**ChatGPT-Style Interface:**
- Dark background with grey chat box
- Sequential output display in chat feed
- System infers next step from user input (no mode buttons)
- **Interactive checkpoints at 2 stages: story narrative and scene descriptions**

**Reference Image Handling (MVP - Streamlined):**
- System uses 3-reference-image approach for visual consistency (Master Mode proven system)
- User can provide brand assets (products, logo, character images) which become/inform reference images
- If no brand assets provided, system auto-generates 3 reference images from story
- **No interactive feedback on reference images in MVP** - they're generated/selected automatically
- Reference image interactive refinement deferred to Growth phase (Phase 2)

**Performance Requirements:**
- End-to-end generation < 10 minutes (including user feedback loops)
- Video quality score > 80 on VBench
- Visual consistency > 85% across clips
- Zero motion artifacts (teleporting, position resets)

**Technical Deliverables:**
- All 4 original pipelines deprecated and removed
- Single unified codebase with modular architecture
- Database migration preserving existing generations
- Comprehensive test coverage

### Growth Features (Post-MVP)

**Interactive Reference Image Refinement (Phase 2):**
- User can review generated reference images and request regeneration
- User can upload custom reference images to replace auto-generated ones
- User can provide feedback on reference image quality before proceeding to scenes
- System displays reference image quality scores and consistency metrics
- Third interactive breakpoint added to pipeline (story → **references** → scenes)

**Enhanced Brand Customization (Phase 2):**
- Brand style guide parser (color palettes, fonts, design rules from uploaded style guide)
- Automatic brand compliance validation (verify output matches brand guidelines)
- Brand asset library management (store/version multiple product shots, characters, logos)
- Template library for common ad types (product demo, testimonial, explainer, announcement)

**Extended Video Formats (Phase 2):**
- Multi-aspect ratio support (16:9 landscape, 9:16 vertical TikTok/Reels, 1:1 square Instagram, 4:5 portrait)
- Variable length optimization (15s, 30s, 60s, 90s with content pacing adapted)
- Platform-specific optimization (TikTok, Instagram Reels, YouTube Shorts, Facebook, LinkedIn)

**Batch Processing & Automation (Phase 2):**
- Bulk video generation from CSV (multiple prompts/variations in one run)
- Scheduled generation jobs (generate at specific times, recurring campaigns)
- Campaign-level management (group related ads, track variants, compare performance)
- Webhook support for workflow automation

**Advanced A/B Testing (Phase 3):**
- Systematic variant generation (automatically create versions with different hooks, CTAs, pacing)
- Statistical significance testing (determine winning variants with confidence intervals)
- Performance tracking dashboard (view quality scores, generation metrics across variants)

**Team Collaboration (Phase 3):**
- Multi-user editing and approval workflows (assign review, request changes, approve)
- Comment/annotation system on generated content
- Version control and history (rollback to previous iterations)
- Role-based permissions (admin, creator, reviewer)

**Post-Generation Editing (Phase 3):**
- Built-in video editor (trim, cut, rearrange clips)
- Audio track customization (background music, voiceover, sound effects)
- Subtitle/caption generation (auto-transcribe, style, position)
- Export to multiple formats and resolutions

### Vision Features (Future)

**Creative Intelligence (Phase 4):**
- Automatic trend detection from social platforms (identify viral patterns, suggest trending styles)
- Style transfer from example videos (user uploads inspiration video, system replicates style)
- Competitive ad analysis (analyze competitor ads, suggest differentiation strategies)
- Performance prediction before generation (estimate engagement likelihood based on historical data)

**Platform Expansion (Phase 5):**
- Mobile app (iOS/Android native apps for on-the-go generation)
- Browser extensions (quick generation from any webpage, integrate with social platforms)
- Direct platform integration (publish to Meta Ads, Google Ads, TikTok Ads Manager from UI)
- Marketplace (user-created templates, brand packs, character libraries)

**Advanced AI Capabilities (Phase 5):**
- Multi-language support (generate ads in different languages, cultural adaptation)
- Voice cloning for consistent brand voice across ads
- Real-time video editing via natural language ("make the first scene faster", "add text overlay")
- Personalization engine (generate variants for different audience segments automatically)

---

## web_app Specific Requirements

### Application Architecture

**Type:** Single Page Application (SPA)
- React 19+ with TypeScript for type safety
- Vite 5.4+ for fast builds and hot module replacement
- Client-side routing for instant navigation
- Zustand for lightweight state management
- Real-time updates via WebSocket connections

**Justification for SPA:**
- Interactive pipeline requires real-time streaming updates (story generation, image generation progress, video rendering status)
- ChatGPT-style conversational interface needs instant message updates without page reloads
- State persistence critical for multi-stage pipeline (story → references → scenes → videos)
- No SEO requirements (authenticated app, not public content)

### Browser Support Matrix

**Primary Support (Full Testing):**
- Chrome/Edge 120+ (Chromium-based, primary development target)
- Firefox 120+
- Safari 17+ (macOS/iOS)

**Minimum Support (Basic Testing):**
- Chrome/Edge 115+
- Firefox 115+
- Safari 16+

**Not Supported:**
- Internet Explorer (deprecated)
- Browsers without WebSocket support
- Browsers without ES2020+ support

**Browser-Specific Considerations:**
- WebSocket reconnection logic tested across all primary browsers
- Video playback compatibility (MP4 H.264 baseline profile for maximum compatibility)
- File upload handling (drag-and-drop for brand assets works in all primary browsers)
- Canvas/blob handling for image display and download

### Responsive Design Requirements

**Target Devices:**
- **Desktop (Primary):** 1920x1080 and above, optimized for video editing/review workflows
- **Laptop:** 1366x768 minimum, full functionality maintained
- **Tablet:** 768px+ width, read-only mode for reviewing generated content (editing deferred to Growth phase)
- **Mobile:** < 768px, not supported in MVP (complex video generation UI not suitable for small screens)

**Layout Strategy:**
- Fluid layout with breakpoints at 1920px, 1366px, 1024px, 768px
- ChatGPT-style feed is responsive (stacks vertically on narrow screens)
- Video preview adapts to viewport (maintains aspect ratio, max-width constraints)
- Side-by-side comparisons (A/B testing) collapse to vertical stack on smaller screens

### Performance Targets

**Page Load:**
- Initial load < 2 seconds (on broadband connection)
- Time to interactive < 3 seconds
- Code splitting by route (lazy load Master Mode, Interactive, Gallery components)

**Real-Time Updates:**
- WebSocket message latency < 200ms (story/scene generation updates stream in near real-time)
- UI updates within 16ms of state change (60fps smooth scrolling in chat feed)
- Image preview rendering < 500ms after generation complete

**Asset Loading:**
- Generated images lazy-loaded (only render when in viewport)
- Video thumbnails prioritized over full video files
- S3 pre-signed URL generation < 100ms

**Memory Management:**
- No memory leaks during long generation sessions (2+ hours)
- WebSocket connection cleanup on component unmount
- Large video files stream rather than load entirely into memory

### SEO Strategy

**Not Applicable for MVP:**
- Authenticated application (login required for all generation features)
- No public content to index
- No marketing pages in current scope

**Future Consideration (Growth Phase):**
- Marketing landing page (publicly accessible)
- Gallery of example generated ads (public showcase)
- Blog/documentation (SEO-optimized content)

### Accessibility Level

**MVP Target: WCAG 2.1 Level A (Baseline Compliance)**

**Keyboard Navigation:**
- All interactive elements (buttons, inputs, chat interface) keyboard accessible
- Tab order follows logical flow (prompt input → generate button → results)
- Escape key closes modals/overlays

**Screen Reader Support:**
- Semantic HTML (proper heading hierarchy, landmarks, ARIA labels)
- Alt text for generated images (auto-generated descriptions from AI)
- Live regions announce generation progress ("Story generation complete", "Generating reference images")

**Visual Accessibility:**
- Minimum contrast ratio 4.5:1 for text (dark background, light grey text meets standard)
- Focus indicators on all interactive elements (visible outline on tab focus)
- No content that relies solely on color (error states use icons + color)

**Deferred to Post-MVP:**
- WCAG 2.1 Level AA compliance (higher contrast, larger click targets)
- Full screen reader optimization for complex video editing workflows
- Keyboard shortcuts for power users
- High contrast mode toggle

**Accessibility Testing:**
- Automated testing with axe-core (CI/CD integration)
- Manual keyboard navigation testing
- Basic screen reader testing with NVDA/JAWS (Windows) and VoiceOver (macOS)

---

## User Experience Principles

### Visual Personality

**"Professional Tools Aesthetic with ChatGPT-Style Simplicity"**

The unified pipeline interface should feel like a professional creative tool (confidence-inspiring, precision-focused) combined with the approachable simplicity of conversational AI interfaces.

**Design Direction:**
- **Color Palette:** Dark background (#1a1a1a or similar), grey chat containers (#2a2a2a), white/light grey text (#e0e0e0), accent color for generation status/CTAs (blue/purple)
- **Typography:** Clean sans-serif (Inter, SF Pro, or similar), clear hierarchy between user input and system responses
- **Spacing:** Generous whitespace in chat feed, comfortable reading line-length, breathing room around media assets
- **Tone:** Confident but not flashy, professional but not intimidating, powerful but not overwhelming

**Mood:**
- Users should feel: "This is a serious tool that respects my time and intelligence"
- NOT feel: "This is complicated and I need training" or "This is too casual for professional work"

### Key Interaction Patterns

**1. Conversational Generation Flow (ChatGPT-Style)**

**Pattern:** Linear chat interface where system guides user through pipeline stages

**Behavior:**
- User submits initial prompt in text input at bottom of screen
- System responds with story generation in chat bubble
- User provides feedback or approves ("looks good", "make it more dramatic", "regenerate")
- System infers intent from natural language (no explicit "Approve" buttons needed, though optional quick actions can exist)
- Conversation continues through reference images → scenes → final video
- All history visible in scrollable feed above

**Why This Matters:**
- Eliminates cognitive load of "what do I do next" - system guides naturally
- Feels familiar (ChatGPT, Claude) - zero learning curve
- Supports both power users (type specific commands) and casual users (conversational requests)

**2. Progressive Disclosure of Complexity**

**Pattern:** Simple by default, powerful when needed

**Behavior:**
- Default view: Clean chat interface with minimal controls (text input, send button, settings icon)
- Advanced options hidden behind settings: reference image upload, advertising framework selection, parallel generation count, quality thresholds
- In-context controls appear when relevant (e.g., "Upload your own reference images" option appears when system is about to generate them)

**Why This Matters:**
- New users aren't overwhelmed by options
- Power users can access advanced features without bloat
- Interface adapts to user expertise level over time

**3. Visual Feedback for Long-Running Operations**

**Pattern:** Clear progress indication for AI generation tasks

**Behavior:**
- Story generation: Streaming text appears in real-time (partial sentences as LLM generates)
- Image generation: Progress bar with stage indicator ("Analyzing prompt...", "Generating image 1 of 3...", "Enhancing quality...")
- Video generation: Per-clip progress with total pipeline progress ("Rendering scene 2/5", overall "45% complete")
- Quality scoring: Real-time metrics appear as scores are calculated

**Why This Matters:**
- Builds trust during long operations (up to 10 minutes total)
- Users understand what's happening, reducing anxiety
- Clear expectations prevent abandonment ("is this stuck?")

**4. Non-Destructive Iteration**

**Pattern:** Users can refine without losing previous versions

**Behavior:**
- Story refinement: User's feedback creates new version, previous visible in chat history
- Scene regeneration: User can regenerate single scene without affecting others, previous scene still accessible
- Reference images: User can request regeneration, previous images remain in chat feed for comparison
- Video generation: Parallel generation creates variants, all viewable side-by-side

**Why This Matters:**
- Encourages experimentation ("try different hooks" without fear of losing good version)
- Supports A/B testing mindset (compare variants)
- Reduces frustration from "I liked the previous version better"

**5. Inline Editing for Precision Control**

**Pattern:** Direct manipulation of generated content where appropriate

**Behavior:**
- Scene descriptions: Click to edit text directly, regenerate video with changes
- Reference image selection: Drag to reorder priority, click to remove/replace
- Brand asset upload: Drag-and-drop interface, preview before generation
- Quality threshold adjustment: Slider controls with live preview of impact

**Why This Matters:**
- Faster than conversational iteration for simple tweaks
- Tactile feedback (direct manipulation) feels responsive
- Balances conversational simplicity with power user efficiency

### Critical User Flows

**Flow 1: First-Time User - Zero to Video (MVP - 2 Interactive Breakpoints)**
1. User arrives at unified pipeline interface (ChatGPT-style empty state with prompt: "Describe the video ad you want to create...")
2. User types prompt ("Create a 30-second ad for my eco-friendly water bottle")
3. **BREAKPOINT 1 - Story:** System generates story, displays in chat bubble with quality score
4. User reads, provides feedback ("make it focus more on sustainability")
5. System refines story, shows updated version
6. User approves ("perfect, continue")
7. System auto-generates 3 reference images from approved story, displays in chat (read-only, no feedback in MVP)
8. System displays: "Using these reference images for visual consistency across all scenes"
9. **BREAKPOINT 2 - Scenes:** System generates scenes with detailed descriptions
10. User reviews scenes, edits one ("make scene 2 more dramatic - show person climbing mountain")
11. System regenerates scene 2 only, shows updated description
12. User approves all scenes ("looks great, generate videos")
13. System generates videos for **all 5 scenes in parallel** - progress bars show each clip simultaneously (Clip 1: 45%, Clip 2: 32%, Clip 3: 51%...)
14. As each clip completes, system displays it in chat feed with playback controls
15. **In background (non-blocking):** VBench scoring starts for each completed clip, scores stream in as available
16. After all clips complete, system stitches final video
17. **In background:** VBench calculates overall video score, displays when complete
18. User can download final video, individual clips, or start new generation while VBench finishes
19. Total time: < 10 minutes (parallel generation significantly faster than sequential)

**Flow 2: Power User - CLI with Brand Assets (MVP - 2 Interactive Breakpoints)**
1. User runs CLI command: `admint generate --prompt "Athletic shoe ad" --product-images ./assets/shoe-*.jpg --logo ./brand/logo.png --framework AIDA --interactive`
2. **BREAKPOINT 1 - Story:** CLI outputs story in terminal, prompts for approval
3. User provides feedback: "make it more energetic"
4. CLI outputs refined story
5. User types "approve"
6. CLI auto-generates 3 reference images using provided product images, displays URLs (read-only, no feedback in MVP)
7. CLI displays: "Using shoe-1.jpg, shoe-2.jpg, shoe-3.jpg as reference images for visual consistency"
8. **BREAKPOINT 2 - Scenes:** CLI generates scenes, displays descriptions with line numbers
9. User types "edit 3" and provides new description for scene 3
10. CLI regenerates scene 3 only, shows updated description
11. User types "approve"
12. CLI generates videos with progress bars showing per-clip completion
13. CLI outputs VBench scores for each clip as they complete
14. CLI stitches final video, outputs path and quality metrics JSON
15. Total time: < 10 minutes

**Flow 3: Parallel Generation - A/B Testing (MVP)**
1. User starts new session, types: "Generate 3 variants of eco-friendly water bottle ad with different hooks: fear-based, aspiration-based, and humor-based"
2. System creates 3 parallel pipeline executions simultaneously
3. For each variant:
   - Generates story with specified hook style
   - User approves or iterates on each story independently (Breakpoint 1)
   - System auto-generates reference images
   - System generates scenes
   - User reviews/edits scenes (Breakpoint 2)
   - System generates videos
4. System displays 3 final videos side-by-side with VBench scores for each
5. User compares quality scores (fear-based: 78, aspiration: 85, humor: 81)
6. User selects aspiration-based variant as winner
7. User optionally refines winning variant further or downloads immediately
8. Total time for 3 variants: ~25-30 minutes (parallelized)

**Connection to Product Differentiator (MVP - 2 Breakpoints):**
These UX patterns directly support the core value proposition:
- **Consistency:** Reference image system (Flow 1 steps 7-8) ensures Master Mode-level visual coherence across all clips
- **Narrative Control:** Interactive breakpoints at story and scenes (Flow 1 steps 3-6, 9-12) enable precise creative control
- **Flexibility:** CLI flow (Flow 2) and UI flow (Flow 1) deliver identical capabilities with 2 breakpoints
- **Professional Quality:** VBench scores displayed for transparency, user decides if quality is acceptable
- **Parallel Generation:** Flow 3 shows A/B testing with same/different prompts running simultaneously

---

## Functional Requirements

**This section defines WHAT capabilities the unified pipeline must have. These are the complete inventory of user-facing and system capabilities that deliver the product vision.**

**Coverage Note:** Every capability mentioned in vision, scope, domain requirements, and project-specific sections is represented below. Missing FRs = missing capabilities.

### User Account & Authentication

- FR1: Users can create accounts with email and password
- FR2: Users can log in securely and maintain authenticated sessions
- FR3: Users can reset passwords via email verification
- FR4: Users can update profile information and preferences
- FR5: System maintains user session state across browser sessions
- FR6: System supports API token authentication for CLI access

### Video Ad Generation Pipeline

**Story Generation:**
- FR7: Users can submit text prompts describing desired video ad
- FR8: System generates advertising stories using multi-agent LLM system (Director + Critic)
- FR9: Users can select advertising framework (AIDA, PAS, FAB, or custom)
- FR10: Users can provide iterative feedback to refine story
- FR11: System streams story generation progress in real-time
- FR12: Users can view story quality scores as generation completes
- FR13: Users can approve story to proceed to next stage or request regeneration

**Reference Image Management (MVP - Streamlined, No Interactive Feedback):**
- FR14: System generates 3 reference images for visual consistency when not provided by user
- FR15: System analyzes reference images using vision-enhanced AI to extract visual characteristics
- FR16: System validates reference image quality before proceeding to scene generation
- FR17: System maintains reference image context throughout generation for character/product consistency
- FR18: System displays generated reference images in chat feed for user awareness (read-only in MVP)

**Note:** Interactive reference image refinement (review, regenerate, upload custom, reorder) deferred to Phase 2 Growth features

**Brand Asset Integration:**
- FR19: Users can upload brand product images (0-N reference shots)
- FR20: Users can upload brand logo
- FR21: Users can upload brand character/mascot images (0-N reference shots)
- FR22: System uses uploaded brand assets to inform/become the 3 reference images
- FR23: System generates reference images from story when no brand assets provided
- FR24: System integrates brand assets into reference image set for visual coherence
- FR25: System displays which brand assets are being used as references in chat feed

**Scene Generation:**
- FR26: System generates detailed scene descriptions using multi-agent LLM system (Writer + Critic + Cohesor)
- FR27: System ensures cross-scene consistency for characters, products, colors, and actions
- FR28: Users can view all generated scenes with descriptions
- FR29: Users can edit individual scene descriptions directly in chat interface
- FR30: Users can request regeneration of specific scenes without affecting others
- FR31: Users can approve all scenes or iterate on specific scenes
- FR32: System validates scene coherence before video generation
- FR33: System displays scene quality scores

**Video Generation & Stitching:**
- FR34: System generates video clips for all approved scenes **in parallel** using AI video models (Veo 3 via Replicate)
- FR35: System displays per-clip generation progress with stage indicators showing parallel execution status
- FR36: System ensures motion continuity across clips (no teleporting artifacts, position consistency)
- FR37: System stitches individual scene videos into final coherent advertisement after all clips complete
- FR38: Users can download final stitched video
- FR39: Users can download individual scene videos

**Quality Scoring (Background, Non-Blocking):**
- FR40: System calculates VBench quality score for each video clip **in background after video completes**
- FR41: System calculates overall VBench quality score for final stitched video **in background**
- FR42: VBench scoring runs asynchronously without blocking webapp interactivity or video generation
- FR43: System displays per-clip and overall video quality metrics in chat feed as they become available (streaming updates)
- FR44: Users can interact with webapp (navigate, start new generation) while VBench scoring runs in background

**Parallel Generation & A/B Testing:**
- FR45: Users can request parallel generation of multiple video variants from same prompt (different hooks, pacing, frameworks)
- FR46: Users can request parallel generation from different prompts simultaneously
- FR47: System generates 2+ variants in parallel with independent pipeline execution
- FR48: Users can view variants side-by-side for comparison
- FR49: Users can view quality scores for each variant (as VBench completes in background)
- FR50: Users can select winning variant for further iteration or download

**Configuration & Advanced Options:**
- FR51: Users can configure quality display thresholds (visual indicators for good/poor scores)
- FR52: Users can configure iteration limits (max refinement attempts per stage)
- FR53: Users can enable/disable specific pipeline stages
- FR54: Users can select advertising frameworks (AIDA, PAS, FAB) or provide custom framework descriptions
- FR55: System supports configuration via UI settings and CLI parameters
- FR56: System validates configuration before pipeline execution

### Interactive Conversational Interface (UI)

**Chat-Style Interaction:**
- FR57: Users interact with pipeline through ChatGPT-style conversational interface
- FR58: System displays all pipeline stages and outputs in scrollable chat feed
- FR59: Users provide feedback and commands via natural language text input at 2 interactive breakpoints (story and scenes)
- FR60: System infers user intent from conversational input (approve, refine, regenerate, edit)
- FR61: System provides optional quick action buttons for common operations (approve, regenerate, edit)
- FR62: System maintains conversation history for entire generation session
- FR63: Users can scroll through history to review previous stages

**Progress & Feedback (Non-Blocking UI Updates):**
- FR64: System streams real-time text generation (partial sentences appear as LLM generates)
- FR65: System displays progress bars for long-running operations (reference image generation, parallel video rendering)
- FR66: System announces stage completion with clear indicators ("Story approved, generating reference images...")
- FR67: System displays quality scores inline as they become available (VBench scores stream in as background processing completes)
- FR68: System provides estimated time remaining for parallel video generation
- FR69: UI remains fully interactive during all background operations (video generation, VBench scoring)

**Media Display:**
- FR70: System displays generated reference images inline in chat feed (read-only in MVP)
- FR71: System displays video previews with playback controls as each clip completes (parallel generation updates)
- FR72: Users can click images/videos for full-screen preview
- FR73: System lazy-loads media assets for performance
- FR74: System displays image alt-text and video descriptions for accessibility

**State Management (Non-Blocking):**
- FR75: System persists generation session state to database asynchronously (no UI blocking)
- FR76: Users can navigate away from pipeline and return without losing progress
- FR77: System maintains WebSocket connection with auto-reconnect on disconnect
- FR78: System recovers gracefully from WebSocket errors without data loss
- FR79: Users can pause generation session and resume later
- FR80: System displays session restoration indicator when resuming
- FR81: Background processes (VBench scoring) continue even when user navigates to other pages

### Command-Line Interface (CLI)

**CLI Execution:**
- FR82: Users can execute full pipeline via CLI command with all UI capabilities
- FR83: CLI accepts text prompts, brand asset paths, and configuration parameters
- FR84: CLI displays generation progress in terminal with progress bars (shows parallel clip generation status)
- FR85: CLI outputs generated content (story text, reference image URLs, video paths)
- FR86: CLI supports interactive mode (prompts for approval at story and scene stages)
- FR87: CLI supports automated mode (runs entire pipeline without user input)
- FR88: CLI outputs quality metrics and scores as JSON (VBench per-clip and overall, as background scoring completes)
- FR89: CLI supports all configuration options available in UI

**CLI Advanced Features:**
- FR90: CLI supports batch processing from input files (CSV with multiple prompts)
- FR91: CLI supports parallel generation (multiple prompts simultaneously, each with parallel clip generation)
- FR92: CLI supports custom output directories
- FR93: CLI supports logging levels (verbose, normal, quiet)
- FR94: CLI displays error messages and troubleshooting guidance
- FR95: CLI supports authentication via API tokens
- FR96: CLI provides help documentation for all commands
- FR97: CLI can poll for background process completion (VBench scoring) and stream results as available

### Quality Metrics & Scoring (Background Processing, Display Only)

- FR98: System calculates VBench quality score for each generated video clip **in background worker process**
- FR99: System calculates overall VBench quality score for final stitched video **in background worker process**
- FR100: System displays quality scores in real-time in chat feed as background processing completes (streaming updates)
- FR101: Users can view detailed quality breakdowns (composition, coherence, motion, visual appeal, overall score)
- FR102: System stores quality metrics in database for historical analysis and comparison
- FR103: Quality scores displayed as visual indicators (color-coded: green > 80, yellow 60-80, red < 60)
- FR104: VBench processes run in FastAPI BackgroundTasks (separate thread pool) to avoid blocking main application

**Note:** Automatic regeneration based on quality thresholds deferred to Phase 2. In MVP, quality scores are informational only - user decides whether to regenerate manually.

### Content Management & Library

**Generation History:**
- FR105: Users can view all previous generation sessions
- FR106: Users can filter generations by date, quality score, or status
- FR107: Users can search generations by prompt text or tags
- FR108: Users can favorite/bookmark specific generations
- FR109: Users can delete unwanted generations
- FR110: System displays thumbnails and metadata for each generation

**Asset Library:**
- FR111: Users can save brand assets to library for reuse
- FR112: Users can organize brand assets with tags and labels
- FR113: Users can view all saved brand assets (products, logos, characters)
- FR114: Users can select brand assets from library when starting new generation
- FR115: System tracks usage of brand assets across generations

**Export & Download:**
- FR116: Users can download final videos in multiple formats (MP4)
- FR117: Users can download individual scene videos separately
- FR118: Users can download reference images
- FR119: Users can download story text and scene descriptions
- FR120: Users can export generation metadata (prompts, settings, quality scores) as JSON
- FR121: System generates pre-signed download URLs with expiration

### System Administration

- FR122: Administrators can view system usage metrics (generations per day, user activity, background task status)
- FR123: Administrators can view AI service costs and usage (OpenAI, Replicate)
- FR124: Administrators can configure global quality thresholds
- FR125: Administrators can enable/disable specific AI models or services
- FR126: Administrators can view error logs and failed generations
- FR127: System tracks and reports API errors for monitoring
- FR128: Administrators can monitor background task execution (VBench processing status, task completion rates)

### Error Handling & Recovery

- FR129: System displays user-friendly error messages for all failure scenarios
- FR130: System provides recovery options when generation fails (retry, adjust parameters, cancel)
- FR131: System logs all errors for debugging and monitoring
- FR132: System gracefully degrades when optional features fail (e.g., skip VBench scoring if worker unavailable, continue without scores)
- FR133: System prevents data loss during errors (auto-save progress, persist state before background operations)
- FR134: Users can view error details for troubleshooting
- FR135: Background task failures do not crash main application or block user interactions

---

## Non-Functional Requirements

**These NFRs are critical for the unified pipeline's value proposition: professional quality, iterative speed, and reliability.**

### Performance

**Why Performance Matters:**
The < 10 minute end-to-end generation time (including user feedback) is a core success criterion and competitive differentiator. Slow generation kills the iterative refinement experience.

**Requirements:**

- **NFR-P1: Total Generation Time < 10 Minutes**
  - Complete pipeline execution from initial prompt to final stitched video must complete in under 10 minutes, including user feedback loops
  - Measured as 95th percentile across all generations
  - Budget allocation: Story generation 1-2 min, reference images 1-2 min, scene generation 2-3 min, video generation 4-5 min
  - Does not include user think time between stages

- **NFR-P2: Real-Time Streaming Latency < 200ms**
  - WebSocket message delivery from backend to frontend must complete within 200ms
  - Story text streaming must show partial content as LLM generates (character-by-character or sentence-by-sentence)
  - Progress updates must stream in near real-time (no multi-second batching)

- **NFR-P3: UI Responsiveness - 60fps**
  - UI updates must occur within 16ms of state change (60 frames per second)
  - Scrolling in chat feed must be smooth without jank
  - Video preview scrubbing must respond instantly to user input

- **NFR-P4: Page Load Time < 3 Seconds**
  - Initial page load to interactive must complete within 3 seconds on broadband connection (25 Mbps+)
  - Time to First Contentful Paint < 1.5 seconds
  - Code splitting by route to reduce initial bundle size

- **NFR-P5: API Response Time < 500ms (P95)**
  - 95th percentile API response time for non-generation endpoints must be under 500ms
  - Includes authentication, configuration retrieval, generation history queries
  - Excludes long-running generation operations (separate timeout requirements)

- **NFR-P6: Memory Efficiency**
  - No memory leaks during extended generation sessions (2+ hours of continuous use)
  - Frontend memory usage must remain under 500MB for typical session (5-10 generations)
  - Backend memory usage per concurrent generation session must remain under 1GB

- **NFR-P7: Asset Loading Performance**
  - Generated images must render in viewport within 500ms of generation completion
  - Video thumbnails must load before full video files (progressive loading)
  - S3 pre-signed URL generation must complete in under 100ms

- **NFR-P8: Parallel Video Generation**
  - System must generate all scene video clips in parallel (not sequential)
  - Support for 3-10 parallel video generation requests to Replicate API simultaneously
  - UI displays progress for all parallel clips with individual progress indicators
  - Total video generation time should approach longest single clip time (not sum of all clips)

- **NFR-P9: Non-Blocking Background Processing**
  - VBench quality scoring must run in FastAPI BackgroundTasks after video generation completes
  - Background tasks must not block main application thread or WebSocket connections
  - UI must remain fully responsive during VBench scoring (can navigate, start new generations)
  - Background task failures must not crash main application (graceful error handling)
  - Background tasks for VBench scoring and video stitching operations
  - Note: BackgroundTasks run in separate thread pool, suitable for I/O-bound and moderate CPU tasks

### Security

**Why Security Matters:**
Handling user-generated content, API keys for expensive AI services (OpenAI, Replicate), user authentication data, and brand assets requires robust security to prevent unauthorized access and cost abuse.

**Requirements:**

- **NFR-S1: Authentication & Authorization**
  - All API endpoints except public marketing pages must require authentication
  - Session tokens must expire after 30 days of inactivity
  - API tokens for CLI must be revocable by user
  - Password reset tokens must expire after 1 hour and be single-use
  - Passwords must be hashed with bcrypt (12+ rounds)

- **NFR-S2: API Key Protection**
  - OpenAI and Replicate API keys must be stored as environment variables, never in code or database
  - API keys must never be exposed to frontend (all AI service calls from backend only)
  - API usage must be rate-limited per user to prevent abuse and cost overruns
  - API errors must not leak sensitive information in error messages

- **NFR-S3: Input Validation**
  - All user inputs (prompts, file uploads, configuration parameters) must be validated and sanitized
  - File uploads must validate file type, size, and scan for malware before processing
  - Maximum prompt length: 5000 characters
  - Maximum file upload size: 10MB per file, 50MB total per generation

- **NFR-S4: Data Privacy**
  - User-generated content (prompts, videos, brand assets) must be private by default (not publicly accessible)
  - S3 pre-signed URLs must expire after 24 hours
  - Users must be able to delete all their data (GDPR compliance)
  - Database must not log sensitive information (passwords, API keys)

- **NFR-S5: HTTPS & Transport Security**
  - All communication must use HTTPS with valid TLS certificates
  - WebSocket connections must use WSS (WebSocket Secure)
  - No mixed content warnings in browser
  - HSTS headers enabled for production deployment

- **NFR-S6: Rate Limiting**
  - API endpoints must implement rate limiting to prevent abuse
  - Generation endpoints: 10 generations per hour per user (configurable)
  - Authentication endpoints: 5 attempts per 15 minutes per IP
  - Rate limit errors must return 429 status with retry-after header

### Scalability

**Why Scalability Matters:**
While MVP targets solo entrepreneurs and small teams (not massive scale), the system must handle growth to hundreds of concurrent users and thousands of daily generations without architectural rewrites.

**Requirements:**

- **NFR-SC1: Concurrent Generation Sessions**
  - System must support 50+ concurrent video generation sessions without degradation
  - Each session represents independent user generating video ad with all pipeline stages
  - Backend must handle concurrent AI API calls (OpenAI, Replicate) with appropriate queueing

- **NFR-SC2: Database Scalability**
  - Database schema must support 100,000+ generation records without query performance degradation
  - Queries for generation history must use indexes (response time < 500ms)
  - Database must support connection pooling for concurrent requests
  - Migration path to PostgreSQL for production (SQLite adequate for development)

- **NFR-SC3: Storage Scalability**
  - S3 storage must support unlimited video/image assets (no hard limits in application)
  - Asset cleanup must run periodically to delete expired pre-signed URL content
  - Storage costs must be monitored and alerts configured for unusual growth

- **NFR-SC4: Horizontal Scaling Readiness**
  - Backend API must be stateless (all state in database or S3)
  - No in-memory session storage (use database or Redis if needed)
  - WebSocket connections must support reconnection to different backend instances
  - Architecture must support load balancing across multiple backend instances (deferred to post-MVP but designed for)

- **NFR-SC5: API Service Limits**
  - System must handle OpenAI rate limits gracefully (queue requests, retry with exponential backoff)
  - System must handle Replicate concurrent generation limits (currently limited by service)
  - System must alert administrators when approaching API quota limits

### Accessibility

**Why Accessibility Matters:**
Legal compliance (especially for B2B customers with accessibility requirements) and inclusive design for users with disabilities.

**Requirements:**

- **NFR-A1: WCAG 2.1 Level A Compliance (MVP Target)**
  - All interactive elements must be keyboard accessible (tab navigation, enter/space activation)
  - Tab order must follow logical content flow
  - Semantic HTML with proper heading hierarchy (h1 → h2 → h3)
  - ARIA labels for screen reader support
  - Minimum color contrast ratio 4.5:1 for normal text, 3:1 for large text

- **NFR-A2: Screen Reader Support**
  - Generated images must have descriptive alt text (auto-generated from AI descriptions)
  - Video content must have descriptive labels
  - Live regions must announce generation progress updates
  - Form inputs must have associated labels
  - Error messages must be announced to screen readers

- **NFR-A3: Keyboard Navigation**
  - All functionality must be accessible via keyboard (no mouse-only interactions)
  - Escape key must close modals and overlays
  - Focus indicators must be visible (outline on focused elements)
  - Keyboard shortcuts must not conflict with browser or assistive technology shortcuts

- **NFR-A4: Visual Accessibility**
  - No content that relies solely on color to convey information (use icons + color for error states)
  - Text must be resizable up to 200% without loss of functionality
  - Dark theme default must meet contrast requirements
  - Focus states must be clearly visible

- **NFR-A5: Automated Accessibility Testing**
  - CI/CD pipeline must include axe-core automated accessibility testing
  - Pull requests must pass accessibility checks before merge
  - Manual keyboard navigation testing for critical flows
  - Screen reader testing with NVDA (Windows) and VoiceOver (macOS) for major releases

**Deferred to Post-MVP:**
- WCAG 2.1 Level AA compliance (higher standards)
- Custom keyboard shortcuts for power users
- High contrast mode toggle
- Full screen reader optimization for complex video editing workflows

### Integration & Reliability

**Why Integration Matters:**
The unified pipeline depends on external AI services (OpenAI, Replicate) and cloud storage (S3). Service reliability and graceful degradation are critical.

**Requirements:**

- **NFR-I1: Third-Party Service Integration**
  - System must integrate with OpenAI API (GPT-4 for story/scene generation)
  - System must integrate with Replicate API (Nano Banana Pro for images, Veo 3 for videos)
  - System must integrate with AWS S3 (video/image storage)
  - All integrations must have timeout configurations (30 seconds for API calls, 10 minutes for video generation)

- **NFR-I2: Graceful Degradation**
  - If quality scoring service fails, generation must continue without scores (log warning, proceed)
  - If WebSocket connection fails, system must fall back to polling for updates
  - If S3 upload fails, system must retry up to 3 times with exponential backoff
  - If AI service returns error, system must display user-friendly message with retry option

- **NFR-I3: Retry & Error Handling**
  - Transient failures (network timeouts, 5xx errors) must be retried automatically (3 attempts with exponential backoff)
  - Permanent failures (4xx errors, invalid API keys) must fail immediately with clear error message
  - AI generation failures must allow user to retry with adjusted parameters
  - System must log all errors for monitoring and debugging

- **NFR-I4: Monitoring & Observability**
  - **Python standard logging** for all application logging with configurable levels
  - System must log all API calls with latency metrics (including background task start/completion)
  - System must track generation success/failure rates
  - System must alert on API error rate > 5%
  - System must track AI service costs per generation
  - System must provide health check endpoint for monitoring (includes background task queue status)
  - Structured logging format for easy parsing and analysis
  - Background task failures logged with full context for debugging

- **NFR-I5: Uptime & Availability**
  - Target 99% uptime for MVP (allows ~7 hours downtime per month)
  - Planned maintenance must be scheduled during low-usage periods
  - Database backups must run daily with 30-day retention
  - Critical errors must alert administrators immediately

### Maintainability & Code Quality

**Why Maintainability Matters:**
The core value proposition is consolidating 4 codebases into 1 maintainable system. Poor code quality would recreate the fragmentation problem.

**Requirements:**

- **NFR-M1: Configuration-Driven Architecture**
  - No hardcoded prompts or workflows in application code
  - All LLM prompts must be externalizable to configuration files
  - Pipeline stages must be configurable (enable/disable, reorder)
  - Quality thresholds, iteration limits, timeouts must be configurable

- **NFR-M2: Modular Architecture**
  - Clear separation: API layer (routes) → Service layer (business logic) → Data layer (ORM)
  - Pipeline stages (story, references, scenes, videos) must be independently testable modules
  - Multi-agent system (Director, Critic, Writer, Cohesor) must be composable and reusable
  - No circular dependencies between modules

- **NFR-M3: Test Coverage**
  - Unit test coverage > 70% for business logic (service layer)
  - **pytest** for all backend testing (unit, integration, API tests)
  - **vitest** for frontend component and integration testing
  - Integration tests for critical flows (end-to-end generation pipeline)
  - API endpoint tests for all routes
  - Frontend component tests for critical UI (chat interface, video preview, real-time updates)

- **NFR-M4: Code Standards**
  - Backend: Python type hints, PEP 8 style, linting with Ruff or Black
  - Frontend: TypeScript strict mode, ESLint rules enforced, Prettier formatting
  - No warnings in CI/CD pipeline
  - Code reviews required for all changes

- **NFR-M5: Documentation**
  - API endpoints documented with OpenAPI/Swagger
  - Service layer functions have docstrings explaining purpose, parameters, return values
  - README with setup instructions, architecture overview, deployment guide
  - Inline comments for complex business logic

- **NFR-M6: Asynchronous Architecture**
  - Clear separation between synchronous API handlers and asynchronous background tasks
  - **FastAPI BackgroundTasks** for background job processing (VBench scoring, video stitching)
  - Background tasks for CPU-intensive operations run after HTTP response sent
  - Parallel execution framework for video generation (asyncio for concurrent Replicate API calls)
  - **FastAPI native WebSocket** for real-time communication with async/await patterns
  - **Redis** for WebSocket session storage and state caching
  - All long-running operations (> 5 seconds) must use BackgroundTasks, not block request handlers
  - Note: Can migrate to Celery/RQ post-MVP if task persistence/retry becomes critical requirement

### Browser Compatibility

**Why Browser Compatibility Matters:**
Users access web app from variety of browsers and versions. Core functionality must work consistently across primary browsers.

**Requirements:**

- **NFR-B1: Primary Browser Support (Full Testing)**
  - Chrome/Edge 120+ (Chromium-based, primary development target)
  - Firefox 120+
  - Safari 17+ (macOS and iOS)
  - All features must work identically in primary browsers

- **NFR-B2: Minimum Browser Support (Basic Testing)**
  - Chrome/Edge 115+
  - Firefox 115+
  - Safari 16+
  - Core functionality must work, minor visual inconsistencies acceptable

- **NFR-B3: Not Supported**
  - Internet Explorer (deprecated)
  - Browsers without WebSocket support
  - Browsers without ES2020+ JavaScript support

- **NFR-B4: Cross-Browser Testing**
  - Automated cross-browser testing in CI/CD (Playwright or similar)
  - Manual testing in all primary browsers before release
  - WebSocket reconnection tested across all primary browsers
  - Video playback compatibility ensured (MP4 H.264 baseline profile)

---

_This PRD captures the essence of ad-mint-ai - **the only AI video ad platform where users get Master Mode-level visual consistency combined with Interactive Mode's narrative control at the two most critical creative decision points: story and scenes.**_

_Created through collaborative discovery between BMad and AI facilitator._

---

## PRD Summary

**Requirements Captured:**
- **135 Functional Requirements** organized across 9 capability areas
- **39 Non-Functional Requirements** across 7 quality dimensions

**Key Highlights:**

**What Makes This Special (MVP - Simplified Scope):**
The unified pipeline solves the fundamental UX problem plaguing AI video tools - forcing users to choose between visual consistency OR narrative control. By combining Master Mode's proven 3-reference-image system with Interactive Mode's conversational feedback flow at **2 critical breakpoints** (story and scene descriptions), users get both professional-grade visual coherence and creative control over what the ad says and shows.

**Core Value Delivered (MVP):**
1. **Consistency-Narrative Control Breakthrough** - 85%+ visual similarity WITH iterative feedback at story and scene stages (the 2 creative decision points that matter most)
2. **Consolidation Complete** - Single codebase replacing 4 fragmented pipelines, 3-4x velocity increase
3. **Professional Quality** - < 10 minute generation, VBench scores > 80, zero motion artifacts
4. **Dual Interface** - Full capabilities via web UI (ChatGPT-style) AND CLI (power users) with identical 2-breakpoint flow
5. **Flexible Brand Integration** - Works with all, some, or no brand assets provided (become/inform reference images)
6. **Parallel Generation** - A/B testing with same or different prompts running simultaneously

**MVP Scope Simplifications:**
- **Reference images: Auto-generated, no interactive feedback** (deferred to Phase 2) - keeps Master Mode's proven consistency system
- **Quality scoring: Display only, no auto-regeneration** (deferred to Phase 2) - VBench scores shown for transparency, user decides
- **2 interactive breakpoints only:** Story narrative and Scene descriptions - the stages where creative control matters most

**Critical Technical Architecture:**
- **Parallel video clip generation:** All scene videos generate simultaneously (not sequential) - total time = longest clip, not sum
- **Background VBench processing:** Quality scoring runs in worker threads without blocking webapp interactivity
- **Non-blocking UI:** Users can navigate, start new generations while VBench scoring and video generation continue in background
- **Task queue architecture:** Long-running operations (VBench, video stitching) handled by background workers with retry logic

**MVP Success When:**
- Users generate professional video ads with > 85% visual consistency while iterating on story and scenes until perfect
- All 4 original pipelines deprecated, single unified codebase operational
- UI and CLI deliver identical 2-breakpoint capabilities with zero WebSocket/state bugs
- Development velocity increases 3-4x from eliminating 4-pipeline maintenance overhead
- VBench scores displayed for all videos (per-clip and overall), giving users quality visibility

**Next Steps:**
Based on the BMad Method workflow path, recommended sequence:

1. **UX Design** (`/bmad:bmm:workflows:create-design`) - Design ChatGPT-style conversational interface, pipeline stage visualizations, and brand asset upload flows
2. **Architecture** (`/bmad:bmm:workflows:architecture`) - Define unified pipeline architecture, multi-agent orchestration, configuration system, and API contracts
3. **Epic Breakdown** (`/bmad:bmm:workflows:create-epics-and-stories`) - Transform 127 FRs into implementable epics and stories with full UX/Architecture context

**Recommendation:** Complete UX Design and Architecture before Epic Breakdown to ensure implementation stories have full context for technical decisions and interaction patterns.

---
