# Roadmap: Hermes v7 SOUL Redesign

## Overview

Устранение архитектурного конфликта между SOUL.md и PipelineEngine: переписываем SOUL.md (LLM = интерпретатор, не оркестратор), адаптируем SKILL.md, удаляем 33 мёртвых тула, деплоим на сервер и тестируем на реальном пресейле. 3 фазы, последовательное выполнение.

## Phases

- [ ] **Phase 1: SOUL.md — Переработка личности** — Финальный SOUL-v3 и запись в контейнер
- [ ] **Phase 2: SKILL.md + Зачистка мёртвого кода** — Адаптация skill + удаление 33 тулов
- [ ] **Phase 3: Деплой и верификация** — Полный деплой, перезапуск, тест на пресейле

## Phase Details

### Phase 1: SOUL.md — Переработка личности
**Goal**: SOUL-v3.md финализирован, проверен и записан в контейнер hermes-20.06
**Depends on**: Nothing (first phase)
**Requirements**: SOUL-01, SOUL-02, SOUL-03, SOUL-04, SOUL-05, SOUL-06, SOUL-07, SOUL-08, SOUL-09, SOUL-10, SOUL-11, SOUL-12
**Success Criteria** (what must be TRUE):
  1. SOUL.md не содержит фраз «я сам решаю», «проактивная автономность», «не жёсткий скрипт»
  2. Первый раздел SOUL.md: «LLM — интерпретатор данных, НЕ оркестратор»
  3. 13 фаз задокументированы как MANDATORY алгоритм
  4. Сохранены tone rules, 7 специализаций, KP-правила
  5. Удалены psyholog48, старый пресейл, Magister
**Plans**: 1 plan

Plans:
- [ ] 01-01: Финализировать SOUL-v3.md и скопировать в контейнер hermes-20.06

### Phase 2: SKILL.md + Зачистка мёртвого кода
**Goal**: SKILL.md адаптирован, 33 мёртвых тула удалены из контейнера
**Depends on**: Phase 1
**Requirements**: SKILL-01, SKILL-02, SKILL-03, SKILL-04, DEAD-01, DEAD-02, DEAD-03
**Success Criteria** (what must be TRUE):
  1. SKILL.md не содержит «не жёсткий скрипт»
  2. SKILL.md ссылается на обязательный 13-фазный пайплайн
  3. 33 мёртвых файла удалены из /opt/hermes/app/tools/
  4. Pipeline engine запускается без ошибок после удаления
**Plans**: 2 plans

Plans:
- [ ] 02-01: Адаптировать SKILL.md (client-onboarding-pipeline) под v7
- [ ] 02-02: Удалить 33 мёртвых тула из контейнера

### Phase 3: Деплой и верификация
**Goal**: Полный деплой на сервер, перезапуск gateway, тест на реальном пресейле
**Depends on**: Phase 2
**Requirements**: DEPLOY-01, DEPLOY-02, DEPLOY-03, DEPLOY-04, DEPLOY-05
**Success Criteria** (what must be TRUE):
  1. docker cp выполнен для SOUL.md и SKILL.md
  2. Hermes gateway перезапущен без ошибок
  3. Health check возвращает 200
  4. Пайплайн успешно проходит на реальном пресейле (все 13 фаз)
  5. LLM не пытается «выбрать инструменты сама» — следует пайплайну
**Plans**: 2 plans

Plans:
- [ ] 03-01: Деплой SOUL.md, SKILL.md и перезапуск gateway
- [ ] 03-02: Тест на реальном пресейле и финальная верификация

---
*Roadmap defined: 2026-06-20*
*Last updated: 2026-06-20 after initial roadmap creation*
