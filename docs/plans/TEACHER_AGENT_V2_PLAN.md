# Teacher Agent v2.0 - Deep Analysis & Full Adoption

**Version:** 2.0.0  
**Status:** 📋 Planning  
**Created:** 2026-05-13  
**Estimated Time:** 8-12 hours

---

## Goal

Upgrade Teacher Agent from pattern detection (v1.0) to deep analysis and full adoption (v2.0).

**Current (v1.0):**
- Detects missing patterns (circuit_breaker, retry, caching)
- Generates gap reports
- Manual upgrade required

**Target (v2.0):**
- Analyzes GitHub solutions completely (architecture, implementation, tests)
- Compares solutions and decides: Full/Partial/Custom adoption
- Automatically adopts full solutions with adaptation
- Generates detailed adoption reports

---

## Architecture Changes

### New Components (4 major)

1. **ArchitectureAnalyzer** - анализ архитектуры целиком
2. **SolutionComparator** - сравнение решений + принятие решения
3. **FullAdopter** - полное внедрение с адаптацией
4. **AdoptionReportGenerator** - детальные отчёты

### Updated Components (3 existing)

1. **GitHubFinder** - приоритет reference repos
2. **CodeAnalyzer** - анализ связей между компонентами
3. **TeacherAgent** - новый workflow с deep analysis

---

## Implementation Plan

### Phase 1: Architecture Analysis (3-4 hours)

**Goal:** Научить Teacher Agent анализировать архитектуру GitHub решений целиком.

#### Task 1.1: FileStructureAnalyzer

**File:** `AIM/src/aim/teacher/architecture/file_structure_analyzer.py`

**Functionality:**
- Сканирует структуру директорий
- Определяет назначение файлов (client, model, test, config)
- Находит entry points
- Выявляет конфигурационные файлы

**Output:**
```python
@dataclass
class FileStructure:
    entry_points: list[str]  # main.py, __init__.py
    clients: list[str]  # *client.py, *api.py
    models: list[str]  # *model.py, *schema.py
    tests: list[str]  # test_*.py
    configs: list[str]  # settings.py, config.py
    utils: list[str]  # utils/, helpers/
```

**Tests:** `AIM/tests/teacher/architecture/test_file_structure_analyzer.py`

#### Task 1.2: ComponentRelationAnalyzer

**File:** `AIM/src/aim/teacher/architecture/component_relation_analyzer.py`

**Functionality:**
- Строит граф зависимостей между модулями
- Определяет coupling (сильная/слабая связь)
- Находит circular dependencies
- Выявляет core vs peripheral components

**Output:**
```python
@dataclass
class ComponentRelations:
    dependency_graph: dict[str, list[str]]  # module -> dependencies
    coupling_score: float  # 0-100 (100 = low coupling)
    circular_deps: list[tuple[str, str]]  # circular dependencies
    core_components: list[str]  # most depended upon
```

**Tests:** `AIM/tests/teacher/architecture/test_component_relation_analyzer.py`

#### Task 1.3: DesignPatternDetector

**File:** `AIM/src/aim/teacher/architecture/design_pattern_detector.py`

**Functionality:**
- Детектирует паттерны проектирования (Strategy, Factory, Observer)
- Находит архитектурные стили (Layered, Hexagonal)
- Определяет принципы (SOLID, DRY)

**Patterns to detect:**
- Strategy: multiple implementations of same interface
- Factory: creation methods returning different types
- Observer: event/callback patterns
- Singleton: single instance patterns
- Dependency Injection: constructor injection

**Output:**
```python
@dataclass
class DesignPatterns:
    patterns: list[str]  # ["Strategy", "Factory"]
    architecture_style: str  # "Layered" | "Hexagonal" | "Clean"
    solid_compliance: dict[str, bool]  # S, O, L, I, D
```

**Tests:** `AIM/tests/teacher/architecture/test_design_pattern_detector.py`

#### Task 1.4: TestCoverageAnalyzer

**File:** `AIM/src/aim/teacher/architecture/test_coverage_analyzer.py`

**Functionality:**
- Анализирует структуру тестов (unit, integration, e2e)
- Оценивает покрытие (по количеству тестов vs функций)
- Находит fixtures и mocks
- Определяет тестовые сценарии

**Output:**
```python
@dataclass
class TestCoverage:
    test_types: dict[str, int]  # {"unit": 50, "integration": 10}
    coverage_estimate: float  # 0-100 (based on test count)
    has_fixtures: bool
    has_mocks: bool
    test_scenarios: list[str]  # extracted from test names
```

**Tests:** `AIM/tests/teacher/architecture/test_test_coverage_analyzer.py`

#### Task 1.5: ArchitectureAnalyzer (orchestrator)

**File:** `AIM/src/aim/teacher/architecture/architecture_analyzer.py`

**Functionality:**
- Оркестрирует все sub-analyzers
- Агрегирует результаты
- Вычисляет общий quality score

**Output:**
```python
@dataclass
class ArchitectureAnalysis:
    file_structure: FileStructure
    component_relations: ComponentRelations
    design_patterns: DesignPatterns
    test_coverage: TestCoverage
    quality_score: float  # 0-100 (weighted average)
```

**Tests:** `AIM/tests/teacher/architecture/test_architecture_analyzer.py`

---

### Phase 2: Solution Comparison (2-3 hours)

**Goal:** Научить Teacher Agent сравнивать решения и принимать решение о внедрении.

#### Task 2.1: ArchitectureScorer

**File:** `AIM/src/aim/teacher/comparison/architecture_scorer.py`

**Functionality:**
- Оценивает modularity (0-100)
- Оценивает testability (0-100)
- Оценивает maintainability (0-100)
- Оценивает scalability (0-100)

**Scoring criteria:**
- Modularity: low coupling + high cohesion
- Testability: test coverage + test structure
- Maintainability: code complexity + documentation
- Scalability: design patterns + architecture style

**Output:**
```python
@dataclass
class ArchitectureScore:
    modularity: float  # 0-100
    testability: float  # 0-100
    maintainability: float  # 0-100
    scalability: float  # 0-100
    overall: float  # weighted average
```

**Tests:** `AIM/tests/teacher/comparison/test_architecture_scorer.py`

#### Task 2.2: QualityScorer

**File:** `AIM/src/aim/teacher/comparison/quality_scorer.py`

**Functionality:**
- Оценивает patterns (0-100): наличие production patterns
- Оценивает error handling (0-100): try/except coverage
- Оценивает documentation (0-100): docstrings, comments
- Оценивает code quality (0-100): complexity, style

**Output:**
```python
@dataclass
class QualityScore:
    patterns: float  # 0-100
    error_handling: float  # 0-100
    documentation: float  # 0-100
    code_quality: float  # 0-100
    overall: float  # weighted average
```

**Tests:** `AIM/tests/teacher/comparison/test_quality_scorer.py`

#### Task 2.3: FitAnalyzer

**File:** `AIM/src/aim/teacher/comparison/fit_analyzer.py`

**Functionality:**
- Task Match (0-100): соответствие задаче агента
- Integration Effort (0-100): сложность интеграции (инверсия)
- Dependency Compatibility (0-100): совместимость зависимостей
- Customization Need (0-100): необходимость кастомизации (инверсия)

**Output:**
```python
@dataclass
class FitScore:
    task_match: float  # 0-100
    integration_effort: float  # 0-100 (100 = easy)
    dependency_compatibility: float  # 0-100
    customization_need: float  # 0-100 (100 = no customization)
    overall: float  # weighted average
```

**Tests:** `AIM/tests/teacher/comparison/test_fit_analyzer.py`

#### Task 2.4: DecisionMaker

**File:** `AIM/src/aim/teacher/comparison/decision_maker.py`

**Functionality:**
- Анализирует все scores
- Применяет правила принятия решений
- Возвращает: Full/Partial/Custom + rationale

**Decision Rules:**
```python
if fit_score >= 90 and quality_score >= 80:
    return "Full Adoption"
elif fit_score >= 70 and quality_score >= 70:
    return "Partial Adoption"
else:
    return "Custom Development"
```

**Output:**
```python
@dataclass
class AdoptionDecision:
    decision: str  # "Full" | "Partial" | "Custom"
    rationale: str  # detailed explanation
    confidence: float  # 0-100
    risks: list[str]  # potential risks
    benefits: list[str]  # expected benefits
```

**Tests:** `AIM/tests/teacher/comparison/test_decision_maker.py`

#### Task 2.5: SolutionComparator (orchestrator)

**File:** `AIM/src/aim/teacher/comparison/solution_comparator.py`

**Functionality:**
- Оркестрирует все scorers
- Сравнивает GitHub solution vs our agent
- Вызывает DecisionMaker
- Генерирует comparison report

**Output:**
```python
@dataclass
class ComparisonResult:
    github_analysis: ArchitectureAnalysis
    our_analysis: ArchitectureAnalysis
    github_score: float  # 0-100
    our_score: float  # 0-100
    fit_score: float  # 0-100
    decision: AdoptionDecision
```

**Tests:** `AIM/tests/teacher/comparison/test_solution_comparator.py`

---

### Phase 3: Full Adoption (3-4 hours)

**Goal:** Научить Teacher Agent полностью внедрять GitHub решения.

#### Task 3.1: FileCopier

**File:** `AIM/src/aim/teacher/adoption/file_copier.py`

**Functionality:**
- Копирует файлы из GitHub репо
- Адаптирует naming conventions (snake_case, PascalCase)
- Обновляет docstrings (добавляет "Adopted from {repo}")
- Сохраняет backup оригинальных файлов

**Output:**
```python
@dataclass
class CopyResult:
    files_copied: list[str]
    files_adapted: list[str]
    backup_path: str
    issues: list[str]
```

**Tests:** `AIM/tests/teacher/adoption/test_file_copier.py`

#### Task 3.2: DependencyInstaller

**File:** `AIM/src/aim/teacher/adoption/dependency_installer.py`

**Functionality:**
- Извлекает зависимости из requirements.txt / pyproject.toml
- Проверяет совместимость версий
- Устанавливает через pip
- Обновляет наш requirements.txt

**Output:**
```python
@dataclass
class DependencyResult:
    dependencies_installed: list[str]
    version_conflicts: list[str]
    requirements_updated: bool
```

**Tests:** `AIM/tests/teacher/adoption/test_dependency_installer.py`

#### Task 3.3: ImportUpdater

**File:** `AIM/src/aim/teacher/adoption/import_updater.py`

**Functionality:**
- Обновляет импорты в скопированных файлах
- Адаптирует пути (их структура → наша структура)
- Добавляет интеграцию с Event Bus, Obsidian
- Проверяет отсутствие circular imports

**Output:**
```python
@dataclass
class ImportUpdateResult:
    files_updated: list[str]
    imports_added: list[str]
    circular_deps_found: list[tuple[str, str]]
```

**Tests:** `AIM/tests/teacher/adoption/test_import_updater.py`

#### Task 3.4: TestMigrator

**File:** `AIM/src/aim/teacher/adoption/test_migrator.py`

**Functionality:**
- Копирует тесты из GitHub репо
- Адаптирует fixtures и mocks
- Обновляет импорты в тестах
- Интегрирует с нашим pytest setup

**Output:**
```python
@dataclass
class TestMigrationResult:
    tests_copied: list[str]
    fixtures_adapted: list[str]
    integration_issues: list[str]
```

**Tests:** `AIM/tests/teacher/adoption/test_test_migrator.py`

#### Task 3.5: IntegrationVerifier

**File:** `AIM/src/aim/teacher/adoption/integration_verifier.py`

**Functionality:**
- Запускает тесты → проверяет что всё работает
- Проверяет интеграцию с Event Bus
- Проверяет интеграцию с Obsidian
- Генерирует отчёт о проблемах

**Output:**
```python
@dataclass
class VerificationResult:
    tests_passing: int
    tests_failing: int
    event_bus_ok: bool
    obsidian_ok: bool
    issues: list[str]
```

**Tests:** `AIM/tests/teacher/adoption/test_integration_verifier.py`

#### Task 3.6: FullAdopter (orchestrator)

**File:** `AIM/src/aim/teacher/adoption/full_adopter.py`

**Functionality:**
- Оркестрирует весь процесс внедрения
- Вызывает все sub-components последовательно
- Rollback при ошибках
- Генерирует adoption result

**Workflow:**
```
1. FileCopier → copy files
2. DependencyInstaller → install deps
3. ImportUpdater → update imports
4. TestMigrator → migrate tests
5. IntegrationVerifier → verify
6. If failed → rollback from backup
```

**Output:**
```python
@dataclass
class AdoptionResult:
    success: bool
    files_copied: list[str]
    dependencies_installed: list[str]
    tests_passing: int
    tests_failing: int
    issues: list[str]
    rollback_performed: bool
```

**Tests:** `AIM/tests/teacher/adoption/test_full_adopter.py`

---

### Phase 4: Reporting & Integration (1-2 hours)

**Goal:** Генерировать детальные отчёты и интегрировать с TeacherAgent.

#### Task 4.1: AdoptionReportGenerator

**File:** `AIM/src/aim/teacher/adoption_report.py`

**Functionality:**
- Генерирует markdown отчёт о внедрении
- Включает все детали (что взяли, как адаптировали, результаты)
- Сохраняет в `AIM/reports/teacher/adoptions/`

**Report Structure:** (см. спецификацию в TEACHER_AGENT.md)

**Tests:** `AIM/tests/teacher/test_adoption_report.py`

#### Task 4.2: Update TeacherAgent

**File:** `AIM/src/aim/teacher/teacher_agent.py`

**Changes:**
- Добавить метод `deep_audit_subagent()` с ArchitectureAnalyzer
- Добавить метод `compare_solutions()` с SolutionComparator
- Добавить метод `adopt_solution()` с FullAdopter
- Обновить workflow: audit → compare → adopt (if Full)

**New Methods:**
```python
def deep_audit_subagent(self, subagent_path: Path) -> ArchitectureAnalysis:
    """Deep analysis of subagent architecture."""
    
def compare_solutions(
    self, 
    our_analysis: ArchitectureAnalysis,
    github_analysis: ArchitectureAnalysis
) -> ComparisonResult:
    """Compare solutions and decide adoption strategy."""
    
def adopt_solution(
    self,
    subagent_path: Path,
    github_repo: str,
    decision: AdoptionDecision
) -> AdoptionResult:
    """Fully adopt GitHub solution."""
```

**Tests:** Update `AIM/tests/teacher/test_teacher_agent.py`

#### Task 4.3: Update CLI

**File:** `scripts/teacher_cli.py`

**New Commands:**
```bash
# Deep audit with architecture analysis
python scripts/teacher_cli.py deep-audit social_agent

# Compare solutions
python scripts/teacher_cli.py compare social_agent

# Adopt solution (if decision is Full)
python scripts/teacher_cli.py adopt social_agent --repo=python-social-api
```

**Tests:** Manual testing

---

## File Structure

```
AIM/src/aim/teacher/
├── architecture/
│   ├── __init__.py
│   ├── file_structure_analyzer.py
│   ├── component_relation_analyzer.py
│   ├── design_pattern_detector.py
│   ├── test_coverage_analyzer.py
│   └── architecture_analyzer.py
├── comparison/
│   ├── __init__.py
│   ├── architecture_scorer.py
│   ├── quality_scorer.py
│   ├── fit_analyzer.py
│   ├── decision_maker.py
│   └── solution_comparator.py
├── adoption/
│   ├── __init__.py
│   ├── file_copier.py
│   ├── dependency_installer.py
│   ├── import_updater.py
│   ├── test_migrator.py
│   ├── integration_verifier.py
│   └── full_adopter.py
├── adoption_report.py
└── teacher_agent.py (updated)

AIM/tests/teacher/
├── architecture/
│   ├── test_file_structure_analyzer.py
│   ├── test_component_relation_analyzer.py
│   ├── test_design_pattern_detector.py
│   ├── test_test_coverage_analyzer.py
│   └── test_architecture_analyzer.py
├── comparison/
│   ├── test_architecture_scorer.py
│   ├── test_quality_scorer.py
│   ├── test_fit_analyzer.py
│   ├── test_decision_maker.py
│   └── test_solution_comparator.py
├── adoption/
│   ├── test_file_copier.py
│   ├── test_dependency_installer.py
│   ├── test_import_updater.py
│   ├── test_test_migrator.py
│   ├── test_integration_verifier.py
│   └── test_full_adopter.py
└── test_adoption_report.py

AIM/reports/teacher/adoptions/
└── {agent_name}_adoption_{date}.md
```

---

## Testing Strategy

**Unit Tests:**
- Каждый компонент имеет свои unit tests
- Моки для внешних зависимостей (GitHub API, file system)
- Coverage target: 90%+

**Integration Tests:**
- Тестирование orchestrators (ArchitectureAnalyzer, SolutionComparator, FullAdopter)
- Реальные GitHub репо (небольшие, для тестов)
- Проверка end-to-end workflow

**E2E Tests:**
- Полный цикл: deep-audit → compare → adopt
- Реальный субагент (создать test_agent для этого)
- Проверка rollback при ошибках

---

## Success Criteria

**Phase 1 (Architecture Analysis):**
- ✅ ArchitectureAnalyzer анализирует GitHub репо
- ✅ Генерирует ArchitectureAnalysis с quality_score
- ✅ Все 5 sub-analyzers работают
- ✅ 15+ unit tests passing

**Phase 2 (Solution Comparison):**
- ✅ SolutionComparator сравнивает решения
- ✅ DecisionMaker принимает решение (Full/Partial/Custom)
- ✅ Генерирует ComparisonResult с rationale
- ✅ 10+ unit tests passing

**Phase 3 (Full Adoption):**
- ✅ FullAdopter копирует файлы с адаптацией
- ✅ Устанавливает зависимости
- ✅ Обновляет импорты
- ✅ Мигрирует тесты
- ✅ Проверяет интеграцию
- ✅ Rollback работает при ошибках
- ✅ 15+ unit tests passing

**Phase 4 (Reporting & Integration):**
- ✅ AdoptionReportGenerator генерирует детальные отчёты
- ✅ TeacherAgent интегрирован с новыми компонентами
- ✅ CLI команды работают
- ✅ E2E test passing

**Overall:**
- ✅ 40+ tests passing
- ✅ Coverage 90%+
- ✅ Documentation updated
- ✅ Real adoption test successful

---

## Risks & Mitigation

**Risk 1: Сложность адаптации кода**
- Mitigation: Начать с простых репо, постепенно усложнять
- Fallback: Partial adoption если Full не работает

**Risk 2: Конфликты зависимостей**
- Mitigation: Проверка совместимости версий
- Fallback: Виртуальное окружение для тестирования

**Risk 3: Circular imports после адаптации**
- Mitigation: ImportUpdater проверяет circular deps
- Fallback: Ручная корректировка импортов

**Risk 4: Тесты не проходят после внедрения**
- Mitigation: IntegrationVerifier + rollback
- Fallback: Откат к backup, ручная доработка

---

## Timeline

**Total:** 8-12 hours

- **Phase 1:** 3-4 hours (Architecture Analysis)
- **Phase 2:** 2-3 hours (Solution Comparison)
- **Phase 3:** 3-4 hours (Full Adoption)
- **Phase 4:** 1-2 hours (Reporting & Integration)

**Recommended approach:** TDD (Test-Driven Development)
- Писать тесты сначала
- Реализовывать компоненты
- Рефакторить при необходимости

---

## Next Steps

1. **Review plan** с пользователем
2. **Start Phase 1** (Architecture Analysis)
3. **Iterate** через все фазы
4. **Test** на реальном агенте
5. **Deploy** v2.0

---

**Created:** 2026-05-13  
**Author:** meAI Architect (via Claude Sonnet 4)  
**Status:** 📋 Ready for implementation
