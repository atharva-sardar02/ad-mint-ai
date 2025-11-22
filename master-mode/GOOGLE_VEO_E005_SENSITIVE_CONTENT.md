# Google Veo API Sensitive Content Error (E005)

**Date:** November 21, 2024  
**Error Code:** E005  
**Error Message:** "The input or output was flagged as sensitive. Please try again with different inputs."

## Problem

During Master Mode video generation, Google's Veo 3.1 API rejected all video generation requests with error code E005, indicating content safety violations.

### Error Details from Logs:
```
Video generation failed: The input or output was flagged as sensitive. 
Please try again with different inputs. (E005) (uIJ6l3ruRD)
```

**Failed Scenes:** All 3 scenes (1, 2, 3)  
**Reference Images Used:**
- `reference_1_boy_in_dc.jpg`
- `reference_2_women.jpg`
- `reference_3_perfume bottle -2.jpg`

## Root Cause

Google's Veo API has built-in content safety filters that automatically scan:
1. **Input prompts** - The text descriptions sent to the model
2. **Reference images** - Images attached for R2V (Reference-to-Video) mode
3. **Generated outputs** - The videos produced by the model

These filters are designed to prevent generation of:
- Sensitive or inappropriate content
- Copyrighted material
- Content that violates Google's AI Principles

**The filter is external to our application** - we cannot control or bypass it.

## Why This Happens

### Common Triggers:
1. **Human subjects in reference images** - Especially close-up faces or people in certain poses
2. **Brand names/logos** - Perfume bottles with visible brand names
3. **Certain descriptive words** - Words that might be interpreted as sensitive
4. **Combination of elements** - Sometimes individual elements are fine, but together they trigger the filter

### Your Case:
The combination of:
- Reference images with people (boy, woman)
- Perfume bottle (potentially branded)
- Detailed scene descriptions about applying perfume

...triggered Google's safety filters.

## Solutions

### 1. **Modify Reference Images** ✅ Recommended
- Use generic, stock-style images without recognizable faces
- Avoid visible brand names/logos on products
- Use well-lit, professional-looking photos
- Try cartoon/illustrated versions instead of photos

### 2. **Simplify Prompts**
- Make scene descriptions less detailed
- Avoid overly specific actions (e.g., "spray perfume on neck")
- Use more general terms

### 3. **Retry with Different Combinations**
- Try with just 1-2 reference images instead of 3
- Test which image triggers the filter by removing them one at a time
- Mix and match different reference images

### 4. **Use Different Models**
If available in your setup, try:
- Different video generation models
- Text-to-Video mode instead of Reference-to-Video mode

### 5. **Contact Google Cloud Support**
If you believe your content is legitimate:
- Review Google's AI Principles
- Contact Google Cloud support with your use case
- Request clarification on what triggered the filter

## Code Fix Applied

### Bug: AttributeError in Completion Data
**File:** `backend/app/api/routes/master_mode.py` (Line 347)

**Error:**
```python
completion_data["story_score"] = response["story"].get("final_score", 0)
# AttributeError: 'str' object has no attribute 'get'
```

**Fix:**
```python
# Before (WRONG)
if "story" in response:
    completion_data["story_score"] = response["story"].get("final_score", 0)

# After (CORRECT)
if "final_score" in response:
    completion_data["story_score"] = response["final_score"]
```

**Reason:** `response["story"]` contains the story text (string), not a dictionary. The score is stored in `response["final_score"]` directly.

## Testing Recommendations

### Test 1: Minimal Reference Images
```
Prompt: "A elegant perfume advertisement"
Images: 
- 1 generic product image (no brand visible)
```

### Test 2: Generic Stock Photos
```
Prompt: "Luxury product showcase"
Images:
- Professional stock photos
- No faces or minimal faces
- Simple backgrounds
```

### Test 3: Illustrated/Cartoon Style
```
Prompt: "Animated perfume commercial"
Images:
- Cartoon/illustrated references
- Stylized rather than photorealistic
```

## Prevention

### Best Practices:
1. ✅ Use stock images from royalty-free sources
2. ✅ Avoid close-up human faces
3. ✅ Remove visible brand names/logos from products
4. ✅ Keep prompts professional and neutral
5. ✅ Test with minimal inputs first, then add complexity

### Red Flags to Avoid:
- ❌ Photos of real people in personal/intimate settings
- ❌ Branded products with visible logos
- ❌ Copyrighted characters or imagery
- ❌ Overly specific body-related descriptions
- ❌ Content that could be interpreted as medical/health claims

## Current Status

✅ **Code Fix Applied:** AttributeError resolved  
⚠️ **API Content Filter:** External limitation - requires different inputs  
📋 **Next Steps:** 
1. Try generation with different reference images
2. Simplify prompts if needed
3. Test with minimal inputs first

## Notes

This is **not a bug in our code** - it's a content policy enforcement by Google's API. The retry logic (3 attempts) is working correctly, but all attempts are being rejected by Google's filters due to the input content itself.

**Recommendation:** Start with very simple, generic inputs to verify the pipeline works, then gradually add complexity while monitoring which changes trigger the filter.

