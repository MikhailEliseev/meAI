"""Unit tests for _apply_niche_conditional_coverage (Phase 3 / D-05 + D-08).

Tests the runtime hard-FAIL override + conditional-total logic that
``three_pass.py`` applies to CoverageReport instances after the Pass 2
calc_coverage and after the final (post-Pass 3) calc_coverage.

Three branches are covered:
  1. Critical niche (plastic_surgery, cosmetology) + item 5 missing →
     HARD FAIL override: status forced to FAIL, item 5 synthesized into
     missing_items if absent, warning logged.
  2. Critical niche + item 5 filled → no override, PASS preserved.
  3. Non-critical niche → conditional total (14 vs 15): item 5 dropped
     from total, not_applicable_items populated, missing_items filtered
     to exclude id==5, coverage_pct recomputed.
  4. Unknown niche → input report returned unchanged (safe fallback).

Plus an asdict contract test verifying that Plan 03-05 (HTML renderer)
can consume not_applicable_items via metadata.get("not_applicable_items", []).

Uses standard library ``unittest`` (no pytest dependency) to match the
convention of existing Hermes test files
(``test_deep_research_merge.py``, ``test_service_categorizer.py``).
"""

import dataclasses
import logging
import unittest

from app.orchestrator.coverage_reporter import CoverageReport
from app.orchestrator.three_pass import _apply_niche_conditional_coverage


class TestApplyNicheConditionalCoverage(unittest.TestCase):
    """Tests for the ``_apply_niche_conditional_coverage`` helper."""

    def setUp(self):
        """Build a base CoverageReport that callers can tweak per test.

        The default report has 14 of 15 items filled (item 5 absent)
        and PASS status — this mirrors the "LLM honestly missed item 5"
        case where the override should fire for critical niches.
        """
        self.base_report = CoverageReport(
            total_items=15,
            filled_items=[1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
            missing_items=[],
            partial_items=[],
            not_applicable_items=[],
            coverage_pct=14 / 15,
            status="PASS",
        )

    # ── Critical niche branch ────────────────────────────────────────────

    def test_critical_niche_with_item5_missing_forces_fail(self):
        """D-05 runtime gate: critical niche + item 5 missing → FAIL.

        The LLM marked 14 of 15 items as filled (item 5 absent), so
        coverage_pct = 14/15 = 0.933 ≥ 0.80 threshold → original
        status is PASS. The override must force FAIL because the
        niche is Instagram-critical and item 5 (Instagram) is missing.
        """
        report = dataclasses.replace(self.base_report)
        with self.assertLogs(
            "app.orchestrator.three_pass", level="WARNING",
        ) as log_ctx:
            result = _apply_niche_conditional_coverage(report, "plastic_surgery")

        self.assertEqual(result.status, "FAIL",
                         "critical niche + item 5 missing must force FAIL")
        # Item 5 must appear in missing_items (synthesized if absent).
        missing_ids = [m.get("id") for m in result.missing_items]
        self.assertIn(5, missing_ids,
                      "item 5 must appear in missing_items after override")
        # Warning log must mention HARD FAIL / forcing coverage=FAIL.
        combined_log = "\n".join(log_ctx.output)
        self.assertTrue(
            "HARD FAIL" in combined_log or "forcing coverage=FAIL" in combined_log,
            f"expected HARD FAIL warning in log; got: {combined_log!r}",
        )
        # Identity preserved (same instance returned).
        self.assertIs(result, report,
                      "helper must return the same CoverageReport instance")

    def test_critical_niche_with_item5_filled_no_override(self):
        """D-05 runtime gate: critical niche + item 5 filled → PASS preserved.

        When item 5 IS in filled_items and NOT in missing_items, the
        niche is Instagram-critical but Instagram was actually called.
        The override must NOT fire — original PASS status preserved.
        """
        report = CoverageReport(
            total_items=15,
            filled_items=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
            missing_items=[],
            partial_items=[],
            not_applicable_items=[],
            coverage_pct=15 / 15,
            status="PASS",
        )
        # Use cosmetology (the other critical niche) for coverage.
        result = _apply_niche_conditional_coverage(report, "cosmetology")

        self.assertEqual(result.status, "PASS",
                         "critical niche + item 5 filled must NOT override")
        self.assertIn(5, result.filled_items,
                      "item 5 must remain in filled_items when filled")
        # No missing_items synthesis (override did not fire).
        self.assertEqual(result.missing_items, [],
                         "missing_items must stay empty when item 5 filled")

    # ── Non-critical niche branch ────────────────────────────────────────

    def test_non_critical_niche_drops_item5_and_populates_not_applicable(self):
        """D-08 runtime gate: non-critical niche → item 5 becomes not_applicable.

        For dental (non-critical): total drops to 14, item 5 is moved
        into not_applicable_items with a clear reason, missing_items
        filter excludes id==5, coverage_pct recomputes against new total.
        """
        # Build a report where item 5 is in missing_items (LLM honestly
        # reported it as missing because Instagram wasn't called — but
        # for a non-critical niche this is now not_applicable, not missing).
        report = CoverageReport(
            total_items=15,
            filled_items=[1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
            missing_items=[{
                "id": 5,
                "name": "Instagram analysis for cosmetology/plastic",
                "reason": "не critical",
                "detail": "",
            }],
            partial_items=[],
            not_applicable_items=[],
            coverage_pct=14 / 15,
            status="PASS",
        )

        result = _apply_niche_conditional_coverage(report, "dental")

        # Total drops from 15 to 14.
        self.assertEqual(result.total_items, 14,
                         "non-critical niche: total_items must be 14")
        # Item 5 appears in not_applicable_items.
        self.assertEqual(len(result.not_applicable_items), 1,
                         "not_applicable_items must contain exactly 1 entry")
        na_entry = result.not_applicable_items[0]
        self.assertEqual(na_entry["id"], 5)
        self.assertIn("dental", na_entry["reason"],
                      "not_applicable reason must mention the niche")
        # missing_items no longer contains id==5.
        missing_ids = [m.get("id") for m in result.missing_items]
        self.assertNotIn(5, missing_ids,
                         "missing_items must NOT contain id==5 for non-critical")
        # Coverage recomputed against new total. 14 filled / 14 total = 100%.
        self.assertAlmostEqual(result.coverage_pct, 1.0, places=3,
                               msg="14/14 must equal 1.0 coverage")
        self.assertEqual(result.status, "PASS",
                         "14/14 = 100% must PASS the 0.80 threshold")

    # ── Unknown niche branch ─────────────────────────────────────────────

    def test_unknown_niche_returns_report_unchanged(self):
        """Safe fallback: unknown niche → report unchanged.

        When the mini-call failed and state.niche == "unknown", the
        helper returns the input report unchanged. This is the safe
        fallback to avoid false-hard-FAIL on mini-call failure.
        """
        report = dataclasses.replace(self.base_report)
        original_status = report.status
        original_pct = report.coverage_pct
        original_missing = list(report.missing_items)
        original_filled = list(report.filled_items)
        original_na = list(report.not_applicable_items)
        original_total = report.total_items

        result = _apply_niche_conditional_coverage(report, "unknown")

        # Identity check — helper returns the SAME instance.
        self.assertIs(result, report,
                      "unknown niche: helper must return input instance")
        # All fields must match the input.
        self.assertEqual(result.status, original_status)
        self.assertEqual(result.coverage_pct, original_pct)
        self.assertEqual(result.missing_items, original_missing)
        self.assertEqual(result.filled_items, original_filled)
        self.assertEqual(result.not_applicable_items, original_na)
        self.assertEqual(result.total_items, original_total)

    # ── asdict contract for Plan 03-05 HTML renderer ─────────────────────

    def test_coverage_report_asdict_includes_not_applicable_items(self):
        """Plan 03-05 consumer contract: asdict(report) has not_applicable_items key.

        The HTML QC section in Plan 03-05 reads not_applicable_items via
        ``metadata.get("not_applicable_items", [])``. This test verifies
        the dataclass field flows through ``dataclasses.asdict()``.
        """
        report = CoverageReport(
            total_items=14,
            filled_items=[1, 2, 3],
            missing_items=[],
            partial_items=[],
            not_applicable_items=[{
                "id": 5,
                "name": "Instagram analysis for cosmetology/plastic",
                "reason": "not_applicable for non-critical niche (dental)",
            }],
            coverage_pct=3 / 14,
            status="FAIL",
        )
        d = dataclasses.asdict(report)
        self.assertIn("not_applicable_items", d,
                      "asdict() must include not_applicable_items key")
        self.assertEqual(len(d["not_applicable_items"]), 1)
        self.assertEqual(d["not_applicable_items"][0]["id"], 5)

    def test_coverage_report_default_not_applicable_items_is_empty_list(self):
        """Backward-compat: default CoverageReport has empty not_applicable_items.

        Phase 2 callers that don't know about the new field must not
        break — the default is an empty list, and asdict() includes
        the key with value ``[]``.
        """
        report = CoverageReport()
        self.assertEqual(report.not_applicable_items, [],
                         "default not_applicable_items must be empty list")
        d = dataclasses.asdict(report)
        self.assertEqual(d["not_applicable_items"], [])


if __name__ == "__main__":
    unittest.main()
