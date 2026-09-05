"""Главный скрипт дайджеста.

Собрать новости → отфильтровать → суммаризировать → опубликовать в канал.

    source .venv/bin/activate
    python main.py

Только сбор и фильтр (без OpenAI и Telegram):

    python main.py --dry-run

Лог пишется в консоль и в logs/digest.log.
"""

from __future__ import annotations

import argparse
import logging
import sys

from bot.logutil import LOG_FILE, setup_logging
from bot.pipeline import run_pipeline

logger = logging.getLogger("main")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Утренний баскетбольный дайджест: RSS → LLM → Telegram-канал.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Только сбор и фильтр, без LLM и публикации.",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="За сколько часов брать новости (по умолчанию 24).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Сколько новостей отдать в LLM (по умолчанию 10).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    log_path = setup_logging()
    logger.info("Старт пайплайна. Лог-файл: %s", log_path.resolve())
    try:
        run_pipeline(hours=args.hours, limit=args.limit, dry_run=args.dry_run)
    except Exception:
        logger.exception("Пайплайн остановился с ошибкой.")
        return 1
    logger.info("Пайплайн завершён успешно.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
