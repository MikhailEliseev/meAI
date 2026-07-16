# 🎯 ПРИОРИТИЗАЦИЯ SUBAGENTS

**Дата:** 2026-05-09  
**Цель:** Определить порядок создания спецификаций и реализации Subagents  
**Критерий:** Критичность для запуска системы + влияние на прибыль

---

## 📊 КРИТЕРИИ ПРИОРИТИЗАЦИИ

### P0 (Критичные) - Без них система не работает
- Блокируют запуск базового функционала
- Обязательны для первого проекта
- Реализация: 1-2 дня

### P1 (Важные) - Нужны для полноценной работы
- Основные каналы привлечения клиентов
- Генерируют прибыль напрямую
- Реализация: 3-5 дней

### P2 (Полезные) - Дают конкурентное преимущество
- Оптимизация и улучшение результатов
- Разведка и аналитика
- Реализация: 5-7 дней

### P3 (Nice to have) - Можно добавить позже
- Автоматизация рутины
- Масштабирование
- Реализация: по мере необходимости

---

## 🚀 P0: КРИТИЧНЫЕ SUBAGENTS (7 штук)

### 1. Medical Fact-Checker Agent ⭐⭐⭐⭐⭐
**Magister:** Content Magister  
**Почему P0:** Медицинская специфика, обязателен по закону  
**Задачи:**
- Проверка медицинских фактов
- Валидация по академическим источникам
- Соответствие законодательству РФ
- Утверждение у доктора

**Статус:** ❌ Нет спецификации  
**Реализация из Superflow:** Нет

---

### 2. Data Reconciliation Agent ⭐⭐⭐⭐⭐
**Magister:** Analytics Magister  
**Почему P0:** От него зависит ВСЁ, поиск истины в данных  
**Задачи:**
- Сверка данных из разных источников
- Поиск расхождений
- Определение истинных значений
- Корреляция метрик

**Статус:** ❌ Нет спецификации  
**Реализация из Superflow:** Нет

---

### 3. Technical SEO Agent ⭐⭐⭐
**Magister:** SEO Magister  
**Почему P0:** Базовая SEO оптимизация  
**Задачи:**
- robots.txt, sitemap.xml
- Meta tags, PageSpeed
- Schema.org validation

**Статус:** ✅ Есть спецификация (из Superflow)  
**Реализация из Superflow:** ✅ Да (`AIM/src/aim/subagents/seo/technical_agent.py`)

---

### 4. Content SEO Agent ⭐⭐⭐
**Magister:** SEO Magister  
**Почему P0:** SEO-оптимизированный контент  
**Задачи:**
- Header structure analysis
- Keyword density
- Readability scoring
- Content quality

**Статус:** ✅ Есть спецификация (из Superflow)  
**Реализация из Superflow:** ✅ Да (`AIM/src/aim/subagents/seo/content_agent.py`)

---

### 5. Links SEO Agent ⭐⭐⭐
**Magister:** SEO Magister  
**Почему P0:** Ссылочная масса критична для SEO  
**Задачи:**
- Internal/external links analysis
- Broken links detection
- Anchor text analysis

**Статус:** ✅ Есть спецификация (из Superflow)  
**Реализация из Superflow:** ✅ Да (`AIM/src/aim/subagents/seo/links_agent.py`)

---

### 6. Tone of Voice Agent ⭐⭐⭐⭐
**Magister:** Brand Magister  
**Почему P0:** Единый стиль коммуникации во всех каналах  
**Задачи:**
- Анализ языка пациентов (реальные звонки, комментарии)
- Формирование деликатного ToV
- Обновление ежеквартально
- Передача Content + Social Magisters

**Статус:** ❌ Нет спецификации  
**Реализация из Superflow:** Нет

---

### 7. Data Collector Agent ⭐⭐⭐⭐
**Magister:** Analytics Magister  
**Почему P0:** Без данных нет аналитики  
**Задачи:**
- Сбор данных из GA, Metrica, Keys.so
- Сбор данных из Direct API, VK Ads API
- Сбор данных из CallTouch, Roistat
- Ежедневный сбор (каждое утро)

**Статус:** ❌ Нет спецификации  
**Реализация из Superflow:** Нет

---

## 💰 P1: ВАЖНЫЕ SUBAGENTS (15 штук)

### SEO Magister (3 агента):

#### 8. Keyword Research Agent ⭐⭐⭐
**Задачи:** Подбор ключевых слов, анализ конкурентов, семантическое ядро

#### 9. Web Analytics Agent ⭐⭐⭐
**Задачи:** GA/Metrica интеграция, воронки конверсии, цели и события

#### 10. Search Console Agent ⭐⭐⭐
**Задачи:** GSC/Yandex Webmaster, позиции, ошибки индексации

---

### Content Magister (3 агента):

#### 11. Blog Content Agent ⭐⭐⭐
**Задачи:** SEO-статьи для блога, экспертный контент

#### 12. Landing Content Agent ⭐⭐⭐
**Задачи:** Продающие лендинги, конверсионный контент

#### 13. Editor Agent ⭐⭐⭐
**Задачи:** Редактура, проверка качества, стиль

---

### Ads Magister (3 агента):

#### 14. Campaign Manager Agent ⭐⭐⭐
**Задачи:** Создание кампаний, настройка таргетинга, запуск

#### 15. Budget Optimizer Agent ⭐⭐⭐
**Задачи:** Динамическая оптимизация бюджета, перераспределение

#### 16. Performance Monitor Agent ⭐⭐⭐
**Задачи:** Мониторинг метрик, автоматическая корректировка

---

### Social Magister (3 агента):

#### 17. Trend Watcher Agent ⭐⭐⭐⭐⭐
**Задачи:** Apify скрапинг, анализ виральности, адаптация трендов  
**Особенность:** ОДИН ИЗ САМЫХ СИЛЬНЫХ БЛОКОВ

#### 18. Content Scheduler Agent ⭐⭐⭐
**Задачи:** Планирование публикаций, оптимальное время

#### 19. AI Sales Admin Agent ⭐⭐⭐⭐
**Задачи:** Продажник-Администратор 24/7, обработка заявок из соцсетей

---

### Analytics Magister (3 агента):

#### 20. Competitor Analysis Agent ⭐⭐⭐
**Задачи:** Еженедельный мониторинг конкурентов, сравнение метрик

#### 21. Report Generator Agent ⭐⭐⭐
**Задачи:** Автоматические отчёты, визуализация, инсайты

#### 22. Data Processor Agent ⭐⭐⭐
**Задачи:** Обработка сырых данных, нормализация, агрегация

---

## 🔍 P2: ПОЛЕЗНЫЕ SUBAGENTS (20 штук)

### GEO Orchestrator (3 агента):

#### 23. GEO Optimization Agent ⭐⭐⭐⭐
**Задачи:** Оптимизация под нейросети (ChatGPT, Perplexity, Claude)

#### 24. GEO Monitoring Agent ⭐⭐⭐
**Задачи:** Мониторинг упоминаний в нейросетях, позиции в AI-выдаче

#### 25. GEO Content Agent ⭐⭐⭐
**Задачи:** Контент для нейросетей, адаптация под AI-запросы

---

### Intelligence Magister (11 агентов - большой рой!):

#### 26. CI Tech Agent ⭐⭐⭐
**Задачи:** Технический анализ сайтов конкурентов

#### 27. CI Content Agent ⭐⭐⭐
**Задачи:** Контент-стратегия конкурентов

#### 28. CI Social Agent ⭐⭐⭐
**Задачи:** SMM активность конкурентов

#### 29. CI Ads Agent ⭐⭐⭐
**Задачи:** Рекламные кампании конкурентов

#### 30. CI Price Agent ⭐⭐⭐
**Задачи:** Ценообразование конкурентов

#### 31. CI Reputation Agent ⭐⭐⭐
**Задачи:** Репутация конкурентов, отзывы

#### 32. Media Monitor Agent ⭐⭐⭐
**Задачи:** Упоминания в СМИ (Медиалогия API)

#### 33. Telegram Channel Monitor Agent ⭐⭐⭐
**Задачи:** Мониторинг Telegram каналов (Telemetr)

#### 34. Comment Analyzer Agent ⭐⭐⭐
**Задачи:** Анализ комментариев конкурентов

#### 35. Predictive Agent ⭐⭐⭐⭐
**Задачи:** Предсказание действий конкурентов

#### 36. Lead Interceptor Agent ⭐⭐⭐⭐
**Задачи:** Перехват лидов на факапах конкурентов

---

### Brand Magister (3 агента):

#### 37. CustDev Analyzer Agent ⭐⭐⭐⭐⭐
**Задачи:** Синтетический + реальный CustDev, JTBD анализ

#### 38. Visual Brand Analyzer Agent ⭐⭐⭐⭐⭐
**Задачи:** Статический (Playwright + Claude Vision) + динамический (Yandex Webvisor)

#### 39. Positioning Agent ⭐⭐⭐
**Задачи:** Отстройка от конкурентов vs мимикрия

---

### Reputation Magister (3 агента):

#### 40. Review Monitor Agent ⭐⭐⭐
**Задачи:** Мониторинг отзывов на всех платформах

#### 41. Social Chat Agent ⭐⭐⭐⭐
**Задачи:** Бот на OpenClaw, 24/7, самообучающийся

#### 42. NPS Analyzer Agent ⭐⭐⭐
**Задачи:** Синтетический (анализ фона) + реальный (опросы) NPS

---

## 🤖 P3: NICE TO HAVE SUBAGENTS (8+ штук)

### Content Magister (7 агентов):

#### 43. Reels Content Agent
**Задачи:** Сценарии для Reels

#### 44. YouTube Content Agent
**Задачи:** Сценарии для YouTube

#### 45. Email Content Agent
**Задачи:** Email-рассылки

#### 46. Telegram/VK Content Agent
**Задачи:** Контент для мессенджеров

#### 47. Banner Content Agent
**Задачи:** Баннеры для рекламы

#### 48. Call Center Script Agent
**Задачи:** Скрипты для колл-центра

#### 49. Leaflet Content Agent
**Задачи:** Листовки и печатные материалы

---

### Ads Magister (1 агент):

#### 50. Creative Tester Agent
**Задачи:** A/B тестирование креативов

---

## 📊 ИТОГОВАЯ СТАТИСТИКА

### По приоритетам:
- **P0 (Критичные):** 7 агентов
- **P1 (Важные):** 15 агентов
- **P2 (Полезные):** 20 агентов
- **P3 (Nice to have):** 8+ агентов

**Итого:** ~50 Subagents

### По статусу реализации:
- ✅ **Реализовано (из Superflow):** 3 агента (Technical SEO, Content SEO, Links SEO)
- ❌ **Нужно создать спецификации:** 47+ агентов

### По Magisters:
- SEO Magister: 6 агентов (3 SEO + 3 GEO)
- Content Magister: 13 агентов
- Ads Magister: 5 агентов
- Social Magister: 3 агента
- Analytics Magister: 6 агентов
- Intelligence Magister: 11 агентов
- Brand Magister: 4 агента
- Reputation Magister: 3 агента

---

## 🚀 ПЛАН РЕАЛИЗАЦИИ

### Неделя 1: P0 (Критичные)
**Цель:** Создать спецификации для 4 недостающих P0 агентов

1. Medical Fact-Checker Agent
2. Data Reconciliation Agent
3. Tone of Voice Agent
4. Data Collector Agent

**Результат:** Базовый функционал готов к реализации

---

### Неделя 2-3: P1 (Важные)
**Цель:** Создать спецификации для 15 P1 агентов

**SEO (3):** Keyword Research, Web Analytics, Search Console  
**Content (3):** Blog, Landing, Editor  
**Ads (3):** Campaign Manager, Budget Optimizer, Performance Monitor  
**Social (3):** Trend Watcher, Content Scheduler, AI Sales Admin  
**Analytics (3):** Competitor Analysis, Report Generator, Data Processor

**Результат:** Основные каналы готовы к реализации

---

### Неделя 4-5: P2 (Полезные)
**Цель:** Создать спецификации для 20 P2 агентов

**GEO (3):** Optimization, Monitoring, Content  
**Intelligence (11):** Весь рой CI агентов  
**Brand (3):** CustDev, Visual Analyzer, Positioning  
**Reputation (3):** Review Monitor, Social Chat, NPS Analyzer

**Результат:** Конкурентное преимущество готово к реализации

---

### Неделя 6+: P3 (Nice to have)
**Цель:** Создать спецификации по мере необходимости

**Content (7):** Специализированные контент-агенты  
**Ads (1):** Creative Tester

**Результат:** Полная автоматизация и масштабирование

---

## 🎯 РЕКОМЕНДАЦИЯ

**Начать с P0 агентов:**

1. **Medical Fact-Checker Agent** (критичный для медицины!)
2. **Data Reconciliation Agent** (от него зависит ВСЁ!)
3. **Tone of Voice Agent** (единый стиль коммуникации)
4. **Data Collector Agent** (без данных нет аналитики)

**Время:** 1-2 дня на создание спецификаций  
**Результат:** Базовый функционал готов к реализации

---

**Дата создания:** 2026-05-09 16:58 GMT+3  
**Статус:** ✅ Приоритизация готова  
**Следующий шаг:** Создать спецификации P0 агентов
