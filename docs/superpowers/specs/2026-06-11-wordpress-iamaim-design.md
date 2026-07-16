# WordPress на iamaim.ru — Design Doc

**Дата:** 2026-06-11
**Цель:** Заменить текущий Next.js-лендинг на полноценный WordPress-сайт с блогом. AIM фронтенд переезжает на `app.iamaim.ru`.

## Архитектура

```
iamaim.ru              → WordPress (новый aim-wp контейнер)
app.iamaim.ru          → AIM фронтенд + /api/* + /telegram/webhook
```

### Новые контейнеры

| Контейнер | Образ | Назначение |
|-----------|-------|------------|
| `aim-wp` | `wordpress:php8.2-fpm-alpine` | PHP-FPM для WordPress |
| `aim-wp-db` | `mariadb:11` | База данных WordPress |

Почему FPM-образ: `aim-nginx` уже обслуживает порты 80/443, он же проксирует PHP-запросы через FastCGI в `aim-wp:9000`. Apache/второй nginx не нужен.

### Маршрутизация трафика

```
aim-nginx → iamaim.ru      → FastCGI → aim-wp:9000 (WordPress)
aim-nginx → app.iamaim.ru  → proxy_pass → aim-frontend:3099 (Next.js)
aim-nginx → /api/*         → proxy_pass → aim-app:8000 (бэкенд)
aim-nginx → /api/chat/*    → proxy_pass → aim-frontend:3099 (SSE streaming)
aim-nginx → /telegram/webhook → proxy_pass → aim-hermes:8000
```

## Docker Compose

Добавить в `AIM/docker-compose.yml`:

```yaml
  wp:
    image: wordpress:php8.2-fpm-alpine
    container_name: aim-wp
    restart: unless-stopped
    environment:
      WORDPRESS_DB_HOST: wp-db
      WORDPRESS_DB_NAME: wordpress
      WORDPRESS_DB_USER: wp_user
      WORDPRESS_DB_PASSWORD: ${WP_DB_PASSWORD}
      WORDPRESS_CONFIG_EXTRA: |
        define('WP_HOME', 'https://iamaim.ru');
        define('WP_SITEURL', 'https://iamaim.ru');
        define('FORCE_SSL_ADMIN', true);
    volumes:
      - wp_content:/var/www/html/wp-content
    networks:
      - aim-network
    depends_on:
      - wp-db

  wp-db:
    image: mariadb:11
    container_name: aim-wp-db
    restart: unless-stopped
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

volumes:
  wp_content:
  wp_db:
```

## Nginx

Конфиг `/opt/aim/AIM/deploy/nginx/iamaim.conf` — полная перезапись.

### iamaim.ru → WordPress

```
server {
    listen 443 ssl http2;
    server_name iamaim.ru www.iamaim.ru;
    root /var/www/html;
    index index.php;

    location / {
        try_files $uri $uri/ /index.php?$args;
    }

    location ~ \.php$ {
        fastcgi_pass wp:9000;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
        fastcgi_read_timeout 300s;
    }

    location ~* /wp-admin {
        allow <USER_IP>;
        deny all;
        # ... php handler nested ...
    }

    location ~* \.(jpg|jpeg|png|webp|avif|svg|css|js|woff2)$ {
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }
}
```

### app.iamaim.ru → AIM

```
server {
    listen 443 ssl http2;
    server_name app.iamaim.ru;
    # ... зеркало текущего конфига для всего AIM ...
}
```

## SSL

1. **DNS:** Добавить A-запись `app.iamaim.ru → 138.16.224.188`
2. **Сертификат:** Расширить существующий Let's Encrypt сертификат, добавив `app.iamaim.ru`:

```bash
docker run --rm \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v /opt/aim/AIM/ssl:/var/www/certbot \
  certbot/certbot certonly --webroot \
  --webroot-path=/var/www/certbot \
  --cert-name iamaim.ru \
  -d iamaim.ru -d www.iamaim.ru -d app.iamaim.ru
```

## После деплоя

1. Telegram webhook: обновить URL на `https://app.iamaim.ru/telegram/webhook`
2. WordPress: установить SEO-плагин (Rank Math / Yoast), тему, кеширование (WP Super Cache или Redis)
3. AIM фронтенд: обновить CORS/redirects если завязаны на `iamaim.ru`

## Риски

- **Swap 100%, RAM 78%** — два новых контейнера добавят нагрузку. Рассмотреть апгрейд RAM сервера или оптимизацию текущих контейнеров.
- **SSL renewal** — после расширения сертификата убедиться, что автообновление работает со всеми тремя доменами.
- **wp-admin доступ** — ограничен по IP, проверить что IP пользователя правильный.
