"""Общие числа и тексты проекта.

Чтобы не разбрасывать «магические» значения по файлам:
время дайджеста, лимиты Telegram, модель YandexGPT и т.п. живут здесь.
"""

from __future__ import annotations

# Сколько часов назад ещё считаем новость свежей.
NEWS_HOURS = 24

# Сколько новостей отдаём в нейросеть для утреннего поста.
DIGEST_TOP_LIMIT = 10

# В топ-10 не больше стольких одиночных сюжетов с одного сайта,
# чтобы Sports.ru не забивал весь выпуск. Сюжеты с нескольких изданий проходят всегда.
DIGEST_MAX_PER_SOURCE = 3

# Порог похожести заголовков (0…1). Выше — строже.
DEFAULT_SIMILARITY_THRESHOLD = 0.45

# Сколько секунд ждать ответ RSS-сайта.
RSS_TIMEOUT_SEC = 15

# Подпись, с которой бот стучится на сайты (некоторые ленты режут пустой запрос).
RSS_USER_AGENT = "telegram-bot-rss/0.1"

# Лимит одного сообщения Telegram чуть ниже официальных 4096 символов.
TELEGRAM_MESSAGE_LIMIT = 4000

# Команда /news может прислать несколько сообщений подряд — не больше этого.
NEWS_REPLY_MAX_MESSAGES = 3

# Модель и настройки вызовов YandexGPT Lite.
YANDEX_GPT_MODEL = "yandexgpt-lite"
YANDEX_COMPLETION_URL = (
    "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
)
YANDEX_REQUEST_TIMEOUT_SEC = 60
DIGEST_TEMPERATURE = 0.5
# Вступление короткое: список новостей в пост добавляет код, не модель.
DIGEST_MAX_TOKENS = 400
SUMMARIZE_TEMPERATURE = 0.3
SUMMARIZE_MAX_TOKENS = 300
DEFAULT_CHAT_TEMPERATURE = 0.4
DEFAULT_CHAT_MAX_TOKENS = 2000

# Локальный планировщик (если запускаете python -m bot.jobs на своём ПК).
SCHEDULER_TIME = "08:00"
SCHEDULER_POLL_SEC = 1

# Заглушки из .env.example — считаем, что значение ещё не заполнено.
PLACEHOLDER_BOT_TOKEN = "your-telegram-bot-token"
PLACEHOLDER_YANDEX_KEY = "your-yandex-api-key"
PLACEHOLDER_YANDEX_FOLDER = "your-yandex-folder-id"

# Имена переменных окружения.
ENV_BOT_TOKEN = "TELEGRAM_BOT_TOKEN"
ENV_YANDEX_KEY = "YANDEX_API_KEY"
ENV_YANDEX_FOLDER = "YANDEX_FOLDER_ID"
ENV_CHANNEL = "CHANNEL_USERNAME"
ENV_RSS_URLS = "RSS_FEED_URLS"
ENV_RSS_URL_LEGACY = "RSS_FEED_URL"
ENV_KEYWORDS = "NEWS_KEYWORDS"
ENV_SIMILARITY = "NEWS_SIMILARITY_THRESHOLD"
