# meAI Implementation Strategy - Model Configuration

**Date:** 2026-05-01  
**Status:** Planning for Implementation

---

## Problem Statement

Текущая модель (Sonnet 4.5 на Cods.on.net) может быть недостаточно мощной для реализации всех 25 задач meAI Core Foundation.

**Нужно:** Opus 4.6 или 4.7 для самого сильного кода.

---

## Recommended Approach: Hybrid Model Strategy

### Strategy A: Task-Based Model Selection (Recommended)

Используй разные модели для разных типов задач:

#### 1. Planning & Architecture (Opus 4.6/4.7)
**Tasks:** 21-25 (Core Architect, Decision Maker, Orchestrator, System Registry, Rollback)
**Why:** Эти задачи требуют глубокого понимания архитектуры и сложной логики
**Model:** `claude-opus-4-6` или `claude-opus-4-7`

#### 2. Infrastructure & Boilerplate (Sonnet 4.5)
**Tasks:** 1-7 (Setup, Config, Database, Obsidian, Event Store, Event Bus)
**Why:** Стандартные паттерны, много boilerplate кода
**Model:** `claude-sonnet-4-5` (текущая модель)

#### 3. Safety & Monitoring (Sonnet 4.5)
**Tasks:** 11-17 (Loop Detector, Timeout Manager, Context Monitor, Health Checks, Metrics)
**Why:** Хорошо документированные паттерны, не требуют креативности
**Model:** `claude-sonnet-4-5`

#### 4. Testing & Deployment (Haiku 4.5 + Opus review)
**Tasks:** 18-20 (FastAPI, Deployment, E2E Test, Documentation)
**Why:** Много шаблонного кода, но нужна проверка Opus
**Model:** `claude-haiku-4-5` для написания, `claude-opus-4-6` для review

---

## Configuration Options

### Option 1: Claude Code Model Override (Per-Task)

В Claude Code можно переключать модель через `/model`:

```bash
# Для сложных задач (21-25)
/model opus

# Для стандартных задач (1-7, 11-17)
/model sonnet

# Для быстрых задач (18-20)
/model haiku
```

**Pros:**
- Гибкость - переключаешь модель по мере необходимости
- Контроль затрат - используешь Opus только где нужно
- Можно использовать текущий Claude Code CLI

**Cons:**
- Нужно помнить переключать модель
- Нет автоматизации

---

### Option 2: GSD Model Profile Configuration

Создай конфигурацию в `.planning/config.json`:

```json
{
  "execution": {
    "model_profile": "hybrid",
    "models": {
      "planning": "claude-opus-4-6",
      "implementation": "claude-sonnet-4-5",
      "testing": "claude-haiku-4-5",
      "review": "claude-opus-4-6"
    },
    "task_model_mapping": {
      "1-7": "claude-sonnet-4-5",
      "8-10": "claude-sonnet-4-5",
      "11-14": "claude-sonnet-4-5",
      "15-17": "claude-sonnet-4-5",
      "18-20": "claude-haiku-4-5",
      "21-25": "claude-opus-4-6"
    }
  }
}
```

Затем используй `/gsd-execute-phase` с этой конфигурацией.

**Pros:**
- Автоматическое переключение моделей
- Оптимизация затрат
- Воспроизводимость

**Cons:**
- Требует поддержки в GSD (может не работать сейчас)
- Сложнее настроить

---

### Option 3: Separate CLI Sessions (Multi-Agent)

Запусти несколько Claude Code сессий с разными моделями:

**Session 1 (Sonnet 4.5):** Tasks 1-17
```bash
claude --model claude-sonnet-4-5
```

**Session 2 (Opus 4.6):** Tasks 21-25
```bash
claude --model claude-opus-4-6
```

**Session 3 (Haiku 4.5):** Tasks 18-20
```bash
claude --model claude-haiku-4-5
```

**Pros:**
- Полный контроль над моделями
- Можно работать параллельно
- Изоляция контекста

**Cons:**
- Нужно управлять несколькими сессиями
- Сложнее координировать

---

### Option 4: External API with Model Selection

Используй Anthropic API напрямую с выбором модели:

```python
# src/meai/utils/claude_client.py
import anthropic

def get_model_for_task(task_number: int) -> str:
    """Get appropriate model for task"""
    if 21 <= task_number <= 25:
        return "claude-opus-4-6"
    elif 18 <= task_number <= 20:
        return "claude-haiku-4-5"
    else:
        return "claude-sonnet-4-5"

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

def generate_code(task_number: int, prompt: str) -> str:
    model = get_model_for_task(task_number)
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text
```

**Pros:**
- Программная автоматизация
- Точный контроль
- Можно интегрировать в CI/CD

**Cons:**
- Требует написания кода
- Нет интерактивности Claude Code

---

## Recommended Implementation Plan

### Phase 1: Infrastructure (Sonnet 4.5) - Week 1
**Tasks:** 1-10
**Model:** `claude-sonnet-4-5` (текущая)
**Approach:** Используй текущий Claude Code CLI

```bash
/model sonnet
# Execute Tasks 1-10
```

### Phase 2: Safety & Monitoring (Sonnet 4.5) - Week 2
**Tasks:** 11-17
**Model:** `claude-sonnet-4-5`
**Approach:** Продолжай с текущей моделью

```bash
/model sonnet
# Execute Tasks 11-17
```

### Phase 3: Core Components (Opus 4.6) - Week 3
**Tasks:** 21-25
**Model:** `claude-opus-4-6` ⭐
**Approach:** Переключись на Opus для сложных задач

```bash
/model opus
# Execute Tasks 21-25
```

### Phase 4: Deployment & Testing (Haiku + Opus Review) - Week 4
**Tasks:** 18-20
**Model:** `claude-haiku-4-5` для написания, `claude-opus-4-6` для review

```bash
/model haiku
# Execute Tasks 18-20

/model opus
# Review and fix issues
```

---

## Cost Optimization

### Estimated Costs (Anthropic API Pricing)

**Opus 4.6:**
- Input: $15 / 1M tokens
- Output: $75 / 1M tokens
- Estimated for Tasks 21-25: ~$50-100

**Sonnet 4.5:**
- Input: $3 / 1M tokens
- Output: $15 / 1M tokens
- Estimated for Tasks 1-17: ~$30-50

**Haiku 4.5:**
- Input: $0.25 / 1M tokens
- Output: $1.25 / 1M tokens
- Estimated for Tasks 18-20: ~$5-10

**Total Estimated Cost:** $85-160

**Savings vs All-Opus:** ~60% (All-Opus would be ~$200-300)

---

## Configuration Files to Update

### 1. Update `.planning/config.json`

```json
{
  "execution": {
    "model_strategy": "hybrid",
    "default_model": "claude-sonnet-4-5",
    "task_models": {
      "core_components": "claude-opus-4-6",
      "infrastructure": "claude-sonnet-4-5",
      "testing": "claude-haiku-4-5"
    }
  },
  "review": {
    "models": {
      "claude": "claude-opus-4-6",
      "codex": "gpt-4-turbo",
      "opencode": "copilot-gpt4"
    }
  }
}
```

### 2. Update `CLAUDE.md` (Project Instructions)

```markdown
# Model Selection Strategy

## Task-Based Model Usage

- **Tasks 1-10 (Infrastructure):** Sonnet 4.5
- **Tasks 11-17 (Safety & Monitoring):** Sonnet 4.5
- **Tasks 18-20 (Deployment):** Haiku 4.5 + Opus review
- **Tasks 21-25 (Core Components):** Opus 4.6 ⭐

## Switching Models

Use `/model <name>` in Claude Code:
- `/model opus` - For complex architecture (Tasks 21-25)
- `/model sonnet` - For standard implementation (Tasks 1-17)
- `/model haiku` - For boilerplate code (Tasks 18-20)
```

### 3. Create Task Execution Script

```bash
#!/bin/bash
# scripts/execute-with-model.sh

TASK_NUMBER=$1

if [ $TASK_NUMBER -ge 21 ] && [ $TASK_NUMBER -le 25 ]; then
    MODEL="opus"
elif [ $TASK_NUMBER -ge 18 ] && [ $TASK_NUMBER -le 20 ]; then
    MODEL="haiku"
else
    MODEL="sonnet"
fi

echo "Executing Task $TASK_NUMBER with model: $MODEL"
echo "/model $MODEL" | claude
```

---

## Action Items

### Immediate (Before Implementation)

1. ✅ **Decide on strategy** - Recommend: Option 1 (Manual model switching)
2. ⬜ **Update CLAUDE.md** with model selection guidelines
3. ⬜ **Create `.planning/config.json`** with model mapping
4. ⬜ **Test model switching** - Verify `/model opus` works
5. ⬜ **Set budget alerts** - Monitor API costs

### During Implementation

1. ⬜ **Start with Sonnet** (Tasks 1-17)
2. ⬜ **Switch to Opus** before Task 21
3. ⬜ **Use Haiku** for Tasks 18-20
4. ⬜ **Opus review** after each phase

---

## Fallback Plan

If Opus 4.6/4.7 is too expensive or unavailable:

1. **Use Sonnet 4.5 for everything** - It's still very capable
2. **Add more review cycles** - Compensate with thorough testing
3. **Use external review** - Codex/OpenCode for second opinion
4. **Iterate more** - Fix issues as they come up

---

## Conclusion

**Recommended Approach:** Hybrid model strategy with manual switching

**Why:**
- Balances quality and cost
- Uses Opus only where it matters (Tasks 21-25)
- Keeps infrastructure tasks efficient with Sonnet
- Total cost: ~$85-160 vs $200-300 for all-Opus

**Next Steps:**
1. Update CLAUDE.md with model guidelines
2. Test `/model opus` command
3. Start implementation with Sonnet (Tasks 1-17)
4. Switch to Opus for core components (Tasks 21-25)

---

**Ready to implement with optimal model selection!** 🚀
