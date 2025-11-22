# Epic: Interactive Video Generation Pipeline

**Author:** BMad
**Date:** 2025-11-19
**Epic Slug:** interactive-pipeline
**Status:** Draft
**Total Stories:** 4
**Total Points:** 10

---

## Epic Goal

Enable professional content creators to have complete control over the video generation pipeline by adding human-in-the-loop feedback at each stage (story, reference images, storyboard), with conversational refinement and advanced image editing capabilities.

**User Value:**
- Reduce wasted API costs by allowing users to catch and fix issues early
- Increase user satisfaction through creative control at each stage
- Improve final video quality through iterative refinement
- Provide professional-grade workflow similar to industry tools

**Business Impact:**
- Competitive differentiation vs. fully automated tools
- Higher user retention through better UX
- Lower support costs (users can self-correct instead of requesting refunds)
- Enables premium pricing tier for interactive mode

---

## Epic Scope

**In Scope:**
- Interactive story generation with conversational feedback
- Interactive reference image generation with chat interface
- Interactive storyboard generation with chat interface
- Advanced image editing using inpainting (object selection/replacement)
- WebSocket-based real-time chat with LLM
- Session state management for pause/resume functionality
- Reorganization of Epic 8-9 CLI tools for better code organization

**Out of Scope:**
- Video editing in the interactive pipeline (Epic 6)
- Automated quality scoring at each stage (Epic 7)
- Multi-user collaboration features
- Saving draft states mid-pipeline (future enhancement)
- Advanced video inpainting (too computationally expensive)
- Integration between CLI tools and web pipeline

---

## Epic Success Criteria

1. ✅ Users can start an interactive pipeline and review AI-generated story before proceeding
2. ✅ Users can provide conversational feedback ("make it funnier") and see story regenerate
3. ✅ Users can review reference images and request changes before storyboard generation
4. ✅ Users can edit images using inpainting to replace specific objects/characters
5. ✅ WebSocket chat maintains connection and auto-reconnects on failure
6. ✅ Session state persists across page refreshes (within TTL)
7. ✅ Full pipeline completion rate > 70% (users who start complete all stages)
8. ✅ User satisfaction score > 4.5/5 for interactive mode vs. 3.5/5 for automated mode

---

## Dependencies

**Technical Dependencies:**
- Redis 7.x for session state management
- Replicate SDXL-inpaint model for image editing
- OpenAI GPT-4 for conversational feedback processing
- Existing pipeline services (story_generator, image_generation, storyboard_generator)

**Prerequisite Work:**
- Epics 1-5 completed (foundation, auth, pipeline, gallery, profile)
- Epic 7 pipeline services available (prompt enhancement, quality control)
- Epic 8-9 CLI tools implemented (provides feedback loop patterns to reuse)

**External Dependencies:**
- No new external API integrations (reuses OpenAI, Replicate)
- Redis instance must be provisioned for production deployment

---

## Story Map

```
Epic: Interactive Video Generation Pipeline (10 points)
│
├── Story 1: CLI Tools Organization (1 point)
│   Goal: Move Epic 8-9 CLI tools to separate directory
│   Dependencies: None
│   Output: backend/cli_tools/ directory with organized CLI scripts
│
├── Story 2: Interactive Story Generation (3 points)
│   Goal: Add conversational feedback for story generation stage
│   Dependencies: Story 1 (organizational cleanup)
│   Output: Working story review UI with chat, WebSocket backend
│
├── Story 3: Interactive Image/Storyboard Feedback (3 points)
│   Goal: Add conversational feedback for image and storyboard stages
│   Dependencies: Story 2 (chat infrastructure in place)
│   Output: Image review UI with chat for both reference and storyboard
│
└── Story 4: Advanced Image Editing (3 points)
    Goal: Add inpainting for object-level image editing
    Dependencies: Story 3 (image review UI exists)
    Output: Image editor with selection tools and inpainting
```

---

## Implementation Sequence

**Phase 1: Preparation (Story 1)**
- Reorganize CLI tools to avoid confusion with web pipeline code
- **Outcome:** Clean separation between development tools and production code

**Phase 2: Core Interactive Infrastructure (Story 2)**
- Build WebSocket communication layer
- Implement session state management
- Create chat interface and story review UI
- Integrate conversational feedback with story generation
- **Outcome:** Working interactive story generation with chat

**Phase 3: Extend to Images (Story 3)**
- Apply interactive pattern to reference images and storyboard
- Reuse chat interface from Story 2
- Handle batch feedback for multiple images
- **Outcome:** Complete interactive pipeline for all stages except video

**Phase 4: Advanced Editing (Story 4)**
- Add inpainting service backend
- Build image editor UI with selection tools
- Integrate SDXL-inpaint model
- **Outcome:** Professional-grade image editing capability

---

## Story Summaries

### Story 1: CLI Tools Organization (1 point)

**As a** developer
**I want** Epic 8-9 CLI tools organized in a separate directory
**So that** they don't get confused with main web application pipeline code

**Key Tasks:**
- Create `backend/cli_tools/` directory
- Move all CLI scripts from Epic 8-9
- Update documentation
- Verify CLI tools still work

**Acceptance Criteria:**
- All CLI tools located in `backend/cli_tools/`
- CLI tools execute successfully: `python cli_tools/enhance_image_prompt.py --help`
- README documents each CLI tool's purpose and usage

### Story 2: Interactive Story Generation (3 points)

**As a** content creator
**I want** to review and refine the AI-generated story through conversation
**So that** I can ensure the narrative matches my vision before spending credits on image generation

**Key Tasks:**
- Backend: Build interactive pipeline orchestrator with pause points
- Backend: Implement WebSocket endpoints for real-time chat
- Backend: Create conversation handler for feedback processing
- Frontend: Build story review UI component
- Frontend: Integrate reusable chat interface
- Testing: End-to-end story generation → feedback → regeneration → approval

**Acceptance Criteria:**
- User can start pipeline and see generated story
- Chat interface allows conversational feedback
- Story regenerates based on feedback
- User can approve to proceed to next stage
- WebSocket reconnects automatically on disconnect

### Story 3: Interactive Image/Storyboard Feedback (3 points)

**As a** content creator
**I want** to review and refine reference images and storyboard images through conversation
**So that** I can ensure visual quality before final video generation

**Key Tasks:**
- Backend: Extend orchestrator for reference_image and storyboard stages
- Backend: Process image-specific feedback
- Frontend: Build image gallery review UI
- Frontend: Reuse chat interface for image feedback
- Frontend: Handle batch feedback for multiple images
- Testing: Image generation → feedback → regeneration → approval

**Acceptance Criteria:**
- User can review reference images with chat interface
- User can provide feedback and see images regenerate
- User can approve images to proceed
- Same workflow works for storyboard images
- Quality scores displayed for each image

### Story 4: Advanced Image Editing (3 points)

**As a** content creator
**I want** to select specific regions in images and replace them with new content
**So that** I can fix specific issues (wrong character, bad background) without regenerating entire image

**Key Tasks:**
- Backend: Implement inpainting service with SDXL-inpaint
- Backend: Process mask data and prompts
- Frontend: Build image editor with canvas and selection tools
- Frontend: Brush/eraser for mask creation
- Frontend: Prompt input for replacement description
- Testing: Mask creation → inpainting → result display

**Acceptance Criteria:**
- User can open image editor from review UI
- User can draw mask over region to replace
- User can provide text prompt for replacement
- Inpainting generates new image with replacement
- Edited image replaces original in pipeline

---

## Total Effort Estimation

**Total Story Points:** 10
**Estimated Timeline:** 8-12 days (assuming 1-2 points per day)

**Breakdown:**
- Story 1: 1 point (~1 day)
- Story 2: 3 points (~2-3 days)
- Story 3: 3 points (~2-3 days)
- Story 4: 3 points (~2-3 days)
- Buffer for testing/integration: ~2 days

---

## Risks and Mitigations

**Risk 1: WebSocket scalability under load**
- **Mitigation:** Load test with 100+ concurrent connections; implement connection pooling; use Redis pub/sub for multi-server support if needed

**Risk 2: Session state grows too large**
- **Mitigation:** Store only essential state; use image URLs instead of base64; implement TTL (1 hour) for automatic cleanup

**Risk 3: Inpainting quality inconsistent**
- **Mitigation:** Use SDXL-inpaint (state-of-the-art); allow multiple regenerations; provide negative prompts; consider ControlNet as fallback

**Risk 4: Users abandon pipeline mid-flow**
- **Mitigation:** Track analytics on abandonment points; optimize UX based on data; consider auto-save draft functionality in future

**Risk 5: External API rate limits exceeded**
- **Mitigation:** Monitor API usage proactively; implement exponential backoff; queue requests during high load; alert at 80% of limit

---

## Success Metrics

**Usage Metrics:**
- Interactive pipeline adoption rate: Target > 50% of users try it
- Completion rate: Target > 70% of users who start complete all stages
- Average feedback messages per session: Track for UX optimization
- Regeneration requests per stage: Track to identify problematic stages

**Quality Metrics:**
- User satisfaction score: Target 4.5/5 for interactive vs. 3.5/5 for automated
- Support ticket reduction: Target 30% fewer "video didn't match my vision" tickets
- Time to final video: Track for UX optimization (interactive may take longer but produce better results)

**Business Metrics:**
- Conversion to premium tier (if interactive is premium feature): Track
- Retention rate for users who try interactive: Compare to automated-only users
- Net Promoter Score (NPS): Track for users of interactive feature

---

**Related Documentation:**
- Technical Specification: `docs/tech-spec.md`
- PRD: `docs/PRD.md` (Section 8.7: Hero-Frame & Iterative Refinement Workflow)
- Architecture: `docs/architecture.md`
- Epic 8 Tech Spec: `docs/sprint-artifacts/tech-spec-epic-8.md` (CLI image feedback loops)
- Epic 9 Tech Spec: `docs/sprint-artifacts/tech-spec-epic-9.md` (CLI video feedback loops)
