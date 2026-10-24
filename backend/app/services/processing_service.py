"""
TrendPulse Processing Service.

Bridges FastAPI endpoints with the core Data Engine processing pipeline.
Executes data cleaning, apparel normalization, anomaly diagnostics,
multi-dimensional trust scoring, and persists snapshots to the database.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from backend.app.database.models import Dataset, DatasetTrustScore, DatasetSnapshot, User
from data_engine.processor import process_file, _json_safe


def process_and_persist_dataset(
    db: Session,
    file_path: str,
    filename: str,
    file_size_bytes: int,
    file_extension: str,
    user: Optional[User] = None,
) -> Dataset:
    """
    Run data engine processing pipeline on uploaded file and save all intelligence records.
    """
    # 1. Create initial pending record
    dataset = Dataset(
        user_id=user.id if user else None,
        organization_id=user.organization_id if user else None,
        filename=filename,
        file_path=str(file_path),
        file_size_bytes=file_size_bytes,
        file_extension=file_extension,
        status="processing",
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    start_time = time.perf_counter()

    try:
        # 2. Execute Data Engine Pipeline
        engine_result = process_file(file_path, enable_llm=False)

        processing_duration_ms = (time.perf_counter() - start_time) * 1000.0

        # 3. Update Dataset Status & Metrics
        dataset.status = "completed"
        dataset.rows_received = engine_result.get("rows_received", 0)
        dataset.rows_cleaned = engine_result.get("rows_after_cleaning", 0)
        dataset.processing_time_ms = round(processing_duration_ms, 2)

        # 4. Save Trust Score Record
        trust_data = engine_result.get("trust_score", {})
        if trust_data:
            dims = trust_data.get("dimensions", {})
            trust_record = DatasetTrustScore(
                dataset_id=dataset.id,
                composite_score=trust_data.get("composite_score", 0.0),
                trust_level=trust_data.get("trust_level", "low"),
                completeness_score=dims.get("completeness", {}).get("score", 0.0),
                validity_score=dims.get("validity", {}).get("score", 0.0),
                consistency_score=dims.get("consistency", {}).get("score", 0.0),
                timeliness_score=dims.get("timeliness", {}).get("score", 0.0),
                uniqueness_score=dims.get("uniqueness", {}).get("score", 0.0),
                assessment=trust_data.get("assessment", ""),
            )
            db.add(trust_record)

        # 5. Save Full Intelligence Snapshot
        # Clean dataframe is not JSON serializable, so extract serializable fields
        snapshot_dict = {k: v for k, v in engine_result.items() if k != "processed_data"}
        snapshot = DatasetSnapshot(
            dataset_id=dataset.id,
            result_json=json.dumps(_json_safe(snapshot_dict)),
        )
        db.add(snapshot)

        db.commit()
        db.refresh(dataset)
        return dataset

    except Exception as exc:
        db.rollback()
        dataset.status = "failed"
        dataset.error_message = str(exc)
        db.commit()
        db.refresh(dataset)
        raise exc
