"""
Tests for TrendPulse Apparel Domain Intelligence Engine.

Tests:
    - Size Normalizer & Size Curve Engine
    - Broken Size Run Detection
    - Colorway & Palette Intelligence
    - Apparel Taxonomy & Title Attribute Extraction
    - Apparel Data Enrichment & Audit Trails
    - Pipeline Integration & JSON Safety
"""

import json
import pandas as pd
import pytest

from data_engine.apparel import (
    normalize_size,
    extract_size_from_title,
    calculate_size_curves,
    detect_broken_size_runs,
    normalize_color,
    extract_color_from_title,
    analyze_colorways,
    extract_apparel_attributes,
    enrich_apparel_data,
    analyze_apparel_domain,
)
from data_engine.processor import process_dataframe


# ============================================================
# 1. Size Normalization & Size Curve Tests
# ============================================================

class TestSizeNormalizer:

    def test_alpha_size_normalization(self):
        cases = [
            ("s", "S", "alpha"),
            ("Small", "S", "alpha"),
            ("medium", "M", "alpha"),
            ("MED", "M", "alpha"),
            ("x-large", "XL", "alpha"),
            ("XXL", "2XL", "alpha"),
            ("2x-large", "2XL", "alpha"),
            ("3XL", "3XL", "alpha"),
            ("free size", "Free Size", "one_size"),
            ("OS", "Free Size", "one_size"),
        ]
        for raw, expected_std, expected_type in cases:
            res = normalize_size(raw)
            assert res["standard_size"] == expected_std
            assert res["size_type"] == expected_type

    def test_numeric_and_inseam_sizes(self):
        assert normalize_size("32")["standard_size"] == "32"
        assert normalize_size("32")["size_type"] == "numeric"
        assert normalize_size("32x30")["standard_size"] == "32x30"
        assert normalize_size("32/34")["standard_size"] == "32x34"

    def test_size_extraction_from_title(self):
        assert extract_size_from_title("Vintage Oversized Graphic Tee - Black / XL") == "XL"
        assert extract_size_from_title("Slim Denim Jeans (Size: 32x30)") == "32x30"
        assert extract_size_from_title("Plain Canvas Tote Bag - Free Size") == "Free Size"

    def test_size_curves_and_broken_runs(self):
        df = pd.DataFrame([
            {"product": "Oversized Tee", "size": "XS", "quantity": 10},
            {"product": "Oversized Tee", "size": "S", "quantity": 2},
            {"product": "Oversized Tee", "size": "2XL", "quantity": 15},
            # Notice M and L are missing completely!
        ])
        curves = calculate_size_curves(df)
        assert curves["status"] == "success"
        assert len(curves["overall_size_curve"]) == 3

        broken = detect_broken_size_runs(df)
        assert len(broken) == 1
        assert broken[0]["product"] == "Oversized Tee"
        assert "M" in broken[0]["missing_core_sizes"]
        assert "L" in broken[0]["missing_core_sizes"]


# ============================================================
# 2. Colorway & Palette Tests
# ============================================================

class TestColorEngine:

    def test_color_normalization_and_families(self):
        assert normalize_color("charcoal")["color_family"] == "Monochrome"
        assert normalize_color("vintage black")["base_color"] == "Black"
        assert normalize_color("sage green")["color_family"] == "Earthy"
        assert normalize_color("dusty rose")["color_family"] == "Pastels"
        assert normalize_color("navy blue")["color_family"] == "Jewel Tones"
        assert normalize_color("neon pink")["color_family"] == "Vibrant"

    def test_color_extraction_from_title(self):
        c_info = extract_color_from_title("Men's Acid Wash Tee - Charcoal / L")
        assert c_info is not None
        assert c_info["standard_color"] == "Charcoal"
        assert c_info["color_family"] == "Monochrome"

    def test_colorways_analysis(self):
        df = pd.DataFrame([
            {"product": "Tee", "color": "Charcoal", "quantity": 10, "price": 500},
            {"product": "Tee", "color": "Sage Green", "quantity": 5, "price": 500},
            {"product": "Hoodie", "color": "Navy Blue", "quantity": 8, "price": 1000},
        ])
        res = analyze_colorways(df)
        assert res["status"] == "success"
        assert len(res["top_colorways"]) == 3
        assert len(res["color_family_distribution"]) == 3


# ============================================================
# 3. Apparel Taxonomy & Attribute Extraction Tests
# ============================================================

class TestApparelTaxonomy:

    def test_rich_title_attribute_extraction(self):
        title = "Women's Acid Wash Oversized Graphic French Terry Hoodie - Vintage Black / L"
        attr = extract_apparel_attributes(title)

        assert attr["gender"] == "Women"
        assert attr["category"] == "Tops"
        assert attr["subcategory"] == "Hoodies"
        assert attr["fit"] == "Oversized / Baggy"
        assert attr["fabric"] == "French Terry"
        assert attr["pattern"] in ("Vintage Washed", "Graphic Print")

    def test_bottoms_and_denim_extraction(self):
        title = "Men's Relaxed Fit Carpenter Denim Jeans - Indigo / 34"
        attr = extract_apparel_attributes(title)

        assert attr["gender"] == "Men"
        assert attr["category"] == "Bottoms"
        assert attr["subcategory"] == "Jeans & Denim"
        assert attr["fit"] == "Relaxed Fit"
        assert attr["fabric"] == "Denim"


# ============================================================
# 4. Apparel Data Enrichment Tests
# ============================================================

class TestApparelCleaner:

    def test_dataframe_enrichment(self):
        df = pd.DataFrame([
            {
                "product": "Men's Heavyweight Oversized Graphic Tee - Vintage Black / XL",
                "quantity": 5,
                "price": 799,
            },
            {
                "product": "Women's Slim Fit Linen Trousers - Sage Green / 28",
                "quantity": 3,
                "price": 1499,
            },
        ])
        enriched_df, audit, summary = enrich_apparel_data(df)

        assert "std_size" in enriched_df.columns
        assert "std_color" in enriched_df.columns
        assert "fit_type" in enriched_df.columns
        assert "fabric_type" in enriched_df.columns
        assert "gender" in enriched_df.columns

        # Row 1 check
        assert enriched_df.loc[0, "std_size"] == "XL"
        assert enriched_df.loc[0, "std_color"] in ("Black", "Vintage Black")
        assert enriched_df.loc[0, "gender"] == "Men"
        assert enriched_df.loc[0, "fit_type"] == "Oversized / Baggy"

        # Row 2 check
        assert enriched_df.loc[1, "std_size"] == "28"
        assert enriched_df.loc[1, "std_color"] == "Sage Green"
        assert enriched_df.loc[1, "gender"] == "Women"
        assert enriched_df.loc[1, "fabric_type"] == "Linen"

        assert summary["enriched_rows"] == 2
        assert len(audit) > 0


# ============================================================
# 5. Processor Pipeline Integration & JSON Safety
# ============================================================

class TestPipelineApparelIntegration:

    def test_full_pipeline_apparel_intelligence(self):
        df = pd.DataFrame([
            {"date": "2026-08-01", "product": "Oversized Boxy Tee - Jet Black / M", "quantity": 10, "price": 699, "customer_id": "C01"},
            {"date": "2026-08-02", "product": "Oversized Boxy Tee - Jet Black / L", "quantity": 8, "price": 699, "customer_id": "C02"},
            {"date": "2026-08-03", "product": "Relaxed Cargo Pants - Khaki / 32", "quantity": 5, "price": 1299, "customer_id": "C03"},
            {"date": "2026-08-04", "product": "Cropped Fleece Hoodie - Baby Pink / S", "quantity": 6, "price": 999, "customer_id": "C04"},
        ])

        result = process_dataframe(df, enable_llm=False)

        assert "apparel_intelligence" in result
        assert "apparel_enrichment_summary" in result
        assert "apparel_audit" in result

        intel = result["apparel_intelligence"]
        assert intel["status"] == "success"
        assert "size_intelligence" in intel
        assert "color_intelligence" in intel
        assert len(intel["fit_intelligence"]) > 0
        assert len(intel["fabric_intelligence"]) > 0
        assert len(intel["gender_distribution"]) > 0

        # Verify JSON serialization safety
        json.dumps(result["apparel_intelligence"])
        json.dumps(result["apparel_enrichment_summary"])
        json.dumps(result["apparel_audit"])
