"""
API Configuration and Rate Limiting

Manages external API keys, rate limiting, and caching for CI system.

Supports:
- PageSpeed Insights API
- Rate limiting (requests per minute/day)
- Response caching (avoid duplicate requests)
- Fallback strategies (when API unavailable)
"""

import asyncio
import hashlib
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv


class APIConfig:
    """API Configuration Manager"""

    def __init__(self):
        # Load environment variables
        load_dotenv()

        # PageSpeed Insights API
        self.pagespeed_api_key = os.getenv("PAGESPEED_API_KEY")
        self.pagespeed_rpm = int(os.getenv("PAGESPEED_REQUESTS_PER_MINUTE", "60"))
        self.pagespeed_rpd = int(os.getenv("PAGESPEED_REQUESTS_PER_DAY", "25000"))

        # Cache configuration
        self.cache_ttl_hours = int(os.getenv("PAGESPEED_CACHE_TTL_HOURS", "24"))
        self.cache_dir = Path("AIM/data/api_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Rate limiting state
        self.rate_limiter = RateLimiter(
            requests_per_minute=self.pagespeed_rpm,
            requests_per_day=self.pagespeed_rpd
        )

    def get_pagespeed_api_key(self) -> Optional[str]:
        """Get PageSpeed Insights API key"""
        return self.pagespeed_api_key

    def has_pagespeed_api_key(self) -> bool:
        """Check if PageSpeed API key is configured"""
        return bool(self.pagespeed_api_key)


class RateLimiter:
    """Rate Limiter for API requests"""

    def __init__(self, requests_per_minute: int = 60, requests_per_day: int = 25000):
        self.rpm = requests_per_minute
        self.rpd = requests_per_day

        # Tracking
        self.minute_requests = []  # List of timestamps
        self.day_requests = []     # List of timestamps

    async def acquire(self):
        """Acquire permission to make API request (with rate limiting)"""
        now = time.time()

        # Clean old requests
        self._clean_old_requests(now)

        # Check rate limits
        while len(self.minute_requests) >= self.rpm:
            # Wait until oldest request expires
            oldest = self.minute_requests[0]
            wait_time = 60 - (now - oldest)
            if wait_time > 0:
                print(f"[Rate Limiter] ⏳ Rate limit reached, waiting {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
                now = time.time()
                self._clean_old_requests(now)
            else:
                break

        if len(self.day_requests) >= self.rpd:
            raise Exception(f"Daily rate limit reached ({self.rpd} requests/day)")

        # Record request
        self.minute_requests.append(now)
        self.day_requests.append(now)

    def _clean_old_requests(self, now: float):
        """Remove requests older than tracking window"""
        # Remove requests older than 1 minute
        self.minute_requests = [t for t in self.minute_requests if now - t < 60]

        # Remove requests older than 1 day
        self.day_requests = [t for t in self.day_requests if now - t < 86400]

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        return {
            "requests_last_minute": len(self.minute_requests),
            "requests_last_day": len(self.day_requests),
            "rpm_limit": self.rpm,
            "rpd_limit": self.rpd,
            "rpm_remaining": self.rpm - len(self.minute_requests),
            "rpd_remaining": self.rpd - len(self.day_requests)
        }


class APICache:
    """Cache for API responses"""

    def __init__(self, cache_dir: Path, ttl_hours: int = 24):
        self.cache_dir = cache_dir
        self.ttl_hours = ttl_hours
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, url: str, params: Dict[str, Any]) -> str:
        """Generate cache key from URL and params"""
        # Create deterministic hash
        key_data = f"{url}:{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    def _get_cache_file(self, cache_key: str) -> Path:
        """Get cache file path"""
        return self.cache_dir / f"{cache_key}.json"

    def get(self, url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached response"""
        cache_key = self._get_cache_key(url, params)
        cache_file = self._get_cache_file(cache_key)

        if not cache_file.exists():
            return None

        # Check if cache is expired
        cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        if cache_age > timedelta(hours=self.ttl_hours):
            # Cache expired, delete it
            cache_file.unlink()
            return None

        # Read cache
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                return cached_data
        except Exception:
            return None

    def set(self, url: str, params: Dict[str, Any], response: Dict[str, Any]):
        """Cache response"""
        cache_key = self._get_cache_key(url, params)
        cache_file = self._get_cache_file(cache_key)

        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(response, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Cache] ⚠️  Failed to cache response: {e}")

    def clear_expired(self):
        """Clear expired cache entries"""
        now = datetime.now()
        expired_count = 0

        for cache_file in self.cache_dir.glob("*.json"):
            cache_age = now - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if cache_age > timedelta(hours=self.ttl_hours):
                cache_file.unlink()
                expired_count += 1

        if expired_count > 0:
            print(f"[Cache] 🗑️  Cleared {expired_count} expired cache entries")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)

        return {
            "total_entries": len(cache_files),
            "total_size_mb": total_size / (1024 * 1024),
            "cache_dir": str(self.cache_dir)
        }


# Global instances
_api_config = None
_api_cache = None


def get_api_config() -> APIConfig:
    """Get global API config instance"""
    global _api_config
    if _api_config is None:
        _api_config = APIConfig()
    return _api_config


def get_api_cache() -> APICache:
    """Get global API cache instance"""
    global _api_cache
    if _api_cache is None:
        config = get_api_config()
        _api_cache = APICache(
            cache_dir=config.cache_dir,
            ttl_hours=config.cache_ttl_hours
        )
    return _api_cache


# Example usage
if __name__ == "__main__":
    config = get_api_config()
    print(f"PageSpeed API Key: {'configured' if config.has_pagespeed_api_key() else 'not configured'}")
    print(f"Rate limits: {config.pagespeed_rpm} req/min, {config.pagespeed_rpd} req/day")
    print(f"Cache TTL: {config.cache_ttl_hours} hours")

    cache = get_api_cache()
    stats = cache.get_stats()
    print(f"Cache: {stats['total_entries']} entries, {stats['total_size_mb']:.2f} MB")
