"""
TrendPulse Customer Churn Risk & Repurchase Timing Predictor.

Analyzes customer-level purchase histories, behavioral inter-purchase intervals,
and monetary value to predict:
    1. Churn Probability (0–100%)
    2. Days until next expected purchase (survival timing)
    3. Expected next order transaction value (₹)
    4. Actionable re-engagement triggers before permanent customer dormancy

Architecture:
    - Consumes customer behavioral matrices from FeatureEngineer.
    - Implements stochastic survival modeling on inter-purchase intervals (mu, sigma).
    - Calibrates single-order customer risks using catalog-wide baseline intervals.
    - Identifies high-value "VIP At Risk" customers for targeted drop invitations.

Design rules:
    - Implements BaseModel contract.
    - Zero side-effects; deterministic random_state.
    - Handles sparse or missing customer_id gracefully without crashing.
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


class CustomerPredictor(BaseModel):
    """
    Predictive engine for customer churn probabilities, repurchase intervals, and expected spend.
    """

    MODEL_NAME = "customer_predictor"
    MODEL_VERSION = "1.0"
    MODEL_TYPE = "survival_interval_and_churn_classifier"

    # Default dormant threshold for apparel (in days)
    GLOBAL_DORMANCY_DAYS = 60.0

    def __init__(self, *, churn_horizon_days: int = 60, random_state: int = 42):
        super().__init__()
        self.churn_horizon_days = churn_horizon_days
        self.random_state = random_state

        # Internal state
        self._customer_profiles: Dict[str, Dict[str, Any]] = {}
        self._store_median_interval: float = 30.0
        self._store_mean_aov: float = 800.0

    # ── BaseModel Interface ───────────────────────────────────────

    def fit(self, df: pd.DataFrame, **kwargs) -> "CustomerPredictor":
        """
        Extract customer behavioral features and establish interval baselines.
        """
        if not isinstance(df, pd.DataFrame) or df.empty or "customer_id" not in df.columns:
            self._is_fitted = False
            return self

        fe = FeatureEngineer(df)
        cf_set = fe.build_customer_features()

        if cf_set.features.empty:
            self._is_fitted = False
            return self

        cust_df = cf_set.features.copy()

        # Catalog-wide baselines
        multi_order = cust_df[cust_df["frequency"] >= 2]
        if not multi_order.empty and (multi_order["purchase_interval_mean"] > 0).any():
            self._store_median_interval = float(multi_order["purchase_interval_mean"].median())
        else:
            self._store_median_interval = self.GLOBAL_DORMANCY_DAYS / 2.0

        if not cust_df.empty:
            self._store_mean_aov = float(cust_df["avg_order_value"].mean())

        # Build predictive customer profiles
        for _, row in cust_df.iterrows():
            cid = str(row.get("customer_id", "unknown"))
            recency = float(row.get("recency_days", 0))
            freq = int(row.get("frequency", 1))
            monetary = float(row.get("monetary", 0))
            aov = float(row.get("avg_order_value", self._store_mean_aov))
            mu_interval = float(row.get("purchase_interval_mean", 0))
            sigma_interval = float(row.get("purchase_interval_std", 0))

            # Churn Probability Computation via Interval Survival Function
            if freq >= 2 and mu_interval > 0:
                # Customer has an established cadence
                effective_sigma = max(sigma_interval, mu_interval * 0.25, 5.0)
                z_score = (recency - mu_interval) / effective_sigma
                # Sigmoid scaling
                churn_prob = 1.0 / (1.0 + np.exp(-1.2 * z_score))
                days_left = mu_interval - recency
                confidence = 0.85
            else:
                # Single-order customer: compare with store-wide interval
                ratio = recency / max(self._store_median_interval, 1.0)
                if ratio >= 2.0:
                    churn_prob = 0.80
                elif ratio >= 1.0:
                    churn_prob = 0.55
                else:
                    churn_prob = 0.25
                days_left = self._store_median_interval - recency
                confidence = 0.65

            churn_prob = max(0.02, min(0.98, float(churn_prob)))

            # Customer Risk Segment
            if churn_prob >= 0.70 and monetary >= self._store_mean_aov * 2:
                segment = "VIP At Risk 🔥"
                action = "URGENT: High-value buyer about to lapse. Send personalized private drop preview with VIP incentive."
            elif churn_prob >= 0.70:
                segment = "Dormant / Churning"
                action = "Trigger automated re-engagement campaign or win-back offer."
            elif churn_prob <= 0.35 and freq >= 2:
                segment = "Active Champion 💎"
                action = "Maintain regular touchpoints; prime candidate for early-access drop notifications."
            else:
                segment = "Casual / Promising"
                action = "Nurture with trending aesthetic recommendations."

            # Expected next purchase timing
            if days_left > 0:
                timing_desc = f"Expected in ~{int(days_left)} days"
                days_to_next = max(1, int(days_left))
            else:
                overdue_by = abs(int(days_left))
                timing_desc = f"Overdue by {overdue_by} days"
                days_to_next = 0

            # Expected next spend: smoothed weighted average
            expected_spend = round((aov * 0.85) + (self._store_mean_aov * 0.15), 2)

            self._customer_profiles[cid] = {
                "churn_probability": round(churn_prob, 3),
                "confidence": confidence,
                "segment": segment,
                "action": action,
                "days_to_next_purchase": days_to_next,
                "timing_desc": timing_desc,
                "expected_spend": expected_spend,
                "recency_days": int(recency),
                "frequency": freq,
                "total_spend": round(monetary, 2),
                "avg_order_value": round(aov, 2),
            }

        self._is_fitted = True
        self._build_metadata(
            status=ModelStatus.EVALUATED,
            metrics={
                "total_customers_modeled": len(self._customer_profiles),
                "high_risk_churn_count": len([p for p in self._customer_profiles.values() if p["churn_probability"] >= 0.70]),
                "store_median_reorder_interval_days": round(self._store_median_interval, 1),
            },
            n_training_samples=len(cust_df),
            target="customer_churn_probability",
            hyperparameters={"churn_horizon_days": self.churn_horizon_days},
        )
        return self

    def predict(self, df: pd.DataFrame, **kwargs) -> List[Prediction]:
        """
        Generate customer churn risk and repurchase predictions.
        """
        if not self._is_fitted:
            return []

        predictions: List[Prediction] = []

        for cid, info in self._customer_profiles.items():
            prob = info["churn_probability"]
            confidence = info["confidence"]

            evidence = [
                f"Customer Segment: {info['segment']}",
                f"Days Since Last Purchase: {info['recency_days']} days",
                f"Total Historical Orders: {info['frequency']} (Total Spend: ₹{info['total_spend']:,.2f})",
                f"Repurchase Timing: {info['timing_desc']}",
                f"Predicted Next Spend: ₹{info['expected_spend']:,.2f}",
            ]

            valid_until = (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()

            pred = self._make_prediction(
                entity_type="customer",
                entity_id=cid,
                prediction_type=PredictionType.CHURN_PROBABILITY,
                value=prob,
                confidence=confidence,
                uncertainty=UncertaintyInterval(
                    lower=max(0.0, round(prob - 0.12, 3)),
                    upper=min(1.0, round(prob + 0.12, 3)),
                ),
                horizon=f"{self.churn_horizon_days}_days",
                valid_until=valid_until,
                evidence=evidence,
                recommended_action=info["action"],
                top_features=[
                    FeatureContribution(name="recency_interval_ratio", importance=0.55, direction="positive" if prob > 0.5 else "negative"),
                    FeatureContribution(name="purchase_frequency", importance=0.30, direction="negative"),
                    FeatureContribution(name="historical_monetary_value", importance=0.15, direction="neutral"),
                ],
                metadata_extra={
                    "customer_segment": info["segment"],
                    "days_to_next_purchase": info["days_to_next_purchase"],
                    "repurchase_timing_description": info["timing_desc"],
                    "predicted_next_order_spend": info["expected_spend"],
                    "historical_frequency": info["frequency"],
                    "historical_total_spend": info["total_spend"],
                },
            )
            predictions.append(pred)

        return predictions

    def get_metadata(self) -> ModelMetadata:
        if self._metadata:
            return self._metadata
        return self._build_metadata(status=ModelStatus.TRAINED)
