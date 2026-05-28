"""ArticleScanner — find journal publications by doctor/clinic name.

Uses Crossref API (free, no key, works from Russia) as primary source.
PubMed E-utilities as optional secondary source (requires API key for Russia).

TTL: 7 days (publications don't change daily).
"""

import logging
import re
import time
import urllib.parse
from typing import Optional

import httpx

from .models import ArticleInfo, ArticleSearchResult

logger = logging.getLogger(__name__)

USER_AGENT = "meAI/1.0 (mailto:me@mikhaileliseev.com)"

CROSSREF_WORKS = "https://api.crossref.org/works"
PUBMED_SEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

_RATE_LIMIT_DELAY = 0.6  # Crossref allows ~2 req/s without token


class ArticleScanner:
    """Scans academic databases for publications by author name."""

    def __init__(self, timeout: float = 12.0, cache_ttl: int = 604800) -> None:
        self._client = httpx.Client(
            timeout=httpx.Timeout(timeout),
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            follow_redirects=True,
        )
        self._cache: dict[str, tuple[float, ArticleSearchResult]] = {}
        self._cache_ttl = cache_ttl
        self._last_request_ts: float = 0.0

    def _rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_request_ts
        if elapsed < _RATE_LIMIT_DELAY:
            time.sleep(_RATE_LIMIT_DELAY - elapsed)
        self._last_request_ts = time.monotonic()

    def close(self) -> None:
        self._client.close()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search_author(self, name: str, specialty: str = "") -> ArticleSearchResult:
        """Search for publications by author name.

        Strategy:
        1. Crossref API (primary — free, works from Russia, 150M+ records)
        2. PubMed E-utilities (secondary — may need API key from Russia)

        If specialty is provided, articles from clearly non-medical journals
        are filtered out (e.g. geology, economics, engineering).
        """
        cached = self._cache_get(name)
        if cached is not None:
            result = cached
        else:
            result = ArticleSearchResult(
                query_name=name,
                sources_searched=[],
            )

            # Primary: Crossref API
            crossref_articles = self._search_crossref(name)
            result.sources_searched.append("crossref")
            result.articles.extend(crossref_articles)
            logger.info("Crossref found %d articles for '%s'", len(crossref_articles), name)

            # Secondary: PubMed (optional, may be blocked in Russia)
            pubmed_articles = self._search_pubmed(name)
            if pubmed_articles:
                result.sources_searched.append("pubmed")
                result.articles.extend(pubmed_articles)

            # Deduplicate by DOI first, then by title
            seen_dois: set[str] = set()
            seen_titles: set[str] = set()
            unique: list[ArticleInfo] = []
            for art in result.articles:
                doi_key = art.doi.lower().strip() if art.doi else ""
                title_key = art.title[:60].lower().strip()
                if doi_key and doi_key in seen_dois:
                    continue
                if title_key and title_key in seen_titles:
                    continue
                if doi_key:
                    seen_dois.add(doi_key)
                if title_key:
                    seen_titles.add(title_key)
                unique.append(art)
            result.articles = unique

            # Filter by author name relevance
            result.articles = self._filter_by_author_relevance(name, result.articles)

            result.total_found = len(result.articles)
            self._cache_set(name, result)

        # Always apply medical relevance filter — a doctor wouldn't publish
        # in geology, economics, or engineering journals regardless of specialty.
        # When specialty IS provided, articles matching it get an extra boost.
        filtered_articles = self._filter_by_medical_relevance(
            result.articles, specialty
        )
        result = ArticleSearchResult(
            query_name=result.query_name,
            sources_searched=list(result.sources_searched),
        )
        result.articles = filtered_articles
        result.total_found = len(filtered_articles)

        return result

    # ------------------------------------------------------------------
    # Crossref API
    # ------------------------------------------------------------------

    def _search_crossref(self, name: str) -> list[ArticleInfo]:
        """Search Crossref API for publications by author name.

        Crossref is a free, open API with 150M+ records. Works from Russia
        without API key. Rate limit: ~2 req/s without token.

        Search strategy: query by surname first, then filter by full name match.
        """
        articles: list[ArticleInfo] = []
        surname = name.split()[0] if name else name

        try:
            self._rate_limit()
            params = {
                "query.author": surname,
                "rows": 20,
                "sort": "published",
                "order": "desc",
                "filter": "type:journal-article",
            }
            resp = self._client.get(CROSSREF_WORKS, params=params)
            if resp.status_code != 200:
                logger.warning("Crossref search for '%s' returned %d", name, resp.status_code)
                return articles

            data = resp.json()
            items = data.get("message", {}).get("items", [])

            for item in items:
                try:
                    # Title
                    title_list = item.get("title", [])
                    title = title_list[0] if title_list else ""
                    if not title or len(title) < 10:
                        continue

                    # Authors
                    authors = []
                    author_match = False
                    for a in item.get("author", []):
                        family = a.get("family", "")
                        given = a.get("given", "")
                        full = f"{family} {given}".strip()
                        authors.append(full)
                        if surname.lower() in family.lower():
                            author_match = True

                    # Always include if surname matches; otherwise skip
                    if not author_match and authors:
                        continue

                    # Year
                    year = 0
                    pub_parts = item.get("published-print", {}).get("date-parts", [[0]])
                    if pub_parts and pub_parts[0]:
                        year = pub_parts[0][0]
                    if not year:
                        created_parts = item.get("created", {}).get("date-parts", [[0]])
                        if created_parts and created_parts[0]:
                            year = created_parts[0][0]

                    # Journal
                    container = item.get("container-title", [])
                    journal = container[0] if container else ""

                    # DOI
                    doi = item.get("DOI", "")

                    # Citations
                    citations = item.get("is-referenced-by-count", 0)

                    # URL
                    url = f"https://doi.org/{doi}" if doi else ""

                    articles.append(ArticleInfo(
                        title=title[:300],
                        authors=authors[:10],
                        journal=journal[:200],
                        year=year,
                        citations=citations,
                        doi=doi,
                        url=url,
                        source="crossref",
                    ))
                except Exception:
                    continue

        except Exception as e:
            logger.warning("Crossref search failed for '%s': %s", name, e)

        return articles

    # ------------------------------------------------------------------
    # PubMed E-utilities (secondary)
    # ------------------------------------------------------------------

    def _search_pubmed(self, name: str) -> list[ArticleInfo]:
        """Search PubMed by author name using E-utilities API.

        NOTE: May return 403 from Russia without an NCBI API key.
        If blocked, this silently returns an empty list.
        """
        articles: list[ArticleInfo] = []
        try:
            encoded = urllib.parse.quote(name)
            search_url = (
                f"{PUBMED_SEARCH}"
                f"?db=pubmed&term={encoded}[author]&retmax=10&retmode=json"
            )
            resp = self._client.get(search_url)
            if resp.status_code != 200:
                logger.debug("PubMed search returned %d (may be blocked in Russia)", resp.status_code)
                return articles

            data = resp.json()
            ids = data.get("esearchresult", {}).get("idlist", [])

            if not ids:
                return articles

            fetch_url = (
                f"{PUBMED_FETCH}"
                f"?db=pubmed&id={','.join(ids)}&retmode=json"
            )
            fetch_resp = self._client.get(fetch_url)
            if fetch_resp.status_code != 200:
                return articles

            summary = fetch_resp.json()
            results = summary.get("result", {})

            for pmid in ids:
                try:
                    doc = results.get(pmid, {})
                    title = doc.get("title", "")
                    pubdate = doc.get("pubdate", "")
                    source = doc.get("source", "")
                    doi = ""
                    article_ids = doc.get("articleids", [])
                    for aid in article_ids:
                        if aid.get("idtype") == "doi":
                            doi = aid.get("value", "")

                    year_match = re.search(r"(\d{4})", pubdate)
                    year = int(year_match.group(1)) if year_match else 0

                    authors_raw = doc.get("authors", [])
                    authors = [a.get("name", "") for a in authors_raw]

                    articles.append(ArticleInfo(
                        title=title,
                        authors=authors,
                        journal=source,
                        year=year,
                        doi=doi,
                        url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        source="pubmed",
                    ))
                except Exception:
                    continue

        except Exception as e:
            logger.debug("PubMed search failed for '%s': %s", name, e)

        return articles

    # ------------------------------------------------------------------
    # Author relevance filter
    # ------------------------------------------------------------------

    @staticmethod
    def _filter_by_author_relevance(name: str, articles: list[ArticleInfo]) -> list[ArticleInfo]:
        """Filter articles by author name match.

        Two-stage filter:
        1. Surname (first word) must appear in at least one author's name
        2. If query has 2+ words, at least one author's name must also contain
           the first letter of the second word (given name initial).

        This filters out same-surname-different-person matches (e.g. Жуманова Г.
        when searching for Жуманова Екатерина).
        """
        if not name or not articles:
            return articles

        parts = name.split()
        surname = parts[0].lower()
        if len(surname) < 3:
            return articles

        given_initial = parts[1][0].lower() if len(parts) > 1 and parts[1] else ""

        def _author_matches(a: ArticleInfo) -> bool:
            for author in a.authors:
                al = author.lower()
                if surname not in al:
                    continue
                if not given_initial:
                    return True
                # Extract the first initial from the given name part.
                # Crossref format: "family given" → "Жуманова Е.Н."
                # The first letter after the surname is the given-name initial.
                surname_pos = al.find(surname)
                after_surname = al[surname_pos + len(surname):].strip()
                # First non-dot, non-space character after surname = first initial
                first_initial = ""
                for ch in after_surname:
                    if ch.isalpha():
                        first_initial = ch
                        break
                if first_initial == given_initial:
                    return True
            return False

        # Stage 1: strict match (surname + initial)
        if given_initial:
            filtered = [a for a in articles if _author_matches(a)]
        else:
            filtered = [
                a for a in articles
                if any(surname in author.lower() for author in a.authors)
            ]

        # Stage 2: if strict removed everything, fall back to surname-only
        if not filtered and given_initial:
            filtered = [
                a for a in articles
                if any(surname in author.lower() for author in a.authors)
            ]

        # Last resort: top-3 by year
        if not filtered:
            articles.sort(key=lambda a: a.year, reverse=True)
            return articles[:3]

        return filtered

    # ------------------------------------------------------------------
    # Medical relevance filter
    # ------------------------------------------------------------------

    # Journals/fields that are clearly NOT medical. If a journal name matches
    # one of these AND has no medical indicators, the article is filtered out.
    _NON_MEDICAL_INDICATORS: tuple[str, ...] = (
        # Geology / Earth sciences
        "геолог", "геофиз", "сейсмолог", "сейсмическ", "минералог",
        "вулканолог", "почвовед", "геодез", "geology", "geophys",
        "geoscience", "seismic", "volcano", "mineralog",
        # Economics / Business / Management
        "экономик", "экономік", "економік", "предприниматель", "підприємництв",
        "финанс", "фінанс", "маркетинг", "менеджмент", "бухгалтерск",
        "economics", "economy", "finance", "accounting", "marketing",
        "management journal", "business", "property relations",
        "ekonomik", "ekonomika", "ekonomich", "predprinimatel", "finans", "bukhgaltersk",
        # Engineering / Manufacturing
        "машиностроен", "станкостроен", "приборостроен", "металлообработк",
        "manufacturing", "machining", "machine tool",
        # Computer science (non-medical)
        "вычислительн", "computer science", "программная инженер",
        # Agriculture
        "сельскохозяйствен", "сельск", "сільськ", "агроном", "аграр",
        "животновод", "растениевод", "ветеринар",
        "agriculture", "agronomy", "agrarian",
        "veterinary", "animal science",
        # Linguistics / Literature
        "филолог", "філолог", "лингвист", "лінгвіст", "языкознание",
        "литературовед", "philology", "linguistics",
        # History / Archaeology
        "историческ", "археолог", "этнограф", "archaeology",
        "istorichesk", "istoriya", "etnograf",
        # Law
        "юридическ", "правовед", "государство и право",
        "law review", "law journal", "jurisprudence", "legal ",
        "yuridich", "yuridichesk", "pravoved", "gosudarstvo i pravo",
        # Construction / Architecture
        "строитель", "архитектур", "construction", "building materials",
        "stroitel", "stroitelny", "arkhitektur",
        # Transport
        "транспорт", "авиацион", "космическ", "aviation", "space engineering",
        # Mining / Oil & Gas
        "металлург", "горнодобыва", "нефтегаз", "нефтян",
        "metallurgy", "mining", "oil & gas", "petroleum",
        "metallurg", "gornodobyv", "neftegaz", "neftyan",
        # Sociology / Political science
        "социолог", "политолог", "философ", "sociology", "political",
        "philosophy", "sotsiolog", "politolog", "filosof",
        # Pedagogy / Education (non-medical)
        "педагогик", "педагогическ", "образование и наука",
        "науки и образования", "science and education",
        "образование в высшей", "безперервної освіти",
        "pedagogy", "education research",
        "pedagogik", "pedagogich", "obrazovanie", "obrazovaniya", "nepreryvnogo", "bezperervnoi",
        # Generic academic journals (non-medical unless from medical institution)
        "вестник", "науковий вісник", "научный вестник", "научной мысли",
        # Latin transliterations of Russian/Ukrainian journal names
        "vestnik", "nauchny", "nauchnyi", "nauchnii", "naukovy", "naukovi", "naukovii",
        "zapiski", "zapisky", "zapysky",
        "seriya", "seriia", "seria",
        "psikholog", "psiholog", "psykholoh", "psikhologii", "psihologii",
        "verhnevolzh",
        "agrotechnological", "agro", "food processing",
        "еколог", "ecology", "техносфер", "technosphere",
        # Housing / Urban studies
        "жилищ", "housing", "urban studies", "урбанист",
        # Thermal / Power engineering
        "термоэлектр", "thermoelectr", "теплоэнергет", "теплофиз",
        "теплов", "энергосбережен", "энергетик", "power engineering",
        # Materials science (non-bio)
        "материаловед", "materials science", "порошков", "металловед",
        # Latin transliterations: basic sciences (when not bio/medical)
        "khimi", "khimiy", "khimia", "khimichesk",
        "fizik", "fizika", "fizichesk",
        "matematik", "matematika", "matematichesk",
        "tekhnolog", "tekhnika", "tekhnichesk", "tekhnicheskii",
        "energetik", "energetika", "energetichesk",
        "teplofiz", "teploenerget", "termoelektr",
    )

    # Medical/healthcare keywords. If a journal or title contains any of these,
    # it's kept even if it also matches a non-medical indicator.
    _MEDICAL_INDICATORS: tuple[str, ...] = (
        "medic", "медицин", "health", "здрав", "здоров",
        "clinic", "клиник", "клинич", "hospital", "patient",
        "surgery", "surgic", "хирург", "physician", "doctor", "врач",
        "pharma", "фарма", "drug", "treatment", "diagnosis", "diagnost",
        "therapy", "therap", "терап", "disease", "болезн",
        "biolog", "биолог", "cell", "molecular", "молекул",
        "genetic", "генет", "immun", "иммун", "microbiol", "микробиолог",
        "oncology", "онколог", "cancer", "tumor", "опухол",
        "cardiology", "кардиолог", "heart", "vascular", "сосудист",
        "neurology", "невролог", "neurosci", "нейро",
        "dermatology", "дерматолог", "skin",
        "gynecology", "гинеколог", "obstetric", "акушер",
        "urology", "уролог", "ophthalmology", "офтальмолог",
        "endocrin", "эндокрин", "gastroenter", "гастроэнтер",
        "pulmonology", "пульмонолог", "respiratory",
        "pediatric", "педиатр", "детск",
        "psychiatry", "психиатр", "mental health", "clinical psychology",
        "dentist", "стоматолог", "dental",
        "orthop", "ортопед", "trauma", "травм",
        "rehabilit", "реабилит", "physiotherap", "физиотерап",
        "anesthesia", "анестез", "radiology", "рентген",
        "nutrition", "нутрициолог", "diet", "диет",
        "toxicology", "токсиколог", "epidemiol", "эпидемиолог",
        "anatomy", "анатом", "physiology", "физиолог",
        "nurse", "nursing", "medical journal", "medical center",
        "lancet", "bmj ", "jama", "nejm",
        "science of food", "food science",
        "biomed", "биомед",
        "laser in medic", "лазерн",
        "cosmet", "космет",
    )

    @classmethod
    def _filter_by_medical_relevance(
        cls, articles: list[ArticleInfo], specialty: str = ""
    ) -> list[ArticleInfo]:
        """Filter out articles from clearly non-medical journals.

        Strategy:
        1. If journal name has a medical indicator → keep
        2. If journal name has a non-medical indicator → filter out
        3. Otherwise → keep (conservative: when in doubt, don't filter)

        Only the journal name is checked — article titles can use medical
        terminology even in non-medical fields (veterinary, biology, etc.).
        A doctor wouldn't publish in an agronomy or geology journal.
        """
        if not articles:
            return articles

        filtered: list[ArticleInfo] = []
        for art in articles:
            journal_lower = art.journal.lower()

            has_medical = any(ind in journal_lower for ind in cls._MEDICAL_INDICATORS)
            if has_medical:
                filtered.append(art)
                continue

            is_non_medical = any(ind in journal_lower for ind in cls._NON_MEDICAL_INDICATORS)
            if not is_non_medical:
                filtered.append(art)

        return filtered

    # ------------------------------------------------------------------
    # Cache
    # ------------------------------------------------------------------

    def _cache_get(self, key: str) -> Optional[ArticleSearchResult]:
        entry = self._cache.get(key)
        if entry is None:
            return None
        ts, value = entry
        if time.monotonic() - ts > self._cache_ttl:
            del self._cache[key]
            return None
        return value

    def _cache_set(self, key: str, value: ArticleSearchResult) -> None:
        self._cache[key] = (time.monotonic(), value)
