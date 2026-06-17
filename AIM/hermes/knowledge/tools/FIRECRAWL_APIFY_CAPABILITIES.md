# FireCrawl + Apify — полные возможности API

Источники: Context7 (firecrawl/firecrawl-docs + apify/api-v2), июнь 2026.

---

## FireCrawl API

Базовый URL: `https://api.firecrawl.dev`
Аутентификация: `Authorization: Bearer <API_KEY>`
У меня: 11 ключей в ротационном банке (`/opt/data/firecrawl_keys.json`)

### 1. Scrape — извлечение контента с одной страницы

```
POST /v1/scrape
Body: {
  "url": "https://clinic.ru/doctors",
  "formats": ["markdown", "html", "screenshot", "links", "json"],
  "onlyMainContent": true,
  "waitFor": 5000,
  "mobile": false,
  "removeBase64Images": true,
  "blockAds": true
}
```

**Форматы вывода:**
- `markdown` — чистый markdown (основной для анализа)
- `html` — очищенный HTML
- `rawHtml` — сырой HTML
- `screenshot` — скриншот страницы
- `links` — все ссылки на странице
- `json` — структурированные данные по schema/prompt
- `summary` — AI-саммари страницы
- `branding` — цвета, шрифты, UI-компоненты

**JSON-извлечение (structured data):**
```json
{
  "url": "https://clinic.ru/doctors",
  "formats": ["json"],
  "jsonOptions": {
    "prompt": "Извлеки всех врачей: имя, специализация, опыт, образование",
    "schema": {
      "type": "object",
      "properties": {
        "doctors": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": {"type": "string"},
              "specialty": {"type": "string"},
              "experience_years": {"type": "number"},
              "education": {"type": "string"}
            }
          }
        }
      }
    }
  }
}
```

**Действия (actions):** `wait`, `click`, `write`, `press`, `scroll`, `screenshot`, `executeJavascript`
- Полезно для интерактивных страниц (кнопки «Показать ещё», вкладки, модальные окна)

**Когда использовать:**
- Извлечение списка врачей со страницы /specialisty
- Получение цен со страниц услуг
- Парсинг отзывов с конкретных страниц
- Любая конкретная страница где нужен полный контент

### 2. Search — веб-поиск + полный контент страниц

```
POST /v2/search
Body: {
  "query": "стоматология Москва рейтинг клиник",
  "limit": 5,
  "scrapeOptions": {
    "formats": ["markdown", "links"],
    "onlyMainContent": true
  }
}
```

**Параметры:**
- `query` — поисковый запрос
- `limit` — макс. результатов
- `tbs` — временной фильтр (`qdr:d` — день, `qdr:w` — неделя, `qdr:m` — месяц)
- `scrapeOptions` — с полным контентом каждой страницы в результате

**В ответе КАЖДЫЙ результат содержит ПОЛНЫЙ markdown страницы.** Это главное отличие от web_search.

**Когда использовать:**
- Поиск конкурентов в городе/нише
- Поиск отзывов о клинике на внешних площадках
- Поиск публикаций врача (elibrary, dissercat)
- Любой поиск где нужен ПОЛНЫЙ текст найденных страниц

### 3. Crawl — обход всего сайта

```
POST /v1/crawl
Body: {
  "url": "https://clinic.ru",
  "limit": 50,
  "scrapeOptions": {
    "formats": ["markdown"],
    "onlyMainContent": true
  }
}
```

**Параметры:**
- `url` — начальная страница
- `limit` — макс. страниц (по умолчанию безлимитно)
- `maxDiscoveryDepth` — глубина обхода
- `includePaths` / `excludePaths` — фильтрация URL

**Когда использовать:**
- Полный сбор контента со всего сайта клиники
- Извлечение ВСЕХ страниц услуг, врачей, цен
- Когда bitrix_scrape не нужен (обычный сайт без JavaScript)

### 4. Map — список всех URL сайта

```
POST /v1/map
Body: {
  "url": "https://clinic.ru"
}
```

**Возвращает:** массив URL — все страницы сайта. Быстро, без скачивания контента.

**Когда использовать:**
- «Что вообще есть на этом сайте?»
- Перед crawl — понять объём
- Проверить структуру сайта клиента

### 5. Extract — структурированные данные с нескольких URL

```
POST /v1/extract
Body: {
  "urls": ["https://clinic1.ru", "https://clinic2.ru"],
  "prompt": "Извлеки специализацию, цены, врачей",
  "schema": { ... }
}
```

**Когда использовать:**
- Сравнение нескольких клиник по одним параметрам
- Пакетное извлечение цен с нескольких сайтов

### Важные опции для медицинских сайтов

- `waitFor: 5000` — если сайт грузит контент через JavaScript
- `mobile: false` — десктоп (основной режим)
- `onlyMainContent: true` — без меню/футера
- `blockAds: true` — блокировка рекламы
- `location.country: "RU"` + `location.languages: ["ru"]` — гео-таргетинг для РФ
- `removeBase64Images: true` — без картинок в base64 (меньше токенов)

### Ротация ключей

У меня 11 ключей. При 402-ошибке система АВТОМАТИЧЕСКИ переключается на следующий ключ (до 3 попыток за вызов). Если все три попытки провалились — НЕ сдавайся, повтори вызов инструмента снова (бэкенд возьмёт следующие ключи).

---

## Apify API

Базовый URL: `https://api.apify.com/v2`
Аутентификация: `Authorization: Bearer <APIFY_TOKEN>`
У меня: 10 токенов в ротационном пуле (`/opt/data/apify_keys.json`)

### Основные эндпоинты

#### Запуск Actor (асинхронный)
```
POST /v2/actors/{actor_id}/runs
Body: { "input_field": "value" }
→ { "data": { "id": "run_id", "defaultDatasetId": "dataset_id" } }
```

#### Запуск Actor + получить результат (синхронный, до 300 сек)
```
POST /v2/actors/{actor_id}/run-sync-get-dataset-items?format=json
Body: { ... input ... }
→ [ { dataset items } ]
```

#### Получить результат выполнения
```
GET /v2/actor-runs/{run_id}/dataset/items?limit=100&clean=true
→ { "items": [...], "total": N, "offset": 0, "limit": 100 }
```

#### Получить статус выполнения
```
GET /v2/acts/{run_id}
→ { "data": { "status": "RUNNING"|"SUCCEEDED"|"FAILED", ... } }
```

### Поиск Actors в Store

```
GET /v2/store?search=google+maps&category=Web+Scraping&limit=10
```

**Категории:** "Web Scraping", "AI", "SEO", "Marketing", "Social Media"

**Параметры:**
- `search` — поиск по названию, описанию, readme
- `category` — фильтр по категории
- `pricingModel` — `FREE`, `FLAT_PRICE_PER_MONTH`, `PRICE_PER_DATASET_ITEM`
- `sortBy` — `popularity`, `newest`, `relevance`
- `allowsAgenticUsers: true` — только акторы, доступные AI-агентам

### Ключевые Actors для AIM (медицинский маркетинг)

| Actor | ID | Что делает |
|-------|----|-----------|
| Google Maps Scraper | `compass/google-maps-scraper` | Поиск компаний на Google Картах: названия, адреса, телефоны, рейтинги, сайты |
| Google Maps Extractor | `lukaskrivka/google-maps-extractor` | Извлечение детальной информации с Google Maps |
| Web Scraper | `apify/web-scraper` | Универсальный скрапер страниц (Playwright) |
| SEO Audit | Various | SEO-анализ сайтов |
| Social Media Scrapers | Various | Instagram, VK, Telegram |

**Google Maps Scraper — основной инструмент find_competitors:**
```
POST /v2/actors/compass/google-maps-scraper/runs
{
  "searchStrings": ["стоматология"],
  "location": "Москва",
  "maxCsvResults": 20,
  "language": "ru"
}
```

### Форматы вывода данных

- `json` — JSON (по умолчанию)
- `csv` — CSV
- `xml` — XML
- `xlsx` — Excel
- `html` — HTML таблица
- `clean: true` — плоская структура без вложенностей (удобно для LLM)

### Ротация токенов

10 токенов в `ApifyKeyPool`. Round-robin, авто-восстановление через 31 день. При exhausted — автоматически берётся следующий.

### Важные моменты

- У Actor может быть `notice` — предупреждение (например: «требует прокси»)
- `isRunnableAnonymously: false` — Actor требует авторизации
- Проверяй `allowsAgenticUsers: true` для автоматического запуска
- Синхронный запуск (`run-sync-get-dataset-items`) — макс 300 секунд. Для долгих запросов используй асинхронный запуск + polling.
- `pricingModel: PRICE_PER_DATASET_ITEM` — плата за каждый результат. Учитывай бюджет.
