"""Мелкие преобразования строк: ссылки RSS и имя канала Telegram."""

from __future__ import annotations


def normalize_feed_url(url: str) -> str:
    """Чинит адрес, если потерялся слэш: https:/site → https://site."""
    url = url.strip()
    if url.startswith("https:/") and not url.startswith("https://"):
        return "https://" + url.removeprefix("https:/")
    if url.startswith("http:/") and not url.startswith("http://"):
        return "http://" + url.removeprefix("http:/")
    return url


def parse_feed_urls(raw: str) -> list[str]:
    """Делит строку «ссылка, ссылка» на список и убирает пустые куски."""
    urls: list[str] = []
    for part in raw.split(","):
        url = normalize_feed_url(part)
        if url:
            urls.append(url)
    return urls


def normalize_channel(raw: str) -> str:
    """Приводит имя канала к виду @name. Числовой id (чат) не трогает."""
    value = raw.strip()
    if not value:
        return value
    if value.startswith("-") or value.lstrip("-").isdigit():
        return value
    if not value.startswith("@"):
        return f"@{value}"
    return value
