<div align="right">

[English](README.md) · **Русский**

</div>

# TelAnalysis

[![CI](https://github.com/emylfy/TelAnalysis/actions/workflows/ci.yml/badge.svg)](https://github.com/emylfy/TelAnalysis/actions/workflows/ci.yml)
![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![License: GPL-3.0](https://img.shields.io/badge/license-GPL--3.0-green.svg)
![Built with Streamlit](https://img.shields.io/badge/built%20with-Streamlit-FF4B4B.svg)

> Streamlit-дашборд для анализа Telegram-чатов из локального экспорта — работает полностью на твоей машине. Кидаешь `result.json`, получаешь heatmap-ы, граф связей, wordcloud, reply latency, sentiment-арки и разбивки по участникам.

<p align="center">
  <img src="docs/screenshots/group-01-overview.png" alt="Вкладка Overview — KPI, hero-блок, дневная активность, пиковые часы" width="900">
</p>

## Что внутри

Читает экспорт Telegram Desktop (отдельный чат или весь архив) и рендерит интерактивный дашборд. Табы адаптируются под тип чата — каналы получают broadcast-метрики, группы — граф связей и Per-user, личные переписки — парную аналитику.

Поддерживаются оба формата экспорта:
- **Один чат** — `Настройки → Экспорт переписки`
- **Весь архив** — `Настройки → Продвинутые настройки → Экспорт данных Telegram` → в сайдбаре появится селектор чатов

UI на **RU / EN** (переключатель в сайдбаре). Содержимое чата не трогается — wordcloud-ы и превью сообщений показывают исходный язык.

## Фичи

| Таб | Что в нём |
| --- | --- |
| **Overview** | KPI-карточки (сообщения, участники, days active, медиа, минуты голосовых), Plotly area-chart активности по дням, calendar heatmap (год × неделя × день, с переключателем «по количеству / писали-нет»), hour × weekday heatmap, топ эмодзи, распределение reply latency, отдельная Q&A latency |
| **Network** | Интерактивный force-directed pyvis-граф (drag / zoom / hover, толщина рёбер по частоте, цвет — Louvain communities), глубина reply-цепочек, матрица «кто кому отвечает». Для маленьких чатов — bar chart. Edges/nodes экспортируются в CSV для Gephi |
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

После этого приложение работает полностью оффлайн. В `.streamlit/config.toml` отключены Deploy-кнопка и телеметрия Streamlit.

## Установка

Требуется **Python 3.10+** (зависимости `pandas 3.x` и `streamlit 1.57+` старее не поддерживают).

### macOS

```bash
# 1. Python 3.10+ через Homebrew (если ещё нет)
brew install python@3.12

# 2. venv + зависимости
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Apple Silicon (M1/M2/M3): всё работает из коробки — у `torch`, `pandas`, `wordcloud` есть готовые arm64-wheel'ы, ничего собирать не надо.

### Linux (Ubuntu / Debian)

```bash
# 1. Системные пакеты — Python 3.10+, venv, build-essential для редких сборок
sudo apt update
sudo apt install -y python3 python3-venv python3-pip build-essential

# Если в дистрибутиве Python <3.10 (Ubuntu 20.04 и старше):
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
# 1. Python 3.10+ — выбери ОДИН способ
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

```bash
source .venv/bin/activate   # если ещё не активирован
streamlit run app.py
```

Открой <http://localhost:8501>. В сайдбаре переключатель **Источник** даёт два режима:

- **Загрузить** (по умолчанию) — перетащи `result.json` в дропзону или кликни и выбери файл. Подходит для экспортов до ~65 МБ.
- **Путь к файлу** — вставь абсолютный или относительный путь (например `demo/group_demo.json`). Заметно быстрее для больших архивов — нет base64-туда-обратно через WebSocket.

После загрузки имя файла свернётся в плашку наверху сайдбара; раскрой её — там кнопка `Загрузить другой файл`. Данные не уходят с твоей машины — см. [Приватность](#приватность).

NLTK-данные (`stopwords`, `punkt_tab`) скачаются автоматически при первом запуске анализа слов. Если на macOS первый `nltk.download()` падает с SSL-ошибкой, прогони один раз `/Applications/Python\ 3.x/Install\ Certificates.command` — относится только к python.org installer-у, не к brew-сборке.

### Попробовать без своих данных

Есть генератор двух синтетических экспортов — групповой чат из 7 человек и личный диалог — чисто чтобы посмотреть дашборд:

```bash
python3 tools/gen_demo_data.py   # создаёт demo/group_demo.json + demo/personal_demo.json
streamlit run app.py
```

В сайдбаре переключи **Источник** на **Путь к файлу** и вставь:
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

Перезапусти Streamlit после установки. Модель не понимает сарказм, шутки и слэнг — числа читай со скепсисом.

## Тесты и линт

```bash
pip install ruff pytest
ruff check .
pytest
```

CI гоняет то же самое на каждый push и PR (`.github/workflows/ci.yml`).

## Источник

Проект построен на основе [**TelAnalysis** by Eduard Isaev](https://github.com/krakodjaba/TelAnalysis) ([@e_isaevsan](https://t.me/stdinio)). Спасибо за оригинальный проект и логику разбора Telegram-экспорта.

Что изменилось в этом форке:
- Переписан UI с pywebio на Streamlit (виртуализованные таблицы — больше не зависает на чатах в десятки тысяч сообщений)
- Заменён matplotlib-граф на интерактивный pyvis + community detection
- Добавлены heatmap-ы активности (hour × weekday, calendar), emoji-аналитика, reply latency
- Добавлен Per-user tab
- Wordcloud теперь и в чатах, не только в каналах
- Чистка модулей: убран мёртвый код, исправлены баги в `remove_emojis` (уничтожал английский текст и обрезал после первой эмодзи), убрана гонка `ThreadPoolExecutor` где она ничего не давала из-за GIL
- Добавлены: глубина reply-цепочек, распределение длин разговоров, самые длинные монологи, трекер мата, sticker-эмодзи по юзерам, forwards-ratio, Q&A latency, sentiment по часам и дням, binary calendar heatmap, longest streak, юбилеи

## Лицензия

GPL-3.0 (унаследована из оригинала). См. [`LICENSE`](LICENSE).
