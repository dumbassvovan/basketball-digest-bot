"""Команда /summarize — краткий пересказ вашего текста через YandexGPT."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.services.yandex_client import summarize_text

logger = logging.getLogger(__name__)


async def summarize_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Пересказывает текст после команды. Без текста — подсказка, как вызывать."""
    if update.message is None:
        return

    text = " ".join(context.args).strip() if context.args else ""
    if not text:
        await update.message.reply_text(
            "Укажите текст после команды, например:\n"
            "/summarize Python — язык программирования..."
        )
        return

    try:
        summary = summarize_text(text)
    except Exception as exc:
        logger.warning("Команда /summarize: %s", exc)
        await update.message.reply_text(f"Не удалось сделать пересказ: {exc}")
        return

    await update.message.reply_text(summary or "Модель вернула пустой ответ.")
