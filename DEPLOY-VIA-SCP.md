# ⚠️ DEPLOY-VIA-SCP — НЕ ДЕЛАЙ git pull НА СЕРВЕРЕ

> Создано 21 июля 2026 после инцидента с падением v2 при пересборке образа.

## Что случилось

На сервере `/opt/aim/AIM/` git-репозиторий **рассинхронизирован** с GitHub:
- Сервер на ветке `main` (старый коммит `e7b0dec`, которого больше нет в истории после filter-repo)
- 2197 uncommitted изменений (включая `.env` с **ключами API**)
- В `origin/main` НЕТ папки `hermes-v2/` — она существует только в `feat/competitor-v2-perplexity-searxng`

Если сделать `git pull` / `git checkout` / `git reset --hard` на сервере — **возможны**:
1. Удаление `.env` (потеря API ключей Perplexity/Apify/Firecrawl)
2. Удаление всей папки `hermes-v2/` (если checkout на main)
3. Возврат сломанного main.py (если checkout на старую ветку с knowledge import)
4. Падение чата v2

## Как ДЕПЛОИТЬ (правильный способ)

**Деплой идёт через scp + docker compose, НЕ через git.**

```bash
# 1. Локально: копируем изменённые файлы на сервер
scp AIM/hermes-v2/app/lib/yandex_reviews.py aim:/opt/aim/AIM/hermes-v2/app/lib/
scp AIM/hermes-v2/app/tools/run_review_platforms.py aim:/opt/aim/AIM/hermes-v2/app/tools/

# 2. На сервере: пересобираем образ + перезапуск
ssh aim "cd /opt/aim/AIM && docker compose build hermes-v2"
ssh aim "cd /opt/aim/AIM && docker compose up -d --force-recreate --no-deps hermes-v2"

# 3. Ждём healthcheck
sleep 30
ssh aim "docker exec aim-hermes-v2 curl -s http://localhost:8000/health"
```

## Что НЕ делать на сервере

```bash
# ❌ ОПАСНО — удалит .env с ключами
git pull
git checkout main
git reset --hard origin/main

# ❌ ОПАСНО — вернёт старую сломанную версию
git checkout <старая ветка>

# ❌ ОПАСНО — затрёт локальные изменения сервера
git stash && git pull
```

## Если очень нужно синхронизировать git на сервере

Аккуратная процедура (ДЕЛАТЬ ТОЛЬКО ПОСЛЕ BACKUP):

```bash
# 1. Backup .env и других конфигов
ssh aim "cp /opt/aim/AIM/.env /root/.env.backup.$(date +%Y%m%d)"

# 2. Спрятать изменения
ssh aim "cd /opt/aim/AIM && git stash"

# 3. Обновить git
ssh aim "cd /opt/aim/AIM && git fetch origin"
ssh aim "cd /opt/aim/AIM && git checkout feat/competitor-v2-perplexity-searxng"
ssh aim "cd /opt/aim/AIM && git pull"

# 4. Вернуть конфиги
ssh aim "cd /opt/aim/AIM && git stash pop"
# Если конфликты — решать вручную, НЕ затирать .env
```

## Почему так

Исторически сервер настраивался вручную: конфиги правились через `vi`,
файлы копировались через scp, образы пересобирались локально. Это работало,
но создало рассинхрон с git. Полная синхронизация — отдельная задача,
пока scp-деплой безопаснее.
