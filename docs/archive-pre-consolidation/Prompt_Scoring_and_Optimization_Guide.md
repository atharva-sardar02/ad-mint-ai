# Scoring and Optimizing Prompts for Image & Video Diffusion Models

## Introduction

Frontier text-to-image and text-to-video diffusion models (such as OpenAI's Sora, Google's Veo, and the Chinese Kling model) can produce astonishing visuals from prompts. However, assessing prompt quality – and iteratively refining prompts for better outputs – remains challenging. The goal is to ensure generated content is realistic, coherent, aesthetically pleasing, stylistically consistent, and (for video) temporally stable.

This guide explores frameworks and metrics for scoring prompt outputs, as well as best practices and model-specific tips to optimize prompts. We cover both academic evaluation methods (e.g. CLIP-score, FID, VBench, PickScore) and industry heuristics, concluding with guidance specific to Sora, Veo, and Kling.

## Quality Criteria for Generated Images and Videos

When evaluating the outputs of diffusion models, several quality dimensions are considered:

### Realism

Does the output look photo-realistic or convincingly drawn/animated as intended? This often means sharp details, correct object proportions, and absence of obvious artifacts. 

Metrics like **FID (Fréchet Inception Distance)** aim to capture overall realism by comparing distribution of generated images to real images. Lower FID indicates the generated images are closer to real ones in distribution. 

For videos, the analogous metric is **FVD (Fréchet Video Distance)** – measuring similarity of spatio-temporal feature distributions in generated vs. real videos.

### Visual Coherence

Are elements in the scene composed logically and free of glitches? This includes proper spatial relationships (e.g. objects not unnaturally merged or floating) and consistency in perspective and lighting. It's a qualitative aspect often judged by human reviewers, though benchmarks like **VBench** include a spatial relationship dimension to test whether models correctly arrange scenes as prompted.

### Aesthetic Appeal

Does the image or video have an appealing composition, color, and style? Aesthetic quality is subjective, but models can be trained to predict human aesthetic ratings. For instance, **LAION's aesthetic predictor** (a linear model on CLIP embeddings) scores images on a 0–10 scale, and was used to filter training data for Stable Diffusion. Higher aesthetic scores correlate with images humans find more beautiful. **PickScore**, discussed later, is another learned metric correlating with human aesthetic preferences.

### Consistency and Continuity

Especially for videos (or image sequences), frames should be consistent: the same character should retain their identity and appearance (identity retention), the scene should maintain a coherent style and context across time, and motion should be smooth (no jitter or temporal flicker). 

New benchmarks like **VBench** explicitly break down video quality into such factors – e.g. evaluating subject identity consistency, motion smoothness, and temporal flickering separately. A good prompt (possibly combined with model features like reference images) should encourage continuity across a video's scenes.

### Adherence to Prompt and Style

The output should match the prompt's requirements: if the prompt asks for a certain style (e.g. "in Van Gogh style") or composition, the result should follow it. Alignment metrics (like **CLIP-score** or the newer **VQAScore**) measure how well the generated image or video content aligns semantically with the prompt text. 

For style adherence, one might also check if the output's visual features correspond to the described style (some methods classify or embed style to verify this). In practice, human evaluation is often used: does the image look "like a Van Gogh painting" as requested, etc.

## Quantitative Metrics and Frameworks for Prompt Output Quality

### 1. Image-Text Alignment Metrics

These metrics score how well a generated image matches the prompt description.

#### CLIP-Score

The most established is **CLIP-Score**, which uses OpenAI's CLIP model to compute the similarity between the image and prompt in a shared embedding space. A higher CLIP-score indicates the image is more semantically compatible with the text (e.g. the objects and scene in the image reflect the prompt). CLIP-score is popular due to its generality and was found to correlate reasonably with human judgments on simple prompts.

**Limitations:** CLIP has known limitations: it tends to treat prompts as a "bag of words," sometimes ignoring word order or relations. This can lead to high scores for images that contain the right objects but in the wrong configuration. For example, CLIP might not distinguish "a dog chasing a cat" versus "a cat chasing a dog", since the same keywords are present.

#### VQAScore

To address CLIP's limitations, researchers introduced **VQAScore (2024)**, which uses a generative Visual QA model to ask yes/no questions about the image and prompt. In essence, VQAScore feeds the prompt as a question (e.g. "Does the image show a dog chasing a cat?") into a VQA model and uses the probability of the answer "yes" as the score. 

This method significantly improved alignment evaluation on complex prompts – VQAScore aligns more closely with human judgment and outperforms CLIP-score on prompts involving multiple objects, relationships, or attributes.

#### Other Alignment Metrics

- **R-Precision**: Used in some research to measure if the correct caption is among top matches for an image in an embedding space
- **BLIP-based scoring**: Using image-captioning models to see if the prompt can be reconstructed from the image

Overall, the trend is toward metrics that better capture compositional semantics than raw CLIP similarity.

### 2. Image Realism and Diversity Metrics

These measure the output quality in terms of realism and variety, often independent of the prompt semantics.

#### Fréchet Inception Distance (FID)

**FID** compares the distribution of generated images to that of real images (typically from a training set) by computing the Fréchet distance between feature vectors (from an Inception network) of the two sets. Lower FID is better – it means the generated images are statistically closer to real images in the feature space. FID is very widely reported in GAN/diffusion papers to indicate overall image fidelity.

**Considerations:**
- Requires a large sample of images and a reference dataset, so it's more for model benchmarking than scoring a single prompt's output
- FID doesn't measure alignment to the prompt; it only gauges realism and diversity
- There's evidence that optimizing purely for FID can misalign with human preferences – for example, one study found that model rankings by FID can even negatively correlate with human rankings on image quality for a given prompt

#### Inception Score (IS)

**Inception Score** looks at how "confident" a classifier is about generated images and how diverse the outputs are. High IS means images are generally specific (easy to classify) yet varied in class. IS is less used now than FID, as it doesn't directly measure realism against real data.

#### Fréchet Video Distance (FVD)

For video, the analogous metric is **FVD**, which extends FID by using a 3D Inception network or similar to incorporate temporal features. FVD is commonly used to evaluate video generative models' realism, though it has been noted to emphasize per-frame quality over temporal smoothness. In response, researchers have proposed variants (e.g., **Frechet Video Motion Distance**) to specifically target motion consistency.

### 3. Learned Preference and Aesthetic Metrics

Instead of relying on pretrained classifiers, a recent trend is to train scoring models on human preferences.

#### PickScore

A prime example is **PickScore**, introduced by the Pick-a-Pic project (2023). PickScore is a scoring function learned from a dataset of over 500,000 human comparisons of text-to-image outputs. Given a prompt and an image, PickScore predicts how likely humans would prefer that image among alternatives.

**Key Advantages:**
- PickScore achieves about 70.2% accuracy in predicting human preferences, slightly above individual human raters (~68%) – essentially "superhuman" at this narrow task
- This outperforms zero-shot CLIP-based scoring (60.8%) and even dedicated aesthetics models (56.8%)
- PickScore correlates strongly with aggregate human judgments (correlation 0.917), whereas traditional FID showed a negative correlation in those tests
- Recommended as a more reliable evaluation metric for image generation than FID or naive CLIP ranking
- Stability AI has open-sourced the PickScore model and dataset, so researchers/practitioners can use this open-source scoring function to automatically rank or filter generated images

#### Aesthetic Predictors

Another approach in this vein is using **Aesthetic Predictors** – e.g., the LAION Aesthetic model which rates images on a 1–10 scale. Many diffusion tooling communities use such aesthetic scores to select the most beautiful image from a batch. While simpler than PickScore (which considers the prompt match too), aesthetic models help ensure the output is artistically pleasing. Some UIs also let users sort or filter generations by an aesthetic score.

### 4. Comprehensive Benchmarks

The ultimate evaluation combines multiple metrics or dimensions.

#### Image Benchmarks

For images, research benchmarks like **DrawBench** and **PartiPrompts** use curated prompt sets and rely on human evaluators to compare outputs from different models qualitatively.

#### VBench (Video Benchmark)

For videos, **VBench (CVPR 2024)** introduced a suite of 16 evaluation dimensions to systematically assess video generative models. These dimensions include many of the criteria mentioned earlier:

- Subject identity consistency (does a person/object stay the same over frames)
- Motion smoothness
- Temporal flicker
- Spatial relationships
- Text fidelity
- And more...

VBench provides for each dimension a set of prompt-based tests and an automatic evaluation method (often involving specialized detectors or measured features). For example:
- To detect identity drift, it might use face recognition embeddings across frames
- For temporal stability, it might measure differences between adjacent frames or use optical flow to see if changes are physically plausible

The VBench team also collected human preference data per dimension to ensure each automatic metric aligns with perception. The benchmark is fully open-sourced, including all prompt suites, evaluation code, and even a public leaderboard for models.

Such frameworks allow developers to pinpoint a model's weaknesses – e.g. if Model A has great per-frame quality but poor motion continuity, the scores will reflect that.

#### GenAI-Bench

Another emerging benchmark, **GenAI-Bench (ECCV 2024)**, focuses on challenging text prompts for images (multi-object, tricky compositions) and uses both CLIP-based and new metrics like VQAScore to rank model performance.

#### Industry Evaluations

In industry, companies like OpenAI and Google also run internal evaluations where human raters score outputs on realism, prompt fidelity, etc., to guide model improvements.

### Summary of Metrics

A combination of alignment metrics (CLIP-score or VQAScore), fidelity metrics (FID/FVD), and preference metrics (PickScore or aesthetics) can be used to score prompt outputs.

## Heuristics and Best Practices for Prompt Optimization

Crafting an effective prompt can dramatically improve output quality. Unlike a fixed description, a well-optimized prompt acts like instructions to the generative model, guiding it towards the desired result. Here are industry-recommended heuristics for prompt writing, distilled from expert communities and official model guides:

### Be Specific, But Avoid Overly Constrained Prompts

Provide enough detail for the model to lock onto your intent (especially for complex scenes), but don't micromanage every pixel. If you leave out key details, the model will fill the gaps creatively – which might yield surprising or undesired results.

**Best Practice:** Start with a clear description of subject and action, then add detail incrementally. If the output is too random, add more constraints; if it's too rigid or bland, try removing details to let the model improvise.

> "Detailed prompts give you control and consistency, while lighter prompts open space for creative outcomes… The right balance depends on your goals."

### Structure Your Prompt Like a Scene Description

Many experts suggest writing prompts in natural language, as if describing a scene to an artist or cinematographer, rather than just a comma-separated list of keywords.

**Recommended Structure:**
- **Who/what** is the focus
- **What** they are doing (action)
- **Where/when** it's happening (context)
- **Style** or mood modifiers
- Possibly in one or two well-formed sentences

**Example Transformation:**
- ❌ Poor: `cat, city, night, realistic, dynamic lighting`
- ✅ Better: `A realistic scene of a cat sprinting across a city rooftop at night, under dynamic neon lighting, cinematic angle.`

This covers subject, action, setting, style and lighting in a coherent description.

**Model-Specific Formulas:**
- **Google Veo**: "A great Veo prompt reads like a one-sentence screenplay: subject → action → setting → style → mood (+ audio)"
- **Kling**: `[Subject], [subject description], [movement], [scene]. [scene description]. [camera angle, lighting, atmosphere]`

### Use Camera and Lighting Cues for Visual Clarity

Diffusion models respond well to cinematography cues that clarify how to frame and light the scene. Adding phrases for camera perspective and lighting can enforce coherence and aesthetic quality.

**Camera Cues:**
- "wide aerial shot"
- "close-up portrait"
- "low-angle view"
- "telephoto shot"
- "macro photograph"
- "steady tracking shot"
- "handheld shaky cam"

**Lighting Cues:**
- "soft golden morning light"
- "harsh neon glow"
- "soft, diffused lighting"
- "dramatic side lighting"

**Benefits:**
- A "soft, diffused lighting" prompt tends to reduce harsh shadows and produce a gentle tone, improving realism for portraits
- Specifying "telephoto shot" or "macro photograph" can influence the level of background blur and focus on subject
- In video, camera motion cues can affect temporal consistency and how the model handles movement

**Sora Guidance:** "State the camera framing, note depth of field, describe the action in beats, and set the lighting and palette."

### Limit Each Prompt to One Scene or Idea

Trying to pack multiple unrelated scenes or a complex sequence of events into one prompt often confuses generation. Instead, follow the rule **"one scene, one action"**.

**Best Practices:**
- If you have a narrative with multiple beats (e.g. first the hero enters a room, then a fight ensues), split that into separate prompts/clips or use the model's special syntax for multiple shots if supported
- Long prompts that attempt a whole storyline may lead to jumbled or inconsistent visuals
- Both Veo and Sora documentation note that shorter prompts (or single-shot prompts) tend to be followed more reliably, whereas extremely long or multi-sentence prompts can overload the model
- For longer videos, one approach is to generate it in segments and stitch them, or use the model's chaining features

**Sora Example:** Generating two 4-second clips and editing them together might yield better fidelity than one continuous 8-second clip, because the model can focus on one shot at a time.

### Iterate and Use Feedback Loops

Treat each generation as a draft. Industry practitioners often generate a batch of variations (using the same prompt or slight tweaks) and then pick the best result – effectively using a selection process.

**Automated Selection:**
- Metrics like CLIP-score or PickScore can assist here: e.g. you could generate 10 images for a prompt and automatically select the top-scoring one as the "best" match
- The Pick-a-Pic team showed that reranking a model's outputs with PickScore produced images that humans preferred far more often than the raw model output
- Even without automated scoring, simply eyeballing multiple candidates and choosing the most coherent image is a quick way to boost quality

**Iterative Refinement:**
- After selecting a good candidate, refine the prompt further by describing desirable attributes observed or correcting errors
- **Prompt remixing**: For example, OpenAI's Sora offers a "remix" function to adjust a prompt slightly and re-render, allowing fine control over the result
- You can iteratively change phrasing, add a detail, or remove something and see how it impacts the output – akin to guiding the model by successive approximations

**The Cycle:** prompt → evaluate → tweak → repeat. This iterative cycle is essential for optimizing prompts, since generative models can be sensitive to wording and order.

### Negative Prompts and Constraints

Many diffusion frameworks support **negative prompts**, where you explicitly list aspects not to include (e.g. "negative prompt: blur, text, watermark, deformed hands"). Using negatives can improve quality by steering the model away from common artifacts.

**Best Practices:**
- Keep negatives concise (comma-separated keywords)
- Avoid terms like "no" or "don't" – just list the unwanted attributes
- Typical negative terms for image models: "low quality, blurry, oversaturated, extra limbs"
- For video: "jerky, flicker, inconsistent"

**Note:** The effect depends on how the model incorporates negative guidance – not all support it equally. When available, negative prompts are a straightforward way to penalize undesired traits and thereby effectively raise the quality score.

### Leverage Model Features for Consistency

If your target model provides special features, use them to maximize quality.

#### Reference Images for Subject Consistency

- **Google's Veo 3** standard model allows uploading 1–3 reference images of a character or object, and it will then maintain that subject's identity throughout the video
- This is extremely useful for identity retention: rather than hoping the prompt alone keeps a character looking the same, the model literally knows who to show

#### Starting Frames or Poses

- Some video models let you specify a starting frame or pose (e.g. Veo's "Start & End Frame" option in the fast model, or Kling's image-to-video initialization)
- Using these can guide the generation to be more coherent and temporally smooth

#### Prompt Weighting or Segmentation

- If a model allows dividing a prompt into segments (like "Shot 1: …; Shot 2: …"), you can ensure each scene is well-defined
- Sora's prompt anatomy encourages separating each shot's description when multiple shots are in one prompt, to give the model clear breakpoints

Utilizing these capabilities goes beyond just scoring – it actively improves the output quality by design, making it easier for the model to meet all the criteria (realism, coherence, style, etc.).

## Model-Specific Prompting Tips and Features

### OpenAI Sora (Text-to-Video)

OpenAI's Sora (now at version 2) is a state-of-the-art text-to-video model capable of ~1 minute clips. While Sora does not explicitly "score" your prompt, OpenAI provides detailed documentation on how to write prompts for the best results.

#### Prompt Structure

The **Sora 2 Prompting Guide** emphasizes treating your prompt like a movie scene description. It suggests including elements like:

- Camera framing
- Action beats
- Lighting
- Color palette
- Timing cues

#### Key Guidelines

1. **Anchor the subject** with a few distinctive details to keep it recognizable
2. **Specify "a single, plausible action"** to make the shot easier to follow
3. **Multi-shot prompts** can be separated by newlines or semicolons; make each shot a self-contained block (one camera setup, one action) for continuity

#### Example Prompt

> "In a 90s documentary-style interview, an old Swedish man sits in a study and says, 'I still remember when I was young.'"

This short prompt already defines:
- Style ("90s documentary")
- Subject and setting (old man in study)
- Dialogue

#### Advanced Formatting

If more detail is needed, Sora prompts can be made ultra-detailed in a multi-line format covering:
- Format & look
- Lenses
- Grading
- Lighting
- Atmosphere
- Location
- etc.

This allows professional-level control (e.g. specifying film stock, time of day lighting, etc.) to maximize fidelity and consistency.

#### Summary

Sora's documentation encourages:
- Balancing detail with creative freedom
- Iterating with small prompt tweaks
- Using cinematic language to get high-quality videos

**Note:** Sora's API has parameters for resolution and length which must be set via API, not via prompt – ensuring those are chosen appropriately (e.g. using higher resolution for more detail) also improves perceived quality.

### Google Veo (Text-to-Video)

Google's Veo (as of v3/3.1) is another leading video diffusion model, known for 1080p footage with audio and strong prompt adherence. Veo likewise doesn't return an explicit "prompt score," but Google DeepMind has published prompt guides for users.

#### Prompt Formula

A concise rule from their team: **"One sentence screenplay"** style prompts – mention subject, action, context, style, mood, and camera in a single sentence if possible.

**Example:**
> "A sleek futuristic robot marches through a rain-soaked neon city street… Low-angle tracking shot, vibrant neon lighting, moody ambiance."

This combines the who, what, where, and how in a vivid manner.

#### Key Guidelines

1. **Visual language**: Describe what the camera sees, not abstract concepts
2. **Avoid multiple actions or scenes** in one prompt
3. **Use film terminology** for clarity

#### Special Features

**Negative Prompts:**
- Veo supports negative prompts
- Add a separate line for `Negative prompt:` with terms like "text, watermark, bad anatomy"
- This can help eliminate common flaws

**Audio Cues:**
- If the user desires sound, they should explicitly mention audio or dialogue
- Examples: "crowd noise in the background", or provide a line of dialogue in quotes as part of the prompt

**Multi-Reference Input (Veo 3 Standard Mode):**
- Allows uploading one or more reference images
- Vastly improves identity retention across the video
- The Veo FAQ notes it ensures "the subject's identity and appearance [remain] across all frames"

**Prompt Rewriter:**
- Google offers a "prompt rewriter" behind the scenes (an AI that may adjust the user's prompt for better results)
- Advanced users can turn it off to have full control

#### Summary

Best practices for Veo:
- Be richly descriptive but concise (1–3 sentences)
- Focus on one core idea
- Use film terminology

By following these, users can achieve outputs that meet high quality bars on realism and coherence – effectively optimizing the prompt to exploit Veo's strengths (like its understanding of cinematic cues).

### Kling (Text-to-Video)

Kling is a cutting-edge Chinese text-to-video diffusion model (with versions 2.0+ emerging) renowned for smooth, lifelike outputs. Kling's developers (and platforms like RunDiffusion hosting it) have provided an official prompt structure and tips.

#### Recommended Formula

**Subject, + subject description, + subject's movement, + scene, + scene details, + optional camera/lighting/atmosphere**

#### Example Prompt

> "A young woman wearing a flowing red dress, sprinting joyfully across a sunlit meadow. Flowers sway in the gentle breeze and birds soar overhead. Wide aerial shot, soft golden light, dreamy atmosphere."

This clearly demonstrates each part:
- **Who**: young woman in red dress
- **What action**: sprinting joyfully
- **Where**: sunlit meadow with flowers and birds
- **Cinematic embellishments**: aerial shot, golden light, dreamy mood

#### Key Guidelines

1. **Keep the description clear and vivid** but not overcrowded
2. **Limit to 2–4 key ideas or elements** to avoid confusion
3. **Use natural language** rather than keyword stuffing
4. **Write naturally**: Use vivid language, not keyword spam – the model responds better to fluent descriptions
5. **Specify camera angles or motion** when it enhances the scene (just like with Sora/Veo)

#### Special Features

**Image-to-Video Initialization:**
- Like Veo, Kling can take an initial image frame to guide the video or maintain a subject
- This is a strategy to improve consistency

**Duration Constraints:**
- Kling versions may have duration limits (e.g. many demos generate ~5 second clips)
- Optimizing within that constraint means focusing the prompt on a short action that fits the timeframe

#### Summary

While Kling doesn't output a quality score to the user, following the "Kling Optimized Prompt Structure" and the provided examples is key to getting high-quality results. Users who adhere to those guidelines report more "cinematic" and consistent videos out of Kling, which implicitly means higher scores on realism, coherence, and style adherence.

## Summary

Sora, Veo, and Kling each provide prompt engineering guidelines rather than direct scoring feedback. All three stress similar themes:

- Articulate the subject and action clearly
- Set the scene and style
- Use filmic language for camera/mood
- Don't cram multiple scenes in one prompt

By leveraging these model-specific tips, users can optimize prompts to achieve the best possible output quality – often reaching a level where automatic metrics (like CLIP-score or PickScore) and human evaluators would rate the results highly on the desired criteria.

The combination of proper prompt craftsmanship and using quantitative metrics to evaluate outcomes gives a powerful framework for iteratively improving generative art and videos.

## References and Further Reading

### Metrics and Benchmarks

- **CLIP-Score**: Hugging Face implementation and documentation
- **VQAScore**: Research paper and implementation details
- **FID (Fréchet Inception Distance)**: Standard metric for image generation evaluation
- **FVD (Fréchet Video Distance)**: Video generation evaluation metric
- **PickScore**: Stability AI's open-source preference scoring model
- **VBench**: Comprehensive video generation benchmark suite (CVPR 2024)
- **GenAI-Bench**: Challenging text prompt benchmark for images (ECCV 2024)

### Model Documentation

- **OpenAI Sora**: Official prompting guide and API documentation
- **Google Veo**: DeepMind's Veo 3 prompting guidelines and features
- **Kling**: Official prompt structure and optimization tips

### Best Practices

- Industry heuristics from expert communities
- Prompt engineering guides from major model providers
- Iterative refinement techniques and feedback loops

---

*Document created: 2025-01-27*  
*Last updated: 2025-01-27*

