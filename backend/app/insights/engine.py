from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from backend.app.models.models import (
    Product, SaleOrder, InventoryItem,
    CustomerInquiry, DataQualityLog
)
from backend.app.ml import get_business_predictions


def _safe_pct(numerator: float, denominator: float, decimals: int = 1) -> float:
    """Safe percentage calculation avoiding division by zero."""
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, decimals)


def _format_inr(amount: float) -> str:
    """Format a number as Indian Rupee string."""
    return f"₹{amount:,.0f}"


def compute_seller_insights(
    db: Session,
    period: str = "all",
    category_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Computes objective, mathematical, data-driven business insights across 7 core domains:
    1. Sales (Total sales, growth, orders, units sold, AOV)
    2. Time (Monthly, day-of-week, time-of-day, spikes & drops)
    3. Products (Best-sellers, category breakdown, units vs revenue, fastest/slow moving, sell-through)
    4. Clothing Preferences (Sizes, category x size, price ranges, category x price)
    5. Customer Behavior (Unique buyers, new vs returning, repeat rate, items per order)
    6. Instagram Content -> Sales (Attribution, engagement vs sales matrix, activity correlation)
    7. Business Trends (Data-driven historical shifts in category, size, price, and sales)

    Strictly adheres to: DATA -> PATTERN -> INSIGHT (no speculative recommendations).
    """
    products = db.query(Product).all()
    all_sales = db.query(SaleOrder).all()
    inventory = db.query(InventoryItem).all()
    inquiries = db.query(CustomerInquiry).all()
    latest_quality = db.query(DataQualityLog).order_by(DataQualityLog.uploaded_at.desc()).first()

    if not products or not all_sales:
        return {
            "has_data": False,
            "message": "No business data available yet. Upload a sales spreadsheet or load sample data."
        }

    # Product lookup map
    product_map = {p.product_id: p for p in products}

    # Filter completed sales for revenue, units, order counting and time aggregation
    completed_sales = [
        s for s in all_sales
        if (s.sale_status or "completed").lower() in ("completed", "paid", "success")
    ]

    # Determine reference date (latest completed sale date in dataset)
    sale_dates = [s.sale_date for s in completed_sales if s.sale_date]
    if not sale_dates:
        sale_dates = [s.sale_date for s in all_sales if s.sale_date]
    ref_date = max(sale_dates) if sale_dates else datetime.utcnow()

    # Apply Period Filter to sales
    if period in ("7d", "last_7_days"):
        start_7d = ref_date - timedelta(days=7)
        filtered_sales = [s for s in completed_sales if s.sale_date and s.sale_date >= start_7d]
        start_prior = start_7d - timedelta(days=7)
        prior_sales = [s for s in completed_sales if s.sale_date and start_prior <= s.sale_date < start_7d]
    elif period in ("30d", "last_30_days"):
        start_30d = ref_date - timedelta(days=30)
        filtered_sales = [s for s in completed_sales if s.sale_date and s.sale_date >= start_30d]
        start_prior = start_30d - timedelta(days=30)
        prior_sales = [s for s in completed_sales if s.sale_date and start_prior <= s.sale_date < start_30d]
    elif period in ("this_month", "monthly") or period.startswith("month:") or period.startswith("month_") or (len(period) == 7 and period[4] == "-"):
        target_year = ref_date.year
        target_month = ref_date.month
        clean_p = period.replace("month:", "").replace("month_", "")
        if len(clean_p) == 7 and clean_p[4] == "-":
            try:
                target_year = int(clean_p[:4])
                target_month = int(clean_p[5:7])
            except ValueError:
                pass
        filtered_sales = [
            s for s in completed_sales
            if s.sale_date and s.sale_date.year == target_year and s.sale_date.month == target_month
        ]
        # Prior period: previous month
        prev_month = 12 if target_month == 1 else target_month - 1
        prev_year = target_year - 1 if target_month == 1 else target_year
        prior_sales = [
            s for s in completed_sales
            if s.sale_date and s.sale_date.year == prev_year and s.sale_date.month == prev_month
        ]
    elif period == "last_month":
        prev_month = 12 if ref_date.month == 1 else ref_date.month - 1
        prev_year = ref_date.year - 1 if ref_date.month == 1 else ref_date.year
        filtered_sales = [
            s for s in completed_sales
            if s.sale_date and s.sale_date.year == prev_year and s.sale_date.month == prev_month
        ]
        # Prior period: month before last month
        two_months_ago = 12 if prev_month == 1 else prev_month - 1
        two_months_year = prev_year - 1 if prev_month == 1 else prev_year
        prior_sales = [
            s for s in completed_sales
            if s.sale_date and s.sale_date.year == two_months_year and s.sale_date.month == two_months_ago
        ]
    elif period == "3m":
        start_3m = ref_date - timedelta(days=90)
        filtered_sales = [s for s in completed_sales if s.sale_date and s.sale_date >= start_3m]
        start_prior = start_3m - timedelta(days=90)
        prior_sales = [s for s in completed_sales if s.sale_date and start_prior <= s.sale_date < start_3m]
    elif period == "6m":
        start_6m = ref_date - timedelta(days=180)
        filtered_sales = [s for s in completed_sales if s.sale_date and s.sale_date >= start_6m]
        start_prior = start_6m - timedelta(days=180)
        prior_sales = [s for s in completed_sales if s.sale_date and start_prior <= s.sale_date < start_6m]
    else:  # "all"
        filtered_sales = completed_sales
        # Split all sales in half for comparison if enough data
        if len(completed_sales) > 1 and sale_dates:
            min_date = min(sale_dates)
            mid_date = min_date + (ref_date - min_date) / 2
            prior_sales = [s for s in completed_sales if s.sale_date and s.sale_date < mid_date]
        else:
            prior_sales = []


    # Apply Category Filter if given
    if category_filter and category_filter.lower() != "all":
        cat_lower = category_filter.lower()
        filtered_sales = [
            s for s in filtered_sales
            if product_map.get(s.product_id) and product_map[s.product_id].category.lower() == cat_lower
        ]
        prior_sales = [
            s for s in prior_sales
            if product_map.get(s.product_id) and product_map[s.product_id].category.lower() == cat_lower
        ]

    # If filtered dataset has no sales in this period, keep it as empty list (do not fabricate or fallback to all_sales)
    if filtered_sales is None:
        filtered_sales = []

    # Available categories list for frontend filter dropdown (clothing only)
    available_categories = sorted(list(set(
        p.category for p in products 
        if p.category and "accessor" not in p.category.lower() and "jewel" not in p.category.lower()
    )))

    # =========================================================================
    # SECTION A: SALES ANALYTICS
    # =========================================================================
    total_sales_raw = sum(s.selling_price * s.quantity for s in filtered_sales)
    total_units_sold = sum(s.quantity for s in filtered_sales)
    # Total distinct orders
    order_ids = set(s.order_id for s in filtered_sales if s.order_id)
    total_orders = len(order_ids) if order_ids else len(filtered_sales)
    aov = total_sales_raw / max(1, total_orders)

    # Growth vs prior period
    prior_sales_raw = sum(s.selling_price * s.quantity for s in prior_sales)
    if prior_sales_raw > 0:
        growth_pct = round(((total_sales_raw - prior_sales_raw) / prior_sales_raw) * 100, 1)
    else:
        growth_pct = 0.0

    # 1. This Month & Previous Month Sales
    this_month_sales = [
        s for s in completed_sales
        if s.sale_date and s.sale_date.year == ref_date.year and s.sale_date.month == ref_date.month
    ]
    this_month_rev = sum(s.selling_price * s.quantity for s in this_month_sales)
    this_month_orders = len(set(s.order_id for s in this_month_sales if s.order_id)) or len(this_month_sales)
    this_month_units = sum(s.quantity for s in this_month_sales)

    prev_month_num = 12 if ref_date.month == 1 else ref_date.month - 1
    prev_year_num = ref_date.year - 1 if ref_date.month == 1 else ref_date.year
    prev_month_sales = [
        s for s in completed_sales
        if s.sale_date and s.sale_date.year == prev_year_num and s.sale_date.month == prev_month_num
    ]
    prev_month_rev = sum(s.selling_price * s.quantity for s in prev_month_sales)
    if prev_month_rev > 0:
        this_month_growth = round(((this_month_rev - prev_month_rev) / prev_month_rev) * 100, 1)
    else:
        this_month_growth = 0.0

    # 2. This Week Sales (last 7 days from ref_date)
    week_start = ref_date - timedelta(days=7)
    this_week_sales = [
        s for s in completed_sales
        if s.sale_date and s.sale_date >= week_start
    ]
    this_week_rev = sum(s.selling_price * s.quantity for s in this_week_sales)
    this_week_orders = len(set(s.order_id for s in this_week_sales if s.order_id)) or len(this_week_sales)
    this_week_units = sum(s.quantity for s in this_week_sales)

    # 3. Sales by Month (All historical for timeline, plus period-scoped)
    all_monthly_data = defaultdict(lambda: {"revenue": 0.0, "units": 0, "order_ids": set(), "sort_key": ""})
    for s in completed_sales:
        if s.sale_date:
            m_key = s.sale_date.strftime("%B %Y")
            s_key = s.sale_date.strftime("%Y-%m")
            all_monthly_data[m_key]["revenue"] += s.selling_price * s.quantity
            all_monthly_data[m_key]["units"] += s.quantity
            all_monthly_data[m_key]["order_ids"].add(s.order_id or f"row_{s.id}")
            all_monthly_data[m_key]["sort_key"] = s_key

    all_sales_by_month = []
    sorted_all_months = sorted(all_monthly_data.items(), key=lambda x: x[1]["sort_key"])
    for m_label, m_vals in sorted_all_months:
        display_m = m_label.split()[0][:3] if " " in m_label else m_label[:3]
        all_sales_by_month.append({
            "month": m_label,
            "sort_key": m_vals["sort_key"],
            "display_month": display_m,
            "display_date": display_m,
            "revenue": round(m_vals["revenue"], 2),
            "revenue_formatted": _format_inr(m_vals["revenue"]),
            "units": m_vals["units"],
            "orders": len(m_vals["order_ids"]),
        })

    # Period-scoped monthly data
    period_monthly_data = defaultdict(lambda: {"revenue": 0.0, "units": 0, "order_ids": set(), "sort_key": ""})
    for s in filtered_sales:
        if s.sale_date:
            m_key = s.sale_date.strftime("%B %Y")
            s_key = s.sale_date.strftime("%Y-%m")
            period_monthly_data[m_key]["revenue"] += s.selling_price * s.quantity
            period_monthly_data[m_key]["units"] += s.quantity
            period_monthly_data[m_key]["order_ids"].add(s.order_id or f"row_{s.id}")
            period_monthly_data[m_key]["sort_key"] = s_key

    sales_by_month = []
    sorted_period_months = sorted(period_monthly_data.items(), key=lambda x: x[1]["sort_key"])
    for m_label, m_vals in sorted_period_months:
        display_m = m_label.split()[0][:3] if " " in m_label else m_label[:3]
        sales_by_month.append({
            "month": m_label,
            "sort_key": m_vals["sort_key"],
            "display_month": display_m,
            "display_date": display_m,
            "revenue": round(m_vals["revenue"], 2),
            "revenue_formatted": _format_inr(m_vals["revenue"]),
            "units": m_vals["units"],
            "orders": len(m_vals["order_ids"]),
        })

    # Fallback to all_sales_by_month if period is all or no period sales
    if not sales_by_month or period == "all":
        sales_by_month = all_sales_by_month

    active_months = [m for m in sales_by_month if m["revenue"] > 0]
    strongest_month = max(active_months, key=lambda x: x["revenue"]) if active_months else None
    month_insight = (
        f"{strongest_month['month']} was the strongest sales month at {strongest_month['revenue_formatted']}."
        if strongest_month else "Monthly trajectory will show here."
    )

    # 4. Sales by Day of Week
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_totals = {d: {"revenue": 0.0, "orders": 0, "units": 0, "dates_seen": set()} for d in day_names}
    for s in filtered_sales:
        if s.sale_date:
            d_name = day_names[s.sale_date.weekday()]
            day_totals[d_name]["revenue"] += s.selling_price * s.quantity
            day_totals[d_name]["orders"] += 1
            day_totals[d_name]["units"] += s.quantity
            day_totals[d_name]["dates_seen"].add(s.sale_date.date())

    sales_by_day = []
    for d_name in day_names:
        num_days = max(1, len(day_totals[d_name]["dates_seen"]))
        rev = day_totals[d_name]["revenue"]
        avg_rev = rev / num_days
        sales_by_day.append({
            "day": d_name,
            "total_revenue": round(rev, 2),
            "total_revenue_formatted": _format_inr(rev),
            "avg_revenue": round(avg_rev, 2),
            "avg_revenue_formatted": _format_inr(avg_rev),
            "orders": day_totals[d_name]["orders"],
            "units": day_totals[d_name]["units"],
        })

    active_days = [d for d in sales_by_day if d["total_revenue"] > 0]
    strongest_day = max(active_days, key=lambda x: x["total_revenue"]) if active_days else None
    day_insight = (
        f"{strongest_day['day']} has the highest sales revenue at {strongest_day['total_revenue_formatted']}."
        if strongest_day else "No weekday sales recorded in this period."
    )

    # 5. Daily Sales Timeline (Day-by-day)
    daily_totals = defaultdict(lambda: {"revenue": 0.0, "orders": 0, "units": 0})
    for s in filtered_sales:
        if s.sale_date:
            d_key = s.sale_date.strftime("%Y-%m-%d")
            daily_totals[d_key]["revenue"] += s.selling_price * s.quantity
            daily_totals[d_key]["orders"] += 1
            daily_totals[d_key]["units"] += s.quantity

    daily_sales = []
    for d_str in sorted(daily_totals.keys()):
        dt = datetime.strptime(d_str, "%Y-%m-%d")
        daily_sales.append({
            "date": d_str,
            "display_date": dt.strftime("%b %d"),
            "day_name": dt.strftime("%A"),
            "revenue": round(daily_totals[d_str]["revenue"], 2),
            "revenue_formatted": _format_inr(daily_totals[d_str]["revenue"]),
            "orders": daily_totals[d_str]["orders"],
            "units": daily_totals[d_str]["units"]
        })

    # 6. Sales Spikes and Drops
    spikes_and_drops = []
    if len(daily_totals) >= 3:
        avg_daily_sales = sum(v["revenue"] for v in daily_totals.values()) / len(daily_totals)
        for d_str, d_val in sorted(daily_totals.items()):
            d_rev = d_val["revenue"]
            if avg_daily_sales > 0:
                pct_diff = round(((d_rev - avg_daily_sales) / avg_daily_sales) * 100, 1)
                dt = datetime.strptime(d_str, "%Y-%m-%d")
                day_name = dt.strftime("%A")
                if pct_diff >= 50.0:
                    spikes_and_drops.append({
                        "type": "SPIKE",
                        "date": d_str,
                        "day_name": day_name,
                        "sales": round(d_rev, 2),
                        "sales_formatted": _format_inr(d_rev),
                        "pct_change": pct_diff,
                        "headline": f"{day_name} sales increased {abs(pct_diff):.0f}% above your normal daily average.",
                        "baseline_formatted": _format_inr(avg_daily_sales)
                    })
                elif pct_diff <= -35.0:
                    spikes_and_drops.append({
                        "type": "DROP",
                        "date": d_str,
                        "day_name": day_name,
                        "sales": round(d_rev, 2),
                        "sales_formatted": _format_inr(d_rev),
                        "pct_change": pct_diff,
                        "headline": f"{day_name} sales were {abs(pct_diff):.0f}% below the normal daily average.",
                        "baseline_formatted": _format_inr(avg_daily_sales)
                    })

        if spikes_and_drops:
            spikes_and_drops.sort(key=lambda x: abs(x["pct_change"]), reverse=True)
            spikes_and_drops = spikes_and_drops[:3]

    # 7. Timeline Series for Sales Overview (Last 7 Days, Last 30 Days, Monthly)
    ref_day = ref_date.date()
    daily_sales_map = defaultdict(lambda: {"revenue": 0.0, "order_ids": set(), "units": 0})
    for s in completed_sales:
        if s.sale_date:
            d_key = s.sale_date.date()
            daily_sales_map[d_key]["revenue"] += s.selling_price * s.quantity
            daily_sales_map[d_key]["order_ids"].add(s.order_id or f"row_{s.id}")
            daily_sales_map[d_key]["units"] += s.quantity

    # (a) Last 7 Days (consecutive daily points, zero-filled if no sales)
    timeline_7d = []
    for i in range(6, -1, -1):
        target_d = ref_day - timedelta(days=i)
        vals = daily_sales_map[target_d]
        timeline_7d.append({
            "date": target_d.strftime("%Y-%m-%d"),
            "display_date": target_d.strftime("%b %d"),
            "day_name": target_d.strftime("%a"),
            "revenue": round(vals["revenue"], 2),
            "revenue_formatted": _format_inr(vals["revenue"]),
            "orders": len(vals["order_ids"]),
            "units": vals["units"]
        })

    rev_7d = sum(p["revenue"] for p in timeline_7d)
    prior_7d_rev = sum(daily_sales_map[ref_day - timedelta(days=i)]["revenue"] for i in range(13, 6, -1))
    growth_7d = round(((rev_7d - prior_7d_rev) / prior_7d_rev) * 100, 1) if prior_7d_rev > 0 else 0.0

    timeline_7d_summary = {
        "total_revenue": round(rev_7d, 2),
        "total_revenue_formatted": _format_inr(rev_7d),
        "avg_daily_revenue": round(rev_7d / 7.0, 2),
        "avg_daily_revenue_formatted": _format_inr(rev_7d / 7.0),
        "total_orders": sum(p["orders"] for p in timeline_7d),
        "total_units": sum(p["units"] for p in timeline_7d),
        "prior_revenue": round(prior_7d_rev, 2),
        "prior_revenue_formatted": _format_inr(prior_7d_rev),
        "growth_pct": growth_7d,
        "growth_is_positive": growth_7d >= 0,
        "date_range": f"{timeline_7d[0]['display_date']} - {timeline_7d[-1]['display_date']}, {ref_day.year}"
    }

    # (b) Last 30 Days (consecutive daily points, zero-filled if no sales)
    timeline_30d = []
    for i in range(29, -1, -1):
        target_d = ref_day - timedelta(days=i)
        vals = daily_sales_map[target_d]
        timeline_30d.append({
            "date": target_d.strftime("%Y-%m-%d"),
            "display_date": target_d.strftime("%b %d"),
            "day_name": target_d.strftime("%a"),
            "revenue": round(vals["revenue"], 2),
            "revenue_formatted": _format_inr(vals["revenue"]),
            "orders": len(vals["order_ids"]),
            "units": vals["units"]
        })

    rev_30d = sum(p["revenue"] for p in timeline_30d)
    prior_30d_rev = sum(daily_sales_map[ref_day - timedelta(days=i)]["revenue"] for i in range(59, 29, -1))
    growth_30d = round(((rev_30d - prior_30d_rev) / prior_30d_rev) * 100, 1) if prior_30d_rev > 0 else 0.0

    timeline_30d_summary = {
        "total_revenue": round(rev_30d, 2),
        "total_revenue_formatted": _format_inr(rev_30d),
        "avg_daily_revenue": round(rev_30d / 30.0, 2),
        "avg_daily_revenue_formatted": _format_inr(rev_30d / 30.0),
        "total_orders": sum(p["orders"] for p in timeline_30d),
        "total_units": sum(p["units"] for p in timeline_30d),
        "prior_revenue": round(prior_30d_rev, 2),
        "prior_revenue_formatted": _format_inr(prior_30d_rev),
        "growth_pct": growth_30d,
        "growth_is_positive": growth_30d >= 0,
        "date_range": f"{timeline_30d[0]['display_date']} - {timeline_30d[-1]['display_date']}, {ref_day.year}"
    }

    # (c) Monthly timeline
    timeline_monthly = all_sales_by_month[-12:] if len(all_sales_by_month) > 12 else all_sales_by_month
    monthly_rev_total = sum(m["revenue"] for m in timeline_monthly)
    months_count = max(1, len(timeline_monthly))
    timeline_monthly_summary = {
        "total_revenue": round(monthly_rev_total, 2),
        "total_revenue_formatted": _format_inr(monthly_rev_total),
        "avg_monthly_revenue": round(monthly_rev_total / months_count, 2),
        "avg_monthly_revenue_formatted": _format_inr(monthly_rev_total / months_count),
        "total_orders": sum(m["orders"] for m in timeline_monthly),
        "total_units": sum(m["units"] for m in timeline_monthly),
        "date_range": f"{timeline_monthly[0]['month']} - {timeline_monthly[-1]['month']}" if timeline_monthly else "All Months"
    }

    # (d) Sales Comparison Objects
    diff_month_rev = this_month_rev - prev_month_rev
    month_comparison = {
        "period_type": "month",
        "current_label": ref_date.strftime("%B %Y"),
        "prior_label": datetime(prev_year_num, prev_month_num, 1).strftime("%B %Y"),
        "current_revenue": round(this_month_rev, 2),
        "current_revenue_formatted": _format_inr(this_month_rev),
        "prior_revenue": round(prev_month_rev, 2),
        "prior_revenue_formatted": _format_inr(prev_month_rev),
        "diff_revenue": round(diff_month_rev, 2),
        "diff_revenue_formatted": f"{'+' if diff_month_rev >= 0 else '-'}₹{abs(diff_month_rev):,.0f}",
        "pct_change": this_month_growth,
        "is_positive": diff_month_rev >= 0,
        "current_orders": this_month_orders,
        "prior_orders": len(set(s.order_id for s in prev_month_sales if s.order_id)) or len(prev_month_sales),
        "current_units": this_month_units,
        "prior_units": sum(s.quantity for s in prev_month_sales)
    }

    diff_week_rev = rev_7d - prior_7d_rev
    week_comparison = {
        "period_type": "week",
        "current_label": "Last 7 Days",
        "prior_label": "Previous 7 Days",
        "current_revenue": round(rev_7d, 2),
        "current_revenue_formatted": _format_inr(rev_7d),
        "prior_revenue": round(prior_7d_rev, 2),
        "prior_revenue_formatted": _format_inr(prior_7d_rev),
        "diff_revenue": round(diff_week_rev, 2),
        "diff_revenue_formatted": f"{'+' if diff_week_rev >= 0 else '-'}₹{abs(diff_week_rev):,.0f}",
        "pct_change": growth_7d,
        "is_positive": diff_week_rev >= 0,
        "current_orders": timeline_7d_summary["total_orders"],
        "prior_orders": sum(len(daily_sales_map[ref_day - timedelta(days=i)]["order_ids"]) for i in range(13, 6, -1)),
        "current_units": timeline_7d_summary["total_units"],
        "prior_units": sum(daily_sales_map[ref_day - timedelta(days=i)]["units"] for i in range(13, 6, -1))
    }

    total_cost_raw = sum(
        (product_map[s.product_id].cost_price if s.product_id in product_map and product_map[s.product_id].cost_price > 0 else s.selling_price * 0.35) * s.quantity
        for s in filtered_sales
    )
    total_profit_raw = max(0.0, total_sales_raw - total_cost_raw)
    gross_margin_pct = _safe_pct(total_profit_raw, total_sales_raw)

    sales_section = {
        "period": period,
        "total_sales_raw": round(total_sales_raw, 2),
        "total_sales_formatted": _format_inr(total_sales_raw),
        "total_cost_raw": round(total_cost_raw, 2),
        "total_cost_formatted": _format_inr(total_cost_raw),
        "total_profit_raw": round(total_profit_raw, 2),
        "total_profit_formatted": _format_inr(total_profit_raw),
        "gross_margin_pct": gross_margin_pct,
        "total_orders": total_orders,
        "units_sold": total_units_sold,
        "aov_raw": round(aov, 2),
        "aov_formatted": _format_inr(aov),
        "growth_pct": growth_pct,
        "growth_is_positive": growth_pct >= 0,
        "prior_period_sales_formatted": _format_inr(prior_sales_raw) if prior_sales_raw > 0 else None,
        "key_insight": f"Generated {_format_inr(total_sales_raw)} across {total_orders} orders ({total_units_sold} units) at an AOV of {_format_inr(aov)}.",
        "this_month": {
            "revenue": round(this_month_rev, 2),
            "revenue_formatted": _format_inr(this_month_rev),
            "orders": this_month_orders,
            "units": this_month_units,
            "growth_vs_last_month": this_month_growth,
            "growth_is_positive": this_month_growth >= 0,
            "month_name": ref_date.strftime("%B %Y"),
            "prev_month_formatted": _format_inr(prev_month_rev)
        },
        "this_week": {
            "revenue": round(this_week_rev, 2),
            "revenue_formatted": _format_inr(this_week_rev),
            "orders": this_week_orders,
            "units": this_week_units
        },
        "timeline": {
            "last_7_days": {
                "points": timeline_7d,
                "summary": timeline_7d_summary
            },
            "last_30_days": {
                "points": timeline_30d,
                "summary": timeline_30d_summary
            },
            "monthly": {
                "points": timeline_monthly,
                "summary": timeline_monthly_summary
            }
        },
        "sales_comparison": {
            "month": month_comparison,
            "week": week_comparison,
            "default": "month"
        },
        "sales_by_month": sales_by_month,
        "all_sales_by_month": all_sales_by_month,
        "month_insight": month_insight,
        "sales_by_day": sales_by_day,
        "day_insight": day_insight,
        "daily_sales": daily_sales,
        "spikes_and_drops": spikes_and_drops[:3]
    }

    time_section = {
        "sales_by_month": sales_by_month,
        "month_insight": month_insight,
        "sales_by_day": sales_by_day,
        "day_insight": day_insight,
        "daily_sales": daily_sales,
        "spikes_and_drops": spikes_and_drops[:4]
    }

    # =========================================================================
    # SECTION C: PRODUCT ANALYTICS
    # =========================================================================
    inv_map = {inv.product_id: inv for inv in inventory}

    # Clothing-only products
    clothing_products = [
        p for p in products
        if p.category and "accessor" not in p.category.lower() and "jewel" not in p.category.lower()
    ]

    # Category scope for products
    if category_filter and category_filter.lower() != "all":
        cat_lower = category_filter.lower()
        active_products = [p for p in clothing_products if p.category and p.category.lower() == cat_lower]
    else:
        active_products = clothing_products

    product_stats = {}
    for p in active_products:
        inv = inv_map.get(p.product_id)
        stock_dt = (inv.date_stocked if inv else None) or p.date_sourced or p.created_at or ref_date
        product_stats[p.product_id] = {
            "product_id": p.product_id,
            "product_name": p.product_name,
            "category": p.category,
            "aesthetic": p.aesthetic,
            "size": p.size,
            "retail_price": p.retail_price,
            "retail_price_formatted": _format_inr(p.retail_price),
            "units_sold": 0,
            "revenue": 0.0,
            "first_sale_date": None,
            "date_stocked": stock_dt
        }

    for s in filtered_sales:
        if s.product_id in product_stats:
            p = product_stats[s.product_id]
            p["units_sold"] += s.quantity
            p["revenue"] += s.selling_price * s.quantity
            if s.sale_date and (p["first_sale_date"] is None or s.sale_date < p["first_sale_date"]):
                p["first_sale_date"] = s.sale_date

    for p in product_stats.values():
        p["pct_of_sales"] = _safe_pct(p["revenue"], total_sales_raw)
        p["revenue_formatted"] = _format_inr(p["revenue"])

    all_product_list = list(product_stats.values())

    # Products with sales in selected period/category
    sold_products = [p for p in all_product_list if p["units_sold"] > 0]
    best_sellers_by_units = sorted(sold_products, key=lambda x: (x["units_sold"], x["revenue"]), reverse=True)[:5]
    best_sellers_by_revenue = sorted(sold_products, key=lambda x: (x["revenue"], x["units_sold"]), reverse=True)[:5]

    # Category performance (aggregated directly from filtered_sales for absolute consistency)
    cat_summary = defaultdict(lambda: {"revenue": 0.0, "units": 0, "products_count": 0})
    for s in filtered_sales:
        p = product_map.get(s.product_id)
        cat_name = p.category if p and p.category else "Uncategorized"
        cat_summary[cat_name]["revenue"] += s.selling_price * s.quantity
        cat_summary[cat_name]["units"] += s.quantity

    for p in all_product_list:
        if p["category"] in cat_summary:
            cat_summary[p["category"]]["products_count"] += 1

    sales_by_category = []
    for cat_name, c_data in sorted(cat_summary.items(), key=lambda x: x[1]["revenue"], reverse=True):
        if not cat_name or "accessor" in cat_name.lower() or "jewel" in cat_name.lower():
            continue
        sales_by_category.append({
            "category": cat_name,
            "revenue": round(c_data["revenue"], 2),
            "revenue_formatted": _format_inr(c_data["revenue"]),
            "units_sold": c_data["units"],
            "pct_of_total": _safe_pct(c_data["revenue"], total_sales_raw),
            "pct_of_units": _safe_pct(c_data["units"], total_units_sold)
        })

    top_cat = sales_by_category[0] if sales_by_category else None
    category_insight = (
        f"{top_cat['category']} generated {top_cat['pct_of_total']}% of total revenue."
        if top_cat else ""
    )

    # Units Sold vs Revenue Contrast
    top_volume_item = best_sellers_by_units[0] if best_sellers_by_units else None
    top_revenue_item = best_sellers_by_revenue[0] if best_sellers_by_revenue else None

    is_same = (top_volume_item["product_id"] == top_revenue_item["product_id"]) if (top_volume_item and top_revenue_item) else False

    volume_vs_revenue_contrast = {
        "volume_leader": {
            "product_id": top_volume_item["product_id"] if top_volume_item else None,
            "name": top_volume_item["product_name"] if top_volume_item else "N/A",
            "category": top_volume_item["category"] if top_volume_item else "",
            "units": top_volume_item["units_sold"] if top_volume_item else 0,
            "revenue": top_volume_item["revenue"] if top_volume_item else 0.0,
            "revenue_formatted": top_volume_item["revenue_formatted"] if top_volume_item else "₹0",
            "unit_price_formatted": top_volume_item["retail_price_formatted"] if top_volume_item else "₹0",
        } if top_volume_item else None,
        "revenue_leader": {
            "product_id": top_revenue_item["product_id"] if top_revenue_item else None,
            "name": top_revenue_item["product_name"] if top_revenue_item else "N/A",
            "category": top_revenue_item["category"] if top_revenue_item else "",
            "units": top_revenue_item["units_sold"] if top_revenue_item else 0,
            "revenue": top_revenue_item["revenue"] if top_revenue_item else 0.0,
            "revenue_formatted": top_revenue_item["revenue_formatted"] if top_revenue_item else "₹0",
            "unit_price_formatted": top_revenue_item["retail_price_formatted"] if top_revenue_item else "₹0",
        } if top_revenue_item else None,
        "is_different": not is_same if (top_volume_item and top_revenue_item) else False,
        "is_same": is_same,
        "finding": (
            f"'{top_volume_item['product_name']}' drove the highest volume ({top_volume_item['units_sold']} units), while '{top_revenue_item['product_name']}' generated the most revenue ({top_revenue_item['revenue_formatted']})."
            if (top_volume_item and top_revenue_item and not is_same)
            else f"'{top_volume_item['product_name']}' leads both volume ({top_volume_item['units_sold']} units) and revenue ({top_volume_item['revenue_formatted']})."
            if (top_volume_item and is_same)
            else "No sales recorded in this period to contrast leaders."
        )
    }

    # Fastest-Selling Products
    # Calculate time to sale only when genuine listing timestamps exist and first_sale_date > date_stocked
    fastest_selling = []
    for p in sold_products:
        if p["first_sale_date"] and p["date_stocked"]:
            diff_seconds = (p["first_sale_date"] - p["date_stocked"]).total_seconds()
            if diff_seconds > 0:
                diff_hours = diff_seconds / 3600.0
                if diff_seconds < 3600:
                    mins = max(1, int(diff_seconds // 60))
                    disp_time = f"{mins} min" if mins == 1 else f"{mins} mins"
                elif diff_hours < 24:
                    hrs = int(round(diff_hours))
                    disp_time = f"{hrs} hour" if hrs == 1 else f"{hrs} hours"
                else:
                    days = max(1, int(diff_hours // 24))
                    disp_time = f"{days} day" if days == 1 else f"{days} days"

                fastest_selling.append({
                    "product_name": p["product_name"],
                    "category": p["category"],
                    "hours_to_sale": round(diff_hours, 2),
                    "display_time": disp_time,
                    "units_sold": p["units_sold"],
                    "revenue": p["revenue"],
                    "revenue_formatted": p["revenue_formatted"]
                })
    fastest_selling = sorted(fastest_selling, key=lambda x: x["hours_to_sale"])[:5]

    # Slow-Moving Products
    # Only include products that are currently available for sale in inventory (status == 'Available' or quantity_on_hand > 0)
    # and have registered 0 sales in the period.
    slow_moving = []
    for p in all_product_list:
        inv = inv_map.get(p["product_id"])
        is_available = inv and (inv.status == "Available" or (inv.quantity_on_hand and inv.quantity_on_hand > 0))
        if is_available and p["units_sold"] == 0:
            stock_date = inv.date_stocked or p["date_stocked"] or ref_date
            days_in_stock = (ref_date - stock_date).days
            slow_moving.append({
                "product_name": p["product_name"],
                "category": p["category"],
                "days_listed": max(1, days_in_stock),
                "price": p["retail_price"],
                "price_formatted": p["retail_price_formatted"]
            })
    slow_moving = sorted(slow_moving, key=lambda x: x["days_listed"], reverse=True)[:5]

    # Sell-Through Rate
    # Ratio of sold units in period to total pieces in scope (sold + currently available)
    total_stocked_units = total_units_sold + len(slow_moving)
    sell_through_rate = _safe_pct(total_units_sold, total_stocked_units) if total_stocked_units > 0 else 0.0

    products_section = {
        "best_sellers_by_units": best_sellers_by_units,
        "best_sellers_by_revenue": best_sellers_by_revenue,
        "sales_by_category": sales_by_category,
        "category_insight": category_insight,
        "volume_vs_revenue_contrast": volume_vs_revenue_contrast,
        "fastest_selling": fastest_selling,
        "slow_moving": slow_moving,
        "sell_through_rate": sell_through_rate,
        "sell_through_insight": f"{total_units_sold} of {total_stocked_units} curated pieces sold ({sell_through_rate}% sell-through rate)." if total_stocked_units > 0 else "No inventory records in scope."
    }

    # =========================================================================
    # SECTION D: CLOTHING SPECIFIC PREFERENCES
    # =========================================================================
    # 1. Sales by Size (strictly clothing sales only)
    clothing_sales = [
        s for s in filtered_sales
        if product_map.get(s.product_id) and product_map[s.product_id].category
        and "accessor" not in product_map[s.product_id].category.lower()
        and "jewel" not in product_map[s.product_id].category.lower()
    ]
    clothing_total_units = sum(s.quantity for s in clothing_sales)
    clothing_total_sales_raw = sum(s.selling_price * s.quantity for s in clothing_sales)

    size_counts = Counter()
    size_revenues = defaultdict(float)
    for s in clothing_sales:
        p = product_map.get(s.product_id)
        if p and p.size:
            sz_clean = p.size.strip().upper()
            size_counts[sz_clean] += s.quantity
            size_revenues[sz_clean] += s.selling_price * s.quantity

    sales_by_size = [
        {
            "size": sz,
            "units_sold": cnt,
            "revenue": round(size_revenues[sz], 2),
            "revenue_formatted": _format_inr(size_revenues[sz]),
            "pct_of_sales": _safe_pct(cnt, clothing_total_units)
        }
        for sz, cnt in size_counts.most_common()
    ]
    top_size = sales_by_size[0] if sales_by_size else None
    size_insight = (
        f"Size {top_size['size']} is your highest-selling size ({top_size['units_sold']} units, {top_size['pct_of_sales']}% of all garment sales)."
        if top_size else "Size distribution will appear here once sales are recorded."
    )

    # 2. Category x Size Matrix
    cat_size_counts = defaultdict(Counter)
    for s in clothing_sales:
        p = product_map.get(s.product_id)
        if p and p.category and p.size:
            sz_clean = p.size.strip().upper()
            cat_size_counts[p.category][sz_clean] += s.quantity

    # Standard order of clothing categories
    preferred_cat_order = ["Outerwear", "Tops", "Bottoms", "Dresses"]
    sorted_cats = sorted(
        cat_size_counts.keys(),
        key=lambda c: preferred_cat_order.index(c) if c in preferred_cat_order else 99
    )

    category_x_size = []
    for cat_name in sorted_cats:
        sizes = cat_size_counts[cat_name]
        cat_total_units = sum(sizes.values())
        top_cat_size = sizes.most_common(1)[0] if sizes else ("N/A", 0)
        dominant_pct = _safe_pct(top_cat_size[1], cat_total_units)
        
        breakdown_items = [
            {
                "size": sz,
                "units": u,
                "pct": _safe_pct(u, cat_total_units)
            }
            for sz, u in sizes.most_common()
        ]
        
        category_x_size.append({
            "category": cat_name,
            "total_units": cat_total_units,
            "dominant_size": top_cat_size[0],
            "dominant_size_units": top_cat_size[1],
            "dominant_size_pct": dominant_pct,
            "breakdown": breakdown_items
        })

    cat_size_findings = []
    for item in category_x_size[:2]:
        cat_size_findings.append(f"Size {item['dominant_size']} is strongest for {item['category']} ({item['dominant_size_pct']}%)")
    cat_size_insight = ". ".join(cat_size_findings) + "." if cat_size_findings else ""

    # 3. Sales by Price Range (Non-overlapping, comprehensive brackets)
    price_brackets = [
        {"label": "₹0 – ₹499", "min": 0, "max": 500, "units": 0, "revenue": 0.0, "orders": 0},
        {"label": "₹500 – ₹999", "min": 500, "max": 1000, "units": 0, "revenue": 0.0, "orders": 0},
        {"label": "₹1,000 – ₹1,499", "min": 1000, "max": 1500, "units": 0, "revenue": 0.0, "orders": 0},
        {"label": "₹1,500 – ₹1,999", "min": 1500, "max": 2000, "units": 0, "revenue": 0.0, "orders": 0},
        {"label": "₹2,000+", "min": 2000, "max": 9999999, "units": 0, "revenue": 0.0, "orders": 0},
    ]

    for s in clothing_sales:
        price = s.selling_price
        for b in price_brackets:
            if b["min"] <= price < b["max"]:
                b["units"] += s.quantity
                b["revenue"] += price * s.quantity
                b["orders"] += 1
                break

    sales_by_price_range = [
        {
            "range": b["label"],
            "units": b["units"],
            "orders": b["orders"],
            "revenue": round(b["revenue"], 2),
            "revenue_formatted": _format_inr(b["revenue"]),
            "pct_of_sales": _safe_pct(b["revenue"], clothing_total_sales_raw),
            "pct_of_units": _safe_pct(b["units"], clothing_total_units)
        }
        for b in price_brackets
    ]

    # Best-performing price bracket by revenue and by volume
    active_brackets = [b for b in sales_by_price_range if b["revenue"] > 0]
    top_revenue_bracket = max(active_brackets, key=lambda x: x["revenue"]) if active_brackets else sales_by_price_range[0]
    top_volume_bracket = max(active_brackets, key=lambda x: x["units"]) if active_brackets else sales_by_price_range[0]

    dominant_price_bracket = top_revenue_bracket
    price_range_insight = (
        f"{top_revenue_bracket['range']} generates the highest revenue at {top_revenue_bracket['revenue_formatted']} ({top_revenue_bracket['pct_of_sales']}% of sales), with {top_revenue_bracket['units']} units sold."
        if top_revenue_bracket["revenue"] > 0 else "Price performance will appear here once sales are recorded."
    )

    # 4. Category x Price Sweet Spots (Defined by highest revenue price bracket per category)
    cat_price_brackets = defaultdict(lambda: defaultdict(lambda: {"revenue": 0.0, "units": 0}))
    cat_all_prices = defaultdict(list)

    for s in clothing_sales:
        p = product_map.get(s.product_id)
        if p and p.category:
            cat = p.category
            price = s.selling_price
            cat_all_prices[cat].append(price)
            for b in price_brackets:
                if b["min"] <= price < b["max"]:
                    cat_price_brackets[cat][b["label"]]["revenue"] += price * s.quantity
                    cat_price_brackets[cat][b["label"]]["units"] += s.quantity
                    break

    sorted_price_cats = sorted(
        cat_all_prices.keys(),
        key=lambda c: preferred_cat_order.index(c) if c in preferred_cat_order else 99
    )

    category_x_price = []
    for cat_name in sorted_price_cats:
        prices = cat_all_prices[cat_name]
        brackets = cat_price_brackets[cat_name]
        total_cat_rev = sum(b["revenue"] for b in brackets.values())
        total_cat_units = sum(b["units"] for b in brackets.values())
        avg_p = sum(prices) / max(1, len(prices))

        if brackets and total_cat_rev > 0:
            best_b_label, best_b_data = max(brackets.items(), key=lambda x: x[1]["revenue"])
            rev_pct = _safe_pct(best_b_data["revenue"], total_cat_rev)
            category_x_price.append({
                "category": cat_name,
                "has_data": True,
                "sweet_spot_bracket": best_b_label,
                "revenue": round(best_b_data["revenue"], 2),
                "revenue_formatted": _format_inr(best_b_data["revenue"]),
                "units_sold": best_b_data["units"],
                "rev_pct": rev_pct,
                "total_category_revenue": round(total_cat_rev, 2),
                "total_category_revenue_formatted": _format_inr(total_cat_rev),
                "total_category_units": total_cat_units,
                "avg_price_formatted": _format_inr(avg_p),
                "finding": f"{cat_name} performs best in {best_b_label} ({_format_inr(best_b_data['revenue'])}, {best_b_data['units']} units, {rev_pct}% of category rev). Average price: {_format_inr(avg_p)}."
            })
        else:
            category_x_price.append({
                "category": cat_name,
                "has_data": False,
                "sweet_spot_bracket": "N/A",
                "revenue": 0.0,
                "revenue_formatted": "₹0",
                "units_sold": 0,
                "rev_pct": 0.0,
                "total_category_revenue": 0.0,
                "total_category_revenue_formatted": "₹0",
                "total_category_units": 0,
                "avg_price_formatted": "₹0",
                "finding": "Insufficient sales data in this period."
            })

    clothing_section = {
        "dominant_size": top_size or {"size": "N/A", "units_sold": 0, "pct_of_sales": 0, "revenue_formatted": "₹0"},
        "sales_by_size": sales_by_size,
        "size_insight": size_insight,
        "category_x_size": category_x_size,
        "cat_size_insight": cat_size_insight,
        "sales_by_price_range": sales_by_price_range,
        "price_range_insight": price_range_insight,
        "dominant_price_bracket": dominant_price_bracket,
        "top_revenue_bracket": top_revenue_bracket,
        "top_volume_bracket": top_volume_bracket,
        "category_x_price": category_x_price
    }

    # =========================================================================
    # SECTION E: CUSTOMER BEHAVIOR ANALYTICS
    # =========================================================================
    # All historical buyers for lifetime metrics
    all_buyer_order_counts = Counter()
    all_buyer_spend = defaultdict(float)
    all_buyer_first_order = {}
    for s in all_sales:
        h = s.customer_identifier or ""
        if h and not h.startswith("Anonymous"):
            all_buyer_order_counts[h] += 1
            all_buyer_spend[h] += s.selling_price * s.quantity
            if h not in all_buyer_first_order:
                all_buyer_first_order[h] = s.sale_date
            elif s.sale_date and all_buyer_first_order[h] and s.sale_date < all_buyer_first_order[h]:
                all_buyer_first_order[h] = s.sale_date

    all_time_unique_customers = len(all_buyer_order_counts)
    all_time_total_spend = sum(all_buyer_spend.values())
    avg_customer_spend_lifetime = round(all_time_total_spend / max(1, all_time_unique_customers), 2)
    all_time_returning = sum(1 for cnt in all_buyer_order_counts.values() if cnt > 1)
    all_time_repeat_rate = _safe_pct(all_time_returning, all_time_unique_customers)

    # Reporting period buyers
    buyer_order_counts = Counter()
    buyer_spend = defaultdict(float)
    for s in filtered_sales:
        h = s.customer_identifier or ""
        if h and not h.startswith("Anonymous"):
            buyer_order_counts[h] += 1
            buyer_spend[h] += s.selling_price * s.quantity

    has_customer_data = len(buyer_order_counts) > 0
    if has_customer_data:
        unique_customers = len(buyer_order_counts)
        if period == "all":
            returning_customers = sum(1 for cnt in buyer_order_counts.values() if cnt > 1)
            new_customers = unique_customers - returning_customers
        else:
            returning_customers = sum(1 for h in buyer_order_counts.keys() if all_buyer_order_counts[h] > 1)
            new_customers = unique_customers - returning_customers

        returning_pct = _safe_pct(returning_customers, unique_customers)
        new_pct = round(100.0 - returning_pct, 1)
        repeat_purchase_rate = returning_pct

        avg_purchases_per_customer = round(total_orders / max(1, unique_customers), 2)
        avg_customer_spend = round(total_sales_raw / max(1, unique_customers), 2)
        avg_items_per_order = round(total_units_sold / max(1, total_orders), 2)

        top_buyers = []
        for h, cnt in buyer_order_counts.most_common(12):
            top_buyers.append({
                "handle": h,
                "orders_count": cnt,
                "total_spend": round(buyer_spend[h], 2),
                "total_spend_formatted": _format_inr(buyer_spend[h]),
                "lifetime_orders_count": all_buyer_order_counts[h],
                "lifetime_spend": round(all_buyer_spend[h], 2),
                "lifetime_spend_formatted": _format_inr(all_buyer_spend[h]),
                "first_order_date": all_buyer_first_order[h].strftime("%b %d, %Y") if h in all_buyer_first_order and all_buyer_first_order[h] else "N/A"
            })

        customer_section = {
            "available": True,
            "unique_customers": unique_customers,
            "all_time_unique_customers": all_time_unique_customers,
            "new_customers": new_customers,
            "new_pct": new_pct,
            "returning_customers": returning_customers,
            "returning_pct": returning_pct,
            "repeat_purchase_rate": repeat_purchase_rate,
            "all_time_repeat_rate": all_time_repeat_rate,
            "avg_purchases_per_customer": avg_purchases_per_customer,
            "avg_customer_spend": avg_customer_spend,
            "avg_customer_spend_formatted": _format_inr(avg_customer_spend),
            "avg_customer_spend_lifetime": avg_customer_spend_lifetime,
            "avg_customer_spend_lifetime_formatted": _format_inr(avg_customer_spend_lifetime),
            "avg_items_per_order": avg_items_per_order,
            "top_buyers": top_buyers,
            "period": period,
            "basis_note": "Based on available recorded sales history.",
            "key_insight": f"{repeat_purchase_rate}% of identified customers made more than one purchase during the analyzed period."
        }
    else:
        customer_section = {
            "available": False,
            "message": "Customer-level analysis requires customer handles or order identification in your uploaded spreadsheet."
        }


    # =========================================================================
    # SECTION G: BUSINESS TRENDS (Historical Patterns from Seller Data)
    # =========================================================================
    trends_list = []
    available_inv_count = db.query(InventoryItem).filter(InventoryItem.status == "Available").count()

    # For trend evaluation and historical evolution, always preserve multi-month perspective
    trend_eval_months = all_sales_by_month if len(sales_by_month) < 2 else sales_by_month

    # 1. Category trend over time
    if len(trend_eval_months) >= 2:
        first_m = trend_eval_months[0]["month"]
        latest_m = trend_eval_months[-1]["month"]

        first_m_sales = [
            s for s in all_sales if s.sale_date and s.sale_date.strftime("%B %Y") == first_m
        ]
        latest_m_sales = [
            s for s in all_sales if s.sale_date and s.sale_date.strftime("%B %Y") == latest_m
        ]

        first_cat_rev = Counter()
        latest_cat_rev = Counter()
        for s in first_m_sales:
            p = product_map.get(s.product_id)
            if p:
                first_cat_rev[p.category] += s.selling_price * s.quantity
        for s in latest_m_sales:
            p = product_map.get(s.product_id)
            if p:
                latest_cat_rev[p.category] += s.selling_price * s.quantity

        first_total = sum(first_cat_rev.values())
        latest_total = sum(latest_cat_rev.values())

        for cat, lat_rev in latest_cat_rev.most_common(3):
            fir_rev = first_cat_rev.get(cat, 0.0)
            lat_pct = _safe_pct(lat_rev, latest_total)
            fir_pct = _safe_pct(fir_rev, first_total)
            delta_pp = round(lat_pct - fir_pct, 1)
            if lat_pct > fir_pct + 4.0:
                trends_list.append({
                    "trend_type": "Category Trend",
                    "domain": "Category Share",
                    "statement": f"{cat} increased from {fir_pct:.1f}% of monthly sales in {first_m} to {lat_pct:.1f}% in {latest_m} (+{delta_pp} percentage points).",
                    "delta": f"+{delta_pp} pp share shift",
                    "direction": "up"
                })
                break

    # 2. Size trend over time
    if len(trend_eval_months) >= 2 and top_size:
        trends_list.append({
            "trend_type": "Size Trend",
            "domain": "Garment Sizing",
            "statement": f"Size {top_size['size']} purchases have maintained steady dominance, accounting for {top_size['pct_of_sales']}% of total units.",
            "delta": f"{top_size['pct_of_sales']}% of sales",
            "direction": "up"
        })

    # 3. Price trend
    if dominant_price_bracket["units"] > 0:
        trends_list.append({
            "trend_type": "Price Trend",
            "domain": "Price Range",
            "statement": f"Purchases in the {dominant_price_bracket['range']} bracket represent the primary price sweet spot ({dominant_price_bracket['pct_of_sales']}% of total revenue).",
            "delta": f"{dominant_price_bracket['pct_of_sales']}% revenue",
            "direction": "stable"
        })

    # 4. Sales momentum trend
    if len(trend_eval_months) >= 3:
        consecutive_growth = True
        for i in range(1, len(trend_eval_months)):
            if trend_eval_months[i]["revenue"] < trend_eval_months[i-1]["revenue"]:
                consecutive_growth = False
                break
        best_month = strongest_month or (max(trend_eval_months, key=lambda x: x["revenue"]) if trend_eval_months else None)
        if consecutive_growth:
            trends_list.append({
                "trend_type": "Sales Trend",
                "domain": "Monthly Momentum",
                "statement": f"Monthly revenue has increased consecutively across {len(trend_eval_months)} recorded months.",
                "delta": "Consecutive Growth",
                "direction": "up"
            })
        elif best_month:
            trends_list.append({
                "trend_type": "Sales Trend",
                "domain": "Monthly Momentum",
                "statement": f"Sales peaked in {best_month['month']} at {best_month['revenue_formatted']}.",
                "delta": f"Peak {best_month['month']}",
                "direction": "up"
            })

    # 5. Product/Volume trend (distinguishing units sold from inventory available)
    if top_cat:
        trends_list.append({
            "trend_type": "Volume Trend",
            "domain": "Inventory Movement",
            "statement": f"{top_cat['category']} accounted for the highest sales volume with {top_cat['units_sold']} units sold ({top_cat['pct_of_total']}% of sales, with {available_inv_count} available inventory pieces).",
            "delta": f"{top_cat['units_sold']} units sold",
            "direction": "up"
        })

    # Detailed monthly breakdowns for rich historical visualizations (always all months for complete timeline)
    monthly_category_trends = []
    monthly_size_trends = []
    monthly_price_trends = []
    monthly_volume_trends = []

    for m in (all_sales_by_month if all_sales_by_month else sales_by_month):
        m_name = m["month"]
        m_sales = [s for s in all_sales if s.sale_date and s.sale_date.strftime("%B %Y") == m_name]
        m_rev = sum(s.selling_price * s.quantity for s in m_sales)
        m_units = sum(s.quantity for s in m_sales)

        # Categories
        cat_counts = Counter()
        cat_revs = defaultdict(float)
        for s in m_sales:
            p = product_map.get(s.product_id)
            if p:
                cat_counts[p.category] += s.quantity
                cat_revs[p.category] += s.selling_price * s.quantity
        monthly_category_trends.append({
            "month": m_name,
            "total_revenue": m_rev,
            "total_units": m_units,
            "categories": [
                {
                    "category": c,
                    "revenue": cat_revs[c],
                    "revenue_formatted": _format_inr(cat_revs[c]),
                    "revenue_share": _safe_pct(cat_revs[c], m_rev),
                    "units": cat_counts[c],
                    "unit_share": _safe_pct(cat_counts[c], m_units)
                }
                for c in ["Outerwear", "Bottoms", "Tops", "Dresses"] if c in cat_revs or c in cat_counts
            ]
        })

        # Sizes
        size_counts = Counter()
        for s in m_sales:
            p = product_map.get(s.product_id)
            if p:
                size_counts[p.size] += s.quantity
        monthly_size_trends.append({
            "month": m_name,
            "total_units": m_units,
            "sizes": [
                {"size": sz, "units": size_counts[sz], "unit_share": _safe_pct(size_counts[sz], m_units)}
                for sz in ["XS", "S", "M", "L", "XL"] if sz in size_counts
            ]
        })

        # Price Brackets
        p_brk = defaultdict(lambda: {"units": 0, "revenue": 0.0})
        for s in m_sales:
            pr = s.selling_price
            if pr < 800:
                b_name = "Under ₹800"
            elif pr <= 1499:
                b_name = "₹800 – ₹1,499"
            else:
                b_name = "₹1,500+"
            p_brk[b_name]["units"] += s.quantity
            p_brk[b_name]["revenue"] += pr * s.quantity

        monthly_price_trends.append({
            "month": m_name,
            "total_revenue": m_rev,
            "brackets": [
                {
                    "bracket": b_name,
                    "revenue": p_brk[b_name]["revenue"],
                    "revenue_formatted": _format_inr(p_brk[b_name]["revenue"]),
                    "revenue_share": _safe_pct(p_brk[b_name]["revenue"], m_rev),
                    "units": p_brk[b_name]["units"],
                    "unit_share": _safe_pct(p_brk[b_name]["units"], m_units)
                }
                for b_name in ["Under ₹800", "₹800 – ₹1,499", "₹1,500+"]
            ]
        })

        # Volume
        monthly_volume_trends.append({
            "month": m_name,
            "units_sold": m_units,
            "by_category": [
                {"category": c, "units": cat_counts[c]}
                for c in ["Outerwear", "Bottoms", "Tops", "Dresses"] if c in cat_counts
            ]
        })

    trends_section = {
        "trends": trends_list,
        "sales_by_month": all_sales_by_month if len(sales_by_month) < 2 else sales_by_month,
        "strongest_month": strongest_month or (max(all_sales_by_month, key=lambda x: x["revenue"]) if all_sales_by_month else None),
        "monthly_category_trends": monthly_category_trends,
        "monthly_size_trends": monthly_size_trends,
        "monthly_price_trends": monthly_price_trends,
        "monthly_volume_trends": monthly_volume_trends,
        "available_inventory_count": available_inv_count,
        "note": "Trends are computed exclusively from your historical data comparisons."
    }

    # =========================================================================
    # SECTION H: ML PREDICTIONS & RECOMMENDATIONS
    # =========================================================================
    # Always train forecasting on the full verified historical series
    predictions_data = get_business_predictions(
        db,
        sales_by_month=all_sales_by_month,
        sales_by_price_range=sales_by_price_range,
        category_x_price=category_x_price
    )

    return {
        "has_data": True,
        "filters_applied": {
            "period": period,
            "category": category_filter or "All",
            "available_categories": available_categories
        },
        "data_quality": {
            "score": latest_quality.quality_score if latest_quality else 100.0,
            "total_records_analyzed": len(filtered_sales),
            "date_range": f"{min(sale_dates).strftime('%b %d, %Y')} – {ref_date.strftime('%b %d, %Y')}" if sale_dates else "N/A",
            "confidence": "High" if len(filtered_sales) > 20 else "Medium"
        },
        "sales": sales_section,
        "time": time_section,
        "products": products_section,
        "clothing": clothing_section,
        "customers": customer_section,
        "trends": trends_section,
        "predictions": predictions_data,
        "recommendations": predictions_data.get("recommendations", [])
    }
