"""
TrendPulse Drop & DM Closing Business Logic Service.

Handles:
- Atomic 10-minute item claims & auto-expiration
- Zero-custody UPI deep link generation (P2P direct)
- Ship-now checkout execution
- 1-Click Shiprocket / Delhivery CSV formatting
- 1-Click WhatsApp Supplier forward message generation
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import io
import csv
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote
from sqlalchemy.orm import Session

from backend.app.database.models import Drop, DropItem, Order, Store


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def release_expired_reservations(db: Session, drop_id: Optional[int] = None) -> int:
    """
    Auto-release any items whose 10-minute reservation timer has expired.
    Returns the number of released items.
    """
    now = utcnow()
    query = db.query(DropItem).filter(
        DropItem.status == "reserved",
        DropItem.reserved_until.isnot(None),
        DropItem.reserved_until < now,
    )
    if drop_id is not None:
        query = query.filter(DropItem.drop_id == drop_id)

    expired_items = query.all()
    count = len(expired_items)
    for item in expired_items:
        item.status = "available"
        item.reserved_until = None
        item.reserved_by_phone = None

    if count > 0:
        db.commit()
    return count


def claim_item(
    db: Session,
    item_id: int,
    buyer_phone: str,
    lock_minutes: int = 0,
) -> Tuple[DropItem, int]:
    """
    Check item availability and return item for checkout.
    Stock stays open and buyable until actually purchased.
    """
    item = db.query(DropItem).filter(DropItem.id == item_id).first()
    if not item:
        raise ValueError(f"Item #{item_id} not found.")

    if item.status == "sold":
        raise ValueError(f"Sorry, '{item.title}' has already been sold!")

    # Item remains available until order checkout is completed
    return item, 0


def update_drop_status(db: Session, drop_id: int, new_status: str) -> Drop:
    """Manually update drop status: 'live', 'closed', 'sold_out', or 'archived'."""
    drop = db.query(Drop).filter(Drop.id == drop_id).first()
    if not drop:
        raise ValueError(f"Drop #{drop_id} not found.")
    drop.status = new_status
    db.commit()
    db.refresh(drop)
    return drop


def build_upi_intent_uri(
    upi_id: str,
    store_name: str,
    amount: float,
    item_id: int,
    item_title: str,
) -> str:
    """
    Generate standard NPCI-compliant UPI Intent deep link:
    upi://pay?pa={upi_id}&pn={store_name}&am={amount}&cu=INR&tn={note}
    Pre-fills exact amount so customer never types price manually.
    """
    note = f"Order #{item_id} - {item_title[:20]}"
    encoded_store = quote(store_name)
    encoded_note = quote(note)
    return (
        f"upi://pay?pa={upi_id.strip()}&pn={encoded_store}"
        f"&am={amount:.2f}&cu=INR&tn={encoded_note}"
    )


def execute_checkout(
    db: Session,
    item_id: int,
    buyer_name: str,
    buyer_ig: str,
    buyer_phone: str,
    address_line: str,
    pincode: str,
    city: str,
    state: str,
    utr_reference: Optional[str] = None,
) -> Order:
    """
    Process ship-now checkout:
    1. Verify item availability
    2. Transition item status to 'sold'
    3. Create Order record with UTR
    4. Auto-close drop to 'sold_out' if all items are now sold
    """
    item = db.query(DropItem).filter(DropItem.id == item_id).first()
    if not item:
        raise ValueError(f"Item #{item_id} not found.")

    if item.status == "sold" or (item.available_units is not None and item.available_units <= 0):
        raise ValueError(f"'{item.title}' is already sold out.")

    store = db.query(Store).filter(Store.id == item.drop.store_id).first()
    if not store:
        raise ValueError("Associated store not found.")

    shipping_fee = store.flat_shipping_fee or 70.0
    total_amount = float(item.price_inr) + float(shipping_fee)

    # Check if order already exists for this item by this specific buyer
    existing_order = db.query(Order).filter(
        Order.item_id == item_id,
        Order.buyer_phone == buyer_phone.strip(),
    ).first()
    if existing_order:
        if utr_reference and not existing_order.utr_reference:
            existing_order.utr_reference = utr_reference
            existing_order.payment_status = "pending_verification"
            db.commit()
            db.refresh(existing_order)
        return existing_order

    # Create new order
    order = Order(
        item_id=item.id,
        store_id=store.id,
        buyer_name=buyer_name.strip(),
        buyer_ig=buyer_ig.strip().lstrip("@"),
        buyer_phone=buyer_phone.strip(),
        address_line=address_line.strip(),
        pincode=pincode.strip(),
        city=city.strip(),
        state=state.strip(),
        shipping_fee_inr=shipping_fee,
        total_amount_inr=total_amount,
        payment_status="cod" if (utr_reference and utr_reference.strip().upper() == "COD") else ("pending_verification" if utr_reference else "pending_utr"),
        utr_reference=utr_reference.strip() if utr_reference else None,
        created_at=utcnow(),
    )
    db.add(order)

    # Decrement available units and update status
    curr_available = item.available_units if item.available_units is not None else (item.stock_units or 1)
    new_available = max(0, curr_available - 1)
    item.available_units = new_available
    if new_available <= 0:
        item.status = "sold"
    else:
        item.status = "available"
    item.reserved_until = None
    item.reserved_by_phone = buyer_phone
    db.commit()
    db.refresh(order)

    # Auto-close drop if 100% of items in this drop are sold out
    drop = item.drop
    if drop:
        remaining_items = db.query(DropItem).filter(
            DropItem.drop_id == drop.id,
            DropItem.status != "sold",
        ).count()
        if remaining_items == 0:
            drop.status = "sold_out"
            db.commit()

    return order


def generate_shiprocket_csv(orders: List[Order]) -> str:
    """
    Generate Shiprocket bulk order import CSV.
    Matches standard Shiprocket format:
    Order ID, Order Date, Channel, Customer Name, Mobile, Email,
    Billing Address, Billing City, Billing State, Billing Pincode,
    Product Name, SKU, Quantity, Unit Price, Total, Payment Method
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Shiprocket CSV header
    writer.writerow([
        "Order ID",
        "Order Date",
        "Channel",
        "Customer Name",
        "Mobile",
        "Email",
        "Billing Address",
        "Billing City",
        "Billing State",
        "Billing Pincode",
        "Product Name",
        "SKU",
        "Quantity",
        "Unit Price",
        "Total",
        "Payment Method",
    ])

    for o in orders:
        item = o.item
        item_name = item.title if item else f"Item #{o.item_id}"
        sku = f"TP-{o.store_id}-{o.item_id}"
        order_date = o.created_at.strftime("%Y-%m-%d %H:%M") if o.created_at else ""

        writer.writerow([
            f"ORD-{o.id}",
            order_date,
            "Custom/Instagram",
            o.buyer_name,
            o.buyer_phone,
            f"{o.buyer_ig}@instagram.com",
            o.address_line,
            o.city,
            o.state,
            o.pincode,
            item_name,
            sku,
            1,
            f"{item.price_inr:.2f}" if item else f"{o.total_amount_inr:.2f}",
            f"{o.total_amount_inr:.2f}",
            "COD" if (o.payment_status == "cod" or (o.utr_reference and o.utr_reference.strip().upper() == "COD")) else "Prepaid",
        ])

    return output.getvalue()


def generate_supplier_whatsapp_url(
    supplier_phone: str,
    order: Order,
    item: DropItem,
) -> str:
    """
    Generate 1-click WhatsApp deep link to forward customer address and item info
    directly to the wholesale supplier for dropshipping.
    """
    clean_phone = supplier_phone.replace("+", "").replace(" ", "").replace("-", "")
    if len(clean_phone) == 10:
        clean_phone = "91" + clean_phone

    msg = (
        f"📦 *New Order Dispatch Request*\n\n"
        f"• *Item:* {item.title}\n"
        f"• *Size:* {item.size_label} (Chest: {item.chest_inches}\", Length: {item.length_inches}\")\n"
        f"• *Order Ref:* ORD-{order.id}\n\n"
        f"📍 *Shipping Address:*\n"
        f"{order.buyer_name}\n"
        f"Phone: {order.buyer_phone}\n"
        f"Address: {order.address_line}\n"
        f"{order.city}, {order.state} - {order.pincode}\n\n"
        f"Please dispatch and send tracking number. Thanks!"
    )

    encoded_msg = quote(msg)
    return f"https://wa.me/{clean_phone}?text={encoded_msg}"
