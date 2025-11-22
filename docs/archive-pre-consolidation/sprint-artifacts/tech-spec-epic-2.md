# Epic Technical Specification: User Authentication

Date: 2025-11-14
Author: BMad
Epic ID: 2
Status: Draft

---

## Overview

Epic 2 implements user authentication and authorization for the AI Video Ad Generator application. This epic enables users to create accounts, log in securely using JWT-based authentication, and access protected features throughout the application. As outlined in the PRD (Section 8.1), the system provides user registration with username and password, secure login that generates JWT tokens, protected routes that restrict access to authenticated users, and logout functionality that clears user sessions. This epic builds upon the foundation established in Epic 1 (database models, API infrastructure) and is a prerequisite for Epic 3 (video generation), Epic 4 (video management), and Epic 5 (user profile), as all user-specific features require authentication.

## Objectives and Scope

**In-Scope:**
- User registration endpoint (`POST /api/auth/register`) with username and password validation
- User login endpoint (`POST /api/auth/login`) that generates JWT tokens
- Current user info endpoint (`GET /api/auth/me`) for authenticated users
- Password hashing using bcrypt with cost factor 12
- JWT token generation and validation with 7-day expiration
- Protected route middleware that verifies JWT tokens on API endpoints
- Frontend registration and login forms with client-side validation
- Protected route components that redirect unauthenticated users to login
- Logout functionality that clears tokens and user state
- Token storage in browser localStorage
- Automatic token inclusion in API requests via Axios interceptors
- 401 error handling that redirects to login page

**Out-of-Scope:**
- Password recovery/reset functionality (post-MVP)
- Email verification (post-MVP)
- Social authentication (OAuth, Google, Facebook) (post-MVP)
- Multi-factor authentication (post-MVP)
- Session management beyond JWT tokens (post-MVP)
- Remember me functionality (post-MVP)
- Account deletion (post-MVP)

## System Architecture Alignment

This epic implements the authentication layer described in the PRD (Section 8.1) and architecture document. The backend authentication follows the FastAPI dependency injection pattern, with JWT token verification implemented as a FastAPI dependency (`app/api/deps.py`) that can be injected into protected route handlers. The architecture's decision to use JWT tokens (7-day expiration) aligns with the PRD's security requirements (NFR-009). The frontend authentication state management uses Zustand (`authStore.ts`), consistent with the architecture's lightweight state management approach. The protected routes implementation uses React Router's `Navigate` component, following the architecture's page-based routing structure. The API client interceptors (request interceptor for token, response interceptor for 401 errors) are implemented in `frontend/src/lib/apiClient.ts`, as specified in the architecture document's API infrastructure setup.

## Detailed Design

### Services and Modules

| Module/Service | Responsibility | Inputs | Outputs | Owner |
|----------------|----------------|--------|---------|-------|
| `backend/app/api/routes/auth.py` | Authentication route handlers (register, login, me) | HTTP requests | HTTP responses with JWT tokens | Backend |
| `backend/app/core/security.py` | Password hashing (bcrypt), JWT token generation/validation | Password, user data | Hashed password, JWT token | Backend |
| `backend/app/api/deps.py` | FastAPI dependency for JWT authentication | HTTP request with Authorization header | Current user object | Backend |
| `backend/app/schemas/auth.py` | Pydantic schemas for auth requests/responses | Request data | Validated schemas | Backend |
| `backend/app/db/models/user.py` | User ORM model (from Epic 1, used here) | - | User model | Backend |
| `frontend/src/routes/Auth/Login.tsx` | Login page component with form | User input | Login submission | Frontend |
| `frontend/src/routes/Auth/Register.tsx` | Registration page component with form | User input | Registration submission | Frontend |
| `frontend/src/store/authStore.ts` | Zustand store for authentication state | Auth actions | Auth state (user, token, isAuthenticated) | Frontend |
| `frontend/src/components/ProtectedRoute.tsx` | Route wrapper that checks authentication | Route component | Protected route or redirect | Frontend |
| `frontend/src/lib/apiClient.ts` | Axios interceptors for token and 401 handling | API requests | Requests with token, 401 redirects | Frontend |
| `frontend/src/lib/authService.ts` | Auth API service functions (login, register, logout) | Credentials | API responses | Frontend |

### Data Models and Contracts

**User Model (from Epic 1, used in Epic 2):**
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
    last_login = Column(DateTime, nullable=True)  # Updated on login
    
    # Relationship
    generations = relationship("Generation", back_populates="user")
```

**Pydantic Request Schemas (`backend/app/schemas/auth.py`):**
```python
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, regex="^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=8, max_length=100)
    email: Optional[str] = Field(None, max_length=255)

class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)
```

**Pydantic Response Schemas:**
```python
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str]
    total_generations: int
    total_cost: float
```

**JWT Token Payload:**
```python
{
    "sub": user_id,  # Subject (user ID)
    "username": username,
    "iat": issued_at_timestamp,  # Issued at
    "exp": expiration_timestamp  # Expiration (7 days from iat)
}
```

### APIs and Interfaces

**Backend API Endpoints:**

| Method | Path | Description | Request Body | Response | Status Codes |
|--------|------|-------------|--------------|----------|--------------|
| POST | `/api/auth/register` | Create new user account | `UserRegister` | `{"message": "User created successfully", "user_id": "..."}` | 201, 400, 422 |
| POST | `/api/auth/login` | Authenticate user and get JWT token | `UserLogin` | `TokenResponse` | 200, 401 |
| GET | `/api/auth/me` | Get current authenticated user info | - (requires JWT in header) | `UserResponse` | 200, 401 |

**Request/Response Examples:**

**Registration:**
```json
// Request
POST /api/auth/register
{
  "username": "john_doe",
  "password": "SecurePass123!",
  "email": "john@example.com"
}

// Response (201 Created)
{
  "message": "User created successfully",
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}

// Error Response (400 Bad Request)
{
  "error": {
    "code": "USERNAME_EXISTS",
    "message": "Username already exists"
  }
}
```

**Login:**
```json
// Request
POST /api/auth/login
{
  "username": "john_doe",
  "password": "SecurePass123!"
}

// Response (200 OK)
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "john_doe",
    "email": "john@example.com",
    "total_generations": 0,
    "total_cost": 0.0
  }
}

// Error Response (401 Unauthorized)
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid username or password"
  }
}
```

**Get Current User:**
```json
// Request
GET /api/auth/me
Headers: Authorization: Bearer {jwt_token}

// Response (200 OK)
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "email": "john@example.com",
  "total_generations": 5,
  "total_cost": 12.45,
  "created_at": "2025-11-10T08:30:00Z",
  "last_login": "2025-11-14T10:15:00Z"
}

// Error Response (401 Unauthorized)
{
  "error": {
    "code": "INVALID_TOKEN",
    "message": "Invalid or expired token"
  }
}
```

**Frontend API Client Interface:**
```typescript
// frontend/src/lib/authService.ts
export const authService = {
  register: async (username: string, password: string, email?: string) => {
    return apiClient.post('/api/auth/register', { username, password, email });
  },
  
  login: async (username: string, password: string) => {
    const response = await apiClient.post('/api/auth/login', { username, password });
    // Store token in localStorage
    localStorage.setItem('token', response.data.access_token);
    return response.data;
  },
  
  getCurrentUser: async () => {
    return apiClient.get('/api/auth/me');
  },
  
  logout: () => {
    localStorage.removeItem('token');
  }
};
```

**Frontend Zustand Auth Store:**
```typescript
// frontend/src/store/authStore.ts
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string, email?: string) => Promise<void>;
  logout: () => void;
  loadUser: () => Promise<void>;
}
```

### Workflows and Sequencing

**User Registration Workflow:**
1. User submits registration form with username, password, and optional email
2. Frontend validates input (username 3-50 chars, password min 8 chars)
3. Frontend sends POST request to `/api/auth/register`
4. Backend validates request using Pydantic schema
5. Backend checks if username already exists in database
6. Backend hashes password using bcrypt (cost factor 12)
7. Backend creates new User record in database
8. Backend returns 201 Created with user_id
9. Frontend shows success message and redirects to login page

**User Login Workflow:**
1. User submits login form with username and password
2. Frontend validates input (non-empty fields)
3. Frontend sends POST request to `/api/auth/login`
4. Backend validates request using Pydantic schema
5. Backend queries database for user by username
6. Backend verifies password using bcrypt.compare()
7. Backend generates JWT token with user_id, username, expiration (7 days)
8. Backend updates user.last_login timestamp
9. Backend returns JWT token and user information
10. Frontend stores token in localStorage
11. Frontend updates Zustand auth store with user and token
12. Frontend redirects to dashboard

**Protected Route Access Workflow:**
1. User navigates to protected route (e.g., `/dashboard`)
2. Frontend ProtectedRoute component checks authStore.isAuthenticated
3. If not authenticated, redirect to `/login` with return URL
4. If authenticated, render protected component
5. Component makes API request with token in Authorization header
6. Backend dependency (`get_current_user`) extracts token from header
7. Backend verifies token signature and expiration
8. Backend queries database for user by user_id from token
9. Backend returns user object to route handler
10. Route handler processes request with authenticated user context

**Logout Workflow:**
1. User clicks logout button
2. Frontend calls authStore.logout()
3. Frontend removes token from localStorage
4. Frontend clears auth state in Zustand store
5. Frontend redirects to login page
6. Subsequent API requests no longer include Authorization header

**Token Refresh Handling (401 Response):**
1. Frontend makes API request with token
2. Backend returns 401 Unauthorized (expired/invalid token)
3. Frontend Axios response interceptor catches 401
4. Frontend clears token from localStorage
5. Frontend clears auth state
6. Frontend redirects to login page with message

## Non-Functional Requirements

### Performance

**NFR-2.1: Authentication Response Time**
- Target: Login/Register endpoints respond in <500ms (PRD Section 9.1, NFR-002)
- Measurement: Average response time over 100 requests
- Implementation: Optimize database queries (indexed username lookup), efficient bcrypt hashing
- Source: PRD Section 9.1 (API Response Time)

**NFR-2.2: JWT Token Verification Performance**
- Target: Token verification in protected routes adds <50ms overhead
- Measurement: Time difference between protected and unprotected route handlers
- Implementation: Fast JWT signature verification, cache user lookup if needed
- Source: Architecture document (authentication performance)

**NFR-2.3: Frontend Form Validation**
- Target: Client-side validation feedback appears instantly (<100ms)
- Measurement: Time from input change to validation message display
- Implementation: Real-time validation on input change, debounced for complex rules
- Source: PRD Section 9.5 (Usability)

### Security

**NFR-2.4: Password Hashing Security**
- Requirement: Passwords hashed using bcrypt with cost factor 12 (PRD Section 16.1, NFR-009)
- Implementation: Use Passlib with bcrypt backend, cost factor 12
- Validation: Verify hashed passwords are never stored in plain text
- Source: PRD Section 16.1 (Authentication Security)

**NFR-2.5: JWT Token Security**
- Requirement: JWT tokens signed with 256-bit secret key, 7-day expiration (PRD Section 16.1, NFR-009)
- Implementation: Use PyJWT with HS256 algorithm, secret key from environment variable
- Validation: Tokens expire after 7 days, invalid tokens rejected
- Source: PRD Section 16.1 (JWT Tokens)

**NFR-2.6: Input Validation and Sanitization**
- Requirement: All user inputs validated and sanitized to prevent injection attacks (PRD Section 16.3, NFR-011)
- Implementation: Pydantic schemas for request validation, regex for username format
- Validation: Test with SQL injection attempts, XSS attempts
- Source: PRD Section 16.3 (Input Validation)

**NFR-2.7: Username Uniqueness**
- Requirement: Username must be unique, enforced at database level
- Implementation: Unique constraint on `users.username` column, check before creation
- Validation: Attempt to create duplicate username returns error
- Source: PRD Section 8.1 (FR-001)

**NFR-2.8: HTTPS in Production**
- Requirement: All API communication over HTTPS in production (PRD Section 16.1)
- Implementation: Nginx SSL configuration, Let's Encrypt certificate (optional for MVP)
- Validation: Verify HTTPS redirect works, HTTP requests blocked
- Source: PRD Section 16.1 (HTTPS)

### Reliability/Availability

**NFR-2.9: Database Transaction Integrity**
- Requirement: User creation and password updates use database transactions
- Implementation: SQLAlchemy session.commit() with rollback on error
- Validation: Test concurrent registration attempts, verify no partial data
- Source: Architecture document (database patterns)

**NFR-2.10: Token Expiration Handling**
- Requirement: Expired tokens handled gracefully with clear error messages
- Implementation: JWT expiration check in dependency, return 401 with clear message
- Validation: Test with expired token, verify user-friendly error response
- Source: PRD Section 16.5 (Error Handling)

**NFR-2.11: Concurrent Login Attempts**
- Requirement: System handles multiple concurrent login/registration requests
- Implementation: FastAPI async support, database connection pooling
- Validation: Load test with 10 concurrent requests
- Source: Architecture document (concurrent users)

### Observability

**NFR-2.12: Authentication Logging**
- Requirement: All authentication events logged (successful login, failed login, registration)
- Implementation: Structured logging in auth routes, log level INFO for success, WARNING for failures
- Log Format: `{"event": "login_success", "username": "...", "timestamp": "..."}`
- Source: PRD Section 9.6 (Logging)

**NFR-2.13: Security Event Logging**
- Requirement: Failed login attempts and suspicious activity logged
- Implementation: Log failed login attempts with username and IP address (if available)
- Log Format: `{"event": "login_failed", "username": "...", "reason": "invalid_password", "timestamp": "..."}`
- Source: PRD Section 16.5 (Error Handling)

**NFR-2.14: Error Message Clarity**
- Requirement: User-friendly error messages (no technical jargon) (PRD Section 9.5, NFR-013)
- Implementation: Error codes and messages defined in error handler, simple JSON structure
- Examples: "Invalid username or password" (not "401 Unauthorized" or "bcrypt verification failed")
- Source: PRD Section 9.5 (Error Messages)

## Dependencies and Integrations

**Backend Dependencies (New for Epic 2):**
- `passlib[bcrypt]` 1.7.4+ (Password hashing with bcrypt)
- `python-jose[cryptography]` 3.3.0+ (JWT token generation and validation)
- `PyJWT` 2.8.0+ (Alternative JWT library, if not using python-jose)

**Backend Dependencies (From Epic 1, Used Here):**
- FastAPI 0.104+ (Web framework)
- SQLAlchemy 2.0+ (ORM for User model)
- Pydantic (Request/response validation)

**Frontend Dependencies (From Epic 1, Used Here):**
- React 18.2+ (UI components)
- TypeScript 5.0+ (Type safety)
- React Router 6+ (Protected routes)
- Zustand 4.4+ (Auth state management)
- Axios 1.6+ (API client with interceptors)

**External Services:**
- None (authentication is self-contained, no external auth providers)

**Database:**
- PostgreSQL (via AWS RDS) or SQLite (development) - User table from Epic 1

**Version Constraints:**
- bcrypt cost factor: 12 (as specified in PRD)
- JWT expiration: 7 days (as specified in PRD)
- All dependencies should use exact versions or version ranges in `requirements.txt` and `package.json`

**Integration Points:**
- Epic 1: Uses User model and database schema
- Epic 3: Provides authentication for video generation endpoints
- Epic 4: Provides authentication for video management endpoints
- Epic 5: Provides authentication for user profile endpoints

## Acceptance Criteria (Authoritative)

**AC-2.1.1: User Registration Backend**
- **Given** a registration request with valid username and password
- **When** the system processes the request
- **Then** a new user account is created with hashed password
- **And** username uniqueness is validated (returns error if duplicate)
- **And** password is hashed using bcrypt with cost factor 12
- **And** response returns 201 Created with user_id

**AC-2.1.2: User Registration Validation**
- **Given** a registration request with invalid data
- **When** the system validates the request
- **Then** validation errors are returned (username too short, password too weak, etc.)
- **And** response returns 422 Unprocessable Entity with error details

**AC-2.1.3: User Login Backend**
- **Given** a login request with valid credentials
- **When** the system authenticates the user
- **Then** a JWT token is generated with 7-day expiration
- **And** user.last_login timestamp is updated
- **And** response returns 200 OK with token and user information

**AC-2.1.4: User Login Failure**
- **Given** a login request with invalid credentials
- **When** the system attempts authentication
- **Then** response returns 401 Unauthorized with error message
- **And** error message is user-friendly ("Invalid username or password")

**AC-2.1.5: Protected Route Authentication**
- **Given** a protected API endpoint
- **When** a request includes a valid JWT token
- **Then** the middleware verifies the token and allows the request
- **And** current user object is available to the route handler

**AC-2.1.6: Protected Route Unauthorized**
- **Given** a protected API endpoint
- **When** a request includes an invalid or expired token
- **Then** response returns 401 Unauthorized with error message
- **And** error message indicates token is invalid or expired

**AC-2.2.1: Registration Form Frontend**
- **Given** I am on the registration page
- **When** I view and submit the registration form
- **Then** I see real-time validation feedback
- **And** I can successfully create an account
- **And** form shows loading state during submission
- **And** success message appears and redirects to login

**AC-2.2.2: Login Form Frontend**
- **Given** I am on the login page
- **When** I submit valid credentials
- **Then** I am authenticated and redirected to dashboard
- **And** token is stored in localStorage
- **And** auth state is updated in Zustand store

**AC-2.2.3: Form Validation**
- **Given** I am on registration or login form
- **When** I enter invalid data
- **Then** validation errors appear in real-time
- **And** submit button is disabled until form is valid
- **And** error messages are clear and actionable

**AC-2.3.1: Protected Route Redirect**
- **Given** I am not logged in
- **When** I try to access a protected route (e.g., `/dashboard`)
- **Then** I am redirected to `/login` page
- **And** the original URL is saved for redirect after login

**AC-2.3.2: Protected Route Access**
- **Given** I am logged in
- **When** I access a protected route
- **Then** the page loads normally
- **And** I can see my username in the navigation

**AC-2.3.3: Token in API Requests**
- **Given** I am logged in
- **When** I make an API request
- **Then** the JWT token is included in Authorization header
- **And** format is: `Authorization: Bearer {token}`

**AC-2.4.1: Logout Functionality**
- **Given** I am logged in
- **When** I click the logout button
- **Then** the system clears JWT token from localStorage
- **And** clears user state from Zustand store
- **And** redirects to login page

**AC-2.4.2: Post-Logout State**
- **Given** I have logged out
- **When** I try to access a protected route
- **Then** I am redirected to login page
- **And** API requests no longer include Authorization header

**AC-2.4.3: 401 Error Handling**
- **Given** I have an expired or invalid token
- **When** I make an API request
- **Then** the response interceptor catches 401 error
- **And** token is cleared from localStorage
- **And** I am redirected to login page

## Traceability Mapping

| AC ID | Spec Section | Component(s)/Module(s) | Test Idea |
|-------|--------------|------------------------|-----------|
| AC-2.1.1 | APIs and Interfaces | `backend/app/api/routes/auth.py` (register endpoint) | POST request with valid data, verify 201 response, check user created in DB |
| AC-2.1.2 | APIs and Interfaces | `backend/app/schemas/auth.py` (UserRegister schema) | POST request with invalid data, verify 422 response with validation errors |
| AC-2.1.3 | APIs and Interfaces | `backend/app/api/routes/auth.py` (login endpoint) | POST request with valid credentials, verify 200 response with JWT token |
| AC-2.1.4 | APIs and Interfaces | `backend/app/api/routes/auth.py` (login endpoint) | POST request with invalid credentials, verify 401 response |
| AC-2.1.5 | APIs and Interfaces | `backend/app/api/deps.py` (get_current_user dependency) | GET request to protected endpoint with valid token, verify user object available |
| AC-2.1.6 | APIs and Interfaces | `backend/app/api/deps.py` (get_current_user dependency) | GET request with invalid/expired token, verify 401 response |
| AC-2.2.1 | Services and Modules | `frontend/src/routes/Auth/Register.tsx` | Fill form, submit, verify success message and redirect |
| AC-2.2.2 | Services and Modules | `frontend/src/routes/Auth/Login.tsx` | Fill form, submit, verify token stored and redirect |
| AC-2.2.3 | Services and Modules | `frontend/src/routes/Auth/*.tsx` (form components) | Enter invalid data, verify validation messages appear |
| AC-2.3.1 | Services and Modules | `frontend/src/components/ProtectedRoute.tsx` | Navigate to protected route without auth, verify redirect |
| AC-2.3.2 | Services and Modules | `frontend/src/components/ProtectedRoute.tsx` | Navigate to protected route with auth, verify page loads |
| AC-2.3.3 | Services and Modules | `frontend/src/lib/apiClient.ts` (request interceptor) | Make API request, inspect headers, verify Authorization header present |
| AC-2.4.1 | Services and Modules | `frontend/src/store/authStore.ts` (logout function) | Click logout, verify token cleared and redirect |
| AC-2.4.2 | Workflows and Sequencing | `frontend/src/components/ProtectedRoute.tsx` | Logout, then navigate to protected route, verify redirect |
| AC-2.4.3 | Services and Modules | `frontend/src/lib/apiClient.ts` (response interceptor) | Make request with expired token, verify 401 handling and redirect |

## Risks, Assumptions, Open Questions

**Risk-2.1: JWT Token Security**
- **Risk:** JWT tokens stored in localStorage are vulnerable to XSS attacks
- **Mitigation:** Use httpOnly cookies for production (post-MVP), implement Content Security Policy (CSP)
- **Status:** Accepted for MVP (localStorage is acceptable for MVP, upgrade to httpOnly cookies in post-MVP)

**Risk-2.2: Password Strength**
- **Risk:** Users may choose weak passwords despite minimum length requirement
- **Mitigation:** Enforce minimum 8 characters, consider password strength meter (post-MVP)
- **Status:** Mitigated - minimum 8 characters enforced, strength meter deferred to post-MVP

**Risk-2.3: Concurrent Registration**
- **Risk:** Race condition when two users register with same username simultaneously
- **Mitigation:** Database unique constraint prevents duplicates, handle IntegrityError gracefully
- **Status:** Mitigated - unique constraint at database level

**Risk-2.4: Token Expiration UX**
- **Risk:** Users may lose work if token expires during long session
- **Mitigation:** 7-day expiration is reasonable, show warning before expiration (post-MVP)
- **Status:** Accepted for MVP, warning system deferred to post-MVP

**Assumption-2.1: Username Format**
- **Assumption:** Usernames are alphanumeric with underscores (regex: `^[a-zA-Z0-9_]+$`)
- **Validation:** Enforced in Pydantic schema, tested with various inputs
- **Status:** Documented and implemented

**Assumption-2.2: Email Optional**
- **Assumption:** Email field is optional, no email verification in MVP
- **Validation:** Email can be null in database, no email-related features in MVP
- **Status:** Documented in PRD and implemented

**Question-2.1: Token Refresh Strategy**
- **Question:** Should we implement token refresh mechanism or require re-login after 7 days?
- **Decision:** For MVP, require re-login after token expiration. Token refresh can be added post-MVP.
- **Status:** Resolved - no refresh mechanism in MVP

**Question-2.2: Remember Me Functionality**
- **Question:** Should we implement "Remember Me" to extend token expiration?
- **Decision:** Deferred to post-MVP. Standard 7-day expiration for all users in MVP.
- **Status:** Resolved - deferred to post-MVP

**Question-2.3: Account Lockout**
- **Question:** Should we implement account lockout after multiple failed login attempts?
- **Decision:** Deferred to post-MVP. Log failed attempts for monitoring.
- **Status:** Resolved - deferred to post-MVP

## Test Strategy Summary

**Unit Tests (Backend):**
- Test password hashing with bcrypt (verify cost factor 12)
- Test JWT token generation and validation
- Test username uniqueness validation
- Test Pydantic schema validation (username format, password length)
- Test password verification (correct and incorrect passwords)
- Test token expiration logic

**Unit Tests (Frontend):**
- Test authStore state management (login, logout, register)
- Test form validation logic
- Test ProtectedRoute component (redirect when not authenticated)
- Test API client interceptors (token injection, 401 handling)

**Integration Tests:**
- Test complete registration flow (frontend form → backend API → database)
- Test complete login flow (frontend form → backend API → token storage)
- Test protected route access with valid token
- Test protected route rejection with invalid/expired token
- Test logout flow (clear token, redirect)
- Test 401 error handling and automatic redirect

**Manual Testing:**
- Test registration form with various inputs (valid, invalid, edge cases)
- Test login form with valid and invalid credentials
- Test protected route access (authenticated and unauthenticated states)
- Test logout functionality
- Test token expiration (wait 7 days or manually expire token)
- Test concurrent registration attempts (same username)
- Test browser refresh with stored token (verify token persists)

**Security Testing:**
- Test SQL injection attempts in username/password fields
- Test XSS attempts in username field
- Test password hashing (verify plain text never stored)
- Test JWT token tampering (modify token, verify rejection)
- Test expired token handling
- Test unauthorized access to protected endpoints

**Test Coverage Goals:**
- Backend: 80%+ coverage for auth routes and security utilities
- Frontend: 70%+ coverage for auth components and store
- Integration: All critical user flows covered

**Test Frameworks:**
- Backend: pytest with FastAPI TestClient
- Frontend: Vitest or React Testing Library
- E2E: Not required for Epic 2 (can be added in Epic 3+)

