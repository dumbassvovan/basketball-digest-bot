"""Внешние сервисы: RSS и OpenAI."""

from bot.services.digest import compose_morning_digest
from bot.services.rss import NewsItem, fetch_recent_news

__all__ = ["NewsItem", "compose_morning_digest", "fetch_recent_news"]
