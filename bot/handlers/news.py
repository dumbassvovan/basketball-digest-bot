"""Команда /news — свежие баскетбольные заголовки в личку."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.constants import NEWS_HOURS, NEWS_REPLY_MAX_MESSAGES
from bot.services.rss import NewsItem, fetch_recent_news
from bot.services.telegram_channel import pack_message_blocks

logger = logging.getLogger(__name__)


def _format_item(item: NewsItem) -> str:
    """Одна новость для сообщения в Telegram."""
    published = (
        item.published.strftime("%Y-%m-%d %H:%M UTC")
        if item.published
        else "дата неизвестна"
    )
    link = f"\n{item.link}" if item.link else ""
    return f"• [{item.weight} изд.] {item.title}\n  {item.source} · {published}{link}"


async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отвечает списком новостей за сутки. Ошибки сети не роняют бота."""
    if update.message is None:
        return

    try:
        items = fetch_recent_news(hours=NEWS_HOURS)
    except Exception as exc:
        logger.warning("Команда /news: %s", exc)
        await update.message.reply_text(f"Не удалось загрузить новости: {exc}")
        return

    if not items:
        await update.message.reply_text(
            "За последние 24 часа новостей нет, либо все ленты недоступны. "
            "Проверьте RSS_FEED_URLS в .env."
        )
        return

    chunks = pack_message_blocks(
        [_format_item(item) for item in items],
        max_messages=NEWS_REPLY_MAX_MESSAGES,
    )
    for chunk in chunks:
        await update.message.reply_text(chunk)
