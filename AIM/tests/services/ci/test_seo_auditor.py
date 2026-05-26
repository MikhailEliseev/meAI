import pytest
from AIM.src.aim.services.ci.seo_auditor import SeoAuditor
from AIM.src.aim.services.ci.models import SeoAuditResult


class TestSeoAuditor:
    def test_audit_extracts_title(self):
        auditor = SeoAuditor()
        try:
            result = auditor.audit("https://example.com")
            assert isinstance(result, SeoAuditResult)
            assert len(result.title) > 0
        finally:
            auditor.close()

    def test_audit_checks_ssl(self):
        auditor = SeoAuditor()
        try:
            result = auditor.audit("https://example.com")
            assert result.has_ssl is True
        finally:
            auditor.close()

    def test_audit_scores_perfect_site(self):
        auditor = SeoAuditor()
        try:
            result = auditor.audit("https://example.com")
            assert 0 <= result.score <= 100
        finally:
            auditor.close()

    def test_audit_detects_missing_meta(self):
        auditor = SeoAuditor()
        try:
            result = auditor.audit("https://example.com")
            assert isinstance(result.meta_description, str)
        finally:
            auditor.close()

    def test_audit_handles_http_error(self):
        auditor = SeoAuditor(timeout=3.0)
        try:
            result = auditor.audit("https://nonexistent-domain-12345.com")
            assert result.error != ""
        finally:
            auditor.close()

    def test_audit_cache_hit(self):
        auditor = SeoAuditor(cache_ttl=3600)
        try:
            result1 = auditor.audit("https://example.com")
            result2 = auditor.audit("https://example.com")
            assert result1 is result2
        finally:
            auditor.close()

    def test_close_cleans_up(self):
        auditor = SeoAuditor()
        auditor.close()
        # Should not raise
