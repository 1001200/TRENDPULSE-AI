from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.models.models import Product, SaleOrder, ContentItem, CustomerInquiry

router = APIRouter()

@router.get("/health", summary="System Health & Connectivity Check")
def health_check(db: Session = Depends(get_db)):
    """
    Verifies that the backend API is live and the database connection is healthy.
    Includes database record counts for frontend status display.
    """
    db_status = "healthy"
    try:
        # Simple test query to ensure database engine and file/server are reachable
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # Record counts for frontend display
    product_count = 0
    order_count = 0
    try:
        product_count = db.query(Product).count()
        order_count = db.query(SaleOrder).count()
    except Exception:
        pass

    return {
        "status": "ok" if db_status == "healthy" else "degraded",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": db_status,
        "api_v1": settings.API_V1_STR,
        "has_data": product_count > 0,
        "record_counts": {
            "products": product_count,
            "orders": order_count,
        }
    }
