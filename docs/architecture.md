## Executive Summary

The AI Video Ad Generator is implemented as a single-tenant web application deployed on a single AWS EC2 instance for MVP. A React + TypeScript + Vite + Tailwind frontend communicates with a FastAPI backend that orchestrates the full text-to-video pipeline, persists user and generation data in an AWS RDS PostgreSQL database, and stores video artifacts on local disk (with a clear path to S3 as the system scales).

## Project Initialization

### Frontend

- Framework: React 18 + TypeScript using Vite as the build tool.
- Styling: Tailwind CSS with a small set of reusable layout and typography components.
- Routing: React Router with a simple page-based routing structure.
- State management: Lightweight global state via Zustand for auth/session and user profile, otherwise local component state.

Suggested initialization (for a fresh codebase):

- `npm create vite@latest frontend -- --template react-ts`
- Install Tailwind, React Router, and Zustand in the `frontend` app.

### Backend

- Runtime: Python 3.11 on a single EC2 instance.
- Framework: FastAPI + Uvicorn.
- ORM: SQLAlchemy 2.x with Pydantic models for request/response schemas.
- Auth: JWT-based auth using PyJWT and bcrypt via Passlib.

Suggested initialization:

- Create a `backend` directory with a FastAPI app structured as described in the project structure section.
- Use a `.env` file and a central config module to manage database URLs and external API keys.

## Decision Summary (Key Technical Choices)

**Frontend**
- React 18 + TypeScript + Vite as the SPA framework and build tool.
- Tailwind CSS for rapid responsive UI implementation.
- React Router for client-side routing.
- Zustand for small, predictable global state (auth/session, user profile).

**Backend**
- FastAPI as the HTTP API layer.
- Uvicorn as the ASGI server.
- SQLAlchemy + Pydantic-based schema layer for persistence and validation.
- Synchronous orchestration of the video pipeline within a single FastAPI process for MVP (no background worker), with clear extension points for future queueing.

**Data & Storage**
- SQLite database in local development, AWS RDS PostgreSQL in production, with identical schema.
- Local disk storage under `/output` on the EC2 instance for videos, thumbnails, and temporary processing files, with a path to S3 for production.

**External Services**
- OpenAI GPT-4 (or Claude) for LLM enhancement of prompts.
- Replicate-hosted video models (e.g., Minimax Video-01, Runway Gen-3, Kling) for clip generation.

**Deployment**
- Single EC2 instance on Ubuntu 22.04 LTS for frontend + backend.
- Managed AWS RDS PostgreSQL instance in the same VPC/subnet as the EC2 instance.
- Nginx serving the built frontend and reverse-proxying `/api/*` to FastAPI.

## Project Structure

High-level repository layout (greenfield target):

```
ad-mint-ai/
  backend/
    app/
      main.py
      api/
        __init__.py
        deps.py
        routes/
          auth.py
          generations.py
          users.py
      core/
        config.py
        security.py
        logging.py
      db/
        base.py
        session.py
        models/
          user.py
          generation.py
      schemas/
        auth.py
        user.py
        generation.py
      services/
        pipeline/
          llm_enhancement.py
          scene_planning.py
          video_generation.py
          overlays.py
          stitching.py
          audio.py
          export.py
        cost_tracking.py
        cancellation.py
      utils/
        ffmpeg.py
        file_paths.py
    tests/
      ...

  frontend/
    src/
      main.tsx
      App.tsx
      routes/
        Dashboard.tsx
        Gallery.tsx
        VideoDetail.tsx
        Profile.tsx
        Auth/
          Login.tsx
          Register.tsx
      components/
        layout/
        ui/
      store/
        authStore.ts
        userStore.ts
      lib/
        apiClient.ts
        config.ts

  docs/
    PRD.md
    AI Video Generation Pipeline.md
    architecture.md
    bmm-workflow-status.yaml
```

## Epic to Architecture Mapping (Conceptual)

- **Authentication & User Management**
  - Backend: `app/api/routes/auth.py`, `app/schemas/auth.py`, `app/db/models/user.py`, `app/core/security.py`.
  - Frontend: `Auth/Login.tsx`, `Auth/Register.tsx`, Zustand `authStore.ts`.

- **Prompt-to-Video Generation**
  - Backend: `generations.py` endpoint (`POST /api/generate`), pipeline services under `services/pipeline/*`, `Generation` model and schema.
  - Frontend: main dashboard route (`Dashboard.tsx`) and generate form, polling status endpoint, progress UI.

- **Video Gallery & Management**
  - Backend: `GET /api/generations`, `GET /api/video/{id}`, `DELETE /api/generations/{id}`.
  - Frontend: `Gallery.tsx`, `VideoDetail.tsx`, shared components for video cards and player.

- **User Profile & Stats**
  - Backend: `GET /api/user/profile`.
  - Frontend: `Profile.tsx`, `userStore.ts`.

## Technology Stack Details

- **Frontend:** React 18, TypeScript 5, Vite 5, Tailwind 3, React Router, Zustand.
- **Backend:** Python 3.11, FastAPI 0.104+, Uvicorn, SQLAlchemy 2.x, Pydantic, Passlib/bcrypt, PyJWT.
- **Video & Media:** Replicate Python SDK, MoviePy, OpenCV, Pillow, FFmpeg, Pydub.
- **Database:** SQLite (local dev), PostgreSQL on AWS RDS (production).
- **Deployment:** AWS EC2, AWS RDS PostgreSQL, Nginx, Systemd, Ubuntu 22.04.

## Implementation Patterns (Key Consistency Rules)

### Naming

- React components: `PascalCase` filenames (`Dashboard.tsx`, `VideoCard.tsx`).
- React hooks and stores: `camelCase` (`useAuth`, `authStore.ts`).
- API routes: `/api/auth/login`, `/api/generate`, `/api/generations`, `/api/status/{id}`, `/api/video/{id}`.
- Database tables: `snake_case` (`users`, `generations`).
- Database columns: `snake_case` (`user_id`, `total_generations`, `total_cost`).

### Error Handling & API Format

- All API errors follow the PRD’s JSON structure:
  - Top-level `error` key with `code` and `message` fields.
- Backend raises structured exceptions that are converted to this format via FastAPI exception handlers.

### Project Organization

- Backend responsibilities are separated into:
  - `api` (routing and HTTP concerns),
  - `schemas` (Pydantic request/response contracts),
  - `db` (SQLAlchemy models and session),
  - `services` (business logic for pipeline and cost tracking),
  - `core` (config, security, logging).
- Frontend uses feature-oriented routing with local component composition and minimal global state via Zustand.

### Pipeline Orchestration

- A single orchestration function coordinates the seven pipeline stages defined in the PRD:
  1. LLM enhancement
  2. Scene planning
  3. Video clip generation
  4. Text overlays
  5. Stitching
  6. Audio layer
  7. Export & persistence
- The `Generation` record is created at the start with `status=pending` and updated step-by-step to drive user-facing progress.

## Security and Performance Considerations

- Strict JWT validation on all protected endpoints and per-user access checks on generation and video resources.
- Rate limiting at the API gateway layer (e.g., with Nginx or a FastAPI middleware) to enforce the PRD’s generation and request limits.
- Logging of every generation request and external API call with correlation IDs for debugging and cost tracking.

## Development Environment

- Backend runs via `uvicorn app.main:app --reload` in development, with `.env` containing API keys and DB URLs.
- Frontend runs via `npm run dev` in the `frontend` directory, with `VITE_API_URL` pointing at the backend.


