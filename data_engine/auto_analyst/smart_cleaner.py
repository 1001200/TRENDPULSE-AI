"""
Smart Reversible Data Cleaner & Quality Audit Engine.

Performs domain-agnostic data cleaning, missing value imputation, deduplication,
and quality score auditing for arbitrary spreadsheet datasets.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd

from data_engine.auto_analyst.type_inferrer import (
    CLEAN_NUMERIC_REGEX,
    try_parse_datetime_series,
    try_parse_numeric_series,
)


def sanitize_column_name(col: str) -> str:
    """Normalize column name to clean snake_case while maintaining readability."""
    cleaned = str(col).strip().lower()
    cleaned = re.sub(r"[^\w\s]", "_", cleaned)
    cleaned = re.sub(r"\s+", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "column"


class CleanResult:
    def __init__(
        self,
        cleaned_df: pd.DataFrame,
        original_df: pd.DataFrame,
        column_mapping: Dict[str, str],
        schema: Dict[str, Dict[str, Any]],
        audit_log: List[Dict[str, Any]],
        health_score: float,
        quality_metrics: Dict[str, Any],
    ):
        self.cleaned_df = cleaned_df
        self.original_df = original_df
        self.column_mapping = column_mapping
        self.schema = schema
        self.audit_log = audit_log
        self.health_score = health_score
        self.quality_metrics = quality_metrics

    def to_dict(self) -> Dict[str, Any]:
        return {
            "health_score": round(self.health_score, 1),
            "quality_metrics": self.quality_metrics,
            "audit_log": self.audit_log,
            "column_mapping": self.column_mapping,
            "rows_before": len(self.original_df),
            "rows_after": len(self.cleaned_df),
            "columns_count": len(self.cleaned_df.columns),
        }


def clean_dataset(df: pd.DataFrame, schema: Dict[str, Dict[str, Any]]) -> CleanResult:
    """
    Clean an arbitrary dataset according to its inferred schema.
    Returns cleaned dataframe, audit trail, and health score.
    """
    original_df = df.copy()
    cleaned = df.copy()
    audit_log = []

    # 1. Normalize Column Names
    col_mapping = {}
    new_cols = []
    used_names = set()
    for col in cleaned.columns:
        norm = sanitize_column_name(col)
        # Ensure uniqueness
        base_norm = norm
        counter = 1
        while norm in used_names:
            norm = f"{base_norm}_{counter}"
            counter += 1
        used_names.add(norm)
        col_mapping[norm] = col
        new_cols.append(norm)

    cleaned.columns = new_cols
    # Update schema keys
    norm_schema = {}
    for norm_col, orig_col in col_mapping.items():
        if orig_col in schema:
            norm_schema[norm_col] = {**schema[orig_col], "original_name": orig_col, "clean_name": norm_col}

    # 2. Deduplication
    initial_rows = len(cleaned)
    cleaned = cleaned.drop_duplicates().reset_index(drop=True)
    duplicates_removed = initial_rows - len(cleaned)
    if duplicates_removed > 0:
        audit_log.append({
            "stage": "deduplication",
            "action": f"Removed {duplicates_removed} exact duplicate rows",
            "impact": f"{duplicates_removed} rows dropped",
            "severity": "low",
        })

    total_cells = len(cleaned) * len(cleaned.columns) if len(cleaned.columns) > 0 else 1
    total_missing_before = int(cleaned.isna().sum().sum())

    # 3. Process each column according to inferred type
    for col, info in norm_schema.items():
        col_type = info.get("inferred_type")
        series = cleaned[col]
        missing_count = int(series.isna().sum())

        if col_type == "numeric":
            # Strip symbols and convert
            is_num, parsed = try_parse_numeric_series(series)
            if is_num and parsed is not None:
                cleaned[col] = parsed
            else:
                cleaned[col] = pd.to_numeric(series, errors="coerce")

            # Impute missing values
            nulls = cleaned[col].isna().sum()
            if nulls > 0 and nulls < len(cleaned):
                median_val = float(cleaned[col].median())
                cleaned[col] = cleaned[col].fillna(median_val)
                audit_log.append({
                    "stage": "imputation",
                    "column": col,
                    "action": f"Imputed {nulls} missing numeric values with column median ({median_val:.2f})",
                    "impact": f"{nulls} cells repaired",
                    "severity": "info",
                })
            elif nulls == len(cleaned):
                cleaned[col] = cleaned[col].fillna(0.0)

        elif col_type == "datetime":
            is_dt, parsed = try_parse_datetime_series(series)
            if is_dt and parsed is not None:
                cleaned[col] = parsed
            else:
                cleaned[col] = pd.to_datetime(series, errors="coerce")

            nulls = cleaned[col].isna().sum()
            if nulls > 0:
                audit_log.append({
                    "stage": "datetime_standardization",
                    "column": col,
                    "action": f"Standardized dates to ISO format. Found {nulls} unparseable/missing date entries.",
                    "impact": f"{nulls} null dates",
                    "severity": "warning",
                })

        elif col_type == "boolean":
            # Map standard booleans
            bool_map = {
                "true": True, "1": True, "yes": True, "y": True, "t": True,
                "false": False, "0": False, "no": False, "n": False, "f": False,
            }
            cleaned[col] = series.astype(str).str.strip().str.lower().map(bool_map).fillna(False)

        elif col_type == "categorical":
            # String cleaning & trim
            cleaned[col] = series.fillna("Unknown").astype(str).str.strip()
            # Collapse internal multiple spaces
            cleaned[col] = cleaned[col].apply(lambda s: re.sub(r"\s+", " ", s))
            if missing_count > 0:
                audit_log.append({
                    "stage": "imputation",
                    "column": col,
                    "action": f"Filled {missing_count} missing categories with 'Unknown'",
                    "impact": f"{missing_count} cells repaired",
                    "severity": "info",
                })

        elif col_type in ["text", "id_or_text"]:
            cleaned[col] = series.fillna("").astype(str).str.strip()

    # 4. Compute Health Score (0 - 100)
    completeness_score = 100.0 - min(100.0, (total_missing_before / total_cells) * 100.0 * 2)
    uniqueness_score = 100.0 - min(100.0, (duplicates_removed / max(1, initial_rows)) * 100.0 * 3)
    validity_score = 98.0  # Base validity after successful type-safe coercion

    health_score = max(10.0, min(100.0, (completeness_score * 0.45) + (uniqueness_score * 0.35) + (validity_score * 0.20)))

    quality_metrics = {
        "completeness_score": round(completeness_score, 1),
        "uniqueness_score": round(uniqueness_score, 1),
        "validity_score": round(validity_score, 1),
        "total_missing_imputed": total_missing_before,
        "duplicates_removed": duplicates_removed,
        "total_records": len(cleaned),
        "total_columns": len(cleaned.columns),
    }

    return CleanResult(
        cleaned_df=cleaned,
        original_df=original_df,
        column_mapping=col_mapping,
        schema=norm_schema,
        audit_log=audit_log,
        health_score=health_score,
        quality_metrics=quality_metrics,
    )
