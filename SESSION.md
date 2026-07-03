# Session: 2026-07-03 — Pipeline v5 E2E WORKING

## 🎯 ТЕКУЩИЙ ФОКУС: ФИКСАЦИЯ ПОБЕДЫ

**Pipeline v5 ДОШЁЛ ДО КОНЦА впервые за 2 месяца разработки.**

3 клиента протестированы end-to-end:
- `arclinic.ru` (СПб, anti-age) → отчёт `8099wt3p`
- `mira-med.ru` (Екатеринбург, семейная) → отчёт `waouaein`
- `iphk.ru` (Москва, пластическая хирургия) → отчёт `59ddggd3`

**Время:** ~14 минут на полный pipeline (13 фаз).

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

## 📋 Следующие приоритеты (по словам Михаила)

1. **Дизайн чата** — Михаил недоволен текущим UI чата
2. **Качество данных** — в отчётах есть вопросы по качеству

(Эти задачи — следующий этап. Текущее состояние — фиксация и бэкап.)

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
