"""
Configuration loader for unified pipeline.

Loads and validates pipeline configurations and prompt templates from YAML files.
Implements Pydantic validation to ensure configuration correctness before execution.
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

from app.schemas.unified_pipeline import PipelineConfig

logger = logging.getLogger(__name__)

# Get config directory path
CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
PROMPTS_DIR = CONFIG_DIR / "prompts"
PIPELINES_DIR = CONFIG_DIR / "pipelines"


class ConfigLoader:
    """Loads and validates pipeline configurations and prompt templates."""

    @staticmethod
    def load_pipeline_config(name: str = "default", overrides: Optional[Dict[str, Any]] = None) -> PipelineConfig:
        """
        Load pipeline configuration from YAML file with Pydantic validation.

        Args:
            name: Configuration name (default, custom, etc.)
            overrides: Optional dictionary of config overrides from API request

        Returns:
            PipelineConfig: Validated configuration object

        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ValueError: If configuration validation fails
        """
        config_path = PIPELINES_DIR / f"{name}.yaml"

        if not config_path.exists():
            raise FileNotFoundError(f"Pipeline configuration not found: {config_path}")

        logger.info(f"Loading pipeline configuration from {config_path}")

        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)

        # Extract pipeline section
        pipeline_config = config_data.get("pipeline", {})

        # Build PipelineConfig from YAML structure
        # Map stage configs to PipelineConfig fields
        stages = {stage["name"]: stage for stage in pipeline_config.get("stages", [])}

        config_dict = {
            "pipeline_name": pipeline_config.get("name", name),
        }

        # Story stage settings
        if "story" in stages:
            config_dict["story_max_iterations"] = stages["story"].get("max_iterations", 3)
            config_dict["story_timeout_seconds"] = stages["story"].get("timeout_seconds", 120)

        # Reference stage settings
        if "reference_images" in stages:
            config_dict["reference_count"] = stages["reference_images"].get("count", 3)
            config_dict["reference_quality_threshold"] = stages["reference_images"].get("quality_threshold", 0.7)

        # Scene stage settings
        if "scenes" in stages:
            config_dict["scene_max_iterations"] = stages["scenes"].get("max_iterations", 2)
            config_dict["scene_timeout_seconds"] = stages["scenes"].get("timeout_seconds", 180)

        # Video stage settings
        if "videos" in stages:
            config_dict["video_parallel"] = stages["videos"].get("parallel", True)
            config_dict["video_max_concurrent"] = stages["videos"].get("max_concurrent", 5)
            config_dict["video_timeout_seconds"] = stages["videos"].get("timeout_seconds", 600)

        # Quality scoring settings
        quality_config = config_data.get("quality", {}).get("vbench", {})
        config_dict["vbench_enabled"] = quality_config.get("enabled", True)
        config_dict["vbench_run_in_background"] = quality_config.get("run_in_background", True)
        config_dict["vbench_threshold_good"] = quality_config.get("threshold_good", 80.0)
        config_dict["vbench_threshold_acceptable"] = quality_config.get("threshold_acceptable", 60.0)

        # Apply overrides from API request
        if overrides:
            logger.info(f"Applying configuration overrides: {overrides}")
            config_dict.update(overrides)

        # Validate with Pydantic
        try:
            config = PipelineConfig(**config_dict)
            logger.info(f"✓ Pipeline configuration loaded and validated: {config.pipeline_name}")
            return config
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise ValueError(f"Invalid pipeline configuration: {e}")

    @staticmethod
    def load_prompt_template(agent_name: str) -> Dict[str, str]:
        """
        Load prompt template for an agent from YAML file.

        Args:
            agent_name: Agent name (story_director, story_critic, scene_writer, etc.)

        Returns:
            Dict with system_prompt and user_prompt_template

        Raises:
            FileNotFoundError: If prompt template doesn't exist
        """
        prompt_path = PROMPTS_DIR / f"{agent_name}.yaml"

        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {prompt_path}")

        logger.info(f"Loading prompt template from {prompt_path}")

        with open(prompt_path, "r") as f:
            prompt_data = yaml.safe_load(f)

        system_prompt = prompt_data.get("system_prompt", "")
        user_prompt_template = prompt_data.get("user_prompt_template", "")

        if not system_prompt or not user_prompt_template:
            raise ValueError(f"Invalid prompt template: missing system_prompt or user_prompt_template in {prompt_path}")

        logger.info(f"✓ Prompt template loaded: {agent_name}")
        return {
            "system_prompt": system_prompt,
            "user_prompt_template": user_prompt_template
        }

    @staticmethod
    def substitute_variables(template: str, variables: Dict[str, Any]) -> str:
        """
        Substitute variables in prompt template.

        Args:
            template: Prompt template with {variable} placeholders
            variables: Dictionary of variable names to values

        Returns:
            str: Template with variables substituted

        Example:
            template = "Create a {framework} story for {product}"
            variables = {"framework": "AIDA", "product": "EcoBottle"}
            result = "Create a AIDA story for EcoBottle"
        """
        result = template
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            result = result.replace(placeholder, str(value))

        return result


# Convenience functions for easy import
def load_pipeline_config(name: str = "default", overrides: Optional[Dict[str, Any]] = None) -> PipelineConfig:
    """Load pipeline configuration."""
    return ConfigLoader.load_pipeline_config(name, overrides)


def load_prompt_template(agent_name: str) -> Dict[str, str]:
    """Load prompt template."""
    return ConfigLoader.load_prompt_template(agent_name)


def substitute_variables(template: str, variables: Dict[str, Any]) -> str:
    """Substitute variables in template."""
    return ConfigLoader.substitute_variables(template, variables)
