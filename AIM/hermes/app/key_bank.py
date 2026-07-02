"""key_bank — Unified API key registry for Hermes.

Single source of truth for ALL API keys. Replaces scattered os.environ.get()
calls across 30+ files with a centralized registry that supports:
- Key discovery (env, JSON pools, rotation banks)
- Health checks (HTTP 402/401/429/403 verification)
- Startup health report
- FirecrawlKeyBank + ApifyPool integration

Usage:
    from app.key_bank import key_bank
    api_key = key_bank.get("BRAVE_API_KEY")
    fc_key = key_bank.get_firecrawl_key()
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ── KeyEntry ───────────────────────────────────────────────────────────

@dataclass
class KeyEntry:
    """Single API key with metadata and health status."""

    name: str                 # "BRAVE_API_KEY"
    value: str                # сам ключ
    source: str               # "env" | "firecrawl_bank" | "apify_pool"
    service: str              # "Brave Search" | "Google PageSpeed" | "Firecrawl"
    category: str             # "search" | "llm" | "russian_market" | "messaging" | "internal"
    status: str = "unknown"   # "unknown" | "active" | "exhausted" | "invalid"
    last_checked: float = 0.0
    check_method: str | None = None   # "http_402" | "http_401" | "http_429" | "http_403"
    check_url: str = ""
    check_auth: str = ""      # "bearer" | "x-subscription-token" | "query:key" | "query:api_key"
    check_http: str = "GET"   # "GET" | "POST" — HTTP method for health check
    check_body: str = ""      # JSON body for POST checks
    exhausted_at: float | None = None


# ── KeyBank ────────────────────────────────────────────────────────────

class KeyBank:
    """Единый реестр API-ключей Hermes."""

    def __init__(self):
        self._keys: dict[str, KeyEntry] = {}
        self._firecrawl_bank = None       # FirecrawlKeyBank instance
        self._apify_pool = None           # ApifyKeyPool instance
        self._register_all()

    # ── Registration ───────────────────────────────────────────────

    def _register_all(self) -> None:
        """Register all known API keys from environment and external pools."""
        self._register_env_keys()
        self._register_firecrawl_keys()
        self._register_apify_keys()
        logger.info("KeyBank: registered %d keys", len(self._keys))

    def _register_env_keys(self) -> None:
        """Register keys from environment variables."""
        definitions = [
            # ── Search APIs ──
            ("BRAVE_API_KEY", "Brave Search", "search",
             "http_402", "https://api.search.brave.com/res/v1/web/search?q=test&count=1",
             "x-subscription-token"),
            ("SERPAPI_KEY", "SerpAPI", "search",
             "http_402", "https://serpapi.com/search?q=test&engine=google",
             "query:api_key"),
            ("SERPER_API_KEY", "Serper.dev", "search",
             "http_402", "https://google.serper.dev/search?q=test",
             "x-subscription-token"),  # Serper uses X-API-KEY, handled in check
            ("GOOGLE_API_KEY", "Google PageSpeed", "search",
             "http_403", "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=https://example.com",
             "query:key"),

            # ── LLM APIs ──
            ("PERPLEXITY_API_KEY", "Perplexity", "llm",
             "http_401", "https://api.perplexity.ai/chat/completions",
             "bearer"),
            ("DEEPSEEK_API_KEY", "DeepSeek", "llm", None, "", ""),
            ("OPENAI_API_KEY", "OpenAI", "llm", None, "", ""),
            ("ANTHROPIC_API_KEY", "Anthropic", "llm", None, "", ""),

            # ── Russian Market ──
            ("YANDEX_DIRECT_TOKEN", "Яндекс.Директ", "russian_market", None, "", ""),
            ("YANDEX_METRIKA_TOKEN", "Яндекс.Метрика", "russian_market", None, "", ""),

            # ── Messaging ──
            ("TELEGRAM_BOT_TOKEN", "Telegram Bot", "messaging", None, "", ""),
            ("TELEGRAM_CHAT_ID", "Telegram Chat", "messaging", None, "", ""),

            # ── Internal / Storage ──
            ("DATABASE_URL", "PostgreSQL", "internal", None, "", ""),
            ("REDIS_URL", "Redis", "internal", None, "", ""),
        ]

        for name, service, category, check_method, check_url, check_auth in definitions:
            value = os.environ.get(name, "").strip()
            if value:
                self._keys[name] = KeyEntry(
                    name=name, value=value, source="env",
                    service=service, category=category,
                    check_method=check_method, check_url=check_url,
                    check_auth=check_auth,
                )

    def _register_firecrawl_keys(self) -> None:
        """Register Firecrawl keys (delegates to FirecrawlKeyBank if available)."""
        # Multiple keys: FIRECRAWL_KEY_1..FIRECRAWL_KEY_20
        for i in range(1, 21):
            key = os.environ.get(f"FIRECRAWL_KEY_{i}", "").strip()
            if key:
                name = f"FIRECRAWL_KEY_{i}"
                self._keys[name] = KeyEntry(
                    name=name, value=key, source="env",
                    service="Firecrawl", category="search",
                    check_method="http_402",
                    check_url="https://api.firecrawl.dev/v2/search",
                    check_auth="bearer",
                    check_http="POST",
                    check_body='{"query":"test","limit":1}',
                )

        # Single key: FIRECRAWL_API_KEY
        single_key = os.environ.get("FIRECRAWL_API_KEY", "").strip()
        if single_key:
            self._keys["FIRECRAWL_API_KEY"] = KeyEntry(
                name="FIRECRAWL_API_KEY", value=single_key, source="env",
                service="Firecrawl", category="search",
                check_method="http_402",
                check_url="https://api.firecrawl.dev/v2/search",
                check_auth="bearer",
                check_http="POST",
                check_body='{"query":"test","limit":1}',
            )

        # Try to wrap FirecrawlKeyBank singleton
        try:
            from app.tools.firecrawl_key_bank import _bank as _fc_bank, _bank_lock
            with _bank_lock:
                if _fc_bank is not None:
                    self._firecrawl_bank = _fc_bank
                    for key in _fc_bank._keys:
                        # These keys may already be registered above; update source
                        for ek_name, ek in list(self._keys.items()):
                            if ek.value == key and ek.source == "env":
                                ek.source = "firecrawl_bank"
            logger.info("KeyBank: wrapped FirecrawlKeyBank (%d keys)",
                        len(self._firecrawl_bank._keys) if self._firecrawl_bank else 0)
        except ImportError:
            pass

    def _register_apify_keys(self) -> None:
        """Register Apify keys from apify_keys.json if available."""
        apify_token = os.environ.get("APIFY_API_TOKEN", "").strip()
        if apify_token:
            self._keys["APIFY_API_TOKEN"] = KeyEntry(
                name="APIFY_API_TOKEN", value=apify_token, source="env",
                service="Apify", category="russian_market",
                check_method="http_401",
                check_url="https://api.apify.com/v2/users/me",
                check_auth="bearer",
            )

        # Try loading from apify_keys.json
        try:
            import json as _json
            apify_keys_path = os.environ.get(
                "APIFY_KEYS_PATH",
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "apify_keys.json"),
            )
            apify_keys_path = os.path.abspath(apify_keys_path)
            if not os.path.exists(apify_keys_path):
                # Fallback: /opt/data/apify_keys.json (production path)
                apify_keys_path = "/opt/data/apify_keys.json"

            if os.path.exists(apify_keys_path):
                with open(apify_keys_path) as f:
                    keys_data = _json.load(f)

                # Support two formats:
                # 1. {"keys": [{"key": "...", "label": "...", "status": "active"}, ...]}
                # 2. ["key1", "key2", ...] (legacy)
                key_objects = []
                if isinstance(keys_data, dict):
                    key_objects = keys_data.get("keys", [])
                elif isinstance(keys_data, list):
                    key_objects = keys_data

                for i, entry in enumerate(key_objects):
                    if isinstance(entry, str) and entry.strip():
                        key_value = entry.strip()
                        key_status = "unknown"
                    elif isinstance(entry, dict):
                        key_value = entry.get("key") or entry.get("token", "")
                        key_status = entry.get("status", "unknown")
                    else:
                        continue

                    if not key_value:
                        continue

                    name = f"APIFY_KEY_{i + 1}"
                    self._keys[name] = KeyEntry(
                        name=name, value=key_value, source="apify_pool",
                        service="Apify", category="russian_market",
                        status=key_status,
                        check_method="http_401",
                        check_url="https://api.apify.com/v2/users/me",
                        check_auth="bearer",
                    )

                apify_keys = [e for e in self._keys.values() if e.service == "Apify" and e.source == "apify_pool"]
                if apify_keys:
                    active = sum(1 for e in apify_keys if e.status == "active")
                    logger.info("KeyBank: loaded %d Apify keys (%d active) from %s",
                               len(apify_keys), active, apify_keys_path)
        except Exception as e:
            logger.debug("KeyBank: Apify keys load skipped: %s", e)

    # ── Access ─────────────────────────────────────────────────────

    def get(self, name: str) -> str | None:
        """Get a key value by name. Returns None if not found."""
        entry = self._keys.get(name)
        if entry and entry.status != "invalid":
            return entry.value
        return None

    def get_firecrawl_key(self) -> str | None:
        """Get a Firecrawl key with rotation support.

        Delegates to FirecrawlKeyBank.get_key_with_fallback() if available,
        otherwise returns the first non-exhausted FIRECRAWL key from env.
        """
        if self._firecrawl_bank:
            return self._firecrawl_bank.get_key()
        # Fallback: find first active Firecrawl key
        for name, entry in self._keys.items():
            if entry.service == "Firecrawl" and entry.status != "exhausted":
                return entry.value
        return None

    def get_apify_keys(self, active_only: bool = True) -> list[str]:
        """Get all Apify keys. If active_only=True — skip exhausted/invalid."""
        result = []
        for entry in self._keys.values():
            if entry.service != "Apify":
                continue
            if active_only and entry.status in ("exhausted", "invalid"):
                continue
            if entry.value:
                result.append(entry.value)
        return result

    def mark_firecrawl_exhausted(self, key: str) -> None:
        """Mark a Firecrawl key as exhausted in both KeyBank and FirecrawlKeyBank."""
        if self._firecrawl_bank:
            self._firecrawl_bank.mark_exhausted(key)
        for entry in self._keys.values():
            if entry.value == key:
                entry.status = "exhausted"
                entry.exhausted_at = time.time()

    def get_apify_keys(self, active_only: bool = True) -> list[str]:
        """Get Apify keys from the pool.

        Args:
            active_only: If True, return only keys with status='active'.

        Returns:
            List of Apify API key strings.
        """
        apify_entries = [e for e in self._keys.values()
                         if e.service == "Apify" and e.source == "apify_pool"]
        if active_only:
            apify_entries = [e for e in apify_entries if e.status == "active"]
        return [e.value for e in apify_entries]

    def mark_apify_exhausted(self, key: str) -> None:
        """Mark an Apify key as exhausted."""
        for entry in self._keys.values():
            if entry.value == key:
                entry.status = "exhausted"
                entry.exhausted_at = time.time()
                logger.warning("KeyBank: marked Apify key %s as exhausted", entry.name)

    def active_count(self) -> int:
        """Count of active keys."""
        return sum(1 for e in self._keys.values() if e.status == "active")

    def exhausted_keys(self) -> list[str]:
        """List of exhausted key names."""
        return [e.name for e in self._keys.values() if e.status == "exhausted"]

    # ── Status ─────────────────────────────────────────────────────

    def status(self, name: str) -> dict:
        """Get status of a single key."""
        entry = self._keys.get(name)
        if not entry:
            return {"name": name, "status": "not_found"}
        return {
            "name": entry.name,
            "service": entry.service,
            "category": entry.category,
            "source": entry.source,
            "status": entry.status,
            "last_checked": entry.last_checked,
            "exhausted_at": entry.exhausted_at,
        }

    def report(self) -> str:
        """Formatted report string."""
        total = len(self._keys)
        by_status: dict[str, list[str]] = {}
        for e in self._keys.values():
            by_status.setdefault(e.status, []).append(e.name)

        lines = [f"Key Bank: {len(by_status.get('active', []))}/{total} active"]
        for status, label in [("exhausted", "exhausted"), ("invalid", "invalid"), ("unknown", "unknown")]:
            names = by_status.get(status, [])
            if names:
                lines.append(f"  {len(names)} {label}: {', '.join(names)}")
        return "\n".join(lines)

    # ── Health Checks ──────────────────────────────────────────────

    async def check(self, name: str) -> dict:
        """Check a single key via HTTP and update its status.

        Returns status dict with check result.
        """
        entry = self._keys.get(name)
        if not entry:
            return {"name": name, "status": "not_found"}
        if not entry.check_method or not entry.check_url:
            return self.status(name)

        result = await self._http_check(entry)
        entry.last_checked = time.time()
        entry.status = result["status"]
        if result["status"] == "exhausted":
            entry.exhausted_at = time.time()
        return result

    async def check_all(self) -> dict:
        """Check ALL keys in parallel. Returns summary dict."""
        if not self._keys:
            return {"total": 0, "active": 0, "exhausted": 0, "invalid": 0, "unknown": 0, "details": {}}

        # Check all keys with check methods in parallel
        checkable = [e for e in self._keys.values() if e.check_method and e.check_url]
        non_checkable = [e for e in self._keys.values() if not e.check_method or not e.check_url]

        results = {}
        if checkable:
            tasks = [self._http_check(entry) for entry in checkable]
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            now = time.time()
            for entry, result in zip(checkable, task_results):
                if isinstance(result, Exception):
                    results[entry.name] = {"status": "unknown", "error": str(result)}
                    entry.last_checked = now
                    continue
                results[entry.name] = result
                entry.last_checked = now
                entry.status = result["status"]
                if result["status"] == "exhausted":
                    entry.exhausted_at = now

        for entry in non_checkable:
            results[entry.name] = {"status": entry.status, "checked": False}

        # Count
        active = sum(1 for r in results.values() if r["status"] == "active")
        exhausted = sum(1 for r in results.values() if r["status"] == "exhausted")
        invalid = sum(1 for r in results.values() if r["status"] == "invalid")
        unknown = sum(1 for r in results.values() if r["status"] == "unknown")

        return {
            "total": len(self._keys),
            "active": active,
            "exhausted": exhausted,
            "invalid": invalid,
            "unknown": unknown,
            "details": results,
        }

    async def _http_check(self, entry: KeyEntry) -> dict:
        """Execute a single HTTP health check for a key.

        Uses httpx for the request. One lightweight request per key.
        """
        import httpx

        try:
            headers = self._build_auth_headers(entry)
            params = {}
            url = entry.check_url

            # query:key auth → add to URL params, not headers
            if entry.check_auth and entry.check_auth.startswith("query:"):
                param_name = entry.check_auth.split(":", 1)[1]
                params[param_name] = entry.value
                headers = {}

            async with httpx.AsyncClient(timeout=15.0) as client:
                if entry.check_http == "POST":
                    body = {}
                    if entry.check_body:
                        try:
                            body = __import__("json").loads(entry.check_body)
                        except Exception:
                            pass
                    if headers:
                        resp = await client.post(url, headers=headers, json=body, params=params)
                    else:
                        resp = await client.post(url, json=body, params=params)
                else:
                    if headers:
                        resp = await client.get(url, headers=headers, params=params)
                    else:
                        resp = await client.get(url, params=params)

                status_code = resp.status_code

            method = entry.check_method or ""
            if method == "http_402":
                if status_code == 402:
                    return {"name": entry.name, "status": "exhausted", "http_status": 402}
                elif status_code == 401:
                    return {"name": entry.name, "status": "invalid", "http_status": 401}
                elif 200 <= status_code < 300:
                    return {"name": entry.name, "status": "active", "http_status": status_code}
                else:
                    # Non-2xx, non-402 → still might be active (rate limit, bad test query, etc.)
                    return {"name": entry.name, "status": "active", "http_status": status_code,
                            "note": f"Unexpected status {status_code}"}

            elif method == "http_401":
                if status_code == 401:
                    return {"name": entry.name, "status": "invalid", "http_status": 401}
                elif status_code == 403:
                    return {"name": entry.name, "status": "invalid", "http_status": 403}
                elif 200 <= status_code < 300:
                    return {"name": entry.name, "status": "active", "http_status": status_code}
                else:
                    return {"name": entry.name, "status": "active", "http_status": status_code,
                            "note": f"Unexpected status {status_code}"}

            elif method == "http_403":
                if status_code == 403:
                    return {"name": entry.name, "status": "invalid", "http_status": 403}
                elif 200 <= status_code < 300:
                    return {"name": entry.name, "status": "active", "http_status": status_code}
                else:
                    return {"name": entry.name, "status": "active", "http_status": status_code,
                            "note": f"Unexpected status {status_code}"}

            elif method == "http_429":
                if status_code == 429:
                    return {"name": entry.name, "status": "exhausted", "http_status": 429}
                elif 200 <= status_code < 300:
                    return {"name": entry.name, "status": "active", "http_status": status_code}
                else:
                    return {"name": entry.name, "status": "active", "http_status": status_code,
                            "note": f"Unexpected status {status_code}"}

            return {"name": entry.name, "status": "unknown", "note": "No check method"}

        except Exception as e:
            logger.debug("KeyBank check failed for %s: %s", entry.name, str(e)[:100])
            return {"name": entry.name, "status": "unknown", "error": str(e)[:200]}

    def _build_auth_headers(self, entry: KeyEntry) -> dict:
        """Build auth headers for a key check request."""
        auth = entry.check_auth
        if not auth:
            return {}
        if auth == "bearer":
            return {"Authorization": f"Bearer {entry.value}"}
        if auth == "x-subscription-token":
            return {"X-Subscription-Token": entry.value}
        if auth == "x-api-key":
            return {"X-API-KEY": entry.value}
        return {}

    # ── Dynamic registration ───────────────────────────────────────

    def register(self, entry: KeyEntry) -> None:
        """Register or update a key entry dynamically."""
        self._keys[entry.name] = entry

    def update_status(self, name: str, status: str, reason: str = "") -> None:
        """Update status of a key (e.g. mark as exhausted)."""
        entry = self._keys.get(name)
        if entry:
            entry.status = status
            if status == "exhausted":
                entry.exhausted_at = time.time()
            logger.info("KeyBank: %s → %s%s", name, status, f" ({reason})" if reason else "")


# ── Module-Level Singleton ─────────────────────────────────────────────

key_bank = KeyBank()
