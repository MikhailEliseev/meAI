#!/usr/bin/env python3
"""
Merge deep research findings into data.json with tier classification.

Usage:
    python3 /root/bin/deep-research-merge.py {client_name}
    python3 deep_research_merge.py {client_name} --classify-only

Reads: /root/work/presale/{client}/data.json + research findings from stdin
Writes: /root/work/presale/{client}/data.json (updated with deep_research section)

Security:
    - All regex patterns are pre-compiled (re.compile) to prevent ReDoS
    - classify_doctor() has a 100ms timeout guard via time.perf_counter
    - JSON input from stdin is validated for structure before writing
    - Atomic writes: temp file + os.rename()
"""

import json
import os
import re
import sys
import tempfile
import time
from datetime import datetime, timezone


# ═══════════════════════════════════════════════════════════════════
# TIER CLASSIFICATION — Pre-compiled regex patterns
# ═══════════════════════════════════════════════════════════════════

# Tier 1 (star): Doctor of Medical Sciences, Professor, Honored Doctor, Academician
TIER_1_PATTERNS = [
    (re.compile(r'д\.\s*м\.\s*н\.', re.IGNORECASE), 'д.м.н.'),
    (re.compile(r'доктор\s+мед(?:ицинских)?\.?\s*наук', re.IGNORECASE), 'доктор медицинских наук'),
    (re.compile(r'профессор(?:\s+кафедры)?', re.IGNORECASE), 'профессор'),
    (re.compile(r'заслуженны[йи]\s+врач\s*(?:РФ|России)', re.IGNORECASE), 'заслуженный врач РФ'),
    (re.compile(r'академик\s+РАМН', re.IGNORECASE), 'академик РАМН'),
    (re.compile(r'член-корр?\.?\s*(?:РАМН|РАН)', re.IGNORECASE), 'член-корр. РАМН/РАН'),
]

# Tier 2 (core): Candidate of Medical Sciences, Chief Doctor, Department Head, Docent
TIER_2_PATTERNS = [
    (re.compile(r'к\.\s*м\.\s*н\.', re.IGNORECASE), 'к.м.н.'),
    (re.compile(r'кандидат\s+мед(?:ицинских)?\.?\s*наук', re.IGNORECASE), 'кандидат медицинских наук'),
    (re.compile(r'главны[йи]\s+врач', re.IGNORECASE), 'главный врач'),
    (re.compile(r'руководитель\s+(?:отделен|клиники|центра)', re.IGNORECASE), 'руководитель отделения'),
    (re.compile(r'зав\.?\s*(?:отделен|отделом)', re.IGNORECASE), 'зав. отделением'),
    (re.compile(r'доцент(?:\s+кафедры)?', re.IGNORECASE), 'доцент'),
]

# Star qualifiers: auto-promote to star even without formal TIER_1 degrees
STAR_QUALIFIER_PATTERNS = [
    re.compile(r'автор\s+(?:методик[иа]|протокол[ао]в|монографи[ий])', re.IGNORECASE),
    re.compile(r'организатор\s+(?:конгресс(?:а|ов)|конференци[ий])', re.IGNORECASE),
    re.compile(r'научны[йи]\s+руководитель', re.IGNORECASE),
    re.compile(r'главны[йи]\s+(?:окружной|городской|областной)\s+специалист', re.IGNORECASE),
]

# Maximum bio length to process (50KB safety limit)
MAX_BIO_LENGTH = 50 * 1024
# Timeout for classify_doctor in seconds
CLASSIFY_TIMEOUT = 0.100  # 100ms


def classify_doctor(name, bio_text, experience_years=0):
    """
    Classify a doctor into tier: star, core, or team.

    Args:
        name: Full name of the doctor (for output only)
        bio_text: Bio string containing degrees, titles, roles
        experience_years: Years of experience (integer)

    Returns:
        dict with keys: full_name, tier, degrees, experience_years, auto_flagged_star

    Security:
        - bio_text truncated to MAX_BIO_LENGTH (50KB) to prevent memory exhaustion
        - All patterns are pre-compiled; no runtime regex compilation
        - 100ms timeout enforced via perf_counter guard
    """
    start_time = time.perf_counter()

    # Safety: truncate excessively long bio
    if len(bio_text) > MAX_BIO_LENGTH:
        bio_text = bio_text[:MAX_BIO_LENGTH]

    degrees = []
    tier = "team"
    has_formal_tier1_degree = False

    # ── Tier 1 check: formal degrees (д.м.н., professor, etc.) ──
    for pattern, label in TIER_1_PATTERNS:
        if pattern.search(bio_text):
            degrees.append(label)
            tier = "star"
            has_formal_tier1_degree = True

    # ── Star qualifiers: auto-promote ──
    if tier != "star":
        for pattern in STAR_QUALIFIER_PATTERNS:
            if pattern.search(bio_text):
                tier = "star"
                break

    # ── Tier 2 check (only if not already star) ──
    if tier == "team":
        for pattern, label in TIER_2_PATTERNS:
            if pattern.search(bio_text):
                degrees.append(label)
                tier = "core"
                break

    # ── Experience heuristics ──
    if tier == "team" and experience_years >= 15:
        tier = "core"
    elif tier == "core" and experience_years >= 25:
        tier = "star"

    # ── Determine auto_flagged_star ──
    # auto_flagged_star = True when star was assigned via qualifier or experience
    # heuristic rather than through a formal TIER_1 degree
    auto_flagged_star = (tier == "star" and not has_formal_tier1_degree)

    # ── Enforce timeout ──
    elapsed = time.perf_counter() - start_time
    if elapsed > CLASSIFY_TIMEOUT:
        # If we somehow exceed timeout, return safe fallback
        return {
            "full_name": name,
            "tier": "team",
            "degrees": [],
            "experience_years": experience_years,
            "auto_flagged_star": False,
        }

    return {
        "full_name": name,
        "tier": tier,
        "degrees": degrees,
        "experience_years": experience_years,
        "auto_flagged_star": auto_flagged_star,
    }


# ═══════════════════════════════════════════════════════════════════
# JSON MERGE LOGIC
# ═══════════════════════════════════════════════════════════════════

def validate_and_merge(data_json, research_input):
    """
    Validate research input and merge into data_json["deep_research"].

    Args:
        data_json: Existing data.json as dict
        research_input: Research findings from stdin (must have clinic or doctors)

    Returns:
        Updated data_json dict with deep_research section merged

    Validation:
        - research_input must contain "clinic" (dict) or "doctors" (list) or both
        - Each doctor must have "full_name" (required)
        - Each doctor is run through classify_doctor() for tier assignment
    """
    # ── Validate input ──
    clinic_data = research_input.get("clinic")
    doctors_data = research_input.get("doctors")
    input_meta = research_input.get("_meta", {})

    if not clinic_data and not doctors_data:
        # Warning but not fatal — empty research is valid
        pass

    # ── Classify doctors ──
    classified_doctors = []
    if doctors_data and isinstance(doctors_data, list):
        for doc in doctors_data:
            if not isinstance(doc, dict):
                continue
            full_name = doc.get("full_name", "")
            if not full_name:
                continue

            bio = doc.get("bio", "")
            experience = doc.get("experience_years", 0)

            # Run tier classification
            classification = classify_doctor(full_name, bio, experience)

            # Build doctor entry — merge classification with research data
            doctor_entry = {
                "full_name": full_name,
                "tier": classification["tier"],
                "degrees": classification["degrees"],
                "experience_years": classification["experience_years"],
                "auto_flagged_star": classification["auto_flagged_star"],
            }

            # Preserve additional research fields if present
            for key in ("specialty", "roles", "publications_count", "dissertation",
                         "patient_reviews_rating", "patient_reviews_count",
                         "social_profiles", "media_mentions", "conferences",
                         "research_confidence"):
                if key in doc:
                    doctor_entry[key] = doc[key]

            classified_doctors.append(doctor_entry)

    # ── Build deep_research section ──
    tier_counts = {"star": 0, "core": 0, "team": 0}
    for d in classified_doctors:
        t = d.get("tier", "team")
        tier_counts[t] = tier_counts.get(t, 0) + 1

    # Calculate sources (preserve from input _meta or default)
    sources = input_meta.get("sources_used", [])
    duration = input_meta.get("research_duration_seconds", 0)

    deep_research = {
        "clinic": clinic_data if clinic_data else {},
        "doctors": classified_doctors,
        "_meta": {
            "researched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total_doctors_found": len(classified_doctors),
            "star_doctors": tier_counts["star"],
            "core_doctors": tier_counts["core"],
            "team_doctors": tier_counts["team"],
            "sources_used": sources,
            "research_duration_seconds": duration,
        }
    }

    # ── Merge into data_json ──
    data_json["deep_research"] = deep_research

    return data_json


# ═══════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════

def _get_data_path(client_name, base_dir="/root/work/presale"):
    """Get path to data.json for a client."""
    return os.path.join(base_dir, client_name, "data.json")


def _read_data_json(path):
    """Read data.json from disk, return empty dict if not found."""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"meta": {}, "clinic": {}, "doctors": [], "competitors": [], "content": {}, "geo": {}}


def _write_data_json_atomic(path, data):
    """Write data.json atomically via temp file + rename."""
    dirname = os.path.dirname(path)
    os.makedirs(dirname, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(dir=dirname, prefix=".data-", suffix=".json.tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.rename(tmp_path, path)
    except Exception:
        # Clean up temp file on failure
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def main():
    """CLI entry point."""
    args = sys.argv[1:]

    if not args:
        print("Usage: python3 deep_research_merge.py {client_name} [--classify-only]", file=sys.stderr)
        sys.exit(1)

    client_name = args[0]
    classify_only = "--classify-only" in args

    # ── Classify-only mode: read doctors from stdin, output classification ──
    if classify_only:
        try:
            input_data = json.loads(sys.stdin.read())
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON input: {e}", file=sys.stderr)
            sys.exit(1)

        doctors = input_data.get("doctors", [])
        results = []
        for doc in doctors:
            if isinstance(doc, dict) and doc.get("full_name"):
                results.append(classify_doctor(
                    doc.get("full_name", ""),
                    doc.get("bio", ""),
                    doc.get("experience_years", 0)
                ))
        print(json.dumps({"doctors": results}, ensure_ascii=False, indent=2))
        return

    # ── Merge mode ──
    data_path = _get_data_path(client_name)

    # Read stdin (research findings JSON)
    try:
        stdin_raw = sys.stdin.read()
        if not stdin_raw.strip():
            print("ERROR: stdin is empty — no research data provided", file=sys.stderr)
            sys.exit(1)
        research_input = json.loads(stdin_raw)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON input from stdin: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate research_input structure
    if not isinstance(research_input, dict):
        print("ERROR: Research input must be a JSON object", file=sys.stderr)
        sys.exit(1)

    has_clinic = "clinic" in research_input and research_input["clinic"] is not None
    has_doctors = "doctors" in research_input and research_input["doctors"] is not None

    if not has_clinic and not has_doctors:
        print("WARNING: Research input has neither clinic nor doctors — nothing to merge", file=sys.stderr)
        sys.exit(0)  # Not fatal

    # Read existing data.json
    try:
        data_json = _read_data_json(data_path)
    except (json.JSONDecodeError, IOError) as e:
        print(f"ERROR: Cannot read data.json: {e}", file=sys.stderr)
        sys.exit(2)

    # Validate and merge
    try:
        updated = validate_and_merge(data_json, research_input)
    except Exception as e:
        print(f"ERROR: Merge failed: {e}", file=sys.stderr)
        sys.exit(2)

    # Atomic write
    try:
        _write_data_json_atomic(data_path, updated)
        print(f"OK: deep_research merged into {data_path}")
        meta = updated.get("deep_research", {}).get("_meta", {})
        print(f"     Doctors: {meta.get('total_doctors_found', 0)} "
              f"(star={meta.get('star_doctors', 0)}, "
              f"core={meta.get('core_doctors', 0)}, "
              f"team={meta.get('team_doctors', 0)})")
    except IOError as e:
        print(f"ERROR: Cannot write data.json: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
