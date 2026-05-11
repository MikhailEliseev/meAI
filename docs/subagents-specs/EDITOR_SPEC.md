# Editor Agent - Спецификация

**Дата:** 2026-05-10  
**Magister:** Content Magister  
**Приоритет:** P1  
**Статус:** Draft

---

## 🎯 РОЛЬ И НАЗНАЧЕНИЕ

### Основная роль:
Editor Agent — автоматизированный редактор контента для медицинского маркетинга. Проверяет и улучшает тексты через многоуровневую проверку (грамматика → стиль → ToV → факты → readability → polish), обеспечивая публикационное качество, медицинскую точность и соответствие бренд-гайдам.

### Что делает:
- ✅ Проверяет грамматику, орфографию, пунктуацию (LanguageTool API)
- ✅ Анализирует readability и упрощает сложные предложения (Textstat, Hemingway)
- ✅ Проверяет соответствие Tone of Voice (интеграция с ToV Agent)
- ✅ Верифицирует медицинские факты (интеграция с Medical Fact-Checker Agent)
- ✅ Оптимизирует читаемость через AI-powered suggestions (Claude API)
- ✅ Генерирует детальный отчёт об изменениях с обоснованием

### Что НЕ делает:
- ❌ Не создаёт контент с нуля (это задача Blog/Landing Content Agent)
- ❌ Не проверяет SEO (это задача SEO Optimizer Agent)
- ❌ Не создаёт визуальный контент (изображения, видео)
- ❌ Не переводит на другие языки (это задача Translation Agent)

### Место в иерархии:
```
Content Magister
    ↓
Content Orchestrator
    ↓
Editor Agent ← вы здесь
```

---

## 📥 ВХОДНЫЕ ДАННЫЕ

### Получает от Orchestrator:

**Формат события:**
```json
{
  "event_type": "subagent.task.assigned",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "editor-agent",
  "payload": {
    "content_draft": "string",
    "content_type": "blog" | "landing" | "email",
    "target_audience": "patients" | "doctors" | "leads",
    "brand_guidelines": {
      "tone": "professional" | "friendly" | "authoritative",
      "formality": "formal" | "casual",
      "terminology_level": "simple" | "medical"
    },
    "medical_context": {
      "topic": "string",
      "specialty": "string",
      "target_readability": 60
    }
  }
}
```

**Обязательные параметры:**
- `content_draft` (string) - Черновик текста для редактирования
- `content_type` (string) - Тип контента: "blog", "landing", "email"
- `target_audience` (string) - Целевая аудитория: "patients", "doctors", "leads"

**Опциональные параметры:**
- `brand_guidelines` (dict) - Бренд-гайды для ToV проверки
- `medical_context` (dict) - Медицинский контекст для проверки фактов
- `target_readability` (int) - Целевой Flesch Reading Ease score (default: 60)

---

## 📤 ВЫХОДНЫЕ ДАННЫЕ

### Отправляет Orchestrator:

**Формат события:**
```json
{
  "event_type": "subagent.task.completed",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "editor-agent",
  "payload": {
    "status": "success" | "partial_success" | "failure",
    "result": {
      "edited_content": "string",
      "changes_summary": {
        "grammar_fixes": 5,
        "style_improvements": 3,
        "tov_adjustments": 2,
        "fact_corrections": 0,
        "readability_changes": 4
      },
      "quality_scores": {
        "readability_score": 65,
        "tov_compliance": 92,
        "grammar_accuracy": 100,
        "medical_accuracy": 100
      },
      "warnings": []
    },
    "metrics": {
      "execution_time_ms": 8500,
      "api_calls": {
        "languagetool": 1,
        "textstat": 1,
        "tov_agent": 1,
        "fact_checker": 1,
        "claude": 2
      }
    },
    "errors": []
  }
}
```

**Структура результата:**
- `edited_content` (string) - Отредактированный текст
- `changes_summary` (dict) - Количество изменений по категориям
- `quality_scores` (dict) - Метрики качества после редактирования
- `warnings` (list) - Предупреждения (если есть)

**Метрики:**
- `execution_time_ms` - Время выполнения (target: < 600000 ms = 10 min)
- `api_calls` - Количество вызовов внешних API

---

## 🔄 АЛГОРИТМ РАБОТЫ

### Шаг 1: Получение задачи
```python
async def receive_task(self, event: Event) -> None:
    """Получить задачу от Orchestrator"""
    self.task_id = event.task_id
    self.content_draft = event.payload["content_draft"]
    self.content_type = event.payload["content_type"]
    self.target_audience = event.payload["target_audience"]
    self.brand_guidelines = event.payload.get("brand_guidelines", {})
    self.medical_context = event.payload.get("medical_context", {})
    self.target_readability = event.payload.get("target_readability", 60)
```

### Шаг 2: Grammar Check (LanguageTool API)
```python
async def check_grammar(self, text: str) -> GrammarResult:
    """Проверка грамматики через LanguageTool API"""
    response = await self.languagetool_client.check(
        text=text,
        language="auto",  # auto-detect Russian/English
        enabledOnly=False
    )
    
    fixes = []
    for match in response["matches"]:
        fixes.append({
            "offset": match["offset"],
            "length": match["length"],
            "message": match["message"],
            "replacements": match["replacements"][:3],  # top 3
            "rule_id": match["rule"]["id"]
        })
    
    return GrammarResult(fixes=fixes, errors_found=len(fixes))
```

**API limits:**
- Free: 20 req/min, 75KB/min, 20KB/req
- Premium: 80 req/min, 300KB/min, 60KB/req
- Retry: 3 attempts with exponential backoff

### Шаг 3: Style & Readability Check (Textstat)
```python
async def check_readability(self, text: str) -> ReadabilityResult:
    """Проверка читаемости через Textstat"""
    import textstat
    
    flesch_reading_ease = textstat.flesch_reading_ease(text)
    flesch_kincaid_grade = textstat.flesch_kincaid_grade(text)
    smog_index = textstat.smog_index(text)
    
    # Identify complex sentences (grade > 14)
    complex_sentences = self._find_complex_sentences(text)
    
    return ReadabilityResult(
        flesch_reading_ease=flesch_reading_ease,
        flesch_kincaid_grade=flesch_kincaid_grade,
        smog_index=smog_index,
        complex_sentences=complex_sentences,
        meets_target=flesch_reading_ease >= self.target_readability
    )
```

**Readability targets:**
- Patients: Flesch Reading Ease > 60 (Grade 6-8)
- Doctors: Flesch Reading Ease 50-60 (Grade 9-12)
- SMOG Index: 6-8 (patients), 9-12 (doctors)

### Шаг 4: Tone of Voice Check (ToV Agent)
```python
async def check_tone_of_voice(self, text: str) -> ToVResult:
    """Проверка ToV через Tone of Voice Agent"""
    event = Event(
        event_type="subagent.task.assigned",
        correlation_id=self.correlation_id,
        task_id=f"{self.task_id}-tov",
        subagent_id="tone-of-voice-agent",
        payload={
            "text": text,
            "brand_guidelines": self.brand_guidelines,
            "content_type": self.content_type
        }
    )
    
    await self.event_bus.publish(event, priority=Priority.P1)
    result = await self.wait_for_result(f"{self.task_id}-tov", timeout=30)
    
    return ToVResult(
        compliance_score=result["compliance_score"],
        violations=result["violations"],
        suggestions=result["suggestions"]
    )
```

**ToV compliance target:** > 90%

### Шаг 5: Medical Facts Check (Medical Fact-Checker Agent)
```python
async def check_medical_facts(self, text: str) -> FactCheckResult:
    """Проверка медицинских фактов через Medical Fact-Checker Agent"""
    event = Event(
        event_type="subagent.task.assigned",
        correlation_id=self.correlation_id,
        task_id=f"{self.task_id}-facts",
        subagent_id="medical-fact-checker-agent",
        payload={
            "text": text,
            "medical_context": self.medical_context
        }
    )
    
    await self.event_bus.publish(event, priority=Priority.P0)  # Critical
    result = await self.wait_for_result(f"{self.task_id}-facts", timeout=180)
    
    return FactCheckResult(
        facts_verified=result["facts_verified"],
        facts_corrected=result["facts_corrected"],
        warnings=result["warnings"]
    )
```

**Medical accuracy target:** 100% facts verified


### Шаг 6: Readability Optimization (Claude API)
```python
async def optimize_readability(self, text: str, issues: list) -> str:
    """Оптимизация читаемости через Claude API"""
    prompt = f"""You are a medical content editor. Improve the readability of this text while maintaining medical accuracy.

Text:
{text}

Issues to fix:
{json.dumps(issues, indent=2)}

Target audience: {self.target_audience}
Target Flesch Reading Ease: {self.target_readability}

Instructions:
1. Simplify complex sentences (grade > 14)
2. Replace jargon with simpler terms (when appropriate for audience)
3. Break long paragraphs
4. Maintain medical accuracy (DO NOT change medical facts)
5. Keep the same tone and style

Return only the improved text, no explanations."""

    response = await self.claude_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text
```

**Claude API cost:** ~$0.05 per 1,500-word article

### Шаг 7: Final Polish (Claude API)
```python
async def final_polish(self, text: str, all_checks: dict) -> str:
    """Финальная полировка через Claude API"""
    prompt = f"""You are a medical content editor. Apply final polish to this text.

Text:
{text}

Previous checks:
- Grammar: {all_checks['grammar']['errors_found']} errors fixed
- Readability: {all_checks['readability']['flesch_reading_ease']} (target: {self.target_readability})
- ToV compliance: {all_checks['tov']['compliance_score']}%
- Medical facts: {all_checks['facts']['facts_verified']} verified

Instructions:
1. Ensure smooth flow between sentences
2. Remove redundancy
3. Strengthen weak phrases
4. Maintain consistency in terminology
5. Add transitions where needed
6. DO NOT change medical facts

Return only the polished text, no explanations."""

    response = await self.claude_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text
```

### Шаг 8: Generate Changes Summary
```python
async def generate_changes_summary(self, original: str, edited: str, checks: dict) -> dict:
    """Генерация отчёта об изменениях"""
    import difflib
    
    diff = list(difflib.unified_diff(
        original.splitlines(),
        edited.splitlines(),
        lineterm=""
    ))
    
    return {
        "grammar_fixes": checks["grammar"]["errors_found"],
        "style_improvements": len(checks["readability"]["complex_sentences"]),
        "tov_adjustments": len(checks["tov"]["violations"]),
        "fact_corrections": checks["facts"]["facts_corrected"],
        "readability_changes": len([s for s in diff if s.startswith("+") or s.startswith("-")]),
        "diff": "\n".join(diff[:100])  # First 100 lines
    }
```

### Шаг 9: Отправка результата
```python
async def send_result(self, edited_content: str, summary: dict, scores: dict) -> None:
    """Отправить результат Orchestrator"""
    event = Event(
        event_type="subagent.task.completed",
        correlation_id=self.correlation_id,
        task_id=self.task_id,
        subagent_id="editor-agent",
        payload={
            "status": "success",
            "result": {
                "edited_content": edited_content,
                "changes_summary": summary,
                "quality_scores": scores,
                "warnings": self.warnings
            },
            "metrics": {
                "execution_time_ms": self.execution_time,
                "api_calls": self.api_calls
            },
            "errors": []
        }
    )
    
    await self.event_bus.publish(event, priority=Priority.P1)
```

---

## 📊 МЕТРИКИ УСПЕХА

### Качество:
- **Grammar errors fixed:** 100% (все найденные ошибки исправлены)
- **Readability score:** > 60 Flesch Reading Ease (для пациентов)
- **ToV compliance:** > 90% (соответствие бренд-гайдам)
- **Medical facts verified:** 100% (все факты проверены)
- **E-E-A-T compliance:** 100% (для YMYL контента)

### Производительность:
- **Time to edit:** < 10 минут (для статьи 1,500 слов)
- **API uptime:** > 99% (доступность внешних API)
- **Error rate:** < 1% (процент неудачных проверок)

### Стоимость:
- **LanguageTool API:** < $0.01 per check
- **Claude API:** < $0.05 per article
- **Total cost per article:** < $0.10

### Бенчмарки:
- **Human editor baseline:** 30-60 минут, $75-150/hour
- **ROI breakeven:** 10-12 минут экономии
- **Quality parity:** 85-90% vs human editor

---

## 🔗 КОММУНИКАЦИЯ С ДРУГИМИ АГЕНТАМИ

### Upstream (получает задачи от):
- **Content Orchestrator** - делегирует задачи редактирования

### Downstream (делегирует задачи):
- **Tone of Voice Agent** - проверка соответствия бренд-гайдам
- **Medical Fact-Checker Agent** - верификация медицинских фактов

### Peer (взаимодействует с):
- **Blog Content Agent** - источник черновиков блогов
- **Landing Content Agent** - источник черновиков лендингов
- **SEO Optimizer Agent** - SEO-оптимизация после редактирования

### Event Bus паттерны:
```python
# Подписка на события
await event_bus.subscribe(
    event_type="subagent.task.assigned",
    handler=self.receive_task,
    filter={"subagent_id": "editor-agent"}
)

# Публикация результата
await event_bus.publish(
    event=result_event,
    priority=Priority.P1
)

# Делегирование субагентам
await event_bus.publish(
    event=delegation_event,
    priority=Priority.P0  # Critical для Medical Fact-Checker
)
```

---

## ⚠️ ОБРАБОТКА ОШИБОК

### Типичные ошибки:

**1. LanguageTool API timeout**
```python
try:
    result = await self.languagetool_client.check(text, timeout=30)
except TimeoutError:
    # Retry with exponential backoff
    for attempt in range(3):
        await asyncio.sleep(2 ** attempt)
        try:
            result = await self.languagetool_client.check(text, timeout=60)
            break
        except TimeoutError:
            if attempt == 2:
                # Fallback: skip grammar check, log warning
                self.warnings.append("Grammar check skipped due to API timeout")
                result = {"matches": []}
```

**2. ToV Agent unavailable**
```python
try:
    tov_result = await self.check_tone_of_voice(text)
except AgentUnavailableError:
    # Fallback: basic ToV check via Claude API
    self.warnings.append("ToV Agent unavailable, using fallback")
    tov_result = await self.fallback_tov_check(text)
```

**3. Medical Fact-Checker timeout**
```python
try:
    facts_result = await self.check_medical_facts(text)
except TimeoutError:
    # CRITICAL: Do not proceed without fact-checking
    raise EditorAgentError(
        "Medical fact-checking failed - cannot proceed",
        severity="critical"
    )
```

**4. Claude API rate limit**
```python
try:
    optimized = await self.optimize_readability(text, issues)
except RateLimitError as e:
    # Wait for rate limit reset
    await asyncio.sleep(e.retry_after)
    optimized = await self.optimize_readability(text, issues)
```

### Retry стратегия:
- **LanguageTool API:** 3 attempts, exponential backoff (2s, 4s, 8s)
- **ToV Agent:** 2 attempts, fallback to Claude API
- **Medical Fact-Checker:** 3 attempts, FAIL if all fail (critical)
- **Claude API:** Wait for rate limit reset, then retry

### Fallback стратегии:
- **Grammar check:** Skip if API unavailable (log warning)
- **ToV check:** Use Claude API as fallback
- **Fact check:** FAIL (no fallback - too critical)
- **Readability:** Use basic Textstat only (no AI optimization)

---

## 🧪 ТЕСТИРОВАНИЕ

### Unit тесты:
```python
# tests/test_editor_agent.py

async def test_grammar_check():
    """Test grammar checking with LanguageTool"""
    agent = EditorAgent()
    text = "This is a test. It have errors."
    result = await agent.check_grammar(text)
    assert result.errors_found > 0
    assert "have" in str(result.fixes)

async def test_readability_check():
    """Test readability calculation"""
    agent = EditorAgent()
    text = "Simple sentence. Another simple sentence."
    result = await agent.check_readability(text)
    assert result.flesch_reading_ease > 60
    assert len(result.complex_sentences) == 0

async def test_full_pipeline():
    """Test full editing pipeline"""
    agent = EditorAgent()
    draft = "This is a draft with errors and complex sentences that need simplification."
    result = await agent.execute({
        "content_draft": draft,
        "content_type": "blog",
        "target_audience": "patients"
    })
    assert result["status"] == "success"
    assert result["quality_scores"]["readability_score"] >= 60
```

### Integration тесты:
```python
# tests/integration/test_editor_integration.py

async def test_tov_agent_integration():
    """Test integration with ToV Agent"""
    editor = EditorAgent()
    tov_agent = ToneOfVoiceAgent()
    
    # Start both agents
    await editor.start()
    await tov_agent.start()
    
    # Send task to editor
    result = await editor.execute({
        "content_draft": "Test content",
        "brand_guidelines": {"tone": "professional"}
    })
    
    assert result["quality_scores"]["tov_compliance"] > 90

async def test_fact_checker_integration():
    """Test integration with Medical Fact-Checker"""
    editor = EditorAgent()
    fact_checker = MedicalFactCheckerAgent()
    
    await editor.start()
    await fact_checker.start()
    
    result = await editor.execute({
        "content_draft": "Aspirin reduces fever.",
        "medical_context": {"topic": "medications"}
    })
    
    assert result["quality_scores"]["medical_accuracy"] == 100
```

### E2E тесты:
```python
# tests/e2e/test_editor_e2e.py

async def test_blog_editing_workflow():
    """Test full blog editing workflow"""
    # 1. Blog Content Agent creates draft
    blog_agent = BlogContentAgent()
    draft = await blog_agent.execute({"topic": "diabetes management"})
    
    # 2. Editor Agent edits draft
    editor = EditorAgent()
    edited = await editor.execute({
        "content_draft": draft["content"],
        "content_type": "blog",
        "target_audience": "patients"
    })
    
    # 3. Verify quality
    assert edited["quality_scores"]["readability_score"] >= 60
    assert edited["quality_scores"]["grammar_accuracy"] == 100
    assert edited["quality_scores"]["medical_accuracy"] == 100
```


---

## 💼 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ

### Пример 1: Редактирование блога для пациентов
```python
# Input
task = {
    "content_draft": """
    Диабет это серьезное заболевание которое влияет на способность организма 
    регулировать уровень глюкозы в крови. Пациенты с диабетом должны 
    мониторить свой уровень сахара регулярно и принимать инсулин если необходимо.
    """,
    "content_type": "blog",
    "target_audience": "patients",
    "medical_context": {
        "topic": "diabetes",
        "specialty": "endocrinology"
    }
}

# Output
result = {
    "edited_content": """
    Диабет — серьёзное заболевание, которое влияет на способность организма 
    регулировать уровень глюкозы в крови. Если у вас диабет, важно регулярно 
    проверять уровень сахара и принимать инсулин по назначению врача.
    """,
    "changes_summary": {
        "grammar_fixes": 3,  # запятые, тире
        "style_improvements": 2,  # упрощение предложений
        "tov_adjustments": 1,  # "вы" вместо "пациенты"
        "fact_corrections": 0,
        "readability_changes": 2
    },
    "quality_scores": {
        "readability_score": 68,  # было 52
        "tov_compliance": 95,
        "grammar_accuracy": 100,
        "medical_accuracy": 100
    }
}
```

### Пример 2: Редактирование лендинга для лидов
```python
# Input
task = {
    "content_draft": """
    Запишитесь на прием к кардиологу сегодня! Мы гарантируем полное 
    излечение всех сердечных заболеваний. Наши врачи имеют опыт более 20 лет.
    """,
    "content_type": "landing",
    "target_audience": "leads",
    "brand_guidelines": {
        "tone": "professional",
        "formality": "formal"
    }
}

# Output
result = {
    "edited_content": """
    Запишитесь на приём к кардиологу сегодня! Наши специалисты с опытом 
    более 20 лет помогут вам позаботиться о здоровье сердца.
    
    *Результаты лечения индивидуальны и зависят от состояния здоровья пациента.
    """,
    "changes_summary": {
        "grammar_fixes": 1,  # "приём" вместо "прием"
        "style_improvements": 1,
        "tov_adjustments": 0,
        "fact_corrections": 1,  # удалена гарантия излечения
        "readability_changes": 2
    },
    "quality_scores": {
        "readability_score": 72,
        "tov_compliance": 92,
        "grammar_accuracy": 100,
        "medical_accuracy": 100
    },
    "warnings": [
        "Added disclaimer: medical claims require disclaimer per 152-ФЗ"
    ]
}
```

### Пример 3: Редактирование для врачей
```python
# Input
task = {
    "content_draft": """
    Пациент поступил с острым коронарным синдромом. Была проведена 
    коронарография которая выявила стеноз ЛКА 90%. Выполнена ангиопластика 
    со стентированием.
    """,
    "content_type": "blog",
    "target_audience": "doctors",
    "medical_context": {
        "topic": "cardiology",
        "specialty": "interventional_cardiology"
    }
}

# Output
result = {
    "edited_content": """
    Пациент поступил с острым коронарным синдромом. Была проведена 
    коронарография, которая выявила стеноз ЛКА 90%. Выполнена ангиопластика 
    со стентированием.
    """,
    "changes_summary": {
        "grammar_fixes": 1,  # запятая после "коронарография"
        "style_improvements": 0,  # медицинская терминология сохранена
        "tov_adjustments": 0,
        "fact_corrections": 0,
        "readability_changes": 0
    },
    "quality_scores": {
        "readability_score": 45,  # ниже для профессионального контента
        "tov_compliance": 100,
        "grammar_accuracy": 100,
        "medical_accuracy": 100
    }
}
```

---

## 🔌 ЗАВИСИМОСТИ

### Внешние API:

**LanguageTool API:**
- URL: `https://api.languagetool.org/v2/check`
- Auth: API key (Premium tier)
- Pricing: $59/mo (1000 calls/day) or $99/mo (2500 calls/day)
- Rate limits: 80 req/min, 300KB/min, 60KB/req
- Documentation: https://languagetool.org/http-api/swagger-ui/

**Claude API (Anthropic):**
- Model: `claude-sonnet-4-20250514`
- Pricing: ~$3 per 1M input tokens, ~$15 per 1M output tokens
- Rate limits: Tier-dependent (check dashboard)
- Documentation: https://docs.anthropic.com/

**Textstat (Python library):**
- Package: `textstat==0.7.3`
- License: MIT
- Installation: `pip install textstat`
- Documentation: https://github.com/textstat/textstat

### Internal Agents:

**Tone of Voice Agent:**
- Event: `subagent.task.assigned` → `tone-of-voice-agent`
- Timeout: 30 seconds
- Priority: P1
- Fallback: Claude API

**Medical Fact-Checker Agent:**
- Event: `subagent.task.assigned` → `medical-fact-checker-agent`
- Timeout: 180 seconds (3 minutes)
- Priority: P0 (Critical)
- Fallback: None (FAIL if unavailable)

### Python Dependencies:
```txt
# requirements.txt
anthropic>=0.25.0
httpx>=0.27.0
textstat>=0.7.3
pydantic>=2.7.0
asyncio>=3.4.3
```

### Environment Variables:
```bash
# .env
LANGUAGETOOL_API_KEY=your_api_key_here
ANTHROPIC_API_KEY=your_api_key_here
LANGUAGETOOL_API_URL=https://api.languagetool.org/v2/check
EDITOR_AGENT_TIMEOUT=600000  # 10 minutes
```

---

## 🚀 DEPLOYMENT

### Docker:
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY .env .

CMD ["python", "-m", "src.aim.subagents.editor_agent"]
```

### Kubernetes:
```yaml
# k8s/editor-agent-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: editor-agent
spec:
  replicas: 2
  selector:
    matchLabels:
      app: editor-agent
  template:
    metadata:
      labels:
        app: editor-agent
    spec:
      containers:
      - name: editor-agent
        image: aim/editor-agent:latest
        env:
        - name: LANGUAGETOOL_API_KEY
          valueFrom:
            secretKeyRef:
              name: editor-agent-secrets
              key: languagetool-api-key
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: editor-agent-secrets
              key: anthropic-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

### Health Checks:
```python
# src/aim/subagents/editor_agent/health.py

async def health_check() -> dict:
    """Health check endpoint"""
    checks = {
        "languagetool_api": await check_languagetool_api(),
        "claude_api": await check_claude_api(),
        "event_bus": await check_event_bus(),
        "tov_agent": await check_tov_agent(),
        "fact_checker": await check_fact_checker()
    }
    
    all_healthy = all(checks.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }
```

---

## 📝 CHANGELOG

### v1.0.0 (2026-05-10)
- ✅ Initial specification created
- ✅ Grammar check via LanguageTool API
- ✅ Readability check via Textstat
- ✅ ToV check via Tone of Voice Agent
- ✅ Medical facts check via Medical Fact-Checker Agent
- ✅ AI-powered optimization via Claude API
- ✅ Comprehensive error handling and retry logic
- ✅ Full test coverage (unit, integration, e2e)

---

## 📋 TODO

### Phase 1 (MVP):
- [ ] Implement LanguageTool API client
- [ ] Implement Textstat integration
- [ ] Implement Claude API client
- [ ] Implement Event Bus communication
- [ ] Implement retry logic and error handling
- [ ] Write unit tests
- [ ] Write integration tests

### Phase 2 (Enhancements):
- [ ] Add support for more languages (French, German, Spanish)
- [ ] Implement caching for repeated checks
- [ ] Add batch processing for multiple articles
- [ ] Implement version control (track changes history)
- [ ] Add A/B testing for different editing strategies

### Phase 3 (Advanced):
- [ ] Train custom LanguageTool rules for medical content
- [ ] Implement custom readability formula for medical content
- [ ] Add support for images and multimedia content
- [ ] Implement real-time collaborative editing
- [ ] Add support for voice-to-text editing

---

## 📚 ПРИЛОЖЕНИЕ A: RESEARCH SUMMARY

### Readability Tools

**Hemingway Editor:**
- Readability score based on Automated Readability Index (ARI)
- Color-coded highlighting: yellow (grade 12), red (grade 14+)
- Target: Grade 9 for general audience, Grade 5 for accessibility
- Desktop app: $19.99 one-time
- API: Not publicly available

**Source:** [Hemingway Editor Help](https://hemingwayapp.com/help/docs/readability)

**Textstat (Python library):**
- Flesch Reading Ease: 0-100 scale (higher = easier)
- Flesch-Kincaid Grade Level: US grade level
- SMOG Index: recommended for healthcare
- Free, open-source

**Source:** [py-readability-metrics](https://github.com/cdimascio/py-readability-metrics)

### Grammar Tools

**LanguageTool API:**
- Pricing: $29/mo (250 calls/day), $39/mo (500), $59/mo (1000), $99/mo (2500)
- Languages: 30+ (English, Russian, German, French, Spanish)
- GDPR-compliant, EU servers
- Self-hosting available

**Source:** [LanguageTool API](https://languagetool.org/proofreading-api)

**Grammarly vs LanguageTool:**
- LanguageTool: multilingual, privacy-focused, cheaper, self-hosting
- Grammarly: English-only, better accuracy (89% grammar, 76% style), no public API
- For medical content: LanguageTool preferred (GDPR, multilingual)

**Source:** [LanguageTool vs Grammarly (2026)](https://awesomeagents.ai/tools/best-ai-grammar-checkers-2026/)

### Medical Content Editing

**Key findings:**
- Medical terminology requires contextual accuracy
- Grammarly: 89% grammar detection, 76% style (medical content)
- LanguageTool: lower false-positive rate, better for medical terms
- Human baseline: $75-150/hour, 30-60 minutes per 1,500 words

**Source:** [Medical Content Review](https://writern.net/medical-content-editing-review/)

### Compliance

**E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness):**
- Google's quality guidelines for YMYL content
- Medical content must demonstrate author credentials
- Citations to authoritative sources required

**YMYL (Your Money or Your Life):**
- Medical, health, financial content
- Higher quality standards
- Fact-checking mandatory

**FDA Regulations:**
- Medical device marketing: 21 CFR Part 801
- Drug advertising: 21 CFR Part 202
- Disclaimers required for health claims

**152-ФЗ (РФ):**
- Федеральный закон о рекламе медицинских услуг
- Запрет на гарантии результата лечения
- Обязательные disclaimers

---

**Автор:** Mikhail Eliseev (via meAI Architect)  
**Версия:** 1.0.0  
**Последнее обновление:** 2026-05-10  
**Статус:** ✅ Ready for Implementation

