"""
Pydantic Schemas for Dataset Uploads & Processing Job Status.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class DatasetSummaryResponse(BaseModel):
    id: int
    filename: str
    file_size_bytes: int
    file_extension: str
    status: str
    rows_received: int
    rows_cleaned: int
    processing_time_ms: float
    created_at: datetime
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DatasetUploadResponse(BaseModel):
    dataset_id: int
    filename: str
    status: str
    message: str
    trust_score: Optional[Dict[str, Any]] = None
    processing_time_ms: float
    rows_received: int
    rows_cleaned: int


class DatasetDetailResponse(BaseModel):
    id: int
    filename: str
    status: str
    rows_received: int
    rows_cleaned: int
    processing_time_ms: float
    created_at: datetime
    trust_score: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
