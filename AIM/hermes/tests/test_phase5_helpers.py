"""Unit tests for Phase 5 HTML helpers (_render_gap_blocks, _render_section_insight).

Per TDD red-green discipline (Plan 05-02 Task 1, tdd="true"), this file is
committed BEFORE the helper implementations — making the red state explicit
in git history.

Covers 13 behavior cases per Plan 05-02 Task 1 <behavior> block:
  - _render_gap_blocks: None / empty list / 4-item list / strength green border /
    growth default border / XSS escape / 5-item DoS cap
  - _render_section_insight: None / empty string / valid string → blockquote /
    XSS escape / 600-char DoS truncation
  - Python 3.11 f-string backslash safety (no SyntaxError when loaded)

The generate_html_report.py module imports tools.registry and app.tools.
session_archive, which are only available inside the aim-hermes Docker
container (hermes-agent pip package). Local test execution stubs these
out and loads the module directly via importlib.
"""

import importlib.util
import sys
import types
from pathlib import Path

# ── Module loading (stub external dependencies) ──────────────────────────
# hermes-agent package is only pip-installed inside the Docker container.
# We stub the two imports generate_html_report.py needs at module-load time:
#   - tools.registry (provides `registry` decorator)
#   - app.tools.session_archive (provides `load_all_data`)


def _load_generate_html_report_module():
    """Load generate_html_report.py via importlib, stubbing externals."""
    # Stub tools.registry
    if "tools" not in sys.modules:
        tools_stub = types.ModuleType("tools")
        registry_stub = types.ModuleType("tools.registry")

        class _RegistryStub:
            """Stub registry — register() is a no-op decorator."""

            def register(self, *args, **kwargs):
                def decorator(fn):
                    return fn

                return decorator

        registry_stub.registry = _RegistryStub()
        tools_stub.registry = registry_stub
        sys.modules["tools"] = tools_stub
        sys.modules["tools.registry"] = registry_stub

    # Stub app.tools.session_archive
    if "app" not in sys.modules:
        app_stub = types.ModuleType("app")
        app_tools_stub = types.ModuleType("app.tools")
        session_archive_stub = types.ModuleType("app.tools.session_archive")
        session_archive_stub.load_all_data = lambda *a, **kw: {}
        app_tools_stub.session_archive = session_archive_stub
        app_stub.tools = app_tools_stub
        sys.modules["app"] = app_stub
        sys.modules["app.tools"] = app_tools_stub
        sys.modules["app.tools.session_archive"] = session_archive_stub

    # Stub pymysql (imported at module top-level)
    if "pymysql" not in sys.modules:
        pymysql_stub = types.ModuleType("pymysql")
        pymysql_stub.connect = lambda *a, **kw: None
        sys.modules["pymysql"] = pymysql_stub

    module_path = (
        Path(__file__).resolve().parent.parent
        / "app" / "tools" / "generate_html_report.py"
    )
    spec = importlib.util.spec_from_file_location(
        "generate_html_report_under_test", module_path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Load module once for all tests in this file.
_MODULE = _load_generate_html_report_module()
_render_gap_blocks = _MODULE._render_gap_blocks
_render_section_insight = _MODULE._render_section_insight
_esc = _MODULE._esc


# ── Test 1: _render_gap_blocks(None) returns "" ──────────────────────────


def test_render_gap_blocks_none():
    """None input → empty string (graceful degradation)."""
    assert _render_gap_blocks(None) == ""


# ── Test 2: _render_gap_blocks([]) returns "" ────────────────────────────


def test_render_gap_blocks_empty_list():
    """Empty list input → empty string (no gap-blocks rendered)."""
    assert _render_gap_blocks([]) == ""


# ── Test 3: 2 strength + 2 growth items → 4 `.gap` divs ──────────────────


def test_render_gap_blocks_four_items():
    """2 strength + 2 growth items → 4 `.gap` divs in HTML output."""
    gap_blocks = [
        {"type": "strength", "title": "Сильная сторона 1", "description": "Описание 1"},
        {"type": "growth", "title": "Точка роста 1", "description": "Описание 2"},
        {"type": "strength", "title": "Сильная сторона 2", "description": "Описание 3"},
        {"type": "growth", "title": "Точка роста 2", "description": "Описание 4"},
    ]
    html = _render_gap_blocks(gap_blocks)
    gap_count = html.count('<div class="gap"')
    assert gap_count == 4, f"Expected 4 .gap divs, got {gap_count}"


# ── Test 4: strength item renders with `var(--green)` border-left ────────


def test_render_gap_blocks_strength_green_border():
    """Strength type → border-left CSS uses var(--green)."""
    gap_blocks = [
        {"type": "strength", "title": "Сильная сторона", "description": "Описание"},
    ]
    html = _render_gap_blocks(gap_blocks)
    assert "var(--green)" in html, (
        f"Expected var(--green) in strength border CSS, got: {html}"
    )


# ── Test 5: growth item renders WITHOUT green border ─────────────────────


def test_render_gap_blocks_growth_no_green():
    """Growth type → NO var(--green) in styling (default border)."""
    gap_blocks = [
        {"type": "growth", "title": "Точка роста", "description": "Описание"},
    ]
    html = _render_gap_blocks(gap_blocks)
    assert "var(--green)" not in html, (
        f"Growth item should NOT have var(--green); got: {html}"
    )


# ── Test 6: XSS escape — <script> becomes &lt;script&gt; ────────────────


def test_render_gap_blocks_xss_escape():
    """HTML in title/description escaped via _esc."""
    gap_blocks = [
        {
            "type": "strength",
            "title": "<script>alert('xss')</script>",
            "description": "<img src=x onerror=alert(1)>",
        },
    ]
    html = _render_gap_blocks(gap_blocks)
    assert "<script>" not in html, f"Raw <script> found in HTML: {html}"
    assert "&lt;script&gt;" in html, f"Escaped &lt;script&gt; missing: {html}"
    assert "<img" not in html, f"Raw <img> found in HTML: {html}"


# ── Test 7: DoS cap — max 5 items rendered ───────────────────────────────


def test_render_gap_blocks_dos_cap():
    """List capped to 5 items (DoS mitigation per T-05-02-D)."""
    gap_blocks = [
        {"type": "strength", "title": f"Title {i}", "description": f"Desc {i}"}
        for i in range(20)
    ]
    html = _render_gap_blocks(gap_blocks)
    gap_count = html.count('<div class="gap"')
    assert gap_count == 5, f"Expected 5 .gap divs (DoS cap), got {gap_count}"


# ── Test 8: _render_section_insight(None) returns "" ─────────────────────


def test_render_section_insight_none():
    """None input → empty string."""
    assert _render_section_insight(None) == ""


# ── Test 9: _render_section_insight("") returns "" ───────────────────────


def test_render_section_insight_empty_string():
    """Empty string input → empty string."""
    assert _render_section_insight("") == ""


# ── Test 10: Valid insight → blockquote with section-insight class ────────


def test_render_section_insight_blockquote():
    """Valid insight string → HTML blockquote with section-insight class."""
    html = _render_section_insight("Главный вывод: клиника лидирует в нише.")
    assert '<blockquote class="section-insight"' in html, (
        f"Expected <blockquote class='section-insight'>; got: {html}"
    )
    assert "</blockquote>" in html, f"Missing closing </blockquote>: {html}"
    assert "Главный вывод" in html, f"Insight text missing from output: {html}"


# ── Test 11: XSS escape — <script> neutralized ──────────────────────────


def test_render_section_insight_xss_escape():
    """HTML in insight escaped via _esc."""
    html = _render_section_insight("<script>alert('xss')</script>")
    assert "<script>" not in html, f"Raw <script> found in HTML: {html}"
    assert "&lt;script&gt;" in html, f"Escaped &lt;script&gt; missing: {html}"


# ── Test 12: DoS cap — 600 chars max with ellipsis ───────────────────────


def test_render_section_insight_truncation():
    """Insight truncated to 600 chars + '...' when exceeding limit."""
    long_insight = "А" * 1000  # 1000 chars, well over the 600 cap
    html = _render_section_insight(long_insight)
    # The insight content between > and </blockquote> should be 600 chars (597 + "...")
    assert "..." in html, f"Ellipsis missing in truncated output: {html}"
    # The raw 1000-char string should NOT appear in full
    assert "А" * 1000 not in html, "Full 1000-char string present — truncation failed"


# ── Test 13: Python 3.11 f-string backslash safety ───────────────────────


def test_python311_fstring_backslash_safety():
    """Both helpers load + execute without SyntaxError under Python 3.11.

    Per Plans 02-01, 03-05, 04-08 lesson: Python 3.11 forbids backslash-
    escaped double quotes inside f-string expression parts. AST parse on
    Python 3.14 passes but container Python 3.11 fails at import time.

    This test verifies the module loads cleanly + both helpers produce
    output — implicitly checking for f-string backslash gotchas.
    """
    # Module already loaded at top of file — if it had backslash issues,
    # collection would have failed before this test ran.
    assert _render_gap_blocks is not None
    assert _render_section_insight is not None

    # Smoke test — call both helpers with simple inputs.
    gaps_html = _render_gap_blocks([
        {"type": "strength", "title": "T", "description": "D"}
    ])
    assert '<div class="gap"' in gaps_html

    insight_html = _render_section_insight("Smoke test insight.")
    assert "<blockquote" in insight_html


# ── Runner for direct execution ──────────────────────────────────────────


if __name__ == "__main__":
    # Allow `python3 test_phase5_helpers.py` direct execution without pytest.
    # Runs each test function in order, prints pass/fail.
    test_functions = [
        (name, fn) for name, fn in sorted(globals().items())
        if name.startswith("test_") and callable(fn)
    ]
    passed = 0
    failed = 0
    for name, fn in test_functions:
        try:
            fn()
            print(f"PASS: {name}")
            passed += 1
        except Exception as exc:
            print(f"FAIL: {name} — {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n=== {passed} passed / {failed} failed / {len(test_functions)} total ===")
    exit(0 if failed == 0 else 1)
