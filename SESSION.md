# Session: 2026-06-18 — Hermes: Качество отчётов и следование пайплайну ✅

## Текущий фокус: Исправление качества работы Hermes (инструменты, pipeline, отчёты) ✅

### Диагностика (корень проблемы)
1. **Инструменты не импортировались** — `__init__.py` регистрировал 17 из 42 доступных инструментов
2. **3PHASE_PIPELINE.md не загружался в промпт** — был только документацией, не в system prompt
3. **Отчёты с inline-стилями** — `publish_scout_report.py` использовал inline styles вместо CSS-классов
4. **CSS-классы отсутствовали** — theme.css не имел классов `.gap`, `.section-label`, `.text-dim` и др.
5. **generate_html_report.py — syntax error** — nested f-string с backslash (Python 3.11)
6. **pymysql не установлен** — зависимость для WordPress-публикации отчётов

### Что сделано
- ✅ `__init__.py` переписан: 42 инструмента с try/except защитой от импорт-ошибок
- ✅ 37 инструментов успешно регистрируются (было 17)
- ✅ `generate_html_report.py` — исправлен syntax error (f-string → concat) + импорт (session_archive)
- ✅ `pymysql` установлен в контейнер
- ✅ `publish_scout_report.py` — все inline-стили заменены на CSS-классы
- ✅ `theme.css` +120 строк недостающих классов (`[data-aim="report"]`)
- ✅ `agent_wrapper.py` — `load_pipeline_md()` загружает 3PHASE_PIPELINE.md в PRESALE-промпт
- ✅ `copy_soul.sh` — копирует 3PHASE_PIPELINE.md в `$HERMES_HOME`
- ✅ 3PHASE_PIPELINE.md (255 строк) доступен в контейнере `/opt/data/`
- ✅ Все файлы синхронизированы: контейнер → хост → локальный репо

### Состояние контейнера aim-hermes
- **Инструменты:** 37 AIM operations + 15 debug = 52 total
- **Pipeline:** загружается лениво при первом PRESALE-запросе
- **SOUL.md:** 39892 chars, загружается при каждом запросе
- **Brave Search:** 402 ошибка (Usage limit exceeded) — нужно решить отдельно
- **pymysql:** установлен (НЕ переживёт пересборку образа — добавить в Dockerfile!)

### Что ещё нужно
- 🔴 Brave Search API key — usage limit exceeded, нужно пополнить/сменить ключ
- 🟡 Добавить `pymysql` в Dockerfile (сейчас только в контейнере через pip install)
- 🟡 Пересобрать Docker-образ, чтобы изменения в app/ коде не потерялись
- 🟡 Обновить модель Hermes (deepseek-chat → более capable модель)

### Предыдущая задача: Telegram-идентификация ✅
- `TELEGRAM_ADMIN_CHAT_ID=322367335` в hermes-fresh
- Кодовое слово «Привет зайка» для ADMIN-режима
- Тон общения: «Вы» с большой буквы для клиентов, «ты» для ADMIN
- SOUL.md синхронизирован (809 строк)
