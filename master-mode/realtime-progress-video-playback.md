# Master Mode: Real-Time Progress & Video Playback

## Overview

Added real-time progress updates using Server-Sent Events (SSE) so the frontend can show which step is currently running, plus video players for individual scenes and final output.

## Backend Implementation

### 1. SSE Progress Endpoint

**File**: `backend/app/api/routes/master_mode_progress.py`

**Endpoint**: `GET /api/master-mode/progress/{generation_id}`

**Features**:
- Streams real-time progress updates
- Uses Server-Sent Events (SSE)
- In-memory queue per generation
- Automatic cleanup when complete

**Progress Update Format**:
```json
{
  "step": "story|scenes|video_params|videos|complete",
  "status": "in_progress|completed|failed",
  "progress": 0-100,
  "message": "Human-readable status message",
  "data": {
    "final_video_path": "...",
    "scene_videos": ["..."]
  }
}
```

### 2. Updated Main Endpoint

**File**: `backend/app/api/routes/master_mode.py`

**New Response Fields**:
```json
{
  "generation_id": "uuid-here",  // NEW!
  "scene_videos": [              // NEW!
    "path/to/scene_01.mp4",
    "path/to/scene_02.mp4",
    ...
  ],
  "final_video_path": "path/to/final.mp4",
  // ... existing fields
}
```

### 3. Progress Steps

| Step | Progress | Message |
|------|----------|---------|
| init | 0% | Starting generation... |
| upload | 5% | Saving reference images... |
| upload | 10% | Saved N reference images |
| story | 15% | Generating story with vision-enhanced AI... |
| story | 30% | Story generated (score: X/100) |
| scenes | 35% | Generating detailed scenes... |
| scenes | 55% | Generated N scenes (cohesion: X/100) |
| video_params | 60% | Preparing video generation parameters... |
| video_params | 65% | Prepared N video generation parameter sets |
| videos | 70% | Generating scene videos (may take several minutes)... |
| videos | 95% | Videos generated and stitched successfully! |
| complete | 100% | Generation complete! |

## Frontend Implementation (TO DO)

### 1. Progress Component

```typescript
// frontend/src/components/master-mode/ProgressTracker.tsx

interface ProgressUpdate {
  step: string;
  status: string;
  progress: number;
  message: string;
  data?: any;
}

export const ProgressTracker = ({ generationId }: { generationId: string }) => {
  const [updates, setUpdates] = useState<ProgressUpdate[]>([]);
  const [currentProgress, setCurrentProgress] = useState(0);

  useEffect(() => {
    const eventSource = new EventSource(
      `http://localhost:8000/api/master-mode/progress/${generationId}`,
      { withCredentials: true }
    );

    eventSource.onmessage = (event) => {
      const update: ProgressUpdate = JSON.parse(event.data);
      setUpdates(prev => [...prev, update]);
      setCurrentProgress(update.progress);
      
      // If complete, close connection
      if (update.step === 'complete') {
        eventSource.close();
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
    };

    return () => eventSource.close();
  }, [generationId]);

  return (
    <div className="progress-tracker">
      {/* Progress bar */}
      <div className="w-full bg-gray-200 rounded-full h-4">
        <div 
          className="bg-blue-600 h-4 rounded-full transition-all duration-500"
          style={{ width: `${currentProgress}%` }}
        />
      </div>
      
      {/* Step list */}
      <div className="mt-4 space-y-2">
        {updates.map((update, idx) => (
          <div key={idx} className="flex items-center gap-2">
            <StatusIcon status={update.status} />
            <span>{update.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
```

### 2. Video Player Component

```typescript
// frontend/src/components/master-mode/VideoPlayer.tsx

export const VideoPlayer = ({ videoPath, title }: { videoPath: string, title: string }) => {
  return (
    <div className="video-player">
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <video 
        controls 
        className="w-full rounded-lg shadow-lg"
        src={`http://localhost:8000${videoPath}`}
      >
        Your browser does not support the video tag.
      </video>
    </div>
  );
};
```

### 3. Updated MasterMode Component

```typescript
// frontend/src/routes/MasterMode.tsx (additions)

const [generationId, setGenerationId] = useState<string | null>(null);
const [sceneVideos, setSceneVideos] = useState<string[]>([]);
const [finalVideo, setFinalVideo] = useState<string | null>(null);

const handleSubmit = async (e: React.FormEvent) => {
  // ... existing code ...
  
  const response = await apiClient.post(...);
  
  setGenerationId(response.data.generation_id);
  setSceneVideos(response.data.scene_videos || []);
  setFinalVideo(response.data.final_video_path);
};

return (
  <div>
    {/* Existing form */}
    
    {/* Progress tracker */}
    {generationId && !finalVideo && (
      <ProgressTracker generationId={generationId} />
    )}
    
    {/* Scene videos */}
    {sceneVideos.length > 0 && (
      <div className="mt-8">
        <h2 className="text-2xl font-bold mb-4">Scene Videos</h2>
        <div className="grid grid-cols-2 gap-4">
          {sceneVideos.map((video, idx) => (
            <VideoPlayer 
              key={idx}
              videoPath={video}
              title={`Scene ${idx + 1}`}
            />
          ))}
        </div>
      </div>
    )}
    
    {/* Final video */}
    {finalVideo && (
      <div className="mt-8">
        <h2 className="text-2xl font-bold mb-4">Final Advertisement</h2>
        <VideoPlayer 
          videoPath={finalVideo}
          title="Complete Advertisement"
        />
      </div>
    )}
  </div>
);
```

## User Experience Flow

### What User Sees:

1. **Submits Form** → Gets `generation_id`
2. **Real-Time Progress**:
   ```
   [░░░░░░░░░░] 0%  Starting generation...
   [██░░░░░░░░] 10% Saved 2 reference images
   [████░░░░░░] 30% Story generated (score: 91/100)
   [██████░░░░] 55% Generated 4 scenes (cohesion: 85/100)
   [███████░░░] 65% Prepared 4 video generation parameter sets
   [████████░░] 70% Generating scene videos (may take several minutes)...
   [█████████░] 95% Videos generated and stitched successfully!
   [██████████] 100% Generation complete!
   ```

3. **Scene Videos Appear** (as they're generated):
   - Scene 1 video player appears
   - Scene 2 video player appears
   - Scene 3 video player appears
   - Scene 4 video player appears

4. **Final Video Appears**:
   - Large video player with complete advertisement
   - Download button
   - Share options

## Technical Details

### SSE vs WebSockets

**Why SSE?**
- Simpler implementation
- One-way communication (server → client)
- Automatic reconnection
- Works over HTTP
- No need for ws:// protocol

**SSE Format**:
```
data: {"step":"story","status":"in_progress","progress":15,"message":"Generating story..."}\n\n
data: {"step":"story","status":"completed","progress":30,"message":"Story generated!"}\n\n
```

### Video Serving

Videos are served as static files:
```
GET /temp/master_mode/{user_id}/{generation_id}/scene_videos/scene_01.mp4
GET /temp/master_mode/{user_id}/{generation_id}/final_video_20251120.mp4
```

Need to mount temp directory in FastAPI:
```python
from fastapi.staticfiles import StaticFiles
app.mount("/temp", StaticFiles(directory="temp"), name="temp")
```

### Progress Queue Cleanup

- Queue created when generation starts
- Queue deleted when generation completes
- Automatic cleanup on error
- Memory-efficient (one queue per active generation)

## Next Steps (Frontend Implementation)

1. **Create ProgressTracker Component**
   - Connect to SSE endpoint
   - Display progress bar
   - Show step-by-step updates
   - Handle errors and timeouts

2. **Create VideoPlayer Component**
   - HTML5 video element
   - Controls (play, pause, seek, volume)
   - Download button
   - Fullscreen support

3. **Update MasterMode Component**
   - Integrate ProgressTracker
   - Display scene videos grid
   - Display final video
   - Add download/share buttons

4. **Add Static File Serving**
   - Mount temp directory in backend
   - Ensure proper CORS headers for video files
   - Add authentication checks

## Files Created/Modified

**Backend**:
- ✅ `backend/app/api/routes/master_mode_progress.py` (NEW)
- ✅ `backend/app/api/routes/master_mode.py` (updated with progress)
- ✅ `backend/app/main.py` (register progress router)

**Frontend** (TO DO):
- [ ] `frontend/src/components/master-mode/ProgressTracker.tsx` (NEW)
- [ ] `frontend/src/components/master-mode/VideoPlayer.tsx` (NEW)
- [ ] `frontend/src/routes/MasterMode.tsx` (integrate components)

## Testing

### Backend SSE Test

```bash
# Start backend
uvicorn app.main:app --reload

# In another terminal, test SSE
curl -N http://localhost:8000/api/master-mode/progress/{generation_id}
```

### Frontend SSE Test

```javascript
const eventSource = new EventSource('http://localhost:8000/api/master-mode/progress/test-id', {
  withCredentials: true
});

eventSource.onmessage = (event) => {
  console.log('Progress update:', JSON.parse(event.data));
};
```

## Benefits

✅ **Real-Time Feedback** - User sees progress as it happens  
✅ **Better UX** - No more "loading..." black box  
✅ **Transparency** - User knows which step is running  
✅ **Video Playback** - Immediate review of individual scenes  
✅ **Final Preview** - See complete ad before downloading  
✅ **Error Visibility** - Know exactly where it failed  

The user now has complete visibility into the generation process from start to finish! 🎬✨


