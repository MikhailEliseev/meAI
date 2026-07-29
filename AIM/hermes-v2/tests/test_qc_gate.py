"""Тесты QC Gate — проверка качества данных перед публикацией отчёта.

Покрывает:
- Каждый пункт (profile, financials, competitors, reviews) в PASS/FAIL
- Overall coverage calculation
- PASS_THRESHOLD (60%)
- Edge cases: пустые данные, невалидный JSON, partial data
- Интеграция с _auto_publish_report (QC FAIL → не публикует)
"""
import json

import pytest

from app.qc_gate import (
    PASS_THRESHOLD,
    _check_competitors,
    _check_financials,
    _check_profile,
    _check_reviews,
    run_qc_gate,
)


# ── Helpers ────────────────────────────────────────────────────────────────

def _profile_raw(**overrides) -> str:
    base = {
        "company_name": "Test Clinic",
        "inn": "7700000000",
        "city": "Москва",
    }
    base.update(overrides)
    return json.dumps(base, ensure_ascii=False)


def _finance_raw(revenue=100_000_000) -> str:
    return json.dumps({"revenue": revenue, "profit": 10_000_000}, ensure_ascii=False)


def _competitors_raw(count=5) -> str:
    comps = [
        {"brand_name": f"Comp {i}", "revenue_year": 100_000_000 * i, "revenue_trend": "growing"}
        for i in range(1, count + 1)
    ]
    return json.dumps({"competitors": comps}, ensure_ascii=False)


def _reviews_raw(yandex=True, twogis=True) -> str:
    platforms = {}
    if yandex:
        platforms["yandex"] = {"rating": 4.5, "reviews": 100}
    if twogis:
        platforms["twogis"] = {"rating": 4.7, "reviews": 50}
    return json.dumps({"platforms": platforms}, ensure_ascii=False)


def _full_collected() -> dict:
    return {
        "extract_clinic_profile": _profile_raw(),
        "company_financials": _finance_raw(),
        "find_competitors": _competitors_raw(5),
        "run_review_platforms": _reviews_raw(),
    }


def _full_profile_cache() -> dict:
    return {
        "company_name": "Test Clinic",
        "inn": "7700000000",
        "city": "Москва",
        "revenue": 100_000_000,
    }


# ── Individual checks ─────────────────────────────────────────────────────

def test_check_profile_pass():
    result = _check_profile({}, _full_profile_cache())
    assert result["passed"] is True
    assert result["details"]["name"] == "Test Clinic"


def test_check_profile_pass_from_collected():
    """Профиль берётся из collected_results если profile_cache пустой."""
    collected = {"extract_clinic_profile": _profile_raw()}
    result = _check_profile(collected, {})
    assert result["passed"] is True


def test_check_profile_fail_empty():
    result = _check_profile({}, {})
    assert result["passed"] is False


def test_check_profile_fail_name_only():
    """Есть имя, но нет ИНН и города → FAIL."""
    result = _check_profile({}, {"company_name": "Test"})
    assert result["passed"] is False


def test_financials_pass():
    result = _check_financials({"company_financials": _finance_raw()}, {})
    assert result["passed"] is True
    assert result["details"]["revenue"] == 100_000_000


def test_financials_pass_from_cache():
    """Выручка из profile_cache (auto-call)."""
    result = _check_financials({}, {"revenue": 50_000_000})
    assert result["passed"] is True


def test_financials_fail_zero():
    result = _check_financials({"company_financials": _finance_raw(revenue=0)}, {})
    assert result["passed"] is False


def test_financials_fail_missing():
    result = _check_financials({}, {})
    assert result["passed"] is False


def test_competitors_pass():
    result = _check_competitors({"find_competitors": _competitors_raw(5)})
    assert result["passed"] is True
    assert result["details"]["with_revenue"] == 5


def test_competitors_pass_exactly_3():
    result = _check_competitors({"find_competitors": _competitors_raw(3)})
    assert result["passed"] is True


def test_competitors_fail_only_2():
    result = _check_competitors({"find_competitors": _competitors_raw(2)})
    assert result["passed"] is False


def test_competitors_fail_empty():
    result = _check_competitors({"find_competitors": '{"competitors": []}'})
    assert result["passed"] is False


def test_reviews_pass_yandex():
    result = _check_reviews({"run_review_platforms": _reviews_raw(yandex=True, twogis=False)})
    assert result["passed"] is True


def test_reviews_pass_both():
    result = _check_reviews({"run_review_platforms": _reviews_raw(yandex=True, twogis=True)})
    assert result["passed"] is True


def test_reviews_fail_no_rating():
    raw = json.dumps({"platforms": {"yandex": {}, "twogis": {}}})
    result = _check_reviews({"run_review_platforms": raw})
    assert result["passed"] is False


# ── run_qc_gate (overall) ─────────────────────────────────────────────────

def test_qc_gate_all_pass():
    result = run_qc_gate(_full_collected(), _full_profile_cache())
    assert result["passed"] is True
    assert result["coverage"] == 1.0
    assert result["coverage_pct"] == 100
    assert result["critical_failures"] == []
    assert len(result["items"]) == 4


def test_qc_gate_threshold_60pct():
    """PASS_THRESHOLD = 0.60 → нужно минимум 2 из 4 пунктов."""
    assert PASS_THRESHOLD == 0.60


def test_qc_gate_partial_pass_50pct():
    """2 из 4 пройдены (50%) → FAIL (ниже 60%)."""
    collected = {
        "extract_clinic_profile": _profile_raw(),
        "company_financials": _finance_raw(),
        # Нет конкурентов и отзывов
    }
    profile_cache = _full_profile_cache()
    result = run_qc_gate(collected, profile_cache)
    assert result["coverage_pct"] == 50
    assert result["passed"] is False
    assert "competitors" in result["critical_failures"]
    assert "reviews" in result["critical_failures"]


def test_qc_gate_partial_pass_75pct():
    """3 из 4 пройдены (75%) → PASS."""
    collected = {
        "extract_clinic_profile": _profile_raw(),
        "company_financials": _finance_raw(),
        "find_competitors": _competitors_raw(5),
        # Нет отзывов
    }
    profile_cache = _full_profile_cache()
    result = run_qc_gate(collected, profile_cache)
    assert result["coverage_pct"] == 75
    assert result["passed"] is True
    assert "reviews" in result["critical_failures"]


def test_qc_gate_empty_data():
    """Полностью пустые данные → FAIL (0%)."""
    result = run_qc_gate({}, {})
    assert result["passed"] is False
    assert result["coverage_pct"] == 0
    assert len(result["critical_failures"]) == 4


def test_qc_gate_invalid_json():
    """Невалидный JSON не должен падать."""
    collected = {
        "extract_clinic_profile": "not json",
        "company_financials": "{broken",
        "find_competitors": "null",
        "run_review_platforms": "",
    }
    result = run_qc_gate(collected, _full_profile_cache())
    # Профиль пройдёт (из profile_cache), остальные — FAIL
    assert result["passed"] is False


def test_qc_gate_returns_items_structure():
    """Каждый item имеет правильную структуру."""
    result = run_qc_gate(_full_collected(), _full_profile_cache())
    for item in result["items"]:
        assert "id" in item
        assert "category" in item
        assert "passed" in item
        assert "details" in item


# ── Integration: _auto_publish_report respects QC gate ────────────────────

@pytest.mark.asyncio
async def test_auto_publish_skipped_on_qc_fail():
    """QC FAIL → отчёт НЕ публикуется."""
    from app.llm import _auto_publish_report

    collected = {
        "find_competitors": '{"competitors": []}',  # 0 конкурентов → QC FAIL
    }
    profile_cache = {"company_name": "Test"}

    import app.report_builder as rb_mod
    original = rb_mod.publish_report

    call_count = 0

    async def counting_publish(html, title):
        nonlocal call_count
        call_count += 1
        return {"status": "published", "url": "https://iamaim.ru/test"}

    rb_mod.publish_report = counting_publish
    try:
        results = []
        async for event in _auto_publish_report(collected, profile_cache, ""):
            results.append(event)
    finally:
        rb_mod.publish_report = original

    # publish_report НЕ должен вызываться (QC FAIL)
    assert call_count == 0, "publish_report was called despite QC FAIL"
    # report_ready не должен yield-иться
    assert results == []


@pytest.mark.asyncio
async def test_auto_publish_runs_on_qc_pass():
    """QC PASS → отчёт публикуется."""
    from app.llm import _auto_publish_report

    collected = _full_collected()
    profile_cache = _full_profile_cache()

    import app.report_builder as rb_mod
    original = rb_mod.publish_report

    async def mock_publish(html, title):
        return {"status": "published", "url": "https://iamaim.ru/test123", "slug": "test123"}

    rb_mod.publish_report = mock_publish
    try:
        results = []
        async for event in _auto_publish_report(collected, profile_cache, "analysis text"):
            results.append(event)
    finally:
        rb_mod.publish_report = original

    assert len(results) == 1
    assert results[0][0] == "report_ready"
    assert results[0][1] == "https://iamaim.ru/test123"
