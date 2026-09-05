"""Сборка и запуск Telegram-бота (команды в личке).

Это не публикация в канал. Канал обновляет python main.py / GitHub Actions.
Запуск: python -m bot
"""

from __future__ import annotations

import logging

from telegram.ext import ApplicationBuilder

from bot.config import get_settings
from bot.handlers import register_handlers

logger = logging.getLogger(__name__)


def main() -> None:
    """Включает long polling: бот ждёт сообщения в Telegram."""
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=logging.INFO,
    )
    try:
        settings = get_settings()
    except Exception as exc:
        logger.error("Не удалось прочитать настройки: %s", exc)
        raise

    application = ApplicationBuilder().token(settings.telegram_bot_token).build()
    register_handlers(application)
    logger.info("Бот запущен. Ожидаю сообщения в Telegram.")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
