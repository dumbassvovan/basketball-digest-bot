"""Публикация текста в Telegram-канал."""

from __future__ import annotations

import asyncio
import logging
import os

from dotenv import load_dotenv
from telegram import Bot
from telegram.constants import MessageLimit

logger = logging.getLogger(__name__)

PLACEHOLDER_CHANNELS = {"@your_channel", "@your-channel", ""}


def normalize_channel(raw: str) -> str:
    value = raw.strip()
    if not value:
        return value
    if value.startswith("-") or value.lstrip("-").isdigit():
        return value
    if not value.startswith("@"):
        return f"@{value}"
    return value


def _credentials() -> tuple[str, str]:
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    channel = normalize_channel(os.getenv("CHANNEL_USERNAME", ""))
    if not token or token == "your-telegram-bot-token":
        raise RuntimeError("Не задан TELEGRAM_BOT_TOKEN в файле .env.")
    if channel in PLACEHOLDER_CHANNELS:
        raise RuntimeError(
            "Не задан CHANNEL_USERNAME в файле .env. "
            "Укажите username канала, например @my_channel."
        )
    return token, channel


def split_telegram_text(text: str, limit: int = 4000) -> list[str]:
    cap = min(limit, MessageLimit.MAX_TEXT_LENGTH)
    if len(text) <= cap:
        return [text]
    chunks: list[str] = []
    rest = text
    while rest:
        if len(rest) <= cap:
            chunks.append(rest)
            break
        cut = rest.rfind("\n\n", 0, cap)
        if cut < cap // 2:
            cut = rest.rfind("\n", 0, cap)
        if cut < cap // 2:
            cut = cap
        chunks.append(rest[:cut].rstrip())
        rest = rest[cut:].lstrip()
    return chunks


async def _publish_async(text: str) -> list[int]:
    token, channel = _credentials()
    message_ids: list[int] = []
    async with Bot(token) as bot:
        for chunk in split_telegram_text(text):
            message = await bot.send_message(chat_id=channel, text=chunk)
            message_ids.append(message.message_id)
            logger.info(
                "Опубликовано в %s, message_id=%s, символов=%s",
                channel,
                message.message_id,
                len(chunk),
            )
    return message_ids


def publish_to_channel(text: str) -> list[int]:
    """Отправляет пост в канал из CHANNEL_USERNAME. Возвращает id сообщений."""
    if not text.strip():
        raise RuntimeError("Пустой текст: в канал отправлять нечего.")
    logger.info("Публикую пост в канал (%s символов).", len(text))
    return asyncio.run(_publish_async(text))
