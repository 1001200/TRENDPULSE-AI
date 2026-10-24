"""
TrendPulse Fashion Unit Economics & Margin Health Engine.

Calculates SKU and category-level Gross Profit Margins, Markdown Drag
(lost profit due to discounting), and the 4-Quadrant Product Profitability Matrix.

Design rules:
    - Deterministic; zero side-effects on input DataFrame.
    - JSON-safe return structure.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from data_engine.utils import clean_number, safe_float, safe_int


def analyze_unit_economics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze gross margins, discount drag, and 4-quadrant product portfolio profitability.
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return {
            "status": "no_data",
            "message": "DataFrame is empty.",
            "overall_metrics": {},
            "profitability_quadrants": {},
            "category_margins": [],
        }

    data = df.copy()

    # Numerical columns prep
    if "quantity" in data.columns:
        data["_qty"] = pd.to_numeric(data["quantity"], errors="coerce").fillna(0.0)
    else:
        data["_qty"] = 1.0

    if "price" in data.columns:
        data["_price"] = pd.to_numeric(data["price"], errors="coerce").fillna(0.0)
    else:
        data["_price"] = 0.0

    if "revenue" in data.columns:
        data["_rev"] = pd.to_numeric(data["revenue"], errors="coerce").fillna(0.0)
    else:
        data["_rev"] = data["_qty"] * data["_price"]

    # Cost Price (COGS) handling
    if "cost_price" in data.columns and data["cost_price"].notna().any():
        data["_cogs_unit"] = pd.to_numeric(data["cost_price"], errors="coerce").fillna(data["_price"] * 0.40)
    else:
        # Default estimated apparel industry benchmark COGS: 40% of selling price (60% gross margin)
        data["_cogs_unit"] = data["_price"] * 0.40

    data["_total_cogs"] = data["_qty"] * data["_cogs_unit"]
    data["_gross_profit"] = data["_rev"] - data["_total_cogs"]
    data["_margin_pct"] = np.where(data["_rev"] > 0, (data["_gross_profit"] / data["_rev"]) * 100, 0.0)

    # Discount / Markdown Drag
    if "discount" in data.columns:
        data["_disc_pct"] = pd.to_numeric(data["discount"], errors="coerce").fillna(0.0)
    else:
        data["_disc_pct"] = 0.0

    # Discount drag in currency: Revenue at full price vs actual discounted revenue
    data["_full_price_rev"] = np.where(
        data["_disc_pct"] < 100,
        data["_rev"] / (1 - (data["_disc_pct"] / 100).clip(upper=0.99)),
        data["_rev"],
    )
    data["_discount_drag"] = (data["_full_price_rev"] - data["_rev"]).clip(lower=0.0)

    total_rev = float(data["_rev"].sum())
    total_cogs = float(data["_total_cogs"].sum())
    total_gross_profit = float(data["_gross_profit"].sum())
    overall_margin_pct = (total_gross_profit / total_rev * 100) if total_rev > 0 else 0.0
    total_discount_drag = float(data["_discount_drag"].sum())

    # SKU-Level Grouping for Portfolio Matrix
    sku_col = "product" if "product" in data.columns else data.columns[0]
    sku_grp = data.groupby(sku_col).agg(
        total_units=("_qty", "sum"),
        total_revenue=("_rev", "sum"),
        total_cogs=("_total_cogs", "sum"),
        total_profit=("_gross_profit", "sum"),
        discount_lost=("_discount_drag", "sum"),
    ).reset_index()

    sku_grp["margin_pct"] = np.where(
        sku_grp["total_revenue"] > 0,
        (sku_grp["total_profit"] / sku_grp["total_revenue"]) * 100,
        0.0,
    )

    median_volume = float(sku_grp["total_units"].median()) if not sku_grp.empty else 0.0
    margin_benchmark = 45.0  # 45% margin threshold for premium apparel

    stars = []
    cash_cows = []
    hidden_gems = []
    value_destroyers = []

    for _, row in sku_grp.iterrows():
        sku_name = str(row[sku_col])
        units = float(row["total_units"])
        rev = float(row["total_revenue"])
        profit = float(row["total_profit"])
        m_pct = float(row["margin_pct"])
        disc = float(row["discount_lost"])

        item_dict = {
            "sku": sku_name,
            "units_sold": clean_number(units),
            "revenue": clean_number(rev),
            "gross_profit": clean_number(profit),
            "gross_margin_percentage": clean_number(m_pct),
            "discount_bleed": clean_number(disc),
        }

        if units >= median_volume and m_pct >= margin_benchmark:
            item_dict["action_advice"] = "Scale ad spend & maintain continuous stock."
            stars.append(item_dict)
        elif units >= median_volume and m_pct < margin_benchmark:
            item_dict["action_advice"] = "Protect volume, optimize COGS to boost margins."
            cash_cows.append(item_dict)
        elif units < median_volume and m_pct >= margin_benchmark:
            item_dict["action_advice"] = "Feature in social drops & improve homepage merchandising."
            hidden_gems.append(item_dict)
        else:
            item_dict["action_advice"] = "Discontinue or clearance out; drag on brand margin."
            value_destroyers.append(item_dict)

    # Sort each quadrant
    stars.sort(key=lambda x: safe_float(x["revenue"]), reverse=True)
    cash_cows.sort(key=lambda x: safe_float(x["revenue"]), reverse=True)
    hidden_gems.sort(key=lambda x: safe_float(x["gross_margin_percentage"]), reverse=True)
    value_destroyers.sort(key=lambda x: safe_float(x["revenue"]), reverse=True)

    # Category Margins
    cat_col = "apparel_category" if "apparel_category" in data.columns else ("category" if "category" in data.columns else None)
    cat_breakdown = []
    if cat_col:
        for c_name, c_df in data.groupby(cat_col):
            c_rev = float(c_df["_rev"].sum())
            c_profit = float(c_df["_gross_profit"].sum())
            c_margin = (c_profit / c_rev * 100) if c_rev > 0 else 0.0
            cat_breakdown.append({
                "category": str(c_name),
                "revenue": clean_number(c_rev),
                "gross_profit": clean_number(c_profit),
                "gross_margin_percentage": clean_number(c_margin),
            })
        cat_breakdown.sort(key=lambda x: safe_float(x["revenue"]), reverse=True)

    return {
        "status": "success",
        "overall_metrics": {
            "total_revenue": clean_number(total_rev),
            "total_cogs": clean_number(total_cogs),
            "total_gross_profit": clean_number(total_gross_profit),
            "gross_margin_percentage": clean_number(overall_margin_pct),
            "total_discount_bleed": clean_number(total_discount_drag),
        },
        "profitability_quadrants": {
            "star_performers": stars[:10],
            "cash_cows": cash_cows[:10],
            "hidden_gems": hidden_gems[:10],
            "value_destroyers": value_destroyers[:10],
        },
        "category_margins": cat_breakdown,
    }


__all__ = ["analyze_unit_economics"]
