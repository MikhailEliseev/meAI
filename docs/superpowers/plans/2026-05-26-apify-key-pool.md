# Apify Key Pool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build ApifyKeyPool service with round-robin rotation, 31-day auto-recovery, and integrate it into ApifyClient for automatic failover on quota errors.

**Architecture:** New `ApifyKeyPool` service reads keys from JSON, rotates via round-robin among active keys, marks exhausted on quota errors, auto-recovers after 31 days. `ApifyClient` loses its singleton + circuit breaker, gains key pool injection with automatic rotation on 402/403.

**Tech Stack:** Python 3.11+, `asyncio`, `json`, stdlib only. No new dependencies.

---

### Task 1: Create apify_keys.json template

**Files:**
- Create: `AIM/data/apify_keys.json`

- [ ] **Step 1: Write the JSON template**

```json
{
  "keys": [
    {
      "token": "apify_api_placeholder_01",
      "status": "active",
      "exhausted_at": null,
      "label": "account-001"
    }
  ]
}
```

Write to `AIM/data/apify_keys.json`:
```bash
cat > AIM/data/apify_keys.json << 'EOF'
{
  "keys": [
    {
      "token": "apify_api_placeholder_01",
      "status": "active",
      "exhausted_at": null,
      "label": "account-001"
    }
  ]
}
EOF
```

- [ ] **Step 2: Verify the file**

```bash
python3 -c "import json; d=json.load(open('AIM/data/apify_keys.json')); print(f'{len(d[\"keys\"])} keys loaded')"
```
Expected: `1 keys loaded`

- [ ] **Step 3: Commit**

```bash
git add AIM/data/apify_keys.json
git commit -m "feat: add apify_keys.json template for key pool storage"
```

---

### Task 2: Write ApifyKeyPool tests (TDD — red phase)

**Files:**
- Create: `AIM/tests/services/test_apify_key_pool.py`

- [ ] **Step 1: Write the test file**

```python
"""Tests for ApifyKeyPool — round-robin, exhaustion, auto-recovery, atomic save."""

import json
import os
import tempfile
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from aim.services.apify_key_pool import ApifyKeyPool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_keys(path: str, keys: list[dict]):
    with open(path, "w") as f:
        json.dump({"keys": keys}, f, indent=2)


def _make_key(token: str, status: str = "active", exhausted_at=None, label: str = ""):
    k = {"token": token, "status": status, "exhausted_at": exhausted_at}
    if label:
        k["label"] = label
    return k


# ---------------------------------------------------------------------------
# Basic round-robin
# ---------------------------------------------------------------------------

class TestRoundRobin:
    def test_three_keys_cycle_in_order(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            _write_keys(f.name, [
                _make_key("key-1", label="acc-1"),
                _make_key("key-2", label="acc-2"),
                _make_key("key-3", label="acc-3"),
            ])
            f.flush()
            pool = ApifyKeyPool(f.name)

        assert pool.get_next_key() == "key-1"
        assert pool.get_next_key() == "key-2"
        assert pool.get_next_key() == "key-3"
        assert pool.get_next_key() == "key-1"

        os.unlink(f.name)

    def test_single_key_always_returns_it(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            _write_keys(f.name, [_make_key("solo")])
            f.flush()
            pool = ApifyKeyPool(f.name)

        assert pool.get_next_key() == "solo"
        assert pool.get_next_key() == "solo"
        assert pool.get_next_key() == "solo"

        os.unlink(f.name)


# ---------------------------------------------------------------------------
# Exhaustion
# ---------------------------------------------------------------------------

class TestExhaustion:
    def test_exhausting_key_removes_it_from_rotation(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            _write_keys(f.name, [
                _make_key("key-a"), _make_key("key-b"), _make_key("key-c"),
            ])
            f.flush()
            pool = ApifyKeyPool(f.name)

        assert pool.get_next_key() == "key-a"
        assert pool.get_next_key() == "key-b"
        pool.mark_exhausted("key-b")

        # только key-a и key-c в ротации
        assert pool.get_next_key() == "key-c"
        assert pool.get_next_key() == "key-a"
        assert pool.get_next_key() == "key-c"

        os.unlink(f.name)

    def test_exhausting_last_key_raises(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            _write_keys(f.name, [_make_key("last-one")])
            f.flush()
            pool = ApifyKeyPool(f.name)

        pool.mark_exhausted("last-one")
        with pytest.raises(RuntimeError, match="no active keys"):
            pool.get_next_key()

        os.unlink(f.name)

    def test_exhaustion_persisted_to_file(self):
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        _write_keys(tmp.name, [_make_key("k1"), _make_key("k2")])
        tmp.flush()
        pool = ApifyKeyPool(tmp.name)
        pool.mark_exhausted("k1")

        # Перезагружаем из файла
        pool2 = ApifyKeyPool(tmp.name)
        assert pool2.get_next_key() == "k2"  # k1 exhausted
        assert pool2.get_next_key() == "k2"  # всё ещё k2

        os.unlink(tmp.name)


# ---------------------------------------------------------------------------
# Auto-recovery
# ---------------------------------------------------------------------------

class TestAutoRecovery:
    def test_recovers_key_after_31_days(self):
        now = datetime.now(timezone.utc)
        exhausted_32_days_ago = (now - timedelta(days=32)).isoformat()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            _write_keys(f.name, [
                _make_key("k1"),
                _make_key("k2", status="exhausted", exhausted_at=exhausted_32_days_ago),
            ])
            f.flush()
            pool = ApifyKeyPool(f.name)

        # k2 должен быть восстановлен
        keys = {pool.get_next_key(), pool.get_next_key()}
        assert keys == {"k1", "k2"}

        os.unlink(f.name)

    def test_does_not_recover_recently_exhausted(self):
        now = datetime.now(timezone.utc)
        exhausted_5_days_ago = (now - timedelta(days=5)).isoformat()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            _write_keys(f.name, [
                _make_key("k1"),
                _make_key("k2", status="exhausted", exhausted_at=exhausted_5_days_ago),
            ])
            f.flush()
            pool = ApifyKeyPool(f.name)

        # k2 всё ещё exhausted
        assert pool.get_next_key() == "k1"
        assert pool.get_next_key() == "k1"

        os.unlink(f.name)


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

class TestStats:
    def test_stats_reflect_exhaustions(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            _write_keys(f.name, [
                _make_key("k1"), _make_key("k2"), _make_key("k3"), _make_key("k4"),
            ])
            f.flush()
            pool = ApifyKeyPool(f.name)

        assert pool.get_stats() == {"total": 4, "active": 4, "exhausted": 0}

        pool.mark_exhausted("k1")
        pool.mark_exhausted("k3")

        assert pool.get_stats() == {"total": 4, "active": 2, "exhausted": 2}

        os.unlink(f.name)


# ---------------------------------------------------------------------------
# File handling
# ---------------------------------------------------------------------------

class TestFileHandling:
    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            ApifyKeyPool("/nonexistent/path/keys.json")

    def test_corrupted_json_raises(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not json {{{")
            f.flush()
            with pytest.raises(json.JSONDecodeError):
                ApifyKeyPool(f.name)
        os.unlink(f.name)
```

- [ ] **Step 2: Run tests — verify they all FAIL**

```bash
cd /Users/mikhaileliseev/Desktop/Dev/meAI && python -m pytest AIM/tests/services/test_apify_key_pool.py -v
```
Expected: All 9 tests FAIL with `ModuleNotFoundError: No module named 'AIM.src.aim.services.apify_key_pool'`

---

### Task 3: Implement ApifyKeyPool (TDD — green phase)

**Files:**
- Create: `AIM/src/aim/services/apify_key_pool.py`

- [ ] **Step 1: Create the module**

```python
"""Apify API key pool with round-robin rotation and 31-day auto-recovery.

Stores keys in JSON, rotates active keys via round-robin, marks exhausted
keys and auto-recovers them after 31 days (Apify free tier reset).
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

_RECOVERY_DAYS = 31
_TMP_STALE_SECONDS = 60


class ApifyKeyPool:
    """Round-robin key pool with automatic exhaustion tracking and recovery."""

    def __init__(self, keys_file: str):
        if not os.path.exists(keys_file):
            raise FileNotFoundError(f"Apify keys file not found: {keys_file}")
        self._keys_file = keys_file
        self._lock = asyncio.Lock()
        self._keys: list[dict] = []
        self._active_indices: list[int] = []
        self._cursor = 0
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_next_key(self) -> str:
        """Return the next active token (round-robin). Raises RuntimeError if pool dry."""
        async with self._lock:
            if not self._active_indices:
                raise RuntimeError("All Apify keys exhausted — no active keys remaining")
            idx = self._active_indices[self._cursor % len(self._active_indices)]
            self._cursor = (self._cursor + 1) % len(self._active_indices)
            return self._keys[idx]["token"]

    async def mark_exhausted(self, token: str):
        """Record a key as exhausted (called on quota error). Persists to file."""
        async with self._lock:
            self._mark_exhausted_locked(token)

    def get_stats(self) -> dict:
        total = len(self._keys)
        active = sum(1 for k in self._keys if k["status"] == "active")
        return {"total": total, "active": active, "exhausted": total - active}

    @property
    def active_count(self) -> int:
        return len(self._active_indices)

    # ------------------------------------------------------------------
    # Internal — load / save
    # ------------------------------------------------------------------

    def _load(self):
        with open(self._keys_file, "r") as f:
            data = json.load(f)

        self._cleanup_stale_tmp()
        self._keys = data.get("keys", [])
        self._auto_recover()
        self._rebuild_indices()

        logger.info(
            "ApifyKeyPool loaded: %d total, %d active, %d exhausted",
            len(self._keys), len(self._active_indices),
            len(self._keys) - len(self._active_indices),
        )

    def _save(self):
        """Atomic write: tmp → replace. Keeps .bak for safety."""
        tmp_path = self._keys_file + ".tmp"
        bak_path = self._keys_file + ".bak"

        with open(tmp_path, "w") as f:
            json.dump({"keys": self._keys}, f, indent=2, ensure_ascii=False)

        if os.path.exists(self._keys_file):
            os.replace(self._keys_file, bak_path)
        os.replace(tmp_path, self._keys_file)

    def _cleanup_stale_tmp(self):
        tmp_path = self._keys_file + ".tmp"
        if os.path.exists(tmp_path):
            try:
                if time.time() - os.path.getmtime(tmp_path) > _TMP_STALE_SECONDS:
                    os.remove(tmp_path)
                    logger.warning("Removed stale tmp file: %s", tmp_path)
            except OSError:
                pass

    # ------------------------------------------------------------------
    # Internal — recovery
    # ------------------------------------------------------------------

    def _auto_recover(self):
        """Reactivate keys exhausted >= 31 days ago."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=_RECOVERY_DAYS)
        recovered = 0

        for key in self._keys:
            if key["status"] != "exhausted":
                continue
            exhausted_at = key.get("exhausted_at")
            if exhausted_at:
                try:
                    if datetime.fromisoformat(exhausted_at) <= cutoff:
                        key["status"] = "active"
                        key["exhausted_at"] = None
                        recovered += 1
                except (ValueError, TypeError):
                    key["status"] = "active"
                    key["exhausted_at"] = None
                    recovered += 1
            else:
                # No date — recover it
                key["status"] = "active"
                recovered += 1

        if recovered:
            logger.info("Auto-recovered %d keys (>= %d days)", recovered, _RECOVERY_DAYS)
            self._save()

    # ------------------------------------------------------------------
    # Internal — indices + exhaustion
    # ------------------------------------------------------------------

    def _rebuild_indices(self):
        self._active_indices = [
            i for i, k in enumerate(self._keys) if k["status"] == "active"
        ]
        self._cursor = 0

    def _mark_exhausted_locked(self, token: str):
        """Mark key exhausted and persist. Caller must hold self._lock."""
        for key in self._keys:
            if key["token"] == token and key["status"] == "active":
                key["status"] = "exhausted"
                key["exhausted_at"] = datetime.now(timezone.utc).isoformat()
                label = key.get("label", token[:20] + "...")
                self._save()
                self._rebuild_indices()
                logger.warning(
                    "Apify key exhausted: %s (remaining active: %d)",
                    label, len(self._active_indices),
                )
                return

        logger.debug("Token not found or already exhausted: %s...", token[:20])
```

Write all content above to `AIM/src/aim/services/apify_key_pool.py`:
```bash
cat > AIM/src/aim/services/apify_key_pool.py << 'PYEOF'
<content from spec>
PYEOF
```

Actually use the Write tool for the whole file since it's ~130 lines.

- [ ] **Step 2: Run tests — verify they PASS (except async sync issues)**

```bash
cd /Users/mikhaileliseev/Desktop/Dev/meAI && python -m pytest AIM/tests/services/test_apify_key_pool.py -v
```
Expected: Tests called `get_next_key()` synchronously — will fail because method is now async. We'll fix tests in next step.

- [ ] **Step 3: Fix tests to use `await` on async methods**

Update `AIM/tests/services/test_apify_key_pool.py` — change all calls:
- `pool.get_next_key()` → `await pool.get_next_key()`
- `pool.mark_exhausted(...)` → `await pool.mark_exhausted(...)`
- All test classes inherit from nothing (plain classes, functions are `async def`)

Mark each test function as `async def` and add `@pytest.mark.asyncio` decorator.

Run:
```bash
cd /Users/mikhaileliseev/Desktop/Dev/meAI && python -m pytest AIM/tests/services/test_apify_key_pool.py -v
```
Expected: All 9 tests PASS

- [ ] **Step 4: Commit**

```bash
git add AIM/src/aim/services/apify_key_pool.py AIM/tests/services/test_apify_key_pool.py
git commit -m "feat: ApifyKeyPool with round-robin, exhaustion, 31-day auto-recovery"
```

---

### Task 4: Refactor ApifyClient to use key pool

**Files:**
- Modify: `AIM/src/aim/services/apify_client.py`

- [ ] **Step 1: Rewrite ApifyClient**

Remove: circuit breaker, `get_apify_client()` singleton, env-var token loading.  
Add: `ApifyKeyPool` injection, auto-rotation on quota errors.

Replace entire file content:

```python
"""Shared Apify client with key-pool-based resilience.

Uses ApifyKeyPool for automatic key rotation on quota exhaustion.
"""

import asyncio
import logging
from datetime import timedelta
from typing import Optional

from apify_client import ApifyClientAsync
from apify_client.errors import ApifyApiError

from .apify_key_pool import ApifyKeyPool

logger = logging.getLogger(__name__)

_DEFAULT_RUN_TIMEOUT = timedelta(minutes=3)
_DEFAULT_MEMORY_MB = 2048
_RETRY_MAX = 3
_RETRY_BASE_DELAY = 2.0

_QUOTA_KEYWORDS = ("quota", "exceeded", "insufficient", "balance", "limit")


class ApifyClient:
    """Async Apify client that auto-rotates Apify keys on quota errors."""

    def __init__(self, key_pool: ApifyKeyPool):
        self._key_pool = key_pool
        self._current_token: Optional[str] = None
        self._client: Optional[ApifyClientAsync] = None

    async def _ensure_client(self):
        if self._client is None:
            self._current_token = await self._key_pool.get_next_key()
            self._client = ApifyClientAsync(token=self._current_token)

    async def call_actor(
        self,
        actor_id: str,
        run_input: dict,
        run_timeout: timedelta = _DEFAULT_RUN_TIMEOUT,
        memory_mbytes: int = _DEFAULT_MEMORY_MB,
        max_retries: int = _RETRY_MAX,
    ):
        await self._ensure_client()
        last_error: Optional[Exception] = None

        for attempt in range(max_retries + 1):
            try:
                run = await self._client.actor(actor_id).call(
                    run_input=run_input,
                    run_timeout=run_timeout,
                    memory_mbytes=memory_mbytes,
                )
                return run

            except ApifyApiError as e:
                if self._is_quota_error(e):
                    logger.warning("Apify quota error, rotating key (attempt %d)", attempt + 1)
                    last_error = e
                    if await self._rotate_key():
                        continue
                    raise RuntimeError("All Apify keys exhausted")

                if e.status_code == 429:
                    delay = _RETRY_BASE_DELAY * (2 ** attempt)
                    logger.warning("Apify 429, attempt %d/%d, waiting %.1fs", attempt + 1, max_retries + 1, delay)
                    last_error = e
                    if attempt < max_retries:
                        await asyncio.sleep(delay)
                        continue
                else:
                    logger.error("Apify API error (status=%s): %s", e.status_code, e)
                    raise

            except Exception as e:
                msg = str(e).lower()
                if any(kw in msg for kw in ("timeout", "connection", "reset", "503", "502")):
                    if attempt < max_retries:
                        delay = _RETRY_BASE_DELAY * (2 ** attempt)
                        logger.warning("Apify transient '%s', attempt %d/%d, waiting %.1fs", e, attempt + 1, max_retries + 1, delay)
                        last_error = e
                        await asyncio.sleep(delay)
                        continue
                raise

        raise last_error or RuntimeError("Apify actor call failed after retries")

    async def get_dataset_items(self, dataset_id: str) -> list[dict]:
        await self._ensure_client()
        dataset = self._client.dataset(dataset_id)
        return [item async for item in dataset.iterate_items()]

    async def close(self):
        pass

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _is_quota_error(self, error: ApifyApiError) -> bool:
        if error.status_code in (402, 403):
            return True
        return any(kw in str(error).lower() for kw in _QUOTA_KEYWORDS)

    async def _rotate_key(self) -> bool:
        """Mark current key exhausted, switch to next. Returns False if pool dry."""
        try:
            await self._key_pool.mark_exhausted(self._current_token)
            self._current_token = await self._key_pool.get_next_key()
            self._client = ApifyClientAsync(token=self._current_token)
            logger.info("Rotated Apify key (active: %d)", self._key_pool.active_count)
            return True
        except RuntimeError:
            logger.error("ApifyKeyPool dry — no active keys left")
            return False
```

Write to `AIM/src/aim/services/apify_client.py` using Write tool.

- [ ] **Step 2: Verify the module imports**

```bash
cd /Users/mikhaileliseev/Desktop/Dev/meAI && python -c "from aim.services.apify_client import ApifyClient; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add AIM/src/aim/services/apify_client.py
git commit -m "refactor(apify): replace singleton + circuit breaker with key pool rotation"
```

---

### Task 5: Update apify_google_maps.py

**Files:**
- Modify: `AIM/src/aim/services/apify_google_maps.py`

- [ ] **Step 1: Update the import and client creation**

The file imports `get_apify_client` which no longer exists. Replace the singleton usage with requiring a client to be passed in.

Changes in `apify_google_maps.py`:

Line 13: Remove `get_apify_client` import:
```python
# Before
from .apify_client import ApifyClient, get_apify_client
# After
from .apify_client import ApifyClient
```

Lines 27-40: Remove default `None` client and `get_apify_client()` fallback:
```python
# Before
async def discover_competitors_google_maps(
    specialization: str,
    city: str,
    count: int = _DEFAULT_COUNT,
    client: Optional[ApifyClient] = None,
) -> list[CompanyProfile]:
    ...
    apify = client or get_apify_client()

# After
async def discover_competitors_google_maps(
    specialization: str,
    city: str,
    count: int = _DEFAULT_COUNT,
    client: ApifyClient | None = None,
) -> list[CompanyProfile]:
    ...
    if client is None:
        raise ValueError("ApifyClient is required — no default singleton available")
    apify = client
```

Also remove `Optional` from typing imports if no longer used.

- [ ] **Step 2: Check for other callers that pass no client**

```bash
grep -rn "discover_competitors_google_maps" AIM/src/ --include="*.py"
```

Update any caller that doesn't pass `client=` to create an ApifyClient with the key pool.

- [ ] **Step 3: Commit**

```bash
git add AIM/src/aim/services/apify_google_maps.py
git commit -m "refactor(apify): require explicit ApifyClient in google maps discovery"
```

---

### Task 6: Create ApifyClient factory / app-level wiring

**Files:**
- Modify: `AIM/src/aim/services/__init__.py` (add factory functions)
- Modify: `AIM/src/aim/services/competitor_matcher.py` (pass client to discovery)

- [ ] **Step 1: Add factory functions to services/__init__.py**

Current `AIM/src/aim/services/__init__.py`:
```python
"""Project creation orchestration service."""
from .project_creator import ProjectCreator
__all__ = ["ProjectCreator"]
```

Append these lines after the existing content:

```python
import os
from pathlib import Path

from .apify_key_pool import ApifyKeyPool
from .apify_client import ApifyClient

_apify_pool: ApifyKeyPool | None = None
_apify_client: ApifyClient | None = None

def get_apify_key_pool() -> ApifyKeyPool:
    global _apify_pool
    if _apify_pool is None:
        default_path = Path(__file__).parent.parent.parent.parent / "data" / "apify_keys.json"
        keys_file = os.environ.get("APIFY_KEYS_FILE", str(default_path))
        _apify_pool = ApifyKeyPool(keys_file)
    return _apify_pool

def get_apify_client() -> ApifyClient:
    global _apify_client
    if _apify_client is None:
        _apify_client = ApifyClient(key_pool=get_apify_key_pool())
    return _apify_client
```

Update `__all__`:
```python
__all__ = ["ProjectCreator", "get_apify_key_pool", "get_apify_client"]
```

- [ ] **Step 2: Update competitor_matcher.py to pass client**

The function `discover_competitors_google_maps` is called inside `CompetitorMatcher._discover()` around line 212. Pass the client:

Import at top of `competitor_matcher.py`:
```python
from . import get_apify_client
```

In the `_discover` method, where `discover_competitors_google_maps` is called:
```python
profiles = await discover_competitors_google_maps(
    specialization=specialization,
    city=city,
    count=count,
    client=get_apify_client(),
)
```

- [ ] **Step 4: Commit**

```bash
git add AIM/src/aim/services/
git commit -m "feat: add ApifyClient factory with key pool, wire into competitor_matcher"
```

---

### Task 7: Create key import script

**Files:**
- Create: `scripts/import_apify_keys.py`

- [ ] **Step 1: Write the import script**

```python
#!/usr/bin/env python3
"""Import Apify API keys from a text file into the JSON key pool.

Input format: one token per line, # comments supported.

Usage:
    python scripts/import_apify_keys.py --input keys.txt
    python scripts/import_apify_keys.py --input keys.txt --output AIM/data/apify_keys.json --label-prefix acc
"""

import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Import Apify API keys into key pool JSON")
    parser.add_argument("--input", required=True, help="Text file with one token per line")
    parser.add_argument("--output", default="AIM/data/apify_keys.json", help="Output JSON file")
    parser.add_argument("--label-prefix", default="account", help="Label prefix (e.g. 'account' → 'account-001')")
    parser.add_argument("--merge", action="store_true", help="Merge into existing file instead of overwriting")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Read tokens
    tokens = []
    with open(input_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            tokens.append(line)

    if not tokens:
        print("Error: no tokens found in input file", file=sys.stderr)
        sys.exit(1)

    # Build keys list
    new_keys = []
    for i, token in enumerate(tokens, start=1):
        new_keys.append({
            "token": token,
            "status": "active",
            "exhausted_at": None,
            "label": f"{args.label_prefix}-{i:03d}",
        })

    if args.merge and output_path.exists():
        with open(output_path) as f:
            existing = json.load(f)
        existing.setdefault("keys", []).extend(new_keys)
        data = existing
    else:
        data = {"keys": new_keys}

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Imported {len(tokens)} keys → {output_path}")
    print(f"  Total keys in file: {len(data['keys'])}")


if __name__ == "__main__":
    main()
```

Write to `scripts/import_apify_keys.py`.

- [ ] **Step 2: Test the script**

```bash
cd /Users/mikhaileliseev/Desktop/Dev/meAI

# Create test input
echo "# Test keys" > /tmp/test_keys.txt
echo "apify_api_test_001" >> /tmp/test_keys.txt
echo "apify_api_test_002" >> /tmp/test_keys.txt
echo "" >> /tmp/test_keys.txt
echo "apify_api_test_003" >> /tmp/test_keys.txt

# Run import to temp output
python scripts/import_apify_keys.py --input /tmp/test_keys.txt --output /tmp/test_apify_keys.json

# Verify
python -c "
import json
d = json.load(open('/tmp/test_apify_keys.json'))
assert len(d['keys']) == 3
assert d['keys'][0]['token'] == 'apify_api_test_001'
assert d['keys'][0]['label'] == 'account-001'
assert d['keys'][2]['token'] == 'apify_api_test_003'
print('OK — 3 keys imported')
"

rm /tmp/test_keys.txt /tmp/test_apify_keys.json
```
Expected: `OK — 3 keys imported`

- [ ] **Step 3: Commit**

```bash
git add scripts/import_apify_keys.py
git commit -m "feat: add Apify key import script (TXT → JSON)"
```

---

### Task 8: Update .env.example

**Files:**
- Modify: `AIM/.env.example`

- [ ] **Step 1: Add APIFY_KEYS_FILE variable, deprecate APIFY_API_TOKEN**

Change lines 97-103 in `AIM/.env.example`:

```bash
# Before (lines ~97-103):
# Apify Google Maps Scraper Configuration
# ...
APIFY_API_TOKEN=your_apify_api_token_here

# After:
# Apify Key Pool Configuration
# Path to JSON file containing all Apify API tokens (managed by key pool)
# Import tokens: python scripts/import_apify_keys.py --input keys.txt
APIFY_KEYS_FILE=AIM/data/apify_keys.json
```

- [ ] **Step 2: Commit**

```bash
git add AIM/.env.example
git commit -m "docs: update .env.example for Apify key pool (APIFY_KEYS_FILE)"
```

---

### Task 9: Integration test — end-to-end with real keys file

**Files:**
- Create: `AIM/tests/services/test_apify_client_with_pool.py`

- [ ] **Step 1: Write integration test for ApifyClient + KeyPool**

```python
"""Integration tests for ApifyClient with ApifyKeyPool."""

import json
import os
import tempfile

import pytest
from aim.services.apify_key_pool import ApifyKeyPool
from aim.services.apify_client import ApifyClient


@pytest.mark.asyncio
async def test_client_initializes_with_first_key():
    """ApifyClient gets its first token from the pool on init."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"keys": [
            {"token": "apify_api_test_key_001", "status": "active", "exhausted_at": None, "label": "test-1"},
        ]}, f)
        f.flush()
        pool = ApifyKeyPool(f.name)
        client = ApifyClient(key_pool=pool)
        await client._ensure_client()
        assert client._current_token == "apify_api_test_key_001"
    os.unlink(f.name)


@pytest.mark.asyncio
async def test_rotate_key_switches_to_next():
    """After exhausting a key, client switches to the next active one."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"keys": [
            {"token": "k1", "status": "active", "exhausted_at": None},
            {"token": "k2", "status": "active", "exhausted_at": None},
        ]}, f)
        f.flush()
        pool = ApifyKeyPool(f.name)
        client = ApifyClient(key_pool=pool)

        # Simulate exhaustion + rotation
        client._current_token = "k1"
        rotated = await client._rotate_key()
        assert rotated is True
        assert client._current_token == "k2"

        # k1 is now exhausted in the pool
        stats = pool.get_stats()
        assert stats["active"] == 1
        assert stats["exhausted"] == 1
    os.unlink(f.name)


@pytest.mark.asyncio
async def test_rotate_key_fails_when_pool_dry():
    """When all keys exhausted, rotation returns False."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"keys": [
            {"token": "only-key", "status": "active", "exhausted_at": None},
        ]}, f)
        f.flush()
        pool = ApifyKeyPool(f.name)
        client = ApifyClient(key_pool=pool)
        client._current_token = "only-key"

        rotated = await client._rotate_key()
        assert rotated is False
    os.unlink(f.name)
```

Write to `AIM/tests/services/test_apify_client_with_pool.py`.

- [ ] **Step 2: Run integration tests**

```bash
cd /Users/mikhaileliseev/Desktop/Dev/meAI && python -m pytest AIM/tests/services/test_apify_client_with_pool.py -v
```
Expected: 3 PASS

- [ ] **Step 3: Commit**

```bash
git add AIM/tests/services/test_apify_client_with_pool.py
git commit -m "test: integration tests for ApifyClient + ApifyKeyPool"
```

---

### Task 10: Final verification — all tests pass, imports clean

- [ ] **Step 1: Run all apify-related tests**

```bash
cd /Users/mikhaileliseev/Desktop/Dev/meAI && python -m pytest AIM/tests/services/test_apify_key_pool.py AIM/tests/services/test_apify_client_with_pool.py -v
```
Expected: 12 PASS (9 from key_pool + 3 from client)

- [ ] **Step 2: Verify all imports**

```bash
cd /Users/mikhaileliseev/Desktop/Dev/meAI && python -c "
from aim.services.apify_key_pool import ApifyKeyPool
from aim.services.apify_client import ApifyClient
print('All imports OK')
"
```

- [ ] **Step 3: Commit any remaining cleanup**

```bash
git status
# If any uncommitted changes remain, commit them
```
