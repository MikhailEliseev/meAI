"""
quick_overview — Hermes tool: Perplexity-fast clinic overview (Phase 1 hook)

Calls Perplexity API (sonar-pro) for a rapid 6-section snapshot:
  BUSINESS, DOCTORS, COMPETITORS, SOCIAL, WEBSITE, HOOK

Runs in PARALLEL with run_prescan via asyncio.gather() in _presale_prompt().
Returns within ~5 seconds — the "wow effect" before prescan stages arrive.

Perplexity API is OpenAI-compatible (base_url: https://api.perplexity.ai).
API key: PERPLEXITY_API_KEY from env.

Registered in Hermes internal registry under toolset "aim-operations".
"""

import asyncio
import json
import logging
import os
from pathlib import Path

from tools.registry import registry

logger = logging.getLogger(__name__)

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
PERPLEXITY_BASE_URL = "https://api.perplexity.ai"
PERPLEXITY_MODEL = "sonar-pro"
REQUEST_TIMEOUT = 45.0  # Perplexity can take 30-45s (was 15s, caused APITimeoutError)
MAX_RETRIES = 1  # one retry if first call fails


def _load_prompt_template() -> str:
    """Load the quick_overview prompt template."""
    prompt_path = Path(__file__).parent.parent / "prompts" / "quick_overview.txt"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    logger.warning("quick_overview prompt file not found at %s", prompt_path)
    # Fallback — minimal prompt
    return (
        "Ты — AI-аналитик медицинского маркетинга. Изучи клинику по URL {url}.\n"
        "Собери: название, юрлицо, ИНН, выручку, город, специализацию, "
        "3-5 врачей, 3-5 конкурентов, соцсети, платформу сайта, "
        "один неожиданный факт. Каждый факт со ссылкой на источник."
    )


async def handle_quick_overview(url=None, **kwargs) -> str:
    """Get a rapid Perplexity-powered overview of a clinic.

    Runs in parallel with run_prescan. Returns in ~5 seconds.
    6 sections: БИЗНЕС, ВРАЧИ, КОНКУРЕНТЫ, СОЦСЕТИ, САЙТ, ЗАЦЕПКА.

    Args:
        url: Client clinic website URL

    Returns:
        JSON string with "overview_text" (2-3 paragraph narrative) and
        "sections" dict with structured data.
    """
    if isinstance(url, dict):
        url = url.get("url", "")

    if not url:
        return json.dumps({"error": "url is required"})

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    if not PERPLEXITY_API_KEY:
        return json.dumps({
            "error": "PERPLEXITY_API_KEY not configured",
            "overview_text": (
                f"Вижу сайт {url}. Загружаю данные… "
                "Для быстрого анализа подключите Perplexity API ключ."
            ),
        })

    logger.info("Running quick_overview for URL: %s", url)

    from app.main import push_tool_progress

    push_tool_progress("quick_overview", f"⚡ Perplexity: изучаю {url}…")

    prompt_template = _load_prompt_template()
    user_prompt = prompt_template.replace("{url}", url)

    last_error = None
    for attempt in range(1, MAX_RETRIES + 2):  # 1 initial + retries
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(
                api_key=PERPLEXITY_API_KEY,
                base_url=PERPLEXITY_BASE_URL,
                timeout=REQUEST_TIMEOUT,
            )

            response = await client.chat.completions.create(
                model=PERPLEXITY_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Ты — AI-аналитик медицинского маркетинга. "
                            "Изучи клинику по URL. Отвечай только фактами из источников. "
                            "Каждый факт — со ссылкой. Без воды."
                        ),
                    },
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=2000,
            )

            overview_text = response.choices[0].message.content or ""

            push_tool_progress(
                "quick_overview",
                "✅ Perplexity: данные получены",
            )

            return json.dumps({
                "url": url,
                "overview_text": overview_text,
                "model": PERPLEXITY_MODEL,
            }, ensure_ascii=False, indent=2)

        except Exception as e:
            last_error = e
            if attempt <= MAX_RETRIES:
                logger.warning(
                    "Perplexity quick_overview attempt %d failed (%s: %s), retrying in 2s…",
                    attempt, type(e).__name__, e,
                )
                await asyncio.sleep(2)
            else:
                logger.exception("Perplexity quick_overview failed after %d attempts for %s", attempt, url)

    # All attempts exhausted — graceful degradation
    return json.dumps({
        "url": url,
        "overview_text": (
            f"Анализирую сайт {url}. "
            "Первичные данные загружаются — через несколько секунд "
            "покажу финансовые показатели, конкурентов и SEO."
        ),
        "error": str(last_error),
        "degraded": True,
    }, ensure_ascii=False, indent=2)


# ── Registry ───────────────────────────────────────────────────────────────

registry.register(
    name="quick_overview",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "quick_overview",
            "description": (
                "RAPID Perplexity-powered overview of a clinic website (~5 seconds). "
                "Returns 6 sections: BUSINESS (name, legal entity, INN, revenue), "
                "DOCTORS (3-5 key doctors), COMPETITORS (3-5 nearby), "
                "SOCIAL (Instagram, VK, Telegram, YouTube, Yandex Maps), "
                "WEBSITE (platform, quality, page count), "
                "HOOK (one surprising fact for the owner). "
                "Use this TOGETHER with run_prescan at the START of presale — "
                "call BOTH in parallel for immediate wow effect while deeper scan runs."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Client clinic website URL (e.g., 'https://clinic.ru')",
                    },
                },
                "required": ["url"],
            },
        },
    },
    handler=handle_quick_overview,
    check_fn=lambda: bool(PERPLEXITY_API_KEY),
    is_async=True,
    description="Perplexity-powered clinic overview (6 sections, ~5s). Parallel with run_prescan for wow effect.",
    emoji="⚡",
)
