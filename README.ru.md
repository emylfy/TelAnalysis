<div align="right">

[English](README.md) · **Русский**

</div>

# TelAnalysis

[![CI](https://github.com/emylfy/TelAnalysis/actions/workflows/ci.yml/badge.svg)](https://github.com/emylfy/TelAnalysis/actions/workflows/ci.yml)
![Python 3.11–3.14](https://img.shields.io/badge/python-3.11--3.14-blue.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)
![Built with React + FastAPI](https://img.shields.io/badge/built%20with-React%20%2B%20FastAPI-61DAFB.svg)

> Локальное веб-приложение для анализа Telegram-чатов из экспорта — работает полностью на твоей машине. Кидаешь `result.json`, получаешь heatmap-ы, граф связей, wordcloud, reply latency, sentiment-арки и разбивки по участникам. React-SPA, которую same-origin раздаёт FastAPI-бэкенд; данные не покидают устройство.

<p align="center">
  <img src="docs/screenshots/group-01-overview.png" alt="Вкладка Overview — KPI, hero-блок, дневная активность, пиковые часы" width="900">
</p>

## Что внутри

Читает экспорт Telegram Desktop (отдельный чат или весь архив) и рендерит интерактивный дашборд. Табы адаптируются под тип чата — каналы получают broadcast-метрики, группы — граф связей и Per-user, личные переписки — парную аналитику.

> **Рекомендуется JSON**: в окне экспорта переключи формат с дефолтного *HTML* на *Machine-readable JSON*. **HTML тоже принимается** (путь к папке экспорта или `messages.html`), но он беднее: в HTML от Telegram нет ID участников, поэтому вкладки «Сеть» и «По участникам» в группах менее точны (приложение предупредит при загрузке). В любом случае экспорт — функция Telegram Desktop; мобильные клиенты и нативный клиент для macOS экспорт переписки не умеют.

Поддерживаются оба формата экспорта:
- **Один чат** — `Настройки → Экспорт переписки`
- **Весь архив** — `Настройки → Продвинутые настройки → Экспорт данных Telegram` → после загрузки появится селектор чатов

UI на **EN / RU** (переключатель в шапке). Содержимое чата не трогается — wordcloud-ы и превью сообщений показывают исходный язык.

## Фичи

| Таб | Что в нём |
| --- | --- |
| **Overview** | KPI-карточки (сообщения, участники, days active, медиа, минуты голосовых), area-chart активности по дням, calendar heatmap (год × неделя × день, с переключателем «по количеству / писали-нет»), hour × weekday heatmap, топ эмодзи, распределение reply latency, отдельная Q&A latency |
| **Network** | Интерактивный force-directed граф (drag / zoom / hover, толщина рёбер по частоте, цвет — Louvain communities), глубина reply-цепочек, матрица «кто кому отвечает». Для маленьких чатов — bar chart. Edges/nodes экспортируются в CSV для Gephi |
| **Words** | Wordcloud + топ слов + виртуализованная таблица, биграммы/триграммы, трекер мата по юзеру (`попаданий / 100 сообщений`), индекс уникального лексикона, извлечение email-ов и телефонов |
| **Channel** | Broadcast-wordcloud и частотный анализ для каналов |
| **Per-user** | Дневная timeline юзера, его hour × weekday heatmap, топ эмодзи, любимые sticker-эмодзи, reply latency, топ слов с wordcloud, radar «манера речи» (длина сообщений, доля вопросов, доля эмодзи, доля реплаев), самые длинные монологи, источники форвардов |
| **Highlights** | Автогенерированные карточки в стиле «Spotify Wrapped», юбилейные milestones, распределение длин разговоров, топ-10 самых длинных сессий |

Опциональный **sentiment-анализ** на `rubert-tiny2-russian-sentiment` — sentiment-скор по юзеру, sentiment-over-time, sentiment по часам и дням недели.

<table>
  <tr>
    <td width="50%"><img src="docs/screenshots/group-02-network.png" alt="Network — force-directed граф с community detection"></td>
    <td width="50%"><img src="docs/screenshots/group-03-words.png" alt="Words — wordcloud и топ-фразы"></td>
  </tr>
  <tr>
    <td width="50%"><img src="docs/screenshots/group-04-per-user.png" alt="Per-user — radar манеры речи и timeline"></td>
    <td width="50%"><img src="docs/screenshots/personal-01-sentiment.png" alt="Sentiment over time — арка отношений в 1-на-1"></td>
  </tr>
</table>

## Приватность

Всё работает локально. Дашборд никуда не отправляет данные — ни аналитики, ни телеметрии, ни вызовов внешних API. Сеть нужна только при первом запуске:

- NLTK скачивает корпуса `stopwords` + `punkt_tab` (~10 МБ).
- *Опционально:* если ставишь `requirements-sentiment.txt`, HuggingFace при первом обращении подтянет модель `rubert-tiny2-russian-sentiment` (~50 МБ).

После этого приложение работает полностью оффлайн. Никакой телеметрии, аналитики или вызовов внешних API.

## Установка

Требуется **Python 3.11+**. В CI проверяется на 3.11, 3.12, 3.13 и 3.14. Для сборки фронтенда нужен **Node.js 20+** (один раз, см. [Запуск](#запуск)).

### macOS

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

### Linux (Ubuntu / Debian)

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

### Linux (Fedora / RHEL)

```bash
sudo dnf install -y python3 python3-pip python3-virtualenv gcc gcc-c++ make
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Linux (Arch)

```bash
sudo pacman -S --needed python python-pip base-devel
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Windows (10 / 11)

```powershell
# 1. Python 3.11+ — выбери ОДИН способ
winget install -e --id Python.Python.3.12
# или установщик с https://www.python.org/downloads/
#   ✓ на первом экране поставь галку "Add python.exe to PATH"

# 2. venv + зависимости (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Если PowerShell отказывается запускать `Activate.ps1` (`running scripts is disabled`) — разреши user-scope скрипты:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

В Command Prompt вместо этого: `.\.venv\Scripts\activate.bat`. Сборка Python из Microsoft Store тоже работает, но установщик с python.org / winget проще находится в `PATH`.

## Запуск

Один локальный сервер (FastAPI + uvicorn) раздаёт React-SPA и API анализа
same-origin — экспорт читается локально и не покидает машину. Лаунчер собирает
фронтенд при первом запуске, для этого нужен **Node.js 20+**:

```bash
source .venv/bin/activate   # если ещё не активирован
./run.sh                    # при первом запуске собирает SPA, потом раздаёт
```

Открой <http://127.0.0.1:8000>. На стартовом экране вставь путь к своему
`result.json` (или открой демо). Можно передать порт (`./run.sh 9000`) или
форсировать пересборку фронта (`./run.sh --rebuild`).

> **Docker:** `docker compose up --build` (или `docker-compose up --build`, если
> стоит только standalone-бинарь — напр. `brew install docker` без Compose-плагина),
> затем открой <http://127.0.0.1:8000>.
> Образ уже включает SPA и два демо — кнопки **«Демо»** работают из коробки.
> Чтобы анализировать свой экспорт, примонтируй его папку и вставь путь *внутри
> контейнера* — раскомментируй блок `volumes:` в `docker-compose.yml`
> (напр. `- /path/to/export:/data:ro`), затем введи в UI `/data/result.json`.
> Русский сентимент (torch + transformers, ~1ГБ) по умолчанию выключен — встрой
> его сборкой `docker build --build-arg WITH_SENTIMENT=1 .` (или раскомментируй
> `args:` в compose-файле).

Для разработки фронта с hot-reload запусти два dev-сервера отдельно — Vite
проксирует `/api` на бэкенд:

```bash
.venv/bin/uvicorn api.main:app --reload --port 8000   # терминал 1 — API
cd frontend && npm install && npm run dev             # терминал 2 — http://localhost:5173
```

NLTK-данные (`stopwords`, `punkt_tab`) скачаются автоматически при первом запуске анализа слов. Если на macOS первый `nltk.download()` падает с SSL-ошибкой, прогони один раз `/Applications/Python\ 3.x/Install\ Certificates.command` — относится только к python.org installer-у, не к brew-сборке.

### Попробовать без своих данных

Есть генератор двух синтетических экспортов — групповой чат из 7 человек и личный диалог — чисто чтобы посмотреть приложение:

```bash
python3 tools/gen_demo_data.py   # создаёт demo/group_demo.json + demo/personal_demo.json
./run.sh
```

На стартовом экране открой демо или вставь путь:
```
demo/group_demo.json       # групповой чат, ~70k сообщений
demo/personal_demo.json    # 1-на-1, ~18k сообщений
```

Содержимое собрано из пулов фраз с фиксированным RNG-сидом, реальных переписок там нет. Файлы в `.gitignore` — регенерируй когда угодно.

## Опциональный sentiment-анализ

Русский / английский сентимент через `rubert-tiny2-russian-sentiment` (~1 ГБ на диске, 50 МБ модель при первом использовании):

```bash
pip install -r requirements-sentiment.txt
```

Перезапусти приложение после установки. Модель не понимает сарказм, шутки и слэнг — числа читай со скепсисом.

## Тесты и линт

```bash
pip install ruff pytest
ruff check .
pytest
```

CI гоняет то же самое на каждый push и PR (`.github/workflows/ci.yml`).

## Источник

Вдохновлено проектом [**TelAnalysis** by Eduard Isaev](https://github.com/krakodjaba/TelAnalysis) ([@e_isaevsan](https://t.me/stdinio)) — спасибо за исходную идею и за то, как разбирать формат экспорта Telegram. Это независимый рерайт: общего UI и архитектуры с оригиналом нет (здесь React-SPA + FastAPI против серверных шаблонов там), а по аналитике он ушёл далеко вперёд.

Чем эта версия отличается:
- React-SPA, которую same-origin раздаёт FastAPI-бэкенд, поверх модульного чистого Python-движка анализа
- Интерактивный force-directed граф ответов с раскраской по Louvain-сообществам; heatmap-ы активности (hour × weekday, calendar)
- Вкладка Per-user (radar манеры речи, reply latency, монологи, sticker-эмодзи, forwards-ratio)
- Русский/английский sentiment (`rubert-tiny2`), MTLD-лексикон, n-граммы фраз, трекер мата
- Глубина reply-цепочек, сессии разговоров, Q&A latency, стрики, юбилеи, highlights в стиле «Spotify Wrapped»
- Поддержка HTML + JSON экспорта, полный архив (много чатов), EN/RU UI, тесты и CI

## Лицензия

MIT — см. [`LICENSE`](LICENSE). TelAnalysis — независимая работа; проект, который её вдохновил, не публикуется под OSI-лицензией, поэтому условия из него не наследуются.
