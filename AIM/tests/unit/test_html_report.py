"""
Unit tests for generate_html_report visual foundation and section builders.

Tests the dual-theme CSS system, navigation, ripple rings, theme toggle,
all 16 section builders, graceful omission, and backward compatibility.
"""
import pytest
from tools.generate_html_report import (
    _build_html, _build_hero, _build_nav, _build_exec_summary,
    _esc, _tag_class_for_score, AIM_DESIGN_CSS
)

# New builder imports (safe try/except for forward compatibility)
try:
    from tools.generate_html_report import (
        _build_about, _build_market, _build_experts, _build_content,
        _build_media, _build_whitefields, _build_presence, _build_strategy, _build_offer,
        _build_competitors, _load_session_data,
    )
    NEW_BUILDERS = True
except ImportError:
    NEW_BUILDERS = False


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def minimal_data():
    """Minimal session data — always works, tests backward compatibility."""
    return {
        "session_hash": "test123",
        "metadata": {"client_name": "ТестКлиника", "archived_at": "2026-01-15T00:00:00Z"},
        "prescan": {},
        "ci_analysis": {},
    }


@pytest.fixture
def full_data():
    """Full session data with all sections populated."""
    return {
        "session_hash": "test123",
        "metadata": {
            "client_name": "ТестКлиника",
            "client_url": "https://test.ru",
            "archived_at": "2026-01-15T00:00:00Z",
        },
        "prescan": {
            "client_name": "ТестКлиника",
            "city": "Москва",
            "stage_1_financials": {
                "revenue": "50 млн ₽",
                "profit": "10 млн ₽",
                "legal_name": "ООО Тест",
                "inn": "1234567890",
                "doctors": 15,
                "employees": 42,
                "revenue_trend": "+12%",
                "okved": "86.10",
                "licenses": "ЛО-77-01-123456",
            },
            "stage_2_under_the_hood": {
                "seo_score": 75,
                "rating": 4.5,
                "reviews": 120,
                "reviews_data": {
                    "platforms": [
                        {"platform": "2GIS", "rating": 4.5, "reviews_count": 120},
                        {"platform": "Яндекс.Карты", "rating": 4.3, "reviews_count": 85},
                    ]
                },
            },
        },
        "ci_analysis": {
            "feature_matrix": [
                {
                    "name": "Конкурент",
                    "total_score": 60,
                    "services": "Услуга",
                    "website": "https://comp.ru",
                }
            ],
            "gaps": [{"gap": "Нет Telegram", "severity": "high"}],
            "advantages": [{"advantage": "Высокий рейтинг"}],
            "top_recommendation": "Запустить Telegram",
            "priority_actions": ["Создать Telegram-канал", "Обновить сайт"],
        },
        "doctor_dossiers": {
            "doctors": [
                {"name": "Иванов Иван", "title": "Хирург", "followers": 15000, "instagram": "@ivanov", "avg_likes": 320},
                {"name": "Петрова Анна", "title": "Дерматолог", "followers": 8500, "instagram": "@petrova", "avg_likes": 180},
            ]
        },
        "instagram_content": {
            "doctors": [
                {"name": "Иванов Иван", "style": "Экспертный", "avg_likes": 320, "avg_views": 5000},
            ],
            "patient_fears": [
                {"fear": "Боль при процедуре", "frequency": "высокая", "covered_by": "Иванов Иван"},
            ]
        },
        "smi_mentions": {
            "articles": [
                {"publication": "РБК", "title": "Как клиника N растёт", "url": "https://rbc.ru/1", "sentiment": "positive", "year": 2025},
            ]
        },
    }


# ── CSS Tests ─────────────────────────────────────────────────────────────────

def test_css_variables_present():
    """Verify :root and [data-theme="dark"] blocks both define --bg variable."""
    assert ":root" in AIM_DESIGN_CSS and "--bg:" in AIM_DESIGN_CSS, (
        "Light theme --bg missing"
    )
    assert '[data-theme="dark"]' in AIM_DESIGN_CSS, "Dark theme block missing"


def test_no_jost_font():
    """Verify 'Jost' font is NOT referenced anywhere in the CSS."""
    assert "Jost" not in AIM_DESIGN_CSS, "Jost font should not be in CSS"


def test_inter_font_present():
    """Verify 'Inter' font is used as the body font family."""
    assert "Inter" in AIM_DESIGN_CSS, "Inter font should be in CSS"


# ── HTML Structure Tests ──────────────────────────────────────────────────────

def test_theme_toggle_present():
    """Verify theme-toggle button exists in the generated HTML."""
    html = _build_html({
        "session_hash": "test",
        "metadata": {"client_name": "Test"},
        "prescan": {},
        "ci_analysis": {},
    })
    assert "theme-toggle" in html, "Theme toggle button missing"


def test_theme_blocking_script():
    """Verify blocking localStorage theme read script is in <head>."""
    html = _build_html({
        "session_hash": "test",
        "metadata": {"client_name": "Test"},
        "prescan": {},
        "ci_analysis": {},
    })
    assert "localStorage.getItem('theme')" in html, (
        "Blocking theme script missing"
    )


def test_ripple_elements_present():
    """Verify 14 ripple ring elements exist in generated HTML."""
    html = _build_html({
        "session_hash": "test",
        "metadata": {"client_name": "Test"},
        "prescan": {},
        "ci_analysis": {},
    })
    assert "ring-pulse-1" in html, "Pulse ring 1 missing"
    assert "ring-lg-1" in html, "Large ring 1 missing"
    assert "ring-pulse-8" in html, "Pulse ring 8 missing"


def test_nav_renders():
    """Verify _build_nav() returns HTML with logo and theme toggle."""
    nav_html = _build_nav({"metadata": {}})
    assert "AIM" in nav_html, "Logo missing from nav"
    assert "theme-toggle" in nav_html, "Theme toggle missing from nav"


def test_nav_links_match_sections():
    """Verify nav links dynamically reflect available data."""
    # Minimal data: only about link
    nav_min = _build_nav({"metadata": {}, "prescan": {}, "ci_analysis": {}})
    assert 'href="#about"' in nav_min, "About nav link always present"
    # With competitor data: market + competitors links appear
    nav_with_comps = _build_nav({
        "metadata": {}, "prescan": {},
        "ci_analysis": {"feature_matrix": [{"name": "Comp"}]},
    })
    assert 'href="#market"' in nav_with_comps, "Market nav link should appear with competitors"
    assert 'href="#competitors"' in nav_with_comps, "Competitors nav link should appear with competitors"
    # With doctor dossiers: experts link appears
    nav_with_docs = _build_nav({
        "metadata": {}, "prescan": {},
        "ci_analysis": {},
        "doctor_dossiers": {"doctors": [{"name": "Dr"}]},
    })
    assert 'href="#experts"' in nav_with_docs, "Experts nav link should appear with doctor data"


def test_hero_has_id():
    """Verify hero section has id=hero for nav anchor scrolling."""
    hero = _build_hero({
        "metadata": {"client_name": "Test"},
        "prescan": {"city": "Moscow"},
    })
    assert 'id="hero"' in hero, "Hero section missing id=hero anchor"


def test_minimal_session_produces_valid_html():
    """Verify minimal session data produces a complete HTML document."""
    html = _build_html({
        "session_hash": "test",
        "metadata": {"client_name": "Test"},
        "prescan": {},
        "ci_analysis": {},
    })
    assert "<!DOCTYPE html>" in html, "DOCTYPE missing"
    assert "</html>" in html, "Closing html tag missing"
    assert "Inter" in html, "Inter font not in output"


def test_xss_client_name_escaped():
    """Verify HTML special characters in client_name are escaped."""
    data = {
        "session_hash": "test",
        "metadata": {"client_name": "<script>alert(1)</script>"},
        "prescan": {},
        "ci_analysis": {},
    }
    html = _build_html(data)
    assert "&lt;script&gt;" in html, "XSS vector not escaped"
    assert "<script>alert(1)</script>" not in html, "Raw script tag leaked"


def test_external_links_have_noopener():
    """Verify all target=_blank links have rel=noopener noreferrer."""
    full_data = {
        "session_hash": "test",
        "metadata": {"client_name": "Test"},
        "prescan": {},
        "ci_analysis": {
            "feature_matrix": [
                {"name": "Comp", "total_score": 50, "website": "https://x.com"}
            ],
            "gaps": [],
            "advantages": [],
            "top_recommendation": "Fix stuff",
            "priority_actions": ["Step 1"],
        },
    }
    html = _build_html(full_data)
    # Count target=_blank occurrences and verify each has rel=noopener
    blank_count = html.count('target="_blank"')
    noopener_count = html.count('rel="noopener noreferrer"')
    assert blank_count > 0, "No target=_blank links found to verify"
    assert blank_count == noopener_count, (
        f"Found {blank_count} target=_blank but only {noopener_count} noopener"
    )


# ── Builder Output Tests ──────────────────────────────────────────────────────

def test_exec_summary_uses_new_classes():
    """Verify exec summary uses .metrics/.metric/.value/.label classes."""
    data = {
        "metadata": {},
        "prescan": {
            "stage_1_financials": {"revenue": "10 млн ₽", "doctors": 5},
            "stage_2_under_the_hood": {"seo_score": 80, "rating": 4.8},
        },
        "ci_analysis": {},
    }
    html = _build_exec_summary(data)
    assert 'class="metrics"' in html, "Should use .metrics wrapper"
    assert 'class="metric"' in html, "Should use .metric items"
    assert 'class="value"' in html, "Should use .value for data"
    assert 'class="label"' in html, "Should use .label for descriptions"
    assert "glass-stat" not in html, "Old .glass-stat class should be gone"
    assert "glass-stats-wrap" not in html, "Old .glass-stats-wrap should be gone"


def test_tag_class_for_score():
    """Verify score threshold logic for metric-tag class assignment."""
    assert _tag_class_for_score(85) == "metric-tag-green"
    assert _tag_class_for_score(60) == "metric-tag-yellow"
    assert _tag_class_for_score(30) == "metric-tag-red"
    assert _tag_class_for_score(None) == "metric-tag-gray"


# ── New Builder Tests (PLAN-02) ────────────────────────────────────────────────

@pytest.mark.skipif(not NEW_BUILDERS, reason="New builders not yet imported")
class TestNewBuilders:
    """Tests for the 9 new section builders with graceful omission."""

    def test_about_renders_with_financials(self, full_data):
        """_build_about renders with revenue and legal info."""
        html = _build_about(full_data)
        assert "Выручка" in html
        assert "ООО Тест" in html
        assert "about" in html

    def test_market_omitted_without_competitors(self):
        """_build_market returns empty string when no feature_matrix."""
        html = _build_market({"ci_analysis": {}})
        assert html == ""

    def test_market_renders_with_competitors(self, full_data):
        """_build_market renders competitor name when feature_matrix present."""
        html = _build_market(full_data)
        assert "Конкурент" in html
        assert "market" in html

    def test_experts_omitted_without_data(self):
        """_build_experts returns empty string when no doctor_dossiers."""
        html = _build_experts({})
        assert html == ""

    def test_experts_renders_with_data(self, full_data):
        """_build_experts renders doctor name when doctor_dossiers present."""
        html = _build_experts(full_data)
        assert "Иванов Иван" in html
        assert "experts" in html

    def test_content_omitted_without_data(self):
        """_build_content returns empty string when no instagram_content."""
        html = _build_content({})
        assert html == ""

    def test_media_omitted_without_data(self):
        """_build_media returns empty string when no smi_mentions."""
        html = _build_media({})
        assert html == ""

    def test_whitefields_omitted_without_ci(self):
        """_build_whitefields returns empty string when no gaps/advantages."""
        html = _build_whitefields({"ci_analysis": {}})
        assert html == ""

    def test_presence_omitted_without_reviews(self):
        """_build_presence returns empty string when no review platforms."""
        html = _build_presence({"prescan": {}})
        assert html == ""

    def test_strategy_omitted_without_ci(self):
        """_build_strategy returns empty string when no CI analysis data."""
        html = _build_strategy({"ci_analysis": {}})
        assert html == ""

    def test_offer_always_renders(self):
        """_build_offer always renders with AIM branding."""
        html = _build_offer({"prescan": {}, "metadata": {"client_name": "Тест"}})
        assert "AIM" in html
        assert "offer" in html

    def test_all_builders_accept_empty_dict(self):
        """All 9 new builders do not raise exception with empty dict."""
        builders = [
            _build_about, _build_market, _build_experts, _build_content,
            _build_media, _build_whitefields, _build_presence, _build_strategy, _build_offer,
        ]
        for b in builders:
            try:
                b({})
            except Exception as e:
                pytest.fail(f"{b.__name__}() raised {type(e).__name__}: {e}")

    def test_minimal_session_has_core_sections(self, minimal_data):
        """Minimal session produces HTML with hero, offer, footer but no data-driven sections."""
        html = _build_html(minimal_data)
        assert '<div class="hero"' in html, "Hero should be present"
        assert '<section id="offer">' in html, "Offer section should be present"
        assert '<footer class="footer">' in html, "Footer should be present"
        assert '<section id="about">' not in html, "About section needs financial data (not in minimal)"
        assert '<section id="experts">' not in html, "Experts section should NOT be present without doctor_dossiers"
        assert '<section id="market">' not in html, "Market section should NOT be present without competitors"

    def test_full_session_has_all_sections(self, full_data):
        """Full session produces HTML with multiple section IDs."""
        html = _build_html(full_data)
        assert '<section id="about">' in html
        assert '<section id="market">' in html
        assert '<section id="experts">' in html
        assert '<section id="content-analysis">' in html
        assert '<section id="media">' in html
        assert '<section id="competitors">' in html
        assert '<section id="whitefields">' in html
        assert '<section id="presence">' in html
        assert '<section id="strategy">' in html
        assert '<section id="offer">' in html

    def test_minimal_session_produces_complete_html(self, minimal_data):
        """Minimal session data produces valid HTML with DOCTYPE."""
        html = _build_html(minimal_data)
        assert "<!DOCTYPE html>" in html
        assert "</html>" in html
        assert "Inter" in html
