# Гермес v2 — Walking Skeleton (Phase 1)
# Минимальный образ: только fastapi + uvicorn + httpx.
# Тяжёлые deps (playwright/apify/pymysql/lighthouse) НЕ здесь — это Phase 3.

FROM python:3.11-slim

# curl ОБЯЗАТЕЛЕН — нужен для HEALTHCHECK (в slim его нет по умолчанию).
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/hermes-v2

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=30s \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
