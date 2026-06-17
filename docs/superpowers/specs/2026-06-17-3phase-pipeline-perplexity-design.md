# 3-Phase Presale Pipeline with Perplexity

**Status:** spec  
**Date:** 2026-06-17  
**Goal:** Упростить пресейл-пайплайн до трёх фаз: быстрый хук (Perplexity) → глубокий анализ (scout-инструменты в фоне) → продающая презентация

## Контекст

Текущая система: 49 инструментов Hermes, ~7 используются в интерактивном пресейле. Проблемы:

1. Клиент ждёт 60-90 секунд тишины перед первым результатом — теряем лиды
2. Пайплайн требует присутствия клиента в чате 5-7 шагов — неестественно
3. aim-app падает с 500 из-за prometheus-fastapi-instrumentator

## Три фазы

### Фаза 1 — Хук и вау-эффект (интерактивная, ~90 сек)

```
Клиент: cliniclancette.ru
  │
  ├─ [t=0] Hermes запускает quick_overview(url) + run_prescan(url) ПАРАЛЛЕЛЬНО
  │
  ├─ [t=~5s] Perplexity вернул → Hermes нарративит 2-3 абзаца:
  │   «Нашёл. Клиника "Ланцетъ", Ростов-на-Дону, стоматология.
  │    ООО "Ланцетъ", на рынке с 2019. Выручка ~18 млн ₽ (Rusprofile).
  │    4 ключевых врача. 12 конкурентов в радиусе 3 км.
  │    Instagram активен. Уже копаю глубже — финансы, лицензии, SEO...»
  │
  ├─ [t=~25s] prescan стадия 1 → «ООО "Ланцетъ", ИНН 6166..., выручка 18.2 млн ₽...»
  ├─ [t=~50s] prescan стадия 2 → «Лицензия ЛО-61-01-..., SEO 62/100...»
  ├─ [t=~80s] prescan стадия 3 → «Рынок: 12 конкурентов...»
  │
  └─ ВАУ → «Хотите полный анализ конкурентов? Оставьте Telegram — пришлю через час.»
      └─ collect_contact
```

### Фаза 2 — Глубокий анализ (фоновая, 1-2 часа)

```
[Клиент ушёл]
  │
  └─ run_background_pipeline(session_hash)
       │
       ├─ find_competitors          (Apify, ~180s)
       ├─ run_ci_analysis           (каждый конкурент, ~300s)
       ├─ run_seo_audit             (~120s)
       ├─ run_review_platforms      (~120s)
       ├─ run_doctor_dossiers       (~120s)
       ├─ run_pagespeed             (~60s)
       ├─ run_ads_intelligence      (~120s)
       ├─ find_company_financials   (~60s)
       ├─ run_instagram_content     (~60s)
       ├─ run_content_analysis      (~120s)
       └─ generate_html_report
            └─ → /opt/data/sessions-archive/{hash}/report.html
```

### Фаза 3 — Продающая презентация

```
Все данные из session archive
  │
  └─ Промт Perplexity #2 (sell_presentation)
     │
     └─ Структура:
        1. Сколько пациентов ты недополучаешь (одна цифра, три источника)
        2. Сколько мы приведём (таблица: канал → сейчас → будет → +пациенты → +выручка)
        3. Что для этого нужно сделать (три действия + сроки)
        4. Сколько стоит и когда окупится (инвестиция, ROI, срок)
```

## Новые компоненты

### quick_overview (новый инструмент Hermes)

Файл: `AIM/hermes/app/tools/quick_overview.py`

- Принимает URL клиники
- Вызывает Perplexity API: `POST https://api.perplexity.ai/chat/completions`, модель `sonar-pro`
- API-ключ: `PERPLEXITY_API_KEY` в `AIM/.env`
- Perplexity API совместим с OpenAI SDK (base_url: `https://api.perplexity.ai`)
- Возвращает структурированный JSON с 6 секциями
- Таймаут: 15 секунд
- Параллельный запуск с run_prescan через `asyncio.gather()`

Промт Perplexity #1: `AIM/hermes/app/prompts/quick_overview.txt`

Системный промт Perplexity: «Ты — AI-аналитик медицинского маркетинга. Изучи клинику по URL.»

Секции:
1. БИЗНЕС — название, юрлицо, ИНН, год, адрес, специализация, выручка, прибыль, тренд
2. ВРАЧИ — 3-5 ключевых врачей, главный врач, упоминания
3. КОНКУРЕНТЫ — 3-5 ближайших в том же городе, название, сайт, чем известны
4. СОЦСЕТИ — Instagram, VK, Telegram, YouTube, Яндекс.Карты, ссылки, активность
5. САЙТ — платформа, качество, глубина
6. ЗАЦЕПКА — один неожиданный факт, который удивит владельца

Требования к ответу: секции с заголовками, только факты из источников, каждый факт со ссылкой.

### run_background_pipeline (новый инструмент Hermes)

Файл: `AIM/hermes/app/tools/run_background_pipeline.py`

- Вызывается Hermes как обычный tool call после `collect_contact`
- Клиент уже ушёл — инструмент работает без ожидания ответа
- Таймаут: 3600 секунд (1 час)
- Принимает session_hash
- Последовательно запускает scout-инструменты
- Сохраняет результаты в session archive
- Вызывает generate_html_report
- После завершения: вызывает sell_presentation (Фаза 3) через Perplexity API

Инструменты в пайплайне:
- find_competitors, run_ci_analysis
- run_seo_audit, run_content_analysis, run_content_gaps
- run_review_platforms, run_doctor_dossiers, run_pagespeed
- run_ads_intelligence, run_ads_report
- find_company_financials, run_instagram_content
- generate_html_report

### sell_presentation (промт, не инструмент)

Файл: `AIM/hermes/app/prompts/sell_presentation.txt`

Использует Perplexity API (или DeepSeek) для генерации продающей презентации из всех данных Фазы 2. Структура: потерянные пациенты → прогноз → действия → цена и ROI.

## Изменения в существующем коде

### agent_wrapper.py — _presale_prompt()

Новая логика первого шага:
1. При получении URL → вызвать `quick_overview` + `run_prescan` параллельно
2. Показать результат Perplexity (2-3 абзаца)
3. Показать prescan-нарратив (3 стадии)
4. «Хотите глубокий анализ конкурентов?» → collect_contact
5. Запустить `run_background_pipeline` в фоне

### AIM/src/aim/main.py

Закомментировать или удалить `Instrumentator().instrument(app).expose(app)`.
Причина: prometheus-fastapi-instrumentator 8.0.0 падает на `_IncludedRouter` объектах FastAPI.
Мониторинг не используется в presale-пайплайне — проще убрать, чем чинить.

### AIM/requirements.txt

Убрать `prometheus-fastapi-instrumentator` (не используется в пайплайне).

### AIM/hermes/requirements.txt (если есть)

Добавить зависимость Perplexity API:
```
openai>=1.0  # Perplexity API совместим с OpenAI SDK
```

## Промты

### Промт Perplexity #1 — quick_overview

```
Ты — AI-аналитик медицинского маркетинга. Изучи клинику по URL {url}.

Собери строго по источникам:

1. БИЗНЕС
   — Название, юрлицо, ИНН
   — Год регистрации, город, адрес
   — Специализация, основные услуги
   — Выручка и прибыль за последний год (Rusprofile / bo.nalog.ru)
   — Тренд выручки: растёт / падает / стабильно

2. ВРАЧИ
   — 3-5 ключевых врачей (ФИО, специализация)
   — Кто главный врач / основатель
   — Упоминания на сторонних ресурсах

3. КОНКУРЕНТЫ
   — 3-5 ближайших конкурентов в том же городе и специализации
   — Название, сайт, чем известны

4. СОЦСЕТИ
   — Instagram, VK, Telegram, YouTube, Яндекс.Карты
   — Ссылки, примерная активность

5. САЙТ
   — Платформа (Tilda, 1C-Bitrix, WordPress, самопис)
   — Качество: лендинг или полноценный сайт
   — Количество страниц (примерно)

6. ЗАЦЕПКА
   — Один неожиданный факт или цифра, которая удивит владельца

Формат ответа: секции с заголовками. Только факты из источников.
Каждый факт — со ссылкой на источник. Без воды.
```

### Промт Perplexity #2 — sell_presentation

```
Ты — стратегический маркетолог медицинского агентства AIM.
Клиент: {clinic_name}, {city}, {specialization}.

Напиши продающую презентацию на основе данных ниже.
Главный вопрос клиента: «Сколько пациентов вы приведёте и за какие деньги?»

Структура:

1. СКОЛЬКО ПАЦИЕНТОВ ТЫ НЕДОПОЛУЧАЕШЬ
   Одна цифра первым абзацем. Три источника потерь — откуда.

2. СКОЛЬКО МЫ ПРИВЕДЁМ
   Таблица: Канал | Сейчас | Будет | +Пациентов | +Выручка
   Итоговая строка с суммой.

3. ЧТО ДЛЯ ЭТОГО НУЖНО СДЕЛАТЬ
   Три действия со сроками. Без деталей — только суть.

4. СКОЛЬКО СТОИТ И КОГДА ОКУПИТСЯ
   Инвестиция, ежемесячные затраты, окупаемость, годовая выручка.

Стиль: живой, уважительный, «смотри, у тебя здесь так, а можно так».
Короткие абзацы. Без маркетинговых штампов. Максимум 3 страницы.

ИСХОДНЫЕ ДАННЫЕ:
{all_data_from_session_archive}
```

## План реализации

### Шаг 0: Починить aim-app
- Убрать `Instrumentator` из `AIM/src/aim/main.py`
- Закрепить зависимости в `AIM/requirements.txt`
- Пересобрать Docker-образ
- Проверить: curl `/api/presale/prescan-staged` → 200

### Шаг 1: quick_overview
- Создать `hermes/app/prompts/quick_overview.txt`
- Создать `hermes/app/tools/quick_overview.py`
- Зарегистрировать в `aim-operations`
- Протестировать на реальных URL

### Шаг 2: run_background_pipeline
- Создать `hermes/app/tools/run_background_pipeline.py`
- Последовательный вызов scout-инструментов
- Сохранение результатов в session archive
- Вызов generate_html_report

### Шаг 3: Обновить _presale_prompt()
- Новая логика Фазы 1: parallel quick_overview + run_prescan
- Сбор контакта после вау-эффекта
- Запуск background_pipeline

### Шаг 4: sell_presentation
- Создать `hermes/app/prompts/sell_presentation.txt`
- Интеграция с Perplexity API для Фазы 3

### Шаг 5: Деплой и тестирование
- Собрать Docker-образы
- Деплой на Polish server
- End-to-end тест с реальной клиникой

## Критерии успеха

1. Клиент получает первый ответ за < 10 секунд (Perplexity)
2. prescan-нарратив начинается без дополнительной паузы
3. Весь интерактивный диалог (Фаза 1) < 2 минут
4. Фаза 2 завершается без ошибок, все данные в session archive
5. Фаза 3 генерирует презентацию с конкретными цифрами: пациенты + деньги + ROI
