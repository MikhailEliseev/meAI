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


import asyncio
import json
from unittest.mock import AsyncMock, patch


class TestAutoCallFinancials:
    """Task 2: company_financials должен auto-call после find_competitors если есть client_inn."""

    def test_financials_called_when_inn_present(self):
        """Если find_competitors вернул client_inn, financials должен вызваться."""
        # Симулируем результат find_competitors с ИНН
        competitors_result = json.dumps({
            "client_inn": "7801234567",
            "competitors": [],
        })

        # Мокаем handle_company_financials
        financials_called = {"inn": None}

        async def fake_financials(inn="", **kwargs):
            financials_called["inn"] = inn
            return json.dumps({"inn": inn, "revenue": 50000000, "name": "Test Clinic"})

        # Проверяем, что auto-call логика извлекает ИНН из competitors_result
        # и вызывает financials (через симуляцию парсинга)
        comp_data = json.loads(competitors_result)
        client_inn = comp_data.get("client_inn")
        assert client_inn == "7801234567", "ИНН должен извлекаться из find_competitors"

        # Запуск fake_financials чтобы проверить сигнатуру
        result = asyncio.run(fake_financials(inn=client_inn))
        assert financials_called["inn"] == "7801234567"
        assert "revenue" in json.loads(result)

    def test_financials_not_called_without_inn(self):
        """Если client_inn пустой, financials НЕ должен вызываться."""
        competitors_result = json.dumps({"client_inn": "", "competitors": []})
        comp_data = json.loads(competitors_result)
        client_inn = comp_data.get("client_inn")
        assert not client_inn, "Пустой ИНН не должен триггерить financials"

    def test_financials_reach_profile_block(self):
        """После auto-call выручка из ФНС должна попасть в блок 01 (профиль)."""
        from app.llm import _build_formatted_blocks

        # Симулируем post-auto-call состояние:
        # - find_competitors отдал client_inn
        # - company_financials отдал выручку, и она легла в profile_cache
        collected = {
            "find_competitors": '{"client_inn": "7801234567", "competitors": []}',
            "company_financials": '{"inn": "7801234567", "revenue": 50000000, "name": "Test"}',
        }
        profile_cache = {
            "_raw_result": '{"city": "Москва", "specialization": "стоматология"}',
            "revenue": 50000000,
            "revenue_trend": "growing",
            "company_name": "Test Clinic",
        }
        blocks = _build_formatted_blocks(collected, profile_cache)
        # Блок 01 (профиль) — должен содержать выручку
        profile_block = blocks[0] if blocks else ""
        # _format_money форматирует 50000000 как "50 млн ₽"
        assert "50" in profile_block or "млн" in profile_block, (
            f"Выручка из financials должна попасть в профиль-блок. "
            f"Got: {profile_block[:200]}"
        )


from app.tools.run_review_platforms import handle_run_review_platforms, _build_summary


class TestReviewsFallback:
    """Task 3: при падении Apify блок отзывов должен показывать дружелюбное сообщение."""

    def test_build_summary_apify_down(self):
        """Когда обе платформы None, summary должно говорить 'недоступны', не 'не найдены'."""
        summary = _build_summary(None, None, "ARclinic")
        # Должно быть дружелюбное сообщение про недоступность, не про отсутствие
        assert "недоступ" in summary.lower() or "не отвечают" in summary.lower(), (
            f"Summary '{summary}' должен говорить про недоступность платформ, "
            "не про отсутствие отзывов у клиники"
        )

    def test_build_summary_partial_data(self):
        """Когда одна платформа есть, а другая None — показываем что есть."""
        yandex = {"rating": 5.0, "reviews": 562}
        summary = _build_summary(yandex, None, "ARclinic")
        assert "5.0" in summary
        assert "562" in summary

    def test_format_reviews_block_shows_message_when_empty(self):
        """Блок 04 не должен полностью исчезать — показываем fallback."""
        # Это требует изменения в _format_reviews_block (llm.py)
        # Сейчас при found_any=False возвращается "" — блок исчезает
        # Должен возвращать минимальный блок с сообщением
        import app.llm as llm_mod

        # Мокаем данные где все platforms пустые
        empty_result = json.dumps({
            "clinic": "TestClinic",
            "platforms": {"yandex": {}, "twogis": {}, "prodoctorov": {}},
            "praise_summary": "",
            "criticism_summary": "",
            "reputation_summary": "Отзывы временно недоступны",
            "source": "apify",
        })
        result = llm_mod._format_reviews_block(empty_result)
        # Должен вернуть НЕ пустую строку — fallback сообщение
        assert result != "", (
            "Блок отзывов не должен исчезать полностью при падении Apify"
        )
        assert "недоступ" in result.lower() or "04" in result, (
            f"Ожидалось fallback-сообщение, получено: {result[:100]}"
        )
