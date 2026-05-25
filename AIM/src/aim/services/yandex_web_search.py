"""Web Search — website discovery for competitors via multiple engines.

Finds competitor websites by searching for the company name + city.
Used as a fallback when Yandex Maps / OSM don't return a website URL.

Search cascade:
  1. DuckDuckGo (Playwright) — less bot-aggressive, good first stop
  2. Yandex (Playwright) — best for Russian results but bot-protected
  3. Google (Playwright) — wider coverage

Filters out aggregator/catalog domains (2gis.ru, zoon.ru, etc.) to return
only the competitor's own domain.
"""

import asyncio
import logging
import re
from typing import Optional
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

# Russian → Latin transliteration for domain guessing
_TRANSLIT_MAP = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    ' ': '-', '_': '-', '.': '', ',': '', '"': '', "'": '', '«': '', '»': '',
    '(': '', ')': '', '–': '-', '—': '-', '/': '-', '\\': '-', '|': '-',
}
# Russian clinics use .ru, .рф, sometimes .com. Other gTLDs (.clinic,
# .medical, .doctor) aren't adopted in the Russian market — they just
# cause DNS NXDOMAIN/timeout noise and slow down discovery.
_DOMAIN_TLDS = ['.ru', '.рф', '.com']
# Common words to strip for shorter domain guesses
_STRIP_WORDS = {
    # Legal forms
    'ооо', 'ooo', 'ао', 'ao', 'зао', 'zao', 'ип', 'ip',
    'общество', 'obschestvo', 'obshestvo',
    'ограниченной', 'ogranichennoy', 'ограниченная', 'ogranichennaya',
    'ответственностью', 'otvetstvennostyu', 'otvetstvennostiu',
    'учреждение', 'uchrezhdenie', 'бюджетное', 'budzhetnoe', 'byudzhetnoe',
    'автономное', 'avtonomnoe', 'некоммерческая', 'nekommercheskaya',
    'организация', 'organizatsiya', 'organizatsia', 'organizaciya',
    # Generic medical nouns
    'клиника', 'clinic', 'мед', 'med', 'центр', 'center',
    'стоматология', 'stomatologiya', 'косметология', 'kosmetologiya',
    'хирургия', 'khirurgiya', 'терапия', 'terapiya', 'ортопедия', 'ortopediya',
    'неврология', 'nevrologiya', 'диагностика', 'diagnostika',
    'педиатрия', 'pediatriya', 'офтальмология', 'oftalmologiya',
    'урология', 'urologiya', 'гинекология', 'ginekologiya',
    'дерматология', 'dermatologiya', 'кардиология', 'kardiologiya',
    'реабилитация', 'reabilitatsiya',
    # Medical adjectives (descriptive, not brand-identifying)
    'наркологическая', 'наркологический', 'narkologicheskaya', 'narkologicheskiy',
    'ветеринарная', 'ветеринарный', 'veterinarnaya', 'veterinarniy',
    'медицинский', 'медицинская', 'meditsinskiy', 'meditsinskaya',
    'стоматологическая', 'стоматологический', 'stomatologicheskaya', 'stomatologicheskiy',
    'косметологический', 'косметологическая', 'kosmetologicheskiy', 'kosmetologicheskaya',
    'неврологический', 'неврологическая', 'nevrologicheskiy', 'nevrologicheskaya',
    'хирургический', 'хирургическая', 'khirurgicheskiy', 'khirurgicheskaya',
    'терапевтический', 'терапевтическая', 'terapevticheskiy', 'terapevticheskaya',
    'ортопедический', 'ортопедическая', 'ortopedicheskiy', 'ortopedicheskaya',
    'диагностический', 'диагностическая', 'diagnosticheskiy', 'diagnosticheskaya',
    'педиатрический', 'педиатрическая', 'pediatricheskiy', 'pediatricheskaya',
    'офтальмологический', 'офтальмологическая', 'oftalmologicheskiy', 'oftalmologicheskaya',
    'урологический', 'урологическая', 'urologicheskiy', 'urologicheskaya',
    'гинекологический', 'гинекологическая', 'ginekologicheskiy', 'ginekologicheskaya',
    'дерматологический', 'дерматологическая', 'dermatologicheskiy', 'dermatologicheskaya',
    'кардиологический', 'кардиологическая', 'kardiologicheskiy', 'kardiologicheskaya',
    'реабилитационный', 'реабилитационная', 'reabilitatsionniy', 'reabilitatsionnaya',
    # Common descriptive words often used in clinic names
    'профессорская', 'профессорский', 'professorskaya', 'professorskiy',
    'семейная', 'семейный', 'semeynaya', 'semeyniy',
    'первая', 'первый', 'pervaya', 'perviy',
    # Doctor/hospital generic
    'доктор', 'доктора', 'doktor', 'doktora',
    'госпиталь', 'hospital',
    'многопрофильный', 'многопрофильная', 'mnogoprofilniy', 'mnogoprofilnaya',
}
# Russian words often translated (not transliterated) in domain names
_TRANSLATE_WORDS = {
    'плюс': 'plus', 'минус': 'minus',
    'мир': 'mir', 'world': 'world',
    'дети': 'deti', 'kids': 'kids',
    'семья': 'semya', 'family': 'family',
    'здоровье': 'zdorovie', 'health': 'health',
    'красота': 'krasota', 'beauty': 'beauty',
    'город': 'gorod', 'city': 'city',
    'дом': 'dom', 'house': 'house',
    'евро': 'euro',
    'лайт': 'lite', 'light': 'light',
    'про': 'pro',
    'мед': 'med',
    'доктор': 'doctor',
    'дентал': 'dental',
}
# Extra TLD variants for brandable 2-word combos.
# Stick to TLDs Russian clinics actually use — niche gTLDs just create DNS noise.
_EXTRA_TLDS = ['.ru', '.com']

# Parked domain / domain-for-sale patterns (checked in <title> and first 2KB of HTML)
_PARKED_TITLE_PATTERNS = [
    # Russian
    'домен продается', 'домен продаётся', 'купить домен', 'куплю домен',
    'магазин доменов', 'продажа доменов', 'аукцион доменов',
    'свободен', 'домен зарегистрирован', 'домен припаркован',
    # English
    'domain for sale', 'buy this domain', 'domain is for sale',
    'domain parking', 'parked domain', 'this domain is parked',
    'domain name for sale', 'purchase this domain',
]
# Domain marketplaces — if page links predominantly to these, it's parked
_PARKED_MARKETPLACE_DOMAINS = {
    'nic.ru', 'rucenter.com', 'rucenter.ru',
    'sedo.com', 'afternic.com', 'godaddy.com', 'namecheap.com',
    'hugedomains.com', 'buydomains.com', 'domainmarket.com',
    'flippa.com', 'dan.com', 'uniregistry.com',
}

# Domains to skip — aggregators, catalogs, maps
_SKIP_DOMAINS = {
    # Maps & directories
    "2gis.ru", "2gis.com",
    "yandex.ru", "yandex.com", "ya.ru",
    "google.com", "maps.google.com",
    # Medical aggregators
    "zoon.ru",
    "prodoctorov.ru",
    "napopravku.ru",
    "doctu.ru",
    "medvisor.ru",
    "medfirms.ru",
    "medbooking.com",
    "topmedclinic.com",
    "krasotaimedicina.ru",
    "spravka.ru",
    "spravochdik.ru",
    "medaboutme.ru",
    "docdoc.ru",
    "meds.ru",
    "medsovet.ru",
    "clinics.ru",
    "medihost.ru",
    # Legal/company registries (ЕГРЮЛ aggregators)
    "dadata.ru",
    "rusprofile.ru",
    "spark-interfax.ru",
    "list-org.com",
    "taxslov.ru",
    "sbis.ru",
    "kontur.ru",
    "catalog.ru",
    "companies.rbc.ru",
    "checko.ru",
    "audit-it.ru",
    "tbank.ru",
    "tochka.com",
    "zachestnyibiznes.ru",
    "ruscompany.ru",
    "egrul.nalog.ru",
    "nalog.ru",
    "saby.ru",
    "synapsenet.ru",
    "orgpage.ru",
    "rusregister.ru",
    "rusprofile.ru",
    "egrul.com",
    "find-org.com",
    "biscont.ru",
    "rusbonds.ru",
    "ruscable.ru",
    "companies-house.ru",
    # General knowledge / reference
    "wikipedia.org", "ru.wikipedia.org",
    "wikidata.org",
    # Social media
    "facebook.com", "instagram.com", "vk.com", "vk.ru",
    "youtube.com", "t.me", "telegram.me",
    "tiktok.com", "ok.ru", "dzen.ru",
    "threads.com", "twitter.com", "x.com",
    "linkedin.com", "pinterest.com",
    "reddit.com", "snapchat.com",
    # Review platforms
    "irecommend.ru", "otzovik.com", "yelp.com",
    "zoon.ru", "flamp.ru",
    "otzyvy.ru", "review.ru",
    # Classifieds / marketplaces
    "avito.ru", "youla.ru", "cian.ru",
    # News / media
    "rbc.ru", "kommersant.ru", "vedomosti.ru", "forbes.ru",
    "tass.ru", "ria.ru", "interfax.ru",
    # Job sites
    "hh.ru", "superjob.ru",
    # Generic
    "unsplash.com", "shutterstock.com", "istockphoto.com",
    "dreamstime.com", "freepik.com",
    # Beauty/directory sites (not clinic websites)
    "barber.su", "prozdor.ru",
    "beautybar.ru", "beautynet.ru", "lookatme.ru",
    "cosmetology.pro", "estetica.ru",
    # Directories / справочники
    "spr.ru", "vsedetali.ru", "sravni.ru",
    "expocalendar.ru", "infodoctor.ru", "reputation.ru",
    "russianhospitals.ru",
    # LemaProf — косметический бренд, не клиника
    "lemanaprof.ru",
    # Garbage / not medical
    "m-dvor.ru",
    # Not clinics (platforms, directories, SaaS)
    "kiberis.ru",  # AI medical reference, not a clinic
    "tenchat.ru",  # business social network
    "rostox-n.com",  # news/conference site, not a clinic
}

# TLDs that are definitely not Russian clinics
_FOREIGN_TLDS = {".ua", ".by", ".kz", ".kg", ".uz", ".tj", ".tm", ".az", ".am", ".ge", ".md"}

_STEALTH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# JS injected before page load to hide automation signals
_STEALTH_INIT_JS = """
// Overwrite navigator.webdriver flag
Object.defineProperty(navigator, 'webdriver', { get: () => false });
// Fake chrome object
window.chrome = { runtime: {} };
// Fake plugins
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
// Fake languages
Object.defineProperty(navigator, 'languages', { get: () => ['ru-RU', 'ru', 'en-US', 'en'] });
"""

_EXTRACT_JS = """
() => {
  const candidates = [];
  const allLinks = document.querySelectorAll('a[href]');
  for (const link of allLinks) {
    const href = link.getAttribute('href');
    if (!href) continue;

    // Skip Yandex internal links and known aggregators
    if (href.startsWith('/') || href.includes('yandex.') || href.includes('ya.ru')) continue;
    if (href.startsWith('#')) continue;

    // Resolve Yandex redirect URLs (e.g. //yandex.ru/clck/...)
    if (href.startsWith('//') && !href.startsWith('//www.')) {
      try {
        const u = new URL('https:' + href);
        const real = u.searchParams.get('url') || u.searchParams.get('text');
        if (real && real.startsWith('http')) {
          candidates.push(real);
        }
      } catch {}
      continue;
    }

    if (href.startsWith('http')) {
      candidates.push(href);
    }
  }
  return candidates;
}
"""

# Google-specific extraction — simpler, Google SERP is more predictable
_GOOGLE_EXTRACT_JS = """
() => {
  const candidates = [];
  // Google organic results: h3 within a link, or #search .g a[href]
  const resultLinks = document.querySelectorAll('#search a[href], #rso a[href], .g a[href]');
  for (const link of resultLinks) {
    const href = link.getAttribute('href');
    if (!href) continue;
    if (href.startsWith('http') && !href.includes('google.com') && !href.includes('youtube.com')) {
      candidates.push(href);
    }
  }
  // Also check general links
  if (candidates.length === 0) {
    const allLinks = document.querySelectorAll('a[href]');
    for (const link of allLinks) {
      const href = link.getAttribute('href');
      if (!href) continue;
      if (href.startsWith('/') || href.startsWith('#')) continue;
      if (href.includes('google.com') || href.includes('gstatic.com')) continue;
      if (href.startsWith('http')) {
        candidates.push(href);
      }
    }
  }
  return candidates;
}
"""


def transliterate(name: str, translate_words: bool = False) -> str | list[str]:
    """Transliterate Russian text to Latin for domain names.

    If translate_words=True, returns a list: [transliterated, translated_version, ...]
    so common words like "плюс" → both "plyus" and "plus" are tried.
    """
    words = name.lower().split()
    # Transliterate each word
    translit_words = []
    for w in words:
        result = []
        for ch in w:
            result.append(_TRANSLIT_MAP.get(ch, ch))
        slug = re.sub(r'-+', '-', ''.join(result))
        slug = re.sub(r'[^a-z0-9-]', '', slug)
        translit_words.append(slug)

    result = '-'.join(translit_words).strip('-') or 'site'

    if not translate_words:
        return result

    # Generate translated variants for each word that has a mapping
    variants = [result]
    for i, w in enumerate(words):
        if w in _TRANSLATE_WORDS:
            # Replace this word with its translation(s)
            translations = _TRANSLATE_WORDS[w].split() if ' ' in _TRANSLATE_WORDS[w] else [_TRANSLATE_WORDS[w]]
            for trans in translations:
                variant_words = translit_words.copy()
                variant_words[i] = trans
                variants.append('-'.join(variant_words).strip('-'))
    return variants


def _is_parked_domain(html: str, domain: str = "") -> bool:
    """Check if an HTML page is a parked domain / domain-for-sale page.

    Looks at <title> and first 2KB for patterns like:
      - "Домен продается", "Domain for sale"
      - Domain marketplace links (nic.ru, sedo.com, etc.)
    """
    if not html:
        return False

    text_lower = html[:3000].lower()

    # Fast check: domain marketplace meta tags
    if 'name="application-name" content="nic.ru"' in text_lower.replace("'", '"'):
        return True
    if 'name="application-name" content="reg.ru"' in text_lower.replace("'", '"'):
        return True

    # Check <title> for parked patterns
    title_match = re.search(r'<title[^>]*>(.*?)</title>', text_lower, re.DOTALL)
    title = title_match.group(1).strip() if title_match else ""

    for pattern in _PARKED_TITLE_PATTERNS:
        if pattern in title:
            return True

    # Check if most external links go to domain marketplaces
    links = re.findall(r'href=["\'](https?://[^"\']+)["\']', text_lower)
    if links and len(links) <= 5:
        marketplace_hits = sum(
            1 for l in links
            if any(md in l for md in _PARKED_MARKETPLACE_DOMAINS)
        )
        if marketplace_hits >= len(links) * 0.4:  # 40%+ links to marketplaces
            return True

    return False


# ── Medical relevance check for domain verification ──────────────────
# Keywords that strongly indicate a medical/dental clinic website
_MEDICAL_KEYWORDS = [
    # Russian dental
    'стоматолог', 'стоматологи', 'дантист', 'имплантаци', 'имплантолог',
    'ортодонт', 'ортопед', 'зуб', 'протезирован', 'отбеливан',
    'кариес', 'пломб', 'винир', 'элайнер',
    # Russian general medical
    'клиник', 'медицин', 'врач', 'доктор', 'пациент',
    'лечени', 'диагност', 'приём', 'прием', 'хирург',
    'косметолог', 'дерматолог', 'гинеколог', 'уролог', 'педиатр',
    'терапевт', 'процедур', 'операци', 'реабилитаци',
    # English dental (for .com sites)
    'dentist', 'dental', 'dentistry', 'implant',
    'orthodont', 'endodont', 'periodont',
    # English medical
    'clinic', 'medical', 'patient', 'doctor', 'surgery',
    'healthcare', 'treatment', 'physician',
    # Contact indicators (most clinic sites have these)
    'записаться', 'консультаци', 'прайс', 'услуги', 'отделение',
    'филиал', 'специалист',
]


def _is_irrelevant_site(html: str, company_name: str = "") -> bool:
    """Check if a website is clearly NOT a medical clinic site.

    Returns True if the site should be REJECTED (irrelevant).
    Looks for:
      - No medical keywords in title/meta/visible text
      - Company name not found on the page
      - Clearly unrelated content (software, e-commerce, equipment store, etc.)
      - E-commerce / online store signals (корзина, каталог товаров, цены)
    """
    if not html:
        return True

    text_lower = html[:50000].lower()

    # Extract title
    title_match = re.search(r'<title[^>]*>(.*?)</title>', text_lower, re.DOTALL)
    title = title_match.group(1).strip() if title_match else ""

    # Extract meta description
    desc_match = re.search(
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
        text_lower,
    )
    meta_desc = desc_match.group(1).strip() if desc_match else ""

    # Visible text only (no HTML tags, CSS, JS)
    _visible_text = re.sub(r"<[^>]+>", " ", text_lower[:10000])
    _visible_search = f"{title} {meta_desc} {_visible_text}"

    # Combined text for company name matching (includes HTML for href/alt)
    search_text = f"{title} {meta_desc} {text_lower[:10000]}"

    # ── E-commerce / equipment store detection ──────────────────────
    _ecommerce_signals = [
        # Russian
        'корзина', 'каталог товаров', 'интернет-магазин',
        'доставка', 'оформление заказа', 'скидка', 'акци',
        'купить', 'в корзину', 'товар', 'цена', 'бесплатная доставка',
        'оптовы', 'розничны', 'прайс-лист на товар',
        # Equipment-specific
        'оборудование', 'расходные материалы', 'инструмент',
        'стоматологическое оборудование', 'медицинское оборудование',
        'стоматологический магазин', 'магазин медицин',
        'dental equipment', 'dental supplies', 'medical equipment',
        'dental shop', 'medical shop',
    ]
    ecom_signals = sum(1 for s in _ecommerce_signals if s in _visible_search)

    # ── Medical keyword check (visible text only) ───────────────────
    medical_hits = sum(1 for kw in _MEDICAL_KEYWORDS if kw in _visible_search)

    # ── Company name match ──────────────────────────────────────────
    name_match = False
    name_match_count = 0
    if company_name:
        name_clean = company_name.lower().strip()
        for ch in '«»"\'()':
            name_clean = name_clean.replace(ch, '')
        name_clean = ' '.join(name_clean.split())

        if len(name_clean) >= 3:
            name_words = [w for w in name_clean.split() if len(w) >= 3]
            for word in name_words:
                translit_word = word.translate(
                    str.maketrans(_TRANSLIT_MAP)
                ) if all(c in _TRANSLIT_MAP for c in word) else word

                if word in search_text or translit_word in search_text:
                    name_match = True
                    name_match_count += 1

    # ── Decision logic ──────────────────────────────────────────────

    # STRONG REJECT: e-commerce / equipment store with ≥2 signals
    if ecom_signals >= 2:
        return True

    # REJECT: e-commerce signals + no medical keywords (equipment store without clinic)
    if ecom_signals >= 1 and medical_hits < 3:
        return True

    # REJECT: no medical keywords — not a medical clinic site.
    # A real clinic's homepage always has at least one medical term
    # (клиника, врач, стоматология, записаться, etc.).
    # Without this, short abbreviations (e.g. "ММК") match industrial sites.
    if medical_hits == 0:
        return True

    # REJECT: only 1 weak medical keyword (e.g. just "клиник" which matches many things)
    _weak_keywords = {'клиник', 'clinic', 'медицин', 'medical', 'врач', 'doctor'}
    strong_hits = sum(1 for kw in _MEDICAL_KEYWORDS if kw in _visible_search and kw not in _weak_keywords)
    if medical_hits > 0 and strong_hits == 0:
        return True  # only weak/generic keywords — likely false positive

    # ── Strong irrelevance signals ──────────────────────────────────
    _strong_irrelevant = [
        ('продажа доменов', 'domain marketplace'),
        ('интернет-магазин', 'online store'),
        ('программное обеспечение', 'software'),
        ('software development', 'software'),
        ('web development', 'web dev'),
        ('хостинг', 'hosting'),
        ('регистрация доменов', 'domain registration'),
    ]
    for signal, _label in _strong_irrelevant:
        if signal in search_text:
            return True

    return False


# Registry URL patterns — URLs matching these are company registries, not clinic websites
_REGISTRY_URL_PATTERNS = [
    r'/company/', r'/contragent/', r'/entity/', r'/organization/', r'/organizacii/',
    r'/org/', r'/card/', r'/profile/', r'/catalog/',
    r'[?&]inn=', r'[?&]ogrn=', r'[?&]query=',
    r'inn-\d+', r'ogrn-\d+',
    r'/id/\d+',  # checko.ru/id/..., rusprofile.ru/id/...
    r'/place/',  # barber.su/place/..., zoon.ru/place/...
    r'/doctors/',  # prozdor.ru/doctors/...
    r'/clinic/',  # directory clinic detail pages
    r'/salon/',  # beauty salon directories
    r'/master/',  # beauty master directories
]


def _is_registry_url(url: str) -> bool:
    """Check if URL looks like a company registry/aggregator page."""
    import re as _re
    url_lower = url.lower()
    for pattern in _REGISTRY_URL_PATTERNS:
        if _re.search(pattern, url_lower):
            return True
    # Very long URLs (>120 chars) are usually registry detail pages
    if len(url) > 120:
        return True
    return False


class YandexWebSearchClient:
    """Multi-engine web search for competitor website discovery.

    Cascade: DuckDuckGo → Yandex → Google.
    """

    def __init__(self):
        self._playwright = None
        self._browser = None
        self._lock = asyncio.Lock()
        self._ddg_lock = asyncio.Lock()  # serialize DDG requests to avoid rate-limiting
        self._consecutive_failures = 0
        self._short_circuit = False
        self._short_circuit_lock = asyncio.Lock()

    async def _ensure_browser(self):
        if self._browser is not None:
            return self._browser

        async with self._lock:
            if self._browser is not None:
                return self._browser

            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-features=IsolateOrigins,site-per-process",
                    "--disable-infobars",
                    "--window-size=1920,1080",
                ],
            )
            logger.info("YandexWebSearch: Playwright browser launched")
            return self._browser

    async def close(self):
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
            logger.info("YandexWebSearch: Playwright browser closed")

    async def search_website(
        self,
        company_name: str,
        city: str = "",
        timeout_ms: int = 20000,
        max_retries: int = 2,
    ) -> Optional[str]:
        """Find a company's website via web search.

        Cascade: DDG → Yandex → Google → Domain guess.
        Short-circuits after 6 consecutive search-engine failures.
        DDG has built-in retry with backoff for rate limiting (HTTP 202).
        DomainGuess failures do NOT count toward short-circuit
        (guessing domains is inherently unreliable, DNS NXDOMAIN is expected).
        """
        # Short-circuit: if 6+ consecutive search-engine failures,
        # engines are likely blocking us. Don't waste time.
        if self._short_circuit:
            logger.debug(
                "YandexWebSearch: short-circuit active (%d failures), skipping '%s'",
                self._consecutive_failures, company_name[:40],
            )
            return None

        # 1. Try DuckDuckGo Lite first (fast, no browser needed)
        result = await self._search_duckduckgo(company_name, city)
        if result:
            logger.info("YandexWebSearch(DDG): found %s for '%s'", result, company_name)
            async with self._short_circuit_lock:
                self._consecutive_failures = 0
            return result

        # 2. Try Yandex (Playwright)
        result = await self._search_yandex(company_name, city, timeout_ms, max_retries)
        if result:
            async with self._short_circuit_lock:
                self._consecutive_failures = 0
            return result

        # 3. Fallback to Google
        logger.info("YandexWebSearch: no result from Yandex, trying Google for '%s'", company_name)
        result = await self._search_google(company_name, city, timeout_ms, max_retries)
        if result:
            logger.info("YandexWebSearch(Google): found %s for '%s'", result, company_name)
            async with self._short_circuit_lock:
                self._consecutive_failures = 0
            return result

        # All 3 search engines failed — increment short-circuit counter
        # (DomainGuess is a bonus attempt, its failure doesn't count)
        async with self._short_circuit_lock:
            self._consecutive_failures += 1
            if self._consecutive_failures >= 6:
                self._short_circuit = True
                logger.warning(
                    "YandexWebSearch: SHORT-CIRCUIT ACTIVATED after %d consecutive search-engine failures",
                    self._consecutive_failures,
                )
            else:
                logger.info(
                    "YandexWebSearch: all search engines failed (%d/%d) for '%s'",
                    self._consecutive_failures, 6, company_name[:40],
                )

        # 4. Final fallback: domain guessing (fast — just DNS/HTTP checks)
        # Don't count failure — guessing is unreliable by design
        logger.debug("YandexWebSearch: trying domain guess for '%s'", company_name[:40])
        result = await self._guess_domain(company_name, city)
        if result:
            logger.info("YandexWebSearch(guess): found %s for '%s'", result, company_name)
            async with self._short_circuit_lock:
                self._consecutive_failures = 0
            return result

        return None

    async def _search_duckduckgo(
        self,
        company_name: str,
        city: str = "",
    ) -> Optional[str]:
        """Search DuckDuckGo for a company website using the ddgs library.

        Uses DDG's internal API (not HTML scraping) — handles rate limiting
        internally. Synchronous call wrapped in thread pool executor.
        """
        query = f"{company_name} {city}".strip()
        # Strip quotes and special chars that can cause DDG API decode errors
        query = query.replace('“', '').replace('”', '').replace('«', '').replace('»', '').replace('"', '').replace("'", "")

        def _search_sync() -> Optional[str]:
            last_error = None
            for attempt in range(3):
                try:
                    from ddgs import DDGS

                    with DDGS() as ddgs:
                        results = list(ddgs.text(query, max_results=10))
                    break  # success
                except Exception as e:
                    last_error = e
                    if attempt < 2:
                        logger.warning(
                            "YandexWebSearch(DDG): attempt %d/3 error for '%s': %s",
                            attempt + 1, query, e,
                        )
                        import time as _time
                        _time.sleep(1.0 * (attempt + 1))
                    continue
            else:
                logger.warning("YandexWebSearch(DDG): all 3 attempts failed for '%s': %s", query, last_error)
                return None

            logger.info(
                "YandexWebSearch(DDG): query='%s' → %d results",
                query, len(results),
            )

            for r in results:
                href = r.get("href", "").strip()
                if not href or not href.startswith("http"):
                    continue
                if self._is_acceptable_url(href):
                    return self._normalize_url(href)

            return None

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _search_sync)

    async def _search_yandex(
        self,
        company_name: str,
        city: str = "",
        timeout_ms: int = 20000,
        max_retries: int = 2,
    ) -> Optional[str]:
        """Search Yandex for a company website."""
        query = f"{company_name} {city}".strip()
        query_encoded = query.replace(" ", "+")
        url = f"https://yandex.ru/search/?text={query_encoded}"

        for attempt in range(max_retries):
            try:
                browser = await self._ensure_browser()
                page = await browser.new_page()
                await page.add_init_script(_STEALTH_INIT_JS)

                try:
                    await page.set_extra_http_headers(_STEALTH_HEADERS)
                    await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                    await asyncio.sleep(2.0)
                    await page.wait_for_selector("body", timeout=5000)

                    candidates = await page.evaluate(_EXTRACT_JS)

                    logger.info(
                        "YandexWebSearch: query='%s' → %d raw candidates",
                        query, len(candidates),
                    )

                    rejected_count = 0
                    for candidate_url in candidates[:30]:
                        if self._is_acceptable_url(candidate_url):
                            logger.info(
                                "YandexWebSearch: found %s for '%s'",
                                candidate_url, query,
                            )
                            return self._normalize_url(candidate_url)
                        else:
                            rejected_count += 1
                            if rejected_count <= 5:
                                logger.info(
                                    "YandexWebSearch: rejected %s for '%s'",
                                    candidate_url[:150], query,
                                )

                    if not candidates:
                        logger.warning(
                            "YandexWebSearch: zero candidates for '%s' — possible captcha/bot block",
                            query,
                        )
                    else:
                        logger.warning(
                            "YandexWebSearch: all %d candidates rejected for '%s'",
                            len(candidates), query,
                        )

                finally:
                    await page.close()

            except Exception as e:
                logger.warning(
                    "YandexWebSearch attempt %d/%d failed for '%s': %s",
                    attempt + 1, max_retries, query, e,
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(1.0 * (attempt + 1))

        return None

    async def _search_google(
        self,
        company_name: str,
        city: str = "",
        timeout_ms: int = 20000,
        max_retries: int = 2,
    ) -> Optional[str]:
        """Google search fallback for company website."""
        query = f"{company_name} {city}".strip()
        query_encoded = query.replace(" ", "+")
        url = f"https://www.google.com/search?q={query_encoded}&hl=ru"

        google_headers = {
            **_STEALTH_HEADERS,
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        }

        for attempt in range(max_retries):
            try:
                browser = await self._ensure_browser()
                page = await browser.new_page()
                await page.add_init_script(_STEALTH_INIT_JS)

                try:
                    await page.set_extra_http_headers(google_headers)
                    await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                    await asyncio.sleep(2.0)
                    await page.wait_for_selector("body", timeout=5000)

                    candidates = await page.evaluate(_GOOGLE_EXTRACT_JS)

                    logger.info(
                        "YandexWebSearch(Google): query='%s' → %d candidates",
                        query, len(candidates),
                    )

                    for candidate_url in candidates:
                        if self._is_acceptable_url(candidate_url):
                            logger.info(
                                "YandexWebSearch(Google): found %s for '%s'",
                                candidate_url, query,
                            )
                            return self._normalize_url(candidate_url)

                    return None

                finally:
                    await page.close()

            except Exception as e:
                logger.warning(
                    "YandexWebSearch(Google) attempt %d/%d failed for '%s': %s",
                    attempt + 1, max_retries, query, e,
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(1.0 * (attempt + 1))

        return None

    async def _guess_domain(
        self,
        company_name: str,
        city: str = "",
    ) -> Optional[str]:
        """Fallback: guess domain from company name via transliteration + HTTP checks.

        Smart generation: extracts brand words, avoids common words (клиника, стоматология),
        generates short variants, and verifies via parallel HTTP GET requests.
        """
        name_lower = company_name.lower().strip()
        # Split on spaces, quotes, punctuation
        raw_words = [w for w in re.split(r'[\s,."«»()—–-]+', name_lower) if w]
        # Filter out common words to find brand-identifying terms
        words = [w for w in raw_words if w not in _STRIP_WORDS]
        if not words:
            words = raw_words  # fallback: use all words if everything was stripped

        # Generate slugs — transliterated + translated variants
        slugs_all: list[str] = []
        for w in words:
            v = transliterate(w, translate_words=True)
            if isinstance(v, list):
                slugs_all.extend(v)
            else:
                slugs_all.append(v)
        slugs = list(dict.fromkeys([s for s in slugs_all if s and len(s) >= 2]))  # unique, keep order

        # Also generate translated versions of the full name for multi-word combos
        full_slugs = transliterate(name_lower, translate_words=True)
        if not isinstance(full_slugs, list):
            full_slugs = [full_slugs]

        candidates = []

        def add_variants(slug: str, extra_tlds: bool = False):
            """Add domain candidates for a slug, with and without dashes."""
            if not slug or len(slug) < 3 or len(slug) > 25:
                return
            for tld in _DOMAIN_TLDS:
                candidates.append(f"{slug}{tld}")
            if extra_tlds:
                for tld in _EXTRA_TLDS:
                    candidates.append(f"{slug}{tld}")
            # Variant without dashes
            no_dash = slug.replace("-", "")
            if no_dash != slug and 3 <= len(no_dash) <= 25:
                for tld in _DOMAIN_TLDS:
                    candidates.append(f"{no_dash}{tld}")

        # 1. First brand word (single word — best guess for branded clinics)
        if slugs:
            add_variants(slugs[0])

        # 2. Two-word combos (with extra TLDs for brandable combos)
        if len(slugs) >= 2:
            add_variants(f"{slugs[0]}-{slugs[-1]}", extra_tlds=True)
            add_variants(f"{slugs[0]}{slugs[-1]}")
            if len(slugs) > 2:
                add_variants(f"{slugs[0]}-{slugs[1]}", extra_tlds=True)

        # 3. Full name variants (only if ≤30 chars)
        for full_slug in full_slugs:
            if full_slug and 3 <= len(full_slug) <= 30:
                for tld in _DOMAIN_TLDS:
                    candidates.append(f"{full_slug}{tld}")
                for tld in _EXTRA_TLDS:
                    candidates.append(f"{full_slug}{tld}")

        # 4. City-brand combos
        if city and slugs:
            city_slug = transliterate(city)
            if city_slug and len(city_slug) >= 2:
                for s in slugs[:3]:  # try first few brand slugs
                    add_variants(f"{s}-{city_slug}")

        # Deduplicate, max 20 candidates, filter by length
        seen = set()
        unique = []
        for c in candidates:
            domain_name = c.split(".")[0] if "." in c else c
            if c not in seen and 3 <= len(domain_name) <= 30:
                seen.add(c)
                unique.append(c)
                if len(unique) >= 20:
                    break

        logger.info(
            "DomainGuess: trying %d candidates for '%s' (first 5: %s)",
            len(unique), company_name, unique[:5],
        )

        # Fresh client
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as guess_client:
            sem = asyncio.Semaphore(5)
            verified: list[str] = []

            async def check_one(domain: str):
                async with sem:
                    for scheme in ("https://", "http://"):
                        try:
                            punycode_domain = domain.encode("idna").decode("ascii")
                        except (UnicodeError, ValueError):
                            punycode_domain = domain
                        url = f"{scheme}{punycode_domain}"
                        try:
                            resp = await guess_client.get(
                                url, headers={
                                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                                }
                            )
                            if resp.status_code < 500:
                                if _is_parked_domain(resp.text, domain):
                                    logger.info("DomainGuess: ✗ %s is a parked domain, skipping", url)
                                    return
                                if _is_irrelevant_site(resp.text, company_name):
                                    logger.info("DomainGuess: ✗ %s content not relevant for '%s', skipping", url, company_name)
                                    return
                                display_url = f"{scheme}{domain}"
                                verified.append(display_url)
                                logger.info("DomainGuess: ✓ %s (HTTP %d)", display_url, resp.status_code)
                                return
                            logger.warning("DomainGuess: ✗ %s HTTP %d", url, resp.status_code)
                        except Exception as e:
                            logger.warning("DomainGuess: ✗ %s → %s: %s", url, type(e).__name__, e)
                            continue

            check_tasks = [asyncio.create_task(check_one(d)) for d in unique]

            if check_tasks:
                for coro in asyncio.as_completed(check_tasks):
                    await coro
                    if verified:
                        for t in check_tasks:
                            if not t.done():
                                t.cancel()
                        break

            if verified:
                url = self._normalize_url(verified[0])
                logger.info("DomainGuess: found %s for '%s'", url, company_name)
                return url

        logger.info("DomainGuess: no reachable domain for '%s'", company_name)
        return None

    @staticmethod
    def _is_acceptable_url(url_str: str) -> bool:
        """Check if a URL is an acceptable Russian clinic website.

        Filters out aggregators, catalogs, social media, foreign TLDs,
        and registry pages (via URL patterns).
        Uses suffix matching for skip domains (e.g. moscow.flamp.ru → flamp.ru).
        """
        domain = YandexWebSearchClient._extract_domain(url_str)
        if not domain:
            return False
        # Exact match
        if domain in _SKIP_DOMAINS:
            return False
        # Suffix match (catches subdomains like moscow.flamp.ru)
        for skip_domain in _SKIP_DOMAINS:
            if domain.endswith("." + skip_domain):
                return False
        if "yandex" in domain or "google" in domain or "duckduckgo" in domain:
            return False
        # Reject foreign TLDs
        for tld in _FOREIGN_TLDS:
            if domain.endswith(tld):
                return False
        # Reject registry pages by URL pattern
        if _is_registry_url(url_str):
            return False
        return True

    @staticmethod
    def _extract_domain(url_str: str) -> Optional[str]:
        """Extract domain from a URL, stripping www. prefix."""
        try:
            parsed = urlparse(url_str)
            host = parsed.hostname or ""
            return host.removeprefix("www.").lower()
        except Exception:
            return None

    @staticmethod
    def _normalize_url(url_str: str) -> str:
        """Ensure URL has https:// scheme and no trailing slash."""
        if not url_str.startswith(("http://", "https://")):
            url_str = "https://" + url_str
        return url_str.rstrip("/")


# ── Singleton ────────────────────────────────────────────────────────

_web_search: YandexWebSearchClient | None = None


def get_web_search_client() -> YandexWebSearchClient:
    global _web_search
    if _web_search is None:
        _web_search = YandexWebSearchClient()
    return _web_search
