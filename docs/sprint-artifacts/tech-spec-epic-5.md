# Epic Technical Specification: User Profile

Date: 2025-11-15
Author: BMad
Epic ID: 5
Status: Draft

---

## Overview

Epic 5 implements user profile display and automatic statistics tracking for the AI Video Ad Generator application. This epic enables users to view their account information, track their usage statistics (total videos generated, total cost spent), and see account metadata (creation date, last login). As outlined in the PRD (Section 8.4), the system provides a profile page that displays user statistics, account creation date, and last login timestamp. Additionally, the system automatically updates user statistics when video generations complete and when users log in. This epic builds upon Epic 1 (database models with user statistics fields), Epic 2 (authentication and protected routes), and depends on Epic 3 (video generation pipeline) for statistics updates. The profile display provides users with visibility into their usage and costs, enabling them to track their activity and spending on the platform.

## Objectives and Scope

**In-Scope:**
- Backend profile endpoint (`GET /api/user/profile`) that returns user information and statistics
- User profile response schema with all required fields (id, username, email, total_generations, total_cost, created_at, last_login)
- Frontend profile page component (`Profile.tsx`) that displays user information and statistics
- Date formatting for account creation ("Member since: {month} {year}") and last login (relative time)
- Currency formatting for total cost display
- Loading and error states for profile page
- Responsive design for mobile, tablet, and desktop
- Automatic user statistics updates:
  - Increment `total_generations` when video generation completes
  - Add generation cost to `total_cost` when video generation completes
  - Update `last_login` timestamp on successful login
- Atomic database transactions for statistics updates
- Profile route integration in navigation (already exists in Navbar)

**Out-of-Scope:**
- User profile editing (change username, email, password) (post-MVP)
- Profile picture upload (post-MVP)
- Account deletion (post-MVP)
- Usage analytics and charts (post-MVP)
- Export user data (post-MVP)
- Profile privacy settings (post-MVP)
- User preferences/settings page (post-MVP)

## System Architecture Alignment

This epic implements the user profile functionality described in the PRD (Section 8.4) and architecture document. The backend profile endpoint follows the FastAPI pattern established in Epic 2, using the existing authentication dependency (`get_current_user` from `app/api/deps.py`) to ensure only authenticated users can access their profile. The User model from Epic 1 already includes all required fields (total_generations, total_cost, created_at, last_login), so no database schema changes are needed. The frontend profile page uses React Router's page-based routing structure (already configured in `App.tsx` with ProtectedRoute wrapper) and follows the architecture's component composition patterns. The profile page can use local component state for MVP, with optional Zustand userStore for future enhancements, consistent with the architecture's lightweight state management approach. Statistics updates are integrated into the video generation pipeline (Epic 3) and login endpoint (Epic 2), following the architecture's service layer pattern for business logic.

## Detailed Design

### Services and Modules

| Module/Service | Responsibility | Inputs | Outputs | Owner |
|----------------|----------------|--------|---------|-------|
| `backend/app/api/routes/users.py` | User profile route handler (`GET /api/user/profile`) | HTTP request with JWT token | User profile response | Backend |
| `backend/app/schemas/user.py` | User profile response schema (UserProfile) | User model data | Validated Pydantic schema | Backend |
| `backend/app/api/deps.py` | Authentication dependency (reuse from Epic 2) | HTTP request with Authorization header | Current user object | Backend |
| `backend/app/db/models/user.py` | User ORM model (from Epic 1, used here) | - | User model with statistics | Backend |
| `backend/app/api/routes/auth.py` | Login endpoint (update last_login) | Login request | Login response | Backend |
| `backend/app/services/cost_tracking.py` | Update user statistics after generation (from Epic 3) | Generation completion event | Updated user statistics | Backend |
| `frontend/src/routes/Profile.tsx` | Profile page component | - | Profile UI with user info and statistics | Frontend |
| `frontend/src/lib/userService.ts` | Profile API service function | - | User profile data | Frontend |
| `frontend/src/lib/apiClient.ts` | API client with interceptors (reuse from Epic 1/2) | API requests | Requests with token | Frontend |
| `frontend/src/components/layout/Navbar.tsx` | Navigation component (Profile link already exists) | - | Navigation with Profile link | Frontend |
| `frontend/src/components/ProtectedRoute.tsx` | Protected route wrapper (reuse from Epic 2) | Route component | Protected route or redirect | Frontend |

### Data Models and Contracts

**User Model (from Epic 1, used in Epic 5):**
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=uuid4)  # UUID
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # bcrypt hash
    email = Column(String(255), nullable=True)
    total_generations = Column(Integer, default=0)  # Updated in Epic 5
    total_cost = Column(Float, default=0.0)  # Updated in Epic 5
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # Displayed in Epic 5
    last_login = Column(DateTime, nullable=True)  # Updated on login, displayed in Epic 5
    
    # Relationship
    generations = relationship("Generation", back_populates="user")
```

**Pydantic Response Schema (`backend/app/schemas/user.py`):**
```python
class UserProfile(BaseModel):
    """Schema for user profile response."""
    
    id: str
    username: str
    email: Optional[str]
    total_generations: int
    total_cost: float
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True
```

**Frontend TypeScript Interface (`frontend/src/lib/types/api.ts`):**
```typescript
interface UserProfile {
  id: string;
  username: string;
  email: string | null;
  total_generations: number;
  total_cost: number;
  created_at: string;  // ISO datetime string
  last_login: string | null;  // ISO datetime string or null
}
```

### APIs and Interfaces

**GET /api/user/profile**
- **Description:** Get current authenticated user's profile and statistics
- **Method:** GET
- **Path:** `/api/user/profile`
- **Headers:** `Authorization: Bearer {jwt_token}`
- **Request:** None (user identified from JWT token)
- **Response (200 OK):**
  ```json
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "john_doe",
    "email": "john@example.com",
    "total_generations": 45,
    "total_cost": 87.32,
    "created_at": "2025-11-10T08:30:00Z",
    "last_login": "2025-11-14T10:15:00Z"
  }
  ```
- **Error Responses:**
  - `401 Unauthorized`: Invalid or expired token
    ```json
    {
      "error": {
        "code": "INVALID_TOKEN",
        "message": "Invalid or expired token"
      }
    }
    ```
  - `404 Not Found`: User not found (should not occur with valid token)
    ```json
    {
      "error": {
        "code": "USER_NOT_FOUND",
        "message": "User not found"
      }
    }
    ```

**POST /api/auth/login (Update - Story 5.2)**
- **Description:** Login endpoint (already exists, update to set last_login timestamp)
- **Method:** POST
- **Path:** `/api/auth/login`
- **Request:** `{ "username": "string", "password": "string" }`
- **Response:** TokenResponse (unchanged)
- **Side Effect:** Updates `user.last_login = datetime.utcnow()` on successful login

**Video Generation Completion (Update - Story 5.2)**
- **Description:** Update user statistics when video generation completes
- **Trigger:** Video generation pipeline completes successfully
- **Action:** 
  - Increment `user.total_generations += 1`
  - Add `user.total_cost += generation.cost`
- **Location:** `backend/app/services/cost_tracking.py` or generation completion handler
- **Transaction:** Must be atomic (database transaction)

### Workflows and Sequencing

**Profile Display Workflow (Story 5.1):**
1. User navigates to `/profile` route
2. ProtectedRoute component checks authentication (redirects to login if not authenticated)
3. Profile component mounts and calls `getUserProfile()` API function
4. API function makes GET request to `/api/user/profile` with JWT token in Authorization header
5. Backend endpoint uses `get_current_user` dependency to extract and verify JWT token
6. Backend queries User model from database using user_id from token
7. Backend serializes User model to UserProfile schema (includes all fields)
8. Backend returns 200 OK with UserProfile JSON response
9. Frontend receives response and formats data:
   - Format `created_at` as "Member since: {month} {year}" (e.g., "Member since: Nov 2025")
   - Format `total_cost` as currency (e.g., "$24.50")
   - Format `last_login` as relative time (e.g., "2 hours ago", "3 days ago")
10. Frontend displays formatted data in Profile component UI
11. If error occurs (401, 404, network), frontend displays error message

**User Statistics Update Workflow (Story 5.2):**
1. Video generation completes successfully (Epic 3)
2. Generation service calculates final cost and updates generation record
3. Generation service calls user statistics update function
4. Update function starts database transaction
5. Update function queries current user record
6. Update function increments `user.total_generations += 1`
7. Update function adds `user.total_cost += generation.cost`
8. Update function commits transaction (atomic operation)
9. User sees updated statistics on next profile page view

**Last Login Update Workflow (Story 5.2):**
1. User submits login credentials (Epic 2)
2. Login endpoint verifies credentials
3. Login endpoint generates JWT token
4. Login endpoint updates `user.last_login = datetime.utcnow()`
5. Login endpoint commits database transaction
6. Login endpoint returns token response
7. User sees updated last_login on profile page

## Non-Functional Requirements

### Performance

- **Profile Endpoint Response Time:** < 200ms (target: < 100ms)
  - Database query for user by ID is indexed (user.id is primary key)
  - Single database query, no joins required
  - Minimal serialization overhead (Pydantic schema)
- **Profile Page Load Time:** < 1 second (target: < 500ms)
  - Single API call on component mount
  - Client-side date/currency formatting (minimal computation)
  - No heavy data processing on frontend
- **Statistics Update Performance:** < 50ms per update
  - Atomic database transaction (single UPDATE query)
  - No impact on video generation pipeline performance
  - Statistics updates are non-blocking

[Source: docs/PRD.md#NFR-002 - API Response Time requirements]

### Security

- **Authentication Required:** Profile endpoint requires valid JWT token
  - Uses existing `get_current_user` dependency from Epic 2
  - Token verification and expiration checking handled by dependency
  - 401 error returned for invalid/expired tokens
- **User Data Access:** Users can only access their own profile
  - User identified from JWT token (user_id in token payload)
  - No user_id parameter in endpoint (prevents access to other users' profiles)
  - Database query uses user_id from token, not from request
- **Data Privacy:** Profile data only includes user's own statistics
  - No exposure of other users' data
  - Statistics are user-specific (total_generations, total_cost are per-user)

[Source: docs/PRD.md#NFR-009 - Authentication Security, NFR-010 - Data Privacy]

### Reliability/Availability

- **Profile Endpoint Availability:** 99%+ uptime (same as overall API)
  - No external dependencies (only database query)
  - Graceful error handling for database connection issues
  - Returns appropriate error codes (401, 404, 500)
- **Statistics Update Reliability:** Atomic transactions ensure data consistency
  - Database transactions prevent partial updates
  - If generation completes but statistics update fails, generation is still marked complete (statistics can be recalculated)
  - No race conditions (database-level locking)
- **Data Accuracy:** Statistics are always accurate
  - Atomic updates prevent inconsistent state
  - Single source of truth (User model in database)
  - No caching of statistics (always read from database)

[Source: docs/PRD.md#NFR-004 - Success Rate, NFR-005 - System Uptime]

### Observability

- **Logging:** Log profile endpoint access and statistics updates
  - Log profile endpoint requests (user_id, response time)
  - Log statistics updates (user_id, old values, new values)
  - Log errors (authentication failures, database errors)
- **Metrics:** Track profile page usage
  - Count of profile page views
  - Profile endpoint response times
  - Statistics update frequency
- **Error Tracking:** Monitor profile-related errors
  - 401 errors (authentication issues)
  - 404 errors (user not found - should not occur)
  - 500 errors (database or server errors)

[Source: docs/architecture.md#Security and Performance Considerations - Logging requirements]

## Dependencies and Integrations

**Backend Dependencies:**
- FastAPI >= 0.104.0 (HTTP framework)
- SQLAlchemy >= 2.0.0 (ORM for User model queries)
- Pydantic >= 2.0.0 (UserProfile schema validation)
- PyJWT >= 2.8.0 (JWT token verification via get_current_user dependency)

**Frontend Dependencies:**
- React >= 18.2.0 (Profile component)
- React Router >= 6.0 (Profile route, already configured)
- Axios >= 1.6.0 (API client for profile endpoint)
- TypeScript >= 5.0 (Type safety for UserProfile interface)

**Internal Dependencies:**
- Epic 1: User model with statistics fields (total_generations, total_cost, created_at, last_login)
- Epic 2: Authentication dependency (`get_current_user`), ProtectedRoute component, API client interceptors
- Epic 3: Video generation pipeline (for statistics updates in Story 5.2)

**External Integrations:**
- None (profile functionality is self-contained, no external APIs)

## Acceptance Criteria (Authoritative)

**Story 5.1: Profile Display**

1. **AC-5.1.1: Backend Profile Endpoint**
   - **Given** I am logged in
   - **When** I request my profile via GET `/api/user/profile`
   - **Then** the system returns user information and statistics (total_generations, total_cost, created_at, last_login, username, email)

2. **AC-5.1.2: Frontend Profile Page Display**
   - **Given** I am logged in
   - **When** I navigate to the profile page
   - **Then** I see:
     - Username and email (if provided)
     - Account creation date: "Member since: {month} {year}"
     - Statistics section:
       - Total Videos Generated: {total_generations}
       - Total Cost Spent: ${total_cost} (formatted as currency)
       - Last Login: {last_login} (formatted as relative time, e.g., "2 hours ago")
     - Logout button

3. **AC-5.1.3: Profile Page Behavior**
   - **Given** I am on the profile page
   - **When** the page loads
   - **Then** it makes an API call to `/api/user/profile` on mount
   - **And** shows a loading state while fetching
   - **And** displays error message if fetch fails
   - **And** has responsive design (works on mobile, tablet, desktop)

**Story 5.2: User Stats Update**

4. **AC-5.2.1: Statistics Update on Generation Completion**
   - **Given** a video generation completes
   - **When** the generation service finishes
   - **Then** the system:
     - Increments `user.total_generations` by 1
     - Adds `generation.cost` to `user.total_cost`

5. **AC-5.2.2: Last Login Update**
   - **Given** a user logs in successfully
   - **When** the login endpoint processes the request
   - **Then** the system updates `user.last_login` to the current timestamp

6. **AC-5.2.3: Atomic Statistics Updates**
   - **Given** statistics updates occur
   - **When** the update is processed
   - **Then** updates are atomic (database transaction ensures consistency)
   - **And** updates are immediate (user sees updated stats on next profile view)
   - **And** updates are accurate (no race conditions, proper locking if needed)

[Source: docs/epics.md#Epic-5]

## Traceability Mapping

| AC ID | Spec Section | Component(s)/API(s) | Test Idea |
|-------|--------------|---------------------|-----------|
| AC-5.1.1 | PRD 14.4, Architecture Epic Mapping | `GET /api/user/profile`, `backend/app/api/routes/users.py`, `backend/app/schemas/user.py`, `backend/app/api/deps.py` | Test endpoint returns all required fields with valid JWT token |
| AC-5.1.1 | PRD 14.4 | `GET /api/user/profile` | Test endpoint returns 401 without token |
| AC-5.1.2 | PRD 13.2, Epics 5.1 | `frontend/src/routes/Profile.tsx` | Test Profile component displays username, email, formatted dates, statistics |
| AC-5.1.2 | PRD 13.2 | `frontend/src/routes/Profile.tsx` | Test Profile component handles missing email gracefully |
| AC-5.1.3 | PRD NFR-012 | `frontend/src/routes/Profile.tsx`, `frontend/src/lib/userService.ts` | Test Profile component makes API call on mount |
| AC-5.1.3 | PRD NFR-012 | `frontend/src/routes/Profile.tsx` | Test Profile component shows loading state |
| AC-5.1.3 | PRD NFR-013 | `frontend/src/routes/Profile.tsx` | Test Profile component displays error message on API failure |
| AC-5.1.3 | PRD NFR-012 | `frontend/src/routes/Profile.tsx` | Test Profile component is responsive (mobile, tablet, desktop) |
| AC-5.2.1 | PRD FR-023, Epics 5.2 | `backend/app/services/cost_tracking.py` or generation completion handler | Test total_generations increments on generation completion |
| AC-5.2.1 | PRD FR-023 | Generation completion handler | Test total_cost adds generation cost on completion |
| AC-5.2.2 | PRD FR-023, Epics 5.2 | `backend/app/api/routes/auth.py` (login endpoint) | Test last_login updates on successful login |
| AC-5.2.3 | PRD FR-023 | Statistics update function | Test statistics updates are atomic (transaction rollback on error) |
| AC-5.2.3 | PRD FR-023 | Statistics update function | Test no race conditions with concurrent updates |

## Risks, Assumptions, Open Questions

**Risks:**
- **Risk:** Statistics updates may fail silently if generation completes but update transaction fails
  - **Mitigation:** Log all statistics update failures, consider retry mechanism, statistics can be recalculated from generations table if needed
- **Risk:** Profile page may show stale data if user has multiple tabs open
  - **Mitigation:** Acceptable for MVP (data is eventually consistent), can add refresh button or auto-refresh post-MVP
- **Risk:** Date formatting may be inconsistent across browsers/locales
  - **Mitigation:** Use consistent date formatting library (date-fns) or JavaScript Intl API, test across browsers

**Assumptions:**
- User model fields (total_generations, total_cost, created_at, last_login) already exist from Epic 1
- Authentication dependency (`get_current_user`) already exists from Epic 2
- ProtectedRoute component already exists from Epic 2
- Profile route is already configured in App.tsx from Epic 2
- Video generation pipeline (Epic 3) will trigger statistics updates when complete
- Login endpoint (Epic 2) can be updated to set last_login timestamp

**Open Questions:**
- Should profile page auto-refresh statistics periodically? (Decision: No for MVP, manual refresh acceptable)
- Should we cache profile data in frontend state? (Decision: No for MVP, fetch on mount is acceptable)
- Should statistics updates be asynchronous/background jobs? (Decision: No for MVP, synchronous updates are acceptable)

## Test Strategy Summary

**Backend Testing:**
- **Unit Tests:** Test UserProfile schema serialization, test statistics update functions
- **Integration Tests:** Test profile endpoint with valid/invalid tokens, test statistics updates on generation completion, test last_login update on login
- **Test Framework:** pytest with httpx for API testing
- **Test Location:** `backend/tests/test_user_profile.py`, `backend/tests/test_user_stats.py`

**Frontend Testing:**
- **Unit Tests:** Test Profile component rendering, test date/currency formatting functions, test loading/error states
- **Integration Tests:** Test profile page API call, test error handling, test responsive design
- **Test Framework:** vitest with @testing-library/react
- **Test Location:** `frontend/src/__tests__/Profile.test.tsx`, `frontend/src/__tests__/userService.test.ts`

**Test Coverage:**
- All acceptance criteria covered by tests
- Edge cases: missing email, null last_login, zero generations/cost
- Error cases: 401, 404, network errors
- Responsive design: mobile, tablet, desktop breakpoints

[Source: docs/architecture.md#Implementation Patterns - Testing requirements]

