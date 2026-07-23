# REVIEW.md — Phase 13: Data Quality Fix

> **Дата:** 2026-07-23
> **Depth:** standard
> **Файлов рассмотрено:** 7

---

## Сводка

| Severity | Count |
|----------|-------|
| 🔴 Critical | **1** |
| 🟡 Warning | **3** |
| 🔵 Info | **3** |

**Вердикт:** Найден 1 Critical (SSRF). Нужно исправить перед боевым использованием. Warning и Info можно отложить.

---

## 🔴 Critical (1)

### C-1: SSRF — scraper не фильтрует internal IPs

**Файл:** `AIM/hermes-v2/app/tools/website_scraper.py:318`
**Severity:** Critical

```python
async with httpx.AsyncClient(headers=_HEADERS, timeout=_TIMEOUT) as client:
    homepage_html = await _fetch_page(base_url, client)
```

URL приходит от пользователя (через чат) и передаётся напрямую в `httpx.get()`. Нет фильтрации internal IP-адресов. Злоумышленник может отправить:
- `http://169.254.169.254/latest/meta-data/` — AWS metadata (IAM credentials)
- `http://localhost:8000/api/...` — внутренние сервисы
- `http://10.0.0.1/admin` — внутренняя сеть

**Эксплойт:** Пользователь пишет `http://169.254.169.254/latest/meta-data/iam/security-credentials/` в чат → scraper скачивает → данные попадают в LLM ответ.

**Решение:**
```python
import ipaddress
from urllib.parse import urlparse

def _is_safe_url(url: str) -> bool:
    """Проверить что URL не указывает на internal ресурсы."""
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        return False
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return False
    except ValueError:
        pass  # domain name, not IP
    # Block localhost variants
    if hostname in ("localhost", "0.0.0.0", "::1"):
        return False
    return True
```

Добавить вызов `_is_safe_url(base_url)` перед `_fetch_page`.

---

## 🟡 Warning (3)

### W-1: Citation regex удаляет валидные годы `[2024]`

**Файл:** `AIM/hermes-v2/app/tools/perplexity_tools.py:17`
**Severity:** Warning

```python
_CITATION_RE = re.compile(r'\[\d+\](?:\[\d+\])*')
```

Regex `\[\d+\]` матчит не только сноски `[1]`, но и валидные значения:
- `[2024]` — год
- `[2025]` — год
- `[100]` — число

Тест показал: `"Цена [2024]"` → `"Цена "` (год удалён).

**Решение:** Ограничить до 1-2 значных чисел:
```python
_CITATION_RE = re.compile(r'\[\d{1,2}\](?:\[\d{1,2}\])*')
```

### W-2: Scraper делает максимум 4 HTTP запроса последовательно

**Файл:** `AIM/hermes-v2/app/tools/website_scraper.py:344-362`
**Severity:** Warning

Скрейпинг: 1 (главная) + 3 (страницы врачей) = 4 запроса последовательно. Каждый с `timeout=15s`. В худшем случае: 4 × 15 = 60 секунд блокировки.

Это блокирует auto-call pipeline — весь анализ ждёт scraper.

**Решение:** Уменьшить timeout для scraper или параллелить страницы врачей:
```python
# Параллельный скрейпинг страниц врачей
doctor_tasks = [_fetch_page(url, client) for url in doctor_pages[:3]]
doctor_results = await asyncio.gather(*doctor_tasks, return_exceptions=True)
```

### W-3: Scraper не ограничивает размер ответа (DoS)

**Файл:** `AIM/hermes-v2/app/tools/website_scraper.py:38-42`
**Severity:** Warning

`_fetch_page` скачивает полный HTML без ограничения размера. Если сайт вернёт 100MB HTML — scraper съест всю память.

**Решение:** Читать поток с лимитом:
```python
resp = await client.stream("GET", url, follow_redirects=True)
chunks = []
total = 0
async for chunk in resp.aiter_bytes():
    total += len(chunk)
    if total > 5_000_000:  # 5MB max
        break
    chunks.append(chunk)
return b"".join(chunks).decode(resp.encoding or "utf-8", errors="ignore")
```

---

## 🔵 Info (3)

### I-1: `beautiflusoup4` + `lxml` добавлены в requirements без pin версии

**Файл:** `AIM/hermes-v2/requirements.txt`
**Severity:** Info

```
beautifulsoup4==4.12.3
lxml==5.2.2
```

Версии pinned — это хорошо. Но `lxml` имеет известные CVE в старых версиях. 5.2.2 актуальна — OK.

### I-2: `_clean_perplexity_text` вызывается 4 раза (для каждого Perplexity тула)

**Файлы:** `perplexity_tools.py:95, 143, 188, 236`
**Severity:** Info

Очистка применяется к каждому тулу отдельно. Если данные проходят через цепочку тулов (Perplexity → LLM → Perplexity), очистка может применяться многократно. Не критично, но неэффективно.

### I-3: `scrape_clinic_website` в `_FORMATTED_TOOLS` — сырой JSON скрыт от LLM

**Файл:** `AIM/hermes-v2/app/llm.py:29`
**Severity:** Info

```python
_FORMATTED_TOOLS = frozenset({"find_competitors", "extract_clinic_profile", "scrape_clinic_website"})
```

Правильное решение — scraper данные попадают в LLM только через format_profile (врачи, соцсети). LLM не видит сырой JSON скрапа.

---

## ✅ Что сделано хорошо

1. **Website scraper** — новый тул, который реально скрейпит сайт (а не Perplexity). Находит врачей, соцсети, услуги.
2. **og:title extraction** — умный подход для Tilda-сайтов (нет h1, но есть meta og:title).
3. **_clean_perplexity_text** — централизованная очистка от сносок, применяется ко всем Perplexity тулам.
4. **3 уровня очистки citation markers** — Perplexity tools → streaming → final text. Надёжно.
5. **Промпт улучшен** — «ОПИРАЙСЯ на данные» вместо «ЗАПРЕЩЕНО повторять». LLM теперь использует реальные данные.
6. **URL → brand name** — если Perplexity дал wrong name, отзывы всё равно ищутся (через домен).
7. **Scraper интегрирован в auto-call** — выполняется автоматически, данные обогащают profile_cache.

---

## Рекомендации (приоритизированы)

| # | Что | Когда | Сложность |
|---|-----|-------|-----------|
| **1** | **C-1: SSRF фильтр** (internal IPs) | **Срочно** | 30 мин |
| 2 | W-1: Ограничить citation regex до `\d{1,2}` | Следующая итерация | 5 мин |
| 3 | W-3: Лимит размера ответа (5MB) | Следующая итерация | 15 мин |
| 4 | W-2: Параллельный скрейпинг страниц врачей | Опционально | 20 мин |

---

## Заключение

Phase 13 значительно улучшила качество данных (scraper, промпт, очистка). Найден **1 Critical (SSRF)** — нужно исправить. Остальные Warning — известные ограничения, не блокируют функциональность.
