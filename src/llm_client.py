"""DeepSeek V4 Flash — OpenAI-compatible chat completions."""

from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.request
from typing import Any

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-v4-flash"

_SECRET_KEYS = ("DEEPSEEK_API_KEY", "OPENAI_API_KEY")


def api_key() -> str | None:
    """Read DeepSeek API key from env or Streamlit secrets."""
    for name in _SECRET_KEYS:
        key = os.environ.get(name, "").strip()
        if key:
            return key
    try:
        import streamlit as st

        for name in _SECRET_KEYS:
            key = str(st.secrets.get(name, "")).strip()
            if key:
                return key
    except Exception:
        pass
    return None


def has_api_key() -> bool:
    return bool(api_key())


def _ssl_context() -> ssl.SSLContext:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def call_json(
    user_prompt: str,
    *,
    system_prompt: str = "你是简愈一人食助手。只输出 JSON，不要其他文字。",
    api_key_override: str | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    """Call DeepSeek-v4-flash and parse JSON response."""
    key = api_key_override or api_key()
    if not key:
        raise ValueError("未配置 DEEPSEEK_API_KEY")

    payload = json.dumps(
        {
            "model": DEEPSEEK_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "thinking": {"type": "disabled"},
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        DEEPSEEK_API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout, context=_ssl_context()) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    content = data["choices"][0]["message"]["content"]
    return json.loads(content)
