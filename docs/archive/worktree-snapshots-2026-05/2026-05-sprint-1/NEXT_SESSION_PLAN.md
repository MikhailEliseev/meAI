# 🚀 План следующей сессии: Vault Operations + Teacher Agent

**Дата создания:** 2026-05-09 01:58 GMT+3  
**Для сессии:** 2026-05-10 (завтра)  
**Подход:** Superflow (Phase 1 → Phase 2)

---

## 🎯 Цель сессии

Реализовать операции для Obsidian vaults (Ingest, Query, Lint) и создать Teacher Agent для обучения Magisters.

---

## 📋 Задачи (приоритизированы)

### Priority 1: Vault Operations Implementation

**Goal:** Implement three core operations for LLM Wiki Pattern

#### Task 1.1: Ingest Operation
**Description:** Process raw sources → create wiki pages

**Requirements:**
- Read files from raw/
- Analyze content and categorize (concepts/technologies/strategies/etc.)
- Generate wiki pages with frontmatter (status: processed)
- Update wiki/index.md
- Log operation in wiki/log.md

**Acceptance criteria:**
- Raw source processed and moved to appropriate wiki category
- Wiki page has proper frontmatter
- index.md updated with new page
- log.md has operation entry

#### Task 1.2: Query Operation
**Description:** Answer questions using wiki → create new wiki pages

**Requirements:**
- Search existing wiki pages
- Answer question using wiki content
- Create new wiki page with answer + citations
- Update wiki/index.md
- Log operation in wiki/log.md

**Acceptance criteria:**
- Question answered using wiki content
- New wiki page created with citations
- index.md updated
- log.md has operation entry

#### Task 1.3: Lint Operation
**Description:** Check vault health

**Requirements:**
- Check for contradictions between wiki pages
- Find orphaned pages (not linked from index.md)
- Detect gaps in knowledge
- Identify stale data (old timestamps)
- Generate health report

**Acceptance criteria:**
- Health report generated
- Issues categorized (critical/warning/info)
- Recommendations provided
- log.md has operation entry

---

### Priority 2: Teacher Agent

**Goal:** Create Teacher Agent for knowledge transfer from Architect to Magisters

#### Task 2.1: Teacher Agent Implementation
**Description:** Agent that collects knowledge from Architect and teaches Magisters

**Requirements:**
- Collect strategic decisions from Architect vault
- Identify relevant knowledge for each Magister domain
- Transfer knowledge to Magister vaults (via Ingest operation)
- Track teaching sessions
- Measure knowledge transfer effectiveness

**Acceptance criteria:**
- Teacher Agent class implemented
- Knowledge collection from Architect works
- Knowledge transfer to Magisters works
- Teaching sessions logged
- Integration tests pass

---

## 🔄 Superflow Workflow

### Phase 0: Onboarding (if needed)
- Detect project state
- Analyze codebase
- Generate health report
- Setup environment

### Phase 1: Discovery (with user)
**Steps:**
1. Context gathering
2. Governance Mode selection (standard recommended)
3. Git Workflow Mode selection (feature branches recommended)
4. Research (parallel agents for vault operations + teacher agent)
5. Brainstorm approaches
6. Product approval
7. Spec creation
8. Spec review (dual-model)
9. Plan creation
10. Plan review (dual-model)
11. User approval
12. Charter creation

### Phase 2: Execution (autonomous)
**Per sprint:**
1. Re-read charter
2. Telegram notification (if available)
3. Create worktree
4. Run baseline tests
5. Dispatch implementers (parallel waves)
6. Unified review (2 agents)
7. Test verification
8. Push + PR
9. Cleanup
10. Telegram notification

### Phase 3: Merge (user-initiated)
1. Pre-merge checklist
2. Doc update
3. Sequential rebase merge
4. Post-merge report

---

## 📊 Estimated Effort

**Vault Operations:**
- Ingest: 2-3 hours (medium complexity)
- Query: 2-3 hours (medium complexity)
- Lint: 1-2 hours (low complexity)

**Teacher Agent:**
- Implementation: 3-4 hours (high complexity)
- Integration: 1-2 hours (medium complexity)

**Total:** 9-14 hours (можно разбить на 2-3 сессии)

---

## 🎯 Success Criteria

### Vault Operations
✅ Ingest operation works for all 13 vaults
✅ Query operation creates wiki pages with citations
✅ Lint operation generates health reports
✅ All operations log to wiki/log.md
✅ Integration tests pass

### Teacher Agent
✅ Teacher Agent collects knowledge from Architect
✅ Knowledge transferred to Magisters
✅ Teaching sessions logged
✅ Integration with vault operations works
✅ Tests pass

---

## 🔧 Technical Stack

**Language:** Python 3.11+  
**Framework:** meAI (existing)  
**Components:**
- VaultOperations class (Ingest, Query, Lint)
- TeacherAgent class (extends BaseAgent)
- Integration with EventBus + EventStore
- Obsidian vault integration

**Testing:**
- Unit tests for each operation
- Integration tests for Teacher Agent
- End-to-end tests for full workflow

---

## 📝 Deliverables

**Code:**
- `src/meai/memory/vault_operations.py` (Ingest, Query, Lint)
- `src/meai/agents/teacher_agent.py` (Teacher Agent)
- `tests/memory/test_vault_operations.py` (unit tests)
- `tests/agents/test_teacher_agent.py` (unit tests)
- `tests/integration/test_teacher_vault_integration.py` (integration tests)

**Documentation:**
- `docs/vault-operations.md` (operations guide)
- `docs/teacher-agent.md` (teacher agent guide)
- Updated `SESSION.md`
- Completion report

---

## 🚀 Quick Start (для следующей сессии)

```bash
# 1. Восстановить контекст
cat SESSION.md
cat SESSION_COMPLETE_2026-05-09.md

# 2. Запустить Superflow
/superflow

# 3. Следовать Phase 1 (Discovery)
# - Выбрать Governance Mode: standard
# - Выбрать Git Workflow: feature branches
# - Пройти все 13 шагов до Charter

# 4. Запустить Phase 2 (Execution)
# - Autonomous execution
# - Parallel implementers
# - Unified review
# - Tests + PR

# 5. Завершить Phase 3 (Merge)
# - Pre-merge checklist
# - Rebase merge
# - Post-merge report
```

---

## 📌 Notes

**Context from previous session:**
- Event Store implemented ✅
- Magisters integrated ✅
- Vaults restructured ✅
- All tests passing ✅

**Ready to use:**
- EventBus (async messaging)
- EventStore (audit log)
- BaseMagister (with EventStore)
- 13 vaults (LLM Wiki Pattern)

**Next steps:**
- Implement vault operations
- Create Teacher Agent
- Test end-to-end workflow

---

**Создано:** 2026-05-09 01:58 GMT+3  
**Статус:** READY FOR NEXT SESSION  
**Подход:** Superflow (autonomous execution)

🚀 Готово к запуску!
