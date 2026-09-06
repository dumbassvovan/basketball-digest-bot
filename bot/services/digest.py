"""Утренний дайджест: топ новостей → нейросеть → готовый пост."""

from __future__ import annotations

from collections.abc import Sequence

from bot.constants import DIGEST_MAX_PER_SOURCE, DIGEST_MAX_TOKENS, DIGEST_TEMPERATURE, DIGEST_TOP_LIMIT, NEWS_HOURS
from bot.services.rss import NewsItem, fetch_recent_news, take_top_stories
from bot.services.yandex_client import complete_chat

# Модель пишет только шапку поста. Список новостей собираем сами:
# заголовок + ссылка, без пересказов — иначе в лимит Telegram не влезает топ-10.
EDITOR_PROMPT = (
    "Игнорируй новости на иностранных языках (английский, греческий и т.д.). "
    "Работай только с русскоязычным контентом. "
    "Все выходные тексты должны быть на грамотном русском языке. "
    "Ты редактор баскетбольного Telegram-канала. "
    "Напиши только короткое вступление к утреннему дайджесту: дата и приветствие, "
    "один-два предложения, живой но профессиональный тон. "
    "Не перечисляй новости, не пиши пересказы, не ставь ссылки — список добавит программа. "
    "Ответ — только вступление, без комментариев."
)


def format_news_for_llm(items: Sequence[NewsItem]) -> str:
    """Краткий список заголовков: модели хватит для тона вступления."""
    return "\n".join(
        f"{index}. {item.title}" for index, item in enumerate(items, start=1)
    )


def format_news_for_telegram(items: Sequence[NewsItem]) -> str:
    """Каждая новость — заголовок и ссылка, без описания."""
    blocks: list[str] = []
    for index, item in enumerate(items, start=1):
        title = item.title.strip() or "(без заголовка)"
        link = (item.link or "").strip()
        if link:
            blocks.append(f"{index}. {title}\n{link}")
        else:
            blocks.append(f"{index}. {title}")
    return "\n\n".join(blocks)


def compose_morning_digest(
    items: Sequence[NewsItem] | None = None,
    *,
    limit: int = DIGEST_TOP_LIMIT,
) -> str:
    """Берёт топ новостей: LLM — вступление, дальше заголовок + ссылка."""
    ranked = list(items) if items is not None else fetch_recent_news(hours=NEWS_HOURS)
    top = take_top_stories(ranked, limit, max_per_source=DIGEST_MAX_PER_SOURCE)
    if not top:
        raise RuntimeError(
            "Нет новостей для дайджеста. Проверьте RSS_FEED_URLS и NEWS_KEYWORDS."
        )

    intro = complete_chat(
        system=EDITOR_PROMPT,
        user="Темы выпуска (не пересказывай, только тон вступления):\n"
        + format_news_for_llm(top),
        temperature=DIGEST_TEMPERATURE,
        max_tokens=DIGEST_MAX_TOKENS,
    ).strip()
    listing = format_news_for_telegram(top)
    if intro:
        return f"{intro}\n\n{listing}"
    return listing
