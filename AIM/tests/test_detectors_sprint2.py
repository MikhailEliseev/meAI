"""
Unit tests for Sprint 2 Marketing Intelligence Detectors

Tests 7 new detectors:
1. Retargeting Detection
2. Email Marketing Detection
3. CRM Detection
4. Quiz/Lead Magnets Detection
5. Social Proof Detection
6. Geo-Targeting Detection
7. Promo Mechanics Detection
"""

import pytest
from src.aim.subagents.competitive_intel.agents.ci_deep_analyzer import CIDeepAnalyzer


@pytest.fixture
def analyzer():
    """Create analyzer instance for testing"""
    return CIDeepAnalyzer(
        agent_id="test_analyzer",
        database_url="sqlite:///test.db",
        vault_path="./test_vault"
    )


class TestRetargetingDetection:
    """Test retargeting pixels detection"""

    def test_detect_facebook_pixel(self, analyzer):
        html = '<script src="https://connect.facebook.net/en_US/fbevents.js"></script>'
        result = analyzer._detect_retargeting(html)
        assert "Facebook" in result["pixels"]
        assert result["count"] >= 1

    def test_detect_vk_pixel(self, analyzer):
        html = '<script src="https://vk.com/js/api/openapi.js"></script>'
        result = analyzer._detect_retargeting(html)
        assert "VK" in result["pixels"]

    def test_detect_multiple_pixels(self, analyzer):
        html = '''
        <script src="https://connect.facebook.net/en_US/fbevents.js"></script>
        <script src="https://vk.com/js/api/openapi.js"></script>
        '''
        result = analyzer._detect_retargeting(html)
        assert result["count"] >= 2
        assert "Facebook" in result["pixels"]
        assert "VK" in result["pixels"]

    def test_no_retargeting(self, analyzer):
        html = '<html><body>No retargeting</body></html>'
        result = analyzer._detect_retargeting(html)
        assert result["count"] == 0
        assert "теряют" in result["business_context"]


class TestEmailMarketingDetection:
    """Test email marketing detection"""

    def test_detect_mailchimp(self, analyzer):
        html = '<script src="https://chimpstatic.com/mcjs-connected/js/users/abc.js"></script>'
        result = analyzer._detect_email_marketing(html)
        assert result["platform"] == "Mailchimp"
        assert result["detected"] == True

    def test_detect_sendpulse(self, analyzer):
        html = '<script src="https://sendpulse.com/js/push/"></script>'
        result = analyzer._detect_email_marketing(html)
        assert result["platform"] == "SendPulse"

    def test_no_email_marketing(self, analyzer):
        html = '<html><body>No email marketing</body></html>'
        result = analyzer._detect_email_marketing(html)
        assert result["detected"] == False


class TestCRMDetection:
    """Test CRM detection"""

    def test_detect_amocrm(self, analyzer):
        html = '<script src="https://www.amocrm.ru/script.js"></script>'
        result = analyzer._detect_crm(html)
        assert result["crm"] == "AmoCRM"
        assert result["detected"] == True

    def test_detect_bitrix24(self, analyzer):
        html = '<div class="b24-web-form"></div>'
        result = analyzer._detect_crm(html)
        assert result["crm"] == "Bitrix24"

    def test_detect_salesforce(self, analyzer):
        html = '<script src="https://www.salesforce.com/form.js"></script>'
        result = analyzer._detect_crm(html)
        assert result["crm"] == "Salesforce"

    def test_no_crm(self, analyzer):
        html = '<html><body>No CRM</body></html>'
        result = analyzer._detect_crm(html)
        assert result["detected"] == False
        assert "теряют лиды" in result["business_context"]


class TestQuizLeadMagnetsDetection:
    """Test quiz and lead magnets detection"""

    def test_detect_quiz(self, analyzer):
        html = '<div class="quiz-container">Пройдите квиз</div>'
        result = analyzer._detect_quiz_lead_magnets(html)
        assert result["detected"] == True
        assert result["confidence"] == 0.7

    def test_detect_calculator(self, analyzer):
        html = '<div class="calculator">Калькулятор стоимости</div>'
        result = analyzer._detect_quiz_lead_magnets(html)
        assert result["detected"] == True

    def test_no_quiz(self, analyzer):
        html = '<html><body>No quiz</body></html>'
        result = analyzer._detect_quiz_lead_magnets(html)
        assert result["detected"] == False


class TestSocialProofDetection:
    """Test social proof detection"""

    def test_detect_reviews(self, analyzer):
        html = '<div class="reviews">Отзывы наших клиентов</div>'
        result = analyzer._detect_social_proof(html)
        assert "reviews" in result["elements"]
        assert result["count"] >= 1

    def test_detect_ratings(self, analyzer):
        html = '<div class="rating">★★★★★ 4.9/5</div>'
        result = analyzer._detect_social_proof(html)
        assert "ratings" in result["elements"]

    def test_detect_multiple_elements(self, analyzer):
        html = '''
        <div class="reviews">Отзывы</div>
        <div class="rating">★★★★★</div>
        <div class="clients">1000+ клиентов</div>
        '''
        result = analyzer._detect_social_proof(html)
        assert result["count"] >= 3

    def test_no_social_proof(self, analyzer):
        html = '<html><body>No social proof</body></html>'
        result = analyzer._detect_social_proof(html)
        assert result["count"] == 0


class TestGeoTargetingDetection:
    """Test geo-targeting detection"""

    def test_detect_geolocation(self, analyzer):
        html = '<script>detectGeolocation()</script>'
        result = analyzer._detect_geo_targeting(html)
        assert result["detected"] == True
        assert result["confidence"] == 0.8

    def test_detect_city_selector(self, analyzer):
        html = '<div class="city-selector">Ваш город: Москва</div>'
        result = analyzer._detect_geo_targeting(html)
        assert result["detected"] == True

    def test_no_geo_targeting(self, analyzer):
        html = '<html><body>No geo-targeting</body></html>'
        result = analyzer._detect_geo_targeting(html)
        assert result["detected"] == False


class TestPromoMechanicsDetection:
    """Test promotional mechanics detection"""

    def test_detect_discount(self, analyzer):
        html = '<div class="promo">Скидка 20%</div>'
        result = analyzer._detect_promo_mechanics(html)
        assert "discount" in result["mechanics"]
        assert result["count"] >= 1

    def test_detect_timer(self, analyzer):
        html = '<div class="countdown-timer">Осталось 2 часа</div>'
        result = analyzer._detect_promo_mechanics(html)
        assert "timer" in result["mechanics"]

    def test_detect_multiple_mechanics(self, analyzer):
        html = '''
        <div class="promo">Скидка 30%</div>
        <div class="timer">Осталось 1 час</div>
        <div class="popup">Успейте купить!</div>
        '''
        result = analyzer._detect_promo_mechanics(html)
        assert result["count"] >= 3

    def test_no_promo_mechanics(self, analyzer):
        html = '<html><body>No promo</body></html>'
        result = analyzer._detect_promo_mechanics(html)
        assert result["count"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
