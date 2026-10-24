"""
Social-First & Viral Thrift Curation API Routes.
"""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.database.models import Dataset

router = APIRouter(prefix="/social", tags=["Social-First & Thrift Curation Intelligence"])


def _get_social_intel(dataset_id: int, db: Session) -> Dict[str, Any]:
    """Helper to fetch social curation intelligence payload."""
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
    return res.get("social_curation", {})


@router.get("/{dataset_id}/aesthetics")
def get_aesthetic_velocity(dataset_id: int, db: Session = Depends(get_db)):
    """Retrieve viral micro-trend aesthetic classifications (Y2K, 90s Grunge, Gorpcore) and velocity."""
    intel = _get_social_intel(dataset_id, db)
    return intel.get("aesthetic_velocity", {})


@router.get("/{dataset_id}/drop-velocity")
def get_drop_velocity(dataset_id: int, db: Session = Depends(get_db)):
    """Retrieve drop clearance speed, first 24-48h flash sell-out score, and drop health grade."""
    intel = _get_social_intel(dataset_id, db)
    return intel.get("drop_velocity", {})


@router.get("/{dataset_id}/sourcing-recommendations")
def get_sourcing_recommendations(dataset_id: int, db: Session = Depends(get_db)):
    """Retrieve actionable 'What to Thrift / Source Next' procurement checklist and Lot ROI multiple."""
    intel = _get_social_intel(dataset_id, db)
    return intel.get("sourcing_recommendations", {})


@router.get("/{dataset_id}/attribution")
def get_social_attribution(dataset_id: int, db: Session = Depends(get_db)):
    """Retrieve revenue and conversion velocity mapped to Instagram Reels, Stories, TikTok, and WhatsApp."""
    intel = _get_social_intel(dataset_id, db)
    return intel.get("social_attribution", {})
