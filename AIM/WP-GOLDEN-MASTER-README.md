# WordPress Golden Master — Эталонный дизайн

**Дата:** 2026-06-28 02:53 МСК
**Источник:** Production сервер после отката на 2 дня назад
**Архив:** `AIM/wp-golden-master.tar.gz` (8.5 MB)

## Что это

Это **эталонная версия WordPress темы AIM** с правильным дизайном, которая работала на production до Phase 09. Используй этот архив как референс для всех будущих изменений в дизайне.

## Содержимое

### Ключевые файлы дизайна:
- **design-showcase-dual-theme.html** (102 KB) — ЕДИНСТВЕННЫЙ источник истины для дизайна
- **theme.css** — CSS переменные для dual theme (light/dark)
- **front-page.php** (24 KB) — главная страница
- **header.php** (8.2 KB) — шапка с theme toggle
- **footer.php** (8.4 KB) — футер

### Чат виджеты:
- **chat-inline.php** (53 KB) — основной чат виджет от 26 июня 02:04
- **chat-inline-pro.php** (22 KB) — PRO версия с phase tracker (из Phase 09, НЕ эталон)
- **aim-pro-endpoints.php** (6.1 KB) — REST endpoints для fallback формы

### Бэкапы:
- **chat-inline.php.backup-before-pro** (50 KB, 26 июня 01:59) — последняя версия ДО Phase 09
- **chat-inline.php.backup-1781787857** (48 KB, 18 июня) — более старая версия
- **functions.php.bak** (11 KB) — backup functions.php

### Структура:
```
assets/         — статические файлы
chat/           — чат компоненты
docs/           — документация
```

## Как использовать

### Восстановление эталонного дизайна:
```bash
# На сервере
docker cp aim-wordpress:/var/www/html/wp-content/themes/aim-theme aim-theme-backup
tar xzf wp-golden-master.tar.gz -C /tmp/aim-theme-golden
docker cp /tmp/aim-theme-golden/. aim-wordpress:/var/www/html/wp-content/themes/aim-theme/
docker exec aim-wordpress chown -R www-data:www-data /var/www/html/wp-content/themes/aim-theme
```

### Извлечение конкретных файлов:
```bash
tar xzf wp-golden-master.tar.gz design-showcase-dual-theme.html
tar xzf wp-golden-master.tar.gz theme.css
tar xzf wp-golden-master.tar.gz chat-inline.php.backup-before-pro
```

## Важно

- **design-showcase-dual-theme.html** — КАНОНИЧЕСКИЙ референс дизайна
- Любые изменения дизайна сверяй с этим файлом
- `chat-inline-pro.php` и `aim-pro-endpoints.php` — это из Phase 09, они НЕ эталон
- Эталонный чат: `chat-inline.php.backup-before-pro` (версия ДО Phase 09)

## История

1. **До 26 июня 01:59** — стабильная версия (backup-before-pro)
2. **26 июня 02:04-02:12** — добавлены PRO компоненты Phase 09
3. **27 июня 23:33** — откат Phase 09 WordPress (но PRO файлы остались)
4. **28 июня 00:50** — откат сервера на 2 дня назад
5. **28 июня 02:53** — создан этот golden master бэкап

## Состояние на момент бэкапа

✅ Сайт работает: https://iamaim.ru → 200 OK
✅ Дизайн эталонный: dual theme, glass cards, Playfair Display + Jost
✅ Все файлы на месте
❓ PRO компоненты присутствуют, но не активны (functions.php не подключает endpoints)
