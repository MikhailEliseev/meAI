"""SEO + GEO аудит сайта клиники.

Один вызов Firecrawl scrape (главная) + robots.txt + llms.txt → 14 метрик.
Результат: GEO Score (0-100), Schema, AI crawlers, тех.показатели.

Источники знаний: claude-seo (GEO, Schema, Technical SEO skills).
"""

import asyncio
import logging
import re
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

FIRECRAWL_SCRAPE = "https://api.firecrawl.dev/v1/scrape"
REQUEST_TIMEOUT = 25.0

# Ленивая загрузка ключей (shared с firecrawl_enricher)
_fc_keys: list[str] = []
_fc_idx = 0

# AI Crawlers для проверки в robots.txt
_AI_CRAWLERS = {
    "GPTBot": "ChatGPT (OpenAI)",
    "OAI-SearchBot": "OpenAI Search",
    "ClaudeBot": "Claude (Anthropic)",
    "PerplexityBot": "Perplexity AI",
    "CCBot": "Common Crawl",
    "Google-Extended": "Gemini (Google)",
    "Bytespider": "ByteDance / TikTok",
}

# Schema types для medical
_MEDICAL_SCHEMAS = [
    "MedicalBusiness", "MedicalClinic", "Physician", "MedicalOrganization",
    "Hospital", "Dentist", "MedicalProcedure",
]
_ORG_SCHEMAS = ["Organization", "LocalBusiness", "Place", "WebSite", "WebPage"]
_PERSON_SCHEMAS = ["Person", "ProfilePage"]


def _load_keys() -> list[str]:
    """Загружает Firecrawl ключи из env/JSON."""
    global _fc_keys
    if _fc_keys:
        return _fc_keys
    import os, json
    keys = set()
    for prefix in ("FIRECRAWL_API_KEY_", "FIRECRAWL_KEY_"):
        for i in range(1, 21):
            k = os.getenv(f"{prefix}{i:02d}", "") or os.getenv(f"{prefix}{i}", "")
            if k:
                keys.add(k)
    single = os.getenv("FIRECRAWL_API_KEY", "")
    if single:
        keys.add(single)
    pool_path = os.getenv("FIRECRAWL_KEYS_FILE", "/opt/keys/firecrawl.json")
    try:
        if os.path.exists(pool_path):
            with open(pool_path) as f:
                data = json.load(f)
            for entry in data.get("keys", []):
                if entry.get("status") == "active":
                    keys.add(entry.get("token", ""))
    except Exception:
        pass
    _fc_keys = [k for k in keys if k]
    return _fc_keys


async def _fc_scrape(url: str, formats: list[str] = None) -> Optional[dict]:
    """Firecrawl scrape с ротацией ключей."""
    global _fc_idx
    keys = _load_keys()
    if not keys:
        return None
    key = keys[_fc_idx % len(keys)]
    _fc_idx += 1
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        try:
            r = await client.post(FIRECRAWL_SCRAPE,
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"url": url, "formats": formats or ["markdown", "html"], "onlyMainContent": False, "waitFor": 3000})
            if r.status_code == 200:
                return r.json().get("data", {})
        except Exception as e:
            logger.debug("FC scrape failed %s: %s", url[:40], str(e)[:80])
    return None


async def _fc_scrape_text(url: str) -> Optional[str]:
    """Firecrawl scrape → только markdown текст."""
    data = await _fc_scrape(url, ["markdown"])
    return data.get("markdown", "") if data else None


# ── Анализаторы ──────────────────────────────────────────────────────

def _detect_cms(html: str, md: str) -> Optional[str]:
    """Определяет CMS по HTML маркерам."""
    combined = (html + " " + md).lower()
    patterns = {
        "1C-Bitrix": ["bitrix", "bx-core", "1c-bitrix"],
        "Tilda": ["tilda", "tildacdn", "tilda.cc"],
        "WordPress": ["wp-content", "wp-includes", "wordpress"],
        "Joomla": ["joomla"],
        "OpenCart": ["opencart", "oc-"],
        "Drupal": ["drupal"],
        "Wix": ["wix.com", "wixstatic"],
        "Shopify": ["shopify", "cdn.shopify"],
        "MODX": ["modx"],
        "SiteEdit": ["siteedit"],
    }
    for cms, markers in patterns.items():
        if any(m in combined for m in markers):
            return cms
    # meta generator
    gen = re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)', html, re.I)
    if gen:
        gen_text = gen.group(1).strip()
        for cms, markers in patterns.items():
            if cms.lower() in gen_text.lower():
                return cms
        if gen_text:
            return gen_text[:30]
    return None


def _detect_schema(html: str) -> dict:
    """Извлекает JSON-LD schema types из HTML."""
    schemas_found = {"medical": [], "organization": [], "person": [], "other": []}
    # JSON-LD blocks
    jsonld_blocks = re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.I | re.DOTALL)
    for block in jsonld_blocks:
        try:
            import json
            data = json.loads(block.strip())
            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict):
                    continue
                stype = item.get("@type", "")
                if isinstance(stype, list):
                    stype = " ".join(stype)
                stype_str = str(stype)
                if any(s.lower() in stype_str.lower() for s in _MEDICAL_SCHEMAS):
                    schemas_found["medical"].append(stype_str)
                elif any(s.lower() in stype_str.lower() for s in _ORG_SCHEMAS):
                    schemas_found["organization"].append(stype_str)
                elif any(s.lower() in stype_str.lower() for s in _PERSON_SCHEMAS):
                    schemas_found["person"].append(stype_str)
                elif stype_str:
                    schemas_found["other"].append(stype_str)
        except (json.JSONDecodeError, TypeError):
            continue
    # Microdata itemscope
    if re.search(r'itemscope[^>]+itemtype=["\'][^"\']*schema\.org', html, re.I):
        schemas_found["other"].append("Microdata detected")
    return schemas_found


def _check_h1(html: str) -> bool:
    """Проверяет наличие H1 на странице."""
    return bool(re.search(r'<h1[^>]*>', html, re.I))


def _check_meta_description(html: str) -> Optional[str]:
    """Возвращает meta description если есть."""
    m = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)', html, re.I)
    return m.group(1).strip()[:120] if m else None


def _check_og_tags(html: str) -> dict:
    """Проверяет Open Graph теги."""
    og = {}
    for prop in ["og:title", "og:description", "og:image", "og:url"]:
        m = re.search(rf'<meta[^>]+property=["\']({re.escape(prop)})["\'][^>]+content=["\']([^"\']+)', html, re.I)
        if m:
            og[prop] = m.group(2).strip()[:80]
    return og


def _check_ssr(html: str, md: str) -> bool:
    """Проверяет server-side rendering (контент в HTML без JS)."""
    # Если markdown содержит значимый контент → SSR работает
    return len(md.strip()) > 500


def _check_https(url: str) -> bool:
    return url.startswith("https://")


def _parse_robots_for_ai(robots_text: str) -> dict:
    """Анализирует robots.txt на AI crawler доступность.

    Алгоритм (соответствует robots.txt RFC):
    1. Парсим robots.txt по блокам (User-agent → директивы)
    2. Для каждого AI краулера: если есть свой блок → берём его правила
    3. Если своего блока нет → берём правила из User-agent: * блока
    4. Если блока * нет → разрешено по умолчанию
    """
    if not robots_text:
        return {"robots_found": False, "ai_crawlers": {}}

    result = {"robots_found": True, "ai_crawlers": {}}
    lines = robots_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    # Парсим блоки: {user_agent: [directives]}
    blocks: dict[str, list[str]] = {}
    current_agents: list[str] = []

    for line in lines:
        line_lower = line.strip().lower()
        if not line_lower or line_lower.startswith("#"):
            continue
        if line_lower.startswith("user-agent:"):
            agent = line_lower.split(":", 1)[1].strip()
            current_agents = [agent]
            # Могут быть подряд несколько User-agent
            blocks.setdefault(agent, [])
        elif line_lower.startswith(("disallow:", "allow:")) and current_agents:
            directive = line_lower
            for agent in current_agents:
                blocks.setdefault(agent, []).append(directive)

    # Проверяем wildcard блок
    wildcard_rules = blocks.get("*", [])

    def _is_crawler_blocked(crawler_lower: str) -> bool:
        """Возвращает True если краулер заблокирован (Disallow: /)."""
        # Если есть конкретный блок для краулера — он приоритетнее
        if crawler_lower in blocks:
            rules = blocks[crawler_lower]
            for rule in rules:
                if rule.startswith("disallow:"):
                    path = rule.split(":", 1)[1].strip()
                    if path == "/" or path == "":
                        return path == "/"  # Disallow: / = blocked, Disallow: = allowed
            return False  # есть блок, но без Disallow: / → разрешён

        # Нет конкретного блока → используем wildcard
        for rule in wildcard_rules:
            if rule.startswith("disallow:"):
                path = rule.split(":", 1)[1].strip()
                if path == "/":
                    return True
        return False

    for crawler, description in _AI_CRAWLERS.items():
        blocked = _is_crawler_blocked(crawler.lower())
        result["ai_crawlers"][crawler] = {
            "description": description,
            "blocked": blocked,
        }
    return result


def _compute_geo_score(audit: dict) -> int:
    """Вычисляет GEO Score (0-100).

    Формула:
    - AI crawlers open: 25 (максимум если все 4 ключевых открыты)
    - llms.txt: 15
    - MedicalBusiness schema: 20
    - SSR (контент без JS): 15
    - H1 + meta description + OG: 15 (по 5 за каждый)
    - HTTPS: 10
    """
    score = 0

    # AI crawlers (25 max) — GPTBot, ClaudeBot, PerplexityBot, OAI-SearchBot
    ai = audit.get("ai_crawlers", {})
    key_crawlers = ["GPTBot", "ClaudeBot", "PerplexityBot", "OAI-SearchBot"]
    open_count = sum(1 for c in key_crawlers if not ai.get(c, {}).get("blocked", False))
    score += int((open_count / len(key_crawlers)) * 25)

    # llms.txt (15)
    if audit.get("llms_txt"):
        score += 15

    # MedicalBusiness schema (20)
    if audit.get("schema", {}).get("medical"):
        score += 20
    elif audit.get("schema", {}).get("organization"):
        score += 10  # частичный за Organization

    # SSR (15)
    if audit.get("ssr"):
        score += 15

    # H1 + meta + OG (15)
    if audit.get("h1"):
        score += 5
    if audit.get("meta_description"):
        score += 5
    if audit.get("og_tags"):
        score += 5

    # HTTPS (10)
    if audit.get("https"):
        score += 10

    return min(score, 100)


# ── Главная функция ──────────────────────────────────────────────────

async def audit_website(url: str) -> dict:
    """Полный SEO + GEO аудит сайта.

    Делает 3 запроса Firecrawl: главная, robots.txt, llms.txt.
    Возвращает dict со всеми метриками + GEO Score.

    Returns:
        {
            "cms": "1C-Bitrix",
            "geo_score": 35,
            "ai_crawlers": {...},
            "llms_txt": false,
            "schema": {...},
            "h1": true,
            "meta_description": "...",
            "og_tags": {...},
            "ssr": true,
            "https": true,
            "page_size_kb": 45.2,
            "title": "...",
            "scripts_count": 42,
            "images_unoptimized": 15,
            "perf_estimate": "средняя",
            "media_mentions": 3,
        }
    """
    # Нормализуем URL
    if "://" not in url:
        url = "https://" + url

    result = {
        "cms": None, "geo_score": 0, "ai_crawlers": {},
        "llms_txt": False, "schema": {}, "h1": False,
        "meta_description": None, "og_tags": {}, "ssr": False,
        "https": False, "page_size_kb": None, "title": None,
        "scripts_count": None, "perf_estimate": None, "media_mentions": 0,
        "yandex_rating": None, "yandex_reviews": None, "vk_followers": None,
    }

    from urllib.parse import urlparse
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    # Параллельно: главная + robots.txt + llms.txt
    main_data, robots_text, llms_text = await asyncio.gather(
        _fc_scrape(url),
        _fc_scrape_text(f"{base_url}/robots.txt"),
        _fc_scrape_text(f"{base_url}/llms.txt"),
        return_exceptions=True,
    )

    # Анализ главной
    if isinstance(main_data, dict):
        html = main_data.get("html", "")
        md = main_data.get("markdown", "")

        result["cms"] = _detect_cms(html, md)
        result["schema"] = _detect_schema(html)
        result["h1"] = _check_h1(html)
        result["meta_description"] = _check_meta_description(html)
        result["og_tags"] = _check_og_tags(html)
        result["ssr"] = _check_ssr(html, md)
        result["https"] = _check_https(url)
        result["page_size_kb"] = round(len(html.encode("utf-8")) / 1024, 1) if html else None
        # F8: Performance estimate — count scripts, images without lazy loading
        scripts = re.findall(r"<script\b", html, re.I)
        result["scripts_count"] = len(scripts)
        size = result["page_size_kb"] or 0
        n_scripts = len(scripts)
        if size > 500 or n_scripts > 80:
            result["perf_estimate"] = "низкая"
        elif size > 200 or n_scripts > 40:
            result["perf_estimate"] = "средняя"
        else:
            result["perf_estimate"] = "высокая"
        title_m = re.search(r"<title[^>]*>([^<]+)", html, re.I)
        if title_m:
            result["title"] = title_m.group(1).strip()[:100]

    # Robots.txt
    if isinstance(robots_text, str) and robots_text:
        result["ai_crawlers"] = _parse_robots_for_ai(robots_text).get("ai_crawlers", {})
    else:
        # Нет robots.txt → ничего не блокирует (de facto open)
        for crawler in _AI_CRAWLERS:
            result["ai_crawlers"][crawler] = {"blocked": False, "description": _AI_CRAWLERS[crawler]}

    # llms.txt
    if isinstance(llms_text, str) and llms_text and len(llms_text) > 50:
        result["llms_txt"] = True

    # F10: СМИ публикации + F9: Рейтинги Я.Карт (Perplexity)
    try:
        from src.aim.services.lib.perplexity_client import perplexity_chat, is_configured
        if is_configured():
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.replace("www.", "")
            brand = domain.split(".")[0]

            # СМИ
            raw_media = await perplexity_chat(
                [{"role": "user", "content": f"Сколько публикаций о клинике {brand} в СМИ (Forbes, RBC, Vademecum, Коммерсантъ)? Только число."}],
                temperature=0.0,
            )
            nums = re.findall(r"(\d+)", raw_media.strip())
            result["media_mentions"] = int(nums[0]) if nums else 0

            # Рейтинг Я.Карт + отзывы
            raw_rating = await perplexity_chat(
                [{"role": "user", "content": f"Найди рейтинг клиники {brand} на Яндекс.Картах. Верни в формате: рейтинг, количество оценок. Например: 4.8, 4096"}],
                temperature=0.0,
            )
            # Ищем "4.8, 4096" или "4.8/5 (4096 оценок)"
            rating_match = re.search(r"(\d+\.\d+)\D+(\d+)", raw_rating.strip())
            if rating_match:
                result["yandex_rating"] = float(rating_match.group(1))
                result["yandex_reviews"] = int(rating_match.group(2))
    except Exception:
        pass

    # F11: VK подписчики (Firecrawl scrape vk.com page)
    try:
        # Найти VK ссылку из уже скрапленного HTML
        if isinstance(main_data, dict):
            html_content = main_data.get("html", "")
            vk_link = re.search(r'href=["\']([^"\']*vk\.com/[^"\'/?#]+)', html_content, re.I)
            if vk_link:
                vk_url = vk_link.group(1)
                vk_data = await _fc_scrape(vk_url, ["markdown"])
                if vk_data:
                    vk_md = vk_data.get("markdown", "")
                    # VK показывает "1.7K followers" или "1 700 подписчиков"
                    vk_match = re.search(r"\*?\*(\d+[.,]?\d*K?)\*?\*?\s*(?:follower|подписч|участник|member)", vk_md, re.I)
                    if not vk_match:
                        # Альтернативный паттерн: **1.7K** followers
                        vk_match = re.search(r"(\d+[.,]?\d*K?)\s*(?:follower|подписч|участник|member)", vk_md, re.I)
                    if vk_match:
                        vk_str = vk_match.group(1).replace(",", ".").replace(" ", "")
                        if "K" in vk_str.upper():
                            result["vk_followers"] = int(float(vk_str.upper().replace("K", "")) * 1000)
                        else:
                            result["vk_followers"] = int(float(vk_str))
    except Exception:
        pass

    # GEO Score
    result["geo_score"] = _compute_geo_score(result)

    logger.info(
        "SEO audit %s: GEO=%d CMS=%s H1=%s schema_med=%s llms=%s perf=%s media=%d yandex=%.1f vk=%s",
        url[:30], result["geo_score"], result["cms"],
        result["h1"], bool(result.get("schema", {}).get("medical")),
        result["llms_txt"], result.get("perf_estimate"),
        result.get("media_mentions", 0),
        result.get("yandex_rating", 0),
        result.get("vk_followers"),
    )

    return result
