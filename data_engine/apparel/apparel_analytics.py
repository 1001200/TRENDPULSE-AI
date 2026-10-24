"""
TrendPulse Apparel Domain Intelligence Analytics.

Aggregates specialized fashion-specific commercial intelligence:
    - Size Curve distribution & Broken Size Run alerts
    - Colorway velocity & Color Family palette shares
    - Fit & Silhouette demand ranking (Oversized vs Slim vs Regular)
    - Gender / Department revenue breakdown
    - Fabric & Pattern preference analytics

Design rules:
    - Deterministic; zero side-effects on input DataFrame.
    - JSON-safe return structure.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import pandas as pd

from data_engine.apparel.size_normalizer import calculate_size_curves, detect_broken_size_runs
from data_engine.apparel.color_engine import analyze_colorways
from data_engine.utils import clean_number, safe_float, safe_int


def analyze_apparel_domain(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate comprehensive fashion and apparel commercial intelligence.
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return {
            "status": "no_data",
            "message": "DataFrame is empty.",
            "size_intelligence": {},
            "color_intelligence": {},
            "fit_intelligence": [],
            "fabric_intelligence": [],
            "gender_distribution": [],
            "pattern_intelligence": [],
            "broken_size_runs": [],
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

    # 1. Size Curves & Broken Runs
    size_df = data.copy()
    if "std_size" in size_df.columns:
        size_df["size"] = size_df["std_size"]
    size_intel = calculate_size_curves(size_df)
    broken_runs = detect_broken_size_runs(size_df)

    # 2. Colorways & Palettes
    color_df = data.copy()
    if "std_color" in color_df.columns:
        color_df["color"] = color_df["std_color"]
    color_intel = analyze_colorways(color_df)

    # 3. Fit & Silhouette Analysis
    fit_intel = []
    if "fit_type" in data.columns:
        for f_name, f_df in data.groupby("fit_type"):
            rev = float(f_df["_rev"].sum())
            qty = float(f_df["_qty"].sum())
            fit_intel.append({
                "fit": str(f_name),
                "revenue": clean_number(rev),
                "units_sold": clean_number(qty),
                "revenue_share_percentage": clean_number((rev / total_rev * 100) if total_rev > 0 else 0.0),
            })
        fit_intel.sort(key=lambda x: safe_float(x["revenue"]), reverse=True)

    # 4. Fabric / Material Analysis
    fabric_intel = []
    if "fabric_type" in data.columns:
        for fab_name, fab_df in data.groupby("fabric_type"):
            rev = float(fab_df["_rev"].sum())
            qty = float(fab_df["_qty"].sum())
            fabric_intel.append({
                "fabric": str(fab_name),
                "revenue": clean_number(rev),
                "units_sold": clean_number(qty),
                "revenue_share_percentage": clean_number((rev / total_rev * 100) if total_rev > 0 else 0.0),
            })
        fabric_intel.sort(key=lambda x: safe_float(x["revenue"]), reverse=True)

    # 5. Gender / Department Distribution
    gender_dist = []
    if "gender" in data.columns:
        for g_name, g_df in data.groupby("gender"):
            rev = float(g_df["_rev"].sum())
            qty = float(g_df["_qty"].sum())
            gender_dist.append({
                "department": str(g_name),
                "revenue": clean_number(rev),
                "units_sold": clean_number(qty),
                "revenue_share_percentage": clean_number((rev / total_rev * 100) if total_rev > 0 else 0.0),
            })
        gender_dist.sort(key=lambda x: safe_float(x["revenue"]), reverse=True)

    # 6. Pattern / Treatment Analysis
    pattern_intel = []
    if "pattern_type" in data.columns:
        for p_name, p_df in data.groupby("pattern_type"):
            rev = float(p_df["_rev"].sum())
            qty = float(p_df["_qty"].sum())
            pattern_intel.append({
                "pattern": str(p_name),
                "revenue": clean_number(rev),
                "units_sold": clean_number(qty),
                "revenue_share_percentage": clean_number((rev / total_rev * 100) if total_rev > 0 else 0.0),
            })
        pattern_intel.sort(key=lambda x: safe_float(x["revenue"]), reverse=True)

    return {
        "status": "success",
        "total_apparel_revenue": clean_number(total_rev),
        "total_apparel_units": clean_number(total_qty),
        "size_intelligence": size_intel,
        "color_intelligence": color_intel,
        "fit_intelligence": fit_intel,
        "fabric_intelligence": fabric_intel,
        "gender_distribution": gender_dist,
        "pattern_intelligence": pattern_intel,
        "broken_size_runs": broken_runs,
    }


__all__ = ["analyze_apparel_domain"]
