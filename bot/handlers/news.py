"""Команда /news — заголовки из RSS."""

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import get_settings
from bot.services.rss import fetch_headlines


async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    settings = get_settings()
    try:
        headlines = fetch_headlines(settings.rss_feed_url)
    except Exception as exc:  # noqa: BLE001 — показываем ошибку пользователю
        await update.message.reply_text(f"Не удалось загрузить ленту: {exc}")
        return

    if not headlines:
        await update.message.reply_text("В ленте пока нет записей.")
        return

    await update.message.reply_text("\n\n".join(headlines))
