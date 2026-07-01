# 06 — ПЛАН РЕАЛИЗАЦИИ (этапы)

**Дата:** 1 июля 2026
**Статус:** Дорожная карта для команды
**Длительность:** 17-26 рабочих дней до MVP

---

## 🎯 ОБЩИЙ ПРИНЦИП

**Не "всё сразу". Не "идеально". А "работает end-to-end".**

Каждый этап = атомарная единица работы с чётким результатом. После каждого этапа — smoke test. Перед следующим этапом — коммит и бэкап.

---

## 📅 ПЛАН ПО НЕДЕЛЯМ

### Неделя 1: Чистка и стабилизация (4-5 дней)

**Цель:** Удалить шум, оставить ядро, починить критические баги.

### Неделя 2: Pipeline v2 (5-7 дней)

**Цель:** Чистый PipelineEngine, 13 фаз, гарантированная публикация отчёта.

### Неделя 3: Дизайн-система (4-6 дней)

**Цель:** Все scout-посты в каноническом дизайне (light + dark + бейджи + ripple).

### Неделя 4: UX и стабилизация (3-5 дней)

**Цель:** End-to-end пользовательский опыт без шероховатостей.

### Неделя 5: Буфер и polish (2-3 дня)

**Цель:** Запас на баги, тесты, документацию.

---

## 📋 ЭТАП 0: ПОДГОТОВКА (1 день)

### День 0: Бэкап и branched-off

**Задачи:**
- [ ] Создать ветку `aim-v2-rewrite` от текущего main
- [ ] Сделать полный бэкап сервера (`/opt/aim → /opt/aim-backup-20260701`)
- [ ] Сделать дамп MariaDB (`mysqldump wordpress > wordpress-backup.sql`)
- [ ] Сделать дамп SQLite Hermes (`cp /opt/data/state.db state.db.backup`)
- [ ] Зафиксировать текущие working URLs (список scout reports для регрессии)
- [ ] Создать новый docker-compose.yml с минимальным набором сервисов

**Результат:**
- Безопасная точка отката
- Список scout URLs для регрессии
- Чистая ветка для разработки

**Smoke test:**
- Сервер работает после бэкапа
- Все scout URLs открываются (например, `https://iamaim.ru/gkzrghmz`)
- Чат отвечает на `https://iamaim.ru`

---

## 📋 ЭТАП 1: ЧИСТКА (2-3 дня)

### День 1: Удаление мёртвого кода

**Задачи:**
- [ ] Удалить `AIM/src/aim/magisters/` (19 файлов, ~3 MB)
- [ ] Удалить `AIM/src/aim/subagents/` (133 файла, ~5 MB)
- [ ] Удалить `AIM/src/aim/events/` (EventBus, 2692 строки)
- [ ] Удалить `test_vault_*` папки (7 папок)
- [ ] Удалить `backup-june24-work-*` (полная копия)
- [ ] Удалить `.venv` если есть
- [ ] Удалить `*.bak`, `*.backup-*` файлы (30+ штук)
- [ ] Удалить `aim-paperclip` контейнер и образ (2.76 GB)
- [ ] Удалить `/opt/data/bin/tirith` (22 MB бинарник)
- [ ] Удалить дубликат `meai` framework (один из двух)

**Smoke test:**
- Hermes container стартует без ошибок
- Чат отвечает
- 67 tools зарегистрированы (пока не уменьшаем)
- Smoke: `curl https://iamaim.ru/api/chat -d '{"message":"test"}'`

### День 2: Удаление лишних контейнеров

**Задачи:**
- [ ] Остановить `aim-paperclip` (если ещё работает)
- [ ] Остановить `aim-frontend` (Next.js, не нужен)
- [ ] Остановить `aim-postgres` (PostgreSQL, не нужен в MVP)
- [ ] Остановить `aim-headroom` (если установлен)
- [ ] Обновить `docker-compose.yml`: оставить 4 контейнера (nginx, wordpress, hermes, mysql) + redis (опционально)
- [ ] Удалить осиротевшие Docker volumes
- [ ] Удалить осиротевшие Docker images

**Результат:**
- 4-5 контейнеров вместо 16
- ~8 GB диска освобождено

**Smoke test:**
- `docker compose up -d` работает
- Все нужные контейнеры running
- `docker compose ps` показывает только нужные

### День 3: Фикс критических багов

**Задачи:**
- [ ] **Синхронизировать SOUL.md** (исправить рассинхрон 106 KB vs 47 KB)
  - Выбрать: какая версия canonical (рекомендация — новая 47 KB)
  - Обновить `/opt/data/SOUL.md` из `/opt/hermes/skills/aim/SOUL.md`
  - Поправить `copy_soul.sh`: всегда перезаписывать
- [ ] **Починить session_archive** (или отключить если не нужно)
  - Прогнать тестовый pipeline
  - Если 14 ошибок "failed to save" — найти причину
  - Либо фикс, либо отключить archive (pipeline работает в памяти)
- [ ] **Убрать дублирующие tools** из реестра
  - Цель: 67 → 30 tools
  - Скрыть от LLM внутренние (orchestrate, finalize_research, read_report_reference)
- [ ] **Переименовать mode** PRESALE → ANALYSIS (опционально, требует согласования)

**Smoke test:**
- SOUL.md: `wc -c /opt/data/SOUL.md` = `wc -c /opt/hermes/skills/aim/SOUL.md`
- Pipeline log: 0 ошибок session_archive
- Tools registry: 30 tools visible to LLM

---

## 📋 ЭТАП 2: PIPELINE v2 (5-7 дней)

### День 4: Рефакторинг PipelineEngine

**Файлы:**
- `AIM/hermes/app/pipeline/engine.py` — основной
- `AIM/hermes/app/pipeline/phases.py` — описание 13 фаз
- `AIM/hermes/app/pipeline/states.py` — state machine

**Задачи:**
- [ ] Прочитать существующий engine.py полностью
- [ ] Упростить: убрать fallback логику, оставить один путь
- [ ] Чёткие названия методов: `_execute_phase_0_prescan()`, `_execute_phase_1_competitors()` и т.д.
- [ ] Логи: каждая фаза = INFO "Phase X started" + INFO "Phase X finished in Ys"
- [ ] Error handling: если фаза падает — записать в state.phases[phase_id].error, НЕ прерывать pipeline
- [ ] Timeout: каждая фаза = max 90s, иначе timed_out

**Результат:**
- engine.py = 400-500 строк (сейчас ~1000+)
- Понятная последовательность фаз
- Чёткие логи для дебага

**Smoke test:**
- `python -m pytest AIM/hermes/tests/test_pipeline.py`
- Прогон на example.ru = 3-4 минуты, 13/13 фаз completed

### День 5: Фаза 0-3 (prescan + competitors + tech + reviews)

**Задачи:**
- [ ] Фаза 0 (prescan/market research): Perplexity API call, parse JSON, save to session_archive
- [ ] Фаза 1 (competitors): Apify actor, parse results, filter commercial clinics, save
- [ ] Фаза 2 (tech audit): Lighthouse + run_tech_seo_audit, parse metrics, save
- [ ] Фаза 3 (reviews): 2ГИС + Яндекс.Карты + ПроДокторов парсинг, save

**Каждая фаза:**
- Отдельный метод в engine.py
- Прогресс через callback (`_phase_progress()`)
- Save to `session_archive.upsert(slug, phase_id, data)`
- Error handling (return `PhaseResult(status=permanent_failure, error=str(e))`)

**Smoke test:**
- Каждая фаза отдельно: `python -c "from app.pipeline.engine import _execute_phase_0; ..."`
- Pipeline на example.ru фазы 0-3 completed

### День 6: Фаза 4-9 (content, doctors, smi, forums, finance, content-plan)

**Задачи:**
- [ ] Фаза 4: `run_content_analysis` (firecrawl сайта клиники)
- [ ] Фаза 5: `find_doctor_handles` (Instagram, VK, Telegram врачей)
- [ ] Фаза 6: `run_smi_mentions` (Brave + Perplexity search)
- [ ] Фаза 7: `run_forum_pains` (Pro-Talks, MedicalFirm, etc.)
- [ ] Фаза 8: `find_company_financials` (nalog.ru ГИР БО)
- [ ] Фаза 9: `run_content_gaps` (LLM synthesis на основе фаз 0-8)

**Smoke test:**
- Pipeline на реальной клинике (diamond-clinic.ru): 9/13 фаз completed
- Время: <6 минут до этого этапа

### День 7: Фаза 10-12 (build_report + qc + publish)

**Задачи:**
- [ ] Фаза 10: `build_report.py` — НОВЫЙ генератор отчётов (см. Этап 3)
- [ ] Фаза 11: `run_validation_check` (QC чек-лист)
  - Проверить что в отчёте есть все 10 секций
  - Проверить что есть минимальный набор данных (название, город, хотя бы 1 конкурент)
  - Если critical данные отсутствуют — пометить report как "partial"
- [ ] Фаза 12: `publish_scout_report` — INSERT в wp_posts
  - post_type = 'page'
  - post_status = 'publish'
  - post_name = random 8-char slug
  - post_content = HTML (с DOCTYPE)

**Smoke test:**
- Полный pipeline на example.ru: 13/13 фаз completed
- report_url возвращает рабочий URL
- HTML валидный (начинается с `<!DOCTYPE`, заканчивается `</html>`)

### День 8-9: Тестирование и стабилизация

**Задачи:**
- [ ] Прогнать pipeline на 5 тестовых URLs:
  - example.ru (тестовый)
  - iphk.ru (реальная клиника)
  - diamond-clinic.ru (реальная)
  - test-clinic.tilda.ws (Tilda сайт)
  - gov-test.gbuz.ru (государственная — должна быть фильтр)
- [ ] Для каждого: проверить что отчёт published, открывается, валидный HTML
- [ ] Тайминги: записать min/avg/max для каждого URL
- [ ] Баг-репорты: фикс критических, остальные в backlog
- [ ] Документация: обновить `app/pipeline/README.md`

**Результат этапа:**
- 5 рабочих scout reports на сервере
- Среднее время pipeline: 5-8 минут
- 0 критических багов

---

## 📋 ЭТАП 3: ДИЗАЙН-СИСТЕМА (4-6 дней)

### День 10: Создание `build_report.py`

**Задачи:**
- [ ] Создать новый файл `AIM/hermes/app/tools/build_report.py`
- [ ] Структура: `_build_html(data, title, url, date)` функция
- [ ] Шаблон: HTML с DOCTYPE, head с Google Fonts (Jost + Playfair Display), все CSS переменные (см. документ 04)
- [ ] Включить ВСЕ компоненты:
  - [ ] Theme toggle button + JavaScript
  - [ ] Water ripple rings (light theme only)
  - [ ] Background ambient glow
  - [ ] Container + section
  - [ ] Sec-tag
  - [ ] Glass-card
  - [ ] Glass-stats-wrap + glass-stat (с animation)
  - [ ] Metric-tag (5 цветов)
  - [ ] Surface-block (green + red)
  - [ ] Glass-table-wrap
  - [ ] CTA-box
  - [ ] Print styles

**Размер:** 600-800 строк Python + HTML template

**Smoke test:**
- `python -c "from app.tools.build_report import _build_html; print(_build_html({}, 'test', '', '')[:200])"`
- HTML начинается с `<!DOCTYPE html>`
- HTML содержит `'Jost'` (НЕ Inter)
- HTML содержит `'metric-tag-green'`

### День 11: Конвертация данных в секции

**Задачи:**
- [ ] Функция `_md_to_html(markdown)` для конверсии markdown в HTML секции
- [ ] Функция `_build_section_market(data)` — секция "Рынок"
- [ ] Функция `_build_section_competitors(data)` — секция "Конкуренты"
- [ ] Функция `_build_section_tech(data)` — секция "Тех.аудит"
- [ ] Функция `_build_section_reviews(data)` — секция "Отзывы"
- [ ] Функция `_build_section_content(data)` — секция "Контент"
- [ ] Функция `_build_section_doctors(data)` — секция "Врачи"
- [ ] Функция `_build_section_smi(data)` — секция "СМИ"
- [ ] Функция `_build_section_finances(data)` — секция "Финансы"
- [ ] Функция `_build_section_recommendations(data)` — секция "Рекомендации"

**Каждая функция:**
- Принимает dict с данными фазы
- Возвращает HTML строку `<section>...</section>`
- Использует только canonical компоненты (документ 04)
- Адаптируется под отсутствие данных ("Данных по этой секции не найдено")

**Smoke test:**
- Каждая функция отдельно: `_build_section_competitors({...})` → HTML строка
- Полный отчёт: 10 секций на тестовых данных

### День 12: Подключение build_report к pipeline

**Задачи:**
- [ ] Заменить в `engine.py` фазе 10: `generate_html_report._build_report_html` → `build_report._build_html`
- [ ] Удалить старый `generate_html_report.py` (698 строк)
- [ ] Удалить `generate_html_report_v7_backup.py`
- [ ] Прогнать полный pipeline, проверить что новый отчёт в canonical дизайне

**Smoke test:**
- Pipeline: фаза 10 successful, HTML generated
- HTML содержит все canonical классы: `.glass-card`, `.metric-tag`, `.surface-block`, `.glass-table-wrap`
- HTML валидный (без unclosed tags)

### День 13: Миграция старых scout reports

**Задачи:**
- [ ] Найти все scout-посты в wp_posts (post_name REGEXP '^[a-z0-9]{8}$' + DOCTYPE)
- [ ] Для каждого: извлечь body, переопределить секции, обернуть в новый canonical HTML
- [ ] Использовать `migrate_scout_design.py` как базу, но с полным canonical дизайном
- [ ] Прогнать миграцию для всех scout reports (около 17-30 постов)
- [ ] Smoke test: открыть 3-5 случайных scout reports, проверить canonical

**Smoke test:**
- Все scout reports имеют theme toggle (JavaScript работает)
- Все имеют glass cards с анимацией
- Все имеют бейджи (где применимо)
- Все имеют surface-block-green/red

### День 14-15: Тестирование дизайн-системы

**Задачи:**
- [ ] Открыть 5 разных scout reports в разных браузерах (Chrome, Safari, Firefox)
- [ ] Проверить light theme: монументально-чёрный на белом
- [ ] Проверить dark theme: Art Deco gold на тёмном
- [ ] Проверить theme toggle: переключение сохраняется в localStorage
- [ ] Проверить responsive: 1920px, 1366px, 768px, 375px (iPhone SE)
- [ ] Проверить print: `Cmd+P` → корректный print preview
- [ ] Lighthouse audit: 90+ на Performance, Accessibility, Best Practices

**Баг-репорты:**
- Список CSS/HTML проблем
- Приоритет: P0 (блокирует), P1 (некрасиво), P2 (minor)
- Фикс P0 и P1

---

## 📋 ЭТАП 4: UX И СТАБИЛИЗАЦИЯ (3-5 дней)

### День 16: Чат-интерфейс

**Задачи:**
- [ ] Проверить chat-inline.php (bubble widget)
- [ ] Проверить chat-pro.html (full-page chat)
- [ ] Проверить прогресс-бар (13 фаз с emoji)
- [ ] Whisper-комментарии во время pipeline (опционально)
- [ ] Theme toggle работает в чате

**Smoke test:**
- Открыть `https://iamaim.ru` → кликнуть bubble → отправить URL → прогресс виден
- Открыть `https://iamaim.ru/chat` → отправить URL → прогресс виден
- Theme toggle работает в обоих режимах

### День 17: SOUL.md обновление

**Задачи:**
- [ ] Прочитать текущий SOUL.md (47 KB версия)
- [ ] Удалить упоминания "арми AI-агентов", "магистров", "субагентов"
- [ ] Обновить identity: "Hermes — AI-аналитик для медицинских клиник"
- [ ] Обновить tool catalog: оставить только 15-20 актуальных tools
- [ ] Убрать упоминания pipeline v3, v4, v6 (только v7)
- [ ] Убрать цены (если есть)
- [ ] Убрать слово "пресейл" (если есть в user-facing частях)

**Результат:**
- SOUL.md: 25-35 KB (сейчас 47 KB)
- Identity = аналитик, не оператор
- Tool catalog актуальный

**Smoke test:**
- Hermes отвечает на "привет" корректно (3 предложения, без "Operator")
- Hermes не упоминает магистров/субагентов
- Hermes знает про 15-20 tools

### День 18: PRESALE промпт (или ANALYSIS)

**Задачи:**
- [ ] Прочитать текущий `_presale_prompt()` в agent_wrapper.py
- [ ] Убедиться что правило "вызови ТОЛЬКО run_full_scout" на месте
- [ ] Добавить: жёсткий формат 3 сообщений (контраст → точки роста → отчёт)
- [ ] Добавить: запрещённые слова (пресейл, КП, купить, заказать)
- [ ] (Опционально) Переименовать в `_analysis_prompt()` если решено

**Smoke test:**
- Прогнать pipeline, проверить что Hermes отправил РОВНО 3 сообщения
- В сообщениях нет запрещённых слов

### День 19: Стабилизация

**Задачи:**
- [ ] Прогнать 10 полных pipeline на разных URL
- [ ] Записать тайминги
- [ ] Зафиксировать все баги
- [ ] Фикс P0 и P1 багов
- [ ] Документация: обновить CLAUDE.md, MEMORY.md
- [ ] Обновить `SESSION.md` и `.current-task` до актуального состояния

**Результат:**
- 10 рабочих scout reports
- 0 критических багов
- Документация актуальна

### День 20: Финальный smoke test

**End-to-end тест:**
- [ ] Михаил открывает `https://iamaim.ru`
- [ ] Кликает "Разобрать мою клинику"
- [ ] Вбивает `https://diamond-clinic.ru`
- [ ] Hermes приветствует и запускает pipeline
- [ ] Прогресс-бар стримит 13 фаз
- [ ] Через 6-7 минут — 3 финальных сообщения
- [ ] Михаил кликает ссылку
- [ ] Открывается красивый отчёт (light/dark toggle)
- [ ] В отчёте: 10 секций, бейджи, таблицы, CTA
- [ ] Михаил переключает тему — всё красиво

**Если всё работает — MVP достигнут.** 🎉

---

## 📋 ЭТАП 5: БУФЕР (2-3 дня)

### Бэклог для буферных дней

- [ ] Дополнительные баг-фиксы
- [ ] Performance оптимизация (если pipeline >8 минут)
- [ ] Дополнительные источники данных (Instagram, HH, VK)
- [ ] Telegram bot тестирование
- [ ] Voice messages тестирование
- [ ] Print PDF export (если нужно)
- [ ] Sharing buttons (опционально)
- [ ] Analytics (Yandex.Metrika или Plausible)
- [ ] SEO настройки (noindex для scout, index для лендинга)
- [ ] Sitemap.xml (без scout reports)

---

## 🚨 РИСКИ И МИТИГАЦИЯ

### Риск 1: Pipeline > 10 минут

**Причина:** Внешние API медленные (Perplexity, Lighthouse, ГИР БО)
**Митигация:**
- Параллельные вызовы (asyncio.gather где возможно)
- Кеширование (Redis или SQLite)
- Уменьшение числа фаз для MVP (если 13 не укладываются)

### Риск 2: LLM не вызывает run_full_scout

**Причина:** PRESALE промпт недостаточно жёсткий
**Митигация:**
- Усилить промпт: "ВСЕГДА ВЫЗЫВАЙ ТОЛЬКО run_full_scout. НЕ вызывай другие tools."
- Удалить из реестра отдельные phase tools (тогда LLM не сможет их вызвать)
- Тестировать на разных URL

### Риск 3: WordPress ломает HTML

**Причина:** wpautop или другой фильтр портит post_content
**Митигация:**
- Custom page template с raw echo (уже сделано 1 июля)
- Проверка: `curl https://iamaim.ru/{slug}` → должен вернуть чистый HTML
- Альтернатива: nginx direct serve из `/opt/data/reports/` (минуя WordPress)

### Риск 4: Дизайн-система не полностью применена

**Причина:** build_report.py может пропустить компоненты
**Митигация:**
- Чек-лист (документ 04) перед каждым коммитом
- Визуальная проверка 5 разных отчётов
- Lighthouse audit на каждом отчёте

### Риск 5: Бэкап не работает

**Причина:** Мало места на диске (сейчас 24/69 GB занято)
**Митигация:**
- Полный бэкап на внешний сервер (rsync на backup VPS)
- Дамп БД в S3-совместимое хранилище
- Тест восстановления (поднять backup на тестовом сервере)

---

## ✅ КОНЕЦ ПЛАНА — КРИТЕРИИ MVP

См. `07-SUCCESS-CRITERIA.md`.

**Главный критерий:** Михаил вбивает URL → через 8 минут открывает отчёт → выглядит как canonical reference → MVP достигнут.

---

## 📊 ТАБЛИЦА ПРОГРЕССА

| Этап | Дни | Статус | Ответственный |
|------|-----|--------|---------------|
| 0. Подготовка | 1 | ⏳ Pending | TBD |
| 1. Чистка | 3 | ⏳ Pending | TBD |
| 2. Pipeline v2 | 6 | ⏳ Pending | TBD |
| 3. Дизайн-система | 5 | ⏳ Pending | TBD |
| 4. UX | 4 | ⏳ Pending | TBD |
| 5. Буфер | 2-3 | ⏳ Pending | TBD |
| **ИТОГО** | **21-22** | | |

**Legend:** ⏳ Pending / 🔄 In Progress / ✅ Done / ❌ Blocked

---

*Этот документ — план работы. Любые изменения в этапе = обновление этого файла + согласование с Михаилом.*
