"""Загрузка настроек из переменных окружения."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    openai_api_key: str
    rss_feed_url: str


def get_settings() -> Settings:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token or token == "your-telegram-bot-token":
        raise RuntimeError(
            "Не задан TELEGRAM_BOT_TOKEN. Скопируйте .env.example в .env "
            "и укажите токен бота от @BotFather."
        )

    return Settings(
        telegram_bot_token=token,
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        rss_feed_url=os.getenv(
            "RSS_FEED_URL",
            "https://news.ycombinator.com/rss",
        ).strip(),
    )
