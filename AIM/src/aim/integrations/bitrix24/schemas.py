"""Pydantic schemas for Bitrix24 CRM entities.

Maps AIM domain models to Bitrix24 REST API format:
- Bitrix24Lead: crm.lead.add / crm.lead.update
- Bitrix24Contact: crm.contact.add / crm.contact.update
- Bitrix24Deal: crm.deal.add / crm.deal.update
- Bitrix24Webhook: incoming webhook payload verification
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Bitrix24Lead(BaseModel):
    """Bitrix24 Lead — maps from AIM Lead model.

    Bitrix24 field names use snake_case (REST API format).
    https://dev.1c-bitrix.ru/rest_help/crm/leads/crm_lead_add.php
    """

    title: str = Field(..., description="Lead title (required)")
    name: Optional[str] = Field(None, description="Contact first name")
    last_name: Optional[str] = Field(None, description="Contact last name")
    phone: list[dict[str, str]] = Field(default_factory=list, description="Phone numbers")
    email: list[dict[str, str]] = Field(default_factory=list, description="Email addresses")
    source_id: Optional[str] = Field(None, description="Lead source: WEB, CALL, etc.")
    source_description: Optional[str] = Field(None, description="Source details")
    comments: Optional[str] = Field(None, description="Lead comments / notes")
    currency_id: Optional[str] = Field("RUB", description="Currency code")
    opportunity: Optional[float] = Field(None, description="Estimated deal amount")
    uf_crm_lead_aim_id: Optional[str] = Field(None, description="AIM internal lead ID (custom field)")
    uf_crm_lead_tier: Optional[str] = Field(None, description="Qualification tier: hot/warm/cold")
    uf_crm_lead_score: Optional[int] = Field(None, description="Qualification score 0-100")

    @field_validator("phone", mode="before")
    @classmethod
    def normalize_phone(cls, v):
        if isinstance(v, str):
            return [{"VALUE": v, "VALUE_TYPE": "WORK"}]
        if isinstance(v, list) and v and isinstance(v[0], str):
            return [{"VALUE": item, "VALUE_TYPE": "WORK"} for item in v]
        return v

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v):
        if isinstance(v, str):
            return [{"VALUE": v, "VALUE_TYPE": "WORK"}]
        if isinstance(v, list) and v and isinstance(v[0], str):
            return [{"VALUE": item, "VALUE_TYPE": "WORK"} for item in v]
        return v

    def to_bitrix24(self) -> dict:
        """Convert to Bitrix24 REST API fields dict, excluding None values."""
        data = self.model_dump(exclude_none=True)
        # Bitrix24 uses uppercase field names in REST API
        return {k.upper(): v for k, v in data.items()}


class Bitrix24Contact(BaseModel):
    """Bitrix24 Contact — maps from AIM Lead personal info.

    https://dev.1c-bitrix.ru/rest_help/crm/contacts/crm_contact_add.php
    """

    name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    phone: list[dict[str, str]] = Field(default_factory=list)
    email: list[dict[str, str]] = Field(default_factory=list)
    source_id: Optional[str] = Field("WEB")
    source_description: Optional[str] = Field(None)
    uf_crm_contact_aim_id: Optional[str] = Field(None, description="AIM internal lead ID")

    @field_validator("phone", "email", mode="before")
    @classmethod
    def normalize_contact_field(cls, v):
        if isinstance(v, str):
            return [{"VALUE": v, "VALUE_TYPE": "WORK"}]
        if isinstance(v, list) and v and isinstance(v[0], str):
            return [{"VALUE": item, "VALUE_TYPE": "WORK"} for item in v]
        return v

    def to_bitrix24(self) -> dict:
        data = self.model_dump(exclude_none=True)
        return {k.upper(): v for k, v in data.items()}


class Bitrix24Deal(BaseModel):
    """Bitrix24 Deal — maps from qualified AIM Lead.

    https://dev.1c-bitrix.ru/rest_help/crm/deals/crm_deal_add.php
    """

    title: str = Field(..., description="Deal title")
    contact_id: Optional[int] = Field(None, description="Linked contact ID")
    lead_id: Optional[int] = Field(None, description="Linked lead ID in Bitrix24")
    category_id: Optional[int] = Field(None, description="Deal category / pipeline")
    stage_id: Optional[str] = Field("NEW", description="Deal stage")
    opportunity: Optional[float] = Field(None, description="Estimated amount")
    currency_id: Optional[str] = Field("RUB")
    comments: Optional[str] = Field(None)
    uf_crm_deal_aim_id: Optional[str] = Field(None, description="AIM internal lead ID")

    def to_bitrix24(self) -> dict:
        data = self.model_dump(exclude_none=True)
        return {k.upper(): v for k, v in data.items()}


class Bitrix24Webhook(BaseModel):
    """Incoming Bitrix24 webhook payload.

    Bitrix24 sends webhook events when entities are created/updated/deleted.
    https://dev.1c-bitrix.ru/rest_help/rest_sum/webhooks.php
    """

    event: str = Field(..., description="Event type: ONCRMLEADADD, ONCRMLEADUPDATE, etc.")
    data: dict = Field(default_factory=dict, description="Entity data")
    ts: Optional[str] = Field(None, description="Event timestamp")
    auth: dict = Field(default_factory=dict, description="Auth info from Bitrix24")

    @property
    def entity_type(self) -> str | None:
        """Extract entity type from event name."""
        event = self.event
        if "LEAD" in event:
            return "lead"
        if "DEAL" in event:
            return "deal"
        if "CONTACT" in event:
            return "contact"
        return None

    @property
    def entity_id(self) -> str | None:
        """Extract entity ID from webhook data."""
        return self.data.get("FIELDS", {}).get("ID", str(self.data.get("FIELDS", {}).get("id", "")))


class CrmSyncResult(BaseModel):
    """Result of a CRM sync operation."""

    success: bool
    action: str = Field(..., description="lead_add, lead_update, contact_add, deal_add")
    bitrix24_id: Optional[int] = Field(None, description="Created entity ID in Bitrix24")
    aim_lead_id: Optional[str] = Field(None, description="AIM lead ID")
    error: Optional[str] = Field(None, description="Error message if failed")
    details: dict = Field(default_factory=dict, description="Additional details")
