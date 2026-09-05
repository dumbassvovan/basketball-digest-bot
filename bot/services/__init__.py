"""Внешние сервисы: RSS и OpenAI."""

from bot.services.digest import compose_morning_digest
from bot.services.rss import NewsItem, collect_news, fetch_recent_news, filter_and_rank

__all__ = [
    "NewsItem",
    "collect_news",
    "compose_morning_digest",
    "fetch_recent_news",
    "filter_and_rank",
]
