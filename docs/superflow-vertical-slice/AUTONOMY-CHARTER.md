# Autonomy Charter: SEO Analysis Workflow

**Project:** SEO Analysis Workflow (Vertical Slice)  
**Phase:** 2 (Execution)  
**Approved:** 2026-05-09T12:31:00Z  
**Valid Until:** Sprint 4 completion or user intervention

---

## Mission

Implement complete end-to-end SEO Analysis workflow from user request to final report, following PLAN.md v1.1 specifications with full autonomy during execution.

---

## Scope of Autonomy

### ✅ Autonomous Actions (No Approval Needed)

**Code Implementation:**
- Create all files specified in PLAN.md v1.1
- Implement all agents (Technical, Content, Links)
- Implement SEO Magister coordination logic
- Update Operator with routing logic
- Write all unit, integration, and e2e tests
- Fix bugs discovered during testing
- Refactor code for quality improvements

**Git Operations:**
- Create feature branches per sprint
- Commit changes with descriptive messages
- Push branches to remote
- Create pull requests with descriptions
- Rebase branches as needed (stacked PRs workflow)

**Testing:**
- Run unit tests after each implementation
- Run integration tests after Event Bus integration
- Run e2e test after Sprint 4
- Fix failing tests
- Add missing test coverage

**Documentation:**
- Update code comments and docstrings
- Create workflow documentation
- Update Obsidian vaults with results
- Maintain CHECKPOINT files

**Dependencies:**
- Install required packages (aiohttp, beautifulsoup4, lxml, textstat)
- Update requirements.txt
- Verify compatibility

**Database:**
- Create seo_reports table migration
- Run migration scripts
- Verify schema

### ⚠️ Requires User Approval

**Architecture Changes:**
- Deviations from PLAN.md v1.1 structure
- Adding new components not in plan
- Changing coordination patterns
- Modifying Event Bus behavior

**External Services:**
- Adding new API dependencies
- Changing API providers
- Modifying rate limits beyond plan

**Scope Changes:**
- Adding features beyond PLAN.md v1.1
- Removing planned features
- Changing sprint boundaries
- Extending timeline beyond 2 weeks

**Production Impact:**
- Merging to main branch (after PR review)
- Deploying to production
- Modifying existing production code outside scope

---

## Decision Authority

### Technical Decisions (Autonomous)

**Implementation Details:**
- Class structure and method signatures
- Error handling patterns
- Logging strategies
- Test structure and mocking
- Code organization within files

**Quality Standards:**
- Code style (follow existing patterns)
- Test coverage (80%+ target)
- Performance optimizations
- Security best practices

**Tooling:**
- Development tools and utilities
- Testing frameworks (pytest)
- Linting and formatting (ruff, mypy)

### Strategic Decisions (Requires Approval)

**Scope:**
- Feature additions/removals
- Timeline changes
- Resource allocation changes

**Architecture:**
- Pattern changes (event-driven → other)
- Component additions (new Magisters, etc.)
- Integration changes (Event Bus → other)

**Risk:**
- Breaking changes to existing code
- Data migration strategies
- Rollback procedures

---

## Quality Gates

### Per Sprint (Autonomous Verification)

**Before PR Creation:**
- [ ] All unit tests pass (80%+ coverage)
- [ ] All integration tests pass
- [ ] Code follows project conventions
- [ ] No linting errors (ruff check)
- [ ] Type checking passes (mypy)
- [ ] Documentation updated

**PR Description Must Include:**
- Summary of changes
- Files created/modified
- Test results
- Breaking changes (if any)
- Next steps

### Sprint 4 (Final Gate - User Approval Required)

**Before Merge to Main:**
- [ ] All 4 sprints complete
- [ ] End-to-end test passes (< 10 minutes)
- [ ] Manual testing on real websites complete
- [ ] All events logged in Event Store
- [ ] Documentation complete
- [ ] User reviews and approves final PR

---

## Communication Protocol

### Checkpoints (Every Sprint)

**After Each Sprint:**
- Create CHECKPOINT-N.md with:
  - Sprint summary
  - Files created/modified
  - Test results
  - Issues encountered
  - Next sprint preview
- Update SESSION.md
- Update .superflow-state.json

### Progress Updates (As Needed)

**When to Report:**
- Sprint completion
- Blocking issues discovered
- Deviations from plan needed
- Quality gate failures
- Timeline concerns

**Update Format:**
- Brief summary (2-3 sentences)
- Current status
- Next actions
- ETA if changed

### Escalation (Immediate)

**Report Immediately If:**
- Cannot proceed without architectural change
- Discovered critical security issue
- Tests consistently failing (> 3 attempts)
- Timeline will exceed 2 weeks
- External dependency unavailable

---

## Sprint Execution Plan

### Sprint 1: Technical SEO Agent (Days 1-3)

**Autonomous Actions:**
1. Create branch `feat/seo-vertical-slice/sprint-1-technical-agent`
2. Implement `AIM/src/aim/subagents/seo/technical_agent.py`
3. Implement PageSpeed API integration (with Lighthouse fallback)
4. Implement robots.txt, sitemap, meta tags, schema parsing
5. Write unit tests (80%+ coverage)
6. Write integration test with Event Bus
7. Run all tests, fix failures
8. Create PR with description
9. Create CHECKPOINT-5.md

**Quality Gate:**
- All tests pass
- Code follows conventions
- No linting/type errors

**Deliverable:**
- Working Technical SEO Agent
- Tests passing
- PR ready for review

---

### Sprint 2: Content SEO Agent (Days 4-6)

**Autonomous Actions:**
1. Create branch `feat/seo-vertical-slice/sprint-2-content-agent` (base: sprint-1)
2. Implement `AIM/src/aim/subagents/seo/content_agent.py`
3. Implement header analysis, keyword density, readability scoring
4. Write unit tests (80%+ coverage)
5. Write integration test with Event Bus
6. Run all tests, fix failures
7. Create PR with description
8. Create CHECKPOINT-6.md

**Quality Gate:**
- All tests pass
- Code follows conventions
- No linting/type errors

**Deliverable:**
- Working Content SEO Agent
- Tests passing
- PR ready for review

---

### Sprint 3: Links SEO Agent (Days 7-9)

**Autonomous Actions:**
1. Create branch `feat/seo-vertical-slice/sprint-3-links-agent` (base: sprint-2)
2. Implement `AIM/src/aim/subagents/seo/links_agent.py`
3. Implement internal/external links, broken links detection, anchor analysis
4. Write unit tests (80%+ coverage)
5. Write integration test with Event Bus
6. Run all tests, fix failures
7. Create PR with description
8. Create CHECKPOINT-7.md

**Quality Gate:**
- All tests pass
- Code follows conventions
- No linting/type errors

**Deliverable:**
- Working Links SEO Agent
- Tests passing
- PR ready for review

---

### Sprint 4: Operator Coordination (Days 10-14)

**Autonomous Actions:**
1. Create branch `feat/seo-vertical-slice/sprint-4-coordination` (base: sprint-3)
2. Update `AIM/src/aim/magisters/seo_magister.py`:
   - Implement `coordinate_analysis()` method
   - Implement `dispatch_subagents()` (parallel with asyncio.gather)
   - Implement `collect_results()` with timeout
   - Implement `aggregate_results()` with scoring formula
3. Update `src/meai/agents/operator.py`:
   - Add Magister registry
   - Implement `route_task()` with pattern matching
4. Create `AIM/src/aim/models/seo_report.py`
5. Create database migration (seo_reports table)
6. Implement Obsidian report generation (LLM Wiki format)
7. Write end-to-end test
8. Run all tests (unit + integration + e2e)
9. Manual testing on real websites
10. Create PR with description
11. Create CHECKPOINT-8.md

**Quality Gate:**
- All tests pass (unit + integration + e2e)
- E2E test completes in < 10 minutes
- Manual testing successful
- All events logged in Event Store
- Documentation complete

**Deliverable:**
- Complete SEO Analysis workflow
- All tests passing
- Documentation complete
- PR ready for final review

**User Approval Required:**
- Review final PR
- Approve merge to main

---

## Success Criteria

### Technical Success
- [ ] All 4 sprints complete
- [ ] All unit tests pass (80%+ coverage)
- [ ] All integration tests pass
- [ ] End-to-end test passes (< 10 minutes)
- [ ] No linting/type errors
- [ ] All events logged in Event Store

### Business Success
- [ ] User can request "Analyze SEO: example.com"
- [ ] System delivers comprehensive report
- [ ] Report provides actionable insights
- [ ] Quality comparable to manual analysis
- [ ] Can be shown to potential clients

### Quality Success
- [ ] Deep analysis (50+ data points)
- [ ] No silent failures
- [ ] Proper error handling
- [ ] Comprehensive logging
- [ ] LLM Wiki compliant reports

---

## Risk Management

### Known Risks (From PLAN.md)

**Risk 1: API Rate Limits**
- Mitigation: Free tier (100/day), rate limiting, retry logic, caching
- Autonomous: Implement all mitigations
- Escalate: If rate limits consistently exceeded

**Risk 2: Coordination Complexity**
- Mitigation: Start synchronous, comprehensive tests, mock Magisters
- Autonomous: Implement as planned
- Escalate: If coordination pattern doesn't work

**Risk 3: Performance**
- Mitigation: Quality over speed (10 min OK), parallel execution, timeouts, partial success
- Autonomous: Implement all mitigations
- Escalate: If consistently exceeds 10 minutes

**Risk 4: Data Quality**
- Mitigation: Validate data, handle missing data, partial results, error logging
- Autonomous: Implement all mitigations
- Escalate: If data quality consistently poor

---

## Constraints

### Time
- **Hard deadline:** 2 weeks from start
- **Sprint duration:** 2-3 days each
- **Buffer:** 2 days for integration testing

### Quality
- **Test coverage:** 80%+ minimum
- **Performance:** < 10 minutes per analysis
- **Code quality:** No linting/type errors
- **Documentation:** Complete and up-to-date

### Scope
- **Fixed:** 3 subagents + coordination (no additions)
- **Fixed:** Event-driven architecture (no changes)
- **Fixed:** SQLite database (no changes)
- **Fixed:** Stacked PRs workflow (no changes)

---

## Termination Conditions

### Automatic Termination

**Charter expires when:**
- Sprint 4 complete and final PR merged
- User explicitly terminates
- 2-week deadline exceeded
- Critical blocker cannot be resolved

### User Can Terminate If:
- Quality standards not met
- Timeline concerns
- Scope changes needed
- Architecture changes needed

---

## Approval

**Approved by:** User  
**Date:** 2026-05-09T12:31:00Z  
**Valid for:** Phase 2 Execution (Sprints 1-4)

**Charter Status:** ✅ ACTIVE

---

## Next Action

Begin Sprint 1: Technical SEO Agent implementation.
