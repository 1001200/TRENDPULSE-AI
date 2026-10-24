"""
TrendPulse Performance Driver Attribution.

Identifies and ranks the exact operational drivers (Products, Categories, and Customer Cohorts)
responsible for revenue growth or contraction:
    - Positive Growth Contributors (Top outperforming SKUs & Categories)
    - Negative Revenue Drags (Underperforming or declining SKUs)
    - Pareto Concentration Analysis (80/20 driver identification)
    - Attribution % to total commercial variance

Design rules:
    - Deterministic; zero side-effects on input DataFrame.
    - JSON-safe return structure.
    - Operates on full historical dataset or period comparisons.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from data_engine.utils import clean_number, safe_float, safe_int


def analyze_performance_drivers(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze product, category, and customer performance drivers and revenue attribution.
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return {
            "status": "no_data",
            "message": "DataFrame is empty.",
            "top_revenue_drivers": [],
            "growth_contributors": [],
            "revenue_drags": [],
            "category_attribution": [],
            "pareto_summary": {},
        }

    data = df.copy()

    # Prepare numeric revenue
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

    total_revenue = float(data["_rev"].sum())

    # 1. Product Revenue Concentration & Pareto Analysis
    pareto_summary = {}
    top_revenue_drivers: List[Dict[str, Any]] = []

    if "product" in data.columns and total_revenue > 0:
        data["_prod"] = data["product"].astype(str).str.strip()
        prod_rev = data.groupby("_prod")["_rev"].sum().sort_values(ascending=False)

        cum_share = 0.0
        p80_count = 0
        total_prods = len(prod_rev)

        for prod_name, rev_val in prod_rev.items():
            r_val = float(rev_val)
            share = (r_val / total_revenue) * 100.0
            cum_share += share

            if p80_count == 0 and cum_share >= 80.0:
                p80_count = len(top_revenue_drivers) + 1

            top_revenue_drivers.append({
                "product": str(prod_name),
                "revenue": clean_number(r_val),
                "revenue_share_percentage": clean_number(share),
                "cumulative_share_percentage": clean_number(min(100.0, cum_share)),
            })

        if p80_count == 0:
            p80_count = total_prods

        pareto_summary = {
            "total_products": total_prods,
            "products_for_80_pct_revenue": p80_count,
            "percentage_of_catalog_for_80_pct_revenue": clean_number((p80_count / total_prods * 100.0) if total_prods > 0 else 100.0),
            "top_product": top_revenue_drivers[0]["product"] if top_revenue_drivers else None,
            "top_product_share": top_revenue_drivers[0]["revenue_share_percentage"] if top_revenue_drivers else 0.0,
            "is_concentrated": bool((p80_count / total_prods) <= 0.20) if total_prods >= 5 else False,
        }

    # 2. Category Revenue Attribution
    category_attribution: List[Dict[str, Any]] = []
    if "category" in data.columns and total_revenue > 0:
        data["_cat"] = data["category"].astype(str).str.strip()
        cat_rev = data.groupby("_cat")["_rev"].sum().sort_values(ascending=False)

        for cat_name, rev_val in cat_rev.items():
            r_val = float(rev_val)
            cat_share = (r_val / total_revenue) * 100.0
            category_attribution.append({
                "category": str(cat_name),
                "revenue": clean_number(r_val),
                "revenue_share_percentage": clean_number(cat_share),
            })

    # 3. Period-over-Period Growth Drivers vs Revenue Drags
    growth_contributors: List[Dict[str, Any]] = []
    revenue_drags: List[Dict[str, Any]] = []

    has_date = "date" in data.columns
    if has_date:
        data["_dt"] = pd.to_datetime(data["date"], errors="coerce")
        valid_dt = data.dropna(subset=["_dt"]).sort_values("_dt")

        if len(valid_dt) >= 2:
            min_d = valid_dt["_dt"].min()
            max_d = valid_dt["_dt"].max()
            mid_d = min_d + (max_d - min_d) / 2

            p1 = valid_dt[valid_dt["_dt"] <= mid_d]
            p2 = valid_dt[valid_dt["_dt"] > mid_d]

            if not p1.empty and not p2.empty and "product" in valid_dt.columns:
                p1_prods = p1.groupby("_prod")["_rev"].sum()
                p2_prods = p2.groupby("_prod")["_rev"].sum()
                all_p = set(p1_prods.index).union(set(p2_prods.index))

                total_variance = float(p2["_rev"].sum() - p1["_rev"].sum())

                deltas = []
                for p_name in all_p:
                    rev_p1 = float(p1_prods.get(p_name, 0.0))
                    rev_p2 = float(p2_prods.get(p_name, 0.0))
                    delta = rev_p2 - rev_p1
                    pct_contrib = (delta / abs(total_variance) * 100.0) if total_variance != 0 else 0.0
                    deltas.append({
                        "product": str(p_name),
                        "prior_period_revenue": clean_number(rev_p1),
                        "recent_period_revenue": clean_number(rev_p2),
                        "revenue_change": clean_number(delta),
                        "contribution_percentage": clean_number(pct_contrib),
                    })

                deltas.sort(key=lambda x: safe_float(x["revenue_change"]), reverse=True)
                growth_contributors = [d for d in deltas if safe_float(d["revenue_change"]) > 0][:5]
                revenue_drags = [d for d in reversed(deltas) if safe_float(d["revenue_change"]) < 0][:5]

    return {
        "status": "success",
        "total_revenue": clean_number(total_revenue),
        "pareto_summary": pareto_summary,
        "top_revenue_drivers": top_revenue_drivers[:10],
        "category_attribution": category_attribution,
        "growth_contributors": growth_contributors,
        "revenue_drags": revenue_drags,
    }


__all__ = ["analyze_performance_drivers"]
