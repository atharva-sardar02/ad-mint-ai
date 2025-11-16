"""
Unit tests for coherence_settings service.
Tests default settings, validation, and defaults application.
"""
import pytest
from app.services.coherence_settings import (
    get_default_settings,
    apply_defaults,
    validate_settings,
    get_settings_metadata,
)
from app.schemas.generation import CoherenceSettings


class TestGetDefaultSettings:
    """Test get_default_settings function."""

    def test_returns_recommended_defaults(self):
        """Test that default settings return recommended values."""
        defaults = get_default_settings()

        assert isinstance(defaults, CoherenceSettings)
        assert defaults.seed_control is True
        assert defaults.enhanced_planning is True
        assert defaults.vbench_quality_control is True
        assert defaults.post_processing_enhancement is True
        assert defaults.ip_adapter_reference is False
        assert defaults.ip_adapter_sequential is False
        assert defaults.lora is False
        assert defaults.controlnet is False
        assert defaults.csfd_detection is False


class TestApplyDefaults:
    """Test apply_defaults function."""

    def test_returns_defaults_when_none_provided(self):
        """Test that None input returns full defaults."""
        result = apply_defaults(None)

        assert isinstance(result, CoherenceSettings)
        assert result.seed_control is True
        assert result.enhanced_planning is True

    def test_applies_defaults_to_partial_settings(self):
        """Test that partial settings get defaults for missing fields."""
        partial = {"seed_control": False, "ip_adapter_reference": True}

        result = apply_defaults(partial)

        assert result.seed_control is False  # Provided value
        assert result.ip_adapter_reference is True  # Provided value
        assert result.ip_adapter_sequential is False  # Default applied
        assert result.enhanced_planning is True  # Default applied
        assert result.vbench_quality_control is True  # Default applied

    def test_backward_compatibility_with_old_ip_adapter_field(self):
        """Test that old ip_adapter field maps to ip_adapter_reference."""
        partial = {"seed_control": False, "ip_adapter": True}

        result = apply_defaults(partial)

        assert result.seed_control is False
        assert result.ip_adapter_reference is True  # Mapped from old field
        assert result.ip_adapter_sequential is False

    def test_preserves_all_provided_values(self):
        """Test that all provided values are preserved."""
        full_settings = {
            "seed_control": False,
            "ip_adapter_reference": True,
            "ip_adapter_sequential": False,
            "lora": True,
            "enhanced_planning": False,
            "vbench_quality_control": False,
            "post_processing_enhancement": False,
            "controlnet": True,
            "csfd_detection": True,
        }

        result = apply_defaults(full_settings)

        assert result.seed_control is False
        assert result.ip_adapter_reference is True
        assert result.ip_adapter_sequential is False
        assert result.lora is True
        assert result.enhanced_planning is False
        assert result.vbench_quality_control is False
        assert result.post_processing_enhancement is False
        assert result.controlnet is True
        assert result.csfd_detection is True


class TestValidateSettings:
    """Test validate_settings function."""

    def test_validates_correct_settings(self):
        """Test that valid settings pass validation."""
        settings = CoherenceSettings(
            seed_control=True,
            ip_adapter_reference=True,
            ip_adapter_sequential=False,
            enhanced_planning=True,  # Required for IP-Adapter
            vbench_quality_control=True,
            post_processing_enhancement=True,
        )

        is_valid, error_message = validate_settings(settings)
        assert is_valid is True
        assert error_message is None

    def test_catches_ip_adapter_without_enhanced_planning(self):
        """Test that IP-Adapter without Enhanced Planning fails validation."""
        settings = CoherenceSettings(
            seed_control=True,
            ip_adapter_reference=True,
            ip_adapter_sequential=False,
            enhanced_planning=False,  # Missing requirement
            vbench_quality_control=True,
            post_processing_enhancement=True,
        )

        is_valid, error_message = validate_settings(settings)
        assert is_valid is False
        assert "IP-Adapter" in error_message
        assert "Enhanced LLM Planning" in error_message

    def test_allows_ip_adapter_when_enhanced_planning_enabled(self):
        """Test that IP-Adapter is valid when Enhanced Planning is enabled."""
        settings = CoherenceSettings(
            seed_control=True,
            ip_adapter_reference=True,
            ip_adapter_sequential=False,
            enhanced_planning=True,  # Requirement met
            vbench_quality_control=True,
            post_processing_enhancement=True,
        )

        is_valid, error_message = validate_settings(settings)
        assert is_valid is True
        assert error_message is None

    def test_catches_both_ip_adapter_modes_enabled(self):
        """Test that both IP-Adapter modes cannot be enabled simultaneously."""
        settings = CoherenceSettings(
            seed_control=True,
            ip_adapter_reference=True,
            ip_adapter_sequential=True,  # Incompatible
            enhanced_planning=True,
            vbench_quality_control=True,
            post_processing_enhancement=True,
        )

        is_valid, error_message = validate_settings(settings)
        assert is_valid is False
        assert "incompatible" in error_message.lower()
        assert "Reference Images" in error_message or "Sequential Images" in error_message

    def test_catches_lora_without_enhanced_planning(self):
        """Test that LoRA without Enhanced Planning fails validation."""
        settings = CoherenceSettings(
            seed_control=True,
            lora=True,
            enhanced_planning=False,  # Missing requirement
            vbench_quality_control=True,
            post_processing_enhancement=True,
        )

        is_valid, error_message = validate_settings(settings)
        assert is_valid is False
        assert "LoRA" in error_message
        assert "Enhanced LLM Planning" in error_message

    def test_catches_controlnet_without_enhanced_planning(self):
        """Test that ControlNet without Enhanced Planning fails validation."""
        settings = CoherenceSettings(
            seed_control=True,
            controlnet=True,
            enhanced_planning=False,  # Missing requirement
            vbench_quality_control=True,
            post_processing_enhancement=True,
        )

        is_valid, error_message = validate_settings(settings)
        assert is_valid is False
        assert "ControlNet" in error_message
        assert "Enhanced LLM Planning" in error_message

    def test_catches_csfd_detection_without_enhanced_planning(self):
        """Test that CSFD Detection without Enhanced Planning fails validation."""
        settings = CoherenceSettings(
            seed_control=True,
            csfd_detection=True,
            enhanced_planning=False,  # Missing requirement
            vbench_quality_control=True,
            post_processing_enhancement=True,
        )

        is_valid, error_message = validate_settings(settings)
        assert is_valid is False
        assert "CSFD" in error_message
        assert "Enhanced LLM Planning" in error_message

    def test_catches_controlnet_and_csfd_incompatibility(self):
        """Test that ControlNet and CSFD Detection are incompatible."""
        settings = CoherenceSettings(
            seed_control=True,
            controlnet=True,
            csfd_detection=True,  # Incompatible with ControlNet
            enhanced_planning=True,
            vbench_quality_control=True,
            post_processing_enhancement=True,
        )

        is_valid, error_message = validate_settings(settings)
        assert is_valid is False
        assert "ControlNet" in error_message
        assert "CSFD" in error_message
        assert "incompatible" in error_message.lower()


class TestGetSettingsMetadata:
    """Test get_settings_metadata function."""

    def test_returns_metadata_for_all_techniques(self):
        """Test that metadata includes all coherence techniques."""
        metadata = get_settings_metadata()

        assert "seed_control" in metadata
        assert "ip_adapter_reference" in metadata
        assert "ip_adapter_sequential" in metadata
        assert "lora" in metadata
        assert "enhanced_planning" in metadata
        assert "vbench_quality_control" in metadata
        assert "post_processing_enhancement" in metadata
        assert "controlnet" in metadata
        assert "csfd_detection" in metadata

    def test_metadata_includes_required_fields(self):
        """Test that each technique metadata includes required fields."""
        metadata = get_settings_metadata()

        for technique, info in metadata.items():
            assert "enabled" in info
            assert "recommended" in info
            assert "cost_impact" in info
            assert "time_impact" in info
            assert "description" in info
            assert "tooltip" in info

    def test_metadata_has_correct_defaults(self):
        """Test that metadata reflects correct default enabled states."""
        metadata = get_settings_metadata()

        assert metadata["seed_control"]["enabled"] is True
        assert metadata["enhanced_planning"]["enabled"] is True
        assert metadata["vbench_quality_control"]["enabled"] is True
        assert metadata["post_processing_enhancement"]["enabled"] is True
        assert metadata["ip_adapter_reference"]["enabled"] is False
        assert metadata["ip_adapter_sequential"]["enabled"] is False
        assert metadata["lora"]["enabled"] is False
        assert metadata["controlnet"]["enabled"] is False
        assert metadata["csfd_detection"]["enabled"] is False

    def test_metadata_includes_dependencies(self):
        """Test that metadata includes dependency information."""
        metadata = get_settings_metadata()

        # IP-Adapter modes should have requires field
        assert "requires" in metadata["ip_adapter_reference"]
        assert "enhanced_planning" in metadata["ip_adapter_reference"]["requires"]
        assert "requires" in metadata["ip_adapter_sequential"]
        assert "enhanced_planning" in metadata["ip_adapter_sequential"]["requires"]

