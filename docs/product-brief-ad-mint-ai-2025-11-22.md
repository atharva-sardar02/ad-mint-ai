# Product Brief: Ad Mint AI - Unified Pipeline

**Date:** 2025-11-22
**Author:** BMad
**Context:** Brownfield Enhancement - Pipeline Consolidation

---

## Executive Summary

Ad Mint AI is consolidating four separate working video ad generation pipelines into a single, unified, best-in-class system that combines the visual consistency of Master Mode, the interactivity of the Interactive Pipeline, quality scoring from the Original Pipeline, and CLI execution capabilities—all in a flexible, configuration-driven architecture.

The unified pipeline will support both UI and CLI interfaces, enable iterative user feedback at all generation stages while maintaining cross-clip visual coherence, and introduce flexible brand input handling (products, logos, characters) that works whether all, some, or no brand assets are provided.

---

## Core Vision

### Problem Statement

**The Current Fragmentation Problem:**

Ad Mint AI currently operates with four separate video generation pipelines, each solving different aspects of the problem but creating significant operational overhead:

1. **Master Mode Pipeline** - Produces the most visually consistent videos using a 3-reference-image approach and multi-agent LLM system, but is completely hardcoded, inflexible, and lacks user interactivity. It cannot generate reference images—they must be provided.

2. **Interactive Pipeline** - Enables valuable user feedback during story, reference image, and scene generation, but lacks the visual consistency mechanisms (reference image system) that make Master Mode effective. Additionally suffers from UI bugs (WebSocket errors, state loss on navigation).

3. **Original Pipeline** - Has useful quality scoring and parallel video generation capabilities but produces poor overall quality and is largely deprecated.

4. **CLI Tools** - Provides standalone command-line execution but is separate from the web UI workflows.

**The Core Problem:**

Teams and individual users must choose between:
- **Consistency OR Interactivity** - Can't have both
- **UI OR CLI** - No unified execution model
- **Hardcoded OR Flexible** - Master Mode works but can't adapt
- **Quality Visibility OR Speed** - Scoring exists but not integrated

This fragmentation means:
- Maintenance burden across 4 codebases
- Feature improvements locked to single pipelines
- User frustration from choosing between critical capabilities
- Inconsistent user experience depending on pipeline chosen
- Technical debt accumulation in separate systems

### Problem Impact

**Development Impact:**
- 4x maintenance overhead (bug fixes, AI model updates, feature additions)
- Duplicate code for similar functionality across pipelines
- Testing complexity with 4 separate workflows
- Risk of drift and incompatibility between pipelines

**User Impact:**
- Inconsistent results depending on pipeline choice
- Cannot combine Master Mode's consistency with Interactive feedback
- Learning curve for different pipeline interfaces
- Workarounds required (e.g., generating ref images separately for Master Mode)
- Frustration with UI bugs in Interactive mode

**Business Impact:**
- Slower feature development due to fragmented codebase
- Higher risk of regression bugs
- Difficult to optimize without affecting all pipelines
- Cannot scale effectively with multiple pipeline codebases

### Why Existing Solutions Fall Short

**Current Pipelines - Partial Solutions:**

- **Master Mode:** Excellent consistency but zero flexibility—hardcoded prompts, fixed workflows, no user input during generation, can't generate its own reference images

- **Interactive Mode:** Good UX concept but incomplete implementation—missing visual consistency features, has stability issues (WebSocket errors), doesn't maintain character/product consistency across clips

- **Original Pipeline:** Built before consistency breakthrough, deprecated quality, but has valuable quality metric display that other pipelines lack

- **CLI Tools:** Standalone capability but disconnected from main workflows—no integration with UI, separate codebase to maintain

**Why Integration Is Hard:**

- Each pipeline has different architecture patterns
- Master Mode's agent orchestration is tightly coupled to hardcoded prompts
- Interactive Mode's state management conflicts with streaming approaches
- Reference image system not designed for on-the-fly generation
- No shared configuration layer across pipelines

### Proposed Solution

**Unified AI Video Ad Generation Pipeline:**

A single, modular pipeline architecture that synthesizes the best features of all four existing pipelines while adding critical missing capabilities:

**Core Capabilities:**

1. **Visual Consistency (from Master Mode)**
   - 3-reference-image system for character/product/style consistency
   - Vision-enhanced AI that analyzes reference images
   - Cross-clip coherence mechanisms (consistent colors, actions, continuity)
   - Motion continuity without typical AI artifacts

2. **Interactivity (from Interactive Mode)**
   - User feedback at all generation stages:
     - Story refinement and narrative approval
     - Reference image evaluation and regeneration
     - Individual scene/shot description edits
   - ChatGPT-style conversational interface
   - Sequential output display in chat feed
   - System infers next step from user input (no mode buttons)

3. **Quality & Performance (from Original Pipeline)**
   - Image and video quality scoring display
   - Parallel video generation for A/B testing
   - Performance metrics and optimization

4. **Dual Execution (from CLI Tools)**
   - Full CLI support for all capabilities
   - Headless backend execution
   - Backend fully decoupled from UI
   - Same functionality via web UI or command line

**New Capabilities:**

1. **Flexible Brand Inputs:**
   - Optional brand product(s) - multiple reference shots
   - Optional brand logo
   - Optional brand character/mascot - multiple reference shots
   - Pipeline adapts whether all, some, or none provided
   - Generates missing assets when needed

2. **Configuration-Driven Architecture:**
   - No hardcoded prompts or workflows
   - Modular agent system
   - Configurable pipeline stages
   - Easy to extend and customize

3. **Improved State Management:**
   - Robust WebSocket handling
   - State persistence across navigation
   - Error recovery and graceful degradation

**Technical Approach:**

- **Modular Pipeline Engine:** Stage-based architecture where each stage (story, reference, scenes, videos) is independent and composable
- **Unified Agent Orchestration:** Shared multi-agent framework (Director, Critic, Cohesor patterns) that works in both interactive and automated modes
- **Smart Reference Image System:** Can accept user-provided images OR generate them on demand, feeding into same consistency mechanisms
- **Dual Interface Layer:** API layer that supports both REST/WebSocket (UI) and programmatic/CLI invocation
- **Quality Integration:** Consistent quality scoring across all generation stages
- **Parallel Execution:** Support for generating multiple variants simultaneously for comparison

### Key Differentiators

**Vs. Current Fragmented Approach:**
- **Unified Codebase:** Single pipeline to maintain, test, and enhance
- **No Feature Trade-offs:** Get consistency AND interactivity AND quality scoring
- **Consistent UX:** Same high-quality experience via UI or CLI
- **Flexible Configuration:** Adapt pipeline without code changes

**Vs. Typical AI Video Generators:**
- **True Visual Consistency:** 3-reference-image approach with vision-enhanced AI (rare in market)
- **Iterative Refinement:** User feedback at every stage, not just prompt engineering
- **Multi-Modal Coherence:** Characters, products, colors, actions stay consistent across clips
- **Advertising Intelligence:** Built on proven frameworks (AIDA, PAS, FAB), not generic video generation

---

## Target Users

### Primary Users

**Solo Entrepreneurs & Small Marketing Teams**

**Current Situation:**
- Need professional video ads but lack budget for agencies or video production teams
- Currently use generic AI video tools that produce inconsistent, low-quality results
- Spend hours trying to get AI tools to maintain character/product consistency
- Want to iterate and refine but tools are "one-shot" generation only

**Frustrations:**
- "AI videos look cheap because characters change between clips"
- "I have to generate 50 times to get one usable video"
- "Can't give feedback during generation—have to start over each time"
- "Tools either let me customize OR give good results, never both"

**What They Value:**
- **Consistency:** Characters and products that look the same across entire ad
- **Control:** Ability to guide and refine at each step
- **Efficiency:** Fast iteration without starting from scratch
- **Professional Quality:** Results that don't scream "cheap AI video"

**Technical Comfort:**
- Comfortable with web interfaces
- Some may prefer CLI for automation/scripting
- Understand basic video/marketing concepts
- Not necessarily technical developers

**Success Looks Like:**
- Creating a polished 30-60 second ad in under an hour (including iterations)
- Brand consistency across all clips
- Professional quality that works for social media, landing pages, presentations
- Ability to A/B test different versions quickly

---

## Success Metrics

### Key Performance Indicators

**Performance Targets:**

1. **Time to Final Video: < 10 minutes**
   - From initial prompt to final rendered video (including user iterations)
   - Critical for user experience and competitive advantage
   - Includes all stages: story generation, reference images, scene creation, video generation
   - Must account for user feedback loops while staying under threshold

2. **Video Quality Score: > 80 on benchmark**
   - Measured using standardized video quality benchmarks (VBench or equivalent)
   - Applies to final stitched video output
   - Ensures professional-grade results comparable to manual production
   - Quality must not degrade when adding interactivity to Master Mode approach

**Technical Success Metrics:**

- **Pipeline Consolidation Complete:** All 4 pipelines deprecated, single codebase operational
- **Feature Parity:** 100% of critical features from all pipelines available in unified version
- **Zero State Bugs:** No WebSocket errors, no state loss on navigation
- **Dual Interface Coverage:** All features accessible via both UI and CLI

**User Experience Metrics:**

- **Visual Consistency Score:** Characters/products maintain > 85% visual similarity across clips
- **Iteration Efficiency:** Users can refine story/scenes without full regeneration
- **Motion Continuity:** Zero artifact occurrences (teleporting objects, position resets)
- **Brand Input Flexibility:** Pipeline successfully generates videos with 0, 1, 2, or 3 brand assets provided

**Quality Metrics:**

- **Parallel Generation Support:** Successfully generate 2+ video variants simultaneously
- **Quality Score Visibility:** Real-time quality metrics displayed at all generation stages
- **Cross-Clip Coherence:** > 90% cohesion score across scene transitions

### Business Objectives

**Primary Goal:** Eliminate technical debt and maintenance burden from 4-pipeline fragmentation

**Secondary Goals:**
- Enable rapid feature development in unified codebase
- Improve user satisfaction by combining consistency + interactivity
- Support both power users (CLI) and mainstream users (UI)
- Position for future enhancements (e.g., advanced brand customization, more video styles)

**Success Looks Like:**
- Single pull request affects entire pipeline (not 4 separate updates)
- New AI model updates deploy once (not 4 times)
- Users choose Ad Mint AI because it offers capabilities competitors can't match
- Development velocity increases 3-4x without pipeline fragmentation overhead

---

## MVP Scope

### Core Features

**Must-Have for Unified Pipeline Launch:**

**1. Visual Consistency System (Master Mode Integration)**
- 3-reference-image input support (user-provided or generated)
- Vision-enhanced AI analysis of reference images
- Character/product consistency tracking across all clips
- Color palette and style consistency mechanisms
- Motion continuity validation (prevent teleporting/artifacts)

**2. Interactive Feedback Loop (Interactive Mode Integration)**
- **Story Stage:** User can review, refine, and approve story before proceeding
- **Reference Image Stage:** User can evaluate, regenerate, or upload custom reference images
- **Scene Stage:** User can edit individual scene descriptions and regenerate specific scenes
- Multi-stage conversation UI (ChatGPT-style interface)
- State persistence across all stages (no data loss on navigation)
- System infers next step from user context (no manual mode switching)

**3. Quality & Performance (Original Pipeline Integration)**
- Real-time quality scoring display (image and video)
- VBench or equivalent quality metrics > 80 threshold validation
- Parallel video generation capability for A/B testing (2+ variants)
- Performance monitoring and < 10 minute total generation time

**4. Dual Execution Interface (CLI Integration)**
- Full REST/WebSocket API for UI consumption
- Complete CLI command set mirroring all UI capabilities
- Headless backend execution (no UI dependency)
- Programmatic API for automation/scripting

**5. Flexible Brand Input System (New Capability)**
- Optional brand product images (0-N reference shots)
- Optional brand logo upload
- Optional brand character/mascot images (0-N reference shots)
- Dynamic pipeline adaptation based on what's provided:
  - All provided: Use all assets for consistency
  - Some provided: Generate missing assets maintaining style
  - None provided: Generate all assets from prompt
- Asset validation and preprocessing

**6. Configuration-Driven Architecture (New Capability)**
- Modular pipeline stage system (story → references → scenes → videos)
- Configurable agent orchestration (Director/Critic/Cohesor patterns)
- No hardcoded prompts or workflows
- Easy stage enable/disable via configuration

**7. Robust State Management (Bug Fixes)**
- Reliable WebSocket connection handling with auto-reconnect
- Session state persistence in database
- Navigation-safe state (no loss when leaving/returning to pipeline view)
- Graceful error recovery and user-friendly error messages

**8. Multi-Agent LLM System**
- Story generation: Director + Critic iterative refinement
- Scene generation: Writer + Critic + Cohesor for coherence
- Vision analysis: Image understanding for reference consistency
- All agents work in both interactive and automated modes

### Out of Scope for MVP

**Defer to Post-Launch:**

- **Advanced Brand Customization:**
  - Brand style guide parsing (color palettes, fonts, design rules)
  - Automatic brand compliance validation
  - Brand asset library management

- **Extended Video Formats:**
  - Vertical video optimization (TikTok/Reels)
  - Different aspect ratios (16:9, 9:16, 1:1, 4:5)
  - Variable length videos (15s, 30s, 60s, 90s)

- **Batch Processing:**
  - Bulk video generation from CSV
  - Scheduled generation jobs
  - Campaign-level management (multiple related ads)

- **Advanced A/B Testing:**
  - Automatic variant generation with systematic changes
  - Statistical significance testing
  - Performance tracking across variants

- **Team Collaboration:**
  - Multi-user editing and approval workflows
  - Comment/annotation system
  - Version control and history

- **Video Editing Post-Generation:**
  - Built-in video editor for trim/cut/rearrange
  - Audio track customization
  - Subtitle/caption generation

- **Analytics & Insights:**
  - Usage analytics dashboard
  - Generation pattern insights
  - Quality trend analysis over time

### MVP Success Criteria

**The unified pipeline MVP is successful when:**

✅ **Consolidation Complete:**
- Single codebase replaces all 4 pipelines
- All original pipelines deprecated and removed
- Zero duplicated functionality

✅ **Performance Achieved:**
- < 10 minute end-to-end generation (including user feedback)
- > 80 quality score on benchmark
- > 85% visual consistency across clips

✅ **Features Functional:**
- Users can iterate on story/scenes while maintaining consistency
- Both UI and CLI work identically
- Brand inputs work with any combination of provided assets
- No WebSocket or state management bugs

✅ **Quality Maintained:**
- Output quality matches or exceeds current Master Mode
- Motion artifacts eliminated
- Parallel generation produces consistent quality

✅ **User Validation:**
- 3-5 test users successfully generate professional-quality ads
- Positive feedback on ChatGPT-style interface
- Users prefer unified pipeline over fragmented options

### Future Vision Features

**Post-MVP Enhancements:**

**Phase 2 - Enhanced Customization:**
- Brand style guide integration
- Advanced scene composition controls
- Custom advertising framework support (beyond AIDA/PAS/FAB)
- Template library for common ad types

**Phase 3 - Scale & Collaboration:**
- Team workspace and collaboration features
- Batch processing and campaign management
- Advanced A/B testing with analytics
- API rate limiting and usage tiers

**Phase 4 - Creative Intelligence:**
- Automatic trend detection and incorporation
- Style transfer from example videos
- Competitive ad analysis and suggestions
- Performance prediction before generation

**Phase 5 - Platform Expansion:**
- Mobile app (iOS/Android)
- Browser extensions for quick generation
- Integration with ad platforms (Meta, Google, TikTok)
- Webhook support for automation workflows

---

