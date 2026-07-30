"""Тесты очистки данных конкурентов в revenue_block (Fix Баг 2+3).

Проверяет:
- Фильтр мусорных имён (LLM-болтовня из Perplexity)
- Дедупликация по ИНН и по имени
- Интеграцию через build_revenue_vs_competitors_block
"""
import json

from app.report_builder.revenue_block import (
    _clean_competitors,
    _is_valid_brand,
    build_revenue_vs_competitors_block,
)


# ── _is_valid_brand ────────────────────────────────────────────────────────────

class TestIsValidBrand:
    def test_real_brand_short(self):
        assert _is_valid_brand("GMTClinic") is True

    def test_real_brand_with_quotes(self):
        assert _is_valid_brand('ООО "ЭСТЕТ"') is True

    def test_real_brand_cyrillic(self):
        assert _is_valid_brand("Фрау Клиник") is True

    def test_garbage_chatter_sentence(self):
        # Баг из отчёта 22mhfsko
        assert _is_valid_brand("Вот несколько известных клиник косметологии в Санкт-Петербурге:") is False

    def test_garbage_too_long(self):
        assert _is_valid_brand("А" * 61) is False

    def test_garbage_with_colon(self):
        assert _is_valid_brand("Перейдём к списку:") is False

    def test_garbage_chatter_word(self):
        assert _is_valid_brand("Например клиника") is False

    def test_garbage_too_many_words(self):
        assert _is_valid_brand("Очень длинное название из пяти отдельных слов") is False

    def test_empty(self):
        assert _is_valid_brand("") is False

    def test_too_short(self):
        assert _is_valid_brand("А") is False


# ── _clean_competitors ─────────────────────────────────────────────────────────

class TestCleanCompetitors:
    def test_filters_garbage_names(self):
        """LLM-болтовня отфильтровывается."""
        comps = [
            {"brand_name": "GMTClinic", "revenue_year": 742_000_000},
            {"brand_name": "Вот несколько известных клиник косметологии:", "revenue_year": 41_000_000},
            {"brand_name": "Фрау Клиник", "revenue_year": 300_000_000},
        ]
        cleaned = _clean_competitors(comps)
        names = [c["brand_name"] for c in cleaned]
        assert "GMTClinic" in names
        assert "Фрау Клиник" in names
        assert "Вот несколько известных клиник косметологии:" not in names
        assert len(cleaned) == 2

    def test_dedup_by_name(self):
        """Дубликат по имени — оставляем запись с большей выручкой."""
        comps = [
            {"brand_name": 'ООО "ЭСТЕТ"', "revenue_year": 102_000_000, "inn": ""},
            {"brand_name": 'ООО «ЭСТЕТ»', "revenue_year": 157_000_000, "inn": ""},
        ]
        cleaned = _clean_competitors(comps)
        # Должен остаться один — с большей выручкой
        assert len(cleaned) == 1
        assert cleaned[0]["revenue_year"] == 157_000_000

    def test_dedup_by_inn_keeps_different_companies(self):
        """Разные ИНН = разные компании (не дедуплицируем)."""
        comps = [
            {"brand_name": "Клиника А", "revenue_year": 100_000_000, "inn": "7700000001"},
            {"brand_name": "Клиника А", "revenue_year": 200_000_000, "inn": "7700000002"},
        ]
        cleaned = _clean_competitors(comps)
        assert len(cleaned) == 2  # разные ИНН — обе остаются

    def test_dedup_by_inn_same_company(self):
        """Один ИНН = одна компания — дедуплицируем (оставляем большую выручку)."""
        comps = [
            {"brand_name": "Клиника А", "revenue_year": 100_000_000, "inn": "7700000001"},
            {"brand_name": "Клиника А филиал", "revenue_year": 200_000_000, "inn": "7700000001"},
        ]
        cleaned = _clean_competitors(comps)
        assert len(cleaned) == 1
        assert cleaned[0]["revenue_year"] == 200_000_000

    def test_preserves_order_by_revenue_in_dedup(self):
        """При дубликате остаётся запись с большей выручкой."""
        comps = [
            {"brand_name": "Лидер", "revenue_year": 500_000_000, "inn": "1111111111"},
            {"brand_name": "Лидер", "revenue_year": 50_000_000, "inn": "1111111111"},
        ]
        cleaned = _clean_competitors(comps)
        assert cleaned[0]["revenue_year"] == 500_000_000

    def test_empty_input(self):
        assert _clean_competitors([]) == []

    def test_all_garbage_filtered(self):
        comps = [
            {"brand_name": "Вот несколько клиник:", "revenue_year": 41_000_000},
            {"brand_name": "Например такая клиника тут", "revenue_year": 10_000_000},
        ]
        cleaned = _clean_competitors(comps)
        assert cleaned == []

    def test_no_revenue_field_kept(self):
        """Конкуренты без revenue_year не должны ломать очистку."""
        comps = [
            {"brand_name": "GMTClinic", "revenue_year": 742_000_000},
            {"brand_name": "БезВыручки"},  # нет revenue_year
        ]
        cleaned = _clean_competitors(comps)
        names = [c["brand_name"] for c in cleaned]
        assert "GMTClinic" in names


# ── Интеграция: build_revenue_vs_competitors_block ─────────────────────────────

class TestRevenueBlockIntegration:
    def _comp_json(self, comps):
        return json.dumps({"competitors": comps}, ensure_ascii=False)

    def test_garbage_excluded_from_table(self):
        """Мусорный конкурент не появляется в финальной таблице."""
        comps_json = self._comp_json([
            {"brand_name": "GMTClinic", "revenue_year": 742_000_000, "revenue_trend": "growing"},
            {"brand_name": "Вот несколько клиник косметологии:", "revenue_year": 41_000_000},
        ])
        html = build_revenue_vs_competitors_block(
            client_revenue=None,
            client_profit=None,
            competitors_result=comps_json,
            company_name="Тест",
        )
        assert "GMTClinic" in html
        assert "Вот несколько" not in html

    def test_duplicate_removed_from_table(self):
        """Дубликат компании не появляется дважды в таблице."""
        comps_json = self._comp_json([
            {"brand_name": 'ООО "ЭСТЕТ"', "revenue_year": 102_000_000, "inn": ""},
            {"brand_name": 'ООО «ЭСТЕТ»', "revenue_year": 157_000_000, "inn": ""},
        ])
        html = build_revenue_vs_competitors_block(
            client_revenue=None,
            client_profit=None,
            competitors_result=comps_json,
            company_name="Тест",
        )
        # Должна быть одна строка (157 млн — большая выручка)
        assert html.count('class="rev-name"') == 1
        assert "157" in html
        assert "102" not in html


# ── Disambiguation: одинаковые имена, разные ИНН ──────────────────────────────

class TestCompetitorDisambiguation:
    """Fix Баг 3 v2: две компании с одинаковым названием но разными ИНН
    должны получить различающий суффикс (ИНН …XXXX), чтобы не выглядеть дублём."""

    def _comp_json(self, comps):
        return json.dumps({"competitors": comps}, ensure_ascii=False)

    def test_same_name_different_inn_gets_suffix(self):
        """Две ООО ЭСТЕТ с разными ИНН → обе видны, с суффиксом ИНН."""
        comps_json = self._comp_json([
            {"brand_name": 'ООО "ЭСТЕТ"', "revenue_year": 102_000_000, "inn": "7816707206"},
            {"brand_name": 'ООО "ЭСТЕТ"', "revenue_year": 157_000_000, "inn": "7842220627"},
        ])
        html = build_revenue_vs_competitors_block(
            client_revenue=None,
            client_profit=None,
            competitors_result=comps_json,
            company_name="Тест",
        )
        # Обе строки присутствуют (разные ИНН = разные компании)
        assert html.count('class="rev-name"') == 2
        # Суффикс с последними 4 цифрами ИНН добавлен
        assert "7206" in html
        assert "0627" in html

    def test_unique_names_no_suffix(self):
        """Разные имена → без суффикса."""
        comps_json = self._comp_json([
            {"brand_name": "GMTClinic", "revenue_year": 742_000_000, "inn": "1111111111"},
            {"brand_name": "Фрау Клиник", "revenue_year": 300_000_000, "inn": "2222222222"},
        ])
        html = build_revenue_vs_competitors_block(
            client_revenue=None,
            client_profit=None,
            competitors_result=comps_json,
            company_name="Тест",
        )
        # Без суффикса ИНН
        assert "1111" not in html
        assert "2222" not in html

