# Multi-Stage Story-Driven System - Quick Start

## What We Built

A **4-stage LLM pipeline** that generates higher-quality video advertisements by separating narrative creation from visual specification.

## The 4 Stages

```
Stage 0: Template Selection  → AI picks best story structure (8 templates)
Stage 1: Story Generation    → Creates narrative, characters, script
Stage 2: Scene Division      → Breaks story into timed scenes
Stage 3: Visual Specification → Generates detailed image prompts
```

## Files Created

```
backend/app/services/pipeline/
├── story_templates.py              # 8 story templates (AIDA, PAS, BAB, etc.)
├── template_selector.py            # Stage 0: AI template selection
├── story_generator.py              # Stage 1: Story & script generation
├── scene_divider.py                # Stage 2: Scene breakdown & timing
├── storyboard_planner.py           # Stage 3: Visual prompts (updated)
└── multi_stage_orchestrator.py    # Main orchestrator

backend/app/schemas/
└── generation.py                   # Updated API schemas (use_multi_stage)

llm-enhancer-atharva/
├── multi-stage-system.md           # Complete documentation
└── multi-stage-quick-start.md      # This file
```

## The 8 Story Templates

1. **AIDA** - Classic advertising (Attention → Interest → Desire → Action)
2. **Problem-Agitate-Solve (PAS)** - Empathize with pain, offer solution
3. **Before-After-Bridge (BAB)** - Show transformation
4. **Hero's Journey** - Epic empowerment narrative
5. **Emotional Arc** - Heartfelt feel-good moments
6. **Teaser-Reveal** - Build mystery, dramatic reveal
7. **Social Proof** - Community trust and testimonials
8. **Sensory Experience** - Immersive sensory indulgence

## How to Use

### Option 1: Let AI Choose Template (Recommended)

```python
from app.services.pipeline.multi_stage_orchestrator import generate_multi_stage_storyboard

result = await generate_multi_stage_storyboard(
    user_prompt="Artisan coffee that starts your morning right",
    target_duration=15
)
```

### Option 2: Manual Template Override

```python
result = await generate_multi_stage_storyboard(
    user_prompt="Fitness app for busy moms",
    target_duration=15,
    template_override="problem-agitate-solve"
)
```

### API Usage

```bash
POST /api/generate
{
  "prompt": "Luxury perfume capturing midnight elegance",
  "target_duration": 15,
  "use_multi_stage": true,
  "template_override": null  // or "teaser-reveal" to force template
}
```

## What You Get

```json
{
  "stage_0_template_selection": {
    "selected_template": "emotional-arc",
    "confidence": 0.87,
    "reasoning": "Coffee + morning = intimate ritual"
  },
  "stage_1_story": {
    "story_title": "Morning Ritual",
    "narrative": {...},
    "character_subject": {
      "character_description": "Woman, 32, 5'6\", chestnut hair, emerald eyes, beauty mark...",
      "product_description": "White ceramic mug, 4 inches, gold rim..."
    },
    "voice_over_script": {...}
  },
  "stage_2_scenes": {
    "scenes": [
      {
        "scene_number": 1,
        "duration_seconds": 4,
        "action_description": "Detailed camera, lighting, action...",
        "camera_work": {...},
        "lighting": {...}
      }
    ]
  },
  "stage_3_storyboard": {
    "consistency_markers": {
      "subject_description": "MASTER template for consistency"
    },
    "scenes": [
      {
        "image_generation_prompt": "80-150 word detailed prompt",
        "start_image_prompt": "First frame specific moment",
        "end_image_prompt": "Last frame different moment"
      }
    ]
  }
}
```

## Key Benefits

### ✅ Better Storytelling
- AI selects optimal narrative structure
- Proven advertising frameworks (AIDA, PAS, Hero's Journey, etc.)
- Structured emotional arcs

### ✅ Character Consistency
- "Police description" level detail (10+ identifiers)
- Forensic character specs: age, height, hair, face, eyes, skin, marks
- Master template copied to all scenes

### ✅ Professional Output
- Voice-over scripts generated
- Camera work specified
- Lighting and composition detailed
- Scene-by-scene timing

### ✅ Flexibility
- Modify each stage independently
- Choose or override templates
- Refine specific scenes

## Trade-offs

| Metric | Legacy Single-Stage | Multi-Stage |
|--------|---------------------|-------------|
| LLM Calls | 1 | 4 |
| Duration | ~10s | ~40-50s |
| Token Cost | 1x | ~4x |
| Quality | Good | Excellent |
| Storytelling | Generic | Structured |
| Character Detail | Basic | Forensic |

## When to Use What

### Use Multi-Stage:
- ✅ Quality is critical
- ✅ Character-driven stories
- ✅ Complex narratives
- ✅ Budget allows

### Use Legacy:
- ✅ Speed is critical
- ✅ Simple product showcase
- ✅ Cost-sensitive
- ✅ No characters

## Example Outputs

### Coffee Ad (Emotional Arc)
```
Prompt: "Artisan coffee that starts your morning right"
Template: Emotional Arc
Story: "Morning Ritual"
Character: Woman, 32, forensic detail
Product: White ceramic mug, gold rim
Scenes: 4 (Quiet → Surprise → Joy → Connection)
Duration: 15s
```

### Fitness App (PAS)
```
Prompt: "Fitness app for busy moms to stay healthy"
Template: Problem-Agitate-Solve
Story: "Mom's Time"
Character: Mother, 35, juggling family
Product: Smartphone with app
Scenes: 4 (Problem → Agitate → Solve → Relief)
Duration: 15s
```

### Luxury Perfume (Teaser-Reveal)
```
Prompt: "Luxury perfume capturing midnight elegance"
Template: Teaser-Reveal
Story: "Midnight Mystery"
Character: N/A (product-focused)
Product: Frosted glass bottle, detailed specs
Scenes: 4 (Mystery → Build → Reveal → Showcase)
Duration: 15s
```

## Next Steps

1. **Test the system**: Run with different prompts to see template selection
2. **Compare outputs**: Run same prompt with multi-stage vs legacy
3. **Analyze results**: Check if selected templates make sense
4. **Refine templates**: Adjust template definitions if needed
5. **Integration**: Update main pipeline to offer multi-stage option

## Technical Details

- **Stage 0**: GPT-4o-mini (~2s, template selection)
- **Stage 1**: GPT-4o (~10-15s, story generation)
- **Stage 2**: GPT-4o (~10-15s, scene division)
- **Stage 3**: GPT-4o (~15-20s, visual prompts)
- **Total**: ~40-50 seconds, ~10,000-13,000 tokens

## Documentation

- **Full docs**: `llm-enhancer-atharva/multi-stage-system.md`
- **This guide**: `llm-enhancer-atharva/multi-stage-quick-start.md`

---

**Status**: ✅ Ready for testing  
**Date**: November 19, 2025  
**Version**: 1.0.0

