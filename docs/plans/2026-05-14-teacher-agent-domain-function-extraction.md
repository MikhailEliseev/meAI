# Teacher Agent: Domain Function Extraction

**Дата:** 2026-05-14 10:42 GMT+3  
**Статус:** PLANNING  
**Приоритет:** P0 (блокирует Phase 2)

---

## Проблема

SkillSelector извлекает только generic infrastructure patterns (retry, circuit breaker, caching), не domain-specific функции (content extraction, SEO analysis).

**Текущее поведение:**
- Из python-seo-analyzer извлекает: Retry, Circuit Breaker, Rate Limiting
- НЕ извлекает: content extraction, SEO meta analysis, heading analysis

**Ожидаемое поведение:**
- Из python-seo-analyzer извлекает: content extraction, SEO analysis, keyword density
- Из WebAnalyzer извлекает: competitor comparison, gap detection
- Generic patterns (retry, circuit breaker) игнорируются (уже есть в base.py)

---

## Корневая причина

**SkillSelector._detect_patterns()** использует hardcoded infrastructure pattern signatures:

```python
self.pattern_signatures = {
    "Circuit Breaker": ["CircuitBreaker", "circuit_breaker", "fail_max"],
    "Retry with Exponential Backoff": ["retry", "exponential", "backoff"],
    "Rate Limiting": ["rate_limit", "token_bucket", "throttle"],
    "Caching": ["cache", "lru_cache", "memoize"],
}
```

Это НЕ ищет domain-specific функции:
- `extract_content()` - content extraction
- `analyze_meta()` - SEO meta analysis
- `calculate_density()` - keyword density
- `compare_content()` - competitor comparison

---

## Решение

### Подход 1: Domain-Specific Pattern Signatures (РЕКОМЕНДУЕТСЯ)

Добавить domain patterns для каждого субагента:

```python
self.domain_pattern_signatures = {
    "ci-content": {
        "content_extraction": [
            "extract", "parse", "scrape", "trafilatura",
            "beautifulsoup", "html", "text", "article"
        ],
        "seo_analysis": [
            "meta", "title", "description", "keywords",
            "heading", "h1", "h2", "seo", "optimize"
        ],
        "keyword_density": [
            "density", "frequency", "keyword", "count",
            "occurrence", "distribution"
        ],
        "competitor_comparison": [
            "compare", "competitor", "gap", "difference",
            "similarity", "overlap"
        ],
    },
    "ci-tech": {
        "lighthouse_audit": [
            "lighthouse", "performance", "vitals", "audit",
            "lcp", "fid", "cls", "speed"
        ],
        "crawl_analysis": [
            "crawl", "sitemap", "robots", "indexing",
            "spider", "discover"
        ],
    },
    # ... other subagents
}
```

**Обновить _detect_patterns():**
```python
def _detect_patterns(
    self, 
    content: str, 
    subagent_type: str | None = None
) -> dict[str, dict]:
    patterns = {}
    
    # 1. Extract domain-specific patterns (if subagent_type provided)
    if subagent_type and subagent_type in self.domain_pattern_signatures:
        domain_patterns = self.domain_pattern_signatures[subagent_type]
        for pattern_name, signatures in domain_patterns.items():
            if self._has_pattern_from_signatures(content, signatures):
                patterns[f"{subagent_type}_{pattern_name}"] = {
                    "name": f"{subagent_type.title()} - {pattern_name.replace('_', ' ').title()}",
                    "description": self._get_domain_pattern_description(subagent_type, pattern_name),
                    "code": self._extract_pattern_code_from_signatures(content, signatures),
                    "quality_score": self._score_pattern(content, pattern_name),
                }
    
    # 2. Skip generic infrastructure patterns (already in base.py)
    # Don't extract: retry, circuit breaker, caching, rate limiting
    
    return patterns
```

### Подход 2: AST-Based Function Detection (АЛЬТЕРНАТИВА)

Извлекать ВСЕ функции/классы из репо, фильтровать по domain keywords:

```python
def _extract_all_functions(self, file_path: Path) -> list[dict]:
    """Extract all functions/classes from file."""
    content = file_path.read_text()
    tree = ast.parse(content)
    
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append({
                "name": node.name,
                "code": ast.get_source_segment(content, node),
                "docstring": ast.get_docstring(node),
                "is_async": isinstance(node, ast.AsyncFunctionDef),
            })
    
    return functions

def _filter_domain_functions(
    self, 
    functions: list[dict], 
    subagent_type: str
) -> list[dict]:
    """Filter functions by domain relevance."""
    keywords = self.domain_keywords.get(subagent_type, [])
    
    domain_functions = []
    for func in functions:
        text = f"{func['name']} {func['docstring'] or ''} {func['code']}".lower()
        matches = sum(1 for kw in keywords if kw in text)
        
        if matches >= 2:  # At least 2 keyword matches
            domain_functions.append(func)
    
    return domain_functions
```

---

## Рекомендация

**Использовать Подход 1 (Domain-Specific Pattern Signatures):**

**Преимущества:**
- ✅ Контролируемое извлечение (только нужные паттерны)
- ✅ Быстрее (не парсит весь AST)
- ✅ Меньше шума (не извлекает helper функции)
- ✅ Легко расширять (добавить новые паттерны)

**Недостатки:**
- ⚠️ Требует определить паттерны для каждого субагента
- ⚠️ Может пропустить нестандартные решения

**Подход 2 (AST-Based):**
- ✅ Извлекает ВСЁ (не пропустит ничего)
- ❌ Много шума (helper функции, utils)
- ❌ Медленнее (парсит весь AST)
- ❌ Сложнее фильтровать

---

## Implementation Plan (Подход 1)

1. **Добавить domain_pattern_signatures** в SkillSelector.__init__()
   - ci-content: content_extraction, seo_analysis, keyword_density, competitor_comparison
   - ci-tech: lighthouse_audit, crawl_analysis, schema_validation
   - keyword-research: keyword_expansion, volume_analysis, difficulty_scoring
   - seo: backlink_analysis, rank_tracking, serp_analysis
   - content: content_generation, tone_analysis, readability_scoring
   - ads: campaign_optimization, bidding_strategy, conversion_tracking

2. **Обновить _detect_patterns()** для domain-specific extraction
   - Извлекать domain patterns (если subagent_type указан)
   - Пропускать generic infrastructure patterns

3. **Добавить _get_domain_pattern_description()** для описаний паттернов

4. **Обновить _extract_pattern_code_from_signatures()** для поиска по domain keywords

5. **Тестировать** на ci-content субагенте

---

## Expected Result

**До (infrastructure patterns):**
```
Skills extracted from python-seo-analyzer:
- Retry with Exponential Backoff ❌
- Circuit Breaker ❌
- Rate Limiting ❌
- Caching ❌
```

**После (domain patterns):**
```
Skills extracted from python-seo-analyzer:
- CI Content - Content Extraction ✅
- CI Content - SEO Analysis ✅
- CI Content - Keyword Density ✅
- CI Content - Heading Structure ✅
```

---

## Validation

**Success criteria:**
- ✅ CI Content Agent получает content extraction/SEO analysis skills
- ✅ Generic patterns (retry, circuit breaker) НЕ извлекаются
- ✅ Domain-specific functions извлекаются из правильных репо
- ✅ Код применяется к правильному файлу
- ✅ Тесты проходят

**Test case:**
```python
# Из python-seo-analyzer должны извлечься:
skills = [
    "CI Content - Content Extraction",
    "CI Content - SEO Analysis",
    "CI Content - Keyword Density",
]

# НЕ должны извлечься:
not_skills = [
    "Retry with Exponential Backoff",
    "Circuit Breaker",
    "Rate Limiting",
]
```

---

## Estimated Time

- Domain pattern signatures: 30-45 минут (для 6 субагентов)
- Update _detect_patterns(): 20-30 минут
- Helper methods: 15-20 минут
- Testing: 20-30 минут
- **Total:** 1.5-2 часа

---

## Notes

**Почему это важно:**
- Это ЕДИНСТВЕННЫЙ способ получить domain-specific обучение
- Generic patterns уже есть в base.py (не нужно дублировать)
- Каждый субагент должен получить уникальные domain skills

**Альтернатива:**
- Если domain pattern signatures не работают → использовать Подход 2 (AST-Based)
- Но сначала попробовать Подход 1 (проще и быстрее)

---

**Автор:** Claude Sonnet 4  
**Дата:** 2026-05-14 10:42 GMT+3  
**Статус:** READY TO IMPLEMENT (NEXT SESSION)
