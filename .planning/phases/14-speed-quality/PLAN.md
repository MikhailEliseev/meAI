# PLAN.md — Phase 14: Speed & Quality Optimization

> **Создан:** 2026-07-23
> **Приоритет:** 🔴 ВЫСОКИЙ
> **Milestone:** 3

---

## Проблема

Анализ логов выявил 4 проблемы:

1. **🐌 Скорость: 4 минуты на анализ** — тулы выполняются последовательно
2. **🔄 Дублирование: 3 тула собирают одни и те же данные** (extract_clinic_profile + quick_overview + scrape_clinic_website)
3. **🏥 Врачи: специализация = "Санкт-Петербург"** — парсер og:title берёт город вместо специализации
4. **🔒 SSRF: scraper не фильтрует internal IPs**

---

## Задачи

### Task 1: Параллельный auto-call pipeline (−2 минуты)

**Файл:** `AIM/hermes-v2/app/llm.py`

**Сейчас (последовательно, ~4 мин):**
```
extract_clinic_profile (~10s)
  → scrape_clinic_website (~5s)
    → quick_overview (~15s)
      → find_competitors (~90s)     ← БУТЫЛОЧНОЕ ГОРЛЫШКО
        → company_financials (~5s)
          → run_review_platforms (~60s)  ← ТОЖЕ ДОЛГО
```

**Станет (параллельно, ~2 мин):**
```
Фаза 1 (последовательно, нужен ИНН):
  extract_clinic_profile (~10s)

Фаза 2 (всё параллельно):
  scrape_clinic_website  ──┐
  quick_overview         ──┤
  find_competitors       ──┼── asyncio.gather → ~90s (максимум из группы)
  company_financials     ──┤
  run_review_platforms   ──┘
```

**Реализация:** Заменить последовательные `if` блоки auto-call на `asyncio.gather()`:
```python
# Все auto-calls после extract_clinic_profile — параллельно
tasks = []
if "scrape_clinic_website" not in collected_results:
    tasks.append(_do_scrape(...))
if "find_competitors" not in collected_results:
    tasks.append(_do_competitors(...))
if "company_financials" not in collected_results:
    tasks.append(_do_financials(...))
if "run_review_platforms" not in collected_results:
    tasks.append(_do_reviews(...))

results = await asyncio.gather(*tasks, return_exceptions=True)
```

**Ожидаемое время: 4 мин → ~2 мин** (экономия ~50%).

### Task 2: Объединить extract_clinic_profile + quick_overview

**Файлы:**
- `AIM/hermes-v2/app/tools/perplexity_tools.py`
- `AIM/hermes-v2/app/llm.py`

**Сейчас:** Два отдельных Perplexity вызова с похожими промптами (~25 сек суммарно).

**Станет:** Один вызов `extract_clinic_profile` с расширенным промптом (включает врачей, соцсети, услуги). `quick_overview` — убрать из auto-call (оставить как ручной тул).

**Промпт `EXTRACT_PROFILE_PROMPT` расширить:**
```json
{
  "inn": "...",
  "company_name": "...",
  "brand_name": "...",
  "specialization": "...",
  "city": "...",
  "address": "...",
  "services": ["..."],
  "website_platform": "...",
  "doctors": [{"name": "...", "specialization": "..."}],
  "social_media": {"instagram": "...", "vk": "...", "telegram": "..."},
  "founded_year": "..."
}
```

**Экономия:** ~15 сек + меньше дублирования данных.

### Task 3: Починить специализацию врачей

**Файл:** `AIM/hermes-v2/app/tools/website_scraper.py`

**Сейчас:** `og:title` = `"Рубаник Кирилл Сергеевич - врач ARclinic, Санкт-Петербург"` → парсер берёт `"Санкт-Петербург"` как специализацию.

**Станет:** Парсер убирает название клиники и город из специализации:
```python
# Было:
spec_part = parts[1].strip()

# Станет:
spec_part = re.sub(
    r'\b(?:врач|ARclinic|клиник[аи]?|Санкт-Петербург|Москва|Россия|г\.)\b',
    '', spec_part, flags=re.I
).strip(" ,.-")
# Если осталась пустота — не записываем специализацию
if not spec_part or len(spec_part) < 3:
    spec_part = ""
```

### Task 4: SSRF фильтр для scraper

**Файл:** `AIM/hermes-v2/app/tools/website_scraper.py`

Добавить `_is_safe_url()` проверку перед `_fetch_page()`:
```python
import ipaddress

def _is_safe_url(url: str) -> bool:
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        return False
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return False
    except ValueError:
        pass
    if hostname in ("localhost", "0.0.0.0", "::1"):
        return False
    return True
```

### Task 5: Убрать quick_overview из обязательного промпта

**Файл:** `AIM/hermes-v2/app/prompts/dialogue.py`

SYSTEM_PROMPT сейчас просит LLM вызвать 4 тула одновременно:
```
1. extract_clinic_profile
2. quick_overview          ← УБРАТЬ (дублирует scraper + extract)
3. find_competitors
4. run_review_platforms
```

Станет 3 тула (extract даёт расширенные данные, scrape даёт врачей/соцсети):
```
1. extract_clinic_profile  ← расширенный (включает врачей/соцсети)
2. find_competitors
3. run_review_platforms
```

### Task 6: Тесты

- `test_parallel_autocalls` — auto-calls выполняются параллельно
- `test_merged_profile` — extract_clinic_profile возвращает врачей/соцсети
- `test_doctor_spec_clean` — специализация не содержит город
- `test_ssrf_blocked` — internal URLs блокируются

### Task 7: E2E smoke

- Замерить время до/после
- Проверить качество ответа (врачи с правильной специализацией)

---

## Acceptance Criteria

- [ ] Время анализа: 4 мин → ≤2 мин
- [ ] Auto-calls выполняются параллельно (asyncio.gather)
- [ ] extract_clinic_profile возвращает врачей и соцсети
- [ ] quick_overview убран из auto-call
- [ ] Врачи: специализация не содержит название города
- [ ] SSRF: internal IPs блокируются
- [ ] 4/4 unit-теста PASS
- [ ] E2E: arclinic.ru → ≤2 мин, врачи с правильной специализацией

---

## Files to Modify

| File | Changes |
|------|---------|
| `AIM/hermes-v2/app/llm.py` | Параллельные auto-calls, убрать quick_overview из auto |
| `AIM/hermes-v2/app/tools/perplexity_tools.py` | Расширить EXTRACT_PROFILE_PROMPT |
| `AIM/hermes-v2/app/tools/website_scraper.py` | SSRF фильтр, фикс специализации |
| `AIM/hermes-v2/app/prompts/dialogue.py` | Убрать quick_overview из SYSTEM_PROMPT |
| `AIM/hermes-v2/tests/test_phase14_speed.py` | 4 новых теста |

---

## Risks

| Risk | Mitigation |
|------|------------|
| Параллельные тулы падают при ошибке одного | `return_exceptions=True` в gather |
| find_competitors зависит от ИНН из extract | Фаза 1 (extract) выполняется последовательно перед параллельной фазой |
| Расширенный промпт Perplexity медленнее | +2-3 сек, но убирает quick_overview (-15 сек) |
