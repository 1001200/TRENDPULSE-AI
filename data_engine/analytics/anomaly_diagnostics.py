"""
TrendPulse Anomaly Root-Cause Diagnostics.

Deeply investigates detected statistical anomalies and diagnoses *why* they occurred:
    - Customer Concentration Diagnosis (Wholesale / B2B bulk buy vs widespread surge)
    - Pricing Distortion vs Volume Spike Classification
    - Single-SKU vs Catalog-wide Outlier Pattern Detection
    - Baseline Forecasting Guidance (Exclude, Adjust, or Keep)

Design rules:
    - Deterministic; zero side-effects on input DataFrame.
    - JSON-safe return structure with actionable root-cause narratives.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from data_engine.utils import clean_number, safe_float, safe_int


def diagnose_anomalies(
    df: pd.DataFrame,
    anomalies: Optional[List[Dict[str, Any]]] = None,
    anomaly_summary: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Diagnose root causes and commercial context for detected statistical anomalies.
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return {
            "status": "no_data",
            "message": "DataFrame is empty.",
            "total_anomalous_records": 0,
            "root_causes": [],
            "diagnoses": [],
            "forecasting_guidance": "No data to analyze.",
        }

    if not anomalies:
        return {
            "status": "no_anomalies",
            "message": "No statistical anomalies detected in dataset.",
            "total_anomalous_records": 0,
            "root_causes": [],
            "diagnoses": [],
            "forecasting_guidance": "Data is clean and suitable for standard time-series forecasting.",
        }

    data = df.copy()

    # Extract anomaly row indices
    anomaly_indices = set()
    for anom in anomalies:
        row_idx = anom.get("row")
        if row_idx is not None and row_idx in data.index:
            anomaly_indices.add(row_idx)

    if not anomaly_indices:
        return {
            "status": "no_matched_rows",
            "message": "Anomaly row indices do not match DataFrame index.",
            "total_anomalous_records": 0,
            "root_causes": [],
            "diagnoses": [],
            "forecasting_guidance": "Anomaly indices could not be resolved.",
        }

    anom_df = data.loc[list(anomaly_indices)].copy()
    normal_df = data.drop(index=list(anomaly_indices), errors="ignore").copy()

    # Numerical columns prep
    for d in (data, anom_df, normal_df):
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

    # 1. Root Cause Breakdown
    diagnoses: List[Dict[str, Any]] = []
    cause_tallies: Dict[str, int] = {
        "wholesale_bulk_order": 0,
        "price_distortion": 0,
        "volume_spike": 0,
        "isolated_high_value_transaction": 0,
    }

    # Baseline benchmarks from clean normal data
    bench_price_by_prod = normal_df.groupby("product")["_price"].mean().to_dict() if "product" in normal_df.columns else {}
    overall_mean_qty = float(normal_df["_qty"].mean()) if not normal_df.empty else 1.0
    overall_mean_price = float(normal_df["_price"].mean()) if not normal_df.empty else 1.0

    for idx, row in anom_df.iterrows():
        qty = float(row.get("_qty", 0.0))
        price = float(row.get("_price", 0.0))
        rev = float(row.get("_rev", 0.0))
        prod = str(row.get("product", "Unknown"))
        cust = str(row.get("customer_id", "Unknown"))
        dt = str(row.get("date", "Unknown"))

        prod_bench_price = bench_price_by_prod.get(prod, overall_mean_price)

        # Classification logic
        if qty >= max(10, overall_mean_qty * 4):
            cause_type = "wholesale_bulk_order" if cust != "Unknown" else "volume_spike"
            cause_desc = f"Outsized unit quantity of {clean_number(qty)} units (vs typical average of {clean_number(overall_mean_qty)} units)."
        elif prod_bench_price > 0 and (price >= prod_bench_price * 2.5 or price <= prod_bench_price * 0.4):
            cause_type = "price_distortion"
            cause_desc = f"Unit price of {clean_number(price)} deviates heavily from standard product baseline price of {clean_number(prod_bench_price)}."
        else:
            cause_type = "isolated_high_value_transaction"
            cause_desc = f"Transaction total revenue of {clean_number(rev)} is an outsized statistical outlier."

        cause_tallies[cause_type] = cause_tallies.get(cause_type, 0) + 1

        diagnoses.append({
            "row_index": safe_int(idx),
            "date": dt,
            "product": prod,
            "customer_id": cust,
            "quantity": clean_number(qty),
            "price": clean_number(price),
            "revenue": clean_number(rev),
            "root_cause_type": cause_type,
            "root_cause_explanation": cause_desc,
        })

    # 2. Macro Pattern Analysis across all anomalies
    root_cause_summary = []
    total_anom_count = len(anom_df)

    # Check customer concentration
    if "customer_id" in anom_df.columns:
        cust_counts = anom_df["customer_id"].value_counts()
        if not cust_counts.empty:
            top_cust = str(cust_counts.index[0])
            top_cust_count = int(cust_counts.iloc[0])
            if (top_cust_count / total_anom_count) >= 0.50 and top_cust != "Unknown":
                root_cause_summary.append({
                    "pattern": "single_customer_concentration",
                    "severity": "high",
                    "summary": f"Customer '{top_cust}' accounts for {top_cust_count} of {total_anom_count} ({clean_number(top_cust_count/total_anom_count*100)}%) anomalous transactions.",
                })

    # Check product concentration
    if "product" in anom_df.columns:
        prod_counts = anom_df["product"].value_counts()
        if not prod_counts.empty:
            top_prod = str(prod_counts.index[0])
            top_prod_count = int(prod_counts.iloc[0])
            if (top_prod_count / total_anom_count) >= 0.50:
                root_cause_summary.append({
                    "pattern": "single_product_concentration",
                    "severity": "medium",
                    "summary": f"Product '{top_prod}' represents {top_prod_count} of {total_anom_count} ({clean_number(top_prod_count/total_anom_count*100)}%) anomalous transactions.",
                })

    # Guidance for ML & Forecasting
    anom_rev_share = (float(anom_df["_rev"].sum()) / float(data["_rev"].sum()) * 100) if float(data["_rev"].sum()) > 0 else 0.0

    if anom_rev_share >= 40.0:
        guidance = "CRITICAL: Detected anomalies account for over 40% of observed revenue. Baseline demand forecasting MUST use anomaly-adjusted clean data to prevent massive inventory over-ordering."
    elif cause_tallies.get("wholesale_bulk_order", 0) > 0:
        guidance = "One-off B2B bulk orders detected. Recommend separating wholesale bulk demand from D2C retail forecasting models."
    else:
        guidance = "Anomalies are isolated. Use standard robust trend filtering for downstream predictive modeling."

    return {
        "status": "success",
        "total_anomalous_records": total_anom_count,
        "anomalous_revenue_share_percentage": clean_number(anom_rev_share),
        "primary_root_causes": cause_tallies,
        "patterns_detected": root_cause_summary,
        "forecasting_guidance": guidance,
        "diagnoses": diagnoses[:10],
    }


__all__ = ["diagnose_anomalies"]
