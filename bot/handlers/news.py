"""Команда /news — заголовки из RSS."""

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import get_settings
from bot.services.rss import fetch_headlines


async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    settings = get_settings()
    headlines = fetch_headlines(settings.rss_feed_urls)

    if not headlines:
        await update.message.reply_text(
            "Не удалось получить новости ни из одного источника. "
            "Проверьте RSS_FEED_URLS в .env."
        )
        return

    await update.message.reply_text("\n\n".join(headlines))
