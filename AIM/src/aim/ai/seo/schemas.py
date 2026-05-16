"""
AI SEO Analyzer Schemas

Pydantic models for SEO analysis results.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Entity(BaseModel):
    """Named entity extracted from content."""
    
    text: str = Field(..., description="Entity text")
    label: str = Field(..., description="Entity type (PERSON, ORG, GPE, etc.)")
    start: int = Field(..., description="Start position in text")
    end: int = Field(..., description="End position in text")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence")


class ContentQualityScore(BaseModel):
    """N-E-E-A-T-T content quality scoring."""
    
    overall: float = Field(..., ge=0.0, le=100.0, description="Overall quality score (0-100)")
    newsworthiness: float = Field(..., ge=0.0, le=100.0, description="Timeliness and relevance")
    expertise: float = Field(..., ge=0.0, le=100.0, description="Author credentials and citations")
    experience: float = Field(..., ge=0.0, le=100.0, description="First-hand knowledge")
    authoritativeness: float = Field(..., ge=0.0, le=100.0, description="Domain authority")
    trustworthiness: float = Field(..., ge=0.0, le=100.0, description="Security and privacy")
    transparency: float = Field(..., ge=0.0, le=100.0, description="Clear authorship")
    readability: float = Field(..., ge=0.0, le=100.0, description="Flesch-Kincaid score")
    recommendations: List[str] = Field(default_factory=list, description="Improvement suggestions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "overall": 85.5,
                "newsworthiness": 90.0,
                "expertise": 85.0,
                "experience": 80.0,
                "authoritativeness": 88.0,
                "trustworthiness": 92.0,
                "transparency": 87.0,
                "readability": 75.0,
                "recommendations": [
                    "Add author bio with credentials",
                    "Include more case studies",
                    "Simplify complex sentences"
                ]
            }
        }


class EntityAnalysis(BaseModel):
    """Entity extraction and optimization analysis."""

    entities: List[Entity] = Field(default_factory=list, description="Extracted entities")
    density: float = Field(..., ge=0.0, le=100.0, description="Entity density (entities per 100 words)")
    schema_suggestions: List[str] = Field(default_factory=list, description="Schema.org markup suggestions")
    related_entities: List[str] = Field(default_factory=list, description="Related entity recommendations")
    knowledge_graph_ready: bool = Field(default=False, description="Ready for knowledge graph")
    
    class Config:
        json_schema_extra = {
            "example": {
                "entities": [
                    {"text": "Москва", "label": "GPE", "start": 0, "end": 6, "confidence": 0.99},
                    {"text": "Стоматология", "label": "ORG", "start": 10, "end": 22, "confidence": 0.95}
                ],
                "density": 2.5,
                "schema_suggestions": [
                    "Add Organization schema for clinic",
                    "Add MedicalBusiness schema",
                    "Add Place schema for location"
                ],
                "related_entities": ["имплантация", "протезирование", "отбеливание"],
                "knowledge_graph_ready": True
            }
        }


class SERPFeature(BaseModel):
    """SERP feature detected."""

    type: str = Field(..., description="Feature type (featured_snippet, paa, knowledge_panel, etc.)")
    present: bool = Field(..., description="Whether feature is present in SERP")
    owned: bool = Field(..., description="Whether we own this feature")
    opportunity_score: float = Field(..., ge=0.0, le=100.0, description="Opportunity score (0-100)")


class SERPAnalysis(BaseModel):
    """SERP analysis results."""
    
    query: str = Field(..., description="Search query")
    featured_snippet: Optional[str] = Field(None, description="Featured snippet content")
    paa_questions: List[str] = Field(default_factory=list, description="People Also Ask questions")
    knowledge_panel: Optional[Dict[str, Any]] = Field(None, description="Knowledge panel data")
    competitor_gaps: List[str] = Field(default_factory=list, description="Content gaps vs competitors")
    serp_features: List[SERPFeature] = Field(default_factory=list, description="All SERP features")
    top_10_urls: List[str] = Field(default_factory=list, description="Top 10 ranking URLs")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "стоматология москва",
                "featured_snippet": "Лучшие стоматологические клиники Москвы...",
                "paa_questions": [
                    "Сколько стоит имплантация зубов в Москве?",
                    "Какая стоматология лучшая в Москве?",
                    "Как выбрать стоматологию?"
                ],
                "knowledge_panel": {"name": "Стоматология", "type": "Medical Business"},
                "competitor_gaps": [
                    "Отсутствует раздел о ценах",
                    "Нет отзывов пациентов",
                    "Не указаны врачи"
                ],
                "serp_features": [],
                "top_10_urls": ["https://example1.com", "https://example2.com"]
            }
        }


class ConversationalOptimization(BaseModel):
    """Conversational search optimization analysis."""
    
    ai_overviews_score: float = Field(..., ge=0.0, le=100.0, description="AI Overviews readiness (0-100)")
    chatgpt_score: float = Field(..., ge=0.0, le=100.0, description="ChatGPT optimization score")
    perplexity_score: float = Field(..., ge=0.0, le=100.0, description="Perplexity optimization score")
    conversational_queries: List[str] = Field(default_factory=list, description="Detected conversational patterns")
    answer_box_ready: bool = Field(default=False, description="Ready for answer boxes")
    faq_suggestions: List[Dict[str, str]] = Field(default_factory=list, description="FAQ schema suggestions")
    citation_score: float = Field(..., ge=0.0, le=100.0, description="Citation quality for AI sources")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ai_overviews_score": 85.0,
                "chatgpt_score": 90.0,
                "perplexity_score": 88.0,
                "conversational_queries": [
                    "как выбрать стоматологию",
                    "что лучше имплант или мост",
                    "сколько стоит отбеливание"
                ],
                "answer_box_ready": True,
                "faq_suggestions": [
                    {"question": "Сколько стоит имплантация?", "answer": "От 30,000 руб..."},
                    {"question": "Больно ли ставить имплант?", "answer": "Процедура проходит под анестезией..."}
                ],
                "citation_score": 92.0
            }
        }


class SEOAnalysisResult(BaseModel):
    """Complete SEO analysis result."""
    
    url: str = Field(..., description="Analyzed URL")
    content_quality: ContentQualityScore = Field(..., description="Content quality scores")
    entity_analysis: EntityAnalysis = Field(..., description="Entity extraction results")
    serp_analysis: Optional[SERPAnalysis] = Field(None, description="SERP analysis (if query provided)")
    conversational: ConversationalOptimization = Field(..., description="Conversational optimization")
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Overall SEO score")
    priority_actions: List[str] = Field(default_factory=list, description="Top priority improvements")
    estimated_impact: str = Field(..., description="Estimated traffic impact (Low/Medium/High)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/services/implants",
                "content_quality": {},
                "entity_analysis": {},
                "serp_analysis": None,
                "conversational": {},
                "overall_score": 87.5,
                "priority_actions": [
                    "Add FAQ schema markup",
                    "Improve entity density",
                    "Optimize for AI Overviews"
                ],
                "estimated_impact": "High"
            }
        }
