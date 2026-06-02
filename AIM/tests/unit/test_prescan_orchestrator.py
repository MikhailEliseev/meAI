"""Unit tests for PrescanOrchestrator.

Tests the parallel prescan flow: 5 threads gathering intelligence
about a client website (structure, financials, SEO, reviews, social).
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from aim.services.prescan_orchestrator import PrescanOrchestrator, PrescanResult


class TestPrescanResult:
    """PrescanResult dataclass serialization tests."""

    def test_empty_result_serializes(self):
        result = PrescanResult()
        d = result.to_dict()
        assert d["specialization"] == ""
        assert d["city"] == ""
        assert d["services"] == []
        assert d["doctors"] == []
        assert d["revenue_year"] is None
        assert d["seo_score"] == 0
        assert d["rating"] is None
        assert d["errors"] == []

    def test_full_result_serializes(self):
        result = PrescanResult(
            specialization="стоматология",
            city="Москва",
            services=["терапия", "хирургия"],
            doctors=[{"name": "Иванов И.И.", "title": "Главврач", "order": 1}],
            price_hints=[{"service": "Консультация", "price": "1500"}],
            inn="7700000001",
            revenue_year=15_000_000,
            profit_year=3_000_000,
            financial_year=2024,
            seo_score=72,
            seo_issues=["не адаптирован под мобильные"],
            has_mobile_viewport=False,
            has_ssl=True,
            load_speed_ms=4200,
            rating=4.3,
            reviews_count=47,
            review_praise=["хвалят врачей"],
            review_complaints=["жалуются на очереди"],
            last_post_date="2026-05-30",
            last_post_platform="vk",
            social_links={"vk": "https://vk.com/clinic"},
            errors=["social: timeout"],
        )
        d = result.to_dict()
        assert d["specialization"] == "стоматология"
        assert d["city"] == "Москва"
        assert len(d["services"]) == 2
        assert len(d["doctors"]) == 1
        assert d["doctors"][0]["name"] == "Иванов И.И."
        assert d["revenue_year"] == 15_000_000
        assert d["seo_score"] == 72
        assert d["rating"] == 4.3
        assert d["social_links"]["vk"] == "https://vk.com/clinic"
        assert "social: timeout" in d["errors"]


class TestPrescanOrchestrator:
    """PrescanOrchestrator flow tests with mocked services."""

    @pytest.fixture
    def orchestrator(self):
        return PrescanOrchestrator()

    @pytest.mark.asyncio
    async def test_url_normalization(self):
        """URL without protocol gets https:// prepended."""
        orchestrator = PrescanOrchestrator()

        with patch.object(orchestrator, '_get_http') as mock_http:
            mock_client = AsyncMock()
            mock_client.get.return_value.text = "<html></html>"
            mock_http.return_value = mock_client

            # Mock all 5 thread dependencies
            with patch(
                'aim.services.prescan_orchestrator.PrescanOrchestrator._quick_seo_scan',
                new_callable=AsyncMock,
            ) as mock_seo, patch(
                'aim.services.prescan_orchestrator.PrescanOrchestrator._quick_reviews',
                new_callable=AsyncMock,
            ) as mock_reviews, patch(
                'aim.services.prescan_orchestrator.PrescanOrchestrator._quick_social_scan',
                new_callable=AsyncMock,
            ) as mock_social, patch(
                'aim.services.prescan_orchestrator.PrescanOrchestrator._extract_inn_from_site',
                new_callable=AsyncMock,
            ) as mock_inn, patch(
                'aim.services.prescan_orchestrator.PrescanOrchestrator._fetch_nalog_financials',
                new_callable=AsyncMock,
            ) as mock_nalog, patch(
                'aim.services.service_extractor.extract_client_profile',
                new_callable=AsyncMock,
            ) as mock_extract:

                mock_seo.return_value = {"score": 70, "issues": [], "has_mobile_viewport": True, "has_ssl": True, "load_speed_ms": 1000}
                mock_reviews.return_value = {"rating": 4.5, "count": 50, "praise": [], "complaints": []}
                mock_social.return_value = {"last_post_date": None, "last_post_platform": None, "links": {}}
                mock_inn.return_value = ""
                mock_nalog.return_value = {}
                mock_extract.return_value = {
                    "specialization": "стоматология", "city": "Москва",
                    "services": [], "doctors": [], "price_hints": [], "inn": "",
                }

                result = await orchestrator.prescan("clinic.ru")

                assert result is not None
                assert result.specialization == "стоматология"
                assert result.city == "Москва"

            await orchestrator.close()

    @pytest.mark.asyncio
    async def test_error_isolation(self):
        """When one thread fails, others still complete and error is recorded."""
        orchestrator = PrescanOrchestrator()

        with patch.object(orchestrator, '_get_http') as mock_http:
            mock_client = AsyncMock()
            mock_client.get.return_value.text = "<html></html>"
            mock_http.return_value = mock_client

            with patch(
                'aim.services.prescan_orchestrator.PrescanOrchestrator._quick_seo_scan',
                new_callable=AsyncMock,
            ) as mock_seo, patch(
                'aim.services.prescan_orchestrator.PrescanOrchestrator._quick_reviews',
                new_callable=AsyncMock,
            ) as mock_reviews, patch(
                'aim.services.prescan_orchestrator.PrescanOrchestrator._quick_social_scan',
                new_callable=AsyncMock,
            ) as mock_social, patch(
                'aim.services.prescan_orchestrator.PrescanOrchestrator._extract_inn_from_site',
                new_callable=AsyncMock,
            ) as mock_inn, patch(
                'aim.services.prescan_orchestrator.PrescanOrchestrator._fetch_nalog_financials',
                new_callable=AsyncMock,
            ) as mock_nalog, patch(
                'aim.services.service_extractor.extract_client_profile',
                new_callable=AsyncMock,
            ) as mock_extract:

                # SEO thread fails, others succeed
                mock_seo.side_effect = RuntimeError("SEO scan crashed")
                mock_reviews.return_value = {"rating": 4.5, "count": 50, "praise": ["отлично"], "complaints": []}
                mock_social.return_value = {"last_post_date": None, "last_post_platform": None, "links": {}}
                mock_inn.return_value = ""
                mock_nalog.return_value = {}
                mock_extract.return_value = {
                    "specialization": "косметология", "city": "Казань",
                    "services": ["чистка"], "doctors": [], "price_hints": [], "inn": "",
                }

                result = await orchestrator.prescan("https://clinic.ru")

                # Other threads should have completed
                assert result.specialization == "косметология"
                assert result.city == "Казань"
                assert result.rating == 4.5
                assert result.reviews_count == 50

                # SEO error should be recorded
                assert len(result.errors) >= 1
                assert any("seo" in e.lower() for e in result.errors)

    @pytest.mark.asyncio
    async def test_progress_callback(self):
        """Progress callback is invoked for each thread."""
        orchestrator = PrescanOrchestrator()
        callbacks = []

        async def track(thread, status):
            callbacks.append((thread, status))

        with patch.object(orchestrator, '_get_http') as mock_http:
            mock_client = AsyncMock()
            mock_client.get.return_value.text = "<html></html>"
            mock_http.return_value = mock_client

            with patch(
                'aim.services.prescan_orchestrator.PrescanOrchestrator._quick_seo_scan',
                new_callable=AsyncMock,
            ) as mock_seo, patch(
                'aim.services.prescan_orchestrator.PrescanOrchestrator._quick_reviews',
                new_callable=AsyncMock,
            ) as mock_reviews, patch(
                'aim.services.prescan_orchestrator.PrescanOrchestrator._quick_social_scan',
                new_callable=AsyncMock,
            ) as mock_social, patch(
                'aim.services.prescan_orchestrator.PrescanOrchestrator._extract_inn_from_site',
                new_callable=AsyncMock,
            ) as mock_inn, patch(
                'aim.services.prescan_orchestrator.PrescanOrchestrator._fetch_nalog_financials',
                new_callable=AsyncMock,
            ) as mock_nalog, patch(
                'aim.services.service_extractor.extract_client_profile',
                new_callable=AsyncMock,
            ) as mock_extract:

                mock_seo.return_value = {"score": 70, "issues": [], "has_mobile_viewport": True, "has_ssl": True, "load_speed_ms": 1000}
                mock_reviews.return_value = {"rating": 4.5, "count": 50, "praise": [], "complaints": []}
                mock_social.return_value = {"last_post_date": None, "last_post_platform": None, "links": {}}
                mock_inn.return_value = ""
                mock_nalog.return_value = {}
                mock_extract.return_value = {
                    "specialization": "стоматология", "city": "Москва",
                    "services": [], "doctors": [], "price_hints": [], "inn": "",
                }

                await orchestrator.prescan("https://clinic.ru", progress_callback=track)

            await orchestrator.close()

        # Each of the 5 threads should emit "scanning" + "done"
        thread_names = {c[0] for c in callbacks}
        assert "structure" in thread_names
        assert "financials" in thread_names
        assert "seo" in thread_names
        assert "reviews" in thread_names
        assert "social" in thread_names

        # Each thread should have at least 2 callbacks (scanning + done)
        for name in thread_names:
            thread_callbacks = [c for c in callbacks if c[0] == name]
            assert len(thread_callbacks) >= 2, f"Thread {name} has {len(thread_callbacks)} callbacks, expected >= 2"


class TestINNValidation:
    """INN checksum validation tests."""

    def test_valid_10_digit_inn(self):
        from aim.services.prescan_orchestrator import PrescanOrchestrator
        # Valid 10-digit INN for a legal entity
        assert PrescanOrchestrator._is_valid_inn("7707083893") is True

    def test_valid_12_digit_inn(self):
        from aim.services.prescan_orchestrator import PrescanOrchestrator
        # Valid 12-digit INN for an individual entrepreneur
        assert PrescanOrchestrator._is_valid_inn("500100732259") is True

    def test_invalid_inn_wrong_checksum(self):
        from aim.services.prescan_orchestrator import PrescanOrchestrator
        assert PrescanOrchestrator._is_valid_inn("7707083890") is False

    def test_invalid_inn_short(self):
        from aim.services.prescan_orchestrator import PrescanOrchestrator
        assert PrescanOrchestrator._is_valid_inn("12345") is False

    def test_invalid_inn_empty(self):
        from aim.services.prescan_orchestrator import PrescanOrchestrator
        assert PrescanOrchestrator._is_valid_inn("") is False

    def test_invalid_inn_non_digit(self):
        from aim.services.prescan_orchestrator import PrescanOrchestrator
        assert PrescanOrchestrator._is_valid_inn("770708389A") is False
