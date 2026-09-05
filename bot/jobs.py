"""Пример периодических задач на schedule.

python-telegram-bot работает асинхронно (polling). schedule удобен
для отдельных скриптов (например, рассылка дайджеста раз в час).
Не смешивайте blocking schedule.run_pending() с Application.run_polling()
в одном потоке без отдельного цикла.
"""

from __future__ import annotations

import time

import schedule

from bot.config import get_settings
from bot.services.rss import fetch_headlines


def log_headlines() -> None:
    settings = get_settings()
    for line in fetch_headlines(settings.rss_feed_url):
        print(line)


def run_scheduler() -> None:
    schedule.every().hour.do(log_headlines)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    run_scheduler()
