# 04 — Broken Components

Что **не работает по задумке** — с severity-метками. Порядок: 🔴 blocking → 🟡 important → 🟢 nit.

---

## 🔴 BLOCKING — критичные проблемы

### 1. PostgreSQL auth сломан — backend не может писать в БД

**Симптом:**
```
$ docker exec aim-app curl -s http://localhost:8000/ready
{
  "status": "not_ready",
  "checks": {"database": false, "redis": true, "event_bus": true}
}
```

**Техническая причина:**
```
$ docker exec aim-app python -c "..."
ERR: InvalidPasswordError password authentication failed for user "aim_user"
```

- Docker volume `aim_postgres_data` инициализирован с паролем `A` (давно)
- В `.env.production` POSTGRES_PASSWORD = `B` (другой)
- PostgreSQL хранит хэш пароля `A`, app пытается подключиться с `B`

**Влияние (что НЕ работает из-за этого):**
- ❌ Все endpoints leads (`POST /api/leads`, `POST /api/leads/capture`, `GET /api/leads`)
- ❌ Analytics (`/api/analytics/*` — все 5 endpoints)
- ❌ Sales (`/api/sales/*` — все 7 endpoints)
- ❌ Onboarding (`/api/onboarding/*` — все 6 endpoints)
- ❌ Email automation (`email_workflows`, `email_events`)
- ❌ GDPR right-to-erasure (`DELETE /api/gdpr/leads/{lead_id}`)
- ❌ Payments table
- ❌ Audit trail
- ❌ Campaigns

**PostgreSQL имеет 45 таблиц — все пустые.** Только `event_bus_messages` имеет 4 строки за всё время (видимо от boot-time эвентов).

**Фикс:** синхронизировать пароль в `.env.production` с тем, что в volume, либо пересоздать volume с новым паролем (потеряв 4 строки event_bus_messages).

---

### 2. Phase 09 не задеплоена — `.current-task` и SESSION.md врут

**Что говорят документы:**
- `.current-task`: "Phase 09 deployed. Test hermes-chat-pro.html end-to-end"
- `SESSION.md`: "✅ Hermes backend: report_url в finish event / ✅ WordPress frontend: hermes-chat-pro.html с Phase Tracker (1020 строк) / ✅ Hermes контейнер перезапущен (04:56:47 UTC)"

**Реальность на сервере:**
```
$ curl -sI https://iamaim.ru/wp-content/themes/aim-theme/chat/hermes-chat-pro.html
HTTP/2 404
```

- `hermes-chat-pro.html` **не существует** ни в Docker volume `aim_wp_content`, ни в `wp-content/themes/aim-theme/chat/`
- Backup-файлы от Phase 09 лежат в `/opt/aim/AIM/hermes/app/`:
  - `main.py.backup-phase09-20260628-075019`
  - `main.py.backup-phase09-20260628-075030`
- Это значит: был commit, были backup-файлы, но **deploy не завершился** или **был откат**

**Влияние:**
- Главный таск из `.current-task` невыполним — файла нет
- Phase 09 функционал (Phase Tracker, Report Preview, Fallback Form) недоступен клиентам

**Фикс:** либо задеплоить файл `hermes-chat-pro.html` на сервер, либо обновить `.current-task` на актуальную задачу.

---

### 3. HeadroomGuard интеграция отсутствует, но описана в SESSION.md как активная

**Что говорит SESSION.md (секция "Текущая конфигурация production"):**
```yaml
HeadroomGuard:
  container: aim-headroom-proxy
  port: 8787
  upstream: https://api.z.ai/api/coding/paas/v4
  mode: optimize

Hermes:
  container: aim-hermes
  OMNIROUTE_URL: http://headroom-proxy:8787/v1
  LLM_MODEL: glm-5
```

**Реальность:**
```
$ docker ps -a --filter name=aim-headroom
(NONE)

$ docker exec aim-hermes env | grep -iE "OMNIROUTE|HEADROOM"
OMNIROUTE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-v4-pro
```

- Контейнера `aim-headroom-proxy` **нет вообще** (даже exited)
- В env Hermes — **напрямую DeepSeek API**, минуя любой прокси
- LLM_MODEL = `deepseek-v4-pro`, не `glm-5`

**Влияние:**
- Вся секция SESSION.md "Phase 2: Testing (⏳ IN PROGRESS)" — не актуальна
- Команда может тратить время на "тестирование HeadroomGuard", не зная что его нет

**Фикс:** обновить SESSION.md, удалить упоминания HeadroomGuard как активного, либо действительно развернуть sidecar.

---

## 🟡 IMPORTANT — серьёзные проблемы

### 4. SOUL.md рассинхронизирован между Docker образом и volume

**Два файла:**
```
/opt/hermes/skills/aim/SOUL.md  (в Docker образе aim-hermes:latest)
  size: 47 KB
  lines: 760
  name: aim-operator-v4
  md5: 24ef46572ed8c46fb120899038c268b6

/opt/data/SOUL.md  (в persistent volume, реально используется)
  size: 106 KB
  lines: 1411
  name: aim-operator
  md5: baf5a424ee1034d31fb4913e26287b78
```

**Скрипт `copy_soul.sh`:**
```bash
if [ ! -f "$TARGET" ] || [ "$SOURCE" -nt "$TARGET" ]; then
    cp "$SOURCE" "$TARGET"
```

- При первом деплое скопировал старую версию
- После обновления образа — НЕ копирует (потому что target уже есть и source не "newer" по mtime)
- Volume "застрял" на версии из прошлого деплоя

**Влияние:**
- Hermes использует старую/другую SOUL.md, не ту что в образе
- Любые правки SOUL.md в коде **не доходят** до runtime
- md5 разные, описания архитектуры кардинально отличаются (v4 — про 3-проходный цикл; runtime — про "армию AI-агентов")

**Фикс:** либо `rm /opt/data/SOUL.md && docker restart aim-hermes`, либо модифицировать `copy_soul.sh` чтобы всегда копировал.

---

### 5. Магистры и субагенты — мёртвый код (152 файла)

**Что есть:**
- `src/aim/magisters/` — 19 файлов (ads_magister + 4 variants, content_magister + 4 variants, seo_magister + 4 variants, analytics_magister + 2 variants, prescan_magister, sales_admin_magister, sales_admin_base, linear_mixin)
- `src/aim/subagents/` — 133 файла (ci-orchestrator с 23 агентами и 16 фазами, sales, ads, content, seo, analytics)
- `src/aim/orchestration/` — 3 файла (hermes_orchestrator, knowledge_bridge, shared_event_bus)
- `src/aim/integration/` — 2 файла (ci_magisters_integration, hermes_context)
- `src/aim/agents/ci_swarm/` — swarm логика

**Реальное использование:**
```bash
$ grep -rE "from src.aim.magisters|from src.aim.subagents" /opt/aim/AIM/hermes/
(empty — ни одного импорта в Hermes)

$ grep -rE "BaseMagister|magister" /opt/aim/AIM/src/aim/api/*.py
(empty — ни в одном endpoint)
```

В `aim-app/main.py`:
```python
# only one magister referenced, in try/except:
try:
    from src.aim.magisters.sales_admin_magister import SalesAdminMagister
    sales_magister = SalesAdminMagister(event_bus=event_bus)
    await sales_magister.start(event_bus)
except Exception as e:
    logger.error("sales_admin_magister_failed", error=str(e))
    # continues anyway
```

**Влияние:**
- 152 файла мёртвого кода в проекте (~3 MB)
- Любые правки в этих файлах не имеют эффекта
- Запутывает новых разработчиков
- CLAUDE.md явно говорит: "Магистры deprecated, CI Orchestrator (23 агента, 16 фаз) заменён прямым вызовом инструментов"

**Фикс:** удалить директории `magisters/`, `subagents/`, `orchestration/`, `integration/`, `agents/ci_swarm/`. Сохранить только `sales_admin_magister.py` если он реально используется (или удалить его тоже, раз он в try/except).

---

### 6. EventBus формально работает, но не используется

**Технически:**
- Таблицы `event_bus_events` и `event_bus_messages` созданы в PostgreSQL
- Endpoint `/ready` показывает `"event_bus": true`
- В main.py инициализируется в lifespan

**Реально:**
- За всё время в `event_bus_messages` — **4 строки**
- В `event_bus_events` — 0 строк
- Импортируется только в `api/content.py`, `api/seo.py` (для CI orchestrator, который не вызывается)

**Влияние:**
- Архитектура event-driven формальна, но не используется
- 2 пустые таблицы в БД + код в `src/aim/orchestration/shared_event_bus.py`

---

### 7. Баг в `session_archive.py` — leading dot в filenames

**Логи за 24h показывают mass errors:**
```
[ERROR] session_archive: failed to save cc5919a8-d58/PERPLEXITY/perplexity_search.json:
  No such file or directory:
  '/opt/data/sessions-archive/cc5919a8-d58/data/.PERPLEXITY/perplexity_search_j9s34cea.json'

[ERROR] session_archive: failed to save cc5919a8-d58/COMPETITORS/find_competitors.json:
  No such file or directory:
  '/opt/data/sessions-archive/cc5919a8-d58/data/.COMPETITORS/find_competitors_0dephx59.json'
```

(повторяется для всех 14 фаз)

**Причина (по коду):**
```python
# session_archive.py:52-54
safe_key = key.replace("/", "_").replace(" ", "_")
fd, tmp_path = tempfile.mkstemp(
    suffix=".json", prefix=f".{safe_key}_", dir=str(data_dir)
)
```

`tempfile.mkstemp` создаёт hidden file (с leading dot). Дальше `os.rename()` пытается переименовать в `{key}.json`, но `key` содержит `/` (например `"PERPLEXITY/perplexity_search"`), и parent директория `.PERPLEXITY` не существует.

**Влияние:**
- Данные фаз scouts не сохраняются в архив
- Каждая фаза логирует ошибку
- Клиент может не получить полный отчёт

**Фикс:** в `save_tool_output()` создавать `parent_dir` для key перед mkstemp:
```python
key_dir = data_dir / safe_key.rsplit("/", 1)[0] if "/" in safe_key else data_dir
key_dir.mkdir(parents=True, exist_ok=True)
```

---

### 8. Docker images экспонируют sensitive порты наружу

| Контейнер | Port | Bind | Проблема |
|---|---|---|---|
| `aim-redis` | 6379 | `0.0.0.0:6379` | ⚠️ Redis exposed to internet |
| `aim-prometheus` | 9090 | `0.0.0.0:9090` | ⚠️ Metrics exposed |
| `aim-grafana` | 3000 | `0.0.0.0:3000` | ⚠️ Dashboard exposed (default admin/admin?) |
| `aim-postgres` | 5432 | `127.0.0.1:5432` ✅ | OK |
| `aim-alertmanager` | 9093 | `127.0.0.1:9093` ✅ | OK |

**Влияние:**
- Redis без пароля доступен всем → любой может читать/писать в cache
- Prometheus показывает все метрики без auth
- Grafana если дефолтные креды — полный доступ к monitoring

**Фикс:** в `docker-compose.yml` изменить `ports:` для production на `127.0.0.1:PORT:PORT` или вообще убрать (использовать только internal network).

---

## 🟢 NIT — мелкие проблемы

### 9. WordPress volume содержит `node_modules` (15.7 MB)

`/var/www/html/wp-content/themes/aim-theme/node_modules/` — 15.7 MB npm packages в Docker volume. Должен быть только build-time (в Dockerfile), а в volume попадать только готовый bundle (`chat/dist/chat-bundle.*`).

**Фикс:** добавить `node_modules` в `.dockerignore` или переместить build в Dockerfile.

---

### 10. Backup-файлы не очищаются

| Файл | Локация | Размер |
|---|---|---|
| `main.py.backup-phase09-20260628-075019` | hermes/app/ | ~30 KB |
| `main.py.backup-phase09-20260628-075030` | hermes/app/ | ~30 KB |
| `agent_wrapper.py.bak` | hermes/app/ | ~30 KB |
| `chat-inline.php.backup-1781386127` | aim-theme/ | — |
| `chat-inline.php.backup-before-pro` | aim-theme/ | — |
| `chat-inline.php.backup-1781787857` | aim-theme/ | — |
| `hermes-chat.html.bak` | aim-theme/chat/ | — |
| `functions.php.bak` | aim-theme/ | — |
| `docker-compose.yml.bak` | AIM/ | — |
| `docker-compose.headroom-deepseek.yml.backup` | AIM/ | — |
| `SESSION.md.bak` | AIM/ | — |
| `ROADMAP.md.bak` | AIM/ | — |
| `.env.production.bak-20260617-150905` | AIM/ | — |
| `apify_keys.json.bak` | AIM/data/ | — |
| `SOUL.backup.md` | hermes/skills/aim/ | — |

**Фикс:** внедрить правило "backups только в git history". Все `*.bak` удалить, при необходимости — `git log` для восстановления.

---

### 11. Дубликат meai framework

```
/opt/aim/src/meai        868 KB
/opt/aim/AIM/src/meai    820 KB
```

Структура идентична (`agents`, `core`, `events`, `integrations`, `knowledge`, `learning`, `memory`, `models`, `reports`, `storage`, `tracking`).

В Docker образе `aim-app` монтируется только один из них (`PYTHONPATH=/app/AIM:/app:/app/src`).

**Фикс:** удалить `/opt/aim/src/meai` (или `/opt/aim/AIM/src/meai` — проверить какой в PYTHONPATH).

---

### 12. `/opt/data/bin/tirith` — бинарник неизвестного назначения

```
$ ls -la /opt/data/bin
-rwxr-xr-x tirith  22 MB  Jun 19 05:56
```

В `aim_hermes_data` volume, в корне `/opt/data/bin/`. Имя "tirith" отсылает к "Minas Tirith" (LOTR) — может быть tool из 3rd party.

**Фикс:** выяснить происхождение (по дате 19 июня — после деплоя), удалить если не используется.

---

### 13. `aim-paperclip` — 2.76 GB образ без документации

- Контейнер `aim-paperclip` запущен 37 часов
- Образ `paperclip-paperclip:latest` 2.76 GB
- Entrypoint: `docker-entrypoint.sh`
- Cmd: `paperclipai run`
- WorkDir: `/home/paperclip`
- В Nginx — отдельный default_server на порту 80 для IP-based доступа

Логи:
```
[INFO]: GET /health 200
[WARN]: GET /metrics 403
[WARN]: GET / 403
```

В CLAUDE.md не описан.

**Фикс:** задокументировать или удалить. Занимает место и CPU.

---

### 14. Дублирующие compose файлы

```
/opt/aim/AIM/docker-compose.yml           (367 строк, главный)
/opt/aim/AIM/docker-compose.zai.yml       (731 B, Z.AI вариант)
/opt/aim/docker-compose.headroom.yml      (HeadroomGuard, не активен)
/opt/aim/hermes-temp/docker-compose.yml   (временный)
```

**Фикс:** оставить только главный, остальные — в git history или отдельную `compose-examples/` папку.

---

### 15. Persistent volume содержит `__pycache__` и тестовые БД

```
/opt/data/  содержит:
  skills/  memories/  proposals/  sessions/  state.db  ← нужное
  bin/tirith (22 MB)  ← не нужное
```

```
/opt/aim/AIM/data/:
  test_init.db, test_ads_agent.db, test_content_writer.db,
  test_complete_system.db, test_seo_real.db   ← тестовые SQLite
  ci-prioritizer.json, ci-content.json, ci-*.json  ← cached CI результаты
  apify_keys.json, apify_keys.json.bak, apify_keys.txt   ← 3 копии ключей
```

**Фикс:** почистить, оставить только production-relevant файлы.

---

## Сводка по severity

| Severity | Кол-во | Что блокирует |
|---|---:|---|
| 🔴 BLOCKING | 3 | Backend БД, Phase 09, документация врёт |
| 🟡 IMPORTANT | 5 | SOUL sync, zombie код, EventBus, session_archive баг, exposed ports |
| 🟢 NIT | 7 | Cleanup, дубликаты, документация |

---

## Зависимости фиксов

```
Фикс #1 (PostgreSQL auth)  →  разблокирует endpoints leads/sales/onboarding
Фикс #4 (SOUL.md sync)     →  прежде чем править SOUL.md в коде
Фикс #2 (Phase 09 deploy)  →  после проверки что main.py backup-файлы нужно деплоить
Фикс #5 (Удаление магистров) →  после подтверждения что sales_admin_magister не используется
Фикс #7 (session_archive)  →  независимо, баг независимый
```

---

*Все находки основаны на прямых измерениях 30.06.2026. Описание фиксов — рекомендации, не инструкции к исполнению.*
