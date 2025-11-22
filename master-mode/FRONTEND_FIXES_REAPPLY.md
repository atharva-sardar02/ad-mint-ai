# Frontend Fixes to Reapply After Git Revert

## Date: 2025-11-21

This document contains all the frontend fixes that were made to resolve video playback and display issues. Apply these after reverting the backend to a working version.

---

## Overview of Frontend Issues Fixed

1. **Video URLs were absolute file paths** (e.g., `D:/gauntlet-ai/...`) instead of HTTP URLs
2. **Videos not playing in gallery** - no thumbnails, just "video is completed"
3. **Editor compatibility** - Master Mode videos were opening in the editor but had no clips
4. **Progress not visible** - SSE connection issues and fallback polling
5. **Network errors** - Frontend timeout on initial POST request

---

## Fix 1: Video URL Construction in VideoPlayer Component

### File: `frontend/src/components/master-mode/VideoPlayer.tsx`

**Problem**: Video paths were absolute file paths like `D:/gauntlet-ai/ad-mint-ai/backend/temp/...`

**Solution**: Detect and extract relative paths from absolute paths

```typescript
// Add this logic to construct the video URL (around line 20-50)

const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Handle different path formats
let videoUrl: string;
if (videoPath.startsWith("http")) {
  // Already a full URL
  videoUrl = videoPath;
} else if (videoPath.includes(":/") || videoPath.includes(":\\")) {
  // Absolute file path (e.g., D:/gauntlet-ai/ad-mint-ai/backend/temp/...)
  // Extract the relative path starting from 'temp' or 'output'
  const normalized = videoPath.replace(/\\/g, "/");
  const tempIndex = normalized.indexOf("/temp/");
  const outputIndex = normalized.indexOf("/output/");
  
  let relativePath: string;
  if (tempIndex !== -1) {
    relativePath = normalized.substring(tempIndex);
  } else if (outputIndex !== -1) {
    relativePath = normalized.substring(outputIndex);
  } else {
    // Fallback if neither 'temp' nor 'output' is found
    console.warn("VideoPlayer: Could not determine relative path from absolute path:", videoPath);
    relativePath = normalized;
  }
  videoUrl = `${apiUrl}${relativePath}`;
} else {
  // Relative path (e.g., /temp/master_mode/...)
  videoUrl = `${apiUrl}${videoPath.startsWith("/") ? "" : "/"}${videoPath.replace(/\\/g, "/")}`;
}

// Use videoUrl in the <video> element
<video src={videoUrl} controls />
```

**Location**: Inside the `VideoPlayer` component, before the return statement.

---

## Fix 2: Disable Editor for Master Mode Videos

### File: `frontend/src/routes/VideoDetail.tsx`

**Problem**: Master Mode videos were opening in the editor but showing 0 clips, causing confusion.

**Solution**: Disable the "Edit Video" button for Master Mode videos.

### Step 1: Add `framework` field to TypeScript interface

**File**: `frontend/src/lib/types/api.ts`

```typescript
export interface GenerationListItem {
  id: string;
  title: string | null;
  prompt: string;
  status: GenerationStatus;
  video_url: string | null;
  thumbnail_url: string | null;
  duration: number;
  cost: number | null;
  created_at: string;
  completed_at: string | null;
  generation_group_id: string | null;
  variation_label: string | null;
  coherence_settings: Record<string, boolean> | null;
  parent_generation_id: string | null;
  model: string | null;
  num_clips: number | null;
  use_llm: boolean | null;
  generation_time_seconds: number | null;
  framework: string | null; // ← ADD THIS LINE
}
```

### Step 2: Conditionally render "Edit Video" button

**File**: `frontend/src/routes/VideoDetail.tsx`

Find the "Edit Video" button (search for `Edit Video`) and wrap it with a condition:

```typescript
{generation.status === "completed" && generation.framework !== "master_mode" && (
  <Button
    onClick={() => navigate(`/editor/${generation.id}`)}
    variant="primary"
    disabled={deleting}
  >
    Edit Video
  </Button>
)}
```

**Location**: Around line 400-410 in the VideoDetail component, inside the actions section.

---

## Fix 3: Fallback Polling for Generation Status

### File: `frontend/src/routes/MasterMode.tsx`

**Problem**: If SSE connection failed, the frontend had no way to retrieve completed videos.

**Solution**: Add polling mechanism to check generation status every 5 seconds.

### Step 1: Add state for tracking 404 errors

```typescript
const [generationNotFoundAttempts, setGenerationNotFoundAttempts] = useState(0);
```

**Location**: Add this with other state declarations at the top of the component.

### Step 2: Add useEffect for polling

```typescript
// Poll for generation status if SSE connection fails or for initial load
useEffect(() => {
  if (!generationId || finalVideo) return;

  const pollForCompletion = async () => {
    try {
      const response = await apiClient.get(`/api/generations/${generationId}`);
      const generation = response.data;
      
      if (generation.status === "completed" && generation.video_url) {
        handleGenerationComplete({
          finalVideoPath: generation.video_url,
          sceneVideos: generation.temp_clip_paths || [],
          numScenes: generation.num_scenes || 0,
          cohesionScore: generation.cohesion_score || 0,
          storyScore: generation.story_score || 0,
        });
        setGenerationNotFoundAttempts(0); // Reset on success
      } else if (generation.status === "failed") {
        setToast({
          message: `Generation failed: ${generation.error_message || "Unknown error"}`,
          type: "error",
          isVisible: true,
        });
        setShowConversation(false);
        setGenerationId(null);
        setGenerationNotFoundAttempts(0);
      } else {
        setGenerationNotFoundAttempts(0); // Reset if still processing
      }
    } catch (error: any) {
      console.error("Failed to poll generation status:", error);
      if (error.response?.status === 404) {
        setGenerationNotFoundAttempts((prev) => prev + 1);
        if (generationNotFoundAttempts >= 3) { // Stop after 3 attempts
          setToast({
            message: "Generation not found. It might have failed or not started. Please try again.",
            type: "error",
            isVisible: true,
          });
          setShowConversation(false);
          setGenerationId(null);
        }
      } else {
        setToast({
          message: `Failed to fetch generation status: ${error.message || "Unknown error"}`,
          type: "error",
          isVisible: true,
        });
        setShowConversation(false);
        setGenerationId(null);
      }
    }
  };

  const interval = setInterval(pollForCompletion, 5000);
  pollForCompletion(); // Also poll immediately

  return () => clearInterval(interval);
}, [generationId, finalVideo, generationNotFoundAttempts]);
```

**Location**: Add this useEffect after the state declarations and before the handler functions.

---

## Fix 4: Network Error Handling

### File: `frontend/src/routes/MasterMode.tsx`

**Problem**: If the initial POST request timed out, the frontend showed an error and stopped, even though generation was running in the background.

**Solution**: Catch network errors and show an info message instead.

### Step 1: Add NetworkError class

**File**: `frontend/src/lib/api/client.ts`

```typescript
export class NetworkError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "NetworkError";
  }
}

// In the axios interceptor for errors:
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response && error.request) {
      // Network error - no response received
      throw new NetworkError("Network error - please check your connection");
    }
    // ... rest of error handling
  }
);
```

### Step 2: Handle network errors in form submission

**File**: `frontend/src/routes/MasterMode.tsx`

In the `handleSubmit` function, update the error handling:

```typescript
catch (error: any) {
  console.error("Error starting generation:", error);
  if (error instanceof NetworkError || error?.name === "NetworkError") {
    setToast({
      message: "Generation is running in the background. Live updates will appear below.",
      type: "info",
      isVisible: true,
    });
  } else {
    setToast({
      message: error.response?.data?.detail || "Failed to start generation",
      type: "error",
      isVisible: true,
    });
    setShowConversation(false); // Hide conversation on hard error
    setGenerationId(null); // Clear generation ID
  }
} finally {
  setIsLoading(false);
}
```

**Location**: Inside the `handleSubmit` function's catch block.

---

## Fix 5: SSE Reconnection Limits

### File: `frontend/src/components/master-mode/LLMConversationViewer.tsx`

**Problem**: SSE would try to reconnect infinitely on errors like 403 Forbidden.

**Solution**: Limit reconnection attempts to 3 and call onError after that.

```typescript
useEffect(() => {
  const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
  
  const eventSource = new EventSource(
    `${apiUrl}/api/master-mode/progress/${generationId}`,
    { withCredentials: true } // Ensure cookies are sent
  );

  let reconnectAttempts = 0;
  const MAX_RECONNECT_ATTEMPTS = 3;

  eventSource.onmessage = (event) => {
    reconnectAttempts = 0; // Reset on successful message
    
    // ... rest of message handling
  };

  eventSource.onerror = (error) => {
    console.error("SSE connection error:", error);
    
    reconnectAttempts++;
    
    if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      eventSource.close();
      if (onError) {
        onError("Connection to server lost. Please refresh the page or check the gallery.");
      }
    }
  };

  return () => {
    eventSource.close();
  };
}, [generationId, onComplete, onError]);
```

**Location**: Inside the `useEffect` hook that creates the EventSource.

---

## Fix 6: Pre-generate Generation ID

### File: `frontend/src/routes/MasterMode.tsx`

**Problem**: Frontend couldn't start SSE stream until backend responded, causing no progress updates.

**Solution**: Generate ID on frontend and send it to backend.

```typescript
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();

  if (!validateForm()) {
    setToast({
      message: "Please fix the errors before submitting",
      type: "error",
      isVisible: true,
    });
    return;
  }

  setIsLoading(true);
  setToast({ message: "", type: "info", isVisible: false });
  setSceneVideos([]);
  setFinalVideo(null);
  setGenerationDetails({});
  setGenerationNotFoundAttempts(0);

  // Pre-generate generation ID so we can start SSE immediately
  const generatedId =
    typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : `gen-${Date.now()}-${Math.random().toString(16).slice(2)}`;

  setGenerationId(generatedId);
  setShowConversation(true); // Start SSE immediately

  try {
    // Prepare form data
    const formData = new FormData();
    formData.append("prompt", prompt);
    if (title) formData.append("title", title);
    if (brandName) formData.append("brand_name", brandName);
    formData.append("generate_scenes", "true");
    formData.append("generate_videos", "true");
    formData.append("client_generation_id", generatedId); // ← Send pre-generated ID
    
    // Add reference images
    referenceImages.forEach((img) => {
      if (img.file) {
        formData.append("reference_images", img.file);
      }
    });

    // Call API
    const response = await apiClient.post<StoryGenerationResponse>(
      "/api/master-mode/generate-story",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );

    setToast({
      message: "Generation started! Watch the AI agents work below.",
      type: "success",
      isVisible: true,
    });
  } catch (error: any) {
    // ... error handling from Fix 4
  } finally {
    setIsLoading(false);
  }
};
```

**Location**: Replace the entire `handleSubmit` function.

---

## Testing Checklist

After applying these fixes, test:

1. ✅ **Video Playback in Gallery**: Videos should play with correct URLs
2. ✅ **Master Mode Videos Don't Open in Editor**: "Edit Video" button should be disabled
3. ✅ **Progress Updates Visible**: SSE should show real-time agent conversation
4. ✅ **Fallback Polling Works**: If SSE fails, polling should retrieve completed videos
5. ✅ **Network Error Handling**: Timeout on POST should show info message, not error
6. ✅ **SSE Reconnection Limits**: Should stop trying after 3 failed attempts

---

## Summary of Changes

### Files Modified:
1. `frontend/src/components/master-mode/VideoPlayer.tsx` - Video URL construction
2. `frontend/src/routes/VideoDetail.tsx` - Disable editor for Master Mode
3. `frontend/src/lib/types/api.ts` - Add `framework` field
4. `frontend/src/routes/MasterMode.tsx` - Polling, network errors, pre-generated ID
5. `frontend/src/components/master-mode/LLMConversationViewer.tsx` - SSE reconnection limits
6. `frontend/src/lib/api/client.ts` - NetworkError class

### Key Improvements:
- 🎬 **Video URLs**: Correctly handle absolute paths from backend
- 🚫 **Editor Protection**: Prevent Master Mode videos from opening in incompatible editor
- 📡 **Robust SSE**: Fallback polling + reconnection limits
- 🌐 **Network Resilience**: Handle timeouts gracefully
- ⚡ **Better UX**: Immediate progress updates with pre-generated IDs

---

## Notes

- All fixes are **frontend-only** and don't depend on backend changes
- These fixes were tested and working before the Story Director regression
- The backend revert won't affect these frontend improvements
- Make sure `VITE_API_URL` environment variable is set correctly

---

## Quick Apply Script (Optional)

If you want to automate applying these fixes, you can create a script. However, **manual application is recommended** to ensure each fix is correctly integrated with your current code.

Good luck! These fixes will make your frontend much more robust. 🚀

