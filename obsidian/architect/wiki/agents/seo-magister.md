# SEO Magister

**Type:** Magister (управляющий агент)
**Domain:** Поисковая оптимизация медицинских сайтов
**Status:** ✅ Implemented (Phase 7)

## Responsibility

Управляет SEO-оптимизацией сайтов медицинских клиник:
- Keyword Research (сбор и кластеризация ключевых слов)
- Технический аудит сайтов
- Анализ конкурентов в поисковой выдаче
- Оптимизация контента под поисковые системы
- Мониторинг позиций

## Subagents

| Subagent | File | Purpose |
|----------|------|---------|
| KeywordResearchAgent | `subagents/seo/keyword_research.py` | Сбор ключевых слов через SEMrush/Ahrefs |
| CompetitorAnalyzer | `subagents/seo/competitor_analyzer.py` | Анализ сайтов конкурентов |
| TechnicalSEOAgent | `subagents/seo/technical_seo.py` | Технический аудит (Core Web Vitals, структура) |
| ContentOptimizer | `subagents/seo/content_optimizer.py` | Оптимизация контента под ключевые слова |
| RankTracker | `subagents/seo/rank_tracker.py` | Мониторинг позиций |

## API Dependencies

- SEMrush API (Keyword Magic Tool)
- Ahrefs API (fallback)

## Resilience Patterns

- Circuit Breaker (fail_max=5, reset_timeout=60s)
- Exponential Backoff (1s → 30s max)
- Token Bucket Rate Limiting
- 1-hour Response Caching

## Vault

`AIM/obsidian/seo-magister/` — LLM Wiki паттерн (raw/ + wiki/ + decisions/)
