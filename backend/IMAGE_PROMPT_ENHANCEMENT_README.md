# Image Prompt Enhancement CLI Tool

Standalone command-line tool for iteratively enhancing image prompts using two specialized LLM agents.

## Overview

This tool uses a two-agent system to transform any basic image prompt into a professional, production-ready specification optimized for image generation models (Stable Diffusion, DALL-E, Midjourney, etc.):

- **Agent 1 (Cinematographer/Creative Director)**: Enhances prompts with camera details, lighting, composition, film stock, mood, and aspect ratio
- **Agent 2 (Prompt Engineer)**: Critiques and scores prompts, providing actionable feedback

The agents iterate until a quality threshold is met or convergence is detected.

## Installation

Ensure you have the required dependencies:

```bash
cd backend
pip install -r requirements.txt
```

Set your OpenAI API key:

```bash
export OPENAI_API_KEY="your-key-here"
# Or add to .env file
```

## Usage

### Basic Usage

```bash
# Read from file
python enhance_image_prompt.py prompt.txt

# Read from stdin
echo "A cat in a city" | python enhance_image_prompt.py -

# Or pipe from file
cat my_prompt.txt | python enhance_image_prompt.py -
```

### Advanced Options

```bash
# Custom output directory
python enhance_image_prompt.py prompt.txt --output-dir ./my_traces

# More iterations for complex prompts
python enhance_image_prompt.py prompt.txt --max-iterations 5

# Higher quality threshold
python enhance_image_prompt.py prompt.txt --threshold 90

# Different models
python enhance_image_prompt.py prompt.txt --creative-model gpt-4 --critique-model gpt-4-turbo

# Verbose logging
python enhance_image_prompt.py prompt.txt --verbose
```

## Output Structure

All trace files are saved to `output/image_prompt_traces/<timestamp>/`:

```
output/image_prompt_traces/20250115_143022/
├── 00_original_prompt.txt              # Original user input
├── 01_agent1_iteration_1.txt           # First Cinematographer enhancement
├── 02_agent2_iteration_1.txt           # First Prompt Engineer critique + score
├── 03_agent1_iteration_2.txt           # Second Cinematographer refinement (if iterated)
├── 04_agent2_iteration_2.txt           # Second Prompt Engineer critique (if iterated)
├── 05_final_enhanced_prompt.txt        # Final enhanced prompt
├── prompt_trace_summary.json            # Metadata: scores, iterations, timestamps
└── FINAL_PROMPT.txt                     # Convenience copy of final prompt
```

## Scoring Dimensions

The Prompt Engineer scores prompts on 5 dimensions (0-100 each):

1. **Completeness**: Does it have all necessary elements (subject, scene, style, brand if applicable)?
2. **Specificity**: Are visual details clear and unambiguous?
3. **Professionalism**: Is it ad-quality language?
4. **Cinematography**: Does it include camera/composition details?
5. **Brand Alignment**: Are brand guidelines present and clear (if applicable)?

The **overall score** is a weighted average:
- Completeness: 25%
- Specificity: 25%
- Professionalism: 20%
- Cinematography: 15%
- Brand Alignment: 15%

## Prompt Scoring Guide Compliance

Enhanced prompts follow the Prompt Scoring Guide best practices:

- **Scene Structure**: Follows pattern (who/what → action → where/when → style)
- **Camera Cues**: Includes cues like "wide aerial shot", "close-up portrait", "telephoto shot", "macro photograph"
- **Lighting Cues**: Includes cues like "soft golden morning light", "harsh neon glow", "dramatic side lighting"
- **Single Scene**: Limited to one scene or idea per prompt
- **Natural Language**: Uses natural language, not keyword stuffing

## Examples

### Example 1: Basic Prompt

**Input:**
```
A cat in a city
```

**Output:**
```
A sleek black cat sprinting across a rain-soaked neon city street at night. Canon EOS R5, 85mm f/1.2 lens, wide aerial shot, dramatic side lighting with harsh neon glow, cinematic color grading, moody atmosphere, 16:9 aspect ratio
```

**Scores:**
- Completeness: 90/100
- Specificity: 88/100
- Professionalism: 92/100
- Cinematography: 95/100
- Brand Alignment: 80/100
- **Overall: 89.0/100**

### Example 2: Product Prompt

**Input:**
```
A coffee maker
```

**Output:**
```
A premium stainless steel coffee maker on a modern kitchen counter, soft golden morning light streaming through a window, Canon EOS R5, 50mm f/1.4 lens, close-up portrait, soft diffused lighting, cinematic color grading with warm tones, professional advertising quality, 16:9 aspect ratio
```

## Command-Line Options

```
positional arguments:
  input                 Input file path or '-' for stdin

optional arguments:
  --output-dir DIR      Output directory for trace files (default: output/image_prompt_traces/<timestamp>)
  --max-iterations N    Maximum iteration rounds (default: 3)
  --threshold F         Score threshold for early stopping (default: 85.0)
  --creative-model M    Model for Cinematographer agent (default: gpt-4-turbo)
  --critique-model M    Model for Prompt Engineer agent (default: gpt-4-turbo)
  --verbose             Enable verbose logging
  -h, --help            Show help message
```

## How It Works

1. **Initial Assessment**: Quick rule-based scoring to determine if enhancement is needed (skips if score >= 75.0)

2. **Iteration Loop** (max 3 rounds by default):
   - **Agent 1 (Cinematographer)**: Enhances prompt with camera, lighting, composition details
   - **Agent 2 (Prompt Engineer)**: Critiques and scores the enhanced prompt
   - **Early Stopping**: Exits if score >= threshold or convergence detected (improvement < 2 points)

3. **Trace Files**: All prompt versions, scores, and metadata saved to trace directory

4. **Console Output**: Displays scores, iteration history, and final enhanced prompt

## Integration with Image Generation

The enhanced prompts are optimized for image generation models and can be used directly with:

- Stable Diffusion (via Replicate, Hugging Face, or local)
- DALL-E (via OpenAI API)
- Midjourney (via Discord bot or API)
- Other text-to-image models

## Performance

- Typical enhancement time: 15-30 seconds for 1-2 iterations
- Target: <45 seconds for 2-iteration enhancement
- Performance depends on OpenAI API response time

## Error Handling

The tool handles:
- Missing API key (graceful error message)
- Invalid file paths (clear error message)
- API failures (error logging with verbose mode)
- Empty stdin input (validation error)

## Testing

Run tests:

```bash
# Unit tests
pytest tests/test_image_prompt_enhancement.py -v

# Integration tests
pytest tests/integration/test_enhance_image_prompt_cli.py -v

# Compliance tests
pytest tests/test_prompt_scoring_guide_compliance.py -v
```

## See Also

- **Service Implementation**: `app/services/pipeline/image_prompt_enhancement.py`
- **Video Prompt Enhancement**: `enhance_prompt.py` (for video prompts)
- **Prompt Scoring Guide**: `docs/Prompt_Scoring_and_Optimization_Guide.md`
- **Epic 8 Tech Spec**: `docs/sprint-artifacts/tech-spec-epic-8.md`



