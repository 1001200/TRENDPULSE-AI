"""
TrendPulse service boundary.

This module provides the backend-facing interface to the data engine.
It keeps HTTP/API layers independent from pandas and internal pipeline
implementation details.
"""

from pathlib import Path
from typing import Any, Optional

from data_engine.processor import (
    process_dataframe,
    process_file,
    result_to_json_safe,
)


def analyze_dataframe(
    dataframe,
    *,
    llm_client=None,
    enable_llm: bool = True,
) -> dict:
    """
    Analyze an already-loaded pandas DataFrame.

    Returns a JSON-safe dictionary suitable for API responses.
    """
    result = process_dataframe(
        dataframe,
        llm_client=llm_client,
        enable_llm=enable_llm,
    )

    return result_to_json_safe(result)


def analyze_file(
    file_path,
    *,
    llm_client=None,
    enable_llm: bool = True,
) -> dict:
    """
    Analyze a CSV or Excel file.

    Returns a JSON-safe dictionary suitable for API responses.
    """
    result = process_file(
        file_path,
        llm_client=llm_client,
        enable_llm=enable_llm,
    )

    return result_to_json_safe(result)


def health_check() -> dict:
    """
    Basic service health information.
    """
    return {
        "service": "TrendPulse Data Engine",
        "status": "healthy",
        "version": "4.0",
    }


__all__ = [
    "analyze_dataframe",
    "analyze_file",
    "health_check",
]