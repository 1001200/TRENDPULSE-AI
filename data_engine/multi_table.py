"""
TrendPulse Multi-Table Relational Ingestion & Auto-Joiner.

Enables enterprise merchants to merge disparate retail tables
(Sales Orders + Inventory/COGS Catalog + Return Logs) into a unified master
analytical dataset with zero data leakage.

Design rules:
    - Pure, immutable joins; input DataFrames are copied.
    - Robust case-insensitive fuzzy key resolution (SKU, Product, Order ID).
    - JSON-safe metadata & audit trail.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import pandas as pd


def _find_key_column(df: pd.DataFrame, candidate_names: Tuple[str, ...]) -> Optional[str]:
    """Find matching column name regardless of casing and underscores."""
    col_map = {c.lower().replace("_", "").replace(" ", ""): c for c in df.columns}
    for cand in candidate_names:
        clean_cand = cand.lower().replace("_", "").replace(" ", "")
        if clean_cand in col_map:
            return col_map[clean_cand]
    return None


def merge_retail_datasets(
    sales_df: pd.DataFrame,
    inventory_df: Optional[pd.DataFrame] = None,
    returns_df: Optional[pd.DataFrame] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Merge sales records with inventory/COGS and returns records.
    Returns: (master_merged_df, merge_audit_report)
    """
    if not isinstance(sales_df, pd.DataFrame) or sales_df.empty:
        return sales_df, {"status": "empty_sales_data", "merged_tables": []}

    master = sales_df.copy(deep=True)
    audit: Dict[str, Any] = {
        "status": "success",
        "initial_sales_rows": len(master),
        "merged_tables": ["sales"],
        "joined_columns": [],
    }

    # 1. Join Inventory / COGS Catalog
    if isinstance(inventory_df, pd.DataFrame) and not inventory_df.empty:
        inv_copy = inventory_df.copy(deep=True)
        sales_sku_key = _find_key_column(master, ("sku", "product", "item_code", "product_name"))
        inv_sku_key = _find_key_column(inv_copy, ("sku", "product", "item_code", "product_name", "barcode"))

        if sales_sku_key and inv_sku_key:
            # Drop conflicting columns except the join key
            non_key_cols = [c for c in inv_copy.columns if c != inv_sku_key and c not in master.columns]
            if non_key_cols:
                inv_subset = inv_copy[[inv_sku_key] + non_key_cols].drop_duplicates(subset=[inv_sku_key])
                master = master.merge(
                    inv_subset,
                    left_on=sales_sku_key,
                    right_on=inv_sku_key,
                    how="left",
                )
                audit["merged_tables"].append("inventory")
                audit["joined_columns"].extend(non_key_cols)

    # 2. Join Returns Log
    if isinstance(returns_df, pd.DataFrame) and not returns_df.empty:
        ret_copy = returns_df.copy(deep=True)
        sales_ord_key = _find_key_column(master, ("order_id", "order_number", "order_ref", "transaction_id"))
        ret_ord_key = _find_key_column(ret_copy, ("order_id", "order_number", "order_ref", "transaction_id"))

        if sales_ord_key and ret_ord_key:
            # Tag returns
            ret_copy["_is_returned"] = True
            reason_col = _find_key_column(ret_copy, ("return_reason", "reason", "issue", "notes"))
            if reason_col:
                ret_copy["return_reason"] = ret_copy[reason_col]
            else:
                ret_copy["return_reason"] = "Customer Return"

            ret_subset = ret_copy[[ret_ord_key, "_is_returned", "return_reason"]].drop_duplicates(subset=[ret_ord_key])
            master = master.merge(
                ret_subset,
                left_on=sales_ord_key,
                right_on=ret_ord_key,
                how="left",
            )
            master["_is_returned"] = master["_is_returned"].fillna(False)
            audit["merged_tables"].append("returns")
            audit["joined_columns"].extend(["_is_returned", "return_reason"])
        else:
            master["_is_returned"] = False

    audit["final_master_rows"] = len(master)
    return master, audit


__all__ = ["merge_retail_datasets"]
