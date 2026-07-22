# PROJECT_MAP — карта проекта meAI_1

> Создано 21 июля 2026 после большой уборки (commit `92a70f7c` + tag `known-good-17jul-0104`).
> Этот документ — ориентир для следующей сессии. Если запутались — читайте сюда.

---

## ⚠️ РЕАЛЬНОЕ СОСТОЯНИЕ ПРОДА (проверено 21 июля на сервере aim)

> **ВНИМАНИЕ:** Предыдущая версия этого документа утверждала «nginx на v1». Это было НЕВЕРНО —
> вывод сделан из git-истории локального репо, а на сервере конфиг правили напрямую без коммита.
> Ниже — реальные данные из `ssh aim` (сервер `78.17.128.169`, Ubuntu `AIM-Server-PL`).

```
ПРОД (iamaim.ru) — ПРОВЕРЕНО 21 июля:
  PHP-фронт → nginx: set $hermes "aim-hermes-v2:8000"     ← v2 УЖЕ В ПРОДЕ
  docker: aim-hermes-v2 Up 3 days (healthy), образ собран 2026-07-16T21:47
  v1 (aim-hermes) — ПОЛНОСТЬЮ УДАЛЁН (нет контейнера, нет образа aim-hermes:latest)

СЛЕДСТВИЕ: откатиться к v1 НЕЛЬЗЯ (его нет). Только git known-good-17jul-0104 для кода.
```

### РЕАЛЬНЫЕ ПРОБЛЕМЫ (что чинить, приоритизировано):

| # | Проблема | Когда | Влияние |
|---|---|---|---|
| 🔴 1 | **Perplexity quota exhausted** | упал **17 июля 23:59** (работал до 23:39) | 5 из 13 тулов падают 401: `extract_clinic_profile`, `quick_overview`, `run_review_platforms`, `perplexity_search`, `run_smi_mentions`. Профиль/отзывы/обзор клиентов не работают. Ключ `pplx-GQ5...c0Hb`, тариф `sonar-pro`, ОДИН ключ (нет пула). |
| 🟡 2 | Telegram webhook → 404 | с 16 июля | v2 не имеет `/telegram/webhook` роута. **Трафика нет в логах** — бот не используется. Низкий приоритет. |
| 🟡 3 | Образ v2 устарел | собран 16 июля 21:47 | Не содержит `ace9d62b` (17 июля 01:04): дизайн-система `:::section-num`, отзывы в чате, форматтеры. **Правки не видны пользователям.** |

### КОРЕНЬ «СЛОМАЛОСЬ» = Perplexity
Чат работает (LLM через z.ai отвечает), но при URL от клиента:
- ✅ `find_competitors` — работает (через aim-app)
- ❌ `extract_clinic_profile`, `quick_overview`, `run_review_platforms` — **401 Perplexity**

---

## Якорь чистого состояния

| Что | Где | Описание |
|---|---|---|
| Рабочий tag | `known-good-17jul-0104` → `ace9d62b` | «дизайн-система верстки + фикс рекомендаций + отзывы», 17 июля 01:04 |
| Страховочный stash | `stash@{0}` | WIP 18 июля: логирование + engine +173 строки. Вернуть: `git stash pop` |
| Текущая ветка | `feat/competitor-v2-perplexity-searxng` | HEAD = `92a70f7c` (уборка) |

Откатиться к рабочему: `git checkout known-good-17jul-0104 -- .` (только файлы) или `git reset --hard known-good-17jul-0104`.

---

## Структура (что есть что)

### Кодовая база
```
AIM/
├── hermes/          ← v1, ОБСЛУЖИВАЕТ ПРОД (не удалять!)
│   ├── app/main.py              (25KB, 77 tools)
│   ├── app/pipeline/            (engine.py, phases.py)
│   └── app/agent_wrapper.py     (54KB)
├── hermes-v2/       ← Walking Skeleton, активная разработка (НЕ в проде)
│   ├── app/main.py              (9.6KB, 6 tools)
│   ├── app/llm.py               (33KB)
│   ├── app/formatters/          (competitors.py, profile.py)
│   └── app/tools/               (find_competitors, run_ads, run_review_platforms, perplexity)
├── theme/
│   └── chat-inline-golden.php   ← фронт чата (HERMES_API = '/api/chat/stream')
├── docker-compose.yml           ← оба сервиса описаны
└── deploy/nginx/iamaim.conf     ← $hermes = "hermes:8000" (v1!)
```

### Git (после уборки: 7 веток)
- `feat/competitor-v2-perplexity-searxng` — текущая работа (14-21 июля)
- `main` — «FINAL GOLDEN STATE» (15 июля)
- `feat/meai-core-foundation` — default на origin
- `checkpoint/2026-07-15-markedjs-prompt-cleanup` — checkpoint
- `backup/all-changes-2026-06-17` — страховка (есть на remote)
- `backup-before-filter-20260515-135320` — старая (май)
- `feature/chat-ux-improvements` — старая (27 июня)

### Архивы (не трогать, historical)
```
docs/archive/
├── legacy-desktop-files/                    ← 99 файлов из "strange files on desktop"
│   ├── Конкурентный анализ ARclinic*.html   (клиентские отчёты)
│   ├── iphk-*-report.md
│   ├── Dual Theme Design System*.html
│   └── finforsellers-*.html
└── worktree-snapshots-2026-05/              ← 52 summary из удалённых worktrees
    ├── 2026-05-sprint-1/
    ├── 2026-05-phase6-e2e/
    ├── 2026-05-plan1-infra/
    └── 2026-05-plan2-magisters/

meAI_1-backups/    ← UNTRACKED (gitignored), 32M, tar.gz от 14 июля. Пограничная дата, оставлена.
```

---

## Что было сделано при уборке (21 июля)

| Этап | Действие | Результат |
|---|---|---|
| 0 | tag `known-good-17jul-0104` | якорь поставлен |
| 1 | Сташи 1-8 удалены, битый reflog починён | 9→1 сташ |
| 2 | 4 dead worktrees удалены | **-1.07 GB** |
| 3 | ОТМЕНЁН — hermes v1 в проде | оставлен |
| 4 | Старые бэкапы (до 14 июля) удалены, strange files → archive | commit `92a70f7c` |
| 5 | 48 веток удалено (squash-merged + merged + dead) | 55→7 веток |

**До уборки:** 55 веток, 9 сташей, 1.5GB worktrees, 36721 незакоммиченный файл, битый stash reflog.
**После:** 7 веток, 1 сташ, чистое дерево, понятная карта.

---

## Открытые вопросы (на следующую сессию)

1. **🔴 Perplexity quota** — пополнить баланс perplexity.ai ИЛИ дать новый ключ ИЛИ отключить Perplexity-тулы (`USE_PERPLEXITY=false`). Решение за Михаилом (платный сервис).
2. **🟡 Пересобрать образ v2** из `ace9d62b` (дизайн-система, отзывы, форматтеры) — после решения по Perplexity, одним деплоем.
3. **🟡 Telegram** — добавить заглушку `/telegram/webhook` в v2 ИЛИ убрать location из nginx. Трафика сейчас нет, низкий приоритет.
4. Что делать с 3 старыми бэкап-ветками (backup/*, feature/chat-ux)?
5. `meAI_1-backups/` (32M) — оставить или удалить?

---

## Команды для работы с сервером

```bash
# SSH
ssh aim                                    # root@78.17.128.169 (AIM-Server-PL, Ubuntu)

# v2 логи (живой трафик, без health-noise)
ssh aim "docker logs aim-hermes-v2 --tail 50 -f 2>&1 | grep -v 'GET /health'"

# Проверить health v2
ssh aim "docker exec aim-hermes-v2 curl -s http://localhost:8000/health"

# Пересобрать и перезапустить v2 (после git pull на сервере)
ssh aim "cd /opt/aim/AIM && docker compose build hermes-v2 && docker compose up -d hermes-v2"

# Проверить Perplexity ключ
ssh aim "grep PERPLEXITY /opt/aim/AIM/.env.production"

# Откатить код v2 к известному-хорошему (ОСТОРОЖНО: v1 уже удалён, отката к v1 нет)
ssh aim "cd /opt/aim/AIM && git fetch && git checkout known-good-17jul-0104 -- AIM/hermes-v2/"
ssh aim "cd /opt/aim/AIM && docker compose build hermes-v2 && docker compose up -d hermes-v2"
```

---

## 🌙 Ночная сессия 21-22 июля 2026 (баг-хантинг + фиксы)

### Найденные и исправленные баги (6 шт):

1. **`_format_reviews_block` markdown ломался** — `"".join(lines)` вместо `"\n".join(lines)`.
   Блок 04 рендерился как сырой текст. Fixed.

2. **Apify actors: неверный input format** — `searchStrings` не существует, правильно `query` + `locations`.
   Я соврал про "Monthly usage hard limit exceeded" — ключи работали, проблема была в моём коде. Fixed.

3. **Apify actors: не ретраить при 500** — платформа Apify иногда лежит, retry на другие ключи
   давал тот же 500 и подвешивал чат на 10+ минут. Fixed (выходим сразу при >=500).

4. **`collected_results = {}` сбрасывался каждый раунд** — auto-calls (financials, reviews)
   не видели результаты прошлых раундов. Блоки 01 и 04 исчезали. Fixed (накапливается).

5. **SearXNG 403 Forbidden** — bot detection блокировал все запросы с 17 июля.
   `find_competitors` работал 211 сек (вместо 90). Fixed (`limiter: false` в settings).

6. **Pre-stream auto-calls пропускались** — если LLM в turn 1 не вызывала тулы,
   auto-calls (extract_clinic_profile, financials, reviews) не выполнялись.
   Fixed (отдельный блок перед streaming, расширенное условие).

7. **Auto-call INN source** — `client_inn` искался только в find_competitors response,
   но aim-app не возвращает его. Fixed (fallback на `profile_cache.inn`).

### Тесты: 72/72 PASS
- 16 тестов в test_reviews_apify.py (Apify actors)
- 12 тестов в test_pipeline_fixes.py (UI messages, financials, fallback)
- 44 теста в остальных (session, competitors, anti-hallucination, key pool)

### Состояние проде (на 22 июля ~00:30 МСК):
- ✅ v2 healthy, SearXNG работает (200), Apify работает (201)
- ⚠️ z.ai 429 (5h limiter) — сброс в 05:49 UTC (08:49 МСК)
- ⚠️ find_competitors ~90 сек (было 211) — всё ещё медленно, но терпимо
- ❌ Блоки 01/04 не проверены в реальном e2e (z.ai 429 мешает)

### Коммиты этой сессии:
- `34d8c930` fix(critical): pre-stream auto-calls
- `159ce866` fix(critical): collected_results накапливает
- `586b5bf9` fix(critical): collected_results reset
- `35a7db6f` fix(financials): INN из profile_cache
- `11c4118f` test: починить 2 устаревших теста
- `1e39bb7f` fix(review): critical — выручка доходит до блока 01
- `8cf3efa0` fix(reviews): graceful fallback
- `4a885766` feat(pipeline): auto-call financials
- `94f71559` fix(ui): честные сообщения (Google Maps→ФНС)
