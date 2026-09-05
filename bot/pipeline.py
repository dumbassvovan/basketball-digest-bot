"""Главный пайплайн: новости → фильтр → дайджест → канал."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from bot.services.digest import compose_morning_digest
from bot.services.rss import NewsItem, collect_news, filter_and_rank
from bot.services.telegram_channel import publish_to_channel

logger = logging.getLogger(__name__)

TOP_LIMIT = 10


def collect_step(*, hours: int = 24) -> list[NewsItem]:
    logger.info("Шаг 1/4: собираю RSS за последние %s ч.", hours)
    items = collect_news(hours=hours)
    logger.info("Собрано новостей за период: %s", len(items))
    return items


def filter_step(items: Sequence[NewsItem], *, limit: int = TOP_LIMIT) -> list[NewsItem]:
    logger.info("Шаг 2/4: фильтрую по ключевым словам и считаю вес.")
    ranked = filter_and_rank(list(items))
    top = ranked[:limit]
    logger.info(
        "После фильтра: %s, в дайджест берём топ-%s (макс. вес %s).",
        len(ranked),
        len(top),
        top[0].weight if top else 0,
    )
    for index, item in enumerate(top, start=1):
        logger.info(
            "  %s. вес=%s | %s | %s",
            index,
            item.weight,
            item.source,
            item.title,
        )
    return top


def summarize_step(items: Sequence[NewsItem]) -> str:
    logger.info("Шаг 3/4: отправляю %s новостей в LLM.", len(items))
    post = compose_morning_digest(items, limit=len(items))
    logger.info("Дайджест готов, символов: %s", len(post))
    return post


def publish_step(post: str) -> list[int]:
    logger.info("Шаг 4/4: публикую дайджест в канал.")
    message_ids = publish_to_channel(post)
    logger.info("Готово. message_id: %s", message_ids)
    return message_ids


def run_pipeline(*, hours: int = 24, limit: int = TOP_LIMIT, dry_run: bool = False) -> str:
    collected = collect_step(hours=hours)
    top = filter_step(collected, limit=limit)
    if not top:
        raise RuntimeError(
            "После фильтра новостей нет. Проверьте RSS_FEED_URLS и NEWS_KEYWORDS."
        )

    if dry_run:
        logger.info("dry-run: суммаризацию и публикацию пропускаю.")
        preview = "\n".join(
            f"{index}. [{item.weight}] {item.title} — {item.link}"
            for index, item in enumerate(top, start=1)
        )
        logger.info("Топ для дайджеста:\n%s", preview)
        return preview

    post = summarize_step(top)
    publish_step(post)
    return post
