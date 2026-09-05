"""Главный скрипт дайджеста: сбор → фильтр → нейросеть → канал.

    python main.py
    python main.py --dry-run
"""

from __future__ import annotations

import argparse
import logging
import sys

from bot.constants import DIGEST_TOP_LIMIT, NEWS_HOURS
from bot.logutil import setup_logging
from bot.pipeline import run_pipeline

logger = logging.getLogger("main")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Разбирает флаги командной строки."""
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
        default=NEWS_HOURS,
        help="За сколько часов брать новости.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DIGEST_TOP_LIMIT,
        help="Сколько новостей отдать в LLM.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Точка входа. 0 — успех, 1 — ошибка (для GitHub Actions)."""
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
