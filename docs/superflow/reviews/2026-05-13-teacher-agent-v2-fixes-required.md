# Teacher Agent v2.0 - Required Fixes

**Date:** 2026-05-13  
**Status:** Action Items from Opus Review  
**Priority:** Fix before implementation

---

## 🔴 BLOCKER 1: Risk Score Calculation Logic

**Location:** `docs/TEACHER_AGENT.md`, Section 3.5, lines 762-800

**Current Code:**
```python
# Line 764
risk_composite = 100 - risk_score.overall  # Invert

# Line 767
if quality_composite >= 80 and fit_composite >= 80 and risk_composite <= 20:
    return AdoptionDecision(decision="Full", ...)
```

**Problem:**
- Семантика `risk_score.overall` неясна
- Если `risk_score.overall = 80` (low risk), то `risk_composite = 20`
- `risk_composite <= 20` проходит, но это означает `risk_score >= 80`
- Board Memo говорит "Risk ≤20" но неясно что это означает

**Fix Option A (Recommended):**
```python
# Define: risk_score.overall = 0-100 (0 = high risk, 100 = no risk)
# Use directly without inversion

if quality_composite >= 80 and fit_composite >= 80 and risk_score.overall >= 80:
    return AdoptionDecision(
        decision="Full",
        rationale="High quality, excellent fit, low risk (risk_score ≥ 80)",
        ...
    )

elif quality_composite >= 70 and fit_composite >= 70 and risk_score.overall >= 70:
    return AdoptionDecision(
        decision="Partial",
        rationale="Good quality, good fit, acceptable risk (risk_score ≥ 70)",
        ...
    )
```

**Fix Option B:**
```python
# Define: risk_score.overall = 0-100 (0 = no risk, 100 = high risk)
# Then inversion is correct

if quality_composite >= 80 and fit_composite >= 80 and risk_score.overall <= 20:
    return AdoptionDecision(
        decision="Full",
        rationale="High quality, excellent fit, low risk (risk_score ≤ 20)",
        ...
    )
```

**Action:**
1. Choose Option A or B
2. Update Section 3.5 (DecisionMaker)
3. Update Section 3.4 (RiskAnalyzer) to clarify semantics
4. Update all decision rules consistently
5. Add docstring explaining risk_score semantics

**Estimated Time:** 30 minutes

---

## 🔴 BLOCKER 2: Compliance Checks Insufficient

**Location:** `docs/TEACHER_AGENT.md`, Section 4.6, Gate 4, lines 1398-1400

**Current:**
```python
**Gate 4: Compliance Check (HIPAA)**
- Check for PII logging
- Check for encryption (at rest, in transit)
- Check for audit trail
- Pass condition: All compliance checks pass
- Fail condition: Any compliance check fails
```

**Problem:**
- Слишком поверхностно для medical marketing
- Нет конкретных алгоритмов проверки
- HIPAA требует детальных checks

**Fix:**

Add detailed compliance checker:

```python
@dataclass
class ComplianceResult:
    passed: bool
    checks: dict[str, bool]
    violations: list[str]
    details: str

class ComplianceChecker:
    """HIPAA compliance checker for medical marketing context."""
    
    async def check_hipaa_compliance(self, repo_path: Path) -> ComplianceResult:
        """Run all HIPAA compliance checks."""
        checks = {
            "phi_detection": await self._check_phi_logging(repo_path),
            "encryption_at_rest": await self._check_encryption_at_rest(repo_path),
            "encryption_in_transit": await self._check_tls_usage(repo_path),
            "audit_logging": await self._check_audit_trail(repo_path),
            "access_controls": await self._check_rbac(repo_path),
            "data_retention": await self._check_retention_policy(repo_path)
        }
        
        violations = [name for name, passed in checks.items() if not passed]
        all_passed = len(violations) == 0
        
        return ComplianceResult(
            passed=all_passed,
            checks=checks,
            violations=violations,
            details=self._generate_report(checks)
        )
    
    async def _check_phi_logging(self, repo_path: Path) -> bool:
        """Check for PHI (Protected Health Information) in logs."""
        # Scan for patterns: SSN, medical record numbers, patient names
        phi_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\bpatient[_\s]*(name|id|record)\b',  # Patient identifiers
            r'\bmedical[_\s]*record\b',
            r'\bdiagnosis\b',
            r'\bprescription\b'
        ]
        
        for py_file in repo_path.rglob("*.py"):
            content = py_file.read_text()
            for pattern in phi_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    # Check if it's in logging statement
                    if "logger." in content or "print(" in content:
                        return False  # PHI logging detected
        
        return True  # No PHI logging
    
    async def _check_encryption_at_rest(self, repo_path: Path) -> bool:
        """Check for encryption at rest (AES-256)."""
        # Look for encryption libraries
        encryption_libs = ["cryptography", "pycryptodome", "nacl"]
        
        # Check requirements.txt
        req_file = repo_path / "requirements.txt"
        if req_file.exists():
            content = req_file.read_text()
            if any(lib in content for lib in encryption_libs):
                # Check for AES usage in code
                for py_file in repo_path.rglob("*.py"):
                    code = py_file.read_text()
                    if "AES" in code or "Fernet" in code:
                        return True
        
        return False  # No encryption at rest
    
    async def _check_tls_usage(self, repo_path: Path) -> bool:
        """Check for TLS 1.2+ in transit."""
        # Look for HTTPS/TLS configuration
        for py_file in repo_path.rglob("*.py"):
            content = py_file.read_text()
            
            # Check for insecure HTTP
            if re.search(r'http://(?!localhost|127\.0\.0\.1)', content):
                return False  # Insecure HTTP detected
            
            # Check for TLS version
            if "ssl.PROTOCOL_TLS" in content or "ssl_version=ssl.PROTOCOL_TLSv1_2" in content:
                return True
        
        return True  # Assume HTTPS by default
    
    async def _check_audit_trail(self, repo_path: Path) -> bool:
        """Check for audit logging (who, what, when)."""
        # Look for audit logging patterns
        audit_patterns = [
            r'audit[_\s]*log',
            r'log[_\s]*audit',
            r'user[_\s]*action',
            r'access[_\s]*log'
        ]
        
        for py_file in repo_path.rglob("*.py"):
            content = py_file.read_text()
            if any(re.search(pattern, content, re.IGNORECASE) for pattern in audit_patterns):
                # Check for timestamp and user tracking
                if "timestamp" in content.lower() and "user" in content.lower():
                    return True
        
        return False  # No audit trail
    
    async def _check_rbac(self, repo_path: Path) -> bool:
        """Check for Role-Based Access Control."""
        # Look for RBAC patterns
        rbac_patterns = [
            r'@require[_\s]*role',
            r'@permission[_\s]*required',
            r'check[_\s]*permission',
            r'has[_\s]*role'
        ]
        
        for py_file in repo_path.rglob("*.py"):
            content = py_file.read_text()
            if any(re.search(pattern, content, re.IGNORECASE) for pattern in rbac_patterns):
                return True
        
        return False  # No RBAC
    
    async def _check_retention_policy(self, repo_path: Path) -> bool:
        """Check for data retention policy."""
        # Look for retention policy patterns
        retention_patterns = [
            r'retention[_\s]*policy',
            r'data[_\s]*retention',
            r'delete[_\s]*after',
            r'expire[_\s]*after'
        ]
        
        for py_file in repo_path.rglob("*.py"):
            content = py_file.read_text()
            if any(re.search(pattern, content, re.IGNORECASE) for pattern in retention_patterns):
                return True
        
        return False  # No retention policy
```

**Action:**
1. Add ComplianceChecker class to Section 4.6
2. Update Gate 4 description with detailed checks
3. Add ComplianceResult dataclass
4. Update ValidationGateRunner._run_gate_4() implementation

**Estimated Time:** 1 hour

---

## 🔴 BLOCKER 3: Sandbox Venv Isolation Missing

**Location:** `docs/TEACHER_AGENT.md`, Section 4.1, lines 986-1051

**Current:**
```python
@dataclass
class SandboxEnvironment:
    worktree_path: Path
    branch_name: str
    snapshot_id: str
    created_at: datetime
```

**Problem:**
- Нет venv isolation для dependencies
- DependencyInstaller будет устанавливать в main environment
- Риск сломать main environment

**Fix:**

Update SandboxEnvironment:
```python
@dataclass
class SandboxEnvironment:
    worktree_path: Path
    branch_name: str
    venv_path: Path              # ADD THIS
    snapshot_id: str
    created_at: datetime
```

Update SandboxManager:
```python
class SandboxManager:
    async def create_sandbox(
        self,
        subagent_name: str,
        adoption_id: str
    ) -> SandboxEnvironment:
        # Create worktree
        worktree_path = Path(f".claude/worktrees/teacher-{adoption_id}")
        branch_name = f"teacher/{subagent_name}-{adoption_id}"
        
        await self._run_git_command(
            f"worktree add {worktree_path} -b {branch_name}"
        )
        
        # Create isolated venv
        venv_path = worktree_path / ".venv"
        await self._create_venv(venv_path)
        
        # Activate venv and install base dependencies
        await self._activate_venv(venv_path)
        await self._install_base_dependencies(venv_path)
        
        # Create snapshot
        snapshot_id = await self._get_current_commit_hash()
        
        return SandboxEnvironment(
            worktree_path=worktree_path,
            branch_name=branch_name,
            venv_path=venv_path,
            snapshot_id=snapshot_id,
            created_at=datetime.now()
        )
    
    async def _create_venv(self, venv_path: Path) -> None:
        """Create isolated virtual environment."""
        await self._run_command(f"python -m venv {venv_path}")
    
    async def _activate_venv(self, venv_path: Path) -> None:
        """Activate virtual environment."""
        # Set environment variables for subprocess calls
        self.venv_bin = venv_path / "bin"
        self.venv_python = self.venv_bin / "python"
        self.venv_pip = self.venv_bin / "pip"
    
    async def _install_base_dependencies(self, venv_path: Path) -> None:
        """Install base dependencies in venv."""
        # Install pytest, pytest-cov for testing
        await self._run_command(
            f"{self.venv_pip} install pytest pytest-cov pytest-asyncio"
        )
```

Update DependencyInstaller:
```python
class DependencyInstaller:
    async def install_dependencies(
        self,
        github_repo_path: Path,
        sandbox: SandboxEnvironment
    ) -> DependencyResult:
        # Extract dependencies
        github_deps = await self._extract_dependencies(github_repo_path)
        our_deps = await self._extract_dependencies(Path("."))
        
        # Check conflicts
        conflicts = self._check_version_conflicts(github_deps, our_deps)
        
        # Install in sandbox venv (NOT main environment)
        dependencies_installed = []
        for dep in github_deps:
            if dep not in our_deps:
                await self._install_dependency_in_sandbox(dep, sandbox)
                dependencies_installed.append(dep)
        
        # Update requirements.txt in sandbox
        if dependencies_installed:
            await self._update_requirements_in_sandbox(dependencies_installed, sandbox)
            requirements_updated = True
        else:
            requirements_updated = False
        
        return DependencyResult(
            dependencies_installed=dependencies_installed,
            version_conflicts=conflicts,
            requirements_updated=requirements_updated
        )
    
    async def _install_dependency_in_sandbox(
        self,
        dependency: str,
        sandbox: SandboxEnvironment
    ) -> None:
        """Install dependency in sandbox venv."""
        pip_path = sandbox.venv_path / "bin" / "pip"
        await self._run_command(f"{pip_path} install {dependency}")
```

**Action:**
1. Update SandboxEnvironment dataclass (add venv_path)
2. Update SandboxManager (add venv creation methods)
3. Update DependencyInstaller (use sandbox venv)
4. Update ValidationGateRunner (run tests in sandbox venv)

**Estimated Time:** 30 minutes

---

## 🟡 MAJOR 4: Performance Metrics Not Defined

**Location:** `docs/TEACHER_AGENT.md`, Section 4.6, Gate 2, lines 1381-1386

**Current:**
```python
**Gate 2: Metrics Check**
- Compare metrics: complexity, coverage, performance
- Pass condition: Metrics improve OR stay same
- Fail condition: Any metric degrades
```

**Problem:**
- "performance" упоминается, но не описано как измерять
- Нет benchmark framework

**Fix:**

Add performance benchmarking:

```python
@dataclass
class PerformanceMetrics:
    response_time_ms: float
    throughput_rps: float
    memory_mb: float
    cpu_percent: float
    degradation_percent: float

class MetricsChecker:
    async def check_performance(
        self,
        sandbox: SandboxEnvironment,
        subagent_name: str
    ) -> PerformanceMetrics:
        """Run performance benchmarks."""
        # Run pytest-benchmark in sandbox
        benchmark_file = self._find_benchmark_file(sandbox, subagent_name)
        
        if not benchmark_file:
            # No benchmarks, skip performance check
            return PerformanceMetrics(
                response_time_ms=0,
                throughput_rps=0,
                memory_mb=0,
                cpu_percent=0,
                degradation_percent=0
            )
        
        # Run benchmarks
        pytest_path = sandbox.venv_path / "bin" / "pytest"
        result = await self._run_command(
            f"{pytest_path} {benchmark_file} --benchmark-json=benchmark.json"
        )
        
        # Parse results
        benchmark_data = json.loads((sandbox.worktree_path / "benchmark.json").read_text())
        
        # Load baseline
        baseline = await self._load_baseline_metrics(subagent_name)
        
        # Calculate metrics
        current_time = benchmark_data["benchmarks"][0]["stats"]["mean"]
        baseline_time = baseline.get("response_time_ms", current_time)
        
        degradation = ((current_time - baseline_time) / baseline_time) * 100
        
        return PerformanceMetrics(
            response_time_ms=current_time * 1000,
            throughput_rps=1000 / current_time if current_time > 0 else 0,
            memory_mb=benchmark_data["benchmarks"][0]["stats"]["peak_memory"] / 1024 / 1024,
            cpu_percent=0,  # TODO: measure CPU
            degradation_percent=degradation
        )
```

**Action:**
1. Add PerformanceMetrics dataclass
2. Add MetricsChecker class with performance benchmarking
3. Update Gate 2 description
4. Add pytest-benchmark to requirements.txt

**Estimated Time:** 30 minutes

---

## 🟡 MAJOR 5: Dependency Vulnerability Scan Missing

**Location:** `docs/TEACHER_AGENT.md`, Section 4.6, Gate 3, lines 1387-1392

**Current:**
```python
**Gate 3: Security Scan**
- Run bandit: `bandit -r AIM/src/aim/subagents/{name}/`
- Check for hardcoded secrets, SQL injection, XSS
- Pass condition: No high/medium severity issues
- Fail condition: Any high/medium severity issues
```

**Problem:**
- Bandit проверяет код, но не dependencies
- Можем внедрить vulnerable dependencies (CVEs)

**Fix:**

Add dependency vulnerability scan:

```python
@dataclass
class DependencySecurityResult:
    passed: bool
    vulnerabilities: list[dict]
    high_severity_count: int
    medium_severity_count: int
    details: str

class SecurityScanner:
    async def scan_dependencies(self, repo_path: Path) -> DependencySecurityResult:
        """Scan dependencies for known vulnerabilities."""
        # Run safety check
        result = await self._run_command(
            f"safety check --json --file {repo_path}/requirements.txt"
        )
        
        vulnerabilities = json.loads(result.stdout)
        
        high_severity = [v for v in vulnerabilities if v.get("severity") == "high"]
        medium_severity = [v for v in vulnerabilities if v.get("severity") == "medium"]
        
        passed = len(high_severity) == 0 and len(medium_severity) == 0
        
        return DependencySecurityResult(
            passed=passed,
            vulnerabilities=vulnerabilities,
            high_severity_count=len(high_severity),
            medium_severity_count=len(medium_severity),
            details=self._format_vulnerabilities(vulnerabilities)
        )
    
    def _format_vulnerabilities(self, vulnerabilities: list[dict]) -> str:
        """Format vulnerabilities for report."""
        if not vulnerabilities:
            return "No vulnerabilities found"
        
        lines = []
        for vuln in vulnerabilities:
            lines.append(
                f"- {vuln['package']} {vuln['version']}: "
                f"{vuln['vulnerability']} (severity: {vuln['severity']})"
            )
        
        return "\n".join(lines)
```

Update ValidationGateRunner:
```python
async def _run_gate_3(
    self,
    sandbox: SandboxEnvironment,
    subagent_name: str
) -> GateResult:
    """Gate 3: Security Scan."""
    start_time = time.time()
    
    # Run bandit (code security)
    bandit_result = await self.security_scanner.scan_code(
        sandbox.worktree_path / f"AIM/src/aim/subagents/{subagent_name}"
    )
    
    # Run safety (dependency security)
    dependency_result = await self.security_scanner.scan_dependencies(
        sandbox.worktree_path
    )
    
    passed = bandit_result.passed and dependency_result.passed
    
    details = f"Bandit: {bandit_result.details}\n\nDependencies: {dependency_result.details}"
    
    return GateResult(
        gate_name="Security Scan",
        passed=passed,
        details=details,
        duration=time.time() - start_time
    )
```

**Action:**
1. Add DependencySecurityResult dataclass
2. Add scan_dependencies() method to SecurityScanner
3. Update Gate 3 to include dependency scan
4. Add safety to requirements.txt

**Estimated Time:** 30 minutes

---

## 🟡 MAJOR 6: GitHub Download Mechanism Not Described

**Location:** `docs/TEACHER_AGENT.md`, Section 6.1, line 1997

**Current:**
```python
# Line 939
github_repo_path = await self._clone_repo(github_repo_url)
```

**Problem:**
- Метод упоминается, но не описан
- Неясно как Teacher САМ скачивает репо

**Fix:**

Add to TeacherAgent class:

```python
async def _clone_repo(self, repo_url: str) -> Path:
    """Clone GitHub repository to temp directory.
    
    Args:
        repo_url: GitHub repository URL (https://github.com/user/repo)
    
    Returns:
        Path to cloned repository
    """
    # Extract repo name
    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    
    # Create temp directory
    temp_dir = Path(".claude/temp/github-repos")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    clone_path = temp_dir / repo_name
    
    if clone_path.exists():
        # Update existing repo
        logger.info(f"Updating existing repo: {repo_name}")
        await self._run_git_command("pull", cwd=clone_path)
    else:
        # Clone new repo
        logger.info(f"Cloning repo: {repo_url}")
        await self._run_git_command(
            f"clone --depth 1 {repo_url} {clone_path}"
        )
    
    return clone_path

async def _run_git_command(self, command: str, cwd: Optional[Path] = None) -> str:
    """Run git command."""
    full_command = f"git {command}"
    
    process = await asyncio.create_subprocess_shell(
        full_command,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        raise RuntimeError(f"Git command failed: {stderr.decode()}")
    
    return stdout.decode()
```

**Action:**
1. Add _clone_repo() method to TeacherAgent
2. Add _run_git_command() helper method
3. Add to Section 6.1 (TeacherAgent Integration)

**Estimated Time:** 15 minutes

---

## 🟡 MAJOR 7: Missing Dependencies

**Location:** Throughout spec

**Problem:**
- Используются библиотеки, которых нет в requirements.txt
- radon (cyclomatic complexity)
- safety (dependency vulnerabilities)
- pytest-benchmark (performance)

**Fix:**

Add to requirements.txt:
```
# Teacher Agent v2.0 dependencies
radon>=6.0.0,<7.0.0              # Cyclomatic complexity analysis
safety>=3.0.0,<4.0.0             # Dependency vulnerability scanning
pytest-benchmark>=4.0.0,<5.0.0   # Performance benchmarking
libcst>=1.1.0,<2.0.0             # AST analysis and code transformation
```

**Action:**
1. Add dependencies to requirements.txt
2. Document in spec (Section 2)

**Estimated Time:** 5 minutes

---

## 🟡 MAJOR 8: CLI Commands Not Async

**Location:** `docs/TEACHER_AGENT.md`, Section 6.2, lines 2200-2256

**Current:**
```python
@cli.command()
@click.argument('subagent_name')
async def audit(subagent_name: str):  # ❌ async def won't work with click
    teacher = TeacherAgent(event_bus, obsidian)
    analysis = await teacher.audit_subagent(subagent_name)
    click.echo(f"Quality Score: {analysis.quality_score}/100")
```

**Problem:**
- Click не поддерживает async def напрямую
- Нужен asyncio.run() wrapper

**Fix:**

```python
@cli.command()
@click.argument('subagent_name')
def audit(subagent_name: str):  # Remove async
    """Deep audit of subagent architecture."""
    async def _audit():
        teacher = TeacherAgent(event_bus, obsidian)
        analysis = await teacher.audit_subagent(subagent_name)
        click.echo(f"Quality Score: {analysis.quality_score}/100")
    
    asyncio.run(_audit())  # Run async function

@cli.command()
@click.argument('subagent_name')
@click.option('--repo', required=True)
def compare(subagent_name: str, repo: str):
    """Compare GitHub solution with our subagent."""
    async def _compare():
        teacher = TeacherAgent(event_bus, obsidian)
        result = await teacher.compare_solution(subagent_name, repo)
        click.echo(f"Decision: {result.decision.decision}")
        click.echo(f"Rationale: {result.decision.rationale}")
    
    asyncio.run(_compare())

# Apply to all CLI commands
```

**Action:**
1. Update all CLI commands in Section 6.2
2. Remove async def from @cli.command()
3. Add asyncio.run() wrapper

**Estimated Time:** 15 minutes

---

## Summary

**Total Fix Time:** ~3 hours

**Priority Order:**
1. 🔴 Risk Score Logic (30 min) - BLOCKER
2. 🔴 Compliance Checks (1 hour) - BLOCKER
3. 🔴 Sandbox Venv (30 min) - BLOCKER
4. 🟡 Performance Metrics (30 min) - MAJOR
5. 🟡 Dependency Scan (30 min) - MAJOR
6. 🟡 GitHub Clone (15 min) - MAJOR
7. 🟡 Dependencies (5 min) - MAJOR
8. 🟡 CLI Async (15 min) - MAJOR

**After Fixes:**
- Spec ready for implementation
- All blockers resolved
- Safety mechanisms complete
- Timeline remains 8-12 hours

---

**Created:** 2026-05-13  
**Next:** Apply fixes → Sonnet review → Implementation
