# Phase 3: Instagram Integration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-23
**Phase:** 3-Instagram Integration
**Areas discussed:** Niche detection, Mandatory mechanism, "Нет Instagram" handling, Doctor discovery flow

---

## Niche Detection

### Q1: Как LLM понимает, что ниша = "Instagram-critical"?

| Option | Description | Selected |
|--------|-------------|----------|
| LLM сама по контексту (Recommended) | LLM читает контент сайта через quick_overview в Pass 1 и сама решает. Гибко, но недетерминированно. Естественный путь в orchestrator-first архитектуре. | ✓ |
| Keyword-list в config | Явный список keywords в config.yaml (косметолог, пластическ, эстетическ, маммопласт, ринопласт). Детерминированно, но требует поддержки словаря. | |
| Гибрид (LLM + keyword-list) | LLM определяет нишу + keyword-list как safety net. Лучшее покрытие, но сложнее реализации. | |
| По ОКВЭД | По справочнику ОКВЭД из ГИР БО. Проблема: косметология часто под общим 86.90. | |

**User's choice:** LLM сама по контексту
**Notes:** —

### Q2: Как механизм определения ниши реализовать технически?

| Option | Description | Selected |
|--------|-------------|----------|
| В ответе Pass 1 | LLM пишет нишу прямо в ответ Pass 1. Orchestrator парсит регуляркой. Просто, но хрупко. | |
| Отдельный mini-call (Recommended) | Orchestrator добавляет короткий второй LLM-вызов между Pass 1 и Pass 2 — да/нет. +1 API вызов (~5с). | ✓ |
| Неявно в Pass 2 | Pass 2 gap-analysis само смотрит: если niche=critical и Instagram не вызван — gap; если niche=other — optional. | |
| Внутри Pass 1 prompt | Pass 1 prompt говорит: если нашёл Instagram-доказательство — обязательно вызови. LLM сама принимает решение. | |

**User's choice:** Отдельный mini-call
**Notes:** —

### Q3: Как быть с boundary cases? (клиника общей хирургии + косметология, стоматология с эстетическими услугами)

| Option | Description | Selected |
|--------|-------------|----------|
| Любое упоминание = critical | Если в услугах хоть одна из косметологии/пластики — critical. Покрытие шире, но иногда IG будет вызываться не для основного профиля. | |
| Только если основной профиль (Recommended) | Если косметология/пластика — основной профиль (>50% услуг или заявлен как главный). Покрытие точнее, но LLM может недооценить. | ✓ |
| Всегда вызывать при сомнении | LLM prompt: если сомневаешься — вызывай. Покрытие максимальное, но больше API трат. | |
| LLM решает сама | Не определять границу. Доверяем LLM вердикту без уточнений. | |

**User's choice:** Только если основной профиль
**Notes:** —

---

## Mandatory Mechanism

### Q1: Как принуждать LLM вызвать Instagram для Instagram-critical ниш?

| Option | Description | Selected |
|--------|-------------|----------|
| Hard-coded orchestrator вызов | Если niche=critical и Instagram не вызван — orchestrator автоматически вызывает в начале Pass 3. 100% гарантия, но нарушает "LLM свободу". | |
| Prompt + QC gate (Recommended) | Pass 1 prompt содержит явное правило. Pass 2 QC gate FAIL если не вызвано. Мягкое принуждение, ~5% шанс LLM забудет. | ✓ |
| Комбинация (3 уровня) | Pass 1 prompt + Pass 2 QC gate FAIL + Pass 3 orchestrator hard-code fallback. 100% coverage + обучение. | |
| Только prompt (минимум) | Только prompt инструкция. LLM сама решает. Самообучение через learnings. | |

**User's choice:** Prompt + QC gate
**Notes:** —

### Q2: Как именно QC gate реагирует на пропуск Instagram для critical niche?

| Option | Description | Selected |
|--------|-------------|----------|
| Soft warning (как Phase 2) | Если пропущен — coverage максимум 14/15 (93%). Это PASS. Но в HTML пометка. Мягкое давление. | |
| Hard FAIL для critical niche (Recommended) | Hard FAIL coverage даже при 14/15. Pass 3 обязательно пытается добрать. | ✓ |
| Per-item critical flag | Instagram item помечен как "critical". Если критический item пропущен — coverage автоматически FAIL. | |
| LLM-judged severity | LLM в Pass 2 оценивает важность пропуска с reason. Orchestrator решает на основе reason. | |

**User's choice:** Hard FAIL для critical niche
**Notes:** —

### Q3: Что если LLM вызвала Instagram, но Perplexity вернул "no data" (handle не найден)?

| Option | Description | Selected |
|--------|-------------|----------|
| Attempt = success | Инструмент вызван — LLM попыталась. Если "no data" — не её fault. QC item = filled с reason. | |
| Retry via find_doctor_handles (Recommended) | Если данных нет — LLM должна попробовать через find_doctor_handles найти альтернативные handles и повторить. Если всё равно нет — QC=filled с reason. | ✓ |
| No data = partial | Если "no data" — QC item=partial. Coverage падает. Pass 3 обязательно пробует альтернативы. | |
| Не различать | Если данных нет в отчёте — пропуска. Простой подход. | |

**User's choice:** Retry via find_doctor_handles
**Notes:** —

---

## "Нет Instagram" Handling

### Q1: Как показать в отчёте, что Instagram данные недоступны?

| Option | Description | Selected |
|--------|-------------|----------|
| Отдельный блок с reason (Recommended) | В HTML отдельный блок в секциях 03+04: "Instagram: данные недоступны — {reason}". Причина из 3-4 вариантов. Честно и прозрачно. | ✓ |
| Прочерки в полях | Секции 03+04 рендерятся как обычно, но avg_likes/avg_views/themes показывают "—". Без явного объяснения. | |
| Скрыть секции | Если у clinic нет Instagram — полностью скрыть секции 03+04 из отчёта. | |
| Блок + баннер | Отдельный блок + баннер в начале отчёта. Двойное уведомление. | |

**User's choice:** Отдельный блок с reason
**Notes:** —

### Q2: Как Instagram item в QC checklist ведёт себя когда данных нет?

| Option | Description | Selected |
|--------|-------------|----------|
| Conditional item (Recommended) | Если niche=non-critical → status=not_applicable. Не считается в покрытии (total=14 вместо 15). Если niche=critical и данных нет после retry → missing с reason. | ✓ |
| Всегда считается | Если данных нет — coverage падает на 1/15. Жёстко, но penalizes клиники без Instagram. | |
| Attempt = filled | Если Instagram реально вызван — item=filled. Покрытие не падает за "no data". | |
| LLM-judged | LLM в Pass 2 сама решает: "достаточно" — filled, реально пусто — missing. | |

**User's choice:** Conditional item
**Notes:** —

---

## Doctor Discovery Flow

### Q1: Откуда берётся список топ-5 врачей для Instagram анализа?

| Option | Description | Selected |
|--------|-------------|----------|
| find_doctor_handles primary (Recommended) | find_doctor_handles — основной источник. Скрейпит сайт клиники, возвращает handles. LLM вызывает сразу после quick_overview. | ✓ |
| LLM primary, find_doctor_handles fallback | LLM сама ищет через web_search + скрейпинг. find_doctor_handles только как fallback. | |
| Merge: find_doctor_handles + LLM search | Оба источника parallel. Merge, dedupe, top-5 по popularity. | |
| Из find_doctor_handles + content_analysis | Из handles + content_analysis без web_search. Может пропустить врачей без website-присутствия. | |

**User's choice:** find_doctor_handles primary
**Notes:** —

### Q2: Как выбрать топ-5 из всех найденных врачей (с учётом "профессора без Instagram")?

| Option | Description | Selected |
|--------|-------------|----------|
| Первые 5 из find_doctor_handles | Простое правило: первые 5 handles (какой порядок возвращает скрейпер). | |
| LLM-сортировка по важности | LLM сортирует врачей по контенту сайта (регалии, отзывы, СМИ). +1 LLM-оценка. | |
| Batch all → top-5 by followers | find_doctor_handles возвращает ВСЕ, run_instagram_content по всем, LLM берёт топ-5 по followers. ~15 handles × 30с = 7-8 мин. | |
| Adaptive: top-5 by site, fallback by followers (Recommended) | find_doctor_handles → top-N. Если top-5 сайта без IG — LLM переупорядочивает по followers_count. Покрытие экспертов + Instagram-active. | ✓ |

**User's choice:** Adaptive: top-5 by site, fallback by followers
**Notes:** Пользователь поднял реальную проблему — профессора и КМН часто не ведут Instagram. Поэтому top-5 по позиции сайта ≠ top-5 по Instagram. Adaptive fallback решает: если топ-5 экспертов без IG — берём Instagram-active из расширенного batch.

### Q3: Сколько handles анализируем в batch?

| Option | Description | Selected |
|--------|-------------|----------|
| Все handles в batches по 5 | Все handles, batch по 5. ~150-500с (до 8 мин). Гарантия: все проанализированы. | |
| Топ-8-10 handles одним batch (Recommended) | Топ-8-10 по позиции сайта, один batch-call. ~90-300с. Баланс: разумный coverage + приемлемое время. | ✓ |
| Strict top-5 (minimum) | Только первые 5. Самый дешёвый, но может полностью пропустить IG-active. | |
| Параллельные batches | 3 параллельных run_instagram_content по 5. 90-180с total. Сложнее реализации. | |

**User's choice:** Топ-8-10 handles одним batch
**Notes:** —

---

## Claude's Discretion

Пользователь не делегировал явных "you decide" решений — все ключевые моменты обсуждены и зафиксированы. Допускается Claude discretion по:
- Точной формулировке prompt для mini-call niche detection
- Структуре HTML-блока «Instagram: данные недоступны»
- Порядку вызовов в Pass 1 (find_doctor_handles vs run_instagram_content)
- Реализации adaptive top-5 fallback

## Deferred Ideas

- Instagram Hashtag Analysis (новый инструмент, отдельная секция) — backlog, Phase 9+
- Instagram Ads Analysis (расходы на продвижение постов врачей) — backlog, Phase 9+
- Reels Performance Analysis (отдельный анализ Reels vs Posts) — backlog, Phase 9+
- TikTok/YouTube Doctors Analysis — другой домен
- Instagram Graph API integration (официальный) — Perplexity сейчас
- Auto-discovery через content_analysis упоминает врачей по имени — future web_search enhancement
