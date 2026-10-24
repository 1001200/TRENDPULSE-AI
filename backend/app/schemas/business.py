"""
Pydantic Schemas for Seller Business Profile Setup.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class BusinessSetupRequest(BaseModel):
    """Payload for creating / updating a seller's business profile."""
    business_name: str
    instagram_handle: str
    upi_id: str
    flat_shipping_fee: float = 70.0
    fulfillment_type: str = "self"  # "self" or "supplier"
    supplier_phone: Optional[str] = None
    niche: Optional[str] = "Curated Vintage Thrift"
    city: Optional[str] = "Delhi"


class BusinessProfileResponse(BaseModel):
    """Response model for seller business profile."""
    id: int
    user_id: Optional[int] = None
    name: str
    slug: str
    instagram_handle: str
    upi_id: str
    flat_shipping_fee: float
    fulfillment_type: str
    supplier_phone: Optional[str] = None
    niche: Optional[str] = None
    city: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
