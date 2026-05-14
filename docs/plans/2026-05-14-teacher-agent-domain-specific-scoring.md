# Teacher Agent: Domain-Specific Scoring

**Дата:** 2026-05-14 10:37 GMT+3  
**Статус:** PLANNING  
**Приоритет:** P0 (блокирует Phase 2)

---

## Проблема

Teacher Agent выбирает generic patterns (Retry, Circuit Breaker) вместо domain-specific решений для субагентов.

**Пример:**
- CI Content Agent должен получить: content extraction, SEO analysis, competitor comparison
- CI Content Agent получает: Retry with Exponential Backoff (generic pattern)
- Это нарушает правило: "Каждый субагент получает уникальное обучение"

**Корневая причина:**
- SkillComparator оценивает skills по generic критериям (completeness, best practices, documentation)
- Не учитывает domain relevance для конкретного субагента
- Generic patterns получают высокий score (75-100) из-за хорошего кода
- Domain-specific patterns получают низкий score из-за простоты

---

## Решение

### 1. Domain-Specific Scoring в SkillComparator

**Добавить:**
```python
def _score_domain_relevance(
    self, 
    skill: Skill, 
    subagent_name: str
) -> float:
    """
    Score domain relevance for subagent.
    
    Returns:
        0-100 score (higher = more relevant)
    """
    # Domain keywords mapping
    domain_keywords = {
        "ci-content": [
            "content", "extraction", "scraping", "parsing",
            "seo", "meta", "heading", "keyword", "density",
            "competitor", "comparison", "gap", "analysis",
            "trafilatura", "beautifulsoup", "html", "text"
        ],
        "ci-tech": [
            "lighthouse", "performance", "vitals", "speed",
            "technical", "crawl", "sitemap", "robots",
            "schema", "structured", "data"
        ],
        # ... other subagents
    }
    
    keywords = domain_keywords.get(subagent_name, [])
    
    # Count keyword matches in skill name + description + code
    text = f"{skill.name} {skill.description} {skill.code_example}".lower()
    matches = sum(1 for kw in keywords if kw in text)
    
    # Score: 0-100 based on matches
    max_matches = len(keywords)
    score = (matches / max_matches) * 100 if max_matches > 0 else 0
    
    return score
```

**Обновить compare_with_context():**
```python
async def compare_with_context(
    self, 
    skills: list[Skill], 
    target_context: TargetContext
) -> SkillComparison:
    # ... existing filtering ...
    
    # Score each compatible skill
    for skill in compatible_skills:
        # Generic quality score (0-100)
        quality_score = self._score_skill(skill)
        
        # Domain relevance score (0-100)
        domain_score = self._score_domain_relevance(
            skill, 
            target_context.subagent_name  # NEW: pass subagent name
        )
        
        # Combined score: 70% domain + 30% quality
        # Domain relevance is MORE important than code quality
        combined_score = (domain_score * 0.7) + (quality_score * 0.3)
        
        skill.quality_score = combined_score
    
    # Sort by combined score
    ranked = sorted(compatible_skills, key=lambda s: s.quality_score, reverse=True)
    
    return SkillComparison(
        best_skill=ranked[0] if ranked else None,
        ranked_skills=ranked,
        filtered_skills=filtered_skills,
    )
```

### 2. Передать subagent_name в TargetContext

**Обновить TargetContext:**
```python
@dataclass
class TargetContext:
    is_async: bool
    libraries: set[str]
    error_style: str  # "raise", "return", "exit"
    base_classes: list[str]
    imports: list[str]
    subagent_name: str  # NEW: для domain scoring
```

**Обновить SkillTeacher.teach_subagent():**
```python
# Step 3: Analyze target context (with subagent name)
target_context = await self.applier._analyze_target_context(
    target_path,
    subagent_name=subagent_name  # NEW: pass subagent name
)

# Step 4: Compare with domain-aware scoring
comparison = await self.comparator.compare_with_context(
    all_skills, 
    target_context  # Contains subagent_name
)
```

### 3. Обновить SkillApplier._analyze_target_context()

```python
async def _analyze_target_context(
    self, 
    target_path: Path,
    subagent_name: str  # NEW parameter
) -> TargetContext:
    # ... existing analysis ...
    
    return TargetContext(
        is_async=is_async,
        libraries=libraries,
        error_style=error_style,
        base_classes=base_classes,
        imports=imports,
        subagent_name=subagent_name,  # NEW field
    )
```

---

## Ожидаемый результат

**До (generic scoring):**
```
Skills ranked:
1. Retry with Exponential Backoff (score: 75.0) ❌ generic
2. Circuit Breaker (score: 70.0) ❌ generic
3. Content Extraction with Trafilatura (score: 45.0) ✅ domain-specific
```

**После (domain-specific scoring):**
```
Skills ranked:
1. Content Extraction with Trafilatura (score: 85.0) ✅ domain-specific
   - Domain score: 90.0 (high keyword match)
   - Quality score: 45.0 (simple code)
   - Combined: 90*0.7 + 45*0.3 = 76.5
2. SEO Meta Analysis (score: 75.0) ✅ domain-specific
3. Retry with Exponential Backoff (score: 52.5) ❌ generic
   - Domain score: 10.0 (low keyword match)
   - Quality score: 75.0 (good code)
   - Combined: 10*0.7 + 75*0.3 = 29.5
```

---

## Implementation Plan

1. **Обновить TargetContext** (добавить subagent_name field)
2. **Обновить SkillApplier._analyze_target_context()** (принимать subagent_name)
3. **Обновить SkillTeacher.teach_subagent()** (передавать subagent_name)
4. **Добавить domain keywords mapping** в SkillComparator
5. **Реализовать _score_domain_relevance()** в SkillComparator
6. **Обновить compare_with_context()** (combined scoring: 70% domain + 30% quality)
7. **Тестировать** на ci-content субагенте

---

## Validation

**Success criteria:**
- ✅ CI Content Agent получает content extraction/SEO analysis skills
- ✅ Generic patterns (retry, circuit breaker) имеют низкий score
- ✅ Domain-specific patterns имеют высокий score
- ✅ Код применяется к правильному файлу
- ✅ Тесты проходят

**Test case:**
```python
# CI Content Agent должен получить:
best_skill.name in [
    "Content Extraction with Trafilatura",
    "SEO Meta Analysis",
    "Competitor Content Comparison",
    "AI Content Detection"
]

# НЕ должен получить:
best_skill.name not in [
    "Retry with Exponential Backoff",
    "Circuit Breaker",
    "Rate Limiting",
    "Caching"
]
```

---

## Estimated Time

- Implementation: 30-45 минут
- Testing: 15-20 минут
- **Total:** 45-65 минут

---

**Автор:** Claude Sonnet 4  
**Дата:** 2026-05-14 10:37 GMT+3  
**Статус:** READY TO IMPLEMENT
