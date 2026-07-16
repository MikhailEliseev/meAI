# Phase 5: Deep Interpretation - Context

**Gathered:** 2026-06-24 (--auto mode — user sleeping)
**Status:** Ready for planning

<domain>
## Phase Boundary

Переписать `interpretation_prompt` для каждой фазы/секции под референс `ИПХиК (2).html`: нарратив с конкретными выводами (не «дамп метрик»), cross-linked секции, бизнес-язык, gap-blocks в формате strength+growth-point, blockquote с главным инсайтом.

**Внутри scope:**
- Переписать интерпретационные промпты для всех 10 секций под нарратив
- Cross-linking: страхи пациентов (04) → gaps врачей (04) → стратегия (09) → offer (10)
- Бизнес-язык: «каждая секунда задержки теряет пациентов» вместо «LCP 7.3s»
- Gap-blocks: ✅ сильная сторона (с цифрой) + 📍 точка роста (с ориентиром на конкурента)
- Blockquote с главным strategic insight в каждой секции

**Вне scope:**
- Новые секции (Phase 4 closed this)
- Новые источники данных (Phase 4 closed this)
- SOUL.md/SKILL.md sync (Phase 6)
- Тесты на 3 нишах (Phase 7)
- Деплой (Phase 8 — но plan 05-XX может включать docker cp если изменения промптов меняют runtime)

</domain>

<decisions>
## Implementation Decisions

### Narrative Rewrite Strategy (INT-01)

- **D-01:** Вместо переписывания N отдельных `interpretation_prompt` (старый v3/v7 паттерн) — подойти через **Pass 3 prompt extension**. Phase 4 Plan 04-05 уже добавил правила для контента секций в Pass 3. Phase 5 добавляет **нарративные правила** к тем же элементам.
- **D-02:** Нарративный стиль = LLM получает явное правило «каждая секция = 2-3 параграфа связанного текста с выводами и цифрами, НЕ маркированный список метрик». Образец — референс `ИПХиК (2).html` (например секция Market: «Клиника ИПХиК стабильно удерживает топ-3 позицию по выручке...» вместо «Выручка: 4.3 млрд, Рост: +26%»).

### Cross-Linking (INT-02)

- **D-03:** Pass 3 prompt содержит явное правило cross-references: «каждая секция должна ссылаться на данные из других секций». Например, Strategy (09) должен упомянуть конкретные страхи из секции 04, gaps из секции 04, рейтинги из DAT-05.
- **D-04:** Реализация: Pass 3 prompt явные фразы «Видя, что {top_fear} из секции 04 — главный страх пациентов, стратегия по направлению Контент должна...». LLM генерит cross-references сама, никаких хардкод-линков.

### Business Language (INT-03)

- **D-05:** Бизнес-язык вместо технического жаргона. Словарь замен в Pass 3 prompt:
  - `LCP 7.3s` → «каждая секунда задержки теряет пациентов»
  - `Bounce rate 65%` → «две трети посетителей уходят, не дочитав»
  - `CLS 0.4` → «контент прыгает при загрузке — выглядит непрофессионально»
  - `DA 25` → «поисковики слабо доверяют сайту»
  - `Backlinks 45` → «45 сайтов ссылаются на клинику — мало для топ-3»
- **D-06:** Цифры ОСТАЮТСЯ (LCP 7.3s, выручка 4.3 млрд), но сопровождаются человеческой интерпретацией. Не одно вместо другого — оба.

### Gap-Block Format (INT-04)

- **D-07:** Единый формат gap-blocks во всех секциях:
  ```
  ✅ Сильная сторона: {что} ({цифра})
  📍 Точка роста: {что улучшить} — ориентир: {конкурент} ({цифра конкурента})
  ```
- **D-08:** Gap-block рендерится через HTML с design-system классами (.gap-block, .gap-strength, .gap-growth). Glass card styling per existing patterns.

### Section Blockquote (INT-05)

- **D-09:** Каждая из 10 секций заканчивается blockquote с главным strategic insight (1-2 предложения). Формат:
  ```
  > {главный вывод секции в бизнес-языке}
  ```
- **D-10:** Реализация: Pass 3 prompt правило «для каждой секции заканчивать `<blockquote class="section-insight">{главный вывод}</blockquote>`». HTML `_build_*_section` рендеры должны поддерживать optional `insight` kwarg.

### Reference Calibration

- **D-11:** Истина для всех нарративных правил — `/Users/mikhaileliseev/Downloads/ИПХиК (2).html`. LLM получает указание «подражать стилю и глубине референса». Конкретные примеры из референса включаются в Pass 3 prompt как few-shot.

### Implementation Split

- **D-12:** 3 плана:
  - **05-01:** Pass 3 prompt narrative rules (добавить правила D-02, D-03, D-05, D-07, D-09)
  - **05-02:** HTML renderers extend (gap-block component + blockquote support в всех 10 _build_*_section)
  - **05-03:** Reference calibration (extract few-shot examples from reference HTML, add to prompt)

### Claude's Discretion

- Точные формулировки narrative правил (какие именно фразы в Pass 3 prompt)
- Точные few-shot examples из reference HTML (какие цитаты включить)
- HTML классы для gap-block (следовать design-showcase-dual-theme.html)
- Структура blockquote (просто `<blockquote>` или wrapped в section footer)
- Нужно ли split 05-02 на несколько планов если HTML renderers много

### Folded Todos

(нет — cross-reference todos не производился в --auto mode)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Reference HTML Report (CANONICAL)
- `/Users/mikhaileliseev/Downloads/ИПХиК (2).html` — 78KB, 965 lines, 10 sections. Эталон стиля, глубины, бизнес-языка. Downstream agents должны читать и подражать.

### Phase 4 Architecture (where interpretation lives)
- `.planning/phases/04-new-sections-data-depth/04-05-SUMMARY.md` — Pass 3 prompt 9 new rules (where to add narrative rules)
- `.planning/phases/04-new-sections-data-depth/04-06-SUMMARY.md` — HTML data sections (extend with gap-block + blockquote)
- `.planning/phases/04-new-sections-data-depth/04-07-SUMMARY.md` — HTML LLM sections (extend with insight kwargs)
- `AIM/hermes/app/orchestrator/pass_fill_assemble.py` — Pass 3 _build_prompt (PRIMARY TARGET)
- `AIM/hermes/app/tools/generate_html_report.py` — 10 _build_*_section renderers (EXTEND)

### Design System
- `AIM/wordpress-core/wp-content/themes/aim-theme/design-showcase-dual-theme.html` — canonical design-system (gap-block styling, blockquote styling)

### Project-Level
- `.planning/PROJECT.md` — Core value, constraints
- `.planning/REQUIREMENTS.md` §Interpretation (INT-01..05) — Phase 5 requirements
- `CLAUDE.md` — project conventions

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/orchestrator/pass_fill_assemble.py:_build_prompt(state)` — Phase 4 added 9 numbered items (7-15). Phase 5 adds narrative rules as items 16+.
- `app/tools/generate_html_report.py` — 10 `_build_*_section` functions from Phase 3+4. Each should accept new optional kwargs: `insight` (for blockquote) and structured `gap_blocks` list.
- `design-showcase-dual-theme.html` — has `.glass-card`, `.metric-tag` classes; gap-block + blockquote patterns TBD via design system analysis.

### Established Patterns
- **Prompt-driven LLM generation:** Все интерпретации идут через Pass 3 prompt, не через Python код. Phase 5 продолжает этот паттерн.
- **Honest reporting:** «данные недоступны: {reason}» применяется и к нарративу — если данных нет, LLM честно об этом говорит в тексте.
- **Design-system dual theme:** Light monochrome + Dark Art Deco gold. Gap-blocks должны работать в обеих темах.

### Integration Points
- `pass_fill_assemble.py` — добавить narrative rules после Phase 4 items 7-15
- `generate_html_report.py:_build_*_section` — extend с `insight` kwarg, добавить `_render_gap_blocks()` helper
- `_build_report_html` — ensure each section gets insight from Pass 3 output

</code_context>

<specifics>
## Specific Ideas

- Образец стиля — референс `ИПХиК (2).html`. Downstream agents обязаны прочитать и подражать.
- Бизнес-язык с заменами (D-05): LCP→«задержка», Bounce→«уходят», DA→«доверие поисковиков»
- Gap-block единый формат во всех секциях (D-07)
- Blockquote в конце каждой секции (D-09)
- Cross-references между секциями через LLM, не хардкод (D-04)

</specifics>

<deferred>
## Deferred Ideas

- A/B-тестирование разных narrative стилей — backlog (после Phase 7)
- Автоматическая оценка качества нарратива (LLM-as-judge) — backlog
- Динамическая глубина секции (short для маленьких клиник, full для крупных) — backlog
- Перевод отчётов на английский — backlog (после TST-01..05)

</deferred>

---

*Phase: 5-Deep Interpretation*
*Context gathered: 2026-06-24 (--auto mode)*
