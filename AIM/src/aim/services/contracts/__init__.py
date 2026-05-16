"""
Contract Management Services

Provides contract generation, e-signature integration, and document management.
"""

from aim.services.contracts.generator import ContractGenerator, ContractVersioning
from aim.services.contracts.templates import ContractType, ContractTemplate
from aim.services.contracts.kontour_client import (
    KontourClient,
    KontourWebhookHandler,
    DocumentStatus,
    SignatureType,
)

__all__ = [
    "ContractGenerator",
    "ContractVersioning",
    "ContractType",
    "ContractTemplate",
    "KontourClient",
    "KontourWebhookHandler",
    "DocumentStatus",
    "SignatureType",
]
