# Story 7.0: Coherence Settings UI Panel

Status: ready-for-dev

## Story

As a user,
I want to see and control which coherence techniques are applied to my video generation,
so that I can customize the quality and consistency settings based on my needs.

## Acceptance Criteria

1. **Coherence Settings Panel Display:**
   **Given** I am on the video generation page
   **When** I view the generation form
   **Then** I see an expandable "Advanced Coherence Settings" section with checkboxes for:
   - ☑ Seed Control (enabled by default, recommended)
   - ☑ IP-Adapter for Character/Product Consistency (enabled by default if entities detected)
   - ☐ LoRA Training (disabled by default, requires trained LoRA)
   - ☑ Enhanced LLM Planning (enabled by default, recommended)
   - ☑ VBench Quality Control (enabled by default, recommended)
   - ☑ Post-Processing Enhancement (enabled by default, recommended)
   - ☐ ControlNet for Compositional Consistency (disabled by default, advanced)
   - ☐ CSFD Character Consistency Detection (disabled by default, character-driven ads only)

2. **Settings Display Details:**
   **Given** I view the coherence settings panel
   **When** I examine each option
   **Then** I see:
   - Checkbox/toggle for each technique
   - Brief description of what each technique does
   - Default state (enabled/disabled)
   - Estimated impact on generation time (if applicable)
   - Estimated impact on cost (if applicable)
   - Tooltip with more details on hover/click

3. **Settings Persistence:**
   **Given** I configure coherence settings
   **When** I submit the video generation
   **Then** the system:
   - Sends selected settings to backend API
   - Stores settings with generation record
   - Applies only selected techniques during generation
   - Remembers my preferences for next generation (optional)

4. **Settings Validation:**
   **Given** I configure coherence settings
   **When** I select/deselect options
   **Then** the system:
   - Shows dependencies (e.g., "IP-Adapter requires Enhanced Planning")
   - Disables incompatible options
   - Shows warnings for recommended combinations
   - Validates settings before submission

[Source: docs/epics.md#Story-7.0]
[Source: docs/sprint-artifacts/tech-spec-epic-7.md#Acceptance-Criteria]

## Tasks / Subtasks

- [ ] Task 1: Create CoherenceSettingsPanel React Component (AC: 1, 2)
  - [ ] Create `frontend/src/components/coherence/CoherenceSettingsPanel.tsx`
  - [ ] Implement expandable/collapsible section UI
  - [ ] Create checkbox/toggle controls for each coherence technique
  - [ ] Add brief descriptions for each technique
  - [ ] Display default state (enabled/disabled) for each option
  - [ ] Show estimated time/cost impact indicators
  - [ ] Implement tooltips with detailed explanations
  - [ ] Style component using Tailwind CSS to match Dashboard design
  - [ ] Make component responsive (mobile, tablet, desktop)
  - [ ] Unit test: Component renders with default settings
  - [ ] Unit test: Component toggles expand/collapse correctly
  - [ ] Unit test: Checkboxes update state correctly

- [ ] Task 2: Integrate CoherenceSettingsPanel into Dashboard (AC: 1, 3)
  - [ ] Import CoherenceSettingsPanel into `frontend/src/routes/Dashboard.tsx`
  - [ ] Add panel below prompt input form (before generate button)
  - [ ] Manage coherence settings state in Dashboard component
  - [ ] Pass settings to generation API call
  - [ ] Ensure settings are included in generation request payload
  - [ ] Test: Settings persist through form submission
  - [ ] Integration test: Full generation flow with coherence settings

- [ ] Task 3: Implement Settings Validation Logic (AC: 4)
  - [ ] Create validation function for coherence settings dependencies
  - [ ] Implement dependency checking (e.g., IP-Adapter requires Enhanced Planning)
  - [ ] Add logic to disable incompatible options
  - [ ] Show warning messages for recommended combinations
  - [ ] Validate settings before form submission
  - [ ] Display validation errors to user
  - [ ] Unit test: Dependency validation works correctly
  - [ ] Unit test: Incompatible options are disabled
  - [ ] Unit test: Warnings display for recommended combinations

- [ ] Task 4: Update Backend Generation Schema (AC: 3)
  - [ ] Add `coherence_settings` JSON field to `Generation` model in `backend/app/db/models/generation.py`
  - [ ] Update Pydantic schema in `backend/app/schemas/generation.py` to accept `coherence_settings`
  - [ ] Create `CoherenceSettings` Pydantic model with all technique fields
  - [ ] Add validation for coherence settings in schema
  - [ ] Update `POST /api/generate` endpoint to accept and store coherence_settings
  - [ ] Ensure backward compatibility (coherence_settings optional, defaults applied if missing)
  - [ ] Unit test: Schema accepts valid coherence settings
  - [ ] Unit test: Schema rejects invalid coherence settings
  - [ ] Integration test: Generation endpoint stores coherence_settings correctly

- [ ] Task 5: Create Coherence Settings Service (AC: 3, 4)
  - [ ] Create `backend/app/services/coherence_settings.py`
  - [ ] Implement `get_default_settings()` function returning recommended defaults
  - [ ] Implement `validate_settings(settings: dict)` function checking dependencies
  - [ ] Implement `apply_defaults(settings: dict)` function filling missing values
  - [ ] Add dependency checking logic (IP-Adapter requires Enhanced Planning, etc.)
  - [ ] Log coherence settings usage for analytics
  - [ ] Unit test: Default settings are correct
  - [ ] Unit test: Validation catches dependency violations
  - [ ] Unit test: Defaults are applied correctly

- [ ] Task 6: Create Database Migration (AC: 3)
  - [ ] Create Alembic migration to add `coherence_settings` JSON column to `generations` table
  - [ ] Ensure column is nullable (backward compatibility)
  - [ ] Add database index if needed for querying
  - [ ] Test migration up and down
  - [ ] Verify existing generations remain unaffected

- [ ] Task 7: Add API Endpoint for Default Settings (AC: 2)
  - [ ] Create `GET /api/coherence/settings/defaults` endpoint
  - [ ] Return default coherence settings with metadata (recommended, cost impact, time impact)
  - [ ] Include descriptions for each technique
  - [ ] Frontend calls this endpoint to populate tooltips and descriptions
  - [ ] Unit test: Endpoint returns correct default settings
  - [ ] Integration test: Frontend can fetch and display default settings

- [ ] Task 8: Implement Settings Persistence (Optional) (AC: 3)
  - [ ] Add user preference storage for coherence settings (optional feature)
  - [ ] Store user's last used settings in localStorage or user profile
  - [ ] Load saved preferences when user returns to Dashboard
  - [ ] Allow user to reset to defaults
  - [ ] Unit test: Settings are saved to localStorage
  - [ ] Unit test: Settings are loaded on component mount

## Dev Notes

### Architecture Patterns and Constraints

- **Frontend Component Structure:** Follow existing Dashboard component patterns. Use React hooks for state management (useState, useEffect). Component should be self-contained and reusable.
- **State Management:** Coherence settings should be managed in Dashboard component state, not in global Zustand store (settings are per-generation, not global user state).
- **API Integration:** Extend existing `generationService` in `frontend/src/lib/generationService.ts` to include coherence_settings in request payload.
- **Backend Schema:** Use Pydantic models for request/response validation. Follow existing pattern in `backend/app/schemas/generation.py`.
- **Database:** Use JSON column type for coherence_settings (PostgreSQL JSONB or SQLite JSON). Ensure backward compatibility with existing generations.
- **Error Handling:** Follow existing error handling patterns in Dashboard (display errors using ErrorMessage component).

[Source: docs/architecture.md#Project-Structure]
[Source: docs/architecture.md#Implementation-Patterns]

### Project Structure Notes

**New Files to Create:**
- `frontend/src/components/coherence/CoherenceSettingsPanel.tsx` - Main settings panel component
- `frontend/src/components/coherence/index.ts` - Barrel export (optional)
- `backend/app/services/coherence_settings.py` - Backend settings service
- `backend/app/schemas/coherence.py` - Pydantic models for coherence settings (optional, can be in generation.py)

**Files to Modify:**
- `frontend/src/routes/Dashboard.tsx` - Add CoherenceSettingsPanel integration
- `frontend/src/lib/generationService.ts` - Add coherence_settings to generation request
- `backend/app/db/models/generation.py` - Add coherence_settings field to Generation model
- `backend/app/schemas/generation.py` - Add CoherenceSettings model and update GenerationCreate schema
- `backend/app/api/routes/generations.py` - Update POST /api/generate to accept coherence_settings
- Database migration file - Add coherence_settings column

**Component Location:**
- Follow existing component structure: `frontend/src/components/` for reusable components
- Create `coherence/` subdirectory for coherence-related components (future stories will add more)

[Source: docs/architecture.md#Project-Structure]

### Testing Standards

- **Unit Tests:** Test components in isolation using React Testing Library. Test state management, validation logic, and UI interactions.
- **Integration Tests:** Test full flow from Dashboard form submission through API call to database storage.
- **E2E Tests:** Test user can expand settings panel, toggle options, see validation messages, and submit generation with settings.
- **Backend Tests:** Use pytest for backend service and API endpoint tests. Test schema validation, default application, and dependency checking.

[Source: docs/architecture.md#Testing]

### Learnings from Previous Story

**From Epic 5 (Last Completed Epic):**
- User statistics update patterns established in `backend/app/services/cost_tracking.py` - follow similar service structure for coherence_settings.py
- Database transaction patterns for atomic updates - coherence settings should be stored atomically with generation record
- Frontend state management patterns in Dashboard.tsx - follow existing form state management approach

**From Epic 3 (Video Generation Pipeline):**
- Generation request/response patterns established in `generationService.ts` - extend this service for coherence settings
- Dashboard form submission flow - integrate coherence settings into existing generation flow
- Backend generation endpoint structure in `generations.py` - add coherence_settings parameter following existing pattern

**Key Reusable Components:**
- `Button` component from `frontend/src/components/ui/Button.tsx` - use for expand/collapse button
- `ErrorMessage` component from `frontend/src/components/ui/ErrorMessage.tsx` - use for validation errors
- Form validation patterns from Dashboard.tsx - reuse for settings validation

[Source: docs/sprint-artifacts/5-2-user-stats-update.md#Dev-Agent-Record]
[Source: frontend/src/routes/Dashboard.tsx]

### References

- [Source: docs/epics.md#Story-7.0] - Story acceptance criteria and technical notes
- [Source: docs/sprint-artifacts/tech-spec-epic-7.md#Services-and-Modules] - Coherence settings service design
- [Source: docs/sprint-artifacts/tech-spec-epic-7.md#Data-Models-and-Contracts] - Generation model extension with coherence_settings
- [Source: docs/sprint-artifacts/tech-spec-epic-7.md#APIs-and-Interfaces] - API endpoint specifications
- [Source: docs/PRD.md#20.2-Phase-3-Features] - Character consistency and quality optimization requirements
- [Source: docs/architecture.md#Project-Structure] - Frontend and backend structure patterns
- [Source: docs/architecture.md#Implementation-Patterns] - Naming conventions and error handling patterns
- [Source: frontend/src/routes/Dashboard.tsx] - Existing Dashboard component for integration reference
- [Source: backend/app/api/routes/generations.py] - Existing generation endpoint for extension reference

## Dev Agent Record

### Context Reference

- docs/sprint-artifacts/stories/7-0-coherence-settings-ui-panel.context.xml

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

## Change Log

- 2025-11-15: Story created (drafted)

