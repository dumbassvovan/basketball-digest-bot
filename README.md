# Telegram-бот на Python

Каркас проекта: RSS → фильтр → LLM-дайджест → публикация в Telegram-канал.

## Главный скрипт

Собирает новости, фильтрует, суммаризирует через LLM и публикует пост в канал.

```bash
source .venv/bin/activate
python main.py
```

Только сбор и фильтр, без OpenAI и Telegram:

```bash
python main.py --dry-run
```

Ход работы пишется в консоль и в файл `logs/digest.log`.

Нужны `TELEGRAM_BOT_TOKEN`, `CHANNEL_USERNAME`, `OPENAI_API_KEY` и `RSS_FEED_URLS` в `.env`. Бот должен быть администратором канала.

## Структура

```
.
├── main.py              # пайплайн: сбор → фильтр → LLM → канал
├── bot/
│   ├── pipeline.py      # шаги пайплайна
│   ├── logutil.py       # лог в файл
│   ├── app.py           # polling-бот (команды в личке)
│   ├── handlers/
│   └── services/
├── logs/digest.log
├── .env.example
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
- `OPENAI_API_KEY` — ключ OpenAI (нужен для `/digest` и `/summarize`)
- `OPENAI_MODEL` — необязательно, по умолчанию `gpt-4o-mini`
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

## Утренний дайджест

Берёт топ-10 новостей (уже с весом) и просит LLM собрать пост для канала:

```bash
source .venv/bin/activate
python generate_digest.py
```

В боте то же самое делает команда `/digest`. Нужен `OPENAI_API_KEY` в `.env`.

## Запуск

```bash
source .venv/bin/activate
python -m bot
```

Команды в личке: `/start`, `/help`, `/news`, `/digest`, `/summarize <текст>`.

Ежедневный запуск пайплайна в 08:00 по Москве лучше делать через GitHub Actions (см. ниже), а не держать `python -m bot.jobs` на своём компьютере.

## Ежедневный запуск в 08:00 по Москве (GitHub Actions)

Компьютер держать включённым не нужно: GitHub сам поднимает виртуальную машину, запускает `python main.py` и выключает её.

Расписание в workflow — cron в **UTC**. Москва постоянно UTC+3, поэтому **08:00 МСК = 05:00 UTC**:

```yaml
cron: "0 5 * * *"
```

Файл: `.github/workflows/daily-digest.yml`.

### Что сделать один раз

1. Залейте этот репозиторий на GitHub (Actions работают в GitHub, не в локальном терминале).
2. Откройте репозиторий → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**.
3. Добавьте секреты (те же значения, что в `.env`):

| Secret | Зачем |
|---|---|
| `TELEGRAM_BOT_TOKEN` | токен бота |
| `OPENAI_API_KEY` | ключ LLM |
| `CHANNEL_USERNAME` | канал, например `@my_channel` |
| `RSS_FEED_URLS` | ленты через запятую |
| `NEWS_KEYWORDS` | необязательно |
| `OPENAI_MODEL` | необязательно, иначе `gpt-4o-mini` |

`.env` в git не кладите: Actions подставляет секреты как переменные окружения.

4. **Settings → Actions → General**: разрешите workflows (для форка может понадобиться Enable workflows).
5. Workflow должен лежать в **ветке по умолчанию** (`main`). Расписание на других ветках GitHub не запускает.

### Как проверить, не дожидаясь утра

1. **Actions** → **Daily digest** → **Run workflow**.
2. Для проверки без публикации в канал включите **dry_run**.
3. После полного прогона в канале должен появиться дайджест. Лог скачивается во вкладке **digest-log** у завершённого job.

Расписание GitHub может сработать с опозданием на несколько минут (иногда до часа) — это ограничение бесплатного cron, не ошибка скрипта.

Публичный репозиторий: минуты Actions бесплатные. Приватный: есть месячный лимит; один запуск занимает около минуты.
