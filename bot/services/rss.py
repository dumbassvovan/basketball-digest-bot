"""Чтение RSS через requests + feedparser."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import feedparser
import requests
from dotenv import load_dotenv
from requests import HTTPError, RequestException

from bot.services.ranking import (
    cosine_similarity,
    matches_keywords,
    parse_keywords,
    same_source,
    similarity_threshold,
    title_vector,
)

REQUEST_TIMEOUT_SEC = 15
USER_AGENT = "telegram-bot-rss/0.1"


@dataclass(frozen=True)
class NewsItem:
    title: str
    link: str
    published: datetime | None
    source: str
    weight: int = 0


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


def _source_name(parsed: feedparser.FeedParserDict, feed_url: str) -> str:
    title = str(parsed.feed.get("title") or "").strip()
    if title:
        return title
    host = urlparse(feed_url).netloc.removeprefix("www.")
    return host or feed_url


def _entry_published(entry: feedparser.FeedParserDict) -> datetime | None:
    parsed_time = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed_time:
        return None
    try:
        return datetime(*parsed_time[:6], tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def _parse_feed(feed_url: str) -> feedparser.FeedParserDict:
    response = requests.get(
        feed_url,
        timeout=REQUEST_TIMEOUT_SEC,
        headers={"User-Agent": USER_AGENT},
    )
    response.raise_for_status()
    parsed = feedparser.parse(response.content)
    if parsed.bozo and not parsed.entries:
        error = parsed.bozo_exception or "лента пустая или это не RSS"
        raise RuntimeError(str(error))
    return parsed


def fetch_recent_news(
    *,
    hours: int = 24,
    env_var: str = "RSS_FEED_URLS",
) -> list[NewsItem]:
    """Берёт RSS-ссылки из переменной окружения и возвращает новости за период.

    Ссылки в переменной задаются через запятую. Недоступные ленты пропускаются
    с предупреждением в консоль. Остаются материалы про баскетбол (NBA, Евролига,
    ВТБ и др.). Вес — число похожих заголовков в других источниках
    (cosine similarity). Список отсортирован по весу.
    """
    load_dotenv()
    raw = os.getenv(env_var) or os.getenv("RSS_FEED_URL") or ""
    urls = parse_feed_urls(raw)
    if not urls:
        print(f"Предупреждение: в окружении нет {env_var}.")
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    keywords = parse_keywords()
    items: list[NewsItem] = []

    for url in urls:
        try:
            parsed = _parse_feed(url)
        except HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "?"
            print(f"Предупреждение: источник RSS недоступен ({status}): {url}")
            continue
        except (RequestException, RuntimeError) as exc:
            print(f"Предупреждение: не удалось загрузить RSS {url}: {exc}")
            continue

        source = _source_name(parsed, url)
        for entry in parsed.entries:
            published = _entry_published(entry)
            if published is None or published < cutoff:
                continue
            title = str(entry.get("title") or "").strip() or "(без заголовка)"
            summary = str(entry.get("summary") or entry.get("description") or "")
            haystack = f"{title} {summary} {source}"
            if not matches_keywords(haystack, keywords):
                continue
            link = str(entry.get("link") or "").strip()
            items.append(
                NewsItem(
                    title=title,
                    link=link,
                    published=published,
                    source=source,
                )
            )

    return _rank_by_similar_sources(items)


def _rank_by_similar_sources(items: list[NewsItem]) -> list[NewsItem]:
    """+1 к весу за каждый похожий заголовок в другом источнике (cosine similarity)."""
    threshold = similarity_threshold()
    vectors = [title_vector(item.title) for item in items]
    weights = [0] * len(items)

    for i, left in enumerate(items):
        for j in range(i + 1, len(items)):
            right = items[j]
            if same_source(left.source, right.source):
                continue
            if cosine_similarity(vectors[i], vectors[j]) >= threshold:
                weights[i] += 1
                weights[j] += 1

    ranked = [
        NewsItem(
            title=item.title,
            link=item.link,
            published=item.published,
            source=item.source,
            weight=weights[index],
        )
        for index, item in enumerate(items)
    ]
    ranked.sort(
        key=lambda item: (
            item.weight,
            item.published or datetime.min.replace(tzinfo=timezone.utc),
        ),
        reverse=True,
    )
    return ranked


def fetch_headlines(
    feed_urls: list[str] | tuple[str, ...] | str,
    limit: int = 5,
) -> list[str]:
    if isinstance(feed_urls, str):
        urls = parse_feed_urls(feed_urls)
    else:
        urls = [normalize_feed_url(url) for url in feed_urls if url]

    headlines: list[str] = []
    for url in urls:
        try:
            parsed = _parse_feed(url)
        except HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "?"
            print(f"Предупреждение: источник RSS недоступен ({status}): {url}")
            continue
        except (RequestException, RuntimeError) as exc:
            print(f"Предупреждение: не удалось загрузить RSS {url}: {exc}")
            continue

        for entry in parsed.entries[:limit]:
            title = str(entry.get("title") or "").strip() or "(без заголовка)"
            link = str(entry.get("link") or "").strip()
            headlines.append(f"• {title}\n  {link}" if link else f"• {title}")
    return headlines
