# Master Mode Documentation

## Overview

Master Mode is a simplified video generation interface designed to streamline the video creation process. It provides a clean, focused UI that collects essential inputs from users without overwhelming them with advanced settings.

## Purpose

Master Mode was created to:
- Simplify the video generation workflow
- Reduce complexity for users who want quick results
- Provide a focused interface for essential inputs only
- Enable faster video creation with minimal configuration

## Features

### Input Fields

1. **Video Title** (Optional)
   - A descriptive name for the video
   - Maximum length: 200 characters
   - Helps users identify their videos later

2. **Brand Name** (Optional)
   - The brand name associated with the video
   - Maximum length: 50 characters
   - Used for branding and identification

3. **Video Prompt** (Required)
   - The main description/prompt for video generation
   - Minimum length: 10 characters
   - This is the core input that drives video generation

4. **Reference Images** (Required - At least 1)
   - Up to 3 reference images can be uploaded
   - Supported formats: JPG, PNG
   - Maximum file size: 10MB per image
   - **Images are analyzed by Vision API**: The Story Director can see the actual person, product, or scene
   - **Exact descriptions**: Stories describe the actual appearance from images, not generic placeholders
   - Images guide visual consistency throughout the video generation process

## User Interface

### Layout

The Master Mode interface features:
- Clean, centered layout with maximum width of 4xl
- Card-based design with shadow and rounded corners
- Responsive grid for reference image uploads (1 column on mobile, 3 columns on desktop)
- Image preview with hover-to-remove functionality
- Real-time validation feedback

### Image Upload

Each reference image slot provides:
- Drag-and-drop style upload area
- Image preview once uploaded
- Remove button (appears on hover)
- File type and size validation
- Visual feedback for upload states

## Technical Implementation

### Component Location

- **Frontend Component**: `frontend/src/routes/MasterMode.tsx`
- **Route**: `/master-mode`
- **Protected Route**: Yes (requires authentication)

### State Management

The component manages:
- Form input states (prompt, title, brandName)
- Reference images array (up to 3 images with file and preview)
- Validation errors
- Loading state
- Toast notifications

### Validation

- **Prompt**: Required, minimum 10 characters
- **Reference Images**: At least 1 image required
- **File Types**: Only JPG and PNG allowed
- **File Size**: Maximum 10MB per image

### API Integration

**Status**: ✅ **Full Pipeline Complete** - Story, Scenes, Video Generation & Stitching

The Master Mode now includes:
1. ✅ Backend API endpoint `/api/master-mode/generate-story`
2. ✅ Two-agent story generation system (Story Director + Story Critic)
3. ✅ Three-agent scene generation system (Scene Writer + Scene Critic + Scene Cohesor)
4. ✅ **Vision API integration** - Story Director can see reference images
5. ✅ Iterative story refinement with conversation history
6. ✅ Sequential scene generation with cohesion checks
7. ✅ Frontend display of story and scene agent conversations
8. ✅ **Video generation** - Parallel Veo 3.1 generation for all scenes
9. ✅ **Custom video stitcher** - Purpose-built Master Mode stitcher with 3 transition types
10. ✅ **Real-time progress** - SSE for live updates and LLM conversation streaming
11. ✅ **Video playback** - Players for individual clips and final stitched video

### Video Generation & Stitching

**Custom Master Mode Stitcher**:
- **Clean Implementation**: ~300 lines vs 500+ in old pipeline
- **3 Transition Types**: `cut` (0.0s), `crossfade` (0.5s), `fade` (0.8s)
- **Context Manager**: Automatic resource cleanup
- **High Quality**: 5000k bitrate, 24fps standard
- **Smart Transitions**: Automatically selected based on Scene Cohesor scores
- **Better Logging**: Detailed progress with emojis

**File**: `backend/app/services/master_mode/video_stitcher.py`

**Why Custom Stitcher?**
- Old pipeline stitcher had 6+ complex transitions (wipe, flash, zoom_blur, glitch)
- Master Mode only needs simple, professional transitions
- Easier to maintain and extend
- Purpose-built for advertisement video workflow

### Agent Conversation Display

When users click "Generate", they can see:

**Story Generation:**
- **Vision-Enhanced Story**: The Story Director analyzes uploaded reference images using OpenAI Vision API
- **Exact Visual Descriptions**: Stories describe the actual person, product, or scene from the images
- **Final Story**: The complete Markdown-formatted story with forensic-level detail
- **Approval Status**: Whether the story was approved or needs revision
- **Quality Score**: Overall score (0-100) from the Story Critic
- **Iteration Count**: Number of refinement rounds
- **Full Conversation**: Complete back-and-forth between agents:
  - Story Director's drafts for each iteration (with image analysis)
  - Story Critic's critiques with scores, strengths, improvements, and priority fixes
  - Visual distinction between agent outputs (blue for Director, purple for Critic)

**Scene Generation:**
- **Scene Overview**: Total scenes, cohesion score, total iterations
- **Individual Scenes**: Each scene with:
  - Detailed 150-250 word visual descriptions
  - Cinematography specs (camera, angles, lenses)
  - Start and end frame descriptions
  - Approval status and quality score
  - Number of iterations per scene
- **Cohesion Analysis**: 
  - Pairwise transition scores (Scene 1→2, 2→3, etc.)
  - Issues and recommendations for each transition
  - Global cohesion issues across all scenes
- **Full Scene Conversation**: Complete back-and-forth between three agents:
  - Scene Writer's detailed scene descriptions (blue)
  - Scene Critic's evaluations with 6-criteria scoring (purple)
  - Scene Cohesor's cohesion feedback and transition analysis (green)

## Future Enhancements

1. **Backend Integration**
   - Create `/api/master-mode/generate` endpoint
   - Handle file uploads
   - Process through video generation pipeline

2. **Progress Tracking**
   - Show generation progress
   - Redirect to generation status page
   - Display real-time updates

3. **Image Preview Enhancement**
   - Full-screen image viewer
   - Image editing capabilities
   - Image reordering

4. **Validation Improvements**
   - Image dimension validation
   - Aspect ratio recommendations
   - Image quality checks

5. **User Experience**
   - Save draft functionality
   - Recent prompts history
   - Template suggestions

## Usage Flow

1. User navigates to `/master-mode`
2. User fills in:
   - Video title (optional)
   - Brand name (optional)
   - Video prompt (required)
   - At least 1 reference image (required)
3. User clicks "Generate Video"
4. Form validates inputs
5. Submission sent to backend (when implemented)
6. User redirected to generation status page

## Design Decisions

### Why 3 Reference Images?

- Provides flexibility for complex scenarios (e.g., person + product + scene)
- Not overwhelming (keeps UI clean)
- Matches common use cases (subject, product, environment)

### Why Simplified Interface?

- Reduces cognitive load
- Faster workflow for common use cases
- Can be extended later with advanced options

### Why Optional Title and Brand Name?

- Allows quick generation without metadata
- System can extract brand from prompt if needed
- Users can add context when available

## Related Files

- `frontend/src/routes/MasterMode.tsx` - Main component
- `frontend/src/App.tsx` - Route configuration
- `frontend/src/components/layout/Navbar.tsx` - Navigation link

## Status

**Current Status**: ✅ **FULLY OPERATIONAL** - Complete End-to-End Pipeline

The Master Mode system is fully implemented and operational:

### ✅ Core Features (Complete)
- **UI Layer**: Form inputs, image upload, validation, responsive design
- **Vision API**: Story Director analyzes actual person/product appearance from reference images
- **Story Generation**: Two-agent system (Director + Critic) with vision capabilities
- **Scene Generation**: Three-agent system (Writer + Critic + Cohesor) with detailed specifications
- **Scene Enhancement**: LLM-based expansion from 150-250 to 300-500 words with cinema-grade specs
- **Video Generation**: Veo 3.1 R2V mode with reference images and enhanced prompts
- **Video Stitching**: Custom Master Mode stitcher with 3 transition types
- **Real-Time Progress**: SSE-based progress tracking and LLM conversation streaming
- **Video Playback**: Players for individual clips and final stitched video

### ✅ Quality Features (Complete)
- **Ultra-Realistic Prompts**: 300-500 word prompts with forensic detail
- **Cinema-Grade Specs**: Camera/lens/lighting specifications (Arri Alexa 65, Zeiss lenses)
- **R2V Mode**: Reference images for perfect subject consistency
- **1080p Resolution**: High-quality output at 16:9 aspect ratio
- **Professional Stitching**: Smooth transitions with high bitrate (5000k)
- **Negative Prompts**: Comprehensive exclusion list for realism

### ✅ User Journey (Complete)
1. Upload reference images (person, product, scene)
2. Story Director analyzes images and describes exact appearance
3. Story generation with iterative refinement (forensic-level detail)
4. Scene generation with cohesion checks and detailed specifications
5. Scene enhancement with LLM expansion (300-500 words)
6. Parallel video generation using Veo 3.1 R2V mode
7. Real-time progress tracking and LLM conversation display
8. Video stitching with automatic transition selection
9. Final video playback with high-quality output

### 📍 File Locations
- **Final Video**: `backend/temp/master_mode/{user_id}/{generation_id}/final_video_YYYYMMDD_HHMMSS.mp4`
- **Scene Videos**: `backend/temp/master_mode/{user_id}/{generation_id}/scene_videos/temp_scene_{N}/`
- **Reference Images**: `backend/temp/master_mode/{user_id}/{generation_id}/reference_{N}_{filename}`

### 🔧 Recent Bug Fixes
- ✅ Fixed `scene_content` variable name error in scene-to-video conversion
- ✅ Fixed logging format error with cost parameter (string vs float handling)
- ✅ Video generation and stitching now working correctly

### 🚀 Next Steps
- Testing and quality validation
- Performance optimization
- User feedback collection
- Fine-tuning enhancement prompts

