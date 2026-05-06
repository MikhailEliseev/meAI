"""
Unit tests for Business Report Generator

Tests report generation functionality.
"""

import pytest
import json
from pathlib import Path
from aim.subagents.competitive_intel.agents.business_report import BusinessReportGenerator


@pytest.fixture
def sample_analysis():
    """Sample deep analysis data"""
    return {
        "name": "Test Clinic",
        "url": "https://test-clinic.ru",
        "analysis_date": "2026-05-06T00:00:00",
        "pages_analyzed_data": [
            {
                "url": "https://test-clinic.ru",
                "type": "homepage",
                "cms": {
                    "cms": "WordPress",
                    "confidence": 1.0,
                    "business_context": "Гибкая CMS"
                },
                "analytics": {
                    "analytics": {
                        "google_analytics": {"detected": True, "confidence": 1.0},
                        "yandex_metrika": {"detected": True, "confidence": 1.0}
                    }
                },
                "call_tracking": {"detected": True, "provider": "Calltouch"},
                "live_chat": {"detected": True, "provider": "Jivo"},
                "messengers": {"messengers": {"WhatsApp": True}, "count": 1},
                "booking_systems": {"detected": True, "system": "YCLIENTS"},
                "payment_systems": {"systems": {"Yandex.Kassa": True}, "count": 1},
                "cdn": {"detected": True, "provider": "Cloudflare"},
                "hosting": {"detected": False},
                "ab_testing": {"detected": False},
                "retargeting": {"pixels": {"Facebook": True}, "count": 1},
                "email_marketing": {"detected": True, "platform": "Mailchimp"},
                "crm": {"detected": True, "crm": "AmoCRM"},
                "quiz_lead_magnets": {"detected": True, "confidence": 0.7},
                "social_proof": {"elements": {"reviews": True, "ratings": True}, "count": 2},
                "geo_targeting": {"detected": False},
                "promo_mechanics": {"mechanics": {"discount": True}, "count": 1}
            }
        ]
    }


class TestBusinessReportGenerator:
    """Test BusinessReportGenerator class"""

    def test_init(self, sample_analysis):
        """Test initialization"""
        generator = BusinessReportGenerator(sample_analysis)
        assert generator.competitor_name == "Test Clinic"
        assert generator.competitor_url == "https://test-clinic.ru"

    def test_map_technical_to_business(self, sample_analysis):
        """Test technical to business mapping"""
        generator = BusinessReportGenerator(sample_analysis)
        business_data = generator._map_technical_to_business()

        assert "competitor_name" in business_data
        assert "overall_score" in business_data
        assert "tech_stack" in business_data
        assert "marketing_maturity" in business_data
        assert "positioning" in business_data
        assert "opportunities" in business_data

    def test_summarize_tech_stack(self, sample_analysis):
        """Test tech stack summarization"""
        generator = BusinessReportGenerator(sample_analysis)
        pages = sample_analysis["pages_analyzed_data"]
        tech_stack = generator._summarize_tech_stack(pages)

        assert "cms" in tech_stack
        assert "analytics" in tech_stack
        assert tech_stack["cms"]["cms"] == "WordPress"

    def test_score_marketing_tools(self, sample_analysis):
        """Test marketing tools scoring"""
        generator = BusinessReportGenerator(sample_analysis)
        pages = sample_analysis["pages_analyzed_data"]
        score = generator._score_marketing_tools(pages)

        assert "score" in score
        assert "level" in score
        assert "tools_count" in score
        assert 0 <= score["score"] <= 100
        assert score["tools_count"] >= 0

    def test_identify_strengths_weaknesses(self, sample_analysis):
        """Test strengths/weaknesses identification"""
        generator = BusinessReportGenerator(sample_analysis)
        pages = sample_analysis["pages_analyzed_data"]
        positioning = generator._identify_strengths_weaknesses(pages)

        assert "strengths" in positioning
        assert "weaknesses" in positioning
        assert isinstance(positioning["strengths"], list)
        assert isinstance(positioning["weaknesses"], list)

    def test_find_opportunities(self, sample_analysis):
        """Test opportunity finding"""
        generator = BusinessReportGenerator(sample_analysis)
        pages = sample_analysis["pages_analyzed_data"]
        opportunities = generator._find_opportunities(pages)

        assert isinstance(opportunities, list)
        assert len(opportunities) <= 3  # Top 3

    def test_calculate_overall_score(self, sample_analysis):
        """Test overall score calculation"""
        generator = BusinessReportGenerator(sample_analysis)
        pages = sample_analysis["pages_analyzed_data"]
        tech_stack = generator._summarize_tech_stack(pages)
        marketing_score = generator._score_marketing_tools(pages)

        score = generator._calculate_overall_score(tech_stack, marketing_score)

        assert 0 <= score <= 100
        assert isinstance(score, int)

    def test_generate_html_content(self, sample_analysis):
        """Test HTML content generation"""
        generator = BusinessReportGenerator(sample_analysis)
        business_data = generator._map_technical_to_business()
        html_content = generator._generate_html_content(business_data)

        assert "<!DOCTYPE html>" in html_content
        assert "Test Clinic" in html_content
        assert "test-clinic.ru" in html_content
        assert "Общая оценка" in html_content

    def test_generate_html_xss_prevention(self, sample_analysis):
        """Test XSS prevention in HTML generation"""
        # Inject malicious data
        sample_analysis["name"] = '<script>alert("XSS")</script>'

        generator = BusinessReportGenerator(sample_analysis)
        business_data = generator._map_technical_to_business()
        html_content = generator._generate_html_content(business_data)

        # Should be escaped
        assert "&lt;script&gt;" in html_content
        assert "<script>" not in html_content or "<script src=" in html_content  # Allow legitimate scripts

    def test_generate_html_file(self, sample_analysis, tmp_path):
        """Test HTML file generation"""
        generator = BusinessReportGenerator(sample_analysis)
        output_path = tmp_path / "report.html"

        result_path = generator.generate_html(str(output_path))

        assert Path(result_path).exists()
        assert Path(result_path).read_text(encoding='utf-8')
        assert "Test Clinic" in Path(result_path).read_text(encoding='utf-8')

    def test_empty_analysis(self):
        """Test with empty analysis data"""
        empty_analysis = {
            "name": "Empty",
            "url": "https://empty.com",
            "pages_analyzed_data": []
        }

        generator = BusinessReportGenerator(empty_analysis)
        business_data = generator._map_technical_to_business()

        assert business_data["overall_score"] == 0
        assert business_data["marketing_maturity"]["score"] == 0


class TestPDFGeneration:
    """Test PDF generation (requires WeasyPrint)"""

    def test_pdf_generation_without_weasyprint(self, sample_analysis, tmp_path):
        """Test PDF generation fails gracefully without WeasyPrint"""
        generator = BusinessReportGenerator(sample_analysis)
        output_path = tmp_path / "report.pdf"

        try:
            generator.generate_pdf(str(output_path))
            # If WeasyPrint is installed, file should exist
            assert Path(output_path).exists()
        except ImportError as e:
            # If WeasyPrint not installed, should raise ImportError
            assert "WeasyPrint" in str(e)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
