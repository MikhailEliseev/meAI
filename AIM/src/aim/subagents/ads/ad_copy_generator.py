"""
Ad Copy Generator - Automated Ad Copy Creation.

Generates high-converting ad copy for Yandex Direct and Google Ads
with A/B testing variants and compliance checking.

Based on: Best practices for ad copywriting
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import structlog
from langchain_openai import ChatOpenAI


@dataclass
class AdHeadline:
    """Ad headline variant."""

    text: str
    length: int
    variant_type: str  # benefit, question, urgency, social_proof


@dataclass
class AdDescription:
    """Ad description variant."""

    text: str
    length: int
    includes_cta: bool
    cta_text: str | None


@dataclass
class CallToAction:
    """Call-to-action suggestion."""

    text: str
    urgency_level: str  # high, medium, low
    action_type: str  # buy, learn, contact, download


@dataclass
class ComplianceCheck:
    """Compliance check result."""

    platform: str  # yandex, google
    is_compliant: bool
    violations: list[str]
    warnings: list[str]


@dataclass
class AdCopyVariant:
    """Complete ad copy variant."""

    variant_id: int
    headline: str
    description: str
    cta: str
    platform: str
    compliance: ComplianceCheck


@dataclass
class AdCopySet:
    """Complete set of ad copy variants."""

    target_keyword: str
    timestamp: str

    # Variants
    variants: list[AdCopyVariant]
    total_variants: int

    # Headlines
    headlines: list[AdHeadline]
    total_headlines: int

    # Descriptions
    descriptions: list[AdDescription]
    total_descriptions: int

    # CTAs
    ctas: list[CallToAction]
    total_ctas: int

    # Platform-specific
    yandex_variants: list[AdCopyVariant]
    google_variants: list[AdCopyVariant]


class AdCopyGenerator:
    """
    Ad Copy Generator.

    Generates high-converting ad copy for Yandex Direct and Google Ads
    with A/B testing variants and compliance checking.
    """

    def __init__(self):
        """Initialize Ad Copy Generator."""
        self.logger = structlog.get_logger()

        # Platform limits
        self.limits = {
            "yandex": {
                "headline_max": 56,
                "description_max": 81,
            },
            "google": {
                "headline_max": 30,
                "description_max": 90,
            },
        }

        # Forbidden words (Yandex/Google policies)
        # Note: "гарантия" removed - it's allowed when used correctly
        self.forbidden_words = [
            "лучший",
            "самый",
            "номер 1",
            "100%",
            "бесплатно",
            "даром",
        ]

    async def generate(
        self,
        target_keyword: str,
        product_name: str,
        benefits: list[str],
        platform: str = "both",  # yandex, google, both
    ) -> AdCopySet:
        """
        Generate ad copy set.

        Args:
            target_keyword: Target keyword for ads
            product_name: Product/service name
            benefits: List of product benefits
            platform: Target platform (yandex, google, both)

        Returns:
            Complete ad copy set with variants
        """
        self.logger.info(
            "ad_copy_generation_start",
            keyword=target_keyword,
            platform=platform,
        )

        # Step 1: Generate headlines
        headlines = self._generate_headlines(
            target_keyword,
            product_name,
            benefits,
        )

        # Step 2: Generate descriptions
        descriptions = self._generate_descriptions(
            target_keyword,
            product_name,
            benefits,
        )

        # Step 3: Generate CTAs
        ctas = self._generate_ctas()

        # Step 4: Create variants
        variants = self._create_variants(
            headlines,
            descriptions,
            ctas,
            platform,
        )

        # Step 5: Check compliance
        for variant in variants:
            variant.compliance = self._check_compliance(
                variant.headline,
                variant.description,
                variant.platform,
            )

        # Step 6: Filter by platform
        yandex_variants = [v for v in variants if v.platform == "yandex"]
        google_variants = [v for v in variants if v.platform == "google"]

        ad_copy_set = AdCopySet(
            target_keyword=target_keyword,
            timestamp=datetime.now().isoformat(),
            variants=variants,
            total_variants=len(variants),
            headlines=headlines,
            total_headlines=len(headlines),
            descriptions=descriptions,
            total_descriptions=len(descriptions),
            ctas=ctas,
            total_ctas=len(ctas),
            yandex_variants=yandex_variants,
            google_variants=google_variants,
        )

        self.logger.info(
            "ad_copy_generation_complete",
            total_variants=len(variants),
            yandex_variants=len(yandex_variants),
            google_variants=len(google_variants),
        )

        return ad_copy_set

    def _generate_headlines(
        self,
        keyword: str,
        product: str,
        benefits: list[str],
    ) -> list[AdHeadline]:
        """Generate headline variants."""
        headlines = []

        # Benefit-focused headlines
        if benefits:
            for benefit in benefits[:2]:  # Top 2 benefits
                text = f"{product}: {benefit}"
                if len(text) <= 56:  # Yandex limit
                    headlines.append(
                        AdHeadline(
                            text=text,
                            length=len(text),
                            variant_type="benefit",
                        )
                    )

        # Question headlines
        questions = [
            f"Ищете {keyword}?",
            f"Нужен {keyword}?",
            f"Где купить {keyword}?",
        ]
        for question in questions:
            if len(question) <= 56:
                headlines.append(
                    AdHeadline(
                        text=question,
                        length=len(question),
                        variant_type="question",
                    )
                )

        # Urgency headlines
        urgency = [
            f"{product} - Закажите сегодня",
            f"{product} - Акция до конца месяца",
        ]
        for text in urgency:
            if len(text) <= 56:
                headlines.append(
                    AdHeadline(
                        text=text,
                        length=len(text),
                        variant_type="urgency",
                    )
                )

        # Social proof headlines
        social_proof = [
            f"{product} - 1000+ клиентов",
            f"{product} - Проверено временем",
        ]
        for text in social_proof:
            if len(text) <= 56:
                headlines.append(
                    AdHeadline(
                        text=text,
                        length=len(text),
                        variant_type="social_proof",
                    )
                )

        return headlines[:8]  # Top 8 headlines

    def _generate_descriptions(
        self,
        keyword: str,
        product: str,
        benefits: list[str],
    ) -> list[AdDescription]:
        """Generate description variants."""
        descriptions = []

        # Benefit-focused descriptions
        if benefits:
            benefit_text = ". ".join(benefits[:2])
            text = f"{benefit_text}. Узнайте больше на сайте."
            if len(text) <= 81:  # Yandex limit
                descriptions.append(
                    AdDescription(
                        text=text,
                        length=len(text),
                        includes_cta=True,
                        cta_text="Узнайте больше",
                    )
                )

        # Feature-focused descriptions
        feature_text = f"{product} для {keyword}. Быстрая доставка. Гарантия качества."
        if len(feature_text) <= 81:
            descriptions.append(
                AdDescription(
                    text=feature_text,
                    length=len(feature_text),
                    includes_cta=False,
                    cta_text=None,
                )
            )

        # Urgency descriptions
        urgency_text = f"Специальное предложение на {keyword}. Закажите сегодня!"
        if len(urgency_text) <= 81:
            descriptions.append(
                AdDescription(
                    text=urgency_text,
                    length=len(urgency_text),
                    includes_cta=True,
                    cta_text="Закажите сегодня",
                )
            )

        # Trust descriptions
        trust_text = f"{product} - надёжное решение для {keyword}. Работаем с 2010 года."
        if len(trust_text) <= 81:
            descriptions.append(
                AdDescription(
                    text=trust_text,
                    length=len(trust_text),
                    includes_cta=False,
                    cta_text=None,
                )
            )

        return descriptions[:6]  # Top 6 descriptions

    def _generate_ctas(self) -> list[CallToAction]:
        """Generate CTA suggestions."""
        ctas = [
            CallToAction(
                text="Заказать сейчас",
                urgency_level="high",
                action_type="buy",
            ),
            CallToAction(
                text="Узнать больше",
                urgency_level="low",
                action_type="learn",
            ),
            CallToAction(
                text="Получить консультацию",
                urgency_level="medium",
                action_type="contact",
            ),
            CallToAction(
                text="Скачать каталог",
                urgency_level="low",
                action_type="download",
            ),
            CallToAction(
                text="Оставить заявку",
                urgency_level="medium",
                action_type="contact",
            ),
        ]

        return ctas

    def _create_variants(
        self,
        headlines: list[AdHeadline],
        descriptions: list[AdDescription],
        ctas: list[CallToAction],
        platform: str,
    ) -> list[AdCopyVariant]:
        """Create ad copy variants."""
        variants = []
        variant_id = 1

        # Determine platforms
        platforms = []
        if platform == "both":
            platforms = ["yandex", "google"]
        else:
            platforms = [platform]

        # Create variants (top 3 headlines x top 2 descriptions)
        for headline in headlines[:3]:
            for description in descriptions[:2]:
                for plat in platforms:
                    # Check length limits
                    limits = self.limits[plat]
                    if (
                        headline.length <= limits["headline_max"]
                        and description.length <= limits["description_max"]
                    ):
                        # Select CTA
                        cta = ctas[0] if ctas else CallToAction(
                            text="Узнать больше",
                            urgency_level="low",
                            action_type="learn",
                        )

                        variants.append(
                            AdCopyVariant(
                                variant_id=variant_id,
                                headline=headline.text,
                                description=description.text,
                                cta=cta.text,
                                platform=plat,
                                compliance=ComplianceCheck(
                                    platform=plat,
                                    is_compliant=True,
                                    violations=[],
                                    warnings=[],
                                ),
                            )
                        )
                        variant_id += 1

        return variants

    def _check_compliance(
        self,
        headline: str,
        description: str,
        platform: str,
    ) -> ComplianceCheck:
        """Check compliance with platform policies."""
        violations = []
        warnings = []

        # Check forbidden words
        text = f"{headline} {description}".lower()
        for word in self.forbidden_words:
            if word in text:
                violations.append(f"Запрещённое слово: '{word}'")

        # Check length limits
        limits = self.limits[platform]
        if len(headline) > limits["headline_max"]:
            violations.append(
                f"Заголовок превышает лимит: {len(headline)} > {limits['headline_max']}"
            )

        if len(description) > limits["description_max"]:
            violations.append(
                f"Описание превышает лимит: {len(description)} > {limits['description_max']}"
            )

        # Check capitalization (warning)
        if headline.isupper():
            warnings.append("Заголовок полностью в верхнем регистре")

        # Check exclamation marks (warning)
        if text.count("!") > 1:
            warnings.append("Слишком много восклицательных знаков")

        is_compliant = len(violations) == 0

        return ComplianceCheck(
            platform=platform,
            is_compliant=is_compliant,
            violations=violations,
            warnings=warnings,
        )


async def main():
    """Example usage."""
    generator = AdCopyGenerator()

    ad_copy_set = await generator.generate(
        target_keyword="зубные имплантаты",
        product_name="Имплантаты Nobel Biocare",
        benefits=[
            "Пожизненная гарантия",
            "Установка за 1 день",
            "Безболезненная процедура",
        ],
        platform="both",
    )

    print(f"Target Keyword: {ad_copy_set.target_keyword}")
    print(f"Total Variants: {ad_copy_set.total_variants}")
    print(f"Yandex Variants: {len(ad_copy_set.yandex_variants)}")
    print(f"Google Variants: {len(ad_copy_set.google_variants)}")
    print()

    print("Sample Variants:")
    for variant in ad_copy_set.variants[:3]:
        print(f"\nVariant #{variant.variant_id} ({variant.platform}):")
        print(f"  Headline: {variant.headline}")
        print(f"  Description: {variant.description}")
        print(f"  CTA: {variant.cta}")
        print(f"  Compliant: {variant.compliance.is_compliant}")
        if variant.compliance.violations:
            print(f"  Violations: {variant.compliance.violations}")


if __name__ == "__main__":
    asyncio.run(main())


# ==============================================================================
# Added by Teacher Agent: ad-copy
# ==============================================================================

import asyncio

async def generate_hashtags(
    product: str,
    description: str,
    target_audience: str,
    platform: str,
    tone: str,
    llm: ChatOpenAI | None = None,
) -> list[str]:
    """
    Generate hashtags for the given platform.

    Returns empty list for platforms that don't use hashtags (google, facebook).
    """
    spec = get_spec(platform)

    # Platforms that don't use hashtags
    if spec.hashtag_max == 0:
        return []

    # Use midpoint of allowed range as target count
    target_count = (spec.hashtag_min + spec.hashtag_max) // 2
    target_count = max(target_count, spec.hashtag_min)

    chain = build_hashtag_chain(llm)
    result = await chain.ainvoke(
        {
            "product": product,
            "description": description,
            "target_audience": target_audience,
            "platform_name": spec.name,
            "tone": tone,
            "hashtag_count": target_count,
        }
    )

    hashtags = result.get("hashtags", [])

    # Enforce platform limits
    hashtags = hashtags[: spec.hashtag_max]

    return hashtags

# ==============================================================================
# Added by Teacher Agent: ad-copy
# ==============================================================================

import asyncio

async def generate_hashtags(
    product: str,
    description: str,
    target_audience: str,
    platform: str,
    tone: str,
    llm: ChatOpenAI | None = None,
) -> list[str]:
    """
    Generate hashtags for the given platform.

    Returns empty list for platforms that don't use hashtags (google, facebook).
    """
    spec = get_spec(platform)

    # Platforms that don't use hashtags
    if spec.hashtag_max == 0:
        return []

    # Use midpoint of allowed range as target count
    target_count = (spec.hashtag_min + spec.hashtag_max) // 2
    target_count = max(target_count, spec.hashtag_min)

    chain = build_hashtag_chain(llm)
    result = await chain.ainvoke(
        {
            "product": product,
            "description": description,
            "target_audience": target_audience,
            "platform_name": spec.name,
            "tone": tone,
            "hashtag_count": target_count,
        }
    )

    hashtags = result.get("hashtags", [])

    # Enforce platform limits
    hashtags = hashtags[: spec.hashtag_max]

    return hashtags

# ==============================================================================
# Added by Teacher Agent: ad-copy
# ==============================================================================

import asyncio

async def generate_hashtags(
    product: str,
    description: str,
    target_audience: str,
    platform: str,
    tone: str,
    llm: ChatOpenAI | None = None,
) -> list[str]:
    """
    Generate hashtags for the given platform.

    Returns empty list for platforms that don't use hashtags (google, facebook).
    """
    spec = get_spec(platform)

    # Platforms that don't use hashtags
    if spec.hashtag_max == 0:
        return []

    # Use midpoint of allowed range as target count
    target_count = (spec.hashtag_min + spec.hashtag_max) // 2
    target_count = max(target_count, spec.hashtag_min)

    chain = build_hashtag_chain(llm)
    result = await chain.ainvoke(
        {
            "product": product,
            "description": description,
            "target_audience": target_audience,
            "platform_name": spec.name,
            "tone": tone,
            "hashtag_count": target_count,
        }
    )

    hashtags = result.get("hashtags", [])

    # Enforce platform limits
    hashtags = hashtags[: spec.hashtag_max]

    return hashtags