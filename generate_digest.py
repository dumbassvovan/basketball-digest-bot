"""Собрать утренний дайджест и вывести в консоль (без публикации в канал).

    python generate_digest.py
"""

from __future__ import annotations

import sys

from bot.constants import DIGEST_TOP_LIMIT
from bot.services.digest import compose_morning_digest


def main() -> int:
    """Печатает текст поста или сообщение об ошибке."""
    try:
        print(compose_morning_digest(limit=DIGEST_TOP_LIMIT))
    except Exception as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
