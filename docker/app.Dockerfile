FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml alembic.ini ./
COPY api ./api
COPY worker ./worker
COPY logic ./logic
COPY alembic ./alembic
COPY README.md ./README.md

RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .
