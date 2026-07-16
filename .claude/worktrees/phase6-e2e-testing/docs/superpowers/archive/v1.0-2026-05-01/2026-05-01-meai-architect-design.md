# meAI Architect Design Specification

**Date:** 2026-05-01  
**Status:** Design Complete, Ready for Implementation  
**Version:** 1.0

---

## Problem Statement

Построить **meAI** — CEO-архитектора, который проектирует и создаёт **AIM** (AI-first medical marketing agency). meAI должен быть надзорным органом управления всем агентством, обладать силой для принятия решений и быть способным к самообучению и адаптации.

---

## Goals

1. **Проектирование архитектуры** — meAI умеет спроектировать структуру агентства
2. **Создание агентов** — автоматическое создание агентов с vaults, промптами, регистрацией
3. **Управление системой** — мониторинг, анализ, оптимизация, обучение
4. **Надзор и контроль** — полная видимость и контроль над агентством
5. **Самообучение** — система адаптируется и улучшается со временем

---

## Architecture Overview

### Two-Level System

```
Level 1: meAI (Architect)
  Location: /Users/mikhaileliseev/Desktop/Dev/!meAI
  Role: Проектирует и создаёт агентство

Level 2: AIM Agency (Operational System)
  Location: /Users/mikhaileliseev/Desktop/Dev/AIM
  Role: Само агентство с Опером, отделами, агентами
```

### meAI Components

```
meAI
├── Core
│   ├── Architect — проектирование архитектуры
│   ├── Decision Maker — принятие решений
│   └── Orchestrator — координация (async)
│
├── Storage Layer
│   ├── SQLite
│   │   ├── events/ — event sourcing
│   │   ├── messages/ — message bus
│   │   └── metrics/ — метрики
│   └── Obsidian
│       ├── context/ — контекст и знания
│       ├── vaults/ — agent vaults
│       └── snapshots/ — checkpoints
│
├── Safety Layer
│   ├── Loop Detection — защита от зацикливания
│   ├── Timeout Manager — таймауты операций
│   ├── Context Monitor — контроль контекста (40% rule)
│   └── Human-in-Loop Gates — критичные решения
│
├── Horizontal Agents
│   ├── Researcher
│   │   ├── Vault: obsidian-vaults/researcher/
│   │   └── Subagents:
│   │       ├── Reddit субагент
│   │       ├── YouTube субагент
│   │       ├── Telegram субагент
│   │       └── LinkedIn субагент
│   └── Teacher (будет создан в AIM)
│
├── Core Systems (14 компонентов)
│   ├── 1. Agent Factory
│   ├── 2. Monitoring & Control
│   ├── 3. Analytics & Optimization
│   ├── 4. Learning & Adaptation
│   ├── 5. Validation & Testing
│   ├── 6. Strategic Planning
│   ├── 7. Communication & Reporting
│   ├── 8. Health Check
│   ├── 9. Communication Protocol
│   ├── 10. Rollback Mechanism
│   ├── 11. Priority System
│   ├── 12. Decision Arbiter
│   ├── 13. Event Sourcing
│   └── 14. Safety Mechanisms
│
└── Communication
    ├── Event Bus (SQLite, async)
    ├── Message Queue (Python asyncio)
    └── Event Sourcing (replay capability)
```

---

## Key Design Decisions

### 1. Dual Storage Architecture

**Decision:** SQLite для событий + Obsidian для знаний

**Rationale:**
- SQLite быстрее для event log и message bus
- Obsidian лучше для human-readable знаний и контекста
- Разделение ответственности: события vs знания

**Alternatives considered:**
- A) Только Obsidian — медленно для событий
- B) Только SQLite — плохо для human-readable контекста
- C) Dual storage (выбрано) — лучшее из обоих миров

### 2. Event Sourcing

**Decision:** Все события в immutable log

**Rationale:**
- Audit trail — видно всю историю
- Replay — можно восстановить состояние
- Time-travel debugging — можно вернуться назад
- Rollback — откат через replay событий

### 3. Async-First Design

**Decision:** Асинхронная коммуникация между компонентами

**Rationale:**
- Один медленный агент не блокирует всех
- Масштабируемость — можно добавлять агентов
- Resilience — сбой одного не роняет систему

### 4. Hybrid Knowledge Access

**Decision:** Гибридный доступ к знаниям (own vault + shared + cross-department search)

**Rationale:**
- Баланс между фокусом и гибкостью
- Субагенты не перегружены, но могут найти нужное
- Контроль через магистров, но не бутылочное горлышко

### 5. Researcher as Separate Agent

**Decision:** Researcher — отдельный горизонтальный агент, не функция meAI

**Rationale:**
- Специализация — исследования требуют экспертизы
- Переиспользование — можно клонировать в AIM
- Разгрузка meAI — архитектор не должен быть исследователем

---

## Interaction Model

### Conversational + Autonomous (B + C)

**Conversational Mode:**
- Пользователь говорит → meAI делает
- Примеры: "Создай структуру AIM", "Добавь субагента"

**Autonomous Mode:**
- meAI сам принимает решения и уведомляет
- Примеры: Обнаружил проблему → предложил решение

### Decision Boundaries (B + C)

**meAI спрашивает разрешения:**
- Создание нового отдела (department)
- Изменение архитектуры системы
- Удаление агентов
- Изменение иерархии
- Большие финансовые решения

**meAI действует автономно:**
- Создание субагентов внутри отдела
- Обновление промптов агентов
- Создание/обновление vault файлов
- Оптимизация структуры
- Регистрация в SYSTEM.md
- Мелкие улучшения

После автономного действия → уведомляет пользователя.

---

## Safety Mechanisms

### Protection Against Common Pitfalls

Based on research (Autogen, CrewAI, Microsoft Autogen):

1. **Loop Detection**
   - Max delegation depth: 5 уровней
   - Если агент вызывает себя > 3 раз → алерт

2. **Timeout Policies**
   - Max 5 минут на операцию
   - После таймаута → rollback + алерт

3. **Context Limits**
   - Max 40% контекста (Dumb Zone rule)
   - Auto-compact при 50%
   - Manual `/clear` при перегрузке

4. **Human-in-Loop Gates**
   - Критичные решения требуют подтверждения
   - Список критичных операций в конфиге

5. **Immutable Event Log**
   - Все события только append
   - Нельзя удалить или изменить
   - Rollback через replay

---

## Communication Protocol

### Message Format

```json
{
  "id": "msg-001",
  "from": "researcher",
  "to": "meai-core",
  "type": "knowledge_package",
  "priority": "high",
  "timestamp": "2026-05-01T14:11:49Z",
  "payload": {...}
}
```

### Message Types

- `knowledge_package` — от Researcher к Teacher
- `agent_status` — от агентов к Monitoring
- `alert` — от любого компонента к meAI Core
- `decision_request` — запрос решения к Decision Arbiter
- `command` — команда от meAI Core к компонентам

### Priority Levels

- **P0 (Critical):** Сбои, алерты, безопасность → немедленно
- **P1 (High):** Стратегические решения → в течение часа
- **P2 (Medium):** Оптимизация, анализ → в течение дня
- **P3 (Low):** Планирование, отчёты → когда есть время

---

## Rollback Mechanism

### Versioning Strategy

```
obsidian-vaults/meai/versions/
├── agents/
│   ├── seo-positions/
│   │   ├── v1.0.0/ (промпт + vault snapshot)
│   │   ├── v1.1.0/
│   │   └── current -> v1.1.0
└── system/
    ├── architecture-v1.md
    ├── architecture-v2.md
    └── current -> architecture-v2.md
```

### Rollback Process

1. Обнаружена проблема (через Monitoring)
2. meAI определяет, какое изменение вызвало проблему
3. Откат к предыдущей версии:
   - Восстановить промпт агента
   - Восстановить vault из snapshot
   - Обновить SYSTEM.md
4. Уведомить собственника
5. Записать в Learning System (почему откатили)

---

## Researcher System

### Purpose

Отдельный агент для исследований рынка, трендов, конкурентов.

### Subagents

- Reddit субагент — мониторинг Reddit
- YouTube субагент — анализ видео и комментариев
- Telegram субагент — мониторинг каналов
- LinkedIn субагент — отслеживание персон и компаний

### Knowledge Packages

Researcher создаёт Knowledge Packages — пакеты знаний с метаданными:

```json
{
  "source": "Персона X, интервью",
  "topics": ["SEO", "SMM", "Content"],
  "content": {
    "seo": "...",
    "smm": "...",
    "content": "..."
  },
  "connections": ["SEO связано с SMM через..."]
}
```

**Ключевая идея:** Не разбивать знания на части. Хранить целиком с метаданными о связях.

### Vault Structure

```
obsidian-vaults/researcher/
├── raw-data/           # Сырые данные от субагентов
├── personas/           # Профили персон
├── sources/            # Источники
└── knowledge-packages/ # Готовые пакеты знаний
```

---

## Decision Arbiter

### Purpose

Разрешение конфликтов между компонентами, когда они дают противоречивые рекомендации.

### Arbitration Process

1. Конфликт обнаружен
2. Decision Arbiter анализирует:
   - Читает данные от обоих компонентов
   - Проверяет правила (rules/)
   - Анализирует исторические данные
   - Оценивает риски
3. Принимает решение или эскалирует собственнику
4. Записывает решение в resolutions/

### Arbitration Rules

1. Безопасность > Эффективность
2. Данные > Предположения
3. Проверенные паттерны > Эксперименты
4. Простота > Сложность
5. При равных аргументах → эскалация собственнику

---

## Technology Stack

### Core

- **Language:** Python 3.11+
- **Framework:** FastAPI (async)
- **Database:** SQLite (events, messages, metrics)
- **Knowledge Base:** Obsidian (markdown files)
- **AI:** Claude API (Anthropic)

### Libraries

- **Async:** asyncio, aiofiles
- **Data:** Pydantic (validation), SQLAlchemy 2.0 (async)
- **Events:** Custom event bus on asyncio queues
- **Monitoring:** structlog (logging)

---

## Acceptance Criteria

### Must Have (MVP)

1. ✅ meAI может создать структуру AIM (папки, SYSTEM.md)
2. ✅ Agent Factory работает (создаёт агентов с vaults и промптами)
3. ✅ Event Bus работает (SQLite + async)
4. ✅ Monitoring показывает статус агентов
5. ✅ Rollback работает (версионирование + восстановление)
6. ✅ Safety mechanisms работают (loop detection, timeouts)
7. ✅ Secrets management (API keys в .env, не в коде)
8. ✅ Automated backups (SQLite + Obsidian)
9. ✅ Rate limiting для Claude API
10. ✅ Graceful shutdown handler
11. ✅ Basic testing (unit + integration)
12. ✅ Deployment strategy (systemd/Docker)
13. ✅ Alerting system (Telegram/Slack notifications)

### Should Have (Post-MVP)

- Researcher Agent (market intelligence gathering)
- Analytics & Optimization Engine
- Learning & Adaptation System
- Strategic Planning System
- Decision Arbiter
- Distributed tracing
- Cost tracking per agent
- Database migrations strategy

### Nice to Have

- Web UI для мониторинга
- Grafana dashboards
- Multi-tenancy support
- GDPR compliance tools

---

## Non-Goals

- ❌ Не строим само агентство AIM (это делает meAI)
- ❌ Не реализуем операционные агенты (Опер, отделы) — это в AIM
- ❌ Не делаем UI для клиентов агентства
- ❌ Не интегрируемся с внешними маркетинговыми платформами (пока)

---

## Constraints

1. **Budget:** Ограничен API costs (Claude API)
2. **Time:** Нужен MVP быстро, итеративное развитие
3. **Complexity:** Начинаем с простого, усложняем по мере необходимости
4. **Context:** 40% rule — не перегружать контекст

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Context explosion | High | 40% rule, auto-compact, `/clear` |
| Infinite loops | High | Loop detection, max depth, timeouts |
| API costs | Medium | Rate limiting, caching, monitoring, budget alerts |
| Data loss | High | Event sourcing, immutable log, automated backups |
| Agent conflicts | Medium | Decision Arbiter, clear rules |
| Slow performance | Medium | Async-first, SQLite for events |
| Secrets exposure | High | .env files, never commit secrets, encryption at rest |
| SQLite corruption | High | Regular backups, WAL mode, integrity checks |
| Obsidian vault deletion | Medium | Automated backups, version control |
| Scalability limits | Medium | Monitor agent count, test at 100+ agents |
| No alerting | Medium | Telegram/Slack integration, email alerts |
| Migration failures | Medium | Database migration strategy, rollback plan |
| Testing gaps | Medium | Unit + integration tests, mocking Claude API |

---

## Operational Requirements

### 1. Secrets Management

**Strategy:**
- API keys в `.env` файле (gitignored)
- Использовать `python-dotenv` для загрузки
- Никогда не коммитить секреты в git
- Rotation strategy: manual (MVP), automated (Post-MVP)

**Implementation:**
```python
# .env
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=sqlite+aiosqlite:///./data/meai.db
OBSIDIAN_VAULT_PATH=./obsidian

# src/meai/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    anthropic_api_key: str
    database_url: str
    obsidian_vault_path: str
    
    class Config:
        env_file = ".env"
```

### 2. Backup & Recovery

**Automated Backups:**
- SQLite: daily backup через cron/systemd timer
- Obsidian: git auto-commit + push каждый час
- Event log: append-only, никогда не удалять

**Backup Script:**
```bash
#!/bin/bash
# scripts/backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
sqlite3 data/meai.db ".backup data/backups/meai_$DATE.db"
cd obsidian && git add -A && git commit -m "Auto-backup $DATE" && git push
```

**Recovery:**
- RPO (Recovery Point Objective): 1 час
- RTO (Recovery Time Objective): 15 минут
- Restore from latest backup + replay event log

### 3. Rate Limiting

**Claude API Rate Limiter:**
```python
# src/meai/core/rate_limiter.py
from aiolimiter import AsyncLimiter

# 50 requests per minute (adjust based on tier)
rate_limiter = AsyncLimiter(max_rate=50, time_period=60)

async def call_claude_api(prompt: str):
    async with rate_limiter:
        response = await anthropic.messages.create(...)
        return response
```

**Budget Alerts:**
- Track API costs в SQLite
- Alert при 80% бюджета
- Auto-shutdown при 100% (опционально)

### 4. Deployment Strategy

**Option A: systemd (Linux)**
```ini
# /etc/systemd/system/meai.service
[Unit]
Description=meAI Architect Service
After=network.target

[Service]
Type=simple
User=meai
WorkingDirectory=/opt/meai
ExecStart=/opt/meai/.venv/bin/uvicorn meai.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Option B: Docker**
```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "meai.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 5. Graceful Shutdown

**Shutdown Handler:**
```python
# src/meai/main.py
import signal
import asyncio

shutdown_event = asyncio.Event()

def handle_shutdown(signum, frame):
    print("Shutting down gracefully...")
    shutdown_event.set()

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

@app.on_event("shutdown")
async def shutdown():
    # Close all connections
    await db.close()
    await event_bus.close()
    # Save state
    await save_state()
```

### 6. Testing Strategy

**Unit Tests:**
```python
# tests/unit/test_agent_factory.py
import pytest
from meai.core.agent_factory import AgentFactory

@pytest.mark.asyncio
async def test_create_agent():
    factory = AgentFactory()
    agent = await factory.create_agent("test-agent", "subagent")
    assert agent.name == "test-agent"
    assert agent.vault_path.exists()
```

**Integration Tests:**
```python
# tests/integration/test_event_bus.py
@pytest.mark.asyncio
async def test_message_flow():
    bus = EventBus()
    await bus.publish("test", {"data": "hello"})
    message = await bus.consume("test")
    assert message["data"] == "hello"
```

**Mocking Claude API:**
```python
# tests/conftest.py
@pytest.fixture
def mock_claude_api(monkeypatch):
    async def mock_create(*args, **kwargs):
        return MockResponse(content="test response")
    monkeypatch.setattr("anthropic.messages.create", mock_create)
```

### 7. Monitoring & Alerting

**Health Check Endpoint:**
```python
# src/meai/main.py
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "uptime": get_uptime(),
        "agents_count": await get_agents_count(),
        "event_bus": await event_bus.health(),
        "database": await db.health()
    }
```

**Alerting:**
- Telegram bot для критичных алертов
- Email для некритичных
- Slack integration (опционально)

### 8. Database Migrations

**Alembic для SQLAlchemy:**
```bash
# Создать миграцию
alembic revision --autogenerate -m "add new table"

# Применить миграцию
alembic upgrade head

# Откатить миграцию
alembic downgrade -1
```

**Migration Strategy:**
- Все изменения схемы через миграции
- Тестировать на копии production данных
- Rollback plan для каждой миграции

### 9. Scalability Limits

**Known Limits:**
- SQLite: max 1000 concurrent connections (WAL mode)
- Obsidian: no hard limit, но performance degradation при 10K+ files
- Event Bus: limited by asyncio queue size (default 0 = unlimited)

**Monitoring:**
- Track agent count
- Alert при > 80 агентах
- Test at 100+ agents before production

### 10. Documentation

**Required Docs:**
- `README.md` — Quick start
- `ARCHITECTURE.md` — System design
- `DEPLOYMENT.md` — How to deploy
- `OPERATIONS.md` — Runbooks
- `API.md` — API documentation
- `ADRs/` — Architecture Decision Records

---

## Security Considerations

### 1. Secrets Management
- ✅ API keys в .env (gitignored)
- ✅ No secrets in code
- ⚠️ Encryption at rest (Post-MVP)
- ⚠️ Secrets rotation (Post-MVP)

### 2. Access Control
- ✅ Obsidian vaults: file system permissions
- ✅ SQLite: file system permissions
- ⚠️ API authentication (Post-MVP)
- ⚠️ Role-based access (Post-MVP)

### 3. Data Privacy
- ⚠️ GDPR compliance (if collecting personal data)
- ⚠️ Data deletion on request
- ⚠️ Audit trail for data access

### 4. Network Security
- ✅ HTTPS for API (if exposed)
- ✅ Firewall rules
- ⚠️ VPN for remote access (Post-MVP)

---

## Success Metrics

1. **Agent Creation Time:** < 1 минута на агента
2. **System Uptime:** > 99%
3. **Context Usage:** < 40% в среднем
4. **Rollback Success Rate:** 100%
5. **Decision Latency:** < 5 секунд для P1 решений

---

## Next Steps

See implementation plan in `plans/2026-05-01-meai-architect-plan.md`

---

## References

- Research findings: Multi-agent systems (Autogen, CrewAI)
- Memory files: `/Users/mikhaileliseev/.claude/projects/-Users-mikhaileliseev-Desktop-Dev--meAI/memory/`
- CLAUDE.md: `/Users/mikhaileliseev/Desktop/Dev/!meAI/CLAUDE.md`

---

**Design approved:** 2026-05-01  
**Ready for implementation:** Yes
