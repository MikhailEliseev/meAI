# Teacher Agent v2.0 - Spec Review (Opus 4.6)

**Date:** 2026-05-13  
**Reviewer:** Deep Spec Reviewer (Opus 4.6)  
**Spec File:** docs/TEACHER_AGENT.md (2496 lines, 79 KB)  
**Product Brief:** docs/superflow/specs/2026-05-13-teacher-agent-v2-brief.md  
**Board Memo:** docs/superflow/specs/2026-05-13-teacher-agent-v2-board-memo.md

---

## Executive Summary

**Overall Assessment:** APPROVE WITH CHANGES

Спецификация Teacher Agent v2.0 детальная и хорошо структурированная, покрывает все основные компоненты автономной системы обучения. Архитектура sound, decision framework чёткий, validation gates адекватны.

**Критические проблемы (3 BLOCKERS):**
1. Risk score calculation logic неправильная (инверсия)
2. Compliance checks слишком поверхностные для medical marketing
3. Sandbox venv isolation не описана

**Готовность к реализации:** 85%  
**Требуется:** Исправить 3 blockers, добавить 5 major improvements

---

## Completeness Check

### ✅ Autonomous Decision Framework
- **Status:** COMPLETE
- DecisionMaker детально описан (Section 3.5)
- Decision rules с точными thresholds
- Third-party agent exception (≥15 points)
- Metrics degradation exception (≤5% if ≥20% improvement)

### ⚠️ GitHub Download Mechanism
- **Status:** INCOMPLETE
- Упоминается `_clone_repo()` но не описан алгоритм
- Нет описания как Teacher САМ скачивает репо (git clone? GitHub API?)
- **Impact:** MINOR - реализация очевидна, но должна быть в спеке

### ✅ Validation Gates
- **Status:** COMPLETE
- 5 gates детально описаны (Section 4.6)
- Sequential execution с early exit
- Pass/fail conditions для каждого gate

### 🔴 Gate 4 (Compliance Check) - BLOCKER
- **Status:** INCOMPLETE
- Только "Check for PII logging" - слишком поверхностно
- Нет конкретных HIPAA checks
- Medical marketing требует детальных compliance rules
- **Impact:** BLOCKER - нельзя реализовать без конкретных правил

### ✅ Rollback Mechanism
- **Status:** COMPLETE
- RollbackManager описан (Section 4.7)
- 30-day window с security exception
- Git snapshot + backup files
- Auto-rollback on validation failure

### ✅ Third-Party Agent Adoption
- **Status:** COMPLETE
- Покрыт в DecisionMaker (lines 805-818)
- Higher threshold (≥15 points)
- Integration validation

### ⚠️ CLI Interface
- **Status:** MOSTLY COMPLETE
- 7 commands описаны (Section 6.2)
- **Issue:** Click commands не async (должны быть `@click.command()` + `asyncio.run()`)
- **Impact:** MINOR - легко исправить при реализации

### ✅ Configuration Settings
- **Status:** COMPLETE
- TeacherSettings dataclass (Section 7.1)
- ValidationGateSettings (Section 7.2)
- All thresholds configurable

---

## Accuracy Check

### 🔴 Risk Score Calculation - BLOCKER

**Problem:**
```python
# Line 764 (Section 3.5)
risk_composite = 100 - risk_score.overall  # Invert

# Line 767
if quality_composite >= 80 and fit_composite >= 80 and risk_composite <= 20:
    decision = "Full"
```

**Issue:** Логика инверсии неправильная!
- `risk_score.overall` = 0-100 (100 = no risk, 0 = high risk)
- `risk_composite = 100 - risk_score.overall` → если risk_score = 80 (low risk), то risk_composite = 20
- `risk_composite <= 20` → проходит только если risk_score ≥ 80
- **НО Board Memo говорит:** "Risk ≤20" означает "low risk score"

**Correct Logic:**
```python
# Option 1: Don't invert, use risk_score directly
if quality_composite >= 80 and fit_composite >= 80 and risk_score.overall >= 80:
    # risk_score.overall ≥ 80 = low risk (100 = no risk)

# Option 2: Invert properly and adjust thresholds
risk_composite = 100 - risk_score.overall  # Now 0 = no risk, 100 = high risk
if quality_composite >= 80 and fit_composite >= 80 and risk_composite <= 20:
    # risk_composite ≤ 20 = low risk
```

**Impact:** BLOCKER - неправильные решения о adoption

**Fix Required:** Определить семантику risk_score (0 = high risk или 100 = high risk?) и исправить все decision rules

---

### ✅ Decision Thresholds
- **Status:** CORRECT
- Quality ≥80, Fit ≥80, Risk ≤20 для Full (соответствует Board Memo)
- Quality ≥70, Fit ≥70, Risk ≤30 для Partial
- Third-party threshold ≥15 points

### ✅ Validation Gates Order
- **Status:** CORRECT
- Tests → Metrics → Security → Compliance → Integration
- Sequential с early exit

### ⚠️ Dataclasses Validation
- **Status:** INCOMPLETE
- Все dataclasses используют `@dataclass` (stdlib)
- Нет validators для полей
- **Recommendation:** Использовать Pydantic для validation (уже в requirements.txt)
- **Impact:** MINOR - можно добавить позже

### ⚠️ TestCoverageAnalyzer Algorithm
- **Status:** OVERSIMPLIFIED
- "coverage estimate based on test count vs functions" - слишком упрощённо
- Не учитывает реальное покрытие (branch coverage, line coverage)
- **Recommendation:** Использовать `pytest-cov` для реального coverage
- **Impact:** MINOR - estimate достаточен для v2.0, можно улучшить позже

---

## Feasibility Check

### ✅ 8-12 Hours Timeline
- **Status:** REALISTIC (на верхней границе)
- Phase 1 (3-4h): 5 analyzers + tests - REALISTIC
- Phase 2 (2-3h): 5 scorers + DecisionMaker + tests - REALISTIC
- Phase 3 (3-4h): 8 components + tests - TIGHT (может быть 4-5h)
- Phase 4 (1-2h): 4 components + CLI + tests - REALISTIC
- **Total:** 9-13 hours (в пределах, но на верхней границе)

### ⚠️ Dependencies
- **Status:** MOSTLY AVAILABLE
- ✅ LibCST - доступен (AST analysis)
- ✅ networkx - доступен (dependency graph)
- ✅ bandit - доступен (security scan)
- ✅ pytest - уже используется
- ❌ **Missing:** `radon` для cyclomatic complexity (нужен для maintainability score)
- ❌ **Missing:** `safety` или `pip-audit` для dependency vulnerabilities
- **Impact:** MINOR - добавить в requirements.txt

### 🔴 Sandbox Venv Isolation - BLOCKER
- **Status:** NOT DESCRIBED
- Git worktree описан, но нет упоминания venv isolation
- DependencyInstaller должен работать в sandbox venv, не в main
- Без venv isolation: риск сломать main environment
- **Impact:** BLOCKER - критично для безопасности
- **Fix Required:** Добавить в SandboxManager создание venv для каждого sandbox

### ⚠️ Performance Metrics
- **Status:** NOT DESCRIBED
- Metrics Check gate проверяет "performance", но не описано как измерять
- Нужен benchmark framework (pytest-benchmark?)
- **Impact:** MAJOR - без этого Gate 2 неполный
- **Recommendation:** Добавить performance benchmarking в ValidationGateRunner

### ✅ API Integrations
- **Status:** REALISTIC
- GitHub API - реалистично (search repos, clone)
- git worktree - реалистично (sandbox isolation)

---

## Autonomy Check

### ✅ NO Approval Workflows
- **Status:** COMPLIANT
- Нет упоминаний approval в workflow
- DecisionMaker принимает решения автономно
- Auto-merge при успешной валидации
- Auto-rollback при проблемах

### ✅ NO User Confirmation Gates
- **Status:** COMPLIANT
- Validation gates автоматические
- Нет "wait for user" steps

### ✅ Notifications Only
- **Status:** COMPLIANT
- NotificationSender отправляет notifications (Section 5.3)
- Не approval requests
- 3 типа notifications: success, failed, rejection

### ✅ All Decisions Automatic
- **Status:** COMPLIANT
- Decision rules чёткие и автоматические
- Thresholds определены в config

---

## Safety Check

### ⚠️ Sandbox Isolation
- **Status:** PARTIAL
- ✅ Git worktree для изоляции кода
- 🔴 **Missing:** Venv isolation для зависимостей (BLOCKER)
- **Impact:** HIGH - без venv можем сломать main environment

### 🔴 Compliance Checks - BLOCKER
- **Status:** INSUFFICIENT
- Gate 4 только "Check for PII logging" - слишком поверхностно
- Medical marketing требует детальных HIPAA checks:
  - PHI (Protected Health Information) detection
  - Encryption at rest (AES-256)
  - Encryption in transit (TLS 1.2+)
  - Audit logging (who, what, when)
  - Access controls (RBAC)
  - Data retention policies
- **Impact:** BLOCKER - нельзя использовать в medical marketing без этого
- **Fix Required:** Добавить конкретные HIPAA compliance rules в Gate 4

### ✅ Rollback Mechanism
- **Status:** ADEQUATE
- Git snapshot + backup files
- 30-day window с security exception
- Auto-rollback on failure

### ⚠️ Security Checks
- **Status:** PARTIAL
- ✅ Bandit для security scan
- ✅ Hardcoded secrets check
- ❌ **Missing:** Dependency vulnerability scan (safety/pip-audit)
- **Impact:** MAJOR - можем внедрить vulnerable dependencies
- **Recommendation:** Добавить dependency scan в Gate 3

---

## Issues Found

### 🔴 BLOCKERS (must fix before implementation)

#### 1. Risk Score Calculation Logic
- **Location:** Section 3.5, lines 762-800
- **Problem:** Инверсия risk_score неправильная, приводит к неправильным решениям
- **Impact:** Teacher будет принимать неправильные решения о adoption
- **Fix:**
  ```python
  # Define risk_score semantics clearly:
  # Option A: risk_score.overall = 0-100 (100 = no risk, 0 = high risk)
  # Then use directly without inversion:
  if quality >= 80 and fit >= 80 and risk_score.overall >= 80:
      decision = "Full"  # risk ≥ 80 = low risk
  
  # Option B: risk_score.overall = 0-100 (0 = no risk, 100 = high risk)
  # Then invert is correct:
  if quality >= 80 and fit >= 80 and risk_score.overall <= 20:
      decision = "Full"  # risk ≤ 20 = low risk
  
  # Choose one and update ALL decision rules consistently
  ```

#### 2. Compliance Checks Insufficient
- **Location:** Section 4.6, Gate 4 (lines 1398-1400)
- **Problem:** Только "Check for PII logging" - недостаточно для HIPAA
- **Impact:** Не можем использовать в medical marketing без детальных checks
- **Fix:** Добавить конкретные HIPAA compliance rules:
  ```python
  class ComplianceChecker:
      async def check_hipaa_compliance(self, repo_path: Path) -> ComplianceResult:
          checks = {
              "phi_detection": self._check_phi_logging(repo_path),
              "encryption_at_rest": self._check_encryption_at_rest(repo_path),
              "encryption_in_transit": self._check_tls_usage(repo_path),
              "audit_logging": self._check_audit_trail(repo_path),
              "access_controls": self._check_rbac(repo_path),
              "data_retention": self._check_retention_policy(repo_path)
          }
          
          all_passed = all(checks.values())
          return ComplianceResult(
              passed=all_passed,
              checks=checks,
              details=self._generate_report(checks)
          )
  ```

#### 3. Sandbox Venv Isolation Missing
- **Location:** Section 4.1 (SandboxManager, lines 986-1051)
- **Problem:** Нет описания venv isolation для зависимостей
- **Impact:** Риск сломать main environment при установке dependencies
- **Fix:** Добавить venv creation в SandboxManager:
  ```python
  class SandboxManager:
      async def create_sandbox(self, subagent_name: str, adoption_id: str) -> SandboxEnvironment:
          # Create worktree
          worktree_path = Path(f".claude/worktrees/teacher-{adoption_id}")
          branch_name = f"teacher/{subagent_name}-{adoption_id}"
          
          await self._run_git_command(f"worktree add {worktree_path} -b {branch_name}")
          
          # Create isolated venv
          venv_path = worktree_path / ".venv"
          await self._create_venv(venv_path)
          
          # Create snapshot
          snapshot_id = await self._get_current_commit_hash()
          
          return SandboxEnvironment(
              worktree_path=worktree_path,
              branch_name=branch_name,
              venv_path=venv_path,  # ADD THIS
              snapshot_id=snapshot_id,
              created_at=datetime.now()
          )
  ```

---

### 🟡 MAJOR (should fix)

#### 4. Performance Metrics Not Defined
- **Location:** Section 4.6, Gate 2 (lines 1381-1386)
- **Problem:** "Metrics Check" упоминает performance, но не описано как измерять
- **Impact:** Gate 2 неполный, не можем проверить performance degradation
- **Fix:** Добавить performance benchmarking:
  ```python
  class MetricsChecker:
      async def check_performance(self, sandbox: SandboxEnvironment, subagent_name: str) -> PerformanceMetrics:
          # Run pytest-benchmark
          benchmark_results = await self._run_benchmarks(sandbox, subagent_name)
          
          # Compare with baseline
          baseline = await self._load_baseline_metrics(subagent_name)
          
          return PerformanceMetrics(
              response_time_ms=benchmark_results.mean,
              throughput_rps=benchmark_results.ops_per_sec,
              memory_mb=benchmark_results.peak_memory,
              degradation_percent=self._calculate_degradation(benchmark_results, baseline)
          )
  ```

#### 5. Dependency Vulnerability Scan Missing
- **Location:** Section 4.6, Gate 3 (lines 1387-1392)
- **Problem:** Bandit проверяет код, но не проверяет dependencies на vulnerabilities
- **Impact:** Можем внедрить vulnerable dependencies (CVEs)
- **Fix:** Добавить dependency scan:
  ```python
  class SecurityScanner:
      async def scan_dependencies(self, repo_path: Path) -> DependencySecurityResult:
          # Run safety or pip-audit
          vulnerabilities = await self._run_safety_check(repo_path)
          
          high_severity = [v for v in vulnerabilities if v.severity == "high"]
          medium_severity = [v for v in vulnerabilities if v.severity == "medium"]
          
          passed = len(high_severity) == 0 and len(medium_severity) == 0
          
          return DependencySecurityResult(
              passed=passed,
              vulnerabilities=vulnerabilities,
              details=self._format_vulnerabilities(vulnerabilities)
          )
  ```

#### 6. GitHub Download Mechanism Not Described
- **Location:** Section 6.1, line 1997 (`_clone_repo()`)
- **Problem:** Упоминается но не описан алгоритм
- **Impact:** Неясно как Teacher САМ скачивает репо
- **Fix:** Добавить в TeacherAgent:
  ```python
  async def _clone_repo(self, repo_url: str) -> Path:
      """Clone GitHub repo to temp directory."""
      repo_name = repo_url.split("/")[-1].replace(".git", "")
      clone_path = Path(f".claude/temp/github-repos/{repo_name}")
      
      if clone_path.exists():
          # Update existing repo
          await self._run_git_command(f"pull", cwd=clone_path)
      else:
          # Clone new repo
          await self._run_git_command(f"clone {repo_url} {clone_path}")
      
      return clone_path
  ```

#### 7. Missing Dependencies in Requirements
- **Location:** Section 2 (Architecture Analysis Layer)
- **Problem:** Используются `radon`, `safety`/`pip-audit` но не в requirements.txt
- **Impact:** Не можем реализовать без этих библиотек
- **Fix:** Добавить в requirements.txt:
  ```
  radon>=6.0.0,<7.0.0           # Cyclomatic complexity
  safety>=3.0.0,<4.0.0          # Dependency vulnerability scan
  pytest-benchmark>=4.0.0       # Performance benchmarking
  ```

#### 8. CLI Commands Not Async
- **Location:** Section 6.2, lines 2200-2256
- **Problem:** Click commands используют `async def` но не вызывают `asyncio.run()`
- **Impact:** CLI не будет работать (async functions нужно запускать через asyncio.run)
- **Fix:**
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
  ```

---

### 🟢 MINOR (nice to have)

#### 9. Dataclasses Should Use Pydantic
- **Location:** All dataclasses (Sections 2-4)
- **Problem:** Используется stdlib `@dataclass`, нет validation
- **Impact:** Можем получить invalid data в runtime
- **Recommendation:** Использовать Pydantic BaseModel для validation
- **Priority:** LOW - можно добавить позже

#### 10. TestCoverageAnalyzer Oversimplified
- **Location:** Section 2.1.4, lines 320-361
- **Problem:** "coverage estimate based on test count vs functions" - слишком упрощённо
- **Impact:** Неточная оценка test coverage
- **Recommendation:** Использовать `pytest-cov` для реального coverage
- **Priority:** LOW - estimate достаточен для v2.0

---

## Recommendation

**APPROVE WITH CHANGES**

Спецификация качественная и детальная, но требует исправления 3 критических blockers перед реализацией:

1. **Risk score calculation logic** - исправить инверсию
2. **Compliance checks** - добавить детальные HIPAA rules
3. **Sandbox venv isolation** - добавить venv creation

После исправления blockers, спецификация готова к реализации.

**Estimated Fix Time:** 2-3 hours (добавить недостающие детали)

---

## Next Steps

### Immediate (Before Implementation)

1. **Fix Risk Score Logic** (30 min)
   - Определить семантику risk_score (0 = high или 100 = high?)
   - Обновить все decision rules
   - Добавить unit tests для decision logic

2. **Add HIPAA Compliance Rules** (1 hour)
   - Детализировать Gate 4 (Compliance Check)
   - Добавить 6 конкретных checks (PHI, encryption, audit, etc.)
   - Добавить ComplianceChecker class

3. **Add Sandbox Venv Isolation** (30 min)
   - Обновить SandboxManager
   - Добавить venv creation
   - Обновить DependencyInstaller для работы с sandbox venv

4. **Add Performance Metrics** (30 min)
   - Детализировать Gate 2 (Metrics Check)
   - Добавить performance benchmarking
   - Добавить MetricsChecker class

5. **Add Dependency Vulnerability Scan** (30 min)
   - Обновить Gate 3 (Security Scan)
   - Добавить safety/pip-audit integration
   - Обновить SecurityScanner class

### After Fixes (Implementation Phase)

6. **Update Requirements.txt**
   - Добавить radon, safety, pytest-benchmark

7. **Fix CLI Async**
   - Обновить CLI commands для правильного async/await

8. **Add GitHub Clone Method**
   - Реализовать `_clone_repo()` в TeacherAgent

### Optional (Post-v2.0)

9. **Migrate to Pydantic** - для validation
10. **Improve TestCoverageAnalyzer** - использовать pytest-cov

---

## Conclusion

Спецификация Teacher Agent v2.0 хорошо продумана и покрывает все основные компоненты автономной системы обучения. Архитектура sound, decision framework чёткий, validation gates адекватны для medical marketing context.

**Strengths:**
- ✅ Полная автономия (no approval workflows)
- ✅ Детальный decision framework с чёткими thresholds
- ✅ 5 validation gates для безопасности
- ✅ Rollback mechanism с 30-day window
- ✅ Audit trail для всех решений
- ✅ Realistic 8-12 hours timeline

**Weaknesses:**
- 🔴 Risk score calculation logic неправильная
- 🔴 Compliance checks недостаточно детальные для HIPAA
- 🔴 Sandbox venv isolation не описана
- 🟡 Performance metrics не определены
- 🟡 Dependency vulnerability scan отсутствует

**After fixing 3 blockers:** Спецификация готова к реализации с высокой уверенностью в успехе.

---

**Review Completed:** 2026-05-13  
**Reviewer:** Deep Spec Reviewer (Opus 4.6)  
**Status:** ✅ APPROVE WITH CHANGES (fix 3 blockers)
