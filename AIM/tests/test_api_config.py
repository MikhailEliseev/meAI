"""
Test API Configuration and Caching
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "AIM" / "src"))
sys.path.insert(0, str(project_root / "src"))

from aim.core.api_config import get_api_config, get_api_cache


async def test_api_config():
    """Test API Configuration and Caching"""

    print("=" * 80)
    print("TEST: API Configuration and Caching")
    print("=" * 80)

    # Test 1: API Config
    print("\n" + "=" * 80)
    print("TEST 1: API Configuration")
    print("=" * 80)

    config = get_api_config()

    print(f"\n✅ API Configuration:")
    print(f"   PageSpeed API Key: {'configured' if config.has_pagespeed_api_key() else 'not configured'}")
    print(f"   Rate limits: {config.pagespeed_rpm} req/min, {config.pagespeed_rpd} req/day")
    print(f"   Cache TTL: {config.cache_ttl_hours} hours")

    # Test 2: Rate Limiter
    print("\n" + "=" * 80)
    print("TEST 2: Rate Limiter")
    print("=" * 80)

    rate_limiter = config.rate_limiter

    print(f"\n✅ Rate Limiter Stats (before):")
    stats = rate_limiter.get_stats()
    print(f"   Requests last minute: {stats['requests_last_minute']}")
    print(f"   Requests last day: {stats['requests_last_day']}")
    print(f"   RPM remaining: {stats['rpm_remaining']}")
    print(f"   RPD remaining: {stats['rpd_remaining']}")

    # Simulate 3 requests
    print(f"\n🔄 Simulating 3 API requests...")
    for i in range(3):
        await rate_limiter.acquire()
        print(f"   Request {i+1} acquired")

    print(f"\n✅ Rate Limiter Stats (after):")
    stats = rate_limiter.get_stats()
    print(f"   Requests last minute: {stats['requests_last_minute']}")
    print(f"   Requests last day: {stats['requests_last_day']}")
    print(f"   RPM remaining: {stats['rpm_remaining']}")
    print(f"   RPD remaining: {stats['rpd_remaining']}")

    # Test 3: Cache
    print("\n" + "=" * 80)
    print("TEST 3: API Cache")
    print("=" * 80)

    cache = get_api_cache()

    print(f"\n✅ Cache Stats (before):")
    stats = cache.get_stats()
    print(f"   Total entries: {stats['total_entries']}")
    print(f"   Total size: {stats['total_size_mb']:.2f} MB")
    print(f"   Cache dir: {stats['cache_dir']}")

    # Test cache set/get
    print(f"\n🔄 Testing cache set/get...")
    test_url = "https://example.com"
    test_params = {"strategy": "mobile", "category": "performance"}
    test_response = {"test": "data", "score": 85}

    cache.set(test_url, test_params, test_response)
    print(f"   ✅ Cached response for {test_url}")

    cached = cache.get(test_url, test_params)
    if cached:
        print(f"   ✅ Retrieved from cache: {cached}")
    else:
        print(f"   ❌ Cache miss")

    # Test cache with different params (should miss)
    different_params = {"strategy": "desktop", "category": "performance"}
    cached = cache.get(test_url, different_params)
    if cached:
        print(f"   ❌ Unexpected cache hit")
    else:
        print(f"   ✅ Cache miss (as expected for different params)")

    print(f"\n✅ Cache Stats (after):")
    stats = cache.get_stats()
    print(f"   Total entries: {stats['total_entries']}")
    print(f"   Total size: {stats['total_size_mb']:.2f} MB")

    # Test 4: Clear expired cache
    print("\n" + "=" * 80)
    print("TEST 4: Clear Expired Cache")
    print("=" * 80)

    print(f"\n🔄 Clearing expired cache entries...")
    cache.clear_expired()

    print(f"\n✅ Cache Stats (after cleanup):")
    stats = cache.get_stats()
    print(f"   Total entries: {stats['total_entries']}")
    print(f"   Total size: {stats['total_size_mb']:.2f} MB")

    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 80)

    print("\n📝 Notes:")
    print("   - PageSpeed API key is optional (works without for limited requests)")
    print("   - Rate limiter prevents exceeding API limits")
    print("   - Cache reduces API calls and improves performance")
    print("   - Cache TTL: 24 hours (configurable via .env)")


if __name__ == "__main__":
    asyncio.run(test_api_config())
