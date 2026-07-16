# WordPress на iamaim.ru — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Заменить Next.js-лендинг iamaim.ru на WordPress (Docker), AIM переезжает на app.iamaim.ru

**Architecture:** aim-nginx маршрутизирует iamaim.ru → WordPress (FastCGI → PHP-FPM), app.iamaim.ru → AIM (фронтенд + API). Новые контейнеры: aim-wp (wordpress:php8.2-fpm-alpine) + aim-wp-db (mariadb:11).

**Tech Stack:** Docker Compose, Nginx, WordPress PHP-FPM, MariaDB, Let's Encrypt

---

### Task 1: DNS — A-запись app.iamaim.ru

**Где:** Панель управления DNS у регистратора домена iamaim.ru

- [ ] **Step 1: Добавить A-запись**

Добавить новую A-запись:
```
app  →  138.16.224.188
```

TTL: 600 (или дефолтный)

- [ ] **Step 2: Проверить DNS**

```bash
dig +short app.iamaim.ru A
```

Expected: `138.16.224.188`

Может занять до часа (обычно 5-10 минут).

---

### Task 2: SSL — расширить Let's Encrypt сертификат

**Файлы:** Сертификат на сервере — `/etc/letsencrypt/live/iamaim.ru/`

- [ ] **Step 1: Остановить nginx (освободить порт 80)**

```bash
ssh aim "docker stop aim-nginx"
```

- [ ] **Step 2: Расширить сертификат (standalone, порт 80 свободен)**

```bash
ssh aim "certbot certonly --standalone --cert-name iamaim.ru \
  -d iamaim.ru -d www.iamaim.ru -d app.iamaim.ru"
```

Подтвердить добавление доменов, если certbot спросит.

- [ ] **Step 3: Проверить, что сертификат обновлён**

```bash
ssh aim "openssl x509 -in /etc/letsencrypt/live/iamaim.ru/fullchain.pem -text -noout | grep DNS:"
```

Expected: DNS:iamaim.ru, DNS:www.iamaim.ru, DNS:app.iamaim.ru

- [ ] **Step 4: Запустить nginx (пока со старым конфигом)**

```bash
ssh aim "docker start aim-nginx"
```

---

### Task 3: .env — пароли WordPress

**Файл:** `/opt/aim/AIM/.env.production` (на сервере)

- [ ] **Step 1: Сгенерировать пароли локально**

```bash
WP_DB_PASSWORD=$(openssl rand -base64 24)
WP_DB_ROOT_PASSWORD=$(openssl rand -base64 24)
echo "WP_DB_PASSWORD=$WP_DB_PASSWORD"
echo "WP_DB_ROOT_PASSWORD=$WP_DB_ROOT_PASSWORD"
```

Скопировать вывод.

- [ ] **Step 2: Добавить пароли в .env.production на сервере**

```bash
ssh aim "echo 'WP_DB_PASSWORD=<сгенерированный_пароль>' >> /opt/aim/AIM/.env.production"
ssh aim "echo 'WP_DB_ROOT_PASSWORD=<сгенерированный_root_пароль>' >> /opt/aim/AIM/.env.production"
```

---

### Task 4: docker-compose.yml — добавить WordPress + MariaDB

**Файл:** `/opt/aim/AIM/docker-compose.yml` (на сервере)

- [ ] **Step 1: Добавить сервис wp в docker-compose.yml**

Открыть `/opt/aim/AIM/docker-compose.yml` и добавить перед секцией `redis:`:

```yaml
  wp:
    image: wordpress:php8.2-fpm-alpine
    container_name: aim-wp
    restart: unless-stopped
    expose:
      - "9000"
    environment:
      WORDPRESS_DB_HOST: wp-db
      WORDPRESS_DB_NAME: wordpress
      WORDPRESS_DB_USER: wp_user
      WORDPRESS_DB_PASSWORD: ${WP_DB_PASSWORD}
      WORDPRESS_CONFIG_EXTRA: |
        define('WP_HOME', 'https://iamaim.ru');
        define('WP_SITEURL', 'https://iamaim.ru');
        define('FORCE_SSL_ADMIN', true);
        define('WP_MEMORY_LIMIT', '256M');
        $_SERVER['HTTPS'] = 'on';
    volumes:
      - wp_content:/var/www/html/wp-content
    networks:
      - aim-network
    depends_on:
      - wp-db
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  wp-db:
    image: mariadb:11
    container_name: aim-wp-db
    restart: unless-stopped
    expose:
      - "3306"
    environment:
      MYSQL_DATABASE: wordpress
      MYSQL_USER: wp_user
      MYSQL_PASSWORD: ${WP_DB_PASSWORD}
      MYSQL_ROOT_PASSWORD: ${WP_DB_ROOT_PASSWORD}
    volumes:
      - wp_db:/var/lib/mysql
    networks:
      - aim-network
    command: >
      --character-set-server=utf8mb4
      --collation-server=utf8mb4_unicode_ci
      --max-allowed-packet=64M
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

- [ ] **Step 2: Добавить volumes в конец файла**

Добавить в секцию `volumes:`:
```yaml
  wp_content:
  wp_db:
```

- [ ] **Step 3: Проверить валидность YAML**

```bash
ssh aim "cd /opt/aim/AIM && docker compose config --quiet 2>&1"
```

Expected: no output (no errors).

---

### Task 5: Nginx — переписать конфиг под WordPress + app.iamaim.ru

**Файл:** `/opt/aim/AIM/deploy/nginx/iamaim.conf` (на сервере)

- [ ] **Step 1: Создать новый nginx конфиг**

Записать `/opt/aim/AIM/deploy/nginx/iamaim.conf`:

```nginx
upstream aim_backend {
    server app:8000;
}

upstream aim_frontend {
    server frontend:3099;
}

upstream aim_hermes {
    server hermes:8000;
}

limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=health_limit:10m rate=100r/s;

# HTTP → HTTPS (оба домена)
server {
    listen 80;
    server_name iamaim.ru www.iamaim.ru app.iamaim.ru;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# ============================================================
# iamaim.ru → WordPress
# ============================================================
server {
    listen 443 ssl http2;
    server_name iamaim.ru www.iamaim.ru;

    ssl_certificate /etc/letsencrypt/live/iamaim.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/iamaim.ru/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;

    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    root /var/www/html;
    index index.php;

    location / {
        try_files $uri $uri/ /index.php?$args;
    }

    location ~ \.php$ {
        fastcgi_pass wp:9000;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param PATH_INFO $fastcgi_path_info;
        include fastcgi_params;
        fastcgi_read_timeout 300s;
        fastcgi_buffers 16 16k;
        fastcgi_buffer_size 32k;
    }

    # wp-admin: разрешить только с IP админа
    location ~* ^/wp-admin {
        allow 127.0.0.1;
        # USER_IP_PLACEHOLDER — будет заменён при деплое
        deny all;

        location ~ \.php$ {
            fastcgi_pass wp:9000;
            fastcgi_index index.php;
            fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
            fastcgi_param PATH_INFO $fastcgi_path_info;
            include fastcgi_params;
            fastcgi_read_timeout 300s;
            fastcgi_buffers 16 16k;
            fastcgi_buffer_size 32k;
        }
    }

    # Статика WordPress — агрессивный кеш
    location ~* \.(jpg|jpeg|png|webp|avif|svg|gif|ico|css|js|woff|woff2|ttf|eot)$ {
        expires 30d;
        add_header Cache-Control "public, max-age=2592000, immutable";
        try_files $uri =404;
    }

    # Блокируем чувствительные файлы
    location ~* \.(htaccess|htpasswd|git|svn|env)$ {
        deny all;
        return 404;
    }

    location ~* wp-config\.php {
        deny all;
        return 404;
    }

    location = /xmlrpc.php {
        deny all;
        return 404;
    }
}

# ============================================================
# app.iamaim.ru → AIM (фронтенд + API + Telegram webhook)
# ============================================================
server {
    listen 443 ssl http2;
    server_name app.iamaim.ru;

    ssl_certificate /etc/letsencrypt/live/iamaim.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/iamaim.ru/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;

    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Frontend API routes (Next.js) — SSE streaming
    location /api/chat/ {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://aim_frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_buffering off;
        proxy_cache off;
        chunked_transfer_encoding on;
        proxy_set_header Connection '';
    }

    # Backend API
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://aim_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

    # Backend health/metrics
    location /health {
        limit_req zone=health_limit burst=20 nodelay;
        proxy_pass http://aim_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ready {
        limit_req zone=health_limit burst=20 nodelay;
        proxy_pass http://aim_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /metrics {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://aim_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Telegram webhook → Hermes
    location /telegram/webhook {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://aim_hermes;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

    # Frontend (everything else)
    location / {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://aim_frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

    # Static files — cache aggressively
    location /_next/static/ {
        proxy_pass http://aim_frontend;
        proxy_set_header Host $host;
        proxy_cache_valid 200 1y;
        add_header Cache-Control "public, max-age=31536000, immutable";
    }

    location ~* \.(jpg|jpeg|png|webp|avif|svg|ico|css|js|woff2)$ {
        proxy_pass http://aim_frontend;
        proxy_set_header Host $host;
        proxy_cache_valid 200 30d;
        add_header Cache-Control "public, max-age=2592000";
    }
}
```

- [ ] **Step 2: Заменить плейсхолдер IP**

Узнать свой IP:
```bash
curl -s ifconfig.me
```

Заменить `USER_IP_PLACEHOLDER` в конфиге на реальный IP:
```bash
MY_IP=$(curl -s ifconfig.me)
ssh aim "sed -i \"s/# USER_IP_PLACEHOLDER.*/allow $MY_IP;/\" /opt/aim/AIM/deploy/nginx/iamaim.conf"
```

- [ ] **Step 3: Проверить nginx конфиг**

```bash
ssh aim "docker run --rm -v /opt/aim/AIM/deploy/nginx/iamaim.conf:/etc/nginx/conf.d/default.conf:ro nginx:alpine nginx -t"
```

Expected: `syntax is ok` + `test is successful`

---

### Task 6: Deploy — запустить новые контейнеры

- [ ] **Step 1: Перезапустить nginx с новым конфигом**

```bash
ssh aim "cd /opt/aim/AIM && docker compose restart nginx"
```

- [ ] **Step 2: Запустить WordPress и MariaDB**

```bash
ssh aim "cd /opt/aim/AIM && docker compose up -d wp-db wp"
```

- [ ] **Step 3: Ждать готовности MariaDB**

```bash
ssh aim "sleep 15 && docker exec aim-wp-db mysqladmin ping -u root -p\${WP_DB_ROOT_PASSWORD} 2>/dev/null"
```

Если не отвечает — подождать ещё 15 секунд.

- [ ] **Step 4: Проверить что все контейнеры поднялись**

```bash
ssh aim "docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E 'aim-wp|aim-wp-db|aim-nginx'"
```

Expected: все три `Up` (healthy)

---

### Task 7: Verify — проверить, что всё работает

- [ ] **Step 1: WordPress доступен на iamaim.ru**

```bash
curl -sk -o /dev/null -w "%{http_code}" https://iamaim.ru/
```

Expected: `302` или `200` (WordPress отдаёт страницу установки/редирект)

- [ ] **Step 2: AIM фронтенд доступен на app.iamaim.ru**

```bash
curl -sk -o /dev/null -w "%{http_code}" https://app.iamaim.ru/
```

Expected: `200` (Next.js лендинг)

- [ ] **Step 3: API работает**

```bash
curl -sk -o /dev/null -w "%{http_code}" https://app.iamaim.ru/health
```

Expected: `200`

- [ ] **Step 4: Telegram webhook доступен**

```bash
curl -sk -o /dev/null -w "%{http_code}" https://app.iamaim.ru/telegram/webhook
```

Expected: Любой ответ (не 502/503/504)

- [ ] **Step 5: Открыть WordPress в браузере**

Открыть `https://iamaim.ru/` — должна быть страница установки WordPress (выбор языка).

Пройти установку: язык → название сайта → логин/пароль админа → email.

---

### Task 8: Post-deploy — финализация

- [ ] **Step 1: Обновить Telegram webhook URL**

Узнать текущий токен бота:
```bash
ssh aim "grep TELEGRAM_BOT_TOKEN /opt/aim/AIM/.env.production"
```

Обновить webhook:
```bash
curl -s "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://app.iamaim.ru/telegram/webhook"
```

Expected: `{"ok":true,"result":true,"description":"Webhook was set"}`

- [ ] **Step 2: Обновить NEXT_PUBLIC_BASE_URL для фронтенда**

В `/opt/aim/AIM/docker-compose.yml`, секция `frontend`:
```yaml
    environment:
      - NEXT_PUBLIC_BASE_URL=https://app.iamaim.ru
```

Перезапустить фронтенд:
```bash
ssh aim "cd /opt/aim/AIM && docker compose up -d --force-recreate frontend"
```

- [ ] **Step 3: Проверить автообновление SSL**

```bash
ssh aim "certbot renew --dry-run 2>&1 | tail -5"
```

Expected: `Congratulations, all simulated renewals succeeded`

- [ ] **Step 4: Установить WordPress плагины (через админку)**

После входа в wp-admin (`https://iamaim.ru/wp-admin`):
- **Rank Math SEO** или **Yoast SEO** — SEO-оптимизация
- **WP Super Cache** или **Redis Object Cache** — кеширование
- **Wordfence** — безопасность
- Тема на выбор (GeneratePress, Astra, Kadence — легковесные и SEO-friendly)

---

### Rollback-план

Если что-то пошло не так — откат за 2 минуты:

```bash
# Остановить WordPress
ssh aim "cd /opt/aim/AIM && docker compose stop wp wp-db"

# Вернуть старый nginx конфиг (лежит в git)
ssh aim "cd /opt/aim/AIM && git checkout deploy/nginx/iamaim.conf"

# Перезапустить nginx
ssh aim "cd /opt/aim/AIM && docker compose restart nginx"

# Фронтенд обратно на iamaim.ru — изменить NEXT_PUBLIC_BASE_URL обратно
# и перезапустить фронтенд
```
