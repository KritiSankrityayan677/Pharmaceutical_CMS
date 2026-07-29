import json
import re
from typing import Any, Dict

from groq import Groq
from ..config import settings

_client = Groq(api_key=settings.groq_api_key)

MAX_INPUT_CHARS = 6000


def _truncate(text: str, max_chars: int = MAX_INPUT_CHARS) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[... document truncated for processing ...]"


def _extract_json(raw: str) -> Dict[str, Any]:
    cleaned = re.sub(r"```(?:json)?", "", raw).strip("` \n\t")
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def chat_json(
    system: str,
    user: str,
    temperature: float = 0.2,
    max_tokens: int = 4000,
) -> Dict[str, Any]:
    resp = _client.chat.completions.create(
        model=settings.groq_model,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system + "\nRespond ONLY with valid JSON."},
            {"role": "user", "content": _truncate(user)},
        ],
    )
    raw = resp.choices[0].message.content
    return _extract_json(raw)


def chat_text(system: str, user: str, temperature: float = 0.3, max_tokens: int = 1024) -> str:
    resp = _client.chat.completions.create(
        model=settings.groq_model,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": _truncate(user)},
        ],
    )
    return resp.choices[0].message.content.strip()