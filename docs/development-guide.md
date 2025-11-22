# Development Guide - Ad Mint AI

**Generated:** 2025-11-22

This guide covers local development setup, running the application, and common development tasks.

---

## Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| **Python** | 3.11+ | Backend runtime |
| **Node.js** | 20.19+ or 22.12+ | Frontend runtime |
| **npm** | 8+ | Package management |
| **Git** | Latest | Version control |

### Check Your Versions

```bash
python --version    # or python3 --version
node --version
npm --version
git --version
```

---

## Initial Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/ad-mint-ai.git
cd ad-mint-ai
```

### 2. Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from template
cp .env.example .env
# Edit .env and add your API keys:
#   OPENAI_API_KEY=sk-...
#   REPLICATE_API_TOKEN=r8_...

# Initialize database
python -m app.db.init_db

# Create demo user
python create_demo_user.py
```

### 3. Frontend Setup

```bash
# Navigate to frontend (from project root)
cd frontend

# Install dependencies
npm install

# Create .env file (optional)
cp .env.example .env
# Default API URL is http://localhost:8000
```

---

## Running the Application

You need **two terminals** - one for backend, one for frontend.

### Terminal 1: Start Backend

```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn app.main:app --reload
```

**Backend will run at:**
- API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- Health Check: http://localhost:8000/api/health

### Terminal 2: Start Frontend

```bash
cd frontend
npm run dev
```

**Frontend will run at:**
- Application: http://localhost:5173

---

## Verify Installation

1. **Health Check:**
   ```bash
   curl http://localhost:8000/api/health
   ```
   Expected: `{"status":"healthy",...}`

2. **Login:**
   - Open http://localhost:5173
   - Click "Login as Demo User" or use:
     - Username: `demo`
     - Password: `demo1234`

---

## Project Structure

```
ad-mint-ai/
├── backend/          # FastAPI backend
│   ├── app/          # Application code
│   ├── tests/        # Backend tests
│   ├── venv/         # Virtual environment
│   └── requirements.txt
│
├── frontend/         # React frontend
│   ├── src/          # Source code
│   ├── dist/         # Build output
│   └── package.json
│
├── deployment/       # Deployment configs
└── docs/             # Documentation (you are here)
```

---

## API Keys Required

### OpenAI (Required for LLM features)
1. Get API key: https://platform.openai.com/api-keys
2. Add to `backend/.env`:
   ```
   OPENAI_API_KEY=sk-proj-...
   ```

### Replicate (Required for image/video generation)
1. Get API token: https://replicate.com/account/api-tokens
2. Add to `backend/.env`:
   ```
   REPLICATE_API_TOKEN=r8_...
   ```

### AWS (Optional - for S3 storage)
Only needed for production deployment:
```
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_VIDEO_BUCKET=ad-mint-ai-videos
AWS_S3_REGION=us-east-1
```

---

## Development Commands

### Backend

```bash
cd backend
source venv/bin/activate

# Run dev server (auto-reload)
uvicorn app.main:app --reload

# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth_routes.py

# Database init
python -m app.db.init_db

# Run migrations
python run_migrations.py

# Create demo user
python create_demo_user.py
```

### Frontend

```bash
cd frontend

# Run dev server
npm run dev

# Run tests
npm run test

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint

# Format code
npx prettier --write src/
```

### CLI Tools

```bash
cd backend
source venv/bin/activate

# Full pipeline
python cli_tools/pipeline.py \
  --prompt "Your ad concept" \
  --reference-images ./refs/ \
  --output ./output/

# Create storyboard
python cli_tools/create_storyboard.py \
  --prompt "Product showcase" \
  --scenes 3

# Generate images
python cli_tools/generate_images.py \
  --prompt "Eco-friendly water bottle" \
  --count 3

# Generate videos
python cli_tools/generate_videos.py \
  --prompts prompts.json \
  --reference-images ./refs/

# Enhance prompts
python cli_tools/enhance_image_prompt.py --input "simple prompt"
python cli_tools/enhance_video_prompt.py --input "simple prompt"
```

---

## Common Issues

### Port Already in Use

**Backend (port 8000):**
```bash
# macOS/Linux
lsof -ti:8000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Frontend (port 5173):**
Vite will automatically use the next available port (5174, 5175, etc.)

### Database Errors

```bash
# Recreate database
cd backend
rm ad_mint_ai.db
python -m app.db.init_db
python create_demo_user.py
```

### Virtual Environment Not Activating

Make sure you're in the `backend/` directory and use the correct command for your OS.

### Module Not Found

```bash
# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### CORS Errors

1. Check that backend is running
2. Verify `CORS_ALLOWED_ORIGINS` in `backend/.env` includes `http://localhost:5173`
3. Restart backend server

### Tailwind CSS Not Working

```bash
cd frontend
rm -rf node_modules
npm install
npm run dev
```

---

## Hot Reload

### Backend

Uvicorn automatically reloads when Python files change (when using `--reload` flag).

### Frontend

Vite Hot Module Replacement (HMR) automatically updates the browser when files change.

If HMR breaks:
1. Stop Vite (`Ctrl+C`)
2. Clear cache: `rm -rf node_modules/.vite`
3. Restart: `npm run dev`

---

## Testing

### Backend Tests

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run specific test file
pytest tests/test_auth_routes.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser

# Run specific test
pytest tests/test_auth_routes.py::test_register_user
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm run test

# Run with UI
npm run test:ui

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test -- --watch

# Run specific test file
npm run test -- src/__tests__/Dashboard.test.tsx
```

---

## Environment Variables

### Backend (.env)

```bash
# Database
DATABASE_URL=sqlite:///./ad_mint_ai.db  # Development
# DATABASE_URL=postgresql://user:pass@host:5432/db  # Production

# Security
SECRET_KEY=change-me-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7 days

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# API Keys
OPENAI_API_KEY=sk-proj-...
REPLICATE_API_TOKEN=r8_...

# AWS (Optional)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_VIDEO_BUCKET=ad-mint-ai-videos
AWS_S3_REGION=us-east-1

# Storage Mode
STORAGE_MODE=local  # or "s3"

# Output Paths
OUTPUT_BASE_DIR=output  # For interactive pipeline

# Debug
DEBUG=True
LOG_LEVEL=INFO
```

### Frontend (.env)

```bash
VITE_API_URL=http://localhost:8000
```

---

## Code Style

### Backend

- **PEP 8** Python style guide
- **Black** auto-formatter (recommended)
- **Type hints** where appropriate

```bash
# Format with Black (if installed)
black backend/app/

# Lint with flake8 (if installed)
flake8 backend/app/
```

### Frontend

- **TypeScript** for all new code
- **ESLint** for linting
- **Prettier** for formatting

```bash
# Lint
npm run lint

# Format
npx prettier --write src/
```

---

## Git Workflow

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes and commit
git add .
git commit -m "Add my feature"

# Push to remote
git push origin feature/my-feature

# Create pull request on GitHub
```

---

## Database Management

### SQLite (Development)

**Location:** `backend/ad_mint_ai.db`

```bash
# View database
sqlite3 backend/ad_mint_ai.db

# Common queries
.tables                    # List tables
SELECT * FROM users;       # View users
SELECT * FROM generations; # View generations
.quit                      # Exit
```

### PostgreSQL (Production)

```bash
# Connect
psql -U user -h host -d ad_mint_ai

# Common queries
\dt                        # List tables
SELECT * FROM users;
\q                         # Exit
```

### Migrations

```bash
cd backend
python run_migrations.py
```

---

## Debugging

### Backend Debugging

Add breakpoints with `import pdb; pdb.set_trace()`:

```python
def my_function():
    import pdb; pdb.set_trace()  # Execution will pause here
    # ... rest of code
```

### Frontend Debugging

- Use browser DevTools (F12)
- Add `console.log()` statements
- Use React DevTools extension

### API Debugging

- **Swagger UI:** http://localhost:8000/docs (test endpoints interactively)
- **curl:** `curl -X POST http://localhost:8000/api/auth/login -H "Content-Type: application/json" -d '{"username":"demo","password":"demo1234"}'`
- **Postman:** Import OpenAPI spec from /docs

---

## Performance Tips

### Backend

- Use async operations where possible
- Enable database connection pooling (PostgreSQL)
- Cache frequently accessed data with Redis
- Use background tasks for long-running operations

### Frontend

- Lazy load routes with React.lazy()
- Optimize images
- Use React.memo() for expensive components
- Debounce search inputs

---

## Production Build

### Frontend

```bash
cd frontend
npm run build

# Output: frontend/dist/
# Serve with: npm run preview
```

### Backend

No build step required. Deploy Python files directly.

---

## Next Steps

- See [API Contracts](./api-contracts.md) for API documentation
- See [Architecture](./architecture-backend.md) for system design
- See [Deployment Guide](../deployment/README.md) for production deployment
