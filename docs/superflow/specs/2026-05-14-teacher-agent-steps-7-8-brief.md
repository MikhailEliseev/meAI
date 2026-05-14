# Product Brief: Teacher Agent Steps 7-8 Completion

**Date:** 2026-05-14  
**Priority:** HIGH  
**Governance Mode:** standard  
**Git Workflow:** solo_single_pr

## Problem Statement

Teacher Agent workflow (Steps 1-6) successfully researches, clones repos, extracts skills, compares, and applies code to the project. However, Steps 7-8 are missing: the applied code is never tested, and changes are never committed. This leaves the teaching workflow incomplete and requires manual intervention.

## Jobs to be Done

When Teacher Agent completes Step 6 (apply code to codebase), I want to automatically test the applied code and commit it, so that the teaching workflow is fully autonomous and changes are persisted.

## User Stories

1. As a Teacher Agent, I want to run tests on applied code so that I can verify the code works before committing
2. As a Teacher Agent, I want to commit applied changes with a descriptive message so that the teaching session is properly documented
3. As a system operator, I want failed tests to block commits so that broken code never enters the repository
4. As a developer, I want test output in the teaching report so that I can see what was verified

## Success Criteria

- Step 7 runs pytest on applied code and captures output
- Step 8 creates git commit with teaching metadata (subagent, skill, source repo)
- Failed tests block commit and report error
- TeachingReport includes test results and commit hash
- End-to-end teaching workflow completes without manual intervention

## Edge Cases

1. **Tests fail:** Capture failure output, set `success=False`, do NOT commit, include error in report
2. **No tests exist:** Skip test execution, proceed to commit with warning in report
3. **Git commit fails:** Capture error, set `success=False`, include error in report
4. **Applied code has no changes:** Skip commit, mark as success with note in report

## Out of Scope

- Test generation (handled by SkillApplier in Step 6)
- Test fixing (manual intervention required if tests fail)
- Multiple commit strategies (single commit per teaching session)
- Rollback on test failure (manual git reset if needed)
