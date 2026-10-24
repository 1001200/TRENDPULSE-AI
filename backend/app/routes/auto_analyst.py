"""
AutoAnalyst API Routes.

Exposes endpoints for zero-shot spreadsheet ingestion, real-time autonomous analysis,
sample dataset evaluation, and cleaned dataset export.
"""

from __future__ import annotations

import io
import uuid
from pathlib import Path
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response, StreamingResponse

from backend.app.database.models import User
from backend.app.services.auth_service import require_current_user
from data_engine.auto_analyst.pipeline import AutoAnalystEngine

router = APIRouter(prefix="/analyst", tags=["Automated Insight Analyst Engine"])

# In-memory store for recent analyses (for cleaned CSV downloads)
ANALYSIS_STORE: Dict[str, Dict[str, Any]] = {}


@router.post("/analyze", status_code=status.HTTP_200_OK)
async def analyze_dataset(
    file: Optional[UploadFile] = File(None),
    sample_id: Optional[str] = Query(None, description="Pre-loaded sample: 'healthcare', 'marketing', 'sales'"),
    current_user: User = Depends(require_current_user),
):
    """
    Ingest an arbitrary CSV or Excel file, clean it, execute ML pattern discovery,
    and return an automated dashboard blueprint with executive findings.
    """
    engine = AutoAnalystEngine()
    analysis_id = str(uuid.uuid4())

    try:
        if file and file.filename:
            contents = await file.read()
            result = engine.run(contents, filename=file.filename)
        elif sample_id:
            sample_paths = {
                "healthcare": "data/raw/sample_healthcare_clinic.csv",
                "marketing": "data/raw/sample_marketing_campaigns.csv",
                "sales": "data/raw/urban_strides_apparel_sample.csv",
            }
            if sample_id not in sample_paths:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unknown sample ID '{sample_id}'. Available: {list(sample_paths.keys())}",
                )
            target_path = Path(sample_paths[sample_id])
            if not target_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Sample file {target_path} not found.",
                )
            result = engine.run(target_path, filename=target_path.name)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either an uploaded file or sample_id must be provided.",
            )

        # Separate internal cleaned dataframe for download
        cleaned_df = result.pop("_cleaned_df", None)
        filename = result["metadata"]["filename"]

        # Cache cleaned CSV with user_id
        if cleaned_df is not None:
            csv_buf = io.StringIO()
            cleaned_df.to_csv(csv_buf, index=False)
            ANALYSIS_STORE[analysis_id] = {
                "user_id": current_user.id,
                "filename": filename,
                "csv_data": csv_buf.getvalue(),
                "created_at": result["metadata"]["processed_at"],
            }

        result["analysis_id"] = analysis_id
        return result

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AutoAnalyst processing failed: {str(exc)}",
        )


@router.get("/download-cleaned/{analysis_id}")
def download_cleaned_dataset(
    analysis_id: str,
    current_user: User = Depends(require_current_user),
):
    """Download the cleaned, standardized dataset as CSV strictly verifying user ownership."""
    cached = ANALYSIS_STORE.get(analysis_id)
    if not cached or (cached.get("user_id") and cached.get("user_id") != current_user.id and current_user.role != "admin"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cleaned dataset expired or not found. Please re-run analysis.",
        )

    filename = cached["filename"]
    clean_name = f"cleaned_{Path(filename).stem}.csv"
    csv_bytes = cached["csv_data"].encode("utf-8")

    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{clean_name}"'},
    )
