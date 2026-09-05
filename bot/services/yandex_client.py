"""Запрос к YandexGPT через официальный HTTP API.

Документация: POST https://llm.api.cloud.yandex.net/foundationModels/v1/completion
Ключ сервисного аккаунта: заголовок Authorization: Api-Key ...
"""

from __future__ import annotations

import logging

import requests
from requests import RequestException

from bot.config import get_settings
from bot.constants import (
    DEFAULT_CHAT_MAX_TOKENS,
    DEFAULT_CHAT_TEMPERATURE,
    SUMMARIZE_MAX_TOKENS,
    SUMMARIZE_TEMPERATURE,
    YANDEX_COMPLETION_URL,
    YANDEX_GPT_MODEL,
    YANDEX_REQUEST_TIMEOUT_SEC,
)

logger = logging.getLogger(__name__)

SUMMARIZE_SYSTEM = "Кратко перескажи текст на русском, 2–4 предложения."


def complete_chat(
    *,
    system: str,
    user: str,
    temperature: float = DEFAULT_CHAT_TEMPERATURE,
    max_tokens: int = DEFAULT_CHAT_MAX_TOKENS,
) -> str:
    """Отправляет system+user в YandexGPT Lite и возвращает текст ответа."""
    settings = get_settings(require_bot_token=False)
    api_key = settings.yandex_api_key
    folder_id = settings.yandex_folder_id
    if not api_key:
        raise RuntimeError("Не задан YANDEX_API_KEY. Добавьте ключ в .env.")
    if not folder_id:
        raise RuntimeError(
            "Не задан YANDEX_FOLDER_ID. Это ID каталога в Yandex Cloud."
        )

    payload = {
        "modelUri": f"gpt://{folder_id}/{YANDEX_GPT_MODEL}",
        "completionOptions": {
            "stream": False,
            "temperature": temperature,
            "maxTokens": str(max_tokens),
        },
        "messages": [
            {"role": "system", "text": system},
            {"role": "user", "text": user},
        ],
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {api_key}",
        "x-folder-id": folder_id,
    }

    try:
        response = requests.post(
            YANDEX_COMPLETION_URL,
            headers=headers,
            json=payload,
            timeout=YANDEX_REQUEST_TIMEOUT_SEC,
        )
    except RequestException as exc:
        logger.warning("YandexGPT недоступен: %s", exc)
        raise RuntimeError(f"YandexGPT недоступен: {exc}") from exc

    if not response.ok:
        detail = _error_detail(response)
        logger.warning("YandexGPT вернул %s: %s", response.status_code, detail)
        raise RuntimeError(f"YandexGPT вернул ошибку {response.status_code}: {detail}")

    try:
        data = response.json()
        text = data["result"]["alternatives"][0]["message"]["text"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        logger.warning("Непонятный ответ YandexGPT: %s", response.text[:500])
        raise RuntimeError("YandexGPT вернул ответ без текста.") from exc

    return str(text).strip()


def summarize_text(text: str) -> str:
    """Короткий пересказ произвольного текста (команда /summarize)."""
    return complete_chat(
        system=SUMMARIZE_SYSTEM,
        user=text,
        temperature=SUMMARIZE_TEMPERATURE,
        max_tokens=SUMMARIZE_MAX_TOKENS,
    )


def _error_detail(response: requests.Response) -> str:
    """Достаёт человекочитаемое сообщение из ответа Яндекса."""
    try:
        payload = response.json()
    except ValueError:
        return response.text[:400]
    message = payload.get("message") or payload.get("error")
    if isinstance(message, dict):
        message = message.get("message") or str(message)
    return str(message or response.text[:400])
