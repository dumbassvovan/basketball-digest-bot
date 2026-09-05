"""Отправка тестового сообщения в Telegram-канал.

    python send_channel_test.py
"""

from __future__ import annotations

import sys

from bot.services.telegram_channel import publish_to_channel


def main() -> int:
    """Шлёт «Привет, это тест». Нужны токен бота и CHANNEL_USERNAME."""
    try:
        ids = publish_to_channel("Привет, это тест")
        print(f"Сообщение отправлено (message_id={ids}).")
    except Exception as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        print(
            "Проверьте: бот добавлен в канал как администратор "
            "и CHANNEL_USERNAME указан верно (@имя).",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
