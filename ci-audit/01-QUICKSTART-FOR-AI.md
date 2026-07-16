# CI System — Quick Start для AI-модели

**Контекст:** Тебе дали этот документ, чтобы ты провёл аудит системы конкурентной разведки (CI) в проекте meAI/AIM. Ниже — минимальный набор информации для понимания системы.

## Суть проблемы (почему тебя позвали)

Система разрабатывается почти месяц. Есть два параллельных CI-пайплайна, которые делают похожие вещи, но по-разному и с разной степенью готовности. Пользователь (Михаил) хочет:
1. Понять, что реально работает, а что — stubs
2. Получить план унификации и доделывания
3. Услышать независимое мнение о архитектуре

## Ключевые файлы (читай в этом порядке)

1. `AIM/src/aim/subagents/competitive_intel/orchestrator/ci_orchestrator.py` (939 строк) — главный оркестратор, 16 фаз
2. `AIM/src/aim/services/ci_marketing_analysis.py` (964 строки) — пресс-релизный анализатор
3. `AIM/src/aim/services/ci/pipeline_runner.py` (~800 строк) — новый pipeline (вызывается из #2)
4. `AIM/src/aim/api/competitors.py` (408 строк) — API: поиск + пресс-релиз
5. `AIM/src/aim/api/seo.py` (179 строк) — API: полный CI

## Два пайплайна

```
Pipeline 1 (Пресс-релиз, РАБОТАЕТ частично):
  Hermes → POST /api/competitors/analyze/stream
    → CiMarketingAnalyzer.analyze()
      → PipelineRunner.run()          # поиск + 5 параллельных коллекторов
      → ComparisonMatrixBuilder.build()
      → _chat_summary_from_matrix()   # структурный, без LLM
    ← chat_summary, feature_matrix, pricing, positioning, tactics=[], recommendation="заглушка"

Pipeline 2 (Полный CI, НЕ РАБОТАЕТ):
  Hermes → POST /api/seo/audit
    → CIOrchestrator.execute_ci_analysis()
      → 16 фаз, но quick tier = только фазы 1-4
      → Фазы 11-15 (TW агенты) — stubs (файлов нет)
    ← WOW-цифры (ВСЕГДА null при quick)
```

## Главные проблемы (5 минут на понимание)

1. **Дублирование.** Два пайплайна делают одно и то же по-разному. CiMarketingAnalyzer и CIOrchestrator не связаны.

2. **Pipeline 1 полурабочий.** Новый `analyze()` использует PipelineRunner, но:
   - `steal_worthy_tactics = []` (не вызывается TacticExtractor)
   - `top_recommendation` — заглушка
   - `chat_summary` — структурный (без LLM)
   - Старый rule-based код (~650 строк) в том же файле — мёртвый груз

3. **Pipeline 2 нерабочий.** CIOrchestrator имеет два пути выполнения:
   - `execute_ci_analysis()` → `_execute_single_phase()` → `_get_agent()` → реально работает
   - `execute_task()` → `_execute_single_agent()` → `_delegate_to_agent()` → возвращает `{"status": "delegated"}` без реального выполнения

4. **TW агенты (фазы 11-15) не существуют.** `_get_agent()` возвращает None для tw-competitor-scout, tw-creative-collector, tw-creative-analyzer, tw-pattern-finder, tw-traffic-analyzer.

5. **SEO аудит возвращает пустые WOW-цифры.** `_compact_audit_result()` читает `findings["phase_7"]`, но при `tier: "quick"` фаза 7 не выполняется.

## Что реально работает (точно)

- `ci_scout.py` — поиск конкурентов (DaData + Google Maps)
- `ci_auditor.py` — аудит сайтов (28 проверок: technical, content, UX, marketing)
- `doctor_extractor.py` — извлечение врачей из HTML + influence scoring
- `pipeline_runner.py` — сбор данных (financials, SEO, social, website, reviews)
- `comparison_matrix.py` — построение матрицы для LLM
- Пресс-релизный `/api/competitors/analyze/stream` — возвращает результаты (хоть и без тактик)

## Вопросы, на которые нужен ответ

1. Как унифицировать два пайплайна? Оставить один или два?
2. В каком порядке доделывать? Что priority #1?
3. Стоит ли сохранять CIOrchestrator с 16 фазами или упростить архитектуру?
4. Как правильно реализовать EventBus-делегирование между агентом и оркестратором?
5. Нужны ли TW агенты (рекламная разведка) на данном этапе?

## Полный аудит

См. `00-OVERVIEW.md` — детальный разбор системы со ссылками на конкретные строки кода.
