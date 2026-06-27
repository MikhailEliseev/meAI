"""
E2E test for Phase 7 SMI MENTIONS — Mass Media Mentions Search.

Tests:
  1. iphk.ru (Институт пластической хирургии, Москва) — niche clinic, likely few mentions
  2. Validates JSON structure and pass results

Usage:
  python test_phase7_e2e.py
  python test_phase7_e2e.py "СМ-Клиника" "Москва"  # large clinic
"""
import asyncio, json, sys, time, os

sys.path.insert(0, "AIM/hermes/app")

TEST_URL = sys.argv[1] if len(sys.argv) > 1 else "https://iphk.ru"
TEST_NAME = sys.argv[2] if len(sys.argv) > 2 else "Институт пластической хирургии"
TEST_CITY = sys.argv[3] if len(sys.argv) > 3 else "Москва"


def validate_structure(data: dict) -> list[str]:
    """Validate the result JSON structure. Returns list of issues."""
    issues = []

    required_top = ["search_term", "total_mentions", "categories_with_mentions",
                    "categories_total", "categories", "top_mentions", "source"]
    for key in required_top:
        if key not in data:
            issues.append(f"Missing top-level key: {key}")

    if "categories" in data:
        expected_cats = ["business", "medical", "regional", "lifestyle"]
        for cat in expected_cats:
            if cat not in data["categories"]:
                issues.append(f"Missing category: {cat}")
            else:
                cat_data = data["categories"][cat]
                for field in ["category", "weight", "mentions_found", "mentions"]:
                    if field not in cat_data:
                        issues.append(f"Category {cat} missing field: {field}")

    if "total_mentions" in data and "categories" in data:
        computed = sum(c["mentions_found"] for c in data["categories"].values())
        if computed != data["total_mentions"]:
            issues.append(f"total_mentions mismatch: {data['total_mentions']} vs computed {computed}")

    return issues


async def main():
    print(f"\U0001f9ea Phase 7 E2E test: {TEST_NAME} ({TEST_CITY})")
    print(f"   URL: {TEST_URL}\n")

    print("=" * 60)
    print("Running run_smi_mentions")
    print("=" * 60)

    t0 = time.monotonic()
    from app.tools.run_smi_mentions import handle_run_smi_mentions

    result_json = await handle_run_smi_mentions(
        url=TEST_URL, company_name=TEST_NAME
    )
    t1 = time.monotonic()

    data = json.loads(result_json)

    if "error" in data and "categories" not in data:
        print(f"\n❌ FAILED ({t1 - t0:.1f}s): {data.get('error')}")
        print(f"   detail: {data.get('detail', '')[:200]}")
        return

    print(f"\n✅ Tool completed ({t1 - t0:.1f}s)")

    # Summary
    print(f"\n{'─' * 60}")
    print("SUMMARY:")
    print("─" * 60)
    print(f"  Search term:          {data.get('search_term')}")
    print(f"  Total mentions:       {data.get('total_mentions')}")
    print(f"  Categories with hits: {data.get('categories_with_mentions')}/{data.get('categories_total')}")
    print(f"  Source:               {data.get('source')}")

    # Category breakdown
    print(f"\n{'─' * 60}")
    print("CATEGORY BREAKDOWN:")
    print("─" * 60)
    for cat_key in ["business", "medical", "regional", "lifestyle"]:
        cat = data.get("categories", {}).get(cat_key, {})
        name = cat.get("category", cat_key)
        found = cat.get("mentions_found", 0)
        weight = cat.get("weight", 0)
        icon = "✅" if found > 0 else "📭"
        print(f"  {icon} {name:20s} weight={weight:.0%}  mentions={found}")

    # Top mentions
    top = data.get("top_mentions", [])
    if top:
        print(f"\n{'─' * 60}")
        print(f"TOP MENTIONS ({len(top)}):")
        print("─" * 60)
        for m in top[:5]:
            print(f"  - {m.get('title', '?')[:80]}")
            print(f"    {m.get('url', '?')}")

    # Validate structure
    issues = validate_structure(data)
    if issues:
        print(f"\n❌ STRUCTURE ISSUES:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print(f"\n✅ Structure valid")

    # Final verdict
    print(f"\n{'=' * 60}")
    total = data.get("total_mentions", 0)
    cats_hit = data.get("categories_with_mentions", 0)
    if total > 0:
        print(f"✅ RESULT: {total} SMI mentions found in {cats_hit} categories")
    else:
        print(f"⚠️  RESULT: No SMI mentions found (this is normal for niche clinics)")

    print(f"\n⏱️  Total: {t1 - t0:.1f}s")
    print("✅ Phase 7 E2E test complete!")


if __name__ == "__main__":
    asyncio.run(main())
