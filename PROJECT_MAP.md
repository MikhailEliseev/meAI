# PROJECT_MAP — карта проекта meAI_1

> Создано 21 июля 2026 после большой уборки (commit `92a70f7c` + tag `known-good-17jul-0104`).
> Этот документ — ориентир для следующей сессии. Если запутались — читайте сюда.

---

## ⚠️ КРИТИЧЕСКОЕ ОТКРЫТИЕ (корень «бардака»)

**Весь фреш-код 14-17 июля писали в `hermes-v2/`, но в проде бегает `hermes/` v1.**

```
ПРОД (iamaim.ru):
  PHP-фронт (chat-inline-golden.php)
    → nginx: proxy_pass http://hermes:8000/api/chat/stream     ← v1
  docker: подняты ОБА сервиса (hermes + hermes-v2), но nginx ходит только на v1

КОД (git):
  AIM/hermes/      — v1, ПОЛНАЯ прод-система (77 tools), последний коммит 16 июля 03:09
  AIM/hermes-v2/   — Walking Skeleton Phase 1 (6 tools), последний коммит 17 июля 01:04
```

**Следствие:** правки дизайн-системы, отзывов, форматтеров (коммит `ace9d62b`) **не видны пользователям**.
docker-compose прямо комментирует: «Старый сервис hermes НЕ трогаем — страховка отката».

### СЛЕДУЮЩИЙ ШАГ (главный)
Решить: доделать v2 и переключить nginx `$hermes = "hermes-v2:8000"`, ИЛИ отказаться от v2 и вернуться к правкам v1.
Файл: `AIM/deploy/nginx/iamaim.conf:44` (`set $hermes "hermes:8000";`).

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

1. **ГЛАВНОЕ:** v1 или v2 — какой hermes развивать дальше?
2. Если v2 — переключить nginx и протестировать end-to-end.
3. Если v1 — перенести правки дизайн-системы/отзывов из v2 в v1.
4. Что делать с 3 старыми бэкап-ветками (backup/*, feature/chat-ux)?
5. `meAI_1-backups/` (32M) — оставить или удалить?
