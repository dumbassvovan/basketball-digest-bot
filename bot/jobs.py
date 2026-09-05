"""Локальный планировщик на schedule (компьютер должен быть включён).

Для запуска без своего ПК используйте GitHub Actions:
.github/workflows/daily-digest.yml — каждый день в 08:00 по Москве.
"""

from __future__ import annotations

import time

import schedule

from bot.logutil import setup_logging
from bot.pipeline import run_pipeline


def job() -> None:
    run_pipeline()


def run_scheduler() -> None:
    setup_logging()
    schedule.every().day.at("08:00").do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    run_scheduler()
