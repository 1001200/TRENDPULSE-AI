"""
TrendPulse Inventory Health, Sell-Through & Stockout Risk Engine.

Calculates Sell-Through Rate (STR %), Weeks of Supply (WOS), Days of Inventory (DOI),
and flags high-risk styles at risk of imminent stockout or overstock stagnation.

Design rules:
    - Deterministic; zero side-effects on input DataFrame.
    - JSON-safe return structure.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from data_engine.utils import clean_number, safe_float, safe_int


def analyze_inventory_health(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze inventory turnover velocity, Sell-Through Rates, and stockout hazards.
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return {
            "status": "no_data",
            "message": "DataFrame is empty.",
            "overall_sell_through_rate": 0.0,
            "stockout_risk_alerts": [],
            "overstock_alerts": [],
            "sku_inventory_metrics": [],
        }

    data = df.copy()

    # Numerical columns prep
    if "quantity" in data.columns:
        data["_qty"] = pd.to_numeric(data["quantity"], errors="coerce").fillna(0.0)
    else:
        data["_qty"] = 1.0

    # Stock on hand
    if "stock" in data.columns and data["stock"].notna().any():
        data["_stock"] = pd.to_numeric(data["stock"], errors="coerce").fillna(0.0)
    else:
        # If no explicit stock column, estimate based on realistic apparel batch sizing
        data["_stock"] = data["_qty"] * 1.5

    # Group by SKU
    sku_col = "product" if "product" in data.columns else data.columns[0]
    sku_grp = data.groupby(sku_col).agg(
        units_sold=("_qty", "sum"),
        current_stock=("_stock", "mean"),
    ).reset_index()

    # Calculate date span in weeks for sales velocity
    weeks_span = 4.0
    if "date" in data.columns:
        dt = pd.to_datetime(data["date"], errors="coerce").dropna()
        if len(dt) >= 2:
            days = (dt.max() - dt.min()).days
            weeks_span = max(1.0, days / 7.0)

    sku_metrics = []
    stockout_alerts = []
    overstock_alerts = []

    total_sold = float(sku_grp["units_sold"].sum())
    total_stock = float(sku_grp["current_stock"].sum())
    total_starting_inv = total_sold + total_stock
    overall_str = (total_sold / total_starting_inv * 100) if total_starting_inv > 0 else 0.0

    for _, row in sku_grp.iterrows():
        sku_name = str(row[sku_col])
        sold = float(row["units_sold"])
        stock = float(row["current_stock"])
        start_inv = sold + stock

        str_pct = (sold / start_inv * 100) if start_inv > 0 else 0.0
        weekly_velocity = sold / weeks_span
        wos = (stock / weekly_velocity) if weekly_velocity > 0 else (99.0 if stock > 0 else 0.0)
        doi = wos * 7.0

        # Health status
        if wos <= 1.5 and weekly_velocity > 0:
            health_status = "CRITICAL STOCKOUT RISK 🚨"
            stockout_alerts.append({
                "sku": sku_name,
                "current_stock": clean_number(stock),
                "weekly_velocity": clean_number(weekly_velocity),
                "weeks_of_supply": clean_number(wos),
                "alert": f"Only {clean_number(wos)} weeks of inventory remaining at current velocity. Stockout imminent.",
                "recommended_reorder_units": clean_number(weekly_velocity * 6.0),  # 6 weeks buffer
            })
        elif wos <= 3.0 and weekly_velocity > 0:
            health_status = "LOW STOCK WARNING ⚠️"
        elif wos >= 16.0:
            health_status = "OVERSTOCK / STAGNANT ❄️"
            overstock_alerts.append({
                "sku": sku_name,
                "current_stock": clean_number(stock),
                "weeks_of_supply": clean_number(wos),
                "alert": f"Holding {clean_number(wos)} weeks of supply. Consider bundling or promotional markdown.",
            })
        else:
            health_status = "HEALTHY VELOCITY ✅"

        sku_metrics.append({
            "sku": sku_name,
            "units_sold": clean_number(sold),
            "current_stock": clean_number(stock),
            "sell_through_rate": clean_number(str_pct),
            "weekly_sales_velocity": clean_number(weekly_velocity),
            "weeks_of_supply": clean_number(wos),
            "days_of_inventory": clean_number(doi),
            "health_status": health_status,
        })

    sku_metrics.sort(key=lambda x: safe_float(x["weeks_of_supply"]))

    return {
        "status": "success",
        "overall_sell_through_rate": clean_number(overall_str),
        "total_units_sold": clean_number(total_sold),
        "total_current_stock": clean_number(total_stock),
        "critical_stockouts_count": len(stockout_alerts),
        "stockout_risk_alerts": stockout_alerts[:10],
        "overstock_alerts": overstock_alerts[:10],
        "sku_inventory_metrics": sku_metrics[:20],
    }


__all__ = ["analyze_inventory_health"]
