# Epic Technical Specification: Foundation & Infrastructure

Date: 2025-11-14
Author: BMad
Epic ID: 1
Status: Draft

---

## Overview

Epic 1 establishes the foundational infrastructure required for the AI Video Ad Generator application. This epic creates the project structure, database schema, API infrastructure, and basic deployment pipeline that all subsequent epics depend upon. As outlined in the PRD, the system is a single-tenant web application with a React + TypeScript frontend and FastAPI backend, deployed on AWS EC2 with PostgreSQL on AWS RDS. This epic implements the core technical foundation that enables user authentication (Epic 2), video generation (Epic 3), video management (Epic 4), and user profiles (Epic 5).

## Objectives and Scope

**In-Scope:**
- Project repository structure with frontend (React + TypeScript + Vite) and backend (Python + FastAPI) directories
- Database schema and SQLAlchemy models for `users` and `generations` tables
- FastAPI backend server with CORS configuration, health endpoint, and basic routing structure
- Frontend API client setup with Axios, TypeScript types, and error handling
- Basic deployment scripts and configuration for AWS EC2 with Nginx
- Environment configuration management (.env files, config modules)
- Development environment setup (virtual environments, build tools, linting)

**Out-of-Scope:**
- User authentication implementation (deferred to Epic 2)
- Video generation pipeline (deferred to Epic 3)
- Video gallery UI (deferred to Epic 4)
- Production monitoring and alerting (post-MVP)
- Multi-instance deployment and horizontal scaling (post-MVP)
- CI/CD pipeline automation (post-MVP)

## System Architecture Alignment

This epic implements the foundational components of the architecture described in `docs/architecture.md`. The project structure follows the greenfield target layout with clear separation between frontend (`frontend/`) and backend (`backend/`) directories. The backend uses FastAPI with SQLAlchemy 2.x for ORM, aligned with the architecture's decision to use synchronous orchestration for MVP. The database schema supports both SQLite (development) and PostgreSQL (production via AWS RDS), as specified in the architecture document. The frontend structure uses React Router for routing and Zustand for minimal global state, consistent with the architecture's lightweight state management approach. The deployment configuration establishes the single EC2 + RDS pattern described in the architecture, with Nginx serving static files and reverse-proxying API requests.

## Detailed Design

### Services and Modules

| Module/Service | Responsibility | Inputs | Outputs | Owner |
|----------------|----------------|--------|---------|-------|
| `backend/app/main.py` | FastAPI application entry point, middleware configuration | HTTP requests | HTTP responses | Backend |
| `backend/app/core/config.py` | Environment variable loading, configuration management | Environment variables | Configuration object | Backend |
| `backend/app/core/security.py` | JWT token utilities (placeholder for Epic 2) | - | - | Backend |
| `backend/app/db/base.py` | SQLAlchemy base and engine initialization | Database URL | Database engine, base class | Backend |
| `backend/app/db/session.py` | Database session management | - | Database session factory | Backend |
| `backend/app/db/models/user.py` | User ORM model definition | - | User model class | Backend |
| `backend/app/db/models/generation.py` | Generation ORM model definition | - | Generation model class | Backend |
| `backend/app/api/routes/auth.py` | Authentication routes (placeholder structure) | - | Route definitions | Backend |
| `backend/app/api/deps.py` | FastAPI dependencies (auth, DB session) | - | Dependency functions | Backend |
| `frontend/src/lib/apiClient.ts` | Axios instance with interceptors | API requests | HTTP client | Frontend |
| `frontend/src/lib/config.ts` | Frontend configuration (API URL) | Environment variables | Config object | Frontend |
| `frontend/src/store/authStore.ts` | Zustand auth state store (placeholder) | - | Auth state | Frontend |
| `deployment/deploy.sh` | Deployment script for EC2 | - | Deployed application | DevOps |
| `deployment/nginx.conf` | Nginx configuration | - | Nginx config file | DevOps |
| `deployment/fastapi.service` | Systemd service file | - | Service definition | DevOps |

### Data Models and Contracts

**User Model (`backend/app/db/models/user.py`):**
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=uuid4)  # UUID
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # bcrypt hash
    email = Column(String(255), nullable=True)
    total_generations = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationship
    generations = relationship("Generation", back_populates="user")
```

**Generation Model (`backend/app/db/models/generation.py`):**
```python
class Generation(Base):
    __tablename__ = "generations"
    
    id = Column(String(36), primary_key=True, default=uuid4)  # UUID
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    duration = Column(Integer, default=15)
    aspect_ratio = Column(String(10), default="9:16")
    status = Column(String(20), default="pending", index=True)  # pending, processing, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    current_step = Column(String(100), nullable=True)
    video_path = Column(String(500), nullable=True)
    video_url = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    framework = Column(String(20), nullable=True)  # PAS, BAB, AIDA
    num_scenes = Column(Integer, nullable=True)
    generation_time_seconds = Column(Integer, nullable=True)
    cost = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="generations")
```

**Indexes:**
- `users.username` (unique index)
- `users.id` (primary key)
- `generations.user_id` (foreign key index)
- `generations.status` (query optimization)
- `generations.created_at` (sorting/filtering)

**Data Types:**
- UUIDs: String(36) for primary keys
- Text fields: Text for long content (prompt, error_message)
- Numeric: Integer for counts/durations, Float for costs
- Timestamps: DateTime with UTC defaults

### APIs and Interfaces

**Backend API Endpoints (Structure Only - Implementation in Later Epics):**

| Method | Path | Description | Status Code | Response |
|--------|------|-------------|-------------|----------|
| GET | `/api/health` | Health check endpoint | 200 | `{"status": "healthy"}` |
| POST | `/api/auth/register` | User registration (Epic 2) | 201/400 | User creation response |
| POST | `/api/auth/login` | User login (Epic 2) | 200/401 | JWT token + user info |
| GET | `/api/auth/me` | Current user info (Epic 2) | 200/401 | User profile |
| POST | `/api/generate` | Start video generation (Epic 3) | 202/422 | Generation ID |
| GET | `/api/status/{id}` | Generation status (Epic 3) | 200/404 | Status object |
| GET | `/api/generations` | List user videos (Epic 4) | 200 | Paginated list |
| GET | `/api/video/{id}` | Video file (Epic 4) | 200/404 | Video stream |
| DELETE | `/api/generations/{id}` | Delete video (Epic 4) | 200/404 | Success message |
| GET | `/api/user/profile` | User profile (Epic 5) | 200/401 | User stats |

**Frontend API Client Interface (`frontend/src/lib/apiClient.ts`):**
```typescript
// Axios instance with base configuration
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor (adds JWT token - Epic 2)
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor (handles 401 errors - Epic 2)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login (Epic 2)
    }
    return Promise.reject(error);
  }
);
```

**Error Response Format (All Endpoints):**
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message"
  }
}
```

### Workflows and Sequencing

**Database Migration Workflow:**
1. Initialize SQLAlchemy base and engine from `DATABASE_URL`
2. Create database tables using `Base.metadata.create_all()` or Alembic migrations
3. Verify tables exist: `users`, `generations`
4. Verify indexes are created on specified columns

**Development Server Startup:**
1. Load environment variables from `.env` file
2. Initialize FastAPI app with CORS middleware
3. Register route modules (auth, generations, users)
4. Start Uvicorn server on port 8000 (development)

**Frontend Build Workflow:**
1. Install dependencies: `npm install`
2. Build production bundle: `npm run build`
3. Output to `frontend/dist/` directory
4. Serve via Nginx in production

**Deployment Workflow (EC2):**
1. SSH into EC2 instance
2. Install system dependencies (Python 3.11, Node.js, FFmpeg, Nginx)
3. Clone repository
4. Set up Python virtual environment and install backend dependencies
5. Build frontend: `npm run build` in `frontend/` directory
6. Configure Nginx to serve `frontend/dist/` and proxy `/api/*` to FastAPI
7. Create systemd service for FastAPI backend
8. Start Nginx and FastAPI services

## Non-Functional Requirements

### Performance

**NFR-001: Health Endpoint Response Time**
- Target: `/api/health` responds in <100ms
- Measurement: Average response time over 100 requests
- Source: PRD Section 9.1 (API Response Time)

**NFR-002: Database Query Performance**
- Target: Table creation and index creation complete in <5 seconds
- Measurement: Time to execute `Base.metadata.create_all()`
- Source: Architecture document (database setup)

**NFR-003: Frontend Build Time**
- Target: Production build completes in <2 minutes
- Measurement: `npm run build` execution time
- Source: Development workflow requirements

### Security

**NFR-004: Environment Variable Protection**
- Requirement: All sensitive configuration (API keys, secrets) stored in `.env` files, never committed to version control
- Implementation: `.gitignore` excludes `.env` files, `.env.example` provided as template
- Source: PRD Section 16.4 (API Keys)

**NFR-005: CORS Configuration**
- Requirement: CORS middleware configured to allow requests from frontend origin only
- Implementation: FastAPI CORS middleware with specific `allow_origins` list
- Source: PRD Section 14 (API Specifications), Architecture document

**NFR-006: Input Validation Foundation**
- Requirement: Pydantic models used for all request/response validation
- Implementation: Request schemas defined in `backend/app/schemas/`
- Source: PRD Section 16.3 (Input Validation)

### Reliability/Availability

**NFR-007: Database Connection Resilience**
- Requirement: SQLAlchemy connection pooling configured with retry logic
- Implementation: Connection pool size: 5-20 connections, retry on connection failure
- Source: Architecture document (database setup)

**NFR-008: Service Auto-Restart**
- Requirement: FastAPI service restarts automatically on failure (systemd)
- Implementation: Systemd service file with `Restart=always`
- Source: PRD Section 19.2 (Deployment Process)

**NFR-009: Nginx High Availability**
- Requirement: Nginx serves static files even if FastAPI backend is down
- Implementation: Nginx configuration with proper error handling for proxy failures
- Source: Architecture document (deployment)

### Observability

**NFR-010: Structured Logging**
- Requirement: All backend operations log with structured format (level, message, timestamp)
- Implementation: Python `logging` module configured in `backend/app/core/logging.py`
- Source: PRD Section 9.6 (Logging), Architecture document

**NFR-011: Health Check Endpoint**
- Requirement: `/api/health` endpoint returns service status
- Implementation: GET endpoint returning `{"status": "healthy"}` or error
- Source: PRD Section 14 (API Specifications)

**NFR-012: Error Logging**
- Requirement: All exceptions logged with stack traces (development) or sanitized messages (production)
- Implementation: FastAPI exception handlers with logging
- Source: PRD Section 16.5 (Error Handling)

## Dependencies and Integrations

**Frontend Dependencies:**
- React 18.2+ (UI library)
- TypeScript 5.0+ (Type safety)
- Vite 5.0+ (Build tool)
- Tailwind CSS 3.3+ (Styling)
- Zustand 4.4+ (State management)
- Axios 1.6+ (HTTP client)
- React Router 6+ (Routing)

**Backend Dependencies:**
- Python 3.11+ (Runtime)
- FastAPI 0.104+ (Web framework)
- Uvicorn (ASGI server)
- SQLAlchemy 2.0+ (ORM)
- Pydantic (Data validation)
- python-dotenv (Environment variable loading)

**Development Dependencies:**
- ESLint + Prettier (Code quality - frontend)
- pytest (Testing - backend, future)
- Alembic (Database migrations, optional for MVP)

**System Dependencies (EC2):**
- Python 3.11
- Node.js 18+ (for frontend build)
- FFmpeg (for future video processing)
- Nginx (Web server)
- PostgreSQL client libraries (psycopg2)

**External Services (Not Used in Epic 1, but Configured):**
- AWS RDS PostgreSQL (Production database)
- AWS EC2 (Deployment target)

**Version Constraints:**
- All dependencies should use exact versions or version ranges specified in `package.json` and `requirements.txt`
- No dependency conflicts between frontend and backend

## Acceptance Criteria (Authoritative)

**AC-1.1.1: Project Structure**
- **Given** a new project repository
- **When** I examine the project structure
- **Then** I see:
  - `frontend/` directory with React + TypeScript + Vite setup
  - `backend/` directory with Python + FastAPI structure
  - `deployment/` directory with deployment scripts
  - `docs/` directory with project documentation
- **And** the structure matches the architecture document layout

**AC-1.1.2: Frontend Configuration**
- **Given** the frontend directory
- **When** I examine `frontend/package.json`
- **Then** I see React 18+, TypeScript 5+, Vite 5+, Tailwind CSS 3.3+
- **And** TypeScript configuration has strict mode enabled
- **And** ESLint and Prettier configurations exist

**AC-1.1.3: Backend Configuration**
- **Given** the backend directory
- **When** I examine `backend/requirements.txt`
- **Then** I see Python 3.11+, FastAPI 0.104+, SQLAlchemy 2.0+
- **And** a `.env.example` file exists with required environment variables

**AC-1.2.1: Database Models**
- **Given** database models are defined
- **When** I run database migrations
- **Then** the `users` table is created with fields: id (UUID), username (unique, indexed), password_hash, email (optional), total_generations, total_cost, created_at, last_login
- **And** the `generations` table is created with all fields as specified in the data model section
- **And** foreign key relationship exists between `generations.user_id` and `users.id`

**AC-1.2.2: Database Indexes**
- **Given** database tables are created
- **When** I query the database schema
- **Then** indexes exist on: `users.username` (unique), `generations.user_id`, `generations.status`, `generations.created_at`

**AC-1.3.1: Backend Health Endpoint**
- **Given** the FastAPI server is running
- **When** I make a GET request to `/api/health`
- **Then** I receive a 200 OK response with `{"status": "healthy"}`

**AC-1.3.2: CORS Configuration**
- **Given** the FastAPI server is running
- **When** I make a request from the frontend origin
- **Then** CORS headers allow the request
- **And** requests from other origins are blocked

**AC-1.3.3: Frontend API Client**
- **Given** the frontend application
- **When** I examine `frontend/src/lib/apiClient.ts`
- **Then** I see an Axios instance configured with base URL from environment variables
- **And** request interceptor structure exists (for JWT token - Epic 2)
- **And** response interceptor structure exists (for 401 handling - Epic 2)

**AC-1.4.1: Deployment Script**
- **Given** I have an AWS EC2 instance with Ubuntu 22.04
- **When** I run the deployment script
- **Then** the script installs system dependencies (Python 3.11, Node.js, FFmpeg, Nginx)
- **And** sets up Python virtual environment
- **And** builds the React frontend
- **And** configures Nginx to serve static files and proxy API requests

**AC-1.4.2: Nginx Configuration**
- **Given** Nginx is configured
- **When** I access the application URL
- **Then** Nginx serves the React frontend from `frontend/dist/`
- **And** requests to `/api/*` are proxied to FastAPI on port 8000

**AC-1.4.3: Systemd Service**
- **Given** the FastAPI backend is deployed
- **When** I check the systemd service status
- **Then** the service is configured with auto-restart on failure
- **And** the service starts on system boot

## Traceability Mapping

| AC ID | Spec Section | Component(s)/Module(s) | Test Idea |
|-------|--------------|------------------------|-----------|
| AC-1.1.1 | Project Structure | Repository root, `frontend/`, `backend/`, `deployment/` | Verify directory structure exists |
| AC-1.1.2 | Frontend Configuration | `frontend/package.json`, `frontend/tsconfig.json`, `frontend/.eslintrc` | Check package versions, TypeScript strict mode, lint config |
| AC-1.1.3 | Backend Configuration | `backend/requirements.txt`, `backend/.env.example` | Verify Python/FastAPI versions, env template |
| AC-1.2.1 | Data Models | `backend/app/db/models/user.py`, `backend/app/db/models/generation.py` | Create tables, verify schema matches spec |
| AC-1.2.2 | Database Indexes | SQLAlchemy model definitions | Query database metadata, verify indexes exist |
| AC-1.3.1 | APIs and Interfaces | `backend/app/api/routes/` (health endpoint) | HTTP GET request to `/api/health`, verify 200 response |
| AC-1.3.2 | APIs and Interfaces | `backend/app/main.py` (CORS middleware) | Test CORS headers with different origins |
| AC-1.3.3 | APIs and Interfaces | `frontend/src/lib/apiClient.ts` | Inspect code, verify interceptor structure |
| AC-1.4.1 | Deployment | `deployment/deploy.sh` | Run script on test EC2, verify all steps complete |
| AC-1.4.2 | Deployment | `deployment/nginx.conf` | Verify Nginx serves frontend and proxies API |
| AC-1.4.3 | Deployment | `deployment/fastapi.service` | Check systemd service file, verify restart policy |

## Risks, Assumptions, Open Questions

**Risk-1: Database Schema Changes**
- **Risk:** Schema changes in later epics may require migrations
- **Mitigation:** Use Alembic for migration management (optional in Epic 1, recommended for production)
- **Status:** Open - consider adding Alembic in Epic 1 vs. later

**Risk-2: Environment Configuration Complexity**
- **Risk:** Multiple environment files (.env for backend, .env for frontend) may cause confusion
- **Mitigation:** Document clearly in README, provide `.env.example` files for both
- **Status:** Mitigated

**Risk-3: Deployment Script Failures**
- **Risk:** Deployment script may fail mid-execution, leaving system in inconsistent state
- **Mitigation:** Add error handling and rollback steps, test on clean EC2 instance
- **Status:** Open - add error handling in deployment script

**Assumption-1: AWS EC2 Access**
- **Assumption:** Developer has AWS EC2 instance with Ubuntu 22.04 and SSH access
- **Validation:** Document EC2 setup requirements in deployment guide
- **Status:** Documented

**Assumption-2: Database Availability**
- **Assumption:** PostgreSQL database (RDS or local) is available and accessible
- **Validation:** Deployment script should verify database connectivity
- **Status:** Open - add database connection check

**Question-1: Migration Strategy**
- **Question:** Should Epic 1 use Alembic for migrations or simple `Base.metadata.create_all()`?
- **Decision:** For MVP, `create_all()` is sufficient. Alembic can be added in Epic 2 if needed.
- **Status:** Resolved - use `create_all()` for MVP

**Question-2: Frontend Build Location**
- **Question:** Where should Nginx serve frontend files from? (`/var/www/html/ad-generator` or project directory?)
- **Decision:** Use project directory structure: `/var/www/ad-generator/frontend/dist/` (configurable)
- **Status:** Resolved

## Test Strategy Summary

**Unit Tests (Backend):**
- Test database model creation and relationships
- Test SQLAlchemy session management
- Test configuration loading from environment variables
- Test CORS middleware configuration

**Integration Tests:**
- Test `/api/health` endpoint returns correct response
- Test database table creation with actual database (SQLite for tests)
- Test frontend build process produces valid output

**Manual Testing:**
- Verify project structure matches specification
- Verify all configuration files exist and are properly formatted
- Test deployment script on clean EC2 instance
- Verify Nginx serves frontend and proxies API correctly
- Verify systemd service starts and restarts on failure

**Test Coverage Goals:**
- Epic 1 focuses on infrastructure setup, so unit tests are minimal
- Primary validation is through manual verification and integration tests
- Full test coverage will be added in later epics when business logic is implemented

**Test Frameworks:**
- Backend: pytest (setup in Epic 1, tests written in Epic 2+)
- Frontend: Vitest or Jest (setup in Epic 1, tests written in Epic 2+)
- E2E: Not required for Epic 1 (infrastructure only)

