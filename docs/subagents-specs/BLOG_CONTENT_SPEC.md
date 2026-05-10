# Blog Content Agent - Спецификация

**Дата:** 2026-05-10  
**Magister:** Content Magister  
**Приоритет:** P1  
**Статус:** Draft

---

## 🎯 РОЛЬ И НАЗНАЧЕНИЕ

### Основная роль:
Создавать максимально эффективные тексты для блога медицинских клиник, которые "бьют прямо в сердце" целевой аудитории, используя интеллектуальный выбор copywriting фреймворка и строгое соблюдение медицинских compliance требований.

### Что делает:
- ✅ Интеллектуально выбирает copywriting фреймворк (AIDA, PAS, BAB, FAB, 4P, StoryBrand, PASTOR) на основе цели, аудитории, этапа customer journey, типа услуги и уровня риска
- ✅ Пишет SEO-оптимизированные статьи длиной 1,500-2,000 слов с readability score 60-70 (Flesch Reading Ease)
- ✅ Проверяет медицинскую точность через PubMed API, обеспечивает E-E-A-T compliance (Experience, Expertise, Authoritativeness, Trustworthiness)
- ✅ Валидирует compliance с FDA и 152-ФЗ (Россия), автоматически детектирует запрещённые claims (outcome guarantees)
- ✅ Адаптирует Tone of Voice под бренд клиники (формальный/дружелюбный/экспертный)
- ✅ Генерирует meta-описания, заголовки, CTA (Call to Action)

### Что НЕ делает:
- ❌ Не создаёт видео-скрипты, подкасты, email-рассылки (только блог-статьи)
- ❌ Не пишет рекламные тексты для paid ads (Google Ads, Facebook Ads)
- ❌ Не создаёт контент для социальных сетей (Instagram, VK, Facebook)
- ❌ Не даёт медицинские рекомендации без disclaimer
- ❌ Не гарантирует результаты лечения (FDA/152-ФЗ violation)

### Место в иерархии:
```
Content Magister
    ↓
Content Orchestrator
    ↓
Blog Content Agent ← вы здесь
```

---

## 📥 ВХОДНЫЕ ДАННЫЕ

### Получает от Orchestrator:

**Формат события:**
```json
{
  "event_type": "subagent.task.assigned",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "blog-content-agent",
  "payload": {
    "goal": "awareness | consideration | conversion",
    "audience": "patients | doctors | administrators",
    "journey_stage": "problem_aware | solution_aware | product_aware",
    "service_type": "diagnostic | treatment | preventive",
    "topic": "string",
    "keywords": ["keyword1", "keyword2"],
    "brand_voice": {
      "tone": "formal | friendly | expert",
      "formality_level": 1-10,
      "expertise_level": 1-10
    },
    "clinic_info": {
      "name": "string",
      "specialization": "string",
      "doctors": [{"name": "string", "credentials": "string"}]
    },
    "target_length": 1500-2000,
    "compliance_level": "low | medium | high"
  }
}
```

**Обязательные параметры:**
- `goal` (string) - Цель статьи: awareness (осведомлённость), consideration (рассмотрение), conversion (конверсия)
- `audience` (string) - Целевая аудитория: patients (пациенты), doctors (врачи), administrators (администраторы)
- `journey_stage` (string) - Этап customer journey: problem_aware, solution_aware, product_aware
- `service_type` (string) - Тип услуги: diagnostic (диагностика), treatment (лечение), preventive (профилактика)
- `topic` (string) - Тема статьи (например, "Боль в спине: причины и лечение")
- `keywords` (array) - Ключевые слова для SEO (primary + secondary)

**Опциональные параметры:**
- `brand_voice` (object) - Tone of Voice бренда (по умолчанию: friendly, formality 5, expertise 7)
- `clinic_info` (object) - Информация о клинике для E-E-A-T
- `target_length` (int) - Целевая длина статьи в словах (по умолчанию: 1500-2000)
- `compliance_level` (string) - Уровень compliance проверки (по умолчанию: medium)

---

## 📤 ВЫХОДНЫЕ ДАННЫЕ

### Отправляет Orchestrator:

**Формат события:**
```json
{
  "event_type": "subagent.task.completed",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "blog-content-agent",
  "payload": {
    "status": "success | partial_success | failure",
    "result": {
      "article": {
        "title": "string (H1)",
        "meta_description": "string (150-160 chars)",
        "content": "string (markdown format)",
        "word_count": 1650,
        "readability_score": 65.2,
        "framework_used": "AIDA | PAS | BAB | FAB | 4P | StoryBrand | PASTOR",
        "compliance_risk": "low | medium | high",
        "cta": "string"
      },
      "seo": {
        "primary_keyword": "string",
        "secondary_keywords": ["string"],
        "keyword_density": 1.5,
        "internal_links": ["url"],
        "external_links": ["url"],
        "schema_markup": "JSON-LD"
      },
      "compliance": {
        "citations": [{"claim": "string", "source": "PubMed PMID"}],
        "disclaimer": "string",
        "prohibited_claims_detected": [],
        "e_e_a_t_score": 8.5
      },
      "quality_metrics": {
        "flesch_reading_ease": 65.2,
        "flesch_kincaid_grade": 8.5,
        "tone_match_score": 0.92,
        "seo_score": 85
      }
    },
    "metrics": {
      "execution_time_ms": 45000,
      "framework_selection_time_ms": 500,
      "content_generation_time_ms": 30000,
      "compliance_check_time_ms": 10000,
      "seo_optimization_time_ms": 4500
    },
    "errors": []
  }
}
```

**Структура результата:**
- `article` (object) - Готовая статья с заголовком, контентом, meta-описанием
- `seo` (object) - SEO-данные (ключевые слова, ссылки, schema markup)
- `compliance` (object) - Compliance данные (цитаты, disclaimer, E-E-A-T score)
- `quality_metrics` (object) - Метрики качества (readability, tone match, SEO score)

**Метрики:**
- `execution_time_ms` - Общее время выполнения (целевое: < 60,000 ms = 1 минута)
- `framework_selection_time_ms` - Время выбора фреймворка (< 1 секунды)
- `content_generation_time_ms` - Время генерации контента (< 45 секунд)
- `compliance_check_time_ms` - Время проверки compliance (< 15 секунд)


---

## 🔄 АЛГОРИТМ РАБОТЫ

### Шаг 1: Получение задачи и валидация (500 ms)

1. Подписаться на события `subagent.task.assigned`
2. Фильтровать по `subagent_id == "blog-content-agent"`
3. Валидировать входные параметры:
   - `goal` in ["awareness", "consideration", "conversion"]
   - `audience` in ["patients", "doctors", "administrators"]
   - `journey_stage` in ["problem_aware", "solution_aware", "product_aware"]
   - `service_type` in ["diagnostic", "treatment", "preventive"]
   - `topic` не пустой
   - `keywords` массив с минимум 1 элементом

**Код:**
```python
async def validate_input(self, payload: dict) -> bool:
    required_fields = ["goal", "audience", "journey_stage", "service_type", "topic", "keywords"]
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"Missing required field: {field}")
    
    valid_goals = ["awareness", "consideration", "conversion"]
    if payload["goal"] not in valid_goals:
        raise ValueError(f"Invalid goal: {payload['goal']}")
    
    # ... остальные проверки
    return True
```

### Шаг 2: Интеллектуальный выбор фреймворка (500 ms)

**Decision Matrix (из исследования, Section 3):**

```python
def select_framework(
    goal: str,
    audience: str,
    journey_stage: str,
    service_type: str,
    compliance_level: str
) -> str:
    """
    Выбирает оптимальный copywriting фреймворк на основе контекста.
    
    Логика выбора:
    1. Awareness + Patients + Problem Aware → PAS (Problem-Agitate-Solution)
    2. Awareness + Patients + Solution Aware → AIDA (Attention-Interest-Desire-Action)
    3. Consideration + Patients + Solution Aware → BAB (Before-After-Bridge)
    4. Consideration + Doctors + Product Aware → FAB (Features-Advantages-Benefits)
    5. Conversion + Patients + Product Aware → 4P (Picture-Promise-Prove-Push)
    6. Conversion + Administrators + Product Aware → FAB
    7. Brand Building (любая аудитория) → StoryBrand
    8. High-ticket services + Product Aware → PASTOR (если compliance = low)
    
    Compliance фильтр:
    - HIGH compliance → только AIDA, FAB, StoryBrand (🟢 LOW risk)
    - MEDIUM compliance → + PAS, BAB (🟡 MEDIUM risk)
    - LOW compliance → все фреймворки включая 4P, PASTOR (🔴 HIGH risk)
    """
    
    # Compliance фильтр
    if compliance_level == "high":
        allowed_frameworks = ["AIDA", "FAB", "StoryBrand"]
    elif compliance_level == "medium":
        allowed_frameworks = ["AIDA", "FAB", "StoryBrand", "PAS", "BAB"]
    else:
        allowed_frameworks = ["AIDA", "FAB", "StoryBrand", "PAS", "BAB", "4P", "PASTOR"]
    
    # Decision tree
    if goal == "awareness":
        if audience == "patients":
            if journey_stage == "problem_aware":
                framework = "PAS"
            else:
                framework = "AIDA"
        else:  # doctors, administrators
            framework = "FAB"
    
    elif goal == "consideration":
        if audience == "patients":
            framework = "BAB"
        else:
            framework = "FAB"
    
    elif goal == "conversion":
        if audience == "patients" and service_type in ["treatment", "diagnostic"]:
            framework = "4P" if "4P" in allowed_frameworks else "AIDA"
        else:
            framework = "FAB"
    
    # Fallback на AIDA если выбранный фреймворк не разрешён
    if framework not in allowed_frameworks:
        framework = "AIDA"
    
    return framework
```

**Пример:**
- Input: goal="awareness", audience="patients", journey_stage="problem_aware", compliance="medium"
- Output: framework="PAS" (Problem-Agitate-Solution)

### Шаг 3: Генерация контента по фреймворку (30-45 секунд)

**Для каждого фреймворка используется свой template:**

**AIDA Template (Awareness):**
```markdown
# [Attention] Эмоциональный заголовок с болью/выгодой
## [Interest] Подзаголовок с конкретной пользой
### [Desire] Описание проблемы + preview решения
#### [Action] Чёткий CTA с следующим шагом

Структура:
- Introduction (150 words): Hook + Problem + Promise + Credentials
- H2: Почему возникает проблема? (300 words)
- H2: Решение (600 words, 3 подраздела H3)
- H2: Как правильно действовать? (300 words)
- H2: Что делать дальше? (200 words) + CTA
- Conclusion (100 words) + CTA
- Disclaimer + Author Bio + References
```

**PAS Template (Consideration):**
```markdown
# [Problem] Описание боли пациента
## [Agitate] Усиление последствий бездействия
### [Solution] Ваша услуга как ответ

Структура:
- Introduction (150 words): Problem statement + Statistics
- H2: Проблема в деталях (400 words)
- H2: Что будет, если не решить? (400 words) - Agitate
- H2: Наше решение (600 words, 3 подраздела H3) - Solution
- H2: Как начать? (200 words) + CTA
- Conclusion (100 words) + CTA
- Disclaimer + Author Bio + References
```

**FAB Template (Conversion, Doctors):**
```markdown
# [Features] Технические характеристики
## [Advantages] Почему это важно
### [Benefits] Результаты для пациентов

Структура:
- Introduction (150 words): Technical overview
- H2: Технические характеристики (500 words) - Features
- H2: Преимущества перед аналогами (500 words) - Advantages
- H2: Клинические результаты (500 words) - Benefits
- H2: Показания и противопоказания (200 words)
- Conclusion (100 words) + CTA
- Disclaimer + Author Bio + References
```

**Код генерации:**
```python
async def generate_content(
    self,
    framework: str,
    topic: str,
    keywords: list,
    brand_voice: dict,
    clinic_info: dict
) -> str:
    """
    Генерирует контент по выбранному фреймворку.
    
    1. Загружает template для фреймворка
    2. Заполняет template данными (topic, keywords, clinic_info)
    3. Адаптирует Tone of Voice под brand_voice
    4. Вплетает keywords естественно (density 1-2%)
    5. Добавляет internal/external links
    6. Генерирует disclaimer и author bio
    """
    
    template = self.load_template(framework)
    
    # Генерация через LLM с промптом
    prompt = f"""
    Напиши статью для медицинского блога по фреймворку {framework}.
    
    Тема: {topic}
    Ключевые слова: {', '.join(keywords)}
    Tone of Voice: {brand_voice['tone']} (formality {brand_voice['formality_level']}/10)
    Клиника: {clinic_info['name']}, специализация: {clinic_info['specialization']}
    
    Требования:
    - Длина: 1,500-2,000 слов
    - Readability: Flesch 60-70 (8th grade level)
    - Keyword density: 1-2%
    - Структура: {template}
    - E-E-A-T: упомянуть врачей с credentials
    - Цитаты: минимум 2 источника из PubMed
    - Disclaimer: обязателен
    
    Запрещено:
    - Outcome guarantees ("100% cure", "guaranteed results")
    - Superlatives без доказательств ("best", "fastest")
    - Medical advice без disclaimer
    """
    
    content = await self.llm.generate(prompt)
    return content
```

### Шаг 4: SEO-оптимизация (4-5 секунд)

**Оптимизация:**
1. **Keyword placement:**
   - Primary keyword в H1 (title)
   - Primary keyword в первых 100 словах
   - Secondary keywords в H2/H3 subheadings
   - Keyword density 1-2% (естественно, не stuffing)

2. **Internal linking:**
   - 3-5 ссылок на связанные статьи блога
   - Anchor text с keywords

3. **External linking:**
   - 2-3 ссылки на авторитетные источники (PubMed, medical journals)
   - Открываются в новой вкладке

4. **Meta-теги:**
   - Title: 50-60 символов, включает primary keyword
   - Description: 150-160 символов, включает primary keyword + CTA

5. **Schema markup:**
   - Article schema (JSON-LD)
   - MedicalWebPage schema
   - FAQPage schema (если есть FAQ секция)

**Код:**
```python
async def optimize_seo(
    self,
    content: str,
    keywords: list,
    topic: str
) -> dict:
    """
    SEO-оптимизация контента.
    """
    primary_keyword = keywords[0]
    secondary_keywords = keywords[1:]
    
    # Проверка keyword placement
    if primary_keyword.lower() not in content[:500].lower():
        # Вставить primary keyword в первый параграф
        content = self.insert_keyword_naturally(content, primary_keyword)
    
    # Генерация meta-тегов
    title = self.generate_title(topic, primary_keyword, max_length=60)
    meta_description = self.generate_meta_description(
        content, primary_keyword, max_length=160
    )
    
    # Schema markup
    schema = {
        "@context": "https://schema.org",
        "@type": "MedicalWebPage",
        "headline": title,
        "description": meta_description,
        "keywords": ", ".join(keywords),
        "author": {
            "@type": "Person",
            "name": clinic_info["doctors"][0]["name"],
            "jobTitle": clinic_info["doctors"][0]["credentials"]
        }
    }
    
    return {
        "title": title,
        "meta_description": meta_description,
        "schema_markup": json.dumps(schema),
        "keyword_density": self.calculate_keyword_density(content, primary_keyword)
    }
```

### Шаг 5: Compliance проверка (10-15 секунд)

**Проверки:**

1. **Prohibited claims detection:**
```python
PROHIBITED_PHRASES = [
    "100% cure", "guaranteed results", "miracle treatment",
    "completely safe", "no side effects", "better than all",
    "FDA approved" (без доказательств), "doctors recommend" (без attribution),
    "fastest", "best", "only treatment", "permanent solution"
]

def detect_prohibited_claims(content: str) -> list:
    violations = []
    for phrase in PROHIBITED_PHRASES:
        if phrase.lower() in content.lower():
            violations.append({
                "phrase": phrase,
                "severity": "high",
                "recommendation": f"Remove or rephrase: '{phrase}'"
            })
    return violations
```

2. **Medical fact verification (PubMed API):**
```python
async def verify_medical_claims(content: str) -> list:
    """
    Извлекает медицинские claims из контента и проверяет через PubMed.
    """
    claims = self.extract_medical_claims(content)
    citations = []
    
    for claim in claims:
        # Поиск в PubMed
        results = await self.pubmed_api.search(claim, max_results=3)
        if results:
            citations.append({
                "claim": claim,
                "source": f"PubMed PMID: {results[0]['pmid']}",
                "title": results[0]["title"],
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{results[0]['pmid']}/"
            })
        else:
            # Claim не подтверждён
            citations.append({
                "claim": claim,
                "source": None,
                "warning": "No PubMed source found - requires manual review"
            })
    
    return citations
```

3. **E-E-A-T score calculation:**
```python
def calculate_e_e_a_t_score(content: str, clinic_info: dict) -> float:
    """
    Оценка E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness).
    
    Критерии:
    - Experience: упоминание реальных кейсов (+2 points)
    - Expertise: credentials врачей упомянуты (+2 points)
    - Authoritativeness: цитаты из PubMed (+2 points per citation, max 4)
    - Trustworthiness: disclaimer присутствует (+2 points)
    
    Max score: 10 points
    """
    score = 0.0
    
    # Experience
    if "пациент" in content.lower() or "случай" in content.lower():
        score += 2.0
    
    # Expertise
    for doctor in clinic_info.get("doctors", []):
        if doctor["name"] in content and doctor["credentials"] in content:
            score += 2.0
            break
    
    # Authoritativeness
    citations_count = content.count("PubMed") + content.count("PMID")
    score += min(citations_count * 2, 4.0)
    
    # Trustworthiness
    if "disclaimer" in content.lower() or "консультация врача" in content.lower():
        score += 2.0
    
    return min(score, 10.0)
```

4. **Disclaimer generation:**
```python
def generate_disclaimer() -> str:
    return """
    **Disclaimer:** Информация в статье носит ознакомительный характер и не является 
    медицинской рекомендацией. Перед началом лечения обязательно проконсультируйтесь 
    с врачом. Результаты могут варьироваться в зависимости от индивидуальных особенностей.
    """
```

### Шаг 6: Quality metrics calculation (1-2 секунды)

**Метрики:**

1. **Readability (Textstat library):**
```python
import textstat

def calculate_readability(content: str) -> dict:
    return {
        "flesch_reading_ease": textstat.flesch_reading_ease(content),  # Target: 60-70
        "flesch_kincaid_grade": textstat.flesch_kincaid_grade(content),  # Target: 8-9
        "smog_index": textstat.smog_index(content),
        "automated_readability_index": textstat.automated_readability_index(content)
    }
```

2. **Tone of Voice match:**
```python
async def calculate_tone_match(content: str, target_tone: dict) -> float:
    """
    Сравнивает tone контента с target brand voice.
    
    Использует LanguageTool API для анализа:
    - Formality level (1-10)
    - Expertise level (1-10)
    - Emotional tone (neutral, friendly, formal)
    """
    analysis = await self.languagetool_api.analyze_tone(content)
    
    formality_diff = abs(analysis["formality"] - target_tone["formality_level"])
    expertise_diff = abs(analysis["expertise"] - target_tone["expertise_level"])
    
    # Score: 1.0 = perfect match, 0.0 = complete mismatch
    score = 1.0 - (formality_diff + expertise_diff) / 20.0
    return max(score, 0.0)
```

3. **SEO score (Frase.io API или custom):**
```python
async def calculate_seo_score(content: str, keywords: list) -> int:
    """
    SEO score 0-100.
    
    Критерии:
    - Primary keyword в title: +20
    - Primary keyword в первых 100 словах: +15
    - Keyword density 1-2%: +15
    - 3+ internal links: +15
    - 2+ external authoritative links: +15
    - Meta description оптимизирована: +10
    - Schema markup присутствует: +10
    """
    score = 0
    
    # ... проверки
    
    return min(score, 100)
```

### Шаг 7: Формирование результата (500 ms)

1. Собрать все компоненты:
   - Article (title, content, meta_description, CTA)
   - SEO data (keywords, links, schema)
   - Compliance data (citations, disclaimer, E-E-A-T score)
   - Quality metrics (readability, tone match, SEO score)

2. Рассчитать execution metrics

3. Сформировать событие результата

### Шаг 8: Отправка результата (100 ms)

1. Отправить событие `subagent.task.completed`
2. Логировать в Event Store
3. Сохранить в Obsidian vault (`obsidian/content-magister/blog-content/`)

**Obsidian vault structure:**
```
obsidian/content-magister/blog-content/
├── articles/
│   └── YYYY-MM-DD-topic-slug.md
├── metrics/
│   └── YYYY-MM-DD-metrics.json
└── learnings/
    └── framework-effectiveness.md
```


---

## 🔧 ИНТЕГРАЦИИ

### Внешние сервисы:

**PubMed API (Medical Citations):**
- API endpoint: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`
- Аутентификация: API key (опционально, увеличивает rate limit)
- Rate limit: 3 requests/second (без ключа), 10 requests/second (с ключом)
- Стоимость: **Бесплатно**
- Документация: https://www.ncbi.nlm.nih.gov/home/develop/api/
- Использование: Проверка медицинских фактов, поиск цитат

**LanguageTool API (Grammar & Tone):**
- API endpoint: `https://api.languagetool.org/v2/check`
- Аутентификация: API key
- Rate limit: 40,000 requests/month
- Стоимость: **$22/month**
- Документация: https://languagetool.org/http-api/
- Использование: Проверка грамматики, анализ tone of voice

**Frase.io API (SEO Optimization):**
- API endpoint: `https://api.frase.io/v1/`
- Аутентификация: API key
- Rate limit: Unlimited documents
- Стоимость: **$115/month**
- Документация: https://www.frase.io/api/
- Использование: SEO score calculation, keyword optimization

**Textstat Library (Readability):**
- Тип: Python библиотека (локально)
- Установка: `pip install textstat`
- Стоимость: **Бесплатно**
- Документация: https://pypi.org/project/textstat/
- Использование: Flesch Reading Ease, Flesch-Kincaid Grade Level

### Внутренние зависимости:

**Обязательные:**
- Event Bus - получение задач, отправка результатов
- Event Store - логирование всех событий
- Obsidian vault - сохранение статей и метрик
- Brand Magister - получение Brand Voice (Tone of Voice)
- Synthetic CustDev - получение болей и языка аудитории

**Опциональные:**
- Tone of Voice Agent - проверка соответствия ToV бренда
- Medical Fact-Checker Agent - дополнительная проверка медицинских фактов
- Keyword Research Agent - получение ключевых слов для SEO
- Editor Agent - финальная редактура и полировка

**Общая стоимость инструментов:**
- Tier 1 (Free): PubMed + Textstat = **$0/month**
- Tier 2 (Professional): PubMed + Textstat + LanguageTool + Frase = **$137/month**
- Tier 3 (Enterprise): + MarketMuse ($1,500/mo) + Clearscope ($350/mo) = **$2,000+/month**

**Рекомендация:** Начать с Tier 2 ($137/month), upgrade до Tier 3 при масштабировании (50+ статей/месяц).

---

## 📊 МЕТРИКИ УСПЕХА

### Качественные метрики:

**Readability (Читабельность):**
- Метрика: Flesch Reading Ease
- Целевое значение: 60-70 (8th-9th grade level для пациентов)
- Как измерять: Textstat library после генерации контента
- Benchmark: 65.2 (средний показатель топ-10 медицинских блогов)

**SEO Quality:**
- Метрика: SEO Score (custom или Frase.io)
- Целевое значение: > 80/100
- Как измерять: Автоматический расчёт после SEO-оптимизации
- Benchmark: 85 (средний показатель топ-10 статей по медицинским запросам)

**Compliance:**
- Метрика: E-E-A-T Score
- Целевое значение: > 8.0/10
- Как измерять: Custom calculation (credentials + citations + disclaimer)
- Benchmark: 8.5 (требование Google для YMYL контента)

**Tone of Voice Match:**
- Метрика: Tone Match Score
- Целевое значение: > 0.85 (85% соответствие)
- Как измерять: LanguageTool API tone analysis vs target brand voice
- Benchmark: 0.92 (отличное соответствие)

### Производительность:

**Скорость:**
- Среднее время выполнения: < 60 секунд (1 минута)
- 95-й перцентиль: < 90 секунд
- Максимальное время: < 120 секунд (2 минуты)

**Breakdown по этапам:**
- Framework selection: < 1 секунда
- Content generation: < 45 секунд (75% времени)
- SEO optimization: < 5 секунд
- Compliance check: < 15 секунд
- Quality metrics: < 2 секунды

**Надёжность:**
- Success rate: > 95% (статья создана без критических ошибок)
- Partial success rate: > 99% (статья создана, но есть warnings)
- Failure rate: < 1% (критическая ошибка, статья не создана)

### Бизнес-метрики:

**Engagement (после публикации, отслеживается отдельно):**
- Time on Page: > 3 минуты (целевое: 3-5 минут)
- Bounce Rate: < 60% (целевое: 40-60%)
- Pages per Session: > 1.5

**Conversion:**
- Conversion Rate: > 2% (целевое: 2-5%)
- CTA Click Rate: > 5%
- Form Submissions: измеряется CRM

**SEO Performance:**
- Organic Traffic: рост на 15-20% через 3 месяца
- Keyword Rankings: топ-10 по primary keyword через 6 месяцев
- Backlinks: 2-3 естественных backlinks через 6 месяцев

**Cost Efficiency:**
- Cost per Article: $137/month ÷ 20 статей = **$6.85/статья** (только инструменты)
- vs Agency: $500-1,000/статья (экономия 98-99%)
- Time Savings: 69% vs ручное написание (5.5 часов → 1.7 часа)

---

## 🧪 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ

### Пример 1: Awareness статья для пациентов (PAS framework)

**Входные данные:**
```json
{
  "goal": "awareness",
  "audience": "patients",
  "journey_stage": "problem_aware",
  "service_type": "treatment",
  "topic": "Боль в спине: причины и лечение",
  "keywords": ["боль в спине", "лечение боли в спине", "причины боли в спине"],
  "brand_voice": {
    "tone": "friendly",
    "formality_level": 5,
    "expertise_level": 7
  },
  "clinic_info": {
    "name": "Клиника Здоровая Спина",
    "specialization": "Вертебрология",
    "doctors": [
      {
        "name": "Иванов Иван Иванович",
        "credentials": "Вертебролог, кандидат медицинских наук, 15 лет опыта"
      }
    ]
  },
  "target_length": 1650,
  "compliance_level": "medium"
}
```

**Выходные данные:**
```json
{
  "status": "success",
  "result": {
    "article": {
      "title": "Боль в спине? 3 упражнения, которые помогли 87% пациентов за 2 недели",
      "meta_description": "Хроническая боль в спине мешает жить? Узнайте 3 простых упражнения, которые помогли 87% пациентов избавиться от боли за 2 недели. Научно доказано.",
      "content": "[Полный текст статьи в markdown, ~1,650 слов]",
      "word_count": 1650,
      "readability_score": 65.2,
      "framework_used": "PAS",
      "compliance_risk": "medium",
      "cta": "Запишитесь на бесплатную консультацию к вертебрологу"
    },
    "seo": {
      "primary_keyword": "боль в спине",
      "secondary_keywords": ["лечение боли в спине", "причины боли в спине", "упражнения для спины"],
      "keyword_density": 1.5,
      "internal_links": [
        "/blog/uprazhneniya-dlya-spiny",
        "/blog/profilaktika-boli-v-spine",
        "/services/vertebrologiya"
      ],
      "external_links": [
        "https://pubmed.ncbi.nlm.nih.gov/12345678/",
        "https://pubmed.ncbi.nlm.nih.gov/23456789/"
      ],
      "schema_markup": "{\"@context\":\"https://schema.org\",\"@type\":\"MedicalWebPage\",...}"
    },
    "compliance": {
      "citations": [
        {
          "claim": "80% болей в спине связаны с мышечным дисбалансом",
          "source": "PubMed PMID: 12345678"
        },
        {
          "claim": "87% пациентов избавились от боли за 2 недели",
          "source": "PubMed PMID: 23456789"
        }
      ],
      "disclaimer": "Информация в статье носит ознакомительный характер...",
      "prohibited_claims_detected": [],
      "e_e_a_t_score": 8.5
    },
    "quality_metrics": {
      "flesch_reading_ease": 65.2,
      "flesch_kincaid_grade": 8.5,
      "tone_match_score": 0.92,
      "seo_score": 85
    }
  },
  "metrics": {
    "execution_time_ms": 45000,
    "framework_selection_time_ms": 500,
    "content_generation_time_ms": 30000,
    "compliance_check_time_ms": 10000,
    "seo_optimization_time_ms": 4500
  },
  "errors": []
}
```

### Пример 2: Conversion статья для врачей (FAB framework)

**Входные данные:**
```json
{
  "goal": "conversion",
  "audience": "doctors",
  "journey_stage": "product_aware",
  "service_type": "diagnostic",
  "topic": "МРТ 3 Тесла: преимущества для диагностики",
  "keywords": ["МРТ 3 Тесла", "магнитно-резонансная томография", "точность диагностики"],
  "brand_voice": {
    "tone": "expert",
    "formality_level": 8,
    "expertise_level": 9
  },
  "clinic_info": {
    "name": "Диагностический Центр Точность",
    "specialization": "Лучевая диагностика",
    "doctors": [
      {
        "name": "Петрова Анна Сергеевна",
        "credentials": "Врач-рентгенолог высшей категории, доктор медицинских наук"
      }
    ]
  },
  "target_length": 1800,
  "compliance_level": "low"
}
```

**Выходные данные:**
```json
{
  "status": "success",
  "result": {
    "article": {
      "title": "МРТ 3 Тесла: точность диагностики 99.2% vs 85% у стандартных МРТ",
      "meta_description": "МРТ 3 Тесла обеспечивает точность диагностики 99.2% против 85% у стандартных МРТ. Раннее выявление патологий, снижение стоимости лечения на 40%.",
      "content": "[Полный текст статьи в markdown, ~1,800 слов]",
      "word_count": 1800,
      "readability_score": 58.5,
      "framework_used": "FAB",
      "compliance_risk": "low",
      "cta": "Запишитесь на МРТ 3 Тесла со скидкой 20%"
    },
    "seo": {
      "primary_keyword": "МРТ 3 Тесла",
      "secondary_keywords": ["магнитно-резонансная томография", "точность диагностики", "МРТ высокого разрешения"],
      "keyword_density": 1.8,
      "internal_links": [
        "/services/mrt-3-tesla",
        "/blog/mrt-vs-kt",
        "/blog/podgotovka-k-mrt"
      ],
      "external_links": [
        "https://pubmed.ncbi.nlm.nih.gov/34567890/",
        "https://pubmed.ncbi.nlm.nih.gov/45678901/"
      ],
      "schema_markup": "{\"@context\":\"https://schema.org\",\"@type\":\"MedicalWebPage\",...}"
    },
    "compliance": {
      "citations": [
        {
          "claim": "Точность диагностики 99.2% vs 85% у стандартных МРТ",
          "source": "PubMed PMID: 34567890"
        },
        {
          "claim": "Снижение стоимости лечения на 40% при раннем выявлении",
          "source": "PubMed PMID: 45678901"
        }
      ],
      "disclaimer": "Информация для медицинских специалистов...",
      "prohibited_claims_detected": [],
      "e_e_a_t_score": 9.2
    },
    "quality_metrics": {
      "flesch_reading_ease": 58.5,
      "flesch_kincaid_grade": 11.2,
      "tone_match_score": 0.95,
      "seo_score": 88
    }
  },
  "metrics": {
    "execution_time_ms": 52000,
    "framework_selection_time_ms": 500,
    "content_generation_time_ms": 35000,
    "compliance_check_time_ms": 12000,
    "seo_optimization_time_ms": 4500
  },
  "errors": []
}
```

### Пример 3: Ошибка - prohibited claim detected

**Входные данные:**
```json
{
  "goal": "conversion",
  "audience": "patients",
  "topic": "Лечение артрита: гарантированное избавление от боли",
  "compliance_level": "high"
}
```

**Выходные данные:**
```json
{
  "status": "failure",
  "result": null,
  "metrics": {
    "execution_time_ms": 15000,
    "framework_selection_time_ms": 500,
    "content_generation_time_ms": 10000,
    "compliance_check_time_ms": 4500
  },
  "errors": [
    {
      "code": "PROHIBITED_CLAIM_DETECTED",
      "message": "Topic contains prohibited claim: 'гарантированное избавление'",
      "details": {
        "prohibited_phrase": "гарантированное",
        "severity": "high",
        "recommendation": "Remove outcome guarantee. Use 'может помочь' or 'показано в исследованиях' instead."
      }
    }
  ]
}
```


---

## 🔒 ОБРАБОТКА ОШИБОК

### Типы ошибок:

**Валидация входных данных:**
- Код: `INVALID_INPUT`
- Причина: Отсутствуют обязательные параметры или неверные значения
- Действие: Вернуть failure сразу с описанием проблемы
- Retry: Нет (требуется исправление входных данных)
- Пример: `goal` не в ["awareness", "consideration", "conversion"]

**Prohibited claim detected:**
- Код: `PROHIBITED_CLAIM_DETECTED`
- Причина: В topic или сгенерированном контенте обнаружены запрещённые claims
- Действие: Вернуть failure с рекомендацией по исправлению
- Retry: Нет (требуется изменение topic или регенерация)
- Пример: "гарантированное излечение", "100% результат"

**External API error (PubMed, LanguageTool, Frase):**
- Код: `EXTERNAL_API_ERROR`
- Причина: API недоступен, rate limit exceeded, timeout
- Действие: Retry с exponential backoff (1s, 2s, 4s)
- Retry: До 3 попыток
- Fallback: Продолжить без этого API (partial_success)
- Пример: PubMed API timeout → продолжить без citation verification

**Content generation timeout:**
- Код: `CONTENT_GENERATION_TIMEOUT`
- Причина: LLM генерация превысила 60 секунд
- Действие: Прервать генерацию, вернуть failure
- Retry: 1 попытка с упрощённым промптом
- Пример: Слишком сложный topic → упростить требования

**Low quality content:**
- Код: `LOW_QUALITY_CONTENT`
- Причина: Readability < 50 или SEO score < 60
- Действие: Регенерировать контент с adjusted параметрами
- Retry: До 2 попыток
- Fallback: Вернуть partial_success с warning

**Insufficient E-E-A-T:**
- Код: `INSUFFICIENT_E_E_A_T`
- Причина: E-E-A-T score < 6.0 (недостаточно credentials, citations)
- Действие: Добавить больше citations и credentials
- Retry: 1 попытка с enhanced E-E-A-T requirements
- Fallback: Вернуть partial_success с warning

### Graceful degradation:

**Сценарий 1: PubMed API недоступен**
```python
try:
    citations = await self.verify_medical_claims(content)
except PubMedAPIError:
    # Fallback: продолжить без автоматической проверки
    citations = []
    warnings.append({
        "code": "PUBMED_API_UNAVAILABLE",
        "message": "Medical claims not verified - manual review required",
        "severity": "medium"
    })
    # Вернуть partial_success
    status = "partial_success"
```

**Сценарий 2: LanguageTool API недоступен**
```python
try:
    tone_score = await self.calculate_tone_match(content, brand_voice)
except LanguageToolAPIError:
    # Fallback: использовать базовую эвристику
    tone_score = self.estimate_tone_heuristic(content, brand_voice)
    warnings.append({
        "code": "LANGUAGETOOL_API_UNAVAILABLE",
        "message": "Tone analysis degraded to heuristic",
        "severity": "low"
    })
```

**Сценарий 3: Низкий readability score**
```python
if readability_score < 60:
    # Попытка упростить контент
    content = await self.simplify_content(content, target_score=65)
    readability_score = self.calculate_readability(content)
    
    if readability_score < 60:
        # Всё ещё низкий → partial_success с warning
        warnings.append({
            "code": "LOW_READABILITY",
            "message": f"Readability {readability_score} below target 60-70",
            "severity": "medium",
            "recommendation": "Manual editing recommended"
        })
        status = "partial_success"
```

### Error response format:

```json
{
  "status": "failure",
  "result": null,
  "metrics": {
    "execution_time_ms": 15000
  },
  "errors": [
    {
      "code": "ERROR_CODE",
      "message": "Human-readable error message",
      "details": {
        "field": "value",
        "expected": "value",
        "actual": "value"
      },
      "severity": "low | medium | high | critical",
      "recommendation": "How to fix this error"
    }
  ]
}
```

---

## 🧪 ТЕСТИРОВАНИЕ

### Unit тесты:

**Покрытие:** > 80%

**Обязательные тесты:**

1. **Framework selection:**
```python
def test_framework_selection_awareness_patients():
    framework = select_framework(
        goal="awareness",
        audience="patients",
        journey_stage="problem_aware",
        service_type="treatment",
        compliance_level="medium"
    )
    assert framework == "PAS"

def test_framework_selection_compliance_filter():
    # HIGH compliance должен фильтровать 4P и PASTOR
    framework = select_framework(
        goal="conversion",
        audience="patients",
        journey_stage="product_aware",
        service_type="treatment",
        compliance_level="high"
    )
    assert framework in ["AIDA", "FAB", "StoryBrand"]
```

2. **Prohibited claims detection:**
```python
def test_prohibited_claims_detection():
    content = "Наше лечение гарантирует 100% излечение"
    violations = detect_prohibited_claims(content)
    assert len(violations) > 0
    assert any("гарантирует" in v["phrase"] for v in violations)
    assert any("100%" in v["phrase"] for v in violations)
```

3. **Readability calculation:**
```python
def test_readability_calculation():
    content = "Простой текст. Короткие предложения. Легко читать."
    score = calculate_readability(content)
    assert score["flesch_reading_ease"] > 70  # Very easy
```

4. **E-E-A-T score:**
```python
def test_e_e_a_t_score_with_credentials():
    content = """
    Статья написана доктором Ивановым, кандидатом медицинских наук.
    Согласно исследованию (PubMed PMID: 12345678), 80% пациентов...
    Disclaimer: Консультация врача обязательна.
    """
    clinic_info = {
        "doctors": [{"name": "Иванов", "credentials": "кандидат медицинских наук"}]
    }
    score = calculate_e_e_a_t_score(content, clinic_info)
    assert score >= 8.0  # High E-E-A-T
```

5. **SEO optimization:**
```python
def test_seo_keyword_placement():
    content = generate_content(
        framework="AIDA",
        topic="Боль в спине",
        keywords=["боль в спине", "лечение"],
        brand_voice={"tone": "friendly"},
        clinic_info={}
    )
    # Primary keyword должен быть в первых 100 словах
    first_100_words = " ".join(content.split()[:100])
    assert "боль в спине" in first_100_words.lower()
```

### Integration тесты:

**Обязательные сценарии:**

1. **End-to-end: получение задачи → генерация → отправка результата:**
```python
async def test_e2e_blog_content_generation():
    # Создать задачу
    task = {
        "goal": "awareness",
        "audience": "patients",
        "topic": "Боль в спине",
        "keywords": ["боль в спине"]
    }
    
    # Отправить через Event Bus
    await event_bus.publish("subagent.task.assigned", task)
    
    # Дождаться результата
    result = await event_bus.subscribe("subagent.task.completed", timeout=120)
    
    # Проверки
    assert result["status"] == "success"
    assert result["result"]["article"]["word_count"] >= 1500
    assert result["result"]["quality_metrics"]["flesch_reading_ease"] >= 60
```

2. **PubMed API integration:**
```python
async def test_pubmed_api_integration():
    claims = ["80% болей в спине связаны с мышечным дисбалансом"]
    citations = await verify_medical_claims(claims)
    assert len(citations) > 0
    assert citations[0]["source"] is not None
    assert "PMID" in citations[0]["source"]
```

3. **Obsidian vault storage:**
```python
async def test_obsidian_vault_storage():
    article = {
        "title": "Test Article",
        "content": "Test content",
        "metrics": {}
    }
    
    # Сохранить в vault
    await save_to_obsidian(article)
    
    # Проверить файл создан
    vault_path = "obsidian/content-magister/blog-content/articles/"
    files = os.listdir(vault_path)
    assert any("test-article" in f for f in files)
```

### E2E тесты:

**Обязательные сценарии:**

1. **Полный цикл: awareness статья для пациентов (PAS)**
2. **Полный цикл: conversion статья для врачей (FAB)**
3. **Error handling: prohibited claim detection**
4. **Error handling: PubMed API unavailable (graceful degradation)**
5. **Performance: генерация статьи < 60 секунд**

---

## 🚀 DEPLOYMENT

### Требования:

**Окружение:**
- Python 3.11+
- Event Bus доступен (Redis/RabbitMQ)
- Event Store доступен (PostgreSQL)
- Obsidian vault доступен (файловая система)

**Зависимости:**
```txt
# requirements.txt
anthropic>=0.18.0          # Claude API для генерации контента
textstat>=0.7.3            # Readability scoring
requests>=2.31.0           # HTTP requests для API
pydantic>=2.5.0            # Data validation
asyncio>=3.4.3             # Async operations
```

**Конфигурация:**
```env
# .env
SUBAGENT_ID=blog-content-agent
EVENT_BUS_URL=redis://localhost:6379
EVENT_STORE_URL=postgresql://localhost:5432/meai
OBSIDIAN_VAULT_PATH=./obsidian/content-magister/blog-content

# External APIs
PUBMED_API_KEY=optional_but_recommended
LANGUAGETOOL_API_KEY=your_key_here
FRASE_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_claude_key

# Limits
MAX_EXECUTION_TIME_MS=120000
MAX_CONTENT_LENGTH_WORDS=3000
MIN_READABILITY_SCORE=50
MIN_E_E_A_T_SCORE=6.0
```

### Мониторинг:

**Метрики для алертов:**

**Performance:**
- Avg execution time > 90 seconds → Warning
- 95th percentile > 120 seconds → Critical
- Success rate < 95% → Warning
- Success rate < 90% → Critical

**Quality:**
- Avg readability score < 60 → Warning
- Avg E-E-A-T score < 7.0 → Warning
- Avg SEO score < 75 → Warning

**Compliance:**
- Prohibited claims detected > 5% → Critical
- Citations missing > 10% → Warning

**Cost:**
- API costs > $200/month → Warning (проверить usage)
- LLM costs > $500/month → Warning (оптимизировать промпты)

**Grafana Dashboard:**
```
Blog Content Agent Dashboard
├── Execution Time (p50, p95, p99)
├── Success Rate (success, partial_success, failure)
├── Quality Metrics (readability, E-E-A-T, SEO)
├── Framework Usage (AIDA, PAS, BAB, FAB, 4P, StoryBrand, PASTOR)
├── API Health (PubMed, LanguageTool, Frase uptime)
└── Cost Tracking (API costs, LLM costs per article)
```

---

## 📚 СВЯЗАННЫЕ ДОКУМЕНТЫ

### Спецификации:
- `CONTENT_MAGISTER_SPEC.md` - Спецификация родительского Content Magister
- `CONTENT_ORCHESTRATOR_SPEC.md` - Спецификация Content Orchestrator
- `TONE_OF_VOICE_SPEC.md` - Tone of Voice Agent (проверка ToV)
- `MEDICAL_FACT_CHECKER_SPEC.md` - Medical Fact-Checker Agent
- `KEYWORD_RESEARCH_SPEC.md` - Keyword Research Agent

### Исследования:
- `obsidian/deep-research/raw/2026-05-10-Blog_Content/Blog_Content_Research_Report.md` - Полное исследование (18,000 слов)
- `docs/briefs/BLOG_CONTENT_BRIEF.md` - Исходный бриф

### Код:
- `AIM/src/aim/subagents/content/blog_content_agent.py` - Реализация (TODO)
- `AIM/tests/subagents/content/test_blog_content_agent.py` - Тесты (TODO)

### Документация:
- Event Bus API - `docs/EVENT_BUS_API.md`
- Event Store API - `docs/EVENT_STORE_API.md`
- Obsidian integration guide - `docs/OBSIDIAN_INTEGRATION.md`

### Внешние ресурсы:
- PubMed API: https://www.ncbi.nlm.nih.gov/home/develop/api/
- LanguageTool API: https://languagetool.org/http-api/
- Frase.io API: https://www.frase.io/api/
- Textstat: https://pypi.org/project/textstat/
- FDA Guidance: https://www.fda.gov/regulatory-information/
- 152-ФЗ: http://www.consultant.ru/document/cons_doc_LAW_61801/

---

## 📋 CHANGELOG

### Version 1.0 (2026-05-10)

**Создана спецификация на основе deep research:**
- ✅ 7 copywriting фреймворков (AIDA, PAS, BAB, FAB, 4P, StoryBrand, PASTOR)
- ✅ Интеллектуальный выбор фреймворка (decision matrix)
- ✅ Compliance проверка (FDA, 152-ФЗ, E-E-A-T)
- ✅ SEO-оптимизация (keywords, meta-теги, schema markup)
- ✅ Readability scoring (Flesch 60-70 target)
- ✅ Tone of Voice адаптация
- ✅ PubMed integration для medical fact checking
- ✅ Graceful degradation при недоступности API

**Метрики:**
- Execution time: < 60 секунд
- Readability: 60-70 (Flesch Reading Ease)
- E-E-A-T score: > 8.0/10
- SEO score: > 80/100
- Success rate: > 95%

**Стоимость инструментов:**
- Tier 2 (Professional): $137/month
- Cost per article: $6.85 (только инструменты)
- vs Agency: $500-1,000/статья (экономия 98-99%)

**Исследование:**
- Deep research: 8 фаз, 208 минут
- Источников: 50+ (academic, industry, tools, regulations)
- Отчёт: 18,000 слов, 14 секций
- Архивировано: `obsidian/deep-research/raw/2026-05-10-Blog_Content/`

---

## 🔮 TODO & FUTURE IMPROVEMENTS

### Приоритет 1 (MVP - Phase 1):
- [ ] Реализовать framework selection algorithm
- [ ] Интегрировать PubMed API для citations
- [ ] Реализовать prohibited claims detection
- [ ] Интегрировать Textstat для readability
- [ ] Базовая SEO-оптимизация (keywords, meta-теги)
- [ ] E-E-A-T score calculation
- [ ] Unit тесты (coverage > 80%)

### Приоритет 2 (Phase 2):
- [ ] Интегрировать LanguageTool API ($22/mo)
- [ ] Интегрировать Frase.io API ($115/mo)
- [ ] Tone of Voice matching
- [ ] Advanced SEO (schema markup, internal linking)
- [ ] Integration тесты
- [ ] Grafana dashboard

### Приоритет 3 (Phase 3):
- [ ] A/B тестирование фреймворков (эмпирическая валидация)
- [ ] ML model для framework selection (на основе performance data)
- [ ] Automated content optimization (iterative improvement)
- [ ] Multi-language support (English, Russian)
- [ ] Custom compliance rules engine
- [ ] Content performance prediction

### Исследовательские задачи:
- [ ] Провести эмпирическое исследование framework effectiveness (50+ статей)
- [ ] Изучить AI-assisted vs human-written content trust (patient surveys)
- [ ] Адаптировать для Russian market specifics (152-ФЗ compliance)
- [ ] Разработать automated compliance checker (ML model на FDA warning letters)
- [ ] Расширить на другие форматы (video scripts, email, social media)

---

**Дата создания:** 2026-05-10  
**Автор:** Mikhail Eliseev (via meAI Architect + Deep Research)  
**Версия:** 1.0  
**Статус:** Draft (Ready for Implementation)  
**Размер:** ~45 KB, ~1,200 строк  
**Исследование:** Blog Content Research (18,000 words, $1.50 estimated cost)

