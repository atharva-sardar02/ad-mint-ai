import logging
from typing import List, Dict, Any

from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

if not settings.OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not configured.")

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def call_chat_model(
    messages: List[Dict[str, str]],
    model: str,
    temperature: float = 0.3,
    max_output_tokens: int = 1500,
    stream: bool = False,
) -> str:
    """
    Multi-message–safe wrapper for GPT-4.1 / GPT-5 chat models.

    - Requires messages=[{role, content}, ...]
    - For GPT-5-family models, leaves temperature at default (1.0)
      and uses max_completion_tokens.
    """

    if not isinstance(messages, list):
        raise TypeError("call_chat_model() requires messages=[...]")

    if not messages:
        raise ValueError("messages must contain at least one message.")

    for i, msg in enumerate(messages):
        if "role" not in msg or "content" not in msg:
            raise ValueError(f"Message #{i} missing required keys: role, content")
        if msg["role"] not in ("system", "user", "assistant"):
            raise ValueError(f"Invalid role in message #{i}: {msg['role']}")
        if not isinstance(msg["content"], str):
            raise TypeError(f"Message #{i} content must be a string.")

    MODELS_USE_COMPLETION_TOKENS = ["gpt-5", "gpt-5-turbo", "gpt-5o"]
    MODELS_TEMPERATURE_RESTRICTED = ["gpt-5", "gpt-5-turbo", "gpt-5o"]

    request_params: Dict[str, Any] = {
        "model": model,
        "messages": messages,
    }

    if model not in MODELS_TEMPERATURE_RESTRICTED:
        request_params["temperature"] = temperature

    if model in MODELS_USE_COMPLETION_TOKENS:
        request_params["max_completion_tokens"] = max_output_tokens
    else:
        request_params["max_tokens"] = max_output_tokens

    try:
        if stream:
            response_text = ""
            stream_resp = await client.chat.completions.create(
                **request_params,
                stream=True,
            )
            async for chunk in stream_resp:
                if chunk.choices and chunk.choices[0].delta:
                    content = chunk.choices[0].delta.content
                    if content:
                        response_text += content

            logger.info(f"[LLM][{model}] Stream complete.")
            return response_text

        resp = await client.chat.completions.create(
            **request_params,
            stream=False,
        )

        if not resp.choices:
            logger.error(f"No choices in model response.")
            raise ValueError(f"{model} returned no choices.")

        text = resp.choices[0].message.content
        if not text:
            logger.error(f"{model} returned empty content.")
            raise ValueError(f"{model} returned empty content.")

        prompt_tokens = getattr(resp.usage, "prompt_tokens", None)
        completion_tokens = getattr(resp.usage, "completion_tokens", None)

        logger.info(
            f"[LLM][{model}] Tokens: prompt={prompt_tokens}, completion={completion_tokens}"
        )

        return text

    except Exception as e:
        logger.exception(f"[LLM ERROR][{model}] {e}")
        raise


def parse_json_str(raw: str) -> Dict[str, Any]:
    """Strict JSON parser with helpful errors."""
    import json
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON from model: {e}\nRaw:\n{raw}") from e