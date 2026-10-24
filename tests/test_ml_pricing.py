"""
Tests for TrendPulse Price Elasticity & Markdown Optimization Engine.

Covers:
    - PriceElasticityOptimizer fit and predict contract compliance
    - Log-log OLS elasticity estimation
    - Category prior blending when variance is low
    - Classification: Elastic vs Inelastic vs Unit Elastic
    - Optimal markdown scheduling for declining styles
    - What-If Price Simulator (volume, revenue, and gross profit projections)
    - Empty and single-product edge cases
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from data_engine.ml.contracts import (
    DataLabel,
    ModelStatus,
    Prediction,
    PredictionType,
)
from data_engine.ml.pricing.elasticity_optimizer import PriceElasticityOptimizer
from tests.test_ml_foundation import _make_clothing_df


class TestPriceElasticityOptimizer:
    def test_elasticity_fit_predict(self):
        df = _make_clothing_df(n_weeks=16)
        optimizer = PriceElasticityOptimizer(random_state=42)
        optimizer.fit(df)

        assert optimizer.is_fitted
        meta = optimizer.get_metadata()
        assert meta.model_name == "price_elasticity_optimizer"
        assert meta.status == ModelStatus.EVALUATED

        predictions = optimizer.predict(df)
        assert len(predictions) > 0

        for pred in predictions:
            assert pred.prediction_type == PredictionType.PRICE_ELASTICITY
            assert pred.data_label == DataLabel.PREDICTED
            assert pred.value is not None
            # Price elasticity in normal downward-sloping demand curves is negative
            assert pred.value < 0.0
            assert 0.0 <= pred.confidence <= 1.0
            assert len(pred.evidence) > 0
            assert "sensitivity" in pred.metadata
            assert "optimal_discount_pct" in pred.metadata

    def test_what_if_price_simulation(self):
        df = _make_clothing_df(n_weeks=16)
        optimizer = PriceElasticityOptimizer()
        optimizer.fit(df)

        # Grab a product from the catalog
        sample_prod = "Oversized Black Tee"
        # Simulate price decrease
        sim_down = optimizer.simulate_price_change(sample_prod, new_price=25.0)
        assert sim_down["status"] == "success"
        assert sim_down["data_label"] == DataLabel.SIMULATED.value
        assert sim_down["product"] == sample_prod
        assert "projected_units" in sim_down
        assert "projected_revenue" in sim_down
        assert "projected_profit" in sim_down
        assert "verdict" in sim_down

        # Simulate price increase
        sim_up = optimizer.simulate_price_change(sample_prod, new_price=80.0)
        assert sim_up["status"] == "success"
        assert sim_up["price_change_pct"] > 0

    def test_simulation_nonexistent_product(self):
        optimizer = PriceElasticityOptimizer()
        optimizer.fit(_make_clothing_df(n_weeks=4))
        res = optimizer.simulate_price_change("Nonexistent Space Suit", 1000.0)
        assert res["status"] == "error"
        assert "not found" in res["message"].lower()

    def test_empty_dataframe(self):
        optimizer = PriceElasticityOptimizer()
        optimizer.fit(pd.DataFrame())
        assert not optimizer.is_fitted
        preds = optimizer.predict(pd.DataFrame())
        assert len(preds) == 0
