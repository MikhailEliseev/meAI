"""
Entity Optimizer for SEO

Extracts entities, optimizes for Knowledge Graph, suggests schema.org markup.
Uses spaCy for NER, analyzes entity density and relationships.
"""

import re
from typing import List, Dict, Any, Optional, Set
from collections import Counter

try:
    import spacy
    from spacy.language import Language
except ImportError:
    spacy = None
    Language = None

from .schemas import Entity, EntityAnalysis


class EntityOptimizer:
    """
    Entity extraction and Knowledge Graph optimization.

    Features:
    - spaCy NER for entity extraction
    - Entity density calculation
    - Schema.org markup suggestions
    - Related entity discovery
    - Knowledge Graph readiness scoring
    """

    # Schema.org types mapping
    SCHEMA_MAPPING = {
        "PERSON": "Person",
        "ORG": "Organization",
        "GPE": "Place",
        "LOC": "Place",
        "PRODUCT": "Product",
        "EVENT": "Event",
        "WORK_OF_ART": "CreativeWork",
        "LAW": "Legislation",
        "LANGUAGE": "Language",
        "DATE": "Date",
        "TIME": "Time",
        "PERCENT": "QuantitativeValue",
        "MONEY": "MonetaryAmount",
        "QUANTITY": "QuantitativeValue",
    }

    # Medical-specific entity types
    MEDICAL_ENTITIES = {
        "DISEASE": "MedicalCondition",
        "SYMPTOM": "MedicalSymptom",
        "TREATMENT": "MedicalProcedure",
        "MEDICATION": "Drug",
        "ANATOMY": "AnatomicalStructure",
    }

    def __init__(self, model_name: str = "ru_core_news_lg"):
        """
        Initialize entity optimizer.

        Args:
            model_name: spaCy model name (default: ru_core_news_lg for Russian)
        """
        if spacy is None:
            raise ImportError(
                "spaCy is required for entity extraction. "
                "Install with: pip install spacy && python -m spacy download ru_core_news_lg"
            )

        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            raise ImportError(
                f"spaCy model '{model_name}' not found. "
                f"Download with: python -m spacy download {model_name}"
            )

    async def analyze(
        self,
        content: str,
        url: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EntityAnalysis:
        """
        Analyze entities in content.

        Args:
            content: HTML content
            url: Page URL
            metadata: Optional metadata (title, description, etc.)

        Returns:
            EntityAnalysis with entities, density, schema suggestions
        """
        # Extract text from HTML
        text = self._extract_text(content)

        # Extract entities with spaCy
        entities = self._extract_entities(text)

        # Calculate entity density
        density = self._calculate_density(entities, text)

        # Generate schema.org suggestions
        schema_suggestions = self._generate_schema_suggestions(entities, url, metadata)

        # Find related entities
        related_entities = self._find_related_entities(entities)

        # Check Knowledge Graph readiness
        kg_ready = self._check_kg_readiness(entities, density, schema_suggestions)

        return EntityAnalysis(
            entities=entities,
            density=density,
            schema_suggestions=schema_suggestions,
            related_entities=related_entities,
            knowledge_graph_ready=kg_ready,
        )

    def _extract_text(self, html: str) -> str:
        """Extract clean text from HTML."""
        # Remove script and style tags
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", text)

        # Decode HTML entities
        text = text.replace("&nbsp;", " ")
        text = text.replace("&quot;", '"')
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")

        # Clean whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def _extract_entities(self, text: str) -> List[Entity]:
        """
        Extract entities using spaCy NER.

        Args:
            text: Clean text

        Returns:
            List of Entity objects
        """
        doc = self.nlp(text)

        entities = []
        for ent in doc.ents:
            # Skip low-confidence entities
            if hasattr(ent, "_.score") and ent._.score < 0.5:
                continue

            entities.append(
                Entity(
                    text=ent.text,
                    label=ent.label_,
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=getattr(ent._, "score", 1.0),
                )
            )

        return entities

    def _calculate_density(self, entities: List[Entity], text: str) -> float:
        """
        Calculate entity density (entities per 100 words).

        Args:
            entities: List of entities
            text: Full text

        Returns:
            Entity density (0-100)
        """
        if not text:
            return 0.0

        # Count words
        words = len(text.split())
        if words == 0:
            return 0.0

        # Calculate density
        density = (len(entities) / words) * 100

        return round(density, 2)

    def _generate_schema_suggestions(
        self,
        entities: List[Entity],
        url: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Generate schema.org markup suggestions.

        Args:
            entities: List of entities
            url: Page URL
            metadata: Optional metadata

        Returns:
            List of schema.org suggestions
        """
        suggestions = []

        # Count entity types
        entity_counts = Counter(e.label for e in entities)

        # Medical content detection
        is_medical = any(
            keyword in url.lower()
            for keyword in ["clinic", "doctor", "medical", "health", "клиника", "врач", "медицин"]
        )

        # Base schema for all pages
        suggestions.append("WebPage (базовая разметка)")

        # Article schema if content-heavy
        if len(entities) > 10:
            suggestions.append("Article (статья с сущностями)")

        # Medical schema
        if is_medical:
            suggestions.append("MedicalWebPage (медицинский контент)")

            if entity_counts.get("PERSON", 0) > 0:
                suggestions.append("Physician (врач)")

            if entity_counts.get("ORG", 0) > 0:
                suggestions.append("MedicalClinic (клиника)")

        # Organization schema
        if entity_counts.get("ORG", 0) > 2:
            suggestions.append("Organization (организация)")

        # Person schema
        if entity_counts.get("PERSON", 0) > 2:
            suggestions.append("Person (персона)")

        # Product schema
        if entity_counts.get("PRODUCT", 0) > 0:
            suggestions.append("Product (продукт)")

        # Event schema
        if entity_counts.get("EVENT", 0) > 0:
            suggestions.append("Event (событие)")

        # FAQ schema if questions detected
        if metadata and "?" in metadata.get("title", ""):
            suggestions.append("FAQPage (вопросы-ответы)")

        # BreadcrumbList for navigation
        if "/" in url and url.count("/") > 3:
            suggestions.append("BreadcrumbList (навигация)")

        return suggestions

    def _find_related_entities(self, entities: List[Entity]) -> List[str]:
        """
        Find related entities for Knowledge Graph.

        Args:
            entities: List of entities

        Returns:
            List of related entity suggestions
        """
        related = []

        # Count entity types
        entity_counts = Counter(e.label for e in entities)

        # Medical relationships
        if entity_counts.get("PERSON", 0) > 0 and entity_counts.get("ORG", 0) > 0:
            related.append("Связь врач-клиника (worksFor)")

        if entity_counts.get("ORG", 0) > 0 and entity_counts.get("GPE", 0) > 0:
            related.append("Связь организация-место (location)")

        # Product relationships
        if entity_counts.get("PRODUCT", 0) > 0 and entity_counts.get("ORG", 0) > 0:
            related.append("Связь продукт-производитель (manufacturer)")

        # Event relationships
        if entity_counts.get("EVENT", 0) > 0 and entity_counts.get("GPE", 0) > 0:
            related.append("Связь событие-место (location)")

        if entity_counts.get("EVENT", 0) > 0 and entity_counts.get("PERSON", 0) > 0:
            related.append("Связь событие-участник (performer)")

        return related

    def _check_kg_readiness(
        self,
        entities: List[Entity],
        density: float,
        schema_suggestions: List[str],
    ) -> bool:
        """
        Check if content is ready for Knowledge Graph.

        Criteria:
        - At least 5 entities
        - Entity density 2-5% (optimal range)
        - At least 3 schema.org suggestions
        - High-confidence entities (avg > 0.7)

        Args:
            entities: List of entities
            density: Entity density
            schema_suggestions: Schema.org suggestions

        Returns:
            True if ready for Knowledge Graph
        """
        # Check entity count
        if len(entities) < 5:
            return False

        # Check density (2-5% is optimal)
        if density < 2.0 or density > 5.0:
            return False

        # Check schema suggestions
        if len(schema_suggestions) < 3:
            return False

        # Check entity confidence
        avg_confidence = sum(e.confidence for e in entities) / len(entities)
        if avg_confidence < 0.7:
            return False

        return True
