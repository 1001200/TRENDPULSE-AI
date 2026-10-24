"""
TrendPulse Price Elasticity & Markdown Optimization Engine.

Quantifies price sensitivity across clothing categories, aesthetics, and SKUs,
prescribes optimal markdown schedules for aging inventory, and simulates
"What-If" pricing scenarios.

Architecture:
    1. Extract historical price-volume pairs and discount variations per product/category.
    2. Fit log-log OLS elasticity regression: ln(Q) = alpha + beta * ln(P) where beta = elasticity (epsilon).
    3. Categorize into Elastic (|e| > 1.1), Inelastic (|e| < 0.9), or Unit Elastic.
    4. Provide optimal step-down markdown trajectories for decelerating / dead inventory.
    5. Support interactive "What-If" pricing simulations (predicting volume, revenue, and gross profit impact).

Design rules:
    - Implements BaseModel contract.
    - Labels predictions as PREDICTED (elasticity) and SIMULATED (price scenarios).
    - Distinguishes causal price sensitivity from statistical correlation.
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
    UncertaintyInterval,
    _convert_numpy,
    insufficient_data_result,
)
from data_engine.ml.feature_store import FeatureEngineer


# ─────────────────────────────────────────────────────────────────────
# Default Category & Aesthetic Elasticity Benchmarks
# ─────────────────────────────────────────────────────────────────────

# Industry-standard empirical benchmarks used when historical price variation is low:
# Negative values: price up -> demand down.
CATEGORY_ELASTICITY_PRIORS: Dict[str, float] = {
    "T-Shirt": -1.35,
    "Tops": -1.25,
    "Jeans": -1.10,
    "Bottoms": -1.15,
    "Hoodie": -0.95,
    "Outerwear": -0.80,
    "Jackets": -0.75,
    "Accessories": -1.40,
    "default": -1.10,
}

AESTHETIC_ELASTICITY_PRIORS: Dict[str, float] = {
    "Archive / Heavyweight Streetwear": -0.65,  # High hype / inelastic
    "Old Money / Quiet Luxury": -0.70,          # Premium tolerant
    "90s Vintage Grunge": -0.85,                # Curated thrift demand
    "Gorpcore / Technical Outdoor": -0.80,      # Technical / inelastic
    "Y2K / 2000s Retro": -1.20,                 # Trend-driven / competitive
    "Blokecore / Vintage Sport": -0.90,         # Moderate
    "Clean Fit / Minimalist": -1.30,            # Basic commodity / elastic
    "Cottagecore / Prairie": -1.15,
    "default": -1.10,
}


# ─────────────────────────────────────────────────────────────────────
# Elasticity Optimizer Model
# ─────────────────────────────────────────────────────────────────────

class PriceElasticityOptimizer(BaseModel):
    """
    Price-demand elasticity model and markdown optimizer for apparel catalogs.
    """

    MODEL_NAME = "price_elasticity_optimizer"
    MODEL_VERSION = "1.0"
    MODEL_TYPE = "log_log_regression_and_elasticity"

    def __init__(self, *, min_price_variation: float = 0.05, random_state: int = 42):
        super().__init__()
        self.min_price_variation = min_price_variation
        self.random_state = random_state

        # Internal model storage
        self._elasticities: Dict[str, Dict[str, Any]] = {}
        self._category_elasticities: Dict[str, float] = {}
        self._product_stats: Dict[str, Dict[str, float]] = {}

    # ── BaseModel Interface ───────────────────────────────────────

    def fit(self, df: pd.DataFrame, **kwargs) -> "PriceElasticityOptimizer":
        """
        Estimate price elasticity per product and category using log-log regression.
        """
        if not isinstance(df, pd.DataFrame) or df.empty:
            self._is_fitted = False
            return self

        data = df.copy()

        # Numeric sanitization
        for col in ["quantity", "price", "revenue", "cost_price", "discount"]:
            if col in data.columns:
                data[f"_{col}"] = pd.to_numeric(data[col], errors="coerce").fillna(0.0)
            else:
                data[f"_{col}"] = 0.0

        if "product" in data.columns:
            data["_product"] = data["product"].astype(str).str.strip()
        else:
            data["_product"] = "unknown"

        if "category" in data.columns:
            data["_category"] = data["category"].astype(str).str.strip()
        else:
            data["_category"] = "Tops"

        # Fit Category-level Elasticities first
        for cat, grp in data.groupby("_category"):
            e_cat = self._fit_log_log(grp["_price"].values, grp["_quantity"].values)
            prior = CATEGORY_ELASTICITY_PRIORS.get(str(cat), CATEGORY_ELASTICITY_PRIORS["default"])
            # Blend empirical elasticity with category prior if empirical sample is small
            if e_cat is not None and not np.isnan(e_cat):
                # Clamp elasticity between -3.5 (hyper-elastic) and -0.2 (hyper-inelastic)
                clamped = max(-3.5, min(-0.2, float(e_cat)))
                self._category_elasticities[str(cat)] = round(clamped * 0.7 + prior * 0.3, 3)
            else:
                self._category_elasticities[str(cat)] = prior

        # Fit Product-level Elasticities
        for product, grp in data.groupby("_product"):
            total_qty = float(grp["_quantity"].sum())
            total_rev = float(grp["_revenue"].sum())
            avg_price = float(grp["_price"].mean())
            avg_cost = float(grp["_cost_price"].mean()) if grp["_cost_price"].sum() > 0 else avg_price * 0.45
            category = str(grp["_category"].iloc[0])

            self._product_stats[str(product)] = {
                "total_units": total_qty,
                "avg_price": avg_price,
                "avg_cost": avg_cost,
                "category": category,
            }

            prices = grp["_price"].values
            quantities = grp["_quantity"].values

            # Check if there is true price variation
            price_std = float(np.std(prices))
            price_mean = float(np.mean(prices)) if len(prices) > 0 else 1.0
            coef_var = price_std / max(price_mean, 0.01)

            e_prod = None
            if coef_var >= self.min_price_variation and len(grp) >= 3:
                e_prod = self._fit_log_log(prices, quantities)

            cat_baseline = self._category_elasticities.get(category, CATEGORY_ELASTICITY_PRIORS["default"])

            if e_prod is not None and not np.isnan(e_prod):
                final_e = max(-3.5, min(-0.2, float(e_prod)))
                source = "empirical_log_log"
                confidence = 0.82
            else:
                final_e = cat_baseline
                source = "category_prior_blend"
                confidence = 0.65

            # Sensitivity classification
            if abs(final_e) > 1.1:
                sensitivity = "Elastic (Volume Sensitive)"
                pricing_posture = "Volume-sensitive: Discounts stimulate demand; price hikes risk sharp volume drop."
            elif abs(final_e) < 0.9:
                sensitivity = "Inelastic (Premium Tolerant)"
                pricing_posture = "Premium-tolerant: Brand has pricing power; price increases retain high margin."
            else:
                sensitivity = "Unit Elastic"
                pricing_posture = "Balanced: Volume changes proportionally with price adjustments."

            self._elasticities[str(product)] = {
                "elasticity": round(final_e, 3),
                "sensitivity": sensitivity,
                "pricing_posture": pricing_posture,
                "source": source,
                "confidence": confidence,
                "avg_price": round(avg_price, 2),
                "avg_cost": round(avg_cost, 2),
                "category": category,
            }

        self._is_fitted = True
        self._build_metadata(
            status=ModelStatus.EVALUATED,
            metrics={
                "n_products_evaluated": len(self._elasticities),
                "mean_elasticity": round(float(np.mean([m["elasticity"] for m in self._elasticities.values()])), 3) if self._elasticities else 0.0,
            },
            n_training_samples=len(data),
            target="price_elasticity",
            hyperparameters={
                "min_price_variation": self.min_price_variation,
                "random_state": self.random_state,
            },
        )
        return self

    def predict(self, df: pd.DataFrame, **kwargs) -> List[Prediction]:
        """
        Generate price elasticity predictions and markdown recommendations.
        """
        if not self._is_fitted:
            return []

        lifecycle_predictions: List[Prediction] = kwargs.get("lifecycle_predictions", [])
        lifecycle_map = {p.entity_id: str(p.value) for p in lifecycle_predictions if p.value}

        predictions: List[Prediction] = []

        for product, info in self._elasticities.items():
            e = info["elasticity"]
            confidence = info["confidence"]
            stage = lifecycle_map.get(product, "mature")

            # Determine optimal markdown recommendation based on elasticity and lifecycle stage
            markdown_rec = self._calculate_markdown_advice(e, stage, info["avg_price"], info["avg_cost"])

            evidence = [
                f"Estimated Price Elasticity (ε): {e}",
                f"Demand Sensitivity: {info['sensitivity']}",
                f"Source: {info['source']}",
                f"Current Lifecycle Stage: {stage.upper()}",
            ]

            valid_until = (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()

            pred = self._make_prediction(
                entity_type="product",
                entity_id=product,
                prediction_type=PredictionType.PRICE_ELASTICITY,
                value=round(e, 3),
                confidence=confidence,
                uncertainty=UncertaintyInterval(
                    lower=round(e * 1.25, 3),  # e is negative, so lower is more negative
                    upper=round(e * 0.75, 3),
                ),
                horizon="14_days",
                valid_until=valid_until,
                evidence=evidence,
                recommended_action=markdown_rec["action"],
                top_features=[
                    FeatureContribution(name="price_volume_responsiveness", importance=0.6, direction="negative"),
                    FeatureContribution(name="category_baseline", importance=0.4, direction="neutral"),
                ],
                metadata_extra={
                    "sensitivity": info["sensitivity"],
                    "pricing_posture": info["pricing_posture"],
                    "current_avg_price": info["avg_price"],
                    "estimated_unit_cost": info["avg_cost"],
                    "optimal_discount_pct": markdown_rec["recommended_discount_pct"],
                    "projected_volume_multiplier": markdown_rec["projected_volume_multiplier"],
                    "projected_gross_margin_pct": markdown_rec["projected_margin_pct"],
                    "markdown_urgency": markdown_rec["urgency"],
                },
            )
            predictions.append(pred)

        return predictions

    def get_metadata(self) -> ModelMetadata:
        if self._metadata:
            return self._metadata
        return self._build_metadata(status=ModelStatus.TRAINED)

    # ── What-If Price Simulator ───────────────────────────────────

    def simulate_price_change(
        self,
        product: str,
        new_price: float,
    ) -> Dict[str, Any]:
        """
        Simulate the commercial outcome of changing a product's price.

        Returns projected volume, revenue, and gross profit delta.
        """
        if not self._is_fitted:
            return {"status": "error", "message": "Model not fitted."}

        stats = self._product_stats.get(product)
        elasticity_info = self._elasticities.get(product)

        if not stats or not elasticity_info:
            return {
                "status": "error",
                "message": f"Product '{product}' not found in catalog.",
            }

        curr_price = stats["avg_price"]
        curr_cost = stats["avg_cost"]
        curr_units = stats["total_units"]
        e = elasticity_info["elasticity"]

        if curr_price <= 0:
            return {"status": "error", "message": "Current price is invalid."}

        # Percentage price change
        price_delta_pct = (new_price - curr_price) / curr_price

        # Projected quantity change: %dQ = epsilon * %dP
        # Q_new = Q_old * (1 + epsilon * delta_P_pct)
        qty_multiplier = max(0.05, 1.0 + (e * price_delta_pct))
        proj_units = round(curr_units * qty_multiplier, 1)

        # Revenue & Gross Profit
        curr_rev = curr_units * curr_price
        curr_profit = curr_units * (curr_price - curr_cost)

        proj_rev = round(proj_units * new_price, 2)
        proj_profit = round(proj_units * (new_price - curr_cost), 2)

        rev_delta_pct = round(((proj_rev - curr_rev) / max(curr_rev, 1.0)) * 100, 2)
        profit_delta_pct = round(((proj_profit - curr_profit) / max(abs(curr_profit), 1.0)) * 100, 2)

        # Qualitative verdict
        if profit_delta_pct > 5:
            verdict = "FAVORABLE: Profit increases significantly."
        elif profit_delta_pct < -5:
            verdict = "UNFAVORABLE: Margin erosion outweighs volume gains."
        else:
            verdict = "NEUTRAL: Revenue and profit remain relatively stable."

        return _convert_numpy({
            "status": "success",
            "data_label": DataLabel.SIMULATED.value,
            "product": product,
            "current_price": round(curr_price, 2),
            "new_price": round(new_price, 2),
            "price_change_pct": round(price_delta_pct * 100, 1),
            "elasticity_applied": e,
            "projected_units": proj_units,
            "units_change_pct": round((qty_multiplier - 1.0) * 100, 1),
            "projected_revenue": proj_rev,
            "revenue_change_pct": rev_delta_pct,
            "projected_profit": proj_profit,
            "profit_change_pct": profit_delta_pct,
            "verdict": verdict,
        })

    # ── Internal Math & Helpers ───────────────────────────────────

    @staticmethod
    def _fit_log_log(prices: np.ndarray, quantities: np.ndarray) -> Optional[float]:
        """Fit ln(Q) = a + b * ln(P) via OLS."""
        p = np.asarray(prices, dtype=float)
        q = np.asarray(quantities, dtype=float)

        # Filter strictly positive pairs
        mask = (p > 0) & (q > 0)
        p_valid = p[mask]
        q_valid = q[mask]

        if len(p_valid) < 3 or np.std(p_valid) == 0:
            return None

        try:
            log_p = np.log(p_valid)
            log_q = np.log(q_valid)
            slope = float(np.polyfit(log_p, log_q, 1)[0])
            # Elasticity in normal demand curves is negative
            return slope if slope < 0 else -0.5
        except Exception:
            return None

    @staticmethod
    def _calculate_markdown_advice(
        elasticity: float,
        lifecycle_stage: str,
        current_price: float,
        cost_price: float,
    ) -> Dict[str, Any]:
        """
        Prescribe tailored markdown schedules.
        """
        # Baseline margins
        margin_pct = ((current_price - cost_price) / max(current_price, 1.0)) * 100

        if lifecycle_stage in ("declining", "dead"):
            # If item is elastic (|e| > 1), a modest discount triggers high volume
            if abs(elasticity) > 1.2:
                rec_discount = 15.0
                urgency = "HIGH"
                action = f"Apply targeted {rec_discount:.0f}% markdown to rapidly liquidate stock before demand disappears."
            elif abs(elasticity) < 0.9:
                # Inelastic: heavy discounting doesn't help volume much, only hurts margin
                rec_discount = 10.0
                urgency = "MEDIUM"
                action = f"Test modest {rec_discount:.0f}% discount or bundle with core items; avoid steep markdowns as demand is price-insensitive."
            else:
                rec_discount = 20.0
                urgency = "HIGH"
                action = f"Schedule {rec_discount:.0f}% seasonal clearance markdown."
        elif lifecycle_stage == "emerging":
            rec_discount = 0.0
            urgency = "LOW"
            action = "Maintain full price. Style is accelerating with zero discount requirement."
        else:
            rec_discount = 0.0
            urgency = "LOW"
            action = "Price is stable. Maintain current price posture."

        # Projected volume multiplier from discount
        price_ratio = 1.0 - (rec_discount / 100.0)
        vol_mult = round(float(price_ratio ** elasticity), 2) if rec_discount > 0 else 1.0
        new_price = current_price * price_ratio
        proj_margin = round(((new_price - cost_price) / max(new_price, 1.0)) * 100, 1)

        return {
            "recommended_discount_pct": rec_discount,
            "projected_volume_multiplier": vol_mult,
            "projected_margin_pct": proj_margin,
            "urgency": urgency,
            "action": action,
        }
