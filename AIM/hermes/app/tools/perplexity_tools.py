"""
perplexity_tools — Hermes tools: Flexible AI-powered search & analysis.

Uses Perplexity API (sonar-pro) if PERPLEXITY_API_KEY is configured,
falls back to the configured LLM (DeepSeek via OMNIROUTE) otherwise.

Tools:
- perplexity_search: Flexible research query with custom prompt
- perplexity_deep_analyze: Deep multi-angle analysis of a topic

Matches Perplexity MCP server capabilities (flexible search + analysis).
"""

import json
import logging
import os

from tools.registry import registry

logger = logging.getLogger(__name__)

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "").strip()
PERPLEXITY_BASE_URL = "https://api.perplexity.ai"
PERPLEXITY_MODEL = "sonar-pro"

# Fallback: use the configured LLM
LLM_BASE_URL = os.getenv("LLM_BASE_URL", os.getenv("OMNIROUTE_URL", "https://api.deepseek.com/v1"))
LLM_API_KEY = os.getenv("LLM_API_KEY", os.getenv("OMNIROUTE_AUTH", os.getenv("DEEPSEEK_API_KEY", "")))
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

USE_PERPLEXITY = bool(PERPLEXITY_API_KEY)
logger.info("perplexity_tools: PERPLEXITY=%s, LLM fallback=%s", "available" if USE_PERPLEXITY else "unavailable", LLM_MODEL)


def _build_system_prompt() -> str:
    return (
        "Ты — AI-аналитик медицинского маркетинга. "
        "Твоя задача — глубокий анализ и фактические ответы. "
        "Каждый факт подкрепляй источником. "
        "Без воды, без общих фраз. "
        "Если данных недостаточно — честно скажи об этом."
    )


async def _call_perplexity(prompt: str, model: str = None, temperature: float = 0.3, max_tokens: int = 12000) -> str:
    """Call Perplexity API (OpenAI-compatible)."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=PERPLEXITY_API_KEY,
        base_url=PERPLEXITY_BASE_URL,
        timeout=90.0,
    )

    response = await client.chat.completions.create(
        model=model or PERPLEXITY_MODEL,
        messages=[
            {"role": "system", "content": _build_system_prompt()},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""


async def _call_llm(prompt: str, temperature: float = 0.3, max_tokens: int = 12000) -> str:
    """Call configured LLM (DeepSeek via OMNIROUTE)."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        timeout=90.0,
    )

    response = await client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": _build_system_prompt()},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""


# ── Tool: perplexity_search ────────────────────────────────────────

async def handle_perplexity_search(question=None, context=None, model=None, **kwargs) -> str:
    """Flexible AI-powered research query.

    Args:
        question: Research question to answer
        context: Optional background context (market, competitors, etc.)
        model: Model override (only for Perplexity: sonar-pro, sonar, sonar-reasoning)
    """
    if isinstance(question, dict):
        d = question
        question = d.get("question", d.get("query", ""))
        context = d.get("context", context)
        model = d.get("model", model)

    if not question:
        return json.dumps({"error": "question is required"})

    logger.info("perplexity_search: %s (perplexity=%s)", question[:80], USE_PERPLEXITY)

    from app.main import push_tool_progress
    push_tool_progress("perplexity", f"🔍 Анализирую: {question[:60]}…")

    prompt = question
    if context:
        prompt = f"КОНТЕКСТ:\n{context}\n\nВОПРОС:\n{question}"

    try:
        if USE_PERPLEXITY:
            answer = await _call_perplexity(prompt, model=model)
            source = f"perplexity ({model or PERPLEXITY_MODEL})"
        else:
            answer = await _call_llm(prompt)
            source = f"llm ({LLM_MODEL})"

        push_tool_progress("perplexity", "✅ Анализ завершён")
        return json.dumps({
            "question": question,
            "answer": answer,
            "source": source,
            "has_context": bool(context),
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error("perplexity_search failed: %s", str(e)[:200])
        return json.dumps({
            "error": str(e)[:500],
            "question": question,
        })


# ── Tool: perplexity_deep_analyze ───────────────────────────────────

async def handle_perplexity_deep_analyze(topic=None, angles=None, context=None, **kwargs) -> str:
    """Deep multi-angle analysis of a topic.

    Args:
        topic: Main topic to analyze
        angles: List of analysis angles (e.g., ['market', 'competitors', 'risks'])
        context: Optional background context
    """
    if isinstance(topic, dict):
        d = topic
        topic = d.get("topic", "")
        angles = d.get("angles", angles)
        context = d.get("context", context)

    if not topic:
        return json.dumps({"error": "topic is required"})

    angle_list = angles if angles else ["market", "competitors", "opportunities", "risks"]
    if isinstance(angle_list, str):
        angle_list = [a.strip() for a in angle_list.split(",")]

    logger.info("perplexity_deep_analyze: %s (angles=%d, perplexity=%s)", topic[:80], len(angle_list), USE_PERPLEXITY)

    from app.main import push_tool_progress
    push_tool_progress("perplexity", f"🧠 Глубокий анализ: {topic[:60]}…")

    prompt_parts = [f"ТЕМА АНАЛИЗА: {topic}"]
    if context:
        prompt_parts.append(f"КОНТЕКСТ:\n{context}")
    prompt_parts.append(f"Проанализируй тему с {len(angle_list)} ракурсов: {', '.join(angle_list)}.")
    prompt_parts.append("По каждому ракурсу — 2-3 конкретных факта с источниками.")
    prompt_parts.append("Формат ответа: для каждого ракурса — короткий раздел с заголовком.")

    prompt = "\n\n".join(prompt_parts)

    try:
        if USE_PERPLEXITY:
            answer = await _call_perplexity(prompt, max_tokens=4000)
            source = f"perplexity ({PERPLEXITY_MODEL})"
        else:
            answer = await _call_llm(prompt, max_tokens=4000)
            source = f"llm ({LLM_MODEL})"

        push_tool_progress("perplexity", "✅ Глубокий анализ завершён")
        return json.dumps({
            "topic": topic,
            "angles_analyzed": angle_list,
            "analysis": answer,
            "source": source,
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error("perplexity_deep_analyze failed: %s", str(e)[:200])
        return json.dumps({
            "error": str(e)[:500],
            "topic": topic,
        })


# ── Register tools ──────────────────────────────────────────────────

def _check_perplexity():
    return USE_PERPLEXITY or bool(LLM_API_KEY)


registry.register(
    name="perplexity_search",
    toolset="aim-operations",
    schema={
            "name": "perplexity_search",
            "description": (
                "Flexible AI-powered research query. Ask any question and get a "
                "well-researched answer with sources. "
                + ("Uses Perplexity sonar-pro for live web search. " if USE_PERPLEXITY else "Uses LLM for analysis. ")
                + "Use for: market research, competitor analysis, trend identification, "
                "answering specific questions about the medical market. "
                "More flexible than quick_overview — custom questions, any topic."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "[REQUIRED] Research question to answer",
                    },
                    "context": {
                        "type": "string",
                        "description": "Optional: background context (market data, competitor info, etc.)",
                    },
                    "model": {
                        "type": "string",
                        "enum": ["sonar-pro", "sonar", "sonar-reasoning"],
                        "description": "Model override (only for Perplexity, default: sonar-pro)",
                    },
                },
                "required": ["question"],
            },
        },
    handler=handle_perplexity_search,
    check_fn=_check_perplexity,
    is_async=True,
    description="Flexible AI-powered research query (Perplexity or LLM fallback)",
    emoji="🔍",
)

registry.register(
    name="perplexity_deep_analyze",
    toolset="aim-operations",
    schema={
            "name": "perplexity_deep_analyze",
            "description": (
                "Deep multi-angle analysis of any topic. Analyzes from multiple "
                "perspectives (market, competitors, opportunities, risks by default). "
                + ("Uses Perplexity for live web research. " if USE_PERPLEXITY else "Uses LLM for analysis. ")
                + "Use for: SWOT analysis, market entry strategy, competitive positioning, "
                "deep dive into any business question. "
                "Returns structured analysis with sources."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "[REQUIRED] Main topic for analysis",
                    },
                    "angles": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Analysis angles (default: ['market', 'competitors', 'opportunities', 'risks'])",
                    },
                    "context": {
                        "type": "string",
                        "description": "Optional: background context to inform the analysis",
                    },
                },
                "required": ["topic"],
            },
        },
    handler=handle_perplexity_deep_analyze,
    check_fn=_check_perplexity,
    is_async=True,
    description="Deep multi-angle AI analysis (Perplexity or LLM fallback)",
    emoji="🧠",
)
