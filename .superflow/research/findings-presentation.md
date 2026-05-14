# Research Findings: Teacher Agent Fixes

## Executive Summary

Teacher Agent имеет две критические проблемы, которые блокируют обучение субагентов:

1. **Target File Mapping Problem**: Teacher использует fallback на base.py вместо правильных файлов субагентов
2. **Import Extraction Problem**: Извлечённый код не содержит необходимых Python imports, что вызывает NameError

Обе проблемы имеют чёткие решения и могут быть исправлены в рамках одного спринта.

---

## Problem 1: Target File Mapping

### Current Behavior
```python
# AIM/src/aim/teacher/teacher.py, line ~180
target_file = Path(f"AIM/src/aim/subagents/{subagent_type}/base.py")
```

Teacher Agent всегда использует `base.py` как target file, что неправильно для всех P1 субагентов.

### Root Cause
Отсутствует mapping между subagent_type и реальными файлами субагентов.

### Discovery
Все 10 P1 субагентов **уже существуют** в правильной структуре:

```
AIM/src/aim/subagents/
├── content/
│   ├── content_brief_generator.py      ✅ EXISTS
│   ├── content_calendar_manager.py     ✅ EXISTS
│   └── content_quality_checker.py      ✅ EXISTS
├── ads/
│   ├── ad_copy_generator.py            ✅ EXISTS
│   ├── bid_strategy_optimizer.py       ✅ EXISTS
│   └── landing_page_analyzer.py        ✅ EXISTS
├── seo/
│   └── schema_generator.py             ✅ EXISTS
└── analytics/
    ├── traffic_analyzer.py             ✅ EXISTS
    ├── conversion_tracker.py           ✅ EXISTS
    └── report_generator.py             ✅ EXISTS
```

### Proposed Solution

Добавить `subagent_target_files` mapping в `SkillTeacher`:

```python
# AIM/src/aim/teacher/teacher.py
SUBAGENT_TARGET_FILES = {
    "content-brief": "AIM/src/aim/subagents/content/content_brief_generator.py",
    "ad-copy": "AIM/src/aim/subagents/ads/ad_copy_generator.py",
    "traffic-analyzer": "AIM/src/aim/subagents/analytics/traffic_analyzer.py",
    "conversion-tracker": "AIM/src/aim/subagents/analytics/conversion_tracker.py",
    "schema-generator": "AIM/src/aim/subagents/seo/schema_generator.py",
    "quality-checker": "AIM/src/aim/subagents/content/content_quality_checker.py",
    "landing-page": "AIM/src/aim/subagents/ads/landing_page_analyzer.py",
    "bid-optimizer": "AIM/src/aim/subagents/ads/bid_strategy_optimizer.py",
    "report-generator": "AIM/src/aim/subagents/analytics/report_generator.py",
    "calendar-manager": "AIM/src/aim/subagents/content/content_calendar_manager.py",
}

async def teach_subagent(self, subagent_name: str, domain: str):
    # Get correct target file
    target_file = Path(SUBAGENT_TARGET_FILES.get(
        subagent_name,
        f"AIM/src/aim/subagents/{subagent_name}/base.py"  # fallback
    ))
```

### Impact
- ✅ Teacher будет применять код в правильные файлы
- ✅ Тесты будут проходить (правильные imports уже есть в target files)
- ✅ Код будет в правильном месте для использования

---

## Problem 2: Import Extraction

### Current Behavior
```python
# Test failure example
NameError: name 'ChatOpenAI' is not defined
```

Извлечённый код использует `ChatOpenAI`, но import не добавлен в файл.

### Root Cause

`SkillExtractor._extract_dependencies()` извлекает только pip packages:

```python
# AIM/src/aim/teacher/skills/skill_extractor.py, line ~80
def _extract_dependencies(self, code: str) -> list[str]:
    """Extract pip package dependencies from code."""
    dependencies = set()
    
    # Extract from import statements
    for line in code.split('\n'):
        if line.strip().startswith(('import ', 'from ')):
            # Extract package name
            if 'import ' in line:
                pkg = line.split('import ')[1].split()[0].split('.')[0]
                dependencies.add(pkg)
    
    return list(dependencies)
```

Возвращает: `["openai", "anthropic"]` (pip packages)  
Не возвращает: `from openai import ChatOpenAI` (Python imports)

### Discovery

Нужно извлекать **два типа зависимостей**:

1. **Pip packages** (для requirements.txt) — уже работает
2. **Python imports** (для вставки в код) — отсутствует

### Proposed Solution

#### Step 1: Add Python Import Extraction

```python
# AIM/src/aim/teacher/skills/skill_extractor.py

import ast
from typing import NamedTuple

class ExtractedImports(NamedTuple):
    """Extracted import statements."""
    statements: list[str]  # Full import lines
    packages: set[str]     # Pip package names

def _extract_python_imports(self, code: str) -> ExtractedImports:
    """
    Extract Python import statements using AST parsing.
    
    Returns:
        ExtractedImports with:
        - statements: ["from openai import ChatOpenAI", "import httpx"]
        - packages: {"openai", "httpx"}
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return ExtractedImports(statements=[], packages=set())
    
    statements = []
    packages = set()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            # import httpx, asyncio
            for alias in node.names:
                statements.append(f"import {alias.name}")
                packages.add(alias.name.split('.')[0])
                
        elif isinstance(node, ast.ImportFrom):
            # from openai import ChatOpenAI
            module = node.module or ""
            names = [alias.name for alias in node.names]
            statements.append(f"from {module} import {', '.join(names)}")
            if module:
                packages.add(module.split('.')[0])
    
    return ExtractedImports(
        statements=list(set(statements)),  # deduplicate
        packages=packages
    )
```

#### Step 2: Update ExtractedImplementation

```python
# AIM/src/aim/teacher/skills/skill_extractor.py

@dataclass
class ExtractedImplementation:
    """Extracted implementation from skill."""
    code: str
    dependencies: list[str]  # pip packages
    python_imports: list[str]  # NEW: Python import statements
    target_function: str | None = None
    target_class: str | None = None
```

#### Step 3: Update SkillApplier to Merge Imports

```python
# AIM/src/aim/teacher/skills/skill_applier.py

def _merge_imports(
    self,
    existing_code: str,
    new_imports: list[str]
) -> str:
    """
    Merge new imports into existing code.
    
    Strategy:
    1. Parse existing imports
    2. Deduplicate with new imports
    3. Insert after existing imports (preserve order)
    """
    try:
        tree = ast.parse(existing_code)
    except SyntaxError:
        # Fallback: insert at top
        return "\n".join(new_imports) + "\n\n" + existing_code
    
    # Find last import line number
    last_import_line = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            last_import_line = max(last_import_line, node.lineno)
    
    # Parse existing imports
    existing_imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                existing_imports.add(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names = [alias.name for alias in node.names]
            existing_imports.add(f"from {module} import {', '.join(names)}")
    
    # Filter out duplicates
    unique_new_imports = [
        imp for imp in new_imports
        if imp not in existing_imports
    ]
    
    if not unique_new_imports:
        return existing_code  # No new imports needed
    
    # Insert after last import
    lines = existing_code.split('\n')
    lines.insert(last_import_line, '\n'.join(unique_new_imports))
    
    return '\n'.join(lines)

async def apply_skill(
    self,
    skill: Skill,
    target_file: Path,
    target_context: TargetContext
) -> ApplyResult:
    # ... existing code ...
    
    # Extract implementation
    extracted = await self.extractor.extract_implementation(
        skill=skill,
        target_context=target_context
    )
    
    # Read existing code
    existing_code = target_file.read_text()
    
    # Merge imports FIRST
    code_with_imports = self._merge_imports(
        existing_code=existing_code,
        new_imports=extracted.python_imports
    )
    
    # Then apply code changes
    modified_code = self._apply_code_changes(
        code=code_with_imports,
        extracted=extracted,
        target_context=target_context
    )
    
    # Write back
    target_file.write_text(modified_code)
```

### Impact
- ✅ Извлечённый код будет содержать все необходимые imports
- ✅ Тесты будут проходить (нет NameError)
- ✅ Код будет работать сразу после применения

---

## Implementation Plan

### Sprint Breakdown

**Sprint 1: Target File Mapping** (2-3 hours)
1. Add `SUBAGENT_TARGET_FILES` mapping to `SkillTeacher`
2. Update `teach_subagent()` to use mapping
3. Add tests for correct file selection
4. Validate with 1 subagent (content-brief)

**Sprint 2: Import Extraction** (4-6 hours)
1. Add `_extract_python_imports()` to `SkillExtractor`
2. Update `ExtractedImplementation` dataclass
3. Add `_merge_imports()` to `SkillApplier`
4. Update `apply_skill()` to merge imports
5. Add tests for import extraction and merging
6. Validate with 1 subagent (content-brief)

**Sprint 3: Full Validation** (2-3 hours)
1. Run Teacher Agent on all 10 P1 subagents
2. Verify all tests pass
3. Check code quality (imports, structure)
4. Document changes

### Total Effort
- **Development**: 8-12 hours
- **Testing**: 2-3 hours
- **Total**: 10-15 hours (1-2 days)

### Risk Assessment
- **Low Risk**: Все изменения локальные, не затрагивают core logic
- **High Impact**: Разблокирует обучение всех 10 P1 субагентов
- **Easy Rollback**: Можно откатить через git revert

---

## Success Criteria

### Must Have
- ✅ Teacher Agent применяет код в правильные файлы (не base.py)
- ✅ Извлечённый код содержит все необходимые imports
- ✅ Все тесты проходят после применения кода
- ✅ Нет NameError или ImportError

### Nice to Have
- ✅ Import deduplication (не дублировать существующие imports)
- ✅ Import ordering (stdlib → third-party → local)
- ✅ Graceful fallback (если AST parsing fails)

---

## Questions for User

1. **Приоритет**: Начать с Target File Mapping или Import Extraction?
   - Рекомендация: Target File Mapping (проще, быстрее, разблокирует тестирование)

2. **Scope**: Исправить только эти 2 проблемы или добавить дополнительные улучшения?
   - Рекомендация: Только эти 2 проблемы (фокус на качестве)

3. **Testing**: Тестировать на 1 субагенте или сразу на всех 10?
   - Рекомендация: Сначала 1 (content-brief), потом все 10

---

## Next Steps

После approval:
1. Brainstorming (expert panel для implementation approach)
2. Product Approval (презентация brief пользователю)
3. Specification (technical spec с dual-model review)
4. Planning (implementation plan с sprint breakdown)
5. Execution (Phase 2 - autonomous implementation)
