"""
Tests for TrendPulse Autonomous Decision & Action Center.

Covers:
    - DecisionEngine fit and predict contract compliance
    - Synthesis of threats (stockouts, dead stock, VIP churn)
    - Synthesis of opportunities (emerging hits, pricing headroom)
    - Prioritized action feed ranking and financial impact attribution
    - Robustness to empty or partial model inputs
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from data_engine.ml.contracts import (
    DataLabel,
    Prediction,
    PredictionType,
    UncertaintyInterval,
)
from data_engine.ml.decision.decision_engine import DecisionEngine


class TestDecisionEngine:
    def test_decision_synthesis(self):
        # Mock cross-domain predictions
        stockout_pred = Prediction(
            prediction_id="so_1",
            model_name="stockout_predictor",
            model_version="1.0",
            entity_type="product",
            entity_id="Vintage Denim Jacket",
            prediction_type=PredictionType.STOCKOUT_PROBABILITY,
            data_label=DataLabel.SIMULATED,
            value=0.85,
            confidence=0.8,
            metadata={
                "forecast_demand": 80,
                "current_stock": 10,
                "expected_stockout_date": "2026-09-15",
                "recommended_replenishment": 70,
            },
        )

        lifecycle_emerging = Prediction(
            prediction_id="lc_1",
            model_name="lifecycle_classifier",
            model_version="1.0",
            entity_type="sku",
            entity_id="Y2K Baby Tee",
            prediction_type=PredictionType.LIFECYCLE_STAGE,
            data_label=DataLabel.PREDICTED,
            value="emerging",
            confidence=0.88,
        )

        lifecycle_dead = Prediction(
            prediction_id="lc_2",
            model_name="lifecycle_classifier",
            model_version="1.0",
            entity_type="sku",
            entity_id="Flared Corduroy Trousers",
            prediction_type=PredictionType.LIFECYCLE_STAGE,
            data_label=DataLabel.PREDICTED,
            value="dead",
            confidence=0.92,
        )

        pricing_pred = Prediction(
            prediction_id="pr_1",
            model_name="price_elasticity_optimizer",
            model_version="1.0",
            entity_type="product",
            entity_id="Heavyweight Archive Hoodie",
            prediction_type=PredictionType.PRICE_ELASTICITY,
            data_label=DataLabel.PREDICTED,
            value=-0.65,  # highly inelastic
            confidence=0.85,
            metadata={"current_avg_price": 1499.0},
        )

        customer_pred = Prediction(
            prediction_id="cp_1",
            model_name="customer_predictor",
            model_version="1.0",
            entity_type="customer",
            entity_id="CUST-999",
            prediction_type=PredictionType.CHURN_PROBABILITY,
            data_label=DataLabel.PREDICTED,
            value=0.82,  # high churn risk
            confidence=0.85,
            metadata={"customer_segment": "VIP At Risk 🔥", "historical_total_spend": 12500.0},
        )

        engine = DecisionEngine()
        engine.fit(
            pd.DataFrame({"x": [1]}),
            demand_predictions=[],
            lifecycle_predictions=[lifecycle_emerging, lifecycle_dead],
            stockout_predictions=[stockout_pred],
            pricing_predictions=[pricing_pred],
            customer_predictions=[customer_pred],
        )

        assert engine.is_fitted
        center = engine.get_decision_center()
        assert center["status"] == "success"
        assert len(center["ranked_threats"]) >= 3  # stockout, dead stock, VIP churn
        assert len(center["ranked_opportunities"]) >= 2  # emerging hit, pricing headroom
        assert len(center["action_feed"]) >= 5

        # Check action feed sorting (priority 1 first)
        priorities = [a["priority"] for a in center["action_feed"]]
        assert priorities == sorted(priorities)

        preds = engine.predict(pd.DataFrame())
        assert len(preds) == len(center["action_feed"])
        for p in preds:
            assert p.prediction_type == PredictionType.ACTION_RECOMMENDATION

    def test_decision_engine_empty(self):
        engine = DecisionEngine()
        engine.fit(pd.DataFrame(), demand_predictions=[], lifecycle_predictions=[])
        assert engine.is_fitted
        center = engine.get_decision_center()
        assert center["status"] == "success"
        assert len(center["ranked_threats"]) == 0
        assert len(center["ranked_opportunities"]) == 0
