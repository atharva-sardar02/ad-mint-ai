# Architecture Document - Ad Mint AI Unified Pipeline

**Project:** Ad Mint AI - AI-Powered Video Advertisement Generator
**Architecture Version:** 1.0
**Date:** 2025-11-22
**Author:** BMad
**Type:** Brownfield Consolidation (4 Pipelines → 1 Unified System)

---

## Executive Summary

This architecture consolidates four fragmented video ad generation pipelines (Master Mode, Interactive, Original, CLI) into a single, unified, maintainable system. The architecture combines Master Mode's 3-reference-image visual consistency with Interactive Mode's conversational feedback flow, while eliminating the technical debt of 4x code duplication.

**Core Architecture Principles:**
1. **Consolidation Without Regression** - All capabilities from 4 pipelines available in unified version
2. **Configuration-Driven** - No hardcoded prompts, fully externalizable configuration
3. **Modular & Testable** - Independent pipeline stages, composable LLM agents
4. **Non-Blocking by Design** - Background tasks for VBench, parallel video generation
5. **Brownfield Compatible** - Works with existing database schema and AWS infrastructure

---

## Decision Summary

| Category | Decision | Version | Rationale |
|----------|----------|---------|-----------|
| **Backend Framework** | FastAPI | 0.104+ | Already in use, async support, OpenAPI docs |
| **Backend Language** | Python | 3.11+ | Existing codebase, AI/ML ecosystem |
| **ORM** | SQLAlchemy | 2.0+ | Already in use, mature, async support |
| **Database (Prod)** | PostgreSQL | Latest | RDS compatibility, production-ready |
| **Database (Dev)** | SQLite | Latest | Existing dev setup, zero config |
| **Frontend Framework** | React | 19+ | Already in use, modern, TypeScript support |
| **Build Tool** | Vite | 5.4+ | Already in use, fast HMR |
| **Styling** | Tailwind CSS | 3.4+ | Already in use (4.1.17), utility-first |
| **State Management** | Zustand | 5.0+ | Already in use, lightweight |
| **Routing** | React Router | 7.9+ | Already in use, standard |
| **TypeScript** | TypeScript | 5.9+ | Already in use, type safety |
| **WebSocket** | FastAPI Native WebSocket | Built-in | Already implemented, no extra dependency |
| **Session Storage** | Redis | 5.0+ | Already in use for WebSocket sessions |
| **Background Tasks** | FastAPI BackgroundTasks | Built-in | Simple, adequate for MVP, no Celery complexity |
| **Testing (Backend)** | pytest | 7.4+ | Already in use, standard Python testing |
| **Testing (Frontend)** | vitest | 1.6+ | Already in use, fast, Vite integration |
| **OpenAI** | GPT-4 | Latest | Story/scene generation, proven quality |
| **Image Generation** | Replicate Nano Banana Pro | Latest | High-quality image generation |
| **Video Generation** | Replicate Veo 3 | Latest | State-of-art video generation |
| **Storage** | AWS S3 | Latest | Already deployed, scalable |
| **Compute** | AWS EC2 | Latest | Already deployed |
| **Database (Prod)** | AWS RDS PostgreSQL | Latest | Already deployed |
| **Reverse Proxy** | Nginx | Latest | Already deployed |
| **Logging** | Python stdlib logging | 3.11+ | Structured format, zero dependencies |

---

## Project Structure

```
ad-mint-ai/
│
├── backend/                          # Python FastAPI Backend
│   ├── app/
│   │   ├── main.py                  # FastAPI app entry point, CORS, middleware
│   │   │
│   │   ├── core/                    # Core configuration and utilities
│   │   │   ├── config.py           # Settings (Pydantic BaseSettings)
│   │   │   ├── security.py         # Auth, JWT, password hashing
│   │   │   └── deps.py             # FastAPI dependencies
│   │   │
│   │   ├── api/                     # API Layer (Routes)
│   │   │   └── routes/
│   │   │       ├── auth.py         # POST /auth/login, /auth/register
│   │   │       ├── unified_pipeline.py  # POST /api/v2/generate (NEW unified endpoint)
│   │   │       ├── websocket.py    # WS /ws/{session_id} (interactive communication)
│   │   │       ├── generations.py  # GET /generations (history, downloads)
│   │   │       ├── assets.py       # POST /assets/upload (brand assets)
│   │   │       └── health.py       # GET /health (monitoring)
│   │   │
│   │   ├── services/                # Service Layer (Business Logic)
│   │   │   │
│   │   │   ├── unified_pipeline/   # NEW: Unified Pipeline Orchestration
│   │   │   │   ├── orchestrator.py # Main pipeline coordinator
│   │   │   │   ├── story_stage.py  # Story generation stage
│   │   │   │   ├── reference_stage.py  # Reference image stage
│   │   │   │   ├── scene_stage.py  # Scene generation stage
│   │   │   │   ├── video_stage.py  # Video generation stage (parallel)
│   │   │   │   └── config_loader.py  # Load pipeline configurations
│   │   │   │
│   │   │   ├── agents/              # Multi-Agent LLM System (Reusable)
│   │   │   │   ├── story_director.py   # Story generation agent
│   │   │   │   ├── story_critic.py     # Story evaluation agent
│   │   │   │   ├── scene_writer.py     # Scene description agent
│   │   │   │   ├── scene_critic.py     # Scene evaluation agent
│   │   │   │   ├── scene_cohesor.py    # Cross-scene consistency agent
│   │   │   │   └── base_agent.py       # Abstract base class for agents
│   │   │   │
│   │   │   ├── quality/             # Quality Scoring
│   │   │   │   ├── vbench_scorer.py    # VBench quality scoring (background task)
│   │   │   │   └── quality_analyzer.py # Quality metric aggregation
│   │   │   │
│   │   │   ├── media/               # Media Processing
│   │   │   │   ├── image_processor.py  # Image analysis, vision AI
│   │   │   │   ├── video_stitcher.py   # Video stitching (background task)
│   │   │   │   └── s3_uploader.py      # S3 upload with pre-signed URLs
│   │   │   │
│   │   │   └── session/             # Session Management
│   │   │       ├── session_storage.py  # Redis session store (already exists)
│   │   │       └── websocket_manager.py # WebSocket connection manager
│   │   │
│   │   ├── db/                      # Data Layer
│   │   │   ├── models/              # SQLAlchemy ORM Models
│   │   │   │   ├── generation.py   # Generation, GenerationGroup (existing)
│   │   │   │   ├── quality_metric.py # QualityMetric (existing)
│   │   │   │   ├── brand_style.py  # BrandStyle (existing)
│   │   │   │   ├── product_image.py # ProductImage (existing)
│   │   │   │   └── user.py         # User authentication
│   │   │   │
│   │   │   ├── migrations/          # Alembic database migrations
│   │   │   └── session.py          # Database session management
│   │   │
│   │   ├── schemas/                 # Pydantic Request/Response Schemas
│   │   │   ├── auth.py             # LoginRequest, TokenResponse
│   │   │   ├── unified_pipeline.py # GenerationRequest, GenerationResponse (NEW)
│   │   │   ├── websocket.py        # WSMessage types (interactive communication)
│   │   │   └── quality.py          # QualityScore schema
│   │   │
│   │   └── config/                  # Configuration Files (NEW - externalized)
│   │       ├── prompts/             # LLM prompt templates
│   │       │   ├── story_director.yaml
│   │       │   ├── story_critic.yaml
│   │       │   ├── scene_writer.yaml
│   │       │   └── ...
│   │       │
│   │       └── pipelines/           # Pipeline stage configurations
│   │           ├── default.yaml    # Default pipeline config
│   │           └── frameworks/     # Advertising frameworks (AIDA, PAS, FAB)
│   │
│   ├── cli_tools/                   # CLI Pipeline (Standalone Execution)
│   │   ├── admint.py               # Main CLI entry point (uses unified_pipeline services)
│   │   └── ...
│   │
│   ├── tests/                       # Backend Tests
│   │   ├── test_api/               # API endpoint tests
│   │   ├── test_services/          # Service layer unit tests
│   │   └── test_integration/       # End-to-end pipeline tests
│   │
│   └── requirements.txt             # Python dependencies
│
├── frontend/                         # React + TypeScript Frontend
│   ├── src/
│   │   ├── main.tsx                # Entry point, React 19 root
│   │   │
│   │   ├── routes/                  # Page Components (React Router)
│   │   │   ├── UnifiedPipeline.tsx # NEW: Main pipeline UI (ChatGPT-style)
│   │   │   ├── Dashboard.tsx       # Generation history, gallery
│   │   │   ├── Login.tsx           # Authentication
│   │   │   └── Settings.tsx        # User preferences
│   │   │
│   │   ├── components/              # Reusable Components
│   │   │   │
│   │   │   ├── chat/               # ChatGPT-Style Interface Components
│   │   │   │   ├── ChatFeed.tsx    # Scrollable message feed
│   │   │   │   ├── MessageBubble.tsx  # User/system message display
│   │   │   │   ├── PromptInput.tsx    # Text input with send button
│   │   │   │   └── QuickActions.tsx   # Optional approve/regenerate buttons
│   │   │   │
│   │   │   ├── pipeline/           # Pipeline Stage Components
│   │   │   │   ├── StoryDisplay.tsx   # Story with quality score
│   │   │   │   ├── ReferenceImages.tsx # 3 reference images (read-only MVP)
│   │   │   │   ├── SceneList.tsx      # Editable scene descriptions
│   │   │   │   ├── VideoPlayer.tsx    # Video preview with controls
│   │   │   │   └── ParallelProgress.tsx # Multi-clip progress bars
│   │   │   │
│   │   │   ├── quality/            # Quality Display Components
│   │   │   │   ├── QualityScore.tsx   # Color-coded score display
│   │   │   │   └── QualityBreakdown.tsx # Detailed metrics
│   │   │   │
│   │   │   └── common/             # Shared UI Components
│   │   │       ├── Button.tsx
│   │   │       ├── LoadingSpinner.tsx
│   │   │       └── ErrorMessage.tsx
│   │   │
│   │   ├── services/                # API Client & Services
│   │   │   ├── api.ts              # Axios instance, interceptors
│   │   │   ├── websocket.ts        # WebSocket manager (auto-reconnect)
│   │   │   └── storage.ts          # Local storage utilities
│   │   │
│   │   ├── store/                   # Zustand State Management
│   │   │   ├── pipelineStore.ts    # Pipeline session state
│   │   │   ├── authStore.ts        # Authentication state
│   │   │   └── uiStore.ts          # UI state (modals, settings)
│   │   │
│   │   ├── types/                   # TypeScript Type Definitions
│   │   │   ├── pipeline.ts         # Generation types
│   │   │   ├── websocket.ts        # WebSocket message types
│   │   │   └── api.ts              # API request/response types
│   │   │
│   │   └── utils/                   # Utility Functions
│   │       ├── formatting.ts       # Date, text formatting
│   │       └── validation.ts       # Input validation
│   │
│   ├── tests/                       # Frontend Tests (vitest)
│   │   ├── components/             # Component tests
│   │   └── integration/            # Integration tests
│   │
│   ├── package.json
│   ├── vite.config.ts              # Vite configuration
│   ├── tailwind.config.js          # Tailwind CSS configuration
│   └── tsconfig.json               # TypeScript configuration
│
├── deployment/                       # Deployment Scripts & Configuration
│   ├── deploy.sh                   # Main deployment script
│   ├── nginx.conf                  # Nginx reverse proxy config
│   ├── fastapi.service             # Systemd service for FastAPI
│   └── README.md                   # Deployment guide
│
├── docs/                             # Documentation
│   ├── index.md                    # Master index (this file)
│   ├── architecture.md             # THIS FILE
│   ├── prd.md                      # Product Requirements
│   ├── api-contracts.md            # API documentation
│   ├── data-models.md              # Database schema
│   └── development-guide.md        # Setup and development
│
└── .env.example                     # Environment variables template
```

---

## Functional Requirements to Architecture Mapping

**This section maps every FR from the PRD to specific architectural components, ensuring complete coverage.**

### User Account & Authentication (FR1-FR6)

| FR | Requirement | Architecture Component | Implementation |
|----|-------------|------------------------|----------------|
| FR1 | Create accounts | `backend/app/api/routes/auth.py` | POST /auth/register endpoint |
| FR2 | Login & sessions | `backend/app/core/security.py` | JWT token generation, validation |
| FR3 | Password reset | `backend/app/api/routes/auth.py` | POST /auth/reset-password with email |
| FR4 | Update profile | `backend/app/api/routes/auth.py` | PATCH /auth/profile |
| FR5 | Session persistence | `backend/app/core/security.py` | JWT with 30-day expiration |
| FR6 | API token auth | `backend/app/core/security.py` | Token-based CLI authentication |

### Video Ad Generation Pipeline (FR7-FR56)

**Story Generation (FR7-FR13):**

| FR | Requirement | Architecture Component | Implementation |
|----|-------------|------------------------|----------------|
| FR7 | Submit prompts | `frontend/src/components/chat/PromptInput.tsx` | Text input with submit |
| FR8 | Multi-agent story gen | `backend/app/services/agents/story_director.py`, `story_critic.py` | Director generates, Critic evaluates |
| FR9 | Select framework | `frontend/src/routes/UnifiedPipeline.tsx` | Settings modal, framework selector |
| FR10 | Iterative feedback | `backend/app/services/unified_pipeline/story_stage.py` | Conversation-driven refinement |
| FR11 | Stream progress | `backend/app/api/routes/websocket.py` | WebSocket streaming updates |
| FR12 | Story quality scores | `backend/app/services/quality/quality_analyzer.py` | Story quality metrics |
| FR13 | Approve/regenerate | `frontend/src/components/chat/QuickActions.tsx` | Approve/Regenerate buttons |

**Reference Image Management (FR14-FR25) - MVP Streamlined:**

| FR | Requirement | Architecture Component | Implementation |
|----|-------------|------------------------|----------------|
| FR14 | Generate 3 ref images | `backend/app/services/unified_pipeline/reference_stage.py` | Auto-generate from story |
| FR15 | Vision AI analysis | `backend/app/services/media/image_processor.py` | GPT-4 Vision analysis |
| FR16 | Validate quality | `backend/app/services/unified_pipeline/reference_stage.py` | Quality threshold check |
| FR17 | Maintain context | `backend/app/services/unified_pipeline/orchestrator.py` | Pass refs to scene stage |
| FR18 | Display in chat | `frontend/src/components/pipeline/ReferenceImages.tsx` | Read-only image display |
| FR19-FR21 | Upload brand assets | `frontend/src/components/common/FileUpload.tsx` | Drag-drop upload |
| FR22 | Use brand assets | `backend/app/services/unified_pipeline/reference_stage.py` | Integrate uploaded assets |
| FR23 | Auto-generate refs | `backend/app/services/unified_pipeline/reference_stage.py` | Generate if none provided |
| FR24 | Integrate assets | `backend/app/services/unified_pipeline/reference_stage.py` | Combine uploaded + generated |
| FR25 | Display asset usage | `frontend/src/components/pipeline/ReferenceImages.tsx` | Show which assets used |

**Scene Generation (FR26-FR33):**

| FR | Requirement | Architecture Component | Implementation |
|----|-------------|------------------------|----------------|
| FR26 | Multi-agent scene gen | `backend/app/services/agents/scene_writer.py`, `scene_critic.py`, `scene_cohesor.py` | Writer → Critic → Cohesor |
| FR27 | Cross-scene consistency | `backend/app/services/agents/scene_cohesor.py` | Ensure character/product/color consistency |
| FR28 | View scenes | `frontend/src/components/pipeline/SceneList.tsx` | Display all scenes with descriptions |
| FR29 | Edit scene descriptions | `frontend/src/components/pipeline/SceneList.tsx` | Inline editing |
| FR30 | Regenerate specific scene | `backend/app/services/unified_pipeline/scene_stage.py` | Regenerate single scene |
| FR31 | Approve/iterate | `frontend/src/components/chat/QuickActions.tsx` | Approve all or iterate |
| FR32 | Validate coherence | `backend/app/services/agents/scene_cohesor.py` | Pre-video validation |
| FR33 | Scene quality scores | `backend/app/services/quality/quality_analyzer.py` | Scene quality metrics |

**Video Generation & Stitching (FR34-FR39):**

| FR | Requirement | Architecture Component | Implementation |
|----|-------------|------------------------|----------------|
| FR34 | **Parallel video generation** | `backend/app/services/unified_pipeline/video_stage.py` | asyncio concurrent calls to Replicate API for all clips |
| FR35 | Per-clip progress | `frontend/src/components/pipeline/ParallelProgress.tsx` | Multiple progress bars updating in real-time |
| FR36 | Motion continuity | `backend/app/services/agents/scene_cohesor.py` | Position/action consistency prompts |
| FR37 | Video stitching | `backend/app/services/media/video_stitcher.py` | BackgroundTasks after all clips complete |
| FR38 | Download final video | `frontend/src/routes/Dashboard.tsx` | S3 pre-signed URL download |
| FR39 | Download clips | `frontend/src/routes/Dashboard.tsx` | Individual clip downloads |

**Quality Scoring (FR40-FR44) - Background, Non-Blocking:**

| FR | Requirement | Architecture Component | Implementation |
|----|-------------|------------------------|----------------|
| FR40 | VBench per-clip | `backend/app/services/quality/vbench_scorer.py` | BackgroundTasks after each clip completes |
| FR41 | VBench overall | `backend/app/services/quality/vbench_scorer.py` | BackgroundTasks after stitching |
| FR42 | Async scoring | `backend/app/api/routes/unified_pipeline.py` | FastAPI BackgroundTasks |
| FR43 | Stream scores | `backend/app/api/routes/websocket.py` | WebSocket updates as scores complete |
| FR44 | UI stays responsive | `frontend/src/routes/UnifiedPipeline.tsx` | No blocking during VBench |

**Parallel Generation & A/B Testing (FR45-FR50):**

| FR | Requirement | Architecture Component | Implementation |
|----|-------------|------------------------|----------------|
| FR45 | Multiple variants | `backend/app/services/unified_pipeline/orchestrator.py` | Multiple pipeline executions |
| FR46 | Different prompts | `frontend/src/routes/UnifiedPipeline.tsx` | Batch prompt input |
| FR47 | Parallel execution | `backend/app/services/unified_pipeline/orchestrator.py` | asyncio parallel pipelines |
| FR48 | Side-by-side view | `frontend/src/components/pipeline/VariantComparison.tsx` | Multi-video display |
| FR49 | Compare scores | `frontend/src/components/quality/QualityComparison.tsx` | Score comparison table |
| FR50 | Select winner | `frontend/src/routes/UnifiedPipeline.tsx` | Select for refinement |

**Configuration & Advanced Options (FR51-FR56):**

| FR | Requirement | Architecture Component | Implementation |
|----|-------------|------------------------|----------------|
| FR51 | Quality thresholds | `frontend/src/routes/Settings.tsx` | Threshold sliders |
| FR52 | Iteration limits | `backend/app/config/pipelines/default.yaml` | max_iterations config |
| FR53 | Enable/disable stages | `backend/app/config/pipelines/default.yaml` | stage_enabled flags |
| FR54 | Select frameworks | `frontend/src/routes/UnifiedPipeline.tsx` | Framework dropdown |
| FR55 | UI + CLI config | `backend/app/services/unified_pipeline/config_loader.py` | Unified config system |
| FR56 | Validate config | `backend/app/services/unified_pipeline/config_loader.py` | Pydantic validation |

### Interactive Conversational Interface (FR57-FR81)

| FR | Requirement | Architecture Component | Implementation |
|----|-------------|------------------------|----------------|
| FR57 | ChatGPT-style interface | `frontend/src/routes/UnifiedPipeline.tsx` | Chat feed layout |
| FR58 | Scrollable feed | `frontend/src/components/chat/ChatFeed.tsx` | Scrollable message list |
| FR59 | Natural language input | `backend/app/services/pipeline/conversation_handler.py` | Intent parsing |
| FR60 | Infer intent | `backend/app/services/pipeline/conversation_handler.py` | Approve/refine/regenerate detection |
| FR61 | Quick action buttons | `frontend/src/components/chat/QuickActions.tsx` | Optional approve/regenerate |
| FR62 | Conversation history | `backend/app/services/session/session_storage.py` | Redis session persistence |
| FR63 | Scroll history | `frontend/src/components/chat/ChatFeed.tsx` | Scrollable with history |
| FR64-FR69 | Progress feedback | `frontend/src/components/pipeline/*`, `backend/app/api/routes/websocket.py` | Real-time WebSocket updates |
| FR70-FR74 | Media display | `frontend/src/components/pipeline/ReferenceImages.tsx`, `VideoPlayer.tsx` | Inline media |
| FR75-FR81 | State management | `backend/app/services/session/session_storage.py`, `frontend/src/store/pipelineStore.ts` | Redis + Zustand |

### Command-Line Interface (FR82-FR97)

| FR | Requirement | Architecture Component | Implementation |
|----|-------------|------------------------|----------------|
| FR82 | Full CLI execution | `backend/cli_tools/admint.py` | CLI entry point |
| FR83 | Accept params | `backend/cli_tools/admint.py` | argparse CLI arguments |
| FR84 | Terminal progress | `backend/cli_tools/admint.py` | tqdm progress bars |
| FR85 | Output content | `backend/cli_tools/admint.py` | stdout text, JSON |
| FR86 | Interactive mode | `backend/cli_tools/admint.py` | Prompt for approval |
| FR87 | Automated mode | `backend/cli_tools/admint.py` | --auto flag |
| FR88 | Quality metrics JSON | `backend/cli_tools/admint.py` | JSON output format |
| FR89 | All config options | `backend/cli_tools/admint.py` | CLI args match API params |
| FR90-FR97 | Advanced CLI | `backend/cli_tools/admint.py` | Batch, parallel, logging |

### Quality Metrics & Scoring (FR98-FR104)

| FR | Requirement | Architecture Component | Implementation |
|----|-------------|------------------------|----------------|
| FR98 | VBench per-clip | `backend/app/services/quality/vbench_scorer.py` | BackgroundTasks |
| FR99 | VBench overall | `backend/app/services/quality/vbench_scorer.py` | BackgroundTasks |
| FR100 | Real-time display | `frontend/src/components/quality/QualityScore.tsx` | WebSocket streaming updates |
| FR101 | Detailed breakdowns | `frontend/src/components/quality/QualityBreakdown.tsx` | Metric details |
| FR102 | Store metrics | `backend/app/db/models/quality_metric.py` | Database persistence |
| FR103 | Visual indicators | `frontend/src/components/quality/QualityScore.tsx` | Color-coded scores |
| FR104 | Separate thread pool | `backend/app/api/routes/unified_pipeline.py` | FastAPI BackgroundTasks |

### Content Management & Library (FR105-FR121)

| FR | Requirement | Architecture Component | Implementation |
|----|-------------|------------------------|----------------|
| FR105-FR110 | Generation history | `frontend/src/routes/Dashboard.tsx`, `backend/app/api/routes/generations.py` | History view, filtering |
| FR111-FR115 | Asset library | `frontend/src/routes/AssetLibrary.tsx`, `backend/app/api/routes/assets.py` | Asset management |
| FR116-FR121 | Export & download | `backend/app/services/media/s3_uploader.py` | Pre-signed URLs |

### System Administration (FR122-FR128)

| FR | Requirement | Architecture Component | Implementation |
|----|-------------|------------------------|----------------|
| FR122 | Usage metrics | `backend/app/api/routes/admin.py` | Admin dashboard API |
| FR123 | AI service costs | `backend/app/services/monitoring/cost_tracker.py` | Cost tracking |
| FR124-FR128 | Admin config | `backend/app/api/routes/admin.py` | Admin endpoints |

### Error Handling & Recovery (FR129-FR135)

| FR | Requirement | Architecture Component | Implementation |
|----|-------------|------------------------|----------------|
| FR129 | User-friendly errors | `frontend/src/components/common/ErrorMessage.tsx` | Error display |
| FR130 | Recovery options | `frontend/src/components/common/ErrorMessage.tsx` | Retry/cancel buttons |
| FR131 | Error logging | `backend/app/core/logging.py` | Python stdlib logging |
| FR132 | Graceful degradation | `backend/app/services/unified_pipeline/orchestrator.py` | Try-except fallbacks |
| FR133 | Prevent data loss | `backend/app/services/session/session_storage.py` | Auto-save state |
| FR134 | Error details | `frontend/src/components/common/ErrorDetails.tsx` | Expandable error info |
| FR135 | Background isolation | `backend/app/api/routes/unified_pipeline.py` | BackgroundTasks error handling |

---

## Technology Stack Details

### Backend Stack

**Framework: FastAPI 0.104+**
- **Why:** High-performance async framework, automatic OpenAPI docs, WebSocket support, type safety with Pydantic
- **Already in use:** Existing codebase built on FastAPI
- **Integration:**
  - Native WebSocket support (no Socket.io needed)
  - BackgroundTasks for async operations
  - Dependency injection for database sessions, auth

**ORM: SQLAlchemy 2.0+**
- **Why:** Mature Python ORM, async support, migration tools (Alembic)
- **Already in use:** Existing database models
- **Models:** Generation, GenerationGroup, QualityMetric, BrandStyle, ProductImage, User

**Database:**
- **Production:** PostgreSQL (AWS RDS) - ACID compliant, JSON support, full-text search
- **Development:** SQLite - Zero config, file-based, adequate for local dev
- **Migration:** Alembic for schema changes

**AI Services:**
- **OpenAI GPT-4:** Story generation, scene generation, vision analysis for reference images
- **Replicate Nano Banana Pro:** High-quality image generation
- **Replicate Veo 3:** State-of-art video generation from text prompts
- **Integration:** Async HTTP calls via httpx, error handling with retry logic

**Background Processing: FastAPI BackgroundTasks**
- **Why:** Built-in, simple, adequate for MVP (VBench scoring, video stitching)
- **How:** Tasks run in separate thread pool after HTTP response sent
- **Use Cases:** VBench quality scoring, video stitching, S3 uploads
- **Limitations:** Tasks don't survive server restarts (acceptable for MVP)
- **Future:** Migrate to Celery if task persistence/retry becomes critical

**Session Storage: Redis 5.0+**
- **Why:** Fast in-memory storage, TTL support, already in use for WebSocket sessions
- **Already in use:** backend/app/services/session/session_storage.py
- **Use Cases:** WebSocket session state caching, temporary data

**WebSocket: FastAPI Native WebSocket**
- **Why:** Built-in, no extra dependencies, async support
- **Already implemented:** backend/app/api/routes/websocket.py
- **Features:** Heartbeat/ping-pong, auto-reconnect on frontend, conversation-driven feedback

**Testing: pytest 7.4+**
- **Why:** Standard Python testing framework, async support (pytest-asyncio)
- **Coverage:** Unit tests (services), integration tests (API), E2E tests (pipeline)
- **Fixtures:** Database, authenticated client, mock AI services

**Logging: Python stdlib logging**
- **Why:** Zero dependencies, structured format via JSON formatter
- **Levels:** DEBUG (development), INFO (production), ERROR (critical)
- **Format:** Structured JSON for easy parsing (timestamp, level, message, context)

### Frontend Stack

**Framework: React 19+**
- **Why:** Modern, component-based, large ecosystem, TypeScript support
- **Already in use:** Existing frontend built on React 19
- **Key Features:** Hooks, context, suspense for async operations

**Build Tool: Vite 5.4+**
- **Why:** Fast HMR, optimized builds, modern tooling
- **Already in use:** Existing build setup
- **Features:** Code splitting, lazy loading, asset optimization

**Styling: Tailwind CSS 3.4+**
- **Why:** Utility-first CSS, rapid development, small production bundle
- **Already in use:** Currently on Tailwind 4.1.17 (can stay or downgrade to 3.4 for stability)
- **Dark Theme:** Default dark background (#1a1a1a), grey chat containers

**State Management: Zustand 5.0+**
- **Why:** Lightweight, hooks-based, minimal boilerplate
- **Already in use:** Existing state management
- **Stores:** pipelineStore (session state), authStore (user auth), uiStore (UI state)

**Routing: React Router 7.9+**
- **Why:** Standard routing library, nested routes, lazy loading
- **Already in use:** Existing routing setup
- **Routes:** /pipeline, /dashboard, /settings, /login

**TypeScript 5.9+**
- **Why:** Type safety, better IDE support, catch errors at compile-time
- **Already in use:** Strict mode enabled
- **Benefits:** Catch API contract mismatches, refactoring safety

**WebSocket Client: Custom implementation**
- **Implementation:** frontend/src/services/websocket.ts
- **Features:** Auto-reconnect, heartbeat, message queueing
- **Integration:** Zustand store for WebSocket state

**HTTP Client: axios 1.13+**
- **Why:** Promise-based, interceptors for auth, already in use
- **Already in use:** Existing API client
- **Features:** Request/response interceptors, error handling

**Testing: vitest 1.6+**
- **Why:** Fast, Vite integration, Jest-compatible API
- **Already in use:** Existing test setup
- **Coverage:** Component tests (@testing-library/react), integration tests

### Infrastructure & Deployment

**Cloud Provider: AWS**
- **Compute:** EC2 instance(s) running FastAPI (uvicorn)
- **Database:** RDS PostgreSQL (production), automated backups
- **Storage:** S3 for generated videos/images, pre-signed URLs with 24hr expiration
- **Already deployed:** Existing AWS infrastructure

**Reverse Proxy: Nginx**
- **Why:** High-performance, static file serving, HTTPS termination, WebSocket support
- **Already deployed:** deployment/nginx.conf
- **Config:** Proxy /api → FastAPI, proxy /ws → WebSocket, serve frontend static files

**Process Manager: systemd**
- **Why:** Built-in on Linux, auto-restart, logging
- **Already deployed:** deployment/fastapi.service
- **Features:** Auto-restart on failure, log to journald

---

## Integration Points

### External Service Integration

**OpenAI GPT-4 API**
- **Endpoints:**
  - `POST /v1/chat/completions` (story, scene generation)
  - `POST /v1/chat/completions` with vision (reference image analysis)
- **Authentication:** API key in Authorization header (env var `OPENAI_API_KEY`)
- **Error Handling:** Retry transient failures (3 attempts, exponential backoff), fail fast on 4xx errors
- **Timeout:** 30 seconds per request
- **Implementation:** `backend/app/services/agents/*.py`

**Replicate API**
- **Models:**
  - Nano Banana Pro (image generation)
  - Veo 3 (video generation)
- **Endpoints:**
  - `POST /v1/predictions` (start generation)
  - `GET /v1/predictions/{id}` (poll status)
- **Authentication:** Token in Authorization header (env var `REPLICATE_API_TOKEN`)
- **Polling:** Check status every 2 seconds until complete/failed
- **Parallel Execution:** asyncio concurrent calls for all scene videos
- **Timeout:** 10 minutes for video generation
- **Implementation:** `backend/app/services/unified_pipeline/video_stage.py`

**AWS S3 Storage**
- **Buckets:**
  - `{project}-videos` (generated videos)
  - `{project}-images` (reference images, scene images)
- **Upload:** Multipart upload for large files (> 5MB)
- **Download:** Pre-signed URLs with 24-hour expiration
- **Authentication:** IAM role (EC2 instance profile) or access keys
- **Error Handling:** Retry failed uploads (3 attempts, exponential backoff)
- **Implementation:** `backend/app/services/media/s3_uploader.py`

**Redis (Session Storage)**
- **Connection:** Redis client via `redis-py`
- **Use Cases:** WebSocket session state caching
- **TTL:** 24 hours for session data
- **Error Handling:** Fallback to in-memory storage if Redis unavailable
- **Implementation:** `backend/app/services/session/session_storage.py`

### Internal Component Integration

**API ↔ Service Layer**
- **Pattern:** API routes call service layer methods, no business logic in routes
- **Error Handling:** Services raise custom exceptions, API routes catch and convert to HTTP responses
- **Example:** `unified_pipeline.py` route → `orchestrator.py` service

**Service ↔ Data Layer**
- **Pattern:** Services use SQLAlchemy ORM models, no raw SQL
- **Transactions:** Use database session context manager for atomic operations
- **Example:** `orchestrator.py` → `Generation` model via database session

**Frontend ↔ Backend**
- **REST API:** axios HTTP client for request/response operations
- **WebSocket:** Custom WebSocket manager for real-time updates (story streaming, progress)
- **Authentication:** JWT token in Authorization header for all requests

**WebSocket Message Flow:**
```
User Input (Frontend)
  → WS Send (frontend/src/services/websocket.ts)
  → WebSocket Route (backend/app/api/routes/websocket.py)
  → Conversation Handler (backend/app/services/pipeline/conversation_handler.py)
  → Pipeline Orchestrator (backend/app/services/unified_pipeline/orchestrator.py)
  → Agent Execution (backend/app/services/agents/*.py)
  → WS Send Response (backend/app/api/routes/websocket.py)
  → Frontend Update (frontend/src/store/pipelineStore.ts)
  → UI Render (frontend/src/components/chat/ChatFeed.tsx)
```

---

## Novel Pattern Designs

### 1. Parallel Video Clip Generation Pattern

**Problem:** Sequential video generation is too slow (5 clips × 1 min each = 5 minutes total)

**Solution:** Generate all scene video clips in parallel using asyncio concurrent execution

**Implementation:**
```python
# backend/app/services/unified_pipeline/video_stage.py

async def generate_all_videos_parallel(scenes: List[Scene]) -> List[VideoResult]:
    """Generate all scene videos in parallel using asyncio."""
    tasks = [generate_single_video(scene) for scene in scenes]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]
```

**Benefits:**
- Total time = longest clip time (~1 min), not sum of all clips (~5 min)
- 5x speed improvement for 5-scene video
- Real-time progress updates for each clip via WebSocket

**Challenges:**
- Replicate API rate limits (handled with semaphore limiting concurrent calls)
- Error handling for partial failures (retry failed clips individually)
- Frontend displays multiple progress bars simultaneously

**Frontend Integration:**
```typescript
// frontend/src/components/pipeline/ParallelProgress.tsx
<ParallelProgress clips={[
  { id: 1, progress: 45, status: 'rendering' },
  { id: 2, progress: 32, status: 'rendering' },
  { id: 3, progress: 51, status: 'rendering' },
  // ...
]} />
```

### 2. Background VBench Scoring Pattern

**Problem:** VBench quality scoring is CPU-intensive and slow (~30 seconds per video), blocking user interaction

**Solution:** Run VBench in FastAPI BackgroundTasks, stream results via WebSocket as they complete

**Implementation:**
```python
# backend/app/api/routes/unified_pipeline.py

@router.post("/generate")
async def generate_video(request: GenerationRequest, background_tasks: BackgroundTasks):
    # ... generate video synchronously ...
    video_result = await orchestrator.generate(request)

    # Start VBench scoring in background (non-blocking)
    background_tasks.add_task(
        run_vbench_scoring,
        video_path=video_result.path,
        session_id=request.session_id,
        websocket_manager=ws_manager  # Stream results via WebSocket
    )

    # Return immediately without waiting for VBench
    return GenerationResponse(video_url=video_result.url, status="complete")
```

**Benefits:**
- User can download video, start new generation, or navigate away immediately
- VBench scores stream in as background task completes
- No blocking of main application thread

**Frontend Integration:**
```typescript
// frontend/src/store/pipelineStore.ts
websocket.on('vbench_score_update', (data) => {
  updateQualityScore(data.clip_id, data.score); // Non-blocking update
});
```

### 3. Conversational Intent Parsing Pattern

**Problem:** Users provide natural language feedback ("make it more dramatic", "looks good") - how to parse intent?

**Solution:** Rule-based + LLM-enhanced intent detection

**Implementation:**
```python
# backend/app/services/pipeline/conversation_handler.py

ACK_MESSAGES = {"yes", "looks good", "approved", "great", ...}

async def parse_intent(user_message: str, context: PipelineContext) -> Intent:
    # Rule-based detection for simple cases
    if user_message.lower() in ACK_MESSAGES:
        return Intent.APPROVE

    if "regenerate" in user_message.lower() or "try again" in user_message.lower():
        return Intent.REGENERATE

    # LLM-enhanced for complex feedback
    if len(user_message.split()) > 5:
        llm_analysis = await analyze_feedback_with_llm(user_message, context)
        return llm_analysis.intent

    # Default to refinement with feedback
    return Intent.REFINE
```

**Benefits:**
- Supports both simple approvals ("ok") and complex feedback ("make the first scene more dramatic")
- No explicit mode buttons needed - system infers user intent
- Graceful fallback to LLM for ambiguous cases

### 4. 3-Reference-Image Consistency System

**Problem:** AI video generators produce inconsistent characters/products across clips

**Solution:** Generate/use 3 reference images, pass to all scene prompts with vision analysis

**Implementation:**
```python
# backend/app/services/unified_pipeline/reference_stage.py

async def generate_reference_images(story: Story, brand_assets: List[Image]) -> List[ReferenceImage]:
    # Use brand assets if provided, otherwise generate
    if brand_assets:
        ref_images = brand_assets[:3]  # Use first 3 brand images
    else:
        # Generate 3 reference images from story
        ref_images = await generate_from_story(story, count=3)

    # Analyze with GPT-4 Vision to extract visual characteristics
    for img in ref_images:
        img.analysis = await analyze_image_with_vision(img)
        # Extracts: character appearance, product features, color palette, style

    return ref_images

async def generate_scene_with_consistency(scene: Scene, ref_images: List[ReferenceImage]) -> Video:
    # Include reference image characteristics in scene prompt
    consistency_context = f"""
    CHARACTER APPEARANCE: {ref_images[0].analysis.character_description}
    PRODUCT FEATURES: {ref_images[1].analysis.product_description}
    COLOR PALETTE: {ref_images[2].analysis.colors}
    """

    scene_prompt = f"{consistency_context}\n\nSCENE: {scene.description}"
    return await replicate_video_api.generate(scene_prompt)
```

**Benefits:**
- >85% visual similarity across all clips (Master Mode proven metric)
- Works whether user provides brand assets or system generates references
- Vision AI analysis ensures detailed consistency prompts

---

## Implementation Patterns (AI Agent Consistency Rules)

**These patterns ensure multiple AI agents write compatible code.**

### Naming Conventions

**Backend (Python):**
- **Files:** snake_case (e.g., `unified_pipeline.py`, `story_director.py`)
- **Classes:** PascalCase (e.g., `StoryDirector`, `GenerationRequest`)
- **Functions/Methods:** snake_case (e.g., `generate_story()`, `validate_config()`)
- **Constants:** UPPER_SNAKE_CASE (e.g., `MAX_ITERATIONS`, `DEFAULT_QUALITY_THRESHOLD`)
- **Private methods:** Leading underscore (e.g., `_internal_helper()`)

**Frontend (TypeScript/React):**
- **Components:** PascalCase files, PascalCase export (e.g., `ChatFeed.tsx` → `export const ChatFeed`)
- **Utilities:** camelCase files, camelCase export (e.g., `formatting.ts` → `export const formatDate`)
- **Types/Interfaces:** PascalCase (e.g., `interface GenerationRequest`, `type VideoResult`)
- **Hooks:** camelCase with `use` prefix (e.g., `useWebSocket`, `usePipelineState`)
- **Constants:** UPPER_SNAKE_CASE (e.g., `const API_BASE_URL = '...'`)

**Database:**
- **Tables:** snake_case, plural (e.g., `generations`, `quality_metrics`)
- **Columns:** snake_case (e.g., `user_id`, `created_at`, `quality_score`)
- **Foreign keys:** `{table_singular}_id` (e.g., `user_id`, `generation_id`)
- **Junction tables:** `{table1}_{table2}` (e.g., `users_generations`)

**API Endpoints:**
- **REST:** Plural resources, lowercase (e.g., `/api/generations`, `/api/assets`)
- **Resource IDs:** Path params (e.g., `/api/generations/{generation_id}`)
- **Actions:** Verbs in path (e.g., `/api/generations/{id}/regenerate`)
- **WebSocket:** `/ws/{session_id}`

### File Organization Patterns

**Backend:**
```
- API routes in backend/app/api/routes/*.py (one file per resource)
- Services in backend/app/services/{domain}/*.py (grouped by domain)
- Models in backend/app/db/models/*.py (one file per table/related tables)
- Schemas in backend/app/schemas/*.py (one file per resource)
- Config in backend/app/config/{domain}/*.yaml (externalized)
```

**Frontend:**
```
- Routes (pages) in frontend/src/routes/*.tsx (one file per route)
- Reusable components in frontend/src/components/{domain}/*.tsx
- Services in frontend/src/services/*.ts (api, websocket, storage)
- State stores in frontend/src/store/*Store.ts (one file per domain)
- Types in frontend/src/types/*.ts (one file per domain)
```

**Tests:**
```
- Backend: backend/tests/test_{layer}/test_{file}.py (mirrors source structure)
- Frontend: frontend/tests/{layer}/{file}.test.tsx (mirrors source structure)
```

### API Response Format

**Success Response:**
```json
{
  "data": { /* actual response payload */ },
  "status": "success",
  "message": "Optional human-readable message"
}
```

**Error Response:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "User-friendly error message",
    "details": { /* optional additional context */ }
  },
  "status": "error"
}
```

**Pagination Response:**
```json
{
  "data": [ /* array of items */ ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 150,
    "total_pages": 8
  },
  "status": "success"
}
```

### WebSocket Message Format

**Client → Server:**
```json
{
  "type": "user_feedback",
  "payload": {
    "message": "make it more dramatic",
    "stage": "story",
    "session_id": "abc123"
  },
  "timestamp": "2025-11-22T10:30:00Z"
}
```

**Server → Client:**
```json
{
  "type": "story_generated" | "progress_update" | "error" | "vbench_score",
  "payload": { /* stage-specific data */ },
  "timestamp": "2025-11-22T10:30:05Z"
}
```

**Message Types:**
- `user_feedback` - User providing feedback/approval
- `story_generated` - Story generation complete
- `reference_images_ready` - Reference images ready
- `scenes_generated` - Scenes generated
- `video_progress` - Video generation progress (per-clip)
- `video_complete` - Video clip complete
- `vbench_score` - Quality score available
- `error` - Error occurred
- `heartbeat` - Connection keep-alive

### Error Handling Patterns

**Backend Exception Hierarchy:**
```python
class PipelineException(Exception):
    """Base exception for pipeline errors."""
    pass

class ValidationError(PipelineException):
    """User input validation failed."""
    pass

class AIServiceError(PipelineException):
    """OpenAI/Replicate API error."""
    pass

class StorageError(PipelineException):
    """S3/database storage error."""
    pass
```

**Error Handling Flow:**
```python
# Service layer raises specific exceptions
try:
    result = await service.generate_story(prompt)
except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
except AIServiceError as e:
    logger.error(f"AI service failed: {e}")
    raise HTTPException(status_code=502, detail="AI service unavailable")
except Exception as e:
    logger.exception("Unexpected error")
    raise HTTPException(status_code=500, detail="Internal server error")
```

**Frontend Error Display:**
```typescript
// frontend/src/components/common/ErrorMessage.tsx
<ErrorMessage
  type="error | warning | info"
  message="User-friendly message"
  details="Technical details (expandable)"
  actions={[
    { label: "Retry", onClick: handleRetry },
    { label: "Cancel", onClick: handleCancel }
  ]}
/>
```

### Database Patterns

**Table Schema:**
```sql
CREATE TABLE generations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    prompt TEXT NOT NULL,
    story_text TEXT,
    reference_images JSONB,  -- Array of S3 URLs
    scenes JSONB,            -- Array of scene objects
    video_url TEXT,
    quality_score FLOAT,
    status VARCHAR(50) NOT NULL,  -- pending, processing, completed, failed
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**Timestamp Columns:**
- Every table has `created_at` and `updated_at`
- Use database triggers or ORM events to auto-update `updated_at`

**Soft Deletes:**
```sql
ALTER TABLE generations ADD COLUMN deleted_at TIMESTAMP;
-- Queries filter WHERE deleted_at IS NULL
```

### Logging Patterns

**Structured Logging Format:**
```python
import logging
import json

logger = logging.getLogger(__name__)

# Log with structured context
logger.info(
    "Story generation complete",
    extra={
        "session_id": session.id,
        "user_id": user.id,
        "duration_ms": duration,
        "quality_score": score,
        "framework": "AIDA"
    }
)
```

**Output (JSON for parsing):**
```json
{
  "timestamp": "2025-11-22T10:30:00Z",
  "level": "INFO",
  "message": "Story generation complete",
  "session_id": "abc123",
  "user_id": "user456",
  "duration_ms": 1250,
  "quality_score": 8.5,
  "framework": "AIDA"
}
```

**Log Levels:**
- **DEBUG:** Detailed diagnostic info (enabled in development)
- **INFO:** General informational messages (default in production)
- **WARNING:** Unexpected but handled situations
- **ERROR:** Errors that require attention
- **CRITICAL:** System-critical failures

### Configuration Patterns

**Configuration Files (YAML):**
```yaml
# backend/app/config/pipelines/default.yaml
pipeline:
  name: "default"
  stages:
    - name: "story"
      enabled: true
      max_iterations: 3
      timeout_seconds: 120

    - name: "reference_images"
      enabled: true
      count: 3
      quality_threshold: 0.7

    - name: "scenes"
      enabled: true
      max_iterations: 2
      timeout_seconds: 180

    - name: "videos"
      enabled: true
      parallel: true
      max_concurrent: 5
      timeout_seconds: 600

quality:
  vbench:
    enabled: true
    run_in_background: true
    threshold_good: 80
    threshold_acceptable: 60
```

**LLM Prompts (YAML):**
```yaml
# backend/app/config/prompts/story_director.yaml
system_prompt: |
  You are an expert advertising story director...

user_prompt_template: |
  Create a {framework} advertising story for:

  Product/Service: {product}
  Target Audience: {audience}
  Key Message: {message}

  Requirements:
  - {requirements}
```

**Loading Configuration:**
```python
# backend/app/services/unified_pipeline/config_loader.py
import yaml
from pathlib import Path

def load_pipeline_config(name: str = "default") -> PipelineConfig:
    config_path = Path(__file__).parent.parent / f"config/pipelines/{name}.yaml"
    with open(config_path) as f:
        data = yaml.safe_load(f)
    return PipelineConfig(**data)  # Pydantic validation
```

---

## Data Architecture

**Complete database schema with relationships:**

```sql
-- Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    api_token VARCHAR(255) UNIQUE,  -- For CLI authentication
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Generations Table (Main pipeline execution record)
CREATE TABLE generations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),

    -- Input
    prompt TEXT NOT NULL,
    framework VARCHAR(50),  -- AIDA, PAS, FAB, custom
    brand_assets JSONB,     -- Uploaded brand images (S3 URLs)

    -- Pipeline State
    status VARCHAR(50) NOT NULL,  -- pending, story, references, scenes, videos, completed, failed
    current_stage VARCHAR(50),

    -- Outputs
    story_text TEXT,
    story_quality_score FLOAT,
    reference_images JSONB,  -- Array of {url, analysis} objects
    scenes JSONB,            -- Array of scene objects with descriptions
    video_clips JSONB,       -- Array of {scene_id, url, duration} objects
    final_video_url TEXT,
    overall_quality_score FLOAT,

    -- Metadata
    config JSONB,            -- Pipeline configuration used
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX idx_generations_user_id ON generations(user_id);
CREATE INDEX idx_generations_status ON generations(status);
CREATE INDEX idx_generations_created_at ON generations(created_at DESC);

-- Generation Groups (for A/B testing variants)
CREATE TABLE generation_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(255),
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE generation_group_members (
    group_id UUID NOT NULL REFERENCES generation_groups(id),
    generation_id UUID NOT NULL REFERENCES generations(id),
    variant_name VARCHAR(100),  -- e.g., "fear-based", "aspiration"
    PRIMARY KEY (group_id, generation_id)
);

-- Quality Metrics (Detailed VBench scores)
CREATE TABLE quality_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    generation_id UUID NOT NULL REFERENCES generations(id),
    clip_index INT,  -- NULL for overall video score, 0-N for individual clips

    -- VBench Metrics
    overall_score FLOAT,
    composition_score FLOAT,
    coherence_score FLOAT,
    motion_score FLOAT,
    visual_appeal_score FLOAT,

    -- Metadata
    scored_at TIMESTAMP NOT NULL DEFAULT NOW(),
    scoring_duration_ms INT
);

CREATE INDEX idx_quality_metrics_generation_id ON quality_metrics(generation_id);

-- Brand Styles (Reusable brand assets)
CREATE TABLE brand_styles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    logo_url TEXT,
    color_palette JSONB,  -- Array of hex colors
    fonts JSONB,          -- Font family, weights
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Product Images (Brand asset library)
CREATE TABLE product_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    brand_style_id UUID REFERENCES brand_styles(id),
    url TEXT NOT NULL,
    type VARCHAR(50),  -- product, character, logo, misc
    tags TEXT[],       -- Searchable tags
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_product_images_user_id ON product_images(user_id);
CREATE INDEX idx_product_images_brand_style_id ON product_images(brand_style_id);
```

**Key Relationships:**
- **User → Generations:** One-to-many (user can have multiple generations)
- **Generation → QualityMetrics:** One-to-many (one overall + N clip scores)
- **Generation → GenerationGroup:** Many-to-many (variants in A/B testing)
- **User → BrandStyles:** One-to-many (user's brand library)
- **BrandStyle → ProductImages:** One-to-many (brand assets)

---

## API Contracts

### Unified Pipeline Endpoint

**POST /api/v2/generate**

**Purpose:** Unified endpoint for all pipeline execution (replaces 4 separate endpoints)

**Request:**
```json
{
  "prompt": "Create a 30-second ad for eco-friendly water bottle",
  "framework": "AIDA",  // Optional: AIDA, PAS, FAB, custom
  "brand_assets": {
    "product_images": ["s3://bucket/product1.jpg", "s3://bucket/product2.jpg"],
    "logo": "s3://bucket/logo.png",
    "character_images": []
  },
  "config": {
    "parallel_variants": 1,  // 1 = single generation, 3 = A/B test 3 variants
    "quality_threshold": 0.8,
    "enable_vbench": true
  },
  "interactive": true,  // true = wait for user feedback, false = automated
  "session_id": "abc123"  // Optional: resume existing session
}
```

**Response (202 Accepted - Async):**
```json
{
  "data": {
    "generation_id": "gen_abc123",
    "session_id": "session_xyz789",
    "websocket_url": "wss://api.example.com/ws/session_xyz789",
    "status": "pending"
  },
  "status": "success",
  "message": "Generation started. Connect to WebSocket for real-time updates."
}
```

**WebSocket Updates:**
```json
// Story generated
{
  "type": "story_generated",
  "payload": {
    "story_text": "...",
    "quality_score": 8.5,
    "awaiting_approval": true
  }
}

// Reference images ready
{
  "type": "reference_images_ready",
  "payload": {
    "images": [
      {"url": "s3://...", "type": "product"},
      {"url": "s3://...", "type": "character"},
      {"url": "s3://...", "type": "logo"}
    ]
  }
}

// Scenes generated
{
  "type": "scenes_generated",
  "payload": {
    "scenes": [
      {"id": 1, "description": "...", "duration": 6},
      {"id": 2, "description": "...", "duration": 6}
    ],
    "awaiting_approval": true
  }
}

// Video clip progress (parallel generation)
{
  "type": "video_progress",
  "payload": {
    "clip_id": 1,
    "progress": 45,  // Percentage
    "status": "rendering"
  }
}

// Video clip complete
{
  "type": "video_complete",
  "payload": {
    "clip_id": 1,
    "url": "s3://...",
    "duration": 6.2
  }
}

// VBench score available (background, non-blocking)
{
  "type": "vbench_score",
  "payload": {
    "clip_id": 1,
    "overall_score": 82.5,
    "breakdown": {
      "composition": 85,
      "coherence": 80,
      "motion": 78,
      "visual_appeal": 87
    }
  }
}

// Final video stitched
{
  "type": "generation_complete",
  "payload": {
    "generation_id": "gen_abc123",
    "final_video_url": "s3://...",
    "clips": [...],
    "overall_quality_score": 83.2
  }
}
```

### WebSocket Interactive Communication

**WS /ws/{session_id}**

**Client → Server (User Feedback):**
```json
{
  "type": "user_feedback",
  "payload": {
    "message": "make the first scene more dramatic",
    "stage": "scenes",
    "scene_id": 1  // Optional: for scene-specific feedback
  }
}
```

**Server → Client (System Response):**
```json
{
  "type": "feedback_acknowledged",
  "payload": {
    "action": "regenerate_scene",  // approve, regenerate, refine
    "scene_id": 1
  }
}

// Then follow-up with updated scene
{
  "type": "scene_updated",
  "payload": {
    "scene_id": 1,
    "description": "Updated dramatic scene description..."
  }
}
```

### Other Key Endpoints

**GET /api/generations**
- List all user generations with filtering (status, date, quality_score)

**GET /api/generations/{id}**
- Get full generation details including all outputs

**GET /api/generations/{id}/download**
- Get pre-signed S3 URL for final video download

**POST /api/assets/upload**
- Upload brand assets (products, logo, characters)
- Returns S3 URLs for use in generation requests

**GET /health**
- Health check endpoint for monitoring
- Returns: API status, database connection, Redis connection, background task queue status

---

## Security Architecture

**Authentication & Authorization:**
- **JWT Tokens:** 30-day expiration, refresh token support
- **Password Hashing:** bcrypt with 12 rounds
- **API Tokens:** For CLI access, user-revocable
- **Rate Limiting:** 10 generations/hour per user (configurable)

**API Key Protection:**
- **Environment Variables:** OPENAI_API_KEY, REPLICATE_API_TOKEN stored in .env (never in code/DB)
- **Backend-Only:** All AI service calls from backend, never expose keys to frontend
- **Cost Monitoring:** Track API usage per user, alert on unusual spikes

**Input Validation:**
- **Pydantic Schemas:** All API requests validated with Pydantic models
- **File Upload:** Max 10MB per file, 50MB total per generation
- **Prompt Length:** Max 5000 characters
- **File Type Validation:** Allowed image types: jpg, png, webp

**Data Privacy:**
- **Private by Default:** User content not publicly accessible
- **S3 Pre-Signed URLs:** 24-hour expiration
- **GDPR Compliance:** Users can delete all their data
- **No Sensitive Logging:** Passwords, API keys never logged

**Transport Security:**
- **HTTPS:** All production traffic over TLS
- **WSS:** WebSocket Secure for real-time communication
- **HSTS:** Strict-Transport-Security header enabled

---

## Performance Considerations

**Target Performance:**
- Total generation time: < 10 minutes (95th percentile)
- WebSocket latency: < 200ms
- API response time: < 500ms (P95 for non-generation endpoints)
- UI responsiveness: 60fps (16ms frame time)

**Optimization Strategies:**

**1. Parallel Video Generation:**
- Generate all scene clips simultaneously using asyncio
- Total time = longest clip (~1 min), not sum of all clips (~5 min)
- Reduces video generation stage from 5 minutes → 1 minute (5x improvement)

**2. Background VBench Scoring:**
- Run VBench in FastAPI BackgroundTasks (separate thread pool)
- User can download/navigate while scoring completes
- Scores stream in via WebSocket as they become available

**3. Frontend Code Splitting:**
- Lazy load routes (`React.lazy()` + `Suspense`)
- Reduces initial bundle size, faster page load

**4. Media Asset Optimization:**
- Lazy load images in chat feed (only render in viewport)
- Video thumbnails load before full video files
- S3 pre-signed URL generation < 100ms

**5. Database Indexing:**
- Indexes on `user_id`, `status`, `created_at` for fast queries
- Connection pooling for concurrent requests

**6. Redis Session Caching:**
- WebSocket session state in Redis (fast in-memory access)
- Reduces database load for session lookups

---

## Deployment Architecture

**Production Environment (AWS):**

```
Internet
   ↓
Nginx (EC2 - Reverse Proxy)
   ├─→ FastAPI Backend (EC2 - uvicorn)
   ├─→ Frontend Static Files (S3 + CloudFront optional)
   └─→ WebSocket Connections (FastAPI native WS)

FastAPI Backend
   ├─→ PostgreSQL (AWS RDS)
   ├─→ Redis (ElastiCache or EC2)
   ├─→ S3 (Media Storage)
   ├─→ OpenAI API
   └─→ Replicate API
```

**Deployment Process:**
1. SSH to EC2 instance
2. Pull latest code from Git
3. Install Python dependencies (`pip install -r requirements.txt`)
4. Run database migrations (`alembic upgrade head`)
5. Build frontend (`npm run build`)
6. Copy frontend dist to Nginx static file location
7. Restart FastAPI service (`systemctl restart fastapi`)
8. Restart Nginx (`systemctl restart nginx`)

**Environment Variables (.env):**
```bash
# Database
DATABASE_URL=postgresql://user:pass@rds-host:5432/dbname

# Redis
REDIS_URL=redis://redis-host:6379/0

# AI Services
OPENAI_API_KEY=sk-...
REPLICATE_API_TOKEN=r8_...

# AWS
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_BUCKET=admint-videos

# App Config
SECRET_KEY=random-secret-key
ENVIRONMENT=production
CORS_ORIGINS=https://example.com
```

---

## Development Environment

**Prerequisites:**
- Python 3.11+
- Node.js 18+
- PostgreSQL (or use SQLite for local dev)
- Redis (optional for local dev, will fallback to in-memory)

**Setup Commands:**

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with API keys

# Initialize database
python -m app.db.init_db
python create_demo_user.py

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install

# Run development server
npm run dev  # Starts on http://localhost:5173

# Run tests
npm test

# Build for production
npm run build
```

**Running Full Stack Locally:**
1. Terminal 1: `cd backend && uvicorn app.main:app --reload`
2. Terminal 2: `cd frontend && npm run dev`
3. Open http://localhost:5173
4. Login with demo credentials (from create_demo_user.py)

---

## Architecture Decision Records (ADRs)

### ADR-001: FastAPI BackgroundTasks vs Celery for MVP

**Decision:** Use FastAPI BackgroundTasks for VBench scoring and video stitching in MVP

**Context:**
- PRD requires non-blocking VBench scoring (NFR-P9)
- Need background task execution for CPU-intensive operations
- Options: Celery (robust, complex) vs BackgroundTasks (simple, built-in)

**Rationale:**
- BackgroundTasks adequate for MVP use cases (VBench runs after video completes, no retry needed)
- Zero additional dependencies (no Redis broker, no Celery workers to manage)
- Brownfield project already has working code, want simplicity for consolidation
- Can migrate to Celery post-MVP if task persistence/retry becomes critical

**Consequences:**
- ✅ Simpler deployment (no Celery workers, no broker configuration)
- ✅ Adequate for MVP (VBench scoring, video stitching)
- ❌ Tasks don't survive server restarts (acceptable - VBench can be re-run)
- ❌ No built-in retry logic (acceptable - manual regeneration available)

**Migration Path:** If task persistence becomes critical, add Celery with Redis broker post-MVP

---

### ADR-002: FastAPI Native WebSocket vs Socket.io

**Decision:** Use FastAPI's native WebSocket implementation

**Context:**
- Interactive pipeline requires real-time bidirectional communication
- Existing codebase already using FastAPI native WebSocket (backend/app/api/routes/websocket.py)
- Options: Continue with native WebSocket vs migrate to Socket.io

**Rationale:**
- Already implemented and working in existing Interactive pipeline
- No additional backend dependencies (Socket.io requires python-socketio library)
- FastAPI native WebSocket supports async/await patterns
- Auto-reconnect implemented on frontend (frontend/src/services/websocket.ts)
- Zero migration cost (brownfield consolidation)

**Consequences:**
- ✅ No new dependencies, uses existing implementation
- ✅ Native async/await support in FastAPI
- ✅ Frontend already has auto-reconnect logic
- ❌ No built-in room/namespace support (not needed for MVP)
- ❌ No automatic fallback to polling (acceptable - modern browsers support WebSocket)

---

### ADR-003: Tailwind CSS 3.4+ vs 4.0+

**Decision:** Recommend Tailwind CSS 3.4+ for stability, but current 4.1.17 is acceptable

**Context:**
- Existing frontend already using Tailwind CSS 4.1.17
- Tailwind CSS 4.0 is very new (released recently)
- Options: Downgrade to stable 3.4.x vs continue with 4.1.17

**Rationale:**
- v4 has significant API changes from v3, potential ecosystem compatibility issues
- v3.4.x is battle-tested in production
- However, frontend already on v4.1.17 and working - migration backward is effort

**Decision:** Accept existing v4.1.17, no downgrade needed unless issues arise

**Consequences:**
- ✅ No migration effort required
- ✅ Access to latest Tailwind features
- ⚠️ Potential ecosystem plugin compatibility issues (monitor)
- 🔄 Can downgrade to v3.4.x post-consolidation if stability issues emerge

---

### ADR-004: Parallel Video Generation Architecture

**Decision:** Use asyncio concurrent execution for all scene video clips

**Context:**
- Sequential video generation too slow (5 clips × 1 min each = 5 minutes)
- Replicate API supports concurrent requests
- Need to generate 3-10 video clips per ad

**Rationale:**
- Dramatic speed improvement: Total time = longest clip (~1 min), not sum (~5 min)
- asyncio built-in, no extra dependencies
- Replicate API rate limits handled with semaphore (max 5-10 concurrent)
- Frontend displays per-clip progress (better UX than waiting 5 minutes)

**Implementation:**
```python
async def generate_all_videos_parallel(scenes: List[Scene]) -> List[VideoResult]:
    semaphore = asyncio.Semaphore(5)  # Max 5 concurrent Replicate calls

    async def generate_with_limit(scene):
        async with semaphore:
            return await replicate_api.generate_video(scene)

    tasks = [generate_with_limit(scene) for scene in scenes]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

**Consequences:**
- ✅ 5x speed improvement (5 min → 1 min for 5 clips)
- ✅ Better UX (see all clips progressing simultaneously)
- ✅ Scales to A/B testing (parallel pipeline executions)
- ⚠️ Replicate API rate limits (mitigated with semaphore)
- ⚠️ Partial failure handling (retry failed clips individually)

---

### ADR-005: Configuration-Driven vs Hardcoded Prompts

**Decision:** Externalize all LLM prompts to YAML configuration files

**Context:**
- Master Mode has hardcoded prompts in Python code
- Need to support multiple advertising frameworks (AIDA, PAS, FAB)
- Want to iterate on prompts without code changes

**Rationale:**
- Configuration-driven architecture (NFR-M1 requirement)
- Prompt engineering is iterative - avoid code changes for every tweak
- Support multiple frameworks without duplicating code
- Easier for non-developers to modify prompts

**Implementation:**
```yaml
# backend/app/config/prompts/story_director.yaml
system_prompt: |
  You are an expert advertising story director...

user_prompt_template: |
  Create a {framework} advertising story for:
  Product: {product}
  ...
```

**Consequences:**
- ✅ Prompt iteration without code changes
- ✅ Easy framework customization (AIDA vs PAS)
- ✅ Non-developers can modify prompts
- ⚠️ Requires Pydantic validation for template variables
- ⚠️ Initial migration effort from hardcoded Master Mode prompts

---

_Generated by BMAD Decision Architecture Workflow v1.0_
_Date: 2025-11-22_
_For: BMad_
