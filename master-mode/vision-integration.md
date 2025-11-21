# Vision API Integration for Story Generation

## Overview

Added reference image support to the Story Director using OpenAI's Vision API. The Story Director can now **see** the actual person, product, or scene elements from user-provided images and write stories based on their exact appearance.

## Changes Made

### Backend

#### 1. `backend/app/api/routes/master_mode.py`
- Added `reference_images: List[UploadFile]` parameter to the endpoint
- Saves uploaded images to temporary directory (`temp/master_mode/{user_id}/`)
- Passes image paths to `generate_story_iterative()`
- **File naming**: `reference_{index}_{filename}` for each uploaded image

#### 2. `backend/app/services/master_mode/story_generator.py`
- Added `reference_image_paths: Optional[List[str]]` parameter
- Passes image paths to `generate_story_draft()`
- Logs the number of reference images provided

#### 3. `backend/app/services/master_mode/story_director.py`
- **Added imports**: `base64`, `Path` for image encoding
- Added `reference_image_paths: Optional[List[str]]` parameter
- **Vision API Integration**:
  - When images are provided, uses OpenAI's vision format with multi-part content
  - Encodes images as base64 data URLs
  - Determines MIME type from file extension (`.jpg`/`.jpeg` → `image/jpeg`, `.png` → `image/png`)
  - Sends both text prompt and images to the LLM
- **Enhanced prompt**: When images are provided, adds explicit instructions:
  ```
  ⚠️ CRITICAL: Study these images carefully and describe EXACTLY what you see:
  - If there's a person: describe their EXACT appearance (age, hair, facial features, clothing, build)
  - If there's a product: describe its EXACT specifications (shape, size, colors, materials, branding)
  - If there's a scene: describe the EXACT environment, lighting, and composition
  
  Your story must reflect the ACTUAL appearance shown in these images, not generic descriptions.
  ```

### Frontend

#### `frontend/src/routes/MasterMode.tsx`
- **Fixed**: Changed `formData.append("reference_image_{index}", file)` to `formData.append("reference_images", file)`
- This matches the backend's `List[UploadFile]` parameter name

## How It Works

### User Flow
1. User uploads 1-3 reference images (person, product, scene)
2. User enters prompt describing the advertisement concept
3. User clicks "Generate"

### Backend Flow
1. **API Endpoint**: Receives images and saves to temp directory
2. **Story Generator**: Passes image paths to Story Director
3. **Story Director**:
   - Reads each image file
   - Encodes as base64
   - Creates vision-format message with text + images
   - OpenAI's `gpt-4o` (vision-capable) analyzes images
   - LLM writes story describing **exactly** what it sees in the images

### Example Vision Message Format
```python
{
  "role": "user",
  "content": [
    {"type": "text", "text": "Create a story... [instructions]"},
    {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,/9j/4AAQ..."}},
    {"type": "image_url", "image_url": {"url": "data:image/png;base64,iVBORw0K..."}}
  ]
}
```

## Benefits

### Before (Text-Only)
- Story Director imagines a generic "30-year-old woman with dark hair"
- Product descriptions are vague: "a perfume bottle"
- Inconsistent across scenes

### After (With Vision)
- Story Director sees the **actual** person: "32-year-old woman, 5'6", shoulder-length chestnut brown hair with subtle highlights, oval face, hazel eyes..."
- Product is exactly described: "8-inch tall frosted glass bottle with rose gold cap, embossed 'Midnight' logo in cursive..."
- **Consistent** appearance across all scenes because the LLM knows exactly what the subject looks like

## Technical Details

### Supported Image Formats
- JPEG/JPG (`.jpg`, `.jpeg`)
- PNG (`.png`)

### Image Encoding
- Base64 encoding for data URLs
- Format: `data:{mime_type};base64,{encoded_data}`

### Model Requirements
- Requires `gpt-4o` or `gpt-4-turbo` (vision-capable models)
- Falls back gracefully if no images provided (text-only mode)

### Error Handling
- If image reading fails, logs error and continues without that image
- If all images fail, continues with text-only mode
- User is notified of any issues via error messages

## File Structure

```
temp/
└── master_mode/
    └── {user_id}/
        ├── reference_1_{filename}.jpg
        ├── reference_2_{filename}.png
        └── reference_3_{filename}.jpg
```

## Future Enhancements

1. **Image Cleanup**: Auto-delete temp images after processing
2. **Image Validation**: Check dimensions, aspect ratio, quality
3. **Image Preprocessing**: Resize, compress for faster uploads
4. **Scene Writer Vision**: Also pass images to Scene Writer for even more accurate scene descriptions
5. **Multi-modal Critique**: Have Story Critic also view images to verify accuracy

## Testing

To test:
1. Upload an image of a person and/or product
2. Enter a prompt like "Create a luxury perfume ad"
3. Check the generated story - it should describe the exact appearance from your images
4. Look for specific details: hair color, clothing, product shape, colors, etc.

## Documentation Updates Needed

- [ ] Update `master-mode/README.md` with vision feature
- [ ] Update `master-mode/API_INTEGRATION.md` with image upload details
- [ ] Update `master-mode/techContext.md` with vision API integration
- [ ] Add example prompts showing vision capabilities


