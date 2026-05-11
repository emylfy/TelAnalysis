# TelAnalysis

Streamlit-дашборд для анализа Telegram-чатов из локального экспорта.

Поддерживает оба формата выгрузки:
- **single chat** (`Settings → Export chat history`) — сразу загружается
- **full archive** (`Settings → Advanced → Export Telegram data`) — в сайдбаре появляется селектор чатов (с поиском и фильтром по типу)

Адаптируется под тип чата: для каналов/групп/личных/saved messages показываются только релевантные табы.

## Что внутри

**Overview**
- KPI: total messages / unique users / days active / media / service
- Plotly area-chart активности по дням
- Calendar heatmap (год × неделя × день)
- Hour × weekday heatmap
- Топ эмодзи и распределение reply latency

**Graph**
- Для групп — интерактивный force-directed pyvis-граф (drag/zoom/hover, толщина рёбер по частоте, цвет — Louvain communities)
- Для маленьких чатов — bar chart "кто отправлял / отвечал / получал ответы"
- Экспорт edges/nodes в CSV для Gephi

**Words**
- Топ слов по чату: wordcloud + bar chart + virtualized table
- Per-user picker: wordcloud юзера, его сообщения с sentiment-скором, top-words
- Извлечение email и телефонов

**Channel**
- Wordcloud + частотный анализ для broadcast-каналов

**Per-user**
- Daily timeline юзера, его hour×weekday heatmap, top emojis, reply latency, top words с wordcloud

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

### Linux (Ubuntu/Debian)

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

### Linux (Fedora/RHEL)

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

## Запуск

```bash
source .venv/bin/activate   # если ещё не активирован
streamlit run app.py
```

Открыть http://localhost:8501. В сайдбаре указать путь к `result.json` (для больших архивов лучше путь, чем upload — десятикратно быстрее).

NLTK-данные (`stopwords`, `punkt_tab`) скачиваются автоматически при первом запуске анализа слов. Если на macOS первый `nltk.download()` падает с SSL-ошибкой, прогони один раз `/Applications/Python\ 3.x/Install\ Certificates.command` (только если ставил Python с python.org installer-ом, не через brew).

## Опциональный sentiment-анализ

Русский/английский сентимент через `rubert-tiny2-russian-sentiment` (~1GB на диске + 50MB модель при первом использовании):

```bash
pip install -r requirements-sentiment.txt
```

Перезапусти streamlit после установки. Модель не понимает сарказм/шутки/слэнг — числа берите со скепсисом.

UI-настройки лежат в `.streamlit/config.toml` (по умолчанию скрыта Deploy-кнопка и отключена телеметрия).

## Тесты и линт

```bash
pip install ruff pytest
ruff check .
pytest
```

CI на push/PR (`.github/workflows/ci.yml`) гоняет то же самое.

## Источник

Проект построен на основе [**TelAnalysis** by Eduard Isaev](https://github.com/krakodjaba/TelAnalysis) ([@e_isaevsan](https://t.me/stdinio)). Спасибо автору за изначальный проект и логику разбора Telegram-экспорта.

Эта версия:
- Переписан UI с pywebio на Streamlit (виртуализованные таблицы — больше не зависает на чатах в десятки тысяч сообщений)
- Заменён matplotlib-граф на интерактивный pyvis с community detection
- Добавлены heatmaps активности (hour × weekday, calendar), emoji-аналитика, reply latency
- Добавлен Per-user tab
- Wordcloud в анализе чатов, не только каналов
- Чистка модулей: убран мёртвый код, исправлены баги в `remove_emojis` (уничтожал английский текст и обрезал после первой эмодзи), убрана гонка `ThreadPoolExecutor` где она ничего не давала из-за GIL

## Лицензия

GPL-3.0 (унаследована из оригинала). См. `LICENSE`.
