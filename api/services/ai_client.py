"""
AI Client - Unified interface for OpenAI, Anthropic, and Volcano (Doubao) APIs.
Lazy initialization with graceful fallback when API keys are unavailable.
"""
import os
import json
import logging
import time
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "doubao-seed-2-0-pro-260215"
FALLBACK_MODEL = "gpt-4o-mini"
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
CACHE_SUPPORTED_MODELS = {"gpt-4o", "gpt-4o-mini", "o1", "o1-mini", "o3", "o3-mini"}
MAX_RETRIES = 3
BASE_DELAY = 1.0
MAX_DELAY = 16.0

_openai_client: Optional["OpenAI"] = None
_anthropic_client: Optional["Anthropic"] = None
_volcano_client: Optional["OpenAI"] = None


def is_openai_key_set() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def is_anthropic_key_set() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY"))


def is_volcano_key_set() -> bool:
    return bool(os.getenv("VOLCANO_API_KEY"))


def is_ai_available() -> bool:
    return is_volcano_key_set() or is_openai_key_set() or is_anthropic_key_set()


def get_openai_client() -> Optional["OpenAI"]:
    global _openai_client
    if _openai_client is not None:
        return _openai_client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI as _OpenAI
    except ImportError:
        return None
    _openai_client = _OpenAI(
        api_key=api_key,
        base_url=os.getenv("OPENAI_BASE_URL"),
        timeout=30.0
    )
    return _openai_client


def get_anthropic_client() -> Optional["Anthropic"]:
    global _anthropic_client
    if _anthropic_client is not None:
        return _anthropic_client
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        from anthropic import Anthropic as _Anthropic
    except ImportError:
        return None
    _anthropic_client = _Anthropic(api_key=api_key, timeout=30.0)
    return _anthropic_client


def get_volcano_client() -> Optional["OpenAI"]:
    global _volcano_client
    if _volcano_client is not None:
        return _volcano_client
    api_key = os.getenv("VOLCANO_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI as _OpenAI
    except ImportError:
        return None
    base_url = os.getenv("VOLCANO_BASE_URL", "https://ark.cn-beijing.volces.com/api/coding")
    _volcano_client = _OpenAI(api_key=api_key, base_url=base_url, timeout=30.0)
    return _volcano_client


def _exponential_backoff(attempt: int) -> float:
    return min(BASE_DELAY * (2 ** attempt), MAX_DELAY)


def chat_completion(
    messages: List[Dict[str, str]],
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 1024,
    response_format: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    """
    Unified chat completion: Volcano (Doubao) → OpenAI → Anthropic.
    Returns None on failure (caller should fall back gracefully).
    """
    # Try Volcano first (highest priority per llm.json config)
    if is_volcano_key_set():
        result = _volcano_chat(messages, model, temperature, max_tokens)
        if result is not None:
            return result

    # Try OpenAI second
    if is_openai_key_set():
        result = _openai_chat(messages, model, temperature, max_tokens, response_format)
        if result is not None:
            return result

    # Try Anthropic last
    if is_anthropic_key_set():
        result = _anthropic_chat(messages, model, temperature, max_tokens)
        if result is not None:
            return result

    return None


def _volcano_chat(
    messages: List[Dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int,
) -> Optional[str]:
    client = get_volcano_client()
    if not client:
        return None

    volcano_model = os.getenv("VOLCANO_MODEL", DEFAULT_MODEL)

    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=volcano_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            error_str = str(e).lower()
            if "401" in error_str or "403" in error_str:
                logger.warning(f"Volcano auth error: {e}")
                return None
            if "429" in error_str:
                logger.warning(f"Volcano rate limit, retry {attempt + 1}/{MAX_RETRIES}")
                time.sleep(_exponential_backoff(attempt))
                continue
            if any(x in error_str for x in ["500", "502", "503", "server error"]):
                logger.warning(f"Volcano server error, retry {attempt + 1}/{MAX_RETRIES}")
                time.sleep(_exponential_backoff(attempt))
                continue
            logger.warning(f"Volcano chat error: {e}")
            return None

    return None


def _openai_chat(
    messages: List[Dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int,
    response_format: Optional[Dict[str, str]],
) -> Optional[str]:
    client = get_openai_client()
    if not client:
        return None

    # Apply prompt caching for system prompt
    chat_messages = []
    for i, msg in enumerate(messages):
        if i == 0 and model in CACHE_SUPPORTED_MODELS:
            chat_messages.append({**msg, "cache_control": {"type": "ephemeral"}})
        else:
            chat_messages.append(msg)

    kwargs: Dict[str, object] = {
        "model": model,
        "messages": chat_messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        kwargs["response_format"] = response_format

    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            error_str = str(e).lower()
            if "401" in error_str or "403" in error_str:
                logger.warning(f"OpenAI auth error: {e}")
                return None
            if "429" in error_str:
                logger.warning(f"OpenAI rate limit, retry {attempt + 1}/{MAX_RETRIES}")
                time.sleep(_exponential_backoff(attempt))
                continue
            if any(x in error_str for x in ["500", "502", "503", "server error"]):
                logger.warning(f"OpenAI server error, retry {attempt + 1}/{MAX_RETRIES}")
                time.sleep(_exponential_backoff(attempt))
                continue
            logger.warning(f"OpenAI chat error: {e}")
            return None

    return None


def _anthropic_chat(
    messages: List[Dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int,
) -> Optional[str]:
    client = get_anthropic_client()
    if not client:
        return None

    system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
    user_msgs = [m["content"] for m in messages if m["role"] == "user"]

    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_msg,
                messages=[{"role": "user", "content": "\n".join(user_msgs)}]
            )
            return response.content[0].text
        except Exception as e:
            error_str = str(e).lower()
            if "401" in error_str or "403" in error_str:
                logger.warning(f"Anthropic auth error: {e}")
                return None
            if "429" in error_str:
                logger.warning(f"Anthropic rate limit, retry {attempt + 1}/{MAX_RETRIES}")
                time.sleep(_exponential_backoff(attempt))
                continue
            logger.warning(f"Anthropic chat error: {e}")
            return None

    return None
