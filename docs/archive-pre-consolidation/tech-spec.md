# ad-mint-ai - Technical Specification

**Author:** BMad
**Date:** 2025-11-19
**Project Level:** Intermediate
**Change Type:** Feature Enhancement
**Development Context:** Brownfield - Existing React/FastAPI Application

---

## Context

### Available Documents

**Loaded Research Documents:**
- Epic7_Research_Analysis.md - Analysis of video quality optimization techniques
- Multi_Scene_Video_Ad_Generation_Research_Report.md - Research on multi-scene coherence

**Existing Project Artifacts:**
- PRD.md - Complete product requirements
- architecture.md - System architecture
- bmm-architecture-2025-11-14.md - Detailed architectural decisions
- epics.md - Epic breakdown with stories
- Multiple tech-specs for Epics 1-9

**Project Status:**
- Active development with Epics 1-5 completed
- Epic 6 (Video Editing) in progress
- Epic 7 (Quality Optimization) in progress
- Epic 8-9 (CLI Feedback Tools) implemented

### Project Stack

**Backend:**
- Framework: FastAPI >= 0.104.0
- Runtime: Python 3.x
- Database: PostgreSQL with SQLAlchemy 2.0+
- Authentication: PyJWT 2.8+, bcrypt 4.0+
- AI/ML: OpenAI 1.0+, Replicate 0.25+
- Video Processing: moviepy 1.0.3+, opencv-python 4.8+
- Image Processing: Pillow 10.0+, transformers 4.30+, torch 2.0+
- Testing: pytest 7.4+, pytest-asyncio 0.21+
- Storage: boto3 1.34+ (AWS S3)

**Frontend:**
- Framework: React 19.2.0
- Language: TypeScript 5.9.3
- Build Tool: Vite 5.4.11
- Styling: Tailwind CSS 4.1.17
- State Management: Zustand 5.0.8
- Routing: react-router-dom 7.9.6
- HTTP Client: axios 1.13.2
- Testing: vitest 1.6.0, @testing-library/react 16.1.0

### Existing Codebase Structure

**Backend Structure (`backend/`):**
```
backend/
├── app/
│   ├── api/                    # API endpoints
│   ├── core/                   # Core config and dependencies
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic schemas
│   └── services/
│       └── pipeline/           # Video generation pipeline (52 service files)
│           ├── multi_stage_orchestrator.py    # Main pipeline orchestrator
│           ├── story_generator.py             # Story generation
│           ├── scene_divider.py               # Scene planning
│           ├── storyboard_generator.py        # Storyboard creation
│           ├── image_generation.py            # Image generation
│           ├── image_prompt_enhancement.py    # Image prompt enhancement
│           ├── video_generation.py            # Video generation
│           ├── video_prompt_enhancement.py    # Video prompt enhancement
│           ├── quality_control.py             # VBench quality scoring
│           └── ... (43 more pipeline services)
├── tests/                      # Test suite
└── requirements.txt            # Python dependencies
```

**Frontend Structure (`frontend/`):**
```
frontend/
├── src/
│   ├── components/             # React components
│   ├── pages/                  # Page components
│   ├── hooks/                  # Custom React hooks
│   ├── services/               # API services
│   ├── stores/                 # Zustand stores
│   ├── types/                  # TypeScript types
│   └── utils/                  # Utility functions
├── package.json                # npm dependencies
└── vite.config.ts              # Vite configuration
```

**Existing Pipeline Flow (4-Stage):**
1. **Stage 0:** Template Selection (AI-powered framework selection)
2. **Stage 1:** Story Generation (narrative & script creation)
3. **Stage 2:** Scene Division (timing & scene breakdown)
4. **Stage 3:** Visual Specification (storyboard with image prompts)
5. **Stage 4:** Generation (image → video generation)

**CLI Tools (Epic 8-9):**
- Located in `backend/` (currently mixed with main codebase)
- `enhance_image_prompt.py` - Image prompt enhancement CLI
- `generate_images.py` - Image generation CLI
- `enhance_video_prompt.py` - Video prompt enhancement CLI
- `generate_videos.py` - Video generation CLI
- `feedback_loop.py` - Integrated feedback loop CLI

---

## The Change

### Problem Statement

**Current Pain Point:**
The existing video generation pipeline in the web application is fully automated with no user interaction between stages. Once a user submits a prompt and clicks "Generate Video," the entire pipeline runs end-to-end without any opportunity for the user to review or provide feedback on intermediate outputs (story, reference images, storyboard images). This "black box" approach leads to:

1. **Wasted API costs:** If the AI-generated story doesn't match the user's vision, they discover this only after spending credits on full video generation
2. **User frustration:** No control over the creative direction between pipeline stages
3. **Suboptimal results:** No opportunity to refine prompts or regenerate individual stages based on intermediate outputs
4. **Poor UX:** Users can't leverage their domain expertise to guide the AI at each stage

**Business Impact:**
- Reduced user satisfaction due to lack of control
- Higher API costs from regenerating entire videos instead of just problematic stages
- Competitive disadvantage vs. tools that offer human-in-the-loop workflows (e.g., Runway, Midjourney's iteration features)

**User Need:**
Professional content creators expect to have control at each stage of the creative pipeline, similar to how they work with other AI creative tools. They want to:
- Review the AI-generated story and refine it through conversation before committing to image generation
- See reference images and either approve them or request modifications before storyboard generation
- Review storyboard images and make targeted edits (inpainting, object replacement) before video generation

### Proposed Solution

Implement an **interactive, human-in-the-loop video generation pipeline** for the web application that pauses at key stages, presents intermediate results to the user, and allows conversational feedback and targeted regeneration before proceeding.

**Key Features:**

1. **Interactive Story Generation** (Stage 1)
   - Generate story → Display in UI → Provide chat interface
   - User can discuss changes with LLM ("make it more humorous", "focus on product benefits")
   - Regenerate story based on feedback
   - User approves story before moving to next stage

2. **Interactive Reference Image Generation** (Stage 2)
   - Generate reference images → Display in UI → Provide chat interface
   - User can request regenerations ("make the background brighter", "change the character's outfit")
   - Basic image editing (future: inpainting for object selection/replacement)
   - User approves reference images before moving to storyboard

3. **Interactive Storyboard Generation** (Stage 3)
   - Generate storyboard images → Display in UI → Provide chat interface
   - User can request regenerations for specific frames
   - Advanced image editing (inpainting, object selection/replacement)
   - User approves storyboard before final video generation

4. **CLI Tools Organization** (Housekeeping)
   - Move Epic 8-9 CLI tools to separate `backend/cli_tools/` directory
   - Keep them separate from main pipeline code to avoid confusion
   - Maintain as developer tools for testing/experimentation

**Technical Approach:**
- Extend existing `multi_stage_orchestrator.py` to support "pause points"
- Add WebSocket support for real-time chat between user and LLM
- Create React components for stage review interfaces
- Integrate existing prompt enhancement services for conversational refinement
- Add image editing capabilities using inpainting models (SDXL-inpaint, ControlNet)

### Scope

**In Scope:**

✅ **Story 1: CLI Tools Organization**
- Move Epic 8-9 CLI tools to `backend/cli_tools/` directory
- Update import paths and documentation
- Verify CLI tools still work independently

✅ **Story 2: Interactive Story Generation**
- Backend: Extend orchestrator with pause/resume for Stage 1
- Backend: Add WebSocket endpoint for story chat
- Backend: Integrate `story_generator.py` with conversational refinement
- Frontend: Story review UI component
- Frontend: Chat interface for story feedback
- Frontend: Story approval/regeneration controls

✅ **Story 3: Interactive Image/Storyboard Feedback**
- Backend: Extend orchestrator with pause/resume for Stages 2-3
- Backend: Add WebSocket endpoints for image chat
- Backend: Integrate image regeneration based on feedback
- Frontend: Image gallery review UI
- Frontend: Chat interface for image feedback
- Frontend: Image approval/regeneration controls

✅ **Story 4: Advanced Image Editing**
- Backend: Integrate inpainting service (SDXL-inpaint or ControlNet)
- Backend: Add object selection/masking API
- Frontend: Image editor UI with selection tools
- Frontend: Inpainting controls ("replace this character", "change background")
- Frontend: Real-time preview of edits

**Out of Scope:**

❌ Video editing in the interactive pipeline (covered by Epic 6)
❌ Automated quality scoring at each stage (Epic 7 functionality)
❌ Multi-user collaboration on same generation
❌ Saving draft states mid-pipeline (could be future enhancement)
❌ Advanced video inpainting (too computationally expensive currently)
❌ Integration with CLI tools (they remain separate developer tools)

---

## Implementation Details

### Source Tree Changes

**Backend Changes:**

1. **backend/cli_tools/** (NEW DIRECTORY)
   - CREATE - Move all Epic 8-9 CLI scripts here
   - `cli_tools/enhance_image_prompt.py` - MOVE from backend/
   - `cli_tools/generate_images.py` - MOVE from backend/
   - `cli_tools/enhance_video_prompt.py` - MOVE from backend/
   - `cli_tools/generate_videos.py` - MOVE from backend/
   - `cli_tools/feedback_loop.py` - MOVE from backend/
   - `cli_tools/README.md` - CREATE - Document CLI tools usage

2. **backend/app/services/pipeline/**
   - `multi_stage_orchestrator.py` - MODIFY - Add pause/resume functionality
   - `interactive_pipeline.py` - CREATE - New interactive pipeline orchestrator
   - `conversation_handler.py` - CREATE - LLM conversation service for feedback
   - `inpainting_service.py` - CREATE - Image inpainting/editing service

3. **backend/app/api/routes/**
   - `interactive_generation.py` - CREATE - API endpoints for interactive pipeline
   - `websocket.py` - CREATE - WebSocket endpoints for real-time chat

4. **backend/app/schemas/**
   - `interactive_schemas.py` - CREATE - Pydantic schemas for interactive pipeline

**Frontend Changes:**

5. **frontend/src/components/generation/**
   - `InteractivePipeline.tsx` - CREATE - Main interactive pipeline component
   - `StoryReview.tsx` - CREATE - Story review interface
   - `ImageReview.tsx` - CREATE - Image review interface
   - `ChatInterface.tsx` - CREATE - Reusable chat component
   - `ImageEditor.tsx` - CREATE - Image editing interface with selection tools

6. **frontend/src/hooks/**
   - `useWebSocket.ts` - CREATE - WebSocket hook for chat
   - `useInteractivePipeline.ts` - CREATE - Pipeline state management hook

7. **frontend/src/services/**
   - `interactive-api.ts` - CREATE - API client for interactive pipeline
   - `websocket-service.ts` - CREATE - WebSocket service

8. **frontend/src/stores/**
   - `pipelineStore.ts` - CREATE - Zustand store for pipeline state

9. **frontend/src/types/**
   - `pipeline.ts` - CREATE - TypeScript types for pipeline

**Test Files:**

10. **backend/tests/services/**
    - `test_interactive_pipeline.py` - CREATE - Interactive pipeline tests
    - `test_conversation_handler.py` - CREATE - Conversation handler tests
    - `test_inpainting_service.py` - CREATE - Inpainting service tests

11. **frontend/src/components/generation/__tests__/**
    - `InteractivePipeline.test.tsx` - CREATE - Component tests
    - `ChatInterface.test.tsx` - CREATE - Chat component tests

### Technical Approach

**1. Backend: Interactive Pipeline Orchestration**

Extend the existing `multi_stage_orchestrator.py` pattern with pause/resume functionality:

```python
# New interactive_pipeline.py
class InteractivePipelineOrchestrator:
    """
    Orchestrates interactive pipeline with pause points.
    Extends multi_stage_orchestrator with user feedback loops.
    """

    async def run_stage_with_pause(
        self,
        stage_name: str,
        generation_fn: Callable,
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Run a stage, save output to session state, notify frontend,
        and wait for user approval before proceeding.
        """
        # 1. Run generation
        result = await generation_fn()

        # 2. Save to session state (Redis/DB)
        await self.save_stage_output(session_id, stage_name, result)

        # 3. Notify frontend via WebSocket
        await self.notify_stage_complete(user_id, stage_name, result)

        # 4. Wait for approval or feedback
        feedback = await self.wait_for_user_action(session_id, stage_name)

        # 5. Process feedback if any
        if feedback.action == "regenerate":
            return await self.handle_regeneration(stage_name, feedback)

        return result
```

**2. Backend: Conversational Refinement**

Reuse existing prompt enhancement patterns from Epic 8-9 but adapt for real-time chat:

```python
# conversation_handler.py
class ConversationHandler:
    """
    Handle conversational feedback using LLM.
    Adapts existing prompt_enhancement patterns for chat.
    """

    async def process_story_feedback(
        self,
        original_story: str,
        user_feedback: str,
        conversation_history: List[Dict]
    ) -> str:
        """
        Process user feedback and generate refined story.
        Uses existing story_generator.py with conversational prompts.
        """
        # Use GPT-4 to understand feedback and refine story
        # Pattern similar to image_prompt_enhancement.py
```

**3. Backend: WebSocket Integration**

Use FastAPI WebSocket support for real-time chat:

```python
# websocket.py
@router.websocket("/ws/pipeline/{session_id}")
async def pipeline_chat_ws(
    websocket: WebSocket,
    session_id: str,
    current_user: User = Depends(get_current_user_ws)
):
    """
    WebSocket endpoint for real-time pipeline chat.
    Handles: user messages, LLM responses, stage notifications.
    """
    await manager.connect(websocket, session_id)

    while True:
        # Receive user message
        data = await websocket.receive_json()

        # Process through conversation handler
        response = await conversation_handler.process(data)

        # Send response
        await websocket.send_json(response)
```

**4. Frontend: Interactive Pipeline Component**

Create staged UI that guides users through each stage:

```typescript
// InteractivePipeline.tsx
export function InteractivePipeline() {
  const [currentStage, setCurrentStage] = useState<PipelineStage>('story');
  const [stageData, setStageData] = useState<StageData | null>(null);
  const { connected, sendMessage } = useWebSocket();

  // Stages: story → reference_image → storyboard → video

  return (
    <div className="pipeline-container">
      <StageProgress current={currentStage} />

      {currentStage === 'story' && (
        <StoryReview
          story={stageData.story}
          onApprove={() => proceedToNextStage()}
          onFeedback={(msg) => sendMessage(msg)}
        />
      )}

      {currentStage === 'reference_image' && (
        <ImageReview
          images={stageData.images}
          onApprove={() => proceedToNextStage()}
          onEdit={(image) => openImageEditor(image)}
        />
      )}

      {/* Similar for storyboard and final stages */}
    </div>
  );
}
```

**5. Frontend: Chat Interface**

Reusable chat component for all stages:

```typescript
// ChatInterface.tsx
export function ChatInterface({
  onMessage,
  messages,
  isLoading
}: ChatInterfaceProps) {
  return (
    <div className="chat-container">
      <MessageList messages={messages} />
      <ChatInput
        onSend={onMessage}
        disabled={isLoading}
        placeholder="Describe what you'd like to change..."
      />
    </div>
  );
}
```

**6. Advanced Image Editing (Inpainting)**

Integrate inpainting models for object-level editing:

```python
# inpainting_service.py
class InpaintingService:
    """
    Image inpainting using SDXL-inpaint or ControlNet.
    Allows user to select regions and replace with new content.
    """

    async def inpaint(
        self,
        image_path: str,
        mask: np.ndarray,  # Binary mask of selected region
        prompt: str,       # Description of replacement
        negative_prompt: Optional[str] = None
    ) -> str:
        """
        Inpaint selected region with new content.
        Uses Replicate SDXL-inpaint model.
        """
        # Call Replicate API with image + mask + prompt
        # Return path to edited image
```

### Existing Patterns to Follow

**Backend Patterns (from existing codebase):**

1. **Service Pattern:**
   - All pipeline services are classes in `app/services/pipeline/`
   - Use async/await for all I/O operations
   - Follow naming: `{feature}_service.py` or `{feature}_generator.py`
   - Example: `story_generator.py`, `image_generation.py`

2. **Error Handling:**
   - Use custom exceptions from `app/core/exceptions.py`
   - Log errors with `logging.getLogger(__name__)`
   - Return structured error responses in API routes

3. **API Routes:**
   - Routes in `app/api/routes/`
   - Use FastAPI dependency injection for auth
   - Follow RESTful patterns with Pydantic schemas
   - Example: `@router.post("/videos/generate")`

4. **Testing:**
   - pytest with async support (`pytest-asyncio`)
   - Mock external API calls (OpenAI, Replicate)
   - Test files mirror source structure: `tests/services/test_{service}.py`

**Frontend Patterns (detected from package.json and common React patterns):**

1. **Component Structure:**
   - Functional components with TypeScript
   - Use hooks for state management
   - Prop types defined with TypeScript interfaces
   - File naming: PascalCase for components (`StoryReview.tsx`)

2. **State Management:**
   - Zustand for global state
   - React hooks (useState, useEffect) for local state
   - Custom hooks for reusable logic (`use{Feature}.ts`)

3. **Styling:**
   - Tailwind CSS utility classes
   - Follow Tailwind conventions for responsive design
   - Component-scoped styles when needed

4. **Testing:**
   - vitest for unit tests
   - @testing-library/react for component testing
   - Test files: `{Component}.test.tsx` in `__tests__` folders

5. **API Calls:**
   - axios for HTTP requests
   - Centralized API client in `services/` folder
   - Error handling with try/catch and user feedback

### Integration Points

**Internal Backend Integrations:**

1. **Existing Pipeline Services** (`app/services/pipeline/`)
   - `multi_stage_orchestrator.py` - Extend with pause points
   - `story_generator.py` - Use for story generation with feedback
   - `image_generation.py` - Use for image generation
   - `storyboard_generator.py` - Use for storyboard generation
   - `image_prompt_enhancement.py` - Use for conversational refinement
   - `quality_control.py` - Optional quality scoring at each stage

2. **Database Models** (`app/models/`)
   - User model for authentication
   - Video model for tracking generation state
   - New: PipelineSession model for storing intermediate state

3. **Authentication** (`app/core/security.py`)
   - JWT token validation for WebSocket connections
   - User authorization for pipeline access

**External API Integrations:**

1. **OpenAI API**
   - GPT-4 for conversational feedback processing
   - Existing configuration in `app/core/config.py`
   - Use existing OpenAI client setup

2. **Replicate API**
   - SDXL for image generation
   - SDXL-inpaint for image editing
   - Video models (Kling, Wan, PixVerse)
   - Existing Replicate client in codebase

**Frontend-Backend Communication:**

1. **REST API**
   - Start pipeline: `POST /api/v1/interactive/start`
   - Get stage status: `GET /api/v1/interactive/{session_id}/status`
   - Approve stage: `POST /api/v1/interactive/{session_id}/approve`
   - Request regeneration: `POST /api/v1/interactive/{session_id}/regenerate`

2. **WebSocket**
   - Real-time chat: `ws://backend/ws/pipeline/{session_id}`
   - Stage completion notifications
   - Progress updates

3. **State Management**
   - Session state stored in Redis or PostgreSQL
   - Frontend maintains local UI state with Zustand
   - Sync state via WebSocket messages

---

## Development Context

### Relevant Existing Code

**Key Files to Review:**

1. **`backend/app/services/pipeline/multi_stage_orchestrator.py`** (Lines 1-200)
   - Current 4-stage pipeline orchestration
   - Pattern for stage execution and result passing
   - Use this as template for interactive orchestrator

2. **`backend/app/services/pipeline/story_generator.py`**
   - Story generation logic with template-based approach
   - LLM prompt patterns for narrative creation
   - Adapt for conversational refinement

3. **`backend/app/services/pipeline/image_prompt_enhancement.py`**
   - Two-agent feedback loop pattern (Cinematographer + Prompt Engineer)
   - Iterative refinement with scoring
   - Reuse this pattern for conversational feedback

4. **`backend/app/services/pipeline/image_generation.py`**
   - Replicate API integration for SDXL
   - Image generation and quality scoring
   - Extend for inpainting support

5. **`backend/app/api/routes/videos.py`** (if exists)
   - Current video generation API patterns
   - Authentication and authorization
   - Response schemas

### Dependencies

**Framework/Libraries:**

**Backend:**
- FastAPI 0.104.0 (web framework)
- uvicorn 0.24.0 (ASGI server)
- SQLAlchemy 2.0.0 (ORM)
- Pydantic 2.0.0 (data validation)
- PyJWT 2.8.0 (authentication)
- openai 1.0.0 (LLM API)
- replicate 0.25.0 (generative AI API)
- moviepy 1.0.3 (video processing)
- opencv-python 4.8.0 (image processing)
- Pillow 10.0.0 (image manipulation)
- boto3 1.34.0 (AWS S3)
- pytest 7.4.0 (testing)
- redis 4.6.0 (NEW - for session state caching)
- websockets 11.0.0 (NEW - WebSocket support)

**Frontend:**
- React 19.2.0 (UI framework)
- TypeScript 5.9.3 (type safety)
- Vite 5.4.11 (build tool)
- Tailwind CSS 4.1.17 (styling)
- Zustand 5.0.8 (state management)
- react-router-dom 7.9.6 (routing)
- axios 1.13.2 (HTTP client)
- vitest 1.6.0 (testing)
- @testing-library/react 16.1.0 (component testing)
- react-konva 18.2.0 (NEW - for image editing canvas)
- socket.io-client 4.7.0 (NEW - WebSocket client, alternative to native WebSocket)

**Internal Modules:**

- `app.services.pipeline.*` - All existing pipeline services
- `app.models.*` - Database models (User, Video)
- `app.schemas.*` - Pydantic schemas
- `app.core.config` - Configuration and settings
- `app.core.security` - Authentication utilities
- `app.core.exceptions` - Custom exceptions

### Configuration Changes

**Backend:**

1. **`.env`** - Add new environment variables:
   ```
   # WebSocket configuration
   WEBSOCKET_HEARTBEAT_INTERVAL=30
   WEBSOCKET_TIMEOUT=300

   # Redis for session state (if using Redis)
   REDIS_URL=redis://localhost:6379
   REDIS_SESSION_TTL=3600

   # Inpainting model
   REPLICATE_INPAINT_MODEL=stability-ai/sdxl-inpaint:1.0
   ```

2. **`backend/app/core/config.py`** - Add new settings:
   ```python
   class Settings:
       # Existing settings...

       # WebSocket settings
       websocket_heartbeat_interval: int = 30
       websocket_timeout: int = 300

       # Redis settings
       redis_url: str = "redis://localhost:6379"
       redis_session_ttl: int = 3600

       # Inpainting
       replicate_inpaint_model: str = "stability-ai/sdxl-inpaint:1.0"
   ```

3. **`backend/requirements.txt`** - Add new dependencies:
   ```
   redis>=4.6.0
   websockets>=11.0.0
   ```

**Frontend:**

4. **`frontend/package.json`** - Add new dependencies:
   ```json
   {
     "dependencies": {
       "react-konva": "^18.2.0",
       "socket.io-client": "^4.7.0"
     }
   }
   ```

5. **`frontend/.env`** - Add WebSocket URL:
   ```
   VITE_WS_URL=ws://localhost:8000
   ```

6. **`frontend/vite.config.ts`** - Configure WebSocket proxy for development:
   ```typescript
   export default defineConfig({
     server: {
       proxy: {
         '/ws': {
           target: 'ws://localhost:8000',
           ws: true
         }
       }
     }
   })
   ```

**No database migrations needed** - Will add PipelineSession model but this is new functionality.

### Existing Conventions (Brownfield)

**Code Style:**

**Backend (Python):**
- **PEP 8** compliance
- **Indentation:** 4 spaces
- **Line length:** 88 characters (Black formatter standard)
- **Quotes:** Double quotes for strings
- **Imports:** Absolute imports, grouped (stdlib, third-party, local)
- **Type hints:** Use type hints for all function signatures
- **Docstrings:** Google-style docstrings for all public functions/classes
- **Naming:**
  - snake_case for functions, variables
  - PascalCase for classes
  - UPPER_CASE for constants

**Frontend (TypeScript/React):**
- **ESLint + Prettier** for formatting
- **Indentation:** 2 spaces
- **Quotes:** Single quotes for strings
- **Semicolons:** Yes (enforced by ESLint)
- **Naming:**
  - PascalCase for components, types, interfaces
  - camelCase for functions, variables
  - UPPER_SNAKE_CASE for constants
- **Imports:** Absolute imports preferred (using @ alias)
- **Component structure:**
  - Props interface before component
  - Functional components with TypeScript
  - Export at bottom of file

**Testing Conventions:**

**Backend:**
- **Framework:** pytest
- **File naming:** `test_{module}.py`
- **Test naming:** `test_{function}_{scenario}`
- **Location:** Mirror source structure in `tests/`
- **Fixtures:** Use pytest fixtures for common setup
- **Mocking:** Use `unittest.mock` or `pytest-mock`
- **Async tests:** Use `@pytest.mark.asyncio` decorator

**Frontend:**
- **Framework:** vitest + @testing-library/react
- **File naming:** `{Component}.test.tsx`
- **Location:** `__tests__` folder next to component
- **Test structure:** Describe blocks for grouping
- **Assertions:** Use vitest `expect` assertions
- **Rendering:** Use `render` from @testing-library/react
- **User interactions:** Use `fireEvent` or `userEvent`

### Test Framework & Standards

**Backend Testing:**
- **Framework:** pytest 7.4+ with pytest-asyncio 0.21+
- **Coverage target:** 80% minimum for new code
- **Test organization:**
  ```
  tests/
  ├── services/
  │   ├── test_interactive_pipeline.py
  │   ├── test_conversation_handler.py
  │   └── test_inpainting_service.py
  ├── api/
  │   └── test_interactive_generation.py
  └── conftest.py  # Shared fixtures
  ```
- **Mocking:** Mock external APIs (OpenAI, Replicate) using `pytest-mock`
- **Async testing:** All async functions tested with `@pytest.mark.asyncio`

**Frontend Testing:**
- **Framework:** vitest 1.6+ with @testing-library/react 16.1+
- **Coverage target:** 70% minimum for new components
- **Test organization:**
  ```
  src/components/generation/
  ├── InteractivePipeline.tsx
  ├── StoryReview.tsx
  └── __tests__/
      ├── InteractivePipeline.test.tsx
      └── StoryReview.test.tsx
  ```
- **Component testing:** Test user interactions, not implementation
- **WebSocket testing:** Mock WebSocket connections
- **State testing:** Test Zustand store logic in isolation

---

## Implementation Stack

**Runtime:**
- Backend: Python 3.11+ (current project version)
- Frontend: Node.js 20.x (for Vite compatibility)

**Backend Stack:**
- Framework: FastAPI 0.104.0
- ASGI Server: uvicorn[standard] 0.24.0
- Database: PostgreSQL 14+ with SQLAlchemy 2.0.0
- ORM: SQLAlchemy 2.0.0
- Validation: Pydantic 2.0.0
- Authentication: PyJWT 2.8.0, bcrypt 4.0.0
- Session Storage: Redis 4.6.0 (NEW)
- WebSocket: websockets 11.0.0 (NEW) or FastAPI built-in WebSocket
- AI/LLM: openai 1.0.0 (GPT-4)
- Generative AI: replicate 0.25.0 (SDXL, SDXL-inpaint, video models)
- Video Processing: moviepy 1.0.3
- Image Processing: opencv-python 4.8.0, Pillow 10.0.0
- ML: transformers 4.30.0, torch 2.0.0
- Cloud Storage: boto3 1.34.0 (AWS S3)
- Testing: pytest 7.4.0, pytest-asyncio 0.21.0, httpx 0.24.0

**Frontend Stack:**
- Framework: React 19.2.0
- Language: TypeScript 5.9.3
- Build Tool: Vite 5.4.11
- CSS Framework: Tailwind CSS 4.1.17
- State Management: Zustand 5.0.8
- Routing: react-router-dom 7.9.6
- HTTP Client: axios 1.13.2
- WebSocket: socket.io-client 4.7.0 (NEW) or native WebSocket API
- Canvas/Drawing: react-konva 18.2.0 (NEW - for image editing)
- Testing: vitest 1.6.0, @testing-library/react 16.1.0, jsdom 25.0.1
- Linting: ESLint 9.39.1 with TypeScript support
- Formatting: Prettier 3.6.2

**Development Tools:**
- Package Manager (Backend): pip
- Package Manager (Frontend): npm
- Version Control: git
- Code Formatting (Backend): black (implicit from conventions)
- Code Formatting (Frontend): prettier 3.6.2
- Linting (Backend): pylint (implicit from conventions)
- Linting (Frontend): eslint 9.39.1

---

## Technical Details

### 1. Interactive Pipeline State Management

**Session State Schema:**
```python
class PipelineSession:
    session_id: str
    user_id: str
    status: Literal["story", "reference_image", "storyboard", "video", "complete"]
    current_stage: str
    outputs: Dict[str, Any]  # {stage_name: output_data}
    conversation_history: List[Dict]  # Chat messages
    created_at: datetime
    updated_at: datetime
```

**State Storage Options:**
- **Option 1 (Recommended):** Redis for fast in-memory session storage with TTL
- **Option 2:** PostgreSQL with JSON column for session data
- **Rationale:** Redis preferred for real-time state with automatic expiration

**State Transitions:**
```
Start → Story (generate) → Story (review) → Reference Image (generate)
  → Reference Image (review) → Storyboard (generate) → Storyboard (review)
  → Video (generate) → Complete
```

**Pause Points:**
- After story generation (wait for approval)
- After reference image generation (wait for approval/editing)
- After storyboard generation (wait for approval/editing)

### 2. WebSocket Message Protocol

**Client → Server Messages:**
```typescript
// Start new pipeline
{
  type: "start_pipeline",
  prompt: string,
  target_duration: number
}

// Send feedback
{
  type: "feedback",
  stage: "story" | "reference_image" | "storyboard",
  message: string
}

// Approve stage
{
  type: "approve_stage",
  stage: string
}

// Request regeneration
{
  type: "regenerate",
  stage: string,
  reason: string
}
```

**Server → Client Messages:**
```typescript
// Stage complete
{
  type: "stage_complete",
  stage: string,
  data: any  // Stage output
}

// LLM response
{
  type: "llm_response",
  message: string
}

// Regeneration in progress
{
  type: "regenerating",
  stage: string,
  progress: number
}

// Error
{
  type: "error",
  error: string
}
```

### 3. Conversational Refinement Algorithm

**Story Feedback Processing:**
```python
async def refine_story_with_feedback(
    original_story: str,
    user_feedback: str,
    conversation_history: List[Dict]
) -> str:
    """
    Refine story based on conversational feedback.

    Algorithm:
    1. Analyze user feedback to extract intent
    2. Identify specific story elements to modify
    3. Generate refined story preserving approved elements
    4. Validate against original prompt requirements
    """

    # Build conversation context
    context = build_context(original_story, conversation_history)

    # Use GPT-4 to understand feedback
    intent = await analyze_feedback_intent(user_feedback, context)

    # Generate refined story
    refined_story = await generate_story_variant(
        original_story=original_story,
        modifications=intent.modifications,
        preserve=intent.elements_to_preserve
    )

    return refined_story
```

**Image Feedback Processing:**
- Similar pattern but focuses on visual elements
- Translates conversational feedback into image generation parameters
- Example: "make it brighter" → increase brightness parameter + regenerate

### 4. Image Inpainting Workflow

**User Flow:**
1. User selects region on image using brush/selection tool
2. Frontend creates binary mask (selected = 1, unselected = 0)
3. User provides text prompt: "replace with a red sports car"
4. Backend sends image + mask + prompt to SDXL-inpaint
5. Return edited image, display in UI

**Technical Implementation:**
```python
async def inpaint_image(
    image_path: str,
    mask: np.ndarray,  # Binary mask (0/1)
    prompt: str,
    negative_prompt: str = "blurry, low quality"
) -> str:
    """
    Inpaint selected region using SDXL-inpaint.

    Steps:
    1. Load original image
    2. Convert mask to PIL Image
    3. Call Replicate SDXL-inpaint model
    4. Download and save result
    5. Return path to edited image
    """

    # Load image and mask
    image = Image.open(image_path)
    mask_img = Image.fromarray((mask * 255).astype(np.uint8))

    # Upload to Replicate
    input_data = {
        "image": image,
        "mask": mask_img,
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "num_inference_steps": 50
    }

    # Run inpainting
    output = await replicate.run(
        "stability-ai/sdxl-inpaint",
        input=input_data
    )

    # Download and save
    edited_path = await download_result(output)

    return edited_path
```

### 5. Performance Considerations

**WebSocket Scalability:**
- Use connection pooling for WebSocket connections
- Implement heartbeat/ping-pong to detect dead connections
- Set reasonable timeout (5 minutes) for idle connections
- Consider horizontal scaling with Redis pub/sub for multi-server support

**Session State Performance:**
- Use Redis with TTL (1 hour) for automatic cleanup
- Serialize large outputs (images) as URLs, not base64
- Implement pagination for conversation history (limit to last 50 messages)

**Image Processing:**
- Resize images to max 2048x2048 before sending to frontend
- Use WebP format for faster loading
- Implement client-side caching for edited images

### 6. Error Handling & Edge Cases

**Network Errors:**
- WebSocket disconnection → Frontend auto-reconnect with exponential backoff
- API timeout → Show user-friendly error, allow retry
- Lost session state → Restore from last saved checkpoint

**AI API Errors:**
- OpenAI rate limit → Queue request and retry
- Replicate model failure → Fallback to different model or notify user
- Invalid LLM response → Ask user to rephrase feedback

**User Actions:**
- User closes browser mid-pipeline → Session expires after TTL, cleanup resources
- User navigates away → Warn before losing progress
- Concurrent edits → Use optimistic locking to prevent conflicts

---

## Development Setup

**Prerequisites:**
- Python 3.11+
- Node.js 20.x+
- PostgreSQL 14+
- Redis 7.x (if using Redis for sessions)
- Git

**Backend Setup:**
```bash
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Set up environment variables
cp .env.example .env
# Edit .env and add:
# - DATABASE_URL
# - OPENAI_API_KEY
# - REPLICATE_API_TOKEN
# - REDIS_URL (if using Redis)
# - AWS credentials for S3

# 6. Run database migrations
alembic upgrade head

# 7. Start Redis (if using)
redis-server

# 8. Start development server
uvicorn app.main:app --reload --port 8000
```

**Frontend Setup:**
```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Set up environment variables
cp .env.example .env
# Edit .env and add:
# - VITE_API_URL=http://localhost:8000
# - VITE_WS_URL=ws://localhost:8000

# 4. Start development server
npm run dev
```

**Running Tests:**
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm run test

# With coverage
pytest --cov=app
npm run test:coverage
```

**Accessing the Application:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Implementation Guide

### Setup Steps

**Before Implementation:**

1. ✅ Create feature branch: `git checkout -b feature/interactive-pipeline`

2. ✅ Review existing code:
   - Read `multi_stage_orchestrator.py` to understand current pipeline
   - Review `image_prompt_enhancement.py` for feedback loop patterns
   - Check `story_generator.py` for story generation logic

3. ✅ Set up development environment:
   - Install Redis locally for session state testing
   - Add new environment variables to `.env`
   - Install new Python dependencies: `pip install redis websockets`
   - Install new npm dependencies: `npm install react-konva socket.io-client`

4. ✅ Database preparation:
   - Create migration for PipelineSession model (if using PostgreSQL for sessions)
   - Run migration: `alembic upgrade head`

5. ✅ Review PRD and Architecture:
   - Confirm interactive pipeline aligns with PRD vision
   - Check architecture for any constraints or patterns to follow

### Implementation Steps

**Implementation will proceed in 4 stories (see Stories section for detailed breakdown):**

#### Story 1: CLI Tools Organization (1 point - ~1 day)

**Goal:** Move Epic 8-9 CLI tools to separate directory

**Steps:**
1. Create `backend/cli_tools/` directory
2. Move CLI scripts from `backend/` to `cli_tools/`:
   - `enhance_image_prompt.py`
   - `generate_images.py`
   - `enhance_video_prompt.py`
   - `generate_videos.py`
   - `feedback_loop.py`
3. Update any import paths in CLI scripts if needed
4. Create `cli_tools/README.md` documenting CLI tool usage
5. Test that CLI tools still work: `python cli_tools/enhance_image_prompt.py --help`
6. Update any documentation referencing CLI tool locations

**Testing:**
- Run each CLI tool to verify no broken imports
- Check that output directories are created correctly

#### Story 2: Interactive Story Generation (3 points - ~2-3 days)

**Goal:** Add interactive story generation with chat feedback

**Backend Steps:**
1. Create `interactive_pipeline.py`:
   - Implement `InteractivePipelineOrchestrator` class
   - Add `run_stage_with_pause()` method
   - Implement session state management (Redis or PostgreSQL)

2. Create `conversation_handler.py`:
   - Implement `ConversationHandler` class
   - Add `process_story_feedback()` method
   - Integrate with OpenAI GPT-4 for feedback processing

3. Create `websocket.py` API route:
   - Implement WebSocket endpoint at `/ws/pipeline/{session_id}`
   - Handle connection management (connect, disconnect, heartbeat)
   - Process chat messages and send responses

4. Create `interactive_generation.py` API route:
   - `POST /api/v1/interactive/start` - Start pipeline
   - `GET /api/v1/interactive/{session_id}/status` - Get status
   - `POST /api/v1/interactive/{session_id}/approve` - Approve stage
   - `POST /api/v1/interactive/{session_id}/regenerate` - Regenerate

5. Create `interactive_schemas.py`:
   - Define Pydantic schemas for all requests/responses

**Frontend Steps:**
6. Create `pipelineStore.ts`:
   - Zustand store for pipeline state
   - Actions: startPipeline, updateStage, sendFeedback, approveStage

7. Create `websocket-service.ts`:
   - WebSocket connection management
   - Message handling (send/receive)
   - Auto-reconnect logic

8. Create `useWebSocket.ts` hook:
   - React hook for WebSocket functionality
   - Return connected status, sendMessage, messages

9. Create `ChatInterface.tsx`:
   - Reusable chat component
   - Message list + input
   - Loading states

10. Create `StoryReview.tsx`:
    - Display generated story
    - Integrate ChatInterface
    - Approve/Regenerate buttons
    - Show conversation history

11. Create `InteractivePipeline.tsx` (Story stage only):
    - Main pipeline component
    - Stage progress indicator
    - Render StoryReview when in story stage
    - Handle stage transitions

**Testing:**
- Backend: Test WebSocket connection, message handling, session state
- Frontend: Test chat interface, story approval flow, WebSocket reconnection
- Integration: Test full story generation → feedback → regeneration → approval

#### Story 3: Interactive Image/Storyboard Feedback (3 points - ~2-3 days)

**Goal:** Add interactive feedback for reference images and storyboard images

**Backend Steps:**
1. Extend `interactive_pipeline.py`:
   - Add reference_image stage support
   - Add storyboard stage support
   - Implement image-specific feedback processing

2. Extend `conversation_handler.py`:
   - Add `process_image_feedback()` method
   - Translate conversational feedback to image parameters
   - Handle batch feedback for multiple images

3. Update API routes:
   - Add image-specific endpoints if needed
   - Handle image regeneration requests

**Frontend Steps:**
4. Create `ImageReview.tsx`:
   - Image gallery display (grid layout)
   - Click to enlarge/select image
   - Integrate ChatInterface for feedback
   - Approve/Regenerate buttons
   - Show quality scores if available

5. Update `InteractivePipeline.tsx`:
   - Add reference_image stage rendering
   - Add storyboard stage rendering
   - Handle stage-specific UI

6. Create `useInteractivePipeline.ts` hook:
   - Pipeline state management logic
   - Stage transition handling
   - Feedback submission

**Testing:**
- Test image generation → feedback → regeneration flow
- Test storyboard generation → feedback → approval
- Test multiple regenerations in sequence

#### Story 4: Advanced Image Editing (3 points - ~2-3 days)

**Goal:** Add inpainting/object selection for image editing

**Backend Steps:**
1. Create `inpainting_service.py`:
   - Implement `InpaintingService` class
   - Add `inpaint()` method with SDXL-inpaint integration
   - Handle mask processing and API calls
   - Return edited image URL

2. Update API routes:
   - `POST /api/v1/interactive/{session_id}/inpaint` - Inpaint image
   - Accept image_id, mask data, prompt, negative_prompt

**Frontend Steps:**
3. Create `ImageEditor.tsx`:
   - Canvas with react-konva for drawing
   - Brush tool for mask selection
   - Eraser tool for mask editing
   - Clear mask button
   - Prompt input for replacement description
   - Preview original + masked region
   - Generate edited image button

4. Integrate ImageEditor with ImageReview:
   - "Edit" button on each image
   - Open ImageEditor modal/panel
   - Display edited result
   - Option to use edited image or revert

5. Update `interactive-api.ts`:
   - Add `inpaintImage()` API call
   - Handle mask data serialization

**Testing:**
- Test mask creation and editing
- Test inpainting with various prompts
- Test edited image replacement in pipeline
- Test edge cases (empty mask, invalid prompt)

### Testing Strategy

**Unit Tests:**

**Backend:**
- `test_interactive_pipeline.py`:
  - Test session creation and state management
  - Test stage transitions
  - Test pause/resume functionality
  - Mock OpenAI and Replicate API calls

- `test_conversation_handler.py`:
  - Test feedback intent extraction
  - Test story/image refinement logic
  - Mock LLM responses

- `test_inpainting_service.py`:
  - Test mask processing
  - Test Replicate API integration
  - Mock API responses

**Frontend:**
- `InteractivePipeline.test.tsx`:
  - Test stage rendering
  - Test stage transitions
  - Mock WebSocket and API calls

- `ChatInterface.test.tsx`:
  - Test message display
  - Test message sending
  - Test loading states

- `ImageEditor.test.tsx`:
  - Test brush tool functionality
  - Test mask creation
  - Mock canvas interactions

**Integration Tests:**

- **End-to-end pipeline flow:**
  1. Start pipeline with prompt
  2. Generate story
  3. Send feedback via chat
  4. Regenerate story
  5. Approve story
  6. Generate reference images
  7. Provide image feedback
  8. Approve images
  9. Generate storyboard
  10. Edit storyboard image (inpainting)
  11. Approve storyboard
  12. Verify final output

- **WebSocket resilience:**
  - Test disconnect/reconnect
  - Test message ordering
  - Test concurrent connections

- **Session state:**
  - Test state persistence across disconnections
  - Test session expiration
  - Test cleanup

**Manual Testing Checklist:**

- [ ] Can start pipeline and see story generated
- [ ] Can chat about story changes
- [ ] Story regenerates based on feedback
- [ ] Can approve story and move to images
- [ ] Can provide feedback on images
- [ ] Images regenerate with updated parameters
- [ ] Can open image editor and create mask
- [ ] Inpainting works and replaces selected region
- [ ] Can approve images and move to storyboard
- [ ] Can edit storyboard images
- [ ] Can complete full pipeline to video generation
- [ ] WebSocket reconnects after disconnection
- [ ] Session state persists across refreshes (within TTL)
- [ ] Error messages display appropriately
- [ ] Loading states show during generation

### Acceptance Criteria

**AC #1: CLI Tools Organization**
- GIVEN the Epic 8-9 CLI tools exist in `backend/`
- WHEN they are moved to `backend/cli_tools/`
- THEN they can still be executed independently
- AND they function identically to before
- AND documentation is updated

**AC #2: Interactive Story Generation**
- GIVEN a user starts the interactive pipeline
- WHEN the story is generated
- THEN it is displayed in the UI with a chat interface
- AND the user can send conversational feedback
- AND the story regenerates based on feedback
- AND the user can approve the story to proceed
- AND the pipeline pauses until approval

**AC #3: Interactive Image Feedback**
- GIVEN the user has approved the story
- WHEN reference images are generated
- THEN they are displayed in a gallery with chat interface
- AND the user can provide feedback on image quality/content
- AND images regenerate based on feedback
- AND the user can approve images to proceed
- AND the same workflow works for storyboard images

**AC #4: Advanced Image Editing**
- GIVEN an image is displayed in the review interface
- WHEN the user clicks "Edit"
- THEN an image editor opens with selection tools
- AND the user can draw a mask over regions to replace
- AND the user can provide a text prompt for replacement
- WHEN the user clicks "Generate"
- THEN the selected region is inpainted with new content
- AND the edited image replaces the original in the pipeline

**AC #5: WebSocket Reliability**
- GIVEN a WebSocket connection is established
- WHEN the connection drops
- THEN the frontend automatically reconnects
- AND chat messages sent during disconnection are queued and sent on reconnect
- AND the user sees a "Reconnecting..." indicator

**AC #6: Session State Persistence**
- GIVEN a pipeline is in progress
- WHEN the user refreshes the browser
- THEN the pipeline state is restored from the session
- AND the user can continue from the current stage
- AND conversation history is preserved

**AC #7: End-to-End Pipeline**
- GIVEN a user completes all interactive stages
- WHEN they approve the final storyboard
- THEN the pipeline proceeds to video generation
- AND the final video is generated with all approved/edited elements
- AND the entire workflow is tracked in the session history

---

## Developer Resources

### File Paths Reference

**Backend Files to Create:**
```
backend/
├── cli_tools/                                      # NEW DIRECTORY
│   ├── enhance_image_prompt.py                    # MOVE from backend/
│   ├── generate_images.py                         # MOVE from backend/
│   ├── enhance_video_prompt.py                    # MOVE from backend/
│   ├── generate_videos.py                         # MOVE from backend/
│   ├── feedback_loop.py                           # MOVE from backend/
│   └── README.md                                  # CREATE
│
├── app/
│   ├── services/
│   │   └── pipeline/
│   │       ├── interactive_pipeline.py            # CREATE
│   │       ├── conversation_handler.py            # CREATE
│   │       └── inpainting_service.py              # CREATE
│   │
│   ├── api/
│   │   └── routes/
│   │       ├── interactive_generation.py          # CREATE
│   │       └── websocket.py                       # CREATE
│   │
│   └── schemas/
│       └── interactive_schemas.py                 # CREATE
│
└── tests/
    ├── services/
    │   ├── test_interactive_pipeline.py           # CREATE
    │   ├── test_conversation_handler.py           # CREATE
    │   └── test_inpainting_service.py             # CREATE
    └── api/
        └── test_interactive_generation.py         # CREATE
```

**Frontend Files to Create:**
```
frontend/
├── src/
│   ├── components/
│   │   └── generation/
│   │       ├── InteractivePipeline.tsx            # CREATE
│   │       ├── StoryReview.tsx                    # CREATE
│   │       ├── ImageReview.tsx                    # CREATE
│   │       ├── ChatInterface.tsx                  # CREATE
│   │       ├── ImageEditor.tsx                    # CREATE
│   │       └── __tests__/
│   │           ├── InteractivePipeline.test.tsx   # CREATE
│   │           ├── ChatInterface.test.tsx         # CREATE
│   │           └── ImageEditor.test.tsx           # CREATE
│   │
│   ├── hooks/
│   │   ├── useWebSocket.ts                        # CREATE
│   │   └── useInteractivePipeline.ts              # CREATE
│   │
│   ├── services/
│   │   ├── interactive-api.ts                     # CREATE
│   │   └── websocket-service.ts                   # CREATE
│   │
│   ├── stores/
│   │   └── pipelineStore.ts                       # CREATE
│   │
│   └── types/
│       └── pipeline.ts                            # CREATE
```

### Key Code Locations

**Existing Code to Reference:**

1. **Pipeline Orchestration Pattern:**
   - File: `backend/app/services/pipeline/multi_stage_orchestrator.py`
   - Lines: 1-200
   - Purpose: Current 4-stage pipeline pattern to extend

2. **Story Generation:**
   - File: `backend/app/services/pipeline/story_generator.py`
   - Lines: 1-150
   - Purpose: Story generation logic to integrate with feedback

3. **Image Prompt Enhancement (Feedback Loop Pattern):**
   - File: `backend/app/services/pipeline/image_prompt_enhancement.py`
   - Lines: 1-300
   - Purpose: Two-agent feedback loop pattern to adapt for chat

4. **Image Generation:**
   - File: `backend/app/services/pipeline/image_generation.py`
   - Lines: 1-200
   - Purpose: Replicate API integration to extend for inpainting

5. **Storyboard Generation:**
   - File: `backend/app/services/pipeline/storyboard_generator.py`
   - Lines: 1-250
   - Purpose: Storyboard creation logic to integrate with editing

### Testing Locations

**Backend Tests:**
```
tests/
├── services/
│   ├── test_interactive_pipeline.py           # Unit tests for interactive pipeline
│   ├── test_conversation_handler.py           # Unit tests for conversation handler
│   └── test_inpainting_service.py             # Unit tests for inpainting
└── api/
    └── test_interactive_generation.py         # API endpoint tests
```

**Frontend Tests:**
```
src/components/generation/__tests__/
├── InteractivePipeline.test.tsx               # Component tests for main pipeline
├── ChatInterface.test.tsx                     # Component tests for chat
└── ImageEditor.test.tsx                       # Component tests for image editing
```

**Integration Tests:**
- Create `tests/integration/test_interactive_flow.py` for end-to-end pipeline testing
- Test full user journey from start to final video generation

### Documentation to Update

**After Implementation:**

1. **README.md** (Project root)
   - Update features list to include interactive pipeline
   - Add section on new interactive mode vs. automated mode

2. **docs/architecture.md**
   - Add interactive pipeline architecture diagram
   - Document WebSocket communication flow
   - Add session state management section

3. **backend/cli_tools/README.md** (NEW)
   - Document all CLI tools usage
   - Provide examples for each tool
   - Explain CLI tools are for development/testing, not production

4. **API Documentation** (Auto-generated via FastAPI)
   - Ensure all new endpoints have proper docstrings
   - Add request/response examples in schemas

5. **CHANGELOG.md**
   - Add entry for interactive pipeline feature
   - Note Epic 8-9 CLI tools reorganization

---

## UX/UI Considerations

**UI Components Affected:**

**New Components:**
- `InteractivePipeline` - Main pipeline interface with stage progression
- `StoryReview` - Story display with chat feedback
- `ImageReview` - Image gallery with chat feedback
- `ChatInterface` - Reusable chat component for LLM interaction
- `ImageEditor` - Canvas-based image editing with inpainting
- `StageProgress` - Visual indicator of pipeline progress

**Modified Components:**
- Video generation page - Add option to use interactive vs. automated pipeline
- Dashboard - Show in-progress interactive sessions

**UX Flow Changes:**

**Current Flow (Automated):**
```
User submits prompt → Loading spinner → Final video ready
(~3-5 minutes, no interaction)
```

**New Interactive Flow:**
```
User submits prompt → Story generated → Review + Chat → Approve
  → Reference images generated → Review + Chat + Edit → Approve
  → Storyboard generated → Review + Chat + Edit → Approve
  → Video generation → Final video ready
(~10-20 minutes with user interaction)
```

**Visual/Interaction Patterns:**

**Design System:**
- Use existing Tailwind CSS classes for consistency
- Follow existing color scheme and typography
- Component structure should match existing patterns in codebase

**Stage Progress Indicator:**
- Horizontal stepper showing: Story → Images → Storyboard → Video
- Current stage highlighted
- Completed stages show checkmark
- Future stages grayed out

**Chat Interface:**
- Similar to ChatGPT-style interface
- User messages on right (blue bubble)
- LLM responses on left (gray bubble)
- Timestamp for each message
- Auto-scroll to latest message
- Loading indicator while LLM generates response

**Image Gallery:**
- Grid layout (2-3 columns on desktop, 1 column on mobile)
- Click to enlarge (modal/lightbox)
- Quality scores displayed as badges
- "Edit" button on hover
- Selected image highlighted

**Image Editor:**
- Full-screen modal or side panel
- Canvas with image displayed
- Toolbar: Brush, Eraser, Clear, Brush Size slider
- Mask overlay (semi-transparent red/blue)
- Prompt input below canvas
- "Generate" button
- Loading state during inpainting
- Before/After comparison slider

**Responsive Design:**
- Mobile: Stack stages vertically, full-width chat
- Tablet: 2-column layout (content + chat sidebar)
- Desktop: 3-column layout (nav + content + chat)

**Accessibility:**

- **Keyboard Navigation:**
  - Tab through all interactive elements (buttons, inputs, images)
  - Enter to submit chat messages
  - Arrow keys to navigate image gallery
  - Escape to close modals

- **Screen Reader Compatibility:**
  - ARIA labels for all buttons: `aria-label="Approve story"`
  - ARIA live regions for chat messages: `aria-live="polite"`
  - Alt text for all generated images
  - Role attributes for custom components: `role="dialog"` for modals

- **ARIA Labels:**
  - Chat input: `aria-label="Enter feedback message"`
  - Approve button: `aria-label="Approve and continue to next stage"`
  - Regenerate button: `aria-label="Regenerate with feedback"`
  - Image editor brush: `aria-label="Brush tool for selection"`

- **Color Contrast:**
  - All text meets WCAG AA standard (4.5:1 for normal text)
  - Interactive elements have sufficient contrast
  - Selected states clearly distinguishable

**User Feedback:**

- **Loading States:**
  - Spinner with message: "Generating story...", "Regenerating images..."
  - Progress bar for long operations (video generation)
  - Disable buttons during processing
  - Show estimated time remaining if available

- **Error Messages:**
  - User-friendly error text: "Oops! Story generation failed. Please try again."
  - Specific errors: "Connection lost. Reconnecting..."
  - Retry button for failed operations
  - Contact support link for persistent errors

- **Success Confirmations:**
  - Toast notification: "Story approved! Moving to image generation..."
  - Checkmark animation on stage completion
  - Success sound (optional, user preference)

- **Progress Indicators:**
  - Stage progress bar at top
  - Current stage highlighted
  - Completed stages with checkmarks
  - Estimated time for each stage

**Empty States:**
- Before story generation: Welcoming message with pipeline explanation
- No conversation history: Prompt to start chatting for improvements
- No images yet: "Generating your images..." with animated placeholder

**Error States:**
- Generation failed: Error message with retry button
- WebSocket disconnected: "Reconnecting..." banner with auto-retry
- Session expired: "Session expired. Start a new generation?"

**Confirmation Dialogs:**
- Leaving page mid-pipeline: "Are you sure? Your progress will be lost."
- Approving stage: "This will proceed to the next stage. Continue?"
- Regenerating: "This will replace the current output. Continue?"

---

## Testing Approach

**CONFORM TO EXISTING TEST STANDARDS:**

**Backend Testing:**
- **Framework:** pytest 7.4.0 with pytest-asyncio 0.21.0
- **File naming:** `test_{module}.py`
- **Test naming:** `test_{function}_{scenario}`
- **Location:** `tests/` mirroring `app/` structure
- **Assertion style:** pytest assert statements
- **Mocking:** pytest-mock (mock external APIs: OpenAI, Replicate)
- **Async tests:** `@pytest.mark.asyncio` decorator for async functions
- **Coverage:** 80% minimum for new code

**Frontend Testing:**
- **Framework:** vitest 1.6.0 with @testing-library/react 16.1.0
- **File naming:** `{Component}.test.tsx`
- **Location:** `__tests__/` folder next to component
- **Assertion style:** vitest `expect()` assertions
- **Rendering:** `render()` from @testing-library/react
- **User interactions:** `fireEvent` or `userEvent` from testing-library
- **Coverage:** 70% minimum for new components

**Test Strategy:**

**1. Unit Tests:**

**Backend:**
- `test_interactive_pipeline.py`:
  - Test session creation and initialization
  - Test stage transitions (story → images → storyboard)
  - Test pause/resume functionality
  - Test session state save/load
  - Mock all external API calls (OpenAI, Replicate)

- `test_conversation_handler.py`:
  - Test feedback intent extraction from user messages
  - Test story refinement logic
  - Test image feedback processing
  - Mock OpenAI GPT-4 responses

- `test_inpainting_service.py`:
  - Test mask processing (numpy array to PIL Image)
  - Test Replicate SDXL-inpaint API call
  - Test image download and save
  - Mock Replicate API responses

- `test_interactive_generation.py`:
  - Test API endpoints (start, status, approve, regenerate)
  - Test request validation (Pydantic schemas)
  - Test authentication/authorization
  - Mock pipeline orchestrator

**Frontend:**
- `InteractivePipeline.test.tsx`:
  - Test rendering of different stages
  - Test stage transitions
  - Test approve/regenerate button clicks
  - Mock WebSocket and API calls

- `ChatInterface.test.tsx`:
  - Test message rendering (user vs. LLM messages)
  - Test message sending
  - Test loading state during LLM response
  - Test auto-scroll to latest message

- `ImageEditor.test.tsx`:
  - Test brush tool selection
  - Test mask drawing (mock canvas interactions)
  - Test prompt input
  - Test generate button click
  - Mock API calls for inpainting

**2. Integration Tests:**

**Backend Integration:**
- `test_interactive_flow.py`:
  - Test full pipeline: start → story → images → storyboard → video
  - Test feedback processing at each stage
  - Test session persistence across stages
  - Use TestClient for API calls
  - Mock external APIs but test real service integration

**Frontend Integration:**
- Test InteractivePipeline + StoryReview + ChatInterface integration
- Test ImageReview + ImageEditor integration
- Test WebSocket message flow
- Use MSW (Mock Service Worker) for API mocking

**3. End-to-End Tests (Manual/Automated):**

**Critical User Journeys:**
1. Happy path: Start → Story (approve) → Images (approve) → Storyboard (approve) → Video
2. Feedback loop: Generate story → Give feedback → Regenerate → Approve
3. Image editing: Generate images → Edit with inpainting → Approve
4. Error recovery: Connection drop → Reconnect → Resume session
5. Multiple regenerations: Regenerate 3 times → Approve

**Performance Tests:**
- WebSocket connection under load (100 concurrent connections)
- Session state read/write performance (Redis benchmarks)
- Large image inpainting (2048x2048) processing time

**Coverage:**

**Target Coverage:**
- Backend: 80% minimum
- Frontend: 70% minimum
- Critical paths: 100% (pipeline orchestration, session management)

**Coverage Commands:**
```bash
# Backend coverage
cd backend
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Frontend coverage
cd frontend
npm run test:coverage
open coverage/index.html
```

**Test Data:**

**Mock Data:**
- Sample prompts for testing
- Pre-generated story text
- Sample image URLs (use placeholder images)
- Mock LLM responses (saved as fixtures)
- Mock Replicate API responses

**Fixtures:**
```python
# pytest fixtures
@pytest.fixture
def sample_session():
    return {
        "session_id": "test-123",
        "user_id": "user-456",
        "status": "story",
        "outputs": {}
    }

@pytest.fixture
def mock_story():
    return {
        "narrative": "Sample story text...",
        "script": "Sample script...",
        "framework": "AIDA"
    }
```

---

## Deployment Strategy

### Deployment Steps

**Pre-Deployment Checklist:**
1. ✅ All tests passing (backend + frontend)
2. ✅ Code reviewed and approved
3. ✅ Environment variables configured in staging/production
4. ✅ Redis instance provisioned and accessible
5. ✅ Database migrations tested in staging
6. ✅ API rate limits reviewed (OpenAI, Replicate)
7. ✅ WebSocket load testing completed

**Deployment Process:**

**1. Backend Deployment:**
```bash
# 1. Merge feature branch to main
git checkout main
git merge feature/interactive-pipeline

# 2. Tag release
git tag -a v1.1.0 -m "Add interactive pipeline feature"
git push origin v1.1.0

# 3. Deploy to staging
# (Assuming CI/CD pipeline auto-deploys to staging on push to main)
# Verify deployment:
curl https://staging-api.ad-mint-ai.com/health

# 4. Run database migrations in staging
alembic upgrade head

# 5. Smoke test in staging:
# - Start interactive pipeline
# - Test WebSocket connection
# - Test each stage (story, images, storyboard)
# - Test inpainting

# 6. Deploy to production (after staging validation)
# (Manual approval or auto-deploy after X hours)

# 7. Run database migrations in production
alembic upgrade head

# 8. Monitor logs and metrics
tail -f /var/log/ad-mint-ai/app.log
# Check Redis connections, WebSocket count, API latency
```

**2. Frontend Deployment:**
```bash
# 1. Build production bundle
cd frontend
npm run build

# 2. Deploy to CDN/hosting (e.g., Vercel, Netlify, S3 + CloudFront)
# (CI/CD auto-deploys on push to main)

# 3. Verify deployment
curl https://ad-mint-ai.com
# Check browser console for errors

# 4. Test interactive pipeline in production
# - Manual test of full user journey
# - Check WebSocket connection (wss://)
# - Verify API calls use production backend
```

**3. Infrastructure:**

**New Services to Deploy:**
- **Redis:** For session state management
  - Provision Redis instance (AWS ElastiCache, Redis Cloud, etc.)
  - Configure TTL (1 hour default)
  - Set up monitoring (memory usage, connection count)

**Configuration Changes:**
- Add Redis URL to environment variables (staging + production)
- Update WebSocket URL in frontend `.env` (wss:// for production)
- Configure CORS to allow WebSocket connections
- Update API rate limits if needed

**4. Gradual Rollout (Optional):**

**Feature Flag Approach:**
- Use feature flag to enable interactive pipeline for subset of users
- Start with 10% of users, monitor for issues
- Increase to 50% after 24 hours if stable
- Full rollout after 1 week

```python
# Example feature flag check
if feature_flags.is_enabled("interactive_pipeline", user_id):
    # Show interactive pipeline option
else:
    # Show only automated pipeline
```

### Rollback Plan

**If Critical Issues Occur:**

**1. Immediate Rollback (< 15 minutes):**
```bash
# 1. Revert backend to previous version
git revert v1.1.0
git push origin main
# CI/CD auto-deploys previous version

# 2. Revert frontend to previous version
# (If using Git-based deployment)
git revert <frontend-commit-hash>
git push origin main

# 3. Verify rollback
curl https://api.ad-mint-ai.com/health
# Check that interactive pipeline endpoints are gone
```

**2. Database Rollback (if migrations caused issues):**
```bash
# Rollback database to previous migration
alembic downgrade -1

# Verify database state
psql -U admin -d ad_mint_ai -c "SELECT * FROM alembic_version;"
```

**3. Feature Flag Disable (quickest option):**
```python
# Disable feature flag without deployment
feature_flags.disable("interactive_pipeline")
# All users revert to automated pipeline
```

**Rollback Triggers:**
- Error rate > 5% for interactive pipeline endpoints
- WebSocket connection failures > 20%
- P0/P1 bugs reported by users (data loss, unable to generate videos)
- Redis connection failures
- External API rate limits exceeded

### Monitoring

**What to Monitor After Deployment:**

**1. Application Metrics:**
- **Error rates:**
  - Overall error rate (target: < 1%)
  - WebSocket connection errors
  - Pipeline stage failures (story, images, storyboard)
  - Inpainting failures

- **Performance:**
  - API response times (target: < 500ms for most endpoints)
  - WebSocket message latency (target: < 100ms)
  - Session state read/write latency (Redis)
  - Pipeline stage completion times

- **Usage:**
  - Number of interactive pipelines started per hour
  - Stage completion rates (how many users complete each stage)
  - Feedback messages per session (avg)
  - Regeneration requests per stage
  - Inpainting requests per session

**2. Infrastructure Metrics:**
- **Redis:**
  - Memory usage (target: < 80% of allocated)
  - Connection count
  - Cache hit rate
  - Eviction rate (should be 0 for session data)

- **WebSocket:**
  - Active WebSocket connections
  - Connection duration (avg)
  - Disconnect rate
  - Reconnection attempts

- **External APIs:**
  - OpenAI API call count and latency
  - Replicate API call count and latency
  - Rate limit proximity (warn at 80%)
  - API error rates

**3. User Experience:**
- **Session Analytics:**
  - Time spent per stage (avg)
  - Abandonment rate (% of users who start but don't finish)
  - User satisfaction (post-generation survey)
  - Feedback quality (LLM analysis of user messages)

- **Error Logs:**
  - Monitor for repeated error patterns
  - User-reported issues (support tickets)
  - Client-side errors (JavaScript console errors)

**4. Alerts to Configure:**
- Error rate > 5% for 5 minutes → Page on-call engineer
- WebSocket connection failures > 20% → Alert Slack channel
- Redis memory > 90% → Alert infrastructure team
- External API rate limit > 80% → Alert development team
- Pipeline abandonment rate > 50% → Alert product team

**Monitoring Tools:**
- **Logs:** CloudWatch Logs, Datadog, or ELK stack
- **Metrics:** Prometheus + Grafana, Datadog, or New Relic
- **Alerts:** PagerDuty, Opsgenie, or Slack webhooks
- **User Analytics:** Mixpanel, Amplitude, or Google Analytics
- **Error Tracking:** Sentry for frontend and backend errors

**Example Grafana Dashboard Panels:**
1. Interactive Pipeline Usage (line chart over time)
2. Stage Completion Funnel (funnel chart: start → story → images → storyboard → video)
3. Error Rate by Endpoint (bar chart)
4. WebSocket Active Connections (gauge)
5. Redis Memory Usage (line chart)
6. External API Latency (line chart: OpenAI, Replicate)
7. Session Duration Distribution (histogram)

---

**End of Technical Specification**
