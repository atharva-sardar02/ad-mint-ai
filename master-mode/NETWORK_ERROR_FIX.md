# Master Mode Network Error Fix

**Date:** November 21, 2024  
**Issue:** Frontend shows "Network error" but backend successfully generates videos

## Problem

The user was experiencing a situation where:
1. ✅ Backend successfully generated videos (visible in temp folder)
2. ✅ All 3 scenes completed (logs show 100% progress)
3. ❌ Frontend shows "Network error - please check your connection"
4. ❌ No video player or results shown on frontend

### Root Cause

The issue was caused by **SSE (Server-Sent Events) connection failures**:

1. Frontend successfully calls `/api/master-mode/generate-story` (generation starts)
2. Backend processes the generation successfully
3. Frontend tries to connect to `/api/master-mode/progress/{generation_id}` via SSE
4. SSE connection fails with **403 Forbidden** (authentication issue)
5. Frontend never receives the completion event
6. User sees "Network error" even though generation succeeded

### Why SSE Failed

`EventSource` (used for SSE) has limitations:
- Cannot send custom headers (like Authorization tokens)
- Relies on cookies for authentication with `withCredentials: true`
- After page refreshes or in some browser states, cookies might not be sent properly
- Returns 403 if authentication fails

## Solution

### 1. **Fallback Polling Mechanism** (Added)

Added a polling mechanism that checks the generation status every 5 seconds if the SSE connection fails:

```typescript
// Poll for generation status if SSE connection fails
useEffect(() => {
  if (!generationId || finalVideo) return;

  const pollForCompletion = async () => {
    try {
      const response = await apiClient.get(`/api/generations/${generationId}`);
      const generation = response.data;
      
      if (generation.status === "completed" && generation.video_url) {
        // Extract video paths from database
        handleGenerationComplete({
          finalVideoPath: generation.video_url,
          sceneVideos: generation.temp_clip_paths || [],
          numScenes: generation.num_scenes || 0,
        });
      } else if (generation.status === "failed") {
        // Show error
      }
    } catch (error) {
      console.error("Failed to poll generation status:", error);
    }
  };

  // Poll every 5 seconds
  const interval = setInterval(pollForCompletion, 5000);
  pollForCompletion(); // Also poll immediately

  return () => clearInterval(interval);
}, [generationId, finalVideo]);
```

### How It Works

1. **Primary Method:** SSE connection via `LLMConversationViewer`
   - Shows real-time LLM interactions
   - Fast updates with conversation details
   
2. **Fallback Method:** HTTP polling (new)
   - Checks generation status every 5 seconds
   - Fetches completed video from database
   - Displays video even if SSE failed
   - Stops polling once video is found or status is "failed"

### Benefits

- ✅ Videos will now display even if SSE connection fails
- ✅ Works with authentication issues
- ✅ Doesn't rely on cookies being sent properly
- ✅ User always sees their completed video
- ✅ Graceful degradation (SSE preferred, polling as backup)

## Files Modified

1. **`frontend/src/routes/MasterMode.tsx`**
   - Added `useEffect` import
   - Added polling mechanism with `useEffect` hook
   - Polls `/api/generations/{generationId}` every 5 seconds
   - Stops when video is found or generation fails

## Testing

To test the fix:

1. **Start a Master Mode generation**
2. **Wait for completion** (3-5 minutes)
3. **Check the frontend:**
   - If SSE works: See real-time LLM conversation + video player
   - If SSE fails: Wait ~5 seconds, video player should appear automatically

## Alternative Solutions (Not Implemented)

### Option A: WebSocket Instead of SSE
- More complex to implement
- Better authentication support
- Overkill for one-way communication

### Option B: Fix SSE Authentication
- EventSource doesn't support custom headers
- Would need to pass token as query parameter (security risk)
- Or use a different SSE library that supports headers

### Option C: Long Polling
- Less efficient than SSE
- More server load
- Current solution uses both (SSE + fallback polling)

## Current Status

✅ **Issue Resolved**
- Fallback polling implemented
- Videos will display even with SSE failures
- No user action required
- Automatic retry every 5 seconds

## Next Steps (Optional Improvements)

1. **Improve SSE Authentication**
   - Consider using query parameters for token (if security allows)
   - Or use a session-based auth that's more cookie-friendly

2. **Add Better Error Messages**
   - Distinguish between "generating" and "checking status"
   - Show polling indicator if SSE fails

3. **Optimize Polling Interval**
   - Could use exponential backoff
   - Or stop polling sooner if status doesn't change

## Follow-Up Enhancement (Nov 21, 2024 - Later)

Users continued to see the `"Network error - please check your connection"` toast because the initial `POST /api/master-mode/generate-story` request runs for 5–8 minutes and exceeds Axios' 5-minute timeout. Although the backend kept running (videos were generated successfully), the frontend thought the request failed and never displayed progress.

### Fixes

1. **Client-Supplied Generation ID**
   - The frontend now creates a UUID **before** submitting the form and sends it as `client_generation_id`.
   - The backend uses this ID (or generates a new one if not provided).
   - SSE queues can now be created even if the POST request is still running.

2. **Optimistic UI**
   - The frontend sets `generationId` and shows the conversation panel immediately after submission.
   - SSE connects right away (even if the POST request is still pending or times out).

3. **Graceful Network Error Handling**
   - If Axios throws a `NetworkError`, we now show an informational toast:  
     `"Generation is running in the background. Live updates will appear below."`
   - We keep the conversation view open so the user still sees streaming progress and completion events.

4. **Idempotent Progress Queues**
   - `create_progress_queue` now reuses existing queues so SSE connections can safely pre-create a queue before the backend starts streaming.

### Result

Even if the initial POST request times out or the browser reports a network error, the user still:
- Sees live progress (SSE or polling fallback)
- Gets completion events
- Watches the final video inside Master Mode without navigating to the gallery

This keeps the UX responsive without rewriting the backend pipeline into background tasks.

