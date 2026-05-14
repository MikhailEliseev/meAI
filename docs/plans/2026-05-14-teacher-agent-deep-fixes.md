# Teacher Agent Deep Fixes Plan

**Дата:** 2026-05-14 09:22 GMT+3  
**Статус:** КРИТИЧНО  
**Приоритет:** P0

---

## Проблема (обнаружена после Phase 1)

Teacher Agent работает end-to-end, но применяет **НЕПРАВИЛЬНЫЙ КОД**:

**Что произошло:**
- ✅ Нашёл 17 репозиториев (SEMrush, Ahrefs, keyword research tools)
- ✅ Клонировал 16 репозиториев
- ✅ Извлёк 11 skills
- ✅ Выбрал "лучший" skill: "Retry with Exponential Backoff" (90.0 score)
- ❌ **Применил НЕПРАВИЛЬНЫЙ код** - CLI функцию с `sys.exit()` вместо async retry pattern
- ❌ Код не подходит для async API client (наш base.py - async класс)
- ❌ Код содержит `urllib` вместо `httpx`
- ❌ Код содержит `sys.exit()` - убивает процесс вместо raise exception

**Корневая проблема:**
Teacher Agent не понимает **КОНТЕКСТ** применения:
- Куда применяется код (async class vs sync function)
- Какие библиотеки используются (httpx vs urllib)
- Какой стиль обработки ошибок (raise vs sys.exit)

---

## Анализ: Почему это произошло?

### 1. SkillSelector - неправильная оценка skills

**Текущая логика:**
```python
# skill_selector.py, lines 484-540
def _extract_pattern_code(self, content: str, pattern_name: str) -> str:
    # Извлекает код по сигнатуре паттерна
    # НО: не проверяет контекст (async vs sync, httpx vs urllib)
```

**Проблема:**
- Ищет паттерн "retry" по ключевым словам
- Находит любой код с "retry" в названии
- Не проверяет совместимость с целевым кодом

### 2. SkillComparator - поверхностное сравнение

**Текущая логика:**
```python
# skill_comparator.py
def _calculate_quality_score(self, skill: Skill) -> float:
    score = 0.0
    
    # Complexity (30%)
    if skill.complexity == "high": score += 30
    
    # Completeness (40%)
    if skill.has_tests: score += 20
    if skill.has_docs: score += 20
    
    # Relevance (30%)
    if skill.domain_specific: score += 30
```

**Проблема:**
- Оценивает "сложность" и "полноту", но не **совместимость**
- Не проверяет: async vs sync, библиотеки, стиль кода
- Высокий score не означает "подходит для нашего кода"

### 3. SkillApplier - слепое применение

**Текущая логика:**
```python
# skill_applier.py, lines 140-180
async def _apply_code(self, code: str, target_path: Path, ...):
    # Просто добавляет код в файл
    # НЕ проверяет совместимость
    # НЕ адаптирует под целевой контекст
```

**Проблема:**
- Append код "как есть"
- Не проверяет async/sync compatibility
- Не адаптирует библиотеки (urllib → httpx)
- Не адаптирует error handling (sys.exit → raise)

---

## Решение: Context-Aware Teaching

### Принцип: "Понимай куда применяешь"

**Новый workflow:**

```
1. Analyze Target Context
   ├─ Read target file (base.py)
   ├─ Detect: async/sync, libraries, error handling style
   └─ Create "Target Profile"

2. Extract Skills with Context
   ├─ Find skills matching target profile
   ├─ Filter incompatible skills
   └─ Rank by compatibility + quality

3. Adapt Code to Target
   ├─ Convert sync → async (if needed)
   ├─ Replace libraries (urllib → httpx)
   ├─ Adapt error handling (sys.exit → raise)
   └─ Preserve pattern logic

4. Validate Before Apply
   ├─ Check imports compatibility
   ├─ Check async/sync compatibility
   ├─ Check error handling compatibility
   └─ ONLY apply if compatible
```

---

## Исправления (приоритизированные)

### Fix 1: Target Context Analysis (КРИТИЧНО)

**Файл:** `AIM/src/aim/teacher/skills/skill_applier.py`

**Добавить:**
```python
@dataclass
class TargetContext:
    """Context of target file where code will be applied."""
    is_async: bool
    libraries: set[str]  # httpx, aiohttp, requests, urllib
    error_style: str  # "raise" or "exit" or "return"
    base_classes: list[str]  # ABC, BaseModel, etc.
    imports: set[str]  # existing imports

async def _analyze_target_context(self, target_path: Path) -> TargetContext:
    """Analyze target file to understand context."""
    if not target_path.exists():
        return TargetContext(
            is_async=False,
            libraries=set(),
            error_style="raise",
            base_classes=[],
            imports=set()
        )
    
    content = target_path.read_text()
    
    # Detect async
    is_async = "async def" in content or "await " in content
    
    # Detect libraries
    libraries = set()
    if "import httpx" in content: libraries.add("httpx")
    if "import aiohttp" in content: libraries.add("aiohttp")
    if "import requests" in content: libraries.add("requests")
    if "import urllib" in content: libraries.add("urllib")
    
    # Detect error style
    error_style = "raise"
    if "sys.exit(" in content: error_style = "exit"
    if "return None" in content and "raise" not in content: error_style = "return"
    
    # Detect base classes
    base_classes = []
    for match in re.finditer(r"class \w+\(([^)]+)\)", content):
        base_classes.extend(m.strip() for m in match.group(1).split(","))
    
    # Detect imports
    imports = set()
    for match in re.finditer(r"^(?:from|import)\s+(\S+)", content, re.MULTILINE):
        imports.add(match.group(1))
    
    return TargetContext(
        is_async=is_async,
        libraries=libraries,
        error_style=error_style,
        base_classes=base_classes,
        imports=imports
    )
```

### Fix 2: Context-Aware Skill Filtering (КРИТИЧНО)

**Файл:** `AIM/src/aim/teacher/skills/skill_comparator.py`

**Добавить:**
```python
def _check_compatibility(
    self,
    skill: Skill,
    target_context: TargetContext
) -> tuple[bool, str]:
    """Check if skill is compatible with target context."""
    
    # Check async/sync compatibility
    skill_is_async = "async def" in skill.code or "await " in skill.code
    if target_context.is_async and not skill_is_async:
        return False, "Target is async, skill is sync"
    
    # Check library compatibility
    skill_libraries = set()
    if "httpx" in skill.code: skill_libraries.add("httpx")
    if "aiohttp" in skill.code: skill_libraries.add("aiohttp")
    if "requests" in skill.code: skill_libraries.add("requests")
    if "urllib" in skill.code: skill_libraries.add("urllib")
    
    if skill_libraries and not skill_libraries.intersection(target_context.libraries):
        return False, f"Library mismatch: skill uses {skill_libraries}, target uses {target_context.libraries}"
    
    # Check error handling compatibility
    if "sys.exit(" in skill.code and target_context.error_style == "raise":
        return False, "Skill uses sys.exit(), target uses raise"
    
    return True, "Compatible"

async def compare_with_context(
    self,
    skills: list[Skill],
    target_context: TargetContext
) -> SkillComparison:
    """Compare skills considering target context."""
    
    # Filter compatible skills
    compatible_skills = []
    for skill in skills:
        is_compatible, reason = self._check_compatibility(skill, target_context)
        if is_compatible:
            compatible_skills.append(skill)
        else:
            self.logger.info(
                "skill_filtered_incompatible",
                skill=skill.name,
                reason=reason
            )
    
    if not compatible_skills:
        self.logger.warning("no_compatible_skills")
        return SkillComparison(
            best_skill=None,
            all_skills=skills,
            comparison_notes="No compatible skills found"
        )
    
    # Compare only compatible skills
    return await self.compare(compatible_skills)
```

### Fix 3: Code Adaptation (ВАЖНО)

**Файл:** `AIM/src/aim/teacher/skills/skill_applier.py`

**Добавить:**
```python
def _adapt_to_context(
    self,
    code: str,
    target_context: TargetContext
) -> str:
    """Adapt code to match target context."""
    
    adapted = code
    
    # Adapt async/sync
    if target_context.is_async and "async def" not in code:
        # Convert sync to async
        adapted = adapted.replace("def ", "async def ")
        # Add await to blocking calls
        adapted = re.sub(
            r"(\w+)\.(get|post|put|delete)\(",
            r"await \1.\2(",
            adapted
        )
    
    # Adapt libraries
    if "urllib" in code and "httpx" in target_context.libraries:
        # Replace urllib with httpx
        adapted = adapted.replace("urllib.request.urlopen", "httpx.AsyncClient().get")
        adapted = adapted.replace("urllib.request.Request", "httpx.Request")
    
    # Adapt error handling
    if "sys.exit(" in code and target_context.error_style == "raise":
        # Replace sys.exit with raise
        adapted = re.sub(
            r"sys\.exit\((\d+)\)",
            r"raise RuntimeError(f'Error code: \1')",
            adapted
        )
    
    return adapted
```

### Fix 4: Validation Before Apply (ВАЖНО)

**Файл:** `AIM/src/aim/teacher/skills/skill_applier.py`

**Добавить:**
```python
async def apply_with_validation(
    self,
    implementation: ExtractedImplementation,
    target_path: Path | None = None,
    subagent_name: str | None = None,
) -> ApplicationResult:
    """Apply with context validation."""
    
    # Step 1: Analyze target context
    final_path = target_path or implementation.suggested_path
    target_context = await self._analyze_target_context(final_path)
    
    # Step 2: Check compatibility
    is_compatible, reason = self._check_code_compatibility(
        implementation.code,
        target_context
    )
    
    if not is_compatible:
        self.logger.error(
            "code_incompatible",
            reason=reason,
            target=str(final_path)
        )
        return ApplicationResult(
            success=False,
            error=f"Code incompatible: {reason}"
        )
    
    # Step 3: Adapt code
    adapted_code = self._adapt_to_context(
        implementation.code,
        target_context
    )
    
    # Step 4: Apply adapted code
    return await self.apply(
        ExtractedImplementation(
            code=adapted_code,
            dependencies=implementation.dependencies,
            suggested_path=implementation.suggested_path,
            tests=implementation.tests,
            documentation=implementation.documentation
        ),
        target_path=target_path,
        subagent_name=subagent_name
    )
```

---

## План выполнения

### Этап 1: Откатить неправильный код (5 минут)

```bash
# Откатить последний teaching commit
git revert 0a9466c --no-edit

# Проверить что base.py вернулся в исходное состояние
git diff HEAD~1 AIM/src/aim/subagents/api_clients/base.py
```

### Этап 2: Реализовать Fix 1 - Target Context Analysis (30 минут)

1. Добавить `TargetContext` dataclass
2. Реализовать `_analyze_target_context()`
3. Добавить тесты для context analysis

### Этап 3: Реализовать Fix 2 - Context-Aware Filtering (30 минут)

1. Добавить `_check_compatibility()`
2. Реализовать `compare_with_context()`
3. Обновить `SkillTeacher.teach_subagent()` для использования context

### Этап 4: Реализовать Fix 3 - Code Adaptation (45 минут)

1. Реализовать `_adapt_to_context()`
2. Добавить адаптацию async/sync
3. Добавить адаптацию библиотек
4. Добавить адаптацию error handling

### Этап 5: Реализовать Fix 4 - Validation (30 минут)

1. Реализовать `apply_with_validation()`
2. Обновить `SkillTeacher` для использования validation
3. Добавить тесты

### Этап 6: Повторить teaching на keyword-research (15 минут)

```python
teacher = SkillTeacher(project_root=aim_root)
report = await teacher.teach_subagent(
    subagent_name="keyword-research",
    domain="keyword research automation python"
)
```

**Ожидаемый результат:**
- ✅ Найдены async-compatible skills
- ✅ Отфильтрованы sync/CLI skills
- ✅ Применён правильный async retry pattern
- ✅ Код адаптирован под httpx
- ✅ Error handling адаптирован под raise

---

## Время выполнения

**Оптимистичный:** 2.5 часа  
**Реалистичный:** 3-4 часа  
**Пессимистичный:** 5-6 часов

---

## Критерий успеха

**Phase 1 (исправленная):**
- ✅ Teacher Agent применяет ПРАВИЛЬНЫЙ код
- ✅ Код совместим с target context (async, httpx, raise)
- ✅ Код адаптирован под наш стиль
- ✅ Тесты проходят
- ✅ Можно переходить к Phase 2 (обучение всех субагентов)

---

**Автор:** Claude Sonnet 4  
**Дата:** 2026-05-14 09:22 GMT+3  
**Статус:** READY TO EXECUTE
