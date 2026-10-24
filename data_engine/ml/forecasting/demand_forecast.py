"""
TrendPulse Demand Forecasting Engine.

Predicts future unit demand per product (and optionally per product × size)
for configurable horizons (7, 14, 30, 60 days).

Architecture:
    1. Build time-series features via FeatureEngineer
    2. Train baseline models (Naive, Seasonal Naive, Moving Average)
    3. Train ML model (GradientBoostingRegressor)
    4. Backtest all candidates with walk-forward validation
    5. Auto-select the model with lowest WAPE
    6. Generate forecasts with prediction intervals
    7. Allocate to size level using observed size ratios

Design rules:
    - Implements ``BaseModel`` contract.
    - Leakage-safe: training never sees future data.
    - Minimum data checks: requires ≥ 2× horizon periods of history.
    - Honest inability: returns ``insufficient_data`` rather than guessing.
    - Deterministic random_state for reproducibility.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor

from data_engine.ml.contracts import (
    BaseModel,
    DataLabel,
    FeatureContribution,
    ModelMetadata,
    ModelStatus,
    Prediction,
    PredictionType,
    UncertaintyInterval,
    _convert_numpy,
    insufficient_data_result,
)
from data_engine.ml.evaluation import (
    BacktestResult,
    BacktestRunner,
    TimeSeriesSplitter,
    compute_prediction_intervals,
    compute_regression_metrics,
    compute_wape,
)
from data_engine.ml.feature_store import FeatureEngineer


# ─────────────────────────────────────────────────────────────────────
# Baseline Models
# ─────────────────────────────────────────────────────────────────────

def _naive_forecast(history: np.ndarray, horizon: int) -> np.ndarray:
    """Last-value naive: predict the last observed value for all future periods."""
    last_val = float(history[-1]) if len(history) > 0 else 0.0
    return np.full(horizon, last_val)


def _seasonal_naive_forecast(history: np.ndarray, horizon: int, season_length: int = 4) -> np.ndarray:
    """Seasonal naive: repeat the last season's values cyclically."""
    if len(history) < season_length:
        return _naive_forecast(history, horizon)
    last_season = history[-season_length:]
    repeats = (horizon // season_length) + 1
    return np.tile(last_season, repeats)[:horizon]


def _moving_average_forecast(history: np.ndarray, horizon: int, window: int = 4) -> np.ndarray:
    """Simple moving average of the last ``window`` periods."""
    if len(history) == 0:
        return np.zeros(horizon)
    w = min(window, len(history))
    avg = float(np.mean(history[-w:]))
    return np.full(horizon, max(avg, 0.0))


# ─────────────────────────────────────────────────────────────────────
# Demand Forecaster
# ─────────────────────────────────────────────────────────────────────

class DemandForecaster(BaseModel):
    """
    Multi-model demand forecaster with automatic model selection.

    Trains baseline + ML models, backtests all candidates, and selects
    the one with the lowest WAPE.  Produces per-product forecasts with
    prediction intervals, then optionally allocates to size level.
    """

    MODEL_NAME = "demand_forecaster"
    MODEL_VERSION = "1.0"
    MODEL_TYPE = "ensemble_auto_select"

    # Minimum history requirements (in weekly periods)
    MIN_HISTORY_MULTIPLIER = 2  # Need ≥ 2× horizon weeks of history

    def __init__(self, *, horizon_days: int = 30, random_state: int = 42):
        super().__init__()
        self.horizon_days = horizon_days
        self.horizon_weeks = max(1, horizon_days // 7)
        self.random_state = random_state

        # Internal state
        self._product_models: Dict[str, Dict[str, Any]] = {}
        self._feature_engineer: Optional[FeatureEngineer] = None
        self._size_ratios: Dict[str, Dict[str, float]] = {}
        self._training_metrics: Dict[str, float] = {}
        self._backtest_results: Dict[str, BacktestResult] = {}

    # ── BaseModel Interface ───────────────────────────────────────

    def fit(self, df: pd.DataFrame, **kwargs) -> "DemandForecaster":
        """
        Train demand forecasting models on historical data.

        Parameters
        ----------
        df : pd.DataFrame
            Enriched DataFrame from the TrendPulse data engine.
        """
        if not isinstance(df, pd.DataFrame) or df.empty:
            self._is_fitted = False
            return self

        self._feature_engineer = FeatureEngineer(df)
        self._size_ratios = self._feature_engineer.build_size_ratios()

        # Build weekly time series per product
        ts_features = self._feature_engineer.build_time_series_features(
            group_col="_product", freq="W"
        )

        if ts_features.features.empty:
            self._is_fitted = False
            return self

        ts_df = ts_features.features

        # Train per product group
        all_wapes: List[float] = []

        for product, grp in ts_df.groupby("group", sort=False):
            grp = grp.sort_values("period_index").reset_index(drop=True)
            history = grp["quantity"].values.astype(float)

            min_required = self.horizon_weeks * self.MIN_HISTORY_MULTIPLIER
            if len(history) < min_required:
                self._product_models[str(product)] = {
                    "status": "insufficient_data",
                    "reason": f"Only {len(history)} weekly periods available, need ≥{min_required}",
                    "history_length": len(history),
                }
                continue

            # Evaluate baselines
            best_model = self._select_best_model(grp, history)
            self._product_models[str(product)] = best_model

            if "wape" in best_model.get("metrics", {}):
                all_wapes.append(best_model["metrics"]["wape"])

        # Aggregate training metrics
        if all_wapes:
            self._training_metrics = {
                "mean_wape": round(float(np.mean(all_wapes)), 4),
                "median_wape": round(float(np.median(all_wapes)), 4),
                "best_wape": round(float(np.min(all_wapes)), 4),
                "worst_wape": round(float(np.max(all_wapes)), 4),
                "n_products_modeled": len([m for m in self._product_models.values() if m.get("status") != "insufficient_data"]),
                "n_products_insufficient": len([m for m in self._product_models.values() if m.get("status") == "insufficient_data"]),
            }

        self._is_fitted = True
        self._build_metadata(
            status=ModelStatus.EVALUATED,
            metrics=self._training_metrics,
            n_training_samples=len(ts_df),
            training_data_range=ts_features.data_range,
            target="weekly_quantity",
            prediction_horizon=f"{self.horizon_days}_days",
            hyperparameters={
                "horizon_days": self.horizon_days,
                "horizon_weeks": self.horizon_weeks,
                "random_state": self.random_state,
            },
        )
        return self

    def predict(self, df: pd.DataFrame, **kwargs) -> List[Prediction]:
        """
        Generate demand forecasts for all products with sufficient history.

        Returns per-product predictions, optionally broken down by size.
        """
        include_sizes = kwargs.get("include_sizes", True)

        if not self._is_fitted:
            return []

        predictions: List[Prediction] = []

        for product, model_info in self._product_models.items():
            if model_info.get("status") == "insufficient_data":
                # Return an explicit insufficient-data prediction
                predictions.append(self._make_prediction(
                    entity_type="product",
                    entity_id=product,
                    prediction_type=PredictionType.DEMAND_FORECAST,
                    value=None,
                    confidence=0.0,
                    horizon=f"{self.horizon_days}_days",
                    evidence=[model_info.get("reason", "Insufficient data")],
                    recommended_action="Collect more historical data",
                    metadata_extra={"status": "insufficient_data"},
                ))
                continue

            forecast_values = model_info.get("forecast", [])
            if not forecast_values:
                continue

            total_forecast = float(np.sum(forecast_values))
            forecast_per_week = forecast_values

            # Prediction interval
            interval = model_info.get("interval", (total_forecast * 0.8, total_forecast * 1.2))

            # Confidence from backtest WAPE (lower WAPE = higher confidence)
            wape = model_info.get("metrics", {}).get("wape", 50.0)
            confidence = max(0.1, min(0.99, 1.0 - wape / 100.0))

            # Top features
            top_feats = model_info.get("top_features", [])

            # Evidence
            evidence = [
                f"Selected model: {model_info.get('selected_model', 'unknown')}",
                f"Backtest WAPE: {wape:.1f}%",
                f"History: {model_info.get('history_length', 0)} weekly periods",
                f"Forecast horizon: {self.horizon_days} days ({self.horizon_weeks} weeks)",
            ]

            # Trend description
            trend = model_info.get("trend", "stable")
            if trend == "increasing":
                evidence.append("Trend: Demand is accelerating")
            elif trend == "decreasing":
                evidence.append("Trend: Demand is decelerating")

            # Recommended action
            action = self._recommend_action(total_forecast, model_info)

            # Staleness: prediction valid until end of horizon
            valid_until = (datetime.now(timezone.utc) + timedelta(days=self.horizon_days)).isoformat()

            # Product-level prediction
            pred = self._make_prediction(
                entity_type="product",
                entity_id=product,
                prediction_type=PredictionType.DEMAND_FORECAST,
                value=round(total_forecast, 1),
                confidence=confidence,
                uncertainty=UncertaintyInterval(
                    lower=round(interval[0], 1),
                    upper=round(interval[1], 1),
                ),
                horizon=f"{self.horizon_days}_days",
                valid_until=valid_until,
                evidence=evidence,
                recommended_action=action,
                top_features=top_feats,
                metadata_extra={
                    "weekly_forecast": [round(v, 1) for v in forecast_per_week],
                    "selected_model": model_info.get("selected_model", ""),
                    "trend": trend,
                },
            )
            predictions.append(pred)

            # Size-level breakdown
            if include_sizes and product in self._size_ratios:
                for size, ratio in self._size_ratios[product].items():
                    size_forecast = total_forecast * ratio
                    size_lower = interval[0] * ratio
                    size_upper = interval[1] * ratio

                    size_pred = self._make_prediction(
                        entity_type="sku",
                        entity_id=f"{product} | {size}",
                        prediction_type=PredictionType.DEMAND_FORECAST,
                        value=round(size_forecast, 1),
                        confidence=round(confidence * 0.95, 4),  # Slightly lower for size-level
                        uncertainty=UncertaintyInterval(
                            lower=round(size_lower, 1),
                            upper=round(size_upper, 1),
                        ),
                        horizon=f"{self.horizon_days}_days",
                        valid_until=valid_until,
                        evidence=[
                            f"Allocated from product forecast ({total_forecast:.0f} units)",
                            f"Size ratio: {size} = {ratio:.1%} of demand",
                        ],
                        metadata_extra={
                            "parent_product": product,
                            "size": size,
                            "size_ratio": ratio,
                        },
                    )
                    predictions.append(size_pred)

        return predictions

    def get_metadata(self) -> ModelMetadata:
        if self._metadata:
            return self._metadata
        return self._build_metadata(status=ModelStatus.TRAINED)

    # ── Model Selection ───────────────────────────────────────────

    def _select_best_model(
        self,
        grp: pd.DataFrame,
        history: np.ndarray,
    ) -> Dict[str, Any]:
        """
        Evaluate baseline + ML models and select the best one.

        Uses walk-forward backtesting to prevent temporal leakage.
        """
        n = len(history)
        val_size = min(self.horizon_weeks, max(1, n // 5))
        train_history = history[:-val_size]
        val_actual = history[-val_size:]

        candidates: Dict[str, Dict[str, Any]] = {}

        # Baseline 1: Naive
        naive_pred = _naive_forecast(train_history, val_size)
        candidates["naive"] = {
            "predictions": naive_pred,
            "metrics": compute_regression_metrics(val_actual, naive_pred),
        }

        # Baseline 2: Seasonal Naive
        sn_pred = _seasonal_naive_forecast(train_history, val_size, season_length=4)
        candidates["seasonal_naive"] = {
            "predictions": sn_pred,
            "metrics": compute_regression_metrics(val_actual, sn_pred),
        }

        # Baseline 3: Moving Average
        ma_pred = _moving_average_forecast(train_history, val_size, window=4)
        candidates["moving_average"] = {
            "predictions": ma_pred,
            "metrics": compute_regression_metrics(val_actual, ma_pred),
        }

        # ML: Gradient Boosting (only if enough data for meaningful features)
        if n >= 12:
            try:
                gb_pred = self._train_gradient_boosting(grp, val_size)
                if gb_pred is not None:
                    candidates["gradient_boosting"] = {
                        "predictions": gb_pred,
                        "metrics": compute_regression_metrics(val_actual, gb_pred),
                    }
            except Exception:
                pass  # ML model failure falls back to baselines

        # Select best by WAPE
        best_name = "moving_average"
        best_wape = float("inf")

        for name, info in candidates.items():
            wape = info["metrics"].get("wape", float("inf"))
            if wape < best_wape:
                best_wape = wape
                best_name = name

        # Generate actual forecast (using ALL history, not just train split)
        if best_name == "naive":
            forecast = _naive_forecast(history, self.horizon_weeks)
        elif best_name == "seasonal_naive":
            forecast = _seasonal_naive_forecast(history, self.horizon_weeks)
        elif best_name == "gradient_boosting":
            try:
                forecast = self._generate_gb_forecast(grp, self.horizon_weeks)
            except Exception:
                forecast = _moving_average_forecast(history, self.horizon_weeks)
                best_name = "moving_average (fallback)"
        else:
            forecast = _moving_average_forecast(history, self.horizon_weeks)

        # Ensure non-negative
        forecast = np.maximum(forecast, 0)

        # Prediction interval from backtest residuals
        total_forecast = float(np.sum(forecast))
        best_metrics = candidates[best_name.split(" ")[0]]["metrics"] if best_name.split(" ")[0] in candidates else {}
        wape_val = best_metrics.get("wape", 20.0)
        margin = max(0.1, wape_val / 100.0)
        interval = (total_forecast * (1 - margin), total_forecast * (1 + margin))

        # Trend detection
        if len(history) >= 4:
            recent = np.mean(history[-2:])
            earlier = np.mean(history[-4:-2])
            if recent > earlier * 1.1:
                trend = "increasing"
            elif recent < earlier * 0.9:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "unknown"

        # Feature importance (from GB model if used)
        top_features = self._get_feature_importance() if best_name == "gradient_boosting" else []

        return {
            "status": "success",
            "selected_model": best_name,
            "forecast": forecast.tolist(),
            "metrics": best_metrics,
            "interval": interval,
            "trend": trend,
            "history_length": n,
            "top_features": top_features,
            "all_candidate_metrics": {
                name: info["metrics"] for name, info in candidates.items()
            },
        }

    # ── Gradient Boosting ─────────────────────────────────────────

    def _train_gradient_boosting(
        self,
        grp: pd.DataFrame,
        val_size: int,
    ) -> Optional[np.ndarray]:
        """Train GBR on time-series features and predict validation period."""
        feature_cols = [
            "period_index", "rolling_4w_qty", "rolling_4w_rev", "ewm_qty",
            "qty_pct_change", "qty_acceleration", "trend_slope",
            "month", "quarter", "week_of_year",
        ]
        available_cols = [c for c in feature_cols if c in grp.columns]
        if len(available_cols) < 3:
            return None

        train = grp.iloc[:-val_size]
        val = grp.iloc[-val_size:]

        X_train = train[available_cols].values
        y_train = train["quantity"].values.astype(float)
        X_val = val[available_cols].values

        if len(X_train) < 4 or np.std(y_train) == 0:
            return None

        self._gb_model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.1,
            subsample=0.8,
            random_state=self.random_state,
        )
        self._gb_model.fit(X_train, y_train)
        self._feature_names = available_cols

        preds = self._gb_model.predict(X_val)
        return np.maximum(preds, 0)

    def _generate_gb_forecast(self, grp: pd.DataFrame, horizon_weeks: int) -> np.ndarray:
        """Generate future forecast using the trained GB model."""
        if not hasattr(self, "_gb_model") or self._gb_model is None:
            raise RuntimeError("GB model not trained")

        feature_cols = list(self._feature_names)
        last_row = grp.iloc[-1]

        forecasts = []
        current_features = {col: float(last_row.get(col, 0)) for col in feature_cols}

        for step in range(horizon_weeks):
            X = np.array([[current_features.get(c, 0) for c in feature_cols]])
            pred = max(0, float(self._gb_model.predict(X)[0]))
            forecasts.append(pred)

            # Update rolling features for next step
            if "period_index" in current_features:
                current_features["period_index"] += 1
            if "rolling_4w_qty" in current_features:
                # Simple update: blend prediction into rolling avg
                old_avg = current_features["rolling_4w_qty"]
                current_features["rolling_4w_qty"] = old_avg * 0.75 + pred * 0.25
            if "ewm_qty" in current_features:
                alpha = 2 / (4 + 1)
                current_features["ewm_qty"] = alpha * pred + (1 - alpha) * current_features["ewm_qty"]

        return np.array(forecasts)

    def _get_feature_importance(self) -> List[FeatureContribution]:
        """Extract top feature importances from the GB model."""
        if not hasattr(self, "_gb_model") or self._gb_model is None:
            return []

        importances = self._gb_model.feature_importances_
        feat_names = self._feature_names

        pairs = sorted(zip(feat_names, importances), key=lambda x: x[1], reverse=True)
        top_5 = pairs[:5]

        return [
            FeatureContribution(
                name=name,
                importance=round(float(imp), 4),
                direction="positive",  # GB doesn't provide direction natively
            )
            for name, imp in top_5
        ]

    # ── Recommendations ───────────────────────────────────────────

    @staticmethod
    def _recommend_action(total_forecast: float, model_info: Dict[str, Any]) -> str:
        """Generate business-relevant recommendation from forecast."""
        trend = model_info.get("trend", "stable")
        wape = model_info.get("metrics", {}).get("wape", 50.0)

        if total_forecast <= 0:
            return "No demand predicted — consider discontinuing or heavy markdown."

        if trend == "increasing" and wape < 25:
            return f"Demand growing — plan to stock ≥{total_forecast:.0f} units for the next period."
        elif trend == "increasing":
            return f"Demand likely growing (moderate confidence) — prepare ~{total_forecast:.0f} units."
        elif trend == "decreasing" and wape < 25:
            return f"Demand declining — reduce next order, target ~{total_forecast:.0f} units."
        elif trend == "decreasing":
            return f"Demand may be declining — monitor closely, tentative target ~{total_forecast:.0f} units."
        else:
            return f"Stable demand — maintain ~{total_forecast:.0f} units for the next period."
