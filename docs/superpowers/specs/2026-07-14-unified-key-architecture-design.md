# Единая архитектура управления API-ключами — дизайн-спека

**Дата:** 2026-07-14
**Автор:** ZCode (brainstorming после аудита ключей)
**Подход:** Путь 1 — единый JSON + volume (рекомендация после анализа нагрузки)
**Объём:** Полностью все провайдеры

---

## 1. Контекст — что не так сейчас

Один набор физических ключей размазан по **пяти независимым механизмам хранения** без координации. Состояние расползается, фолбэк-тулы не находят ключи, баги гарантированы.

### Текущий хаос (подтверждён аудитом 2026-07-14)

```
КЛЮЧИ APIFY (13 физических аккаунтов):
  Механизм 1: /opt/aim/AIM/data/apify_keys.json     ← aim-app (ГЛАВНЫЙ)
  Механизм 2: /opt/hermes-data/apify_keys.json      ← hermes
  Механизм 3: /opt/hermes-data/AIM/data/apify_keys.json ← зомби-копия
  Механизм 4: env APIFY_API_TOKEN + APIFY_TOKEN_1..13  ← KeyBank

КЛЮЧИ FIRECRAWL (14 физических аккаунтов):
  Механизм 1: firecrawl_keys.json (2 копии!)        ← FirecrawlKeyBank
  Механизм 2: env FIRECRAWL_KEY_1..14               ← KeyBank (формат A)
  Механизм 3: env FIRECRAWL_API_KEY                 ← fallback
  Механизм 4: env FIRECRAWL_API_KEY_01..14          ← ДУБЛЬ формата A!

КЛЮЧИ ДРУГИХ ПРОВАЙДЕРОВ (только env, без пула):
  BRAVE_API_KEY, GOOGLE_API_KEY, AHREFS_API_KEY,
  SEMRUSH_API_KEY, PERPLEXITY_API_KEY, DEEPSEEK_API_KEY,
  ANTHROPIC_API_KEY, ASSEMBLYAI_API_KEY, TELEGRAM_BOT_TOKEN
```

### Симптомы (из debugging-сессии)
1. **Apify:** aim-app помечал ключи exhausted, hermes не знал → расползание состояния
2. **Firecrawl:** `firecrawl_key_bank.py` не вызывал `_save()` после recovery → ключи залипали в файле навсегда (починено 2026-07-14, но корень — множественные источники)
3. **Фолбэки мертвы:** Crawlee возвращает мусор, Firecrawl делает 3 попытки и падает (KeyBank видит 0 ключей из-за рассинхрона singleton)
4. **Сброс в одном файле не работает:** мы полчаса сбрасывали hermes-копии, а реально работал aim-app-файл

## 2. Целевая архитектура

### Принцип: один провайдер → один файл → один источник правды

```
/opt/aim-keys/                          ← НОВЫЙ единый volume (хост)
├── apify.json          ← 13 ключей Apify (единственный источник)
├── firecrawl.json      ← 14 ключей Firecrawl (единственный источник)
├── serpapi.json        ← (пустой/заготовка, если будут ключи)
├── brave.json          ← (1 ключ, может остаться в env)
└── health.json         ← кэш последних health-чеков (runtime, не конфиг)
```

Монтируется во ВСЕ контейнеры по **одному** пути:
```yaml
# docker-compose.yml — добавляется каждому сервису:
  app:      volumes: [ /opt/aim-keys:/opt/keys:rw ]
  hermes:   volumes: [ /opt/aim-keys:/opt/keys:rw ]
  hermes-v2:volumes: [ /opt/aim-keys:/opt/keys:rw ]
```

### Унифицированная структура JSON (один формат для всех провайдеров)

```json
{
  "provider": "apify",
  "updated_at": "2026-07-14T16:00:00Z",
  "keys": [
    {
      "token": "apify_api_...",
      "label": "key-01",
      "status": "active",
      "exhausted_at": null,
      "exhaust_reason": null,
      "last_checked": "2026-07-14T15:30:00Z",
      "account_email": "sandrahenderson87200@smaqt.com",
      "plan": "FREE",
      "credits_max": 5
    }
  ]
}
```

Единые поля для ВСЕХ провайдеров. `exhaust_reason`: `"rate_limited"` | `"insufficient_credits"` | `"invalid"` | null.

## 3. Унифицированная логика recovery (одна для всех)

Корень бага Firecrawl был в том, что recovery-логика писалась заново для каждого пула. Делаем **один** модуль `key_pool.py`, который используют все провайдеры:

```python
# /opt/aim/AIM/src/aim/services/key_pool.py (НОВЫЙ, унифицированный)

class UnifiedKeyPool:
    """Единый пул ключей с одинаковой recovery-логикой для всех провайдеров."""

    RECOVERY_RULES = {
        "rate_limited":         timedelta(minutes=30),   # временный 429
        "insufficient_credits": "next_billing_month",    # ежемесячный reset
        "invalid":              None,                    # не восстанавливаем (умер ключ)
    }

    def __init__(self, provider: str, file_path: str): ...
    def get_next_key(self) -> str: ...
    def mark_exhausted(self, token: str, reason: str): ...
    def _auto_recover(self): ...   # ВСЕГДА вызывает _save() (фикс бага)
    def _save(self): ...           # атомарный tmp+replace
    def health_check_all(self): ... # пинг каждого ключа через API провайдера
```

**Ключевое правило:** `_auto_recover()` **всегда** вызывает `_save()` если что-то восстановил. Это фикс корневого бага, применённый централизованно.

## 4. План миграции (без даунтайма)

### Шаг 1: Создать единый volume + canonical-файлы
- `mkdir /opt/aim-keys/`
- Извлечь ключи из текущих источников (apify_keys.json + env), дедуплицировать, записать в `/opt/aim-keys/apify.json` и `firecrawl.json` в едином формате
- Структура файла: один ключ = одна запись со всеми полями (включая email/plan из аудита)

### Шаг 2: Смонтировать volume во все контейнеры
- Добавить `volumes: [ /opt/aim-keys:/opt/keys:rw ]` в docker-compose для app, hermes, (future) hermes-v2
- Перезапуск контейнеров

### Шаг 3: Переключить код на единый путь (через env)
Код уже поддерживает `APIFY_KEYS_FILE`, `FIRECRAWL_KEYS_FILE`. Устанавливаем:
```yaml
environment:
  - APIFY_KEYS_FILE=/opt/keys/apify.json
  - FIRECRAWL_KEYS_FILE=/opt/keys/firecrawl.json
```
aim-app читает `/opt/keys/apify.json`, hermes читает ТОТ ЖЕ файл → координация.

### Шаг 4: Заменить разрозненные key_pool классы на UnifiedKeyPool
- `apify_key_pool.py` (aim-app) → делегирует в UnifiedKeyPool("apify", ...)
- `firecrawl_key_bank.py` (hermes) → делегирует в UnifiedKeyPool("firecrawl", ...)
- Старые файлы-копии (`/opt/hermes-data/apify_keys.json` и т.д.) — удалить после подтверждения

### Шаг 5: Health-check endpoint
- `GET /api/keys/health` в aim-app → отчёт: «apify: 13 active, firecrawl: 14 active, brave: 1 active»
- Подключить к мониторингу (Prometheus/Grafana уже есть)

### Шаг 6: Удалить дубль env-ключей
- После миграции: `FIRECRAWL_KEY_1..14` + `FIRECRAWL_API_KEY_01..14` → только `FIRECRAWL_KEYS_FILE=/opt/keys/firecrawl.json`
- Аналогично для Apify

## 5. Что войдёт в каждый файл (провайдеры)

| Провайдер | Источник сейчас | Кол-во ключей | Recovery правило |
|---|---|---|---|
| **Apify** | 3 JSON + env | 13 | insufficient_credits → next month |
| **Firecrawl** | 2 JSON + env×2 формата | 14 | rate_limited 30м + credits next month |
| **SerpAPI** | env (не настроен) | 0 | rate_limited 60с (in-memory OK) |
| **Brave Search** | env BRAVE_API_KEY | 1 | оставить в env (1 ключ, пул не нужен) |
| **Perplexity** | env PERPLEXITY_API_KEY | 1 | оставить в env |
| **DeepSeek/Anthropic/Google/Ahrefs/Semrush/AssemblyAI** | env | по 1 | оставить в env |

**Правило:** в unified-pool идут только провайдеры с **множественными ключами** (Apify 13, Firecrawl 14). Сингл-ключи остаются в env — пул для одного ключа = overkill.

## 6. Фолбэк-скраперы (отдельный подтема)

Аудит 2026-07-14 показал:
- ✅ Scrapy работает
- ✅ DuckDuckGo работает (через Perplexity fallback)
- ❌ Crawlee возвращает мусор (158 байт, не контент)
- ❌ Firecrawl не работает (3 попытки → fail, KeyBank не находит ключи)

После миграции ключей Firecrawl должен заработать (ключи станут доступны). Crawlee требует отдельного разбора (возможно, сломан JS-runtime в контейнере). Это выносится в отдельную задачу, не блокирует архитектуру ключей.

## 7. Риски и митигации

| Риск | Вероятность | Митигация |
|---|---|---|
| Гонка записи (два контейнера пишут exhausted одновременно) | Низкая (~раз в месяц) | Атомарный tmp+replace уже есть; если станет проблемой → Path 2 (микросервис) |
| Потеря файла при миграции | Средняя | Бэкап всех текущих файлов перед шагом 1; git-история |
| Рассинхрон при откате (вернули старый контейнер) | Низкая | env APIFY_KEYS_FILE имеет фолбэк на старый путь |
| Новый путь не смонтирован в каком-то контейнере | Средняя | Health-check endpoint покажет «0 keys» → явный сигнал |

## 8. Критерии успеха

1. Один файл `/opt/aim-keys/apify.json` — единственный источник правды для Apify во ВСЕХ контейнерах
2. `GET /api/keys/health` отдаёт корректный статус всех провайдеров
3. Сброс ключа в одном файле мгновенно виден всем контейнерам (без рестарта)
4. Firecrawl-тулы реально работают (после миграции ключей)
5. Recovery срабатывает автоматически и персистит на диск (фикс `_save()`)
6. Старые файлы-копии удалены (кроме бэкапов)
7. Гермес v2 (когда будет строиться) подключается к `/opt/keys/` из коробки

## 9. Что НЕ входит в скоуп

- Починка Crawlee (отдельная задача — диагностика JS-runtime)
- Микросервис ключей (Path 2) — только если Path 1 покажет гонки в проде
- Авто-пополнение ключей (покупка платных тарифов) — ручное действие
- Миграция SerpAPI (нет ключей — нечего мигрировать)

---

## Эволюция документа
Эта спецификация основана на аудите 2026-07-14. При реализации — сверять с реальным состоянием продакшена. Если Path 1 покажет гонки → переход на Path 2 (микросервис).

**Реализация — отдельной сессией.** Эта спека фиксирует дизайн, чтобы не потерять контекст.
