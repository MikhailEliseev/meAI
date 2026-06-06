"""
Monkey-patch: inject Firecrawl key bank into hermes-agent provider.

Replaces _get_direct_firecrawl_config() with a bank-aware version
that falls back to the 12-key rotation bank when the env key is
exhausted or unavailable. Also wraps search() and extract() to auto-rotate
on 402/credit-exhaustion errors.

Applied at startup via hermes_cli/main.py before any web search.
"""
import json
import logging
import os
import threading
from pathlib import Path
from functools import wraps

logger = logging.getLogger("firecrawl_provider_bank")

_KEY_BANK_PATH = "/root/.hermes/keys/firecrawl_keys.json"
_lock = threading.Lock()
_dead_keys = set()
_current_key: str | None = None
_patch_applied = False


def _load_active_keys():
    """Load active, non-exhausted keys from the Firecrawl key bank."""
    try:
        bank = json.loads(Path(_KEY_BANK_PATH).read_text())
        return [
            k["token"]
            for k in bank["keys"]
            if k.get("status") == "active" and k["token"] not in _dead_keys
        ]
    except Exception as e:
        logger.warning("firecrawl_provider_bank: cannot load bank: %s", e)
        return []


def _get_patched_firecrawl_config():
    """Bank-aware replacement for _get_direct_firecrawl_config().

    Priority:
      1. FIRECRAWL_API_KEY env var (if not marked dead)
      2. First available active key from rotation bank
      3. Env key as last resort (even if dead — let caller handle 402)
    """
    global _current_key

    env_key = os.getenv("FIRECRAWL_API_KEY", "").strip()
    api_url = os.getenv("FIRECRAWL_API_URL", "").strip().rstrip("/")

    # Try env key first
    if env_key and env_key not in _dead_keys:
        kwargs = {}
        if env_key:
            kwargs["api_key"] = env_key
        if api_url:
            kwargs["api_url"] = api_url
        _current_key = env_key
        return kwargs, ("direct", api_url or None, env_key)

    # Fall back to key bank
    bank_keys = _load_active_keys()
    if bank_keys:
        key = bank_keys[0]
        kwargs = {"api_key": key}
        if api_url:
            kwargs["api_url"] = api_url
        _current_key = key
        logger.info("firecrawl_provider_bank: using bank key %s (env key unavailable/dead)", key[:20])
        return kwargs, ("direct", api_url or None, key)

    # Last resort: return env key even if dead
    if env_key or api_url:
        kwargs = {}
        if env_key:
            kwargs["api_key"] = env_key
        if api_url:
            kwargs["api_url"] = api_url
        _current_key = env_key
        return kwargs, ("direct", api_url or None, env_key)

    return None


def mark_key_dead(key):
    """Mark a key as dead and force client re-creation on next call."""
    global _current_key
    with _lock:
        _dead_keys.add(key)
        logger.warning(
            "firecrawl_provider_bank: key %s marked dead (now %d dead keys)",
            key[:20], len(_dead_keys),
        )


def _is_credit_exhausted(error_msg: str) -> bool:
    """Detect credit exhaustion in Firecrawl error messages."""
    msg_lower = error_msg.lower()
    return any(phrase in msg_lower for phrase in [
        "402",
        "payment required",
        "insufficient credits",
        "insufficient_credits",
        "no credits",
        "credit",
    ])


def _bust_client_cache():
    """Force recreation of Firecrawl client with next available key."""
    import tools.web_tools as _wt
    _wt._firecrawl_client = None
    _wt._firecrawl_client_config = None
    logger.info("firecrawl_provider_bank: client cache busted for key rotation")


def _wrap_search_with_rotation():
    """Wrap FirecrawlWebSearchProvider.search() with auto-rotation on 402."""
    import plugins.web.firecrawl.provider as provider_mod

    original_search = provider_mod.FirecrawlWebSearchProvider.search

    @wraps(original_search)
    def search_with_rotation(self, query: str, limit: int = 5):
        result = original_search(self, query, limit)

        # Check for credit exhaustion in failed search
        if not result.get("success") and result.get("error"):
            error_msg = result["error"]
            if _is_credit_exhausted(error_msg):
                key_to_mark = _current_key
                if key_to_mark:
                    mark_key_dead(key_to_mark)
                    _bust_client_cache()

                    # Retry with next key
                    logger.info(
                        "firecrawl_provider_bank: retrying search with next key after 402"
                    )
                    try:
                        retry_result = original_search(self, query, limit)
                        if retry_result.get("success"):
                            logger.info(
                                "firecrawl_provider_bank: search retry OK with rotated key"
                            )
                            return retry_result
                    except Exception:
                        logger.warning(
                            "firecrawl_provider_bank: search retry also failed"
                        )

        return result

    provider_mod.FirecrawlWebSearchProvider.search = search_with_rotation
    logger.info("firecrawl_provider_bank: FirecrawlWebSearchProvider.search() wrapped with 402 auto-rotation")


def _wrap_extract_with_rotation():
    """Wrap FirecrawlWebSearchProvider.extract() with auto-rotation on 402.

    extract() is async and returns List[Dict] — detects credit exhaustion
    across all per-URL results and retries failed URLs with next key.
    """
    import plugins.web.firecrawl.provider as provider_mod

    original_extract = provider_mod.FirecrawlWebSearchProvider.extract

    @wraps(original_extract)
    async def extract_with_rotation(self, urls, **kwargs):
        result = await original_extract(self, urls, **kwargs)

        # Check if ANY URL failed with credit exhaustion
        has_credit_error = False
        for item in result:
            error = item.get("error", "")
            if _is_credit_exhausted(str(error)):
                has_credit_error = True
                break

        if has_credit_error:
            key_to_mark = _current_key
            if key_to_mark:
                mark_key_dead(key_to_mark)
                _bust_client_cache()

                # Retry ALL URLs with next key
                logger.info(
                    "firecrawl_provider_bank: retrying extract with next key after 402"
                )
                try:
                    retry_result = await original_extract(self, urls, **kwargs)
                    retry_has_error = any(
                        _is_credit_exhausted(str(item.get("error", "")))
                        for item in retry_result
                    )
                    if not retry_has_error:
                        logger.info(
                            "firecrawl_provider_bank: extract retry OK with rotated key"
                        )
                        return retry_result
                except Exception:
                    logger.warning(
                        "firecrawl_provider_bank: extract retry also failed"
                    )

        return result

    provider_mod.FirecrawlWebSearchProvider.extract = extract_with_rotation
    logger.info("firecrawl_provider_bank: FirecrawlWebSearchProvider.extract() wrapped with 402 auto-rotation")


def apply():
    """Apply the monkey-patch to the Firecrawl provider module."""
    global _patch_applied

    if _patch_applied:
        logger.info("firecrawl_provider_bank: already applied, skipping")
        return

    import plugins.web.firecrawl.provider as provider_mod

    # Replace the config function with bank-aware version
    provider_mod._get_direct_firecrawl_config = _get_patched_firecrawl_config

    # Bust the module-level cache in tools.web_tools so the next call
    # re-evaluates _get_direct_firecrawl_config (now our patched version)
    _bust_client_cache()

    # Wrap search and extract with 402 auto-rotation
    _wrap_search_with_rotation()
    _wrap_extract_with_rotation()

    _patch_applied = True

    # Use print for startup visibility — logging not configured yet
    bank_keys = _load_active_keys()
    print(
        f"[firecrawl_provider_bank] PATCH APPLIED: key bank ({len(bank_keys)} keys) + 402 rotation active. "
        f"env_key={'set' if os.getenv('FIRECRAWL_API_KEY', '').strip() else 'not set'}",
        flush=True,
    )
