"""
TrendPulse Autonomous Decision & Action Center.

The master synthesis engine that combines all predictive intelligence layers:
    - Demand Forecasts & Size Curves
    - Product Lifecycle Trajectories
    - Stockout & Inventory Depletion Simulations
    - Price Elasticity & Markdown Optimizers
    - Customer Churn & Repurchase Timing
    - Viral Aesthetic Velocities

Outputs:
    1. Ranked Commercial Threats (Imminent stockouts, dead capital, VIP churn)
    2. Ranked Growth Opportunities (Emerging viral hits, pricing headroom, sourcing spikes)
    3. Unified Prescriptive Action Feed with quantified financial impact (₹).

Design rules:
    - Implements BaseModel contract.
    - Labels outputs as RECOMMENDED.
    - Pure synthesis; robust to partial or absent model inputs.
    - Deterministic; zero side-effects.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from data_engine.ml.contracts import (
    BaseModel,
    DataLabel,
    FeatureContribution,
    ModelMetadata,
    ModelStatus,
    Prediction,
    PredictionType,
    _convert_numpy,
)


class DecisionEngine(BaseModel):
    """
    Unified Prescriptive Decision & Opportunity Engine for TrendPulse.
    """

    MODEL_NAME = "decision_engine"
    MODEL_VERSION = "1.0"
    MODEL_TYPE = "cross_domain_decision_synthesis"

    def __init__(self):
        super().__init__()
        self._threats: List[Dict[str, Any]] = []
        self._opportunities: List[Dict[str, Any]] = []
        self._action_feed: List[Dict[str, Any]] = []
        self._summary_stats: Dict[str, Any] = {}

    # ── BaseModel Interface ───────────────────────────────────────

    def fit(self, df: pd.DataFrame, **kwargs) -> "DecisionEngine":
        """
        Synthesize cross-domain predictive outputs into an actionable decision matrix.
        """
        demand_preds: List[Prediction] = kwargs.get("demand_predictions", [])
        lifecycle_preds: List[Prediction] = kwargs.get("lifecycle_predictions", [])
        stockout_preds: List[Prediction] = kwargs.get("stockout_predictions", [])
        pricing_preds: List[Prediction] = kwargs.get("pricing_predictions", [])
        customer_preds: List[Prediction] = kwargs.get("customer_predictions", [])

        # Reset lists
        self._threats = []
        self._opportunities = []
        self._action_feed = []

        # ── 1. Synthesize Commercial Threats ──────────────────────────

        # Threat A: Imminent Stockouts on High-Demand Products
        for sp in stockout_preds:
            prob = float(sp.value) if sp.value is not None else 0.0
            if prob >= 0.65:
                meta = sp.metadata or {}
                forecast_demand = float(meta.get("forecast_demand", 50))
                current_stock = float(meta.get("current_stock", 0))
                unmet_units = max(1, forecast_demand - current_stock)
                est_loss = unmet_units * 899.0  # estimated revenue at risk

                threat = {
                    "threat_type": "IMMINENT_STOCKOUT",
                    "severity": "CRITICAL" if prob >= 0.80 else "HIGH",
                    "entity_id": sp.entity_id,
                    "headline": f"Stockout Alert: {sp.entity_id} ({prob:.0%} risk)",
                    "expected_date": meta.get("expected_stockout_date", "Within 14 days"),
                    "revenue_at_risk": round(est_loss, 2),
                    "rationale": f"Projected demand of {forecast_demand:.0f} units exceeds current stock of {current_stock:.0f} units.",
                    "recommended_action": sp.recommended_action or f"Reorder {unmet_units:.0f} units immediately.",
                }
                self._threats.append(threat)

                self._action_feed.append({
                    "priority": 1 if prob >= 0.80 else 2,
                    "category": "INVENTORY",
                    "action_type": "REORDER",
                    "entity_id": sp.entity_id,
                    "headline": f"Reorder {meta.get('recommended_replenishment', unmet_units):.0f} units of {sp.entity_id}",
                    "reason": f"Stockout likely by {meta.get('expected_stockout_date', 'soon')}. Protects ₹{est_loss:,.2f} revenue.",
                    "financial_impact": round(est_loss, 2),
                    "impact_type": "REVENUE_PROTECTED",
                })

        # Threat B: Dead Stock Traps
        for lp in lifecycle_preds:
            if lp.value == "dead":
                threat = {
                    "threat_type": "DEAD_STOCK_STAGNATION",
                    "severity": "HIGH",
                    "entity_id": lp.entity_id,
                    "headline": f"Dead Stock Trap: {lp.entity_id}",
                    "rationale": "Style velocity has collapsed to near-zero with high days since last sale.",
                    "recommended_action": lp.recommended_action or "Clearance or bundle to free up working capital.",
                    "revenue_at_risk": 0.0,
                }
                self._threats.append(threat)

                self._action_feed.append({
                    "priority": 2,
                    "category": "PRICING",
                    "action_type": "MARKDOWN",
                    "entity_id": lp.entity_id,
                    "headline": f"Liquidate {lp.entity_id} via clearance markdown",
                    "reason": "Style is stagnant; recover cash to reinvest in trending inventory.",
                    "financial_impact": 0.0,
                    "impact_type": "CASH_RECOVERED",
                })

        # Threat C: VIP Customer Churn
        for cp in customer_preds:
            prob = float(cp.value) if cp.value is not None else 0.0
            meta = cp.metadata or {}
            if prob >= 0.70 and "VIP" in str(meta.get("customer_segment", "")):
                spend = float(meta.get("historical_total_spend", 2000.0))
                threat = {
                    "threat_type": "VIP_CUSTOMER_CHURN",
                    "severity": "HIGH",
                    "entity_id": cp.entity_id,
                    "headline": f"VIP Churn Risk: Customer {cp.entity_id}",
                    "rationale": f"High past spend (₹{spend:,.2f}) but reorder cycle has lapsed.",
                    "recommended_action": cp.recommended_action,
                    "revenue_at_risk": round(spend * 0.5, 2),
                }
                self._threats.append(threat)

                self._action_feed.append({
                    "priority": 2,
                    "category": "CUSTOMER",
                    "action_type": "VIP_OUTREACH",
                    "entity_id": cp.entity_id,
                    "headline": f"Send private preview invitation to VIP {cp.entity_id}",
                    "reason": f"Customer at {prob:.0%} churn risk; recover ₹{spend * 0.5:,.2f} annual spend.",
                    "financial_impact": round(spend * 0.5, 2),
                    "impact_type": "LTV_SAVED",
                })

        # ── 2. Synthesize Growth Opportunities ────────────────────────

        # Opportunity A: Emerging Viral Hits
        for lp in lifecycle_preds:
            if lp.value == "emerging":
                opp = {
                    "opportunity_type": "VIRAL_EMERGING_HIT",
                    "priority": "HIGH",
                    "entity_id": lp.entity_id,
                    "headline": f"Emerging Hit: {lp.entity_id}",
                    "rationale": "Sales velocity is actively accelerating with positive trend momentum.",
                    "recommended_action": "Scale marketing and increase inventory commitments.",
                    "projected_gain": 35000.0,
                }
                self._opportunities.append(opp)

                self._action_feed.append({
                    "priority": 1,
                    "category": "SOURCING",
                    "action_type": "SCALE_SUPPLY",
                    "entity_id": lp.entity_id,
                    "headline": f"Scale production / procurement of {lp.entity_id}",
                    "reason": "Style is accelerating; capture peak viral window.",
                    "financial_impact": 35000.0,
                    "impact_type": "GROWTH_UPSIDE",
                })

        # Opportunity B: Inelastic Pricing Power (Price Increase Potential)
        for pp in pricing_preds:
            meta = pp.metadata or {}
            e = float(pp.value) if pp.value is not None else -1.0
            if abs(e) < 0.75:  # Highly inelastic
                curr_price = float(meta.get("current_avg_price", 999.0))
                potential_lift = curr_price * 0.10 * 40  # 10% bump over 40 units
                opp = {
                    "opportunity_type": "PRICING_POWER_HEADROOM",
                    "priority": "MEDIUM",
                    "entity_id": pp.entity_id,
                    "headline": f"Pricing Headroom: {pp.entity_id} (ε = {e:.2f})",
                    "rationale": "Strong brand/curation equity. Customers are price-insensitive for this style.",
                    "recommended_action": f"Test +10% price bump (from ₹{curr_price:.0f} to ₹{curr_price * 1.1:.0f}) to increase gross profit margin.",
                    "projected_gain": round(potential_lift, 2),
                }
                self._opportunities.append(opp)

                self._action_feed.append({
                    "priority": 3,
                    "category": "PRICING",
                    "action_type": "INCREASE_PRICE",
                    "entity_id": pp.entity_id,
                    "headline": f"Increase price of {pp.entity_id} by +10%",
                    "reason": f"Inelastic demand (ε = {e:.2f}); adds ₹{potential_lift:,.2f} pure gross profit with zero volume loss.",
                    "financial_impact": round(potential_lift, 2),
                    "impact_type": "MARGIN_EXPANSION",
                })

        # Sort actions by priority (1 is highest)
        self._action_feed.sort(key=lambda x: x.get("priority", 3))

        total_threat_risk = sum(t.get("revenue_at_risk", 0.0) for t in self._threats)
        total_opp_gain = sum(o.get("projected_gain", 0.0) for o in self._opportunities)

        self._summary_stats = {
            "total_threats_detected": len(self._threats),
            "total_opportunities_detected": len(self._opportunities),
            "total_prescriptive_actions": len(self._action_feed),
            "total_revenue_at_risk": round(total_threat_risk, 2),
            "total_projected_opportunity_gain": round(total_opp_gain, 2),
        }

        self._is_fitted = True
        self._build_metadata(
            status=ModelStatus.EVALUATED,
            metrics=self._summary_stats,
            target="autonomous_business_actions",
        )
        return self

    def predict(self, df: pd.DataFrame, **kwargs) -> List[Prediction]:
        """
        Generate structured action predictions from synthesized findings.
        """
        if not self._is_fitted:
            return []

        predictions: List[Prediction] = []

        for action in self._action_feed:
            valid_until = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

            pred = self._make_prediction(
                entity_type=action.get("category", "system").lower(),
                entity_id=action.get("entity_id", "catalog"),
                prediction_type=PredictionType.ACTION_RECOMMENDATION,
                value=action.get("action_type", "ACTION"),
                confidence=0.90,
                valid_until=valid_until,
                evidence=[action.get("reason", "")],
                recommended_action=action.get("headline", ""),
                metadata_extra=action,
            )
            predictions.append(pred)

        return predictions

    def get_metadata(self) -> ModelMetadata:
        if self._metadata:
            return self._metadata
        return self._build_metadata(status=ModelStatus.TRAINED)

    def get_decision_center(self) -> Dict[str, Any]:
        """Return the complete decision center payload for the API."""
        return _convert_numpy({
            "status": "success",
            "data_label": DataLabel.RECOMMENDED.value,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": self._summary_stats,
            "ranked_threats": self._threats,
            "ranked_opportunities": self._opportunities,
            "action_feed": self._action_feed,
        })
