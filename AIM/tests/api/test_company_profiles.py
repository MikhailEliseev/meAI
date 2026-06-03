"""Integration tests for Company Profiles API.

Tests the GET /by-url and POST /upsert endpoints.
Uses in-memory SQLite — each test gets a clean database.
"""

import pytest
from datetime import datetime, timezone

from httpx import AsyncClient


TEST_URL = "https://test-clinic.ru"
TEST_INN = "1234567890"
TEST_DATA = {"stage_1": {"revenue": 10_000_000, "employees": 15}}


@pytest.mark.asyncio
async def test_upsert_creates_new_profile(client: AsyncClient):
    """POST /upsert with new (url, inn) creates a record — returns 201."""
    response = await client.post(
        "/api/company-profiles/upsert",
        json={"url": TEST_URL, "inn": TEST_INN, "profile_data": TEST_DATA},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["created"] is True
    assert data["profile"]["url"] == TEST_URL
    assert data["profile"]["inn"] == TEST_INN
    assert data["profile"]["profile_data"] == TEST_DATA
    assert "id" in data["profile"]
    assert "created_at" in data["profile"]
    assert "updated_at" in data["profile"]


@pytest.mark.asyncio
async def test_upsert_updates_existing_profile(client: AsyncClient):
    """POST /upsert with existing (url, inn) updates profile_data — no duplicate, 200."""
    # Create first
    r1 = await client.post(
        "/api/company-profiles/upsert",
        json={"url": TEST_URL, "inn": TEST_INN, "profile_data": TEST_DATA},
    )
    assert r1.status_code == 201
    profile_id = r1.json()["profile"]["id"]

    # Update with new data
    new_data = {"stage_1": {"revenue": 15_000_000}, "stage_2": {"seo_score": 80}}
    r2 = await client.post(
        "/api/company-profiles/upsert",
        json={"url": TEST_URL, "inn": TEST_INN, "profile_data": new_data},
    )
    assert r2.status_code == 200
    data = r2.json()
    assert data["created"] is False
    assert data["profile"]["id"] == profile_id
    assert data["profile"]["profile_data"] == new_data


@pytest.mark.asyncio
async def test_get_by_url_returns_profile(client: AsyncClient):
    """GET /by-url returns the full profile — 200 with profile_data populated."""
    # Create profile
    await client.post(
        "/api/company-profiles/upsert",
        json={"url": TEST_URL, "inn": TEST_INN, "profile_data": TEST_DATA},
    )

    # Get by URL
    response = await client.get(
        "/api/company-profiles/by-url",
        params={"url": TEST_URL},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["found"] is True
    assert data["profile"]["url"] == TEST_URL
    assert data["profile"]["inn"] == TEST_INN
    assert data["profile"]["profile_data"] == TEST_DATA


@pytest.mark.asyncio
async def test_get_by_url_unknown_returns_404(client: AsyncClient):
    """GET /by-url for unknown URL returns 404 with {found: false}."""
    response = await client.get(
        "/api/company-profiles/by-url",
        params={"url": "https://no-such-clinic.ru"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["found"] is False
    assert data["url"] == "https://no-such-clinic.ru"


@pytest.mark.asyncio
async def test_profile_persists_across_requests(client: AsyncClient):
    """Second GET returns same data — profile persisted in DB."""
    # Create
    await client.post(
        "/api/company-profiles/upsert",
        json={"url": TEST_URL, "inn": TEST_INN, "profile_data": TEST_DATA},
    )

    # Two GETs
    r1 = await client.get("/api/company-profiles/by-url", params={"url": TEST_URL})
    r2 = await client.get("/api/company-profiles/by-url", params={"url": TEST_URL})

    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["profile"] == r2.json()["profile"]


@pytest.mark.asyncio
async def test_upsert_with_different_inn_creates_separate_record(client: AsyncClient):
    """Same URL with different INN creates separate profile (composite key)."""
    r1 = await client.post(
        "/api/company-profiles/upsert",
        json={"url": TEST_URL, "inn": "1111111111", "profile_data": {"note": "first"}},
    )
    r2 = await client.post(
        "/api/company-profiles/upsert",
        json={"url": TEST_URL, "inn": "2222222222", "profile_data": {"note": "second"}},
    )

    assert r1.status_code == 201 and r2.status_code == 201
    assert r1.json()["profile"]["id"] != r2.json()["profile"]["id"]

    # GET without INN returns the most recently updated
    r3 = await client.get("/api/company-profiles/by-url", params={"url": TEST_URL})
    assert r3.json()["profile"]["inn"] == "2222222222"

    # GET with INN returns the specific one
    r4 = await client.get(
        "/api/company-profiles/by-url",
        params={"url": TEST_URL, "inn": "1111111111"},
    )
    assert r4.json()["profile"]["inn"] == "1111111111"


@pytest.mark.asyncio
async def test_upsert_rejects_invalid_url(client: AsyncClient):
    """POST /upsert with invalid URL returns 400."""
    response = await client.post(
        "/api/company-profiles/upsert",
        json={"url": "not-a-url", "inn": "1234567890", "profile_data": {}},
    )
    assert response.status_code == 400
    assert "error" in response.json()


@pytest.mark.asyncio
async def test_get_rejects_empty_url(client: AsyncClient):
    """GET /by-url with empty url returns 400."""
    response = await client.get(
        "/api/company-profiles/by-url",
        params={"url": ""},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_upsert_default_empty_inn(client: AsyncClient):
    """POST /upsert without INN defaults to empty string."""
    response = await client.post(
        "/api/company-profiles/upsert",
        json={"url": TEST_URL, "profile_data": {"empty_inn": True}},
    )
    assert response.status_code == 201
    assert response.json()["profile"]["inn"] == ""


@pytest.mark.asyncio
async def test_empty_profile_data_accepted(client: AsyncClient):
    """POST /upsert with empty profile_data dict is accepted."""
    response = await client.post(
        "/api/company-profiles/upsert",
        json={"url": TEST_URL, "inn": TEST_INN, "profile_data": {}},
    )
    assert response.status_code == 201
    assert response.json()["profile"]["profile_data"] == {}
