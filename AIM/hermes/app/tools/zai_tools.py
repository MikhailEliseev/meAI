"""zai_tools — Hermes tools using z.ai Coding Plan built-in services.

Three tools that complement existing scrapers/search:

1. zai_reader — read URL via z.ai's web reader (free under Coding Plan).
   Alternative to web_fetch for cases where z.ai's reader gives better results
   (handles JS-rendered sites, returns cleaned markdown).

2. zai_search — web search via z.ai's chat completion with web_search tool
   injection. Uses Coding Plan quota (not the standalone /web_search which
   requires separate package).

3. zai_zread — AI document summarization via chat completion. Sends a URL or
   document text to glm-5 with instruction to summarize. Alternative to
   perplexity_deep_analyze for content comprehension tasks.

All three use OMNIROUTE_URL + OMNIROUTE_AUTH env vars (z.ai credentials).
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

OMNIROUTE_URL = os.getenv("OMNIROUTE_URL", "https://api.z.ai/api/coding/paas/v4")
OMNIROUTE_AUTH = os.getenv("OMNIROUTE_AUTH", "")
DEFAULT_MODEL = os.getenv("LLM_MODEL", "glm-5")


def _client_timeout() -> httpx.Client:
    return httpx.Client(timeout=60.0)


async def handle_zai_reader(url: str | None = None, **kwargs) -> str:
    """Read URL content via z.ai /reader endpoint.

    Returns cleaned markdown content. Useful for:
    - JS-rendered sites where web_fetch returns empty
    - Articles with paywalls (z.ai reader often bypasses)
    - Getting markdown instead of HTML for cleaner LLM processing

    Args:
        url: URL to read
    """
    if isinstance(url, dict):
        url = url.get("url", "")

    if not url:
        return json.dumps({"error": "url is required"})

    base = OMNIROUTE_URL.rstrip("/")
    logger.info("zai_reader: %s", url[:120])

    try:
        with _client_timeout() as client:
            resp = client.post(
                f"{base}/reader",
                headers={
                    "Authorization": f"Bearer {OMNIROUTE_AUTH}",
                    "Content-Type": "application/json",
                },
                json={"url": url},
            )

        if resp.status_code != 200:
            return json.dumps({
                "error": f"z.ai reader returned {resp.status_code}",
                "detail": resp.text[:300],
            }, ensure_ascii=False)

        data = resp.json()
        result = data.get("reader_result", {})
        content = result.get("content", "") if isinstance(result, dict) else ""

        return json.dumps({
            "url": url,
            "model": data.get("model", "web-reader"),
            "content_chars": len(content),
            "content": content[:10000],  # cap for tool result
        }, ensure_ascii=False)

    except Exception as exc:
        logger.exception("zai_reader failed")
        return json.dumps({"error": str(exc)})


async def handle_zai_search(
    query: str | None = None,
    search_engine: str = "search_std",
    **kwargs,
) -> str:
    """Web search via z.ai chat completion with web_search tool.

    Uses Coding Plan quota (NOT standalone /web_search which needs package).
    Injects web_search tool into chat completion; glm-5 may or may not use it
    based on its judgment.

    Args:
        query: Search query (Russian or English)
        search_engine: "search_std" (default, cheapest), "search_pro" (better)
    """
    if isinstance(query, dict):
        query = query.get("query", "")

    if not query:
        return json.dumps({"error": "query is required"})

    base = OMNIROUTE_URL.rstrip("/")
    logger.info("zai_search: %s (engine=%s)", query[:100], search_engine)

    try:
        with _client_timeout() as client:
            resp = client.post(
                f"{base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OMNIROUTE_AUTH}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": DEFAULT_MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": query,
                        }
                    ],
                    "tools": [
                        {
                            "type": "web_search",
                            "web_search": {
                                "search_engine": search_engine,
                                "search_result": True,
                            },
                        }
                    ],
                    "stream": False,
                    "max_tokens": 2000,
                    "reasoning": {"enabled": False},
                    "thinking": {"type": "disabled"},
                },
            )

        if resp.status_code != 200:
            return json.dumps({
                "error": f"z.ai returned {resp.status_code}",
                "detail": resp.text[:300],
            }, ensure_ascii=False)

        data = resp.json()
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})

        content = message.get("content", "")
        # web_search may also return search_result in the message
        search_results = message.get("web_search", [])

        return json.dumps({
            "query": query,
            "search_engine": search_engine,
            "answer_chars": len(content),
            "answer": content,
            "sources_count": len(search_results) if isinstance(search_results, list) else 0,
            "sources": search_results[:5] if isinstance(search_results, list) else [],
        }, ensure_ascii=False)

    except Exception as exc:
        logger.exception("zai_search failed")
        return json.dumps({"error": str(exc)})


async def handle_zai_zread(
    url: str | None = None,
    question: str | None = None,
    **kwargs,
) -> str:
    """AI document reading via z.ai: read URL then answer question.

    Combines /reader (fetch URL) + chat completion (answer question about it).
    Alternative to perplexity_deep_analyze for URL-based analysis.

    Args:
        url: URL of the document/article to analyze
        question: Specific question about the document
            (default: "Summarize key points in 5 bullets")
    """
    if isinstance(url, dict):
        url = url.get("url")
        question = url.get("question") if isinstance(url, dict) else None

    if not url:
        return json.dumps({"error": "url is required"})

    if not question:
        question = "Выдели 5 ключевых тезисов из этого документа в виде маркированного списка"

    base = OMNIROUTE_URL.rstrip("/")
    logger.info("zai_zread: %s (question=%s)", url[:100], question[:80])

    try:
        # Step 1: read URL via /reader
        with _client_timeout() as client:
            reader_resp = client.post(
                f"{base}/reader",
                headers={
                    "Authorization": f"Bearer {OMNIROUTE_AUTH}",
                    "Content-Type": "application/json",
                },
                json={"url": url},
            )

        if reader_resp.status_code != 200:
            return json.dumps({
                "error": f"reader failed: {reader_resp.status_code}",
                "detail": reader_resp.text[:200],
            }, ensure_ascii=False)

        reader_data = reader_resp.json().get("reader_result", {})
        document = reader_data.get("content", "") if isinstance(reader_data, dict) else ""

        if not document:
            return json.dumps({"error": "no content extracted from URL"})

        # Step 2: ask glm-5 the question about the document
        with _client_timeout() as client:
            chat_resp = client.post(
                f"{base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OMNIROUTE_AUTH}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": DEFAULT_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Ты анализируешь документ. Отвечай на русском, конкретно, без воды.",
                        },
                        {
                            "role": "user",
                            "content": f"Документ с {url}:\n\n{document[:8000]}\n\nВопрос: {question}",
                        },
                    ],
                    "stream": False,
                    "max_tokens": 2000,
                    "reasoning": {"enabled": False},
                    "thinking": {"type": "disabled"},
                },
            )

        if chat_resp.status_code != 200:
            return json.dumps({
                "error": f"chat failed: {chat_resp.status_code}",
                "document_chars": len(document),
            }, ensure_ascii=False)

        chat_data = chat_resp.json()
        answer = chat_data.get("choices", [{}])[0].get("message", {}).get("content", "")

        return json.dumps({
            "url": url,
            "question": question,
            "document_chars": len(document),
            "answer_chars": len(answer),
            "answer": answer,
        }, ensure_ascii=False)

    except Exception as exc:
        logger.exception("zai_zread failed")
        return json.dumps({"error": str(exc)})


# ── Registry ────────────────────────────────────────────────────────────

from tools.registry import registry  # noqa: E402


registry.register(
    name="zai_reader",
    toolset="aim-operations",
    schema={
        "name": "zai_reader",
        "description": (
            "Читать URL через z.ai Web Reader (бесплатно в Coding Plan). "
            "Возвращает cleaned markdown. ПОЛЕЗНО когда web_fetch вернул пустой JS-контент "
            "или HTML-мусор. Альтернатива crawlee_scrape, но через z.ai. "
            "Используй как ДОПОЛНЕНИЕ для cross-check с web_fetch."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL для чтения (https://...)",
                },
            },
            "required": ["url"],
        },
    },
    handler=handle_zai_reader,
    check_fn=lambda: True,
    is_async=True,
    description="Read URL via z.ai Web Reader (free under Coding Plan)",
    emoji="📖",
)

registry.register(
    name="zai_search",
    toolset="aim-operations",
    schema={
        "name": "zai_search",
        "description": (
            "Web search через z.ai (использует Coding Plan квоту). "
            "Альтернатива perplexity_search для cross-validation. "
            "Возвращает ответ + источники. Используй search_std (быстро, дёшево) "
            "или search_pro (глубже)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Поисковый запрос",
                },
                "search_engine": {
                    "type": "string",
                    "enum": ["search_std", "search_pro"],
                    "description": "search_std (default, дёшево) или search_pro (лучше качество)",
                },
            },
            "required": ["query"],
        },
    },
    handler=handle_zai_search,
    check_fn=lambda: True,
    is_async=True,
    description="Web search via z.ai (Coding Plan)",
    emoji="🔍",
)

registry.register(
    name="zai_zread",
    toolset="aim-operations",
    schema={
        "name": "zai_zread",
        "description": (
            "AI-чтение документа через z.ai: читает URL + отвечает на вопрос. "
            "Комбинация web_reader + glm-5. Альтернатива perplexity_deep_analyze "
            "для анализа конкретного URL. Бесплатно в Coding Plan."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL документа для анализа",
                },
                "question": {
                    "type": "string",
                    "description": "Вопрос о документе (default: 5 ключевых тезисов)",
                },
            },
            "required": ["url"],
        },
    },
    handler=handle_zai_zread,
    check_fn=lambda: True,
    is_async=True,
    description="AI document reader via z.ai (free under Coding Plan)",
    emoji="🧠",
)
