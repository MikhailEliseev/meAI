# Hermes Agent — AIM Operator container
# Python 3.11 per D-02 (not 3.13 as in official Hermes Dockerfile)
# Custom minimal build — no Node.js, no Playwright, no TUI, no browser

FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# App directory
WORKDIR /opt/hermes

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir \
    "hermes-agent[mcp]>=0.14.0" \
    "hermes-agent[messaging]>=0.14.0" \
    "hermes-agent[web]>=0.14.0" \
    "hermes-agent[anthropic]>=0.14.0"

# Patch AIAgent: remove stream_options which causes HTTP 400 from OmniRoute
# when include_usage is requested but provider doesn't support it.
# (Previously we also forced stream=False, but OmniRoute now handles streaming.)
RUN find /usr/local/lib/python3.11/site-packages -name 'run_agent.py' -exec \
    sed -i '/"stream_options": {.*include_usage.*}/d' {} \;

# Copy application code
COPY app/ ./app/
COPY knowledge/ ./knowledge/

# Copy skills from repo (D-03: stored in repo, copied into image at build time)
COPY skills/ ./skills/

# Copy startup script from Plan 15-01
COPY scripts/copy_soul.sh ./scripts/copy_soul.sh
RUN chmod +x ./scripts/copy_soul.sh

# Runtime configuration
ENV HERMES_HOME=/opt/data
ENV PYTHONUNBUFFERED=1
ENV HERMES_CONFIG_QUIET=1

# OMNIROUTE CONFIG (D-05)
ENV OMNIROUTE_URL=http://193.111.152.14:7451
ENV OMNIROUTE_AUTH=U9pjtK:hxtlqz

# Create data directory (Docker volume mount point per D-06)
RUN mkdir -p /opt/data/sessions /opt/data/leads /opt/data/logs

# Volume for persistent data (D-06)
VOLUME ["/opt/data"]

# Health check (D-29)
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port (D-07: internal Docker network only, NOT exposed to host)
EXPOSE 8000

# Startup: copy SOUL.md to HERMES_HOME (Pitfall 4), then start FastAPI
ENTRYPOINT ["/bin/bash", "-c", "/opt/hermes/scripts/copy_soul.sh && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
