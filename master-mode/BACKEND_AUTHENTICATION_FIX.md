# Backend Authentication & SSE Fix

## Issue Analysis

Based on the frontend errors:
1. **403 Forbidden on `/api/master-mode/progress/{id}`** - SSE endpoint requires authentication
2. **404 Not Found on `/api/generations/{id}`** - Generation record not found in database
3. **SSE reconnection loop** - Frontend tries to reconnect indefinitely

## Root Cause

After the git revert, the backend is missing the authentication credentials or the generation record wasn't created properly. The SSE endpoint at `backend/app/api/routes/master_mode_progress.py` line 114 requires `current_user: User = Depends(get_current_user)`.

## Solutions

### Option 1: Make SSE Endpoint Public (Quick Fix)

If Master Mode generations don't require strict authentication during progress streaming:

**File**: `backend/app/api/routes/master_mode_progress.py`

```python
# Change line 111-116 from:
@router.get("/progress/{generation_id}")
async def stream_progress(
    generation_id: str,
    current_user: User = Depends(get_current_user)  # ← Remove this
):
    """Stream real-time progress updates via SSE."""
    logger.info(f"[Progress] Starting stream for {generation_id}")

# To:
@router.get("/progress/{generation_id}")
async def stream_progress(
    generation_id: str
    # No authentication required for streaming progress
):
    """Stream real-time progress updates via SSE."""
    logger.info(f"[Progress] Starting stream for {generation_id}")
```

### Option 2: Fix Frontend Authentication (Proper Fix)

Ensure the frontend is sending authentication cookies/headers with the SSE request.

**File**: `frontend/src/components/master-mode/LLMConversationViewer.tsx`

The fix is already applied (line 66: `withCredentials: true`), but verify your API client is configured correctly.

**File**: `frontend/src/lib/apiClient.ts` (or equivalent)

```typescript
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  withCredentials: true, // ← Ensure this is set
  headers: {
    'Content-Type': 'application/json',
  },
});

// ... interceptors ...
```

### Option 3: Add Database Record Creation Check

Ensure the generation record is created BEFORE starting SSE.

**File**: `backend/app/api/routes/master_mode.py`

Verify this logic exists (around line 150-180):

```python
@router.post("/generate-story")
async def generate_story(
    # ... parameters ...
    client_generation_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        # Use client_generation_id if provided
        generation_id = client_generation_id if client_generation_id else str(uuid.uuid4())
        
        # CREATE DATABASE RECORD FIRST
        db_generation = Generation(
            id=generation_id,
            user_id=current_user.id,
            prompt=prompt,
            title=title or "Master Mode Video",
            status="processing",
            progress=0,
            current_step="Initializing...",
            framework="master_mode",
            created_at=datetime.utcnow()
        )
        db.add(db_generation)
        db.commit()
        logger.info(f"[Master Mode] Created database record for generation {generation_id}")
        
        # THEN create progress queue
        create_progress_queue(generation_id)
        await send_progress_update(generation_id, "init", "in_progress", 0, "Starting generation...")
        
        # ... rest of generation logic ...
```

## Recommended Fix

**Use Option 1 (Remove authentication from SSE)** for the quickest fix, as SSE streams are ephemeral and don't expose sensitive data. The generation_id itself acts as a capability token.

## Testing

After applying the fix:

1. Start backend: `cd backend && python -m uvicorn app.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Submit a Master Mode generation
4. Verify no 403 errors in browser console
5. Verify progress updates appear in real-time

## Additional: Add Fallback Polling (Frontend Fix 3)

This was missing from the original frontend fixes and provides resilience if SSE fails.

See: `FRONTEND_FIXES_REAPPLY.md` - Fix 3

This should already be documented but needs to be implemented in `frontend/src/routes/MasterMode.tsx`.

