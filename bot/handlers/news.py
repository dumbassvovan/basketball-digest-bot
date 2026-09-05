"""Команда /news — заголовки из RSS за последние 24 часа."""

from telegram import Update
from telegram.ext import ContextTypes

from bot.services.rss import fetch_recent_news

TELEGRAM_MESSAGE_LIMIT = 4000


def _format_item(item) -> str:
    published = (
        item.published.strftime("%Y-%m-%d %H:%M UTC")
        if item.published
        else "дата неизвестна"
    )
    link = f"\n{item.link}" if item.link else ""
    return f"• {item.title}\n  {item.source} · {published}{link}"


async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    items = fetch_recent_news(hours=24)
    if not items:
        await update.message.reply_text(
            "За последние 24 часа новостей нет, либо все ленты недоступны. "
            "Проверьте RSS_FEED_URLS в .env."
        )
        return

    chunks: list[str] = []
    current = ""
    for item in items:
        block = _format_item(item)
        if current and len(current) + 2 + len(block) > TELEGRAM_MESSAGE_LIMIT:
            chunks.append(current)
            current = block
        else:
            current = f"{current}\n\n{block}" if current else block
    if current:
        chunks.append(current)

    for chunk in chunks[:3]:
        await update.message.reply_text(chunk)
