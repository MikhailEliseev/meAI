# PLAN.md — Phase 13: Data Quality Fix (КРИТИЧНО)

> **Создан:** 2026-07-23
> **Приоритет:** 🔴 МАКСИМАЛЬНЫЙ
> **Milestone:** 3 (Chat Report Delivery)
> **Цель:** Кардинально улучшить качество данных в чате

---

## Проблема

Гермес выдаёт «нейрослоп» — галлюцинирует числа, не находит врачей, соцсети, отзывы. Причины:

1. **Нет скрейпинга сайта клиники** — `extract_clinic_profile` использует Perplexity (поисковик), который не видит страницы сайта
2. **Отзывы ищут по имени, не по URL** — Apify использует `company_name + city`, если Perplexity дал wrong name → нет отзывов
3. **Schema профиля не запрашивает врачей/соцсети** — даже если данные есть, они не возвращаются
4. **LLM запрещают использовать данные** — anti-hallucination создаёт data vacuum

---

## Задачи

### Task 1: Website Scraper — новый тул `scrape_clinic_website`

**Файл:** `AIM/hermes-v2/app/tools/website_scraper.py` (NEW)

**Что делает:** Скрейпит реальный сайт клиники через Firecrawl (уже есть в aim-app) или через прямой HTTP + BeautifulSoup.

**Извлекает:**
- Имена врачей со страниц `/vrachi/`, `/doctors/`, `/team/`, `/specialists/`
- Соцсети из футера/хедера (Instagram, VK, Telegram, YouTube, WhatsApp)
- Услуги с главной или `/services/`
- Контакты (телефон, email, адрес)
- CMS/Tech (Tilda, WordPress, Bitrix — из meta generator)

**Подход:**
1. Скрейпить главную страницу через httpx
2. Найти ссылки на `/vrachi`, `/doctors`, `/team`, `/specialists` (regex)
3. Скрейпить каждую страницу врачей
4. Извлечь имена врачей (CSS selectors: `.doctor-name`, `.doctor-card h3`, `article h2`)
5. Извлечь соцсети из footer/social links (regex `instagram.com/`, `vk.com/`, `t.me/`)
6. Извлечь CMS из `<meta name="generator">` или patterns

**Fallback:** Если httpx не справляется (JS-heavy) → Firecrawl API.

### Task 2: Расширить `extract_clinic_profile` schema

**Файл:** `AIM/hermes-v2/app/tools/perplexity_tools.py:228-276`

Добавить в JSON schema:
```json
{
  "doctors": [{"name": "...", "specialization": "..."}],
  "social_media": {"instagram": "...", "vk": "...", "telegram": "..."},
  "reviews_summary": "Краткое описание репутации"
}
```

### Task 3: Использовать URL для поиска отзывов

**Файлы:**
- `AIM/hermes-v2/app/lib/yandex_reviews.py`
- `AIM/hermes-v2/app/lib/gis2_reviews.py`

Добавить поиск по URL (если Apify actor поддерживает) или извлекать название из URL для более точного поиска.

### Task 4: Ослабить anti-hallucination — разрешить LLM использовать данные

**Файл:** `AIM/hermes-v2/app/llm.py:762-787`

Изменить инструкцию: вместо «НЕ повторяй данные» → «Опирайся на конкретные данные из секций выше. Приводи цифры. Не выдумывай — если данных нет, так и скажи.»

### Task 5: Улучшить SYSTEM_PROMPT — фокус на grounded answers

**Файл:** `AIM/hermes-v2/app/prompts/dialogue.py`

Добавить чёткие правила:
- «Каждый вывод должен опираться на конкретный факт из данных выше»
- «Если данных нет — пиши 'информация не найдена', не выдумывай»
- «Приводи 2-3 конкретных числа в каждом абзаце»

### Task 6: Интегрировать website_scraper в pipeline

**Файл:** `AIM/hermes-v2/app/llm.py`

Добавить `scrape_clinic_website` в auto-call последовательность:
1. extract_clinic_profile (Perplexity — INN, название)
2. **scrape_clinic_website (NEW — врачи, соцсети, услуги)** ← НОВЫЙ
3. find_competitors (ФНС + SearXNG)
4. run_review_platforms (Apify)
5. company_financials (ФНС)

### Task 7: Обновить форматоры — показывать врачей и соцсети

**Файлы:**
- `AIM/hermes-v2/app/formatters/profile.py` — добавить блок врачей
- `AIM/hermes-v2/app/formatters/overview.py` — надёжный парсер

### Task 8: Тесты + E2E

---

## Acceptance Criteria

- [ ] Website scraper находит врачей на сайте клиники
- [ ] Website scraper находит соцсети (Instagram, VK, Telegram)
- [ ] Отзывы находятся для 90% клиник (не только по имени)
- [ ] LLM не галлюцинирует — использует реальные данные
- [ ] В чате видны конкретные имена врачей, ссылки на соцсети, рейтинги
- [ ] E2E: arclinic.ru → врачи найдены, соцсети найдены, отзывы найдены
