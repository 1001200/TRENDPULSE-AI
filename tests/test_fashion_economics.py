"""
Unit & Integration Tests for Fashion Unit Economics, Inventory Health, and Multi-Table Ingestion.
"""

import pandas as pd
import pytest

from data_engine.economics.margins import analyze_unit_economics
from data_engine.economics.inventory_health import analyze_inventory_health
from data_engine.multi_table import merge_retail_datasets


@pytest.fixture
def economics_dataframe():
    return pd.DataFrame({
        "date": ["2026-07-01", "2026-07-05", "2026-07-10", "2026-07-15"],
        "product": [
            "Oversized Heavyweight Tee - Black / M",
            "Relaxed Carpenter Jeans - Indigo / 32",
            "Vintage Washed Hoodie - Grey / L",
            "Slow Moving Deadstock Cap - Navy / Free Size",
        ],
        "quantity": [30, 25, 5, 1],
        "price": [799, 1499, 1299, 499],
        "cost_price": [280, 550, 450, 350],
        "stock": [5, 40, 10, 80],
        "discount": [0, 10, 0, 30],
        "category": ["Tops", "Bottoms", "Tops", "Accessories"],
    })


def test_unit_economics_margins_and_discount_drag(economics_dataframe):
    res = analyze_unit_economics(economics_dataframe)
    assert res["status"] == "success"

    metrics = res["overall_metrics"]
    assert metrics["total_revenue"] > 0
    assert metrics["total_gross_profit"] > 0
    assert metrics["gross_margin_percentage"] > 50.0
    assert metrics["total_discount_bleed"] > 0

    quadrants = res["profitability_quadrants"]
    assert "star_performers" in quadrants
    assert "cash_cows" in quadrants
    assert "hidden_gems" in quadrants
    assert "value_destroyers" in quadrants


def test_inventory_health_wos_and_stockout_alerts(economics_dataframe):
    res = analyze_inventory_health(economics_dataframe)
    assert res["status"] == "success"
    assert res["overall_sell_through_rate"] > 0
    assert "stockout_risk_alerts" in res

    # Tee has 30 units sold and only 5 in stock -> critical stockout risk!
    alerts = res["stockout_risk_alerts"]
    assert len(alerts) > 0
    assert any("Tee" in a["sku"] for a in alerts)
    assert alerts[0]["weeks_of_supply"] < 2.0


def test_multi_table_auto_joiner():
    sales_df = pd.DataFrame({
        "Order ID": ["ORD_01", "ORD_02", "ORD_03"],
        "SKU": ["SKU_TEE_BLK_M", "SKU_JEAN_IND_32", "SKU_HOOD_GRY_L"],
        "Units": [2, 1, 1],
        "Selling Price": [799, 1499, 1299],
    })

    inv_df = pd.DataFrame({
        "SKU": ["SKU_TEE_BLK_M", "SKU_JEAN_IND_32", "SKU_HOOD_GRY_L"],
        "Cost Price": [280, 550, 450],
        "Stock on Hand": [50, 20, 15],
        "Lead Time Days": [7, 14, 10],
    })

    returns_df = pd.DataFrame({
        "Order ID": ["ORD_02"],
        "Return Reason": ["Size runs small"],
    })

    merged_df, audit = merge_retail_datasets(sales_df, inv_df, returns_df)

    assert len(merged_df) == 3
    assert "Cost Price" in merged_df.columns
    assert "Stock on Hand" in merged_df.columns
    assert "_is_returned" in merged_df.columns
    assert merged_df.loc[merged_df["Order ID"] == "ORD_02", "_is_returned"].values[0] is True
    assert merged_df.loc[merged_df["Order ID"] == "ORD_01", "_is_returned"].values[0] is False
    assert "inventory" in audit["merged_tables"]
    assert "returns" in audit["merged_tables"]
