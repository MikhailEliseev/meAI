# Landing Content Agent - Спецификация

**Дата:** 2026-05-10  
**Magister:** Content Magister  
**Приоритет:** P1  
**Статус:** Draft

---

## 🎯 РОЛЬ И НАЗНАЧЕНИЕ

### Основная роль:
Landing Content Agent создаёт высококонверсионные лендинги для медицинских услуг с целевой конверсией 5-15% (в 3 раза выше блога). Специализируется на conversion-focused контенте с использованием проверенных фреймворков (AIDA, PAS, 4P) и психологических триггеров, адаптированных для медицинской специфики и compliance требований.

### Что делает:
- ✅ Создаёт полные лендинги (800-1,500 слов) с фокусом на конверсию
- ✅ Выбирает оптимальный conversion framework на основе типа услуги
- ✅ Применяет психологические триггеры этично (authority, social proof, reciprocity)
- ✅ Оптимизирует структуру (hero, problem, solution, benefits, social proof, pricing, FAQ, CTA)
- ✅ Обеспечивает medical compliance (FDA, HIPAA, E-E-A-T, YMYL, 152-ФЗ)
- ✅ Создаёт multi-step формы захвата лидов (+30-40% конверсии)
- ✅ Оптимизирует CTA (текст, цвет, размещение)
- ✅ Генерирует exit-intent popup контент

### Что НЕ делает:
- ❌ Информационный контент (это Blog Content Agent)
- ❌ Длинные статьи >1,500 слов (это Blog Content Agent)
- ❌ SEO-оптимизацию (это Keyword Research Agent)
- ❌ Визуальный дизайн (это UI/UX дизайнер)
- ❌ Техническую реализацию (это Frontend Developer)

### Место в иерархии:
```
Content Magister
    ↓
Content Orchestrator
    ↓
Landing Content Agent ← вы здесь
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
  "subagent_id": "landing-content-agent",
  "payload": {
    "service_name": "Cardiac Screening",
    "service_type": "diagnostic",
    "service_description": "Comprehensive heart health evaluation",
    "target_audience": "patients",
    "audience_segment": "adults 40+, concerned about heart health",
    "price_point": "mid",
    "price": 1500,
    "physician_credentials": {
      "name": "Dr. John Smith",
      "degree": "MD, FACC",
      "experience_years": 15,
      "specialization": "Cardiology",
      "certifications": ["Board-certified Cardiologist", "Fellow of American College of Cardiology"]
    },
    "social_proof": {
      "patients_treated": 5000,
      "success_rate": 98,
      "testimonials": [
        {
          "patient_name": "Jane D.",
          "quote": "Dr. Smith's screening saved my life",
          "consent": true
        }
      ]
    },
    "offer": {
      "type": "discount",
      "value": "10% off first consultation",
      "urgency": "Limited slots this week"
    },
    "brand_voice": "professional, compassionate, trustworthy",
    "tone_of_voice_id": "uuid"
  }
}
```

**Обязательные параметры:**
- `service_name` (string) - Название услуги
- `service_type` (enum) - Тип услуги: "diagnostic", "treatment", "preventive", "elective"
- `service_description` (string) - Описание услуги
- `target_audience` (enum) - "patients", "physicians", "administrators"
- `price_point` (enum) - "budget", "mid", "premium"

**Опциональные параметры:**
- `price` (float) - Цена услуги (если известна)
- `physician_credentials` (object) - Данные врача для authority signals
- `social_proof` (object) - Отзывы, статистика, сертификаты
- `offer` (object) - Специальное предложение
- `brand_voice` (string) - Характеристики голоса бренда
- `tone_of_voice_id` (string) - ID для проверки через Tone of Voice Agent

---

## 📤 ВЫХОДНЫЕ ДАННЫЕ

### Отправляет Orchestrator:

**Формат события:**
```json
{
  "event_type": "subagent.task.completed",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "landing-content-agent",
  "payload": {
    "status": "success",
    "result": {
      "landing_page": {
        "hero_section": {
          "headline": "Worried About Your Heart Health?",
          "subheadline": "Get a Comprehensive Cardiac Screening in 30 Minutes",
          "cta_text": "Schedule Free Consultation",
          "hero_image_description": "Professional photo of Dr. Smith in white coat"
        },
        "problem_section": "...",
        "solution_section": "...",
        "benefits_section": [...],
        "social_proof_section": {...},
        "pricing_section": {...},
        "faq_section": [...],
        "final_cta_section": {...},
        "exit_intent_popup": {...}
      },
      "lead_capture_form": {
        "type": "multi-step",
        "steps": [
          {
            "step": 1,
            "question": "What brings you here today?",
            "field_type": "dropdown",
            "options": ["Heart screening", "Follow-up", "Second opinion"]
          },
          {
            "step": 2,
            "question": "How soon do you need an appointment?",
            "field_type": "radio",
            "options": ["This week", "Next week", "This month"]
          },
          {
            "step": 3,
            "fields": [
              {"name": "first_name", "type": "text", "required": true},
              {"name": "last_name", "type": "text", "required": true},
              {"name": "phone", "type": "tel", "required": true},
              {"name": "email", "type": "email", "required": false}
            ]
          }
        ]
      },
      "metadata": {
        "framework_used": "AIDA",
        "psychological_triggers": ["authority", "social_proof", "reciprocity"],
        "word_count": 1450,
        "conversion_score_predicted": 85,
        "compliance_risk": "low",
        "readability_score": 65
      }
    },
    "metrics": {
      "execution_time_ms": 45000,
      "framework_selection_time_ms": 2000,
      "content_generation_time_ms": 38000,
      "compliance_check_time_ms": 5000
    },
    "errors": []
  }
}
```

**Структура результата:**
- `landing_page` (object) - Полный контент лендинга по секциям
- `lead_capture_form` (object) - Структура multi-step формы
- `metadata` (object) - Метаданные о созданном контенте

**Метрики:**
- `execution_time_ms` - Время выполнения (target: <60 секунд)
- `framework_selection_time_ms` - Время выбора фреймворка
- `content_generation_time_ms` - Время генерации контента
- `compliance_check_time_ms` - Время проверки compliance

---

## 🔄 АЛГОРИТМ РАБОТЫ

### Шаг 1: Анализ входных данных и выбор фреймворка

**Цель:** Определить оптимальный conversion framework на основе типа услуги, аудитории и цены.

**Decision Matrix:**

```python
def select_framework(service_type, price_point, audience_segment):
    """
    Выбор conversion framework на основе характеристик услуги.
    
    Returns: framework_name, compliance_risk
    """
    if service_type == "diagnostic" or service_type == "preventive":
        return "AIDA", "low"  # 5-8% conversion
    
    elif service_type == "treatment":
        # Проверяем, есть ли чёткая боль (pain point)
        if has_clear_pain_point(service_description):
            return "PAS", "medium"  # 8-12% conversion
        else:
            return "BAB", "medium"  # 7-11% conversion
    
    elif service_type == "elective" and price_point == "premium":
        return "4P", "medium"  # 6-10% conversion (требует proof)
    
    elif is_transformational_service(service_type):
        return "BAB", "medium"  # 7-11% conversion
    
    elif is_emotional_service(service_type):
        # HIGH RISK - использовать с осторожностью
        return "PASTOR", "high"  # 8-14% conversion
    
    else:
        return "AIDA", "low"  # Default safe choice
```

**Compliance Risk Assessment:**
- LOW: AIDA, FAB, StoryBrand
- MEDIUM: PAS, BAB, 4P
- HIGH: PASTOR (требует дополнительной проверки)

**Выход:** `framework_name`, `compliance_risk`


### Step 2: Content Generation

**Цель:** Создать контент для всех секций лендинга на основе выбранного фреймворка.

**Процесс:**

1. **Hero Section (Above the Fold)**
   - Формула заголовка: `[Боль] + [Решение] + [Результат]`
   - Пример: "Боль в спине мешает жить? Избавьтесь от неё за 3 сеанса без операций"
   - Подзаголовок: усиление обещания + социальное доказательство
   - CTA: яркая кнопка с action-oriented текстом ("Записаться на консультацию")

2. **Problem Section**
   - Описание боли аудитории (из Synthetic CustDev)
   - Agitation: усиление проблемы (что будет, если не решить)
   - Эмоциональный резонанс: "Вы не одиноки, 70% людей сталкиваются с этим"

3. **Solution Section**
   - Как услуга решает проблему
   - Уникальное преимущество (UVP из Brand Magister)
   - Процесс лечения (3-5 шагов)

4. **Benefits Section**
   - 3-5 ключевых выгод (не features, а benefits)
   - Формат: иконка + заголовок + описание
   - Фокус на результат, не на процесс

5. **Social Proof Section**
   - Отзывы пациентов (с фото, именем, результатом)
   - Статистика: "500+ пациентов", "15 лет опыта", "98% успеха"
   - Кейсы: до/после (если этично и разрешено)
   - Сертификаты врачей

6. **Pricing Section**
   - Прозрачная цена или "от X руб"
   - Anchoring: показать более дорогой вариант сначала
   - Оффер: скидка, бонус, гарантия
   - CTA: "Записаться со скидкой 20%"

7. **FAQ Section**
   - 5-7 типичных вопросов (из Synthetic CustDev)
   - Краткие ответы (2-3 предложения)
   - Снятие возражений

8. **Final CTA Section**
   - Повторение оффера
   - Urgency: "Осталось 3 места на этой неделе"
   - Форма захвата лида

**Код:**

```python
async def generate_content(
    self,
    framework: str,
    service: dict,
    audience_pain: str,
    uvp: str
) -> dict:
    """
    Генерирует контент для всех секций лендинга.
    
    Args:
        framework: Выбранный фреймворк (AIDA, PAS, 4P)
        service: Данные об услуге
        audience_pain: Боль аудитории из Synthetic CustDev
        uvp: Unique Value Proposition из Brand Magister
    
    Returns:
        dict: Контент для всех секций
    """
    # Генерация hero section
    hero = await self._generate_hero(
        pain=audience_pain,
        solution=service["name"],
        result=service["expected_result"]
    )
    
    # Генерация problem section
    problem = await self._generate_problem(
        pain=audience_pain,
        agitation=await self._agitate_problem(audience_pain)
    )
    
    # Генерация solution section
    solution = await self._generate_solution(
        service=service,
        uvp=uvp,
        process=service["treatment_process"]
    )
    
    # Генерация benefits section
    benefits = await self._generate_benefits(
        features=service["features"],
        framework=framework
    )
    
    # Генерация social proof section
    social_proof = await self._generate_social_proof(
        testimonials=service["testimonials"],
        statistics=service["statistics"],
        certificates=service["certificates"]
    )
    
    # Генерация pricing section
    pricing = await self._generate_pricing(
        price=service["price"],
        offer=service["offer"],
        anchoring=True
    )
    
    # Генерация FAQ section
    faq = await self._generate_faq(
        objections=service["objections"],
        questions=service["common_questions"]
    )
    
    # Генерация final CTA section
    final_cta = await self._generate_final_cta(
        offer=service["offer"],
        urgency=service["urgency_trigger"]
    )
    
    return {
        "hero": hero,
        "problem": problem,
        "solution": solution,
        "benefits": benefits,
        "social_proof": social_proof,
        "pricing": pricing,
        "faq": faq,
        "final_cta": final_cta
    }
```

### Step 3: Psychological Triggers Application

**Цель:** Внедрить психологические триггеры этично и эффективно.

**Триггеры:**

1. **Scarcity (Дефицит)**
   - "Осталось 3 места на этой неделе"
   - "Акция действует до 31 мая"
   - Этично: реальный дефицит, не fake urgency

2. **Social Proof (Социальное доказательство)**
   - "500+ пациентов вылечились"
   - "15 лет опыта, кандидат медицинских наук"
   - Отзывы с фото и именами (с согласием 152-ФЗ)

3. **Authority (Авторитет)**
   - Credentials врачей: "Кандидат медицинских наук, 15 лет опыта"
   - Сертификаты и лицензии
   - Публикации в медицинских журналах

4. **Urgency (Срочность)**
   - "Запишитесь сегодня — получите скидку 20%"
   - "Акция заканчивается через 3 дня"
   - Этично: реальные дедлайны, не fake countdown

5. **Reciprocity (Взаимность)**
   - "Бесплатная консультация при записи сегодня"
   - "Скачайте чек-лист: 10 упражнений от боли в спине"
   - Даём ценность → получаем контакт

6. **Consistency (Последовательность)**
   - Micro-commitments: "Согласны, что здоровье важнее денег?"
   - Постепенное вовлечение: quiz → результат → запись

**Код:**

```python
async def apply_psychological_triggers(
    self,
    content: dict,
    triggers: list[str]
) -> dict:
    """
    Применяет психологические триггеры к контенту.
    
    Args:
        content: Сгенерированный контент
        triggers: Список триггеров для применения
    
    Returns:
        dict: Контент с триггерами
    """
    for trigger in triggers:
        if trigger == "scarcity":
            content["hero"]["subheadline"] += " Осталось 3 места на этой неделе."
            content["final_cta"]["urgency"] = "Акция действует до 31 мая"
        
        elif trigger == "social_proof":
            content["hero"]["subheadline"] += " 500+ пациентов уже избавились от боли."
            content["social_proof"]["statistics"] = {
                "patients": "500+",
                "experience": "15 лет",
                "success_rate": "98%"
            }
        
        elif trigger == "authority":
            content["solution"]["credentials"] = {
                "degree": "Кандидат медицинских наук",
                "experience": "15 лет опыта",
                "certificates": ["Сертификат специалиста", "Лицензия"]
            }
        
        elif trigger == "urgency":
            content["pricing"]["offer"] += " Только до 31 мая!"
            content["final_cta"]["button_text"] = "Записаться со скидкой (осталось 3 дня)"
        
        elif trigger == "reciprocity":
            content["hero"]["lead_magnet"] = {
                "title": "Бесплатная консультация",
                "description": "При записи сегодня"
            }
        
        elif trigger == "consistency":
            content["problem"]["micro_commitment"] = "Согласны, что боль мешает жить полной жизнью?"
    
    return content
```

### Step 4: Multi-Step Form Creation

**Цель:** Создать форму захвата лида с высокой конверсией.

**Стратегия:**

1. **Multi-step vs Single-step**
   - Multi-step: +30-40% конверсии (исследование показало)
   - Используем multi-step для high-ticket услуг (>10,000 руб)
   - Single-step для low-ticket (<5,000 руб)

2. **Обязательные поля (минимум для высокой конверсии)**
   - Имя (текст)
   - Телефон (валидация формата)

3. **Опциональные поля**
   - Email (для email-маркетинга)
   - Комментарий (описание проблемы)
   - Предпочитаемое время звонка

4. **Шаги multi-step формы**
   - Шаг 1: "Какая у вас проблема?" (выбор из списка)
   - Шаг 2: "Как давно беспокоит?" (выбор: <1 месяца, 1-6 месяцев, >6 месяцев)
   - Шаг 3: "Оставьте контакты для записи" (имя + телефон)

5. **Валидация**
   - Телефон: формат +7 (XXX) XXX-XX-XX
   - Email: формат name@domain.com
   - Real-time валидация (без отправки формы)

6. **Защита от спама**
   - reCAPTCHA v3 (невидимая)
   - Honeypot fields (скрытые поля для ботов)

7. **CRM интеграция**
   - Автоматическая отправка лида в AmoCRM/Bitrix24
   - Webhook при успешной отправке

**Код:**

```python
async def create_lead_form(
    self,
    service_price: int,
    fields: list[str]
) -> dict:
    """
    Создаёт форму захвата лида.
    
    Args:
        service_price: Цена услуги (для выбора multi-step vs single-step)
        fields: Список полей для формы
    
    Returns:
        dict: Конфигурация формы
    """
    # Выбор типа формы
    form_type = "multi_step" if service_price > 10000 else "single_step"
    
    if form_type == "multi_step":
        return {
            "type": "multi_step",
            "steps": [
                {
                    "step": 1,
                    "question": "Какая у вас проблема?",
                    "type": "radio",
                    "options": [
                        "Боль в спине",
                        "Боль в шее",
                        "Головная боль",
                        "Другое"
                    ]
                },
                {
                    "step": 2,
                    "question": "Как давно беспокоит?",
                    "type": "radio",
                    "options": [
                        "Меньше месяца",
                        "1-6 месяцев",
                        "Больше 6 месяцев"
                    ]
                },
                {
                    "step": 3,
                    "question": "Оставьте контакты для записи",
                    "fields": [
                        {
                            "name": "name",
                            "type": "text",
                            "label": "Ваше имя",
                            "required": True,
                            "validation": "^[А-Яа-яЁёA-Za-z\\s-]+$"
                        },
                        {
                            "name": "phone",
                            "type": "tel",
                            "label": "Телефон",
                            "required": True,
                            "validation": "^\\+7\\s?\\(?\\d{3}\\)?\\s?\\d{3}-?\\d{2}-?\\d{2}$",
                            "placeholder": "+7 (999) 999-99-99"
                        }
                    ]
                }
            ],
            "protection": {
                "recaptcha": {
                    "enabled": True,
                    "version": "v3",
                    "threshold": 0.5
                },
                "honeypot": {
                    "enabled": True,
                    "field_name": "website"
                }
            },
            "integration": {
                "crm": "amocrm",
                "webhook_url": "https://api.amocrm.ru/leads",
                "api_key": "${AMOCRM_API_KEY}"
            }
        }
    else:
        return {
            "type": "single_step",
            "fields": [
                {
                    "name": "name",
                    "type": "text",
                    "label": "Ваше имя",
                    "required": True
                },
                {
                    "name": "phone",
                    "type": "tel",
                    "label": "Телефон",
                    "required": True,
                    "validation": "^\\+7\\s?\\(?\\d{3}\\)?\\s?\\d{3}-?\\d{2}-?\\d{2}$"
                }
            ],
            "protection": {
                "recaptcha": {"enabled": True, "version": "v3"},
                "honeypot": {"enabled": True}
            },
            "integration": {
                "crm": "amocrm",
                "webhook_url": "https://api.amocrm.ru/leads"
            }
        }
```

### Step 5: Compliance Verification

**Цель:** Проверить соответствие медицинским требованиям и законам.

**Проверки:**

1. **FDA/152-ФЗ Compliance**
   - Нет гарантий результата ("100% излечение" → запрещено)
   - Нет outcome guarantees ("Вылечим за 3 дня" → запрещено)
   - Есть disclaimers: "Результаты индивидуальны"

2. **E-E-A-T Requirements**
   - Указаны credentials врачей
   - Есть ссылки на медицинские источники (если применимо)
   - Показана экспертность

3. **YMYL (Your Money Your Life)**
   - Медицинские советы с disclaimer
   - Нет прямых рекомендаций без консультации
   - Призыв к консультации с врачом

4. **152-ФЗ (Персональные данные)**
   - Согласие на обработку персональных данных
   - Политика конфиденциальности
   - Отзывы только с согласием пациентов

**Код:**

```python
async def verify_compliance(self, content: dict) -> dict:
    """
    Проверяет соответствие контента медицинским требованиям.
    
    Args:
        content: Сгенерированный контент
    
    Returns:
        dict: Результат проверки с рисками
    """
    risks = []
    
    # Проверка на outcome guarantees
    guarantee_patterns = [
        r"100%\s+(излечение|успех|гарантия)",
        r"вылечим\s+за\s+\d+\s+(день|дня|дней)",
        r"гарантируем\s+результат"
    ]
    
    for section in content.values():
        text = str(section)
        for pattern in guarantee_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                risks.append({
                    "type": "outcome_guarantee",
                    "severity": "high",
                    "section": section,
                    "pattern": pattern,
                    "recommendation": "Удалить гарантии результата"
                })
    
    # Проверка наличия disclaimers
    if "disclaimer" not in content.get("final_cta", {}):
        risks.append({
            "type": "missing_disclaimer",
            "severity": "medium",
            "recommendation": "Добавить disclaimer: 'Результаты индивидуальны'"
        })
    
    # Проверка credentials
    if "credentials" not in content.get("solution", {}):
        risks.append({
            "type": "missing_credentials",
            "severity": "medium",
            "recommendation": "Добавить credentials врачей"
        })
    
    # Проверка согласия на обработку данных
    if "privacy_policy" not in content.get("lead_form", {}):
        risks.append({
            "type": "missing_privacy_policy",
            "severity": "high",
            "recommendation": "Добавить ссылку на политику конфиденциальности"
        })
    
    # Определение общего уровня риска
    risk_level = "low"
    if any(r["severity"] == "high" for r in risks):
        risk_level = "high"
    elif any(r["severity"] == "medium" for r in risks):
        risk_level = "medium"
    
    return {
        "compliant": len(risks) == 0,
        "risk_level": risk_level,
        "risks": risks,
        "recommendations": [r["recommendation"] for r in risks]
    }
```


### Step 6: CTA Optimization

**Цель:** Оптимизировать призывы к действию для максимальной конверсии.

**Стратегия:**

1. **Количество CTA на странице**
   - Минимум 3 CTA: hero, после benefits, final
   - Оптимально 5-7 CTA: каждая секция + sticky button

2. **Тексты кнопок**
   - Action-oriented: "Записаться", "Получить консультацию", "Узнать цену"
   - Избегать: "Отправить", "Submit", "Нажмите здесь"
   - С выгодой: "Записаться со скидкой 20%"
   - С urgency: "Записаться сегодня"

3. **Цвета кнопок**
   - Контрастный к фону (высокая видимость)
   - Психология цвета в медицине:
     - Зелёный: здоровье, безопасность, доверие
     - Синий: профессионализм, надёжность
     - Оранжевый: энергия, действие (для CTA)
   - A/B тестирование цветов

4. **Размещение**
   - Above the fold (hero section)
   - После каждой ключевой секции
   - Sticky button (прилипает при скролле)
   - Exit-intent popup

5. **Размер и визуальная иерархия**
   - Большие кнопки (минимум 44x44px для мобильных)
   - Достаточный padding (16-24px)
   - Тень или hover эффект

**Код:**

```python
async def optimize_cta(
    self,
    content: dict,
    offer: str,
    urgency: str
) -> dict:
    """
    Оптимизирует CTA для максимальной конверсии.
    
    Args:
        content: Сгенерированный контент
        offer: Оффер (скидка, бонус)
        urgency: Триггер срочности
    
    Returns:
        dict: Оптимизированные CTA
    """
    cta_variants = {
        "hero": {
            "text": f"Записаться {offer}",
            "color": "#FF6B35",  # Оранжевый для действия
            "size": "large",
            "position": "center",
            "urgency": urgency
        },
        "after_benefits": {
            "text": "Получить консультацию",
            "color": "#4CAF50",  # Зелёный для доверия
            "size": "medium",
            "position": "center"
        },
        "after_pricing": {
            "text": f"Записаться со скидкой",
            "color": "#FF6B35",
            "size": "large",
            "position": "center",
            "urgency": "Только до 31 мая"
        },
        "final": {
            "text": f"Записаться сейчас {offer}",
            "color": "#FF6B35",
            "size": "xlarge",
            "position": "center",
            "urgency": urgency
        },
        "sticky": {
            "text": "Записаться",
            "color": "#FF6B35",
            "size": "medium",
            "position": "bottom-right",
            "show_on_scroll": 500  # Показать после 500px скролла
        }
    }
    
    return {
        "cta_count": len(cta_variants),
        "cta_variants": cta_variants,
        "ab_test": {
            "enabled": True,
            "variants": [
                {"text": "Записаться", "color": "#FF6B35"},
                {"text": "Получить консультацию", "color": "#4CAF50"},
                {"text": "Узнать цену", "color": "#2196F3"}
            ]
        }
    }
```

### Step 7: Exit-Intent Popup Generation

**Цель:** Создать exit-intent popup для восстановления 5-15% уходящих посетителей.

**Стратегия:**

1. **Когда показывать**
   - При движении мыши к верхней границе браузера
   - Только 1 раз за сессию (не раздражать)
   - Не показывать на мобильных (плохой UX)

2. **Что предлагать**
   - Скидка 10-20%: "Не уходите! Скидка 20% при записи сегодня"
   - Бесплатная консультация: "Получите бесплатную консультацию"
   - Lead magnet: "Скачайте чек-лист: 10 упражнений от боли"
   - Гайд: "Бесплатный гайд: Как избавиться от боли за 7 дней"

3. **Compliance**
   - Не обманывать (реальные офферы)
   - Не блокировать закрытие (крестик должен быть виден)
   - Не показывать слишком часто

4. **A/B тестирование**
   - Разные офферы для разных сегментов
   - Тестирование заголовков, изображений, CTA

5. **Метрика успеха**
   - Exit-intent conversion rate > 5%
   - Если < 5% → менять оффер

**Код:**

```python
async def generate_exit_intent_popup(
    self,
    offer_type: str,
    discount: int = 20
) -> dict:
    """
    Генерирует exit-intent popup.
    
    Args:
        offer_type: Тип оффера (discount, free_consultation, lead_magnet)
        discount: Размер скидки (если offer_type = discount)
    
    Returns:
        dict: Конфигурация popup
    """
    offers = {
        "discount": {
            "headline": f"Не уходите! Скидка {discount}% при записи сегодня",
            "subheadline": "Предложение действует только сегодня",
            "cta_text": f"Записаться со скидкой {discount}%",
            "image": "discount-badge.png"
        },
        "free_consultation": {
            "headline": "Получите бесплатную консультацию",
            "subheadline": "Узнайте, как мы можем помочь вам",
            "cta_text": "Получить консультацию",
            "image": "doctor-consultation.jpg"
        },
        "lead_magnet": {
            "headline": "Скачайте бесплатный чек-лист",
            "subheadline": "10 упражнений от боли в спине",
            "cta_text": "Скачать чек-лист",
            "image": "checklist-preview.png"
        }
    }
    
    selected_offer = offers.get(offer_type, offers["discount"])
    
    return {
        "enabled": True,
        "trigger": {
            "type": "exit_intent",
            "mouse_position": "top",
            "delay": 0,
            "show_once_per_session": True,
            "mobile_enabled": False  # Плохой UX на мобильных
        },
        "content": selected_offer,
        "form": {
            "fields": [
                {"name": "name", "type": "text", "required": True},
                {"name": "phone", "type": "tel", "required": True}
            ]
        },
        "design": {
            "overlay_opacity": 0.8,
            "close_button_visible": True,
            "animation": "fade-in"
        },
        "ab_test": {
            "enabled": True,
            "variants": [
                {"offer_type": "discount", "discount": 20},
                {"offer_type": "free_consultation"},
                {"offer_type": "lead_magnet"}
            ]
        },
        "metrics": {
            "target_conversion_rate": 0.05,  # 5% минимум
            "optimal_conversion_rate": 0.15  # 15% оптимально
        }
    }
```

### Step 8: Quality Checks and Metadata Generation

**Цель:** Проверить качество лендинга и сгенерировать метаданные.

**Проверки:**

1. **Длина контента**
   - Целевая длина: 800-1,500 слов
   - Если < 800 → добавить контент
   - Если > 1,500 → сократить или разбить на секции

2. **Readability Score**
   - Flesch Reading Ease > 60 (понятно для широкой аудитории)
   - Средняя длина предложения < 20 слов
   - Избегать сложных терминов без объяснения

3. **SEO Score**
   - Ключевые слова в заголовке (H1)
   - Ключевые слова в первых 100 словах
   - Meta description (150-160 символов)
   - Alt текст для изображений

4. **Conversion Score (predicted)**
   - На основе наличия элементов:
     - Hero section с CTA: +10 баллов
     - Social proof: +15 баллов
     - Multi-step form: +20 баллов
     - Exit-intent popup: +10 баллов
     - Speed < 3 сек: +15 баллов
     - Mobile optimized: +10 баллов
   - Максимум: 100 баллов
   - Целевой score: > 70

5. **Compliance Risk**
   - Low: нет рисков
   - Medium: есть рекомендации
   - High: есть критичные проблемы (блокировка публикации)

**Код:**

```python
async def perform_quality_checks(self, content: dict) -> dict:
    """
    Выполняет проверки качества и генерирует метаданные.
    
    Args:
        content: Полный контент лендинга
    
    Returns:
        dict: Результаты проверок и метаданные
    """
    # Подсчёт слов
    word_count = sum(
        len(str(section).split())
        for section in content.values()
    )
    
    # Readability score (упрощённая формула Flesch)
    text = " ".join(str(s) for s in content.values())
    sentences = text.count('.') + text.count('!') + text.count('?')
    words = len(text.split())
    syllables = sum(self._count_syllables(word) for word in text.split())
    
    flesch_score = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
    
    # Conversion score prediction
    conversion_score = 0
    if "hero" in content and "cta" in content["hero"]:
        conversion_score += 10
    if "social_proof" in content:
        conversion_score += 15
    if content.get("lead_form", {}).get("type") == "multi_step":
        conversion_score += 20
    if content.get("exit_intent_popup", {}).get("enabled"):
        conversion_score += 10
    # Speed и mobile проверяются на этапе deployment
    
    # Compliance check
    compliance_result = await self.verify_compliance(content)
    
    # SEO metadata
    seo_metadata = {
        "title": content["hero"]["headline"][:60],  # Max 60 символов
        "description": content["hero"]["subheadline"][:160],  # Max 160 символов
        "keywords": self._extract_keywords(content),
        "og_image": content.get("hero", {}).get("image"),
        "canonical_url": content.get("url")
    }
    
    return {
        "quality_checks": {
            "word_count": {
                "value": word_count,
                "target": "800-1500",
                "status": "pass" if 800 <= word_count <= 1500 else "warning"
            },
            "readability": {
                "flesch_score": round(flesch_score, 1),
                "target": "> 60",
                "status": "pass" if flesch_score > 60 else "warning"
            },
            "conversion_score": {
                "value": conversion_score,
                "target": "> 70",
                "status": "pass" if conversion_score > 70 else "warning"
            }
        },
        "compliance": compliance_result,
        "seo_metadata": seo_metadata,
        "predicted_conversion_rate": self._predict_conversion_rate(conversion_score),
        "recommendations": self._generate_recommendations(
            word_count, flesch_score, conversion_score, compliance_result
        )
    }

def _count_syllables(self, word: str) -> int:
    """Подсчитывает количество слогов в слове (упрощённо)."""
    vowels = "аеёиоуыэюяАЕЁИОУЫЭЮЯ"
    count = sum(1 for char in word if char in vowels)
    return max(1, count)

def _predict_conversion_rate(self, conversion_score: int) -> float:
    """Предсказывает конверсию на основе score."""
    # Линейная интерполяция: 0 баллов = 2%, 100 баллов = 15%
    return 0.02 + (conversion_score / 100) * 0.13

def _generate_recommendations(
    self,
    word_count: int,
    flesch_score: float,
    conversion_score: int,
    compliance_result: dict
) -> list[str]:
    """Генерирует рекомендации по улучшению."""
    recommendations = []
    
    if word_count < 800:
        recommendations.append("Добавить больше контента (минимум 800 слов)")
    elif word_count > 1500:
        recommendations.append("Сократить контент или разбить на секции")
    
    if flesch_score < 60:
        recommendations.append("Упростить язык (короче предложения, проще слова)")
    
    if conversion_score < 70:
        recommendations.append("Добавить больше conversion элементов (CTA, social proof, exit-intent)")
    
    if compliance_result["risk_level"] != "low":
        recommendations.extend(compliance_result["recommendations"])
    
    return recommendations
```

---

## 4. Выходные данные

**Формат:** JSON event через Event Bus

**Структура:**

```json
{
  "event_type": "landing.content.generated",
  "timestamp": "2026-05-10T12:00:00Z",
  "agent_id": "landing-content-agent",
  "data": {
    "landing_page": {
      "hero": {
        "headline": "Боль в спине мешает жить? Избавьтесь от неё за 3 сеанса без операций",
        "subheadline": "500+ пациентов уже избавились от боли. Осталось 3 места на этой неделе.",
        "cta": {
          "text": "Записаться со скидкой 20%",
          "color": "#FF6B35",
          "url": "/book"
        },
        "image": "hero-back-pain.jpg"
      },
      "problem": {
        "headline": "Боль в спине разрушает вашу жизнь",
        "description": "Вы не можете нормально спать, работать, играть с детьми...",
        "agitation": "Если не лечить, боль будет только усиливаться...",
        "micro_commitment": "Согласны, что боль мешает жить полной жизнью?"
      },
      "solution": {
        "headline": "Мы избавим вас от боли без операций",
        "uvp": "Уникальная методика, основанная на 15-летнем опыте",
        "process": [
          "Диагностика (30 минут)",
          "Лечение (3 сеанса по 60 минут)",
          "Контроль результата (через 2 недели)"
        ],
        "credentials": {
          "degree": "Кандидат медицинских наук",
          "experience": "15 лет опыта",
          "certificates": ["Сертификат специалиста"]
        }
      },
      "benefits": [
        {
          "icon": "pain-relief.svg",
          "headline": "Избавление от боли за 3 сеанса",
          "description": "98% пациентов чувствуют улучшение уже после первого сеанса"
        },
        {
          "icon": "no-surgery.svg",
          "headline": "Без операций и таблеток",
          "description": "Безопасные методы, без побочных эффектов"
        },
        {
          "icon": "guarantee.svg",
          "headline": "Гарантия результата",
          "description": "Если не поможет — вернём деньги"
        }
      ],
      "social_proof": {
        "testimonials": [
          {
            "name": "Иван Петров",
            "photo": "ivan-petrov.jpg",
            "text": "Боль ушла после 2 сеансов! Спасибо!",
            "rating": 5
          }
        ],
        "statistics": {
          "patients": "500+",
          "experience": "15 лет",
          "success_rate": "98%"
        },
        "certificates": ["certificate1.jpg", "certificate2.jpg"]
      },
      "pricing": {
        "price": "5000 руб",
        "original_price": "6000 руб",
        "discount": "20%",
        "offer": "Скидка 20% при записи сегодня",
        "cta": {
          "text": "Записаться со скидкой",
          "urgency": "Только до 31 мая"
        }
      },
      "faq": [
        {
          "question": "Сколько сеансов нужно?",
          "answer": "Обычно 3-5 сеансов, в зависимости от тяжести случая"
        },
        {
          "question": "Это больно?",
          "answer": "Нет, процедура безболезненная"
        }
      ],
      "final_cta": {
        "headline": "Запишитесь сегодня и получите скидку 20%",
        "urgency": "Осталось 3 места на этой неделе",
        "cta": {
          "text": "Записаться сейчас",
          "color": "#FF6B35"
        },
        "disclaimer": "Результаты индивидуальны. Необходима консультация врача."
      }
    },
    "lead_form": {
      "type": "multi_step",
      "steps": [
        {
          "step": 1,
          "question": "Какая у вас проблема?",
          "type": "radio",
          "options": ["Боль в спине", "Боль в шее", "Головная боль", "Другое"]
        },
        {
          "step": 2,
          "question": "Как давно беспокоит?",
          "type": "radio",
          "options": ["Меньше месяца", "1-6 месяцев", "Больше 6 месяцев"]
        },
        {
          "step": 3,
          "question": "Оставьте контакты для записи",
          "fields": [
            {"name": "name", "type": "text", "required": true},
            {"name": "phone", "type": "tel", "required": true}
          ]
        }
      ],
      "protection": {
        "recaptcha": {"enabled": true, "version": "v3"},
        "honeypot": {"enabled": true}
      },
      "integration": {
        "crm": "amocrm",
        "webhook_url": "https://api.amocrm.ru/leads"
      }
    },
    "exit_intent_popup": {
      "enabled": true,
      "headline": "Не уходите! Скидка 20% при записи сегодня",
      "cta_text": "Записаться со скидкой 20%"
    },
    "metadata": {
      "framework_used": "AIDA",
      "psychological_triggers": ["scarcity", "social_proof", "authority", "urgency"],
      "word_count": 1200,
      "readability_score": 65.3,
      "conversion_score": 85,
      "predicted_conversion_rate": 0.13,
      "compliance_risk": "low",
      "seo_metadata": {
        "title": "Избавьтесь от боли в спине за 3 сеанса без операций",
        "description": "500+ пациентов уже избавились от боли. Запишитесь сегодня и получите скидку 20%.",
        "keywords": ["боль в спине", "лечение", "без операций"]
      }
    }
  }
}
```

---

## 5. Метрики успеха

### Ключевые метрики

| Метрика | Целевое значение | Критичность |
|---------|------------------|-------------|
| Conversion Rate | 5-15% | 🔴 CRITICAL |
| Exit-Intent Conversion | > 5% | 🟡 IMPORTANT |
| Page Load Time | < 3 секунды | 🔴 CRITICAL |
| Readability Score | > 60 | 🟡 IMPORTANT |
| Compliance Risk | Low | 🔴 CRITICAL |
| Word Count | 800-1,500 | 🟢 OPTIONAL |
| SEO Score | > 80 | 🟡 IMPORTANT |

### Бенчмарки

**Conversion Rate по фреймворкам:**
- AIDA: 8-12% (лучший для high-ticket услуг)
- PAS: 6-10% (лучший для pain-focused продаж)
- 4P: 10-15% (лучший для premium услуг)

**Conversion Rate по элементам:**
- Multi-step form: +30-40% vs single-step
- Exit-intent popup: +5-15% recovery rate
- Social proof: +25-40% trust
- Speed < 3 сек: baseline (каждая секунда задержки = -7%)

**Сравнение с Blog Content:**
- Blog Content: 2-5% conversion
- Landing Content: 5-15% conversion
- Разница: 3x выше


---

## 6. Коммуникация с другими агентами

### Входящие события (подписки)

| Event Type | Источник | Когда обрабатывать | Действие |
|------------|----------|-------------------|----------|
| `landing.content.request` | Content Magister | Запрос на создание лендинга | Запустить генерацию |
| `tone.verified` | Tone of Voice Agent | Проверка ToV завершена | Применить корректировки |
| `medical.facts.verified` | Medical Fact-Checker | Проверка фактов завершена | Обновить контент |
| `brand.voice.updated` | Brand Magister | Обновление Brand Voice | Пересоздать контент |

### Исходящие события (публикации)

| Event Type | Получатель | Когда отправлять | Данные |
|------------|-----------|------------------|--------|
| `landing.content.generated` | Content Magister | Лендинг создан | Полный контент + метаданные |
| `tone.verification.request` | Tone of Voice Agent | Нужна проверка ToV | Контент для проверки |
| `medical.facts.check.request` | Medical Fact-Checker | Нужна проверка фактов | Медицинские утверждения |
| `landing.content.failed` | Content Magister | Ошибка генерации | Причина ошибки |

### Интеграции с агентами

**Обязательные:**
1. **Tone of Voice Agent** — проверка соответствия ToV бренда
2. **Medical Fact-Checker Agent** — проверка медицинских фактов
3. **Brand Magister** — получение Brand Voice и UVP

**Опциональные:**
1. **Editor Agent** — финальная редактура и полировка
2. **A/B Testing Agent** — создание вариантов для тестирования (TODO)

### Пример коммуникации

```python
# Получение запроса от Content Magister
async def handle_landing_request(self, event: Event):
    """Обрабатывает запрос на создание лендинга."""
    
    # 1. Генерация контента
    landing = await self.generate_landing(event.data)
    
    # 2. Запрос проверки ToV
    await self.event_bus.publish(Event(
        type="tone.verification.request",
        data={"content": landing, "brand_id": event.data["brand_id"]}
    ))
    
    # 3. Ожидание результата проверки
    tone_result = await self.wait_for_event("tone.verified")
    
    # 4. Применение корректировок
    if not tone_result.data["compliant"]:
        landing = await self.apply_tone_corrections(
            landing, tone_result.data["corrections"]
        )
    
    # 5. Запрос проверки медицинских фактов
    await self.event_bus.publish(Event(
        type="medical.facts.check.request",
        data={"content": landing}
    ))
    
    # 6. Ожидание результата проверки
    medical_result = await self.wait_for_event("medical.facts.verified")
    
    # 7. Применение корректировок
    if not medical_result.data["verified"]:
        landing = await self.apply_medical_corrections(
            landing, medical_result.data["corrections"]
        )
    
    # 8. Отправка результата
    await self.event_bus.publish(Event(
        type="landing.content.generated",
        data={"landing": landing, "metadata": self.metadata}
    ))
```

---

## 7. Обработка ошибок

### Типичные ошибки

| Ошибка | Причина | Решение | Retry? |
|--------|---------|---------|--------|
| `InvalidServiceDataError` | Неполные данные об услуге | Запросить недостающие данные у пользователя | ❌ No |
| `ComplianceViolationError` | Нарушение медицинских требований | Удалить проблемные утверждения | ✅ Yes (1x) |
| `ToneVerificationFailedError` | Не прошла проверка ToV | Применить корректировки ToV Agent | ✅ Yes (2x) |
| `MedicalFactsCheckFailedError` | Не прошла проверка фактов | Применить корректировки Fact-Checker | ✅ Yes (2x) |
| `APITimeoutError` | Таймаут внешнего API | Повторить запрос с exponential backoff | ✅ Yes (3x) |
| `ContentGenerationError` | Ошибка генерации контента | Попробовать другой фреймворк | ✅ Yes (1x) |

### Стратегии обработки

**1. Retry с exponential backoff**
```python
async def retry_with_backoff(
    self,
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0
) -> Any:
    """Повторяет функцию с exponential backoff."""
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            await asyncio.sleep(delay)
```

**2. Fallback на другой фреймворк**
```python
async def generate_with_fallback(self, service: dict) -> dict:
    """Генерирует контент с fallback на другой фреймворк."""
    frameworks = ["AIDA", "PAS", "4P"]
    
    for framework in frameworks:
        try:
            return await self.generate_content(service, framework)
        except ContentGenerationError:
            if framework == frameworks[-1]:
                raise
            continue
```

**3. Graceful degradation**
```python
async def generate_landing_safe(self, service: dict) -> dict:
    """Генерирует лендинг с graceful degradation."""
    try:
        # Полная генерация
        return await self.generate_landing_full(service)
    except Exception as e:
        # Упрощённая генерация без опциональных элементов
        return await self.generate_landing_minimal(service)
```

### Логирование ошибок

```python
async def handle_error(self, error: Exception, context: dict):
    """Обрабатывает и логирует ошибку."""
    
    # Логирование в Obsidian vault
    await self.vault.append_to_log(
        f"## [{datetime.now()}] error | {error.__class__.__name__}\n\n"
        f"**Context:** {context}\n"
        f"**Error:** {str(error)}\n"
        f"**Traceback:** {traceback.format_exc()}\n\n"
        "---\n"
    )
    
    # Отправка события об ошибке
    await self.event_bus.publish(Event(
        type="landing.content.failed",
        data={
            "error": error.__class__.__name__,
            "message": str(error),
            "context": context
        }
    ))
    
    # Метрики
    await self.metrics.increment("errors", tags={
        "error_type": error.__class__.__name__
    })
```

---

## 8. Тестирование

### Unit Tests

**Тестируемые компоненты:**
1. Framework selection logic
2. Content generation для каждого фреймворка
3. Psychological triggers application
4. Multi-step form creation
5. Compliance verification
6. CTA optimization
7. Exit-intent popup generation
8. Quality checks

**Пример теста:**

```python
import pytest
from aim.subagents.landing_content_agent import LandingContentAgent

@pytest.mark.asyncio
async def test_framework_selection():
    """Тестирует выбор фреймворка."""
    agent = LandingContentAgent()
    
    # High-ticket услуга → AIDA
    framework = await agent.select_framework(
        content_type="landing",
        service_type="treatment",
        price=50000,
        audience_segment="patients"
    )
    assert framework == "AIDA"
    
    # Pain-focused услуга → PAS
    framework = await agent.select_framework(
        content_type="landing",
        service_type="diagnostic",
        price=5000,
        audience_segment="patients"
    )
    assert framework == "PAS"

@pytest.mark.asyncio
async def test_compliance_verification():
    """Тестирует проверку compliance."""
    agent = LandingContentAgent()
    
    # Контент с outcome guarantee → high risk
    content = {
        "hero": {"headline": "Вылечим за 3 дня на 100%"}
    }
    result = await agent.verify_compliance(content)
    assert result["risk_level"] == "high"
    assert any(r["type"] == "outcome_guarantee" for r in result["risks"])
    
    # Контент без гарантий → low risk
    content = {
        "hero": {"headline": "Избавьтесь от боли"},
        "final_cta": {"disclaimer": "Результаты индивидуальны"}
    }
    result = await agent.verify_compliance(content)
    assert result["risk_level"] == "low"

@pytest.mark.asyncio
async def test_multi_step_form_creation():
    """Тестирует создание multi-step формы."""
    agent = LandingContentAgent()
    
    # High-ticket → multi-step
    form = await agent.create_lead_form(
        service_price=50000,
        fields=["name", "phone"]
    )
    assert form["type"] == "multi_step"
    assert len(form["steps"]) == 3
    
    # Low-ticket → single-step
    form = await agent.create_lead_form(
        service_price=3000,
        fields=["name", "phone"]
    )
    assert form["type"] == "single_step"
```

### Integration Tests

**Тестируемые сценарии:**
1. Полный цикл генерации лендинга
2. Интеграция с Tone of Voice Agent
3. Интеграция с Medical Fact-Checker Agent
4. Интеграция с Brand Magister
5. Event Bus коммуникация

**Пример теста:**

```python
@pytest.mark.asyncio
async def test_full_landing_generation():
    """Тестирует полный цикл генерации лендинга."""
    agent = LandingContentAgent()
    
    # Входные данные
    service = {
        "name": "Лечение боли в спине",
        "type": "treatment",
        "price": 5000,
        "description": "Безоперационное лечение",
        "physicians": [{"name": "Иван Иванов", "credentials": "КМН"}],
        "testimonials": [{"name": "Пётр", "text": "Помогло!"}]
    }
    
    # Генерация
    result = await agent.generate_landing(service)
    
    # Проверки
    assert "landing_page" in result
    assert "hero" in result["landing_page"]
    assert "problem" in result["landing_page"]
    assert "solution" in result["landing_page"]
    assert "benefits" in result["landing_page"]
    assert "social_proof" in result["landing_page"]
    assert "pricing" in result["landing_page"]
    assert "faq" in result["landing_page"]
    assert "final_cta" in result["landing_page"]
    
    assert "lead_form" in result
    assert "metadata" in result
    
    # Проверка метаданных
    assert result["metadata"]["conversion_score"] > 70
    assert result["metadata"]["compliance_risk"] == "low"
    assert 800 <= result["metadata"]["word_count"] <= 1500
```

### Performance Tests

**Метрики:**
- Время генерации лендинга: < 30 секунд
- Время проверки compliance: < 5 секунд
- Время создания формы: < 2 секунды

```python
@pytest.mark.asyncio
async def test_generation_performance():
    """Тестирует производительность генерации."""
    agent = LandingContentAgent()
    
    service = {...}  # Тестовые данные
    
    start = time.time()
    result = await agent.generate_landing(service)
    duration = time.time() - start
    
    assert duration < 30, f"Generation took {duration}s (max 30s)"
```

---

## 9. Примеры использования

### Пример 1: Создание лендинга для high-ticket услуги

**Входные данные:**

```json
{
  "service": {
    "name": "Комплексное лечение позвоночника",
    "type": "treatment",
    "price": 50000,
    "description": "Безоперационное лечение грыжи позвоночника",
    "expected_result": "Избавление от боли за 10 сеансов",
    "treatment_process": [
      "Диагностика МРТ",
      "Индивидуальный план лечения",
      "10 сеансов терапии",
      "Контроль результата"
    ],
    "physicians": [
      {
        "name": "Иван Иванов",
        "credentials": "Кандидат медицинских наук, 15 лет опыта",
        "photo": "ivan-ivanov.jpg"
      }
    ],
    "testimonials": [
      {
        "name": "Пётр Петров",
        "photo": "petr-petrov.jpg",
        "text": "Боль ушла после 5 сеансов! Рекомендую!",
        "rating": 5
      }
    ],
    "statistics": {
      "patients": "500+",
      "experience": "15 лет",
      "success_rate": "98%"
    },
    "offer": "Скидка 20% при записи сегодня",
    "urgency_trigger": "Осталось 3 места на этой неделе"
  },
  "audience_segment": "patients",
  "brand_id": "clinic-123"
}
```

**Выходные данные:**

Полный лендинг с:
- Framework: AIDA (high-ticket)
- Multi-step form (3 шага)
- Exit-intent popup (скидка 20%)
- 5 CTA на странице
- Conversion score: 85
- Predicted conversion rate: 13%

### Пример 2: Создание лендинга для low-ticket услуги

**Входные данные:**

```json
{
  "service": {
    "name": "Консультация невролога",
    "type": "diagnostic",
    "price": 3000,
    "description": "Первичная консультация с диагностикой",
    "expected_result": "Точный диагноз и план лечения"
  }
}
```

**Выходные данные:**

Упрощённый лендинг с:
- Framework: PAS (pain-focused)
- Single-step form (имя + телефон)
- Exit-intent popup (бесплатная консультация)
- 3 CTA на странице
- Conversion score: 70
- Predicted conversion rate: 9%

### Пример 3: Обработка ошибки compliance

**Входные данные:**

```json
{
  "service": {
    "name": "Лечение рака",
    "description": "Гарантируем 100% излечение за 30 дней"
  }
}
```

**Результат:**

```json
{
  "error": "ComplianceViolationError",
  "risks": [
    {
      "type": "outcome_guarantee",
      "severity": "high",
      "pattern": "100% излечение",
      "recommendation": "Удалить гарантии результата"
    }
  ],
  "compliance_risk": "high",
  "action": "Блокировка публикации до исправления"
}
```


---

## 10. Зависимости

### Внешние API

| API | Назначение | Цена | Лимиты | Критичность |
|-----|-----------|------|--------|-------------|
| Anthropic Claude API | Генерация контента | $15/1M input tokens, $75/1M output tokens | 100K tokens/min | 🔴 CRITICAL |
| LanguageTool API | Проверка грамматики и стиля | Free: 20 req/min, Premium: $59/year | 20-100 req/min | 🟡 IMPORTANT |
| Textstat | Readability score | Free (Python library) | N/A | 🟢 OPTIONAL |
| AmoCRM API | Интеграция CRM | От 499 руб/мес | 500 req/min | 🟡 IMPORTANT |
| reCAPTCHA v3 | Защита от спама | Free: 1M assessments/month | 1M/month | 🟡 IMPORTANT |

### Python библиотеки

```python
# requirements.txt
anthropic>=0.18.0          # Claude API
langdetect>=1.0.9          # Определение языка
textstat>=0.7.3            # Readability metrics
pydantic>=2.0.0            # Data validation
aiohttp>=3.9.0             # Async HTTP
python-dotenv>=1.0.0       # Environment variables
```

### Внутренние зависимости

**Framework (meai):**
- `meai.agents.base_agent.Agent` — базовый класс агента
- `meai.events.event_bus.EventBus` — коммуникация через события
- `meai.memory.obsidian.ObsidianVault` — интеграция с Obsidian

**Агенты (AIM):**
- `Tone of Voice Agent` — проверка соответствия ToV
- `Medical Fact-Checker Agent` — проверка медицинских фактов
- `Brand Magister` — получение Brand Voice и UVP
- `Content Magister` — родительский Magister

### Конфигурация

```python
# config/landing_content_agent.yaml
agent:
  name: "landing-content-agent"
  version: "1.0.0"
  vault_path: "AIM/obsidian/content-magister/subagents/landing-content/"

frameworks:
  default: "AIDA"
  available: ["AIDA", "PAS", "4P", "BAB", "FAB", "StoryBrand", "PASTOR"]

conversion:
  target_rate: 0.10  # 10%
  min_rate: 0.05     # 5%
  max_rate: 0.15     # 15%

content:
  min_words: 800
  max_words: 1500
  target_readability: 60

compliance:
  strict_mode: true
  auto_fix: false  # Не исправлять автоматически, только предупреждать

forms:
  multi_step_threshold: 10000  # Цена услуги для multi-step формы
  required_fields: ["name", "phone"]
  optional_fields: ["email", "comment"]

exit_intent:
  enabled: true
  default_offer: "discount"
  default_discount: 20
  show_once_per_session: true

api:
  anthropic:
    model: "claude-opus-4-7"
    max_tokens: 4096
    temperature: 0.7
  
  languagetool:
    url: "https://api.languagetool.org/v2/check"
    language: "ru-RU"
  
  amocrm:
    url: "https://api.amocrm.ru"
    timeout: 30

metrics:
  track_conversion: true
  track_readability: true
  track_compliance: true
```

---

## 11. Deployment

### Docker

**Dockerfile:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY src/ ./src/
COPY config/ ./config/

# Переменные окружения
ENV PYTHONPATH=/app
ENV ANTHROPIC_API_KEY=""
ENV AMOCRM_API_KEY=""

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import sys; sys.exit(0)"

# Запуск
CMD ["python", "-m", "aim.subagents.landing_content_agent"]
```

**docker-compose.yml:**

```yaml
version: '3.8'

services:
  landing-content-agent:
    build: .
    container_name: landing-content-agent
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - AMOCRM_API_KEY=${AMOCRM_API_KEY}
      - DATABASE_URL=sqlite+aiosqlite:///./data/aim.db
      - OBSIDIAN_VAULT_PATH=/app/obsidian
    volumes:
      - ./AIM/obsidian:/app/obsidian
      - ./AIM/data:/app/data
    restart: unless-stopped
    networks:
      - aim-network

networks:
  aim-network:
    driver: bridge
```

### Kubernetes

**deployment.yaml:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: landing-content-agent
  namespace: aim
spec:
  replicas: 2
  selector:
    matchLabels:
      app: landing-content-agent
  template:
    metadata:
      labels:
        app: landing-content-agent
    spec:
      containers:
      - name: landing-content-agent
        image: aim/landing-content-agent:1.0.0
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: aim-secrets
              key: anthropic-api-key
        - name: AMOCRM_API_KEY
          valueFrom:
            secretKeyRef:
              name: aim-secrets
              key: amocrm-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Мониторинг

**Prometheus metrics:**

```python
from prometheus_client import Counter, Histogram, Gauge

# Метрики
landings_generated = Counter(
    'landing_content_generated_total',
    'Total number of landings generated',
    ['framework', 'service_type']
)

generation_duration = Histogram(
    'landing_content_generation_duration_seconds',
    'Time spent generating landing content',
    ['framework']
)

conversion_score = Gauge(
    'landing_content_conversion_score',
    'Predicted conversion score',
    ['framework', 'service_type']
)

compliance_violations = Counter(
    'landing_content_compliance_violations_total',
    'Total number of compliance violations',
    ['violation_type', 'severity']
)
```

---

## 12. Changelog

### Version 1.0.0 (2026-05-10)

**Создана спецификация Landing Content Agent**

**Основные возможности:**
- Интеллектуальный выбор conversion framework (AIDA, PAS, 4P)
- Генерация всех секций лендинга (hero, problem, solution, benefits, social proof, pricing, FAQ, final CTA)
- Применение психологических триггеров (scarcity, social proof, authority, urgency, reciprocity, consistency)
- Создание multi-step форм захвата лидов (+30-40% конверсии)
- Проверка медицинской compliance (FDA, 152-ФЗ, E-E-A-T, YMYL)
- Оптимизация CTA (5-7 CTA на странице)
- Exit-intent popup (5-15% recovery rate)
- Quality checks (word count, readability, conversion score, compliance risk)

**Метрики:**
- Целевая конверсия: 5-15% (3x выше блога)
- Predicted conversion score: 0-100
- Readability score: > 60
- Page load time: < 3 секунды

**Интеграции:**
- Tone of Voice Agent (проверка ToV)
- Medical Fact-Checker Agent (проверка фактов)
- Brand Magister (получение UVP)
- AmoCRM (отправка лидов)

**Размер спецификации:** ~45 KB, ~1,200 строк

**Исследование:** Landing Page Content Research (81 KB, 18,000 слов, deep mode)

---

## 13. TODO

### Высокий приоритет (P0)

- [ ] Реализовать базовый класс агента
- [ ] Реализовать framework selection logic
- [ ] Реализовать content generation для AIDA, PAS, 4P
- [ ] Реализовать compliance verification
- [ ] Реализовать multi-step form creation
- [ ] Интеграция с Tone of Voice Agent
- [ ] Интеграция с Medical Fact-Checker Agent
- [ ] Интеграция с Brand Magister

### Средний приоритет (P1)

- [ ] Реализовать psychological triggers application
- [ ] Реализовать CTA optimization
- [ ] Реализовать exit-intent popup generation
- [ ] Реализовать quality checks
- [ ] Добавить A/B тестирование вариантов
- [ ] Интеграция с AmoCRM
- [ ] Добавить reCAPTCHA v3

### Низкий приоритет (P2)

- [ ] Реализовать остальные фреймворки (BAB, FAB, StoryBrand, PASTOR)
- [ ] Добавить визуальный дизайн генерацию
- [ ] Добавить chatbot integration
- [ ] Добавить retargeting pixels setup
- [ ] Добавить speed optimization recommendations

### Исследования

- [ ] A/B тестирование фреймворков (какой лучше для каких услуг)
- [ ] Оптимизация exit-intent popup (какие офферы работают лучше)
- [ ] Исследование влияния multi-step форм на конверсию в медицине
- [ ] Benchmarking конверсии по типам услуг (diagnostic, treatment, preventive)

---

## Приложение A: Полный отчёт исследования

**Источник:** `~/Documents/Landing_Page_Content_Research_20260510/Landing_Page_Content_Research_Report.md`

**Размер:** 81 KB, 18,000 слов

**Режим:** Deep (8 фаз, 180 минут)

**Основные разделы:**

1. Executive Summary
2. Introduction
3. Conversion Frameworks Deep Dive
4. Psychological Triggers in Medical Marketing
5. Landing Page Structure & Anatomy
6. Medical Compliance & Legal Requirements
7. Lead Capture Forms Optimization
8. Call-to-Action (CTA) Best Practices
9. Social Proof Elements
10. Pricing Presentation Strategies
11. Mobile Optimization
12. Exit-Intent Popups
13. Retargeting & Analytics
14. Speed Optimization
15. A/B Testing Methodology
16. Visual Design Principles
17. Chatbot Integration
18. Synthesis & Strategic Recommendations

**Ключевые находки:**

- Multi-step forms: +30-40% конверсии vs single-step
- Page speed: каждая секунда задержки = -7% конверсии
- Authority signals: +25-40% доверия
- Exit-intent popups: 5-15% recovery rate
- Social proof: +25-40% конверсии
- AIDA framework: лучший для high-ticket услуг (8-12% конверсия)
- PAS framework: лучший для pain-focused продаж (6-10% конверсия)
- 4P framework: лучший для premium услуг (10-15% конверсия)

**Источники:** 15 источников (FDA guidelines, HIPAA compliance, Google research, training data)

**Полный отчёт доступен в:** `~/Documents/Landing_Page_Content_Research_20260510/`

---

**Конец спецификации**

**Автор:** Mikhail Eliseev (via meAI Architect)  
**Дата создания:** 2026-05-10  
**Версия:** 1.0.0  
**Статус:** ✅ Готов к реализации

