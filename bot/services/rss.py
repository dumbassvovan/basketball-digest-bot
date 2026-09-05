"""Чтение RSS через requests + feedparser."""

from __future__ import annotations

import feedparser
import requests

REQUEST_TIMEOUT_SEC = 15


def fetch_headlines(feed_url: str, limit: int = 5) -> list[str]:
    response = requests.get(
        feed_url,
        timeout=REQUEST_TIMEOUT_SEC,
        headers={"User-Agent": "telegram-bot-rss/0.1"},
    )
    response.raise_for_status()
    parsed = feedparser.parse(response.content)
    if parsed.bozo and not parsed.entries:
        raise RuntimeError(f"Не удалось прочитать RSS: {feed_url}")

    headlines: list[str] = []
    for entry in parsed.entries[:limit]:
        title = getattr(entry, "title", "").strip() or "(без заголовка)"
        link = getattr(entry, "link", "").strip()
        headlines.append(f"• {title}\n  {link}" if link else f"• {title}")
    return headlines
