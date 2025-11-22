# Story 1.1: Unified Pipeline Orchestrator & Configuration System

Status: ready-for-dev

## Story

As a backend developer,
I want a single pipeline orchestrator that coordinates all stages (story, references, scenes, videos) using externalized YAML configurations,
so that we eliminate hardcoded Master Mode prompts and have one execution path for both UI and CLI.

## Acceptance Criteria

1. **Single Orchestrator Module** - A single `backend/app/services/unified_pipeline/orchestrator.py` module coordinates all pipeline stages (story → references → scenes → videos)

2. **Externalized Prompts** - All LLM prompts are externalized to `backend/app/config/prompts/*.yaml` files:
   - `story_director.yaml` - Story generation prompt template
   - `story_critic.yaml` - Story evaluation prompt
   - `scene_writer.yaml` - Scene description generation
   - `scene_critic.yaml` - Scene evaluation prompt
   - `scene_cohesor.yaml` - Cross-scene consistency validation

3. **Pipeline Stage Configuration** - Pipeline configurations exist in `backend/app/config/pipelines/default.yaml` with:
   - Stage enable/disable flags (story: true, reference_images: true, scenes: true, videos: true)
   - Max iterations per stage (story: 3, scenes: 2)
   - Timeout settings (story: 120s, scenes: 180s, videos: 600s)
   - Quality thresholds (vbench_enabled: true, threshold_good: 80, threshold_acceptable: 60)
   - Parallel generation settings (parallel: true, max_concurrent: 5)

4. **Pydantic Config Validation** - Orchestrator loads configuration via `config_loader.py` with Pydantic validation (PipelineConfig schema validates all settings before execution)

5. **Dual Execution Modes** - Orchestrator supports:
   - **Interactive mode:** Waits for user approval via WebSocket at story and scene stages
   - **Automated mode:** Runs entire pipeline without user input (CLI headless execution)

6. **Unified API Endpoint** - `POST /api/v2/generate` endpoint accepts GenerationRequest schema with all required fields:
   - prompt (required)
   - framework (optional: AIDA, PAS, FAB, custom)
   - brand_assets (optional: product_images[], logo, character_images[])
   - config overrides (optional: quality_threshold, parallel_variants, enable_vbench)
   - interactive flag (true for UI, false for CLI automated)
   - session_id (optional for resuming)

7. **Database Tracking** - Orchestrator creates Generation database record tracking:
   - Status progression (pending → story → references → scenes → videos → completed/failed)
   - Current stage indicator
   - All outputs (story_text, reference_images JSONB, scenes JSONB, video_clips JSONB, final_video_url)
   - Config snapshot used (JSONB)
   - Error message if failed

8. **No Hardcoded Workflows** - Zero hardcoded prompts or pipeline logic in Python code - all configurable via YAML

## Tasks / Subtasks

- [ ] Create unified pipeline orchestrator module (AC: #1, #5, #6, #7)
  - [ ] Implement `backend/app/services/unified_pipeline/orchestrator.py` with main `generate()` method
  - [ ] Add stage execution sequencing (story → references → scenes → videos)
  - [ ] Implement interactive mode with WebSocket approval waiting
  - [ ] Implement automated mode for CLI execution
  - [ ] Add Generation database record creation and status tracking
  - [ ] Write unit tests for orchestrator stage transitions

- [ ] Externalize LLM prompts to YAML configs (AC: #2, #8)
  - [ ] Create `backend/app/config/prompts/` directory structure
  - [ ] Extract hardcoded Master Mode prompts to YAML files (story_director, story_critic, scene_writer, scene_critic, scene_cohesor)
  - [ ] Implement variable substitution in prompts ({framework}, {product}, {audience}, etc.)
  - [ ] Write unit tests for prompt loading and variable replacement

- [ ] Create pipeline configuration system (AC: #3, #4)
  - [ ] Implement `backend/app/services/unified_pipeline/config_loader.py`
  - [ ] Create `backend/app/config/pipelines/default.yaml` with all stage settings
  - [ ] Create Pydantic schema `backend/app/schemas/unified_pipeline.py` (PipelineConfig, GenerationRequest, GenerationResponse)
  - [ ] Add config validation before pipeline execution
  - [ ] Write unit tests for config loading and Pydantic validation

- [ ] Implement unified API endpoint (AC: #6)
  - [ ] Create `backend/app/api/routes/unified_pipeline.py` with POST /api/v2/generate
  - [ ] Add request validation using GenerationRequest Pydantic schema
  - [ ] Return 202 Accepted with generation_id, session_id, websocket_url
  - [ ] Add error handling (400 Bad Request, 401 Unauthorized, 429 Rate Limit, 500 Internal Error)
  - [ ] Write API integration tests

- [ ] Extend database schema for unified pipeline (AC: #7)
  - [ ] Add JSONB fields to Generation model (reference_images, scenes, video_clips, config)
  - [ ] Add current_stage field to track pipeline progress
  - [ ] Create Alembic migration for schema changes
  - [ ] Test migration on development database
  - [ ] Write database model tests for JSONB serialization

- [ ] Integration testing (AC: All)
  - [ ] Test end-to-end pipeline execution (prompt → final video) in automated mode
  - [ ] Test interactive mode with WebSocket feedback loops
  - [ ] Verify config-driven architecture (change YAML, verify behavior changes)
  - [ ] Test error recovery and graceful degradation
  - [ ] Performance testing: verify < 10 min total generation time

## Dev Notes

### Architecture Patterns and Constraints

**From Architecture.md:**
- **Unified Pipeline Orchestration** (lines 78-86): Four independent pipeline stages coordinated by single orchestrator, each stage implemented as separate service module with clear input/output contracts
- **Configuration Patterns** (ADR-005, lines 1672-1706): All LLM prompts externalized to YAML templates with variable substitution, pipeline stage configs (enable/disable, timeouts, quality thresholds), Pydantic validation for config schemas
- **Background Task Processing** (ADR-001, lines 1562-1583): FastAPI BackgroundTasks for VBench scoring and video stitching, separate thread pool execution, non-blocking HTTP responses
- **Data Models** (lines 1092-1121): Reuses existing Generation table with JSONB fields (reference_images, scenes, video_clips, config), preserves brownfield schema compatibility

**From Tech-Spec (Epic 1):**
- Component Alignment Table (lines 54-66): Unified Orchestrator location `backend/app/services/unified_pipeline/orchestrator.py`, Multi-Agent LLM System reusable agents in `backend/app/services/agents/*.py`
- Services and Modules Table (lines 80-87): Orchestrator responsibilities include main pipeline coordinator, stage execution sequencing, interactive/automated mode routing, session state management
- Workflows and Sequencing (lines 433-490): Main Pipeline Execution Flow with interactive and automated mode branches, WebSocket communication for user feedback

**Testing Requirements:**
- Unit Tests: `tests/test_services/test_orchestrator.py` - verify single entry point and stage transitions
- Integration Tests: `tests/test_integration/test_pipeline_execution.py` - verify state transitions
- Configuration Tests: `tests/test_services/test_config_loader.py` - validate prompt loading and config schema
- API Tests: `tests/test_api/test_unified_pipeline.py` - endpoint tests with various request payloads

### Project Structure Notes

**Component Locations** (from Tech-Spec Component Alignment, lines 54-66):
- **Unified Orchestrator:** `backend/app/services/unified_pipeline/orchestrator.py`
- **Config Loader:** `backend/app/services/unified_pipeline/config_loader.py`
- **Multi-Agent LLM System:** `backend/app/services/agents/` (story_director.py, story_critic.py, scene_writer.py, scene_critic.py, scene_cohesor.py)
- **API Endpoint:** `backend/app/api/routes/unified_pipeline.py`
- **Database Models:** `backend/app/db/models/generation.py` (existing, extend with JSONB fields)
- **Pydantic Schemas:** `backend/app/schemas/unified_pipeline.py`
- **Prompt Templates:** `backend/app/config/prompts/*.yaml`
- **Pipeline Configs:** `backend/app/config/pipelines/default.yaml`

**Database Schema Changes** (from Tech-Spec lines 132-169):
```sql
-- Add JSONB fields to existing generations table
ALTER TABLE generations ADD COLUMN brand_assets JSONB;
ALTER TABLE generations ADD COLUMN reference_images JSONB;
ALTER TABLE generations ADD COLUMN scenes JSONB;
ALTER TABLE generations ADD COLUMN video_clips JSONB;
ALTER TABLE generations ADD COLUMN config JSONB;
ALTER TABLE generations MODIFY COLUMN framework VARCHAR(50);
```

**Naming Conventions** (from Architecture.md lines 760-786):
- Backend files: snake_case (`unified_pipeline.py`, `story_director.py`)
- Classes: PascalCase (`StoryDirector`, `GenerationRequest`)
- Functions/methods: snake_case (`generate_story()`, `validate_config()`)
- Constants: UPPER_SNAKE_CASE (`MAX_ITERATIONS`, `DEFAULT_QUALITY_THRESHOLD`)

### References

**Technical Specifications:**
- [Source: docs/sprint-artifacts/tech-spec-epic-epic-1.md#Detailed-Design] - Services and Modules table defines orchestrator responsibilities and component structure
- [Source: docs/sprint-artifacts/tech-spec-epic-epic-1.md#Workflows-and-Sequencing] - Main Pipeline Execution Flow (lines 433-490)
- [Source: docs/sprint-artifacts/tech-spec-epic-epic-1.md#Data-Models-and-Contracts] - Database Schema with JSONB extensions (lines 132-169)
- [Source: docs/sprint-artifacts/tech-spec-epic-epic-1.md#APIs-and-Interfaces] - Unified Pipeline Endpoint specification (lines 249-292)

**Architecture Decisions:**
- [Source: docs/architecture.md#ADR-005] - Configuration-Driven vs Hardcoded Prompts (lines 1673-1706)
- [Source: docs/architecture.md#ADR-001] - FastAPI BackgroundTasks vs Celery for MVP (lines 1562-1583)
- [Source: docs/architecture.md#Novel-Pattern-Designs] - Configuration Patterns (lines 1007-1073)
- [Source: docs/architecture.md#Project-Structure] - Backend structure and file organization (lines 56-147)

**Requirements Traceability:**
- [Source: docs/epics.md#Story-1.1] - Story 1.1 acceptance criteria (lines 85-134)
- [Source: docs/epics.md#FR-Coverage-Matrix] - FR51-FR56 Configuration requirements, FR82-FR97 CLI execution (lines 464-484)

### Constraints and Technical Debt

**From Architecture.md ADR-001 (lines 1562-1583):**
- **No Celery Dependency:** Use FastAPI BackgroundTasks for MVP (adequate for VBench/stitching), can migrate post-MVP if task persistence becomes critical
- **Limitation:** Tasks don't survive server restarts (acceptable - VBench can be re-run)
- **Migration Path:** If task persistence becomes critical, add Celery with Redis broker post-MVP

**From Architecture.md (lines 69-73):**
- **PostgreSQL Production / SQLite Development:** Preserve existing database setup, no schema migration required beyond adding JSONB fields
- **Brownfield Compatibility:** Cannot change existing database models (Generation, QualityMetric, etc.), add fields only, maintain backward compatibility

**Existing Codebase to Leverage:**
- WebSocket implementation: `backend/app/api/routes/websocket.py` (already exists, reuse for interactive mode)
- Session storage: `backend/app/services/session/session_storage.py` (already exists for WebSocket sessions)
- Database models: `backend/app/db/models/generation.py` (extend with JSONB fields, preserve existing functionality)

## Dev Agent Record

### Context Reference

- docs/sprint-artifacts/1-1-unified-pipeline-orchestrator-configuration-system.context.xml

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

<!-- Links to debug logs will be added during development -->

### Completion Notes List

<!-- Implementation notes, patterns, deviations will be added when story is complete -->

### File List

<!-- NEW/MODIFIED/DELETED files will be listed here after implementation -->
