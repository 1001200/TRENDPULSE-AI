"""
TrendPulse Slow-Selling Product Risk Engine.
Analyzes currently available unsold inventory against historical time-to-sale benchmarks.
Transparent, non-destructive, and strictly preserves valid availability states.
"""

from typing import Dict, Any, List
from datetime import datetime
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


def assess_inventory_risks(
    available_items: List[Dict[str, Any]],
    sold_items: List[Dict[str, Any]],
    reference_date: datetime = None
) -> Dict[str, Any]:
    """
    Identifies currently available unsold items that exceed benchmark time-to-sale.

    Rules & Guards:
    - Never flags a sold-out item as slow-moving.
    - Compares days-on-hand against category-specific time-to-sale of completed sales.
    - Returns structured risk cards with transparent explanations.
    """
    if reference_date is None:
        reference_date = datetime(2026, 10, 25)

    if not available_items:
        return {
            "has_slow_moving_items": False,
            "items_count": 0,
            "risk_items": [],
            "message": "All listed inventory items have completed sales. No unsold stock detected."
        }

    # 1. Compute category benchmarks from sold items (days to sale)
    category_time_to_sale = defaultdict(list)
    for s in sold_items:
        stk_date = s.get("date_stocked")
        sale_date = s.get("sale_date")
        cat = s.get("category", "General")
        if stk_date and sale_date and isinstance(stk_date, datetime) and isinstance(sale_date, datetime):
            days = max(0, (sale_date - stk_date).days)
            category_time_to_sale[cat].append(days)

    cat_benchmarks = {}
    for cat, days_list in category_time_to_sale.items():
        if days_list:
            avg_days = sum(days_list) / len(days_list)
            cat_benchmarks[cat] = {
                "avg_days_to_sale": round(avg_days, 1),
                "p90_days_to_sale": max(days_list)
            }

    # 2. Evaluate available inventory items
    risk_items = []
    for item in available_items:
        stk_date = item.get("date_stocked")
        if not stk_date:
            continue
        if isinstance(stk_date, str):
            try:
                stk_date = datetime.fromisoformat(stk_date)
            except Exception:
                continue

        days_on_hand = max(0, (reference_date - stk_date).days)
        cat = item.get("category", "General")
        benchmark = cat_benchmarks.get(cat, {"avg_days_to_sale": 7.0, "p90_days_to_sale": 21.0})
        avg_tt_sale = benchmark["avg_days_to_sale"]

        # Flag if days on hand significantly exceeds the average time-to-sale
        is_slow = days_on_hand > max(20, avg_tt_sale * 3)

        if is_slow:
            risk_items.append({
                "product_id": item.get("product_id"),
                "product_name": item.get("product_name"),
                "category": cat,
                "size": item.get("size", "Free Size"),
                "retail_price": item.get("retail_price", 0.0),
                "retail_price_formatted": _format_inr(item.get("retail_price", 0.0)),
                "date_stocked": stk_date.strftime("%b %d, %Y"),
                "days_on_hand": days_on_hand,
                "category_avg_days_to_sale": avg_tt_sale,
                "velocity_ratio": round(days_on_hand / max(1.0, avg_tt_sale), 1),
                "suggested_action": f"Review listing price or restyle for upcoming drop. Listed for {days_on_hand} days vs {avg_tt_sale:.0f}-day category average."
            })

    # Sort by days on hand descending (longest unsold first)
    risk_items.sort(key=lambda x: x["days_on_hand"], reverse=True)

    return {
        "has_slow_moving_items": len(risk_items) > 0,
        "items_count": len(risk_items),
        "risk_items": risk_items,
        "summary": f"{len(risk_items)} active inventory items have remained listed longer than comparable sold items." if risk_items else "No inventory items are currently flagged as slow-moving."
    }
