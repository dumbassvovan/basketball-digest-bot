"""Чтение RSS через requests + feedparser."""

from __future__ import annotations

import feedparser
import requests
from requests import HTTPError, RequestException

REQUEST_TIMEOUT_SEC = 15


def normalize_feed_url(url: str) -> str:
    """Чинит схемы вида https:/example.com → https://example.com."""
    url = url.strip()
    if url.startswith("https:/") and not url.startswith("https://"):
        return "https://" + url.removeprefix("https:/")
    if url.startswith("http:/") and not url.startswith("http://"):
        return "http://" + url.removeprefix("http:/")
    return url


def parse_feed_urls(raw: str) -> list[str]:
    """Делит RSS_FEED_URLS по запятой и убирает пробелы вокруг ссылок."""
    urls: list[str] = []
    for part in raw.split(","):
        url = normalize_feed_url(part)
        if url:
            urls.append(url)
    return urls


def _fetch_one_feed(feed_url: str, limit: int) -> list[str]:
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


def fetch_headlines(feed_urls: list[str] | tuple[str, ...] | str, limit: int = 5) -> list[str]:
    if isinstance(feed_urls, str):
        urls = parse_feed_urls(feed_urls)
    else:
        urls = [normalize_feed_url(url) for url in feed_urls if url]

    headlines: list[str] = []
    for url in urls:
        try:
            headlines.extend(_fetch_one_feed(url, limit))
        except HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "?"
            print(f"Предупреждение: источник RSS недоступен ({status}): {url}")
        except (RequestException, RuntimeError) as exc:
            print(f"Предупреждение: не удалось загрузить RSS {url}: {exc}")
    return headlines
