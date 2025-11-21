"""
Tests for ConversationHandler image feedback processing.

Tests cover:
- Image feedback processing with selected indices
- Clip reference parsing (various formats)
- Image modification extraction (brightness, saturation, style)
- Batch feedback handling
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.pipeline.conversation_handler import ConversationHandler, get_conversation_handler
from app.schemas.interactive import ChatMessage
from datetime import datetime


class TestConversationHandlerImageFeedback:
    """Test suite for image feedback processing."""

    @pytest.fixture
    def handler(self):
        """Create ConversationHandler instance for testing."""
        return ConversationHandler(model="gpt-4-turbo")

    @pytest.fixture
    def sample_image_data(self):
        """Sample image data for testing."""
        return {
            "images": [
                {
                    "index": 1,
                    "path": "/output/image_1.png",
                    "url": "/api/v1/outputs/image_1.png",
                    "prompt": "Test prompt 1",
                    "quality_score": 85
                },
                {
                    "index": 2,
                    "path": "/output/image_2.png",
                    "url": "/api/v1/outputs/image_2.png",
                    "prompt": "Test prompt 2",
                    "quality_score": 72
                },
                {
                    "index": 3,
                    "path": "/output/image_3.png",
                    "url": "/api/v1/outputs/image_3.png",
                    "prompt": "Test prompt 3",
                    "quality_score": 90
                }
            ]
        }

    @pytest.fixture
    def sample_conversation_history(self):
        """Sample conversation history."""
        return [
            ChatMessage(
                type="user",
                content="Generate reference images",
                timestamp=datetime.utcnow()
            ),
            ChatMessage(
                type="assistant",
                content="I've generated 3 reference images",
                timestamp=datetime.utcnow()
            )
        ]

    @pytest.mark.asyncio
    async def test_process_image_feedback_with_selected_indices(
        self, handler, sample_image_data, sample_conversation_history
    ):
        """Test processing image feedback with pre-selected indices."""
        feedback = "Make the background brighter"
        selected_indices = [1, 2]

        with patch.object(handler.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            # Mock OpenAI response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "I'll make the backgrounds brighter for images 1 and 2"
            mock_create.return_value = mock_response

            result = await handler.process_image_feedback(
                image_data=sample_image_data,
                feedback=feedback,
                conversation_history=sample_conversation_history,
                selected_indices=selected_indices
            )

            assert result is not None
            assert "response" in result
            assert "modifications" in result
            assert "confidence" in result
            assert "affected_indices" in result
            assert result["affected_indices"] == selected_indices
            assert "brightness" in result["modifications"]
            assert result["modifications"]["brightness"] == "increase"

    @pytest.mark.asyncio
    async def test_process_image_feedback_without_selected_indices(
        self, handler, sample_image_data, sample_conversation_history
    ):
        """Test processing image feedback without pre-selected indices (defaults to all)."""
        feedback = "All images are too dark"

        with patch.object(handler.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "I'll brighten all images"
            mock_create.return_value = mock_response

            result = await handler.process_image_feedback(
                image_data=sample_image_data,
                feedback=feedback,
                conversation_history=sample_conversation_history,
                selected_indices=None
            )

            assert result is not None
            assert "affected_indices" in result
            # Should default to all images when no specific reference
            assert len(result["affected_indices"]) > 0

    @pytest.mark.asyncio
    async def test_process_image_feedback_error_handling(
        self, handler, sample_image_data, sample_conversation_history
    ):
        """Test error handling when OpenAI API fails."""
        feedback = "Make it better"

        with patch.object(handler.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error")

            result = await handler.process_image_feedback(
                image_data=sample_image_data,
                feedback=feedback,
                conversation_history=sample_conversation_history
            )

            # Should return fallback response
            assert result is not None
            assert result["confidence"] == 0.0
            assert "clarify" in result["response"].lower()


class TestClipReferenceParsing:
    """Test suite for clip reference parsing."""

    @pytest.fixture
    def handler(self):
        """Create ConversationHandler instance for testing."""
        return ConversationHandler(model="gpt-4-turbo")

    def test_parse_clip_single_reference(self, handler):
        """Test parsing single clip reference: 'Clip 2'."""
        feedback = "Clip 2 needs more motion blur"
        total_clips = 5

        result = handler._parse_clip_references(feedback, total_clips)

        assert result == [2]

    def test_parse_clip_range_reference(self, handler):
        """Test parsing clip range: 'Clips 1-3'."""
        feedback = "Clips 1-3 need better lighting"
        total_clips = 5

        result = handler._parse_clip_references(feedback, total_clips)

        assert result == [1, 2, 3]

    def test_parse_all_clips_reference(self, handler):
        """Test parsing 'all images' reference."""
        feedback = "all images are too dark"
        total_clips = 3

        result = handler._parse_clip_references(feedback, total_clips)

        assert result == [1, 2, 3]

    def test_parse_ordinal_reference(self, handler):
        """Test parsing ordinal references: 'second clip', 'third image'."""
        test_cases = [
            ("the second clip needs work", [2]),
            ("fix the third image", [3]),
            ("first frame is broken", [1]),
        ]

        for feedback, expected in test_cases:
            result = handler._parse_clip_references(feedback, 5)
            assert result == expected, f"Failed for: {feedback}"

    def test_parse_no_specific_reference_defaults_to_all(self, handler):
        """Test that feedback with no specific reference defaults to all clips."""
        feedback = "needs better color grading"
        total_clips = 4

        result = handler._parse_clip_references(feedback, total_clips)

        # Should default to all clips
        assert result == [1, 2, 3, 4]

    def test_parse_out_of_range_clip_reference(self, handler):
        """Test that out-of-range clip references are handled gracefully."""
        feedback = "Clip 10 is broken"
        total_clips = 3

        result = handler._parse_clip_references(feedback, total_clips)

        # Should return empty list for out-of-range
        assert result == []

    def test_parse_multiple_formats(self, handler):
        """Test parsing various formats."""
        test_cases = [
            ("image 2", 5, [2]),
            ("frame 3", 5, [3]),
            ("clips 2-4", 5, [2, 3, 4]),
            ("every clip", 3, [1, 2, 3]),
            ("all frames", 3, [1, 2, 3]),
        ]

        for feedback, total_clips, expected in test_cases:
            result = handler._parse_clip_references(feedback, total_clips)
            assert result == expected, f"Failed for: {feedback}"


class TestImageModificationExtraction:
    """Test suite for image modification extraction."""

    @pytest.fixture
    def handler(self):
        """Create ConversationHandler instance for testing."""
        return ConversationHandler(model="gpt-4-turbo")

    @pytest.mark.asyncio
    async def test_extract_brightness_modifications(self, handler):
        """Test extraction of brightness adjustments."""
        test_cases = [
            ("make it brighter", "increase"),
            ("increase brightness", "increase"),
            ("make it darker", "decrease"),
            ("dimmer please", "decrease"),
        ]

        for feedback, expected_value in test_cases:
            result = await handler._extract_image_modifications(
                feedback=feedback,
                image_count=3
            )
            assert "brightness" in result
            assert result["brightness"] == expected_value

    @pytest.mark.asyncio
    async def test_extract_saturation_modifications(self, handler):
        """Test extraction of saturation/color adjustments."""
        # Test increase saturation
        result = await handler._extract_image_modifications(
            feedback="more vibrant colors",
            image_count=3
        )
        assert "saturation" in result
        assert result["saturation"] == "increase"

        # Test decrease saturation
        result = await handler._extract_image_modifications(
            feedback="muted colors",
            image_count=3
        )
        assert "saturation" in result
        assert result["saturation"] == "decrease"

    @pytest.mark.asyncio
    async def test_extract_style_modifications(self, handler):
        """Test extraction of style changes."""
        test_cases = [
            ("make it cinematic", "cinematic"),
            ("realistic style", "realistic"),
            ("illustrated look", "illustrated"),
            ("minimalist design", "minimalist"),
            ("dramatic lighting", "dramatic"),
        ]

        for feedback, expected_style in test_cases:
            result = await handler._extract_image_modifications(
                feedback=feedback,
                image_count=3
            )
            assert "style" in result
            assert result["style"] == expected_style

    @pytest.mark.asyncio
    async def test_extract_element_modifications(self, handler):
        """Test extraction of element-specific modifications."""
        test_cases = [
            ("change the background", "modify_background"),
            ("different character outfit", "modify_outfit"),
            ("update the person's clothing", "modify_outfit"),
        ]

        for feedback, expected_key in test_cases:
            result = await handler._extract_image_modifications(
                feedback=feedback,
                image_count=3
            )
            assert expected_key in result
            assert result[expected_key] is True

    @pytest.mark.asyncio
    async def test_extract_multiple_modifications(self, handler):
        """Test extraction of multiple modifications from single feedback."""
        feedback = "make the background brighter and more colorful with cinematic style"

        result = await handler._extract_image_modifications(
            feedback=feedback,
            image_count=3
        )

        assert "brightness" in result
        assert "saturation" in result
        assert "style" in result
        assert result["brightness"] == "increase"
        assert result["saturation"] == "increase"
        assert result["style"] == "cinematic"

    @pytest.mark.asyncio
    async def test_feedback_text_stored(self, handler):
        """Test that raw feedback text is always stored."""
        feedback = "whatever changes"

        result = await handler._extract_image_modifications(
            feedback=feedback,
            image_count=3
        )

        assert "feedback_text" in result
        assert result["feedback_text"] == feedback


class TestConversationHandlerSingleton:
    """Test the global handler singleton."""

    def test_get_conversation_handler_returns_instance(self):
        """Test that get_conversation_handler returns a ConversationHandler instance."""
        handler = get_conversation_handler()

        assert handler is not None
        assert isinstance(handler, ConversationHandler)

    def test_get_conversation_handler_returns_same_instance(self):
        """Test that get_conversation_handler returns the same instance (singleton)."""
        handler1 = get_conversation_handler()
        handler2 = get_conversation_handler()

        assert handler1 is handler2
