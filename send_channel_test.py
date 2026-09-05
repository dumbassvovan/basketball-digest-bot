"""Отправка тестового сообщения в Telegram-канал.

Нужны переменные в .env:
    TELEGRAM_BOT_TOKEN=...
    CHANNEL_USERNAME=@your_channel

Бот должен быть администратором канала с правом публиковать сообщения.

Запуск из корня проекта:
    source .venv/bin/activate
    python send_channel_test.py
"""

from __future__ import annotations

import asyncio
import os
import sys

from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError


def normalize_channel(raw: str) -> str:
    value = raw.strip()
    if not value:
        return value
    if value.startswith("-") or value.lstrip("-").isdigit():
        return value
    if not value.startswith("@"):
        return f"@{value}"
    return value


async def send_test() -> None:
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    channel = normalize_channel(os.getenv("CHANNEL_USERNAME", ""))

    if not token or token == "your-telegram-bot-token":
        raise RuntimeError("Не задан TELEGRAM_BOT_TOKEN в файле .env.")
    if not channel or channel in {"@your_channel", "@your-channel"}:
        raise RuntimeError(
            "Не задан CHANNEL_USERNAME в файле .env. "
            "Укажите username канала, например @my_channel."
        )

    async with Bot(token) as bot:
        message = await bot.send_message(
            chat_id=channel,
            text="Привет, это тест",
        )

    print(
        f"Сообщение отправлено в {channel} "
        f"(message_id={message.message_id})."
    )


def main() -> int:
    try:
        asyncio.run(send_test())
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
