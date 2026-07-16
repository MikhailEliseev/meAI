# LLM-Based CI Analysis — Design Spec

**Date:** 2026-05-26
**Status:** Approved
**Replaces:** `AIM/src/aim/services/ci_marketing_analysis.py` (rule-based, deterministic)

## Goal

Replace the current rule-based CI analysis (if/else SWOT, pattern-matched tactics) with an LLM-powered system that:
1. Collects real data from 5 sources in parallel (competitors, financials, websites, SEO, social media)
2. Builds a structured ComparisonMatrix (20+ parameters)
3. Uses LLM to generate expert dialogue — step-by-step, data-backed, specific per competitor
4. Shows progress indicators during data collection so users don't leave

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Hermes Operator                       │
│  (PRESALE mode — ведёт диалог с клиентом)                │
└────────────┬────────────────────────────────┬───────────┘
             │                                │
    ┌────────▼──────────┐           ┌─────────▼──────────┐
    │  Pipeline Runner  │           │  Dialogue Manager  │
    │  (сбор данных)     │           │  (LLM-нарратив)    │
    └────────┬──────────┘           └─────────┬──────────┘
             │                                │
    ┌────────▼──────────┐           ┌─────────▼──────────┐
    │  Data Collectors  │           │  ComparisonMatrix   │
    │  (параллельно)     │──────────▶│  (20+ параметров)   │
    └───────────────────┘           └─────────┬──────────┘
                                              │
                                     ┌────────▼──────────┐
                                     │  LLM Narrator     │
                                     │  (hook + диалог)   │
                                     └───────────────────┘
```

### Components

**Pipeline Runner** — orchestrates data collection in parallel, tracks progress, builds ComparisonMatrix, handles caching with per-collector TTLs.

**Data Collectors** (3 existing + 2 new, run in parallel for each competitor):

| # | Collector | Source | TTL | Status |
|---|-----------|--------|-----|--------|
| 1 | CompetitorFinder | Apify Google Maps + DaData INN | 30 days | ✅ Exists |
| 2 | FinancialsCollector | bo.nalog.gov.ru | 30 days | ✅ Exists |
| 3 | WebsiteScraper | Playwright (features, ИНН, соцсети) | 7 days | ✅ Exists |
| 4 | SeoAuditor | Direct scraping (meta, speed, index) | 7 days | 🆕 |
| 5 | SocialScanner | Instagram, Telegram, VK, TikTok | 24 hours | 🆕 |

**ComparisonMatrix** — structured JSON with 20+ parameters for 3-5 competitors + client site. Compact format (~5000 tokens).

**Dialogue Manager + LLM Narrator** — receives the matrix + client data in system prompt, generates:
1. Quick hook (1 paragraph, key data point per competitor)
2. Step-by-step dialogue (user picks which competitor to explore)
3. Follow-up answers (instant — matrix already in context)
4. Comparison with client's own site at every opportunity

### Data Collection Flow

```
Client sends website URL
    │
    ▼
[PROGRESS: "Ищу конкурентов..."]
    │
1. CompetitorFinder (Apify Google Maps)
    │
    ▼
[PROGRESS: "Нашёл 4 конкурента. Собираю данные..."]
    │
2. PARALLEL for each competitor:
   ├── FinancialsCollector  → [PROGRESS: "Смотрю финансовую отчётность..."]
   ├── WebsiteScraper       → [PROGRESS: "Захожу на сайт {name}..."]
   ├── SeoAuditor           → [PROGRESS: "Проверяю SEO {name}..."]
   └── SocialScanner        → [PROGRESS: "Ищу соцсети {name}..."]
    │
    ▼
[PROGRESS: "Сравниваю с вашим сайтом..."]
    │
3. ComparisonMatrix built
    │
    ▼
[PROGRESS: "Готово! Вот что я нашёл..."]
    │
4. Dialogue starts — LLM gets matrix in context
```

### Progress Indicators

At each pipeline step, Hermes sends a brief status message so the user doesn't leave:
- "Ищу конкурентов по вашему сайту..."
- "Нашёл 4 конкурента. Собираю данные о каждом..."
- "Смотрю финансовую отчётность Юцковской..."
- "Захожу на сайт ИПХиК..."
- "Проверяю SEO ошибки на сайте Юцковской..."
- "Ищу соцсети конкурентов..."
- "Сравниваю с вашим сайтом..."
- "Готово! Вот что я нашёл..."

These are system-level messages (not LLM-generated) — emitted by Pipeline Runner between stages.

## SeoAuditor (NEW)

Basic SEO audit without paid APIs (SEMrush/Ahrefs reserved for paid tier):

- Title tag (presence, length, quality)
- Meta description (presence, length)
- H1-H3 structure (missing, duplicate, too many)
- Meta viewport (mobile-friendly check)
- SSL certificate (present/expired)
- Page load speed (basic timing)
- Broken links (status code check on internal links)
- Indexability (robots.txt, canonical, sitemap.xml)
- Social meta tags (og:title, og:image)

**TTL:** 7 days
**Input:** competitor URL
**Output:** `seo: { score: 0-100, issues: [string, ...] }`

## SocialScanner (NEW)

Finds and analyzes competitor social media presence:

- Platform discovery: searches Instagram, Telegram, VK, TikTok by company name
- Basic stats: followers/subscribers, posting frequency
- Recent posts: last 5-10 posts with topics and engagement
- Content formats: photo/video/text/stories distribution
- Top themes: extracted from post titles/descriptions

**TTL:** 24 hours
**Input:** company name
**Output:** `social: { instagram: {...}, telegram: {...}, vk: {...}, tiktok: {...} }`

## ComparisonMatrix Structure

```json
{
  "client": {
    "url": "https://client.ru",
    "name": "...",
    "seo": {"score": 72, "issues": ["..."], "pages_scraped": 15},
    "social": {"instagram": true, "telegram": false, "vk": true, "tiktok": false},
    "features": ["booking", "chat", "pricing_page"]
  },
  "competitors": [
    {
      "id": 1,
      "name": "Юцковская",
      "url": "yutskovskaya.ru",
      "financials": {
        "revenue": {"2025": 242176000, "2024": 218962000},
        "profit": {"2025": 20922000, "2024": 21361000},
        "trend": "growing"
      },
      "seo": {
        "score": 45,
        "issues": [
          "40% pages not indexed",
          "no SSL",
          "missing H1 on 12 pages",
          "slow mobile: 4.2s"
        ]
      },
      "social": {
        "instagram": {"handle": "@yutskovskaya", "posts_month": 3, "avg_likes": 120, "topics": ["laser", "procedures"]},
        "telegram": {"exists": false},
        "vk": {"handle": "@yutskovskaya", "posts_month": 8, "avg_likes": 340, "topics": ["promotions", "doctors"]},
        "tiktok": {"exists": false}
      },
      "website": {
        "features": ["booking", "price_list"],
        "missing": ["chat", "calculator", "reviews_block"],
        "doctors_count": 7,
        "directions_claimed": 15,
        "pricing_visible": true
      },
      "positioning": "клиника профессора, экспертный подход",
      "scraped_at": "2026-05-26T15:00:00Z"
    }
  ]
}
```

## Dialogue Manager

### System Prompt (core rules)

```
Ты — Hermes, AI-аналитик агентства AIM. Твоя задача — провести клиента
через конкурентный анализ. Ты говоришь как эксперт, который реально изучил
конкурентов. Каждый твой вывод подкреплён конкретными данными из матрицы.

ПРАВИЛА:
1. Не выдумывай цифры — бери только из матрицы
2. Если данных нет — честно скажи "по этому параметру данных нет"
3. Сравнивай с сайтом клиента при каждой возможности
4. Веди диалог, не лекцию — спрашивай, интересно ли копнуть глубже
5. Показывай слабые места конкурентов с конкретикой
6. Отвечай на русском, живым экспертный тоном
```

### Dialogue Flow

```
1. HOOK (автоматически, без вопроса)
   "Смотрите, нашёл 4 конкурентов. Юцковская — 242 млн выручки,
    но сайт не индексируется по 40% страниц. ИПХиК — 4.2 млрд,
    но соцсетей практически нет..."

2. OFFER CHOICE
   "По кому показать сравнение первым?"

3. COMPETITOR SHOWCASE (по выбранному конкуренту)
   ├── Финансы: "Вот их выручка, вот прибыль, вот тренд"
   ├── SEO vs клиент: "У них 40% страниц вне индекса, у вас — 5%"
   ├── Соцсети: "В Instagram 3 поста за месяц, у вас — 12"
   ├── Сайт: "Форма записи есть, чата нет, калькулятора нет"
   └── Главная слабость: "Обещают 15 направлений, но 7 врачей"

4. FOLLOW-UP
   "Интересно посмотреть их цены? Или проверим, какие темы
    они гоняют в соцсетях?"

5. NEXT COMPETITOR или SUMMARY
   "Следующий конкурент? Или давайте подведу итог?"
```

### Token Budget

- System prompt: ~500 tokens
- ComparisonMatrix (5 competitors compact): ~5000 tokens
- Dialogue history: ~2000 tokens
- **Total: ~7500 tokens** (within 8K budget)

### Follow-up Questions (instant — no tools called)

Since the matrix is in context, LLM answers follow-ups without re-scraping:
- "А какие у них цены?" → reads matrix, answers
- "Сравни мои соцсети с Юцковской" → client data vs competitor data
- "Что мне сделать чтобы их обойти?" → LLM generates recommendations from gaps

### Client Corrections

If client says "это не мои конкуренты, вот мои: ..." — Hermes restarts Pipeline Runner with new competitor names. New data collection, new matrix, fresh dialogue.

## Caching Strategy

Per-collector TTLs checked before data collection. Cache key = competitor identifier (INN for financials, URL for SEO/website, company name for social).

| Collector | TTL | Rationale |
|-----------|-----|-----------|
| CompetitorFinder | 30 days | Google Maps results change rarely |
| FinancialsCollector | 30 days | Tax filings update once per year |
| WebsiteScraper | 7 days | Website content changes occasionally |
| SeoAuditor | 7 days | SEO changes slowly |
| SocialScanner | 24 hours | Social media activity is daily |

Cache stored in Redis (existing infrastructure).

## Error Handling

Each collector is independent — if one fails, others proceed:

| Failure | Behavior |
|---------|----------|
| Apify API down | "Не смог найти конкурентов автоматически. Скиньте их сайты вручную." |
| nalog.ru unreachable | Matrix without financial data; SEO/social/website still present |
| Competitor website down | No website data for that competitor; financials/social may still exist |
| Social media not found | "Instagram не обнаружен" — this IS an insight |
| All collectors fail for one competitor | Skip competitor, proceed with others |

## Scope

**In scope:**
- Pipeline Runner with parallel collection + progress indicators
- SeoAuditor (basic, no paid APIs)
- SocialScanner (Instagram, Telegram, VK, TikTok)
- ComparisonMatrix (20+ parameters with scoring)
- Dialogue Manager with LLM narrative
- Caching with per-collector TTLs
- Integration into Hermes Operator PRESALE mode

**Out of scope (paid tier / future):**
- Deep dive per competitor (paid product)
- SEMrush/Ahrefs integration (premium SEO)
- YouTube analysis
- Video content transcription
- Historical social media trend analysis

---

*Design approved 2026-05-26 via brainstorming with Миша.*
