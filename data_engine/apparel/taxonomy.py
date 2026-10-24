"""
TrendPulse Apparel Taxonomy & Title Attribute Extractor.

Extracts rich fashion attributes directly from unstructured product titles:
    - Gender / Department (Men, Women, Unisex, Kids)
    - Macro Category & Micro Subcategory
    - Fit & Silhouette (Oversized, Slim, Regular, Relaxed, Cropped, Wide Leg, etc.)
    - Fabric & Material (Cotton, Linen, Denim, Fleece, French Terry, Silk, Corduroy, etc.)
    - Pattern & Treatment (Graphic Print, Vintage Washed, Solid, Striped, Plaid, etc.)
    - Occasion / Style (Streetwear, Casual, Formal, Activewear, Loungewear)

Design rules:
    - Deterministic; zero side-effects on input.
    - Robust multi-keyword precedence matching.
    - JSON-safe return structure.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


# ----------------------------------------------------
# 1. Gender / Department Patterns
# ----------------------------------------------------
GENDER_PATTERNS = [
    (r"\b(women'?s?|womens|ladies|girls?|female|her)\b", "Women"),
    (r"\b(men'?s?|mens|guys?|male|him)\b", "Men"),
    (r"\b(unisex|all-gender|genderless)\b", "Unisex"),
    (r"\b(boys?|boy'?s?)\b", "Kids / Boys"),
    (r"\b(baby|infant|toddler)\b", "Baby / Infants"),
]

# ----------------------------------------------------
# 2. Fit / Silhouette Patterns
# ----------------------------------------------------
FIT_PATTERNS = [
    (r"\b(oversized?|baggy|drop\s*shoulder|boyfriend)\b", "Oversized / Baggy"),
    (r"\b(boxy|boxy\s*fit)\b", "Boxy Fit"),
    (r"\b(slim|slim\s*fit|skinny|fitted|bodycon)\b", "Slim Fit"),
    (r"\b(relaxed|relaxed\s*fit|loose|easy\s*fit)\b", "Relaxed Fit"),
    (r"\b(cropped|crop)\b", "Cropped"),
    (r"\b(wide\s*leg|flared?|bell\s*bottom)\b", "Wide Leg / Flared"),
    (r"\b(straight|straight\s*leg|straight\s*fit)\b", "Straight Fit"),
    (r"\b(tapered|tapered\s*fit|cuffed)\b", "Tapered"),
    (r"\b(regular|regular\s*fit|classic|standard\s*fit)\b", "Regular Fit"),
]

# ----------------------------------------------------
# 3. Fabric & Material Patterns
# ----------------------------------------------------
FABRIC_PATTERNS = [
    (r"\b(french\s*terry)\b", "French Terry"),
    (r"\b(fleece)\b", "Fleece"),
    (r"\b(denim|jean)\b", "Denim"),
    (r"\b(linen)\b", "Linen"),
    (r"\b(corduroy)\b", "Corduroy"),
    (r"\b(silk|mulberry\s*silk)\b", "Silk"),
    (r"\b(satin)\b", "Satin"),
    (r"\b(wool|merino|cashmere)\b", "Wool / Knit"),
    (r"\b(leather|faux\s*leather|vegan\s*leather|pu\s*leather)\b", "Leather"),
    (r"\b(suede)\b", "Suede"),
    (r"\b(cotton|100%\s*cotton|supima|organic\s*cotton)\b", "Cotton"),
    (r"\b(polyester|poly)\b", "Polyester"),
    (r"\b(nylon)\b", "Nylon"),
    (r"\b(rayon|viscose)\b", "Rayon / Viscose"),
]

# ----------------------------------------------------
# 4. Pattern & Surface Treatment Patterns
# ----------------------------------------------------
PATTERN_PATTERNS = [
    (r"\b(acid\s*wash|vintage\s*wash|stone\s*wash|mineral\s*wash|washed)\b", "Vintage Washed"),
    (r"\b(graphic|printed|print|typography|front\s*print|back\s*print)\b", "Graphic Print"),
    (r"\b(striped?|stripes|pinstripe)\b", "Striped"),
    (r"\b(plaid|checkered?|tartan|gingham)\b", "Plaid / Checkered"),
    (r"\b(tie\s*dye|tiedye)\b", "Tie Dye"),
    (r"\b(embroidered?|embroidery)\b", "Embroidered"),
    (r"\b(floral|flower|botanical)\b", "Floral Print"),
    (r"\b(camo|camouflage)\b", "Camouflage"),
    (r"\b(solid|plain|basic)\b", "Solid / Plain"),
]

# ----------------------------------------------------
# 5. Apparel Category & Subcategory Hierarchy
# ----------------------------------------------------
CATEGORY_PATTERNS = [
    # Tops - Hoodies & Sweatshirts
    (r"\b(hoodie|hooded|zip\s*hoodie|pullover\s*hoodie)\b", "Tops", "Hoodies"),
    (r"\b(sweatshirt|crewneck|crew\s*neck\s*sweatshirt)\b", "Tops", "Sweatshirts"),
    (r"\b(sweater|cardigan|knitwear|pullover|jumper)\b", "Tops", "Sweaters & Knitwear"),

    # Tops - T-Shirts & Polos
    (r"\b(tee|t-shirt|tshirt|t\s*shirt)\b", "Tops", "T-Shirts"),
    (r"\b(polo|polo\s*shirt|collar\s*tee)\b", "Tops", "Polos"),
    (r"\b(shirt|button\s*down|button\s*up|flannel|oxford)\b", "Tops", "Shirts"),
    (r"\b(tank|tank\s*top|sleeveless|vest\s*top|camisole|cami)\b", "Tops", "Tank Tops"),
    (r"\b(crop\s*top|cropped\s*tee)\b", "Tops", "Crop Tops"),

    # Bottoms
    (r"\b(jeans?|denim\s*pants?)\b", "Bottoms", "Jeans & Denim"),
    (r"\b(cargo|cargos|cargo\s*pants?)\b", "Bottoms", "Cargo Pants"),
    (r"\b(joggers?|sweatpants?|track\s*pants?)\b", "Bottoms", "Joggers & Sweatpants"),
    (r"\b(trousers?|chinos?|dress\s*pants?|slacks)\b", "Bottoms", "Trousers & Chinos"),
    (r"\b(shorts?|bermuda|swim\s*shorts?)\b", "Bottoms", "Shorts"),
    (r"\b(skirts?|mini\s*skirt|maxi\s*skirt)\b", "Bottoms", "Skirts"),
    (r"\b(leggings?|tights)\b", "Bottoms", "Leggings"),

    # Outerwear
    (r"\b(puffer|down\s*jacket|bubble\s*jacket)\b", "Outerwear", "Puffers"),
    (r"\b(blazer|suit\s*jacket)\b", "Outerwear", "Blazers"),
    (r"\b(coat|trench|overcoat|parka)\b", "Outerwear", "Coats"),
    (r"\b(jacket|bomber|varsity|windbreaker|denim\s*jacket)\b", "Outerwear", "Jackets"),
    (r"\b(vest|gilet)\b", "Outerwear", "Vests"),

    # Dresses & Jumpsuits
    (r"\b(dress|gown|sundress|slip\s*dress)\b", "Dresses & Jumpsuits", "Dresses"),
    (r"\b(jumpsuit|romper|playsuit|dungarees?)\b", "Dresses & Jumpsuits", "Jumpsuits & Rompers"),

    # Activewear
    (r"\b(sports\s*bra|gym\s*bra)\b", "Activewear", "Sports Bras"),
    (r"\b(activewear|gym\s*wear|biker\s*shorts?|tracksuit)\b", "Activewear", "Gym & Workout"),

    # Innerwear / Loungewear
    (r"\b(pajamas?|pyjamas?|sleepwear|nightwear|lounge\s*set)\b", "Innerwear & Loungewear", "Sleepwear"),
    (r"\b(boxers?|briefs?|underwear|panties|bra)\b", "Innerwear & Loungewear", "Underwear"),
]


def extract_apparel_attributes(title: str, existing_category: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract structured fashion attributes from a raw product title.
    """
    if not isinstance(title, str) or not title.strip():
        return {
            "gender": "Unisex",
            "category": existing_category or "Uncategorized",
            "subcategory": "General Apparel",
            "fit": "Regular Fit",
            "fabric": "Standard",
            "pattern": "Solid / Plain",
        }

    clean = title.lower()

    # 1. Gender
    gender = "Unisex"
    for pat, g_val in GENDER_PATTERNS:
        if re.search(pat, clean):
            gender = g_val
            break

    # 2. Fit
    fit = "Regular Fit"
    for pat, f_val in FIT_PATTERNS:
        if re.search(pat, clean):
            fit = f_val
            break

    # 3. Fabric
    fabric = "Standard"
    for pat, fab_val in FABRIC_PATTERNS:
        if re.search(pat, clean):
            fabric = fab_val
            break

    # 4. Pattern
    pattern = "Solid / Plain"
    for pat, p_val in PATTERN_PATTERNS:
        if re.search(pat, clean):
            pattern = p_val
            break

    # 5. Category & Subcategory
    cat = existing_category or "Uncategorized"
    subcat = "General Apparel"

    for pat, c_val, sub_val in CATEGORY_PATTERNS:
        if re.search(pat, clean):
            cat = c_val
            subcat = sub_val
            break

    # Fallback if existing category matches known pattern
    if cat == "Uncategorized" and existing_category:
        cat_lower = str(existing_category).lower()
        for pat, c_val, sub_val in CATEGORY_PATTERNS:
            if re.search(pat, cat_lower):
                cat = c_val
                subcat = sub_val
                break

    return {
        "gender": gender,
        "category": cat,
        "subcategory": subcat,
        "fit": fit,
        "fabric": fabric,
        "pattern": pattern,
    }


__all__ = [
    "extract_apparel_attributes",
    "GENDER_PATTERNS",
    "FIT_PATTERNS",
    "FABRIC_PATTERNS",
    "PATTERN_PATTERNS",
    "CATEGORY_PATTERNS",
]
