"""
Seller Drop Management & Operations Endpoints.

Enables the seller to:
- Configure store settings & direct UPI ID
- Create drops & quick-upload items in 30 seconds (with auto-aesthetic classifier)
- Manage live orders and verify UTR payments
- 1-Click Shiprocket CSV export (Stockists)
- 1-Click WhatsApp Supplier forward links (Resellers)
- Live Sourcing Card (powered by data_engine/social_curation)
"""

from __future__ import annotations

import io
import os
import uuid
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, File, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.database.models import Drop, DropItem, Order, Store, User
from backend.app.services.auth_service import require_current_user
from backend.app.services.tenant_service import get_user_store, get_user_drop, get_user_order
from backend.app.schemas.drop import (
    DropCreate,
    DropItemCreate,
    DropItemResponse,
    DropResponse,
    OrderResponse,
    StoreCreate,
    StoreResponse,
)
from backend.app.services.drop_service import (
    generate_shiprocket_csv,
    generate_supplier_whatsapp_url,
    release_expired_reservations,
    update_drop_status,
    to_naive_utc,
    utcnow,
)
from data_engine.social_curation.aesthetics import classify_aesthetic

router = APIRouter(prefix="/seller", tags=["Seller Drop Operations"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload-image")
async def upload_item_image(
    file: UploadFile = File(...),
    current_user: User = Depends(require_current_user),
):
    """Upload product photo from local device storage."""
    ext = os.path.splitext(file.filename or "")[1].lower() or ".jpg"
    filename = f"piece_{uuid.uuid4().hex[:12]}{ext}"
    dest_path = os.path.join(UPLOAD_DIR, filename)
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"url": f"/uploads/{filename}", "filename": filename}


class DropStatusUpdate(BaseModel):
    status: str  # "live", "closed", "sold_out", "archived"


def _get_or_create_store_for_user(db: Session, current_user: User) -> Store:
    """Helper to fetch or create a store tied strictly to the authenticated user."""
    store = db.query(Store).filter(Store.user_id == current_user.id).first()
    if store:
        return store

    # Create a new isolated store for this user
    store = Store(
        user_id=current_user.id,
        name=f"{current_user.full_name or 'Curated'} Brand",
        slug=f"store-{current_user.id}",
        instagram_handle="brand.curator",
        upi_id="brand@okaxis",
        phone="9876543210",
        fulfillment_type="self",
        flat_shipping_fee=70.0,
        niche="Curated Vintage Thrift",
        city="Delhi NCR",
        policies="All sales final for curated items unless damaged in transit.",
        created_at=utcnow(),
    )
    db.add(store)
    db.commit()
    db.refresh(store)
    return store


_get_or_create_default_store = _get_or_create_store_for_user


@router.get("/store", response_model=StoreResponse)
def get_store(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """Retrieve seller's store profile tied to their account."""
    return _get_or_create_store_for_user(db, current_user)


@router.post("/store", response_model=StoreResponse)
def update_store(
    payload: StoreCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """Create or update store details, UPI handle, and fulfillment mode."""
    store = _get_or_create_store_for_user(db, current_user)


    if current_user and not store.user_id:
        store.user_id = current_user.id

    store.name = payload.name
    store.slug = payload.slug
    store.instagram_handle = payload.instagram_handle.lstrip("@")
    store.upi_id = payload.upi_id
    store.phone = payload.phone
    store.fulfillment_type = payload.fulfillment_type
    store.supplier_phone = payload.supplier_phone
    store.flat_shipping_fee = payload.flat_shipping_fee
    store.niche = payload.niche or "Curated Vintage Thrift"
    store.city = payload.city or "Delhi"
    store.policies = payload.policies

    db.commit()
    db.refresh(store)
    return store


@router.post("/drops", response_model=DropResponse)
def create_drop(
    payload: DropCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """Create a new drop batch for an upcoming Instagram Reel."""
    store = _get_or_create_store_for_user(db, current_user)
    drop = Drop(
        store_id=store.id,
        title=payload.title,
        slug=payload.slug,
        status="live",
        created_at=utcnow(),
    )
    db.add(drop)
    db.commit()
    db.refresh(drop)

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
        items=[],
    )


@router.get("/drops", response_model=List[DropResponse])
def list_drops(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """List all drops with their items and real-time statuses."""
    store = _get_or_create_store_for_user(db, current_user)
    release_expired_reservations(db)

    drops = db.query(Drop).filter(Drop.store_id == store.id).order_by(Drop.created_at.desc()).all()
    now = utcnow()

    response = []
    for d in drops:
        items_payload = []
        for item in d.items:
            sec_rem = None
            reserved_dt = to_naive_utc(item.reserved_until)
            if item.status == "reserved" and reserved_dt:
                sec_rem = max(0, int((reserved_dt - now).total_seconds()))

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
                    stock_units=getattr(item, "stock_units", 1) or 1,
                    available_units=getattr(item, "available_units", 1) if getattr(item, "available_units", 1) is not None else 1,
                    status=item.status,
                    reserved_until=item.reserved_until,
                    seconds_remaining=sec_rem,
                    created_at=item.created_at,
                )
            )

        response.append(
            DropResponse(
                id=d.id,
                store_id=store.id,
                title=d.title,
                slug=d.slug,
                status=d.status,
                created_at=d.created_at,
                store_name=store.name,
                instagram_handle=store.instagram_handle,
                upi_id=store.upi_id,
                flat_shipping_fee=store.flat_shipping_fee,
                items=items_payload,
            )
        )
    return response


@router.patch("/drops/{drop_id}/status")
def change_drop_status(
    drop_id: int,
    payload: DropStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """Manually open or close a drop link."""
    valid_statuses = {"live", "closed", "sold_out", "archived"}
    if payload.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{payload.status}'. Must be one of: {valid_statuses}",
        )
    drop = get_user_drop(db, drop_id, current_user)
    drop.status = payload.status
    db.commit()
    db.refresh(drop)
    return {"success": True, "drop_id": drop.id, "status": drop.status}


@router.post("/drops/{drop_id}/items", response_model=DropItemResponse)
def add_item_to_drop(
    drop_id: int,
    payload: DropItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """
    30-second quick item lister.
    Automatically classifies aesthetic (Y2K, Grunge, Gorpcore, etc.) from title!
    """
    drop = get_user_drop(db, drop_id, current_user)

    # Automatic aesthetic classifier from your data_engine
    aesthetic_info = classify_aesthetic(payload.title)
    detected_aesthetic = aesthetic_info.get("aesthetic", "Vintage Streetwear")

    stock = max(1, payload.stock_units if payload.stock_units is not None else 1)
    item = DropItem(
        drop_id=drop.id,
        title=payload.title,
        aesthetic=detected_aesthetic,
        category=payload.category or "Apparel",
        size_label=payload.size_label or "Free Size",
        chest_inches=payload.chest_inches,
        length_inches=payload.length_inches,
        price_inr=payload.price_inr,
        condition_score=payload.condition_score or "10/10",
        photo_url=payload.photo_url,
        stock_units=stock,
        available_units=stock,
        status="available",
        created_at=utcnow(),
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return DropItemResponse(
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
        stock_units=item.stock_units,
        available_units=item.available_units,
        status=item.status,
        created_at=item.created_at,
    )


@router.delete("/drops/{drop_id}/items/{item_id}")
def delete_drop_item(
    drop_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """Remove a piece from the drop."""
    drop = get_user_drop(db, drop_id, current_user)
    item = db.query(DropItem).filter(DropItem.id == item_id, DropItem.drop_id == drop.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")
    db.delete(item)
    db.commit()
    return {"success": True, "deleted_id": item_id}


@router.get("/orders", response_model=List[OrderResponse])
def list_seller_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """List all orders with customer details and 1-click supplier forward URLs."""
    store = _get_or_create_store_for_user(db, current_user)
    orders = (
        db.query(Order)
        .filter(Order.store_id == store.id)
        .order_by(Order.created_at.desc())
        .all()
    )

    results = []
    for o in orders:
        wa_url = None
        if store.fulfillment_type == "supplier" and store.supplier_phone and o.item:
            wa_url = generate_supplier_whatsapp_url(
                supplier_phone=store.supplier_phone,
                order=o,
                item=o.item,
            )

        results.append(
            OrderResponse(
                id=o.id,
                item_id=o.item_id,
                store_id=o.store_id,
                item_title=o.item.title if o.item else "Garment",
                buyer_name=o.buyer_name,
                buyer_ig=o.buyer_ig,
                buyer_phone=o.buyer_phone,
                address_line=o.address_line,
                pincode=o.pincode,
                city=o.city,
                state=o.state,
                shipping_fee_inr=o.shipping_fee_inr,
                total_amount_inr=o.total_amount_inr,
                payment_status=o.payment_status,
                utr_reference=o.utr_reference,
                created_at=o.created_at,
                whatsapp_supplier_url=wa_url,
            )
        )
    return results


@router.post("/orders/{order_id}/verify", response_model=OrderResponse)
def verify_order_payment(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """1-tap payment verification by seller."""
    order = get_user_order(db, order_id, current_user)

    order.payment_status = "verified"
    db.commit()
    db.refresh(order)

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


@router.get("/export/shiprocket")
def export_shiprocket_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """Direct CSV download of all orders formatted for Shiprocket bulk upload."""
    store = _get_or_create_store_for_user(db, current_user)
    orders = db.query(Order).filter(Order.store_id == store.id).all()

    csv_data = generate_shiprocket_csv(orders)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=shiprocket_orders_{store.slug}.csv"
        },
    )


@router.get("/sourcing-card")
def get_sourcing_intelligence_card(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """
    Live 'What to Thrift Next' procurement card.
    Analyzes which aesthetics and sizes sold out fastest!
    """
    store = _get_or_create_store_for_user(db, current_user)
    sold_items = (
        db.query(DropItem)
        .join(Drop)
        .filter(Drop.store_id == store.id, DropItem.status == "sold")
        .all()
    )

    if not sold_items:
        return {
            "status": "pending_sales",
            "message": "Complete your first drop to unlock live sourcing intelligence!",
            "top_aesthetic": "Y2K / Vintage Streetwear",
            "top_size": "L (Chest 42)",
            "action_advice": "Source oversized vintage graphic tees and Y2K aesthetic tops for your next drop.",
        }

    # Group by aesthetic
    aesthetic_counts = {}
    size_counts = {}
    total_rev = 0.0

    for it in sold_items:
        aesthetic_counts[it.aesthetic] = aesthetic_counts.get(it.aesthetic, 0) + 1
        size_counts[it.size_label] = size_counts.get(it.size_label, 0) + 1
        total_rev += it.price_inr

    top_aesthetic = max(aesthetic_counts, key=aesthetic_counts.get)
    top_size = max(size_counts, key=size_counts.get)

    return {
        "status": "active",
        "total_items_sold": len(sold_items),
        "total_revenue_inr": total_rev,
        "top_aesthetic": top_aesthetic,
        "top_size": top_size,
        "action_advice": (
            f"High sell-through rate detected for '{top_aesthetic}' in '{top_size}'. "
            f"Prioritize this category during your next flea market/wholesale run."
        ),
    }
