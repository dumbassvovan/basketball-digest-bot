"""Сбор новостей из RSS-лент.

Что делает этот файл:
1. Скачивает ленты из RSS_FEED_URLS.
2. Оставляет новости за последние сутки.
3. Фильтр по баскетбольным словам и расчёт «веса» (сколько других сайтов
   написали похожее) делает filter_and_rank.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import feedparser
import requests
from requests import HTTPError, RequestException

from bot.config import rss_feeds_raw
from bot.constants import NEWS_HOURS, RSS_TIMEOUT_SEC, RSS_USER_AGENT
from bot.services.ranking import (
    cosine_similarity,
    entry_language,
    is_russian_news,
    matches_keywords,
    parse_keywords,
    same_source,
    similarity_threshold,
    title_vector,
)
from bot.util import parse_feed_urls

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NewsItem:
    """Одна новость: заголовок, ссылка, дата, сайт, вес и краткий текст из RSS."""

    title: str
    link: str
    published: datetime | None
    source: str
    weight: int = 0
    summary: str = ""


def _source_name(parsed: feedparser.FeedParserDict, feed_url: str) -> str:
    """Имя источника: заголовок ленты или адрес сайта."""
    title = str(parsed.feed.get("title") or "").strip()
    if title:
        return title
    host = urlparse(feed_url).netloc.removeprefix("www.")
    return host or feed_url


def _entry_published(entry: feedparser.FeedParserDict) -> datetime | None:
    """Дата новости из RSS. Если даты нет или она битая — возвращает None."""
    parsed_time = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed_time:
        return None
    try:
        return datetime(*parsed_time[:6], tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def _parse_feed(feed_url: str) -> feedparser.FeedParserDict:
    """Скачивает XML ленты и разбирает его через feedparser."""
    response = requests.get(
        feed_url,
        timeout=RSS_TIMEOUT_SEC,
        headers={"User-Agent": RSS_USER_AGENT},
    )
    response.raise_for_status()
    parsed = feedparser.parse(response.content)
    if parsed.bozo and not parsed.entries:
        error = parsed.bozo_exception or "лента пустая или это не RSS"
        raise RuntimeError(str(error))
    return parsed


def _items_from_feed(
    parsed: feedparser.FeedParserDict,
    source: str,
    cutoff: datetime,
) -> list[NewsItem]:
    """Достаёт из одной ленты свежие русскоязычные новости."""
    feed_language = str(parsed.feed.get("language") or parsed.feed.get("lang") or "")
    items: list[NewsItem] = []
    skipped_lang = 0
    for entry in parsed.entries:
        published = _entry_published(entry)
        if published is None or published < cutoff:
            continue
        title = str(entry.get("title") or "").strip() or "(без заголовка)"
        summary = str(entry.get("summary") or entry.get("description") or "")
        language = entry_language(entry, feed_language)
        if not is_russian_news(title, summary, language):
            skipped_lang += 1
            continue
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
    if skipped_lang:
        logger.info(
            "Лента %s: пропущено нерусских записей — %s",
            source,
            skipped_lang,
        )
    return items


def collect_news(*, hours: int = NEWS_HOURS) -> list[NewsItem]:
    """Скачивает все ленты. Сломанный сайт пропускает и пишет предупреждение."""
    urls = parse_feed_urls(rss_feeds_raw())
    if not urls:
        logger.warning("В окружении нет RSS_FEED_URLS.")
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
        except (RequestException, RuntimeError, OSError) as exc:
            logger.warning("Не удалось загрузить RSS %s: %s", url, exc)
            continue
        except Exception as exc:  # лента странная — не роняем весь сбор
            logger.warning("Неожиданная ошибка RSS %s: %s", url, exc)
            continue

        source = _source_name(parsed, url)
        from_feed = _items_from_feed(parsed, source, cutoff)
        items.extend(from_feed)
        logger.info("Лента %s: записей за период — %s", source, len(from_feed))

    logger.info("Всего собрано за %s ч: %s", hours, len(items))
    return items


def filter_and_rank(items: list[NewsItem]) -> list[NewsItem]:
    """Оставляет баскетбол и ставит вес по похожим заголовкам на других сайтах."""
    keywords = parse_keywords()
    kept = [
        item
        for item in items
        if matches_keywords(f"{item.title} {item.summary} {item.source}", keywords)
    ]
    shown = ", ".join(keywords[:6]) + ("…" if len(keywords) > 6 else "")
    logger.info(
        "Фильтр ключевых слов (%s): было %s, осталось %s",
        shown,
        len(items),
        len(kept),
    )
    ranked = _rank_by_similar_sources(kept)
    logger.info("Ранжирование по cosine similarity завершено.")
    return ranked


def fetch_recent_news(*, hours: int = NEWS_HOURS) -> list[NewsItem]:
    """Полный путь: сбор → фильтр → вес. Список от новых/важных к остальным."""
    return filter_and_rank(collect_news(hours=hours))


def _pair_weights(items: list[NewsItem]) -> list[int]:
    """Для каждой новости: сколько похожих заголовков на других сайтах."""
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
    return weights


def _rank_by_similar_sources(items: list[NewsItem]) -> list[NewsItem]:
    """Вешает вес на новости и сортирует: сначала больший вес, потом свежее."""
    weights = _pair_weights(items)
    ranked = [
        replace(item, weight=weights[index]) for index, item in enumerate(items)
    ]
    ranked.sort(
        key=lambda item: (
            item.weight,
            item.published or datetime.min.replace(tzinfo=timezone.utc),
        ),
        reverse=True,
    )
    return ranked
