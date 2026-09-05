"""Команда /digest — утренний пост через нейросеть (в личку, не в канал)."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.constants import DIGEST_TOP_LIMIT
from bot.services.digest import compose_morning_digest
from bot.services.telegram_channel import split_telegram_text

logger = logging.getLogger(__name__)


async def digest_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Собирает топ новостей, просит LLM написать пост и присылает его вам."""
    if update.message is None:
        return

    await update.message.reply_text("Собираю топ-10 и пишу дайджест…")
    try:
        post = compose_morning_digest(limit=DIGEST_TOP_LIMIT)
    except Exception as exc:
        logger.warning("Команда /digest: %s", exc)
        await update.message.reply_text(f"Не удалось собрать дайджест: {exc}")
        return

    if not post:
        await update.message.reply_text("Модель вернула пустой ответ.")
        return

    for chunk in split_telegram_text(post):
        await update.message.reply_text(chunk)
