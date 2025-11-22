# Ad Mint AI - Project Documentation Index

**Project:** Ad Mint AI - AI-Powered Video Advertisement Generator
**Type:** Multi-part Application (Backend API + Frontend Web App + Infrastructure)
**Generated:** 2025-11-22
**Status:** Active Development - Pipeline Consolidation Phase

---

## 🎯 Project Overview

Ad Mint AI is an AI-powered platform that automatically generates professional-quality video advertisements from text prompts using advanced AI models (OpenAI GPT-4, Replicate Flux/Kling) and proven advertising frameworks (AIDA, PAS, FAB).

**Key Capabilities:**
- **Story Generation:** AI-powered narrative creation using multi-agent systems
- **Visual Consistency:** 3-reference-image approach for character/product consistency
- **Interactive Refinement:** User feedback loops at each generation stage
- **Quality Metrics:** Automated image and video quality scoring
- **Multiple Pipelines:** 4 working pipelines with different strengths (consolidation in progress)

---

## 🚨 Critical Context: Pipeline Consolidation

**Current State:** 4 separate working pipelines requiring consolidation

1. **Master Mode Pipeline** ⭐
   - ✅ Best consistency (3 ref images approach)
   - ✅ Complex LLM agent chain (5+ agents)
   - ❌ Hardcoded, inflexible
   - ❌ No user interactivity
   - ❌ Cannot generate images (must provide)

2. **Interactive Pipeline**
   - ✅ User feedback/iteration
   - ✅ Conversational interface
   - ❌ No visual consistency (missing ref images)
   - ⚠️ Buggy UI (WebSocket errors on navigation)

3. **Original Pipeline**
   - ✅ Quality score display
   - ❌ Poor overall quality
   - → Action: Scrap except quality features

4. **CLI Tools**
   - ✅ Standalone command-line capability
   - → Action: Integrate into unified pipeline

**Consolidation Goal:** Unified pipeline combining:
- Master mode's 3-ref-image consistency
- Interactive mode's user feedback
- Quality score displays
- UI + CLI execution options
- Image generation capability
- Flexible, configuration-driven architecture

See [API Contracts](./api-contracts.md) for detailed pipeline comparison.

---

## 📚 Quick Reference

| Category | Technology | Version | Location |
|----------|------------|---------|----------|
| **Backend** | Python + FastAPI | 3.11+, 0.104+ | `backend/` |
| **Frontend** | React + TypeScript + Vite | 19+, 5.9+, 5.4+ | `frontend/` |
| **Database** | SQLAlchemy (SQLite/PostgreSQL) | 2.0+ | `backend/app/db/` |
| **AI Models** | OpenAI GPT-4, Replicate Flux/Kling | - | Via API |
| **Deployment** | AWS (EC2, RDS, S3) + Nginx | - | `deployment/` |

---

## 📖 Core Documentation

### Architecture & Design

| Document | Description |
|----------|-------------|
| [Technology Stack](./technology-stack.md) | Complete technology inventory: frameworks, libraries, AI services |
| [API Contracts](./api-contracts.md) | ⭐ All 4 pipelines documented: endpoints, request/response schemas, comparison matrix |
| [Data Models](./data-models.md) | Database schema: Generation, User, QualityMetric, BrandStyle models |
| [Source Tree Analysis](./source-tree-analysis.md) | Annotated directory structure with critical files highlighted |

### Development

| Document | Description |
|----------|-------------|
| [Development Guide](./development-guide.md) | Setup, running locally, testing, common issues |
| [Deployment Guide](../deployment/README.md) | Production deployment to AWS EC2 + RDS + S3 |

### Existing Documentation (Pre-Consolidation)

| Location | Purpose |
|----------|---------|
| `llm-enhancer-atharva/` | LLM workflow documentation (26 files) |
| `master-mode/` | Master mode implementation context (47+ files) |
| `memory-bank/` | Project memory bank (6 context files) |
| `docs/archive-pre-consolidation/` | **⚠️ Old docs from multiple workflows (100+ files, not trusted)** |

---

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + TypeScript)            │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Master Mode │  │ Interactive  │  │ Original/Gallery │  │
│  │     UI      │  │ Pipeline UI  │  │       UI         │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                Backend (FastAPI)                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              API Layer (Routes)                       │  │
│  │  /master-mode  /interactive  /generations            │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Service Layer (Business Logic)              │  │
│  │  ┌────────────────┐  ┌─────────────┐  ┌───────────┐ │  │
│  │  │  Master Mode   │  │ Interactive │  │  Original │ │  │
│  │  │  (5+ Agents)   │  │   Pipeline  │  │  Pipeline │ │  │
│  │  └────────────────┘  └─────────────┘  └───────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Data Layer (ORM + Database)              │  │
│  │  SQLAlchemy → PostgreSQL/SQLite                       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
┌───────────────┐    ┌──────────────┐    ┌─────────────────┐
│  OpenAI API   │    │ Replicate API│    │   AWS S3        │
│  (GPT-4)      │    │ (Flux, Kling)│    │  (Video Storage)│
└───────────────┘    └──────────────┘    └─────────────────┘
```

### Master Mode Agent System

```
Story Generation (2-Agent System):
┌─────────────────┐
│ Story Director  │──► Generates story draft
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Story Critic   │──► Evaluates (score, improvements)
└────────┬────────┘
         │
         ▼ (iterates until approved)
┌─────────────────┐
│  Final Story    │
└─────────────────┘

Scene Generation (3-Agent System):
┌─────────────────┐
│  Scene Writer   │──► Detailed scene content
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Scene Critic   │──► Evaluates each scene
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Scene Cohesor   │──► Cross-scene consistency
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Final Scenes   │──► Enhanced + Stitched Video
└─────────────────┘
```

---

## 🗂️ Project Structure Quick Reference

```
ad-mint-ai/
│
├── backend/                     # ⭐ Python FastAPI Backend
│   ├── app/
│   │   ├── main.py             # Entry point
│   │   ├── api/routes/         # API endpoints
│   │   │   ├── master_mode.py  # Master mode pipeline
│   │   │   ├── interactive_generation.py  # Interactive pipeline
│   │   │   └── generations.py  # Original pipeline (3400+ lines)
│   │   ├── services/
│   │   │   ├── master_mode/    # 5+ LLM agents (Director, Critic, Writer, Cohesor)
│   │   │   └── pipeline/       # Interactive + original services
│   │   ├── db/
│   │   │   ├── models/         # SQLAlchemy models
│   │   │   └── migrations/     # Database migrations
│   │   └── schemas/            # Pydantic request/response schemas
│   ├── cli_tools/              # ⭐ CLI Pipeline (standalone)
│   ├── tests/                  # Backend tests
│   └── requirements.txt
│
├── frontend/                    # ⭐ React + TypeScript Frontend
│   ├── src/
│   │   ├── main.tsx            # Entry point
│   │   ├── routes/             # Page components
│   │   │   ├── MasterMode.tsx  # Master mode UI
│   │   │   └── Dashboard.tsx   # Original pipeline UI
│   │   ├── components/
│   │   │   ├── generation/     # Pipeline-specific components
│   │   │   │   └── InteractivePipeline.tsx  # Interactive UI (buggy WebSocket)
│   │   │   └── master-mode/    # Master mode components
│   │   ├── store/              # Zustand state
│   │   └── lib/                # API client, services
│   ├── package.json
│   └── vite.config.ts
│
├── deployment/                  # ⭐ Deployment Infrastructure
│   ├── deploy.sh               # Main deployment script
│   ├── nginx.conf              # Reverse proxy config
│   └── fastapi.service         # Systemd service
│
├── docs/                        # 📖 Generated Documentation (You Are Here)
│   ├── index.md                # This file (master index)
│   ├── api-contracts.md        # All 4 pipelines documented
│   ├── data-models.md          # Database schema
│   ├── technology-stack.md     # Tech inventory
│   ├── source-tree-analysis.md # Annotated directory structure
│   ├── development-guide.md    # Setup and development
│   ├── project-scan-report.json # Workflow state
│   └── archive-pre-consolidation/  # Old docs (not trusted)
│
├── llm-enhancer-atharva/        # Documentation: LLM workflow (26 files)
├── master-mode/                 # Documentation: Master mode context (47+ files)
├── memory-bank/                 # Documentation: Project memory (6 files)
│
└── README.md                    # Main project README
```

---

## 🔍 Key Files for AI Analysis

### Backend Pipelines

**Master Mode (Best Consistency):**
- API: `backend/app/api/routes/master_mode.py` (418 lines)
- Agents: `backend/app/services/master_mode/` (14 files)
  - `story_director.py`, `story_critic.py`
  - `scene_writer.py`, `scene_critic.py`, `scene_cohesor.py`
  - `scene_enhancer.py`, `appearance_sanitizer.py`
  - `video_generation.py`, `video_stitcher.py`

**Interactive (User Feedback):**
- API: `backend/app/api/routes/interactive_generation.py` (612 lines)
- Orchestrator: `backend/app/services/pipeline/interactive_pipeline.py`
- UI: `frontend/src/components/generation/InteractivePipeline.tsx`

**Original (Quality Scoring):**
- API: `backend/app/api/routes/generations.py` (3400+ lines, needs refactor)
- Quality: `backend/app/services/pipeline/image_quality_scoring.py`
- Models: `backend/app/db/models/quality_metric.py`

**CLI (Standalone):**
- `backend/cli_tools/pipeline.py` (orchestrator)
- `backend/cli_tools/create_storyboard.py`
- `backend/cli_tools/generate_images.py`
- `backend/cli_tools/generate_videos.py`

### Database Schema

- **Primary Model:** `backend/app/db/models/generation.py`
  - `Generation` class (stores all generation data)
  - `GenerationGroup` class (for A/B comparisons)
- **Quality:** `backend/app/db/models/quality_metric.py`
- **Brand/Product:** `backend/app/db/models/brand_style.py`, `product_image.py`

---

## 🚀 Getting Started

### Quick Start (5 Minutes)

```bash
# 1. Clone and setup backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# 2. Configure API keys
cp .env.example .env
# Edit .env: Add OPENAI_API_KEY and REPLICATE_API_TOKEN

# 3. Initialize database
python -m app.db.init_db
python create_demo_user.py

# 4. Start backend (Terminal 1)
uvicorn app.main:app --reload

# 5. Setup and start frontend (Terminal 2)
cd frontend
npm install
npm run dev

# 6. Open http://localhost:5173 and login with demo/demo1234
```

See [Development Guide](./development-guide.md) for detailed setup.

---

## 📊 Pipeline Comparison Matrix

| Feature | Master Mode | Interactive | Original | CLI Tools |
|---------|-------------|-------------|----------|-----------|
| **Consistency (3 ref images)** | ✅ Best | ❌ None | Partial | ✅ Supported |
| **User Feedback** | ❌ No | ✅ Full | ❌ No | ❌ No |
| **Quality Scores** | ❌ No | ❌ No | ✅ Yes | ❌ No |
| **Image Generation** | ❌ Must provide | ✅ Generates | ✅ Generates | ✅ Generates |
| **LLM Agent Chain** | ✅ Complex (5+) | ✅ Basic | ✅ Basic | ✅ Available |
| **UI Stability** | ✅ Stable | ⚠️ WebSocket bugs | ✅ Stable | ❌ CLI only |
| **Flexibility** | ❌ Hardcoded | ✅ Flexible | ✅ Flexible | ✅ Scriptable |

**Target:** Unified pipeline with all ✅ features and no ❌ weaknesses.

---

## 🗺️ Documentation Map

### For AI Development Agents

When building features or fixing bugs, reference these docs:

**Understanding the System:**
1. Start with [API Contracts](./api-contracts.md) - understand all pipelines
2. Review [Data Models](./data-models.md) - understand database schema
3. Check [Source Tree Analysis](./source-tree-analysis.md) - locate relevant files
4. Reference [Technology Stack](./technology-stack.md) - understand dependencies

**Implementing Changes:**
1. Read [Development Guide](./development-guide.md) - setup environment
2. Follow code patterns from existing pipelines
3. Update database via migrations (`backend/app/db/migrations/`)
4. Add tests (`backend/tests/`, `frontend/src/__tests__/`)

**Pipeline-Specific Work:**
- **Master Mode:** Read `master-mode/` context docs
- **Interactive:** Check `llm-enhancer-atharva/` workflow docs
- **Quality Features:** Review `backend/app/services/pipeline/quality_control.py`
- **CLI:** Check `backend/cli_tools/README.md`

### For Human Developers

**First Time Setup:**
1. [Development Guide](./development-guide.md) - Get running locally
2. [README.md](../README.md) - Project overview

**Feature Development:**
1. [API Contracts](./api-contracts.md) - Understand endpoints
2. [Data Models](./data-models.md) - Understand data
3. [Source Tree Analysis](./source-tree-analysis.md) - Find files

**Deployment:**
1. [Deployment Guide](../deployment/README.md) - AWS deployment

---

## ⚠️ Known Issues

1. **Interactive Pipeline WebSocket Error:**
   - Issue: Navigating away from `/interactive` URL causes WebSocket errors
   - Workaround: Don't navigate away during active session
   - Fix Required: Improve WebSocket reconnection logic

2. **Master Mode Hardcoded Logic:**
   - Issue: Many parameters are hardcoded (iteration limits, thresholds)
   - Fix Required: Move to configuration-driven approach

3. **Original Pipeline Code Size:**
   - Issue: `generations.py` is 3400+ lines, difficult to maintain
   - Fix Required: Refactor into smaller modules

4. **Documentation Fragmentation:**
   - Issue: 100+ old docs in archive, multiple memory banks
   - Status: **This documentation consolidation addresses this issue**

---

## 🎯 Consolidation Roadmap

### Phase 1: Analysis & Planning (Current)
- ✅ Document all 4 pipelines
- ✅ Identify best features from each
- ✅ Create unified architecture plan

### Phase 2: Backend Unification
- Merge master_mode + interactive + original services
- Create `/api/v2/generate` unified endpoint
- Implement flexible reference image system (provide or generate)
- Integrate quality scoring into all pipelines
- Fix WebSocket stability issues

### Phase 3: Frontend Consolidation
- Create unified pipeline UI component
- Support all modes (master/interactive/auto)
- Integrate quality score displays
- Fix navigation/WebSocket bugs

### Phase 4: CLI Integration
- Ensure CLI tools can invoke unified pipeline
- Maintain standalone script capability

### Phase 5: Testing & Migration
- Comprehensive testing of unified pipeline
- Migrate existing generations database
- Update documentation

---

## 📞 Support & Resources

### Documentation Files

| File | Lines | Purpose |
|------|-------|---------|
| `index.md` | This file | Master index and entry point |
| `api-contracts.md` | ~1100 | Complete API documentation for all 4 pipelines |
| `data-models.md` | ~600 | Database schema and ORM models |
| `technology-stack.md` | ~400 | Technology inventory |
| `source-tree-analysis.md` | ~600 | Annotated directory structure |
| `development-guide.md` | ~500 | Setup, running, testing |

### External Resources

- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **React Docs:** https://react.dev/
- **SQLAlchemy Docs:** https://docs.sqlalchemy.org/
- **Vite Docs:** https://vite.dev/
- **OpenAI API:** https://platform.openai.com/docs
- **Replicate API:** https://replicate.com/docs

---

## 🏁 Next Steps

### For New Developers

1. Read [Development Guide](./development-guide.md)
2. Set up local environment
3. Explore master mode pipeline code
4. Review existing documentation in `master-mode/` and `llm-enhancer-atharva/`

### For AI Agents Working on Consolidation

1. **Read All Pipeline Docs:** [API Contracts](./api-contracts.md) sections 1-4
2. **Understand Data Model:** [Data Models](./data-models.md)
3. **Locate Code:** [Source Tree Analysis](./source-tree-analysis.md)
4. **Plan Unified API:** Design `/api/v2/generate` that supports all features
5. **Implement Incrementally:** Start with master mode + quality scores, add interactivity

### For Product Planning

- Review consolidation goals in [API Contracts](./api-contracts.md) "Consolidation Goal" section
- See pipeline comparison matrix (this file, above)
- Review existing feature documentation in `master-mode/progress.md`

---

**Last Updated:** 2025-11-22
**Documentation Version:** 1.0 (Initial Consolidation)
**Next Review:** After Phase 2 completion (backend unification)
