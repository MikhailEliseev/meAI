"""
Technical SEO Analyzer for competitor content analysis.

Analyzes technical SEO factors: Core Web Vitals, mobile optimization, page speed, schema markup.
"""

import re
from typing import Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup


class TechnicalSEOAnalyzer:
    """
    Analyze technical SEO factors.

    Metrics:
    - Core Web Vitals (LCP, INP, CLS)
    - Mobile optimization
    - Page speed
    - Schema markup validation
    - HTTPS and security
    - Canonical tags
    - Meta robots
    - Structured data
    """

    def __init__(
        self,
        lcp_threshold: float = 2.5,
        inp_threshold: float = 200.0,
        cls_threshold: float = 0.1,
    ):
        """
        Initialize Technical SEO Analyzer.

        Args:
            lcp_threshold: Largest Contentful Paint threshold in seconds (default: 2.5s)
            inp_threshold: Interaction to Next Paint threshold in milliseconds (default: 200ms)
            cls_threshold: Cumulative Layout Shift threshold (default: 0.1)
        """
        self.lcp_threshold = lcp_threshold
        self.inp_threshold = inp_threshold
        self.cls_threshold = cls_threshold

    def analyze(self, html: str, url: str, metrics: Optional[dict] = None) -> dict:
        """
        Analyze technical SEO factors.

        Args:
            html: Raw HTML content
            url: Page URL
            metrics: Optional Core Web Vitals metrics from external tool (Lighthouse, PageSpeed Insights)

        Returns:
            Dictionary with technical SEO analysis results
        """
        soup = BeautifulSoup(html, "html.parser")

        # Core Web Vitals
        core_web_vitals = self._analyze_core_web_vitals(metrics) if metrics else None

        # Mobile optimization
        mobile_optimization = self._analyze_mobile_optimization(soup)

        # Page speed factors
        page_speed = self._analyze_page_speed_factors(soup, html)

        # Schema markup
        schema_markup = self._analyze_schema_markup(soup)

        # Security and HTTPS
        security = self._analyze_security(url, soup)

        # Meta tags
        meta_tags = self._analyze_meta_tags(soup)

        # Technical score
        technical_score = self._calculate_technical_score(
            core_web_vitals=core_web_vitals,
            mobile_optimization=mobile_optimization,
            page_speed=page_speed,
            schema_markup=schema_markup,
            security=security,
            meta_tags=meta_tags,
        )

        return {
            "core_web_vitals": core_web_vitals,
            "mobile_optimization": mobile_optimization,
            "page_speed": page_speed,
            "schema_markup": schema_markup,
            "security": security,
            "meta_tags": meta_tags,
            "technical_score": round(technical_score, 2),
            "technical_level": self._get_technical_level(technical_score),
        }

    def _analyze_core_web_vitals(self, metrics: dict) -> dict:
        """
        Analyze Core Web Vitals metrics.

        Metrics from Lighthouse or PageSpeed Insights:
        - LCP (Largest Contentful Paint): <2.5s good, 2.5-4s needs improvement, >4s poor
        - INP (Interaction to Next Paint): <200ms good, 200-500ms needs improvement, >500ms poor
        - CLS (Cumulative Layout Shift): <0.1 good, 0.1-0.25 needs improvement, >0.25 poor
        """
        lcp = metrics.get("lcp", 0)
        inp = metrics.get("inp", 0)
        cls = metrics.get("cls", 0)

        return {
            "lcp": {
                "value": lcp,
                "threshold": self.lcp_threshold,
                "status": "good" if lcp <= self.lcp_threshold else "needs_improvement" if lcp <= 4.0 else "poor",
                "unit": "seconds",
            },
            "inp": {
                "value": inp,
                "threshold": self.inp_threshold,
                "status": "good" if inp <= self.inp_threshold else "needs_improvement" if inp <= 500 else "poor",
                "unit": "milliseconds",
            },
            "cls": {
                "value": cls,
                "threshold": self.cls_threshold,
                "status": "good" if cls <= self.cls_threshold else "needs_improvement" if cls <= 0.25 else "poor",
                "unit": "score",
            },
            "overall_status": self._get_cwv_overall_status(lcp, inp, cls),
        }

    def _get_cwv_overall_status(self, lcp: float, inp: float, cls: float) -> str:
        """Get overall Core Web Vitals status."""
        lcp_good = lcp <= self.lcp_threshold
        inp_good = inp <= self.inp_threshold
        cls_good = cls <= self.cls_threshold

        if lcp_good and inp_good and cls_good:
            return "good"
        elif lcp > 4.0 or inp > 500 or cls > 0.25:
            return "poor"
        else:
            return "needs_improvement"

    def _analyze_mobile_optimization(self, soup: BeautifulSoup) -> dict:
        """
        Analyze mobile optimization.

        Checks:
        - Viewport meta tag
        - Responsive design indicators
        - Mobile-friendly font sizes
        - Touch target sizes
        """
        viewport = soup.find("meta", attrs={"name": "viewport"})
        has_viewport = viewport is not None

        viewport_content = viewport.get("content", "") if viewport else ""
        has_width_device = "width=device-width" in viewport_content
        has_initial_scale = "initial-scale=1" in viewport_content

        # Check for responsive design indicators
        has_media_queries = bool(
            soup.find_all("link", attrs={"media": re.compile(r"screen|only screen")})
        )

        # Check for mobile-specific meta tags
        has_mobile_web_app = soup.find("meta", attrs={"name": "mobile-web-app-capable"}) is not None
        has_apple_mobile = soup.find("meta", attrs={"name": "apple-mobile-web-app-capable"}) is not None

        mobile_score = 0
        if has_viewport:
            mobile_score += 40
        if has_width_device:
            mobile_score += 20
        if has_initial_scale:
            mobile_score += 20
        if has_media_queries:
            mobile_score += 10
        if has_mobile_web_app or has_apple_mobile:
            mobile_score += 10

        return {
            "has_viewport": has_viewport,
            "viewport_content": viewport_content,
            "has_width_device": has_width_device,
            "has_initial_scale": has_initial_scale,
            "has_media_queries": has_media_queries,
            "has_mobile_meta_tags": has_mobile_web_app or has_apple_mobile,
            "mobile_score": mobile_score,
            "mobile_friendly": mobile_score >= 60,
        }

    def _analyze_page_speed_factors(self, soup: BeautifulSoup, html: str) -> dict:
        """
        Analyze page speed factors.

        Checks:
        - Image optimization (lazy loading, srcset)
        - CSS/JS optimization (minification, async/defer)
        - Resource hints (preload, prefetch, preconnect)
        - Compression indicators
        """
        # Images
        images = soup.find_all("img")
        images_with_lazy = sum(1 for img in images if img.get("loading") == "lazy")
        images_with_srcset = sum(1 for img in images if img.get("srcset"))

        # Scripts
        scripts = soup.find_all("script")
        scripts_with_async = sum(1 for script in scripts if script.get("async") is not None)
        scripts_with_defer = sum(1 for script in scripts if script.get("defer") is not None)

        # Stylesheets
        stylesheets = soup.find_all("link", attrs={"rel": "stylesheet"})

        # Resource hints
        preload = soup.find_all("link", attrs={"rel": "preload"})
        prefetch = soup.find_all("link", attrs={"rel": "prefetch"})
        preconnect = soup.find_all("link", attrs={"rel": "preconnect"})
        dns_prefetch = soup.find_all("link", attrs={"rel": "dns-prefetch"})

        # HTML size
        html_size_kb = len(html.encode("utf-8")) / 1024

        return {
            "images": {
                "total": len(images),
                "with_lazy_loading": images_with_lazy,
                "with_srcset": images_with_srcset,
                "lazy_loading_percentage": round(images_with_lazy / len(images) * 100, 2) if images else 0,
            },
            "scripts": {
                "total": len(scripts),
                "with_async": scripts_with_async,
                "with_defer": scripts_with_defer,
                "optimized_percentage": round((scripts_with_async + scripts_with_defer) / len(scripts) * 100, 2) if scripts else 0,
            },
            "stylesheets": {
                "total": len(stylesheets),
            },
            "resource_hints": {
                "preload": len(preload),
                "prefetch": len(prefetch),
                "preconnect": len(preconnect),
                "dns_prefetch": len(dns_prefetch),
                "total": len(preload) + len(prefetch) + len(preconnect) + len(dns_prefetch),
            },
            "html_size_kb": round(html_size_kb, 2),
        }

    def _analyze_schema_markup(self, soup: BeautifulSoup) -> dict:
        """
        Analyze schema markup (structured data).

        Checks:
        - JSON-LD scripts
        - Microdata
        - RDFa
        - Schema types
        """
        # JSON-LD
        json_ld_scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
        has_json_ld = len(json_ld_scripts) > 0

        # Microdata
        microdata_items = soup.find_all(attrs={"itemscope": True})
        has_microdata = len(microdata_items) > 0

        # RDFa
        rdfa_items = soup.find_all(attrs={"typeof": True})
        has_rdfa = len(rdfa_items) > 0

        # Schema types (from itemtype or @type in JSON-LD)
        schema_types = set()
        for item in microdata_items:
            itemtype = item.get("itemtype", "")
            if itemtype:
                schema_types.add(itemtype.split("/")[-1])

        return {
            "has_json_ld": has_json_ld,
            "json_ld_count": len(json_ld_scripts),
            "has_microdata": has_microdata,
            "microdata_count": len(microdata_items),
            "has_rdfa": has_rdfa,
            "rdfa_count": len(rdfa_items),
            "schema_types": list(schema_types),
            "has_structured_data": has_json_ld or has_microdata or has_rdfa,
        }

    def _analyze_security(self, url: str, soup: BeautifulSoup) -> dict:
        """
        Analyze security factors.

        Checks:
        - HTTPS
        - Mixed content
        - Security headers (from meta tags)
        """
        parsed_url = urlparse(url)
        is_https = parsed_url.scheme == "https"

        # Check for mixed content (HTTP resources on HTTPS page)
        mixed_content = []
        if is_https:
            for tag in soup.find_all(["img", "script", "link", "iframe"]):
                src = tag.get("src") or tag.get("href")
                if src and src.startswith("http://"):
                    mixed_content.append(src)

        has_mixed_content = len(mixed_content) > 0

        # Security meta tags
        csp = soup.find("meta", attrs={"http-equiv": "Content-Security-Policy"})
        has_csp = csp is not None

        return {
            "is_https": is_https,
            "has_mixed_content": has_mixed_content,
            "mixed_content_count": len(mixed_content),
            "has_csp": has_csp,
            "security_score": 100 if is_https and not has_mixed_content else 50 if is_https else 0,
        }

    def _analyze_meta_tags(self, soup: BeautifulSoup) -> dict:
        """
        Analyze important meta tags.

        Checks:
        - Canonical tag
        - Meta robots
        - Alternate tags (hreflang)
        """
        canonical = soup.find("link", attrs={"rel": "canonical"})
        has_canonical = canonical is not None
        canonical_url = canonical.get("href") if canonical else None

        robots = soup.find("meta", attrs={"name": "robots"})
        has_robots = robots is not None
        robots_content = robots.get("content", "") if robots else ""

        # Hreflang tags
        hreflang_tags = soup.find_all("link", attrs={"rel": "alternate", "hreflang": True})
        has_hreflang = len(hreflang_tags) > 0

        return {
            "has_canonical": has_canonical,
            "canonical_url": canonical_url,
            "has_robots": has_robots,
            "robots_content": robots_content,
            "has_hreflang": has_hreflang,
            "hreflang_count": len(hreflang_tags),
        }

    def _calculate_technical_score(
        self,
        core_web_vitals: Optional[dict],
        mobile_optimization: dict,
        page_speed: dict,
        schema_markup: dict,
        security: dict,
        meta_tags: dict,
    ) -> float:
        """
        Calculate overall technical SEO score.

        Weighted components:
        - Core Web Vitals: 30% (if available)
        - Mobile optimization: 20%
        - Page speed factors: 20%
        - Schema markup: 15%
        - Security: 10%
        - Meta tags: 5%
        """
        score = 0.0

        # Core Web Vitals (30%)
        if core_web_vitals:
            cwv_status = core_web_vitals["overall_status"]
            if cwv_status == "good":
                score += 30.0
            elif cwv_status == "needs_improvement":
                score += 15.0
            else:
                score += 0.0
        else:
            # If no CWV data, redistribute weight to other factors
            pass

        # Mobile optimization (20%)
        score += mobile_optimization["mobile_score"] * 0.20

        # Page speed factors (20%)
        page_speed_score = 0.0
        # Images optimization
        if page_speed["images"]["total"] > 0:
            page_speed_score += page_speed["images"]["lazy_loading_percentage"] * 0.3
        # Scripts optimization
        if page_speed["scripts"]["total"] > 0:
            page_speed_score += page_speed["scripts"]["optimized_percentage"] * 0.3
        # Resource hints
        if page_speed["resource_hints"]["total"] > 0:
            page_speed_score += min(page_speed["resource_hints"]["total"] * 10, 40)

        score += min(page_speed_score, 20.0)

        # Schema markup (15%)
        if schema_markup["has_structured_data"]:
            schema_score = 0.0
            if schema_markup["has_json_ld"]:
                schema_score += 10.0
            if schema_markup["has_microdata"]:
                schema_score += 3.0
            if schema_markup["has_rdfa"]:
                schema_score += 2.0
            score += min(schema_score, 15.0)

        # Security (10%)
        score += security["security_score"] * 0.10

        # Meta tags (5%)
        meta_score = 0.0
        if meta_tags["has_canonical"]:
            meta_score += 2.0
        if meta_tags["has_robots"]:
            meta_score += 1.5
        if meta_tags["has_hreflang"]:
            meta_score += 1.5
        score += meta_score

        return max(0.0, min(100.0, score))

    def _get_technical_level(self, score: float) -> str:
        """Get technical SEO level description."""
        if score >= 80:
            return "excellent"
        elif score >= 60:
            return "good"
        elif score >= 40:
            return "fair"
        else:
            return "poor"
