# 09 — Refactor Roadmap

Дорожная карта рефакторинга AIM. 5 фаз, каждая ~1-2 дня работы.

---

## 📅 Общая структура

| Фаза | Длительность | Риск | Цель |
|---|---|---|---|
| **A. Stabilization** | 1 день | 🟢 низкий | Починить критические баги, ничего не ломая |
| **B. Documentation sync** | 1 день | 🟢 низкий | Привести в порядок CLAUDE.md, SESSION.md, .current-task |
| **C. Cleanup Phase 1** | 1 день | 🟡 средний | Удалить очевидный мусор (backups, logs, venv) |
| **D. Cleanup Phase 2** | 2-3 дня | 🟠 высокий | Удалить deprecated код (magisters, subagents, pipeline) |
| **E. Architecture simplification** | 2-3 дня | 🟠 высокий | Уйти от PostgreSQL к SQLite (или починить PG auth) |

**Итого:** 7-10 рабочих дней.

---

## 🟢 Фаза A: Stabilization (ДЕНЬ 1)

**Цель:** исправить критические баги без удаления кода. Production должен работать стабильно.

### A.1 Починить PostgreSQL auth

**Проблема:** `InvalidPasswordError for user "aim_user"`

**Диагностика:**
```bash
# 1. Узнать текущий пароль в volume (можно только reset)
docker exec aim-postgres cat /var/lib/postgresql/data/pg_hba.conf | head -20

# 2. Узнать пароль в .env.production
grep POSTGRES_PASSWORD /opt/aim/AIM/.env.production

# 3. Проверить, может ли aim_user подключиться с паролем из .env
docker exec aim-postgres psql -U aim_user -d aim_db -c "SELECT 1"
```

**Решение (вариант 1 — изменить пароль в PostgreSQL под .env):**
```bash
docker exec aim-postgres psql -U aim_user -d aim_db <<EOF
ALTER USER aim_user WITH PASSWORD 'NEW_PASSWORD_FROM_ENV';
EOF
```

**Решение (вариант 2 — пересоздать volume с нуля):**
```bash
# ⚠️ ПОТЕРЯ ДАННЫХ (но они и так пустые)
docker-compose down postgres
docker volume rm aim_postgres_data
docker-compose up -d postgres
```

**Проверка:**
```bash
docker exec aim-app curl -s http://localhost:8000/ready
# должно вернуть: {"status":"ready","checks":{"database":true,...}}
```

---

### A.2 Решить вопрос с SOUL.md

**Проблема:** образ (47 KB) ≠ volume (106 KB).

**Решение:**
1. **Решить, какая версия canonical** (вероятно — volume, 106 KB, более свежая по смыслу)
2. Скопировать volume версию в git:
   ```bash
   ssh aim 'docker exec aim-hermes cat /opt/data/SOUL.md' > AIM/hermes/skills/aim/SOUL.md
   ```
3. Закоммитить
4. Исправить `copy_soul.sh`:
   ```bash
   # Always copy, без условия "if newer"
   cp "$SOURCE" "$TARGET"
   ```
5. Пересобрать образ и перезапустить:
   ```bash
   cd /opt/aim/AIM
   docker-compose build hermes
   docker-compose up -d hermes
   ```
6. Проверить:
   ```bash
   docker exec aim-hermes md5sum /opt/hermes/skills/aim/SOUL.md /opt/data/SOUL.md
   # должно совпасть
   ```

---

### A.3 Починить session_archive баг

**Проблема:** leading dot в filenames, parent dir не создаётся.

**Файл:** `AIM/hermes/app/tools/session_archive.py:43-64`

**Текущий код:**
```python
def save_tool_output(session_id, key, value):
    data_dir = _data_dir(session_id)
    data_dir.mkdir(parents=True, exist_ok=True)
    filepath = data_dir / f"{key}.json"
    filepath.parent.mkdir(parents=True, exist_ok=True)  # создаёт data/.PERPLEXITY/

    safe_key = key.replace("/", "_").replace(" ", "_")  # но key уже использован выше!
    fd, tmp_path = tempfile.mkstemp(suffix=".json", prefix=f".{safe_key}_", dir=str(data_dir))
    # ^ tmp файл в data/, с leading dot
    ...
    os.rename(tmp_path, str(filepath))  # пытается переименовать в data/PERPLEXITY/file.json
    # но путь содержит слэш, parent не существует → fail
```

**Исправление:**
```python
def save_tool_output(session_id, key, value):
    data_dir = _data_dir(session_id)
    data_dir.mkdir(parents=True, exist_ok=True)

    # Сначала sanitize key
    safe_key = key.replace("/", "_").replace(" ", "_")
    filepath = data_dir / f"{safe_key}.json"
    filepath.parent.mkdir(parents=True, exist_ok=True)  # теперь parent это всегда data_dir

    # tempfile БЕЗ leading dot в prefix
    fd, tmp_path = tempfile.mkstemp(suffix=".json", prefix=f"{safe_key}_", dir=str(data_dir))
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2, default=str)

    os.rename(tmp_path, str(filepath))
    return str(filepath)
```

**Проверка:**
```bash
docker-compose restart hermes
# Запустить scout pipeline, убедиться что нет ошибок в логах
docker logs aim-hermes --tail 50 | grep "session_archive"
```

---

### A.4 Приватные порты

**Проблема:** Redis (6379), Prometheus (9090), Grafana (3000) экспонированы на 0.0.0.0.

**Решение:** в `docker-compose.yml` изменить:
```yaml
# Было:
redis:
  ports:
    - "6379:6379"

# Стало:
redis:
  ports:
    - "127.0.0.1:6379:6379"
```

Аналогично для prometheus и grafana.

**Проверка:**
```bash
docker-compose up -d redis prometheus grafana
curl http://aim:6379  # должно быть connection refused снаружи, OK с localhost
```

---

### A.5 Закрыть Docker image vulnerabilities

**Проверка на sensitive данные в образах:**
```bash
docker history aim-hermes:latest --no-trunc | grep -iE "(KEY|TOKEN|PASSWORD|SECRET)"
```

Если найдено — пересобрать с `--build-arg` или multi-stage build.

---

### A.6 Smoke test после Phase A

```bash
# 1. Сайт доступен
curl -sI https://iamaim.ru/ | head -1
# → HTTP/2 200

# 2. Чат отвечает
curl -s -X POST https://iamaim.ru/api/chat \
  -H "Authorization: Bearer $HERMES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message":"тест"}'
# → JSON с reply

# 3. aim-app ready
docker exec aim-app curl -s http://localhost:8000/ready | python -m json.tool
# → {"status":"ready","checks":{"database":true,"redis":true,"event_bus":true}}

# 4. Hermes health
docker exec aim-hermes curl -s http://localhost:8000/health
# → {"status":"healthy",...}
```

---

## 🟢 Фаза B: Documentation Sync (ДЕНЬ 2)

**Цель:** привести документы в соответствие с реальностью.

### B.1 Обновить `.current-task`

**Сейчас:** "Phase 09 deployed. Test hermes-chat-pro.html" (false)

**Цель (пример):** "PostgreSQL auth fixed. Phase A complete. Next: Phase B documentation sync"

---

### B.2 Переписать SESSION.md

**Удалить:**
- Секцию "Phase 09 Deployed" — не задеплоено
- Секцию "HeadroomGuard integration plan" — не активна
- "Текущая конфигурация production" с headroom

**Добавить:**
- Текущий статус: "Phase A (stabilization) complete"
- Реальная конфигурация: DeepSeek direct, 67 tools, SQLite state
- Что работает: chat pipeline, monitoring, Telegram bot
- Что не работает: backend CRM (leads/sales/onboarding) — не используется активно

---

### B.3 Обновить CLAUDE.md

**Изменить:**
- "16 контейнеров" (с paperclip)
- "67 tools" (вместо 17)
- Убрать секцию "Hermes Backup" (удалена в коммите 017acba)
- Заменить "Что НЕ использовать" на "Что УДАЛИТЬ" со ссылкой на refactor-analysis
- Добавить секцию про `aim-paperclip` (когда выяснится что это)

**Проверить и обновить:**
- Секцию Tools — полный список 67 шт
- Секцию Architecture — актуальная схема

---

### B.4 Зафиксировать refactor-analysis в git

```bash
cd /Users/mikhaileliseev/Desktop/Dev/meAI_1
git add refactor-analysis/
git commit -m "docs: add refactor-analysis snapshot (10 files)"
```

---

## 🟡 Фаза C: Cleanup Phase 1 (ДЕНЬ 3)

**Цель:** удалить очевидный мусор. Низкий риск.

### C.1 Backup-файлы

```bash
# Find all
find /opt/aim -maxdepth 5 \( -name "*.bak" -o -name "*.backup" -o -name "*.backup-*" \) -type f

# Verify count
find /opt/aim -maxdepth 5 \( -name "*.bak" -o -name "*.backup" -o -name "*.backup-*" \) -type f | wc -l

# Delete
find /opt/aim -maxdepth 5 \( -name "*.bak" -o -name "*.backup" -o -name "*.backup-*" \) -type f -delete
```

**Проверка:** сайт работает, чат отвечает.

---

### C.2 Логи без ротации

```bash
# Текущие размеры
du -sh /opt/aim/AIM/logs/*

# Truncate app.log (не удалять — приложение пишет)
truncate -s 0 /opt/aim/AIM/logs/app.log

# Удалить старые nginx logs
find /opt/aim/AIM/logs/nginx -type f -mtime +7 -delete
```

**Настроить logrotate:**
```bash
cat > /etc/logrotate.d/aim <<EOF
/opt/aim/AIM/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
EOF
```

---

### C.3 Dev artifacts

```bash
# .venv (236 MB)
rm -rf /opt/aim/AIM/.venv

# .cache, .pytest_cache, .local, .superflow, .playwright-mcp
rm -rf /opt/aim/AIM/.cache
rm -rf /opt/aim/AIM/.pytest_cache
rm -rf /opt/aim/AIM/.local
rm -rf /opt/aim/AIM/.superflow
rm -rf /opt/aim/AIM/.playwright-mcp
rm -rf /opt/aim/AIM/.backups

# Тестовые SQLite БД
rm /opt/aim/AIM/data/test_*.db

# CI cached results (если не нужны для regression)
mkdir -p /opt/aim/AIM/data/_archived
mv /opt/aim/AIM/data/ci-*.json /opt/aim/AIM/data/ci-deep /opt/aim/AIM/data/ci-tech /opt/aim/AIM/data/_archived/

# ChatExport
mv /opt/data/ChatExport_2026-06-18.zip /opt/aim/AIM/data/_archived/
```

---

### C.4 Дубликаты framework

**Проверить, какой meai используется:**
```bash
docker exec aim-app python -c "import meai; print(meai.__file__)"
# → /app/src/meai/__init__.py
```

PYTHONPATH в docker-compose: `/app/AIM:/app:/app/src`. Используется `/opt/aim/AIM/src/meai`.

**Удалить дубль:**
```bash
rm -rf /opt/aim/src/meai
rm -rf /opt/aim/src/meai.egg-info
```

---

### C.5 WordPress theme node_modules

```bash
# В Docker volume
docker exec aim-wordpress rm -rf /var/www/html/wp-content/themes/aim-theme/node_modules
```

**В `wordpress-core/.dockerignore` добавить:**
```
**/node_modules
```

---

### C.6 Старые backups

```bash
# Hermes backups
ls /opt/hermes-backup-20260618-000755/  # проверить что есть на сервере (внешняя директория)
ls /opt/hermes-archive/

# Удалить старше 30 дней
find /opt -maxdepth 2 -name "hermes-backup-*" -mtime +30 -exec rm -rf {} \;
find /opt -maxdepth 2 -name "*-backup-*" -mtime +30 -exec rm -rf {} \;
```

---

### C.7 Smoke test после Phase C

```bash
# Сайт + чат + Hermes работают
curl -sI https://iamaim.ru/ | head -1
docker exec aim-hermes curl -s http://localhost:8000/health
docker exec aim-app curl -s http://localhost:8000/health
docker exec aim-wordpress wp --version  # если wp-cli есть
```

---

## 🟠 Фаза D: Cleanup Phase 2 — DEPRECATED CODE (ДНИ 4-6)

**Цель:** удалить deprecated magisters, subagents, pipeline v7. Высокий риск.

### D.1 Подготовка: backup

```bash
# Backup Docker volumes перед удалением кода
docker run --rm -v aim_hermes_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/hermes_data_$(date +%Y%m%d).tar.gz /data

docker run --rm -v aim_wp_content:/data -v $(pwd):/backup alpine \
  tar czf /backup/wp_content_$(date +%Y%m%d).tar.gz /data

# Git tag
git tag pre-cleanup-phase-d
git push --tags
```

---

### D.2 Удалить Magisters

```bash
# Сначала убедиться что не используется
grep -rE "from src.aim.magisters|from .magisters" /opt/aim/AIM/hermes/ /opt/aim/AIM/src/aim/api/
# Должно быть пусто (или только sales_admin_magister в main.py)

# Удалить всю директорию
rm -rf /opt/aim/AIM/src/aim/magisters/

# Если sales_admin_magister нужен — выделить в отдельный мини-сервис
```

**В main.py убрать:**
```python
# Убрать блок try/except с SalesAdminMagister (98-117 строки)
```

---

### D.3 Удалить Subagents

```bash
# Проверить что не импортируется
grep -rE "from src.aim.subagents|from .subagents" /opt/aim/AIM/hermes/ /opt/aim/AIM/src/aim/main.py
# Только 3 endpoints используют subagents

# Решить: либо оставить эти 3 endpoints без subagents (заглушки), либо переписать
# Затем:
rm -rf /opt/aim/AIM/src/aim/subagents/
```

**Альтернатива:** не удалять subagents полностью, а только `competitive_intel/` (CI orchestrator с 23 агентами).

---

### D.4 Удалить EventBus

```bash
# Удалить код
rm /opt/aim/AIM/src/aim/orchestration/shared_event_bus.py

# Удалить usage в main.py (lifespan init)
# Удалить usage в api/content.py, api/seo.py

# Опционально — удалить таблицы
docker exec aim-postgres psql -U aim_user -d aim_db -c "DROP TABLE event_bus_messages, event_bus_events;"
```

---

### D.5 Удалить Hermes pipeline v7

```bash
# Проверить что pipeline engine не вызывается
grep -rE "from .pipeline|from app.pipeline" /opt/aim/AIM/hermes/app/

# Удалить
rm -rf /opt/aim/AIM/hermes/app/pipeline/

# Удалить config секцию pipeline из config.yaml
```

---

### D.6 Удалить Hermes legacy

```bash
rm /opt/aim/AIM/hermes/app/omniroute_direct.py
rm -rf /opt/aim/AIM/hermes/_archive/
rm -rf /opt/aim/AIM/hermes/knowledge/
# mcp-proxy — проверить, нужен ли
# patches — проверить
```

---

### D.7 Удалить Obsidian vaults

```bash
# Оставить только architect (если есть) и teacher (если используется)
# Удалить все ci-*, magister vaults
rm -rf /opt/aim/AIM/obsidian/ads-magister
rm -rf /opt/aim/AIM/obsidian/analytics-magister
rm -rf /opt/aim/AIM/obsidian/content-magister
rm -rf /opt/aim/AIM/obsidian/seo-magister
rm -rf /opt/aim/AIM/obsidian/seo-magister-1
rm -rf /opt/aim/AIM/obsidian/social-magister
rm -rf /opt/aim/AIM/obsidian/ai-magister
rm -rf /opt/aim/AIM/obsidian/email-magister
rm -rf /opt/aim/AIM/obsidian/intelligence-magister
rm -rf /opt/aim/AIM/obsidian/magisters
rm -rf /opt/aim/AIM/obsidian/ci-*  # все CI vaults
rm -rf /opt/aim/AIM/obsidian/test-agent
# Оставить: architect, teacher, operator, deep-research
```

---

### D.8 Удалить .planning

```bash
rm -rf /opt/aim/AIM/.planning
```

---

### D.9 Удалить локальный frontend (если есть Docker образ)

```bash
# Проверить что Docker образ не зависит от локальной директории
grep -E "context|dockerfile" /opt/aim/AIM/docker-compose.yml | head -10
# Если build context: ./frontend — НЕ удалять
# Если только image: aim-frontend:latest — можно удалить

# Если можно удалить:
rm -rf /opt/aim/AIM/frontend
```

---

### D.10 Пересборка и smoke test

```bash
cd /opt/aim/AIM
docker-compose build --no-cache hermes app
docker-compose up -d

# Smoke tests
curl -sI https://iamaim.ru/ | head -1
curl -s -X POST https://iamaim.ru/api/chat -H "Authorization: Bearer $HERMES_API_KEY" -H "Content-Type: application/json" -d '{"message":"тест"}'
docker exec aim-hermes curl -s http://localhost:8000/health
docker exec aim-app curl -s http://localhost:8000/ready
```

**Откат если что-то сломалось:**
```bash
git checkout pre-cleanup-phase-d -- .
docker-compose build --no-cache
docker-compose up -d
```

---

## 🟠 Фаза E: Architecture Simplification (ДНИ 7-10)

**Цель:** упростить архитектуру. Самый высокий риск.

### E.1 Решить: PostgreSQL или SQLite

**Вопрос для владельца продукта (см. 10-DECISIONS-NEEDED.md #1):**
- Ожидаемый рост负载?
- Используется ли backend CRM (leads/sales/onboarding) в реальности?

**Если SQLite:**
- Перенести нужные таблицы в SQLite в `/opt/data/aim.db`
- Удалить PostgreSQL контейнер
- Удалить postgres-exporter
- Сэкономить ~400 MB RAM, упростить стек

**Если PostgreSQL:**
- Починить auth (Phase A.1)
- Удалить неиспользуемые таблицы (event_bus_*)
- Убрать exposes

---

### E.2 Решить: aim-frontend (Next.js) нужен?

**Вопрос #2:** `/chat-test`, `/chat-old`, `/chat-new` используются?

**Если нет:**
- Остановить контейнер aim-frontend
- Удалить из docker-compose
- Убрать nginx routes на /chat-test, /chat-old, /chat-new, /_next/

**Если да:**
- Оставить как есть

---

### E.3 Решить: aim-paperclip

**Вопрос #3:** что делает этот контейнер 2.76 GB?

**Если не используется:** остановить, удалить образ, убрать nginx default_server на него.

**Если используется:** задокументировать.

---

### E.4 Упростить docker-compose

Объединить `docker-compose.yml`, `docker-compose.zai.yml`, `docker-compose.headroom.yml` в один canonical.

Удалить deprecated options, добавить healthcheck для всех сервисов.

---

### E.5 Финальная проверка

```bash
# Полный audit после рефакторинга
docker ps -a
docker images
docker volume ls
df -h /

# Smoke tests все endpoints
for endpoint in /api/leads /api/analytics/realtime /api/onboarding/start /api/sales/pipeline; do
  curl -s -o /dev/null -w "%{http_code} $endpoint\n" https://iamaim.ru$endpoint
done

# Проверить что documents нет
find /opt/aim -maxdepth 5 \( -name "*.bak" -o -name "*.backup*" \) -type f
# должно быть 0

# Проверить что magisters/subagents удалены
ls /opt/aim/AIM/src/aim/magisters 2>&1
ls /opt/aim/AIM/src/aim/subagents 2>&1
# оба должны вернуть "No such file or directory"
```

---

## 🎯 Метрики успеха после рефакторинга

| Метрика | До | После Phase A-E |
|---|---|---|
| Контейнеры | 16 | 10-12 |
| Образы (размер) | 13.1 GB | 6-8 GB |
| .bak файлов | 15+ | 0 |
| Zombie код | ~3 MB | 0 |
| Python файлов | ~250 | ~100 |
| Markdown в корне | 233 | 5-10 |
| .venv на хосте | 236 MB | 0 |
| Логи без ротации | 87 MB | <10 MB |
| Postgres exposes | 1 (public) | 0 |
| Redis exposes | 1 (public) | 0 |
| Расхождений docs | 15+ | 0 |

---

## 🚨 Что НИКОГДА не делать при рефакторинге

1. ❌ Не удалять Docker volumes без backup
2. ❌ Не удалять `.env.production` без проверки что есть копия
3. ❌ Не удалять `/opt/data/state.db` (потеряем все 32 сессии)
4. ❌ Не удалять `aim_hermes_data` volume целиком
5. ❌ Не деплоить без smoke test после каждой фазы
6. ❌ Не коммитить изменения магистров/subagents без smoke test всех endpoints
7. ❌ Не оставлять незакоммиченных изменений между фазами

---

## 📋 Чек-лист завершения рефакторинга

- [ ] Phase A: PostgreSQL auth починён, /ready возвращает `database: true`
- [ ] Phase A: SOUL.md синхронизирован между образом и volume
- [ ] Phase A: session_archive баг исправлен
- [ ] Phase A: чувствительные порты привязаны к localhost
- [ ] Phase B: `.current-task` обновлён
- [ ] Phase B: SESSION.md переписан
- [ ] Phase B: CLAUDE.md обновлён
- [ ] Phase C: все `*.bak` удалены
- [ ] Phase C: logrotate настроен
- [ ] Phase C: .venv, .planning, dev artifacts удалены
- [ ] Phase C: дубликат meai удалён
- [ ] Phase C: node_modules в theme удалён
- [ ] Phase D: magisters удалены
- [ ] Phase D: subagents удалены
- [ ] Phase D: EventBus удалён
- [ ] Phase D: Hermes pipeline v7 удалён
- [ ] Phase D: Obsidian vaults почищены
- [ ] Phase E: решение по PostgreSQL принято и выполнено
- [ ] Phase E: решение по aim-frontend принято
- [ ] Phase E: решение по aim-paperclip принято
- [ ] Все smoke tests проходят
- [ ] Git тег `post-refactor-YYYYMMDD` создан
- [ ] Финальный отчёт написан

---

*Этот документ — план. Перед началом любой фазы — прочитать соответствующую секцию в `04-BROKEN-COMPONENTS.md` и `05-DEAD-CODE-INVENTORY.md`.*
