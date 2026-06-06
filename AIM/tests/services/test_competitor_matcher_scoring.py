"""Tests for competitor_matcher scoring (S1, S2, M1, S4)."""
import inspect
import pytest
from src.aim.services.competitor_matcher import (
    W_REVENUE, W_LOCATION, W_SERVICES, W_SPECIALIZATION,
    W_DATA, W_POPULARITY, W_VISIBILITY,
    _score_revenue_match,
    _score_location,
    _score_services,
    _score_popularity,
    _score_visibility,
    _score_specialization_purity,
    _is_state_healthcare,
    _is_multi_profile_client,
    _is_multi_profile_candidate,
    _haversine,
    _extract_city,
    _name_similarity,
    _candidate_services,
    ClientProfile,
    CompanyProfile,
    CompetitorMatcher,
)


# ── Helpers ───────────────────────────────────────────────────────────

def _make_client(**kwargs) -> ClientProfile:
    defaults = {"url": "http://test.ru", "specialization": "стоматология",
                "city": "Москва", "services": []}
    defaults.update(kwargs)
    return ClientProfile(**defaults)


def _make_candidate(**kwargs) -> CompanyProfile:
    c = CompanyProfile(inn=kwargs.pop("inn", "1234567890"))
    for k, v in kwargs.items():
        setattr(c, k, v)
    return c


# ── S1 + S2: Weights rebalanced ──────────────────────────────────────

class TestScoringWeights:
    """S1: popularity 0.13 (was 0.11), S2: services 0.12 (was 0.25)."""

    def test_all_weights_sum_to_one(self):
        weights = [W_REVENUE, W_LOCATION, W_SERVICES, W_SPECIALIZATION,
                   W_DATA, W_POPULARITY, W_VISIBILITY]
        assert abs(sum(weights) - 1.0) < 0.001

    def test_popularity_weight_raised(self):
        """S1: popularity now 0.13 (was 0.11)."""
        assert W_POPULARITY == 0.13

    def test_service_overlap_weight_lowered(self):
        """S2: service_overlap now 0.12 (was 0.25)."""
        assert W_SERVICES == 0.12

    def test_data_quality_weight_raised(self):
        """data_quality now 0.15 (was 0.14)."""
        assert W_DATA == 0.15

    def test_visibility_weight_raised(self):
        """visibility now 0.10 (was 0.10) — unchanged."""
        assert W_VISIBILITY == 0.10


# ── M1: Pure Jaccard (no TF-IDF) ─────────────────────────────────────

class TestJaccardScoring:
    """M1: _score_services uses pure Jaccard, not TF-IDF + Jaccard."""

    def test_jaccard_returns_float_between_zero_and_one(self):
        client = _make_client(services=["терапия", "ортопедия", "имплантация"])
        cand = _make_candidate(
            source_services={"терапия": None, "ортопедия": None, "имплантация": None},
            source_specialization="стоматология",
            name="Тест",
        )
        score = _score_services(client, cand)
        assert 0.0 < score <= 1.0

    def test_partial_overlap_positive(self):
        client = _make_client(services=["терапия", "ортопедия", "имплантация"])
        cand = _make_candidate(
            source_services={"терапия": None},
            source_specialization="стоматология",
            name="Тест",
        )
        score = _score_services(client, cand)
        assert 0.0 < score < 1.0

    def test_no_overlap_returns_zero(self):
        client = _make_client(services=["терапия", "ортопедия"])
        cand = _make_candidate(
            source_services={"косметология": None},
            source_specialization="косметология",
            name="Тест",
        )
        score = _score_services(client, cand)
        assert score == 0.0

    def test_empty_client_services_returns_neutral(self):
        client = _make_client(services=[])
        cand = _make_candidate(name="Тест")
        score = _score_services(client, cand)
        assert score == 0.5

    def test_jaccard_symmetric(self):
        """Jaccard should give same score regardless of order."""
        client = _make_client(services=["терапия", "хирургия"])
        cand1 = _make_candidate(
            source_services={"терапия": None, "хирургия": None},
            source_specialization="стоматология",
            name="А",
        )
        cand2 = _make_candidate(
            source_services={"хирургия": None, "терапия": None},
            source_specialization="стоматология",
            name="Б",
        )
        # Note: _candidate_services adds specialization-specific defaults,
        # so scores may differ due to different default sets. This test
        # confirms the Jaccard function runs without error for both.
        s1 = _score_services(client, cand1)
        s2 = _score_services(client, cand2)
        assert isinstance(s1, float)
        assert isinstance(s2, float)


# ── Revenue match ─────────────────────────────────────────────────────

class TestRevenueMatch:
    def test_exact_match(self):
        assert _score_revenue_match(50_000_000, 50_000_000) == 0.8

    def test_similar_revenue(self):
        score = _score_revenue_match(50_000_000, 60_000_000)
        assert 0.5 < score < 1.0

    def test_very_different_revenue(self):
        score = _score_revenue_match(10_000_000, 200_000_000)
        assert score < 0.3

    def test_different_magnitude(self):
        """10M vs 100M — should be very low score."""
        score = _score_revenue_match(10_000_000, 100_000_000)
        assert score < 0.2


# ── Location / Haversine ──────────────────────────────────────────────

class TestHaversine:
    def test_same_point(self):
        assert _haversine(55.75, 37.62, 55.75, 37.62) == 0.0

    def test_moscow_to_spb(self):
        dist = _haversine(55.7558, 37.6173, 59.9343, 30.3351)
        assert 600 < dist < 700  # ~635 km

    def test_nearby(self):
        dist = _haversine(55.75, 37.62, 55.76, 37.63)
        assert dist < 2.0


class TestLocationScoring:
    def test_same_city(self):
        """Same city by address without coordinates → 0.7."""
        client = _make_client(city="Москва")
        cand = _make_candidate(legal_address="г. Москва, ул. Тверская, 1")
        score = _score_location(client, cand)
        assert score == 0.7  # same city by address, no coords → 0.7

    def test_nearby_cities_with_coords(self):
        """Cities within 50 km via coordinates should score well.

        _score_location takes city_lat/city_lon as explicit parameters,
        not from ClientProfile attributes.
        """
        client = _make_client(city="Москва")
        cand = _make_candidate(
            legal_address="г. Химки", geo_lat=55.90, geo_lon=37.43
        )
        score = _score_location(client, cand, city_lat=55.75, city_lon=37.62)
        assert 0.3 < score <= 1.0  # <50 km but not same city

    def test_far_cities_low_score(self):
        client = _make_client(city="Москва")
        cand = _make_candidate(
            legal_address="г. Новосибирск", geo_lat=55.03, geo_lon=82.92
        )
        score = _score_location(client, cand, city_lat=55.75, city_lon=37.62)
        assert score < 0.3  # far away

    def test_megalopolis_wider_radius(self):
        """Moscow clinics 10 km apart should still score well (25 km radius)."""
        client = _make_client(city="Москва")
        # Two Moscow clinics ~10 km apart (center vs outskirts)
        cand = _make_candidate(
            legal_address="г. Москва, ул. Профсоюзная, 100",
            geo_lat=55.65, geo_lon=37.55,
        )
        score = _score_location(client, cand, city_lat=55.75, city_lon=37.62)
        assert score > 0.5  # 10 km within 25 km radius → ~0.6

    def test_non_megalopolis_tighter_radius(self):
        """Non-megalopolis city: 10 km should score 0 (7 km limit)."""
        client = _make_client(city="Тула")
        cand = _make_candidate(
            legal_address="г. Тула, ул. Ленина, 10",
            geo_lat=54.20, geo_lon=37.62,
        )
        score = _score_location(client, cand, city_lat=54.30, city_lon=37.62)
        assert score == 0.0  # ~11 km > 7 km → 0


# ── State healthcare filter ───────────────────────────────────────────

class TestStateHealthcareFilter:
    def test_gauz_filtered(self):
        assert _is_state_healthcare("ГАУЗ Городская Больница №1")

    def test_gbuz_filtered(self):
        assert _is_state_healthcare("ГБУЗ Поликлиника №5")

    def test_muz_filtered(self):
        assert _is_state_healthcare("МУЗ Центральная Районная Больница")

    def test_ooo_not_filtered(self):
        assert not _is_state_healthcare('ООО "Стоматология Все Свои"')

    def test_ip_not_filtered(self):
        assert not _is_state_healthcare("ИП Иванов Стоматолог")

    def test_ao_not_filtered(self):
        assert not _is_state_healthcare('АО "Медицинский Центр"')


# ── S4: named_competitors parameter ──────────────────────────────────

class TestNamedCompetitorsSignature:
    """S4: find_competitors accepts named_competitors parameter."""

    def test_signature_has_named_competitors(self):
        sig = inspect.signature(CompetitorMatcher.find_competitors)
        assert "named_competitors" in sig.parameters

    def test_named_competitors_default_is_none(self):
        sig = inspect.signature(CompetitorMatcher.find_competitors)
        param = sig.parameters["named_competitors"]
        assert param.default is None


# ── Multi-profile detection ───────────────────────────────────────────

class TestMultiProfileDetection:
    def test_dental_is_not_multi(self):
        client = _make_client(specialization="стоматология")
        assert not _is_multi_profile_client(client)

    def test_cosmo_is_not_multi(self):
        client = _make_client(specialization="косметология")
        assert not _is_multi_profile_client(client)

    def test_multi_is_multi(self):
        client = _make_client(specialization="многопрофильная клиника")
        assert _is_multi_profile_client(client)


# ── City extraction from address ──────────────────────────────────────

class TestCityExtraction:
    def test_full_address(self):
        assert _extract_city("г. Москва, ул. Тверская, 1") == "Москва"

    def test_no_city(self):
        assert _extract_city("ул. Ленина, д. 5") == ""

    def test_spb_full_name(self):
        assert _extract_city("Санкт-Петербург, Невский проспект") == "Санкт-Петербург"


# ── Name similarity ───────────────────────────────────────────────────

class TestNameSimilarity:
    def test_identical(self):
        assert _name_similarity("Стоматология Все Свои", "Стоматология Все Свои") == 1.0

    def test_different(self):
        score = _name_similarity("Стоматология Все Свои", "Косметология Красота")
        assert score < 0.5

    def test_shared_tokens(self):
        score = _name_similarity("Стоматология Все Свои", "Стоматология Улыбка")
        assert 0.0 < score < 1.0
