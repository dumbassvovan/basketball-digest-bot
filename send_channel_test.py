"""Отправка тестового сообщения в Telegram-канал.

    source .venv/bin/activate
    python send_channel_test.py
"""

from __future__ import annotations

import sys

from bot.services.telegram_channel import publish_to_channel
from telegram.error import TelegramError


def main() -> int:
    try:
        ids = publish_to_channel("Привет, это тест")
        print(f"Сообщение отправлено (message_id={ids}).")
    except TelegramError as exc:
        print(f"Telegram не принял сообщение: {exc}", file=sys.stderr)
        print(
            "Проверьте: бот добавлен в канал как администратор "
            "и CHANNEL_USERNAME указан верно (@имя).",
            file=sys.stderr,
        )
        return 1
    except Exception as exc:  # noqa: BLE001 — показать ошибку в консоли
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
