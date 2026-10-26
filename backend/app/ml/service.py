"""
TrendPulse Machine Learning Orchestration Service.
Coordinates time series forecasting, inventory risk analysis, opportunity identification,
and actionable recommendation synthesis from verified business data.
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime

from backend.app.models.models import Product, SaleOrder, InventoryItem
from backend.app.ml.forecasting import forecast_monthly_sales
from backend.app.ml.inventory_risk import assess_inventory_risks
from backend.app.ml.category_opportunity import analyze_category_opportunities
from backend.app.ml.pricing_opportunity import analyze_pricing_opportunities
from backend.app.ml.repeat_purchase import analyze_repeat_purchase_patterns
from backend.app.ml.recommendations import generate_actionable_recommendations


# Simple in-memory cache to avoid redundant recomputations on repeated visits
_PREDICTIONS_CACHE = {
    "key": None,
    "timestamp": None,
    "data": None
}


def get_business_predictions(
    db: Session,
    sales_by_month: List[Dict[str, Any]] = None,
    sales_by_price_range: List[Dict[str, Any]] = None,
    category_x_price: List[Dict[str, Any]] = None,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Computes evaluated ML predictions and actionable business recommendations.
    Uses cached result if database sales count and order count have not changed.
    """
    global _PREDICTIONS_CACHE

    all_sales = db.query(SaleOrder).filter(SaleOrder.sale_status == "completed").all()
    all_products = db.query(Product).all()
    all_inv = db.query(InventoryItem).all()

    cache_key = f"{len(all_sales)}_{len(all_products)}_{len(all_inv)}"
    if not force_refresh and _PREDICTIONS_CACHE["key"] == cache_key and _PREDICTIONS_CACHE["data"] is not None:
        return _PREDICTIONS_CACHE["data"]

    product_map = {p.product_id: p for p in all_products}

    # 1. Build monthly sales aggregates if not passed
    if sales_by_month is None:
        month_dict = {}
        for s in all_sales:
            if not s.sale_date:
                continue
            m_key = s.sale_date.strftime("%Y-%m")
            m_label = s.sale_date.strftime("%B %Y")
            if m_key not in month_dict:
                month_dict[m_key] = {"month": m_label, "revenue": 0.0, "units": 0, "orders": 0, "dt": s.sale_date}
            month_dict[m_key]["revenue"] += s.selling_price * s.quantity
            month_dict[m_key]["units"] += s.quantity
            month_dict[m_key]["orders"] += 1
        sorted_m = sorted(month_dict.values(), key=lambda x: x["dt"])
        sales_by_month = [
            {"month": m["month"], "revenue": round(m["revenue"], 2), "units": m["units"], "orders": m["orders"]}
            for m in sorted_m
        ]

    # 2. Sales Time Series Forecast
    forecast_result = forecast_monthly_sales(sales_by_month)

    # 3. Slow-Moving Product Risk (Available vs Sold items)
    available_items = []
    sold_items = []
    for inv in all_inv:
        prod = product_map.get(inv.product_id)
        prod_data = {
            "product_id": inv.product_id,
            "product_name": prod.product_name if prod else inv.product_id,
            "category": prod.category if prod else "General",
            "size": prod.size if prod else "Free Size",
            "retail_price": prod.retail_price if prod else 0.0,
            "date_stocked": inv.date_stocked,
            "status": inv.status
        }
        if inv.status == "Available":
            available_items.append(prod_data)

    for s in all_sales:
        prod = product_map.get(s.product_id)
        sold_items.append({
            "product_id": s.product_id,
            "category": prod.category if prod else "General",
            "date_stocked": prod.date_sourced if prod and prod.date_sourced else (s.sale_date.replace(hour=19, minute=0) if s.sale_date else None),
            "sale_date": s.sale_date
        })

    # Reference date is max sale date or current date
    latest_sale_date = max((s.sale_date for s in all_sales if s.sale_date), default=datetime(2026, 10, 25))
    inv_risk_result = assess_inventory_risks(available_items, sold_items, reference_date=datetime(2026, 10, 25))

    # 4. Category & Product Opportunities
    clothing_sales = [s for s in all_sales if product_map.get(s.product_id)]
    category_opportunities = analyze_category_opportunities(sales_by_month, clothing_sales, product_map)

    # 5. Pricing Opportunities
    if sales_by_price_range is None:
        sales_by_price_range = []
    if category_x_price is None:
        category_x_price = []
    pricing_opportunities = analyze_pricing_opportunities(sales_by_price_range, category_x_price, clothing_sales, product_map)

    # 6. Customer Repeat-Purchase Behavioral Insights
    repeat_purchase_result = analyze_repeat_purchase_patterns(all_sales)

    # 7. Actionable Business Recommendations
    recommendations = generate_actionable_recommendations(
        forecast_result=forecast_result,
        inventory_risk_result=inv_risk_result,
        category_opportunities=category_opportunities,
        pricing_opportunities=pricing_opportunities,
        repeat_purchase_result=repeat_purchase_result
    )

    result = {
        "sales_forecast": forecast_result,
        "inventory_risk": inv_risk_result,
        "category_opportunities": category_opportunities,
        "pricing_opportunities": pricing_opportunities,
        "repeat_purchase_insights": repeat_purchase_result,
        "recommendations": recommendations,
        "metadata": {
            "model_version": "v1.2-retail-ts",
            "generated_at": datetime.utcnow().isoformat(),
            "records_analyzed": len(all_sales),
            "available_stock_count": len(available_items),
            "sufficient_data": forecast_result.get("sufficient_data", False)
        }
    }

    _PREDICTIONS_CACHE["key"] = cache_key
    _PREDICTIONS_CACHE["timestamp"] = datetime.utcnow()
    _PREDICTIONS_CACHE["data"] = result

    return result
