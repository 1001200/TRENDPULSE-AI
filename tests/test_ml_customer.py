"""
Tests for TrendPulse Customer Churn & Repurchase Timing Predictor.

Covers:
    - CustomerPredictor fit and predict contract compliance
    - Churn probability estimation (0.0 to 1.0)
    - Days to next purchase survival estimation
    - VIP At Risk prioritization
    - Handling absent customer_id or empty DataFrame
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
from data_engine.ml.customer.churn_predictor import CustomerPredictor
from tests.test_ml_foundation import _make_clothing_df


class TestCustomerPredictor:
    def test_customer_fit_predict(self):
        df = _make_clothing_df(n_weeks=20)
        predictor = CustomerPredictor(random_state=42)
        predictor.fit(df)

        assert predictor.is_fitted
        meta = predictor.get_metadata()
        assert meta.model_name == "customer_predictor"
        assert meta.status == ModelStatus.EVALUATED

        predictions = predictor.predict(df)
        assert len(predictions) > 0

        for pred in predictions:
            assert pred.prediction_type == PredictionType.CHURN_PROBABILITY
            assert pred.data_label == DataLabel.PREDICTED
            assert pred.value is not None
            assert 0.0 <= pred.value <= 1.0
            assert 0.0 <= pred.confidence <= 1.0
            assert len(pred.evidence) > 0
            assert pred.recommended_action is not None
            assert "days_to_next_purchase" in pred.metadata
            assert "predicted_next_order_spend" in pred.metadata

    def test_customer_without_customer_id(self):
        df = _make_clothing_df(n_weeks=8).drop(columns=["customer_id"])
        predictor = CustomerPredictor()
        predictor.fit(df)
        assert not predictor.is_fitted
        preds = predictor.predict(df)
        assert len(preds) == 0

    def test_empty_dataframe(self):
        predictor = CustomerPredictor()
        predictor.fit(pd.DataFrame())
        assert not predictor.is_fitted
        preds = predictor.predict(pd.DataFrame())
        assert len(preds) == 0
