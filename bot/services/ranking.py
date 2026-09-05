"""Фильтр ключевых слов и вес новости по похожим заголовкам."""

from __future__ import annotations

import math
import os
import re
from collections import Counter

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
DEFAULT_SIMILARITY_THRESHOLD = 0.45


def parse_keywords(raw: str | None = None) -> tuple[str, ...]:
    text = (raw if raw is not None else os.getenv("NEWS_KEYWORDS", "")).strip()
    if not text:
        return DEFAULT_KEYWORDS
    return tuple(part.strip().casefold() for part in text.split(",") if part.strip())


def _keyword_forms(keyword: str) -> tuple[str, ...]:
    forms = [keyword]
    if len(keyword) >= 5 and keyword[-1] in "аяью":
        stem = keyword[:-1]
        if stem not in forms:
            forms.append(stem)
    return tuple(forms)


def matches_keywords(text: str, keywords: tuple[str, ...] | None = None) -> bool:
    haystack = text.casefold()
    words = keywords if keywords is not None else parse_keywords()
    for keyword in words:
        if not keyword:
            continue
        if any(form in haystack for form in _keyword_forms(keyword)):
            return True
    return False


def title_tokens(title: str) -> list[str]:
    tokens: list[str] = []
    for token in TOKEN_RE.findall(title.casefold()):
        if len(token) < 3 or token in STOPWORDS:
            continue
        tokens.append(token)
    return tokens


def title_vector(title: str) -> Counter[str]:
    return Counter(title_tokens(title))


def cosine_similarity(left: Counter[str], right: Counter[str]) -> float:
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
    raw = os.getenv("NEWS_SIMILARITY_THRESHOLD", "").strip()
    if not raw:
        return DEFAULT_SIMILARITY_THRESHOLD
    try:
        value = float(raw)
    except ValueError:
        return DEFAULT_SIMILARITY_THRESHOLD
    return min(max(value, 0.0), 1.0)


def same_source(left: str, right: str) -> bool:
    return left.strip().casefold() == right.strip().casefold()
