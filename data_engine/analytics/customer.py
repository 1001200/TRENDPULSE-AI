"""
TrendPulse Customer Analytics & Segmentation.

Computes comprehensive deterministic customer intelligence:
    - Customer count & repeat rate
    - Order frequency distributions
    - Top customers by revenue and transaction count
    - RFM (Recency, Frequency, Monetary) segmentation & cohort classification

Design rules:
    - Deterministic; zero side-effects on input DataFrame.
    - JSON-safe return structure.
    - Gracefully handles absent or sparse customer_id fields.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from data_engine.utils import clean_number, safe_float, safe_int


def _assign_rfm_segment(r_score: int, f_score: int, m_score: int) -> str:
    """Assign business-meaningful clothing customer segment based on RFM scores (1 to 3)."""
    # High recency (3 = recent), High frequency (3 = frequent), High monetary (3 = high spend)
    if r_score >= 3 and f_score >= 3 and m_score >= 3:
        return "VIP / Champions"
    elif r_score >= 2 and f_score >= 2:
        return "Loyal Customers"
    elif r_score >= 3 and f_score == 1:
        return "New / Promising"
    elif r_score == 2 and f_score == 1:
        return "Occasional Shoppers"
    elif r_score == 1 and f_score >= 2:
        return "At Risk (High Past Value)"
    elif r_score == 1 and f_score == 1 and m_score >= 2:
        return "Dormant High-Spenders"
    else:
        return "Lost / Inactive"


def analyze_customers(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate customer behavior analytics and RFM segmentation.
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return {
            "status": "no_data",
            "message": "DataFrame is empty.",
            "metrics": {},
            "segments": [],
            "top_customers": [],
        }

    if "customer_id" not in df.columns:
        return {
            "status": "column_missing",
            "message": "No customer_id column identified in dataset.",
            "metrics": {},
            "segments": [],
            "top_customers": [],
        }

    data = df.copy()
    data["_cust"] = data["customer_id"].astype(str).str.strip()
    data = data[~data["_cust"].isin(["", "nan", "None", "null"])]

    if data.empty:
        return {
            "status": "insufficient_data",
            "message": "No valid customer identifiers found.",
            "metrics": {},
            "segments": [],
            "top_customers": [],
        }

    # Prepare revenue
    if "revenue" in data.columns:
        data["_rev"] = pd.to_numeric(data["revenue"], errors="coerce").fillna(0.0)
    elif "quantity" in data.columns and "price" in data.columns:
        q = pd.to_numeric(data["quantity"], errors="coerce").fillna(0.0)
        p = pd.to_numeric(data["price"], errors="coerce").fillna(0.0)
        data["_rev"] = q * p
    else:
        data["_rev"] = 0.0

    # Prepare date for recency
    has_date = "date" in data.columns
    if has_date:
        data["_dt"] = pd.to_datetime(data["date"], errors="coerce")
        max_date = data["_dt"].max()
    else:
        max_date = None

    # Aggregations per customer
    customer_groups = data.groupby("_cust")
    
    cust_metrics = customer_groups.agg(
        total_spend=("_rev", "sum"),
        order_count=("_cust", "count"),
    )

    if has_date and max_date is not None and pd.notna(max_date):
        last_dates = customer_groups["_dt"].max()
        cust_metrics["last_purchase_date"] = last_dates
        cust_metrics["recency_days"] = (max_date - last_dates).dt.days.fillna(0).astype(int)
    else:
        cust_metrics["recency_days"] = 0

    total_customers = len(cust_metrics)
    total_revenue = float(cust_metrics["total_spend"].sum())
    repeat_customers = int((cust_metrics["order_count"] > 1).sum())
    single_order_customers = total_customers - repeat_customers

    repeat_rate = (repeat_customers / total_customers * 100.0) if total_customers > 0 else 0.0
    arpu = (total_revenue / total_customers) if total_customers > 0 else 0.0
    avg_orders_per_cust = float(cust_metrics["order_count"].mean()) if total_customers > 0 else 0.0

    # ----------------------------------------------------
    # RFM Scoring & Segmentation
    # ----------------------------------------------------
    # Recency: lower days is better (rank 3 > 2 > 1)
    if total_customers >= 3 and has_date:
        try:
            r_scores = pd.qcut(
                cust_metrics["recency_days"].rank(method="first", ascending=False),
                q=3,
                labels=[1, 2, 3]
            ).astype(int)
        except Exception:
            r_scores = pd.Series(2, index=cust_metrics.index)
    else:
        r_scores = pd.Series(2, index=cust_metrics.index)

    # Frequency: higher order_count is better (rank 3 > 2 > 1)
    if total_customers >= 3 and (cust_metrics["order_count"].max() > cust_metrics["order_count"].min()):
        try:
            f_scores = pd.qcut(
                cust_metrics["order_count"].rank(method="first"),
                q=3,
                labels=[1, 2, 3]
            ).astype(int)
        except Exception:
            f_scores = pd.Series(2, index=cust_metrics.index)
    else:
        f_scores = pd.Series(
            np.where(cust_metrics["order_count"] > 1, 3, 1),
            index=cust_metrics.index
        )

    # Monetary: higher total_spend is better (rank 3 > 2 > 1)
    if total_customers >= 3 and (cust_metrics["total_spend"].max() > cust_metrics["total_spend"].min()):
        try:
            m_scores = pd.qcut(
                cust_metrics["total_spend"].rank(method="first"),
                q=3,
                labels=[1, 2, 3]
            ).astype(int)
        except Exception:
            m_scores = pd.Series(2, index=cust_metrics.index)
    else:
        m_scores = pd.Series(2, index=cust_metrics.index)

    cust_metrics["r_score"] = r_scores
    cust_metrics["f_score"] = f_scores
    cust_metrics["m_score"] = m_scores

    segments = []
    for idx, row in cust_metrics.iterrows():
        seg = _assign_rfm_segment(int(row["r_score"]), int(row["f_score"]), int(row["m_score"]))
        segments.append(seg)
    cust_metrics["segment"] = segments

    # Segment summary
    segment_summary = []
    for seg_name, seg_df in cust_metrics.groupby("segment"):
        seg_count = len(seg_df)
        seg_rev = float(seg_df["total_spend"].sum())
        segment_summary.append({
            "segment": str(seg_name),
            "customer_count": seg_count,
            "customer_percentage": clean_number((seg_count / total_customers) * 100.0),
            "total_revenue": clean_number(seg_rev),
            "revenue_percentage": clean_number((seg_rev / total_revenue * 100.0) if total_revenue > 0 else 0.0),
            "average_order_value": clean_number(seg_rev / seg_df["order_count"].sum() if seg_df["order_count"].sum() > 0 else 0.0),
        })

    segment_summary.sort(key=lambda x: safe_float(x["total_revenue"]), reverse=True)

    # Top Customers by Revenue
    top_revenue_custs = cust_metrics.sort_values("total_spend", ascending=False).head(5)
    top_by_revenue = []
    for cust_id, row in top_revenue_custs.iterrows():
        top_by_revenue.append({
            "customer_id": str(cust_id),
            "total_spend": clean_number(row["total_spend"]),
            "order_count": safe_int(row["order_count"]),
            "segment": str(row["segment"]),
            "recency_days": safe_int(row["recency_days"]),
        })

    # Frequency distribution
    freq_bins = {
        "1_order": int((cust_metrics["order_count"] == 1).sum()),
        "2_to_3_orders": int(((cust_metrics["order_count"] >= 2) & (cust_metrics["order_count"] <= 3)).sum()),
        "4_to_10_orders": int(((cust_metrics["order_count"] >= 4) & (cust_metrics["order_count"] <= 10)).sum()),
        "10+_orders": int((cust_metrics["order_count"] > 10).sum()),
    }

    return {
        "status": "success",
        "overview": {
            "total_customers": total_customers,
            "repeat_customers": repeat_customers,
            "single_purchase_customers": single_order_customers,
            "repeat_customer_rate": clean_number(repeat_rate),
            "average_revenue_per_customer": clean_number(arpu),
            "average_orders_per_customer": clean_number(avg_orders_per_cust),
            "total_customer_revenue": clean_number(total_revenue),
        },
        "frequency_distribution": freq_bins,
        "segments": segment_summary,
        "top_customers_by_revenue": top_by_revenue,
    }


__all__ = ["analyze_customers"]
