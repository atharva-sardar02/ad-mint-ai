# Tech Context

- **Backend:** FastAPI + Uvicorn, Python 3.11+. Key dependencies include Pydantic v2, SQLAlchemy 2, Redis (optional), OpenAI async SDK, Pillow/MoviePy for media, and boto3 for S3 integration.
- **Frontend:** React + Vite + TypeScript, Zustand for state, custom WebSocket service for the pipeline, Tailwind/utility CSS.
- **Storage:** Default local dev uses SQLite for legacy tables but the interactive pipeline prefers Redis/Postgres. Without Redis/Postgres, sessions remain in memory—good for dev but not durable.
- **Async Patterns:** Backend services (generation, conversation handler) are async and expect event-loop friendly libraries. Long-running operations should avoid blocking.
- **Environment:** `.env` under `backend/` stores secrets (OpenAI key, DB URLs, AWS creds). `VITE_API_URL` controls frontend API base.
- **Tooling:** Tests via pytest/pytest-asyncio. CLI tools exist for batch generation and are stored under `backend/cli_tools`.
