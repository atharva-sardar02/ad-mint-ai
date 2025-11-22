# Epic 9 Alignment Analysis: Storyboard Foundation Review

**Date:** 2025-11-17  
**Author:** PM Agent (BMad)  
**Status:** ✅ Epic 9 is ALIGNED with Storyboard Foundation

---

## Executive Summary

Epic 9 stories are **well-aligned** with the current storyboard implementation (Epic 8.3/8.4). The storyboard system outputs all required data structures, file paths, and metadata that Epic 9 needs. However, there is **one enhancement opportunity**: Epic 9.1 should explicitly use the unified narrative document for context, which is available but not explicitly required in the current story definition.

**Key Findings:**
- ✅ **Story 9.1**: Fully aligned - all required storyboard data available
- ✅ **Story 9.2**: Fully aligned - all required storyboard data available  
- ⚠️ **Enhancement Opportunity**: Unified narrative document available but not explicitly required in Epic 9.1 AC

---

## Storyboard Foundation (Epic 8.3/8.4) - Current State

### What We're Outputting

**1. Image Files (PNG):**
- `clip_001_start.png`, `clip_001_end.png`
- `clip_002_start.png`, `clip_002_end.png`
- ... (up to 10 clips)
- ✅ Visual coherence maintained via sequential image-to-image generation

**2. Storyboard Metadata JSON:**
- Complete clip information (number, description, prompts)
- Motion descriptions for each clip
- Camera metadata (movement, shot size, perspective, lens)
- Start/end frame file paths (absolute paths)
- Scene dependencies and narrative flow
- ✅ **Unified narrative document reference** (`unified_narrative_path`)

**3. Unified Narrative Document:**
- Overall story narrative
- Emotional arc per scene
- Visual progression strategy
- ✅ Available for Epic 9.1 context (via `unified_narrative_path` in metadata)

---

## Story 9.1: Video Prompt Enhancement - Alignment Analysis

### Acceptance Criteria #4: Storyboard JSON Processing

**Epic 9.1 Requirement:**
```
Given I have a storyboard JSON file from Story 8.3 (storyboard_metadata.json)
When I run python enhance_video_prompt.py --storyboard storyboard_metadata.json
Then the CLI tool:
- Loads the storyboard JSON file and parses clip information
- For each clip in the storyboard:
  - Extracts the clip's motion_description as the base motion prompt ✅
  - Extracts camera metadata: camera_movement, shot_size, perspective, lens_type ✅
  - Uses start/end frame paths as context ✅
  - Enhances the motion prompt using two-agent feedback loop
```

**Storyboard Output Verification:**

| Required Field | Storyboard JSON Location | Status |
|---------------|-------------------------|--------|
| `motion_description` per clip | `clips[].motion_description` | ✅ Available |
| `camera_movement` | `clips[].camera_movement` | ✅ Available |
| `shot_size` | `clips[].shot_size` | ✅ Available |
| `perspective` | `clips[].perspective` | ✅ Available |
| `lens_type` | `clips[].lens_type` | ✅ Available |
| `start_frame_path` | `clips[].start_frame_path` | ✅ Available (absolute paths) |
| `end_frame_path` | `clips[].end_frame_path` | ✅ Available (absolute paths) |
| Storyboard JSON structure | `storyboard_metadata.json` | ✅ Valid JSON structure |

**✅ VERDICT: Story 9.1 AC #4 is FULLY ALIGNED**

### ✅ Unified Narrative Context - NOW REQUIRED

**Status: UPDATED - Now Explicitly Required**

**Epic 8.4 AC #4 Explicitly States:**
> "Given the unified narrative document exists, When Epic 9 video generation processes the storyboard, Then video generation can use the narrative document to:
> - Guide video prompt enhancement with narrative context
> - Ensure video clips maintain story coherence
> - Apply consistent emotional tone across scenes
> - Maintain visual progression throughout the video
> - Create smooth narrative transitions between clips"

**Epic 9.1 Story Status - UPDATED:**
- ✅ Story 9.1 AC #4 **NOW EXPLICITLY REQUIRES** loading and using unified narrative document
- ✅ Narrative context is **required** when processing storyboards (building upon Epic 8.4)
- ✅ Agent 1 (Video Director) must use narrative context (emotional arc, visual progression, scene connections)
- ✅ Agent 2 (Prompt Engineer) validates narrative coherence in enhanced prompts
- ✅ Two-agent feedback loop per clip with narrative context integration

**Implementation Requirements:**
- Load unified narrative document from `unified_narrative_path` in storyboard metadata
- Pass narrative context to two-agent enhancement loop for each clip
- Ensure motion prompts maintain story coherence with overall narrative
- Follow emotional arc progression from narrative
- Apply consistent visual progression strategy

---

## Story 9.2: Video Generation - Alignment Analysis

### Acceptance Criteria: Storyboard Mode Support

**Epic 9.2 Requirement:**
```
Given I have:
- Storyboard start/end frames (from Story 8.3)
When I run python generate_videos.py ... --storyboard path/to/storyboard.json
Then the CLI tool:
- For image-to-video: Calls an image-to-video model with hero frame + motion prompt
- Supports storyboard mode: --storyboard path/to/storyboard.json
```

**Storyboard Output Verification:**

| Required Field | Storyboard Output | Status |
|---------------|-------------------|--------|
| Start frame images | `clip_XXX_start.png` (PNG files) | ✅ Available |
| End frame images | `clip_XXX_end.png` (PNG files) | ✅ Available |
| Frame file paths | `clips[].start_frame_path`, `clips[].end_frame_path` | ✅ Available (absolute paths) |
| Motion prompts | `clips[].motion_description` (base) | ✅ Available |
| Enhanced motion prompts | Will be generated by Story 9.1 | ✅ Will be available |
| Storyboard JSON | `storyboard_metadata.json` | ✅ Available |

**✅ VERDICT: Story 9.2 is FULLY ALIGNED**

---

## Data Completeness Checklist

### Required for Epic 9.1 ✅

- [x] Motion descriptions per clip (`clips[].motion_description`)
- [x] Camera metadata (movement, shot size, perspective, lens) (`clips[]` and `shot_list[]`)
- [x] Start/end frame file paths (`clips[].start_frame_path/end_frame_path`)
- [x] Clip numbers and ordering (`clips[].clip_number`)
- [x] Storyboard metadata JSON structure (valid JSON)
- [x] **BONUS**: Unified narrative path (`unified_narrative_path`) - available but not required
- [x] **BONUS**: Narrative summary (`narrative_summary`) - available but not required

### Required for Epic 9.2 ✅

- [x] Start frame images (PNG files) (`clip_XXX_start.png`)
- [x] End frame images (PNG files) (`clip_XXX_end.png`)
- [x] File paths to images (absolute paths in JSON)
- [x] Aspect ratio information (`aspect_ratio` field)
- [x] Clip sequence information (`clips[]` array with `clip_number`)

### Nice-to-Have (Available) ✅

- [x] Scene dependencies (`scene_dependencies[]`)
- [x] Narrative flow description (`narrative_flow`)
- [x] Consistency groupings (`consistency_groupings[]`)
- [x] Shot list summary (`shot_list[]`)
- [x] Original prompt reference (`prompt` field)
- [x] Framework information (`framework` field)
- [x] **Unified narrative document** (markdown + JSON) - available for context

---

## Integration Code Examples

### Story 9.1: Loading Storyboard for Motion Prompt Enhancement

```python
# Epic 9.1 can load storyboard JSON:
import json
from pathlib import Path

storyboard_path = Path("output/storyboards/20251117_201652/storyboard_metadata.json")
with open(storyboard_path) as f:
    storyboard = json.load(f)

# Access unified narrative (if needed):
unified_narrative_path = storyboard.get("unified_narrative_path")
if unified_narrative_path:
    with open(unified_narrative_path) as f:
        narrative = f.read()  # or parse JSON if using .json version

# For each clip:
for clip in storyboard["clips"]:
    motion_prompt = clip["motion_description"]  # ✅ Available
    camera_metadata = {
        "movement": clip["camera_movement"],
        "shot_size": clip["shot_size"],
        "perspective": clip["perspective"],
        "lens_type": clip["lens_type"]
    }  # ✅ All available
    
    # Enhance motion prompt using two-agent loop
    enhanced_motion = enhance_video_prompt(
        motion_prompt,
        camera_metadata,
        start_frame=clip["start_frame_path"],  # ✅ Available
        end_frame=clip["end_frame_path"],  # ✅ Available
        narrative_context=narrative  # ⚠️ Available but not required in current AC
    )
```

### Story 9.2: Using Storyboard Frames for Video Generation

```python
# Epic 9.2 can use storyboard frames:
for clip in storyboard["clips"]:
    # Image-to-video generation
    video = generate_video(
        start_frame=clip["start_frame_path"],  # ✅ Available
        end_frame=clip["end_frame_path"],  # ✅ Available
        motion_prompt=enhanced_motion_prompt,  # From 9.1
        mode="image-to-video"
    )
```

---

## Recommendations

### 1. ✅ **UPDATED** - Epic 9 is Ready to Build with Narrative Integration

The storyboard foundation provides all required data structures. Epic 9 can start development immediately.

**Key Updates Made:**
- ✅ Story 9.1 AC #4 **NOW EXPLICITLY REQUIRES** unified narrative document usage
- ✅ Two-agent feedback loop per clip is confirmed and documented
- ✅ Narrative context integration is now a required part of storyboard processing
- ✅ Prerequisites updated to include Story 8.4 (Unified Narrative Generation)

### 2. ✅ **TWO-AGENT APPROACH CONFIRMED**

**Per-Clip Enhancement Process:**
- **Agent 1 (Video Director)**: Enhances motion description with:
  - Detailed camera movement specifications
  - Motion intensity and style
  - Frame rate considerations
  - Temporal continuity hints
  - **Narrative context integration** (emotional arc, visual progression, scene connections from unified narrative)
  
- **Agent 2 (Prompt Engineer)**: Critiques and scores the enhanced motion prompt
  - Validates narrative coherence
  - Scores on 6 dimensions (Completeness, Specificity, Professionalism, Cinematography, Temporal Coherence, Brand Alignment)
  
- **Iterative Loop**: Max 3 rounds until score threshold met or convergence detected
- **Per Clip**: Each clip in the storyboard gets its own two-agent enhancement loop with narrative context

### 3. ✅ **VERIFICATION COMPLETE** - Data Completeness

All required fields are present in storyboard output:
- ✅ Motion descriptions
- ✅ Camera metadata
- ✅ Frame file paths
- ✅ Clip ordering
- ✅ Narrative context (available)

---

## Conclusion

**✅ Epic 9 is FULLY ALIGNED with the storyboard foundation.**

**Key Strengths:**
- Complete metadata structure with all required fields
- All file paths accessible (absolute paths)
- Motion descriptions included for each clip
- Camera metadata comprehensive
- Narrative context available (bonus feature)
- Visual coherence maintained (sequential generation working)

**Enhancement Opportunity:**
- Consider explicitly requiring unified narrative usage in Story 9.1 AC #4 to ensure narrative coherence (as intended by Epic 8.4)

**Ready to proceed with Epic 9 development!** 🚀

---

## References

- **Storyboard Output Review**: `docs/sprint-artifacts/storyboard-output-review-for-epic9.md`
- **Epic 8.4 Story**: `docs/epics.md#Story-8.4` (Unified Narrative Generation)
- **Epic 9.1 Story**: `docs/epics.md#Story-9.1` (Video Prompt Enhancement)
- **Epic 9.2 Story**: `docs/epics.md#Story-9.2` (Video Generation)
- **Epic 9 Tech Spec**: `docs/sprint-artifacts/tech-spec-epic-9.md`
- **Storyboard Service**: `backend/app/services/pipeline/storyboard_service.py`
- **Storyboard Metadata Examples**: `backend/output/storyboards/*/storyboard_metadata.json`

