"""Команда /summarize — краткий пересказ через OpenAI."""

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import get_settings
from bot.services.openai_client import summarize_text


async def summarize_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if update.message is None:
        return

    text = " ".join(context.args).strip() if context.args else ""
    if not text:
        await update.message.reply_text(
            "Укажите текст после команды, например:\n"
            "/summarize Python — язык программирования..."
        )
        return

    settings = get_settings()
    try:
        summary = summarize_text(settings.openai_api_key, text)
    except Exception as exc:  # noqa: BLE001 — показываем ошибку пользователю
        await update.message.reply_text(f"Не удалось сделать пересказ: {exc}")
        return

    await update.message.reply_text(summary or "Модель вернула пустой ответ.")
