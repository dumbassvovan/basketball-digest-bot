"""Вызовы OpenAI Chat Completions."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from openai import OpenAI

DEFAULT_MODEL = "gpt-4o-mini"


def _api_key(api_key: str | None = None) -> str:
    load_dotenv()
    key = (api_key or os.getenv("OPENAI_API_KEY", "")).strip()
    if not key or key == "your-openai-api-key":
        raise RuntimeError(
            "Не задан OPENAI_API_KEY. Добавьте ключ в файл .env."
        )
    return key


def _model() -> str:
    load_dotenv()
    return os.getenv("OPENAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def complete_chat(
    *,
    system: str,
    user: str,
    api_key: str | None = None,
    temperature: float = 0.4,
    max_tokens: int = 2000,
) -> str:
    client = OpenAI(api_key=_api_key(api_key))
    response = client.chat.completions.create(
        model=_model(),
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    content = response.choices[0].message.content
    return (content or "").strip()


def summarize_text(api_key: str, text: str) -> str:
    return complete_chat(
        api_key=api_key,
        system="Кратко перескажи текст на русском, 2–4 предложения.",
        user=text,
        temperature=0.3,
        max_tokens=300,
    )
