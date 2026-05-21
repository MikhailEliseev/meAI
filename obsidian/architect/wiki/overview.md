# Project Overview

**Updated:** 2026-05-21

## What is AIM?

AIM — AI-first medical marketing agency at [iamaim.ru](https://iamaim.ru).

Полностью автономная система, где AI-агенты управляют маркетингом медицинских клиник:
- SEO анализ и оптимизация
- Контент-маркетинг с ФЗ-38 compliance
- Мультиплатформенная реклама (Яндекс.Директ, VK Ads, Telegram Ads)
- Лидогенерация и квалификация лидов
- Автоматизированные продажи (Bitrix24 CRM)

## Architecture

```
meAI/                           # Command Center
├── src/meai/                   # Framework
│   ├── core/                   # Architect, Orchestrator, Decision Maker
│   ├── agents/                 # Base: Operator, BaseMagister, BaseAgent
│   ├── events/                 # Event Bus, Event Store
│   ├── memory/                 # Obsidian integration
│   └── storage/                # Database
├── AIM/                        # Agency Application
│   ├── src/aim/
│   │   ├── magisters/          # SEO, Content, Ads, Analytics, AI, Sales Admin
│   │   ├── subagents/          # 20+ specialized subagents
│   │   ├── api/                # FastAPI routes (leads, sales, telegram, payments)
│   │   ├── integrations/       # Bitrix24, Linear, HH.ru
│   │   ├── services/           # Lead capture, qualification, escalation
│   │   └── models/             # SQLAlchemy models
│   ├── obsidian/               # Agent vaults (19 agents)
│   ├── hermes/                 # Telegram bot for alerts + admin
│   ├── frontend/               # Next.js landing page
│   └── deploy/                 # Docker, Nginx, monitoring configs
└── obsidian/architect/         # Architect's strategic vault
```

## Implementation Status

| Component | Status | Phase |
|-----------|--------|-------|
| Framework (Architect, Operator, Event Bus) | ✅ Complete | 1-6 |
| Database (SQLAlchemy, Alembic) | ✅ Complete | 1-6 |
| Obsidian Memory (LLM Wiki) | ✅ Complete | 1-6 |
| Magisters (SEO, Content, Ads, Analytics, AI, Sales) | ✅ Complete | 7-9, 12 |
| CI System (Competitor Intelligence) | ✅ Complete | 10 |
| Client Acquisition (Landing, Payments, Leads) | ✅ Complete | 11 |
| Sales Admin (Hermes, Bitrix24, Telegram webhook) | ✅ Complete | 12 |
| Ads API Clients (Yandex Direct, VK, Telegram) | ✅ Complete | 13 |
| Multi-platform Campaign Sync | ✅ Complete | 13 |
| Frontend (iamaim.ru landing) | ✅ Complete | 11, 13 |
| Monitoring (Prometheus, Grafana) | ✅ Complete | 8 |
| Teacher Agent (continuous learning) | ⚠️ Not active | — |

## Current Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0 async
- **Database:** PostgreSQL (production), SQLite (dev)
- **Cache:** Redis
- **Frontend:** Next.js
- **Deploy:** Docker Compose, Nginx
- **Monitoring:** Prometheus, Grafana, Alertmanager
- **Integrations:** Bitrix24 CRM, Linear, HH.ru, YooKassa, Telegram Bot API
- **AI:** Claude API (Anthropic), structlog

## Environment

- **Local:** MacBook Air M3, macOS
- **Server:** SSH `aim` (root@AIM-Server)
- **Repo:** github.com/MikhailEliseev/meAI
- **Production:** https://iamaim.ru
