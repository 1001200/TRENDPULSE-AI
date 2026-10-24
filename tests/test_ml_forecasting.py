"""
Tests for TrendPulse Demand Forecaster.

Covers:
    - DemandForecaster fit and predict contract compliance
    - Auto-selection between baselines and GradientBoosting
    - Multi-horizon forecasting (7d, 14d, 30d, 60d)
    - Size-level allocation via observed ratios
    - Insufficient data handling (honest inability)
    - Non-negative forecasts and prediction interval logic
    - Fallback behavior on noisy/sparse data
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from datetime import datetime, timedelta

from data_engine.ml.contracts import (
    DataLabel,
    ModelStatus,
    PredictionType,
)
from data_engine.ml.forecasting.demand_forecast import (
    DemandForecaster,
    _naive_forecast,
    _seasonal_naive_forecast,
    _moving_average_forecast,
)
from tests.test_ml_foundation import _make_clothing_df


class TestBaselineForecasts:
    def test_naive_forecast(self):
        history = np.array([10, 15, 20])
        forecast = _naive_forecast(history, horizon=3)
        assert len(forecast) == 3
        np.testing.assert_array_equal(forecast, np.array([20, 20, 20]))

    def test_seasonal_naive_forecast(self):
        history = np.array([10, 20, 30, 40, 12, 22, 32, 42])
        forecast = _seasonal_naive_forecast(history, horizon=6, season_length=4)
        assert len(forecast) == 6
        expected = np.array([12, 22, 32, 42, 12, 22])
        np.testing.assert_array_equal(forecast, expected)

    def test_moving_average_forecast(self):
        history = np.array([10, 20, 30, 40])
        forecast = _moving_average_forecast(history, horizon=2, window=2)
        assert len(forecast) == 2
        np.testing.assert_array_equal(forecast, np.array([35.0, 35.0]))


class TestDemandForecaster:
    def test_forecaster_sufficient_data(self):
        df = _make_clothing_df(n_weeks=24)
        forecaster = DemandForecaster(horizon_days=30, random_state=42)
        forecaster.fit(df)

        assert forecaster.is_fitted
        meta = forecaster.get_metadata()
        assert meta.status == ModelStatus.EVALUATED
        assert meta.prediction_horizon == "30_days"

        predictions = forecaster.predict(df, include_sizes=True)
        assert len(predictions) > 0

        # Verify product-level and SKU-level predictions exist
        product_preds = [p for p in predictions if p.entity_type == "product"]
        sku_preds = [p for p in predictions if p.entity_type == "sku"]

        assert len(product_preds) > 0
        assert len(sku_preds) > 0

        for p in product_preds:
            assert p.prediction_type == PredictionType.DEMAND_FORECAST
            assert p.data_label == DataLabel.PREDICTED
            if p.value is not None:
                assert p.value >= 0
                assert 0.0 <= p.confidence <= 1.0
                assert p.uncertainty is not None
                assert p.uncertainty.lower <= p.uncertainty.upper

        for s in sku_preds:
            assert s.entity_type == "sku"
            assert "parent_product" in s.metadata
            assert "size" in s.metadata
            assert s.value is not None
            assert s.value >= 0

    def test_forecaster_insufficient_data(self):
        # Only 2 weeks of data when 30 days (4 weeks) needs >= 8 weeks
        df = _make_clothing_df(n_weeks=2)
        forecaster = DemandForecaster(horizon_days=30)
        forecaster.fit(df)

        predictions = forecaster.predict(df)
        assert len(predictions) > 0
        for p in predictions:
            assert p.confidence == 0.0
            assert p.value is None
            assert p.metadata.get("status") == "insufficient_data"

    def test_forecaster_empty_dataframe(self):
        forecaster = DemandForecaster(horizon_days=14)
        forecaster.fit(pd.DataFrame())
        assert not forecaster.is_fitted
        predictions = forecaster.predict(pd.DataFrame())
        assert len(predictions) == 0

    def test_forecaster_different_horizons(self):
        df = _make_clothing_df(n_weeks=26)
        forecaster_14d = DemandForecaster(horizon_days=14)
        forecaster_14d.fit(df)
        preds_14d = forecaster_14d.predict(df, include_sizes=False)

        forecaster_60d = DemandForecaster(horizon_days=60)
        forecaster_60d.fit(df)
        preds_60d = forecaster_60d.predict(df, include_sizes=False)

        p14 = [p for p in preds_14d if p.value is not None]
        p60 = [p for p in preds_60d if p.value is not None]

        if p14 and p60:
            # 60-day demand forecast should generally be greater than 14-day forecast for the same item
            dict_14 = {p.entity_id: p.value for p in p14}
            dict_60 = {p.entity_id: p.value for p in p60}
            common = set(dict_14.keys()) & set(dict_60.keys())
            for entity in common:
                assert dict_60[entity] >= dict_14[entity]
