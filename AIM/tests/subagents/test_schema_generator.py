"""Tests for Schema Markup Generator."""

import pytest

from src.aim.subagents.seo.schema_generator import (
    SchemaGenerator,
    SchemaValidation,
    SchemaReport,
)


@pytest.fixture
def generator():
    """Create Schema Generator instance."""
    return SchemaGenerator()


@pytest.mark.asyncio
async def test_generate_organization(generator):
    """Test Organization schema generation."""
    data = {
        "name": "Example Clinic",
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

    schema = await generator.generate("Organization", data)

    assert schema["@context"] == "https://schema.org"
    assert schema["@type"] == "Organization"
    assert schema["name"] == "Example Clinic"
    assert schema["url"] == "https://example.com"
    assert "address" in schema
    assert schema["address"]["@type"] == "PostalAddress"


@pytest.mark.asyncio
async def test_generate_local_business(generator):
    """Test LocalBusiness schema generation."""
    data = {
        "business_type": "DentalClinic",
        "name": "Dental Clinic",
        "address": {
            "street": "Main St, 1",
            "city": "Moscow",
            "region": "Moscow",
            "postal_code": "125009",
            "country": "RU",
        },
        "telephone": "+7-495-123-4567",
        "geo": {
            "latitude": 55.7558,
            "longitude": 37.6173,
        },
    }

    schema = await generator.generate("LocalBusiness", data)

    assert schema["@type"] == "DentalClinic"
    assert schema["name"] == "Dental Clinic"
    assert schema["telephone"] == "+7-495-123-4567"
    assert "geo" in schema
    assert schema["geo"]["@type"] == "GeoCoordinates"


@pytest.mark.asyncio
async def test_generate_product(generator):
    """Test Product schema generation."""
    data = {
        "name": "Dental Implant",
        "image": ["https://example.com/implant.jpg"],
        "description": "High-quality dental implant",
        "offers": {
            "price": 50000,
            "currency": "RUB",
            "availability": "https://schema.org/InStock",
            "url": "https://example.com/implant",
        },
        "rating": {
            "value": 4.8,
            "count": 120,
        },
        "brand": "Example Brand",
    }

    schema = await generator.generate("Product", data)

    assert schema["@type"] == "Product"
    assert schema["name"] == "Dental Implant"
    assert "offers" in schema
    assert schema["offers"]["price"] == 50000
    assert "aggregateRating" in schema
    assert schema["aggregateRating"]["ratingValue"] == 4.8


@pytest.mark.asyncio
async def test_generate_article(generator):
    """Test Article schema generation."""
    data = {
        "article_type": "BlogPosting",
        "headline": "How to Care for Dental Implants",
        "author": "Dr. Smith",
        "date_published": "2026-05-14",
        "image": "https://example.com/article.jpg",
        "publisher": {
            "name": "Example Clinic",
            "logo": "https://example.com/logo.png",
        },
    }

    schema = await generator.generate("Article", data)

    assert schema["@type"] == "BlogPosting"
    assert schema["headline"] == "How to Care for Dental Implants"
    assert schema["author"]["@type"] == "Person"
    assert schema["author"]["name"] == "Dr. Smith"
    assert "publisher" in schema


@pytest.mark.asyncio
async def test_generate_faq(generator):
    """Test FAQPage schema generation."""
    data = {
        "questions": [
            {
                "question": "How long do dental implants last?",
                "answer": "With proper care, dental implants can last 20+ years.",
            },
            {
                "question": "Is the procedure painful?",
                "answer": "The procedure is performed under anesthesia and is painless.",
            },
        ],
    }

    schema = await generator.generate("FAQPage", data)

    assert schema["@type"] == "FAQPage"
    assert len(schema["mainEntity"]) == 2
    assert schema["mainEntity"][0]["@type"] == "Question"
    assert schema["mainEntity"][0]["acceptedAnswer"]["@type"] == "Answer"


@pytest.mark.asyncio
async def test_generate_howto(generator):
    """Test HowTo schema generation."""
    data = {
        "name": "How to Brush Your Teeth",
        "description": "Step-by-step guide",
        "steps": [
            {"name": "Step 1", "text": "Apply toothpaste"},
            {"name": "Step 2", "text": "Brush for 2 minutes"},
            {"name": "Step 3", "text": "Rinse mouth"},
        ],
    }

    schema = await generator.generate("HowTo", data)

    assert schema["@type"] == "HowTo"
    assert schema["name"] == "How to Brush Your Teeth"
    assert len(schema["step"]) == 3
    assert schema["step"][0]["position"] == 1


@pytest.mark.asyncio
async def test_generate_breadcrumb(generator):
    """Test BreadcrumbList schema generation."""
    data = {
        "items": [
            {"name": "Home", "url": "https://example.com"},
            {"name": "Services", "url": "https://example.com/services"},
            {"name": "Implants", "url": "https://example.com/services/implants"},
        ],
    }

    schema = await generator.generate("BreadcrumbList", data)

    assert schema["@type"] == "BreadcrumbList"
    assert len(schema["itemListElement"]) == 3
    assert schema["itemListElement"][0]["position"] == 1
    assert schema["itemListElement"][0]["name"] == "Home"


@pytest.mark.asyncio
async def test_validate_valid_schema(generator):
    """Test validation of valid schema."""
    schema = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "Example",
        "url": "https://example.com",
    }

    validation = await generator.validate(schema)

    assert isinstance(validation, SchemaValidation)
    assert validation.is_valid is True
    assert validation.schema_type == "Organization"
    assert len(validation.errors) == 0


@pytest.mark.asyncio
async def test_validate_missing_context(generator):
    """Test validation with missing @context."""
    schema = {
        "@type": "Organization",
        "name": "Example",
        "url": "https://example.com",
    }

    validation = await generator.validate(schema)

    assert validation.is_valid is False
    assert any("@context" in error for error in validation.errors)


@pytest.mark.asyncio
async def test_validate_missing_required_field(generator):
    """Test validation with missing required field."""
    schema = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "Example",
        # Missing 'url'
    }

    validation = await generator.validate(schema)

    assert validation.is_valid is False
    assert any("url" in error for error in validation.errors)


@pytest.mark.asyncio
async def test_validate_product_warnings(generator):
    """Test Product schema validation warnings."""
    schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "Product",
        "image": ["image.jpg"],
        "description": "Description",
        # Missing offers and rating
    }

    validation = await generator.validate(schema)

    assert validation.is_valid is True  # No errors, just warnings
    assert len(validation.warnings) > 0
    assert any("offers" in warning for warning in validation.warnings)


@pytest.mark.asyncio
async def test_analyze_page(generator):
    """Test page analysis."""
    html = """
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "Example",
        "url": "https://example.com"
    }
    </script>
    """

    report = await generator.analyze_page(
        url="https://example.com",
        html_content=html,
    )

    assert isinstance(report, SchemaReport)
    assert report.url == "https://example.com"
    assert len(report.schemas) > 0
    assert len(report.validation_results) > 0
    assert isinstance(report.missing_schemas, list)
    assert 0 <= report.overall_score <= 100


@pytest.mark.asyncio
async def test_identify_missing_schemas(generator):
    """Test missing schemas identification."""
    missing = await generator._identify_missing_schemas(
        "https://example.com/clinic",
        "",
    )

    assert isinstance(missing, list)
    # Organization is in mock data, so not missing
    assert "LocalBusiness" in missing  # URL contains 'clinic'
    assert "BreadcrumbList" in missing


@pytest.mark.asyncio
async def test_check_rich_results_eligible(generator):
    """Test rich results eligibility check."""
    schemas = [
        {"@type": "Product"},
        {"@type": "Organization"},
    ]

    eligible = await generator._check_rich_results(schemas)

    assert eligible is True  # Product is eligible


@pytest.mark.asyncio
async def test_check_rich_results_not_eligible(generator):
    """Test rich results not eligible."""
    schemas = [
        {"@type": "Organization"},
    ]

    eligible = await generator._check_rich_results(schemas)

    assert eligible is False


def test_calculate_score_perfect(generator):
    """Test score calculation with perfect schemas."""
    validations = [
        SchemaValidation(
            is_valid=True,
            schema_type="Organization",
            errors=[],
            warnings=[],
            recommendations=[],
        ),
    ]
    missing = []

    score = generator._calculate_score(validations, missing)

    assert score == 100.0


def test_calculate_score_with_errors(generator):
    """Test score calculation with errors."""
    validations = [
        SchemaValidation(
            is_valid=False,
            schema_type="Organization",
            errors=["Missing field"],
            warnings=["Warning"],
            recommendations=[],
        ),
    ]
    missing = ["LocalBusiness"]

    score = generator._calculate_score(validations, missing)

    assert score < 100.0
    assert score >= 0.0


def test_calculate_score_empty(generator):
    """Test score calculation with no schemas."""
    score = generator._calculate_score([], [])

    assert score == 0.0
