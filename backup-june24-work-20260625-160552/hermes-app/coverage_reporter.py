"""CoverageReporter — compute presale coverage % from Pass 2 gap_report.

Per Phase 2 Plan 02-03 / QC-03 + QC-04:
  - calc_coverage(gap_report) → CoverageReport dataclass
  - format_coverage_text(report) → multiline text for logs / interpretations
  - PASS = >=12/15 (80%) filled items per QC-04

This module is robust to:
  - empty gap_report ({}) → CoverageReport with coverage_pct=0.0, status=FAIL
  - malformed gap_report (missing keys, wrong types) → no crash, default values

It does NOT make LLM calls — it works on the already-parsed gap_report that
Pass 2 produced. The LLM is responsible for honestly evaluating each item
(ORC-04 honest-data principle).

Phase 3 / D-08 — added not_applicable_items field:
  CoverageReport gained a new ``not_applicable_items`` list field. This
  field is populated by the ``_apply_niche_conditional_coverage`` helper
  in three_pass.py (Plan 03-06) for non-critical niches where item 5
  (Instagram) does not apply. The calc_coverage function itself is NOT
  niche-aware — it does not filter items by applicability. Niche
  conditional logic lives entirely in the helper. This preserves the
  Phase 2 contract (calc_coverage is deterministic given gap_report)
  while letting Phase 3 layer the niche-conditional override on top.
  Plan 03-05 HTML renders this field distinctly from missing_items.
"""

import logging
from dataclasses import dataclass, field

from app.orchestrator.qc_checklist import (
    QC_CHECKLIST,
    PASS_THRESHOLD,
    PASS_MIN_ITEMS,
    get_item_by_id,
)

logger = logging.getLogger(__name__)


@dataclass
class CoverageReport:
    """Result of calc_coverage(gap_report).

    Attributes:
        total_items: Always 18 (len of QC_CHECKLIST after Phase 4 expansion).
            Stored for HTML rendering where the QC_CHECKLIST import would be
            a heavier dependency.
        filled_items: List of item ids the LLM marked as 'filled'.
        missing_items: List of dicts ``{"id": N, "name": str, "reason": str}``
            for items the LLM could not fill. Used by HTML section + Pass 3
            prompt.
        partial_items: Same shape as missing_items — items where data exists
            but doesn't fully meet the pass criterion.
        not_applicable_items: List of dicts ``{"id": N, "name": str, "reason": str}``
            for items that do not apply to the current niche (e.g., item 5
            Instagram analysis for a non-critical niche like dental). Populated
            by the ``_apply_niche_conditional_coverage`` helper in three_pass.py.
            Used by HTML QC section (Plan 03-05) to render not-applicable items
            distinctly from missing items. Empty list by default — preserved
            for backward compatibility with Phase 2 callers.
        coverage_pct: Float 0.0..1.0 = filled / total.
        status: "PASS" if coverage_pct >= PASS_THRESHOLD else "FAIL".
    """

    total_items: int = 18
    filled_items: list[int] = field(default_factory=list)
    missing_items: list[dict] = field(default_factory=list)
    partial_items: list[dict] = field(default_factory=list)
    not_applicable_items: list[dict] = field(default_factory=list)
    coverage_pct: float = 0.0
    status: str = "FAIL"


def calc_coverage(gap_report: dict) -> CoverageReport:
    """Convert Pass 2 gap_report dict into a CoverageReport.

    Args:
        gap_report: Dict with structure ``{"items": [{"id": int, "status": str,
            "detail": str, "reason": str}], "summary": {...}}``. Robust to
            missing keys, non-dict items, and missing status fields.

    Returns:
        CoverageReport with filled / missing / partial buckets + PASS/FAIL.
    """
    total = len(QC_CHECKLIST)  # 18 after Phase 4 expansion
    filled: list[int] = []
    missing: list[dict] = []
    partial: list[dict] = []

    if isinstance(gap_report, dict):
        raw_items = gap_report.get("items", [])
    else:
        raw_items = []
        logger.warning(
            "calc_coverage: gap_report is not a dict (%s) — treating as empty",
            type(gap_report).__name__,
        )

    if not isinstance(raw_items, list):
        logger.warning(
            "calc_coverage: gap_report['items'] is not a list (%s) — treating as empty",
            type(raw_items).__name__,
        )
        raw_items = []

    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        try:
            item_id = int(raw.get("id", 0))
        except (TypeError, ValueError):
            continue
        if item_id < 1 or item_id > total:
            continue
        status = str(raw.get("status", "")).lower().strip()
        detail = raw.get("detail", "")
        reason = raw.get("reason", "") or raw.get("detail", "") or "причина не указана"
        meta = get_item_by_id(item_id) or {}
        name = meta.get("name", f"Item {item_id}")

        if status == "filled":
            filled.append(item_id)
        elif status == "partial":
            partial.append({"id": item_id, "name": name, "reason": reason,
                            "detail": detail})
        elif status == "missing":
            missing.append({"id": item_id, "name": name, "reason": reason,
                            "detail": detail})
        else:
            # Unknown status → treat as missing with the raw reason.
            missing.append({"id": item_id, "name": name,
                            "reason": f"unknown status: {status!r}",
                            "detail": detail})

    # Items NOT mentioned at all in the gap_report are also missing.
    mentioned = set(filled) | {m["id"] for m in missing} | {p["id"] for p in partial}
    for item in QC_CHECKLIST:
        if item["id"] not in mentioned:
            missing.append({
                "id": item["id"],
                "name": item["name"],
                "reason": "не оценён LLM (пункт отсутствует в gap_report)",
                "detail": "",
            })

    filled_count = len(filled)
    coverage_pct = filled_count / total if total else 0.0
    status = "PASS" if coverage_pct >= PASS_THRESHOLD else "FAIL"

    report = CoverageReport(
        total_items=total,
        filled_items=sorted(filled),
        missing_items=missing,
        partial_items=partial,
        coverage_pct=coverage_pct,
        status=status,
    )
    logger.debug(
        "Computed coverage: filled=%d/%d (%.1f%%) — %s",
        filled_count, total, coverage_pct * 100, status,
    )
    return report


def format_coverage_text(report: CoverageReport) -> str:
    """Render a CoverageReport as multi-line text for logs / interpretations.

    Format (stable header for grep):
        QC Coverage: {filled}/{total} ({pct}%) — {status}
        Filled: {ids}
        Partial: {ids} — {reasons}
        Missing (marked unavailable): {ids} — {reasons}
    """
    pct_str = f"{report.coverage_pct * 100:.1f}"
    filled_str = ", ".join(str(i) for i in report.filled_items) or "(none)"

    lines = [
        f"QC Coverage: {len(report.filled_items)}/{report.total_items} "
        f"({pct_str}%) — {report.status}",
        f"Filled: {filled_str}",
    ]

    if report.partial_items:
        partial_str = "; ".join(
            f"{p['id']} ({p['name']}): {p['reason']}" for p in report.partial_items
        )
        lines.append(f"Partial: {partial_str}")

    if report.missing_items:
        missing_str = "; ".join(
            f"{m['id']} ({m['name']}): {m['reason']}" for m in report.missing_items
        )
        lines.append(f"Missing (marked unavailable): {missing_str}")

    return "\n".join(lines)
