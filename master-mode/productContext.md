# Master Mode - Product Context

## Why Master Mode Exists

The main video generation interface (Dashboard) has become complex with many advanced settings, coherence options, and configuration choices. While powerful, this creates barriers for users who:
- Want quick results without learning all options
- Have simple use cases that don't need advanced features
- Are overwhelmed by too many choices
- Need to generate videos frequently and want a streamlined process

## Problems It Solves

### Problem 1: Complexity Overload
**Before**: Users face 10+ settings panels, multiple tabs, and numerous configuration options.

**After**: Single, focused form with only essential inputs.

### Problem 2: Decision Fatigue
**Before**: Users must decide on coherence settings, model selection, duration, LLM usage, etc.

**After**: Smart defaults handle all decisions automatically.

### Problem 3: Time to First Video
**Before**: New users spend 5-10 minutes understanding and configuring settings.

**After**: Experienced workflow: fill form → upload images → generate (under 2 minutes).

### Problem 4: Learning Curve
**Before**: Users need to understand technical concepts (IP adapter, LoRA, seed control, etc.).

**After**: No technical knowledge required - just describe what you want and provide images.

## How It Should Work

### User Journey

1. **Access**: User navigates to `/master-mode` from navbar
2. **Input**: User fills simple form:
   - Enters video description (prompt)
   - Optionally adds title and brand name
   - Uploads 1-3 reference images
3. **Validation**: Form validates inputs in real-time
4. **Submit**: User clicks "Generate Video"
5. **Processing**: System handles all complexity behind the scenes
6. **Result**: User is redirected to generation status page

### User Experience Goals

- **Simplicity**: Form should feel effortless to complete
- **Clarity**: Every field's purpose is obvious
- **Feedback**: Immediate validation and error messages
- **Confidence**: Users trust the system will produce good results
- **Speed**: Minimal time from idea to submission

## Target Users

### Primary Users
- **Content creators** who generate videos frequently
- **Marketing teams** creating multiple ad variations
- **Non-technical users** who want professional results without complexity

### Use Cases

1. **Quick Ad Creation**
   - User has product images and a brief description
   - Needs video quickly for social media
   - Doesn't need to fine-tune every setting

2. **Consistent Brand Videos**
   - User uploads brand images
   - System maintains brand consistency automatically
   - Multiple videos share visual style

3. **Rapid Prototyping**
   - User wants to test an idea quickly
   - Can iterate on prompt and images
   - Fast feedback loop

## Design Principles

1. **Progressive Disclosure**: Show only what's needed now
2. **Smart Defaults**: System makes good decisions automatically
3. **Visual Feedback**: Clear indication of what's happening
4. **Error Prevention**: Validate before submission
5. **Forgiveness**: Easy to correct mistakes

## Integration with Main System

Master Mode is not a replacement for the full Dashboard - it's a simplified entry point that:
- Uses the same backend pipeline
- Generates the same quality videos
- Shares the same authentication
- Appears in the same gallery
- Can be enhanced later with more options

## Future Vision

Master Mode could evolve to:
- Learn from user preferences
- Suggest optimal settings based on prompt
- Provide templates for common scenarios
- Support batch generation
- Integrate with external tools


