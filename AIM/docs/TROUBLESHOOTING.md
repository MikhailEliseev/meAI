# Troubleshooting Guide

Руководство по решению типичных проблем при работе с AIM Testing Infrastructure.

## Содержание

- [Проблемы с тестами](#проблемы-с-тестами)
- [Проблемы с API](#проблемы-с-api)
- [Проблемы с окружением](#проблемы-с-окружением)
- [Проблемы с базой данных](#проблемы-с-базой-данных)
- [Проблемы с производительностью](#проблемы-с-производительностью)
- [Инструменты отладки](#инструменты-отладки)

---

## Проблемы с тестами

### Async Fixture Compatibility

**Проблема:**
```
PytestUnraisableExceptionWarning: Exception ignored in: <coroutine object 'async_fixture'>
RuntimeWarning: coroutine 'async_fixture' was never awaited
```

**Причина:** pytest-asyncio STRICT mode не совместим с некоторыми async fixtures.

**Решение 1:** Использовать `function` scope
```python
@pytest.fixture(scope="function")
async def event_bus():
    bus = EventBus()
    yield bus
    await bus.close()
```

**Решение 2:** Использовать `session` scope
```python
@pytest.fixture(scope="session")
async def event_store():
    store = EventStore()
    await store.initialize()
    yield store
    await store.close()
```

**Решение 3:** Отключить STRICT mode в `pytest.ini`
```ini
[pytest]
asyncio_mode = auto
```

---

### Import Errors

**Проблема:**
```
ModuleNotFoundError: No module named 'aim'
ImportError: attempted relative import with no known parent package
```

**Причина:** Python не находит модули проекта.

**Решение 1:** Добавить `__init__.py` файлы
```bash
# Проверить наличие __init__.py
find AIM/src -type d -exec test -f {}/__init__.py \; -print

# Создать недостающие
touch AIM/src/aim/__init__.py
touch AIM/src/aim/subagents/__init__.py
```

**Решение 2:** Установить проект в editable mode
```bash
cd AIM
pip install -e .
```

**Решение 3:** Добавить в PYTHONPATH
```bash
export PYTHONPATH="${PYTHONPATH}:${PWD}/AIM/src"
```

---

### Flaky Tests

**Проблема:** Тесты проходят/падают случайным образом.

**Причина:** Недетерминированное поведение (время, random, race conditions).

**Решение 1:** Заморозить время с `freezegun`
```python
from freezegun import freeze_time

@freeze_time("2026-05-15 12:00:00")
async def test_time_dependent():
    result = await generate_report()
    assert result.timestamp == datetime(2026, 5, 15, 12, 0, 0)
```

**Решение 2:** Мокировать random
```python
@pytest.fixture
def mock_random(monkeypatch):
    monkeypatch.setattr("random.random", lambda: 0.5)
```

**Решение 3:** Добавить таймауты
```python
@pytest.mark.timeout(5)
async def test_with_timeout():
    result = await long_running_operation()
    assert result is not None
```

---

### Mock Data Issues

**Проблема:** Моки не работают или возвращают неправильные данные.

**Причина:** Неправильная настройка monkeypatch или неполные mock объекты.

**Решение 1:** Проверить путь для monkeypatch
```python
# ❌ НЕПРАВИЛЬНО - мокируем не там
monkeypatch.setattr("semrush.SEMrushClient.expand_keywords", mock_expand)

# ✅ ПРАВИЛЬНО - полный путь
monkeypatch.setattr(
    "aim.subagents.api_clients.semrush.SEMrushClient.expand_keywords",
    mock_expand
)
```

**Решение 2:** Убедиться что mock объекты полные
```python
# ❌ НЕПРАВИЛЬНО - неполный объект
mock_keyword = {"keyword": "test"}

# ✅ ПРАВИЛЬНО - все обязательные поля
mock_keyword = KeywordData(
    keyword="test",
    volume=1000,
    cpc=5.0,
    difficulty=0.5,
    intent="commercial"
)
```

---

### Test Coverage Issues

**Проблема:** Coverage ниже порога (60%).

**Причина:** Не все ветки кода покрыты тестами.

**Решение 1:** Найти непокрытые строки
```bash
pytest tests/ --cov=src/aim --cov-report=term-missing
```

**Решение 2:** Добавить тесты для edge cases
```python
# Тестировать не только happy path
async def test_expand_keywords_empty_seed():
    with pytest.raises(ValueError):
        await client.expand_keywords("")

async def test_expand_keywords_zero_volume():
    keywords = await client.expand_keywords("test", min_volume=0)
    assert len(keywords) > 0
```

**Решение 3:** Исключить файлы из coverage
```ini
# .coveragerc
[run]
omit =
    */tests/*
    */test_*.py
    */__init__.py
```

---

## Проблемы с API

### Rate Limit Errors

**Проблема:**
```
httpx.HTTPStatusError: 429 Too Many Requests
RateLimitError: API rate limit exceeded
```

**Причина:** Превышен лимит запросов к API.

**Решение 1:** Увеличить capacity rate limiter
```python
# .env
RATE_LIMIT_CAPACITY=20  # Было 10
RATE_LIMIT_REFILL=2.0   # Было 1.0
```

**Решение 2:** Добавить задержку между запросами
```python
import asyncio

for keyword in keywords:
    result = await client.expand_keywords(keyword)
    await asyncio.sleep(1)  # 1 секунда между запросами
```

**Решение 3:** Использовать кеш
```python
# Кеш на 1 час
@cached(ttl=3600)
async def expand_keywords(seed: str):
    return await client.expand_keywords(seed)
```

---

### Authentication Errors

**Проблема:**
```
httpx.HTTPStatusError: 401 Unauthorized
AuthenticationError: Invalid API key
```

**Причина:** Неправильный или отсутствующий API ключ.

**Решение 1:** Проверить .env файл
```bash
# Проверить что ключ установлен
cat AIM/.env | grep SEMRUSH_API_KEY

# Проверить что нет пробелов
SEMRUSH_API_KEY=abc123  # ✅ Правильно
SEMRUSH_API_KEY= abc123 # ❌ Пробелы
```

**Решение 2:** Проверить валидность ключа
```python
# Тестовый запрос
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get(
        "https://api.semrush.com/analytics/v1/",
        params={"key": "YOUR_KEY", "type": "domain_ranks"}
    )
    print(response.status_code)  # Должно быть 200
```

**Решение 3:** Обновить ключ
```bash
# Получить новый ключ на semrush.com
# Обновить .env
echo "SEMRUSH_API_KEY=new_key_here" >> AIM/.env
```

---

### Timeout Errors

**Проблема:**
```
httpx.TimeoutException: Request timeout
asyncio.TimeoutError: Task timed out
```

**Причина:** API не отвечает в течение таймаута.

**Решение 1:** Увеличить таймаут
```python
client = httpx.AsyncClient(timeout=30.0)  # Было 10.0
```

**Решение 2:** Добавить retry
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def fetch_with_retry():
    return await client.get(url)
```

**Решение 3:** Использовать fallback
```python
try:
    result = await primary_api.fetch()
except httpx.TimeoutException:
    logger.warning("Primary API timeout, using fallback")
    result = await fallback_api.fetch()
```

---

### Circuit Breaker Opens

**Проблема:**
```
CircuitBreakerError: Circuit breaker is open
```

**Причина:** Слишком много ошибок, circuit breaker открылся.

**Решение 1:** Проверить логи
```python
import structlog
logger = structlog.get_logger()

# Найти причину ошибок
logger.info("circuit_breaker_opened", fail_count=5, errors=errors)
```

**Решение 2:** Увеличить fail_max
```python
breaker = CircuitBreaker(
    fail_max=10,  # Было 5
    reset_timeout=60
)
```

**Решение 3:** Дождаться reset_timeout
```python
# Circuit breaker автоматически закроется через reset_timeout
await asyncio.sleep(60)  # Подождать 60 секунд
```

---

## Проблемы с окружением

### Virtual Environment Issues

**Проблема:** Пакеты не найдены или неправильная версия Python.

**Причина:** Virtual environment не активирован или поврежден.

**Решение 1:** Активировать venv
```bash
# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

# Проверить
which python  # Должно быть .../venv/bin/python
```

**Решение 2:** Пересоздать venv
```bash
# Удалить старый
rm -rf venv

# Создать новый
python3.11 -m venv venv
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt
```

**Решение 3:** Проверить версию Python
```bash
python --version  # Должно быть 3.11+
```

---

### Dependency Conflicts

**Проблема:**
```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed
ERROR: Cannot install package-a and package-b because these package versions have conflicting dependencies
```

**Причина:** Конфликт версий зависимостей.

**Решение 1:** Обновить pip
```bash
pip install --upgrade pip setuptools wheel
```

**Решение 2:** Установить с --force-reinstall
```bash
pip install --force-reinstall -r requirements.txt
```

**Решение 3:** Использовать pip-tools
```bash
pip install pip-tools
pip-compile requirements.in
pip-sync requirements.txt
```

---

### Environment Variables Not Loaded

**Проблема:** Переменные из .env не загружаются.

**Причина:** .env файл не в правильном месте или не загружен.

**Решение 1:** Проверить расположение .env
```bash
# .env должен быть в AIM/
ls -la AIM/.env

# Проверить содержимое
cat AIM/.env
```

**Решение 2:** Загрузить явно
```python
from dotenv import load_dotenv
import os

# Загрузить из конкретного файла
load_dotenv("AIM/.env")

# Проверить
print(os.getenv("SEMRUSH_API_KEY"))
```

**Решение 3:** Использовать python-dotenv
```bash
pip install python-dotenv
```

---

## Проблемы с базой данных

### Database Locked

**Проблема:**
```
sqlite3.OperationalError: database is locked
```

**Причина:** Другой процесс держит блокировку базы.

**Решение 1:** Закрыть все соединения
```python
# Явно закрыть все соединения
await engine.dispose()
```

**Решение 2:** Увеличить таймаут
```python
engine = create_async_engine(
    "sqlite+aiosqlite:///./data/meai.db",
    connect_args={"timeout": 30}  # Было 5
)
```

**Решение 3:** Использовать WAL mode
```python
engine = create_async_engine(
    "sqlite+aiosqlite:///./data/meai.db",
    connect_args={"check_same_thread": False}
)

# Включить WAL
async with engine.begin() as conn:
    await conn.execute(text("PRAGMA journal_mode=WAL"))
```

---

### Migration Errors

**Проблема:**
```
alembic.util.exc.CommandError: Can't locate revision identified by 'abc123'
```

**Причина:** Несоответствие версий миграций.

**Решение 1:** Проверить текущую версию
```bash
alembic current
alembic history
```

**Решение 2:** Откатить и применить заново
```bash
alembic downgrade base
alembic upgrade head
```

**Решение 3:** Пересоздать базу
```bash
# ВНИМАНИЕ: Удалит все данные!
rm data/meai.db
alembic upgrade head
```

---

### Schema Mismatch

**Проблема:**
```
sqlalchemy.exc.OperationalError: no such column: tasks.new_column
```

**Причина:** Схема базы не соответствует моделям.

**Решение 1:** Создать миграцию
```bash
alembic revision --autogenerate -m "Add new_column"
alembic upgrade head
```

**Решение 2:** Проверить модели
```python
# Убедиться что модель определена
class Task(Base):
    __tablename__ = "tasks"
    new_column = Column(String)  # Должно быть определено
```

---

## Проблемы с производительностью

### Slow Tests

**Проблема:** Тесты выполняются слишком долго (> 1 минута).

**Причина:** Медленные операции или слишком много тестов.

**Решение 1:** Найти медленные тесты
```bash
pytest tests/ --durations=10
```

**Решение 2:** Запустить параллельно
```bash
pip install pytest-xdist
pytest tests/ -n auto  # Использовать все CPU
```

**Решение 3:** Оптимизировать fixtures
```python
# Использовать session scope для дорогих fixtures
@pytest.fixture(scope="session")
async def expensive_fixture():
    # Создаётся один раз на всю сессию
    return await create_expensive_resource()
```

---

### High Memory Usage

**Проблема:** Тесты потребляют много памяти (> 1 GB).

**Причина:** Утечки памяти или большие объекты в памяти.

**Решение 1:** Профилировать память
```bash
pip install memory_profiler
python -m memory_profiler tests/test_file.py
```

**Решение 2:** Очищать кеш
```python
@pytest.fixture(autouse=True)
async def clear_cache():
    yield
    await cache.clear()
```

**Решение 3:** Использовать генераторы
```python
# ❌ НЕПРАВИЛЬНО - всё в памяти
keywords = [await fetch(kw) for kw in seed_keywords]

# ✅ ПРАВИЛЬНО - по одному
async for keyword in fetch_keywords(seed_keywords):
    process(keyword)
```

---

### API Cost Overruns

**Проблема:** Превышен бюджет на API запросы.

**Причина:** Слишком много запросов или неэффективное использование.

**Решение 1:** Включить budget guard
```python
# .env
MAX_COST_USD=5.0  # Максимальная стоимость
```

**Решение 2:** Использовать кеш агрессивнее
```python
# Увеличить TTL кеша
CACHE_TTL=7200  # 2 часа вместо 1
```

**Решение 3:** Батчить запросы
```python
# Вместо 100 запросов по 1 keyword
for keyword in keywords:
    await client.expand_keywords(keyword)

# Один запрос на 100 keywords
await client.expand_keywords_batch(keywords)
```

---

## Инструменты отладки

### Pytest Debugging

**Запуск с отладкой:**
```bash
# Показать print statements
pytest tests/ -s

# Остановиться на первой ошибке
pytest tests/ -x

# Запустить последние упавшие тесты
pytest tests/ --lf

# Показать локальные переменные при ошибке
pytest tests/ -l

# Войти в debugger при ошибке
pytest tests/ --pdb
```

**Verbose output:**
```bash
# Подробный вывод
pytest tests/ -vv

# Показать все assert детали
pytest tests/ -vv --tb=long
```

---

### Logging

**Включить логи в тестах:**
```python
import structlog

# Настроить логирование
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ]
)

logger = structlog.get_logger()
logger.info("test_started", test_name="test_example")
```

**Логи в файл:**
```python
import logging

logging.basicConfig(
    filename="tests.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

---

### Profiling

**Профилирование времени:**
```bash
pip install pytest-profiling
pytest tests/ --profile
```

**Профилирование памяти:**
```bash
pip install memory_profiler
python -m memory_profiler tests/test_file.py
```

**Профилирование CPU:**
```bash
pip install py-spy
py-spy record -o profile.svg -- pytest tests/
```

---

### Interactive Debugging

**IPython debugger:**
```python
import ipdb

async def test_example():
    result = await some_function()
    ipdb.set_trace()  # Остановиться здесь
    assert result is not None
```

**PDB debugger:**
```python
import pdb

async def test_example():
    result = await some_function()
    pdb.set_trace()  # Остановиться здесь
    assert result is not None
```

---

## Получение помощи

### Документация
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [httpx Documentation](https://www.python-httpx.org/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)

### Логи и метрики
- Проверить `tests.log` для детальных логов
- Использовать `--tb=long` для полных traceback
- Запустить с `-vv` для verbose output

### Контакты
- **Email:** contact@iamaim.ru
- **Issues:** GitHub Issues
- **Discussions:** GitHub Discussions

---

**Last Updated:** 2026-05-15  
**Version:** 1.0  
**Maintainer:** Mikhail Eliseev
