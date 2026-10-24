"""
Data Export & Report Download Routes.
"""

from __future__ import annotations

import io
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse
import pandas as pd
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.database.models import Dataset, User
from backend.app.services.auth_service import require_current_user
from backend.app.services.tenant_service import get_user_dataset
from data_engine.processor import process_file

router = APIRouter(prefix="/export", tags=["Data & Report Exporting"])


@router.get("/{dataset_id}/clean-csv")
def export_clean_csv(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """
    Download the standardized, cleaned, and apparel-enriched dataset as a CSV file.
    Strictly verifies tenant dataset ownership.
    """
    dataset = get_user_dataset(db, dataset_id, current_user)

    # Process file to get the enriched dataframe
    result = process_file(dataset.file_path, enable_llm=False)
    clean_df = result.get("processed_data")

    if not isinstance(clean_df, pd.DataFrame):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate cleaned DataFrame for export.",
        )

    buffer = io.StringIO()
    clean_df.to_csv(buffer, index=False)
    buffer.seek(0)

    clean_filename = f"cleaned_{dataset.filename.rsplit('.', 1)[0]}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={clean_filename}"},
    )


@router.get("/{dataset_id}/report-json")
def export_full_report_json(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """
    Download the full intelligence snapshot JSON report.
    Strictly verifies tenant dataset ownership.
    """
    dataset = get_user_dataset(db, dataset_id, current_user)
    if not dataset.snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Intelligence snapshot for dataset {dataset_id} not found.",
        )

    report_filename = f"trendpulse_report_{dataset.id}.json"
    return Response(
        content=dataset.snapshot.result_json,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={report_filename}"},
    )
