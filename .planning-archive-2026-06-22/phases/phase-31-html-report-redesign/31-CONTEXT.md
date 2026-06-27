# Phase 31: HTML Report Redesign — ИПХиК-level Quality

**Gathered:** 2026-06-16
**Status:** Ready for research

<domain>
## Phase Boundary

Переделать `generate_html_report.py` (924 строки, базовый стекломорфизм) так, чтобы генерируемые отчёты приближались по качеству к эталону `ИПХиК (1).html` (966 строк ручной вёрстки) — dual theme, ripple-анимации, 10+ глубоких секций, per-doctor анализ, custom дизайн под каждого клиента.

**Ключевое ограничение:** ИПХиК.html — ручная работа с конкретными данными. Наша система должна генерировать отчёты АВТОМАТИЧЕСКИ из prescan + CI данных. Не копируем структуру 1:1 — адаптируем под data-driven подход.

**Success Criteria:**
1. Dual theme (light/dark toggle) с CSS variables — переключение без перезагрузки
2. Ripple ring анимации на фоне (8-14 пульсирующих колец)
3. Fixed navigation bar с якорными ссылками на секции
4. 10+ секций, каждая с section-label и заголовком
5. Per-doctor анализ с соцсетями (если данные есть в prescan)
6. Content analysis секция (если есть данные)
7. Market comparison table с трендами выручки
8. Whitefields / gaps таблица сравнения
9. Strategy recommendations с шагами
10. CTA offer blocks
11. Inter font (вместо Jost) + Playfair Display
12. Graceful omission: секции без данных не рендерятся
13. WordPress публикация сохраняется (pymysql → wp_posts)
14. Обратная совместимость: существующие сессии генерируют отчёт без ошибок

</domain>

<decisions>
## Design Decisions

### D-01: Data-driven архитектура секций
Каждая секция — отдельный builder, который проверяет наличие данных перед рендерингом. Нет данных → секция отсутствует. Это сохраняет подход текущего generate_html_report.py, но с расширенным набором секций.

### D-02: Dual theme через CSS variables + data-theme атрибут
`:root` для светлой темы, `[data-theme="dark"]` для тёмной. Переключение через JavaScript (одна кнопка в nav). Цвета из ИПХиК.html:
- Light: `--bg: #ffffff`, `--surface: #F5F5F5`, `--text: #1A1A1A`, `--accent: #1A1A1A`
- Dark: `--bg: #0D0D0D`, `--surface: #1A1A1A`, `--text: #F0F0F0`, `--accent: #F0F0F0`

### D-03: Ripple rings — CSS-only анимации
14 position:fixed колец с `pulse-ring` анимацией. Не требуют JavaScript. `@media (max-width: 768px)` скрываются. Кольца — часть фона, не влияют на контент.

### D-04: Font stack — Inter вместо Jost
ИПХиК.html использует Inter (body) + Playfair Display (headings). Меняем Jost → Inter для лучшей читаемости и соответствия эталону.

### D-05: Секции строятся из реальных данных prescan + CI
Новые секции (experts, content analysis, media, whitefields, strategy) требуют новых полей в данных. Если данных нет — секция пропускается. Никаких хардкод-данных.

### D-06: Сохраняем прямую публикацию в WordPress
`_publish_to_wordpress()` остаётся без изменений. pymysql → wp_posts. Генерация HTML и публикация — раздельные шаги.

### D-07: Обратная совместимость
Старые сессии (без новых полей) должны генерировать отчёт без ошибок. Все новые секции проверяют наличие данных.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Существующий код
- `AIM/hermes/app/tools/generate_html_report.py` — Текущий генератор (924 строки): CSS, 10 build-функций, WordPress publisher
- `/Users/mikhaileliseev/Downloads/ИПХиК (1).html` — Эталон качества (966 строк): dual theme, ripple rings, 10 секций, per-doctor анализ
- `AIM/hermes/app/tools/finalize_research.py` — Вызывает generate_html_report (line 111)
- `AIM/hermes/app/tools/__init__.py` — Регистрация тулзы (line: `from . import generate_html_report`)

### Data Sources (prescan stages)
- `prescan-data.json` → stage_1_financials (revenue, profit, doctors, legal_name, inn)
- `prescan-data.json` → stage_2_under_the_hood (seo_score, seo_fails, rating, reviews, pagespeed)
- `prescan-data.json` → stage_3_market (revenue_trend, competitors nearby)
- `ci-analysis.json` → feature_matrix, gaps, advantages, steal_worthy_tactics, top_recommendation

### Design System Reference
- ИПХиК.html CSS variables (lines 12-43): `:root` + `[data-theme="dark"]`
- Ripple rings (lines 95-122): `.ripple-ring`, `.ring-pulse-*`, `@keyframes pulse-ring`
- Navigation (lines 63-78): fixed glass nav with logo, links, theme toggle
- Expert cards (lines 185-199): `.expert-category`, `.expert-item`
- Gap blocks (lines 215-220): `.gap` with colored left border

</canonical_refs>

<specifics>
## Specific Design Elements to Adopt

### 1. Dual Theme Toggle
```html
<button class="theme-toggle" onclick="document.documentElement.dataset.theme=document.documentElement.dataset.theme==='dark'?'light':'dark'">🌓</button>
```
Тема сохраняется в localStorage: `localStorage.getItem('aim-theme')`. При загрузке страницы — проверка localStorage.

### 2. Navigation Bar
Fixed position, glassmorphism (`backdrop-filter: blur(16px)`), logo + якорные ссылки на секции. Ссылки сворачиваются на mobile (`@media max-width: 768px`).

### 3. Section Structure
Каждая секция:
- `section-label` (нумерованный заголовок: "01 - О клинике")
- `h2` заголовок
- Контент (таблицы, карточки, метрики)
- `hr` разделитель между секциями

### 4. New Sections (data-dependent)
| # | Секция | Данные | Сейчас |
|---|--------|--------|--------|
| 01 | Hero | client_name, city, url, scan_date | ✅ Есть |
| 02 | About | legal_name, inn, okved, revenue, profit, trend, employees, licenses | 🔄 Расширить financials |
| 03 | Market | feature_matrix с revenue, trend, doctors, social | 🔄 Расширить competitors |
| 04 | Experts | doctors[] с name, title, instagram, followers, avg_likes, content_style | ✨ Новая |
| 05 | Content Analysis | per-doctor content breakdown, patient fears | ✨ Новая |
| 06 | Media | media_mentions[] (Forbes, RBC, Vademecum) | ✨ Новая |
| 07 | Competitors | per-competitor detailed cards | 🔄 Расширить |
| 08 | Whitefields | gaps comparison table (Telegram, Schema, GEO, etc.) | 🔄 Из CI gaps |
| 09 | Digital Presence | platforms status table (9 platforms) | ✨ Новая |
| 10 | Strategy | 5 strategic directions with steps | 🔄 Из recommendations |
| 11 | Offer/CTA | 8 service blocks + CTA box | 🔄 Из recommendations |

### 5. Ripple Rings Implementation
14 абсолютно позиционированных колец с классом `.ripple-ring`. 6 статичных (`.ring-lg-1..6`), 8 анимированных (`.ring-pulse-1..8`). Все внутри `<div class="ripple">` с `position: fixed; pointer-events: none`.

</specifics>

<deferred>
## Deferred Ideas

### Персонализация под клиента (Phase 31.5)
- Кастомные цвета под бренд клиента (из логотипа)
- Кастомный hero-блок с фото клиники
- Индивидуальный CTA текст

### PDF экспорт (Phase 31.6)
- Server-side PDF генерация (WeasyPrint / Playwright)
- Кнопка "Скачать PDF" в navigation bar

### Интерактивные чарты (Phase 31.7)
- Chart.js графики (тренды выручки, сравнение конкурентов)
- Интерактивная карта конкурентов (Яндекс.Карты API)

### Multi-language (Phase 31.8)
- Английская версия отчёта
- Переключение языка в navigation bar
</deferred>
