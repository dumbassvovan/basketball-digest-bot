# Telegram-бот на Python

Каркас проекта: RSS → фильтр → LLM-дайджест → публикация в Telegram-канал.

## Главный скрипт

Собирает новости, фильтрует, суммаризирует через LLM и публикует пост в канал.

```bash
source .venv/bin/activate
python main.py
```

Только сбор и фильтр, без YandexGPT и Telegram:

```bash
python main.py --dry-run
```

Ход работы пишется в консоль и в файл `logs/digest.log`.

Нужны `TELEGRAM_BOT_TOKEN`, `CHANNEL_USERNAME`, `YANDEX_API_KEY`, `YANDEX_FOLDER_ID` и `RSS_FEED_URLS` в `.env`. Бот должен быть администратором канала.

## Структура

```
.
├── main.py                 # утренний дайджест в канал
├── bot/
│   ├── constants.py        # лимиты, время, имена переменных
│   ├── config.py           # чтение .env
│   ├── util.py             # разбор ссылок и @канала
│   ├── pipeline.py         # шаги: сбор → фильтр → LLM → канал
│   ├── logutil.py          # лог в файл
│   ├── app.py              # команды бота в личке
│   ├── handlers/           # /start /news /digest /summarize
│   └── services/           # RSS, рейтинг, YandexGPT, публикация
├── logs/digest.log
├── .github/workflows/      # запуск каждый день в 08:00 МСК
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

В файл входят: `python-telegram-bot`, `feedparser`, `requests`, `python-dotenv`, `schedule`.

Проверка, что пакеты на месте:

```bash
pip show python-telegram-bot feedparser requests python-dotenv schedule
```

## Токены в `.env`

1. Скопируйте шаблон (если файла `.env` ещё нет):

```bash
cp .env.example .env
```

2. Откройте `.env` и подставьте значения:

- `TELEGRAM_BOT_TOKEN` — токен от [@BotFather](https://t.me/BotFather)
- `CHANNEL_USERNAME` — username канала (`@my_channel`)
- `YANDEX_API_KEY` — API-ключ сервисного аккаунта Yandex Cloud
- `YANDEX_FOLDER_ID` — ID каталога в Yandex Cloud (как узнать — ниже)
- `RSS_FEED_URLS` — RSS-ленты через запятую (см. список ниже)
- `NEWS_KEYWORDS` — необязательный фильтр тем (русские слова через запятую)

### Русские RSS по баскетболу

Открытых лент мало: у крупных СМИ либо общий спорт, либо старые URL уже не работают. Ниже — то, что отвечает 200 и отдаёт XML на русском по баскетболу (проверка 2026-09).

**Берём в дайджест** (это значение по умолчанию в `.env.example`):

| Источник | URL |
|---|---|
| Eurohoops (русская редакция) | `https://www.eurohoops.net/ru/feed/` |
| Чемпионат | `https://www.championat.com/rss/news/basketball/` |
| Sports.ru, рубрика «Баскетбол» | `https://www.sports.ru/rss/rubric.xml?id=210` |
| Sportbox | `https://news.sportbox.ru/taxonomy/term/45/0/feed` |
| Матч ТВ | `https://matchtv.ru/articles/rss/basketball` |
| Спорт-Экспресс | `https://www.sport-express.ru/services/materials/news/basketball/se/` |
| Basket.ru | `https://www.basket.ru/news/rss` (редирект на `/news/feed/`) |

**Не подключать:**

- `https://www.championat.com/basketball/rss.xml` — HTML, не RSS
- `https://news.sportbox.ru/Vidy_sporta/Basketbol/rss` — 404
- `https://basket.ru/rss.xml` — 404
- `https://rsport.ria.ru/export/rss2/basketball/index.xml` — 404 (есть только общий спорт: `…/export/rss2/index.xml`)
- `https://www.sports.ru/rss/rubric.xml?id=208` — это футбол, не баскетбол
- Ленты Lenta / Газета.Ru / РИА Спорт целиком — смешанный спорт, баскетбола почти нет
- NBA.com, Euroleague.com — английский; бот такие пункты отбрасывает

После смены списка обновите и секрет GitHub Actions `RSS_FEED_URLS`: локальный `.env` туда сам не попадает.

### Как узнать YANDEX_FOLDER_ID

1. Откройте [консоль Yandex Cloud](https://console.yandex.cloud/).
2. Слева вверху выберите нужный **каталог** (folder), не облако целиком.
3. На обзоре каталога найдите поле **Идентификатор** / **ID** — строка вроде `b1gxxxxxxxxxxxxxxxxx`.
4. Либо откройте каталог и посмотрите адрес в браузере:  
   `https://console.yandex.cloud/folders/<ВОТ_ЭТОТ_ID>/...`

Ключ `YANDEX_API_KEY` создаётся в том же каталоге: **Сервисные аккаунты** → ваш аккаунт → **API-ключи** → создать ключ. У сервисного аккаунта должна быть роль на Foundation Models, например `ai.languageModels.user`.

`python-dotenv` подхватывает этот файл при старте бота. Не публикуйте `.env` в git: он уже в `.gitignore`.

## Запуск локально

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
| `YANDEX_API_KEY` | API-ключ YandexGPT |
| `YANDEX_FOLDER_ID` | ID каталога Yandex Cloud |
| `CHANNEL_USERNAME` | канал, например `@my_channel` |
| `RSS_FEED_URLS` | ленты через запятую |
| `NEWS_KEYWORDS` | необязательно |

`.env` в git не кладите: Actions подставляет секреты как переменные окружения.

4. **Settings → Actions → General**: разрешите workflows (для форка может понадобиться Enable workflows).
5. Workflow должен лежать в **ветке по умолчанию** (`main`). Расписание на других ветках GitHub не запускает.

### Как проверить, не дожидаясь утра

1. **Actions** → **Daily digest** → **Run workflow**.
2. Для проверки без публикации в канал включите **dry_run**.
3. После полного прогона в канале должен появиться дайджест. Лог скачивается во вкладке **digest-log** у завершённого job.

Расписание GitHub может сработать с опозданием на несколько минут (иногда до часа) — это ограничение бесплатного cron, не ошибка скрипта.

Публичный репозиторий: минуты Actions бесплатные. Приватный: есть месячный лимит; один запуск занимает около минуты.
