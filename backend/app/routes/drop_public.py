"""
Public Drop & Checkout Endpoints (Instagram In-App Browser Facing).

Zero-auth buyer endpoints for:
- Viewing active drops and live item availability
- Claiming an item (10-minute atomic lock)
- Generating direct P2P UPI payment intent
- Completing ship-now checkout with address & UTR
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.database.models import Drop, DropItem, Store
from backend.app.schemas.drop import (
    ClaimRequest,
    ClaimResponse,
    CheckoutRequest,
    DropResponse,
    DropItemResponse,
    OrderResponse,
)
from backend.app.services.drop_service import (
    build_upi_intent_uri,
    claim_item,
    execute_checkout,
    release_expired_reservations,
    to_naive_utc,
    utcnow,
)

router = APIRouter(prefix="/public", tags=["Public Instagram Drop Front"])


@router.get("/drop/{slug}", response_model=DropResponse)
def get_public_drop(slug: str, db: Session = Depends(get_db)):
    """
    Public endpoint loaded when buyer taps the Instagram bio or story link.
    Auto-releases expired reservations so inventory is always fresh.
    """
    drop = db.query(Drop).filter(Drop.slug == slug).first()
    if not drop:
        # Also try finding by store slug
        store = db.query(Store).filter(Store.slug == slug).first()
        if store and store.drops:
            drop = store.drops[0]

    if not drop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drop '{slug}' not found.",
        )

    # Check if all items are sold out to auto-update status
    if drop.status == "live":
        unsold = [i for i in drop.items if i.status != "sold"]
        if len(drop.items) > 0 and len(unsold) == 0:
            drop.status = "sold_out"
            db.commit()

    store = drop.store
    now = utcnow()

    items_payload = []
    for item in drop.items:
        items_payload.append(
            DropItemResponse(
                id=item.id,
                drop_id=item.drop_id,
                title=item.title,
                aesthetic=item.aesthetic,
                category=item.category,
                size_label=item.size_label,
                chest_inches=item.chest_inches,
                length_inches=item.length_inches,
                price_inr=item.price_inr,
                condition_score=item.condition_score,
                photo_url=item.photo_url,
                stock_units=item.stock_units or 1,
                available_units=item.available_units if item.available_units is not None else (item.stock_units or 1),
                status=item.status,
                reserved_until=None,
                seconds_remaining=0,
                created_at=item.created_at,
            )
        )

    return DropResponse(
        id=drop.id,
        store_id=store.id,
        title=drop.title,
        slug=drop.slug,
        status=drop.status,
        created_at=drop.created_at,
        store_name=store.name,
        instagram_handle=store.instagram_handle,
        upi_id=store.upi_id,
        flat_shipping_fee=store.flat_shipping_fee,
        items=items_payload,
    )


@router.post("/items/{item_id}/claim", response_model=ClaimResponse)
def claim_drop_item(
    item_id: int,
    payload: ClaimRequest,
    db: Session = Depends(get_db),
):
    """
    Buyer claims an item. Locks the piece atomically for 10 minutes.
    Returns the direct P2P UPI URI pre-filled with total amount (price + shipping).
    """
    try:
        item, seconds_remaining = claim_item(
            db=db,
            item_id=item_id,
            buyer_phone=payload.buyer_phone,
            lock_minutes=10,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    store = item.drop.store
    shipping_fee = store.flat_shipping_fee or 70.0
    total_amount = float(item.price_inr) + float(shipping_fee)

    upi_uri = build_upi_intent_uri(
        upi_id=store.upi_id,
        store_name=store.name,
        amount=total_amount,
        item_id=item.id,
        item_title=item.title,
    )

    return ClaimResponse(
        success=True,
        message="Item ready for payment with pre-filled price.",
        item_id=item.id,
        status=item.status,
        seconds_remaining=0,
        upi_intent_uri=upi_uri,
        flat_shipping_fee=shipping_fee,
        total_amount_inr=total_amount,
    )


@router.post("/items/{item_id}/checkout", response_model=OrderResponse)
def checkout_drop_item(
    item_id: int,
    payload: CheckoutRequest,
    db: Session = Depends(get_db),
):
    """
    Buyer submits shipping details and 12-digit UTR to lock the purchase.
    Item transitions permanently to SOLD.
    """
    try:
        order = execute_checkout(
            db=db,
            item_id=item_id,
            buyer_name=payload.buyer_name,
            buyer_ig=payload.buyer_ig,
            buyer_phone=payload.buyer_phone,
            address_line=payload.address_line,
            pincode=payload.pincode,
            city=payload.city,
            state=payload.state,
            utr_reference=payload.utr_reference,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return OrderResponse(
        id=order.id,
        item_id=order.item_id,
        store_id=order.store_id,
        item_title=order.item.title if order.item else "Garment",
        buyer_name=order.buyer_name,
        buyer_ig=order.buyer_ig,
        buyer_phone=order.buyer_phone,
        address_line=order.address_line,
        pincode=order.pincode,
        city=order.city,
        state=order.state,
        shipping_fee_inr=order.shipping_fee_inr,
        total_amount_inr=order.total_amount_inr,
        payment_status=order.payment_status,
        utr_reference=order.utr_reference,
        created_at=order.created_at,
    )
