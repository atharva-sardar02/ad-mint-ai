# Feature: Sora Prompt and Reference Image Support

## Overview
This PR adds comprehensive support for OpenAI's Sora video generation model, including optimized prompt assembly and reference image integration. The implementation introduces a new scene assembler service that converts compact JSON fragments into Sora-compatible prompts, and enhances the video generation pipeline to support reference images for improved visual consistency.

## Key Changes

### 🎬 New Features

#### 1. Scene Assembler Service (`scene_assembler.py`)
- **Purpose**: Converts compact JSON fragments into optimized Sora video prompts
- **Key Features**:
  - Strict shot language enforcement (single 4-second shots)
  - Camera movement control (static, push-in, glide, slow pan)
  - Reference image awareness (adjusts prompts for stability when reference images are used)
  - Product usage description (behavior-focused, not appearance-focused)
  - Output constraints: 1-2 sentences, 20-45 words max
  - Post-processing to ensure Sora-compatible format

#### 2. Reference Image Support
- Integration with Sora-2 API for reference image-based generation
- Reference image path handling throughout the pipeline
- Automatic prompt adjustments when reference images are present

#### 3. Enhanced LLM Pipeline
- Updated LLM enhancement service to work with new scene assembler
- Compact fragment format (3-7 word fragments) for better prompt assembly
- Improved prompt structure for Sora compatibility

### 🔧 Pipeline Improvements

#### Video Generation Service
- Sora-2 API integration
- Reference image support in video generation calls
- Enhanced error handling and fallback mechanisms
- Improved prompt assembly workflow

#### Audio Service
- Enhanced audio processing for multi-scene videos
- Better synchronization with video generation pipeline

#### Scene Planning
- Updated to work with new scene assembler format
- Improved fragment generation for Sora prompts

### 📝 API & Schema Updates

#### Generation Routes
- Updated `/api/generate` endpoint to support reference images
- Enhanced request/response handling for Sora generation
- Improved error messages and validation

#### Schemas
- Updated `GenerateRequest` schema with Sora-specific options
- Enhanced `StatusResponse` with additional metadata
- Support for reference image tracking

### 📚 Documentation & Testing

- Added troubleshooting guide for network errors
- Created test script for Sora prompt validation (`test_sora_prompt.py`)
- Updated parallel processing documentation
- Enhanced test coverage for scene planning

### 🛠️ Infrastructure

- Updated migrations script
- Enhanced logging configuration
- Improved configuration management for Sora API

## Technical Details

### Scene Assembler Architecture
The scene assembler uses a two-stage process:
1. **Fragment Sanitization**: Clamps fragment fields into Sora-friendly ranges
2. **Prompt Assembly**: Converts sanitized fragments into natural prose using GPT-4-turbo

### Reference Image Flow
1. Reference image uploaded/stored
2. Image path passed through pipeline
3. Scene assembler adjusts prompts for stability
4. Sora-2 API called with reference image
5. Generated video maintains visual consistency

## Testing

- ✅ Unit tests updated for scene planning
- ✅ Integration tests for Sora prompt generation
- ✅ Manual testing with reference images
- ✅ Network error handling validated

## Breaking Changes

None - this is a feature addition that maintains backward compatibility.

## Migration Notes

- No database migrations required
- Existing generations continue to work
- New Sora features are opt-in via API parameters

## Related Issues

- Implements Sora-2 integration
- Adds reference image support for visual consistency
- Improves prompt quality for video generation

## Checklist

- [x] Code follows project style guidelines
- [x] Tests added/updated
- [x] Documentation updated
- [x] No breaking changes
- [x] Backward compatible
- [x] Error handling implemented
- [x] Logging enhanced

## Files Changed

- **New Files**: 
  - `backend/app/services/pipeline/scene_assembler.py`
  - `docs/TROUBLESHOOTING_NETWORK_ERRORS.md`
  - `test_sora_prompt.py`

- **Modified Files**:
  - `backend/app/api/routes/generations.py`
  - `backend/app/schemas/generation.py`
  - `backend/app/services/pipeline/audio.py`
  - `backend/app/services/pipeline/llm_enhancement.py`
  - `backend/app/services/pipeline/scene_planning.py`
  - `backend/app/services/pipeline/video_generation.py`
  - `backend/run_migrations.py`

## Next Steps

- Monitor Sora API usage and costs
- Gather feedback on prompt quality
- Consider additional camera movement options
- Evaluate performance optimizations

