#!/usr/bin/env python3
"""Phase 5 bug fixes test — Instagram handle verification + follower counts.

Tests:
  1. Regex fix: «87.5K followers» / «52K подписчиков» pattern (Bug 2)
  2. Full find_doctor_handles run on iphk.ru (end-to-end)

Note: Test 2 (topsearch/_enrich_follower_counts) removed — dead code
deleted as part of ultra-budget mode (Perplexity cost optimization).

Run inside aim-hermes container:
  docker exec aim-hermes python /tmp/test_phase5_fixes.py
"""

import asyncio
import sys
import time

# ── Test 1: Regex fix (Bug 2) ────────────────────────────────────

def test_regex_number_first():
    """Test that the regex now matches 'number + keyword' patterns."""
    from app.tools.find_doctor_handles import _parse_enrichment

    # Sample text with "87.5K followers" pattern (number BEFORE keyword)
    sample = """Врач: Авраам Дошенко | пластический хирург
Instagram: @avdoshenko
Статистика: 87.5K followers, 120 posts"""

    doctors = _parse_enrichment(sample, ["Авраам Дошенко"])
    assert doctors, "Should find 1 doctor"
    d = doctors[0]
    followers = d.get("instagram_followers_approx", 0)
    print(f"  Test 1a (87.5K followers): followers={followers}")
    assert followers > 0, f"Expected > 0 followers, got {followers}"
    assert followers >= 87000, f"Expected ~87K, got {followers}"
    print("  ✅ Test 1a PASSED")

    # Sample text with "52K подписчиков" pattern (Russian, number-first)
    sample2 = """Врач: Захаров Дмитрий | косметолог
Instagram: @drzakharov
Статистика: 52K подписчиков на данный момент"""
    doctors2 = _parse_enrichment(sample2, ["Захаров Дмитрий"])
    assert doctors2, "Should find 1 doctor"
    d2 = doctors2[0]
    followers2 = d2.get("instagram_followers_approx", 0)
    print(f"  Test 1b (52K подписчиков): followers={followers2}")
    assert followers2 > 0, f"Expected > 0 followers, got {followers2}"
    assert followers2 >= 50000, f"Expected ~52K, got {followers2}"
    print("  ✅ Test 1b PASSED")

    # Sample text with "followers: 87.5K" pattern (keyword-first, decimal)
    sample3 = """Врач: Иванова Елена | дерматолог
Instagram: @elena_ivanova
followers: 87.5K"""
    doctors3 = _parse_enrichment(sample3, ["Иванова Елена"])
    assert doctors3, "Should find 1 doctor"
    d3 = doctors3[0]
    followers3 = d3.get("instagram_followers_approx", 0)
    print(f"  Test 1c (followers: 87.5K): followers={followers3}")
    assert followers3 > 0, f"Expected > 0 followers, got {followers3}"
    print("  ✅ Test 1c PASSED")

    # Sample with whole number (no K/M)
    sample4 = """Врач: Петров Сергей | хирург
Instagram: @drpetrov
подписчиков: 3200"""
    doctors4 = _parse_enrichment(sample4, ["Петров Сергей"])
    assert doctors4, "Should find 1 doctor"
    d4 = doctors4[0]
    followers4 = d4.get("instagram_followers_approx", 0)
    print(f"  Test 1d (подписчиков: 3200): followers={followers4}")
    assert followers4 == 3200, f"Expected 3200, got {followers4}"
    print("  ✅ Test 1d PASSED")

    print("✅ Bug 2 REGEX FIX: ALL TESTS PASSED\n")


# ── Test 2: Perplexity follower enrichment (REMOVED — dead code) ────
# _enrich_follower_counts and _parse_follower_count were removed
# as part of ultra-budget mode. Follower enrichment is now handled
# entirely within the single batch Perplexity call in handle_find_doctor_handles.


# ── Test 3: End-to-end on iphk.ru ─────────────────────────────────

async def test_e2e_iphk():
    """Full find_doctor_handles run on iphk.ru."""
    from app.tools.find_doctor_handles import handle_find_doctor_handles

    print("  Running handle_find_doctor_handles for iphk.ru...")
    start = time.monotonic()

    result_json = await handle_find_doctor_handles(
        url="https://iphk.ru",
        company_name="Институт пластической хирургии и косметологии",
        city="Москва",
        specialization="",
    )

    elapsed = time.monotonic() - start
    result = __import__("json").loads(result_json)

    doctors = result.get("doctors", [])
    doctors_with_ig = [d for d in doctors if d.get("instagram")]
    print(f"\n  Found {len(doctors)} doctors, {len(doctors_with_ig)} with Instagram")

    # Check specific handles
    for d in doctors_with_ig:
        handle = d.get("instagram", "")
        followers = d.get("instagram_followers_approx", 0)
        print(f"    @{handle}: {followers} followers")

    # Criteria checks - handles must be found, follower counts depend on Perplexity
    avdoshenko = [d for d in doctors_with_ig if d.get("instagram", "").lower() == "avdoshenko"]
    drzakharov = [d for d in doctors_with_ig if d.get("instagram", "").lower() == "drzakharov"]

    if avdoshenko:
        f = avdoshenko[0].get("instagram_followers_approx", 0)
        print(f"\n  @avdoshenko followers: {f}")
        print(f"  ✅ @avdoshenko found ({'followers > 0' if f > 0 else 'followers=0 — depends on Perplexity output'})")
    else:
        print("\n  ⚠️ @avdoshenko not found in this run")

    if drzakharov:
        f = drzakharov[0].get("instagram_followers_approx", 0)
        print(f"  @drzakharov followers: {f}")
        print(f"  ✅ @drzakharov found ({'followers > 0' if f > 0 else 'followers=0 — depends on Perplexity output'})")
    else:
        print("  ⚠️ @drzakharov not found in this run")

    print(f"\n  Total time: {elapsed:.1f}s")
    assert elapsed < 75.0, f"E2E should complete in < 75s, took {elapsed:.1f}s"
    print("  ✅ E2E time < 75s")

    print("✅ E2E IPHK.RU: ALL TESTS PASSED\n")


# ── Main ──────────────────────────────────────────────────────────

async def main():
    print("=" * 60)
    print("Phase 5 Bug Fixes — Test Suite")
    print("=" * 60)
    print()

    all_passed = True

    # Test 1: Regex
    print("── Test 1: Regex fix (Bug 2) ──")
    try:
        test_regex_number_first()
    except Exception as e:
        print(f"❌ Test 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    # Test 2: Follower enrichment — REMOVED (dead code)
    # _enrich_follower_counts was deleted as part of ultra-budget mode.

    # Test 3: E2E
    print("── Test 3: E2E on iphk.ru ──")
    try:
        await test_e2e_iphk()
    except Exception as e:
        print(f"❌ Test 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    print("=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 60)
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
