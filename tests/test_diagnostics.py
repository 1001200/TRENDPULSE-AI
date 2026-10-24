"""
Tests for TrendPulse Phase 3 Diagnostic Intelligence.

Tests:
    - Price-Volume-Mix (PVM) revenue variance decomposition
    - Mathematical invariant verification: Volume Effect + Price Effect + Mix Effect = Total Delta
    - Performance driver attribution & Pareto concentration
    - Anomaly root-cause contextualization & forecasting guidance
    - Processor pipeline integration & JSON safety
"""

import json
import pandas as pd
import pytest

from data_engine.analytics import (
    decompose_revenue,
    analyze_performance_drivers,
    diagnose_anomalies,
)
from data_engine.processor import process_dataframe


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def multi_period_clothing_df():
    """Generates a multi-month clothing dataset with price changes, volume shifts, and product mix variations."""
    records = []
    
    # Month 1 (Base): 2026-06
    # 10 Tees @ 500 = 5000, 5 Jeans @ 1000 = 5000 -> Total = 10,000, Qty = 15, ASP = 666.67
    records.extend([
        {"date": "2026-06-05", "product": "Basic Tee", "category": "T-Shirt", "quantity": 10, "price": 500, "customer_id": "C001", "order_id": "ORD01"},
        {"date": "2026-06-15", "product": "Slim Jeans", "category": "Jeans", "quantity": 5, "price": 1000, "customer_id": "C002", "order_id": "ORD02"},
    ])
    
    # Month 2 (Current): 2026-07
    # 20 Tees @ 600 (Price up by 100, Vol up by 10) = 12,000
    # 2 Jeans @ 1000 (Vol down by 3) = 2,000
    # 5 Silk Shirts @ 2000 (New higher tier product - Mix shift) = 10,000
    # Total = 24,000, Qty = 27
    records.extend([
        {"date": "2026-07-05", "product": "Basic Tee", "category": "T-Shirt", "quantity": 20, "price": 600, "customer_id": "C001", "order_id": "ORD03"},
        {"date": "2026-07-10", "product": "Slim Jeans", "category": "Jeans", "quantity": 2, "price": 1000, "customer_id": "C002", "order_id": "ORD04"},
        {"date": "2026-07-20", "product": "Silk Shirt", "category": "Shirts", "quantity": 5, "price": 2000, "customer_id": "C003", "order_id": "ORD05"},
    ])

    return pd.DataFrame(records)


@pytest.fixture
def anomalous_clothing_df():
    """Generates a dataset with intentional wholesale spikes and pricing outliers."""
    records = []
    # Normal baseline orders
    for i in range(1, 20):
        records.append({
            "date": f"2026-08-{i:02d}",
            "product": "Oversized Tee",
            "category": "T-Shirt",
            "quantity": 2 if i % 2 == 0 else 3,
            "price": 699 if i % 2 == 0 else 749,
            "customer_id": f"C{i:03d}",
            "order_id": f"O{i:03d}",
        })
    # Anomaly 1: Wholesale bulk spike from a single customer
    records.append({
        "date": "2026-08-25",
        "product": "Oversized Tee",
        "category": "T-Shirt",
        "quantity": 200,
        "price": 699,
        "customer_id": "WHOLESALE_01",
        "order_id": "O_BULK_01",
    })
    # Anomaly 2: Price distortion / typo
    records.append({
        "date": "2026-08-26",
        "product": "Oversized Tee",
        "category": "T-Shirt",
        "quantity": 1,
        "price": 69900,  # 100x typo
        "customer_id": "C050",
        "order_id": "O_TYPO_01",
    })

    return pd.DataFrame(records)


# ============================================================
# 1. Revenue Decomposition Tests
# ============================================================

class TestRevenueDecomposition:

    def test_empty_dataframe(self):
        res = decompose_revenue(pd.DataFrame())
        assert res["status"] == "insufficient_data"

    def test_mathematical_sum_invariant(self, multi_period_clothing_df):
        """Volume Effect + Price Effect + Mix Effect must equal Total Revenue Delta."""
        res = decompose_revenue(multi_period_clothing_df)
        assert res["status"] == "success"

        total_delta = res["summary"]["total_revenue_delta"]
        vol = res["decomposition"]["volume_effect"]["impact"]
        pri = res["decomposition"]["price_effect"]["impact"]
        mix = res["decomposition"]["mix_effect"]["impact"]

        # 24,000 - 10,000 = 14,000 delta
        assert total_delta == 14000.0
        # Sum of components must equal total delta within rounding precision
        calculated_sum = vol + pri + mix
        assert abs(calculated_sum - total_delta) < 0.05

    def test_primary_driver_and_diagnostic_explanation(self, multi_period_clothing_df):
        res = decompose_revenue(multi_period_clothing_df)
        assert res["primary_driver"] in ("Volume Effect", "Price Effect", "Mix Effect")
        assert len(res["diagnostic_explanation"]) > 20
        assert "Revenue" in res["diagnostic_explanation"]

    def test_product_details_included(self, multi_period_clothing_df):
        res = decompose_revenue(multi_period_clothing_df)
        prods = res["product_details"]
        assert len(prods) == 3
        # Basic Tee revenue grew from 5000 to 12000
        tee = next(p for p in prods if p["product"] == "Basic Tee")
        assert tee["revenue_delta"] == 7000.0


# ============================================================
# 2. Performance Driver Attribution Tests
# ============================================================

class TestPerformanceDrivers:

    def test_empty_dataframe(self):
        res = analyze_performance_drivers(pd.DataFrame())
        assert res["status"] == "no_data"

    def test_pareto_concentration_and_drivers(self, multi_period_clothing_df):
        res = analyze_performance_drivers(multi_period_clothing_df)
        assert res["status"] == "success"
        assert res["total_revenue"] == 34000.0  # 10k + 24k

        pareto = res["pareto_summary"]
        assert pareto["total_products"] == 3
        assert pareto["top_product"] in ("Basic Tee", "Silk Shirt")

        # Growth contributors and revenue drags
        assert len(res["growth_contributors"]) > 0
        top_growth = res["growth_contributors"][0]
        assert top_growth["revenue_change"] > 0
        assert top_growth["product"] in ("Basic Tee", "Silk Shirt")

        # Category attribution
        cats = res["category_attribution"]
        assert len(cats) >= 2
        total_share = sum(c["revenue_share_percentage"] for c in cats)
        assert abs(total_share - 100.0) < 0.5


# ============================================================
# 3. Anomaly Root-Cause Diagnostic Tests
# ============================================================

class TestAnomalyDiagnostics:

    def test_no_anomalies_detected(self, multi_period_clothing_df):
        res = diagnose_anomalies(multi_period_clothing_df, anomalies=[])
        assert res["status"] == "no_anomalies"
        assert "clean" in res["forecasting_guidance"]

    def test_wholesale_bulk_order_and_price_distortion_diagnosis(self, anomalous_clothing_df):
        # Trigger anomaly detection through full pipeline
        proc_res = process_dataframe(anomalous_clothing_df, enable_llm=False)
        anom_diag = proc_res["anomaly_diagnostics"]

        assert anom_diag["status"] == "success"
        assert anom_diag["total_anomalous_records"] >= 2
        assert anom_diag["anomalous_revenue_share_percentage"] > 0

        causes = anom_diag["primary_root_causes"]
        assert causes.get("wholesale_bulk_order", 0) > 0 or causes.get("volume_spike", 0) > 0
        assert causes.get("price_distortion", 0) > 0 or causes.get("isolated_high_value_transaction", 0) > 0

        # Check forecasting guidance is actionable
        assert len(anom_diag["forecasting_guidance"]) > 10


# ============================================================
# 4. Processor Pipeline Integration & JSON Safety
# ============================================================

class TestProcessorDiagnosticsIntegration:

    def test_pipeline_includes_all_diagnostic_layers(self, multi_period_clothing_df):
        result = process_dataframe(multi_period_clothing_df, enable_llm=False)
        assert "revenue_decomposition" in result
        assert "performance_drivers" in result
        assert "anomaly_diagnostics" in result

        assert result["revenue_decomposition"]["status"] == "success"
        assert result["performance_drivers"]["status"] == "success"

    def test_json_safe_serialization(self, multi_period_clothing_df):
        result = process_dataframe(multi_period_clothing_df, enable_llm=False)
        json.dumps(result["revenue_decomposition"])
        json.dumps(result["performance_drivers"])
        json.dumps(result["anomaly_diagnostics"])
