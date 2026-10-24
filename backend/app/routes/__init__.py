"""
Routes aggregator module.
"""

from backend.app.routes.auth import router as auth_router
from backend.app.routes.upload import router as upload_router
from backend.app.routes.analytics import router as analytics_router
from backend.app.routes.apparel import router as apparel_router
from backend.app.routes.export import router as export_router
from backend.app.routes.social import router as social_router
from backend.app.routes.economics import router as economics_router
from backend.app.routes.ml import router as ml_router
from backend.app.routes.ai_chat import router as ai_router
from backend.app.routes.drop_public import router as drop_public_router
from backend.app.routes.drop_seller import router as drop_seller_router
from backend.app.routes.auto_analyst import router as auto_analyst_router
from backend.app.routes.business import router as business_router

__all__ = [
    "auth_router",
    "upload_router",
    "analytics_router",
    "apparel_router",
    "export_router",
    "social_router",
    "economics_router",
    "ml_router",
    "ai_router",
    "drop_public_router",
    "drop_seller_router",
    "auto_analyst_router",
    "business_router",
]

