# Master Mode - Technical Context

## Technologies Used

### Frontend
- **React** with TypeScript
- **React Router** for routing
- **Tailwind CSS** for styling
- **File API** for image handling
- **FormData API** for multipart uploads

### Backend (Planned)
- **FastAPI** for API endpoints
- **Python** for backend logic
- **OpenAI GPT-4o** (text and **vision** for story generation)
- **OpenAI GPT-4o** (text-only for scene generation and critiques)
- **Image Processing**: Base64 encoding for vision API
- **Existing video generation pipeline** for processing
- **File storage** for temporary image storage in `temp/master_mode/`

## Development Setup

### Frontend Component
- **Location**: `frontend/src/routes/MasterMode.tsx`
- **Dependencies**: Uses existing UI components (Button, Textarea, ErrorMessage, Toast)
- **Routing**: Configured in `frontend/src/App.tsx`
- **Navigation**: Added to `frontend/src/components/layout/Navbar.tsx`

### Backend (To Be Created)
- **Route File**: `backend/app/api/routes/master_mode.py`
- **Integration**: Will use existing `process_generation` function
- **File Handling**: Will use existing temp storage patterns

## Technical Constraints

### File Upload Constraints
- **Max File Size**: 10MB per image
- **Supported Formats**: JPG, JPEG, PNG
- **Max Images**: 3 reference images
- **Validation**: Client-side and server-side

### Form Constraints
- **Prompt**: Minimum 10 characters, no maximum (backend may have limit)
- **Title**: Maximum 200 characters
- **Brand Name**: Maximum 50 characters
- **All fields**: UTF-8 encoding

### Browser Support
- Modern browsers with File API support
- FormData API support required
- URL.createObjectURL support for previews

## Dependencies

### Frontend Dependencies
- React (existing)
- React Router (existing)
- UI components (existing)
- No new dependencies required

### Backend Dependencies (Planned)
- FastAPI (existing)
- File handling utilities (existing)
- Video generation pipeline (existing)
- No new dependencies required

## API Specifications

### Endpoint (To Be Created)
```
POST /api/master-mode/generate
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

### Request Format
- Multipart form data
- Fields: prompt, title, brand_name, reference_image_1, reference_image_2, reference_image_3
- Files: Up to 3 image files

### Response Format
```json
{
  "generation_id": "uuid-string",
  "status": "processing",
  "message": "Video generation started"
}
```

## Integration Points

### With Authentication
- Uses existing auth store (`useAuthStore`)
- Protected route requires authentication
- Token included in API requests

### With Video Generation Pipeline
- Maps inputs to standard generation parameters
- Uses existing `process_generation` function
- Follows existing generation flow
- Returns standard generation_id

### With UI Components
- Reuses existing Button, Textarea, ErrorMessage, Toast
- Follows existing styling patterns
- Consistent with Dashboard UI

## File Handling Details

### Image Upload Process
1. User selects file via `<input type="file">`
2. File validated (type, size) client-side
3. Preview URL created: `URL.createObjectURL(file)`
4. File stored in component state
5. On submit: File added to FormData
6. FormData sent to backend
7. Backend saves to temp storage
8. Images processed through pipeline
9. Temp files cleaned up after processing

### Preview URL Management
- Created when file selected
- Revoked when file removed
- Revoked on component unmount (cleanup)
- Prevents memory leaks

## Validation Implementation

### Client-Side Validation
```typescript
// Prompt validation
if (!prompt.trim() || prompt.trim().length < 10) {
  errors.prompt = "Prompt must be at least 10 characters";
}

// Image validation
const hasAtLeastOneImage = referenceImages.some(img => img.file !== null);
if (!hasAtLeastOneImage) {
  errors.referenceImages = "At least one reference image is required";
}

// File type validation
if (!["image/jpeg", "image/jpg", "image/png"].includes(file.type)) {
  errors.referenceImages = "Only JPG and PNG images are allowed";
}

// File size validation
if (file.size > 10 * 1024 * 1024) {
  errors.referenceImages = "Image size must be less than 10MB";
}
```

### Server-Side Validation (Planned)
- Re-validate all client checks
- Additional security checks
- File content verification
- Rate limiting

## Error Handling

### Client-Side Error Handling
- Field-level validation errors
- Network errors caught in try-catch
- User-friendly error messages
- Toast notifications for feedback

### Server-Side Error Handling (Planned)
- 400: Validation errors with details
- 401: Authentication errors
- 413: File too large
- 500: Server errors with generic message

## Performance Considerations

### Image Handling
- Preview URLs for instant feedback (no server round-trip)
- File size validation before upload (saves bandwidth)
- Efficient FormData construction
- Background processing for generation

### API Design
- Async processing (immediate response)
- Background task for video generation
- Progress tracking via polling (existing pattern)
- Efficient file storage and cleanup

## Security Considerations

### File Upload Security (Planned)
- MIME type validation (verify actual file content)
- File size limits enforced
- Secure temp storage location
- Cleanup after processing
- Malicious content scanning (if available)

### Input Sanitization
- Prompt text sanitization
- Brand name format validation
- Prevent injection attacks
- Rate limiting per user

## Testing Considerations

### Frontend Testing
- Form validation tests
- Image upload tests
- Error handling tests
- UI interaction tests

### Backend Testing (Planned)
- API endpoint tests
- File upload tests
- Validation tests
- Integration tests with pipeline

## Deployment Considerations

### File Storage
- Temporary storage location
- Cleanup strategy
- Storage limits
- Backup considerations

### API Endpoints
- Rate limiting
- Authentication requirements
- Error responses
- Logging and monitoring

