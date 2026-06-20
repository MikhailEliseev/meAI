# Session: 2026-06-21 — Фазы 2+3 перетестированы на iphk.ru ✅

## Текущий фокус: Фазы 2 и 3 работают на правильном тестовом сайте.

### Важное: DNS внутри контейнера
- Проблема с iphk.ru была **transient-сбоем** (после рестарта контейнера)
- Сейчас резолвится: iphk.ru → 79.174.93.31
- Docker DNS: 127.0.0.11 → upstream 8.8.8.8 / 1.1.1.1
- Не резолвится только blokhinclinic.ru (домен, вероятно, мёртв)

### Фаза 3 — переработка
- `run_review_platforms.py` v2: Perplexity (sonar-pro) — пошаговый запрос по платформам
  - Шаг 1: Яндекс.Карты, Шаг 2: Google Maps, Шаг 3: ПроДокторов, Шаг 4: 2ГИС, Шаг 5: Отзовик/IRecommend/Zoon
  - Пошаговый формат заставляет Perplexity копать глубже по каждой платформе
  - Fallback: DeepSeek (без web search)

### Результаты тестов на iphk.ru (Институт пластической хирургии и косметологии, Москва)

**Фаза 2 TECH AUDIT (73.9s):**
- PageSpeed: mobile=55, desktop=83
- Tech SEO: 96 images, 1% alt, title 81 chars (длинный), structured data: MedicalOrganization, WebSite
- AI: llms.txt=False, ai.txt=False
- Топ-3 проблемы: мобильная скорость, alt-теги, длинный title

**Фаза 3 SOCIAL VERIFIER (27.1s):**
- Яндекс.Карты: 5.0/5, 1152 отзыва
- ПроДокторов: 4.5/5, 100+ отзывов
- Google Maps, 2ГИС, Отзовик — не найдены
- Выявлены реальные проблемы: завышение стоимости, задержки приёма, навязывание услуг

### Фаза 2 (предыдущее)
- run_tech_seo_audit + run_pagespeed + AI-оптимизация (llms.txt/ai.txt/Schema.org)

### Фаза 1 (предыдущее)
- Perplexity→конкуренты, 3 дыры закрыты, interpretation_prompt v2

---
## Правило: НЕ ПЕРЕСОБИРАТЬ КОНТЕЙНЕР
- `docker cp` + `docker restart aim-hermes`
- Никаких `docker compose build` — теряется состояние бота
