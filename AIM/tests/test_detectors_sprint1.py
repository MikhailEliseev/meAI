"""
Unit tests for Sprint 1 Business-Oriented Detectors

Tests 10 new detectors:
1. CMS Detection
2. Analytics Detection
3. Call Tracking Detection
4. Live Chat Detection
5. Messengers Detection
6. Booking Systems Detection
7. Payment Systems Detection
8. CDN Detection
9. Hosting Detection
10. A/B Testing Detection
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


class TestCMSDetection:
    """Test CMS detection"""

    def test_detect_wordpress(self, analyzer):
        html = '<link href="/wp-content/themes/mytheme/style.css">'
        result = analyzer._detect_cms(html, {})
        assert result["cms"] == "WordPress"
        assert result["confidence"] >= 0.5
        assert "wp-content" in result["evidence"]

    def test_detect_bitrix(self, analyzer):
        html = '<script src="/bitrix/templates/main/script.js"></script>'
        result = analyzer._detect_cms(html, {})
        assert result["cms"] == "Bitrix"
        assert result["confidence"] >= 0.5

    def test_detect_bitrix_from_header(self, analyzer):
        html = '<html></html>'
        headers = {'X-Powered-By': '1C-Bitrix'}
        result = analyzer._detect_cms(html, headers)
        assert result["cms"] == "Bitrix"
        assert result["confidence"] == 1.0

    def test_detect_tilda(self, analyzer):
        html = '<script src="https://tilda.cc/js/tilda.js"></script>'
        result = analyzer._detect_cms(html, {})
        assert result["cms"] == "Tilda"
        assert result["confidence"] >= 0.5

    def test_detect_custom(self, analyzer):
        html = '<html><body>Custom site</body></html>'
        result = analyzer._detect_cms(html, {})
        assert result["cms"] == "Custom"
        assert result["confidence"] == 0.5


class TestAnalyticsDetection:
    """Test analytics detection"""

    def test_detect_google_analytics(self, analyzer):
        html = '<script>gtag("config", "G-ABC123")</script>'
        result = analyzer._detect_analytics(html)
        assert result["analytics"]["google_analytics"]["detected"] == True
        assert result["analytics"]["google_analytics"]["confidence"] > 0

    def test_detect_yandex_metrika(self, analyzer):
        html = '<script src="https://mc.yandex.ru/metrika/tag.js"></script>'
        result = analyzer._detect_analytics(html)
        assert result["analytics"]["yandex_metrika"]["detected"] == True

    def test_detect_multiple_analytics(self, analyzer):
        html = '''
        <script>gtag("config", "G-ABC123")</script>
        <script src="https://mc.yandex.ru/metrika/tag.js"></script>
        '''
        result = analyzer._detect_analytics(html)
        assert result["analytics"]["google_analytics"]["detected"] == True
        assert result["analytics"]["yandex_metrika"]["detected"] == True
        assert "Полный стек" in result["business_context"]

    def test_no_analytics(self, analyzer):
        html = '<html><body>No analytics</body></html>'
        result = analyzer._detect_analytics(html)
        assert result["analytics"]["google_analytics"]["detected"] == False
        assert "не обнаружена" in result["business_context"]


class TestCallTrackingDetection:
    """Test call tracking detection"""

    def test_detect_calltouch(self, analyzer):
        html = '<script src="https://calltouch.ru/widget.js"></script>'
        result = analyzer._detect_call_tracking(html)
        assert result["provider"] == "Calltouch"
        assert result["detected"] == True
        assert result["confidence"] > 0

    def test_detect_callibri(self, analyzer):
        html = '<div class="clbr-widget"></div>'
        result = analyzer._detect_call_tracking(html)
        assert result["provider"] == "Callibri"
        assert result["detected"] == True

    def test_no_call_tracking(self, analyzer):
        html = '<html><body>No call tracking</body></html>'
        result = analyzer._detect_call_tracking(html)
        assert result["detected"] == False
        assert "теряют" in result["business_context"]


class TestLiveChatDetection:
    """Test live chat detection"""

    def test_detect_jivo(self, analyzer):
        html = '<script src="//code.jivosite.com/widget.js"></script>'
        result = analyzer._detect_live_chat(html)
        assert result["provider"] == "Jivo"
        assert result["detected"] == True

    def test_detect_carrot(self, analyzer):
        html = '<script>carrotquest.init()</script>'
        result = analyzer._detect_live_chat(html)
        assert result["provider"] == "Carrot"
        assert result["detected"] == True

    def test_no_live_chat(self, analyzer):
        html = '<html><body>No chat</body></html>'
        result = analyzer._detect_live_chat(html)
        assert result["detected"] == False


class TestMessengersDetection:
    """Test messengers detection"""

    def test_detect_whatsapp(self, analyzer):
        html = '<a href="https://wa.me/79991234567">WhatsApp</a>'
        result = analyzer._detect_messengers(html)
        assert "WhatsApp" in result["messengers"]
        assert result["count"] == 1

    def test_detect_telegram(self, analyzer):
        html = '<a href="https://t.me/username">Telegram</a>'
        result = analyzer._detect_messengers(html)
        assert "Telegram" in result["messengers"]

    def test_detect_multiple_messengers(self, analyzer):
        html = '''
        <a href="https://wa.me/79991234567">WhatsApp</a>
        <a href="https://t.me/username">Telegram</a>
        '''
        result = analyzer._detect_messengers(html)
        assert result["count"] == 2
        assert "WhatsApp" in result["messengers"]
        assert "Telegram" in result["messengers"]

    def test_no_messengers(self, analyzer):
        html = '<html><body>No messengers</body></html>'
        result = analyzer._detect_messengers(html)
        assert result["count"] == 0


class TestBookingSystemsDetection:
    """Test booking systems detection"""

    def test_detect_yclients(self, analyzer):
        html = '<iframe src="https://n237778.yclients.com/"></iframe>'
        result = analyzer._detect_booking_systems(html)
        assert result["system"] == "YCLIENTS"
        assert result["detected"] == True

    def test_detect_dikidi(self, analyzer):
        html = '<script src="https://dikidi.ru/widget.js"></script>'
        result = analyzer._detect_booking_systems(html)
        assert result["system"] == "Dikidi"
        assert result["detected"] == True

    def test_no_booking(self, analyzer):
        html = '<html><body>No booking</body></html>'
        result = analyzer._detect_booking_systems(html)
        assert result["detected"] == False


class TestPaymentSystemsDetection:
    """Test payment systems detection"""

    def test_detect_yandex_kassa(self, analyzer):
        html = '<script src="https://yookassa.ru/checkout.js"></script>'
        result = analyzer._detect_payment_systems(html)
        assert "Yandex.Kassa" in result["systems"]
        assert result["count"] >= 1

    def test_detect_stripe(self, analyzer):
        html = '<script src="https://js.stripe.com/v3/"></script>'
        result = analyzer._detect_payment_systems(html)
        assert "Stripe" in result["systems"]

    def test_no_payment(self, analyzer):
        html = '<html><body>No payment</body></html>'
        result = analyzer._detect_payment_systems(html)
        assert result["count"] == 0


class TestCDNDetection:
    """Test CDN detection"""

    def test_detect_cloudflare(self, analyzer):
        html = '<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery.js"></script>'
        result = analyzer._detect_cdn(html)
        assert result["provider"] == "Cloudflare"
        assert result["detected"] == True

    def test_detect_cloudfront(self, analyzer):
        html = '<img src="https://d111111abcdef8.cloudfront.net/image.jpg">'
        result = analyzer._detect_cdn(html)
        assert result["provider"] == "CloudFront"
        assert result["detected"] == True

    def test_no_cdn(self, analyzer):
        html = '<html><body>No CDN</body></html>'
        result = analyzer._detect_cdn(html)
        assert result["detected"] == False


class TestHostingDetection:
    """Test hosting detection"""

    def test_detect_from_html(self, analyzer):
        html = '<script src="https://example.beget.com/script.js"></script>'
        result = analyzer._detect_hosting(html, {})
        assert result["provider"] == "Beget"
        assert result["confidence"] == 0.6

    def test_detect_from_header(self, analyzer):
        html = '<html></html>'
        headers = {'Server': 'cloudflare'}
        result = analyzer._detect_hosting(html, headers)
        assert result["provider"] == "Cloudflare"
        assert result["confidence"] == 0.9

    def test_no_hosting_detected(self, analyzer):
        html = '<html><body>Unknown hosting</body></html>'
        result = analyzer._detect_hosting(html, {})
        assert result["detected"] == False
        assert result["confidence"] == 0.3


class TestABTestingDetection:
    """Test A/B testing detection"""

    def test_detect_google_optimize(self, analyzer):
        html = '<script src="https://www.googleoptimize.com/optimize.js"></script>'
        result = analyzer._detect_ab_testing(html)
        assert result["tool"] == "Google Optimize"
        assert result["detected"] == True

    def test_detect_vwo(self, analyzer):
        html = '<script src="https://dev.visualwebsiteoptimizer.com/lib.js"></script>'
        result = analyzer._detect_ab_testing(html)
        assert result["tool"] == "VWO"
        assert result["detected"] == True

    def test_no_ab_testing(self, analyzer):
        html = '<html><body>No A/B testing</body></html>'
        result = analyzer._detect_ab_testing(html)
        assert result["detected"] == False


class TestErrorHandling:
    """Test error handling in detectors"""

    def test_safe_detector_call_success(self, analyzer):
        def dummy_detector(html):
            return {"result": "success"}

        result = analyzer._safe_detector_call(dummy_detector, "<html></html>")
        assert result["result"] == "success"

    def test_safe_detector_call_failure(self, analyzer):
        def failing_detector(html):
            raise ValueError("Test error")

        result = analyzer._safe_detector_call(failing_detector, "<html></html>")
        assert "error" in result
        assert result["confidence"] == 0.0
        assert result["detector"] == "failing_detector"


class TestSecurityHelpers:
    """Test security helper methods"""

    def test_escape_html(self, analyzer):
        dangerous = '<script>alert("XSS")</script>'
        safe = analyzer._escape_html(dangerous)
        assert "&lt;script&gt;" in safe
        assert "<script>" not in safe

    def test_escape_html_empty(self, analyzer):
        result = analyzer._escape_html("")
        assert result == ""

    def test_escape_html_none(self, analyzer):
        result = analyzer._escape_html(None)
        assert result == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
