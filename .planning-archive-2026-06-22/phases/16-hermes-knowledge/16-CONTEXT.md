# Phase 16: Hermes Knowledge Training — Context

**Gathered:** 2026-05-19
**Status:** Ready for planning

## Phase Boundary

Обучить Hermes всему, что умеет система AIM. Создать comprehensive SOUL.md, который кодирует полное знание:
- Всех агентов и субагентов (как работают, что умеют)
- Как вести клиентов (новых — presale, текущих — active projects)
- Как запускать агентство и управлять workflow
- Как работать с информацией и данными
- Как давать рекомендации по рекламным кампаниям
- Всю стратегию WOW-данных и «3 числа»

## Implementation Decisions

### Knowledge Domains for SOUL.md

- **D-01:** Hermes должен знать архитектуру всех 4 Magisters (SEO, Content, Ads, Analytics) — их субагентов, API clients, и что каждый умеет
- **D-02:** Режимы работы (PRESALE/ACTIVE/ADMIN) — полное описание поведения в каждом
- **D-03:** WOW-Data Strategy — какие данные показывать клиенту, 7 блоков бесплатного аудита
- **D-04:** Принцип «3 числа» — пациенты/срок/цена — как отвечать клиенту
- **D-05:** Token Economy — Tier 0/1/2, когда запускать дорогие анализы
- **D-06:** Lead Dossier System — структура папок, статусы лида
- **D-07:** Omni-Channel Follow-up — сайт → Telegram → Email, догонялки по дням
- **D-08:** Agent Orchestration — как Hermes запускает Magisters через MCP tools
- **D-09:** Российский рынок — ФЗ-152, ЮKassa, Яндекс.Директ/Метрика, российские соцсети
- **D-10:** Все 6 MCP tools с детальным описанием входов/выходов

### Claude's Discretion
- Структура и формат SOUL.md (один файл или несколько skills)
- Уровень детализации по каждому domain
- Приоритетность разделов в SOUL.md

## Specific Ideas

Из запроса пользователя:
1. «все агенты и субагенты под капотом» — полная карта системы
2. «как вести клиентов» — presale flow + active project flow
3. «как общаться с новыми, с текущими» — разные tone of voice для разных стадий
4. «как запускать агентство» — agency workflows и automation
5. «как работать с информацией» — data flow, reports, analytics
6. «как давать рекомендации по рекламным кампаниям» — ads recommendations logic

## Deferred Ideas

None — всё в scope фазы.

---

*Phase: 16-hermes-knowledge*
*Context gathered: 2026-05-19*
