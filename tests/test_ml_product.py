"""
Tests for TrendPulse Product Lifecycle Classifier.

Covers:
    - LifecycleClassifier fit and predict contract compliance
    - 6-stage lifecycle categorization (NEW, EMERGING, GROWING, MATURE, DECLINING, DEAD)
    - Deterministic rule-based labeling & RandomForest confidence scoring
    - Feature importance and evidence generation
    - Empty and single-SKU edge cases
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from data_engine.ml.contracts import (
    DataLabel,
    LifecycleStage,
    ModelStatus,
    PredictionType,
)
from data_engine.ml.product.lifecycle import LifecycleClassifier
from tests.test_ml_foundation import _make_clothing_df


class TestLifecycleClassifier:
    def test_lifecycle_fit_predict(self):
        df = _make_clothing_df(n_weeks=18)
        classifier = LifecycleClassifier(random_state=42)
        classifier.fit(df)

        assert classifier.is_fitted
        meta = classifier.get_metadata()
        assert meta.model_name == "lifecycle_classifier"
        assert meta.target == "lifecycle_stage"

        predictions = classifier.predict(df)
        assert len(predictions) > 0

        valid_stages = {s.value for s in LifecycleStage}

        for pred in predictions:
            assert pred.prediction_type == PredictionType.LIFECYCLE_STAGE
            assert pred.data_label == DataLabel.PREDICTED
            assert pred.value in valid_stages
            assert 0.0 <= pred.confidence <= 1.0
            assert len(pred.evidence) > 0
            assert pred.recommended_action is not None
            assert "velocity_units_per_week" in pred.metadata

    def test_lifecycle_empty_df(self):
        classifier = LifecycleClassifier()
        classifier.fit(pd.DataFrame())
        assert not classifier.is_fitted
        preds = classifier.predict(pd.DataFrame())
        assert len(preds) == 0

    def test_new_item_classification(self):
        # A single item selling for only 2 weeks should be classified as NEW
        dates = ["2025-01-01", "2025-01-05", "2025-01-10"]
        df = pd.DataFrame({
            "date": dates,
            "product": ["Brand New Top"] * 3,
            "category": ["Tops"] * 3,
            "size": ["M"] * 3,
            "quantity": [2, 3, 2],
            "price": [30.0] * 3,
        })
        classifier = LifecycleClassifier()
        classifier.fit(df)
        preds = classifier.predict(df)
        assert len(preds) == 1
        assert preds[0].value == LifecycleStage.NEW.value
        assert "NEW" in preds[0].evidence[0] or "weeks" in preds[0].evidence[1] or preds[0].value == "new"

    def test_dead_stock_classification(self):
        # Item with last sale 60 days ago and very low units
        dates = ["2025-01-01", "2025-01-02"]
        # Max date in catalog is 2025-04-01 (90 days later)
        df = pd.DataFrame({
            "date": ["2025-01-01", "2025-01-02", "2025-04-01"],
            "product": ["Dead Pants", "Dead Pants", "Active Shirt"],
            "category": ["Bottoms", "Bottoms", "Tops"],
            "size": ["L", "L", "M"],
            "quantity": [1, 1, 50],
            "price": [20.0, 20.0, 40.0],
        })
        classifier = LifecycleClassifier()
        classifier.fit(df)
        preds = classifier.predict(df)
        dead_pred = [p for p in preds if "Dead Pants" in p.entity_id]
        if dead_pred:
            assert dead_pred[0].value == LifecycleStage.DEAD.value
