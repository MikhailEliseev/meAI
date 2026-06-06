#!/usr/bin/env python3
"""
Quality gate for presale data.json validation.

Usage:
    python3 /root/bin/quality-gate.py /root/work/presale/{client}/data.json
    python3 /root/bin/quality-gate.py /root/work/presale/{client}/data.json --strict

Checks completeness of clinic, doctors, competitors, geo, and deep_research sections.
Non-blocking warnings for deep_research (Phase 0 may be partially executed).
"""

import json
import sys
import os
from datetime import datetime


def validate_data(data_json, strict=False):
    """
    Validate presale data.json and return list of gaps.

    Args:
        data_json: Parsed data.json as dict
        strict: If True, all WARNING gaps become CRITICAL

    Returns:
        list of gap descriptions (strings)
    """
    gaps = []

    # ── Clinic checks ──
    clinic = data_json.get("clinic", {})

    if not clinic.get("inn"):
        gaps.append("MISSING: clinic.inn")

    if not clinic.get("revenue"):
        gaps.append("MISSING: clinic.revenue")

    tech_audit = clinic.get("tech_audit", {})
    if not tech_audit:
        gaps.append("MISSING: clinic.tech_audit (Phase 1 not executed)")

    # ── Doctor checks ──
    doctors = data_json.get("doctors", [])
    if not doctors:
        gaps.append("MISSING: doctors[] (empty)")
    else:
        for i, doc in enumerate(doctors):
            if not doc.get("ig_username") and not doc.get("social_profiles", {}).get("instagram"):
                gaps.append(f"WARNING: doctors[{i}].ig_username missing (no Instagram found)")

            confidence = doc.get("confidence", doc.get("research_confidence"))
            if confidence == "SINGLE_SOURCE" or confidence is None:
                gaps.append(f"WARNING: doctors[{i}] has low confidence ({confidence})")

    # ── Competitor checks ──
    competitors = data_json.get("competitors", [])
    if not competitors:
        gaps.append("WARNING: competitors[] (empty)")

    for i, comp in enumerate(competitors):
        if not comp.get("revenue"):
            gaps.append(f"WARNING: competitors[{i}].revenue missing")
        if not comp.get("score"):
            gaps.append(f"WARNING: competitors[{i}].score missing")

    # ── Geo checks ──
    geo = data_json.get("geo", {})
    if not geo.get("schema_ok"):
        gaps.append("MISSING: geo.schema_ok")
    if not geo.get("chatgpt_geo"):
        gaps.append("MISSING: geo.chatgpt_geo")
    if not geo.get("yandex_maps"):
        gaps.append("MISSING: geo.yandex_maps")
    if not geo.get("google_maps"):
        gaps.append("MISSING: geo.google_maps")

    # ── Deep Research checks (Phase 0) — NON-BLOCKING WARNING ──
    deep_research = data_json.get("deep_research", {})
    if not deep_research.get("clinic"):
        gaps.append("MISSING: deep_research.clinic (Phase 0 not executed)")
    if not deep_research.get("doctors"):
        gaps.append("MISSING: deep_research.doctors (Phase 0 not executed)")

    # ── Meta check ──
    meta = data_json.get("meta", {})
    if not meta.get("client"):
        gaps.append("MISSING: meta.client")
    if not meta.get("generated_at"):
        gaps.append("WARNING: meta.generated_at missing")

    return gaps


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 quality-gate.py <data.json path> [--strict]", file=sys.stderr)
        sys.exit(1)

    data_path = sys.argv[1]
    strict = "--strict" in sys.argv

    if not os.path.exists(data_path):
        print(f"ERROR: File not found: {data_path}", file=sys.stderr)
        sys.exit(2)

    try:
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"ERROR: Cannot read data.json: {e}", file=sys.stderr)
        sys.exit(2)

    gaps = validate_data(data, strict=strict)

    # ── Classify gaps ──
    critical = [g for g in gaps if g.startswith("MISSING:")]
    warnings = [g for g in gaps if g.startswith("WARNING:")]

    print(f"=== Quality Gate Report ===")
    print(f"File: {data_path}")
    print(f"Date: {datetime.now().isoformat()}")
    print(f"Mode: {'STRICT' if strict else 'NORMAL'}")
    print()

    print(f"CRITICAL gaps: {len(critical)}")
    for g in critical:
        print(f"  [CRITICAL] {g}")

    print(f"WARNING gaps: {len(warnings)}")
    for g in warnings:
        print(f"  [WARNING] {g}")

    print()

    if strict and critical:
        print(f"RESULT: FAILED — {len(critical)} critical gaps")
        sys.exit(1)
    elif critical:
        print(f"RESULT: PASSED WITH GAPS — {len(critical)} critical, {len(warnings)} warnings")
        print("NOTE: deep_research gaps are non-blocking in NORMAL mode")
        sys.exit(0)
    elif warnings:
        print(f"RESULT: PASSED — {len(warnings)} warnings only")
        sys.exit(0)
    else:
        print("RESULT: PASSED — all checks green")
        sys.exit(0)


if __name__ == "__main__":
    main()
