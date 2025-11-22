# Master Mode - Project Brief

## Overview

Master Mode is a simplified video generation interface designed to streamline the video creation process for users who want quick, high-quality results without navigating complex settings and configurations.

## Core Purpose

Master Mode exists to:
- **Simplify the workflow**: Provide a focused, minimal interface that collects only essential inputs
- **Reduce cognitive load**: Eliminate decision fatigue from advanced settings
- **Enable faster creation**: Allow users to generate videos quickly with minimal configuration
- **Maintain quality**: Ensure high-quality output despite simplified inputs

## Key Requirements

### User Inputs (Required)
1. **Video Prompt** - Minimum 10 characters, describes the desired video
2. **At least 1 Reference Image** - JPG or PNG, max 10MB per image

### User Inputs (Optional)
1. **Video Title** - Maximum 200 characters, helps identify videos later
2. **Brand Name** - Maximum 50 characters, used for branding

### Technical Requirements
- Support up to 3 reference images
- File validation (type and size)
- Real-time form validation
- Responsive design (mobile and desktop)
- Protected route (requires authentication)
- Integration with existing video generation pipeline

## Success Criteria

1. **User Experience**
   - Users can generate videos in under 2 minutes
   - Form is intuitive and requires no training
   - Clear validation feedback
   - Smooth image upload experience

2. **Technical**
   - Form submission integrates with backend API
   - Images are properly validated and stored
   - Generation pipeline processes Master Mode requests correctly
   - Error handling provides clear user feedback

3. **Quality**
   - Generated videos maintain quality standards
   - Reference images are used effectively
   - Brand information is properly applied

## Scope

### In Scope
- Simple form interface with 4 input fields
- Image upload with preview
- Form validation
- Backend API integration
- Integration with existing video generation pipeline

### Out of Scope (For Now)
- Advanced settings or customization
- Image editing capabilities
- Draft saving
- Template system
- Batch generation

## Constraints

- Must work with existing authentication system
- Must integrate with current video generation pipeline
- Must maintain consistency with existing UI/UX patterns
- File size limits: 10MB per image
- Supported formats: JPG, PNG only

## Timeline

- **Phase 1 (Complete)**: UI implementation
- **Phase 2 (Pending)**: Backend API integration
- **Phase 3 (Future)**: Enhancements and optimizations


