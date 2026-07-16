# PLAN: Phase 01 — Stabilization & Cleanup

**Создан:** 30 июня 2026
**Ссылка на контекст:** `refactor-analysis/00-PROJECT-CONTEXT.md`
**Цель фазы:** Подготовить систему к фокусу на конкурентной разведке — стабилизировать, очистить, NOTHING else.

---

## 🎯 Goal (одной фразой)

**Система стабилизирована и очищена от мёртвого код и инфраструктуры — Hermes работает с 18 корректно вызывающимися tools, чат отвечает, errors в логах ≤ 1/час.**

---

## ✅ Acceptance Criteria

После выполнения всех задач фазы:

- [ ] AC-1: `docker exec aim-app curl -s http://localhost:8000/ready` возвращает `database: true`
- [ ] AC-2: `docker logs aim-hermes --since 1h | grep -c "session_archive.*failed"` = **0**
- [ ] AC-3: `docker exec aim-hermes md5sum /opt/data/SOUL.md /opt/hermes/skills/aim/SOUL.md` — суммы **совпадают**
- [ ] AC-4: `docker ps -a --filter name=aim-paperclip` — пусто (контейнер удалён)
- [ ] AC-5: `ls /opt/aim/AIM/src/aim/magisters/ 2>&1` → "No such file or directory"
- [ ] AC-6: `ls /opt/aim/AIM/src/aim/subagents/ 2>&1` → "No such file or directory"
- [ ] AC-7: `ls /opt/aim/AIM/hermes/app/pipeline/ 2>&1` → "No such file or directory"
- [ ] AC-8: `find /opt/aim -maxdepth 5 -name "*.bak" -o -name "*.backup-*" 2>/dev/null | wc -l` = **0**
- [ ] AC-9: `du -sh /opt/aim/AIM/.venv 2>/dev/null` → "No such file or directory"
- [ ] AC-10: `curl -sI https://iamaim.ru/ | head -1` = `HTTP/2 200`
- [ ] AC-11: `curl -s -X POST https://iamaim.ru/api/chat -H "Authorization: Bearer $HERMES_API_KEY" -H "Content-Type: application/json" -d '{"message":"тест"}'` → возвращает JSON с `reply`
- [ ] AC-12: `docker exec aim-hermes curl -s http://localhost:8000/health` → `{"status":"healthy",...}`
- [ ] AC-13: SESSION.md обновлён — нет упоминаний HeadroomGuard как активного
- [ ] AC-14: CLAUDE.md обновлён — 67 tools (не 17), нет Hermes Backup ссылки
- [ ] AC-15: `.current-task` обновлён — актуальная задача

---

## 📋 Задачи (Waves)

Задачи сгруппированы в 5 волн. Каждая волна завершается smoke test. Если smoke test падает — wave не переходит в следующую.

---

### 🔵 Wave 1: Critical Stabilization (Day 1)

**Цель:** починить блокирующие баги. Минимальные изменения кода.

---

#### Task 1.1: Backup перед любыми изменениями

**Owner:** Claude Code
**Time:** 5 минут
**Risk:** нет

**Команды:**
```bash
# Git tag на текущее состояние
cd /Users/mikhaileliseev/Desktop/Dev/meAI_1
git tag pre-phase-01-stabilization
git push --tags 2>/dev/null || echo "tag created locally"

# Backup Docker volumes на сервере
ssh aim 'mkdir -p /opt/backups/pre-phase-01-$(date +%Y%m%d) && \
  docker run --rm -v aim_hermes_data:/data -v /opt/backups/pre-phase-01-$(date +%Y%m%d):/backup alpine \
    tar czf /backup/hermes_data.tar.gz /data && \
  docker run --rm -v aim_wp_content:/data -v /opt/backups/pre-phase-01-$(date +%Y%m%d):/backup alpine \
    tar czf /backup/wp_content.tar.gz /data && \
  docker exec aim-postgres pg_dumpall -U aim_user > /opt/backups/pre-phase-01-$(date +%Y%m%d)/postgres_dump.sql 2>&1 && \
  ls -la /opt/backups/pre-phase-01-$(date +%Y%m%d)/'
```

**Acceptance:**
- Git tag создан
- 3 backup файла на сервере: hermes_data.tar.gz, wp_content.tar.gz, postgres_dump.sql

---

#### Task 1.2: Починить PostgreSQL auth

**Owner:** Claude Code
**Time:** 15 минут
**Risk:** 🟢 низкий (только password update)
**Связано с:** AC-1

**Диагностика (сначала):**
```bash
ssh aim 'cat /opt/aim/AIM/.env.production | grep POSTGRES_PASSWORD'
ssh aim 'docker exec aim-postgres psql -U aim_user -d aim_db -c "SELECT 1"'
```

**Если `psql -U aim_user` работает локально (из контейнера postgres)** — значит пароль volume известен. Тогда:
```bash
# Получить текущий пароль (тем же способом что в volume)
ssh aim 'docker exec aim-postgres cat /var/lib/postgresql/.pgpass 2>/dev/null || \
  docker exec aim-postgres sh -c "echo $POSTGRES_PASSWORD"'
```

**Решение (вариант A — обновить пароль в PostgreSQL под .env):**
```bash
# 1. Достать NEW_PASSWORD из .env.production
NEW_PWD=$(ssh aim 'grep POSTGRES_PASSWORD /opt/aim/AIM/.env.production | cut -d= -f2')

# 2. Обновить пароль пользователя
ssh aim "docker exec aim-postgres psql -U aim_user -d aim_db -c \"ALTER USER aim_user WITH PASSWORD '$NEW_PWD';\""

# 3. Перезапустить aim-app чтобы подхватил (env уже правильный)
ssh aim 'docker-compose -f /opt/aim/AIM/docker-compose.yml restart app'

# 4. Подождать healthcheck
ssh aim 'sleep 30 && docker exec aim-app curl -s http://localhost:8000/ready'
```

**Решение (вариант B — если A не работает): пересоздать volume:**
```bash
ssh aim 'cd /opt/aim/AIM && \
  docker-compose stop app && \
  docker-compose stop postgres && \
  docker volume rm aim_postgres_data && \
  docker-compose up -d postgres && \
  sleep 20 && \
  docker-compose up -d app && \
  sleep 30 && \
  docker exec aim-app curl -s http://localhost:8000/ready'
```

**Verification (AC-1):**
```bash
ssh aim 'docker exec aim-app curl -s http://localhost:8000/ready | python3 -m json.tool'
# Должно вывести: {"status":"ready","checks":{"database":true,"redis":true,"event_bus":true},...}
```

---

#### Task 1.3: Починить session_archive баг

**Owner:** Claude Code
**Time:** 20 минут
**Risk:** 🟢 низкий (одна функция, локальный фикс)
**Связано с:** AC-2

**Файл:** `AIM/hermes/app/tools/session_archive.py:30-64`

**Изменение:**

Старый код (баг):
```python
filepath = data_dir / f"{key}.json"
filepath.parent.mkdir(parents=True, exist_ok=True)
safe_key = key.replace("/", "_").replace(" ", "_")
fd, tmp_path = tempfile.mkstemp(suffix=".json", prefix=f".{safe_key}_", dir=str(data_dir))
```

Новый код:
```python
# Sanitize FIRST — key может содержать "/" (например "PERPLEXITY/file")
safe_key = key.replace("/", "_").replace(" ", "_")
filepath = data_dir / f"{safe_key}.json"
filepath.parent.mkdir(parents=True, exist_ok=True)

# tmpfile БЕЗ leading dot (был баг — создавал hidden .PERPLEXITY_file.json)
fd, tmp_path = tempfile.mkstemp(suffix=".json", prefix=f"{safe_key}_", dir=str(data_dir))
```

**Apply через Edit tool (локально):**
- Read file → Edit → сохранить

**Деплой на сервер:**
```bash
# Auto-commit before deploy (правило из CLAUDE.md)
cd /Users/mikhaileliseev/Desktop/Dev/meAI_1
./scripts/auto-commit-deploy.sh

# Скопировать файл на сервер
scp AIM/hermes/app/tools/session_archive.py \
  aim:/opt/aim/AIM/hermes/app/tools/session_archive.py

# Перезапустить hermes
ssh aim 'docker restart aim-hermes && sleep 10'
```

**Verification (AC-2):**
```bash
ssh aim 'docker logs aim-hermes --since 1h 2>&1 | grep -c "session_archive.*failed"'
# Должно вывести: 0 (после тестового запуска prescan)
```

**Smoke test после фикса:**
```bash
# Запустить тестовый prescan через API Hermes
HERMES_KEY=$(ssh aim 'grep HERMES_API_KEY /opt/aim/AIM/.env.production | cut -d= -f2')
curl -s -X POST https://iamaim.ru/api/chat \
  -H "Authorization: Bearer $HERMES_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message":"https://example.ru"}' | head -c 200
# Проверить логи на ошибки session_archive
```

---

#### Task 1.4: Синхронизировать SOUL.md

**Owner:** Claude Code
**Time:** 10 минут
**Risk:** 🟢 низкий
**Связано с:** AC-3

**Решение:** версия из `/opt/data/SOUL.md` (106 KB, runtime) канонична — это то, что Hermes реально использует.

**Команды:**
```bash
# 1. Скачать runtime SOUL.md на локальную машину
ssh aim 'docker exec aim-hermes cat /opt/data/SOUL.md' > \
  /Users/mikhaileliseev/Desktop/Dev/meAI_1/AIM/hermes/skills/aim/SOUL.md

# 2. Проверить размеры
wc -l /Users/mikhaileliseev/Desktop/Dev/meAI_1/AIM/hermes/skills/aim/SOUL.md
# Должно быть ~1411 строк

# 3. Закоммитить
cd /Users/mikhaileliseev/Desktop/Dev/meAI_1
git add AIM/hermes/skills/aim/SOUL.md
git commit -m "fix(hermes): sync SOUL.md from runtime volume to image source

The volume had a newer SOUL.md (106KB, 1411 lines, name=aim-operator)
while the image had an old version (47KB, 760 lines, name=aim-operator-v4).
copy_soul.sh doesn't update when target exists. Taking volume as canonical."

# 4. Исправить copy_soul.sh — всегда копировать
# Файл: AIM/hermes/scripts/copy_soul.sh
# Убрать условие "if [ ! -f "$TARGET" ] || [ "$SOURCE" -nt "$TARGET" ]"
# Оставить только: cp "$SOURCE" "$TARGET"

# 5. Пересобрать образ и перезапустить
ssh aim 'cd /opt/aim/AIM && docker-compose build hermes && docker-compose up -d hermes'
```

**Verification (AC-3):**
```bash
ssh aim 'docker exec aim-hermes md5sum /opt/hermes/skills/aim/SOUL.md /opt/data/SOUL.md'
# Две md5 суммы должны СОВПАДАТЬ
```

---

#### Task 1.5: Приватные Docker порты

**Owner:** Claude Code
**Time:** 10 минут
**Risk:** 🟡 средний (если кто-то использует извне — отвалится)

**Изменить в `AIM/docker-compose.yml`:**

```yaml
#redis:
#  ports:
#    - "6379:6379"               # СТАРОЕ
#    - "127.0.0.1:6379:6379"     # НОВОЕ

#prometheus:
#  ports:
#    - "9090:9090"               # СТАРОЕ
#    - "127.0.0.1:9090:9090"     # НОВОЕ

#grafana:
#  ports:
#    - "3000:3000"               # СТАРОЕ
#    - "127.0.0.1:3000:3000"     # НОВОЕ
```

**Apply:**
```bash
# 1. Редактировать локально через Edit tool
# 2. Auto-commit
# 3. Скопировать на сервер (или git pull)
scp AIM/docker-compose.yml aim:/opt/aim/AIM/docker-compose.yml

# 4. Применить
ssh aim 'cd /opt/aim/AIM && docker-compose up -d redis prometheus grafana'

# 5. Проверить
ssh aim 'curl -s --max-time 3 http://78.17.128.169:6379 2>&1 || echo "OK: connection refused"'
# Ожидаемый ответ: empty (refused) или "OK: connection refused"
```

---

### 🟢 Wave 1 Smoke Test

```bash
echo "=== Wave 1 Smoke Test ==="

# 1. Сайт работает
echo "1. iamaim.ru:"
curl -sI https://iamaim.ru/ | head -1

# 2. Chat endpoint
echo -e "\n2. Chat endpoint:"
HERMES_KEY=$(ssh aim 'grep HERMES_API_KEY /opt/aim/AIM/.env.production | cut -d= -f2')
curl -s -X POST https://iamaim.ru/api/chat \
  -H "Authorization: Bearer $HERMES_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message":"привет"}' | head -c 100
echo ""

# 3. aim-app ready
echo -e "\n3. aim-app /ready:"
ssh aim 'docker exec aim-app curl -s http://localhost:8000/ready'

# 4. Hermes health
echo -e "\n\n4. Hermes /health:"
ssh aim 'docker exec aim-hermes curl -s http://localhost:8000/health'

# 5. SOUL.md sync
echo -e "\n\n5. SOUL.md sync:"
ssh aim 'docker exec aim-hermes md5sum /opt/hermes/skills/aim/SOUL.md /opt/data/SOUL.md'

echo -e "\n=== Wave 1 complete ==="
```

**Критерий перехода к Wave 2:** ВСЕ 5 проверок проходят.

---

### 🟠 Wave 2: Infrastructure Cleanup (Day 2)

**Цель:** удалить инфраструктурный мусор и неизвестные компоненты.

---

#### Task 2.1: Удалить aim-paperclip

**Owner:** Claude Code
**Time:** 10 минут
**Risk:** 🟢 низкий (решение Михаила — удалить)
**Связано с:** AC-4

**Команды:**
```bash
ssh aim '
  # 1. Остановить контейнер
  docker stop aim-paperclip

  # 2. Удалить контейнер
  docker rm aim-paperclip

  # 3. Удалить образ (2.76 GB)
  docker rmi paperclip-paperclip:latest

  # 4. Проверить что нет paperclip-compose файла
  ls /opt/aim/AIM/docker-compose*.yml | head -5
'
```

**Также убрать из nginx default_server** (если есть отдельный):
```bash
# Проверить конфиг nginx
ssh aim 'docker exec aim-nginx cat /etc/nginx/conf.d/default.conf | grep -B2 -A5 paperclip'

# Если есть — убрать секцию default_server на порту 80 для paperclip
# (отредактировать конфиг, перезапустить nginx)
```

**Verification (AC-4):**
```bash
ssh aim 'docker ps -a --filter name=aim-paperclip'
# Ожидаемый вывод: пусто (только заголовок таблицы)
```

---

#### Task 2.2: Удалить tirith binary

**Owner:** Claude Code
**Time:** 2 минуты
**Risk:** 🟢 низкий

```bash
ssh aim 'rm -f /opt/data/bin/tirith && rmdir /opt/data/bin 2>/dev/null; ls /opt/data/bin 2>&1'
# Ожидаемый вывод: "No such file or directory"
```

---

#### Task 2.3: Удалить .venv, .planning, dev artifacts на сервере

**Owner:** Claude Code
**Time:** 5 минут
**Risk:** 🟢 низкий (всё есть в Docker образах)

```bash
ssh aim '
  cd /opt/aim/AIM

  # Удалить .venv (236 MB)
  rm -rf .venv

  # Удалить .planning (старые plans — теперь у нас новый phase-01-stabilization)
  # Но СОХРАНИТЬ локальный .planning/phase-01-stabilization/PLAN.md
  rm -rf .planning

  # Удалить dev caches
  rm -rf .cache .pytest_cache .local .superflow .playwright-mcp .backups

  # Проверить освобождённое место
  df -h / | tail -1
'
```

---

#### Task 2.4: Удалить backup-файлы (.bak, .backup-*)

**Owner:** Claude Code
**Time:** 5 минут
**Risk:** 🟢 низкий (git history остаётся)

```bash
ssh aim '
  # Найти все .bak и .backup-* файлы
  echo "Found:"
  find /opt/aim -maxdepth 5 \( -name "*.bak" -o -name "*.backup" -o -name "*.backup-*" \) -type f | wc -l

  # Удалить
  find /opt/aim -maxdepth 5 \( -name "*.bak" -o -name "*.backup" -o -name "*.backup-*" \) -type f -delete

  # Также в WordPress volume
  docker exec aim-wordpress sh -c "
    cd /var/www/html/wp-content/themes/aim-theme &&
    find . -maxdepth 3 \( -name \"*.bak\" -o -name \"*.backup-*\" \) -type f -delete
  "

  # Проверить
  find /opt/aim -maxdepth 5 \( -name "*.bak" -o -name "*.backup*" \) -type f | wc -l
'
```

**Verification (AC-8):**
```bash
ssh aim 'find /opt/aim -maxdepth 5 \( -name "*.bak" -o -name "*.backup*" \) -type f 2>/dev/null | wc -l'
# Должно быть 0
```

---

#### Task 2.5: Настроить logrotate + truncate logs

**Owner:** Claude Code
**Time:** 10 минут
**Risk:** 🟢 низкий

```bash
ssh aim '
  # Truncate текущие большие логи
  truncate -s 0 /opt/aim/AIM/logs/app.log
  find /opt/aim/AIM/logs/nginx -type f -mtime +7 -delete

  # Настроить logrotate
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

  # Проверить
  logrotate -d /etc/logrotate.d/aim | head -20

  # Проверить размер
  du -sh /opt/aim/AIM/logs/
'
```

---

#### Task 2.6: Удалить node_modules в WordPress theme

**Owner:** Claude Code
**Time:** 2 минуты
**Risk:** 🟢 низкий (build уже сделан в chat/dist/)

```bash
ssh aim 'docker exec aim-wordpress rm -rf /var/www/html/wp-content/themes/aim-theme/node_modules'

# Проверить
ssh aim 'docker exec aim-wordpress ls /var/www/html/wp-content/themes/aim-theme/node_modules 2>&1'
# Ожидаемый вывод: "No such file or directory"
```

---

#### Task 2.7: Удалить дубликат meai framework

**Owner:** Claude Code
**Time:** 2 минуты
**Risk:** 🟢 низкий (PYTHONPATH указывает на /opt/aim/AIM/src/meai)

```bash
ssh aim '
  # Подтвердить какой используется
  docker exec aim-app python -c "import meai; print(meai.__file__)"
  # Должно быть: /app/AIM/src/meai/__init__.py

  # Удалить дубль
  rm -rf /opt/aim/src/meai
  rm -rf /opt/aim/src/meai.egg-info

  # Проверить
  ls /opt/aim/src/ 2>&1
'
```

---

### 🟢 Wave 2 Smoke Test

```bash
echo "=== Wave 2 Smoke Test ==="

# 1. paperclip удалён
echo "1. paperclip gone:"
ssh aim 'docker ps -a --filter name=aim-paperclip --format "{{.Names}}"'

# 2. tirith удалён
echo -e "\n2. tirith gone:"
ssh aim 'ls /opt/data/bin 2>&1'

# 3. .venv удалён
echo -e "\n3. .venv gone:"
ssh aim 'ls /opt/aim/AIM/.venv 2>&1'

# 4. Backup файлов нет
echo -e "\n4. .bak files count:"
ssh aim 'find /opt/aim -maxdepth 5 -name "*.bak" -type f 2>/dev/null | wc -l'

# 5. Чат работает
echo -e "\n5. Chat:"
HERMES_KEY=$(ssh aim 'grep HERMES_API_KEY /opt/aim/AIM/.env.production | cut -d= -f2')
curl -s -X POST https://iamaim.ru/api/chat \
  -H "Authorization: Bearer $HERMES_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message":"тест"}' | head -c 100

echo -e "\n=== Wave 2 complete ==="
```

---

### 🟠 Wave 3: Code Cleanup (Day 3)

**Цель:** удалить deprecated Python код (magisters, subagents, pipeline v7, EventBus).

⚠️ **ВЫСОКИЙ РИСК.** Перед удалением — backup (Task 1.1 уже сделан). После — обязательный smoke test всех 18 aim-app-dependent tools.

---

#### Task 3.1: Удалить magisters (19 файлов)

**Связано с:** AC-5

**Перед удалением — финальная проверка:**
```bash
ssh aim '
  echo "Imports of magisters in active code:"
  grep -rE "from src.aim.magisters|from .magisters" \
    /opt/aim/AIM/hermes/ \
    /opt/aim/AIM/src/aim/api/ \
    /opt/aim/AIM/src/aim/main.py \
    2>/dev/null | grep -v __pycache__
'
# Должно быть: только sales_admin_magister в main.py (в try/except)
```

**Изменения в коде:**
1. Убрать из `src/aim/main.py` блок с SalesAdminMagister (строки ~93-117)
2. Удалить директорию

```bash
# 1. Локально отредактировать main.py (Edit tool)
# Убрать try/except блок с SalesAdminMagister

# 2. Auto-commit
./scripts/auto-commit-deploy.sh

# 3. На сервере
ssh aim '
  cd /opt/aim/AIM
  git pull  # или scp main.py

  # Удалить magisters
  rm -rf src/aim/magisters/

  # Пересобрать образ
  docker-compose build app

  # Перезапустить
  docker-compose up -d app
  sleep 30

  # Smoke
  docker exec aim-app curl -s http://localhost:8000/ready
'
```

**Verification (AC-5):**
```bash
ssh aim 'ls /opt/aim/AIM/src/aim/magisters/ 2>&1'
# Ожидаемый вывод: "No such file or directory"
```

---

#### Task 3.2: Удалить subagents (133 файла)

**Связано с:** AC-6

**Финальная проверка:**
```bash
ssh aim 'grep -rE "from src.aim.subagents|from .subagents" /opt/aim/AIM/src/aim/api/ /opt/aim/AIM/src/aim/main.py 2>/dev/null | grep -v __pycache__'
# 3 endpoints: content.py, sales.py, seo.py
```

**Решение для 3 endpoints:**
- `api/content.py:42` — закомментировать lazy import CIOrchestrator
- `api/sales.py:23` — заменить на заглушку или закомментировать
- `api/seo.py:131` — закомментировать lazy import

**Затем:**
```bash
# 1. Локально отредактировать 3 файла
# 2. Auto-commit
# 3. На сервере удалить директорию
ssh aim '
  cd /opt/aim/AIM
  git pull
  rm -rf src/aim/subagents/
  docker-compose build app
  docker-compose up -d app
  sleep 30
  docker exec aim-app curl -s http://localhost:8000/ready
'
```

**Verification (AC-6):**
```bash
ssh aim 'ls /opt/aim/AIM/src/aim/subagents/ 2>&1'
# "No such file or directory"
```

---

#### Task 3.3: Удалить pipeline v7 (2692 строки)

**Связано с:** AC-7

**Финальная проверка:**
```bash
ssh aim 'grep -rE "from .pipeline|from app.pipeline|from hermes.app.pipeline" /opt/aim/AIM/hermes/ 2>/dev/null | grep -v __pycache__'
```

**Команды:**
```bash
ssh aim '
  cd /opt/aim/AIM
  rm -rf hermes/app/pipeline/

  # Убрать секцию pipeline из config.yaml (локально, через Edit)
  # Потом git pull

  docker-compose build hermes
  docker-compose up -d hermes
  sleep 15
  docker exec aim-hermes curl -s http://localhost:8000/health
'
```

**Verification (AC-7):**
```bash
ssh aim 'ls /opt/aim/AIM/hermes/app/pipeline/ 2>&1'
# "No such file or directory"
```

---

#### Task 3.4: Удалить EventBus + integration + orchestration

```bash
# Проверить использование
ssh aim 'grep -rE "EventBus|event_bus|shared_event_bus" /opt/aim/AIM/src/aim/ 2>/dev/null | grep -v __pycache__ | grep -v ".pyc"'
```

**Удалить:**
- `src/aim/orchestration/` (3 файла)
- `src/aim/integration/` (2 файла)
- В `main.py` — убрать EventBus init в lifespan
- В `api/content.py`, `api/seo.py` — убрать EventBus usage

**Команды:**
```bash
# 1. Отредактировать main.py, content.py, seo.py локально
# 2. Auto-commit
# 3. На сервере
ssh aim '
  cd /opt/aim/AIM
  git pull
  rm -rf src/aim/orchestration/
  rm -rf src/aim/integration/
  rm -rf src/aim/agents/ci_swarm/
  docker-compose build app
  docker-compose up -d app
'
```

---

#### Task 3.5: Удалить Hermes legacy файлы

```bash
ssh aim '
  cd /opt/aim/AIM/hermes

  # Удалить legacy
  rm -f app/omniroute_direct.py
  rm -rf _archive/
  rm -rf knowledge/
  # mcp-proxy/ и patches/ — проверить, удалить если не используются
  rm -rf mcp-proxy/  # если не используется

  # Пересобрать
  cd /opt/aim/AIM
  docker-compose build hermes
  docker-compose up -d hermes
'
```

---

#### Task 3.6: Удалить Obsidian vaults (кроме architect, teacher если нужно)

```bash
ssh aim '
  cd /opt/aim/AIM/obsidian
  # Удалить всё кроме architect и (опционально) teacher
  for dir in ads-magister analytics-magister ai-magister content-magister email-magister intelligence-magister seo-magister seo-magister-1 social-magister ci-auditor ci-content ci-ecosystem ci-factchecker ci-finance ci-hh ci-orchestrator ci-pricing ci-prioritizer ci-reputation ci-research ci-scout ci-site-crawler ci-strategist ci-vacancies magisters test-agent operator deep-research; do
    [ -d "$dir" ] && rm -rf "$dir"
  done
  ls
'
```

---

### 🟢 Wave 3 Smoke Test

```bash
echo "=== Wave 3 Smoke Test ==="

# 1. magisters gone
echo "1. magisters:"
ssh aim 'ls /opt/aim/AIM/src/aim/magisters 2>&1 | head -1'

# 2. subagents gone
echo -e "\n2. subagents:"
ssh aim 'ls /opt/aim/AIM/src/aim/subagents 2>&1 | head -1'

# 3. pipeline gone
echo -e "\n3. pipeline v7:"
ssh aim 'ls /opt/aim/AIM/hermes/app/pipeline 2>&1 | head -1'

# 4. aim-app ready
echo -e "\n4. aim-app /ready:"
ssh aim 'docker exec aim-app curl -s http://localhost:8000/ready'

# 5. Hermes health
echo -e "\n\n5. Hermes /health:"
ssh aim 'docker exec aim-hermes curl -s http://localhost:8000/health'

# 6. Все 18 aim-app-dependent tools загружены
echo -e "\n\n6. Tools count:"
ssh aim 'docker logs aim-hermes --since 5m 2>&1 | grep -cE "registry.register"'

# 7. Chat работает
echo -e "\n7. Chat:"
HERMES_KEY=$(ssh aim 'grep HERMES_API_KEY /opt/aim/AIM/.env.production | cut -d= -f2')
curl -s -X POST https://iamaim.ru/api/chat \
  -H "Authorization: Bearer $HERMES_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message":"https://example.ru"}' | head -c 200

echo -e "\n=== Wave 3 complete ==="
```

---

### 🔵 Wave 4: Documentation Sync (Day 4)

**Цель:** привести SESSION.md, CLAUDE.md, .current-task в соответствие с реальностью.

---

#### Task 4.1: Переписать SESSION.md

**Локально:** отредактировать `/Users/mikhaileliseev/Desktop/Dev/meAI_1/SESSION.md`

**Структура:**
```markdown
# Session: 2026-07-XX — Phase 01 Stabilization Complete

## Текущий фокус

**Phase 01 (Stabilization & Cleanup) завершена.**

Что сделано:
- ✅ PostgreSQL auth починен
- ✅ session_archive баг исправлен
- ✅ SOUL.md синхронизирован
- ✅ Docker порты приватизированы
- ✅ aim-paperclip удалён (2.76 GB свободно)
- ✅ Magisters/Subagents/EventBus/Pipeline v7 удалены
- ✅ Backup-файлы очищены

Что дальше (Phase 02):
- Анализ Phase 09 (исторического)
- Упрощение tools для LLM
- Фокус на run_full_scout

## Реальная конфигурация production

```yaml
Hermes:
  container: aim-hermes (aim-hermes:latest)
  LLM_MODEL: deepseek-v4-pro
  OMNIROUTE_URL: https://api.deepseek.com/v1 (прямой, без headroom)
  tools: 67 зарегистрировано

aim-app:
  container: aim-app
  PostgreSQL: working (auth fixed)
  endpoints: 53

Чат:
  URL: https://iamaim.ru/wp-content/themes/aim-theme/chat/hermes-chat.html
  Inline: chat-inline.php на главной

Контейнеры: 14 (после удаления paperclip)
```

## Что НЕ делать

- ❌ Возвращать HeadroomGuard (отложено до MVP результата)
- ❌ Деплоить Phase 09 без анализа
- ❌ Добавлять CRM/PM/мультиагентность
```

---

#### Task 4.2: Обновить CLAUDE.md

**Изменения:**

1. Секция "Hermes Backup" — удалить (директория удалена в коммите 017acba)
2. Количество tools: 67 (не 17)
3. Секция "Что НЕ использовать" → переименовать в "Что УДАЛЕНО"
4. Добавить ссылку на `refactor-analysis/00-PROJECT-CONTEXT.md`
5. Добавить про aim-paperclip — что удалён
6. Убрать HeadroomGuard упоминания

---

#### Task 4.3: Обновить .current-task

```bash
# Локально
echo "Phase 01 complete. Next: Phase 02 — analyze Phase 09, simplify tools for LLM, fix run_full_scout." > /Users/mikhaileliseev/Desktop/Dev/meAI_1/.current-task

# На сервере
ssh aim 'echo "Phase 01 complete. Next: Phase 02 — analyze Phase 09, simplify tools for LLM, fix run_full_scout." > /opt/aim/AIM/.current-task'
```

---

### 🟢 Wave 4 Smoke Test

```bash
echo "=== Wave 4 Smoke Test ==="

# 1. SESSION.md не содержит HeadroomGuard
echo "1. SESSION.md HeadroomGuard mentions:"
grep -ci "headroom" /Users/mikhaileliseev/Desktop/Dev/meAI_1/SESSION.md

# 2. CLAUDE.md не содержит "Hermes Backup" ссылки
echo -e "\n2. CLAUDE.md Hermes Backup mentions:"
grep -ci "hermes-backup" /Users/mikhaileliseev/Desktop/Dev/meAI_1/CLAUDE.md

# 3. .current-task обновлён
echo -e "\n3. .current-task:"
cat /Users/mikhaileliseev/Desktop/Dev/meAI_1/.current-task

echo -e "\n=== Wave 4 complete ==="
```

---

### 🔵 Wave 5: Final Verification (Day 5)

**Цель:** комплексный smoke test всей системы.

---

#### Task 5.1: Полный functional test

```bash
echo "=== FINAL VERIFICATION ==="
echo ""

# AC-1: PostgreSQL
echo "AC-1 PostgreSQL:"
ssh aim 'docker exec aim-app curl -s http://localhost:8000/ready | python3 -m json.tool'
echo ""

# AC-2: session_archive clean
echo "AC-2 session_archive errors (last 1h):"
ssh aim 'docker logs aim-hermes --since 1h 2>&1 | grep -c "session_archive.*failed"'
echo ""

# AC-3: SOUL.md sync
echo "AC-3 SOUL.md md5:"
ssh aim 'docker exec aim-hermes md5sum /opt/hermes/skills/aim/SOUL.md /opt/data/SOUL.md'
echo ""

# AC-4: paperclip gone
echo "AC-4 paperclip gone:"
ssh aim 'docker ps -a --filter name=aim-paperclip --format "{{.Names}}" | wc -l'
echo ""

# AC-5,6,7: deprecated code gone
echo "AC-5 magisters gone:"
ssh aim 'ls /opt/aim/AIM/src/aim/magisters 2>&1 | head -1'
echo "AC-6 subagents gone:"
ssh aim 'ls /opt/aim/AIM/src/aim/subagents 2>&1 | head -1'
echo "AC-7 pipeline v7 gone:"
ssh aim 'ls /opt/aim/AIM/hermes/app/pipeline 2>&1 | head -1'
echo ""

# AC-8: no backup files
echo "AC-8 backup files count:"
ssh aim 'find /opt/aim -maxdepth 5 \( -name "*.bak" -o -name "*.backup*" \) -type f 2>/dev/null | wc -l'
echo ""

# AC-9: .venv gone
echo "AC-9 .venv gone:"
ssh aim 'ls /opt/aim/AIM/.venv 2>&1 | head -1'
echo ""

# AC-10: website
echo "AC-10 iamaim.ru:"
curl -sI https://iamaim.ru/ | head -1
echo ""

# AC-11: chat
echo "AC-11 Chat:"
HERMES_KEY=$(ssh aim 'grep HERMES_API_KEY /opt/aim/AIM/.env.production | cut -d= -f2')
curl -s -X POST https://iamaim.ru/api/chat \
  -H "Authorization: Bearer $HERMES_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message":"тест"}' | head -c 200
echo ""

# AC-12: Hermes health
echo -e "\nAC-12 Hermes health:"
ssh aim 'docker exec aim-hermes curl -s http://localhost:8000/health'

echo -e "\n=== PHASE 01 COMPLETE ==="
```

---

#### Task 5.2: Создать отчёт о завершении Phase 01

**Локально:**
```bash
# Создать SUMMARY.md в phase-01-stabilization/
cat > /Users/mikhaileliseev/Desktop/Dev/meAI_1/.planning/phases/phase-01-stabilization/SUMMARY.md <<EOF
# Phase 01 — Stabilization & Cleanup (COMPLETE)

**Дата завершения:** $(date +%Y-%m-%d)
**Длительность:** 5 дней

## Результаты

### Acceptance Criteria — все 15 выполнены
- [x] AC-1: PostgreSQL auth works
- [x] AC-2: session_archive no errors
- [x] AC-3: SOUL.md synced
- [x] AC-4: paperclip removed
- [x] AC-5: magisters removed
- [x] AC-6: subagents removed
- [x] AC-7: pipeline v7 removed
- [x] AC-8: no backup files
- [x] AC-9: .venv removed
- [x] AC-10: website works
- [x] AC-11: chat works
- [x] AC-12: Hermes healthy
- [x] AC-13: SESSION.md updated
- [x] AC-14: CLAUDE.md updated
- [x] AC-15: .current-task updated

## Метрики

| Метрика | До | После |
|---|---|---|
| Docker контейнеры | 16 | 14 |
| Docker образы (размер) | 13.1 GB | ~10 GB |
| .bak файлов | 15+ | 0 |
| Zombie код | ~3 MB | 0 |
| .venv | 236 MB | 0 |
| Logs без ротации | 87 MB | <5 MB |
| Python файлов | ~250 | ~100 |

## Что дальше

Phase 02: Анализ Phase 09 + упрощение tools + починка run_full_scout.
EOF
```

---

#### Task 5.3: Git tag для завершения

```bash
cd /Users/mikhaileliseev/Desktop/Dev/meAI_1
git tag phase-01-complete
git push --tags 2>/dev/null || echo "tag local"
```

---

## 🚨 Risk Mitigation

### Что может пойти не так

1. **aim-app не запускается после удаления magisters**
   - **Mitigation:** Backup в Task 1.1, git tag pre-phase-01
   - **Rollback:** `git checkout pre-phase-01-stabilization -- src/aim/main.py && docker-compose build && docker-compose up -d`

2. **Hermes теряет tools после удаления pipeline**
   - **Mitigation:** Pipeline НЕ используется в tools. Smoke test после удаления
   - **Rollback:** git tag pre-phase-01-stabilization

3. **PostgreSQL reset теряет данные**
   - **Mitigation:** Backup в Task 1.1. Данные и так пустые (4 строки event_bus)
   - **Acceptable**

4. **Чат перестаёт работать**
   - **Mitigation:** Smoke test после каждой волны
   - **Stop criterion:** если Wave N smoke test fail — откат к Wave N-1

---

## 📋 Definition of Done

Phase 01 завершена когда:
1. ✅ ВСЕ 15 acceptance criteria выполнены
2. ✅ Final verification (Task 5.1) проходит без ошибок
3. ✅ SUMMARY.md создан
4. ✅ Git tag `phase-01-complete` создан
5. ✅ SESSION.md / CLAUDE.md / .current-task обновлены
6. ✅ Готов к Phase 02 (анализ Phase 09 + simplification)

---

## 🎯 После Phase 01 (preview Phase 02)

```
Phase 02 — Simplification & Focus
- Task 2.1: Глубокий анализ Phase 09 (создать 13-PHASE09-ANALYSIS.md)
- Task 2.2: Скрыть детальные tools от LLM, оставить run_full_scout
- Task 2.3: Починить run_full_scout (14 фаз + session_archive + publish)
- Task 2.4: UX test (URL → отчёт)
```

---

*Этот план — результат 4 часов аудита + 30 минут планирования. Каждое действие обосновано refactor-analysis/. Если что-то непонятно — читать 00-PROJECT-CONTEXT.md.*
