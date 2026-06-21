# syntax=docker/dockerfile:1

# Stage 1: build the React SPA
FROM node:20-slim AS frontend
WORKDIR /build/frontend
# Install deps first for layer caching.
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build          # emits /build/frontend/dist

# Stage 2: Python runtime
FROM python:3.12-slim AS runtime

# Russian sentiment (torch + transformers, ~1GB) is OFF by default to keep the
# image small. Enable with:  docker build --build-arg WITH_SENTIMENT=1 .
ARG WITH_SENTIMENT=0

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NLTK_DATA=/usr/local/share/nltk_data \
    MPLCONFIGDIR=/tmp/mpl \
    HF_HOME=/home/app/.cache/huggingface

# Non-root runtime user (created early so the optional model cache below lands
# in a home dir we can hand over to it).
RUN useradd --create-home --uid 10001 app

WORKDIR /app

# Python deps (analysis engine + FastAPI backend).
COPY requirements.txt requirements-sentiment.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the NLTK corpora so first request is offline & instant.
RUN python -m nltk.downloader -d "$NLTK_DATA" stopwords punkt punkt_tab

# Optional: install the sentiment stack and pre-bake the model into the image
# (so the container needs no network at runtime). Skipped unless opted in.
RUN if [ "$WITH_SENTIMENT" = "1" ]; then \
      pip install --no-cache-dir -r requirements-sentiment.txt && \
      python -c "from transformers import AutoTokenizer, AutoModelForSequenceClassification as M; n='seara/rubert-tiny2-russian-sentiment'; AutoTokenizer.from_pretrained(n); M.from_pretrained(n)" && \
      chown -R app:app /home/app; \
    fi

# App code + the built SPA from stage 1 + the two bundled demos (so the
# landing screen's "Try demo" buttons work inside the container).
COPY analysis/ ./analysis/
COPY api/ ./api/
COPY ui/ ./ui/
COPY demo/ ./demo/
COPY nltk_analyse.py stopwords_list.py utils.py config.json ./
COPY --from=frontend /build/frontend/dist ./frontend/dist

USER app

LABEL org.opencontainers.image.title="TelAnalysis" \
      org.opencontainers.image.version="0.1.0" \
      org.opencontainers.image.source="https://github.com/emylfy/TelAnalysis"

EXPOSE 8000

# Liveness probe hits the API's /api/health (returns 200 once uvicorn is up).
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')" || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
