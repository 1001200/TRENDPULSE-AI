"""
Adaptive Visual Grammar & Chart Synthesizer.

Inspects data types, cardinality, and statistical distributions to automatically
construct declarative, ready-to-render visual chart specifications (Recharts compatible)
without requiring manual chart selection.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


def synthesize_kpi_cards(
    df: pd.DataFrame,
    num_cols: List[str],
    cat_cols: List[str],
    dt_cols: List[str]
) -> List[Dict[str, Any]]:
    """Synthesize primary KPI cards based on available metrics."""
    cards = []

    # 1. Total Volume / Records
    cards.append({
        "id": "total_records",
        "title": "Total Records Analyzed",
        "value": f"{len(df):,}",
        "subtitle": "Cleaned rows in dataset",
        "badge": "Volume",
        "tone": "neutral",
    })

    # 2. Date Span if available
    if dt_cols:
        dt_col = dt_cols[0]
        valid_dates = pd.to_datetime(df[dt_col]).dropna()
        if not valid_dates.empty:
            min_d = valid_dates.min().strftime("%b %d, %Y")
            max_d = valid_dates.max().strftime("%b %d, %Y")
            days_span = (valid_dates.max() - valid_dates.min()).days
            cards.append({
                "id": "time_span",
                "title": "Temporal Range",
                "value": f"{days_span} Days",
                "subtitle": f"{min_d} - {max_d}",
                "badge": "Coverage",
                "tone": "info",
            })

    # 3. Primary Numeric Metrics (Sum & Average)
    for col in num_cols[:3]:
        series = df[col].dropna()
        if series.empty:
            continue
        total_sum = float(series.sum())
        mean_val = float(series.mean())

        # Format intelligently
        is_large = total_sum > 10000 or mean_val > 100
        formatted_sum = f"{total_sum:,.0f}" if is_large else f"{total_sum:,.2f}"
        formatted_mean = f"{mean_val:,.1f}" if is_large else f"{mean_val:,.2f}"

        col_title = col.replace("_", " ").title()
        cards.append({
            "id": f"kpi_{col}",
            "title": f"Total {col_title}",
            "value": formatted_sum,
            "subtitle": f"Avg: {formatted_mean} / record",
            "badge": "Aggregate",
            "tone": "primary",
        })

    # 4. Top Category if available
    if cat_cols:
        top_cat = cat_cols[0]
        top_val = df[top_cat].value_counts().head(1)
        if not top_val.empty:
            val_name = str(top_val.index[0])
            val_pct = round((top_val.values[0] / len(df)) * 100, 1)
            cards.append({
                "id": "top_category",
                "title": f"Dominant {top_cat.replace('_', ' ').title()}",
                "value": val_name[:20],
                "subtitle": f"{val_pct}% of total records",
                "badge": "Concentration",
                "tone": "success",
            })

    return cards[:4]


def synthesize_time_series_chart(
    df: pd.DataFrame,
    dt_col: str,
    num_col: str
) -> Optional[Dict[str, Any]]:
    """Synthesize temporal trend chart (Area/Line chart)."""
    sub = df[[dt_col, num_col]].dropna().copy()
    if len(sub) < 3:
        return None

    sub[dt_col] = pd.to_datetime(sub[dt_col], errors="coerce")
    sub = sub.dropna().sort_values(dt_col)
    if sub.empty:
        return None

    span_days = (sub[dt_col].max() - sub[dt_col].min()).days

    # Choose aggregation frequency
    if span_days > 180:
        sub["period"] = sub[dt_col].dt.to_period("M").dt.to_timestamp()
    elif span_days > 30:
        sub["period"] = sub[dt_col].dt.to_period("W").dt.to_timestamp()
    else:
        sub["period"] = sub[dt_col].dt.to_period("D").dt.to_timestamp()

    grouped = sub.groupby("period")[num_col].agg(["sum", "mean", "count"]).reset_index()
    if len(grouped) < 2:
        return None

    data_points = []
    for _, row in grouped.iterrows():
        data_points.append({
            "period": row["period"].strftime("%Y-%m-%d"),
            "display_date": row["period"].strftime("%b %d"),
            "total": round(float(row["sum"]), 2),
            "average": round(float(row["mean"]), 2),
            "count": int(row["count"]),
        })

    metric_name = num_col.replace("_", " ").title()
    return {
        "chart_type": "area",
        "id": "time_trend_chart",
        "title": f"Temporal Velocity: {metric_name} Over Time",
        "subtitle": f"Automated time-series aggregation of {metric_name} indexed by {dt_col}",
        "x_key": "display_date",
        "y_key": "total",
        "y_label": f"Total {metric_name}",
        "data": data_points,
    }


def synthesize_categorical_pareto_chart(
    df: pd.DataFrame,
    cat_col: str,
    num_col: Optional[str]
) -> Optional[Dict[str, Any]]:
    """Synthesize category breakdown (Sorted Pareto Bar Chart)."""
    if cat_col not in df.columns:
        return None

    if num_col and num_col in df.columns:
        agg = df.groupby(cat_col)[num_col].agg(["sum", "count"]).reset_index()
        agg = agg.sort_values(by="sum", ascending=False).head(10)
        val_key = "sum"
        metric_label = f"Total {num_col.replace('_', ' ').title()}"
    else:
        agg = df[cat_col].value_counts().reset_index().head(10)
        agg.columns = [cat_col, "count"]
        val_key = "count"
        metric_label = "Record Count"

    data_points = []
    for _, row in agg.iterrows():
        data_points.append({
            "category": str(row[cat_col])[:22],
            "value": round(float(row[val_key]), 2),
            "count": int(row["count"]) if "count" in row else 1,
        })

    cat_name = cat_col.replace("_", " ").title()
    return {
        "chart_type": "bar",
        "id": "category_distribution_chart",
        "title": f"Distribution by {cat_name}",
        "subtitle": f"Comparative breakdown across top {cat_name} segments",
        "x_key": "category",
        "y_key": "value",
        "y_label": metric_label,
        "data": data_points,
    }


def synthesize_correlation_scatter(
    df: pd.DataFrame,
    col_a: str,
    col_b: str,
    r_val: float
) -> Optional[Dict[str, Any]]:
    """Synthesize scatter plot for top correlated pair."""
    sub = df[[col_a, col_b]].dropna()
    if len(sub) < 5:
        return None

    sample_size = min(300, len(sub))
    sampled = sub.sample(sample_size, random_state=42)

    data_points = []
    for _, row in sampled.iterrows():
        data_points.append({
            "x": round(float(row[col_a]), 2),
            "y": round(float(row[col_b]), 2),
        })

    return {
        "chart_type": "scatter",
        "id": "correlation_scatter_chart",
        "title": f"Coupling: {col_a.replace('_', ' ').title()} vs {col_b.replace('_', ' ').title()}",
        "subtitle": f"Pearson coefficient r = {r_val:.2f} ({'Positive' if r_val > 0 else 'Negative'} association)",
        "x_key": "x",
        "y_key": "y",
        "x_label": col_a.replace("_", " ").title(),
        "y_label": col_b.replace("_", " ").title(),
        "r_value": r_val,
        "data": data_points,
    }


def synthesize_histogram(
    df: pd.DataFrame,
    num_col: str
) -> Optional[Dict[str, Any]]:
    """Synthesize frequency distribution histogram."""
    series = df[num_col].dropna()
    if len(series) < 10 or series.nunique() < 4:
        return None

    counts, bin_edges = np.histogram(series, bins=8)
    data_points = []
    for i in range(len(counts)):
        bin_label = f"{bin_edges[i]:,.0f}-{bin_edges[i+1]:,.0f}" if bin_edges[i+1] > 10 else f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}"
        data_points.append({
            "bin": bin_label,
            "count": int(counts[i]),
        })

    return {
        "chart_type": "histogram",
        "id": "histogram_chart",
        "title": f"Distribution Profile: {num_col.replace('_', ' ').title()}",
        "subtitle": f"Frequency distribution across 8 computed histogram bins",
        "x_key": "bin",
        "y_key": "count",
        "y_label": "Frequency",
        "data": data_points,
    }


def synthesize_dashboard(
    df: pd.DataFrame,
    num_cols: List[str],
    cat_cols: List[str],
    dt_cols: List[str],
    top_correlation: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Construct complete, adaptive visual dashboard blueprint.
    """
    kpis = synthesize_kpi_cards(df, num_cols, cat_cols, dt_cols)
    charts = []

    # 1. Time Series Chart (if date exists and numeric exists)
    if dt_cols and num_cols:
        ts_chart = synthesize_time_series_chart(df, dt_cols[0], num_cols[0])
        if ts_chart:
            charts.append(ts_chart)

    # 2. Categorical Pareto Bar
    if cat_cols:
        primary_num = num_cols[0] if num_cols else None
        bar_chart = synthesize_categorical_pareto_chart(df, cat_cols[0], primary_num)
        if bar_chart:
            charts.append(bar_chart)

    # 3. Correlation Scatter (if correlated pair provided)
    if top_correlation:
        scatter = synthesize_correlation_scatter(
            df,
            top_correlation["column_a"],
            top_correlation["column_b"],
            top_correlation["r_value"]
        )
        if scatter:
            charts.append(scatter)

    # 4. Secondary Categorical or Distribution Chart
    if len(cat_cols) > 1:
        sec_num = num_cols[1] if len(num_cols) > 1 else (num_cols[0] if num_cols else None)
        sec_bar = synthesize_categorical_pareto_chart(df, cat_cols[1], sec_num)
        if sec_bar:
            charts.append(sec_bar)
    elif num_cols and (not charts or charts[-1]["chart_type"] != "histogram"):
        hist = synthesize_histogram(df, num_cols[0])
        if hist:
            charts.append(hist)

    return {
        "kpi_cards": kpis,
        "charts": charts,
    }
