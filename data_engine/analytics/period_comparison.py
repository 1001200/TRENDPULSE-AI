"""
TrendPulse Period-over-Period Analytics.

Calculates temporal delta comparisons (Week-over-Week, Month-over-Month,
and Rolling Window periods) for key retail business metrics:
    - Revenue
    - Quantity (Units sold)
    - Orders / Transaction count
    - Average Order Value (AOV)
    - Average Selling Price (ASP)
    - Top growing and declining categories/products

Design rules:
    - Deterministic; zero side-effects on input DataFrame.
    - JSON-safe return structure.
    - Gracefully handles short timeframes or sparse datasets.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from data_engine.utils import clean_number, safe_float, safe_int


def _calc_change(current: float, previous: float) -> Dict[str, Any]:
    """Calculate absolute and percentage change with direction."""
    abs_change = current - previous
    if previous == 0:
        pct_change = 100.0 if current > 0 else (-100.0 if current < 0 else 0.0)
    else:
        pct_change = (abs_change / abs(previous)) * 100.0

    if pct_change > 1.0:
        direction = "increasing"
    elif pct_change < -1.0:
        direction = "decreasing"
    else:
        direction = "flat"

    return {
        "current": clean_number(current),
        "previous": clean_number(previous),
        "absolute_change": clean_number(abs_change),
        "percentage_change": clean_number(pct_change),
        "direction": direction,
    }


def _prepare_period_df(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Ensure clean date, quantity, and revenue columns."""
    if df.empty or "date" not in df.columns:
        return None

    data = df.copy()
    data["_dt"] = pd.to_datetime(data["date"], errors="coerce")
    data = data.dropna(subset=["_dt"]).sort_values("_dt")

    if data.empty:
        return None

    if "quantity" in data.columns:
        data["_qty"] = pd.to_numeric(data["quantity"], errors="coerce").fillna(0.0)
    else:
        data["_qty"] = 0.0

    if "revenue" in data.columns:
        data["_rev"] = pd.to_numeric(data["revenue"], errors="coerce").fillna(0.0)
    elif "price" in data.columns:
        prices = pd.to_numeric(data["price"], errors="coerce").fillna(0.0)
        data["_rev"] = data["_qty"] * prices
    else:
        data["_rev"] = 0.0

    return data


def _summarize_slice(slice_df: pd.DataFrame) -> Dict[str, float]:
    """Summarize metrics for a dataframe slice."""
    if slice_df.empty:
        return {
            "revenue": 0.0,
            "quantity": 0.0,
            "orders": 0.0,
            "aov": 0.0,
            "asp": 0.0,
        }

    rev = float(slice_df["_rev"].sum())
    qty = float(slice_df["_qty"].sum())
    orders = float(len(slice_df))
    aov = (rev / orders) if orders > 0 else 0.0
    asp = (rev / qty) if qty > 0 else 0.0

    return {
        "revenue": rev,
        "quantity": qty,
        "orders": orders,
        "aov": aov,
        "asp": asp,
    }


def _compare_slices(
    curr_df: pd.DataFrame,
    prev_df: pd.DataFrame,
    period_name: str,
    curr_label: str,
    prev_label: str,
) -> Dict[str, Any]:
    """Compare two slices across all standard business dimensions."""
    curr_summary = _summarize_slice(curr_df)
    prev_summary = _summarize_slice(prev_df)

    metrics = {
        "revenue": _calc_change(curr_summary["revenue"], prev_summary["revenue"]),
        "quantity": _calc_change(curr_summary["quantity"], prev_summary["quantity"]),
        "orders": _calc_change(curr_summary["orders"], prev_summary["orders"]),
        "average_order_value": _calc_change(curr_summary["aov"], prev_summary["aov"]),
        "average_selling_price": _calc_change(curr_summary["asp"], prev_summary["asp"]),
    }

    # Category breakdowns if available
    category_drivers: List[Dict[str, Any]] = []
    if "category" in curr_df.columns and "category" in prev_df.columns:
        curr_cat = curr_df.groupby("category")["_rev"].sum()
        prev_cat = prev_df.groupby("category")["_rev"].sum()
        all_cats = set(curr_cat.index).union(set(prev_cat.index))

        for cat in all_cats:
            c_rev = float(curr_cat.get(cat, 0.0))
            p_rev = float(prev_cat.get(cat, 0.0))
            chg = _calc_change(c_rev, p_rev)
            category_drivers.append({
                "category": str(cat),
                **chg,
            })
        category_drivers.sort(key=lambda x: safe_float(x.get("absolute_change")), reverse=True)

    # Product breakdowns if available
    product_drivers: List[Dict[str, Any]] = []
    if "product" in curr_df.columns and "product" in prev_df.columns:
        curr_prod = curr_df.groupby("product")["_rev"].sum()
        prev_prod = prev_df.groupby("product")["_rev"].sum()
        all_prods = set(curr_prod.index).union(set(prev_prod.index))

        for prod in all_prods:
            c_rev = float(curr_prod.get(prod, 0.0))
            p_rev = float(prev_prod.get(prod, 0.0))
            chg = _calc_change(c_rev, p_rev)
            product_drivers.append({
                "product": str(prod),
                **chg,
            })
        product_drivers.sort(key=lambda x: safe_float(x.get("absolute_change")), reverse=True)

    top_growing_products = [p for p in product_drivers if safe_float(p.get("absolute_change")) > 0][:5]
    top_declining_products = [p for p in reversed(product_drivers) if safe_float(p.get("absolute_change")) < 0][:5]

    return {
        "period_type": period_name,
        "current_period": curr_label,
        "previous_period": prev_label,
        "metrics": metrics,
        "category_drivers": category_drivers[:5],
        "top_growing_products": top_growing_products,
        "top_declining_products": top_declining_products,
    }


def analyze_period_over_period(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate complete period-over-period comparative analytics.

    Evaluates:
        - Month-over-Month (MoM)
        - Week-over-Week (WoW)
        - Equal-Half Split comparison (when calendar periods are sparse)
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return {
            "status": "insufficient_data",
            "message": "DataFrame is empty or invalid.",
            "month_over_month": None,
            "week_over_week": None,
            "period_split": None,
        }

    data = _prepare_period_df(df)
    if data is None or len(data) < 2:
        return {
            "status": "insufficient_data",
            "message": "Insufficient valid dates for period comparison.",
            "month_over_month": None,
            "week_over_week": None,
            "period_split": None,
        }

    # 1. Month-over-Month
    mom_result = None
    data["_year_month"] = data["_dt"].dt.to_period("M")
    unique_months = sorted(data["_year_month"].unique())
    if len(unique_months) >= 2:
        curr_m = unique_months[-1]
        prev_m = unique_months[-2]
        curr_df = data[data["_year_month"] == curr_m]
        prev_df = data[data["_year_month"] == prev_m]
        mom_result = _compare_slices(
            curr_df, prev_df, "month_over_month", str(curr_m), str(prev_m)
        )

    # 2. Week-over-Week
    wow_result = None
    data["_year_week"] = data["_dt"].dt.to_period("W")
    unique_weeks = sorted(data["_year_week"].unique())
    if len(unique_weeks) >= 2:
        curr_w = unique_weeks[-1]
        prev_w = unique_weeks[-2]
        curr_df = data[data["_year_week"] == curr_w]
        prev_df = data[data["_year_week"] == prev_w]
        wow_result = _compare_slices(
            curr_df, prev_df, "week_over_week", str(curr_w), str(prev_w)
        )

    # 3. Two-Half Period Split (fallback for general comparisons regardless of duration)
    min_date = data["_dt"].min()
    max_date = data["_dt"].max()
    mid_date = min_date + (max_date - min_date) / 2

    first_half = data[data["_dt"] <= mid_date]
    second_half = data[data["_dt"] > mid_date]

    split_result = None
    if not first_half.empty and not second_half.empty:
        p1_label = f"{min_date.strftime('%Y-%m-%d')} to {mid_date.strftime('%Y-%m-%d')}"
        p2_label = f"{(mid_date + pd.Timedelta(seconds=1)).strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}"
        split_result = _compare_slices(
            second_half, first_half, "halves_split", p2_label, p1_label
        )

    return {
        "status": "success",
        "date_range": {
            "start": min_date.strftime("%Y-%m-%d"),
            "end": max_date.strftime("%Y-%m-%d"),
            "total_days": safe_int((max_date - min_date).days) + 1,
        },
        "month_over_month": mom_result,
        "week_over_week": wow_result,
        "period_split": split_result,
    }


__all__ = ["analyze_period_over_period"]
