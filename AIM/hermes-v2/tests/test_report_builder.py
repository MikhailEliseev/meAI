"""Тесты для report_builder v2 — новый генератор отчётов.

Покрывает:
- build_data_dict: адаптация collected_results → data dict
- _build_hero_meta: извлечение метаданных для hero
- build_report_html: структурные проверки (nav, hero, ripple, секции, CTA)
- Edge cases: пустые данные, отсутствующие ключи, fallback
"""

import json

import pytest

from app.report_builder.adapter import (
    _build_hero_meta,
    _safe_load_json,
    build_data_dict,
)
from app.report_builder.builder import (
    _build_hero_html,
    _build_nav_html,
    _build_ripple_html,
    build_report_html,
)
from app.report_builder.css import _CANONICAL_CSS, get_fonts_import


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────

def _profile_raw(**overrides) -> str:
    """Стандартный profile JSON для тестов."""
    base = {
        "company_name": "Test Clinic",
        "inn": "7700000000",
        "city": "Москва",
        "address": "ул. Тестовая, 1",
        "doctors_count": 10,
        "registration_date": "2018-05-10",
        "okved": "86.10",
    }
    base.update(overrides)
    return json.dumps(base, ensure_ascii=False)


def _finance_raw(revenue=100_000_000, profit=10_000_000) -> str:
    return json.dumps(
        {"revenue": revenue, "profit": profit, "revenue_trend": "growing"},
        ensure_ascii=False,
    )


def _reviews_raw(rating=4.5, reviews=100) -> str:
    return json.dumps(
        {
            "platforms": {
                "yandex": {"rating": rating, "reviews": reviews},
                "twogis": {"rating": 4.4, "reviews": 20},
            }
        },
        ensure_ascii=False,
    )


def _competitors_raw() -> str:
    return json.dumps(
        {
            "competitors": [
                {"brand_name": "Comp 1", "revenue_year": 200_000_000, "revenue_trend": "growing"},
                {"brand_name": "Comp 2", "revenue_year": 50_000_000, "revenue_trend": "stable"},
            ]
        },
        ensure_ascii=False,
    )


# ──────────────────────────────────────────────────────────────────────────
# _safe_load_json
# ──────────────────────────────────────────────────────────────────────────

def test_safe_load_json_valid():
    assert _safe_load_json('{"a": 1}') == {"a": 1}


def test_safe_load_json_invalid():
    assert _safe_load_json("not json") is None
    assert _safe_load_json("") is None
    assert _safe_load_json(None) is None


# ──────────────────────────────────────────────────────────────────────────
# _build_hero_meta
# ──────────────────────────────────────────────────────────────────────────

def test_hero_meta_full_data():
    """Все источники данных — full hero_meta."""
    meta = _build_hero_meta(
        profile_raw=_profile_raw(),
        finance_raw=_finance_raw(revenue=380_000_000),
        reviews_raw=_reviews_raw(rating=5.0, reviews=562),
        profile_cache={"city": "Москва", "url": "https://test.ru"},
        company_name="Test Clinic",
    )
    assert meta["city"] == "Москва"
    assert meta["address"] == "ул. Тестовая, 1"
    assert meta["doctors_count"] == 10
    assert meta["founded_year"] == "2018"
    assert meta["rating"] == 5.0
    assert meta["reviews_count"] == 562
    assert "380 млн" in meta["revenue_str"]
    assert "5.0★" in meta["subtitle"]
    assert "562 отзывов" in meta["subtitle"]


def test_hero_meta_empty_data():
    """Пустые все источники — fallback subtitle, пустые поля."""
    meta = _build_hero_meta(
        profile_raw="{}",
        finance_raw="{}",
        reviews_raw="{}",
        profile_cache={},
        company_name="Test",
    )
    assert meta["city"] == ""
    assert meta["doctors_count"] is None
    assert meta["rating"] is None
    assert meta["revenue_str"] == ""
    assert meta["subtitle"] == "Маркетинговый аудит и точки роста"


def test_hero_meta_invalid_json():
    """Невалидный JSON — не падаем, возвращаем пустые поля."""
    meta = _build_hero_meta(
        profile_raw="not json",
        finance_raw="also not json",
        reviews_raw="{}",
        profile_cache={},
        company_name="Test",
    )
    assert meta["city"] == ""
    assert meta["doctors_count"] is None


def test_hero_meta_revenue_billions():
    """Выручка > 1 млрд — форматирование 'млрд ₽'."""
    meta = _build_hero_meta(
        profile_raw="{}",
        finance_raw=_finance_raw(revenue=4_300_000_000),
        reviews_raw="{}",
        profile_cache={},
        company_name="Test",
    )
    assert "4.3 млрд" in meta["revenue_str"]


def test_hero_meta_profile_cache_priority():
    """profile_cache имеет приоритет над extract_clinic_profile для city."""
    meta = _build_hero_meta(
        profile_raw=_profile_raw(city="Казань"),
        finance_raw="{}",
        reviews_raw="{}",
        profile_cache={"city": "Москва"},
        company_name="Test",
    )
    assert meta["city"] == "Москва"


def test_hero_meta_fallback_to_profile_json():
    """Если в profile_cache нет city — берём из extract_clinic_profile."""
    meta = _build_hero_meta(
        profile_raw=_profile_raw(city="Екатеринбург"),
        finance_raw="{}",
        reviews_raw="{}",
        profile_cache={},
        company_name="Test",
    )
    assert meta["city"] == "Екатеринбург"


# ──────────────────────────────────────────────────────────────────────────
# build_data_dict
# ──────────────────────────────────────────────────────────────────────────

def test_build_data_dict_metadata():
    """metadata извлекается из profile_cache."""
    data = build_data_dict({}, {"company_name": "ACME", "url": "https://acme.ru", "inn": "123"}, "")
    assert data["metadata"]["company_name"] == "ACME"
    assert data["metadata"]["url"] == "https://acme.ru"
    assert data["metadata"]["inn"] == "123"


def test_build_data_dict_hero_meta_present():
    """hero_meta всегда есть (может быть с пустыми полями)."""
    data = build_data_dict({}, {}, "")
    assert "hero_meta" in data
    assert isinstance(data["hero_meta"], dict)


def test_build_data_dict_nav_sections_filtered():
    """nav_sections содержит только те секции, для которых есть контент."""
    data = build_data_dict(
        {"extract_clinic_profile": _profile_raw()},
        {"company_name": "Test"},
        "llm analysis text",
    )
    nav = data["hero_meta"]["nav_sections"]
    # PROFILE_interp будет (из llm_text), остальные — нет
    labels = [s["label"] for s in nav]
    assert "О клинике" in labels
    # id — это HTML anchor
    assert all(s["id"].startswith("sec-") for s in nav)


def test_build_data_dict_finance_normalization():
    """company_financials (плоский) → FINANCE.find_company_financials (вложенный)."""
    data = build_data_dict(
        {"company_financials": _finance_raw(revenue=500_000_000, profit=50_000_000)},
        {},
        "",
    )
    fin_raw = data["FINANCE"]["find_company_financials"]
    fin = json.loads(fin_raw)
    assert fin["company"]["latest_revenue"] == 500_000_000
    assert fin["company"]["latest_profit"] == 50_000_000


# ──────────────────────────────────────────────────────────────────────────
# CSS / get_fonts_import
# ──────────────────────────────────────────────────────────────────────────

def test_canonical_css_contains_key_classes():
    """CSS содержит все ключевые классы новой вёрстки."""
    for cls in [
        ".aim-report-scope",
        ".water-ripples",
        ".ripple-ring",
        ".hero",
        ".section",
        ".section-label",
        ".metrics",
        ".glass-stats-wrap",
        ".glass-stat",
        ".surface-block",
        ".card-glass",
        ".cta-box",
        ".btn-primary",
        ".report-footer",
        ".revenue-block",
        ".rev-table-wrap",
        ".metric-tag",
    ]:
        assert cls in _CANONICAL_CSS, f"Missing CSS class: {cls}"


def test_canonical_css_responds_to_site_theme():
    """CSS реагирует на переключение темы сайтом (html[data-theme=dark])."""
    # Шапка сайта iamaim.ru переключает html[data-theme], не наш scope.
    # Наш CSS должен это поддерживать.
    assert 'html[data-theme="dark"] .aim-report-scope' in _CANONICAL_CSS


def test_canonical_css_has_dark_theme():
    """CSS содержит dark theme правила."""
    assert '[data-theme="dark"]' in _CANONICAL_CSS
    assert "--accent-rp: #c9a96e" in _CANONICAL_CSS  # Art Deco Gold


def test_canonical_css_has_ripple_animation():
    """CSS содержит keyframes для ripple анимации."""
    assert "@keyframes aim-water-ripple" in _CANONICAL_CSS
    assert "@keyframes aim-glass-glow" in _CANONICAL_CSS


def test_fonts_import_returns_link_tags():
    """get_fonts_import возвращает <link> теги для Google Fonts."""
    fonts = get_fonts_import()
    assert "fonts.googleapis.com" in fonts
    assert "Inter" in fonts
    assert "Playfair+Display" in fonts
    assert "<link" in fonts


# ──────────────────────────────────────────────────────────────────────────
# _build_ripple_html
# ──────────────────────────────────────────────────────────────────────────

def test_ripple_html_structure():
    """3 origin × 5 колец = 15 ripple-ring (сбалансированно, не перегружает взгляд)."""
    html = _build_ripple_html()
    assert html.count('<div class="ripple-ring"></div>') == 15
    for i in range(1, 4):  # origins 1, 2, 3
        assert f"ripple-origin-{i}" in html
    # origins 4, 5, 6 больше не рендерятся
    for i in (4, 5, 6):
        assert f"ripple-origin-{i}" not in html
    assert 'class="water-ripples"' in html


# ──────────────────────────────────────────────────────────────────────────
# _build_nav_html
# ──────────────────────────────────────────────────────────────────────────

def test_nav_html_with_sections():
    """Шапка сайта уже содержит кнопку темы — _build_nav_html возвращает пустую строку."""
    sections = [
        {"id": "sec-profile", "label": "О клинике"},
        {"id": "sec-reviews", "label": "Отзывы"},
    ]
    html = _build_nav_html(sections, "Test")
    # Нет своей nav-панели
    assert '<nav class="report-nav">' not in html
    # Нет своей кнопки toggle (используем кнопку сайта)
    assert "theme-toggle-report" not in html
    assert html == ""


def test_nav_html_empty_sections():
    """Пустые секции — тоже пустая строка."""
    html = _build_nav_html([], "Test")
    assert html == ""


# ──────────────────────────────────────────────────────────────────────────
# _build_hero_html
# ──────────────────────────────────────────────────────────────────────────

def test_hero_html_full():
    """Hero с полным набором meta-данных."""
    data = {
        "metadata": {"company_name": "ACME Clinic"},
        "hero_meta": {
            "city": "Москва",
            "address": "ул. Пушкина, 10",
            "founded_year": "2015",
            "doctors_count": 12,
            "rating": 5.0,
            "reviews_count": 562,
            "subtitle": "Москва · 12 врачей",
        },
    }
    html = _build_hero_html(data, "ACME Clinic")
    assert '<div class="hero">' in html
    assert "ACME Clinic" in html
    assert "AI MARKETING ANALYSIS" in html  # label
    assert "Москва · 12 врачей" in html  # subtitle в <em>
    assert "📍 Москва, ул. Пушкина, 10" in html
    assert "🏥" in html  # doctors emoji
    assert "📅 С 2015" in html
    assert "⭐ 5.0" in html
    assert "562 отзывов" in html


def test_hero_html_minimal():
    """Hero с пустыми meta — не падает, показывает только название."""
    data = {
        "metadata": {"company_name": "ACME"},
        "hero_meta": {"subtitle": ""},
    }
    html = _build_hero_html(data, "ACME")
    assert '<div class="hero">' in html
    assert "ACME" in html
    # subtitle fallback
    assert "Маркетинговый аудит" in html


def test_hero_html_fallback_to_title():
    """Если нет company_name — используется title."""
    data = {"metadata": {}, "hero_meta": {}}
    html = _build_hero_html(data, "Fallback Title")
    assert "Fallback Title" in html


# ──────────────────────────────────────────────────────────────────────────
# build_report_html (интеграционные тесты)
# ──────────────────────────────────────────────────────────────────────────

def _full_data() -> dict:
    """Полный data dict со всеми секциями."""
    return {
        "metadata": {"company_name": "ACME", "url": "https://acme.ru", "inn": "123"},
        "hero_meta": {
            "city": "Москва",
            "address": "ул. Теста, 1",
            "founded_year": "2018",
            "doctors_count": 10,
            "rating": 4.8,
            "reviews_count": 100,
            "revenue_str": "100 млн ₽",
            "subtitle": "Москва · 10 врачей · 100 млн ₽ выручки",
            "nav_sections": [
                {"id": "sec-profile", "label": "О клинике"},
                {"id": "sec-overview", "label": "Рынок"},
                {"id": "sec-competitors", "label": "Конкуренты"},
                {"id": "sec-reviews", "label": "Отзывы"},
            ],
        },
        "PROFILE_interp": {"content": "## Профиль\n\nACME — тест.", "label": "Профиль"},
        "OVERVIEW_interp": {"content": "## Рынок\n\nТестовый обзор.", "label": "Обзор"},
        "COMPETITORS_interp": {"content": "## Конкуренты\n\nТест.", "label": "Конкуренты"},
        "REVIEWS_interp": {"content": "## Отзывы\n\nТест.", "label": "Отзывы"},
        "FINANCE": {"find_company_financials": json.dumps({"company": {"latest_revenue": 100_000_000, "latest_profit": 10_000_000}})},
        "COMPETITORS": {"find_competitors": _competitors_raw()},
    }


def test_build_report_html_structure():
    """Полная структурная проверка отчёта."""
    html = build_report_html(_full_data(), "ACME")
    # Scoped wrapper
    assert 'class="aim-report-scope"' in html
    assert 'data-theme="light"' in html
    # Fonts
    assert "fonts.googleapis.com" in html
    # CSS
    assert "<style>" in html
    # Ripple
    assert 'class="water-ripples"' in html
    assert html.count('<div class="ripple-ring"></div>') == 15
    # Theme toggle — нет своего (используем кнопку сайта)
    assert "theme-toggle-report" not in html
    assert '<nav class="report-nav">' not in html
    # Hero
    assert '<div class="hero">' in html
    assert "ACME" in html
    # Sections — COMPETITORS убран (таблица рендерится в revenue_block),
    # теперь 3 секции: Профиль (01), Рынок (02), Отзывы (03).
    assert html.count('<section class="section"') == 3
    assert 'id="sec-profile"' in html
    assert 'id="sec-overview"' in html
    assert 'id="sec-competitors"' not in html  # нет отдельной секции
    assert 'id="sec-reviews"' in html
    # Section labels (01, 02, 03) — сквозная нумерация пересчиталась
    assert "01 — О КЛИНИКЕ" in html
    assert "02 — РЫНОК" in html
    assert "03 — ОТЗЫВЫ" in html
    # Конкуренты рендерятся только в revenue_block
    assert '<section class="revenue-block">' in html
    # CTA
    assert '<div class="cta-box">' in html
    assert "Связаться в Telegram" in html
    # Footer
    assert '<div class="report-footer">' in html
    assert "iamaim.ru" in html


def test_build_report_html_revenue_block_present():
    """Revenue block рендерится при наличии FINANCE данных — минималистичный стиль."""
    html = build_report_html(_full_data(), "ACME")
    assert '<section class="revenue-block">' in html
    assert "ACME vs" in html  # заголовок
    # Минималистичная таблица
    assert "rev-table-wrap" in html
    # Акцентная подсветка строки клиента
    assert "rev-row-client" in html
    # БЕЗ медальности (ранги без золотого/серебряного/бронзового цвета)
    assert "rev-rank-1" not in html
    assert "rev-rank-2" not in html
    assert "rev-rank-3" not in html


def test_build_report_html_revenue_block_absent():
    """Без FINANCE и без конкурентов — revenue block НЕ рендерится.

    Проверяем отсутствие <section class="revenue-block"> (HTML-элемента),
    а не подстроки 'revenue-block' (которая есть в CSS).
    """
    data = {
        "metadata": {"company_name": "ACME"},
        "hero_meta": {"nav_sections": []},
        "FINANCE": {"find_company_financials": "{}"},
        "COMPETITORS": {"find_competitors": "{}"},
    }
    html = build_report_html(data, "ACME")
    # HTML-элемент не отрендерился (CSS может содержать класс)
    assert '<section class="revenue-block">' not in html
    assert "rev-table-wrap" not in html.split("</style>")[-1]  # в контенте (после CSS)


def test_build_report_html_empty_data():
    """Полностью пустые данные — отчёт всё равно строится (без секций)."""
    data = {"metadata": {}, "hero_meta": {"nav_sections": []}}
    html = build_report_html(data, "Empty")
    assert 'class="aim-report-scope"' in html
    # Нет своей nav-панели и нет своего toggle (используем сайт)
    assert "theme-toggle-report" not in html
    assert '<nav class="report-nav">' not in html
    assert '<div class="hero">' in html
    assert "Empty" in html
    assert '<div class="cta-box">' in html
    assert '<div class="report-footer">' in html
    # Нет секций
    assert '<section class="section"' not in html


def test_build_report_html_skips_empty_sections():
    """Секции с пустым content — пропускаются."""
    data = {
        "metadata": {"company_name": "ACME"},
        "hero_meta": {"nav_sections": [{"id": "sec-profile", "label": "О клинике"}]},
        "PROFILE_interp": {"content": "", "label": "Профиль"},  # пустая
        "OVERVIEW_interp": {"content": "Реальный контент", "label": "Обзор"},
    }
    html = build_report_html(data, "ACME")
    # PROFILE пропущена (пустой content), OVERVIEW есть
    assert 'id="sec-profile"' not in html
    assert 'id="sec-overview"' in html


def test_build_report_html_is_wpautop_safe():
    """HTML минифицирован (без переносов в блоках) — wpautop-safe."""
    html = build_report_html(_full_data(), "ACME")
    # CSS — в одну строку (минифицирован)
    # Проверяем что нет подряд идущих 3+ переносов внутри основных блоков
    # (это означало бы что wpautop добавит <p> и сломает вёрстку)
    # Берём срез с контентом (без CSS)
    content_start = html.find('class="aim-report-scope"')
    if content_start > 0:
        content = html[content_start:]
        # Допускается не более 2 переносов подряд в контенте
        assert "\n\n\n" not in content, "Triple newline in content - wpautop will break it"


def test_build_report_html_theme_toggle_works():
    """Тема отчёта управляется кнопкой сайта (html[data-theme]), не нашей.

    Наш CSS должен иметь правило html[data-theme=dark] .aim-report-scope,
    чтобы при клике на #theme-toggle-btn в шапке сайта отчёт тоже менял тему.
    """
    html = build_report_html(_full_data(), "ACME")
    # Нашей кнопки toggle нет — используем кнопку сайта
    assert "theme-toggle-report" not in html
    # CSS содержит правило для html[data-theme=dark]
    assert 'html[data-theme="dark"] .aim-report-scope' in _CANONICAL_CSS


def test_build_report_html_escapes_company_name():
    """Название компании с HTML-спецсимволами — экранируется."""
    data = {
        "metadata": {"company_name": "<script>alert('xss')</script>"},
        "hero_meta": {"nav_sections": []},
    }
    html = build_report_html(data, "<b>title</b>")
    # XSS не проходит — script экранирован
    assert "<script>alert" not in html
    assert "&lt;script&gt;" in html


def test_build_report_html_has_fonts_and_css():
    """Fonts и CSS присутствуют в начале."""
    html = build_report_html(_full_data(), "ACME")
    fonts_pos = html.find("fonts.googleapis.com")
    css_pos = html.find("<style>")
    scope_pos = html.find('class="aim-report-scope"')
    assert fonts_pos > 0
    assert css_pos > fonts_pos  # fonts раньше CSS
    assert scope_pos > css_pos  # scope после CSS


# ──────────────────────────────────────────────────────────────────────────
# Интеграционный тест: adapter → builder
# ──────────────────────────────────────────────────────────────────────────

def test_end_to_end_adapter_to_builder():
    """Полный пайплайн: collected_results → build_data_dict → build_report_html."""
    collected = {
        "extract_clinic_profile": _profile_raw(company_name="E2E Clinic", doctors_count=20),
        "company_financials": _finance_raw(revenue=200_000_000),
        "find_competitors": _competitors_raw(),
        "run_review_platforms": _reviews_raw(rating=4.7, reviews=200),
    }
    profile_cache = {"company_name": "E2E Clinic", "url": "https://e2e.ru", "inn": "999"}

    data = build_data_dict(collected, profile_cache, "## Профиль\n\nE2E клиника.")

    html = build_report_html(data, "E2E Clinic")

    # Все ключевые элементы присутствуют
    assert "E2E Clinic" in html
    assert '<div class="hero">' in html
    # Нет своего toggle — используем кнопку сайта
    assert "theme-toggle-report" not in html
    assert '<nav class="report-nav">' not in html
    assert "4.7" in html  # rating из reviews
    assert "200" in html  # reviews count
    assert "20" in html  # doctors_count
    assert '<div class="cta-box">' in html


def test_end_to_end_minimal_data():
    """Минимальные данные — отчёт всё равно строится."""
    data = build_data_dict({}, {"company_name": "Min"}, "")
    html = build_report_html(data, "Min")
    assert "Min" in html
    assert '<div class="hero">' in html
