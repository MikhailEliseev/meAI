# Teacher Agent - Анализ проблем и план исправления

**Дата:** 2026-05-14  
**Статус:** КРИТИЧЕСКИЕ ПРОБЛЕМЫ ОБНАРУЖЕНЫ

---

## Проблемы в текущей реализации

### Проблема 1: SkillSelector не клонирует репозитории

**Текущий код:**
```python
async def search_github_repos(self, query: str, max_results: int = 10) -> list[GitHubRepo]:
    # Только поиск через GitHub API
    # Возвращает список GitHubRepo с URL, stars, description
    # НО НЕ КЛОНИРУЕТ!
```

**Что не так:**
- ❌ Метод `clone_repo()` существует, но НИКОГДА не вызывается
- ❌ `extract_skills()` принимает `repo_path`, но откуда взять path если не клонировали?
- ❌ Workflow: search → extract, но между ними нет клонирования!

**Последствия:**
- Невозможно извлечь skills из репозитория
- `extract_skills()` никогда не сработает
- Вся система Teacher Agent сломана

### Проблема 2: SkillExtractor не разбирает до молекул

**Текущий код:**
```python
async def extract(self, skill: Skill, target_path: Path | None = None) -> ExtractedImplementation:
    # Берёт skill.code_example (500 символов из SkillSelector)
    # Извлекает dependencies через ast.parse
    # Генерирует instructions
    # НО НЕ РАЗБИРАЕТ ДО МОЛЕКУЛ!
```

**Что не так:**
- ❌ Работает только с 500 символами кода (из `_extract_pattern_code`)
- ❌ Не читает полный файл из репозитория
- ❌ Не извлекает параметры (fail_max, reset_timeout)
- ❌ Не извлекает edge cases
- ❌ Не извлекает тесты
- ❌ Не извлекает метрики

**Последствия:**
- Поверхностная интеграция (как в GITHUB_INTEGRATION_DEEP_ANALYSIS.md)
- Нет деталей для правильного внедрения
- "Use circuit breaker" вместо "fail_max=5, reset_timeout=60s"

### Проблема 3: Нет orchestrator для полного workflow

**Отсутствует:**
```python
class SkillTeacher:
    async def teach_subagent(self, subagent_name: str):
        # 1. Research domain-specific (SkillSelector)
        # 2. Clone ALL repos
        # 3. Extract skills from ALL repos
        # 4. Compare skills (SkillComparator)
        # 5. Extract best implementation (SkillExtractor)
        # 6. APPLY to codebase (missing!)
        # 7. TEST (missing!)
        # 8. COMMIT (missing!)
```

**Что не так:**
- ❌ Нет полного workflow от research до commit
- ❌ Нет применения кода в проект
- ❌ Нет тестирования
- ❌ Нет коммита

**Последствия:**
- Невозможно обучить субагента end-to-end
- Работа останавливается на "нашли паттерны"
- Нет внедрения в код

### Проблема 4: Domain-specific patterns не используются

**Текущий код:**
```python
self.domain_pattern_signatures = {
    "ads": {
        "mcp_server": [...],
        "api_client": [...],
        "oauth": [...],
    },
    "seo": {...},
    # ... 60+ domain-specific patterns
}
```

**Что не так:**
- ✅ Паттерны определены (хорошо!)
- ❌ Но используются только в `_detect_patterns()`
- ❌ Нет специализированной обработки для каждого домена
- ❌ Нет приоритизации domain-specific над generic

**Последствия:**
- Domain-specific паттерны теряются среди generic
- Ads субагент не получает MCP-specific знания
- SEO субагент не получает DataFrame-first паттерны

---

## План исправления

### Этап 1: Исправить SkillSelector (клонирование)

**Добавить метод:**
```python
async def research_and_clone(
    self, 
    subagent_name: str, 
    domain: str
) -> dict[str, Path]:
    """
    Research domain-specific solutions AND clone ALL repos.
    
    Returns:
        Dict mapping repo URL to local path
    """
    # 1. Search GitHub (existing)
    results = await self.research_domain_specific(subagent_name, domain)
    
    # 2. Clone ALL repos
    cloned_repos = {}
    for query, repos in results.items():
        for repo in repos:
            clone_path = Path(f"~/temp/research-repos/{repo.url.split('/')[-1]}")
            await self.clone_repo(repo.url, clone_path)
            cloned_repos[repo.url] = clone_path
    
    return cloned_repos
```

### Этап 2: Улучшить SkillExtractor (разбор до молекул)

**Добавить метод:**
```python
async def extract_deep(
    self, 
    repo_path: Path, 
    pattern_name: str,
    subagent_type: str
) -> DeepExtraction:
    """
    Deep extraction: parameters, edge cases, tests, metrics.
    
    Returns:
        DeepExtraction with all details
    """
    # 1. Find pattern file
    pattern_file = self._find_pattern_file(repo_path, pattern_name)
    
    # 2. Extract parameters
    parameters = self._extract_parameters(pattern_file)
    
    # 3. Extract edge cases
    edge_cases = self._extract_edge_cases(pattern_file)
    
    # 4. Find and extract tests
    test_file = self._find_test_file(repo_path, pattern_name)
    tests = self._extract_tests(test_file)
    
    # 5. Extract metrics
    metrics = self._extract_metrics(pattern_file)
    
    return DeepExtraction(
        code=pattern_file.read_text(),
        parameters=parameters,
        edge_cases=edge_cases,
        tests=tests,
        metrics=metrics,
    )
```

### Этап 3: Создать SkillTeacher (orchestrator)

**Новый файл:** `AIM/src/aim/teacher/skills/skill_teacher.py`

```python
class SkillTeacher:
    """
    Orchestrates full teaching workflow:
    1. Research domain-specific
    2. Clone ALL repos
    3. Extract skills from ALL repos
    4. Compare and rank
    5. Extract best implementation (deep)
    6. Apply to codebase
    7. Test
    8. Commit
    """
    
    async def teach_subagent(
        self, 
        subagent_name: str,
        domain: str
    ) -> TeachingReport:
        # Full workflow implementation
        pass
```

### Этап 4: Добавить применение кода (SkillApplier)

**Новый файл:** `AIM/src/aim/teacher/skills/skill_applier.py`

```python
class SkillApplier:
    """
    Applies extracted skills to codebase:
    1. Create/update files
    2. Add dependencies to requirements.txt
    3. Adapt code to project structure
    4. Generate tests
    """
    
    async def apply(
        self, 
        extraction: DeepExtraction,
        target_path: Path
    ) -> ApplicationResult:
        # Apply implementation
        pass
```

---

## Приоритеты

### P0 (Критично - сделать сейчас)
1. ✅ Исправить SkillSelector: добавить `research_and_clone()`
2. ✅ Создать SkillTeacher orchestrator
3. ✅ Добавить SkillApplier для применения кода

### P1 (Важно - сделать после P0)
4. Улучшить SkillExtractor: добавить `extract_deep()`
5. Добавить тестирование в workflow
6. Добавить коммит в workflow

### P2 (Желательно - сделать после P1)
7. Улучшить domain-specific обработку
8. Добавить метрики успеха
9. Добавить rollback при ошибках

---

## Следующие шаги

1. **Сейчас:** Исправить SkillSelector (добавить клонирование)
2. **Потом:** Создать SkillTeacher (orchestrator)
3. **Затем:** Добавить SkillApplier (применение кода)
4. **Наконец:** Протестировать на Ads субагенте

---

**Статус:** ГОТОВ К ИСПРАВЛЕНИЮ  
**Оценка времени:** 2-3 часа  
**Приоритет:** P0 (КРИТИЧНО)
