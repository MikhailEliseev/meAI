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
- Автоматическое принятие решений (Full/Partial/Custom/Reject)
- Изолированное тестирование в sandbox (git worktree)
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
1. Сканировать директории рекурсивно
2. Классифицировать файлы по назначению (regex patterns)
3. Подсчитать метрики (файлы, строки)
4. Определить entry points (main, __init__, app)

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
    dependency_graph: dict[str, list[str]]  # module -> [dependencies]
    coupling_score: float                    # 0-100 (100 = low coupling)
    circular_deps: list[tuple[str, str]]    # Circular dependencies
    core_components: list[str]               # Most depended upon
    peripheral_components: list[str]         # Least depended upon
```


**Algorithm:**
1. Parse imports из всех Python файлов (AST)
2. Построить граф зависимостей (networkx)
3. Найти circular dependencies (cycle detection)
4. Вычислить coupling score (edges / nodes ratio)
5. Определить core vs peripheral (in-degree)

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
    architecture_style: str                  # "Layered" | "Hexagonal" | "Clean" | "MVC"
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
1. Analyze class hierarchies (inheritance, interfaces)
2. Detect creation patterns (factory methods)
3. Find event/callback patterns (observer)
4. Check SOLID principles (SRP, OCP, LSP, ISP, DIP)
5. Determine architecture style (layering, dependencies)

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
    coverage_estimate: float                 # 0-100 (based on test count vs functions)
    has_fixtures: bool                       # pytest fixtures detected
    has_mocks: bool                          # unittest.mock or pytest-mock detected
    test_scenarios: list[str]                # Extracted from test names
    test_quality_score: float                # 0-100 (based on assertions, coverage)
```

**Algorithm:**
1. Найти все test файлы (test_*.py, *_test.py)
2. Классифицировать тесты (unit, integration, e2e) по patterns
3. Подсчитать количество тестов vs функций (coverage estimate)
4. Детектировать fixtures и mocks
5. Извлечь test scenarios из имён тестов
6. Оценить качество тестов (assertions per test, coverage)

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
risk_composite = 100 - risk_score.overall  # Invert (lower risk = higher score)

# Full Adoption
if quality_composite >= 80 and fit_composite >= 80 and risk_composite <= 20:
    return AdoptionDecision(
        decision="Full",
        rationale="High quality, excellent fit, low risk",
        confidence=90,
        action_plan="Clone → Adapt → Validate → Auto-merge"
    )

# Partial Adoption
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
    created_at: datetime
```

**Workflow:**
1. Create git worktree: `.claude/worktrees/teacher-{adoption_id}`
2. Create branch: `teacher/{subagent_name}-{adoption_id}`
3. Create snapshot (git commit hash)
4. Return SandboxEnvironment

**Implementation:**
```python
class SandboxManager:
    async def create_sandbox(
        self,
        subagent_name: str,
        adoption_id: str
    ) -> SandboxEnvironment:
        # Create worktree
        worktree_path = Path(f".claude/worktrees/teacher-{adoption_id}")
        branch_name = f"teacher/{subagent_name}-{adoption_id}"
        
        await self._run_git_command(
            f"worktree add {worktree_path} -b {branch_name}"
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
- Check for PII logging
- Check for encryption (at rest, in transit)
- Check for audit trail
- Pass condition: All compliance checks pass
- Fail condition: Any compliance check fails

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
        self.architecture_analyzer = ArchitectureAnalyzer()
        self.solution_comparator = SolutionComparator()
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
        query: str
    ) -> list[str]:
        """Search GitHub for relevant solutions."""
        # Use GitHub API to search
        # Rank by stars, activity, quality
        # Return top 5 repo URLs
    
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

# Поиск GitHub решений
python scripts/teacher_cli.py search <subagent_name> --query "circuit breaker python"

# Сравнение решений
python scripts/teacher_cli.py compare <subagent_name> --repo <github_url>

# Autonomous adoption (если decision Full/Partial)
python scripts/teacher_cli.py adopt <subagent_name> --repo <github_url>

# Rollback adoption
python scripts/teacher_cli.py rollback <adoption_id>

# Full autonomous learning cycle
python scripts/teacher_cli.py learn <subagent_name>

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
