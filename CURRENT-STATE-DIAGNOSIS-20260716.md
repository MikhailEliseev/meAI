# Текущее состояние системы — Памятка для диагностики (2026-07-16 10:54)

## 🔴 Критическая проблема

**Pipeline падает с TypeError:** `resolve_brands_batch() got an unexpected keyword argument 'max_brands'`

### Что происходит:
1. Код на диске обновлён (параметр `max_brands=40` добавлен в `brand_resolver.py`)
2. rsync успешно скопировал файлы на сервер
3. Docker build выполнен 2 раза
4. **НО:** Контейнер aim-app работает со СТАРОЙ версией кода

### Почему:
Docker **кэширует** слои при сборке. Файл `brand_resolver.py` не попал в новый образ из-за:
- Aggressive layer caching
- COPY команда в Dockerfile использует кэш предыдущего слоя
- `docker build` без `--no-cache` не пересобирает Python файлы

### Последняя попытка:
Запустил `docker build --no-cache` но процесс был отменён (занимает 5-10 минут).

---

## 📊 Что сделано за сессию

### ✅ Успешно реализовано:
1. **8 багфиксов** из плана 2026-07-16-data-accuracy-bugfixes.md
   - Robots parser consecutive User-agent
   - Doctor heading regex
   - Instagram duplicate + private accounts
   - scraped_services → revenue_history
   - Brand resolver timeout
   - VK followers comma separator
   - _is_related_entity generic words filter
   - Exhausted keys TTL 1h

2. **5 раундов Code Review**
   - Найден orphaned `try:` (SyntaxError)
   - Исправлены все критические баги

3. **F1-F11** все фичи реализованы
   - GEO Score, VK followers, Yandex rating работают

4. **Оптимизации производительности** (план 2026-07-16-pipeline-performance-optimization.md)
   - Task 1: Perplexity limit 20 per prompt
   - Task 2: Semaphore 5→15 (bo.nalog concurrency)
   - Task 3: max_brands=40 в resolve_brands_batch
   - Task 4: count=10 по умолчанию (было 5)

### ⚠️ Проблемы:
- **Docker кэш:** Код не попадает в контейнер
- **Время pipeline:** Было 330s, цель 90-150s — не протестировано из-за Docker кэша
- **hermes-v2 format_competitors:** Приходилось пересобирать 3 раза (забывал)

---

## 🔍 Что нужно продиагностировать

### 1. Проверить что в контейнере (ПРИОРИТЕТ 1)
```bash
ssh aim 'docker exec aim-app cat /app/AIM/src/aim/services/brand_resolver.py | grep -A 5 "def resolve_brands_batch"'
```

**Ожидаемое:** Должен быть параметр `max_brands: int = 40`

**Если нет:** Docker build не подхватывает изменения файлов.

---

### 2. Проверить Dockerfile COPY команды
```bash
cat /opt/aim/AIM/Dockerfile | grep -E "COPY|FROM"
```

**Возможная проблема:** COPY использует wildcard или кэш слоя со старыми файлами.

**Решение:** 
- Option A: `docker build --no-cache` (долго, но надёжно)
- Option B: Изменить Dockerfile чтобы COPY был после установки зависимостей
- Option C: `docker system prune -a` перед build (удалит весь кэш)

---

### 3. Проверить rsync скопировал правильные файлы
```bash
ssh aim 'grep -n "max_brands" /opt/aim/AIM/src/aim/services/brand_resolver.py | head -3'
```

**Ожидаемое:** Должны быть строки с `max_brands=40` и `max_brands: int = 40`.

**Если нет:** rsync не скопировал или скопировал старую версию.

---

### 4. Проверить что Docker образ свежий
```bash
ssh aim 'docker images aim:latest --format "{{.CreatedAt}}"'
```

**Ожидаемое:** Время должно быть в пределах последних 10 минут.

**Если старше:** Docker build не пересоздал образ.

---

## 🛠️ План действий для продолжения

### Вариант A: Быстрый (5-10 минут)
1. Завершить `docker build --no-cache` (было отменено)
2. Пересобрать hermes-v2 тоже с --no-cache
3. Тест на toriclinic.ru
4. Замерить время (цель <150s)

### Вариант B: Надёжный (15 минут)
1. `docker system prune -a` — удалить весь кэш
2. `docker build --no-cache -t aim:latest`
3. `docker compose build --no-cache hermes-v2`
4. Перезапустить оба контейнера
5. Тест на toriclinic.ru

### Вариант C: Debug (если A/B не помогут)
1. Проверить Dockerfile построчно
2. Изменить порядок COPY команд
3. Добавить `RUN echo "$(date)" > /tmp/build_timestamp` для инвалидации кэша
4. Пересобрать

---

## 📝 Файлы изменённые за сессию

### aim-app (Python backend):
- `AIM/src/aim/services/lib/seo_auditor.py` — robots parser, VK, Yandex, media
- `AIM/src/aim/services/lib/firecrawl_enricher.py` — doctors, exhausted keys TTL
- `AIM/src/aim/services/lib/instagram_enricher.py` — duplicate removal, private accounts
- `AIM/src/aim/services/competitor_matcher_v2.py` — Perplexity limit 20, max_brands=40 call
- `AIM/src/aim/services/brand_resolver.py` — **max_brands=40 parameter**, semaphore 15, timeout
- `AIM/src/aim/services/rusprofile/models.py` — revenue_history field
- `AIM/src/aim/api/competitors.py` — count=10 default

### hermes-v2 (Chat frontend):
- `AIM/hermes-v2/app/llm.py` — audit block format, perf/media/VK/Yandex
- `AIM/hermes-v2/app/formatters/competitors.py` — client_reg_date, client_scl
- `AIM/hermes-v2/app/formatters/overview.py` — platform removed
- `AIM/hermes-v2/app/tools/competitors.py` — count=10 default

### Планы:
- `docs/superpowers/plans/2026-07-16-data-accuracy-bugfixes.md`
- `docs/superpowers/plans/2026-07-16-pipeline-performance-optimization.md`

### Отчёты:
- `AUTONOMOUS-SESSION-REPORT-20260716.md`
- `HANDOFF-2026-07-16.md`

---

## 🎯 Цель после исправления Docker кэша

**toriclinic.ru должен обработаться за 90-150 секунд** (было 330s):
- Stage 1: 13 брендов вместо 71 ✅ (видно в логах)
- Stage 2: 40 брендов / 15 параллельно = 15-20s (оптимизация)
- Stage 3.5: 10 конкурентов enrichment = 60-80s
- **Итого:** 90-150s

---

## 💾 Бэкапы

- Git tag: `meAI_1-backup-20260716-final`
- Server: `/opt/backups/code-backup-20260716-final/aim-code.tar.gz` (107M)
- Branch: `feat/competitor-v2-perplexity-searxng`
- Commits за сессию: 50+

---

## ⚡ Следующий шаг

**Выбери вариант A или B** — завершить полную пересборку Docker без кэша и протестировать toriclinic.ru.

После этого — замерить время и убедиться что оптимизации работают (71→13 брендов уже видно, это хорошо).
