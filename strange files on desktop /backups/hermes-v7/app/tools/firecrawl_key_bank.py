"""FireCrawl API key bank with round-robin rotation and exhaustion tracking.

Shared module used by both:
- firecrawl_web.py (Hermes tools: firecrawl_scrape, firecrawl_search, etc.)
- firecrawl_provider_bank.py (monkey-patch for hermes-agent internal provider)

Loads keys from FIRECRAWL_KEYS_FILE (default: /opt/data/firecrawl_keys.json).
Falls back to FIRECRAWL_API_KEY env var if no bank file found.

Exhaustion types:
- "insufficient_credits" — account has 0 credits. Recovers at start of next month (billing cycle).
- "rate_limited" — temporary 429/402 from rate limiting. Recovers after RECOVERY_MINUTES.
"""

import json
import logging
import os
import threading
import time
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("firecrawl_key_bank")

_RECOVERY_MINUTES = 30  # For rate-limited keys
_MONTHLY_RECOVERY_DAY = 1  # Day of month when credits refresh (1 = first day)

_lock = threading.Lock()
_keys: list[dict] = []
_active_indices: list[int] = []
_cursor = 0
_bank_file: str | None = None
_last_call = 0.0
_MIN_INTERVAL = 1.2  # seconds between Firecrawl API calls (account-level rate limit)


def init(bank_file: str | None = None):
    """Initialize the key bank. Call once at startup."""
    global _bank_file, _keys, _active_indices, _cursor

    if bank_file is None:
        bank_file = os.environ.get(
            "FIRECRAWL_KEYS_FILE",
            "/opt/data/firecrawl_keys.json",
        )

    _bank_file = bank_file

    if os.path.exists(bank_file):
        _load(bank_file)
        logger.info(
            "FirecrawlKeyBank: loaded %d keys (%d active) from %s",
            len(_keys), len(_active_indices), bank_file,
        )
    else:
        logger.info(
            "FirecrawlKeyBank: no bank file at %s — falling back to FIRECRAWL_API_KEY env var",
            bank_file,
        )


def get_next_key() -> str:
    """Return next active key. Falls back to env var. Raises RuntimeError if nothing available."""
    global _cursor, _last_call

    with _lock:
        # Rate limit: ensure minimum interval between Firecrawl API calls.
        # Tools run in ThreadPoolExecutor, so time.sleep() is safe.
        now = time.time()
        gap = _MIN_INTERVAL - (now - _last_call)
        if gap > 0:
            time.sleep(gap)
        _last_call = time.time()

        # Auto-recover exhausted keys
        _auto_recover()

        if _active_indices:
            idx = _active_indices[_cursor % len(_active_indices)]
            _cursor = (_cursor + 1) % len(_active_indices)
            return _keys[idx]["token"]

    # Fallback: env var
    env_key = os.environ.get("FIRECRAWL_API_KEY", "").strip()
    if env_key:
        return env_key

    raise RuntimeError("No FireCrawl keys available — bank empty and FIRECRAWL_API_KEY not set")


def mark_exhausted(token: str, reason: str = "rate_limited"):
    """Mark a key as exhausted.

    Args:
        token: The API key token.
        reason: "insufficient_credits" (monthly recovery) or
                "rate_limited" (temporary, auto-recover after RECOVERY_MINUTES).
    """
    with _lock:
        for k in _keys:
            if k["token"] == token and k["status"] == "active":
                k["status"] = "exhausted"
                k["exhausted_at"] = time.time()
                k["exhaust_reason"] = reason
                # Store exhaustion date for monthly recovery
                if reason == "insufficient_credits":
                    now = datetime.now()
                    k["exhausted_year"] = now.year
                    k["exhausted_month"] = now.month
                _rebuild_indices()
                _save()
                logger.warning(
                    "FireCrawlKeyBank: key %s exhausted [%s] (%d active remaining)",
                    k.get("label", token[:20]), reason, len(_active_indices),
                )
                return

    logger.debug("FireCrawlKeyBank: token not found or already exhausted: %s...", token[:20])


def active_count() -> int:
    return len(_active_indices)


def get_key_with_fallback() -> str:
    """Return next active key from bank, falling back to FIRECRAWL_API_KEY env var.

    Safe to call from any tool — raises RuntimeError only when bank is empty
    AND env var is not set.
    """
    try:
        return get_next_key()
    except RuntimeError:
        env_key = os.environ.get("FIRECRAWL_API_KEY", "").strip()
        if env_key:
            return env_key
        raise RuntimeError("No FireCrawl keys available — bank empty and FIRECRAWL_API_KEY not set")


def is_credit_exhausted(error_msg: str) -> bool:
    """Check if error message indicates credit/rate-limit exhaustion."""
    return classify_exhaustion(error_msg) is not None


def classify_exhaustion(error_msg: str) -> str | None:
    """Classify exhaustion type from error message.

    Returns:
        "insufficient_credits" — account has 0 credits, recovers monthly
        "rate_limited" — temporary rate limit, recover after RECOVERY_MINUTES
        None — not an exhaustion error
    """
    msg = error_msg.lower()
    # Monthly recovery: account has no credits (billing cycle refresh)
    if any(p in msg for p in ["insufficient credits", "insufficient_credits",
                                 "no credits", "credit limit reached",
                                 "account credits", "upgrade your plan"]):
        return "insufficient_credits"
    # Temporary: rate limiting
    if any(p in msg for p in ["402", "payment required", "rate limit",
                                 "too many requests", "429"]):
        return "rate_limited"
    return None


def _load(path: str):
    global _keys, _active_indices, _cursor
    data = json.loads(Path(path).read_text())
    _keys = data["keys"]
    _auto_recover()
    _rebuild_indices()
    _cursor = 0


def _save():
    if not _bank_file:
        return
    try:
        tmp = _bank_file + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"keys": _keys}, f, indent=2, ensure_ascii=False)
        os.replace(tmp, _bank_file)
    except Exception as e:
        logger.warning("FireCrawlKeyBank: save failed: %s", e)


def _rebuild_indices():
    global _active_indices
    _active_indices = [i for i, k in enumerate(_keys) if k["status"] == "active"]


def _auto_recover():
    """Reactivate exhausted keys based on recovery rules.

    Recovery logic:
    - rate_limited: recover after RECOVERY_MINUTES (30 min)
    - insufficient_credits: recover at start of next billing month
    """
    now = time.time()
    now_dt = datetime.now()
    cutoff_rate_limited = now - (_RECOVERY_MINUTES * 60)

    recovered_rate = 0
    recovered_credits = 0

    for k in _keys:
        if k["status"] != "exhausted":
            continue

        reason = k.get("exhaust_reason")
        exhausted_at = k.get("exhausted_at") or 0

        # Rate-limited keys: recover after 30 minutes
        if reason == "rate_limited":
            try:
                if exhausted_at <= cutoff_rate_limited:
                    k["status"] = "active"
                    k["exhausted_at"] = None
                    k.pop("exhaust_reason", None)
                    recovered_rate += 1
            except (TypeError, ValueError):
                k["status"] = "active"
                k["exhausted_at"] = None
                k.pop("exhaust_reason", None)
                recovered_rate += 1

        # Credit-exhausted keys: recover if new billing month started
        elif reason == "insufficient_credits":
            exhausted_year = k.get("exhausted_year")
            exhausted_month = k.get("exhausted_month")

            if exhausted_year and exhausted_month:
                # Check if we're in a new month after exhaustion
                month_changed = (
                    (now_dt.year > exhausted_year) or
                    (now_dt.year == exhausted_year and now_dt.month > exhausted_month)
                )

                if month_changed:
                    k["status"] = "active"
                    k["exhausted_at"] = None
                    k.pop("exhaust_reason", None)
                    k.pop("exhausted_year", None)
                    k.pop("exhausted_month", None)
                    recovered_credits += 1
                    logger.info(
                        "FireCrawlKeyBank: recovered key %s (new billing month: %d-%02d)",
                        k.get("label", "?"), now_dt.year, now_dt.month,
                    )

    if recovered_rate or recovered_credits:
        logger.info(
            "FireCrawlKeyBank: auto-recovered %d rate-limited + %d credit-refreshed keys",
            recovered_rate, recovered_credits,
        )
        _rebuild_indices()
