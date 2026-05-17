# E2E Test Fix Memo - 2026-05-17

## Проблема
E2E тесты падают с ошибкой `no such table: leads` и другими проблемами.

## Корневая причина
Было **два разных Base объекта**:
1. `aim.database.Base` (использовался в тестах)
2. `aim.storage.models.Base` (использовался в моделях Lead, Payment, Document, Onboarding)

## Что уже исправлено ✅

### 1. Унификация Base (КРИТИЧНО!)
**Файл:** `src/aim/database.py`

```python
# БЫЛО (НЕПРАВИЛЬНО):
from sqlalchemy.orm import declarative_base
Base = declarative_base()

# СТАЛО (ПРАВИЛЬНО):
from aim.storage.models import Base  # Единый источник истины
```

### 2. Импорт моделей в conftest.py
**Файл:** `tests/conftest.py`

Добавлены импорты ПОСЛЕ импорта Base:
```python
from aim.database import Base
from aim.main import app

# Import all models to register them with Base.metadata
from aim.models.lead import Lead  # noqa: F401
from aim.models.linear_task import LinearTask  # noqa: F401
from aim.models.email_workflow import EmailWorkflow  # noqa: F401
from aim.models.scheduled_email import ScheduledEmail  # noqa: F401
from aim.models.email_event import EmailEvent  # noqa: F401
from aim.models.email_template import EmailTemplate  # noqa: F401
from aim.models.payment import Payment  # noqa: F401
from aim.models.document import Document  # noqa: F401
from aim.models.onboarding import Onboarding  # noqa: F401
```

### 3. Фикстуры в conftest.py
**Файл:** `tests/conftest.py`

```python
@pytest.fixture
async def client(db, encryption_key):
    """Create async HTTP client for API testing."""
    from aim.database import get_db

    # Override get_db dependency to use test database
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Clean up
    app.dependency_overrides.clear()

@pytest.fixture
def mock_recaptcha():
    """Mock reCAPTCHA verification for tests."""
    with patch("aim.services.lead_capture.LeadCaptureService._verify_recaptcha") as mock:
        mock.return_value = AsyncMock(return_value=None)
        yield mock
```

### 4. API endpoint исправления
**Файл:** `src/aim/api/leads.py`

```python
# Добавлен import os
import os

# Исправлен get_lead_service
def get_lead_service(db: AsyncSession = Depends(get_db)) -> LeadCaptureService:
    """Dependency to get LeadCaptureService instance."""
    recaptcha_secret = os.getenv("RECAPTCHA_SECRET_KEY", "test_secret_key")
    return LeadCaptureService(db, recaptcha_secret=recaptcha_secret)

# Исправлен capture_lead endpoint
result = await service.capture_lead(
    request=request,  # Передаём request объект, не dict
    client_ip=client_ip,
)
```

### 5. Тестовые данные
**Файл:** `tests/e2e/test_lead_capture_flow.py`

Все тесты обновлены с обязательными полями:
```python
form_data = {
    "name": "Dr. Иван Петров",
    "email": "ivan.petrov@clinic-premium.ru",
    "phone": "+79991234567",
    "clinic_name": "Премиум Клиника",
    "specialty": "dentistry",  # ОБЯЗАТЕЛЬНО
    "city": "Москва",
    "services": ["implants", "orthodontics", "surgery"],
    "monthly_budget": 500000,
    "current_marketing": ["yandex_direct", "instagram", "seo"],
    "pain_points": ["low_conversion", "high_cpc", "no_analytics"],
    "fz152_consent": True,  # ОБЯЗАТЕЛЬНО
    "recaptcha_token": "test_token_hot_lead",  # ОБЯЗАТЕЛЬНО
    "utm_source": "yandex",
    "utm_medium": "cpc",
    "utm_campaign": "dental_implants_moscow",
}
```

## Что ещё нужно исправить ❌

### 1. API endpoint возвращает Pydantic объект, не dict
**Проблема:** `'LeadCaptureResponse' object is not subscriptable`

**Файл:** `src/aim/api/leads.py`

```python
# СЕЙЧАС (НЕПРАВИЛЬНО):
return LeadCaptureResponse(
    lead_id=result["lead_id"],  # result - это Pydantic объект!
    tier=result["tier"],
    score=result["score"],
    message="Лид успешно создан",
)

# НУЖНО (ПРАВИЛЬНО):
return LeadCaptureResponse(
    lead_id=result.lead_id,  # Доступ через атрибуты
    tier=result.tier,
    score=result.score,
    message=result.message,
)
```

### 2. Сервис должен возвращать dict с tier и score
**Проблема:** `LeadCaptureService.capture_lead()` возвращает `LeadCaptureResponse`, но в нём нет `tier` и `score`.

**Решение:** Либо изменить возвращаемый тип сервиса на dict, либо добавить поля в `LeadCaptureResponse`.

**Вариант 1 (проще):** Изменить API endpoint
```python
# В src/aim/api/leads.py
result = await service.capture_lead(
    request=request,
    client_ip=client_ip,
)

# result уже LeadCaptureResponse, просто вернуть его
return result
```

**Вариант 2:** Добавить tier и score в LeadCaptureResponse
```python
# В src/aim/schemas/lead.py
class LeadCaptureResponse(BaseModel):
    success: bool = True
    lead_id: str
    message: str
    estimated_response_time: str
    tier: Optional[str] = None  # Добавить
    score: Optional[float] = None  # Добавить
```

### 3. Транзакции закрываются преждевременно
**Проблема:** `This transaction is closed`

**Причина:** `db_session` fixture использует `async with session:` который автоматически коммитит/роллбэкит при выходе.

**Решение:** Убрать автоматический commit в фикстуре
```python
# В tests/conftest.py
@pytest.fixture
async def db_session(encryption_key):
    """Create async database session for tests."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # ИЗМЕНИТЬ ЭТО:
    async with async_session_factory() as session:
        yield session
        # Не делать commit/rollback автоматически
        # Пусть тесты сами управляют транзакциями

    await engine.dispose()
```

## Быстрый запуск после перезапуска сессии

```bash
cd /Users/mikhaileliseev/Desktop/Dev/!meAI/AIM
source venv/bin/activate

# Проверить что Base унифицирован
grep "from aim.storage.models import Base" src/aim/database.py

# Запустить один тест
python -m pytest tests/e2e/test_lead_capture_flow.py::test_hot_lead_capture_flow_end_to_end -xvs

# Запустить все E2E тесты
python -m pytest tests/e2e/test_lead_capture_flow.py -v
```

## Статус
- ✅ База данных создаётся (все 11 таблиц)
- ✅ Модели зарегистрированы в Base.metadata
- ✅ Фикстуры настроены
- ✅ Mock reCAPTCHA работает
- ❌ API endpoint возвращает неправильный формат
- ❌ Транзакции закрываются преждевременно

## Следующие шаги
1. Исправить API endpoint (вернуть result напрямую)
2. Добавить tier и score в LeadCaptureResponse
3. Исправить управление транзакциями в фикстуре
4. Запустить все 31 E2E тест
5. Закоммитить изменения

## Файлы для проверки
- `src/aim/database.py` - Base должен быть из storage.models
- `tests/conftest.py` - импорты моделей, фикстуры
- `src/aim/api/leads.py` - API endpoint
- `src/aim/schemas/lead.py` - LeadCaptureResponse schema
- `tests/e2e/test_lead_capture_flow.py` - тестовые данные
