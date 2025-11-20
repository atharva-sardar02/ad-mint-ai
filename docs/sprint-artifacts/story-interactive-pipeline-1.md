# User Story 1.1: CLI Tools Organization

**Epic:** Interactive Video Generation Pipeline
**Story ID:** interactive-pipeline-1
**Status:** review
**Points:** 1
**Priority:** High (blocks other stories)

---

## User Story

**As a** developer
**I want** Epic 8-9 CLI tools organized in a separate `backend/cli_tools/` directory
**So that** they don't get confused with the main web application pipeline code and development tools are clearly separated from production code

---

## Acceptance Criteria

**AC #1: Directory Structure Created**
- GIVEN the Epic 8-9 CLI tools exist scattered in `backend/`
- WHEN I create the new `backend/cli_tools/` directory
- THEN all CLI tools are moved to this directory with proper organization

**AC #2: All CLI Tools Moved**
- GIVEN the following CLI tools from Epic 8-9:
  - `enhance_image_prompt.py`
  - `generate_images.py`
  - `enhance_video_prompt.py`
  - `generate_videos.py`
  - `feedback_loop.py`
- WHEN they are moved to `backend/cli_tools/`
- THEN the directory contains all 5 CLI tools
- AND no CLI tools remain in `backend/` root

**AC #3: CLI Tools Function Correctly**
- GIVEN each CLI tool in the new location
- WHEN I run `python cli_tools/{tool_name}.py --help`
- THEN the tool executes without import errors
- AND displays correct usage information

**AC #4: Documentation Updated**
- GIVEN the new CLI tools directory
- WHEN I create `backend/cli_tools/README.md`
- THEN it documents the purpose of each tool
- AND provides usage examples for each tool
- AND explains that these are development/testing tools, not production code

**AC #5: Import Paths Valid**
- GIVEN the CLI tools may import from `app/services/pipeline/`
- WHEN I check all import statements
- THEN all imports use correct paths (absolute or relative)
- AND tools can still access shared pipeline services

---

## Tasks/Subtasks

**Preparation:**
- [x] Review current locations of all Epic 8-9 CLI tools (AC: #1, #2)
- [x] Identify any dependencies or import paths that need updating (AC: #5)

**Directory Organization:**
- [x] Create `backend/cli_tools/` directory (AC: #1)
- [x] Move `enhance_image_prompt.py` to `cli_tools/` (AC: #2)
- [x] Move `generate_images.py` to `cli_tools/` (AC: #2)
- [x] Move `enhance_video_prompt.py` to `cli_tools/` (AC: #2)
- [x] Move `generate_videos.py` to `cli_tools/` (AC: #2)
- [x] Move `create_storyboard.py` to `cli_tools/` (AC: #2) - Note: `feedback_loop.py` does not exist in the codebase

**Import Path Updates:**
- [x] Update imports in CLI tools if needed (change relative to absolute) (AC: #5)
- [x] Test imports work correctly from new location (AC: #5)

**Documentation:**
- [x] Create `cli_tools/README.md` with tool descriptions (AC: #4)
- [x] Document usage examples for each tool (AC: #4)
- [x] Add note that these are development tools (AC: #4)

**Verification:**
- [x] Test each CLI tool execution: `python cli_tools/enhance_image_prompt.py --help` (AC: #3)
- [x] Verify all tools show correct help output (AC: #3)
- [x] Check no broken imports or missing dependencies (AC: #3, #5)

**Cleanup:**
- [x] Remove any leftover files in `backend/` root (AC: #2)
- [x] Update any project documentation that references CLI tool locations (AC: #4)

---

## Technical Summary

This story is pure housekeeping to improve code organization. Epic 8-9 created CLI tools for image and video feedback loops as development/testing utilities. These tools are currently scattered in the `backend/` directory, which can cause confusion with the main web application pipeline code.

**What We're Doing:**
- Moving all CLI tools to dedicated `backend/cli_tools/` directory
- Ensuring imports still work after the move
- Documenting the purpose and usage of each tool

**Why It Matters:**
- Clear separation between development tools and production code
- Easier onboarding for new developers (clear "these are dev tools" location)
- Prevents accidental inclusion of CLI tools in production deployments
- Sets up clean codebase structure for Stories 2-4 (web pipeline work)

**Files Involved:**
- `backend/enhance_image_prompt.py` → `backend/cli_tools/enhance_image_prompt.py`
- `backend/generate_images.py` → `backend/cli_tools/generate_images.py`
- `backend/enhance_video_prompt.py` → `backend/cli_tools/enhance_video_prompt.py`
- `backend/generate_videos.py` → `backend/cli_tools/generate_videos.py`
- `backend/feedback_loop.py` → `backend/cli_tools/feedback_loop.py`
- `backend/cli_tools/README.md` (NEW)

---

## Project Structure Notes

**files_to_modify:**
```
backend/cli_tools/                           # CREATE directory
backend/cli_tools/enhance_image_prompt.py    # MOVE
backend/cli_tools/generate_images.py         # MOVE
backend/cli_tools/enhance_video_prompt.py    # MOVE
backend/cli_tools/generate_videos.py         # MOVE
backend/cli_tools/feedback_loop.py           # MOVE
backend/cli_tools/README.md                  # CREATE
```

**test_locations:**
- No new tests required (CLI tools already have tests or are manual testing tools)
- Verification is manual: run each tool with `--help` flag

**story_points:** 1

**dependencies:**
- None (this is foundational cleanup work)

**estimated_effort:** ~1 day (4-6 hours)

---

## Key Code References

**Existing CLI Tools to Move:**
- `backend/enhance_image_prompt.py` - Image prompt enhancement CLI (Epic 8)
- `backend/generate_images.py` - Image generation CLI (Epic 8)
- `backend/create_storyboard.py` - Storyboard creation CLI (Epic 8, if exists)
- `backend/enhance_video_prompt.py` - Video prompt enhancement CLI (Epic 9)
- `backend/generate_videos.py` - Video generation CLI (Epic 9)
- `backend/feedback_loop.py` - Integrated feedback loop CLI (Epic 9)

**Pipeline Services They Import:**
- `app/services/pipeline/image_prompt_enhancement.py`
- `app/services/pipeline/image_generation.py`
- `app/services/pipeline/video_prompt_enhancement.py`
- `app/services/pipeline/video_generation_cli.py`
- `app/services/pipeline/storyboard_service.py`

**Import Pattern After Move:**
```python
# CLI tools in cli_tools/ can import from app/ using:
import sys
from pathlib import Path
# Add parent directory to path if needed
sys.path.append(str(Path(__file__).parent.parent))

from app.services.pipeline.image_generation import generate_images
```

---

## Context References

**Primary Reference:**
- Technical Specification: `docs/tech-spec.md`
  - See "Source Tree Changes" section for detailed file organization
  - See "CLI Tools (Epic 8-9)" in Existing Codebase Structure

**Related Documentation:**
- Epic 8 Tech Spec: `docs/sprint-artifacts/tech-spec-epic-8.md` (CLI MVP - Image Generation)
- Epic 9 Tech Spec: `docs/sprint-artifacts/tech-spec-epic-9.md` (CLI MVP - Video Generation)

---

## Dev Agent Record

**Agent Model Used:**
- claude-sonnet-4-5-20250929

**Context Reference:**
- docs/sprint-artifacts/story-interactive-pipeline-1.context.xml

**Debug Log:**
- Created backend/cli_tools/ directory successfully
- Moved 5 CLI tools from backend/ to backend/cli_tools/
- Updated sys.path imports from parent to parent.parent in all CLI tools
- Created comprehensive README.md documenting all tools and usage patterns
- Verified all tools execute successfully with --help flag

**Completion Notes:**
- Successfully reorganized all Epic 8-9 CLI tools into dedicated backend/cli_tools/ directory
- All 5 CLI tools moved: enhance_image_prompt.py, generate_images.py, enhance_video_prompt.py, generate_videos.py, create_storyboard.py
- Note: feedback_loop.py mentioned in story does not exist in the codebase (likely renamed or combined with other tools)
- Updated all import paths from `sys.path.insert(0, str(Path(__file__).parent))` to `sys.path.insert(0, str(Path(__file__).parent.parent))` to maintain correct module access
- Created comprehensive README.md (307 lines) with:
  - Purpose and usage for each CLI tool
  - Complete command-line examples for common workflows
  - Environment requirements and troubleshooting guide
  - Clear warnings that these are development tools, not production code
- Verified all CLI tools execute without import errors via --help flag testing
- No leftover CLI tool files remain in backend/ root directory
- All acceptance criteria met successfully

**Files Modified:**
- backend/cli_tools/ (CREATED)
- backend/cli_tools/enhance_image_prompt.py (MOVED from backend/, updated imports)
- backend/cli_tools/generate_images.py (MOVED from backend/, updated imports)
- backend/cli_tools/enhance_video_prompt.py (MOVED from backend/, updated imports)
- backend/cli_tools/generate_videos.py (MOVED from backend/, updated imports)
- backend/cli_tools/create_storyboard.py (MOVED from backend/, updated imports)
- backend/cli_tools/README.md (CREATED)
- docs/sprint-artifacts/sprint-status.yaml (updated status: ready-for-dev → in-progress)
- docs/sprint-artifacts/story-interactive-pipeline-1.md (updated tasks, completion notes)

**Test Results:**
- ✅ All CLI tools execute successfully with --help flag
- ✅ No import errors detected
- ✅ All tools display correct usage information
- ✅ No leftover files in backend/ root
- ✅ Directory structure matches acceptance criteria

---

## Review Notes

**Code Review:**
- TBD

**QA Notes:**
- TBD

**Deployment Notes:**
- TBD
