# Requirements: Hermes v7 SOUL Redesign

**Defined:** 2026-06-20
**Core Value:** LLM — интерпретатор данных, НЕ оркестратор. Python (PipelineEngine) контролирует последовательность фаз и обработку ошибок.

## v1 Requirements

### SOUL — Переработка личности

- [ ] **SOUL-01**: Удалён язык автономности («Я сам решаю, какие инструменты вызвать», «Проактивная автономность», «Рекомендуемый поток (не жёсткий скрипт)»)
- [ ] **SOUL-02**: Добавлен главный принцип: «LLM — интерпретатор данных, НЕ оркестратор. Python контролирует последовательность фаз»
- [ ] **SOUL-03**: Вшиты 13 фаз как MANDATORY алгоритм (PERPLEXITY → TECH AUDIT → ... → PRESENTATION)
- [ ] **SOUL-04**: Для каждой фазы указаны: tools, timeout, retries, что делает, задача LLM
- [ ] **SOUL-05**: Таблица PhaseContract со всеми параметрами (max_retries, retry_on_key_exhaustion, allow_no_data, timeout, on_permanent_failure)
- [ ] **SOUL-06**: Сохранены правила тона (Вы/ты, Привет зайка)
- [ ] **SOUL-07**: Сохранены 7 медицинских специализаций и приоритеты определения ниши
- [ ] **SOUL-08**: Сохранены KP-правила (Humanization Linter, Client-as-Hero 3:1, Quality Gate, 11-block structure)
- [ ] **SOUL-09**: Удалены уроки psyholog48 (8 правил)
- [ ] **SOUL-10**: Удалён старый поток пресейла (run_prescan → find_competitors → CI analysis)
- [ ] **SOUL-11**: Удалён каталог старых инструментов (orchestrate, run_prescan, find_competitors)
- [ ] **SOUL-12**: Удалены упоминания Magister-архитектуры

### SKILL — Адаптация client-onboarding-pipeline

- [ ] **SKILL-01**: Убран язык «Рекомендуемый поток (не жёсткий скрипт)»
- [ ] **SKILL-02**: Добавлена ссылка на обязательный 13-фазный пайплайн
- [ ] **SKILL-03**: Удалены ссылки на старый orchestrate tool
- [ ] **SKILL-04**: Удалены ссылки на AIM API endpoints (prescan-staged, competitors/find, competitors/analyze)

### DEAD — Зачистка мёртвого кода

- [ ] **DEAD-01**: Идентифицированы все файлы не в `_TOOL_HANDLERS` (33 файла)
- [ ] **DEAD-02**: Мёртвые тулы удалены из контейнера `hermes-20.06`
- [ ] **DEAD-03**: После удаления пайплайн запускается без ошибок

### DEPLOY — Деплой на сервер

- [ ] **DEPLOY-01**: Новый SOUL.md скопирован в контейнер через `docker cp`
- [ ] **DEPLOY-02**: Новый SKILL.md скопирован в контейнер
- [ ] **DEPLOY-03**: Hermes gateway перезапущен
- [ ] **DEPLOY-04**: Health check пройден
- [ ] **DEPLOY-05**: Пайплайн протестирован на реальном пресейле

## Out of Scope

| Feature | Reason |
|---------|--------|
| Изменение engine.py / phases.py | Пайплайн работает корректно, проблема только в SOUL.md |
| Смена модели (DeepSeek V4 Pro) | Не относится к задаче |
| Пересборка Docker-образа | Деплой через docker cp, без пересборки |
| Добавление новых фаз в пайплайн | Не в scope текущей зачистки |
| Рефакторинг тулов | Только удаление мёртвых, не переписывание |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SOUL-01 | Phase 1 | Pending |
| SOUL-02 | Phase 1 | Pending |
| SOUL-03 | Phase 1 | Pending |
| SOUL-04 | Phase 1 | Pending |
| SOUL-05 | Phase 1 | Pending |
| SOUL-06 | Phase 1 | Pending |
| SOUL-07 | Phase 1 | Pending |
| SOUL-08 | Phase 1 | Pending |
| SOUL-09 | Phase 1 | Pending |
| SOUL-10 | Phase 1 | Pending |
| SOUL-11 | Phase 1 | Pending |
| SOUL-12 | Phase 1 | Pending |
| SKILL-01 | Phase 2 | Pending |
| SKILL-02 | Phase 2 | Pending |
| SKILL-03 | Phase 2 | Pending |
| SKILL-04 | Phase 2 | Pending |
| DEAD-01 | Phase 2 | Pending |
| DEAD-02 | Phase 2 | Pending |
| DEAD-03 | Phase 2 | Pending |
| DEPLOY-01 | Phase 3 | Pending |
| DEPLOY-02 | Phase 3 | Pending |
| DEPLOY-03 | Phase 3 | Pending |
| DEPLOY-04 | Phase 3 | Pending |
| DEPLOY-05 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 24 total
- Mapped to phases: 24
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-20*
*Last updated: 2026-06-20 after initial definition*
