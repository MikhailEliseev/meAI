"""
E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness) scoring for medical YMYL content.

Based on Google's Search Quality Rater Guidelines and medical content best practices.
Focuses on medical marketing context (iamaim.ru).
"""

import re
from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup


class EEATScorer:
    """
    Score content for E-E-A-T signals with medical YMYL focus.

    E-E-A-T components:
    - Experience: First-hand experience, case studies, patient outcomes
    - Expertise: Medical qualifications, credentials, specialization
    - Authoritativeness: Recognition, citations, industry standing
    - Trustworthiness: Transparency, accuracy, citations, updates
    """

    # Medical credentials patterns
    MEDICAL_CREDENTIALS = [
        r"\bMD\b",
        r"\bDO\b",
        r"\bPhD\b",
        r"\bDDS\b",
        r"\bRN\b",
        r"\bNP\b",
        r"\bPA\b",
        r"врач",
        r"доктор",
        r"профессор",
        r"кандидат медицинских наук",
        r"доктор медицинских наук",
    ]

    # Medical terminology (indicates expertise)
    MEDICAL_TERMS = [
        "диагностика",
        "лечение",
        "терапия",
        "хирургия",
        "анестезия",
        "реабилитация",
        "профилактика",
        "симптомы",
        "заболевание",
        "патология",
    ]

    # Authoritative sources for citations
    AUTHORITATIVE_SOURCES = [
        "pubmed",
        "ncbi.nlm.nih.gov",
        "who.int",
        "cdc.gov",
        "nih.gov",
        "minzdrav.gov.ru",
        "rosminzdrav.ru",
        "медвестник.рф",
    ]

    def __init__(
        self,
        min_word_count: int = 300,
        freshness_months: int = 12,
        min_update_percentage: float = 0.20,
    ):
        """
        Initialize E-E-A-T scorer.

        Args:
            min_word_count: Minimum word count for quality content
            freshness_months: Maximum age in months for fresh content
            min_update_percentage: Minimum content update percentage (20-30%)
        """
        self.min_word_count = min_word_count
        self.freshness_months = freshness_months
        self.min_update_percentage = min_update_percentage

    def score(
        self,
        html: str,
        text: str,
        url: str,
        published_date: Optional[datetime] = None,
        updated_date: Optional[datetime] = None,
    ) -> dict:
        """
        Calculate E-E-A-T score for content.

        Args:
            html: Raw HTML content
            text: Clean text content
            url: Page URL
            published_date: Publication date (if available)
            updated_date: Last update date (if available)

        Returns:
            Dictionary with E-E-A-T scores and signals
        """
        soup = BeautifulSoup(html, "html.parser")

        # Calculate individual E-E-A-T components
        experience_score = self._score_experience(text, soup)
        expertise_score = self._score_expertise(text, soup, html)
        authoritativeness_score = self._score_authoritativeness(text, soup, html)
        trustworthiness_score = self._score_trustworthiness(
            text, soup, html, published_date, updated_date
        )

        # Overall E-E-A-T score (weighted average)
        # Medical YMYL: Expertise and Trustworthiness are most critical
        overall_score = (
            experience_score * 0.15
            + expertise_score * 0.35
            + authoritativeness_score * 0.20
            + trustworthiness_score * 0.30
        )

        # Compliance level
        compliance = self._determine_compliance(overall_score)

        return {
            "overall_score": round(overall_score, 2),
            "compliance": compliance,
            "experience": {
                "score": round(experience_score, 2),
                "signals": self._get_experience_signals(text, soup),
            },
            "expertise": {
                "score": round(expertise_score, 2),
                "signals": self._get_expertise_signals(text, soup, html),
            },
            "authoritativeness": {
                "score": round(authoritativeness_score, 2),
                "signals": self._get_authoritativeness_signals(text, soup, html),
            },
            "trustworthiness": {
                "score": round(trustworthiness_score, 2),
                "signals": self._get_trustworthiness_signals(
                    text, soup, html, published_date, updated_date
                ),
            },
            "recommendations": self._generate_recommendations(
                experience_score,
                expertise_score,
                authoritativeness_score,
                trustworthiness_score,
            ),
        }

    def _score_experience(self, text: str, soup: BeautifulSoup) -> float:
        """
        Score first-hand experience signals.

        Indicators:
        - Case studies, patient outcomes
        - Before/after examples
        - Personal experience language ("we", "our patients")
        - Specific numbers and results
        """
        score = 0.0

        # Case study indicators
        case_study_patterns = [
            r"случай из практики",
            r"клинический случай",
            r"пациент[а-я]*\s+\d+\s+лет",
            r"результат[ы]?\s+лечения",
            r"до и после",
        ]
        for pattern in case_study_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += 15.0

        # Personal experience language
        personal_patterns = [r"\bнаш[иеа]?\b", r"\bмы\b", r"наши пациенты"]
        personal_count = sum(
            len(re.findall(pattern, text, re.IGNORECASE))
            for pattern in personal_patterns
        )
        score += min(personal_count * 2, 20.0)

        # Specific numbers (outcomes, statistics)
        numbers_pattern = r"\d+%|\d+\s+пациент"
        numbers_count = len(re.findall(numbers_pattern, text))
        score += min(numbers_count * 3, 15.0)

        # Images with before/after
        images = soup.find_all("img")
        for img in images:
            alt = img.get("alt", "").lower()
            if "до" in alt and "после" in alt:
                score += 10.0
                break

        return min(score, 100.0)

    def _score_expertise(self, text: str, soup: BeautifulSoup, html: str) -> float:
        """
        Score medical expertise signals.

        Indicators:
        - Medical credentials (MD, PhD, врач)
        - Specialization mentions
        - Medical terminology usage
        - Author bio with qualifications
        """
        score = 0.0

        # Medical credentials
        credentials_found = []
        for pattern in self.MEDICAL_CREDENTIALS:
            if re.search(pattern, text, re.IGNORECASE):
                credentials_found.append(pattern)
                score += 15.0

        # Cap credentials score
        score = min(score, 30.0)

        # Medical terminology density
        term_count = sum(
            text.lower().count(term.lower()) for term in self.MEDICAL_TERMS
        )
        word_count = len(text.split())
        if word_count > 0:
            term_density = term_count / word_count
            score += min(term_density * 1000, 25.0)

        # Author bio section
        author_bio = soup.find(["div", "section"], class_=re.compile(r"author|bio"))
        if author_bio:
            bio_text = author_bio.get_text()
            if any(
                re.search(pattern, bio_text, re.IGNORECASE)
                for pattern in self.MEDICAL_CREDENTIALS
            ):
                score += 20.0

        # Specialization mentions
        specialization_patterns = [
            r"специализ[а-я]+",
            r"специалист по",
            r"эксперт в области",
        ]
        for pattern in specialization_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += 10.0
                break

        # Schema.org markup for medical professionals
        if "MedicalOrganization" in html or "Physician" in html:
            score += 15.0

        return min(score, 100.0)

    def _score_authoritativeness(
        self, text: str, soup: BeautifulSoup, html: str
    ) -> float:
        """
        Score authoritativeness signals.

        Indicators:
        - Citations to authoritative sources
        - Awards, certifications, memberships
        - Media mentions, publications
        - Industry recognition
        """
        score = 0.0

        # Citations to authoritative sources
        links = soup.find_all("a", href=True)
        authoritative_citations = 0
        for link in links:
            href = link.get("href", "").lower()
            if any(source in href for source in self.AUTHORITATIVE_SOURCES):
                authoritative_citations += 1

        score += min(authoritative_citations * 10, 30.0)

        # Awards and certifications
        award_patterns = [
            r"награ[дж][а-я]*",
            r"сертификат",
            r"лицензия",
            r"аккредитация",
            r"член[а-я]*\s+ассоциации",
        ]
        for pattern in award_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += 10.0

        # Publications and media
        publication_patterns = [
            r"публикаци[яи]",
            r"статья в",
            r"исследование",
            r"научная работа",
        ]
        for pattern in publication_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += 8.0

        # Industry recognition
        recognition_patterns = [r"лучш[ий]", r"топ-\d+", r"рейтинг"]
        for pattern in recognition_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += 5.0

        # Organization schema
        if "MedicalOrganization" in html:
            score += 10.0

        return min(score, 100.0)

    def _score_trustworthiness(
        self,
        text: str,
        soup: BeautifulSoup,
        html: str,
        published_date: Optional[datetime],
        updated_date: Optional[datetime],
    ) -> float:
        """
        Score trustworthiness signals.

        Indicators:
        - Content freshness (updated within 6-12 months)
        - Transparency (contact info, privacy policy)
        - Accuracy (citations, references)
        - Security (HTTPS, privacy)
        """
        score = 0.0

        # Content freshness
        if updated_date:
            months_old = (datetime.now() - updated_date).days / 30
            if months_old <= self.freshness_months:
                score += 25.0
            elif months_old <= 24:
                score += 15.0
            else:
                score += 5.0
        elif published_date:
            months_old = (datetime.now() - published_date).days / 30
            if months_old <= self.freshness_months:
                score += 20.0
            elif months_old <= 24:
                score += 10.0

        # Update date visible
        update_patterns = [
            r"обновлено",
            r"последнее обновление",
            r"дата обновления",
            r"updated",
        ]
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in update_patterns):
            score += 10.0

        # Contact information
        contact_patterns = [r"контакт[ы]", r"телефон", r"email", r"адрес"]
        contact_count = sum(
            1 for pattern in contact_patterns if re.search(pattern, text, re.IGNORECASE)
        )
        score += min(contact_count * 5, 15.0)

        # Privacy policy and legal
        legal_patterns = [
            r"политика конфиденциальности",
            r"пользовательское соглашение",
            r"правовая информация",
        ]
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in legal_patterns):
            score += 10.0

        # References and citations
        references = soup.find_all(["cite", "blockquote"])
        score += min(len(references) * 3, 15.0)

        # Medical disclaimer
        disclaimer_patterns = [
            r"консультация врача",
            r"не является медицинской консультацией",
            r"обратитесь к специалисту",
        ]
        if any(
            re.search(pattern, text, re.IGNORECASE) for pattern in disclaimer_patterns
        ):
            score += 10.0

        # Structured data (schema.org)
        if "schema.org" in html:
            score += 10.0

        return min(score, 100.0)

    def _determine_compliance(self, score: float) -> str:
        """Determine E-E-A-T compliance level."""
        if score >= 80:
            return "excellent"
        elif score >= 60:
            return "good"
        elif score >= 40:
            return "fair"
        else:
            return "poor"

    def _get_experience_signals(self, text: str, soup: BeautifulSoup) -> list[str]:
        """Extract experience signals found."""
        signals = []

        if re.search(r"случай из практики|клинический случай", text, re.IGNORECASE):
            signals.append("Case studies present")

        if re.search(r"до и после", text, re.IGNORECASE):
            signals.append("Before/after examples")

        personal_count = len(re.findall(r"\bнаш[иеа]?\b|\bмы\b", text, re.IGNORECASE))
        if personal_count > 5:
            signals.append(f"Personal experience language ({personal_count} instances)")

        numbers_count = len(re.findall(r"\d+%|\d+\s+пациент", text))
        if numbers_count > 0:
            signals.append(f"Specific outcomes ({numbers_count} instances)")

        return signals

    def _get_expertise_signals(
        self, text: str, soup: BeautifulSoup, html: str
    ) -> list[str]:
        """Extract expertise signals found."""
        signals = []

        credentials = []
        for pattern in self.MEDICAL_CREDENTIALS:
            if re.search(pattern, text, re.IGNORECASE):
                credentials.append(pattern.replace("\\b", "").replace("\\", ""))

        if credentials:
            signals.append(f"Medical credentials: {', '.join(credentials[:3])}")

        term_count = sum(
            text.lower().count(term.lower()) for term in self.MEDICAL_TERMS
        )
        if term_count > 10:
            signals.append(f"Medical terminology ({term_count} instances)")

        if soup.find(["div", "section"], class_=re.compile(r"author|bio")):
            signals.append("Author bio section present")

        if "MedicalOrganization" in html or "Physician" in html:
            signals.append("Medical schema markup present")

        return signals

    def _get_authoritativeness_signals(
        self, text: str, soup: BeautifulSoup, html: str
    ) -> list[str]:
        """Extract authoritativeness signals found."""
        signals = []

        links = soup.find_all("a", href=True)
        authoritative_count = sum(
            1
            for link in links
            if any(
                source in link.get("href", "").lower()
                for source in self.AUTHORITATIVE_SOURCES
            )
        )

        if authoritative_count > 0:
            signals.append(f"Authoritative citations ({authoritative_count})")

        if re.search(
            r"награ[дж][а-я]*|сертификат|лицензия", text, re.IGNORECASE
        ):
            signals.append("Awards/certifications mentioned")

        if re.search(r"публикаци[яи]|статья в|исследование", text, re.IGNORECASE):
            signals.append("Publications mentioned")

        if "MedicalOrganization" in html:
            signals.append("Organization schema present")

        return signals

    def _get_trustworthiness_signals(
        self,
        text: str,
        soup: BeautifulSoup,
        html: str,
        published_date: Optional[datetime],
        updated_date: Optional[datetime],
    ) -> list[str]:
        """Extract trustworthiness signals found."""
        signals = []

        if updated_date:
            months_old = (datetime.now() - updated_date).days / 30
            signals.append(f"Last updated: {months_old:.1f} months ago")

        if re.search(r"обновлено|последнее обновление", text, re.IGNORECASE):
            signals.append("Update date visible")

        contact_count = sum(
            1
            for pattern in [r"контакт[ы]", r"телефон", r"email"]
            if re.search(pattern, text, re.IGNORECASE)
        )
        if contact_count > 0:
            signals.append(f"Contact information ({contact_count} types)")

        if re.search(r"политика конфиденциальности", text, re.IGNORECASE):
            signals.append("Privacy policy present")

        references = soup.find_all(["cite", "blockquote"])
        if references:
            signals.append(f"References/citations ({len(references)})")

        if re.search(
            r"консультация врача|не является медицинской консультацией",
            text,
            re.IGNORECASE,
        ):
            signals.append("Medical disclaimer present")

        if "schema.org" in html:
            signals.append("Structured data present")

        return signals

    def _generate_recommendations(
        self,
        experience: float,
        expertise: float,
        authoritativeness: float,
        trustworthiness: float,
    ) -> list[str]:
        """Generate recommendations based on scores."""
        recommendations = []

        if experience < 50:
            recommendations.append(
                "Add case studies and patient outcomes to demonstrate experience"
            )
            recommendations.append("Include before/after examples with specific results")

        if expertise < 60:
            recommendations.append(
                "Add author credentials and medical qualifications prominently"
            )
            recommendations.append("Increase medical terminology usage appropriately")
            recommendations.append("Add author bio section with expertise details")

        if authoritativeness < 60:
            recommendations.append(
                "Add citations to authoritative medical sources (PubMed, WHO, etc.)"
            )
            recommendations.append(
                "Mention certifications, licenses, and professional memberships"
            )
            recommendations.append("Add schema.org markup for medical organization")

        if trustworthiness < 60:
            recommendations.append(
                "Update content regularly (20-30% every 6-12 months for medical YMYL)"
            )
            recommendations.append("Display last update date prominently")
            recommendations.append("Add comprehensive contact information")
            recommendations.append("Include privacy policy and medical disclaimer")
            recommendations.append("Add references and citations to support claims")

        return recommendations
