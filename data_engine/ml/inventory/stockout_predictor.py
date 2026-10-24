"""
TrendPulse Stockout & Inventory Prediction Engine.

Moves inventory intelligence from descriptive (what happened) to predictive
(what will happen) by combining demand forecasts with current inventory state.

Predicts per SKU:
    - Stockout probability (0–100%)
    - Expected stockout date
    - Inventory depletion curve
    - Recommended replenishment quantity

Architecture:
    - Consumes demand forecast output + current inventory from the data engine.
    - NOT a standalone ML model — it's a simulation that uses the demand
      forecaster's output as input (labeled SIMULATED, not PREDICTED).
    - Falls back gracefully when inventory data is missing.

Design rules:
    - Implements ``BaseModel`` contract.
    - Labels outputs as ``SIMULATED`` (inventory projection ≠ ML prediction).
    - Requires inventory (stock) data to function.
    - Returns ``insufficient_data`` if stock column is absent.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

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
from data_engine.ml.feature_store import FeatureEngineer


# ─────────────────────────────────────────────────────────────────────
# Risk Thresholds
# ─────────────────────────────────────────────────────────────────────

STOCKOUT_HIGH = 0.75
STOCKOUT_MEDIUM = 0.40
OVERSTOCK_THRESHOLD_WOS = 12  # Weeks of supply


# ─────────────────────────────────────────────────────────────────────
# Stockout Predictor
# ─────────────────────────────────────────────────────────────────────

class StockoutPredictor(BaseModel):
    """
    Predicts stockout risk by simulating inventory depletion against
    demand forecasts.

    This is a simulation model, not a statistical ML model.
    Outputs are labeled ``SIMULATED`` to distinguish from ML predictions.
    """

    MODEL_NAME = "stockout_predictor"
    MODEL_VERSION = "1.0"
    MODEL_TYPE = "simulation"

    def __init__(
        self,
        *,
        horizon_days: int = 30,
        safety_stock_factor: float = 1.2,
        lead_time_days: int = 14,
    ):
        super().__init__()
        self.horizon_days = horizon_days
        self.horizon_weeks = max(1, horizon_days // 7)
        self.safety_stock_factor = safety_stock_factor
        self.lead_time_days = lead_time_days

        # Internal state
        self._inventory_state: Dict[str, float] = {}
        self._demand_forecasts: Dict[str, Dict[str, Any]] = {}
        self._sku_features: Optional[pd.DataFrame] = None

    # ── BaseModel Interface ───────────────────────────────────────

    def fit(self, df: pd.DataFrame, **kwargs) -> "StockoutPredictor":
        """
        Prepare inventory state and integrate demand forecasts.

        Parameters
        ----------
        df : pd.DataFrame
            Enriched DataFrame from the data engine.
        demand_predictions : List[Prediction], optional
            Pre-computed demand forecasts from DemandForecaster.
        """
        if not isinstance(df, pd.DataFrame) or df.empty:
            self._is_fitted = False
            return self

        data = df.copy()

        # Check if stock data exists
        has_stock = "stock" in data.columns
        if has_stock:
            data["_stock"] = pd.to_numeric(data["stock"], errors="coerce").fillna(0)
        else:
            data["_stock"] = 0.0

        # Parse dates and quantities
        if "date" in data.columns:
            data["_date"] = pd.to_datetime(data["date"], errors="coerce")
        else:
            data["_date"] = pd.NaT

        data["_qty"] = pd.to_numeric(data.get("quantity", 0), errors="coerce").fillna(0)

        if "product" in data.columns:
            data["_product"] = data["product"].astype(str).str.strip()
        else:
            data["_product"] = "unknown"

        # Build current inventory state (latest stock per product)
        if has_stock and data["_date"].notna().any():
            latest = data.sort_values("_date").groupby("_product").last()
            self._inventory_state = latest["_stock"].to_dict()
        elif has_stock:
            avg_stock = data.groupby("_product")["_stock"].mean()
            self._inventory_state = avg_stock.to_dict()
        else:
            self._inventory_state = {}

        # Build SKU-level sales velocity from FeatureEngineer
        fe = FeatureEngineer(df)
        sku_fs = fe.build_sku_features()
        if not sku_fs.features.empty:
            self._sku_features = sku_fs.features.copy()

        # Integrate demand forecasts if provided
        demand_predictions: List[Prediction] = kwargs.get("demand_predictions", [])
        for pred in demand_predictions:
            if pred.prediction_type == PredictionType.DEMAND_FORECAST and pred.value is not None:
                self._demand_forecasts[pred.entity_id] = {
                    "forecast": float(pred.value),
                    "lower": pred.uncertainty.lower if pred.uncertainty else float(pred.value) * 0.8,
                    "upper": pred.uncertainty.upper if pred.uncertainty else float(pred.value) * 1.2,
                    "confidence": pred.confidence,
                }

        self._is_fitted = True
        self._build_metadata(
            status=ModelStatus.EVALUATED,
            metrics={
                "n_products_with_inventory": len(self._inventory_state),
                "n_products_with_forecast": len(self._demand_forecasts),
            },
            n_training_samples=len(df),
            target="stockout_probability",
            prediction_horizon=f"{self.horizon_days}_days",
            hyperparameters={
                "horizon_days": self.horizon_days,
                "safety_stock_factor": self.safety_stock_factor,
                "lead_time_days": self.lead_time_days,
            },
        )
        return self

    def predict(self, df: pd.DataFrame, **kwargs) -> List[Prediction]:
        """
        Generate stockout predictions for all products with inventory data.
        """
        if not self._is_fitted:
            return []

        if not self._inventory_state:
            return [self._make_prediction(
                entity_type="system",
                entity_id="all",
                prediction_type=PredictionType.STOCKOUT_PROBABILITY,
                value=None,
                confidence=0.0,
                evidence=["No inventory/stock data available in dataset"],
                recommended_action="Include a 'stock' column in your data for inventory predictions.",
                metadata_extra={"status": "insufficient_data"},
            )]

        predictions: List[Prediction] = []

        for product, current_stock in self._inventory_state.items():
            current_stock = float(current_stock)
            if current_stock < 0:
                current_stock = 0

            # Get demand forecast
            forecast_info = self._demand_forecasts.get(product, {})

            # If no ML forecast, estimate from velocity
            if not forecast_info and self._sku_features is not None:
                velocity_row = self._sku_features[
                    self._sku_features["product"] == product
                ]
                if not velocity_row.empty:
                    vel = float(velocity_row.iloc[0].get("velocity_units_per_week", 0))
                    forecast_demand = vel * self.horizon_weeks
                    forecast_info = {
                        "forecast": forecast_demand,
                        "lower": forecast_demand * 0.8,
                        "upper": forecast_demand * 1.2,
                        "confidence": 0.5,  # Lower confidence for velocity-based estimate
                        "source": "velocity_estimate",
                    }

            if not forecast_info:
                continue

            forecast_demand = float(forecast_info["forecast"])
            forecast_lower = float(forecast_info.get("lower", forecast_demand * 0.8))
            forecast_upper = float(forecast_info.get("upper", forecast_demand * 1.2))
            forecast_confidence = float(forecast_info.get("confidence", 0.5))

            # Simulate inventory depletion
            sim = self._simulate_depletion(
                current_stock=current_stock,
                forecast_demand=forecast_demand,
                forecast_upper=forecast_upper,
            )

            stockout_prob = sim["stockout_probability"]
            expected_date = sim["expected_stockout_date"]
            depletion_curve = sim["depletion_curve"]

            # Recommended replenishment quantity
            replenishment = self._calculate_replenishment(
                current_stock=current_stock,
                forecast_demand=forecast_upper,  # Use upper bound for safety
            )

            # Confidence: blend forecast confidence with inventory data quality
            confidence = forecast_confidence * 0.9  # Slightly discount for simulation layer

            # Evidence
            evidence = [
                f"Current stock: {current_stock:.0f} units",
                f"Forecasted demand ({self.horizon_days}d): {forecast_demand:.0f} units",
                f"Demand range: {forecast_lower:.0f} – {forecast_upper:.0f} units",
            ]

            if stockout_prob >= STOCKOUT_HIGH:
                evidence.append(f"⚠️ HIGH stockout risk ({stockout_prob:.0%})")
            elif stockout_prob >= STOCKOUT_MEDIUM:
                evidence.append(f"⚡ MEDIUM stockout risk ({stockout_prob:.0%})")
            else:
                evidence.append(f"✅ LOW stockout risk ({stockout_prob:.0%})")

            if expected_date:
                evidence.append(f"Expected stockout: {expected_date}")

            # Check overstock
            wos = (current_stock / (forecast_demand / self.horizon_weeks * 7)) if forecast_demand > 0 else float("inf")
            if wos > OVERSTOCK_THRESHOLD_WOS:
                evidence.append(f"⚠️ OVERSTOCK: {wos:.0f} weeks of supply")

            # Recommended action
            action = self._recommend_action(
                stockout_prob=stockout_prob,
                current_stock=current_stock,
                forecast_demand=forecast_demand,
                replenishment=replenishment,
                wos=wos,
            )

            # Staleness
            valid_until = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

            pred = Prediction(
                prediction_id="",
                model_name=self.MODEL_NAME,
                model_version=self.MODEL_VERSION,
                entity_type="product",
                entity_id=str(product),
                prediction_type=PredictionType.STOCKOUT_PROBABILITY,
                data_label=DataLabel.SIMULATED,  # Simulation, not ML prediction
                value=round(stockout_prob, 4),
                confidence=round(confidence, 4),
                uncertainty=UncertaintyInterval(
                    lower=round(sim.get("prob_lower", max(0, stockout_prob - 0.15)), 4),
                    upper=round(sim.get("prob_upper", min(1, stockout_prob + 0.15)), 4),
                ),
                horizon=f"{self.horizon_days}_days",
                valid_until=valid_until,
                evidence=evidence,
                recommended_action=action,
                model_metrics=dict(self.get_metadata().metrics) if self._metadata else {},
                metadata=_convert_numpy({
                    "current_stock": current_stock,
                    "forecast_demand": forecast_demand,
                    "expected_stockout_date": expected_date,
                    "recommended_replenishment": replenishment,
                    "weeks_of_supply": round(wos, 1) if wos != float("inf") else None,
                    "depletion_curve": depletion_curve,
                }),
            )
            predictions.append(pred)

        return predictions

    def get_metadata(self) -> ModelMetadata:
        if self._metadata:
            return self._metadata
        return self._build_metadata(status=ModelStatus.TRAINED)

    # ── Simulation ────────────────────────────────────────────────

    def _simulate_depletion(
        self,
        current_stock: float,
        forecast_demand: float,
        forecast_upper: float,
    ) -> Dict[str, Any]:
        """
        Simulate inventory depletion over the forecast horizon.

        Returns stockout probability, expected date, and depletion curve.
        """
        weekly_demand = forecast_demand / max(self.horizon_weeks, 1)
        weekly_demand_upper = forecast_upper / max(self.horizon_weeks, 1)

        # Depletion curve (week by week)
        stock = current_stock
        depletion_curve: List[Dict[str, Any]] = []
        stockout_week: Optional[int] = None

        for week in range(1, self.horizon_weeks + 1):
            stock -= weekly_demand
            depletion_curve.append({
                "week": week,
                "projected_stock": round(max(stock, 0), 1),
                "cumulative_demand": round(weekly_demand * week, 1),
            })
            if stock <= 0 and stockout_week is None:
                stockout_week = week

        # Stockout probability
        # Based on ratio of demand to stock, adjusted for uncertainty
        if current_stock <= 0:
            stockout_prob = 1.0
        elif forecast_demand <= 0:
            stockout_prob = 0.0
        else:
            # How much of demand can we cover?
            coverage_ratio = current_stock / forecast_upper  # Use upper bound
            if coverage_ratio >= 1.5:
                stockout_prob = 0.05
            elif coverage_ratio >= 1.0:
                stockout_prob = 0.15
            elif coverage_ratio >= 0.75:
                stockout_prob = 0.45
            elif coverage_ratio >= 0.5:
                stockout_prob = 0.70
            elif coverage_ratio >= 0.25:
                stockout_prob = 0.85
            else:
                stockout_prob = 0.95

        # Expected stockout date
        expected_date: Optional[str] = None
        if stockout_week is not None:
            date = datetime.now(timezone.utc) + timedelta(weeks=stockout_week)
            expected_date = date.strftime("%Y-%m-%d")

        # Probability bounds (from demand uncertainty)
        coverage_lower = current_stock / max(forecast_upper, 1)
        coverage_upper_bound = current_stock / max(forecast_demand * 0.8, 1)

        return {
            "stockout_probability": round(stockout_prob, 4),
            "expected_stockout_date": expected_date,
            "depletion_curve": depletion_curve,
            "stockout_week": stockout_week,
            "prob_lower": max(0, stockout_prob - 0.15),
            "prob_upper": min(1, stockout_prob + 0.15),
        }

    def _calculate_replenishment(
        self,
        current_stock: float,
        forecast_demand: float,
    ) -> float:
        """
        Calculate recommended replenishment quantity.

        Considers: forecast demand, current stock, safety stock factor,
        and supplier lead time.
        """
        # Demand during lead time
        daily_demand = forecast_demand / max(self.horizon_days, 1)
        lead_time_demand = daily_demand * self.lead_time_days

        # Target stock = forecast demand + lead time buffer + safety margin
        target_stock = (forecast_demand + lead_time_demand) * self.safety_stock_factor

        replenishment = max(0, target_stock - current_stock)
        return round(replenishment, 0)

    # ── Recommendations ───────────────────────────────────────────

    @staticmethod
    def _recommend_action(
        stockout_prob: float,
        current_stock: float,
        forecast_demand: float,
        replenishment: float,
        wos: float,
    ) -> str:
        """Generate business-relevant inventory recommendation."""
        if current_stock <= 0:
            return f"URGENT: Out of stock. Reorder immediately — recommended qty: {replenishment:.0f} units."

        if stockout_prob >= STOCKOUT_HIGH:
            return f"HIGH RISK: Reorder {replenishment:.0f} units immediately — stockout likely within forecast horizon."

        if stockout_prob >= STOCKOUT_MEDIUM:
            return f"MODERATE RISK: Plan to reorder ~{replenishment:.0f} units within 1 week."

        if wos > OVERSTOCK_THRESHOLD_WOS:
            return "OVERSTOCK: Consider markdown or promotional activity to move excess inventory."

        if wos > 8:
            return "Healthy inventory. No immediate action required."

        return f"LOW RISK: Inventory adequate. Monitor — next review recommended in {max(1, int(wos)):.0f} weeks."
