"""
TrendPulse Product Lifecycle Classifier.

Classifies every SKU/product into one of 6 apparel lifecycle stages
based on sales trajectory features:

    NEW        — Recently launched, < 3 weeks of history
    EMERGING   — Accelerating velocity, gaining traction
    GROWING    — Strong consistent sales, positive trend
    MATURE     — Steady long-term seller, low volatility
    DECLINING  — Decelerating velocity, past peak
    DEAD       — Near-zero velocity, stagnant inventory

Architecture:
    1. Consume SKU features from FeatureEngineer
    2. Apply rule-based auto-labeling from feature distributions
    3. Train RandomForestClassifier for confidence scoring & explainability
    4. Output per-SKU lifecycle stage with confidence, evidence, and action

Design rules:
    - Implements ``BaseModel`` contract.
    - Rule-based labeling is transparent and auditable.
    - RF is used for confidence calibration and feature importance, NOT
      as an opaque black box — the rules define the stages, RF refines
      the confidence boundaries.
    - Deterministic; zero side-effects.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from data_engine.ml.contracts import (
    BaseModel,
    DataLabel,
    FeatureContribution,
    LifecycleStage,
    ModelMetadata,
    ModelStatus,
    Prediction,
    PredictionType,
    _convert_numpy,
    insufficient_data_result,
)
from data_engine.ml.evaluation import compute_classification_metrics
from data_engine.ml.feature_store import FeatureEngineer, FeatureSet


# ─────────────────────────────────────────────────────────────────────
# Stage → Action mapping
# ─────────────────────────────────────────────────────────────────────

STAGE_ACTIONS: Dict[str, str] = {
    LifecycleStage.NEW: "Monitor closely — too early to make inventory commitments.",
    LifecycleStage.EMERGING: "Increase inventory — this product is gaining traction fast.",
    LifecycleStage.GROWING: "Protect stock and scale marketing — strong demand trajectory.",
    LifecycleStage.MATURE: "Maintain continuous availability — steady reliable seller.",
    LifecycleStage.DECLINING: "Reduce reorders and plan markdown — demand is fading.",
    LifecycleStage.DEAD: "Clearance, bundle, or discontinue — minimal remaining demand.",
}

STAGE_RISK: Dict[str, str] = {
    LifecycleStage.NEW: "Uncertainty — insufficient history to confirm trajectory.",
    LifecycleStage.EMERGING: "May be a flash trend — monitor velocity sustainability.",
    LifecycleStage.GROWING: "Stockout risk if demand exceeds supply.",
    LifecycleStage.MATURE: "Margin erosion from competitors or market saturation.",
    LifecycleStage.DECLINING: "Overstock risk if not proactively managed.",
    LifecycleStage.DEAD: "Capital tied up in unsellable inventory.",
}


# ─────────────────────────────────────────────────────────────────────
# Lifecycle Classifier
# ─────────────────────────────────────────────────────────────────────

class LifecycleClassifier(BaseModel):
    """
    Classifies every product/SKU into a lifecycle stage.

    Two-phase approach:
        Phase 1: Deterministic rule-based labeling (transparent, auditable)
        Phase 2: RandomForest refinement for confidence scoring and
                 feature importance (explainability)
    """

    MODEL_NAME = "lifecycle_classifier"
    MODEL_VERSION = "1.0"
    MODEL_TYPE = "rule_based + random_forest"

    # Thresholds for rule-based classification
    NEW_MAX_WEEKS = 3
    DEAD_MAX_VELOCITY = 0.5      # units/week
    DEAD_MIN_RECENCY = 21        # days since last sale
    EMERGING_MIN_TREND = 0.3     # 30% velocity acceleration
    DECLINING_MAX_TREND = -0.2   # 20% velocity deceleration
    MATURE_MAX_CV = 0.5          # coefficient of variation

    def __init__(self, *, random_state: int = 42):
        super().__init__()
        self.random_state = random_state
        self._rf_model: Optional[RandomForestClassifier] = None
        self._sku_features: Optional[FeatureSet] = None
        self._labels: Dict[str, str] = {}
        self._training_metrics: Dict[str, float] = {}

    # ── BaseModel Interface ───────────────────────────────────────

    def fit(self, df: pd.DataFrame, **kwargs) -> "LifecycleClassifier":
        """
        Train the lifecycle classifier.

        1. Generate SKU features via FeatureEngineer
        2. Apply rule-based auto-labeling
        3. Train RandomForest for confidence calibration
        """
        if not isinstance(df, pd.DataFrame) or df.empty:
            self._is_fitted = False
            return self

        fe = FeatureEngineer(df)
        self._sku_features = fe.build_sku_features()

        if self._sku_features.features.empty:
            self._is_fitted = False
            return self

        features_df = self._sku_features.features.copy()

        # Phase 1: Rule-based labeling
        features_df["_rule_stage"] = features_df.apply(self._rule_classify, axis=1)
        self._labels = dict(zip(features_df["sku"], features_df["_rule_stage"]))

        # Phase 2: Train RF for confidence scoring
        numeric_cols = [
            "total_units", "total_revenue", "avg_selling_price",
            "velocity_units_per_week", "velocity_trend", "active_weeks",
            "num_selling_weeks", "recency_days", "coefficient_of_variation",
            "revenue_share_pct", "margin_pct", "avg_discount",
            "days_since_first_sale", "size_count", "size_fragmentation",
        ]
        available_cols = [c for c in numeric_cols if c in features_df.columns]

        if len(available_cols) >= 3 and len(features_df) >= 5:
            X = features_df[available_cols].fillna(0).values
            y = features_df["_rule_stage"].values

            # Only train if we have at least 2 distinct classes
            if len(set(y)) >= 2:
                self._rf_model = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=5,
                    min_samples_leaf=2,
                    random_state=self.random_state,
                    class_weight="balanced",
                )
                self._rf_model.fit(X, y)
                self._feature_names = available_cols

                # Evaluate (in-sample — backtesting would require temporal splits
                # which don't make sense for lifecycle classification)
                y_pred = self._rf_model.predict(X)
                self._training_metrics = compute_classification_metrics(
                    y, y_pred,
                    labels=[s.value for s in LifecycleStage],
                )
            else:
                self._training_metrics = {"note": "single_class_dataset"}
        else:
            self._training_metrics = {"note": "insufficient_features_for_rf"}

        self._is_fitted = True
        self._build_metadata(
            status=ModelStatus.EVALUATED,
            metrics=_convert_numpy(self._training_metrics),
            n_training_samples=len(features_df),
            training_data_range=self._sku_features.data_range,
            target="lifecycle_stage",
            hyperparameters={"random_state": self.random_state},
        )
        return self

    def predict(self, df: pd.DataFrame, **kwargs) -> List[Prediction]:
        """Generate lifecycle classifications for all SKUs."""
        if not self._is_fitted or self._sku_features is None:
            return []

        features_df = self._sku_features.features
        predictions: List[Prediction] = []

        numeric_cols = list(self._feature_names) if self._feature_names else []

        for _, row in features_df.iterrows():
            sku = str(row.get("sku", "unknown"))
            product = str(row.get("product", sku))
            category = str(row.get("category", "unknown"))

            # Rule-based stage
            stage = self._rule_classify(row)

            # Confidence from RF
            confidence = 0.7  # default for rule-based only
            top_features: List[FeatureContribution] = []

            if self._rf_model is not None and numeric_cols:
                try:
                    X = np.array([[float(row.get(c, 0)) for c in numeric_cols]])
                    probas = self._rf_model.predict_proba(X)[0]
                    class_labels = self._rf_model.classes_

                    # Find probability of the rule-assigned stage
                    if stage in class_labels:
                        stage_idx = list(class_labels).index(stage)
                        confidence = float(probas[stage_idx])
                    else:
                        confidence = float(np.max(probas))

                    # Feature importance
                    importances = self._rf_model.feature_importances_
                    pairs = sorted(
                        zip(numeric_cols, importances),
                        key=lambda x: x[1], reverse=True,
                    )
                    top_features = [
                        FeatureContribution(
                            name=name,
                            importance=round(float(imp), 4),
                            direction=self._feature_direction(name, row, stage),
                        )
                        for name, imp in pairs[:5]
                    ]
                except Exception:
                    pass

            # Evidence
            evidence = self._build_evidence(row, stage)

            # Staleness: lifecycle re-assessment every 7 days
            valid_until = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

            pred = self._make_prediction(
                entity_type="sku",
                entity_id=sku,
                prediction_type=PredictionType.LIFECYCLE_STAGE,
                value=stage,
                confidence=round(confidence, 4),
                valid_until=valid_until,
                evidence=evidence,
                recommended_action=STAGE_ACTIONS.get(stage, "Monitor."),
                top_features=top_features,
                metadata_extra={
                    "product": product,
                    "category": category,
                    "risk": STAGE_RISK.get(stage, ""),
                    "velocity_units_per_week": round(float(row.get("velocity_units_per_week", 0)), 2),
                    "velocity_trend": round(float(row.get("velocity_trend", 0)), 4),
                    "recency_days": int(row.get("recency_days", 0)),
                },
            )
            predictions.append(pred)

        return predictions

    def get_metadata(self) -> ModelMetadata:
        if self._metadata:
            return self._metadata
        return self._build_metadata(status=ModelStatus.TRAINED)

    # ── Rule-Based Classification ─────────────────────────────────

    def _rule_classify(self, row: pd.Series) -> str:
        """
        Deterministic rule-based lifecycle classification.

        Rules are applied in priority order (most specific first).
        """
        active_weeks = float(row.get("active_weeks", 0))
        velocity = float(row.get("velocity_units_per_week", 0))
        trend = float(row.get("velocity_trend", 0))
        recency = int(row.get("recency_days", 0))
        cv = float(row.get("coefficient_of_variation", 0))
        total_units = float(row.get("total_units", 0))

        # DEAD: No recent sales and very low velocity, or dormant for 45+ days
        if (velocity <= self.DEAD_MAX_VELOCITY and recency >= self.DEAD_MIN_RECENCY) or recency >= 45:
            return LifecycleStage.DEAD.value

        # NEW: Very recent product with minimal history and recent sales
        if active_weeks <= self.NEW_MAX_WEEKS and recency <= self.DEAD_MIN_RECENCY:
            return LifecycleStage.NEW.value

        # EMERGING: Strong positive acceleration
        if trend >= self.EMERGING_MIN_TREND and active_weeks <= 12:
            return LifecycleStage.EMERGING.value

        # DECLINING: Significant deceleration
        if trend <= self.DECLINING_MAX_TREND and active_weeks > 6:
            return LifecycleStage.DECLINING.value

        # GROWING: Positive trend, good velocity, moderate history
        if trend > 0.05 and velocity > 1.0 and active_weeks > 4:
            return LifecycleStage.GROWING.value

        # MATURE: Stable, low volatility, long history
        if cv <= self.MATURE_MAX_CV and active_weeks > 8 and velocity > 0.5:
            return LifecycleStage.MATURE.value

        # Fallback based on trend direction
        if trend > 0:
            return LifecycleStage.GROWING.value
        elif trend < -0.1:
            return LifecycleStage.DECLINING.value
        else:
            return LifecycleStage.MATURE.value

    # ── Evidence & Explainability ─────────────────────────────────

    @staticmethod
    def _build_evidence(row: pd.Series, stage: str) -> List[str]:
        """Build human-readable evidence list for a classification."""
        evidence = []

        velocity = float(row.get("velocity_units_per_week", 0))
        trend = float(row.get("velocity_trend", 0))
        recency = int(row.get("recency_days", 0))
        active_weeks = float(row.get("active_weeks", 0))
        cv = float(row.get("coefficient_of_variation", 0))
        units = float(row.get("total_units", 0))
        rev_share = float(row.get("revenue_share_pct", 0))

        evidence.append(f"Sales velocity: {velocity:.1f} units/week")

        if trend > 0.1:
            evidence.append(f"Velocity trend: +{trend:.0%} (accelerating)")
        elif trend < -0.1:
            evidence.append(f"Velocity trend: {trend:.0%} (decelerating)")
        else:
            evidence.append(f"Velocity trend: stable ({trend:+.0%})")

        evidence.append(f"Active for {active_weeks:.0f} weeks")
        evidence.append(f"Last sale: {recency} days ago")
        evidence.append(f"Total units sold: {units:.0f}")

        if rev_share > 5:
            evidence.append(f"Revenue share: {rev_share:.1f}% (significant)")
        elif rev_share > 1:
            evidence.append(f"Revenue share: {rev_share:.1f}%")

        if cv > 1.0:
            evidence.append(f"High sales volatility (CV={cv:.2f})")
        elif cv < 0.3:
            evidence.append(f"Very consistent sales (CV={cv:.2f})")

        return evidence

    @staticmethod
    def _feature_direction(name: str, row: pd.Series, stage: str) -> str:
        """Determine if a feature pushes toward or against the assigned stage."""
        val = float(row.get(name, 0))
        if name == "velocity_trend":
            if stage in (LifecycleStage.EMERGING, LifecycleStage.GROWING):
                return "positive" if val > 0 else "negative"
            elif stage in (LifecycleStage.DECLINING, LifecycleStage.DEAD):
                return "positive" if val < 0 else "negative"
        if name == "recency_days":
            return "positive" if (stage == LifecycleStage.DEAD and val > 14) else "neutral"
        if name == "velocity_units_per_week":
            return "positive" if val > 1 else "negative"
        return "neutral"
