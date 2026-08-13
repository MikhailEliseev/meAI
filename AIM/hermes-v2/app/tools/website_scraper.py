"""scrape_clinic_website — скрейпит реальный сайт клиники.

Извлекает: врачей, соцсети, услуги, контакты, CMS.
Использует httpx + BeautifulSoup (не Perplexity!).

Подход:
1. Проверка SSRF (блокировка internal IPs)
2. Скрейпить главную страницу
3. Найти ссылки на /vrachi, /doctors, /team, /specialists
4. Скрейпить страницы врачей
5. Извлечь имена врачей, соцсети, услуги
"""
import ipaddress
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
_MAX_RESPONSE_SIZE = 5_000_000  # 5MB лимит (DoS защита)
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}

# Паттерны городов/мусора в специализации врачей (Phase 14 Task 3)
_CITY_JUNK_RE = re.compile(
    r'\b(?:Санкт-Петербург|Москва|Россия|Екатеринбург|Новосибирск|'
    r'Казань|Нижний\s+Новгород|Самара|Ростов-на-Дону|Уфа|'
    r'Краснодар|Челябинск|Воронеж|Пермь|г\.?)\b',
    re.IGNORECASE,
)


def _is_safe_url(url: str) -> bool:
    """Проверить что URL не указывает на internal ресурсы (SSRF защита).

    Блокирует:
    - Private IPs (10.x, 172.16-31.x, 192.168.x)
    - Loopback (127.x, ::1)
    - Link-local (169.254.x — AWS metadata)
    - localhost, 0.0.0.0
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False
        # Попытаться распарсить как IP
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                logger.warning("SSRF blocked: %s (internal IP)", url)
                return False
        except ValueError:
            pass  # Не IP — домен, OK
        # Блокировать localhost variants
        if hostname.lower() in ("localhost", "0.0.0.0", "::1"):
            logger.warning("SSRF blocked: %s (localhost)", url)
            return False
        return True
    except Exception:
        return False

# Паттерны для поиска страниц врачей (Bug 2 fix: расширены)
DOCTOR_URL_PATTERNS = [
    r"/vrachi", r"/doctors", r"/team", r"/specialists", r"/staff",
    r"/doctors-page", r"/our-doctors", r"/about/doctors",
    r"/klinika/vrachi", r"/klinika/doctors",
    r"/o-nas/vrachi", r"/o-klinike/vrachi",
    # Bug 2 fix: дополнительные паттерны для русских клиник
    r"/specialist", r"/spetsialisty", r"/sotrudniki", r"/personal",
    r"/vrach", r"/doctor", r"/med-personal", r"/medpersonal",
    r"/our-team", r"/our-staff", r"/o-kompanii/vrachi",
    r"/klinika/komanda", r"/komanda", r"/about/team",
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
    """Скачать HTML страницу (с SSRF проверкой и размер-лимитом).
    Fallback: если прямой запрос не удался — Jina Reader (r.jina.ai)."""
    if not _is_safe_url(url):
        logger.warning("scrape: SSRF blocked URL: %s", url)
        return None

    # 1. Прямой запрос (оригинальная логика)
    try:
        resp = await client.get(url, follow_redirects=True)
        if resp.status_code == 200:
            if len(resp.content) > _MAX_RESPONSE_SIZE:
                logger.warning("scrape: %s too large (%d bytes), truncating", url, len(resp.content))
                return resp.text[:_MAX_RESPONSE_SIZE]
            if resp.encoding is None or resp.encoding == "ascii":
                resp.encoding = resp.charset_encoding or "utf-8"
            return resp.text
        logger.warning("scrape: %s returned %d", url, resp.status_code)
    except Exception as e:
        logger.warning("scrape: %s failed: %s", url, str(e)[:100])

    # 2. FALLBACK: Jina Reader (бесплатно, r.jina.ai)
    html = await _fetch_page_jina(url)
    if html:
        logger.info("scrape: %s — got content via Jina Reader fallback", url)
        return html
    return None


async def _fetch_page_jina(url: str) -> str | None:
    """Fallback: прочитать страницу через Jina Reader (r.jina.ai).
    Возвращает Markdown → конвертируем в HTML для BS4.
    Бесплатно, без API-ключа, обходит антибот-защиту."""
    jina_url = f"https://r.jina.ai/{url}"
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(20.0, connect=10.0)) as jc:
            jresp = await jc.get(
                jina_url,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "text/plain",
                },
            )
            if jresp.status_code != 200:
                return None
            markdown = jresp.text[:_MAX_RESPONSE_SIZE]
            if not markdown.strip() or len(markdown) < 50:
                return None
            # Конвертировать Markdown → минимальный HTML для BS4
            # [text](url) → <a href="url">text</a>
            html_body = re.sub(
                r"\[([^\]]+)\]\(([^)]+)\)",
                r'<a href="\2">\1</a>',
                markdown,
            )
            return f"<html><body>{html_body}</body></html>"
    except Exception as e:
        logger.warning("scrape: Jina fallback failed for %s: %s", url, str(e)[:80])
    return None


def _find_doctor_pages(base_url: str, soup: BeautifulSoup) -> list[str]:
    """Найти ссылки на страницы врачей (Bug 2 fix: расширен поиск + пагинация)."""
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

    # Bug 2 fix: ищем пагинацию (?PAGEN_1=2, ?page=2) на главной и доп. страницах
    pagination_patterns = [r"pagen", r"page=", r"/page/", r"?p=", r"_page="]
    for link in soup.find_all("a", href=True):
        href = link["href"].lower()
        # Если ссылка содержит паттерн пагинации и ведёт на ту же секцию
        if any(p in href for p in pagination_patterns):
            full_url = urljoin(base_url, link["href"])
            if urlparse(full_url).netloc == urlparse(base_url).netloc:
                # Добавляем пагинированные страницы врачей (содержат /vrachi или /doctors)
                if any(pat in href for pat in DOCTOR_URL_PATTERNS):
                    doctor_urls.add(full_url)

    return list(doctor_urls)[:10]  # Bug 2 fix: было 5, теперь 10


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
                    # Убрать название клиники, город, мусор
                    spec_part = re.sub(
                        r'\b(?:врач|ARclinic|клиник[аи]?|центр)\b',
                        '', spec_part, flags=re.I
                    ).strip(" ,.-")
                    # Phase 14: убрать города и гео-мусор
                    spec_part = _CITY_JUNK_RE.sub('', spec_part).strip(" ,.-")
                    # Если осталась пустота — специализация не найдена
                    if spec_part and len(spec_part) >= 3 and not spec_part.lower().startswith("спб"):
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

    return doctors[:25]  # Bug 2 fix: было 15, теперь 25


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


# Фразы, которые НЕ являются именами врачей (футер/меню/legal сайта).
# Скрапер ошибочно тащил «Политика конфиденциальности» и т.п. как врачей.
_NON_DOCTOR_RE = re.compile(
    r"политик[ау]\s+(конфиденц|обработк|использован)|"
    r"обработк[ау]\s+персональн|персональных\s+данных|"
    r"пользовательск\w*\s+соглашен|соглашен\w*\s+на\s+обработк|"
    r"договор\s+оферты|оферт[аы]|"
    r"карта\s+сайта|обратн\w*\s+связь|связать\w*\s+с\s+нам|"
    r"записат\w*\s+на\s+при[её]м|запись\s+на\s+при[её]м|оставить\s+заявк|"
    r"заказать\s+звонок|перезвон\w*|"
    r"личный\s+кабинет|корзин[аы]|избранн\w*|"
    r"все\s+права\s+защищен|все\s+права|copyright|©|"
    r"разработан\w*|сделано\s+в|сайт\s+создал|"
    r"^\s*(услуг[аиы]|цен[аыны]|прайс|стоимост\w*|контакт\w*|отзыв\w*|"
    r"о\s+нас|о\s+компани\w*|главна\w*|меню|наверх|далее|подробнее|читать)\s*$|"
    r"реквизит\w*|согласи\w+\s+на|"
    r"график\s+работ|режим\s+работ|время\s+работ",
    re.IGNORECASE,
)


# Брендовые слова — «Implant Dentistry», «Smile Clinic», «Стоматология Юг» — НЕ врачи.
# Английские — с \b (не склоняются). Русские бренд-стемы — с [а-яё]* (склонения:
# «стоматология», «клиники»). Короткие «зуб»/«мед» НЕ включаем — коллидируют с
# фамилиями (Зубов, Медведев).
_BRAND_KEYWORDS_RE = re.compile(
    r"\b(dentistry|dental|clinic|clinik|implant|smile|teeth|tooth|"
    r"medical|medicine|center|centre|hospital|care|wellness)|"
    r"\b(стоматолог|дентал|клиник|имплант|улыбк|здоров|медиц|центральн)[а-яё]*",
    re.IGNORECASE,
)


def _looks_like_doctor_name(text: str) -> bool:
    """Эвристика: похож ли текст на имя врача?"""
    if not text or len(text) < 5 or len(text) > 80:
        return False
    # Запрет футер/меню/legal-фраз («Политика конфиденциальности» и т.п.)
    if _NON_DOCTOR_RE.search(text):
        return False
    # Запрет брендовых названий («Implant Dentistry», «Smile Clinic»)
    if _BRAND_KEYWORDS_RE.search(text):
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


def _find_services_page(base_url: str, soup: BeautifulSoup) -> str | None:
    """Fix 7: найти отдельную страницу услуг (приоритет над homepage).
    
    Возвращает URL страницы услуг или None если не найдена.
    """
    # Паттерны URL страниц услуг
    service_patterns = [
        r"/services", r"/uslugi", r"/price", r"/prices", r"/pricelist",
        r"/napravleniya", r"/lechenie", r"/procedury", r"/med-uslugi",
        r"/kosmetologiya", r"/service", r"/tsenyi"
    ]
    
    for link in soup.find_all("a", href=True):
        href = link["href"].lower()
        for pattern in service_patterns:
            if pattern in href:
                full_url = urljoin(base_url, link["href"])
                # Проверить что это тот же домен
                if urlparse(full_url).netloc == urlparse(base_url).netloc:
                    return full_url
    return None


def _extract_services(soup: BeautifulSoup, require_medical_terms: bool = True) -> list[str]:
    """Извлечь услуги клиники (Fix 7: опциональный whitelist для /services/ страниц).
    
    Args:
        soup: BeautifulSoup объект страницы
        require_medical_terms: если False, не требуем медицинские термины 
            (используется для страниц /services/ где весь контекст медицинский)
    """
    services = []

    # Bug 4 fix: блэклист навигационных/промо элементов (не услуги!)
    _SERVICE_BLOCKLIST = {
        # Навигация
        "все услуги", "выберите направление", "выберите услугу", "показать все",
        "смотреть все", "подробнее", "узнать больше", "читать далее",
        "записаться", "записаться на прием", "записаться онлайн",
        "заказать звонок", "обратный звонок", "оставить заявку",
        # Промо/события
        "день рождения", "акция", "скидка", "спецпредложение", "новости",
        "блог", "статьи", "отзывы", "контакты", "о клинике", "о нас",
        # Generic
        "главная", "меню", "поиск", "404",
    }

    # Fix 6: whitelist медицинских терминов — принимаем ТОЛЬКО услуги с этими словами
    _MEDICAL_TERMS = {
        # Специализации
        "косметолог", "дерматолог", "хирург", "пластический", "эстетическ",
        "стоматолог", "ортодонт", "имплантолог", "терапевт", "педиатр",
        "гинеколог", "уролог", "кардиолог", "невролог", "эндокринолог",
        "офтальмолог", "лор", "отоларинголог", "травматолог", "ортопед",
        # Процедуры/услуги
        "лечение", "диагностика", "операция", "удаление", "коррекция",
        "отбеливание", "чистка", "пилинг", "мезотерапия", "ботокс",
        "филлер", "биоревитализ", "лазер", "увеличение", "подтяжка",
        "липосакция", "ринопластика", "блефаропластика", "маммопластика",
        "абдоминопластика", "лифтинг", "контур", "инъекция",
        "массаж", "физиотерапия", "узи", "мрт", "кт", "рентген",
        "анализ", "обследование", "консультация врача", "прием врача",
        # Общие
        "терапия", "профилактика", "реабилитация", "восстановление",
    }

    def _is_blocked(text: str) -> bool:
        """Проверить, является ли текст навигационным мусором."""
        text_lower = text.lower().strip()
        if text_lower in _SERVICE_BLOCKLIST:
            return True
        for phrase in ("записаться", "заказать", "обратный звонок", "оставить заявку",
                        "показать все", "смотреть все", "подробнее"):
            if phrase in text_lower:
                return True
        return False

    def _has_medical_term(text: str) -> bool:
        """Fix 6: проверить, содержит ли текст медицинский термин."""
        text_lower = text.lower()
        return any(term in text_lower for term in _MEDICAL_TERMS)

    # По CSS классам
    service_selectors = [
        {"name": "div", "class_": re.compile(r"service|uslug", re.I)},
        {"name": "li", "class_": re.compile(r"service|uslug", re.I)},
        {"name": "a", "class_": re.compile(r"service|uslug", re.I)},
    ]

    for selector in service_selectors:
        items = soup.find_all(**selector)
        for item in items:
            # Bug 4 fix: пропустить элементы внутри <nav>
            if item.find_parent("nav"):
                continue
            text = item.get_text(strip=True)
            if text and len(text) > 3 and len(text) < 100:
                # Bug 4 fix: проверить блэклист
                if _is_blocked(text):
                    continue
                # Fix 7: на странице /services/ не требуем медицинские термины
                if require_medical_terms and not _has_medical_term(text):
                    continue
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


# ── Fix 1: ИНН из подвала/копирайта сайта ──────────────────────────────────
_INN_RE = re.compile(r'\b(\d{10}|\d{12})\b')
_OGRN_RE = re.compile(r'[Оо]ГРН(?:ИП)?\s*(?::|-)?\s*(\d{13,15})', re.U)


def _extract_inn(soup: BeautifulSoup) -> str:
    """Извлечь ИНН из подвала сайта.

    Российские сайты обязаны публиковать ИНН в футере.
    Ищем: текст рядом с 'ИНН', потом regex по всему тексту.
    """
    text = soup.get_text(separator=" ", strip=True)

    # 1. Контекстный поиск: "ИНН: 7701234567" или "ИНН 7701234567"
    inn_context = re.search(r'[Ии]НН\s*(?::|-)?\s*(\d{10,12})', text)
    if inn_context:
        inn = inn_context.group(1)
        if len(inn) in (10, 12):
            return inn

    # 2. Regex по всему тексту — ищем 10-значные числа рядом со словами юр. лица
    footer = soup.find("footer")
    if footer:
        footer_text = footer.get_text(separator=" ", strip=True)
        inn_match = _INN_RE.search(footer_text)
        if inn_match:
            return inn_match.group(1)

    # 3. По всему тексту (последний шанс — много ложных срабатываний)
    # Ищем только если рядом есть слова ООО/АО/ИП/Компания
    legal_context = re.search(
        r'(?:ООО|АО|ОАО|ИП|Компания|Общество)[^<]{0,200}?(\d{10})\b',
        text
    )
    if legal_context:
        return legal_context.group(1)

    return ""


def _extract_address(soup: BeautifulSoup) -> str:
    """Извлечь адрес клиники из сайта.

    Ищем в footer, контактах, блоке address.
    """
    # 1. <address> тег
    addr_tag = soup.find("address")
    if addr_tag:
        addr_text = addr_tag.get_text(separator=" ", strip=True)
        if len(addr_text) > 10:
            return addr_text[:300]

    # 2. Footer — обычно там адрес
    footer = soup.find("footer")
    if footer:
        footer_text = footer.get_text(separator=" ", strip=True)
        # Ищем паттерн адреса: "г. Москва" или "ул." или индекс
        addr_match = re.search(
            r'((?:г\.?\s*|гор\.?\s*)?[А-ЯЁ][а-яё]+(?:[-\s][А-ЯЁа-яё]+)*[,\s]+'
            r'(?:ул\.?|пр\.?|пер\.?|наб\.?|ш\.?|б-р\.?)\s*'
            r'[А-ЯЁа-яё]+\s*\d*[а-я]?[,\s]*\d+[а-я]?)',
            footer_text
        )
        if addr_match:
            return addr_match.group(1)[:300]

    # 3. По тексту — индекс + город
    postal_match = re.search(
        r'(\d{6}[,\s]+(?:г\.?\s*)?[А-ЯЁ][а-яё]+[,\s]+(?:ул\.?|пр\.?)\s*[А-ЯЁа-яё]+[^<]{0,50})',
        soup.get_text(separator=" ", strip=True)
    )
    if postal_match:
        return postal_match.group(1)[:300]

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

        # Fix 7: Найти отдельную страницу услуг (приоритет над homepage)
        services_page_url = _find_services_page(base_url, soup)
        if services_page_url:
            logger.info("scrape: found services page: %s", services_page_url)
            services_html = await _fetch_page(services_page_url, client)
            if services_html:
                result["pages_scraped"] += 1
                services_soup = BeautifulSoup(services_html, "lxml")
                # На странице услуг НЕ требуем медицинские термины — весь контекст медицинский
                result["services"] = _extract_services(services_soup, require_medical_terms=False)
            else:
                # Fallback: если страница услуг недоступна, берём с homepage
                result["services"] = _extract_services(soup, require_medical_terms=True)
        else:
            # Нет отдельной страницы услуг — берём с homepage (с whitelist)
            result["services"] = _extract_services(soup, require_medical_terms=True)

        # Определить CMS
        result["cms"] = _detect_cms(soup)

        # Извлечь телефон
        result["phone"] = _extract_phone(soup)

        # Fix 1: Извлечь ИНН из подвала/копирайта сайта
        inn = _extract_inn(soup)
        if inn:
            result["inn"] = inn
            logger.info("scrape: INN found from website: %s", inn)

        # Fix 3: Извлечь адрес из footer/address тегов
        address = _extract_address(soup)
        if address:
            result["address"] = address
            logger.info("scrape: address found: %s", address[:60])

        # 2. Найти страницы врачей
        doctor_pages = _find_doctor_pages(base_url, soup)
        logger.info("scrape: found %d doctor pages: %s", len(doctor_pages), doctor_pages)

        # 3. Скрейпить страницы врачей (Bug 2 fix: было 3 страницы, теперь 8)
        for doctor_url in doctor_pages[:8]:  # Максимум 8 страниц
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

                # Bug 2 fix: ищем пагинацию на странице врачей и переходим на след. страницу
                for link in doctor_soup.find_all("a", href=True):
                    href = link["href"].lower()
                    if any(p in href for p in ["pagen", "page=", "/page/"]):
                        next_url = urljoin(doctor_url, link["href"])
                        if urlparse(next_url).netloc == urlparse(base_url).netloc:
                            if next_url not in doctor_pages and len(doctor_pages) < 12:
                                doctor_pages.append(next_url)

            if len(result["doctors"]) >= 20:  # Bug 2 fix: было 15, теперь 20
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
