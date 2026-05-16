"""Document Schemas

Pydantic models for document processing API.

Part of: Phase 11 Sprint 3 - Task 3.3
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class DocumentUploadRequest(BaseModel):
    """Request to upload a document."""

    lead_id: str = Field(..., min_length=1, max_length=50)
    document_type: Literal["license", "inn", "ogrn", "contract"] = Field(...)


class DocumentUploadResponse(BaseModel):
    """Response after document upload."""

    document_id: str
    status: str
    message: str


class ExtractedData(BaseModel):
    """Structured data extracted from document."""

    # License information
    license_number: Optional[str] = None
    license_date: Optional[str] = None
    license_issuer: Optional[str] = None

    # Clinic information
    clinic_name: Optional[str] = None
    clinic_address: Optional[str] = None
    clinic_phone: Optional[str] = None
    clinic_email: Optional[str] = None

    # Legal entity information
    inn: Optional[str] = None
    ogrn: Optional[str] = None
    kpp: Optional[str] = None

    # Director information
    director_name: Optional[str] = None
    director_position: Optional[str] = None

    @field_validator("inn")
    @classmethod
    def validate_inn_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate INN format (10 or 12 digits)."""
        if v is None:
            return v
        if not v.isdigit():
            raise ValueError("INN must contain only digits")
        if len(v) not in (10, 12):
            raise ValueError("INN must be 10 or 12 digits")
        return v

    @field_validator("ogrn")
    @classmethod
    def validate_ogrn_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate OGRN format (13 or 15 digits)."""
        if v is None:
            return v
        if not v.isdigit():
            raise ValueError("OGRN must contain only digits")
        if len(v) not in (13, 15):
            raise ValueError("OGRN must be 13 or 15 digits")
        return v

    @field_validator("kpp")
    @classmethod
    def validate_kpp_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate KPP format (9 digits)."""
        if v is None:
            return v
        if not v.isdigit():
            raise ValueError("KPP must contain only digits")
        if len(v) != 9:
            raise ValueError("KPP must be 9 digits")
        return v


class ValidationResult(BaseModel):
    """Result of document validation."""

    is_valid: bool
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DocumentStatusResponse(BaseModel):
    """Response with document processing status."""

    document_id: str
    status: str
    document_type: str
    file_name: str
    file_size: int
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    extracted_data: Optional[ExtractedData] = None
    validation_result: Optional[ValidationResult] = None


class DocumentListResponse(BaseModel):
    """Response with list of documents."""

    documents: list[DocumentStatusResponse]
    total: int
