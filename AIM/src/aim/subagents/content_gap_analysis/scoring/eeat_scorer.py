"""
E-E-A-T Scorer for Medical Content

Calculates E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness)
scores for medical content based on Google's YMYL guidelines.
"""

from typing import Optional

from ..schemas import ScrapedPageData, EEATScores


class EEATScorer:
    """E-E-A-T scorer for medical content

    Weights (total = 1.0):
    - Experience: 0.3 (author credentials, first-hand experience)
    - Expertise: 0.3 (medical citations, depth of content)
    - Authoritativeness: 0.2 (domain authority, backlinks)
    - Trustworthiness: 0.2 (HTTPS, contact info, privacy policy)
    """

    # Weights for E-E-A-T components
    EXPERIENCE_WEIGHT = 0.3
    EXPERTISE_WEIGHT = 0.3
    AUTHORITATIVENESS_WEIGHT = 0.2
    TRUSTWORTHINESS_WEIGHT = 0.2

    # Thresholds
    MIN_WORD_COUNT_FOR_DEPTH = 1000  # Minimum words for "deep" content
    OPTIMAL_WORD_COUNT = 2000  # Optimal word count for medical content
    MIN_CITATIONS_FOR_EXPERTISE = 3  # Minimum citations for high expertise
    OPTIMAL_CITATIONS = 8  # Optimal number of citations

    def calculate_eeat_score(
        self,
        page: ScrapedPageData,
        domain_authority: Optional[float] = None,
        backlinks_count: Optional[int] = None,
    ) -> EEATScores:
        """Calculate E-E-A-T score for a page

        Args:
            page: Scraped page data
            domain_authority: Domain authority (0.0-1.0), optional
            backlinks_count: Number of backlinks, optional

        Returns:
            EEATScores with component scores and total
        """
        experience = self._calculate_experience_score(page)
        expertise = self._calculate_expertise_score(page)
        authoritativeness = self._calculate_authoritativeness_score(
            page, domain_authority, backlinks_count
        )
        trustworthiness = self._calculate_trustworthiness_score(page)

        total = (
            experience * self.EXPERIENCE_WEIGHT
            + expertise * self.EXPERTISE_WEIGHT
            + authoritativeness * self.AUTHORITATIVENESS_WEIGHT
            + trustworthiness * self.TRUSTWORTHINESS_WEIGHT
        )

        return EEATScores(
            experience=experience,
            expertise=expertise,
            authoritativeness=authoritativeness,
            trustworthiness=trustworthiness,
            total=total,
        )

    def _calculate_experience_score(self, page: ScrapedPageData) -> float:
        """Calculate Experience score (0.0-1.0)

        Factors:
        - Doctor-authored content (0.6 weight)
        - Author credentials present (0.3 weight)
        - First-person language indicators (0.1 weight)
        """
        score = 0.0

        # Doctor-authored (highest weight for medical content)
        if page.is_doctor_authored:
            score += 0.6
        elif page.author_credentials:
            # Has credentials but not doctor (e.g., RN, NP)
            score += 0.3

        # Author name present
        if page.author_name:
            score += 0.3

        # First-person language (indicates personal experience)
        if page.body_text:
            first_person_indicators = ["I have", "In my experience", "I've seen", "my patients"]
            text_lower = page.body_text.lower()
            if any(indicator in text_lower for indicator in first_person_indicators):
                score += 0.1

        return min(score, 1.0)

    def _calculate_expertise_score(self, page: ScrapedPageData) -> float:
        """Calculate Expertise score (0.0-1.0)

        Factors:
        - Medical citations (0.5 weight)
        - Content depth (word count) (0.3 weight)
        - Technical terminology (0.2 weight)
        """
        score = 0.0

        # Medical citations (PubMed, journals)
        if page.medical_citations_count > 0:
            # Normalize: 0 citations = 0.0, optimal citations = 1.0
            citation_score = min(
                page.medical_citations_count / self.OPTIMAL_CITATIONS, 1.0
            )
            score += citation_score * 0.5

        # Content depth (word count)
        if page.word_count:
            if page.word_count >= self.OPTIMAL_WORD_COUNT:
                depth_score = 1.0
            elif page.word_count >= self.MIN_WORD_COUNT_FOR_DEPTH:
                # Linear scale between min and optimal
                depth_score = (
                    page.word_count - self.MIN_WORD_COUNT_FOR_DEPTH
                ) / (self.OPTIMAL_WORD_COUNT - self.MIN_WORD_COUNT_FOR_DEPTH)
            else:
                # Below minimum = low score
                depth_score = page.word_count / self.MIN_WORD_COUNT_FOR_DEPTH * 0.5

            score += depth_score * 0.3

        # Technical terminology (medical terms)
        if page.body_text:
            medical_terms = [
                "diagnosis", "treatment", "procedure", "symptoms", "condition",
                "therapy", "clinical", "medical", "patient", "disease"
            ]
            text_lower = page.body_text.lower()
            term_count = sum(1 for term in medical_terms if term in text_lower)
            # Normalize: 0 terms = 0.0, 5+ terms = 1.0
            terminology_score = min(term_count / 5.0, 1.0)
            score += terminology_score * 0.2

        return min(score, 1.0)

    def _calculate_authoritativeness_score(
        self,
        page: ScrapedPageData,
        domain_authority: Optional[float] = None,
        backlinks_count: Optional[int] = None,
    ) -> float:
        """Calculate Authoritativeness score (0.0-1.0)

        Factors:
        - Domain authority (0.5 weight)
        - Backlinks count (0.3 weight)
        - Content freshness (0.2 weight)
        """
        score = 0.0

        # Domain authority (from API or estimate)
        if domain_authority is not None:
            score += domain_authority * 0.5
        else:
            # Estimate based on domain characteristics
            # Medical/educational domains (.edu, .gov, .org) get higher score
            if any(tld in page.domain for tld in [".edu", ".gov", ".org"]):
                score += 0.4
            else:
                score += 0.2  # Default for commercial domains

        # Backlinks count
        if backlinks_count is not None:
            # Normalize: 0 backlinks = 0.0, 100+ backlinks = 1.0
            backlinks_score = min(backlinks_count / 100.0, 1.0)
            score += backlinks_score * 0.3
        else:
            # No backlinks data = neutral score
            score += 0.15

        # Content freshness (placeholder - would need last_updated date)
        # For now, give neutral score
        score += 0.1

        return min(score, 1.0)

    def _calculate_trustworthiness_score(self, page: ScrapedPageData) -> float:
        """Calculate Trustworthiness score (0.0-1.0)

        Factors:
        - HTTPS (0.3 weight)
        - Contact information (0.3 weight)
        - Privacy policy (0.2 weight)
        - Professional design (0.2 weight)
        """
        score = 0.0

        # HTTPS (security)
        if page.has_https:
            score += 0.3

        # Contact information
        if page.has_contact_info:
            score += 0.3

        # Privacy policy
        if page.has_privacy_policy:
            score += 0.2

        # Professional design (estimate from content structure)
        if page.h1 and page.h2_list and len(page.h2_list) >= 3:
            # Well-structured content = professional design
            score += 0.2

        return min(score, 1.0)

    def classify_quality_tier(self, eeat_score: float) -> str:
        """Classify E-E-A-T score into quality tier

        Args:
            eeat_score: Total E-E-A-T score (0.0-1.0)

        Returns:
            Quality tier: "excellent", "good", "fair", "poor"
        """
        if eeat_score >= 0.8:
            return "excellent"
        elif eeat_score >= 0.6:
            return "good"
        elif eeat_score >= 0.4:
            return "fair"
        else:
            return "poor"

    def get_improvement_recommendations(
        self, page: ScrapedPageData, scores: EEATScores
    ) -> list[str]:
        """Get recommendations to improve E-E-A-T score

        Args:
            page: Scraped page data
            scores: Current E-E-A-T scores

        Returns:
            List of improvement recommendations
        """
        recommendations = []

        # Experience improvements
        if scores.experience < 0.6:
            if not page.is_doctor_authored:
                recommendations.append(
                    "Add doctor author with verified credentials (DDS, DMD, MD)"
                )
            if not page.author_name:
                recommendations.append("Add author byline with credentials")

        # Expertise improvements
        if scores.expertise < 0.6:
            if page.medical_citations_count < self.MIN_CITATIONS_FOR_EXPERTISE:
                recommendations.append(
                    f"Add medical citations (target: {self.OPTIMAL_CITATIONS} citations from PubMed/journals)"
                )
            if page.word_count and page.word_count < self.MIN_WORD_COUNT_FOR_DEPTH:
                recommendations.append(
                    f"Increase content depth (target: {self.OPTIMAL_WORD_COUNT}+ words)"
                )

        # Authoritativeness improvements
        if scores.authoritativeness < 0.6:
            recommendations.append("Build backlinks from authoritative medical sites")
            recommendations.append("Update content regularly to maintain freshness")

        # Trustworthiness improvements
        if scores.trustworthiness < 0.6:
            if not page.has_https:
                recommendations.append("Enable HTTPS for security")
            if not page.has_contact_info:
                recommendations.append("Add contact information (phone, email, address)")
            if not page.has_privacy_policy:
                recommendations.append("Add privacy policy link")

        return recommendations
