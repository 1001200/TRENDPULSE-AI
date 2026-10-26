import uuid
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from backend.app.pipeline.detector import detect_column_mappings
from backend.app.pipeline.cleaner import (
    clean_currency_and_number,
    clean_quantity,
    clean_date,
    clean_size,
    clean_product_name,
    validate_price_range,
    infer_category_and_aesthetic
)
from backend.app.pipeline.audit import AuditLedger
from backend.app.models.models import (
    Product, SaleOrder, InventoryItem, ContentItem,
    CustomerInquiry, DataQualityLog
)


def _generate_sku(category: str, idx: int) -> str:
    """Generate a human-readable SKU with category prefix."""
    prefix_map = {
        "Tops": "TOP",
        "Bottoms": "BTM",
        "Dresses": "DRS",
        "Outerwear": "OUT",
        "Uncategorized": "SKU",
    }
    prefix = prefix_map.get(category, "SKU")
    return f"{prefix}-{idx:04d}"


def process_and_normalize_records(
    rows: List[Dict[str, Any]],
    db: Session,
    source_name: str = "Uploaded Spreadsheet"
) -> Tuple[Dict[str, Any], int]:
    """
    Ingests arbitrary tabular rows, detects columns, executes non-destructive cleaning,
    logs every mutation into an audit ledger, and saves standardized entities into the database.
    """
    if not rows:
        return {"error": "Empty dataset provided"}, 0

    batch_id = f"batch_{uuid.uuid4().hex[:8]}"
    ledger = AuditLedger(batch_id=batch_id, source_name=source_name)
    ledger.set_total_rows(len(rows))

    # 1. Detect column mapping
    sample_cols = list(rows[0].keys())
    col_map = detect_column_mappings(sample_cols)

    saved_products = 0
    saved_sales = 0
    saved_content = 0
    saved_inquiries = 0

    # Track seen orders for dedup
    seen_order_keys = set()

    for idx, row in enumerate(rows, start=1):
        # Extract row fields using detected column mappings
        def get_val(key: str) -> Any:
            src_col = col_map.get(key)
            return row.get(src_col) if src_col else None

        raw_name = get_val("product_name")
        raw_id = get_val("product_id")
        raw_order = get_val("order_id")
        raw_price = get_val("retail_price")
        raw_cost = get_val("cost_price")
        raw_qty = get_val("quantity")
        raw_date = get_val("sale_date")
        raw_listing_date = get_val("listing_date")
        raw_cat = get_val("category")
        raw_aes = get_val("aesthetic")
        raw_size = get_val("size")
        raw_channel = get_val("channel")
        raw_customer = get_val("customer")
        raw_status = get_val("sale_status")
        raw_views = get_val("views")
        raw_saves = get_val("saves")
        raw_likes = get_val("likes")
        raw_shares = get_val("shares")
        raw_discount = get_val("discount")
        raw_brand = get_val("brand")
        raw_inquiry_type = get_val("inquiry_type")
        raw_outcome = get_val("outcome")
        raw_notes = get_val("notes")

        # Skip completely empty rows
        if not raw_name and not raw_price and not raw_id and not raw_views:
            ledger.log_skip(idx, "Completely blank or malformed record")
            continue

        # Clean Product Title & ID
        cleaned_name, name_note = clean_product_name(raw_name)
        if not cleaned_name:
            cleaned_name = f"Curated Piece #{idx}"
            ledger.log(
                row_idx=idx,
                column="product_name",
                original_val=raw_name,
                cleaned_val=cleaned_name,
                issue="Missing product name",
                action_taken=f"Generated fallback title '{cleaned_name}'",
                severity="WARNING",
                rule_name="missing_product_name"
            )
        elif name_note:
            ledger.log(idx, "product_name", raw_name, cleaned_name, "Name formatting", name_note, "INFO", "clean_product_name")

        # Clean Numbers (Prices and COGS)
        retail_price, p_note = clean_currency_and_number(raw_price)
        if p_note:
            ledger.log(idx, "price", raw_price, retail_price, "Currency / number formatting issue", p_note, "INFO", "currency_strip")
        if retail_price is None or retail_price <= 0:
            ledger.log(idx, "price", raw_price, 0.0, "Invalid retail price", "Invalid or missing price flagged", "ERROR", "invalid_price")
            retail_price = 0.0

        # Validate price range
        if retail_price > 0:
            price_valid, price_warning = validate_price_range(retail_price, "retail")
            if price_warning:
                ledger.log(idx, "price", retail_price, retail_price, "Price range check", price_warning, "WARNING", "price_range_check")

        cost_price, c_note = clean_currency_and_number(raw_cost)
        if c_note:
            ledger.log(idx, "cost_price", raw_cost, cost_price, "COGS formatting issue", c_note, "INFO", "currency_strip")
        if cost_price is None or cost_price < 0:
            cost_price = round(retail_price * 0.35, 2)
            ledger.log(
                idx, "cost_price", raw_cost, cost_price,
                "Missing COGS wholesale cost",
                f"Estimated wholesale cost at standard 35% benchmark ({cost_price})",
                "INFO",
                "estimate_cogs"
            )

        # Infer category and aesthetic first
        category_cleaned, aesthetic_cleaned, inf_note = infer_category_and_aesthetic(
            cleaned_name, given_cat=raw_cat, given_aes=raw_aes
        )
        if inf_note:
            ledger.log(idx, "category/aesthetic", f"cat={raw_cat}, aes={raw_aes}", f"{category_cleaned} / {aesthetic_cleaned}", "Missing taxonomy", inf_note, "INFO", "infer_taxonomy")

        # Clean Size
        size_cleaned, s_note = clean_size(raw_size)
        if s_note:
            ledger.log(idx, "size", raw_size, size_cleaned, "Size inconsistency", s_note, "INFO", "size_normalize")

        # Generate product ID (deterministic slug if not provided)
        import re as re_mod
        clean_slug = re_mod.sub(r'[^A-Z0-9]+', '-', f"{category_cleaned}-{cleaned_name}-{size_cleaned}".upper()).strip('-')
        product_id = str(raw_id).strip() if raw_id and str(raw_id).strip().lower() not in ("none", "nan", "") else clean_slug

        # Clean Quantity & Date
        quantity, q_note = clean_quantity(raw_qty)
        if q_note:
            ledger.log(idx, "quantity", raw_qty, quantity, "Quantity issue", q_note, "INFO", "quantity_normalize")

        sale_dt, dt_note = clean_date(raw_date)
        if not sale_dt:
            ledger.log(idx, "date", raw_date, "NULL", "Invalid date", "Could not parse transaction date", "ERROR", "invalid_date")

        listing_dt = None
        if raw_listing_date:
            listing_dt, _ = clean_date(raw_listing_date)
        stock_dt = listing_dt or sale_dt or datetime.utcnow()

        # Clean discount
        discount, disc_note = clean_currency_and_number(raw_discount)
        if disc_note:
            ledger.log(idx, "discount", raw_discount, discount, "Discount formatting", disc_note, "INFO", "currency_strip")
        discount = discount if discount is not None and discount >= 0 else 0.0

        # Clean brand
        brand = str(raw_brand).strip() if raw_brand and str(raw_brand).lower() not in ("nan", "none", "") else "Vintage / Thrift"

        # Clean status
        sale_status = str(raw_status).strip().lower() if raw_status and str(raw_status).strip().lower() not in ("nan", "none", "") else "completed"

        # Validate order ID
        if not raw_order or str(raw_order).strip().lower() in ("", "[blank]", "none", "nan", "blank"):
            order_id = None
            ledger.log(idx, "order_id", raw_order, "NULL", "Missing order ID", "Missing required transaction identifier", "ERROR", "missing_order_id")
        else:
            order_id = str(raw_order).strip()

        # Deduplication check
        row_key = f"{product_id}|{sale_dt.date() if sale_dt else ''}|{str(raw_customer).strip() if raw_customer else ''}|{order_id or idx}"
        is_duplicate = row_key in seen_order_keys
        if is_duplicate:
            ledger.log(
                idx, "Row", row_key, "FLAGGED_DUPLICATE",
                "Possible duplicate order",
                f"Same product+date+customer combination as a previous row",
                "WARNING",
                "duplicate_detection"
            )
        seen_order_keys.add(row_key)

        # 2. Database Upsert / Save
        # A. Product Entity
        existing_product = db.query(Product).filter(Product.product_id == product_id).first()
        if not existing_product:
            product = Product(
                product_id=product_id,
                product_name=cleaned_name,
                category=category_cleaned,
                brand=brand,
                aesthetic=aesthetic_cleaned,
                size=size_cleaned,
                condition="Gently Used",
                cost_price=cost_price,
                retail_price=retail_price,
                source_file=source_name,
                source_row_idx=idx,
                date_sourced=listing_dt,
                created_at=stock_dt
            )
            db.add(product)
            db.flush()

            # B. Inventory Entity
            inv_item = InventoryItem(
                product_id=product_id,
                quantity_on_hand=max(0, (quantity or 1) - 1 if (quantity or 1) > 0 else 0),
                date_stocked=stock_dt,
                status="Sold" if (quantity or 1) >= 1 else "Available"
            )
            db.add(inv_item)
            saved_products += 1

        # C. Sale Order Entity (only if price > 0, qty > 0, valid date, valid order_id, and not exact duplicate)
        if retail_price > 0 and quantity is not None and quantity > 0 and sale_dt and order_id and not is_duplicate:
            order = SaleOrder(
                order_id=order_id,
                product_id=product_id,
                sale_date=sale_dt,
                quantity=quantity,
                selling_price=retail_price,
                discount_amount=discount,
                channel=str(raw_channel).strip() if raw_channel else "Instagram DM",
                customer_identifier=str(raw_customer).strip() if raw_customer else f"@buyer_{idx}",
                inquiry_type=str(raw_inquiry_type).strip() if raw_inquiry_type else "DM",
                sale_status=sale_status,
                notes=str(raw_notes).strip() if raw_notes and str(raw_notes).lower() not in ("nan", "none", "") else ""
            )
            db.add(order)
            saved_sales += 1

        # D. Content / Reel Entity if view metrics exist in row
        views_num, _ = clean_currency_and_number(raw_views)
        saves_num, _ = clean_currency_and_number(raw_saves)
        likes_num, _ = clean_currency_and_number(raw_likes)
        shares_num, _ = clean_currency_and_number(raw_shares)

        if views_num is not None and views_num > 0:
            content_id = f"reel_{uuid.uuid4().hex[:6]}"
            content = ContentItem(
                content_id=content_id,
                platform="Instagram",
                content_type="Reel",
                content_url=f"https://instagram.com/reel/{content_id}",
                posted_at=sale_dt,
                views=int(views_num),
                likes=int(likes_num or 0),
                saves=int(saves_num or 0),
                shares=int(shares_num or 0),
                linked_product_ids=[product_id],
                product_tags_count=1
            )
            db.add(content)
            saved_content += 1

        # E. Customer Inquiry Entity if outcome data exists
        if raw_outcome and str(raw_outcome).lower() not in ("nan", "none", ""):
            inquiry = CustomerInquiry(
                product_id=product_id,
                inquiry_date=sale_dt,
                inquiry_type=str(raw_inquiry_type).strip() if raw_inquiry_type else "DM",
                customer_identifier=str(raw_customer).strip() if raw_customer else f"@user_{idx}",
                outcome=str(raw_outcome).strip(),
                notes=str(raw_notes).strip() if raw_notes and str(raw_notes).lower() not in ("nan", "none", "") else ""
            )
            db.add(inquiry)
            saved_inquiries += 1

    # 3. Save Data Quality Log
    summary = ledger.to_summary_dict()
    quality_log = DataQualityLog(
        batch_id=batch_id,
        source_name=source_name,
        total_rows=summary["total_rows"],
        valid_rows=summary["valid_rows"],
        flagged_rows=summary["flagged_rows"],
        skipped_rows=summary["skipped_rows"],
        mutations_count=summary["mutations_count"],
        info_count=summary["info_count"],
        warning_count=summary["warning_count"],
        error_count=summary["error_count"],
        quality_score=summary["quality_score"],
        audit_trail_json=summary["audit_trail"],
        cleaning_rules_applied=summary["cleaning_rules_applied"]
    )
    db.add(quality_log)
    db.commit()

    summary["saved_entities"] = {
        "products": saved_products,
        "sales": saved_sales,
        "content_items": saved_content,
        "inquiries": saved_inquiries
    }
    return summary, saved_products
