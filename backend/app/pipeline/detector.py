import re
from typing import Dict, List, Optional, Tuple

# Standard retail target schema fields and their common synonyms
SYNONYM_MAP: Dict[str, List[str]] = {
    "order_id": [
        "order id", "order no", "order_id", "order_number", "order#", "order num",
        "invoice", "invoice no", "inv no", "transaction id", "trans id", "txn id",
        "receipt id", "order_idx"
    ],
    "product_name": [
        "product", "product name", "item", "item name", "title", "product_name",
        "item_title", "garment", "piece", "product_title", "description",
        "item title", "product title"
    ],
    "product_id": [
        "product id", "sku", "item id", "code", "barcode", "product_id",
        "item_code", "item_no", "sku_code", "sku code", "item no"
    ],
    "category": [
        "category", "type", "garment type", "collection", "apparel category",
        "section", "dept", "department", "apparel type", "garment_type"
    ],
    "aesthetic": [
        "aesthetic", "vibe", "style", "subculture", "trend", "look", "tags"
    ],
    "size": [
        "size", "sizing", "measurement", "chest", "fit", "size_label", "measurements"
    ],
    "condition": [
        "condition", "grade", "quality", "thrift grade", "state", "item_condition"
    ],
    "cost_price": [
        "unit cost", "unit cost (rs.)", "cost price", "cogs", "cost", "wholesale",
        "wholesale price", "buying price", "sourcing cost", "purchase price", "cost_price",
        "est. cost", "estimated cost", "est cost"
    ],
    "retail_price": [
        "unit price", "unit price (rs.)", "price", "retail price", "selling price",
        "mrp", "listing price", "retail_price", "sales value", "sale amount", "amount", "revenue"
    ],
    "quantity": [
        "qty", "quantity", "units", "units sold", "count", "stock",
        "quantity sold", "pcs", "volume"
    ],
    "sale_date": [
        "date", "sale date", "order date", "timestamp", "purchased at",
        "time", "created_at", "sold_at", "sale_date", "order_date"
    ],
    "listing_date": [
        "listing date", "date listed", "stock date", "date stocked", "drop date",
        "drop time", "listing_date", "date_stocked", "drop_date", "drop_time", "listed_at",
        "drop timestamp", "date sourced", "date_sourced"
    ],
    "channel": [
        "channel", "source", "order source", "platform", "sales channel",
        "sales_channel", "order_source", "payment", "payment method", "payment_method", "payment mode"
    ],
    "sale_status": [
        "order status", "sale status", "order_status", "sale_status", "status",
        "payment status", "fulfillment status", "state", "order state"
    ],
    "customer": [
        "customer", "buyer", "handle", "phone", "instagram", "client",
        "buyer handle", "instagram_handle", "buyer_handle", "customer_name"
    ],
    "views": [
        "views", "impressions", "reach", "video views", "reel_views", "reel views"
    ],
    "saves": [
        "saves", "bookmarks", "saved", "reel_saves", "reel saves"
    ],
    "likes": [
        "likes", "hearts", "favorites"
    ],
    "shares": [
        "shares", "sends", "forwards"
    ],
    "inquiry_type": [
        "inquiry type", "inquiry_type", "enquiry type", "contact type",
        "interaction type", "interaction"
    ],
    "outcome": [
        "outcome", "result", "inquiry outcome", "purchase outcome",
        "conversion"
    ],
    "notes": [
        "notes", "comments", "remark", "remarks", "memo"
    ],
    "content_caption": [
        "caption", "content_caption", "content caption", "post caption",
        "reel caption", "description text"
    ],
    "hashtags": [
        "hashtags", "tags", "hash_tags", "hash tags"
    ],
    "discount": [
        "discount", "discount amount", "discount_amount", "disc",
        "discount_pct", "discount pct", "off"
    ],
    "brand": [
        "brand", "label", "brand name", "brand_name", "manufacturer"
    ]
}


def clean_header(header: str) -> str:
    """Standardizes header string for comparison."""
    h = str(header).lower().strip()
    h = re.sub(r'[\s_]+', ' ', h)
    return h


def detect_column_mappings(columns: List[str]) -> Dict[str, Optional[str]]:
    """
    Analyzes incoming table headers and returns a map of:
    { standard_field: original_source_column_name }
    """
    cleaned_source_cols = {clean_header(col): col for col in columns}
    mapped_targets: Dict[str, Optional[str]] = {}
    claimed_exact: set = set()

    # Pass 1: Exact matches
    for standard_field, synonyms in SYNONYM_MAP.items():
        mapped_targets[standard_field] = None
        for syn in synonyms:
            if syn in cleaned_source_cols:
                mapped_targets[standard_field] = cleaned_source_cols[syn]
                claimed_exact.add(cleaned_source_cols[syn])
                break

    # Pass 2: Substring matches for unmapped targets
    for standard_field, synonyms in SYNONYM_MAP.items():
        if mapped_targets[standard_field] is not None:
            continue
        found = False
        for syn in synonyms:
            for clean_src, original_src in cleaned_source_cols.items():
                if original_src in claimed_exact:
                    continue
                if syn in clean_src or (len(clean_src) >= 5 and clean_src in syn):
                    mapped_targets[standard_field] = original_src
                    found = True
                    break
            if found:
                break

    return mapped_targets


def detect_column_mappings_with_confidence(columns: List[str]) -> Dict[str, Dict]:
    """
    Enhanced column detection that returns confidence scores.
    Returns: { standard_field: { "source_col": str|None, "confidence": float, "match_type": str } }
    """
    cleaned_source_cols = {clean_header(col): col for col in columns}
    results: Dict[str, Dict] = {}
    claimed_exact: set = set()

    # Pass 1: Exact matches
    for standard_field, synonyms in SYNONYM_MAP.items():
        best_match = None
        for syn in synonyms:
            if syn in cleaned_source_cols:
                best_match = cleaned_source_cols[syn]
                claimed_exact.add(best_match)
                results[standard_field] = {
                    "source_col": best_match,
                    "confidence": 1.0,
                    "match_type": "exact"
                }
                break
        if not best_match:
            results[standard_field] = {
                "source_col": None,
                "confidence": 0.0,
                "match_type": "none"
            }

    # Pass 2: Substring matches
    for standard_field, synonyms in SYNONYM_MAP.items():
        if results[standard_field]["confidence"] == 1.0:
            continue

        best_match = None
        best_confidence = 0.0
        match_type = "none"

        for syn in synonyms:
            for clean_src, original_src in cleaned_source_cols.items():
                if original_src in claimed_exact:
                    continue
                if syn in clean_src or (len(clean_src) >= 5 and clean_src in syn):
                    if 0.7 > best_confidence:
                        best_match = original_src
                        best_confidence = 0.7
                        match_type = "substring"

        if best_match:
            results[standard_field] = {
                "source_col": best_match,
                "confidence": best_confidence,
                "match_type": match_type
            }

    return results


def get_unmapped_columns(columns: List[str], mapped: Dict[str, Optional[str]]) -> List[str]:
    """Returns columns from the source that were NOT mapped to any standard field."""
    mapped_originals = set(v for v in mapped.values() if v is not None)
    return [col for col in columns if col not in mapped_originals]
