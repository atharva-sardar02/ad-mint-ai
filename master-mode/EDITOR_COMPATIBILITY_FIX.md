# Editor Compatibility Fix for Master Mode Videos

**Date:** November 21, 2024  
**Issue:** Master Mode videos cannot be edited in the Editor, causing errors

## Problem

When clicking "Edit Video" on a Master Mode video:
1. ❌ Editor tries to load quality metrics (Master Mode doesn't use quality metrics)
2. ❌ Editor expects `clips` array (empty for Master Mode)
3. ❌ Editor expects scene planning data (Master Mode uses different pipeline)
4. ❌ Console errors: `clips: Array(0)`, "cannot play the video"

## Root Cause

Master Mode videos use a completely different generation pipeline:
- **Regular Pipeline:** Scene planning → Individual clips with quality metrics → Stitching
- **Master Mode Pipeline:** Story Director → Scene Writer → Scene Enhancer → Video generation → Stitching

The Editor is designed for the regular pipeline and expects:
- QualityMetric records in database
- Individual clip files with paths
- Scene planning metadata
- Clip-level quality scores

Master Mode doesn't generate any of these.

## Solution

Disable the "Edit Video" button for Master Mode videos since they're incompatible with the Editor.

### Implementation

#### 1. Add `framework` Field to API Response

**Backend Schema** (`backend/app/schemas/generation.py`):
```python
class GenerationListItem(BaseModel):
    ...
    framework: Optional[str] = Field(None, description="Framework used (e.g., 'PAS', 'BAB', 'AIDA', 'master_mode')")
```

**Backend API** (`backend/app/api/routes/generations.py`):
```python
GenerationListItem(
    ...
    framework=gen.framework,  # Added
)
```

#### 2. Conditionally Hide Edit Button

**Frontend** (`frontend/src/routes/VideoDetail.tsx`):
```typescript
{/* Edit button - only for non-master-mode videos */}
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

## User Experience

### Master Mode Videos

**Video Detail Page:**
```
┌────────────────────────────────────┐
│  [Video Player]                    │
│                                     │
│  Master Mode Video                 │
│  Status: Completed                 │
│                                     │
│  Actions:                          │
│  [View Storyboard] [Delete Video]  │  ← No "Edit Video" button
└────────────────────────────────────┘
```

### Regular Videos

**Video Detail Page:**
```
┌────────────────────────────────────┐
│  [Video Player]                    │
│                                     │
│  My Advertisement                  │
│  Status: Completed                 │
│                                     │
│  Actions:                          │
│  [View Storyboard] [Edit Video] [Delete Video]  │  ← Edit button visible
└────────────────────────────────────┘
```

## Technical Details

### Framework Values

| Framework | Description | Editor Compatible? |
|-----------|-------------|-------------------|
| `null` | Legacy videos | ✅ Yes |
| `"PAS"` | Problem-Agitate-Solution | ✅ Yes |
| `"BAB"` | Before-After-Bridge | ✅ Yes |
| `"AIDA"` | Attention-Interest-Desire-Action | ✅ Yes |
| `"master_mode"` | Master Mode pipeline | ❌ No |

### Why Master Mode Can't Be Edited

**Missing Data:**
1. No QualityMetric records
2. No individual scene clip files in expected format
3. No scene planning metadata
4. Different file structure (`/temp/master_mode/` vs `/output/`)

**Different Pipeline:**
- Master Mode generates scenes using AI agents (Director, Critic, Writer, etc.)
- Scenes are generated as complete prompts, not clip-by-clip
- Video generation uses Veo 3.1 directly
- No quality scoring per clip

**Incompatible Features:**
- Editor relies on clip-level manipulation
- Editor uses quality metrics for scoring
- Editor expects specific clip naming/numbering
- Editor timeline based on scene planning structure

## Future Enhancements

### Phase 1: Master Mode Viewer (Not Editor)

Create a specialized viewer for Master Mode videos:
- View LLM conversation history
- See story and scene descriptions
- View individual scene videos
- Download scene videos separately
- View brand name and references used

### Phase 2: Limited Editing

Add basic editing capabilities for Master Mode:
- Trim individual scenes
- Reorder scenes
- Adjust transitions
- Add text overlays
- Change music

### Phase 3: Full Editor Integration

Make Master Mode fully compatible:
- Generate quality metrics post-facto
- Store clips in editor-compatible format
- Support full editor features
- Allow regenerating individual scenes

## Testing

### Test Case 1: Master Mode Video

1. Generate Master Mode video
2. Go to Video Detail page
3. **Expected:** No "Edit Video" button
4. **Expected:** "View Storyboard" and "Delete Video" buttons visible

### Test Case 2: Regular Video

1. Generate regular video (PAS/BAB/AIDA)
2. Go to Video Detail page
3. **Expected:** "Edit Video" button visible
4. **Expected:** All buttons work correctly

### Test Case 3: Framework Field

```python
# API test
response = await client.get(f"/api/generations/{generation_id}")
assert "framework" in response.json()
assert response.json()["framework"] in [None, "PAS", "BAB", "AIDA", "master_mode"]
```

## Files Changed

1. ✅ `backend/app/schemas/generation.py`
   - Added `framework` field to `GenerationListItem`

2. ✅ `backend/app/api/routes/generations.py`
   - Added `framework=gen.framework` to both list and detail responses

3. ✅ `frontend/src/routes/VideoDetail.tsx`
   - Conditional rendering: hide Edit button if `framework === "master_mode"`

4. ✅ Created `master-mode/EDITOR_COMPATIBILITY_FIX.md` - Full documentation

## Migration Notes

### Existing Videos

- Regular videos: `framework` will be `null` or one of `["PAS", "BAB", "AIDA"]`
- Editor will work fine (`framework !== "master_mode"` is true when framework is null)
- No database migration needed

### New Videos

- Master Mode: `framework="master_mode"` set during generation
- Regular pipeline: `framework` set based on user selection
- Editor button properly hidden/shown

## Known Limitations

### Master Mode Videos

❌ Cannot be edited in Editor  
✅ Can be viewed and downloaded  
✅ Can be deleted  
✅ Individual scenes accessible via `temp_clip_paths`  
⚠️ No thumbnail generation  
⚠️ No quality metrics  

### Workaround for Editing

If user wants to edit Master Mode video:
1. Download individual scene videos from `temp_clip_paths`
2. Import into external video editor
3. Edit and export
4. Upload as new video

---

**Status:** ✅ Fix Complete  
**Impact:** Master Mode videos no longer show broken Edit button  
**User Experience:** Clear separation between editable and view-only videos  
**Future Work:** Consider Master Mode viewer with LLM conversation display

