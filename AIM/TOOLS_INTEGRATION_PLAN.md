# План интеграции старых инструментов в AIM Agency

**Дата:** 2026-05-04  
**Статус:** Архитектурный план  
**Цель:** Превратить 5 готовых инструментов в субагентов агентства AIM

---

## 📊 Инвентаризация инструментов

### 1. AI CustDev (Customer Development Platform)

**Что это:**
- Платформа для проведения CustDev интервью с AI-аватарами
- Методология Advanced JTBD (Jobs-To-Be-Done)
- 165+ детальных аватаров с когнитивными биасами
- Генерация Jobs Graph, RAT Analysis, Activating Knowledge

**Технологии:**
- Backend: FastAPI + PostgreSQL + Redis
- Frontend: Next.js 14 + TypeScript
- AI: Claude Opus 4.6 через api.kiro.cheap
- 14 AJTBD вопросов в 6 блоках

**Статус:** ✅ Production Ready (v1.2)

**Ценность для агентства:**
- Глубокое понимание клиентов
- Product-Market Fit для новых продуктов
- Activating Knowledge для маркетинга
- Сегментация по Core Jobs

---

### 2. ROI (Competitive Intelligence System)

**Что это:**
- Две системы конкурентной разведки для российского рынка
- **CI Orchestrator** — универсальный агент (любая ниша, любой город)
- **Trendwatching RU** — анализ рекламных креативов

**Архитектура:**
- 23 специализированных агента
- Hub-and-spoke через оркестратор
- Параллельная обработка в фазе 5
- 16 фаз с gate approval

**Источники данных:**
- WebSearch, WebFetch, Playwright
- VK, Telegram, Яндекс.Карты, 2ГИС
- Flamp, Otzovik, hh.ru, Rusprofile

**Статус:** ✅ Рабочий (активно использовался)

**Ценность для агентства:**
- Полная конкурентная разведка
- Анализ рекламных креативов
- Стратегия отстройки
- Репутационный аудит

---

### 3. YandexDirect (YAD Agent)

**Что это:**
- Multi-agent, multi-account оркестратор для Яндекс.Директ
- Управление множеством аккаунтов с изолированной историей
- Автопилот с расписанием и webhook alerts

**Компоненты:**
- Orchestrator с параллельным выполнением
- 4 специализированных агента: planner, bidding, optimizer, reporter
- Rule engine (if → then)
- Analytics fusion layer (кампании/группы/ключевые слова)
- CRM layer scaffold (опционально)

**Возможности:**
- OAuth + Direct API интеграция
- Автоматическая оптимизация ставок
- Snapshot collection (Direct + Metrica)
- Creative QA (3-stage gate)
- Policy guardrails

**Статус:** ✅ MVP готов

**Ценность для агентства:**
- Автоматизация контекстной рекламы
- Управление множеством клиентов
- Оптимизация бюджетов
- Интеграция с Метрикой

---

### 4. Дзен пулемет GSR (Content Automation)

**Что это:**
- Автоматическая генерация и публикация контента в Telegram
- Система с модерацией и RSS
- Расписание публикаций

**Компоненты:**
- `farm_manager` — планировщик (1 пост/день, окно 8-22)
- `telegram_publisher` — публикация через Telethon
- `rss_builder` — генерация RSS фидов
- `admin_panel` — модерация контента
- `perplexity_client` — генерация через Perplexity

**Режимы:**
- **manual** — генерация автоматическая, публикация после модерации
- **auto** — полностью автоматическая публикация

**Статус:** ✅ Работает на сервере

**Ценность для агентства:**
- Автоматизация контент-маркетинга
- Telegram каналы клиентов
- Модерация перед публикацией
- RSS для интеграций

---

### 5. GEO оптимизатор (SEO Indexation Tool)

**Что это:**
- Инструмент для массовой индексации статей в Яндекс и Google
- Генерация статей по шаблону с SEO-оптимизацией
- Интеграция с Google Search Console и Bing Webmaster

**Стандарты контента:**
- HTML-каркас с SEO мета-тегами
- Размер файла: 25-40KB
- Количество слов: 2000-4000
- Время чтения: 10-20 минут
- 3-5 таблиц с данными
- 2-3 реальных кейса

**Компоненты:**
- Генератор статей по шаблону
- Автоматическая публикация на сервер (SSH/SCP)
- Генерация sitemap.xml
- Отправка на переобход в Вебмастере

**Статус:** ✅ Активно использовался

**Ценность для агентства:**
- SEO-продвижение клиентов
- Массовая генерация контента
- Автоматическая индексация
- Органический трафик

---

## 🏗️ Архитектура интеграции

### Текущая структура meAI/AIM

```
!meAI/                          # Command Center
├── src/meai/                   # Framework (базовые классы)
│   ├── core/                   # Architect, Orchestrator, Decision Maker
│   ├── agents/                 # Base: Operator, BaseMagister, BaseAgent
│   ├── events/                 # Event Bus, Event Store
│   ├── memory/                 # Obsidian integration
│   └── storage/                # Database
├── AIM/                        # Agency (приложение)
│   ├── src/aim/                # Конкретная реализация
│   │   ├── magisters/          # SEO, Content, Ads Magisters
│   │   └── subagents/          # Конкретные субагенты
│   ├── obsidian/               # Vaults агентов
│   └── data/                   # База агентства
```

### Новая структура с инструментами

```
AIM/
├── src/aim/
│   ├── magisters/              # Magisters (координаторы)
│   │   ├── seo_magister.py
│   │   ├── content_magister.py
│   │   └── ads_magister.py
│   └── subagents/              # Субагенты (исполнители)
│       ├── custdev/            # 🆕 AI CustDev
│       │   ├── __init__.py
│       │   ├── custdev_agent.py
│       │   ├── avatar_loader.py
│       │   ├── interview_manager.py
│       │   └── analytics_generator.py
│       ├── competitive_intel/  # 🆕 ROI
│       │   ├── __init__.py
│       │   ├── ci_orchestrator_agent.py
│       │   ├── ci_scout.py
│       │   ├── ci_auditor.py
│       │   └── tw_orchestrator_agent.py
│       ├── yandex_direct/      # 🆕 YandexDirect
│       │   ├── __init__.py
│       │   ├── yad_orchestrator_agent.py
│       │   ├── planner_agent.py
│       │   ├── bidding_agent.py
│       │   └── optimizer_agent.py
│       ├── content_automation/ # 🆕 Дзен пулемет
│       │   ├── __init__.py
│       │   ├── content_farm_agent.py
│       │   ├── telegram_publisher_agent.py
│       │   └── rss_builder_agent.py
│       └── seo_indexation/     # 🆕 GEO оптимизатор
│           ├── __init__.py
│           ├── article_generator_agent.py
│           ├── indexation_agent.py
│           └── sitemap_generator_agent.py
├── obsidian/                   # Vaults агентов
│   ├── custdev-agent/
│   ├── ci-agent/
│   ├── yad-agent/
│   ├── content-farm-agent/
│   └── seo-agent/
└── data/                       # База агентства
```

---

## 🔄 Паттерн интеграции

### Шаг 1: Обёртка в BaseAgent

Каждый инструмент оборачивается в класс, наследующий `BaseAgent`:

```python
from meai.agents.base_agent import BaseAgent
from meai.events.event_bus import EventBus

class CustDevAgent(BaseAgent):
    """AI CustDev субагент для проведения интервью"""
    
    def __init__(self, agent_id: str, event_bus: EventBus):
        super().__init__(agent_id, event_bus)
        # Инициализация оригинального инструмента
        self.avatar_loader = AvatarLoader()
        self.interview_manager = InterviewManager()
    
    async def execute_task(self, task: Task) -> TaskResult:
        """Выполнить задачу CustDev"""
        # Парсинг задачи
        project_id = task.payload.get("project_id")
        target_audience = task.payload.get("target_audience")
        
        # Выполнение через оригинальный инструмент
        avatars = await self.avatar_loader.match_avatars(target_audience)
        interviews = await self.interview_manager.conduct_interviews(avatars)
        analytics = await self.generate_analytics(interviews)
        
        # Возврат результата
        return TaskResult(
            task_id=task.id,
            status="completed",
            result=analytics
        )
    
    def get_capabilities(self) -> list[str]:
        return [
            "custdev_interview",
            "avatar_matching",
            "jobs_graph_generation",
            "rat_analysis"
        ]
```

### Шаг 2: Регистрация в AgentFactory

```python
# src/meai/agents/factory.py
from aim.subagents.custdev.custdev_agent import CustDevAgent

class AgentFactory:
    def create_agent(self, agent_type: str, agent_id: str) -> BaseAgent:
        if agent_type == "custdev":
            return CustDevAgent(agent_id, self.event_bus)
        # ... другие агенты
```

### Шаг 3: Obsidian Vault для агента

```
AIM/obsidian/custdev-agent/
├── raw/                        # Источники (immutable)
├── wiki/                       # Структурированное знание
│   ├── index.md               # Каталог
│   ├── log.md                 # Хронология операций
│   ├── concepts/              # Концепции AJTBD
│   ├── technologies/          # FastAPI, Claude API
│   ├── strategies/            # Методология интервью
│   ├── agents/                # Связи с другими агентами
│   ├── workflows/             # Процессы CustDev
│   ├── projects/              # Проекты клиентов
│   ├── sources/               # Обработанные источники
│   └── connections/           # Синтезы
├── decisions/                 # Стратегические решения
└── SCHEMA.md                  # Правила vault
```

### Шаг 4: Делегирование через Operator

```python
# Operator получает задачу от Architect
task = Task(
    id="task_001",
    type="custdev_interview",
    payload={
        "project_id": "client_001",
        "target_audience": "женщины 25-45, косметология"
    }
)

# Operator делегирует CustDev агенту
await operator.delegate_to_agent(task, agent_type="custdev")

# CustDev агент выполняет и возвращает результат
result = await custdev_agent.execute_task(task)

# Operator агрегирует результаты
await operator.report_to_user(result)
```

---

## 📋 План миграции (по приоритетам)

### Приоритет 1: ROI (Competitive Intelligence)

**Почему первым:**
- Самый востребованный инструмент
- Уже имеет агентную архитектуру (23 агента)
- Легко интегрируется в систему

**Задачи:**
1. Создать `AIM/src/aim/subagents/competitive_intel/`
2. Обернуть CI Orchestrator в `CIAgent(BaseAgent)`
3. Обернуть TW Orchestrator в `TWAgent(BaseAgent)`
4. Создать Obsidian vault `AIM/obsidian/ci-agent/`
5. Зарегистрировать в AgentFactory
6. Тестовый запуск через Operator

**Время:** 2-3 дня

---

### Приоритет 2: YandexDirect (YAD Agent)

**Почему вторым:**
- Критичен для монетизации
- Уже имеет оркестратор + 4 агента
- Автопилот готов

**Задачи:**
1. Создать `AIM/src/aim/subagents/yandex_direct/`
2. Обернуть YAD Orchestrator в `YADAgent(BaseAgent)`
3. Интегрировать OAuth + Direct API
4. Создать Obsidian vault `AIM/obsidian/yad-agent/`
5. Настроить автопилот через Operator
6. Тестовый запуск с реальным аккаунтом

**Время:** 3-4 дня

---

### Приоритет 3: AI CustDev

**Почему третьим:**
- Ценный для стратегии
- Полнофункциональный MVP
- Требует интеграции FastAPI + PostgreSQL

**Задачи:**
1. Создать `AIM/src/aim/subagents/custdev/`
2. Обернуть Interview Manager в `CustDevAgent(BaseAgent)`
3. Интегрировать с базой AIM (или отдельная БД)
4. Создать Obsidian vault `AIM/obsidian/custdev-agent/`
5. Тестовый запуск интервью
6. Интеграция с Content Magister

**Время:** 4-5 дней

---

### Приоритет 4: Дзен пулемет (Content Automation)

**Почему четвёртым:**
- Автоматизация контента
- Telegram интеграция
- Модерация контента

**Задачи:**
1. Создать `AIM/src/aim/subagents/content_automation/`
2. Обернуть Farm Manager в `ContentFarmAgent(BaseAgent)`
3. Интегрировать Telegram Publisher
4. Создать Obsidian vault `AIM/obsidian/content-farm-agent/`
5. Настроить расписание через Operator
6. Тестовый запуск с модерацией

**Время:** 3-4 дня

---

### Приоритет 5: GEO оптимизатор (SEO Indexation)

**Почему последним:**
- Специфичный для SEO
- Требует интеграции с GSC/Bing
- Менее критичен на старте

**Задачи:**
1. Создать `AIM/src/aim/subagents/seo_indexation/`
2. Обернуть генератор статей в `SEOAgent(BaseAgent)`
3. Интегрировать GSC API
4. Создать Obsidian vault `AIM/obsidian/seo-agent/`
5. Тестовый запуск генерации
6. Интеграция с SEO Magister

**Время:** 3-4 дня

---

## 🎯 Итоговая архитектура

### Иерархия

```
YOU (Human)
  ↓
ARCHITECT (Strategy Layer)
  ↓
OPERATOR (Tactical Layer)
  ↓
MAGISTERS (Domain Coordinators)
  ├── SEO Magister
  │   ├── CI Agent (ROI)
  │   └── SEO Agent (GEO оптимизатор)
  ├── Content Magister
  │   ├── CustDev Agent (AI CustDev)
  │   └── Content Farm Agent (Дзен пулемет)
  └── Ads Magister
      └── YAD Agent (YandexDirect)
```

### Коммуникация

- **Event Bus** — асинхронная передача задач
- **Obsidian Vaults** — персистентная память агентов
- **Database** — структурированные данные (задачи, метрики, логи)
- **Event Store** — иммутабельный аудит лог

---

## 📊 Ожидаемые результаты

### После интеграции всех инструментов

**Возможности агентства:**
1. ✅ Полная конкурентная разведка (ROI)
2. ✅ Автоматизация Яндекс.Директ (YAD)
3. ✅ Глубокий CustDev (AI CustDev)
4. ✅ Автоматизация контента (Дзен пулемет)
5. ✅ SEO-продвижение (GEO оптимизатор)

**Автономность:**
- Operator делегирует задачи субагентам
- Субагенты выполняют автономно
- Результаты агрегируются и отчитываются YOU

**Масштабируемость:**
- Каждый инструмент = независимый субагент
- Легко добавлять новые инструменты
- Параллельное выполнение задач

---

## 🚀 Следующие шаги

### Немедленно (сегодня)

1. **Создать структуру папок** для субагентов
2. **Начать с ROI** — самый простой для интеграции
3. **Обернуть CI Orchestrator** в BaseAgent
4. **Тестовый запуск** через Operator

### На этой неделе

1. Интегрировать ROI полностью
2. Начать интеграцию YandexDirect
3. Создать Obsidian vaults для агентов
4. Документация для Architect

### В течение месяца

1. Интегрировать все 5 инструментов
2. Полное тестирование через Operator
3. Автопилот для YandexDirect
4. Первый реальный клиент

---

## 📈 Статус интеграции

### ✅ День 1 завершён (2026-05-04)

**ROI (Competitive Intelligence) - Приоритет 1**

**Создано:**
- ✅ CI Orchestrator (16 фаз, 3 tier, управление 23 агентами)
- ✅ CI Scout (Phase 1) - поиск и кластеризация конкурентов
- ✅ CI Auditor (Phase 2-3) - глубокий аудит сайтов (technical/content/UX/marketing)
- ✅ CI Reputation (Phase 4) - анализ репутации через 5 источников
- ✅ CI Factchecker (Phase 6) - проверка фактов и confidence scoring
- ✅ CI Strategist (Phase 7-8) - стратегический синтез + GTM

**Obsidian Vaults (LLM Wiki pattern):**
- ✅ `AIM/obsidian/ci-orchestrator/`
- ✅ `AIM/obsidian/ci-scout/`
- ✅ `AIM/obsidian/ci-auditor/`
- ✅ `AIM/obsidian/ci-reputation/`
- ✅ `AIM/obsidian/ci-factchecker/`
- ✅ `AIM/obsidian/ci-strategist/`

**Тестирование:**
- ✅ Комплексный интеграционный тест (`scripts/test_ci_pipeline.py`)
- ✅ Все 5 агентов работают корректно
- ✅ Pipeline протестирован end-to-end
- ✅ Результаты сохраняются в `AIM/data/ci-*.json`

**Статистика:**
- ~4800 строк production-ready кода
- 5 агентов с полной бизнес-логикой
- 6 vaults с правильной структурой
- 3 коммита созданы

**Результаты теста:**
```
Phase 1 (Scout):       5 конкурентов найдено
Phase 2 (Auditor):     63.2/100 средняя оценка
Phase 3 (Reputation):  82.4/100 средняя репутация
Phase 4 (Factchecker): acceptable качество данных
Phase 5 (Strategist):  5 рекомендаций
```

### ⏳ День 2 - в процессе

**Оставшиеся 18 агентов из 23:**

**Phase 5 (7 параллельных агентов):**
- ⏳ CI Finance - финансовый анализ
- ⏳ CI Vacancies - анализ вакансий
- ⏳ CI Tech - tech stack анализ
- ⏳ CI Site Crawler - глубокий краулинг
- ⏳ CI Content - контент-стратегия
- ⏳ CI Pricing - ценовой анализ
- ⏳ CI Ecosystem - экосистема партнёров

**Phase 9:**
- ⏳ CI Prioritizer - приоритизация инсайтов

**Phase 10:**
- ⏳ CI Marketing Strategy - маркетинговая стратегия

**Phase 11-15 (Traffic Wars):**
- ⏳ TW Competitor Scout - поиск рекламных конкурентов
- ⏳ TW Creative Collector - сбор креативов
- ⏳ TW Creative Analyzer - анализ креативов
- ⏳ TW Pattern Finder - поиск паттернов
- ⏳ TW Traffic Analyzer - анализ трафика

**Phase 16:**
- ⏳ CI Offer Generator - генерация коммерческого предложения

**Время:** 2-3 дня

### 📅 День 3 - запланировано

**Интеграция с Magisters:**
- ⏳ Подключение CI системы к SEO Magister
- ⏳ Подключение CI системы к Content Magister
- ⏳ Подключение CI системы к Ads Magister
- ⏳ End-to-end тестирование через Operator
- ⏳ Документация для Architect

**Время:** 1-2 дня

### 🔜 Следующие приоритеты

**Приоритет 2: YandexDirect (YAD Agent)**
- Статус: Не начато
- Время: 3-4 дня

**Приоритет 3: AI CustDev**
- Статус: Не начато
- Время: 4-5 дней

**Приоритет 4: Дзен пулемет (Content Automation)**
- Статус: Не начато
- Время: 3-4 дня

**Приоритет 5: GEO оптимизатор (SEO Indexation)**
- Статус: Не начато
- Время: 2-3 дня

---

**Версия:** 1.1  
**Дата:** 2026-05-04  
**Последнее обновление:** 2026-05-04T19:22  
**Автор:** meAI + Claude Opus 4.6
