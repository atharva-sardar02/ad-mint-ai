# Source Tree Analysis - Ad Mint AI

**Generated:** 2025-11-22
**Project Root:** `/Users/kalin.ivanov/rep/ad-mint-ai`

---

## Project Structure Overview

```
ad-mint-ai/
├── backend/                     # Python FastAPI backend (main application)
├── frontend/                    # React + TypeScript frontend
├── deployment/                  # Infrastructure and deployment configs
├── llm-enhancer-atharva/       # Documentation: LLM workflow documentation
├── master-mode/                 # Documentation: Master mode feature context
├── memory-bank/                 # Documentation: Project context storage
├── docs/                        # Generated documentation (this folder)
│   └── archive-pre-consolidation/  # Old docs from multiple workflows
├── .bmad/                       # BMad workflow system
├── .claude/                     # Claude Code configuration
├── .codex/                      # Codex configuration
└── README.md                    # Main project README
```

---

## Backend (`backend/`)

**Type:** Python FastAPI API Server
**Entry Point:** `backend/app/main.py`

```
backend/
├── app/                         # Main application package
│   ├── main.py                 # ⭐ FastAPI application entry point
│   │
│   ├── api/                    # API layer
│   │   ├── routes/             # Route handlers (controllers)
│   │   │   ├── auth.py         # Authentication endpoints
│   │   │   ├── brand_styles.py # Brand style management
│   │   │   ├── editor.py       # Video editor endpoints
│   │   │   ├── generations.py  # ⭐ Original pipeline (large file ~3400 lines)
│   │   │   ├── generations_with_image.py  # Image-enhanced generation
│   │   │   ├── interactive_generation.py  # ⭐ Interactive pipeline
│   │   │   ├── master_mode.py  # ⭐ Master mode pipeline
│   │   │   ├── master_mode_progress.py  # Progress streaming for master mode
│   │   │   ├── products.py     # Product image management
│   │   │   ├── users.py        # User management
│   │   │   └── websocket.py    # WebSocket connections
│   │   └── deps.py             # Dependency injection (get_current_user, etc.)
│   │
│   ├── core/                   # Core utilities
│   │   ├── config.py           # Configuration management (env vars, settings)
│   │   ├── security.py         # Password hashing, JWT token creation
│   │   ├── logging.py          # Structured logging setup
│   │   └── rate_limit.py       # Rate limiting utilities
│   │
│   ├── db/                     # Database layer
│   │   ├── base.py             # Database engine and Base class
│   │   ├── session.py          # Session management (get_db dependency)
│   │   ├── init_db.py          # Database initialization script
│   │   ├── models/             # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── user.py         # User model
│   │   │   ├── generation.py  # ⭐ Generation & GenerationGroup models
│   │   │   ├── editing_session.py  # Video editor sessions
│   │   │   ├── brand_style.py  # Brand style extraction
│   │   │   ├── product_image.py # Product images
│   │   │   ├── quality_metric.py # Quality scoring
│   │   │   └── uploaded_image.py
│   │   └── migrations/         # Database migrations
│   │       ├── add_conversation_history.py
│   │       ├── add_coherence_settings.py
│   │       ├── create_brand_product_image_tables.py
│   │       └── run_all.py      # Run all migrations
│   │
│   ├── schemas/                # Pydantic schemas (request/response validation)
│   │   ├── auth.py             # Auth schemas
│   │   ├── user.py             # User schemas
│   │   ├── generation.py       # Generation schemas
│   │   ├── editor.py           # Editor schemas
│   │   ├── brand_style.py      # Brand style schemas
│   │   ├── product_image.py    # Product image schemas
│   │   └── interactive.py      # Interactive pipeline schemas
│   │
│   └── services/               # ⭐ Business logic layer (pipelines)
│       │
│       ├── master_mode/        # ⭐ Master Mode Pipeline (Agent System)
│       │   ├── __init__.py
│       │   ├── story_generator.py      # Story Director agent
│       │   ├── story_critic.py         # Story Critic agent
│       │   ├── story_director.py       # Orchestrates story generation
│       │   ├── scene_generator.py      # Scene Writer agent
│       │   ├── scene_critic.py         # Scene Critic agent
│       │   ├── scene_cohesor.py        # Scene Cohesor agent
│       │   ├── scene_enhancer.py       # Scene enhancement with vision
│       │   ├── scene_writer.py         # Scene writing logic
│       │   ├── scene_to_video.py       # Convert scenes to video params
│       │   ├── appearance_sanitizer.py # Ensure character consistency
│       │   ├── video_generation.py     # Parallel video generation
│       │   ├── video_stitcher.py       # Stitch scene videos together
│       │   ├── streaming_wrapper.py    # Real-time progress streaming
│       │   ├── schemas.py              # Master mode Pydantic schemas
│       │   └── test_appearance_sanitizer.py
│       │
│       ├── pipeline/           # ⭐ Original + Interactive Pipeline Services
│       │   ├── interactive_pipeline.py  # ⭐ Interactive orchestrator
│       │   ├── conversation_handler.py  # Chat-based feedback processing
│       │   ├── multi_stage_orchestrator.py  # Original pipeline orchestrator
│       │   ├── fill_in_orchestrator.py      # Fill-in template system
│       │   │
│       │   ├── prompt_enhancement.py        # LLM prompt enhancement
│       │   ├── image_prompt_enhancement.py
│       │   ├── video_prompt_enhancement.py
│       │   ├── storyboard_prompt_enhancement.py
│       │   ├── kling_stage3_prompt_enhancer.py
│       │   │
│       │   ├── story_generator.py       # Story generation
│       │   ├── story_templates.py       # PAS/BAB/AIDA templates
│       │   ├── prompt_generator.py      # Generate prompts from story
│       │   ├── scene_planning.py        # Scene breakdown
│       │   ├── scene_divider.py
│       │   ├── scene_assembler.py
│       │   │
│       │   ├── image_generation.py      # Image generation (Flux)
│       │   ├── image_generation_batch.py
│       │   ├── video_generation_cli.py  # Video generation
│       │   ├── inpainting_service.py    # Image editing/inpainting
│       │   │
│       │   ├── storyboard_service.py    # Storyboard creation
│       │   ├── storyboard_generator.py
│       │   ├── brand_style_extractor.py # Extract brand from images
│       │   │
│       │   ├── quality_control.py       # Quality scoring
│       │   ├── image_quality_scoring.py
│       │   │
│       │   ├── overlays.py              # Text overlays on video
│       │   ├── audio.py                 # Audio/music addition
│       │   ├── export.py                # Final video export
│       │   ├── seed_manager.py          # Seed/consistency control
│       │   ├── cache.py                 # Caching layer
│       │   ├── progress_tracking.py     # Progress updates
│       │   ├── time_estimation.py       # Estimate generation time
│       │   └── llm_client.py            # OpenAI client wrapper
│       │
│       ├── editor/             # Video editor services
│       │   ├── editor_service.py
│       │   ├── trim_service.py
│       │   ├── split_service.py
│       │   ├── merge_service.py
│       │   ├── save_service.py
│       │   └── export_service.py
│       │
│       ├── storage/            # Storage abstraction
│       │   └── s3_storage.py   # S3 upload/download
│       │
│       ├── image_generation.py       # Image generation orchestrator
│       ├── video_generation_standalone.py
│       ├── coherence_settings.py     # Coherence technique management
│       ├── cost_tracking.py          # Track API costs
│       └── cancellation.py           # Generation cancellation
│
├── assets/                     # Asset storage
│   ├── music/                  # Background music files
│   ├── sfx/                    # Sound effects
│   └── users/                  # User-uploaded assets
│       ├── {user_id}/
│       │   ├── brand_styles/   # Brand style images
│       │   └── products/       # Product images
│
├── cli_tools/                  # ⭐ CLI Pipeline (Standalone)
│   ├── pipeline.py             # Main CLI orchestrator
│   ├── create_storyboard.py    # Storyboard CLI
│   ├── generate_images.py      # Image generation CLI
│   ├── generate_videos.py      # Video generation CLI
│   ├── enhance_image_prompt.py
│   ├── enhance_video_prompt.py
│   ├── README.md
│   ├── COMMANDS.md
│   └── QUICKSTART.md
│
├── temp/                       # Temporary generation files
│   └── master_mode/            # Master mode temp storage
│       └── {user_id}/
│           └── {generation_id}/
│               ├── reference_1_*.jpg
│               ├── reference_2_*.jpg
│               ├── reference_3_*.jpg
│               ├── scene_videos/
│               │   ├── scene_01.mp4
│               │   ├── scene_02.mp4
│               │   └── scene_03.mp4
│               └── final_video_*.mp4
│
├── output/                     # Output storage (original pipeline)
│   ├── videos/
│   └── thumbnails/
│
├── tests/                      # Backend tests
│   ├── test_auth_routes.py
│   ├── test_generation_routes.py
│   ├── test_cost_tracking.py
│   └── test_conversation_handler.py
│
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (not in git)
├── .env.example                # Environment template
├── ad_mint_ai.db               # SQLite database (development)
└── venv/                       # Python virtual environment
```

### Critical Backend Files

| File | Purpose | Lines |
|------|---------|-------|
| `app/main.py` | FastAPI app entry, CORS, middleware, routes | ~293 |
| `app/api/routes/master_mode.py` | Master mode pipeline endpoint | ~418 |
| `app/api/routes/interactive_generation.py` | Interactive pipeline endpoints | ~612 |
| `app/api/routes/generations.py` | Original pipeline (complex, needs refactor) | ~3400+ |
| `app/services/master_mode/story_director.py` | Story generation orchestrator | ~179 |
| `app/services/master_mode/video_stitcher.py` | Video assembly logic | ~200+ |
| `app/services/pipeline/interactive_pipeline.py` | Interactive orchestrator | Large |
| `app/db/models/generation.py` | Main data model | ~79 |

---

## Frontend (`frontend/`)

**Type:** React + TypeScript SPA
**Entry Point:** `frontend/src/main.tsx`
**Build Tool:** Vite

```
frontend/
├── src/
│   ├── main.tsx                # ⭐ Application entry point
│   ├── App.tsx                 # Root component with routing
│   ├── index.css               # Global styles (Tailwind)
│   │
│   ├── routes/                 # Page-level route components
│   │   ├── Auth/
│   │   │   ├── Login.tsx       # Login page
│   │   │   └── Register.tsx    # Registration page
│   │   ├── Dashboard.tsx       # Main dashboard (original pipeline)
│   │   ├── Gallery.tsx         # Video gallery
│   │   ├── Profile.tsx         # User profile
│   │   ├── VideoDetail.tsx     # Video detail view
│   │   └── MasterMode.tsx      # ⭐ Master mode UI
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   └── Navbar.tsx      # Top navigation bar
│   │   │
│   │   ├── ui/                 # Reusable UI components
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Textarea.tsx
│   │   │   ├── ErrorMessage.tsx
│   │   │   └── LoadingSpinner.tsx
│   │   │
│   │   ├── generation/         # ⭐ Pipeline-specific components
│   │   │   ├── InteractivePipeline.tsx  # ⭐ Interactive mode UI (buggy WebSocket)
│   │   │   ├── ChatInterface.tsx         # Chat feedback interface
│   │   │   ├── StoryReview.tsx           # Story review/approval
│   │   │   ├── ImageReview.tsx           # Image review/selection
│   │   │   ├── ImageEditor.tsx           # Image inpainting editor
│   │   │   ├── VideoGallery.tsx          # Video grid display
│   │   │   ├── ComparisonView.tsx        # A/B comparison view
│   │   │   └── ParallelGenerationPanel.tsx
│   │   │
│   │   ├── master-mode/        # ⭐ Master mode components
│   │   │   ├── ProgressTracker.tsx       # Progress visualization
│   │   │   ├── LLMConversationViewer.tsx # Agent conversation display
│   │   │   ├── VideoPlayer.tsx           # Video playback
│   │   │   └── ConversationHistory.tsx
│   │   │
│   │   └── ProtectedRoute.tsx  # Auth-required route wrapper
│   │
│   ├── store/                  # Zustand state management
│   │   └── authStore.ts        # Authentication state (user, token, login/logout)
│   │
│   ├── lib/                    # Utilities and services
│   │   ├── apiClient.ts        # ⭐ Axios instance with interceptors
│   │   ├── authService.ts      # Auth API calls (login, register, getMe)
│   │   ├── generationService.ts # Original pipeline API calls
│   │   ├── interactive-api.ts  # Interactive pipeline API calls
│   │   ├── config.ts           # API endpoints config
│   │   └── types/              # TypeScript type definitions
│   │       └── pipeline.ts     # Pipeline-related types
│   │
│   └── __tests__/              # Frontend tests
│       ├── setup.ts            # Vitest setup
│       ├── Dashboard.test.tsx
│       └── generationService.test.ts
│
├── public/                     # Static assets
│   └── vite.svg                # Vite logo
│
├── dist/                       # Build output (generated)
├── node_modules/               # NPM dependencies
├── package.json                # NPM package configuration
├── package-lock.json           # Dependency lock file
├── tsconfig.json               # TypeScript configuration
├── tsconfig.app.json           # App-specific TS config
├── tsconfig.node.json          # Node-specific TS config
├── vite.config.ts              # ⭐ Vite build configuration
├── eslint.config.js            # ESLint configuration
├── postcss.config.js           # PostCSS configuration (Tailwind)
├── .prettierrc                 # Prettier formatting config
└── README.md                   # Frontend-specific README
```

### Critical Frontend Files

| File | Purpose | Lines |
|------|---------|-------|
| `src/main.tsx` | App entry, React render | ~10 |
| `src/App.tsx` | Router setup, global layout | ~100+ |
| `src/routes/MasterMode.tsx` | Master mode UI with progress tracking | Medium |
| `src/components/generation/InteractivePipeline.tsx` | Interactive pipeline UI | Large |
| `src/lib/apiClient.ts` | Axios setup, auth interceptors | ~50 |
| `src/store/authStore.ts` | Auth state management | ~50 |

---

## Deployment (`deployment/`)

**Type:** Infrastructure as Code + Scripts
**Target:** AWS EC2 + RDS + S3

```
deployment/
├── deploy.sh                   # ⭐ Main deployment automation script
├── fastapi.service             # Systemd service file for FastAPI
├── nginx.conf                  # Nginx reverse proxy configuration
├── user-data.sh                # EC2 user data script
│
├── setup-rds.sh                # PostgreSQL RDS setup
├── setup-s3-videos.sh          # S3 bucket for video storage
├── setup-s3-frontend.sh        # S3 bucket for frontend hosting
│
├── scripts/                    # Helper scripts
│   ├── backup.sh
│   ├── restore.sh
│   └── health-check.sh
│
├── production/                 # Production-specific configs
│   ├── .env.production
│   └── docker-compose.prod.yml
│
├── logrotate-fastapi           # Log rotation config
├── lifecycle-policy.json       # S3 lifecycle policy
├── temp-bucket-policy.json     # S3 bucket policy
├── temp-cors-config.json       # S3 CORS configuration
│
├── DEPLOY_CHECKLIST.md         # Deployment checklist
└── README.md                   # Deployment guide
```

---

## Documentation Folders

### llm-enhancer-atharva/

**Purpose:** Documentation for the LLM-based image/video generation workflow (by Atharva)

```
llm-enhancer-atharva/
├── README.md                   # Overview
├── workflow-overview.md        # Complete workflow explanation
├── models-and-services.md      # AI models used
├── consistency-system.md       # Visual consistency approach
├── implementation-details.md   # Technical details
├── sequential-image-generation.md
├── complete-pipeline-flow-diagram.md
├── CHANGELOG.md
└── test-results-*.md           # Test results documentation
```

### master-mode/

**Purpose:** Master mode feature documentation and context (non-BMad workflow)

```
master-mode/
├── README.md                   # Master mode overview
├── projectbrief.md             # Initial project brief
├── progress.md                 # Development progress
├── activeContext.md            # Current working context
├── techContext.md              # Technical context
├── productContext.md           # Product requirements context
├── systemPatterns.md           # System design patterns
│
├── vision-integration.md       # Vision AI integration
├── scene-generation-summary.md
├── video-generation-stitching.md
├── agent-sequence-reference.md # LLM agent workflow
│
├── IMPLEMENTATION_COMPLETE.md
├── FIXES_APPLIED_SUMMARY.md
├── API_INTEGRATION.md
└── *_FIX.md                    # Various fix documentation
```

### memory-bank/

**Purpose:** Project memory bank (used by non-BMad workflow)

```
memory-bank/
├── activeContext.md            # Active development context
├── productContext.md           # Product requirements
├── progress.md                 # Progress tracking
├── projectbrief.md             # Project brief
├── systemPatterns.md           # System patterns
└── techContext.md              # Technical context
```

---

## Configuration Files

### Root Level

| File | Purpose |
|------|---------|
| `.gitignore` | Git ignore rules (venv, node_modules, .env, *.db) |
| `README.md` | Main project documentation |
| `.bmad/` | BMad workflow system configuration |
| `.claude/` | Claude Code configuration |
| `.codex/` | Codex configuration |
| `.cursor/` | Cursor IDE configuration |

---

## Integration Points

### Backend ↔ Frontend

**Primary:** REST API (`http://localhost:8000/api/`)
**Real-time:** WebSocket (`ws://localhost:8000/ws/`)

**Flow:**
```
Frontend (React)
    ↓ HTTP Request (axios)
Backend (FastAPI routes)
    ↓ Service layer
Pipeline Services (master_mode, interactive, original)
    ↓ External APIs
OpenAI, Replicate
    ↓ Storage
Database (SQLAlchemy), Files (temp/, output/), S3
```

### Backend ↔ External Services

- **OpenAI API:** GPT-4 for prompt enhancement, story generation, scene planning
- **Replicate API:** Flux (images), Kling (videos), potential SORA access
- **AWS S3:** Video storage (optional, local fallback)
- **PostgreSQL RDS:** Production database (optional, SQLite fallback)

---

## Entry Points Summary

| Component | Entry Point | Command |
|-----------|-------------|---------|
| **Backend** | `backend/app/main.py` | `uvicorn app.main:app --reload` |
| **Frontend** | `frontend/src/main.tsx` | `npm run dev` |
| **CLI Tools** | `backend/cli_tools/pipeline.py` | `python cli_tools/pipeline.py` |
| **Deployment** | `deployment/deploy.sh` | `sudo ./deployment/deploy.sh` |
| **DB Init** | `backend/app/db/init_db.py` | `python -m app.db.init_db` |
| **Migrations** | `backend/app/db/migrations/run_all.py` | `python run_migrations.py` |

---

## Critical Directories for AI Consolidation

Given the user's goal to consolidate 4 pipelines, these are the key directories to analyze:

### Backend Pipelines

1. **Master Mode:** `backend/app/services/master_mode/`
   - 14 Python files
   - Complex agent system (Story Director/Critic, Scene Writer/Critic/Cohesor)
   - Best visual consistency (3 ref images)

2. **Interactive:** `backend/app/services/pipeline/interactive_pipeline.py`
   - User feedback loops
   - Conversational interface
   - WebSocket integration

3. **Original:** `backend/app/api/routes/generations.py` + `backend/app/services/pipeline/*`
   - Quality scoring
   - Comparison groups
   - Legacy orchestrators

4. **CLI:** `backend/cli_tools/`
   - 7 standalone scripts
   - Complete pipeline orchestration
   - No UI dependency

### Frontend Pipelines

1. **Master Mode UI:** `frontend/src/routes/MasterMode.tsx` + `frontend/src/components/master-mode/`
2. **Interactive UI:** `frontend/src/components/generation/InteractivePipeline.tsx` (WebSocket issues)
3. **Original UI:** `frontend/src/routes/Dashboard.tsx` + comparison/gallery components

---

## File Count Summary

| Directory | File Count (approx) |
|-----------|---------------------|
| `backend/app/` | 100+ Python files |
| `frontend/src/` | 50+ TypeScript/TSX files |
| `deployment/` | 15+ config/script files |
| `cli_tools/` | 10+ Python files |
| `docs/` (generated) | 5+ documentation files |
| `docs/archive-pre-consolidation/` | 100+ old docs |

---

## Next Steps for Consolidation

Based on this source tree analysis, the consolidation should focus on:

1. **Merge Pipeline Logic:** Unify `master_mode/`, `interactive_pipeline.py`, and original orchestrators
2. **Standardize API Routes:** Create unified `/api/v2/generate` endpoint that supports all modes
3. **Fix WebSocket Issues:** Stabilize interactive mode WebSocket handling
4. **Preserve Best Features:** Keep master mode consistency + interactive feedback + quality scoring
5. **CLI Integration:** Ensure CLI tools can invoke unified pipeline
6. **Frontend Consolidation:** Create single flexible UI that adapts to pipeline mode
