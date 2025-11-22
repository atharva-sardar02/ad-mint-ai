# Master Mode API Integration Guide

## Overview

This document outlines the API integration requirements for Master Mode video generation.

## API Endpoint

### POST `/api/master-mode/generate`

Creates a new video generation request using Master Mode inputs.

### Request Format

**Content-Type**: `multipart/form-data`

#### Form Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `prompt` | string | Yes | Video generation prompt (min 10 characters) |
| `title` | string | No | Video title (max 200 characters) |
| `brand_name` | string | No | Brand name (max 50 characters) |
| `reference_image_1` | file | Yes* | First reference image (JPG/PNG, max 10MB) |
| `reference_image_2` | file | No | Second reference image (JPG/PNG, max 10MB) |
| `reference_image_3` | file | No | Third reference image (JPG/PNG, max 10MB) |

*At least one reference image is required.

### Request Example

```javascript
const formData = new FormData();
formData.append('prompt', 'Create a luxury perfume ad showcasing elegance');
formData.append('title', 'Luxury Perfume Ad - Instagram');
formData.append('brand_name', 'Chanel');
formData.append('reference_image_1', file1);
formData.append('reference_image_2', file2);
formData.append('reference_image_3', file3);

fetch('/api/master-mode/generate', {
  method: 'POST',
  body: formData
});
```

### Response Format

#### Success Response (202 Accepted)

```json
{
  "generation_id": "uuid-string",
  "status": "processing",
  "message": "Video generation started"
}
```

#### Error Response (400 Bad Request)

```json
{
  "error": "Validation failed",
  "details": {
    "prompt": "Prompt must be at least 10 characters",
    "reference_images": "At least one reference image is required"
  }
}
```

#### Error Response (413 Payload Too Large)

```json
{
  "error": "File too large",
  "details": "Reference images must be less than 10MB each"
}
```

## Backend Implementation Notes

### File Handling

1. **Save uploaded images** to temporary storage
2. **Validate file types** (JPG, PNG only)
3. **Validate file sizes** (max 10MB per image)
4. **Generate unique filenames** to avoid conflicts
5. **Clean up temporary files** after processing

### Integration with Existing Pipeline

Master Mode should integrate with the existing video generation pipeline:

1. **Use existing `process_generation` function** or create a simplified wrapper
2. **Map Master Mode inputs** to standard generation parameters:
   - `prompt` → `prompt`
   - `title` → `title`
   - `brand_name` → `brand_name`
   - `reference_image_1` → `user_initial_reference` (first image)
   - `reference_image_2`, `reference_image_3` → Additional reference images

3. **Set default values** for Master Mode:
   - `use_llm`: `true` (always use LLM for storyboard planning)
   - `use_advanced_image_generation`: `true` (always use enhanced generation)
   - `preferred_model`: `google/veo-3.1` (default model)
   - `target_duration`: `15` (default duration)

### Processing Flow

```
1. Receive multipart form data
2. Validate inputs
3. Save reference images to temp storage
4. Create generation record in database
5. Start background task for video generation
6. Return generation_id immediately
7. Process video generation asynchronously
```

## Frontend Integration

### Update MasterMode Component

Update `frontend/src/routes/MasterMode.tsx` to call the API:

```typescript
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();

  if (!validateForm()) {
    // Show error
    return;
  }

  setIsLoading(true);

  try {
    const formData = new FormData();
    formData.append('prompt', prompt);
    if (title) formData.append('title', title);
    if (brandName) formData.append('brand_name', brandName);
    
    referenceImages.forEach((img, index) => {
      if (img.file) {
        formData.append(`reference_image_${index + 1}`, img.file);
      }
    });

    const response = await fetch('/api/master-mode/generate', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}` // Get from auth store
      },
      body: formData
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Generation failed');
    }

    const data = await response.json();
    
    // Redirect to generation status page
    navigate(`/generation/${data.generation_id}`);
  } catch (error) {
    // Show error toast
  } finally {
    setIsLoading(false);
  }
};
```

## Error Handling

### Client-Side Validation

- Prompt length (min 10 characters)
- At least one reference image
- File type validation (JPG, PNG)
- File size validation (max 10MB)

### Server-Side Validation

- Re-validate all client-side checks
- Additional security checks
- File content validation (verify actual image format)
- Rate limiting

## Security Considerations

1. **File Upload Security**
   - Validate file MIME types (not just extensions)
   - Scan for malicious content
   - Limit file sizes
   - Use secure file storage

2. **Authentication**
   - Require valid authentication token
   - Check user permissions
   - Rate limit per user

3. **Input Sanitization**
   - Sanitize prompt text
   - Validate brand name format
   - Prevent injection attacks

## Testing

### Test Cases

1. **Valid Submission**
   - All required fields provided
   - Valid images uploaded
   - Should return 202 with generation_id

2. **Missing Required Fields**
   - Missing prompt → 400 error
   - No reference images → 400 error

3. **Invalid Files**
   - Wrong file type → 400 error
   - File too large → 413 error
   - Corrupted file → 400 error

4. **Authentication**
   - No token → 401 error
   - Invalid token → 401 error

## Next Steps

1. Create backend endpoint `/api/master-mode/generate`
2. Implement file upload handling
3. Integrate with existing video generation pipeline
4. Update frontend to call API
5. Add error handling and user feedback
6. Test end-to-end flow


