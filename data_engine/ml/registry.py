"""
TrendPulse ML Model Registry — Lightweight In-Memory Tracking.

Tracks all models trained during a dataset processing run:
    - model name, version, type, status
    - training metadata (timestamp, data range, samples, features)
    - evaluation metrics
    - hyperparameters

Design rules:
    - In-memory only (no database persistence yet).
    - JSON-serializable for API responses.
    - Thread-safe for future async usage.
    - Each processor run gets its own registry instance.
"""

from __future__ import annotations

import threading
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from data_engine.ml.contracts import ModelMetadata, _convert_numpy


class ModelRegistry:
    """
    In-memory registry tracking all ML models trained during a pipeline run.

    Usage::

        registry = ModelRegistry()
        registry.register(model.get_metadata())
        registry.register(another_model.get_metadata())

        # API serialization
        summary = registry.to_dict()
    """

    def __init__(self):
        self._models: Dict[str, ModelMetadata] = {}
        self._lock = threading.Lock()

    def register(self, metadata: ModelMetadata) -> None:
        """Register a trained model's metadata."""
        key = f"{metadata.model_name}:{metadata.model_version}"
        with self._lock:
            self._models[key] = metadata

    def get(self, model_name: str, model_version: str = "") -> Optional[ModelMetadata]:
        """Look up a model by name and optional version."""
        with self._lock:
            if model_version:
                return self._models.get(f"{model_name}:{model_version}")
            # Return latest version for the model name
            matches = [
                v for k, v in self._models.items()
                if k.startswith(f"{model_name}:")
            ]
            return matches[-1] if matches else None

    def list_models(self) -> List[ModelMetadata]:
        """Return all registered models."""
        with self._lock:
            return list(self._models.values())

    @property
    def model_count(self) -> int:
        with self._lock:
            return len(self._models)

    def to_dict(self) -> Dict[str, Any]:
        """JSON-safe dictionary for API responses."""
        models = self.list_models()
        return _convert_numpy({
            "total_models": len(models),
            "models": [m.to_dict() for m in models],
        })

    def summary(self) -> List[Dict[str, Any]]:
        """Compact summary of all registered models."""
        return [
            {
                "model_name": m.model_name,
                "model_version": m.model_version,
                "model_type": m.model_type,
                "status": m.status,
                "n_features": m.n_features,
                "n_training_samples": m.n_training_samples,
                "metrics": m.metrics,
            }
            for m in self.list_models()
        ]
