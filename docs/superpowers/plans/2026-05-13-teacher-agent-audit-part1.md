# Teacher Agent Audit - Part 1: Setup & Infrastructure

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Audit and upgrade 25-30 old subagents using GitHub-integrated deep analysis approach

**Architecture:** Teacher Agent reads old subagents → finds GitHub repos → clones & studies code → upgrades subagents with production patterns

**Tech Stack:** Python 3.11+, GitHub API, git, pytest

**Plan Structure:**
- Part 1: Setup & Infrastructure (this file)
- Part 2: Audit Engine (2026-05-13-teacher-agent-audit-part2.md)
- Part 3: Upgrade Engine (2026-05-13-teacher-agent-audit-part3.md)
- Part 4: Execution (2026-05-13-teacher-agent-audit-part4.md)

---

## Task 1: Create Teacher Agent Directory Structure

**Files:**
- Create: `AIM/src/aim/teacher/__init__.py`
- Create: `AIM/src/aim/teacher/teacher_agent.py`
- Create: `AIM/src/aim/teacher/audit_engine.py`
- Create: `AIM/src/aim/teacher/upgrade_engine.py`
- Create: `AIM/tests/teacher/__init__.py`
- Create: `AIM/tests/teacher/test_teacher_agent.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p AIM/src/aim/teacher
mkdir -p AIM/tests/teacher
touch AIM/src/aim/teacher/__init__.py
touch AIM/tests/teacher/__init__.py
```

- [ ] **Step 2: Verify structure**

Run: `ls -la AIM/src/aim/teacher/ AIM/tests/teacher/`
Expected: Directories exist with __init__.py files

- [ ] **Step 3: Commit**

```bash
git add AIM/src/aim/teacher/ AIM/tests/teacher/
git commit -m "feat(teacher): create Teacher Agent directory structure"
```

---

## Task 2: Create Subagent Inventory

**Files:**
- Create: `AIM/src/aim/teacher/subagent_inventory.py`
- Create: `AIM/tests/teacher/test_subagent_inventory.py`

- [ ] **Step 1: Write failing test**

```python
# AIM/tests/teacher/test_subagent_inventory.py
import pytest
from AIM.src.aim.teacher.subagent_inventory import SubagentInventory


def test_scan_subagents():
    """Test scanning subagents directory."""
    inventory = SubagentInventory()
    subagents = inventory.scan()
    
    assert len(subagents) > 0
    assert "content_writer_agent" in [s.name for s in subagents]


def test_subagent_metadata():
    """Test subagent metadata extraction."""
    inventory = SubagentInventory()
    subagents = inventory.scan()
    
    subagent = subagents[0]
    assert hasattr(subagent, "name")
    assert hasattr(subagent, "path")
    assert hasattr(subagent, "created_date")
    assert hasattr(subagent, "has_github_integration")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest AIM/tests/teacher/test_subagent_inventory.py -v`
Expected: FAIL with "No module named 'AIM.src.aim.teacher.subagent_inventory'"

- [ ] **Step 3: Write minimal implementation**

```python
# AIM/src/aim/teacher/subagent_inventory.py
"""Subagent inventory scanner."""

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class SubagentInfo:
    """Subagent metadata."""
    name: str
    path: str
    created_date: datetime
    has_github_integration: bool
    lines_of_code: int


class SubagentInventory:
    """Scan and inventory all subagents."""
    
    def __init__(self, subagents_dir: str = "AIM/src/aim/subagents"):
        self.subagents_dir = Path(subagents_dir)
    
    def scan(self) -> list[SubagentInfo]:
        """Scan subagents directory and return metadata."""
        subagents = []
        
        # Scan main subagents directory
        for file in self.subagents_dir.glob("*.py"):
            if file.name == "__init__.py":
                continue
            
            info = self._extract_metadata(file)
            if info:
                subagents.append(info)
        
        return subagents
    
    def _extract_metadata(self, file_path: Path) -> SubagentInfo | None:
        """Extract metadata from subagent file."""
        try:
            content = file_path.read_text()
            
            # Check for GitHub integration markers
            has_github = any([
                "Adapted from" in content,
                "Source:" in content and "github.com" in content,
                "pybreaker" in content,
                "trafilatura" in content,
            ])
            
            # Get creation date from git
            import subprocess
            result = subprocess.run(
                ["git", "log", "--follow", "--format=%aI", "--", str(file_path)],
                capture_output=True,
                text=True,
            )
            dates = result.stdout.strip().split("\n")
            created_date = datetime.fromisoformat(dates[-1]) if dates and dates[0] else datetime.now()
            
            # Count lines
            lines = len(content.split("\n"))
            
            return SubagentInfo(
                name=file_path.stem,
                path=str(file_path),
                created_date=created_date,
                has_github_integration=has_github,
                lines_of_code=lines,
            )
        except Exception:
            return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest AIM/tests/teacher/test_subagent_inventory.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add AIM/src/aim/teacher/subagent_inventory.py AIM/tests/teacher/test_subagent_inventory.py
git commit -m "feat(teacher): add subagent inventory scanner"
```

---

## Task 3: Create GitHub Repository Finder

**Files:**
- Create: `AIM/src/aim/teacher/github_finder.py`
- Create: `AIM/tests/teacher/test_github_finder.py`

- [ ] **Step 1: Write failing test**

```python
# AIM/tests/teacher/test_github_finder.py
import pytest
from AIM.src.aim.teacher.github_finder import GitHubFinder


def test_find_repos_for_topic():
    """Test finding GitHub repos for a topic."""
    finder = GitHubFinder()
    repos = finder.find_repos("content writing SEO")
    
    assert len(repos) > 0
    assert all(hasattr(r, "url") for r in repos)
    assert all(hasattr(r, "stars") for r in repos)
    assert all(hasattr(r, "description") for r in repos)


def test_filter_by_stars():
    """Test filtering repos by star count."""
    finder = GitHubFinder(min_stars=100)
    repos = finder.find_repos("SEO analysis")
    
    assert all(r.stars >= 100 for r in repos)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest AIM/tests/teacher/test_github_finder.py -v`
Expected: FAIL with "No module named 'AIM.src.aim.teacher.github_finder'"

- [ ] **Step 3: Write minimal implementation**

```python
# AIM/src/aim/teacher/github_finder.py
"""GitHub repository finder for subagent topics."""

from dataclasses import dataclass
import httpx


@dataclass
class GitHubRepo:
    """GitHub repository metadata."""
    url: str
    name: str
    stars: int
    description: str
    language: str


class GitHubFinder:
    """Find relevant GitHub repositories for subagent topics."""
    
    def __init__(self, min_stars: int = 50):
        self.min_stars = min_stars
        self.client = httpx.Client(timeout=30.0)
    
    def find_repos(self, topic: str, max_results: int = 10) -> list[GitHubRepo]:
        """
        Find GitHub repos for a topic.
        
        Args:
            topic: Search topic (e.g., "content writing SEO")
            max_results: Maximum number of results
        
        Returns:
            List of GitHubRepo objects
        """
        # GitHub API search
        query = f"{topic} language:python stars:>={self.min_stars}"
        url = "https://api.github.com/search/repositories"
        
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": max_results,
        }
        
        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            repos = []
            for item in data.get("items", []):
                repo = GitHubRepo(
                    url=item["html_url"],
                    name=item["full_name"],
                    stars=item["stargazers_count"],
                    description=item.get("description", ""),
                    language=item.get("language", "Python"),
                )
                repos.append(repo)
            
            return repos
        except Exception as e:
            print(f"Error finding repos: {e}")
            return []
    
    def __del__(self):
        """Close HTTP client."""
        if hasattr(self, "client"):
            self.client.close()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest AIM/tests/teacher/test_github_finder.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add AIM/src/aim/teacher/github_finder.py AIM/tests/teacher/test_github_finder.py
git commit -m "feat(teacher): add GitHub repository finder"
```

---

## Task 4: Create Repository Cloner

**Files:**
- Create: `AIM/src/aim/teacher/repo_cloner.py`
- Create: `AIM/tests/teacher/test_repo_cloner.py`

- [ ] **Step 1: Write failing test**

```python
# AIM/tests/teacher/test_repo_cloner.py
import pytest
import tempfile
import shutil
from pathlib import Path
from AIM.src.aim.teacher.repo_cloner import RepoCloner


def test_clone_repo():
    """Test cloning a GitHub repository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cloner = RepoCloner(base_dir=tmpdir)
        
        # Clone a small test repo
        result = cloner.clone("https://github.com/octocat/Hello-World")
        
        assert result.success
        assert result.path.exists()
        assert (result.path / ".git").exists()


def test_skip_existing_repo():
    """Test skipping already cloned repo."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cloner = RepoCloner(base_dir=tmpdir)
        
        # Clone once
        result1 = cloner.clone("https://github.com/octocat/Hello-World")
        
        # Clone again (should skip)
        result2 = cloner.clone("https://github.com/octocat/Hello-World")
        
        assert result1.success
        assert result2.success
        assert result2.skipped
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest AIM/tests/teacher/test_repo_cloner.py -v`
Expected: FAIL with "No module named 'AIM.src.aim.teacher.repo_cloner'"

- [ ] **Step 3: Write minimal implementation**

```python
# AIM/src/aim/teacher/repo_cloner.py
"""GitHub repository cloner."""

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CloneResult:
    """Result of cloning operation."""
    success: bool
    path: Path
    skipped: bool = False
    error: str | None = None


class RepoCloner:
    """Clone GitHub repositories for analysis."""
    
    def __init__(self, base_dir: str = "~/temp/research-repos"):
        self.base_dir = Path(base_dir).expanduser()
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def clone(self, url: str) -> CloneResult:
        """
        Clone a GitHub repository.
        
        Args:
            url: GitHub repository URL
        
        Returns:
            CloneResult with success status and path
        """
        # Extract repo name from URL
        repo_name = url.rstrip("/").split("/")[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]
        
        target_path = self.base_dir / repo_name
        
        # Skip if already exists
        if target_path.exists():
            return CloneResult(
                success=True,
                path=target_path,
                skipped=True,
            )
        
        # Clone repository
        try:
            result = subprocess.run(
                ["git", "clone", url, str(target_path)],
                capture_output=True,
                text=True,
                timeout=300,
            )
            
            if result.returncode == 0:
                return CloneResult(
                    success=True,
                    path=target_path,
                )
            else:
                return CloneResult(
                    success=False,
                    path=target_path,
                    error=result.stderr,
                )
        except Exception as e:
            return CloneResult(
                success=False,
                path=target_path,
                error=str(e),
            )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest AIM/tests/teacher/test_repo_cloner.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add AIM/src/aim/teacher/repo_cloner.py AIM/tests/teacher/test_repo_cloner.py
git commit -m "feat(teacher): add repository cloner"
```

---

**Part 1 Complete!** Continue with Part 2: Audit Engine (2026-05-13-teacher-agent-audit-part2.md)
