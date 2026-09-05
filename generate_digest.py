"""Собрать утренний дайджест и вывести в консоль.

    source .venv/bin/activate
    python generate_digest.py
"""

from __future__ import annotations

import sys

from bot.services.digest import compose_morning_digest


def main() -> int:
    try:
        print(compose_morning_digest(limit=10))
    except Exception as exc:  # noqa: BLE001 — скрипт для консоли
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
