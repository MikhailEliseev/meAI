"""Tests for ApifyKeyPool — round-robin, exhaustion, auto-recovery, stats, file handling."""

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone

import pytest

from aim.services.apify_key_pool import ApifyKeyPool


# ── Helpers ────────────────────────────────────────────────────────────

def _make_keys_file(keys: list[dict]) -> str:
    """Create a temp JSON file with the given keys list and return its path."""
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump({"keys": keys}, tmp)
    tmp.close()
    return tmp.name


def _active_key(token: str, label: str = "") -> dict:
    return {"token": token, "status": "active", "exhausted_at": None, "label": label}


def _exhausted_key(token: str, days_ago: int = 0, label: str = "") -> dict:
    exhausted_at = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()
    return {"token": token, "status": "exhausted", "exhausted_at": exhausted_at, "label": label}


# ── TestRoundRobin ─────────────────────────────────────────────────────

class TestRoundRobin:
    """Keys cycle in order. Single key always returns."""

    @pytest.mark.asyncio
    async def test_three_keys_cycle_in_order(self):
        keys = [_active_key("tok-a", "a"), _active_key("tok-b", "b"), _active_key("tok-c", "c")]
        path = _make_keys_file(keys)
        try:
            pool = ApifyKeyPool(path)
            assert await pool.get_next_key() == "tok-a"
            assert await pool.get_next_key() == "tok-b"
            assert await pool.get_next_key() == "tok-c"
            assert await pool.get_next_key() == "tok-a"  # wraps around
            assert await pool.get_next_key() == "tok-b"
        finally:
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_single_key_always_returns(self):
        keys = [_active_key("only-token")]
        path = _make_keys_file(keys)
        try:
            pool = ApifyKeyPool(path)
            assert await pool.get_next_key() == "only-token"
            assert await pool.get_next_key() == "only-token"
            assert await pool.get_next_key() == "only-token"
        finally:
            os.unlink(path)


# ── TestExhaustion ─────────────────────────────────────────────────────

class TestExhaustion:
    """Exhausting removes from rotation. Last key exhausted raises. Persistence."""

    @pytest.mark.asyncio
    async def test_exhausted_key_removed_from_rotation(self):
        keys = [_active_key("tok-a"), _active_key("tok-b")]
        path = _make_keys_file(keys)
        try:
            pool = ApifyKeyPool(path)
            assert await pool.get_next_key() == "tok-a"
            await pool.mark_exhausted("tok-a")
            # tok-a is gone, so next is tok-b
            assert await pool.get_next_key() == "tok-b"
            assert await pool.get_next_key() == "tok-b"  # still tok-b, only one left
        finally:
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_last_key_exhausted_raises(self):
        keys = [_active_key("only-token")]
        path = _make_keys_file(keys)
        try:
            pool = ApifyKeyPool(path)
            await pool.mark_exhausted("only-token")
            with pytest.raises(RuntimeError, match="no active keys"):
                await pool.get_next_key()
        finally:
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_exhaustion_persisted_to_file(self):
        keys = [_active_key("tok-a"), _active_key("tok-b")]
        path = _make_keys_file(keys)
        try:
            pool = ApifyKeyPool(path)
            await pool.mark_exhausted("tok-a")

            # Create a new pool from the same file — tok-a should still be exhausted
            pool2 = ApifyKeyPool(path)
            assert await pool2.get_next_key() == "tok-b"
        finally:
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_exhausted_at_timestamp_recorded(self):
        keys = [_active_key("tok-a")]
        path = _make_keys_file(keys)
        try:
            pool = ApifyKeyPool(path)
            await pool.mark_exhausted("tok-a")

            with open(path) as f:
                data = json.load(f)
            key = data["keys"][0]
            assert key["status"] == "exhausted"
            assert key["exhausted_at"] is not None
            # Should be a valid ISO timestamp
            datetime.fromisoformat(key["exhausted_at"])
        finally:
            os.unlink(path)


# ── TestAutoRecovery ───────────────────────────────────────────────────

class TestAutoRecovery:
    """Keys exhausted >= 31 days ago auto-reactivate. < 31 days stay exhausted."""

    @pytest.mark.asyncio
    async def test_recovers_after_32_days(self):
        keys = [_active_key("tok-a"), _exhausted_key("tok-b", days_ago=32)]
        path = _make_keys_file(keys)
        try:
            pool = ApifyKeyPool(path)
            # tok-b should have been auto-recovered
            assert pool.active_count == 2
            # Both should be in rotation
            tokens = set()
            for _ in range(4):
                tokens.add(await pool.get_next_key())
            assert tokens == {"tok-a", "tok-b"}
        finally:
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_does_not_recover_after_5_days(self):
        keys = [_active_key("tok-a"), _exhausted_key("tok-b", days_ago=5)]
        path = _make_keys_file(keys)
        try:
            pool = ApifyKeyPool(path)
            # tok-b should still be exhausted
            assert pool.active_count == 1
            assert await pool.get_next_key() == "tok-a"
            assert await pool.get_next_key() == "tok-a"
        finally:
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_recovers_exactly_at_31_days(self):
        keys = [_active_key("tok-a"), _exhausted_key("tok-b", days_ago=31)]
        path = _make_keys_file(keys)
        try:
            pool = ApifyKeyPool(path)
            # 31 days ago means >= 31 days → should recover
            assert pool.active_count == 2
        finally:
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_recovers_multiple_exhausted_keys(self):
        keys = [
            _active_key("tok-a"),
            _exhausted_key("tok-b", days_ago=35),
            _exhausted_key("tok-c", days_ago=40),
        ]
        path = _make_keys_file(keys)
        try:
            pool = ApifyKeyPool(path)
            assert pool.active_count == 3
        finally:
            os.unlink(path)


# ── TestStats ──────────────────────────────────────────────────────────

class TestStats:
    """Stats reflect exhaustions correctly."""

    @pytest.mark.asyncio
    async def test_stats_initial_state(self):
        keys = [_active_key("a"), _active_key("b"), _active_key("c")]
        path = _make_keys_file(keys)
        try:
            pool = ApifyKeyPool(path)
            stats = pool.get_stats()
            assert stats == {"total": 3, "active": 3, "exhausted": 0}
        finally:
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_stats_after_exhaustions(self):
        keys = [_active_key("a"), _active_key("b"), _active_key("c"), _active_key("d")]
        path = _make_keys_file(keys)
        try:
            pool = ApifyKeyPool(path)
            await pool.mark_exhausted("a")
            await pool.mark_exhausted("b")
            stats = pool.get_stats()
            assert stats == {"total": 4, "active": 2, "exhausted": 2}
        finally:
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_active_count_property(self):
        keys = [_active_key("a"), _active_key("b"), _active_key("c"), _active_key("d")]
        path = _make_keys_file(keys)
        try:
            pool = ApifyKeyPool(path)
            assert pool.active_count == 4
            await pool.mark_exhausted("a")
            assert pool.active_count == 3
            await pool.mark_exhausted("b")
            assert pool.active_count == 2
        finally:
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_stats_with_auto_recovered_keys(self):
        keys = [
            _active_key("a"),
            _exhausted_key("b", days_ago=35),
            _exhausted_key("c", days_ago=5),
        ]
        path = _make_keys_file(keys)
        try:
            pool = ApifyKeyPool(path)
            # b auto-recovered, c stays exhausted
            stats = pool.get_stats()
            assert stats == {"total": 3, "active": 2, "exhausted": 1}
        finally:
            os.unlink(path)


# ── TestFileHandling ───────────────────────────────────────────────────

class TestFileHandling:
    """Missing file raises FileNotFoundError. Corrupted JSON raises JSONDecodeError."""

    def test_missing_file_raises_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            ApifyKeyPool("/tmp/nonexistent_apify_keys_xyz.json")

    def test_corrupted_json_raises_decode_error(self):
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        tmp.write("this is not valid json {{{")
        tmp.close()
        try:
            with pytest.raises(json.JSONDecodeError):
                ApifyKeyPool(tmp.name)
        finally:
            os.unlink(tmp.name)

    def test_empty_file_raises_decode_error(self):
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        tmp.write("")
        tmp.close()
        try:
            with pytest.raises(json.JSONDecodeError):
                ApifyKeyPool(tmp.name)
        finally:
            os.unlink(tmp.name)

    def test_valid_file_loads_without_error(self):
        keys = [_active_key("tok-a")]
        path = _make_keys_file(keys)
        try:
            pool = ApifyKeyPool(path)
            assert pool.active_count == 1
        finally:
            os.unlink(path)

    def test_file_without_keys_field_raises_key_error(self):
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump({"wrong_field": []}, tmp)
        tmp.close()
        try:
            with pytest.raises(KeyError):
                ApifyKeyPool(tmp.name)
        finally:
            os.unlink(tmp.name)
