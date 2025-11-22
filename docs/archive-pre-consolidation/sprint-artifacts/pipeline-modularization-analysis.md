# Video Generation Pipeline Modularization Analysis

**Date:** 2025-11-18  
**Author:** PM Agent (BMad)  
**Status:** Analysis Complete - Ready for Implementation Planning

---

## Executive Summary

After analyzing both the **epic-8** (CLI-based) and **llm-enhancer** (UI-integrated) branches, I've identified the core architectural differences and what it would take to create a modular pipeline where backend components can be swapped while maintaining standard artifacts between stages.

**Key Finding:** Both implementations share the same conceptual pipeline stages but use different data structures and artifact formats. Modularization is feasible and will provide significant value for testing and future extensibility.

---

## Current State: Two Parallel Implementations

### Implementation 1: LLM-Enhancer Branch (UI-Integrated)

**Location:** `backend/app/services/pipeline/`

**Key Components:**
- `video_generation.py` - Main video generation service
- `storyboard_planner.py` - Storyboard planning with GPT-4 Vision
- `storyboard_generator.py` - Storyboard image generation
- `llm_enhancement.py` - LLM prompt enhancement
- `scene_planning.py` - Scene planning service
- `image_generation.py` - Image generation service

**Artifact Structure:**
- **Input:** `AdSpecification` (Pydantic model) with `Scene` objects
- **Intermediate:** `ScenePlan` (Pydantic model) with enriched `Scene` objects
- **Scene Object Fields:**
  ```python
  {
    scene_number: int
    scene_type: str
    visual_prompt: str
    model_prompts: dict[str, str]  # Model-specific optimized prompts
    reference_image_path: Optional[str]
    start_image_path: Optional[str]  # For Kling 2.5 Turbo
    end_image_path: Optional[str]     # For Kling 2.5 Turbo
    text_overlay: Optional[TextOverlay]
    duration: int
    sound_design: Optional[str]
  }
  ```
- **Output:** Video clip paths (strings)

**Integration:** FastAPI endpoints (`/api/generate`, `/api/generate-with-image`)

**Pipeline Flow:**
```
User Prompt → LLM Enhancement → Scene Planning → Storyboard Generation 
→ Video Generation → Stitching → Final Video
```

---

### Implementation 2: Epic-8 Branch (CLI-Based)

**Location:** `backend/app/services/` and `backend/app/services/pipeline/`

**Key Components:**
- `video_generation_standalone.py` - Standalone video generation (bypasses pipeline)
- `video_generation_cli.py` - CLI video generation with VBench scoring
- `storyboard_service.py` - Storyboard creation service
- `video_prompt_enhancement.py` - Video prompt enhancement CLI

**Artifact Structure:**
- **Input:** `storyboard_metadata.json` (JSON file)
- **Intermediate:** `storyboard_enhanced_motion_prompts.json` (JSON file)
- **Storyboard JSON Structure:**
  ```json
  {
    "clips": [
      {
        "clip_number": 1,
        "description": "...",
        "start_frame_prompt": "...",
        "end_frame_prompt": "...",
        "motion_description": "...",
        "camera_movement": "...",
        "shot_size": "...",
        "perspective": "...",
        "lens_type": "...",
        "start_frame_path": "path/to/clip_001_start.png",
        "end_frame_path": "path/to/clip_001_end.png"
      }
    ],
    "unified_narrative_path": "path/to/unified_narrative.json"
  }
  ```
- **Enhanced Motion Prompts JSON:**
  ```json
  {
    "storyboard_path": "...",
    "unified_narrative_path": "...",
    "clips": [
      {
        "clip_number": 1,
        "enhanced_motion_prompt": "...",
        "start_frame_path": "...",
        "end_frame_path": "..."
      }
    ]
  }
  ```
- **Output:** Video clip paths with VBench scores

**Integration:** CLI commands (separate Python scripts)

**Pipeline Flow:**
```
User Prompt → Image Prompt Enhancement → Image Generation → Storyboard Creation 
→ Video Prompt Enhancement → Video Generation (with VBench) → Assembly
```

---

## Key Differences Analysis

### 1. **Data Structure Format**

| Aspect | LLM-Enhancer | Epic-8 |
|--------|-------------|--------|
| **Format** | Pydantic models (`Scene`, `ScenePlan`) | JSON files (`storyboard_metadata.json`) |
| **Type Safety** | ✅ Strong typing with Pydantic validation | ❌ Manual JSON parsing |
| **Image Paths** | `reference_image_path`, `start_image_path`, `end_image_path` | `start_frame_path`, `end_frame_path` |
| **Prompt Storage** | `visual_prompt` + `model_prompts` dict | `enhanced_motion_prompt` (single string) |
| **Metadata** | Rich scene metadata in object | Camera metadata in JSON |

### 2. **Component Architecture**

| Component | LLM-Enhancer | Epic-8 |
|-----------|-------------|--------|
| **Video Generation** | `generate_video_clip(scene: Scene, ...)` | `generate_video_clip_with_model(prompt: str, image_input: str, ...)` |
| **Storyboard** | `StoryboardPlan` with `StoryboardScene[]` | `storyboard_metadata.json` with `clips[]` |
| **Image Handling** | Integrated in Scene objects | Separate file paths in JSON |
| **Model Support** | Model-specific prompts in `model_prompts` dict | Single prompt string |

### 3. **Integration Points**

| Aspect | LLM-Enhancer | Epic-8 |
|--------|-------------|--------|
| **Entry Point** | FastAPI endpoints | CLI scripts |
| **Progress Tracking** | Database + WebSocket (implied) | File-based traces |
| **Error Handling** | HTTP exceptions | CLI error messages |
| **Cancellation** | Background task cancellation | Process interruption |

### 4. **Quality Control**

| Aspect | LLM-Enhancer | Epic-8 |
|--------|-------------|--------|
| **Scoring** | VBench integration (implied) | VBench scoring with ranking |
| **Regeneration** | Automatic (implied) | Manual retry logic |
| **Quality Metrics** | Database storage | JSON trace files |

---

## Modularization Strategy

### Phase 1: Define Standard Artifact Interfaces

Create a unified artifact schema that both implementations can produce and consume:

```python
# backend/app/schemas/pipeline_artifacts.py

from pydantic import BaseModel
from typing import Optional, Dict, List
from pathlib import Path

class StandardSceneArtifact(BaseModel):
    """Standard scene artifact that all pipeline stages must produce/consume."""
    scene_number: int
    scene_type: str  # "Attention", "Interest", etc.
    
    # Prompts
    visual_prompt: str  # Base visual prompt
    motion_prompt: Optional[str] = None  # Motion description
    model_specific_prompts: Dict[str, str] = {}  # Optimized for each model
    
    # Image paths (standardized naming)
    reference_image_path: Optional[Path] = None  # Style reference
    start_frame_path: Optional[Path] = None      # First frame (Kling 2.5)
    end_frame_path: Optional[Path] = None        # Last frame (Kling 2.5)
    
    # Metadata
    duration_seconds: int
    camera_movement: Optional[str] = None
    shot_size: Optional[str] = None
    perspective: Optional[str] = None
    lens_type: Optional[str] = None
    
    # Overlays & Audio
    text_overlay: Optional[Dict] = None
    sound_design: Optional[str] = None
    
    # Quality metrics (populated after generation)
    quality_scores: Optional[Dict] = None
    video_path: Optional[Path] = None

class StandardStoryboardArtifact(BaseModel):
    """Standard storyboard artifact."""
    storyboard_id: str
    framework: str  # "AIDA", "PAS", "BAB"
    total_duration_seconds: int
    scenes: List[StandardSceneArtifact]
    
    # Narrative context
    unified_narrative_path: Optional[Path] = None
    consistency_markers: Optional[Dict] = None
    
    # Metadata
    created_at: str
    metadata_path: Optional[Path] = None  # Path to original JSON if from CLI
```

### Phase 2: Create Adapter Layer

Create adapters to convert between implementations:

```python
# backend/app/services/pipeline/adapters.py

from app.schemas.pipeline_artifacts import StandardSceneArtifact, StandardStoryboardArtifact
from app.schemas.generation import Scene, ScenePlan
import json
from pathlib import Path

class SceneAdapter:
    """Adapter between Scene (LLM-Enhancer) and StandardSceneArtifact."""
    
    @staticmethod
    def scene_to_artifact(scene: Scene) -> StandardSceneArtifact:
        """Convert LLM-Enhancer Scene to standard artifact."""
        return StandardSceneArtifact(
            scene_number=scene.scene_number,
            scene_type=scene.scene_type,
            visual_prompt=scene.visual_prompt,
            motion_prompt=None,  # Extract from visual_prompt if needed
            model_specific_prompts=scene.model_prompts,
            reference_image_path=Path(scene.reference_image_path) if scene.reference_image_path else None,
            start_frame_path=Path(scene.start_image_path) if scene.start_image_path else None,
            end_frame_path=Path(scene.end_image_path) if scene.end_image_path else None,
            duration_seconds=scene.duration,
            text_overlay=scene.text_overlay.dict() if scene.text_overlay else None,
            sound_design=scene.sound_design,
        )
    
    @staticmethod
    def artifact_to_scene(artifact: StandardSceneArtifact) -> Scene:
        """Convert standard artifact to LLM-Enhancer Scene."""
        from app.schemas.generation import Scene, TextOverlay
        
        return Scene(
            scene_number=artifact.scene_number,
            scene_type=artifact.scene_type,
            visual_prompt=artifact.visual_prompt,
            model_prompts=artifact.model_specific_prompts,
            reference_image_path=str(artifact.reference_image_path) if artifact.reference_image_path else None,
            start_image_path=str(artifact.start_frame_path) if artifact.start_frame_path else None,
            end_image_path=str(artifact.end_frame_path) if artifact.end_frame_path else None,
            duration=artifact.duration_seconds,
            text_overlay=TextOverlay(**artifact.text_overlay) if artifact.text_overlay else None,
            sound_design=artifact.sound_design,
        )

class StoryboardJSONAdapter:
    """Adapter between storyboard JSON (Epic-8) and StandardStoryboardArtifact."""
    
    @staticmethod
    def json_to_artifact(json_path: Path) -> StandardStoryboardArtifact:
        """Load storyboard JSON and convert to standard artifact."""
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        scenes = []
        for clip in data.get('clips', []):
            scene = StandardSceneArtifact(
                scene_number=clip['clip_number'],
                scene_type=clip.get('description', ''),
                visual_prompt=clip.get('motion_description', ''),
                motion_prompt=clip.get('enhanced_motion_prompt') or clip.get('motion_description'),
                start_frame_path=Path(clip['start_frame_path']) if clip.get('start_frame_path') else None,
                end_frame_path=Path(clip['end_frame_path']) if clip.get('end_frame_path') else None,
                duration_seconds=clip.get('duration', 4),
                camera_movement=clip.get('camera_movement'),
                shot_size=clip.get('shot_size'),
                perspective=clip.get('perspective'),
                lens_type=clip.get('lens_type'),
            )
            scenes.append(scene)
        
        return StandardStoryboardArtifact(
            storyboard_id=json_path.stem,
            framework=data.get('framework', 'AIDA'),
            total_duration_seconds=data.get('total_duration', 15),
            scenes=scenes,
            unified_narrative_path=Path(data['unified_narrative_path']) if data.get('unified_narrative_path') else None,
            created_at=data.get('created_at', ''),
            metadata_path=json_path,
        )
    
    @staticmethod
    def artifact_to_json(artifact: StandardStoryboardArtifact, output_path: Path):
        """Convert standard artifact to storyboard JSON format."""
        data = {
            'framework': artifact.framework,
            'total_duration': artifact.total_duration_seconds,
            'num_clips': len(artifact.scenes),
            'clips': [
                {
                    'clip_number': scene.scene_number,
                    'description': scene.scene_type,
                    'motion_description': scene.motion_prompt or scene.visual_prompt,
                    'enhanced_motion_prompt': scene.motion_prompt,
                    'start_frame_path': str(scene.start_frame_path) if scene.start_frame_path else None,
                    'end_frame_path': str(scene.end_frame_path) if scene.end_frame_path else None,
                    'duration': scene.duration_seconds,
                    'camera_movement': scene.camera_movement,
                    'shot_size': scene.shot_size,
                    'perspective': scene.perspective,
                    'lens_type': scene.lens_type,
                }
                for scene in artifact.scenes
            ],
            'unified_narrative_path': str(artifact.unified_narrative_path) if artifact.unified_narrative_path else None,
            'created_at': artifact.created_at,
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
```

### Phase 3: Abstract Component Interfaces

Define interfaces that all pipeline components must implement:

```python
# backend/app/services/pipeline/interfaces.py

from abc import ABC, abstractmethod
from typing import List, Optional
from app.schemas.pipeline_artifacts import StandardSceneArtifact, StandardStoryboardArtifact

class StoryboardPlannerInterface(ABC):
    """Interface for storyboard planning components."""
    
    @abstractmethod
    async def plan_storyboard(
        self,
        prompt: str,
        reference_image_path: Optional[str] = None,
        num_clips: int = 3,
        framework: str = "AIDA"
    ) -> StandardStoryboardArtifact:
        """Generate storyboard plan from prompt."""
        pass

class VideoGeneratorInterface(ABC):
    """Interface for video generation components."""
    
    @abstractmethod
    async def generate_video_clip(
        self,
        scene: StandardSceneArtifact,
        output_dir: str,
        generation_id: str,
        model_name: Optional[str] = None,
        cancellation_check: Optional[callable] = None
    ) -> str:
        """Generate video clip from scene artifact. Returns path to video file."""
        pass

class ImageGeneratorInterface(ABC):
    """Interface for image generation components."""
    
    @abstractmethod
    async def generate_images(
        self,
        prompt: str,
        num_variations: int = 4,
        output_dir: str = None
    ) -> List[str]:
        """Generate image variations. Returns list of image paths."""
        pass
```

### Phase 4: Implement Component Wrappers

Wrap existing implementations to conform to interfaces:

```python
# backend/app/services/pipeline/components/llm_enhancer_wrapper.py

from app.services.pipeline.interfaces import StoryboardPlannerInterface, VideoGeneratorInterface
from app.services.pipeline.adapters import SceneAdapter
from app.services.pipeline.storyboard_planner import get_storyboard_system_prompt
from app.services.pipeline.video_generation import generate_video_clip as llm_generate_clip
from app.schemas.pipeline_artifacts import StandardStoryboardArtifact, StandardSceneArtifact

class LLMEnhancerStoryboardPlanner(StoryboardPlannerInterface):
    """Wrapper for LLM-Enhancer storyboard planner."""
    
    async def plan_storyboard(
        self,
        prompt: str,
        reference_image_path: Optional[str] = None,
        num_clips: int = 3,
        framework: str = "AIDA"
    ) -> StandardStoryboardArtifact:
        # Use existing storyboard_planner.py
        from app.services.pipeline.storyboard_planner import create_storyboard_plan
        
        storyboard_plan = await create_storyboard_plan(
            prompt=prompt,
            reference_image_path=reference_image_path,
            num_clips=num_clips,
            framework=framework
        )
        
        # Convert to standard artifact
        scenes = [SceneAdapter.scene_to_artifact(scene) for scene in storyboard_plan.scenes]
        
        return StandardStoryboardArtifact(
            storyboard_id=storyboard_plan.storyboard_id,
            framework=storyboard_plan.framework,
            total_duration_seconds=storyboard_plan.total_duration,
            scenes=scenes,
        )

class LLMEnhancerVideoGenerator(VideoGeneratorInterface):
    """Wrapper for LLM-Enhancer video generator."""
    
    async def generate_video_clip(
        self,
        scene: StandardSceneArtifact,
        output_dir: str,
        generation_id: str,
        model_name: Optional[str] = None,
        cancellation_check: Optional[callable] = None
    ) -> str:
        # Convert to LLM-Enhancer Scene
        llm_scene = SceneAdapter.artifact_to_scene(scene)
        
        # Use existing video generation
        video_path, _ = await llm_generate_clip(
            scene=llm_scene,
            output_dir=output_dir,
            generation_id=generation_id,
            scene_number=scene.scene_number,
            cancellation_check=cancellation_check,
            preferred_model=model_name,
            reference_image_path=str(scene.reference_image_path) if scene.reference_image_path else None,
            start_image_path=str(scene.start_frame_path) if scene.start_frame_path else None,
            end_image_path=str(scene.end_frame_path) if scene.end_frame_path else None,
        )
        
        return video_path
```

```python
# backend/app/services/pipeline/components/epic8_wrapper.py

from app.services.pipeline.interfaces import StoryboardPlannerInterface, VideoGeneratorInterface
from app.services.pipeline.adapters import StoryboardJSONAdapter
from app.services.video_generation_standalone import generate_video_clip_with_model
from app.schemas.pipeline_artifacts import StandardStoryboardArtifact, StandardSceneArtifact

class Epic8StoryboardPlanner(StoryboardPlannerInterface):
    """Wrapper for Epic-8 storyboard planner (CLI-based)."""
    
    async def plan_storyboard(
        self,
        prompt: str,
        reference_image_path: Optional[str] = None,
        num_clips: int = 3,
        framework: str = "AIDA"
    ) -> StandardStoryboardArtifact:
        # Use existing storyboard_service.py
        from app.services.pipeline.storyboard_service import create_storyboard
        
        storyboard_result = await create_storyboard(
            prompt=prompt,
            num_clips=num_clips,
            reference_image_path=reference_image_path,
            total_duration=15,
        )
        
        # Load JSON and convert to standard artifact
        return StoryboardJSONAdapter.json_to_artifact(storyboard_result.metadata_path)

class Epic8VideoGenerator(VideoGeneratorInterface):
    """Wrapper for Epic-8 video generator (CLI-based with VBench)."""
    
    async def generate_video_clip(
        self,
        scene: StandardSceneArtifact,
        output_dir: str,
        generation_id: str,
        model_name: Optional[str] = None,
        cancellation_check: Optional[callable] = None
    ) -> str:
        # Use standalone video generation
        video_path, _ = await generate_video_clip_with_model(
            prompt=scene.motion_prompt or scene.visual_prompt,
            duration=scene.duration_seconds,
            output_dir=output_dir,
            generation_id=generation_id,
            model_name=model_name or "kwaivgi/kling-v2.1",
            clip_index=scene.scene_number,
            image_input=str(scene.start_frame_path) if scene.start_frame_path else None,
            end_image_input=str(scene.end_frame_path) if scene.end_frame_path else None,
        )
        
        return video_path
```

### Phase 5: Pipeline Orchestrator

Create a configurable pipeline orchestrator:

```python
# backend/app/services/pipeline/orchestrator.py

from app.services.pipeline.interfaces import (
    StoryboardPlannerInterface,
    VideoGeneratorInterface,
    ImageGeneratorInterface
)
from app.schemas.pipeline_artifacts import StandardStoryboardArtifact, StandardSceneArtifact
from typing import Optional

class PipelineOrchestrator:
    """Orchestrates video generation pipeline with swappable components."""
    
    def __init__(
        self,
        storyboard_planner: StoryboardPlannerInterface,
        video_generator: VideoGeneratorInterface,
        image_generator: Optional[ImageGeneratorInterface] = None,
    ):
        self.storyboard_planner = storyboard_planner
        self.video_generator = video_generator
        self.image_generator = image_generator
    
    async def generate_video(
        self,
        prompt: str,
        reference_image_path: Optional[str] = None,
        num_clips: int = 3,
        framework: str = "AIDA",
        output_dir: str = None,
        generation_id: str = None,
        cancellation_check: Optional[callable] = None
    ) -> List[str]:
        """Generate complete video from prompt using configured components."""
        
        # Stage 1: Plan storyboard
        storyboard = await self.storyboard_planner.plan_storyboard(
            prompt=prompt,
            reference_image_path=reference_image_path,
            num_clips=num_clips,
            framework=framework
        )
        
        # Stage 2: Generate video clips
        video_paths = []
        for scene in storyboard.scenes:
            video_path = await self.video_generator.generate_video_clip(
                scene=scene,
                output_dir=output_dir,
                generation_id=generation_id,
                cancellation_check=cancellation_check
            )
            video_paths.append(video_path)
        
        return video_paths
```

### Phase 6: Configuration & Factory

Create a factory to instantiate components based on configuration:

```python
# backend/app/services/pipeline/factory.py

from app.services.pipeline.components.llm_enhancer_wrapper import (
    LLMEnhancerStoryboardPlanner,
    LLMEnhancerVideoGenerator
)
from app.services.pipeline.components.epic8_wrapper import (
    Epic8StoryboardPlanner,
    Epic8VideoGenerator
)
from app.services.pipeline.orchestrator import PipelineOrchestrator

class PipelineFactory:
    """Factory for creating pipeline components based on configuration."""
    
    @staticmethod
    def create_orchestrator(
        storyboard_backend: str = "llm-enhancer",  # or "epic8"
        video_backend: str = "llm-enhancer",        # or "epic8"
    ) -> PipelineOrchestrator:
        """Create orchestrator with specified backend components."""
        
        # Storyboard planner
        if storyboard_backend == "llm-enhancer":
            storyboard_planner = LLMEnhancerStoryboardPlanner()
        elif storyboard_backend == "epic8":
            storyboard_planner = Epic8StoryboardPlanner()
        else:
            raise ValueError(f"Unknown storyboard backend: {storyboard_backend}")
        
        # Video generator
        if video_backend == "llm-enhancer":
            video_generator = LLMEnhancerVideoGenerator()
        elif video_backend == "epic8":
            video_generator = Epic8VideoGenerator()
        else:
            raise ValueError(f"Unknown video backend: {video_backend}")
        
        return PipelineOrchestrator(
            storyboard_planner=storyboard_planner,
            video_generator=video_generator,
        )
```

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1)
- [ ] Create `StandardSceneArtifact` and `StandardStoryboardArtifact` schemas
- [ ] Implement adapter layer (`SceneAdapter`, `StoryboardJSONAdapter`)
- [ ] Write unit tests for adapters

### Phase 2: Interfaces (Week 1-2)
- [ ] Define component interfaces (`StoryboardPlannerInterface`, `VideoGeneratorInterface`)
- [ ] Create wrapper implementations for LLM-Enhancer components
- [ ] Create wrapper implementations for Epic-8 components
- [ ] Write integration tests

### Phase 3: Orchestration (Week 2)
- [ ] Implement `PipelineOrchestrator`
- [ ] Create `PipelineFactory` for component instantiation
- [ ] Add configuration support (environment variables or config file)

### Phase 4: Integration (Week 2-3)
- [ ] Update FastAPI endpoints to use orchestrator
- [ ] Update CLI tools to use orchestrator
- [ ] Add backend selection via config/CLI args
- [ ] Write end-to-end tests

### Phase 5: Testing & Validation (Week 3)
- [ ] Test swapping backends mid-pipeline
- [ ] Validate artifact compatibility
- [ ] Performance benchmarking
- [ ] Documentation

---

## Benefits of Modularization

### 1. **Backend Swapping**
- Test different video generation backends without code changes
- A/B test quality between implementations
- Gradual migration path

### 2. **Component Reusability**
- Mix and match components (e.g., Epic-8 storyboard + LLM-Enhancer video)
- Reuse components in different contexts (CLI, API, background jobs)

### 3. **Future Extensibility**
- Add new backends (e.g., new video model provider) by implementing interface
- No need to modify existing code
- Plugin architecture

### 4. **Testing**
- Mock components for unit testing
- Test components in isolation
- Integration tests with real backends

### 5. **Maintainability**
- Clear separation of concerns
- Standardized artifact format
- Easier to understand data flow

---

## Risks & Mitigations

### Risk 1: Data Loss During Conversion
**Mitigation:** Comprehensive adapter tests, validation at each conversion step

### Risk 2: Performance Overhead
**Mitigation:** Adapters are lightweight (just data transformation), minimal overhead

### Risk 3: Breaking Changes
**Mitigation:** Version artifacts, maintain backward compatibility in adapters

### Risk 4: Complexity
**Mitigation:** Clear documentation, factory pattern hides complexity from users

---

## Next Steps

1. **Review & Approval:** Get stakeholder approval on modularization approach
2. **Prioritize:** Decide which phases to implement first
3. **Resource Allocation:** Assign developers to adapter/orchestrator work
4. **Timeline:** Finalize implementation timeline based on priorities

---

## Decisions & Configuration

### Artifact Persistence
**Decision:** All artifacts (prompts, images, videos, JSONs) should persist to disk.
- Prompts: Saved as `.txt` files in trace directories
- Images: Saved as `.png` files in output directories
- Videos: Saved as `.mp4` files in output directories
- JSONs: Saved as `.json` files (storyboard metadata, enhanced prompts, generation traces)

### Backward Compatibility
**Decision:** None required. We can break existing formats since this is a major refactor.

### Configuration
**Decision:** Environment variables (`.env` file) for backend selection.
```env
# Pipeline Backend Configuration
PIPELINE_STORYBOARD_BACKEND=llm-enhancer  # or "epic8"
PIPELINE_VIDEO_BACKEND=llm-enhancer       # or "epic8"
PIPELINE_IMAGE_BACKEND=llm-enhancer       # or "epic8"
```

### Migration Strategy
**Decision:** All at once - complete migration in single implementation phase.

### Testing Strategy
**Decision:** Focus on output format validation rather than comprehensive test coverage.
- Ensure each component produces standard artifact format
- Validate image, storyboard, and video outputs follow same structure
- Verify prompts between stages use consistent format

---

## Key Services & Files Mapping

### Complete Pipeline Component Correspondence

#### Stage 1: Prompt/LLM Enhancement

| Function | LLM-Enhancer Implementation | Epic-8 Implementation | Output Artifact |
|----------|----------------------------|----------------------|-----------------|
| **Prompt Enhancement** | `app/services/pipeline/llm_enhancement.py`<br/>`enhance_prompt_with_llm()` | `app/services/pipeline/image_prompt_enhancement.py`<br/>`enhance_image_prompt_iterative()` | Enhanced prompt text (`.txt`) |
| **Video Prompt Enhancement** | `app/services/pipeline/prompt_enhancement.py`<br/>`enhance_video_prompt()` | `app/services/pipeline/video_prompt_enhancement.py`<br/>`enhance_video_prompt_iterative()`<br/>`enhance_storyboard_motion_prompts()` | Enhanced motion prompts (`.txt` + JSON) |
| **Storyboard Prompt Enhancement** | `app/services/pipeline/storyboard_prompt_enhancement.py`<br/>`enhance_storyboard_prompts()` | Same file (shared) | Enhanced storyboard prompts (JSON) |

**Key Files:**
- **LLM-Enhancer:** `backend/app/services/pipeline/llm_enhancement.py`
- **Epic-8:** `backend/app/services/pipeline/image_prompt_enhancement.py`, `backend/app/services/pipeline/video_prompt_enhancement.py`
- **Shared:** `backend/app/services/pipeline/storyboard_prompt_enhancement.py`

---

#### Stage 2: Image Generation

| Function | LLM-Enhancer Implementation | Epic-8 Implementation | Output Artifact |
|----------|----------------------------|----------------------|-----------------|
| **Reference Image Generation** | `app/services/pipeline/image_generation.py`<br/>`generate_image()` | `app/services/image_generation.py`<br/>`generate_images()` | Image files (`.png`) + metadata JSON |
| **Storyboard Frame Generation** | `app/services/pipeline/image_generation_batch.py`<br/>`generate_images_with_sequential_references()` | `app/services/pipeline/storyboard_service.py`<br/>Uses `app/services/image_generation.py` | Start/end frame images (`.png`) |

**Key Files:**
- **LLM-Enhancer:** `backend/app/services/pipeline/image_generation.py`, `backend/app/services/pipeline/image_generation_batch.py`
- **Epic-8:** `backend/app/services/image_generation.py`
- **Shared:** `backend/app/services/pipeline/storyboard_service.py` (uses Epic-8 image generation)

**Output Format:**
- Images: `{generation_id}_scene_{scene_number}.png` or `clip_{clip_number}_start.png` / `clip_{clip_number}_end.png`
- Metadata: JSON with image paths, prompts, scores

---

#### Stage 3: Storyboard Planning & Creation

| Function | LLM-Enhancer Implementation | Epic-8 Implementation | Output Artifact |
|----------|----------------------------|----------------------|-----------------|
| **Storyboard Planning** | `app/services/pipeline/storyboard_planner.py`<br/>`plan_storyboard()` | `app/services/pipeline/storyboard_service.py`<br/>`create_storyboard()` | `StoryboardPlan` (dict) or `storyboard_metadata.json` |
| **Storyboard Generation** | `app/services/pipeline/storyboard_generator.py`<br/>`generate_storyboard()` | `app/services/pipeline/storyboard_service.py`<br/>`create_storyboard()` | Storyboard JSON + frame images |
| **Scene Planning** | `app/services/pipeline/scene_planning.py`<br/>`plan_scenes()`<br/>`create_basic_scene_plan_from_prompt()` | `app/services/pipeline/scene_planning.py`<br/>Same functions (shared) | `ScenePlan` (Pydantic) |

**Key Files:**
- **LLM-Enhancer:** `backend/app/services/pipeline/storyboard_planner.py`, `backend/app/services/pipeline/storyboard_generator.py`
- **Epic-8:** `backend/app/services/pipeline/storyboard_service.py`
- **Shared:** `backend/app/services/pipeline/scene_planning.py`

**Output Format:**
- **LLM-Enhancer:** `StoryboardPlan` dict with `scenes[]` containing `Scene` objects
- **Epic-8:** `storyboard_metadata.json` with `clips[]` array
- **Standard Artifact:** `StandardStoryboardArtifact` with `scenes[]` containing `StandardSceneArtifact`

---

#### Stage 4: Video Generation

| Function | LLM-Enhancer Implementation | Epic-8 Implementation | Output Artifact |
|----------|----------------------------|----------------------|-----------------|
| **Video Clip Generation** | `app/services/pipeline/video_generation.py`<br/>`generate_video_clip()`<br/>`generate_all_clips()` | `app/services/video_generation_standalone.py`<br/>`generate_video_clip_with_model()` | Video files (`.mp4`) |
| **Storyboard Video Generation** | Same as above | `app/services/pipeline/video_generation_cli.py`<br/>`generate_storyboard_videos()`<br/>`generate_image_to_video()` | Video files per clip (`.mp4`) + VBench scores |

**Key Files:**
- **LLM-Enhancer:** `backend/app/services/pipeline/video_generation.py`
- **Epic-8:** `backend/app/services/video_generation_standalone.py`, `backend/app/services/pipeline/video_generation_cli.py`

**Output Format:**
- Videos: `{generation_id}_scene_{scene_number}.mp4` or `clip_{clip_number}_video_{attempt}.mp4`
- Metadata: JSON with video paths, model used, costs, VBench scores (Epic-8)

---

#### Stage 5: Video Assembly & Post-Processing

| Function | LLM-Enhancer Implementation | Epic-8 Implementation | Output Artifact |
|----------|----------------------------|----------------------|-----------------|
| **Video Stitching** | `app/services/pipeline/stitching.py`<br/>`stitch_video_clips()` | Same file (shared) | Final stitched video (`.mp4`) |
| **Text Overlays** | `app/services/pipeline/overlays.py`<br/>`add_overlays_to_clips()` | Same file (shared) | Video with overlays (`.mp4`) |
| **Audio Layer** | `app/services/pipeline/audio.py`<br/>`add_audio_layer()` | Same file (shared) | Video with audio (`.mp4`) |
| **Export** | `app/services/pipeline/export.py`<br/>`export_final_video()` | Same file (shared) | Final exported video (`.mp4`) |

**Key Files:**
- **Shared:** All post-processing files are shared between implementations
  - `backend/app/services/pipeline/stitching.py`
  - `backend/app/services/pipeline/overlays.py`
  - `backend/app/services/pipeline/audio.py`
  - `backend/app/services/pipeline/export.py`

---

#### Stage 6: Quality Control & Scoring

| Function | LLM-Enhancer Implementation | Epic-8 Implementation | Output Artifact |
|----------|----------------------------|----------------------|-----------------|
| **Image Quality Scoring** | `app/services/pipeline/image_quality_scoring.py` | `app/services/image_generation.py`<br/>Uses external scoring | Quality scores (JSON) |
| **Video Quality Scoring** | `app/services/pipeline/video_quality_scoring.py` | `app/services/pipeline/video_generation_cli.py`<br/>VBench integration | VBench scores (JSON) |
| **Quality Control** | `app/services/pipeline/quality_control.py` | Same file (shared) | Quality metrics (JSON) |

**Key Files:**
- **LLM-Enhancer:** `backend/app/services/pipeline/image_quality_scoring.py`, `backend/app/services/pipeline/video_quality_scoring.py`
- **Epic-8:** VBench scoring integrated in `video_generation_cli.py`
- **Shared:** `backend/app/services/pipeline/quality_control.py`

---

### Integration Points

#### API Endpoints (LLM-Enhancer)

| Endpoint | File | Function |
|----------|------|----------|
| `POST /api/generate` | `app/api/routes/generations.py` | `create_generation()` → `process_generation()` |
| `POST /api/generate-with-image` | `app/api/routes/generations_with_image.py` | `create_generation_with_image()` |
| `GET /api/status/{id}` | `app/api/routes/generations.py` | `get_generation_status()` |

**Key File:** `backend/app/api/routes/generations.py` (main pipeline orchestrator for UI)

---

#### CLI Tools (Epic-8)

| CLI Tool | File | Function |
|----------|------|----------|
| Image prompt enhancement | `backend/scripts/enhance_image_prompt.py` | CLI wrapper for `image_prompt_enhancement.py` |
| Image generation | `backend/scripts/generate_images.py` | CLI wrapper for `image_generation.py` |
| Storyboard creation | `backend/scripts/create_storyboard.py` | CLI wrapper for `storyboard_service.py` |
| Video prompt enhancement | `backend/scripts/enhance_video_prompt.py` | CLI wrapper for `video_prompt_enhancement.py` |
| Video generation | `backend/scripts/generate_videos.py` | CLI wrapper for `video_generation_cli.py` |

**Key Files:** CLI scripts in `backend/scripts/` directory

---

### Data Flow Comparison

#### LLM-Enhancer Pipeline Flow:
```
User Prompt
  ↓
llm_enhancement.py → AdSpecification (Pydantic)
  ↓
storyboard_planner.py → StoryboardPlan (dict)
  ↓
storyboard_generator.py → StoryboardPlan with images
  ↓
image_generation.py → Scene images (reference, start, end)
  ↓
video_generation.py → Video clips (Scene objects)
  ↓
stitching.py → Final video
```

#### Epic-8 Pipeline Flow:
```
User Prompt
  ↓
image_prompt_enhancement.py → Enhanced prompt (.txt)
  ↓
image_generation.py → Best image (.png) + metadata.json
  ↓
storyboard_service.py → storyboard_metadata.json + frame images
  ↓
video_prompt_enhancement.py → storyboard_enhanced_motion_prompts.json
  ↓
video_generation_cli.py → Video clips (.mp4) + VBench scores
  ↓
stitching.py → Final video
```

---

### Standard Artifact Format (Target)

All components should produce/consume these standard artifacts:

#### StandardSceneArtifact
```python
{
    "scene_number": int,
    "scene_type": str,
    "visual_prompt": str,
    "motion_prompt": Optional[str],
    "model_specific_prompts": Dict[str, str],
    "reference_image_path": Optional[Path],
    "start_frame_path": Optional[Path],
    "end_frame_path": Optional[Path],
    "duration_seconds": int,
    "camera_movement": Optional[str],
    "shot_size": Optional[str],
    "perspective": Optional[str],
    "lens_type": Optional[str],
    "text_overlay": Optional[Dict],
    "sound_design": Optional[str],
    "quality_scores": Optional[Dict],
    "video_path": Optional[Path]
}
```

#### StandardStoryboardArtifact
```python
{
    "storyboard_id": str,
    "framework": str,
    "total_duration_seconds": int,
    "scenes": List[StandardSceneArtifact],
    "unified_narrative_path": Optional[Path],
    "consistency_markers": Optional[Dict],
    "created_at": str,
    "metadata_path": Optional[Path]
}
```

**Persistence Format:**
- JSON file: `{output_dir}/storyboard_metadata.json`
- Images: `{output_dir}/clip_{clip_number}_start.png`, `{output_dir}/clip_{clip_number}_end.png`
- Prompts: `{output_dir}/prompts/clip_{clip_number}_enhanced_motion_prompt.txt`
- Videos: `{output_dir}/clips/clip_{clip_number}_video_{attempt}.mp4`

---

**End of Analysis**

