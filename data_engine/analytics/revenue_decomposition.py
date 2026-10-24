"""
TrendPulse Price-Volume-Mix (PVM) Revenue Decomposition.

Mathematically decomposes period-over-period revenue variances into three
mutually exclusive commercial drivers:
    1. Volume Effect — Variance driven by changes in total units sold at baseline ASP.
    2. Price Effect  — Variance driven by direct changes in unit selling prices.
    3. Mix Effect    — Variance driven by customer basket shifts toward higher or lower value items.

Design rules:
    - Mathematically rigorous: Price Effect + Volume Effect + Mix Effect = Total Revenue Delta.
    - Deterministic; zero side-effects on input DataFrame.
    - Returns JSON-safe results with intuitive business diagnostics.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from data_engine.utils import clean_number, safe_float, safe_int


def _prepare_period_splits(df: pd.DataFrame) -> Optional[tuple[pd.DataFrame, pd.DataFrame, str, str]]:
    """Split dataset into two comparative periods (latest month vs prior month, or halves)."""
    if df.empty or "date" not in df.columns or len(df) < 2:
        return None

    data = df.copy()
    data["_dt"] = pd.to_datetime(data["date"], errors="coerce")
    data = data.dropna(subset=["_dt"]).sort_values("_dt")

    if len(data) < 2:
        return None

    # Check for months first
    data["_ym"] = data["_dt"].dt.to_period("M")
    unique_months = sorted(data["_ym"].unique())

    if len(unique_months) >= 2:
        curr_m = unique_months[-1]
        prev_m = unique_months[-2]
        curr_df = data[data["_ym"] == curr_m].copy()
        prev_df = data[data["_ym"] == prev_m].copy()
        return curr_df, prev_df, str(curr_m), str(prev_m)

    # Fallback to halves split
    min_date = data["_dt"].min()
    max_date = data["_dt"].max()
    mid_date = min_date + (max_date - min_date) / 2

    first_half = data[data["_dt"] <= mid_date].copy()
    second_half = data[data["_dt"] > mid_date].copy()

    if first_half.empty or second_half.empty:
        return None

    curr_label = f"Recent Half ({mid_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')})"
    prev_label = f"Prior Half ({min_date.strftime('%Y-%m-%d')} to {mid_date.strftime('%Y-%m-%d')})"
    return second_half, first_half, curr_label, prev_label


def decompose_revenue(
    df: pd.DataFrame,
    curr_df: Optional[pd.DataFrame] = None,
    prev_df: Optional[pd.DataFrame] = None,
    curr_label: str = "Current Period",
    prev_label: str = "Previous Period",
) -> Dict[str, Any]:
    """
    Perform full Price-Volume-Mix (PVM) revenue variance decomposition.
    """
    if curr_df is None or prev_df is None:
        if not isinstance(df, pd.DataFrame) or df.empty:
            return {
                "status": "insufficient_data",
                "message": "DataFrame is empty.",
                "total_delta": None,
                "decomposition": {},
            }
        split = _prepare_period_splits(df)
        if split is None:
            return {
                "status": "insufficient_data",
                "message": "Insufficient date ranges to decompose revenue variance.",
                "total_delta": None,
                "decomposition": {},
            }
        curr_df, prev_df, curr_label, prev_label = split

    # Ensure clean price, quantity, revenue, and product
    for d in (curr_df, prev_df):
        if "quantity" in d.columns:
            d["_qty"] = pd.to_numeric(d["quantity"], errors="coerce").fillna(0.0)
        else:
            d["_qty"] = 0.0

        if "price" in d.columns:
            d["_price"] = pd.to_numeric(d["price"], errors="coerce").fillna(0.0)
        else:
            d["_price"] = 0.0

        if "revenue" in d.columns:
            d["_rev"] = pd.to_numeric(d["revenue"], errors="coerce").fillna(0.0)
        else:
            d["_rev"] = d["_qty"] * d["_price"]

        if "product" in d.columns:
            d["_prod"] = d["product"].astype(str).str.strip()
        else:
            d["_prod"] = "All Products"

    # Aggregates
    rev_0 = float(prev_df["_rev"].sum())
    rev_1 = float(curr_df["_rev"].sum())
    qty_0 = float(prev_df["_qty"].sum())
    qty_1 = float(curr_df["_qty"].sum())

    total_rev_delta = rev_1 - rev_0
    total_qty_delta = qty_1 - qty_0

    asp_0 = (rev_0 / qty_0) if qty_0 > 0 else 0.0
    asp_1 = (rev_1 / qty_1) if qty_1 > 0 else 0.0

    # 1. Volume Effect = (Q1 - Q0) * ASP0
    # The revenue change expected solely from selling more or fewer units at the baseline average price
    volume_effect = total_qty_delta * asp_0

    # 2. Product-level Price Effect
    # For each product: (P1_i - P0_i) * Q1_i
    # Products in both periods
    curr_prod_grp = curr_df.groupby("_prod").agg(qty=("_qty", "sum"), rev=("_rev", "sum"))
    prev_prod_grp = prev_df.groupby("_prod").agg(qty=("_qty", "sum"), rev=("_rev", "sum"))

    curr_prod_grp["avg_price"] = np.where(curr_prod_grp["qty"] > 0, curr_prod_grp["rev"] / curr_prod_grp["qty"], 0.0)
    prev_prod_grp["avg_price"] = np.where(prev_prod_grp["qty"] > 0, prev_prod_grp["rev"] / prev_prod_grp["qty"], 0.0)

    all_prods = set(curr_prod_grp.index).union(set(prev_prod_grp.index))
    price_effect = 0.0
    product_details = []

    for prod in all_prods:
        q1 = float(curr_prod_grp.loc[prod, "qty"]) if prod in curr_prod_grp.index else 0.0
        q0 = float(prev_prod_grp.loc[prod, "qty"]) if prod in prev_prod_grp.index else 0.0
        p1 = float(curr_prod_grp.loc[prod, "avg_price"]) if prod in curr_prod_grp.index else 0.0
        p0 = float(prev_prod_grp.loc[prod, "avg_price"]) if prod in prev_prod_grp.index else 0.0

        r1 = q1 * p1
        r0 = q0 * p0
        prod_delta = r1 - r0

        # If product existed in both periods with positive price, calculate direct price change
        if q1 > 0 and p0 > 0:
            prod_price_effect = (p1 - p0) * q1
        else:
            prod_price_effect = 0.0

        price_effect += prod_price_effect

        product_details.append({
            "product": prod,
            "previous_revenue": clean_number(r0),
            "current_revenue": clean_number(r1),
            "revenue_delta": clean_number(prod_delta),
            "previous_price": clean_number(p0),
            "current_price": clean_number(p1),
            "previous_quantity": clean_number(q0),
            "current_quantity": clean_number(q1),
        })

    # 3. Mix Effect = Total Delta - Volume Effect - Price Effect
    mix_effect = total_rev_delta - volume_effect - price_effect

    # Percentage contributions
    if total_rev_delta != 0:
        vol_pct = (volume_effect / abs(total_rev_delta)) * 100.0
        pri_pct = (price_effect / abs(total_rev_delta)) * 100.0
        mix_pct = (mix_effect / abs(total_rev_delta)) * 100.0
    else:
        vol_pct = pri_pct = mix_pct = 0.0

    # Determine primary driver
    abs_effects = [
        ("Volume Effect", abs(volume_effect), volume_effect),
        ("Price Effect", abs(price_effect), price_effect),
        ("Mix Effect", abs(mix_effect), mix_effect),
    ]
    abs_effects.sort(key=lambda x: x[1], reverse=True)
    primary_driver_name = abs_effects[0][0]
    primary_driver_val = abs_effects[0][2]

    # Generate diagnostic sentence
    growth_direction = "increased" if total_rev_delta > 0 else ("decreased" if total_rev_delta < 0 else "remained flat")
    pct_str = f"{(total_rev_delta / rev_0 * 100):+.1f}%" if rev_0 > 0 else "N/A"
    
    diagnostic_message = (
        f"Revenue {growth_direction} by {clean_number(total_rev_delta)} ({pct_str}) from {prev_label} to {curr_label}. "
        f"The primary commercial driver was the {primary_driver_name} ({clean_number(primary_driver_val)} impact). "
    )
    if volume_effect > 0:
        diagnostic_message += f"Higher sales volume contributed +{clean_number(volume_effect)}. "
    elif volume_effect < 0:
        diagnostic_message += f"Lower sales volume created a drag of {clean_number(volume_effect)}. "

    if price_effect > 0:
        diagnostic_message += f"Price increases added +{clean_number(price_effect)}. "
    elif price_effect < 0:
        diagnostic_message += f"Price discounting reduced revenue by {clean_number(price_effect)}. "

    if mix_effect > 0:
        diagnostic_message += f"Favorable product mix (shift toward higher-ticket items) added +{clean_number(mix_effect)}."
    elif mix_effect < 0:
        diagnostic_message += f"Unfavorable product mix (shift toward lower-priced items) reduced revenue by {clean_number(mix_effect)}."

    return {
        "status": "success",
        "current_period": curr_label,
        "previous_period": prev_label,
        "summary": {
            "previous_revenue": clean_number(rev_0),
            "current_revenue": clean_number(rev_1),
            "total_revenue_delta": clean_number(total_rev_delta),
            "percentage_change": clean_number(((rev_1 - rev_0) / rev_0 * 100) if rev_0 > 0 else 0.0),
            "previous_quantity": clean_number(qty_0),
            "current_quantity": clean_number(qty_1),
            "previous_average_selling_price": clean_number(asp_0),
            "current_average_selling_price": clean_number(asp_1),
        },
        "decomposition": {
            "volume_effect": {
                "impact": clean_number(volume_effect),
                "contribution_percentage": clean_number(vol_pct),
                "explanation": "Revenue impact from change in total unit volume sold.",
            },
            "price_effect": {
                "impact": clean_number(price_effect),
                "contribution_percentage": clean_number(pri_pct),
                "explanation": "Revenue impact from direct changes in unit selling prices.",
            },
            "mix_effect": {
                "impact": clean_number(mix_effect),
                "contribution_percentage": clean_number(mix_pct),
                "explanation": "Revenue impact from customer preference shifts between price tiers.",
            },
        },
        "primary_driver": primary_driver_name,
        "diagnostic_explanation": diagnostic_message.strip(),
        "product_details": sorted(product_details, key=lambda x: safe_float(x["revenue_delta"]), reverse=True),
    }


__all__ = ["decompose_revenue"]
