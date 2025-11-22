# Full Professional Workflow for Generative-AI Video Creation

> Based on professional creator processes for generating cinematic AI video content

## Overview

This document outlines the complete end-to-end workflow that professional creators follow when generating high-quality video content using AI tools. The process emphasizes iteration, refinement, and the understanding that failure is an expected part of the creative process.

---

## Phase 1: TEXT → PHOTO

**Goal:** Generate one strong, polished hero frame that defines the visual identity of the video.

### Why Start with a Still Image?

Even though text-to-video is possible, professional creators find that starting with a single high-quality still image leads to vastly better cinematic output. The image becomes the anchor for:
- Style
- Lighting
- Mood
- Composition

### 1.1. Write the First Prompt

A professional does not expect the first prompt to work. They treat it as an iterative process.

**Initial prompt should include:**
- **Subject** - What is the main focus?
- **Lighting** - Direction, quality, color temperature
- **Mood** - Emotional tone and atmosphere
- **Camera brand/lens** - Specific equipment references (e.g., Leica M11, Alexa Mini)
- **Composition** - Framing, rule of thirds, depth
- **Film stock / color science** - Visual aesthetic (e.g., Cinestill 800T)
- **Tone and atmosphere** - Overall feeling
- **Specific aesthetic** - References like "Nike commercial", "super realism"
- **Aspect ratio** - Format specification (e.g., `--ar 16:9`)
- **Stylization and omni-weight parameters** - Technical controls

**Example Structure:**
```
"A hand holding up the Larry O'Brien trophy with blue and orange confetti…
shot on Leica M11… Cinestill 800T look… cinematic composition… shallow depth… 
super realism —ar 16:9 —raw —ow 800"
```

### 1.2. Iterate Like a Slot Machine

Professionals expect many failed generations. This is normal and expected.

**Iteration strategies:**
- Regenerate the same prompt repeatedly
- Adjust omni-weight (OW) parameters
- Add or remove style references
- Use image prompts for reference
- Tweak lighting descriptions
- Adjust composition details
- Modify grain and texture parameters
- Adjust stylization sliders (typically 100–300 range)
- Use Omni Reference Slider (typically 50–200 range)

**Goal:** Land one image that "hits" — the moment where the vibe is right.

### 1.3. Polish the Image

Once a strong frame is found:

1. **Export the image** in high resolution
2. **Clean imperfections in Photoshop:**
   - Remove dust and artifacts
   - Fix anatomy issues
   - Clean up edges
   - Correct compositing errors
   - Enhance details

This creates the **master keyframe** that will be used for video generation.

---

## Phase 2: PHOTO → VIDEO

**Goal:** Turn the polished still image into a cinematic moving shot.

The creator specifically uses **Kling** as their primary engine for this phase.

### 2.1. Send the Polished Frame to Kling

Kling is used to:
- Animate the still image
- Add motion, parallax, and cinematic energy
- Generate slow motion effects
- Create push-ins, tracking, or camera movement
- Add dynamic elements

**Important:** They do not expect good output on the first try.

> "It often takes countless generations to land something usable."

### 2.2. Improve Prompting (DeepSeek Assist)

They use **DeepSeek** to:
- Rewrite prompts for clarity
- Clarify the cinematographic direction
- Improve Kling's understanding of camera moves and lighting
- Fix logical inconsistencies
- Refine technical descriptions

### 2.3. Write Cinematographer-Level Prompts

Professionals describe shots like a real DP (Director of Photography):

**Camera specifications:**
- Camera type (Alexa Mini, Leica, RED, Sony Venice)
- Lens (35mm, Helios 44, Cooke S4)
- Lighting direction (backlit, motivated lighting, hard rim light)
- Camera movement (push-in, dolly left, static tripod, handheld)
- Frame rate (120 fps slow motion)
- Environmental details (dust, confetti, rain, particles)

**Example from professional workflow:**
```
"Alexa Mini steadily pushing in with cinematic depth through a Helios-44 58mm lens…"
```

### 2.4. Add Negative Prompts

Negative prompts help clean up artifacts and stabilize output.

**Common negative prompts:**
- "fast movements"
- "disfigurements"
- "low quality"
- "dust particles"
- "artifacts"
- "distortions"

### 2.5. Iterate Again

Professionals expect:
- Many failed generations
- Inconsistent outputs
- Strange distortions
- Unexpected movements

**Best practice:** Tweak instead of brute-forcing.

> "If things aren't clicking, try reworking the prompt instead of brute-forcing."

---

## Phase 3: Professional Mindset

### Trial and Error is the Norm

This workflow is deliberately chaotic and experimental.

**A professional expects:**
- 10 versions of a prompt → 10 wildly different results
- 1 masterpiece → 20 trash outputs
- Inconsistency across generations
- Time-consuming iteration
- Credit burn
- Patience-testing randomness

**They normalize failure as part of the workflow.**

### Key Principles

The creator stresses:

1. **AI is unpredictable** - Embrace the chaos
2. **Expect weirdness** - Strange outputs are normal
3. **Expect failure** - Most attempts won't work
4. **Take breaks** - Don't burn out on iteration
5. **Treat it like a creative slot machine** - Keep pulling until you hit
6. **Celebrate the 1% of outputs that are magic** - Quality over quantity

---

## Full End-to-End Pipeline Summary

### PHASE 1 — Text → Photo (Midjourney)

1. Write a detailed, cinematic initial prompt
2. Generate repeatedly (dozens of attempts)
3. Adjust omni-weight, stylization, references
4. Regenerate until the "hero frame" appears
5. Export and fix imperfections in Photoshop

### PHASE 2 — Photo → Video (Kling)

1. Import still into Kling
2. Write cinematographer-level prompts
3. Add negative prompts
4. Enhance prompts using DeepSeek
5. Generate dozens of versions
6. Refine movement, lighting, realism
7. Keep only the best shot

### PHASE 3 — Professional Mindset

1. Expect failure
2. Over-generate and curate
3. Iterate until the cinematic magic emerges

---

## Tools Used

- **Midjourney** - Text-to-image generation
- **Photoshop** - Image refinement and cleanup
- **Kling** - Image-to-video animation
- **DeepSeek** - Prompt enhancement and refinement

---

## Key Takeaways

1. **Start with a hero frame** - Don't skip the image generation phase
2. **Iteration is mandatory** - Expect dozens of attempts per phase
3. **Polish matters** - Clean up images before video generation
4. **Write like a cinematographer** - Use professional camera and lighting terminology
5. **Failure is expected** - Most outputs will be unusable
6. **Quality over quantity** - One perfect shot is worth 20 failed attempts
7. **Use AI assistance** - Tools like DeepSeek can improve prompt quality
8. **Patience is essential** - This is not a fast process

---

## Notes

- This workflow prioritizes quality over speed
- Credit costs can be significant due to high iteration rates
- Time investment is substantial but necessary for professional results
- The process requires both technical knowledge and creative vision
- Understanding cinematography principles significantly improves outcomes

