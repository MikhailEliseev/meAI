# 📋 ШПАРГАЛКА — Что сделано в сессии (июль 2026)

> Обновлено: 2026-07-29
> Ветка: `feat/competitor-v2-perplexity-searxng`
> Сервер: `aim` = `78.17.128.169`

---

## 🏗️ ПРОЕКТ: meAI_1 / iamaim.ru

**Что это:** AI-чат для анализа медицинских клиник. Пользователь шлёт URL сайта → hermes-v2 собирает данные (4 блока) → публикует красивый отчёт на iamaim.ru.

**Архитектура:**
```
iamaim.ru (WordPress) → nginx → hermes-v2 (FastAPI :8000)
                                    ├─ LLM: glm-5.2 через z.ai
                                    ├─ Tools: find_competitors, extract_clinic_profile,
                                    │         run_review_platforms, company_financials
                                    ├─ Data: Apify (отзывы), SearXNG (поиск), ФНС (выручка)
                                    └─ Output: HTML отчёт → MariaDB → iamaim.ru/{slug}
```

**Контейнеры на сервере:**
- `aim-hermes-v2` — главный бэкенд (Python 3.11, FastAPI)
- `aim-nginx` — роутинг
- `aim-wordpress` — сайт (WP)
- `aim-mysql` — MariaDB 11 (wp_posts с отчётами)
- `aim-searxng` — поисковая выдача

---

## ✅ ЗАВЕРШЁННЫЕ ФАЗЫ (Milestones 1-3)

### Milestone 1: Interactive Chat Redesign (Phases 1-8) ✅
Основной чат: walking skeleton, диалоговый сервер, тулы, кнопки, деплой.

### Milestone 2: v3 Feature Parity (Phases 9-10) ✅
HTML-отчёты с дизайн-системой + публикация в WordPress.

| Phase | Что | Tag |
|-------|-----|-----|
| **9** | HTML Builder — canonical CSS (Inter+Playfair, ripple, glass-cards, hero) | — |
| **10** | WordPress Publisher — `publish_report()` → MariaDB → URL | — |

**Полировка (5 раундов):**
- Минималистичная таблица (стиль чата, не громоздкая)
- Тема синхронизирована с сайтом (`html[data-theme=dark]`)
- GPU-оптимизация ripple (`transform: scale`, 0 layout-shift)
- Ripple уменьшен в 2 раза (15 колец вместо 30)
- Убрана медальность, убрана дубль-кнопка темы

**Tag:** `report-generator-v6-done`
**Smoke:** https://iamaim.ru/6hk3z8o3/

### Milestone 3: Chat Report Delivery (Phases 11-14) ✅

| Phase | Что | Tag | UAT |
|-------|-----|-----|-----|
| **11** | Chat Integration — автопубликация + SSE `report-ready` + карточка | `phase-11-review-fixed` | 8/8 ✅ |
| **12** | Report Download — кнопка «Скачать PDF» + WeasyPrint | `phase-12-done` | 7/7 ✅ |
| **13** | Data Quality — scraper врачей + промпт + отзывы (убрать [N] сноски) | `phase-13-done` | ✅ |
| **14** | Speed & Quality — 4 мин → 2.7 мин + SSRF защита + качество | `phase-14-done` | ✅ |

---

## 🔑 КЛЮЧЕВЫЕ ФАЙЛЫ

### Backend (hermes-v2)
```
app/
├── main.py              # FastAPI: /api/chat/stream + /report/{slug}/download
├── llm.py               # chat_with_tools() + _auto_publish_report()
├── session.py           # SQLite хранилище истории
├── tools/
│   ├── competitors.py   # find_competitors (SearXNG + ФНС)
│   ├── reviews.py       # run_review_platforms (Apify: Яндекс + 2ГИС)
│   └── ...
├── report_builder/
│   ├── builder.py       # build_report_html() — CSS + hero + ripple + секции
│   ├── css.py           # _CANONICAL_CSS (~700 строк дизайн-системы)
│   ├── adapter.py       # build_data_dict() — v2 collected_results → data
│   ├── revenue_block.py # Таблица «Выручка vs Конкуренты»
│   ├── publisher.py     # publish_report() + get_report_html_by_slug()
│   ├── pdf_converter.py # html_to_pdf() через WeasyPrint
│   ├── pdf_builder.py   # build_pdf_html() — table-based для WeasyPrint
│   └── markdown_engine.py # Markdown→HTML (STATS, tables, metric-tags)
└── formatters/
    ├── profile.py       # format_profile() — Markdown с ::: блоками
    ├── competitors.py   # format_competitors() — таблица ФНС
    └── overview.py      # format_overview()
```

### Frontend
```
AIM/theme/
├── chat-inline.php      # Чат: SSE парсинг, renderReportCard(), parseMarkdown()
├── chat-inline-golden.php  # (не используется)
└── chat-inline-pro.php     # (не используется)
```

### Infrastructure
```
AIM/deploy/nginx/iamaim.conf  # Роутинг: /api/ → hermes, /report/ → hermes
AIM/hermes-v2/Dockerfile      # WeasyPrint deps (libcairo2, libpango)
AIM/hermes-v2/requirements.txt
```

---

## 🔧 КАК ЭТО РАБОТАЕТ (E2E flow)

```
1. Пользователь пишет "arclinic.ru" в чат
2. hermes-v2 /api/chat/stream:
   a. extract_clinic_profile (Perplexity) → ИНН, адрес, врачи
   b. find_competitors (SearXNG + aim-app) → конкуренты + выручка ФНС
   c. company_financials (ФНС) → выручка клиента
   d. run_review_platforms (Apify) → Яндекс.Карты + 2ГИС рейтинги
3. LLM (glm-5.2) стримит анализ → text-delta events
4. _auto_publish_report():
   a. build_data_dict(collected_results, profile_cache, llm_text)
   b. build_report_html(data, title) → красивый HTML
   c. publish_report(html, title) → MariaDB INSERT → https://iamaim.ru/{slug}
5. SSE event "report-ready" → фронтенд показывает карточку
6. Пользователь кликает «Открыть отчёт» → iamaim.ru/{slug}
7. Или кликает «Скачать PDF» → /report/{slug}/download → WeasyPrint → PDF
```

---

## 📊 ТЕСТЫ

**144/145 PASS** (1 несвязанный fail в `test_llm.py::test_system_prompt_prepended` — старый assertion "Гермес" → "AI-ассистент AIM").

| Файл | Тестов | Что покрывает |
|------|--------|---------------|
| test_report_builder.py | 34 | CSS, builder, adapter, revenue block |
| test_phase11_chat_report.py | 17 | Автопубликация, SSE, гварды, frontend |
| test_phase12_pdf_download.py | 7 | PDF endpoint, headers, slug validation |
| test_reviews_apify.py | 16 | Apify отзывы (Яндекс + 2ГИС) |
| test_publisher.py | 12 | WordPress publish (мок MySQL) |
| test_pipeline_fixes.py | 12 | collected_results, auto-calls |
| Остальные | ~46 | Session, competitors, anti-hallucination, key pool |

---

## 🏷️ TAGS (backup points)

```
known-good-17jul-0104          # Бэкап до начала работы
report-generator-v6-done       # Phase 9-10 + полировка CSS
phase-11-done                  # Phase 11 базовая
phase-11-review-fixed          # Phase 11 + code review fixes (W-1/W-2/W-3/I-2)
phase-12-done                  # Phase 12 PDF download
phase-13-done                  # Phase 13 data quality
phase-14-done                  # Phase 14 speed optimization
pipeline-v5-working-e2e        # Pipeline v5 (работающий E2E)
pipeline-v6-quality-fixes      # Pipeline v6 (качество)
```

---

## 🔴 ИЗВЕСТНЫЕ ПРОБЛЕМЫ

1. **`test_llm.py::test_system_prompt_prepended`** — fail (старый assertion, не связан с работой)
2. **Сервер рассинхронизирован с git** — деплой через SCP, не git pull (см. `DEPLOY-VIA-SCP.md`)
3. **Telegram бот** — остался на v1 (v2 не имеет webhook-роутов)
4. **Скорость чата** — ~2.7 мин (улучшено с 4 мин в Phase 14)

---

## 🚀 КАК ДЕПЛОИТЬ

```bash
# 1. SCP файлов на сервер
scp AIM/hermes-v2/app/*.py aim:/opt/aim/AIM/hermes-v2/app/
scp AIM/theme/chat-inline.php aim:/opt/aim/AIM/theme/

# 2. Пересборка образа
ssh aim "cd /opt/aim/AIM && docker compose build hermes-v2"

# 3. Перезапуск (БЕЗ --force-recreate для всего, только hermes-v2)
ssh aim "cd /opt/aim/AIM && docker compose up -d --no-deps --force-recreate hermes-v2"

# 4. Обновить chat-inline.php в WordPress
ssh aim "docker cp /opt/aim/AIM/theme/chat-inline.php aim-wordpress:/var/www/html/wp-content/themes/aim-theme/chat-inline.php"

# 5. Проверка
ssh aim "docker exec aim-hermes-v2 curl -s http://localhost:8000/health"
```

**НЕ ДЕЛАТЬ:** `git pull` на сервере (рассинхронизирован).

---

## 📋 ЧТО ДАЛЬШЕ

- **Phase 13: QC Critique** — 18-пунктный чеклист качества (опционально)
- **Telegram bot** на v2 — нужен перенос webhook-роутов
- **Auth/sessions** — Bearer token, персистентные сессии
- **PDF caching** — LRU cache для популярных отчётов
- **Migrate pymysql → aiomysql** в `publish_report()`
```
