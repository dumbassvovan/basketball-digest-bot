"""Проверка RSS-лент из .env до запуска бота.

    python check_rss.py
"""

from __future__ import annotations

import sys
from urllib.parse import urlparse

import feedparser

from bot.config import rss_feeds_raw
from bot.util import parse_feed_urls

CHECK_USER_AGENT = "telegram-bot-rss-check/0.1"


def site_name(url: str, feed_title: str = "") -> str:
    """Человекочитаемое имя сайта для строки в консоли."""
    title = feed_title.strip()
    if title:
        return title
    host = urlparse(url).netloc
    return host.removeprefix("www.") or url


def check_feed(url: str) -> tuple[bool, str]:
    """Пробует открыть одну ленту через feedparser."""
    parsed = feedparser.parse(
        url,
        request_headers={"User-Agent": CHECK_USER_AGENT},
    )
    count = len(parsed.entries)
    name = site_name(url, str(parsed.feed.get("title") or ""))

    if parsed.bozo and count == 0:
        error = parsed.bozo_exception or "лента пустая или это не RSS"
        return False, f"❌ Ошибка: {name}, {error}"

    return True, f"✅ Успех: {name}, найдено {count} новостей"


def main() -> int:
    """Печатает результат по каждой ссылке из RSS_FEED_URLS."""
    urls = parse_feed_urls(rss_feeds_raw())
    if not urls:
        print("В .env нет RSS_FEED_URLS. Добавьте ссылки через запятую.")
        return 1

    print(f"Проверяю {len(urls)} лент из .env:\n")
    failures = 0
    for url in urls:
        print(f"→ {url}")
        try:
            ok, line = check_feed(url)
        except Exception as exc:
            ok = False
            line = f"❌ Ошибка: {site_name(url)}, {exc}"
        print(line)
        print()
        if not ok:
            failures += 1

    if failures:
        print(f"Готово: ошибок {failures} из {len(urls)}.")
        return 1
    print("Готово: все ленты открываются.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
