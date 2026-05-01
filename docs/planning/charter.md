# meAI Core Foundation - Execution Charter

**Date:** 2026-05-01T18:15:45Z  
**Status:** APPROVED - Ready for Execution  
**Phase:** 2 (Execution)

---

## Charter Approval

**Approved by:** User  
**Approved at:** 2026-05-01T18:15:33Z  
**Plan Version:** v1.1  
**Governance Mode:** Critical

---

## Execution Parameters

**Timeline:** 6-7 weeks  
**Start Date:** 2026-05-01  
**Target Completion:** 2026-06-12 to 2026-06-19  
**Tasks:** 24 tasks across 6 sprints + buffer  
**Model Strategy:** Hybrid (Sonnet + Opus + Haiku)  
**Budget:** $95-180

---

## Sprint Schedule

| Sprint | Duration | Tasks | Model | Deliverable |
|--------|----------|-------|-------|-------------|
| 1A | Week 1 (5d) | 1-4 | Sonnet | Foundation |
| 1B | Week 1.5 (3-4d) | 5-6 | Opus | Event System |
| 2 | Week 2-2.5 (5-7d) | 8-14 | Sonnet | Agent Factory & Safety |
| 3 | Week 3 (5d) | 7, 15-17 | Sonnet | Monitoring |
| 4 | Week 4 (5d) | 18, 21-22 | Opus | FastAPI + Core Start |
| 5 | Week 5 (5d) | 23-25 | Opus | Core Complete |
| 6 | Week 6 (5d) | 19-20 | Haiku/Sonnet | Deployment & E2E |
| Buffer | Week 7 (3-5d) | - | - | Integration & Polish |

---

## Success Criteria (MVP)

1. [ ] meAI can create AIM structure
2. [ ] Agent Factory works
3. [ ] Event Bus works
4. [ ] Monitoring shows status
5. [ ] Rollback works
6. [ ] Safety mechanisms work
7. [ ] Secrets management
8. [ ] Automated backups
9. [ ] Rate limiting
10. [ ] Graceful shutdown
11. [ ] Testing infrastructure (> 80%)
12. [ ] Deployment strategy
13. [ ] Alerting system

---

## Key Decisions Locked

1. ✅ Event Store vs Event Bus - Separate concerns (see event-sourcing-design.md)
2. ✅ Task 10/24 merged - System Registry in Sprint 2
3. ✅ FastAPI moved to Sprint 4 - Before Decision Maker needs it
4. ✅ Opus for Tasks 5-6 - Event sourcing complexity
5. ✅ Timeline 6-7 weeks - Realistic with TDD
6. ✅ Telegram optional - Falls back to logging

---

## Reference Documents

**Planning:**
- Brief: `.superflow/brief.md`
- Spec v1.1: `docs/planning/spec-v1.1.md`
- Event Sourcing Design: `docs/planning/event-sourcing-design.md`
- Plan v1.1: `docs/planning/plan-v1.1.md`

**Archive:**
- Original Plan: `docs/superpowers/archive/v1.0-2026-05-01/2026-05-01-meai-core-foundation-plan.md`

---

## Execution Rules

1. **TDD Approach:** Test first, implement, verify
2. **Atomic Commits:** One task = one commit
3. **Sprint Reviews:** After each sprint (dual-model in Critical mode)
4. **Integration Tests:** 0.5-1 day per sprint
5. **User Approval:** After each sprint
6. **Context Compaction:** After Sprint 2 and Sprint 4

---

## Next Action

**Start Sprint 1A (Week 1):**
- Model: Sonnet 4.5
- Tasks: 1-4 (Setup, Config, Database, Obsidian)
- Duration: 5 days
- First Task: Task 1 (already done - dependencies added)
- Next Task: Task 2 (Configuration Management)

---

**Charter Locked:** 2026-05-01T18:15:45Z  
**Ready to Execute:** YES ✅
