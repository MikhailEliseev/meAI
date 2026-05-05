# 🎯 Roadmap: Business-Oriented CI Report

**Дата:** 2026-05-05  
**Проблема:** Текущий отчёт технический, нужен бизнес-ориентированный  
**Приоритет:** HIGH

---

## 📋 Что нужно добавить в CI Deep Analyzer

### 1. CMS Detection (Критично!)

**Зачем:** Понять технологический стек конкурента

**Что детектировать:**
- WordPress (wp-content, wp-includes)
- Bitrix (bitrix/templates, 1C-Bitrix)
- Tilda (tilda.cc, tilda.ws)
- Wix (wix.com)
- Joomla (joomla)
- Самописная (отсутствие известных CMS)

**Как детектировать:**
```python
def detect_cms(html: str, headers: dict) -> str:
    # Check headers
    if 'X-Powered-By' in headers:
        powered_by = headers['X-Powered-By'].lower()
        if 'bitrix' in powered_by:
            return 'Bitrix'
    
    # Check HTML
    if 'wp-content' in html or 'wp-includes' in html:
        return 'WordPress'
    if 'tilda.cc' in html or 'tilda.ws' in html:
        return 'Tilda'
    if 'wix.com' in html:
        return 'Wix'
    if 'joomla' in html.lower():
        return 'Joomla'
    
    return 'Custom (самописная)'
```

---

### 2. Analytics Detection (Критично!)

**Зачем:** Понять, насколько конкурент data-driven

**Что детектировать:**
- Google Analytics (UA-XXXXX, G-XXXXX, gtag.js, analytics.js)
- Яндекс.Метрика (mc.yandex.ru, metrika/tag.js)
- Google Tag Manager (googletagmanager.com)
- Facebook Pixel (facebook.net/en_US/fbevents.js)
- VK Pixel (vk.com/js/api/openapi.js)

**Как детектировать:**
```python
def detect_analytics(html: str) -> dict:
    analytics = {
        'google_analytics': bool(re.search(r'UA-\d+|G-[A-Z0-9]+|gtag\.js|analytics\.js', html)),
        'yandex_metrika': bool(re.search(r'mc\.yandex\.ru|metrika/tag\.js', html)),
        'google_tag_manager': 'googletagmanager.com' in html,
        'facebook_pixel': 'facebook.net/en_US/fbevents.js' in html,
        'vk_pixel': 'vk.com/js/api/openapi.js' in html
    }
    return analytics
```

---

### 3. Call-Tracking Detection (Важно!)

**Зачем:** Понять, отслеживают ли конкуренты звонки

**Что детектировать:**
- Calltouch (calltouch.ru)
- Callibri (callibri.ru)
- Roistat (roistat.com)
- Comagic (comagic.ru)
- Ringostat (ringostat.com)

**Как детектировать:**
```python
def detect_calltracking(html: str) -> dict:
    calltracking = {
        'calltouch': 'calltouch.ru' in html,
        'callibri': 'callibri.ru' in html,
        'roistat': 'roistat.com' in html,
        'comagic': 'comagic.ru' in html,
        'ringostat': 'ringostat.com' in html
    }
    return calltracking
```

---

### 4. Messengers Detection (Важно!)

**Зачем:** Понять каналы коммуникации с клиентами

**Что детектировать:**
- WhatsApp (wa.me, api.whatsapp.com)
- Telegram (t.me, telegram.me)
- Viber (viber://chat)
- VK (vk.com/im)
- Facebook Messenger (m.me)

**Как детектировать:**
```python
def detect_messengers(html: str) -> dict:
    messengers = {
        'whatsapp': bool(re.search(r'wa\.me|api\.whatsapp\.com', html)),
        'telegram': bool(re.search(r't\.me|telegram\.me', html)),
        'viber': 'viber://chat' in html,
        'vk': 'vk.com/im' in html,
        'facebook_messenger': 'm.me' in html
    }
    return messengers
```

---

### 5. Marketing Tools Detection (Важно!)

**Зачем:** Понять маркетинговый стек конкурента

**Что детектировать:**
- Marquiz (marquiz.ru) - квизы
- Carrot quest (carrotquest.io) - чат-боты
- Jivo (jivosite.com) - онлайн-чат
- Envybox (envybox.io) - виджеты
- Callback (callback.ru) - обратный звонок
- GetButton (getbutton.io) - кнопка мессенджеров

**Как детектировать:**
```python
def detect_marketing_tools(html: str) -> dict:
    tools = {
        'marquiz': 'marquiz.ru' in html,
        'carrotquest': 'carrotquest.io' in html,
        'jivo': 'jivosite.com' in html,
        'envybox': 'envybox.io' in html,
        'callback': 'callback.ru' in html,
        'getbutton': 'getbutton.io' in html
    }
    return tools
```

---

### 6. Image Alt Text Analysis (SEO)

**Зачем:** Понять качество SEO-оптимизации изображений

**Что проверять:**
- Процент изображений с alt текстом
- Процент изображений с пустым alt
- Процент изображений без alt

**Как детектировать:**
```python
def analyze_image_alts(html: str) -> dict:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    
    images = soup.find_all('img')
    total = len(images)
    
    if total == 0:
        return {'total': 0, 'with_alt': 0, 'empty_alt': 0, 'no_alt': 0}
    
    with_alt = sum(1 for img in images if img.get('alt') and img.get('alt').strip())
    empty_alt = sum(1 for img in images if img.get('alt') == '')
    no_alt = sum(1 for img in images if not img.get('alt'))
    
    return {
        'total': total,
        'with_alt': with_alt,
        'with_alt_percent': (with_alt / total) * 100,
        'empty_alt': empty_alt,
        'no_alt': no_alt
    }
```

---

### 7. Meta Keywords Detection (SEO)

**Зачем:** Понять, используют ли конкуренты keywords (устаревшая практика)

**Что проверять:**
- Наличие meta keywords
- Количество keywords

**Как детектировать:**
```python
def detect_meta_keywords(html: str) -> dict:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    
    keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
    
    if keywords_tag and keywords_tag.get('content'):
        keywords = keywords_tag.get('content')
        return {
            'has_keywords': True,
            'keywords': keywords,
            'count': len(keywords.split(','))
        }
    
    return {'has_keywords': False, 'keywords': None, 'count': 0}
```

---

### 8. Page Speed Analysis (UX)

**Зачем:** Понять скорость загрузки сайта

**Что проверять:**
- Time to First Byte (TTFB)
- First Contentful Paint (FCP)
- Largest Contentful Paint (LCP)
- Total page load time

**Уже реализовано:** Частично (через PageSpeed API)

**Нужно добавить:** Простой замер времени загрузки

```python
import time

async def measure_page_load_time(url: str) -> float:
    start = time.time()
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            await response.text()
    end = time.time()
    return end - start
```

---

### 9. Geo-Optimization Analysis (Local SEO)

**Зачем:** Понять, оптимизирован ли сайт для локального поиска

**Что проверять:**
- Schema.org LocalBusiness
- Адрес в контактах
- Телефон в контактах
- Карта на сайте (Google Maps, Яндекс.Карты)
- Микроразметка адреса

**Как детектировать:**
```python
def analyze_geo_optimization(html: str) -> dict:
    has_local_business = 'LocalBusiness' in html or 'MedicalBusiness' in html
    has_address = bool(re.search(r'г\.\s*Москва|Москва,|Moscow', html))
    has_phone = bool(re.search(r'\+7\s*\(\d{3}\)\s*\d{3}-\d{2}-\d{2}', html))
    has_google_maps = 'maps.google.com' in html or 'google.com/maps' in html
    has_yandex_maps = 'yandex.ru/maps' in html
    
    return {
        'has_local_business_schema': has_local_business,
        'has_address': has_address,
        'has_phone': has_phone,
        'has_google_maps': has_google_maps,
        'has_yandex_maps': has_yandex_maps,
        'geo_score': sum([has_local_business, has_address, has_phone, 
                          has_google_maps or has_yandex_maps]) / 4 * 100
    }
```

---

## 📊 Новый формат отчёта "для людей"

### Структура отчёта

```markdown
# Анализ конкурента: [Название]

## 🎯 Краткая сводка
- **CMS:** WordPress / Bitrix / Tilda / Самописная
- **Технологическая зрелость:** Высокая / Средняя / Низкая
- **Маркетинговая зрелость:** Высокая / Средняя / Низкая
- **Скорость сайта:** Быстрый / Средний / Медленный

---

## 💻 Технологический стек

### CMS и платформа
- **CMS:** WordPress 6.4
- **Хостинг:** Cloudflare (по IP)
- **Сервер:** Nginx

### Аналитика и отслеживание
- ✅ Google Analytics (GA4)
- ✅ Яндекс.Метрика
- ✅ Google Tag Manager
- ❌ Facebook Pixel
- ❌ VK Pixel

**Вывод:** Базовая аналитика настроена, но нет пикселей соцсетей.

### Call-tracking
- ✅ Calltouch
- ❌ Roistat
- ❌ Comagic

**Вывод:** Отслеживают звонки через Calltouch.

---

## 📱 Каналы коммуникации

### Мессенджеры
- ✅ WhatsApp
- ✅ Telegram
- ❌ Viber
- ❌ VK

**Вывод:** Используют популярные мессенджеры.

### Онлайн-чат
- ✅ Jivo
- ❌ Carrot quest

**Вывод:** Есть онлайн-чат для быстрой связи.

---

## 🎯 Маркетинговые инструменты

### Лидогенерация
- ❌ Marquiz (квизы)
- ❌ Envybox (виджеты)
- ✅ Callback (обратный звонок)

**Вывод:** Базовые инструменты, нет квизов.

### Ретаргетинг
- ❌ Facebook Pixel
- ❌ VK Pixel
- ❌ myTarget

**Вывод:** Не настроен ретаргетинг. Упущенная возможность!

---

## 🔍 SEO-оптимизация

### Базовые метрики
- **Title:** ✅ 30/30 страниц (100%)
- **Description:** ✅ 30/30 страниц (100%)
- **H1:** ✅ 30/30 страниц (100%)
- **Keywords:** ❌ Не используются (правильно!)

### Изображения
- **Всего изображений:** 150
- **С alt текстом:** 120 (80%)
- **Без alt текста:** 30 (20%)

**Вывод:** Хорошая оптимизация изображений, но есть что улучшить.

### Geo-оптимизация
- ✅ Schema LocalBusiness
- ✅ Адрес в контактах
- ✅ Телефон в контактах
- ✅ Яндекс.Карты на сайте
- **Geo Score:** 100/100

**Вывод:** Отличная локальная оптимизация!

---

## ⚡ Производительность

### Скорость загрузки
- **Время загрузки:** 2.3 секунды
- **TTFB:** 0.8 секунды
- **FCP:** 1.2 секунды
- **LCP:** 2.1 секунды

**Вывод:** Средняя скорость, можно улучшить.

### Core Web Vitals
- **LCP:** 2.1s (Хорошо, < 2.5s)
- **CLS:** 0.05 (Отлично, < 0.1)
- **INP:** 150ms (Хорошо, < 200ms)

**Вывод:** Проходит Core Web Vitals.

---

## 🔒 Безопасность

- **HTTPS:** ✅
- **HSTS:** ✅
- **CSP:** ❌
- **Security Score:** 65/100

**Вывод:** Базовая безопасность, но нет CSP.

---

## 💡 Рекомендации

### Что делают хорошо
1. ✅ Настроена базовая аналитика (GA + Метрика)
2. ✅ Есть call-tracking (Calltouch)
3. ✅ Отличная geo-оптимизация (100/100)
4. ✅ Хорошая SEO-оптимизация (title, description, h1)

### Что можно улучшить
1. ❌ Нет ретаргетинга (Facebook Pixel, VK Pixel)
2. ❌ Нет квизов для лидогенерации (Marquiz)
3. ❌ 20% изображений без alt текста
4. ❌ Нет Content Security Policy
5. ⚠️ Средняя скорость загрузки (2.3s)

### Наши преимущества (если мы лучше)
- Мы используем квизы → конверсия выше на 30%
- У нас настроен ретаргетинг → возврат клиентов
- У нас CSP → выше безопасность
- У нас быстрее сайт → лучше ранжирование

---

## 📊 Итоговая оценка

| Категория | Оценка | Комментарий |
|-----------|--------|-------------|
| Технологии | 8/10 | Современный стек |
| Аналитика | 7/10 | Базовая настройка |
| Маркетинг | 5/10 | Нет квизов и ретаргетинга |
| SEO | 9/10 | Отличная оптимизация |
| Скорость | 6/10 | Средняя |
| Безопасность | 7/10 | Нет CSP |

**Общая оценка:** 7/10 (Хороший конкурент)

**Вывод:** Сильный конкурент с хорошей SEO-оптимизацией, но есть пробелы в маркетинге (нет ретаргетинга и квизов).
```

---

### 10. Semantic Core Analysis (Критично для маркетинга!)

**Зачем:** Понять, под какие запросы оптимизирован сайт конкурента

**Что анализировать:**
- Ключевые слова в Title
- Ключевые слова в Description
- Ключевые слова в H1
- Ключевые слова в тексте страницы
- Частотность ключевых слов
- Семантическое ядро конкурента

**Как анализировать:**
```python
def extract_semantic_core(pages_data: List[dict]) -> dict:
    """
    Извлекает семантическое ядро из всех страниц
    
    Returns:
    {
        'keywords': {
            'имплантация зубов': {
                'frequency': 15,  # встречается на 15 страницах
                'in_title': 10,   # в title на 10 страницах
                'in_h1': 8,       # в h1 на 8 страницах
                'pages': [...]    # список URL
            },
            'отбеливание зубов': {...},
            ...
        },
        'top_keywords': [
            ('имплантация зубов', 15),
            ('отбеливание зубов', 12),
            ...
        ],
        'categories': {
            'услуги': ['имплантация', 'отбеливание', 'брекеты'],
            'локация': ['москва', 'центр'],
            'бренд': ['название клиники']
        }
    }
    """
    from collections import Counter
    import re
    
    all_keywords = []
    keyword_details = {}
    
    for page in pages_data:
        title = page.get('title', '').lower()
        description = page.get('description', '').lower()
        h1 = page.get('h1', '').lower()
        text = page.get('text', '').lower()
        
        # Extract keywords (2-3 word phrases)
        words = re.findall(r'\b[а-яё]+\b', title + ' ' + description + ' ' + h1)
        
        # Generate 2-3 word phrases
        for i in range(len(words) - 1):
            phrase = ' '.join(words[i:i+2])
            if len(phrase) > 5:  # Skip short phrases
                all_keywords.append(phrase)
                
                if phrase not in keyword_details:
                    keyword_details[phrase] = {
                        'frequency': 0,
                        'in_title': 0,
                        'in_h1': 0,
                        'pages': []
                    }
                
                keyword_details[phrase]['frequency'] += 1
                keyword_details[phrase]['pages'].append(page['url'])
                
                if phrase in title:
                    keyword_details[phrase]['in_title'] += 1
                if phrase in h1:
                    keyword_details[phrase]['in_h1'] += 1
    
    # Count frequency
    counter = Counter(all_keywords)
    top_keywords = counter.most_common(50)
    
    # Categorize keywords
    categories = {
        'услуги': [],
        'локация': [],
        'бренд': []
    }
    
    service_keywords = ['имплантация', 'отбеливание', 'брекеты', 'виниры', 
                        'чистка', 'лечение', 'удаление', 'протезирование']
    location_keywords = ['москва', 'центр', 'метро', 'район']
    
    for keyword, freq in top_keywords:
        if any(service in keyword for service in service_keywords):
            categories['услуги'].append(keyword)
        elif any(loc in keyword for loc in location_keywords):
            categories['локация'].append(keyword)
    
    return {
        'keywords': keyword_details,
        'top_keywords': top_keywords,
        'categories': categories,
        'total_unique_keywords': len(keyword_details)
    }
```

**Формат в отчёте:**

```markdown
## 🎯 Семантическое ядро

### Топ-20 ключевых запросов

| # | Запрос | Частота | В Title | В H1 | Категория |
|---|--------|---------|---------|------|-----------|
| 1 | имплантация зубов | 15 | 10 | 8 | Услуги |
| 2 | отбеливание зубов | 12 | 9 | 7 | Услуги |
| 3 | стоматология москва | 10 | 8 | 5 | Локация |
| 4 | брекеты цена | 8 | 6 | 4 | Услуги |
| 5 | виниры москва | 7 | 5 | 3 | Услуги + Локация |

### Категории запросов

**Услуги (15 запросов):**
- имплантация зубов (15)
- отбеливание зубов (12)
- брекеты цена (8)
- виниры москва (7)
- чистка зубов (6)

**Локация (8 запросов):**
- стоматология москва (10)
- стоматология центр (5)
- клиника метро (4)

**Бренд (3 запроса):**
- [название клиники] (20)
- [название клиники] отзывы (5)

### Сравнение с нашим семантическим ядром

| Наш запрос | У конкурента | Вывод |
|------------|--------------|-------|
| имплантация зубов | ✅ 15 страниц | Сильная конкуренция |
| отбеливание зубов | ✅ 12 страниц | Сильная конкуренция |
| лазерное отбеливание | ❌ 0 страниц | Наша возможность! |
| виниры без обточки | ❌ 0 страниц | Наша возможность! |

**Вывод:** 
- Конкурент сильно оптимизирован под базовые запросы
- Есть возможности в нишевых запросах (лазерное отбеливание, виниры без обточки)
- Рекомендуем фокус на long-tail запросах

### Пробелы в семантике конкурента

**Запросы, которых нет у конкурента:**
1. лазерное отбеливание зубов (наша возможность)
2. виниры без обточки (наша возможность)
3. имплантация за один день (наша возможность)
4. безболезненное лечение зубов (наша возможность)

**Рекомендация:** Создать контент под эти запросы для захвата трафика.
```

---

## 🚀 План реализации

### Phase 1: Добавить детекторы (2-3 часа)
1. CMS Detection
2. Analytics Detection
3. Call-tracking Detection
4. Messengers Detection
5. Marketing Tools Detection

### Phase 2: Добавить анализаторы (1-2 часа)
1. Image Alt Text Analysis
2. Meta Keywords Detection
3. Page Load Time Measurement
4. Geo-Optimization Analysis

### Phase 3: Создать новый формат отчёта (1 час)
1. Шаблон "для людей"
2. Генератор отчёта
3. Экспорт в PDF

### Phase 4: Тестирование (30 минут)
1. Запустить на 6 конкурентах
2. Проверить все детекторы
3. Создать финальный отчёт

**Итого:** 5-6 часов работы

---

## 📝 Следующие шаги

**Завтра (2026-05-06):**
1. Реализовать все детекторы
2. Обновить CI Deep Analyzer
3. Перезапустить анализ 6 конкурентов
4. Создать новый отчёт "для людей"

**Приоритет:** HIGH (это критично для продаж!)

---

**Создано:** 2026-05-05 21:30  
**Статус:** Roadmap  
**Следующий шаг:** Реализация завтра
