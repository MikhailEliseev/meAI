# AI Sales Admin Agent - Спецификация

**Дата создания:** 2026-05-10  
**Версия:** 1.0  
**Статус:** Draft  
**Приоритет:** P1 (Важный)  
**Домен:** Social  
**Родительский Magister:** Social Magister

---

## 1. ОБЗОР

### 1.1 Назначение

**AI Sales Admin Agent** — виртуальный администратор клиники 24/7, который мониторит все каналы коммуникации, отвечает по протоколам и использует структурированную базу знаний из Obsidian Vault.

**Ключевые функции:**
- Мониторинг всех каналов (Telegram, Instagram, VK, WhatsApp, сайт)
- Мгновенный ответ на сообщения (< 30 секунд)
- Квалификация лидов (холодный → квали-лид)
- Запись на консультацию
- Эскалация менеджеру при необходимости
- Соблюдение 152-ФЗ (медицинские данные)

### 1.2 Роль в системе

**Тип:** Subagent (исполнитель)  
**Родительский Magister:** Social Magister  
**Домен:** Social (социальные сети и коммуникации)  
**Автономность:** Высокая (работает 24/7 без участия человека)

**Взаимодействие:**
- **Получает:** Настройки от Social Magister при setup
- **Отправляет:** Квали-лиды в CRM, уведомления менеджеру
- **Использует:** Obsidian Vault (база знаний), CRM API, каналы коммуникации

### 1.3 Уникальная ценность

**Почему критично для агентства:**

1. **Скорость = конверсия**
   - Ответ через 30 секунд вместо 5 минут
   - Клиент не уходит к конкуренту
   - Первый ответил = получил клиента

2. **24/7 доступность**
   - Клиенты пишут в любое время
   - Нет потерянных лидов из-за нерабочих часов
   - Конкуренты спят — мы работаем

3. **Омниканальность**
   - Один агент на все каналы
   - Единая история клиента
   - Нет дублирования работы

4. **Суперэкспертиза**
   - Знает всё о продуктах/ценах/врачах
   - Клиент получает точный ответ сразу
   - Нет "сейчас уточню"

5. **Квалификация лидов**
   - Превращает холодных в квали-лидов
   - Менеджер получает готовых клиентов
   - Экономия времени менеджера

6. **152-ФЗ compliance**
   - Соблюдает закон о персональных данных
   - Защита клиники от штрафов
   - Безопасная работа с медицинскими данными

### 1.4 Границы ответственности

**Что делает агент:**
- ✅ Мониторит все каналы коммуникации 24/7
- ✅ Отвечает на типовые вопросы (цены, услуги, врачи)
- ✅ Квалифицирует лидов (потребность, срочность, готовность)
- ✅ Записывает на консультацию (интеграция с календарём)
- ✅ Сохраняет всю историю в CRM (даже незначительные коммуникации)
- ✅ Эскалирует менеджеру при необходимости
- ✅ Обновляет базу знаний (мониторинг сайта)
- ✅ Соблюдает 152-ФЗ (медицинские данные → эскалация)

**Что НЕ делает агент:**
- ❌ Не имеет доступа к медицинским данным (152-ФЗ)
- ❌ Не может посмотреть историю болезни пациента
- ❌ Не принимает решения о лечении
- ❌ Не продаёт сложные услуги без менеджера (пока в backlog)
- ❌ Не работает с агрессивными пациентами (эскалация → блокировка)

---

## 2. ВХОДНЫЕ ДАННЫЕ

### 2.1 Источники данных

**Основные источники:**

1. **Obsidian Vault** — база знаний клиники
   - Продукты и услуги
   - Цены (актуальные)
   - Врачи и специалисты
   - Расписание
   - FAQ (типовые вопросы)

2. **Мониторинг сайта** — автоматическое обновление
   - WordPress REST API (`/wp-json/wp/v2/`)
   - Bitrix24 REST API
   - Schema.org парсинг
   - Playwright (fallback)

3. **CRM система** — история клиента
   - Предыдущие обращения
   - Статус лида
   - Записи на консультации

4. **Календарь** — свободные слоты
   - Google Calendar API
   - Яндекс.Календарь API

5. **Медицинские источники** — для сложных вопросов
   - Perplexity API
   - PubMed (опционально)

### 2.2 Обязательные параметры

**Pydantic модель:**

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class AISalesAdminConfig(BaseModel):
    """Конфигурация AI Sales Admin Agent"""
    
    # Проект
    project_id: str = Field(..., description="ID проекта (для изоляции)")
    project_url: str = Field(..., description="URL сайта клиники")
    
    # Каналы коммуникации
    channels: List[str] = Field(..., description="Список каналов: telegram, instagram, vk, whatsapp, website")
    
    # API ключи (зависят от выбранных каналов)
    telegram_bot_token: Optional[str] = Field(None, description="Токен Telegram бота")
    instagram_api_key: Optional[str] = Field(None, description="Ключ Instagram API")
    vk_api_key: Optional[str] = Field(None, description="Ключ VK API")
    whatsapp_api_key: Optional[str] = Field(None, description="Ключ WhatsApp Business API")
    website_chat_api_key: Optional[str] = Field(None, description="Ключ Website Chat API")
    
    # CRM
    crm_type: str = Field(..., description="Тип CRM: bitrix24, amocrm")
    crm_api_key: str = Field(..., description="Ключ CRM API")
    crm_webhook_url: Optional[str] = Field(None, description="Webhook для уведомлений")
    
    # Календарь
    calendar_type: str = Field(..., description="Тип календаря: google, yandex")
    calendar_api_key: str = Field(..., description="Ключ Calendar API")
    
    # AI
    openai_api_key: str = Field(..., description="Ключ OpenAI API")
    voice_enabled: bool = Field(False, description="Включить голосовое общение")
    assembly_ai_key: Optional[str] = Field(None, description="Ключ Assembly AI (если voice_enabled)")
    
    # Obsidian
    obsidian_vault_path: str = Field(..., description="Путь к Obsidian Vault")
```

### 2.3 Опциональные параметры

```python
class AISalesAdminOptionalConfig(BaseModel):
    """Опциональные параметры"""
    
    # Производительность
    response_time_target: int = Field(30, description="Целевое время ответа (секунды)")
    max_conversation_duration: int = Field(10, description="Максимальная длительность диалога (минуты)")
    
    # Эскалация
    escalation_keywords: List[str] = Field(
        default_factory=list,
        description="Ключевые слова для эскалации менеджеру"
    )
    working_hours: Dict[str, str] = Field(
        default_factory=dict,
        description="Рабочие часы менеджеров: {'start': '09:00', 'end': '18:00'}"
    )
    
    # Квалификация (настраивается при setup)
    qualification_questions: List[str] = Field(
        default_factory=list,
        description="Вопросы для квалификации лида"
    )
    qualification_criteria: Dict[str, any] = Field(
        default_factory=dict,
        description="Критерии квали-лида"
    )
    
    # ToV
    tone_of_voice_file: Optional[str] = Field(None, description="Путь к файлу ToV")
    
    # Мониторинг сайта
    site_monitoring_enabled: bool = Field(True, description="Включить мониторинг сайта")
    site_monitoring_schedule: str = Field("0 3 * * *", description="Расписание (cron)")
    
    # Fallback
    fallback_model: str = Field("deepseek", description="Fallback модель: deepseek, qwen")
```

### 2.4 Валидация входных данных

**Правила валидации:**

1. **project_id** — уникальный, только буквы/цифры/дефис
2. **project_url** — валидный URL, доступен по HTTPS
3. **channels** — минимум 1 канал, максимум 5
4. **API ключи** — обязательны для выбранных каналов
5. **crm_type** — только bitrix24 или amocrm
6. **calendar_type** — только google или yandex
7. **response_time_target** — от 10 до 120 секунд
8. **working_hours** — валидный формат времени (HH:MM)

**Ошибки валидации:**
- `INVALID_PROJECT_ID` — неверный формат project_id
- `INVALID_PROJECT_URL` — URL недоступен
- `MISSING_API_KEY` — не указан обязательный API ключ
- `INVALID_CRM_TYPE` — неподдерживаемый тип CRM
- `INVALID_WORKING_HOURS` — неверный формат рабочих часов

### 2.5 Дополнительные метаданные (ВАЖНО)

**Принцип:** Всё, что может агент раздобыть, должно подтягиваться в CRM.

**Источник:** Интервью, строка 199 — "Там есть стандартный набор: UTM-метки, геолокации и прочая информация, которая может подтягиваться в CRM-ку. Всё, что может агент раздобыть, надо подтягивать."

**Обязательные метаданные:**

1. **UTM-метки** (источник трафика):
   - `utm_source` — источник (google, yandex, instagram, direct)
   - `utm_medium` — канал (cpc, organic, social, referral)
   - `utm_campaign` — название кампании
   - `utm_content` — вариант объявления
   - `utm_term` — ключевое слово

2. **Геолокация** (откуда пишет пациент):
   - `geo_country` — страна (Россия)
   - `geo_city` — город (Москва, Санкт-Петербург)
   - `geo_region` — регион (Московская область)
   - Источник: IP-адрес → GeoIP база (MaxMind, ipapi.co)

3. **Устройство и браузер**:
   - `device_type` — тип устройства (mobile, desktop, tablet)
   - `device_os` — операционная система (iOS, Android, Windows, macOS)
   - `browser` — браузер (Chrome, Safari, Firefox)
   - `browser_version` — версия браузера
   - Источник: User-Agent заголовок

4. **Referrer** (откуда пришёл):
   - `referrer_url` — полный URL источника
   - `referrer_domain` — домен источника (google.com, instagram.com)
   - Источник: HTTP Referer заголовок

5. **Временные метки**:
   - `first_touch_time` — время первого касания (когда впервые написал)
   - `last_touch_time` — время последнего сообщения
   - `response_time` — время реакции агента (секунды)
   - `conversation_duration` — длительность диалога (минуты)

**Опциональные метаданные (если доступны):**

6. **Социальные профили**:
   - `telegram_username` — username в Telegram
   - `instagram_username` — username в Instagram
   - `vk_id` — ID пользователя VK
   - `profile_photo_url` — URL фото профиля

7. **Поведенческие данные**:
   - `pages_visited` — какие страницы сайта посетил (если есть tracking)
   - `time_on_site` — время на сайте до обращения
   - `previous_visits` — количество предыдущих визитов
   - `scroll_depth` — глубина прокрутки страницы

**Реализация:**

```python
class LeadMetadata(BaseModel):
    """Дополнительные метаданные лида"""
    
    # UTM-метки
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None
    utm_term: Optional[str] = None
    
    # Геолокация
    geo_country: Optional[str] = None
    geo_city: Optional[str] = None
    geo_region: Optional[str] = None
    geo_ip: Optional[str] = None
    
    # Устройство и браузер
    device_type: Optional[str] = None  # mobile/desktop/tablet
    device_os: Optional[str] = None
    browser: Optional[str] = None
    browser_version: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Referrer
    referrer_url: Optional[str] = None
    referrer_domain: Optional[str] = None
    
    # Временные метки
    first_touch_time: datetime
    last_touch_time: datetime
    response_time: int  # секунды
    conversation_duration: int  # минуты
    
    # Социальные профили (опционально)
    telegram_username: Optional[str] = None
    instagram_username: Optional[str] = None
    vk_id: Optional[str] = None
    profile_photo_url: Optional[str] = None
    
    # Поведенческие данные (опционально)
    pages_visited: Optional[List[str]] = None
    time_on_site: Optional[int] = None  # секунды
    previous_visits: Optional[int] = None
    scroll_depth: Optional[int] = None  # проценты

async def collect_metadata(message: Message) -> LeadMetadata:
    """Собрать все доступные метаданные"""
    
    metadata = LeadMetadata(
        first_touch_time=datetime.now(),
        last_touch_time=datetime.now(),
        response_time=0,
        conversation_duration=0,
    )
    
    # UTM-метки (из URL или сохранённые в сессии)
    if message.utm_params:
        metadata.utm_source = message.utm_params.get("utm_source")
        metadata.utm_medium = message.utm_params.get("utm_medium")
        metadata.utm_campaign = message.utm_params.get("utm_campaign")
        metadata.utm_content = message.utm_params.get("utm_content")
        metadata.utm_term = message.utm_params.get("utm_term")
    
    # Геолокация (из IP)
    if message.ip_address:
        geo = await get_geo_from_ip(message.ip_address)
        metadata.geo_country = geo.country
        metadata.geo_city = geo.city
        metadata.geo_region = geo.region
        metadata.geo_ip = message.ip_address
    
    # Устройство и браузер (из User-Agent)
    if message.user_agent:
        device_info = parse_user_agent(message.user_agent)
        metadata.device_type = device_info.device_type
        metadata.device_os = device_info.os
        metadata.browser = device_info.browser
        metadata.browser_version = device_info.browser_version
        metadata.user_agent = message.user_agent
    
    # Referrer
    if message.referrer:
        metadata.referrer_url = message.referrer
        metadata.referrer_domain = extract_domain(message.referrer)
    
    # Социальные профили
    if message.channel == "telegram":
        metadata.telegram_username = message.from_user.username
    elif message.channel == "instagram":
        metadata.instagram_username = message.from_user.username
    elif message.channel == "vk":
        metadata.vk_id = message.from_user.id
    
    return metadata
```

**Зачем это нужно:**

1. **Атрибуция** — понять, откуда пришёл лид (какая реклама сработала)
2. **Сегментация** — разделить лидов по городам, устройствам, источникам
3. **Оптимизация** — понять, какие каналы приносят лучших лидов
4. **Персонализация** — адаптировать общение под устройство и контекст
5. **Аналитика** — построить воронку от первого касания до продажи

**Метрики качества:**
- **Metadata coverage:** > 80% (процент лидов с полными метаданными)
- **Geo accuracy:** > 95% (точность определения города)
- **UTM preservation:** 100% (UTM-метки не теряются)

---

## 3. АЛГОРИТМ РАБОТЫ

### 3.1 Основные шаги

**Алгоритм (8 шагов):**

```
1. Получение сообщения
   ↓
2. Создание/обновление лида в CRM
   ↓
3. Быстрый ответ (< 30 секунд)
   ↓
4. Квалификация лида
   ↓
5. Ответ на вопросы (из базы знаний)
   ↓
6. Запись на консультацию (если квали-лид)
   ↓
7. Эскалация менеджеру (если необходимо)
   ↓
8. Сохранение истории (CRM + Obsidian)
```

**Детальное описание:**

**Шаг 1: Получение сообщения**
- Мониторинг всех подключённых каналов
- Webhook от Telegram/Instagram/VK/WhatsApp/сайта
- Парсинг сообщения (текст, голос, изображение)
- Определение типа сообщения (новый лид / существующий клиент)

**Шаг 2: Создание/обновление лида в CRM**
- Проверка: есть ли лид в CRM (по username/phone/email)
- Если нет → создать новый лид
- Если есть → обновить существующий
- Сохранить метаданные (канал, время, UTM-метки)

**Шаг 3: Быстрый ответ (< 30 секунд)**
- Приветствие (персонализированное, если есть имя)
- Подтверждение получения сообщения
- Установление контакта

**Шаг 4: Квалификация лида**
- Выяснить потребность (что беспокоит?)
- Определить срочность (когда нужна консультация?)
- Оценить готовность (готов записаться?)
- Классификация: cold/warm/hot/qualified

**Шаг 5: Ответ на вопросы**
- Поиск в базе знаний Obsidian
- Если нет ответа → поиск в медицинских источниках (Perplexity)
- Если всё равно нет → эскалация менеджеру

**Шаг 6: Запись на консультацию**
- Проверка свободных слотов в календаре
- Предложение времени
- Подтверждение записи
- Отправка подтверждения (SMS/email)

**Шаг 7: Эскалация менеджеру**
- Триггеры: медицинские данные, сложный вопрос, горячий лид
- Уведомление менеджера (CRM + Telegram/email)
- Передача контекста диалога

**Шаг 8: Сохранение истории**
- CRM: полная история диалога + метаданные
- Obsidian: копия для аналитики + неотвеченные вопросы

### 3.2 Специфичная логика

**1. Скорость ответа < 30 секунд**
- Критично для конверсии
- Мониторинг в реальном времени
- Приоритет: новые сообщения > продолжение диалога

**2. Деликатный ToV (медицинская специфика)**
- Без давления и агрессивных продаж
- Эмпатия и понимание
- Профессиональный, но дружелюбный тон
- Использование ToV из Tone of Voice Agent

**3. Квалификация через вопросы**
- Настраивается при setup под каждый проект
- Методы: BANT, SPIN, или кастомные
- Деликатно, без допроса
- Естественный диалог

**4. Автоматическая запись в CRM**
- Все коммуникации, даже незначительные
- Даже если пациент просто поздоровался
- Полная история для менеджера

**5. 152-ФЗ compliance (КРИТИЧНО)**

**Триггеры эскалации (медицинские данные):**
- "я уже у вас был"
- "посмотрите мою историю"
- "мои анализы"
- "что мне назначали"
- "мои результаты"
- "моя карта"
- "мои записи"

**Действие:**
- Немедленная эскалация менеджеру (без попыток ответить)
- Сообщение пациенту: "Сейчас соединю вас с администратором, который сможет посмотреть вашу историю"
- Логирование запроса (для аудита 152-ФЗ)

**6. Настройка при setup (индивидуально для каждого проекта)**
- Критерии квали-лида (что считать "горячим")
- Правила эскалации менеджеру (когда передавать)
- Вопросы для квалификации
- Рабочие часы менеджеров
- ToV и стиль общения

**7. Приоритеты мониторинга сайта (ВАЖНО)**

**Проблема:** Playwright не даёт чёткой информации о ценах и услугах.

**Источник:** Интервью, строка 127 — "мониторинг через Playwright не даёт прям чёткой информации. Возможно, стоит подумать и добавить какой-нибудь скрипт, который чисто по коду или API будет вытаскивать информацию. Например, если это WordPress или Bitrix, то можно получить чистый прайс по элементам и следить за изменениями."

**Приоритеты (от лучшего к худшему):**

**Приоритет 1: REST API (РЕКОМЕНДУЕТСЯ)**

Прямой доступ к структурированным данным через API CMS.

**WordPress REST API:**
```python
async def fetch_wordpress_prices(site_url: str) -> List[Service]:
    """Получить услуги и цены через WordPress REST API"""
    
    # Получить все страницы услуг
    pages_url = f"{site_url}/wp-json/wp/v2/pages?per_page=100"
    pages = await fetch_json(pages_url)
    
    # Получить кастомные типы постов (если есть)
    services_url = f"{site_url}/wp-json/wp/v2/services?per_page=100"
    services = await fetch_json(services_url)
    
    # Получить WooCommerce продукты (если используется)
    products_url = f"{site_url}/wp-json/wc/v3/products?per_page=100"
    products = await fetch_json(products_url)
    
    # Парсить цены из контента
    all_services = []
    for item in pages + services + products:
        service = parse_service_from_content(item)
        if service:
            all_services.append(service)
    
    return all_services
```

**Bitrix24 REST API:**
```python
async def fetch_bitrix_prices(site_url: str, api_key: str) -> List[Service]:
    """Получить услуги и цены через Bitrix24 REST API"""
    
    # Получить каталог товаров/услуг
    catalog_url = f"{site_url}/rest/{api_key}/crm.product.list"
    products = await fetch_json(catalog_url)
    
    # Получить цены
    all_services = []
    for product in products["result"]:
        service = Service(
            id=product["ID"],
            name=product["NAME"],
            price=float(product["PRICE"]),
            currency=product["CURRENCY_ID"],
            description=product["DESCRIPTION"],
            category=product["SECTION_ID"],
        )
        all_services.append(service)
    
    return all_services
```

**Преимущества:**
- ✅ Структурированные данные (JSON)
- ✅ Точные цены (из базы данных)
- ✅ Быстро (нет рендеринга страниц)
- ✅ Надёжно (официальный API)
- ✅ Легко отслеживать изменения (сравнение JSON)

**Приоритет 2: Schema.org парсинг**

Извлечение структурированных данных из HTML (если есть микроразметка).

```python
async def fetch_schema_org_prices(site_url: str) -> List[Service]:
    """Получить услуги через Schema.org микроразметку"""
    
    # Получить HTML страницы
    html = await fetch_html(f"{site_url}/services")
    
    # Найти JSON-LD блоки
    soup = BeautifulSoup(html, "html.parser")
    scripts = soup.find_all("script", type="application/ld+json")
    
    all_services = []
    for script in scripts:
        data = json.loads(script.string)
        
        # Парсить Service или Product
        if data.get("@type") in ["Service", "Product", "MedicalProcedure"]:
            service = Service(
                name=data.get("name"),
                price=float(data.get("offers", {}).get("price", 0)),
                currency=data.get("offers", {}).get("priceCurrency", "RUB"),
                description=data.get("description"),
            )
            all_services.append(service)
    
    return all_services
```

**Преимущества:**
- ✅ Структурированные данные
- ✅ Не требует API ключей
- ✅ Работает на любой CMS (если есть разметка)

**Недостатки:**
- ⚠️ Не все сайты имеют Schema.org
- ⚠️ Может быть неполным

**Приоритет 3: Playwright (FALLBACK)**

Рендеринг страницы и парсинг HTML (если нет API и Schema.org).

```python
async def fetch_playwright_prices(site_url: str) -> List[Service]:
    """Получить услуги через Playwright (fallback)"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Открыть страницу услуг
        await page.goto(f"{site_url}/services")
        await page.wait_for_load_state("networkidle")
        
        # Найти элементы с ценами (селекторы зависят от сайта)
        services = await page.query_selector_all(".service-item")
        
        all_services = []
        for service_el in services:
            name = await service_el.query_selector(".service-name")
            price = await service_el.query_selector(".service-price")
            
            if name and price:
                service = Service(
                    name=await name.inner_text(),
                    price=parse_price(await price.inner_text()),
                    currency="RUB",
                )
                all_services.append(service)
        
        await browser.close()
    
    return all_services
```

**Преимущества:**
- ✅ Работает на любом сайте
- ✅ Видит динамический контент (JavaScript)

**Недостатки:**
- ❌ Медленно (рендеринг страницы)
- ❌ Хрупко (селекторы могут измениться)
- ❌ Ресурсоёмко (браузер)
- ❌ Сложно парсить (нет структуры)

**Стратегия выбора:**

```python
async def update_knowledge_base(site_url: str, config: SiteConfig):
    """Обновить базу знаний (приоритеты)"""
    
    services = None
    method_used = None
    
    # Приоритет 1: REST API
    if config.cms_type == "wordpress":
        try:
            services = await fetch_wordpress_prices(site_url)
            method_used = "WordPress REST API"
        except Exception as e:
            logger.warning(f"WordPress API failed: {e}")
    
    elif config.cms_type == "bitrix24":
        try:
            services = await fetch_bitrix_prices(site_url, config.bitrix_api_key)
            method_used = "Bitrix24 REST API"
        except Exception as e:
            logger.warning(f"Bitrix24 API failed: {e}")
    
    # Приоритет 2: Schema.org
    if not services:
        try:
            services = await fetch_schema_org_prices(site_url)
            if services:
                method_used = "Schema.org"
        except Exception as e:
            logger.warning(f"Schema.org parsing failed: {e}")
    
    # Приоритет 3: Playwright (fallback)
    if not services:
        try:
            services = await fetch_playwright_prices(site_url)
            method_used = "Playwright (fallback)"
        except Exception as e:
            logger.error(f"Playwright failed: {e}")
            raise
    
    # Сохранить в Obsidian
    await save_to_obsidian(services, method_used)
    
    logger.info(f"Knowledge base updated: {len(services)} services via {method_used}")
```

**Обновление базы знаний:**
- Ежедневный мониторинг сайта (3:00 AM)
- Автоматическое обновление цен/услуг в Obsidian
- Webhook при изменении (если CMS поддерживает)
- Сравнение с предыдущей версией (diff)
- Уведомление при изменении цен

**Метрики качества:**
- **API success rate:** > 95% (REST API работает)
- **Data accuracy:** 100% (цены совпадают с сайтом)
- **Update latency:** < 1 час (изменения обнаружены быстро)

**8. Предпродажная квалификация (ВАЖНО)**

**Цель:** Превратить холодный лид в квали-лид деликатно и быстро.

**Источник:** Интервью, строка 103 — "заложить прям предпродажный какой-то механизм, посмотреть лучшие практики того, как закрывать первичку на агентском уровне. Так, чтобы быстро из холодного лида это превратилось с помощью данного инструмента, данного агента в квали-лид, но сделать это очень деликатно."

**Определение "первичка закрыта":**

Квали-лид = лид, который:
1. **Выразил потребность** — понятно, что беспокоит / какая услуга нужна
2. **Определил срочность** — когда нужна консультация (срочно / на неделе / не срочно)
3. **Готов к действию** — согласен записаться на консультацию или готов к звонку менеджера

**Методы квалификации:**

**BANT (Budget, Authority, Need, Timeline):**
- **Budget** — обсуждён ли бюджет (в медицине часто пропускается)
- **Authority** — кто принимает решение (сам пациент / родственник)
- **Need** — какая потребность (что беспокоит)
- **Timeline** — когда нужна консультация

**SPIN (Situation, Problem, Implication, Need-Payoff):**
- **Situation** — текущая ситуация (что происходит)
- **Problem** — проблема (что беспокоит)
- **Implication** — последствия (что будет, если не решить)
- **Need-Payoff** — выгода от решения (что получит пациент)

**Медицинская адаптация (деликатная):**

```python
class QualificationFlow:
    """Предпродажная квалификация для медицинской клиники"""
    
    async def qualify_lead(self, conversation: Conversation) -> LeadStatus:
        """Квалифицировать лида через естественный диалог"""
        
        # Шаг 1: Установить контакт (эмпатия)
        await self.send_message(
            "Здравствуйте! Я виртуальный администратор клиники. "
            "Чем могу помочь?"
        )
        
        # Шаг 2: Выяснить потребность (что беспокоит)
        need = await self.ask_about_need(conversation)
        # Примеры вопросов:
        # - "Что вас беспокоит?"
        # - "Какая услуга вас интересует?"
        # - "С чем хотели бы проконсультироваться?"
        
        # Шаг 3: Определить срочность (когда нужна консультация)
        urgency = await self.ask_about_urgency(conversation)
        # Примеры вопросов:
        # - "Как срочно нужна консультация?"
        # - "Когда вам было бы удобно прийти?"
        # - "Есть ли острая боль или дискомфорт?"
        
        # Шаг 4: Предложить решение (запись на консультацию)
        ready = await self.offer_booking(conversation)
        # Примеры:
        # - "Могу записать вас на консультацию к [врач]. Удобно в [время]?"
        # - "У нас есть свободное время [дата] в [время]. Подойдёт?"
        
        # Шаг 5: Классифицировать лида
        if need and urgency and ready:
            return LeadStatus.QUALIFIED  # Квали-лид (первичка закрыта)
        elif need and urgency:
            return LeadStatus.HOT  # Горячий (почти готов)
        elif need:
            return LeadStatus.WARM  # Тёплый (есть интерес)
        else:
            return LeadStatus.COLD  # Холодный (просто спросил)

async def ask_about_need(self, conversation: Conversation) -> Optional[str]:
    """Выяснить потребность деликатно"""
    
    # Не допрос, а естественный диалог
    questions = [
        "Что вас беспокоит?",
        "Какая услуга вас интересует?",
        "С чем хотели бы проконсультироваться?",
    ]
    
    # Адаптация под контекст
    if "болит" in conversation.last_message.lower():
        return await self.send_message(
            "Понимаю, что беспокоит боль. "
            "Расскажите, пожалуйста, подробнее — где и как давно?"
        )
    
    # Если пациент уже назвал услугу
    if any(service in conversation.last_message.lower() for service in ["имплант", "чистка", "отбеливание"]):
        return conversation.last_message  # Потребность ясна
    
    # Иначе — задать вопрос
    return await self.send_message(random.choice(questions))

async def ask_about_urgency(self, conversation: Conversation) -> Optional[str]:
    """Определить срочность деликатно"""
    
    # Триггеры срочности
    urgent_keywords = ["болит", "острая", "сильная", "срочно", "сегодня", "завтра"]
    if any(kw in conversation.last_message.lower() for kw in urgent_keywords):
        return "urgent"  # Срочно
    
    # Спросить про сроки
    response = await self.send_message(
        "Когда вам было бы удобно прийти на консультацию? "
        "Есть свободное время на этой неделе."
    )
    
    if "сегодня" in response.lower() or "завтра" in response.lower():
        return "urgent"
    elif "неделя" in response.lower() or "скоро" in response.lower():
        return "this_week"
    else:
        return "not_urgent"

async def offer_booking(self, conversation: Conversation) -> bool:
    """Предложить запись на консультацию"""
    
    # Найти свободные слоты
    slots = await self.get_available_slots(urgency=conversation.urgency)
    
    if not slots:
        # Нет свободных слотов → эскалация менеджеру
        await self.send_message(
            "Сейчас соединю вас с администратором, "
            "который подберёт удобное время."
        )
        await self.escalate_to_manager(reason="no_available_slots")
        return False
    
    # Предложить ближайший слот
    slot = slots[0]
    response = await self.send_message(
        f"Могу записать вас на консультацию к {slot.doctor} "
        f"{slot.date} в {slot.time}. Подойдёт?"
    )
    
    # Проверить согласие
    if any(kw in response.lower() for kw in ["да", "подойдёт", "хорошо", "записывайте"]):
        await self.book_appointment(slot, conversation.lead_id)
        return True  # Готов записаться (квали-лид!)
    
    return False  # Не готов
```

**Критерии "первичка закрыта" (квали-лид):**

1. **Потребность выяснена** — понятно, что беспокоит или какая услуга нужна
2. **Срочность определена** — понятно, когда нужна консультация
3. **Готовность к действию** — согласен записаться или готов к звонку менеджера

**Метрика успеха:**
- **Conversion rate "холодный лид → квали-лид":** > 40%
- **Time to qualification:** < 5 минут (среднее время квалификации)
- **Escalation rate:** < 20% (процент эскалаций менеджеру)

**Особенности медицинской квалификации:**

1. **Деликатность** — без давления, эмпатия, понимание
2. **Естественный диалог** — не допрос, а разговор
3. **Адаптация под контекст** — если болит → срочность выше
4. **Эскалация при необходимости** — сложные случаи → менеджер
5. **152-ФЗ compliance** — медицинские данные → немедленная эскалация

**Настройка при setup:**

Для каждого проекта настраиваются:
- Критерии квали-лида (что считать "готовым")
- Вопросы для квалификации (BANT, SPIN, или кастомные)
- Триггеры срочности (ключевые слова)
- Правила эскалации (когда передавать менеджеру)

**Пример успешной квалификации:**

```
Пациент: Здравствуйте, сколько стоит имплантация?
Агент: Здравствуйте! Стоимость имплантации от 35 000 руб. 
        Что вас беспокоит — нужно восстановить один зуб или несколько?

Пациент: Один зуб, давно удалили, хочу поставить имплант.
Агент: Понятно. Для имплантации нужна консультация хирурга-имплантолога. 
       Когда вам было бы удобно прийти?

Пациент: Можно на этой неделе?
Агент: Конечно! Есть свободное время в четверг 15 мая в 14:00. Подойдёт?

Пациент: Да, записывайте.
Агент: Отлично! Записал вас на 15 мая в 14:00 к Иванову И.И. 
       Отправлю подтверждение на ваш номер. Как вас зовут?

Пациент: Алексей.
Агент: Спасибо, Алексей! Жду вас 15 мая. Если будут вопросы — пишите.

✅ Квали-лид (первичка закрыта):
   - Потребность: имплантация одного зуба
   - Срочность: на этой неделе
   - Готовность: записался на консультацию
```

### 3.3 Внешние API

**Каналы коммуникации:**
- **Telegram Bot API** — получение/отправка сообщений
- **Instagram Graph API** — Direct сообщения
- **VK API** — сообщения сообщества
- **WhatsApp Business API** — сообщения
- **Website Chat API** — онлайн-чат (Jivo, Carrot quest)

**AI и обработка:**
- **Assembly AI** — транскрибация голосовых (если voice_enabled)
- **OpenAI API** — генерация ответов (GPT-4o / GPT-4o-mini)
- **Fallback:** DeepSeek / Qwen (китайские бесплатные модели)

**Интеграции:**
- **CRM API** — Bitrix24 / amoCRM (создание/обновление лидов)
- **Календарь API** — Google Calendar / Яндекс.Календарь (запись)
- **Obsidian Vault** — локальное чтение базы знаний

**Мониторинг сайта:**
- **WordPress REST API** — получение страниц, услуг, цен
- **Bitrix24 REST API** — получение каталога товаров/услуг
- **Schema.org парсинг** — структурированные данные
- **Playwright** — fallback (если нет API)
- **Perplexity API** — поиск медицинских исследований

---

## 4. ВЫХОДНЫЕ ДАННЫЕ

### 4.1 Формат результата

**В CRM (основное хранилище):**

```python
class LeadData(BaseModel):
    """Данные лида в CRM"""
    
    # Обязательные поля
    lead_id: str = Field(..., description="ID лида в CRM")
    status: str = Field(..., description="cold/warm/hot/qualified")
    conversation_history: List[Dict] = Field(..., description="Полная история диалога")
    
    # Контактные данные
    contact_name: Optional[str] = Field(None, description="Имя пациента")
    contact_phone: Optional[str] = Field(None, description="Телефон")
    contact_email: Optional[str] = Field(None, description="Email")
    
    # Источник
    source_channel: str = Field(..., description="telegram/instagram/vk/whatsapp/website")
    first_message_time: datetime = Field(..., description="Время первого сообщения")
    response_time: int = Field(..., description="Время реакции агента (секунды)")
    
    # Квалификация
    need: Optional[str] = Field(None, description="Что беспокоит, какая услуга")
    urgency: Optional[str] = Field(None, description="срочно/на неделе/не срочно")
    budget_discussed: bool = Field(False, description="Обсуждался ли бюджет")
    ready_to_book: bool = Field(False, description="Готов записаться")
    
    # Дополнительные данные (всё, что удалось раздобыть)
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None
    utm_term: Optional[str] = None
    geo_location: Optional[str] = None
    device_type: Optional[str] = None
    previous_interactions: Optional[List[str]] = None
    interested_services: Optional[List[str]] = None
    interested_doctors: Optional[List[str]] = None
    unanswered_questions: Optional[List[str]] = None
    
    # Метаданные
    agent_version: str = Field(..., description="Версия агента")
    conversation_duration: int = Field(..., description="Длительность диалога (минуты)")
    messages_count: int = Field(..., description="Количество сообщений")
    escalated_to_manager: bool = Field(False, description="Передан менеджеру")
    escalation_reason: Optional[str] = Field(None, description="Причина эскалации")
```

**В Obsidian (резервное + аналитика):**

```
obsidian/social-magister/wiki/
├── conversations/
│   └── {project_id}/
│       └── {date}/
│           └── {lead_id}.md  # Копия диалога
├── analytics/
│   └── {project_id}/
│       ├── conversion_rate.md  # Конверсия в квали-лид
│       ├── response_time.md    # Время ответа
│       └── unanswered.md       # Неотвеченные вопросы
└── knowledge_gaps/
    └── {project_id}/
        └── missing_answers.md  # Вопросы без ответа
```

### 4.2 Сохранение результатов

**База данных (SQLite):**

```sql
CREATE TABLE ai_sales_admin_conversations (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    lead_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    status TEXT NOT NULL,
    conversation_history JSON NOT NULL,
    contact_data JSON,
    qualification_data JSON,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_project_lead ON ai_sales_admin_conversations(project_id, lead_id);
CREATE INDEX idx_status ON ai_sales_admin_conversations(status);
CREATE INDEX idx_created_at ON ai_sales_admin_conversations(created_at);
```

**Obsidian Vault:**

```markdown
---
lead_id: uuid
project_id: project-123
channel: telegram
status: qualified
created_at: 2026-05-10T12:00:00Z
---

# Диалог с пациентом

## Контактные данные
- Имя: Иван Иванов
- Телефон: +7 (999) 123-45-67
- Канал: Telegram (@ivan_ivanov)

## Квалификация
- Потребность: Консультация стоматолога
- Срочность: На этой неделе
- Готовность: Готов записаться
- Статус: Квали-лид

## История диалога

**[12:00] Пациент:** Здравствуйте, сколько стоит консультация стоматолога?

**[12:00] Агент:** Здравствуйте! Первичная консультация стоматолога — 2000 рублей. Что вас беспокоит?

**[12:01] Пациент:** Болит зуб, нужно срочно посмотреть.

**[12:01] Агент:** Понимаю, как неприятно. Когда вам удобно прийти на консультацию?

**[12:02] Пациент:** Можно завтра или послезавтра?

**[12:02] Агент:** Да, конечно! Завтра есть свободное время в 14:00 и 16:00. Что вам удобнее?

**[12:03] Пациент:** 14:00 подойдёт.

**[12:03] Агент:** Отлично! Записал вас на завтра в 14:00 к стоматологу. Подскажите ваше имя и телефон для подтверждения?

**[12:04] Пациент:** Иван Иванов, +7 (999) 123-45-67

**[12:04] Агент:** Спасибо, Иван! Запись подтверждена. Отправил вам SMS с напоминанием. До встречи завтра в 14:00!

## Результат
- ✅ Квали-лид
- ✅ Записан на консультацию
- ✅ Сохранено в CRM
```

---

## 5. МЕТРИКИ КАЧЕСТВА

### 5.1 Производительность

**Обязательные метрики:**

- **Success rate:** > 95%
  - Процент успешных ответов без ошибок
  - Измерение: (успешные ответы / все ответы) × 100%
  - Алерт: < 90% → Warning, < 85% → Critical

- **Response time:** < 30 секунд
  - Среднее время первого ответа
  - Измерение: время от получения сообщения до первого ответа
  - Алерт: > 45 секунд → Warning, > 60 секунд → Critical

- **Conversation duration:** < 5 минут
  - Среднее время до квалификации лида
  - Измерение: время от первого сообщения до статуса "qualified"
  - Алерт: > 10 минут → Warning

### 5.2 Качественные метрики

**Конверсия:**

- **Конверсия в квали-лид:** > 30%
  - Процент холодных лидов, превращённых в квали-лидов
  - Измерение: (квали-лиды / все обращения) × 100%
  - Алерт: < 20% → Warning, < 15% → Critical

- **Escalation rate:** < 20%
  - Процент эскалаций менеджеру
  - Измерение: (эскалации / все обращения) × 100%
  - Алерт: > 30% → Warning (агент не справляется)

- **Patient satisfaction:** > 4.5/5
  - Оценка пациента после диалога (опционально)
  - Измерение: опрос после диалога
  - Алерт: < 4.0 → Warning

**Бизнес-метрики (через CRM):**

- **Квали-лид → Запись:** > 50%
  - Сколько квали-лидов записались на консультацию
  - Измерение: (записи / квали-лиды) × 100%
  - Алерт: < 40% → Warning

- **Квали-лид → Продажа:** > 20%
  - Сколько квали-лидов стали клиентами
  - Измерение: (продажи / квали-лиды) × 100%
  - Алерт: < 15% → Warning

- **Revenue per lead:** средний чек
  - Средний чек от лидов агента
  - Измерение: сумма продаж / количество лидов
  - Цель: зависит от клиники

### 5.3 Специфичные метрики

**Compliance:**

- **152-ФЗ compliance:** 100%
  - Все запросы медицинских данных эскалированы
  - Измерение: (эскалации по 152-ФЗ / запросы мед. данных) × 100%
  - Алерт: < 100% → Critical (нарушение закона!)

**База знаний:**

- **Knowledge base coverage:** > 90%
  - Процент вопросов, на которые агент смог ответить
  - Измерение: (ответы из базы / все вопросы) × 100%
  - Алерт: < 80% → Warning (база знаний неполная)

- **Price accuracy:** 100%
  - Актуальность цен в базе знаний
  - Измерение: сравнение с сайтом
  - Алерт: < 100% → Critical (неверные цены!)

### 5.4 Дашборд метрик

**Ежедневный дашборд:**
- Количество обращений
- Конверсия в квали-лид
- Среднее время ответа
- Топ-10 вопросов
- Неотвеченные вопросы
- Эскалации менеджеру

**Еженедельный отчёт:**
- Динамика конверсии
- Сравнение с предыдущей неделей
- Топ-10 услуг (по интересу)
- Топ-10 врачей (по интересу)
- Рекомендации по улучшению

---

## 6. ИНТЕГРАЦИИ

### 6.1 Event Bus

**Получение задач от Social Magister:**
```json
{
  "event_type": "social.sales_admin.requested",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "ai-sales-admin",
  "payload": {
    "project_id": "clinic-123",
    "message": {
      "channel": "telegram",
      "from": "@user123",
      "text": "Здравствуйте, сколько стоит консультация?",
      "timestamp": "2026-05-10T12:00:00Z"
    }
  }
}
```

**Отправка результатов Social Magister:**
```json
{
  "event_type": "social.sales_admin.completed",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "ai-sales-admin",
  "payload": {
    "status": "success",
    "result": {
      "lead_id": "lead-456",
      "lead_status": "qualified",
      "conversation_summary": "Пациент интересуется консультацией стоматолога, записан на завтра в 14:00",
      "next_action": "manager_followup"
    },
    "metrics": {
      "execution_time_ms": 15000,
      "response_time_ms": 25000,
      "messages_count": 8,
      "conversion": "qualified"
    },
    "errors": []
  }
}
```

### 6.2 Event Store

**Логирование всех событий:**
- `social.sales_admin.requested` — получено сообщение от пациента
- `social.sales_admin.completed` — диалог завершён
- `social.sales_admin.failed` — ошибка обработки
- `escalation.required` — эскалация менеджеру

**Формат записи:**
```json
{
  "event_id": "uuid",
  "event_type": "social.sales_admin.completed",
  "correlation_id": "uuid",
  "timestamp": "2026-05-10T12:15:00Z",
  "subagent_id": "ai-sales-admin",
  "payload": {
    "project_id": "clinic-123",
    "lead_id": "lead-456",
    "status": "qualified",
    "channel": "telegram"
  }
}
```

### 6.3 Obsidian Vault

**Путь:** `obsidian/social-magister/`

**Операции:**
- **Ingest:** Сохранение диалогов в `raw/conversations/`
- **Query:** Чтение истории для анализа
- **Lint:** Проверка противоречий, устаревших данных

**Специальные файлы:**
- `wiki/log.md` — хронология всех операций
- `wiki/index.md` — каталог всех страниц
- `wiki/conversations/{project_id}/` — диалоги по проектам
- `wiki/analytics/{project_id}/` — аналитика по проектам
- `wiki/knowledge_gaps/{project_id}/` — неотвеченные вопросы

### 6.4 Database

**Таблицы:**
- `ai_sales_admin_conversations` — диалоги с пациентами
- `ai_sales_admin_leads` — лиды и их статусы
- `ai_sales_admin_knowledge_base` — база знаний (кэш)

**Операции:**
- INSERT: сохранение новых диалогов
- SELECT: чтение истории для анализа
- UPDATE: обновление статусов лидов

### 6.5 Teacher Agent

**Интеграция:**
- Teacher Agent читает `wiki/log.md` и `wiki/conversations/`
- Анализирует успешные/неудачные диалоги
- Обновляет best practices для квалификации
- Улучшает вопросы и стратегии

**Частота обучения:**
- Периодический пересмотр: раз в квартал
- Экстренное обучение: при падении конверсии < 20%
- Адаптация: при изменении ToV или продуктов клиники

### 6.6 Внешние API

**Каналы коммуникации:**
- **Telegram Bot API** — `https://api.telegram.org/bot{token}/`
  - Методы: getUpdates, sendMessage, sendPhoto
  - Rate limit: 30 сообщений/секунду
  - Аутентификация: Bot token

- **Instagram Graph API** — `https://graph.instagram.com/v18.0/`
  - Методы: GET/POST /{ig-user-id}/messages
  - Rate limit: 200 запросов/час
  - Аутентификация: Access token

- **VK API** — `https://api.vk.com/method/`
  - Методы: messages.send, messages.getHistory
  - Rate limit: 3 запроса/секунду
  - Аутентификация: Access token

- **WhatsApp Business API** — `https://graph.facebook.com/v18.0/`
  - Методы: POST /{phone-number-id}/messages
  - Rate limit: 80 сообщений/секунду
  - Аутентификация: Access token

**AI и обработка:**
- **Assembly AI** — `https://api.assemblyai.com/v2/`
  - Методы: POST /transcript (транскрибация)
  - Rate limit: 100 запросов/минуту
  - Аутентификация: API key

- **OpenAI API** — `https://api.openai.com/v1/`
  - Модели: gpt-4o, gpt-4o-mini
  - Rate limit: 10,000 запросов/минуту
  - Аутентификация: API key

**Интеграции:**
- **Bitrix24 REST API** — `https://{domain}.bitrix24.ru/rest/`
  - Методы: crm.lead.add, crm.lead.update
  - Rate limit: 2 запроса/секунду
  - Аутентификация: Webhook или OAuth

- **amoCRM API** — `https://{domain}.amocrm.ru/api/v4/`
  - Методы: POST /leads, PATCH /leads/{id}
  - Rate limit: 7 запросов/секунду
  - Аутентификация: Access token

- **Google Calendar API** — `https://www.googleapis.com/calendar/v3/`
  - Методы: events.list, events.insert
  - Rate limit: 1,000,000 запросов/день
  - Аутентификация: OAuth 2.0

**Мониторинг сайта:**
- **WordPress REST API** — `{site_url}/wp-json/wp/v2/`
  - Методы: GET /pages, GET /posts
  - Rate limit: зависит от хостинга
  - Аутентификация: не требуется (публичные данные)

- **Perplexity API** — `https://api.perplexity.ai/`
  - Методы: POST /chat/completions
  - Rate limit: 50 запросов/минуту
  - Аутентификация: API key

---

## 7. ОБРАБОТКА ОШИБОК

### 7.1 Стандартные ошибки

**INVALID_INPUT:**
- Причина: Пустое сообщение, неверный формат
- Действие: Вернуть failure сразу
- Retry: Нет
- Логирование: Event Store + системные логи

**API_ERROR:**
- Причина: Временная недоступность внешнего API
- Действие: Retry с exponential backoff (3 попытки, 30 секунд интервал)
- Если все попытки исчерпаны → вернуть partial_success с сообщением пациенту
- Логирование: Event Store + системные логи

**TIMEOUT:**
- Причина: Превышено максимальное время выполнения
- Действие: Вернуть partial_success с частичными результатами
- Retry: Нет
- Логирование: Event Store + Obsidian

**INTERNAL_ERROR:**
- Причина: Внутренняя ошибка агента (баг в коде)
- Действие: Логировать, вернуть failure, эскалировать
- Retry: Нет
- Эскалация: Social Magister → Operator → User

### 7.2 Специфичные ошибки

**API_UNAVAILABLE:**
- Причина: API канала недоступен (Telegram/Instagram/VK down)
- Действие: Retry 3 раза (30 секунд интервал)
- Если не помогло → логировать, уведомить администратора
- Сообщение пациенту: "Извините, технические неполадки. Попробуйте через 5 минут или позвоните нам"
- Retry: Да (3 попытки)
- Эскалация: Critical (если все каналы недоступны)

**CRM_CONNECTION_ERROR:**
- Причина: CRM не отвечает
- Действие: Retry 3 раза (10 секунд интервал)
- Если не помогло → сохранить диалог в Obsidian (резервное хранилище)
- Синхронизировать с CRM позже (когда восстановится)
- Продолжить диалог с пациентом (не прерывать)
- Retry: Да (3 попытки)
- Эскалация: Warning

**OPENAI_API_ERROR:**
- Причина: OpenAI API недоступен
- Действие: Fallback на DeepSeek / Qwen (китайские модели)
- Если и они недоступны → шаблонные ответы (FAQ)
- Эскалация менеджеру, если вопрос сложный
- Retry: Нет (сразу fallback)
- Эскалация: Warning

**KNOWLEDGE_BASE_OUTDATED:**
- Причина: База знаний устарела (цены изменились на сайте)
- Действие: Предупредить пациента "Уточню актуальную информацию"
- Запустить внеплановое обновление базы знаний
- Эскалация менеджеру для точного ответа
- Retry: Нет
- Эскалация: Warning

**INAPPROPRIATE_BEHAVIOR:**
- Причина: Неадекватное поведение пациента (мат, угрозы, спам, троллинг)
- Действие: Протокол (предупреждение → эскалация → блокировка)
- Критерии: мат, угрозы, оскорбления, спам (> 10 сообщений/минуту), троллинг
- Retry: Нет
- Эскалация: Critical (при третьем нарушении)

**Протокол неадекватного поведения:**
1. **Первое нарушение:** Вежливое предупреждение
   - Сообщение: "Пожалуйста, давайте общаться уважительно"
   - Логирование в CRM + Obsidian
2. **Второе нарушение:** Эскалация менеджеру
   - Уведомление администратора
   - Передача контекста диалога
3. **Третье нарушение:** Блокировка пользователя
   - Добавление в чёрный список
   - Блокировка во всех каналах
   - Уведомление администратора

**MEDICAL_DATA_REQUEST:**
- Причина: Пациент просит медицинские данные (152-ФЗ)
- Действие: Немедленная эскалация менеджеру (без попыток ответить)
- Сообщение: "Сейчас соединю вас с администратором, который сможет посмотреть вашу историю"
- Логирование запроса (для аудита 152-ФЗ)
- Retry: Нет
- Эскалация: Critical (нарушение закона, если не эскалировать)

**Ключевые фразы для MEDICAL_DATA_REQUEST:**
- "я уже у вас был"
- "посмотрите мою историю"
- "мои анализы"
- "что мне назначали"
- "мои результаты"
- "моя карта"
- "мои записи"

**COMPLEX_QUESTION:**
- Причина: Вопрос слишком сложный (агент не знает ответа)
- Действие: Честно признать "Не могу точно ответить, сейчас соединю с администратором"
- Эскалация менеджеру
- Логирование вопроса (для улучшения базы знаний)
- Retry: Нет
- Эскалация: Warning

### 7.3 Эскалация

**Путь эскалации:**
```
AI Sales Admin Agent → Social Magister → Operator → User → Architect
```

**Когда эскалировать:**
- Critical errors (блокируют работу системы)
- Success rate < 90% в течение 3 дней
- Конверсия в квали-лид < 15% в течение недели
- 152-ФЗ нарушения (медицинские данные)
- Неадекватное поведение пациента (третье нарушение)

**Формат эскалации:**
```json
{
  "event_type": "escalation.required",
  "correlation_id": "uuid",
  "source": "ai-sales-admin",
  "severity": "critical",
  "payload": {
    "error_type": "MEDICAL_DATA_REQUEST",
    "message": "Пациент запросил медицинские данные (152-ФЗ)",
    "context": {
      "project_id": "clinic-123",
      "lead_id": "lead-456",
      "channel": "telegram",
      "conversation_history": [...]
    },
    "escalation_path": ["Social Magister", "Operator", "User"]
  }
}
```

### 7.4 Graceful Degradation

**При частичном сбое:**
1. Выполнить максимум возможного
2. Вернуть `partial_success`
3. Указать, что не удалось выполнить
4. Уведомить Social Magister

**Примеры:**
- Если CRM недоступен → сохранить в Obsidian, синхронизировать позже
- Если OpenAI недоступен → использовать fallback модели (DeepSeek, Qwen)
- Если календарь недоступен → предложить пациенту позвонить для записи
- Если критичная ошибка → эскалировать немедленно

---

## 8. ОБУЧЕНИЕ И АДАПТАЦИЯ

### 8.1 Интеграция с Teacher Agent

**Что Teacher Agent предоставляет:**
- Обновлённые best practices для квалификации лидов
- Улучшенные вопросы для диалога
- Новые паттерны успешных диалогов
- Рекомендации по оптимизации конверсии

**Как AI Sales Admin Agent обучается:**
1. Teacher Agent читает `wiki/log.md` и `wiki/conversations/`
2. Анализирует успешные/неудачные диалоги
3. Выявляет паттерны (какие вопросы работают, какие нет)
4. Создаёт обновлённые инструкции для квалификации
5. AI Sales Admin Agent применяет новые инструкции
6. Тестирует на контрольной выборке
7. Сохраняет результаты в Obsidian

**Частота обучения:**
- Периодический пересмотр: раз в квартал
- Экстренное обучение: при падении конверсии < 20%
- Адаптация: при изменении ToV или продуктов клиники

### 8.2 История в Obsidian

**Структура:**
```
obsidian/social-magister/wiki/
├── log.md                    # Хронология операций
├── conversations/
│   └── {project_id}/         # Диалоги по проектам
│       └── {date}/
│           └── {lead_id}.md
├── analytics/
│   └── {project_id}/         # Аналитика по проектам
│       ├── conversion_rate.md
│       ├── response_time.md
│       └── top_questions.md
├── knowledge_gaps/
│   └── {project_id}/         # Неотвеченные вопросы
│       └── missing_answers.md
└── strategies/
    └── qualification_best_practices.md  # Best practices
```

**Формат log.md:**
```markdown
## [2026-05-10 12:00] conversation_started | Telegram @user123, clinic-123
## [2026-05-10 12:05] lead_qualified | Lead lead-456, status: qualified
## [2026-05-10 12:10] booking_created | Appointment tomorrow 14:00
```

### 8.3 Адаптация

**Автоматическая адаптация:**
- Если конверсия падает < 20% → запросить обучение у Teacher Agent
- Если новые паттерны обнаружены → логировать для анализа
- Если изменились цены на сайте → обновить базу знаний

**Ручная адаптация:**
- Пользователь может изменить параметры через Social Magister
- Пользователь может добавить новые вопросы для квалификации
- Пользователь может изменить критерии квали-лида

---

## 9. ЛОГИРОВАНИЕ

### 9.1 Event Store (обязательно)

**Логируемые события:**
- `social.sales_admin.requested` — получено сообщение
- `social.sales_admin.completed` — диалог завершён
- `social.sales_admin.failed` — ошибка обработки
- `escalation.required` — эскалация менеджеру

**Формат:**
```json
{
  "event_id": "uuid",
  "event_type": "social.sales_admin.completed",
  "correlation_id": "uuid",
  "timestamp": "2026-05-10T12:15:00Z",
  "subagent_id": "ai-sales-admin",
  "payload": {
    "project_id": "clinic-123",
    "lead_id": "lead-456",
    "status": "qualified",
    "channel": "telegram",
    "response_time_ms": 25000,
    "messages_count": 8
  }
}
```

### 9.2 Obsidian Vault (обязательно)

**История операций (`wiki/log.md`):**
```markdown
## [2026-05-10 12:00] conversation_started | Telegram @user123, clinic-123
## [2026-05-10 12:05] lead_qualified | Lead lead-456, status: qualified
## [2026-05-10 12:10] booking_created | Appointment tomorrow 14:00
```

**Результаты работы:**
- `wiki/conversations/` — диалоги с пациентами
- `wiki/analytics/` — аналитика по проектам
- `wiki/knowledge_gaps/` — неотвеченные вопросы

**Метрики производительности:**
- `wiki/metrics/conversion_rate.md` — конверсия в квали-лид
- `wiki/metrics/response_time.md` — время ответа
- `wiki/metrics/escalation_rate.md` — процент эскалаций

### 9.3 Системные логи (опционально)

**Debug информация:**
- API запросы и ответы
- Время выполнения каждого шага
- Промежуточные результаты

**Ошибки и warnings:**
- Ошибки API
- Таймауты
- Валидация данных

**Формат:**
```
[2026-05-10 12:00:00] [INFO] [ai-sales-admin] [correlation-id-123] Received message from Telegram @user123
[2026-05-10 12:00:03] [INFO] [ai-sales-admin] [correlation-id-123] Created lead in CRM: lead-456
[2026-05-10 12:00:25] [INFO] [ai-sales-admin] [correlation-id-123] Sent response (25s)
```

---

## 10. ТЕСТИРОВАНИЕ

### 10.1 Unit тесты

**Покрытие:** > 80%

**Обязательные тесты:**
- `test_validate_input` — валидация входных данных
- `test_api_error_handling` — обработка ошибок API
- `test_retry_with_backoff` — retry механизм
- `test_save_to_crm` — сохранение в CRM
- `test_save_to_obsidian` — сохранение в Obsidian
- `test_format_result` — формирование результата

**Специфичные тесты:**

```python
def test_medical_data_request_escalation():
    """Тест эскалации при запросе медицинских данных (152-ФЗ)"""
    agent = AISalesAdminAgent(config)
    message = "Посмотрите мою историю болезни"
    
    result = await agent.process_message(message)
    
    assert result.escalated_to_manager == True
    assert result.escalation_reason == "MEDICAL_DATA_REQUEST"
    assert "152-ФЗ" in result.logs

def test_inappropriate_behavior_protocol():
    """Тест протокола неадекватного поведения"""
    agent = AISalesAdminAgent(config)
    
    # Первое нарушение
    result1 = await agent.process_message("мат и оскорбления")
    assert result1.warning_sent == True
    
    # Второе нарушение
    result2 = await agent.process_message("ещё мат")
    assert result2.escalated_to_manager == True
    
    # Третье нарушение
    result3 = await agent.process_message("снова мат")
    assert result3.user_blocked == True

def test_knowledge_base_query():
    """Тест запроса к базе знаний"""
    agent = AISalesAdminAgent(config)
    message = "Сколько стоит консультация стоматолога?"
    
    result = await agent.process_message(message)
    
    assert result.answer_found == True
    assert "2000" in result.response  # Цена из базы знаний
    assert result.source == "knowledge_base"
```

### 10.2 Integration тесты

**Обязательные сценарии:**
- `test_receive_message_from_telegram` — получение сообщения через Telegram Bot API
- `test_create_lead_in_crm` — создание лида в CRM (Bitrix24/amoCRM)
- `test_send_response_to_telegram` — отправка ответа через Telegram Bot API
- `test_log_to_event_store` — логирование в Event Store
- `test_save_to_obsidian_vault` — сохранение в Obsidian vault
- `test_escalation_on_medical_data` — эскалация при запросе медицинских данных
- `test_integration_with_calendar` — интеграция с календарём (запись)

### 10.3 E2E тесты

**Обязательные сценарии:**

```python
async def test_full_conversation_flow():
    """Полный цикл: сообщение → квалификация → запись → CRM"""
    # 1. Создать тестовое сообщение
    message = {
        "channel": "telegram",
        "from": "@test_user",
        "text": "Здравствуйте, сколько стоит консультация стоматолога?"
    }
    
    # 2. Отправить через Event Bus
    await event_bus.publish("social.sales_admin.requested", message)
    
    # 3. Дождаться результата
    result = await event_bus.subscribe("social.sales_admin.completed")
    
    # 4. Проверить результат
    assert result["status"] == "success"
    assert result["lead_status"] == "qualified"
    
    # 5. Проверить сохранение в CRM
    crm_lead = await crm.get_lead(result["lead_id"])
    assert crm_lead is not None
    assert crm_lead["status"] == "qualified"
    
    # 6. Проверить сохранение в Obsidian
    obsidian_file = f"obsidian/social-magister/wiki/conversations/{project_id}/{date}/{lead_id}.md"
    assert os.path.exists(obsidian_file)

async def test_medical_data_escalation_e2e():
    """E2E тест эскалации при запросе медицинских данных"""
    message = {
        "channel": "telegram",
        "from": "@test_user",
        "text": "Посмотрите мою историю болезни"
    }
    
    result = await agent.process_message(message)
    
    # Проверить эскалацию
    assert result.escalated_to_manager == True
    assert result.escalation_reason == "MEDICAL_DATA_REQUEST"
    
    # Проверить логирование (152-ФЗ аудит)
    event = await event_store.get_event(result.event_id)
    assert event["payload"]["compliance"] == "152-FZ"

async def test_inappropriate_behavior_e2e():
    """E2E тест протокола неадекватного поведения"""
    # Три нарушения подряд
    for i in range(3):
        message = {"channel": "telegram", "from": "@bad_user", "text": "мат"}
        result = await agent.process_message(message)
    
    # Проверить блокировку
    assert result.user_blocked == True
    
    # Проверить, что пользователь в чёрном списке
    blacklist = await agent.get_blacklist()
    assert "@bad_user" in blacklist
```

---

## 11. DEPLOYMENT

### 11.1 Требования

**Окружение:**
- Python 3.11+
- Event Bus доступен
- Event Store доступен
- Obsidian vault доступен (`obsidian/social-magister/`)
- Database доступна (`data/aim.db`)
- Сервер 24/7 (не локально)

**Зависимости:**
```txt
httpx >= 0.24.0              # API запросы
pydantic >= 2.0.0            # Валидация данных
sqlalchemy >= 2.0.0          # База данных
python-frontmatter >= 1.0.0  # Obsidian frontmatter
openai >= 1.0.0              # OpenAI API
assemblyai >= 0.17.0         # Assembly AI (если voice_enabled)
playwright >= 1.40.0         # Мониторинг сайта (fallback)
```

### 11.2 Конфигурация (.env)

```env
SUBAGENT_ID=ai-sales-admin
EVENT_BUS_URL=...
EVENT_STORE_URL=...
OBSIDIAN_VAULT_PATH=./obsidian/social-magister
DATABASE_URL=sqlite+aiosqlite:///./data/aim.db

# Проект
PROJECT_ID=clinic-123
PROJECT_URL=https://clinic123.ru

# Каналы
CHANNELS=telegram,instagram,vk,whatsapp,website
TELEGRAM_BOT_TOKEN=...
INSTAGRAM_API_KEY=...
VK_API_KEY=...
WHATSAPP_API_KEY=...
WEBSITE_CHAT_API_KEY=...

# CRM
CRM_TYPE=bitrix24
CRM_API_KEY=...
CRM_WEBHOOK_URL=...

# Календарь
CALENDAR_TYPE=google
CALENDAR_API_KEY=...

# AI
OPENAI_API_KEY=...
VOICE_ENABLED=false
ASSEMBLY_AI_KEY=...

# Мониторинг сайта
SITE_MONITORING_ENABLED=true
SITE_MONITORING_SCHEDULE=0 3 * * *

# Fallback
FALLBACK_MODEL=deepseek
```

### 11.3 Мониторинг

**Метрики для алертов:**
- Success rate < 95% → Warning
- Success rate < 90% → Critical
- Response time > 45 секунд → Warning
- Response time > 60 секунд → Critical
- Конверсия в квали-лид < 20% → Warning
- Конверсия в квали-лид < 15% → Critical
- 152-ФЗ compliance < 100% → Critical (нарушение закона!)

**Дашборд метрик:**
- Количество обращений в день
- Процент success / partial / failed
- Среднее время ответа
- Конверсия в квали-лид
- Топ-10 вопросов
- Топ-10 ошибок
- Эскалации менеджеру

### 11.4 Изоляция проектов (КРИТИЧНО)

**Архитектура:** Один экземпляр агента на проект

**Проблема:**
Разные клиники имеют разные базы знаний, ToV, продукты, цены. Нельзя допустить пересечения данных между проектами — это приведёт к ошибкам в ответах пациентам и нарушению конфиденциальности.

**Решение: Полная изоляция на всех уровнях**

**1. Изоляция Obsidian Vaults:**
```
obsidian/
├── social-magister-clinic-123/     # Проект 1
│   ├── raw/
│   ├── wiki/
│   └── decisions/
├── social-magister-clinic-456/     # Проект 2
│   ├── raw/
│   ├── wiki/
│   └── decisions/
└── social-magister-clinic-789/     # Проект 3
    ├── raw/
    ├── wiki/
    └── decisions/
```

**Путь к vault:** `obsidian/social-magister-{project_id}/`

**2. Изоляция базы данных:**

**Вариант A: Отдельные схемы (рекомендуется):**
```sql
-- Схема для каждого проекта
CREATE SCHEMA ai_sales_admin_clinic_123;
CREATE SCHEMA ai_sales_admin_clinic_456;

-- Таблицы в схеме проекта
CREATE TABLE ai_sales_admin_clinic_123.conversations (...);
CREATE TABLE ai_sales_admin_clinic_123.leads (...);
```

**Вариант B: Префикс в таблицах:**
```sql
CREATE TABLE ai_sales_admin_clinic_123_conversations (...);
CREATE TABLE ai_sales_admin_clinic_123_leads (...);
```

**Вариант C: Отдельные базы данных:**
```
data/
├── aim_clinic_123.db
├── aim_clinic_456.db
└── aim_clinic_789.db
```

**Рекомендация:** Вариант A (схемы) — баланс между изоляцией и управляемостью.

**3. Изоляция конфигурации:**

Каждый проект имеет свой `.env` файл:
```
config/
├── clinic-123.env
├── clinic-456.env
└── clinic-789.env
```

**Обязательные параметры в .env:**
- `PROJECT_ID` — уникальный ID проекта
- `OBSIDIAN_VAULT_PATH` — путь к vault проекта
- `DATABASE_SCHEMA` — схема БД проекта
- Все API ключи (CRM, календарь, каналы)

**4. Deployment стратегия:**

**Вариант A: Docker контейнер на проект (рекомендуется):**
```bash
# Запуск агента для clinic-123
docker run -d \
  --name ai-sales-admin-clinic-123 \
  --env-file config/clinic-123.env \
  ai-sales-admin:latest

# Запуск агента для clinic-456
docker run -d \
  --name ai-sales-admin-clinic-456 \
  --env-file config/clinic-456.env \
  ai-sales-admin:latest
```

**Преимущества:**
- Полная изоляция процессов
- Независимые перезапуски
- Простое масштабирование
- Безопасность (контейнеры изолированы)

**Вариант B: Один процесс, мультитенант:**
```python
# НЕ РЕКОМЕНДУЕТСЯ — риск пересечения данных
agents = {
    "clinic-123": AISalesAdminAgent(config_123),
    "clinic-456": AISalesAdminAgent(config_456),
}
```

**Проблемы:**
- Риск утечки данных между проектами
- Сложная отладка
- Один падающий проект роняет всех

**5. Проверка изоляции:**

**При запуске агента:**
```python
async def verify_isolation(project_id: str):
    """Проверка изоляции проекта"""
    
    # 1. Проверить, что vault существует и пустой/изолированный
    vault_path = f"obsidian/social-magister-{project_id}/"
    assert os.path.exists(vault_path), f"Vault {vault_path} не существует"
    
    # 2. Проверить, что схема БД существует
    schema = f"ai_sales_admin_{project_id}"
    assert await db.schema_exists(schema), f"Схема {schema} не существует"
    
    # 3. Проверить, что нет пересечений с другими проектами
    other_projects = await db.query("SELECT DISTINCT project_id FROM all_projects WHERE project_id != ?", project_id)
    for other in other_projects:
        # Проверить, что нет доступа к данным другого проекта
        assert not await can_access_data(project_id, other.project_id)
    
    # 4. Проверить уникальность API ключей (если требуется)
    # Например, один Telegram бот не может обслуживать два проекта
```

**6. Мониторинг изоляции:**

**Метрики:**
- Количество активных проектов
- Изоляция vault (нет пересечений)
- Изоляция БД (нет cross-schema запросов)
- Изоляция процессов (отдельные контейнеры)

**Алерты:**
- Cross-project data access → Critical (нарушение изоляции!)
- Shared API keys → Warning (риск пересечения)
- Missing vault/schema → Critical (проект не изолирован)

**7. Документация для deployment:**

```markdown
# Добавление нового проекта

1. Создать Obsidian Vault:
   mkdir -p obsidian/social-magister-{project_id}/{raw,wiki,decisions}

2. Создать схему БД:
   CREATE SCHEMA ai_sales_admin_{project_id};

3. Создать конфигурацию:
   cp config/template.env config/{project_id}.env
   # Заполнить все параметры

4. Запустить контейнер:
   docker run -d --name ai-sales-admin-{project_id} \
     --env-file config/{project_id}.env \
     ai-sales-admin:latest

5. Проверить изоляцию:
   python scripts/verify_isolation.py {project_id}
```

---

**Дата создания:** 2026-05-10  
**Автор:** Mikhail Eliseev (via meAI Architect)  
**Статус:** Ready  
**Применение:** P1 агент для Social Magister
