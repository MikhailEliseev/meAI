"""Company Profile Pydantic Schemas

Request/response validation for company_profiles API.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CompanyProfileCreate(BaseModel):
    """Request to create or update a company profile."""
    url: str
    inn: str = ""
    profile_data: dict[str, Any] = Field(default_factory=dict)


class CompanyProfileResponse(BaseModel):
    """Response with full company profile data."""
    id: int
    url: str
    inn: str
    profile_data: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyProfileFound(BaseModel):
    """Response when profile is found."""
    found: bool = True
    profile: CompanyProfileResponse


class CompanyProfileNotFound(BaseModel):
    """Response when profile is not found."""
    found: bool = False
    url: str


class StagedPrescanRequest(BaseModel):
    """Request to run 3-stage ultra-deep prescan."""
    url: str = Field(..., description="Client clinic website URL")
    force_refresh: bool = Field(default=False, description="Skip cache, re-run all stages")


class StagedPrescanResponse(BaseModel):
    """Response with 3-stage prescan results."""
    success: bool
    url: str
    cached: bool = False
    elapsed_seconds: float
    profile_data: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
