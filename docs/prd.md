# ad-mint-ai - Product Requirements Document

**Author:** BMad
**Date:** 2025-11-22
**Version:** 1.0

---

## Executive Summary

Ad Mint AI is consolidating four separate video ad generation pipelines into a single, unified, best-in-class system that eliminates the false choice between visual consistency and user control. The unified pipeline combines Master Mode's industry-leading 3-reference-image consistency system with Interactive Mode's iterative feedback capabilities, Original Pipeline's quality scoring visibility, and CLI's headless execution—all in a flexible, configuration-driven architecture that works seamlessly via web UI or command line.

This is a brownfield consolidation project that transforms fragmented technical debt (4 separate codebases requiring 4x maintenance) into a cohesive competitive advantage: the only AI video ad platform where users get Master Mode-level character/product consistency while maintaining full creative control through feedback at every generation stage.

### What Makes This Special

**"Master Mode-level visual consistency combined with Interactive Mode's iterative user feedback - the only AI video ad generator that doesn't force users to choose between consistency OR control."**

Every existing AI video generator—including our own current pipelines—forces users into an impossible trade-off:

- **Choose Consistency:** Use Master Mode, get videos with characters/products that look the same across clips, but lose all ability to iterate, refine, or guide the generation. It's a black box that either works or doesn't.

- **Choose Control:** Use Interactive Mode, provide feedback at each stage, shape the narrative and visuals, but get videos where characters morph between scenes and products change appearance—making the final output unusable for professional advertising.

The unified pipeline breaks this constraint by merging Master Mode's sophisticated reference image system (vision-enhanced AI analyzing 3 reference shots for cross-clip consistency) with Interactive Mode's conversation-driven refinement flow. Users get both: professional-grade visual coherence AND the creative control to iterate until the ad perfectly matches their vision.

This isn't incremental improvement—it's solving the fundamental UX problem that makes current AI video tools frustrating for serious marketing work.

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
- **Frontend:** React 19+, TypeScript 5.9+, Vite 5.4+
- **Database:** PostgreSQL (production) / SQLite (development)
- **AI Services:** OpenAI GPT-4, Replicate (Flux for images, Kling for videos)
- **Deployment:** AWS EC2 + RDS + S3 with Nginx reverse proxy

---

## Success Criteria

**The unified pipeline succeeds when users experience the "impossible combination" - Master Mode consistency with Interactive Mode control - and development velocity increases from eliminating 4-pipeline fragmentation.**

### User Experience Success

**1. The Consistency-Control Breakthrough**
- Users generate professional video ads with > 85% visual similarity for characters/products across all clips (Master Mode standard) WHILE providing iterative feedback at story, reference image, and scene stages (Interactive Mode capability)
- Zero forced trade-offs: users don't choose between consistency OR control - they get both
- Confidence in final output: users trust that their brand assets will appear correctly and consistently

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
