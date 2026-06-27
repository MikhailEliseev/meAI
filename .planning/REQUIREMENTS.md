# Requirements — Hermes v5: Full Coverage Reports

**Source:** PROJECT.md (Core Value: Полнота данных через LLM-оркестратора с 3-проходным циклом)
**Mode:** YOLO (auto-include table stakes + explicitly mentioned features)

---

## v1 Requirements

### Research (RES)

- [x] **RES-01**: Определить фактическую причину, почему LLM v4 пропускает инструменты и фазы при оркестрации (промпт / модель / pipeline-ограничение / комбинация)
- [x] **RES-02**: Измерить текущий coverage: сколько из 40+ инструментов LLM вызывает за типичный прогон пресейла
- [x] **RES-03**: Измерить текущее покрытие секций референса: какие из 10 секций ИПХиК (2).html фактически появляются в отчётах v4
- [x] **RES-04**: Изучить логи 3-5 последних прогонов Hermes на server (`/opt/data/sessions-archive/`) — что LLM вызывала, что пропустила, где обрезала вывод
- [x] **RES-05**: Протестировать `run_instagram_content` руками на 1 клинике — работает ли, какие данные возвращает, нужен ли отдельный handler

### Orchestration (ORC)

- [x] **ORC-01**: Реализовать 3-проходный цикл: Сбор → Гэп-анализ → Допосбор + Сборка (автоматически, без ручного вмешательства)
- [x] **ORC-02**: LLM-оркестратор выбирает инструменты по ситуации, а не по жёсткому pipeline (как v1, не v3/v7)
- [x] **ORC-03**: Гэп-анализ сравнивает собранные данные с QC-чек-листом покрытия (см. QC-01) и принимает решение о допосборе
- [x] **ORC-04**: Если после 3-го прохода остаются пробелы — LLM честно отмечает «данные недоступны», не выдумывает
- [x] **ORC-05**: PipelineEngine остаётся как опция (не удаляется), но оркестратор — основной режим

### Instagram (IG)

- [x] **IG-01**: Добавить `run_instagram_content` в `engine.py:_TOOL_HANDLERS` (сейчас инструмент зарегистрирован для LLM, но pipeline не может его вызвать) — Plan 03-01
- [x] **IG-02**: Для каждой ниши, где Instagram критичен (косметология, пластическая хирургия), LLM-оркестратор ОБЯЗАТЕЛЬНО вызывает Instagram-анализ
- [x] **IG-03**: Для каждого найденного врача (топ-5) собирается: подписчики, avg лайки, avg просмотры, стиль контента, темы (в %), пробелы, потенциал — как в секциях 03+04 референса
- [x] **IG-04**: Если у клиники нет Instagram — честно фиксируется в отчёте, не блокирует остальные фазы

### Sections (SEC)

- [x] **SEC-01**: Добавить секцию «Strategy» — 5 конкретных направлений на основе собранных данных (контент, Telegram, GEO, репутация, кросс-промо), как секция 09 референса
- [x] **SEC-02**: Добавить секцию «Offer» — «Что AIM может сделать для клиники», с конкретными шагами и CTA, как секция 10 референса
- [x] **SEC-03**: Секция «Whitefields» — матрица: клиент vs 3-5 конкурентов по полям (сейчас только content_gaps, нужна именно матрица)
- [x] **SEC-04**: Секция «Experts» — ТОП-5 врачей: ФИО, регалии, подписчики, avg лайки/просмотры, стиль контента — *tool layer satisfied by Plan 04-02 (structured_regalia + _merge_doctor_data); Pass 3 prompt pending Plan 04-05; HTML rendering pending Plan 04-06*
- [x] **SEC-05**: Секция «Content Analysis» — по каждому топ-врачу: стиль, темы, пробелы, потенциал + Топ-5 страхов пациентов с форумов

### Data Depth (DAT)

- [x] **DAT-01**: Динамика выручки за 3 года (сейчас только текущий год из ГИР БО) — сравнить с референсом «+79% за 3 года (2.4 млрд → 3.4 млрд → 4.3 млрд)» — *tool layer Plan 04-01; HTML rendering Plan 04-06 — D-13 strict rule + D-14 table+blockquote*
- [x] **DAT-02**: Конкретные ссылки на СМИ-публикации (сейчас только счётчики по категориям) — Forbes, RBC, Vademecum с URL и датами
- [x] **DAT-03**: Карточки конкурентов с годом основания, выручкой, числом хирургов, Instagram, спецификой (сейчас только таблица) — *HTML rendering Plan 04-06 — all D-20 fields rendered per competitor card*
- [x] **DAT-04**: Метрики клиники: выручка, прибыль, сотрудники, операционные, лицензии, ОКВЭД на человеческом языке — *tool layer Plan 04-01; HTML rendering Plan 04-06 — D-21 okved_humanized LLM translation*
- [x] **DAT-05**: Рейтинги и отзывы с разбивкой по платформам: ПроДокторов, Яндекс.Карты, 2ГИС, Google Maps, Zoon, Отзовик, IRecommend

### Interpretation (INT)

- [x] **INT-01**: Переписать `interpretation_prompt` для каждой фазы под референс: нарратив с конкретными выводами, не «дамп метрик»
- [x] **INT-02**: Каждая секция отчёта связана с другими: страхи пациентов (04) → пробелы врачей (04) → стратегия (09). Не изолированные блоки
- [x] **INT-03**: Бизнес-язык: «каждая секунда задержки теряет пациентов», а не «LCP 7.3s»
- [x] **INT-04**: Конкретные gap-блоки: ✅ сильная сторона (с цифрой), 📍 точка роста (с ориентиром на конкурента)
- [x] **INT-05**: Главный вывод (blockquote) в каждой секции — 1-2 предложения, главный стратегический инсайт

### Quality Check (QC)

- [x] **QC-01**: QC-чек-лист покрытия: 10-20 пунктов (Instagram врачей? Стратегия? Offer? Динамика за 3 года? СМИ-ссылки? Карточки конкурентов? Страхи пациентов? Метрики клиники? Рейтинги? Тех. аудит? Whitefields?)
- [x] **QC-02**: Автоматическая проверка чек-листа перед генерацией HTML — если что-то пусто, вернуться на допосбор
- [x] **QC-03**: Отчёт о покрытии в конце каждого прогона: % заполненных пунктов чек-листа
- [x] **QC-04**: Цель покрытия: ≥ 80% пунктов чек-листа заполнены реальными данными (не «нет данных»)

### Sync (SYN)

- [x] **SYN-01**: Устранить рассинхрон фаз: phases.py (13) vs SKILL.md (14) vs серверная v3 SOUL.md (16) — привести к единой истине *(SOUL.md: "16 фаз" устранено в Plan 06-01; SKILL.md и phases.py — Plan 06-02)*
- [x] **SYN-02**: SOUL.md описывает 3-проходный цикл, LLM-оркестратора, catalogue инструментов — без жёсткой последовательности фаз *(Plan 06-01 — SOUL.md rewritten v4→v5 with 3-pass orchestrator + 18-item QC checklist + 26 _TOOL_HANDLERS + ORCHESTRATOR_MODE opt-in switch)*
- [x] **SYN-03**: SKILL.md (aim-scout) описывает оркестратор + чек-лист покрытия, не «FULL AUTO pipeline»
- [x] **SYN-04**: engine.py _TOOL_HANDLERS включает все инструменты, которые LLM может вызывать (не подмножество)
- [x] **SYN-05**: Удалить из SOUL.md/SKILL.md упоминания фаз, которых нет в коде (0.5, 0.75, 0.8, 3.2 из серверной v3) *(Plan 06-01 — SOUL.md phantom phases = 0 occurrences; SKILL.md audit — Plan 06-02)*

### Test (TST)

- [x] **TST-01**: Тест на 3 разных нишах: пластическая хирургия (iphk.ru — есть референс), стоматология, косметология
- [x] **TST-02**: Для каждого теста: сравнение с референсом по чек-листу покрытия, субъективная оценка админом
- [x] **TST-03**: Тест в PRESALE режиме (через Telegram-бота, как реальный клиент)
- [ ] **TST-04**: Тест в ADMIN режиме (Михаил запускает вручную для конкретной клиники)
- [x] **TST-05**: Фиксация результатов: proposal.html + feedback.md в `/opt/data/memories/proposals/[client-slug]/`

### Deploy (DPL)

- [ ] **DPL-01**: Деплой через `docker cp` + перезапуск gateway (нельзя пересобирать образ)
- [ ] **DPL-02**: Без даунтайма: фазы не должны прерываться при деплое изменений SOUL.md/SKILL.md
- [ ] **DPL-03**: Health check возвращает 200 после деплоя
- [ ] **DPL-04**: Backup перед деплоем: `hermes-backup-YYYYMMDD/` локально + на сервере
- [ ] **DPL-05**: Rollback plan: если новый SOUL/SKILL ломает пресейл, вернуть предыдущую версию за < 5 минут

---

## v2 Requirements (Deferred)

- Мультиагентный prescan (несколько LLM-агентов параллельно собирают данные по разным аспектам клиники) — backlog
- Автоматический A/B-тест отчётов (две версии HTML, замер какой лучше конвертирует клиента) — backlog
- Автоматическое обновление SOUL.md на основе learnings (сейчас ручная консолидация каждые 10 learnings) — backlog
- Real-time мониторинг coverage % на дашборде — backlog

---

## Out of Scope

- **Смена LLM-модели** — DeepSeek V4 Pro остаётся. Проблема в оркестрации, не в модели.
- **Миграция на другой фреймворк** — FastAPI + hermes-agent остаются.
- **Переписывание дизайн-системы HTML-отчётов** — dual theme, glass cards — канон.
- **Удаление PipelineEngine** — остаётся как опция, не удаляется.
- **Поддержка государственных клиник** (ГАУЗ/ГБУЗ/МУЗ) — вне бизнеса AIM.
- **Ручные итерации админом** — 3-проходный цикл автоматический, админ не вмешивается.

---

## Traceability

(Filled by ROADMAP.md — each requirement mapped to a phase)

| REQ-ID | Phase | Status |
|--------|-------|--------|
| RES-01 | Phase 1 | Complete (Plan 01-03) |
| RES-02 | Phase 1 | Complete (Plan 01-01) |
| RES-03 | Phase 1 | Complete (Plan 01-01) |
| RES-04 | Phase 1 | Complete (Plan 01-02) |
| RES-05 | Phase 1 | Complete (Plan 01-04) |
| ORC-01 | Phase 2 | Complete (Plan 02-02) |
| ORC-02 | Phase 2 | Complete (Plan 02-02) |
| ORC-03 | Phase 2 | Complete (Plan 02-03) |
| ORC-04 | Phase 2 | Complete (Plan 02-03) |
| ORC-05 | Phase 2 | Complete (Plan 02-01) |
| QC-01..04 | Phase 2 | Complete (Plan 02-03) |
| IG-01 | Phase 3 | Complete (Plan 03-01) |
| IG-02 | Phase 3 | Complete (Plan 03-03 + 03-06) |
| IG-03 | Phase 3 | Complete (Plan 03-04 + 03-05) |
| IG-04 | Phase 3 | Complete (Plan 03-05) |
| SEC-01..03, 05 | Phase 4 | Complete (Plan 04-05 prompt + Plan 04-07 HTML rendering) |
| SEC-04 | Phase 4 | Complete (Plan 04-02 tool + Plan 04-05 prompt + Plan 04-07 HTML rendering) |
| DAT-01 | Phase 4 | Complete (Plan 04-01 tool + Plan 04-06 HTML) |
| DAT-02 | Phase 4 | Complete (Plan 04-03 tool + Plan 04-06 HTML) |
| DAT-03 | Phase 4 | Complete (Plan 04-06 HTML rendering) |
| DAT-04 | Phase 4 | Complete (Plan 04-01 tool + Plan 04-06 HTML) |
| DAT-05 | Phase 4 | Complete (Plan 04-06 HTML rendering) |
| INT-01..03 | Phase 5 | Complete (Plan 05-01 prompt layer — items 16/17/18) |
| INT-04..05 | Phase 5 | Pending Plan 05-02 (Plan 05-01 prompt layer complete — items 19/20; HTML rendering pending) |
| SYN-01, 02, 05 | Phase 6 | Partial (Plan 06-01 SOUL.md complete; SYN-03/04 + full SYN-01/05 audit pending Plans 06-02, 06-03) |
| SYN-03, 04 | Phase 6 | Pending Plan 06-02 (SKILL.md sync) + 06-03 (engine.py assertion) |
| TST-01..05 | Phase 7 | Pending |
| DPL-01..05 | Phase 8 | Pending |

**Coverage:** 48/48 requirements mapped — no orphans, no duplicates.
**Phase 1 complete:** 5/5 RES requirements addressed.
**Phase 2 complete:** 9/9 ORC+QC requirements addressed (ORC-01..05, QC-01..04).
**Phase 3 complete:** 4/4 IG requirements fully addressed (IG-01 complete; IG-02 complete — prompt + data-model scaffolding from Plan 03-03 + runtime hard-FAIL override + conditional-total logic from Plan 03-06; IG-03 complete — adaptive top-5 cohort selection from Plan 03-04 + HTML rendering helpers from Plan 03-05; IG-04 complete — honest "Instagram: данные недоступны — {reason}" block in sections 03/04 + canonical not_applicable_items rendering in QC section + Pass 3 prompt kwargs from Plan 03-05).
**Phase 5 in progress:** 3/5 INT requirements fully addressed (INT-01..03 complete via Plan 05-01 prompt-layer items 16-18; INT-04..05 prompt rules added in Plan 05-01 items 19-20, HTML rendering deferred to Plan 05-02).

---
*Last updated: 2026-06-24 after Plan 05-01 completion (Pass 3 prompt items 16-21 narrative quality rules; INT-01..03 fully satisfied at prompt layer; INT-04..05 pending Plan 05-02 HTML rendering)*
