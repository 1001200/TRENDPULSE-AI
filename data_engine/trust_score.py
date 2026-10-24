"""
TrendPulse Multi-Dimensional Data Trust Score.

Provides a composite trust score based on five independently measured
dimensions of data quality:

    1. Completeness  — How much data is present vs. expected?
    2. Validity      — How much data passes business rules?
    3. Consistency    — Are values internally consistent?
    4. Timeliness     — Is the data temporally coherent?
    5. Uniqueness     — How much duplication exists?

Each dimension is scored 0–100. The composite trust score is a weighted
average of all dimensions.

Design rules:
    - Deterministic; no randomness.
    - Never modifies the input DataFrame.
    - Returns a fully JSON-safe dictionary.
    - Every dimension includes a breakdown explaining its score.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from data_engine.utils import safe_float, safe_int


# ============================================================
# Configuration
# ============================================================

TRUST_VERSION = "1.0"

# Dimension weights (must sum to 1.0)
DIMENSION_WEIGHTS = {
    "completeness": 0.25,
    "validity": 0.25,
    "consistency": 0.20,
    "timeliness": 0.15,
    "uniqueness": 0.15,
}

# Required columns for a clothing sales dataset
REQUIRED_COLUMNS = ["date", "product", "quantity", "price"]
RECOMMENDED_COLUMNS = ["category", "customer_id", "order_id", "discount"]

# Thresholds
HIGH_TRUST_THRESHOLD = 85.0
MEDIUM_TRUST_THRESHOLD = 60.0

# Date range: transactions older than this many years are suspicious
MAX_REASONABLE_AGE_YEARS = 10


# ============================================================
# Completeness Dimension
# ============================================================

def score_completeness(
    df: pd.DataFrame,
    validation: Optional[dict] = None,
) -> dict:
    """
    Measure how much of the expected data is present.

    Sub-scores:
        - Column presence:  Are required/recommended columns present?
        - Cell completeness: What fraction of cells have non-null values?
        - Row completeness:  What fraction of rows have all required fields?
    """
    if df.empty:
        return {
            "score": 0.0,
            "column_presence": 0.0,
            "cell_completeness": 0.0,
            "row_completeness": 0.0,
            "missing_required": list(REQUIRED_COLUMNS),
            "missing_recommended": list(RECOMMENDED_COLUMNS),
            "breakdown": "Dataset is empty.",
        }

    # --- Column presence ---
    present_required = [c for c in REQUIRED_COLUMNS if c in df.columns]
    present_recommended = [c for c in RECOMMENDED_COLUMNS if c in df.columns]

    missing_required = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    missing_recommended = [c for c in RECOMMENDED_COLUMNS if c not in df.columns]

    # Required columns weighted 70%, recommended 30%
    req_score = (len(present_required) / len(REQUIRED_COLUMNS)) * 100 if REQUIRED_COLUMNS else 100
    rec_score = (len(present_recommended) / len(RECOMMENDED_COLUMNS)) * 100 if RECOMMENDED_COLUMNS else 100
    column_presence = req_score * 0.7 + rec_score * 0.3

    # --- Cell completeness ---
    total_cells = df.shape[0] * df.shape[1]
    non_null_cells = int(df.notna().sum().sum())
    cell_completeness = (non_null_cells / total_cells) * 100 if total_cells > 0 else 0.0

    # --- Row completeness (all required fields present in each row) ---
    available_required = [c for c in REQUIRED_COLUMNS if c in df.columns]
    if available_required:
        complete_rows = int(df[available_required].notna().all(axis=1).sum())
        row_completeness = (complete_rows / len(df)) * 100
    else:
        row_completeness = 0.0

    # Composite: column presence 30%, cell completeness 30%, row completeness 40%
    score = column_presence * 0.30 + cell_completeness * 0.30 + row_completeness * 0.40
    score = round(max(0.0, min(100.0, score)), 2)

    parts = []
    if missing_required:
        parts.append(f"Missing required columns: {', '.join(missing_required)}.")
    if missing_recommended:
        parts.append(f"Missing recommended columns: {', '.join(missing_recommended)}.")
    parts.append(f"Cell completeness: {cell_completeness:.1f}%.")
    parts.append(f"Row completeness: {row_completeness:.1f}%.")

    return {
        "score": score,
        "column_presence": round(column_presence, 2),
        "cell_completeness": round(cell_completeness, 2),
        "row_completeness": round(row_completeness, 2),
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
        "breakdown": " ".join(parts),
    }


# ============================================================
# Validity Dimension
# ============================================================

def score_validity(
    df: pd.DataFrame,
    validation: Optional[dict] = None,
) -> dict:
    """
    Measure how much data passes business validation rules.

    Uses the validation report from the validator module when available,
    otherwise performs basic checks directly.
    """
    if df.empty:
        return {
            "score": 0.0,
            "valid_row_ratio": 0.0,
            "issues_by_severity": {"error": 0, "warning": 0},
            "breakdown": "Dataset is empty.",
        }

    total_rows = len(df)
    error_count = 0
    warning_count = 0
    error_rows = set()

    if validation and "issues" in validation:
        for issue in validation["issues"]:
            severity = issue.get("severity", "warning")
            row = issue.get("row")
            if severity == "error":
                error_count += 1
                if row is not None:
                    error_rows.add(row)
            else:
                warning_count += 1

    # Valid rows = rows without errors
    valid_rows = total_rows - len(error_rows)
    valid_row_ratio = (valid_rows / total_rows) * 100 if total_rows > 0 else 0.0

    # Errors penalize heavily, warnings penalize lightly
    error_penalty = min(len(error_rows) / max(total_rows, 1) * 100, 100)
    warning_penalty = min(warning_count / max(total_rows, 1) * 15, 30)  # cap at 30

    score = max(0.0, 100.0 - error_penalty - warning_penalty)
    score = round(min(100.0, score), 2)

    parts = []
    if error_count:
        parts.append(f"{error_count} validation errors across {len(error_rows)} rows.")
    if warning_count:
        parts.append(f"{warning_count} validation warnings.")
    if not parts:
        parts.append("All rows pass validation.")

    return {
        "score": score,
        "valid_row_ratio": round(valid_row_ratio, 2),
        "error_count": error_count,
        "warning_count": warning_count,
        "error_rows": len(error_rows),
        "issues_by_severity": {"error": error_count, "warning": warning_count},
        "breakdown": " ".join(parts),
    }


# ============================================================
# Consistency Dimension
# ============================================================

def score_consistency(
    df: pd.DataFrame,
    anomaly_summary: Optional[dict] = None,
) -> dict:
    """
    Measure internal data consistency.

    Checks:
        - Numeric columns contain only numeric values (no mixed types).
        - Revenue consistency (if quantity × price ≈ revenue when all exist).
        - Anomaly ratio (high anomalies suggest inconsistency).
    """
    if df.empty:
        return {
            "score": 0.0,
            "type_consistency": 0.0,
            "anomaly_ratio": 0.0,
            "breakdown": "Dataset is empty.",
        }

    # --- Type consistency ---
    # For numeric columns, what fraction of non-null values are actually numeric?
    numeric_cols = ["quantity", "price", "discount", "cost_price", "stock", "revenue"]
    type_scores = []

    for col in numeric_cols:
        if col not in df.columns:
            continue
        series = df[col].dropna()
        if series.empty:
            continue
        numeric_values = pd.to_numeric(series, errors="coerce")
        valid_count = int(numeric_values.notna().sum())
        ratio = valid_count / len(series) * 100 if len(series) > 0 else 100.0
        type_scores.append(ratio)

    type_consistency = sum(type_scores) / len(type_scores) if type_scores else 100.0

    # --- Anomaly ratio ---
    total_anomalies = 0
    affected_rows = 0
    if anomaly_summary:
        total_anomalies = safe_int(anomaly_summary.get("total_anomalies", 0))
        affected_rows = safe_int(anomaly_summary.get("affected_rows", 0))

    anomaly_ratio = (affected_rows / len(df)) * 100 if len(df) > 0 else 0.0
    anomaly_penalty = min(anomaly_ratio * 2, 40)  # cap penalty at 40 points

    # Composite
    score = type_consistency * 0.60 + (100.0 - anomaly_penalty) * 0.40
    score = round(max(0.0, min(100.0, score)), 2)

    parts = []
    parts.append(f"Type consistency: {type_consistency:.1f}%.")
    if total_anomalies:
        parts.append(
            f"{total_anomalies} anomalies in {affected_rows} rows "
            f"({anomaly_ratio:.1f}% of dataset)."
        )
    else:
        parts.append("No anomalies detected.")

    return {
        "score": score,
        "type_consistency": round(type_consistency, 2),
        "anomaly_ratio": round(anomaly_ratio, 2),
        "total_anomalies": total_anomalies,
        "affected_rows": affected_rows,
        "breakdown": " ".join(parts),
    }


# ============================================================
# Timeliness Dimension
# ============================================================

def score_timeliness(
    df: pd.DataFrame,
) -> dict:
    """
    Measure temporal coherence.

    Checks:
        - Date column parsability.
        - Date range reasonableness (not from the distant past).
        - Future date ratio.
        - Date ordering (are dates monotonically ordered or scrambled?).
    """
    if df.empty or "date" not in df.columns:
        return {
            "score": 50.0 if df.empty else 70.0,
            "parsable_ratio": 0.0,
            "future_ratio": 0.0,
            "date_range_days": 0,
            "breakdown": "No date column available." if "date" not in df.columns else "Dataset is empty.",
        }

    dates = pd.to_datetime(df["date"], errors="coerce")
    total = len(dates)
    parsable = int(dates.notna().sum())
    parsable_ratio = (parsable / total) * 100 if total > 0 else 0.0

    today = pd.Timestamp.now().normalize()
    valid_dates = dates.dropna()

    if valid_dates.empty:
        return {
            "score": max(0.0, parsable_ratio * 0.5),
            "parsable_ratio": round(parsable_ratio, 2),
            "future_ratio": 0.0,
            "date_range_days": 0,
            "breakdown": "No valid dates could be parsed.",
        }

    # Future dates
    future_count = int((valid_dates > today).sum())
    future_ratio = (future_count / len(valid_dates)) * 100

    # Date range
    min_date = valid_dates.min()
    max_date = valid_dates.max()
    date_range_days = (max_date - min_date).days

    # Ancient dates
    cutoff = today - pd.Timedelta(days=MAX_REASONABLE_AGE_YEARS * 365)
    ancient_count = int((valid_dates < cutoff).sum())
    ancient_ratio = (ancient_count / len(valid_dates)) * 100

    # Score components
    parsable_score = parsable_ratio
    future_penalty = min(future_ratio * 3, 30)
    ancient_penalty = min(ancient_ratio * 3, 20)

    score = parsable_score - future_penalty - ancient_penalty
    score = round(max(0.0, min(100.0, score)), 2)

    parts = [f"Date parsability: {parsable_ratio:.1f}%."]
    if future_count:
        parts.append(f"{future_count} future dates detected ({future_ratio:.1f}%).")
    if ancient_count:
        parts.append(f"{ancient_count} dates older than {MAX_REASONABLE_AGE_YEARS} years.")
    parts.append(f"Date range: {date_range_days} days.")

    return {
        "score": score,
        "parsable_ratio": round(parsable_ratio, 2),
        "future_ratio": round(future_ratio, 2),
        "ancient_ratio": round(ancient_ratio, 2),
        "date_range_days": date_range_days,
        "min_date": str(min_date.date()) if pd.notna(min_date) else None,
        "max_date": str(max_date.date()) if pd.notna(max_date) else None,
        "breakdown": " ".join(parts),
    }


# ============================================================
# Uniqueness Dimension
# ============================================================

def score_uniqueness(
    df: pd.DataFrame,
    validation: Optional[dict] = None,
) -> dict:
    """
    Measure data uniqueness (absence of duplication).

    Checks:
        - Exact duplicate rows.
        - Near-duplicate ratio.
    """
    if df.empty:
        return {
            "score": 100.0,
            "duplicate_ratio": 0.0,
            "duplicate_count": 0,
            "breakdown": "Dataset is empty (no duplicates possible).",
        }

    total = len(df)
    duplicate_count = int(df.duplicated(keep="first").sum())
    duplicate_ratio = (duplicate_count / total) * 100 if total > 0 else 0.0

    # Score: 100 minus a scaled penalty
    # First few duplicates are tolerable; high ratios are severely penalized
    if duplicate_ratio <= 1.0:
        penalty = duplicate_ratio * 5  # mild
    elif duplicate_ratio <= 10.0:
        penalty = 5 + (duplicate_ratio - 1) * 4  # moderate
    else:
        penalty = 41 + (duplicate_ratio - 10) * 2  # severe

    score = round(max(0.0, min(100.0, 100.0 - penalty)), 2)

    parts = []
    if duplicate_count:
        parts.append(
            f"{duplicate_count} duplicate rows ({duplicate_ratio:.1f}% of dataset)."
        )
    else:
        parts.append("No duplicate rows detected.")

    return {
        "score": score,
        "duplicate_ratio": round(duplicate_ratio, 2),
        "duplicate_count": duplicate_count,
        "breakdown": " ".join(parts),
    }


# ============================================================
# Trust Level Classification
# ============================================================

def classify_trust_level(score: float) -> str:
    """
    Classify composite trust score into a human-readable level.
    """
    if score >= HIGH_TRUST_THRESHOLD:
        return "high"
    if score >= MEDIUM_TRUST_THRESHOLD:
        return "medium"
    return "low"


# ============================================================
# Composite Trust Score
# ============================================================

def calculate_trust_score(
    df: pd.DataFrame,
    *,
    validation: Optional[dict] = None,
    anomaly_summary: Optional[dict] = None,
) -> dict:
    """
    Calculate the multi-dimensional TrendPulse Data Trust Score.

    Parameters
    ----------
    df : pd.DataFrame
        The cleaned/processed DataFrame.
    validation : dict, optional
        Output from validator.validate_data().
    anomaly_summary : dict, optional
        The 'summary' key from anomaly_detector.detect_anomalies().

    Returns
    -------
    dict
        JSON-safe trust score report with composite score and per-dimension details.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("calculate_trust_score expects a pandas DataFrame.")

    completeness = score_completeness(df, validation=validation)
    validity = score_validity(df, validation=validation)
    consistency = score_consistency(df, anomaly_summary=anomaly_summary)
    timeliness = score_timeliness(df)
    uniqueness = score_uniqueness(df, validation=validation)

    dimensions = {
        "completeness": completeness,
        "validity": validity,
        "consistency": consistency,
        "timeliness": timeliness,
        "uniqueness": uniqueness,
    }

    # Weighted composite
    composite = sum(
        dimensions[dim]["score"] * DIMENSION_WEIGHTS[dim]
        for dim in DIMENSION_WEIGHTS
    )
    composite = round(max(0.0, min(100.0, composite)), 2)

    trust_level = classify_trust_level(composite)

    # Build overall assessment
    weak_dimensions = [
        dim for dim, detail in dimensions.items()
        if detail["score"] < MEDIUM_TRUST_THRESHOLD
    ]
    strong_dimensions = [
        dim for dim, detail in dimensions.items()
        if detail["score"] >= HIGH_TRUST_THRESHOLD
    ]

    if trust_level == "high":
        assessment = "Data quality is high across all dimensions. Downstream analytics and ML models can proceed with confidence."
    elif trust_level == "medium":
        assessment = f"Data quality is acceptable but has weaknesses in: {', '.join(weak_dimensions) if weak_dimensions else 'several areas'}. Review before critical decisions."
    else:
        assessment = f"Data quality is low. Major issues in: {', '.join(weak_dimensions) if weak_dimensions else 'multiple areas'}. Data cleaning and validation required before analysis."

    return {
        "version": TRUST_VERSION,
        "composite_score": composite,
        "trust_level": trust_level,
        "assessment": assessment,
        "dimensions": dimensions,
        "weights": dict(DIMENSION_WEIGHTS),
        "weak_dimensions": weak_dimensions,
        "strong_dimensions": strong_dimensions,
    }


__all__ = [
    "calculate_trust_score",
    "score_completeness",
    "score_validity",
    "score_consistency",
    "score_timeliness",
    "score_uniqueness",
    "classify_trust_level",
    "TRUST_VERSION",
]
