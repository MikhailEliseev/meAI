# Phase 4: Базовый сценарий (база → кнопки → по запросу) — Context

**Gathered:** 2026-07-14
**Status:** Ready for implementation

<domain>
## Phase Boundary

Формализация сценария «база → кнопки → по запросу» в backend. Phase 3 доказал что модель САМА вызывает quick_overview + find_competitors по URL — но это было стихийно. Phase 4 делает это надёжным через усиленный промпт + добавляет SSE-событие `suggestions` с адаптивными кнопками.

**Что входит в Phase 4:**
- Усиленный системный промпт: жёсткая политика «при URL → база → кнопки → ждёшь»
- SSE-событие `suggestions` (CHAT-01): `{type:"suggestions", buttons:[{label, tool}]}`
- Адаптивная логика кнопок (CHAT-05): модель анализирует результат базы → предлагает 2-4 релевантных действия
- Питч услуг AIM в конце базы (FLOW-04)
- База ≤4 мин (FLOW-02) — проверяется измерением

**Что НЕ входит (Phase 5):**
- Фронтенд: useStreamChat.js обрабатывает suggestions → рендерит кнопки (CHAT-02, CHAT-03)
- Клик по кнопке → действие (CHAT-04)
- Сборка HTML-отчёта (FLOW-06)

</domain>

<decisions>
## Implementation Decisions (locked)

### Промпт — усилить «базовый сценарий»
Phase 3 промпт говорил «проведи базовый анализ». Phase 4 делает жёстче:
- При URL в сообщении → ВСЕГДА вызывай quick_overview + find_competitors (один раз)
- После базы → НЕ вызывай тулзы автоматически
- Предложи кнопки в ТЕКСТЕ ответа (до SSE suggestions)
- В конце базы → короткий питч AIM (1-2 предложения)

### SSE suggestions — как эмитить
Два варианта:
A) Backend сам генерирует кнопки (rule-based: после базы →固定 4 кнопки)
B) Модель возвращает кнопки в ответе, backend парсит

Решение: **гибрид (A+B)**. Промпт просит модель закончить базу спец-маркером `[SUGGESTIONS]` со списком. Backend парсит маркер → эмитит SSE `suggestions` → убирает маркер из текста. Если маркера нет → fallback на rule-based 4 кнопки. Это даёт адаптивность (модель видит результат) + надёжность (fallback).

### Формат suggestions (CHAT-01)
```json
{"type":"suggestions","buttons":[
  {"label":"Глубокий анализ конкурентов","tool":"run_ci_analysis"},
  {"label":"Проверить соцсети","tool":"run_instagram_content"}
]}
```

### Маркер в ответе модели
Модель пишет в конце ответа:
```
[SUGGESTIONS]
Глубокий анализ конкурентов|run_ci_analysis
Проверить соцсети|run_instagram_content
Упоминания в СМИ|run_smi_mentions
[/SUGGESTIONS]
```
Backend парсит, эмитит suggestions, вырезает из текста.

</decisions>

<canonical_refs>
- Spec раздел 5 (промпт), раздел 6 (протокол кнопок)
- Phase 3 SUMMARY — tool-calling уже работает
- AIM/theme/chat/src/useStreamChat.js — фронт (Phase 5 добавит case 'suggestions')
</canonical_refs>

<deferred>
- Фронтенд кнопки (Phase 5)
- generate_html_report (Phase 5)
- run_ci_analysis, run_seo_audit прокси (Phase 3 Wave 2)
</deferred>
