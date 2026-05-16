"""
AI Ad Copy Generator

Generates medical ad copy with compliance checking and A/B testing variants.

Part of: Phase 10 - AI Enhancement (Task 2.1)
"""

import asyncio
from typing import Any, List, Dict
from datetime import datetime, timezone

from AIM.src.aim.ai.ads.schemas import (
    AdCopyResult,
    AdCopyVariant,
    ComplianceCheck,
    AdTemplate,
)


class AdCopyGenerator:
    """AI-powered ad copy generator for medical advertising

    Features:
    - 320+ templates for medical specialties
    - Compliance checking (FDA/HIPAA for US, ФЗ-323 for Russia)
    - A/B testing variants generation (3-5 variants)
    - Emotional triggers (urgency, trust, fear, social proof)
    - Platform-specific optimization (Yandex Direct, Google Ads)
    - Cost tracking (~$0.14 per ad set)

    Target: 15%+ CTR improvement over manual copy
    """

    def __init__(
        self,
        llm_client: Any,
        market: str = "russia",
        platform: str = "yandex_direct",
    ):
        """Initialize Ad Copy Generator

        Args:
            llm_client: LLM client for text generation
            market: Target market (russia, usa)
            platform: Ad platform (yandex_direct, google_ads)
        """
        self.llm_client = llm_client
        self.market = market
        self.platform = platform

        # Load templates (stub - will load from JSON in production)
        self.templates = self._load_templates()

        # Compliance rules by market
        self.compliance_rules = self._load_compliance_rules()

    async def generate(
        self,
        specialty: str,
        service: str,
        target_audience: str | None = None,
        emotional_trigger: str | None = None,
        num_variants: int = 3,
    ) -> AdCopyResult:
        """Generate ad copy variants with compliance checking

        Args:
            specialty: Medical specialty (e.g., "Стоматология")
            service: Specific service (e.g., "Имплантация зубов")
            target_audience: Target audience description
            emotional_trigger: Preferred emotional trigger (urgency, trust, fear, social_proof)
            num_variants: Number of variants to generate (3-5)

        Returns:
            AdCopyResult with variants and compliance check
        """
        # Select template
        template = self._select_template(specialty, service, emotional_trigger)

        # Generate variants in parallel
        variant_tasks = [
            self._generate_variant(template, specialty, service, target_audience, i)
            for i in range(num_variants)
        ]

        variants = await asyncio.gather(*variant_tasks)

        # Check compliance for all variants
        compliance = await self._check_compliance(variants, specialty, service)

        # Calculate generation cost (based on LLM tokens)
        generation_cost = self._calculate_cost(num_variants)

        return AdCopyResult(
            specialty=specialty,
            service=service,
            platform=self.platform,
            variants=variants,
            compliance=compliance,
            template_used=template.template_id,
            generation_cost=generation_cost,
        )

    async def _generate_variant(
        self,
        template: AdTemplate,
        specialty: str,
        service: str,
        target_audience: str | None,
        variant_index: int,
    ) -> AdCopyVariant:
        """Generate single ad copy variant

        Args:
            template: Ad template to use
            specialty: Medical specialty
            service: Specific service
            target_audience: Target audience description
            variant_index: Variant index (for diversity)

        Returns:
            AdCopyVariant with headline, description, CTA
        """
        # Build prompt for LLM
        prompt = self._build_generation_prompt(
            template, specialty, service, target_audience, variant_index
        )

        # Generate with LLM
        response = await self.llm_client.generate(
            prompt=prompt,
            max_tokens=200,
            temperature=0.7 + (variant_index * 0.1),  # Increase diversity
        )

        # Parse response
        headline, description, cta = self._parse_llm_response(response.content)

        # Predict CTR (stub - will use ML model in production)
        predicted_ctr = self._predict_ctr(headline, description, cta)

        return AdCopyVariant(
            headline=headline,
            description=description,
            cta=cta,
            emotional_trigger=template.emotional_trigger,
            compliance_score=0.0,  # Will be filled by compliance check
            predicted_ctr=predicted_ctr,
        )

    async def _check_compliance(
        self,
        variants: List[AdCopyVariant],
        specialty: str,
        service: str,
    ) -> ComplianceCheck:
        """Check compliance for all variants

        Args:
            variants: List of ad copy variants
            specialty: Medical specialty
            service: Specific service

        Returns:
            ComplianceCheck with violations and recommendations
        """
        violations = []
        warnings = []
        recommendations = []

        # Get compliance rules for market
        rules = self.compliance_rules.get(self.market, {})

        for variant in variants:
            # Check forbidden words
            forbidden_words = rules.get("forbidden_words", [])
            for word in forbidden_words:
                if word.lower() in variant.headline.lower() or word.lower() in variant.description.lower():
                    violations.append(f"Запрещённое слово: '{word}'")

            # Check required disclaimers
            required_disclaimers = rules.get("required_disclaimers", [])
            for disclaimer in required_disclaimers:
                if disclaimer not in variant.description:
                    warnings.append(f"Рекомендуется добавить: '{disclaimer}'")

            # Check length limits
            if len(variant.headline) > 30:
                violations.append(f"Заголовок слишком длинный: {len(variant.headline)} символов (макс 30)")

            if len(variant.description) > 90:
                violations.append(f"Описание слишком длинное: {len(variant.description)} символов (макс 90)")

        # Generate recommendations
        if self.market == "russia":
            recommendations.append("Добавьте номер лицензии клиники")
            recommendations.append("Укажите юридический адрес")

        # Calculate compliance score
        total_checks = len(variants) * 5  # 5 checks per variant
        failed_checks = len(violations)
        compliance_score = max(0.0, (total_checks - failed_checks) / total_checks * 100)

        # Update variant compliance scores
        for variant in variants:
            variant.compliance_score = compliance_score

        return ComplianceCheck(
            passed=len(violations) == 0,
            score=compliance_score,
            violations=violations,
            warnings=warnings,
            recommendations=recommendations,
        )

    def _select_template(
        self,
        specialty: str,
        service: str,
        emotional_trigger: str | None,
    ) -> AdTemplate:
        """Select best template for specialty/service

        Args:
            specialty: Medical specialty
            service: Specific service
            emotional_trigger: Preferred emotional trigger

        Returns:
            AdTemplate matching criteria
        """
        # Filter templates by specialty and service
        matching = [
            t for t in self.templates
            if t.specialty == specialty and t.service == service
        ]

        # Filter by emotional trigger if specified
        if emotional_trigger:
            matching = [t for t in matching if t.emotional_trigger == emotional_trigger]

        # Return first match or default template
        if matching:
            return matching[0]

        # Default template
        return AdTemplate(
            template_id="default",
            specialty=specialty,
            service=service,
            emotional_trigger=emotional_trigger or "trust",
            headline_template="{service}",
            description_template="{benefit}. {cta_text}.",
            cta_options=["Записаться", "Узнать больше"],
            compliance_notes=[],
        )

    def _build_generation_prompt(
        self,
        template: AdTemplate,
        specialty: str,
        service: str,
        target_audience: str | None,
        variant_index: int,
    ) -> str:
        """Build prompt for LLM generation

        Args:
            template: Ad template
            specialty: Medical specialty
            service: Specific service
            target_audience: Target audience description
            variant_index: Variant index

        Returns:
            Prompt string for LLM
        """
        prompt = f"""Создай рекламное объявление для медицинской услуги.

Специальность: {specialty}
Услуга: {service}
Платформа: {self.platform}
Эмоциональный триггер: {template.emotional_trigger}
"""

        if target_audience:
            prompt += f"Целевая аудитория: {target_audience}\n"

        prompt += f"""
Вариант: {variant_index + 1}

Требования:
- Заголовок: максимум 30 символов
- Описание: максимум 90 символов
- Призыв к действию (CTA): короткий и ясный
- Используй эмоциональный триггер: {template.emotional_trigger}
- Соблюдай медицинскую этику (не обещай гарантированное излечение)

Формат ответа:
ЗАГОЛОВОК: [текст заголовка]
ОПИСАНИЕ: [текст описания]
CTA: [текст призыва к действию]
"""

        return prompt

    def _parse_llm_response(self, content: str) -> tuple[str, str, str]:
        """Parse LLM response into headline, description, CTA

        Args:
            content: LLM response content

        Returns:
            Tuple of (headline, description, cta)
        """
        lines = content.strip().split("\n")

        headline = ""
        description = ""
        cta = ""

        for line in lines:
            if line.startswith("ЗАГОЛОВОК:"):
                headline = line.replace("ЗАГОЛОВОК:", "").strip()
            elif line.startswith("ОПИСАНИЕ:"):
                description = line.replace("ОПИСАНИЕ:", "").strip()
            elif line.startswith("CTA:"):
                cta = line.replace("CTA:", "").strip()

        # Fallback if parsing failed
        if not headline:
            headline = "Медицинские услуги"
        if not description:
            description = "Качественное лечение. Запишитесь на консультацию."
        if not cta:
            cta = "Записаться"

        return headline, description, cta

    def _predict_ctr(self, headline: str, description: str, cta: str) -> float:
        """Predict CTR for ad copy (stub)

        Args:
            headline: Ad headline
            description: Ad description
            cta: Call-to-action

        Returns:
            Predicted CTR in percent (0-100)
        """
        # Stub: simple heuristic based on length and keywords
        score = 2.0  # Base CTR

        # Bonus for optimal length
        if 20 <= len(headline) <= 30:
            score += 0.5
        if 70 <= len(description) <= 90:
            score += 0.5

        # Bonus for action words in CTA
        action_words = ["записаться", "узнать", "получить", "позвонить"]
        if any(word in cta.lower() for word in action_words):
            score += 0.3

        # Bonus for numbers in headline
        if any(char.isdigit() for char in headline):
            score += 0.2

        return min(score, 10.0)  # Cap at 10%

    def _calculate_cost(self, num_variants: int) -> float:
        """Calculate generation cost

        Args:
            num_variants: Number of variants generated

        Returns:
            Cost in USD
        """
        # Stub: $0.14 per ad set (3-5 variants)
        return 0.14

    def _load_templates(self) -> List[AdTemplate]:
        """Load ad templates (stub)

        Returns:
            List of AdTemplate objects
        """
        # Stub: return sample templates
        # In production, load from JSON file with 320+ templates
        return [
            AdTemplate(
                template_id="dental_implants_urgency",
                specialty="Стоматология",
                service="Имплантация зубов",
                emotional_trigger="urgency",
                headline_template="{service} за {timeframe}",
                description_template="{benefit}. {guarantee}. {cta_text}.",
                cta_options=["Записаться", "Узнать цену"],
                compliance_notes=["Указать номер лицензии"],
            ),
            AdTemplate(
                template_id="dental_implants_trust",
                specialty="Стоматология",
                service="Имплантация зубов",
                emotional_trigger="trust",
                headline_template="{service} от {experience}",
                description_template="{credentials}. {guarantee}. {cta_text}.",
                cta_options=["Записаться на консультацию"],
                compliance_notes=["Указать сертификаты врачей"],
            ),
        ]

    def _load_compliance_rules(self) -> Dict[str, Any]:
        """Load compliance rules by market

        Returns:
            Dict of compliance rules by market
        """
        return {
            "russia": {
                "forbidden_words": [
                    "лучший",
                    "гарантированное излечение",
                    "100% результат",
                    "чудо",
                ],
                "required_disclaimers": [
                    "Имеются противопоказания",
                    "Необходима консультация специалиста",
                ],
            },
            "usa": {
                "forbidden_words": [
                    "cure",
                    "guaranteed",
                    "miracle",
                ],
                "required_disclaimers": [
                    "Results may vary",
                    "Consult your physician",
                ],
            },
        }

    async def close(self):
        """Close resources"""
        # No resources to close for now
        pass


async def generate_ad_copy(
    specialty: str,
    service: str,
    llm_client: Any,
    market: str = "russia",
    platform: str = "yandex_direct",
    target_audience: str | None = None,
    emotional_trigger: str | None = None,
    num_variants: int = 3,
) -> AdCopyResult:
    """Convenience function to generate ad copy

    Args:
        specialty: Medical specialty
        service: Specific service
        llm_client: LLM client
        market: Target market (russia, usa)
        platform: Ad platform (yandex_direct, google_ads)
        target_audience: Target audience description
        emotional_trigger: Preferred emotional trigger
        num_variants: Number of variants (3-5)

    Returns:
        AdCopyResult with variants and compliance check
    """
    generator = AdCopyGenerator(
        llm_client=llm_client,
        market=market,
        platform=platform,
    )

    try:
        result = await generator.generate(
            specialty=specialty,
            service=service,
            target_audience=target_audience,
            emotional_trigger=emotional_trigger,
            num_variants=num_variants,
        )
        return result
    finally:
        await generator.close()
