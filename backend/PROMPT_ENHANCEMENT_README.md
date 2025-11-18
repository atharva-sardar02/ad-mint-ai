# Prompt Enhancement CLI Tool

Standalone command-line tool for iteratively enhancing prompts using two specialized LLM agents.

## Overview

This tool uses a two-agent system to transform any user prompt into a professional, production-ready specification:

- **Agent 1 (Creative Director)**: Enhances prompts with cinematography, brand elements, and professional advertising language
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
python enhance_prompt.py prompt.txt

# Read from stdin
echo "Create an ad for my product" | python enhance_prompt.py -

# Or pipe from file
cat my_prompt.txt | python enhance_prompt.py -
```

### Advanced Options

```bash
# Custom output directory
python enhance_prompt.py prompt.txt --output-dir ./my_traces

# More iterations for complex prompts
python enhance_prompt.py prompt.txt --max-iterations 5

# Higher quality threshold
python enhance_prompt.py prompt.txt --threshold 90

# Different models
python enhance_prompt.py prompt.txt --creative-model gpt-4 --critique-model gpt-4-turbo

# Verbose logging
python enhance_prompt.py prompt.txt --verbose
```

## Output Structure

All trace files are saved to `output/prompt_traces/<timestamp>/`:

```
output/prompt_traces/20250115_143022/
├── 00_original_prompt.txt              # Original user input
├── 01_agent1_iteration_1.txt           # First Creative Director enhancement
├── 02_agent2_iteration_1.txt           # First Prompt Engineer critique + score
├── 03_agent1_iteration_2.txt           # Second Creative Director refinement (if iterated)
├── 04_agent2_iteration_2.txt           # Second Prompt Engineer critique (if iterated)
├── 05_final_enhanced_prompt.txt        # Final enhanced prompt
├── FINAL_PROMPT.txt                     # Convenience copy of final prompt
└── prompt_trace_summary.json           # Complete metadata and history
```

## Example

**Input (`prompt.txt`):**
```
Create an ad for my coffee shop
```

**Run:**
```bash
python enhance_prompt.py prompt.txt
```

**Output:**
- Enhanced prompt with cinematography details, brand elements, professional language
- All intermediate versions saved to trace files
- Score breakdown and iteration history
- Final prompt ready for video generation

**Example Enhanced Output:**
```
Cinematic 15-second video advertisement for a premium coffee shop, featuring:
- Opening scene: Wide establishing shot (35mm lens, golden hour lighting) of the coffee shop exterior with warm, inviting atmosphere
- Medium shot of barista crafting artisanal coffee with steam and rich espresso crema
- Close-up of coffee beans being ground, emphasizing quality and freshness
- Final scene: Customer enjoying coffee with satisfied expression, soft focus background
- Brand colors: Deep brown (#3E2723) and warm cream (#FFF8E1)
- Mood: Cozy, professional, artisanal
- Target audience: Coffee enthusiasts, professionals aged 25-45
- Call-to-action: "Experience Artisan Coffee Today"
```

## Integration with Pipeline

This tool can be used standalone for testing, or integrated into the main pipeline:

```python
from app.services.pipeline.prompt_enhancement import enhance_prompt_iterative

result = await enhance_prompt_iterative(
    user_prompt="Create an ad for my product",
    max_iterations=3,
    score_threshold=85.0,
    trace_dir=Path("output/prompt_traces/my_generation")
)

enhanced_prompt = result.final_prompt
# Use enhanced_prompt for VideoDirectorGPT planning...
```

## Scoring Dimensions

Prompts are scored on 5 dimensions (0-100 each):

1. **Completeness**: Has all necessary elements (product, brand, style, target audience)
2. **Specificity**: Visual details are clear and unambiguous
3. **Professionalism**: Ad-quality language and structure
4. **Cinematography**: Camera/composition details included
5. **Brand Alignment**: Brand guidelines present and clear

**Overall Score**: Weighted average of all dimensions

## Cost & Performance

- **Cost**: ~$0.01-0.04 per enhancement (depending on iterations)
- **Time**: ~6-12 seconds for 2-3 iterations
- **Early Stopping**: Automatically stops if score ≥ threshold or convergence detected

## Tips

1. **Start simple**: Even minimal prompts get enhanced significantly
2. **Check traces**: Review intermediate files to understand the enhancement process
3. **Adjust threshold**: Lower threshold (75-80) for faster results, higher (90+) for premium quality
4. **Use verbose mode**: `--verbose` to see detailed agent interactions

## Troubleshooting

**"OPENAI_API_KEY not configured"**
- Set `OPENAI_API_KEY` environment variable or add to `.env` file

**"No prompt provided"**
- Ensure input file exists and is not empty
- Check file encoding (should be UTF-8)

**Low scores after iterations**
- Try increasing `--max-iterations`
- Check if prompt is too vague or ambiguous
- Review critique files to see what improvements are needed

