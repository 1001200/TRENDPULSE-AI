"""
TrendPulse Category & Product Opportunity Engine.
Identifies clothing categories and product archetypes with demonstrated growth velocity
and inventory turnover, formulating evidence-backed opportunities.
"""

from typing import Dict, Any, List
from collections import defaultdict, Counter


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


def analyze_category_opportunities(
    sales_by_month: List[Dict[str, Any]],
    clothing_sales: List[Any],
    product_map: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Analyzes historical category momentum, share shifts, and volume velocity.
    """
    if not sales_by_month or len(sales_by_month) < 2:
        return []

    first_m = sales_by_month[0]["month"]
    latest_m = sales_by_month[-1]["month"]

    # Calculate category revenue and units in first vs latest month
    cat_stats_first = defaultdict(lambda: {"revenue": 0.0, "units": 0})
    cat_stats_latest = defaultdict(lambda: {"revenue": 0.0, "units": 0})
    cat_stats_all = defaultdict(lambda: {"revenue": 0.0, "units": 0})

    for s in clothing_sales:
        p = product_map.get(s.product_id)
        if not p or not p.category:
            continue
        cat = p.category
        m_str = s.sale_date.strftime("%B %Y") if s.sale_date else ""
        rev = s.selling_price * s.quantity
        cat_stats_all[cat]["revenue"] += rev
        cat_stats_all[cat]["units"] += s.quantity

        if m_str == first_m:
            cat_stats_first[cat]["revenue"] += rev
            cat_stats_first[cat]["units"] += s.quantity
        elif m_str == latest_m:
            cat_stats_latest[cat]["revenue"] += rev
            cat_stats_latest[cat]["units"] += s.quantity

    first_tot_rev = sum(d["revenue"] for d in cat_stats_first.values())
    latest_tot_rev = sum(d["revenue"] for d in cat_stats_latest.values())
    all_tot_rev = sum(d["revenue"] for d in cat_stats_all.values())

    opportunities = []

    for cat, lat_data in cat_stats_latest.items():
        fir_data = cat_stats_first.get(cat, {"revenue": 0.0, "units": 0})
        lat_share = (lat_data["revenue"] / max(1.0, latest_tot_rev)) * 100
        fir_share = (fir_data["revenue"] / max(1.0, first_tot_rev)) * 100
        share_diff_pp = lat_share - fir_share
        all_data = cat_stats_all.get(cat, {"revenue": 0.0, "units": 0})

        if share_diff_pp > 3.0:
            # Significant growth in revenue share
            opportunities.append({
                "category": cat,
                "opportunity_type": "Share Expansion",
                "finding": f"{cat} expanded from {fir_share:.1f}% of sales in {first_m} to {lat_share:.1f}% in {latest_m} (+{share_diff_pp:.1f} percentage points).",
                "evidence": f"{all_data['units']} units sold, {_format_inr(all_data['revenue'])} total revenue ({all_data['revenue']/max(1.0, all_tot_rev)*100:.1f}% of total).",
                "growth_pp": round(share_diff_pp, 1),
                "suggested_action": f"Test a small additional batch of 3–5 curated {cat.lower()} before committing larger sourcing capital.",
                "confidence": "High" if all_data["units"] >= 6 else "Moderate"
            })

    # High-volume turnover anchor
    top_vol_cat = max(cat_stats_all.items(), key=lambda x: x[1]["units"]) if cat_stats_all else None
    if top_vol_cat and (not opportunities or top_vol_cat[0] != opportunities[0]["category"]):
        cat, d = top_vol_cat
        opportunities.append({
            "category": cat,
            "opportunity_type": "Volume Anchor",
            "finding": f"{cat} represents your highest-volume sales driver with {d['units']} units sold.",
            "evidence": f"{_format_inr(d['revenue'])} revenue across {d['units']} garments ({d['units']/max(1, sum(x['units'] for x in cat_stats_all.values()))*100:.1f}% of all units sold).",
            "growth_pp": 0.0,
            "suggested_action": f"Maintain consistent stock of {cat.lower()} as a dependable basket builder for your drops.",
            "confidence": "High"
        })

    return opportunities
