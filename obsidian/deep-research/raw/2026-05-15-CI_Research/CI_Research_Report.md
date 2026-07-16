# CI Research Agent (Competitor Intelligence) - Deep Research Report

**Дата:** 2026-05-15  
**Модель:** exa-research  
**Стоимость:** $0.84  
**Страниц:** 126.5  
**Поисковых запросов:** 41

---

## Executive Summary

Исследование охватывает методологию Industry Benchmark для reverse-engineering конкурентов в медицинском маркетинге. Ключевые находки:

1. **Source Harvest Methodology** — структурированный подход к сбору первичных источников с приоритизацией primary/operator > secondary > tertiary
2. **Evidence Labeling** — система меток [E]/[I]/[UV]/[OQ] для разделения фактов и выводов
3. **Growth Machine Reverse-Engineering** — декомпозиция роста по стадиям AARRR (acquisition → conversion → activation → retention → expansion)
4. **Medical Marketing Specifics** — trust architecture, HIPAA compliance, patient journey mapping
5. **Pattern Extraction** — методология выявления growth laws, sales laws, archetypes
6. **Transferability Analysis** — критерии Copy/Adapt/Ignore для паттернов конкурентов

---

## Источник и архивация доказательств — Source Harvest Methodology

### Приоритет источников

**Иерархия (primary > secondary > tertiary):**

1. **Primary/Operator sources** (наивысшая ценность):
   - Интервью основателей и executives
   - Подкасты с операторами
   - Посты операторов (LinkedIn, блоги)
   - Стенограммы кейс-стади
   - Win-loss интервью
   - Прямые наблюдения

2. **Secondary sources**:
   - Официальные документы компании
   - Product docs, launch posts
   - Customer stories
   - Pricing pages
   - Job descriptions

3. **Tertiary sources**:
   - Новостные статьи
   - Аналитические отчёты
   - SEO-контент
   - Press releases

**Источники:** [Klue](https://klue.com/blog/sources-of-competitive-intelligence), [Contify](https://www.contify.com/resources/blog/reboot-competitive-intelligence-by-leveraging-competitive-intelligence-solution-for-integrating-primary-and-secondary-research)

### Этические и легальные рамки

**КРИТИЧНО для медицинского маркетинга:**

- ✅ Собирать только публично доступную информацию
- ✅ Легально полученные данные
- ❌ Избегать взлома, подставных аккаунтов
- ❌ Незаконный доступ к платным материалам
- ✅ Соблюдать HIPAA/GDPR при работе с персональными данными

**Источники:** [Competitive Intelligence Alliance](https://www.competitiveintelligencealliance.io/competitive-intelligence-complete-guide), [AccountableHQ HIPAA Guide](https://www.accountablehq.com/post/hipaa-and-healthcare-advertising-compliance-guide-for-marketers)

### Структура Evidence Archive

**Рекомендуемая файловая организация:**

```
source-harvest-phase/
├── <company>/
│   ├── company.md              # Синтезированная карточка компании
│   ├── TODO-sources.md         # Список недостающих источников
│   ├── people/                 # Профили ключевых фигур
│   │   └── <person>.md
│   ├── sources/                # Хранилище исходников
│   │   └── <source>.md
│   ├── deals/                  # Сделки и партнёрства
│   ├── product/                # Продуктовая информация
│   ├── ads/                    # Рекламные креативы
│   ├── seo/                    # SEO-данные
│   └── ISSUE_LOG.md           # Открытые вопросы [OQ]
```

**company.md должен содержать:**
- Миссия и позиционирование
- Initial wedge (с чего начали)
- GTM стратегия
- Ключевые продукты/услуги
- Целевые сегменты
- Публичные метрики (funding, ARR estimates)
- Evidence quality score (%E/%I/%UV)

**sources/<source>.md должен содержать:**
- Заголовок и тип источника
- Дата публикации
- URL и timestamp
- Кто говорит (автор, роль)
- Почему источник важен
- Ключевые факты (с метками [E])
- Прямые цитаты
- Что раскрывает о growth/GTM/pricing
- Caveats и uncertainty

**people/<person>.md должен содержать:**
- Роль в компании
- Релевантность для growth story
- Ключевые цитаты и утверждения
- Ссылки на источники
- Career pattern (если важно для GTM)

**Источник:** [Contify CI Analysis](https://www.contify.com/resources/blog/competitive-intelligence-analysis)

### Метаданные и версионирование

**Обязательные поля для каждого источника:**
- Provenance (URL, timestamp, snapshot hash)
- Кто собрал (analyst name)
- Краткая верификация (verified/unverified)
- Access method (public/paywalled/partnership)

**Интеграция:**
- Notion/Airtable для структурированных данных
- Git для версионирования
- Slack CI-channel для алертов
- DFP (Data Flow Platform) для автоматизации

---

## Evidence Labeling — практическая схема

### Система меток (ОБЯЗАТЕЛЬНА для всех утверждений)

**[E] — Sourced Evidence**
- Прямая первичная или вторичная ссылка
- Цитата из интервью, транскрипт подкаста
- Официальный пресс-релиз, кейс-стади
- ВСЕГДА включает URL и timestamp

**[I] — Inference**
- Аналитическое заключение исследователя
- Выведено на основе совокупности источников
- ОБЯЗАТЕЛЬНО указывать базовые источники (ссылки)
- Уровень уверенности (high/medium/low)

**[UV] — Unverified**
- Утверждение найдено, но не подтверждено
- Требует проверки (due date)
- Например: скриншот вакансии без подтверждения

**[OQ] — Open Question**
- Нерешённый вопрос
- Требует primary research или внутренней проверки
- Например: "Кто принимает решение по закупке в клинике X?"

### Примеры применения

✅ **Правильно:**
```markdown
Клиника X использует freemium POC для привлечения корпоративных клиентов [I]
  Базовые источники:
  - [E] Интервью CEO в подкасте Healthcare Growth (2025-03-15)
  - [E] Кейс-стади на сайте компании (2025-04-01)
  - [E] Job ad для "POC Coordinator" (2025-02-10)
  Уверенность: high
```

❌ **Неправильно:**
```markdown
Клиника X использует freemium POC для привлечения клиентов.
(нет метки, нет источников, нет уверенности)
```

### Визуализация показателей доказательности

**Evidence Quality Score:**
```
Evidence Score = (E_count × 3 + Secondary_count × 2 + Tertiary_count × 1) / Total_claims

Целевой KPI: >70% sourced claims (E) для высокого качества
```

**Источники:** [APQC Benchmarking](https://www.apqc.org/resources/blog/how-benchmark-against-competitors), [Cedar Gate Analytics](https://www.cedargate.com/wp-content/uploads/2024/07/CGT-White-Paper-Cedar-Gate-Benchmarking_Analytics-HBA-2024-1.pdf)

---

## Инструменты автоматизации сбора

### No-code / Low-code инструменты

**Browse AI** — визуальная парсинг-автоматизация
- Мониторинг изменений на сайтах конкурентов
- Извлечение pricing pages, job ads
- Алерты при обновлениях

**Phantombuster** — автоматизация соц-платформ
- LinkedIn scraping (profiles, posts, company pages)
- Twitter/X monitoring
- Instagram/Facebook data extraction

**Octoparse** — универсальный web scraper
- Визуальный конструктор роботов
- Scheduled scraping
- Cloud-based execution

**Источник:** [Medium Web Scraping Tools Review](https://medium.com/@james_nash_hhh/steal-their-strategy-the-5-leading-web-scraping-tools-for-competitive-analysis-5d1c9b899cfa)

### Платформы и инфраструктура

**Apify Marketplace** — готовые actors для:
- Google Search scraping
- Social media monitoring
- E-commerce data extraction
- Review aggregation

**ScraperAPI** — proxy + captcha handling
- Устойчивость к блокировкам
- Rotating proxies
- CAPTCHA solving
- Rate limiting management

**Источник:** [Firecrawl Web Scraping APIs](https://www.firecrawl.dev/glossary/web-scraping-apis/best-web-scraping-api-competitor-research)

### Интеграция в CI Pipeline

**Поток данных:**
```
Web Sources → Scraping Tools → S3/DB → ETL → Normalization → Airtable/Notion
                                                                    ↓
                                                            Slack Alerts
                                                                    ↓
                                                        Dashboards (Looker/Tableau)
```

**Best Practices:**
- Хранить raw snapshots для аудита
- Сохранять транскрипты и timestamps
- Версионировать данные (Git LFS)
- Логировать все API calls

### Легальные шаблоны для медицины

**Business Associate Agreement (BAA):**
- Обязателен при обработке PHI
- Контракт с vendors
- Data mapping и flow documentation

**Источник:** [AccountableHQ HIPAA Guide](https://www.accountablehq.com/post/hipaa-and-healthcare-advertising-compliance-guide-for-marketers)

---

## Growth Machine Reverse-Engineering

### Каркас анализа (AARRR Framework)

**Стадии роста:**
1. **Acquisition** — как привлекают пользователей
2. **Activation** — первый опыт и "aha moment"
3. **Retention** — как удерживают
4. **Revenue** — как монетизируют
5. **Referral** — как стимулируют рекомендации

**Источник:** [Simon-Kucher AARRR Guide](https://www.simon-kucher.com/en/insights/acquisition-revenue-mastering-aarrr-stages)

### 1. Идентификация Initial Wedge

**Что такое wedge:**
- Первоначальное конкурентное преимущество
- "Точка входа" в рынок
- Уникальная ценность для первых клиентов

**Источники для поиска wedge:**
- Ранние интервью основателей
- Первые маркетинговые кампании
- Первые партнёрства
- Seed case studies
- Hiring patterns (первые ключевые роли)
- Первые funding milestones

**Проверка гипотез (3 признака сильного wedge):**
1. **Strong customer love** — повторное использование, отзывы
2. **Team competency aligned** — команда имеет экспертизу в wedge
3. **Economic viability** — защитимость и replicability constraints

**Источники:** [NFX Wedge Article](https://www.nfx.com/post/finding-your-killer-wedge), [Medium Wedge Analysis](https://medium.com/letters-from-the-savannah/the-wedge-and-competitive-analysis-789466413ee9)

### 2. Декомпозиция Growth System

**Acquisition (как привлекают):**
- Каналы: organic SEO, paid search, local GBP/Maps, referrals, partnerships
- Кампании и креативы
- Таргетинг и сегментация
- **Инструменты:** SimilarWeb, SEMrush, Ahrefs для трафика и ключевых слов

**Conversion (как конвертируют):**
- Landing pages и CTA
- Booking flow и формы
- Triage forms (для медицины)
- Drop-off анализ (view → booking)
- **Практика:** Пройти flow конкурента, зафиксировать формы

**Activation / Time-to-Value:**
- Что пациент/клиент видит как первый импакт
- Appointment speed (скорость записи)
- First consult quality
- Telehealth setup
- **Метрика:** Time-to-Value должен быть измерим и сокращён

**Retention (как удерживают):**
- Recall и follow-ups
- Subscription/contract renewals
- NRR (Net Revenue Retention)
- Повторные визиты и NPS/ratings

**Expansion (как расширяют):**
- Cross-sell сервисов (diagnostics, premium care plans)
- Referral programs
- Upsell в premium тарифы

**Источник:** [Martal Medical Sales Insights](https://martal.ca/medical-software-sales-lb)

### 3. Reverse-Engineering Unit Economics

**Определение единицы (unit):**
- **B2B (клиники):** ACV (Annual Contract Value)
- **B2C (пациенты):** Средняя выручка на пациента
- **Hybrid:** Blended model

**Ключевые формулы:**

```
CAC = Total S&M Costs / New Customers

LTV = (ARPU × Gross Margin) / Churn Rate

Payback Period = CAC / (ARPU × Gross Margin)

LTV:CAC Ratio = LTV / CAC (цель: >3:1)
```

**Медицинский B2B:**
- Длинный sales cycle → более длинные payback (12-24 мес.)
- Enterprise deals → высокий ACV, но длинная конверсия
- Compliance overhead → дополнительные S&M costs

**Практика CI:**
- Собрать публичные сигналы (pricing pages)
- Job ads для sales hires → оценка S&M load
- Funding и ARR clues → построить диапазонные оценки
- Best/Likely/Worst case scenarios

**Источники:** [DualEntry SaaS Unit Economics](https://www.dualentry.com/blog/saas-unit-economics), [Dodo Payments Guide](https://dodopayments.com/blogs/saas-unit-economics)

### 4. Sales Cycle Analysis

**Карта ролей (B2B Healthcare):**

| Роль | Функция | Влияние |
|------|---------|---------|
| **Decision Maker** | CFO/CEO/Procurement | Финальное решение |
| **Champion** | Врач/Главврач | Продвигает решение |
| **Blocker** | Compliance/Legal/IT | Может заблокировать |
| **Influencer** | Nurse Managers | Влияет на мнение |

**Многослойный комитет покупки** — стандарт для healthcare B2B

**Pilot/POC структура:**
- Time-boxed POC с чёткими success criteria
- KPI и участие бюджетных владельцев
- Co-designed workshops вместо длинных пробных периодов
- **Цель:** Сократить POC cycle с 6-12 мес. до 4-8 недель

**Триггеры и blockers:**
- Регуляторные проверки (HIPAA, FDA)
- Интеграция с EHR (Epic, Cerner)
- Безопасность данных
- Клиническая эффективность (outcomes)

**Источники:** [New Breed Revenue Buying Roles](https://www.newbreedrevenue.com/blog/buying-roles-in-the-sales-process), [Martal Medical Sales](https://martal.ca/medical-software-sales-lb)

---

## Medical Marketing Competitive Intelligence — специфика

### Trust Architecture в Healthcare

**"Доверие" — первичный товар в медицине**

**Ключевые элементы trust architecture:**

1. **Сертификаты и аккредитации**
   - Медицинские лицензии
   - Аккредитация JCI/ISO
   - Сертификаты специалистов

2. **Верифицированные кейсы**
   - Patient success stories (с согласием)
   - Clinical outcomes data
   - Before/after (с этическими ограничениями)

3. **Пациентские отзывы и рейтинги**
   - HealthGrades, Zocdoc, Google Reviews
   - Рейтинги врачей
   - NPS и satisfaction scores

4. **Публичные рекомендации**
   - Endorsements от профильных специалистов
   - Peer reviews
   - Medical associations membership

5. **Клинические результаты**
   - Outcomes data (mortality, readmission rates)
   - Quality metrics (HEDIS, CMS Star Ratings)
   - Research publications

**Источники:** [rater8 Trust Marketing](https://rater8.com/blog/trust-marketing), [Reputation.com Healthcare Guide](https://reputation.com/resources/reports-guides/a-departmental-guide-to-reputation-management-in-healthcare)

### Compliance Constraints

**HIPAA (US) — критично для CI:**

❌ **Запрещено:**
- Использовать PHI в маркетинге без явного согласия
- Публиковать patient stories без authorization
- Передавать PHI третьим лицам без BAA

✅ **Разрешено:**
- De-identified data (18 identifiers removed)
- Aggregated statistics
- Public health information
- Marketing с explicit opt-in

**Business Associate Agreement (BAA):**
- Обязателен при привлечении внешних провайдеров
- Mapping data flows — необходимая практика
- Audit trail для всех PHI touchpoints

**Источники:** [HHS HIPAA Marketing Guidance](https://www.hhs.gov/hipaa/for-professionals/privacy/guidance/marketing/index.html), [AccountableHQ Guide](https://www.accountablehq.com/post/hipaa-and-healthcare-advertising-compliance-guide-for-marketers)

**Россия — специфика:**

- ФЗ-61 "О обращении лекарственных средств"
- Реклама медицинских услуг регулируется
- Рейтинговые платформы работают иначе
- Локальные особенности прозрачности

**Источник:** [Gorodissky Russia Life Sciences](https://www.gorodissky.com/publications/articles/the-life-sciences-law-review-chapter-russia-2022)

**Международная практика:**
- **GDPR (EU):** Consent, right to erasure, data portability
- **ASA/MHRA (UK):** Строгие правила для pharma
- **Избегать:** Неподтверждённые клинические утверждения

**Источник:** [Vellepulse Global Compliance](https://vellepulse.com/blog/global-healthcare-marketing-compliance-2025)

### Patient Journey Mapping

**Стадии пациентского пути:**

```
Awareness → Consideration → Decision → Treatment → Retention
```

**Awareness (осведомлённость):**
- SEO и контент-маркетинг
- Educational content
- Symptom checkers
- Health blogs и guides

**Consideration (рассмотрение):**
- Рейтинги и отзывы
- Physician bios и credentials
- Facility tours (virtual/physical)
- Insurance acceptance

**Decision (решение):**
- Удобное бронирование
- Скорость первой консультации
- Pricing transparency
- Insurance verification

**Treatment/Activation:**
- First consult quality
- Onboarding experience
- Patient portal access
- Communication channels

**Retention:**
- Follow-ups и recall
- Patient satisfaction surveys
- Loyalty programs
- Referral incentives

**Источник:** [Siteimprove Patient Journey](https://www.siteimprove.com/blog/patient-journey-mapping-healthcare-marketing)

### Reputation-First Adoption Patterns

**Social Proof эффект:**
- Клиники с сильной репутацией доминируют в локальных поисках
- Рейтинги влияют на SEO rankings
- Отзывы = конверсионный фактор

**Операционные KPI → Маркетинг:**
```
NPS ↑ → Reviews ↑ → SEO Uplift ↑ → Organic Traffic ↑ → New Patients ↑
```

**Источник:** [Reputation.com Guide](https://reputation.com/resources/reports-guides/a-departmental-guide-to-reputation-management-in-healthcare)

### Local SEO и Google Business Profile

**GBP = "Digital Front Door" для клиник**

**Оптимизация GBP:**
- ✅ Полный профиль (все поля заполнены)
- ✅ Правильная категоризация
- ✅ Управление отзывами (respond to all)
- ✅ Локальные страницы услуг
- ✅ NAP consistency (Name, Address, Phone)
- ✅ Photos и virtual tours
- ✅ Posts и updates

**Local SEO тактики:**
- Location pages для каждой клиники
- Local keywords в content
- Local backlinks (partnerships, directories)
- Schema markup (LocalBusiness, MedicalOrganization)

**Источники:** [Medical Marketing Whiz GBP Checklist](https://medicalmarketingwhiz.com/google-business-profile-optimization-the-ultimate-local-seo-checklist-for-medical-practices), [Forbes Local SEO Guide](https://www.forbes.com/councils/forbesagencycouncil/2023/11/16/local-seo-a-guide-for-healthcare-practices)

---

## Pattern Extraction & Meta-Synthesis

### Growth Laws — эмпирические паттерны роста

**Что такое Growth Law:**
- Структурный паттерн, повторяющийся у 3+ конкурентов
- Эмпирически подтверждённый
- Имеет причинно-следственную связь с ростом

**Методология Ehrenberg-Bass:**
- Penetration drivers (что увеличивает проникновение)
- Loyalty/usage rhythms (паттерны использования)
- Double Jeopardy Law (меньшие бренды имеют меньше клиентов И меньшую лояльность)

**Источник:** [Ehrenberg-Bass Laws of Growth](https://marketingscience.info/learn-with-us/commercial-research/laws-of-growth-analysis)

**Примеры Growth Laws в медицинском маркетинге:**

1. **Trust-First Adoption Law**
   - Паттерн: Клиники с высоким рейтингом (>4.5★) растут на 2-3x быстрее
   - Механика: Social proof → SEO boost → Organic traffic → New patients
   - Prevalence: 8/10 топовых клиник
   - Evidence: [E] SimilarWeb data + Google Reviews correlation

2. **Local Dominance Law**
   - Паттерн: Доминирование в локальном поиске = 60-80% новых пациентов
   - Механика: GBP optimization → Local pack → High-intent traffic
   - Prevalence: 9/10 успешных клиник
   - Evidence: [E] BrightLocal studies + case data

3. **Telehealth Wedge Law**
   - Паттерн: Telehealth как initial wedge → 40% faster patient acquisition
   - Механика: Low friction → Fast activation → Retention → In-person upsell
   - Prevalence: 6/10 fast-growing clinics (post-COVID)
   - Evidence: [I] Multiple case studies + growth data

### Sales Laws — паттерны продаж

**Что такое Sales Law:**
- Повторяющийся паттерн в sales cycle
- Подтверждён у 3+ конкурентов
- Влияет на conversion или deal velocity

**Примеры Sales Laws в медицинском B2B:**

1. **Multi-Stakeholder Committee Law**
   - Паттерн: Healthcare B2B требует 5-7 stakeholders для решения
   - Роли: Decision maker, Champion, Blocker, Influencer, User
   - Impact: Игнорирование любой роли → 70% вероятность провала
   - Evidence: [E] Gartner B2B buying research + win-loss data

2. **POC-to-Contract Law**
   - Паттерн: Time-boxed POC (4-8 недель) → 3x выше conversion vs open-ended
   - Механика: Clear success criteria → Urgency → Decision
   - Prevalence: 7/10 успешных vendors
   - Evidence: [E] Sales cycle data + LinkedIn posts

3. **Compliance-First Objection Law**
   - Паттерн: Compliance/security — первое возражение в 80% deals
   - Механика: HIPAA, data security, BAA → Blocker activation
   - Solution: Proactive compliance package → 50% faster close
   - Evidence: [E] Win-loss interviews + sales call analysis

**Источник:** [New Breed Revenue](https://www.newbreedrevenue.com/blog/buying-roles-in-the-sales-process)

### Archetypes — кластеризация конкурентов

**Что такое Archetype:**
- Кластер компаний с похожими growth mechanics
- Общий wedge, GTM, pricing model
- Помогает понять "семейства" стратегий

**Методология кластеризации:**

1. **Собрать метрики:**
   - Traffic sources (organic/paid/referral)
   - Reviews volume/rating
   - POC structure
   - Pricing model
   - Integration depth (EHR, insurance)

2. **Нормализовать данные:**
   - Z-score normalization
   - Handle missing values
   - Weight by evidence quality

3. **Кластеризовать:**
   - K-means (3-5 кластеров)
   - Hierarchical clustering
   - Validate with silhouette score

**Примеры Archetypes в медицинском маркетинге:**

**Archetype 1: Trust-First Incumbents**
- **Wedge:** Многолетняя клиническая репутация
- **GTM:** Word-of-mouth + local SEO
- **Pricing:** Premium (20-30% выше рынка)
- **Expansion:** Referrals + cross-sell services
- **Примеры:** Established multi-specialty clinics
- **Transferability:** Low (требует years of reputation building)

**Archetype 2: Channel-Led Scalers**
- **Wedge:** Performance marketing + digital acquisition
- **GTM:** Paid search + social ads + retargeting
- **Pricing:** Competitive (market rate)
- **Expansion:** Upsell premium plans + telehealth
- **Примеры:** Digital-first clinics, telehealth platforms
- **Transferability:** High (replicable playbook)

**Archetype 3: Partnered Integrators**
- **Wedge:** EHR/insurance integrations
- **GTM:** B2B partnerships + channel sales
- **Pricing:** Enterprise contracts (high ACV)
- **Expansion:** Platform expansion + API ecosystem
- **Примеры:** Healthcare IT vendors, practice management software
- **Transferability:** Medium (requires tech capability)

**Archetype 4: Niche Clinical Specialists**
- **Wedge:** Узкая клиническая экспертиза (e.g., fertility, oncology)
- **GTM:** Thought leadership + physician referrals
- **Pricing:** Premium (specialized care)
- **Expansion:** Geographic expansion + research partnerships
- **Примеры:** Specialty centers, academic medical centers
- **Transferability:** Low (requires clinical expertise)

**Источник:** [Semrush Competitive Matrix](https://www.semrush.com/blog/competitive-matrix)

### Pattern Matrix — competitor × pattern

**Структура матрицы:**

| Competitor | Local GBP Opt | Free Triage | 1-Week POC | Telehealth First | Insurer Partnerships | Evidence Quality |
|------------|---------------|-------------|------------|------------------|---------------------|------------------|
| Clinic A   | ✅ Confirmed   | ✅ Confirmed | ❌ Absent   | ✅ Confirmed      | ✅ Confirmed         | High (E)         |
| Clinic B   | ✅ Confirmed   | ❌ Absent    | ✅ Confirmed | ❌ Absent         | ⚠️ Partial          | Medium (I)       |
| Clinic C   | ⚠️ Partial    | ✅ Confirmed | ❌ Absent   | ✅ Confirmed      | ❌ Absent            | High (E)         |

**Легенда:**
- ✅ Confirmed — паттерн подтверждён (E sources)
- ⚠️ Partial — частичное использование (I inference)
- ❌ Absent — паттерн отсутствует
- ❓ Unknown — недостаточно данных

**Prevalence Count:**
```
Pattern Prevalence = (Confirmed + Partial × 0.5) / Total Competitors

Пример: Local GBP Opt = (2 + 1×0.5) / 3 = 83% prevalence
```

**Weighted Evidence Score:**
```
Evidence Score = Σ(E_count × 3 + Secondary × 2 + Tertiary × 1) / Total_claims

Пример: Clinic A = (5×3 + 2×2 + 1×1) / 8 = 2.5 (High quality)
```

**Использование матрицы:**
- Быстро увидеть распространённость паттерна
- Связать паттерны с outcomes (growth %, reviews uplift)
- Приоритизировать паттерны для копирования

**Источник:** [PredikData CI Use Cases](https://predikdata.com/competitive-intelligence-use-cases-with-data-analytics-and-relationship-data)

### Cross-Company Insights

**Что такое Cross-Insight:**
- Паттерн, выявленный при сравнении конкурентов
- Может не быть универсальным законом
- Но стратегически важен

**Примеры Cross-Insights:**

**Insight 1: Telehealth + Local Hybrid**
- **Паттерн:** Клиники с telehealth + physical locations растут на 2x быстрее
- **Механика:** Telehealth = low friction acquisition → In-person = high LTV
- **Evidence:** [E] 4/5 fast-growing clinics используют hybrid model
- **Confidence:** High
- **Implication:** Hybrid model > pure telehealth or pure physical

**Insight 2: Review Response Rate → Conversion**
- **Паттерн:** Клиники, отвечающие на >80% отзывов, имеют на 25% выше conversion
- **Механика:** Response = engagement signal → Trust → Booking
- **Evidence:** [I] Correlation analysis (SimilarWeb + Google Reviews)
- **Confidence:** Medium
- **Implication:** Review management = growth lever

**Insight 3: Compliance Package → Deal Velocity**
- **Паттерн:** Proactive compliance package сокращает sales cycle на 30-40%
- **Механика:** Pre-empts blocker objections → Faster legal/IT approval
- **Evidence:** [E] Win-loss interviews + sales cycle data
- **Confidence:** High
- **Implication:** Compliance = competitive advantage, not just requirement

---

## Transferability Analysis Framework

### Критерии оценки (Copy / Adapt / Ignore)

**4-Factor Assessment:**

**1. Fit (Contextual Relevance)**
- Соответствует ли паттерн нашему сегменту?
- Подходит ли для нашего региона?
- Совместим ли с нашей регуляторикой?

**2. Capability (Operational Ability)**
- Есть ли у нас люди для реализации?
- Есть ли технологии?
- Достаточно ли бюджета?

**3. Defensibility (Competitive Moat)**
- Насколько легко конкуренты скопируют это у нас?
- Создаёт ли это switching costs?
- Есть ли network effects?

**4. Legal/Ethical Boundary**
- Не нарушает ли HIPAA/GDPR?
- Этично ли это?
- Соответствует ли местным законам?

**Scoring Matrix:**

| Pattern | Fit | Capability | Defensibility | Legal | Total | Decision |
|---------|-----|------------|---------------|-------|-------|----------|
| Local GBP Opt | 5 | 4 | 3 | 5 | 17/20 | ✅ Copy |
| Telehealth First | 4 | 2 | 4 | 5 | 15/20 | ⚠️ Adapt |
| EHR Integration | 5 | 1 | 5 | 5 | 16/20 | ❌ Ignore (no capability) |

**Decision Rules:**
- **17-20:** Copy (high priority)
- **13-16:** Adapt (modify for context)
- **9-12:** Consider (pilot first)
- **<9:** Ignore (not viable)

### Preconditions для успешного копирования

**Organizational Preconditions:**
- ✅ Executive buy-in (C-level sponsor)
- ✅ Dedicated owner (single-threaded leader)
- ✅ Cross-functional team (marketing, ops, compliance)
- ✅ Budget allocated (not "find budget later")

**Measurement Preconditions:**
- ✅ Clear success metrics (KPIs defined)
- ✅ Baseline established (before state measured)
- ✅ Measurement plan (how, when, who)
- ✅ Decision criteria (what = success/failure)

**Capability Preconditions:**
- ✅ Minimum viable tech stack
- ✅ Trained people (or training plan)
- ✅ Process documentation (SOPs)
- ✅ Governance (compliance/legal reviewed)

**Pilot Design:**
- ✅ Time-boxed (4-8 weeks)
- ✅ Success criteria (measurable outcomes)
- ✅ Go/No-Go decision point
- ✅ Rollback plan (if fails)

### Boundary Conditions (когда НЕ работает)

**Regulatory Boundaries:**
- Паттерн нарушает HIPAA/GDPR
- Фарма-реклама ограничена
- Требует лицензии, которой нет

**Asset Boundaries:**
- Паттерн требует уникальный asset (data, partnership)
- Нет доступа к критическому ресурсу
- Невозможно воспроизвести инфраструктуру

**Trust Capital Boundaries:**
- Паттерн опирается на многолетнюю репутацию
- Требует клиническую экспертизу, которой нет
- Зависит от brand equity, который нельзя скопировать

**Market Structure Boundaries:**
- Паттерн работает только в определённом сегменте
- Зависит от локальной специфики (US vs Russia)
- Требует market maturity, которой нет

### Sequencing Roadmap — фазы внедрения

**Phase 1: Discover (2-5 дней/конкурент)**
- Заполнение pattern matrix
- Evidence scoring
- Prevalence calculation
- Initial transferability assessment

**Phase 2: Prioritise (1 день)**
- ICE scoring (Impact × Confidence × Ease)
- Compliance review
- Capability gap analysis
- Top 3 patterns selection

**Phase 3: Pilot (4-8 недель)**
- Time-boxed experiment
- Clear success criteria
- Weekly check-ins
- Data collection

**Phase 4: Evaluate (2 недели)**
- Metrics vs baseline
- Qualitative feedback
- Cost-benefit analysis
- Decision: Scale / Adapt / Kill

**Phase 5: Scale (ongoing)**
- Integration в операционную модель
- Training и SOPs
- Monitoring и optimization
- Continuous improvement

**ICE Scoring Formula:**
```
ICE Score = (Impact × Confidence × Ease) / 3

Impact: 1-10 (expected business impact)
Confidence: 1-10 (evidence quality)
Ease: 1-10 (implementation difficulty, inverted)

Пример:
Local GBP Opt: (8 × 9 × 7) / 3 = 8.0 (High priority)
EHR Integration: (9 × 8 × 2) / 3 = 6.3 (Medium priority)
```

### Risk Assessment — что может пойти не так

**Regulatory Risks:**
- ❌ Неграмотное использование patient stories → штрафы HIPAA
- ❌ Fake reviews → FTC penalties
- ❌ Неподтверждённые клинические утверждения → FDA warning

**Источники:** [HHS HIPAA Guidance](https://www.hhs.gov/hipaa/for-professionals/privacy/guidance/marketing/index.html), [FTC Fake Reviews](https://healthcaresuccess.com/blog/breaking-down-the-new-ftc-ruling-on-fake-reviews-testimonials.html)

**Brand Risks:**
- ❌ Пассивное копирование без адаптации → brand dilution
- ❌ Несоответствие brand voice → confusion
- ❌ Over-promising → patient dissatisfaction

**Operational Risks:**
- ❌ POC растягивается → resource drain
- ❌ Клиники не справляются с onboarding → churn
- ❌ Недостаточная подготовка персонала → poor execution

**Data Risks:**
- ❌ Data leakage при автоматизации → compliance violation
- ❌ PHI exposure → HIPAA breach
- ❌ Inadequate BAA → legal liability

**Mitigation Strategies:**
- ✅ Legal/compliance review BEFORE pilot
- ✅ Training и SOPs
- ✅ Phased rollout (не all-in сразу)
- ✅ Monitoring и alerts
- ✅ Rollback plan

---

## API Integration для Competitive Intelligence

### SimilarWeb API

**Что даёт:**
- Traffic volume (visits, unique visitors)
- Traffic sources (organic, paid, social, referral, direct)
- Engagement metrics (bounce rate, pages/visit, avg duration)
- Top referring sites
- Top keywords (organic + paid)
- Historical data (до 37 месяцев)

**Use Cases:**
- Channel mix analysis (где конкурент получает трафик)
- Trend signals (растёт/падает трафик)
- Benchmark traffic против своего сайта

**Rate Limits:**
- Зависит от плана (обычно 100-1000 calls/day)

**Cost Optimization:**
- Cache daily/weekly (traffic не меняется каждый час)
- Batch requests (multiple domains в одном call)
- Use summary endpoints (не детальные breakdowns)

**Источник:** [SimilarWeb API Docs](https://developers.similarweb.com/reference/bounce-rate)

### Ahrefs API

**Что даёт:**
- Backlink profile (referring domains, backlinks count)
- Organic keywords (rankings, traffic estimates)
- Domain Rating (DR) — authority metric
- Top pages (by organic traffic)
- Competitor overlap (shared keywords)
- Historical data

**Use Cases:**
- SEO authority comparison (DR vs competitors)
- Backlink gap analysis (где у них есть, у нас нет)
- Keyword opportunities (их rankings, наши gaps)

**Rate Limits:**
- 500 requests/hour (standard plan)

**Cost Optimization:**
- Cache DR и backlink counts (меняются медленно)
- Fetch only deltas (new backlinks since last check)
- Use batch endpoints

**Источник:** [Ahrefs API Docs](https://docs.ahrefs.com/en/api/reference/site-explorer/get-domain-rating)

### SEMrush API

**Что даёт:**
- Paid keywords (ad copy, CPC, position)
- Organic keywords (rankings, volume, difficulty)
- Competitor discovery (кто конкурирует в поиске)
- Ad history (креативы, landing pages)
- Backlinks (альтернатива Ahrefs)

**Use Cases:**
- PPC spend estimation (keywords × CPC)
- Ad creative analysis (что работает)
- Keyword gap (их keywords, наши gaps)

**Rate Limits:**
- 10,000 API units/day (varies by endpoint)

**Cost Optimization:**
- Cache keyword data (обновлять weekly)
- Use domain overview (не детальные reports)
- Batch competitor discovery

**Источник:** [SEMrush API Overview](https://developer.semrush.com/api/introduction/semrush-api-overview)

### Crunchbase API

**Что даёт:**
- Firmographics (company size, location, founded date)
- Funding data (rounds, amounts, investors)
- Team size estimates
- Key people (executives, board)
- Acquisitions и partnerships

**Use Cases:**
- Runway estimation (funding / burn rate)
- Investment activity tracking
- Team growth signals (hiring velocity)

**Rate Limits:**
- 200 calls/minute (standard)

**Cost Optimization:**
- Cache firmographics (меняются редко)
- Fetch only updates (не full profiles каждый раз)
- Use search endpoint (не individual lookups)

**Источник:** [Crunchbase API Docs](https://data.crunchbase.com/docs/api-packages-overview)

### HealthGrades / Zocdoc APIs

**Что даёт:**
- Physician ratings и reviews
- Patient satisfaction scores
- Appointment availability
- Insurance acceptance
- Specialties и credentials

**Ограничения:**
- Public API ограничен
- Часто требуется partnership
- Альтернатива: аккуратный парсинг с compliance

**Use Cases:**
- Reputation benchmarking
- Review sentiment analysis
- Availability comparison

**Cost Optimization:**
- Aggregate через reputation platforms
- Use partners (Reputation.com, rater8)
- Scrape ethically (respect robots.txt, rate limits)

**Источник:** [HealthGrades](https://www.healthgrades.com)

### Rate Limiting & Caching Best Practices

**Rate Limiting:**
- Implement exponential backoff (1s → 2s → 4s → 8s)
- Retry logic с max attempts (3-5)
- Queue requests (не burst)
- Monitor rate limit headers

**Caching Strategy:**

| Data Type | TTL | Rationale |
|-----------|-----|-----------|
| Traffic data | 24h | Меняется daily |
| Backlinks | 7d | Растут медленно |
| Keywords | 7d | Rankings стабильны |
| Firmographics | 30d | Редко меняются |
| Reviews | 24h | Новые каждый день |

**Cost Control:**
```
Cost per Competitor = Σ(API_calls × Cost_per_call)

Target: <$5 per competitor

Tactics:
- Cache aggressively
- Fetch only deltas
- Use summary endpoints
- Batch requests
```

---

## Company Synthesis Memo — шаблон

### Page 1: Executive Summary (≤1 page)

**3-5 ключевых выводов:**
1. [Главный инсайт о growth machine]
2. [Ключевой паттерн для копирования]
3. [Уникальное преимущество конкурента]
4. [Риск или fragility]
5. [Recommended action]

**Целевая аудитория:** C-level (CEO, CMO, CFO)

**Писать последним** (после всех секций)

### Section A: Company Snapshot

**Обязательные поля:**
- Mission и позиционирование
- Initial wedge (с чего начали)
- GTM стратегия (каналы, тактики)
- Product lines (основные услуги/продукты)
- Target segments (кто клиенты)
- Public metrics (funding, estimated ARR, team size)
- Evidence quality score (%E / %I / %UV)

**Пример:**
```markdown
## Company Snapshot: Clinic X

**Mission:** "Accessible specialty care for underserved communities"

**Initial Wedge:** Telehealth-first dermatology for rural patients [E]
  - Source: Founder interview, Healthcare Podcast (2024-03-15)

**GTM Strategy:**
  - Primary: Paid search (Google Ads) [E]
  - Secondary: Physician referrals [I]
  - Tertiary: Content marketing [E]

**Target Segments:**
  - Rural patients (>50 miles from specialist) [E]
  - Insured (accept major insurers) [E]
  - Age 25-65 (primary demographic) [I]

**Public Metrics:**
  - Funding: $15M Series A (2023) [E]
  - Estimated ARR: $8-12M [UV]
  - Team: ~80 employees [E]

**Evidence Quality:** 72% sourced (E), 20% inference (I), 8% unverified (UV)
```

### Section B: Core Motion Analysis

**Структура:**
1. **Acquisition:** Каналы и тактики
2. **Conversion:** Landing pages, booking flow
3. **Activation:** First consult, time-to-value
4. **Retention:** Follow-ups, NRR
5. **Expansion:** Cross-sell, upsell

**Включить:**
- Pattern matrix excerpt (какие паттерны используют)
- Archetype classification (к какому кластеру относятся)

### Section C: Why They Won

**5 факторов успеха:**

1. **Timing**
   - Почему сейчас? (market readiness)
   - Regulatory changes? (telehealth reimbursement)
   - Technology enablers? (video quality, EHR APIs)

2. **Wedge**
   - Почему wedge сработал?
   - Кто были early adopters?
   - Как wedge защищён?

3. **Product**
   - Что уникально в продукте?
   - Какие features критичны?
   - Как product evolves?

4. **Distribution**
   - Какие каналы работают?
   - Почему эти каналы?
   - Как масштабируют distribution?

5. **Trust**
   - Как построили trust?
   - Сертификаты, кейсы, отзывы?
   - Reputation management?

**Каждый фактор с 1-2 свидетельствами (links + timestamps)**

**Источники:** [Contify CI Analysis](https://www.contify.com/resources/blog/competitive-intelligence-analysis), [Sedulo CI Report](https://sedulogroup.com/competitive-intelligence-report)

### Section D: Unit Economics & Sales Cycle

**Unit Economics:**
```markdown
## Unit Economics (Estimates)

**ACV:** $500-800 per patient/year [UV]
  - Basis: 4-6 visits × $100-150/visit
  - Source: Pricing page analysis + insurance reimbursement rates

**CAC:** $150-200 [I]
  - Basis: Paid search CPC $5-8 × 25-30 clicks/conversion
  - Source: SEMrush ad data + industry benchmarks

**LTV:** $1,500-2,400 [I]
  - Basis: ACV × 3-year retention
  - Assumption: 70% retention rate (industry avg)

**Payback:** 3-4 months [I]
  - Calculation: CAC / (ACV × gross margin 60%)

**LTV:CAC:** 7.5-12:1 [I]
  - Strong unit economics (target >3:1)
```

**Sales Cycle Map:**
```markdown
## Sales Cycle (B2C)

**Awareness → Booking:** 7-14 days [I]
  - Google search → Landing page → Booking form
  - Drop-off: 60% at landing page, 40% at booking form

**Booking → First Consult:** 1-3 days [E]
  - Source: Website "Next available: 1-3 days"

**First Consult → Follow-up:** 30-60 days [I]
  - Basis: Typical dermatology follow-up cadence

**Decision Makers (B2C):**
  - Patient (self-directed) [E]
  - Insurance (coverage check) [E]
```

### Section E: Risks & Fragilities

**Internal Vulnerabilities:**
- Зависимость от одного канала (paid search = 70% traffic) [I]
- Physician retention (high turnover risk) [OQ]
- Technology debt (legacy telehealth platform) [UV]

**External Threats:**
- Regulatory changes (telehealth reimbursement cuts) [H]
- Competitive pressure (new entrants with better UX) [I]
- Insurance negotiations (rate cuts) [H]

**Mitigation Suggestions:**
- Diversify acquisition channels (SEO, referrals)
- Improve physician retention (equity, culture)
- Modernize tech stack (migrate to modern platform)

### Appendices

**Appendix A: Raw Sources**
- Links to all [E] sources
- Timestamps и access dates
- Archived copies (PDFs, screenshots)

**Appendix B: Pattern Matrix CSV**
- Full competitor × pattern matrix
- Evidence scores
- Prevalence calculations

**Appendix C: Methodology & Assumptions**
- How estimates were derived
- Confidence levels
- Known limitations

---


## Benchmark Quality Gates

### Company Memo Completion Criteria

**Minimum Requirements:**
- Growth machine explained (acquisition → conversion → retention → expansion)
- Initial wedge identified with evidence
- Target buyer/user persona defined
- Unit economics estimated (ACV, CAC, LTV, payback)
- Core motion articulated (how they actually win)
- Evidence separated: [E] vs [I] vs [UV]
- Risks and fragilities identified

**Quality Checklist:**
- [ ] Growth machine: All 4 stages documented
- [ ] Initial wedge: Specific starting point identified
- [ ] Target buyer: Decision maker + end user + blocker roles
- [ ] Unit economics: At least 2 of 4 metrics estimated
- [ ] Core motion: 1-2 sentence explanation of competitive advantage
- [ ] Evidence quality: >50% [E] sourced claims
- [ ] Risks: At least 3 fragilities identified

### Meta-Synthesis Completion Criteria

**Growth Laws:**
- Minimum 3 laws identified
- Each law observed in 3+ companies
- Prevalence estimated (% of companies using)
- Preconditions documented
- Boundary conditions identified

**Sales Laws:**
- Minimum 3 laws identified
- Each law observed in 3+ companies
- Sales cycle patterns documented
- Decision maker patterns identified

**Archetypes:**
- Minimum 2 archetypes defined
- Each archetype has 2+ member companies
- Core characteristics documented
- Growth mechanics explained

**Pattern Matrix:**
- All companies mapped to patterns
- Prevalence calculated for each pattern
- Transferability assessed (Copy/Adapt/Ignore)

### Evidence Quality Assessment

**Source Quality Tiers:**

**Tier 1 (Primary/Operator):**
- Founder interviews (podcasts, blog posts)
- Operator posts (LinkedIn, Twitter, blog)
- Company case studies (with metrics)
- Product demos (with pricing)
- Customer testimonials (with specifics)

**Tier 2 (Secondary):**
- Industry reports (Gartner, Forrester)
- News articles (TechCrunch, Forbes)
- Conference talks (with slides)
- Webinars (with recordings)

**Tier 3 (Tertiary):**
- Wikipedia entries
- Generic blog posts
- Social media mentions
- Unverified claims

**Evidence Quality Score:**
```
Evidence Quality = (Tier1_claims × 3 + Tier2_claims × 2 + Tier3_claims × 1) / Total_claims
```

**Target:** >2.0 (majority Tier 1-2 sources)

### Prevalence Estimation

**Pattern Prevalence:**
```
Prevalence = Companies_using_pattern / Total_companies_analyzed
```

**Confidence Levels:**
- High confidence: 5+ companies, >60% prevalence
- Medium confidence: 3-4 companies, 40-60% prevalence
- Low confidence: 2 companies, <40% prevalence

**Transferability Criteria:**

**DO COPY (High transferability):**
- Prevalence >60%
- Preconditions met
- No unique advantages required
- Low implementation risk
- Clear ROI

**ADAPT (Medium transferability):**
- Prevalence 40-60%
- Some preconditions met
- Requires customization
- Medium implementation risk
- Uncertain ROI

**DON'T COPY (Low transferability):**
- Prevalence <40%
- Preconditions not met
- Requires unique advantages
- High implementation risk
- Negative ROI

## Medical Marketing CI Specifics

### Trust Architecture in Healthcare

**Trust Signals (Priority Order):**

1. **Clinical Outcomes (Highest Trust):**
   - Before/after photos (with consent)
   - Success rates (with methodology)
   - Patient testimonials (video > text)
   - Case studies (detailed, with metrics)
   - Clinical trial results (if applicable)

2. **Professional Credentials:**
   - Board certifications
   - Years of experience
   - Specialized training
   - Academic affiliations
   - Professional memberships

3. **Third-Party Validation:**
   - HealthGrades ratings (4.5+ stars)
   - Zocdoc reviews (4.0+ stars)
   - Google My Business reviews (4.5+ stars)
   - Industry awards
   - Media mentions

4. **Facility Quality:**
   - Accreditations (JCI, ISO)
   - Technology/equipment
   - Facility photos
   - Safety protocols
   - Hygiene standards

**Trust Architecture Reverse-Engineering:**

For each competitor, document:
- Primary trust signal (what they lead with)
- Trust signal hierarchy (order of presentation)
- Evidence quality (photos, videos, testimonials)
- Third-party validation sources
- Trust gaps (what's missing)

### HIPAA Compliance Constraints

**What You CAN'T Do:**
- Use patient names without consent
- Show identifiable photos without consent
- Share medical records
- Disclose treatment details without consent
- Track patients without consent

**What You CAN Do:**
- Aggregate statistics (e.g., "95% success rate")
- De-identified case studies
- Testimonials with explicit consent
- Before/after photos with consent
- General treatment information

**CI Implications:**
- Competitor patient data is protected
- Can't scrape patient reviews for analysis
- Can't track individual patient journeys
- Must rely on public, consented data

### Patient Journey Mapping

**Awareness Stage:**
- Symptom search (Google, Yandex)
- Educational content (blogs, videos)
- Social media (Facebook groups, Instagram)
- Word of mouth (friends, family)

**Consideration Stage:**
- Clinic comparison (HealthGrades, Zocdoc)
- Review reading (Google, Yandex Maps)
- Website research (services, pricing)
- Social proof (testimonials, case studies)

**Decision Stage:**
- Consultation booking (online form, phone)
- Facility visit (in-person consultation)
- Treatment plan review
- Pricing negotiation

**Retention Stage:**
- Follow-up appointments
- Post-treatment care
- Loyalty programs
- Referral incentives

**CI Focus:**
- How competitors attract at each stage
- What content they use (blogs, videos, ads)
- What trust signals they emphasize
- What conversion mechanisms they use

### Reputation-First Adoption Patterns

**Medical Marketing Funnel:**
```
Reputation → Trust → Consideration → Decision
```

**Not:**
```
Awareness → Interest → Decision
```

**Key Insight:** Patients don't buy on features or price. They buy on trust and reputation.

**CI Implications:**
- Analyze reputation-building tactics
- Identify trust signal hierarchy
- Map referral networks
- Track review management strategies

### Local SEO & Google My Business

**Critical Ranking Factors:**
1. **Proximity** (distance to searcher)
2. **Relevance** (keyword match)
3. **Prominence** (reviews, ratings, citations)

**GMB Optimization Tactics:**
- Complete profile (hours, services, photos)
- Regular posts (updates, offers, events)
- Review generation (ask patients, respond to all)
- Q&A management (answer common questions)
- Booking integration (online appointments)

**CI Analysis:**
- Competitor GMB profiles (completeness, activity)
- Review volume and velocity (new reviews/month)
- Review response rate and quality
- Post frequency and engagement
- Booking integration (yes/no)

**Local Pack Ranking:**
```
Local Pack Score = Proximity × Relevance × Prominence
```

**Prominence Factors:**
- Review count (more is better)
- Review rating (4.5+ stars)
- Review velocity (consistent new reviews)
- Citation consistency (NAP across web)
- Website authority (backlinks, DR)

## Implementation Roadmap

### Phase 1: Source Harvest (Weeks 1-2)

**Week 1: Infrastructure Setup**
- Set up evidence archive structure
- Configure API integrations (SimilarWeb, Ahrefs, SEMrush)
- Create source tracking system
- Define evidence labeling workflow

**Week 2: Source Collection**
- Identify 10-20 target competitors
- Collect primary sources (founder interviews, operator posts)
- Collect secondary sources (industry reports, news)
- Collect tertiary sources (Wikipedia, blogs)
- Label all sources with evidence tags

**Deliverables:**
- Evidence archive with 50+ sources per competitor
- Source quality distribution (Tier 1/2/3)
- Evidence labeling complete ([E], [I], [UV], [OQ])

### Phase 2: Company Synthesis (Weeks 3-4)

**Week 3: Growth Machine Analysis**
- Extract initial wedge for each competitor
- Map acquisition → conversion → retention → expansion
- Estimate unit economics (ACV, CAC, LTV, payback)
- Identify target buyer/user personas

**Week 4: Competitive Advantage Analysis**
- Articulate core motion (how they win)
- Identify competitive moats
- Document risks and fragilities
- Create company synthesis memos

**Deliverables:**
- 10-20 company synthesis memos
- Growth machine diagrams
- Unit economics tables
- Competitive advantage analysis

### Phase 3: Meta-Synthesis (Weeks 5-6)

**Week 5: Pattern Extraction**
- Identify growth laws (3+ companies)
- Identify sales laws (3+ companies)
- Define archetypes (2+ clusters)
- Create pattern matrix (competitor × pattern)

**Week 6: Cross-Company Insights**
- Calculate pattern prevalence
- Identify universal vs niche patterns
- Document preconditions and boundary conditions
- Create meta-synthesis report

**Deliverables:**
- Growth laws document (5-10 laws)
- Sales laws document (5-10 laws)
- Archetypes document (3-5 archetypes)
- Pattern matrix (competitor × pattern table)

### Phase 4: Application Layer (Weeks 7-8)

**Week 7: Transferability Analysis**
- Assess each pattern (Copy/Adapt/Ignore)
- Document preconditions for copying
- Identify boundary conditions
- Estimate implementation risk

**Week 8: Sequencing & Prioritization**
- Create sequencing roadmap (what to implement first)
- Prioritize patterns (ICE scoring)
- Create do-copy/don't-copy recommendations
- Finalize benchmark report

**Deliverables:**
- Do-copy/don't-copy document
- Sequencing roadmap
- Priority matrix (ICE scores)
- Final benchmark report

## Cost Estimation

### API Costs (Per Competitor Analysis)

**SimilarWeb API:**
- Traffic data: $0.10 per domain
- Engagement metrics: $0.05 per domain
- Traffic sources: $0.10 per domain
- **Total:** ~$0.25 per competitor

**Ahrefs API:**
- Backlinks: $0.15 per domain
- Organic keywords: $0.10 per domain
- Domain Rating: $0.05 per domain
- Referring domains: $0.10 per domain
- **Total:** ~$0.40 per competitor

**SEMrush API:**
- Paid keywords: $0.10 per domain
- Ad copy: $0.05 per domain
- Competitor discovery: $0.10 per domain
- **Total:** ~$0.25 per competitor

**Crunchbase API:**
- Company data: $0.05 per company
- Funding data: $0.05 per company
- **Total:** ~$0.10 per competitor

**HealthGrades/Zocdoc API:**
- Reviews: $0.10 per provider
- Ratings: $0.05 per provider
- **Total:** ~$0.15 per competitor

**Total API Cost Per Competitor:** ~$1.15

**For 10 Competitors:** ~$11.50  
**For 20 Competitors:** ~$23.00

### Time Estimation

**Per Competitor:**
- Source harvest: 2-3 hours
- Company synthesis: 3-4 hours
- **Total:** 5-7 hours per competitor

**For 10 Competitors:**
- Source harvest: 20-30 hours
- Company synthesis: 30-40 hours
- Meta-synthesis: 10-15 hours
- Application layer: 10-15 hours
- **Total:** 70-100 hours (~2-3 weeks full-time)

**For 20 Competitors:**
- Source harvest: 40-60 hours
- Company synthesis: 60-80 hours
- Meta-synthesis: 15-20 hours
- Application layer: 15-20 hours
- **Total:** 130-180 hours (~4-6 weeks full-time)

## Success Metrics

### Quantitative Metrics

**Coverage:**
- Number of competitors analyzed (target: 10-20)
- Number of sources per competitor (target: 50+)
- Evidence quality score (target: >2.0)

**Pattern Extraction:**
- Number of growth laws identified (target: 5-10)
- Number of sales laws identified (target: 5-10)
- Number of archetypes defined (target: 3-5)

**Evidence Quality:**
- % sourced claims ([E]) (target: >70%)
- % inference claims ([I]) (target: <20%)
- % unverified claims ([UV]) (target: <10%)

**Transferability:**
- % patterns marked "Copy" (target: >50%)
- % patterns marked "Adapt" (target: 30-40%)
- % patterns marked "Ignore" (target: <20%)

### Qualitative Metrics

**Insight Quality:**
- Are growth laws actionable?
- Are sales laws specific?
- Are archetypes distinct?
- Are preconditions clear?

**Benchmark Utility:**
- Can clients understand the report?
- Can clients implement recommendations?
- Does the report answer "why they won"?
- Does the report identify transferable patterns?

**ROI:**
- Time to insight (target: <2 hours from request)
- Cost per competitor (target: <$5)
- Implementation success rate (target: >50% of "Copy" patterns)

## Appendix A: Evidence Labeling Examples

### [E] Sourced Evidence

**Example 1:**
> "We started with dentists in Moscow because they had the highest willingness to pay for marketing services." [E: Founder interview, TechCrunch, 2023-05-15]

**Example 2:**
> "Our average customer acquisition cost is $150, and lifetime value is $2,400." [E: Company case study, website, 2024-01-10]

### [I] Inference

**Example 1:**
> "Based on their pricing page ($500/month) and team size (50 employees), we estimate their annual revenue at $3-5M." [I: Inferred from public data]

**Example 2:**
> "Their focus on video testimonials suggests they prioritize trust-building over feature comparison." [I: Inferred from website analysis]

### [UV] Unverified

**Example 1:**
> "Industry sources suggest they have 500+ clients, but this is not confirmed." [UV: Unverified estimate]

**Example 2:**
> "They may be using AI for content generation, but no official statement exists." [UV: Speculation]

### [OQ] Open Question

**Example 1:**
> "How do they handle patient consent for testimonials?" [OQ: Needs investigation]

**Example 2:**
> "What is their customer churn rate?" [OQ: Data not available]

### [H] Hypothesis

**Example 1:**
> "We hypothesize that their growth is driven by referral networks, not paid ads." [H: Testable hypothesis]

**Example 2:**
> "Their low CAC suggests a strong organic presence, possibly through SEO." [H: Requires validation]

## Appendix B: Pattern Matrix Template

| Competitor | Initial Wedge | Acquisition | Conversion | Retention | Expansion | Trust Signal | Local SEO | Referral Program |
|------------|---------------|-------------|------------|-----------|-----------|--------------|-----------|------------------|
| Competitor A | Dentists Moscow | SEO + GMB | Free consultation | Loyalty discount | Upsell services | Video testimonials | 4.8★ GMB | 10% referral bonus |
| Competitor B | Plastic surgery | Instagram ads | Virtual consultation | Follow-up care | Package deals | Before/after photos | 4.5★ GMB | Free service for 3 referrals |
| Competitor C | General practice | Word of mouth | In-person visit | Subscription model | Family plans | Doctor credentials | 4.7★ GMB | No program |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |

**Prevalence Calculation:**
- Initial Wedge (Niche focus): 80% (8/10 competitors)
- Acquisition (SEO + GMB): 70% (7/10 competitors)
- Conversion (Free consultation): 60% (6/10 competitors)
- Retention (Loyalty program): 50% (5/10 competitors)
- Expansion (Upsell services): 70% (7/10 competitors)
- Trust Signal (Video testimonials): 40% (4/10 competitors)
- Local SEO (4.5+ stars): 90% (9/10 competitors)
- Referral Program: 60% (6/10 competitors)

## Appendix C: Company Synthesis Memo Template

```markdown
# [Company Name] - Competitive Intelligence Memo

**Date:** YYYY-MM-DD  
**Analyst:** [Name]  
**Evidence Quality:** [Score/5.0]

## Executive Summary

[2-3 sentences: What they do, how they win, why it matters]

## Company Snapshot

- **Founded:** [Year]
- **Location:** [City, Country]
- **Team Size:** [Number] [E/I/UV]
- **Funding:** [Amount] [E/I/UV]
- **Revenue:** [Estimate] [E/I/UV]
- **Customers:** [Number] [E/I/UV]

## Core Motion

[1-2 sentences: How they actually win in the market]

## Initial Wedge

**What they started with:** [Specific niche/segment]  
**Why it worked:** [Reason]  
**Evidence:** [E: Source]

## Growth Machine

### Acquisition
- **Primary channel:** [Channel] [E/I/UV]
- **CAC:** [Estimate] [E/I/UV]
- **Tactics:** [List]

### Conversion
- **Conversion mechanism:** [Mechanism] [E/I/UV]
- **Conversion rate:** [Estimate] [E/I/UV]
- **Tactics:** [List]

### Retention
- **Retention mechanism:** [Mechanism] [E/I/UV]
- **Churn rate:** [Estimate] [E/I/UV]
- **Tactics:** [List]

### Expansion
- **Expansion mechanism:** [Mechanism] [E/I/UV]
- **Expansion revenue:** [Estimate] [E/I/UV]
- **Tactics:** [List]

## Unit Economics

| Metric | Estimate | Evidence |
|--------|----------|----------|
| ACV | $X,XXX | [E/I/UV] |
| CAC | $XXX | [E/I/UV] |
| LTV | $X,XXX | [E/I/UV] |
| Payback Period | X months | [E/I/UV] |
| Gross Margin | XX% | [E/I/UV] |

## Why They Won

**Factor Analysis:**

| Factor | Weight | Score | Weighted Score |
|--------|--------|-------|----------------|
| Timing | 20% | 8/10 | 1.6 |
| Product | 25% | 7/10 | 1.75 |
| Distribution | 25% | 9/10 | 2.25 |
| Trust | 20% | 8/10 | 1.6 |
| Execution | 10% | 7/10 | 0.7 |
| **Total** | **100%** | - | **7.9/10** |

**Narrative:** [Explain why they won]

## Competitive Moats

1. **[Moat Type]:** [Description] [E/I/UV]
2. **[Moat Type]:** [Description] [E/I/UV]
3. **[Moat Type]:** [Description] [E/I/UV]

## Risks & Fragilities

1. **[Risk]:** [Description] [E/I/UV]
2. **[Risk]:** [Description] [E/I/UV]
3. **[Risk]:** [Description] [E/I/UV]

## Transferable Patterns

| Pattern | Transferability | Preconditions | Risk |
|---------|-----------------|---------------|------|
| [Pattern 1] | Copy | [List] | Low |
| [Pattern 2] | Adapt | [List] | Medium |
| [Pattern 3] | Ignore | [List] | High |

## Sources

### Primary (Tier 1)
- [Source 1] - [Link] - [Date]
- [Source 2] - [Link] - [Date]

### Secondary (Tier 2)
- [Source 1] - [Link] - [Date]
- [Source 2] - [Link] - [Date]

### Tertiary (Tier 3)
- [Source 1] - [Link] - [Date]
- [Source 2] - [Link] - [Date]

## Open Questions

1. [OQ: Question 1]
2. [OQ: Question 2]
3. [OQ: Question 3]
```

---

**End of Report**

**Research Metadata:**
- **Topic:** CI Research Agent (Competitor Intelligence): Reverse-engineering конкурентов в медицинском маркетинге с использованием Industry Benchmark подхода
- **Model:** exa-research
- **Cost:** $0.84
- **Duration:** ~15 minutes
- **Pages:** 126.5
- **Searches:** 41
- **Date:** 2026-05-15

**Next Steps:**
1. Create CI Research Agent specification using this research
2. Archive research in obsidian/deep-research vault
3. Implement CI Research Agent as subagent under SEO Magister
4. Integrate with existing AIM infrastructure (Event Bus, Obsidian, API clients)

