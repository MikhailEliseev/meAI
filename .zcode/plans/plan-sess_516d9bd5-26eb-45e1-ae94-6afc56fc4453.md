# План: Точность данных — клиентский скрапинг + фильтр связанных юрлиц

## Корень: клиентский сайт никогда не скрапится Firecrawl

Все данные о клиенте (CMS, соцсети, врачи) — от Perplexity (угадывает). Firecrawl enrichment работает только для конкурентов.

---

### Фикс 1: Client enrichment в Stage 3.5b (проблемы 2, 3, 4, 5)

**Файл:** `AIM/src/aim/services/competitor_matcher_v2.py`

Добавить client website enrichment рядом с Stage 3.5b:

```python
# ── STAGE 3.5c: CLIENT website enrichment (Firecrawl) ──
if url:
    client_site = await scrape_website(url)  # CMS, размер, соцсети из HTML
    if client_site.get("cms"):
        self.last_client_cms = client_site["cms"]
    if client_site.get("socials"):
        self.last_client_socials = client_site["socials"]
    
    # Врачи клиента
    client_doctors = await scrape_doctors(url, company_name or "")
    if client_doctors:
        self.last_client_doctors = client_doctors
```

Это решает:
- CMS: реальный Bitrix из HTML, не Perplexity-угаданный Tilda
- Соцсети: реальные ссылки из подвала/HTML, не Perplexity-текст
- Врачи: скрап /vrachi на сайте клиента

Новые поля в API response: `client_cms`, `client_socials`, `client_doctors`

### Фикс 2: scrape_website с соцсетями (проблема 3)

**Файл:** `AIM/src/aim/services/lib/firecrawl_enricher.py`

Расширить `scrape_website` — извлекать соцсети из markdown/HTML:

```python
def _extract_socials_from_html(html: str) -> dict:
    """Ищет instagram.com/, vk.com/, t.me/, youtube.com/ в href ссылках."""
    socials = {}
    for platform, pattern in [
        ("instagram", r'href=["\']([^"\']*instagram\.com/[^"\'/?]+)'),
        ("vk", r'href=["\']([^"\']*vk\.com/[^"\'/?]+)'),
        ("telegram", r'href=["\']([^"\']*(?:t\.me|telegram\.me)/[^"\'/?]+)'),
        ("youtube", r'href=["\']([^"\']*youtube\.com/[^"\'/?]+)'),
    ]:
        m = re.search(pattern, html, re.I)
        if m:
            socials[platform] = m.group(1)
    return socials
```

### Фикс 3: profile.py — реальные данные вместо Perplexity (проблема 2)

**Файл:** `AIM/hermes-v2/app/llm.py` — `_build_formatted_blocks`

После `format_profile`, если есть `client_data` из pipeline response:
- `website_platform` ← `client_cms` (Firecrawl, не Perplexity)
- `socials` ← `client_socials` (Firecrawl)
- `doctors` ← `client_doctors` (Firecrawl)

### Фикс 4: Связанные юрлица — ЛАНЦЕТЪ (проблема 1)

**Файл:** `AIM/src/aim/services/competitor_matcher_v2.py`

Два подхода:
**A. ОГРН совпадение** — bo.nalog `get_organization` отдаёт ОГРН. Если competitor ОГРН начинается с тех же цифр что client → связанное юрлицо.
**B. Название-family** — "ЛАНЦЕТЪ" содержит часть имени клиента "Институт пластической хирургии" → связанное.

Простой фильтр: если `competitor.legal_name` содержит 3+ слова из `client.legal_name` → skip.

### Фикс 5: scrape_doctors — больше паттернов + sitemap (проблема 4)

**Файл:** `AIM/src/aim/services/lib/firecrawl_enricher.py`

```python
_DOCTOR_URL_PATTERNS = [
    "/vrachi", "/doctors", "/team", "/specialists", "/staff",
    "/about/doctors", "/o-klinike/vrachi",
    "/specialisty", "/our-team", "/kollektiv",  # НОВЫЕ
    "/klinika/komanda", "/klinik/vrachi",
]
```

Также: если ни один паттерн не сработал → Firecrawl /map → найти URL содержащий "vrach"/"doctor"/"team".

---

## Порядок

```
WAVE 1 (параллельно):
  ├─ 1a: firecrawl_enricher — соцсети из HTML + больше doctor URLs
  └─ 1b: competitor_matcher_v2 — client enrichment + связные юрлица

WAVE 2:
  ├─ 2a: API response — client_cms, client_socials, client_doctors
  └─ 2b: llm.py _build_formatted_blocks — pipeline data для профиля

WAVE 3:
  └─ E2E тест IPHK: Bitrix (не Tilda), IG+VK найдены, врачи посчитаны, ЛАНЦЕТЪ отфильтрован
```

## Что НЕ меняется
- ❌ Стилистика чата (GOLDEN STATE)
- ❌ SSE протокол
- ❌ ФНС данные (выручка, прибыль — уже точные)
- ❌ Конкурент pipeline (уже работает)