---
title: "CI System: URL Validation and Data Flow Problem"
decision_id: "ci-url-validation-2026-05-05"
timestamp: "2026-05-05T16:42:00"
confidence: 0.92
status: problem_identified
tags: [problem, ci-system, data-flow, url-validation]
---

# Problem: CI System URL Validation and Data Flow

## Context

User provided competitor pool for cosmetology project:
1. Tori Clinic - toriclinic.ru ✅
2. Professional Clinic - profclinic.ru ✅
3. CIDK - cidk.ru ✅
4. Frau Clinic - frauklinik.ru ✅
5. Клиника Юлии Щербатовой - doctor-shcherbatova.ru ❌

**What happened:**
- CI Deep Analyzer started analysis immediately without URL validation
- 5th competitor failed (wrong URL: doctor-shcherbatova.ru)
- Correct URL: juliasherbatova.ru
- System returned 0% quality without asking user

## Problems Identified

### Problem 1: No URL Validation Before Analysis

**Current behavior:**
```python
# CI Deep Analyzer
async def execute_task(self, task: Task):
    competitors = task.payload["competitors"]
    
    # Сразу начинает анализ без проверки
    for comp in competitors:
        await self._analyze_competitor(comp["url"])
```

**What should happen:**
```python
# CI Deep Analyzer
async def execute_task(self, task: Task):
    competitors = task.payload["competitors"]
    
    # 1. Проверить доступность URL
    validated = await self._validate_urls(competitors)
    
    # 2. Если есть проблемы → спросить пользователя
    if validated["failed"]:
        await self.ask_user(
            f"Не удалось подключиться к {len(validated['failed'])} конкурентам:\n"
            f"{validated['failed']}\n"
            f"Проверьте URL или пропустите этих конкурентов?"
        )
    
    # 3. Продолжить с валидными URL
    for comp in validated["success"]:
        await self._analyze_competitor(comp["url"])
```

### Problem 2: CI Scout Doesn't Validate URLs

**Current behavior:**
```python
# CI Scout Agent (ci_scout.py:268)
profile = {
    "name": name,
    "url": f"https://{self._slugify(name)}.ru",  # Генерирует URL автоматически
    ...
}
```

**Problem:**
- CI Scout генерирует URL автоматически через slugify
- Не проверяет реальную доступность
- Не спрашивает пользователя о правильных URL

**What should happen:**
```python
# CI Scout Agent
async def _build_single_profile(self, name: str, niche: str, geo: str):
    # 1. Попытаться найти URL через WebSearch
    url = await self._find_competitor_url(name, niche, geo)
    
    # 2. Если не нашли → спросить пользователя
    if not url:
        url = await self.ask_user(
            f"Не удалось найти URL для '{name}'. "
            f"Введите URL или пропустите этого конкурента?"
        )
    
    # 3. Проверить доступность
    is_accessible = await self._check_url_accessible(url)
    
    if not is_accessible:
        url = await self.ask_user(
            f"URL {url} недоступен для '{name}'. "
            f"Введите правильный URL или пропустите?"
        )
    
    profile = {
        "name": name,
        "url": url,
        "url_validated": True,
        ...
    }
```

### Problem 3: Data Flow Between Agents

**Current flow:**
```
CI Scout (Phase 1)
  ↓ generates URLs automatically
  ↓ saves to ci-competitors.json
CI Deep Analyzer (Phase 5)
  ↓ reads URLs from payload
  ↓ starts analysis immediately
  ↓ fails silently if URL wrong
```

**What should happen:**
```
CI Scout (Phase 1)
  ↓ finds competitors
  ↓ tries to find URLs via WebSearch
  ↓ asks user for missing/wrong URLs
  ↓ validates all URLs
  ↓ saves validated URLs to ci-competitors.json
  
CI Orchestrator (between phases)
  ↓ reads ci-competitors.json
  ↓ checks if all URLs validated
  ↓ if not → asks user before Phase 5
  
CI Deep Analyzer (Phase 5)
  ↓ receives validated URLs
  ↓ starts analysis
  ↓ if fails → asks user (not silent fail)
```

## Root Cause

**Architectural issue:** Agents work in isolation without user interaction checkpoints.

**Missing components:**
1. **URL Validator** - проверяет доступность URL перед анализом
2. **User Interaction Layer** - спрашивает пользователя при проблемах
3. **Data Validation Gates** - проверяет качество данных между фазами

## Impact

**Current impact:**
- ❌ Wasted time analyzing wrong URLs
- ❌ Silent failures (0% quality without explanation)
- ❌ No user feedback loop
- ❌ Poor user experience

**Potential impact:**
- ❌ Client reports with wrong competitor data
- ❌ Missed competitors due to wrong URLs
- ❌ Loss of trust in CI system

## Solution Design

### Component 1: URL Validator (New Agent)

```python
class CIURLValidator(Agent):
    """
    Validates competitor URLs before analysis.
    
    Responsibilities:
    1. Check URL accessibility (HTTP 200)
    2. Check robots.txt permissions
    3. Detect redirects
    4. Ask user for corrections if needed
    """
    
    async def validate_urls(self, competitors: List[Dict]) -> Dict:
        validated = {"success": [], "failed": [], "redirected": []}
        
        for comp in competitors:
            result = await self._check_url(comp["url"])
            
            if result["status"] == "success":
                validated["success"].append(comp)
            elif result["status"] == "redirect":
                # Ask user: use redirect or original?
                choice = await self.ask_user(
                    f"{comp['name']}: {comp['url']} → {result['redirect_url']}\n"
                    f"Использовать новый URL?"
                )
                if choice == "yes":
                    comp["url"] = result["redirect_url"]
                    validated["success"].append(comp)
            else:
                validated["failed"].append({
                    "name": comp["name"],
                    "url": comp["url"],
                    "error": result["error"]
                })
        
        # Ask user about failed URLs
        if validated["failed"]:
            corrections = await self._ask_user_corrections(validated["failed"])
            validated["success"].extend(corrections)
        
        return validated
```

### Component 2: CI Scout Enhancement

**Add URL discovery:**
```python
async def _find_competitor_url(self, name: str, niche: str, geo: str) -> Optional[str]:
    """
    Find competitor URL via WebSearch.
    
    Queries:
    - "{name} {geo} официальный сайт"
    - "{name} {niche} {geo} site:"
    - "{name} контакты телефон сайт"
    """
    queries = [
        f"{name} {geo} официальный сайт",
        f"{name} {niche} {geo}",
        f"{name} контакты"
    ]
    
    for query in queries:
        results = await self.web_search(query)
        url = self._extract_url_from_results(results, name)
        if url:
            return url
    
    return None
```

### Component 3: CI Orchestrator Enhancement

**Add validation gate between phases:**
```python
async def _execute_phases(self, tier: str, payload: Dict[str, Any]):
    results = {}
    
    # Phase 1: Scout
    phase1_result = await self._execute_phase(1, payload, results)
    results["phase_1"] = phase1_result
    
    # VALIDATION GATE: Check URLs before Phase 5
    if tier in ["deep", "full"]:
        competitors = phase1_result["top_for_analysis"]
        
        # Validate URLs
        validator = CIURLValidator(...)
        validated = await validator.validate_urls(competitors)
        
        # Update payload with validated URLs
        payload["competitors"] = validated["success"]
    
    # Phase 5: Deep Analysis (with validated URLs)
    phase5_result = await self._execute_phase(5, payload, results)
    ...
```

### Component 4: CI Deep Analyzer Enhancement

**Add failure handling:**
```python
async def _analyze_competitor(self, competitor: Dict) -> Dict:
    try:
        # Try to analyze
        result = await self._deep_analysis(competitor["url"])
        
        # Check quality
        if result["quality_score"] < 10:
            # Ask user
            action = await self.ask_user(
                f"Не удалось проанализировать {competitor['name']} ({competitor['url']}).\n"
                f"Причина: {result['error']}\n"
                f"Что делать?\n"
                f"1. Проверить URL\n"
                f"2. Пропустить\n"
                f"3. Попробовать с другими настройками"
            )
            
            if action == "1":
                new_url = await self.ask_user(f"Введите правильный URL для {competitor['name']}:")
                competitor["url"] = new_url
                return await self._analyze_competitor(competitor)
            elif action == "2":
                return {"status": "skipped", "reason": "user_choice"}
            elif action == "3":
                return await self._analyze_with_js_rendering(competitor)
        
        return result
        
    except Exception as e:
        # Don't fail silently!
        await self.ask_user(
            f"Ошибка при анализе {competitor['name']}: {str(e)}\n"
            f"Продолжить с остальными конкурентами?"
        )
        return {"status": "error", "error": str(e)}
```

## Implementation Plan

### Phase 1: URL Validator (Priority: P0)
1. Create `ci_url_validator.py`
2. Implement URL accessibility check
3. Implement user interaction for corrections
4. Add to CI Orchestrator as validation gate

### Phase 2: CI Scout Enhancement (Priority: P1)
1. Add WebSearch integration for URL discovery
2. Add user interaction for missing URLs
3. Update profile building to validate URLs
4. Save validation status to ci-competitors.json

### Phase 3: CI Deep Analyzer Enhancement (Priority: P1)
1. Add failure handling with user interaction
2. Add quality check after analysis
3. Add retry logic with user corrections
4. Never return 0% silently

### Phase 4: CI Orchestrator Enhancement (Priority: P2)
1. Add validation gates between phases
2. Add data quality checks
3. Add user interaction checkpoints
4. Add phase dependency validation

## Success Criteria

✅ **No silent failures** - always ask user if something wrong
✅ **URL validation before analysis** - check accessibility first
✅ **User interaction checkpoints** - ask for corrections when needed
✅ **Data quality gates** - validate data between phases
✅ **Clear error messages** - explain what went wrong and why

## Risks

**Risk 1: Too many user interactions**
- Mitigation: Batch questions, ask only when necessary
- Mitigation: Remember user choices for similar cases

**Risk 2: Slow validation**
- Mitigation: Validate URLs in parallel
- Mitigation: Cache validation results

**Risk 3: User fatigue**
- Mitigation: Provide smart defaults
- Mitigation: Allow "auto-fix" mode for experienced users

## Next Steps

1. ✅ Document problem (this file)
2. ⏳ Create CI URL Validator agent
3. ⏳ Enhance CI Scout with URL discovery
4. ⏳ Enhance CI Deep Analyzer with failure handling
5. ⏳ Add validation gates to CI Orchestrator
6. ⏳ Test with real competitor pool
7. ⏳ Update documentation

## Related Files

- `AIM/src/aim/subagents/competitive_intel/agents/ci_scout.py` - needs URL discovery
- `AIM/src/aim/subagents/competitive_intel/agents/ci_deep_analyzer.py` - needs failure handling
- `AIM/src/aim/subagents/competitive_intel/orchestrator/ci_orchestrator.py` - needs validation gates
- `scripts/test_ci_deep_multi.py` - test script that exposed this problem

## User Feedback

> "Ты сходу начал искать урлы, а нам надо, чтобы оператор спрашивал конкретно урлы, если у него есть сомнения."

> "И у нас в конкурентном анализе есть агент, который собирает конкурентов. Надо, чтобы он тоже смотрел по конкурентам."

> "Проанализируй все, что ты сделал, и подумай, как эти данные можно использовать далее и куда передавать."

---

**Status:** Problem identified, solution designed, ready for implementation
**Confidence:** 92% (high confidence in problem analysis, medium confidence in solution completeness)
**Owner:** meAI Architect
**Created:** 2026-05-05T16:42:00
