# Teacher Agent v2.0 - Technical Specification

**Version:** 2.0.0  
**Status:** 📋 Specification  
**Created:** 2026-05-13  
**Author:** meAI Architect

---

## 1. Overview

### 1.1 Purpose

Teacher Agent v2.0 — полностью автономная система непрерывного обучения и улучшения субагентов через анализ и внедрение лучших практик из GitHub.

**Ключевое отличие от v1.0:** Полная автономия. Teacher САМ принимает решения о внедрении без user approval.

### 1.2 Scope

**В scope:**
- Автономный анализ GitHub решений (архитектура, код, тесты)
- **Извлечение отдельных навыков (skills) из решений** ⭐
- **Сравнение каждого навыка индивидуально (GitHub vs наш)** ⭐
- **Обучение системы конкретным паттернам (не копирование кода)** ⭐
- Автоматическое принятие решений (Full/Partial/Custom/Reject)
- Изолированное тестирование в sandbox (git worktree + venv)
- Автоматическая валидация (5 gates)
- Автоматическое внедрение при успешной валидации
- Автоматический rollback при проблемах
- Adoption сторонних агентов (если лучше наших)
- Audit trail всех решений
- Self-learning из результатов

**Вне scope:**
- Manual approval workflow
- Async approval queue
- User review gates
- Автоматическое внедрение без валидации
- Поддержка языков кроме Python
- Копирование кода без адаптации (только skill extraction + teaching)

### 1.3 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Teacher Agent v2.0                       │
│                   (Autonomous Learning System)               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │   1. GitHub Discovery & Ranking         │
        │   - Search top repos by topic           │
        │   - Rank by stars, activity, quality    │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │   2. Architecture Analysis Layer        │
        │   - FileStructureAnalyzer               │
        │   - ComponentRelationAnalyzer           │
        │   - DesignPatternDetector               │
        │   - TestCoverageAnalyzer                │
        │   → ArchitectureAnalysis (quality_score)│
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │   2.3 Skill Extraction & Teaching ⭐    │
        │   - SkillExtractor (find patterns)      │
        │   - SkillComparator (GitHub vs ours)    │
        │   - SkillSelector (choose best)         │
        │   - SkillTeacher (adapt & integrate)    │
        │   → Individual skill adoption           │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │   3. Solution Comparison Layer          │
        │   - ArchitectureScorer (modularity)     │
        │   - QualityScorer (patterns, docs)      │
        │   - FitAnalyzer (task match)            │
        │   - RiskAnalyzer (security, compliance) │
        │   → DecisionMaker (autonomous rules)    │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │   4. Decision (Autonomous)              │
        │   Quality ≥80, Fit ≥80, Risk ≤20        │
        │   → Full Adoption                       │
        │   Quality ≥70, Fit ≥70, Risk ≤30        │
        │   → Partial Adoption (adapt)            │
        │   Quality ≥60, Fit ≥60, Risk ≤40        │
        │   → Custom Development (reference)      │
        │   Below thresholds → Reject             │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │   5. Adoption Layer (if approved)       │
        │   - SandboxManager (git worktree)       │
        │   - FileCopier (adapt naming)           │
        │   - DependencyInstaller                 │
        │   - ImportUpdater                       │
        │   - TestMigrator                        │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │   6. Validation Gates (5 sequential)    │
        │   Gate 1: Sandbox Tests (all pass)      │
        │   Gate 2: Metrics Check (improve/same)  │
        │   Gate 3: Security Scan (no vulns)      │
        │   Gate 4: Compliance (HIPAA)            │
        │   Gate 5: Integration (Event Bus)       │
        └─────────────────────────────────────────┘
                              │
                 ┌────────────┴────────────┐
                 │                         │
                 ▼                         ▼
        ┌─────────────────┐      ┌─────────────────┐
        │  All Gates Pass │      │  Any Gate Fails │
        │  → Auto-Merge   │      │  → Auto-Rollback│
        └─────────────────┘      └─────────────────┘
                 │                         │
                 ▼                         ▼
        ┌─────────────────┐      ┌─────────────────┐
        │ Adoption Report │      │ Failure Report  │
        │ + Notification  │      │ + Notification  │
        └─────────────────┘      └─────────────────┘
```

### 1.4 Integration with meAI Framework

**Teacher Agent** интегрируется с существующей архитектурой:

```
meAI Framework
├── Architect (Strategy Layer)
├── Operator (Tactical Layer)
├── Magisters (Domain Layer)
│   ├── SEO Magister
│   ├── Content Magister
│   └── Ads Magister
├── Subagents (Execution Layer)
│   └── [Teacher улучшает эти агенты]
└── Teacher Agent (Learning Layer) ← NEW
    └── Непрерывное обучение системы
```

**Взаимодействие:**
- Teacher читает спецификации субагентов из `docs/subagents-specs/`
- Анализирует реализацию в `AIM/src/aim/subagents/`
- Ищет улучшения на GitHub
- Автономно внедряет улучшения
- Логирует решения в `obsidian/teacher/`
- Отправляет notifications через Event Bus

### 1.5 Obsidian Vault Structure

```
obsidian/teacher/
├── wiki/
│   ├── index.md                    # Каталог всех страниц
│   ├── log.md                      # Хронология операций
│   ├── concepts/
│   │   ├── autonomous-learning.md  # Концепция автономного обучения
│   │   ├── decision-framework.md   # Framework принятия решений
│   │   └── validation-gates.md     # Validation gates
│   ├── technologies/
│   │   ├── github-api.md           # GitHub API integration
│   │   ├── ast-analysis.md         # AST analysis tools
│   │   └── git-worktree.md         # Git worktree для sandbox
│   ├── strategies/
│   │   ├── adoption-strategy.md    # Стратегия внедрения
│   │   ├── rollback-strategy.md    # Стратегия rollback
│   │   └── learning-strategy.md    # Стратегия обучения
│   ├── agents/
│   │   └── subagents-profile.md    # Профили субагентов
│   ├── workflows/
│   │   ├── discovery.md            # GitHub discovery workflow
│   │   ├── analysis.md             # Architecture analysis workflow
│   │   ├── adoption.md             # Adoption workflow
│   │   └── rollback.md             # Rollback workflow
│   ├── projects/
│   │   └── adoptions/              # История adoptions
│   │       ├── YYYY-MM-DD-agent-name.md
│   │       └── ...
│   └── connections/
│       └── learning-cycles.md      # Связи между циклами обучения
├── decisions/
│   ├── adoption-decisions.md       # История решений о внедрении
│   ├── rejection-reasons.md        # Причины отказов
│   └── learning-insights.md        # Инсайты из обучения
└── raw/
    └── github-repos/               # Клонированные репо для анализа
```

---

## 2. Core Components

### 2.0 GitHub Discovery & Research Layer

**КРИТИЧЕСКИ ВАЖНО:** Teacher Agent должен проводить глубокие исследования через Brave/Exa/Perplexity для поиска лучших GitHub решений.

**Принцип:** Не просто искать по GitHub API → Глубокое исследование темы → Находить топовые репозитории → Анализировать каждый.

#### 2.0.1 ResearchOrchestrator

**Purpose:** Оркестрация глубокого исследования темы через multiple sources.

**Input:**
```python
subagent_name: str              # Имя субагента (e.g., "seo_analyzer")
topic: str                      # Тема для исследования (e.g., "SEO analysis Python")
research_depth: str             # "quick" | "standard" | "deep"
```

**Output:**
```python
@dataclass
class ResearchResult:
    topic: str
    github_repos: list[GitHubRepo]          # Топовые репозитории
    best_practices: list[str]               # Лучшие практики из статей
    tools_and_libraries: list[str]          # Инструменты и библиотеки
    industry_insights: list[str]            # Инсайты индустрии
    research_sources: list[str]             # Источники (URLs)
    research_timestamp: datetime
    research_cost: float                    # Стоимость исследования ($)
```

**Workflow:**
1. **Web Research** (Brave/Exa/Perplexity) → best practices, tools, insights
2. **GitHub Search** (GitHub API + Exa) → top repositories
3. **Rank & Filter** → select top 5-10 repos
4. **Return** ResearchResult

**Implementation:**
```python
class ResearchOrchestrator:
    def __init__(self):
        self.web_researcher = WebResearcher()      # Brave/Exa/Perplexity
        self.github_searcher = GitHubSearcher()    # GitHub API + Exa
        self.repo_ranker = RepoRanker()
    
    async def research_topic(
        self,
        subagent_name: str,
        topic: str,
        research_depth: str = "standard"
    ) -> ResearchResult:
        # 1. Web research (parallel)
        web_results = await self.web_researcher.research(
            topic=topic,
            depth=research_depth,
            focus=["best practices", "tools", "libraries", "patterns"]
        )
        
        # 2. GitHub search (parallel)
        github_results = await self.github_searcher.search(
            query=topic,
            language="Python",
            min_stars=100,
            max_results=20
        )
        
        # 3. Rank repositories
        ranked_repos = await self.repo_ranker.rank(
            repos=github_results,
            criteria=["stars", "activity", "quality", "relevance"]
        )
        
        # 4. Select top repos
        top_repos = ranked_repos[:10]
        
        return ResearchResult(
            topic=topic,
            github_repos=top_repos,
            best_practices=web_results.best_practices,
            tools_and_libraries=web_results.tools,
            industry_insights=web_results.insights,
            research_sources=web_results.sources + [r.url for r in top_repos],
            research_timestamp=datetime.now(),
            research_cost=web_results.cost
        )
```

#### 2.0.2 WebResearcher

**Purpose:** Глубокое исследование темы через Brave/Exa/Perplexity.

**Input:**
```python
topic: str                      # "SEO analysis Python"
depth: str                      # "quick" | "standard" | "deep"
focus: list[str]                # ["best practices", "tools", "patterns"]
```

**Output:**
```python
@dataclass
class WebResearchResult:
    best_practices: list[str]               # Лучшие практики
    tools: list[str]                        # Инструменты и библиотеки
    insights: list[str]                     # Инсайты индустрии
    sources: list[str]                      # URLs источников
    cost: float                             # Стоимость ($)
```

**Research Strategy:**

**Quick (5-10 minutes, ~$0.50):**
- Exa web_search_exa: 10 results
- Extract key points from top 5 articles
- Focus: tools, libraries, top repos

**Standard (10-20 minutes, ~$1.50):**
- Exa web_search_exa: 20 results
- Exa deep_researcher_start: "standard" model
- Extract: best practices, tools, patterns, insights
- Focus: comprehensive overview

**Deep (20-40 minutes, ~$3.00):**
- Exa web_search_exa: 30 results
- Exa deep_researcher_start: "pro" model
- Multiple research angles:
  - Best practices and patterns
  - Production implementations
  - Performance optimization
  - Security considerations
  - Industry trends
- Focus: deep understanding, edge cases, trade-offs

**Implementation:**
```python
class WebResearcher:
    def __init__(self):
        self.exa_client = ExaClient()
        self.brave_client = BraveClient()  # Fallback
    
    async def research(
        self,
        topic: str,
        depth: str = "standard",
        focus: list[str] = None
    ) -> WebResearchResult:
        if depth == "quick":
            return await self._quick_research(topic, focus)
        elif depth == "standard":
            return await self._standard_research(topic, focus)
        else:  # deep
            return await self._deep_research(topic, focus)
    
    async def _quick_research(
        self,
        topic: str,
        focus: list[str]
    ) -> WebResearchResult:
        # Exa web search
        search_results = await self.exa_client.web_search_exa(
            query=f"{topic} best practices tools libraries",
            numResults=10
        )
        
        # Extract key points from top 5
        best_practices = []
        tools = []
        insights = []
        
        for result in search_results[:5]:
            # Parse content
            if "best practice" in result.text.lower():
                best_practices.extend(self._extract_practices(result.text))
            if "library" in result.text.lower() or "tool" in result.text.lower():
                tools.extend(self._extract_tools(result.text))
        
        return WebResearchResult(
            best_practices=best_practices,
            tools=tools,
            insights=insights,
            sources=[r.url for r in search_results[:5]],
            cost=0.50
        )
    
    async def _standard_research(
        self,
        topic: str,
        focus: list[str]
    ) -> WebResearchResult:
        # 1. Exa web search (broader)
        search_results = await self.exa_client.web_search_exa(
            query=f"{topic} {' '.join(focus)}",
            numResults=20
        )
        
        # 2. Deep research with Exa
        research_prompt = f"""
        Research topic: {topic}
        
        Focus areas:
        {chr(10).join(f'- {f}' for f in focus)}
        
        Please provide:
        1. Best practices and patterns
        2. Popular tools and libraries
        3. Industry insights and trends
        4. Production implementation examples
        """
        
        research_id = await self.exa_client.deep_researcher_start(
            instructions=research_prompt,
            model="exa-research"  # Standard model
        )
        
        # Wait for completion
        research_result = await self._wait_for_research(research_id)
        
        # Parse research result
        best_practices = self._extract_practices(research_result)
        tools = self._extract_tools(research_result)
        insights = self._extract_insights(research_result)
        
        return WebResearchResult(
            best_practices=best_practices,
            tools=tools,
            insights=insights,
            sources=[r.url for r in search_results] + [research_result.source],
            cost=1.50
        )
    
    async def _deep_research(
        self,
        topic: str,
        focus: list[str]
    ) -> WebResearchResult:
        # 1. Exa web search (comprehensive)
        search_results = await self.exa_client.web_search_exa(
            query=f"{topic} {' '.join(focus)} production implementation",
            numResults=30
        )
        
        # 2. Multiple deep research angles
        research_angles = [
            "Best practices and design patterns",
            "Production implementations and case studies",
            "Performance optimization techniques",
            "Security considerations and compliance",
            "Industry trends and future directions"
        ]
        
        research_results = []
        for angle in research_angles:
            research_prompt = f"""
            Research topic: {topic}
            Angle: {angle}
            
            Provide detailed analysis with:
            - Specific examples and code patterns
            - Trade-offs and considerations
            - Real-world implementations
            - Edge cases and pitfalls
            """
            
            research_id = await self.exa_client.deep_researcher_start(
                instructions=research_prompt,
                model="exa-research-pro"  # Pro model for deep research
            )
            
            result = await self._wait_for_research(research_id)
            research_results.append(result)
        
        # Synthesize all research
        best_practices = []
        tools = []
        insights = []
        
        for result in research_results:
            best_practices.extend(self._extract_practices(result))
            tools.extend(self._extract_tools(result))
            insights.extend(self._extract_insights(result))
        
        # Deduplicate
        best_practices = list(set(best_practices))
        tools = list(set(tools))
        insights = list(set(insights))
        
        return WebResearchResult(
            best_practices=best_practices,
            tools=tools,
            insights=insights,
            sources=[r.url for r in search_results] + [r.source for r in research_results],
            cost=3.00
        )
    
    async def _wait_for_research(self, research_id: str) -> dict:
        """Wait for deep research to complete."""
        while True:
            result = await self.exa_client.deep_researcher_check(research_id)
            if result["status"] == "completed":
                return result
            await asyncio.sleep(5)
```

#### 2.0.3 GitHubSearcher

**Purpose:** Поиск топовых GitHub репозиториев по теме.

**Input:**
```python
query: str                      # "SEO analysis Python"
language: str                   # "Python"
min_stars: int                  # 100
max_results: int                # 20
```

**Output:**
```python
@dataclass
class GitHubRepo:
    url: str                            # https://github.com/user/repo
    name: str                           # user/repo
    description: str
    stars: int
    forks: int
    last_updated: datetime
    language: str
    topics: list[str]
    readme_summary: str                 # First 500 chars of README
```

**Search Strategy:**

1. **GitHub API Search:**
   - Query: `{query} language:{language} stars:>={min_stars}`
   - Sort by: stars, updated
   - Filter: active repos (updated in last 6 months)

2. **Exa GitHub Search (parallel):**
   - Query: `{query} site:github.com`
   - Extract repo URLs
   - Cross-reference with GitHub API results

3. **Merge & Deduplicate:**
   - Combine results from both sources
   - Remove duplicates
   - Return top N by stars

**Implementation:**
```python
class GitHubSearcher:
    def __init__(self):
        self.github_client = GitHubAPIClient()
        self.exa_client = ExaClient()
    
    async def search(
        self,
        query: str,
        language: str = "Python",
        min_stars: int = 100,
        max_results: int = 20
    ) -> list[GitHubRepo]:
        # 1. GitHub API search
        github_results = await self.github_client.search_repositories(
            query=f"{query} language:{language} stars:>={min_stars}",
            sort="stars",
            order="desc",
            per_page=max_results
        )
        
        # 2. Exa search (parallel)
        exa_results = await self.exa_client.web_search_exa(
            query=f"{query} site:github.com",
            numResults=max_results
        )
        
        # 3. Parse Exa results to extract GitHub URLs
        exa_repos = []
        for result in exa_results:
            if "github.com" in result.url:
                repo_info = await self.github_client.get_repo_info(result.url)
                if repo_info and repo_info.stars >= min_stars:
                    exa_repos.append(repo_info)
        
        # 4. Merge and deduplicate
        all_repos = github_results + exa_repos
        unique_repos = {repo.url: repo for repo in all_repos}.values()
        
        # 5. Sort by stars
        sorted_repos = sorted(unique_repos, key=lambda r: r.stars, reverse=True)
        
        return sorted_repos[:max_results]
```

#### 2.0.4 RepoRanker

**Purpose:** Ранжирование репозиториев по качеству и релевантности.

**Input:**
```python
repos: list[GitHubRepo]
criteria: list[str]             # ["stars", "activity", "quality", "relevance"]
```

**Output:**
```python
@dataclass
class RankedRepo:
    repo: GitHubRepo
    rank_score: float               # 0-100
    stars_score: float              # 0-100
    activity_score: float           # 0-100
    quality_score: float            # 0-100
    relevance_score: float          # 0-100
```

**Ranking Criteria:**

**Stars Score (0-100):**
- Linear scale: 100 stars = 0, 10000+ stars = 100
- Formula: `min(100, (stars - 100) / 100)`

**Activity Score (0-100):**
- Last commit within 1 month: 100
- Last commit within 3 months: 80
- Last commit within 6 months: 60
- Last commit within 1 year: 40
- Older: 20

**Quality Score (0-100):**
- Has README: +20
- Has tests: +20
- Has CI/CD: +20
- Has documentation: +20
- Has examples: +20

**Relevance Score (0-100):**
- Topic match: +30 (if repo topics match query)
- Description match: +30 (semantic similarity)
- Language match: +20 (if language matches)
- Recent activity: +20 (updated in last 3 months)

**Overall Rank Score:**
```python
rank_score = (
    stars_score * 0.30 +
    activity_score * 0.25 +
    quality_score * 0.25 +
    relevance_score * 0.20
)
```

**Implementation:**
```python
class RepoRanker:
    async def rank(
        self,
        repos: list[GitHubRepo],
        criteria: list[str]
    ) -> list[RankedRepo]:
        ranked = []
        
        for repo in repos:
            stars_score = self._score_stars(repo.stars)
            activity_score = self._score_activity(repo.last_updated)
            quality_score = await self._score_quality(repo)
            relevance_score = self._score_relevance(repo)
            
            rank_score = (
                stars_score * 0.30 +
                activity_score * 0.25 +
                quality_score * 0.25 +
                relevance_score * 0.20
            )
            
            ranked.append(RankedRepo(
                repo=repo,
                rank_score=rank_score,
                stars_score=stars_score,
                activity_score=activity_score,
                quality_score=quality_score,
                relevance_score=relevance_score
            ))
        
        # Sort by rank_score
        return sorted(ranked, key=lambda r: r.rank_score, reverse=True)
```

---

### 2.1 Architecture Analysis Layer

#### 2.1.1 FileStructureAnalyzer

**Purpose:** Анализ структуры файлов и директорий GitHub решения.

**Input:**
```python
repo_path: Path  # Путь к клонированному репо
```

**Output:**
```python
@dataclass
class FileStructure:
    entry_points: list[str]      # main.py, __init__.py, app.py
    clients: list[str]            # *client.py, *api.py
    models: list[str]             # *model.py, *schema.py, *entity.py
    tests: list[str]              # test_*.py, *_test.py
    configs: list[str]            # settings.py, config.py, .env
    utils: list[str]              # utils/, helpers/, common/
    docs: list[str]               # README.md, docs/, *.md
    total_files: int              # Общее количество файлов
    total_lines: int              # Общее количество строк кода
```

**Algorithm:**
1. Сканировать директории рекурсивно (pathlib.rglob("*.py"))
2. Классифицировать файлы по назначению используя regex patterns:
   - clients: r".*/(client|api|service)s?/.*\.py"
   - models: r".*/(model|schema|entity)s?/.*\.py"
   - utils: r".*/(util|helper|tool)s?/.*\.py"
   - tests: r".*/tests?/.*\.py|.*test_.*\.py|.*_test\.py"
   - config: r".*/(config|setting)s?/.*\.py"
   - core: r".*/core/.*\.py"
3. Подсчитать метрики (файлы, строки кода без комментариев)
4. Определить entry points (main.py, __main__.py, app.py, cli.py)

**Implementation:**
```python
class FileStructureAnalyzer:
    def analyze(self, repo_path: Path) -> FileStructure:
        # Scan directory tree
        # Classify files by patterns
        # Count metrics
        # Return FileStructure
```

#### 2.1.2 ComponentRelationAnalyzer

**Purpose:** Построение графа зависимостей между модулями.

**Input:**
```python
repo_path: Path
file_structure: FileStructure
```

**Output:**
```python
@dataclass
class ComponentRelations:
    dependency_graph: dict[str, list[str]]  # module_path -> [dependency_module_paths]
    coupling_score: float                    # 0-100: (edges / nodes) * 100, normalized
    circular_deps: list[tuple[str, str]]    # Circular dependencies
    core_components: list[str]               # Most depended upon (in-degree >= 3)
    peripheral_components: list[str]         # Least depended upon (in-degree <= 1)
```


**Algorithm:**
1. Parse imports из всех Python файлов (AST)
2. Построить граф зависимостей (networkx): nodes = module paths, edges = imports
3. Найти circular dependencies (networkx.simple_cycles)
4. Вычислить coupling score: (num_edges / num_nodes) * 100, clamped to 0-100
5. Определить core vs peripheral: core if in-degree >= 3, peripheral if in-degree <= 1

**Implementation:**
```python
class ComponentRelationAnalyzer:
    def analyze(self, repo_path: Path, file_structure: FileStructure) -> ComponentRelations:
        # Parse imports with AST
        # Build dependency graph
        # Detect circular dependencies
        # Calculate coupling score
        # Identify core components
        # Return ComponentRelations
```

#### 2.1.3 DesignPatternDetector

**Purpose:** Детектирование паттернов проектирования и архитектурных стилей.

**Input:**
```python
repo_path: Path
component_relations: ComponentRelations
```

**Output:**
```python
@dataclass
class DesignPatterns:
    patterns: list[str]                      # ["Strategy", "Factory", "Observer"]
    architecture_style: str                  # "Layered" | "Hexagonal" | "Clean" | "MVC" | "Microservices" | "Event-Driven" | "CQRS"
    solid_compliance: dict[str, bool]        # S, O, L, I, D principles
    pattern_confidence: dict[str, float]     # Pattern -> confidence (0-1)
```

**Patterns to Detect:**
- **Strategy:** Multiple implementations of same interface
- **Factory:** Creation methods returning different types
- **Observer:** Event/callback patterns
- **Singleton:** Single instance patterns
- **Dependency Injection:** Constructor injection
- **Repository:** Data access abstraction
- **Circuit Breaker:** Fault tolerance pattern

**Algorithm:**
1. Analyze class hierarchies (AST: ClassDef nodes, bases attribute for inheritance)
2. Detect creation patterns:
   - Factory: methods named create_*, build_*, make_* returning different types
   - Builder: methods returning self for chaining
3. Find event/callback patterns:
   - Observer: methods named on_*, handle_*, callback with function args
   - Event Bus: publish/subscribe method pairs
4. Check SOLID principles:
   - SRP: class has single responsibility (low method count, focused naming)
   - OCP: uses inheritance/composition (abstract base classes)
   - LSP: subclasses don't break parent contracts (no NotImplementedError in overrides)
   - ISP: small focused interfaces (ABC with few methods)
   - DIP: depends on abstractions (imports from .base, .interface modules)
5. Determine architecture style:
   - Layered: dependency direction top-down (presentation → business → data)
   - Hexagonal: core has no external dependencies (ports/adapters pattern)
   - Clean: dependency inversion (domain independent of infrastructure)
   - Event-Driven: event bus usage, async handlers

**Implementation:**
```python
class DesignPatternDetector:
    def detect(self, repo_path: Path, component_relations: ComponentRelations) -> DesignPatterns:
        # Analyze class hierarchies
        # Detect patterns with heuristics
        # Check SOLID compliance
        # Determine architecture style
        # Return DesignPatterns with confidence
```

#### 2.1.4 TestCoverageAnalyzer

**Purpose:** Анализ структуры и покрытия тестов.

**Input:**
```python
repo_path: Path
file_structure: FileStructure
```

**Output:**
```python
@dataclass
class TestCoverage:
    test_types: dict[str, int]               # {"unit": 50, "integration": 10, "e2e": 5}
    coverage_estimate: float                 # 0-100: (test_count / function_count) * 100
    has_fixtures: bool                       # pytest fixtures detected
    has_mocks: bool                          # unittest.mock or pytest-mock detected
    test_scenarios: list[str]                # Extracted from test names
    test_quality_score: float                # 0-100: (assertions_per_test * 0.4 + fixture_usage * 0.3 + mock_usage * 0.3) * 100
```

**Algorithm:**
1. Найти все test файлы (test_*.py, *_test.py)
2. Классифицировать тесты (unit, integration, e2e) по patterns:
   - unit: test functions without external dependencies (no db, no api calls)
   - integration: test functions with db/api mocks or fixtures
   - e2e: test functions with full system setup (no mocks)
3. Подсчитать coverage_estimate: (total_test_count / total_function_count) * 100
4. Детектировать fixtures (pytest.fixture decorator) и mocks (unittest.mock, pytest-mock imports)
5. Извлечь test scenarios из имён тестов (test_should_*, test_when_*, test_given_*)
6. Оценить test_quality_score: (assertions_per_test * 0.4 + fixture_usage * 0.3 + mock_usage * 0.3) * 100

**Implementation:**
```python
class TestCoverageAnalyzer:
    def analyze(self, repo_path: Path, file_structure: FileStructure) -> TestCoverage:
        # Find test files
        # Classify test types
        # Estimate coverage
        # Detect fixtures and mocks
        # Extract test scenarios
        # Calculate test quality score
        # Return TestCoverage
```

#### 2.1.5 ArchitectureAnalyzer (Orchestrator)

**Purpose:** Оркестрация всех sub-analyzers и агрегация результатов.

**Input:**
```python
repo_path: Path
```

**Output:**
```python
@dataclass
class ArchitectureAnalysis:
    file_structure: FileStructure
    component_relations: ComponentRelations
    design_patterns: DesignPatterns
    test_coverage: TestCoverage
    quality_score: float                     # 0-100 (weighted average)
    analysis_timestamp: datetime
    repo_url: str
```

**Quality Score Calculation:**
```python
quality_score = (
    file_structure_score * 0.15 +           # Структура (15%)
    coupling_score * 0.25 +                  # Coupling (25%)
    pattern_score * 0.20 +                   # Patterns (20%)
    test_coverage_score * 0.30 +             # Tests (30%)
    documentation_score * 0.10               # Docs (10%)
)
```

**Implementation:**
```python
class ArchitectureAnalyzer:
    def __init__(self):
        self.file_analyzer = FileStructureAnalyzer()
        self.relation_analyzer = ComponentRelationAnalyzer()
        self.pattern_detector = DesignPatternDetector()
        self.test_analyzer = TestCoverageAnalyzer()
    
    async def analyze(self, repo_path: Path, repo_url: str) -> ArchitectureAnalysis:
        # Run all analyzers in parallel
        file_structure = await self.file_analyzer.analyze(repo_path)
        component_relations = await self.relation_analyzer.analyze(repo_path, file_structure)
        design_patterns = await self.pattern_detector.detect(repo_path, component_relations)
        test_coverage = await self.test_analyzer.analyze(repo_path, file_structure)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(
            file_structure, component_relations, design_patterns, test_coverage
        )
        
        return ArchitectureAnalysis(
            file_structure=file_structure,
            component_relations=component_relations,
            design_patterns=design_patterns,
            test_coverage=test_coverage,
            quality_score=quality_score,
            analysis_timestamp=datetime.now(),
            repo_url=repo_url
        )
```

---

## 2.3 Skill Extraction & Teaching Layer

**КРИТИЧЕСКИ ВАЖНО:** Teacher Agent должен извлекать и обучать ОТДЕЛЬНЫМ НАВЫКАМ (skills), а не просто копировать целые решения.

**Принцип:** Разбираем GitHub решения до молекул → Берём только лучшие навыки → Учим нашу систему конкретным паттернам.

### 2.3.1 SkillExtractor

**Purpose:** Извлечение конкретных навыков (skills) из GitHub решений.

**Input:**
```python
repo_path: Path
architecture_analysis: ArchitectureAnalysis
```

**Output:**
```python
@dataclass
class ExtractedSkill:
    name: str                           # "circuit_breaker", "retry_logic", "rate_limiting"
    category: str                       # "resilience" | "performance" | "security" | "observability" | "error_handling"
    implementation: str                 # Код реализации (функция/класс)
    dependencies: list[str]             # Внешние зависимости (pybreaker, tenacity, etc.)
    usage_examples: list[str]           # Примеры использования из репо
    metrics: dict[str, float]           # Метрики (latency_ms, success_rate, etc.)
    confidence: float                   # 0-1 (уверенность в качестве)
    source_file: str                    # Путь к файлу в репо
    source_lines: tuple[int, int]       # Диапазон строк (start, end)

@dataclass
class SkillExtractionResult:
    skills: list[ExtractedSkill]        # Все найденные навыки
    categories: dict[str, int]          # Категория -> количество
    total_skills: int
    extraction_timestamp: datetime
```

**Skill Categories:**

1. **Resilience (устойчивость):**
   - Circuit Breaker (защита от каскадных сбоев)
   - Retry Logic (повторные попытки с backoff)
   - Timeout Handling (таймауты для операций)
   - Fallback Mechanisms (запасные варианты)
   - Bulkhead Pattern (изоляция ресурсов)

2. **Performance (производительность):**
   - Caching (кеширование ответов)
   - Connection Pooling (пул соединений)
   - Lazy Loading (отложенная загрузка)
   - Batch Processing (пакетная обработка)
   - Async/Await Patterns (асинхронность)

3. **Security (безопасность):**
   - Input Validation (валидация входных данных)
   - SQL Injection Prevention (защита от SQL injection)
   - XSS Prevention (защита от XSS)
   - Secret Management (управление секретами)
   - Rate Limiting (ограничение запросов)

4. **Observability (наблюдаемость):**
   - Structured Logging (структурированные логи)
   - Metrics Collection (сбор метрик)
   - Distributed Tracing (трассировка)
   - Health Checks (проверки здоровья)
   - Error Tracking (отслеживание ошибок)

5. **Error Handling (обработка ошибок):**
   - Custom Exceptions (кастомные исключения)
   - Error Recovery (восстановление после ошибок)
   - Graceful Degradation (плавная деградация)
   - Error Reporting (отчёты об ошибках)
   - Dead Letter Queue (очередь неудачных задач)

**Detection Heuristics:**

```python
# Circuit Breaker
if "circuit" in code.lower() or "breaker" in code.lower():
    if has_state_machine(code) and has_failure_threshold(code):
        skill = "circuit_breaker"

# Retry Logic
if "retry" in code.lower() or "tenacity" in imports:
    if has_exponential_backoff(code) or has_max_attempts(code):
        skill = "retry_logic"

# Rate Limiting
if "rate" in code.lower() and "limit" in code.lower():
    if has_token_bucket(code) or has_sliding_window(code):
        skill = "rate_limiting"

# Caching
if "cache" in code.lower() or "redis" in imports or "memcached" in imports:
    if has_ttl(code) or has_invalidation(code):
        skill = "caching"

# Structured Logging
if "structlog" in imports or "loguru" in imports:
    if has_context_binding(code) or has_json_output(code):
        skill = "structured_logging"
```

**Algorithm:**
1. Сканировать все Python файлы в репо
2. Для каждого файла:
   - Парсить AST (функции, классы, декораторы)
   - Искать паттерны по heuristics
   - Извлекать код реализации
   - Найти примеры использования (в tests/ или examples/)
   - Извлечь метрики (если есть в коде или документации)
3. Группировать навыки по категориям
4. Оценить confidence (0-1) на основе:
   - Полнота реализации (0.3)
   - Наличие тестов (0.3)
   - Наличие документации (0.2)
   - Наличие примеров (0.2)

**Implementation:**
```python
class SkillExtractor:
    def __init__(self):
        self.heuristics = self._load_heuristics()
    
    async def extract_skills(
        self,
        repo_path: Path,
        architecture_analysis: ArchitectureAnalysis
    ) -> SkillExtractionResult:
        skills = []
        
        # Scan all Python files
        for file_path in repo_path.rglob("*.py"):
            # Parse AST
            tree = ast.parse(file_path.read_text())
            
            # Detect skills using heuristics
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    detected_skills = self._detect_skills(node, file_path)
                    skills.extend(detected_skills)
        
        # Group by category
        categories = {}
        for skill in skills:
            categories[skill.category] = categories.get(skill.category, 0) + 1
        
        return SkillExtractionResult(
            skills=skills,
            categories=categories,
            total_skills=len(skills),
            extraction_timestamp=datetime.now()
        )
    
    def _detect_skills(self, node: ast.AST, file_path: Path) -> list[ExtractedSkill]:
        # Apply heuristics to detect skills
        # Extract implementation code
        # Find usage examples
        # Calculate confidence
        pass
```

### 2.3.2 SkillComparator

**Purpose:** Сравнение каждого навыка индивидуально (GitHub vs наш).

**Input:**
```python
github_skill: ExtractedSkill
our_repo_path: Path
our_architecture_analysis: ArchitectureAnalysis
```

**Output:**
```python
@dataclass
class SkillComparison:
    skill_name: str                     # "circuit_breaker"
    category: str                       # "resilience"
    github_score: float                 # 0-100
    our_score: float                    # 0-100 (0 если нет у нас)
    winner: str                         # "github" | "ours" | "tie" | "missing"
    delta: float                        # github_score - our_score
    reasoning: str                      # Почему один лучше другого
    adoption_recommendation: str        # "adopt" | "keep_ours" | "hybrid" | "skip"
    github_implementation: str          # Код из GitHub
    our_implementation: str | None      # Код из нашей системы (если есть)
```

**Scoring Criteria (0-100 per skill):**

1. **Implementation Quality (40 points):**
   - Полнота реализации: 0-15
   - Обработка edge cases: 0-10
   - Код читаемый и понятный: 0-10
   - Следует best practices: 0-5

2. **Testing (25 points):**
   - Unit тесты есть: +10
   - Integration тесты есть: +10
   - Test coverage > 80%: +5

3. **Documentation (15 points):**
   - Docstrings есть: +5
   - Примеры использования: +5
   - Inline комментарии для сложных мест: +5

4. **Performance (10 points):**
   - Метрики производительности указаны: +5
   - Оптимизирован для production: +5

5. **Maintainability (10 points):**
   - Конфигурируемый (не hardcoded): +5
   - Легко интегрируется: +5

**Decision Rules:**

```python
# Adopt GitHub skill
if github_score > our_score + 10:  # Минимум 10 points разница
    return "adopt"

# Keep our skill
elif our_score > github_score + 10:
    return "keep_ours"

# Hybrid (взять лучшее из обоих)
elif abs(github_score - our_score) <= 10 and both_have_unique_features:
    return "hybrid"

# Skip (оба плохие или не нужно)
else:
    return "skip"
```

**Algorithm:**
1. Найти аналогичный навык в нашей системе (по имени и категории)
2. Если не найден → our_score = 0, winner = "github", recommendation = "adopt"
3. Если найден:
   - Оценить GitHub implementation (0-100)
   - Оценить our implementation (0-100)
   - Сравнить scores
   - Определить winner
   - Сгенерировать reasoning
   - Дать recommendation

**Implementation:**
```python
class SkillComparator:
    async def compare_skill(
        self,
        github_skill: ExtractedSkill,
        our_repo_path: Path,
        our_architecture_analysis: ArchitectureAnalysis
    ) -> SkillComparison:
        # Find our implementation of same skill
        our_skill = await self._find_our_skill(
            github_skill.name,
            github_skill.category,
            our_repo_path
        )
        
        # Score GitHub implementation
        github_score = self._score_implementation(github_skill)
        
        # Score our implementation (0 if not found)
        our_score = 0
        our_implementation = None
        if our_skill:
            our_score = self._score_implementation(our_skill)
            our_implementation = our_skill.implementation
        
        # Determine winner
        if our_score == 0:
            winner = "missing"
            recommendation = "adopt"
        elif github_score > our_score + 10:
            winner = "github"
            recommendation = "adopt"
        elif our_score > github_score + 10:
            winner = "ours"
            recommendation = "keep_ours"
        elif abs(github_score - our_score) <= 10:
            winner = "tie"
            recommendation = "hybrid"
        else:
            winner = "tie"
            recommendation = "skip"
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            github_skill, our_skill, github_score, our_score
        )
        
        return SkillComparison(
            skill_name=github_skill.name,
            category=github_skill.category,
            github_score=github_score,
            our_score=our_score,
            winner=winner,
            delta=github_score - our_score,
            reasoning=reasoning,
            adoption_recommendation=recommendation,
            github_implementation=github_skill.implementation,
            our_implementation=our_implementation
        )
```

### 2.3.3 SkillSelector

**Purpose:** Выбор только лучших навыков для внедрения.

**Input:**
```python
skill_comparisons: list[SkillComparison]
adoption_strategy: str  # "aggressive" | "conservative" | "balanced"
```

**Output:**
```python
@dataclass
class SkillSelectionResult:
    skills_to_adopt: list[SkillComparison]      # Навыки для внедрения
    skills_to_keep: list[SkillComparison]       # Наши навыки лучше
    skills_to_hybrid: list[SkillComparison]     # Гибридный подход
    skills_to_skip: list[SkillComparison]       # Пропустить
    total_improvement: float                     # Ожидаемое улучшение (%)
    selection_rationale: str                     # Обоснование выбора
```

**Selection Strategies:**

1. **Aggressive (берём всё, что лучше):**
   - Adopt if github_score > our_score + 5
   - Риск: может сломать существующую систему
   - Польза: максимальное улучшение

2. **Conservative (берём только явно лучшее):**
   - Adopt if github_score > our_score + 20
   - Риск: минимальный
   - Польза: только проверенные улучшения

3. **Balanced (золотая середина):**
   - Adopt if github_score > our_score + 10
   - Риск: умеренный
   - Польза: значимые улучшения

**Algorithm:**
1. Фильтровать comparisons по adoption_strategy
2. Группировать по recommendation (adopt, keep_ours, hybrid, skip)
3. Рассчитать total_improvement:
   ```python
   total_improvement = sum(
       (comp.github_score - comp.our_score) / comp.our_score * 100
       for comp in skills_to_adopt
       if comp.our_score > 0
   ) / len(skills_to_adopt)
   ```
4. Сгенерировать selection_rationale

**Implementation:**
```python
class SkillSelector:
    def select_skills(
        self,
        skill_comparisons: list[SkillComparison],
        adoption_strategy: str = "balanced"
    ) -> SkillSelectionResult:
        # Define threshold based on strategy
        threshold = {
            "aggressive": 5,
            "conservative": 20,
            "balanced": 10
        }[adoption_strategy]
        
        # Filter by recommendation and threshold
        skills_to_adopt = [
            comp for comp in skill_comparisons
            if comp.adoption_recommendation == "adopt"
            and comp.delta >= threshold
        ]
        
        skills_to_keep = [
            comp for comp in skill_comparisons
            if comp.adoption_recommendation == "keep_ours"
        ]
        
        skills_to_hybrid = [
            comp for comp in skill_comparisons
            if comp.adoption_recommendation == "hybrid"
        ]
        
        skills_to_skip = [
            comp for comp in skill_comparisons
            if comp.adoption_recommendation == "skip"
        ]
        
        # Calculate total improvement
        total_improvement = self._calculate_improvement(skills_to_adopt)
        
        # Generate rationale
        selection_rationale = self._generate_rationale(
            skills_to_adopt, skills_to_keep, skills_to_hybrid, skills_to_skip,
            adoption_strategy, threshold
        )
        
        return SkillSelectionResult(
            skills_to_adopt=skills_to_adopt,
            skills_to_keep=skills_to_keep,
            skills_to_hybrid=skills_to_hybrid,
            skills_to_skip=skills_to_skip,
            total_improvement=total_improvement,
            selection_rationale=selection_rationale
        )
```

### 2.3.4 SkillTeacher

**Purpose:** Обучение нашей системы конкретным навыкам (не копирование кода, а адаптация паттернов).

**Input:**
```python
skill_to_adopt: SkillComparison
target_subagent: str                    # Имя субагента для обучения
sandbox: SandboxEnvironment
```

**Output:**
```python
@dataclass
class TeachingResult:
    skill_name: str
    target_subagent: str
    taught_successfully: bool
    integration_points: list[str]       # Где интегрирован навык
    before_metrics: dict[str, float]    # Метрики до обучения
    after_metrics: dict[str, float]     # Метрики после обучения
    improvement: float                  # % улучшения
    code_changes: list[str]             # Список изменённых файлов
    tests_added: list[str]              # Список добавленных тестов
    teaching_notes: str                 # Заметки о процессе обучения
```

**Teaching Process:**

1. **Analyze Integration Points:**
   - Где в нашем коде нужен этот навык?
   - Какие файлы/классы/функции затронуты?
   - Какие зависимости нужно добавить?

2. **Adapt Pattern (не копировать код!):**
   - Понять ПРИНЦИП работы навыка
   - Адаптировать под нашу архитектуру
   - Сохранить наш стиль кода
   - Добавить наши конвенции (Event Bus, Obsidian, etc.)

3. **Integrate:**
   - Создать/обновить файлы в sandbox
   - Добавить зависимости в requirements.txt
   - Обновить импорты
   - Добавить конфигурацию

4. **Test:**
   - Написать unit тесты для навыка
   - Написать integration тесты
   - Запустить все тесты
   - Измерить метрики (до/после)

5. **Document:**
   - Добавить docstrings
   - Обновить документацию субагента
   - Добавить примеры использования
   - Записать teaching notes

**Example: Teaching Circuit Breaker**

```python
# GitHub implementation (python-seo-analyzer)
class CircuitBreaker:
    def __init__(self, fail_max=5, reset_timeout=60):
        self.fail_count = 0
        self.fail_max = fail_max
        self.reset_timeout = reset_timeout
        self.state = "closed"
    
    def call(self, func):
        if self.state == "open":
            if time.time() - self.last_fail > self.reset_timeout:
                self.state = "half_open"
            else:
                raise CircuitBreakerError("Circuit is open")
        
        try:
            result = func()
            if self.state == "half_open":
                self.state = "closed"
                self.fail_count = 0
            return result
        except Exception as e:
            self.fail_count += 1
            if self.fail_count >= self.fail_max:
                self.state = "open"
                self.last_fail = time.time()
            raise

# Our adapted implementation (AIM/src/aim/subagents/api_clients/base.py)
from pybreaker import CircuitBreaker
from aim.events.event_bus import EventBus

class BaseClient:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        # Adapted: use pybreaker library (production-ready)
        self.circuit_breaker = CircuitBreaker(
            fail_max=5,
            reset_timeout=60,
            listeners=[self._on_circuit_open, self._on_circuit_close]
        )
    
    async def _fetch(self, url: str):
        # Adapted: integrated with Event Bus
        try:
            result = self.circuit_breaker.call(
                lambda: httpx.get(url)
            )
            await self.event_bus.publish(
                "api.request.success",
                {"url": url, "status": "ok"}
            )
            return result
        except CircuitBreakerError:
            await self.event_bus.publish(
                "api.circuit.open",
                {"url": url, "reason": "too_many_failures"}
            )
            raise
    
    def _on_circuit_open(self):
        # Adapted: log to Obsidian
        self.obsidian.log("Circuit breaker opened - too many failures")
    
    def _on_circuit_close(self):
        # Adapted: log to Obsidian
        self.obsidian.log("Circuit breaker closed - service recovered")
```

**Algorithm:**
1. Analyze GitHub implementation (понять принцип)
2. Find integration points в нашем коде
3. Adapt pattern:
   - Использовать production-ready библиотеки (pybreaker вместо custom)
   - Интегрировать с Event Bus (публиковать события)
   - Интегрировать с Obsidian (логировать состояния)
   - Сохранить наш стиль (async/await, type hints, docstrings)
4. Write tests:
   - Unit тесты для circuit breaker
   - Integration тесты с Event Bus
   - Тесты для edge cases (half_open state, reset_timeout)
5. Measure improvement:
   - Before: no circuit breaker, cascading failures
   - After: circuit breaker, graceful degradation
   - Improvement: 95% reduction in cascading failures

**Implementation:**
```python
class SkillTeacher:
    def __init__(self, event_bus: EventBus, obsidian: ObsidianVault):
        self.event_bus = event_bus
        self.obsidian = obsidian
    
    async def teach_skill(
        self,
        skill_to_adopt: SkillComparison,
        target_subagent: str,
        sandbox: SandboxEnvironment
    ) -> TeachingResult:
        # 1. Analyze integration points
        integration_points = await self._analyze_integration_points(
            skill_to_adopt, target_subagent
        )
        
        # 2. Measure before metrics
        before_metrics = await self._measure_metrics(target_subagent)
        
        # 3. Adapt pattern (NOT copy code!)
        adapted_code = await self._adapt_pattern(
            skill_to_adopt.github_implementation,
            target_subagent,
            integration_points
        )
        
        # 4. Integrate into sandbox
        code_changes = await self._integrate_code(
            adapted_code, target_subagent, sandbox
        )
        
        # 5. Write tests
        tests_added = await self._write_tests(
            skill_to_adopt, target_subagent, sandbox
        )
        
        # 6. Run tests
        test_results = await self._run_tests(sandbox)
        
        # 7. Measure after metrics
        after_metrics = await self._measure_metrics(target_subagent)
        
        # 8. Calculate improvement
        improvement = self._calculate_improvement(
            before_metrics, after_metrics
        )
        
        # 9. Document
        teaching_notes = await self._document_teaching(
            skill_to_adopt, integration_points, improvement
        )
        
        return TeachingResult(
            skill_name=skill_to_adopt.skill_name,
            target_subagent=target_subagent,
            taught_successfully=test_results.all_passed,
            integration_points=integration_points,
            before_metrics=before_metrics,
            after_metrics=after_metrics,
            improvement=improvement,
            code_changes=code_changes,
            tests_added=tests_added,
            teaching_notes=teaching_notes
        )
    
    async def _adapt_pattern(
        self,
        github_implementation: str,
        target_subagent: str,
        integration_points: list[str]
    ) -> str:
        # NOT copying code - adapting pattern!
        # 1. Understand the principle
        # 2. Use production-ready libraries
        # 3. Integrate with our architecture (Event Bus, Obsidian)
        # 4. Follow our conventions (async/await, type hints, docstrings)
        # 5. Add our error handling
        pass
```

### 2.3.5 SkillExtractionOrchestrator

**Purpose:** Оркестрация всего процесса извлечения и обучения навыкам.

**Input:**
```python
github_repo_url: str
target_subagent: str
adoption_strategy: str  # "aggressive" | "conservative" | "balanced"
```

**Output:**
```python
@dataclass
class SkillExtractionReport:
    github_repo_url: str
    target_subagent: str
    extraction_result: SkillExtractionResult
    comparisons: list[SkillComparison]
    selection_result: SkillSelectionResult
    teaching_results: list[TeachingResult]
    overall_improvement: float          # % улучшения субагента
    skills_adopted: int
    skills_kept: int
    skills_skipped: int
    total_time: float                   # Время выполнения (секунды)
    report_timestamp: datetime
```

**Workflow:**
1. Clone GitHub repo
2. Extract skills (SkillExtractor)
3. Compare each skill (SkillComparator)
4. Select best skills (SkillSelector)
5. Teach selected skills (SkillTeacher)
6. Aggregate results
7. Return report

**Implementation:**
```python
class SkillExtractionOrchestrator:
    def __init__(self):
        self.extractor = SkillExtractor()
        self.comparator = SkillComparator()
        self.selector = SkillSelector()
        self.teacher = SkillTeacher()
    
    async def extract_and_teach(
        self,
        github_repo_url: str,
        target_subagent: str,
        adoption_strategy: str = "balanced"
    ) -> SkillExtractionReport:
        start_time = time.time()
        
        # 1. Clone repo
        repo_path = await self._clone_repo(github_repo_url)
        
        # 2. Analyze architecture
        architecture_analysis = await self._analyze_architecture(repo_path)
        
        # 3. Extract skills
        extraction_result = await self.extractor.extract_skills(
            repo_path, architecture_analysis
        )
        
        # 4. Compare each skill
        our_repo_path = Path(f"AIM/src/aim/subagents/{target_subagent}")
        our_analysis = await self._analyze_architecture(our_repo_path)
        
        comparisons = []
        for skill in extraction_result.skills:
            comparison = await self.comparator.compare_skill(
                skill, our_repo_path, our_analysis
            )
            comparisons.append(comparison)
        
        # 5. Select best skills
        selection_result = self.selector.select_skills(
            comparisons, adoption_strategy
        )
        
        # 6. Create sandbox
        sandbox = await self._create_sandbox(target_subagent)
        
        # 7. Teach selected skills
        teaching_results = []
        for skill_comp in selection_result.skills_to_adopt:
            teaching_result = await self.teacher.teach_skill(
                skill_comp, target_subagent, sandbox
            )
            teaching_results.append(teaching_result)
        
        # 8. Calculate overall improvement
        overall_improvement = sum(
            tr.improvement for tr in teaching_results
        ) / len(teaching_results) if teaching_results else 0
        
        total_time = time.time() - start_time
        
        return SkillExtractionReport(
            github_repo_url=github_repo_url,
            target_subagent=target_subagent,
            extraction_result=extraction_result,
            comparisons=comparisons,
            selection_result=selection_result,
            teaching_results=teaching_results,
            overall_improvement=overall_improvement,
            skills_adopted=len(selection_result.skills_to_adopt),
            skills_kept=len(selection_result.skills_to_keep),
            skills_skipped=len(selection_result.skills_to_skip),
            total_time=total_time,
            report_timestamp=datetime.now()
        )
```

---

## 3. Solution Comparison Layer

### 3.1 ArchitectureScorer

**Purpose:** Оценка архитектурного качества решения.

**Input:**
```python
architecture_analysis: ArchitectureAnalysis
```

**Output:**
```python
@dataclass
class ArchitectureScore:
    modularity: float                        # 0-100 (low coupling, high cohesion)
    testability: float                       # 0-100 (test coverage, test quality)
    maintainability: float                   # 0-100 (complexity, documentation)
    scalability: float                       # 0-100 (patterns, architecture style)
    overall: float                           # Weighted average
```

**Scoring Criteria:**

**Modularity (0-100):**
- Coupling score (from ComponentRelationAnalyzer)
- No circular dependencies: +20
- Clear separation of concerns: +20
- Small, focused modules: +10

**Testability (0-100):**
- Test coverage estimate: 0-40 points
- Has fixtures: +15
- Has mocks: +15
- Test quality score: 0-30 points

**Maintainability (0-100):**
- Low complexity (cyclomatic): 0-30 points
- Good documentation: 0-30 points
- Consistent code style: 0-20 points
- Clear naming: 0-20 points

**Scalability (0-100):**
- Design patterns detected: +10 per pattern (max 40)
- Architecture style (Layered/Hexagonal/Clean): +30
- SOLID compliance: +6 per principle (max 30)

**Implementation:**
```python
class ArchitectureScorer:
    def score(self, analysis: ArchitectureAnalysis) -> ArchitectureScore:
        modularity = self._score_modularity(analysis)
        testability = self._score_testability(analysis)
        maintainability = self._score_maintainability(analysis)
        scalability = self._score_scalability(analysis)
        
        overall = (
            modularity * 0.30 +
            testability * 0.30 +
            maintainability * 0.20 +
            scalability * 0.20
        )
        
        return ArchitectureScore(
            modularity=modularity,
            testability=testability,
            maintainability=maintainability,
            scalability=scalability,
            overall=overall
        )
```

### 3.2 QualityScorer

**Purpose:** Оценка качества кода и практик.

**Input:**
```python
repo_path: Path
architecture_analysis: ArchitectureAnalysis
```

**Output:**
```python
@dataclass
class QualityScore:
    patterns: float                          # 0-100 (production patterns detected)
    error_handling: float                    # 0-100 (try/except coverage)
    documentation: float                     # 0-100 (docstrings, comments, README)
    code_quality: float                      # 0-100 (complexity, style, type hints)
    overall: float                           # Weighted average
```

**Scoring Criteria:**

**Patterns (0-100):**
- Circuit breaker: +20
- Retry logic: +15
- Rate limiting: +15
- Caching: +15
- Logging: +10
- Metrics: +10
- Health checks: +15

**Error Handling (0-100):**
- Try/except coverage: 0-50 points
- Custom exceptions: +20
- Error logging: +15
- Graceful degradation: +15

**Documentation (0-100):**
- README quality: 0-30 points
- Docstrings coverage: 0-40 points
- Inline comments: 0-15 points
- API docs: +15

**Code Quality (0-100):**
- Low cyclomatic complexity: 0-30 points
- Type hints coverage: 0-30 points
- Consistent style (ruff/black): +20
- No code smells: +20

**Implementation:**
```python
class QualityScorer:
    def score(self, repo_path: Path, analysis: ArchitectureAnalysis) -> QualityScore:
        patterns = self._score_patterns(repo_path)
        error_handling = self._score_error_handling(repo_path)
        documentation = self._score_documentation(repo_path, analysis)
        code_quality = self._score_code_quality(repo_path)
        
        overall = (
            patterns * 0.30 +
            error_handling * 0.25 +
            documentation * 0.20 +
            code_quality * 0.25
        )
        
        return QualityScore(
            patterns=patterns,
            error_handling=error_handling,
            documentation=documentation,
            code_quality=code_quality,
            overall=overall
        )
```

### 3.3 FitAnalyzer

**Purpose:** Оценка соответствия решения нашим задачам.

**Input:**
```python
subagent_spec_path: Path                     # Путь к спецификации субагента
github_analysis: ArchitectureAnalysis        # Анализ GitHub решения
our_analysis: ArchitectureAnalysis           # Анализ нашего субагента
```

**Output:**
```python
@dataclass
class FitScore:
    task_match: float                        # 0-100 (соответствие задаче)
    integration_effort: float                # 0-100 (100 = easy integration)
    dependency_compatibility: float          # 0-100 (совместимость зависимостей)
    customization_need: float                # 0-100 (100 = no customization)
    overall: float                           # Weighted average
```

**Scoring Criteria:**

**Task Match (0-100):**
- Read subagent spec (Section 1: Overview, Section 3: Algorithm)
- Compare GitHub solution purpose vs spec purpose
- Check if GitHub solution solves same problem
- Semantic similarity: 0-100 points

**Integration Effort (0-100):**
- Similar architecture style: +30
- Compatible with Event Bus: +25
- Compatible with Obsidian: +25
- Few external dependencies: +20

**Dependency Compatibility (0-100):**
- All dependencies available in PyPI: +40
- No version conflicts with our requirements.txt: +40
- No OS-specific dependencies: +20

**Customization Need (0-100):**
- Works out-of-box: 100 points
- Minor config changes: 80 points
- Code adaptation needed: 60 points
- Major refactoring needed: 40 points

**Implementation:**
```python
class FitAnalyzer:
    def analyze(
        self,
        subagent_spec_path: Path,
        github_analysis: ArchitectureAnalysis,
        our_analysis: ArchitectureAnalysis
    ) -> FitScore:
        task_match = self._score_task_match(subagent_spec_path, github_analysis)
        integration_effort = self._score_integration_effort(github_analysis, our_analysis)
        dependency_compatibility = self._score_dependency_compatibility(github_analysis)
        customization_need = self._score_customization_need(github_analysis, our_analysis)
        
        overall = (
            task_match * 0.40 +
            integration_effort * 0.25 +
            dependency_compatibility * 0.20 +
            customization_need * 0.15
        )
        
        return FitScore(
            task_match=task_match,
            integration_effort=integration_effort,
            dependency_compatibility=dependency_compatibility,
            customization_need=customization_need,
            overall=overall
        )
```

### 3.4 RiskAnalyzer

**Purpose:** Оценка рисков внедрения решения.

**Input:**
```python
repo_path: Path
github_analysis: ArchitectureAnalysis
our_analysis: ArchitectureAnalysis
```

**Output:**
```python
@dataclass
class RiskScore:
    security: float                          # 0-100 (100 = no security risks)
    compliance: float                        # 0-100 (100 = HIPAA compliant)
    breaking_changes: float                  # 0-100 (100 = no breaking changes)
    stability: float                         # 0-100 (100 = stable, mature)
    overall: float                           # Weighted average (lower = higher risk)
```

**Scoring Criteria:**

**Security (0-100):**
- No hardcoded secrets: +25
- No SQL injection vulnerabilities: +25
- No XSS vulnerabilities: +20
- Secure dependencies (no known CVEs): +30

**Compliance (0-100):**
- No PII logging: +30
- Encryption at rest: +25
- Encryption in transit: +25
- Audit trail: +20

**Breaking Changes (0-100):**
- No API changes: +40
- No database schema changes: +30
- No config changes: +20
- Backward compatible: +10

**Stability (0-100):**
- Repo age > 1 year: +25
- Active maintenance (commits in last 3 months): +25
- Stars > 100: +20
- Issues/PRs ratio < 0.3: +30

**Implementation:**
```python
class RiskAnalyzer:
    def analyze(
        self,
        repo_path: Path,
        github_analysis: ArchitectureAnalysis,
        our_analysis: ArchitectureAnalysis
    ) -> RiskScore:
        security = self._score_security(repo_path)
        compliance = self._score_compliance(repo_path)
        breaking_changes = self._score_breaking_changes(github_analysis, our_analysis)
        stability = self._score_stability(github_analysis)
        
        # Medical marketing context: security 2x weight
        overall = (
            security * 0.40 +
            compliance * 0.30 +
            breaking_changes * 0.20 +
            stability * 0.10
        )
        
        return RiskScore(
            security=security,
            compliance=compliance,
            breaking_changes=breaking_changes,
            stability=stability,
            overall=overall
        )
```


### 3.5 DecisionMaker

**Purpose:** Автономное принятие решений о внедрении на основе scores.

**Input:**
```python
architecture_score: ArchitectureScore
quality_score: QualityScore
fit_score: FitScore
risk_score: RiskScore
```

**Output:**
```python
@dataclass
class AdoptionDecision:
    decision: str                            # "Full" | "Partial" | "Custom" | "Reject"
    rationale: str                           # Detailed explanation
    confidence: float                        # 0-100
    risks: list[str]                         # Identified risks
    benefits: list[str]                      # Expected benefits
    action_plan: str                         # What to do next
```

**Decision Rules (Autonomous):**

```python
# Calculate composite scores
quality_composite = (architecture_score.overall + quality_score.overall) / 2
fit_composite = fit_score.overall
# risk_score semantics: 0 = safe, 100 = dangerous (no inversion needed)
risk_composite = risk_score.overall

# Full Adoption (low risk threshold)
if quality_composite >= 80 and fit_composite >= 80 and risk_composite <= 20:
    return AdoptionDecision(
        decision="Full",
        rationale="High quality, excellent fit, low risk",
        confidence=90,
        action_plan="Clone → Adapt → Validate → Auto-merge"
    )

# Partial Adoption (acceptable risk threshold)
elif quality_composite >= 70 and fit_composite >= 70 and risk_composite <= 30:
    return AdoptionDecision(
        decision="Partial",
        rationale="Good quality, good fit, acceptable risk - adaptation needed",
        confidence=75,
        action_plan="Clone → Adapt parameters → Validate → Auto-merge"
    )

# Custom Development
elif quality_composite >= 60 and fit_composite >= 60 and risk_composite <= 40:
    return AdoptionDecision(
        decision="Custom",
        rationale="Moderate quality, moderate fit - use as reference",
        confidence=60,
        action_plan="Study architecture → Build custom solution"
    )

# Reject
else:
    return AdoptionDecision(
        decision="Reject",
        rationale="Below thresholds - not suitable",
        confidence=50,
        action_plan="Log reasoning → Continue search"
    )
```

**Third-Party Agent Exception:**

```python
# If GitHub solution is a complete agent (not just a library)
if is_complete_agent(github_analysis):
    # Higher threshold: must be significantly better
    quality_delta = quality_composite - our_quality_composite
    
    if quality_delta >= 15 and fit_composite >= 80 and risk_composite <= 20:
        return AdoptionDecision(
            decision="Full",
            rationale=f"Third-party agent is {quality_delta} points better",
            confidence=85,
            action_plan="Clone → Integrate → Validate → Replace our agent"
        )
```

**Metrics Degradation Exception:**

```python
# Check if any metric degrades
if any_metric_degrades(github_analysis, our_analysis):
    max_degradation = calculate_max_degradation()
    improvement_elsewhere = calculate_improvement_elsewhere()
    
    # Default: reject if ANY degradation
    if max_degradation > 0:
        # Exception: accept ≤5% degradation if ≥20% improvement elsewhere
        if max_degradation <= 5 and improvement_elsewhere >= 20:
            return AdoptionDecision(
                decision="Partial",
                rationale=f"Accept {max_degradation}% degradation for {improvement_elsewhere}% improvement",
                confidence=70,
                action_plan="Clone → Adapt → Validate → Notify user of trade-off"
            )
        else:
            return AdoptionDecision(
                decision="Reject",
                rationale=f"Metrics degrade by {max_degradation}%",
                confidence=80,
                action_plan="Log reasoning → Continue search"
            )
```

**Implementation:**
```python
class DecisionMaker:
    def decide(
        self,
        architecture_score: ArchitectureScore,
        quality_score: QualityScore,
        fit_score: FitScore,
        risk_score: RiskScore,
        github_analysis: ArchitectureAnalysis,
        our_analysis: ArchitectureAnalysis
    ) -> AdoptionDecision:
        # Calculate composite scores
        quality_composite = (architecture_score.overall + quality_score.overall) / 2
        fit_composite = fit_score.overall
        risk_composite = 100 - risk_score.overall
        
        # Check third-party agent exception
        if self._is_complete_agent(github_analysis):
            decision = self._decide_third_party_agent(
                quality_composite, fit_composite, risk_composite,
                github_analysis, our_analysis
            )
            if decision:
                return decision
        
        # Check metrics degradation
        if self._any_metric_degrades(github_analysis, our_analysis):
            decision = self._handle_metrics_degradation(
                github_analysis, our_analysis
            )
            if decision.decision == "Reject":
                return decision
        
        # Apply standard decision rules
        return self._apply_decision_rules(
            quality_composite, fit_composite, risk_composite
        )
```

### 3.6 SolutionComparator (Orchestrator)

**Purpose:** Оркестрация всех scorers и принятие решения.

**Input:**
```python
subagent_name: str
github_repo_url: str
```

**Output:**
```python
@dataclass
class ComparisonResult:
    github_analysis: ArchitectureAnalysis
    our_analysis: ArchitectureAnalysis
    architecture_score: ArchitectureScore
    quality_score: QualityScore
    fit_score: FitScore
    risk_score: RiskScore
    decision: AdoptionDecision
    comparison_timestamp: datetime
```

**Workflow:**
1. Clone GitHub repo to temp directory
2. Analyze GitHub solution (ArchitectureAnalyzer)
3. Analyze our subagent (ArchitectureAnalyzer)
4. Score architecture (ArchitectureScorer)
5. Score quality (QualityScorer)
6. Score fit (FitAnalyzer)
7. Score risk (RiskAnalyzer)
8. Make decision (DecisionMaker)
9. Return ComparisonResult

**Implementation:**
```python
class SolutionComparator:
    def __init__(self):
        self.architecture_analyzer = ArchitectureAnalyzer()
        self.architecture_scorer = ArchitectureScorer()
        self.quality_scorer = QualityScorer()
        self.fit_analyzer = FitAnalyzer()
        self.risk_analyzer = RiskAnalyzer()
        self.decision_maker = DecisionMaker()
    
    async def compare(
        self,
        subagent_name: str,
        github_repo_url: str
    ) -> ComparisonResult:
        # Clone GitHub repo
        github_repo_path = await self._clone_repo(github_repo_url)
        
        # Analyze both solutions in parallel
        github_analysis, our_analysis = await asyncio.gather(
            self.architecture_analyzer.analyze(github_repo_path, github_repo_url),
            self.architecture_analyzer.analyze(
                Path(f"AIM/src/aim/subagents/{subagent_name}"),
                "our_implementation"
            )
        )
        
        # Score in parallel
        architecture_score, quality_score, fit_score, risk_score = await asyncio.gather(
            self.architecture_scorer.score(github_analysis),
            self.quality_scorer.score(github_repo_path, github_analysis),
            self.fit_analyzer.analyze(
                Path(f"docs/subagents-specs/{subagent_name}_SPEC.md"),
                github_analysis,
                our_analysis
            ),
            self.risk_analyzer.analyze(github_repo_path, github_analysis, our_analysis)
        )
        
        # Make decision
        decision = self.decision_maker.decide(
            architecture_score, quality_score, fit_score, risk_score,
            github_analysis, our_analysis
        )
        
        return ComparisonResult(
            github_analysis=github_analysis,
            our_analysis=our_analysis,
            architecture_score=architecture_score,
            quality_score=quality_score,
            fit_score=fit_score,
            risk_score=risk_score,
            decision=decision,
            comparison_timestamp=datetime.now()
        )
```

---

## 4. Adoption Layer

### 4.1 SandboxManager

**Purpose:** Управление изолированным окружением для тестирования (git worktree).

**Input:**
```python
subagent_name: str
adoption_id: str  # UUID для этого adoption attempt
```

**Output:**
```python
@dataclass
class SandboxEnvironment:
    worktree_path: Path                      # Путь к worktree
    branch_name: str                         # Имя ветки
    snapshot_id: str                         # ID snapshot для rollback
    venv_path: Path                          # Путь к venv для dependency isolation
    created_at: datetime
```

**Workflow:**
1. Create git worktree: `.claude/worktrees/teacher-{adoption_id}`
2. Create branch: `teacher/{subagent_name}-{adoption_id}`
3. Create venv: `.claude/worktrees/teacher-{adoption_id}/.venv`
4. Create snapshot (git commit hash)
5. Return SandboxEnvironment

**Implementation:**
```python
class SandboxManager:
    async def create_sandbox(
        self,
        subagent_name: str,
        adoption_id: str
    ) -> SandboxEnvironment:
        # Create worktree with specific git commands
        worktree_path = Path(f".claude/worktrees/teacher-{adoption_id}")
        branch_name = f"teacher/{subagent_name}-{adoption_id}"
        
        # Git command: git worktree add <path> -b <branch>
        await self._run_git_command(
            f"worktree add {worktree_path} -b {branch_name}"
        )
        
        # Create venv for dependency isolation
        venv_path = worktree_path / ".venv"
        await self._run_command(
            f"python -m venv {venv_path}"
        )
        
        # Create snapshot (current commit hash)
        snapshot_id = await self._run_git_command("rev-parse HEAD")
        
        return SandboxEnvironment(
            worktree_path=worktree_path,
            branch_name=branch_name,
            snapshot_id=snapshot_id.strip(),
            venv_path=venv_path,
            created_at=datetime.now()
        )
    
    async def cleanup_sandbox(self, sandbox: SandboxEnvironment) -> None:
        # Git command: git worktree remove <path> --force
        await self._run_git_command(
            f"worktree remove {sandbox.worktree_path} --force"
        )
        )
        
        # Create snapshot
        snapshot_id = await self._get_current_commit_hash()
        
        return SandboxEnvironment(
            worktree_path=worktree_path,
            branch_name=branch_name,
            snapshot_id=snapshot_id,
            created_at=datetime.now()
        )
    
    async def cleanup_sandbox(
        self,
        sandbox: SandboxEnvironment,
        keep_changes: bool = False
    ) -> None:
        if keep_changes:
            # Merge to main
            await self._run_git_command(f"checkout main")
            await self._run_git_command(f"merge {sandbox.branch_name}")
        
        # Remove worktree
        await self._run_git_command(f"worktree remove {sandbox.worktree_path}")
        
        # Delete branch
        await self._run_git_command(f"branch -D {sandbox.branch_name}")
```

### 4.2 FileCopier

**Purpose:** Копирование файлов из GitHub репо с адаптацией.

**Input:**
```python
github_repo_path: Path
target_path: Path                            # AIM/src/aim/subagents/{name}
sandbox: SandboxEnvironment
```

**Output:**
```python
@dataclass
class CopyResult:
    files_copied: list[str]                  # Список скопированных файлов
    files_adapted: list[str]                 # Список адаптированных файлов
    backup_path: Path                        # Путь к backup
    issues: list[str]                        # Проблемы при копировании
```

**Adaptation Rules:**
1. **Naming conventions:**
   - snake_case для файлов и функций
   - PascalCase для классов
   - UPPER_CASE для констант

2. **Docstrings:**
   - Добавить "Adopted from {repo_url}" в начало каждого docstring
   - Сохранить оригинальный docstring

3. **Imports:**
   - Обновить пути импортов (их структура → наша структура)
   - Добавить импорты Event Bus, Obsidian если нужно

4. **Backup:**
   - Создать backup оригинальных файлов в `.claude/backups/teacher/{adoption_id}/`

**Implementation:**
```python
class FileCopier:
    async def copy_files(
        self,
        github_repo_path: Path,
        target_path: Path,
        sandbox: SandboxEnvironment,
        repo_url: str
    ) -> CopyResult:
        files_copied = []
        files_adapted = []
        issues = []
        
        # Create backup
        backup_path = Path(f".claude/backups/teacher/{sandbox.snapshot_id}")
        await self._create_backup(target_path, backup_path)
        
        # Copy files
        for file_path in self._get_python_files(github_repo_path):
            try:
                # Read source
                content = await self._read_file(file_path)
                
                # Adapt content
                adapted_content = await self._adapt_content(content, repo_url)
                
                # Write to target (in sandbox)
                target_file = target_path / file_path.name
                await self._write_file(
                    sandbox.worktree_path / target_file,
                    adapted_content
                )
                
                files_copied.append(str(file_path))
                if content != adapted_content:
                    files_adapted.append(str(file_path))
                    
            except Exception as e:
                issues.append(f"{file_path}: {str(e)}")
        
        return CopyResult(
            files_copied=files_copied,
            files_adapted=files_adapted,
            backup_path=backup_path,
            issues=issues
        )
```

### 4.3 DependencyInstaller

**Purpose:** Установка зависимостей из GitHub решения.

**Input:**
```python
github_repo_path: Path
sandbox: SandboxEnvironment
```

**Output:**
```python
@dataclass
class DependencyResult:
    dependencies_installed: list[str]        # Установленные зависимости
    version_conflicts: list[str]             # Конфликты версий
    requirements_updated: bool               # requirements.txt обновлён
```

**Workflow:**
1. Extract dependencies from requirements.txt / pyproject.toml
2. Check version compatibility with our requirements.txt
3. Install dependencies in sandbox venv
4. Update our requirements.txt with new dependencies
5. Return DependencyResult

**Implementation:**
```python
class DependencyInstaller:
    async def install_dependencies(
        self,
        github_repo_path: Path,
        sandbox: SandboxEnvironment
    ) -> DependencyResult:
        # Extract dependencies
        github_deps = await self._extract_dependencies(github_repo_path)
        our_deps = await self._extract_dependencies(Path("."))
        
        # Check conflicts
        conflicts = self._check_version_conflicts(github_deps, our_deps)
        
        # Install in sandbox
        dependencies_installed = []
        for dep in github_deps:
            if dep not in our_deps:
                await self._install_dependency(dep, sandbox)
                dependencies_installed.append(dep)
        
        # Update requirements.txt
        if dependencies_installed:
            await self._update_requirements(dependencies_installed, sandbox)
            requirements_updated = True
        else:
            requirements_updated = False
        
        return DependencyResult(
            dependencies_installed=dependencies_installed,
            version_conflicts=conflicts,
            requirements_updated=requirements_updated
        )
```


### 4.4 ImportUpdater

**Purpose:** Обновление импортов в скопированных файлах.

**Input:**
```python
target_path: Path                            # AIM/src/aim/subagents/{name}
sandbox: SandboxEnvironment
github_structure: FileStructure              # Структура GitHub репо
our_structure: FileStructure                 # Наша структура
```

**Output:**
```python
@dataclass
class ImportUpdateResult:
    files_updated: list[str]                 # Обновлённые файлы
    imports_added: list[str]                 # Добавленные импорты
    circular_deps_found: list[tuple[str, str]]  # Circular dependencies
```

**Workflow:**
1. Parse imports в каждом файле (AST)
2. Map GitHub imports → our imports
3. Add Event Bus, Obsidian imports if needed
4. Check for circular dependencies
5. Update files in sandbox
6. Return ImportUpdateResult

**Implementation:**
```python
class ImportUpdater:
    async def update_imports(
        self,
        target_path: Path,
        sandbox: SandboxEnvironment,
        github_structure: FileStructure,
        our_structure: FileStructure
    ) -> ImportUpdateResult:
        files_updated = []
        imports_added = []
        circular_deps = []
        
        for file_path in self._get_python_files(sandbox.worktree_path / target_path):
            # Parse imports
            tree = ast.parse(await self._read_file(file_path))
            
            # Map imports
            new_imports = self._map_imports(tree, github_structure, our_structure)
            
            # Add framework imports
            framework_imports = self._add_framework_imports(tree)
            imports_added.extend(framework_imports)
            
            # Update file
            updated_content = self._update_file_imports(file_path, new_imports)
            await self._write_file(file_path, updated_content)
            files_updated.append(str(file_path))
        
        # Check circular dependencies
        circular_deps = self._detect_circular_deps(sandbox.worktree_path / target_path)
        
        return ImportUpdateResult(
            files_updated=files_updated,
            imports_added=imports_added,
            circular_deps_found=circular_deps
        )
```

### 4.5 TestMigrator

**Purpose:** Миграция тестов из GitHub репо.

**Input:**
```python
github_repo_path: Path
target_test_path: Path                       # AIM/tests/subagents/{name}
sandbox: SandboxEnvironment
```

**Output:**
```python
@dataclass
class TestMigrationResult:
    tests_copied: list[str]                  # Скопированные тесты
    fixtures_adapted: list[str]              # Адаптированные fixtures
    integration_issues: list[str]            # Проблемы интеграции
```

**Workflow:**
1. Copy test files from GitHub repo
2. Adapt fixtures (pytest fixtures, mocks)
3. Update imports in tests
4. Integrate with our pytest setup (conftest.py)
5. Return TestMigrationResult

**Implementation:**
```python
class TestMigrator:
    async def migrate_tests(
        self,
        github_repo_path: Path,
        target_test_path: Path,
        sandbox: SandboxEnvironment
    ) -> TestMigrationResult:
        tests_copied = []
        fixtures_adapted = []
        issues = []
        
        # Find test files
        test_files = self._find_test_files(github_repo_path)
        
        for test_file in test_files:
            try:
                # Copy test
                content = await self._read_file(test_file)
                
                # Adapt fixtures
                adapted_content, adapted_fixtures = await self._adapt_fixtures(content)
                fixtures_adapted.extend(adapted_fixtures)
                
                # Update imports
                adapted_content = await self._update_test_imports(adapted_content)
                
                # Write to target
                target_file = target_test_path / test_file.name
                await self._write_file(
                    sandbox.worktree_path / target_file,
                    adapted_content
                )
                tests_copied.append(str(test_file))
                
            except Exception as e:
                issues.append(f"{test_file}: {str(e)}")
        
        return TestMigrationResult(
            tests_copied=tests_copied,
            fixtures_adapted=fixtures_adapted,
            integration_issues=issues
        )
```

### 4.6 ValidationGateRunner

**Purpose:** Запуск 5 validation gates последовательно.

**Input:**
```python
sandbox: SandboxEnvironment
subagent_name: str
```

**Output:**
```python
@dataclass
class ValidationResult:
    gate_results: dict[str, GateResult]      # Gate name -> result
    all_passed: bool                         # Все gates прошли
    failed_gates: list[str]                  # Список failed gates
    validation_timestamp: datetime
```

**Gate Results:**
```python
@dataclass
class GateResult:
    gate_name: str                           # "Sandbox Tests" | "Metrics Check" | etc.
    passed: bool                             # Gate прошёл
    details: str                             # Детали (output, metrics, etc.)
    duration: float                          # Время выполнения (секунды)
```

**5 Validation Gates:**

**Gate 1: Sandbox Tests**
- Run all tests in sandbox: `pytest AIM/tests/subagents/{name}/ -v`
- Pass condition: All tests pass (exit code 0)
- Fail condition: Any test fails

**Gate 2: Metrics Check**
- Compare metrics: complexity, coverage, performance
- Pass condition: Metrics improve OR stay same
- Fail condition: Any metric degrades (exception: ≤5% if ≥20% improvement elsewhere)

**Gate 3: Security Scan**
- Run bandit: `bandit -r AIM/src/aim/subagents/{name}/`
- Check for hardcoded secrets, SQL injection, XSS
- Pass condition: No high/medium severity issues
- Fail condition: Any high/medium severity issues

**Gate 4: Compliance Check (HIPAA)**
- Check for PHI (Protected Health Information) detection and handling
- Check for encryption at rest (database, files) and in transit (HTTPS, TLS)
- Check for audit logging for all PHI access (who, when, what)
- Check for role-based access control (RBAC) implementation
- Check for data retention policies compliance (minimum necessary principle)
- Check for breach notification procedures implementation
- Pass condition: All 6 HIPAA checks pass
- Fail condition: Any HIPAA check fails

**Gate 5: Integration Test**
- Test Event Bus integration
- Test Obsidian integration
- Test with existing Magisters
- Pass condition: All integrations work
- Fail condition: Any integration fails

**Implementation:**
```python
class ValidationGateRunner:
    async def run_gates(
        self,
        sandbox: SandboxEnvironment,
        subagent_name: str
    ) -> ValidationResult:
        gate_results = {}
        
        # Gate 1: Sandbox Tests
        gate_results["Sandbox Tests"] = await self._run_gate_1(sandbox, subagent_name)
        if not gate_results["Sandbox Tests"].passed:
            return self._early_exit(gate_results)
        
        # Gate 2: Metrics Check
        gate_results["Metrics Check"] = await self._run_gate_2(sandbox, subagent_name)
        if not gate_results["Metrics Check"].passed:
            return self._early_exit(gate_results)
        
        # Gate 3: Security Scan
        gate_results["Security Scan"] = await self._run_gate_3(sandbox, subagent_name)
        if not gate_results["Security Scan"].passed:
            return self._early_exit(gate_results)
        
        # Gate 4: Compliance Check
        gate_results["Compliance Check"] = await self._run_gate_4(sandbox, subagent_name)
        if not gate_results["Compliance Check"].passed:
            return self._early_exit(gate_results)
        
        # Gate 5: Integration Test
        gate_results["Integration Test"] = await self._run_gate_5(sandbox, subagent_name)
        
        all_passed = all(result.passed for result in gate_results.values())
        failed_gates = [name for name, result in gate_results.items() if not result.passed]
        
        return ValidationResult(
            gate_results=gate_results,
            all_passed=all_passed,
            failed_gates=failed_gates,
            validation_timestamp=datetime.now()
        )
```

### 4.7 RollbackManager

**Purpose:** Управление rollback при проблемах.

**Input:**
```python
sandbox: SandboxEnvironment
adoption_id: str
```

**Output:**
```python
@dataclass
class RollbackResult:
    success: bool                            # Rollback успешен
    snapshot_restored: str                   # Восстановленный snapshot
    files_restored: list[str]                # Восстановленные файлы
    rollback_timestamp: datetime
```

**Rollback Workflow:**
1. Restore from snapshot (git reset --hard {snapshot_id})
2. Remove worktree
3. Delete branch
4. Restore backup files
5. Return RollbackResult

**30-Day Rollback Window:**
- Rollback доступен 30 дней после adoption
- После 30 дней snapshot архивируется
- Exception: Security issues можно rollback всегда

**Implementation:**
```python
class RollbackManager:
    async def rollback(
        self,
        sandbox: SandboxEnvironment,
        adoption_id: str
    ) -> RollbackResult:
        # Restore from snapshot
        await self._run_git_command(
            f"reset --hard {sandbox.snapshot_id}"
        )
        
        # Restore backup files
        backup_path = Path(f".claude/backups/teacher/{adoption_id}")
        files_restored = await self._restore_backup(backup_path)
        
        # Cleanup sandbox
        await self.sandbox_manager.cleanup_sandbox(sandbox, keep_changes=False)
        
        return RollbackResult(
            success=True,
            snapshot_restored=sandbox.snapshot_id,
            files_restored=files_restored,
            rollback_timestamp=datetime.now()
        )
    
    async def is_rollback_available(
        self,
        adoption_id: str,
        adoption_date: datetime
    ) -> bool:
        # Check 30-day window
        days_since_adoption = (datetime.now() - adoption_date).days
        
        if days_since_adoption <= 30:
            return True
        
        # Check security exception
        if await self._is_security_issue(adoption_id):
            return True
        
        return False
```

### 4.8 FullAdopter (Orchestrator)

**Purpose:** Оркестрация всего процесса adoption.

**Input:**
```python
subagent_name: str
github_repo_url: str
decision: AdoptionDecision
comparison_result: ComparisonResult
```

**Output:**
```python
@dataclass
class AdoptionResult:
    success: bool                            # Adoption успешен
    adoption_id: str                         # UUID adoption
    files_copied: list[str]                  # Скопированные файлы
    dependencies_installed: list[str]        # Установленные зависимости
    tests_passing: int                       # Количество passing tests
    tests_failing: int                       # Количество failing tests
    validation_result: ValidationResult      # Результаты validation gates
    issues: list[str]                        # Проблемы
    rollback_performed: bool                 # Rollback выполнен
    adoption_timestamp: datetime
```

**Workflow:**
1. Create sandbox (SandboxManager)
2. Copy files (FileCopier)
3. Install dependencies (DependencyInstaller)
4. Update imports (ImportUpdater)
5. Migrate tests (TestMigrator)
6. Run validation gates (ValidationGateRunner)
7. If all gates pass → merge to main
8. If any gate fails → rollback
9. Generate adoption report
10. Send notification
11. Return AdoptionResult

**Implementation:**
```python
class FullAdopter:
    def __init__(self):
        self.sandbox_manager = SandboxManager()
        self.file_copier = FileCopier()
        self.dependency_installer = DependencyInstaller()
        self.import_updater = ImportUpdater()
        self.test_migrator = TestMigrator()
        self.validation_gate_runner = ValidationGateRunner()
        self.rollback_manager = RollbackManager()
    
    async def adopt(
        self,
        subagent_name: str,
        github_repo_url: str,
        decision: AdoptionDecision,
        comparison_result: ComparisonResult
    ) -> AdoptionResult:
        adoption_id = str(uuid.uuid4())
        rollback_performed = False
        
        try:
            # 1. Create sandbox
            sandbox = await self.sandbox_manager.create_sandbox(
                subagent_name, adoption_id
            )
            
            # 2. Copy files
            copy_result = await self.file_copier.copy_files(
                comparison_result.github_analysis.repo_path,
                Path(f"AIM/src/aim/subagents/{subagent_name}"),
                sandbox,
                github_repo_url
            )
            
            # 3. Install dependencies
            dep_result = await self.dependency_installer.install_dependencies(
                comparison_result.github_analysis.repo_path,
                sandbox
            )
            
            # 4. Update imports
            import_result = await self.import_updater.update_imports(
                Path(f"AIM/src/aim/subagents/{subagent_name}"),
                sandbox,
                comparison_result.github_analysis.file_structure,
                comparison_result.our_analysis.file_structure
            )
            
            # 5. Migrate tests
            test_result = await self.test_migrator.migrate_tests(
                comparison_result.github_analysis.repo_path,
                Path(f"AIM/tests/subagents/{subagent_name}"),
                sandbox
            )
            
            # 6. Run validation gates
            validation_result = await self.validation_gate_runner.run_gates(
                sandbox, subagent_name
            )
            
            # 7. Decision: merge or rollback
            if validation_result.all_passed:
                # Auto-merge
                await self.sandbox_manager.cleanup_sandbox(sandbox, keep_changes=True)
                success = True
            else:
                # Auto-rollback
                await self.rollback_manager.rollback(sandbox, adoption_id)
                rollback_performed = True
                success = False
            
            return AdoptionResult(
                success=success,
                adoption_id=adoption_id,
                files_copied=copy_result.files_copied,
                dependencies_installed=dep_result.dependencies_installed,
                tests_passing=self._count_passing_tests(validation_result),
                tests_failing=self._count_failing_tests(validation_result),
                validation_result=validation_result,
                issues=copy_result.issues + dep_result.version_conflicts,
                rollback_performed=rollback_performed,
                adoption_timestamp=datetime.now()
            )
            
        except Exception as e:
            # Rollback on any exception
            if 'sandbox' in locals():
                await self.rollback_manager.rollback(sandbox, adoption_id)
            
            return AdoptionResult(
                success=False,
                adoption_id=adoption_id,
                files_copied=[],
                dependencies_installed=[],
                tests_passing=0,
                tests_failing=0,
                validation_result=None,
                issues=[str(e)],
                rollback_performed=True,
                adoption_timestamp=datetime.now()
            )
```

---

## 5. Reporting & Audit Layer

### 5.1 AdoptionReportGenerator

**Purpose:** Генерация детальных отчётов о adoption.

**Input:**
```python
adoption_result: AdoptionResult
comparison_result: ComparisonResult
decision: AdoptionDecision
```

**Output:**
```python
report_path: Path  # Path to generated markdown report
```

**Report Structure:**
```markdown
# Adoption Report: {subagent_name}

**Date:** YYYY-MM-DD HH:MM  
**Adoption ID:** {adoption_id}  
**Status:** ✅ Success | ❌ Failed  
**GitHub Repo:** {repo_url}

## Decision

**Type:** Full | Partial | Custom | Reject  
**Rationale:** {rationale}  
**Confidence:** {confidence}%

## Scores

| Metric | GitHub | Our | Delta |
|--------|--------|-----|-------|
| Quality | {score} | {score} | {delta} |
| Fit | {score} | - | - |
| Risk | {score} | - | - |

## Changes

**Files Copied:** {count}
- file1.py
- file2.py

**Dependencies Installed:** {count}
- library1==1.0.0
- library2==2.0.0

**Tests Migrated:** {count}

## Validation Results

### Gate 1: Sandbox Tests
✅ Passed | ❌ Failed  
Details: {details}

### Gate 2: Metrics Check
✅ Passed | ❌ Failed  
Details: {details}

### Gate 3: Security Scan
✅ Passed | ❌ Failed  
Details: {details}

### Gate 4: Compliance Check
✅ Passed | ❌ Failed  
Details: {details}

### Gate 5: Integration Test
✅ Passed | ❌ Failed  
Details: {details}

## Outcome

{success_message | failure_message}

## Rollback

Available until: {date} (30 days)  
Command: `teacher rollback {adoption_id}`
```

**Implementation:**
```python
class AdoptionReportGenerator:
    async def generate_report(
        self,
        adoption_result: AdoptionResult,
        comparison_result: ComparisonResult,
        decision: AdoptionDecision,
        subagent_name: str
    ) -> Path:
        # Generate markdown report
        report_content = self._build_report(
            adoption_result, comparison_result, decision, subagent_name
        )
        
        # Save to Obsidian vault
        report_path = Path(
            f"obsidian/teacher/wiki/projects/adoptions/"
            f"{datetime.now().strftime('%Y-%m-%d')}-{subagent_name}.md"
        )
        
        await self._write_file(report_path, report_content)
        
        # Update log.md
        await self._update_log(report_path, adoption_result)
        
        return report_path
```


### 5.2 AuditTrailLogger

**Purpose:** Логирование всех решений и действий для audit trail.

**Input:**
```python
event_type: str                              # "decision" | "adoption" | "rollback"
event_data: dict[str, Any]                   # Event-specific data
```

**Output:**
```python
log_entry_id: str                            # UUID log entry
```

**Log Entry Format:**
```python
@dataclass
class AuditLogEntry:
    entry_id: str                            # UUID
    timestamp: datetime
    event_type: str                          # "decision" | "adoption" | "rollback"
    subagent_name: str
    github_repo_url: str
    decision: str                            # "Full" | "Partial" | "Custom" | "Reject"
    scores: dict[str, float]                 # Quality, Fit, Risk scores
    validation_result: Optional[ValidationResult]
    outcome: str                             # "success" | "failed" | "rolled_back"
    rationale: str                           # Why this decision was made
```

**Implementation:**
```python
class AuditTrailLogger:
    async def log_event(
        self,
        event_type: str,
        event_data: dict[str, Any]
    ) -> str:
        entry_id = str(uuid.uuid4())
        
        # Create log entry
        log_entry = AuditLogEntry(
            entry_id=entry_id,
            timestamp=datetime.now(),
            event_type=event_type,
            **event_data
        )
        
        # Save to Obsidian vault
        await self._save_to_vault(log_entry)
        
        # Update decisions/adoption-decisions.md
        await self._update_decisions_log(log_entry)
        
        return entry_id
```

### 5.3 NotificationSender

**Purpose:** Отправка notifications пользователю через Event Bus.

**Input:**
```python
notification_type: str                       # "adoption_success" | "adoption_failed" | "rollback"
notification_data: dict[str, Any]
```

**Output:**
```python
notification_sent: bool
```

**Notification Types:**

**1. Adoption Success:**
```
🎓 Teacher Agent: Adoption Complete

Subagent: {name}
GitHub Repo: {url}
Decision: Full Adoption
Status: ✅ All validation gates passed

Changes:
- {count} files copied
- {count} dependencies installed
- {count} tests passing

Report: obsidian/teacher/wiki/projects/adoptions/{date}-{name}.md
```

**2. Adoption Failed:**
```
🎓 Teacher Agent: Adoption Failed

Subagent: {name}
GitHub Repo: {url}
Decision: Full Adoption
Status: ❌ Validation failed

Failed Gates:
- {gate_name}: {reason}

Rollback: ✅ Performed
Report: obsidian/teacher/wiki/projects/adoptions/{date}-{name}.md
```

**3. Rejection:**
```
🎓 Teacher Agent: Solution Rejected

Subagent: {name}
GitHub Repo: {url}
Decision: Reject
Reason: {rationale}

Scores:
- Quality: {score}/100
- Fit: {score}/100
- Risk: {score}/100

Report: obsidian/teacher/wiki/projects/adoptions/{date}-{name}.md
```

**Implementation:**
```python
class NotificationSender:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
    
    async def send_notification(
        self,
        notification_type: str,
        notification_data: dict[str, Any]
    ) -> bool:
        # Build notification message
        message = self._build_message(notification_type, notification_data)
        
        # Send via Event Bus
        await self.event_bus.publish(
            Event(
                type="teacher.notification",
                priority=Priority.P1,
                payload={
                    "notification_type": notification_type,
                    "message": message,
                    "data": notification_data
                }
            )
        )
        
        return True
```

---

## 6. TeacherAgent Integration

### 6.1 TeacherAgent Class

**Purpose:** Main orchestrator для всей системы Teacher Agent v2.0.

**Interface:**
```python
class TeacherAgent:
    def __init__(
        self,
        event_bus: EventBus,
        obsidian: ObsidianVault
    ):
        self.event_bus = event_bus
        self.obsidian = obsidian
        
        # Initialize components
        self.research_orchestrator = ResearchOrchestrator()  # NEW: Deep research
        self.architecture_analyzer = ArchitectureAnalyzer()
        self.solution_comparator = SolutionComparator()
        self.skill_orchestrator = SkillExtractionOrchestrator()  # NEW: Skill extraction
        self.full_adopter = FullAdopter()
        self.report_generator = AdoptionReportGenerator()
        self.audit_logger = AuditTrailLogger()
        self.notification_sender = NotificationSender(event_bus)
    
    async def audit_subagent(
        self,
        subagent_name: str
    ) -> ArchitectureAnalysis:
        """Deep analysis of subagent architecture."""
        subagent_path = Path(f"AIM/src/aim/subagents/{subagent_name}")
        return await self.architecture_analyzer.analyze(
            subagent_path,
            "our_implementation"
        )
    
    async def find_github_solutions(
        self,
        subagent_name: str,
        query: str,
        research_depth: str = "standard"
    ) -> list[str]:
        """Search GitHub for relevant solutions using deep research."""
        # Use ResearchOrchestrator for deep research
        research_result = await self.research_orchestrator.research_topic(
            subagent_name=subagent_name,
            topic=query,
            research_depth=research_depth
        )
        
        # Log research to Obsidian
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
        
        # Return top repo URLs
        return [repo.url for repo in research_result.github_repos[:5]]
    
    async def compare_solution(
        self,
        subagent_name: str,
        github_repo_url: str
    ) -> ComparisonResult:
        """Compare GitHub solution with our subagent."""
        return await self.solution_comparator.compare(
            subagent_name,
            github_repo_url
        )
    
    async def adopt_solution(
        self,
        subagent_name: str,
        github_repo_url: str,
        comparison_result: ComparisonResult
    ) -> AdoptionResult:
        """Autonomously adopt GitHub solution if decision is Full/Partial."""
        decision = comparison_result.decision
        
        # Log decision
        await self.audit_logger.log_event(
            "decision",
            {
                "subagent_name": subagent_name,
                "github_repo_url": github_repo_url,
                "decision": decision.decision,
                "scores": {
                    "quality": comparison_result.quality_score.overall,
                    "fit": comparison_result.fit_score.overall,
                    "risk": comparison_result.risk_score.overall
                },
                "rationale": decision.rationale
            }
        )
        
        # If Reject or Custom → skip adoption
        if decision.decision in ["Reject", "Custom"]:
            await self.notification_sender.send_notification(
                "rejection",
                {
                    "subagent_name": subagent_name,
                    "github_repo_url": github_repo_url,
                    "decision": decision
                }
            )
            return None
        
        # Adopt (Full or Partial)
        adoption_result = await self.full_adopter.adopt(
            subagent_name,
            github_repo_url,
            decision,
            comparison_result
        )
        
        # Generate report
        report_path = await self.report_generator.generate_report(
            adoption_result,
            comparison_result,
            decision,
            subagent_name
        )
        
        # Log adoption
        await self.audit_logger.log_event(
            "adoption",
            {
                "subagent_name": subagent_name,
                "github_repo_url": github_repo_url,
                "decision": decision.decision,
                "outcome": "success" if adoption_result.success else "failed",
                "validation_result": adoption_result.validation_result
            }
        )
        
        # Send notification
        notification_type = "adoption_success" if adoption_result.success else "adoption_failed"
        await self.notification_sender.send_notification(
            notification_type,
            {
                "subagent_name": subagent_name,
                "github_repo_url": github_repo_url,
                "adoption_result": adoption_result,
                "report_path": report_path
            }
        )
        
        return adoption_result
    
    async def rollback_adoption(
        self,
        adoption_id: str
    ) -> RollbackResult:
        """Rollback a previous adoption."""
        # Load adoption metadata
        adoption_metadata = await self._load_adoption_metadata(adoption_id)
        
        # Check if rollback available
        if not await self.full_adopter.rollback_manager.is_rollback_available(
            adoption_id,
            adoption_metadata.adoption_timestamp
        ):
            raise ValueError(f"Rollback not available for {adoption_id}")
        
        # Perform rollback
        rollback_result = await self.full_adopter.rollback_manager.rollback(
            adoption_metadata.sandbox,
            adoption_id
        )
        
        # Log rollback
        await self.audit_logger.log_event(
            "rollback",
            {
                "adoption_id": adoption_id,
                "subagent_name": adoption_metadata.subagent_name,
                "rollback_result": rollback_result
            }
        )
        
        # Send notification
        await self.notification_sender.send_notification(
            "rollback",
            {
                "adoption_id": adoption_id,
                "subagent_name": adoption_metadata.subagent_name,
                "rollback_result": rollback_result
            }
        )
        
        return rollback_result
    
    async def autonomous_learning_cycle(
        self,
        subagent_name: str
    ) -> None:
        """Full autonomous learning cycle for a subagent."""
        # 1. Audit current subagent
        our_analysis = await self.audit_subagent(subagent_name)
        
        # 2. Find GitHub solutions
        query = self._build_search_query(subagent_name)
        github_repos = await self.find_github_solutions(subagent_name, query)
        
        # 3. Compare each solution
        for repo_url in github_repos:
            comparison_result = await self.compare_solution(subagent_name, repo_url)
            
            # 4. Autonomous decision + adoption
            if comparison_result.decision.decision in ["Full", "Partial"]:
                adoption_result = await self.adopt_solution(
                    subagent_name,
                    repo_url,
                    comparison_result
                )
                
                # If adoption successful, stop searching
                if adoption_result and adoption_result.success:
                    break
```

### 6.2 CLI Commands

**Purpose:** CLI интерфейс для Teacher Agent.

**Commands:**

```bash
# Deep audit субагента
python scripts/teacher_cli.py audit <subagent_name>

# ⭐ Deep research topic (Brave/Exa/Perplexity + GitHub)
python scripts/teacher_cli.py research <subagent_name> --query "circuit breaker python" --depth <quick|standard|deep>

# Поиск GitHub решений (uses research internally)
python scripts/teacher_cli.py search <subagent_name> --query "circuit breaker python" --depth <quick|standard|deep>

# Сравнение решений
python scripts/teacher_cli.py compare <subagent_name> --repo <github_url>

# ⭐ Extract skills from GitHub repo
python scripts/teacher_cli.py extract-skills --repo <github_url>

# ⭐ Compare specific skill (GitHub vs ours)
python scripts/teacher_cli.py compare-skill <subagent_name> --skill <skill_name> --repo <github_url>

# ⭐ Teach specific skill to subagent
python scripts/teacher_cli.py teach-skill <subagent_name> --skill <skill_name> --repo <github_url>

# ⭐ Extract and teach all skills (full skill adoption workflow)
python scripts/teacher_cli.py extract-and-teach <subagent_name> --repo <github_url> --strategy <aggressive|balanced|conservative>

# Autonomous adoption (если decision Full/Partial)
python scripts/teacher_cli.py adopt <subagent_name> --repo <github_url>

# Rollback adoption
python scripts/teacher_cli.py rollback <adoption_id>

# Full autonomous learning cycle
python scripts/teacher_cli.py learn <subagent_name> --depth <quick|standard|deep>

# List all adoptions
python scripts/teacher_cli.py list-adoptions

# Show adoption report
python scripts/teacher_cli.py show-adoption <adoption_id>
```

**Implementation:**
```python
# scripts/teacher_cli.py
import asyncio
import click
from AIM.src.aim.teacher.teacher_agent import TeacherAgent

@click.group()
def cli():
    """Teacher Agent v2.0 CLI"""
    pass

@cli.command()
@click.argument('subagent_name')
async def audit(subagent_name: str):
    """Deep audit of subagent architecture."""
    teacher = TeacherAgent(event_bus, obsidian)
    analysis = await teacher.audit_subagent(subagent_name)
    click.echo(f"Quality Score: {analysis.quality_score}/100")

@cli.command()
@click.argument('subagent_name')
@click.option('--repo', required=True)
async def compare(subagent_name: str, repo: str):
    """Compare GitHub solution with our subagent."""
    teacher = TeacherAgent(event_bus, obsidian)
    result = await teacher.compare_solution(subagent_name, repo)
    click.echo(f"Decision: {result.decision.decision}")
    click.echo(f"Rationale: {result.decision.rationale}")

@cli.command()
@click.option('--repo', required=True)
async def extract_skills(repo: str):
    """Extract skills from GitHub repo."""
    teacher = TeacherAgent(event_bus, obsidian)
    result = await teacher.skill_orchestrator.extract_skills(repo)
    
    click.echo(f"✅ Extracted {result.total_skills} skills")
    click.echo("\nBy category:")
    for category, count in result.categories.items():
        click.echo(f"  {category}: {count}")
    
    click.echo("\nTop skills:")
    for skill in sorted(result.skills, key=lambda s: s.confidence, reverse=True)[:10]:
        click.echo(f"  - {skill.name} ({skill.category}): confidence {skill.confidence:.2f}")

@cli.command()
@click.argument('subagent_name')
@click.option('--skill', required=True)
@click.option('--repo', required=True)
async def compare_skill(subagent_name: str, skill: str, repo: str):
    """Compare specific skill (GitHub vs ours)."""
    teacher = TeacherAgent(event_bus, obsidian)
    
    # Extract skills from GitHub
    extraction = await teacher.skill_orchestrator.extract_skills(repo)
    github_skill = next((s for s in extraction.skills if s.name == skill), None)
    
    if not github_skill:
        click.echo(f"❌ Skill '{skill}' not found in {repo}")
        return
    
    # Compare
    comparison = await teacher.skill_orchestrator.comparator.compare_skill(
        github_skill, subagent_name
    )
    
    click.echo(f"Skill: {comparison.skill_name}")
    click.echo(f"GitHub Score: {comparison.github_score}/100")
    click.echo(f"Our Score: {comparison.our_score}/100")
    click.echo(f"Winner: {comparison.winner}")
    click.echo(f"Recommendation: {comparison.adoption_recommendation}")
    click.echo(f"\nReasoning: {comparison.reasoning}")

@cli.command()
@click.argument('subagent_name')
@click.option('--skill', required=True)
@click.option('--repo', required=True)
async def teach_skill(subagent_name: str, skill: str, repo: str):
    """Teach specific skill to subagent."""
    teacher = TeacherAgent(event_bus, obsidian)
    
    # Extract and compare skill
    extraction = await teacher.skill_orchestrator.extract_skills(repo)
    github_skill = next((s for s in extraction.skills if s.name == skill), None)
    
    if not github_skill:
        click.echo(f"❌ Skill '{skill}' not found")
        return
    
    comparison = await teacher.skill_orchestrator.comparator.compare_skill(
        github_skill, subagent_name
    )
    
    # Create sandbox
    sandbox = await teacher.sandbox_manager.create_sandbox(subagent_name)
    
    # Teach skill
    result = await teacher.skill_orchestrator.teacher.teach_skill(
        comparison, subagent_name, sandbox
    )
    
    if result.taught_successfully:
        click.echo(f"✅ Skill '{skill}' taught successfully!")
        click.echo(f"Improvement: {result.improvement:.1f}%")
        click.echo(f"Files changed: {len(result.code_changes)}")
        click.echo(f"Tests added: {len(result.tests_added)}")
    else:
        click.echo(f"❌ Failed to teach skill '{skill}'")

@cli.command()
@click.argument('subagent_name')
@click.option('--repo', required=True)
@click.option('--strategy', default='balanced', type=click.Choice(['aggressive', 'balanced', 'conservative']))
async def extract_and_teach(subagent_name: str, repo: str, strategy: str):
    """Extract and teach all skills (full workflow)."""
    teacher = TeacherAgent(event_bus, obsidian)
    
    click.echo(f"🔍 Extracting skills from {repo}...")
    report = await teacher.skill_orchestrator.extract_and_teach(
        repo, subagent_name, strategy
    )
    
    click.echo(f"\n✅ Skill extraction complete!")
    click.echo(f"Total skills extracted: {report.extraction_result.total_skills}")
    click.echo(f"Skills adopted: {report.skills_adopted}")
    click.echo(f"Skills kept (ours better): {report.skills_kept}")
    click.echo(f"Skills skipped: {report.skills_skipped}")
    click.echo(f"Overall improvement: {report.overall_improvement:.1f}%")
    click.echo(f"Time: {report.total_time:.1f}s")
    
    click.echo("\n📊 Teaching results:")
    for result in report.teaching_results:
        click.echo(f"  - {result.skill_name}: {result.improvement:.1f}% improvement")

@cli.command()
@click.argument('subagent_name')
@click.option('--repo', required=True)
async def adopt(subagent_name: str, repo: str):
    """Autonomously adopt GitHub solution."""
    teacher = TeacherAgent(event_bus, obsidian)
    
    # Compare first
    comparison = await teacher.compare_solution(subagent_name, repo)
    
    # Adopt if Full/Partial
    if comparison.decision.decision in ["Full", "Partial"]:
        result = await teacher.adopt_solution(subagent_name, repo, comparison)
        if result.success:
            click.echo("✅ Adoption successful!")
        else:
            click.echo("❌ Adoption failed (rolled back)")
    else:
        click.echo(f"❌ Decision: {comparison.decision.decision}")
        click.echo(f"Reason: {comparison.decision.rationale}")

@cli.command()
@click.argument('adoption_id')
async def rollback(adoption_id: str):
    """Rollback a previous adoption."""
    teacher = TeacherAgent(event_bus, obsidian)
    result = await teacher.rollback_adoption(adoption_id)
    click.echo(f"✅ Rollback successful: {len(result.files_restored)} files restored")

@cli.command()
@click.argument('subagent_name')
async def learn(subagent_name: str):
    """Full autonomous learning cycle."""
    teacher = TeacherAgent(event_bus, obsidian)
    await teacher.autonomous_learning_cycle(subagent_name)
    click.echo("✅ Learning cycle complete")

if __name__ == '__main__':
    cli()
```

---

## 7. Configuration

### 7.1 Decision Thresholds

```python
# AIM/src/aim/config/teacher_settings.py

@dataclass
class TeacherSettings:
    # Decision thresholds
    full_adoption_quality_threshold: float = 80.0
    full_adoption_fit_threshold: float = 80.0
    full_adoption_risk_threshold: float = 20.0
    
    partial_adoption_quality_threshold: float = 70.0
    partial_adoption_fit_threshold: float = 70.0
    partial_adoption_risk_threshold: float = 30.0
    
    custom_development_quality_threshold: float = 60.0
    custom_development_fit_threshold: float = 60.0
    custom_development_risk_threshold: float = 40.0
    
    # Third-party agent threshold
    third_party_quality_delta_threshold: float = 15.0
    
    # Metrics degradation
    max_acceptable_degradation: float = 5.0
    min_improvement_elsewhere: float = 20.0
    
    # Rollback window
    rollback_window_days: int = 30
    
    # Medical marketing context
    security_weight_multiplier: float = 2.0
    compliance_required: bool = True
    
    # GitHub search
    max_repos_to_analyze: int = 5
    min_repo_stars: int = 100
    min_repo_age_days: int = 365
```

### 7.2 Validation Gate Settings

```python
@dataclass
class ValidationGateSettings:
    # Gate 1: Sandbox Tests
    test_timeout_seconds: int = 300
    require_all_tests_pass: bool = True
    
    # Gate 2: Metrics Check
    allow_metrics_degradation: bool = False
    max_degradation_percent: float = 5.0
    
    # Gate 3: Security Scan
    bandit_severity_threshold: str = "medium"
    fail_on_hardcoded_secrets: bool = True
    
    # Gate 4: Compliance Check
    require_hipaa_compliance: bool = True
    require_encryption_at_rest: bool = True
    require_encryption_in_transit: bool = True
    
    # Gate 5: Integration Test
    test_event_bus_integration: bool = True
    test_obsidian_integration: bool = True
```

---

## 8. Success Metrics

### 8.1 Efficiency Metrics

**Adoption Time:**
- Target: 15-30 minutes per adoption
- Baseline (manual): 2-4 hours
- Improvement: 75-90% time reduction

**Adoptions Per Month:**
- Target: 10+ successful adoptions
- Baseline (manual): 2-3 adoptions
- Improvement: 3-5x increase

**Failed Adoptions:**
- Target: <5% failure rate
- Baseline (manual): ~30% failure rate
- Improvement: 6x reduction

### 8.2 Autonomy Metrics

**Autonomy Rate:**
- Target: 95%+ adoptions without human intervention
- Measurement: (auto_adoptions / total_adoptions) * 100

**Notification-Only Rate:**
- Target: 100% notifications, 0% approval requests
- Measurement: All adoptions send notifications, none require approval

### 8.3 Safety Metrics

**Production Incidents:**
- Target: 0 incidents from Teacher adoptions
- Measurement: Track incidents attributed to Teacher

**Validation Pass Rate:**
- Target: 90%+ first-attempt pass rate
- Measurement: (adoptions_passing_all_gates / total_adoption_attempts) * 100

**Rollback Rate:**
- Target: <10% rollback rate
- Measurement: (rollbacks / total_adoptions) * 100

### 8.4 Learning Metrics

**Decision Accuracy:**
- Target: +10% improvement per month
- Measurement: Track false positives/negatives, adjust thresholds

**Self-Correction Rate:**
- Target: 90%+ (Teacher learns from failures)
- Measurement: (corrected_decisions / total_failed_decisions) * 100

### 8.5 Skill Extraction Metrics ⭐

**Skills Extracted Per Repo:**
- Target: 10-20 skills per GitHub repo
- Measurement: Average skills extracted across all analyzed repos

**Skill Adoption Rate:**
- Target: 30-50% of extracted skills adopted
- Measurement: (skills_adopted / skills_extracted) * 100

**Skill Categories Coverage:**
- Target: All 5 categories represented (Resilience, Performance, Security, Observability, Error Handling)
- Measurement: Track distribution across categories

**Skill-Level Improvement:**
- Target: 15-25% average improvement per skill
- Measurement: Average (github_skill_score - our_skill_score) for adopted skills

**Teaching Success Rate:**
- Target: 95%+ skills taught successfully
- Measurement: (skills_taught_successfully / skills_attempted) * 100

**Integration Quality:**
- Target: 90%+ skills integrate without breaking existing code
- Measurement: (skills_integrated_cleanly / skills_taught) * 100

---

## 9. Implementation Timeline

### Phase 1: Architecture Analysis (3-4 hours)

**Tasks:**
1. Implement FileStructureAnalyzer
2. Implement ComponentRelationAnalyzer
3. Implement DesignPatternDetector
4. Implement TestCoverageAnalyzer
5. Implement ArchitectureAnalyzer (orchestrator)
6. Write unit tests (15+ tests)

**Deliverable:** ArchitectureAnalysis with quality_score

### Phase 1.5: Skill Extraction & Teaching Layer ⭐ (4-5 hours)

**Tasks:**
1. Implement SkillExtractor (pattern detection heuristics)
2. Implement SkillComparator (GitHub vs ours scoring)
3. Implement SkillSelector (selection strategies)
4. Implement SkillTeacher (pattern adaptation & integration)
5. Implement SkillExtractionOrchestrator
6. Write unit tests (20+ tests)
7. Write integration tests (skill extraction → comparison → teaching)

**Deliverable:** SkillExtractionReport with teaching results

### Phase 2: Solution Comparison (2-3 hours)

**Tasks:**
1. Implement ArchitectureScorer
2. Implement QualityScorer
3. Implement FitAnalyzer
4. Implement RiskAnalyzer
5. Implement DecisionMaker (autonomous rules)
6. Implement SolutionComparator (orchestrator)
7. Write unit tests (10+ tests)

**Deliverable:** ComparisonResult with autonomous decision

### Phase 3: Full Adoption (3-4 hours)

**Tasks:**
1. Implement SandboxManager
2. Implement FileCopier
3. Implement DependencyInstaller
4. Implement ImportUpdater
5. Implement TestMigrator
6. Implement ValidationGateRunner (5 gates)
7. Implement RollbackManager
8. Implement FullAdopter (orchestrator)
9. Write unit tests (15+ tests)

**Deliverable:** AdoptionResult with auto-merge/rollback

### Phase 4: Reporting & Integration (1-2 hours)

**Tasks:**
1. Implement AdoptionReportGenerator
2. Implement AuditTrailLogger
3. Implement NotificationSender
4. Implement TeacherAgent (main class)
5. Implement CLI commands
6. Write integration tests (5+ tests)
7. Update documentation

**Deliverable:** Complete Teacher Agent v2.0 system

**Total Time:** 8-12 hours

---

## 10. Risk Mitigation

### Risk 1: Bad Adoption Breaks Production

**Mitigation:**
- Sandbox isolation (git worktree)
- 5 validation gates (sequential, fail-fast)
- Auto-rollback on any gate failure
- 30-day rollback window

**Likelihood:** Low  
**Impact:** Low (auto-rollback)

### Risk 2: Teacher Makes Wrong Decision

**Mitigation:**
- Conservative thresholds (Quality ≥70, Fit ≥70, Risk ≤30)
- Audit trail for all decisions
- User notifications with reasoning
- Self-learning from results

**Likelihood:** Medium (10-15% initially)  
**Impact:** Low (validation gates catch issues)

### Risk 3: Third-Party Agent Incompatibility

**Mitigation:**
- Higher quality threshold (≥15 points better)
- Integration validation in sandbox
- Event Bus + Obsidian compatibility checks
- Rollback available

**Likelihood:** Medium  
**Impact:** Low (validation catches incompatibility)

### Risk 4: Metrics Degradation Not Caught

**Mitigation:**
- Comprehensive metrics tracking
- Zero tolerance for degradation (default)
- Exception only for significant trade-offs
- User notification on exceptions

**Likelihood:** Low  
**Impact:** Medium (medical marketing context)

---

**Created:** 2026-05-13  
**Author:** meAI Architect (via Claude Sonnet 4)  
**Status:** 📋 Ready for Review

---

## 9. Monitoring & Alerting System

### 9.1 Purpose

**Критически важно:** Если Exa, GitHub API или другие endpoints недоступны, Teacher Agent не может получать данные для обучения системы. Это означает, что система перестаёт расти и улучшаться.

**Решение:** Автоматические алерты пользователю через Operator при любых проблемах с источниками данных.

### 9.2 Monitored Endpoints

**Research Endpoints:**
1. **Exa API** (web_search_exa, deep_researcher_start)
   - Critical: без этого нет deep research
   - Fallback: Brave Search API (если доступен)

2. **GitHub API** (search repositories, get repo details)
   - Critical: без этого нет GitHub discovery
   - Rate limit: 60 req/hour (unauthenticated), 5000 req/hour (authenticated)

3. **Brave Search API** (fallback для Exa)
   - Optional: используется только если Exa недоступен

**Integration Endpoints:**
4. **Event Bus** (publish events)
   - Critical: без этого нет коммуникации с Operator

5. **Obsidian Vault** (write logs, decisions)
   - Critical: без этого нет audit trail

### 9.3 Health Check System

```python
@dataclass
class EndpointHealth:
    endpoint_name: str              # "exa_api", "github_api", etc.
    status: str                     # "healthy", "degraded", "down"
    last_check: datetime
    last_success: datetime
    consecutive_failures: int
    error_message: str | None
    response_time_ms: float | None

@dataclass
class SystemHealth:
    overall_status: str             # "healthy", "degraded", "critical"
    endpoints: list[EndpointHealth]
    can_research: bool              # Can perform deep research?
    can_discover_github: bool       # Can find GitHub repos?
    can_alert: bool                 # Can send alerts to Operator?
    timestamp: datetime

class HealthMonitor:
    def __init__(self, event_bus: EventBus, obsidian: ObsidianVault):
        self.event_bus = event_bus
        self.obsidian = obsidian
        self.endpoints = {
            "exa_api": EndpointHealth(...),
            "github_api": EndpointHealth(...),
            "brave_api": EndpointHealth(...),
            "event_bus": EndpointHealth(...),
            "obsidian": EndpointHealth(...)
        }
        self.alert_threshold = 3  # Alert after 3 consecutive failures
    
    async def check_all_endpoints(self) -> SystemHealth:
        """Check health of all critical endpoints."""
        for name, endpoint in self.endpoints.items():
            await self._check_endpoint(name, endpoint)
        
        # Determine overall status
        overall_status = self._calculate_overall_status()
        
        # Check capabilities
        can_research = self._can_perform_research()
        can_discover_github = self._can_discover_github()
        can_alert = self._can_send_alerts()
        
        health = SystemHealth(
            overall_status=overall_status,
            endpoints=list(self.endpoints.values()),
            can_research=can_research,
            can_discover_github=can_discover_github,
            can_alert=can_alert,
            timestamp=datetime.now()
        )
        
        # Send alerts if needed
        await self._send_alerts_if_needed(health)
        
        return health
    
    async def _check_endpoint(self, name: str, endpoint: EndpointHealth):
        """Check single endpoint health."""
        start_time = time.time()
        
        try:
            if name == "exa_api":
                # Quick test: search for "test"
                await self.exa_client.web_search_exa(
                    query="test",
                    numResults=1
                )
            elif name == "github_api":
                # Quick test: search for "python"
                await self.github_client.search_repositories(
                    query="python",
                    per_page=1
                )
            elif name == "brave_api":
                # Quick test: search for "test"
                await self.brave_client.search(query="test", count=1)
            elif name == "event_bus":
                # Quick test: publish test event
                await self.event_bus.publish(Event(
                    type="teacher.health_check",
                    data={"test": True}
                ))
            elif name == "obsidian":
                # Quick test: write to vault
                await self.obsidian.log("Health check", metadata={"test": True})
            
            # Success
            response_time = (time.time() - start_time) * 1000
            endpoint.status = "healthy"
            endpoint.last_check = datetime.now()
            endpoint.last_success = datetime.now()
            endpoint.consecutive_failures = 0
            endpoint.error_message = None
            endpoint.response_time_ms = response_time
            
        except Exception as e:
            # Failure
            endpoint.status = "down"
            endpoint.last_check = datetime.now()
            endpoint.consecutive_failures += 1
            endpoint.error_message = str(e)
            endpoint.response_time_ms = None
    
    def _calculate_overall_status(self) -> str:
        """Calculate overall system health status."""
        critical_endpoints = ["exa_api", "github_api", "event_bus"]
        
        # Check critical endpoints
        critical_down = [
            name for name in critical_endpoints
            if self.endpoints[name].status == "down"
        ]
        
        if len(critical_down) >= 2:
            return "critical"  # 2+ critical endpoints down
        elif len(critical_down) == 1:
            return "degraded"  # 1 critical endpoint down
        else:
            return "healthy"   # All critical endpoints up
    
    def _can_perform_research(self) -> bool:
        """Check if system can perform deep research."""
        exa_healthy = self.endpoints["exa_api"].status == "healthy"
        brave_healthy = self.endpoints["brave_api"].status == "healthy"
        
        # Can research if Exa OR Brave is available
        return exa_healthy or brave_healthy
    
    def _can_discover_github(self) -> bool:
        """Check if system can discover GitHub repos."""
        return self.endpoints["github_api"].status == "healthy"
    
    def _can_send_alerts(self) -> bool:
        """Check if system can send alerts to Operator."""
        return self.endpoints["event_bus"].status == "healthy"
    
    async def _send_alerts_if_needed(self, health: SystemHealth):
        """Send alerts to Operator if endpoints are down."""
        for endpoint in health.endpoints:
            # Alert after N consecutive failures
            if endpoint.consecutive_failures >= self.alert_threshold:
                await self._send_alert(endpoint, health)
    
    async def _send_alert(
        self,
        endpoint: EndpointHealth,
        health: SystemHealth
    ):
        """Send alert to Operator about endpoint failure."""
        # Determine severity
        if endpoint.endpoint_name in ["exa_api", "github_api"]:
            severity = "CRITICAL"
        else:
            severity = "WARNING"
        
        # Determine impact
        impact = []
        if not health.can_research:
            impact.append("❌ Cannot perform deep research")
        if not health.can_discover_github:
            impact.append("❌ Cannot discover GitHub repos")
        if not health.can_alert:
            impact.append("❌ Cannot send alerts (this is the last one!)")
        
        # Create alert message
        alert_message = f"""
🚨 Teacher Agent Alert: {severity}

Endpoint: {endpoint.endpoint_name}
Status: {endpoint.status}
Consecutive failures: {endpoint.consecutive_failures}
Last success: {endpoint.last_success.strftime('%Y-%m-%d %H:%M:%S')}
Error: {endpoint.error_message}

Impact on system:
{chr(10).join(impact) if impact else "✅ System can still operate (fallback available)"}

Overall system status: {health.overall_status.upper()}

Action required:
1. Check {endpoint.endpoint_name} availability
2. Verify API keys/credentials
3. Check rate limits (GitHub: 60/hour without token, 5000/hour with token)
4. Review error logs in Obsidian vault

⚠️ System growth is blocked until this is resolved!
        """.strip()
        
        # Send to Operator via Event Bus
        try:
            await self.event_bus.publish(Event(
                type="teacher.alert",
                priority=Priority.P0 if severity == "CRITICAL" else Priority.P1,
                data={
                    "severity": severity,
                    "endpoint": endpoint.endpoint_name,
                    "message": alert_message,
                    "health": health,
                    "timestamp": datetime.now().isoformat()
                }
            ))
            
            # Log to Obsidian
            await self.obsidian.log(
                f"Alert sent: {endpoint.endpoint_name} down",
                metadata={
                    "severity": severity,
                    "consecutive_failures": endpoint.consecutive_failures,
                    "error": endpoint.error_message
                }
            )
            
        except Exception as e:
            # Cannot send alert via Event Bus - log to Obsidian as last resort
            await self.obsidian.log(
                f"CRITICAL: Cannot send alert! Event Bus down. Original alert: {alert_message}",
                metadata={"error": str(e)}
            )
```

### 9.4 Integration with TeacherAgent

```python
class TeacherAgent:
    def __init__(self, event_bus: EventBus, obsidian: ObsidianVault):
        self.event_bus = event_bus
        self.obsidian = obsidian
        
        # Existing components
        self.research_orchestrator = ResearchOrchestrator()
        self.skill_orchestrator = SkillExtractionOrchestrator()
        # ...
        
        # NEW: Health monitoring
        self.health_monitor = HealthMonitor(event_bus, obsidian)
    
    async def learn_from_github(
        self,
        subagent_name: str,
        research_depth: str = "standard"
    ) -> LearningResult:
        """Main learning workflow with health checks."""
        
        # 1. Check system health BEFORE starting
        health = await self.health_monitor.check_all_endpoints()
        
        if health.overall_status == "critical":
            # Cannot proceed - send alert and abort
            await self._handle_critical_health(health)
            raise SystemHealthError(
                "Cannot proceed: critical endpoints down. "
                "User has been alerted via Operator."
            )
        
        if health.overall_status == "degraded":
            # Can proceed with limitations - log warning
            await self.obsidian.log(
                f"Starting learning with degraded health: {health}",
                metadata={"subagent": subagent_name}
            )
        
        # 2. Proceed with learning workflow
        try:
            # GitHub discovery
            if health.can_discover_github:
                repos = await self.find_github_solutions(...)
            else:
                # Fallback: use cached repos or skip
                repos = await self._get_cached_repos(subagent_name)
            
            # Deep research
            if health.can_research:
                research = await self.research_orchestrator.research_topic(...)
            else:
                # Fallback: use cached research or skip
                research = await self._get_cached_research(subagent_name)
            
            # Continue with skill extraction, comparison, teaching...
            
        except Exception as e:
            # Check if failure is due to endpoint issues
            health_after = await self.health_monitor.check_all_endpoints()
            if health_after.overall_status != health.overall_status:
                # Health degraded during execution - alert user
                await self._handle_health_degradation(health, health_after)
            raise
    
    async def _handle_critical_health(self, health: SystemHealth):
        """Handle critical system health - alert user and abort."""
        alert_message = f"""
🚨 CRITICAL: Teacher Agent Cannot Operate

System health: {health.overall_status.upper()}

Endpoints down:
{chr(10).join(f'- {e.endpoint_name}: {e.error_message}' for e in health.endpoints if e.status == 'down')}

Impact:
- Can research: {health.can_research}
- Can discover GitHub: {health.can_discover_github}
- Can alert: {health.can_alert}

⚠️ SYSTEM GROWTH IS BLOCKED!

Action required immediately:
1. Check endpoint availability
2. Verify API keys/credentials
3. Review rate limits
4. Check error logs in Obsidian vault

Learning workflow aborted.
        """.strip()
        
        await self.event_bus.publish(Event(
            type="teacher.critical_health",
            priority=Priority.P0,
            data={
                "message": alert_message,
                "health": health,
                "timestamp": datetime.now().isoformat()
            }
        ))
    
    async def _handle_health_degradation(
        self,
        health_before: SystemHealth,
        health_after: SystemHealth
    ):
        """Handle health degradation during execution."""
        alert_message = f"""
⚠️ WARNING: System Health Degraded During Execution

Before: {health_before.overall_status}
After: {health_after.overall_status}

New failures:
{chr(10).join(
    f'- {e.endpoint_name}: {e.error_message}'
    for e in health_after.endpoints
    if e.status == 'down' and e.consecutive_failures == 1
)}

Current learning workflow may be incomplete.
        """.strip()
        
        await self.event_bus.publish(Event(
            type="teacher.health_degraded",
            priority=Priority.P1,
            data={
                "message": alert_message,
                "health_before": health_before,
                "health_after": health_after,
                "timestamp": datetime.now().isoformat()
            }
        ))
```

### 9.5 Operator Integration

```python
class Operator:
    async def handle_teacher_alert(self, event: Event):
        """Handle alerts from Teacher Agent."""
        severity = event.data["severity"]
        message = event.data["message"]
        
        # Log to Operator's vault
        await self.obsidian.log(
            f"Teacher Alert: {severity}",
            metadata=event.data
        )
        
        # Notify user via configured channel
        if severity == "CRITICAL":
            # Critical: notify immediately
            await self._notify_user_urgent(message)
        else:
            # Warning: add to daily digest
            await self._add_to_digest(message)
    
    async def _notify_user_urgent(self, message: str):
        """Notify user immediately about critical issue."""
        # Option 1: Telegram (if configured)
        if self.telegram_enabled:
            await self.telegram.send_message(
                chat_id=self.user_chat_id,
                text=f"🚨 URGENT: Teacher Agent\n\n{message}"
            )
        
        # Option 2: Email (if configured)
        if self.email_enabled:
            await self.email.send(
                to=self.user_email,
                subject="🚨 URGENT: Teacher Agent Cannot Operate",
                body=message
            )
        
        # Option 3: Console output (always)
        print(f"\n{'='*60}")
        print("🚨 URGENT ALERT FROM TEACHER AGENT")
        print(f"{'='*60}")
        print(message)
        print(f"{'='*60}\n")
```

### 9.6 Health Check Schedule

**Frequency:**
- Before each learning cycle: Always check health
- During learning cycle: Check after each major step (research, GitHub discovery, skill extraction)
- Periodic: Every 1 hour (background health check)

**Alert Thresholds:**
- 3 consecutive failures → Send alert
- 5 consecutive failures → Mark as critical
- 10 consecutive failures → Disable endpoint (use fallback)

### 9.7 Fallback Strategies

**If Exa API down:**
- Use Brave Search API (if available)
- Use cached research from previous cycles
- Skip deep research, proceed with GitHub discovery only

**If GitHub API down:**
- Use cached repository list
- Skip new repository discovery
- Focus on improving existing subagents with cached data

**If both Exa and GitHub down:**
- CRITICAL: Cannot proceed with learning
- Alert user immediately
- System growth is blocked

**If Event Bus down:**
- CRITICAL: Cannot communicate with Operator
- Log to Obsidian vault as last resort
- System is isolated

### 9.8 Metrics & Monitoring

**Health Metrics:**
- Endpoint uptime percentage (target: 99%+)
- Average response time per endpoint
- Consecutive failure count
- Time since last successful check

**Alert Metrics:**
- Alerts sent per day
- Alert severity distribution (CRITICAL vs WARNING)
- Time to resolution (from alert to endpoint recovery)
- False positive rate

**Impact Metrics:**
- Learning cycles blocked due to endpoint failures
- Subagents not updated due to data unavailability
- System growth rate (with vs without endpoint issues)

### 9.9 Success Criteria

**System Health:**
- ✅ All critical endpoints monitored
- ✅ Alerts sent within 1 minute of failure threshold
- ✅ User notified via Operator (Telegram/Email/Console)
- ✅ Fallback strategies implemented
- ✅ No silent failures (always alert on critical issues)

**User Experience:**
- ✅ User knows immediately when system cannot grow
- ✅ Clear action items in alert messages
- ✅ No surprise "why isn't Teacher working?" moments
- ✅ Transparency: user sees all endpoint health status

---

### 1.4 Triggers & Workflow

**КРИТИЧЕСКИ ВАЖНО:** Teacher Agent должен работать автономно по расписанию и событиям, не только по ручным командам.

#### Автоматические Триггеры

**1. Scheduled (Cron-like):**
```python
# Полный цикл обучения
- Каждые 2 недели: Audit всех субагентов + Learning cycle для критических
- Каждую неделю: GitHub market research (новые топовые репо)
- Каждый день: Health check всех субагентов (метрики, статус)

# Реализация через Event Bus
await event_bus.schedule_recurring(
    event_type="teacher.full_learning_cycle",
    interval=timedelta(weeks=2),
    priority=Priority.P2
)
```

**2. Event-Driven:**
```python
# Новый субагент создан
Event: "subagent.created"
→ Teacher: Initial research + teaching

# Субагент показывает плохие метрики
Event: "subagent.metrics_degraded"
→ Teacher: Check for better solutions on GitHub

# GitHub webhook: новый релиз в отслеживаемом репо
Event: "github.release_published"
→ Teacher: Analyze changes, update if needed

# Субагент "заболел" (код удалён/переименован)
Event: "subagent.missing"
→ Teacher: Handle via SystemAuditor
```

**3. Manual Triggers:**
```bash
# Полный цикл для всех субагентов
python scripts/teacher_cli.py run-learning-cycle --strategy sequential

# Аудит системы
python scripts/teacher_cli.py audit-system

# Обучение конкретного субагента
python scripts/teacher_cli.py teach <subagent_name> --depth deep

# Исследование рынка для категории
python scripts/teacher_cli.py research-market --category seo
```

#### Complete Workflow

```
┌─────────────────────────────────────────┐
│  TRIGGER (auto/manual)                  │
│  - Scheduled (every 2 weeks)            │
│  - Event (new subagent, bad metrics)    │
│  - Manual (CLI command)                 │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  1. SYSTEM AUDIT                        │
│  SystemAuditor.audit_all_subagents()    │
│  - Discover all subagents               │
│  - Check health (healthy/degraded/...)  │
│  - Check last taught date               │
│  - Check performance metrics            │
│  - Handle missing/deprecated            │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  2. LEARNING PLAN                       │
│  LearningScheduler.create_learning_plan()│
│  - Prioritize (P1-P4)                   │
│  - Choose strategy (sequential/parallel)│
│  - Estimate time & cost                 │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  3. MARKET RESEARCH (for each subagent) │
│  ResearchOrchestrator.research_topic()  │
│  - Deep research (Exa)                  │
│  - GitHub search (API + Exa)            │
│  - Rank repos                           │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  4. TEACH (for each subagent)           │
│  SkillExtractionOrchestrator.teach()    │
│  - Clone → Analyze → Extract → Compare  │
│  - Select → Teach → Validate            │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  5. REPORT                              │
│  - Update Obsidian vault                │
│  - Send summary to Operator             │
│  - Schedule next learning cycle         │
└─────────────────────────────────────────┘
```

#### Frequency & Cost Estimates

**Full Learning Cycle (all subagents):**
- Frequency: Every 2 weeks
- Duration: 2-4 hours (depends on # of subagents)
- Cost: $5-15 (depends on research depth)

**Single Subagent Teaching:**
- Duration: 15-30 minutes
- Cost: $1.50-3.00 (standard/deep research)

**Daily Health Check:**
- Duration: 5 minutes
- Cost: $0 (no external APIs)


### 2.1 System Auditor

**Purpose:** Аудит всех субагентов системы, обнаружение "заболевших" и "отчисленных", приоритизация обучения.

#### 2.1.1 Data Structures

```python
@dataclass
class SubagentHealth:
    name: str
    status: str                    # "healthy" | "degraded" | "missing" | "deprecated"
    last_taught: datetime | None
    performance_metrics: dict[str, float]
    needs_update: bool
    priority: int                  # 1-5 (1 = critical, 5 = low)
    reason: str                    # Why needs update or status

@dataclass
class SystemAuditReport:
    audit_timestamp: datetime
    total_subagents: int
    healthy: int
    degraded: int
    missing: int
    deprecated: int
    needs_teaching: list[SubagentHealth]
    priority_queue: list[SubagentHealth]  # Sorted by priority
```

#### 2.1.2 SystemAuditor Implementation

```python
class SystemAuditor:
    """Аудит всей системы субагентов."""
    
    def __init__(self, event_bus: EventBus, obsidian: ObsidianVault):
        self.event_bus = event_bus
        self.obsidian = obsidian
        self.registry_path = "AIM/src/aim/subagents/"
        self.critical_subagents = [
            "keyword_research",
            "content_gap_analysis",
            "competitor_analysis",
            "technical_seo"
        ]
    
    async def audit_all_subagents(self) -> SystemAuditReport:
        """
        Полный аудит всех субагентов системы.
        
        Workflow:
        1. Discover all subagents (from registry + filesystem)
        2. Check each subagent health
        3. Classify by status
        4. Prioritize for teaching
        5. Handle missing/deprecated
        """
        
        # 1. Discover all subagents
        subagents = await self._discover_all_subagents()
        
        # 2. Check health for each
        health_reports = []
        for subagent in subagents:
            health = await self._check_subagent_health(subagent)
            health_reports.append(health)
        
        # 3. Classify by status
        healthy = [h for h in health_reports if h.status == "healthy"]
        degraded = [h for h in health_reports if h.status == "degraded"]
        missing = [h for h in health_reports if h.status == "missing"]
        deprecated = [h for h in health_reports if h.status == "deprecated"]
        
        # 4. Prioritize for teaching
        needs_teaching = [h for h in health_reports if h.needs_update]
        priority_queue = sorted(needs_teaching, key=lambda h: h.priority)
        
        # 5. Handle missing/deprecated
        for subagent in missing:
            await self._handle_missing_subagent(subagent)
        
        # 6. Create report
        report = SystemAuditReport(
            audit_timestamp=datetime.now(),
            total_subagents=len(subagents),
            healthy=len(healthy),
            degraded=len(degraded),
            missing=len(missing),
            deprecated=len(deprecated),
            needs_teaching=needs_teaching,
            priority_queue=priority_queue
        )
        
        # 7. Log to Obsidian
        await self.obsidian.log(
            f"System audit completed: {len(subagents)} total, {len(needs_teaching)} need teaching",
            metadata=report.__dict__
        )
        
        return report
    
    async def _discover_all_subagents(self) -> list[str]:
        """
        Discover all subagents from:
        1. Registry (AIM/src/aim/subagents/)
        2. Specs (docs/subagents-specs/)
        3. Obsidian vaults (obsidian/*/wiki/agents/)
        """
        
        subagents = set()
        
        # From filesystem
        if os.path.exists(self.registry_path):
            for item in os.listdir(self.registry_path):
                if os.path.isdir(os.path.join(self.registry_path, item)):
                    if not item.startswith("_"):
                        subagents.add(item)
        
        # From specs
        specs_path = "docs/subagents-specs/"
        if os.path.exists(specs_path):
            for spec_file in os.listdir(specs_path):
                if spec_file.endswith("_SPEC.md"):
                    name = spec_file.replace("_SPEC.md", "").lower()
                    subagents.add(name)
        
        return sorted(list(subagents))
    
    async def _check_subagent_health(self, subagent_name: str) -> SubagentHealth:
        """
        Check health of a single subagent.
        
        Checks:
        1. Code exists?
        2. Last taught date (from Obsidian)
        3. Performance metrics (from database)
        4. Recent errors (from logs)
        """
        
        # Check if code exists
        code_path = os.path.join(self.registry_path, subagent_name)
        code_exists = os.path.exists(code_path)
        
        if not code_exists:
            return SubagentHealth(
                name=subagent_name,
                status="missing",
                last_taught=None,
                performance_metrics={},
                needs_update=False,
                priority=1 if subagent_name in self.critical_subagents else 3,
                reason="Code directory not found"
            )
        
        # Check last taught date
        last_taught = await self._get_last_taught_date(subagent_name)
        days_since_taught = (datetime.now() - last_taught).days if last_taught else 999
        
        # Check performance metrics
        metrics = await self._get_performance_metrics(subagent_name)
        
        # Determine status
        if days_since_taught > 60:
            status = "degraded"
            reason = f"Not taught for {days_since_taught} days"
            needs_update = True
            priority = 2
        elif metrics.get("error_rate", 0) > 0.1:
            status = "degraded"
            reason = f"High error rate: {metrics['error_rate']:.1%}"
            needs_update = True
            priority = 1
        elif days_since_taught > 28:
            status = "healthy"
            reason = "Due for routine update"
            needs_update = True
            priority = 3
        else:
            status = "healthy"
            reason = "Recently taught, metrics good"
            needs_update = False
            priority = 5
        
        # Critical subagents get higher priority
        if subagent_name in self.critical_subagents and needs_update:
            priority = max(1, priority - 1)
        
        return SubagentHealth(
            name=subagent_name,
            status=status,
            last_taught=last_taught,
            performance_metrics=metrics,
            needs_update=needs_update,
            priority=priority,
            reason=reason
        )
    
    async def _handle_missing_subagent(self, subagent: SubagentHealth):
        """
        Handle subagent that is "missing" (code deleted/renamed).
        
        Actions:
        1. Check git history - was it renamed?
        2. If renamed → update registry
        3. If deleted → mark as deprecated
        4. If critical → alert user via Operator
        """
        
        # Check git history
        git_log = await self._check_git_history(subagent.name)
        
        if git_log.get("renamed_to"):
            # Renamed → update registry
            new_name = git_log["renamed_to"]
            await self.obsidian.log(
                f"Subagent renamed: {subagent.name} → {new_name}",
                metadata={"old_name": subagent.name, "new_name": new_name}
            )
            
        elif git_log.get("deleted"):
            # Deleted → mark deprecated
            await self.obsidian.log(
                f"Subagent deleted: {subagent.name}",
                metadata={"subagent": subagent.name, "deleted_at": git_log["deleted_at"]}
            )
            
            # If critical → alert
            if subagent.name in self.critical_subagents:
                await self.event_bus.publish(Event(
                    type="teacher.critical_subagent_missing",
                    priority=Priority.P0,
                    data={
                        "subagent": subagent.name,
                        "message": f"🚨 Critical subagent {subagent.name} was deleted!",
                        "action_required": "Restore or replace immediately"
                    }
                ))
    
    async def _check_git_history(self, subagent_name: str) -> dict:
        """Check git history for renames/deletions."""
        
        # Check for renames
        result = subprocess.run(
            ["git", "log", "--follow", "--diff-filter=R", "--", f"*{subagent_name}*"],
            capture_output=True,
            text=True
        )
        
        if "renamed" in result.stdout.lower():
            # Parse renamed_to from git log
            # Simplified - real implementation would parse git output
            return {"renamed_to": "new_name"}
        
        # Check for deletions
        result = subprocess.run(
            ["git", "log", "--diff-filter=D", "--", f"*{subagent_name}*"],
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            return {"deleted": True, "deleted_at": datetime.now()}
        
        return {}
    
    async def _get_last_taught_date(self, subagent_name: str) -> datetime | None:
        """Get last taught date from Obsidian vault."""
        
        # Read from obsidian/teacher/wiki/agents/subagents-profile.md
        profile_path = "obsidian/teacher/wiki/agents/subagents-profile.md"
        
        if not os.path.exists(profile_path):
            return None
        
        # Parse profile for last_taught date
        # Simplified - real implementation would parse markdown
        return datetime.now() - timedelta(days=30)  # Placeholder
    
    async def _get_performance_metrics(self, subagent_name: str) -> dict[str, float]:
        """Get performance metrics from database."""
        
        # Query database for recent metrics
        # Simplified - real implementation would query actual DB
        return {
            "success_rate": 0.95,
            "error_rate": 0.05,
            "avg_response_time": 1.2,
            "requests_per_day": 100
        }
```

#### 2.1.3 CLI Commands

```bash
# Full system audit
python scripts/teacher_cli.py audit-system

# Output:
# ╔═══════════════════════════════════════════════════════════╗
# ║  System Audit Report - 2026-05-13 17:15                  ║
# ╚═══════════════════════════════════════════════════════════╝
# 
# Total subagents: 25
# ✅ Healthy: 20
# ⚠️  Degraded: 3
#    - keyword_research (not taught for 45 days)
#    - content_gap_analysis (high error rate: 12%)
#    - ads_budget_optimizer (not taught for 35 days)
# ❌ Missing: 1
#    - old_analytics_agent (deleted)
# 🗑️  Deprecated: 1
#    - legacy_seo_agent
# 
# Priority Queue (needs teaching):
# 1. [P1] content_gap_analysis (high error rate)
# 2. [P2] keyword_research (not taught for 45 days)
# 3. [P2] ads_budget_optimizer (not taught for 35 days)
# 4. [P3] technical_seo (routine update)
# 5. [P3] competitor_analyzer (routine update)

# Check specific subagent
python scripts/teacher_cli.py check-health <subagent_name>
```

---

### 2.2 Learning Scheduler

**Purpose:** Планирование и приоритизация обучения на основе аудита системы.

#### 2.2.1 Data Structures

```python
@dataclass
class LearningTask:
    subagent_name: str
    priority: Priority              # P1-P4
    reason: str                     # Why needs teaching
    research_depth: str             # "quick" | "standard" | "deep"
    estimated_time: int             # Minutes
    estimated_cost: float           # USD

@dataclass
class LearningPlan:
    created_at: datetime
    strategy: str                   # "sequential" | "parallel" | "batch"
    total_subagents: int
    total_estimated_time: int       # Minutes
    total_estimated_cost: float     # USD
    tasks: list[LearningTask]
```

#### 2.2.2 LearningScheduler Implementation

```python
class LearningScheduler:
    """Планирование и приоритизация обучения."""
    
    def __init__(self, event_bus: EventBus, obsidian: ObsidianVault):
        self.event_bus = event_bus
        self.obsidian = obsidian
    
    async def create_learning_plan(
        self,
        audit_report: SystemAuditReport,
        strategy: str = "sequential"
    ) -> LearningPlan:
        """
        Create learning plan based on audit report.
        
        Priorities:
        - P1 (CRITICAL): Degraded + critical for business
        - P2 (HIGH): Not taught for >4 weeks
        - P3 (MEDIUM): New top repos on GitHub
        - P4 (LOW): Optional improvements
        
        Strategies:
        - sequential: Teach one by one (safe, slow)
        - parallel: Teach multiple in parallel (fast, risky)
        - batch: Group by category (SEO, Content, Ads)
        """
        
        tasks = []
        
        # P1: Critical degraded subagents
        for subagent in audit_report.priority_queue:
            if subagent.priority == 1:
                tasks.append(LearningTask(
                    subagent_name=subagent.name,
                    priority=Priority.P1,
                    reason=subagent.reason,
                    research_depth="deep",
                    estimated_time=60,
                    estimated_cost=3.0
                ))
        
        # P2: Not taught recently (>28 days)
        for subagent in audit_report.priority_queue:
            if subagent.priority == 2:
                days_since = (datetime.now() - subagent.last_taught).days if subagent.last_taught else 999
                tasks.append(LearningTask(
                    subagent_name=subagent.name,
                    priority=Priority.P2,
                    reason=f"Not taught for {days_since} days",
                    research_depth="standard",
                    estimated_time=30,
                    estimated_cost=1.5
                ))
        
        # P3: Routine updates
        for subagent in audit_report.priority_queue:
            if subagent.priority == 3:
                tasks.append(LearningTask(
                    subagent_name=subagent.name,
                    priority=Priority.P3,
                    reason="Routine update",
                    research_depth="quick",
                    estimated_time=15,
                    estimated_cost=0.5
                ))
        
        # Calculate totals
        total_time = sum(t.estimated_time for t in tasks)
        total_cost = sum(t.estimated_cost for t in tasks)
        
        plan = LearningPlan(
            created_at=datetime.now(),
            strategy=strategy,
            total_subagents=len(tasks),
            total_estimated_time=total_time,
            total_estimated_cost=total_cost,
            tasks=tasks
        )
        
        # Save plan to Obsidian
        await self._save_plan(plan)
        
        return plan
    
    async def _save_plan(self, plan: LearningPlan):
        """Save learning plan to Obsidian."""
        
        plan_md = f"""# Learning Plan - {plan.created_at.strftime('%Y-%m-%d')}

**Strategy:** {plan.strategy}  
**Total Subagents:** {plan.total_subagents}  
**Estimated Time:** {plan.total_estimated_time} minutes  
**Estimated Cost:** ${plan.total_estimated_cost:.2f}

## Tasks

"""
        
        for i, task in enumerate(plan.tasks, 1):
            plan_md += f"""### {i}. {task.subagent_name} [{task.priority.name}]

**Reason:** {task.reason}  
**Research Depth:** {task.research_depth}  
**Estimated Time:** {task.estimated_time} min  
**Estimated Cost:** ${task.estimated_cost:.2f}

---

"""
        
        plan_file = f"obsidian/teacher/wiki/projects/learning-plans/{plan.created_at.strftime('%Y-%m-%d')}.md"
        os.makedirs(os.path.dirname(plan_file), exist_ok=True)
        
        with open(plan_file, "w") as f:
            f.write(plan_md)
        
        await self.obsidian.log(
            f"Learning plan created: {plan.total_subagents} subagents, {plan.total_estimated_time} min, ${plan.total_estimated_cost:.2f}",
            metadata=plan.__dict__
        )
```

#### 2.2.3 CLI Commands

```bash
# Create learning plan from audit
python scripts/teacher_cli.py create-learning-plan --strategy sequential

# Output:
# ╔═══════════════════════════════════════════════════════════╗
# ║  Learning Plan Created - 2026-05-13 17:20                 ║
# ╚═══════════════════════════════════════════════════════════╝
# 
# Strategy: sequential
# Total subagents: 5
# Estimated time: 3 hours 15 minutes
# Estimated cost: $9.50
# 
# Tasks:
# 1. [P1] content_gap_analysis (deep, 60 min, $3.00)
# 2. [P2] keyword_research (standard, 30 min, $1.50)
# 3. [P2] ads_budget_optimizer (standard, 30 min, $1.50)
# 4. [P3] technical_seo (quick, 15 min, $0.50)
# 5. [P3] competitor_analyzer (quick, 15 min, $0.50)
# 
# Plan saved to: obsidian/teacher/wiki/projects/learning-plans/2026-05-13.md
# 
# Execute plan? (y/n)

# Execute existing plan
python scripts/teacher_cli.py execute-plan obsidian/teacher/wiki/projects/learning-plans/2026-05-13.md
```

