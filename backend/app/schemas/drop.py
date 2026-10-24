"""
Pydantic Schemas for TrendPulse Drop & DM Closing System.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class StoreBase(BaseModel):
    name: str
    slug: str
    instagram_handle: str
    upi_id: str
    phone: str
    fulfillment_type: str = "self"  # "self" or "supplier"
    supplier_phone: Optional[str] = None
    flat_shipping_fee: float = 70.0
    niche: Optional[str] = "Curated Vintage Thrift"
    city: Optional[str] = "Delhi"
    policies: Optional[str] = "All sales final for 1-of-1 vintage items unless wrong item received."


class StoreCreate(StoreBase):
    pass


class StoreResponse(StoreBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DropItemBase(BaseModel):
    title: str
    category: str = "Apparel"
    size_label: str = "Free Size"
    chest_inches: Optional[float] = None
    length_inches: Optional[float] = None
    price_inr: float
    condition_score: str = "10/10"
    photo_url: Optional[str] = None
    stock_units: int = 1
    available_units: Optional[int] = 1


class DropItemCreate(DropItemBase):
    pass


class DropItemResponse(DropItemBase):
    id: int
    drop_id: int
    aesthetic: str
    status: str
    reserved_until: Optional[datetime] = None
    seconds_remaining: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DropCreate(BaseModel):
    title: str
    slug: str


class DropResponse(BaseModel):
    id: int
    store_id: int
    title: str
    slug: str
    status: str
    created_at: datetime
    store_name: str
    instagram_handle: str
    upi_id: str
    flat_shipping_fee: float
    items: List[DropItemResponse] = []

    model_config = {"from_attributes": True}


class ClaimRequest(BaseModel):
    buyer_phone: str = Field(..., min_length=10, max_length=15)


class ClaimResponse(BaseModel):
    success: bool
    message: str
    item_id: int
    status: str
    seconds_remaining: int
    upi_intent_uri: str
    flat_shipping_fee: float
    total_amount_inr: float


class CheckoutRequest(BaseModel):
    buyer_name: str = Field(..., min_length=2, max_length=100)
    buyer_ig: str = Field(..., min_length=2, max_length=50)
    buyer_phone: str = Field(..., min_length=10, max_length=15)
    address_line: str = Field(..., min_length=5)
    pincode: str = Field(..., min_length=6, max_length=6)
    city: str = Field(..., min_length=2)
    state: str = Field(..., min_length=2)
    utr_reference: Optional[str] = Field(None, max_length=50)


class OrderResponse(BaseModel):
    id: int
    item_id: int
    store_id: int
    item_title: str
    buyer_name: str
    buyer_ig: str
    buyer_phone: str
    address_line: str
    pincode: str
    city: str
    state: str
    shipping_fee_inr: float
    total_amount_inr: float
    payment_status: str
    utr_reference: Optional[str]
    created_at: datetime
    whatsapp_supplier_url: Optional[str] = None

    model_config = {"from_attributes": True}
