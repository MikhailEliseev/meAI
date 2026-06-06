"""
Contract Management Services

Provides contract generation, e-signature integration, and document management.
"""

from src.aim.services.contracts.generator import ContractGenerator, ContractVersioning
from src.aim.services.contracts.templates import ContractType, ContractTemplate
from src.aim.services.contracts.kontour_client import (
    KontourClient,
    KontourWebhookHandler,  # DEPRECATED — replaced by KontourPoller
    DocumentStatus,
    SignatureType,
    verify_webhook_signature,
    get_signature_type_for_amount,
)
from src.aim.services.contracts.kontour_auth import KontourAuth
from src.aim.services.contracts.kontour_poller import KontourPoller

__all__ = [
    "ContractGenerator",
    "ContractVersioning",
    "ContractType",
    "ContractTemplate",
    "KontourClient",
    "KontourAuth",
    "KontourPoller",
    "KontourWebhookHandler",
    "DocumentStatus",
    "SignatureType",
    "verify_webhook_signature",
    "get_signature_type_for_amount",
]
