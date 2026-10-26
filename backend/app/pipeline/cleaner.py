import re
from datetime import datetime
from typing import Any, Tuple, Optional, List, Dict


def clean_currency_and_number(val: Any) -> Tuple[Optional[float], Optional[str]]:
    """
    Cleans messy currency numbers: '$1,299.50', '₹ 899', '(100)', '45%'.
    Returns: (cleaned_float, change_note_if_any)
    """
    if val is None:
        return None, None

    val_str = str(val).strip()
    if val_str == "" or val_str.lower() in ("nan", "null", "none", "n/a", "-"):
        return None, None

    original_str = val_str
    note = None

    # Check for accounting negative: (100) -> -100
    is_negative = False
    if val_str.startswith("(") and val_str.endswith(")"):
        is_negative = True
        val_str = val_str[1:-1].strip()
        note = "Converted accounting negative parentheses to negative number"

    # Check for currency symbols & separators (including ■ prefix)
    cleaned_num = re.sub(r'[■$₹€£,\s]', '', val_str)

    # Check for percentage
    if cleaned_num.endswith('%'):
        cleaned_num = cleaned_num[:-1]
        try:
            num = float(cleaned_num) / 100.0
            return (num if not is_negative else -num), f"Converted percentage {original_str} to decimal ratio {num}"
        except ValueError:
            return None, f"Failed to parse percentage: {original_str}"

    try:
        num = float(cleaned_num)
        if is_negative:
            num = -num
        if cleaned_num != original_str and not note:
            note = f"Stripped formatting/currency from '{original_str}' to {num}"
        return num, note
    except ValueError:
        return None, f"Invalid numeric format: '{original_str}'"


def clean_quantity(val: Any) -> Tuple[Optional[int], Optional[str]]:
    """
    Cleans integer quantities, ensuring valid positive values.
    Returns (quantity, note). If missing or non-positive/invalid, returns (None, note).
    """
    if val is None or str(val).strip().lower() in ("nan", "none", "", "null", "[blank]"):
        return None, "Missing quantity"

    val_str = str(val).strip()
    word_to_num = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
    if val_str.lower() in word_to_num:
        return None, f"Non-numeric text quantity '{val_str}'"

    num, note = clean_currency_and_number(val)
    if num is None:
        return None, f"Invalid quantity format: '{val_str}'"

    qty = int(round(num))
    if qty <= 0:
        return None, f"Non-positive quantity {qty}"

    if str(val).strip() != str(qty):
        return qty, f"Normalized quantity '{val}' to {qty}"
    return qty, None


def clean_date(val: Any) -> Tuple[Optional[datetime], Optional[str]]:
    """
    Parses dates across ISO, DD/MM/YYYY, MM/DD/YYYY, or epoch.
    Returns (datetime, note). If invalid or missing, returns (None, note).
    Does NOT substitute current month/date for transaction records.
    """
    if isinstance(val, datetime):
        return val, None

    if not val or str(val).strip().lower() in ("nan", "none", "", "null", "[blank]"):
        return None, "Missing transaction date"

    val_str = str(val).strip()
    date_formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
        "%b %d, %Y",
        "%d %b %Y",
        "%d-%b-%Y",
        "%Y-%m-%dT%H:%M:%S",
    ]

    for fmt in date_formats:
        try:
            dt = datetime.strptime(val_str, fmt)
            note = None
            if fmt != "%Y-%m-%d":
                note = f"Standardized date format '{val_str}' into ISO datetime"
            return dt, note
        except ValueError:
            continue

    return None, f"Could not parse invalid date '{val_str}'"


def clean_size(val: Any) -> Tuple[str, Optional[str]]:
    """Normalizes clothing sizes (S, M, L, XL, XXL, Free Size)."""
    if not val or str(val).strip().lower() in ("nan", "none", ""):
        return "Free Size", "Defaulted empty size to 'Free Size'"

    s = str(val).strip()
    s_lower = s.lower()

    mapping = {
        "s": "S",
        "small": "S",
        "m": "M",
        "medium": "M",
        "med": "M",
        "l": "L",
        "large": "L",
        "xl": "XL",
        "extra large": "XL",
        "xxl": "XXL",
        "2xl": "XXL",
        "3xl": "XXXL",
        "xs": "XS",
        "extra small": "XS",
        "free": "Free Size",
        "freesize": "Free Size",
        "free size": "Free Size",
        "one size": "Free Size",
        "os": "Free Size"
    }

    if s_lower in mapping:
        cleaned = mapping[s_lower]
        note = f"Normalized size '{s}' to '{cleaned}'" if s != cleaned else None
        return cleaned, note

    return s.upper(), None


def clean_product_name(name: Any) -> Tuple[str, Optional[str]]:
    """
    Cleans product names: strips excess whitespace, normalizes to Title Case.
    """
    if not name or str(name).strip().lower() in ("nan", "none", ""):
        return "", "Missing product name"

    raw = str(name).strip()
    # Collapse multiple spaces
    cleaned = re.sub(r'\s+', ' ', raw)
    # Title case normalization
    title_cased = cleaned.title()

    note = None
    if cleaned != raw:
        note = f"Cleaned whitespace in product name: '{raw}' → '{cleaned}'"
    if title_cased != cleaned and not note:
        note = f"Normalized casing of product name: '{cleaned}' → '{title_cased}'"

    return title_cased, note


def clean_category(val: Any) -> Tuple[str, Optional[str]]:
    """Normalizes clothing category names (strictly clothing only)."""
    if not val or str(val).strip().lower() in ("nan", "none", "", "null"):
        return "Tops", "Missing category defaulted to clothing Tops"

    raw = str(val).strip()
    lower = raw.lower()

    # Non-clothing items / accessories must never enter the clothing category domain
    non_clothing_keywords = [
        "accessor", "jewel", "hat", "cap", "bag", "tote", "belt", "wallet",
        "sock", "shoe", "footwear", "glass", "scarf", "beanie", "ring", "chain"
    ]
    if any(kw in lower for kw in non_clothing_keywords):
        return "Tops", f"Non-clothing item '{raw}' normalized to clothing Tops"

    category_map = {
        "top": "Tops", "tops": "Tops", "tee": "Tops", "tees": "Tops",
        "t-shirt": "Tops", "t-shirts": "Tops", "shirt": "Tops", "shirts": "Tops",
        "blouse": "Tops", "blouses": "Tops", "flannel": "Tops", "tank": "Tops", "polo": "Tops",
        "knitwear": "Knitwear", "cardigan": "Knitwear", "cardigans": "Knitwear", "sweater": "Knitwear", "sweaters": "Knitwear", "knit": "Knitwear",
        "bottom": "Bottoms", "bottoms": "Bottoms", "pants": "Bottoms", "pant": "Bottoms",
        "jeans": "Bottoms", "denim": "Bottoms", "shorts": "Bottoms", "short": "Bottoms",
        "trouser": "Bottoms", "trousers": "Bottoms", "skirt": "Bottoms", "skirts": "Bottoms",
        "cargo": "Bottoms", "cargos": "Bottoms", "sweatpants": "Bottoms", "track pants": "Bottoms",
        "dress": "Dresses", "dresses": "Dresses", "gown": "Dresses", "jumpsuit": "Dresses", "romper": "Dresses",
        "outerwear": "Outerwear", "jacket": "Outerwear", "jackets": "Outerwear",
        "coat": "Outerwear", "coats": "Outerwear", "hoodie": "Outerwear", "hoodies": "Outerwear",
        "sweatshirt": "Outerwear", "sweatshirts": "Outerwear", "blazer": "Outerwear",
        "windbreaker": "Outerwear", "puffer": "Outerwear",
    }

    if lower in category_map:
        cleaned = category_map[lower]
        note = f"Normalized category '{raw}' to '{cleaned}'" if raw != cleaned else None
        return cleaned, note

    # Check partial matching if exact not found
    if any(k in lower for k in ["knitwear", "cardigan", "sweater", "knit"]):
        return "Knitwear", f"Categorized '{raw}' as Knitwear"
    if any(k in lower for k in ["jacket", "coat", "hoodie", "sweatshirt", "blazer", "windbreaker", "puffer", "outerwear"]):
        return "Outerwear", f"Categorized '{raw}' as Outerwear"
    if any(k in lower for k in ["pant", "jean", "denim", "trouser", "skirt", "short", "cargo", "bottom"]):
        return "Bottoms", f"Categorized '{raw}' as Bottoms"
    if any(k in lower for k in ["dress", "gown", "jumpsuit"]):
        return "Dresses", f"Categorized '{raw}' as Dresses"
    if any(k in lower for k in ["shirt", "tee", "top", "blouse", "flannel"]):
        return "Tops", f"Categorized '{raw}' as Tops"

    return "Tops", f"Unrecognized category '{raw}' normalized to clothing Tops"


def validate_price_range(price: Optional[float], context: str = "retail") -> Tuple[bool, Optional[str]]:
    """
    Flags prices outside reasonable thrift clothing range.
    Returns (is_valid, warning_message).
    """
    if price is None:
        return True, None

    if price < 0:
        return False, f"Negative {context} price ({price}) — likely data error"

    if context == "retail":
        if 0 < price < 50:
            return True, f"Unusually low {context} price (₹{price}) — verify this is correct"
        if price > 50000:
            return True, f"Very high {context} price (₹{price:,.0f}) — unusual for thrift/resale"
    elif context == "cost":
        if 0 < price < 10:
            return True, f"Unusually low sourcing cost (₹{price}) — verify"
        if price > 25000:
            return True, f"Very high sourcing cost (₹{price:,.0f}) — unusual for thrift sourcing"

    return True, None


def detect_similar_product_names(names: List[str]) -> List[Tuple[int, int, str]]:
    """
    Simple duplicate product detection using lowercase exact match after stripping.
    Returns list of (idx_a, idx_b, reason) tuples.
    """
    duplicates = []
    normalized = {}
    for idx, name in enumerate(names):
        key = re.sub(r'[\s\-_]+', '', name.lower().strip())
        if key in normalized:
            duplicates.append((normalized[key], idx, f"Possible duplicate: '{names[normalized[key]]}' ≈ '{name}'"))
        else:
            normalized[key] = idx
    return duplicates


def infer_category_and_aesthetic(product_name: str, given_cat: Optional[str] = None, given_aes: Optional[str] = None) -> Tuple[str, str, Optional[str]]:
    """
    Infers apparel category and aesthetic subculture from garment title if unspecified.
    """
    name_lower = str(product_name).lower()
    notes = []

    # Category inference
    cat = None
    if given_cat and str(given_cat).strip().lower() not in ("nan", "none", "", "null"):
        cleaned_cat, cat_note = clean_category(given_cat)
        cat = cleaned_cat
        if cat_note:
            notes.append(cat_note)

    if not cat:
        if any(w in name_lower for w in ["knit", "cardigan", "sweater"]):
            cat = "Knitwear"
        elif any(w in name_lower for w in ["jacket", "coat", "blazer", "hoodie", "bomber", "windbreaker", "puffer"]):
            cat = "Outerwear"
        elif any(w in name_lower for w in ["pant", "cargo", "jeans", "denim", "skirt", "trouser", "shorts", "bottom"]):
            cat = "Bottoms"
        elif any(w in name_lower for w in ["dress", "gown", "sundress", "slip", "maxi", "midi"]):
            cat = "Dresses"
        else:
            cat = "Tops"
        notes.append(f"Inferred clothing category '{cat}' from product title")

    # Aesthetic inference
    aes = given_aes.strip() if given_aes and str(given_aes).lower() not in ("nan", "none", "") else None
    if not aes:
        if any(w in name_lower for w in ["y2k", "rhinestone", "corset", "cyber", "baby tee", "halter", "mesh"]):
            aes = "Y2K"
        elif any(w in name_lower for w in ["vintage", "90s", "retro", "varsity", "80s", "distressed", "grandpa"]):
            aes = "Vintage 90s"
        elif any(w in name_lower for w in ["gorpcore", "parachut", "cargo", "tactical", "utility", "nylon"]):
            aes = "Gorpcore"
        elif any(w in name_lower for w in ["streetwear", "oversized", "graphic", "skate", "boxy", "racing"]):
            aes = "Streetwear"
        elif any(w in name_lower for w in ["grunge", "flannel", "punk", "leather", "biker", "chain"]):
            aes = "Grunge"
        elif any(w in name_lower for w in ["minimal", "linen", "basic", "clean", "classic", "monochrome"]):
            aes = "Minimalist"
        elif any(w in name_lower for w in ["cottagecore", "floral", "prairie", "ruffle", "lace"]):
            aes = "Cottagecore"
        else:
            aes = "Vintage Curated"
        notes.append(f"Inferred aesthetic tag '{aes}' from garment details")

    return cat, aes, ("; ".join(notes) if notes else None)
