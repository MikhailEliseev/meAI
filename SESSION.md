# Session: 2026-07-03 — Pipeline v5 → v6 Quality Analysis

## 🎯 ТЕКУЩИЙ СТАТУС: АНАЛИЗ КАЧЕСТВА ЗАВЕРШЁН, ПЛАН v6 ГОТОВ

**Pipeline v5 ДОШЁЛ ДО КОНЦА впервые за 2 месяца разработки** (3 июля 2026, 12:27 UTC)

3 клиента протестированы end-to-end:
- `arclinic.ru` (СПб, anti-age) → отчёт `8099wt3p`
- `mira-med.ru` (Екатеринбург, семейная) → отчёт `waouaein`
- `iphk.ru` (Москва, пластическая хирургия) → отчёт `59ddggd3`

**Время:** ~14 минут на полный pipeline (13 фаз).

**ВАЖНО:** Проведён детальный анализ качества отчётов. Выявлены критические проблемы с данными (0 конкурентов, отсутствие врачей с Instagram). План улучшений → `PIPELINE-V6-QUALITY-IMPROVEMENT-PLAN.md`

---

## ✅ Что было сделано (3 июля 2026)

### Исправлено 4 бага + 1 скрытый P0c:

| Баг | Файл | Было → Стало |
|---|---|---|
| **P0** SSE timeout | `functions.php:183` | `CURLOPT_TIMEOUT 120 → 1200` |
| **P0b** SSE deadline | `main.py:482` | `_SSE_DEADLINE 420 → 1200` |
| **P0c** fastcgi timeout | `nginx iamaim.conf` | `fastcgi_read_timeout 300 → 1200` |
| **P1** URL fallback | NEW `_url_utils.py` | Общий helper + 7 tool handlers обновлены |
| **P2** session_archive | `session_archive.py:52` | `key.replace("/", "_")` + engine.py `/` → `_` |
| **P3** HTML BUILD | (симптом P2) | Починился автоматически |

### Создано файлов:
- `AIM/hermes/app/tools/_url_utils.py` — URL extraction & recovery helper

### Git теги:
- `pipeline-v5-working-e2e` (HEAD commit `3399726`)

### Бэкапы:
- Сервер: `/opt/hermes-backups/pipeline-v5-working-20260703-124759/`
- Локально: `~/Desktop/Dev/meAI_1-backups/pipeline-v5-working-20260703/pipeline-v5-backup.tar.gz` (2.9 MB)

---

## 🔍 Анализ качества данных (3 июля 2026, 13:20-13:56 UTC)

### Проведён детальный root cause analysis

**Сравнение:** Эталонный отчёт (старая версия) vs Pipeline v5 (session 71b5e599-5fd)

**Критические находки:**
- ❌ **Конкуренты:** 8 → **0 конкурентов** (вернулся только ЛАНЦЕТЪ — подразделение самого ИПХиК)
- ❌ **Врачи:** 15 врачей с Instagram → **5 врачей БЕЗ Instagram handles**
- ❌ **Метрики:** Детальные Instagram метрики → **НЕТ ДАННЫХ**
- ❌ **Контент-анализ:** Deep audit 20 Reels × 4 врача → **НЕТ АНАЛИЗА**

**Root cause:**
1. `find_competitors` fallback не срабатывает при низком качестве (только при пустоте)
2. `find_doctor_handles` не вызывался (не в списке обязательных инструментов)
3. Interpretation промпты "оправдывают" плохие данные вместо сообщения о проблеме

**Решение:** План улучшений для Pipeline v6 → `PIPELINE-V6-QUALITY-IMPROVEMENT-PLAN.md`

**Архитектурное улучшение (13:21 UTC):**
- ✅ Миграция с Docker volume на bind mount
- ✅ Сырые данные теперь доступны по пути `/opt/hermes-data/sessions-archive/`
- ✅ 68 сессий скопированы на хост
- ✅ Контейнер перезапущен успешно

---

## ✅ Pipeline v6 внедрён (3 июля 2026, 14:18-14:24 UTC)

**Статус:** DEPLOYED TO PRODUCTION

**Время внедрения:** 6 минут (14:18-14:24 UTC)

**Внедрённые улучшения:**
- FIX #1: Улучшена fallback логика find_competitors (quality score)
- FIX #2: Обязательный вызов find_doctor_handles в SOUL.md
- FIX #3: Валидация качества в generate_html_report

**Git:**
- Commit: `ceea4c5` — feat: Pipeline v6 quality improvements (FIX #1-#3)
- Tag: `pipeline-v6-quality-fixes`

**Backup:** `/opt/hermes-backups/pre-pipeline-v6-20260703-172258.tar.gz` (34KB)

**Контейнер:** aim-hermes перезапущен, статус `healthy` ✅

---

## 📋 Следующие приоритеты

1. ✅ ~~**Качество данных**~~ — анализ завершён, внедрён
2. ✅ ~~**Внедрение Pipeline v6**~~ — FIX #1-#3 развёрнуты на production
3. **E2E тест Pipeline v6** — протестировать на iphk.ru / новой клинике
4. **Дизайн чата** — улучшение UI/UX

---

## 🔧 Текущая конфигурация production

```
Hermes: aim-hermes container (healthy)
Model: glm-5.2 via z.ai (HeadroomGuard отключён)
Pipeline: 13 phases, ~14 min
Timeouts (все 20 мин):
  - Hermes _SSE_DEADLINE: 1200s
  - WordPress CURLOPT_TIMEOUT: 1200s
  - Nginx fastcgi_read_timeout: 1200s
  - Nginx proxy_read_timeout (/api/chat): 600s
SOUL.md: 105K
```

## Тестовые сессии (для future reference)

| Сессия | Клиент | URL отчёта | Дата |
|---|---|---|---|
| `fa3c0ba7-fbc` | arclinic.ru | https://iamaim.ru/8099wt3p | 2026-07-03 |
| `b13bcaca-e86` | mira-med.ru | https://iamaim.ru/waouaein | 2026-07-03 |
| `71b5e599-5fd` | iphk.ru | https://iamaim.ru/59ddggd3 | 2026-07-03 |

## Известные мелкие проблемы (не блокируют)

- ❌ `run_pagespeed` падает с Lighthouse error (fallback через `_direct_technical_audit` работает)
- ❌ `generate_html_report` падает с MySQL publish error (fallback через `publish_scout_report` работает)
- ❌ Telegram bot: 401 Unauthorized (давняя проблема, не наша)

---

## ⚠️ ПРЕДУПРЕЖДЕНИЕ

**Никогда не откатывайся ниже commit `3db5f18` (2026-07-03 02:24)** — там ещё не было P1-P2 фиксов. Полностью рабочий коммит: `3399726` (с tag `pipeline-v5-working-e2e`).

В случае отката:
```bash
git checkout pipeline-v5-working-e2e -- AIM/
ssh aim "cd /opt/hermes-backups/pipeline-v5-working-20260703-124759"
```
