"""
Unit tests for EEATScorer

Tests E-E-A-T scoring for medical content.
"""

import pytest

from AIM.src.aim.subagents.content_gap_analysis.scoring.eeat_scorer import EEATScorer
from AIM.src.aim.subagents.content_gap_analysis.schemas import ScrapedPageData


@pytest.fixture
def scorer():
    """Create EEATScorer instance"""
    return EEATScorer()


@pytest.fixture
def high_quality_page():
    """High-quality medical content"""
    return ScrapedPageData(
        url="https://example.com/dental-implants",
        domain="example.com",
        is_client=False,
        title="Dental Implants: Complete Guide by Dr. Smith DDS",
        word_count=2500,
        author_name="Dr. John Smith, DDS",
        author_credentials="DDS",
        is_doctor_authored=True,
        medical_citations_count=8,
        pubmed_links=["https://pubmed.ncbi.nlm.nih.gov/12345678"],
        body_text="In my experience treating patients for over 20 years, dental implants offer excellent results. Clinical studies show high success rates. The procedure involves careful diagnosis and treatment planning.",
        has_https=True,
        has_contact_info=True,
        has_privacy_policy=True,
        h1="Dental Implants Guide",
        h2_list=["What Are Implants", "Types", "Benefits", "Procedure"],
    )


@pytest.fixture
def low_quality_page():
    """Low-quality content"""
    return ScrapedPageData(
        url="http://example.com/page",
        domain="example.com",
        is_client=False,
        title="Dental Info",
        word_count=300,
        author_name=None,
        author_credentials=None,
        is_doctor_authored=False,
        medical_citations_count=0,
        body_text="Some basic information about dental procedures.",
        has_https=False,
        has_contact_info=False,
        has_privacy_policy=False,
    )


class TestEEATScorer:
    """Test E-E-A-T scoring functionality"""

    def test_calculate_eeat_high_quality(self, scorer, high_quality_page):
        """Test E-E-A-T score for high-quality content"""
        scores = scorer.calculate_eeat_score(high_quality_page)

        # High-quality page should have high scores
        assert scores.experience >= 0.8  # Doctor-authored
        assert scores.expertise >= 0.7  # Good citations and depth
        assert scores.trustworthiness >= 0.8  # HTTPS, contact, privacy
        assert scores.total >= 0.7  # Overall high quality

    def test_calculate_eeat_low_quality(self, scorer, low_quality_page):
        """Test E-E-A-T score for low-quality content"""
        scores = scorer.calculate_eeat_score(low_quality_page)

        # Low-quality page should have low scores
        assert scores.experience <= 0.3  # No author
        assert scores.expertise <= 0.3  # No citations, short content
        assert scores.trustworthiness <= 0.3  # No HTTPS, no contact
        assert scores.total <= 0.4  # Overall low quality

    def test_experience_score_doctor_authored(self, scorer):
        """Test Experience score for doctor-authored content"""
        page = ScrapedPageData(
            url="https://example.com/page",
            domain="example.com",
            is_client=False,
            author_name="Dr. Jane Doe, DMD",
            author_credentials="DMD",
            is_doctor_authored=True,
            body_text="In my experience, patients respond well to this treatment.",
        )

        score = scorer._calculate_experience_score(page)

        # Doctor + credentials + first-person = high score (allow floating point precision)
        assert score >= 0.89

    def test_experience_score_non_doctor(self, scorer):
        """Test Experience score for non-doctor author"""
        page = ScrapedPageData(
            url="https://example.com/page",
            domain="example.com",
            is_client=False,
            author_name="Sarah Johnson, RN",
            author_credentials="RN",
            is_doctor_authored=False,
        )

        score = scorer._calculate_experience_score(page)

        # Non-doctor with credentials = medium score
        assert 0.3 <= score <= 0.6

    def test_experience_score_no_author(self, scorer):
        """Test Experience score with no author"""
        page = ScrapedPageData(
            url="https://example.com/page",
            domain="example.com",
            is_client=False,
            author_name=None,
            is_doctor_authored=False,
        )

        score = scorer._calculate_experience_score(page)

        # No author = low score
        assert score <= 0.1

    def test_expertise_score_citations(self, scorer):
        """Test Expertise score based on citations"""
        # Optimal citations
        page_optimal = ScrapedPageData(
            url="https://example.com/page",
            domain="example.com",
            is_client=False,
            medical_citations_count=8,
            word_count=2000,
            body_text="Clinical diagnosis and treatment of medical conditions.",
        )

        score_optimal = scorer._calculate_expertise_score(page_optimal)
        assert score_optimal >= 0.8

        # Few citations
        page_few = ScrapedPageData(
            url="https://example.com/page",
            domain="example.com",
            is_client=False,
            medical_citations_count=2,
            word_count=2000,
            body_text="Clinical diagnosis and treatment of medical conditions.",
        )

        score_few = scorer._calculate_expertise_score(page_few)
        assert score_few < score_optimal

    def test_expertise_score_word_count(self, scorer):
        """Test Expertise score based on word count"""
        # Optimal word count
        page_optimal = ScrapedPageData(
            url="https://example.com/page",
            domain="example.com",
            is_client=False,
            word_count=2000,
            medical_citations_count=5,
            body_text="Medical content with diagnosis, treatment, procedure, symptoms, therapy.",
        )

        score_optimal = scorer._calculate_expertise_score(page_optimal)

        # Short content
        page_short = ScrapedPageData(
            url="https://example.com/page",
            domain="example.com",
            is_client=False,
            word_count=500,
            medical_citations_count=5,
            body_text="Medical content with diagnosis, treatment, procedure, symptoms, therapy.",
        )

        score_short = scorer._calculate_expertise_score(page_short)

        assert score_optimal > score_short

    def test_expertise_score_medical_terminology(self, scorer):
        """Test Expertise score based on medical terminology"""
        page_with_terms = ScrapedPageData(
            url="https://example.com/page",
            domain="example.com",
            is_client=False,
            word_count=1500,
            medical_citations_count=3,
            body_text="The diagnosis involves clinical examination. Treatment options include medical therapy and surgical procedure. Patient symptoms indicate the condition requires immediate medical attention.",
        )

        page_without_terms = ScrapedPageData(
            url="https://example.com/page",
            domain="example.com",
            is_client=False,
            word_count=1500,
            medical_citations_count=3,
            body_text="This is some general content about health topics without specific terminology.",
        )

        score_with = scorer._calculate_expertise_score(page_with_terms)
        score_without = scorer._calculate_expertise_score(page_without_terms)

        assert score_with > score_without

    def test_authoritativeness_score_domain_authority(self, scorer):
        """Test Authoritativeness score with domain authority"""
        page = ScrapedPageData(
            url="https://example.edu/page",
            domain="example.edu",
            is_client=False,
        )

        # High domain authority
        score_high = scorer._calculate_authoritativeness_score(page, domain_authority=0.9)
        assert score_high >= 0.5

        # Low domain authority
        score_low = scorer._calculate_authoritativeness_score(page, domain_authority=0.2)
        assert score_low < score_high

    def test_authoritativeness_score_backlinks(self, scorer):
        """Test Authoritativeness score with backlinks"""
        page = ScrapedPageData(
            url="https://example.com/page",
            domain="example.com",
            is_client=False,
        )

        # Many backlinks
        score_many = scorer._calculate_authoritativeness_score(
            page, domain_authority=0.5, backlinks_count=150
        )

        # Few backlinks
        score_few = scorer._calculate_authoritativeness_score(
            page, domain_authority=0.5, backlinks_count=10
        )

        assert score_many > score_few

    def test_authoritativeness_score_edu_domain(self, scorer):
        """Test Authoritativeness score for .edu domain"""
        page_edu = ScrapedPageData(
            url="https://university.edu/page",
            domain="university.edu",
            is_client=False,
        )

        page_com = ScrapedPageData(
            url="https://example.com/page",
            domain="example.com",
            is_client=False,
        )

        score_edu = scorer._calculate_authoritativeness_score(page_edu)
        score_com = scorer._calculate_authoritativeness_score(page_com)

        # .edu should score higher than .com
        assert score_edu > score_com

    def test_trustworthiness_score_https(self, scorer):
        """Test Trustworthiness score with HTTPS"""
        page_https = ScrapedPageData(
            url="https://example.com/page",
            domain="example.com",
            is_client=False,
            has_https=True,
            has_contact_info=True,
            has_privacy_policy=True,
            h1="Title",
            h2_list=["H2-1", "H2-2", "H2-3"],
        )

        page_http = ScrapedPageData(
            url="http://example.com/page",
            domain="example.com",
            is_client=False,
            has_https=False,
            has_contact_info=True,
            has_privacy_policy=True,
            h1="Title",
            h2_list=["H2-1", "H2-2", "H2-3"],
        )

        score_https = scorer._calculate_trustworthiness_score(page_https)
        score_http = scorer._calculate_trustworthiness_score(page_http)

        assert score_https > score_http

    def test_trustworthiness_score_contact_info(self, scorer):
        """Test Trustworthiness score with contact info"""
        page_with = ScrapedPageData(
            url="https://example.com/page",
            domain="example.com",
            is_client=False,
            has_https=True,
            has_contact_info=True,
            has_privacy_policy=True,
            h1="Title",
            h2_list=["H2-1", "H2-2", "H2-3"],
        )

        page_without = ScrapedPageData(
            url="https://example.com/page",
            domain="example.com",
            is_client=False,
            has_https=True,
            has_contact_info=False,
            has_privacy_policy=True,
            h1="Title",
            h2_list=["H2-1", "H2-2", "H2-3"],
        )

        score_with = scorer._calculate_trustworthiness_score(page_with)
        score_without = scorer._calculate_trustworthiness_score(page_without)

        assert score_with > score_without

    def test_classify_quality_tier(self, scorer):
        """Test quality tier classification"""
        assert scorer.classify_quality_tier(0.9) == "excellent"
        assert scorer.classify_quality_tier(0.7) == "good"
        assert scorer.classify_quality_tier(0.5) == "fair"
        assert scorer.classify_quality_tier(0.3) == "poor"

    def test_get_improvement_recommendations_low_experience(self, scorer):
        """Test recommendations for low Experience score"""
        page = ScrapedPageData(
            url="https://example.com/page",
            domain="example.com",
            is_client=False,
            author_name=None,
            is_doctor_authored=False,
            word_count=2000,
            medical_citations_count=5,
        )

        scores = scorer.calculate_eeat_score(page)
        recommendations = scorer.get_improvement_recommendations(page, scores)

        # Should recommend adding doctor author
        assert any("doctor author" in rec.lower() for rec in recommendations)

    def test_get_improvement_recommendations_low_expertise(self, scorer):
        """Test recommendations for low Expertise score"""
        page = ScrapedPageData(
            url="https://example.com/page",
            domain="example.com",
            is_client=False,
            author_name="Dr. Smith, DDS",
            is_doctor_authored=True,
            word_count=500,
            medical_citations_count=1,
        )

        scores = scorer.calculate_eeat_score(page)
        recommendations = scorer.get_improvement_recommendations(page, scores)

        # Should recommend adding citations and increasing depth
        assert any("citation" in rec.lower() for rec in recommendations)
        assert any("depth" in rec.lower() or "word" in rec.lower() for rec in recommendations)

    def test_get_improvement_recommendations_low_trustworthiness(self, scorer):
        """Test recommendations for low Trustworthiness score"""
        page = ScrapedPageData(
            url="http://example.com/page",
            domain="example.com",
            is_client=False,
            author_name="Dr. Smith, DDS",
            is_doctor_authored=True,
            word_count=2000,
            medical_citations_count=5,
            has_https=False,
            has_contact_info=False,
            has_privacy_policy=False,
        )

        scores = scorer.calculate_eeat_score(page)
        recommendations = scorer.get_improvement_recommendations(page, scores)

        # Should recommend HTTPS, contact info, privacy policy
        assert any("https" in rec.lower() for rec in recommendations)
        assert any("contact" in rec.lower() for rec in recommendations)
        assert any("privacy" in rec.lower() for rec in recommendations)

    def test_eeat_weights_sum_to_one(self, scorer):
        """Test that E-E-A-T weights sum to 1.0"""
        total = (
            scorer.EXPERIENCE_WEIGHT
            + scorer.EXPERTISE_WEIGHT
            + scorer.AUTHORITATIVENESS_WEIGHT
            + scorer.TRUSTWORTHINESS_WEIGHT
        )
        assert abs(total - 1.0) < 0.001  # Allow for floating point precision
