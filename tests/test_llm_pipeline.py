import pandas as pd

from data_engine.processor import process_dataframe


def test_pipeline_llm_disabled():
    df = pd.DataFrame(
        {
            "Order Date": ["2026-08-20", "2026-08-21", "2026-08-22"],
            "Product Name": ["Black Tee", "Blue Jeans", "White Hoodie"],
            "Category": ["T-Shirt", "Jeans", "Hoodie"],
            "Qty Sold": [5, 3, 4],
            "Selling Price": [699, 1299, 799],
            "Customer ID": ["C001", "C002", "C003"],
        }
    )

    result = process_dataframe(
        df,
        enable_llm=False,
    )

    assert result["status"] == "success"
    assert result["llm_analysis"] is None

    print("\nLLM DISABLED PIPELINE")
    print(result["llm_analysis"])


def test_pipeline_llm_fallback():
    df = pd.DataFrame(
        {
            "Order Date": ["2026-08-20", "2026-08-21", "2026-08-22"],
            "Product Name": ["Black Tee", "Blue Jeans", "White Hoodie"],
            "Category": ["T-Shirt", "Jeans", "Hoodie"],
            "Qty Sold": [5, 3, 4],
            "Selling Price": [699, 1299, 799],
            "Customer ID": ["C001", "C002", "C003"],
        }
    )

    result = process_dataframe(
        df,
        enable_llm=True,
        llm_client=None,
    )

    assert result["status"] == "success"
    assert result["llm_analysis"] is not None
    assert isinstance(result["llm_analysis"], dict)
    assert "enabled" in result["llm_analysis"]
    assert "recommendations" in result["llm_analysis"]

    print("\nLLM FALLBACK PIPELINE")
    print(result["llm_analysis"])


def test_pipeline_result_contains_all_intelligence_layers():
    df = pd.DataFrame(
        {
            "Order Date": ["2026-08-20", "2026-08-21", "2026-08-22"],
            "Product Name": ["Black Tee", "Blue Jeans", "White Hoodie"],
            "Category": ["T-Shirt", "Jeans", "Hoodie"],
            "Qty Sold": [5, 3, 4],
            "Selling Price": [699, 1299, 799],
            "Customer ID": ["C001", "C002", "C003"],
        }
    )

    result = process_dataframe(
        df,
        enable_llm=True,
    )

    required_keys = [
        "version",
        "status",
        "column_mapping",
        "cleaning_summary",
        "cleaning_audit",
        "validation",
        "anomalies",
        "anomaly_summary",
        "profiler",
        "quality_report",
        "insights",
        "llm_analysis",
        "processed_data",
    ]

    for key in required_keys:
        assert key in result

    assert result["status"] == "success"
    assert isinstance(result["processed_data"], pd.DataFrame)

    print("\nFULL INTELLIGENCE PIPELINE")
    print("Status:", result["status"])
    print("LLM:", result["llm_analysis"])
    print("Processed columns:", list(result["processed_data"].columns))