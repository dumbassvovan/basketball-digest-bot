"""Запрос к OpenAI: отправить текст, получить ответ модели."""

from __future__ import annotations

import logging

from openai import OpenAI

from bot.config import get_settings
from bot.constants import (
    DEFAULT_CHAT_MAX_TOKENS,
    DEFAULT_CHAT_TEMPERATURE,
    PLACEHOLDER_OPENAI_KEY,
    SUMMARIZE_MAX_TOKENS,
    SUMMARIZE_TEMPERATURE,
)

logger = logging.getLogger(__name__)

SUMMARIZE_SYSTEM = "Кратко перескажи текст на русском, 2–4 предложения."


def complete_chat(
    *,
    system: str,
    user: str,
    api_key: str | None = None,
    temperature: float = DEFAULT_CHAT_TEMPERATURE,
    max_tokens: int = DEFAULT_CHAT_MAX_TOKENS,
) -> str:
    """Отправляет system+user в ChatGPT и возвращает текст ответа."""
    settings = get_settings(require_bot_token=False)
    key = (api_key or settings.openai_api_key).strip()
    if not key or key == PLACEHOLDER_OPENAI_KEY:
        raise RuntimeError("Не задан OPENAI_API_KEY. Добавьте ключ в файл .env.")

    try:
        client = OpenAI(api_key=key)
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as exc:
        logger.warning("OpenAI не ответил: %s", exc)
        raise RuntimeError(f"OpenAI не ответил: {exc}") from exc

    content = response.choices[0].message.content
    return (content or "").strip()


def summarize_text(api_key: str, text: str) -> str:
    """Короткий пересказ произвольного текста (команда /summarize)."""
    return complete_chat(
        api_key=api_key,
        system=SUMMARIZE_SYSTEM,
        user=text,
        temperature=SUMMARIZE_TEMPERATURE,
        max_tokens=SUMMARIZE_MAX_TOKENS,
    )
