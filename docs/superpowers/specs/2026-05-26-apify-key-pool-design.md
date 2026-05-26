# Apify Key Pool: Round-Robin + Auto-Recovery

**Status:** design  
**Date:** 2026-05-26  
**Scope:** Apify API key rotation service для 200-300 ключей

## Problem

Сейчас один `APIFY_API_TOKEN` в env. Apify free tier = $5/мес на аккаунт. Когда лимит исчерпан — всё падает. Нужно роутить 200-300 ключей с автоматическим переключением при исчерпании.

## Design

### Components

#### 1. `AIM/src/aim/services/apify_key_pool.py` — новый файл

Сервис-пул ключей. Ни от чего не зависит, чистый Python.

```
ApifyKeyPool
├── __init__(keys_file: str)
│   ├── загружает JSON
│   ├── _auto_recover() — реактивирует ключи где exhausted_at + 31d < now
│   └── строит _active_indices из active-ключей
│
├── get_next_key() → str
│   └── round-robin: cursor = (cursor + 1) % len(_active_indices)
│
├── mark_exhausted(token: str)
│   ├── убирает из _active_indices
│   ├── пишет exhausted_at = now в ключ
│   └── атомарно сохраняет JSON (tmp file + os.replace)
│
├── get_stats() → dict
│   └── {total, active, exhausted, last_rotation}
│
├── _auto_recover()
│   └── for key in exhausted: if now - exhausted_at >= 31 days → active
│
└── _save() — атомарная запись JSON
```

**Атомарность:** запись в `.tmp` → `os.replace()` (атомарно на POSIX). При старте если есть `.tmp` старше 60 секунд — удаляем (краш во время записи).

**Thread safety:** `asyncio.Lock` на `get_next_key` и `mark_exhausted`.

#### 2. `AIM/src/aim/services/apify_client.py` — рефакторинг

- **Убрать** `get_apify_client()` синглтон
- **Убрать** circuit breaker (теперь failover на другой ключ — лучшая защита)
- `__init__` принимает `key_pool: ApifyKeyPool`
- При 402/403 или "quota" в сообщении ошибки:
  ```
  key_pool.mark_exhausted(current_token)
  new_token = key_pool.get_next_key()
  self._client = ApifyClientAsync(token=new_token)
  retry call_actor() (1 попытка)
  ```
- Если `get_next_key()` бросает (нет ключей) → `RuntimeError("All Apify keys exhausted")`

#### 3. `AIM/data/apify_keys.json` — хранилище

```json
{
  "keys": [
    {
      "token": "apify_api_...",
      "status": "active",
      "exhausted_at": null,
      "label": "account-001"
    }
  ],
  "stats": {
    "total": 0,
    "active": 0,
    "exhausted": 0,
    "last_rotation": null
  }
}
```

#### 4. `scripts/import_apify_keys.py` — скрипт импорта

Читает TXT (один ключ на строку, `#` — комментарий) → генерирует `apify_keys.json`.

```bash
python scripts/import_apify_keys.py --input keys.txt --output AIM/data/apify_keys.json
```

### Flow

```
ApifyClient.call_actor()
  ↓
  try: await self._client.actor(id).call(...)
  ↓ ApifyApiError(402/403) или "quota exceeded" в тексте
  ↓
  self._key_pool.mark_exhausted(self._current_token)
  ↓
  self._current_token = self._key_pool.get_next_key()
  ↓
  self._client = ApifyClientAsync(token=self._current_token)
  ↓
  retry call_actor() — 1 попытка
  ↓ если опять ошибка → повторяем исключение и пробуем следующий
  ↓ если active ключей 0 → RuntimeError("All Apify keys exhausted")
```

### Что меняется в вызывающем коде

| Файл | Изменение |
|------|-----------|
| `apify_google_maps.py` | Без изменений — использует `client=` опционально |
| `scraping_service.py` | Без изменений |
| `competitor_matcher.py` | `ApifyClient()` → `ApifyClient(key_pool=pool)` |
| Точка входа (FastAPI startup) | Создать `key_pool = ApifyKeyPool("AIM/data/apify_keys.json")` |

### Edge Cases

| Ситуация | Поведение |
|----------|-----------|
| Все 300 ключей exhausted | `RuntimeError`, логгирование, алерт |
| JSON повреждён | При загрузке `json.JSONDecodeError` → попытка читать `.bak` → если нет → `RuntimeError` |
| Параллельные вызовы | `asyncio.Lock` защищает `get_next_key` и `mark_exhausted` |
| Ключ исчерпан посередине вызова | Apify списывает при старте actor'а. Если на ключе оставалось $0.01 — вызов пройдёт, следующий — нет. Реактивный подход не даёт 100% гарантии, это acceptable tradeoff |
| 31-дневный сброс | Проверяется при каждой загрузке пула (старт сервиса). Не требует крона |

### Что НЕ делаем

- Превентивный трекинг usage через `run.usage` — оверхед, реактивного подхода достаточно
- REST API для управления ключами — файла + скрипта импорта достаточно
- Крон для авто-восстановления — проверка при загрузке покрывает
- База данных — JSON на 300 записей это ~20 KB, летает

### Dependencies

Никаких новых. Только `asyncio`, `json`, `os`, `logging`, `datetime` — всё в stdlib.
