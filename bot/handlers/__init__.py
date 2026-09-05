"""Подключение команд Telegram к приложению бота."""

from telegram.ext import Application, CommandHandler

from bot.handlers.digest import digest_command
from bot.handlers.news import news_command
from bot.handlers.start import help_command, start_command
from bot.handlers.summarize import summarize_command


def register_handlers(application: Application) -> None:
    """Регистрирует /start, /help, /news, /digest и /summarize."""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("news", news_command))
    application.add_handler(CommandHandler("digest", digest_command))
    application.add_handler(CommandHandler("summarize", summarize_command))
