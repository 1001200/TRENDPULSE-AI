"""
TrendPulse shared utility functions.

This module provides common numeric helpers used across the data engine.
Every other module should import from here instead of defining local copies.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def safe_float(value) -> float:
    """
    Safely convert a value to float.

    Returns 0.0 for NaN, None, or unconvertible values.
    """
    try:
        if pd.isna(value):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def safe_int(value) -> int:
    """
    Safely convert a value to int.

    Returns 0 for NaN, None, or unconvertible values.
    """
    try:
        if pd.isna(value):
            return 0
        return int(value)
    except (TypeError, ValueError):
        return 0


def clean_number(value, decimals: int = 2):
    """
    Convert numpy/pandas numeric values into normal Python
    int/float values suitable for JSON/UI output.

    Parameters
    ----------
    value : any
        The value to clean.
    decimals : int
        Number of decimal places to round to.
        Default is 2 (business display).
        Use 6 for statistical precision (anomaly scores, etc.).

    Returns
    -------
    int | float | None
    """
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(value):
        return None
    if value.is_integer():
        return int(value)
    return round(value, decimals)


def index_to_output_value(index):
    """
    Convert a pandas/numpy index value into a JSON-safe value.
    """
    if isinstance(index, (int, np.integer)):
        return int(index)

    if isinstance(index, (float, np.floating)):
        if np.isfinite(index) and float(index).is_integer():
            return int(index)
        return float(index)

    if isinstance(index, (str, bool)):
        return index

    return str(index)


__all__ = [
    "safe_float",
    "safe_int",
    "clean_number",
    "index_to_output_value",
]
