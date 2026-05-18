"""
Contract Generation API

API endpoints for generating and managing contracts.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import structlog

from aim.services.contracts import (
    ContractGenerator,
    ContractType,
    KontourClient,
    SignatureType,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/api/contracts", tags=["contracts"])


class GenerateContractRequest(BaseModel):
    """Request to generate contract"""
    contract_type: ContractType
    client_data: Dict[str, Any] = Field(
        ...,
        description="Client information (name, INN, address, etc.)",
    )
    contract_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contract-specific data (pricing, terms, etc.)",
    )
    send_for_signature: bool = Field(
        default=False,
        description="Send for e-signature after generation",
    )


class GenerateContractResponse(BaseModel):
    """Response with generated contract"""
    contract_path: str
    contract_number: str
    contract_type: str
    document_id: str | None = None
    signature_url: str | None = None


class ContractStatusResponse(BaseModel):
    """Contract status response"""
    document_id: str
    status: str
    sent_at: str | None = None
    signed_at: str | None = None
    declined_at: str | None = None
    decline_reason: str | None = None


@router.post("/generate", response_model=GenerateContractResponse)
async def generate_contract(
    request: GenerateContractRequest,
    background_tasks: BackgroundTasks,
) -> GenerateContractResponse:
    """
    Generate contract PDF

    Creates PDF contract from template and optionally sends for e-signature.
    """
    try:
        # Initialize generator
        generator = ContractGenerator()

        # Generate contract based on type
        if request.contract_type == ContractType.SERVICE_AGREEMENT:
            contract_path = generator.generate_service_agreement(
                client_data=request.client_data,
                pricing=request.contract_data,
            )
        elif request.contract_type == ContractType.NDA:
            contract_path = generator.generate_nda(
                client_data=request.client_data,
            )
        elif request.contract_type == ContractType.ADDENDUM:
            contract_path = generator.generate_addendum(
                client_data=request.client_data,
                original_contract_number=request.contract_data["contract_number"],
                original_contract_date=request.contract_data["contract_date"],
                changes=request.contract_data["changes"],
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown contract type: {request.contract_type}",
            )

        # Extract contract number from path
        contract_number = contract_path.split("/")[-1].split("_")[1]

        logger.info(
            "contract_generated",
            contract_type=request.contract_type,
            contract_number=contract_number,
            contract_path=contract_path,
        )

        # Send for signature if requested
        document_id = None
        signature_url = None

        if request.send_for_signature:
            # STUB: In Phase 12, this will use real Kontour client
            background_tasks.add_task(
                _send_for_signature_background,
                contract_path,
                request.client_data,
            )
            document_id = f"STUB-{contract_number}"
            signature_url = f"https://diadoc.kontur.ru/sign/{document_id}"

        return GenerateContractResponse(
            contract_path=contract_path,
            contract_number=contract_number,
            contract_type=request.contract_type,
            document_id=document_id,
            signature_url=signature_url,
        )

    except Exception as e:
        logger.error(
            "contract_generation_failed",
            error=str(e),
            contract_type=request.contract_type,
        )
        raise HTTPException(
            status_code=500,
            detail="Contract generation failed",
        )


@router.get("/status/{document_id}", response_model=ContractStatusResponse)
async def get_contract_status(document_id: str) -> ContractStatusResponse:
    """
    Get contract signature status

    STUB: Returns mock status. Real implementation in Phase 12.
    """
    try:
        # STUB: Initialize Kontour client
        kontour = KontourClient(
            api_key="STUB_API_KEY",
            organization_id="STUB_ORG_ID",
        )

        # Get status
        status = await kontour.get_document_status(document_id)

        return ContractStatusResponse(
            document_id=status["document_id"],
            status=status["status"],
            sent_at=status.get("sent_at"),
            signed_at=status.get("signed_at"),
            declined_at=status.get("declined_at"),
            decline_reason=status.get("decline_reason"),
        )

    except Exception as e:
        logger.error(
            "contract_status_check_failed",
            error=str(e),
            document_id=document_id,
        )
        raise HTTPException(
            status_code=500,
            detail="Contract status check failed",
        )


@router.post("/resend/{document_id}")
async def resend_signature_notification(document_id: str) -> Dict[str, str]:
    """
    Resend signature notification

    STUB: Logs resend. Real implementation in Phase 12.
    """
    try:
        # STUB: Initialize Kontour client
        kontour = KontourClient(
            api_key="STUB_API_KEY",
            organization_id="STUB_ORG_ID",
        )

        # Resend notification
        await kontour.resend_notification(document_id)

        return {"message": "Notification resent", "document_id": document_id}

    except Exception as e:
        logger.error(
            "resend_notification_failed",
            error=str(e),
            document_id=document_id,
        )
        raise HTTPException(
            status_code=500,
            detail="Resend notification failed",
        )


@router.post("/cancel/{document_id}")
async def cancel_signature_request(
    document_id: str,
    reason: str,
) -> Dict[str, str]:
    """
    Cancel signature request

    STUB: Logs cancellation. Real implementation in Phase 12.
    """
    try:
        # STUB: Initialize Kontour client
        kontour = KontourClient(
            api_key="STUB_API_KEY",
            organization_id="STUB_ORG_ID",
        )

        # Cancel request
        await kontour.cancel_signature_request(document_id, reason)

        return {"message": "Signature request cancelled", "document_id": document_id}

    except Exception as e:
        logger.error(
            "cancel_signature_failed",
            error=str(e),
            document_id=document_id,
        )
        raise HTTPException(
            status_code=500,
            detail="Contract cancellation failed",
        )


async def _send_for_signature_background(
    contract_path: str,
    client_data: Dict[str, Any],
) -> None:
    """
    Send contract for signature in background

    STUB: Logs action. Real implementation in Phase 12.
    """
    try:
        # STUB: Initialize Kontour client
        kontour = KontourClient(
            api_key="STUB_API_KEY",
            organization_id="STUB_ORG_ID",
        )

        # Determine signature type based on contract amount
        amount = client_data.get("monthly_fee", 0)
        from aim.services.contracts.kontour_client import get_signature_type_for_amount
        signature_type = get_signature_type_for_amount(amount)

        # Send for signature
        document_id = await kontour.send_for_signature(
            document_path=contract_path,
            recipient_email=client_data["client_email"],
            recipient_name=client_data["client_name"],
            recipient_inn=client_data["client_inn"],
            signature_type=signature_type,
            message="Пожалуйста, подпишите договор на оказание услуг по маркетинговому продвижению.",
        )

        logger.info(
            "contract_sent_for_signature",
            document_id=document_id,
            recipient_email=client_data["client_email"],
        )

    except Exception as e:
        logger.error(
            "send_for_signature_failed",
            error=str(e),
            contract_path=contract_path,
        )
