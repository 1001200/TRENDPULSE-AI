"""
TrendPulse ML Intelligence API Routes — All-in-One Predictive Suite.

Provides REST endpoints for:
    - Demand Forecasting (units, intervals, size curves)
    - Product Lifecycle Classification (6 stages)
    - Stockout Risk Predictions & Replenishment
    - Price Elasticity & Markdown Optimization
    - What-If Price Scenario Simulation
    - Customer Churn Risk & Repurchase Timing
    - Autonomous Decision & Opportunity Center
    - Model Registry Metadata & Pipeline Summary
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.database.models import Dataset, DatasetSnapshot, User
from backend.app.services.auth_service import require_current_user
from backend.app.services.tenant_service import get_user_dataset

router = APIRouter(prefix="/api/v1/ml", tags=["ML Intelligence"])


# ── Pydantic Request Schemas ──────────────────────────────────────

class PriceSimRequest(BaseModel):
    product: str = Field(..., description="Exact product name to simulate")
    new_price: float = Field(..., gt=0.0, description="Hypothetical new selling price in ₹")


# ── Helpers ───────────────────────────────────────────────────────

def _get_ml_intelligence(dataset_id: int, db: Session, current_user: User) -> dict:
    """Retrieve ML intelligence results strictly verifying caller's dataset ownership."""
    dataset = get_user_dataset(db, dataset_id, current_user)
    if dataset.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Dataset {dataset_id} status is '{dataset.status}' — must be 'completed'.",
        )

    snapshot = db.query(DatasetSnapshot).filter(
        DatasetSnapshot.dataset_id == dataset_id
    ).first()
    if not snapshot:
        raise HTTPException(status_code=404, detail="No processed snapshot found for this dataset.")

    result = snapshot.get_result()
    ml = result.get("ml_intelligence")
    if not ml:
        raise HTTPException(
            status_code=404,
            detail="ML intelligence not available — dataset may have been processed before ML layer was added.",
        )
    return ml



# ── Endpoints ─────────────────────────────────────────────────────

@router.get("/{dataset_id}/demand-forecast")
def get_demand_forecast(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """
    Demand forecasts for all products in a dataset.

    Returns per-product (and per-size) demand predictions
    with confidence intervals, model selection details, and business recommendations.
    """
    ml = _get_ml_intelligence(dataset_id, db, current_user)
    return {
        "dataset_id": dataset_id,
        "prediction_type": "demand_forecast",
        "predictions": ml.get("demand_forecast", []),
    }


@router.get("/{dataset_id}/product-lifecycle")
def get_product_lifecycle(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """
    Product lifecycle classifications for all SKUs.

    Returns lifecycle stage (NEW/EMERGING/GROWING/MATURE/DECLINING/DEAD)
    with confidence, evidence, risk assessment, and recommended actions.
    """
    ml = _get_ml_intelligence(dataset_id, db, current_user)
    return {
        "dataset_id": dataset_id,
        "prediction_type": "product_lifecycle",
        "predictions": ml.get("product_lifecycle", []),
    }


@router.get("/{dataset_id}/stockout-predictions")
def get_stockout_predictions(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """
    Stockout risk predictions for all products with inventory data.

    Returns stockout probability, expected stockout date, depletion curves,
    and recommended replenishment quantities.
    """
    ml = _get_ml_intelligence(dataset_id, db, current_user)
    return {
        "dataset_id": dataset_id,
        "prediction_type": "stockout_prediction",
        "predictions": ml.get("stockout_predictions", []),
    }


@router.get("/{dataset_id}/price-elasticity")
def get_price_elasticity(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """
    Price elasticity of demand and optimal markdown schedules.

    Quantifies sensitivity (Elastic vs Inelastic vs Unit Elastic) and prescribes
    margin-defending discount trajectories for decelerating inventory.
    """
    ml = _get_ml_intelligence(dataset_id, db, current_user)
    return {
        "dataset_id": dataset_id,
        "prediction_type": "price_elasticity",
        "predictions": ml.get("price_elasticity", []),
    }


@router.post("/{dataset_id}/simulate-price")
def simulate_price(
    dataset_id: int,
    payload: PriceSimRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """
    Simulate a 'What-If' price adjustment for a specific product.

    Calculates projected volume multiplier, revenue delta %, and gross profit impact (₹).
    """
    ml = _get_ml_intelligence(dataset_id, db, current_user)
    pricing_list = ml.get("price_elasticity", [])

    # Find the target product's elasticity metadata
    target_pred = None
    for p in pricing_list:
        if isinstance(p, dict) and p.get("entity_id") == payload.product:
            target_pred = p
            break

    current_price = 1000.0
    current_volume = 100.0
    elasticity = -1.5
    unit_cogs = 400.0

    if target_pred:
        meta = target_pred.get("metadata", {})
        elasticity = meta.get("elasticity", -1.5)
        current_price = meta.get("current_price", 1000.0)
        current_volume = meta.get("avg_weekly_volume", 100.0)

    if current_price <= 0:
        current_price = 1000.0

    pct_price_change = (payload.new_price - current_price) / current_price
    pct_volume_change = elasticity * pct_price_change
    qty_multiplier = max(0.05, 1.0 + pct_volume_change)
    projected_volume = current_volume * qty_multiplier

    base_rev = current_volume * current_price
    proj_rev = projected_volume * payload.new_price
    rev_change_pct = round(((proj_rev - base_rev) / max(base_rev, 1.0)) * 100, 2)

    base_profit = current_volume * (current_price - unit_cogs)
    proj_profit = projected_volume * (payload.new_price - unit_cogs)
    profit_change_pct = round(((proj_profit - base_profit) / max(abs(base_profit), 1.0)) * 100, 2)

    return {
        "product": payload.product,
        "current_price": current_price,
        "new_price": payload.new_price,
        "elasticity_coefficient": round(elasticity, 3),
        "demand_sensitivity": "Elastic" if abs(elasticity) > 1.0 else "Inelastic",
        "projected_units_change_percentage": round((qty_multiplier - 1.0) * 100, 2),
        "projected_revenue_change_percentage": rev_change_pct,
        "projected_gross_profit_change_percentage": profit_change_pct,
        "commercial_verdict": "FAVORABLE: Gross profit increases." if profit_change_pct > 0 else "UNFAVORABLE: Margin erosion exceeds volume gain.",
    }


@router.get("/{dataset_id}/customer-predictions")
def get_customer_predictions(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """
    Customer churn risks, repurchase survival timing, and expected transaction spend.

    Identifies VIP at-risk buyers and personalized re-engagement timing.
    """
    ml = _get_ml_intelligence(dataset_id, db, current_user)
    return {
        "dataset_id": dataset_id,
        "prediction_type": "customer_predictions",
        "predictions": ml.get("customer_predictions", []),
    }


@router.get("/{dataset_id}/decision-center")
def get_decision_center(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """
    Autonomous Decision & Action Center.

    Synthesizes all predictive models into:
        1. Ranked Commercial Threats (Stockouts, Dead Stock, VIP Churn)
        2. Ranked Growth Opportunities (Emerging Hits, Pricing Power)
        3. Prescriptive Action Feed with quantified financial impact (₹).
    """
    ml = _get_ml_intelligence(dataset_id, db, current_user)
    return {
        "dataset_id": dataset_id,
        "decision_center": ml.get("decision_center", {}),
    }


@router.get("/{dataset_id}/model-registry")
def get_model_registry(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """
    Metadata for all ML models trained on a dataset.

    Returns model names, versions, types, training metrics,
    feature lists, and evaluation results.
    """
    ml = _get_ml_intelligence(dataset_id, db, current_user)
    return {
        "dataset_id": dataset_id,
        "registry": ml.get("model_registry", {}),
    }


@router.get("/{dataset_id}/summary")
def get_ml_summary(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """
    High-level summary of the complete All-in-One ML suite for a dataset.
    """
    ml = _get_ml_intelligence(dataset_id, db, current_user)

    forecasts = ml.get("demand_forecast", [])
    lifecycles = ml.get("product_lifecycle", [])
    stockouts = ml.get("stockout_predictions", [])
    pricing = ml.get("price_elasticity", [])
    customers = ml.get("customer_predictions", [])
    decision = ml.get("decision_center", {})
    registry = ml.get("model_registry", {})

    n_forecasts = len([f for f in forecasts if isinstance(f, dict) and f.get("value") is not None])
    n_lifecycle = len([l for l in lifecycles if isinstance(l, dict) and l.get("value") is not None])
    n_stockout = len([s for s in stockouts if isinstance(s, dict) and s.get("value") is not None])
    n_pricing = len([p for p in pricing if isinstance(p, dict) and p.get("value") is not None])
    n_customers = len([c for c in customers if isinstance(c, dict) and c.get("value") is not None])

    high_risk_stockouts = [
        s for s in stockouts
        if isinstance(s, dict) and isinstance(s.get("value"), (int, float)) and s["value"] >= 0.70
    ]

    vip_at_risk = [
        c for c in customers
        if isinstance(c, dict) and isinstance(c.get("value"), (int, float)) and c["value"] >= 0.70
        and "VIP" in str(c.get("metadata", {}).get("customer_segment", ""))
    ]

    return {
        "dataset_id": dataset_id,
        "ml_status": ml.get("status", "unknown"),
        "total_models_trained": registry.get("total_models", 0),
        "suite_coverage": {
            "demand_forecasts": n_forecasts,
            "lifecycle_classifications": n_lifecycle,
            "stockout_predictions": n_stockout,
            "pricing_models": n_pricing,
            "customer_profiles": n_customers,
            "prescriptive_actions": len(decision.get("action_feed", [])),
        },
        "critical_highlights": {
            "high_risk_stockouts": len(high_risk_stockouts),
            "vip_customers_at_risk": len(vip_at_risk),
            "total_commercial_threats": decision.get("summary", {}).get("total_threats_detected", 0),
            "total_growth_opportunities": decision.get("summary", {}).get("total_opportunities_detected", 0),
            "projected_opportunity_gain": decision.get("summary", {}).get("total_projected_opportunity_gain", 0),
        },
    }
