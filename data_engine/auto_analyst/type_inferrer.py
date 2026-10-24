"""
Zero-Shot Column Type Inferrer.

Automatically detects column types (datetime, numeric, categorical, boolean, text/id)
across arbitrary, unseen spreadsheet datasets without prior domain knowledge.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd


# Regex for stripping common currency symbols, commas, and percentage signs
CLEAN_NUMERIC_REGEX = re.compile(r"[\$,€£₹¥%,\s]")


def is_boolean_series(series: pd.Series) -> bool:
    """Check if series consists of boolean-like values."""
    non_null = series.dropna()
    if non_null.empty:
        return False
    unique_vals = set(non_null.astype(str).str.strip().str.lower().unique())
    bool_sets = [
        {"true", "false"},
        {"yes", "no"},
        {"y", "n"},
        {"0", "1"},
        {"t", "f"},
    ]
    return any(unique_vals.issubset(b_set) for b_set in bool_sets)


def try_parse_numeric_series(series: pd.Series) -> Tuple[bool, pd.Series | None]:
    """
    Attempt to parse a series as numeric, handling currency symbols, commas,
    percentages, and accounting parentheses for negative numbers: (100.5) -> -100.5.
    """
    if pd.api.types.is_numeric_dtype(series):
        return True, series

    non_null = series.dropna()
    if non_null.empty:
        return False, None

    sample = non_null.astype(str).str.strip()
    # Replace accounting parentheses: (123.45) -> -123.45
    sample_cleaned = sample.apply(lambda s: f"-{s[1:-1]}" if isinstance(s, str) and s.startswith("(") and s.endswith(")") else s)
    # Strip symbols
    sample_cleaned = sample_cleaned.apply(lambda s: CLEAN_NUMERIC_REGEX.sub("", s) if isinstance(s, str) else s)

    # Try numeric conversion
    converted = pd.to_numeric(sample_cleaned, errors="coerce")
    success_rate = converted.notna().sum() / len(sample)

    if success_rate >= 0.75:
        # Full conversion
        full_cleaned = series.dropna().astype(str).str.strip()
        full_cleaned = full_cleaned.apply(lambda s: f"-{s[1:-1]}" if isinstance(s, str) and s.startswith("(") and s.endswith(")") else s)
        full_cleaned = full_cleaned.apply(lambda s: CLEAN_NUMERIC_REGEX.sub("", s) if isinstance(s, str) else s)
        full_numeric = pd.to_numeric(full_cleaned, errors="coerce")
        # Reindex to original
        return True, full_numeric.reindex(series.index)

    return False, None


def try_parse_datetime_series(series: pd.Series) -> Tuple[bool, pd.Series | None]:
    """
    Attempt to parse a series as datetime across common formats.
    """
    if pd.api.types.is_datetime64_any_dtype(series):
        return True, series

    non_null = series.dropna()
    if non_null.empty:
        return False, None

    # Filter out pure numbers or single digits to avoid false-positive year/number parsing
    sample = non_null.head(100).astype(str).str.strip()
    if sample.str.isnumeric().all() and sample.str.len().max() <= 4:
        # Avoid treating IDs or year-only columns as full datetimes unless length is 4 and reasonable
        is_year = (sample.str.len() == 4).all() and sample.astype(int).between(1970, 2040).all()
        if not is_year:
            return False, None

    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            converted = pd.to_datetime(sample, errors="coerce")
        valid_count = converted.notna().sum()
        if valid_count / len(sample) >= 0.75:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                full_converted = pd.to_datetime(series, errors="coerce")
            # Verify year range is realistic (1950 to 2050)
            years = full_converted.dt.year.dropna()
            if not years.empty and (years.between(1950, 2050).mean() >= 0.8):
                return True, full_converted
    except Exception:
        pass

    return False, None


def infer_column_types(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    Examine each column of the dataframe and classify its semantic type:
    - 'datetime': Date, timestamp
    - 'numeric': Continuous/discrete numbers, currency, percentages
    - 'boolean': Binary indicators
    - 'categorical': Low-to-moderate cardinality discrete categories
    - 'id_or_text': High cardinality identifiers, names, free-form text
    """
    schema = {}
    total_rows = len(df)

    for col in df.columns:
        series = df[col]
        non_null_count = series.notna().sum()
        null_count = total_rows - non_null_count
        unique_count = series.nunique()

        # Default fallback
        col_info = {
            "name": col,
            "inferred_type": "text",
            "confidence": 0.5,
            "null_count": int(null_count),
            "unique_count": int(unique_count),
            "is_identifier": False,
        }

        if non_null_count == 0:
            col_info["inferred_type"] = "empty"
            col_info["confidence"] = 1.0
            schema[col] = col_info
            continue

        # 1. Check Datetime
        is_dt, parsed_dt = try_parse_datetime_series(series)
        if is_dt:
            col_info["inferred_type"] = "datetime"
            col_info["confidence"] = 0.95
            schema[col] = col_info
            continue

        # 2. Check Boolean
        if is_boolean_series(series):
            col_info["inferred_type"] = "boolean"
            col_info["confidence"] = 0.90
            schema[col] = col_info
            continue

        # 3. Check Numeric
        is_num, parsed_num = try_parse_numeric_series(series)
        if is_num:
            # Check if it might be an arbitrary row index / ID (e.g. perfectly sequential 1..N)
            is_seq_id = False
            if total_rows > 10 and unique_count == total_rows and str(col).lower() in ["id", "index", "row_id", "uid"]:
                is_seq_id = True

            if is_seq_id:
                col_info["inferred_type"] = "id_or_text"
                col_info["is_identifier"] = True
                col_info["confidence"] = 0.95
            else:
                col_info["inferred_type"] = "numeric"
                col_info["confidence"] = 0.95
            schema[col] = col_info
            continue

        # 4. Check Categorical vs High-Cardinality Text / ID
        cardinality_ratio = unique_count / non_null_count if non_null_count > 0 else 0

        # Identifier naming clues
        col_lower = str(col).lower()
        id_keywords = ["id", "uuid", "guid", "code", "ssn", "mrn", "key", "token", "hash"]
        has_id_keyword = any(k in col_lower.split("_") or col_lower.endswith(k) for k in id_keywords)

        if (cardinality_ratio > 0.85 and total_rows > 30) or (has_id_keyword and cardinality_ratio > 0.6):
            col_info["inferred_type"] = "id_or_text"
            col_info["is_identifier"] = True
            col_info["confidence"] = 0.85
        elif unique_count <= 50 or cardinality_ratio <= 0.25:
            col_info["inferred_type"] = "categorical"
            col_info["confidence"] = 0.90
        else:
            col_info["inferred_type"] = "id_or_text"
            col_info["confidence"] = 0.70

        schema[col] = col_info

    return schema
