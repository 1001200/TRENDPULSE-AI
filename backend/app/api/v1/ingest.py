import csv
import io
import json
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from backend.app.db.session import get_db
from backend.app.pipeline.normalizer import process_and_normalize_records
from backend.app.pipeline.extractors import (
    detect_file_format,
    extract_csv,
    extract_excel,
    extract_pdf,
    extract_docx,
    extract_txt,
    extract_image
)
from backend.app.pipeline.staging import (
    analyze_uploaded_files,
    update_staged_batch,
    commit_staged_batch,
    get_staged_session
)
from backend.app.models.models import (
    DataQualityLog, Product, SaleOrder, InventoryItem,
    ContentItem, CustomerInquiry
)
from backend.app.api.v1.sample_data import SAMPLE_THRIFT_DATA

router = APIRouter()


class StageUpdatePayload(BaseModel):
    session_id: str
    exclude_row_ids: Optional[List[str]] = None
    include_row_ids: Optional[List[str]] = None
    accept_issue_ids: Optional[List[str]] = None
    exclude_issue_ids: Optional[List[str]] = None
    cell_edits: Optional[List[Dict[str, Any]]] = None
    bulk_action: Optional[str] = None


class ConfirmImportPayload(BaseModel):
    session_id: str


@router.post("/analyze", summary="Analyze Uploaded Files and Detect Data Quality Issues")
async def analyze_files(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Accepts single or multiple files (CSV, XLS, XLSX, PDF, DOCX, TXT, PNG, JPG, JPEG, WebP),
    extracts tabular content, detects column schemas and record types, identifies duplicates,
    missing values, formatting inconsistencies, and prepares staged data for seller review.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    files_payload = []
    for f in files:
        content = await f.read()
        files_payload.append((f.filename, content))

    try:
        result = analyze_uploaded_files(files_payload, db)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing uploaded files: {str(e)}")


@router.post("/stage-update", summary="Update Staged Data Quality Actions & Cell Edits")
def update_staging(
    payload: StageUpdatePayload,
    db: Session = Depends(get_db)
):
    """
    Applies seller corrections, row exclusions/inclusions, and batch approvals
    to the active staged session before final import.
    """
    try:
        result = update_staged_batch(payload.session_id, payload.dict(exclude_unset=True))
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update staged batch: {str(e)}")


@router.get("/stage/{session_id}", summary="Get Staged Session State")
def get_staging_status(session_id: str):
    """Retrieves current staging state, preview rows, and issues list."""
    session = get_staged_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Staging session not found or expired.")
    return {
        "success": True,
        "session_id": session_id,
        "files": session["files"],
        "summary": session["summary"],
        "issues": session["issues"],
        "preview_rows": session["cleaned_rows"][:100],
        "total_preview_count": len(session["cleaned_rows"])
    }


@router.post("/confirm-import", summary="Confirm & Commit Validated Records to Database")
def confirm_import(
    payload: ConfirmImportPayload,
    db: Session = Depends(get_db)
):
    """
    Commits approved cleaned records into the database within an atomic transaction.
    Guarantees no partial corruption or silent duplication.
    """
    try:
        result = commit_staged_batch(payload.session_id, db)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database import failed: {str(e)}")


@router.post("/upload", summary="Upload & Ingest Retail Data File (Direct Ingestion)")
async def upload_file_direct(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Backward-compatible direct upload supporting CSV, XLSX, XLS, PDF, DOCX, TXT, and Images.
    Extracts records, cleans formatting, logs mutations, and persists directly.
    """
    filename = file.filename
    content = await file.read()

    try:
        fmt = detect_file_format(filename, content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    rows = []
    try:
        if fmt == "csv":
            _, rows, _ = extract_csv(content)
        elif fmt in ("xlsx", "xls"):
            _, rows, _ = extract_excel(content, is_xls=(fmt == "xls"))
        elif fmt == "pdf":
            _, rows, _, _ = extract_pdf(content)
        elif fmt == "docx":
            _, rows, _, _ = extract_docx(content)
        elif fmt == "txt":
            _, rows, _ = extract_txt(content)
        elif fmt in ("png", "jpg", "jpeg", "webp"):
            _, rows, _, _ = extract_image(content, filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Extraction failed: {str(e)}")

    if not rows:
        raise HTTPException(status_code=400, detail=f"No readable business records could be extracted from '{filename}'.")

    summary, saved_count = process_and_normalize_records(rows, db, source_name=file.filename)
    return {
        "success": True,
        "message": f"Successfully ingested {saved_count} standardized records from {file.filename}",
        "summary": summary
    }


@router.post("/sample", summary="Load Sample Instagram Thrift Data")
def load_sample_thrift_data(db: Session = Depends(get_db)):
    """
    Populates the database with realistic sample Instagram thrift / resale store records,
    demonstrating column detection, non-destructive cleaning, and business insights.
    """
    # Clear existing data to load clean sample batch
    db.query(CustomerInquiry).delete()
    db.query(SaleOrder).delete()
    db.query(InventoryItem).delete()
    db.query(ContentItem).delete()
    db.query(Product).delete()
    db.query(DataQualityLog).delete()
    db.commit()

    summary, count = process_and_normalize_records(
        SAMPLE_THRIFT_DATA, db, source_name="Sample_Instagram_Thrift_Log.csv"
    )
    return {
        "success": True,
        "message": f"Loaded {count} sample thrift items with non-destructive audit log.",
        "summary": summary
    }


@router.get("/stats", summary="Get Database Record Counts")
def get_ingestion_stats(db: Session = Depends(get_db)):
    """Returns counts of all entities in the database."""
    return {
        "products": db.query(Product).count(),
        "sales": db.query(SaleOrder).count(),
        "content_items": db.query(ContentItem).count(),
        "inquiries": db.query(CustomerInquiry).count(),
        "inventory_items": db.query(InventoryItem).count(),
        "quality_logs": db.query(DataQualityLog).count(),
        "has_data": db.query(Product).count() > 0
    }


@router.delete("/reset", summary="Reset All Data")
def reset_all_data(db: Session = Depends(get_db)):
    """Clears all data from the database for a fresh start."""
    db.query(CustomerInquiry).delete()
    db.query(SaleOrder).delete()
    db.query(InventoryItem).delete()
    db.query(ContentItem).delete()
    db.query(Product).delete()
    db.query(DataQualityLog).delete()
    db.commit()
    return {
        "success": True,
        "message": "All data has been cleared. You can now upload fresh data or load sample data."
    }


@router.get("/history", summary="Get Data Quality & Ingestion History")
def get_ingestion_history(db: Session = Depends(get_db)):
    """Returns past ingestion logs and quality health scores."""
    logs = db.query(DataQualityLog).order_by(DataQualityLog.uploaded_at.desc()).all()
    return [
        {
            "batch_id": log.batch_id,
            "uploaded_at": log.uploaded_at.isoformat(),
            "source_name": log.source_name,
            "total_rows": log.total_rows,
            "valid_rows": log.valid_rows,
            "flagged_rows": log.flagged_rows,
            "skipped_rows": log.skipped_rows,
            "mutations_count": log.mutations_count,
            "info_count": log.info_count,
            "warning_count": log.warning_count,
            "error_count": log.error_count,
            "quality_score": log.quality_score,
            "cleaning_rules_applied": log.cleaning_rules_applied,
            "audit_trail": log.audit_trail_json
        }
        for log in logs
    ]
