"""
run_content_analysis — Hermes tool: Content Analysis (v2)

Использует Perplexity (sonar-pro) для пошагового анализа контента
медицинского сайта: структура, качество, контент-маркетинг, конверсия.

Fallback: DeepSeek через LLM_BASE_URL (если PERPLEXITY_API_KEY не задан).
"""

import json
import logging
import os
import time

from tools.registry import registry

logger = logging.getLogger(__name__)

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "").strip()
PERPLEXITY_BASE_URL = "https://api.perplexity.ai"
PERPLEXITY_MODEL = "sonar-pro"
USE_PERPLEXITY = bool(PERPLEXITY_API_KEY)

# Fallback LLM
LLM_BASE_URL = os.getenv("LLM_BASE_URL", os.getenv("OMNIROUTE_URL", "https://api.deepseek.com/v1"))
LLM_API_KEY = os.getenv("LLM_API_KEY", os.getenv("OMNIROUTE_AUTH", os.getenv("DEEPSEEK_API_KEY", "")))
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

REQUEST_TIMEOUT = 90.0
MAX_TOKENS = 8000

_cache: dict[str, tuple[float, str]] = {}
_CACHE_TTL = 600


def _normalize_args(first_param, defaults):
    """If hermes-agent passes the whole arguments object as first_param, extract all values."""
    if isinstance(first_param, dict):
        return {k: first_param.get(k, defaults[k]) for k in defaults}
    return None


def _build_query(company_name: str, city: str, url: str) -> str:
    """Построить Perplexity-запрос для анализа контента сайта.

    Пошаговый формат — заставляет Perplexity анализировать каждый аспект
    отдельно, а не давать поверхностную оценку.
    """
    target = company_name or url
    location = f" (г. {city})" if city else ""
    website = f", сайт: {url}" if url and url.startswith("http") else ""

    return (
        f"Проанализируй контент сайта клиники «{target}»{location}{website} "
        f"по следующему плану. Для каждого шага зайди на сайт и изучи реальные страницы.\n\n"
        "ВАЖНО: выполняй каждый шаг последовательно. Приводи конкретные примеры "
        "страниц, заголовков, формулировок. Не пиши общими фразами.\n\n"
        "## Шаг 1 — Структура сайта\n"
        "Пройди по навигации сайта и опиши:\n"
        "- Какие разделы есть (услуги, о клинике, врачи, цены, блог, акции, контакты)\n"
        "- Типы страниц: лендинги услуг, статьи блога, карточки врачей, прайс-лист\n"
        "- Глубина навигации (сколько кликов до самой глубокой страницы)\n"
        "- Есть ли хлебные крошки, меню в футере, карта сайта\n"
        "- Примерное количество страниц в каждом разделе\n\n"
        "## Шаг 2 — Качество контента\n"
        "Проанализируй тексты на сайте по критериям:\n"
        "- Медицинская достоверность: указаны ли источники, авторы, есть ли ссылки на исследования\n"
        "- Читабельность: сложность языка, структура текстов (абзацы, подзаголовки, списки)\n"
        "- Уникальность: оригинальный контент или шаблонные тексты\n"
        "- SEO-оптимизация: заголовки H1-H3, мета-теги (title/description), alt у изображений\n"
        "- Приведи 2-3 примера СИЛЬНЫХ страниц (с URL или названиями) — что хорошо сделано\n"
        "- Приведи 2-3 примера СЛАБЫХ страниц — что плохо, как исправить\n\n"
        "## Шаг 3 — Контент-маркетинг\n"
        "Изучи блог и информационные разделы:\n"
        "- Ведёт ли клиника блог? Как часто публикации?\n"
        "- Какие форматы используются: статьи, новости, кейсы, видео, подкасты\n"
        "- Какие темы покрыты: заболевания, методы лечения, профилактика, образ жизни\n"
        "- Качество статей: глубина, актуальность, наличие дат публикации\n"
        "- Есть ли ссылки на соцсети клиники (VK, Telegram, YouTube, Дзен)\n"
        "- Какие темы НЕ покрыты — пробелы в контент-стратегии\n\n"
        "## Шаг 4 — Конверсионные элементы\n"
        "Оцени элементы, превращающие посетителей в пациентов:\n"
        "- CTA (call-to-action): кнопки записи, телефоны, формы обратной связи\n"
        "- Формы захвата: какие данные собирают, на каких страницах расположены\n"
        "- Социальное доказательство: отзывы пациентов, кейсы, фото до/после, лицензии\n"
        "- Прайс-лист: есть ли цены на сайте, насколько прозрачно\n"
        "- Акции и спецпредложения: есть ли, как оформлены\n\n"
        "## ИТОГОВАЯ СВОДКА\n"
        "После анализа всех шагов напиши краткую сводку:\n"
        "- TOP-3 сильных стороны контента (с конкретными примерами)\n"
        "- TOP-3 слабых места (что нужно исправить)\n"
        "- 2 конкретные рекомендации: какой контент добавить в первую очередь и почему"
    )


def _build_system_prompt() -> str:
    return (
        "Ты — контент-аналитик маркетингового агентства AIM, специализирующегося "
        "на медицинском маркетинге. Твоя задача — глубоко проанализировать контент "
        "сайта медицинской клиники. "
        "Ищи реальные страницы, читай тексты, оценивай качество. "
        "Будь конкретен: называй разделы, страницы, формулировки. "
        "Не давай общих оценок вроде «контент хороший» — объясняй почему. "
        "Критикуй конструктивно: каждая проблема должна сопровождаться рекомендацией."
    )


async def _call_perplexity(prompt: str) -> str:
    """Вызвать Perplexity API (sonar-pro, web search)."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=PERPLEXITY_API_KEY,
        base_url=PERPLEXITY_BASE_URL,
        timeout=REQUEST_TIMEOUT,
    )
    response = await client.chat.completions.create(
        model=PERPLEXITY_MODEL,
        messages=[
            {"role": "system", "content": _build_system_prompt()},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=MAX_TOKENS,
    )
    return response.choices[0].message.content or ""


async def _call_llm(prompt: str) -> str:
    """Fallback: LLM через LLM_BASE_URL (без web search)."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        timeout=REQUEST_TIMEOUT,
    )
    response = await client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты — контент-аналитик агентства AIM. "
                    "У тебя нет доступа к интернету, поэтому если ты не можешь "
                    "проанализировать сайт — честно напиши об этом. "
                    "Не выдумывай данные о сайте, которых не видишь."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=MAX_TOKENS,
    )
    return response.choices[0].message.content or ""


async def handle_run_content_analysis(url=None, content_type="all", **kwargs) -> str:
    """Analyze content quality on a medical clinic website.

    Uses Perplexity sonar-pro to perform a step-by-step analysis of:
    site structure, content quality, content marketing, and conversion elements.
    Falls back to LLM if no Perplexity key.

    Args:
        url: Website URL to analyze (e.g., "https://clinic.ru")
        content_type: Type of content to analyze: "all", "blog", "services", "landing"
        company_name: Clinic name for search (from kwargs)
        city: City for geo-targeting (from kwargs)

    Returns:
        JSON string with structured content analysis.
    """
    unpacked = _normalize_args(url, {"url": "", "content_type": "all"})
    if unpacked:
        url = unpacked.get("url", url)
        content_type = unpacked.get("content_type", content_type)

    # Extract company_name and city from kwargs or unpacked args
    company_name = kwargs.get("company_name", "")
    city = kwargs.get("city", "")
    if unpacked:
        if not company_name:
            company_name = unpacked.get("company_name", "")
        if not city:
            city = unpacked.get("city", "")

    search_target = url or company_name or ""
    if not search_target:
        return json.dumps({"error": "URL or clinic name is required"}, ensure_ascii=False)

    # Extract domain as name fallback
    if search_target.startswith("http") and not company_name:
        from urllib.parse import urlparse
        parsed = urlparse(search_target)
        company_name = parsed.netloc.replace("www.", "")

    query_name = company_name or search_target

    cache_key = f"content_v2_{query_name}_{content_type}"
    cached = _cache.get(cache_key)
    if cached is not None:
        cached_ts, cached_result = cached
        if time.time() - cached_ts < _CACHE_TTL:
            logger.info("Content cache HIT for: %s", query_name)
            return cached_result
        del _cache[cache_key]

    logger.info("Content analysis (Perplexity=%s) for: %s, city=%s, type=%s",
                "available" if USE_PERPLEXITY else "unavailable", query_name, city, content_type)

    try:
        from app.main import push_tool_progress

        push_tool_progress("content", f"📝 Анализирую контент {query_name}…")

        query = _build_query(query_name, city, url)
        source = ""

        if USE_PERPLEXITY:
            push_tool_progress("content", "🔍 Perplexity анализирует структуру и качество контента…")
            answer = await _call_perplexity(query)
            source = f"perplexity ({PERPLEXITY_MODEL})"
        else:
            push_tool_progress("content", "⚠️ Perplexity недоступен, использую LLM (без web search)…")
            answer = await _call_llm(query)
            source = f"llm ({LLM_MODEL}) — без веб-поиска"

        push_tool_progress("content", "✅ Контент-анализ завершён")

        result = {
            "url": url,
            "clinic": query_name,
            "city": city or "не указан",
            "content_type": content_type,
            "analysis": answer,
            "source": source,
            "analyzed_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }

        result_json = json.dumps(result, ensure_ascii=False, indent=2)
        _cache[cache_key] = (time.time(), result_json)
        return result_json

    except Exception as e:
        logger.exception("Content analysis error for %s", query_name)
        return json.dumps({
            "error": "Content analysis failed",
            "detail": str(e)[:500],
        }, ensure_ascii=False)


registry.register(
    name="run_content_analysis",
    toolset="aim-operations",
    schema={
            "name": "run_content_analysis",
            "description": (
                "Analyze content quality on a medical clinic website. "
                "Uses Perplexity web search to perform step-by-step analysis of "
                "site structure, content quality, content marketing, and conversion elements. "
                "Evaluates medical accuracy, SEO optimization, readability, "
                "and conversion effectiveness per page type."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Website URL to analyze (e.g., 'https://clinic.ru')",
                    },
                    "content_type": {
                        "type": "string",
                        "description": "Type of content to analyze: all, blog, services, landing",
                        "enum": ["all", "blog", "services", "landing"],
                    },
                },
                "required": ["url"],
            },
        },
    handler=handle_run_content_analysis,
    check_fn=lambda: True,
    is_async=True,
    description="Analyze content quality (Perplexity): structure, SEO, readability, conversion per page type",
    emoji="📝",
)
