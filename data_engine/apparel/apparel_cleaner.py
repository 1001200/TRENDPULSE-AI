"""
TrendPulse Apparel Data Enrichment & Cleaning Engine.

Takes raw/mapped clothing data and enriches it with standardized, auditable
apparel-domain features:
    - Standard Size & Size Type
    - Standard Color & Color Family
    - Gender / Department Classification
    - Macro Category & Micro Subcategory
    - Fit & Silhouette
    - Fabric & Material
    - Pattern & Surface Treatment

Design rules:
    - Deterministic; zero side-effects on input DataFrame (uses deep copies).
    - Maintains an auditable enrichment log.
    - JSON-safe return structure.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple
import pandas as pd

from data_engine.apparel.size_normalizer import normalize_size, extract_size_from_title
from data_engine.apparel.color_engine import normalize_color, extract_color_from_title
from data_engine.apparel.taxonomy import extract_apparel_attributes
from data_engine.utils import clean_number, safe_int


def enrich_apparel_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]], Dict[str, Any]]:
    """
    Enrich DataFrame with structured fashion attributes and generate an audit trail.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("enrich_apparel_data expects a pandas DataFrame.")

    if df.empty:
        return df.copy(), [], {"enriched_rows": 0, "attributes_extracted": 0}

    data = df.copy(deep=True)
    audit_trail: List[Dict[str, Any]] = []

    has_product = "product" in data.columns
    has_size = "size" in data.columns
    has_color = "color" in data.columns
    has_category = "category" in data.columns

    std_sizes = []
    size_types = []
    std_colors = []
    color_families = []
    genders = []
    apparel_cats = []
    apparel_subcats = []
    fits = []
    fabrics = []
    patterns = []

    for idx, row in data.iterrows():
        prod_title = str(row["product"]) if has_product and pd.notna(row["product"]) else ""
        existing_cat = str(row["category"]) if has_category and pd.notna(row["category"]) else None

        # 1. Size Extraction & Normalization
        raw_size = row.get("size") if has_size else None
        if pd.notna(raw_size) and str(raw_size).strip():
            s_info = normalize_size(raw_size)
            std_s = s_info["standard_size"]
            s_type = s_info["size_type"]
        elif has_product and prod_title:
            extracted_s = extract_size_from_title(prod_title)
            if extracted_s:
                std_s = extracted_s
                s_type = normalize_size(extracted_s)["size_type"]
                audit_trail.append({
                    "row": safe_int(idx),
                    "attribute": "size",
                    "action": "extracted_from_title",
                    "original": prod_title,
                    "inferred_value": std_s,
                })
            else:
                std_s = "Unknown"
                s_type = "unknown"
        else:
            std_s = "Unknown"
            s_type = "unknown"

        # 2. Color Extraction & Normalization
        raw_color = row.get("color") if has_color else None
        if pd.notna(raw_color) and str(raw_color).strip():
            c_info = normalize_color(raw_color)
            std_c = c_info["standard_color"]
            c_fam = c_info["color_family"]
        elif has_product and prod_title:
            c_info = extract_color_from_title(prod_title)
            if c_info:
                std_c = c_info["standard_color"]
                c_fam = c_info["color_family"]
                audit_trail.append({
                    "row": safe_int(idx),
                    "attribute": "color",
                    "action": "extracted_from_title",
                    "original": prod_title,
                    "inferred_value": std_c,
                })
            else:
                std_c = "Unknown"
                c_fam = "Unknown"
        else:
            std_c = "Unknown"
            c_fam = "Unknown"

        # 3. Taxonomy Extraction (Gender, Category, Subcat, Fit, Fabric, Pattern)
        tax_info = extract_apparel_attributes(prod_title, existing_category=existing_cat)

        std_sizes.append(std_s)
        size_types.append(s_type)
        std_colors.append(std_c)
        color_families.append(c_fam)
        genders.append(tax_info["gender"])
        apparel_cats.append(tax_info["category"])
        apparel_subcats.append(tax_info["subcategory"])
        fits.append(tax_info["fit"])
        fabrics.append(tax_info["fabric"])
        patterns.append(tax_info["pattern"])

    # Add enriched columns
    data["std_size"] = std_sizes
    data["size_type"] = size_types
    data["std_color"] = std_colors
    data["color_family"] = color_families
    data["gender"] = genders
    data["apparel_category"] = apparel_cats
    data["apparel_subcategory"] = apparel_subcats
    data["fit_type"] = fits
    data["fabric_type"] = fabrics
    data["pattern_type"] = patterns

    summary = {
        "enriched_rows": len(data),
        "attributes_extracted_count": len(audit_trail),
        "sizes_identified_count": int((data["std_size"] != "Unknown").sum()),
        "colors_identified_count": int((data["std_color"] != "Unknown").sum()),
        "categories_classified_count": int((data["apparel_category"] != "Uncategorized").sum()),
    }

    return data, audit_trail, summary


__all__ = ["enrich_apparel_data"]
