# Teacher Agent - Chief Learning Officer

**Version:** 1.0.0  
**Status:** ✅ Production Ready  
**Created:** 2026-05-13

## Overview

Teacher Agent — автономный Chief Learning Officer системы meAI. Его задача — непрерывно обучать и улучшать субагентов, используя лучшие практики из GitHub.

## Core Principles: Deep Analysis & Full Adoption

**КРИТИЧЕСКИ ВАЖНО:** Teacher Agent должен работать как архитектор-копировщик, а не просто детектор пробелов.

### Принцип 1: Разбор по молекулам

**Требование:** Анализировать GitHub решения ПОЛНОСТЬЮ, а не только отдельные паттерны.

**Что анализировать:**
1. **Архитектура:**
   - Структура файлов и директорий
   - Связи между компонентами
   - Паттерны проектирования (Strategy, Factory, Observer)
   - Разделение ответственности (SRP, DRY)

2. **Реализация:**
   - Как организован код (классы, функции, модули)
   - Как обрабатываются ошибки end-to-end
   - Как реализованы resilience patterns (circuit breaker + retry + rate limiting вместе)
   - Как организовано логирование и метрики

3. **Тестирование:**
   - Структура тестов (unit, integration, e2e)
   - Покрытие кода
   - Моки и фикстуры
   - Тестовые сценарии

4. **Зависимости:**
   - Какие библиотеки используются
   - Версии и совместимость
   - Конфигурация (settings, env vars)

**Запрещено:**
- ❌ Анализировать только отдельные паттерны (circuit_breaker, retry)
- ❌ Смотреть только на один файл
- ❌ Игнорировать архитектуру и связи

**Обязательно:**
- ✅ Изучить ВСЮ архитектуру решения
- ✅ Понять КАК компоненты работают вместе
- ✅ Разобрать ПОЧЕМУ выбраны такие решения
- ✅ Найти edge cases и их обработку

### Принцип 2: Решение о внедрении

**Три варианта:**

#### A. Полное внедрение (100% adoption)

**Когда:** GitHub решение подходит на 100% под наши задачи.

**Критерии:**
- ✅ Решает ту же задачу, что наш агент
- ✅ Архитектура лучше нашей (modularity, testability, maintainability)
- ✅ Все паттерны production-ready
- ✅ Хорошее тестовое покрытие
- ✅ Активная поддержка (commits, issues, stars)

**Действия:**
1. Копировать архитектуру полностью (файлы, структура)
2. Адаптировать под наши naming conventions
3. Установить зависимости
4. Портировать тесты
5. Интегрировать с нашей системой (Event Bus, Obsidian)
6. Запустить тесты → всё работает
7. Закоммитить: `refactor(agent): adopt production architecture from {repo}`

**Пример:**
```
Нашли: python-social-media-api-client (1000+ stars)
Их архитектура:
  - client/base.py (все resilience patterns)
  - client/twitter.py (наследуется от base)
  - models/post.py (Pydantic схемы)
  - tests/ (95% coverage)

Наш social_agent.py: 4.2 KB, всё в одном файле

Решение: ПОЛНОЕ ВНЕДРЕНИЕ
→ Создаём social_agent/client/, models/, tests/
→ Копируем их архитектуру с адаптацией
→ Результат: production-ready агент
```

#### B. Частичное внедрение (Partial adoption)

**Когда:** GitHub решение частично подходит, но не на 100%.

**Критерии:**
- ✅ Решает похожую задачу
- ⚠️ Архитектура избыточна или недостаточна
- ✅ Есть ценные паттерны и решения
- ⚠️ Нужна адаптация под наши нужды

**Действия:**
1. Взять лучшие куски (классы, функции, паттерны)
2. Адаптировать под нашу архитектуру
3. Интегрировать с существующим кодом
4. Добавить недостающее
5. Протестировать
6. Закоммитить: `feat(agent): adopt {pattern} from {repo}`

**Пример:**
```
Нашли: content-analyzer-ml (500+ stars)
Их решение: ML-модель для анализа контента
Наш агент: rule-based анализ

Решение: ЧАСТИЧНОЕ ВНЕДРЕНИЕ
→ Берём их feature extraction (TF-IDF, embeddings)
→ Берём их error handling patterns
→ НЕ берём ML-модель (пока не нужна)
→ Результат: улучшенный feature extraction
```

#### C. Разработка своего (Custom development)

**Когда:** GitHub решения не подходят.

**Критерии:**
- ❌ Нет подходящих решений на GitHub
- ❌ Все решения устаревшие или плохого качества
- ✅ Наша задача уникальна
- ✅ Но есть лучшие практики для изучения

**Действия:**
1. Изучить лучшие практики из топовых репо
2. Взять архитектурные паттерны
3. Разработать своё решение с нуля
4. Применить все production patterns
5. Протестировать
6. Закоммитить: `feat(agent): implement {feature} with best practices`

**Пример:**
```
Задача: Medical content compliance checker (YMYL)
GitHub: нет специализированных решений

Решение: РАЗРАБОТКА СВОЕГО
→ Изучаем архитектуру из healthcare-compliance-tools
→ Берём паттерны из content-analyzers
→ Разрабатываем свой checker с этими паттернами
→ Результат: уникальное решение с best practices
```

### Принцип 3: Качество важнее скорости

**Правило:** Лучше потратить 2 часа на глубокий анализ, чем 10 минут на поверхностный.

**Почему:**
- Поверхностный анализ → пропускаем важные детали
- Глубокий анализ → находим edge cases, архитектурные решения, best practices
- Качественное внедрение → агент работает production-ready

**Время на анализ:**
- Простой агент (API client): 30-60 минут
- Средний агент (content analyzer): 1-2 часа
- Сложный агент (ML pipeline): 2-4 часа

### Принцип 4: Документирование решений

**Требование:** Каждое решение о внедрении должно быть задокументировано.

**Что документировать:**
1. **Какие GitHub репо изучены** (название, stars, URL)
2. **Что взяли** (архитектура, паттерны, код)
3. **Почему взяли** (критерии, преимущества)
4. **Как адаптировали** (изменения, интеграция)
5. **Результат** (метрики, тесты, score)

**Формат:**
```markdown
# Adoption Report: {agent_name}

## GitHub Repositories Analyzed
1. {repo_name} ({stars} stars) - {description}
   - Architecture: {summary}
   - Patterns: {list}
   - Quality: {score}/100

## Decision: {Full/Partial/Custom}

**Rationale:**
- {reason 1}
- {reason 2}

## What We Adopted
- {component 1}: {description}
- {component 2}: {description}

## Adaptations Made
- {change 1}
- {change 2}

## Results
- Score: {before} → {after}
- Tests: {count} passing
- Coverage: {percentage}%
```

## Architecture

### Current Architecture (v1.0 - Pattern Detection)

```
Teacher Agent
  ↓
1. SubagentInventory → сканирует все субагенты
  ↓
2. GitHubFinder → находит топовые репо по теме
  ↓
3. RepoCloner → клонирует репо для анализа
  ↓
4. CodeAnalyzer → анализирует код (imports, patterns, complexity)
  ↓
5. GapDetector → сравнивает наш код vs GitHub
  ↓
6. AuditReportGenerator → генерирует отчёт с gaps
  ↓
7. PatternExtractor → извлекает паттерны из GitHub
  ↓
8. CodeGenerator → генерирует код для внедрения
  ↓
9. UpgradeApplier → применяет улучшения с backup
```

**Status:** ✅ Implemented (v1.0)  
**Capability:** Detects missing patterns, generates gap reports

### Target Architecture (v2.0 - Deep Analysis & Full Adoption)

```
Teacher Agent
  ↓
1. SubagentInventory → сканирует все субагенты
  ↓
2. GitHubFinder → находит топовые репо (reference + topic-specific)
  ↓
3. RepoCloner → клонирует репо для анализа
  ↓
4. ArchitectureAnalyzer → анализирует архитектуру целиком ⭐ NEW
   ├─ FileStructureAnalyzer → структура файлов и директорий
   ├─ ComponentRelationAnalyzer → связи между компонентами
   ├─ DesignPatternDetector → паттерны проектирования
   └─ TestCoverageAnalyzer → тестовое покрытие
  ↓
5. SolutionComparator → сравнивает решения ⭐ NEW
   ├─ ArchitectureScorer → оценка архитектуры (modularity, testability)
   ├─ QualityScorer → оценка качества (patterns, error handling)
   ├─ FitAnalyzer → соответствие нашим задачам
   └─ DecisionMaker → Full/Partial/Custom adoption
  ↓
6. FullAdopter → полное внедрение решения ⭐ NEW
   ├─ FileCopier → копирование файлов с адаптацией
   ├─ DependencyInstaller → установка зависимостей
   ├─ ImportUpdater → обновление импортов
   ├─ TestMigrator → портирование тестов
   └─ IntegrationVerifier → проверка интеграции
  ↓
7. AdoptionReportGenerator → отчёт о внедрении ⭐ NEW
  ↓
8. [Legacy] GapDetector → сравнивает паттерны (fallback)
  ↓
9. [Legacy] PatternExtractor → извлекает паттерны (fallback)
  ↓
10. [Legacy] UpgradeApplier → частичное внедрение (fallback)
```

**Status:** 🚧 Planned (v2.0)  
**Capability:** Deep analysis, full adoption, architecture comparison

### New Components (v2.0)

#### 4. ArchitectureAnalyzer ⭐ NEW

**Purpose:** Анализирует архитектуру GitHub решения целиком.

**Sub-components:**

1. **FileStructureAnalyzer:**
   - Сканирует структуру директорий
   - Определяет назначение каждого файла
   - Находит entry points и main modules
   - Выявляет конфигурационные файлы

2. **ComponentRelationAnalyzer:**
   - Строит граф зависимостей между модулями
   - Определяет coupling и cohesion
   - Находит circular dependencies
   - Выявляет core vs peripheral components

3. **DesignPatternDetector:**
   - Детектирует паттерны проектирования (Strategy, Factory, Observer, etc.)
   - Находит архитектурные стили (Layered, Hexagonal, Clean Architecture)
   - Определяет принципы (SOLID, DRY, KISS)

4. **TestCoverageAnalyzer:**
   - Анализирует структуру тестов (unit, integration, e2e)
   - Оценивает покрытие кода
   - Находит test fixtures и mocks
   - Определяет тестовые сценарии

**Output:**
```python
@dataclass
class ArchitectureAnalysis:
    file_structure: dict[str, str]  # path -> purpose
    components: list[Component]  # name, type, dependencies
    design_patterns: list[str]  # detected patterns
    test_coverage: float  # percentage
    quality_score: float  # 0-100
```

#### 5. SolutionComparator ⭐ NEW

**Purpose:** Сравнивает GitHub решение с нашим агентом и принимает решение о внедрении.

**Sub-components:**

1. **ArchitectureScorer:**
   - Modularity (0-100): насколько модульная архитектура
   - Testability (0-100): насколько легко тестировать
   - Maintainability (0-100): насколько легко поддерживать
   - Scalability (0-100): насколько легко масштабировать

2. **QualityScorer:**
   - Patterns (0-100): наличие production patterns
   - Error Handling (0-100): обработка ошибок end-to-end
   - Documentation (0-100): качество документации
   - Code Quality (0-100): читаемость, стиль, complexity

3. **FitAnalyzer:**
   - Task Match (0-100): соответствие задаче
   - Integration Effort (0-100): сложность интеграции (инверсия: 100 = легко)
   - Dependency Compatibility (0-100): совместимость зависимостей
   - Customization Need (0-100): необходимость кастомизации (инверсия: 100 = не нужна)

4. **DecisionMaker:**
   - Анализирует все scores
   - Применяет правила принятия решений
   - Возвращает: Full/Partial/Custom + rationale

**Decision Rules:**
```python
if fit_score >= 90 and quality_score >= 80:
    return "Full Adoption"  # Подходит на 100%
elif fit_score >= 70 and quality_score >= 70:
    return "Partial Adoption"  # Берём лучшие куски
else:
    return "Custom Development"  # Разрабатываем своё
```

**Output:**
```python
@dataclass
class ComparisonResult:
    decision: str  # "Full" | "Partial" | "Custom"
    rationale: str  # Почему такое решение
    github_score: float  # 0-100
    our_score: float  # 0-100
    fit_score: float  # 0-100
    adoption_plan: AdoptionPlan  # Что делать
```

#### 6. FullAdopter ⭐ NEW

**Purpose:** Полное внедрение GitHub решения в наш агент.

**Sub-components:**

1. **FileCopier:**
   - Копирует файлы из GitHub репо
   - Адаптирует naming conventions
   - Обновляет docstrings и комментарии
   - Сохраняет backup оригинальных файлов

2. **DependencyInstaller:**
   - Извлекает зависимости из requirements.txt / pyproject.toml
   - Проверяет совместимость версий
   - Устанавливает через pip
   - Обновляет наш requirements.txt

3. **ImportUpdater:**
   - Обновляет импорты в скопированных файлах
   - Адаптирует пути (их структура → наша структура)
   - Добавляет интеграцию с Event Bus, Obsidian
   - Проверяет отсутствие circular imports

4. **TestMigrator:**
   - Копирует тесты из GitHub репо
   - Адаптирует fixtures и mocks
   - Обновляет импорты в тестах
   - Интегрирует с нашим pytest setup

5. **IntegrationVerifier:**
   - Запускает тесты → проверяет что всё работает
   - Проверяет интеграцию с Event Bus
   - Проверяет интеграцию с Obsidian
   - Генерирует отчёт о проблемах

**Output:**
```python
@dataclass
class AdoptionResult:
    success: bool
    files_copied: list[str]
    dependencies_installed: list[str]
    tests_passing: int
    tests_failing: int
    issues: list[str]  # Проблемы при внедрении
```

#### 7. AdoptionReportGenerator ⭐ NEW

**Purpose:** Генерирует детальный отчёт о внедрении.

**Report Structure:**
```markdown
# Adoption Report: {agent_name}

**Date:** {date}  
**Decision:** {Full/Partial/Custom}  
**Status:** {Success/Failed}

## GitHub Repositories Analyzed

1. **{repo_name}** ({stars} stars)
   - URL: {url}
   - Architecture Score: {score}/100
   - Quality Score: {score}/100
   - Fit Score: {score}/100

## Decision Rationale

{detailed explanation why Full/Partial/Custom}

## What We Adopted

### Architecture
- {component 1}: {description}
- {component 2}: {description}

### Patterns
- {pattern 1}: {description}
- {pattern 2}: {description}

### Dependencies
- {library 1}: {version}
- {library 2}: {version}

## Adaptations Made

1. {adaptation 1}
2. {adaptation 2}

## Integration

- Event Bus: {status}
- Obsidian: {status}
- Tests: {passing}/{total}

## Results

**Before:**
- Score: {score}/100
- Patterns: {list}
- Tests: {count}

**After:**
- Score: {score}/100
- Patterns: {list}
- Tests: {count}

**Improvement:** +{delta} points
```

## Components

### 1. SubagentInventory

Сканирует все субагенты в `AIM/src/aim/subagents/`:
- Извлекает метаданные (name, path, created_date, lines_of_code)
- Определяет наличие GitHub integration
- Использует git log для определения даты создания

**Usage:**
```python
from AIM.src.aim.teacher.subagent_inventory import SubagentInventory

inventory = SubagentInventory()
subagents = inventory.scan()

for subagent in subagents:
    print(f"{subagent.name}: {subagent.lines_of_code} lines")
```

### 2. GitHubFinder

Находит релевантные GitHub репозитории:
- GitHub API search с фильтрацией по звёздам (min 50)
- Сортировка по популярности
- Возвращает top-N репозиториев

**Usage:**
```python
from AIM.src.aim.teacher.github_finder import GitHubFinder

finder = GitHubFinder(github_token="your_token")
repos = await finder.find_repos(
    topic="content writer",
    min_stars=50,
    max_results=3
)
```

### 3. RepoCloner

Клонирует репозитории для анализа:
- Клонирует в `~/temp/research-repos/`
- Skip если уже склонирован
- Timeout 300s для больших репо

**Usage:**
```python
from AIM.src.aim.teacher.repo_cloner import RepoCloner

cloner = RepoCloner()
local_path = await cloner.clone(
    repo_url="https://github.com/user/repo",
    target_dir="~/temp/research-repos"
)
```

### 4. CodeAnalyzer

Анализирует Python код:
- `extract_imports()` — извлекает все импорты через AST
- `detect_patterns()` — находит паттерны (circuit_breaker, retry, caching, rate_limiting, metrics, logging)
- `count_complexity()` — считает cyclomatic complexity

**Patterns Detected:**
- **circuit_breaker**: pybreaker, CircuitBreaker
- **retry**: tenacity, @retry
- **caching**: aiocache, @cached
- **rate_limiting**: aiolimiter, RateLimiter
- **metrics**: prometheus_client, Counter
- **logging**: structlog, get_logger

**Usage:**
```python
from AIM.src.aim.teacher.code_analyzer import CodeAnalyzer

analyzer = CodeAnalyzer()
result = analyzer.analyze_file("/path/to/file.py")

print(f"Imports: {result.imports}")
print(f"Patterns: {result.patterns}")
print(f"Complexity: {result.complexity}")
```

### 5. GapDetector

Сравнивает наш код vs GitHub:
- Находит missing patterns
- Классифицирует по severity (CRITICAL/HIGH/MEDIUM/LOW)
- Генерирует рекомендации

**Severity Levels:**
- **CRITICAL** (-30 points): circuit_breaker — production-breaking
- **HIGH** (-20 points): retry, rate_limiting — performance/reliability
- **MEDIUM** (-10 points): caching, metrics, logging — quality

**Scoring:**
- 100 - penalties = final score
- ≥80: ✅ PASS
- 60-79: ⚠️ NEEDS IMPROVEMENT
- <60: ❌ FAIL

**Usage:**
```python
from AIM.src.aim.teacher.gap_detector import GapDetector

detector = GapDetector()
result = detector.detect_gaps(
    our_code=our_analysis,
    github_codes=[github_analysis1, github_analysis2]
)

print(f"Score: {result.score}/100")
print(f"Gaps: {len(result.gaps)}")
```

### 6. AuditReportGenerator

Генерирует markdown отчёты:
- Группировка gaps по severity
- Список GitHub репозиториев
- Рекомендации по внедрению
- Сохранение в `AIM/reports/teacher/`

**Usage:**
```python
from AIM.src.aim.teacher.audit_report import AuditReportGenerator

generator = AuditReportGenerator()
report = generator.generate(
    subagent_name="content_writer_agent",
    gap_result=gap_result,
    github_repos=repos
)

generator.save(report, "AIM/reports/teacher/content_writer_agent_audit.md")
```

### 7. PatternExtractor

Извлекает паттерны из GitHub кода:
- Circuit breaker (pybreaker)
- Retry (tenacity)
- Rate limiting (aiolimiter)
- Caching (aiocache)
- Парсит параметры и imports

**Usage:**
```python
from AIM.src.aim.teacher.pattern_extractor import PatternExtractor

extractor = PatternExtractor()
pattern = extractor.extract_pattern(
    github_code=code,
    pattern_name="circuit_breaker"
)

print(f"Imports: {pattern.imports}")
print(f"Code: {pattern.code_snippet}")
```

### 8. CodeGenerator

Генерирует код для внедрения:
- `add_imports()` — добавляет импорты
- `add_to_init()` — добавляет код в __init__
- `add_decorator()` — добавляет декораторы
- Сохраняет отступы и форматирование

**Usage:**
```python
from AIM.src.aim.teacher.code_generator import CodeGenerator

generator = CodeGenerator()
new_code = generator.apply_pattern(
    original_code=code,
    pattern=pattern,
    gap=gap
)
```

### 9. UpgradeApplier

Применяет улучшения:
- Создаёт backup с timestamp
- Применяет все gaps через CodeGenerator
- Возвращает UpgradeResult с success status

**Usage:**
```python
from AIM.src.aim.teacher.upgrade_applier import UpgradeApplier

applier = UpgradeApplier()
result = applier.apply_upgrade(
    subagent_path="/path/to/agent.py",
    gaps=gaps,
    patterns=patterns
)

if result.success:
    print(f"✅ Upgrade successful - {result.patterns_applied} patterns applied")
else:
    print(f"❌ Upgrade failed: {result.error}")
```

## CLI Usage

### Audit Single Subagent

```bash
python scripts/teacher_cli.py audit content_writer_agent
```

**Output:**
```
🔍 Auditing content_writer_agent...
📊 Score: 60.0/100
📝 Report saved to: AIM/reports/teacher/content_writer_agent_audit.md
⚠️  NEEDS IMPROVEMENT - Some gaps detected
```

### Audit All Subagents

```bash
python scripts/teacher_cli.py audit-all
```

**Output:**
```
🔍 Auditing all subagents...
📊 Audited 25 subagents:
✅ keyword_research_agent: 90.0/100
⚠️  content_writer_agent: 60.0/100
❌ seo_analyzer_agent: 40.0/100
...
📝 Summary saved to: AIM/reports/teacher/audit_summary.md
```

### Upgrade Subagent

```bash
python scripts/teacher_cli.py upgrade content_writer_agent
```

**Output:**
```
🔧 Upgrading content_writer_agent...
✅ Upgrade successful - 3 patterns applied
```

### Show Subagent Info

```bash
python scripts/teacher_cli.py info content_writer_agent
```

**Output:**
```
📋 Subagent: content_writer_agent
📁 Path: AIM/src/aim/subagents/content_writer_agent.py
📅 Created: 2026-05-01
📏 Lines: 450
🔗 GitHub Integration: No
```

## Workflow

### Learning Cycle (Every 2-4 Weeks)

1. **Scan Subagents**
   ```python
   teacher = TeacherAgent()
   subagents = teacher.inventory.scan()
   ```

2. **Audit All**
   ```python
   results = teacher.audit_all()
   ```

3. **Prioritize**
   - CRITICAL (score < 60): Upgrade immediately
   - HIGH (score 60-79): Plan for next sprint
   - MEDIUM (score ≥ 80): Backlog

4. **Upgrade Critical**
   ```python
   for result in results:
       if result.score < 60:
           teacher.upgrade_subagent(path, result)
   ```

5. **Save Reports**
   - Individual reports: `AIM/reports/teacher/{agent}_audit.md`
   - Summary: `AIM/reports/teacher/audit_summary.md`

### Manual Workflow

1. **Audit Single Subagent**
   ```bash
   python scripts/teacher_cli.py audit content_writer_agent
   ```

2. **Review Report**
   ```bash
   cat AIM/reports/teacher/content_writer_agent_audit.md
   ```

3. **Upgrade if Needed**
   ```bash
   python scripts/teacher_cli.py upgrade content_writer_agent
   ```

4. **Verify Changes**
   ```bash
   git diff AIM/src/aim/subagents/content_writer_agent.py
   ```

5. **Test**
   ```bash
   pytest AIM/tests/subagents/test_content_writer_agent.py
   ```

6. **Commit**
   ```bash
   git add AIM/src/aim/subagents/content_writer_agent.py
   git commit -m "feat(teacher): upgrade content_writer_agent with GitHub patterns"
   ```

## Example Audit Report

```markdown
# Audit Report: content_writer_agent

**Date:** 2026-05-13 12:00:00  
**Score:** 60.0/100  
**Status:** ⚠️ NEEDS IMPROVEMENT

---

## GitHub Repositories Analyzed

- sethblack/python-seo-analyzer (300+ stars)
- user/content-writer (150+ stars)

---

## Gaps Detected

### 🔴 CRITICAL (implement immediately)

**circuit_breaker**
- Missing circuit breaker pattern found in GitHub repo
- **Action:** Add pybreaker with fail_max=5, reset_timeout=60s

### 🟡 HIGH (plan for next sprint)

**retry**
- Missing retry pattern found in GitHub repo
- **Action:** Add tenacity with exponential backoff (1s → 30s max)

**rate_limiting**
- Missing rate limiting pattern found in GitHub repo
- **Action:** Add aiolimiter with token bucket algorithm

### 🟢 MEDIUM (backlog)

**caching**
- Missing caching pattern found in GitHub repo
- **Action:** Add aiocache with 1-hour TTL

**metrics**
- Missing metrics pattern found in GitHub repo
- **Action:** Add prometheus_client for monitoring

**logging**
- Missing structured logging pattern found in GitHub repo
- **Action:** Add structlog for better observability

---

**Generated by Teacher Agent**
```

## Testing

Run all tests:
```bash
pytest AIM/tests/teacher/ -v
```

**Test Coverage:**
- SubagentInventory: 2 tests
- GitHubFinder: 2 tests
- RepoCloner: 2 tests
- CodeAnalyzer: 3 tests
- GapDetector: 2 tests
- AuditReportGenerator: 2 tests
- PatternExtractor: 2 tests
- CodeGenerator: 2 tests
- UpgradeApplier: 2 tests
- TeacherAgent: 2 tests
- CLI: 2 tests

**Total:** 23 tests

Run specific component tests:
```bash
# Test code analyzer
pytest AIM/tests/teacher/test_code_analyzer.py -v

# Test gap detector
pytest AIM/tests/teacher/test_gap_detector.py -v

# Test upgrade applier
pytest AIM/tests/teacher/test_upgrade_applier.py -v
```

## Metrics

**Per Audit:**
- GitHub API calls: 1-3
- Repos cloned: 1-3
- Time: 30-60 seconds
- Cost: Free (GitHub API)

**Per Upgrade:**
- Backup created: Yes (with timestamp)
- Patterns applied: 1-5
- Time: 5-10 seconds
- Rollback: Manual (restore from backup)

**Audit All (25 subagents):**
- Time: 15-30 minutes
- GitHub API calls: 25-75
- Repos cloned: 25-75
- Reports generated: 26 (25 individual + 1 summary)

## Configuration

### Environment Variables

Add to `.env`:
```bash
# Teacher Agent Configuration
GITHUB_TOKEN=your_github_token_here  # Optional, increases rate limit
TEACHER_MIN_STARS=50                 # Min stars for GitHub repos
TEACHER_MAX_REPOS=3                  # Max repos to analyze per subagent
TEACHER_CLONE_TIMEOUT=300            # Clone timeout in seconds
```

### GitHub Token

Get token from: https://github.com/settings/tokens

**Permissions needed:**
- `public_repo` (read public repositories)

**Rate Limits:**
- Without token: 60 requests/hour
- With token: 5000 requests/hour

## Future Enhancements

### 1. Automatic Scheduling

```python
# Cron job every 2 weeks
@cron("0 0 */14 * *")
async def auto_audit():
    teacher = TeacherAgent()
    results = await teacher.audit_all()
    
    # Auto-upgrade CRITICAL gaps
    for result in results:
        if result.score < 60:
            await teacher.upgrade_subagent(result.path, result)
```

### 2. Deep Analysis

- AST-based pattern extraction
- Semantic code similarity (embeddings)
- Dependency graph analysis
- Performance profiling

### 3. Learning from Feedback

- Track upgrade success rate
- Learn which patterns work best
- A/B testing for patterns
- Feedback loop from production metrics

### 4. Multi-Language Support

- TypeScript/JavaScript
- Go, Rust
- Java, C#

### 5. Integration with CI/CD

```yaml
# .github/workflows/teacher-audit.yml
name: Teacher Audit
on:
  schedule:
    - cron: '0 0 */14 * *'  # Every 2 weeks
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Teacher Audit
        run: python scripts/teacher_cli.py audit-all
      - name: Upload Reports
        uses: actions/upload-artifact@v2
        with:
          name: audit-reports
          path: AIM/reports/teacher/
```

## Files

### Source Code

```
AIM/src/aim/teacher/
├── __init__.py
├── teacher_agent.py          # Main orchestrator
├── subagent_inventory.py     # Subagent scanner
├── github_finder.py          # GitHub search
├── repo_cloner.py            # Repository cloner
├── code_analyzer.py          # Code analysis
├── gap_detector.py           # Gap detection
├── audit_report.py           # Report generation
├── pattern_extractor.py      # Pattern extraction
├── code_generator.py         # Code generation
└── upgrade_applier.py        # Upgrade application
```

### CLI

```
scripts/
└── teacher_cli.py            # Command-line interface
```

### Tests

```
AIM/tests/teacher/
├── __init__.py
├── test_subagent_inventory.py
├── test_github_finder.py
├── test_repo_cloner.py
├── test_code_analyzer.py
├── test_gap_detector.py
├── test_audit_report.py
├── test_pattern_extractor.py
├── test_code_generator.py
├── test_upgrade_applier.py
├── test_teacher_agent.py
└── test_teacher_cli.py
```

### Reports

```
AIM/reports/teacher/
├── {agent}_audit.md          # Individual audit reports
└── audit_summary.md          # Summary of all audits
```

## Troubleshooting

### GitHub API Rate Limit

**Problem:** `GitHub API rate limit exceeded`

**Solution:**
1. Add GitHub token to `.env`
2. Wait for rate limit reset (check headers)
3. Reduce `TEACHER_MAX_REPOS`

### Clone Timeout

**Problem:** `Repository clone timeout`

**Solution:**
1. Increase `TEACHER_CLONE_TIMEOUT`
2. Check network connection
3. Skip large repos (>100MB)

### Pattern Not Detected

**Problem:** Pattern exists but not detected

**Solution:**
1. Check pattern keywords in `code_analyzer.py`
2. Add custom pattern detection
3. Use AST-based detection instead of regex

### Upgrade Failed

**Problem:** `Upgrade failed: syntax error`

**Solution:**
1. Check backup file (`.backup.{timestamp}`)
2. Restore from backup
3. Fix pattern manually
4. Report issue to Teacher Agent

## Best Practices

### 1. Regular Audits

Run audits every 2-4 weeks to keep subagents up-to-date.

### 2. Review Before Upgrade

Always review audit report before applying upgrade.

### 3. Test After Upgrade

Run tests after upgrade to ensure nothing broke.

### 4. Commit Frequently

Commit after each successful upgrade for easy rollback.

### 5. Monitor Metrics

Track audit scores over time to measure improvement.

### 6. Prioritize CRITICAL

Focus on CRITICAL gaps first (score < 60).

### 7. Learn from GitHub

Study GitHub repos to understand patterns deeply.

### 8. Backup Everything

Teacher Agent creates backups, but keep your own too.

## Support

**Issues:** https://github.com/mikhaileliseev/meAI/issues  
**Docs:** https://github.com/mikhaileliseev/meAI/docs  
**Author:** Mikhail Eliseev (via meAI Architect)

---

**License:** MIT  
**Status:** ✅ Production Ready  
**Version:** 1.0.0  
**Last Updated:** 2026-05-13
