# Инструкция для продолжения Plan 1 в новой сессии

**Дата:** 2026-05-02  
**Статус:** План 1 частично завершён, нужно дописать Tasks 10-15 с полным детальным кодом

---

## Что уже сделано

✅ **Spec готов:** `docs/superpowers/specs/2026-05-02-university-knowledge-system-design.md`

✅ **Plan 1 частично готов:**
- Tasks 1-5: Полный детальный код (Infrastructure: Qdrant, Embeddings, Fallback Storage)
- Tasks 6-8: Полный детальный код (API Integrations: Perplexity, YouTube, Telegram)
- Task 9: Полный детальный код (Researcher Agent)

⏳ **Нужно дописать Tasks 10-15 с полным детальным кодом:**
- Task 10: Teacher Agent - Core (evaluation, storage)
- Task 11: Teacher Agent - Search & Distribution
- Task 12: Integration Test - Researcher → Teacher
- Task 13: Integration Test - Qdrant Fallback
- Task 14: Setup Script (Qdrant collections)
- Task 15: End-to-End Test

---

## Файлы с готовыми задачами

Детальный код для Tasks 6-9 находится в:
- `/tmp/plan_tasks_6_8.md` (Tasks 6-8: API integrations)
- `/tmp/plan_task_9.md` (Task 9: Researcher Agent)

Backup текущего плана:
- `docs/superpowers/plans/2026-05-02-university-infrastructure-core.md.backup`

---

## Что нужно сделать в новой сессии

### Шаг 1: Создать Tasks 10-11 (Teacher Agent) с полным кодом

**Task 10: Teacher Agent - Core**

Структура (как Task 9):
- Step 1: Write failing test for Teacher initialization
- Step 2: Run test to verify it fails
- Step 3: Write Teacher Agent implementation
  - Inherits from `Agent` base class
  - Capabilities: `evaluate_knowledge`, `store_knowledge`, `distribute_to_magisters`, `search_knowledge`
  - Uses: `QdrantClient`, `EmbeddingsModel`, `FallbackStorage`
  - Database tables: `teacher_knowledge`, `teacher_evaluations`, `teacher_distributions`
- Step 4-8: Tests for each capability
- Step 9: Commit

**Ключевые методы Teacher:**

```python
async def evaluate_knowledge(self, knowledge: dict) -> float:
    """Evaluate knowledge quality (1-10)
    
    Factors:
    - Source authority (trusted domains = higher score)
    - Content length (too short = lower score)
    - Has citations (with citations = higher score)
    """
    score = 5.0  # base
    
    # Source authority
    if knowledge.get("source_trusted"):
        score += 2.0
    
    # Content quality
    content_length = len(knowledge.get("content", ""))
    if content_length > 500:
        score += 1.0
    
    # Has citations
    if len(knowledge.get("sources", [])) > 0:
        score += 2.0
    
    return min(score, 10.0)


async def store_knowledge(self, knowledge: dict) -> str:
    """Store knowledge in Qdrant (or fallback to SQLite)
    
    Steps:
    1. Generate embeddings via EmbeddingsModel
    2. Try to store in Qdrant
    3. If Qdrant fails → store in FallbackStorage
    4. Return knowledge ID
    """
    # Generate embeddings
    vector = await self.embeddings.encode(knowledge["content"])
    
    try:
        # Try Qdrant
        point = PointStruct(
            id=knowledge_id,
            vector=vector,
            payload={
                "content": knowledge["content"],
                "source": knowledge["source"],
                "quality_score": knowledge["quality_score"],
                # ... metadata
            }
        )
        await self.qdrant.upsert_points(collection, [point])
    
    except Exception:
        # Fallback to SQLite
        await self.fallback.store_knowledge({
            "content": knowledge["content"],
            "vector": vector,
            "collection": collection,
            # ... metadata
        })
```

**Task 11: Teacher Agent - Search & Distribution**

Добавить методы:
- `search_knowledge(query, collection, limit)` — vector search
- `handle_magister_query(query)` — handle Magister questions
- `request_research(topic)` — request Researcher via Event Bus

---

### Шаг 2: Создать Tasks 12-13 (Integration Tests) с полным кодом

**Task 12: Integration Test - Researcher → Teacher**

```python
@pytest.mark.asyncio
async def test_researcher_teacher_flow():
    """Test full flow: Researcher → Teacher → Qdrant"""
    
    # 1. Start Qdrant (assume running)
    # 2. Initialize Researcher and Teacher
    # 3. Teacher requests research
    # 4. Researcher finds knowledge (mocked Perplexity)
    # 5. Researcher sends to Teacher via Event Bus
    # 6. Teacher evaluates and stores in Qdrant
    # 7. Verify knowledge in Qdrant
```

**Task 13: Integration Test - Qdrant Fallback**

```python
@pytest.mark.asyncio
async def test_qdrant_fallback():
    """Test fallback to SQLite when Qdrant unavailable"""
    
    # 1. Normal: Qdrant available, store succeeds
    # 2. Fallback: Stop Qdrant, store goes to SQLite
    # 3. Recovery: Start Qdrant, sync from SQLite
```

---

### Шаг 3: Создать Tasks 14-15 (Scripts) с полным кодом

**Task 14: Setup Script**

```python
# scripts/setup_qdrant.py
"""Initialize Qdrant collections"""

async def main():
    # Connect to Qdrant
    # Create 6 collections (seo, content, ads, smm, analytics, intelligence)
    # Set vector size = 1024 (bge-m3)
    # Set distance = COSINE
```

**Task 15: End-to-End Test**

```python
# scripts/test_university_core.py
"""Complete E2E test"""

async def main():
    # 1. Initialize all components
    # 2. Research → Teacher → Qdrant
    # 3. Search knowledge
    # 4. Test fallback
    # Print results with ✅/❌
```

---

### Шаг 4: Объединить всё в один файл

```bash
# Объединить все части
cat docs/superpowers/plans/2026-05-02-university-infrastructure-core.md.backup \
    | head -n 850 > /tmp/plan_full.md  # Tasks 1-5

cat /tmp/plan_tasks_6_8.md >> /tmp/plan_full.md  # Tasks 6-8
cat /tmp/plan_task_9.md >> /tmp/plan_full.md     # Task 9
cat /tmp/plan_tasks_10_15.md >> /tmp/plan_full.md  # Tasks 10-15 (новые)

# Заменить старый план
mv /tmp/plan_full.md docs/superpowers/plans/2026-05-02-university-infrastructure-core.md
```

---

### Шаг 5: Commit

```bash
git add docs/superpowers/plans/2026-05-02-university-infrastructure-core.md
git commit -m "docs: complete Plan 1 with full detailed code for all 15 tasks

Plan 1: University Infrastructure + Core (COMPLETE)

All tasks now have full TDD implementation with:
- Complete test code
- Complete implementation code
- Step-by-step instructions
- Expected outputs
- Commit messages

Tasks 1-5: Infrastructure (Qdrant, Embeddings, Fallback)
Tasks 6-8: API Integrations (Perplexity, YouTube, Telegram)
Task 9: Researcher Agent
Tasks 10-11: Teacher Agent (Core + Search)
Tasks 12-13: Integration Tests
Tasks 14-15: Setup + E2E Test

Ready for execution via subagent-driven-development or executing-plans.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Принцип "Deep & Correct"

**Важно:** Каждая задача (10-15) должна иметь:
- ✅ Полный код тестов (не "write tests", а реальный код)
- ✅ Полный код реализации (не "implement X", а реальный код)
- ✅ Пошаговые инструкции с командами
- ✅ Ожидаемые результаты
- ❌ Никаких "TBD", "TODO", "implement later"
- ❌ Никаких "similar to Task N" без кода

**Формат как в Tasks 1-9:**
- Step 1: Write failing test (с полным кодом теста)
- Step 2: Run test (с командой и ожидаемым выводом)
- Step 3: Write implementation (с полным кодом)
- Step 4: Run test (с командой и ожидаемым выводом)
- Step 5-8: Дополнительные тесты (с полным кодом)
- Step 9: Commit (с полным commit message)

---

## Контекст для новой сессии

**Проект:** meAI - CEO-архитектор для AIM агентства  
**Философия:** Deep & Correct - делаем всё глубоко и правильно, без спешки  
**Текущая задача:** Завершить Plan 1 с полным детальным кодом для Tasks 10-15  

**Spec:** `docs/superpowers/specs/2026-05-02-university-knowledge-system-design.md`  
**Plan (частичный):** `docs/superpowers/plans/2026-05-02-university-infrastructure-core.md`  

**Следующие планы:**
- Plan 2: Magisters + Hybrid Search
- Plan 3: Experience Learning

---

## Команда для продолжения

Скопируй этот текст в новую сессию:

```
Продолжаю работу над Plan 1 для University Infrastructure + Core.

Контекст:
- Tasks 1-9 готовы с полным детальным кодом
- Нужно дописать Tasks 10-15 с таким же уровнем детализации
- Принцип: "Deep & Correct" - полный код, никаких placeholders
- Инструкция: docs/superpowers/plans/CONTINUE-PLAN-1.md

Начинаю с Task 10: Teacher Agent - Core.
```

---

**Удачи в новой сессии! 🚀**
