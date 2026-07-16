---
title: "Teacher Agent - Implementation Design"
type: agent
created: 2026-05-03T08:36
priority: critical
status: design
tags:
  - teacher
  - learning-system
  - hierarchy
  - magisters
  - feedback-loop
related:
  - "[[gatekeeper-agent]]"
  - "[[synthesis-strategy-aim-agency-v2]]"
  - "[[monitor-gatekeeper-integration]]"
---

# Teacher Agent - Implementation Design

## Роль в системе

**Teacher (Ректор) — центр обучающей системы агентства.**

Не обучает субагентов напрямую, а **обучает магистров**, которые затем обучают субагентов. Принимает обратную связь от магистров для улучшения системы.

## Архитектура

### Иерархия обучения

```
YOU (Собственник)
  ↕ стратегия / обратная связь
OPERATOR (Операционный директор)
  ↕ операционные задачи / проблемы
TEACHER (Ректор)
  ↕ знания / улучшения
MAGISTERS (Магистры по направлениям)
  ↕ узкие знания / пробелы
SUBAGENTS (Узкоспециализированные исполнители)
```

### Интеграция с существующей системой

```
Monitor + Gatekeeper
    ↓ (новые знания прошли проверку)
raw/ → wiki/
    ↓ (структурированные инсайты)
Synthesis Agent
    ↓ (connections и actionable plans)
TEACHER AGENT ← НОВОЕ ЗВЕНО
    ↓ (распределение знаний)
Magisters
    ↓ (адаптация для субагентов)
Subagents
```

## Компоненты Teacher Agent

### 1. Knowledge Distributor (Распределитель знаний)

**Задача:** Получать новые знания из wiki и распределять магистрам.

**Источники:**
- `wiki/sources/` - обработанные источники
- `wiki/connections/` - синтезированные инсайты
- `wiki/strategies/` - стратегии
- `wiki/technologies/` - технологии

**Логика:**
```python
class KnowledgeDistributor:
    """Распределяет знания из wiki магистрам"""
    
    async def distribute_new_knowledge(self, wiki_doc: Path) -> List[str]:
        """
        Определить, каким магистрам релевантно новое знание
        
        Returns:
            List магистров, которым нужно передать знание
        """
        # 1. Читаем wiki-документ
        frontmatter = self.parse_frontmatter(wiki_doc)
        tags = frontmatter.get("tags", [])
        
        # 2. Определяем релевантных магистров
        relevant_magisters = []
        
        if any(tag in tags for tag in ["seo", "search", "ranking"]):
            relevant_magisters.append("seo-magister")
        
        if any(tag in tags for tag in ["content", "copywriting", "articles"]):
            relevant_magisters.append("content-magister")
        
        if any(tag in tags for tag in ["ads", "advertising", "ppc"]):
            relevant_magisters.append("ads-magister")
        
        if any(tag in tags for tag in ["ai", "automation", "agents"]):
            relevant_magisters.append("ai-magister")
        
        # 3. Отправляем знание магистрам
        for magister in relevant_magisters:
            await self.send_knowledge_to_magister(magister, wiki_doc)
        
        return relevant_magisters
    
    async def send_knowledge_to_magister(self, magister: str, wiki_doc: Path):
        """Отправить знание магистру"""
        
        # Создаём задачу для магистра через Event Bus
        task = Task(
            type="knowledge_update",
            magister=magister,
            source=wiki_doc,
            priority="high"
        )
        
        await self.event_bus.publish(task)
```

### 2. Magister Manager (Менеджер магистров)

**Задача:** Управлять магистрами и их базами знаний.

**Функции:**
- Создание новых магистров
- Обновление баз знаний магистров
- Мониторинг активности магистров
- Обработка обратной связи от магистров

**Логика:**
```python
class MagisterManager:
    """Управляет магистрами и их базами знаний"""
    
    def __init__(self, magisters_dir: Path):
        self.magisters_dir = magisters_dir
        self.magisters = self.load_magisters()
    
    def load_magisters(self) -> Dict[str, Magister]:
        """Загрузить всех магистров"""
        magisters = {}
        
        for magister_dir in self.magisters_dir.iterdir():
            if magister_dir.is_dir():
                magister = Magister.from_directory(magister_dir)
                magisters[magister.name] = magister
        
        return magisters
    
    async def create_magister(self, name: str, domain: str, description: str) -> Magister:
        """Создать нового магистра"""
        
        magister_dir = self.magisters_dir / name
        magister_dir.mkdir(exist_ok=True)
        
        # Создаём структуру
        (magister_dir / "knowledge-base.md").touch()
        (magister_dir / "sources.md").touch()
        (magister_dir / "improvements.md").touch()
        (magister_dir / "problems.md").touch()
        (magister_dir / "subagents").mkdir(exist_ok=True)
        
        # Создаём конфиг
        config = {
            "name": name,
            "domain": domain,
            "description": description,
            "created": datetime.now().isoformat(),
            "status": "active"
        }
        
        with open(magister_dir / "config.yaml", 'w') as f:
            yaml.dump(config, f)
        
        magister = Magister(name, domain, magister_dir)
        self.magisters[name] = magister
        
        return magister
    
    async def update_magister_knowledge(self, magister_name: str, knowledge: Dict):
        """Обновить базу знаний магистра"""
        
        magister = self.magisters[magister_name]
        
        # Добавляем новое знание в knowledge-base.md
        await magister.add_knowledge(knowledge)
        
        # Логируем
        await self.log_knowledge_update(magister_name, knowledge)
    
    async def process_magister_feedback(self, magister_name: str, feedback: Dict):
        """Обработать обратную связь от магистра"""
        
        feedback_type = feedback.get("type")
        
        if feedback_type == "missing_knowledge":
            # Магистру не хватает знаний
            await self.handle_missing_knowledge(magister_name, feedback)
        
        elif feedback_type == "outdated_info":
            # Информация устарела
            await self.handle_outdated_info(magister_name, feedback)
        
        elif feedback_type == "system_improvement":
            # Предложение улучшения системы
            await self.handle_system_improvement(magister_name, feedback)
        
        elif feedback_type == "escalation":
            # Эскалация к Operator
            await self.escalate_to_operator(magister_name, feedback)
```

### 3. Feedback Processor (Обработчик обратной связи)

**Задача:** Обрабатывать обратную связь от магистров и улучшать систему.

**Типы обратной связи:**
1. **Missing Knowledge** - не хватает знаний
2. **Outdated Info** - информация устарела
3. **System Improvement** - предложение улучшения
4. **Escalation** - эскалация к Operator

**Логика:**
```python
class FeedbackProcessor:
    """Обрабатывает обратную связь от магистров"""
    
    async def handle_missing_knowledge(self, magister: str, feedback: Dict):
        """Обработать запрос на недостающие знания"""
        
        topic = feedback.get("topic")
        urgency = feedback.get("urgency", "medium")
        
        # 1. Ищем знания в wiki
        existing_knowledge = await self.search_wiki(topic)
        
        if existing_knowledge:
            # Знания есть, просто не были переданы магистру
            await self.send_knowledge_to_magister(magister, existing_knowledge)
            return
        
        # 2. Знаний нет - нужно найти новые источники
        # Создаём задачу для Monitor
        task = Task(
            type="find_knowledge",
            topic=topic,
            magister=magister,
            urgency=urgency
        )
        
        await self.event_bus.publish(task)
        
        # 3. Логируем запрос
        await self.log_knowledge_request(magister, topic, urgency)
    
    async def handle_outdated_info(self, magister: str, feedback: Dict):
        """Обработать сообщение об устаревшей информации"""
        
        wiki_doc = feedback.get("wiki_doc")
        reason = feedback.get("reason")
        
        # 1. Помечаем документ как устаревший
        await self.mark_as_outdated(wiki_doc, reason)
        
        # 2. Создаём задачу на обновление
        task = Task(
            type="update_knowledge",
            wiki_doc=wiki_doc,
            reason=reason,
            magister=magister
        )
        
        await self.event_bus.publish(task)
        
        # 3. Уведомляем других магистров, использующих этот документ
        await self.notify_affected_magisters(wiki_doc)
    
    async def handle_system_improvement(self, magister: str, feedback: Dict):
        """Обработать предложение улучшения системы"""
        
        improvement = feedback.get("improvement")
        impact = feedback.get("impact", "medium")
        
        # 1. Сохраняем предложение
        await self.save_improvement_proposal(magister, improvement, impact)
        
        # 2. Если impact высокий - эскалируем Operator
        if impact == "high":
            await self.escalate_to_operator(magister, {
                "type": "system_improvement",
                "improvement": improvement,
                "impact": impact
            })
        
        # 3. Логируем
        await self.log_improvement_proposal(magister, improvement)
    
    async def escalate_to_operator(self, magister: str, feedback: Dict):
        """Эскалировать проблему к Operator"""
        
        # Создаём задачу для Operator
        task = Task(
            type="escalation",
            from_magister=magister,
            feedback=feedback,
            priority="high"
        )
        
        await self.event_bus.publish(task, priority=Priority.P0)
        
        # Логируем эскалацию
        await self.log_escalation(magister, feedback)
```

### 4. Learning Strategy Manager (Менеджер стратегии обучения)

**Задача:** Управлять стратегией обучения и улучшать её на основе обратной связи.

**Функции:**
- Анализ эффективности обучения
- Обновление стратегии на основе feedback
- A/B тестирование разных подходов
- Метрики обучения

**Логика:**
```python
class LearningStrategyManager:
    """Управляет стратегией обучения"""
    
    async def analyze_learning_effectiveness(self) -> Dict:
        """Анализировать эффективность обучения"""
        
        metrics = {
            "magisters_active": 0,
            "knowledge_updates_last_week": 0,
            "feedback_received": 0,
            "escalations": 0,
            "improvements_implemented": 0
        }
        
        # Собираем метрики по магистрам
        for magister in self.magisters.values():
            if magister.status == "active":
                metrics["magisters_active"] += 1
            
            metrics["knowledge_updates_last_week"] += magister.get_updates_count(days=7)
            metrics["feedback_received"] += magister.get_feedback_count()
        
        # Анализируем эффективность
        effectiveness_score = self.calculate_effectiveness_score(metrics)
        
        return {
            "metrics": metrics,
            "effectiveness_score": effectiveness_score,
            "recommendations": self.generate_recommendations(metrics)
        }
    
    async def update_learning_strategy(self, feedback: List[Dict]):
        """Обновить стратегию обучения на основе feedback"""
        
        # Анализируем паттерны в feedback
        patterns = self.analyze_feedback_patterns(feedback)
        
        # Если много запросов на недостающие знания - улучшаем мониторинг
        if patterns["missing_knowledge_ratio"] > 0.3:
            await self.improve_knowledge_monitoring()
        
        # Если много устаревшей информации - увеличиваем частоту обновлений
        if patterns["outdated_info_ratio"] > 0.2:
            await self.increase_update_frequency()
        
        # Если много эскалаций - проблема в системе
        if patterns["escalation_ratio"] > 0.1:
            await self.investigate_system_issues()
```

## Obsidian Structure

```
obsidian/
├── teacher/                        # Teacher Agent vault
│   ├── raw/                       # Входящие знания (от Monitor)
│   ├── wiki/
│   │   ├── index.md              # Каталог знаний
│   │   ├── log.md                # Лог операций
│   │   ├── magisters/            # Информация о магистрах
│   │   ├── strategies/           # Стратегии обучения
│   │   ├── feedback/             # Обратная связь от магистров
│   │   └── escalations/          # Эскалации к Operator
│   ├── decisions/                # Решения Teacher
│   └── SCHEMA.md                 # Правила vault
│
├── magisters/
│   ├── seo-magister/
│   │   ├── raw/                  # Входящие знания от Teacher
│   │   ├── wiki/
│   │   │   ├── knowledge-base.md # База знаний
│   │   │   ├── sources.md        # Источники для мониторинга
│   │   │   ├── improvements.md   # Идеи улучшений
│   │   │   └── problems.md       # Проблемы для эскалации
│   │   ├── subagents/            # Знания для субагентов
│   │   │   ├── positions.md
│   │   │   ├── content.md
│   │   │   └── links.md
│   │   └── SCHEMA.md
│   │
│   ├── content-magister/
│   ├── ads-magister/
│   └── ai-magister/
│
└── subagents/
    ├── seo-positions/              # Узкая база "на пальцах"
    │   ├── how-to.md
    │   ├── tools.md
    │   └── examples.md
    └── ...
```

## Workflow Examples

### Example 1: Новое знание из wiki

```
1. Monitor + Gatekeeper обрабатывают raw/
   ↓
2. Wiki-документ создаётся в architect/wiki/sources/
   ↓
3. Synthesis Agent создаёт connection
   ↓
4. Teacher Agent получает уведомление о новом connection
   ↓
5. KnowledgeDistributor определяет релевантных магистров
   ↓
6. Teacher отправляет знание магистрам через Event Bus
   ↓
7. Magisters получают знание и обновляют свои базы
   ↓
8. Magisters адаптируют знание для субагентов
   ↓
9. Subagents применяют новые знания в работе
```

### Example 2: Магистр запрашивает знания

```
1. SEO Magister: "Не хватает знаний по Google алгоритмам 2026"
   ↓
2. Teacher получает feedback через Event Bus
   ↓
3. FeedbackProcessor ищет знания в wiki
   ↓
4. Знаний нет → создаётся задача для Monitor
   ↓
5. Monitor ищет новые источники
   ↓
6. Gatekeeper проверяет качество
   ↓
7. Wiki-документ создаётся
   ↓
8. Teacher отправляет знание SEO Magister
   ↓
9. SEO Magister обновляет базы субагентов
```

### Example 3: Системное улучшение

```
1. Content Magister: "Субагенты перегружены текстом, нужно больше примеров"
   ↓
2. Teacher получает feedback (type: system_improvement, impact: high)
   ↓
3. FeedbackProcessor эскалирует к Operator
   ↓
4. Operator принимает решение изменить формат обучения
   ↓
5. Teacher обновляет стратегию обучения
   ↓
6. Magisters получают новую стратегию
   ↓
7. Magisters адаптируют базы субагентов (больше примеров, меньше теории)
   ↓
8. Subagents работают эффективнее
```

## Implementation Roadmap

### Phase 1: Core Components (1 неделя)

**Priority 1:**
- [ ] Создать Teacher Agent базовый класс
- [ ] Реализовать KnowledgeDistributor
- [ ] Реализовать MagisterManager
- [ ] Создать структуру Obsidian vaults

**Priority 2:**
- [ ] Интеграция с Event Bus
- [ ] Создать первого магистра (SEO Magister)
- [ ] Протестировать распределение знаний

### Phase 2: Feedback Loop (1 неделя)

**Priority 1:**
- [ ] Реализовать FeedbackProcessor
- [ ] Обработка 4 типов feedback
- [ ] Эскалация к Operator

**Priority 2:**
- [ ] Создать остальных магистров (Content, Ads, AI)
- [ ] Протестировать feedback loop end-to-end

### Phase 3: Learning Strategy (2 недели)

**Priority 1:**
- [ ] Реализовать LearningStrategyManager
- [ ] Метрики эффективности обучения
- [ ] Автоматическое улучшение стратегии

**Priority 2:**
- [ ] Dashboard для мониторинга обучения
- [ ] A/B тестирование подходов
- [ ] ML для оптимизации распределения знаний

## Metrics & Success Criteria

### До Teacher Agent:
- ❌ Знания не распределяются систематически
- ❌ Нет обратной связи от агентов
- ❌ Нет улучшения системы обучения
- ❌ Субагенты не обучаются

### После Teacher Agent:
- ✅ Автоматическое распределение знаний магистрам
- ✅ Обратная связь обрабатывается
- ✅ Система обучения улучшается
- ✅ Субагенты получают адаптированные знания

### Target Metrics:
- Knowledge distribution time: <5 минут (от wiki до магистра)
- Feedback response time: <1 час
- Magister satisfaction: >80%
- System improvement rate: 1+ улучшение/неделя

## Next Steps

### Immediate (сегодня):
1. ✅ Создать этот design документ
2. ⏳ Создать базовую структуру Teacher Agent
3. ⏳ Создать Obsidian vaults для Teacher и Magisters

### Short-term (эта неделя):
1. Реализовать KnowledgeDistributor
2. Реализовать MagisterManager
3. Создать первого магистра (SEO Magister)
4. Протестировать распределение знаний

### Long-term (этот месяц):
1. Реализовать полный feedback loop
2. Создать всех магистров
3. Интегрировать с Operator
4. Добавить метрики и dashboard

---

**Architect Decision:** Teacher Agent — критический компонент для масштабирования обучения в агентстве. Реализовать как следующий приоритет после Synthesis Agent.
