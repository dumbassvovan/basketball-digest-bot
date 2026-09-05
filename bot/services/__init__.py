"""Внешние сервисы: RSS и OpenAI."""

from bot.services.rss import NewsItem, fetch_recent_news

__all__ = ["NewsItem", "fetch_recent_news"]
