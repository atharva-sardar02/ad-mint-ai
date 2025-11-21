# Master Mode - System Patterns

## Architecture Overview

Master Mode follows a simplified request-response pattern that integrates with the existing video generation pipeline.

```
User Input → Frontend Form → Backend API → Video Generation Pipeline → Result
```

## Component Structure

### Frontend Component

**Location**: `frontend/src/routes/MasterMode.tsx`

**Structure**:
- Single component with all form logic
- State management using React hooks
- Form validation before submission
- Image preview management
- Toast notifications for feedback

**Key Patterns**:
- Controlled components for all inputs
- File upload handling with preview URLs
- Client-side validation before API call
- Error state management

### Backend Integration (Planned)

**Location**: `backend/app/api/routes/master_mode.py` (to be created)

**Pattern**:
- FastAPI route handler
- Multipart form data parsing
- File upload handling
- Integration with existing `process_generation` function

## Data Flow

### Input Flow
```
User Form → Validation → FormData → API Request → Backend Processing
```

### Image Handling Flow
```
File Upload → Preview URL → Validation → FormData → Backend Storage → Pipeline
```

### Generation Flow
```
Master Mode Inputs → Parameter Mapping → Standard Pipeline → Video Output
```

## State Management Patterns

### Frontend State
- **Form State**: Controlled inputs (prompt, title, brandName)
- **Image State**: Array of objects with file and preview
- **Validation State**: Error messages per field
- **UI State**: Loading, toast notifications

### State Updates
- Real-time validation on input change
- Image preview on file selection
- Error clearing on correction
- Loading state during submission

## Validation Patterns

### Client-Side Validation
- **Prompt**: Required, min 10 characters
- **Images**: At least 1 required, max 3
- **File Types**: JPG, PNG only
- **File Sizes**: Max 10MB per image

### Server-Side Validation (Planned)
- Re-validate all client checks
- File content verification (not just extension)
- Security checks (malicious content scanning)
- Rate limiting

## Error Handling Patterns

### Client-Side Errors
- Field-level validation errors
- File upload errors
- Network errors
- Display via ErrorMessage component and toast

### Server-Side Errors (Planned)
- Validation errors → 400 Bad Request
- File too large → 413 Payload Too Large
- Authentication errors → 401 Unauthorized
- Server errors → 500 Internal Server Error

## Integration Patterns

### With Existing Pipeline

Master Mode maps to standard generation parameters:

```python
{
    "prompt": user_prompt,
    "title": user_title or None,
    "brand_name": user_brand_name or None,
    "image_path": first_reference_image,
    "use_llm": True,  # Always enabled
    "use_advanced_image_generation": True,  # Always enabled
    "preferred_model": "google/veo-3.1",  # Default
    "target_duration": 15,  # Default
    # Additional reference images handled separately
}
```

### With Authentication

- Uses existing authentication system
- Protected route requires valid token
- User context available for generation tracking

## File Handling Patterns

### Image Upload
1. User selects file
2. Client validates (type, size)
3. Create preview URL (URL.createObjectURL)
4. Store file in component state
5. On submit: add to FormData
6. Backend receives and saves to temp storage
7. Process through pipeline
8. Clean up temp files after processing

### Preview Management
- Create preview URL when file selected
- Revoke URL when file removed or component unmounts
- Prevent memory leaks with proper cleanup

## UI/UX Patterns

### Form Layout
- Centered card design
- Responsive grid for images
- Clear labels and help text
- Visual feedback for all states

### Image Upload UI
- Drag-and-drop style upload area
- Preview with hover-to-remove
- Clear indication of required vs optional
- File type and size hints

### Feedback Patterns
- Real-time validation errors
- Toast notifications for actions
- Loading states during submission
- Success redirect to status page

## Security Patterns

### File Upload Security (Planned)
- MIME type validation (not just extension)
- File content scanning
- Size limits enforced
- Secure temp storage
- Cleanup after processing

### Input Sanitization
- Prompt text sanitization
- Brand name format validation
- Prevent injection attacks
- Rate limiting per user

## Performance Patterns

### Image Handling
- Preview URLs for instant feedback
- File size validation before upload
- Efficient FormData construction
- Background processing for generation

### API Design
- Async processing (return immediately)
- Background task for video generation
- Progress tracking via polling
- Efficient file storage

## Extension Patterns

### Future Enhancements
- Can add more fields without breaking existing flow
- Can add advanced options toggle (hidden by default)
- Can add template system
- Can add batch processing

### Maintainability
- Single component for easy updates
- Clear separation of concerns
- Well-documented code
- Follows existing project patterns


