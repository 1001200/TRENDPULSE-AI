from fastapi import APIRouter
from backend.app.api.v1 import health, ingest, insights, profile

api_router = APIRouter()

# Core system health check
api_router.include_router(health.router, tags=["Health"])

# Data Ingestion & Non-Destructive Cleaning Pipeline
api_router.include_router(ingest.router, prefix="/ingest", tags=["Ingestion & Data Quality"])

# The 5 Core Questions Insight Engine
api_router.include_router(insights.router, prefix="/insights", tags=["Core Business Insights"])

# Authenticated Business Profile & Account Identity
api_router.include_router(profile.router, prefix="/profile", tags=["Business Profile"])

