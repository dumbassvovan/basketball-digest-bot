"""Утренний дайджест: топ новостей → LLM → готовый пост для Telegram."""

from __future__ import annotations

from collections.abc import Sequence

from bot.services.openai_client import complete_chat
from bot.services.rss import NewsItem, fetch_recent_news

EDITOR_PROMPT = (
    "Ты редактор баскетбольного Telegram-канала. Составь утренний дайджест "
    "из этих новостей. Формат: заголовок + 2–3 предложения сути + ссылка. "
    "Тон — живой, но профессиональный. В начале — дата и приветствие. "
    "Ответ — готовый пост для Telegram, без лишних комментариев."
)


def format_news_for_llm(items: Sequence[NewsItem]) -> str:
    blocks: list[str] = []
    for index, item in enumerate(items, start=1):
        published = (
            item.published.strftime("%Y-%m-%d %H:%M UTC")
            if item.published
            else "дата неизвестна"
        )
        blocks.append(
            f"{index}. {item.title}\n"
            f"Источник: {item.source}\n"
            f"Вес: {item.weight}\n"
            f"Дата: {published}\n"
            f"Ссылка: {item.link or 'нет ссылки'}"
        )
    return "\n\n".join(blocks)


def compose_morning_digest(
    items: Sequence[NewsItem] | None = None,
    *,
    limit: int = 10,
    api_key: str | None = None,
) -> str:
    """Берёт топ-10 новостей, отправляет их в LLM и возвращает готовый пост."""
    ranked = list(items) if items is not None else fetch_recent_news(hours=24)
    top = ranked[:limit]
    if not top:
        raise RuntimeError(
            "Нет новостей для дайджеста. Проверьте RSS_FEED_URLS и NEWS_KEYWORDS."
        )

    user_message = "Новости:\n\n" + format_news_for_llm(top)
    return complete_chat(
        api_key=api_key,
        system=EDITOR_PROMPT,
        user=user_message,
        temperature=0.5,
        max_tokens=2500,
    )
