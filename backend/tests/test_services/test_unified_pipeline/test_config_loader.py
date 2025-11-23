"""
Unit tests for config_loader module.

Tests AC-2, AC-3, AC-4: YAML configuration loading and Pydantic validation.
"""
import pytest
from app.services.unified_pipeline.config_loader import (
    ConfigLoader,
    load_pipeline_config,
    load_prompt_template,
    substitute_variables
)
from app.schemas.unified_pipeline import PipelineConfig


class TestConfigLoader:
    """Test configuration loading functionality."""

    def test_load_default_pipeline_config(self):
        """Test loading default pipeline configuration with Pydantic validation."""
        config = load_pipeline_config(name="default")

        assert isinstance(config, PipelineConfig)
        assert config.pipeline_name == "default"
        assert config.story_max_iterations >= 1
        assert config.video_parallel is True
        assert config.vbench_enabled is True

    def test_load_pipeline_config_with_overrides(self):
        """Test loading config with request overrides."""
        overrides = {
            "story_max_iterations": 5,
            "vbench_enabled": False
        }

        config = load_pipeline_config(name="default", overrides=overrides)

        assert config.story_max_iterations == 5
        assert config.vbench_enabled is False
        # Other values should remain from default
        assert config.pipeline_name == "default"

    def test_load_nonexistent_config_raises_error(self):
        """Test that loading nonexistent config raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_pipeline_config(name="nonexistent")

    def test_load_story_director_prompt_template(self):
        """Test loading story director prompt template."""
        template = load_prompt_template("story_director")

        assert "system_prompt" in template
        assert "user_prompt_template" in template
        assert len(template["system_prompt"]) > 100
        assert "{framework}" in template["user_prompt_template"]

    def test_load_all_prompt_templates(self):
        """Test that all required prompt templates can be loaded."""
        agent_names = [
            "story_director",
            "story_critic",
            "scene_writer",
            "scene_critic",
            "scene_cohesor"
        ]

        for agent_name in agent_names:
            template = load_prompt_template(agent_name)
            assert template["system_prompt"]
            assert template["user_prompt_template"]

    def test_substitute_variables(self):
        """Test variable substitution in templates."""
        template = "Create a {framework} story for {product}"
        variables = {
            "framework": "AIDA",
            "product": "EcoBottle"
        }

        result = substitute_variables(template, variables)

        assert result == "Create a AIDA story for EcoBottle"
        assert "{framework}" not in result
        assert "{product}" not in result

    def test_substitute_variables_with_missing_vars(self):
        """Test that missing variables are left unchanged."""
        template = "Create a {framework} story for {product}"
        variables = {"framework": "AIDA"}

        result = substitute_variables(template, variables)

        assert "{framework}" not in result
        assert "{product}" in result  # Missing variable remains

    def test_pydantic_validation_enforces_constraints(self):
        """Test that Pydantic validation enforces field constraints."""
        # Test invalid max_iterations (< 1)
        with pytest.raises(ValueError):
            PipelineConfig(story_max_iterations=0)

        # Test invalid concurrent value (> 10)
        with pytest.raises(ValueError):
            PipelineConfig(video_max_concurrent=15)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
