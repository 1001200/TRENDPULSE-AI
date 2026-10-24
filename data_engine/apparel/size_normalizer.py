"""
TrendPulse Apparel Size Normalization & Size Curve Engine.

Standardizes heterogeneous clothing size strings across alpha, numeric,
waist/inseam, dual-range, and one-size formats.
Calculates catalog size curves and detects Broken Size Runs.

Design rules:
    - Deterministic; zero side-effects on input DataFrame.
    - JSON-safe return structure.
    - Handles merchant-specific size variations gracefully.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from data_engine.utils import clean_number, safe_float, safe_int


# Standard alpha ordering for clothing sorting
ALPHA_ORDER = ["3XS", "2XS", "XS", "S", "M", "L", "XL", "2XL", "3XL", "4XL", "5XL", "Free Size"]
CORE_ALPHA_SIZES = {"S", "M", "L", "XL"}
CORE_NUMERIC_SIZES = {"30", "32", "34", "36"}


def normalize_size(raw_val: Any) -> Dict[str, str]:
    """
    Standardize a raw size input into a canonical format and size type.
    """
    if pd.isna(raw_val) or raw_val is None:
        return {"standard_size": "Unknown", "size_type": "unknown", "raw": ""}

    text = str(raw_val).strip()
    if not text:
        return {"standard_size": "Unknown", "size_type": "unknown", "raw": text}

    clean = text.lower().replace(".", "").replace(",", "").strip()

    # 1. One Size / Free Size
    if clean in {"free size", "one size", "os", "osfa", "fs", "free", "onesize", "freesize", "one-size", "free-size"}:
        return {"standard_size": "Free Size", "size_type": "one_size", "raw": text}

    # 2. Alpha sizes mapping
    alpha_map = {
        "3xs": "3XS", "xxxs": "3XS", "xxx-small": "3XS", "xxx small": "3XS",
        "2xs": "2XS", "xxs": "2XS", "xx-small": "2XS", "xx small": "2XS",
        "xs": "XS", "x-small": "XS", "x small": "XS", "extra small": "XS", "extrasmall": "XS",
        "s": "S", "sm": "S", "small": "S",
        "m": "M", "med": "M", "medium": "M",
        "l": "L", "lg": "L", "large": "L",
        "xl": "XL", "x-large": "XL", "x large": "XL", "extra large": "XL", "extralarge": "XL", "1xl": "XL",
        "2xl": "2XL", "xxl": "2XL", "2x-large": "2XL", "2x large": "2XL", "xx-large": "2XL", "xx large": "2XL", "2x": "2XL",
        "3xl": "3XL", "xxxl": "3XL", "3x-large": "3XL", "3x large": "3XL", "3x": "3XL",
        "4xl": "4XL", "xxxxl": "4XL", "4x-large": "4XL", "4x large": "4XL", "4x": "4XL",
        "5xl": "5XL", "xxxxxl": "5XL", "5x-large": "5XL", "5x large": "5XL", "5x": "5XL",
    }

    if clean in alpha_map:
        return {"standard_size": alpha_map[clean], "size_type": "alpha", "raw": text}

    # 3. Waist x Inseam bottom sizes (e.g. 32x30, 32/32, 34/34, 32-30)
    inseam_match = re.match(r"^([2-4][0-9])\s*[x\/\-]\s*([2-4][0-9])$", clean)
    if inseam_match:
        w, i = inseam_match.group(1), inseam_match.group(2)
        return {"standard_size": f"{w}x{i}", "size_type": "waist_inseam", "raw": text}

    # 4. Numeric waist / chest sizes (e.g. 28, 30, 32, 34, 36, 38, 40, 42, 44)
    num_match = re.match(r"^([0-9]{2})$", clean)
    if num_match:
        val = int(num_match.group(1))
        if 24 <= val <= 56:
            return {"standard_size": str(val), "size_type": "numeric", "raw": text}

    # 5. Dual / Range sizes (e.g. S/M, M-L, L/XL)
    dual_match = re.match(r"^([a-z0-9]+)\s*[\/\-]\s*([a-z0-9]+)$", clean)
    if dual_match:
        part1 = normalize_size(dual_match.group(1))["standard_size"]
        part2 = normalize_size(dual_match.group(2))["standard_size"]
        if part1 != "Unknown" and part2 != "Unknown":
            return {"standard_size": f"{part1}-{part2}", "size_type": "dual_range", "raw": text}

    # Prefix/Suffix patterns like "Size: L" or "L (US)"
    prefix_match = re.search(r"\b(3xs|2xs|xs|s|m|l|xl|2xl|xxl|3xl|xxxl|4xl|5xl)\b", clean)
    if prefix_match and len(clean.split()) <= 3:
        matched = prefix_match.group(1)
        if matched in alpha_map:
            return {"standard_size": alpha_map[matched], "size_type": "alpha", "raw": text}

    # Fallback to uppercase clean string
    return {"standard_size": text.upper(), "size_type": "custom", "raw": text}


def extract_size_from_title(title: str) -> Optional[str]:
    """Extract standard size from a product title or variant string if size column is missing."""
    if not isinstance(title, str) or not title.strip():
        return None

    # Matches "- XL", "/ L", "(Size: M)", "[XXL]", "- 32x30", "/ 28"
    patterns = [
        r"[\-\/\(\[\,]\s*(?:size[:\s]*)?([321]?[xX]?[sSmMlL]{1,3}|[2-4][0-9]x[2-4][0-9]|[2-4][0-9]|free\s*size|one\s*size)\s*[\)\]\,]?$",
        r"\b(?:size[:\s]+)([321]?[xX]?[sSmMlL]{1,3}|[2-4][0-9]x[2-4][0-9]|[2-4][0-9]|free\s*size|one\s*size)\b",
    ]
    for pat in patterns:
        m = re.search(pat, title, re.IGNORECASE)
        if m:
            norm = normalize_size(m.group(1))
            if norm["standard_size"] != "Unknown":
                return norm["standard_size"]
    return None


def calculate_size_curves(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate size demand distributions across the catalog and per category/product.
    """
    if not isinstance(df, pd.DataFrame) or df.empty or "size" not in df.columns:
        return {
            "status": "no_size_data",
            "message": "No size column available in dataset.",
            "overall_size_curve": [],
            "category_size_curves": {},
        }

    data = df.copy()
    data["_std_size"] = data["size"].apply(lambda s: normalize_size(s)["standard_size"])
    data = data[data["_std_size"] != "Unknown"]

    if data.empty:
        return {
            "status": "no_valid_sizes",
            "message": "Could not standardize sizes from dataset.",
            "overall_size_curve": [],
            "category_size_curves": {},
        }

    qty_col = "_qty"
    if "quantity" in data.columns:
        data[qty_col] = pd.to_numeric(data["quantity"], errors="coerce").fillna(0.0)
    else:
        data[qty_col] = 1.0

    total_units = float(data[qty_col].sum())
    if total_units == 0:
        total_units = 1.0

    # Overall size curve
    overall_grouped = data.groupby("_std_size")[qty_col].sum()
    overall_curve = []
    for s_name, units in overall_grouped.items():
        u = float(units)
        pct = (u / total_units) * 100.0
        overall_curve.append({
            "size": str(s_name),
            "units_sold": clean_number(u),
            "share_percentage": clean_number(pct),
        })

    # Sort alpha sizes by standard apparel order
    def _size_sort_key(item: Dict[str, Any]) -> int:
        s = item["size"]
        if s in ALPHA_ORDER:
            return ALPHA_ORDER.index(s)
        return 100

    overall_curve.sort(key=_size_sort_key)

    # Category size curves
    category_curves = {}
    if "category" in data.columns:
        for cat_name, cat_df in data.groupby("category"):
            c_units = float(cat_df[qty_col].sum())
            if c_units <= 0:
                continue
            cat_curve = []
            for s_name, u_val in cat_df.groupby("_std_size")[qty_col].sum().items():
                u = float(u_val)
                cat_curve.append({
                    "size": str(s_name),
                    "units_sold": clean_number(u),
                    "share_percentage": clean_number((u / c_units) * 100.0),
                })
            cat_curve.sort(key=_size_sort_key)
            category_curves[str(cat_name)] = cat_curve

    return {
        "status": "success",
        "total_units_analyzed": clean_number(total_units),
        "overall_size_curve": overall_curve,
        "category_size_curves": category_curves,
    }


def detect_broken_size_runs(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Detect styles suffering from broken size runs (e.g. M/L missing while XS/XXL sold).
    """
    if not isinstance(df, pd.DataFrame) or df.empty or "size" not in df.columns or "product" not in df.columns:
        return []

    data = df.copy()
    data["_std_size"] = data["size"].apply(lambda s: normalize_size(s)["standard_size"])
    data = data[data["_std_size"] != "Unknown"]

    if data.empty:
        return []

    if "quantity" in data.columns:
        data["_qty"] = pd.to_numeric(data["quantity"], errors="coerce").fillna(0.0)
    else:
        data["_qty"] = 1.0

    broken_runs = []

    for prod_name, p_df in data.groupby("product"):
        sizes_present = set(p_df["_std_size"].unique())
        total_style_units = float(p_df["_qty"].sum())

        # Only analyze styles with at least 5 units sold
        if total_style_units < 5 or len(sizes_present) < 2:
            continue

        # Check for Alpha broken size run (core sizes S, M, L)
        alpha_present = sizes_present.intersection(set(ALPHA_ORDER))
        if len(alpha_present) >= 2:
            has_s = "S" in sizes_present
            has_m = "M" in sizes_present
            has_l = "L" in sizes_present
            has_fringe = ("XS" in sizes_present or "2XL" in sizes_present or "3XL" in sizes_present)

            # Missing core size M or L while outer sizes are present
            if has_fringe and (not has_m or not has_l):
                missing_core = [s for s in ["M", "L"] if s not in sizes_present]
                broken_runs.append({
                    "product": str(prod_name),
                    "issue": "broken_size_run",
                    "severity": "high",
                    "available_sizes": sorted(list(sizes_present), key=lambda x: ALPHA_ORDER.index(x) if x in ALPHA_ORDER else 99),
                    "missing_core_sizes": missing_core,
                    "explanation": f"Core size(s) {', '.join(missing_core)} have 0 sales/stock while fringe sizes remain, indicating stockout-induced lost sales.",
                })

    return broken_runs


__all__ = [
    "normalize_size",
    "extract_size_from_title",
    "calculate_size_curves",
    "detect_broken_size_runs",
    "ALPHA_ORDER",
]
