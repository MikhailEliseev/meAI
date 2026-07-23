"""scrape_clinic_website — скрейпит реальный сайт клиники (Phase 13).

Извлекает: врачей, соцсети, услуги, контакты, CMS.
Использует httpx + BeautifulSoup (не Perplexity!).

Подход:
1. Скрейпить главную страницу
2. Найти ссылки на /vrachi, /doctors, /team, /specialists
3. Скрейпить страницы врачей
4. Извлечь имена врачей, соцсети, услуги
"""
import json
import logging
import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.tools.registry import register

logger = logging.getLogger(__name__)

# Таймауты и заголовки
_TIMEOUT = httpx.Timeout(15.0, connect=10.0)
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}

# Паттерны для поиска страниц врачей
DOCTOR_URL_PATTERNS = [
    r"/vrachi", r"/doctors", r"/team", r"/specialists", r"/staff",
    r"/doctors-page", r"/our-doctors", r"/about/doctors",
    r"/klinika/vrachi", r"/klinika/doctors",
    r"/o-nas/vrachi", r"/o-klinike/vrachi",
]

# Паттерны соцсетей (Российские + международные)
SOCIAL_PATTERNS = {
    "instagram": r"instagram\.com/([a-zA-Z0-9_.]+)",
    "vk": r"vk\.com/([a-zA-Z0-9_.]+)",
    "telegram": r"t(?:elegram)?\.me/([a-zA-Z0-9_]+)",
    "youtube": r"youtube\.com/(?:@|channel/|user/|c/)([a-zA-Z0-9_\-]+)",
    "rutube": r"rutube\.ru/(?:u/|channel/)([a-zA-Z0-9_\-]+)",
    "whatsapp": r"wa\.me/(\d+)",
    "dzen": r"dzen\.ru/([a-zA-Z0-9_.]+)",
    "tenchat": r"tenchat\.ru/([a-zA-Z0-9_.]+)",
}


async def _fetch_page(url: str, client: httpx.AsyncClient) -> str | None:
    """Скачать HTML страницу."""
    try:
        resp = await client.get(url, follow_redirects=True)
        if resp.status_code == 200:
            # Попробовать разные кодировки
            if resp.encoding is None or resp.encoding == "ascii":
                resp.encoding = resp.charset_encoding or "utf-8"
            return resp.text
        logger.warning("scrape: %s returned %d", url, resp.status_code)
    except Exception as e:
        logger.warning("scrape: %s failed: %s", url, str(e)[:100])
    return None


def _find_doctor_pages(base_url: str, soup: BeautifulSoup) -> list[str]:
    """Найти ссылки на страницы врачей."""
    doctor_urls = set()
    base_path = urlparse(base_url).path

    for link in soup.find_all("a", href=True):
        href = link["href"].lower()
        for pattern in DOCTOR_URL_PATTERNS:
            if pattern in href:
                full_url = urljoin(base_url, link["href"])
                # Не добавлять external links
                if urlparse(full_url).netloc == urlparse(base_url).netloc:
                    doctor_urls.add(full_url)
                break

    return list(doctor_urls)[:5]  # Максимум 5 страниц врачей


def _extract_doctors(soup: BeautifulSoup, url: str = "") -> list[dict]:
    """Извлечь имена врачей из страницы."""
    doctors = []

    # Попытка 0: meta og:title (Tilda и другие — имя врача в meta)
    og_title = soup.find("meta", attrs={"property": "og:title"})
    if og_title and og_title.get("content"):
        content = og_title["content"].strip()
        # "Батиенко Дарья Дмитриевна - врач ARclinic, Санкт-Петербург"
        # Извлечь имя до первого " - "
        name = content.split(" - ")[0].split(" — ")[0].strip()
        if name and _looks_like_doctor_name(name):
            # Попытка извлечь специализацию
            spec = ""
            if "врач" in content.lower():
                # "Батиенко Д.Д. - врач-косметолог"
                parts = re.split(r'\s*[-–—]\s*', content, maxsplit=1)
                if len(parts) > 1:
                    spec_part = parts[1].strip()
                    # Убрать название клиники и город
                    spec_part = re.sub(r'\b(?:врач|ARclinic|клиник[аи]?)\b', '', spec_part, flags=re.I).strip(" ,.-")
                    if spec_part:
                        spec = spec_part[:80]
            doctors.append({"name": name, "specialization": spec})
            return doctors  # Страница одного врача — возвращаем сразу

    # Попытка 1: Tilda-классы (t-name, t-title)
    tilda_selectors = ["t-name", "t-name_xl", "t-name_md", "t-title", "t-heading"]
    for cls in tilda_selectors:
        elements = soup.find_all(class_=cls)
        for el in elements:
            text = el.get_text(strip=True)
            if text and _looks_like_doctor_name(text) and len(text) < 80:
                if text not in [d["name"] for d in doctors]:
                    doctors.append({"name": text, "specialization": ""})
        if len(doctors) >= 15:
            return doctors

    # Попытка 2: CSS классы (типичные для медицинских сайтов)
    doctor_selectors = [
        {"name": "div", "class_": re.compile(r"doctor|vrach|specialist|team-member|card-doctor", re.I)},
        {"name": "div", "class_": re.compile(r"team-item|staff-item|person", re.I)},
        {"name": "article", "class_": re.compile(r"doctor|vrach|specialist", re.I)},
        {"name": "li", "class_": re.compile(r"doctor|vrach|specialist", re.I)},
    ]

    for selector in doctor_selectors:
        cards = soup.find_all(**selector)
        for card in cards:
            name = _extract_name_from_card(card)
            if name and len(name) > 3 and name not in [d["name"] for d in doctors]:
                spec = _extract_spec_from_card(card)
                doctors.append({"name": name, "specialization": spec})
        if len(doctors) >= 15:
            break

    # Попытка 3: Заголовки h1-h4
    if not doctors:
        for tag in soup.find_all(["h1", "h2", "h3", "h4"]):
            text = tag.get_text(strip=True)
            if _looks_like_doctor_name(text) and text not in [d["name"] for d in doctors]:
                spec = ""
                sibling = tag.find_next_sibling()
                if sibling:
                    spec_text = sibling.get_text(strip=True)[:100]
                    if len(spec_text) < 100:
                        spec = spec_text
                doctors.append({"name": text, "specialization": spec})
            if len(doctors) >= 15:
                break

    return doctors[:15]


def _extract_name_from_card(card) -> str:
    """Извлечь имя из карточки врача."""
    # Ищем заголовок внутри карточки
    for tag in card.find_all(["h2", "h3", "h4", "h5", "strong", "b"]):
        text = tag.get_text(strip=True)
        if text and len(text) > 3 and len(text) < 100:
            return text

    # Ищем по классу name
    name_el = card.find(class_=re.compile(r"name|title|fio", re.I))
    if name_el:
        return name_el.get_text(strip=True)

    return ""


def _extract_spec_from_card(card) -> str:
    """Извлечь специализацию из карточки врача."""
    spec_el = card.find(class_=re.compile(r"spec|position|job|desc|post", re.I))
    if spec_el:
        return spec_el.get_text(strip=True)[:150]
    return ""


def _looks_like_doctor_name(text: str) -> bool:
    """Эвристика: похож ли текст на имя врача?"""
    if not text or len(text) < 5 or len(text) > 80:
        return False
    # Паттерны: "Иванов И.И.", "Иван Иванов", "Иванов Иван Иванович"
    words = text.split()
    if len(words) < 2 or len(words) > 5:
        return False
    # Должны быть кириллица или латиница
    has_alpha = any(c.isalpha() for c in text)
    # Не должно быть цифр, спецсимволов
    has_bad = any(c in text for c in "0123456789©®™")
    return has_alpha and not has_bad


def _extract_socials(soup: BeautifulSoup) -> dict:
    """Извлечь соцсети из HTML."""
    socials = {}
    html_text = str(soup)

    for platform, pattern in SOCIAL_PATTERNS.items():
        matches = re.findall(pattern, html_text, re.IGNORECASE)
        if matches:
            # Берём первый непустой
            handle = matches[0]
            if handle and handle not in ("share", "post", "sharer"):
                socials[platform] = handle

    return socials


def _extract_services(soup: BeautifulSoup) -> list[str]:
    """Извлечь услуги клиники."""
    services = []

    # По CSS классам
    service_selectors = [
        {"name": "div", "class_": re.compile(r"service|uslug", re.I)},
        {"name": "li", "class_": re.compile(r"service|uslug", re.I)},
        {"name": "a", "class_": re.compile(r"service|uslug", re.I)},
    ]

    for selector in service_selectors:
        items = soup.find_all(**selector)
        for item in items:
            text = item.get_text(strip=True)
            if text and len(text) > 3 and len(text) < 100:
                # Очистить от вложенных элементов
                clean = " ".join(text.split())[:100]
                if clean not in services:
                    services.append(clean)
        if len(services) >= 10:
            break

    return services[:10]


def _detect_cms(soup: BeautifulSoup) -> str:
    """Определить CMS/платформу сайта."""
    # meta generator
    generator = soup.find("meta", attrs={"name": "generator"})
    if generator and generator.get("content"):
        content = generator["content"].lower()
        if "wordpress" in content:
            return "WordPress"
        if "tilda" in content:
            return "Tilda"
        if "bitrix" in content or "1c-bitrix" in content:
            return "Bitrix"
        if "joomla" in content:
            return "Joomla"
        if "drupal" in content:
            return "Drupal"
        if "modx" in content:
            return "MODX"
        return generator["content"][:50]

    # Tilda: ищем tilda.cc или tildacdn
    if soup.find("script", src=re.compile(r"tilda", re.I)):
        return "Tilda"
    # Проверка body class
    body = soup.find("body")
    if body and body.get("class"):
        classes = " ".join(body.get("class", []))
        if "tilda" in classes.lower():
            return "Tilda"

    return ""


def _extract_phone(soup: BeautifulSoup) -> str:
    """Извлечь телефон."""
    for link in soup.find_all("a", href=re.compile(r"tel:", re.I)):
        phone = link.get("href", "").replace("tel:", "").strip()
        if phone:
            return phone

    # По тексту
    phone_match = re.search(
        r"(?:\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}",
        soup.get_text()
    )
    if phone_match:
        return phone_match.group()

    return ""


async def scrape_clinic_website(url: str) -> str:
    """Скрейпить сайт клиники — извлечь врачей, соцсети, услуги.

    Args:
        url: URL сайта клиники (например https://arclinic.ru)

    Returns:
        JSON строка с данными: doctors, socials, services, cms, phone
    """
    # Нормализовать URL
    if not url.startswith("http"):
        url = "https://" + url
    base_url = url.rstrip("/")

    logger.info("scrape_clinic_website: starting for %s", base_url)

    result = {
        "url": base_url,
        "doctors": [],
        "socials": {},
        "services": [],
        "cms": "",
        "phone": "",
        "pages_scraped": 0,
    }

    async with httpx.AsyncClient(headers=_HEADERS, timeout=_TIMEOUT) as client:
        # 1. Скрейпить главную
        homepage_html = await _fetch_page(base_url, client)
        if not homepage_html:
            logger.warning("scrape: homepage failed for %s", base_url)
            return json.dumps(result, ensure_ascii=False)

        result["pages_scraped"] = 1
        soup = BeautifulSoup(homepage_html, "lxml")

        # Извлечь соцсети с главной
        result["socials"] = _extract_socials(soup)

        # Извлечь услуги с главной
        result["services"] = _extract_services(soup)

        # Определить CMS
        result["cms"] = _detect_cms(soup)

        # Извлечь телефон
        result["phone"] = _extract_phone(soup)

        # 2. Найти страницы врачей
        doctor_pages = _find_doctor_pages(base_url, soup)
        logger.info("scrape: found %d doctor pages: %s", len(doctor_pages), doctor_pages)

        # 3. Скрейпить страницы врачей
        for doctor_url in doctor_pages[:3]:  # Максимум 3 страницы
            doctor_html = await _fetch_page(doctor_url, client)
            if doctor_html:
                result["pages_scraped"] += 1
                doctor_soup = BeautifulSoup(doctor_html, "lxml")
                doctors = _extract_doctors(doctor_soup)
                for doc in doctors:
                    if doc["name"] not in [d["name"] for d in result["doctors"]]:
                        result["doctors"].append(doc)

                # Также проверить соцсети на странице врачей
                page_socials = _extract_socials(doctor_soup)
                for k, v in page_socials.items():
                    if k not in result["socials"]:
                        result["socials"][k] = v

            if len(result["doctors"]) >= 15:
                break

        # Если врачи не найдены на отдельных страницах — попробовать на главной
        if not result["doctors"]:
            doctors = _extract_doctors(soup)
            result["doctors"] = doctors

    logger.info(
        "scrape: completed for %s — doctors=%d, socials=%d, services=%d, cms=%s",
        base_url, len(result["doctors"]), len(result["socials"]),
        len(result["services"]), result["cms"],
    )

    return json.dumps(result, ensure_ascii=False)


async def handle_scrape_clinic_website(url: str, **kwargs) -> str:
    """Handler for scrape_clinic_website tool."""
    if isinstance(url, dict):
        url = url.get("url", "")
    return await scrape_clinic_website(url)


# Регистрация в registry
register(
    name="scrape_clinic_website",
    schema={
        "type": "function",
        "function": {
            "name": "scrape_clinic_website",
            "description": "Скрейпит сайт клиники — находит врачей (имена, специализации), "
                           "соцсети (VK, Telegram, Instagram, YouTube), услуги, телефон, CMS. "
                           "ВЫЗЫВАЙ когда клиент прислал URL сайта — для получения данных с САЙТА.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL сайта клиники (например https://arclinic.ru)",
                    },
                },
                "required": ["url"],
            },
        },
    },
    handler=handle_scrape_clinic_website,
    check_fn=lambda: True,
    is_async=True,
)
