# Architect — Knowledge Base Index

**Last updated:** 2026-05-21 18:30
**Project:** meAI → AIM (AI-first medical marketing agency at iamaim.ru)
**Phase:** 13 complete (47/47 plans, 100%)

---

## Categories

### Concepts (5)
- [[wiki/concepts/llm-wiki-pattern]] — LLM Wiki by Andrej Karpathy (три слоя: raw → wiki → schema)
- [[wiki/concepts/ai-automation-medical-marketing]] — AI-автоматизация медицинского маркетинга
- [[wiki/concepts/three-layer-hierarchy]] — Architect → Operator → Agents
- [[wiki/concepts/multi-platform-ads]] — Кросс-платформенная реклама (Yandex, VK, Telegram)
- [[wiki/concepts/russian-market-adaptation]] — Адаптация западных практик под РФ

### Technologies (5)
- [[wiki/technologies/stack]] — Python 3.11+, FastAPI, PostgreSQL, Docker, Redis, Prometheus
- [[wiki/technologies/deployment]] — Docker Compose, Nginx, GitHub Actions
- [[wiki/technologies/api-clients]] — Yandex Direct API v5, VK Ads API, Telegram Bot API
- [[wiki/technologies/integrations]] — Bitrix24 CRM, Linear, HH.ru, YooKassa, Контур.Диадок
- [[wiki/technologies/monitoring]] — Prometheus, Grafana, Alertmanager, Sentry

### Strategies (4)
- [[wiki/strategies/seo-medical-clinics]] — SEO стратегия для медицинских клиник
- [[wiki/strategies/content-marketing-medical-clinics]] — Контент-маркетинг для медицины
- [[wiki/strategies/ads-multi-platform]] — Мультиплатформенная рекламная стратегия
- [[wiki/strategies/sales-automation]] — Автоматизация продаж и лидогенерации

### Agents (15+)
**Magisters (управляющие):**
- [[wiki/agents/seo-magister]] — SEO Magister (анализ, оптимизация, мониторинг)
- [[wiki/agents/content-magister]] — Content Magister (контент, брифы, качество)
- [[wiki/agents/ads-magister]] — Ads Magister (Яндекс.Директ, VK Ads, Telegram Ads)
- [[wiki/agents/analytics-magister]] — Analytics Magister (трафик, конверсии, атрибуция)
- [[wiki/agents/ai-magister]] — AI Magister (lead scoring, предиктивная аналитика)
- [[wiki/agents/sales-admin-magister]] — Sales Admin Magister (квалификация, эскалация, CRM)

**CI (Competitor Intelligence):**
- [[wiki/agents/ci-orchestrator]] — CI Orchestrator (координация анализа конкурентов)
- [[wiki/agents/ci-scout]] — CI Scout (поиск и обнаружение конкурентов)
- [[wiki/agents/ci-auditor]] — CI Auditor (аудит сайтов конкурентов)
- [[wiki/agents/ci-factchecker]] — CI Factchecker (проверка фактов и данных)
- [[wiki/agents/ci-strategist]] — CI Strategist (стратегия на основе данных конкурентов)

**Sales:**
- [[wiki/agents/crm-agent]] — CRM Agent (Bitrix24 интеграция)
- [[wiki/agents/telegram-monitor]] — Telegram Monitor (мониторинг каналов)
- [[wiki/agents/website-monitor]] — Website Monitor (мониторинг сайтов)
- [[wiki/agents/knowledge-manager]] — Knowledge Manager (база знаний клиентов)

### Workflows (6)
- [[wiki/workflows/inbox-processing]] — Обработка входящих задач
- [[wiki/workflows/phase-execution]] — Выполнение фаз (Plan → Execute → Verify → Summary)
- [[wiki/workflows/deployment]] — Деплой на сервер (push → pull → restart)
- [[wiki/workflows/obsidian-sync]] — Синхронизация Obsidian vaults (local ↔ server)
- [[wiki/workflows/teacher-learning-cycle]] — Цикл обучения Teacher Agent (каждые 2-4 недели)
- [[wiki/workflows/campaign-sync]] — Синхронизация рекламных кампаний с API → DB

### Projects / Phases (13)
- [[wiki/projects/phase-01-06]] — Phases 1-6: Foundation (Architect, Operator, Event Bus, Agents)
- [[wiki/projects/phase-07-09]] — Phases 7-9: Magisters + Subagents
- [[wiki/projects/phase-10]] — Phase 10: CI System (Competitor Intelligence)
- [[wiki/projects/phase-11]] — Phase 11: Client Acquisition (Lead Scoring, Landing, Payments)
- [[wiki/projects/phase-12]] — Phase 12: Sales Admin Agent (Hermes, Bitrix24, Telegram)
- [[wiki/projects/phase-13]] — Phase 13: Landing + Marketing (Ads API clients, Campaigns)

### Sources (4)
- [[wiki/sources/2026-05-02-blackhat-seo]] — BlackHat SEO методы
- [[wiki/sources/2026-05-02-claude-design]] — Claude Design для создания сайтов
- [[wiki/sources/yandex-direct-api-docs]] — Яндекс.Директ API v5 документация
- [[wiki/sources/vk-ads-api-docs]] — VK Ads API документация

### Connections (5)
- [[wiki/connections/ci-data-flow-analysis]] — CI data flow анализ
- [[wiki/connections/synthesis-strategy-aim-agency]] — Стратегия AIM агентства v1
- [[wiki/connections/synthesis-strategy-aim-agency-v2]] — Стратегия AIM агентства v2 (уточнённая)
- [[wiki/connections/multi-platform-ads-architecture]] — Архитектура мультиплатформенной рекламы
- [[wiki/connections/sales-pipeline-flow]] — Flow лидогенерации и продаж

---

## Server Status

| Service | Status |
|---------|--------|
| aim-app (FastAPI) | ✅ Running |
| aim-postgres | ✅ Running |
| aim-nginx | ✅ Running |
| aim-hermes | ✅ Running |
| aim-redis | ✅ Running |
| aim-frontend | ✅ Running |
| aim-prometheus | ✅ Running |
| aim-grafana | ✅ Running |
| aim-alertmanager | ✅ Running |

**SSH:** `ssh aim` (root@server)
**URL:** https://iamaim.ru

---

## Statistics

- Total wiki pages: 40+
- Phases completed: 13 (47/47 plans, 100%)
- Agents implemented: 20+
- Tests: 45+
- Last ingest: 2026-05-21 18:30
- Last deployment: 2026-05-21 18:10
- Last lint: Never ⚠️
