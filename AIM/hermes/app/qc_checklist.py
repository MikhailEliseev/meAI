"""QC_CHECKLIST — 15-item presale coverage checklist (Phase 2 / Plan 02-03).

Per RESEARCH.md Section 5.4 — 15-item QC checklist for presale coverage.
Each item has an objective pass criterion sourced from Plan 01 evidence
(missing sections) + Plan 02 evidence (skip/truncate points) + Plan 04
evidence (Instagram verification). PASS = >=12/15 (80%) per QC-04.

This module is consumed by:
  - pass_gap_analyze.py (Pass 2 prompt — LLM evaluates each item)
  - coverage_reporter.py (PASS/FAIL math + text rendering)
  - generate_html_report.py (HTML QC Coverage section in Task 3)

The checklist is a module-level constant (list of dicts) so it can be
iterated, filtered, and versioned. If future phases need to add or split
items, bump VERSION and document the change in the PLAN/SUMMARY.

Phase 3 / Plan 03-03 additions (VERSION 1.1.0):
  - Item 5 (Instagram) carries `conditional_on_niche: True` flag (D-08).
  - CRITICAL_NICHES constant lists the niches where item 5 applies.
  - Three helper functions exported for downstream plans (03-04, 03-05, 03-06):
      * is_item_applicable(item_id, niche) -> bool
      * applicable_items(niche) -> list[dict]
      * is_niche_instagram_critical(niche) -> bool
  Runtime conditional-total logic lives in Plan 03-06 (this plan ships
  the data-model scaffolding only).
"""

import logging

logger = logging.getLogger(__name__)

# ── Versioning ───────────────────────────────────────────────────────────
# Bump when checklist items are added, removed, or their pass criteria
# change. Pass 2 prompt and HTML rendering read this for traceability.
# 1.1.0 (Phase 3 / Plan 03-03): item 5 conditional_on_niche flag + 3 helpers.
# 1.2.0 (Phase 4 / Plan 04-04): items 16-18 added (clinic_metrics, ratings,
#   expert_regalia). Item 8 refined (concrete URLs from 5 target СМИ).
#   Item 11 refined (3-year trend with YoY %). PASS_MIN_ITEMS updated.
VERSION = "1.2.0"

# ── Thresholds (QC-04) ───────────────────────────────────────────────────
# PASS_THRESHOLD = 0.80 → 80% coverage required (QC-04).
# PASS_MIN_ITEMS = 15   → derived: 18 * 0.8 = 14.4 → round up to 15.
PASS_THRESHOLD: float = 0.80
PASS_MIN_ITEMS: int = 15

# ── Niche-conditional logic (Phase 3 / D-08) ─────────────────────────────
# Niches where Instagram analysis is critical. Item 5 (Instagram) only
# applies to clinics in these niches. For all other niches the item is
# marked not_applicable and excluded from the effective total (Plan 03-06).
# Per D-03: a clinic is Instagram-critical only if cosmetology / plastic
# surgery is the MAIN profile (>50% of services). The niche_detector
# mini-call (Plan 03-02) makes that determination; this tuple is the
# canonical list of critical values the rest of the code consumes.
CRITICAL_NICHES: tuple[str, ...] = ("plastic_surgery", "cosmetology")

# ── The 15-item checklist ────────────────────────────────────────────────
# Order matches RESEARCH.md Section 5.4 table (items 1..15). DO NOT reorder
# — the HTML section and Pass 2 prompt depend on stable numbering.
QC_CHECKLIST: list[dict] = [
    {
        "id": 1,
        "category": "about",
        "name": "About data collected (ОКВЭД, licenses, revenue)",
        "pass_criteria": (
            "ОКВЭД, licenses, revenue — at least 2 of 3 fields populated "
            "with real data from nalog.ru / prescan"
        ),
        "source": "Plan 01 — About missing 100%",
    },
    {
        "id": 2,
        "category": "market",
        "name": "Market section data (competitor table with >=3 competitors)",
        "pass_criteria": (
            ">=3 competitors with revenue + trend populated"
        ),
        "source": "Plan 01 — Market missing 100%",
    },
    {
        "id": 3,
        "category": "competitors",
        "name": "Competitors returned by find_competitors",
        "pass_criteria": (
            ">=3 competitors; if initial call returned 0, retried with broader geo"
        ),
        "source": "Plan 02 — competitors: [] for iphk.ru",
    },
    {
        "id": 4,
        "category": "experts",
        "name": "Experts identified (top-5 doctor ФИО)",
        "pass_criteria": (
            ">=3 doctors identified with full ФИО (not clinic name)"
        ),
        "source": "Plan 02 — врачи не найдены",
    },
    {
        "id": 5,
        "category": "instagram",
        "name": "Instagram analysis for cosmetology/plastic",
        "pass_criteria": (
            "If clinic niche matches cosmetology/plastic, run_instagram_content "
            "called (even if it honestly returns 'no data')"
        ),
        "source": "Plan 04 — Instagram never runs",
        "conditional_on_niche": True,
    },
    {
        "id": 6,
        "category": "content",
        "name": "Content themes with %",
        "pass_criteria": ">=3 themes with percentages per top doctor",
        "source": "Plan 01 — Content Analysis 80% missing",
    },
    {
        "id": 7,
        "category": "content",
        "name": "Content gaps with severity",
        "pass_criteria": ">=2 gaps with severity levels (low/medium/high)",
        "source": "Plan 04 v2 schema",
    },
    {
        "id": 8,
        "category": "media",
        "name": "SMI mentions with concrete URLs",
        "pass_criteria": (
            ">=3 mentions with concrete URLs from target СМИ "
            "(Forbes, RBC, Vademecum, Kommersant, ТАСС) — via run_media_urls tool"
        ),
        "source": "Plan 01 — Media shallow + Phase 4 / DAT-02",
    },
    {
        "id": 9,
        "category": "forum",
        "name": "Forum pains (patient fears)",
        "pass_criteria": ">=5 patient fears collected from forums",
        "source": "Plan 01 — section 04 partial",
    },
    {
        "id": 10,
        "category": "financials",
        "name": "Revenue for current year",
        "pass_criteria": "Revenue number present (from ГИР БО or nalog.ru)",
        "source": "Plan 01 — About missing",
    },
    {
        "id": 11,
        "category": "financials",
        "name": "Revenue dynamics 3 years with YoY %",
        "pass_criteria": (
            "3-year revenue trend with YoY % AND total growth % — "
            "from find_company_financials revenue_dynamics block. "
            "If <3 years available: item must be marked 'missing' with "
            "reason 'недостаточно данных для динамики' (D-13 strict rule)"
        ),
        "source": "Plan 01 — only current year + Phase 4 / DAT-01 / D-13",
    },
    {
        "id": 12,
        "category": "competitors",
        "name": "Competitor cards detailed (year founded, surgeons, Instagram)",
        "pass_criteria": (
            ">=3 competitor cards with >=4 fields each "
            "(year founded, surgeons, Instagram, revenue, etc.)"
        ),
        "source": "Plan 01 — Competitors 80% missing",
    },
    {
        "id": 13,
        "category": "strategy",
        "name": "Whitefields comparison matrix",
        "pass_criteria": (
            "Matrix: client vs >=3 competitors by >=5 fields "
            "(not just content_gaps list)"
        ),
        "source": "Plan 01 — Whitefields 80% missing",
    },
    {
        "id": 14,
        "category": "strategy",
        "name": "Strategy with 5 directions",
        "pass_criteria": (
            "5 concrete directions: content, Telegram, GEO, reputation, cross-promo"
        ),
        "source": "Plan 01 — Strategy weak",
    },
    {
        "id": 15,
        "category": "offer",
        "name": "Offer section (\"Что AIM может\")",
        "pass_criteria": (
            "Concrete steps + CTA matching reference section 10"
        ),
        "source": "Plan 01 — Offer 80% missing",
    },
    {
        "id": 16,
        "category": "financials",
        "name": "Clinic metrics (DAT-04)",
        "pass_criteria": (
            "Clinic metrics block present: revenue, profit, employees (if available), "
            "licenses (from prescan), ОКВЭД codes (LLM translates to human language in Pass 3) — "
            "from find_company_financials clinic_metrics block"
        ),
        "source": "Phase 4 / DAT-04 / D-21",
    },
    {
        "id": 17,
        "category": "reputation",
        "name": "Ratings on 2 platforms (DAT-05)",
        "pass_criteria": (
            "Ratings present for at least 2 platforms: "
            "ПроДокторов + Яндекс.Карты — via run_review_platforms. "
            "Each platform: rating + review count"
        ),
        "source": "Phase 4 / DAT-05 / D-22-23",
    },
    {
        "id": 18,
        "category": "experts",
        "name": "Expert регалии from site scrape (SEC-04)",
        "pass_criteria": (
            ">=3 doctors with structured_regalia: degree (КМН/ДМН), "
            "academic_title (профессор/доцент), experience_years, education — "
            "from find_doctor_handles structured_regalia field"
        ),
        "source": "Phase 4 / SEC-04 / D-08",
    },
]


def render_checklist_for_llm() -> str:
    """Render the checklist as plain text suitable for the Pass 2 prompt.

    Each line: ``{id}. {name} — pass: {pass_criteria}``
    The LLM uses this to self-evaluate collected data per item.
    """
    lines = []
    for item in QC_CHECKLIST:
        lines.append(
            f"{item['id']}. {item['name']} — pass: {item['pass_criteria']}"
        )
    rendered = "\n".join(lines)
    logger.debug("Rendered QC checklist for LLM (%d items)", len(QC_CHECKLIST))
    return rendered


def get_item_by_id(item_id: int) -> dict | None:
    """Look up a single checklist item by id (helper for HTML rendering)."""
    for item in QC_CHECKLIST:
        if item["id"] == item_id:
            return item
    return None


# ── Phase 3 / Plan 03-03 helpers ─────────────────────────────────────────
# These three helpers encode the D-08 conditional-checklist rule at the
# data-model level. Runtime enforcement (actual coverage-total recomputation)
# lives in Plan 03-06; this module only exposes the pure predicates that
# every consumer (Pass 2 prompt, HTML renderer, 03-06 coverage override)
# can rely on.


def is_niche_instagram_critical(niche: str) -> bool:
    """Return True iff ``niche`` is in :data:`CRITICAL_NICHES`.

    Used by:
      - pass_gap_analyze.run_pass_gap_analyze (this plan, Task 3) to decide
        which niche_instruction string to inject into the Pass 2 prompt.
      - Plan 03-06 runtime hard-FAIL override to decide whether missing
        item 5 forces coverage=FAIL regardless of other items filled.

    Args:
        niche: The verdict string produced by niche_detector (Plan 03-02).
            One of "plastic_surgery", "cosmetology", "dental",
            "general_medicine", "other", "unknown", or "" (not yet set).

    Returns:
        True iff niche is "plastic_surgery" or "cosmetology". Returns
        False for "unknown" and "" — when the mini-call failed or hasn't
        run, we do NOT treat the run as Instagram-critical at the helper
        level (the prompt layer has its own cautious wording for the
        "unknown" case).
    """
    return niche in CRITICAL_NICHES


def is_item_applicable(item_id: int, niche: str) -> bool:
    """Return True iff checklist item ``item_id`` applies to ``niche``.

    Per D-08:
      - Item 5 (Instagram) is applicable ONLY when niche is critical
        OR when niche is "unknown" (mini-call failed — safer to
        over-require than under-require; Pass 2 will decide based on
        evidence it actually sees).
      - All 14 other items are universally applicable regardless of niche.

    Used by:
      - :func:`applicable_items` (this module) to filter the checklist.
      - Plan 03-06 `_apply_niche_conditional_coverage` to compute the
        effective total per run (15 for critical niches, 14 for
        non-critical niches).

    Args:
        item_id: Checklist item id (1..15).
        niche: Niche verdict string (see :func:`is_niche_instagram_critical`).

    Returns:
        True if the item should be counted toward coverage for this run.
    """
    if niche == "unknown":
        # Mini-call failed — keep item 5 in scope. Pass 2 will assess
        # actual evidence; if Instagram data is genuinely missing AND
        # the clinic turns out to be critical, the LLM has been told to
        # flag the item as missing. (Per Plan 03-02 fallback rationale:
        # safer to over-require than to silently drop the item.)
        return True
    if item_id == 5 and not is_niche_instagram_critical(niche):
        # Non-critical niche → Instagram item does not apply.
        return False
    return True


def applicable_items(niche: str) -> list[dict]:
    """Return the subset of :data:`QC_CHECKLIST` that applies to ``niche``.

    Convenience filter used by Plan 03-06 to recompute the effective
    checklist total for a given run.

    Args:
        niche: Niche verdict string (see :func:`is_niche_instagram_critical`).

    Returns:
        List of checklist item dicts (each unchanged from QC_CHECKLIST).
        For non-critical niches this is 14 items (item 5 filtered out).
        For critical or "unknown" niches this is all 15 items.
    """
    return [
        item for item in QC_CHECKLIST
        if is_item_applicable(item["id"], niche)
    ]
