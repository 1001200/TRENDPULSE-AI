"""
TrendPulse Drop Velocity & Flash Sell-Out Analytics.

Tracks the clearance speed, instant sell-out rates, and lifecycle velocity
of social media / Instagram Reel drop releases.

Design rules:
    - Deterministic; zero side-effects on input DataFrame.
    - JSON-safe return structure.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import pandas as pd

from data_engine.utils import clean_number, safe_float, safe_int


def analyze_drop_velocity(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze sales velocity across individual collection drops and flash releases.
    """
    if not isinstance(df, pd.DataFrame) or df.empty or "date" not in df.columns:
        return {
            "status": "no_data",
            "message": "DataFrame is empty or lacks date column.",
            "total_drops_detected": 0,
            "drops": [],
        }

    data = df.copy()
    data["_dt"] = pd.to_datetime(data["date"], errors="coerce")
    data = data.dropna(subset=["_dt"]).sort_values("_dt")

    if data.empty:
        return {
            "status": "insufficient_data",
            "message": "No valid dates found.",
            "total_drops_detected": 0,
            "drops": [],
        }

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

    # Group into drops by month or weekly clusters
    data["_drop_period"] = data["_dt"].dt.to_period("M").astype(str)
    
    drops_summary = []
    for drop_name, drop_df in data.groupby("_drop_period", sort=True):
        drop_rev = float(drop_df["_rev"].sum())
        drop_qty = float(drop_df["_qty"].sum())
        total_orders = len(drop_df)

        # Analyze daily velocity within the drop
        daily_sales = drop_df.groupby(drop_df["_dt"].dt.date)["_qty"].sum()
        first_day_qty = float(daily_sales.iloc[0]) if not daily_sales.empty else 0.0
        first_day_pct = (first_day_qty / drop_qty * 100) if drop_qty > 0 else 0.0

        first_3_days_qty = float(daily_sales.head(3).sum()) if not daily_sales.empty else 0.0
        first_3_days_pct = (first_3_days_qty / drop_qty * 100) if drop_qty > 0 else 0.0

        # Flash Sell-Out Score (0 to 100)
        # Weighted heavily on first 3 days velocity
        flash_score = min(100.0, first_3_days_pct * 1.2)
        if flash_score >= 80:
            clearance_grade = "Instant Flash Sell-Out 🔥 (Viral Surge)"
        elif flash_score >= 60:
            clearance_grade = "High Velocity Drop ⚡ (Strong Demand)"
        elif flash_score >= 40:
            clearance_grade = "Steady Burn Drop 📈 (Consistent Clearance)"
        else:
            clearance_grade = "Slow Moving Drop ⏳ (Requires Promotion)"

        top_drop_sku = str(drop_df.groupby("product")["_qty"].sum().idxmax()) if "product" in drop_df.columns else "N/A"

        drops_summary.append({
            "drop_name": f"Drop {drop_name}",
            "start_date": drop_df["_dt"].min().strftime("%Y-%m-%d"),
            "end_date": drop_df["_dt"].max().strftime("%Y-%m-%d"),
            "total_revenue": clean_number(drop_rev),
            "total_units_sold": clean_number(drop_qty),
            "total_orders": total_orders,
            "day_1_clearance_percentage": clean_number(first_day_pct),
            "day_3_clearance_percentage": clean_number(first_3_days_pct),
            "flash_sellout_score": clean_number(flash_score),
            "clearance_grade": clearance_grade,
            "fastest_selling_sku": top_drop_sku,
        })

    return {
        "status": "success",
        "total_drops_detected": len(drops_summary),
        "drops": drops_summary,
    }


__all__ = ["analyze_drop_velocity"]
