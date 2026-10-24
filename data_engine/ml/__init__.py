"""
TrendPulse ML Engine — Predictive & Decision Intelligence Layer.

Sits on top of the existing data engine and transforms TrendPulse from
a diagnostic analytics platform into an autonomous predictive decision engine.

Architecture:
    EXISTING DATA ENGINE → FEATURE ENGINE → ML ENGINE → SYNTHESIS → DECISION CENTER

Modules:
    contracts      : BaseModel ABC, Prediction, ModelMetadata, enums
    feature_store  : Centralized leakage-safe feature engineering
    evaluation     : Time-series splitting, backtesting, metrics
    registry       : In-memory model tracking
    forecasting/   : Demand forecasting (baseline + GBR auto-select)
    product/       : Product lifecycle classification (6-stage)
    inventory/     : Stockout prediction & replenishment simulation
    pricing/       : Price elasticity & markdown optimization
    customer/      : Customer churn risk & repurchase survival timing
    decision/      : Autonomous decision center (threats, opportunities, actions)
"""

from __future__ import annotations

import pandas as pd

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
    BacktestResult,
    BacktestRunner,
    TimeSeriesSplitter,
    compute_regression_metrics,
    compute_classification_metrics,
    compute_prediction_intervals,
)
from data_engine.ml.registry import ModelRegistry
from data_engine.ml.forecasting import DemandForecaster
from data_engine.ml.product import LifecycleClassifier
from data_engine.ml.inventory import StockoutPredictor
from data_engine.ml.pricing import PriceElasticityOptimizer
from data_engine.ml.customer import CustomerPredictor
from data_engine.ml.decision import DecisionEngine


def run_ml_intelligence(
    df: pd.DataFrame,
    *,
    horizon_days: int = 30,
    include_sizes: bool = True,
) -> dict:
    """
    Run the complete All-in-One ML intelligence suite on an enriched DataFrame.

    Orchestrates:
        1. Demand Forecaster (Size-curve aware, auto-selected)
        2. Lifecycle Classifier (6-stage apparel trajectory)
        3. Stockout Predictor (Depletion simulation & replenishment)
        4. Price Elasticity Optimizer (Log-log elasticity & markdowns)
        5. Customer Predictor (Churn risk & repurchase survival)
        6. Autonomous Decision Engine (Synthesis into ranked threats & opportunities)

    Failures are safely isolated via try/except so ML errors NEVER break
    core data cleaning or descriptive analytics.
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return {
            "status": "no_data",
            "message": "DataFrame is empty — ML models require data.",
            "demand_forecast": [],
            "product_lifecycle": [],
            "stockout_predictions": [],
            "price_elasticity": [],
            "customer_predictions": [],
            "decision_center": {},
            "model_registry": {"total_models": 0, "models": []},
        }

    registry = ModelRegistry()
    result = {
        "status": "success",
        "demand_forecast": [],
        "product_lifecycle": [],
        "stockout_predictions": [],
        "price_elasticity": [],
        "customer_predictions": [],
        "decision_center": {},
        "model_registry": {},
    }

    # Helper collectors for downstream synthesis
    demand_pred_objects: List[Prediction] = []
    lifecycle_pred_objects: List[Prediction] = []
    stockout_pred_objects: List[Prediction] = []
    pricing_pred_objects: List[Prediction] = []
    customer_pred_objects: List[Prediction] = []

    # ── 1. Demand Forecasting ────────────────────────────────────
    try:
        forecaster = DemandForecaster(horizon_days=horizon_days)
        forecaster.fit(df)
        if forecaster.is_fitted:
            demand_pred_objects = forecaster.predict(df, include_sizes=include_sizes)
            result["demand_forecast"] = [p.to_dict() for p in demand_pred_objects]
            registry.register(forecaster.get_metadata())
        else:
            result["demand_forecast"] = [insufficient_data_result(
                "demand_forecaster",
                "Insufficient historical data for demand forecasting.",
                "At least 8 weeks of sales history.",
            )]
    except Exception as exc:
        result["demand_forecast"] = [{
            "status": "model_error",
            "model": "demand_forecaster",
            "error": str(exc),
        }]

    # ── 2. Product Lifecycle Classification ──────────────────────
    try:
        lifecycle = LifecycleClassifier()
        lifecycle.fit(df)
        if lifecycle.is_fitted:
            lifecycle_pred_objects = lifecycle.predict(df)
            result["product_lifecycle"] = [p.to_dict() for p in lifecycle_pred_objects]
            registry.register(lifecycle.get_metadata())
        else:
            result["product_lifecycle"] = [insufficient_data_result(
                "lifecycle_classifier",
                "Insufficient product data for lifecycle classification.",
            )]
    except Exception as exc:
        result["product_lifecycle"] = [{
            "status": "model_error",
            "model": "lifecycle_classifier",
            "error": str(exc),
        }]

    # ── 3. Stockout & Replenishment Simulation ───────────────────
    try:
        stockout = StockoutPredictor(horizon_days=horizon_days)
        stockout.fit(df, demand_predictions=demand_pred_objects)
        if stockout.is_fitted:
            stockout_pred_objects = stockout.predict(df)
            result["stockout_predictions"] = [p.to_dict() for p in stockout_pred_objects]
            registry.register(stockout.get_metadata())
        else:
            result["stockout_predictions"] = [insufficient_data_result(
                "stockout_predictor",
                "Unable to build inventory predictions.",
            )]
    except Exception as exc:
        result["stockout_predictions"] = [{
            "status": "model_error",
            "model": "stockout_predictor",
            "error": str(exc),
        }]

    # ── 4. Price Elasticity & Markdown Optimization ──────────────
    try:
        pricing_opt = PriceElasticityOptimizer()
        pricing_opt.fit(df)
        if pricing_opt.is_fitted:
            pricing_pred_objects = pricing_opt.predict(df, lifecycle_predictions=lifecycle_pred_objects)
            result["price_elasticity"] = [p.to_dict() for p in pricing_pred_objects]
            registry.register(pricing_opt.get_metadata())
        else:
            result["price_elasticity"] = [insufficient_data_result(
                "price_elasticity_optimizer",
                "Insufficient pricing variation to estimate elasticity.",
            )]
    except Exception as exc:
        result["price_elasticity"] = [{
            "status": "model_error",
            "model": "price_elasticity_optimizer",
            "error": str(exc),
        }]

    # ── 5. Customer Churn & Repurchase Prediction ────────────────
    try:
        cust_pred = CustomerPredictor()
        cust_pred.fit(df)
        if cust_pred.is_fitted:
            customer_pred_objects = cust_pred.predict(df)
            result["customer_predictions"] = [p.to_dict() for p in customer_pred_objects]
            registry.register(cust_pred.get_metadata())
        else:
            result["customer_predictions"] = [insufficient_data_result(
                "customer_predictor",
                "No customer identifiers available for retention modeling.",
            )]
    except Exception as exc:
        result["customer_predictions"] = [{
            "status": "model_error",
            "model": "customer_predictor",
            "error": str(exc),
        }]

    # ── 6. Autonomous Decision & Action Center ───────────────────
    try:
        decision_eng = DecisionEngine()
        decision_eng.fit(
            df,
            demand_predictions=demand_pred_objects,
            lifecycle_predictions=lifecycle_pred_objects,
            stockout_predictions=stockout_pred_objects,
            pricing_predictions=pricing_pred_objects,
            customer_predictions=customer_pred_objects,
        )
        if decision_eng.is_fitted:
            result["decision_center"] = decision_eng.get_decision_center()
            registry.register(decision_eng.get_metadata())
        else:
            result["decision_center"] = {
                "status": "insufficient_data",
                "message": "Unable to synthesize decision center.",
            }
    except Exception as exc:
        result["decision_center"] = {
            "status": "model_error",
            "model": "decision_engine",
            "error": str(exc),
        }

    # ── Registry ─────────────────────────────────────────────────
    result["model_registry"] = registry.to_dict()

    return _convert_numpy(result)


__all__ = [
    "run_ml_intelligence",
    "BaseModel",
    "DataLabel",
    "FeatureContribution",
    "FeatureEngineer",
    "FeatureSet",
    "LifecycleStage",
    "ModelMetadata",
    "ModelRegistry",
    "ModelStatus",
    "Prediction",
    "PredictionType",
    "UncertaintyInterval",
    "DemandForecaster",
    "LifecycleClassifier",
    "StockoutPredictor",
    "PriceElasticityOptimizer",
    "CustomerPredictor",
    "DecisionEngine",
    "BacktestResult",
    "BacktestRunner",
    "TimeSeriesSplitter",
    "compute_regression_metrics",
    "compute_classification_metrics",
    "compute_prediction_intervals",
    "insufficient_data_result",
]
