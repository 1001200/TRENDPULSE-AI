"""
Unit & Integration Tests for TrendPulse Social Curation & Viral Aesthetic Intelligence.
"""

import pandas as pd
import pytest

from data_engine.social_curation.aesthetics import classify_aesthetic, analyze_aesthetic_velocity
from data_engine.social_curation.drop_velocity import analyze_drop_velocity
from data_engine.social_curation.thrift_sourcing import generate_sourcing_recommendations
from data_engine.social_curation.social_attribution import analyze_social_attribution


@pytest.fixture
def social_sales_dataframe():
    return pd.DataFrame({
        "date": [
            "2026-07-05", "2026-07-05", "2026-07-06",
            "2026-08-01", "2026-08-01", "2026-08-03",
        ],
        "product": [
            "Y2K Cyber Rhinestone Baby Tee - Silver / S",
            "90s Vintage Acid Washed Baggy Carpenter Jeans - Indigo / 32",
            "Gorpcore Utility Cargo Pants with Drawstring - Khaki / M",
            "Old Money Cable Knit Linen Polo - Cream / L",
            "Heavyweight 280 GSM Boxy Streetwear Tee - Vintage Black / XL",
            "Vintage Blokecore Striped Football Jersey - Emerald / L",
        ],
        "quantity": [10, 8, 6, 12, 15, 5],
        "price": [899, 1499, 1299, 1799, 799, 1199],
        "category": ["Tops", "Bottoms", "Bottoms", "Tops", "Tops", "Tops"],
        "cost_price": [350, 600, 500, 700, 300, 450],
        "channel": ["Instagram Reels", "Instagram Reels", "TikTok", "Instagram Bio", "WhatsApp VIP", "Direct"],
    })


def test_classify_aesthetic_rules():
    assert classify_aesthetic("Y2K Rhinestone Cyber Baby Tee")["aesthetic"] == "Y2K / 2000s Retro"
    assert classify_aesthetic("90s Acid Wash Distressed Grunge Denim")["aesthetic"] == "90s Vintage Grunge"
    assert classify_aesthetic("Tactical Nylon Gorpcore Utility Vest")["aesthetic"] == "Gorpcore / Utility Techwear"
    assert classify_aesthetic("Old Money Cable Knit Linen Trousers")["aesthetic"] == "Old Money / Quiet Luxury"
    assert classify_aesthetic("Archive Heavyweight 280 GSM Boxy Drop Shoulder Tee")["aesthetic"] == "Archive / Heavyweight Streetwear"
    assert classify_aesthetic("Vintage Soccer Football Jersey Tracksuit")["aesthetic"] == "Blokecore / Vintage Sportswear"
    assert classify_aesthetic("Solid Black Essential Plain Tee")["aesthetic"] == "Clean Fit / Minimalist"


def test_analyze_aesthetic_velocity(social_sales_dataframe):
    res = analyze_aesthetic_velocity(social_sales_dataframe)
    assert res["status"] == "success"
    assert res["total_revenue_analyzed"] > 0
    assert len(res["top_aesthetics_by_revenue"]) >= 5

    # Check top aesthetic has clean revenue metrics
    top = res["top_aesthetics_by_revenue"][0]
    assert "aesthetic" in top
    assert "revenue_share_percentage" in top
    assert "average_selling_price" in top


def test_analyze_drop_velocity(social_sales_dataframe):
    res = analyze_drop_velocity(social_sales_dataframe)
    assert res["status"] == "success"
    assert res["total_drops_detected"] == 2  # July and August drops

    drop_1 = res["drops"][0]
    assert "drop_name" in drop_1
    assert "flash_sellout_score" in drop_1
    assert "clearance_grade" in drop_1
    assert drop_1["day_1_clearance_percentage"] >= 0


def test_generate_sourcing_recommendations(social_sales_dataframe):
    res = generate_sourcing_recommendations(social_sales_dataframe)
    assert res["status"] == "success"
    assert res["top_aesthetic_to_hunt"] is not None
    assert res["top_size_to_hunt"] is not None
    assert len(res["sourcing_checklist"]) > 0

    # Lot sourcing ROI
    roi = res["lot_sourcing_roi"]
    assert "sourcing_roi_multiple" in roi
    assert "total_sourcing_cost" in roi
    assert "gross_profit" in roi


def test_analyze_social_attribution(social_sales_dataframe):
    res = analyze_social_attribution(social_sales_dataframe)
    assert res["status"] == "success"
    assert res["top_converting_channel"] is not None
    assert len(res["channels"]) >= 4

    ig = next((c for c in res["channels"] if "Instagram" in c["channel"]), None)
    assert ig is not None
    assert ig["revenue"] > 0
    assert ig["average_order_value"] > 0
