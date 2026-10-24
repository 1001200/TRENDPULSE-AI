"""
TrendPulse ML Evaluation Framework.

Provides time-series-aware validation splitting, backtesting, and
metric computation for all ML models.

Design rules:
    - Time-series splits NEVER leak future data into training.
    - Backtesting uses expanding-window walk-forward validation.
    - Metrics handle edge cases (near-zero actuals in MAPE, etc.).
    - Deterministic; zero side-effects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd


# ─────────────────────────────────────────────────────────────────────
# Time-Series Splitter
# ─────────────────────────────────────────────────────────────────────

@dataclass
class SplitFold:
    """One train/validation fold for time-series cross-validation."""
    fold_index: int
    train_start: str
    train_end: str
    val_start: str
    val_end: str
    train_indices: List[int] = field(default_factory=list)
    val_indices: List[int] = field(default_factory=list)


class TimeSeriesSplitter:
    """
    Walk-forward expanding-window time-series cross-validation.

    Guarantees that the training set always precedes the validation set
    in time, preventing temporal data leakage.

    Parameters
    ----------
    n_splits : int
        Number of validation folds.
    min_train_periods : int
        Minimum number of time periods in the training set.
    val_periods : int
        Number of time periods in each validation fold.
    """

    def __init__(
        self,
        n_splits: int = 3,
        min_train_periods: int = 8,
        val_periods: int = 4,
    ):
        self.n_splits = n_splits
        self.min_train_periods = min_train_periods
        self.val_periods = val_periods

    def split(
        self,
        dates: pd.Series,
        freq: str = "W",
    ) -> List[SplitFold]:
        """
        Generate time-aware train/validation split indices.

        Parameters
        ----------
        dates : pd.Series
            Datetime series (must be parseable).
        freq : str
            Resampling frequency for period boundaries.

        Returns
        -------
        List[SplitFold]
            Ordered folds with train/validation index lists.
        """
        dt = pd.Series(pd.to_datetime(dates, errors="coerce"))
        valid_mask = dt.notna()
        if valid_mask.sum() < self.min_train_periods + self.val_periods:
            return []

        # Get unique sorted periods
        period_index = pd.PeriodIndex(dt[valid_mask].dt.to_period(freq).unique()).sort_values()
        n_periods = len(period_index)

        total_needed = self.min_train_periods + self.val_periods * self.n_splits
        if n_periods < self.min_train_periods + self.val_periods:
            return []

        # Calculate step size between folds
        available_for_validation = n_periods - self.min_train_periods
        step = max(1, available_for_validation // self.n_splits)

        folds: List[SplitFold] = []
        for i in range(self.n_splits):
            train_end_idx = self.min_train_periods + i * step - 1
            val_start_idx = train_end_idx + 1
            val_end_idx = min(val_start_idx + self.val_periods - 1, n_periods - 1)

            if val_start_idx >= n_periods:
                break

            train_periods = set(period_index[:train_end_idx + 1])
            val_periods_set = set(period_index[val_start_idx:val_end_idx + 1])

            dt_periods = dt[valid_mask].dt.to_period(freq)
            train_idx = dt.index[valid_mask][dt_periods.isin(train_periods)].tolist()
            val_idx = dt.index[valid_mask][dt_periods.isin(val_periods_set)].tolist()

            if not train_idx or not val_idx:
                continue

            fold = SplitFold(
                fold_index=i,
                train_start=str(period_index[0].start_time.date()),
                train_end=str(period_index[train_end_idx].end_time.date()),
                val_start=str(period_index[val_start_idx].start_time.date()),
                val_end=str(period_index[val_end_idx].end_time.date()),
                train_indices=train_idx,
                val_indices=val_idx,
            )
            folds.append(fold)

        return folds


# ─────────────────────────────────────────────────────────────────────
# Metric Functions
# ─────────────────────────────────────────────────────────────────────

def compute_mae(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Mean Absolute Error."""
    if len(actual) == 0:
        return 0.0
    return float(np.mean(np.abs(actual - predicted)))


def compute_rmse(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Root Mean Squared Error."""
    if len(actual) == 0:
        return 0.0
    return float(np.sqrt(np.mean((actual - predicted) ** 2)))


def compute_mape(actual: np.ndarray, predicted: np.ndarray, epsilon: float = 1.0) -> float:
    """
    Mean Absolute Percentage Error (safe).

    Uses epsilon floor to prevent division by zero when actuals are small.
    """
    if len(actual) == 0:
        return 0.0
    safe_actual = np.maximum(np.abs(actual), epsilon)
    return float(np.mean(np.abs((actual - predicted) / safe_actual)) * 100)


def compute_smape(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Symmetric Mean Absolute Percentage Error."""
    if len(actual) == 0:
        return 0.0
    denom = np.abs(actual) + np.abs(predicted)
    denom = np.where(denom == 0, 1.0, denom)
    return float(np.mean(2.0 * np.abs(actual - predicted) / denom) * 100)


def compute_wape(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Weighted Absolute Percentage Error — robust to near-zero actuals."""
    if len(actual) == 0:
        return 0.0
    total_actual = np.sum(np.abs(actual))
    if total_actual == 0:
        return 0.0
    return float(np.sum(np.abs(actual - predicted)) / total_actual * 100)


def compute_regression_metrics(
    actual: np.ndarray,
    predicted: np.ndarray,
) -> Dict[str, float]:
    """Compute all regression metrics at once."""
    a = np.asarray(actual, dtype=float)
    p = np.asarray(predicted, dtype=float)
    return {
        "mae": round(compute_mae(a, p), 4),
        "rmse": round(compute_rmse(a, p), 4),
        "mape": round(compute_mape(a, p), 4),
        "smape": round(compute_smape(a, p), 4),
        "wape": round(compute_wape(a, p), 4),
    }


def compute_classification_metrics(
    actual: np.ndarray,
    predicted: np.ndarray,
    labels: Optional[List[str]] = None,
) -> Dict[str, float]:
    """
    Compute accuracy, macro precision, macro recall, macro F1.
    Uses manual calculation to avoid sklearn import overhead for simple metrics.
    """
    a = np.asarray(actual)
    p = np.asarray(predicted)
    n = len(a)
    if n == 0:
        return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0}

    accuracy = float(np.mean(a == p))

    unique_labels = labels or list(set(a) | set(p))
    precisions, recalls = [], []

    for label in unique_labels:
        tp = int(np.sum((p == label) & (a == label)))
        fp = int(np.sum((p == label) & (a != label)))
        fn = int(np.sum((p != label) & (a == label)))

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        precisions.append(prec)
        recalls.append(rec)

    macro_prec = float(np.mean(precisions))
    macro_rec = float(np.mean(recalls))
    f1 = (2 * macro_prec * macro_rec / (macro_prec + macro_rec)) if (macro_prec + macro_rec) > 0 else 0.0

    return {
        "accuracy": round(accuracy, 4),
        "precision": round(macro_prec, 4),
        "recall": round(macro_rec, 4),
        "f1": round(f1, 4),
    }


# ─────────────────────────────────────────────────────────────────────
# Backtest Runner
# ─────────────────────────────────────────────────────────────────────

@dataclass
class BacktestResult:
    """Result of a backtest run across multiple folds."""
    model_name: str
    n_folds: int
    fold_metrics: List[Dict[str, float]]
    aggregate_metrics: Dict[str, float]
    actuals: List[float] = field(default_factory=list)
    predictions: List[float] = field(default_factory=list)


class BacktestRunner:
    """
    Runs walk-forward backtesting for forecasting models.

    Trains on expanding historical windows, predicts into the future,
    and accumulates accuracy metrics across all folds.
    """

    def __init__(self, splitter: Optional[TimeSeriesSplitter] = None):
        self.splitter = splitter or TimeSeriesSplitter()

    def run(
        self,
        df: pd.DataFrame,
        date_col: str,
        target_col: str,
        train_fn: Callable,
        predict_fn: Callable,
        group_col: Optional[str] = None,
    ) -> BacktestResult:
        """
        Execute walk-forward backtesting.

        Parameters
        ----------
        df : pd.DataFrame
            Full dataset.
        date_col : str
            Name of the datetime column.
        target_col : str
            Name of the target variable column.
        train_fn : Callable
            ``fn(train_df) -> model`` — trains and returns a model.
        predict_fn : Callable
            ``fn(model, val_df) -> np.ndarray`` — returns predictions.
        group_col : str, optional
            If provided, backtest is run per group and results are aggregated.

        Returns
        -------
        BacktestResult
        """
        folds = self.splitter.split(df[date_col])
        if not folds:
            return BacktestResult(
                model_name="backtest",
                n_folds=0,
                fold_metrics=[],
                aggregate_metrics={"status": "insufficient_data_for_backtesting"},
            )

        all_actuals: List[float] = []
        all_preds: List[float] = []
        fold_metrics: List[Dict[str, float]] = []

        for fold in folds:
            train_df = df.iloc[fold.train_indices]
            val_df = df.iloc[fold.val_indices]

            if train_df.empty or val_df.empty:
                continue

            try:
                model = train_fn(train_df)
                preds = predict_fn(model, val_df)
                actuals = val_df[target_col].values.astype(float)

                metrics = compute_regression_metrics(actuals, preds)
                fold_metrics.append(metrics)

                all_actuals.extend(actuals.tolist())
                all_preds.extend(preds.tolist())
            except Exception:
                continue

        if all_actuals and all_preds:
            agg = compute_regression_metrics(
                np.array(all_actuals), np.array(all_preds)
            )
        else:
            agg = {}

        return BacktestResult(
            model_name="backtest",
            n_folds=len(fold_metrics),
            fold_metrics=fold_metrics,
            aggregate_metrics=agg,
            actuals=all_actuals,
            predictions=all_preds,
        )


# ─────────────────────────────────────────────────────────────────────
# Prediction Interval Estimator
# ─────────────────────────────────────────────────────────────────────

def compute_prediction_intervals(
    backtest_result: BacktestResult,
    point_forecast: float,
    confidence: float = 0.9,
) -> Tuple[float, float]:
    """
    Compute prediction interval from backtest residuals.

    Uses empirical quantiles of backtest errors to produce
    prediction intervals without distributional assumptions.

    Parameters
    ----------
    backtest_result : BacktestResult
        Result of walk-forward backtesting.
    point_forecast : float
        The point forecast to build intervals around.
    confidence : float
        Confidence level (e.g. 0.9 for 90% interval).

    Returns
    -------
    (lower, upper) : Tuple[float, float]
    """
    if not backtest_result.actuals or not backtest_result.predictions:
        # No backtest data — use ±20% as conservative default
        return (point_forecast * 0.8, point_forecast * 1.2)

    residuals = np.array(backtest_result.actuals) - np.array(backtest_result.predictions)
    alpha = (1 - confidence) / 2
    lower_q = float(np.quantile(residuals, alpha))
    upper_q = float(np.quantile(residuals, 1 - alpha))

    lower = max(0, point_forecast + lower_q)
    upper = point_forecast + upper_q

    return (round(lower, 2), round(upper, 2))
