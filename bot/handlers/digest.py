"""Команда /digest — утренний пост через LLM."""

from telegram import Update
from telegram.ext import ContextTypes

from bot.services.digest import compose_morning_digest

TELEGRAM_MESSAGE_LIMIT = 4000


def _chunks(text: str) -> list[str]:
    if len(text) <= TELEGRAM_MESSAGE_LIMIT:
        return [text]
    parts: list[str] = []
    rest = text
    while rest:
        parts.append(rest[:TELEGRAM_MESSAGE_LIMIT])
        rest = rest[TELEGRAM_MESSAGE_LIMIT:]
    return parts


async def digest_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    await update.message.reply_text("Собираю топ-10 и пишу дайджест…")
    try:
        post = compose_morning_digest(limit=10)
    except Exception as exc:  # noqa: BLE001 — показываем ошибку пользователю
        await update.message.reply_text(f"Не удалось собрать дайджест: {exc}")
        return

    if not post:
        await update.message.reply_text("Модель вернула пустой ответ.")
        return

    for chunk in _chunks(post):
        await update.message.reply_text(chunk)
