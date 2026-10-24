"""
TrendPulse Thrift Sourcing ROI & "What to Source Next" Recommender.

Provides actionable procurement intelligence for vintage curators,
thrift businesses, and drop brands:
    - Sourcing Lot ROI & Cost-to-Realization Multiple
    - Automated "What to Source Next" procurement checklist synthesized
      from viral aesthetic velocity, size curves, and top silhouettes.

Design rules:
    - Deterministic; zero side-effects on input DataFrame.
    - JSON-safe return structure.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import pandas as pd

from data_engine.social_curation.aesthetics import classify_aesthetic
from data_engine.apparel.size_normalizer import normalize_size
from data_engine.utils import clean_number, safe_float, safe_int


def generate_sourcing_recommendations(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Synthesize velocity, size curves, aesthetics, and margins to generate a
    prioritized 'What to Thrift / Source Next' procurement checklist.
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return {
            "status": "no_data",
            "message": "DataFrame is empty.",
            "sourcing_checklist": [],
            "top_aesthetic_to_hunt": None,
            "top_size_to_hunt": None,
            "procurement_guidance": "Insufficient sales data to generate sourcing recommendations.",
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

    # Classify aesthetics & sizes
    if "product" in data.columns:
        data["_aesthetic"] = data["product"].apply(lambda p: classify_aesthetic(p)["aesthetic"])
    else:
        data["_aesthetic"] = "Clean Fit / Minimalist"

    if "size" in data.columns:
        data["_std_size"] = data["size"].apply(lambda s: normalize_size(s)["standard_size"])
    elif "product" in data.columns:
        from data_engine.apparel.size_normalizer import extract_size_from_title
        data["_std_size"] = data["product"].apply(lambda p: extract_size_from_title(p) or "Unknown")
    else:
        data["_std_size"] = "Unknown"

    total_rev = float(data["_rev"].sum())

    # 1. Top Aesthetic Demand
    aes_grp = data.groupby("_aesthetic")["_rev"].sum().sort_values(ascending=False)
    top_aes = str(aes_grp.index[0]) if not aes_grp.empty else "Vintage Streetwear"

    # 2. Top Size Demand
    valid_size_df = data[data["_std_size"] != "Unknown"]
    if not valid_size_df.empty:
        size_grp = valid_size_df.groupby("_std_size")["_qty"].sum().sort_values(ascending=False)
        top_size = str(size_grp.index[0])
    else:
        top_size = "L / XL"

    # 3. Prioritized Sourcing Checklist Items
    checklist: List[Dict[str, Any]] = []

    # Combine Aesthetic + Category + Top Sizes
    group_cols = ["_aesthetic"]
    if "apparel_category" in data.columns:
        group_cols.append("apparel_category")
    elif "category" in data.columns:
        group_cols.append("category")

    for keys, sub_df in data.groupby(group_cols):
        aes_val = keys[0] if isinstance(keys, tuple) else keys
        cat_val = keys[1] if isinstance(keys, tuple) else "Apparel"

        sub_rev = float(sub_df["_rev"].sum())
        sub_qty = float(sub_df["_qty"].sum())
        asp = (sub_rev / sub_qty) if sub_qty > 0 else 0.0

        # Find best size in this cluster
        sub_valid_sizes = sub_df[sub_df["_std_size"] != "Unknown"]
        best_size = str(sub_valid_sizes.groupby("_std_size")["_qty"].sum().idxmax()) if not sub_valid_sizes.empty else "All Sizes"
        rev_share = (sub_rev / total_rev) if total_rev > 0 else 0.0
        priority = "High Priority 🔥" if rev_share >= 0.25 else ("Medium Priority ⚡" if rev_share >= 0.10 else "Niche / Test 🎯")

        checklist.append({
            "aesthetic": str(aes_val),
            "category": str(cat_val),
            "recommended_sizes_to_hunt": best_size,
            "historical_revenue": clean_number(sub_rev),
            "average_selling_price": clean_number(asp),
            "sourcing_priority": priority,
            "procurement_advice": f"Hunt {aes_val} {cat_val} specifically in size {best_size}. Achieves strong average selling price of ₹{clean_number(asp)}.",
        })

    checklist.sort(key=lambda x: safe_float(x["historical_revenue"]), reverse=True)

    # 4. Sourcing Lot ROI / Margin Realization
    lot_roi_summary = {}
    if "cost_price" in data.columns and data["cost_price"].notna().any():
        cogs = float(pd.to_numeric(data["cost_price"], errors="coerce").fillna(0.0).sum())
        if cogs > 0:
            roi_multiple = total_rev / cogs
            gross_profit = total_rev - cogs
            lot_roi_summary = {
                "total_sourcing_cost": clean_number(cogs),
                "total_realized_revenue": clean_number(total_rev),
                "gross_profit": clean_number(gross_profit),
                "sourcing_roi_multiple": f"{clean_number(roi_multiple)}x",
                "profit_margin_percentage": clean_number((gross_profit / total_rev * 100) if total_rev > 0 else 0.0),
            }

    narrative = (
        f"For your upcoming collection/drop, prioritize sourcing '{top_aes}' pieces, "
        f"particularly in size '{top_size}'. This aesthetic and size curve drove the largest share "
        f"of fast-clearing revenue in recent performance."
    )

    return {
        "status": "success",
        "top_aesthetic_to_hunt": top_aes,
        "top_size_to_hunt": top_size,
        "procurement_guidance": narrative,
        "sourcing_checklist": checklist[:8],
        "lot_sourcing_roi": lot_roi_summary,
    }


__all__ = ["generate_sourcing_recommendations"]
