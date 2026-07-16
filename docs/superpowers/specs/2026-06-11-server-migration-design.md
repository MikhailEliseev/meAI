# Миграция AIM на новый сервер + WordPress — Design Doc

**Дата:** 2026-06-11
**Цель:** Перенести AIM с текущего сервера (138.16.224.188) на новый (78.17.128.169) и развернуть WordPress на iamaim.ru.

## Текущий сервер (источник)

| Параметр | Значение |
|----------|----------|
| IP | 138.16.224.188 |
| OS | Ubuntu 22.04 |
| CPU | 2 ядра |
| RAM | 3.8 GB |
| Disk | 59 GB (84% занято, swap 100%) |

## Новый сервер (назначение)

| Параметр | Значение |
|----------|----------|
| IP | 78.17.128.169 |
| OS | Ubuntu 24.04 LTS |
| CPU | 2 ядра |
| RAM | 3.8 GB |
| Disk | 30 GB (будет расширен) |

## Итоговая архитектура

```
78.17.128.169 (aim-nginx :80/:443)
├── iamaim.ru        → WordPress (aim-wp:9000, FastCGI)
├── app.iamaim.ru    → AIM фронтенд (aim-frontend:3099)
├── /api/*           → AIM бэкенд (aim-app:8000)
└── /telegram/webhook → Hermes (aim-hermes:8000)
```

## План миграции (8 шагов)

### Шаг 1: Установка Docker на новом сервере

```bash
curl -fsSL https://get.docker.com | sh
systemctl enable docker --now
```

### Шаг 2: Клонирование репо

```bash
mkdir -p /opt/aim
cd /opt/aim
git clone git@github.com:MikhailEliseev/meAI.git AIM
```

### Шаг 3: Копирование секретов и данных

**Мигрируем:**
- `.env.production` — scp с текущего сервера
- `hermes_data` volume (24 MB)
- `/opt/aim/leads/` (228 KB)
- `/opt/aim/AIM/data/` (40 KB)
- Grafana dashboards (53 MB)
- Obsidian vaults (684 KB)

**Мигрируем через pg_dump:**
- Postgres `aim_db` (8 MB)

**НЕ мигрируем:**
- SSL-сертификаты (получим новые)
- Prometheus-метрики (история не нужна)
- Redis (кеш перестроится)

### Шаг 4: Развёртывание AIM

```bash
cd /opt/aim/AIM
docker compose up -d
```

### Шаг 5: WordPress

Два новых контейнера в docker-compose.yml:
- `aim-wp` — wordpress:php8.2-fpm-alpine
- `aim-wp-db` — mariadb:11

### Шаг 6: Nginx

Конфиг iamaim.conf: два server блока — WordPress на iamaim.ru, AIM на app.iamaim.ru.

### Шаг 7: Миграция БД

```bash
# На старом сервере
docker exec aim-postgres pg_dump -U aim_user aim_db -Fc > /tmp/aim_db.dump
scp /tmp/aim_db.dump root@78.17.128.169:/tmp/

# На новом сервере
docker cp /tmp/aim_db.dump aim-postgres:/tmp/
docker exec aim-postgres pg_restore -U aim_user -d aim_db /tmp/aim_db.dump
```

### Шаг 8: DNS-переключение

A-записи у регистратора:
```
iamaim.ru     → 78.17.128.169
www.iamaim.ru → 78.17.128.169
app.iamaim.ru → 78.17.128.169
```

После пропагации — SSL через certbot standalone, проверка всего стека.

## Риски

- **SSH-ключ для GitHub:** на новом сервере нужно настроить deploy key для `git clone`
- **SSL renewal:** certbot должен использовать standalone (останавливать nginx на время обновления) или переключиться на webroot
- **Telegram webhook:** после переключения DNS обновить URL бота на `https://app.iamaim.ru/telegram/webhook`
- **NEXT_PUBLIC_BASE_URL:** фронтенд должен знать новый URL `https://app.iamaim.ru`
