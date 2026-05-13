# Teacher Agent v2.0 - Spec Review (Sonnet 4.5)

**Date:** 2026-05-13  
**Reviewer:** Implementation Reviewer (Sonnet 4.5)  
**Spec File:** docs/TEACHER_AGENT.md (2496 lines, 79 KB)  
**Perspective:** Implementation Feasibility

---

## Executive Summary

**Overall Assessment:** NEEDS CLARIFICATION BEFORE IMPLEMENTATION

Спецификация Teacher Agent v2.0 детальная и хорошо структурированная с точки зрения архитектуры, но имеет существенные пробелы в деталях реализации. Многие алгоритмы описаны на высоком уровне без конкретных шагов, dataclasses неполные, integration points недостаточно детализированы.

**Критические проблемы для implementation:**
1. AST analysis algorithms слишком абстрактные (как именно детектировать patterns?)
2. File adaptation logic не описана (как адаптировать imports, naming?)
3. Git operations детали отсутствуют (worktree commands, merge strategy)
4. Metrics calculation формулы неполные (как считать coupling_score?)
5. Error handling scenarios не покрыты (что делать при partial failures?)

**Готовность к реализации:** 60%  
**Требуется:** Добавить 8 blockers, 12 major clarifications

---

## Code Implementability

### Dataclasses Analysis

#### ✅ Well-Defined Dataclasses

**FileStructure** (lines 203-214):
- ✅ Все поля определены с типами
- ✅ Назначение каждого поля понятно
- ⚠️ Missing: regex patterns для классификации файлов

**ComponentRelations** (lines 244-251):
- ✅ Поля определены
- 🔴 **BLOCKER:** `coupling_score` формула не описана (как считать?)
- 🔴 **BLOCKER:** `dependency_graph` формат неясен (dict[str, list[str]] - что такое str? module path? file path?)

**DesignPatterns** (lines 286-291):
- ✅ Поля определены
- 🔴 **BLOCKER:** `architecture_style` enum values не определены (что кроме "Layered", "Hexagonal", "Clean", "MVC"?)
- ⚠️ Missing: `pattern_confidence` как считать?

**TestCoverage** (lines 333-340):
- ✅ Поля определены
- 🔴 **BLOCKER:** `coverage_estimate` формула не описана (test count / function count * 100?)
- 🔴 **BLOCKER:** `test_quality_score` формула не описана

**ArchitectureScore** (lines 444-449):
- ✅ Поля определены
- ✅ Формула overall score есть (lines 486-491)
- 🟡 **MAJOR:** Как считать каждый sub-score? (modularity, testability, etc.)

**AdoptionDecision** (lines 749-756):
- ✅ Поля определены
- ✅ Enum values для decision определены
- ✅ Хорошо структурирован

**SandboxEnvironment** (lines 996-1002):
- ✅ Поля определены
- 🔴 **BLOCKER:** Missing `venv_path` (Opus нашёл - нужен для dependency isolation)

**ValidationResult** (lines 1357-1363):
- ✅ Поля определены
- ✅ Хорошо структурирован

#### 🔴 Implementation Blockers in Dataclasses

1. **ComponentRelations.coupling_score** - формула не описана
2. **ComponentRelations.dependency_graph** - формат ключей неясен
3. **DesignPatterns.architecture_style** - enum values неполные
4. **TestCoverage.coverage_estimate** - формула не описана
5. **TestCoverage.test_quality_score** - формула не описана
6. **SandboxEnvironment.venv_path** - отсутствует (нужен!)

### Algorithms Analysis

#### FileStructureAnalyzer (lines 216-230)

**Algorithm (lines 217-220):**
```
1. Сканировать директории рекурсивно
2. Классифицировать файлы по назначению (regex patterns)
3. Подсчитать метрики (файлы, строки)
4. Определить entry points (main, __init__, app)
```

**Implementability:** 🟡 PARTIAL
- ✅ Шаг 1 понятен (os.walk или pathlib.rglob)
- 🔴 **BLOCKER:** Шаг 2 - regex patterns НЕ ОПРЕДЕЛЕНЫ (какие patterns для clients? models? utils?)
- ✅ Шаг 3 понятен (count files, sum lines)
- 🟡 **MAJOR:** Шаг 4 - как определить entry points? (по имени файла? по содержимому?)

**Missing Details:**
- Regex patterns для каждой категории
- Как обрабатывать __init__.py (entry point или нет?)
- Как считать строки кода (с комментариями? без?)

#### ComponentRelationAnalyzer (lines 254-271)

**Algorithm (lines 255-260):**
```
1. Parse imports из всех Python файлов (AST)
2. Построить граф зависимостей (networkx)
3. Найти circular dependencies (cycle detection)
4. Вычислить coupling score (edges / nodes ratio)
5. Определить core vs peripheral (in-degree)
```

**Implementability:** 🟡 PARTIAL
- ✅ Шаг 1 понятен (ast.parse, ast.Import, ast.ImportFrom)
- 🟡 **MAJOR:** Шаг 2 - формат графа неясен (nodes = file paths? module names?)
- ✅ Шаг 3 понятен (networkx.simple_cycles)
- 🔴 **BLOCKER:** Шаг 4 - формула coupling_score НЕ ОПРЕДЕЛЕНА (edges/nodes? normalized как?)
- 🟡 **MAJOR:** Шаг 5 - threshold для core vs peripheral не определён

**Missing Details:**
- Как мапить imports на file paths? (import foo.bar → foo/bar.py?)
- Как обрабатывать relative imports? (from . import x)
- Как обрабатывать external imports? (import numpy - игнорировать?)
- Coupling score формула и нормализация

#### DesignPatternDetector (lines 294-318)

**Algorithm (lines 302-307):**
```
1. Analyze class hierarchies (inheritance, interfaces)
2. Detect creation patterns (factory methods)
3. Find event/callback patterns (observer)
4. Check SOLID principles (SRP, OCP, LSP, ISP, DIP)
5. Determine architecture style (layering, dependencies)
```

**Implementability:** 🔴 INSUFFICIENT
- 🔴 **BLOCKER:** Шаг 1 - КАК анализировать? (AST? какие heuristics?)
- 🔴 **BLOCKER:** Шаг 2 - КАК детектировать factory? (по имени метода? по return type?)
- 🔴 **BLOCKER:** Шаг 3 - КАК детектировать observer? (по callback args? по naming?)
- 🔴 **BLOCKER:** Шаг 4 - КАК проверять SOLID? (конкретные правила?)
- 🔴 **BLOCKER:** Шаг 5 - КАК определять architecture style? (по dependency direction?)

**Missing Details:**
- Конкретные heuristics для каждого pattern
- AST node types для анализа
- Confidence calculation для каждого pattern
- SOLID compliance rules (что проверять для каждого принципа?)

**This is the BIGGEST implementation gap** - pattern detection слишком абстрактный.

#### TestCoverageAnalyzer (lines 341-361)

**Algorithm (lines 342-349):**
```
1. Найти все test файлы (test_*.py, *_test.py)
2. Классифицировать тесты (unit, integration, e2e) по patterns
3. Подсчитать количество тестов vs функций (coverage estimate)
4. Детектировать fixtures и mocks
5. Извлечь test scenarios из имён тестов
6. Оценить качество тестов (assertions per test, coverage)
```

**Implementability:** 🟡 PARTIAL
- ✅ Шаг 1 понятен (glob test_*.py)
- 🟡 **MAJOR:** Шаг 2 - patterns для классификации НЕ ОПРЕДЕЛЕНЫ
- 🔴 **BLOCKER:** Шаг 3 - формула coverage estimate НЕ ОПРЕДЕЛЕНА
- 🟡 **MAJOR:** Шаг 4 - как детектировать? (по import? по usage?)
- ✅ Шаг 5 понятен (parse test function names)
- 🔴 **BLOCKER:** Шаг 6 - формула test_quality_score НЕ ОПРЕДЕЛЕНА

**Missing Details:**
- Patterns для unit/integration/e2e classification
- Coverage estimate формула
- Test quality score формула (assertions per test weight?)


### Scoring Algorithms Analysis

#### ArchitectureScorer (lines 452-500)

**Scoring Criteria (lines 454-476):**

**Modularity (0-100):**
- Coupling score (from ComponentRelationAnalyzer)
- No circular dependencies: +20
- Clear separation of concerns: +20
- Small, focused modules: +10

**Implementability:** 🔴 INSUFFICIENT
- 🔴 **BLOCKER:** Coupling score формула не определена (base score?)
- 🟡 **MAJOR:** "Clear separation of concerns" - КАК проверять? (heuristic?)
- 🟡 **MAJOR:** "Small, focused modules" - threshold? (lines per file? functions per file?)

**Testability (0-100):**
- Test coverage estimate: 0-40 points
- Has fixtures: +15
- Has mocks: +15
- Test quality score: 0-30 points

**Implementability:** 🟡 PARTIAL
- 🔴 **BLOCKER:** Test coverage estimate формула не определена
- ✅ Has fixtures/mocks - понятно (boolean check)
- 🔴 **BLOCKER:** Test quality score формула не определена

**Maintainability (0-100):**
- Low complexity (cyclomatic): 0-30 points
- Good documentation: 0-30 points
- Consistent code style: 0-20 points
- Clear naming: 0-20 points

**Implementability:** 🟡 PARTIAL
- ✅ Cyclomatic complexity - понятно (radon)
- 🟡 **MAJOR:** "Good documentation" - КАК измерять? (docstring coverage? README quality?)
- 🟡 **MAJOR:** "Consistent code style" - КАК проверять? (ruff check? black --check?)
- 🟡 **MAJOR:** "Clear naming" - КАК оценивать? (length? conventions?)

**Scalability (0-100):**
- Design patterns detected: +10 per pattern (max 40)
- Architecture style (Layered/Hexagonal/Clean): +30
- SOLID compliance: +6 per principle (max 30)

**Implementability:** 🟡 PARTIAL
- 🔴 **BLOCKER:** Pattern detection не определён (см. DesignPatternDetector)
- 🟡 **MAJOR:** Architecture style scoring - только 4 стиля? (что если другой?)
- 🟡 **MAJOR:** SOLID compliance - как проверять каждый принцип?

#### QualityScorer (lines 516-575)

**Patterns (0-100):**
- Circuit breaker: +20
- Retry logic: +15
- Rate limiting: +15
- Caching: +15
- Logging: +10
- Metrics: +10
- Health checks: +15

**Implementability:** 🔴 INSUFFICIENT
- 🔴 **BLOCKER:** КАК детектировать каждый pattern? (по import? по code pattern?)
- Circuit breaker - искать `pybreaker`? или pattern в коде?
- Retry logic - искать `tenacity`? или `@retry` decorator?
- Rate limiting - искать `aiolimiter`? или custom implementation?

**Missing Details:**
- Конкретные detection rules для каждого pattern
- Что если custom implementation? (не библиотека)
- Confidence scoring для detection

**Error Handling (0-100):**
- Try/except coverage: 0-50 points
- Custom exceptions: +20
- Error logging: +15
- Graceful degradation: +15

**Implementability:** 🟡 PARTIAL
- 🟡 **MAJOR:** Try/except coverage - КАК считать? (% functions with try/except?)
- 🟡 **MAJOR:** Custom exceptions - КАК детектировать? (class inherits Exception?)
- 🟡 **MAJOR:** Error logging - КАК проверять? (logging.error in except blocks?)
- 🔴 **BLOCKER:** Graceful degradation - КАК детектировать? (слишком абстрактно)

#### FitAnalyzer (lines 598-652)

**Task Match (0-100):**
- Read subagent spec (Section 1: Overview, Section 3: Algorithm)
- Compare GitHub solution purpose vs spec purpose
- Check if GitHub solution solves same problem
- Semantic similarity: 0-100 points

**Implementability:** 🔴 INSUFFICIENT
- ✅ Read spec - понятно
- 🔴 **BLOCKER:** "Semantic similarity" - КАК вычислять? (embeddings? keyword matching? LLM?)
- Нужен конкретный алгоритм или библиотека

**Integration Effort (0-100):**
- Similar architecture style: +30
- Compatible with Event Bus: +25
- Compatible with Obsidian: +25
- Few external dependencies: +20

**Implementability:** 🟡 PARTIAL
- 🟡 **MAJOR:** "Similar architecture style" - КАК сравнивать? (string match?)
- 🔴 **BLOCKER:** "Compatible with Event Bus" - КАК проверять? (ищем EventBus usage? или можем адаптировать?)
- 🔴 **BLOCKER:** "Compatible with Obsidian" - КАК проверять?
- 🟡 **MAJOR:** "Few external dependencies" - threshold? (<10? <20?)

#### RiskAnalyzer (lines 676-731)

**Security (0-100):**
- No hardcoded secrets: +25
- No SQL injection vulnerabilities: +25
- No XSS vulnerabilities: +20
- Secure dependencies (no known CVEs): +30

**Implementability:** 🟡 PARTIAL
- ✅ Hardcoded secrets - bandit может детектировать
- ✅ SQL injection - bandit может детектировать
- ✅ XSS - bandit может детектировать
- 🟡 **MAJOR:** Secure dependencies - нужен safety/pip-audit (Opus нашёл)

**Stability (0-100):**
- Repo age > 1 year: +25
- Active maintenance (commits in last 3 months): +25
- Stars > 100: +20
- Issues/PRs ratio < 0.3: +30

**Implementability:** ✅ GOOD
- ✅ Все метрики можно получить из GitHub API
- ✅ Формулы понятны

---

## Integration Points

### Event Bus Integration

**Usage in Spec:**
- Line 144: "Отправляет notifications через Event Bus"
- Line 1932: NotificationSender uses EventBus
- Line 2071: Send notification via Event Bus

**Implementability:** ✅ GOOD
- ✅ EventBus interface определён в meAI framework
- ✅ Event type: "teacher.notification"
- ✅ Priority: P1
- ✅ Payload structure определена

**Missing Details:**
- ⚠️ Event subscription - кто слушает teacher.notification?
- ⚠️ Event acknowledgment - нужен ли?

### Obsidian Integration

**Usage in Spec:**
- Line 148-184: Obsidian vault structure
- Line 1780: Save report to Obsidian
- Line 1840: Save log entry to vault
- Line 1960: ObsidianVault parameter in TeacherAgent.__init__

**Implementability:** ✅ GOOD
- ✅ Vault structure определена
- ✅ File paths определены
- ✅ ObsidianVault interface существует в meAI framework

**Missing Details:**
- ⚠️ Frontmatter format для adoption reports
- ⚠️ Linking strategy (как линковать между страницами?)

### GitHub API Integration

**Usage in Spec:**
- Line 1987: find_github_solutions() - search GitHub
- Line 1997: _clone_repo() - clone repo

**Implementability:** 🔴 INSUFFICIENT
- 🔴 **BLOCKER:** GitHub API calls НЕ ОПИСАНЫ
  - Какой endpoint для search? (GET /search/repositories?)
  - Какие query parameters? (q, sort, order?)
  - Pagination? (per_page, page?)
  - Rate limiting? (5000 requests/hour?)
- 🔴 **BLOCKER:** _clone_repo() НЕ РЕАЛИЗОВАН (Opus нашёл)
  - git clone command?
  - Куда клонировать? (.claude/temp/github-repos/{name}?)
  - Как обрабатывать existing repos? (git pull?)

**Missing Details:**
- GitHub API authentication (token?)
- API rate limiting handling
- Clone location and cleanup strategy

### Git Worktree Operations

**Usage in Spec:**
- Line 1005-1024: SandboxManager.create_sandbox()
- Line 1036-1050: SandboxManager.cleanup_sandbox()

**Implementability:** 🟡 PARTIAL
- ✅ git worktree add command понятен
- ✅ git worktree remove command понятен
- 🟡 **MAJOR:** Merge strategy не описана (line 1043: "merge {branch_name}" - fast-forward? squash?)
- 🟡 **MAJOR:** Conflict resolution не описана (что если merge conflict?)
- 🔴 **BLOCKER:** Venv creation НЕ ОПИСАНА (Opus нашёл - критично!)

**Missing Details:**
- Merge strategy (fast-forward, squash, merge commit?)
- Conflict resolution workflow
- Venv creation and activation in worktree

### File Operations

**Usage in Spec:**
- Line 1092-1137: FileCopier.copy_files()
- Line 1232-1269: ImportUpdater.update_imports()

**Implementability:** 🔴 INSUFFICIENT
- 🔴 **BLOCKER:** File adaptation logic НЕ ОПИСАНА
  - Line 1116: "_adapt_content()" - ЧТО ИМЕННО адаптировать?
  - Naming conventions - КАК переименовывать? (regex? AST?)
  - Docstrings - КАК добавлять "Adopted from"? (в начало? в конец?)
  - Imports - КАК мапить? (их структура → наша структура)
- 🔴 **BLOCKER:** Import mapping НЕ ОПРЕДЕЛЁН
  - Line 1250: "_map_imports()" - КАК мапить?
  - Нужна таблица маппинга? (их module → наш module?)
  - Что если нет соответствия?

**Missing Details:**
- Конкретные adaptation rules (regex patterns, AST transformations)
- Import mapping table или алгоритм
- Error handling для unmappable imports

---

## Error Handling

### Exception Scenarios

**Covered in Spec:**
- Line 1654-1671: FullAdopter exception handling (try/except with rollback)
- Line 1489-1508: RollbackManager.rollback()

**Implementability:** 🟡 PARTIAL
- ✅ Top-level exception handling есть
- 🟡 **MAJOR:** Partial failures НЕ ПОКРЫТЫ
  - Что если FileCopier скопировал 5/10 файлов и упал?
  - Что если DependencyInstaller установил 3/5 dependencies и упал?
  - Rollback должен откатить partial changes?

**Missing Scenarios:**
1. **GitHub API failures:**
   - Rate limit exceeded
   - Repo not found
   - Authentication failed
   - Network timeout

2. **Git operation failures:**
   - Worktree creation failed (disk space?)
   - Merge conflict
   - Branch already exists
   - Detached HEAD state

3. **Dependency installation failures:**
   - Version conflict
   - Package not found in PyPI
   - Compilation error (C extensions)
   - Disk space exhausted

4. **Validation gate failures:**
   - Tests timeout (>300s)
   - Bandit crashes
   - pytest crashes
   - Out of memory

5. **File operation failures:**
   - Permission denied
   - Disk full
   - File locked
   - Encoding errors

### Retry Logic

**Mentioned in Spec:**
- Line 528: "Retry logic: +15" (QualityScorer pattern detection)

**Implementability:** 🔴 NOT DESCRIBED
- 🔴 **BLOCKER:** Retry logic для Teacher Agent НЕ ОПИСАНА
  - Какие операции retry? (GitHub API? git commands?)
  - Сколько попыток? (3? 5?)
  - Backoff strategy? (exponential? linear?)
  - Какие exceptions retry? (network errors? все?)

**Missing Details:**
- Retry configuration (max_attempts, backoff)
- Retryable vs non-retryable errors
- Retry logging and metrics

### Rollback Scenarios

**Covered in Spec:**
- Line 1471-1508: RollbackManager implementation
- Line 1636-1640: Auto-rollback on validation failure

**Implementability:** ✅ GOOD
- ✅ Git snapshot restore понятен
- ✅ Backup file restore понятен
- ✅ Worktree cleanup понятен

**Missing Details:**
- ⚠️ Partial rollback - можно ли откатить только часть? (только dependencies? только files?)
- ⚠️ Rollback validation - как проверить что rollback успешен?


---

## Testing Strategy

### Unit Tests

**Mentioned in Spec:**
- Line 2396: "Write unit tests (15+ tests)" (Phase 1)
- Line 2410: "Write unit tests (10+ tests)" (Phase 2)
- Line 2425: "Write unit tests (15+ tests)" (Phase 3)

**Implementability:** 🟡 PARTIAL
- ✅ Test count targets определены
- 🔴 **BLOCKER:** Test scenarios НЕ ОПРЕДЕЛЕНЫ
  - Какие edge cases тестировать?
  - Какие mock data использовать?
  - Какие assertions проверять?

**Missing Details:**

**Phase 1 Tests (Architecture Analysis):**
- FileStructureAnalyzer:
  - Test empty repo
  - Test repo with only __init__.py
  - Test repo with mixed file types
  - Test deeply nested structure
- ComponentRelationAnalyzer:
  - Test circular dependencies detection
  - Test external imports handling
  - Test relative imports
  - Test coupling score calculation
- DesignPatternDetector:
  - Test each pattern detection (Strategy, Factory, Observer, etc.)
  - Test false positives
  - Test confidence scoring
- TestCoverageAnalyzer:
  - Test fixture detection
  - Test mock detection
  - Test coverage estimate calculation

**Phase 2 Tests (Solution Comparison):**
- ArchitectureScorer:
  - Test modularity scoring
  - Test testability scoring
  - Test edge cases (score = 0, score = 100)
- QualityScorer:
  - Test pattern detection scoring
  - Test error handling scoring
- FitAnalyzer:
  - Test semantic similarity calculation
  - Test integration effort scoring
- RiskAnalyzer:
  - Test security scoring
  - Test compliance scoring
- DecisionMaker:
  - Test each decision rule (Full, Partial, Custom, Reject)
  - Test third-party agent exception
  - Test metrics degradation exception

**Phase 3 Tests (Full Adoption):**
- SandboxManager:
  - Test worktree creation
  - Test venv creation
  - Test cleanup with/without keeping changes
- FileCopier:
  - Test file adaptation
  - Test backup creation
  - Test error handling (permission denied, disk full)
- DependencyInstaller:
  - Test version conflict detection
  - Test requirements.txt update
- ImportUpdater:
  - Test import mapping
  - Test circular dependency detection
- TestMigrator:
  - Test fixture adaptation
  - Test import updates in tests
- ValidationGateRunner:
  - Test each gate independently
  - Test sequential execution with early exit
  - Test all gates pass scenario
  - Test any gate fails scenario
- RollbackManager:
  - Test snapshot restore
  - Test backup restore
  - Test 30-day window check

### Integration Tests

**Mentioned in Spec:**
- Line 2436: "Write integration tests (5+ tests)" (Phase 4)
- Line 1400-1406: Gate 5 (Integration Test)

**Implementability:** 🟡 PARTIAL
- ✅ Gate 5 описан (Event Bus, Obsidian, Magisters)
- 🔴 **BLOCKER:** Integration test scenarios НЕ ОПРЕДЕЛЕНЫ

**Missing Details:**

**Integration Test Scenarios:**
1. **End-to-End Adoption Flow:**
   - Search GitHub → Compare → Adopt → Validate → Merge
   - Expected: Successful adoption with all gates passing
   
2. **End-to-End Rejection Flow:**
   - Search GitHub → Compare → Reject (low quality)
   - Expected: Rejection notification sent
   
3. **End-to-End Rollback Flow:**
   - Adopt → Validation fails → Auto-rollback
   - Expected: Original state restored
   
4. **Event Bus Integration:**
   - Teacher sends notification → Operator receives
   - Expected: Event delivered with correct payload
   
5. **Obsidian Integration:**
   - Generate report → Save to vault → Read back
   - Expected: Report saved with correct frontmatter

### Mock Data

**Mentioned in Spec:**
- Line 2411: "Write unit tests" (но mock data не описана)

**Implementability:** 🔴 INSUFFICIENT
- 🔴 **BLOCKER:** Mock data НЕ ОПРЕДЕЛЕНА
  - Mock GitHub repos для тестирования
  - Mock ArchitectureAnalysis results
  - Mock ComparisonResult
  - Mock ValidationResult

**Missing Details:**

**Required Mock Data:**

1. **Mock GitHub Repos:**
   ```python
   # tests/fixtures/mock_repos/
   ├── high_quality_repo/      # Quality 85, Fit 85, Risk 15 → Full
   ├── medium_quality_repo/    # Quality 72, Fit 72, Risk 25 → Partial
   ├── low_quality_repo/       # Quality 55, Fit 55, Risk 45 → Reject
   └── third_party_agent/      # Complete agent (not library)
   ```

2. **Mock Analysis Results:**
   ```python
   @pytest.fixture
   def mock_high_quality_analysis():
       return ArchitectureAnalysis(
           file_structure=FileStructure(...),
           component_relations=ComponentRelations(coupling_score=85, ...),
           design_patterns=DesignPatterns(patterns=["Strategy", "Factory"], ...),
           test_coverage=TestCoverage(coverage_estimate=80, ...),
           quality_score=85
       )
   ```

3. **Mock Validation Results:**
   ```python
   @pytest.fixture
   def mock_all_gates_pass():
       return ValidationResult(
           gate_results={
               "Sandbox Tests": GateResult(passed=True, ...),
               "Metrics Check": GateResult(passed=True, ...),
               "Security Scan": GateResult(passed=True, ...),
               "Compliance Check": GateResult(passed=True, ...),
               "Integration Test": GateResult(passed=True, ...)
           },
           all_passed=True,
           failed_gates=[]
       )
   ```

### Test Fixtures

**Mentioned in Spec:**
- Line 463: "Has fixtures: +15" (scoring criteria)
- Line 1321: TestMigrator adapts fixtures

**Implementability:** 🟡 PARTIAL
- ✅ Fixture detection упомянут
- 🔴 **BLOCKER:** Test fixtures для Teacher Agent НЕ ОПРЕДЕЛЕНЫ

**Missing Details:**

**Required Fixtures:**

```python
# tests/conftest.py

@pytest.fixture
def temp_repo_path(tmp_path):
    """Temporary directory for cloning repos."""
    return tmp_path / "repos"

@pytest.fixture
def sandbox_env(tmp_path):
    """Mock sandbox environment."""
    return SandboxEnvironment(
        worktree_path=tmp_path / "worktree",
        branch_name="teacher/test-adoption",
        venv_path=tmp_path / "worktree/.venv",
        snapshot_id="abc123",
        created_at=datetime.now()
    )

@pytest.fixture
def mock_event_bus():
    """Mock Event Bus for testing."""
    return Mock(spec=EventBus)

@pytest.fixture
def mock_obsidian():
    """Mock Obsidian vault for testing."""
    return Mock(spec=ObsidianVault)

@pytest.fixture
def teacher_agent(mock_event_bus, mock_obsidian):
    """Teacher Agent instance for testing."""
    return TeacherAgent(
        event_bus=mock_event_bus,
        obsidian=mock_obsidian
    )
```

---

## Dependencies

### Existing Dependencies

**From requirements.txt (already available):**
- ✅ `httpx` - HTTP client (для GitHub API)
- ✅ `pydantic` - Data validation
- ✅ `pytest` - Testing framework
- ✅ `networkx` - Graph analysis (dependency graph)

### Missing Dependencies

**Identified by Opus (lines 163-166):**
- ❌ `radon>=6.0.0,<7.0.0` - Cyclomatic complexity
- ❌ `safety>=3.0.0,<4.0.0` - Dependency vulnerability scan
- ❌ `pytest-benchmark>=4.0.0` - Performance benchmarking

**Additional Missing (found during implementation review):**
- ❌ `libcst>=1.0.0` - AST analysis and transformation (better than stdlib ast)
- ❌ `bandit>=1.7.0` - Security scanning (mentioned in spec but not in requirements)
- ❌ `GitPython>=3.1.0` - Git operations (easier than subprocess)

### Dependency Compatibility

**Implementability:** ✅ GOOD
- ✅ Все dependencies доступны в PyPI
- ✅ Нет известных version conflicts
- ✅ Все dependencies Python 3.11+ compatible

**Version Pinning Strategy:**
- ✅ Spec использует semantic versioning (>=X.0.0,<Y.0.0)
- ✅ Consistent с existing requirements.txt

### Installation Order

**Implementability:** ✅ GOOD
- ✅ Нет специального installation order
- ✅ Все dependencies независимые

**Recommended additions to requirements.txt:**
```
# Teacher Agent dependencies
radon>=6.0.0,<7.0.0              # Cyclomatic complexity analysis
safety>=3.0.0,<4.0.0             # Dependency vulnerability scanning
pytest-benchmark>=4.0.0,<5.0.0   # Performance benchmarking
libcst>=1.0.0,<2.0.0             # AST analysis and transformation
bandit>=1.7.0,<2.0.0             # Security scanning
GitPython>=3.1.0,<4.0.0          # Git operations
```

---

## Implementation Gaps Found

### 🔴 BLOCKERS (cannot implement without)

#### 1. Pattern Detection Algorithms Missing
- **Location:** Section 2.1.3 (DesignPatternDetector, lines 294-318)
- **Impact:** Cannot implement DesignPatternDetector без конкретных heuristics
- **Need:** Добавить в spec:
  ```python
  # Strategy Pattern Detection
  def detect_strategy_pattern(self, repo_path: Path) -> bool:
      # 1. Find classes with same base class
      # 2. Check if methods have same signature
      # 3. Check if used interchangeably
      # Confidence: high if 3/3, medium if 2/3, low if 1/3
  
  # Factory Pattern Detection
  def detect_factory_pattern(self, repo_path: Path) -> bool:
      # 1. Find methods returning different types
      # 2. Check method name contains "create", "build", "make"
      # 3. Check if returns subclasses of common base
      # Confidence: high if 3/3, medium if 2/3, low if 1/3
  
  # Observer Pattern Detection
  def detect_observer_pattern(self, repo_path: Path) -> bool:
      # 1. Find callback/event registration methods
      # 2. Check for notify/trigger methods
      # 3. Check for subscriber list
      # Confidence: high if 3/3, medium if 2/3, low if 1/3
  ```

#### 2. Metrics Calculation Formulas Missing
- **Location:** Multiple locations (ComponentRelations, TestCoverage, ArchitectureScore)
- **Impact:** Cannot calculate scores без формул
- **Need:** Добавить в spec:
  ```python
  # Coupling Score (0-100)
  coupling_score = 100 - (edges / nodes * 100)
  # Normalize: if > 100, cap at 100; if < 0, floor at 0
  
  # Coverage Estimate (0-100)
  coverage_estimate = min(100, (test_count / function_count) * 100)
  
  # Test Quality Score (0-100)
  test_quality_score = (
      (assertions_per_test / 5) * 50 +  # Max 5 assertions = 50 points
      (has_fixtures ? 25 : 0) +
      (has_mocks ? 25 : 0)
  )
  ```

#### 3. File Adaptation Logic Missing
- **Location:** Section 4.2 (FileCopier, lines 1092-1137)
- **Impact:** Cannot adapt files без конкретных rules
- **Need:** Добавить в spec:
  ```python
  def _adapt_content(self, content: str, repo_url: str) -> str:
      # 1. Add "Adopted from" to docstrings
      content = self._add_adoption_notice(content, repo_url)
      
      # 2. Update naming conventions
      content = self._fix_naming_conventions(content)
      
      # 3. Update imports (preliminary, detailed in ImportUpdater)
      content = self._update_import_paths(content)
      
      return content
  
  def _add_adoption_notice(self, content: str, repo_url: str) -> str:
      # Parse with libcst
      # Find first docstring
      # Prepend "Adopted from {repo_url}\n\n"
      # Return modified content
  
  def _fix_naming_conventions(self, content: str) -> str:
      # Parse with libcst
      # Rename functions to snake_case
      # Rename classes to PascalCase
      # Rename constants to UPPER_CASE
      # Return modified content
  ```

#### 4. Import Mapping Algorithm Missing
- **Location:** Section 4.4 (ImportUpdater, lines 1232-1269)
- **Impact:** Cannot update imports без mapping algorithm
- **Need:** Добавить в spec:
  ```python
  def _map_imports(
      self,
      tree: ast.Module,
      github_structure: FileStructure,
      our_structure: FileStructure
  ) -> dict[str, str]:
      """Map GitHub imports to our imports."""
      mapping = {}
      
      # Strategy 1: Direct file name match
      for github_file in github_structure.clients:
          our_file = self._find_matching_file(github_file, our_structure.clients)
          if our_file:
              mapping[github_file] = our_file
      
      # Strategy 2: Semantic similarity (if no direct match)
      for github_file in github_structure.clients:
          if github_file not in mapping:
              our_file = self._find_similar_file(github_file, our_structure.clients)
              if our_file:
                  mapping[github_file] = our_file
      
      # Strategy 3: Ask user (if still no match)
      # ... (через AskUserQuestion?)
      
      return mapping
  ```

#### 5. GitHub API Integration Missing
- **Location:** Section 6.1 (TeacherAgent, lines 1984-1992)
- **Impact:** Cannot search/clone repos без API details
- **Need:** Добавить в spec:
  ```python
  async def find_github_solutions(
      self,
      subagent_name: str,
      query: str
  ) -> list[str]:
      """Search GitHub for relevant solutions."""
      # 1. Build search query
      search_query = f"{query} language:python stars:>100"
      
      # 2. Call GitHub API
      response = await self.http_client.get(
          "https://api.github.com/search/repositories",
          params={
              "q": search_query,
              "sort": "stars",
              "order": "desc",
              "per_page": 10
          },
          headers={"Authorization": f"token {self.github_token}"}
      )
      
      # 3. Extract repo URLs
      repos = response.json()["items"]
      repo_urls = [repo["html_url"] for repo in repos[:5]]
      
      # 4. Filter by quality (stars, activity, age)
      filtered_urls = self._filter_repos(repos)
      
      return filtered_urls
  
  async def _clone_repo(self, repo_url: str) -> Path:
      """Clone GitHub repo to temp directory."""
      repo_name = repo_url.split("/")[-1].replace(".git", "")
      clone_path = Path(f".claude/temp/github-repos/{repo_name}")
      
      if clone_path.exists():
          # Update existing repo
          repo = git.Repo(clone_path)
          repo.remotes.origin.pull()
      else:
          # Clone new repo
          git.Repo.clone_from(repo_url, clone_path)
      
      return clone_path
  ```

#### 6. Sandbox Venv Isolation Missing
- **Location:** Section 4.1 (SandboxManager, lines 1005-1051)
- **Impact:** Risk breaking main environment без venv isolation
- **Need:** Добавить в spec (Opus уже нашёл):
  ```python
  async def create_sandbox(
      self,
      subagent_name: str,
      adoption_id: str
  ) -> SandboxEnvironment:
      # Create worktree
      worktree_path = Path(f".claude/worktrees/teacher-{adoption_id}")
      branch_name = f"teacher/{subagent_name}-{adoption_id}"
      
      await self._run_git_command(f"worktree add {worktree_path} -b {branch_name}")
      
      # Create isolated venv
      venv_path = worktree_path / ".venv"
      await self._create_venv(venv_path)
      
      # Activate venv for subsequent operations
      self.venv_python = venv_path / "bin" / "python"
      
      # Create snapshot
      snapshot_id = await self._get_current_commit_hash()
      
      return SandboxEnvironment(
          worktree_path=worktree_path,
          branch_name=branch_name,
          venv_path=venv_path,  # ADD THIS
          snapshot_id=snapshot_id,
          created_at=datetime.now()
      )
  
  async def _create_venv(self, venv_path: Path) -> None:
      """Create isolated virtual environment."""
      await asyncio.create_subprocess_exec(
          "python", "-m", "venv", str(venv_path)
      )
  ```

#### 7. Compliance Check Rules Missing
- **Location:** Section 4.6, Gate 4 (lines 1398-1400)
- **Impact:** Cannot validate HIPAA compliance без конкретных rules
- **Need:** Добавить в spec (Opus уже нашёл):
  ```python
  class ComplianceChecker:
      async def check_hipaa_compliance(self, repo_path: Path) -> ComplianceResult:
          checks = {
              "phi_detection": await self._check_phi_logging(repo_path),
              "encryption_at_rest": await self._check_encryption_at_rest(repo_path),
              "encryption_in_transit": await self._check_tls_usage(repo_path),
              "audit_logging": await self._check_audit_trail(repo_path),
              "access_controls": await self._check_rbac(repo_path),
              "data_retention": await self._check_retention_policy(repo_path)
          }
          
          all_passed = all(checks.values())
          return ComplianceResult(
              passed=all_passed,
              checks=checks,
              details=self._generate_report(checks)
          )
      
      async def _check_phi_logging(self, repo_path: Path) -> bool:
          """Check for PHI in logs."""
          # Search for logging.info/debug/error with PHI patterns
          # PHI patterns: SSN, email, phone, address, medical record number
          # Return False if found
      
      async def _check_encryption_at_rest(self, repo_path: Path) -> bool:
          """Check for encryption at rest."""
          # Search for database connections
          # Check if encryption enabled (SQLCipher, encrypted columns)
          # Return True if encrypted or no database
      
      async def _check_tls_usage(self, repo_path: Path) -> bool:
          """Check for TLS in HTTP requests."""
          # Search for httpx/requests calls
          # Check if verify=True (default)
          # Check if https:// URLs
          # Return False if http:// or verify=False
  ```

#### 8. Risk Score Calculation Logic Wrong
- **Location:** Section 3.5 (DecisionMaker, lines 762-800)
- **Impact:** Wrong decisions about adoption
- **Need:** Fix (Opus уже нашёл):
  ```python
  # CURRENT (WRONG):
  risk_composite = 100 - risk_score.overall  # Invert
  if quality >= 80 and fit >= 80 and risk_composite <= 20:
      decision = "Full"
  
  # FIXED (Option 1 - no inversion):
  # Define: risk_score.overall = 0-100 (100 = no risk, 0 = high risk)
  if quality >= 80 and fit >= 80 and risk_score.overall >= 80:
      decision = "Full"  # risk ≥ 80 = low risk
  
  # FIXED (Option 2 - proper inversion):
  # Define: risk_score.overall = 0-100 (0 = no risk, 100 = high risk)
  if quality >= 80 and fit >= 80 and risk_score.overall <= 20:
      decision = "Full"  # risk ≤ 20 = low risk
  ```


### 🟡 MAJOR (need clarification)

#### 9. Semantic Similarity Algorithm Missing
- **Location:** Section 3.3 (FitAnalyzer, lines 600-606)
- **Impact:** Cannot calculate task_match score без алгоритма
- **Need:** Добавить в spec:
  ```python
  async def _score_task_match(
      self,
      subagent_spec_path: Path,
      github_analysis: ArchitectureAnalysis
  ) -> float:
      # Read spec
      spec_content = await self._read_file(subagent_spec_path)
      spec_purpose = self._extract_purpose(spec_content)  # Section 1: Overview
      
      # Extract GitHub purpose
      github_readme = await self._read_file(github_analysis.repo_path / "README.md")
      github_purpose = self._extract_purpose(github_readme)
      
      # Calculate semantic similarity
      # Option 1: Keyword matching (simple)
      keywords_spec = set(spec_purpose.lower().split())
      keywords_github = set(github_purpose.lower().split())
      overlap = len(keywords_spec & keywords_github)
      similarity = (overlap / len(keywords_spec | keywords_github)) * 100
      
      # Option 2: Embeddings (advanced, requires sentence-transformers)
      # from sentence_transformers import SentenceTransformer
      # model = SentenceTransformer('all-MiniLM-L6-v2')
      # emb_spec = model.encode(spec_purpose)
      # emb_github = model.encode(github_purpose)
      # similarity = cosine_similarity(emb_spec, emb_github) * 100
      
      return similarity
  ```

#### 10. Performance Metrics Not Defined
- **Location:** Section 4.6, Gate 2 (lines 1381-1386)
- **Impact:** Cannot check performance degradation
- **Need:** Добавить в spec (Opus уже нашёл):
  ```python
  class MetricsChecker:
      async def check_performance(
          self,
          sandbox: SandboxEnvironment,
          subagent_name: str
      ) -> PerformanceMetrics:
          # Run pytest-benchmark in sandbox
          benchmark_results = await self._run_benchmarks(sandbox, subagent_name)
          
          # Load baseline metrics
          baseline = await self._load_baseline_metrics(subagent_name)
          
          # Calculate degradation
          degradation = {}
          for metric in ["response_time_ms", "throughput_rps", "memory_mb"]:
              current = benchmark_results[metric]
              baseline_val = baseline[metric]
              degradation[metric] = ((current - baseline_val) / baseline_val) * 100
          
          max_degradation = max(degradation.values())
          
          return PerformanceMetrics(
              response_time_ms=benchmark_results["response_time_ms"],
              throughput_rps=benchmark_results["throughput_rps"],
              memory_mb=benchmark_results["memory_mb"],
              degradation_percent=max_degradation
          )
      
      async def _run_benchmarks(
          self,
          sandbox: SandboxEnvironment,
          subagent_name: str
      ) -> dict:
          # Run pytest-benchmark
          result = await asyncio.create_subprocess_exec(
              str(sandbox.venv_path / "bin" / "pytest"),
              f"AIM/tests/subagents/{subagent_name}/",
              "--benchmark-only",
              "--benchmark-json=benchmark.json",
              cwd=sandbox.worktree_path
          )
          
          # Parse results
          with open(sandbox.worktree_path / "benchmark.json") as f:
              data = json.load(f)
          
          return {
              "response_time_ms": data["benchmarks"][0]["stats"]["mean"] * 1000,
              "throughput_rps": 1 / data["benchmarks"][0]["stats"]["mean"],
              "memory_mb": data["benchmarks"][0]["stats"]["max_memory_mb"]
          }
  ```

#### 11. Dependency Vulnerability Scan Missing
- **Location:** Section 4.6, Gate 3 (lines 1387-1392)
- **Impact:** Can adopt vulnerable dependencies
- **Need:** Добавить в spec (Opus уже нашёл):
  ```python
  class SecurityScanner:
      async def scan_dependencies(self, repo_path: Path) -> DependencySecurityResult:
          # Run safety check
          result = await asyncio.create_subprocess_exec(
              "safety", "check",
              "--json",
              "--file", str(repo_path / "requirements.txt"),
              stdout=asyncio.subprocess.PIPE
          )
          
          stdout, _ = await result.communicate()
          vulnerabilities = json.loads(stdout)
          
          # Filter by severity
          high_severity = [v for v in vulnerabilities if v["severity"] == "high"]
          medium_severity = [v for v in vulnerabilities if v["severity"] == "medium"]
          
          passed = len(high_severity) == 0 and len(medium_severity) == 0
          
          return DependencySecurityResult(
              passed=passed,
              vulnerabilities=vulnerabilities,
              high_count=len(high_severity),
              medium_count=len(medium_severity),
              details=self._format_vulnerabilities(vulnerabilities)
          )
  ```

#### 12. Retry Logic Not Described
- **Location:** Throughout spec (GitHub API, git commands, etc.)
- **Impact:** Failures on transient errors
- **Need:** Добавить в spec:
  ```python
  from tenacity import retry, stop_after_attempt, wait_exponential
  
  class TeacherAgent:
      @retry(
          stop=stop_after_attempt(3),
          wait=wait_exponential(multiplier=1, min=1, max=10),
          retry=retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException))
      )
      async def find_github_solutions(self, subagent_name: str, query: str) -> list[str]:
          # GitHub API call with retry
          ...
      
      @retry(
          stop=stop_after_attempt(3),
          wait=wait_exponential(multiplier=1, min=1, max=10),
          retry=retry_if_exception_type(git.GitCommandError)
      )
      async def _clone_repo(self, repo_url: str) -> Path:
          # Git clone with retry
          ...
  ```

#### 13. Merge Strategy Not Defined
- **Location:** Section 4.1 (SandboxManager.cleanup_sandbox, line 1043)
- **Impact:** Unclear how to merge (fast-forward? squash? merge commit?)
- **Need:** Добавить в spec:
  ```python
  async def cleanup_sandbox(
      self,
      sandbox: SandboxEnvironment,
      keep_changes: bool = False
  ) -> None:
      if keep_changes:
          # Merge to main with squash (clean history)
          await self._run_git_command("checkout main")
          await self._run_git_command(
              f"merge --squash {sandbox.branch_name}",
              f"-m 'Teacher Agent: Adopt improvements from {sandbox.branch_name}'"
          )
          
          # Handle merge conflicts
          if await self._has_merge_conflicts():
              # Auto-resolve conflicts (prefer incoming changes)
              await self._run_git_command("checkout --theirs .")
              await self._run_git_command("add .")
          
          await self._run_git_command("commit")
      
      # Remove worktree
      await self._run_git_command(f"worktree remove {sandbox.worktree_path}")
      
      # Delete branch
      await self._run_git_command(f"branch -D {sandbox.branch_name}")
  ```

#### 14. File Classification Patterns Missing
- **Location:** Section 2.1.1 (FileStructureAnalyzer, line 218)
- **Impact:** Cannot classify files без patterns
- **Need:** Добавить в spec:
  ```python
  FILE_PATTERNS = {
      "entry_points": [r"main\.py$", r"__main__\.py$", r"app\.py$", r"__init__\.py$"],
      "clients": [r".*client\.py$", r".*api\.py$", r".*service\.py$"],
      "models": [r".*model\.py$", r".*schema\.py$", r".*entity\.py$", r".*dto\.py$"],
      "tests": [r"test_.*\.py$", r".*_test\.py$"],
      "configs": [r"settings\.py$", r"config\.py$", r"\.env$", r".*\.yaml$", r".*\.toml$"],
      "utils": [r"utils/.*\.py$", r"helpers/.*\.py$", r"common/.*\.py$"],
      "docs": [r"README\.md$", r"docs/.*\.md$", r".*\.md$"]
  }
  ```

#### 15. Test Classification Patterns Missing
- **Location:** Section 2.1.4 (TestCoverageAnalyzer, line 343)
- **Impact:** Cannot classify tests без patterns
- **Need:** Добавить в spec:
  ```python
  TEST_PATTERNS = {
      "unit": [
          r"test_.*_unit\.py$",
          r".*mock.*",  # Uses mocks = likely unit test
          r".*fixture.*"  # Uses fixtures = likely unit test
      ],
      "integration": [
          r"test_.*_integration\.py$",
          r".*database.*",  # Database tests = integration
          r".*api.*"  # API tests = integration
      ],
      "e2e": [
          r"test_.*_e2e\.py$",
          r"test_.*_end_to_end\.py$",
          r".*selenium.*",  # Browser tests = e2e
          r".*playwright.*"  # Browser tests = e2e
      ]
  }
  ```

#### 16. SOLID Compliance Rules Missing
- **Location:** Section 2.1.3 (DesignPatternDetector, line 305)
- **Impact:** Cannot check SOLID без rules
- **Need:** Добавить в spec:
  ```python
  def check_solid_compliance(self, repo_path: Path) -> dict[str, bool]:
      return {
          "S": self._check_srp(repo_path),  # Single Responsibility
          "O": self._check_ocp(repo_path),  # Open/Closed
          "L": self._check_lsp(repo_path),  # Liskov Substitution
          "I": self._check_isp(repo_path),  # Interface Segregation
          "D": self._check_dip(repo_path)   # Dependency Inversion
      }
  
  def _check_srp(self, repo_path: Path) -> bool:
      """Single Responsibility: Each class has one reason to change."""
      # Heuristic: Class with <10 methods, <200 lines
      # Check all classes, return True if 80%+ comply
      ...
  
  def _check_ocp(self, repo_path: Path) -> bool:
      """Open/Closed: Open for extension, closed for modification."""
      # Heuristic: Uses inheritance/composition, not if/else chains
      # Check for abstract base classes, interfaces
      ...
  
  def _check_lsp(self, repo_path: Path) -> bool:
      """Liskov Substitution: Subclasses can replace base classes."""
      # Heuristic: Subclasses don't override methods with incompatible signatures
      # Check method signatures in inheritance hierarchy
      ...
  
  def _check_isp(self, repo_path: Path) -> bool:
      """Interface Segregation: Many specific interfaces > one general."""
      # Heuristic: Interfaces have <5 methods
      # Check abstract base classes
      ...
  
  def _check_dip(self, repo_path: Path) -> bool:
      """Dependency Inversion: Depend on abstractions, not concretions."""
      # Heuristic: Constructor injection, depends on abstract base classes
      # Check __init__ parameters
      ...
  ```

#### 17. Core vs Peripheral Threshold Missing
- **Location:** Section 2.1.2 (ComponentRelationAnalyzer, line 260)
- **Impact:** Cannot determine core components без threshold
- **Need:** Добавить в spec:
  ```python
  def _identify_core_components(self, dependency_graph: nx.DiGraph) -> list[str]:
      """Identify core components by in-degree."""
      # Calculate in-degree for each node
      in_degrees = dict(dependency_graph.in_degree())
      
      # Threshold: top 20% by in-degree = core
      threshold = sorted(in_degrees.values(), reverse=True)[int(len(in_degrees) * 0.2)]
      
      core = [node for node, degree in in_degrees.items() if degree >= threshold]
      return core
  
  def _identify_peripheral_components(self, dependency_graph: nx.DiGraph) -> list[str]:
      """Identify peripheral components by in-degree."""
      # Threshold: bottom 20% by in-degree = peripheral
      in_degrees = dict(dependency_graph.in_degree())
      threshold = sorted(in_degrees.values())[int(len(in_degrees) * 0.2)]
      
      peripheral = [node for node, degree in in_degrees.items() if degree <= threshold]
      return peripheral
  ```

#### 18. Documentation Quality Scoring Missing
- **Location:** Section 3.1 (ArchitectureScorer, line 467)
- **Impact:** Cannot score maintainability без documentation scoring
- **Need:** Добавить в spec:
  ```python
  def _score_documentation(self, repo_path: Path) -> float:
      """Score documentation quality (0-30 points)."""
      score = 0
      
      # README quality (0-10 points)
      readme_path = repo_path / "README.md"
      if readme_path.exists():
          readme_content = readme_path.read_text()
          if len(readme_content) > 500:  # Substantial README
              score += 5
          if "## Installation" in readme_content:  # Has installation section
              score += 2
          if "## Usage" in readme_content:  # Has usage section
              score += 3
      
      # Docstring coverage (0-15 points)
      docstring_coverage = self._calculate_docstring_coverage(repo_path)
      score += docstring_coverage * 0.15  # 100% coverage = 15 points
      
      # Inline comments (0-5 points)
      comment_ratio = self._calculate_comment_ratio(repo_path)
      score += min(5, comment_ratio * 50)  # 10% comments = 5 points
      
      return score
  ```

#### 19. Code Style Checking Missing
- **Location:** Section 3.1 (ArchitectureScorer, line 469)
- **Impact:** Cannot score maintainability без style checking
- **Need:** Добавить в spec:
  ```python
  async def _check_code_style(self, repo_path: Path) -> bool:
      """Check if code follows consistent style."""
      # Run ruff check
      result = await asyncio.create_subprocess_exec(
          "ruff", "check", str(repo_path),
          stdout=asyncio.subprocess.PIPE,
          stderr=asyncio.subprocess.PIPE
      )
      
      stdout, stderr = await result.communicate()
      
      # Parse output
      violations = len(stdout.decode().split("\n"))
      
      # Threshold: <10 violations per 1000 lines = consistent
      total_lines = self._count_total_lines(repo_path)
      violations_per_1k = (violations / total_lines) * 1000
      
      return violations_per_1k < 10
  ```

#### 20. Clear Naming Evaluation Missing
- **Location:** Section 3.1 (ArchitectureScorer, line 470)
- **Impact:** Cannot score maintainability без naming evaluation
- **Need:** Добавить в spec:
  ```python
  def _evaluate_naming_clarity(self, repo_path: Path) -> float:
      """Evaluate naming clarity (0-20 points)."""
      score = 0
      
      # Check average identifier length (not too short, not too long)
      avg_length = self._calculate_avg_identifier_length(repo_path)
      if 5 <= avg_length <= 20:  # Sweet spot
          score += 10
      
      # Check for abbreviations (fewer = better)
      abbrev_ratio = self._calculate_abbreviation_ratio(repo_path)
      score += (1 - abbrev_ratio) * 10  # 0% abbreviations = 10 points
      
      return score
  ```

### 🟢 MINOR (nice to have)

#### 21. Dataclasses Should Use Pydantic
- **Location:** All dataclasses throughout spec
- **Impact:** No runtime validation
- **Recommendation:** Migrate to Pydantic BaseModel
- **Priority:** LOW - можно добавить позже

#### 22. TestCoverageAnalyzer Should Use pytest-cov
- **Location:** Section 2.1.4 (lines 341-361)
- **Impact:** Coverage estimate неточный
- **Recommendation:** Use pytest-cov для реального coverage
- **Priority:** LOW - estimate достаточен для v2.0

---

## Comparison with Opus Review

### Agreement Areas

**Both reviews found same BLOCKERS:**
1. ✅ Risk score calculation logic wrong (Opus line 86-116, Sonnet #8)
2. ✅ Compliance checks insufficient (Opus line 224-300, Sonnet #7)
3. ✅ Sandbox venv isolation missing (Opus line 168-330, Sonnet #6)

**Both reviews found same MAJOR issues:**
4. ✅ Performance metrics not defined (Opus line 176-180, Sonnet #10)
5. ✅ Dependency vulnerability scan missing (Opus line 247-379, Sonnet #11)
6. ✅ GitHub download mechanism not described (Opus line 382-400, Sonnet #5)
7. ✅ Missing dependencies in requirements (Opus line 404-411, Sonnet - Dependencies section)
8. ✅ CLI commands not async (Opus line 413-429, Sonnet - noted but not blocker)

### Sonnet Found Additional Issues

**Implementation-specific blockers (Opus missed):**
1. 🆕 Pattern detection algorithms missing (#1) - BIGGEST GAP
2. 🆕 Metrics calculation formulas missing (#2)
3. 🆕 File adaptation logic missing (#3)
4. 🆕 Import mapping algorithm missing (#4)
5. 🆕 Semantic similarity algorithm missing (#9)
6. 🆕 Retry logic not described (#12)
7. 🆕 Merge strategy not defined (#13)
8. 🆕 File classification patterns missing (#14)
9. 🆕 Test classification patterns missing (#15)
10. 🆕 SOLID compliance rules missing (#16)
11. 🆕 Core vs peripheral threshold missing (#17)
12. 🆕 Documentation quality scoring missing (#18)
13. 🆕 Code style checking missing (#19)
14. 🆕 Clear naming evaluation missing (#20)

**Why Opus missed these:**
- Opus focused on architecture and high-level feasibility
- Sonnet focused on line-by-line implementation details
- Opus assumed "algorithms can be implemented" without checking HOW
- Sonnet checked "can I write code from this spec?" and found gaps

### Complementary Reviews

**Opus strengths:**
- Strategic architecture review
- Business logic validation
- Risk assessment
- Timeline feasibility

**Sonnet strengths:**
- Implementation details
- Algorithm specifications
- Code-level feasibility
- Testing strategy

**Together:** Complete picture of spec quality

---

## Recommendation

**NEEDS CLARIFICATION BEFORE IMPLEMENTATION**

Спецификация Teacher Agent v2.0 хорошо продумана на архитектурном уровне, но имеет существенные пробелы в деталях реализации. Многие алгоритмы описаны на высоком уровне ("analyze", "detect", "score") без конкретных шагов, формул, или heuristics.

**Critical Issues:**
- 8 BLOCKERS (cannot implement without)
- 12 MAJOR clarifications needed
- 2 MINOR improvements (optional)

**After fixing blockers and major issues:** Спецификация будет готова к реализации с высокой уверенностью в успехе.

**Estimated Fix Time:** 4-6 hours (добавить недостающие алгоритмы и формулы)

---

## Implementation Estimate

**After fixes:**

### Phase 1: Architecture Analysis (4-5 hours)
- FileStructureAnalyzer: 1h (+ patterns)
- ComponentRelationAnalyzer: 1h (+ coupling formula)
- DesignPatternDetector: 2h (+ detection heuristics) ⚠️ COMPLEX
- TestCoverageAnalyzer: 1h (+ formulas)
- Unit tests: 1h

**Complexity:** HIGH (pattern detection)

### Phase 2: Solution Comparison (3-4 hours)
- ArchitectureScorer: 1h (+ scoring formulas)
- QualityScorer: 1h (+ pattern detection)
- FitAnalyzer: 1h (+ semantic similarity)
- RiskAnalyzer: 0.5h
- DecisionMaker: 0.5h (+ fix risk logic)
- Unit tests: 1h

**Complexity:** MEDIUM

### Phase 3: Full Adoption (5-6 hours)
- SandboxManager: 1h (+ venv creation)
- FileCopier: 1.5h (+ adaptation logic)
- DependencyInstaller: 0.5h
- ImportUpdater: 1.5h (+ mapping algorithm)
- TestMigrator: 0.5h
- ValidationGateRunner: 1h (+ compliance rules)
- RollbackManager: 0.5h
- Unit tests: 1.5h

**Complexity:** HIGH (file adaptation, import mapping)

### Phase 4: Reporting & Integration (2-3 hours)
- AdoptionReportGenerator: 0.5h
- AuditTrailLogger: 0.5h
- NotificationSender: 0.5h
- TeacherAgent: 1h (+ GitHub API, retry logic)
- CLI: 0.5h (+ async fix)
- Integration tests: 1h

**Complexity:** MEDIUM

**Total Time:** 14-18 hours (vs spec estimate 8-12 hours)

**Why longer:**
- Missing algorithms need to be designed AND implemented
- Pattern detection is complex (2h → 3-4h realistically)
- File adaptation and import mapping are complex (1h each → 2-3h each)
- Testing will take longer with more edge cases

---

## Next Steps

### Immediate (Before Implementation)

**Priority 1: Fix Opus Blockers (2-3 hours)**
1. Fix risk score calculation logic (30 min)
2. Add HIPAA compliance rules (1 hour)
3. Add sandbox venv isolation (30 min)
4. Add performance metrics (30 min)
5. Add dependency vulnerability scan (30 min)

**Priority 2: Add Implementation Details (2-3 hours)**
6. Add pattern detection algorithms (1 hour) ⚠️ CRITICAL
7. Add metrics calculation formulas (30 min)
8. Add file adaptation logic (30 min)
9. Add import mapping algorithm (30 min)
10. Add GitHub API integration (30 min)

**Priority 3: Add Missing Patterns (1 hour)**
11. Add file classification patterns (15 min)
12. Add test classification patterns (15 min)
13. Add SOLID compliance rules (30 min)

### After Fixes (Implementation Phase)

**Phase 1:** Implement Architecture Analysis Layer (4-5 hours)
**Phase 2:** Implement Solution Comparison Layer (3-4 hours)
**Phase 3:** Implement Full Adoption Layer (5-6 hours)
**Phase 4:** Implement Reporting & Integration (2-3 hours)

### Optional (Post-v2.0)

- Migrate dataclasses to Pydantic
- Improve TestCoverageAnalyzer with pytest-cov
- Add semantic similarity with embeddings (sentence-transformers)

---

## Conclusion

Спецификация Teacher Agent v2.0 хорошо продумана на архитектурном уровне и покрывает все основные компоненты автономной системы обучения. Однако, с точки зрения implementation, спецификация имеет существенные пробелы в деталях.

**Strengths:**
- ✅ Архитектура sound и хорошо структурирована
- ✅ Decision framework чёткий с точными thresholds
- ✅ Validation gates адекватны для medical marketing
- ✅ Dataclasses хорошо определены (структура)
- ✅ Integration points определены (Event Bus, Obsidian, GitHub)

**Weaknesses:**
- 🔴 Algorithms слишком абстрактные (pattern detection, scoring)
- 🔴 Formulas отсутствуют (coupling_score, coverage_estimate, test_quality_score)
- 🔴 File adaptation logic не описана
- 🔴 Import mapping algorithm не определён
- 🔴 GitHub API integration не детализирован
- 🔴 Error handling scenarios не покрыты
- 🔴 Retry logic не описана
- 🔴 Test scenarios и mock data не определены

**After fixing 8 blockers and 12 major issues:** Спецификация будет готова к реализации с высокой уверенностью в успехе.

**Realistic Implementation Time:** 14-18 hours (vs spec estimate 8-12 hours)

**Recommendation:** Consolidate Opus and Sonnet reviews, apply fixes, then start implementation.

---

**Review Completed:** 2026-05-13  
**Reviewer:** Implementation Reviewer (Sonnet 4.5)  
**Status:** ⚠️ NEEDS CLARIFICATION (fix 8 blockers + 12 major issues)
