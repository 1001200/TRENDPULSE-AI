"""
Fashion Unit Economics & Inventory Health API Routes.
"""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.database.models import Dataset

router = APIRouter(prefix="/economics", tags=["Fashion Unit Economics & Inventory Health"])


def _get_economics_intel(dataset_id: int, db: Session) -> Dict[str, Any]:
    """Helper to fetch fashion economics payload."""
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
    return res.get("fashion_economics", {})


@router.get("/{dataset_id}/margins")
def get_unit_economics_margins(dataset_id: int, db: Session = Depends(get_db)):
    """Retrieve SKU and category gross profit margins, COGS, and markdown/discount bleed."""
    intel = _get_economics_intel(dataset_id, db)
    return intel.get("unit_economics", {})


@router.get("/{dataset_id}/profitability-matrix")
def get_profitability_matrix(dataset_id: int, db: Session = Depends(get_db)):
    """Retrieve 4-Quadrant portfolio ranking: Stars, Cash Cows, Hidden Gems, and Value Destroyers."""
    intel = _get_economics_intel(dataset_id, db)
    ue = intel.get("unit_economics", {})
    return ue.get("profitability_quadrants", {})


@router.get("/{dataset_id}/inventory-health")
def get_inventory_health(dataset_id: int, db: Session = Depends(get_db)):
    """Retrieve Sell-Through Rates (STR), Weeks of Supply (WOS), and Days of Inventory (DOI)."""
    intel = _get_economics_intel(dataset_id, db)
    return intel.get("inventory_health", {})


@router.get("/{dataset_id}/stockout-alerts")
def get_stockout_alerts(dataset_id: int, db: Session = Depends(get_db)):
    """Retrieve critical stockout risk warnings and smart reorder quantities."""
    intel = _get_economics_intel(dataset_id, db)
    inv = intel.get("inventory_health", {})
    return {
        "critical_stockouts_count": inv.get("critical_stockouts_count", 0),
        "stockout_risk_alerts": inv.get("stockout_risk_alerts", []),
        "overstock_alerts": inv.get("overstock_alerts", []),
    }
