"""
Tests for TrendPulse Stockout & Inventory Predictor.

Covers:
    - StockoutPredictor fit and predict contract compliance
    - Stockout probability calculation
    - Replenishment recommendation logic
    - Depletion simulation curve
    - Handling missing stock column gracefully
    - Integration with demand forecasts
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
from data_engine.ml.inventory.stockout_predictor import StockoutPredictor
from tests.test_ml_foundation import _make_clothing_df


class TestStockoutPredictor:
    def test_stockout_with_inventory_and_forecasts(self):
        df = _make_clothing_df(n_weeks=12)

        # Mock pre-computed demand forecasts
        mock_forecasts = [
            Prediction(
                prediction_id="f1",
                model_name="demand_forecaster",
                model_version="1.0",
                entity_type="product",
                entity_id="Oversized Black Tee",
                prediction_type=PredictionType.DEMAND_FORECAST,
                data_label=DataLabel.PREDICTED,
                value=150.0,
                confidence=0.85,
                uncertainty=UncertaintyInterval(lower=120.0, upper=180.0),
            )
        ]

        predictor = StockoutPredictor(horizon_days=30)
        predictor.fit(df, demand_predictions=mock_forecasts)

        assert predictor.is_fitted
        preds = predictor.predict(df)
        assert len(preds) > 0

        for p in preds:
            assert p.prediction_type == PredictionType.STOCKOUT_PROBABILITY
            assert p.data_label == DataLabel.SIMULATED
            assert 0.0 <= p.value <= 1.0
            assert "depletion_curve" in p.metadata
            assert "recommended_replenishment" in p.metadata
            assert len(p.evidence) > 0

    def test_stockout_without_stock_column(self):
        df = _make_clothing_df(n_weeks=6)
        df_no_stock = df.drop(columns=["stock"])

        predictor = StockoutPredictor()
        predictor.fit(df_no_stock)
        preds = predictor.predict(df_no_stock)

        assert len(preds) == 1
        assert preds[0].metadata.get("status") == "insufficient_data"
        assert preds[0].value is None

    def test_urgent_reorder_on_zero_stock(self):
        df = pd.DataFrame({
            "date": ["2025-01-01", "2025-01-08"],
            "product": ["Sold Out Tee", "Sold Out Tee"],
            "category": ["Tops", "Tops"],
            "size": ["M", "M"],
            "quantity": [10, 15],
            "price": [20.0, 20.0],
            "stock": [0, 0],
        })
        predictor = StockoutPredictor(horizon_days=30)
        predictor.fit(df)
        preds = predictor.predict(df)

        assert len(preds) == 1
        pred = preds[0]
        assert pred.value == 1.0  # 100% stockout risk
        assert "URGENT" in pred.recommended_action or pred.metadata.get("current_stock") == 0
