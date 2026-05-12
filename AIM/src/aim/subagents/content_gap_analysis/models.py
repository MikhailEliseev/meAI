"""
Database Models for Content Gap Analysis Agent

SQLAlchemy models for storing scraped pages, topic clusters, and content gaps.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ScrapedPage(Base):
    """Scraped page content and metadata

    Stores content from both client and competitor sites.
    Used for topic clustering and gap detection.
    """
    __tablename__ = "scraped_pages"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Source identification
    url = Column(String(2048), nullable=False, unique=True, index=True)
    domain = Column(String(255), nullable=False, index=True)
    is_client = Column(Boolean, nullable=False, default=False, index=True)

    # Content
    title = Column(String(512), nullable=True)
    meta_description = Column(String(1024), nullable=True)
    h1 = Column(String(512), nullable=True)
    h2_list = Column(JSON, nullable=True)  # List of H2 headings
    h3_list = Column(JSON, nullable=True)  # List of H3 headings
    body_text = Column(Text, nullable=True)
    word_count = Column(Integer, nullable=True)

    # Content type and structure
    content_type = Column(String(50), nullable=True)  # blog_post, service_page, faq, etc.

    # Author and credentials
    author_name = Column(String(255), nullable=True)
    author_credentials = Column(String(512), nullable=True)  # DDS, DMD, MD, etc.
    is_doctor_authored = Column(Boolean, nullable=False, default=False)

    # Medical citations
    medical_citations_count = Column(Integer, nullable=False, default=0)
    pubmed_links = Column(JSON, nullable=True)  # List of PubMed URLs
    journal_references = Column(JSON, nullable=True)  # List of journal citations

    # Quality metrics
    readability_score = Column(Float, nullable=True)  # Flesch-Kincaid grade level
    eeat_score = Column(Float, nullable=True)  # E-E-A-T score (0.0-1.0)

    # E-E-A-T components (for debugging/analysis)
    experience_score = Column(Float, nullable=True)  # 0.0-1.0
    expertise_score = Column(Float, nullable=True)  # 0.0-1.0
    authoritativeness_score = Column(Float, nullable=True)  # 0.0-1.0
    trustworthiness_score = Column(Float, nullable=True)  # 0.0-1.0

    # Traffic and engagement (from API or estimates)
    traffic_estimate = Column(Integer, nullable=True)
    backlinks_count = Column(Integer, nullable=True)

    # Technical
    has_https = Column(Boolean, nullable=False, default=True)
    has_contact_info = Column(Boolean, nullable=False, default=False)
    has_privacy_policy = Column(Boolean, nullable=False, default=False)

    # Metadata
    scraped_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    analysis_id = Column(String(36), nullable=False, index=True)  # UUID of analysis run

    # Relationships
    cluster_assignments = relationship("PageClusterAssignment", back_populates="page")


class TopicCluster(Base):
    """Topic cluster from BERTopic

    Groups pages by semantic similarity.
    Used for gap detection and hierarchy building.
    """
    __tablename__ = "topic_clusters"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Cluster identification
    cluster_id = Column(Integer, nullable=False, index=True)  # BERTopic cluster ID
    analysis_id = Column(String(36), nullable=False, index=True)  # UUID of analysis run

    # Cluster metadata
    cluster_name = Column(String(255), nullable=False)  # Human-readable name
    representative_words = Column(JSON, nullable=True)  # Top words from BERTopic

    # Hierarchy
    parent_cluster_id = Column(Integer, ForeignKey("topic_clusters.id"), nullable=True)
    parent_cluster = relationship("TopicCluster", remote_side=[id], backref="subclusters")

    # Coverage statistics
    total_pages = Column(Integer, nullable=False, default=0)
    client_pages = Column(Integer, nullable=False, default=0)
    competitor_pages = Column(Integer, nullable=False, default=0)

    # Quality metrics
    avg_eeat_score = Column(Float, nullable=True)
    avg_word_count = Column(Integer, nullable=True)
    silhouette_score = Column(Float, nullable=True)  # Cluster quality metric

    # Metadata
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    page_assignments = relationship("PageClusterAssignment", back_populates="cluster")
    gaps = relationship("ContentGap", back_populates="cluster")


class PageClusterAssignment(Base):
    """Many-to-many relationship between pages and clusters

    A page can belong to multiple clusters (hierarchical clustering).
    """
    __tablename__ = "page_cluster_assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)

    page_id = Column(Integer, ForeignKey("scraped_pages.id"), nullable=False, index=True)
    cluster_id = Column(Integer, ForeignKey("topic_clusters.id"), nullable=False, index=True)

    # Assignment metadata
    confidence = Column(Float, nullable=True)  # Clustering confidence (0.0-1.0)
    is_representative = Column(Boolean, nullable=False, default=False)  # Is this page representative of cluster?

    # Relationships
    page = relationship("ScrapedPage", back_populates="cluster_assignments")
    cluster = relationship("TopicCluster", back_populates="page_assignments")


class ContentGap(Base):
    """Detected content gap

    Represents a topic/cluster where competitors have content but client doesn't.
    """
    __tablename__ = "content_gaps"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Gap identification
    analysis_id = Column(String(36), nullable=False, index=True)  # UUID of analysis run
    cluster_id = Column(Integer, ForeignKey("topic_clusters.id"), nullable=True, index=True)

    # Gap details
    topic = Column(String(512), nullable=False)
    gap_type = Column(String(50), nullable=False)  # missing_topic, underrepresented_topic

    # Scoring
    opportunity_score = Column(Float, nullable=False, index=True)  # 0-100
    priority = Column(String(10), nullable=False, index=True)  # P0, P1, P2, P3

    # Opportunity score components (for debugging/analysis)
    competitor_avg_traffic = Column(Float, nullable=True)
    competitor_avg_quality = Column(Float, nullable=True)
    topic_relevance = Column(Float, nullable=True)
    keyword_search_volume = Column(Float, nullable=True)
    content_difficulty = Column(Float, nullable=True)
    existing_client_coverage = Column(Float, nullable=True)

    # Competitor coverage
    competitor_coverage = Column(JSON, nullable=False)  # Dict of competitor URLs with metrics

    # Recommendations
    recommended_word_count = Column(Integer, nullable=True)
    recommended_content_type = Column(String(50), nullable=True)
    recommended_actions = Column(JSON, nullable=True)  # List of action items
    target_keywords = Column(JSON, nullable=True)  # List of keywords

    # Metadata
    detected_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    cluster = relationship("TopicCluster", back_populates="gaps")


class AnalysisRun(Base):
    """Analysis run metadata

    Tracks each content gap analysis execution.
    """
    __tablename__ = "analysis_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Run identification
    analysis_id = Column(String(36), nullable=False, unique=True, index=True)  # UUID

    # Input parameters
    client_url = Column(String(2048), nullable=False)
    competitor_urls = Column(JSON, nullable=False)  # List of competitor URLs
    niche = Column(String(255), nullable=False)
    analysis_depth = Column(String(20), nullable=False)  # quick, standard, deep
    max_pages_per_site = Column(Integer, nullable=False)
    max_cost_usd = Column(Float, nullable=False)

    # Results summary
    status = Column(String(20), nullable=False)  # success, partial_success, failure
    total_pages_scraped = Column(Integer, nullable=False, default=0)
    total_gaps_found = Column(Integer, nullable=False, default=0)
    p0_gaps = Column(Integer, nullable=False, default=0)
    p1_gaps = Column(Integer, nullable=False, default=0)
    p2_gaps = Column(Integer, nullable=False, default=0)
    p3_gaps = Column(Integer, nullable=False, default=0)

    # Performance metrics
    execution_time_ms = Column(Integer, nullable=True)
    api_calls = Column(Integer, nullable=False, default=0)
    total_cost_usd = Column(Float, nullable=False, default=0.0)

    # Quality metrics
    avg_client_eeat = Column(Float, nullable=True)
    avg_competitor_eeat = Column(Float, nullable=True)
    avg_client_word_count = Column(Integer, nullable=True)
    avg_competitor_word_count = Column(Integer, nullable=True)

    # Errors
    errors = Column(JSON, nullable=True)  # List of error objects

    # Metadata
    started_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
