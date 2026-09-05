"""Чтение настроек из файла .env и переменных окружения.

Секреты (токен бота, ключ YandexGPT) должны жить в .env, а не в коде.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from bot.constants import (
    ENV_BOT_TOKEN,
    ENV_CHANNEL,
    ENV_RSS_URL_LEGACY,
    ENV_RSS_URLS,
    ENV_YANDEX_FOLDER,
    ENV_YANDEX_KEY,
    PLACEHOLDER_BOT_TOKEN,
    PLACEHOLDER_YANDEX_FOLDER,
    PLACEHOLDER_YANDEX_KEY,
)
from bot.util import normalize_channel, parse_feed_urls

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Набор настроек, который нужен боту и пайплайну."""

    telegram_bot_token: str
    yandex_api_key: str
    yandex_folder_id: str
    channel_username: str
    rss_feed_urls: tuple[str, ...]


def _env(name: str, default: str = "") -> str:
    """Читает переменную окружения и обрезает пробелы по краям."""
    return os.getenv(name, default).strip()


def rss_feeds_raw() -> str:
    """Строка со ссылками RSS: новая переменная или старое имя RSS_FEED_URL."""
    return _env(ENV_RSS_URLS) or _env(ENV_RSS_URL_LEGACY)


def get_settings(*, require_bot_token: bool = True) -> Settings:
    """Собирает настройки. Если токена нет — объясняет, что делать."""
    token = _env(ENV_BOT_TOKEN)
    if require_bot_token and (not token or token == PLACEHOLDER_BOT_TOKEN):
        raise RuntimeError(
            "Не задан TELEGRAM_BOT_TOKEN. Скопируйте .env.example в .env "
            "и укажите токен бота от @BotFather."
        )

    yandex_key = _env(ENV_YANDEX_KEY)
    if yandex_key == PLACEHOLDER_YANDEX_KEY:
        yandex_key = ""
    folder_id = _env(ENV_YANDEX_FOLDER)
    if folder_id == PLACEHOLDER_YANDEX_FOLDER:
        folder_id = ""

    return Settings(
        telegram_bot_token=token,
        yandex_api_key=yandex_key,
        yandex_folder_id=folder_id,
        channel_username=normalize_channel(_env(ENV_CHANNEL)),
        rss_feed_urls=tuple(parse_feed_urls(rss_feeds_raw())),
    )
