"""
TrendPulse Advanced Anomaly Detection Engine V4.

Design:
- Never mutates caller data.
- Uses robust, deterministic statistics.
- Detects cell-level anomalies and aggregates them to rows.
- Separates "statistical unusualness" from "business severity".
- Preserves original DataFrame indices.
- Provides compatibility helpers used by older TrendPulse code.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Iterable, Optional

import numpy as np
import pandas as pd

from data_engine.utils import safe_float, safe_int
from data_engine.utils import clean_number as _clean_number

ENGINE_VERSION = "4.0"

DEFAULT_Z_THRESHOLD = 3.0
DEFAULT_MODIFIED_Z_THRESHOLD = 3.5
DEFAULT_IQR_MULTIPLIER = 1.5
EXTREME_IQR_MULTIPLIER = 3.0

MIN_VALUES_FOR_DETECTION = 5
MIN_UNIQUE_VALUES_FOR_DETECTION = 3
MAD_EPSILON = 1e-12
STD_EPSILON = 1e-12

# Business identifiers should not normally be treated as continuous measures.
DEFAULT_EXCLUDED_COLUMNS = {
    "id", "order_id", "customer_id", "product_id", "sku",
    "phone", "zip", "postal_code"
}


def clean_number(value):
    """Anomaly detector uses 6 decimal places for statistical precision."""
    return _clean_number(value, decimals=6)


def normalize_method_name(method) -> str:
    return "" if method is None else str(method).strip().lower()


def empty_summary() -> dict:
    return {
        "total_anomalies": 0,
        "affected_rows": 0,
        "affected_columns": [],
        "by_column": {},
        "by_method": {},
        "by_severity": {"critical": 0, "warning": 0},
        "row_scores": {},
        "method_agreement": {},
    }


def empty_result() -> dict:
    return {
        "version": ENGINE_VERSION,
        "anomalies": [],
        "summary": empty_summary(),
    }


def get_numeric_columns(
    df: pd.DataFrame,
    include_columns: Optional[Iterable[str]] = None,
    exclude_columns: Optional[Iterable[str]] = None,
) -> list[str]:
    if not isinstance(df, pd.DataFrame):
        raise TypeError("get_numeric_columns expects a pandas DataFrame.")

    excludes = set(DEFAULT_EXCLUDED_COLUMNS)
    if exclude_columns:
        excludes.update(exclude_columns)

    if include_columns is not None:
        candidates = [c for c in include_columns if c in df.columns]
    else:
        candidates = list(df.columns)

    result = []
    for column in candidates:
        if column in excludes:
            continue
        series = pd.to_numeric(df[column], errors="coerce")
        # Only accept columns with actual numeric evidence.
        if int(series.notna().sum()) >= MIN_VALUES_FOR_DETECTION:
            result.append(column)

    return sorted(result, key=str)


def prepare_numeric_series(series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def is_detectable_series(
    series: pd.Series,
    min_values: int = MIN_VALUES_FOR_DETECTION,
    min_unique: int = MIN_UNIQUE_VALUES_FOR_DETECTION,
) -> bool:
    values = prepare_numeric_series(series).dropna()
    return len(values) >= min_values and values.nunique() >= min_unique


def calculate_iqr_bounds(values, multiplier=DEFAULT_IQR_MULTIPLIER):
    values = pd.Series(values, dtype="float64").dropna()
    if values.empty:
        return None, None
    q1 = float(values.quantile(0.25))
    q3 = float(values.quantile(0.75))
    iqr = q3 - q1
    if abs(iqr) <= MAD_EPSILON:
        return q1, q3
    return q1 - multiplier * iqr, q3 + multiplier * iqr


def calculate_zscore_parameters(values):
    values = pd.Series(values, dtype="float64").dropna()
    if values.empty:
        return None, None
    return float(values.mean()), float(values.std(ddof=0))


def calculate_mad_parameters(values):
    values = pd.Series(values, dtype="float64").dropna()
    if values.empty:
        return None, None
    median = float(values.median())
    mad = float(np.median(np.abs(values.to_numpy() - median)))
    return median, mad


def detect_iqr(values, multiplier=DEFAULT_IQR_MULTIPLIER):
    values = prepare_numeric_series(values)
    clean = values.dropna()
    if not is_detectable_series(clean):
        return {}

    q1 = float(clean.quantile(0.25))
    q3 = float(clean.quantile(0.75))
    iqr = q3 - q1
    if abs(iqr) <= MAD_EPSILON:
        return {}

    lower = q1 - multiplier * iqr
    upper = q3 + multiplier * iqr
    result = {}

    for idx, value in clean.items():
        value = float(value)
        if value < lower or value > upper:
            distance = (lower - value) if value < lower else (value - upper)
            score = distance / max(iqr, MAD_EPSILON)
            result[idx] = {
                "score": float(score),
                "direction": "low" if value < lower else "high",
                "lower_bound": lower,
                "upper_bound": upper,
            }
    return result


def detect_z_score(values, threshold=DEFAULT_Z_THRESHOLD):
    values = prepare_numeric_series(values)
    clean = values.dropna()
    if not is_detectable_series(clean):
        return {}

    mean = float(clean.mean())
    std = float(clean.std(ddof=0))
    if std <= STD_EPSILON:
        return {}

    result = {}
    for idx, value in clean.items():
        z = (float(value) - mean) / std
        if abs(z) >= threshold:
            result[idx] = {
                "score": abs(float(z)),
                "direction": "low" if z < 0 else "high",
                "mean": mean,
                "std": std,
            }
    return result


def detect_modified_z(values, threshold=DEFAULT_MODIFIED_Z_THRESHOLD):
    values = prepare_numeric_series(values)
    clean = values.dropna()
    if not is_detectable_series(clean):
        return {}

    median = float(clean.median())
    mad = float(np.median(np.abs(clean.to_numpy() - median)))
    if mad <= MAD_EPSILON:
        return {}

    # 0.67448975 converts MAD to the normal-distribution scale.
    scores = 0.67448975 * (clean - median) / mad
    result = {}
    for idx, score in scores.items():
        score = float(score)
        if abs(score) >= threshold:
            result[idx] = {
                "score": abs(score),
                "direction": "low" if score < 0 else "high",
                "median": median,
                "mad": mad,
            }
    return result


def determine_severity(
    method_count: int,
    score: float,
    value,
    lower_bound=None,
    upper_bound=None,
) -> str:
    # Agreement between independent methods is stronger evidence than
    # a single extreme statistic.
    if method_count >= 2:
        return "critical"
    if score >= 8:
        return "critical"
    if lower_bound is not None and upper_bound is not None:
        try:
            if value < lower_bound * 0.25 or value > upper_bound * 4:
                return "critical"
        except (TypeError, ZeroDivisionError):
            pass
    return "warning"


def merge_column_detections(
    column: str,
    detections: dict[str, dict],
    original_series: pd.Series,
) -> list[dict]:
    by_row = defaultdict(list)

    for method, records in detections.items():
        for row, info in records.items():
            by_row[row].append((method, info))

    output = []
    for row in by_row:
        methods = sorted(
            {normalize_method_name(m) for m, _ in by_row[row]}
        )
        infos = [info for _, info in by_row[row]]
        scores = [safe_float(info.get("score")) for info in infos]
        best = max(infos, key=lambda x: safe_float(x.get("score")))
        value = original_series.loc[row]

        severity = determine_severity(
            len(methods),
            max(scores) if scores else 0,
            value,
            best.get("lower_bound"),
            best.get("upper_bound"),
        )

        output.append({
            "row": row,
            "column": str(column),
            "value": clean_number(value) if isinstance(
                value, (int, float, np.integer, np.floating)
            ) else value,
            "method": methods[0] if len(methods) == 1 else "ensemble",
            "methods": methods,
            "method_count": len(methods),
            "score": clean_number(max(scores) if scores else 0),
            "severity": severity,
            "direction": best.get("direction", "unknown"),
            "reason": (
                f"Detected by {', '.join(methods)}."
                if len(methods) > 1
                else f"Detected by {methods[0]}."
            ),
        })

    return output


def detect_column_anomalies(
    df: pd.DataFrame,
    column: str,
    z_threshold=DEFAULT_Z_THRESHOLD,
    modified_z_threshold=DEFAULT_MODIFIED_Z_THRESHOLD,
    iqr_multiplier=DEFAULT_IQR_MULTIPLIER,
    use_z_score=True,
    use_iqr=True,
    use_modified_z=True,
) -> list[dict]:
    series = prepare_numeric_series(df[column])
    if not is_detectable_series(series):
        return []

    detections = {}
    if use_iqr:
        detections["iqr"] = detect_iqr(series, iqr_multiplier)
    if use_z_score:
        detections["z_score"] = detect_z_score(series, z_threshold)
    if use_modified_z:
        detections["modified_z"] = detect_modified_z(
            series, modified_z_threshold
        )

    return merge_column_detections(column, detections, df[column])


def _sort_value(value):
    if isinstance(value, (int, float, np.integer, np.floating)):
        return (0, float(value))
    return (1, str(value))


def anomaly_sort_key(anomaly):
    severity_rank = {"critical": 0, "warning": 1}
    return (
        severity_rank.get(anomaly.get("severity"), 9),
        str(anomaly.get("column", "")),
        _sort_value(anomaly.get("row")),
    )


def deduplicate_anomalies(anomalies: list[dict]) -> list[dict]:
    # One record per row/column. Preserve all agreeing methods.
    merged = {}
    for anomaly in anomalies:
        key = (anomaly.get("row"), anomaly.get("column"))
        current = merged.get(key)
        if current is None:
            merged[key] = dict(anomaly)
            continue

        methods = set(current.get("methods", [current.get("method")]))
        methods.update(anomaly.get("methods", [anomaly.get("method")]))
        current["methods"] = sorted(m for m in methods if m)
        current["method_count"] = len(current["methods"])
        current["method"] = (
            current["methods"][0]
            if len(current["methods"]) == 1
            else "ensemble"
        )
        current["score"] = clean_number(
            max(safe_float(current.get("score")),
                safe_float(anomaly.get("score")))
        )
        if current["method_count"] >= 2:
            current["severity"] = "critical"
        elif anomaly.get("severity") == "critical":
            current["severity"] = "critical"
        if current.get("reason"):
            current["reason"] = (
                f"Detected by {', '.join(current['methods'])}."
            )

    return list(merged.values())


def build_anomaly_summary(anomalies: list[dict]) -> dict:
    by_column = Counter()
    by_method = Counter()
    by_severity = Counter({"critical": 0, "warning": 0})
    affected_rows = set()
    row_scores = defaultdict(float)
    method_agreement = Counter()

    for anomaly in anomalies:
        column = str(anomaly.get("column"))
        by_column[column] += 1
        affected_rows.add(anomaly.get("row"))

        methods = anomaly.get("methods") or [anomaly.get("method")]
        for method in methods:
            if method:
                by_method[str(method)] += 1

        severity = anomaly.get("severity")
        if severity in by_severity:
            by_severity[severity] += 1

        row_scores[str(anomaly.get("row"))] += safe_float(
            anomaly.get("score")
        )
        method_agreement[str(len(methods))] += 1

    return {
        "total_anomalies": len(anomalies),
        "affected_rows": len(affected_rows),
        "affected_columns": sorted(by_column),
        "by_column": dict(sorted(by_column.items())),
        "by_method": dict(sorted(by_method.items())),
        "by_severity": dict(sorted(by_severity.items())),
        "row_scores": dict(sorted(row_scores.items())),
        "method_agreement": dict(sorted(method_agreement.items())),
    }


class AnomalyDetectionResult(dict):
    """Dict result that also supports the legacy `(anomalies, summary)` unpacking."""

    def __iter__(self):
        yield self.get("anomalies", [])
        yield self.get("summary", empty_summary())


def detect_anomalies(
    df: pd.DataFrame,
    columns=None,
    exclude_columns=None,
    z_threshold=DEFAULT_Z_THRESHOLD,
    modified_z_threshold=DEFAULT_MODIFIED_Z_THRESHOLD,
    iqr_multiplier=DEFAULT_IQR_MULTIPLIER,
    use_z_score=True,
    use_iqr=True,
    use_modified_z=True,
):
    if not isinstance(df, pd.DataFrame):
        raise TypeError("detect_anomalies expects a pandas DataFrame.")
    if df.empty:
        return AnomalyDetectionResult(empty_result())
    for name, value in {
        "z_threshold": z_threshold,
        "modified_z_threshold": modified_z_threshold,
        "iqr_multiplier": iqr_multiplier,
    }.items():
        if value is not None and value <= 0:
            raise ValueError(f"{name} must be greater than zero.")

    numeric_columns = get_numeric_columns(
        df, include_columns=columns, exclude_columns=exclude_columns
    )

    anomalies = []
    for column in numeric_columns:
        anomalies.extend(
            detect_column_anomalies(
                df, column,
                z_threshold=z_threshold,
                modified_z_threshold=modified_z_threshold,
                iqr_multiplier=iqr_multiplier,
                use_z_score=use_z_score,
                use_iqr=use_iqr,
                use_modified_z=use_modified_z,
            )
        )

    anomalies = deduplicate_anomalies(anomalies)
    anomalies.sort(key=anomaly_sort_key)

    return AnomalyDetectionResult({
        "version": ENGINE_VERSION,
        "anomalies": anomalies,
        "summary": build_anomaly_summary(anomalies),
    })


def analyze_anomalies(df, *args, **kwargs):
    """Compatibility alias. Returns a V4 result supporting tuple unpacking."""
    return detect_anomalies(df, *args, **kwargs)


def get_anomaly_summary(df, *args, **kwargs):
    return detect_anomalies(df, *args, **kwargs)["summary"]


def get_anomalies(df, *args, **kwargs):
    return detect_anomalies(df, *args, **kwargs)["anomalies"]


def get_anomaly_row_indices(anomalies):
    indices = {
        a.get("row")
        for a in (anomalies or [])
        if isinstance(a, dict) and "row" in a
    }
    try:
        return sorted(indices)
    except TypeError:
        return sorted(indices, key=str)


def get_anomaly_columns(anomalies):
    return sorted({
        str(a.get("column"))
        for a in (anomalies or [])
        if isinstance(a, dict) and a.get("column") is not None
    })


def get_critical_anomalies(anomalies):
    return [
        a for a in (anomalies or [])
        if isinstance(a, dict) and a.get("severity") == "critical"
    ]


def get_warning_anomalies(anomalies):
    return [
        a for a in (anomalies or [])
        if isinstance(a, dict) and a.get("severity") == "warning"
    ]


def exclude_anomaly_rows(df, anomalies):
    if not isinstance(df, pd.DataFrame):
        raise TypeError("exclude_anomaly_rows expects a pandas DataFrame.")
    return df.drop(
        labels=[i for i in get_anomaly_row_indices(anomalies) if i in df.index],
        errors="ignore",
    ).copy()


def detect_and_exclude(df, columns=None, exclude_columns=None, **kwargs):
    result = detect_anomalies(
        df, columns=columns, exclude_columns=exclude_columns, **kwargs
    )
    return result, exclude_anomaly_rows(df, result["anomalies"])


def run_anomaly_detection(df, columns=None, exclude_columns=None, **kwargs):
    return detect_anomalies(
        df, columns=columns, exclude_columns=exclude_columns, **kwargs
    )


def find_anomalies(df, columns=None, exclude_columns=None, **kwargs):
    return get_anomalies(
        df, columns=columns, exclude_columns=exclude_columns, **kwargs
    )
