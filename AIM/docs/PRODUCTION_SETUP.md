# Production Setup Guide

Руководство по настройке AIM Agency для production окружения.

## Содержание

- [Требования](#требования)
- [Установка](#установка)
- [Конфигурация](#конфигурация)
- [API Ключи](#api-ключи)
- [Валидация](#валидация)
- [Запуск](#запуск)
- [Мониторинг](#мониторинг)
- [Troubleshooting](#troubleshooting)

## Требования

### Системные требования

- Python 3.11+
- SQLite 3.35+ (или PostgreSQL 14+)
- 2GB RAM минимум
- 10GB свободного места на диске

### API Аккаунты

**Обязательные:**
- Google Analytics 4 (GA4) - бесплатно
- SEMrush API - от $200/месяц
- Secret key для шифрования сессий

**Опциональные:**
- Yandex Metrica - бесплатно (для российского рынка)
- Ahrefs API - от $500/месяц (fallback для SEMrush)
- HH API - бесплатно (для HR аналитики)
- PageSpeed Insights API - бесплатно, 25K запросов/день

## Установка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd !meAI
```

### 2. Создание виртуального окружения

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# или
venv\Scripts\activate  # Windows
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Создание директорий

```bash
mkdir -p AIM/data
mkdir -p AIM/obsidian
```

## Конфигурация

### 1. Создание .env файла

```bash
cp AIM/.env.example AIM/.env
```

### 2. Редактирование .env

Откройте `AIM/.env` и настройте следующие параметры:

#### Google Analytics 4 (Обязательно)

```bash
# GA4 Property ID (найти в GA4 Admin > Property Settings)
GA4_PROPERTY_ID=123456789

# Путь к JSON файлу service account
GA4_SERVICE_ACCOUNT_FILE=/path/to/service-account.json

# ИЛИ JSON напрямую (для cloud deployments)
# GA4_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
```

**Как получить GA4 credentials:**
1. Перейдите в [Google Cloud Console](https://console.cloud.google.com)
2. Создайте новый проект или выберите существующий
3. Включите Google Analytics Data API
4. Создайте Service Account:
   - IAM & Admin > Service Accounts > Create Service Account
   - Скачайте JSON ключ
5. Добавьте Service Account в GA4:
   - GA4 Admin > Property Access Management
   - Add Users > введите email service account
   - Роль: Viewer

#### SEMrush API (Обязательно)

```bash
SEMRUSH_API_KEY=your_semrush_api_key_here
```

**Как получить:**
1. Зарегистрируйтесь на [SEMrush](https://www.semrush.com)
2. Подпишитесь на API план (от $200/месяц)
3. Account Settings > API > получите ключ

#### Secret Key (Обязательно)

```bash
# Сгенерируйте безопасный ключ
SECRET_KEY=$(openssl rand -hex 32)
```

#### Yandex Metrica (Опционально)

```bash
YANDEX_METRICA_COUNTER_ID=12345678
YANDEX_METRICA_ACCESS_TOKEN=your_oauth_token_here
```

**Как получить:**
1. Создайте счётчик в [Яндекс.Метрике](https://metrika.yandex.ru)
2. Получите OAuth токен:
   - Перейдите на [OAuth страницу](https://oauth.yandex.ru/authorize?response_type=token&client_id=YOUR_CLIENT_ID)
   - Разрешите доступ
   - Скопируйте токен из URL

#### Ahrefs API (Опционально)

```bash
AHREFS_API_KEY=your_ahrefs_api_key_here
```

**Как получить:**
1. Зарегистрируйтесь на [Ahrefs](https://ahrefs.com)
2. Подпишитесь на API план (от $500/месяц)
3. Account Settings > API > получите ключ

#### Database

```bash
# SQLite (по умолчанию)
DATABASE_URL=sqlite+aiosqlite:///./AIM/data/aim.db

# PostgreSQL (для production)
# DATABASE_URL=postgresql+asyncpg://user:password@localhost/aim
```

#### Obsidian Vaults

```bash
OBSIDIAN_BASE_PATH=./AIM/obsidian
```

#### Environment

```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

### 3. Rate Limiting (Опционально)

Настройте лимиты запросов для каждого API:

```bash
# GA4 API (10 запросов/сек по умолчанию)
GA4_RATE_LIMIT_CAPACITY=10
GA4_RATE_LIMIT_REFILL=1.0

# SEMrush API (10 запросов/сек по умолчанию)
SEMRUSH_RATE_LIMIT_CAPACITY=10
SEMRUSH_RATE_LIMIT_REFILL=1.0
```

### 4. Budget Control (Опционально)

Контроль расходов на API:

```bash
# Максимальная стоимость одного запроса (USD)
MAX_COST_USD=5.0

# Минимальное количество ключевых слов
MIN_KEYWORDS=100

# Минимальный объём поиска
MIN_VOLUME=10
```

### 5. Caching (Опционально)

```bash
# Время жизни кеша (секунды)
CACHE_TTL=3600

# Backend (memory или redis)
CACHE_BACKEND=memory

# Redis (если используется)
# REDIS_HOST=localhost
# REDIS_PORT=6379
# REDIS_DB=0
```

## Валидация

### Проверка конфигурации

```bash
python AIM/scripts/validate_env.py
```

Скрипт проверит:
- ✅ Наличие всех обязательных переменных
- ✅ Формат значений (числа, URL, пути к файлам)
- ✅ Существование файлов (service account JSON)
- ⚠️ Опциональные переменные (warnings)

### Проверка API connectivity

```bash
python AIM/scripts/validate_env.py --check-connectivity
```

Дополнительно проверит:
- 🌐 Подключение к GA4 API
- 🌐 Подключение к SEMrush API
- 🌐 Подключение к Ahrefs API (если настроен)

**Примеры вывода:**

✅ **Успешная валидация:**
```
================================================================================
Validation Summary
================================================================================

✓ All configuration checks passed!
```

❌ **Ошибки конфигурации:**
```
================================================================================
Validation Summary
================================================================================

✗ Found 2 error(s):
  • GA4_PROPERTY_ID is not set (GA4 property ID)
  • SECRET_KEY is not set (Secret key for session encryption)

✗ Configuration validation failed. Please fix the errors above.
ℹ See .env.example for configuration examples and documentation.
```

⚠️ **Warnings (опциональные настройки):**
```
================================================================================
Validation Summary
================================================================================

⚠ Found 3 warning(s):
  • YANDEX_METRICA_COUNTER_ID is not set (optional)
  • AHREFS_API_KEY is not set (optional)
  • OBSIDIAN_BASE_PATH: Directory does not exist (will be created)

✓ Configuration validation passed!
⚠ Some optional features are not configured.
```

## Запуск

### Development режим

```bash
# Активировать виртуальное окружение
source venv/bin/activate

# Запустить тесты
pytest AIM/tests/ -v

# Запустить сервер (TODO)
# uvicorn aim.main:app --reload
```

### Production режим

```bash
# Установить ENVIRONMENT=production в .env
ENVIRONMENT=production

# Запустить с gunicorn (TODO)
# gunicorn aim.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Мониторинг

### Логи

Логи записываются в:
- `stdout` (по умолчанию)
- Файл (если настроен `LOG_FILE`)

Формат логов:
```json
{
  "event": "api_request",
  "timestamp": "2026-05-14T14:47:23Z",
  "level": "info",
  "client": "semrush",
  "method": "expand_keywords",
  "duration_ms": 234,
  "status": "success"
}
```

### Метрики (Prometheus)

Доступные метрики:
- `api_requests_total` - Общее количество запросов
- `api_request_duration_seconds` - Длительность запросов
- `api_errors_total` - Количество ошибок
- `circuit_breaker_state` - Состояние circuit breaker
- `cache_hits_total` - Попадания в кеш
- `cache_misses_total` - Промахи кеша

### Health Check (TODO)

```bash
curl http://localhost:8000/health
```

Ответ:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "database": "ok",
    "ga4": "ok",
    "semrush": "ok"
  }
}
```

## Troubleshooting

### GA4 Authentication Failed

**Проблема:**
```
GA4 API: Connection failed - 403 Forbidden
```

**Решение:**
1. Проверьте, что Service Account добавлен в GA4 Property
2. Проверьте, что Google Analytics Data API включен в Cloud Console
3. Проверьте формат JSON файла (должен содержать `private_key`)

### SEMrush Rate Limit Exceeded

**Проблема:**
```
SEMrush API: HTTP 429 Too Many Requests
```

**Решение:**
1. Увеличьте `SEMRUSH_RATE_LIMIT_REFILL` в .env
2. Уменьшите `SEMRUSH_RATE_LIMIT_CAPACITY`
3. Проверьте лимиты вашего API плана

### Database Connection Error

**Проблема:**
```
sqlalchemy.exc.OperationalError: unable to open database file
```

**Решение:**
1. Проверьте, что директория `AIM/data/` существует
2. Проверьте права доступа к директории
3. Для PostgreSQL: проверьте, что сервер запущен

### Circuit Breaker Open

**Проблема:**
```
CircuitBreakerError: Circuit breaker is open
```

**Решение:**
1. Проверьте логи на предыдущие ошибки API
2. Подождите 60 секунд (reset timeout)
3. Проверьте connectivity к API
4. Если проблема повторяется, увеличьте `fail_max` в коде

### Cache Not Working

**Проблема:**
Кеш не сохраняет данные между запросами.

**Решение:**
1. Проверьте `ENABLE_CACHE=true` в .env
2. Для Redis: проверьте подключение к серверу
3. Проверьте `CACHE_TTL` (не слишком короткий?)
4. Проверьте логи на ошибки кеширования

## Стоимость API

### SEMrush

- **План:** API Subscription
- **Стоимость:** $200-500/месяц
- **Лимиты:** 40,000 запросов/день
- **Цена за запрос:** ~$0.01

### Ahrefs

- **План:** API Subscription
- **Стоимость:** $500-1000/месяц
- **Лимиты:** Зависит от плана
- **Цена за запрос:** ~$0.02

### Google Analytics 4

- **Стоимость:** Бесплатно
- **Лимиты:** 
  - 25,000 запросов/день (standard)
  - 200,000 запросов/день (Analytics 360)

### PageSpeed Insights

- **Стоимость:** Бесплатно
- **Лимиты:** 25,000 запросов/день

### Yandex Metrica

- **Стоимость:** Бесплатно
- **Лимиты:** 10,000 запросов/день

## Безопасность

### Защита API ключей

1. **Никогда не коммитьте .env файл в git**
   - `.env` уже в `.gitignore`
   - Используйте `.env.example` для документации

2. **Используйте переменные окружения в production**
   ```bash
   export GA4_PROPERTY_ID=123456789
   export SEMRUSH_API_KEY=xxx
   ```

3. **Ротация ключей**
   - Меняйте API ключи каждые 90 дней
   - Меняйте SECRET_KEY при компрометации

4. **Ограничение доступа**
   - Используйте IP whitelist для API (если доступно)
   - Ограничьте права Service Account в GA4

### HTTPS

В production всегда используйте HTTPS:
```bash
# Nginx reverse proxy
server {
    listen 443 ssl;
    server_name iamaim.ru;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
    }
}
```

## Backup

### База данных

```bash
# SQLite backup
cp AIM/data/aim.db AIM/data/aim.db.backup

# PostgreSQL backup
pg_dump aim > aim_backup.sql
```

### Obsidian vaults

```bash
# Backup всех vaults
tar -czf obsidian_backup.tar.gz AIM/obsidian/
```

### Конфигурация

```bash
# Backup .env (без коммита в git!)
cp AIM/.env AIM/.env.backup
```

## Масштабирование

### Horizontal Scaling

Для масштабирования на несколько инстансов:

1. **Используйте PostgreSQL вместо SQLite**
   ```bash
   DATABASE_URL=postgresql+asyncpg://user:password@db-server/aim
   ```

2. **Используйте Redis для кеша**
   ```bash
   CACHE_BACKEND=redis
   REDIS_HOST=redis-server
   ```

3. **Load Balancer**
   ```
   nginx -> [instance1, instance2, instance3]
   ```

### Vertical Scaling

Для увеличения производительности одного инстанса:

1. **Увеличьте workers**
   ```bash
   gunicorn aim.main:app -w 8
   ```

2. **Увеличьте connection pool**
   ```bash
   DATABASE_POOL_SIZE=20
   DATABASE_MAX_OVERFLOW=40
   ```

3. **Оптимизируйте кеш**
   ```bash
   CACHE_TTL=7200  # 2 часа
   ```

## Поддержка

- **Документация:** `AIM/docs/`
- **Issues:** GitHub Issues
- **Email:** support@iamaim.ru

## Changelog

### v1.0.0 (2026-05-14)

- ✅ GA4 API integration
- ✅ SEMrush API integration
- ✅ Ahrefs API integration (fallback)
- ✅ Traffic Analyzer subagent
- ✅ Conversion Tracker subagent
- ✅ Environment validation script
- ✅ Production setup documentation
