"""
Seller Business Profile & Dashboard Routes.

Endpoints for one-time business setup and seller dashboard data.
"""

from __future__ import annotations

import re
import secrets
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from backend.app.database.connection import get_db
from backend.app.database.models import User, Store, Drop, DropItem, Order
from backend.app.schemas.business import BusinessSetupRequest, BusinessProfileResponse
from backend.app.services.auth_service import require_current_user

router = APIRouter(prefix="/business", tags=["Business"])


def _generate_slug(name: str) -> str:
    """Generate a URL-friendly slug from a business name."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not slug:
        slug = "store"
    slug = f"{slug}-{secrets.token_hex(3)}"
    return slug


@router.get("/profile", response_model=Optional[BusinessProfileResponse])
def get_business_profile(
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """Get the authenticated seller's business profile (store), or null if not set up."""
    store = db.query(Store).filter(Store.user_id == current_user.id).first()
    if not store:
        return None
    return store


@router.post("/profile", response_model=BusinessProfileResponse, status_code=status.HTTP_201_CREATED)
def create_or_update_business_profile(
    data: BusinessSetupRequest,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """Create or update the seller's business profile (store)."""
    store = db.query(Store).filter(Store.user_id == current_user.id).first()

    if store:
        # Update existing store
        store.name = data.business_name
        store.instagram_handle = data.instagram_handle
        store.upi_id = data.upi_id
        store.flat_shipping_fee = data.flat_shipping_fee
        store.fulfillment_type = data.fulfillment_type
        store.supplier_phone = data.supplier_phone
        store.niche = data.niche
        store.city = data.city
    else:
        # Create new store linked to user
        slug = _generate_slug(data.business_name)
        # Ensure uniqueness
        while db.query(Store).filter(Store.slug == slug).first():
            slug = _generate_slug(data.business_name)

        store = Store(
            user_id=current_user.id,
            name=data.business_name,
            slug=slug,
            instagram_handle=data.instagram_handle,
            upi_id=data.upi_id,
            phone="",  # Not collecting personal WhatsApp
            flat_shipping_fee=data.flat_shipping_fee,
            fulfillment_type=data.fulfillment_type,
            supplier_phone=data.supplier_phone,
            niche=data.niche,
            city=data.city,
        )
        db.add(store)

    # Mark user onboarding as fully completed in database
    current_user.onboarding_status = "completed"
    db.commit()
    db.refresh(store)
    return store


@router.get("/dashboard")
def get_dashboard_data(
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """Get the seller's dashboard: store info, live drops, previous drops, recent orders, revenue."""
    store = db.query(Store).filter(Store.user_id == current_user.id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found. Complete setup first.",
        )

    # Fetch all drops with items eagerly loaded
    drops = (
        db.query(Drop)
        .filter(Drop.store_id == store.id)
        .options(joinedload(Drop.items))
        .order_by(Drop.created_at.desc())
        .all()
    )

    live_drops = []
    previous_drops = []

    for drop in drops:
        total_items = len(drop.items)
        claimed_items = sum(1 for i in drop.items if i.status in ("reserved", "sold"))
        total_revenue = sum(i.price_inr for i in drop.items if i.status == "sold")
        clearance_pct = round((claimed_items / total_items * 100), 1) if total_items > 0 else 0

        drop_data = {
            "id": drop.id,
            "title": drop.title,
            "slug": drop.slug,
            "status": drop.status,
            "created_at": drop.created_at.isoformat() if drop.created_at else None,
            "total_items": total_items,
            "claimed_items": claimed_items,
            "clearance_pct": clearance_pct,
            "revenue": total_revenue,
        }

        if drop.status == "live":
            live_drops.append(drop_data)
        else:
            previous_drops.append(drop_data)

    # Recent orders (bulk fetched to prevent N+1 query latency over cloud DB)
    recent_orders = (
        db.query(Order)
        .filter(Order.store_id == store.id)
        .order_by(Order.created_at.desc())
        .limit(20)
        .all()
    )

    item_ids = [order.item_id for order in recent_orders if order.item_id]
    items_map = {}
    if item_ids:
        items = db.query(DropItem).filter(DropItem.id.in_(item_ids)).all()
        items_map = {item.id: item for item in items}

    orders_data = []
    for order in recent_orders:
        item = items_map.get(order.item_id)
        orders_data.append({
            "id": order.id,
            "buyer_name": order.buyer_name,
            "buyer_ig": order.buyer_ig,
            "item_title": item.title if item else "Unknown",
            "total_amount": order.total_amount_inr,
            "payment_status": order.payment_status,
            "utr_reference": order.utr_reference,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "city": order.city,
            "state": order.state,
        })

    # Aggregated revenue
    total_revenue = sum(
        o.total_amount_inr for o in db.query(Order).filter(
            Order.store_id == store.id,
            Order.payment_status == "verified"
        ).all()
    )

    return {
        "store": {
            "id": store.id,
            "name": store.name,
            "slug": store.slug,
            "instagram_handle": store.instagram_handle,
            "upi_id": store.upi_id,
            "flat_shipping_fee": store.flat_shipping_fee,
            "fulfillment_type": store.fulfillment_type,
            "niche": store.niche,
            "city": store.city,
        },
        "live_drops": live_drops,
        "previous_drops": previous_drops,
        "recent_orders": orders_data,
        "total_verified_revenue": total_revenue,
    }
