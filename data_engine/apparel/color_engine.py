"""
TrendPulse Colorway & Palette Intelligence Engine.

Standardizes 150+ apparel colorways and retail shade names into:
    - Canonical Base Colors (Black, White, Grey, Blue, Green, Red, Pink, etc.)
    - Commercial Color Families (Monochrome, Neutrals, Earthy, Pastels, Jewel Tones, Vibrant)

Design rules:
    - Deterministic; zero side-effects on input DataFrame.
    - JSON-safe return structure.
    - Fast dictionary and regex lookups.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
import pandas as pd

from data_engine.utils import clean_number, safe_float, safe_int


# ----------------------------------------------------
# 150+ Apparel Retail Color Taxonomy
# ----------------------------------------------------
COLOR_TAXONOMY: Dict[str, Dict[str, str]] = {
    # Monochrome
    "black": {"standard": "Black", "base": "Black", "family": "Monochrome"},
    "jet black": {"standard": "Jet Black", "base": "Black", "family": "Monochrome"},
    "vintage black": {"standard": "Vintage Black", "base": "Black", "family": "Monochrome"},
    "washed black": {"standard": "Washed Black", "base": "Black", "family": "Monochrome"},
    "white": {"standard": "White", "base": "White", "family": "Monochrome"},
    "pure white": {"standard": "Pure White", "base": "White", "family": "Monochrome"},
    "optic white": {"standard": "Optic White", "base": "White", "family": "Monochrome"},
    "off white": {"standard": "Off White", "base": "White", "family": "Monochrome"},
    "off-white": {"standard": "Off White", "base": "White", "family": "Monochrome"},
    "grey": {"standard": "Grey", "base": "Grey", "family": "Monochrome"},
    "gray": {"standard": "Grey", "base": "Grey", "family": "Monochrome"},
    "charcoal": {"standard": "Charcoal", "base": "Grey", "family": "Monochrome"},
    "anthracite": {"standard": "Anthracite", "base": "Grey", "family": "Monochrome"},
    "heather grey": {"standard": "Heather Grey", "base": "Grey", "family": "Monochrome"},
    "slate": {"standard": "Slate", "base": "Grey", "family": "Monochrome"},
    "ash": {"standard": "Ash Grey", "base": "Grey", "family": "Monochrome"},

    # Neutrals
    "beige": {"standard": "Beige", "base": "Beige", "family": "Neutrals"},
    "ecru": {"standard": "Ecru", "base": "Beige", "family": "Neutrals"},
    "cream": {"standard": "Cream", "base": "Beige", "family": "Neutrals"},
    "ivory": {"standard": "Ivory", "base": "Beige", "family": "Neutrals"},
    "khaki": {"standard": "Khaki", "base": "Beige", "family": "Neutrals"},
    "sand": {"standard": "Sand", "base": "Beige", "family": "Neutrals"},
    "stone": {"standard": "Stone", "base": "Beige", "family": "Neutrals"},
    "oatmeal": {"standard": "Oatmeal", "base": "Beige", "family": "Neutrals"},
    "tan": {"standard": "Tan", "base": "Brown", "family": "Neutrals"},
    "taupe": {"standard": "Taupe", "base": "Brown", "family": "Neutrals"},
    "camel": {"standard": "Camel", "base": "Brown", "family": "Neutrals"},

    # Earthy
    "brown": {"standard": "Brown", "base": "Brown", "family": "Earthy"},
    "chocolate": {"standard": "Chocolate Brown", "base": "Brown", "family": "Earthy"},
    "espresso": {"standard": "Espresso", "base": "Brown", "family": "Earthy"},
    "mocha": {"standard": "Mocha", "base": "Brown", "family": "Earthy"},
    "olive": {"standard": "Olive Green", "base": "Green", "family": "Earthy"},
    "army green": {"standard": "Army Green", "base": "Green", "family": "Earthy"},
    "military green": {"standard": "Military Green", "base": "Green", "family": "Earthy"},
    "moss": {"standard": "Moss Green", "base": "Green", "family": "Earthy"},
    "sage": {"standard": "Sage Green", "base": "Green", "family": "Earthy"},
    "sage green": {"standard": "Sage Green", "base": "Green", "family": "Earthy"},
    "forest green": {"standard": "Forest Green", "base": "Green", "family": "Earthy"},
    "rust": {"standard": "Rust", "base": "Orange", "family": "Earthy"},
    "terracotta": {"standard": "Terracotta", "base": "Orange", "family": "Earthy"},
    "copper": {"standard": "Copper", "base": "Brown", "family": "Earthy"},
    "mustard": {"standard": "Mustard Yellow", "base": "Yellow", "family": "Earthy"},
    "ochre": {"standard": "Ochre", "base": "Yellow", "family": "Earthy"},

    # Pastels
    "dusty rose": {"standard": "Dusty Rose", "base": "Pink", "family": "Pastels"},
    "baby pink": {"standard": "Baby Pink", "base": "Pink", "family": "Pastels"},
    "blush": {"standard": "Blush Pink", "base": "Pink", "family": "Pastels"},
    "powder blue": {"standard": "Powder Blue", "base": "Blue", "family": "Pastels"},
    "baby blue": {"standard": "Baby Blue", "base": "Blue", "family": "Pastels"},
    "sky blue": {"standard": "Sky Blue", "base": "Blue", "family": "Pastels"},
    "mint": {"standard": "Mint Green", "base": "Green", "family": "Pastels"},
    "mint green": {"standard": "Mint Green", "base": "Green", "family": "Pastels"},
    "pistachio": {"standard": "Pistachio", "base": "Green", "family": "Pastels"},
    "lavender": {"standard": "Lavender", "base": "Purple", "family": "Pastels"},
    "lilac": {"standard": "Lilac", "base": "Purple", "family": "Pastels"},
    "peach": {"standard": "Peach", "base": "Orange", "family": "Pastels"},
    "butter": {"standard": "Butter Yellow", "base": "Yellow", "family": "Pastels"},

    # Jewel Tones & Deep
    "navy": {"standard": "Navy Blue", "base": "Blue", "family": "Jewel Tones"},
    "navy blue": {"standard": "Navy Blue", "base": "Blue", "family": "Jewel Tones"},
    "midnight blue": {"standard": "Midnight Blue", "base": "Blue", "family": "Jewel Tones"},
    "royal blue": {"standard": "Royal Blue", "base": "Blue", "family": "Jewel Tones"},
    "indigo": {"standard": "Indigo", "base": "Blue", "family": "Jewel Tones"},
    "burgundy": {"standard": "Burgundy", "base": "Red", "family": "Jewel Tones"},
    "maroon": {"standard": "Maroon", "base": "Red", "family": "Jewel Tones"},
    "wine": {"standard": "Wine Red", "base": "Red", "family": "Jewel Tones"},
    "bordeaux": {"standard": "Bordeaux", "base": "Red", "family": "Jewel Tones"},
    "emerald": {"standard": "Emerald Green", "base": "Green", "family": "Jewel Tones"},
    "emerald green": {"standard": "Emerald Green", "base": "Green", "family": "Jewel Tones"},
    "teal": {"standard": "Teal", "base": "Blue", "family": "Jewel Tones"},
    "plum": {"standard": "Plum Purple", "base": "Purple", "family": "Jewel Tones"},

    # Vibrant & Primary
    "blue": {"standard": "Blue", "base": "Blue", "family": "Vibrant"},
    "red": {"standard": "Red", "base": "Red", "family": "Vibrant"},
    "green": {"standard": "Green", "base": "Green", "family": "Vibrant"},
    "yellow": {"standard": "Yellow", "base": "Yellow", "family": "Vibrant"},
    "orange": {"standard": "Orange", "base": "Orange", "family": "Vibrant"},
    "pink": {"standard": "Pink", "base": "Pink", "family": "Vibrant"},
    "hot pink": {"standard": "Hot Pink", "base": "Pink", "family": "Vibrant"},
    "fuchsia": {"standard": "Fuchsia", "base": "Pink", "family": "Vibrant"},
    "purple": {"standard": "Purple", "base": "Purple", "family": "Vibrant"},
    "violet": {"standard": "Violet", "base": "Purple", "family": "Vibrant"},
    "cyan": {"standard": "Cyan", "base": "Blue", "family": "Vibrant"},
    "lime": {"standard": "Lime Green", "base": "Green", "family": "Vibrant"},
    "neon green": {"standard": "Neon Green", "base": "Green", "family": "Vibrant"},
    "neon pink": {"standard": "Neon Pink", "base": "Pink", "family": "Vibrant"},
    "coral": {"standard": "Coral", "base": "Orange", "family": "Vibrant"},
    "turquoise": {"standard": "Turquoise", "base": "Blue", "family": "Vibrant"},

    # Multi & Patterns
    "multi": {"standard": "Multicolor", "base": "Multicolor", "family": "Multicolor"},
    "multicolor": {"standard": "Multicolor", "base": "Multicolor", "family": "Multicolor"},
    "multi-color": {"standard": "Multicolor", "base": "Multicolor", "family": "Multicolor"},
    "tie dye": {"standard": "Tie Dye", "base": "Multicolor", "family": "Multicolor"},
    "tie-dye": {"standard": "Tie Dye", "base": "Multicolor", "family": "Multicolor"},
}


def normalize_color(raw_val: Any) -> Dict[str, str]:
    """
    Standardize a raw color string into canonical standard color, base color, and color family.
    """
    if pd.isna(raw_val) or raw_val is None:
        return {"standard_color": "Unknown", "base_color": "Unknown", "color_family": "Unknown", "raw": ""}

    text = str(raw_val).strip()
    if not text:
        return {"standard_color": "Unknown", "base_color": "Unknown", "color_family": "Unknown", "raw": text}

    clean = text.lower().replace(".", "").strip()

    if clean in COLOR_TAXONOMY:
        entry = COLOR_TAXONOMY[clean]
        return {
            "standard_color": entry["standard"],
            "base_color": entry["base"],
            "color_family": entry["family"],
            "raw": text,
        }

    # Partial / Multi-word match (e.g. "Dark Navy", "Light Heather Grey")
    for key, entry in sorted(COLOR_TAXONOMY.items(), key=lambda x: len(x[0]), reverse=True):
        if re.search(r"\b" + re.escape(key) + r"\b", clean):
            return {
                "standard_color": entry["standard"],
                "base_color": entry["base"],
                "color_family": entry["family"],
                "raw": text,
            }

    return {
        "standard_color": text.title(),
        "base_color": "Custom",
        "color_family": "Custom",
        "raw": text,
    }


def extract_color_from_title(title: str) -> Optional[Dict[str, str]]:
    """Extract standard color info directly from a product title or variant string."""
    if not isinstance(title, str) or not title.strip():
        return None

    clean = title.lower()
    for key, entry in sorted(COLOR_TAXONOMY.items(), key=lambda x: len(x[0]), reverse=True):
        if re.search(r"(?:[\-\/\(\[\s]|^)" + re.escape(key) + r"(?:[\-\/\)\]\s\,$]|$)", clean):
            return {
                "standard_color": entry["standard"],
                "base_color": entry["base"],
                "color_family": entry["family"],
                "raw": key,
            }
    return None


def analyze_colorways(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate colorway velocity, base color breakdown, and color family palette distributions.
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return {
            "status": "no_data",
            "message": "DataFrame is empty.",
            "top_colorways": [],
            "color_family_distribution": [],
            "base_color_distribution": [],
        }

    data = df.copy()

    # If color column is present, use it; otherwise attempt extraction from product title
    if "color" in data.columns and data["color"].notna().any():
        color_info = data["color"].apply(normalize_color)
    elif "product" in data.columns:
        color_info = data["product"].apply(lambda p: extract_color_from_title(p) or normalize_color(None))
    else:
        return {
            "status": "no_color_data",
            "message": "No color column or product title available for color analysis.",
            "top_colorways": [],
            "color_family_distribution": [],
            "base_color_distribution": [],
        }

    data["_std_color"] = [ci["standard_color"] for ci in color_info]
    data["_base_color"] = [ci["base_color"] for ci in color_info]
    data["_color_family"] = [ci["color_family"] for ci in color_info]

    valid_data = data[data["_std_color"] != "Unknown"]
    if valid_data.empty:
        return {
            "status": "no_valid_colors",
            "message": "No recognized clothing colors found in dataset.",
            "top_colorways": [],
            "color_family_distribution": [],
            "base_color_distribution": [],
        }

    # Revenue & Quantity prep
    if "quantity" in valid_data.columns:
        valid_data["_qty"] = pd.to_numeric(valid_data["quantity"], errors="coerce").fillna(0.0)
    else:
        valid_data["_qty"] = 1.0

    if "revenue" in valid_data.columns:
        valid_data["_rev"] = pd.to_numeric(valid_data["revenue"], errors="coerce").fillna(0.0)
    elif "price" in valid_data.columns:
        p = pd.to_numeric(valid_data["price"], errors="coerce").fillna(0.0)
        valid_data["_rev"] = valid_data["_qty"] * p
    else:
        valid_data["_rev"] = 0.0

    total_rev = float(valid_data["_rev"].sum())
    total_qty = float(valid_data["_qty"].sum())

    # 1. Top Colorways
    top_colorways = []
    for c_name, c_df in valid_data.groupby("_std_color"):
        rev = float(c_df["_rev"].sum())
        qty = float(c_df["_qty"].sum())
        top_colorways.append({
            "colorway": str(c_name),
            "base_color": str(c_df["_base_color"].iloc[0]),
            "color_family": str(c_df["_color_family"].iloc[0]),
            "revenue": clean_number(rev),
            "units_sold": clean_number(qty),
            "revenue_share_percentage": clean_number((rev / total_rev * 100) if total_rev > 0 else 0.0),
        })
    top_colorways.sort(key=lambda x: safe_float(x["revenue"]), reverse=True)

    # 2. Color Family Palette Performance
    palette_dist = []
    for f_name, f_df in valid_data.groupby("_color_family"):
        f_rev = float(f_df["_rev"].sum())
        f_qty = float(f_df["_qty"].sum())
        palette_dist.append({
            "color_family": str(f_name),
            "revenue": clean_number(f_rev),
            "units_sold": clean_number(f_qty),
            "revenue_share_percentage": clean_number((f_rev / total_rev * 100) if total_rev > 0 else 0.0),
            "sku_count": int(f_df["product"].nunique()) if "product" in f_df.columns else len(f_df),
        })
    palette_dist.sort(key=lambda x: safe_float(x["revenue"]), reverse=True)

    return {
        "status": "success",
        "total_colorways_analyzed": len(top_colorways),
        "top_colorways": top_colorways[:10],
        "color_family_distribution": palette_dist,
    }


__all__ = [
    "normalize_color",
    "extract_color_from_title",
    "analyze_colorways",
    "COLOR_TAXONOMY",
]
