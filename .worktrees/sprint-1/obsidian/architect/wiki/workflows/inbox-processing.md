---
title: "Architect Raw Inbox - Улучшения после анализа ошибки"
type: improvement
created: 2026-05-02
priority: high
status: draft
tags:
  - architect
  - workflow
  - improvement
  - automation
---

# Architect Raw Inbox - Улучшения после анализа ошибки

## Проблема

**Что произошло:**
Пользователь попросил: "давай подумаем какой функционал мы можем дать агентству на основе этих двух видео"

**Моя ошибка:**
Я начал читать исходные транскрипты из `raw/` вместо уже обработанных wiki-документов.

**Почему это проблема:**
- Трата времени на повторный анализ
- Игнорирование уже проделанной работы
- Нарушение принципа "знания компилируются один раз"

---

## Анализ причин

### Причина 1: Неявная связь raw → wiki

**Проблема:**
- В `raw/` файлах есть `output: "[[wiki-file]]"` в frontmatter
- Но я не проверил это перед чтением

**Решение:**
- Добавить явную проверку: "есть ли уже обработанный wiki?"
- Если есть → читать wiki, не raw

### Причина 2: Отсутствие индекса wiki

**Проблема:**
- Нет центрального места, где видны все обработанные темы
- Приходится искать по файлам

**Решение:**
- Создать `wiki/index.md` с каталогом всех тем
- Автоматически обновлять при обработке

### Причина 3: Нет явного workflow для синтеза

**Проблема:**
- Непонятно, что делать после обработки нескольких заметок
- Нет следующего шага "синтез → решение"

**Решение:**
- Добавить этап "synthesis" в workflow
- Автоматически предлагать синтез после N обработанных заметок

---

## Улучшения системы

### Улучшение 1: Умная проверка перед чтением

**Добавить в `architect_inbox_monitor.py`:**

```python
def should_read_raw_or_wiki(self, raw_file: Path) -> tuple[str, Path]:
    """
    Определить, читать raw или wiki
    
    Returns:
        ("raw", path) или ("wiki", path)
    """
    frontmatter = self.parse_frontmatter(raw_file)
    
    # Проверяем, обработан ли файл
    if frontmatter.get('status') == 'processed':
        # Ищем output wiki
        output = frontmatter.get('output', '')
        if output:
            # Извлекаем имя файла из [[wiki-file]]
            wiki_name = output.strip('[]').strip()
            wiki_path = self.wiki_dir / f"{wiki_name}.md"
            
            if wiki_path.exists():
                return ("wiki", wiki_path)
    
    return ("raw", raw_file)
```

**Использование:**

```python
source_type, source_path = self.should_read_raw_or_wiki(file_path)

if source_type == "wiki":
    print(f"✅ Уже обработан, читаю wiki: {source_path.name}")
else:
    print(f"📥 Новый файл, читаю raw: {source_path.name}")
```

### Улучшение 2: Wiki Index (Каталог)

**Создать `wiki/index.md`:**

```markdown
# Architect Wiki - Каталог

Автоматически обновляемый индекс всех обработанных тем.

## По дате

### 2026-05-02

- [[blackhat-seo-igaming-analysis]] - BlackHat SEO методы (strategy)
- [[claude-design-practical-guide]] - Claude Design гайд (technical)
- [[medical-content-analysis-agent]] - Medical Content Agent (idea)

## По типу

### Strategy
- [[blackhat-seo-igaming-analysis]]

### Technical
- [[claude-design-practical-guide]]

### Ideas
- [[medical-content-analysis-agent]]

## По приоритету

### HIGH
- [[blackhat-seo-igaming-analysis]]
- [[claude-design-practical-guide]]
- [[medical-content-analysis-agent]]

## Связи

### AI-агенты
- [[blackhat-seo-igaming-analysis]]
- [[medical-content-analysis-agent]]

### Автоматизация
- [[blackhat-seo-igaming-analysis]]
- [[claude-design-practical-guide]]

---

**Последнее обновление:** 2026-05-02T20:50:00Z  
**Всего документов:** 3
```

**Автоматическое обновление:**

```python
def update_wiki_index(self, new_wiki_file: Path, metadata: dict):
    """Обновить wiki/index.md после создания нового wiki"""
    index_path = self.wiki_dir / "index.md"
    
    # Читаем текущий индекс
    if index_path.exists():
        with open(index_path, 'r') as f:
            content = f.read()
    else:
        content = self.generate_empty_index()
    
    # Добавляем новую запись
    date = metadata.get('created', datetime.now().strftime('%Y-%m-%d'))
    title = metadata.get('title', new_wiki_file.stem)
    type_ = metadata.get('type', 'note')
    priority = metadata.get('priority', 'medium')
    
    # Обновляем секции
    content = self.add_to_index_section(content, "По дате", date, title, type_)
    content = self.add_to_index_section(content, "По типу", type_, title)
    content = self.add_to_index_section(content, "По приоритету", priority, title)
    
    # Сохраняем
    with open(index_path, 'w') as f:
        f.write(content)
```

### Улучшение 3: Synthesis Workflow

**Добавить этап "synthesis" после обработки:**

```python
def check_synthesis_needed(self) -> bool:
    """
    Проверить, нужен ли синтез
    
    Критерии:
    - 3+ обработанных заметки за сессию
    - Или явный запрос пользователя
    - Или связанные темы
    """
    # Считаем обработанные за сегодня
    today = datetime.now().strftime('%Y-%m-%d')
    processed_today = self.count_processed_today(today)
    
    if processed_today >= 3:
        return True
    
    # Проверяем связанные темы
    related_topics = self.find_related_topics()
    if len(related_topics) >= 2:
        return True
    
    return False

def suggest_synthesis(self):
    """Предложить синтез обработанных заметок"""
    print("\n🔗 Обнаружены связанные темы!")
    print("Рекомендую синтез для создания стратегического плана.")
    print("\nОбработано сегодня:")
    
    for wiki_file in self.get_processed_today():
        metadata = self.parse_frontmatter(wiki_file)
        print(f"  - {metadata.get('title')} ({metadata.get('type')})")
    
    print("\n💡 Промпт для синтеза:")
    print("Проанализируй wiki-документы и создай стратегический план")
```

### Улучшение 4: Synthesis Agent

**Создать специального агента для синтеза:**

```python
class SynthesisAgent:
    """
    Агент для синтеза wiki-документов в стратегические планы
    """
    
    def __init__(self, wiki_dir: Path, decisions_dir: Path):
        self.wiki_dir = wiki_dir
        self.decisions_dir = decisions_dir
    
    def synthesize(self, wiki_files: list[Path], goal: str) -> Path:
        """
        Синтезировать wiki-документы в стратегический план
        
        Args:
            wiki_files: Список wiki для анализа
            goal: Цель синтеза (например, "функционал для AIM Agency")
        
        Returns:
            Путь к созданному decision-документу
        """
        # 1. Читаем все wiki
        wikis = [self.read_wiki(f) for f in wiki_files]
        
        # 2. Извлекаем ключевые инсайты
        insights = self.extract_insights(wikis)
        
        # 3. Находим связи
        connections = self.find_connections(insights)
        
        # 4. Генерируем стратегический план
        plan = self.generate_strategic_plan(insights, connections, goal)
        
        # 5. Сохраняем в decisions/
        decision_file = self.save_decision(plan)
        
        return decision_file
    
    def extract_insights(self, wikis: list[dict]) -> list[dict]:
        """Извлечь ключевые инсайты из wiki"""
        insights = []
        
        for wiki in wikis:
            # Ищем секции с инсайтами
            if 'Ключевые инсайты' in wiki['content']:
                insights.append({
                    'source': wiki['title'],
                    'type': wiki['type'],
                    'insights': self.parse_insights_section(wiki['content'])
                })
        
        return insights
    
    def find_connections(self, insights: list[dict]) -> list[dict]:
        """Найти связи между инсайтами"""
        connections = []
        
        # Ищем общие темы
        themes = {}
        for insight in insights:
            for theme in insight.get('themes', []):
                if theme not in themes:
                    themes[theme] = []
                themes[theme].append(insight['source'])
        
        # Создаём связи
        for theme, sources in themes.items():
            if len(sources) >= 2:
                connections.append({
                    'theme': theme,
                    'sources': sources,
                    'type': 'common_theme'
                })
        
        return connections
```

---

## Новый Workflow

### Этап 1: Обработка (как сейчас)

```
raw/ → Монитор → Классификация → Claude → wiki/ + decisions/
```

### Этап 2: Индексация (новое)

```
wiki/ → Update index.md → Проверка связей
```

### Этап 3: Синтез (новое)

```
wiki/ (3+ документа) → Synthesis Agent → Strategic Plan → decisions/
```

### Этап 4: Действие (новое)

```
decisions/ → Action Plan → Tasks → Execution
```

---

## Улучшенный промпт для Claude

**Вместо:**
> "давай подумаем какой функционал мы можем дать агентству на основе этих двух видео"

**Лучше:**
> "Проанализируй wiki-документы по темам [X, Y] и создай стратегический план функционала для AIM Agency"

**Или автоматически:**
> "Обнаружены связанные темы: [blackhat-seo, claude-design, medical-content]. Синтезировать в стратегический план?"

---

## Следующие шаги для синтеза

### Шаг 1: Автоматическое обнаружение связей

**Когда запускать:**
- После обработки 3+ заметок
- При явном запросе пользователя
- При обнаружении общих тем

**Что делать:**
1. Сканировать `wiki/` на связанные темы
2. Группировать по темам (AI-агенты, автоматизация, медицина)
3. Предлагать синтез

### Шаг 2: Создание стратегического плана

**Входные данные:**
- Wiki-документы по теме
- Цель синтеза
- Контекст проекта (AIM Agency)

**Выходные данные:**
- Strategic plan в `decisions/`
- Action items
- Roadmap
- Метрики успеха

### Шаг 3: Декомпозиция на задачи

**Из стратегического плана:**
- Извлечь action items
- Создать задачи в backlog
- Приоритизировать
- Назначить на спринты

### Шаг 4: Execution

**Через Operator:**
- Делегировать задачи агентам
- Мониторить выполнение
- Собирать результаты
- Отчитываться

---

## Имплементация

### Priority 1: Умная проверка (сегодня)

```python
# Добавить в architect_inbox_monitor.py
def should_read_raw_or_wiki(self, raw_file: Path) -> tuple[str, Path]:
    # ... (код выше)
```

### Priority 2: Wiki Index (завтра)

```python
# Создать wiki/index.md
# Добавить автоматическое обновление
```

### Priority 3: Synthesis Detection (эта неделя)

```python
# Добавить check_synthesis_needed()
# Добавить suggest_synthesis()
```

### Priority 4: Synthesis Agent (следующая неделя)

```python
# Создать SynthesisAgent
# Интегрировать с Operator
```

---

## Метрики успеха

**Эффективность:**
- Время на синтез: <10 минут (vs 30+ минут вручную)
- Точность связей: 90%+ релевантных
- Качество планов: проходят review с первого раза

**Автоматизация:**
- 80%+ синтезов автоматические
- 0 повторных чтений raw-файлов
- 100% обновление индекса

---

## Вывод

**Проблема:** Читал raw вместо wiki  
**Причина:** Нет явной проверки и workflow для синтеза  
**Решение:** 4 улучшения + новый workflow

**Следующий шаг:** Имплементировать Priority 1 (умная проверка) сегодня

---

**Architect Decision:** Улучшения одобрены. Начинаем с Priority 1.
