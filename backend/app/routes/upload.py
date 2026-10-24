"""
Dataset Upload & Lifecycle Management Routes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.database.models import Dataset, DatasetSnapshot, User
from backend.app.schemas.upload import DatasetSummaryResponse, DatasetUploadResponse, DatasetDetailResponse
from backend.app.services.auth_service import require_current_user
from backend.app.services.tenant_service import get_user_dataset
from backend.app.services.upload_service import save_upload_file
from backend.app.services.processing_service import process_and_persist_dataset

router = APIRouter(prefix="/datasets", tags=["Dataset Ingestion & Management"])


@router.post("/upload", response_model=DatasetUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_and_process_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """
    Upload a raw clothing sales dataset (CSV / XLSX), execute the full Data Engine
    pipeline (cleaning, apparel normalization, anomaly diagnostics, trust scoring),
    and persist results.
    """
    saved_path, file_size, file_ext = save_upload_file(file)

    try:
        dataset = process_and_persist_dataset(
            db=db,
            file_path=str(saved_path),
            filename=file.filename or "uploaded_data",
            file_size_bytes=file_size,
            file_extension=file_ext,
            user=current_user,
        )

        trust_summary = None
        if dataset.trust_score:
            trust_summary = {
                "composite_score": dataset.trust_score.composite_score,
                "trust_level": dataset.trust_score.trust_level,
                "assessment": dataset.trust_score.assessment,
            }

        return DatasetUploadResponse(
            dataset_id=dataset.id,
            filename=dataset.filename,
            status=dataset.status,
            message="Dataset uploaded, cleaned, and analyzed successfully.",
            trust_score=trust_summary,
            processing_time_ms=dataset.processing_time_ms,
            rows_received=dataset.rows_received,
            rows_cleaned=dataset.rows_cleaned,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data processing failed: {str(exc)}",
        )


@router.get("/", response_model=List[DatasetSummaryResponse])
def list_datasets(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """List all uploaded datasets with processing status and row metrics strictly for the authenticated tenant."""
    query = db.query(Dataset)
    if current_user.role == "admin":
        pass
    elif current_user.organization_id:
        query = query.filter(Dataset.organization_id == current_user.organization_id)
    else:
        query = query.filter(Dataset.user_id == current_user.id)

    datasets = query.order_by(Dataset.created_at.desc()).offset(skip).limit(limit).all()
    return datasets


@router.get("/{dataset_id}", response_model=DatasetDetailResponse)
def get_dataset_details(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """Retrieve complete intelligence snapshot for a dataset strictly owned by the caller."""
    dataset = get_user_dataset(db, dataset_id, current_user)

    result_data = dataset.snapshot.get_result() if dataset.snapshot else None
    trust_dict = None
    if dataset.trust_score:
        trust_dict = {
            "composite_score": dataset.trust_score.composite_score,
            "trust_level": dataset.trust_score.trust_level,
            "completeness": dataset.trust_score.completeness_score,
            "validity": dataset.trust_score.validity_score,
            "consistency": dataset.trust_score.consistency_score,
            "timeliness": dataset.trust_score.timeliness_score,
            "uniqueness": dataset.trust_score.uniqueness_score,
            "assessment": dataset.trust_score.assessment,
        }

    return DatasetDetailResponse(
        dataset_id=dataset.id,
        filename=dataset.filename,
        status=dataset.status,
        rows_received=dataset.rows_received,
        rows_cleaned=dataset.rows_cleaned,
        created_at=dataset.created_at,
        trust_score=trust_dict,
        result=result_data,
    )


@router.get("/{dataset_id}/result")
def get_dataset_result(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """Retrieve raw engine result dictionary directly for caller's dataset."""
    dataset = get_user_dataset(db, dataset_id, current_user)
    if not dataset.snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Result snapshot for dataset {dataset_id} not found.",
        )
    return dataset.snapshot.get_result()


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """Delete a dataset record, snapshot, and associated file storage strictly for caller's dataset."""
    dataset = get_user_dataset(db, dataset_id, current_user)

    # Remove file from disk
    try:
        Path(dataset.file_path).unlink(missing_ok=True)
    except Exception:
        pass

    db.delete(dataset)
    db.commit()
    return None
