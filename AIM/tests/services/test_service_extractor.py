"""Tests for service_extractor — specialization (C1), services (C3), city (S3)."""
import pytest
from src.aim.services.service_extractor import (
    _detect_specialization,
    _detect_services,
    _detect_city,
    _extract_city_from_schema,
    _extract_city_from_url,
)


# ── C1: Dominance-based specialization detection ─────────────────────

class TestSpecializationDetection:
    """C1: dominance-based — most keyword matches wins, not first-match."""

    def test_single_category_clear_winner(self):
        """Clear dental keywords → стоматология."""
        text = "стоматология лечение зубов кариес имплантация протезирование брекеты"
        assert _detect_specialization(text, "http://test.ru") == "стоматология"

    def test_dominance_dental_over_cosmo(self):
        """6 dental keywords vs 1 cosmo keyword → стоматология wins by count."""
        text = "стоматолог терапевт пародонтолог ортодонт хирург имплантолог ботокс"
        assert _detect_specialization(text, "http://test.ru") == "стоматология"

    def test_cosmetology_clear_winner(self):
        text = "косметолог косметология эстетическ ботокс филлеры"
        assert _detect_specialization(text, "http://test.ru") == "косметология"

    def test_multiprofile_wins_when_no_specific_keywords(self):
        """With only generic clinic terms → многопрофильная."""
        text = "медицинский центр клиника здоровье"
        result = _detect_specialization(text, "http://test.ru")
        assert result == "многопрофильная клиника"

    def test_pediatrics_wins_over_default(self):
        text = "педиатр педиатрия детск медицинский центр"
        assert _detect_specialization(text, "http://test.ru") == "педиатрия"

    def test_empty_text_falls_back_to_url(self):
        """When text has no keywords, fall back to URL analysis."""
        result = _detect_specialization("просто текст", "https://stomat-clinic.ru")
        assert result == "стоматология"

    def test_empty_text_empty_url_returns_empty(self):
        result = _detect_specialization("нет ключевых слов", "http://example.com")
        assert result == ""


# ── C3: Negation context filtering ───────────────────────────────────

class TestServiceDetection:
    """C3: services near negation markers are excluded, others remain."""

    def test_negation_implant_excluded_simple(self):
        """имплантация after противопоказания → excluded."""
        text = "противопоказания к имплантации: диабет, сердечная недостаточность"
        services = _detect_services(text.lower())
        assert "имплантация" not in services

    def test_negation_in_one_sentence_services_in_another(self):
        """Negation only blocks the adjacent service, not distant ones."""
        text = "противопоказания к имплантации: диабет. услуги: терапия, ортопедия, брекеты."
        services = _detect_services(text.lower())
        assert "терапия" in services
        assert "ортопедия" in services

    def test_positive_implant_detected(self):
        """имплантация in positive context → detected."""
        text = "мы проводим имплантацию зубов любой сложности"
        services = _detect_services(text.lower())
        assert "имплантация" in services

    def test_not_using_marker_excludes(self):
        """не используем имплантацию → excluded."""
        text = "не используем имплантацию в нашей практике"
        services = _detect_services(text.lower())
        assert "имплантация" not in services

    def test_not_doing_marker_excludes(self):
        """не делаем брекеты → excluded."""
        text = "не делаем брекеты для пациентов старше 50"
        services = _detect_services(text.lower())
        assert "брекеты" not in services

    def test_contraindicated_marker_excludes(self):
        """противопоказани blocks any nearby service."""
        text = "противопоказания: не рекомендуется имплантация"
        services = _detect_services(text.lower())
        assert "имплантация" not in services

    def test_multiple_services_some_negated(self):
        """Mix of negated and non-negated: non-negated detected, negated excluded."""
        text = (
            "услуги клиники: терапия и ортопедия высокого уровня. "
            "лечение зубов любой сложности. "
            "важно: противопоказания к имплантации при диабете. "
            "мы не делаем брекеты пациентам старше 60 лет. "
            "также проводим профессиональную чистку зубов и отбеливание."
        )
        services = _detect_services(text.lower())
        assert "терапия" in services
        assert "ортопедия" in services
        assert "имплантация" not in services
        assert "ортодонтия" not in services  # брекеты excluded
        assert "гигиена" in services  # чистка зубов, отбеливание


# ── S3: City detection ───────────────────────────────────────────────

class TestCityDetection:
    """S3: JSON-LD schema.org + full-page text search."""

    def test_detect_city_prepositional(self):
        """City in 'в Городе' pattern."""
        assert _detect_city("стоматология в Орле, лечение зубов") == "Орёл"

    def test_detect_city_direct_name(self):
        """Direct city name match."""
        assert _detect_city("клиника Москва центр") == "Москва"

    def test_detect_city_declined_form(self):
        """Declined form 'в Москве' matches Москва."""
        assert _detect_city("клиника в Москве на Тверской") == "Москва"

    def test_city_beyond_5000_chars(self):
        """City beyond first 5000 chars is still detected (full-page search)."""
        padding = "X" * 6000
        text = padding + "Стоматология в Казани — лечение зубов"
        assert _detect_city(text) == "Казань"

    def test_city_declined_beyond_5000(self):
        """Declined city beyond 5000 chars is found."""
        padding = "X" * 6000
        text = padding + "Клиника в Екатеринбурге на Ленина"
        assert _detect_city(text) == "Екатеринбург"


class TestSchemaCityExtraction:
    """S3: JSON-LD/schema.org addressLocality parsing."""

    def test_simple_jsonld(self):
        html = """
        <html><head>
        <script type="application/ld+json">
        {"@context":"https://schema.org","@type":"MedicalOrganization",
         "address":{"@type":"PostalAddress","addressLocality":"Москва"}}
        </script></head><body></body></html>
        """
        assert _extract_city_from_schema(html) == "Москва"

    def test_jsonld_with_graph(self):
        html = """
        <html><head>
        <script type="application/ld+json">
        {"@context":"https://schema.org","@graph":[
         {"@type":"MedicalOrganization","address":
          {"@type":"PostalAddress","addressLocality":"Казань"}}
        ]}
        </script></head><body></body></html>
        """
        assert _extract_city_from_schema(html) == "Казань"

    def test_no_schema_returns_empty(self):
        assert _extract_city_from_schema("<html><body>Нет разметки</body></html>") == ""

    def test_jsonld_address_string(self):
        """address as inline string with city name."""
        html = """
        <html><head>
        <script type="application/ld+json">
        {"@context":"https://schema.org","@type":"LocalBusiness",
         "address":"ул. Ленина, 1, Новосибирск"}
        </script></head><body></body></html>
        """
        assert _extract_city_from_schema(html) == "Новосибирск"


class TestUrlCityExtraction:
    def test_domain_prefix_msk(self):
        assert _extract_city_from_url("https://msk.clinic.ru") == "Москва"

    def test_domain_prefix_spb(self):
        assert _extract_city_from_url("https://spb.dental.ru") == "Санкт-Петербург"

    def test_no_city_in_url(self):
        assert _extract_city_from_url("https://example.com") == ""
