"""
TrendPulse Viral Aesthetic & Micro-Trend Intelligence.

Automatically classifies unstructured clothing products and thrift pieces
into viral social media aesthetic movements (Y2K, 90s Grunge, Gorpcore,
Old Money, Archive Streetwear, Blokecore, Clean Fit, Cottagecore)
and tracks aesthetic velocity across social drops.

Design rules:
    - Deterministic; zero side-effects on input DataFrame.
    - Multi-keyword pattern matching with aesthetic confidence scoring.
    - JSON-safe return structure.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from data_engine.utils import clean_number, safe_float, safe_int


AESTHETIC_RULES: List[Tuple[str, List[str], str]] = [
    (
        "Y2K / 2000s Retro",
        [
            r"\b(y2k|2000s|baby\s*tee|rhinestone|low\s*rise|parachute\s*pants?|cyber|metallic|trucker\s*hat|flare|butterfly)\b",
        ],
        "High viral energy across Instagram Reels & TikTok youth curation.",
    ),
    (
        "90s Vintage Grunge",
        [
            r"\b(acid\s*wash|vintage\s*wash|stone\s*wash|distressed|grunge|band\s*tee|faded|worn|carpenter|raw\s*hem|flannel|ripped)\b",
        ],
        "Dominant thrift and vintage lot aesthetic with steady sell-through.",
    ),
    (
        "Gorpcore / Utility Techwear",
        [
            r"\b(gorpcore|utility|cargo|tactical|parachute|nylon|windbreaker|water\s*resistant|drawstring|hiking|trail|fleece\s*vest)\b",
        ],
        "High-ticket functional outdoor & urban streetwear trend.",
    ),
    (
        "Old Money / Quiet Luxury",
        [
            r"\b(old\s*money|quiet\s*luxury|linen|cable\s*knit|oxford|polo\s*collar|tailored|trousers?|cashmere|preppy|chinos?)\b",
        ],
        "Sophisticated, high-AOV aesthetic favoring neutral palettes.",
    ),
    (
        "Archive / Heavyweight Streetwear",
        [
            r"\b(archive|heavyweight|240\s*gsm|280\s*gsm|boxy|drop\s*shoulder|french\s*terry|garment\s*dyed|oversized\s*tee|oversized\s*hoodie)\b",
        ],
        "Core D2C streetwear staple with high repeat buyer loyalty.",
    ),
    (
        "Blokecore / Vintage Sportswear",
        [
            r"\b(blokecore|jersey|football\s*jersey|soccer|track\s*jacket|tracksuit|vintage\s*sports?|racing|moto|sportswear)\b",
        ],
        "Fast-rising social media sports retro aesthetic.",
    ),
    (
        "Cottagecore / Coquette",
        [
            r"\b(cottagecore|coquette|corset|lace|floral|ruffle|ribbon|eyelet|smocked|tiered\s*dress|puff\s*sleeve)\b",
        ],
        "Feminine vintage curation staple with strong seasonal summer demand.",
    ),
    (
        "Clean Fit / Minimalist",
        [
            r"\b(clean\s*fit|minimalist|solid|basic|essential|monochrome|plain|straight\s*fit|classic)\b",
        ],
        "Evergreen baseline aesthetic with low markdown risk.",
    ),
]


def classify_aesthetic(text: str) -> Dict[str, str]:
    """
    Classify a product title or thrift description into its primary viral aesthetic.
    """
    if not isinstance(text, str) or not text.strip():
        return {
            "aesthetic": "Clean Fit / Minimalist",
            "aesthetic_code": "clean_fit",
            "explanation": "Default minimal baseline.",
        }

    clean = text.lower()
    for name, patterns, explanation in AESTHETIC_RULES:
        for pat in patterns:
            if re.search(pat, clean):
                code = name.split("/")[0].strip().lower().replace(" ", "_")
                return {
                    "aesthetic": name,
                    "aesthetic_code": code,
                    "explanation": explanation,
                }

    return {
        "aesthetic": "Clean Fit / Minimalist",
        "aesthetic_code": "clean_fit",
        "explanation": "Solid baseline styling.",
    }


def analyze_aesthetic_velocity(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate revenue, unit velocity, and trend trajectory across all viral aesthetics.
    """
    if not isinstance(df, pd.DataFrame) or df.empty or "product" not in df.columns:
        return {
            "status": "no_data",
            "message": "DataFrame is empty or lacks product titles.",
            "top_aesthetics": [],
            "trending_aesthetics": [],
        }

    data = df.copy()

    # Numerical columns prep
    if "quantity" in data.columns:
        data["_qty"] = pd.to_numeric(data["quantity"], errors="coerce").fillna(0.0)
    else:
        data["_qty"] = 1.0

    if "revenue" in data.columns:
        data["_rev"] = pd.to_numeric(data["revenue"], errors="coerce").fillna(0.0)
    elif "price" in data.columns:
        p = pd.to_numeric(data["price"], errors="coerce").fillna(0.0)
        data["_rev"] = data["_qty"] * p
    else:
        data["_rev"] = 0.0

    total_rev = float(data["_rev"].sum())
    total_qty = float(data["_qty"].sum())

    # Tag each item
    data["_aesthetic"] = data["product"].apply(lambda p: classify_aesthetic(p)["aesthetic"])

    aesthetic_breakdown = []
    for aes_name, a_df in data.groupby("_aesthetic"):
        rev = float(a_df["_rev"].sum())
        qty = float(a_df["_qty"].sum())
        item_count = int(a_df["product"].nunique())
        rev_share = (rev / total_rev * 100) if total_rev > 0 else 0.0

        # Calculate Average Selling Price for this aesthetic
        asp = (rev / qty) if qty > 0 else 0.0

        aesthetic_breakdown.append({
            "aesthetic": str(aes_name),
            "revenue": clean_number(rev),
            "units_sold": clean_number(qty),
            "unique_styles_count": item_count,
            "average_selling_price": clean_number(asp),
            "revenue_share_percentage": clean_number(rev_share),
        })

    aesthetic_breakdown.sort(key=lambda x: safe_float(x["revenue"]), reverse=True)

    # Trend Direction based on multi-period data if available
    trending = []
    if "date" in data.columns:
        data["_dt"] = pd.to_datetime(data["date"], errors="coerce")
        valid_dt = data.dropna(subset=["_dt"]).sort_values("_dt")
        if len(valid_dt) >= 2:
            min_d = valid_dt["_dt"].min()
            max_d = valid_dt["_dt"].max()
            mid_d = min_d + (max_d - min_d) / 2

            p1 = valid_dt[valid_dt["_dt"] <= mid_d]
            p2 = valid_dt[valid_dt["_dt"] > mid_d]

            if not p1.empty and not p2.empty:
                p1_grp = p1.groupby("_aesthetic")["_rev"].sum()
                p2_grp = p2.groupby("_aesthetic")["_rev"].sum()

                all_aesthetics = set(p1_grp.index).union(set(p2_grp.index))
                for a_name in all_aesthetics:
                    r1 = float(p1_grp.get(a_name, 0.0))
                    r2 = float(p2_grp.get(a_name, 0.0))
                    delta = r2 - r1
                    pct_growth = ((r2 - r1) / r1 * 100) if r1 > 0 else (100.0 if r2 > 0 else 0.0)

                    status_str = "Heating Up 🔥" if pct_growth > 15.0 else ("Cooling Down ❄️" if pct_growth < -15.0 else "Stable ⚡")

                    trending.append({
                        "aesthetic": str(a_name),
                        "prior_revenue": clean_number(r1),
                        "recent_revenue": clean_number(r2),
                        "growth_percentage": clean_number(pct_growth),
                        "trend_status": status_str,
                    })

                trending.sort(key=lambda x: safe_float(x["growth_percentage"]), reverse=True)

    return {
        "status": "success",
        "total_revenue_analyzed": clean_number(total_rev),
        "total_units_sold": clean_number(total_qty),
        "top_aesthetics_by_revenue": aesthetic_breakdown,
        "aesthetic_velocity_trends": trending,
    }


__all__ = ["classify_aesthetic", "analyze_aesthetic_velocity", "AESTHETIC_RULES"]
