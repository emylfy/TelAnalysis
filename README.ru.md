<div align="right">

[English](README.md) · **Русский**

</div>

# TelAnalysis

[![CI](https://github.com/emylfy/TelAnalysis/actions/workflows/ci.yml/badge.svg)](https://github.com/emylfy/TelAnalysis/actions/workflows/ci.yml)
![Python 3.11–3.14](https://img.shields.io/badge/python-3.11--3.14-blue.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)
![Built with React + FastAPI](https://img.shields.io/badge/built%20with-React%20%2B%20FastAPI-61DAFB.svg)

> Принимает экспорт Telegram-чата и показывает его как интерактивный дашборд: heatmap-ы активности, граф ответов, wordcloud-ы, разбивки по участникам и опциональный sentiment. Работает локально в браузере — без загрузки куда-либо и без аккаунта.

<p align="center">
  <img src="docs/screenshots/group-01-overview.png" alt="Вкладка Overview — KPI, hero-блок, дневная активность, пиковые часы" width="900">
</p>

## Что внутри

Читает экспорт Telegram Desktop (отдельный чат или весь архив) и рендерит интерактивный дашборд. Табы адаптируются под тип чата: каналы получают broadcast-метрики, группы — граф связей и Per-user, личные переписки — парную аналитику.

> **Рекомендуется JSON**: в окне экспорта формат лучше переключить с дефолтного *HTML* на *Machine-readable JSON*. **HTML тоже принимается** (путь к папке экспорта или `messages.html`), но он беднее: в HTML от Telegram нет ID участников, поэтому вкладки «Сеть» и «По участникам» в группах менее точны (приложение предупредит при загрузке). В любом случае экспорт — функция Telegram Desktop; мобильные клиенты и нативный клиент для macOS экспорт переписки не умеют.

Поддерживаются оба формата экспорта:
- **Один чат** — `Настройки → Экспорт переписки`
- **Весь архив** — `Настройки → Продвинутые настройки → Экспорт данных Telegram` → после загрузки появится селектор чатов и [менеджер чатов](#управление-архивом-освобождение-места) для подчистки архива

UI на **EN / RU** (переключатель в шапке). Содержимое чата не трогается — wordcloud-ы и превью сообщений показывают исходный язык.

## Чем интересен

Несколько вещей, которых не даст обычный счётчик сообщений:

- **Кто кому отвечает быстрее** — для личных чатов статистика ответов *по каждому направлению*: медиана и 90-й перцентиль времени ответа, плюс доля ответов в пределах 5 / 30 / 60 минут.
- **Сколько вы реально проговорили** — сообщения группируются в сессии разговоров, поэтому видно настоящее время в переписке, а не только число сообщений.
- **Кто начинает и кто закрывает** — доля начатых разговоров и «последнего слова» перед паузой по каждому участнику.
- **Граф ответов с авто-сообществами** — для групп: Louvain-кластеры и «портрет чата» с хабами, мостами и магнитами ответов.
- **Любимые стикеры — настоящими картинками** — восстановлены из экспорта и показаны изображениями, а не emoji-тегами.
- **Слова, которые вас выдают** — log-odds отличающие слова, которые выделяют каждого в личной переписке.
- **Юбилейные вехи** — 100 / 365 / 1000 дней, 10k / 100k сообщений: когда порог пройден и какой следующий.
- **Лидерборд мата** — попаданий на 100 сообщений с морфологическим сопоставлением корней (народная фича; в чисто английских чатах просто не сработает).

## Фичи

Overview открывается **recap'ом в стиле «Wrapped»**: короткая сводка, sparkline активности, ключевые числа (сообщения, участники, дней в эфире, медиа, минуты голосовых), юбилейные вехи и карточки-хайлайты (пиковый час, самый громкий день, топ-эмодзи, самый длинный стрик).

| Таб | Что в нём |
| --- | --- |
| **Overview** | График активности по дням и calendar heatmap по годам, hour×weekday heatmap с подписями про пиковый час и сов, overlap по часам для 1-на-1. Сессии разговоров, разбивка медиа и голосовых, топ доменов ссылок и эмодзи, reply latency (вопрос→ответ) и самые длинные монологи. |
| **Network** | Интерактивный force-directed граф (drag, zoom, hover): толщина и стрелки рёбер — число и направление ответов, цвет узла — Louvain-сообщество, плюс «портрет чата» (хабы, мосты, магниты), таблица ролей и глубина reply-цепочек. Маленькие чаты показываются bar chart-ом; узлы и рёбра экспортируются в CSV для Gephi. |
| **Words** | Wordcloud (по всему чату или по юзеру), топ слов (график и таблица), частые фразы (биграммы и триграммы), богатство лексикона (MTLD) по участникам и извлечённые email-ы и телефоны. |
| **Channel** | Wordcloud и частотный анализ слов для broadcast-каналов. |
| **Per-user** | Отдельная страница на участника — персона-карточка, ключевые плитки (сообщения, доля последнего слова, слов на сообщение, доля вопросов, скорость ответа), radar тона, timeline и heatmap-ы и много чего ещё (полный список ниже). |

<details>
<summary>Всё на странице участника</summary>

- Персона-карточка с трейт-чипами (сова / жаворонок, кратко / многословно, инициатор / отвечающий, быстро / медленно)
- Ключевые плитки: сообщения, доля последнего слова, слов на сообщение, доля вопросов, доля реплаев
- Radar тона против среднего по чату (вопросы, восклицания, CAPS, реплаи)
- Дневная timeline и hour×weekday heatmap
- Распределения по времени суток и длине сообщений
- Скорость ответа и reciprocity (по направлениям в 1-на-1)
- Стрики активности и самые длинные молчания
- Как часто начинает разговоры и доля форвардов
- Характерные фразы; топ слов, эмодзи и стикеров
- Log-odds отличающие слова (что выделяет его в 1-на-1)
- Лидерборд мата (`попаданий / 100 сообщений`)
</details>

Опциональный **sentiment-анализ** (`rubert-tiny2-russian-sentiment`, RU/EN — [ставится отдельно](#опциональный-sentiment-анализ)) добавляет арку sentiment-over-time, линии тона по участникам, разбивку по часам и дням недели и самые позитивные и негативные сообщения — на вкладках **Words** и **Per-user**.

<p align="center"><b>Network</b> — force-directed граф ответов с авто-сообществами</p>

<p align="center">
  <img src="docs/screenshots/group-02-network.png" alt="Network — force-directed граф с community detection" width="900">
</p>

<p align="center"><b>Words</b> — wordcloud, топ слов и частые фразы</p>

<p align="center">
  <img src="docs/screenshots/group-03-words.png" alt="Words — wordcloud и топ-фразы" width="900">
</p>

<p align="center"><b>Per-user</b> — страница на участника: персона, radar тона, timeline-ы</p>

<p align="center">
  <img src="docs/screenshots/group-04-per-user.png" alt="Per-user — radar манеры речи и timeline" width="900">
</p>

<p align="center"><b>Sentiment</b> — арка отношений во времени (опциональная модель)</p>

<p align="center">
  <img src="docs/screenshots/personal-01-sentiment.png" alt="Sentiment over time — арка отношений в 1-на-1" width="900">
</p>

## Управление архивом (освобождение места)

Полный архив Telegram — это десятки гигабайт медиа, которые вы никогда не откроете. Для JSON-архивов с правом записи кнопка **Manage chats** ранжирует чаты по размеру на диске (с разбивкой по медиа) и даёт удалять или *слимить* их — выкидывая тяжёлое медиа, но оставляя текст. Удаления уезжают в обратимую `.telanalysis_trash/` и освобождаются только после **Empty trash**. Менеджер правит папку на месте — укажите копию, чтобы сохранить оригинал.

## Приватность

Всё работает на локальной машине — без аккаунта, без загрузки куда-либо, без телеметрии. В сеть уходит только разовая загрузка при первом запуске: корпуса NLTK `stopwords` + `punkt_tab` (~10 МБ) и — **только если вы сами включили** — модель сентимента (см. [Опциональный sentiment-анализ](#опциональный-sentiment-анализ)). После этого приложение полностью работает оффлайн.

## Установка

Требуется **Python 3.11+**. В CI проверяется на 3.11, 3.12, 3.13 и 3.14. Для сборки фронтенда нужен **Node.js 20+** (один раз, см. [Запуск](#запуск)).

Базовая установка одинакова на всех ОС:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Платформенные нюансы (системные пакеты, Apple Silicon, Windows PowerShell):

<details>
<summary><b>macOS</b></summary>

```bash
# 1. Python 3.11+ через Homebrew (если ещё нет)
brew install python@3.12

# 2. venv + зависимости
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Apple Silicon (M1/M2/M3): всё работает из коробки — у `torch`, `wordcloud` и прочих есть готовые arm64-wheel'ы, ничего собирать не надо.
</details>

<details>
<summary><b>Linux (Ubuntu / Debian)</b></summary>

```bash
# 1. Системные пакеты — Python 3.11+, venv, build-essential для редких сборок
sudo apt update
sudo apt install -y python3 python3-venv python3-pip build-essential

# Если в дистрибутиве Python <3.11 (Ubuntu 22.04 и старше):
#   sudo add-apt-repository ppa:deadsnakes/ppa
#   sudo apt install -y python3.12 python3.12-venv

# 2. venv + зависимости
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
</details>

<details>
<summary><b>Linux (Fedora / RHEL)</b></summary>

```bash
sudo dnf install -y python3 python3-pip python3-virtualenv gcc gcc-c++ make
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
</details>

<details>
<summary><b>Linux (Arch)</b></summary>

```bash
sudo pacman -S --needed python python-pip base-devel
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
</details>

<details>
<summary><b>Windows (10 / 11)</b></summary>

```powershell
# 1. Python 3.11+ — любой из способов
winget install -e --id Python.Python.3.12
# или установщик с https://www.python.org/downloads/
#   ✓ на первом экране нужна галка "Add python.exe to PATH"

# 2. venv + зависимости (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Если PowerShell отказывается запускать `Activate.ps1` (`running scripts is disabled`) — нужно разрешить user-scope скрипты:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

В Command Prompt вместо этого: `.\.venv\Scripts\activate.bat`. Сборка Python из Microsoft Store тоже работает, но установщик с python.org / winget проще находится в `PATH`.
</details>

## Запуск

Один локальный сервер (FastAPI + uvicorn) раздаёт React-SPA и API анализа
на одном origin. Лаунчер собирает фронтенд при первом запуске, для этого нужен
**Node.js 20+**:

```bash
source .venv/bin/activate   # если ещё не активирован
./run.sh                    # при первом запуске собирает SPA, потом раздаёт
```

Приложение откроется на <http://127.0.0.1:8000>. На стартовом экране
указывается путь к `result.json` (или открывается демо). Можно передать порт
(`./run.sh 9000`) или форсировать пересборку фронта (`./run.sh --rebuild`).

<details>
<summary><b>Docker</b></summary>

`docker compose up --build` (или `docker-compose up --build`, если стоит только standalone-бинарь — напр. `brew install docker` без Compose-плагина), затем открыть <http://127.0.0.1:8000>. Образ уже включает SPA и два демо — кнопки **«Демо»** работают из коробки.

Чтобы анализировать собственный экспорт, нужно примонтировать его папку и указать путь *внутри контейнера*: раскомментировать блок `volumes:` в `docker-compose.yml` (напр. `- /path/to/export:/data:ro`) и ввести в UI `/data/result.json`.

Русский сентимент (torch + transformers, ~1 ГБ) по умолчанию выключен — включается сборкой `docker build --build-arg WITH_SENTIMENT=1 .` (или раскомментированием `args:` в compose-файле).
</details>

Для разработки фронта с hot-reload два dev-сервера запускаются отдельно — Vite
проксирует `/api` на бэкенд:

```bash
.venv/bin/uvicorn api.main:app --reload --port 8000   # терминал 1 — API
cd frontend && npm install && npm run dev             # терминал 2 — http://localhost:5173
```

NLTK-данные (`stopwords`, `punkt_tab`) скачаются автоматически при первом запуске анализа слов. Если на macOS первый `nltk.download()` падает с SSL-ошибкой, достаточно один раз запустить `/Applications/Python\ 3.x/Install\ Certificates.command` — относится только к python.org installer-у, не к brew-сборке.

### Попробовать без собственных данных

Два синтетических экспорта лежат прямо в репозитории, поэтому кнопки **«Демо»** на стартовом экране работают сразу после клонирования — ничего качать или генерировать не нужно (они же зашиты в Docker-образ):

```
demo/group_demo.json       # групповой чат, ~70k сообщений
demo/personal_demo.json    # 1-на-1, ~18k сообщений
```

Перегенерировать их (или поправить профили участников) можно генератором:

```bash
python3 tools/gen_demo_data.py   # перезаписывает demo/group_demo.json + demo/personal_demo.json
```

Содержимое собрано из пулов фраз с фиксированным RNG-сидом, реальных переписок там нет.

## Опциональный sentiment-анализ

Русский / английский сентимент через `rubert-tiny2-russian-sentiment`. Зависимости `torch` + `transformers` занимают ~1 ГБ на диске; сами веса модели — ~50 МБ, качаются при первом обращении:

```bash
pip install -r requirements-sentiment.txt
```

После установки приложение нужно перезапустить. Сама модель не понимает шутки и слэнг, а оценку на явных маркерах сарказма (🤡 🙄, концевой `/s`) приложение приглушает — но это грубая эвристика, числа стоит читать со скепсисом.

**Другая модель.** По умолчанию модель ориентирована на русский. Чтобы оценивать другой язык, задайте `TLA_SENTIMENT_MODEL` — любую модель sequence-classification с HuggingFace, среди меток которой есть *positive* / *negative* — и перезапустите:

```bash
# мультиязычная (английский, испанский, …)
TLA_SENTIMENT_MODEL=cardiffnlp/twitter-xlm-roberta-base-sentiment ./run.sh
# только английский
TLA_SENTIMENT_MODEL=distilbert-base-uncased-finetuned-sst-2-english ./run.sh
```

## Скриншоты

Картинки дашборда в этом README сгенерированы, а не сняты руками — после изменений в UI их достаточно перегенерировать:

```bash
pip install playwright            # dev-only, специально не в requirements.txt
python -m playwright install chromium
python tools/screenshots.py       # пишет 5 PNG в docs/screenshots/
```

`tools/screenshots.py` гоняет headless Chromium по двум встроенным демо и перезаписывает `docs/screenshots/*.png`. Если сервер ещё не запущен — поднимет его сам; `--only <имя>` обновит один скрин, `--base-url` укажет другой порт. Sentiment-скрин требует опциональную модель (см. выше) — без неё он пропускается.

## Тесты и линт

```bash
pip install ruff pytest
ruff check .
pytest
```

CI гоняет то же самое на каждый push и PR (`.github/workflows/ci.yml`).

## Источник

Вдохновлено проектом [**TelAnalysis** by Eduard Isaev](https://github.com/krakodjaba/TelAnalysis) ([@e_isaevsan](https://t.me/stdinio)) — спасибо за исходную идею и за то, как разбирать формат экспорта Telegram. Это независимый рерайт со своим UI и архитектурой (здесь React-SPA + FastAPI, там серверные шаблоны) и другим, более широким набором аналитики.

## Лицензия

MIT — см. [`LICENSE`](LICENSE). TelAnalysis — независимая работа; проект, который её вдохновил, не публикуется под OSI-лицензией, поэтому условия из него не наследуются.
