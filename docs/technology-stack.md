# Technology Stack - Ad Mint AI

**Generated:** 2025-11-22
**Project Type:** Multi-part (Backend API + Frontend Web App + Infrastructure)

## Overview

Ad Mint AI is an AI-powered video advertisement generation platform built with a modern full-stack architecture, featuring multiple AI video generation pipelines with visual consistency controls.

---

## Backend (Python FastAPI)

### Core Framework
| Technology | Version | Purpose |
|------------|---------|---------|
| **FastAPI** | 0.104+ | High-performance async web framework |
| **Python** | 3.11+ | Primary backend language |
| **Uvicorn** | 0.24+ | ASGI server with auto-reload |
| **Pydantic** | 2.0+ | Data validation and settings management |

### Database & ORM
| Technology | Version | Purpose |
|------------|---------|---------|
| **SQLAlchemy** | 2.0+ | ORM and database toolkit |
| **SQLite** | - | Development database |
| **PostgreSQL** | - | Production database (via psycopg2-binary, asyncpg) |
| **Alembic** | - | Database migrations |

### Authentication & Security
| Technology | Purpose |
|------------|---------|
| **JWT** (PyJWT 2.8+) | Token-based authentication |
| **bcrypt** (4.0+) | Password hashing |
| **Python-multipart** | Form data handling |

### AI & ML Services
| Technology | Version | Purpose |
|------------|---------|---------|
| **OpenAI** | 1.0+ | GPT models for prompt enhancement, story generation, scene planning |
| **Replicate** | 0.25+ | Video/image generation models (Flux, Kling, SORA access) |
| **Transformers** | 4.30+ | HuggingFace models for quality scoring |
| **PyTorch** | 2.0+ | ML inference |

### Video & Image Processing
| Technology | Version | Purpose |
|------------|---------|---------|
| **MoviePy** | 1.0.3+ | Video editing, composition, export |
| **OpenCV** (opencv-python) | 4.8+ | Image/video manipulation, frame extraction |
| **Pillow** | 10.0+ | Image processing |
| **NumPy** | 1.24+ (< 2.0) | Numerical operations for media processing |

### Cloud & Storage
| Technology | Purpose |
|------------|---------|
| **Boto3** | 1.34+ | AWS S3 integration for video/asset storage |
| **Redis** | 5.0+ | Caching and queue management |

### Testing
| Technology | Purpose |
|------------|---------|
| **Pytest** | 7.4+ | Test framework |
| **Pytest-asyncio** | 0.21+ | Async test support |
| **httpx** | 0.24+ | Async HTTP client for testing |

### API Routes (Pipelines)

The backend exposes multiple pipeline endpoints:

1. **Master Mode Pipeline** (`/api/master_mode`)
   - Location: `backend/app/services/master_mode/`
   - Services: story_generator, story_director, scene_generator, scene_enhancer, scene_critic, appearance_sanitizer, video_generation, video_stitcher
   - Best consistency (3 ref images approach)

2. **Interactive Pipeline** (`/api/v1/interactive`)
   - Location: `backend/app/services/pipeline/interactive_pipeline.py`
   - Features: User feedback loops, conversation handler, iterative refinement
   - WebSocket support for real-time updates

3. **Original Pipeline** (`/api/generations`, `/api/generations-with-image`)
   - Location: `backend/app/services/pipeline/` (various orchestrators)
   - Features: Quality scoring, storyboard generation, multi-stage orchestration

4. **CLI Tools** (Standalone)
   - Location: `backend/cli_tools/`
   - Tools: create_storyboard.py, generate_images.py, generate_videos.py, enhance_image_prompt.py, enhance_video_prompt.py, pipeline.py

---

## Frontend (React + TypeScript)

### Core Framework
| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 19.2+ | UI framework |
| **TypeScript** | 5.9.3 | Type-safe development |
| **React Router** | 7.9.6+ | Client-side routing |
| **Vite** | 5.4.11+ | Build tool and dev server |

### State Management
| Technology | Version | Purpose |
|------------|---------|---------|
| **Zustand** | 5.0.8+ | Lightweight state management |

### Styling
| Technology | Version | Purpose |
|------------|---------|---------|
| **Tailwind CSS** | 4.1.17+ | Utility-first CSS framework |
| **PostCSS** | 8.5.6+ | CSS processing |
| **Autoprefixer** | 10.4.22+ | CSS vendor prefixing |

### Canvas & Media
| Technology | Version | Purpose |
|------------|---------|---------|
| **Konva** | 9.3.22+ | Canvas manipulation for video editor |
| **React-Konva** | 19.2+ | React bindings for Konva |
| **use-image** | 1.1.4+ | Image loading hook |

### HTTP & API
| Technology | Version | Purpose |
|------------|---------|---------|
| **Axios** | 1.13.2+ | HTTP client with interceptors |
| **WebSocket** | Native | Real-time communication for interactive pipeline |

### Testing
| Technology | Version | Purpose |
|------------|---------|---------|
| **Vitest** | 1.6+ | Fast unit test framework |
| **@vitest/ui** | 1.6+ | Test UI |
| **@testing-library/react** | 16.1+ | React component testing |
| **@testing-library/jest-dom** | 6.6.3+ | DOM matchers |
| **@testing-library/user-event** | 14.6.1+ | User interaction simulation |
| **jsdom** | 25.0.1+ | DOM environment for tests |

### Linting & Formatting
| Technology | Version | Purpose |
|------------|---------|---------|
| **ESLint** | 9.39.1+ | Code linting |
| **Prettier** | 3.6.2+ | Code formatting |
| **typescript-eslint** | 8.46.3+ | TypeScript-specific linting |

### UI Components

The frontend has multiple pipeline-specific interfaces:

1. **Master Mode UI** (`/master-mode`)
   - Components: Located in `frontend/src/routes/MasterMode.tsx`
   - Features: Progress tracking, LLM conversation viewer, video playback

2. **Interactive Pipeline UI** (`/interactive`)
   - Component: `frontend/src/components/generation/InteractivePipeline.tsx`
   - Related: ChatInterface.tsx, StoryReview.tsx, ImageReview.tsx, ImageEditor.tsx
   - Known Issue: WebSocket errors on navigation

3. **Original Pipeline UI** (Dashboard `/dashboard`)
   - Features: Quality score display, video gallery
   - Components: VideoGallery.tsx, ComparisonView.tsx, ParallelGenerationPanel.tsx

---

## Deployment & Infrastructure

### Web Server
| Technology | Purpose |
|------------|---------|
| **Nginx** | Reverse proxy, static file serving |

### Process Management
| Technology | Purpose |
|------------|---------|
| **Systemd** | FastAPI service management (fastapi.service) |

### Deployment Automation
| Technology | Purpose |
|------------|---------|
| **Bash Scripts** | Automated deployment (deploy.sh) |
| **Setup Scripts** | RDS setup (setup-rds.sh), S3 setup (setup-s3-frontend.sh, setup-s3-videos.sh) |

### Cloud Services (AWS)
| Service | Purpose |
|---------|---------|
| **EC2** | Application hosting |
| **RDS** | PostgreSQL database |
| **S3** | Video storage and frontend assets |
| **CloudFront** | CDN (potential) |

### Logging & Monitoring
| Technology | Purpose |
|------------|---------|
| **Logrotate** | Log rotation (logrotate-fastapi) |
| **Python logging** | Structured logging in backend |

---

## Architecture Pattern

**Pattern:** Service-Oriented Architecture with Multiple Pipeline Strategies

The application follows a **layered architecture** with clear separation:

1. **API Layer** - FastAPI routes and WebSocket endpoints
2. **Service Layer** - Pipeline orchestrators, LLM services, generation services
3. **Data Layer** - SQLAlchemy models, database session management
4. **Storage Layer** - S3 service abstraction, local fallback

**Key Architectural Features:**
- **Multi-Pipeline Architecture:** 4 independent video generation pipelines with different trade-offs
- **WebSocket Integration:** Real-time progress streaming for interactive pipeline
- **Async/Await:** Throughout backend for concurrent operations
- **Reference Image System:** Master mode uses 3 reference images for visual consistency
- **LLM Agent Chain:** Story → Scene → Enhancement → Video generation workflow

---

## Development Tools

### Version Control
- **Git** with `.gitignore` for Python, Node.js, and media files

### Environment Management
- **Python venv** for backend isolation
- **npm** for frontend package management

### Configuration
- **Environment Variables** (.env files) for API keys, database URLs, CORS settings

---

## Integration Points

### External APIs
1. **OpenAI API** - GPT-4 for prompt engineering, story generation, scene planning
2. **Replicate API** - Video generation (Kling, potential SORA), image generation (Flux)

### Internal Integration
- **Frontend ↔ Backend:** RESTful API + WebSocket for real-time updates
- **Backend ↔ S3:** Video/image asset storage
- **Backend ↔ Database:** User data, generation metadata, quality metrics

---

## Key Technical Debt & Consolidation Needs

### Pipeline Fragmentation
- **4 separate pipelines** with overlapping functionality
- **Inconsistent consistency:** Master mode has reference image consistency, others don't
- **UI issues:** Interactive pipeline has WebSocket navigation bugs
- **Hardcoded logic:** Master mode lacks flexibility

### Target: Unified Pipeline
**Requirements:**
- Combine master mode's 3-ref-image consistency
- Integrate interactive mode's user feedback capability
- Preserve quality score displays from original pipeline
- Support both UI and CLI execution
- Add image generation (not just ref image input)
- Flexible, configurable architecture

---

## Quality & Performance Features

### Quality Control
- **Image Quality Scoring** (image_quality_scoring.py)
- **Video Quality Metrics** (stored in quality_metric model)
- **VBench Integration** (planned - commented in requirements.txt)

### Performance Optimizations
- **Parallel Processing:** Multi-scene video generation
- **Caching:** Redis for frequently accessed data
- **Async Operations:** FastAPI async routes for non-blocking I/O
- **Seed Management:** Reproducible generations with seed control

---

## Summary Table

| Category | Backend | Frontend | Deployment |
|----------|---------|----------|------------|
| **Language** | Python 3.11+ | TypeScript 5.9+ | Bash |
| **Framework** | FastAPI | React 19 | Nginx + Systemd |
| **Database** | SQLAlchemy (PostgreSQL/SQLite) | - | AWS RDS |
| **State** | Database + Redis | Zustand | - |
| **Styling** | - | Tailwind CSS 4 | - |
| **Testing** | Pytest | Vitest | - |
| **Build Tool** | Uvicorn | Vite 5 | - |
| **Storage** | Boto3 (S3) | - | AWS S3 |
| **AI Services** | OpenAI, Replicate | - | - |

**Architecture:** Multi-part application with service-oriented backend, component-based frontend, and cloud-native deployment
