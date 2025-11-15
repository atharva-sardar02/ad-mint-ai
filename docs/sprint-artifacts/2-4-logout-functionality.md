# Story 2.4: Logout Functionality

Status: ready-for-dev

## Story

As a user,
I want to log out of my account,
so that my session is cleared and I return to the login page.

## Acceptance Criteria

1. **Logout Functionality:**
   **Given** I am logged in
   **When** I click the logout button
   **Then** the system clears JWT token from localStorage
   **And** clears user state from Zustand store
   **And** redirects to login page

2. **Post-Logout State:**
   **Given** I have logged out
   **When** I try to access a protected route
   **Then** I am redirected to login page
   **And** API requests no longer include Authorization header

3. **401 Error Handling:**
   **Given** I have an expired or invalid token
   **When** I make an API request
   **Then** the response interceptor catches 401 error
   **And** token is cleared from localStorage
   **And** I am redirected to login page

[Source: docs/epics.md#Story-2.4]
[Source: docs/sprint-artifacts/tech-spec-epic-2.md#AC-2.4.1]
[Source: docs/sprint-artifacts/tech-spec-epic-2.md#AC-2.4.2]
[Source: docs/sprint-artifacts/tech-spec-epic-2.md#AC-2.4.3]

## Tasks / Subtasks

- [ ] Task 1: Implement Logout Function in Auth Service (AC: 1)
  - [ ] Update `frontend/src/lib/authService.ts` logout function
  - [ ] Ensure logout clears token from localStorage
  - [ ] Add TypeScript return type annotations
  - [ ] Handle any errors gracefully

- [ ] Task 2: Update Zustand Auth Store Logout Action (AC: 1)
  - [ ] Update `frontend/src/store/authStore.ts` logout action
  - [ ] Clear token from localStorage
  - [ ] Reset user state to null
  - [ ] Set isAuthenticated to false
  - [ ] Ensure state updates are atomic

- [ ] Task 3: Add Logout Button to Navigation (AC: 1)
  - [ ] Create or update navigation component (e.g., `frontend/src/components/layout/Navbar.tsx`)
  - [ ] Add logout button that calls authStore.logout()
  - [ ] Show logout button only when user is authenticated
  - [ ] Style logout button with Tailwind CSS
  - [ ] Ensure mobile-responsive design
  - [ ] Add loading state during logout (optional: show spinner)

- [ ] Task 4: Implement Redirect After Logout (AC: 1)
  - [ ] Update logout action to redirect to `/login` after clearing state
  - [ ] Use React Router's `useNavigate` hook or programmatic navigation
  - [ ] Ensure redirect happens after state is cleared
  - [ ] Handle edge cases (e.g., logout while on login page)

- [ ] Task 5: Verify Protected Route Redirect After Logout (AC: 2)
  - [ ] Test that ProtectedRoute component redirects unauthenticated users
  - [ ] Verify redirect works after logout
  - [ ] Ensure original URL is not saved after logout (should not redirect back)
  - [ ] Test navigation to protected routes after logout

- [ ] Task 6: Verify API Client Interceptor Behavior (AC: 2, 3)
  - [ ] Verify request interceptor no longer adds Authorization header after logout
  - [ ] Test that 401 errors trigger logout and redirect (already implemented in Story 2.2)
  - [ ] Ensure token is cleared from localStorage on 401
  - [ ] Verify auth state is cleared on 401

- [ ] Task 7: Testing (AC: 1, 2, 3)
  - [ ] Create unit tests for authStore.logout() action
  - [ ] Create unit tests for authService.logout() function
  - [ ] Create integration test: logout flow (click logout → state cleared → redirect)
  - [ ] Create integration test: protected route access after logout
  - [ ] Create integration test: 401 error handling (if not already covered)
  - [ ] Test logout from different pages (dashboard, gallery, profile)
  - [ ] Test logout with expired token scenario

[Source: docs/sprint-artifacts/tech-spec-epic-2.md#Services-and-Modules]
[Source: docs/sprint-artifacts/tech-spec-epic-2.md#Workflows-and-Sequencing]

## Dev Notes

### Architecture Patterns and Constraints

- **Frontend Framework:** React 18 + TypeScript + Vite (from Epic 1)
- **State Management:** Zustand for auth state (lightweight, as per architecture)
- **Routing:** React Router 6+ for page-based routing structure
- **Navigation:** Logout button should be accessible from authenticated pages (dashboard, gallery, profile)
- **Token Management:** localStorage for JWT tokens (acceptable for MVP, consider httpOnly cookies post-MVP)
- **Error Handling:** User-friendly error messages (no technical jargon), follow PRD error structure
- **API Client:** Axios interceptors already configured in Story 2.2 for token injection and 401 handling

[Source: docs/architecture.md#Decision-Summary]
[Source: docs/architecture.md#Project-Structure]
[Source: docs/sprint-artifacts/tech-spec-epic-2.md#System-Architecture-Alignment]
[Source: docs/PRD.md#Non-Functional-Requirements]

### Project Structure Notes

- **Frontend Services:** `frontend/src/lib/authService.ts` - Auth API service functions (update logout function)
- **Frontend Store:** `frontend/src/store/authStore.ts` - Zustand store for authentication state (update logout action)
- **Frontend Components:** `frontend/src/components/layout/Navbar.tsx` or similar - Navigation component with logout button
- **Frontend Routes:** Logout should work from any authenticated page (dashboard, gallery, profile)
- **Frontend API Client:** `frontend/src/lib/apiClient.ts` - Axios instance with interceptors (already configured in Story 2.2)
- **Testing:** `frontend/tests/` or `frontend/src/__tests__/` - Unit and integration tests for logout functionality

[Source: docs/architecture.md#Project-Structure]
[Source: docs/sprint-artifacts/tech-spec-epic-2.md#Services-and-Modules]

### Learnings from Previous Story

**From Story 2-2-authentication-frontend (Status: done)**

- **Auth Store Structure:** Zustand authStore has `logout` action that needs to be enhanced - currently clears token and user state, but may need redirect logic
- **Token Storage:** JWT tokens stored in localStorage via `localStorage.setItem('token', ...)` - logout should use `localStorage.removeItem('token')`
- **API Client Interceptors:** Request interceptor reads token from localStorage and adds to Authorization header - after logout, token should be null, so no header added
- **Response Interceptor:** 401 error handling already implemented in Story 2.2 - clears token, clears auth state, redirects to `/login` - logout should follow similar pattern
- **Navigation:** React Router setup already configured in Story 2.2 - use `useNavigate` hook or programmatic navigation for redirect
- **Protected Routes:** ProtectedRoute component already implemented in Story 2.3 - checks `authStore.isAuthenticated` and redirects if false - logout should set this to false

**New Files Created (to reference):**
- `frontend/src/lib/authService.ts` - Auth service with logout function (needs enhancement)
- `frontend/src/store/authStore.ts` - Zustand auth store with logout action (needs enhancement)
- `frontend/src/lib/apiClient.ts` - API client with interceptors (already handles 401, no changes needed)
- `frontend/src/components/ProtectedRoute.tsx` - Protected route component (from Story 2.3, works with auth state)

**Architectural Decisions:**
- Logout should be a simple action that clears state and redirects - no API call needed (JWT tokens are stateless)
- Logout button should be visible in navigation when authenticated - consider adding to Navbar component
- After logout, user should be redirected to login page - do not save return URL (unlike protected route redirect)
- 401 error handling already triggers logout-like behavior - ensure logout action is consistent with this

**Testing Patterns:**
- Unit tests for authStore and authService should test logout action
- Integration tests should verify complete logout flow: click logout → state cleared → redirect → protected route blocks access
- Test logout from different pages to ensure consistent behavior

[Source: docs/sprint-artifacts/2-2-authentication-frontend.md#Dev-Agent-Record]
[Source: docs/sprint-artifacts/2-2-authentication-frontend.md#Completion-Notes-List]
[Source: docs/sprint-artifacts/2-2-authentication-frontend.md#File-List]

### References

- [Source: docs/epics.md#Story-2.4] - Story requirements and acceptance criteria
- [Source: docs/sprint-artifacts/tech-spec-epic-2.md#AC-2.4.1] - Logout functionality acceptance criteria
- [Source: docs/sprint-artifacts/tech-spec-epic-2.md#AC-2.4.2] - Post-logout state acceptance criteria
- [Source: docs/sprint-artifacts/tech-spec-epic-2.md#AC-2.4.3] - 401 error handling acceptance criteria
- [Source: docs/sprint-artifacts/tech-spec-epic-2.md#Logout-Workflow] - Logout workflow details
- [Source: docs/sprint-artifacts/tech-spec-epic-2.md#Services-and-Modules] - Frontend services and modules specifications
- [Source: docs/architecture.md#Decision-Summary] - Architecture decisions for frontend (React, TypeScript, Zustand, Tailwind)
- [Source: docs/architecture.md#Project-Structure] - Frontend project structure and organization
- [Source: docs/PRD.md#User-Interface-Design] - UI design principles and navigation requirements
- [Source: docs/PRD.md#Non-Functional-Requirements] - Usability requirements (NFR-012, NFR-013)

## Dev Agent Record

### Context Reference

- `docs/sprint-artifacts/2-4-logout-functionality.context.xml`

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

## Change Log

- 2025-11-14: Story drafted from epics.md and tech-spec-epic-2.md

