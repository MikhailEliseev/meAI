"""Тесты фиксов пайплайна чата v2 (Task 1-3 плана 2026-07-21)."""
from app.llm import _TOOL_MESSAGES


class TestToolMessagesHonest:
    """Task 1: UI-сообщения не должны врать про Google Maps и ИНН."""

    def test_find_competitors_message_no_google_maps(self):
        """Сообщение о конкурентах НЕ должно упоминать Google Maps."""
        msg = _TOOL_MESSAGES["find_competitors"]["start"]
        assert "Google Maps" not in msg, (
            f"Сообщение '{msg}' упоминает Google Maps, "
            "но код использует Perplexity+SearXNG→ФНС стратегию"
        )

    def test_find_competitors_message_mentions_fns(self):
        """Сообщение должно честно говорить про ФНС/налоговую."""
        msg = _TOOL_MESSAGES["find_competitors"]["start"]
        assert "ФНС" in msg or "налогов" in msg or "Perplexity" in msg, (
            f"Сообщение '{msg}' не объясняет реальный источник данных"
        )

    def test_extract_clinic_profile_message_honest_about_inn(self):
        """Сообщение о профиле не должно обещать ИНН (Perplexity его не находит)."""
        msg = _TOOL_MESSAGES["extract_clinic_profile"]["start"]
        # ИНН может упоминаться, но не как главный результат
        assert "ИНН" not in msg or "адрес" in msg, (
            f"Сообщение '{msg}' обещает ИНН как главный результат, "
            "но Perplexity его почти никогда не находит"
        )
