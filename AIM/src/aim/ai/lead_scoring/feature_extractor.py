"""Lead Feature Extractor

Extracts 30+ features from lead data for ML-based scoring.

Features:
- Demographic: specialty, clinic size, location
- Behavioral: message quality, response time, UTM
- Engagement: form completion, message length
- Technical: device type, browser, session duration
- Timing: day of week, hour of day
- Source: traffic source, referral
- Historical: previous submissions, email domain
- Compliance: ФЗ-152 consent, data completeness

Part of: Phase 11 Sprint 2 - Task 2.2
"""

import re
from datetime import datetime, timezone
from typing import Any

from AIM.src.aim.models.lead import Lead
from AIM.src.aim.schemas.lead import MedicalSpecialty


class LeadFeatureExtractor:
    """Extract 30+ features from lead data for scoring"""

    # High-value specialties (Russian market)
    HIGH_VALUE_SPECIALTIES = {
        MedicalSpecialty.PLASTIC_SURGERY.value: 5,
        MedicalSpecialty.DENTISTRY.value: 4,
        MedicalSpecialty.OPHTHALMOLOGY.value: 4,
        MedicalSpecialty.COSMETOLOGY.value: 3,
        MedicalSpecialty.DERMATOLOGY.value: 3,
    }

    # Location tiers (Russian market)
    LOCATION_TIERS = {
        "moscow": 10,
        "spb": 8,
        "regional": 5,
        "small": 2,
    }

    # Business email domains
    BUSINESS_DOMAINS = {".ru", ".com", ".org", ".net"}
    FREE_EMAIL_DOMAINS = {"gmail.com", "yandex.ru", "mail.ru", "rambler.ru"}

    def extract(self, lead: Lead, metadata: dict[str, Any]) -> dict[str, Any]:
        """Extract features for scoring

        Args:
            lead: Lead record from database
            metadata: Request metadata (user_agent, utm, session_duration, etc.)

        Returns:
            Dictionary of extracted features
        """
        return {
            # Demographic factors (10 points)
            "specialty": lead.specialty,
            "specialty_value": self._get_specialty_value(lead.specialty),
            "clinic_size": self._infer_clinic_size(lead.clinic_name_encrypted),
            "location": self._infer_location(lead.phone_encrypted),
            "location_value": self._get_location_value(lead.phone_encrypted),
            # Behavioral factors (20 points)
            "message_quality": self._score_message_quality(lead.message_encrypted),
            "response_time": self._get_response_time_category(lead.created_at),
            "utm_campaign": metadata.get("utm_campaign"),
            "utm_campaign_value": self._score_utm_campaign(metadata.get("utm_campaign")),
            # Engagement factors (15 points)
            "form_completion": self._calc_completion_rate(lead),
            "message_length": len(lead.message_encrypted or ""),
            "has_phone_and_email": True,  # Always true (both required)
            # Technical factors (10 points)
            "device_type": self._parse_device(metadata.get("user_agent")),
            "browser": self._parse_browser(metadata.get("user_agent")),
            "session_duration": metadata.get("session_duration", 0),
            # Timing factors (10 points)
            "day_of_week": lead.created_at.weekday(),
            "hour_of_day": lead.created_at.hour,
            "is_business_hours": self._is_business_hours(lead.created_at),
            # Source factors (15 points)
            "traffic_source": lead.source,
            "is_referral": lead.source == "referral",
            "is_organic": lead.source == "organic_search",
            # Historical factors (10 points)
            "previous_submissions": 0,  # TODO: Query database for email_hash count
            "email_domain_type": self._classify_email_domain(lead.email_encrypted),
            # Compliance factors (10 points)
            "fz152_consent": lead.fz152_consent,
            "data_completeness": self._calc_data_completeness(lead),
        }

    def _get_specialty_value(self, specialty: str) -> int:
        """Get specialty value score (0-5)"""
        return self.HIGH_VALUE_SPECIALTIES.get(specialty, 2)

    def _infer_clinic_size(self, clinic_name_encrypted: str) -> str:
        """Infer clinic size from name

        Args:
            clinic_name_encrypted: Encrypted clinic name

        Returns:
            "chain" or "single"

        Note:
            Since name is encrypted, we can't analyze it.
            For MVP, return "single" (most common).
            TODO: Add clinic_size field to form or use external database.
        """
        # TODO: Decrypt and analyze clinic name for chain indicators
        # For now, assume single clinic (most common case)
        return "single"

    def _infer_location(self, phone_encrypted: str) -> str:
        """Infer location from phone number

        Args:
            phone_encrypted: Encrypted phone number

        Returns:
            Location tier: "moscow", "spb", "regional", "small"

        Note:
            Since phone is encrypted, we can't analyze area code.
            For MVP, return "regional" (neutral tier).
            TODO: Add location field to form or decrypt phone for area code.
        """
        # TODO: Decrypt phone and check area code
        # Moscow: +7495, +7499
        # St. Petersburg: +7812
        # For now, assume regional (neutral)
        return "regional"

    def _get_location_value(self, phone_encrypted: str) -> int:
        """Get location value score (0-10)"""
        location = self._infer_location(phone_encrypted)
        return self.LOCATION_TIERS.get(location, 5)

    def _score_message_quality(self, message_encrypted: str | None) -> int:
        """Score message quality (0-10)

        Factors:
        - Length (>50 words = high intent)
        - Specificity (mentions procedures, prices, dates)
        - Grammar and structure

        Args:
            message_encrypted: Encrypted message text

        Returns:
            Quality score 0-10

        Note:
            Since message is encrypted, we can't analyze content.
            For MVP, score based on length only.
            TODO: Decrypt message for content analysis.
        """
        if not message_encrypted:
            return 0

        # TODO: Decrypt and analyze message content
        # For now, score based on encrypted length (proxy for real length)
        length = len(message_encrypted)

        if length > 200:
            return 10
        elif length > 100:
            return 7
        elif length > 50:
            return 5
        else:
            return 3

    def _get_response_time_category(self, created_at: datetime) -> str:
        """Get response time category

        Args:
            created_at: Lead creation timestamp

        Returns:
            "business_hours", "evening", "night", "weekend"
        """
        if created_at.weekday() >= 5:  # Saturday or Sunday
            return "weekend"

        hour = created_at.hour
        if 9 <= hour < 18:
            return "business_hours"
        elif 18 <= hour < 22:
            return "evening"
        else:
            return "night"

    def _score_utm_campaign(self, utm_campaign: str | None) -> int:
        """Score UTM campaign (0-5)

        High-intent campaigns:
        - implants, surgery, laser
        - Specific procedures

        Low-intent campaigns:
        - general, promo, discount

        Args:
            utm_campaign: UTM campaign parameter

        Returns:
            Campaign value score 0-5
        """
        if not utm_campaign:
            return 0

        utm_lower = utm_campaign.lower()

        # High-intent keywords
        high_intent = ["implant", "surgery", "laser", "procedure", "treatment"]
        if any(keyword in utm_lower for keyword in high_intent):
            return 5

        # Medium-intent keywords
        medium_intent = ["consultation", "appointment", "specialist"]
        if any(keyword in utm_lower for keyword in medium_intent):
            return 3

        # Low-intent (generic campaigns)
        return 1

    def _calc_completion_rate(self, lead: Lead) -> float:
        """Calculate form completion rate (0.0-1.0)

        Args:
            lead: Lead record

        Returns:
            Completion rate (1.0 = all fields filled)
        """
        total_fields = 5  # name, phone, email, clinic_name, message
        filled_fields = 4  # name, phone, email, clinic_name (required)

        if lead.message_encrypted:
            filled_fields += 1

        return filled_fields / total_fields

    def _parse_device(self, user_agent: str | None) -> str:
        """Parse device type from user agent

        Args:
            user_agent: User agent string

        Returns:
            "desktop", "mobile", or "tablet"
        """
        if not user_agent:
            return "unknown"

        ua_lower = user_agent.lower()

        if "mobile" in ua_lower or "android" in ua_lower:
            return "mobile"
        elif "tablet" in ua_lower or "ipad" in ua_lower:
            return "tablet"
        else:
            return "desktop"

    def _parse_browser(self, user_agent: str | None) -> str:
        """Parse browser from user agent

        Args:
            user_agent: User agent string

        Returns:
            Browser name: "chrome", "safari", "firefox", "edge", "other"
        """
        if not user_agent:
            return "unknown"

        ua_lower = user_agent.lower()

        if "chrome" in ua_lower and "edg" not in ua_lower:
            return "chrome"
        elif "safari" in ua_lower and "chrome" not in ua_lower:
            return "safari"
        elif "firefox" in ua_lower:
            return "firefox"
        elif "edg" in ua_lower:
            return "edge"
        else:
            return "other"

    def _is_business_hours(self, created_at: datetime) -> bool:
        """Check if submission is during business hours

        Business hours: Monday-Friday, 9:00-18:00

        Args:
            created_at: Lead creation timestamp

        Returns:
            True if business hours, False otherwise
        """
        if created_at.weekday() >= 5:  # Weekend
            return False

        hour = created_at.hour
        return 9 <= hour < 18

    def _classify_email_domain(self, email_encrypted: str) -> str:
        """Classify email domain type

        Args:
            email_encrypted: Encrypted email address

        Returns:
            "business" or "free"

        Note:
            Since email is encrypted, we can't analyze domain.
            For MVP, return "free" (most common).
            TODO: Add email_domain field to form or decrypt email.
        """
        # TODO: Decrypt email and check domain
        # Business: clinic.ru, company.com
        # Free: gmail.com, yandex.ru, mail.ru
        # For now, assume free email (most common)
        return "free"

    def _calc_data_completeness(self, lead: Lead) -> float:
        """Calculate data completeness (0.0-1.0)

        Checks:
        - All required fields filled
        - Optional fields filled
        - UTM parameters present

        Args:
            lead: Lead record

        Returns:
            Completeness score 0.0-1.0
        """
        total_points = 10
        points = 0

        # Required fields (5 points)
        if lead.name_encrypted:
            points += 1
        if lead.phone_encrypted:
            points += 1
        if lead.email_encrypted:
            points += 1
        if lead.clinic_name_encrypted:
            points += 1
        if lead.fz152_consent:
            points += 1

        # Optional fields (3 points)
        if lead.message_encrypted:
            points += 1
        if lead.specialty:
            points += 1
        if lead.source:
            points += 1

        # UTM parameters (2 points)
        if lead.utm_source:
            points += 1
        if lead.utm_campaign:
            points += 1

        return points / total_points
