"""
Prompt files for the 3-stage perfume ad pipeline.
"""

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


def load_prompt(filename: str) -> str:
    """Load a prompt file from the prompts directory."""
    prompt_path = PROMPTS_DIR / filename
    return prompt_path.read_text(encoding="utf-8").strip()


# Load prompts at module level
STAGE1_BLUEPRINT_PROMPT = load_prompt("stage1_blueprint_prompt.txt")
STAGE2_SCENT_PROFILE_PROMPT = load_prompt("stage2_scent_profile_prompt.txt")
STAGE3_SCENE_ASSEMBLER_PROMPT = load_prompt("stage3_scene_assembler_prompt.txt")

