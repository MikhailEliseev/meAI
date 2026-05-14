# Implementation Plan: Teacher Agent Steps 7-8

**Date:** 2026-05-14  
**Brief:** docs/superflow/specs/2026-05-14-teacher-agent-steps-7-8-brief.md  
**Spec:** docs/superflow/specs/2026-05-14-teacher-agent-steps-7-8-design.md  
**Governance:** standard  
**Git Workflow:** solo_single_pr

## Overview

Complete Teacher Agent teaching workflow by implementing Steps 7 (test execution) and 8 (git commit). This makes the teaching workflow fully autonomous from research to commit.

## Sprint Breakdown

### Sprint 1: Core Implementation (60-90 min)

**Goal:** Implement Steps 7-8 in skill_teacher.py with full error handling

**Tasks:**
1. Add new dataclasses (TestResults, CommitResult) to skill_teacher.py
2. Implement _run_tests() method with pytest execution
3. Implement _commit_changes() method with git operations
4. Update teach_subagent() to call Steps 7-8
5. Update TeachingReport to include test_results field

**Files Modified:**
- `AIM/src/aim/teacher/skills/skill_teacher.py` (~100 lines added)

**Acceptance Criteria:**
- TestResults and CommitResult dataclasses defined
- _run_tests() executes pytest and captures output
- _commit_changes() creates git commit with metadata
- teach_subagent() calls both methods in sequence
- Failed tests block commit
- No changes = skip commit gracefully

### Sprint 2: Testing (45-60 min)

**Goal:** Add comprehensive test coverage for Steps 7-8

**Tasks:**
1. Add unit tests for _run_tests() (3 test cases)
2. Add unit tests for _commit_changes() (2 test cases)
3. Add integration test for full workflow (1 test case)
4. Verify all tests pass

**Files Modified:**
- `AIM/tests/teacher/skills/test_skill_teacher.py` (~200 lines added)

**New Files:**
- `AIM/tests/teacher/skills/test_skill_teacher_integration.py` (~100 lines)

**Acceptance Criteria:**
- test_run_tests_success passes
- test_run_tests_failure passes
- test_run_tests_no_files passes
- test_commit_changes_success passes
- test_commit_changes_no_files passes
- test_teach_subagent_end_to_end passes
- All existing tests still pass

## Implementation Details

### Sprint 1: Core Implementation

#### Task 1: Add Dataclasses

Location: Top of `AIM/src/aim/teacher/skills/skill_teacher.py`

```python
@dataclass
class TestResults:
    """Results of test execution."""
    success: bool
    summary: str
    output: str
    failures: list[str] = field(default_factory=list)

@dataclass
class CommitResult:
    """Result of git commit."""
    success: bool
    commit_hash: str | None
    message: str = ""
    error: str | None = None
```

Update TeachingReport:
```python
@dataclass
class TeachingReport:
    # ... existing fields ...
    test_results: TestResults | None = None  # NEW
    commit_hash: str | None = None           # EXISTING
```

#### Task 2: Implement _run_tests()

```python
async def _run_tests(
    self, 
    test_files: list[Path], 
    subagent_name: str
) -> TestResults:
    """Run pytest on applied code."""
    
    if not test_files:
        return TestResults(
            success=True,
            summary="No tests to run",
            output=""
        )
    
    # Run pytest
    cmd = f"pytest {' '.join(str(f) for f in test_files)} -v"
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        timeout=300
    )
    
    return TestResults(
        success=result.returncode == 0,
        summary=f"{len(test_files)} test files",
        output=result.stdout + result.stderr,
        failures=[] if result.returncode == 0 else ["pytest failed"]
    )
```

#### Task 3: Implement _commit_changes()

```python
async def _commit_changes(
    self,
    files_created: list[Path],
    files_modified: list[Path],
    subagent_name: str,
    skill_name: str,
    source_repo: str
) -> CommitResult:
    """Commit applied changes with teaching metadata."""
    
    all_files = files_created + files_modified
    
    if not all_files:
        return CommitResult(
            success=True,
            commit_hash=None,
            message="No changes to commit"
        )
    
    # Stage files
    for file in all_files:
        subprocess.run(["git", "add", str(file)], check=True)
    
    # Create commit message
    message = f"""teach({subagent_name}): apply {skill_name}

Taught {subagent_name} with skill from {source_repo}

Files created: {len(files_created)}
Files modified: {len(files_modified)}

Source: {source_repo}
Skill: {skill_name}

Co-Authored-By: Teacher Agent <teacher@aim.ai>"""
    
    # Commit
    result = subprocess.run(
        ["git", "commit", "-m", message],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        return CommitResult(
            success=False,
            commit_hash=None,
            error=result.stderr
        )
    
    # Get commit hash
    hash_result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True
    )
    
    return CommitResult(
        success=True,
        commit_hash=hash_result.stdout.strip(),
        message=message
    )
```

#### Task 4: Update teach_subagent()

Add after Step 6 (application):

```python
# Step 7: Test
self.logger.info("step_7_test")

test_results = await self._run_tests(
    test_files=application.tests_created,
    subagent_name=subagent_name
)

report.test_results = test_results

if not test_results.success:
    self.logger.error("tests_failed", failures=test_results.failures)
    report.error = f"Tests failed: {test_results.summary}"
    return report

# Step 8: Commit
self.logger.info("step_8_commit")

commit_result = await self._commit_changes(
    files_created=application.files_created,
    files_modified=application.files_modified,
    subagent_name=subagent_name,
    skill_name=report.best_skill.name if report.best_skill else "unknown",
    source_repo=report.best_skill.source_repo if report.best_skill else "unknown"
)

report.commit_hash = commit_result.commit_hash

if not commit_result.success:
    self.logger.error("commit_failed", error=commit_result.error)
    report.error = f"Commit failed: {commit_result.error}"
    return report

report.success = True
```

### Sprint 2: Testing

#### Unit Tests for _run_tests()

File: `AIM/tests/teacher/skills/test_skill_teacher.py`

```python
@pytest.mark.asyncio
async def test_run_tests_success(teacher, tmp_path):
    """Should run pytest and return success."""
    test_file = tmp_path / "test_dummy.py"
    test_file.write_text("def test_pass(): assert True")
    
    result = await teacher._run_tests([test_file], "test")
    
    assert result.success
    assert "test_dummy.py" in result.output

@pytest.mark.asyncio
async def test_run_tests_failure(teacher, tmp_path):
    """Should capture test failures."""
    test_file = tmp_path / "test_dummy.py"
    test_file.write_text("def test_fail(): assert False")
    
    result = await teacher._run_tests([test_file], "test")
    
    assert not result.success
    assert len(result.failures) > 0

@pytest.mark.asyncio
async def test_run_tests_no_files(teacher):
    """Should handle no test files gracefully."""
    result = await teacher._run_tests([], "test")
    
    assert result.success
    assert "No tests" in result.summary
```

#### Unit Tests for _commit_changes()

```python
@pytest.mark.asyncio
async def test_commit_changes_success(teacher, tmp_path):
    """Should create git commit with metadata."""
    # Setup git repo
    subprocess.run(["git", "init"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    
    # Create file
    test_file = tmp_path / "test.py"
    test_file.write_text("# test")
    
    result = await teacher._commit_changes(
        files_created=[test_file],
        files_modified=[],
        subagent_name="test",
        skill_name="test_skill",
        source_repo="github.com/test/repo"
    )
    
    assert result.success
    assert result.commit_hash is not None
    assert "teach(test)" in result.message

@pytest.mark.asyncio
async def test_commit_changes_no_files(teacher):
    """Should handle no changes gracefully."""
    result = await teacher._commit_changes(
        files_created=[],
        files_modified=[],
        subagent_name="test",
        skill_name="test_skill",
        source_repo="github.com/test/repo"
    )
    
    assert result.success
    assert result.commit_hash is None
```

#### Integration Test

File: `AIM/tests/teacher/skills/test_skill_teacher_integration.py`

```python
@pytest.mark.asyncio
async def test_teach_subagent_end_to_end(tmp_path):
    """Test complete teaching workflow Steps 1-8."""
    # Setup
    teacher = SkillTeacher(project_root=tmp_path)
    
    # Mock GitHub repos (Steps 1-2)
    # Mock skill extraction (Step 3)
    # Mock comparison (Step 4)
    # Mock application (Step 6)
    
    # Execute
    report = await teacher.teach_subagent("test", "test domain")
    
    # Verify
    assert report.success
    assert report.test_results is not None
    assert report.test_results.success
    assert report.commit_hash is not None
    assert len(report.commit_hash) == 40  # Git SHA-1
```

## Error Handling

| Error | Handling | User Impact |
|-------|----------|-------------|
| Tests fail | Set `success=False`, capture output, skip commit | Teaching report shows failure, no commit created |
| No tests exist | Log warning, skip test step, proceed to commit | Commit created with warning in report |
| Git commit fails | Set `success=False`, capture error | Teaching report shows failure, changes staged but not committed |
| Subprocess timeout | Raise exception, set `success=False` | Teaching fails, user notified |

## Dependencies

**Existing:**
- `subprocess` (stdlib)
- `pytest` (already in requirements.txt)

**New:**
None

## Verification

After each sprint:

1. **Code Quality:**
   ```bash
   ruff check AIM/src/aim/teacher/skills/
   mypy AIM/src/aim/teacher/skills/
   ```

2. **Tests:**
   ```bash
   pytest AIM/tests/teacher/skills/ -v
   ```

3. **Integration:**
   ```bash
   pytest AIM/tests/teacher/skills/test_skill_teacher_integration.py -v
   ```

## Rollback Plan

If implementation fails:
1. Revert changes: `git checkout AIM/src/aim/teacher/skills/skill_teacher.py`
2. Remove test files
3. Review error logs
4. Fix issues
5. Retry

## Success Criteria

- [ ] All dataclasses defined
- [ ] _run_tests() implemented and tested
- [ ] _commit_changes() implemented and tested
- [ ] teach_subagent() calls Steps 7-8
- [ ] All unit tests pass (6 tests)
- [ ] Integration test passes (1 test)
- [ ] Failed tests block commit
- [ ] No changes handled gracefully
- [ ] Git commit includes metadata
- [ ] Code passes ruff and mypy

## Estimated Effort

- Sprint 1: 60-90 minutes
- Sprint 2: 45-60 minutes
- **Total: 105-150 minutes**

## Notes

- Steps 7-8 complete the autonomous teaching workflow
- Test execution ensures code quality before commit
- Git commit preserves teaching metadata for audit
- Error handling prevents broken code from being committed
