"""
NLP Extractor

Extracts structured information from text using spaCy NLP.
"""

from typing import Dict, Any, Optional, List
import re
import structlog
import spacy
from spacy.matcher import Matcher

logger = structlog.get_logger()


class NLPExtractor:
    """
    NLP-based information extractor

    Extracts practice information, analytics access, and ad accounts
    from document text using spaCy NLP and pattern matching.
    """

    def __init__(self, model: str = "en_core_web_sm"):
        """
        Initialize NLP extractor

        Args:
            model: spaCy model name (default: en_core_web_sm)
        """
        try:
            self.nlp = spacy.load(model)
        except OSError:
            # Model not installed, use blank model
            logger.warning("spacy_model_not_found", model=model, fallback="blank")
            self.nlp = spacy.blank("en")

        self.matcher = Matcher(self.nlp.vocab)
        self._setup_patterns()
        self.logger = logger.bind(service="nlp_extractor")

    def _setup_patterns(self) -> None:
        """Setup extraction patterns"""
        # Email pattern
        self.matcher.add("EMAIL", [[{"LIKE_EMAIL": True}]])

        # Phone pattern
        self.matcher.add("PHONE", [
            [{"TEXT": {"REGEX": r"\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}"}}]
        ])

        # Website pattern
        self.matcher.add("WEBSITE", [
            [{"TEXT": {"REGEX": r"https?://[^\s]+"}}],
            [{"TEXT": {"REGEX": r"www\.[^\s]+"}}],
        ])

    async def extract_practice_info(
        self,
        text: str,
    ) -> Dict[str, Any]:
        """
        Extract practice information

        Args:
            text: Document text

        Returns:
            Practice information with confidence scores
        """
        doc = self.nlp(text)

        # Extract entities
        practice_name = None
        location = None
        specialty = None

        for ent in doc.ents:
            if ent.label_ == "ORG" and not practice_name:
                # First organization is likely practice name
                practice_name = ent.text
            elif ent.label_ in ["GPE", "LOC"] and not location:
                # First location
                location = ent.text

        # Extract specialty (pattern matching)
        specialties = [
            "dental", "dentistry", "orthodontics", "periodontics",
            "endodontics", "prosthodontics", "oral surgery",
            "pediatric dentistry", "cosmetic dentistry",
        ]

        text_lower = text.lower()
        for spec in specialties:
            if spec in text_lower:
                specialty = spec.title()
                break

        # Extract contact info using matcher
        matches = self.matcher(doc)
        emails = []
        phones = []
        websites = []

        for match_id, start, end in matches:
            span = doc[start:end]
            match_type = self.nlp.vocab.strings[match_id]

            if match_type == "EMAIL":
                emails.append(span.text)
            elif match_type == "PHONE":
                phones.append(span.text)
            elif match_type == "WEBSITE":
                websites.append(span.text)

        # Calculate confidence
        confidence = 0.0
        if practice_name:
            confidence += 0.3
        if location:
            confidence += 0.2
        if specialty:
            confidence += 0.2
        if emails:
            confidence += 0.15
        if phones:
            confidence += 0.15

        result = {
            "practice_name": practice_name,
            "location": location,
            "specialty": specialty,
            "emails": list(set(emails)),
            "phones": list(set(phones)),
            "websites": list(set(websites)),
            "confidence": min(confidence, 1.0),
        }

        self.logger.info(
            "practice_info_extracted",
            practice_name=practice_name,
            confidence=result["confidence"],
        )

        return result

    async def extract_analytics_access(
        self,
        text: str,
    ) -> Dict[str, Any]:
        """
        Extract analytics access information

        Args:
            text: Document text

        Returns:
            Analytics access info with confidence
        """
        text_lower = text.lower()

        # Google Analytics patterns
        ga_patterns = [
            r"UA-\d{4,10}-\d{1,4}",  # Universal Analytics
            r"G-[A-Z0-9]{10}",  # GA4
            r"google analytics.*?(\S+@\S+)",  # Email with GA mention
        ]

        ga_ids = []
        ga_emails = []

        for pattern in ga_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if "UA-" in pattern or "G-" in pattern:
                ga_ids.extend(matches)
            else:
                ga_emails.extend(matches)

        # Yandex Metrica patterns
        ym_patterns = [
            r"metrica.*?(\d{8})",  # Metrica ID
            r"yandex.*?metrica.*?(\S+@\S+)",  # Email with Metrica mention
        ]

        ym_ids = []
        ym_emails = []

        for pattern in ym_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if r"\d{8}" in pattern:
                ym_ids.extend(matches)
            else:
                ym_emails.extend(matches)

        # Calculate confidence
        confidence = 0.0
        if ga_ids:
            confidence += 0.4
        if ga_emails:
            confidence += 0.2
        if ym_ids:
            confidence += 0.3
        if ym_emails:
            confidence += 0.1

        result = {
            "google_analytics": {
                "property_ids": list(set(ga_ids)),
                "access_emails": list(set(ga_emails)),
            },
            "yandex_metrica": {
                "counter_ids": list(set(ym_ids)),
                "access_emails": list(set(ym_emails)),
            },
            "confidence": min(confidence, 1.0),
        }

        self.logger.info(
            "analytics_access_extracted",
            ga_ids_count=len(ga_ids),
            ym_ids_count=len(ym_ids),
            confidence=result["confidence"],
        )

        return result

    async def extract_ad_accounts(
        self,
        text: str,
    ) -> Dict[str, Any]:
        """
        Extract ad account information

        Args:
            text: Document text

        Returns:
            Ad account info with confidence
        """
        text_lower = text.lower()

        # Google Ads patterns
        google_ads_patterns = [
            r"(\d{3}-\d{3}-\d{4})",  # Google Ads ID format
            r"google ads.*?(\S+@\S+)",  # Email with Google Ads mention
            r"adwords.*?(\S+@\S+)",  # Email with AdWords mention
        ]

        google_ads_ids = []
        google_ads_emails = []

        for pattern in google_ads_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if r"\d{3}-\d{3}-\d{4}" in pattern:
                google_ads_ids.extend(matches)
            else:
                google_ads_emails.extend(matches)

        # Yandex Direct patterns
        yandex_direct_patterns = [
            r"direct.*?(\d{8,10})",  # Direct client ID
            r"yandex.*?direct.*?(\S+@\S+)",  # Email with Direct mention
        ]

        yandex_direct_ids = []
        yandex_direct_emails = []

        for pattern in yandex_direct_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if r"\d{8,10}" in pattern:
                yandex_direct_ids.extend(matches)
            else:
                yandex_direct_emails.extend(matches)

        # Calculate confidence
        confidence = 0.0
        if google_ads_ids:
            confidence += 0.4
        if google_ads_emails:
            confidence += 0.2
        if yandex_direct_ids:
            confidence += 0.3
        if yandex_direct_emails:
            confidence += 0.1

        result = {
            "google_ads": {
                "account_ids": list(set(google_ads_ids)),
                "access_emails": list(set(google_ads_emails)),
            },
            "yandex_direct": {
                "client_ids": list(set(yandex_direct_ids)),
                "access_emails": list(set(yandex_direct_emails)),
            },
            "confidence": min(confidence, 1.0),
        }

        self.logger.info(
            "ad_accounts_extracted",
            google_ads_count=len(google_ads_ids),
            yandex_direct_count=len(yandex_direct_ids),
            confidence=result["confidence"],
        )

        return result

    async def extract_all(
        self,
        text: str,
    ) -> Dict[str, Any]:
        """
        Extract all information from text

        Args:
            text: Document text

        Returns:
            Complete extraction results
        """
        practice_info = await self.extract_practice_info(text)
        analytics_access = await self.extract_analytics_access(text)
        ad_accounts = await self.extract_ad_accounts(text)

        # Calculate overall confidence
        overall_confidence = (
            practice_info["confidence"] * 0.4 +
            analytics_access["confidence"] * 0.3 +
            ad_accounts["confidence"] * 0.3
        )

        result = {
            "practice_info": practice_info,
            "analytics_access": analytics_access,
            "ad_accounts": ad_accounts,
            "overall_confidence": overall_confidence,
        }

        self.logger.info(
            "extraction_complete",
            overall_confidence=overall_confidence,
        )

        return result
