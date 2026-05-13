# Teacher Agent v2.0 - GitHub Discovery & Research Layer Added ✅

**Date:** 2026-05-13  
**Status:** COMPLETE - Ready for Final Approval

---

## Summary

Добавил критически важный компонент **GitHub Discovery & Research Layer** в спецификацию Teacher Agent v2.0.

**Spec Size:**
- Before: 3483 lines, 116 KB
- After: 3900+ lines, 130+ KB
- Added: +417 lines, +14 KB

**Time:** ~30 minutes

---

## What Was Added

### New Section 2.0: GitHub Discovery & Research Layer

**4 новых компонента:**

#### 2.0.1 ResearchOrchestrator
- Оркестрация всего процесса исследования
- Параллельный запуск web research + GitHub search
- Ранжирование репозиториев
- Возврат топ-5 решений

**Output:**
```python
@dataclass
class ResearchResult:
    topic: str                          # "circuit breaker python"
    github_repos: list[GitHubRepo]      # Топ репозитории
    best_practices: list[str]           # Лучшие практики из исследования
    tools_and_libraries: list[str]      # Инструменты и библиотеки
    industry_insights: list[str]        # Инсайты индустрии
    research_sources: list[str]         # Источники (URLs)
    research_timestamp: datetime
    research_cost: float                # Стоимость исследования
```

#### 2.0.2 WebResearcher
- Глубокое исследование через Exa MCP tools
- 3 уровня глубины: quick (~$0.50), standard (~$1.50), deep (~$3.00)
- Использует `web_search_exa` для поиска
- Использует `deep_researcher_start` для глубокого анализа
- Извлекает best practices, tools, industry insights

**Workflow:**
```python
# 1. Exa web search (20 результатов)
search_results = await self.exa_client.web_search_exa(
    query=f"{topic} best practices python",
    numResults=20
)

# 2. Deep research с Exa
research_id = await self.exa_client.deep_researcher_start(
    instructions=research_prompt,
    model="exa-research"  # или exa-research-fast/pro
)

# 3. Ожидание завершения
research_result = await self._wait_for_research(research_id)

# 4. Парсинг результатов
best_practices = self._extract_best_practices(research_result)
tools = self._extract_tools(research_result)
insights = self._extract_insights(research_result)
```

**Research Depth Levels:**
- **quick** (~$0.50, 5-10 мин): exa-research-fast, 10 источников
- **standard** (~$1.50, 10-20 мин): exa-research, 20 источников
- **deep** (~$3.00, 20-40 мин): exa-research-pro, 30+ источников

#### 2.0.3 GitHubSearcher
- Двойной поиск: GitHub API + Exa search
- Параллельное выполнение обоих поисков
- Merge и deduplication результатов
- Сортировка по звёздам

**Workflow:**
```python
# 1. GitHub API search (параллельно)
github_results = await self.github_client.search_repositories(
    query=f"{query} language:{language}",
    sort="stars",
    order="desc"
)

# 2. Exa search (параллельно)
exa_results = await self.exa_client.web_search_exa(
    query=f"{query} site:github.com",
    numResults=max_results
)

# 3. Merge и deduplicate
all_repos = self._merge_results(github_results, exa_results)

# 4. Sort by stars
sorted_repos = sorted(all_repos, key=lambda r: r.stars, reverse=True)
```

**Why Dual Search:**
- GitHub API: официальные данные, точная сортировка по звёздам
- Exa search: находит репо, которые GitHub API может пропустить
- Merge: максимальный охват релевантных решений

#### 2.0.4 RepoRanker
- Ранжирование репозиториев по 4 критериям
- Scoring 0-100 по каждому критерию
- Weighted average для финального score

**Scoring Criteria:**
1. **Stars (30 points):** Популярность репозитория
2. **Activity (25 points):** Недавние коммиты (last 6 months)
3. **Quality (25 points):** README, tests, CI/CD, docs
4. **Relevance (20 points):** Соответствие query

**Formula:**
```python
final_score = (
    stars_score * 0.30 +
    activity_score * 0.25 +
    quality_score * 0.25 +
    relevance_score * 0.20
)
```

**Output:**
```python
@dataclass
class RankedRepo:
    repo: GitHubRepo
    final_score: float              # 0-100
    stars_score: float              # 0-100
    activity_score: float           # 0-100
    quality_score: float            # 0-100
    relevance_score: float          # 0-100
    ranking_rationale: str
```

---

## Updated Architecture Diagram

Добавил новый шаг перед Architecture Analysis:

```
1. GitHub Discovery & Research Layer ⭐
   - ResearchOrchestrator (координация)
   - WebResearcher (Exa deep research)
   - GitHubSearcher (GitHub API + Exa)
   - RepoRanker (scoring)
   ↓
2. Architecture Analysis Layer
   ↓
2.3 Skill Extraction & Teaching
   ↓
3. Solution Comparison Layer
```

---

## Updated find_github_solutions Method

**Before (stub):**
```python
async def find_github_solutions(self, subagent_name: str, query: str) -> list[str]:
    """Search GitHub for relevant solutions."""
    # Use GitHub API to search for repositories
    # Return list of repository URLs
    return []  # Stub
```

**After (full implementation):**
```python
async def find_github_solutions(
    self,
    subagent_name: str,
    query: str,
    research_depth: str = "standard"
) -> list[str]:
    """Search GitHub for relevant solutions using deep research."""
    
    # 1. Deep research через ResearchOrchestrator
    research_result = await self.research_orchestrator.research_topic(
        subagent_name=subagent_name,
        topic=query,
        research_depth=research_depth
    )
    
    # 2. Логирование результатов
    await self.obsidian.log(
        f"Research completed: {len(research_result.github_repos)} repos found",
        metadata={
            "topic": query,
            "depth": research_depth,
            "cost": research_result.research_cost,
            "best_practices": len(research_result.best_practices),
            "tools": len(research_result.tools_and_libraries)
        }
    )
    
    # 3. Возврат топ-5 репозиториев
    return [repo.url for repo in research_result.github_repos[:5]]
```

---

## Updated TeacherAgent.__init__

**Added:**
```python
class TeacherAgent:
    def __init__(self, event_bus: EventBus, obsidian: ObsidianVault):
        # NEW: Research orchestration
        self.research_orchestrator = ResearchOrchestrator()
        
        # NEW: Skill extraction orchestration
        self.skill_orchestrator = SkillExtractionOrchestrator()
        
        # Existing components
        self.architecture_analyzer = ArchitectureAnalyzer()
        self.solution_comparator = SolutionComparator()
        self.full_adopter = FullAdopter()
        # ...
```

---

## New CLI Commands

```bash
# NEW: Deep research command
python scripts/teacher_cli.py research <subagent_name> \
    --query "circuit breaker python" \
    --depth <quick|standard|deep>

# Output:
# Research completed in 12 minutes
# Cost: $1.50
# Found 15 GitHub repos
# Extracted 25 best practices
# Identified 12 tools/libraries
# Top 5 repos:
# 1. pybreaker/pybreaker (880 stars, score: 95/100)
# 2. Netflix/Hystrix (23k stars, score: 92/100)
# ...

# Updated: search with depth
python scripts/teacher_cli.py search <subagent_name> \
    --query "..." \
    --depth <quick|standard|deep>

# Updated: learn with depth
python scripts/teacher_cli.py learn <subagent_name> \
    --depth <quick|standard|deep>
```

---

## Key Differences: Before vs After

### Before (GitHub API Only)
```
GitHub API Search
   ↓
Get top repos by stars
   ↓
Return URLs
   ↓
No deep research
No best practices extraction
No industry insights
```

### After (Deep Research + GitHub) ⭐
```
Parallel Execution:
├─ WebResearcher (Exa deep research)
│  ├─ web_search_exa (20 results)
│  ├─ deep_researcher_start (analysis)
│  └─ Extract: best practices, tools, insights
│
└─ GitHubSearcher (dual search)
   ├─ GitHub API (official data)
   ├─ Exa search (additional repos)
   └─ Merge + deduplicate
   ↓
RepoRanker (scoring)
   ↓
Top 5 repos + research insights
```

---

## Example Workflow

**Scenario:** Analyzing circuit breaker implementations for SEO Agent

**Step 1: Deep Research (WebResearcher)**
```
Query: "circuit breaker python best practices"
Depth: standard ($1.50)

Exa web_search_exa:
- Found 20 articles/docs
- Sources: Martin Fowler, AWS, Netflix, Microsoft

Exa deep_researcher_start:
- Analyzed 20 sources
- Extracted 25 best practices:
  * Use half_open state for recovery
  * Implement exponential backoff
  * Monitor failure rate metrics
  * Set appropriate timeout thresholds
  * ...

- Identified 12 tools:
  * pybreaker (Python)
  * Hystrix (Java, reference)
  * resilience4j (Java, modern)
  * ...

- Industry insights:
  * Netflix uses 50% failure threshold
  * AWS recommends 60s reset timeout
  * Half-open state critical for recovery
  * ...
```

**Step 2: GitHub Search (GitHubSearcher)**
```
Query: "circuit breaker python"
Language: Python
Min stars: 100

GitHub API results:
1. pybreaker/pybreaker (880 stars)
2. shopify/semian (1.2k stars, Ruby but relevant)
3. ...

Exa search results:
1. pybreaker/pybreaker (duplicate)
2. some-user/circuit-breaker-py (150 stars, not in GitHub API)
3. ...

Merged: 15 unique repos
```

**Step 3: Ranking (RepoRanker)**
```
pybreaker/pybreaker:
  Stars: 880 → 88/100 (30 points * 0.88 = 26.4)
  Activity: 5 commits last month → 90/100 (25 points * 0.90 = 22.5)
  Quality: README, tests, CI, docs → 95/100 (25 points * 0.95 = 23.75)
  Relevance: exact match "circuit breaker" → 100/100 (20 points * 1.0 = 20.0)
  Final Score: 92.65/100

some-user/circuit-breaker-py:
  Stars: 150 → 15/100 (30 points * 0.15 = 4.5)
  Activity: 0 commits last 6 months → 0/100 (0)
  Quality: README only, no tests → 30/100 (25 points * 0.30 = 7.5)
  Relevance: exact match → 100/100 (20.0)
  Final Score: 32.0/100
```

**Step 4: Result**
```
Top 5 repos:
1. pybreaker/pybreaker (score: 92.65)
2. Netflix/Hystrix (score: 90.0, reference)
3. resilience4j/resilience4j (score: 88.5, Java but patterns)
4. ...

Best practices (25 total):
- Use half_open state for recovery
- Implement exponential backoff
- Monitor failure rate metrics
- ...

Tools (12 total):
- pybreaker (production-ready)
- tenacity (retry logic)
- prometheus-client (metrics)
- ...

Industry insights:
- Netflix: 50% failure threshold
- AWS: 60s reset timeout
- Microsoft: circuit breaker + bulkhead pattern
- ...

Research cost: $1.50
Time: 12 minutes
```

---

## Why This Is Critical

**User Requirement:**
> "Проверь, пожалуйста, он точно проводит глубокие исследования через поиск Brave, Exo или Perplexity. И ищет и исследования, и GitHub."

**Before:** Teacher использовал только GitHub API (stub implementation)  
**After:** Teacher проводит глубокое исследование через Exa + GitHub search

**Key Benefits:**
1. **Deep Research** - не только репозитории, но и best practices из статей/документации
2. **Dual Search** - GitHub API + Exa для максимального охвата
3. **Industry Insights** - что делают Netflix, AWS, Microsoft
4. **Tool Discovery** - находит не только репо, но и библиотеки/инструменты
5. **Cost Control** - 3 уровня глубины ($0.50 / $1.50 / $3.00)
6. **Quality Ranking** - не просто по звёздам, но по activity + quality + relevance

---

## Integration with Skill Extraction Layer

**Complete Workflow:**
```
1. GitHub Discovery & Research
   ↓ (top 5 repos + best practices)
2. Architecture Analysis
   ↓ (понимание структуры)
2.3 Skill Extraction
   ↓ (извлечение 10-20 skills)
   SkillComparator
   ↓ (сравнение каждого skill)
   SkillSelector
   ↓ (выбор лучших)
   SkillTeacher
   ↓ (обучение системы)
3. Solution Comparison
   ↓ (если нужно full adoption)
```

**Example:**
```
Research: "circuit breaker python"
  ↓
Found: pybreaker (880 stars, score 92.65)
Best practices: 25 (half_open state, exponential backoff, ...)
  ↓
Clone: git clone https://github.com/pybreaker/pybreaker
  ↓
Extract Skills:
- circuit_breaker (resilience): confidence 0.95
- exponential_backoff (resilience): confidence 0.90
- failure_rate_monitoring (observability): confidence 0.85
  ↓
Compare Each Skill:
- circuit_breaker: GitHub 85/100 vs Ours 60/100 → adopt
- exponential_backoff: GitHub 70/100 vs Ours 85/100 → keep_ours
  ↓
Teach Selected Skills:
- Adapt circuit_breaker pattern
- Use pybreaker library (production-ready)
- Integrate with Event Bus
- Add Obsidian logging
  ↓
Result: 95% reduction in cascading failures
```

---

## Success Metrics (Section 8.6)

**Research Coverage:**
- Target: 100% critical subagents researched before skill extraction

**Research Depth Distribution:**
- Quick: 20% (simple patterns)
- Standard: 60% (most cases)
- Deep: 20% (complex domains)

**Research Quality:**
- Target: 20+ sources per standard research
- Target: 15+ best practices extracted
- Target: 10+ tools/libraries identified

**GitHub Discovery:**
- Target: 10-20 repos found per search
- Target: Top 5 repos score > 80/100

**Cost Efficiency:**
- Target: Average research cost < $2.00
- Target: 80%+ research reusable across subagents

**Time Efficiency:**
- Quick: < 10 minutes
- Standard: 10-20 minutes
- Deep: 20-40 minutes

---

## Updated Implementation Phase

**Phase 1.0: GitHub Discovery & Research Layer (3-4 hours)**

**Tasks:**
1. Implement ResearchOrchestrator (coordination logic)
2. Implement WebResearcher (Exa MCP integration)
3. Implement GitHubSearcher (GitHub API + Exa dual search)
4. Implement RepoRanker (scoring algorithm)
5. Update find_github_solutions method
6. Write unit tests (15+ tests)
7. Write integration tests (research → ranking → top repos)

**Deliverable:** ResearchResult with top repos + best practices + tools

---

## Next Steps

1. ✅ GitHub Discovery & Research Layer added to spec
2. ✅ Skill Extraction & Teaching Layer added to spec
3. ⏳ Final user approval (Task #25)
4. ⏳ Begin Phase 1.0 implementation (3-4 hours)
5. ⏳ Begin Phase 1.5 implementation (4-5 hours)

---

## Recommendation

**READY FOR FINAL APPROVAL** ✅

Спецификация теперь полностью соответствует требованию пользователя:
- ✅ Глубокое исследование через Exa (web_search_exa + deep_researcher_start)
- ✅ Поиск GitHub репозиториев (GitHub API + Exa dual search)
- ✅ Извлечение best practices из исследований
- ✅ Ранжирование репозиториев по качеству
- ✅ Извлечение отдельных навыков (не копирование целых решений)
- ✅ Сравнение каждого навыка индивидуально
- ✅ Обучение системы конкретным паттернам
- ✅ Адаптация под нашу архитектуру (Event Bus, Obsidian)
- ✅ Измерение улучшения по каждому навыку

Можно начинать implementation после финального approval.

---

**Created:** 2026-05-13  
**Changes:** +417 lines, +14 KB  
**New Components:** 4 (ResearchOrchestrator, WebResearcher, GitHubSearcher, RepoRanker)  
**Status:** ✅ Complete - Ready for Final Approval
