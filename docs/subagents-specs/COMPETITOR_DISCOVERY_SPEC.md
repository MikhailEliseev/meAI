# Competitor Discovery Agent — Спецификация

**Дата:** 2026-05-22
**Версия:** 2.0.0
**Приоритет:** P0
**Родительский Magister:** Sales Admin Agent (пресейл)
**Статус:** Спецификация (реализация частичная — competitor_matcher.py)

---

## 1. Обзор

### 1.1 Назначение

Competitor Discovery Agent находит 3 максимально релевантных конкурента для клиники клиента на этапе пресейла. Релевантность определяется по трём осям:

1. **Услуги/направления** — такой же набор услуг и специализаций
2. **Масштаб** — сравнимая выручка, количество сотрудников
3. **Локация** — тот же город, ≤50 км

Агент должен различать:
- **Моно-клиники** (только косметология) → конкуренты только косметология
- **Мульти-клиники** (косметология + стоматология + гинекология) → конкуренты с похожим набором направлений

### 1.2 Почему это важно

**Пресейл — момент максимальной ценности.** Если бот показывает нерелевантных конкурентов ("Клиника концептуальной стоматологии" для косметологии), клиент теряет доверие. Если показывает релевантных — это WOW-эффект, который конвертирует в продажу.

### 1.3 Текущее состояние

`competitor_matcher.py` (1163+ строк) реализует:
- Трёхуровневый discovery: DaData + OSM + Yandex Maps
- Скоринг по 6 компонентам: revenue, location, services, data_quality, popularity, visibility
- Государственный фильтр (ГАУЗ, ГБУЗ, etc.)
- Специализационный фильтр (source_specialization)

**Проблемы (выявлены 2026-05-22):**
1. DaData-кандидаты не попадают в топ-10 (отсутствие координат + нулевой popularity/visibility)
2. Одинаковые скоры у OSM-кандидатов (дифференциация только по location)
3. OSM-специализация определяется поисковым запросом, не реальными услугами
4. Yandex Maps API 403 — невалидный ключ
5. Нет различения моно vs мульти-профильная

---

## 2. Архитектура Discovery Pipeline

### 2.1 Четырёхуровневый Discovery

```
URL клиента
  ↓
Service Extractor → ClientProfile (услуги, специализация, город)
  ↓
┌──────────────────────────────────────────────────────────┐
│ Tier 1: DaData API (suggest/party)                       │
│   Поиск по OKVED + специализации                         │
│   Возвращает: юрлица, ИНН, ОГРН, фин. данные, адрес     │
│   Сила: финансовые данные, юрстатус                      │
│   Слабость: нет координат, рейтингов, сайтов             │
├──────────────────────────────────────────────────────────┤
│ Tier 2: 2GIS API (items/search)                ← НОВЫЙ   │
│   Поиск организаций по рубрикам + гео                    │
│   Возвращает: название, адрес, координаты, телефон,      │
│   сайт, рейтинг Flamp, отзывы, фото, расписание          │
│   Сила: лучший API для РФ, Flamp-рейтинги, точные данные │
├──────────────────────────────────────────────────────────┤
│ Tier 3: OSM Overpass + Nominatim                         │
│   Поиск по amenity типу (dentist/clinic/doctors)         │
│   Возвращает: название, координаты, телефон, сайт        │
│   Сила: находит "скрытые" клиники без юрлица              │
│   Слабость: нет фин. данных, рейтингов                   │
├──────────────────────────────────────────────────────────┤
│ Tier 4: Yandex Geosearch API (search-maps)   ← ПОЧИНИТЬ  │
│   Поиск организаций по тексту + гео                      │
│   Возвращает: название, адрес, координаты, рейтинг,      │
│   категории, телефон, сайт                               │
│   Сила: Яндекс-рейтинги, coverage                        │
└──────────────────────────────────────────────────────────┘
  ↓
Enrichment Layer
  ├─ Geocode DaData-адресов через Yandex/2GIS/Nominatim
  ├─ DaData-обогащение OSM/2GIS/Yandex кандидатов (фин. данные)
  └─ Cross-source deduplication (name similarity + INN)
  ↓
Scoring Layer
  ├─ Service TF-IDF + cosine similarity (из EMM)
  ├─ Revenue matching (фактические данные + estimation)
  ├─ Location scoring (haversine distance)
  ├─ Popularity scoring (ratings + reviews)
  └─ Specialization purity scoring (моно vs мульти)
  ↓
Top-3 CompetitorMatch
```

### 2.2 Приоритет источников

При равных скорах:
1. Кандидаты с реальными фин. данными (data_quality ≥ 0.85)
2. Кандидаты из нескольких источников (2GIS + DaData)
3. Кандидаты с рейтингами и отзывами

---

## 3. Ключевые алгоритмы (из GitHub Research)

### 3.1 TF-IDF + Cosine Similarity для услуг

**Источник:** ING Bank EntityMatchingModel (94★, MIT)

Адаптируем подход: вместо сравнения названий компаний — сравниваем списки услуг.

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def _service_tfidf_score(client_services: list[str], candidate_services: list[str]) -> float:
    """TF-IDF векторизация услуг + cosine similarity."""
    if not client_services or not candidate_services:
        return 0.0
    
    # Объединяем услуги в "документы" (пробелы как разделители)
    client_doc = " ".join(client_services)
    candidate_doc = " ".join(candidate_services)
    
    # Обучаем на лету (маленький корпус)
    vectorizer = TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 2),  # униграммы + биграммы ("лазерная эпиляция")
        lowercase=True,
    )
    
    try:
        tfidf = vectorizer.fit_transform([client_doc, candidate_doc])
        sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
        return float(sim)
    except ValueError:
        return 0.0
```

**Преимущество перед текущим подходом (точное совпадение):**
- "лазерная эпиляция" частично совпадёт с "эпиляция лазером"
- "терапевтическая стоматология" частично совпадёт с "стоматология терапевтическая"
- Улавливает семантическую близость, не только точные совпадения

### 3.2 Cross-lingual Name Matching

**Источник:** Graphlet-AI eridu (4★, Apache 2.0)

Используем SentenceTransformer для сравнения названий клиник на разных языках (русский, английский, транслит).

```python
from sentence_transformers import SentenceTransformer

_model = None

def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(
            "paraphrase-multilingual-MiniLM-L12-v2",
            device="cpu",
        )
    return _model

def _name_embedding_similarity(name1: str, name2: str) -> float:
    """Cross-lingual name similarity via SentenceTransformer."""
    model = _get_model()
    emb1 = model.encode([name1], normalize_embeddings=True)
    emb2 = model.encode([name2], normalize_embeddings=True)
    return float((emb1 @ emb2.T)[0][0])
```

**Применение:**
- Дедупликация кандидатов между источниками (DaData vs OSM vs 2GIS)
- Сравнение названий: "Клиника Академической Косметологии" vs "ООО Академия Косметологии"
- Порог сходства: > 0.75 → один и тот же бизнес

### 3.3 Algorithmic Confidence Scoring

**Источник:** MarketSense-AI (0★, MIT)

Confidence считается по реальным сигналам, не по LLM.

```python
def _compute_confidence(profile: CompanyProfile) -> float:
    """Вычисляет confidence score на основе доступных данных."""
    score = 0.4  # baseline
    
    # Реальные финансовые данные
    if profile.has_real_financials():
        score += 0.25
    
    # Координаты известны
    if profile.geo_lat is not None and profile.geo_lon is not None:
        score += 0.15
    
    # Рейтинг и отзывы
    if profile.rating is not None:
        score += 0.10
    if profile.reviews_count is not None and profile.reviews_count > 0:
        score += 0.05
    
    # Сайт известен
    if profile.website:
        score += 0.05
    
    return min(score, 1.0)
```

### 3.4 Specialization Purity Scoring

**КРИТИЧЕСКИЙ КОМПОНЕНТ.** Отличает моно от мульти-профильных клиник.

```python
def _specialization_compatibility(
    client: ClientProfile,
    candidate: CompanyProfile,
) -> float:
    """Насколько специализация кандидата совместима с клиентом.
    
    Возвращает 0.0 → 1.0, где:
    - 1.0 = одинаковая специализация (оба косметология)
    - 0.5 = кандидат мульти-профильный, клиент моно
    - 0.0 = совершенно разные специализации
    """
    client_spec = client.specialization
    candidate_specs = _candidate_services(client, candidate)
    
    # Моно-клиент: косметология
    if client_spec and len(client.services) <= 5:
        # Проверяем что кандидат ТОЖЕ косметология (не мульти)
        has_client_spec = client_spec in candidate_specs
        # Проверяем что кандидат НЕ содержит других специализаций
        other_specs = [s for s in candidate_specs if s != client_spec
                       and s in SPECIALIZATIONS]
        if has_client_spec and not other_specs:
            return 1.0  # идеально: моно косметология vs моно косметология
        elif has_client_spec and other_specs:
            return 0.6  # кандидат мульти (косметология + стоматология)
        else:
            return 0.0  # совсем другая специализация
    
    # Мульти-клиент
    overlap = len(set(client.services) & set(candidate_specs))
    total = len(client.services)
    return overlap / total if total > 0 else 0.5
```

---

## 4. Scoring Model v2

### 4.1 Обновлённые веса

| Компонент | Вес v1 | Вес v2 | Обоснование |
|-----------|--------|--------|-------------|
| Service Overlap (TF-IDF) | 0.30 | **0.30** | Главный фактор релевантности |
| Specialization Purity | - | **0.15** | НОВЫЙ: моно vs мульти |
| Revenue Match | 0.15 | **0.15** | Масштаб важен |
| Location Score | 0.15 | **0.15** | Гео-близость |
| Popularity | 0.20 | **0.10** | Снижен: не у всех есть рейтинги |
| Visibility | 0.10 | **0.05** | Снижен: не у всех есть сайты |
| Data Quality | 0.10 | **0.10** | Реальные данные > оценки |

**Ключевые изменения:**
- Popularity снижен с 0.20 до 0.10 — не penalize кандидатов без рейтингов
- Visibility снижен с 0.10 до 0.05
- Добавлен Specialization Purity (0.15) — главный дифференциатор моно/мульти
- Убран OSM-бонус (+0.04) — искусственное преимущество

### 4.2 Формула

```python
total = (
    service_overlap * 0.30
    + specialization_purity * 0.15
    + revenue_match * 0.15
    + location_score * 0.15
    + data_quality * 0.10
    + popularity_score * 0.10
    + visibility_score * 0.05
)
```

### 4.3 Service Overlap (TF-IDF версия)

```python
def _score_services_v2(client: ClientProfile, candidate: CompanyProfile) -> float:
    """TF-IDF cosine similarity между услугами клиента и кандидата."""
    candidate_services = _candidate_services(client, candidate)
    
    if not client.services or not candidate_services:
        return 0.0
    
    # TF-IDF similarity (основной сигнал)
    tfidf_sim = _service_tfidf_score(client.services, candidate_services)
    
    # Jaccard similarity (дополнительный сигнал)
    client_set = set(client.services)
    cand_set = set(candidate_services)
    jaccard = len(client_set & cand_set) / len(client_set | cand_set) if client_set | cand_set else 0.0
    
    # Комбинируем: 70% TF-IDF + 30% Jaccard
    return 0.7 * tfidf_sim + 0.3 * jaccard
```

### 4.4 Location Score (с геокодированием для DaData)

```python
async def _score_location_v2(
    client: ClientProfile,
    candidate: CompanyProfile,
    geocoder: GeocoderService,
) -> float:
    """Location scoring с обязательным геокодированием DaData-адресов."""
    # Пытаемся получить координаты
    lat, lon = candidate.geo_lat, candidate.geo_lon
    
    if lat is None and candidate.legal_address:
        # Геокодируем адрес (Yandex/2GIS/Nominatim)
        coords = await geocoder.geocode(candidate.legal_address)
        if coords:
            lat, lon = coords
            candidate.geo_lat, candidate.geo_lon = lat, lon  # cache
    
    if lat is not None and lon is not None and client.city_lat and client.city_lon:
        distance = _haversine(client.city_lat, client.city_lon, lat, lon)
        return max(0.0, 1.0 - min(distance / 50.0, 1.0))
    
    # Fallback: city name match
    if client.city and client.city.lower() in (candidate.legal_address or "").lower():
        return 0.7
    
    return 0.3  # unknown
```

---

## 5. Входные данные

### 5.1 ClientProfile (из service_extractor.py)

```python
@dataclass
class ClientProfile:
    url: str                              # URL сайта клиники
    specialization: str = ""              # "косметология", "стоматология", etc.
    city: str = ""                        # "Москва", "Казань", etc.
    services: list[str] = []              # Извлечённые услуги
    estimated_revenue: Optional[int] = None
    company_name: Optional[str] = None    # Название клиники с сайта
    inn: Optional[str] = None             # ИНН если найден на сайте
    city_lat: Optional[float] = None      # Геокодированный центр города
    city_lon: Optional[float] = None
```

### 5.2 Внешние API ключи

```bash
# .env
DADATA_API_KEY=xxx          # DaData suggest/party (бесплатно 10k/день)
DADATA_SECRET_KEY=xxx       # Для финансовых данных
YANDEX_MAPS_API_KEY=xxx     # HTTP Геокодер ключ (не JS API!)
TWOGIS_API_KEY=xxx          # 2GIS Platform demo key
```

### 5.3 Параметры поиска

```python
SEARCH_RADIUS_M = 15000     # 15 км радиус поиска
MAX_DISTANCE_KM = 50.0      # максимальная дистанция
MAX_RESULTS = 3             # топ-3 на выход
MAX_CANDIDATES_PER_SOURCE = 30  # максимум кандидатов от каждого источника
```

---

## 6. Выходные данные

### 6.1 CompetitorMatch (расширенный)

```python
@dataclass
class CompetitorMatch:
    profile: CompanyProfile
    
    # Обогащённые данные
    website: Optional[str] = None
    phone: Optional[str] = None
    services: list[str] = []           # общие услуги с клиентом
    
    # Скоринг (0.0 – 1.0)
    service_overlap: float = 0.0       # TF-IDF cosine similarity услуг
    specialization_match: float = 0.0  # НОВЫЙ: совместимость специализаций
    revenue_match: float = 0.0
    location_score: float = 0.0
    popularity_score: float = 0.0
    visibility_score: float = 0.0
    data_quality: float = 0.7
    total_score: float = 0.0
    
    # Объяснение
    match_reason: str = ""             # "схожий масштаб, рядом, те же услуги"
    match_strengths: list[str] = []    # ["revenue", "services", "location"]
    match_weaknesses: list[str] = []   # ["no_financials", "far_away"]
```

### 6.2 API Response

```json
{
  "success": true,
  "url": "https://delight-lancette.ru/",
  "competitors": [
    {
      "inn": "7723011982",
      "legal_name": "ООО «Линлайн»",
      "brand_name": "Клиника Линлайн",
      "revenue_year": 45000000,
      "employee_count": 25,
      "legal_address": "г Москва, ул. Профсоюзная, д. 104",
      "geo_lat": 55.6488,
      "geo_lon": 37.5397,
      "data_source": "2gis+dadata",
      "confidence": 0.85,
      "services": ["косметология", "лазерная эпиляция", "дерматология"],
      "service_overlap": 0.78,
      "specialization_match": 1.0,
      "revenue_match": 0.88,
      "location_score": 0.91,
      "popularity_score": 0.72,
      "total_score": 0.82,
      "match_reason": "те же услуги, схожий масштаб, рядом (3.2 км), реальные фин. данные",
      "match_strengths": ["services", "specialization", "revenue", "location"],
      "match_weaknesses": []
    }
  ]
}
```

---

## 7. Интеграция с другими агентами

### 7.1 Pre-Sale Flow (Sales Admin Agent)

```
Sales Admin Agent
  ↓ run_seo_audit(url)
  ↓ показывает WOW-цифры
  ↓ предлагает найти конкурентов
  ↓
Competitor Discovery Agent
  ├─ find_competitors(url)
  ├─ возвращает топ-3
  ↓
Sales Admin Agent
  ↓ показывает конкурентов клиенту
  ↓ "Подходят для сравнения?"
  ↓
Client: "Да" / "Вот мои: clinic-X.ru"
  ↓
present_competitors(status, competitors)
  ↓ сохраняет в pre-sale/competitors/
  ↓
[Если горячий лид] → Competitor Analysis Agent (CI)
[Если холодный] → сбор контакта
```

### 7.2 Competitor Intelligence Agent

Получает найденных конкурентов для глубокого CI-анализа:
- Технический аудит сайтов конкурентов
- SEO-анализ (ключевые слова, позиции)
- Контент-анализ (качество, полнота)
- Сравнительный отчёт для клиента

### 7.3 Hermes Tools

```python
# hermes/app/tools/find_competitors.py
async def find_competitors(url: str) -> dict:
    """Найти 3 похожих конкурентов для клиники."""
    ...

# hermes/app/tools/present_competitors.py
async def present_competitors(
    status: str,  # "approved" | "client_suggested" | "reroll"
    competitors: list[dict] | None = None,
) -> dict:
    """Зафиксировать выбор конкурентов клиентом."""
    ...
```

---

## 8. План реализации

### Фаза 1: Критические фиксы (день 1)

| # | Задача | Файл | Трудоёмкость |
|---|--------|------|-------------|
| 1 | Убрать OSM-бонус (+0.04) | competitor_matcher.py | 5 мин |
| 2 | Добавить геокодирование DaData-адресов | competitor_matcher.py | 1 час |
| 3 | Понизить веса popularity (0.10) и visibility (0.05) | competitor_matcher.py | 5 мин |
| 4 | Добавить Specialization Purity в scoring | competitor_matcher.py | 3 часа |
| 5 | Заменить точное совпадение услуг на TF-IDF + Jaccard | competitor_matcher.py | 2 часа |
| 6 | Починить Yandex Maps ключ (получить "HTTP Геокодер") | .env + yandex_maps.py | 1 час |

### Фаза 2: 2GIS Integration (день 2)

| # | Задача | Файл | Трудоёмкость |
|---|--------|------|-------------|
| 7 | Создать 2GIS API client | services/twogis_client.py | 4 часа |
| 8 | Интегрировать 2GIS в discovery pipeline | competitor_matcher.py | 2 часа |
| 9 | Добавить Flamp-рейтинги в popularity scoring | competitor_matcher.py | 1 час |

### Фаза 3: Embedding Matching (день 3)

| # | Задача | Файл | Трудоёмкость |
|---|--------|------|-------------|
| 10 | Установить sentence-transformers | requirements.txt | 10 мин |
| 11 | Реализовать cross-lingual name matching | competitor_matcher.py | 2 часа |
| 12 | Заменить текущую _name_similarity на embedding-based | competitor_matcher.py | 1 час |
| 13 | Улучшить дедупликацию (DaData vs OSM vs 2GIS) | competitor_matcher.py | 2 часа |

### Фаза 4: Тестирование и деплой (день 4)

| # | Задача | Трудоёмкость |
|---|--------|-------------|
| 14 | Интеграционный тест: 3 разных клиники (космето, стомато, мульти) | 3 часа |
| 15 | Деплой на сервер + валидация логов | 1 час |
| 16 | A/B сравнение результатов v1 vs v2 | 1 час |

---

## 9. Метрики успеха

### 9.1 Технические метрики

| Метрика | Текущая (v1) | Цель (v2) | Измерение |
|---------|-------------|-----------|-----------|
| DaData кандидатов в топ-3 | 0 из 3 | ≥ 1 из 3 | Логи scoring |
| Дифференциация скоров (std dev) | ~0.01 | ≥ 0.05 | Логи scoring |
| Точность специализации (моно vs мульти) | 0% | ≥ 90% | Ручная проверка |
| Покрытие координатами | ~40% | ≥ 80% | geo_lat != None |
| Доступность Yandex Maps | 0% | 100% | HTTP 200 |
| Время ответа | ~8s | ≤ 5s | API timing |

### 9.2 Бизнес-метрики

| Метрика | Цель | Измерение |
|---------|------|-----------|
| Конверсия "показали конкурентов → одобрили" | ≥ 70% | pre-sale/decisions/ |
| Конверсия "одобрили → оставили контакт" | ≥ 50% | lead_capture |
| Релевантность (клиент согласен с подбором) | ≥ 80% | Отзывы в чате |

---

## 10. Зависимости

### 10.1 Новые Python пакеты

```
sentence-transformers>=3.0.0   # Cross-lingual name embeddings (из eridu)
scikit-learn>=1.3.0            # TF-IDF + cosine similarity (из EMM)
```

### 10.2 Новые API ключи

```
TWOGIS_API_KEY                 # platform.2gis.ru → "Демо-ключ"
YANDEX_MAPS_API_KEY (новый)    # developer.tech.yandex.ru → "HTTP Геокодер"
```

### 10.3 Существующие зависимости

- `competitor_matcher.py` — основной файл (рефакторинг)
- `rusprofile/client.py` — DaData API (без изменений)
- `rusprofile/models.py` — CompanyProfile, ClientProfile, CompetitorMatch (расширить)
- `osm_discovery.py` — OSM Overpass + Nominatim (без изменений)
- `yandex_maps.py` — Yandex Geosearch (починить ключ)
- `service_extractor.py` — извлечение услуг с сайта (без изменений)

---

## 11. Обработка ошибок

### 11.1 Отказы источников

```python
async def _discover_with_fallback(client: ClientProfile) -> list[CompanyProfile]:
    """Последовательный discovery с fallback."""
    candidates = []
    
    # Tier 1: DaData (must have)
    try:
        dadata = await _search_dadata(client)
        candidates.extend(dadata)
    except Exception as e:
        logger.error("DaData discovery failed: %s", e)
    
    # Tier 2: 2GIS (primary geo)
    try:
        twogis = await _search_2gis(client)
        candidates.extend(twogis)
    except Exception as e:
        logger.warning("2GIS discovery failed: %s", e)
    
    # Tier 3: OSM (fallback geo)
    try:
        osm = await _search_osm(client)
        candidates.extend(osm)
    except Exception as e:
        logger.warning("OSM discovery failed: %s", e)
    
    # Tier 4: Yandex (optional enrichment)
    try:
        yandex = await _search_yandex(client)
        candidates.extend(yandex)
    except Exception as e:
        logger.info("Yandex Maps skipped: %s", e)
    
    if not candidates:
        raise CompetitorDiscoveryError("All discovery sources failed")
    
    return candidates
```

### 11.2 Таймауты и retry

```python
# Per-source timeouts
SOURCE_TIMEOUTS = {
    "dadata": 10.0,
    "2gis": 5.0,
    "osm": 15.0,    # Overpass может быть медленным
    "yandex": 10.0,
}

# Retry: только для transient failures
RETRYABLE_ERRORS = (httpx.TimeoutException, httpx.NetworkError)
MAX_RETRIES = 2
```

### 11.3 Минимальный viable результат

Если все источники вернули мало кандидатов (< 5), ослабляем фильтры:
1. Расширяем радиус поиска (15 км → 50 км)
2. Ослабляем специализационный фильтр
3. Возвращаем лучших из того что есть, с пометкой `confidence: low`

---

## 12. Тестирование

### 12.1 Тестовые сценарии

```python
TEST_CASES = [
    {
        "name": "Моно-косметология Москва",
        "url": "https://delight-lancette.ru/",
        "expected_specialization": "косметология",
        "expected_city": "Москва",
        "check": [
            "топ-3 без стоматологий",
            "все в Москве или ≤50 км",
            "service_overlap ≥ 0.3 у всех",
            "хотя бы 1 DaData кандидат в топ-3",
        ],
    },
    {
        "name": "Моно-стоматология Казань",
        "url": "https://stomat-kazan.ru/",
        "expected_specialization": "стоматология",
        "check": [
            "топ-3 только стоматология",
            "service_overlap ≥ 0.3",
        ],
    },
    {
        "name": "Мульти-клиника (космето + стомато + гинеко)",
        "url": "https://example-multi-clinic.ru/",
        "expected_specialization": "многопрофильная клиника",
        "check": [
            "топ-3 с похожим набором направлений",
            "не моно-клиники",
        ],
    },
]
```

### 12.2 Unit тесты

```python
# tests/services/test_competitor_discovery.py

def test_service_tfidf_exact_match():
    client = ["косметология", "лазерная эпиляция"]
    candidate = ["косметология", "лазерная эпиляция"]
    assert _service_tfidf_score(client, candidate) > 0.9

def test_service_tfidf_partial_match():
    client = ["лазерная эпиляция", "косметология"]
    candidate = ["эпиляция лазером", "косметолог"]
    assert _service_tfidf_score(client, candidate) > 0.3  # частичное совпадение

def test_service_tfidf_no_match():
    client = ["косметология", "лазерная эпиляция"]
    candidate = ["стоматология", "имплантация"]
    assert _service_tfidf_score(client, candidate) < 0.3

def test_specialization_purity_mono_vs_mono():
    client = ClientProfile(specialization="косметология", services=["косметология", "эпиляция"])
    candidate = CompanyProfile(legal_name="Клиника косметологии", source_specialization="косметология")
    assert _candidate_services(client, candidate) == ["косметология", "терапия"]
    # Должен быть высокий purity score

def test_specialization_purity_mono_vs_multi():
    client = ClientProfile(specialization="косметология", services=["косметология"])
    candidate = CompanyProfile(legal_name="Медицинский центр", source_specialization="косметология")
    # Кандидат на самом деле мульти-профильный, хоть и tagged как косметология
    # Purity score должен быть ниже
```

---

## 13. TODO / Future Research

### 🔴 CRITICAL (сделать сейчас)
1. Починить Yandex Maps API ключ — получить "HTTP Геокодер" ключ
2. Убрать OSM-бонус, перебалансировать веса
3. Добавить TF-IDF matching для услуг
4. Добавить Specialization Purity scoring
5. Геокодировать DaData-адреса

### 🟡 HIGH (следующий спринт)
6. Интегрировать 2GIS API как Tier 2
7. Cross-lingual name embeddings (SentenceTransformer)
8. Улучшить дедупликацию между источниками

### 🟢 LOW (бэклог)
9. Flamp API для рейтингов (если 2GIS недостаточно)
10. Google Maps как дополнительный источник
11. Prodoctorov.ru scraping для врачебных клиник
12. CompanyKG2 графовые эмбеддинги (KDD 2024) — если будет 100k+ кандидатов

---

## Приложение A: GitHub Research Sources

| Репозиторий | Звёзды | Что взяли |
|-------------|--------|-----------|
| [ing-bank/EntityMatchingModel](https://github.com/ing-bank/EntityMatchingModel) | 94 | TF-IDF + cosine similarity для matching |
| [dedupeio/dedupe](https://github.com/dedupeio/dedupe) | 4,466 | Активное обучение, блокировка кандидатов |
| [Graphlet-AI/eridu](https://github.com/Graphlet-AI/eridu) | 4 | Cross-lingual SentenceTransformer эмбеддинги |
| [llcresearch/CompanyKG2](https://github.com/llcresearch/CompanyKG2) | 21 | KDD 2024: графовые эмбеддинги, competitor retrieval бенчмарки |
| [sudo-Harshk/MarketSense-AI](https://github.com/sudo-Harshk/MarketSense-AI) | 0 | Algorithmic confidence scoring, quality URL guard |
| [eddiepease/company2vec](https://github.com/eddiepease/company2vec) | 49 | Усреднение word embeddings для профиля компании |
| [guy-hartstein/company-research-agent](https://github.com/guy-hartstein/company-research-agent) | 1,894 | Multi-agent LangGraph архитектура для исследования компаний |

## Приложение B: API Research Summary

| API | Статус | Бесплатно/день | Ключ |
|-----|--------|---------------|------|
| DaData suggest/party | ✅ Работает | 10,000 | DADATA_API_KEY |
| 2GIS Places API | 🔴 Нет ключа | Demo (тестирование) | platform.2gis.ru |
| OSM Overpass | ✅ Работает | ∞ (rate-limited) | Не нужен |
| Yandex Geosearch | 🔴 403 ошибка | 1,000 | Нужен новый "HTTP Геокодер" |
| Yandex Geocoder | 🔴 403 ошибка | 1,000 | Тот же ключ |
| Google Places | 🔴 Не используется | $200/мес кредит | GCP проект |

---

**Changelog:**
- 2026-05-22: v2.0.0 — Полная спецификация на основе GitHub + API research. Добавлены TF-IDF matching, specialization purity, 2GIS integration, cross-lingual embeddings, перебалансированы scoring веса.

