"""Чтение RSS через requests + feedparser."""

from __future__ import annotations

import logging
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
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NewsItem:
    title: str
    link: str
    published: datetime | None
    source: str
    weight: int = 0
    summary: str = ""


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


def collect_news(
    *,
    hours: int = 24,
    env_var: str = "RSS_FEED_URLS",
) -> list[NewsItem]:
    """Скачивает ленты и оставляет записи за последние `hours` часов (без фильтра тем)."""
    load_dotenv()
    raw = os.getenv(env_var) or os.getenv("RSS_FEED_URL") or ""
    urls = parse_feed_urls(raw)
    if not urls:
        logger.warning("В окружении нет %s.", env_var)
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    items: list[NewsItem] = []

    for url in urls:
        logger.info("Загружаю ленту: %s", url)
        try:
            parsed = _parse_feed(url)
        except HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "?"
            logger.warning("Источник RSS недоступен (%s): %s", status, url)
            continue
        except (RequestException, RuntimeError) as exc:
            logger.warning("Не удалось загрузить RSS %s: %s", url, exc)
            continue

        source = _source_name(parsed, url)
        kept = 0
        for entry in parsed.entries:
            published = _entry_published(entry)
            if published is None or published < cutoff:
                continue
            title = str(entry.get("title") or "").strip() or "(без заголовка)"
            summary = str(entry.get("summary") or entry.get("description") or "")
            link = str(entry.get("link") or "").strip()
            items.append(
                NewsItem(
                    title=title,
                    link=link,
                    published=published,
                    source=source,
                    summary=summary,
                )
            )
            kept += 1
        logger.info("Лента %s: записей за период — %s", source, kept)

    logger.info("Всего собрано за %s ч: %s", hours, len(items))
    return items


def filter_and_rank(items: list[NewsItem]) -> list[NewsItem]:
    """Оставляет баскетбольные темы и считает вес по похожим заголовкам."""
    keywords = parse_keywords()
    kept: list[NewsItem] = []
    for item in items:
        haystack = f"{item.title} {item.summary} {item.source}"
        if matches_keywords(haystack, keywords):
            kept.append(item)
    logger.info(
        "Фильтр ключевых слов (%s): было %s, осталось %s",
        ", ".join(keywords[:6]) + ("…" if len(keywords) > 6 else ""),
        len(items),
        len(kept),
    )
    ranked = _rank_by_similar_sources(kept)
    logger.info("Ранжирование по cosine similarity завершено.")
    return ranked


def fetch_recent_news(
    *,
    hours: int = 24,
    env_var: str = "RSS_FEED_URLS",
) -> list[NewsItem]:
    """Сбор за период + фильтр тем + вес. Список отсортирован по весу."""
    return filter_and_rank(collect_news(hours=hours, env_var=env_var))


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
            summary=item.summary,
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
            logger.warning("Источник RSS недоступен (%s): %s", status, url)
            continue
        except (RequestException, RuntimeError) as exc:
            logger.warning("Не удалось загрузить RSS %s: %s", url, exc)
            continue

        for entry in parsed.entries[:limit]:
            title = str(entry.get("title") or "").strip() or "(без заголовка)"
            link = str(entry.get("link") or "").strip()
            headlines.append(f"• {title}\n  {link}" if link else f"• {title}")
    return headlines
