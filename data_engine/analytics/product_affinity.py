"""
TrendPulse Product Affinity & Market Basket Intelligence.

Analyzes product co-purchases across baskets (orders or customer-date pairs):
    - Top co-purchased product pairs
    - Support, Confidence, and Lift metrics for bundle recommendations
    - Cross-category affinity (e.g., T-Shirts + Jeans)

Design rules:
    - Deterministic; zero side-effects on input DataFrame.
    - JSON-safe return structure.
    - Robust fallback when order_id is absent (derives baskets from customer_id + date).
"""

from __future__ import annotations

from collections import Counter
from itertools import combinations
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from data_engine.utils import clean_number, safe_float, safe_int


def analyze_product_affinity(df: pd.DataFrame, top_n: int = 10) -> Dict[str, Any]:
    """
    Compute product and category affinity rules from basket transactions.
    """
    if not isinstance(df, pd.DataFrame) or df.empty or "product" not in df.columns:
        return {
            "status": "no_data",
            "message": "DataFrame is empty or lacks product column.",
            "total_baskets": 0,
            "multi_item_baskets": 0,
            "top_product_pairs": [],
            "category_affinity": [],
        }

    data = df.copy()
    data["_prod"] = data["product"].astype(str).str.strip()
    data = data[~data["_prod"].isin(["", "nan", "None", "null"])]

    if data.empty:
        return {
            "status": "insufficient_data",
            "message": "No valid products found.",
            "total_baskets": 0,
            "multi_item_baskets": 0,
            "top_product_pairs": [],
            "category_affinity": [],
        }

    # Determine basket identifier: order_id > (customer_id + date) > (customer_id)
    basket_col = None
    if "order_id" in data.columns and data["order_id"].notna().sum() > 0:
        data["_basket"] = data["order_id"].astype(str).str.strip()
        basket_col = "order_id"
    elif "customer_id" in data.columns and "date" in data.columns:
        data["_basket"] = data["customer_id"].astype(str) + "::" + data["date"].astype(str)
        basket_col = "customer_date"
    elif "customer_id" in data.columns:
        data["_basket"] = data["customer_id"].astype(str).str.strip()
        basket_col = "customer_id"
    else:
        return {
            "status": "no_basket_identifier",
            "message": "Neither order_id nor customer_id is available to identify baskets.",
            "total_baskets": 0,
            "multi_item_baskets": 0,
            "top_product_pairs": [],
            "category_affinity": [],
        }

    # Filter out empty basket ids
    data = data[~data["_basket"].isin(["", "nan", "None", "null", "nan::nan"])]
    
    # Map products & categories to each basket
    basket_products: Dict[str, set] = {}
    basket_categories: Dict[str, set] = {}
    has_cat = "category" in data.columns

    for _, row in data.iterrows():
        b_id = row["_basket"]
        prod = row["_prod"]
        if b_id not in basket_products:
            basket_products[b_id] = set()
            if has_cat:
                basket_categories[b_id] = set()
        basket_products[b_id].add(prod)
        if has_cat and pd.notna(row.get("category")):
            basket_categories[b_id].add(str(row["category"]).strip())

    total_baskets = len(basket_products)
    multi_item_baskets = sum(1 for prods in basket_products.values() if len(prods) > 1)

    if total_baskets == 0 or multi_item_baskets == 0:
        return {
            "status": "single_item_baskets_only",
            "message": "All identified baskets contain only single distinct items.",
            "total_baskets": total_baskets,
            "multi_item_baskets": 0,
            "basket_source": basket_col,
            "top_product_pairs": [],
            "category_affinity": [],
        }

    # 1. Product Item Frequencies & Co-occurrences
    item_counts: Counter = Counter()
    pair_counts: Counter = Counter()

    for prods in basket_products.values():
        for p in prods:
            item_counts[p] += 1
        if len(prods) > 1:
            for pair in combinations(sorted(prods), 2):
                pair_counts[pair] += 1

    top_pairs: List[Dict[str, Any]] = []
    for (item_a, item_b), count in pair_counts.most_common(top_n):
        # Metrics:
        support = count / total_baskets
        conf_a_b = count / item_counts[item_a] if item_counts[item_a] > 0 else 0.0
        conf_b_a = count / item_counts[item_b] if item_counts[item_b] > 0 else 0.0
        expected_prob = (item_counts[item_a] / total_baskets) * (item_counts[item_b] / total_baskets)
        lift = (support / expected_prob) if expected_prob > 0 else 1.0

        top_pairs.append({
            "product_a": item_a,
            "product_b": item_b,
            "co_occurrence_count": safe_int(count),
            "support_percentage": clean_number(support * 100.0),
            "confidence_a_to_b": clean_number(conf_a_b * 100.0),
            "confidence_b_to_a": clean_number(conf_b_a * 100.0),
            "lift": clean_number(lift),
            "bundle_recommendation": f"Customers buying '{item_a}' are {clean_number(lift)}x more likely to also buy '{item_b}'.",
        })

    # 2. Category Cross-Affinity
    cat_pair_counts: Counter = Counter()
    if has_cat:
        for cats in basket_categories.values():
            if len(cats) > 1:
                for c_pair in combinations(sorted(cats), 2):
                    cat_pair_counts[c_pair] += 1

    top_cat_pairs: List[Dict[str, Any]] = []
    for (cat_a, cat_b), count in cat_pair_counts.most_common(top_n):
        top_cat_pairs.append({
            "category_a": cat_a,
            "category_b": cat_b,
            "co_occurrence_count": safe_int(count),
            "percentage_of_multi_category_baskets": clean_number((count / multi_item_baskets) * 100.0) if multi_item_baskets > 0 else 0.0,
        })

    return {
        "status": "success",
        "basket_source": basket_col,
        "total_baskets": total_baskets,
        "multi_item_baskets": multi_item_baskets,
        "multi_item_basket_rate": clean_number((multi_item_baskets / total_baskets) * 100.0),
        "top_product_pairs": top_pairs,
        "category_affinity": top_cat_pairs,
    }


__all__ = ["analyze_product_affinity"]
