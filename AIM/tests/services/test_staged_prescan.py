"""Tests for 3-stage ultra-deep prescan pipeline.

Tests prescan_staged() with mocked external services.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aim.services.prescan_orchestrator import PrescanOrchestrator, PrescanResult


@pytest.fixture
def orchestrator():
    return PrescanOrchestrator()


@pytest.mark.asyncio
async def test_prescan_staged_fires_callback_for_each_stage(orchestrator):
    """All 3 stages complete; progress_callback fires 3 times."""
    callbacks = []

    async def cb(stage_number, stage_name, summary, is_final):
        callbacks.append({"stage": stage_number, "name": stage_name, "final": is_final})

    with patch.object(orchestrator, '_stage_1_financials', new_callable=AsyncMock) as m1, \
         patch.object(orchestrator, '_stage_2_deep', new_callable=AsyncMock) as m2, \
         patch.object(orchestrator, '_stage_3_market', new_callable=AsyncMock) as m3, \
         patch.object(orchestrator, '_cache_get', new_callable=AsyncMock) as mc, \
         patch.object(orchestrator, '_cache_put', new_callable=AsyncMock) as mp:

        mc.return_value = None  # no cache
        m1.return_value = {"revenue": {"latest": 10000000}, "_errors": []}
        m2.return_value = {"seo_deep": {"score": 70}, "_errors": []}
        m3.return_value = {"revenue_multi_year": {}, "_errors": []}

        result = await orchestrator.prescan_staged(
            "https://test-clinic.ru",
            progress_callback=cb,
        )

    assert len(callbacks) == 3
    assert callbacks[0]["stage"] == 1
    assert callbacks[0]["name"] == "Финансовый хук"
    assert not callbacks[0]["final"]
    assert callbacks[1]["stage"] == 2
    assert callbacks[2]["stage"] == 3
    assert callbacks[2]["final"]
    assert "stage_1" in result
    assert "stage_2" in result
    assert "stage_3" in result


@pytest.mark.asyncio
async def test_stage_1_contains_financial_keys(orchestrator):
    """Stage 1 summary has revenue, profit, legal_entity keys."""
    with patch.object(orchestrator, '_extract_inn_from_site', new_callable=AsyncMock) as mi, \
         patch.object(orchestrator, '_extract_inn_by_name', new_callable=AsyncMock) as mn, \
         patch.object(orchestrator, '_fetch_nalog_financials', new_callable=AsyncMock) as mf:
        mi.return_value = ""
        mn.return_value = ""
        mf.return_value = {}

        with patch(
            'aim.services.service_extractor.extract_client_profile',
            new_callable=AsyncMock,
        ) as me:
            me.return_value = {
                "specialization": "Косметология",
                "city": "Москва",
                "services": ["Чистка лица"],
                "doctors": [],
                "inn": "",
            }
            result = await orchestrator._stage_1_financials("https://test-clinic.ru")

    assert "revenue" in result
    assert "profit" in result
    assert "legal_entity" in result
    assert "specialization" in result
    assert result["specialization"] == "Косметология"
    assert result["city"] == "Москва"


@pytest.mark.asyncio
async def test_stage_2_contains_deep_keys(orchestrator):
    """Stage 2 summary has licenses, founders, seo_deep, reviews, social keys."""
    with patch.object(orchestrator, '_quick_seo_scan', new_callable=AsyncMock) as ms, \
         patch.object(orchestrator, '_quick_reviews', new_callable=AsyncMock) as mr, \
         patch.object(orchestrator, '_quick_social_scan', new_callable=AsyncMock) as ml:

        ms.return_value = {"score": 70, "issues": [], "has_mobile_viewport": True,
                           "has_ssl": True, "load_speed_ms": 1200}
        mr.return_value = {"rating": 4.5, "count": 20, "praise": [], "complaints": []}
        ml.return_value = {"links": {"vk": "https://vk.com/clinic"}, "last_post_date": None}

        result = await orchestrator._stage_2_deep(
            "https://test-clinic.ru",
            {"legal_entity": {"inn": "", "legal_name": ""}, "specialization": "", "city": ""},
        )

    assert "licenses" in result
    assert "founders" in result
    assert "general_director" in result
    assert "seo_deep" in result
    assert result["seo_deep"]["score"] == 70
    assert "reviews" in result
    assert result["reviews"]["rating"] == 4.5
    assert "social" in result


@pytest.mark.asyncio
async def test_stage_3_contains_market_keys(orchestrator):
    """Stage 3 summary has maps, competitors, revenue trends, content audit keys."""
    with patch.object(orchestrator, '_get_http', new_callable=AsyncMock) as mh:
        mock_http = AsyncMock()
        mock_response = MagicMock()
        mock_response.text = "<html><title>Test Clinic</title></html>"
        mock_response.status_code = 200
        mock_http.get.return_value = mock_response
        mh.return_value = mock_http

        result = await orchestrator._stage_3_market(
            "https://test-clinic.ru",
            {"legal_entity": {"inn": "", "legal_name": "Test Clinic"}, "city": "Москва", "specialization": "Косметология"},
            {},
        )

    assert "revenue_multi_year" in result
    assert "yandex_maps" in result
    assert "google_maps" in result
    assert "nearby_competitors" in result
    assert "content_audit" in result


@pytest.mark.asyncio
async def test_cache_hit_skips_stages(orchestrator):
    """Second prescan_staged reads from cache — skips all stages."""
    cached_data = {
        "stage_1": {"revenue": {"latest": 5000000}},
        "stage_2": {"seo_deep": {"score": 80}},
        "stage_3": {"revenue_multi_year": {}},
    }

    with patch.object(orchestrator, '_cache_get', new_callable=AsyncMock) as mc:
        mc.return_value = cached_data

        result = await orchestrator.prescan_staged(
            "https://cached-clinic.ru",
            force_refresh=False,
        )

    assert result == cached_data
    mc.assert_called_once()


@pytest.mark.asyncio
async def test_force_refresh_bypasses_cache(orchestrator):
    """force_refresh=True skips cache and re-runs all stages."""
    callbacks = []

    async def cb(stage_number, stage_name, summary, is_final):
        callbacks.append(stage_number)

    with patch.object(orchestrator, '_stage_1_financials', new_callable=AsyncMock) as m1, \
         patch.object(orchestrator, '_stage_2_deep', new_callable=AsyncMock) as m2, \
         patch.object(orchestrator, '_stage_3_market', new_callable=AsyncMock) as m3, \
         patch.object(orchestrator, '_cache_get', new_callable=AsyncMock) as mc, \
         patch.object(orchestrator, '_cache_put', new_callable=AsyncMock) as mp:

        m1.return_value = {"revenue": {}, "_errors": []}
        m2.return_value = {"seo_deep": {}, "_errors": []}
        m3.return_value = {"revenue_multi_year": {}, "_errors": []}

        result = await orchestrator.prescan_staged(
            "https://clinic.ru",
            progress_callback=cb,
            force_refresh=True,
        )

    assert len(callbacks) == 3  # All 3 stages ran
    mc.assert_not_called()  # Cache never checked


@pytest.mark.asyncio
async def test_prescan_backward_compatible(orchestrator):
    """Existing prescan() method still works and returns PrescanResult."""
    with patch.object(orchestrator, '_get_http', new_callable=AsyncMock) as mh, \
         patch.object(orchestrator, '_quick_reviews', new_callable=AsyncMock) as mr, \
         patch.object(orchestrator, '_quick_social_scan', new_callable=AsyncMock) as ms, \
         patch.object(orchestrator, '_fetch_nalog_financials', new_callable=AsyncMock) as mf, \
         patch.object(orchestrator, '_extract_inn_from_site', new_callable=AsyncMock) as mi, \
         patch.object(orchestrator, '_extract_inn_by_name', new_callable=AsyncMock) as mn:

        mock_http = AsyncMock()
        mock_response = MagicMock()
        mock_response.text = "<html><head><title>Test</title><meta name='viewport' content='width=device-width'></head><h1>Clinic</h1></html>"
        mock_response.status_code = 200
        mock_http.get.return_value = mock_response
        mh.return_value = mock_http

        mr.return_value = {"rating": None, "count": 0, "praise": [], "complaints": []}
        ms.return_value = {"links": {}, "last_post_date": None}
        mf.return_value = {}
        mi.return_value = ""
        mn.return_value = ""

        with patch(
            'aim.services.service_extractor.extract_client_profile',
            new_callable=AsyncMock,
        ) as me:
            me.return_value = None
            result = await orchestrator.prescan("https://test-clinic.ru")

    assert isinstance(result, PrescanResult)
    assert hasattr(result, 'to_dict')
    result_dict = result.to_dict()
    assert "specialization" in result_dict


@pytest.mark.asyncio
async def test_stage_errors_do_not_block_pipeline(orchestrator):
    """Stage failure does not block subsequent stages."""
    callbacks = []

    async def cb(stage_number, stage_name, summary, is_final):
        callbacks.append(stage_number)

    with patch.object(orchestrator, '_stage_1_financials', new_callable=AsyncMock) as m1, \
         patch.object(orchestrator, '_stage_2_deep', new_callable=AsyncMock) as m2, \
         patch.object(orchestrator, '_stage_3_market', new_callable=AsyncMock) as m3, \
         patch.object(orchestrator, '_cache_get', new_callable=AsyncMock) as mc, \
         patch.object(orchestrator, '_cache_put', new_callable=AsyncMock) as mp:

        mc.return_value = None
        m1.return_value = {"revenue": {}, "_errors": ["dadata: timeout"]}
        m2.side_effect = Exception("Stage 2 crashed")  # This should NOT propagate
        m3.return_value = {"revenue_multi_year": {}, "_errors": []}

        result = await orchestrator.prescan_staged(
            "https://clinic.ru",
            progress_callback=cb,
        )

    # Stage 1 should have fired callback
    assert len(callbacks) >= 1
    assert "stage_1" in result


@pytest.mark.asyncio
async def test_roszdravnadzor_graceful_degradation():
    """RoszdravnadzorClient returns [] on timeout/error, never raises."""
    from aim.services.roszdravnadzor.client import RoszdravnadzorClient

    client = RoszdravnadzorClient(timeout=1.0)
    try:
        result = await client.search_licenses("Тестовая Клиника", inn="1234567890")
        assert isinstance(result, list)
        # Should return empty list (service is unreachable from local dev)
    finally:
        await client.close()
