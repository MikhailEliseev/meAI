"""Project creation orchestration service."""

import os
from pathlib import Path

from .project_creator import ProjectCreator
from .apify_key_pool import ApifyKeyPool
from .apify_client import ApifyClient

__all__ = ["ProjectCreator", "get_apify_key_pool", "get_apify_client"]


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
