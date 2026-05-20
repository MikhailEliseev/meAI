"""
Shared fixtures for Competitive Intel agent tests.

Provides:
- API key removal (forces structured null)
- Sample competitor data
- Mock httpx responses for SerpAPI/SEMrush/Ahrefs API simulations
"""

import pytest
import os


@pytest.fixture
def unset_api_keys(monkeypatch):
    """Remove all CI-relevant API keys so agents must return structured null."""
    keys_to_unset = [
        "SERPAPI_API_KEY",
        "SERPAPI_KEY",
        "SEMRUSH_API_KEY",
        "AHREFS_API_KEY",
        "PAGESPEED_API_KEY",
        "HH_ACCESS_TOKEN",
        "GA4_SERVICE_ACCOUNT",
        "YANDEX_METRICA_ACCESS_TOKEN",
        "YANDEX_DIRECT_TOKEN",
    ]
    for key in keys_to_unset:
        monkeypatch.delenv(key, raising=False)
    return True


@pytest.fixture
def sample_competitor():
    return {
        "name": "Test Clinic",
        "url": "https://test-clinic.ru",
        "domain": "test-clinic.ru",
    }


@pytest.fixture
def sample_competitors():
    return [
        {"name": "Test Clinic A", "url": "https://test-clinic-a.ru", "domain": "test-clinic-a.ru"},
        {"name": "Test Clinic B", "url": "https://test-clinic-b.ru", "domain": "test-clinic-b.ru"},
        {"name": "Test Clinic C", "url": "https://test-clinic-c.ru", "domain": "test-clinic-c.ru"},
    ]


@pytest.fixture
def sample_traffic_data():
    return {
        "monthly_organic_traffic": 5000,
        "monthly_direct_traffic": 1200,
        "monthly_paid_traffic": 800,
        "conversion_rate": 0.025,
        "data_source": "ga4",
        "confidence": 0.8,
    }
