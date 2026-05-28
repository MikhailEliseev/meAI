# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY AIM/requirements.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies (including Chromium for Playwright)
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libdbus-1-3 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
    libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2 libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY AIM/src/aim ./AIM/src/aim
COPY src/meai ./src/meai
COPY AIM/obsidian ./AIM/obsidian
COPY AIM/alembic ./AIM/alembic
COPY AIM/alembic.ini ./AIM/alembic.ini
COPY scripts ./scripts
COPY AIM/.env.production .env

# Create data directory
RUN mkdir -p data/production logs AIM/data AIM/reports

# Set Python path
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app/AIM/src:/app/src

# Install Chromium browser for Playwright (Yandex Maps search)
RUN playwright install chromium

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "AIM.src.aim.main:app", "--host", "0.0.0.0", "--port", "8000"]
