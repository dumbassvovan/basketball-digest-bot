"""Публикация текста в Telegram-канал и нарезка длинных сообщений."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence

from telegram import Bot
from telegram.constants import MessageLimit
from telegram.error import TelegramError

from bot.config import get_settings
from bot.constants import PLACEHOLDER_BOT_TOKEN, TELEGRAM_MESSAGE_LIMIT
from bot.util import normalize_channel

logger = logging.getLogger(__name__)

PLACEHOLDER_CHANNELS = {"@your_channel", "@your-channel", ""}


def _credentials() -> tuple[str, str]:
    """Токен бота и @канал. Без них публиковать некуда."""
    settings = get_settings(require_bot_token=True)
    token = settings.telegram_bot_token
    channel = normalize_channel(settings.channel_username)
    if not token or token == PLACEHOLDER_BOT_TOKEN:
        raise RuntimeError("Не задан TELEGRAM_BOT_TOKEN в файле .env.")
    if channel in PLACEHOLDER_CHANNELS:
        raise RuntimeError(
            "Не задан CHANNEL_USERNAME в файле .env. "
            "Укажите username канала, например @my_channel."
        )
    return token, channel


def split_telegram_text(text: str, limit: int = TELEGRAM_MESSAGE_LIMIT) -> list[str]:
    """Режет длинный пост на куски, стараясь не рвать абзац посередине."""
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


def pack_message_blocks(
    blocks: Sequence[str],
    *,
    limit: int = TELEGRAM_MESSAGE_LIMIT,
    max_messages: int | None = None,
) -> list[str]:
    """Склеивает короткие блоки в сообщения, пока хватает лимита символов."""
    chunks: list[str] = []
    current = ""
    for block in blocks:
        if current and len(current) + 2 + len(block) > limit:
            chunks.append(current)
            current = block
        else:
            current = f"{current}\n\n{block}" if current else block
    if current:
        chunks.append(current)
    if max_messages is not None:
        return chunks[:max_messages]
    return chunks


async def _publish_async(text: str) -> list[int]:
    """Отправляет один или несколько кусков текста в канал."""
    token, channel = _credentials()
    message_ids: list[int] = []
    try:
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
    except TelegramError as exc:
        logger.warning("Telegram не принял сообщение: %s", exc)
        raise RuntimeError(f"Telegram не принял сообщение: {exc}") from exc
    return message_ids


def publish_to_channel(text: str) -> list[int]:
    """Кладёт пост в канал из CHANNEL_USERNAME. Возвращает id сообщений."""
    if not text.strip():
        raise RuntimeError("Пустой текст: в канал отправлять нечего.")
    logger.info("Публикую пост в канал (%s символов).", len(text))
    return asyncio.run(_publish_async(text))
