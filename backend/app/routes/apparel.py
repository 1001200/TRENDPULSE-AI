"""
Apparel & Fashion Domain Intelligence API Routes.
"""

from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.database.models import Dataset

router = APIRouter(prefix="/apparel", tags=["Apparel & Fashion Intelligence"])


def _get_apparel_intel(dataset_id: int, db: Session) -> Dict[str, Any]:
    """Helper to fetch apparel intelligence payload."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID {dataset_id} not found.",
        )
    if not dataset.snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No intelligence snapshot available for dataset ID {dataset_id}.",
        )
    res = dataset.snapshot.get_result()
    return res.get("apparel_intelligence", {})


@router.get("/{dataset_id}")
def get_full_apparel_intelligence(dataset_id: int, db: Session = Depends(get_db)):
    """Retrieve full fashion domain intelligence report."""
    return _get_apparel_intel(dataset_id, db)


@router.get("/{dataset_id}/size-curves")
def get_size_curves(dataset_id: int, db: Session = Depends(get_db)):
    """Retrieve overall catalog and category-level size demand curves."""
    intel = _get_apparel_intel(dataset_id, db)
    return intel.get("size_intelligence", {})


@router.get("/{dataset_id}/broken-size-runs")
def get_broken_size_runs(dataset_id: int, db: Session = Depends(get_db)):
    """Retrieve styles suffering from broken size runs (lost sales in core sizes M/L)."""
    intel = _get_apparel_intel(dataset_id, db)
    return intel.get("broken_size_runs", [])


@router.get("/{dataset_id}/colorways")
def get_colorway_analytics(dataset_id: int, db: Session = Depends(get_db)):
    """Retrieve top colorways and color family palette distributions."""
    intel = _get_apparel_intel(dataset_id, db)
    return intel.get("color_intelligence", {})


@router.get("/{dataset_id}/fits")
def get_fit_intelligence(dataset_id: int, db: Session = Depends(get_db)):
    """Retrieve fit and silhouette popularity ranking (Oversized, Slim, Regular, Cropped)."""
    intel = _get_apparel_intel(dataset_id, db)
    return intel.get("fit_intelligence", [])


@router.get("/{dataset_id}/fabrics")
def get_fabric_intelligence(dataset_id: int, db: Session = Depends(get_db)):
    """Retrieve fabric and material preference distribution."""
    intel = _get_apparel_intel(dataset_id, db)
    return intel.get("fabric_intelligence", [])
