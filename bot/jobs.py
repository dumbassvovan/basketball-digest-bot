"""Локальный планировщик (компьютер должен быть включён).

Для запуска без своего ПК — GitHub Actions, файл
.github/workflows/daily-digest.yml (каждый день в 08:00 по Москве).
"""

from __future__ import annotations

import logging
import time

import schedule

from bot.constants import SCHEDULER_POLL_SEC, SCHEDULER_TIME
from bot.logutil import setup_logging
from bot.pipeline import run_pipeline

logger = logging.getLogger(__name__)


def job() -> None:
    """Одна попытка собрать дайджест. Ошибка не убивает цикл расписания."""
    try:
        run_pipeline()
    except Exception:
        logger.exception("Ежедневный запуск не удался, жду следующее время.")


def run_scheduler() -> None:
    """Каждый день в SCHEDULER_TIME запускает пайплайн."""
    setup_logging()
    schedule.every().day.at(SCHEDULER_TIME).do(job)
    logger.info("Планировщик включён, время %s (локальные часы компьютера).", SCHEDULER_TIME)
    while True:
        schedule.run_pending()
        time.sleep(SCHEDULER_POLL_SEC)


if __name__ == "__main__":
    run_scheduler()
