"""Проверка RSS-лент из .env до запуска бота.

Запуск из корня проекта:
    source .venv/bin/activate
    python check_rss.py
"""

from __future__ import annotations

import os
import sys
from urllib.parse import urlparse

from dotenv import load_dotenv
import feedparser

from bot.services.rss import parse_feed_urls


def site_name(url: str, feed_title: str = "") -> str:
    title = feed_title.strip()
    if title:
        return title
    host = urlparse(url).netloc
    return host.removeprefix("www.") or url


def check_feed(url: str) -> tuple[bool, str]:
    parsed = feedparser.parse(
        url,
        request_headers={"User-Agent": "telegram-bot-rss-check/0.1"},
    )
    count = len(parsed.entries)
    name = site_name(url, str(parsed.feed.get("title") or ""))

    if parsed.bozo and count == 0:
        error = parsed.bozo_exception or "лента пустая или это не RSS"
        return False, f"❌ Ошибка: {name}, {error}"

    return True, f"✅ Успех: {name}, найдено {count} новостей"


def main() -> int:
    load_dotenv()
    raw = os.getenv("RSS_FEED_URLS") or os.getenv("RSS_FEED_URL") or ""
    urls = parse_feed_urls(raw)

    if not urls:
        print("В .env нет RSS_FEED_URLS. Добавьте ссылки через запятую.")
        return 1

    print(f"Проверяю {len(urls)} лент из .env:\n")
    failures = 0
    for url in urls:
        print(f"→ {url}")
        try:
            ok, line = check_feed(url)
        except Exception as exc:  # noqa: BLE001 — скрипт должен дойти до всех лент
            ok = False
            host = site_name(url)
            line = f"❌ Ошибка: {host}, {exc}"
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
