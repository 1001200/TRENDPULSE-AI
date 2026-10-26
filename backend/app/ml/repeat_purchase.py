"""
TrendPulse Repeat-Purchase Behavioral Analytics & Opportunities Engine.
Analyzes repeat-purchase intervals, customer loyalty concentration, and returning buyer spend patterns.
"""

from typing import Dict, Any, List
from collections import defaultdict, Counter
from datetime import datetime


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


def analyze_repeat_purchase_patterns(
    all_sales: List[Any]
) -> Dict[str, Any]:
    """
    Computes inter-order intervals, returning vs new customer spend comparisons,
    and drop timing dynamics.
    """
    customer_orders = defaultdict(list)
    for s in all_sales:
        cust = s.customer_identifier or ""
        if cust and not cust.startswith("Anonymous"):
            customer_orders[cust].append({
                "date": s.sale_date,
                "amount": s.selling_price * s.quantity,
                "units": s.quantity
            })

    if not customer_orders:
        return {
            "has_data": False,
            "message": "Customer handles required to compute repeat purchase behavior."
        }

    total_unique = len(customer_orders)
    repeat_customers = {c: orders for c, orders in customer_orders.items() if len(orders) > 1}
    repeat_count = len(repeat_customers)
    repeat_rate = round((repeat_count / max(1, total_unique)) * 100, 1)

    # Compute inter-purchase days interval for returning buyers
    intervals = []
    repeat_total_spend = 0.0
    single_total_spend = 0.0

    for cust, orders in customer_orders.items():
        sorted_orders = sorted(orders, key=lambda x: x["date"] if x["date"] else datetime.min)
        cust_spend = sum(o["amount"] for o in sorted_orders)
        if len(sorted_orders) > 1:
            repeat_total_spend += cust_spend
            for i in range(1, len(sorted_orders)):
                d1 = sorted_orders[i - 1]["date"]
                d2 = sorted_orders[i]["date"]
                if d1 and d2:
                    delta_days = (d2 - d1).days
                    if delta_days >= 0:
                        intervals.append(delta_days)
        else:
            single_total_spend += cust_spend

    avg_interval_days = round(sum(intervals) / max(1, len(intervals)), 1) if intervals else 0.0
    avg_repeat_spend = round(repeat_total_spend / max(1, repeat_count), 2)
    single_count = total_unique - repeat_count
    avg_single_spend = round(single_total_spend / max(1, single_count), 2)
    spend_multiplier = round(avg_repeat_spend / max(1.0, avg_single_spend), 1)

    return {
        "has_data": True,
        "unique_customers": total_unique,
        "repeat_customers_count": repeat_count,
        "repeat_rate": repeat_rate,
        "avg_days_between_purchases": avg_interval_days,
        "avg_repeat_customer_spend": avg_repeat_spend,
        "avg_repeat_customer_spend_formatted": _format_inr(avg_repeat_spend),
        "avg_single_customer_spend": avg_single_spend,
        "avg_single_customer_spend_formatted": _format_inr(avg_single_spend),
        "spend_multiplier": spend_multiplier,
        "finding": f"{repeat_count} of {total_unique} buyers ({repeat_rate}%) have returned, spending an average of {_format_inr(avg_repeat_spend)} ({spend_multiplier}x single buyers).",
        "actionable_insight": f"Repeat buyers make follow-up purchases approximately every {avg_interval_days:.0f} days. Announce drop previews to previous buyers 30 minutes before public Instagram drops."
    }
