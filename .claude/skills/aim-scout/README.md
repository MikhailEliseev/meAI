# AIM Scout — справочник

## Версия 2.0.0

## Инструменты

### Apify: Instagram Profile Scraper

**Actor:** `apify~instagram-profile-scraper`
**Документация:** https://apify.com/apify/instagram-profile-scraper

#### Параметры запуска

```json
{
  "usernames": ["handle_without_@"],
  "maxPosts": 24
}
```

#### Поля ответа (ключевые)

| Поле | Описание |
|------|----------|
| `followersCount` | Подписчики |
| `postsCount` | Всего постов |
| `biography` | Bio |
| `externalUrl` | Сайт из шапки |
| `isBusinessAccount` | Бизнес-аккаунт? |
| `businessCategoryName` | Категория |
| `latestPosts[N].likesCount` | Лайки поста |
| `latestPosts[N].commentsCount` | Комментарии |
| `latestPosts[N].caption` | Текст поста |
| `latestPosts[N].videoViewCount` | Просмотры (видео) |

#### Расчёт ER

```
ER = (среднее лайков на 24 постах) / followers * 100
```

#### Ключи Apify

Файл: `AIM/data/apify_keys.json` — 12 ключей, 8 активных.

При exhaust-ключе обновить:
```bash
python3 -c "
import json, datetime
with open('AIM/data/apify_keys.json') as f:
    data = json.load(f)
# Пометить ключ N как exhausted
data['keys'][N]['status'] = 'exhausted'
data['keys'][N]['exhausted_at'] = '$(date -u +%Y-%m-%dT%H:%M:%S+00:00)'
with open('AIM/data/apify_keys.json', 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
"
```

---

### Sherlock — поиск аккаунтов по 400+ платформам (v2.0)

**Установка:**
```bash
pip install sherlock-project
```

**Запуск:**
```bash
sherlock {username} --output /tmp/{slug}-sherlock.json --timeout 10
```

**Что находит:** соцсети (Instagram, VK, Facebook, Twitter/X, TikTok), форумы, GitHub, блоги, профессиональные сети.

**Документация:** https://github.com/sherlock-project/sherlock

---

### Maigret — досье на человека по 3000+ сайтам (v2.0)

**Установка:**
```bash
pip install maigret
```

**Запуск:**
```bash
maigret "{full_name}" --all-sites --timeout 15 --json --output /tmp/{slug}-dossier.json
```

**Что находит:** соцсети, профессиональные профили (ProDoctorov, DocDoc), форумы, публикации, блоги.

**Документация:** https://github.com/soxoj/maigret

---

### web-check — OSINT-анализ сайта (v2.0)

**Установка:**
```bash
docker run -d -p 3001:3000 lissy93/web-check
```

**API:**
```bash
curl -s "http://localhost:3001/api/check?url=https://{website}" | python3 -m json.tool
```

**Что проверяет:**
- DNS-записи (A, MX, NS, TXT, CNAME)
- SSL-сертификат (CA, срок действия)
- WHOIS (регистратор, дата регистрации)
- HTTP-заголовки безопасности (CSP, HSTS, X-Frame-Options)
- Трекеры и технологии (Wappalyzer)
- Сервер (nginx/apache), IP, хостинг
- Cookies, связанные домены, блокировка контента

**Документация:** https://github.com/lissy93/web-check

---

### Facebook Ads Library MCP (v2.0)

**Установка:**
```bash
git clone https://github.com/RamsesAguirre777/facebook-ads-library-mcp.git
cd facebook-ads-library-mcp
pip install -r requirements.txt
```

**Добавить в ~/.claude/settings.json:**
```json
{
  "mcpServers": {
    "facebook_ads": {
      "command": "python",
      "args": ["/path/to/facebook-ads-library-mcp/facebook_ads_mcp_complete.py"]
    }
  }
}
```

**Ключевые инструменты:**
- `search_facebook_ads()` — поиск всей рекламы бренда
- `competitive_ad_analysis()` — сравнение стратегий нескольких брендов
- `analyze_ad_creative_elements()` — AI-анализ креативов
- `generate_facebook_intelligence_report()` — полный отчёт

**Документация:** https://github.com/RamsesAguirre777/facebook-ads-library-mcp

---

### Telegram MCP (v2.0)

**Установка (один из):**
```bash
# Вариант 1: chigwell/telegram-mcp
git clone https://github.com/chigwell/telegram-mcp.git
cd telegram-mcp && pip install -r requirements.txt

# Вариант 2: sparfenyuk/mcp-telegram (MTProto)
git clone https://github.com/sparfenyuk/mcp-telegram.git
```

**Ключевые возможности:**
- Чтение чатов и каналов
- Поиск контактов
- Анализ постов: просмотры, реакции, репосты

**Документация:** https://github.com/chigwell/telegram-mcp

---

### HeadHunter API (v2.0)

**Бесплатный API, без ключа:**
```bash
# Поиск работодателя
curl -s "https://api.hh.ru/employers?text={clinic_name}&area=2"

# Поиск вакансий
curl -s "https://api.hh.ru/vacancies?employer_id={hh_id}&per_page=50"
```

**Документация:** https://github.com/hhru/api

---

### Госзакупки (v2.0)

**Поиск тендеров по ИНН:**
```
site:zakupki.gov.ru "{ИНН}" OR "{юрлицо}"
```

**Документация:** https://zakupki.gov.ru

---

### Арбитражные дела (v2.0)

**Поиск дел по ИНН:**
```
site:kad.arbitr.ru "{юрлицо}" OR "{ИНН}"
```

**Документация:** https://kad.arbitr.ru

---

### ФНС (egrul.nalog.ru)

**Получение выписки:**
```bash
TOKEN=$(curl -s -X POST "https://egrul.nalog.ru/" \
  -d "query={ИНН}&page=1&pageSize=1" \
  -H "Content-Type: application/x-www-form-urlencoded" | python3 -c "import sys,json; print(json.load(sys.stdin)['t'])")

sleep 3
curl -s "https://egrul.nalog.ru/search-result/$TOKEN" | python3 -m json.tool
```

---

## Форматы вывода (v2.0)

| Файл | Формат | Назначение |
|------|--------|------------|
| `{slug}-scout-brief.json` | JSON | Основной файл для сервера (`/aim-intel`) |
| `{slug}-scout-report.md` | Markdown | Человекочитаемый отчёт |
| `{slug}-scout-report.csv` | CSV | Таблицы для Excel/Google Sheets |
| `{slug}-scout-metadata.json` | JSON | Метаданные сканирования |
| `{slug}-scout-diff.md` | Markdown | Diff-отчёт (если --diff) |
| `{slug}-comparison-matrix.md` | Markdown | Сравнительная матрица (если 2+ цели) |

---

## Интеграция с aim-intel

```
/aim-scout {name} {instagram} {website}
    ↓
  Apify + Sherlock + Maigret + web-check + Facebook Ads + Telegram
    ↓
  Структурированный бриф + Markdown-отчёт + CSV + LLM-промпт
    ↓
  Пользователь кормит промпт своей LLM
    ↓
  LLM возвращает data.json
    ↓
/aim-intel {client} {slug}
    ↓
  data.json → сервер → competitor-mgr.py ✅
```

---

## Рефересные скиллы (для изучения)

| Скилл | Репозиторий | Звёзды | Ключевая фича |
|-------|------------|--------|---------------|
| **recon** | [g-baskin/recon](https://github.com/g-baskin/recon) | — | 5-фазный пайплайн: recon → tech → security → pre-launch → IP |
| **market-competitors** | [zubair-trabzada/ai-marketing-claude](https://github.com/zubair-trabzada/ai-marketing-claude) | 1843 | SWOT, Positioning Map, Feature Matrix, Pricing Matrix |
| **facebook-ads-mcp** | [RamsesAguirre777/facebook-ads-library-mcp](https://github.com/RamsesAguirre777/facebook-ads-library-mcp) | — | 15+ инструментов анализа рекламы конкурентов |
| **competitive-ads-extractor** | [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) | — | Извлечение рекламы из Facebook Ad Library + LinkedIn |
| **lead-research-assistant** | [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) | — | Поиск и квалификация лидов |
| **web-check** | [lissy93/web-check](https://github.com/lissy93/web-check) | 33357 | OSINT-комбайн: DNS, SSL, WHOIS, трекеры, технологии |
| **sherlock** | [sherlock-project/sherlock](https://github.com/sherlock-project/sherlock) | ~62k | Поиск аккаунтов по username в 400+ соцсетях |
| **maigret** | [soxoj/maigret](https://github.com/soxoj/maigret) | ~14k | Досье на человека по 3000+ сайтов |
| **telegram-mcp** | [chigwell/telegram-mcp](https://github.com/chigwell/telegram-mcp) | — | MCP-сервер Telegram |
| **unifapi-agents** | [unifapi-agent/agents](https://github.com/unifapi-agent/agents) | 486 | SEO, GEO, social listening, competitive intelligence |
