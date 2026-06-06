"""
Integration tests for CI Pipeline — Phase 1-4 fixes.

Covers:
  - wow_estimator (Phase 4)
  - CiMarketingAnalyzer: tactics, SWOT, summary, recommendation (Phase 1)
  - AuditTask persistence (Phase 2 H5 fix)
  - _generate_analysis_summary output structure (Phase 1 H4 fix)
"""

import json
import os
import tempfile
import time
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.aim.services.ci.wow_estimator import compute_wow_numbers
from src.aim.services.ci.models import WowMetrics
from src.aim.services.ci_marketing_analysis import (
    CiAnalysisResult,
    SwotQuadrant,
    StealWorthyTactic,
    _tactic_impact_effort,
)
from src.aim.subagents.competitive_intel.orchestrator.ci_orchestrator import CIOrchestrator


# ── Fixtures ──────────────────────────────────────────────────────────


def _make_fake_matrix(competitors=None, client=None):
    """Build a ComparisonMatrix-like object for testing."""

    class FakeMatrix:
        pass

    m = FakeMatrix()
    m.competitors = competitors or []
    m.client = client or {"features": [], "missing": []}
    return m


def _competitor_a():
    return {
        "name": "Конкурент А",
        "url": "https://a.ru",
        "website": {
            "features": ["онлайн-запись", "калькулятор цен"],
            "pricing_visible": True,
            "missing": [],
        },
        "seo": {"score": 45, "issues": ["no ssl", "missing h1 on 12 pages"]},
        "social": {
            "instagram": {"exists": True, "handle": "a_inst", "posts_month": 10, "avg_likes": 200, "topics": []},
            "telegram": {"exists": False},
            "vk": {"exists": True, "handle": "a_vk", "posts_month": 5, "avg_likes": 50, "topics": []},
        },
        "financials": {"latest_revenue": 50_000_000, "trend": "растёт"},
        "gm_rating": 4.2,
        "gm_reviews_count": 25,
        "yandex_rating": 4.0,
        "yandex_reviews_count": 15,
        "prodoctorov_rating": 3.9,
        "prodoctorov_reviews_count": 8,
        "positioning": "Премиум-стоматология в центре Казани",
        "doctors": [
            {"name": "Иванов И.И.", "is_leader": True, "influence_score": 75, "specialty": "ортодонт"},
        ],
    }


def _competitor_b():
    return {
        "name": "Конкурент Б",
        "url": "https://b.ru",
        "website": {
            "features": [],
            "pricing_visible": False,
            "missing": ["онлайн-запись", "калькулятор цен"],
        },
        "seo": {"score": 85, "issues": []},
        "social": {},
        "financials": {},
        "gm_rating": 0,
        "gm_reviews_count": 0,
        "yandex_rating": 3.5,
        "yandex_reviews_count": 10,
        "prodoctorov_rating": 0,
        "prodoctorov_reviews_count": 0,
        "positioning": "",
        "doctors": [],
    }


@pytest.fixture
def analyzer():
    from meai.events.event_bus import EventBus
    return CIOrchestrator(agent_id="test-analyzer", event_bus=EventBus())


@pytest.fixture
def matrix_two_comps():
    return _make_fake_matrix(
        competitors=[_competitor_a(), _competitor_b()],
        client={"features": ["чат"], "missing": ["онлайн-запись", "калькулятор цен"]},
    )


@pytest.fixture
def matrix_empty():
    return _make_fake_matrix(competitors=[], client={"features": [], "missing": []})


# ── Phase 4: wow_estimator ────────────────────────────────────────────


class TestWowEstimator:
    def test_weak_competitors(self):
        """Weak SEO + low ratings → high patient capture."""
        r = compute_wow_numbers(
            competitor_count=5, avg_seo_score=45, avg_rating=3.8,
            pricing_visible_ratio=0.3, booking_ratio=0.2,
        )
        assert r.patients_per_month == 63  # 10+25+15+5+5+3
        assert r.time_to_result_weeks == 4
        assert r.cost_per_patient_rub == 900  # 1200-300
        assert r.is_estimated is True

    def test_strong_competitors(self):
        """Strong SEO + high ratings → slow growth."""
        r = compute_wow_numbers(
            competitor_count=8, avg_seo_score=80, avg_rating=4.5,
            pricing_visible_ratio=0.8, booking_ratio=0.9,
        )
        assert r.patients_per_month == 50  # 10+40, no bonuses
        assert r.time_to_result_weeks == 12
        assert r.cost_per_patient_rub == 1800

    def test_empty_defaults(self):
        """Zero inputs → reasonable defaults with pricing/booking bonuses."""
        r = compute_wow_numbers()
        assert r.patients_per_month == 18  # 10 + 5 (pricing) + 3 (booking)
        assert r.time_to_result_weeks == 8
        assert r.cost_per_patient_rub == 800

    def test_single_competitor(self):
        """One competitor → cheapest acquisition."""
        r = compute_wow_numbers(competitor_count=1, avg_seo_score=60, avg_rating=4.0)
        assert r.cost_per_patient_rub == 800
        assert r.patients_per_month >= 15  # 10+5, +5 for SEO 50-70

    def test_wow_metrics_dataclass(self):
        """WowMetrics dataclass works."""
        w = WowMetrics(patients_per_month=30, time_to_result_weeks=8, cost_per_patient_rub=1200, is_estimated=True)
        assert w.patients_per_month == 30
        assert w.is_estimated is True

        w2 = WowMetrics()
        assert w2.patients_per_month is None
        assert w2.is_estimated is False


# ── Phase 1: Tactic classifier ────────────────────────────────────────


class TestTacticClassifier:
    def test_high_impact_keywords(self):
        assert _tactic_impact_effort("онлайн-запись") == ("High", "Medium")
        assert _tactic_impact_effort("online booking") == ("High", "Medium")
        assert _tactic_impact_effort("цены") == ("High", "Low")
        assert _tactic_impact_effort("отзывы") == ("High", "Low")

    def test_medium_impact_default(self):
        assert _tactic_impact_effort("дизайн сайта") == ("Medium", "Low")
        assert _tactic_impact_effort("something random") == ("Medium", "Low")

    def test_effort_classification(self):
        assert _tactic_impact_effort("личный кабинет") == ("High", "Medium")
        assert _tactic_impact_effort("калькулятор") == ("High", "Medium")


# ── Phase 1: Tactics extraction ───────────────────────────────────────


class TestTacticsExtraction:
    def test_extracts_tactics_from_matrix(self, analyzer, matrix_two_comps):
        tactics = analyzer._extract_tactics_from_matrix(matrix_two_comps)
        assert len(tactics) > 0, "Tactics should not be empty"

    def test_tactic_structure(self, analyzer, matrix_two_comps):
        tactics = analyzer._extract_tactics_from_matrix(matrix_two_comps)
        for t in tactics:
            assert t.tactic_description
            assert t.source_competitor
            assert t.expected_impact
            assert t.estimated_effort
            assert t.why_it_works

    def test_tactics_sorted_by_impact(self, analyzer, matrix_two_comps):
        tactics = analyzer._extract_tactics_from_matrix(matrix_two_comps)
        impact_order = {"High": 0, "Medium": 1, "Low": 2}
        for i in range(len(tactics) - 1):
            a = impact_order[tactics[i].expected_impact]
            b = impact_order[tactics[i + 1].expected_impact]
            assert a <= b, f"Tactics not sorted: {tactics[i].expected_impact} before {tactics[i+1].expected_impact}"

    def test_tactics_max_8(self, analyzer, matrix_two_comps):
        tactics = analyzer._extract_tactics_from_matrix(matrix_two_comps)
        assert len(tactics) <= 8

    def test_weak_seo_tactic(self, analyzer, matrix_two_comps):
        tactics = analyzer._extract_tactics_from_matrix(matrix_two_comps)
        seo_tactics = [t for t in tactics if "SEO" in t.tactic_description]
        assert len(seo_tactics) > 0, "Should include SEO exploit tactic for weak-SEO competitor"

    def test_no_pricing_tactic(self, analyzer, matrix_two_comps):
        tactics = analyzer._extract_tactics_from_matrix(matrix_two_comps)
        pricing_tactics = [t for t in tactics if "цены" in t.tactic_description.lower()]
        assert len(pricing_tactics) > 0, "Should include pricing transparency tactic"


# ── Phase 1: SWOT extraction ──────────────────────────────────────────


class TestSwotExtraction:
    def test_swot_has_all_quadrants(self, analyzer, matrix_two_comps):
        swot = analyzer._extract_swot_from_matrix(matrix_two_comps)
        assert "strengths" in swot
        assert "weaknesses" in swot
        assert "opportunities" in swot
        assert "threats" in swot

    def test_swot_not_empty(self, analyzer, matrix_two_comps):
        swot = analyzer._extract_swot_from_matrix(matrix_two_comps)
        assert len(swot["strengths"]) > 0
        assert len(swot["weaknesses"]) > 0
        assert len(swot["opportunities"]) > 0
        assert len(swot["threats"]) > 0

    def test_swot_max_5(self, analyzer, matrix_two_comps):
        swot = analyzer._extract_swot_from_matrix(matrix_two_comps)
        for quadrant in ["strengths", "weaknesses", "opportunities", "threats"]:
            assert len(swot[quadrant]) <= 5, f"{quadrant} has {len(swot[quadrant])} items, max 5"

    def test_empty_matrix_defaults(self, analyzer, matrix_empty):
        swot = analyzer._extract_swot_from_matrix(matrix_empty)
        assert any("локальный рынок" in s for s in swot["strengths"])
        assert len(swot["opportunities"]) > 0  # default opportunity


# ── Phase 1: Top recommendation ───────────────────────────────────────


class TestTopRecommendation:
    def test_targets_weak_seo(self, analyzer, matrix_two_comps):
        rec = analyzer._top_rec_from_matrix(matrix_two_comps)
        assert "Конкурент А" in rec
        assert "SEO" in rec
        assert "45" in rec  # their SEO score

    def test_empty_matrix_fallback(self, analyzer, matrix_empty):
        rec = analyzer._top_rec_from_matrix(matrix_empty)
        assert isinstance(rec, str)
        assert len(rec) > 10

    def test_substantive_output(self, analyzer, matrix_two_comps):
        rec = analyzer._top_rec_from_matrix(matrix_two_comps)
        assert len(rec) > 40, f"Recommendation too short: {len(rec)} chars"


# ── Phase 1 H4: Analysis summary ──────────────────────────────────────


class TestAnalysisSummary:
    def test_has_all_sections(self, analyzer, matrix_two_comps):
        swot = analyzer._extract_swot_from_matrix(matrix_two_comps)
        tactics = analyzer._extract_tactics_from_matrix(matrix_two_comps)
        rec = analyzer._top_rec_from_matrix(matrix_two_comps)
        wow = {"patients_per_month": 63, "time_to_result_weeks": 4, "cost_per_patient_rub": 900, "is_estimated": True}

        summary = analyzer._generate_analysis_summary(matrix_two_comps, swot, tactics, rec, wow)

        assert "Обзор конкурентной среды" in summary
        assert "По конкурентам" in summary
        assert "SWOT-анализ" in summary
        assert "Что можно внедрить" in summary
        assert "Прогноз по пациентам" in summary
        assert "Главная рекомендация" in summary

    def test_includes_competitor_names(self, analyzer, matrix_two_comps):
        swot = analyzer._extract_swot_from_matrix(matrix_two_comps)
        tactics = analyzer._extract_tactics_from_matrix(matrix_two_comps)
        rec = analyzer._top_rec_from_matrix(matrix_two_comps)
        wow = {"patients_per_month": 63, "time_to_result_weeks": 4, "cost_per_patient_rub": 900}

        summary = analyzer._generate_analysis_summary(matrix_two_comps, swot, tactics, rec, wow)

        assert "Конкурент А" in summary
        assert "Конкурент Б" in summary

    def test_empty_matrix_message(self, analyzer, matrix_empty):
        swot = analyzer._extract_swot_from_matrix(matrix_empty)
        tactics = analyzer._extract_tactics_from_matrix(matrix_empty)
        rec = analyzer._top_rec_from_matrix(matrix_empty)
        wow = {}

        summary = analyzer._generate_analysis_summary(matrix_empty, swot, tactics, rec, wow)
        assert "Не удалось найти конкурентов" in summary

    def test_wow_section_skipped_when_empty(self, analyzer, matrix_two_comps):
        swot = analyzer._extract_swot_from_matrix(matrix_two_comps)
        tactics = analyzer._extract_tactics_from_matrix(matrix_two_comps)
        rec = analyzer._top_rec_from_matrix(matrix_two_comps)

        summary = analyzer._generate_analysis_summary(matrix_two_comps, swot, tactics, rec, {})
        assert "Прогноз по пациентам" not in summary  # no wow data

    def test_tactics_section_skipped_when_empty(self, analyzer, matrix_two_comps):
        swot = analyzer._extract_swot_from_matrix(matrix_two_comps)
        rec = analyzer._top_rec_from_matrix(matrix_two_comps)
        wow = {"patients_per_month": 10}

        summary = analyzer._generate_analysis_summary(matrix_two_comps, swot, [], rec, wow)
        assert "Что можно внедрить" not in summary


# ── Phase 1: CiAnalysisResult ─────────────────────────────────────────


class TestCiAnalysisResult:
    def test_default_wow_is_none(self):
        r = CiAnalysisResult()
        assert r.wow is None

    def test_wow_assignment(self):
        r = CiAnalysisResult()
        r.wow = {"patients_per_month": 30, "time_to_result_weeks": 8, "cost_per_patient_rub": 1200}
        assert r.wow["patients_per_month"] == 30

    def test_tactics_field(self):
        r = CiAnalysisResult()
        r.steal_worthy_tactics = [StealWorthyTactic(
            source_competitor="X",
            tactic_description="test",
            why_it_works="test",
            estimated_effort="Low",
            expected_impact="High",
        )]
        assert len(r.steal_worthy_tactics) == 1

    def test_swot_field(self):
        r = CiAnalysisResult()
        r.aggregate_swot = SwotQuadrant(
            strengths=["s1"], weaknesses=["w1"], opportunities=["o1"], threats=["t1"]
        )
        assert r.aggregate_swot.strengths == ["s1"]

    def test_all_fields_present(self):
        r = CiAnalysisResult()
        assert hasattr(r, "chat_summary")
        assert hasattr(r, "feature_matrix")
        assert hasattr(r, "pricing_comparison")
        assert hasattr(r, "positioning_map")
        assert hasattr(r, "steal_worthy_tactics")
        assert hasattr(r, "aggregate_swot")
        assert hasattr(r, "top_recommendation")
        assert hasattr(r, "wow")
        assert hasattr(r, "error")
        assert hasattr(r, "analysis_duration_seconds")


# ── Phase 2 H5: AuditTask persistence ─────────────────────────────────


class TestAuditTaskPersistence:
    def test_to_dict(self):
        from src.aim.api.seo import AuditTask

        task = AuditTask(task_id="test-1", status="pending", progress="Запуск...")
        task.started_at = time.time()

        d = task.to_dict()
        assert d["task_id"] == "test-1"
        assert d["status"] == "pending"
        assert d["progress"] == "Запуск..."
        assert d["result"] is None
        assert d["error"] is None

    def test_from_dict(self):
        from src.aim.api.seo import AuditTask

        d = {
            "task_id": "test-2",
            "status": "done",
            "result": {"wow": {"patients_per_month": 30}},
            "error": None,
            "started_at": 1000.0,
            "finished_at": 2000.0,
            "progress": "Готово",
        }
        task = AuditTask.from_dict(d)
        assert task.task_id == "test-2"
        assert task.status == "done"
        assert task.result["wow"]["patients_per_month"] == 30
        assert task.finished_at == 2000.0

    def test_roundtrip(self):
        from src.aim.api.seo import AuditTask

        original = AuditTask(
            task_id="roundtrip-1",
            status="running",
            progress="Анализирую...",
            started_at=time.time(),
        )
        original.result = {"competitors": 5}

        restored = AuditTask.from_dict(original.to_dict())
        assert restored.task_id == original.task_id
        assert restored.status == original.status
        assert restored.result == original.result

    def test_file_persist_and_load(self):
        tmp = tempfile.mkdtemp()
        try:
            tasks_file = Path(tmp) / "seo_audit_tasks.json"

            from src.aim.api.seo import AuditTask

            # Create and save
            task = AuditTask(task_id="persist-1", status="done", finished_at=time.time())
            task.result = {"wow": {"patients_per_month": 42}}
            tasks_file.parent.mkdir(parents=True, exist_ok=True)
            tasks_file.write_text(
                json.dumps([task.to_dict()], ensure_ascii=False, indent=2)
            )

            # Read back
            data = json.loads(tasks_file.read_text())
            assert len(data) == 1
            restored = AuditTask.from_dict(data[0])
            assert restored.task_id == "persist-1"
            assert restored.result["wow"]["patients_per_month"] == 42
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)

    def test_ttl_expired_cleanup(self):
        from src.aim.api.seo import AuditTask

        # Create expired task
        old = AuditTask(
            task_id="expired-1",
            status="done",
            finished_at=time.time() - 100_000,  # ~28 hours ago
        )
        # Create fresh task
        fresh = AuditTask(
            task_id="fresh-1",
            status="done",
            finished_at=time.time() - 60,  # 1 minute ago
        )

        now = time.time()
        TTL = 86400  # 24 hours

        data = [old.to_dict(), fresh.to_dict()]
        filtered = []
        for td in data:
            finished = td.get("finished_at", 0)
            if finished and td.get("status") in ("done", "error") and (now - finished) > TTL:
                continue
            filtered.append(td)

        assert len(filtered) == 1
        assert filtered[0]["task_id"] == "fresh-1"

    def test_running_task_not_expired(self):
        from src.aim.api.seo import AuditTask

        # Running task that started long ago — should NOT be cleaned up
        running = AuditTask(
            task_id="running-old",
            status="running",
            started_at=time.time() - 100_000,
            finished_at=0,
        )

        now = time.time()
        TTL = 86400

        finished = running.finished_at
        if finished and running.status in ("done", "error") and (now - finished) > TTL:
            expired = True
        else:
            expired = False

        assert not expired, "Running task should never be expired"


# ── Phase 3: CIOrchestrator has Path 1 ────────────────────────────────


class TestCIOrchestratorStructure:
    def test_execute_ci_analysis_exists(self):
        from src.aim.subagents.competitive_intel.orchestrator.ci_orchestrator import CIOrchestrator
        assert hasattr(CIOrchestrator, "execute_ci_analysis")

    def test_path2_stubs_removed(self):
        from src.aim.subagents.competitive_intel.orchestrator.ci_orchestrator import CIOrchestrator
        assert not hasattr(CIOrchestrator, "_delegate_to_agent"), "_delegate_to_agent stub should be removed"
        assert not hasattr(CIOrchestrator, "_execute_single_agent"), "_execute_single_agent stub should be removed"
        assert not hasattr(CIOrchestrator, "_execute_phase_stub"), "_execute_phase_stub should be removed"


# ── Phase 4: models consistency ───────────────────────────────────────


class TestModelsConsistency:
    def test_wow_metrics_importable(self):
        from src.aim.services.ci.models import WowMetrics
        w = WowMetrics(patients_per_month=10, time_to_result_weeks=4, cost_per_patient_rub=800)
        assert w.patients_per_month == 10

    def test_all_models_importable(self):
        from src.aim.services.ci.models import (
            SeoAuditResult, SocialProfile, SocialScanResult,
            DoctorInfo, CompetitorFull, ComparisonMatrix, PipelineProgress,
        )
        # All imports succeed
        assert True


# ── Phase 21: Unified Architecture ───────────────────────────────────

class TestUnifiedArchitecture:
    """Phase 21 — CI Pipeline Unification."""

    def test_unified_result_quick_defaults(self):
        from src.aim.services.ci.models import UnifiedCiResult
        r = UnifiedCiResult()
        assert r.tier == "quick"
        assert r.is_quick is True
        assert r.chat_summary == ""
        assert r.feature_matrix == {}
        assert r.findings == {}

    def test_unified_result_deep_tier(self):
        from src.aim.services.ci.models import UnifiedCiResult
        r = UnifiedCiResult(
            tier="deep",
            findings={"phase_1": {"status": "success"}},
            phases_executed=[1, 2, 3],
            competitors_analyzed=5,
            quality_score={"score": 85},
        )
        assert r.is_quick is False
        assert r.findings["phase_1"]["status"] == "success"
        assert r.phases_executed == [1, 2, 3]
        assert r.competitors_analyzed == 5

    def test_unified_result_to_dict(self):
        from src.aim.services.ci.models import UnifiedCiResult, SwotQuadrant, StealWorthyTactic
        r = UnifiedCiResult(
            tier="quick",
            chat_summary="test summary",
            feature_matrix={"competitors": [{"name": "C1"}]},
            aggregate_swot=SwotQuadrant(strengths=["s1"]),
            steal_worthy_tactics=[StealWorthyTactic(
                source_competitor="C1",
                tactic_description="t1",
                why_it_works="because",
            )],
            wow={"patients_per_month": 30},
            analysis_duration_seconds=5.5,
        )
        d = r.to_dict()
        assert d["tier"] == "quick"
        assert d["chat_summary"] == "test summary"
        assert d["feature_matrix"]["competitors"][0]["name"] == "C1"
        assert d["aggregate_swot"]["strengths"] == ["s1"]
        assert d["steal_worthy_tactics"][0]["tactic"] == "t1"
        assert d["wow"]["patients_per_month"] == 30
        assert d["analysis_duration_seconds"] == 5.5

    def test_ci_analysis_result_backward_compat(self):
        from src.aim.services.ci_marketing_analysis import CiAnalysisResult, SwotQuadrant
        r = CiAnalysisResult()
        assert hasattr(r, "chat_summary")
        assert hasattr(r, "feature_matrix")
        assert hasattr(r, "steal_worthy_tactics")
        assert hasattr(r, "aggregate_swot")
        assert hasattr(r, "top_recommendation")
        assert hasattr(r, "wow")
        assert hasattr(r, "error")
        assert hasattr(r, "analysis_duration_seconds")
        # New Phase 21 fields
        assert hasattr(r, "tier")
        assert hasattr(r, "findings")
        assert hasattr(r, "phases_executed")

    async def test_orchestrator_event_bus_injection(self):
        from meai.events.event_bus import EventBus
        from src.aim.subagents.competitive_intel.orchestrator.ci_orchestrator import CIOrchestrator

        eb = EventBus()
        o = CIOrchestrator(agent_id="test-w5", event_bus=eb)

        # Agent should use shared event_bus
        scout = await o._get_agent("ci-scout")
        assert scout is not None
        assert scout.event_bus is eb

    def test_orchestrator_tier_routing_has_quick_path(self):
        import inspect
        from src.aim.subagents.competitive_intel.orchestrator.ci_orchestrator import CIOrchestrator

        src = inspect.getsource(CIOrchestrator.execute_ci_analysis)
        assert "tier" in src
        assert "quick" in src
        assert "_run_quick_analysis" in src

    def test_orchestrator_agent_type_set(self):
        from meai.events.event_bus import EventBus
        from src.aim.subagents.competitive_intel.orchestrator.ci_orchestrator import CIOrchestrator

        o = CIOrchestrator(agent_id="test-w5b", event_bus=EventBus())
        assert o.agent_type == "ci-orchestrator"

    def test_swot_quadrant_in_models(self):
        from src.aim.services.ci.models import SwotQuadrant
        s = SwotQuadrant(strengths=["s1"], weaknesses=["w1"])
        assert s.strengths == ["s1"]


# ── Phase 21: EventBus delegation end-to-end ──────────────────────────

import asyncio
from datetime import datetime, timezone
from meai.agents.base_agent import Agent, Task, TaskResult, TaskStatus
from meai.events.event_bus import Message


class _MinimalTaskAgent(Agent):
    """Minimal Agent for testing _listen_for_tasks EventBus delegation."""

    def __init__(self, agent_id="test-minimal", database_url="sqlite+aiosqlite:///:memory:"):
        super().__init__(
            agent_id=agent_id,
            agent_type="test",
            database_url=database_url,
            vault_path="/tmp/test-minimal-vault",
        )
        self.executed_tasks: list[Task] = []

    async def execute_task(self, task: Task) -> TaskResult:
        self.executed_tasks.append(task)
        return TaskResult(
            subtask_id=task.subtask_id,
            agent_id=self.agent_id,
            action=task.action,
            status="success",
            result={"phase": task.data.get("phase", "test"), "ok": True},
            error=None,
            duration_seconds=0.05,
            completed_at=datetime.now(timezone.utc),
        )

    def get_capabilities(self) -> list[str]:
        return ["analyze"]


class TestEventBusDelegation:
    """Verify _listen_for_tasks() picks up task.request Messages and executes them."""

    async def test_listen_for_tasks_picks_up_message(self):
        """Agent polls EventBus, finds task.request, executes it."""
        from meai.events.event_bus import EventBus

        eb = EventBus("sqlite+aiosqlite:///:memory:")
        await eb.initialize()

        agent = _MinimalTaskAgent()
        agent.event_bus = eb
        await agent.initialize()

        # Publish task.request Message
        await eb.publish(Message(
            from_agent="test-orchestrator",
            to_agent=agent.agent_id,
            message_type="task.request",
            priority=1,
            payload={
                "correlation_id": "test-correlation-42",
                "task": {
                    "task_id": "task-1",
                    "subtask_id": "phase-1",
                    "parent_task_id": "task-1",
                    "action": "analyze",
                    "description": "Test phase",
                    "priority": 1,
                    "payload": {"niche": "test", "geo": "test"},
                    "data": {"phase": 1},
                },
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        ))

        # Wait for agent to pick up message and execute
        await asyncio.sleep(1.0)

        # Verify agent executed the task
        assert len(agent.executed_tasks) == 1, f"Expected 1 executed task, got {len(agent.executed_tasks)}"
        executed = agent.executed_tasks[0]
        assert executed.action == "analyze"
        assert executed.subtask_id == "phase-1"
        assert executed.payload == {"niche": "test", "geo": "test"}

        await agent.shutdown()
        await eb.close()

    async def test_listen_for_tasks_ignores_non_task_requests(self):
        """Agent skips Messages that are not task.request."""
        from meai.events.event_bus import EventBus

        eb = EventBus("sqlite+aiosqlite:///:memory:")
        await eb.initialize()

        agent = _MinimalTaskAgent()
        agent.event_bus = eb
        await agent.initialize()

        # Publish non-task.request messages
        await eb.publish(Message(
            from_agent="other",
            to_agent=agent.agent_id,
            message_type="agent.result",
            priority=1,
            payload={"some": "data"},
            timestamp=datetime.now(timezone.utc).isoformat(),
        ))

        await asyncio.sleep(0.8)

        # Agent should NOT execute anything
        assert len(agent.executed_tasks) == 0, (
            f"Agent executed {len(agent.executed_tasks)} tasks from non-task.request messages"
        )

        await agent.shutdown()
        await eb.close()

    async def test_orchestrator_full_delegation_flow(self):
        """CIOrchestrator._execute_single_phase → task.request → agent → ci.agent.completed."""
        from meai.events.event_bus import EventBus, Event
        from src.aim.subagents.competitive_intel.orchestrator.ci_orchestrator import CIOrchestrator

        eb = EventBus("sqlite+aiosqlite:///:memory:")
        await eb.initialize()

        o = CIOrchestrator(agent_id="test-flow", event_bus=eb)
        o._agent_instances["ci-scout"] = None  # force creation of our minimal agent

        # Replace _get_agent to return minimal test agent with _bridged_report
        async def _get_test_agent(agent_name):
            agent = _MinimalTaskAgent(agent_id=f"test-flow-{agent_name}")
            agent.event_bus = eb
            agent._ci_correlation_id: str | None = None

            _original_report = agent.report_result

            async def _bridged_report(result):
                await _original_report(result)
                corr_id = getattr(agent, '_ci_correlation_id', 'unknown')
                await eb.publish(Event(
                    event_type="ci.agent.completed",
                    payload={
                        "correlation_id": corr_id,
                        "agent": agent_name,
                        "phase": None,
                        "status": result.status if hasattr(result, 'status') else 'completed',
                        "result": result.result if hasattr(result, 'result') else {},
                    }
                ))

            agent.report_result = _bridged_report
            await agent.initialize()
            o._agent_instances[agent_name] = agent
            return agent

        o._get_agent = _get_test_agent

        task_data = {
            "task_id": "ci-flow-001",
            "niche": "стоматология",
            "geo": "Москва",
            "competitors": ["https://example.com"],
            "correlation_id": "ci-flow-001",
        }

        result = await o._execute_single_phase(
            phase_num=1,
            agent_name="ci-scout",
            task_data=task_data,
        )

        assert result["phase"] == 1
        assert result["agent"] == "ci-scout"
        assert result["status"] == "success"
        assert result["result"]["ok"] is True

        await eb.close()

    async def test_eventbus_delegation_timeout_when_no_agent(self):
        """_execute_single_phase returns stub when agent is None."""
        from meai.events.event_bus import EventBus
        from src.aim.subagents.competitive_intel.orchestrator.ci_orchestrator import CIOrchestrator

        eb = EventBus("sqlite+aiosqlite:///:memory:")
        await eb.initialize()

        o = CIOrchestrator(agent_id="test-to", event_bus=eb)

        result = await o._execute_single_phase(
            phase_num=99,
            agent_name="ci-nonexistent",
            task_data={"task_id": "x", "niche": "x", "geo": "x"},
        )

        assert result["status"] == "stub"
        await eb.close()
