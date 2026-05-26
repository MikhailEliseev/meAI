"""Unit tests for DialogueManager.

Covers: system prompt embedding, hook prompt generation (with and without
competitors), fallback response rendering, and chat() flow (LLM vs no-LLM).
"""

import pytest

from AIM.src.aim.services.ci.comparison_matrix import ComparisonMatrixBuilder
from AIM.src.aim.services.ci.dialogue_manager import (
    SYSTEM_PROMPT_TEMPLATE,
    DialogueManager,
)
from AIM.src.aim.services.ci.models import (
    CompetitorFull,
    SeoAuditResult,
    SocialScanResult,
)


class TestDialogueManager:
    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def _make_matrix(self, n_competitors: int = 1):
        """Build a ComparisonMatrix with *n_competitors* simple competitors."""
        builder = ComparisonMatrixBuilder()
        comps = []
        for i in range(n_competitors):
            comps.append(
                CompetitorFull(
                    name=f"Clinic {i}",
                    url=f"https://clinic{i}.ru",
                    financials={
                        "revenue": {"2025": (i + 1) * 10_000_000},
                        "profit": {"2025": (i + 1) * 1_000_000},
                        "trend": "growing",
                    },
                    seo=SeoAuditResult(
                        url=f"https://clinic{i}.ru",
                        score=70 + i * 5,
                        issues=[f"Issue {j}" for j in range(3)],
                    ),
                    social=SocialScanResult(company_name=f"Clinic {i}"),
                    website_features=["booking"],
                    positioning=f"Тестовое позиционирование {i}",
                )
            )
        return builder.build("https://client.ru", {"booking": True}, comps)

    # ------------------------------------------------------------------
    # build_system_prompt
    # ------------------------------------------------------------------

    def test_build_system_prompt_embeds_data(self):
        """System prompt must contain client URL, competitor name, and rules."""
        dm = DialogueManager()
        matrix = self._make_matrix(1)

        prompt = dm.build_system_prompt(matrix)

        # Client data embedded
        assert "https://client.ru" in prompt
        # Competitor data embedded
        assert "Clinic 0" in prompt
        # Rules from the template are present
        assert "НИКАКИХ ВЫДУМОК" in prompt
        assert "СРАВНИВАЙ С КЛИЕНТОМ" in prompt
        # Template sections present
        assert "=== ДАННЫЕ КЛИЕНТА ===" in prompt
        assert "=== ДАННЫЕ КОНКУРЕНТОВ ===" in prompt
        assert "=== ПРАВИЛА ===" in prompt
        assert "=== ФОРМАТ ОТВЕТА ===" in prompt

    # ------------------------------------------------------------------
    # build_hook_prompt
    # ------------------------------------------------------------------

    def test_build_hook_prompt_with_competitors(self):
        """With 2 competitors hook must mention revenue and end with the
        comparison-choice question."""
        dm = DialogueManager()
        matrix = self._make_matrix(2)

        prompt = dm.build_hook_prompt(matrix)

        # Revenue figures for both competitors
        assert "10.0 млн ₽" in prompt  # Clinic 0: 10M
        assert "20.0 млн ₽" in prompt  # Clinic 1: 20M
        # Competitor names
        assert "Clinic 0" in prompt
        assert "Clinic 1" in prompt
        # Must end with the question
        assert "По кому показать сравнение первым?" in prompt
        # Hook instruction
        assert "HOOK" in prompt

    def test_build_hook_prompt_empty(self):
        """With 0 competitors returns the no-competitors message."""
        dm = DialogueManager()
        matrix = self._make_matrix(0)

        prompt = dm.build_hook_prompt(matrix)

        assert prompt == "Конкурентов не найдено. Я не могу построить анализ."

    # ------------------------------------------------------------------
    # _fallback_response
    # ------------------------------------------------------------------

    def test_fallback_response_has_competitor_data(self):
        """Fallback contains competitor name, revenue, SEO score, and website
        features."""
        builder = ComparisonMatrixBuilder()
        comp = CompetitorFull(
            name="TestClinic",
            url="https://test.ru",
            financials={
                "revenue": {"2025": 10_000_000},
                "profit": {"2025": 1_000_000},
                "trend": "growing",
            },
            seo=SeoAuditResult(
                url="https://test.ru",
                score=80,
                issues=["Missing H1", "Slow load"],
            ),
            social=SocialScanResult(company_name="TestClinic"),
            website_features=["booking", "chat"],
        )
        matrix = builder.build(
            "https://client.ru", {"booking": True}, [comp], client_name="ClientCo"
        )

        dm = DialogueManager()
        text = dm._fallback_response(matrix)

        # Competitor name
        assert "TestClinic" in text
        # Revenue
        assert "10.0 млн ₽" in text
        # SEO score
        assert "80/100" in text
        # SEO issues
        assert "Missing H1" in text
        # Website features
        assert "booking" in text
        assert "chat" in text
        # Structure markers
        assert "### Финансы" in text
        assert "### SEO" in text
        assert "### Соцсети" in text
        assert "### Сайт" in text
        assert "## Итог" in text

    def test_fallback_response_empty(self):
        """Matrix with no competitors produces the empty report."""
        dm = DialogueManager()
        matrix = self._make_matrix(0)

        text = dm._fallback_response(matrix)

        assert "Конкурентный анализ" in text
        assert "Найдено конкурентов: **0**" in text
        assert "## Итог" in text

    def test_fallback_client_name_fallback(self):
        """When client has no name, 'Ваш сайт' is used."""
        dm = DialogueManager()
        matrix = self._make_matrix(1)

        text = dm._fallback_response(matrix)
        assert "Ваш сайт" in text

    # ------------------------------------------------------------------
    # chat()
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_chat_returns_fallback_when_no_llm(self):
        """When llm_client is None, chat() returns the fallback response."""
        dm = DialogueManager(llm_client=None)
        matrix = self._make_matrix(1)

        reply = await dm.chat(matrix, "Расскажи про Clinic 0")

        # Should be the fallback (structured markdown)
        assert "Конкурентный анализ" in reply
        assert "Clinic 0" in reply
        assert "## Итог" in reply

    @pytest.mark.asyncio
    async def test_chat_constructs_correct_messages(self):
        """chat() must pass the correct messages list: [system, ...history, user]."""
        captured_messages = None

        async def mock_llm(messages):
            nonlocal captured_messages
            captured_messages = messages
            return "Mock LLM reply"

        dm = DialogueManager(llm_client=mock_llm)
        matrix = self._make_matrix(1)

        history = [
            {"role": "user", "content": "Кто конкуренты?"},
            {"role": "assistant", "content": "Вот список..."},
        ]

        reply = await dm.chat(matrix, "Расскажи про Clinic 0", history=history)

        # LLM returned its mock value
        assert reply == "Mock LLM reply"

        # Verify message structure
        assert captured_messages is not None
        assert len(captured_messages) == 4  # system + 2 history + 1 user

        # First message: system
        assert captured_messages[0]["role"] == "system"
        assert "https://client.ru" in captured_messages[0]["content"]
        assert "Clinic 0" in captured_messages[0]["content"]

        # History preserved
        assert captured_messages[1] == history[0]
        assert captured_messages[2] == history[1]

        # Last message: user input
        assert captured_messages[3]["role"] == "user"
        assert captured_messages[3]["content"] == "Расскажи про Clinic 0"

    @pytest.mark.asyncio
    async def test_chat_no_history(self):
        """chat() without history passes only [system, user]."""
        captured_messages = None

        async def mock_llm(messages):
            nonlocal captured_messages
            captured_messages = messages
            return "OK"

        dm = DialogueManager(llm_client=mock_llm)
        matrix = self._make_matrix(1)

        await dm.chat(matrix, "Привет")

        assert captured_messages is not None
        assert len(captured_messages) == 2
        assert captured_messages[0]["role"] == "system"
        assert captured_messages[1] == {"role": "user", "content": "Привет"}

    @pytest.mark.asyncio
    async def test_chat_fallback_on_llm_error(self):
        """When the LLM raises, chat() falls back gracefully."""
        async def broken_llm(messages):
            raise RuntimeError("API unavailable")

        dm = DialogueManager(llm_client=broken_llm)
        matrix = self._make_matrix(1)

        reply = await dm.chat(matrix, "Что там?")

        # Should return fallback output, not raise
        assert "Конкурентный анализ" in reply
        assert "Clinic 0" in reply

    # ------------------------------------------------------------------
    # _format_revenue
    # ------------------------------------------------------------------

    def test_format_revenue_millions(self):
        assert DialogueManager._format_revenue(10_000_000) == "10.0 млн ₽"
        assert DialogueManager._format_revenue(1_500_000) == "1.5 млн ₽"

    def test_format_revenue_billions(self):
        assert DialogueManager._format_revenue(1_000_000_000) == "1.0 млрд ₽"
        assert DialogueManager._format_revenue(2_500_000_000) == "2.5 млрд ₽"

    def test_format_revenue_small(self):
        result = DialogueManager._format_revenue(500_000)
        assert "500" in result
        assert "000" in result or "500 000" in result

    def test_format_revenue_non_numeric(self):
        assert DialogueManager._format_revenue("N/A") == "N/A"
        assert DialogueManager._format_revenue(None) == "None"

    # ------------------------------------------------------------------
    # build_system_messages
    # ------------------------------------------------------------------

    def test_build_system_messages_returns_list_with_system(self):
        dm = DialogueManager()
        matrix = self._make_matrix(1)

        messages = dm.build_system_messages(matrix)

        assert isinstance(messages, list)
        assert len(messages) == 1
        assert messages[0]["role"] == "system"
        assert "https://client.ru" in messages[0]["content"]
