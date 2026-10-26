from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from backend.app.db.session import get_db, Base, engine
from backend.app.models.models import BusinessProfile

router = APIRouter()

# Ensure table exists
Base.metadata.create_all(bind=engine)


class ProfileUpdateRequest(BaseModel):
    business_name: Optional[str] = None
    instagram_handle: Optional[str] = None
    currency: Optional[str] = None
    account_type: Optional[str] = None


@router.get("", summary="Get Authenticated Business Profile")
def get_business_profile(db: Session = Depends(get_db)):
    """
    Returns the business profile for the authenticated business account.
    If not yet initialized, creates and returns the default profile ('Studio Atelier').
    Neutral fallback 'My Business' is used if business_name is empty.
    """
    profile = db.query(BusinessProfile).filter_by(business_id="default_business").first()
    if not profile:
        profile = BusinessProfile(
            business_id="default_business",
            business_name="Studio Atelier",
            instagram_handle="@studio.atelier",
            account_type="Business Account",
            currency="₹ INR (Indian Rupee)"
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return {
        "business_id": profile.business_id,
        "business_name": profile.business_name or "My Business",
        "instagram_handle": profile.instagram_handle or "@store",
        "account_type": profile.account_type or "Business Account",
        "currency": profile.currency or "₹ INR (Indian Rupee)",
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None
    }


@router.post("", summary="Update Authenticated Business Profile")
def update_business_profile(req: ProfileUpdateRequest, db: Session = Depends(get_db)):
    """
    Updates the business name, instagram handle, or settings for the business account.
    """
    profile = db.query(BusinessProfile).filter_by(business_id="default_business").first()
    if not profile:
        profile = BusinessProfile(business_id="default_business")
        db.add(profile)

    if req.business_name is not None:
        name_clean = req.business_name.strip()
        profile.business_name = name_clean if name_clean else "My Business"
    if req.instagram_handle is not None:
        profile.instagram_handle = req.instagram_handle.strip()
    if req.currency is not None:
        profile.currency = req.currency.strip()
    if req.account_type is not None:
        profile.account_type = req.account_type.strip()

    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)

    return {
        "success": True,
        "business_id": profile.business_id,
        "business_name": profile.business_name,
        "instagram_handle": profile.instagram_handle,
        "account_type": profile.account_type,
        "currency": profile.currency,
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None
    }
