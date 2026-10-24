"""
TrendPulse AI Fashion Copilot Routes.

Endpoints for instant executive store diagnosis and conversational ChatGPT-style Q&A.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.database.models import Dataset, DatasetSnapshot, User
from backend.app.services.auth_service import require_current_user
from backend.app.services.tenant_service import get_user_dataset
from backend.app.services.ai_advisor import (
    generate_executive_diagnosis,
    answer_merchant_query,
)

router = APIRouter(prefix="/ai", tags=["AI Fashion Advisor"])


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Question from the fashion merchant")


def _get_snapshot_result(dataset_id: int, db: Session, current_user: User) -> Dict[str, Any]:
    dataset = get_user_dataset(db, dataset_id, current_user)
    if not dataset.snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No processed snapshot found for dataset {dataset_id}.",
        )
    return dataset.snapshot.get_result()


@router.get("/diagnosis/{dataset_id}")
def get_executive_diagnosis(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """
    Generate an instant plain-English 60-second store diagnosis:
    where the brand is losing money, where it is winning, and 3 moves for this week.
    Strictly verifies tenant dataset ownership.
    """
    snapshot = _get_snapshot_result(dataset_id, db, current_user)
    return generate_executive_diagnosis(snapshot)


@router.post("/chat/{dataset_id}")
def chat_with_store(
    dataset_id: int,
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """
    Conversational AI Copilot: answer any question about the uploaded sales
    using the actual store numbers in clean plain English.
    Strictly verifies tenant dataset ownership.
    """
    snapshot = _get_snapshot_result(dataset_id, db, current_user)
    return answer_merchant_query(request.query, snapshot)
