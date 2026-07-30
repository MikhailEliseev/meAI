"""Тесты модуля analysis.py — глубокий LLM-анализ для отчёта."""
import json

from app.report_builder.analysis import (
    _build_context,
    _fmt_followers,
    _fmt_money,
    _parse_analysis_sections,
    split_analysis_by_section,
)


# ── Форматтеры ─────────────────────────────────────────────────────────────────

class TestFormatters:
    def test_fmt_money_millions(self):
        assert _fmt_money(121_000_000) == "121 млн ₽"

    def test_fmt_money_billions(self):
        assert _fmt_money(1_500_000_000) == "1.5 млрд ₽"

    def test_fmt_money_none(self):
        assert _fmt_money(None) == "нет данных"

    def test_fmt_money_zero(self):
        assert _fmt_money(0) == "нет данных"

    def test_fmt_followers_thousands(self):
        assert _fmt_followers(31_000) == "31K"

    def test_fmt_followers_millions(self):
        assert _fmt_followers(1_500_000) == "1.5M"

    def test_fmt_followers_none(self):
        assert _fmt_followers(None) == "—"


# ── Парсинг секций ─────────────────────────────────────────────────────────────

class TestParseSections:
    def test_parse_all_four_sections(self):
        text = """=== ПОЗИЦИЯ ===
Текст позиции.

=== СИЛЬНЫЕ ===
- Сила 1

=== РОСТ ===
- Пробел 1

=== РЕКОМЕНДАЦИИ ===
1. Действие 1"""
        sections = _parse_analysis_sections(text)
        assert "Текст позиции" in sections["позиция"]
        assert "Сила 1" in sections["сильные"]
        assert "Пробел 1" in sections["рост"]
        assert "Действие 1" in sections["рекомендации"]

    def test_parse_empty_text(self):
        sections = _parse_analysis_sections("")
        assert all(v == "" for v in sections.values())

    def test_parse_missing_section(self):
        text = "=== ПОЗИЦИЯ ===\nТолько позиция."
        sections = _parse_analysis_sections(text)
        assert "позиция" in sections["позиция"]
        assert sections["сильные"] == ""

    def test_split_profile_and_reviews(self):
        text = """=== ПОЗИЦИЯ ===
Позиция.

=== СИЛЬНЫЕ ===
Силы.

=== РОСТ ===
Рост.

=== РЕКОМЕНДАЦИИ ===
Рек."""
        split = split_analysis_by_section(text)
        assert "Позиция" in split["profile"]
        assert "Силы" in split["profile"]
        assert "Рост" in split["reviews"]
        assert "Рек" in split["reviews"]


# ── Построение контекста ───────────────────────────────────────────────────────

class TestBuildContext:
    def test_context_includes_profile(self):
        context = _build_context(
            {"extract_clinic_profile": json.dumps({"specialization": "косметология"})},
            {"company_name": "Тест Клиник", "inn": "7700000001", "city": "Москва"},
        )
        assert "Тест Клиник" in context
        assert "7700000001" in context
        assert "Москва" in context
        assert "косметология" in context

    def test_context_includes_competitors(self):
        cr = {
            "find_competitors": json.dumps({
                "competitors": [
                    {"brand_name": "Конкурент А", "revenue_year": 100_000_000, "profit_year": 10_000_000},
                ],
            }),
        }
        context = _build_context(cr, {"company_name": "Тест"})
        assert "Конкурент А" in context
        assert "100 млн" in context
        assert "10 млн" in context

    def test_context_includes_reviews_and_neuro(self):
        cr = {
            "run_review_platforms": json.dumps({
                "platforms": {"yandex": {"rating": 5.0, "reviews": 564}},
                "neuro_summary": "Отличная клиника с внимательным персоналом",
                "review_quotes": [{"text": "Всё понравилось", "source": "2ГИС"}],
                "praise_summary": "Персонал | Чистота",
            }),
        }
        context = _build_context(cr, {"company_name": "Тест"})
        assert "5.0" in context
        assert "564" in context
        assert "Отличная клиника" in context
        assert "Всё понравилось" in context
        assert "Персонал" in context

    def test_context_includes_scrape_doctors(self):
        cr = {
            "scrape_clinic_website": json.dumps({
                "doctors": [{"name": "Иванов И.", "specialization": "косметолог"}],
                "socials": {"vk": "clinic"},
                "cms": "Tilda",
            }),
        }
        context = _build_context(cr, {"company_name": "Тест"})
        assert "Иванов И." in context
        assert "косметолог" in context
        assert "vk: clinic" in context
        assert "Tilda" in context

    def test_context_no_financials(self):
        context = _build_context({}, {"company_name": "Тест"})
        assert "нет данных" in context

    def test_context_empty(self):
        context = _build_context({}, {})
        assert "Клиника" in context or "Тест" in context or len(context) > 0


# ── Интеграция: build_data_dict с analysis_text ────────────────────────────────

class TestBuildDataDictWithAnalysis:
    def test_analysis_text_used_for_profile(self):
        """analysis_text (ПОЗИЦИЯ+СИЛЬНЫЕ) попадает в PROFILE_interp."""
        from app.report_builder.adapter import build_data_dict

        analysis = """=== ПОЗИЦИЯ ===
Лидер рынка с выручкой 500 млн.

=== СИЛЬНЫЕ ===
- Рейтинг 5.0
- 10 врачей

=== РОСТ ===
- Нет Instagram

=== РЕКОМЕНДАЦИИ ===
Создать VK."""
        data = build_data_dict(
            {"extract_clinic_profile": "{}"},
            {"company_name": "Тест"},
            llm_text="",
            analysis_text=analysis,
        )
        # PROFILE_interp должен содержать ПОЗИЦИЯ + СИЛЬНЫЕ
        profile = data.get("PROFILE_interp", {}).get("content", "")
        assert "Лидер рынка" in profile or "500 млн" in profile
        assert "Рейтинг" in profile

    def test_no_analysis_falls_back_to_formatted(self):
        """Без analysis_text — fallback на formatted blocks (как раньше)."""
        from app.report_builder.adapter import build_data_dict

        data = build_data_dict(
            {"extract_clinic_profile": json.dumps({"company_name": "Тест", "inn": "123"})},
            {"company_name": "Тест"},
            llm_text="",
            analysis_text="",
        )
        # Должен быть профиль из formatter
        assert "PROFILE_interp" in data
