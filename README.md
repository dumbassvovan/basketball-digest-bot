# Telegram-бот на Python

Каркас проекта: структура пакетов, зависимости и загрузка токенов из `.env`.

## Структура

```
.
├── bot/
│   ├── __init__.py
│   ├── __main__.py      # python -m bot
│   ├── app.py           # запуск polling
│   ├── config.py        # чтение .env
│   ├── handlers/        # команды Telegram
│   └── services/        # RSS и OpenAI
├── .env.example         # шаблон секретов (можно коммитить)
├── .env                 # ваши токены (не коммитится)
├── .gitignore
├── requirements.txt
└── README.md
```

## Как установить зависимости

Нужен Python 3.10 или новее.

1. Создайте виртуальное окружение в корне проекта:

```bash
python3 -m venv .venv
```

2. Активируйте его:

```bash
# Linux / macOS
source .venv/bin/activate

# Windows (cmd)
.venv\Scripts\activate.bat
```

3. Обновите pip и установите пакеты из `requirements.txt`:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

В файл входят: `python-telegram-bot`, `feedparser`, `requests`, `openai`, `python-dotenv`, `schedule`.

Проверка, что пакеты на месте:

```bash
pip show python-telegram-bot feedparser requests openai python-dotenv schedule
```

## Токены в `.env`

1. Скопируйте шаблон (если файла `.env` ещё нет):

```bash
cp .env.example .env
```

2. Откройте `.env` и подставьте значения:

- `TELEGRAM_BOT_TOKEN` — токен от [@BotFather](https://t.me/BotFather)
- `CHANNEL_USERNAME` — username канала для тестовой публикации (`@my_channel`)
- `OPENAI_API_KEY` — ключ OpenAI (нужен для `/summarize`)
- `RSS_FEED_URLS` — RSS-ленты через запятую для `/news` (битые источники пропускаются)
- `NEWS_KEYWORDS` — необязательный фильтр тем через запятую (по умолчанию NBA, баскетбол, Евролига, ВТБ и близкие слова)

`python-dotenv` подхватывает этот файл при старте бота. Не публикуйте `.env` в git: он уже в `.gitignore`.

## Проверка RSS до запуска бота

```bash
source .venv/bin/activate
python check_rss.py
```

Скрипт читает `RSS_FEED_URLS` из `.env` и для каждой ссылки пишет успех или ошибку.

## Тест публикации в канал

В `.env` укажите `CHANNEL_USERNAME=@ваш_канал`. Бот должен быть администратором канала.

```bash
source .venv/bin/activate
python send_channel_test.py
```

Скрипт отправит в канал текст «Привет, это тест».

## Запуск

```bash
source .venv/bin/activate
python -m bot
```

Команды в Telegram: `/start`, `/help`, `/news`, `/summarize <текст>`.

Библиотека `schedule` добавлена в зависимости на будущее (периодические задачи). Сейчас бот работает через long polling `python-telegram-bot`.
