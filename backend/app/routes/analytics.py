"""
Analytics & Diagnostic Intelligence API Routes.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.database.models import Dataset, User
from backend.app.services.auth_service import require_current_user
from backend.app.services.tenant_service import get_user_dataset

router = APIRouter(prefix="/analytics", tags=["Analytics & Diagnostic Intelligence"])


def _get_dataset_snapshot(dataset_id: int, db: Session, current_user: User) -> Dict[str, Any]:
    """Helper to fetch and parse snapshot payload strictly validating tenant ownership."""
    dataset = get_user_dataset(db, dataset_id, current_user)
    if not dataset.snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No intelligence snapshot available for dataset ID {dataset_id}.",
        )
    return dataset.snapshot.get_result()


@router.get("/{dataset_id}/trust-score")
def get_trust_score(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """Retrieve 5-dimension Data Trust Score and quality assessment."""
    result = _get_dataset_snapshot(dataset_id, db, current_user)
    return result.get("trust_score", {})


@router.get("/{dataset_id}/revenue-decomposition")
def get_revenue_decomposition(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """Retrieve Price-Volume-Mix (PVM) mathematical variance decomposition."""
    result = _get_dataset_snapshot(dataset_id, db, current_user)
    return result.get("revenue_decomposition", {})


@router.get("/{dataset_id}/performance-drivers")
def get_performance_drivers(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """Retrieve top growth contributors, revenue drags, and Pareto 80/20 concentration."""
    result = _get_dataset_snapshot(dataset_id, db, current_user)
    return result.get("performance_drivers", {})


@router.get("/{dataset_id}/customer-analytics")
def get_customer_analytics(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """Retrieve repeat purchase rates, order frequencies, and RFM cohort segmentation."""
    result = _get_dataset_snapshot(dataset_id, db, current_user)
    return result.get("customer_analytics", {})


@router.get("/{dataset_id}/product-affinity")
def get_product_affinity(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """Retrieve market basket co-purchases, Support, Confidence, and Lift metrics."""
    result = _get_dataset_snapshot(dataset_id, db, current_user)
    return result.get("product_affinity", {})


@router.get("/{dataset_id}/period-comparison")
def get_period_comparison(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """Retrieve Week-over-Week and Month-over-Month comparative metrics."""
    result = _get_dataset_snapshot(dataset_id, db, current_user)
    return result.get("period_comparison", {})


@router.get("/{dataset_id}/time-series")
def get_time_series(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """Retrieve multi-grain weekly/monthly trends and day-of-week retail seasonality."""
    result = _get_dataset_snapshot(dataset_id, db, current_user)
    return result.get("time_aggregation", {})


@router.get("/{dataset_id}/anomalies")
def get_anomaly_diagnostics(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """Retrieve detected anomalies with root-cause diagnostic classifications."""
    result = _get_dataset_snapshot(dataset_id, db, current_user)
    return {
        "anomaly_summary": result.get("anomaly_summary", {}),
        "anomaly_diagnostics": result.get("anomaly_diagnostics", {}),
        "anomalies": result.get("anomalies", []),
    }
