"""Integration tests for ApifyClient with ApifyKeyPool."""

import json
import os
import tempfile

import pytest
from aim.services.apify_key_pool import ApifyKeyPool
from aim.services.apify_client import ApifyClient


def _keys_file(tokens: list[str]) -> str:
    """Create a temp JSON with active keys and return path."""
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    keys = [
        {"token": t, "status": "active", "exhausted_at": None, "label": f"test-{i}"}
        for i, t in enumerate(tokens, 1)
    ]
    json.dump({"keys": keys}, tmp)
    tmp.close()
    return tmp.name


@pytest.mark.asyncio
async def test_client_initializes_with_first_key():
    """ApifyClient gets its first token from the pool on _ensure_client."""
    path = _keys_file(["apify_api_test_key_001"])
    try:
        pool = ApifyKeyPool(path)
        client = ApifyClient(key_pool=pool)
        await client._ensure_client()
        assert client._current_token == "apify_api_test_key_001"
        assert client._client is not None
    finally:
        os.unlink(path)


@pytest.mark.asyncio
async def test_rotate_key_switches_to_next():
    """Marking current exhausted switches to next active key."""
    path = _keys_file(["k1", "k2", "k3"])
    try:
        pool = ApifyKeyPool(path)
        client = ApifyClient(key_pool=pool)

        # Simulate having used k1
        client._current_token = "k1"
        rotated = await client._rotate_key()
        assert rotated is True
        assert client._current_token == "k2"

        # k1 is now exhausted in the pool
        stats = pool.get_stats()
        assert stats["active"] == 2
        assert stats["exhausted"] == 1
    finally:
        os.unlink(path)


@pytest.mark.asyncio
async def test_rotate_key_fails_when_pool_dry():
    """When only key is exhausted, rotation returns False."""
    path = _keys_file(["only-key"])
    try:
        pool = ApifyKeyPool(path)
        client = ApifyClient(key_pool=pool)
        client._current_token = "only-key"

        rotated = await client._rotate_key()
        assert rotated is False
        assert pool.active_count == 0
    finally:
        os.unlink(path)


@pytest.mark.asyncio
async def test_multiple_rotations_cycle_through_all():
    """Exhausting multiple keys cycles through remaining active ones."""
    path = _keys_file(["a", "b", "c", "d"])
    try:
        pool = ApifyKeyPool(path)
        client = ApifyClient(key_pool=pool)

        client._current_token = "a"
        assert await client._rotate_key()  # a→b
        assert client._current_token == "b"

        assert await client._rotate_key()  # b→c
        assert client._current_token == "c"

        assert await client._rotate_key()  # c→d
        assert client._current_token == "d"

        # Only d left active
        assert pool.active_count == 1
        stats = pool.get_stats()
        assert stats == {"total": 4, "active": 1, "exhausted": 3}
    finally:
        os.unlink(path)
