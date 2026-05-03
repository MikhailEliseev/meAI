---
title: "Synthesis Strategy for AIM Agency - Actionable Plans"
type: connection
created: 2026-05-03T08:33
priority: critical
status: active
tags:
  - synthesis
  - aim-agency
  - actionable-plans
  - automation
related:
  - "[[monitor-gatekeeper-integration]]"
  - "[[2026-05-02-blackhat-seo]]"
  - "[[medical-content-agent]]"
  - "[[competitor-intelligence-agent]]"
---

# Synthesis Strategy for AIM Agency - Actionable Plans

## Проблема, которую решаем

**Текущее состояние:**
- Wiki заполняется инсайтами из разных источников
- Инсайты изолированы (sources/, agents/, strategies/)
- Нет автоматического синтеза в actionable plans
- Connections/ создаются вручную

**Желаемое состояние:**
- Автоматический синтез инсайтов из wiki
- Actionable plans для AIM Agency
- Connections между разными областями знаний
- Приоритизация по impact и feasibility

## Архитектура синтеза

### 3-Layer Synthesis Pipeline

```
Layer 1: Collection (Сбор)
    ↓
wiki/sources/ + wiki/agents/ + wiki/strategies/
    ↓
Layer 2: Synthesis (Синтез)
    ↓
Synthesis Agent читает wiki → находит связи → создаёт connections/
    ↓
Layer 3: Actionable Plans (Планы)
    ↓
connections/ → prioritization → actionable plans для AIM Agency
```

### Synthesis Agent Architecture

```python
class SynthesisAgent:
    """Агент для синтеза инсайтов в actionable plans"""
    
    def __init__(self, wiki_dir: Path):
        self.wiki_dir = wiki_dir
        self.sources_dir = wiki_dir / "sources"
        self.agents_dir = wiki_dir / "agents"
        self.strategies_dir = wiki_dir / "strategies"
        self.connections_dir = wiki_dir / "connections"
    
    async def synthesize_for_domain(self, domain: str) -> Path:
        """
        Синтезировать инсайты для конкретного домена
        
        Args:
            domain: "medical-marketing" | "ai-automation" | "seo" | "content"
        
        Returns:
            Path к созданному connection-документу
        """
        # 1. Собрать релевантные wiki-документы
        relevant_docs = await self.collect_relevant_docs(domain)
        
        # 2. Извлечь ключевые инсайты
        insights = await self.extract_insights(relevant_docs)
        
        # 3. Найти связи между инсайтами
        connections = await self.find_connections(insights)
        
        # 4. Создать actionable plan
        plan = await self.create_actionable_plan(connections, domain)
        
        # 5. Сохранить в connections/
        connection_path = await self.save_connection(plan, domain)
        
        return connection_path
    
    async def collect_relevant_docs(self, domain: str) -> List[Dict]:
        """Собрать релевантные wiki-документы для домена"""
        docs = []
        
        # Читаем все wiki-документы
        for category in ["sources", "agents", "strategies", "technologies"]:
            category_dir = self.wiki_dir / category
            if not category_dir.exists():
                continue
            
            for doc_path in category_dir.glob("*.md"):
                # Парсим frontmatter
                frontmatter = self.parse_frontmatter(doc_path)
                
                # Проверяем релевантность по тегам
                tags = frontmatter.get("tags", [])
                if self.is_relevant_for_domain(tags, domain):
                    docs.append({
                        "path": doc_path,
                        "category": category,
                        "frontmatter": frontmatter,
                        "content": doc_path.read_text()
                    })
        
        return docs
    
    async def extract_insights(self, docs: List[Dict]) -> List[Dict]:
        """Извлечь ключевые инсайты из документов"""
        insights = []
        
        for doc in docs:
            # Вызываем Claude CLI для извлечения инсайтов
            prompt = f"""
Извлеки ключевые инсайты из wiki-документа.

Документ: {doc['path'].name}
Категория: {doc['category']}

Контент:
{doc['content']}

Задача:
1. Найди 3-5 ключевых инсайтов
2. Для каждого инсайта определи:
   - Суть (1-2 предложения)
   - Применимость для AIM Agency (high/medium/low)
   - Требуемые ресурсы (time, budget, skills)
   - Потенциальный impact (high/medium/low)

Формат ответа (JSON):
{{
  "insights": [
    {{
      "summary": "...",
      "applicability": "high",
      "resources": {{"time": "2 weeks", "budget": "5000", "skills": ["AI", "SEO"]}},
      "impact": "high"
    }}
  ]
}}
"""
            
            result = await self.call_claude_cli(prompt, model="sonnet")
            doc_insights = json.loads(result)
            
            for insight in doc_insights["insights"]:
                insight["source"] = doc["path"].name
                insight["category"] = doc["category"]
                insights.append(insight)
        
        return insights
    
    async def find_connections(self, insights: List[Dict]) -> List[Dict]:
        """Найти связи между инсайтами"""
        connections = []
        
        # Группируем инсайты по темам
        themes = self.group_by_themes(insights)
        
        for theme, theme_insights in themes.items():
            if len(theme_insights) < 2:
                continue  # Нужно минимум 2 инсайта для связи
            
            # Вызываем Claude CLI для поиска связей
            prompt = f"""
Найди связи между инсайтами на тему: {theme}

Инсайты:
{json.dumps(theme_insights, indent=2, ensure_ascii=False)}

Задача:
1. Найди синергии между инсайтами
2. Определи, как они дополняют друг друга
3. Создай unified strategy, объединяющую инсайты

Формат ответа (JSON):
{{
  "theme": "{theme}",
  "synergies": ["синергия 1", "синергия 2"],
  "unified_strategy": "описание стратегии",
  "combined_impact": "high/medium/low",
  "implementation_order": ["шаг 1", "шаг 2", "шаг 3"]
}}
"""
            
            result = await self.call_claude_cli(prompt, model="opus")
            connection = json.loads(result)
            connection["insights"] = theme_insights
            connections.append(connection)
        
        return connections
    
    async def create_actionable_plan(self, connections: List[Dict], domain: str) -> Dict:
        """Создать actionable plan из connections"""
        
        # Приоритизируем connections по impact и feasibility
        prioritized = self.prioritize_connections(connections)
        
        # Создаём план
        plan = {
            "domain": domain,
            "created": datetime.now().isoformat(),
            "connections": prioritized,
            "phases": [],
            "total_impact": self.calculate_total_impact(prioritized),
            "estimated_timeline": self.estimate_timeline(prioritized)
        }
        
        # Разбиваем на фазы
        plan["phases"] = self.create_phases(prioritized)
        
        return plan
    
    def prioritize_connections(self, connections: List[Dict]) -> List[Dict]:
        """Приоритизировать connections по impact и feasibility"""
        
        # Scoring matrix
        for conn in connections:
            impact_score = self.score_impact(conn["combined_impact"])
            feasibility_score = self.score_feasibility(conn["insights"])
            
            conn["priority_score"] = impact_score * feasibility_score
            conn["priority"] = self.get_priority_label(conn["priority_score"])
        
        # Сортируем по priority_score
        return sorted(connections, key=lambda x: x["priority_score"], reverse=True)
    
    def create_phases(self, connections: List[Dict]) -> List[Dict]:
        """Разбить connections на фазы реализации"""
        phases = []
        
        # Phase 1: Quick Wins (high impact, high feasibility)
        quick_wins = [c for c in connections if c["priority"] == "critical"]
        if quick_wins:
            phases.append({
                "name": "Phase 1: Quick Wins",
                "duration": "1-2 weeks",
                "connections": quick_wins,
                "goal": "Быстрые результаты для валидации подхода"
            })
        
        # Phase 2: Core Infrastructure (high impact, medium feasibility)
        core = [c for c in connections if c["priority"] == "high"]
        if core:
            phases.append({
                "name": "Phase 2: Core Infrastructure",
                "duration": "1-2 months",
                "connections": core,
                "goal": "Построить основу для масштабирования"
            })
        
        # Phase 3: Advanced Features (medium impact, variable feasibility)
        advanced = [c for c in connections if c["priority"] == "medium"]
        if advanced:
            phases.append({
                "name": "Phase 3: Advanced Features",
                "duration": "2-3 months",
                "connections": advanced,
                "goal": "Расширенные возможности и оптимизация"
            })
        
        return phases
```

## Пример синтеза для AIM Agency

### Input: Wiki Documents

**1. sources/2026-05-02-blackhat-seo.md**
- Инсайт 1: AI-агенты для автоматизации контента
- Инсайт 2: CloudFlare Pages для безопасности
- Инсайт 3: Процессы важнее людей

**2. agents/medical-content-agent.md**
- Инсайт 1: Генерация медицинского контента
- Инсайт 2: SEO-оптимизация для медицины
- Инсайт 3: Экспертная валидация

**3. agents/competitor-intelligence-agent.md**
- Инсайт 1: Мониторинг конкурентов
- Инсайт 2: Анализ трендов
- Инсайт 3: Автоматические отчёты

### Processing: Synthesis Agent

**Шаг 1: Collect**
- Собрано 3 документа
- Извлечено 9 инсайтов
- Определены темы: "AI automation", "Medical content", "Competitive intelligence"

**Шаг 2: Extract Insights**
```json
{
  "insights": [
    {
      "summary": "AI-агенты могут автоматизировать генерацию медицинского контента с SEO-оптимизацией",
      "applicability": "high",
      "resources": {
        "time": "2 weeks",
        "budget": "5000",
        "skills": ["AI", "Medical", "SEO"]
      },
      "impact": "high",
      "source": "2026-05-02-blackhat-seo.md + medical-content-agent.md"
    }
  ]
}
```

**Шаг 3: Find Connections**
```json
{
  "theme": "AI-Powered Medical Content Automation",
  "synergies": [
    "AI-агенты (BlackHat SEO) + Medical Content Agent = автоматизация контента",
    "CloudFlare Pages (безопасность) + Medical sites = защита клиентских сайтов",
    "Competitor Intelligence + Medical trends = контент на основе трендов"
  ],
  "unified_strategy": "Создать систему автоматической генерации медицинского контента на основе анализа конкурентов и трендов",
  "combined_impact": "high",
  "implementation_order": [
    "1. Настроить Competitor Intelligence Agent для медицинской ниши",
    "2. Интегрировать Medical Content Agent с анализом трендов",
    "3. Автоматизировать публикацию на CloudFlare Pages",
    "4. Добавить SEO-оптимизацию и мониторинг позиций"
  ]
}
```

**Шаг 4: Create Actionable Plan**
```json
{
  "domain": "medical-marketing",
  "created": "2026-05-03T08:33:00Z",
  "total_impact": "high",
  "estimated_timeline": "6-8 weeks",
  "phases": [
    {
      "name": "Phase 1: Quick Wins",
      "duration": "1-2 weeks",
      "connections": [
        {
          "theme": "AI-Powered Medical Content Automation",
          "priority": "critical",
          "actions": [
            "Настроить Competitor Intelligence Agent",
            "Создать первые 10 статей автоматически",
            "Опубликовать на CloudFlare Pages"
          ]
        }
      ],
      "goal": "Доказать, что автоматизация работает"
    },
    {
      "name": "Phase 2: Core Infrastructure",
      "duration": "1-2 months",
      "connections": [
        {
          "theme": "Scalable Content Pipeline",
          "priority": "high",
          "actions": [
            "Автоматизировать весь pipeline (анализ → генерация → публикация)",
            "Добавить SEO-мониторинг",
            "Интегрировать с клиентскими сайтами"
          ]
        }
      ],
      "goal": "Построить масштабируемую систему"
    }
  ]
}
```

### Output: Connection Document

**connections/ai-medical-content-automation.md** (создаётся автоматически)

## Реализация Synthesis Agent

### Priority 1: Базовая версия (1-2 дня)

**Функционал:**
- Чтение wiki-документов из sources/, agents/, strategies/
- Извлечение инсайтов через Claude CLI
- Простой поиск связей (по тегам и темам)
- Создание connection-документов вручную (на основе синтеза)

**Код:**
```python
# scripts/synthesis_agent.py

import asyncio
from pathlib import Path
from typing import List, Dict
import json
import subprocess

class SynthesisAgent:
    def __init__(self, wiki_dir: Path):
        self.wiki_dir = wiki_dir
    
    async def synthesize_for_domain(self, domain: str) -> Path:
        """Синтезировать инсайты для домена"""
        
        # 1. Собрать документы
        docs = await self.collect_relevant_docs(domain)
        print(f"📚 Собрано документов: {len(docs)}")
        
        # 2. Извлечь инсайты
        insights = await self.extract_insights(docs)
        print(f"💡 Извлечено инсайтов: {len(insights)}")
        
        # 3. Найти связи
        connections = await self.find_connections(insights)
        print(f"🔗 Найдено связей: {len(connections)}")
        
        # 4. Создать план
        plan = await self.create_actionable_plan(connections, domain)
        print(f"📋 План создан: {plan['estimated_timeline']}")
        
        # 5. Сохранить
        connection_path = await self.save_connection(plan, domain)
        print(f"✅ Сохранено: {connection_path}")
        
        return connection_path

async def main():
    wiki_dir = Path("obsidian/architect/wiki")
    agent = SynthesisAgent(wiki_dir)
    
    # Синтезируем для medical marketing
    connection = await agent.synthesize_for_domain("medical-marketing")
    print(f"\n🎉 Connection создан: {connection}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Priority 2: Автоматизация (1 неделя)

**Функционал:**
- Автоматический запуск при обновлении wiki
- Интеграция с Monitor (после создания wiki → запуск синтеза)
- Автоматическое обновление index.md
- Логирование в log.md

### Priority 3: Advanced Features (2-3 недели)

**Функционал:**
- ML для поиска неочевидных связей
- Автоматическая приоритизация по ROI
- Интеграция с метриками AIM Agency
- Dashboard для визуализации connections

## Метрики успеха

### До Synthesis Agent:
- ❌ Connections создаются вручную
- ❌ Инсайты изолированы
- ❌ Нет actionable plans
- ❌ Синтез занимает часы

### После Synthesis Agent:
- ✅ Connections создаются автоматически
- ✅ Инсайты связываются
- ✅ Actionable plans генерируются
- ✅ Синтез занимает минуты

## Next Steps

### Immediate (сегодня):
1. ✅ Создать этот документ (connections/synthesis-strategy-aim-agency-v2.md)
2. ⏳ Реализовать базовую версию Synthesis Agent
3. ⏳ Протестировать на существующих wiki-документах

### Short-term (эта неделя):
1. Интегрировать Synthesis Agent с Monitor
2. Автоматизировать создание connections/
3. Создать первые actionable plans для AIM Agency

### Long-term (этот месяц):
1. Добавить ML для поиска связей
2. Создать dashboard для connections
3. Интегрировать с метриками AIM Agency

## Вывод

**Проблема:** Wiki заполняется, но инсайты не синтезируются в actionable plans.

**Решение:** Synthesis Agent, который автоматически:
1. Читает wiki-документы
2. Извлекает инсайты
3. Находит связи
4. Создаёт actionable plans

**Результат:** Автоматический синтез знаний в конкретные планы для AIM Agency.

---

**Architect Decision:** Реализовать Synthesis Agent как следующий приоритет после улучшения Monitor.
