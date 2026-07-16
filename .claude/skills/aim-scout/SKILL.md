---
name: aim-scout
version: 2.0.0
description: >
  Глубокая конкурентная разведка: 16 фаз сбора данных перед LLM-анализом.
  Зеркальное отражение client-onboarding-pipeline, но для конкурентов.
  Триггер: «/aim-scout {name}», «разведай {name}», «competitor scout».
---

# Competitor Scout — 16 фаз разведки конкурента

## Зеркало Hermes-онбординга

Hermes делает 16 фаз для КЛИЕНТА на сервере. Ты делаешь 16 фаз для КОНКУРЕНТА
локально, через терминал. Результат → `/aim-intel` → сервер.

**Целевое время: 50-65 минут.** Фазы нельзя пропускать.

## Навигация

| Фаза | Название | Аналог в Hermes |
|------|----------|-----------------|
| 0 | PRE-FLIGHT | Phase 0: PRE-FLIGHT |
| 0.5 | INSTAGRAM PROFILE | Phase 0.5: Deep Research |
| 0.75 | INSTAGRAM CONTENT | Phase 0.75: Audience Analysis |
| 0.8 | ADS INTELLIGENCE 🆕 | Phase 0.8: Ad Strategy |
| 1 | TECH AUDIT: SPEED | Phase 1: Tech Audit |
| 2 | TECH AUDIT: SEO, STACK & OSINT | Phase 1: Tech Audit (продолжение) |
| 3 | SOCIAL: CROSS-PLATFORM | Phase 2: Social Verifier |
| 3.2 | TELEGRAM CHANNELS 🆕 | Phase 3.2: Telegram Intel |
| 3.5 | KEY PERSONS: DOCTORS | Phase 3.5: Key Persons |
| 3.6 | SMI MENTIONS | Phase 3.6: SMI Placement Map |
| 4 | COMPETITOR MATRIX | Phase 4: Competitors |
| 5 | RATINGS & REVIEWS | Phase 5: Forum Pains + Reviews |
| 6 | FINANCIAL: FNS + | Phase 6: Finance |
| 7 | GAPS, ADVANTAGES & TACTICS | Phase 7: Content Plan (адаптировано) |
| 8 | DATA ASSEMBLY | Phase 8: HTML Build (адаптировано) |
| 9 | VALIDATION | Phase 9: QC Critique |
| 10 | LLM HANDOFF | Phase 10: Presentation |

---

## Железные правила

0. **RESULT GATE** — 2 цикла проверки перед handoff. Каждый `[ ]` → `[x]`.
1. **FULL DEPTH** — каждая фаза = реальный запуск инструментов, не «быстрый поиск».
2. **PARALLEL** — фазы без зависимостей запускай параллельно (1+2, 3.2+3.5+3.6, 5+6, 0.5+0.8).
3. **НЕ додумывай** — если инструмент не дал данных → `null`, не придумывай.
4. **TOOL FALLBACK** — Apify-ключ 402/429 → следующий. Firecrawl 402 → web_search.
5. **Instagram handle всегда без @**
6. **Apify actor:** `apify~instagram-profile-scraper` (НЕ `apify~instagram-scraper`)
7. **Ключи:** `AIM/data/apify_keys.json` — round-robin, метить exhausted
8. **НЕ дублируй** `/aim-intel`. Scout = сбор, Intel = загрузка.
9. **Execution Log** — каждая фаза: `[ ]` → `[x]` перед переходом дальше.
10. **DIFF MODE** 🆕 — если `/aim-scout --diff {name}` → сравнивай с предыдущим data.json

---

## Форматы вывода 🆕

Помимо JSON для сервера, создавай человекочитаемые отчёты:

```
/tmp/{slug}-scout-brief.json        # JSON для сервера (основной)
/tmp/{slug}-scout-report.md         # Markdown-отчёт (для человека)
/tmp/{slug}-scout-report.csv        # CSV-таблицы (для Excel/Sheets)
/tmp/{slug}-scout-metadata.json     # Метаданные сканирования
/tmp/{slug}-scout-diff.md           # Diff-отчёт (если --diff)
/tmp/{slug}-comparison-matrix.md    # Сравнительная матрица (если 2+ целей)
```

### metadata.json 🆕

```json
{
  "target": "{name}",
  "slug": "{slug}",
  "scan_date": "2026-06-09T12:00:00Z",
  "phases_completed": [0, 0.5, 0.75, 0.8, 1, 2, 3, 3.2, 3.5, 3.6, 4, 5, 6, 7, 8, 9, 10],
  "flags": { "diff": false, "deep": true },
  "previous_scan": null
}
```

---

## Фаза 0: PRE-FLIGHT

**Execution Log:**
- [ ] Приняты вводные (name, slug, instagram, website, client, city)
- [ ] Проверен сервер (есть ли уже data.json)
- [ ] Проверен флаг --diff (если да — загружен предыдущий data.json)
- [ ] Apify-ключи проверены (минимум 1 активный)
- [ ] Доступность внешних инструментов проверена (sherlock, maigret, web-check)

### Прими вводные

```
/aim-scout {name} {instagram} {website?}
```

- `name` — название клиники
- `slug` — короткий id (придумай если не указан)
- `instagram` — handle БЕЗ @
- `website` — URL (если нет — добудь из Instagram)
- `client` — slug клиента (спроси если не указан)
- `city` — по умолчанию Санкт-Петербург

### Флаги 🆕

```
/aim-scout --diff {name}          # Diff-режим: сравнить с прошлым сканированием
/aim-scout --deep {name}          # Полный пайплайн (по умолчанию)
/aim-scout --phases 1,2,4 {name}  # Только указанные фазы
```

### Проверь сервер

```bash
ssh aim "cat /opt/hermes-data/AIM/{client}/competitors/{slug}/data.json 2>/dev/null" || echo "NOT_FOUND"
```

Если `NOT_FOUND` — продолжаем. Если есть — покажи, спроси про обновление.

Если `--diff` — загрузи предыдущий data.json в `/tmp/{slug}-scout-previous.json` для сравнения.

### Проверь Apify-ключи

```bash
python3 -c "
import json
with open('AIM/data/apify_keys.json') as f:
    keys = json.load(f)['keys']
active = [k for k in keys if k['status'] == 'active']
print(f'Active: {len(active)}/{len(keys)}')
"
```

Если 0 активных — скажи пользователю, стоп.

### Проверь внешние инструменты 🆕

```bash
which sherlock && echo "sherlock: OK" || echo "sherlock: NOT FOUND (pip install sherlock-project)"
which maigret && echo "maigret: OK" || echo "maigret: NOT FOUND (pip install maigret)"
docker ps -a 2>/dev/null | grep web-check && echo "web-check: OK" || echo "web-check: NOT RUNNING (docker run -d -p 3001:3000 lissy93/web-check)"
```

---

## Фаза 0.5: INSTAGRAM PROFILE

**Execution Log:**
- [ ] Apify Profile Scraper запущен и завершён (SUCCEEDED)
- [ ] Извлечены: followers, posts, bio, externalUrl, category
- [ ] Найдены linked accounts в bio
- [ ] Обнаружен CEO/основатель

### Запусти Apify

```bash
curl -s -X POST "https://api.apify.com/v2/acts/apify~instagram-profile-scraper/runs?token={API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"usernames": ["{handle}"], "maxPosts": 24}'
```

Фейловер по ключам если 402/429. Полли до SUCCEEDED (30-90 сек).

### Извлеки

Из dataset собери:
- `username`, `fullName`, `biography`, `followersCount`, `postsCount`, `followsCount`
- `isBusinessAccount`, `businessCategoryName`, `verified`
- `externalUrls[]` — все ссылки из шапки (taplink, podcast, VK, сайт)
- `latestPosts[]` — 24 поста (будут использованы в Фазе 0.75)
- **Linked accounts:** из bio найди другие @аккаунты (косметология, CEO, партнёры)
- **CEO/основатель:** отдельно выдели личный аккаунт руководителя

---

## Фаза 0.75: INSTAGRAM CONTENT

**Execution Log:**
- [ ] Подсчитан ER (avg likes / followers * 100)
- [ ] Определён доминирующий формат (Video/Sidecar/Image) с % breakdown
- [ ] Выделены 3-5 тем контента (из caption'ов 24 постов)
- [ ] Найден топ-3 и худший пост
- [ ] Определён формат контента (шоу/интрига/авторская/школа/до-после)
- [ ] Вычислен gap в контенте

### Метрики (из 24 постов)

```python
posts = profile['latestPosts']
likes = [p.get('likesCount', 0) for p in posts]
comments = [p.get('commentsCount', 0) for p in posts]
views = [p.get('videoViewCount', 0) for p in posts]

er = (sum(likes) / len(likes)) / followers * 100
avg_likes = sum(likes) / len(likes)
avg_comments = sum(comments) / len(comments)
avg_views = sum(views) / len(views)

# Типы постов
types = {}
for p in posts:
    t = p.get('type', 'Unknown')
    types[t] = types.get(t, 0) + 1

# Частота
from datetime import datetime
dates = [datetime.fromisoformat(p['timestamp'].replace('Z', '+00:00')) for p in posts if p.get('timestamp')]
dates.sort(reverse=True)
intervals = [(dates[i] - dates[i+1]).days for i in range(len(dates)-1)]
avg_interval = sum(intervals) / len(intervals) if intervals else 0
```

### Темы контента

Сгруппируй caption'ы 24 постов в 3-5 смысловых тем. Примеры тем:
- До/после операций
- Закулисье / процесс
- Экспертный контент (советы врачей)
- Социальные доказательства (бизнес-клубы, мероприятия)
- Знакомство с врачами

### Формат

Определи доминирующий формат из:
- **шоу** — развлекательный, тренды, челленджи
- **интрига** — кликбейт, вопросы, загадки
- **авторская** — харизма конкретного врача
- **школа** — образовательный, инструкции
- **до/после** — результаты процедур

### Топ и провалы

- Топ-3 поста: caption + likes + views + url
- Худший пост: что не зашло аудитории и почему
- **Gap:** чего НЕ хватает в контенте (например: нет Reels, нет врачей в кадре, нет образовательного контента)

---

## Фаза 0.8: ADS INTELLIGENCE 🆕

**Execution Log:**
- [ ] Facebook Ad Library: поиск активной рекламы конкурента
- [ ] Извлечены: количество активных объявлений, платформы (FB/IG/Messenger)
- [ ] Определены основные рекламные месседжи и креативы
- [ ] Выделены CTA-паттерны (что используют для конверсии)
- [ ] LinkedIn Ads проверены (если B2B-сегмент)
- [ ] Telegram Ads проверены (если РФ-рынок)

### Facebook Ad Library

Используй Firecrawl для скрапинга Facebook Ad Library (публичный доступ):

```json
{
  "url": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=RU&q={clinic_name}",
  "waitFor": 8000,
  "formats": ["markdown"]
}
```

Альтернативно — MCP-сервер `facebook-ads-library-mcp` (если установлен):

```bash
# Поиск рекламы конкурента
mcp__facebook_ads__search_facebook_ads --query "{clinic_name}" --country RU

# Анализ рекламных креативов
mcp__facebook_ads__analyze_ad_creative_elements --brand "{clinic_name}"
```

### Извлеки из рекламы

- **Количество активных объявлений** — интенсивность рекламной кампании
- **Платформы:** Facebook / Instagram / Messenger / Audience Network
- **Форматы:** изображение / видео / карусель / коллекция
- **Месседжи:** какие проблемы подсвечивают, какие УТП
- **CTA:** «Записаться», «Узнать цену», «Получить консультацию», «Скачать прайс»
- **Лендинги:** куда ведут ссылки из объявлений (отдельные страницы? quiz? прайс?)
- **Частота обновления:** как часто меняют креативы (если есть история)

### LinkedIn Ads 🆕

```json
{
  "url": "https://www.linkedin.com/ad-library/search?query={clinic_name}",
  "waitFor": 5000,
  "formats": ["markdown"]
}
```

### Telegram Ads 🆕

Проверь через Telegram Ads API (если есть доступ) или поиском:
```
site:t.me "{название}" реклама
```

### Ad Intelligence Summary

Собери в структуру:
```json
{
  "ads_intel": {
    "facebook": {
      "active_ads_count": 12,
      "platforms": ["facebook", "instagram"],
      "formats": {"video": 7, "image": 5},
      "top_messages": ["Безоперационная ринопластика за 30 минут", "Рассрочка 0% на 12 месяцев"],
      "cta_patterns": ["Записаться на консультацию", "Узнать свою цену"],
      "landing_pages": ["/rhinoplasty", "/promo-june"],
      "estimated_budget": "medium"
    },
    "linkedin": null,
    "telegram": {
      "active_ads_count": 3,
      "channels": ["@spb_beauty", "@spb_medicine"]
    }
  }
}
```

---

## Фаза 1: TECH AUDIT — SPEED

**Execution Log:**
- [ ] PageSpeed API вызван (мобильный)
- [ ] Извлечены: Performance, Accessibility, Best Practices, SEO
- [ ] Core Web Vitals: LCP, FCP, TBT, CLS
- [ ] Статус CWV: Passed / Failed

### PageSpeed

```bash
# Если есть Google API ключ:
curl -s "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=https://{website}&strategy=mobile&key={GOOGLE_API_KEY}"

# Без ключа — Firecrawl скрапит pagespeed.web.dev:
```

Используй Firecrawl:
```json
{
  "url": "https://pagespeed.web.dev/report?url=https://{website}&form_factor=mobile",
  "waitFor": 10000,
  "formats": ["markdown"]
}
```

Извлеки:
- **Performance:** 0-100
- **Accessibility:** 0-100
- **Best Practices:** 0-100
- **SEO:** 0-100
- **LCP:** Largest Contentful Paint (сек)
- **FCP:** First Contentful Paint (сек)
- **TBT:** Total Blocking Time (мс)
- **CLS:** Cumulative Layout Shift
- **CWV Status:** Passed / Failed

---

## Фаза 2: TECH AUDIT — SEO, STACK & OSINT

**Execution Log:**
- [ ] Schema.org типы найдены (view-source)
- [ ] llms.txt проверен (основной + full)
- [ ] CMS определена
- [ ] Analytics определена (Метрика, GA4, Calltouch)
- [ ] Instagram-виджет на сайте: да/нет
- [ ] 🆕 DNS-записи получены (A, MX, NS, TXT, CNAME)
- [ ] 🆕 SSL-сертификат проверен (срок, CA)
- [ ] 🆕 WHOIS получен (регистратор, дата регистрации)
- [ ] 🆕 HTTP-заголовки безопасности проверены (CSP, HSTS, X-Frame-Options)
- [ ] 🆕 Трекеры и технологии найдены
- [ ] 🆕 SEO Content Gap: темы конкурентов, которых нет у клиента

### Schema.org

```bash
curl -s "https://{website}" | grep -oP 'itemtype="[^"]*"' | sort -u
```

Или Firecrawl raw HTML → grep по `application/ld+json` и `itemtype`.

Типы которые ищем: MedicalBusiness, LocalBusiness, Physician, MedicalOrganization, Organization, WebPage, Product, FAQ, BreadcrumbList

### llms.txt

```bash
curl -s -o /dev/null -w "%{http_code}" "https://{website}/llms.txt"
curl -s -o /dev/null -w "%{http_code}" "https://{website}/llms-full.txt"
```

Если 200 — прочитай содержимое (кратко).

### CMS & Analytics (из HTML)

```bash
curl -s "https://{website}" | grep -ioE 'bitrix|wordpress|wp-content|tilda|joomla|drupal|modx|umi|custom' | sort -u
curl -s "https://{website}" | grep -ioE 'metrika|gtag|ga4|calltouch|roistat|carrotquest|jivosite|livechat' | sort -u
```

### Instagram на сайте

Проверь есть ли виджет или ссылки на Instagram:
```bash
curl -s "https://{website}" | grep -ic 'instagram'
```

### OSINT: DNS, SSL, WHOIS, Headers 🆕

#### DNS-записи

```bash
dig ANY {domain} +short
dig A {domain} +short
dig MX {domain} +short
dig NS {domain} +short
dig TXT {domain} +short
```

Извлеки: IP-адрес(а), почтовый провайдер (Google Workspace / Yandex 360 / custom), NS-серверы, TXT-записи (SPF, DKIM, DMARC, верификация Яндекс/Google).

#### SSL-сертификат

```bash
echo | openssl s_client -servername {domain} -connect {domain}:443 2>/dev/null | openssl x509 -noout -dates -issuer -subject
```

Извлеки: Issuer (CA), срок действия (notBefore / notAfter), Subject (на какой домен), осталось дней.

#### WHOIS

```bash
whois {domain} | grep -iE 'registrar|creation|expir|registrant|country|org'
```

Извлеки: Registrar, Creation Date, Expiry Date, Registrant Organization (если не скрыт), Country.

#### HTTP Security Headers

```bash
curl -sI "https://{website}" | grep -iE 'strict-transport|csp|content-security|x-frame|x-content|x-xss|referrer-policy|permissions-policy'
```

Проверь наличие:
- `Strict-Transport-Security` (HSTS)
- `Content-Security-Policy` (CSP)
- `X-Frame-Options`
- `X-Content-Type-Options`
- `Referrer-Policy`
- `Permissions-Policy`

#### Трекеры и технологии

```bash
# Через web-check API (если запущен Docker):
curl -s "http://localhost:3001/api/check?url=https://{website}" | python3 -m json.tool

# Или grep по HTML:
curl -s "https://{website}" | grep -ioE 'gtag|fbq|pixel|vkshare|tiktok|analytics|counter|tracker' | sort -u
```

Классифицируй найденные трекеры:
- **Аналитика:** GA4, Яндекс.Метрика, LiveInternet
- **Рекламные:** Facebook Pixel, VK Pixel, TikTok Pixel, myTarget
- **CRM/Чаты:** Calltouch, Roistat, CarrotQuest, JivoSite
- **Тепловые карты:** Hotjar, CrazyEgg (если есть)

#### SEO Content Gap Analysis 🆕

Сравни контент конкурента с контентом клиента:

```bash
# Найди блог конкурента
curl -s "https://{website}/sitemap.xml" | grep -oP 'https://[^<]+' | head -50
```

```markdown
| Тема | Конкурент | Клиент | Gap |
|------|-----------|--------|-----|
| Ринопластика без операции | ✅ Статья + видео | ❌ | Критический |
| Лазерная эпиляция: FAQ | ✅ FAQ-раздел | ✅ Кратко | Частичный |
| Отзывы пациентов (видео) | ✅ YouTube плейлист | ❌ | Высокий |
| Цены на ботулотоксин | ✅ Прайс-страница | ✅ | Закрыт |
```

Выдели:
- **Critical gaps** — темы, которые покрывают 2+ конкурентов, а клиент — нет
- **Quick wins** — темы, которые можно закрыть за 1-2 дня
- **Content depth** — у кого более глубокий контент (лонгриды vs короткие посты)

---

## Фаза 3: SOCIAL — CROSS-PLATFORM

**Execution Log:**
- [ ] 🆕 Sherlock запущен для поиска аккаунтов по 400+ платформам
- [ ] Telegram найден/не найден
- [ ] VK найден/не найден
- [ ] YouTube найден/не найден
- [ ] Дзен найден/не найден
- [ ] 🆕 Одноклассники, Rutube, Likee проверены
- [ ] Для каждой платформы: подписчики, активность
- [ ] 🆕 Cross-contamination: проверены пересечения аудиторий

### Автоматический поиск: Sherlock 🆕

```bash
sherlock {clinic_name} --output /tmp/{slug}-sherlock.json --timeout 10
```

Sherlock проверит 400+ платформ автоматически. Из результатов извлеки:
- Все найденные аккаунты (платформа + username + url)
- Для каждого: существует / не существует

Если Sherlock не установлен:
```bash
pip install sherlock-project
```

### Ручной поиск по ключевым платформам (фейловер)

```bash
# 4 параллельных поиска:
"{название}" Telegram канал
"{название}" VK
"{название}" YouTube
"{название}" Дзен
```

### Дополнительные платформы (РФ) 🆕

```
"{название}" Одноклассники
"{название}" Rutube
"{название}" Likee
"{название}" Yappy
```

Для каждой найденной платформы:
- URL
- Подписчики (если доступно)
- Дата последнего поста
- Темы контента

### Cross-contamination 🆕

Проверь, подписан ли клиент на конкурента (из Фазы 0.5: followsCount + запроси у пользователя).

Дополнительно — проверь пересечения аудиторий:
```bash
# Если есть доступ к Instagram API:
# Сравни подписчиков клиента и конкурента (пересечения)
```

---

## Фаза 3.2: TELEGRAM CHANNELS 🆕

**Execution Log:**
- [ ] Telegram-канал(ы) конкурента найдены
- [ ] Извлечены: подписчики, частота постов, средние просмотры
- [ ] Определён формат контента (новости/экспертиза/акции/закулисье)
- [ ] Найден CEO/основатель в Telegram (личный канал)
- [ ] Проанализированы обсуждения в профильных чатах

### Поиск каналов

```bash
# Поиск через Telegram MCP (если установлен):
mcp__telegram__search_contacts "{clinic_name}"

# Или через Firecrawl:
"{название}" site:t.me
```

### Анализ канала

Если найден канал — скрапь последние 20 постов:
- **Подписчики** (если公开но)
- **Средние просмотры** на пост
- **ER по просмотрам** (просмотры / подписчики * 100)
- **Частота:** постов в неделю
- **Формат:** новости / экспертные статьи / акции / закулисье / репосты
- **Тональность:** формальная / дружеская / экспертная
- **Вовлечение:** реакции, комментарии, репосты

### Связанные каналы

- CEO/основатель — личный канал
- Партнёрские каналы — кого репостят
- Профильные чаты — где обсуждают клинику

---

## Фаза 3.5: KEY PERSONS — DOCTORS

**Execution Log:**
- [ ] Сайт проскраплен (main page + /about + /doctors + /specialists)
- [ ] ВСЕ врачи извлечены: ФИО, специализация, должность, степень, стаж
- [ ] Instagram-хендлы врачей найдены (если указаны на сайте)
- [ ] 🆕 Maigret запущен для каждого star/core врача
- [ ] 🆕 Досье на врачей: соцсети, публикации, профессиональные профили
- [ ] Врачи классифицированы: star / core / team

### Скрап сайта

Сначала Map сайта чтобы найти страницы с врачами:
```json
{ "url": "https://{website}", "search": "врач" }
```

Затем скрапь найденные страницы:
```json
{ "url": "https://{website}/doctors", "formats": ["markdown"], "onlyMainContent": true }
```

Если SPA — добавь `waitFor: 5000`.

### Досье на врачей через Maigret 🆕

Для каждого врача уровня star и core запусти Maigret:

```bash
maigret "{full_name}" --all-sites --timeout 15 --json --output /tmp/{slug}-doctor-{id}-dossier.json
```

Если Maigret не установлен:
```bash
pip install maigret
```

Maigret проверит 3000+ сайтов и найдёт:
- **Соцсети:** Instagram, VK, Facebook, Twitter/X, LinkedIn
- **Профессиональные:** ProDoctorov, DocDoc, СберЗдоровье, DocFinder
- **Форумы:** woman.ru, health.mail.ru, babyblog.ru
- **Публикации:** eLibrary, CyberLeninka, PubMed (если врач публикуется)
- **Блоги:** Яндекс.Дзен, Telegram

### Классификация врачей

| Tier | Критерий |
|------|----------|
| **star** | Свой Instagram с >1000 подписчиков, медийная личность, CEO/основатель |
| **core** | Врач с уникальной специализацией, к.м.н./д.м.н., опыт >10 лет |
| **team** | Остальные врачи |

### Досье на врача (расширенное) 🆕

```json
{
  "full_name": "Иванова Мария Сергеевна",
  "tier": "star",
  "specialization": "Пластический хирург",
  "degree": "д.м.н.",
  "experience_years": 15,
  "social_profiles": {
    "instagram": "@dr_ivanova",
    "vk": "vk.com/dr_ivanova",
    "telegram": "@dr_ivanova_channel",
    "prodoctorov": "prodoctorov.ru/spb/vrach/12345/"
  },
  "publications_count": 23,
  "media_mentions": 7,
  "dossier_file": "/tmp/{slug}-doctor-ivanova-dossier.json"
}
```

---

## Фаза 3.6: SMI MENTIONS

**Execution Log:**
- [ ] Business: forbes.ru, rbc.ru, kommersant.ru
- [ ] Glossy: marieclaire.ru, vogue.ru
- [ ] Medical: vademec.ru
- [ ] Regional: fontanka.ru, dp.ru, sobaka.ru
- [ ] 🆕 Telegram-СМИ: Mash, Baza, 112, SHOT
- [ ] Все результаты с source, title, URL, date

### 4+1 категорий (Firecrawl search, параллельно)

```
a) Business:
  site:forbes.ru "{название}"
  site:rbc.ru "{название}"
  site:kommersant.ru "{название}"

b) Glossy:
  site:marieclaire.ru "{название}"
  site:vogue.ru "{название}"

c) Medical:
  site:vademec.ru "{название}"

d) Regional (СПб):
  site:fontanka.ru "{название}"
  site:dp.ru "{название}"
  site:sobaka.ru "{название}"

e) Telegram-СМИ 🆕:
  site:t.me "{название}" Mash
  site:t.me "{название}" Baza
  site:t.me "{название}" SHOT
```

---

## Фаза 4: COMPETITOR MATRIX (расширенная)

**Execution Log:**
- [ ] ProDoctorov: поиск конкурентов в том же районе
- [ ] 🆕 SWOT-анализ для КАЖДОГО конкурента (включая target)
- [ ] 🆕 Positioning Map построена (X: простота↔мощность, Y: бюджет↔премиум)
- [ ] 🆕 Feature Comparison Matrix заполнена
- [ ] 🆕 Pricing Comparison Matrix заполнена
- [ ] Определена позиция в матрице (лидер / претендент / нишевой / слабый)
- [ ] Ключевые цифры для сравнения с клиентом

### ProDoctorov discovery

Найди страницу конкурента на ProDoctorov → посмотри «Похожие клиники» или «В том же районе».

### SWOT-анализ каждого конкурента 🆕

Для КАЖДОГО найденного конкурента (включая target clinic):

```markdown
## SWOT: {Clinic Name}

### STRENGTHS (сильные стороны)
- [Конкретная сила с доказательством]
- [Конкретная сила с доказательством]

### WEAKNESSES (слабые стороны)
- [Конкретная слабость с доказательством]
- [Конкретная слабость с доказательством]

### OPPORTUNITIES (возможности для клиента)
- [Возможность на основе слабости конкурента]
- [Возможность на основе рыночного пробела]

### THREATS (угрозы — что конкурент делает лучше)
- [Угроза с потенциальным влиянием]
- [Угроза с потенциальным влиянием]
```

### Positioning Map 🆕

Построй позиционную карту:

```
POSITIONING MAP — {city} {specialization}
==========================================

                    ПРЕМИУМ
                       |
        {clinic_c}     |     {aspirational}
                       |
  ПРОСТОТА ────────────┼────────────── МОЩНОСТЬ
                       |
        {target}       |     {clinic_a}
                       |
                       |
                    БЮДЖЕТ
```

Оси:
- **X (горизонталь):** Простота (узкая специализация, мало услуг) ↔ Мощность (широкий спектр, многопрофильность)
- **Y (вертикаль):** Бюджет (доступные цены, эконом) ↔ Премиум (высокие цены, VIP-сервис)

### Feature Comparison Matrix 🆕

```markdown
| Категория | Фича | {Target} | {Comp A} | {Comp B} | {Comp C} |
|-----------|------|----------|----------|----------|----------|
| **Приём** | Очная консультация | ✅ | ✅ | ✅ | ✅ |
| | Онлайн-консультация | ✅ | ❌ | ✅ | ❌ |
| | Выезд на дом | ❌ | ✅ | ❌ | ❌ |
| **Хирургия** | Ринопластика | ✅ | ✅ | ❌ | ✅ |
| | Блефаропластика | ✅ | ✅ | ✅ | ❌ |
| | Липосакция | ✅ | ❌ | ✅ | ✅ |
| **Косметология** | Ботулотоксин | ✅ | ✅ | ✅ | ✅ |
| | Контурная пластика | ✅ | ✅ | ✅ | ✅ |
| | Лазерная эпиляция | ❌ | ✅ | ❌ | ✅ |
| **Диагностика** | УЗИ | ✅ | ✅ | ❌ | ✅ |
| | 3D-моделирование | ✅ | ❌ | ❌ | ❌ |
```

Используй: ✅ Full, ◐ Partial, ❌ No, 🆕 Beta.

Выдели:
- **Moats** (защитные рвы) — фичи, которые есть только у target
- **Gaps** (уязвимости) — фичи, которых нет у target, но есть у конкурентов
- **Betas** — фичи в стадии запуска (возможность опередить)

### Pricing Comparison Matrix 🆕

```markdown
| Услуга | {Target} | {Comp A} | {Comp B} | {Comp C} | Рынок (сред.) |
|--------|----------|----------|----------|----------|---------------|
| Первичная консультация | {price} | {price} | {price} | {price} | {avg} |
| Ринопластика | {price} | {price} | {price} | {price} | {avg} |
| Блефаропластика | {price} | {price} | {price} | {price} | {avg} |
| Ботулотоксин (1 ед.) | {price} | {price} | {price} | {price} | {avg} |
| Контурная пластика (1 мл) | {price} | {price} | {price} | {price} | {avg} |
```

**Pricing Strategy Assessment:**
- Цены выше/ниже/на уровне рынка?
- Прозрачность: цены на сайте или «по запросу»?
- Модель: фикс / за единицу / пакетная
- Есть ли рассрочка / кредит?
- Якорение цен (премиум-пакет для сравнения)?

### Вывод

**Позиция в матрице:** лидер рынка / претендент / нишевой игрок / слабый конкурент

---

## Фаза 5: RATINGS & REVIEWS

**Execution Log:**
- [ ] ProDoctorov: rating, count, positive_themes, negative_themes
- [ ] Яндекс.Карты: rating, count
- [ ] 2ГИС: rating, count
- [ ] 🆕 Google Maps: rating, count
- [ ] Форумные упоминания: woman.ru, irecommend.ru
- [ ] 🆕 Отзовик, IRecommend, Zoon
- [ ] Key quote найден

### ProDoctorov

Скрапь страницу клиники (Firecrawl):
```json
{ "url": "https://prodoctorov.ru/spb/{clinic_slug}/", "formats": ["markdown"] }
```

Извлеки:
- rating, review count
- positive_themes (3-5)
- negative_themes (3-5)
- key_quote (самый показательный отзыв, дословно)

### Яндекс.Карты

Используй Playwright browser для скрапинга (Яндекс.Карты требуют JS):
```bash
mcp__playwright__browser_navigate "https://yandex.ru/maps/org/{clinic_name}/"
mcp__playwright__browser_snapshot
```

### 2ГИС

Аналогично — Playwright или Firecrawl search.

### Google Maps 🆕

```bash
# Поиск через Firecrawl:
"{clinic_name}" site:maps.google.com OR site:google.com/maps

# Или Google Places API:
curl -s "https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={clinic_name}&inputtype=textquery&fields=rating,user_ratings_total,reviews&key={GOOGLE_API_KEY}"
```

### Отзовики (расширенный список) 🆕

```
site:otzovik.com "{название}"
site:irecommend.ru "{название}"
site:zoon.ru "{название}"
site:yell.ru "{название}"
site:spr.ru "{название}"
```

### Форумы

Firecrawl search:
```
site:woman.ru "{название}"
site:irecommend.ru "{название}"
```

---

## Фаза 6: FINANCIAL — FNS + 🆕

**Execution Log:**
- [ ] ИНН найден (из футера сайта или поиска)
- [ ] Выписка ФНС получена (если ИНН найден)
- [ ] Выручка, прибыль, сотрудники, ОКВЭД извлечены
- [ ] 🆕 HeadHunter: количество открытых вакансий
- [ ] 🆕 Госзакупки: участие в тендерах (zakupki.gov.ru)
- [ ] 🆕 Арбитражные дела: судебные споры (kad.arbitr.ru)

### Шаг 1: Найди ИНН

Приоритет:
1. Футер сайта (Фаза 3.5)
2. web_search: `«{название}» ИНН`
3. ProDoctorov — в карточке клиники часто есть юрлицо

### Шаг 2: Выписка ФНС

```bash
# POST — получить токен
TOKEN=$(curl -s -X POST "https://egrul.nalog.ru/" \
  -d "query={ИНН}&page=1&pageSize=1" \
  -H "Content-Type: application/x-www-form-urlencoded" | python3 -c "import sys,json; print(json.load(sys.stdin)['t'])")

# GET — получить JSON
sleep 3
curl -s "https://egrul.nalog.ru/search-result/$TOKEN" | python3 -m json.tool
```

Извлеки:
- `НаимЮЛ` — название юрлица
- `Выручка`, `Прибыль`, `Сотрудники` (если есть в выписке)
- `ОКВЭД` — основной вид деятельности
- `Статус` — действующее / ликвидировано

### Шаг 3: HeadHunter — мониторинг найма 🆕

```bash
# Поиск вакансий по названию компании
curl -s "https://api.hh.ru/vacancies?employer_id={hh_id}&per_page=50" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Открытых вакансий: {data[\"found\"]}')
for v in data['items']:
    print(f'  - {v[\"name\"]} ({v.get(\"area\", {}).get(\"name\", \"?\")})')
"
```

Если HH.ru ID неизвестен — найди через поиск:
```bash
curl -s "https://api.hh.ru/employers?text={clinic_name}&area=2" | python3 -m json.tool
```

Извлеки:
- Количество открытых вакансий (индикатор роста/сжатия)
- Какие специалисты нужны (врачи каких специализаций, администраторы, маркетологи)
- Зарплатные вилки (если указаны)

### Шаг 4: Госзакупки 🆕

```bash
# Поиск tenders по ИНН
curl -s "https://zakupki.gov.ru/epz/order/extendedsearch/results.html?searchString={ИНН}" 2>/dev/null
```

Или Firecrawl:
```
site:zakupki.gov.ru "{ИНН}" OR "{юрлицо}"
```

Извлеки:
- Количество тендеров
- Суммы контрактов
- Типы закупок (медикаменты, оборудование, ремонт)

### Шаг 5: Арбитражные дела 🆕

```bash
# Поиск по ИНН
curl -s "https://kad.arbitr.ru/Kad/SearchInstances?query={ИНН}" 2>/dev/null
```

Или Firecrawl:
```
site:kad.arbitr.ru "{юрлицо}" OR "{ИНН}"
```

Извлеки:
- Количество дел (истец / ответчик)
- Категории споров (долги, договоры, трудовые)
- Суммы исков (если доступно)

---

## Фаза 7: GAPS, ADVANTAGES & TACTICS

**Execution Log:**
- [ ] 3+ gaps определены (что конкурент делает ХУЖЕ клиента)
- [ ] 3+ advantages определены (что конкурент делает ЛУЧШЕ клиента — честно)
- [ ] 2-3 wow_insights сформулированы
- [ ] 🆕 5-10 Steal-Worthy Tactics выделены
- [ ] 🆕 Messaging Differentiation Strategy сформулирована

### Gaps (уязвимости конкурента)

На основе ВСЕХ собранных данных:
- Где конкурент слабее клиента?
- Чего нет в контенте?
- Какие услуги отсутствуют?
- Где проседает качество (отзывы, speed, соцсети)?

### Advantages (честно)

- Где конкурент СИЛЬНЕЕ клиента?
- Чему стоит научиться?

### Wow Insights

2-3 ключевых наблюдения, которые повлияют на стратегию. Не «у них 40K подписчиков», а «у них CEO — лицо бренда с личным Instagram, что даёт +30% к engagement vs безликие аккаунты».

### Steal-Worthy Tactics 🆕

Конкретные тактики конкурентов, которые стоит скопировать или адаптировать:

```markdown
## STEAL-WORTHY TACTICS

### 1. [{Competitor}] — [{Tactic}]
**Описание:** [Что именно делают]
**Почему работает:** [Объяснение эффективности]
**Как внедрить:** [Конкретные шаги для клиента]
**Трудоёмкость:** Low / Medium / High
**Ожидаемый эффект:** Low / Medium / High

### 2. [{Competitor}] — [{Tactic}]
...
```

Фокусируйся на тактиках которые:
- **Доказанные** — работают у конкурента (есть метрики, отзывы)
- **Адаптируемые** — можно кастомизировать под клиента
- **Недоиспользуемые** — клиент такого ещё не делает

### Messaging Differentiation Strategy 🆕

На основе конкурентного анализа — рекомендованная стратегия дифференциации:

1. **Category:** Может ли клиент создать или захватить под-категорию?
   - Пример: «единственная клиника с 3D-моделированием результата ДО операции»
2. **Audience:** Может ли клиент владеть узким сегментом?
   - Пример: «фокус на мужскую пластическую хирургию»
3. **Tone:** Какой tone of voice выделит клиента на фоне конкурентов?
   - Пример: «научный подход vs эмоциональные обещания»

---

## Фаза 8: DATA ASSEMBLY

**Execution Log:**
- [ ] Pre-filled data.json создан
- [ ] 🆕 Markdown-отчёт создан: `/tmp/{slug}-scout-report.md`
- [ ] 🆕 CSV-таблицы созданы: `/tmp/{slug}-scout-report.csv`
- [ ] 🆕 metadata.json создан: `/tmp/{slug}-scout-metadata.json`
- [ ] 🆕 Comparison Matrix создана (если 2+ цели): `/tmp/{slug}-comparison-matrix.md`
- [ ] 🆕 Diff-отчёт создан (если --diff): `/tmp/{slug}-scout-diff.md`
- [ ] Все механически собранные поля заполнены
- [ ] null там где данных нет (не додумано)
- [ ] Файлы сохранены

### Создай pre-filled JSON

Возьми схему из `.claude/skills/aim-intel/data-schema.json`.
Заполни ВСЕ поля, которые собраны механически (Фазы 0-7).
Поля которые не собраны — `null`.

Сохрани:
```bash
# /tmp/{slug}-scout-brief.json
```

### Создай Markdown-отчёт 🆕

Структура отчёта:

```markdown
# Scout Report: {clinic_name}
**Дата сканирования:** {date}
**Фазы выполнены:** 0–10
**Целевое время:** {elapsed}

## Executive Summary
[3-5 ключевых находок, 1 абзац]

## Instagram
- Подписчики: {followers}
- ER: {er}%
- Формат: {format}
- Топ-3 поста: [кратко]

## Ads Intelligence 🆕
- Активных объявлений FB/IG: {count}
- Основной месседж: {message}

## Tech Audit
- Performance: {score}/100
- CWV: {status}
- CMS: {cms}
- OSINT: SSL до {date}, WHOIS: {registrar}

## Social Presence
| Платформа | Подписчики | Активность |
|-----------|-----------|------------|
| Instagram | {n} | {freq}/нед |
| Telegram | {n} | {freq}/нед |
| VK | {n} | {freq}/нед |
| YouTube | {n} | {freq}/нед |

## Key Persons
- Star: {name} ({specialization})
- Core: {count} врачей
- Team: {count} врачей

## Competitor Matrix
- Позиция: {position}
- SWOT: [кратко]

## Ratings
| Платформа | Рейтинг | Отзывов |
|-----------|---------|---------|
| ProDoctorov | {n} | {n} |
| Яндекс.Карты | {n} | {n} |
| 2ГИС | {n} | {n} |

## Financial
- ИНН: {inn}
- Выручка: {revenue}
- Сотрудники: {employees}
- Вакансий (HH): {n}

## Gaps & Advantages
- Gaps: [3+]
- Advantages: [3+]
- Wow Insights: [2-3]

## Steal-Worthy Tactics
[5-10 тактик]

## Полные файлы
- JSON: `/tmp/{slug}-scout-brief.json`
- CSV: `/tmp/{slug}-scout-report.csv`

```

### Создай CSV-таблицы 🆕

Выгрузи ключевые данные в CSV для Excel/Google Sheets:

```csv
category,metric,{target},{comp_a},{comp_b},{comp_c}
instagram,followers,{n},{n},{n},{n}
instagram,er,{n}%,{n}%,{n}%,{n}%
tech,performance,{n},{n},{n},{n}
tech,cms,{cms},{cms},{cms},{cms}
ratings,prodoctorov,{n},{n},{n},{n}
ratings,yandex_maps,{n},{n},{n},{n}
ratings,2gis,{n},{n},{n},{n}
pricing,consultation,{price},{price},{price},{price}
pricing,rhinoplasty,{price},{price},{price},{price}
...
```

### Comparison Matrix (если 2+ цели) 🆕

Если пользователь запросил разведку нескольких конкурентов одновременно — создай сравнительную матрицу:

```markdown
# Competitive Comparison Matrix

| Dimension | {Target A} | {Target B} | {Target C} | Возможность для клиента |
|-----------|-----------|-----------|-----------|------------------------|
| Core Product | ... | ... | ... | ... |
| Pricing | ... | ... | ... | ... |
| Tech Stack | ... | ... | ... | ... |
| Instagram ER | ... | ... | ... | ... |
| Team Size | ... | ... | ... | ... |
| Rating | ... | ... | ... | ... |
| Key Gap | ... | ... | ... | ... |
| Moat | ... | ... | ... | ... |
```

### Diff-режим 🆕

Если флаг `--diff` — сравни с предыдущим сканированием:

```markdown
# Recon Diff: {clinic_name}
**Предыдущее сканирование:** {date}
**Текущее сканирование:** {date}

## Обнаруженные изменения

### 🆕 Новое
- [Чего не было раньше]

### ✏️ Изменилось
- [Что было: X, стало: Y]

### ❌ Исчезло
- [Что было раньше, но пропало]

### ✅ Без изменений
- [Ключевые стабильные показатели]
```

Категории изменений:
| Категория | Что изменилось | Сигнал |
|-----------|---------------|--------|
| **Команда** | Новые врачи, уход ключевых | Рост / сжатие |
| **Контент** | Новые форматы, смена тона | Стратегический сдвиг |
| **Цены** | Повышение / понижение | Изменение позиционирования |
| **Реклама** | Новые кампании, смена креативов | Маркетинговая активность |
| **Услуги** | Новые направления, снятие старых | Диверсификация |
| **Соцсети** | Рост/падение подписчиков, новые платформы | Развитие присутствия |

---

## Фаза 9: VALIDATION

**Execution Log:**
- [ ] Цикл 1: все фазы 0-8 проверены, `[ ]` → `[x]`
- [ ] Цикл 2: повторная проверка после доделывания
- [ ] JSON валиден (python3 -m json.tool)
- [ ] Нет длинных тире (—)
- [ ] Нет слова «EGRUL»
- [ ] Все обязательные ключи верхнего уровня присутствуют
- [ ] 🆕 Новые ключи: ads_intel, osint, telegram_channels, steal_worthy_tactics, doctor_dossiers, hh_vacancies, arbitration
- [ ] 🆕 Markdown-отчёт создан и читабелен
- [ ] 🆕 CSV создан и валиден (открывается в Excel)
- [ ] 🆕 metadata.json создан
- [ ] 🆕 Diff-отчёт создан (если --diff)
- [ ] UTF-8

### 10 проверок (расширенный список)

1. **Execution Log:** все фазы 0-8: каждый `[ ]` → `[x]`
2. **JSON валидность:** `python3 -m json.tool /tmp/{slug}-scout-brief.json`
3. **Em-dash:** `grep '—' /tmp/{slug}-scout-brief.json` → пусто
4. **EGRUL:** `grep -i 'egrul' /tmp/{slug}-scout-brief.json` → пусто
5. **Обязательные ключи:** clinic, doctors, content_analysis, tech_audit, smi, gaps, wow_insights, ads_intel 🆕, osint 🆕, steal_worthy_tactics 🆕
6. **Кодировка:** `file /tmp/{slug}-scout-brief.json` → UTF-8
7. **Нет выдумок:** все значения либо из инструментов, либо null
8. **Markdown-отчёт 🆕:** `wc -l /tmp/{slug}-scout-report.md` → >50 строк
9. **CSV 🆕:** `python3 -c "import csv; list(csv.reader(open('/tmp/{slug}-scout-report.csv')))"` → без ошибок
10. **metadata.json 🆕:** `python3 -m json.tool /tmp/{slug}-scout-metadata.json` → валиден

Если проверка провалена — вернуться и исправить.

---

## Фаза 10: LLM HANDOFF

**Execution Log:**
- [ ] Структурированный бриф выдан пользователю
- [ ] LLM-промпт выдан (фокус на НЕсобранных данных)
- [ ] Pre-filled data.json передан
- [ ] 🆕 Markdown-отчёт передан
- [ ] 🆕 CSV передан
- [ ] 🆕 Diff-отчёт передан (если --diff)
- [ ] Next step объяснён: /aim-intel

### Выдай бриф

Сжатая сводка по всем 16 фазам (1 экран терминала).

### Выдай LLM-промпт 🆕 (обновлённый)

```
Ты — агент конкурентной разведки AIM. Я уже собрал механически ~75% данных
через Apify, Firecrawl, PageSpeed, web-check, Sherlock, Maigret, ФНС и HH.ru.
Вот pre-filled JSON: /tmp/{slug}-scout-brief.json
Вот Markdown-отчёт: /tmp/{slug}-scout-report.md

Твоя задача — дополнить пробелы (null-поля) и провести анализ:

1. Контент-анализ: определи ФОРМАТ (шоу/интрига/авторская/школа/до-после)
2. Ads Intelligence: проанализируй рекламные креативы — какие месседжи, CTA, форматы
3. Врачи: если сайт не отдал — найди через поиск. Дополни досье (Maigret)
4. Telegram: дополни анализ каналов — тональность, вовлечение, контент-стратегия
5. Отзывы: выдели positive/negative themes, key_quote
6. СМИ: дополни если нашёл новые упоминания
7. SWOT: дополни анализ по каждому конкуренту
8. GAPS: что конкурент делает ХУЖЕ клиента (5+)
9. STEAL-WORTHY TACTICS: дополни список тактик для копирования (до 10)
10. WOW_INSIGHTS: 2-3 ключевых инсайта
11. MESSAGING STRATEGY: рекомендация по дифференциации

Верни ПОЛНЫЙ data.json (схема в data-schema.json).
БЕЗ длинных тире (— → –). БЕЗ «EGRUL» (→ «выписка ФНС»).
Если данных нет — null или пустой массив.
```

### Next step

```
Next: скорми pre-filled JSON + промпт своей LLM → /aim-intel {client} {slug}
```

Файлы для передачи:
- `/tmp/{slug}-scout-brief.json` — JSON для сервера
- `/tmp/{slug}-scout-report.md` — Markdown-отчёт для чтения
- `/tmp/{slug}-scout-report.csv` — Таблицы для Excel
- `/tmp/{slug}-scout-metadata.json` — Метаданные сканирования
- `/tmp/{slug}-scout-diff.md` — Diff-отчёт (если --diff)
- `/tmp/{slug}-comparison-matrix.md` — Сравнительная матрица (если 2+ цели)
