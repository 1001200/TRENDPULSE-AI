"""
TrendPulse Sales Forecasting Service.
Implements explainable time-series forecasting (SMA, Holt's Exponential Smoothing, Naive persistence)
with chronological holdout backtesting, MAE / WAPE evaluation, and prediction intervals.
"""

import math
from typing import Dict, Any, List
from datetime import datetime


def _format_inr(val: float) -> str:
    """Format a number into Indian Rupee string."""
    try:
        val_int = int(round(val))
        is_neg = val_int < 0
        val_int = abs(val_int)
        s = str(val_int)
        if len(s) <= 3:
            res = s
        else:
            last3 = s[-3:]
            rest = s[:-3]
            groups = []
            while len(rest) > 2:
                groups.insert(0, rest[-2:])
                rest = rest[:-2]
            if rest:
                groups.insert(0, rest)
            res = ",".join(groups) + "," + last3
        prefix = "-₹" if is_neg else "₹"
        return f"{prefix}{res}"
    except Exception:
        return f"₹{val:,.0f}"


def forecast_monthly_sales(monthly_sales: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Given a list of monthly sales records in chronological order:
    [{ "month": "June 2026", "revenue": 7394.0, "units": 6, "orders": 6 }, ...]

    Returns a structured forecast for the next calendar month, including:
    - Target forecast period
    - Point forecast (expected revenue)
    - 80% prediction interval [low, high]
    - Evaluation against naive baseline on historical holdout
    - Historical actuals and forecast points for charting
    """
    if not monthly_sales or len(monthly_sales) < 3:
        return {
            "sufficient_data": False,
            "message": "More consistent sales history is needed to generate a reliable forecast. A minimum of 3 recorded months is required.",
            "forecast_period": None,
            "forecasted_revenue": 0.0,
            "forecasted_revenue_formatted": "₹0",
            "interval_low": 0.0,
            "interval_high": 0.0,
            "model_name": "Insufficient History",
            "historical_points": monthly_sales,
            "forecast_points": []
        }

    revenues = [float(m.get("revenue", 0.0)) for m in monthly_sales]
    month_names = [m.get("month", "") for m in monthly_sales]

    n = len(revenues)

    # 1. Chronological Holdout Backtesting (Hold out the most recent month)
    # Train on months 0 .. n-2, evaluate on month n-1
    train_rev = revenues[:-1]
    actual_test = revenues[-1]
    test_month_name = month_names[-1]

    # Baseline A: Naive Persistence (last observed month before holdout)
    naive_pred = train_rev[-1]
    naive_mae = abs(actual_test - naive_pred)

    # Baseline B: Simple Moving Average (window = min(3, len(train_rev)))
    w = min(3, len(train_rev))
    sma_pred = sum(train_rev[-w:]) / w
    sma_mae = abs(actual_test - sma_pred)

    # Baseline C: Holt's Linear Exponential Smoothing
    alpha = 0.4
    beta = 0.3
    level = train_rev[0]
    trend = train_rev[1] - train_rev[0] if len(train_rev) > 1 else 0.0
    for val in train_rev[1:]:
        prev_level = level
        level = alpha * val + (1 - alpha) * (level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend
    holt_pred = max(0.0, level + trend)
    holt_mae = abs(actual_test - holt_pred)

    # Model Selection based on holdout MAE
    candidates = [
        ("Simple Moving Average (3-Month Window)", sma_pred, sma_mae),
        ("Holt's Linear Exponential Smoothing", holt_pred, holt_mae),
        ("Naive Persistence Baseline", naive_pred, naive_mae)
    ]
    candidates.sort(key=lambda x: x[2])
    best_model_name, best_holdout_pred, best_holdout_mae = candidates[0]

    # Calculate holdout WAPE for best model
    holdout_wape = round((best_holdout_mae / max(1.0, actual_test)) * 100, 1)

    # 2. Produce Next Month Forecast using all available data
    # Parse last month to determine next calendar month
    last_m_str = month_names[-1]
    next_month_name = "Next Month"
    try:
        # e.g. "September 2026"
        dt = datetime.strptime(last_m_str, "%B %Y")
        if dt.month == 12:
            next_dt = datetime(dt.year + 1, 1, 1)
        else:
            next_dt = datetime(dt.year, dt.month + 1, 1)
        next_month_name = next_dt.strftime("%B %Y")
    except Exception:
        next_month_name = "Next Month"

    # Compute forecast with chosen best model architecture
    if "Moving Average" in best_model_name:
        w_all = min(3, len(revenues))
        forecast_rev = sum(revenues[-w_all:]) / w_all
    elif "Holt" in best_model_name:
        level = revenues[0]
        trend = revenues[1] - revenues[0] if len(revenues) > 1 else 0.0
        for val in revenues[1:]:
            prev_level = level
            level = alpha * val + (1 - alpha) * (level + trend)
            trend = beta * (level - prev_level) + (1 - beta) * trend
        forecast_rev = max(0.0, level + trend)
    else:
        forecast_rev = revenues[-1]

    # 3. Estimate Uncertainty / Prediction Interval
    # Residuals from one-step-ahead rolling predictions
    residuals = []
    for i in range(1, len(revenues)):
        step_sma = sum(revenues[max(0, i - 3):i]) / max(1, min(i, 3))
        residuals.append(revenues[i] - step_sma)

    std_err = math.sqrt(sum(r**2 for r in residuals) / max(1, len(residuals)))
    # 80% confidence interval multiplier (~1.28)
    margin = 1.28 * std_err
    interval_low = max(0.0, round(forecast_rev - margin, 0))
    interval_high = round(forecast_rev + margin, 0)
    point_forecast = round(forecast_rev, 0)

    # Chart data: historical actuals + connected forecast
    historical_points = [
        {
            "month": m["month"],
            "revenue": round(m["revenue"], 0),
            "revenue_formatted": _format_inr(m["revenue"]),
            "is_forecast": False
        }
        for m in monthly_sales
    ]

    forecast_points = [
        {
            "month": next_month_name,
            "revenue": point_forecast,
            "revenue_formatted": _format_inr(point_forecast),
            "interval_low": interval_low,
            "interval_low_formatted": _format_inr(interval_low),
            "interval_high": interval_high,
            "interval_high_formatted": _format_inr(interval_high),
            "is_forecast": True
        }
    ]

    return {
        "sufficient_data": True,
        "forecast_period": next_month_name,
        "forecasted_revenue": point_forecast,
        "forecasted_revenue_formatted": _format_inr(point_forecast),
        "interval_low": interval_low,
        "interval_low_formatted": _format_inr(interval_low),
        "interval_high": interval_high,
        "interval_high_formatted": _format_inr(interval_high),
        "model_name": best_model_name,
        "evaluation": {
            "holdout_month": test_month_name,
            "actual_holdout_revenue": actual_test,
            "actual_holdout_revenue_formatted": _format_inr(actual_test),
            "holdout_mae": round(best_holdout_mae, 0),
            "holdout_mae_formatted": _format_inr(best_holdout_mae),
            "holdout_wape_pct": holdout_wape,
            "naive_mae": round(naive_mae, 0),
            "naive_mae_formatted": _format_inr(naive_mae),
            "baseline_improvement_pct": round(max(0.0, (naive_mae - best_holdout_mae) / max(1.0, naive_mae)) * 100, 1)
        },
        "training_records_count": len(monthly_sales),
        "historical_points": historical_points,
        "forecast_points": forecast_points,
        "note": "Mathematical estimate generated from your historical sales trajectory. Not guaranteed income."
    }
