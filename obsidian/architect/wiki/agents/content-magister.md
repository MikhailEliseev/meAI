# Content Magister

**Type:** Magister (управляющий агент)
**Domain:** Медицинский контент-маркетинг
**Status:** ✅ Implemented (Phase 8)

## Responsibility

Управляет контент-маркетингом медицинских клиник:
- Генерация SEO-оптимизированного контента
- Проверка медицинской достоверности (фактчекинг)
- ФЗ-38 compliance (закон о рекламе медицинских услуг)
- Планирование контент-плана
- Анализ качества контента

## Subagents

| Subagent | File | Purpose |
|----------|------|---------|
| BlogContentAgent | `subagents/content/blog_writer.py` | Написание статей для блога |
| MedicalFactChecker | `subagents/content/fact_checker.py` | Проверка медицинских утверждений |
| FZ38ComplianceChecker | `subagents/content/fz38_checker.py` | Проверка соответствия ФЗ-38 |
| ContentPlanner | `subagents/content/planner.py` | Планирование контент-календаря |
| ContentGapAnalyzer | `subagents/content/gap_analyzer.py` | Анализ пробелов в контенте |

## ФЗ-38 Compliance

Автоматическая проверка всех текстов:
- Запрещены утверждения о гарантии эффективности
- Обязательный disclaimer о противопоказаниях
- Возрастное ограничение 18+
- Запрещены ссылки на конкретные случаи излечения

## Vault

`AIM/obsidian/content-magister/` — LLM Wiki паттерн
