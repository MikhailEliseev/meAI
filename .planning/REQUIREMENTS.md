# REQUIREMENTS.md — Milestone 2: v3 Feature Parity

> **Создан:** 2026-07-22
> **Milestone:** v3 Feature Parity с v1
> **Фокус:** HTML-отчёты + QC critique
> **Предыдущий milestone:** см. `.planning/MILESTONES.md`

---

## REQ-1: HTML-отчёт на iamaim.ru/{slug}

**Пользовательская история:**
Как владелец клиники, после анализа в чате я хочу получить **ссылку на красивый HTML-отчёт** (iamaim.ru/{slug}), которой могу поделиться с коллегами. Отчёт содержит все 4 секции (профиль, конкуренты, отзывы, аудит) + аналитика, в фирменном дизайне AIM.

**Контекст v1:**
- `build_report.py` (1580 строк) — HTML builder с AIM Design System
- `publish_scout_report.py` (237 строк) — публикация через direct MySQL insertion в WordPress (pymysql)
- Возвращает `https://iamaim.ru/{slug}`

**Требования:**

### REQ-1.1: Сбор данных для отчёта
- Собрать результаты тулов (profile, competitors, reviews, audit, overview) в единую структуру
- Источник: `collected_results` + `profile_cache` из `chat_with_tools`

### REQ-1.2: HTML builder (перенос из v1)
- Перенести `build_report.py` в `hermes-v2/app/report_builder/`
- Адаптировать под v2 формат данных
- Сохранить AIM Design System (шрифты, классы, theme toggle)

### REQ-1.3: Публикация в WordPress
- Через pymysql (direct MySQL insert в wp_posts)
- Генерация случайного slug (6 символов)
- Возврат URL: `https://iamaim.ru/{slug}`

### REQ-1.4: Интеграция в чат
- После завершения анализа, отчёт публикуется автоматически
- SSE-событие `report-ready` с URL
- Фронтенд показывает кнопку «📄 Открыть полный отчёт»

---

## REQ-2: QC Critique

**Пользовательская история:**
Система **проверяет качество отчёта** перед публикацией — заполняет ли он ключевые пункты (ИНН, выручка, врачи, конкуренты, отзывы). Если coverage < 80%, пометить WARN.

**Контекст v1:**
- `qc_checklist.py` (342 строки) — 18-пунктный чеклист v1.2.0
- PASS_THRESHOLD = 80%

**Требования:**

### REQ-2.1: QC чеклист
- Проверка: есть ли данные для каждой категории в `collected_results`
- Возвращает: {item, status: PASS/FAIL, detail}

### REQ-2.2: Интеграция
- QC выполняется ПОСЛЕ сбора данных, ДО публикации
- Результат включается в HTML-отчёт (секция «Качество данных»)

---

## Out of Scope

- ❌ Telegram бот
- ❌ Mode system (PRESALE/ADMIN)
- ❌ Перенос остальных v1 тулов
- ❌ Voice transcriber, Token economy, Knowledge vault
