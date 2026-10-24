"""
TrendPulse ML Contracts — Common Interfaces & Data Structures.

Every ML model in TrendPulse MUST implement :class:`BaseModel` and
return :class:`Prediction` objects.  This guarantees uniform contracts
across forecasting, classification, regression, and risk models so that
downstream consumers (API, decision engine, frontend, LLM layer) never
need model-specific deserialization.

Design rules:
    - All contracts are plain dataclasses — no ORM, no heavy frameworks.
    - JSON-serializable via ``asdict()`` + ``_json_safe()``.
    - Enums use string values for human-readable API responses.
    - BaseModel is an ABC — concrete models override abstract methods.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd


# ─────────────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────────────

class PredictionType(str, Enum):
    """Kind of prediction a model produces."""
    DEMAND_FORECAST = "demand_forecast"
    LIFECYCLE_STAGE = "lifecycle_stage"
    STOCKOUT_PROBABILITY = "stockout_probability"
    CHURN_PROBABILITY = "churn_probability"
    REPURCHASE_TIMING = "repurchase_timing"
    PRICE_ELASTICITY = "price_elasticity"
    TREND_TRAJECTORY = "trend_trajectory"
    MARKDOWN_SCHEDULE = "markdown_schedule"
    ACTION_RECOMMENDATION = "action_recommendation"
    BUSINESS_OPPORTUNITY = "business_opportunity"
    BUSINESS_THREAT = "business_threat"


class DataLabel(str, Enum):
    """
    Distinguishes the *source* of a number so downstream consumers
    never confuse a hard fact with a model guess.
    """
    OBSERVED = "observed"
    PREDICTED = "predicted"
    ESTIMATED = "estimated"
    SIMULATED = "simulated"
    RECOMMENDED = "recommended"


class LifecycleStage(str, Enum):
    """Product lifecycle stages for clothing SKUs."""
    NEW = "new"
    EMERGING = "emerging"
    GROWING = "growing"
    MATURE = "mature"
    DECLINING = "declining"
    DEAD = "dead"


class ModelStatus(str, Enum):
    """Current status of a trained model."""
    TRAINED = "trained"
    EVALUATED = "evaluated"
    SELECTED = "selected"
    FAILED = "failed"
    INSUFFICIENT_DATA = "insufficient_data"


# ─────────────────────────────────────────────────────────────────────
# Data Structures
# ─────────────────────────────────────────────────────────────────────

@dataclass
class UncertaintyInterval:
    """Lower/upper bounds for a prediction."""
    lower: float
    upper: float


@dataclass
class FeatureContribution:
    """One feature's contribution to a prediction — for explainability."""
    name: str
    importance: float
    direction: str  # "positive" | "negative" | "neutral"


@dataclass
class Prediction:
    """
    Universal prediction envelope.

    Every ML model in TrendPulse returns a list of these.
    Downstream consumers never need to know which model produced the
    prediction — they only read this contract.
    """
    prediction_id: str
    model_name: str
    model_version: str
    entity_type: str            # "sku", "product", "category", "customer"
    entity_id: str
    prediction_type: str        # PredictionType value
    data_label: str             # DataLabel value — always "predicted"

    # The actual prediction
    value: Any                  # numeric for regression, string for classification
    confidence: float           # 0.0–1.0

    # Optional enrichment
    uncertainty: Optional[UncertaintyInterval] = None
    horizon: Optional[str] = None               # "7_days", "30_days", etc.
    generated_at: str = ""
    valid_until: Optional[str] = None           # staleness boundary
    features_used: List[str] = field(default_factory=list)
    top_features: List[FeatureContribution] = field(default_factory=list)
    model_metrics: Dict[str, float] = field(default_factory=dict)
    evidence: List[str] = field(default_factory=list)
    recommended_action: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now(timezone.utc).isoformat()
        if not self.prediction_id:
            self.prediction_id = uuid.uuid4().hex[:12]

    def to_dict(self) -> Dict[str, Any]:
        """JSON-safe dictionary representation."""
        d = asdict(self)
        # Ensure numpy types are converted
        return _convert_numpy(d)


@dataclass
class ModelMetadata:
    """
    Metadata for a trained model — stored in the ModelRegistry.
    """
    model_name: str
    model_version: str
    model_type: str             # "random_forest", "gradient_boosting", "rule_based", etc.
    status: str                 # ModelStatus value

    training_timestamp: str = ""
    training_data_range: Optional[Dict[str, str]] = None   # {"start": ..., "end": ...}
    feature_names: List[str] = field(default_factory=list)
    target: str = ""
    prediction_horizon: Optional[str] = None
    metrics: Dict[str, float] = field(default_factory=dict)
    n_training_samples: int = 0
    n_features: int = 0
    hyperparameters: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.training_timestamp:
            self.training_timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return _convert_numpy(asdict(self))


# ─────────────────────────────────────────────────────────────────────
# Base Model ABC
# ─────────────────────────────────────────────────────────────────────

class BaseModel(ABC):
    """
    Abstract base for every TrendPulse ML model.

    Concrete models must implement:
        - ``fit(df, **kwargs)``         → train on data
        - ``predict(df, **kwargs)``     → produce ``List[Prediction]``
        - ``get_metadata()``            → return ``ModelMetadata``

    Optional overrides:
        - ``evaluate(df, **kwargs)``    → compute metrics on held-out data
        - ``explain(prediction)``       → enrich a prediction with explainability
    """

    MODEL_NAME: str = "base"
    MODEL_VERSION: str = "1.0"
    MODEL_TYPE: str = "unknown"

    def __init__(self):
        self._is_fitted: bool = False
        self._metadata: Optional[ModelMetadata] = None
        self._feature_names: List[str] = []

    # ── Abstract methods ──────────────────────────────────────────

    @abstractmethod
    def fit(self, df: pd.DataFrame, **kwargs) -> "BaseModel":
        """Train the model. Returns self for chaining."""
        ...

    @abstractmethod
    def predict(self, df: pd.DataFrame, **kwargs) -> List[Prediction]:
        """Generate predictions. Returns list of Prediction objects."""
        ...

    @abstractmethod
    def get_metadata(self) -> ModelMetadata:
        """Return model metadata after training."""
        ...

    # ── Optional overrides ────────────────────────────────────────

    def evaluate(self, df: pd.DataFrame, **kwargs) -> Dict[str, float]:
        """Evaluate model on held-out data. Returns metric dict."""
        return {}

    def explain(self, prediction: Prediction) -> Prediction:
        """Enrich a prediction with top feature contributions."""
        return prediction

    # ── Convenience ───────────────────────────────────────────────

    @property
    def is_fitted(self) -> bool:
        return self._is_fitted

    def _build_metadata(
        self,
        *,
        status: str = ModelStatus.TRAINED,
        metrics: Optional[Dict[str, float]] = None,
        n_training_samples: int = 0,
        training_data_range: Optional[Dict[str, str]] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
        target: str = "",
        prediction_horizon: Optional[str] = None,
    ) -> ModelMetadata:
        """Helper to construct a ModelMetadata from the model's class attrs."""
        self._metadata = ModelMetadata(
            model_name=self.MODEL_NAME,
            model_version=self.MODEL_VERSION,
            model_type=self.MODEL_TYPE,
            status=status,
            feature_names=list(self._feature_names),
            target=target,
            prediction_horizon=prediction_horizon,
            metrics=metrics or {},
            n_training_samples=n_training_samples,
            n_features=len(self._feature_names),
            training_data_range=training_data_range,
            hyperparameters=hyperparameters or {},
        )
        return self._metadata

    def _make_prediction(
        self,
        *,
        entity_type: str,
        entity_id: str,
        prediction_type: str,
        value: Any,
        confidence: float,
        uncertainty: Optional[UncertaintyInterval] = None,
        horizon: Optional[str] = None,
        valid_until: Optional[str] = None,
        evidence: Optional[List[str]] = None,
        recommended_action: Optional[str] = None,
        top_features: Optional[List[FeatureContribution]] = None,
        metadata_extra: Optional[Dict[str, Any]] = None,
    ) -> Prediction:
        """Helper to build a Prediction with model-level defaults."""
        meta = self.get_metadata()
        return Prediction(
            prediction_id=uuid.uuid4().hex[:12],
            model_name=self.MODEL_NAME,
            model_version=self.MODEL_VERSION,
            entity_type=entity_type,
            entity_id=str(entity_id),
            prediction_type=prediction_type,
            data_label=DataLabel.PREDICTED,
            value=value,
            confidence=round(float(confidence), 4),
            uncertainty=uncertainty,
            horizon=horizon,
            valid_until=valid_until,
            features_used=list(meta.feature_names) if meta else [],
            top_features=top_features or [],
            model_metrics=dict(meta.metrics) if meta else {},
            evidence=evidence or [],
            recommended_action=recommended_action,
            metadata=metadata_extra or {},
        )


# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────

def _convert_numpy(obj):
    """Recursively convert numpy types to native Python for JSON safety."""
    if isinstance(obj, dict):
        return {k: _convert_numpy(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_convert_numpy(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj) if not np.isnan(obj) else None
    if isinstance(obj, np.ndarray):
        return _convert_numpy(obj.tolist())
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    try:
        if pd.isna(obj):
            return None
    except (TypeError, ValueError):
        pass
    return obj


def insufficient_data_result(
    model_name: str,
    reason: str,
    minimum_required: str = "",
) -> Dict[str, Any]:
    """
    Standard response when a model cannot produce predictions
    due to insufficient data.  Prefer honest inability over fake intelligence.
    """
    result: Dict[str, Any] = {
        "status": "insufficient_data",
        "model": model_name,
        "reason": reason,
        "predictions": [],
    }
    if minimum_required:
        result["minimum_required"] = minimum_required
    return result
