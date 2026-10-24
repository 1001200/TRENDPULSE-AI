"""
Pydantic Schemas for Analytical Endpoints.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class TrustScoreResponse(BaseModel):
    dataset_id: int
    composite_score: float
    trust_level: str
    assessment: str
    dimensions: Dict[str, Any]
    weights: Dict[str, float]


class RevenueDecompositionResponse(BaseModel):
    dataset_id: int
    current_period: str
    previous_period: str
    summary: Dict[str, Any]
    decomposition: Dict[str, Any]
    primary_driver: str
    diagnostic_explanation: str


class ApparelIntelligenceResponse(BaseModel):
    dataset_id: int
    total_apparel_revenue: float
    total_apparel_units: float
    size_intelligence: Dict[str, Any]
    color_intelligence: Dict[str, Any]
    fit_intelligence: List[Dict[str, Any]]
    fabric_intelligence: List[Dict[str, Any]]
    gender_distribution: List[Dict[str, Any]]
    broken_size_runs: List[Dict[str, Any]]
