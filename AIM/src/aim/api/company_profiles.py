"""Company Profiles API Endpoints

GET  /api/company-profiles/by-url  — retrieve cached prescan profile
POST /api/company-profiles/upsert  — create or update a profile
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aim.database import get_db
from aim.models.company_profile import CompanyProfileModel
from aim.schemas.company_profile import (
    CompanyProfileCreate,
    CompanyProfileFound,
    CompanyProfileNotFound,
    CompanyProfileResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/company-profiles", tags=["company-profiles"])


def _validate_url(url: str) -> str:
    if not url or not isinstance(url, str):
        raise ValueError("URL is required and must be a string")
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        raise ValueError("URL must start with http:// or https://")
    return url


@router.get("/by-url")
async def get_profile_by_url(
    url: str = Query(..., description="Company website URL"),
    inn: str = Query("", description="Optional INN for disambiguation"),
    db: AsyncSession = Depends(get_db),
):
    try:
        url = _validate_url(url)
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": str(e)},
        )

    stmt = select(CompanyProfileModel).where(CompanyProfileModel.url == url)
    if inn:
        stmt = stmt.where(CompanyProfileModel.inn == inn)
    stmt = stmt.order_by(CompanyProfileModel.updated_at.desc()).limit(1)

    result = await db.execute(stmt)
    row = result.scalar_one_or_none()

    if row is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=CompanyProfileNotFound(url=url).model_dump(),
        )

    return CompanyProfileFound(
        profile=CompanyProfileResponse.model_validate(row)
    ).model_dump(mode="json")


@router.post("/upsert")
async def upsert_profile(
    body: CompanyProfileCreate,
    db: AsyncSession = Depends(get_db),
):
    try:
        url = _validate_url(body.url)
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": str(e)},
        )

    inn = (body.inn or "").strip()

    existing_stmt = (
        select(CompanyProfileModel)
        .where(CompanyProfileModel.url == url, CompanyProfileModel.inn == inn)
        .limit(1)
    )
    existing_result = await db.execute(existing_stmt)
    existing = existing_result.scalar_one_or_none()

    if existing:
        existing.profile_data = body.profile_data
        existing.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(existing)
        resp = CompanyProfileResponse.model_validate(existing)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"created": False, "profile": resp.model_dump(mode="json")},
        )

    new_profile = CompanyProfileModel(
        url=url,
        inn=inn,
        profile_data=body.profile_data,
    )
    db.add(new_profile)
    await db.commit()
    await db.refresh(new_profile)
    resp = CompanyProfileResponse.model_validate(new_profile)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"created": True, "profile": resp.model_dump(mode="json")},
    )
