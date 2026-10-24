"""
Tests for TrendPulse Phase 2 Descriptive Analytics.

Tests:
    - Period-over-period comparison (WoW, MoM, Split halves)
    - Customer analytics (Repeat rates, RFM segments, top customers)
    - Product affinity & market basket analytics (Support, Confidence, Lift)
    - Time-series aggregation (Weekly, Monthly, Quarterly, Day-of-Week)
    - Processor pipeline integration & JSON safety
"""

import json
import pandas as pd
import pytest

from data_engine.analytics import (
    analyze_period_over_period,
    analyze_customers,
    analyze_product_affinity,
    aggregate_time_series,
)
from data_engine.processor import process_dataframe


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def multi_period_clothing_df():
    """Generates a realistic 3-month dataset with repeat customers and multi-item orders."""
    records = []
    
    # Month 1: 2026-06
    records.extend([
        {"date": "2026-06-05", "product": "Black Tee", "category": "T-Shirt", "quantity": 10, "price": 699, "customer_id": "C001", "order_id": "ORD01"},
        {"date": "2026-06-05", "product": "Blue Jeans", "category": "Jeans", "quantity": 5, "price": 1299, "customer_id": "C001", "order_id": "ORD01"},
        {"date": "2026-06-12", "product": "White Hoodie", "category": "Hoodie", "quantity": 8, "price": 999, "customer_id": "C002", "order_id": "ORD02"},
        {"date": "2026-06-20", "product": "Black Tee", "category": "T-Shirt", "quantity": 12, "price": 699, "customer_id": "C003", "order_id": "ORD03"},
    ])
    
    # Month 2: 2026-07 (Higher volume)
    records.extend([
        {"date": "2026-07-02", "product": "Black Tee", "category": "T-Shirt", "quantity": 15, "price": 699, "customer_id": "C001", "order_id": "ORD04"},
        {"date": "2026-07-02", "product": "White Hoodie", "category": "Hoodie", "quantity": 10, "price": 999, "customer_id": "C001", "order_id": "ORD04"},
        {"date": "2026-07-15", "product": "Blue Jeans", "category": "Jeans", "quantity": 7, "price": 1299, "customer_id": "C002", "order_id": "ORD05"},
        {"date": "2026-07-25", "product": "Cargo Pants", "category": "Pants", "quantity": 6, "price": 1499, "customer_id": "C004", "order_id": "ORD06"},
    ])
    
    # Month 3: 2026-08
    records.extend([
        {"date": "2026-08-05", "product": "Black Tee", "category": "T-Shirt", "quantity": 20, "price": 699, "customer_id": "C001", "order_id": "ORD07"},
        {"date": "2026-08-05", "product": "Blue Jeans", "category": "Jeans", "quantity": 10, "price": 1299, "customer_id": "C001", "order_id": "ORD07"},
        {"date": "2026-08-10", "product": "White Hoodie", "category": "Hoodie", "quantity": 12, "price": 999, "customer_id": "C005", "order_id": "ORD08"},
        {"date": "2026-08-20", "product": "Cargo Pants", "category": "Pants", "quantity": 8, "price": 1499, "customer_id": "C003", "order_id": "ORD09"},
    ])

    return pd.DataFrame(records)


# ============================================================
# 1. Period Comparison Tests
# ============================================================

class TestPeriodComparison:

    def test_empty_dataframe(self):
        res = analyze_period_over_period(pd.DataFrame())
        assert res["status"] == "insufficient_data"
        assert res["month_over_month"] is None

    def test_single_date(self):
        df = pd.DataFrame([{"date": "2026-08-01", "quantity": 5, "price": 100}])
        res = analyze_period_over_period(df)
        assert res["status"] == "insufficient_data"

    def test_month_over_month_metrics(self, multi_period_clothing_df):
        res = analyze_period_over_period(multi_period_clothing_df)
        assert res["status"] == "success"
        mom = res["month_over_month"]
        assert mom is not None
        assert "revenue" in mom["metrics"]
        assert "quantity" in mom["metrics"]
        assert "orders" in mom["metrics"]
        assert mom["metrics"]["revenue"]["current"] is not None
        assert mom["metrics"]["revenue"]["previous"] is not None
        assert mom["metrics"]["revenue"]["direction"] in ("increasing", "decreasing", "flat")

    def test_week_over_week_metrics(self, multi_period_clothing_df):
        res = analyze_period_over_period(multi_period_clothing_df)
        wow = res["week_over_week"]
        assert wow is not None
        assert wow["period_type"] == "week_over_week"

    def test_split_comparison_present(self, multi_period_clothing_df):
        res = analyze_period_over_period(multi_period_clothing_df)
        split = res["period_split"]
        assert split is not None
        assert "metrics" in split


# ============================================================
# 2. Customer Analytics Tests
# ============================================================

class TestCustomerAnalytics:

    def test_empty_dataframe(self):
        res = analyze_customers(pd.DataFrame())
        assert res["status"] == "no_data"

    def test_missing_customer_column(self):
        df = pd.DataFrame([{"product": "Tee", "price": 500}])
        res = analyze_customers(df)
        assert res["status"] == "column_missing"

    def test_customer_repeat_rate_and_rfm(self, multi_period_clothing_df):
        res = analyze_customers(multi_period_clothing_df)
        assert res["status"] == "success"
        overview = res["overview"]
        assert overview["total_customers"] == 5
        # C001 (4 orders), C002 (2 orders), C003 (2 orders) -> 3 repeat customers
        assert overview["repeat_customers"] == 3
        assert overview["single_purchase_customers"] == 2
        assert overview["repeat_customer_rate"] == 60.0
        assert overview["average_revenue_per_customer"] > 0

        # RFM Segments
        assert len(res["segments"]) > 0
        top_custs = res["top_customers_by_revenue"]
        assert len(top_custs) > 0
        assert top_custs[0]["customer_id"] == "C001"  # C001 has highest spend


# ============================================================
# 3. Product Affinity Tests
# ============================================================

class TestProductAffinity:

    def test_empty_dataframe(self):
        res = analyze_product_affinity(pd.DataFrame())
        assert res["status"] == "no_data"

    def test_missing_basket_identifier(self):
        df = pd.DataFrame([{"product": "Tee"}, {"product": "Jeans"}])
        res = analyze_product_affinity(df)
        assert res["status"] == "no_basket_identifier"

    def test_single_item_baskets_only(self):
        df = pd.DataFrame([
            {"order_id": "O1", "product": "Tee"},
            {"order_id": "O2", "product": "Jeans"},
        ])
        res = analyze_product_affinity(df)
        assert res["status"] == "single_item_baskets_only"

    def test_product_affinity_cooccurrence_and_lift(self, multi_period_clothing_df):
        res = analyze_product_affinity(multi_period_clothing_df)
        assert res["status"] == "success"
        assert res["multi_item_baskets"] > 0
        top_pairs = res["top_product_pairs"]
        assert len(top_pairs) > 0

        # Black Tee + Blue Jeans co-occur in ORD01 and ORD07
        pair = top_pairs[0]
        assert "product_a" in pair
        assert "product_b" in pair
        assert pair["co_occurrence_count"] >= 1
        assert pair["lift"] is not None
        assert "bundle_recommendation" in pair

        # Cross category affinity
        assert len(res["category_affinity"]) > 0


# ============================================================
# 4. Time Aggregation Tests
# ============================================================

class TestTimeAggregation:

    def test_empty_dataframe(self):
        res = aggregate_time_series(pd.DataFrame())
        assert res["status"] == "no_data"

    def test_multi_period_aggregation(self, multi_period_clothing_df):
        res = aggregate_time_series(multi_period_clothing_df)
        assert res["status"] == "success"
        assert len(res["monthly"]) == 3
        assert len(res["weekly"]) >= 3
        assert len(res["day_of_week_distribution"]) == 7
        assert res["peak_shopping_day"] is not None

        # Check fields in month record
        m1 = res["monthly"][0]
        assert "period" in m1
        assert "total_revenue" in m1
        assert "top_product" in m1
        assert "top_category" in m1


# ============================================================
# 5. Processor Pipeline Integration & JSON Safety
# ============================================================

class TestProcessorAnalyticsIntegration:

    def test_pipeline_includes_all_analytics(self, multi_period_clothing_df):
        result = process_dataframe(multi_period_clothing_df, enable_llm=False)
        assert "period_comparison" in result
        assert "customer_analytics" in result
        assert "product_affinity" in result
        assert "time_aggregation" in result

        assert result["period_comparison"]["status"] == "success"
        assert result["customer_analytics"]["status"] == "success"
        assert result["product_affinity"]["status"] == "success"
        assert result["time_aggregation"]["status"] == "success"

    def test_json_safe_serialization(self, multi_period_clothing_df):
        result = process_dataframe(multi_period_clothing_df, enable_llm=False)
        # Processed data is a dataframe for python callers, but the analytics blocks must be directly json serializable
        json.dumps(result["period_comparison"])
        json.dumps(result["customer_analytics"])
        json.dumps(result["product_affinity"])
        json.dumps(result["time_aggregation"])
