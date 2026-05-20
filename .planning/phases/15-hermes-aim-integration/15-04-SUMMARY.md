---
phase: 15-hermes-aim-integration
plan: 04
subsystem: docker-deployment-monitoring
tags: [docker-compose, prometheus, alertmanager, telegram, telethon, monitoring]

# Dependency graph
requires: [15-03-fastapi-http-wrapper]
provides:
  - "Hermes service in docker-compose.yml with restart policy, healthcheck, resource limits"
  - "Persistent hermes_data Docker volume for sessions, leads, logs (S-15-07)"
  - "Telegram Bot API webhook for incoming client messages (D-16)"
  - "Telethon MCP tools (search_telegram_chats, send_telegram_message) for outgoing (D-19)"
  - "Unified chat: Telegram messages flow through same Hermes Operator (D-17)"
  - "Session binding via tg:// deep link (D-18)"
  - "Prometheus Hermes scrape target (D-29, D-30)"
  - "HermesDown alert (60s downtime → critical) (D-31)"
  - "Alertmanager Telegram + Email receivers (D-32)"
  - "DEEPSEEK_API_KEY removed from .env.production (D-11)"
affects: []

# Tech tracking
tech-stack:
  added:
    - "python-telegram-bot (Bot API webhook)"
    - "Telethon (MTProto user-client for outgoing + search)"
  patterns:
    - "Docker restart: unless-stopped replaces systemd (D-08)"
    - "expose (not ports) for internal-only services (D-07)"
    - "Hybrid Telegram: Bot API (incoming) + Telethon (outgoing) (D-16)"
    - "Unified chat: one AIAgent serves web + Telegram (D-17)"
    - "Deep link binding: tg://bind_<session_id> → /start command → chat-lead mapping (D-18)"
    - "Lazy Telethon init: client created on first tool call, not at import time"

key-files:
  created:
    - AIM/hermes/app/telegram_gateway.py
    - AIM/hermes/app/tools/telegram_tools.py
  modified:
    - AIM/docker-compose.yml
    - AIM/.env.production
    - AIM/hermes/app/main.py
    - AIM/prometheus.yml
    - AIM/deploy/monitoring/rules.yml
    - AIM/deploy/monitoring/alertmanager.yml

# Acceptance summary
- docker-compose.yml: hermes service with expose, healthcheck, volume, restart ✅
- .env.production: HERMES_API_KEY, HERMES_URL, TELEGRAM vars added; DEEPSEEK_API_KEY absent ✅
- telegram_gateway.py: webhook + bind-session routes, run_agent() unified chat ✅
- telegram_tools.py: 2 Telethon tools registered in aim-operations toolset ✅
- main.py: telegram_router included ✅
- prometheus.yml: aim-hermes job scraping hermes:8000 ✅
- rules.yml: HermesDown alert (critical, 1m for, runbook) ✅
- alertmanager.yml: telegram_configs + email_configs → me@mikhaileliseev.com ✅
