"""
TrendPulse Pricing Opportunity Engine.
Identifies price brackets with stronger conversion velocity and historical revenue concentration.
Frames recommendations as controlled, low-risk pricing experiments.
"""

from typing import Dict, Any, List
from collections import defaultdict


def _format_inr(val: float) -> str:
    try:
        val_int = int(round(val))
        is_neg = val_int < 0
        val_int = abs(val_int)
        s = str(val_int)
        if len(s) <= 3:
            res = s
        else:
            last3 = s[-3:]
            rest = s[:-3]
            groups = []
            while len(rest) > 2:
                groups.insert(0, rest[-2:])
                rest = rest[:-2]
            if rest:
                groups.insert(0, rest)
            res = ",".join(groups) + "," + last3
        prefix = "-₹" if is_neg else "₹"
        return f"{prefix}{res}"
    except Exception:
        return f"₹{val:,.0f}"


def analyze_pricing_opportunities(
    sales_by_price_range: List[Dict[str, Any]],
    category_x_price: List[Dict[str, Any]],
    clothing_sales: List[Any],
    product_map: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Analyzes price brackets and category sweet spots, formulating testable pricing experiments.
    """
    opportunities = []

    # 1. Overall price bracket concentration
    if sales_by_price_range:
        top_rev = max(sales_by_price_range, key=lambda x: x["revenue"])
        top_vol = max(sales_by_price_range, key=lambda x: x["units"])

        if top_rev["revenue"] > 0:
            opportunities.append({
                "scope": "Overall Sweet Spot",
                "price_bracket": top_rev["range"],
                "finding": f"The {top_rev['range']} price bracket generated the highest total revenue ({top_rev['revenue_formatted']}, {top_rev['pct_of_sales']}% of sales).",
                "evidence": f"{top_rev['orders']} orders, {top_rev['units']} units sold at {top_rev['revenue_formatted']}.",
                "suggested_action": f"Price newly sourced items into {top_rev['range']} where quality and aesthetic support it to match buyer willingness to pay.",
                "confidence": "High" if top_rev["units"] >= 6 else "Moderate"
            })

    # 2. Category-specific pricing opportunities
    for cat_item in category_x_price:
        if cat_item.get("has_data") and cat_item.get("units_sold", 0) >= 3:
            cat = cat_item["category"]
            bracket = cat_item["sweet_spot_bracket"]
            rev = cat_item["revenue_formatted"]
            units = cat_item["units_sold"]
            share = cat_item["rev_pct"]
            opportunities.append({
                "scope": f"{cat} Pricing",
                "category": cat,
                "price_bracket": bracket,
                "finding": f"{cat} has performed strongest in the {bracket} bracket ({share}% of category revenue).",
                "evidence": f"{units} units sold at {rev} (average category price: {cat_item['avg_price_formatted']}).",
                "suggested_action": f"Test listing 2–3 new {cat.lower()} pieces within {bracket} on your next drop to evaluate conversion speed.",
                "confidence": "High" if units >= 5 else "Moderate"
            })

    return opportunities
