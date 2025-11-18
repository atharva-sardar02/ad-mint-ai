# LLM Enhancer Workflow - Documentation

This folder contains documentation for the new storyboard-based video generation workflow implemented by Atharva.

## Overview

The new workflow uses a three-phase approach:
1. **Detailed Storyboard Planning** - LLM creates detailed prompts for each scene
2. **Reference Image Generation** - Sequential image generation with visual consistency
3. **Video Generation** - Parallel video generation using detailed prompts and reference images

## Table of Contents

- [Workflow Overview](./workflow-overview.md) - Complete workflow explanation
- [Models and Services](./models-and-services.md) - What we're using and why
- [Consistency System](./consistency-system.md) - How we maintain visual cohesion
- [Implementation Details](./implementation-details.md) - Technical implementation
- [API Reference](./api-reference.md) - Function signatures and usage

### Recent Updates & Test Results

- [Test Results: Perfume + Woman](./test-results-perfume-woman.md) - Latest test analysis (Nov 18, 2025)
- [Action Plan: Character Consistency](./action-plan-character-consistency.md) - Fix for character identity
- [Critical Fix: Subject Identity](./critical-fix-subject-identity-enforcement.md) - Master Template approach validation
- [Master Template Approach](./master-template-approach.md) - How subject copying works
- [Sequential Image Generation](./sequential-image-generation.md) - Visual reference chain
- [Subject Identity and Scene Variation](./subject-identity-and-scene-variation.md) - Design goals
- [Workflow Diagram](./workflow-diagram.md) - Visual pipeline overview

#### Current Status (Nov 18, 2025)

**✅ What's Working:**
- ✅ Master Template Copy-Paste Approach - LLM successfully copies subject descriptions
- ✅ Product Identity - Bottles/products maintain identity across scenes (shape, color, features)
- ✅ Sequential Image Generation - Visual reference chain working correctly
- ✅ Infrastructure - Core pipeline is solid

**🔄 In Progress:**
- 🔄 Character Consistency - Fixing generic character descriptions (see action plan)
- 🔄 Size Consistency - Adding size reference objects for scale

**❌ Known Issues:**
- ❌ Generic character descriptions produce different people in each scene
- ❌ Size variations without visual anchors (e.g., "6.5 inches tall" not enforced)

**Next Steps:**
1. Implement "Police Description" requirement for characters (detailed physical traits)
2. Add size reference objects to prompts
3. Test with enhanced character descriptions
4. Validate improvements

## Key Features

- **Detailed Storyboard Planning**: LLM creates rich, detailed prompts (40-80 words) for each scene
- **Sequential Image Generation**: Each image uses the previous one as reference for visual consistency
- **Parallel Video Generation**: All videos generated simultaneously using detailed prompts + reference images
- **Dual Consistency**: Text-based markers + visual reference images
- **AIDA Framework**: Attention → Interest → Desire → Action structure
- **Kling 2.5 Turbo Pro Support**: Generates start and end frame images for precise video control
- **Storyboard Visualizer UI**: Real-time visual storyboard display with image generation prompts
- **Image Generation Prompts**: Displays actual prompts (with consistency markers) used for each image
- **Brand Overlay**: Automatic brand name extraction and overlay at the end of videos (centered with background)
- **Resilient Error Handling**: Text overlays, audio, and brand overlay failures don't stop generation
- **Storyboard Reconstruction**: Automatic fallback to reconstruct storyboard from scene_plan for older generations

## Quick Start

```python
# The workflow is automatically triggered when you call:
POST /api/generate
{
  "prompt": "Create an ad for a fitness app",
  "use_llm": true  # Enables storyboard planning
}
```

The system will:
1. Plan detailed storyboard (GPT-4o)
2. Generate reference images sequentially (Nano Banana)
3. Generate videos in parallel (Sora-2/Veo-3/PixVerse)
4. Assemble final video

