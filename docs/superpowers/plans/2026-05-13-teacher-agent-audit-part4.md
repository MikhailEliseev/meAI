# Teacher Agent Audit - Part 4: Execution & Main Orchestrator

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build main Teacher Agent orchestrator that runs full audit-upgrade cycle

**Architecture:** Orchestrator → Inventory → Find GitHub → Clone → Audit → Upgrade → Report

**Tech Stack:** Python 3.11+, asyncio, pytest

**Prerequisites:** Parts 1-3 completed (all components ready)

---

## Task 11: Create Main Teacher Agent

**Files:**
- Create: `AIM/src/aim/teacher/teacher_agent.py`
- Create: `AIM/tests/teacher/test_teacher_agent.py`

- [ ] **Step 1: Write failing test**

```python
# AIM/tests/teacher/test_teacher_agent.py
import pytest
from pathlib import Path
from AIM.src.aim.teacher.teacher_agent import TeacherAgent


@pytest.mark.asyncio
async def test_audit_single_subagent():
    """Test auditing a single subagent."""
    teacher = TeacherAgent()
    
    result = await teacher.audit_subagent("content_writer_agent")
    
    assert result is not None
    assert result.subagent_name == "content_writer_agent"
    assert result.score >= 0
    assert result.score <= 100


@pytest.mark.asyncio
async def test_audit_all_subagents():
    """Test auditing all subagents."""
    teacher = TeacherAgent()
    
    results = await teacher.audit_all()
    
    assert len(results) > 0
    assert all(r.score >= 0 for r in results)
    assert all(r.score <= 100 for r in results)


@pytest.mark.asyncio
async def test_upgrade_subagent():
    """Test upgrading a subagent."""
    teacher = TeacherAgent()
    
    # First audit
    audit_result = await teacher.audit_subagent("content_writer_agent")
    
    # Then upgrade if needed
    if audit_result.gaps:
        upgrade_result = await teacher.upgrade_subagent(
            "content_writer_agent",
            audit_result,
        )
        
        assert upgrade_result.success
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest AIM/tests/teacher/test_teacher_agent.py -v`
Expected: FAIL with "No module named 'AIM.src.aim.teacher.teacher_agent'"

- [ ] **Step 3: Write minimal implementation**

```python
# AIM/src/aim/teacher/teacher_agent.py
"""Teacher Agent - Continuous System Learning."""

import asyncio
from pathlib import Path

from AIM.src.aim.teacher.audit_report import AuditReportGenerator, AuditResult
from AIM.src.aim.teacher.code_analyzer import CodeAnalyzer
from AIM.src.aim.teacher.gap_detector import GapDetector
from AIM.src.aim.teacher.github_finder import GitHubFinder
from AIM.src.aim.teacher.pattern_extractor import PatternExtractor
from AIM.src.aim.teacher.repo_cloner import RepoCloner
from AIM.src.aim.teacher.subagent_inventory import SubagentInventory
from AIM.src.aim.teacher.upgrade_applier import UpgradeApplier, UpgradeResult


class TeacherAgent:
    """
    Teacher Agent - Chief Learning Officer.
    
    Responsibilities:
    - Audit all subagents for GitHub integration
    - Find production-ready patterns from GitHub
    - Upgrade subagents with best practices
    - Generate learning reports
    """
    
    def __init__(
        self,
        subagents_dir: str = "AIM/src/aim/subagents",
        reports_dir: str = "obsidian/teacher/wiki/learning-cycles",
    ):
        self.subagents_dir = Path(subagents_dir)
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Components
        self.inventory = SubagentInventory(str(self.subagents_dir))
        self.github_finder = GitHubFinder(min_stars=50)
        self.repo_cloner = RepoCloner()
        self.analyzer = CodeAnalyzer()
        self.gap_detector = GapDetector()
        self.extractor = PatternExtractor()
        self.applier = UpgradeApplier()
        self.report_generator = AuditReportGenerator()
    
    async def audit_subagent(self, subagent_name: str) -> AuditResult:
        """
        Audit a single subagent.
        
        Args:
            subagent_name: Name of subagent to audit
        
        Returns:
            AuditResult with gaps and score
        """
        # Find subagent file
        subagent_file = self.subagents_dir / f"{subagent_name}.py"
        if not subagent_file.exists():
            raise FileNotFoundError(f"Subagent not found: {subagent_name}")
        
        # Read subagent code
        our_code = subagent_file.read_text()
        
        # Determine topic from subagent name
        topic = subagent_name.replace("_", " ")
        
        # Find GitHub repos
        repos = self.github_finder.find_repos(topic, max_results=5)
        
        if not repos:
            # No repos found, score based on existing patterns
            our_patterns = self.analyzer.detect_patterns(our_code)
            score = len(our_patterns) * 20  # 20 points per pattern
            
            return AuditResult(
                subagent_name=subagent_name,
                github_repos=[],
                gaps=[],
                score=min(score, 100),
            )
        
        # Clone repos and analyze
        all_gaps = []
        for repo in repos[:3]:  # Top 3 repos
            clone_result = self.repo_cloner.clone(repo.url)
            
            if not clone_result.success:
                continue
            
            # Find main Python files in repo
            py_files = list(clone_result.path.rglob("*.py"))
            
            for py_file in py_files[:5]:  # Top 5 files
                try:
                    github_code = py_file.read_text()
                    gaps = self.gap_detector.detect(our_code, github_code)
                    all_gaps.extend(gaps)
                except Exception:
                    continue
        
        # Deduplicate gaps by pattern
        unique_gaps = {}
        for gap in all_gaps:
            if gap.pattern not in unique_gaps:
                unique_gaps[gap.pattern] = gap
        
        gaps = list(unique_gaps.values())
        
        # Calculate score (100 - penalties)
        score = 100
        for gap in gaps:
            if gap.severity.value == "critical":
                score -= 30
            elif gap.severity.value == "high":
                score -= 20
            elif gap.severity.value == "medium":
                score -= 10
        
        score = max(score, 0)
        
        return AuditResult(
            subagent_name=subagent_name,
            github_repos=[r.name for r in repos[:3]],
            gaps=gaps,
            score=score,
        )
    
    async def audit_all(self) -> list[AuditResult]:
        """
        Audit all subagents.
        
        Returns:
            List of AuditResult for each subagent
        """
        subagents = self.inventory.scan()
        
        # Filter out subagents with GitHub integration
        to_audit = [s for s in subagents if not s.has_github_integration]
        
        print(f"Found {len(to_audit)} subagents to audit (out of {len(subagents)} total)")
        
        # Audit each subagent
        results = []
        for subagent in to_audit:
            print(f"Auditing {subagent.name}...")
            
            try:
                result = await self.audit_subagent(subagent.name)
                results.append(result)
                
                # Save report
                report_path = self.reports_dir / f"{subagent.name}_audit.md"
                self.report_generator.save(result, report_path)
                
                print(f"  Score: {result.score:.1f}/100")
                print(f"  Gaps: {len(result.gaps)}")
            except Exception as e:
                print(f"  Error: {e}")
        
        return results
    
    async def upgrade_subagent(
        self,
        subagent_name: str,
        audit_result: AuditResult,
    ) -> UpgradeResult:
        """
        Upgrade a subagent based on audit result.
        
        Args:
            subagent_name: Name of subagent
            audit_result: Audit result with gaps
        
        Returns:
            UpgradeResult with success status
        """
        if not audit_result.gaps:
            return UpgradeResult(
                success=True,
                file_path=self.subagents_dir / f"{subagent_name}.py",
                patterns_applied=[],
            )
        
        # Find subagent file
        subagent_file = self.subagents_dir / f"{subagent_name}.py"
        
        # Get GitHub code from first repo
        if not audit_result.github_repos:
            return UpgradeResult(
                success=False,
                file_path=subagent_file,
                error="No GitHub repos to extract patterns from",
            )
        
        # Clone first repo
        repo_name = audit_result.github_repos[0]
        repo_url = f"https://github.com/{repo_name}"
        clone_result = self.repo_cloner.clone(repo_url)
        
        if not clone_result.success:
            return UpgradeResult(
                success=False,
                file_path=subagent_file,
                error=f"Failed to clone {repo_url}",
            )
        
        # Find main Python file
        py_files = list(clone_result.path.rglob("*.py"))
        if not py_files:
            return UpgradeResult(
                success=False,
                file_path=subagent_file,
                error="No Python files found in repo",
            )
        
        github_code = py_files[0].read_text()
        
        # Apply upgrade
        return self.applier.apply(subagent_file, audit_result.gaps, github_code)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest AIM/tests/teacher/test_teacher_agent.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add AIM/src/aim/teacher/teacher_agent.py AIM/tests/teacher/test_teacher_agent.py
git commit -m "feat(teacher): add main Teacher Agent orchestrator"
```

---

## Task 12: Create CLI Interface

**Files:**
- Create: `scripts/teacher_cli.py`
- Test: Manual testing

- [ ] **Step 1: Write CLI script**

```python
# scripts/teacher_cli.py
"""Teacher Agent CLI - Audit and upgrade subagents."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from AIM.src.aim.teacher.teacher_agent import TeacherAgent


async def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/teacher_cli.py audit [subagent_name]")
        print("  python scripts/teacher_cli.py audit-all")
        print("  python scripts/teacher_cli.py upgrade <subagent_name>")
        sys.exit(1)
    
    command = sys.argv[1]
    teacher = TeacherAgent()
    
    if command == "audit":
        if len(sys.argv) < 3:
            print("Error: subagent_name required")
            sys.exit(1)
        
        subagent_name = sys.argv[2]
        print(f"Auditing {subagent_name}...")
        
        result = await teacher.audit_subagent(subagent_name)
        
        print(f"\nScore: {result.score:.1f}/100")
        print(f"GitHub Repos: {len(result.github_repos)}")
        print(f"Gaps: {len(result.gaps)}")
        
        if result.gaps:
            print("\nGaps detected:")
            for gap in result.gaps:
                print(f"  - {gap.pattern} ({gap.severity.value})")
                print(f"    {gap.description}")
                print(f"    Action: {gap.recommendation}")
    
    elif command == "audit-all":
        print("Auditing all subagents...")
        
        results = await teacher.audit_all()
        
        print(f"\n{'='*60}")
        print("AUDIT SUMMARY")
        print(f"{'='*60}")
        print(f"Total subagents audited: {len(results)}")
        
        # Sort by score
        results.sort(key=lambda r: r.score)
        
        print("\nResults (worst to best):")
        for result in results:
            status = "✅" if result.score >= 80 else "⚠️" if result.score >= 60 else "❌"
            print(f"{status} {result.subagent_name}: {result.score:.1f}/100 ({len(result.gaps)} gaps)")
        
        # Summary stats
        avg_score = sum(r.score for r in results) / len(results)
        print(f"\nAverage score: {avg_score:.1f}/100")
        
        critical_count = sum(1 for r in results if r.score < 60)
        print(f"Critical (< 60): {critical_count}")
        
        needs_work = sum(1 for r in results if 60 <= r.score < 80)
        print(f"Needs work (60-80): {needs_work}")
        
        good = sum(1 for r in results if r.score >= 80)
        print(f"Good (>= 80): {good}")
    
    elif command == "upgrade":
        if len(sys.argv) < 3:
            print("Error: subagent_name required")
            sys.exit(1)
        
        subagent_name = sys.argv[2]
        print(f"Upgrading {subagent_name}...")
        
        # First audit
        print("Step 1: Auditing...")
        audit_result = await teacher.audit_subagent(subagent_name)
        
        if not audit_result.gaps:
            print("No gaps found! Subagent is already up to date.")
            sys.exit(0)
        
        print(f"Found {len(audit_result.gaps)} gaps")
        
        # Then upgrade
        print("Step 2: Applying upgrades...")
        upgrade_result = await teacher.upgrade_subagent(subagent_name, audit_result)
        
        if upgrade_result.success:
            print(f"✅ Upgrade successful!")
            print(f"Patterns applied: {', '.join(upgrade_result.patterns_applied)}")
            print(f"Backup saved: {upgrade_result.backup_path}")
        else:
            print(f"❌ Upgrade failed: {upgrade_result.error}")
            sys.exit(1)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Test CLI - audit single subagent**

Run: `python scripts/teacher_cli.py audit content_writer_agent`
Expected: Shows score, gaps, recommendations

- [ ] **Step 3: Test CLI - audit all**

Run: `python scripts/teacher_cli.py audit-all`
Expected: Shows summary of all subagents with scores

- [ ] **Step 4: Commit**

```bash
git add scripts/teacher_cli.py
git commit -m "feat(teacher): add CLI interface for audit and upgrade"
```

---

## Task 13: Create Documentation

**Files:**
- Create: `docs/TEACHER_AGENT.md`

- [ ] **Step 1: Write documentation**

```markdown
# Teacher Agent - Continuous System Learning

**Status:** ✅ Production Ready  
**Version:** 1.0.0  
**Date:** 2026-05-13

---

## Overview

Teacher Agent is the Chief Learning Officer of the meAI system. It continuously monitors, audits, and upgrades all subagents using production-ready patterns from GitHub.

**Key Features:**
- Automatic subagent inventory
- GitHub repository discovery
- Pattern extraction and analysis
- Gap detection vs best practices
- Automated code upgrades
- Learning cycle reports

---

## Architecture

```
Teacher Agent
  ↓
1. Inventory Scan (find all subagents)
  ↓
2. GitHub Discovery (find relevant repos)
  ↓
3. Repository Cloning (clone top repos)
  ↓
4. Pattern Analysis (extract patterns)
  ↓
5. Gap Detection (compare our code vs GitHub)
  ↓
6. Upgrade Application (apply patterns)
  ↓
7. Report Generation (learning cycle report)
```

---

## Usage

### Audit Single Subagent

```bash
python scripts/teacher_cli.py audit content_writer_agent
```

**Output:**
- Score (0-100)
- GitHub repos analyzed
- Gaps detected
- Recommendations

### Audit All Subagents

```bash
python scripts/teacher_cli.py audit-all
```

**Output:**
- Summary of all subagents
- Scores sorted worst to best
- Statistics (critical, needs work, good)

### Upgrade Subagent

```bash
python scripts/teacher_cli.py upgrade content_writer_agent
```

**Steps:**
1. Audit subagent
2. Find GitHub patterns
3. Apply upgrades
4. Create backup
5. Report results

---

## Scoring System

**Score = 100 - penalties**

**Penalties:**
- Critical gap (no circuit breaker, no error handling): -30 points
- High gap (no retry, no rate limiting): -20 points
- Medium gap (no caching, no metrics): -10 points

**Thresholds:**
- ✅ Good: >= 80 points
- ⚠️ Needs work: 60-79 points
- ❌ Critical: < 60 points

---

## Gap Severity

### 🔴 CRITICAL (implement immediately)
- Circuit breaker (prevents cascading failures)
- Error handling (prevents crashes)
- Input validation (prevents security issues)

### 🟡 HIGH (plan for next sprint)
- Retry logic (improves reliability)
- Rate limiting (prevents API abuse)
- Timeout handling (prevents hangs)

### 🟢 MEDIUM (backlog)
- Caching (improves performance)
- Metrics (enables monitoring)
- Structured logging (enables debugging)

---

## Reports

Reports are saved to: `obsidian/teacher/wiki/learning-cycles/`

**Format:**
```markdown
# Audit Report: [subagent_name]

**Date:** YYYY-MM-DD HH:MM:SS
**Score:** XX.X/100
**Status:** ✅ PASS / ⚠️ NEEDS IMPROVEMENT / ❌ FAIL

## GitHub Repositories Analyzed
- repo1
- repo2

## Gaps Detected

### 🔴 CRITICAL
- pattern: description
- Action: recommendation

### 🟡 HIGH
- pattern: description
- Action: recommendation
```

---

## Learning Cycle

**Frequency:** Every 2-4 weeks

**Process:**
1. Run `audit-all` to scan all subagents
2. Review reports in `obsidian/teacher/wiki/learning-cycles/`
3. Prioritize upgrades (critical first)
4. Run `upgrade` for each subagent
5. Test upgraded subagents
6. Commit changes

---

## Examples

### Example 1: Content Writer Agent

**Before:**
```python
class ContentWriterAgent:
    def fetch_data(self):
        return requests.get(url)  # No error handling
```

**After:**
```python
from pybreaker import CircuitBreaker
from tenacity import retry, stop_after_attempt

class ContentWriterAgent:
    def __init__(self):
        self.breaker = CircuitBreaker(fail_max=5, reset_timeout=60)
    
    @retry(stop=stop_after_attempt(3))
    def fetch_data(self):
        return self.breaker.call(self._do_fetch)
```

**Improvements:**
- ✅ Circuit breaker added
- ✅ Retry logic added
- ✅ Production-ready error handling

---

## Troubleshooting

### "No GitHub repos found"
- Topic too specific → broaden search terms
- Min stars too high → lower threshold (default: 50)

### "Failed to clone repo"
- Network issue → check internet connection
- Private repo → skip (Teacher Agent only uses public repos)

### "Upgrade failed"
- Syntax error in original code → fix manually first
- Complex code structure → apply patterns manually

---

## Future Enhancements

1. **Automatic scheduling** - Run audit every 2 weeks
2. **PR creation** - Auto-create PRs for upgrades
3. **Test generation** - Generate tests for new patterns
4. **Metrics tracking** - Track improvement over time
5. **Multi-language support** - Support non-Python subagents

---

**Version:** 1.0.0  
**Author:** meAI Architect  
**Status:** ✅ Production Ready
```

- [ ] **Step 2: Commit documentation**

```bash
git add docs/TEACHER_AGENT.md
git commit -m "docs: add Teacher Agent documentation"
```

---

## Task 14: Integration Test

**Files:**
- Create: `AIM/tests/integration/test_teacher_agent_e2e.py`

- [ ] **Step 1: Write E2E test**

```python
# AIM/tests/integration/test_teacher_agent_e2e.py
"""End-to-end test for Teacher Agent."""

import pytest
import tempfile
import shutil
from pathlib import Path
from AIM.src.aim.teacher.teacher_agent import TeacherAgent


@pytest.mark.asyncio
async def test_full_audit_upgrade_cycle():
    """Test complete audit → upgrade cycle."""
    # Create temp subagent
    with tempfile.TemporaryDirectory() as tmpdir:
        subagents_dir = Path(tmpdir) / "subagents"
        subagents_dir.mkdir()
        
        # Create simple subagent without patterns
        test_agent = subagents_dir / "test_agent.py"
        test_agent.write_text("""
import requests

class TestAgent:
    def __init__(self):
        self.url = "http://example.com"
    
    def fetch(self):
        return requests.get(self.url)
""")
        
        # Initialize Teacher Agent
        teacher = TeacherAgent(
            subagents_dir=str(subagents_dir),
            reports_dir=str(Path(tmpdir) / "reports"),
        )
        
        # Step 1: Audit
        audit_result = await teacher.audit_subagent("test_agent")
        
        assert audit_result.score < 100  # Should have gaps
        assert len(audit_result.gaps) > 0
        
        # Step 2: Upgrade
        upgrade_result = await teacher.upgrade_subagent("test_agent", audit_result)
        
        assert upgrade_result.success
        assert len(upgrade_result.patterns_applied) > 0
        
        # Step 3: Verify upgrade
        updated_code = test_agent.read_text()
        
        # Should have at least one pattern
        has_pattern = any([
            "CircuitBreaker" in updated_code,
            "retry" in updated_code,
            "AsyncLimiter" in updated_code,
        ])
        
        assert has_pattern
```

- [ ] **Step 2: Run E2E test**

Run: `pytest AIM/tests/integration/test_teacher_agent_e2e.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add AIM/tests/integration/test_teacher_agent_e2e.py
git commit -m "test(teacher): add end-to-end integration test"
```

---

## Task 15: Final Verification

**Files:**
- None (verification only)

- [ ] **Step 1: Run all tests**

Run: `pytest AIM/tests/teacher/ -v`
Expected: All tests pass

- [ ] **Step 2: Test CLI on real subagent**

Run: `python scripts/teacher_cli.py audit content_writer_agent`
Expected: Shows real audit results

- [ ] **Step 3: Verify directory structure**

Run: `ls -la AIM/src/aim/teacher/ AIM/tests/teacher/`
Expected: All files present

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat(teacher): complete Teacher Agent implementation

Teacher Agent v1.0.0 - Continuous System Learning

Components:
- Subagent inventory scanner
- GitHub repository finder
- Repository cloner
- Code analyzer (pattern detection)
- Gap detector (vs best practices)
- Pattern extractor (from GitHub)
- Code generator (apply patterns)
- Upgrade applier (with backup)
- Audit report generator
- Main orchestrator
- CLI interface

Features:
- Audit single subagent
- Audit all subagents
- Upgrade subagent with GitHub patterns
- Generate learning cycle reports
- Automatic backup before upgrade

Tests: 15+ tests passing
Status: Production Ready

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>"
```

---

**Part 4 Complete! All 4 parts finished.**

## Execution Summary

**Total Tasks:** 15 tasks
**Total Steps:** ~75 steps
**Estimated Time:** 4-6 hours (with subagent-driven development)

**Components Built:**
1. ✅ Subagent Inventory
2. ✅ GitHub Finder
3. ✅ Repository Cloner
4. ✅ Code Analyzer
5. ✅ Gap Detector
6. ✅ Audit Report Generator
7. ✅ Pattern Extractor
8. ✅ Code Generator
9. ✅ Upgrade Applier
10. ✅ Main Teacher Agent
11. ✅ CLI Interface
12. ✅ Documentation
13. ✅ E2E Tests

**Next Steps:**
1. Execute plan using subagent-driven-development
2. Run `audit-all` on real subagents
3. Review reports and prioritize upgrades
4. Upgrade critical subagents first
5. Schedule recurring audits (every 2-4 weeks)

---

**Plan complete and saved!**

**Execution options:**

**1. Subagent-Driven (recommended)** - Fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
