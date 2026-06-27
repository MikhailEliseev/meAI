"""
E2E test for Phase 6 HIRING SIGNALS — Multi-Pass HH.ru Vacancy Analysis.

Tests:
  1. iphk.ru (small clinic, likely no hh.ru employer) → expect no_data + HIGH confidence
  2. СМ-Клиника (large clinic, should have vacancies) → expect data_found

Usage:
  python test_phase6_e2e.py                    # default: iphk.ru
  python test_phase6_e2e.py "СМ-Клиника" "" "Москва"  # large clinic test
"""
import asyncio, json, sys, time, os

sys.path.insert(0, "AIM/hermes/app")

TEST_URL = sys.argv[1] if len(sys.argv) > 1 else "https://iphk.ru"
TEST_NAME = sys.argv[2] if len(sys.argv) > 2 else "Институт пластической хирургии"
TEST_CITY = sys.argv[3] if len(sys.argv) > 3 else "Москва"


def validate_structure(data: dict) -> list[str]:
    """Validate the result JSON structure. Returns list of issues."""
    issues = []

    required_top = ["search_term", "searched_as", "area_id", "confidence", "verdict", "vacancies_found", "passes", "vacancies"]
    for key in required_top:
        if key not in data:
            issues.append(f"Missing top-level key: {key}")

    if "passes" in data:
        passes = data["passes"]
        expected_passes = ["apify", "perplexity", "fallback", "alternative_names"]
        for p in expected_passes:
            if p not in passes:
                issues.append(f"Missing pass: {p}")

        for pass_name, pass_data in passes.items():
            if pass_data and "status" not in pass_data:
                issues.append(f"Pass {pass_name} missing 'status' field")

    if "confidence" in data:
        if data["confidence"] not in ("HIGH", "MEDIUM", "LOW"):
            issues.append(f"Invalid confidence: {data['confidence']}")

    if "verdict" in data:
        if data["verdict"] not in ("data_found", "no_data"):
            issues.append(f"Invalid verdict: {data['verdict']}")

    return issues


def analyze_pass_results(data: dict):
    """Print detailed pass-by-pass analysis."""
    print(f"\n{'─' * 60}")
    print("PASS RESULTS:")
    print("─" * 60)

    passes = data.get("passes", {})
    for pass_name in ["apify", "perplexity", "fallback", "alternative_names"]:
        pass_data = passes.get(pass_name)
        if not pass_data:
            print(f"  {pass_name:25s} ⚠️  MISSING")
            continue

        status = pass_data.get("status", "?")
        note = pass_data.get("note", "")

        icon = {"data_found": "✅", "empty": "📭", "error": "❌", "skipped": "⏭️ ", "inconclusive": "🤔"}.get(status, "❓")
        print(f"  {icon} {pass_name:23s} [{status:14s}] {note[:80]}")

        # Extra details for data_found
        if status == "data_found":
            if pass_name == "apify":
                print(f"     employer: {pass_data.get('employer_name', '?')}")
                print(f"     vacancies: {pass_data.get('vacancies_found', 0)}")
                print(f"     source: {pass_data.get('source', '?')}")
            elif pass_name == "fallback":
                results = pass_data.get("search_results", [])
                print(f"     results: {len(results)}")
                for r in results[:3]:
                    print(f"     - {r.get('title', '?')[:70]}")
            elif pass_name == "alternative_names":
                matches = pass_data.get("matches", [])
                print(f"     matches: {len(matches)}")


async def main():
    print(f"🧪 Phase 6 E2E test: {TEST_NAME} ({TEST_CITY})")
    print(f"   URL: {TEST_URL}\n")

    # Run the tool
    print("=" * 60)
    print("Running run_hh_analysis (multi-pass)")
    print("=" * 60)

    t0 = time.monotonic()
    from app.tools.run_hh_analysis import handle_run_hh_analysis

    result_json = await handle_run_hh_analysis(
        url=TEST_URL, company_name=TEST_NAME, city=TEST_CITY
    )
    t1 = time.monotonic()

    data = json.loads(result_json)

    # Check for errors
    if "error" in data and "passes" not in data:
        print(f"\n❌ FAILED ({t1 - t0:.1f}s): {data.get('error')}")
        print(f"   detail: {data.get('detail', '')[:200]}")
        return

    print(f"\n✅ Tool completed ({t1 - t0:.1f}s)")

    # Summary
    print(f"\n{'─' * 60}")
    print("SUMMARY:")
    print("─" * 60)
    print(f"  Search term:    {data.get('search_term')}")
    print(f"  Searched as:    {data.get('searched_as')}")
    print(f"  Area ID:        {data.get('area_id')}")
    print(f"  City:           {data.get('city')}")
    print(f"  Confidence:     {data.get('confidence')}")
    print(f"  Verdict:        {data.get('verdict')}")
    print(f"  Vacancies found:{data.get('vacancies_found')}")

    # Validate structure
    issues = validate_structure(data)
    if issues:
        print(f"\n❌ STRUCTURE ISSUES:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print(f"\n✅ Structure valid")

    # Detailed pass results
    analyze_pass_results(data)

    # Vacancies (if any)
    vacancies = data.get("vacancies", [])
    if vacancies:
        print(f"\n{'─' * 60}")
        print(f"VACANCIES ({len(vacancies)}):")
        print("─" * 60)
        for v in vacancies[:10]:
            salary = ""
            if v.get("salary_from") or v.get("salary_to"):
                fr = v.get("salary_from", "?")
                to = v.get("salary_to", "?")
                cur = v.get("salary_currency", "")
                salary = f" [{fr}-{to} {cur}]"
            print(f"  - {v.get('name', '?')}{salary}")
            print(f"    {v.get('area', '?')} | {v.get('published_at', '?')[:10]}")

    # Final verdict
    print(f"\n{'=' * 60}")
    verdict = data.get("verdict", "?")
    confidence = data.get("confidence", "?")

    if verdict == "data_found":
        print(f"✅ RESULT: Vacancies found (confidence={confidence})")
    elif verdict == "no_data" and confidence == "HIGH":
        print(f"✅ RESULT: No vacancies — HIGH confidence (2+ independent passes agree)")
    elif verdict == "no_data":
        print(f"⚠️  RESULT: No vacancies — {confidence} confidence (some passes failed)")
    else:
        print(f"❓ RESULT: verdict={verdict}, confidence={confidence}")

    # Performance check
    if t1 - t0 > 120:
        print(f"⚠️  WARNING: Tool took {t1 - t0:.1f}s (expected <120s)")

    print(f"\n⏱️  Total: {t1 - t0:.1f}s")
    print("✅ Phase 6 E2E test complete!")


if __name__ == "__main__":
    asyncio.run(main())
