# AIM/tests/services/ci/test_social_scanner.py
import pytest
from AIM.src.aim.services.ci.social_scanner import SocialScanner
from AIM.src.aim.services.ci.models import SocialScanResult, SocialProfile


class TestSocialScanner:
    def test_scan_returns_result(self):
        scanner = SocialScanner(timeout=5.0)
        result = scanner.scan("Юцковская")
        assert isinstance(result, SocialScanResult)
        assert result.company_name == "Юцковская"

    def test_scan_checks_platforms(self):
        scanner = SocialScanner(timeout=5.0)
        result = scanner.scan("Сбербанк")  # well-known, likely has social presence
        # At least one platform should report (exists=True or False, not error state)
        platforms_checked = (
            result.instagram is not None
            or result.telegram is not None
            or result.vk is not None
            or result.tiktok is not None
        )
        assert platforms_checked

    def test_scan_handles_unknown_company(self):
        scanner = SocialScanner(timeout=5.0)
        result = scanner.scan("абвгд-несуществующая-компания-12345")
        assert isinstance(result, SocialScanResult)
        assert result.error == ""  # no error, just not found

    def test_scan_cache_hit(self):
        scanner = SocialScanner(cache_ttl=3600)
        result1 = scanner.scan("Сбербанк")
        result2 = scanner.scan("Сбербанк")
        assert result1 is result2

    def test_close(self):
        scanner = SocialScanner()
        scanner.close()
        # Should not raise
