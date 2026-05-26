# AIM/src/aim/services/ci/dialogue_manager.py
"""DialogueManager — LLM-powered expert dialogue for competitive intelligence.

Receives a ComparisonMatrix (client + competitors with 20+ parameters)
and generates a structured expert narrative:
  1. Hook — one key fact per competitor
  2. Expert choice — user picks which competitor to explore
  3. Competitor showcase — finance, SEO, social, website, weakness
  4. Follow-up — suggests next exploration angle
  5. Summary

Key design:
  - Stateless: matrix is passed on every call, no internal storage.
  - history is the last N messages from the conversation (client-side managed).
  - _fallback_response provides a structured markdown summary when no LLM is available.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Optional

from .models import ComparisonMatrix

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt — embedded into every LLM call
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_TEMPLATE = """Ты — Hermes, AI-аналитик агентства AIM. Твоя задача — провести клиента через конкурентный анализ так, как это сделал бы живой эксперт, который реально изучил каждого конкурента.

У тебя есть матрица конкурентного анализа — реальные данные, собранные нашими инструментами. Каждый вывод ты подкрепляешь конкретными цифрами из матрицы, а не общими фразами.

=== ДАННЫЕ КЛИЕНТА ===
{client_json}

=== ДАННЫЕ КОНКУРЕНТОВ ===
{competitors_json}

=== ПРАВИЛА ===
1. НИКАКИХ ВЫДУМОК: бери цифры только из матрицы. Если данных по параметру нет — честно скажи «по этому параметру данных нет».
2. СРАВНИВАЙ С КЛИЕНТОМ: при каждой возможности показывай, как конкурент выглядит на фоне сайта клиента. «У них 40% страниц вне индекса, у вас — 5%».
3. ЖИВОЙ ДИАЛОГ: не лекция. Задавай вопросы, предлагай копнуть глубже. «Интересно посмотреть их цены?», «Сравнить соцсети с вашими?»
4. КОНКРЕТИКА: показывай слабые места конкурентов с цифрами. Не «у них плохое SEO», а «40% страниц не проиндексировано, нет SSL, H1 отсутствует на 12 страницах».
5. НА РУССКОМ: отвечай на русском языке, живым экспертным тоном. Можно использовать «смотрите», «вот это поворот», «а знаете что интересно».
6. СТРУКТУРА: HOOK → выбор конкурента → разбор (финансы → SEO → соцсети → сайт → слабость) → follow-up → итог.
7. ПОЛЬЗА: цель диалога — чтобы клиент ушёл с конкретными инсайтами о конкурентах и пониманием, куда двигаться.

=== ФОРМАТ ОТВЕТА ===
- Первое сообщение (HOOK): 1-2 ярких факта на каждого конкурента, заканчивается вопросом «По кому показать сравнение первым?»
- Разбор конкурента: последовательно финансы, SEO, соцсети, сайт, главная слабость. Каждый блок — 2-4 предложения.
- Follow-up: 1-2 вопроса с конкретными направлениями для дальнейшего разбора.
- Итог: суммаризация по всем конкурентам, главный вывод, рекомендация."""


# ---------------------------------------------------------------------------
# Dialogue manager
# ---------------------------------------------------------------------------

class DialogueManager:
    """LLM-powered dialogue engine for competitive intelligence.

    Receives a ComparisonMatrix on every call (stateless) and produces
    expert narrative: hook, competitor showcase, follow-up questions.

    Usage::

        dm = DialogueManager(llm_client=my_openai_client)
        matrix = builder.build(client_url=..., features=..., competitors_full=...)

        # Generate the hook
        hook = dm.build_hook_prompt(matrix)

        # Continue dialogue
        reply = await dm.chat(matrix, "Расскажи про Юцковскую", history=[])
    """

    def __init__(self, llm_client=None):
        """Initialize dialogue manager.

        Args:
            llm_client: Any async callable with signature
                ``async def llm(messages: list[dict]) -> str``.
                If None, all chat calls fall back to ``_fallback_response``.
        """
        self._llm = llm_client

    # ------------------------------------------------------------------
    # Prompt builders
    # ------------------------------------------------------------------

    def build_system_prompt(self, matrix: ComparisonMatrix) -> str:
        """Build the full system prompt with matrix data embedded as JSON.

        Args:
            matrix: ComparisonMatrix from the pipeline.

        Returns:
            Formatted system prompt string, ready to be the first message
            in the LLM messages list.
        """
        client_json = self._json_dump(matrix.client)
        competitors_json = self._json_dump(matrix.competitors)
        return SYSTEM_PROMPT_TEMPLATE.format(
            client_json=client_json,
            competitors_json=competitors_json,
        )

    def build_hook_prompt(self, matrix: ComparisonMatrix) -> str:
        """Build the initial hook message prompt.

        The hook picks the strongest number (revenue) and the weakest spot
        (SEO gap or social gap) for each competitor, then ends with
        «По кому показать сравнение первым?»

        Args:
            matrix: ComparisonMatrix from the pipeline.

        Returns:
            A ready-to-send user-message string that triggers the hook.
        """
        competitor_names = [c.get("name", f"Конкурент #{c.get('id','?')}") for c in matrix.competitors]
        count = len(competitor_names)

        if count == 0:
            return "Конкурентов не найдено. Я не могу построить анализ."

        # Build competitor facts for the prompt
        facts_parts: list[str] = []
        for c in matrix.competitors:
            parts: list[str] = []
            name = c.get("name", "Конкурент")

            # Revenue — strongest number
            fin = c.get("financials", {})
            rev = fin.get("latest_revenue")
            if rev:
                parts.append(f"выручка {self._format_revenue(rev)}")
            else:
                parts.append("финансовые данные отсутствуют")

            # SEO gap — weakest spot
            seo = c.get("seo", {})
            seo_score = seo.get("score")
            if seo_score is not None and seo_score < 60:
                issues = seo.get("issues", [])
                if issues:
                    parts.append(f"слабое SEO ({issues[0].lower() if issues else f'оценка {seo_score}'})")
                else:
                    parts.append(f"SEO: {seo_score}/100")
            elif seo_score is not None:
                parts.append(f"SEO: {seo_score}/100 (ок)")

            # Social gap
            social = c.get("social", {})
            platforms_found = sum(
                1 for plat in ("instagram", "telegram", "vk", "tiktok")
                if social.get(plat, {}).get("exists")
            )
            if platforms_found <= 1:
                parts.append(f"соцсети почти не ведут ({platforms_found} платформ из 4)")
            else:
                parts.append(f"активны в {platforms_found} соцсетях")

            facts_parts.append(f"- {name}: {', '.join(parts)}")

        facts_block = "\n".join(facts_parts)

        prompt = (
            "Ты начинаешь диалог с клиентом. Вот данные конкурентов:\n\n"
            f"{facts_block}\n\n"
            "Сделай HOOK — один абзац с самыми яркими цифрами (выручка + слабые места). "
            "Говори живо, как эксперт который реально изучил конкурентов. "
            "Закончи вопросом: «По кому показать сравнение первым?»"
        )
        return prompt

    def build_system_messages(self, matrix: ComparisonMatrix) -> list[dict]:
        """Build the initial messages list for a new conversation.

        Returns a list with a single system message.
        Append user/assistant turns and pass to ``chat``.
        """
        return [{"role": "system", "content": self.build_system_prompt(matrix)}]

    # ------------------------------------------------------------------
    # Core dialogue
    # ------------------------------------------------------------------

    async def chat(
        self,
        matrix: ComparisonMatrix,
        message: str,
        history: Optional[list[dict]] = None,
    ) -> str:
        """Process a dialogue turn.

        The matrix is re-embedded into the system prompt on every call,
        keeping the manager stateless. ``history`` contains the last N
        messages (user/assistant pairs) from the ongoing conversation.

        If no LLM client was configured, falls back to
        ``_fallback_response``.

        Args:
            matrix: The comparison matrix (passed on every call).
            message: The user's latest message.
            history: Previous turns as ``[{"role":..., "content":...}, ...]``.

        Returns:
            Assistant reply string.
        """
        if self._llm is None:
            logger.info("No LLM client configured — using fallback response.")
            return self._fallback_response(matrix)

        messages = self.build_system_messages(matrix)
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": message})

        try:
            reply = await self._llm(messages)
            return reply
        except Exception as exc:
            logger.error("LLM call failed: %s", exc, exc_info=True)
            return self._fallback_response(matrix)

    # ------------------------------------------------------------------
    # Fallback
    # ------------------------------------------------------------------

    def _fallback_response(self, matrix: ComparisonMatrix) -> str:
        """Structured markdown summary from matrix data — used when LLM is unavailable.

        Creates a complete analysis text that can be shown to the client
        directly, covering every competitor with revenue, SEO score,
        social presence, and website features.
        """
        client_name = matrix.client.get("name", "Ваш сайт") if matrix.client else "Ваш сайт"
        lines: list[str] = [
            f"# Конкурентный анализ для «{client_name}»",
            "",
            f"Найдено конкурентов: **{len(matrix.competitors)}**",
            "",
        ]

        for i, c in enumerate(matrix.competitors, 1):
            name = c.get("name", f"Конкурент #{c.get('id', '?')}")
            url = c.get("url", "")
            lines.append(f"## {i}. {name}")
            if url:
                lines.append(f"Сайт: {url}")
            lines.append("")

            # Financials
            fin = c.get("financials", {})
            rev = fin.get("latest_revenue")
            profit = fin.get("latest_profit")
            trend = fin.get("trend", "")
            lines.append("### Финансы")
            if rev:
                lines.append(f"- Выручка: {self._format_revenue(rev)}")
            if profit:
                lines.append(f"- Прибыль: {self._format_revenue(profit)}")
            if trend:
                lines.append(f"- Тренд: {trend}")
            if not rev and not profit:
                lines.append("- Финансовые данные отсутствуют")
            lines.append("")

            # SEO
            seo = c.get("seo", {})
            seo_score = seo.get("score")
            lines.append("### SEO")
            if seo_score is not None:
                lines.append(f"- Оценка: **{seo_score}/100**")
            issues = seo.get("issues", [])
            if issues:
                for issue in issues[:5]:
                    lines.append(f"- Проблема: {issue}")
            if seo_score is None and not issues:
                lines.append("- Данные SEO отсутствуют")
            lines.append("")

            # Social
            social = c.get("social", {})
            lines.append("### Соцсети")
            found_any = False
            for plat in ("instagram", "telegram", "vk", "tiktok"):
                pdata = social.get(plat, {})
                if pdata.get("exists"):
                    found_any = True
                    handle = pdata.get("handle", "")
                    posts = pdata.get("posts_month", 0)
                    topics = pdata.get("topics", [])
                    topic_str = f" | темы: {', '.join(topics[:3])}" if topics else ""
                    lines.append(f"- **{plat.capitalize()}**: @{handle} | постов/мес: {posts}{topic_str}")
            if not found_any:
                lines.append("- Соцсети не обнаружены")
            lines.append("")

            # Website
            website = c.get("website", {})
            features = website.get("features", [])
            missing = website.get("missing", [])
            doctors = website.get("doctors_count", 0)
            directions = website.get("directions_claimed", 0)
            pricing = website.get("pricing_visible", False)
            lines.append("### Сайт")
            if features:
                lines.append(f"- Есть: {', '.join(features)}")
            if missing:
                lines.append(f"- Отсутствует: {', '.join(missing)}")
            if doctors:
                lines.append(f"- Врачей: {doctors}")
            if directions:
                lines.append(f"- Направлений заявлено: {directions}")
            lines.append(f"- Цены видны: {'Да' if pricing else 'Нет'}")
            lines.append("")

            # Positioning
            positioning = c.get("positioning", "")
            if positioning:
                lines.append(f"Позиционирование: *{positioning}*")
                lines.append("")

        # Summary
        lines.append("---")
        lines.append("")
        lines.append("## Итог")
        lines.append(
            "Это автоматически сгенерированный отчёт на основе собранных данных. "
            "Для интерактивного диалога с экспертной оценкой подключите LLM."
        )

        if matrix.generated_at:
            lines.append("")
            lines.append(f"_Данные собраны: {matrix.generated_at[:19]}_")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _json_dump(obj: Any) -> str:
        """Serialize object to compact JSON for embedding in prompts."""
        return json.dumps(obj, ensure_ascii=False, indent=2)

    @staticmethod
    def _format_revenue(value: Any) -> str:
        """Format revenue numbers in readable form (e.g. 242176000 -> '242,2 млн ₽')."""
        if isinstance(value, (int, float)):
            num = float(value)
            if num >= 1_000_000_000:
                return f"{num / 1_000_000_000:.1f} млрд ₽"
            elif num >= 1_000_000:
                return f"{num / 1_000_000:.1f} млн ₽"
            else:
                return f"{num:,.0f} ₽".replace(",", " ")
        return str(value)
