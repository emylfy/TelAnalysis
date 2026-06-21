# syntax=docker/dockerfile:1

# --- Stage 1: build the React SPA -------------------------------------------
FROM node:20-slim AS frontend
WORKDIR /build/frontend
# Install deps first for layer caching.
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build          # emits /build/frontend/dist

# --- Stage 2: Python runtime ------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NLTK_DATA=/usr/local/share/nltk_data

WORKDIR /app

# Python deps (analysis engine + FastAPI backend).
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the NLTK corpora so first request is offline & instant.
RUN python -m nltk.downloader -d "$NLTK_DATA" stopwords punkt punkt_tab

# App code + the built SPA from stage 1.
COPY analysis/ ./analysis/
COPY api/ ./api/
COPY ui/ ./ui/
COPY nltk_analyse.py stopwords_list.py utils.py config.json ./
COPY --from=frontend /build/frontend/dist ./frontend/dist

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
