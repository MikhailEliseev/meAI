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

---

## Quality Tasks (golden-test baseline 2026-08-11)

> Добавлено после прогона golden-тестов (`AIM/hermes-v2/golden/`) на 5 клиниках.
> Базлайн: G1 grounding=100% (но это точность, не полнота), **JUDGE=2.5/5**,
> LLM **подавляет реальные данные** (выручка 287M, конкуренты — в данных, но в ответе «не найдено»).

### Q1: Fix data-suppression prompt 🔴 #1 (главное)

**Файл:** `AIM/hermes-v2/app/llm.py:1201-1226` (Path B inline message)

**Проблема:** инструкция «КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО повторять данные… НЕ повторяй НИ ОДНОЙ цифры» заставляет LLM выкидывать выручку/конкурентов и писать «не найдено». Это **противоположность** тому, что нужно.

**Fix:** Свести Path A (`llm.py:964-991`) и Path B к ОДНОЙ согласованной инструкции: «ИСПОЛЬЗУЙ конкретные числа из данных в анализе; не дублируй таблицы целиком, но обязательно ссылайся на ключевые цифры (выручка, рейтинг, конкуренты)».

**Acceptance:** после фикса — 287M / White Aurora / Стамус появляются в ответе implantkrd (видно в golden re-run).

### Q2: Запрет фабрикации качественных деталей 🔴 #2

**Файл:** `AIM/hermes-v2/app/prompts/dialogue.py` + `llm.py`

**Проблема:** LLM выдумывает «ПроДокторов», «детское протезирование 14 упоминаний» (нет в данных).

**Fix:** добавить в промпт: «Не выдумывай названия площадок, имена врачей, темы отзывов и числа упоминаний. Если данных нет — «информация не найдена».»

### Q3: Upstream aim-app 500 + пустые financials 🔴 #3

**Проблема:** `aim-app /api/company-profiles/by-url` → **500** на 3/5 клиник (implantkrd, dentakrd, feniks); «parallel financials: empty» на liteclinic. LLM легитимно не имеет финансов → «не найдено».

**Fix:** дебажить эндпоинт в aim-app (FastAPI). Отдельная подзадача — может требовать доступа к aim-app контейнеру/логам.

### Q4: Temperature (детерминизм) 🟡 #4

**Файлы:** `config.py:17`, `llm.py:755,1229`, `analysis.py:262`

**Fix:** `LLM_TEMPERATURE = 0.25` в config; передать во все `create()`. Снизит разброс прогонов (implantkrd дал 83% в одном прогоне, 100% в другом).

### Q5: Усиление golden-тестов 🟡

- **G6 coverage:** «использовал ли LLM ключевые факты из formatted_blocks?» — поймает подавление данных (G1 точность = 100% вводит в заблуждение).
- **Judge robust:** retry + мягкий парсинг (4/5 ответов judge были пустые → не JSON).

---

## Updated Acceptance Criteria (quality)

- [ ] Q1: implantkrd — выручка 287M и ≥1 конкурент упомянуты в ответе (golden re-run)
- [ ] Q2: нет выдуманных площадок/врачей (judge comment чистый)
- [ ] Q3: aim-app /api/company-profiles/by-url → 200 (или graceful fallback)
- [ ] Q4: LLM_TEMPERATURE задан; разброс G1 между прогонами < 10%
- [ ] Q5: G6 metric добавлен; judge отдаёт JSON на 5/5 кейсов
- [ ] JUDGE avg ≥ 3.5/5 (сейчас 2.5/5 на единственном измеренном)

---

## Wave 2: Stability Tasks (golden-прогон 11 клиник, 2026-08-12)

> Q1-Q5 выполнены и валидированы. Прогон на 11 клиниках (6 краснодарских + ARclinic
> + 5 новых: erasmile/toriclinic/yutskovskaya/delight/olymp) показал: G3=10/11 ✅,
> G7=11/11 ✅ (стабильно), но 3 остаточные проблемы. Цель Wave 2 — добить их.

### Текущий scorecard (baseline Wave 2)

| Метрика | 11 клиник | Вердикт |
|---------|-----------|---------|
| G1 grounding (точность) | 86-90% avg | стабильно ✅ |
| G6 coverage (полнота) | 83% avg, но **yutskovskaya 54%, liteclinic 62%** | 🟡 проседает |
| G3 clean | 10/11 | ✅ почти идеально |
| G5 coherence | **5/11** ❌ | 🔴 массовое false-positive |
| G7 consistency | 11/11 ✅ | стабильно ✅ |
| Ungrounded claims | точечные (1.6, 1736, 4.8…) | 🟡 нужен G8 |

### W1: G5 coherence — точное определение противоречия 🔴

**Файл:** `AIM/hermes-v2/golden/checks.py` (`check_coherence`)

**Проблема:** G5 считает противоречием любые «лидер» + «отстаёт» рядом. Но
«лидер по выручке, отстаёт по цифровому маркетингу» — **легитимный бизнес-вывод**.
Текущая реализация ловит 6/11 ложных срабатываний → бесполезна.

**Fix:** противоречие = утверждение «лидер» и «отстаёт» **по одной и той же метрике**
в одном предложении/абзаце. Не противоречие = разные метрики (выручка vs маркетинг).

**Реализация:**
1. Извлечь claim-ы с привязкой к метрике: «лидер по {выручке}», «отстаёт по {маркетингу}».
2. Противоречие = «лидер по X» + «отстаёт по X» (один X).
3. Разные метрики → pass.

**Acceptance:** на 11 golden-snapshots G5 даёт ≤2 true-противоречия (а не 6 false).
Проверить: `python3 golden/run_golden.py --out /opt/data/golden_new5` (assert, без API).

### W2: G6 coverage — добить «ленивых» клиник 🟡

**Файл:** `AIM/hermes-v2/app/llm.py:965-995` (Path A prompt)

**Проблема:** несмотря на «упомяни КАЖДОГО конкурента» (добавлено в Q1+промпт-фикс),
на части клиник LLM цитирует только половину (yutskovskaya 54%, liteclinic 62%).
Усиление промпта дальше → риск переспама (ответ слишком длинный).

**Подход:** вместо давления на LLM — **структурированный блок сравнения**.
После таблицы конкурентов добавить в formatted_blocks готовый «сравнительный абзац»
с ВСЕМИ конкурентами (кодом, не LLM) — LLM опирается на него как на факты.

**Реализация:**
1. В `_build_formatted_blocks` добавить блок «📊 Сравнение»: клиент vs каждый конкурент
   (выручка в X раз, на Y млн) — генерируется кодом из find_competitors.
2. LLM получает готовую сравнительную фактуру → цитирует всех.

**Acceptance:** yutskovskaya G6 ≥ 75%, liteclinic G6 ≥ 75% (golden re-run).

### W3: G8 — обоснованность чисел (ungrounded claims) 🟡

**Файл:** `AIM/hermes-v2/golden/checks.py` (новый check)

**Проблема:** G1 ловит «число не в данных», но не отличает:
- легитимные производные (287/110 = «в 2.6 раз», 8/287 = «маржа 2.8%»)
- выдумки (нет источников: «1736», «619»)

**Fix:** G8 = «классификация ungrounded-чисел»:
1. Для каждого ungrounded числа проверить: является ли оно **производным** от данных
   (отношение, процент, разница двух grounded чисел)?
2. Если да — пометить «derived» (не нарушение).
3. Если нет — «fabricated» (нарушение).

**Реализация:** в check_grounding добавить derivability-check (число ≈ a/b или a±b для
grounded a,b в пределах 10%). G8 score = fabricated / total_claims.

**Acceptance:** на 11 snapshots G8 классифицирует ≥80% ungrounded как derived/fabricated.
Список «fabricated» — короткий и actionable.

### W4: Judge robustness — починить пустые ответы 🟢

**Файл:** `AIM/hermes-v2/golden/judge.py`

**Проблема:** JUDGE=0.0 на всех кейсах — GLM-5.2 не отдаёт JSON на judge-промпт
даже с retry (3 попытки). Возможно: промпт требует JSON, но модель игнорирует;
или нужен response_format={"type":"json_object"}.

**Fix (опционально, low-priority):**
1. Попробовать `response_format={"type":"json_object"}` (если Z.AI-шлюз поддерживает).
2. Или упростить judge-промпт: «верни только 4 числа через запятую».
3. Или использовать другой judge (но это +квота/зависимости).

**Acceptance:** JUDGE отдаёт число на ≥4/5 кейсах.

---

## Wave 2 — Acceptance Criteria

- [ ] W1: G5 — ≤2 true-противоречия на 11 snapshots (assert, без API)
- [ ] W2: G6 — yutskovskaya и liteclinic ≥ 75% (golden re-run)
- [ ] W3: G8 — классификация ungrounded (derived vs fabricated), ≥80% покрыто
- [ ] W4 (опц.): JUDGE отдаёт число на ≥4/5 кейсах
- [ ] Полный re-run 11 клиник: G3 ≥ 10/11, G6 avg ≥ 80%, G7 11/11

## Files to Modify (Wave 2)

| File | Changes |
|------|---------|
| `golden/checks.py` | W1: rewrite `check_coherence` (metric-bound); W3: add G8 derivability |
| `golden/run_golden.py` | W3: G8 в scorecard |
| `app/llm.py` (`_build_formatted_blocks`) | W2: кодогенерация «сравнительного абзаца» |
| `golden/judge.py` | W4 (опц.): response_format или упрощённый промпт |

## Priorities

| Task | Impact | Effort | Priority |
|------|--------|--------|----------|
| **W1** (G5) | средний (false-positive мешает читать scorecard) | малый (1 функция) | 🔴 первым |
| **W2** (G6) | высокий (качество ответа на «ленивых» клиниках) | средний (кодогенерация + тест) | 🔴 вторым |
| **W3** (G8) | средний (различает производные vs выдумки) | средний (эвристика) | 🟡 третьим |
| **W4** (judge) | низкий (JUDGE всё равно secondary-метрика) | малый-средний | 🟢 опционально |

## Risks

| Risk | Mitigation |
|------|------------|
| W2 кодогенерация блока «сравнение» удлинит formatted_blocks → больше токенов | Блок компактный (5-8 строк), +200 токонов — допустимо |
| W3 derivability-эвристика даёт false-negative (не узнает легитимное) | Порог 10%, ручная проверка списка fabricated |
| W1: сложно извлечь метрику из «лидер по выручке» | Список метрик-ключей (выручка/прибыль/маркетинг/рейтинг/врачи); fallback — если метрики разные → не противоречие |
