# Hermes v7 — Полный редизайн SOUL.md и личности

Дата: 2026-06-20
Статус: /brainstorming, анализ завершён, написание SOUL.md — waiting for go

---

## 1. Корень проблемы старого Гермеса

**Архитектурный конфликт между SOUL.md и Pipeline Engine:**

| Файл | Что говорит | Проблема |
|------|-------------|----------|
| `SOUL.md:11` | «Я сам решаю, какие инструменты вызвать, в каком порядке» | LLM игнорирует пайплайн |
| `SOUL.md:23` | «Проактивная автономность. Я сам выбираю что и когда запустить» | LLM импровизирует |
| `SOUL.md:117` | «Рекомендуемый поток (не жёсткий скрипт)» | Даёт разрешение отклоняться |
| `SKILL.md:234` | «Рекомендуемый поток (не жёсткий скрипт)» | Дублирует проблему |
| `engine.py:11` | **«LLM — интерпретатор данных, НЕ оркестратор. Python контролирует последовательность.»** | ИСТИНА |

**Результат конфликта:** LLM следовала инструкции «я сам решаю» и пропускала/переставляла фазы пайплайна. Отчёты были неполными.

**Решение:** Переписать SOUL.md так, чтобы он ОТРАЖАЛ реальную архитектуру v7, а не противоречил ей.

---

## 2. Архитектура Pipeline v7 (что обнаружено)

### 2.1. Главный принцип (из engine.py)

```
LLM — интерпретатор данных, НЕ оркестратор.
Python контролирует последовательность и обработку ошибок.
```

PipelineEngine — Python-стейт-машина. Она сама:
- Перебирает PHASES последовательно
- Вызывает tool handlers напрямую (через `_TOOL_HANDLERS` map)
- Обрабатывает ошибки (retry с ротацией ключей)
- Решает, что NO_DATA — легитимный исход
- Персистит данные в `accumulated_data`

LLM используется только для:
- Интерпретации данных каждой фазы (узкий промпт)
- Tool-calling interface (форматирование параметров)

### 2.2. 13 фаз пайплайна (из phases.py:326-340)

```
Phase 0:  PERPLEXITY (Deep Research)  — web_search, Perplexity sonar-pro, 120s
Phase 1:  TECH AUDIT                  — run_pagespeed + run_seo_audit, 300s
Phase 2:  SOCIAL VERIFIER             — run_review_platforms, 180s, allow_no_data
Phase 3:  CONTENT ANALYSIS            — run_content_analysis, 120s
Phase 4:  KEY PERSONS                 — run_hh_analysis + run_doctor_dossiers, 180s, allow_no_data
Phase 5:  SMI MENTIONS                — run_smi_mentions, 120s, allow_no_data
Phase 6:  COMPETITORS                 — find_competitors + run_ci_analysis, 600s, max_retries=3
Phase 7:  FORUM PAINS                 — web_search, 120s, allow_no_data
Phase 8:  FINANCE                     — find_company_financials, 60s, allow_no_data
Phase 9:  CONTENT PLAN                — run_content_gaps, 120s, allow_no_data
Phase 10: HTML BUILD                  — generate_html_report, 120s, interactive
Phase 11: QC CRITIQUE                 — LLM-проверка по 10 пунктам, 90s
Phase 12: PRESENTATION                — publish_scout_report, 60s, interactive
```

**Ключевое:** PERPLEXITY — Фаза 0. Она идёт ПЕРВОЙ и является фундаментом для всех остальных фаз. Именно Perplexity определяет рынок, город, нишу и находит конкурентов.

### 2.3. PhaseContract (states.py:24-40)

```python
max_retries: int = 0           # Максимум повторных попыток
retry_on_key_exhaustion: bool  # Ротировать API-ключи при exhausted
allow_no_data: bool            # NO_DATA = легитимный исход (не ошибка)
timeout: int = 120             # Таймаут в секундах
on_permanent_failure: str      # "skip" — пропустить, "abort" — остановить пайплайн
```

### 2.4. PRE-FLIGHT (пред-фаза, не в основном списке)

Перед запуском фаз Python определяет:
- `client_city` — из /contacts страницы сайта
- `client_specialization` — из главной страницы (title/H1)
- `client_inn` — из /contacts или /rekvizity

Без URL и города пайплайн абортится.

### 2.5. Tool Handler Map (engine.py:40-55)

14 инструментов, каждый привязан к Python-хендлеру:
```
web_search, run_pagespeed, run_seo_audit, find_competitors,
run_review_platforms, run_content_analysis, run_hh_analysis,
run_doctor_dossiers, run_ci_analysis, run_smi_mentions,
run_content_gaps, find_company_financials, generate_html_report,
publish_scout_report
```

### 2.6. PipelineState (states.py:66-92)

```python
session_id, client_url, client_name, client_city,
client_specialization, client_inn, current_phase,
phases: dict[int, PhaseResult], retry_counts,
accumulated_data: dict, started_at, mode
```

---

## 3. Что УДАЛИТЬ из SOUL.md

### 3.1. Автономность (корень проблемы)
- [ ] «Я сам решаю, какие инструменты вызвать, в каком порядке» (строка 11)
- [ ] «Проактивная автономность. Я сам выбираю что и когда запустить» (строка 23)
- [ ] «Рекомендуемый поток (не жёсткий скрипт)» (строка 117)
- [ ] «Если клиент спрашивает про цены — покажи цены… Не заставляй его проходить все шаги» (строка 128)

### 3.2. Старые клиентские уроки
- [ ] «Уроки из реального пресейла (psyholog48, июнь 2026)» — все 8 правил (строки 151-199)
- [ ] Упоминания psyholog48, Центр семейной психологии Выставкиной

### 3.3. Старый пресейл-флоу
- [ ] PRESALE секция с пресейл-пайплайном (run_prescan → find_competitors → CI analysis)
- [ ] «Рекомендуемый поток» из SKILL.md (строка 234)
- [ ] «Что работает хорошо» (живые фразы) — частично сохранить тон

### 3.4. Старый каталог инструментов
- [ ] orchestrate (универсальный оркестратор — не используется)
- [ ] run_prescan (трёхстадийная разведка — заменено пайплайном)
- [ ] find_competitors, present_competitors (заменено пайплайном)
- [ ] run_ads_report, show_project_status (ACTIVE mode — не актуально)
- [ ] collect_contact, qualify_lead, escalate_to_manager (SALES_ADMIN)
- [ ] show_all_leads, get_lead_pipeline (ADMIN tools — отдельно)
- [ ] search_telegram_chats, send_telegram_message
- [ ] hermes-debug toolset (shell_exec, file_read, file_write, api_debug) — Hermes native

### 3.5. Архитектура магистров
- [ ] «Архитектура: Магистры и субагенты» — вся секция (строки 399-425)
- [ ] Списки субагентов (ci_tech_real.py, content_writer_agent.py и т.д.)

### 3.6. Устаревшие детали
- [ ] AIM-APP инструменты (orchestrate, prescan-staged, competitors/find)
- [ ] Упоминания «я вызываю инструменты через orchestrate»
- [ ] ACTIVE mode (для действующих клиентов — не в этом SOUL)
- [ ] SALES_ADMIN mode
- [ ] Multi-entity clinics (деталь реализации, не для SOUL)
- [ ] Российский рынок — ФЗ-152, ЮKassa (детали, не для SOUL)
- [ ] Услуги и цены (от 80 000 ₽/мес и т.д.) — не для SOUL
- [ ] KPI framework (North Star CPA < 2000 ₽)

---

## 4. Что СОХРАНИТЬ из SOUL.md

### 4.1. Идентичность
- [x] «AIM Ассистент» — AI-интерфейс агентства AIM (iamaim.ru)
- [x] «Я НЕ Михаил» — разграничение
- [x] Telegram-интерфейс (без привязки к AIM-APP)

### 4.2. Тон и обращение — ЖЁСТКОЕ ПРАВИЛО
- [x] Клиенты: ВСЕГДА на «Вы», официально-дружелюбный тон
- [x] Запрещено: «привет», «слушай», «смотри», «ты»
- [x] Разрешено: «здравствуйте», «добрый день», «смотрите»
- [x] Михаил (ADMIN): свободный тон, на «ты», прямо и кратко
- [x] Кодовое слово «Привет зайка» — 100% Михаил, полный доступ

### 4.3. Режимы работы
- [x] Telegram chat_id → ADMIN / PRESALE
- [x] «Привет зайка» → немедленно ADMIN
- [x] ADMIN: никаких предложений сверх запроса, минимальный вызов инструмента

### 4.4. Базовые принципы
- [x] «Инструменты, не фантазии» — все цифры из результатов тулов
- [x] «Язык собственника» — пациенты, выручка, сроки
- [x] «Не даю медицинских советов» — «Это решит врач на приёме»
- [x] «Работаю только в коммерческой медицине» — ГАУЗ, ГБУЗ, ГУЗ, МУЗ, МБУЗ НЕ работаем

### 4.5. Знание ниш медицинских клиник
- [x] 7 специализаций (стоматология, косметология, пластическая хирургия, многопрофильная, диагностика, офтальмология, педиатрия)
- [x] Как определять нишу: Title/H1 (×5) > Домен (×3) > Тело страницы (×1)
- [x] Приоритеты: пластическая хирургия > косметология, стоматология > многопрофильная
- [x] Российская специфика: родительный падеж, Bitrix (~70% коммерческих клиник)
- [x] Фильтр гос. учреждений

### 4.6. Правила КП (КОMMЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ)
- [x] Humanization Linter (em-dash, buzzwords, пустые вступления, пассивный залог)
- [x] Client-as-Hero 3:1 (на каждое «мы» — три «вы»/«ваш»)
- [x] Quality Gate (CP Quality Score ≥ 0.80, Red Flags — стоп-отправка)
- [x] 11-блочная структура КП (Executive Summary → … → Конфигуратор)
- [x] Pre-CP Checklist (5 вопросов перед началом)
- [x] Что успех выглядит (What Success Looks Like)
- [x] Cost of Inaction
- [x] Юридическая чистота (ОРД/ЕРИР, ФЗ-38, ФЗ-152)
- [x] Категории услуг: БАЗА/РЕКОМЕНДОВАНО/ОПЦИОНАЛЬНО/СЛЕДУЮЩИЙ ЭТАП
- [x] Чат-выжимка: 3 пункта + цена + результат + ссылка
- [x] Follow-up: 4 касания (multi-channel)
- [x] Сохранение КП в `/opt/data/memories/proposals/[slug]/`
- [x] Confidence Score перед отправкой
- [x] Никаких длинных тире (—) — только дефис (-)

### 4.7. Самообучение
- [x] Память: `/opt/data/memories/`
- [x] Learnings → surprises → patterns → rules
- [x] Консолидация в SOUL.md каждые 10 learnings
- [x] 4 категории GSD: Decisions, Lessons, Patterns, Surprises

### 4.8. Сохранение ключей
- [x] Алгоритм: ключ → CREDENTIALS.md → сообщить → проверить .env
- [x] Структура CREDENTIALS.md

### 4.9. Критические правила
- [x] Bitrix-сайты → ТОЛЬКО browser (web_fetch вернёт пустой контент)
- [x] Не имитирую данные — честно говорю «недоступно»
- [x] При network error — говорю что внутри контейнера
- [x] Фильтрую гос. учреждения

---

## 5. Что ДОБАВИТЬ в новый SOUL.md

### 5.1. ГЛАВНЫЙ ПРИНЦИП (новый)
```
LLM — интерпретатор данных, НЕ оркестратор.
Python (PipelineEngine) контролирует последовательность фаз и обработку ошибок.
Я не выбираю инструменты и не решаю порядок фаз.
Моя роль: анализировать данные, которые собирает пайплайн.
```

### 5.2. Пайплайн как ОБЯЗАТЕЛЬНЫЙ АЛГОРИТМ
- 13 фаз, СТРОГО последовательно
- Никаких «рекомендуемый поток» или «не жёсткий скрипт»
- Фазы нельзя пропускать, переставлять или объединять
- Каждая фаза: название, инструменты, что собирает, таймаут
- PERPLEXITY — Фаза 0, фундамент для всего остального
- PRE-FLIGHT: город и специализация определяются ДО запуска фаз
- NO_DATA — легитимный исход (не ошибка) для фаз с allow_no_data
- PhaseContract: retry с ротацией ключей, abort на критических фазах

### 5.3. Роль LLM в пайплайне
- Интерпретировать данные каждой фазы (узкий промпт)
- НЕ решать, какую фазу запускать следующей
- НЕ пропускать фазы потому что «и так понятно»
- НЕ менять порядок фаз

### 5.4. Описание фаз (адаптированное для SOUL)
Краткое описание каждой из 13 фаз — что делает, какие инструменты, что на выходе.

---

## 6. Структура нового SOUL.md (проект)

```
---
name: aim-operator-v3
description: AIM Operator v3 — Hermes v7 Pipeline Agent. Python-controlled 13-phase onboarding. Telegram interface.
---

# AIM Ассистент v3

## Идентичность
(кто я, что такое AIM, я НЕ Михаил)

## ГЛАВНЫЙ ПРИНЦИП
(LLM — интерпретатор, НЕ оркестратор. Python контролирует.)

## 13-фазный пайплайн — ЖЁСТКИЙ АЛГОРИТМ
### PRE-FLIGHT (город, специализация, ИНН)
### Фаза 0: PERPLEXITY — Deep Research (фундамент)
### Фаза 1: TECH AUDIT — Pagespeed + SEO
### Фаза 2: SOCIAL VERIFIER — Отзывы и рейтинги
### Фаза 3: CONTENT ANALYSIS — Контент сайта
### Фаза 4: KEY PERSONS — Врачи и учредители
### Фаза 5: SMI MENTIONS — Упоминания в СМИ
### Фаза 6: COMPETITORS — Поиск + CI-анализ
### Фаза 7: FORUM PAINS — Боли пациентов
### Фаза 8: FINANCE — Финансовые данные
### Фаза 9: CONTENT PLAN — Контент-план
### Фаза 10: HTML BUILD — Сборка отчёта
### Фаза 11: QC CRITIQUE — Проверка качества (10 пунктов)
### Фаза 12: PRESENTATION — Публикация

## PhaseContract
(NO_DATA, retry, key rotation, abort vs skip)

## Модель
(DeepSeek V4 Pro, не упоминать клиенту)

## Режимы работы
(Telegram chat_id, ADMIN/PRESALE, «Привет зайка»)

## Тон и обращение
(Вы/ты, клиенты/Михаил)

## Знание ниш медицинских клиник
(7 специализаций, приоритеты, российская специфика)

## Правила КП
(Humanization Linter, Client-as-Hero, Quality Gate, 11 блоков, etc.)

## Самообучение
(память, learnings, surprises, patterns, rules)

## Сохранение ключей
(CREDENTIALS.md, алгоритм)

## Критические правила
(Bitrix → browser, не имитировать данные, гос. учреждения, network error)
```

---

## 7. Файлы, которые нужно изменить

| Файл | Действие |
|------|----------|
| `/opt/hermes/skills/aim/SOUL.md` | **Полная перезапись** — новый SOUL-v3 |
| `skills/aim/client-onboarding-pipeline/SKILL.md` | **Удалить или переписать** — убрать «не жёсткий скрипт», заменить на ссылку на SOUL |
| `app/pipeline/phases.py` | Без изменений (эталон) |
| `app/pipeline/engine.py` | Без изменений (эталон) |
| `app/pipeline/states.py` | Без изменений (эталон) |

---

## 8. Ключевые инсайты из анализа

1. **Конфликт SOUL.md ↔ engine.py — главная причина сбоев.** LLM следовала SOUL.md («я сам решаю»), а не пайплайну.

2. **PERPLEXITY должен быть первым.** Фаза 0 даёт фундамент: рынок, конкуренты, тренды. Без него все остальные фазы работают вслепую.

3. **Python — оркестратор, не LLM.** Именно Python перебирает фазы, вызывает tool handlers, обрабатывает ошибки. LLM только интерпретирует данные внутри каждой фазы.

4. **NO_DATA — не ошибка.** Для многих фаз (SOCIAL, KEY PERSONS, SMI, FORUM, FINANCE) отсутствие данных — нормально. Не нужно паниковать или выдумывать цифры.

5. **aim-scout (run_aim_scout.py, 1414 строк) — это альтернативная реализация с другим порядком фаз.** Pipeline v7 (phases.py + engine.py) — правильная версия. aim-scout — исторический артефакт.

6. **SKILL.md дублирует проблему.** Там тоже «Рекомендуемый поток (не жёсткий скрипт)». Нужно синхронизировать с новым SOUL.

7. **Правила КП работают.** Humanization Linter, Quality Gate, Client-as-Hero — это ценное, что нужно сохранить. Они не противоречат пайплайну.

---

## 9. Следующие шаги

1. [ ] Согласовать структуру нового SOUL.md
2. [ ] Написать новый SOUL.md (команда пользователя)
3. [ ] Обновить SKILL.md (убрать «не жёсткий скрипт»)
4. [ ] Задеплоить в контейнер hermes-20.06
5. [ ] Перезапустить gateway
6. [ ] Протестировать на реальном пресейле
