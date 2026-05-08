---
title: "Lesson: CI URL Validation Silent Failure"
date: "2026-05-05"
category: "bug"
severity: "critical"
tags: [ci-system, validation, user-interaction, silent-failure, data-quality]
status: "active"
---

# Lesson Learned: CI URL Validation Silent Failure

## What Happened (Что случилось)

CI Deep Analyzer проанализировал 5 конкурентов из косметологии. 4 конкурента получили 100% качества, но 5-й конкурент (Клиника Юлии Щербатовой) получил 0% качества.

**Проблема:** Система вернула 0% результат без вопроса пользователю.

**Детали:**
- Неправильный URL: `doctor-shcherbatova.ru` (не работает)
- Правильный URL: `juliasherbatova.ru`
- Агент попытался проанализировать, получил пустой результат, вернул 0% молча
- Пользователь узнал о проблеме только после просмотра результатов

## Why It Happened (Почему случилось)

**Root Cause 1: CI Scout генерирует URL автоматически**
```python
# ci_scout.py:269
profile = {
    "name": name,
    "url": f"https://{self._slugify(name)}.ru",  # ❌ Auto-generated
    ...
}
```
- Slugify преобразует "Клиника Юлии Щербатовой" → "doctor-shcherbatova"
- Не проверяет реальную доступность URL
- Не спрашивает пользователя о правильном URL

**Root Cause 2: Нет URL validation между фазами**
```
Phase 1 (Scout) → ci-competitors.json → Phase 5 (Deep Analyzer)
❌ Нет проверки URL между фазами
```

**Root Cause 3: CI Deep Analyzer не спрашивает при ошибках**
```python
# ci_deep_analyzer.py
async def execute_task(self, task: Task):
    for comp in competitors:
        result = await self._analyze_competitor(comp)
        # ❌ Если result["quality_score"] == 0 → молча возвращает
```

**Root Cause 4: Архитектурная проблема**
- Агенты работают в изоляции без user interaction checkpoints
- Нет validation gates между фазами
- Нет проверки качества данных перед дорогими операциями

## Impact (Влияние)

- **User impact:** 
  - Потрачено время на анализ неправильного URL
  - Неполные результаты (4 из 5 конкурентов)
  - Плохой UX - система не спросила, просто вернула 0%
  
- **System impact:**
  - Wasted resources на попытку анализа недоступного URL
  - Неполные данные в ci-deep/deep_analysis.json
  - Потеря доверия к CI системе

- **Business impact:**
  - Клиентский отчёт будет неполным
  - Пропущен важный конкурент
  - Риск принятия решений на неполных данных

## Solution (Решение)

**Создать 3-компонентную систему:**

1. **URL Validator Agent** (новый агент)
   - Проверяет доступность URL перед анализом
   - Спрашивает пользователя при проблемах
   - Работает между Phase 1 и Phase 5

2. **Validation Gates в CI Orchestrator**
   - Проверка данных между фазами
   - User interaction checkpoints
   - Никогда не fail silently

3. **Enhanced Error Handling в агентах**
   - CI Scout: WebSearch для поиска реальных URL
   - CI Deep Analyzer: спрашивает при 0% качестве
   - Все агенты: никогда не возвращают пустой результат молча

**Документация:**
- Problem: `obsidian/architect/decisions/2026-05-05-16-42-ci-url-validation-problem.md`
- Data Flow: `obsidian/architect/wiki/connections/ci-data-flow-analysis.md`

## Prevention Rules (Правила предотвращения)

1. **ALWAYS: Validate URLs before expensive operations**
   ```python
   # Before deep analysis
   validated = await self._validate_url(url)
   if not validated:
       url = await self.ask_user(f"URL {url} недоступен. Введите правильный URL:")
   ```

2. **NEVER: Return 0% or empty results without asking user**
   ```python
   # After analysis
   if result["quality_score"] < 10:
       action = await self.ask_user(
           f"Не удалось проанализировать {name}. Что делать?\n"
           f"1. Проверить URL\n2. Пропустить\n3. Попробовать другие настройки"
       )
   ```

3. **NEVER: Auto-generate URLs without validation**
   ```python
   # ❌ Wrong
   url = f"https://{slugify(name)}.ru"
   
   # ✅ Right
   url = await self._find_url_via_websearch(name, niche, geo)
   if not url:
       url = await self.ask_user(f"Введите URL для {name}:")
   validated = await self._check_url_accessible(url)
   ```

4. **CHECK: Data quality between phases**
   ```python
   # In CI Orchestrator between phases
   if not self._validate_phase_output(phase_result):
       await self.ask_user("Данные неполные. Продолжить или исправить?")
   ```

5. **ALWAYS: Add validation gates before expensive operations**
   - Before Phase 5 (Deep Analysis) → validate URLs
   - Before Phase 10 (TW Agents) → validate competitors data
   - Before Phase 16 (Offer Generator) → validate all data

## Code Examples (Примеры кода)

### ❌ Wrong (Неправильно)

```python
# CI Scout - auto-generates URL
profile = {
    "name": name,
    "url": f"https://{self._slugify(name)}.ru",  # ❌ Не проверяет
}

# CI Deep Analyzer - fails silently
async def execute_task(self, task: Task):
    for comp in competitors:
        result = await self._analyze_competitor(comp)
        # ❌ Если 0% → молча возвращает
        results.append(result)
    return results
```

### ✅ Right (Правильно)

```python
# CI Scout - finds real URL
async def _build_single_profile(self, name: str, niche: str, geo: str):
    # 1. Try to find URL via WebSearch
    url = await self._find_competitor_url(name, niche, geo)
    
    # 2. If not found → ask user
    if not url:
        url = await self.ask_user(
            f"Не удалось найти URL для '{name}'. Введите URL:"
        )
    
    # 3. Validate accessibility
    is_accessible = await self._check_url_accessible(url)
    if not is_accessible:
        url = await self.ask_user(
            f"URL {url} недоступен. Введите правильный URL:"
        )
    
    profile = {
        "name": name,
        "url": url,
        "url_validated": True,
        ...
    }

# CI Deep Analyzer - asks on failure
async def _analyze_competitor(self, competitor: Dict) -> Dict:
    try:
        result = await self._deep_analysis(competitor["url"])
        
        # Check quality
        if result["quality_score"] < 10:
            action = await self.ask_user(
                f"Не удалось проанализировать {competitor['name']}.\n"
                f"Причина: {result.get('error', 'unknown')}\n"
                f"Что делать?\n"
                f"1. Проверить URL\n"
                f"2. Пропустить\n"
                f"3. Попробовать с другими настройками"
            )
            
            if action == "1":
                new_url = await self.ask_user(
                    f"Введите правильный URL для {competitor['name']}:"
                )
                competitor["url"] = new_url
                return await self._analyze_competitor(competitor)
            elif action == "2":
                return {"status": "skipped", "reason": "user_choice"}
            elif action == "3":
                return await self._analyze_with_js_rendering(competitor)
        
        return result
        
    except Exception as e:
        # ✅ Never fail silently!
        await self.ask_user(
            f"Ошибка при анализе {competitor['name']}: {str(e)}\n"
            f"Продолжить с остальными?"
        )
        return {"status": "error", "error": str(e)}

# CI Orchestrator - validation gate
async def _execute_phases(self, tier: str, payload: Dict):
    # Phase 1: Scout
    phase1_result = await self._execute_phase(1, payload, {})
    
    # ✅ VALIDATION GATE before Phase 5
    if tier in ["deep", "full"]:
        competitors = phase1_result["top_for_analysis"]
        
        # Validate URLs
        validator = CIURLValidator(...)
        validated = await validator.validate_urls(competitors)
        
        # Update payload with validated URLs
        payload["competitors"] = validated["success"]
    
    # Phase 5: Deep Analysis (with validated URLs)
    phase5_result = await self._execute_phase(5, payload, results)
```

## Related

- **Decision:** [CI URL Validation Problem](../../decisions/2026-05-05-16-42-ci-url-validation-problem.md)
- **Analysis:** [CI Data Flow Analysis](../connections/ci-data-flow-analysis.md)
- **Issue:** Клиника Юлии Щербатовой - wrong URL (doctor-shcherbatova.ru → juliasherbatova.ru)
- **Similar lessons:** None yet (first lesson in CI system)

## Applied To (Применено к)

- [ ] CI Scout Agent - add URL discovery via WebSearch
- [ ] CI Deep Analyzer - add error handling with user interaction
- [ ] CI Orchestrator - add validation gates between phases
- [ ] CI URL Validator - create new agent (P0)
- [ ] Documentation - update CI system docs
- [ ] Tests - add URL validation tests

## Implementation Status

**Status:** Solution designed, ready for implementation

**Next Steps:**
1. Create CI URL Validator agent
2. Add validation gate in CI Orchestrator
3. Enhance CI Deep Analyzer error handling
4. Enhance CI Scout URL discovery
5. Test with real competitor pool

**Priority:** P0 (Critical - blocks Phase 5 reliability)

---

**Created:** 2026-05-05
**Last Updated:** 2026-05-05
**Author:** meAI Architect
**Triggered By:** User feedback on CI Deep Analyzer results
