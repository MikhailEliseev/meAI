# Hermes Migration Package

**Дата создания:** 2026-06-20 00:29
**Архив:** `hermes_migration_20260620_002901.tar.gz` (338 KB)
**Назначение:** Полный бекап Hermes для переезда на новый сервер

---

## Содержимое архива

### Конфигурация
- `config.yaml` — конфигурация модели (DeepSeek v4 Pro), таймауты pipeline, file_protection, mode_gate
- `.env` — все API-ключи (DeepSeek, Apify ×14, Firecrawl ×15, OpenRouter, Telegram, WordPress DB)
- `SOUL.md` — личность Hermes, инструкции, уроки (69 KB)

### Код
- `app/` — 37 инструментов Hermes
  - `routers/session_api.py` — FastAPI роутер для веб-чата
  - `voice_transcriber.py` — транскрипция голосовых сообщений
  - `omniroute_direct.py` — прямой роутинг между Telegram и веб-чатом
  - `tools/` — 37 инструментов (aim-operations + hermes-debug)

### Инструменты AIM Operations (15 tools)
1. `run_aim_scout.py` — aim-scout v7.0 (17 фаз: prescan → competitors → cross-employment → forum scraping → HTML report)
2. `find_competitors.py` — поиск конкурентов через Apify (Google Maps)
3. `present_competitors.py` — форматирование списка конкурентов для клиента
4. `run_prescan.py` — prescan сайта (3 стадии: tech audit, social verifier, content analysis)
5. `run_content_analysis.py` — контент-анализ
6. `show_project_status.py` — статус проекта
7. `collect_contact.py` — сбор контактов (имя, телефон, email)
8. `qualify_lead.py` — квалификация лида
9. `escalate_to_manager.py` — передача менеджеру
10. `update_knowledge.py` — запись знаний
11. `run_doctor_dossiers.py` — досье врачей
12. `generate_html_report.py` — HTML-отчёты в дизайн-системе AIM
13. `run_background_pipeline.py` — фоновый пайплайн
14. `run_web_search.py` — веб-поиск через Firecrawl
15. `run_validation_check.py` — валидация результатов

### Hermes Debug Tools (22 tools)
- `shell_exec.py` — выполнение shell-команд
- `web_scraper.py` — скрейпинг сайтов
- `bitrix_scraper.py` — парсинг Битрикса
- `rotate_api_key.py` — ротация API-ключей
- `run_pagespeed.py` — PageSpeed тесты
- `run_review_platforms.py` — агрегация отзывов
- `run_content_gaps.py` — контент-гэпы
- `deep_research_merge.py` — мёрдж глубокой разведки
- `geo_optimizer_tools.py` — гео-оптимизация
- И другие debug-инструменты

### Скиллы
- `skills/` — директория скиллов Hermes (client-onboarding-pipeline v6.2.0, aim-scout v7.0, ui-ux-pro-max)

### База знаний
- `knowledge/` — знания агентов (teacher/, seo/, content/, ads/)
  - `teacher/` — Teacher Agent (Chief Learning Officer)
  - `seo/` — SEO-знания
  - `content/` — контент-маркетинг
  - `ads/` — реклама (Яндекс.Директ)

### Память
- `memories/` — память Hermes (долгосрочная, проектная, лидовая)

### AIM интеграция
- `AIM/` — интеграция с WordPress (публикация отчётов, досье врачей)

### Ключи
- `keys/` — ротируемые API-ключи
- `apify_keys.json` — 14 Apify-ключей с метаданными
- `firecrawl_keys.json` — 15 Firecrawl-ключей с метаданными

---

## Модель и провайдер

**КРИТИЧНО:** Hermes работает **только** на DeepSeek v4 Pro через прямой API.

### config.yaml
```yaml
model:
  default: deepseek-chat
  provider: deepseek

providers:
  deepseek:
    base_url: https://api.deepseek.com/v1
    api_key: ${DEEPSEEK_API_KEY}
```

### .env
```bash
LLM_MODEL=deepseek-chat
LLM_PROVIDER=deepseek
LLM_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_API_KEY=sk-ffa554cfd26b4b4193142819e469d6a4
```

**Важно:** Переменные `.env` имеют приоритет над `config.yaml`. Секция `providers.deepseek` в config.yaml обязательна, иначе hermes-agent регенерирует дефолтную конфигурацию (OpenRouter + gpt-4o-mini).

---

## Инструкции по развёртыванию

### 1. Распаковать архив
```bash
tar xzf hermes_migration_20260620_002901.tar.gz -C /opt/hermes/
```

### 2. Создать docker-compose.yml
```yaml
version: '3.8'

services:
  hermes:
    image: ghcr.io/cktang88/hermes-agent:latest
    container_name: hermes
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - /opt/hermes:/opt/hermes
      - /opt/data:/opt/data
    environment:
      - PYTHONUNBUFFERED=1
    command: hermes gateway
```

### 3. Запустить контейнер
```bash
docker-compose up -d hermes
```

### 4. Проверить статус
```bash
docker exec hermes hermes status
```

Должно быть:
```
Model:        deepseek-chat
Provider:     DeepSeek
DeepSeek      ✓ sk-f...d6a4
```

### 5. Защитить конфигурацию
```bash
docker exec hermes chmod 444 /opt/hermes/config.yaml
```

---

## Проблемы и решения

### Проблема: Hermes падает на OpenRouter/gpt-4o-mini
**Причина:** hermes-agent регенерирует config.yaml при отсутствии секции `providers`

**Решение:**
1. Добавить секцию `providers.deepseek` в config.yaml
2. Добавить `LLM_MODEL`, `LLM_PROVIDER`, `LLM_BASE_URL` в .env
3. Защитить config.yaml (chmod 444)

### Проблема: "No LLM provider configured"
**Причина:** Отсутствует секция `providers` в config.yaml или переменные в .env

**Решение:**
```bash
# Проверить .env
docker exec hermes cat /opt/hermes/.env | grep LLM

# Проверить config.yaml
docker exec hermes cat /opt/hermes/config.yaml | head -10

# Перезапустить
docker restart hermes
```

---

## Версии

- **Hermes:** v7.0 (2026-06-20)
- **aim-scout:** v7.0 (17 фаз)
- **client-onboarding-pipeline:** v6.2.0
- **Python:** 3.11.15
- **hermes-agent:** latest (ghcr.io/cktang88/hermes-agent)

---

## Контакты

- **Сервер:** Polish AIM server (78.17.128.169, `ssh aim`)
- **Проект:** meAI → AIM (iamaim.ru)
- **Репо:** github.com/username/meAI
