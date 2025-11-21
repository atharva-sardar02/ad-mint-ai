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

#### Current Status (Nov 19, 2025)

**✅ What's Working:**
- ✅ Google Veo 3.1 Integration - Default model with R2V mode and start/end frame control
- ✅ User Reference Image Direct Usage - User's image used directly as first scene reference
- ✅ Enhanced Image Generation - Always enabled by default with prompt enhancement and quality scoring
- ✅ Sequential Image Generation - Visual reference chain working correctly
- ✅ Product Identity - Bottles/products maintain identity across scenes (shape, color, features)
- ✅ Storyboard Image Display - Complete images with click-to-view popup modal
- ✅ LLM-Selected Transitions - Scene transitions selected by LLM for smooth video flow

**🔄 Recent Updates:**
- 🔄 Model changed to Google Veo 3.1 (from Veo 3)
- 🔄 User images now used directly (not regenerated) for first scene
- 🔄 Enhanced image generation always enabled (no toggle required)
- 🔄 Storyboard images display improvements (no cropping, popup viewer)

## Key Features

- **Google Veo 3.1 (Default)**: Premium cinematic quality with R2V mode (1-3 reference images) and start/end frame control
- **User Reference Image Direct Usage**: User-provided images used directly as first scene reference (not regenerated)
- **Enhanced Image Generation**: Always enabled by default with 2-agent prompt enhancement and 4-model quality scoring
- **Detailed Storyboard Planning**: LLM creates rich, detailed prompts (40-80 words) for each scene
- **Sequential Image Generation**: Each image uses the previous one as reference for visual consistency
- **Parallel Video Generation**: All videos generated simultaneously using detailed prompts + reference images
- **Dual Consistency**: Text-based markers + visual reference images
- **AIDA Framework**: Attention → Interest → Desire → Action structure
- **Start/End Frame Control**: Generates start and end frame images for precise video control (Veo 3.1, Kling 2.5 Turbo Pro)
- **Storyboard Visualizer UI**: Real-time visual storyboard display with complete images and click-to-view popup
- **Image Generation Prompts**: Displays actual prompts (with consistency markers) used for each image
- **LLM-Selected Transitions**: Scene transitions selected by LLM for smooth video flow
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
2. Use user's reference image directly (if provided) or generate reference images sequentially (Enhanced mode with prompt enhancement + quality scoring)
3. Generate videos in parallel (Veo 3.1 default/Sora-2/PixVerse)
4. Assemble final video with LLM-selected transitions

**With User Reference Image:**
```python
POST /api/generate-with-image
{
  "prompt": "Create an ad for a luxury perfume",
  "image": [your reference image file]
}
```
Your image will be used directly as the first scene's reference, ensuring all generated images maintain consistency with your original.

