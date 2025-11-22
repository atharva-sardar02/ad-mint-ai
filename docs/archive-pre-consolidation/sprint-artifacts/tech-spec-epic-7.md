# Epic Technical Specification: Multi-Scene Coherence & Quality Optimization

Date: 2025-11-15
Author: BMad
Epic ID: 7
Status: Draft

---

## Overview

Epic 7 implements state-of-the-art generation-time consistency techniques and automated quality control to ensure professional multi-scene video coherence—the core differentiator for professional ad generation. This epic incorporates bleeding-edge research techniques prioritizing prevention (generation-time consistency) over correction (post-processing), as outlined in the Multi-Scene Video Ad Generation Research Report. The system leverages seed control, IP-Adapter, LoRA training, VideoDirectorGPT-style LLM planning, VBench quality metrics, CSFD character consistency detection, ControlNet compositional consistency, and enhanced post-processing to maintain visual coherence across multiple scenes. This epic addresses the fundamental challenge identified in the PRD (Section 20.2 Phase 3 Features) and research report: maintaining character identity, visual style, and narrative flow across multiple generated video clips. The implementation builds upon Epic 3's video generation pipeline, adding sophisticated consistency enforcement mechanisms that transform basic multi-scene generation into professional-quality ad production.

## Objectives and Scope

**In-Scope:**
- Coherence Settings UI Panel (Story 7.0) - User-controllable settings interface for enabling/disabling coherence techniques
- Seed Control and Latent Reuse (Story 7.1) - Shared random seeds and latent state reuse across scenes
- Enhanced LLM Planning (Story 7.2) - VideoDirectorGPT-style planning with consistency groupings, entity descriptions, and shot lists
- IP-Adapter Integration (Story 7.3) - Identity preservation for characters and products using reference images
- LoRA Training Pipeline (Story 7.4) - Training and application of LoRA models for recurring characters/products
- VBench Quality Control (Story 7.5) - Automated quality assessment with temporal, aesthetic, and prompt alignment metrics
- Enhanced Post-Processing (Story 7.6) - Brand-aware color grading, transition optimization, and style normalization
- CSFD Character Consistency (Story 7.7) - Cross-Scene Face Distance scoring for character-driven ads
- ControlNet Integration (Story 7.8) - Compositional consistency via depth maps, layout control, and pose consistency
- Quality Feedback Loop (Story 7.9) - Comprehensive metrics tracking and pattern recognition for continuous improvement

**Out-of-Scope:**
- Real-time video generation (maintains async pipeline from Epic 3)
- Custom model training beyond LoRA fine-tuning
- Manual video editing workflows (covered in Epic 6)
- Multi-user collaboration features
- Advanced analytics dashboards (basic metrics only)
- Integration with external video editing software
- Real-time quality monitoring during generation (post-generation assessment only)

## System Architecture Alignment

Epic 7 extends the existing video generation pipeline architecture established in Epic 3. The coherence and quality optimization features integrate seamlessly with the existing pipeline services:

**Integration Points:**
- **Coherence Settings Service** - New service that reads user preferences and applies them throughout the pipeline
- **Enhanced Scene Planning** - Extends `services/pipeline/scene_planning.py` with VideoDirectorGPT-style planning
- **Video Generation Service** - Extends `services/pipeline/video_generation.py` with seed control, IP-Adapter, LoRA, and ControlNet integration
- **Quality Control Service** - New service `services/pipeline/quality_control.py` for VBench and CSFD assessment
- **Enhanced Post-Processing** - Extends `services/pipeline/export.py` with brand-aware color grading and transition optimization
- **Asset Management** - New service `services/assets/` for managing reference images, LoRA models, and quality metrics

**Database Extensions:**
- `generations` table: Add `coherence_settings` JSON field, `seed_value` integer, `quality_metrics` JSON field
- New `lora_models` table: Store trained LoRA models with metadata
- New `reference_images` table: Store entity reference images for IP-Adapter
- New `quality_metrics` table: Store VBench and CSFD scores per clip

**Frontend Components:**
- New `CoherenceSettingsPanel` component in `frontend/src/components/coherence/`
- Extends `Dashboard.tsx` with coherence settings UI
- Optional quality metrics display in `VideoDetail.tsx`

**Constraints:**
- Must maintain backward compatibility with existing video generation (Epic 3)
- All coherence techniques are optional and user-controllable
- Quality assessment should not significantly increase generation time
- LoRA training requires GPU infrastructure (may need external service integration)

## Detailed Design

### Services and Modules

| Service/Module | Responsibility | Inputs | Outputs | Owner |
|----------------|----------------|--------|---------|-------|
| `coherence_settings.py` | Manages user coherence preferences, validates settings, applies defaults | User settings from UI, generation request | Coherence configuration object | Backend Team |
| `enhanced_scene_planning.py` | VideoDirectorGPT-style planning with consistency groupings, entity descriptions, shot lists | User prompt, LLM API | Enhanced scene plan with consistency markers | Backend Team |
| `seed_manager.py` | Generates and manages seeds for video generation, implements latent reuse | Generation ID, scene plan | Seed value, latent states | Backend Team |
| `ip_adapter_service.py` | Manages reference images, applies IP-Adapter conditioning to video generation | Entity descriptions, reference images | IP-Adapter configuration | Backend Team |
| `lora_service.py` | Trains LoRA models, manages LoRA assets, applies LoRA during generation | Training images, entity metadata | Trained LoRA model, LoRA application config | Backend Team |
| `quality_control.py` | Runs VBench and CSFD assessments, triggers regeneration for low-quality clips | Generated video clips | Quality scores, regeneration flags | Backend Team |
| `enhanced_post_processing.py` | Brand-aware color grading, transition optimization, style normalization | Video clips, brand guidelines, quality metrics | Enhanced video with color grading | Backend Team |
| `controlnet_service.py` | Generates depth maps, applies layout control, enforces pose consistency | Scene plan, reference scenes | ControlNet configuration | Backend Team |
| `quality_analytics.py` | Tracks quality metrics, performs pattern recognition, provides feedback | Quality metrics, generation outcomes | Analytics insights, improvement recommendations | Backend Team |
| `asset_manager.py` | Stores and retrieves reference images, LoRA models, manages asset lifecycle | Images, LoRA files | Asset URLs, metadata | Backend Team |

### Data Models and Contracts

**Enhanced Generation Model:**
```python
class Generation(Base):
    # ... existing fields from Epic 3 ...
    coherence_settings: JSON = Column(JSON, nullable=True)  # User-selected coherence techniques
    seed_value: Optional[int] = Column(Integer, nullable=True)  # Shared seed for all scenes
    quality_metrics: JSON = Column(JSON, nullable=True)  # VBench, CSFD scores
    enhanced_planning_output: JSON = Column(JSON, nullable=True)  # VideoDirectorGPT-style plan
```

**New LoRA Model:**
```python
class LoRAModel(Base):
    id: UUID = Column(UUID, primary_key=True)
    user_id: UUID = Column(UUID, ForeignKey('users.id'), nullable=False)
    entity_name: str = Column(String, nullable=False)  # Character/product name
    entity_type: str = Column(String, nullable=False)  # 'character' or 'product'
    model_path: str = Column(String, nullable=False)  # Path to .safetensors file
    base_model: str = Column(String, nullable=False)  # Base model used for training
    training_config: JSON = Column(JSON, nullable=True)  # Training parameters
    created_at: DateTime = Column(DateTime, default=datetime.utcnow)
    updated_at: DateTime = Column(DateTime, onupdate=datetime.utcnow)
```

**New Reference Image:**
```python
class ReferenceImage(Base):
    id: UUID = Column(UUID, primary_key=True)
    generation_id: UUID = Column(UUID, ForeignKey('generations.id'), nullable=True)
    entity_name: str = Column(String, nullable=False)
    entity_type: str = Column(String, nullable=False)  # 'character' or 'product'
    image_path: str = Column(String, nullable=False)
    embedding: Optional[bytes] = Column(LargeBinary, nullable=True)  # IP-Adapter embedding
    created_at: DateTime = Column(DateTime, default=datetime.utcnow)
```

**New Quality Metrics:**
```python
class QualityMetric(Base):
    id: UUID = Column(UUID, primary_key=True)
    generation_id: UUID = Column(UUID, ForeignKey('generations.id'), nullable=False)
    scene_number: int = Column(Integer, nullable=False)
    clip_path: str = Column(String, nullable=False)
    vbench_scores: JSON = Column(JSON, nullable=True)  # Temporal, aesthetic, alignment scores
    csfd_score: Optional[float] = Column(Float, nullable=True)  # Character consistency score
    overall_quality: float = Column(Float, nullable=True)  # Composite score 0-100
    passed_threshold: bool = Column(Boolean, default=True)
    created_at: DateTime = Column(DateTime, default=datetime.utcnow)
```

**Enhanced Scene Plan Schema:**
```json
{
  "consistency_groups": [
    {
      "entity_name": "Character A",
      "entity_type": "character",
      "scenes": [1, 3, 5],
      "visual_requirements": {
        "colors": ["#FF5733", "#FFFFFF"],
        "style": "professional, confident",
        "appearance": "dark hair, blue eyes, business suit"
      }
    }
  ],
  "shot_list": [
    {
      "shot_number": 1,
      "scene_number": 1,
      "description": "Wide shot of character entering office",
      "duration": 3,
      "camera_movement": "dolly_in",
      "shot_size": "wide",
      "perspective": "third_person",
      "lens_type": "35mm"
    }
  ],
  "entity_descriptions": {
    "Character A": "Professional businessperson, 30s, confident demeanor..."
  }
}
```

### APIs and Interfaces

**Enhanced Generation Endpoint:**
```
POST /api/generate
Request Body:
{
  "prompt": "Create a luxury watch ad",
  "coherence_settings": {
    "seed_control": true,
    "ip_adapter": true,
    "lora": false,
    "enhanced_planning": true,
    "vbench_quality_control": true,
    "post_processing_enhancement": true,
    "controlnet": false,
    "csfd_detection": false
  }
}
Response: { "generation_id": "uuid", "status": "pending" }
```

**LoRA Training Endpoint:**
```
POST /api/lora/train
Request Body:
{
  "entity_name": "Brand Mascot",
  "entity_type": "character",
  "training_images": ["url1", "url2", ...],
  "base_model": "stable-diffusion-xl-base-1.0"
}
Response: { "lora_id": "uuid", "status": "training", "estimated_time": 3600 }
```

**Quality Metrics Endpoint:**
```
GET /api/generations/{id}/quality
Response: {
  "generation_id": "uuid",
  "overall_quality": 85.5,
  "vbench_scores": {
    "temporal_quality": 88.2,
    "aesthetic_quality": 82.1,
    "prompt_alignment": 86.3
  },
  "csfd_score": 0.25,
  "scene_metrics": [...]
}
```

**Coherence Settings Endpoint:**
```
GET /api/coherence/settings/defaults
Response: {
  "seed_control": { "enabled": true, "recommended": true, "cost_impact": "none" },
  "ip_adapter": { "enabled": true, "recommended": true, "cost_impact": "low" },
  ...
}
```

### Workflows and Sequencing

**Enhanced Video Generation Pipeline (with Coherence):**

1. **User Submits Generation Request** with coherence settings
2. **Coherence Settings Service** validates and applies defaults
3. **Enhanced Scene Planning** (if enabled):
   - LLM generates VideoDirectorGPT-style plan with consistency groupings
   - Creates entity descriptions and shot list metadata
   - Identifies entities requiring consistency (characters, products)
4. **Reference Image Generation** (if IP-Adapter enabled):
   - For each entity in consistency groups, generate or retrieve reference image
   - Store reference images in asset manager
5. **Seed Generation** (if seed control enabled):
   - Generate single random seed for entire video
   - Store seed in generation record
6. **Video Clip Generation** (per scene, with coherence techniques):
   - Apply seed value to all Replicate API calls
   - If IP-Adapter enabled: Condition generation on entity reference images
   - If LoRA enabled: Load and apply LoRA models for entities
   - If ControlNet enabled: Generate depth maps and apply layout control
   - Use enhanced shot list metadata in visual prompts
   - Apply latent reuse for continuous scenes
7. **Quality Assessment** (if VBench enabled):
   - After each clip generation, run VBench evaluation
   - Store quality scores in quality_metrics table
   - If score below threshold, trigger regeneration (up to 2 retries)
8. **CSFD Analysis** (if enabled and character-driven):
   - Extract face embeddings from character scenes
   - Calculate CSFD scores
   - Flag scenes with high drift
9. **Enhanced Post-Processing** (if enabled):
   - Apply brand-aware color grading using histogram matching
   - Optimize transitions based on scene analysis
   - Normalize lighting and style across clips
10. **Video Assembly** (existing from Epic 3):
    - Stitch clips with optimized transitions
    - Add audio layer
    - Final export
11. **Quality Analytics**:
    - Store all quality metrics
    - Update quality feedback loop
    - Generate improvement recommendations

**LoRA Training Workflow:**

1. User uploads training images (10-20 images recommended)
2. System validates image quality and dataset size
3. Training service processes images:
   - Preprocesses images (resize, normalize)
   - Configures training parameters (rank, learning rate, epochs)
   - Trains LoRA model using base model
   - Validates trained model quality
4. Store trained LoRA in asset library
5. Associate LoRA with user account and entity
6. LoRA available for future generations

## Non-Functional Requirements

### Performance

- **Generation Time Impact:**
  - Seed control: No additional time (built into generation)
  - IP-Adapter: +10-15% per scene (reference image processing)
  - LoRA: +5% per scene (model loading)
  - Enhanced Planning: +30-60 seconds (additional LLM call)
  - VBench Quality Control: +20-30 seconds per clip (evaluation time)
  - CSFD Detection: +10-15 seconds per character scene (face detection)
  - ControlNet: +15-20% per scene (depth map generation)
  - Enhanced Post-Processing: +30-45 seconds (color grading computation)
  - **Target:** Total coherence overhead should not exceed 2x baseline generation time

- **Latency Requirements:**
  - Coherence settings validation: <100ms
  - Enhanced scene planning: <60 seconds (LLM call)
  - Reference image generation: <30 seconds per entity
  - Quality assessment: <30 seconds per clip
  - LoRA training: <2 hours for 20-image dataset (async, background job)

- **Throughput:**
  - Support concurrent generations with independent coherence settings
  - Quality assessment should not block pipeline (async processing where possible)

### Security

- **Asset Protection:**
  - LoRA models and reference images are user-scoped (users can only access their own assets)
  - Asset storage encrypted at rest
  - Secure API endpoints for asset upload/download

- **API Key Management:**
  - Coherence techniques may require additional API keys (IP-Adapter services, VBench)
  - Store API keys securely in environment variables
  - Rotate keys regularly

- **Data Privacy:**
  - Quality metrics stored with generation records (user-scoped)
  - Anonymized analytics for pattern recognition (optional, with user consent)

### Reliability/Availability

- **Graceful Degradation:**
  - If IP-Adapter service unavailable, fall back to standard generation
  - If VBench evaluation fails, continue generation without quality assessment
  - If LoRA model fails to load, fall back to IP-Adapter or standard generation
  - If enhanced planning fails, fall back to basic scene planning (Epic 3)

- **Error Handling:**
  - All coherence techniques wrapped in try-catch blocks
  - Log errors but don't fail entire generation
  - User notification if coherence techniques partially fail

- **Retry Logic:**
  - Quality-triggered regeneration: Up to 2 retries per clip
  - LoRA training: Automatic retry on transient failures
  - Reference image generation: 3 retries with exponential backoff

### Observability

- **Logging:**
  - Log coherence settings applied to each generation
  - Log quality scores and regeneration triggers
  - Log LoRA training progress and outcomes
  - Log IP-Adapter usage and reference image associations

- **Metrics:**
  - Track coherence technique usage (which techniques are most popular)
  - Track quality score distributions (VBench, CSFD)
  - Track regeneration rates (how often quality triggers regeneration)
  - Track LoRA training success rates and training times
  - Track cost impact of coherence techniques

- **Monitoring:**
  - Alert on high regeneration rates (indicates quality issues)
  - Alert on LoRA training failures
  - Alert on quality assessment service downtime
  - Monitor asset storage usage (reference images, LoRA models)

## Dependencies and Integrations

### New Python Dependencies

```
# Quality Assessment
vbench>=0.1.0  # VBench evaluation library (if available)
face-recognition>=1.3.0  # Face detection for CSFD
insightface>=0.7.3  # Face embedding extraction (ArcFace alternative)

# IP-Adapter
diffusers>=0.21.0  # IP-Adapter implementation
transformers>=4.35.0  # Model loading
torch>=2.0.0  # Deep learning framework

# LoRA Training
peft>=0.6.0  # Parameter-Efficient Fine-Tuning
accelerate>=0.24.0  # Training acceleration
kohya-ss>=0.1.0  # LoRA training utilities (if using)

# ControlNet
controlnet-aux>=0.4.0  # ControlNet preprocessing
depth-anything>=0.1.0  # Depth map generation (MiDaS alternative)

# Enhanced Image Processing
scikit-image>=0.21.0  # Histogram matching, color grading
lutgen>=0.1.0  # LUT generation for color grading

# Asset Management
boto3>=1.28.0  # S3 storage for assets (future)
pillow>=10.1.0  # Already in requirements, used for image processing
```

### External Services

- **VBench Evaluation Service:**
  - GitHub: Vchitect/VBench
  - May require local deployment or API integration
  - Alternative: Implement custom quality metrics based on VBench methodology

- **IP-Adapter Services:**
  - Can use diffusers library locally
  - May integrate with Replicate if IP-Adapter models available
  - Alternative: Pre-process reference images locally, send embeddings to video generation

- **LoRA Training Infrastructure:**
  - Requires GPU (NVIDIA H100, A100, or RTX 4090+)
  - Options: Local GPU, RunPod, Vast.ai, or AWS SageMaker
  - For MVP: Use external service (RunPod API) for training

- **Face Recognition Services:**
  - Use face-recognition library (dlib-based) or InsightFace
  - Both can run locally without external API

### Frontend Dependencies

No new major dependencies required. Existing React + TypeScript stack sufficient.

Optional enhancements:
- `react-tooltip` or similar for coherence settings tooltips
- Chart library (e.g., `recharts`) for quality metrics visualization (optional)

## Acceptance Criteria (Authoritative)

1. **Coherence Settings UI (Story 7.0):**
   - User can view and toggle coherence techniques in Dashboard
   - Settings persist with generation request
   - Dependencies and warnings displayed correctly
   - Default settings applied when user doesn't specify

2. **Seed Control (Story 7.1):**
   - Same seed used for all scenes in a video when enabled
   - Seed value stored in generation record
   - Latent reuse applied for continuous scenes when marked in plan

3. **Enhanced Planning (Story 7.2):**
   - LLM generates consistency groupings for entities
   - Shot list includes camera metadata (movement, size, perspective, lens)
   - Entity descriptions provided for consistency requirements
   - Enhanced plan stored in generation record

4. **IP-Adapter (Story 7.3):**
   - Reference images generated/retrieved for entities requiring consistency
   - IP-Adapter conditioning applied during video generation
   - Character/product identity preserved across scenes
   - Reference images stored in asset manager

5. **LoRA Training (Story 7.4):**
   - Users can upload training images for character/product
   - LoRA model trains successfully on validated dataset
   - Trained LoRA applies during generation when enabled
   - LoRA models stored and associated with user/entity

6. **VBench Quality Control (Story 7.5):**
   - VBench evaluation runs after each clip generation (if enabled)
   - Quality scores stored in quality_metrics table
   - Low-quality clips trigger automatic regeneration (up to 2 retries)
   - Quality scores accessible via API

7. **Enhanced Post-Processing (Story 7.6):**
   - Brand color palette preserved during color grading
   - Transitions optimized based on scene analysis
   - Lighting and style normalized across clips
   - No quality degradation (maintains 1080p minimum)

8. **CSFD Detection (Story 7.7):**
   - Face embeddings extracted from character scenes
   - CSFD scores calculated for character consistency
   - Scores stored in quality_metrics table
   - Optional regeneration triggered for high CSFD scores

9. **ControlNet Integration (Story 7.8):**
   - Depth maps generated for reference scenes
   - Layout control applied for consistent composition
   - Pose consistency enforced using OpenPose (if applicable)
   - ControlNet configuration stored with generation

10. **Quality Feedback Loop (Story 7.9):**
    - All quality metrics tracked and stored
    - Pattern recognition identifies effective techniques
    - Analytics insights available for system improvement
    - Quality trends visible over time

## Traceability Mapping

| Acceptance Criteria | Spec Section | Component/API | Test Idea |
|---------------------|--------------|---------------|-----------|
| Coherence Settings UI | Services: coherence_settings.py | Frontend: CoherenceSettingsPanel, POST /api/generate | Unit test settings validation, E2E test settings persistence |
| Seed Control | Services: seed_manager.py | video_generation.py: apply_seed() | Verify same seed in all Replicate calls, test seed storage |
| Enhanced Planning | Services: enhanced_scene_planning.py | LLM API integration | Test consistency groupings extraction, shot list generation |
| IP-Adapter | Services: ip_adapter_service.py | video_generation.py: apply_ip_adapter() | Test reference image generation, verify identity preservation |
| LoRA Training | Services: lora_service.py | POST /api/lora/train | Test training pipeline, verify LoRA application in generation |
| VBench Quality | Services: quality_control.py | quality_control.py: evaluate_vbench() | Test VBench integration, verify regeneration triggers |
| Enhanced Post-Processing | Services: enhanced_post_processing.py | export.py: apply_color_grading() | Test color grading, verify brand palette preservation |
| CSFD Detection | Services: quality_control.py | quality_control.py: calculate_csfd() | Test face detection, verify CSFD score calculation |
| ControlNet | Services: controlnet_service.py | video_generation.py: apply_controlnet() | Test depth map generation, verify layout control |
| Quality Analytics | Services: quality_analytics.py | GET /api/generations/{id}/quality | Test metrics tracking, verify pattern recognition |

**PRD Traceability:**
- FR-030 (Video Coherence Analysis) → Stories 7.5, 7.7, 7.6
- FR-031 (Coherence Enhancement) → Stories 7.1, 7.3, 7.4, 7.6, 7.8
- FR-032 (Prompt Optimization) → Stories 7.2, 7.9
- FR-033 (Quality Feedback Loop) → Story 7.9

## Risks, Assumptions, Open Questions

### Risks

**Risk: VBench Library Availability**
- **Description:** VBench may not have a ready-to-use Python library, requiring custom implementation
- **Mitigation:** Research VBench implementation options, consider custom metrics based on VBench methodology, or use alternative quality assessment libraries
- **Status:** Open - requires research

**Risk: LoRA Training Infrastructure Cost**
- **Description:** GPU infrastructure for LoRA training may be expensive or unavailable
- **Mitigation:** Use external services (RunPod, Vast.ai) for training, implement async training jobs, consider cloud GPU spot instances
- **Status:** Open - requires cost analysis

**Risk: IP-Adapter Integration Complexity**
- **Description:** IP-Adapter may require significant integration work with Replicate API or local models
- **Mitigation:** Research Replicate IP-Adapter support, consider pre-processing reference images locally, fallback to standard generation if unavailable
- **Status:** Open - requires technical research

**Risk: Quality Assessment Performance**
- **Description:** VBench and CSFD evaluation may significantly slow down generation pipeline
- **Mitigation:** Implement async quality assessment, run evaluations in parallel where possible, make quality control optional
- **Status:** Open - requires performance testing

**Risk: ControlNet Model Compatibility**
- **Description:** ControlNet may not be compatible with all video generation models (Replicate API limitations)
- **Mitigation:** Research ControlNet support in Replicate models, implement only for supported models, provide clear user guidance
- **Status:** Open - requires API research

### Assumptions

1. **Replicate API Support:** Assumes Replicate API supports seed parameters, image inputs for IP-Adapter, and optional LoRA/ControlNet integration
2. **LLM Capabilities:** Assumes GPT-4 or Claude can generate VideoDirectorGPT-style planning with consistency groupings
3. **User Behavior:** Assumes users will enable recommended coherence techniques by default
4. **Quality Thresholds:** Assumes quality thresholds can be tuned based on user feedback and testing
5. **Asset Storage:** Assumes sufficient storage for reference images and LoRA models (can scale to S3)

### Open Questions

1. **Q: Should LoRA training be synchronous or asynchronous?**
   - **Answer:** Asynchronous - training can take hours, should be background job with status updates

2. **Q: What quality thresholds should trigger regeneration?**
   - **Answer:** TBD - Start with conservative thresholds (VBench <70, CSFD >0.5), tune based on user feedback

3. **Q: Should quality metrics be visible to end users?**
   - **Answer:** Optional - Basic quality indicator in UI, detailed metrics available via API for power users

4. **Q: How many reference images per entity for IP-Adapter?**
   - **Answer:** Start with 1 reference image, support multiple angles/expressions in future

5. **Q: Should coherence techniques be configurable per scene or per video?**
   - **Answer:** Per video for MVP, per-scene control in future enhancement

## Test Strategy Summary

### Unit Tests

- **Coherence Settings Service:** Test validation, default application, dependency checking
- **Seed Manager:** Test seed generation, storage, retrieval
- **Enhanced Scene Planning:** Test LLM prompt construction, JSON parsing, consistency grouping extraction
- **IP-Adapter Service:** Test reference image generation, embedding extraction, conditioning application
- **LoRA Service:** Test training pipeline, model loading, application during generation
- **Quality Control:** Test VBench integration, CSFD calculation, regeneration triggers
- **Post-Processing:** Test color grading algorithms, transition optimization, style normalization
- **ControlNet Service:** Test depth map generation, layout control, pose consistency

### Integration Tests

- **End-to-End Generation with Coherence:**
  - Test full pipeline with all coherence techniques enabled
  - Verify settings persistence through pipeline
  - Verify quality metrics collection
  - Verify asset storage and retrieval

- **Coherence Technique Combinations:**
  - Test seed control + IP-Adapter
  - Test LoRA + ControlNet
  - Test enhanced planning + all techniques
  - Verify no conflicts between techniques

- **Quality Assessment Integration:**
  - Test VBench evaluation after clip generation
  - Test regeneration trigger on low quality
  - Test CSFD calculation for character scenes
  - Verify quality metrics storage

### Performance Tests

- **Generation Time Impact:**
  - Measure baseline generation time (Epic 3)
  - Measure generation time with each coherence technique
  - Measure total time with all techniques enabled
  - Verify overhead stays within 2x baseline target

- **Quality Assessment Performance:**
  - Measure VBench evaluation time per clip
  - Measure CSFD calculation time
  - Verify async processing doesn't block pipeline

### Acceptance Test Scenarios

1. **User enables all recommended coherence techniques, generates video, verifies quality improvement**
2. **User trains LoRA for brand mascot, generates multiple ads, verifies character consistency**
3. **System detects low-quality clip via VBench, automatically regenerates, achieves acceptable quality**
4. **Character-driven ad with CSFD detection enabled, system flags inconsistent scenes, user regenerates**
5. **User disables all coherence techniques, generates video, verifies basic functionality maintained**

### Test Coverage Goals

- **Unit Test Coverage:** >80% for all new services
- **Integration Test Coverage:** All critical paths (generation with coherence, quality assessment, asset management)
- **Acceptance Test Coverage:** All 10 stories covered by at least one E2E scenario

