"""
Tests for TrendPulse ML Foundation — Contracts, Feature Store, Evaluation, Registry.

Covers:
    - BaseModel contract enforcement
    - Prediction / ModelMetadata dataclass construction
    - FeatureEngineer: SKU features, time-series features, customer features, size ratios
    - Leakage prevention (as_of_date cutoff)
    - TimeSeriesSplitter: walk-forward splitting
    - Metric functions: MAE, RMSE, MAPE, sMAPE, WAPE
    - ModelRegistry: register / lookup / serialization
    - Edge cases: empty DataFrames, missing columns, single-row data
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from datetime import datetime, timedelta

from data_engine.ml.contracts import (
    BaseModel,
    DataLabel,
    FeatureContribution,
    LifecycleStage,
    ModelMetadata,
    ModelStatus,
    Prediction,
    PredictionType,
    UncertaintyInterval,
    _convert_numpy,
    insufficient_data_result,
)
from data_engine.ml.feature_store import FeatureEngineer, FeatureSet
from data_engine.ml.evaluation import (
    TimeSeriesSplitter,
    compute_mae,
    compute_rmse,
    compute_mape,
    compute_smape,
    compute_wape,
    compute_regression_metrics,
    compute_classification_metrics,
    compute_prediction_intervals,
    BacktestResult,
)
from data_engine.ml.registry import ModelRegistry


# ─────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────

def _make_clothing_df(n_weeks: int = 20) -> pd.DataFrame:
    """Generate realistic clothing sales DataFrame for testing."""
    rng = np.random.default_rng(42)
    dates = []
    products, categories, sizes, quantities, prices = [], [], [], [], []
    customer_ids, stocks, cost_prices = [], [], []

    product_catalog = [
        ("Oversized Black Tee", "Tops", ["S", "M", "L", "XL"]),
        ("Vintage Denim Jacket", "Outerwear", ["M", "L"]),
        ("Y2K Baby Tee", "Tops", ["XS", "S", "M"]),
        ("Cargo Pants", "Bottoms", ["M", "L", "XL"]),
    ]

    base_date = datetime(2025, 1, 1)

    for week in range(n_weeks):
        for product, cat, size_list in product_catalog:
            for size in size_list:
                n_days = rng.integers(1, 5)
                for _ in range(n_days):
                    day_offset = week * 7 + rng.integers(0, 7)
                    date = base_date + timedelta(days=int(day_offset))
                    qty = max(1, int(rng.normal(5, 2)))
                    price = round(rng.uniform(15, 65), 2)
                    cost = round(price * rng.uniform(0.3, 0.6), 2)
                    stock_val = max(0, int(rng.normal(100, 30)))

                    dates.append(date.strftime("%Y-%m-%d"))
                    products.append(product)
                    categories.append(cat)
                    sizes.append(size)
                    quantities.append(qty)
                    prices.append(price)
                    customer_ids.append(f"CUST-{rng.integers(1, 30):03d}")
                    stocks.append(stock_val)
                    cost_prices.append(cost)

    return pd.DataFrame({
        "date": dates,
        "product": products,
        "category": categories,
        "size": sizes,
        "quantity": quantities,
        "price": prices,
        "customer_id": customer_ids,
        "stock": stocks,
        "cost_price": cost_prices,
    })


# ─────────────────────────────────────────────────────────────────────
# Contract Tests
# ─────────────────────────────────────────────────────────────────────

class TestContracts:
    def test_prediction_auto_id(self):
        p = Prediction(
            prediction_id="",
            model_name="test",
            model_version="1.0",
            entity_type="product",
            entity_id="tee-1",
            prediction_type=PredictionType.DEMAND_FORECAST,
            data_label=DataLabel.PREDICTED,
            value=42,
            confidence=0.9,
        )
        assert p.prediction_id != ""
        assert len(p.prediction_id) == 12
        assert p.generated_at != ""

    def test_prediction_to_dict(self):
        p = Prediction(
            prediction_id="abc123",
            model_name="test",
            model_version="1.0",
            entity_type="sku",
            entity_id="tee-1 | M",
            prediction_type=PredictionType.LIFECYCLE_STAGE,
            data_label=DataLabel.PREDICTED,
            value="growing",
            confidence=0.85,
            uncertainty=UncertaintyInterval(lower=0.7, upper=0.95),
        )
        d = p.to_dict()
        assert d["prediction_id"] == "abc123"
        assert d["uncertainty"]["lower"] == 0.7
        assert isinstance(d, dict)

    def test_model_metadata(self):
        m = ModelMetadata(
            model_name="demand_forecaster",
            model_version="1.0",
            model_type="gradient_boosting",
            status=ModelStatus.EVALUATED,
            metrics={"wape": 12.5},
            n_training_samples=100,
        )
        assert m.training_timestamp != ""
        d = m.to_dict()
        assert d["metrics"]["wape"] == 12.5

    def test_numpy_conversion(self):
        data = {
            "int": np.int64(42),
            "float": np.float64(3.14),
            "nan": np.float64("nan"),
            "array": np.array([1, 2, 3]),
            "bool": np.bool_(True),
        }
        safe = _convert_numpy(data)
        assert safe["int"] == 42
        assert safe["float"] == 3.14
        assert safe["nan"] is None
        assert safe["array"] == [1, 2, 3]
        assert safe["bool"] is True

    def test_insufficient_data_result(self):
        r = insufficient_data_result("test_model", "Not enough rows", "50 rows minimum")
        assert r["status"] == "insufficient_data"
        assert r["minimum_required"] == "50 rows minimum"

    def test_enums(self):
        assert PredictionType.DEMAND_FORECAST == "demand_forecast"
        assert DataLabel.SIMULATED == "simulated"
        assert LifecycleStage.EMERGING == "emerging"
        assert ModelStatus.EVALUATED == "evaluated"


# ─────────────────────────────────────────────────────────────────────
# Feature Store Tests
# ─────────────────────────────────────────────────────────────────────

class TestFeatureStore:
    def test_sku_features_shape(self):
        df = _make_clothing_df(n_weeks=12)
        fe = FeatureEngineer(df)
        fs = fe.build_sku_features()

        assert isinstance(fs, FeatureSet)
        assert not fs.features.empty
        assert fs.n_features > 0
        assert "velocity_units_per_week" in fs.feature_names
        assert "total_units" in fs.features.columns
        assert fs.data_range is not None

    def test_sku_features_no_negative_velocity(self):
        df = _make_clothing_df(n_weeks=12)
        fe = FeatureEngineer(df)
        fs = fe.build_sku_features()
        assert (fs.features["velocity_units_per_week"] >= 0).all()

    def test_time_series_features(self):
        df = _make_clothing_df(n_weeks=12)
        fe = FeatureEngineer(df)
        ts = fe.build_time_series_features(freq="W")

        assert not ts.features.empty
        assert "rolling_4w_qty" in ts.feature_names
        assert "trend_slope" in ts.feature_names
        assert "group" in ts.features.columns

    def test_customer_features(self):
        df = _make_clothing_df(n_weeks=12)
        fe = FeatureEngineer(df)
        cf = fe.build_customer_features()

        assert not cf.features.empty
        assert "recency_days" in cf.feature_names
        assert "frequency" in cf.feature_names
        assert "size_consistency" in cf.feature_names

    def test_size_ratios(self):
        df = _make_clothing_df(n_weeks=12)
        fe = FeatureEngineer(df)
        ratios = fe.build_size_ratios()

        assert isinstance(ratios, dict)
        assert len(ratios) > 0
        for product, size_dist in ratios.items():
            total = sum(size_dist.values())
            assert abs(total - 1.0) < 0.01, f"Size ratios for {product} don't sum to 1"

    def test_leakage_prevention(self):
        df = _make_clothing_df(n_weeks=20)
        cutoff = pd.Timestamp("2025-02-15")

        fe = FeatureEngineer(df, as_of_date=cutoff)
        fs = fe.build_sku_features()

        # All data should be before cutoff
        if not fs.features.empty and fs.data_range:
            end_date = pd.Timestamp(fs.data_range["end"])
            assert end_date <= cutoff

    def test_empty_dataframe(self):
        fe = FeatureEngineer(pd.DataFrame())
        fs = fe.build_sku_features()
        assert fs.features.empty
        assert fs.metadata.get("status") == "no_data"

    def test_missing_columns(self):
        df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
        fe = FeatureEngineer(df)
        cf = fe.build_customer_features()
        assert cf.features.empty


# ─────────────────────────────────────────────────────────────────────
# Evaluation Tests
# ─────────────────────────────────────────────────────────────────────

class TestEvaluation:
    def test_mae(self):
        actual = np.array([10, 20, 30])
        pred = np.array([12, 18, 33])
        assert compute_mae(actual, pred) == pytest.approx(7.0 / 3.0, abs=0.01)

    def test_rmse(self):
        actual = np.array([10, 20, 30])
        pred = np.array([10, 20, 30])
        assert compute_rmse(actual, pred) == 0.0

    def test_wape(self):
        actual = np.array([100, 200, 300])
        pred = np.array([110, 190, 310])
        # Total error = 10 + 10 + 10 = 30, total actual = 600
        assert compute_wape(actual, pred) == pytest.approx(5.0, abs=0.01)

    def test_smape_symmetry(self):
        a = np.array([10.0])
        p = np.array([12.0])
        # sMAPE should be the same regardless of which is "actual"
        s1 = compute_smape(a, p)
        s2 = compute_smape(p, a)
        assert s1 == pytest.approx(s2, abs=0.01)

    def test_mape_safe_zero(self):
        actual = np.array([0.0, 100.0])
        pred = np.array([5.0, 110.0])
        # Should not crash on zero actual (uses epsilon)
        result = compute_mape(actual, pred)
        assert result >= 0

    def test_regression_metrics_all_keys(self):
        a = np.array([10, 20, 30])
        p = np.array([12, 22, 28])
        m = compute_regression_metrics(a, p)
        assert "mae" in m
        assert "rmse" in m
        assert "mape" in m
        assert "smape" in m
        assert "wape" in m

    def test_classification_metrics(self):
        actual = np.array(["A", "B", "A", "B", "A"])
        pred = np.array(["A", "B", "A", "A", "A"])
        m = compute_classification_metrics(actual, pred)
        assert m["accuracy"] == pytest.approx(0.8, abs=0.01)
        assert "precision" in m
        assert "recall" in m
        assert "f1" in m

    def test_time_series_splitter(self):
        dates = pd.date_range("2025-01-01", periods=52, freq="W")
        splitter = TimeSeriesSplitter(n_splits=3, min_train_periods=20, val_periods=4)
        folds = splitter.split(dates, freq="W")

        assert len(folds) > 0
        for fold in folds:
            # Training set must come before validation in time
            assert fold.train_end <= fold.val_start
            assert max(fold.train_indices) < min(fold.val_indices)

    def test_prediction_intervals(self):
        bt = BacktestResult(
            model_name="test",
            n_folds=3,
            fold_metrics=[],
            aggregate_metrics={},
            actuals=[100, 110, 90, 105],
            predictions=[95, 115, 88, 100],
        )
        lower, upper = compute_prediction_intervals(bt, 100, confidence=0.9)
        assert lower < 100
        assert upper > 100

    def test_empty_backtest_intervals(self):
        bt = BacktestResult(model_name="test", n_folds=0, fold_metrics=[], aggregate_metrics={})
        lower, upper = compute_prediction_intervals(bt, 100)
        assert lower == 80.0
        assert upper == 120.0


# ─────────────────────────────────────────────────────────────────────
# Registry Tests
# ─────────────────────────────────────────────────────────────────────

class TestModelRegistry:
    def test_register_and_lookup(self):
        registry = ModelRegistry()
        meta = ModelMetadata(
            model_name="demand_forecaster",
            model_version="1.0",
            model_type="gradient_boosting",
            status=ModelStatus.EVALUATED,
        )
        registry.register(meta)

        found = registry.get("demand_forecaster", "1.0")
        assert found is not None
        assert found.model_name == "demand_forecaster"

    def test_lookup_latest(self):
        registry = ModelRegistry()
        registry.register(ModelMetadata("m1", "1.0", "rf", ModelStatus.TRAINED))
        registry.register(ModelMetadata("m1", "2.0", "gbr", ModelStatus.EVALUATED))

        found = registry.get("m1")
        assert found.model_version == "2.0"

    def test_list_models(self):
        registry = ModelRegistry()
        registry.register(ModelMetadata("a", "1.0", "rf", ModelStatus.TRAINED))
        registry.register(ModelMetadata("b", "1.0", "gbr", ModelStatus.TRAINED))
        assert registry.model_count == 2
        assert len(registry.list_models()) == 2

    def test_to_dict(self):
        registry = ModelRegistry()
        registry.register(ModelMetadata("a", "1.0", "rf", ModelStatus.TRAINED, metrics={"mae": 5.0}))
        d = registry.to_dict()
        assert d["total_models"] == 1
        assert d["models"][0]["metrics"]["mae"] == 5.0

    def test_empty_registry(self):
        registry = ModelRegistry()
        assert registry.model_count == 0
        assert registry.get("nonexistent") is None
