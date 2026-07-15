"""Тесты анти-галлюцинационного слоя (P1-P3).

P2: _filtered_tool_content — скрывает raw JSON форматированных тулов.
P3: format_overview — очищает quick_overview от галлюцинаций Perplexity.
P1: chat_with_tools events — 'formatted' event для таблиц из кода.
"""

import json

import pytest

from app.llm import (
    _filtered_tool_content,
    _FORMATTED_TOOLS,
    _TOOL_RESULT_HIDDEN,
    _check_hallucinations,
)
from app.formatters.overview import format_overview
from app.formatters.competitors import format_competitors
from app.formatters.profile import format_profile


# ═══════════════════════════════════════════════════════════════════════════
# P2: Фильтрация raw JSON
# ═══════════════════════════════════════════════════════════════════════════

class TestToolContentFilter:
    """P2: _filtered_tool_content скрывает JSON форматированных тулов."""

    def test_find_competitors_hidden(self):
        """find_competitors JSON заменяется на заглушку."""
        raw = json.dumps({"competitors": [{"brand": "Test", "revenue": 999999}]})
        result = _filtered_tool_content("find_competitors", raw)
        assert result == _TOOL_RESULT_HIDDEN
        assert "999999" not in result

    def test_extract_clinic_profile_hidden(self):
        """extract_clinic_profile JSON заменяется на заглушку."""
        raw = json.dumps({"inn": "7708698635", "company_name": "IPHK"})
        result = _filtered_tool_content("extract_clinic_profile", raw)
        assert result == _TOOL_RESULT_HIDDEN
        assert "7708698635" not in result

    def test_quick_overview_kept(self):
        """quick_overview (качественные данные) НЕ скрывается."""
        raw = "ВРАЧИ: Иванов И.И. — хирург. Соцсети: instagram.com/test"
        result = _filtered_tool_content("quick_overview", raw)
        assert result == raw

    def test_perplexity_search_kept(self):
        """perplexity_search НЕ скрывается."""
        raw = "Свободный текст поиска"
        result = _filtered_tool_content("perplexity_search", raw)
        assert result == raw

    def test_unknown_tool_kept(self):
        """Неизвестный тул — не скрывается."""
        raw = "какой-то результат"
        result = _filtered_tool_content("unknown_tool", raw)
        assert result == raw

    def test_formatted_tools_set(self):
        """_FORMATTED_TOOLS содержит только форматированные тулы."""
        assert "find_competitors" in _FORMATTED_TOOLS
        assert "extract_clinic_profile" in _FORMATTED_TOOLS
        assert "quick_overview" not in _FORMATTED_TOOLS


# ═══════════════════════════════════════════════════════════════════════════
# P3: format_overview — очистка quick_overview
# ═══════════════════════════════════════════════════════════════════════════

class TestFormatOverview:
    """P3: format_overview извлекает факты, убирает галлюцинации."""

    SAMPLE_OVERVIEW = """**БИЗНЕС:**
IPHK — Институт пластической хирургии и косметологии
ИНН: 7708698635
Город: Москва

**ВРАЧИ:**
- Иванов И.И. — пластический хирург
- Петрова А.Б. — косметолог
- Сидоров В.Г. — челюстно-лицевой хирург

**СОЦСЕТИ:**
Instagram: https://instagram.com/iphk_clinic
VK: https://vk.com/iphk

**САЙТ:**
Платформа: Tilda, около 45 страниц

**ЗАЦЕПКА:**
Сайт клиники получает ~19 000 визитов в месяц — это меньше чем у 3 из 5 конкурентов.

Выручка: 500 млн рублей."""

    def test_extracts_doctors(self):
        """Врачи извлекаются из секции ВРАЧИ."""
        md = format_overview(self.SAMPLE_OVERVIEW)
        assert "Иванов И.И." in md
        assert "Петрова А.Б." in md
        assert "Сидоров В.Г." in md

    def test_extracts_socials(self):
        """Соцсети извлекаются (ссылки из оригинального текста)."""
        md = format_overview(self.SAMPLE_OVERVIEW)
        assert "instagram.com/iphk_clinic" in md
        assert "vk.com/iphk" in md
        assert "Instagram" in md

    def test_extracts_platform(self):
        """Платформа сайта детектится."""
        md = format_overview(self.SAMPLE_OVERVIEW)
        assert "Tilda" in md

    def test_strips_hallucinated_visits(self):
        """Оценка «~19 000 визитов» вырезается (источник галлюцинаций)."""
        md = format_overview(self.SAMPLE_OVERVIEW)
        assert "19 000" not in md
        assert "визит" not in md.lower() or "19" not in md

    def test_strips_unexpected_fact(self):
        """«ЗАЦЕПКА» секция вырезается."""
        md = format_overview(self.SAMPLE_OVERVIEW)
        assert "ЗАЦЕПКА" not in md
        assert "зацепк" not in md.lower()

    def test_strips_revenue(self):
        """Выручка из overview вырезается (есть точная в competitors)."""
        md = format_overview(self.SAMPLE_OVERVIEW)
        assert "500 млн" not in md

    def test_empty_input(self):
        """Пустой ввод → пустая строка."""
        assert format_overview("") == ""
        assert format_overview("   ") == ""

    def test_error_json_skipped(self):
        """JSON с error → пустая строка."""
        assert format_overview('{"error": "failed"}') == ""

    def test_no_useful_data(self):
        """Текст без врачей/соцсетей → пустой блок (не показываем пустоту)."""
        md = format_overview("Какой-то текст без структурированных данных.")
        assert md == ""


# ═══════════════════════════════════════════════════════════════════════════
# P1: Formatters (интеграция с formatted blocks)
# ═══════════════════════════════════════════════════════════════════════════

class TestFormatters:
    """P1: форматтеры корректно обрабатывают JSON данных."""

    COMPETITORS_JSON = json.dumps({
        "competitors": [
            {"brand_name": "GMTClinic", "revenue_year": 742000000,
             "revenue_trend": "growing", "surgeons_count": 12,
             "instagram_followers": 31000},
            {"brand_name": "Клазко", "revenue_year": 371000000,
             "revenue_trend": "stable", "surgeons_count": 8,
             "instagram_followers": 30000},
        ]
    })

    def test_format_competitors_table(self):
        """Таблица конкурентов рендерится с правильными данными."""
        md = format_competitors(self.COMPETITORS_JSON)
        assert "GMTClinic" in md
        assert "742" in md  # млн
        assert "📈" in md  # growing trend
        assert "31K" in md  # instagram followers

    def test_format_competitors_empty(self):
        """Пустой список → сообщение «не найдено»."""
        md = format_competitors('{"competitors": []}')
        assert "не найден" in md

    def test_format_profile(self):
        """Профиль клиники рендерится."""
        profile_json = json.dumps({
            "company_name": "ООО Тест",
            "inn": "7708698635",
            "city": "Москва",
            "specialization": "пластическая хирургия",
        })
        md, data = format_profile(profile_json)
        assert "ООО Тест" in md
        assert "7708698635" in md
        assert "Москва" in md
        assert data["inn"] == "7708698635"


# ═══════════════════════════════════════════════════════════════════════════
# P4: Пост-проверка галлюцинаций
# ═══════════════════════════════════════════════════════════════════════════

class TestHallucinationCheck:
    """P4: _check_hallucinations логирует подозрительные формулировки."""

    def test_detects_tilde_numbers(self, caplog):
        """«~19 000» детектится как оценочное число."""
        import logging
        caplog.set_level(logging.WARNING)
        _check_hallucinations("Клиника получает ~19 000 визитов", True)
        assert any("ANTI-HALLUCINATION" in r.message for r in caplog.records)

    def test_detects_approximately(self, caplog):
        """«примерно 500» детектится."""
        import logging
        caplog.set_level(logging.WARNING)
        _check_hallucinations("Выручка примерно 500 млн", True)
        assert any("примерно" in r.message for r in caplog.records)

    def test_clean_text_no_warning(self, caplog):
        """Чистый текст без оценок — нет warning."""
        import logging
        caplog.set_level(logging.WARNING)
        _check_hallucinations("Клиника в середине рынка. Рекомендация: усилить Instagram.", True)
        assert not any("ANTI-HALLUCINATION" in r.message for r in caplog.records)

    def test_skipped_without_formatted(self, caplog):
        """Без formatted blocks проверка пропускается."""
        import logging
        caplog.set_level(logging.WARNING)
        _check_hallucinations("~19 000 визитов", False)
        assert not any("ANTI-HALLUCINATION" in r.message for r in caplog.records)
