"""
TrendPulse Time-Series Multi-Grain Aggregation.

Aggregates daily clothing sales transactions into multiple temporal grains:
    - Weekly time-series (Revenue, Units, Orders, AOV, Top Product/Category)
    - Monthly time-series
    - Quarterly time-series
    - Day-of-week seasonality & shopping pattern distribution

Design rules:
    - Deterministic; zero side-effects on input DataFrame.
    - JSON-safe return structure.
    - Handles variable date frequencies and gaps.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from data_engine.utils import clean_number, safe_float, safe_int


def _aggregate_by_period(
    data: pd.DataFrame,
    period_col: str,
    period_name: str,
) -> List[Dict[str, Any]]:
    """Helper to aggregate metrics across a temporal period group."""
    records: List[Dict[str, Any]] = []

    for period_val, group in data.groupby(period_col, sort=True):
        rev = float(group["_rev"].sum())
        qty = float(group["_qty"].sum())
        orders = len(group)
        aov = (rev / orders) if orders > 0 else 0.0
        asp = (rev / qty) if qty > 0 else 0.0

        top_prod = None
        if "product" in group.columns and group["product"].notna().any():
            top_prod = str(group.groupby("product")["_rev"].sum().idxmax())

        top_cat = None
        if "category" in group.columns and group["category"].notna().any():
            top_cat = str(group.groupby("category")["_rev"].sum().idxmax())

        records.append({
            "period": str(period_val),
            "total_revenue": clean_number(rev),
            "total_quantity": clean_number(qty),
            "order_count": orders,
            "average_order_value": clean_number(aov),
            "average_selling_price": clean_number(asp),
            "top_product": top_prod,
            "top_category": top_cat,
        })

    return records


def aggregate_time_series(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate weekly, monthly, quarterly aggregations and day-of-week seasonality.
    """
    if not isinstance(df, pd.DataFrame) or df.empty or "date" not in df.columns:
        return {
            "status": "no_data",
            "message": "DataFrame is empty or lacks date column.",
            "weekly": [],
            "monthly": [],
            "quarterly": [],
            "day_of_week_distribution": [],
        }

    data = df.copy()
    data["_dt"] = pd.to_datetime(data["date"], errors="coerce")
    data = data.dropna(subset=["_dt"]).sort_values("_dt")

    if data.empty:
        return {
            "status": "insufficient_data",
            "message": "No valid dates could be parsed.",
            "weekly": [],
            "monthly": [],
            "quarterly": [],
            "day_of_week_distribution": [],
        }

    # Prepare revenue & quantity
    if "quantity" in data.columns:
        data["_qty"] = pd.to_numeric(data["quantity"], errors="coerce").fillna(0.0)
    else:
        data["_qty"] = 0.0

    if "revenue" in data.columns:
        data["_rev"] = pd.to_numeric(data["revenue"], errors="coerce").fillna(0.0)
    elif "price" in data.columns:
        p = pd.to_numeric(data["price"], errors="coerce").fillna(0.0)
        data["_rev"] = data["_qty"] * p
    else:
        data["_rev"] = 0.0

    # Date Period columns
    data["_week"] = data["_dt"].dt.to_period("W").astype(str)
    data["_month"] = data["_dt"].dt.to_period("M").astype(str)
    data["_quarter"] = data["_dt"].dt.to_period("Q").astype(str)
    data["_dow_num"] = data["_dt"].dt.dayofweek
    data["_dow_name"] = data["_dt"].dt.day_name()

    weekly_series = _aggregate_by_period(data, "_week", "weekly")
    monthly_series = _aggregate_by_period(data, "_month", "monthly")
    quarterly_series = _aggregate_by_period(data, "_quarter", "quarterly")

    # Day of Week Distribution (Monday = 0 to Sunday = 6)
    dow_distribution: List[Dict[str, Any]] = []
    total_rev = float(data["_rev"].sum())

    day_order = [
        (0, "Monday"), (1, "Tuesday"), (2, "Wednesday"),
        (3, "Thursday"), (4, "Friday"), (5, "Saturday"), (6, "Sunday")
    ]

    for dow_num, dow_name in day_order:
        day_df = data[data["_dow_num"] == dow_num]
        day_rev = float(day_df["_rev"].sum())
        day_orders = len(day_df)
        day_qty = float(day_df["_qty"].sum())

        dow_distribution.append({
            "day_number": dow_num,
            "day_name": dow_name,
            "total_revenue": clean_number(day_rev),
            "revenue_percentage": clean_number((day_rev / total_rev * 100.0) if total_rev > 0 else 0.0),
            "order_count": day_orders,
            "total_quantity": clean_number(day_qty),
        })

    # Find peak shopping day
    peak_day = max(dow_distribution, key=lambda x: safe_float(x["total_revenue"])) if dow_distribution else None

    return {
        "status": "success",
        "date_range": {
            "start": data["_dt"].min().strftime("%Y-%m-%d"),
            "end": data["_dt"].max().strftime("%Y-%m-%d"),
            "unique_days": int(data["_dt"].dt.normalize().nunique()),
        },
        "weekly": weekly_series,
        "monthly": monthly_series,
        "quarterly": quarterly_series,
        "day_of_week_distribution": dow_distribution,
        "peak_shopping_day": peak_day["day_name"] if peak_day else None,
    }


__all__ = ["aggregate_time_series"]
