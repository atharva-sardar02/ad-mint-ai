"""
Conversation Handler for Interactive Pipeline Feedback

Processes conversational feedback from users and extracts structured modifications
to apply to story/image/storyboard regeneration.

Uses GPT-4 to understand natural language feedback and translate it into
actionable modifications (tone, focus, structure, style changes).
"""

import json
import logging
from typing import Any, Dict, List, Optional

import openai
from app.core.config import settings
from app.schemas.interactive import ChatMessage

logger = logging.getLogger(__name__)


class ConversationHandler:
    """
    Handles conversational feedback processing for interactive pipeline.

    Responsibilities:
    - Extract user intent from conversational feedback
    - Generate appropriate responses explaining planned modifications
    - Convert feedback into structured modifications for regeneration
    - Maintain conversation context
    """

    def __init__(self, model: str = "gpt-4-turbo"):
        """
        Initialize conversation handler.

        Args:
            model: OpenAI model to use for conversation processing
        """
        self.model = model
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info(f"ConversationHandler initialized (model: {model})")

    async def process_story_feedback(
        self,
        story: Dict[str, Any],
        feedback: str,
        conversation_history: List[ChatMessage]
    ) -> Dict[str, Any]:
        """
        Process user feedback about the generated story.

        Args:
            story: Current story output (narrative, script, etc.)
            feedback: User's natural language feedback
            conversation_history: Previous conversation messages

        Returns:
            dict: {
                "response": str - conversational response to user,
                "modifications": dict - structured modifications to apply,
                "confidence": float - confidence in understanding (0-1)
            }
        """
        logger.info(f"Processing story feedback: {feedback[:100]}...")

        # Build conversation context
        messages = self._build_conversation_context(
            stage="story",
            current_output=story,
            conversation_history=conversation_history
        )

        # Add user feedback
        messages.append({
            "role": "user",
            "content": feedback
        })

        try:
            # Call GPT-4 to process feedback
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )

            llm_response = response.choices[0].message.content

            # Extract modifications from response
            modifications = await self._extract_modifications(
                feedback=feedback,
                llm_response=llm_response,
                stage="story"
            )

            logger.info(f"✅ Feedback processed. Modifications: {modifications}")

            return {
                "response": llm_response,
                "modifications": modifications,
                "confidence": 0.85  # TODO: Calculate actual confidence
            }

        except Exception as e:
            logger.error(f"❌ Feedback processing failed: {e}")
            return {
                "response": "I understand you'd like to make changes. Could you please clarify what you'd like to modify?",
                "modifications": {},
                "confidence": 0.0
            }

    async def process_image_feedback(
        self,
        image_data: Dict[str, Any],
        feedback: str,
        conversation_history: List[ChatMessage],
        selected_indices: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Process user feedback about reference images or storyboard images.

        Args:
            image_data: Current image data (includes images list, prompts, metadata)
            feedback: User's natural language feedback
            conversation_history: Previous conversation messages
            selected_indices: Optional list of selected image indices for targeted feedback

        Returns:
            dict: {
                "response": str - conversational response explaining changes,
                "modifications": dict - structured modifications to apply,
                "confidence": float - confidence in understanding (0-1),
                "affected_indices": list[int] - which images will be regenerated
            }
        """
        logger.info(f"Processing image feedback: {feedback[:100]}...")
        if selected_indices:
            logger.info(f"   Selected images: {selected_indices}")

        # Build conversation context
        messages = self._build_conversation_context(
            stage="reference_image",
            current_output=image_data,
            conversation_history=conversation_history
        )

        # Add user feedback with image context
        feedback_with_context = feedback
        if selected_indices:
            feedback_with_context = f"[User selected images: {selected_indices}] {feedback}"

        messages.append({
            "role": "user",
            "content": feedback_with_context
        })

        try:
            # Call GPT-4 to process feedback
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )

            llm_response = response.choices[0].message.content

            # Extract modifications and affected indices
            modifications = await self._extract_image_modifications(
                feedback=feedback,
                llm_response=llm_response,
                selected_indices=selected_indices,
                image_count=len(image_data.get("images", []))
            )

            # Determine which images are affected
            affected_indices = modifications.pop("affected_indices", selected_indices or [])

            logger.info(f"✅ Image feedback processed. Modifications: {modifications}")
            logger.info(f"   Affected images: {affected_indices}")

            return {
                "response": llm_response,
                "modifications": modifications,
                "confidence": 0.85,
                "affected_indices": affected_indices
            }

        except Exception as e:
            logger.error(f"❌ Image feedback processing failed: {e}")
            return {
                "response": "I understand you'd like to make changes to the images. Could you please clarify which images and what modifications you'd like?",
                "modifications": {},
                "confidence": 0.0,
                "affected_indices": selected_indices or []
            }

    async def process_storyboard_feedback(
        self,
        storyboard_data: Dict[str, Any],
        feedback: str,
        conversation_history: List[ChatMessage]
    ) -> Dict[str, Any]:
        """
        Process user feedback about storyboard.

        Args:
            storyboard_data: Current storyboard data
            feedback: User's natural language feedback
            conversation_history: Previous conversation messages

        Returns:
            dict: Response and modifications for storyboard regeneration
        """
        logger.info(f"Processing storyboard feedback: {feedback[:100]}...")

        modifications = await self._extract_storyboard_modifications(feedback)

        return {
            "response": f"I'll update the storyboard with your suggestions",
            "modifications": modifications,
            "confidence": 0.80
        }

    # ========================================================================
    # Internal Helper Methods
    # ========================================================================

    def _build_conversation_context(
        self,
        stage: str,
        current_output: Dict[str, Any],
        conversation_history: List[ChatMessage]
    ) -> List[Dict[str, str]]:
        """
        Build conversation context for GPT-4.

        Args:
            stage: Current pipeline stage
            current_output: Current stage output
            conversation_history: Previous messages

        Returns:
            list: Conversation messages for OpenAI API
        """
        messages = [
            {
                "role": "system",
                "content": self._get_system_prompt(stage)
            }
        ]

        # Add current output as context
        if stage == "story":
            narrative = current_output.get("narrative", "")
            if isinstance(narrative, dict):
                narrative_text = json.dumps(narrative, ensure_ascii=False)
            else:
                narrative_text = str(narrative)
            narrative_preview = narrative_text[:500]
            messages.append({
                "role": "assistant",
                "content": f"I've generated this story:\n\n{narrative_preview}..."
            })

        # Add conversation history
        # Defensive check: ensure conversation_history is a list
        logger.info(f"conversation_history type: {type(conversation_history)}, value: {conversation_history}")

        if isinstance(conversation_history, dict):
            logger.warning("conversation_history is a dict, converting to list of values")
            conversation_history = list(conversation_history.values())
        elif not isinstance(conversation_history, list):
            logger.error(f"conversation_history is unexpected type: {type(conversation_history)}")
            conversation_history = []  # Fallback to empty list

        for msg in conversation_history[-5:]:  # Last 5 messages for context
            if msg.type == "user":
                messages.append({"role": "user", "content": msg.content})
            elif msg.type == "assistant":
                messages.append({"role": "assistant", "content": msg.content})

        return messages

    def _get_system_prompt(self, stage: str) -> str:
        """Get system prompt for a specific stage."""
        prompts = {
            "story": """You are a creative assistant helping users refine video ad stories.
Your role is to understand their feedback and explain what changes you'll make.
Be conversational and helpful. Extract key modifications like:
- Tone changes (humorous, dramatic, inspirational, etc.)
- Focus areas (product benefits, emotional appeal, call-to-action, etc.)
- Structure changes (shorter opening, faster pace, different arc, etc.)
- Style preferences (minimalist, cinematic, energetic, etc.)

Respond naturally and confirm what you understand before regenerating.""",

            "reference_image": """You are an art director helping users refine reference images.
Understand feedback about:
- Visual style (realistic, illustrated, cinematic, etc.)
- Color preferences (vibrant, muted, brand colors, etc.)
- Composition (close-up, wide shot, perspective, etc.)
- Mood (energetic, calm, dramatic, etc.)

Respond conversationally and explain visual changes clearly.""",

            "storyboard": """You are a storyboard artist helping users refine scene breakdowns.
Understand feedback about:
- Scene timing (faster/slower pacing)
- Shot types (close-ups, wide shots, camera movements)
- Transitions (cuts, fades, zooms)
- Scene order or content changes

Respond naturally and confirm the changes you'll make."""
        }
        return prompts.get(stage, "You are a helpful assistant.")

    async def _extract_modifications(
        self,
        feedback: str,
        llm_response: str,
        stage: str
    ) -> Dict[str, Any]:
        """
        Extract structured modifications from feedback.

        This uses GPT-4 again with function calling to get JSON output.
        """
        try:
            # Use GPT-4 function calling to extract structured modifications
            functions = [
                {
                    "name": "extract_story_modifications",
                    "description": "Extract structured modifications from user feedback",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tone": {"type": "string", "description": "Tone change (humorous, dramatic, etc.)"},
                            "focus_areas": {"type": "array", "items": {"type": "string"}, "description": "What to emphasize"},
                            "structure_changes": {"type": "array", "items": {"type": "string"}, "description": "Structure modifications"},
                            "style": {"type": "string", "description": "Overall style change"},
                            "other": {"type": "string", "description": "Other modifications"}
                        }
                    }
                }
            ]

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Extract modifications from this feedback"},
                    {"role": "user", "content": feedback}
                ],
                functions=functions,
                function_call={"name": "extract_story_modifications"},
                temperature=0.3
            )

            function_call = response.choices[0].message.function_call
            if function_call:
                modifications = json.loads(function_call.arguments)
                return {k: v for k, v in modifications.items() if v}  # Remove None values

        except Exception as e:
            logger.warning(f"Structured extraction failed, using heuristics: {e}")

        # Fallback: heuristic extraction
        return self._heuristic_extraction(feedback, stage)

    def _heuristic_extraction(self, feedback: str, stage: str) -> Dict[str, Any]:
        """Fallback heuristic extraction if GPT-4 function calling fails."""
        feedback_lower = feedback.lower()
        modifications = {}

        # Tone detection
        tones = {
            "humor": ["funny", "humorous", "humor", "joke", "playful", "lighthearted"],
            "dramatic": ["dramatic", "intense", "powerful", "bold", "strong"],
            "inspirational": ["inspiring", "motivational", "uplifting", "hopeful"],
            "professional": ["professional", "serious", "formal", "business"]
        }
        for tone, keywords in tones.items():
            if any(keyword in feedback_lower for keyword in keywords):
                modifications["tone"] = tone
                break

        # Focus area detection
        focus_keywords = {
            "product benefits": ["benefit", "feature", "advantage", "value"],
            "emotional appeal": ["emotion", "feel", "heart", "connect"],
            "call to action": ["call to action", "cta", "buy now", "sign up"]
        }
        focus_areas = []
        for focus, keywords in focus_keywords.items():
            if any(keyword in feedback_lower for keyword in keywords):
                focus_areas.append(focus)
        if focus_areas:
            modifications["focus_areas"] = focus_areas

        # Structure detection
        if any(word in feedback_lower for word in ["shorter", "brief", "concise", "quick"]):
            modifications.setdefault("structure_changes", []).append("shorter")
        if any(word in feedback_lower for word in ["longer", "detailed", "elaborate"]):
            modifications.setdefault("structure_changes", []).append("longer")
        if any(word in feedback_lower for word in ["faster", "pace", "quick"]):
            modifications.setdefault("structure_changes", []).append("faster_pace")

        return modifications

    async def _extract_image_modifications(
        self,
        feedback: str,
        llm_response: str = "",
        selected_indices: Optional[List[int]] = None,
        image_count: int = 0
    ) -> Dict[str, Any]:
        """
        Extract modifications for image regeneration.

        Args:
            feedback: User's feedback text
            llm_response: LLM's response (optional)
            selected_indices: Pre-selected image indices
            image_count: Total number of images

        Returns:
            dict: Modifications including affected_indices
        """
        modifications = {}

        # Parse clip references from feedback (if not explicitly selected)
        if not selected_indices:
            clip_indices = self._parse_clip_references(feedback, image_count)
            modifications["affected_indices"] = clip_indices
        else:
            modifications["affected_indices"] = selected_indices

        # Extract visual modification keywords
        feedback_lower = feedback.lower()

        # Brightness/Exposure adjustments
        if any(word in feedback_lower for word in ["brighter", "lighter", "increase brightness"]):
            modifications["brightness"] = "increase"
        elif any(word in feedback_lower for word in ["darker", "dimmer", "decrease brightness"]):
            modifications["brightness"] = "decrease"

        # Color adjustments
        if any(word in feedback_lower for word in ["vibrant", "saturated", "colorful", "vivid"]):
            modifications["saturation"] = "increase"
        elif any(word in feedback_lower for word in ["muted", "desaturated", "less color"]):
            modifications["saturation"] = "decrease"

        # Style changes
        style_keywords = {
            "cinematic": ["cinematic", "film", "movie"],
            "realistic": ["realistic", "photorealistic", "real"],
            "illustrated": ["illustrated", "drawn", "artistic", "painterly"],
            "minimalist": ["minimalist", "simple", "clean"],
            "dramatic": ["dramatic", "bold", "intense"]
        }
        for style, keywords in style_keywords.items():
            if any(keyword in feedback_lower for keyword in keywords):
                modifications["style"] = style
                break

        # Prompt modifications (for regeneration)
        if "background" in feedback_lower:
            modifications["modify_background"] = True
        if "character" in feedback_lower or "person" in feedback_lower:
            modifications["modify_character"] = True
        if "outfit" in feedback_lower or "clothing" in feedback_lower:
            modifications["modify_outfit"] = True

        # Store raw feedback for prompt enhancement
        modifications["feedback_text"] = feedback

        return modifications

    def _parse_clip_references(self, feedback: str, total_clips: int) -> List[int]:
        """
        Parse clip references from user feedback.

        Supports formats like:
        - "Clip 2" or "clip 2" → [2]
        - "Clips 1-3" or "clips 1-3" → [1, 2, 3]
        - "second clip" or "third image" → [2] or [3]
        - "all images" or "all clips" → [1, 2, ..., N]
        - No reference → all clips

        Args:
            feedback: User feedback text
            total_clips: Total number of clips/images

        Returns:
            list[int]: List of clip indices (1-indexed)
        """
        import re

        feedback_lower = feedback.lower()

        # Check for "all" keywords
        if any(word in feedback_lower for word in ["all clips", "all images", "all frames", "every clip", "every image"]):
            return list(range(1, total_clips + 1))

        # Check for range: "clips 1-3" or "images 2-4"
        range_match = re.search(r"(?:clip|image|frame)s?\s+(\d+)\s*-\s*(\d+)", feedback_lower)
        if range_match:
            start, end = int(range_match.group(1)), int(range_match.group(2))
            return list(range(start, min(end + 1, total_clips + 1)))

        # Check for single clip: "clip 2" or "image 3"
        single_match = re.search(r"(?:clip|image|frame)\s+(\d+)", feedback_lower)
        if single_match:
            clip_num = int(single_match.group(1))
            return [clip_num] if 1 <= clip_num <= total_clips else []

        # Check for ordinal: "second clip", "third image", "first frame"
        ordinal_map = {
            "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
            "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10
        }
        for ordinal, num in ordinal_map.items():
            if ordinal in feedback_lower and any(word in feedback_lower for word in ["clip", "image", "frame"]):
                return [num] if num <= total_clips else []

        # Default: if no specific reference, assume all images
        logger.info(f"No specific clip reference found in feedback, defaulting to all ({total_clips}) clips")
        return list(range(1, total_clips + 1))

    async def _extract_storyboard_modifications(self, feedback: str) -> Dict[str, Any]:
        """Extract modifications for storyboard regeneration."""
        # Similar to image modifications but for storyboard context
        return {
            "adjustments": "apply feedback",
            "feedback_text": feedback
        }


# Global handler instance
_handler: Optional[ConversationHandler] = None


def get_conversation_handler() -> ConversationHandler:
    """Get the global conversation handler instance."""
    global _handler
    if _handler is None:
        _handler = ConversationHandler()
    return _handler
