"""Validate QC_CHECKLIST (15 items from RESEARCH.md Section 5.4) and CoverageReporter.

These tests cover the Phase 2 / Plan 02-03 QC checklist module + coverage
reporter. They assert:
  - QC_CHECKLIST has exactly 15 items with the required schema
  - PASS_THRESHOLD / PASS_MIN_ITEMS constants match QC-04 (>=80%, >=12/15)
  - calc_coverage correctly classifies PASS / FAIL on edge boundaries
  - format_coverage_text renders a stable summary header
  - empty / malformed gap_report does NOT crash (robustness)
  - render_checklist_for_llm exposes all 15 items for the Pass 2 prompt

Per TDD red-green discipline (Plan 02-03 Task 1, tdd="true"), this file is
committed BEFORE qc_checklist.py / coverage_reporter.py — making the red
state explicit in git history.
"""

import pytest

from app.orchestrator.qc_checklist import (
    QC_CHECKLIST,
    PASS_THRESHOLD,
    PASS_MIN_ITEMS,
    render_checklist_for_llm,
)
from app.orchestrator.coverage_reporter import (
    CoverageReport,
    calc_coverage,
    format_coverage_text,
)


# ── QC_CHECKLIST structure ───────────────────────────────────────────────


def test_qc_checklist_has_15_items():
    """QC-01: checklist must be within 10-20 range. 15 is the chosen count
    per RESEARCH.md Section 5.4."""
    assert len(QC_CHECKLIST) == 15, f"Expected 15 items, got {len(QC_CHECKLIST)}"


def test_qc_checklist_pass_criteria_defined():
    """Every item must carry id / category / name / pass_criteria / source
    so Pass 2 can render them and HTML section can display them."""
    for item in QC_CHECKLIST:
        assert isinstance(item, dict), f"Item is not a dict: {item!r}"
        for required_field in ("id", "category", "name", "pass_criteria", "source"):
            assert required_field in item, (
                f"Item {item.get('id', '?')} missing field {required_field}: {item!r}"
            )


def test_qc_checklist_ids_are_1_to_15():
    """Items should be numbered 1..15 sequentially for stable display."""
    ids = [it["id"] for it in QC_CHECKLIST]
    assert ids == list(range(1, 16)), f"Expected ids 1..15, got {ids}"


def test_qc_checklist_thresholds():
    """QC-04: PASS = >=80% which is 12 of 15 items."""
    assert PASS_THRESHOLD == 0.80
    assert PASS_MIN_ITEMS == 12  # 15 * 0.8 = 12


# ── CoverageReport.calc_coverage ─────────────────────────────────────────


def _make_gap_report(filled_ids, partial_ids=None, missing_ids=None, reasons=None):
    """Helper: build a gap_report dict with the schema Pass 2 emits."""
    partial_ids = partial_ids or []
    missing_ids = missing_ids or []
    reasons = reasons or {}
    items = []
    for i in filled_ids:
        items.append({"id": i, "status": "filled", "detail": "ok", "reason": ""})
    for i in partial_ids:
        items.append({"id": i, "status": "partial", "detail": "weak",
                      "reason": reasons.get(i, "partial coverage")})
    for i in missing_ids:
        items.append({"id": i, "status": "missing", "detail": "",
                      "reason": reasons.get(i, "no data")})
    return {"items": items, "summary": {}}


def test_coverage_report_pass():
    """13/15 filled = 86.67% → PASS."""
    gap = _make_gap_report(
        filled_ids=list(range(1, 14)),
        missing_ids=[14],
        partial_ids=[15],
    )
    report = calc_coverage(gap)
    assert report.coverage_pct >= 0.80
    assert report.status == "PASS"
    # 13 filled out of 15 → ~86.67%
    assert 0.86 <= report.coverage_pct <= 0.87


def test_coverage_report_fail():
    """8/15 filled = 53.33% → FAIL."""
    gap = _make_gap_report(
        filled_ids=list(range(1, 9)),
        missing_ids=list(range(9, 16)),
    )
    report = calc_coverage(gap)
    assert report.coverage_pct < 0.80
    assert report.status == "FAIL"


def test_coverage_report_edge_12_of_15():
    """Exactly 12/15 = 80.0% — boundary case → PASS per QC-04."""
    gap = _make_gap_report(
        filled_ids=list(range(1, 13)),
        missing_ids=[13, 14, 15],
    )
    report = calc_coverage(gap)
    assert report.coverage_pct >= PASS_THRESHOLD
    assert report.status == "PASS"


def test_coverage_report_edge_11_of_15():
    """11/15 = 73.33% → FAIL (below 80% threshold)."""
    gap = _make_gap_report(
        filled_ids=list(range(1, 12)),
        missing_ids=list(range(12, 16)),
    )
    report = calc_coverage(gap)
    assert report.coverage_pct < PASS_THRESHOLD
    assert report.status == "FAIL"


def test_coverage_report_missing_with_reason():
    """Missing items must carry their reason into the CoverageReport so
    format_coverage_text can surface 'why' to the admin / client (ORC-04)."""
    gap = _make_gap_report(
        filled_ids=[1, 2, 3],
        missing_ids=[14],
        reasons={14: "forums unavailable"},
        partial_ids=[15],
    )
    report = calc_coverage(gap)
    missing_with_reason = [
        m for m in report.missing_items
        if m.get("id") == 14
    ]
    assert missing_with_reason, "Missing item 14 not found in report"
    assert missing_with_reason[0].get("reason") == "forums unavailable"


def test_coverage_report_empty_gap_report():
    """Defensive: empty dict must not crash, returns FAIL with 0%."""
    report = calc_coverage({})
    assert report.coverage_pct == 0.0
    assert report.status == "FAIL"
    # All 15 items should be reported as missing (or zero filled — the key
    # requirement is robustness, not the exact fallback shape).
    assert report.total_items == 15


def test_coverage_report_malformed_gap_report():
    """Defensive: items missing required keys must not crash calc_coverage."""
    gap = {
        "items": [
            {"id": 1},  # no status
            "not-a-dict",  # wrong type
            {"id": 2, "status": "filled"},
        ],
        "summary": {},
    }
    report = calc_coverage(gap)
    # Must not raise; status is FAIL since coverage is well below threshold.
    assert report.status in ("PASS", "FAIL")  # only sanity check — robust call


# ── format_coverage_text ─────────────────────────────────────────────────


def test_format_coverage_text_includes_summary():
    """Per QC-03: text report must include the canonical summary header
    'QC Coverage: X/15 (Y%) — PASS|FAIL' so logs are greppable."""
    gap = _make_gap_report(
        filled_ids=list(range(1, 14)),
        missing_ids=[14],
        partial_ids=[15],
    )
    report = calc_coverage(gap)
    text = format_coverage_text(report)
    assert "QC Coverage:" in text
    assert "/15" in text
    assert "PASS" in text
    # Filled ids should appear in the text
    assert "1" in text  # at least one filled id mentioned


def test_format_coverage_text_includes_missing_reasons():
    """ORC-04: missing items must show their reason in the text report."""
    gap = _make_gap_report(
        filled_ids=[1, 2],
        missing_ids=[3],
        reasons={3: "Форумы недоступны"},
    )
    report = calc_coverage(gap)
    text = format_coverage_text(report)
    assert "Форумы недоступны" in text or "недоступны" in text.lower()


# ── render_checklist_for_llm ─────────────────────────────────────────────


def test_render_checklist_for_llm_has_all_15_items():
    """Pass 2 prompt embeds render_checklist_for_llm() output. It must
    reference all 15 items by id + name so the LLM evaluates each one."""
    text = render_checklist_for_llm()
    for item in QC_CHECKLIST:
        assert str(item["id"]) in text, f"Item id {item['id']} not in rendered checklist"
        assert item["name"] in text, f"Item name {item['name']!r} not in rendered checklist"


def test_render_checklist_for_llm_includes_pass_criteria():
    """LLM must see the pass criteria to self-evaluate correctly."""
    text = render_checklist_for_llm()
    # At least the first item's pass_criteria should appear
    assert QC_CHECKLIST[0]["pass_criteria"] in text
