# Миграция AIM на новый сервер + WordPress — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Перенести AIM с 138.16.224.188 на 78.17.128.169 и развернуть WordPress на iamaim.ru. AIM переезжает на app.iamaim.ru.

**Architecture:** Новый сервер (Ubuntu 24.04) — чистая установка Docker, клон репо, docker compose up AIM, добавляем WordPress (php-fpm + MariaDB), настраиваем nginx (iamaim.ru → WP, app.iamaim.ru → AIM), мигрируем данные, переключаем DNS.

**Tech Stack:** Ubuntu 24.04, Docker, Docker Compose, Nginx, WordPress PHP-FPM, MariaDB, Let's Encrypt, PostgreSQL 16, Redis 7

---

### Task 1: Новый сервер — Docker + SSH-ключ для GitHub

- [ ] **Step 1: Установить Docker**

```bash
ssh root@78.17.128.169 "curl -fsSL https://get.docker.com | sh && systemctl enable docker --now && docker --version"
```

Expected: `Docker version 2x.x.x`

- [ ] **Step 2: Сгенерировать SSH-ключ для GitHub**

```bash
ssh root@78.17.128.169 'ssh-keygen -t ed25519 -C "aim-server-deploy-v2" -f ~/.ssh/id_ed25519 -N "" && cat ~/.ssh/id_ed25519.pub'
```

Скопировать публичный ключ.

- [ ] **Step 3: Добавить ключ в GitHub deploy keys**

Открыть https://github.com/MikhailEliseev/meAI/settings/keys/new

Вставить:
- Title: `aim-server-deploy-v2`
- Key: скопированный публичный ключ
- ✅ Allow write access

- [ ] **Step 4: Проверить доступ к GitHub**

```bash
ssh root@78.17.128.169 "ssh -o StrictHostKeyChecking=accept-new -T git@github.com 2>&1"
```

Expected: `Hi MikhailEliseev/meAI! You've successfully authenticated...`

- [ ] **Step 5: Создать структуру каталогов**

```bash
ssh root@78.17.128.169 "mkdir -p /opt/aim/leads /opt/aim/AIM"
```

---

### Task 2: Клонирование репо + .env

- [ ] **Step 1: Клонировать репо**

```bash
ssh root@78.17.128.169 "cd /opt/aim && git clone git@github.com:MikhailEliseev/meAI.git AIM"
```

- [ ] **Step 2: Скопировать .env.production со старого сервера**

```bash
ssh aim "cat /opt/aim/AIM/.env.production" > /tmp/aim-env-prod
scp /tmp/aim-env-prod root@78.17.128.169:/opt/aim/AIM/.env.production
rm /tmp/aim-env-prod
```

- [ ] **Step 3: Добавить WordPress-пароли в .env.production**

```bash
ssh root@78.17.128.169 "echo 'WP_DB_PASSWORD=chudLO16UpknuQyI42Q1gbqP08MMgqJV' >> /opt/aim/AIM/.env.production && echo 'WP_DB_ROOT_PASSWORD=EB/GwtK/jd89Hz0EsIIQ7qjq0L1qmRn4' >> /opt/aim/AIM/.env.production"
```

- [ ] **Step 4: Создать симлинк .env**

```bash
ssh root@78.17.128.169 "ln -s /opt/aim/AIM/.env /opt/aim/.env 2>/dev/null; ls -la /opt/aim/.env"
```

---

### Task 3: Docker Compose — добавить WordPress

- [ ] **Step 1: Вставить wp + wp-db перед redis**

Найти строку `  redis:` в `/opt/aim/AIM/docker-compose.yml` на новом сервере:

```bash
ssh root@78.17.128.169 "grep -n '^  redis:' /opt/aim/AIM/docker-compose.yml"
```

Вставить перед ней содержимое блока (используя sed с вставкой):

```bash
ssh root@78.17.128.169 'sed -i "$(grep -n \"^  redis:\" /opt/aim/AIM/docker-compose.yml | cut -d: -f1)i\\\\
  wp:\\\\
    image: wordpress:php8.2-fpm-alpine\\\\
    container_name: aim-wp\\\\
    restart: unless-stopped\\\\
    expose:\\\\
      - \\\\\"9000\\\\\"\\\\
    environment:\\\\
      WORDPRESS_DB_HOST: wp-db\\\\
      WORDPRESS_DB_NAME: wordpress\\\\
      WORDPRESS_DB_USER: wp_user\\\\
      WORDPRESS_DB_PASSWORD: \\\\\${WP_DB_PASSWORD}\\\\
      WORDPRESS_CONFIG_EXTRA: |\\\\
        define('"'"'WP_HOME'"'"', '"'"'https://iamaim.ru'"'"');\\\\
        define('"'"'WP_SITEURL'"'"', '"'"'https://iamaim.ru'"'"');\\\\
        define('"'"'FORCE_SSL_ADMIN'"'"', true);\\\\
        define('"'"'WP_MEMORY_LIMIT'"'"', '"'"'256M'"'"');\\\\
        \\\\$_SERVER['"'"'HTTPS'"'"'] = '"'"'on'"'"';\\\\
    volumes:\\\\
      - wp_content:/var/www/html/wp-content\\\\
    networks:\\\\
      - aim-network\\\\
    depends_on:\\\\
      - wp-db\\\\
    deploy:\\\\
      resources:\\\\
        limits:\\\\
          cpus: '"'"'0.5'"'"'\\\\
          memory: 512M\\\\
    logging:\\\\
      driver: \\\\\"json-file\\\\\"\\\\
      options:\\\\
        max-size: \\\\\"10m\\\\\"\\\\
        max-file: \\\\\"3\\\\\"\\\\
\\\\
  wp-db:\\\\
    image: mariadb:11\\\\
    container_name: aim-wp-db\\\\
    restart: unless-stopped\\\\
    expose:\\\\
      - \\\\\"3306\\\\\"\\\\
    environment:\\\\
      MYSQL_DATABASE: wordpress\\\\
      MYSQL_USER: wp_user\\\\
      MYSQL_PASSWORD: \\\\\${WP_DB_PASSWORD}\\\\
      MYSQL_ROOT_PASSWORD: \\\\\${WP_DB_ROOT_PASSWORD}\\\\
    volumes:\\\\
      - wp_db:/var/lib/mysql\\\\
    networks:\\\\
      - aim-network\\\\
    command: >\\\\
      --character-set-server=utf8mb4\\\\
      --collation-server=utf8mb4_unicode_ci\\\\
      --max-allowed-packet=64M\\\\
    deploy:\\\\
      resources:\\\\
        limits:\\\\
          cpus: '"'"'0.5'"'"'\\\\
          memory: 512M\\\\
    logging:\\\\
      driver: \\\\\"json-file\\\\\"\\\\
      options:\\\\
        max-size: \\\\\"10m\\\\\"\\\\
        max-file: \\\\\"3\\\\\"" /opt/aim/AIM/docker-compose.yml'
```

Альтернативно — проще записать wp-блок локально и scp на сервер, затем вставить через Python.

**Более надёжный способ — через Python на сервере:**

```bash
ssh root@78.17.128.169 'python3 << '\''PYEOF'\''
import re

with open("/opt/aim/AIM/docker-compose.yml", "r") as f:
    content = f.read()

wp_block = """  wp:
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
        define('\\''WP_HOME'\\'', '\\''https://iamaim.ru'\\'');
        define('\\''WP_SITEURL'\\'', '\\''https://iamaim.ru'\\'');
        define('\\''FORCE_SSL_ADMIN'\\'', true);
        define('\\''WP_MEMORY_LIMIT'\\'', '\\''256M'\\'');
        $_SERVER['\\''HTTPS'\\''] = '\\''on'\\'';
    volumes:
      - wp_content:/var/www/html/wp-content
    networks:
      - aim-network
    depends_on:
      - wp-db
    deploy:
      resources:
        limits:
          cpus: '\\''0.5'\\''
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
          cpus: '\\''0.5'\\''
          memory: 512M
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

"""

# Insert before redis:
content = content.replace("  redis:", wp_block + "  redis:")

# Add volumes
if "wp_content:" not in content:
    content = content.rstrip() + "\n  wp_content:\n  wp_db:\n"

with open("/opt/aim/AIM/docker-compose.yml", "w") as f:
    f.write(content)

print("docker-compose.yml updated")
PYEOF'
```

- [ ] **Step 2: Проверить валидность YAML**

```bash
ssh root@78.17.128.169 "cd /opt/aim/AIM && docker compose config --quiet 2>&1"
```

Expected: no output.

- [ ] **Step 3: Обновить NEXT_PUBLIC_BASE_URL**

```bash
ssh root@78.17.128.169 "sed -i 's|NEXT_PUBLIC_BASE_URL=https://iamaim.ru|NEXT_PUBLIC_BASE_URL=https://app.iamaim.ru|' /opt/aim/AIM/docker-compose.yml"
```

- [ ] **Step 4: Проверить изменение**

```bash
ssh root@78.17.128.169 "grep NEXT_PUBLIC_BASE_URL /opt/aim/AIM/docker-compose.yml"
```

Expected: `NEXT_PUBLIC_BASE_URL=https://app.iamaim.ru`

---

### Task 4: Nginx-конфиг

- [ ] **Step 1: Записать новый конфиг на сервер**

Создать локально `/tmp/iamaim.conf` с полным содержимым (WordPress + AIM server blocks), затем:

```bash
scp /tmp/iamaim.conf root@78.17.128.169:/opt/aim/AIM/deploy/nginx/iamaim.conf
```

**Содержимое конфига (записать в `/tmp/iamaim.conf` локально):**

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

# iamaim.ru -> WordPress
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

    location ~* ^/wp-admin {
        allow 127.0.0.1;
        # WP_ADMIN_IP_PLACEHOLDER
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

    location ~* \.(jpg|jpeg|png|webp|avif|svg|gif|ico|css|js|woff|woff2|ttf|eot)$ {
        expires 30d;
        add_header Cache-Control "public, max-age=2592000, immutable";
        try_files $uri =404;
    }

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

# app.iamaim.ru -> AIM
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

    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://aim_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

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

    location /telegram/webhook {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://aim_hermes;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

    location / {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://aim_frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

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

```bash
MY_IP=$(curl -s ifconfig.me)
ssh root@78.17.128.169 "sed -i \"s/# WP_ADMIN_IP_PLACEHOLDER/allow $MY_IP;/\" /opt/aim/AIM/deploy/nginx/iamaim.conf"
```

- [ ] **Step 3: Проверить конфиг nginx**

```bash
ssh root@78.17.128.169 "docker run --rm -v /opt/aim/AIM/deploy/nginx/iamaim.conf:/etc/nginx/conf.d/default.conf:ro nginx:alpine nginx -t"
```

Expected: `syntax is ok` + `test is successful`

- [ ] **Step 4: Создать certbot webroot-директорию**

```bash
ssh root@78.17.128.169 "mkdir -p /opt/aim/AIM/ssl"
```

---

### Task 5: Запуск AIM на новом сервере

- [ ] **Step 1: Запустить все сервисы**

```bash
ssh root@78.17.128.169 "cd /opt/aim/AIM && docker compose up -d 2>&1"
```

- [ ] **Step 2: Ждать инициализации**

```bash
ssh root@78.17.128.169 "sleep 30 && docker ps --format 'table {{.Names}}\t{{.Status}}'"
```

Expected: все контейнеры `Up` (healthy или running)

- [ ] **Step 3: Проверить health эндпоинты**

```bash
ssh root@78.17.128.169 "curl -sf http://localhost:8000/health && echo ' app-ok'"
ssh root@78.17.128.169 "curl -sf http://localhost:8000/health -H 'Host: app.iamaim.ru' 2>/dev/null || docker exec aim-hermes curl -sf http://localhost:8000/health && echo ' hermes-ok'"
```

---

### Task 6: Миграция данных

- [ ] **Step 1: Дамп Postgres на старом сервере**

```bash
ssh aim "docker exec aim-postgres pg_dump -U aim_user -d aim_db -Fc -f /tmp/aim_db.dump"
ssh aim "docker cp aim-postgres:/tmp/aim_db.dump /tmp/aim_db.dump"
scp root@138.16.224.188:/tmp/aim_db.dump /tmp/aim_db.dump
scp /tmp/aim_db.dump root@78.17.128.169:/tmp/aim_db.dump
```

- [ ] **Step 2: Восстановить Postgres на новом сервере**

```bash
ssh root@78.17.128.169 "docker cp /tmp/aim_db.dump aim-postgres:/tmp/aim_db.dump && docker exec aim-postgres pg_restore -U aim_user -d aim_db --clean --if-exists /tmp/aim_db.dump 2>&1"
```

Expected: pg_restore завершается без фатальных ошибок (предупреждения про несуществующие объекты — нормально)

- [ ] **Step 3: Скопировать Hermes data**

```bash
ssh aim "docker exec aim-hermes tar -czf /tmp/hermes_data.tar.gz -C /opt/data . 2>/dev/null"
ssh aim "docker cp aim-hermes:/tmp/hermes_data.tar.gz /tmp/hermes_data.tar.gz"
scp root@138.16.224.188:/tmp/hermes_data.tar.gz /tmp/hermes_data.tar.gz
scp /tmp/hermes_data.tar.gz root@78.17.128.169:/tmp/hermes_data.tar.gz
ssh root@78.17.128.169 "docker cp /tmp/hermes_data.tar.gz aim-hermes:/tmp/ && docker exec aim-hermes tar -xzf /tmp/hermes_data.tar.gz -C /opt/data/"
```

- [ ] **Step 4: Скопировать leads + AIM data + Grafana + Obsidian**

```bash
scp -r root@138.16.224.188:/opt/aim/leads/ /tmp/aim-leads
scp -r /tmp/aim-leads/ root@78.17.128.169:/opt/aim/leads/

ssh aim "docker exec aim-grafana tar -czf /tmp/grafana.tar.gz -C /var/lib/grafana . 2>/dev/null"
ssh aim "docker cp aim-grafana:/tmp/grafana.tar.gz /tmp/grafana.tar.gz"
scp root@138.16.224.188:/tmp/grafana.tar.gz /tmp/grafana.tar.gz
scp /tmp/grafana.tar.gz root@78.17.128.169:/tmp/grafana.tar.gz
ssh root@78.17.128.169 "docker cp /tmp/grafana.tar.gz aim-grafana:/tmp/ && docker exec aim-grafana tar -xzf /tmp/grafana.tar.gz -C /var/lib/grafana/"
```

- [ ] **Step 5: Скопировать AIM data + Obsidian**

```bash
ssh root@78.17.128.169 "scp -r root@138.16.224.188:/opt/aim/AIM/data/ /opt/aim/AIM/data/ 2>/dev/null"
ssh root@78.17.128.169 "scp -r root@138.16.224.188:/opt/aim/AIM/obsidian/ /opt/aim/AIM/obsidian/ 2>/dev/null"
```

Альтернатива (если scp между серверами напрямую не работает):

```bash
# Локально
scp -r root@138.16.224.188:/opt/aim/AIM/data/ /tmp/aim-data
scp -r /tmp/aim-data/ root@78.17.128.169:/opt/aim/AIM/data/

scp -r root@138.16.224.188:/opt/aim/AIM/obsidian/ /tmp/aim-obsidian
scp -r /tmp/aim-obsidian/ root@78.17.128.169:/opt/aim/AIM/obsidian/
```

---

### Task 7: DNS + SSL (критический шаг — даунтайм ~15 мин)

- [ ] **Step 1: Переключить A-записи у регистратора**

В панели DNS-регистратора iamaim.ru изменить/добавить:

```
iamaim.ru     A → 78.17.128.169
www.iamaim.ru A → 78.17.128.169
app.iamaim.ru A → 78.17.128.169  (новая запись)
```

TTL: минимальный (300 или 120)

- [ ] **Step 2: Ждать пропагации DNS**

```bash
watch -n 30 "dig +short iamaim.ru A && dig +short app.iamaim.ru A"
```

Ждать пока оба покажут `78.17.128.169`.

- [ ] **Step 3: Остановить nginx на новом сервере**

```bash
ssh root@78.17.128.169 "docker stop aim-nginx"
```

- [ ] **Step 4: Получить SSL-сертификат**

```bash
ssh root@78.17.128.169 "certbot certonly --standalone --agree-tos --email info@iamaim.ru -d iamaim.ru -d www.iamaim.ru -d app.iamaim.ru"
```

- [ ] **Step 5: Проверить сертификат**

```bash
ssh root@78.17.128.169 "openssl x509 -in /etc/letsencrypt/live/iamaim.ru/fullchain.pem -text -noout | grep DNS:"
```

Expected: DNS:iamaim.ru, DNS:www.iamaim.ru, DNS:app.iamaim.ru

- [ ] **Step 6: Обновить nginx mount для сертификатов**

```bash
ssh root@78.17.128.169 "sed -i 's|- ./ssl:/etc/nginx/ssl:ro|- /etc/letsencrypt:/etc/letsencrypt:ro|' /opt/aim/AIM/docker-compose.yml"
```

- [ ] **Step 7: Запустить nginx**

```bash
ssh root@78.17.128.169 "cd /opt/aim/AIM && docker compose up -d nginx"
```

---

### Task 8: Проверка всего

- [ ] **Step 1: WordPress доступен**

```bash
curl -sk -o /dev/null -w "%{http_code}" https://iamaim.ru/
```

Expected: `302` или `200`

- [ ] **Step 2: AIM на app.iamaim.ru**

```bash
curl -sk -o /dev/null -w "%{http_code}" https://app.iamaim.ru/
```

Expected: `200`

- [ ] **Step 3: API работает**

```bash
curl -sk -o /dev/null -w "%{http_code}" https://app.iamaim.ru/health
```

Expected: `200`

- [ ] **Step 4: Telegram webhook**

```bash
curl -sk -o /dev/null -w "%{http_code}" https://app.iamaim.ru/telegram/webhook
```

Expected: не 502/503/504

- [ ] **Step 5: Пройти WordPress-установку**

Открыть https://iamaim.ru/ в браузере, пройти установку (язык, название сайта, логин/пароль админа, email).

---

### Task 9: Пост-деплой

- [ ] **Step 1: Обновить Telegram webhook**

```bash
TOKEN=$(ssh root@78.17.128.169 "grep TELEGRAM_BOT_TOKEN /opt/aim/AIM/.env.production | cut -d= -f2")
curl -s "https://api.telegram.org/bot${TOKEN}/setWebhook?url=https://app.iamaim.ru/telegram/webhook"
```

Expected: `{"ok":true,"result":true}`

- [ ] **Step 2: Настроить certbot автообновление**

```bash
ssh root@78.17.128.169 "(crontab -l 2>/dev/null; echo '0 3 * * * docker stop aim-nginx && certbot renew --quiet && docker start aim-nginx') | crontab -"
```

- [ ] **Step 3: Проверить dry-run автообновления**

```bash
ssh root@78.17.128.169 "docker stop aim-nginx && certbot renew --dry-run && docker start aim-nginx"
```

Expected: `Congratulations, all simulated renewals succeeded`

- [ ] **Step 4: Установить WordPress-плагины (через админку)**

- Rank Math SEO или Yoast SEO
- WP Super Cache
- Wordfence Security
- Тема (GeneratePress, Astra или Kadence)

- [ ] **Step 5: Перезапустить все контейнеры для чистоты**

```bash
ssh root@78.17.128.169 "cd /opt/aim/AIM && docker compose restart"
```

---

### Rollback-план

Если что-то пошло не так после переключения DNS:

```bash
# 1. Вернуть DNS-записи на старый IP (138.16.224.188)
# 2. Ждать пропагации (5-15 мин)
# 3. Старый сервер всё ещё работает — трафик вернётся на него
```

Старый сервер не выключаем 24 часа после миграции.
