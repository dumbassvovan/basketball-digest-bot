"""Сборка и запуск Telegram-бота."""

from __future__ import annotations

import logging

from telegram.ext import ApplicationBuilder

from bot.config import get_settings
from bot.handlers import register_handlers

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    settings = get_settings()
    application = (
        ApplicationBuilder()
        .token(settings.telegram_bot_token)
        .build()
    )
    register_handlers(application)
    logger.info("Бот запущен. Ожидаю сообщения в Telegram.")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
