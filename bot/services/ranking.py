"""Ключевые слова и похожесть заголовков (cosine similarity).

Зачем: из ленты выкидываем не-баскетбол и поднимаем сюжеты,
которые повторили несколько изданий.
"""

from __future__ import annotations

import math
import os
import re
from collections import Counter

from bot.constants import DEFAULT_SIMILARITY_THRESHOLD, ENV_KEYWORDS, ENV_SIMILARITY

# Слова, по которым узнаём баскетбольную тему (можно переопределить в .env).
DEFAULT_KEYWORDS = (
    "nba",
    "нба",
    "wnba",
    "баскетбол",
    "basketball",
    "basket",
    "евролига",
    "euroleague",
    "eurocup",
    "еврокубок",
    "втб",
    "vtb",
    "fiba",
    "фиба",
    "ncaa",
    "единая лига",
    "united league",
    "цска",
    "cska",
)

# Короткие слова, которые не помогают понять тему («в», «the»…).
STOPWORDS = {
    "the",
    "a",
    "an",
    "of",
    "in",
    "on",
    "to",
    "for",
    "and",
    "or",
    "with",
    "from",
    "by",
    "at",
    "is",
    "are",
    "as",
    "after",
    "over",
    "into",
    "и",
    "в",
    "во",
    "на",
    "с",
    "со",
    "по",
    "за",
    "для",
    "это",
    "как",
    "что",
    "от",
    "из",
    "к",
    "о",
    "об",
    "про",
    "не",
}

TOKEN_RE = re.compile(r"[a-zа-яё0-9]+", re.IGNORECASE)
MIN_TOKEN_LENGTH = 3


def parse_keywords(raw: str | None = None) -> tuple[str, ...]:
    """Список тем: из .env NEWS_KEYWORDS или встроенный набор."""
    text = (raw if raw is not None else os.getenv(ENV_KEYWORDS, "")).strip()
    if not text:
        return DEFAULT_KEYWORDS
    return tuple(part.strip().casefold() for part in text.split(",") if part.strip())


def _keyword_forms(keyword: str) -> tuple[str, ...]:
    """Добавляет короткую основу, чтобы «Евролиги» находило «евролига»."""
    forms = [keyword]
    if len(keyword) >= 5 and keyword[-1] in "аяью":
        stem = keyword[:-1]
        if stem not in forms:
            forms.append(stem)
    return tuple(forms)


def matches_keywords(text: str, keywords: tuple[str, ...] | None = None) -> bool:
    """True, если в тексте есть хотя бы одно ключевое слово."""
    haystack = text.casefold()
    words = keywords if keywords is not None else parse_keywords()
    for keyword in words:
        if keyword and any(form in haystack for form in _keyword_forms(keyword)):
            return True
    return False


def title_tokens(title: str) -> list[str]:
    """Режет заголовок на слова, выкидывает короткие и стоп-слова."""
    tokens: list[str] = []
    for token in TOKEN_RE.findall(title.casefold()):
        if len(token) < MIN_TOKEN_LENGTH or token in STOPWORDS:
            continue
        tokens.append(token)
    return tokens


def title_vector(title: str) -> Counter[str]:
    """Счётчик слов заголовка — «вектор» для сравнения похожести."""
    return Counter(title_tokens(title))


def cosine_similarity(left: Counter[str], right: Counter[str]) -> float:
    """Число от 0 до 1: насколько два заголовка похожи по составу слов."""
    if not left or not right:
        return 0.0
    dot = sum(left[token] * right[token] for token in set(left) & set(right))
    if dot == 0:
        return 0.0
    norm_left = math.sqrt(sum(value * value for value in left.values()))
    norm_right = math.sqrt(sum(value * value for value in right.values()))
    if norm_left == 0 or norm_right == 0:
        return 0.0
    return dot / (norm_left * norm_right)


def similarity_threshold() -> float:
    """Порог похожести из .env или значение по умолчанию."""
    raw = os.getenv(ENV_SIMILARITY, "").strip()
    if not raw:
        return DEFAULT_SIMILARITY_THRESHOLD
    try:
        value = float(raw)
    except ValueError:
        return DEFAULT_SIMILARITY_THRESHOLD
    return min(max(value, 0.0), 1.0)


def same_source(left: str, right: str) -> bool:
    """Один и тот же сайт? Тогда пару для веса не считаем."""
    return left.strip().casefold() == right.strip().casefold()
