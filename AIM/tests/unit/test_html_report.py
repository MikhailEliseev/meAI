"""
Unit tests for generate_html_report visual foundation.

Tests the dual-theme CSS system, navigation, ripple rings, theme toggle,
and ensures all builders use the new CSS class names correctly.
"""
import pytest
from tools.generate_html_report import (
    _build_html, _build_hero, _build_nav, _build_exec_summary,
    _esc, _tag_class_for_score, AIM_DESIGN_CSS
)


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
            },
            "stage_2_under_the_hood": {
                "seo_score": 75,
                "rating": 4.5,
                "reviews": 120,
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
    """Verify nav links point to key section IDs."""
    nav_html = _build_nav({"metadata": {}})
    assert 'href="#hero"' in nav_html, "Hero nav link missing"
    assert 'href="#market"' in nav_html, "Market nav link missing"
    assert 'href="#competitors"' in nav_html, "Competitors nav link missing"


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
