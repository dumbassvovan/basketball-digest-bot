"""Команды /start и /help."""

from telegram import Update
from telegram.ext import ContextTypes

HELP_TEXT = (
    "Команды:\n"
    "/start — приветствие\n"
    "/help — эта справка\n"
    "/news — заголовки из RSS\n"
    "/digest — утренний дайджест через LLM\n"
    "/summarize <текст> — краткий пересказ через OpenAI"
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    await update.message.reply_text(
        "Бот запущен. Напишите /help, чтобы увидеть список команд."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    await update.message.reply_text(HELP_TEXT)
