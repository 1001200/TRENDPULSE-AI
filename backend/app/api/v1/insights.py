from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from backend.app.db.session import get_db
from backend.app.insights.engine import compute_seller_insights

router = APIRouter()


@router.get("", summary="Get Objective Seller Business Insights")
def get_insights(
    period: Optional[str] = Query("all", description="Period filter: all, this_month, last_month, 3m, 6m"),
    category: Optional[str] = Query(None, description="Category filter (e.g. Tops, Outerwear)"),
    db: Session = Depends(get_db)
):
    """
    Returns objective, mathematical answers to what is actually happening
    in the seller's business across:
    Sales, Time, Products, Clothing Preferences, Customer Behavior, Instagram Attribution, and Trends.
    """
    return compute_seller_insights(db, period=period, category_filter=category)


@router.get("/predictions", summary="Get ML-Powered Predictions & Business Recommendations")
def get_predictions(db: Session = Depends(get_db)):
    """
    Returns mathematical sales forecasts, slow-selling product risks,
    category growth velocity, and evidence-backed actionable recommendations.
    """
    from backend.app.ml import get_business_predictions
    return get_business_predictions(db)
