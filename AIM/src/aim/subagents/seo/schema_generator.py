"""
Schema Markup Generator - Structured Data Generation.

Generates Schema.org markup (JSON-LD) for different content types:
Organization, LocalBusiness, Product, Article, FAQ, HowTo, BreadcrumbList.

Based on: Schema.org vocabulary + Google Rich Results guidelines
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import structlog


@dataclass
class SchemaValidation:
    """Schema validation result."""

    is_valid: bool
    schema_type: str
    errors: list[str]
    warnings: list[str]
    recommendations: list[str]


@dataclass
class SchemaReport:
    """Complete schema markup report."""

    url: str
    timestamp: str
    schemas: list[dict[str, Any]]
    validation_results: list[SchemaValidation]
    missing_schemas: list[str]
    rich_results_eligible: bool
    overall_score: float  # 0-100


class SchemaGenerator:
    """
    Schema Markup Generator.

    Generates and validates Schema.org structured data markup.
    """

    def __init__(self):
        """Initialize Schema Generator."""
        self.logger = structlog.get_logger()

        # Required fields for each schema type
        self.required_fields = {
            "Organization": ["@type", "name", "url"],
            "LocalBusiness": ["@type", "name", "address", "telephone"],
            "Product": ["@type", "name", "image", "description"],
            "Article": ["@type", "headline", "author", "datePublished"],
            "FAQPage": ["@type", "mainEntity"],
            "HowTo": ["@type", "name", "step"],
            "BreadcrumbList": ["@type", "itemListElement"],
        }

    async def generate(
        self,
        schema_type: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Generate schema markup.

        Args:
            schema_type: Type of schema (Organization, Product, etc.)
            data: Data for schema generation

        Returns:
            JSON-LD schema markup
        """
        self.logger.info(
            "schema_generation_start",
            schema_type=schema_type,
        )

        # Generate schema based on type
        if schema_type == "Organization":
            schema = await self._generate_organization(data)
        elif schema_type == "LocalBusiness":
            schema = await self._generate_local_business(data)
        elif schema_type == "Product":
            schema = await self._generate_product(data)
        elif schema_type == "Article":
            schema = await self._generate_article(data)
        elif schema_type == "FAQPage":
            schema = await self._generate_faq(data)
        elif schema_type == "HowTo":
            schema = await self._generate_howto(data)
        elif schema_type == "BreadcrumbList":
            schema = await self._generate_breadcrumb(data)
        else:
            raise ValueError(f"Unsupported schema type: {schema_type}")

        self.logger.info(
            "schema_generation_complete",
            schema_type=schema_type,
        )

        return schema

    async def validate(
        self,
        schema: dict[str, Any],
    ) -> SchemaValidation:
        """
        Validate schema markup.

        Args:
            schema: Schema markup to validate

        Returns:
            Validation result
        """
        schema_type = schema.get("@type", "Unknown")

        errors = []
        warnings = []
        recommendations = []

        # Check @context
        if "@context" not in schema:
            errors.append("Missing @context field")
        elif schema["@context"] != "https://schema.org":
            warnings.append("@context should be https://schema.org")

        # Check @type
        if "@type" not in schema:
            errors.append("Missing @type field")

        # Check required fields
        if schema_type in self.required_fields:
            for field in self.required_fields[schema_type]:
                if field not in schema:
                    errors.append(f"Missing required field: {field}")

        # Type-specific validation
        if schema_type == "Product":
            if "offers" not in schema:
                warnings.append("Product should have offers")
            if "aggregateRating" not in schema:
                recommendations.append("Add aggregateRating for rich results")

        elif schema_type == "Article":
            if "image" not in schema:
                warnings.append("Article should have image")
            if "dateModified" not in schema:
                recommendations.append("Add dateModified for freshness")

        elif schema_type == "LocalBusiness":
            if "geo" not in schema:
                warnings.append("LocalBusiness should have geo coordinates")
            if "openingHours" not in schema:
                recommendations.append("Add openingHours for better visibility")

        is_valid = len(errors) == 0

        return SchemaValidation(
            is_valid=is_valid,
            schema_type=schema_type,
            errors=errors,
            warnings=warnings,
            recommendations=recommendations,
        )

    async def analyze_page(
        self,
        url: str,
        html_content: str | None = None,
    ) -> SchemaReport:
        """
        Analyze page for schema markup.

        Args:
            url: URL to analyze
            html_content: HTML content (if None, will fetch)

        Returns:
            Complete schema analysis report
        """
        self.logger.info("schema_analysis_start", url=url)

        # Extract existing schemas from page
        schemas = await self._extract_schemas(html_content or "")

        # Validate each schema
        validation_results = []
        for schema in schemas:
            validation = await self.validate(schema)
            validation_results.append(validation)

        # Identify missing schemas
        missing_schemas = await self._identify_missing_schemas(url, html_content or "")

        # Check rich results eligibility
        rich_results_eligible = await self._check_rich_results(schemas)

        # Calculate overall score
        overall_score = self._calculate_score(validation_results, missing_schemas)

        report = SchemaReport(
            url=url,
            timestamp=datetime.now().isoformat(),
            schemas=schemas,
            validation_results=validation_results,
            missing_schemas=missing_schemas,
            rich_results_eligible=rich_results_eligible,
            overall_score=round(overall_score, 1),
        )

        self.logger.info(
            "schema_analysis_complete",
            url=url,
            schemas_found=len(schemas),
            score=overall_score,
        )

        return report

    async def _generate_organization(self, data: dict[str, Any]) -> dict[str, Any]:
        """Generate Organization schema."""
        schema = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": data.get("name", ""),
            "url": data.get("url", ""),
        }

        # Optional fields
        if "logo" in data:
            schema["logo"] = data["logo"]
        if "description" in data:
            schema["description"] = data["description"]
        if "email" in data:
            schema["email"] = data["email"]
        if "telephone" in data:
            schema["telephone"] = data["telephone"]
        if "address" in data:
            schema["address"] = {
                "@type": "PostalAddress",
                "streetAddress": data["address"].get("street", ""),
                "addressLocality": data["address"].get("city", ""),
                "addressRegion": data["address"].get("region", ""),
                "postalCode": data["address"].get("postal_code", ""),
                "addressCountry": data["address"].get("country", ""),
            }
        if "social_media" in data:
            schema["sameAs"] = data["social_media"]

        return schema

    async def _generate_local_business(self, data: dict[str, Any]) -> dict[str, Any]:
        """Generate LocalBusiness schema."""
        schema = {
            "@context": "https://schema.org",
            "@type": data.get("business_type", "LocalBusiness"),
            "name": data.get("name", ""),
            "address": {
                "@type": "PostalAddress",
                "streetAddress": data.get("address", {}).get("street", ""),
                "addressLocality": data.get("address", {}).get("city", ""),
                "addressRegion": data.get("address", {}).get("region", ""),
                "postalCode": data.get("address", {}).get("postal_code", ""),
                "addressCountry": data.get("address", {}).get("country", ""),
            },
            "telephone": data.get("telephone", ""),
        }

        # Optional fields
        if "url" in data:
            schema["url"] = data["url"]
        if "image" in data:
            schema["image"] = data["image"]
        if "price_range" in data:
            schema["priceRange"] = data["price_range"]
        if "geo" in data:
            schema["geo"] = {
                "@type": "GeoCoordinates",
                "latitude": data["geo"].get("latitude", 0),
                "longitude": data["geo"].get("longitude", 0),
            }
        if "opening_hours" in data:
            schema["openingHours"] = data["opening_hours"]

        return schema

    async def _generate_product(self, data: dict[str, Any]) -> dict[str, Any]:
        """Generate Product schema."""
        schema = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": data.get("name", ""),
            "image": data.get("image", []),
            "description": data.get("description", ""),
        }

        # Offers
        if "offers" in data:
            schema["offers"] = {
                "@type": "Offer",
                "price": data["offers"].get("price", 0),
                "priceCurrency": data["offers"].get("currency", "RUB"),
                "availability": data["offers"].get("availability", "https://schema.org/InStock"),
                "url": data["offers"].get("url", ""),
            }

        # Rating
        if "rating" in data:
            schema["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": data["rating"].get("value", 0),
                "reviewCount": data["rating"].get("count", 0),
            }

        # Brand
        if "brand" in data:
            schema["brand"] = {
                "@type": "Brand",
                "name": data["brand"],
            }

        return schema

    async def _generate_article(self, data: dict[str, Any]) -> dict[str, Any]:
        """Generate Article schema."""
        schema = {
            "@context": "https://schema.org",
            "@type": data.get("article_type", "Article"),
            "headline": data.get("headline", ""),
            "author": {
                "@type": "Person",
                "name": data.get("author", ""),
            },
            "datePublished": data.get("date_published", ""),
        }

        # Optional fields
        if "image" in data:
            schema["image"] = data["image"]
        if "date_modified" in data:
            schema["dateModified"] = data["date_modified"]
        if "publisher" in data:
            schema["publisher"] = {
                "@type": "Organization",
                "name": data["publisher"].get("name", ""),
                "logo": {
                    "@type": "ImageObject",
                    "url": data["publisher"].get("logo", ""),
                },
            }

        return schema

    async def _generate_faq(self, data: dict[str, Any]) -> dict[str, Any]:
        """Generate FAQPage schema."""
        schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [],
        }

        # Add questions
        for qa in data.get("questions", []):
            schema["mainEntity"].append({
                "@type": "Question",
                "name": qa.get("question", ""),
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": qa.get("answer", ""),
                },
            })

        return schema

    async def _generate_howto(self, data: dict[str, Any]) -> dict[str, Any]:
        """Generate HowTo schema."""
        schema = {
            "@context": "https://schema.org",
            "@type": "HowTo",
            "name": data.get("name", ""),
            "step": [],
        }

        # Optional fields
        if "description" in data:
            schema["description"] = data["description"]
        if "image" in data:
            schema["image"] = data["image"]
        if "total_time" in data:
            schema["totalTime"] = data["total_time"]

        # Add steps
        for i, step in enumerate(data.get("steps", []), 1):
            schema["step"].append({
                "@type": "HowToStep",
                "position": i,
                "name": step.get("name", ""),
                "text": step.get("text", ""),
            })

        return schema

    async def _generate_breadcrumb(self, data: dict[str, Any]) -> dict[str, Any]:
        """Generate BreadcrumbList schema."""
        schema = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [],
        }

        # Add breadcrumb items
        for i, item in enumerate(data.get("items", []), 1):
            schema["itemListElement"].append({
                "@type": "ListItem",
                "position": i,
                "name": item.get("name", ""),
                "item": item.get("url", ""),
            })

        return schema

    async def _extract_schemas(self, html: str) -> list[dict[str, Any]]:
        """Extract existing schemas from HTML."""
        # Mock data (real implementation would parse HTML)
        return [
            {
                "@context": "https://schema.org",
                "@type": "Organization",
                "name": "Example Clinic",
                "url": "https://example.com",
            }
        ]

    async def _identify_missing_schemas(
        self,
        url: str,
        html: str,
    ) -> list[str]:
        """Identify missing schema types."""
        missing = []

        # Check for common missing schemas
        existing_types = [s.get("@type") for s in await self._extract_schemas(html)]

        if "Organization" not in existing_types:
            missing.append("Organization")
        if "LocalBusiness" not in existing_types and "clinic" in url.lower():
            missing.append("LocalBusiness")
        if "BreadcrumbList" not in existing_types:
            missing.append("BreadcrumbList")

        return missing

    async def _check_rich_results(self, schemas: list[dict[str, Any]]) -> bool:
        """Check if schemas are eligible for rich results."""
        eligible_types = ["Product", "Article", "FAQPage", "HowTo", "LocalBusiness"]
        return any(s.get("@type") in eligible_types for s in schemas)

    def _calculate_score(
        self,
        validations: list[SchemaValidation],
        missing_schemas: list[str],
    ) -> float:
        """Calculate overall schema score."""
        if not validations and not missing_schemas:
            return 0.0

        score = 100.0

        # Deduct for invalid schemas
        for validation in validations:
            if not validation.is_valid:
                score -= 20
            score -= len(validation.errors) * 5
            score -= len(validation.warnings) * 2

        # Deduct for missing schemas
        score -= len(missing_schemas) * 10

        return max(0, score)


async def main():
    """Example usage."""
    generator = SchemaGenerator()

    # Generate Organization schema
    org_data = {
        "name": "Example Dental Clinic",
        "url": "https://example.com",
        "logo": "https://example.com/logo.png",
        "telephone": "+7-495-123-4567",
        "address": {
            "street": "Tverskaya St, 1",
            "city": "Moscow",
            "region": "Moscow",
            "postal_code": "125009",
            "country": "RU",
        },
    }

    schema = await generator.generate("Organization", org_data)
    print("Generated Schema:")
    print(json.dumps(schema, indent=2, ensure_ascii=False))

    # Validate schema
    validation = await generator.validate(schema)
    print(f"\nValidation: {'✅ Valid' if validation.is_valid else '❌ Invalid'}")
    if validation.errors:
        print("Errors:", validation.errors)
    if validation.warnings:
        print("Warnings:", validation.warnings)


if __name__ == "__main__":
    asyncio.run(main())
