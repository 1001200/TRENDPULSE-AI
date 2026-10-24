"""
TrendPulse Enterprise FastAPI Application.

Main entry point for the clothing data intelligence API.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import settings
from backend.app.database.connection import init_db
from backend.app.routes import (
    auth_router,
    upload_router,
    analytics_router,
    apparel_router,
    export_router,
    social_router,
    economics_router,
    ml_router,
    ai_router,
    drop_public_router,
    drop_seller_router,
    auto_analyst_router,
    business_router,
)


UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup & shutdown events."""
    # Initialize DB tables on startup
    init_db()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
# 👗 TrendPulse Fashion Intelligence & Data Engine API

The specialized AI/ML and business intelligence decision platform built exclusively for the clothing, thrift, and apparel industry.

### Core Capabilities:
* **Audited Data Cleaning & Normalization:** Ingestion of raw merchant CSV/Excel files with cell-level audit tracking.
* **Apparel Domain Normalization:** Automatic standardization of sizes (XS-5XL, 32x30, Free Size), 150+ colorways, and fashion taxonomy attributes.
* **Viral Aesthetic & Social Curation:** Auto-tagging Y2K, 90s Grunge, Gorpcore, Old Money, Drop velocity, and 'What to Thrift Next' sourcing checklists.
* **Unit Economics & Inventory Health:** Gross margins, discount bleed / markdown drag, 4-Quadrant Profitability Matrix, Sell-Through Rates (STR), and Weeks of Supply (WOS).
* **Data Trust Scoring:** 5-dimensional data quality assessment (Completeness, Validity, Consistency, Timeliness, Uniqueness).
* **Diagnostic & Commercial Intelligence:** Price-Volume-Mix (PVM) revenue decomposition, performance drivers, RFM customer cohorts, and basket affinity (Lift/Support).
* **Fashion Intelligence:** Catalog size curves, broken size run stockout alerts, and color family palette distributions.
* **ML Predictive Intelligence:** Demand forecasting (baseline + GBR auto-select), product lifecycle classification (6-stage), and stockout probability predictions with replenishment recommendations.
""",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    """Adds enterprise security headers without disrupting OAuth redirects."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


# Include API v1 Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(upload_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(apparel_router, prefix=settings.API_V1_STR)
app.include_router(export_router, prefix=settings.API_V1_STR)
app.include_router(social_router, prefix=settings.API_V1_STR)
app.include_router(economics_router, prefix=settings.API_V1_STR)
app.include_router(ml_router)
app.include_router(ai_router, prefix=settings.API_V1_STR)
app.include_router(drop_public_router, prefix=settings.API_V1_STR)
app.include_router(drop_seller_router, prefix=settings.API_V1_STR)
app.include_router(drop_public_router, prefix="/api")
app.include_router(drop_seller_router, prefix="/api")
app.include_router(auto_analyst_router, prefix=settings.API_V1_STR)
app.include_router(auto_analyst_router, prefix="/api")
app.include_router(business_router, prefix=settings.API_V1_STR)
app.include_router(business_router, prefix="/api")

# Mount Static Uploads
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/", tags=["System"])
def root():
    """API Root index."""
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR,
    }


@app.get("/health", tags=["System"])
def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.VERSION,
    }
