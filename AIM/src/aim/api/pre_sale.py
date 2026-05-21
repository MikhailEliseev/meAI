"""Pre-Sale API Endpoints

POST /api/pre-sale/chat          — append message to chat log
POST /api/pre-sale/session       — save/update session metadata
"""

import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from aim.services.pre_sale_folder import PreSaleFolder

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pre-sale", tags=["pre-sale"])


# ── Request/Response models ────────────────────────────────────────

class AppendChatRequest(BaseModel):
    lead_id: str = Field(..., description="Lead ID")
    role: str = Field(..., pattern=r"^(bot|client|system)$")
    message: str = Field(..., min_length=1, max_length=10000)


class AppendChatResponse(BaseModel):
    success: bool = True
    lead_id: str
    role: str


class SaveSessionRequest(BaseModel):
    lead_id: str = Field(..., description="Lead ID")
    url: str = Field(..., description="Client website URL")
    specialization: str = ""
    city: str = ""
    services: list[str] = Field(default_factory=list)
    company_name: str | None = None


class SaveSessionResponse(BaseModel):
    success: bool = True
    lead_id: str


class UpdatePhaseRequest(BaseModel):
    lead_id: str = Field(..., description="Lead ID")
    phase: str = Field(..., description="Current phase name")


class UpdatePhaseResponse(BaseModel):
    success: bool = True
    lead_id: str
    phase: str


# ── Endpoints ──────────────────────────────────────────────────────

@router.post("/chat", response_model=AppendChatResponse, status_code=status.HTTP_200_OK)
async def append_chat(body: AppendChatRequest) -> AppendChatResponse:
    """Append a message to the full chat log for a lead."""
    folder = PreSaleFolder(body.lead_id)
    folder.append_chat(role=body.role, text=body.message)

    logger.debug("chat_appended: lead_id=%s role=%s", body.lead_id, body.role)

    return AppendChatResponse(
        success=True,
        lead_id=body.lead_id,
        role=body.role,
    )


@router.post("/session", response_model=SaveSessionResponse, status_code=status.HTTP_200_OK)
async def save_session(body: SaveSessionRequest) -> SaveSessionResponse:
    """Save pre-sale session metadata."""
    folder = PreSaleFolder(body.lead_id)
    folder.save_session(
        url=body.url,
        specialization=body.specialization,
        city=body.city,
        services=body.services,
        company_name=body.company_name,
    )

    logger.info("pre_sale_session_saved: lead_id=%s", body.lead_id)

    return SaveSessionResponse(
        success=True,
        lead_id=body.lead_id,
    )


@router.post("/session/phase", response_model=UpdatePhaseResponse, status_code=status.HTTP_200_OK)
async def update_phase(body: UpdatePhaseRequest) -> UpdatePhaseResponse:
    """Update the current phase of a pre-sale session."""
    folder = PreSaleFolder(body.lead_id)
    folder.update_phase(body.phase)

    logger.info("pre_sale_phase_updated: lead_id=%s phase=%s", body.lead_id, body.phase)

    return UpdatePhaseResponse(
        success=True,
        lead_id=body.lead_id,
        phase=body.phase,
    )
