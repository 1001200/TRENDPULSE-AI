import pandas as pd
import numpy as np

from data_engine.utils import safe_float, safe_int, clean_number, index_to_output_value


# ============================================================
# TRENDPULSE INSIGHT ENGINE V3
# ============================================================
"""
Evidence-aware Business Intelligence layer for TrendPulse.

V3 principles
--------------
1. Never modify the input DataFrame.
2. Preserve observed business metrics.
3. Detect the business impact of anomalies.
4. Produce an adjusted baseline excluding anomalous rows.
5. Compare observed vs adjusted trends.
6. Never treat anomaly-driven growth as reliable growth.
7. Consume Profiler V3 information.
8. Produce deterministic, UI-friendly business intelligence.
9. Important conclusions carry a confidence level.
10. Preserve backward-compatible APIs from V1/V2.

Expected columns when available
-------------------------------
product
category
quantity
price
date

Optional
--------
discount
revenue

Important implementation detail
--------------------------------
Anomalies are detected against original row indices, while time
analysis aggregates rows into daily values. Therefore anomaly
indices are explicitly mapped to anomaly dates before calculating
daily adjusted trends.
"""


# ============================================================
# Configuration
# ============================================================

ENGINE_VERSION = "3.0"

DEFAULT_TOP_N = 5

HIGH_CONCENTRATION_THRESHOLD = 50.0
LOW_CONCENTRATION_THRESHOLD = 20.0

STRONG_CORRELATION_THRESHOLD = 0.70
VERY_STRONG_CORRELATION_THRESHOLD = 0.90

MIN_TREND_POINTS = 3
TREND_CHANGE_THRESHOLD = 5.0

HIGH_ANOMALY_REVENUE_SHARE = 50.0
VERY_HIGH_ANOMALY_REVENUE_SHARE = 80.0

HIGH_ANOMALY_QUANTITY_SHARE = 50.0

HIGH_MISSING_PERCENT = 20.0




def percentage_change(first, last):
    """
    Calculate percentage change between two values.
    """
    first = safe_float(first)
    last = safe_float(last)

    if first == 0:

        if last > 0:
            return 100.0

        if last < 0:
            return -100.0

        return 0.0

    return (
        (last - first)
        / abs(first)
    ) * 100.0


def normalize_indices(indices):
    """
    Normalize anomaly indices into a set while preserving
    arbitrary pandas index types.
    """
    if indices is None:
        return set()

    if isinstance(indices, (str, bytes)):
        return {indices}

    try:
        return set(indices)

    except TypeError:
        return {indices}




def empty_result():
    """
    Return a safe empty V3 result.
    """
    return {
        "version": ENGINE_VERSION,
        "executive_summary": {},
        "summary": {},
        "insights": [],
        "opportunities": [],
        "risks": [],
        "product_analysis": {},
        "category_analysis": {},
        "time_analysis": {},
        "concentration": {},
        "anomaly_analysis": {},
        "profiler_analysis": {}
    }


# ============================================================
# Revenue Preparation
# ============================================================

def prepare_revenue_data(df):
    """
    Create a temporary analysis DataFrame.

    Revenue is calculated as:
        quantity * price

    When both quantity and price are available, that calculation
    is used deterministically.

    The original DataFrame is never modified.
    """
    data = df.copy()

    if (
        "quantity" in data.columns
        and "price" in data.columns
    ):
        data["quantity"] = pd.to_numeric(
            data["quantity"],
            errors="coerce"
        )

        data["price"] = pd.to_numeric(
            data["price"],
            errors="coerce"
        )

        data["revenue"] = (
            data["quantity"]
            * data["price"]
        )

    elif "revenue" in data.columns:
        data["revenue"] = pd.to_numeric(
            data["revenue"],
            errors="coerce"
        )

    return data


# ============================================================
# Overall Summary
# ============================================================

def calculate_summary(df):
    """
    Calculate observed high-level business metrics.
    """
    summary = {
        "rows": len(df),
        "total_quantity": 0,
        "total_revenue": 0,
        "average_price": 0,
        "average_quantity": 0,
        "average_order_value": 0
    }

    if "quantity" in df.columns:

        quantity = pd.to_numeric(
            df["quantity"],
            errors="coerce"
        )

        summary["total_quantity"] = clean_number(
            quantity.sum()
        )

        summary["average_quantity"] = clean_number(
            quantity.mean()
        )

    if "price" in df.columns:

        price = pd.to_numeric(
            df["price"],
            errors="coerce"
        )

        summary["average_price"] = clean_number(
            price.mean()
        )

    if "revenue" in df.columns:

        revenue = pd.to_numeric(
            df["revenue"],
            errors="coerce"
        )

        summary["total_revenue"] = clean_number(
            revenue.sum()
        )

        valid_revenue = revenue.dropna()

        if not valid_revenue.empty:
            summary["average_order_value"] = clean_number(
                valid_revenue.mean()
            )

    return summary


# ============================================================
# Product Analysis
# ============================================================

def analyze_products(
    df,
    top_n=DEFAULT_TOP_N
):
    """
    Analyze product-level quantity and revenue.
    """
    if "product" not in df.columns:
        return {}

    aggregations = {}

    if "quantity" in df.columns:
        aggregations["quantity"] = "sum"

    if "revenue" in df.columns:
        aggregations["revenue"] = "sum"

    if not aggregations:
        return {}

    data = df[
        ["product"] + list(aggregations.keys())
    ].copy()

    data["product"] = (
        data["product"]
        .astype(str)
        .str.strip()
    )

    grouped = (
        data
        .groupby(
            "product",
            dropna=False
        )
        .agg(aggregations)
    )

    result = {
        "products": [],
        "top_by_quantity": [],
        "top_by_revenue": [],
        "bottom_by_quantity": [],
        "bottom_by_revenue": []
    }

    # --------------------------------------------------------
    # Complete Product List
    # --------------------------------------------------------

    for product, row in grouped.iterrows():

        item = {
            "product": product
        }

        if "quantity" in grouped.columns:
            item["quantity"] = clean_number(
                row["quantity"]
            )

        if "revenue" in grouped.columns:
            item["revenue"] = clean_number(
                row["revenue"]
            )

        result["products"].append(item)

    # --------------------------------------------------------
    # Quantity
    # --------------------------------------------------------

    if "quantity" in grouped.columns:

        quantity_sorted = grouped.sort_values(
            "quantity",
            ascending=False,
            kind="stable"
        )

        for product, row in quantity_sorted.head(
            top_n
        ).iterrows():

            result["top_by_quantity"].append({
                "product": product,
                "quantity": clean_number(
                    row["quantity"]
                )
            })

        quantity_bottom = grouped.sort_values(
            "quantity",
            ascending=True,
            kind="stable"
        )

        for product, row in quantity_bottom.head(
            top_n
        ).iterrows():

            result["bottom_by_quantity"].append({
                "product": product,
                "quantity": clean_number(
                    row["quantity"]
                )
            })

    # --------------------------------------------------------
    # Revenue
    # --------------------------------------------------------

    if "revenue" in grouped.columns:

        revenue_sorted = grouped.sort_values(
            "revenue",
            ascending=False,
            kind="stable"
        )

        for product, row in revenue_sorted.head(
            top_n
        ).iterrows():

            result["top_by_revenue"].append({
                "product": product,
                "revenue": clean_number(
                    row["revenue"]
                )
            })

        revenue_bottom = grouped.sort_values(
            "revenue",
            ascending=True,
            kind="stable"
        )

        for product, row in revenue_bottom.head(
            top_n
        ).iterrows():

            result["bottom_by_revenue"].append({
                "product": product,
                "revenue": clean_number(
                    row["revenue"]
                )
            })

    return result


# ============================================================
# Category Analysis
# ============================================================

def analyze_categories(df):
    """
    Analyze category-level quantity and revenue.
    """
    if "category" not in df.columns:
        return {}

    aggregations = {}

    if "quantity" in df.columns:
        aggregations["quantity"] = "sum"

    if "revenue" in df.columns:
        aggregations["revenue"] = "sum"

    if not aggregations:
        return {}

    data = df.copy()

    data["category"] = (
        data["category"]
        .astype(str)
        .str.strip()
    )

    grouped = (
        data
        .groupby(
            "category",
            dropna=False
        )
        .agg(aggregations)
    )

    sort_column = list(
        aggregations.keys()
    )[0]

    grouped = grouped.sort_values(
        sort_column,
        ascending=False,
        kind="stable"
    )

    result = {
        "categories": [],
        "top_category": None
    }

    for category, row in grouped.iterrows():

        item = {
            "category": category
        }

        if "quantity" in grouped.columns:
            item["quantity"] = clean_number(
                row["quantity"]
            )

        if "revenue" in grouped.columns:
            item["revenue"] = clean_number(
                row["revenue"]
            )

        result["categories"].append(item)

    if result["categories"]:
        result["top_category"] = (
            result["categories"][0]
        )

    return result


# ============================================================
# Trend Calculation
# ============================================================

def calculate_trend(series):
    """
    Calculate a simple linear trend.

    Returns:
        direction
        percentage_change
        slope
        first_value
        last_value
        points
    """
    values = pd.to_numeric(
        series,
        errors="coerce"
    ).dropna()

    if len(values) < MIN_TREND_POINTS:

        return {
            "direction": "unknown",
            "percentage_change": 0.0,
            "slope": 0.0,
            "first_value": (
                clean_number(values.iloc[0])
                if len(values) > 0
                else None
            ),
            "last_value": (
                clean_number(values.iloc[-1])
                if len(values) > 0
                else None
            ),
            "points": len(values)
        }

    first = safe_float(
        values.iloc[0]
    )

    last = safe_float(
        values.iloc[-1]
    )

    change = percentage_change(
        first,
        last
    )

    try:
        x = np.arange(
            len(values),
            dtype=float
        )

        y = values.to_numpy(
            dtype=float
        )

        slope = np.polyfit(
            x,
            y,
            1
        )[0]

    except (TypeError, ValueError, np.linalg.LinAlgError):
        slope = 0.0

    if change > TREND_CHANGE_THRESHOLD:
        direction = "increasing"

    elif change < -TREND_CHANGE_THRESHOLD:
        direction = "decreasing"

    else:
        direction = "stable"

    return {
        "direction": direction,
        "percentage_change": round(
            float(change),
            2
        ),
        "slope": clean_number(
            slope
        ),
        "first_value": clean_number(
            first
        ),
        "last_value": clean_number(
            last
        ),
        "points": len(values)
    }


# ============================================================
# Robust Trend
# ============================================================

def calculate_robust_trend(
    series,
    anomalous_indices=None
):
    """
    Calculate observed and anomaly-adjusted trends.

    Anomalous observations are excluded from the adjusted
    baseline.

    The indices supplied must belong to the index of `series`.
    """
    anomalous_indices = normalize_indices(
        anomalous_indices
    )

    values = pd.to_numeric(
        series,
        errors="coerce"
    )

    observed = calculate_trend(
        values
    )

    adjusted_mask = ~values.index.isin(
        anomalous_indices
    )

    adjusted_values = values.loc[
        adjusted_mask
    ]

    adjusted = calculate_trend(
        adjusted_values
    )

    observed_direction = observed.get(
        "direction"
    )

    adjusted_direction = adjusted.get(
        "direction"
    )

    valid_indices = list(
        values.dropna().index
    )

    endpoint_affected = False

    if valid_indices:

        first_index = valid_indices[0]
        last_index = valid_indices[-1]

        endpoint_affected = (
            first_index in anomalous_indices
            or last_index in anomalous_indices
        )

    direction_changed = (
        observed_direction != adjusted_direction
        and observed_direction != "unknown"
        and adjusted_direction != "unknown"
    )

    if direction_changed:

        confidence = "low"

        reason = (
            "The anomaly-adjusted trend differs "
            "from the observed trend."
        )

    elif endpoint_affected:

        confidence = "low"

        reason = (
            "An anomalous observation affects "
            "a trend endpoint."
        )

    elif anomalous_indices:

        confidence = "medium"

        reason = (
            "Anomalies are present but do not "
            "materially change the trend direction."
        )

    else:

        confidence = "high"

        reason = (
            "No detected anomalies affect "
            "the trend calculation."
        )

    return {
        "observed": observed,
        "adjusted": adjusted,
        "confidence": confidence,
        "reason": reason,
        "anomaly_rows": len(
            anomalous_indices
        ),
        "endpoint_affected": endpoint_affected,
        "direction_changed": direction_changed
    }


# ============================================================
# Time Helpers
# ============================================================

def map_anomaly_rows_to_dates(
    df,
    anomalous_indices
):
    """
    Map original row-level anomaly indices to normalized
    calendar dates.

    This is the critical bridge between row-level anomaly
    detection and daily time-series analysis.
    """
    if "date" not in df.columns:
        return set()

    anomalous_indices = normalize_indices(
        anomalous_indices
    )

    if not anomalous_indices:
        return set()

    existing_indices = [
        index
        for index in anomalous_indices
        if index in df.index
    ]

    if not existing_indices:
        return set()

    dates = pd.to_datetime(
        df.loc[
            existing_indices,
            "date"
        ],
        errors="coerce"
    ).dropna()

    return set(
        dates.dt.normalize()
    )


def daily_anomaly_mask(
    daily_index,
    anomaly_dates
):
    """
    Build a boolean mask for daily rows affected by anomalies.
    """
    if not anomaly_dates:
        return pd.Series(
            False,
            index=daily_index
        )

    normalized_index = pd.to_datetime(
        daily_index
    ).normalize()

    return pd.Series(
        normalized_index.isin(
            anomaly_dates
        ),
        index=daily_index
    )


# ============================================================
# Time Analysis
# ============================================================

def analyze_time(
    df,
    anomalous_indices=None
):
    """
    Analyze sales over time.

    Returns:
        daily totals
        highest days
        observed trends
        adjusted trends
        trend confidence

    Anomalies are supplied as original row indices. They are
    mapped to dates before daily aggregation.
    """
    if "date" not in df.columns:
        return {}

    if (
        "quantity" not in df.columns
        and "revenue" not in df.columns
    ):
        return {}

    anomalous_indices = normalize_indices(
        anomalous_indices
    )

    data = df.copy()

    data["date"] = pd.to_datetime(
        data["date"],
        errors="coerce"
    )

    data = data.dropna(
        subset=["date"]
    )

    if data.empty:
        return {}

    aggregations = {}

    if "quantity" in data.columns:
        data["quantity"] = pd.to_numeric(
            data["quantity"],
            errors="coerce"
        )

        aggregations["quantity"] = "sum"

    if "revenue" in data.columns:
        data["revenue"] = pd.to_numeric(
            data["revenue"],
            errors="coerce"
        )

        aggregations["revenue"] = "sum"

    daily = (
        data
        .groupby(
            data["date"].dt.normalize()
        )
        .agg(aggregations)
        .sort_index()
    )

    result = {
        "daily": [],
        "highest_quantity_day": None,
        "highest_revenue_day": None,
        "revenue_trend": None,
        "quantity_trend": None,
        "anomaly_dates": []
    }

    # --------------------------------------------------------
    # Map row-level anomalies -> daily dates
    # --------------------------------------------------------

    anomaly_dates = map_anomaly_rows_to_dates(
        df,
        anomalous_indices
    )

    result["anomaly_dates"] = sorted(
        str(value.date())
        for value in anomaly_dates
    )

    daily_mask = daily_anomaly_mask(
        daily.index,
        anomaly_dates
    )

    # --------------------------------------------------------
    # Daily Data
    # --------------------------------------------------------

    for date, row in daily.iterrows():

        item = {
            "date": str(
                pd.Timestamp(date).date()
            )
        }

        if "quantity" in daily.columns:
            item["quantity"] = clean_number(
                row["quantity"]
            )

        if "revenue" in daily.columns:
            item["revenue"] = clean_number(
                row["revenue"]
            )

        item["anomaly_affected"] = bool(
            daily_mask.loc[date]
        )

        result["daily"].append(item)

    # --------------------------------------------------------
    # Highest Quantity Day
    # --------------------------------------------------------

    if "quantity" in daily.columns:

        valid_quantity = daily[
            "quantity"
        ].dropna()

        if not valid_quantity.empty:

            highest = valid_quantity.idxmax()

            result["highest_quantity_day"] = {
                "date": str(
                    pd.Timestamp(highest).date()
                ),
                "quantity": clean_number(
                    daily.loc[
                        highest,
                        "quantity"
                    ]
                ),
                "anomaly_affected": bool(
                    daily_mask.loc[highest]
                )
            }

    # --------------------------------------------------------
    # Highest Revenue Day
    # --------------------------------------------------------

    if "revenue" in daily.columns:

        valid_revenue = daily[
            "revenue"
        ].dropna()

        if not valid_revenue.empty:

            highest = valid_revenue.idxmax()

            result["highest_revenue_day"] = {
                "date": str(
                    pd.Timestamp(highest).date()
                ),
                "revenue": clean_number(
                    daily.loc[
                        highest,
                        "revenue"
                    ]
                ),
                "anomaly_affected": bool(
                    daily_mask.loc[highest]
                )
            }

    # --------------------------------------------------------
    # Revenue Trend
    # --------------------------------------------------------

    if "revenue" in daily.columns:

        adjusted_revenue = daily.loc[
            ~daily_mask,
            "revenue"
        ]

        result["revenue_trend"] = (
            calculate_robust_trend(
                daily["revenue"],
                anomalous_indices=daily.index[
                    daily_mask
                ]
            )
        )

        result["revenue_trend"]["adjusted"] = (
            calculate_trend(
                adjusted_revenue
            )
        )

        result["revenue_trend"][
            "anomaly_dates"
        ] = sorted(
            str(value.date())
            for value in anomaly_dates
        )

    # --------------------------------------------------------
    # Quantity Trend
    # --------------------------------------------------------

    if "quantity" in daily.columns:

        adjusted_quantity = daily.loc[
            ~daily_mask,
            "quantity"
        ]

        result["quantity_trend"] = (
            calculate_robust_trend(
                daily["quantity"],
                anomalous_indices=daily.index[
                    daily_mask
                ]
            )
        )

        result["quantity_trend"]["adjusted"] = (
            calculate_trend(
                adjusted_quantity
            )
        )

        result["quantity_trend"][
            "anomaly_dates"
        ] = sorted(
            str(value.date())
            for value in anomaly_dates
        )

    return result


# ============================================================
# Sales Concentration
# ============================================================

def analyze_concentration(df):
    """
    Analyze observed revenue concentration.
    """
    if "product" not in df.columns:
        return {}

    if "revenue" not in df.columns:
        return {}

    data = df[
        ["product", "revenue"]
    ].copy()

    data["product"] = (
        data["product"]
        .astype(str)
        .str.strip()
    )

    data["revenue"] = pd.to_numeric(
        data["revenue"],
        errors="coerce"
    )

    grouped = (
        data
        .groupby("product")["revenue"]
        .sum()
        .sort_values(
            ascending=False,
            kind="stable"
        )
    )

    total_revenue = safe_float(
        grouped.sum()
    )

    if total_revenue <= 0:

        return {
            "total_revenue": 0,
            "top_product": None,
            "top_product_share": 0.0,
            "top_3_product_share": 0.0,
            "classification": "unknown"
        }

    top_product = grouped.index[0]

    top_product_share = (
        grouped.head(1).sum()
        / total_revenue
    ) * 100

    top_3_share = (
        grouped.head(3).sum()
        / total_revenue
    ) * 100

    if (
        top_3_share
        >= HIGH_CONCENTRATION_THRESHOLD
    ):
        classification = (
            "highly_concentrated"
        )

    elif (
        top_3_share
        >= LOW_CONCENTRATION_THRESHOLD
    ):
        classification = (
            "moderately_concentrated"
        )

    else:
        classification = "diversified"

    return {
        "total_revenue": clean_number(
            total_revenue
        ),
        "top_product": str(
            top_product
        ),
        "top_product_share": round(
            float(top_product_share),
            2
        ),
        "top_3_product_share": round(
            float(top_3_share),
            2
        ),
        "classification": classification
    }


# ============================================================
# Anomaly Analysis
# ============================================================

def analyze_anomaly_impact(
    df,
    anomalies
):
    """
    Determine the business impact of anomaly rows.

    Uses row-level anomaly records from the anomaly detector.
    """
    if not anomalies:

        return {
            "anomalous_rows": [],
            "affected_rows": 0,
            "affected_columns": [],
            "affected_products": [],
            "affected_dates": [],
            "observed_revenue": clean_number(
                df["revenue"].sum()
            )
            if "revenue" in df.columns
            else 0,
            "anomalous_revenue": 0,
            "anomalous_revenue_share": 0.0,
            "adjusted_revenue": (
                clean_number(
                    df["revenue"].sum()
                )
                if "revenue" in df.columns
                else 0
            ),
            "observed_quantity": (
                clean_number(
                    df["quantity"].sum()
                )
                if "quantity" in df.columns
                else 0
            ),
            "anomalous_quantity": 0,
            "anomalous_quantity_share": 0.0,
            "adjusted_quantity": (
                clean_number(
                    df["quantity"].sum()
                )
                if "quantity" in df.columns
                else 0
            ),
            "severity_counts": {},
            "methods": [],
            "row_indices": []
        }

    row_indices = set()
    columns = set()
    severity_counts = {}
    methods = set()

    for anomaly in anomalies:

        if not isinstance(
            anomaly,
            dict
        ):
            continue

        row = anomaly.get(
            "row"
        )

        if row in df.index:
            row_indices.add(row)

        column = anomaly.get(
            "column"
        )

        if column:
            columns.add(column)

        severity = anomaly.get(
            "severity"
        )

        if severity:
            severity_counts[
                severity
            ] = (
                severity_counts.get(
                    severity,
                    0
                ) + 1
            )

        method = anomaly.get(
            "method"
        )

        if method:
            methods.add(method)

    anomalous_rows = df.loc[
        df.index.intersection(
            list(row_indices)
        )
    ].copy()

    observed_revenue = (
        safe_float(
            df["revenue"].sum()
        )
        if "revenue" in df.columns
        else 0.0
    )

    anomalous_revenue = (
        safe_float(
            anomalous_rows["revenue"].sum()
        )
        if "revenue" in anomalous_rows.columns
        else 0.0
    )

    adjusted_revenue = (
        observed_revenue
        - anomalous_revenue
    )

    observed_quantity = (
        safe_float(
            df["quantity"].sum()
        )
        if "quantity" in df.columns
        else 0.0
    )

    anomalous_quantity = (
        safe_float(
            anomalous_rows["quantity"].sum()
        )
        if "quantity" in anomalous_rows.columns
        else 0.0
    )

    adjusted_quantity = (
        observed_quantity
        - anomalous_quantity
    )

    if observed_revenue != 0:

        revenue_share = (
            anomalous_revenue
            / abs(observed_revenue)
        ) * 100

    else:
        revenue_share = 0.0

    if observed_quantity != 0:

        quantity_share = (
            anomalous_quantity
            / abs(observed_quantity)
        ) * 100

    else:
        quantity_share = 0.0

    affected_products = []

    if "product" in anomalous_rows.columns:

        affected_products = (
            anomalous_rows["product"]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
        )

    affected_dates = []

    if "date" in anomalous_rows.columns:

        dates = pd.to_datetime(
            anomalous_rows["date"],
            errors="coerce"
        ).dropna()

        affected_dates = [
            str(value.date())
            for value in dates
        ]

    return {
        "anomalous_rows": [
            index_to_output_value(index)
            for index in sorted(
                row_indices,
                key=lambda value: str(value)
            )
        ],
        "affected_rows": len(
            row_indices
        ),
        "affected_columns": sorted(
            columns
        ),
        "affected_products": (
            affected_products
        ),
        "affected_dates": sorted(
            set(affected_dates)
        ),
        "observed_revenue": clean_number(
            observed_revenue
        ),
        "anomalous_revenue": clean_number(
            anomalous_revenue
        ),
        "anomalous_revenue_share": round(
            revenue_share,
            2
        ),
        "adjusted_revenue": clean_number(
            adjusted_revenue
        ),
        "observed_quantity": clean_number(
            observed_quantity
        ),
        "anomalous_quantity": clean_number(
            anomalous_quantity
        ),
        "anomalous_quantity_share": round(
            quantity_share,
            2
        ),
        "adjusted_quantity": clean_number(
            adjusted_quantity
        ),
        "severity_counts": severity_counts,
        "methods": sorted(methods),
        "row_indices": list(
            row_indices
        )
    }


def analyze_anomalies(
    anomaly_summary,
    anomalies=None,
    df=None
):
    """
    Convert anomaly detector output into business signals.

    Supports:

        analyze_anomalies(summary)

    and:

        analyze_anomalies(
            summary,
            anomalies,
            df
        )
    """
    if anomaly_summary is None:
        anomaly_summary = {}

    total = safe_int(
        anomaly_summary.get(
            "total_anomalies",
            0
        )
    )

    by_column = anomaly_summary.get(
        "by_column",
        {}
    )

    by_method = anomaly_summary.get(
        "by_method",
        {}
    )

    by_severity = anomaly_summary.get(
        "by_severity",
        {}
    )

    if not isinstance(by_column, dict):
        by_column = {}

    if not isinstance(by_method, dict):
        by_method = {}

    if not isinstance(by_severity, dict):
        by_severity = {}

    result = {
        "total_anomalies": total,
        "affected_columns": list(
            by_column.keys()
        ),
        "critical_anomalies": safe_int(
            by_severity.get(
                "critical",
                0
            )
        ),
        "warning_anomalies": safe_int(
            by_severity.get(
                "warning",
                0
            )
        ),
        "by_column": dict(
            by_column
        ),
        "by_method": dict(
            by_method
        ),
        "by_severity": dict(
            by_severity
        )
    }

    if (
        isinstance(df, pd.DataFrame)
        and anomalies is not None
    ):

        impact = analyze_anomaly_impact(
            df,
            anomalies
        )

        result.update(
            impact
        )

    else:

        result.update({
            "anomalous_rows": [],
            "affected_rows": 0,
            "affected_columns": list(by_column.keys()),
            "affected_products": [],
            "affected_dates": [],
            "observed_revenue": 0,
            "anomalous_revenue": 0,
            "anomalous_revenue_share": 0.0,
            "adjusted_revenue": 0,
            "observed_quantity": 0,
            "anomalous_quantity": 0,
            "anomalous_quantity_share": 0.0,
            "adjusted_quantity": 0,
            "severity_counts": {},
            "methods": [],
            "row_indices": []
        })

    return result


# ============================================================
# Adjusted Summary
# ============================================================

def calculate_adjusted_summary(
    df,
    anomaly_rows
):
    """
    Calculate business metrics after excluding
    anomaly-affected rows.
    """
    anomaly_rows = normalize_indices(
        anomaly_rows
    )

    valid_anomaly_rows = [
        index
        for index in anomaly_rows
        if index in df.index
    ]

    adjusted = df.drop(
        labels=valid_anomaly_rows,
        errors="ignore"
    )

    summary = calculate_summary(
        adjusted
    )

    summary["excluded_rows"] = len(
        valid_anomaly_rows
    )

    summary["remaining_rows"] = len(
        adjusted
    )

    return summary


# ============================================================
# Observed vs Adjusted Analysis
# ============================================================

def build_observed_adjusted_analysis(
    observed_summary,
    adjusted_summary
):
    """
    Compare observed and adjusted metrics.
    """
    observed_revenue = safe_float(
        observed_summary.get(
            "total_revenue",
            0
        )
    )

    adjusted_revenue = safe_float(
        adjusted_summary.get(
            "total_revenue",
            0
        )
    )

    observed_quantity = safe_float(
        observed_summary.get(
            "total_quantity",
            0
        )
    )

    adjusted_quantity = safe_float(
        adjusted_summary.get(
            "total_quantity",
            0
        )
    )

    revenue_difference = (
        observed_revenue
        - adjusted_revenue
    )

    quantity_difference = (
        observed_quantity
        - adjusted_quantity
    )

    if observed_revenue != 0:

        revenue_share = (
            revenue_difference
            / abs(observed_revenue)
        ) * 100

    else:
        revenue_share = 0.0

    if observed_quantity != 0:

        quantity_share = (
            quantity_difference
            / abs(observed_quantity)
        ) * 100

    else:
        quantity_share = 0.0

    return {
        "observed": {
            "revenue": clean_number(
                observed_revenue
            ),
            "quantity": clean_number(
                observed_quantity
            )
        },
        "adjusted": {
            "revenue": clean_number(
                adjusted_revenue
            ),
            "quantity": clean_number(
                adjusted_quantity
            )
        },
        "impact": {
            "revenue_difference": clean_number(
                revenue_difference
            ),
            "revenue_share": round(
                revenue_share,
                2
            ),
            "quantity_difference": clean_number(
                quantity_difference
            ),
            "quantity_share": round(
                quantity_share,
                2
            )
        }
    }


# ============================================================
# Profiler Analysis
# ============================================================

def analyze_profiler(profile):
    """
    Extract business signals from Profiler V3.
    """
    result = {
        "outlier_columns": [],
        "identifier_columns": [],
        "strong_correlations": [],
        "warnings": [],
        "intelligence_signals": []
    }

    if not isinstance(profile, dict):
        return result

    column_profiles = profile.get(
        "column_profiles",
        {}
    )

    if not isinstance(column_profiles, dict):
        column_profiles = {}

    # --------------------------------------------------------
    # Column Intelligence
    # --------------------------------------------------------

    for column, details in (
        column_profiles.items()
    ):

        if not isinstance(
            details,
            dict
        ):
            continue

        intelligence = details.get(
            "intelligence",
            {}
        )

        if not isinstance(intelligence, dict):
            intelligence = {}

        signals = intelligence.get(
            "signals",
            []
        )

        if not isinstance(signals, list):
            signals = []

        for signal in signals:

            result[
                "intelligence_signals"
            ].append({
                "column": column,
                "signal": signal
            })

        if "contains_outliers" in signals:

            result[
                "outlier_columns"
            ].append(column)

        if intelligence.get(
            "likely_identifier",
            False
        ):

            result[
                "identifier_columns"
            ].append(column)

        numeric = details.get(
            "numeric",
            {}
        )

        if not isinstance(numeric, dict):
            continue

        if numeric.get(
            "distribution_shape"
        ) == "highly_right_skewed":

            result["warnings"].append({
                "column": column,
                "type": "right_skew",
                "message": (
                    f"{column} is highly "
                    "right skewed."
                )
            })

        if numeric.get(
            "variability"
        ) == "high":

            result["warnings"].append({
                "column": column,
                "type": "high_variability",
                "message": (
                    f"{column} has high "
                    "relative variability."
                )
            })

    # --------------------------------------------------------
    # Relationships
    # --------------------------------------------------------

    relationships = profile.get(
        "relationships",
        {}
    )

    if not isinstance(relationships, dict):
        relationships = {}

    correlation_details = (
        relationships.get(
            "correlation_details",
            {}
        )
    )

    if not isinstance(correlation_details, dict):
        correlation_details = {}

    for name, details in (
        correlation_details.items()
    ):

        if not isinstance(
            details,
            dict
        ):
            continue

        correlation = details.get(
            "correlation"
        )

        if (
            correlation is None
            or abs(
                safe_float(correlation)
            ) < STRONG_CORRELATION_THRESHOLD
        ):
            continue

        result[
            "strong_correlations"
        ].append({
            "columns": name,
            "correlation": clean_number(
                correlation
            ),
            "strength": details.get(
                "strength",
                "strong"
            ),
            "direction": details.get(
                "direction",
                "unknown"
            ),
            "outlier_warning": details.get(
                "outlier_warning"
            )
        })

    # --------------------------------------------------------
    # Outlier-Driven Correlation Warnings
    # --------------------------------------------------------

    outlier_warnings = (
        relationships.get(
            "outlier_warnings",
            []
        )
    )

    if not isinstance(outlier_warnings, list):
        outlier_warnings = []

    for warning in outlier_warnings:

        if not isinstance(
            warning,
            dict
        ):
            continue

        result["warnings"].append({
            "type": (
                "outlier_driven_correlation"
            ),
            "columns": warning.get(
                "columns",
                []
            ),
            "message": warning.get(
                "message",
                ""
            )
        })

    # --------------------------------------------------------
    # Dataset Intelligence
    # --------------------------------------------------------

    dataset_intelligence = profile.get(
        "dataset_intelligence",
        []
    )

    if not isinstance(dataset_intelligence, list):
        dataset_intelligence = []

    for item in dataset_intelligence:

        if isinstance(
            item,
            dict
        ):

            result["warnings"].append({
                "type": item.get(
                    "type",
                    "dataset_signal"
                ),
                "severity": item.get(
                    "severity",
                    "info"
                ),
                "columns": item.get(
                    "columns",
                    []
                ),
                "message": item.get(
                    "message",
                    ""
                )
            })

    # --------------------------------------------------------
    # Deterministic Deduplication
    # --------------------------------------------------------

    result["outlier_columns"] = list(
        dict.fromkeys(
            result["outlier_columns"]
        )
    )

    result["identifier_columns"] = list(
        dict.fromkeys(
            result["identifier_columns"]
        )
    )

    return result


# ============================================================
# Confidence Engine
# ============================================================

def determine_confidence(
    anomaly_analysis,
    profiler_analysis,
    relevant_revenue=True
):
    """
    Determine confidence in business conclusions.

    This is intentionally conservative.
    """
    anomaly_share = safe_float(
        anomaly_analysis.get(
            "anomalous_revenue_share",
            0
        )
    )

    if (
        relevant_revenue
        and anomaly_share
        >= VERY_HIGH_ANOMALY_REVENUE_SHARE
    ):
        return "low"

    if (
        relevant_revenue
        and anomaly_share
        >= HIGH_ANOMALY_REVENUE_SHARE
    ):
        return "medium"

    warnings = profiler_analysis.get(
        "warnings",
        []
    )

    if len(warnings) >= 3:
        return "medium"

    return "high"


# ============================================================
# Generate Core Insights
# ============================================================

def generate_insights(
    summary,
    adjusted_summary,
    product_analysis,
    category_analysis,
    time_analysis,
    concentration,
    anomaly_analysis,
    profiler_analysis
):
    """
    Generate evidence-aware business insights.
    """
    insights = []

    total_revenue = safe_float(
        summary.get(
            "total_revenue",
            0
        )
    )

    total_quantity = safe_float(
        summary.get(
            "total_quantity",
            0
        )
    )

    anomaly_revenue_share = safe_float(
        anomaly_analysis.get(
            "anomalous_revenue_share",
            0
        )
    )

    anomaly_quantity_share = safe_float(
        anomaly_analysis.get(
            "anomalous_quantity_share",
            0
        )
    )

    # --------------------------------------------------------
    # Revenue
    # --------------------------------------------------------

    if total_revenue > 0:

        insights.append({
            "type": "revenue",
            "severity": "info",
            "confidence": determine_confidence(
                anomaly_analysis,
                profiler_analysis
            ),
            "revenue": clean_number(
                total_revenue
            ),
            "message": (
                f"Observed total revenue is "
                f"{total_revenue:,.2f}."
            )
        })

    # --------------------------------------------------------
    # Quantity
    # --------------------------------------------------------

    if total_quantity > 0:

        insights.append({
            "type": "sales_volume",
            "severity": "info",
            "confidence": determine_confidence(
                anomaly_analysis,
                profiler_analysis,
                relevant_revenue=False
            ),
            "quantity": clean_number(
                total_quantity
            ),
            "message": (
                f"Observed total quantity sold is "
                f"{total_quantity:,.0f} units."
            )
        })

    # --------------------------------------------------------
    # Anomaly Impact
    # --------------------------------------------------------

    if anomaly_revenue_share >= HIGH_ANOMALY_REVENUE_SHARE:

        insights.append({
            "type": "anomaly_revenue_impact",
            "severity": "critical",
            "confidence": "high",
            "revenue_share": round(
                anomaly_revenue_share,
                2
            ),
            "message": (
                f"{anomaly_revenue_share:.2f}% of observed "
                "revenue comes from anomaly-affected rows. "
                "Raw revenue should not be treated as a "
                "reliable representation of the underlying "
                "business baseline."
            )
        })

    elif anomaly_revenue_share > 0:

        insights.append({
            "type": "anomaly_revenue_impact",
            "severity": "warning",
            "confidence": "high",
            "revenue_share": round(
                anomaly_revenue_share,
                2
            ),
            "message": (
                f"{anomaly_revenue_share:.2f}% of observed "
                "revenue is associated with anomaly-affected "
                "rows."
            )
        })

    if anomaly_quantity_share >= HIGH_ANOMALY_QUANTITY_SHARE:

        insights.append({
            "type": "anomaly_quantity_impact",
            "severity": "warning",
            "confidence": "high",
            "quantity_share": round(
                anomaly_quantity_share,
                2
            ),
            "message": (
                f"{anomaly_quantity_share:.2f}% of observed "
                "sales volume comes from anomaly-affected "
                "rows."
            )
        })

    # --------------------------------------------------------
    # Top Product
    # --------------------------------------------------------

    top_products = product_analysis.get(
        "top_by_revenue",
        []
    )

    if top_products:

        top = top_products[0]

        confidence = (
            "low"
            if (
                top.get("revenue", 0)
                and top.get("product")
                in anomaly_analysis.get(
                    "affected_products",
                    []
                )
            )
            else "high"
        )

        insights.append({
            "type": "top_product",
            "severity": "info",
            "confidence": confidence,
            "product": top["product"],
            "revenue": top["revenue"],
            "message": (
                f"{top['product']} is the leading "
                f"observed revenue product with "
                f"{top['revenue']:,.2f} in revenue."
            )
        })

    # --------------------------------------------------------
    # Top Volume Product
    # --------------------------------------------------------

    top_quantity = product_analysis.get(
        "top_by_quantity",
        []
    )

    if top_quantity:

        top = top_quantity[0]

        insights.append({
            "type": "top_volume_product",
            "severity": "info",
            "confidence": "high",
            "product": top["product"],
            "quantity": top["quantity"],
            "message": (
                f"{top['product']} has the highest "
                f"observed sales volume at "
                f"{top['quantity']:,.0f} units."
            )
        })

    # --------------------------------------------------------
    # Top Category
    # --------------------------------------------------------

    top_category = category_analysis.get(
        "top_category"
    )

    if top_category:

        category = top_category.get(
            "category"
        )

        if "revenue" in top_category:

            insights.append({
                "type": "top_category",
                "severity": "info",
                "confidence": "high",
                "category": category,
                "revenue": top_category[
                    "revenue"
                ],
                "message": (
                    f"{category} is the highest-"
                    "revenue category with "
                    f"{top_category['revenue']:,.2f}."
                )
            })

    # --------------------------------------------------------
    # Best Day
    # --------------------------------------------------------

    highest_day = time_analysis.get(
        "highest_revenue_day"
    )

    if highest_day:

        highest_date = highest_day[
            "date"
        ]

        confidence = (
            "low"
            if highest_day.get(
                "anomaly_affected",
                highest_date in anomaly_analysis.get(
                    "affected_dates",
                    []
                )
            )
            else "high"
        )

        insights.append({
            "type": "best_day",
            "severity": "info",
            "confidence": confidence,
            "date": highest_date,
            "revenue": highest_day[
                "revenue"
            ],
            "message": (
                f"{highest_date} generated the "
                "highest observed daily revenue at "
                f"{highest_day['revenue']:,.2f}."
            )
        })

    # --------------------------------------------------------
    # Revenue Trend
    # --------------------------------------------------------

    revenue_trend = time_analysis.get(
        "revenue_trend"
    )

    if revenue_trend:

        observed = revenue_trend.get(
            "observed",
            {}
        )

        adjusted = revenue_trend.get(
            "adjusted",
            {}
        )

        observed_direction = observed.get(
            "direction"
        )

        adjusted_direction = adjusted.get(
            "direction"
        )

        confidence = revenue_trend.get(
            "confidence",
            "medium"
        )

        if (
            observed_direction
            != adjusted_direction
            and adjusted_direction
            != "unknown"
        ):

            insights.append({
                "type": "revenue_trend",
                "severity": "warning",
                "confidence": "low",
                "direction": adjusted_direction,
                "observed_direction": observed_direction,
                "adjusted_direction": adjusted_direction,
                "percentage_change": adjusted.get(
                    "percentage_change",
                    0
                ),
                "message": (
                    "The observed revenue trend is "
                    "not reliable because anomaly "
                    "adjustment changes the trend "
                    f"from {observed_direction} to "
                    f"{adjusted_direction}."
                )
            })

        elif observed_direction != "unknown":

            insights.append({
                "type": "revenue_trend",
                "severity": (
                    "positive"
                    if observed_direction
                    == "increasing"
                    else
                    "warning"
                    if observed_direction
                    == "decreasing"
                    else
                    "info"
                ),
                "confidence": confidence,
                "direction": observed_direction,
                "observed_percentage_change": (
                    observed.get(
                        "percentage_change",
                        0
                    )
                ),
                "adjusted_percentage_change": (
                    adjusted.get(
                        "percentage_change",
                        0
                    )
                ),
                "message": (
                    f"Revenue is {observed_direction}. "
                    f"Observed change is "
                    f"{observed.get('percentage_change', 0):.2f}%, "
                    f"while the anomaly-adjusted change is "
                    f"{adjusted.get('percentage_change', 0):.2f}%."
                )
            })

    # --------------------------------------------------------
    # Quantity Trend
    # --------------------------------------------------------

    quantity_trend = time_analysis.get(
        "quantity_trend"
    )

    if quantity_trend:

        observed = quantity_trend.get(
            "observed",
            {}
        )

        adjusted = quantity_trend.get(
            "adjusted",
            {}
        )

        observed_direction = observed.get(
            "direction"
        )

        adjusted_direction = adjusted.get(
            "direction"
        )

        if (
            observed_direction
            != adjusted_direction
            and adjusted_direction
            != "unknown"
        ):

            insights.append({
                "type": "quantity_trend",
                "severity": "warning",
                "confidence": "low",
                "direction": adjusted_direction,
                "observed_direction": observed_direction,
                "adjusted_direction": adjusted_direction,
                "message": (
                    "The observed sales-volume trend "
                    "changes after anomaly adjustment."
                )
            })

        elif observed_direction != "unknown":

            insights.append({
                "type": "quantity_trend",
                "severity": "info",
                "confidence": quantity_trend.get(
                    "confidence",
                    "medium"
                ),
                "direction": observed_direction,
                "observed_percentage_change": (
                    observed.get(
                        "percentage_change",
                        0
                    )
                ),
                "adjusted_percentage_change": (
                    adjusted.get(
                        "percentage_change",
                        0
                    )
                ),
                "message": (
                    f"Sales volume is "
                    f"{observed_direction}, with an "
                    f"observed change of "
                    f"{observed.get('percentage_change', 0):.2f}%."
                )
            })

    # --------------------------------------------------------
    # Concentration
    # --------------------------------------------------------

    classification = concentration.get(
        "classification"
    )

    if classification == "highly_concentrated":

        insights.append({
            "type": "revenue_concentration",
            "severity": "warning",
            "confidence": "high",
            "share": concentration.get(
                "top_3_product_share",
                0
            ),
            "message": (
                "Revenue is highly concentrated "
                "among a small number of products."
            )
        })

    elif classification == "moderately_concentrated":

        insights.append({
            "type": "revenue_concentration",
            "severity": "info",
            "confidence": "high",
            "share": concentration.get(
                "top_3_product_share",
                0
            ),
            "message": (
                "Revenue is moderately concentrated "
                "among the leading products."
            )
        })

    # --------------------------------------------------------
    # Critical Anomalies
    # --------------------------------------------------------

    critical = safe_int(
        anomaly_analysis.get(
            "critical_anomalies",
            0
        )
    )

    warnings = safe_int(
        anomaly_analysis.get(
            "warning_anomalies",
            0
        )
    )

    if critical > 0:

        word = (
            "anomaly"
            if critical == 1
            else "anomalies"
        )

        insights.append({
            "type": "anomaly",
            "severity": "critical",
            "confidence": "high",
            "message": (
                f"{critical} critical "
                f"{word} were detected."
            )
        })

    if warnings > 0:

        word = (
            "anomaly"
            if warnings == 1
            else "anomalies"
        )

        insights.append({
            "type": "anomaly",
            "severity": "warning",
            "confidence": "high",
            "message": (
                f"{warnings} warning "
                f"{word} were detected."
            )
        })

    # --------------------------------------------------------
    # Profiler Outliers
    # --------------------------------------------------------

    for column in profiler_analysis.get(
        "outlier_columns",
        []
    ):

        insights.append({
            "type": "outlier",
            "severity": "warning",
            "confidence": "high",
            "column": column,
            "message": (
                f"{column} contains statistical "
                "outliers."
            )
        })

    # --------------------------------------------------------
    # Identifier Columns
    # --------------------------------------------------------

    for column in profiler_analysis.get(
        "identifier_columns",
        []
    ):

        insights.append({
            "type": "identifier",
            "severity": "info",
            "confidence": "high",
            "column": column,
            "message": (
                f"{column} appears to behave "
                "like an identifier."
            )
        })

    # --------------------------------------------------------
    # Correlations
    # --------------------------------------------------------

    for correlation in profiler_analysis.get(
        "strong_correlations",
        []
    ):

        columns = correlation.get(
            "columns",
            ""
        )

        strength = correlation.get(
            "strength",
            "strong"
        )

        direction = correlation.get(
            "direction",
            "unknown"
        )

        outlier_warning = correlation.get(
            "outlier_warning"
        )

        confidence = (
            "low"
            if outlier_warning
            else "high"
        )

        insights.append({
            "type": "correlation",
            "severity": (
                "warning"
                if outlier_warning
                else "info"
            ),
            "confidence": confidence,
            "columns": columns,
            "correlation": correlation.get(
                "correlation"
            ),
            "message": (
                f"{columns} show a "
                f"{strength} "
                f"{direction} correlation."
            )
        })

        if outlier_warning:

            insights.append({
                "type": "correlation_warning",
                "severity": "warning",
                "confidence": "high",
                "columns": columns,
                "message": outlier_warning
            })

    return insights


# ============================================================
# Opportunity Generation
# ============================================================

def generate_opportunities(
    product_analysis,
    category_analysis,
    time_analysis,
    concentration,
    anomaly_analysis
):
    """
    Generate evidence-based business opportunities.
    """
    opportunities = []

    affected_products = set(
        anomaly_analysis.get(
            "affected_products",
            []
        )
    )

    anomaly_share = safe_float(
        anomaly_analysis.get(
            "anomalous_revenue_share",
            0
        )
    )

    # --------------------------------------------------------
    # Strong Product
    # --------------------------------------------------------

    top_products = product_analysis.get(
        "top_by_revenue",
        []
    )

    if top_products:

        top = top_products[0]

        if top["product"] in affected_products:

            opportunities.append({
                "type": "product_validation",
                "priority": "high",
                "product": top["product"],
                "confidence": "low",
                "message": (
                    f"{top['product']} leads observed "
                    "revenue, but its performance is "
                    "affected by detected anomalies. "
                    "Validate the underlying transaction "
                    "before increasing inventory or promotion."
                )
            })

        else:

            opportunities.append({
                "type": "product_growth",
                "priority": "high",
                "product": top["product"],
                "confidence": "high",
                "message": (
                    f"{top['product']} is the leading "
                    "revenue product and may be a candidate "
                    "for additional promotion or inventory."
                )
            })

    # --------------------------------------------------------
    # Increasing Revenue
    # --------------------------------------------------------

    trend = time_analysis.get(
        "revenue_trend"
    )

    if trend:

        adjusted = trend.get(
            "adjusted",
            {}
        )

        if adjusted.get(
            "direction"
        ) == "increasing":

            opportunities.append({
                "type": "growth",
                "priority": "high",
                "confidence": trend.get(
                    "confidence",
                    "medium"
                ),
                "message": (
                    "The anomaly-adjusted revenue baseline "
                    "is trending upward. Strong-performing "
                    "products or categories may deserve "
                    "additional attention."
                )
            })

    # --------------------------------------------------------
    # Diversification
    # --------------------------------------------------------

    if concentration.get(
        "classification"
    ) == "highly_concentrated":

        opportunities.append({
            "type": "diversification",
            "priority": "medium",
            "confidence": "high",
            "message": (
                "Revenue concentration creates an "
                "opportunity to develop secondary "
                "products and reduce dependence "
                "on the leading product."
            )
        })

    # --------------------------------------------------------
    # Category Optimization
    # --------------------------------------------------------

    categories = category_analysis.get(
        "categories",
        []
    )

    if len(categories) >= 2:

        strongest = categories[0]
        weakest = categories[-1]

        if (
            "revenue" in strongest
            and "revenue" in weakest
            and safe_float(
                strongest["revenue"]
            )
            > safe_float(
                weakest["revenue"]
            )
        ):

            opportunities.append({
                "type": "category_optimization",
                "priority": "medium",
                "confidence": "high",
                "strongest_category": (
                    strongest["category"]
                ),
                "weakest_category": (
                    weakest["category"]
                ),
                "message": (
                    f"{strongest['category']} is "
                    f"outperforming {weakest['category']}. "
                    "Category-level allocation and "
                    "promotion could be optimized."
                )
            })

    # --------------------------------------------------------
    # Clean Baseline Opportunity
    # --------------------------------------------------------

    if anomaly_share >= HIGH_ANOMALY_REVENUE_SHARE:

        opportunities.append({
            "type": "data_validation",
            "priority": "critical",
            "confidence": "high",
            "message": (
                "Validate the anomaly-affected transactions "
                "before making strategic decisions because "
                f"{anomaly_share:.2f}% of observed revenue "
                "is associated with anomalies."
            )
        })

    return opportunities


# ============================================================
# Risk Generation
# ============================================================

def generate_risks(
    anomaly_analysis,
    profiler_analysis,
    time_analysis,
    concentration
):
    """
    Generate business risks from data signals.
    """
    risks = []

    # --------------------------------------------------------
    # Critical Anomalies
    # --------------------------------------------------------

    critical = safe_int(
        anomaly_analysis.get(
            "critical_anomalies",
            0
        )
    )

    if critical > 0:

        risks.append({
            "type": "data_anomaly",
            "severity": "critical",
            "confidence": "high",
            "message": (
                f"{critical} critical data anomalies "
                "may distort business metrics and "
                "should be investigated."
            )
        })

    # --------------------------------------------------------
    # Revenue Impact
    # --------------------------------------------------------

    anomaly_share = safe_float(
        anomaly_analysis.get(
            "anomalous_revenue_share",
            0
        )
    )

    if anomaly_share >= VERY_HIGH_ANOMALY_REVENUE_SHARE:

        risks.append({
            "type": "anomaly_revenue_risk",
            "severity": "critical",
            "confidence": "high",
            "revenue_share": anomaly_share,
            "message": (
                f"{anomaly_share:.2f}% of observed revenue "
                "is associated with anomaly-affected rows. "
                "Strategic conclusions based on raw revenue "
                "are unreliable until these transactions "
                "are validated."
            )
        })

    elif anomaly_share >= HIGH_ANOMALY_REVENUE_SHARE:

        risks.append({
            "type": "anomaly_revenue_risk",
            "severity": "warning",
            "confidence": "high",
            "revenue_share": anomaly_share,
            "message": (
                f"{anomaly_share:.2f}% of observed revenue "
                "is associated with anomaly-affected rows."
            )
        })

    # --------------------------------------------------------
    # Outliers
    # --------------------------------------------------------

    outlier_columns = profiler_analysis.get(
        "outlier_columns",
        []
    )

    if outlier_columns:

        risks.append({
            "type": "outlier_risk",
            "severity": "warning",
            "confidence": "high",
            "columns": outlier_columns,
            "message": (
                "Statistical outliers exist in numeric "
                "columns and may distort averages, "
                "correlations, and trends."
            )
        })

    # --------------------------------------------------------
    # Outlier-Driven Correlations
    # --------------------------------------------------------

    for warning in profiler_analysis.get(
        "warnings",
        []
    ):

        if (
            warning.get("type")
            == "outlier_driven_correlation"
        ):

            risks.append({
                "type": "correlation_risk",
                "severity": "warning",
                "confidence": "high",
                "columns": warning.get(
                    "columns",
                    []
                ),
                "message": warning.get(
                    "message",
                    "A correlation may be "
                    "influenced by outliers."
                )
            })

    # --------------------------------------------------------
    # High Variability / Skew
    # --------------------------------------------------------

    for warning in profiler_analysis.get(
        "warnings",
        []
    ):

        if warning.get(
            "type"
        ) in {
            "right_skew",
            "high_variability"
        }:

            risks.append({
                "type": warning.get(
                    "type"
                ),
                "severity": "info",
                "confidence": "high",
                "column": warning.get(
                    "column"
                ),
                "message": warning.get(
                    "message",
                    ""
                )
            })

    # --------------------------------------------------------
    # Decreasing Revenue
    # --------------------------------------------------------

    trend = time_analysis.get(
        "revenue_trend"
    )

    if trend:

        adjusted = trend.get(
            "adjusted",
            {}
        )

        if adjusted.get(
            "direction"
        ) == "decreasing":

            risks.append({
                "type": "revenue_decline",
                "severity": "warning",
                "confidence": trend.get(
                    "confidence",
                    "medium"
                ),
                "message": (
                    "The anomaly-adjusted revenue "
                    "baseline is trending downward "
                    "across the observed period."
                )
            })

    # --------------------------------------------------------
    # Concentration
    # --------------------------------------------------------

    if concentration.get(
        "classification"
    ) == "highly_concentrated":

        risks.append({
            "type": "concentration_risk",
            "severity": "warning",
            "confidence": "high",
            "top_product": concentration.get(
                "top_product"
            ),
            "share": concentration.get(
                "top_product_share"
            ),
            "message": (
                "A large share of revenue depends "
                "on a small number of products."
            )
        })

    return risks


# ============================================================
# Executive Summary
# ============================================================

def generate_executive_summary(
    summary,
    adjusted_summary,
    anomaly_analysis,
    insights,
    opportunities,
    risks
):
    """
    Generate a deterministic executive-level summary.
    """
    observed_revenue = safe_float(
        summary.get(
            "total_revenue",
            0
        )
    )

    adjusted_revenue = safe_float(
        adjusted_summary.get(
            "total_revenue",
            0
        )
    )

    anomaly_share = safe_float(
        anomaly_analysis.get(
            "anomalous_revenue_share",
            0
        )
    )

    # --------------------------------------------------------
    # Business Health
    # --------------------------------------------------------

    if anomaly_share >= VERY_HIGH_ANOMALY_REVENUE_SHARE:

        business_health = "critical"

    elif anomaly_share >= HIGH_ANOMALY_REVENUE_SHARE:

        business_health = "caution"

    elif any(
        risk.get("severity") == "critical"
        for risk in risks
    ):

        business_health = "critical"

    elif any(
        risk.get("severity") == "warning"
        for risk in risks
    ):

        business_health = "caution"

    else:

        business_health = "healthy"

    # --------------------------------------------------------
    # Headline
    # --------------------------------------------------------

    if anomaly_share >= VERY_HIGH_ANOMALY_REVENUE_SHARE:

        headline = (
            "Observed business performance is dominated "
            "by anomalous transactions."
        )

    elif anomaly_share >= HIGH_ANOMALY_REVENUE_SHARE:

        headline = (
            "Business metrics require validation because "
            "anomalies materially affect observed revenue."
        )

    elif adjusted_revenue > observed_revenue:

        headline = (
            "The adjusted business baseline is stronger "
            "than the observed dataset suggests."
        )

    else:

        headline = (
            "Business performance can be interpreted "
            "with reasonable confidence."
        )

    # --------------------------------------------------------
    # Key Finding
    # --------------------------------------------------------

    if anomaly_share >= HIGH_ANOMALY_REVENUE_SHARE:

        key_finding = (
            f"{anomaly_share:.2f}% of observed revenue "
            "is associated with anomaly-affected rows."
        )

    elif insights:

        key_finding = insights[0].get(
            "message",
            "No dominant finding identified."
        )

    else:

        key_finding = (
            "No dominant business finding identified."
        )

    # --------------------------------------------------------
    # Primary Opportunity
    # --------------------------------------------------------

    if opportunities:

        primary_opportunity = opportunities[0].get(
            "message",
            ""
        )

    else:

        primary_opportunity = (
            "No significant opportunity identified "
            "from the available signals."
        )

    # --------------------------------------------------------
    # Primary Risk
    # --------------------------------------------------------

    if risks:

        primary_risk = risks[0].get(
            "message",
            ""
        )

    else:

        primary_risk = (
            "No significant risk identified."
        )

    # --------------------------------------------------------
    # Confidence
    # --------------------------------------------------------

    if anomaly_share >= HIGH_ANOMALY_REVENUE_SHARE:

        confidence = "low"

    elif any(
        item.get("confidence") == "low"
        for item in insights
    ):

        confidence = "low"

    elif any(
        item.get("confidence") == "medium"
        for item in insights
    ):

        confidence = "medium"

    else:

        confidence = "high"

    return {
        "headline": headline,
        "business_health": business_health,
        "key_finding": key_finding,
        "primary_opportunity": (
            primary_opportunity
        ),
        "primary_risk": primary_risk,
        "confidence": confidence,
        "observed_revenue": clean_number(
            observed_revenue
        ),
        "adjusted_revenue": clean_number(
            adjusted_revenue
        ),
        "anomalous_revenue_share": round(
            anomaly_share,
            2
        )
    }


# ============================================================
# MAIN INSIGHT ENGINE
# ============================================================

def generate_insights_report(
    df,
    anomaly_summary=None,
    profiler=None,
    anomalies=None
):
    """
    Generate the complete TrendPulse Insight Engine V3 report.

    Parameters
    ----------
    df : pandas.DataFrame
        Cleaned/processed dataset.

    anomaly_summary : dict, optional
        Output summary from anomaly detector.

    profiler : dict, optional
        Output from Profiler V3.

    anomalies : list, optional
        Row-level anomaly records from anomaly detector.

    Returns
    -------
    dict
        Structured TrendPulse V3 business intelligence report.
    """
    if not isinstance(
        df,
        pd.DataFrame
    ):
        raise TypeError(
            "generate_insights_report "
            "expects a pandas DataFrame."
        )

    if df.empty:
        return empty_result()

    # --------------------------------------------------------
    # Prepare Data
    # --------------------------------------------------------

    data = prepare_revenue_data(
        df
    )

    # --------------------------------------------------------
    # Observed Analysis
    # --------------------------------------------------------

    summary = calculate_summary(
        data
    )

    # --------------------------------------------------------
    # Anomaly Analysis
    # --------------------------------------------------------

    anomaly_analysis = analyze_anomalies(
        anomaly_summary,
        anomalies=anomalies,
        df=data
    )

    anomaly_rows = normalize_indices(
        anomaly_analysis.get(
            "row_indices",
            []
        )
    )

    # --------------------------------------------------------
    # Adjusted Summary
    # --------------------------------------------------------

    adjusted_summary = (
        calculate_adjusted_summary(
            data,
            anomaly_rows
        )
    )

    observed_adjusted = (
        build_observed_adjusted_analysis(
            summary,
            adjusted_summary
        )
    )

    # --------------------------------------------------------
    # Adjusted Dataset
    # --------------------------------------------------------

    valid_anomaly_rows = [
        index
        for index in anomaly_rows
        if index in data.index
    ]

    adjusted_data = data.drop(
        labels=valid_anomaly_rows,
        errors="ignore"
    )

    # --------------------------------------------------------
    # Product Analysis
    # --------------------------------------------------------

    product_analysis = analyze_products(
        data
    )

    adjusted_product_analysis = (
        analyze_products(
            adjusted_data
        )
    )

    if product_analysis:

        product_analysis[
            "observed_vs_adjusted"
        ] = {
            "observed": product_analysis.get(
                "products",
                []
            ),
            "adjusted": adjusted_product_analysis.get(
                "products",
                []
            )
        }

    # --------------------------------------------------------
    # Category Analysis
    # --------------------------------------------------------

    category_analysis = analyze_categories(
        data
    )

    adjusted_category_analysis = (
        analyze_categories(
            adjusted_data
        )
    )

    if category_analysis:

        category_analysis[
            "observed_vs_adjusted"
        ] = {
            "observed": category_analysis.get(
                "categories",
                []
            ),
            "adjusted": adjusted_category_analysis.get(
                "categories",
                []
            )
        }

    # --------------------------------------------------------
    # Time Analysis
    # --------------------------------------------------------

    time_analysis = analyze_time(
        data,
        anomalous_indices=anomaly_rows
    )

    # --------------------------------------------------------
    # Concentration
    # --------------------------------------------------------

    concentration = (
        analyze_concentration(
            data
        )
    )

    adjusted_concentration = (
        analyze_concentration(
            adjusted_data
        )
    )

    if concentration:

        concentration[
            "adjusted"
        ] = adjusted_concentration

    # --------------------------------------------------------
    # Profiler
    # --------------------------------------------------------

    profiler_analysis = analyze_profiler(
        profiler
    )

    # --------------------------------------------------------
    # Core Insights
    # --------------------------------------------------------

    insights = generate_insights(
        summary,
        adjusted_summary,
        product_analysis,
        category_analysis,
        time_analysis,
        concentration,
        anomaly_analysis,
        profiler_analysis
    )

    # --------------------------------------------------------
    # Opportunities
    # --------------------------------------------------------

    opportunities = (
        generate_opportunities(
            product_analysis,
            category_analysis,
            time_analysis,
            concentration,
            anomaly_analysis
        )
    )

    # --------------------------------------------------------
    # Risks
    # --------------------------------------------------------

    risks = generate_risks(
        anomaly_analysis,
        profiler_analysis,
        time_analysis,
        concentration
    )

    # --------------------------------------------------------
    # Executive Summary
    # --------------------------------------------------------

    executive_summary = (
        generate_executive_summary(
            summary,
            adjusted_summary,
            anomaly_analysis,
            insights,
            opportunities,
            risks
        )
    )

    # --------------------------------------------------------
    # Final Report
    # --------------------------------------------------------

    return {
        "version": ENGINE_VERSION,

        "executive_summary":
            executive_summary,

        "summary": {
            "observed": summary,
            "adjusted": adjusted_summary,
            "observed_vs_adjusted":
                observed_adjusted
        },

        "insights":
            insights,

        "opportunities":
            opportunities,

        "risks":
            risks,

        "product_analysis":
            product_analysis,

        "category_analysis":
            category_analysis,

        "time_analysis":
            time_analysis,

        "concentration":
            concentration,

        "anomaly_analysis":
            anomaly_analysis,

        "profiler_analysis":
            profiler_analysis
    }


# ============================================================
# BACKWARD-COMPATIBLE ALIAS
# ============================================================

def create_insight_report(
    df,
    anomaly_summary=None,
    profiler=None,
    anomalies=None
):
    """
    Backward-compatible alias for
    generate_insights_report().
    """
    return generate_insights_report(
        df,
        anomaly_summary=anomaly_summary,
        profiler=profiler,
        anomalies=anomalies
    )